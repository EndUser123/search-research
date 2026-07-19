// ccr-admission-proxy.js — observability and forwarding layer for CCR.
//
// This proxy sits BEFORE CCR in the request path:
//   Claude Code → admission-proxy (:3458) → CCR (configured PORT) → providers
//
// ROLE: count logical requests, record lifecycle events in a SQLite ledger,
// expose Prometheus metrics on /metrics, and forward all inference requests
// to CCR unchanged. The proxy does NOT reject or gate requests based on
// estimated token count — CCR's routing determines which provider model
// handles each request.
//
// TOKEN ESTIMATE: heuristic — chars / CHAR_PER_TOKEN on the full request body.
// Recorded in the ledger for observability. This is NOT the same as CCR's
// tiktoken count; it is a conservative approximation.
//
// HISTORY: a context ceiling (SAFE_CEILING) previously rejected requests
// exceeding a token threshold. It was removed because it blocked
// compaction requests and introduced a cascade of exemption bugs. The
// SAFE_CEILING constant is retained only for the OVER_CEILING observability
// label — it no longer gates forwarding.
//
// WIRING: cc-ccr.ps1 sets ANTHROPIC_BASE_URL to this proxy's port (:3458)
// instead of CCR directly. CCR_PORT is read from the configured CCR port,
// with 3456 retained only as the explicit compatibility fallback.

const http = require("http");
const fs = require("fs");
const path = require("path");
const { shapeAnthropicRequest } = require("./ccr-context-shaper");
const ledger = require("./ccr-request-ledger");

const PROXY_PORT = parseInt(process.env.CCR_ADMISSION_PORT || "3458", 10);
const CCR_HOST = process.env.CCR_HOST || "127.0.0.1";
const CCR_PORT = parseInt(process.env.CCR_PORT || "3456", 10);

// -- Shared canonical route-metadata (single source in ccr-route-metadata.js) ---
const {
  CONTEXT_LIMITS: VERIFIED_ROUTE_LIMITS,
  ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY,
  GLOBAL_CONTEXT_LIMIT,
  OUTPUT_RESERVE,
  CHAR_PER_TOKEN,
} = require("./ccr-route-metadata");

// Local llama.cpp has a separate live-context/admission path in the custom
// router. It must not lower the blanket cloud ceiling for requests that fall
// back from local to a verified 1M cloud backend.

const SAFE_CEILING = GLOBAL_CONTEXT_LIMIT - OUTPUT_RESERVE;


const LOG_FILE = process.env.CCR_ADMISSION_LOG || "P:/.claude/state/ccr-admission-log.jsonl";
const CCR_CONFIG_PATH = process.env.CCR_CONFIG_PATH || "C:/Users/brsth/.claude-code-router/config.json";

const INFERENCE_PATHS = new Set([
  "/v1/messages",
  "/v1/chat/completions",
  "/v1/completions",
  "/completion",
  "/infill",
]);

function requestPath(url) {
  try { return new URL(url || "/", "http://localhost").pathname; } catch { return url || "/"; }
}

function isInferencePath(method, url) {
  return method === "POST" && INFERENCE_PATHS.has(requestPath(url));
}

function statusOutcome(statusCode) {
  const status = Number(statusCode || 0);
  if (status >= 200 && status < 400) return "completed";
  if ([502, 503, 504].includes(status)) return "upstream_unavailable";
  return "failed";
}

function requestModel(body) {
  return body?.model || body?.model_alias || "unknown";
}

function collectRoutes(value, routes = new Set()) {
  if (typeof value === "string" && value.includes(",")) {
    routes.add(value);
  } else if (Array.isArray(value)) {
    for (const item of value) collectRoutes(item, routes);
  } else if (value && typeof value === "object") {
    for (const item of Object.values(value)) collectRoutes(item, routes);
  }
  return routes;
}

function getConfiguredRoutes(configPath = CCR_CONFIG_PATH) {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const routeConfig = { Router: config.Router, fallback: config.fallback };
  return [...collectRoutes(routeConfig)].sort();
}

function getUnverifiedConfiguredRoutes(configPath = CCR_CONFIG_PATH) {
  return getConfiguredRoutes(configPath).filter((route) =>
    !(route in VERIFIED_ROUTE_LIMITS) && !ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY.has(route));
}

function validateConfiguredRoutes(configPath = CCR_CONFIG_PATH) {
  const unverified = getUnverifiedConfiguredRoutes(configPath);
  if (unverified.length) {
    throw new Error(`Unverified CCR routes: ${unverified.join(", ")}`);
  }
  return true;
}

function logAdmission(entry) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    fs.appendFileSync(LOG_FILE, JSON.stringify(entry) + "\n");
  } catch {}
}

function estimateTokens(body) {
  // Serialize the full body (messages + system + tools + thinking) and count chars.
  // This is a heuristic, NOT CCR's exact tiktoken count. See header comment.
  const json = typeof body === "string" ? body : JSON.stringify(body);
  const inputEstimate = Math.ceil(json.length / CHAR_PER_TOKEN);
  const maxTokens = body?.max_tokens || body?.maxTokens || 0;
  return { inputEstimate, maxTokens, total: inputEstimate + maxTokens };
}

function getSystemScopes() {
  const raw = process.env.CCR_CONTEXT_SYSTEM_SCOPES || "";
  return raw.split(",").map((scope) => scope.trim()).filter(Boolean);
}

function safeJsonBytes(body) {
  try { return Buffer.byteLength(JSON.stringify(body), "utf8"); } catch { return 0; }
}

function prepareAdmissionBody(body) {
  try {
    return shapeAnthropicRequest(body, { systemScopes: getSystemScopes() });
  } catch (error) {
    return {
      body,
      changed: false,
      telemetry: {
        failed_open: true,
        failure: error instanceof Error ? error.message : String(error),
        raw_bytes: safeJsonBytes(body),
        shaped_bytes: safeJsonBytes(body),
        bytes_saved: 0,
        compacted_count: 0,
        compacted_resources: [],
        system_blocks_dropped: 0,
        system_blocks_dropped_hashes: [],
      },
    };
  }
}

function observeResponseBody() {
  let tail = "";
  return {
    push(chunk) {
      tail = (tail + Buffer.from(chunk).toString("utf8")).slice(-131072);
    },
    outputTokens() {
      const matches = [...tail.matchAll(/(?:completion_tokens|output_tokens|tokens_predicted)"?\s*:\s*(\d+)/g)];
      if (!matches.length) return null;
      return Number(matches[matches.length - 1][1]);
    },
    quotaFailure() {
      return /quota|rate[-_ ]?limit|too many requests|resource exhausted/i.test(tail);
    },
  };
}

function forwardToCCR(req, bodyBuf, res, lifecycle = null) {
  const headers = { ...req.headers, "content-length": String(bodyBuf.length) };
  delete headers["transfer-encoding"];
  if (lifecycle) headers["x-request-id"] = lifecycle.requestId;
  const observer = observeResponseBody();
  const attemptId = lifecycle ? `attempt-${lifecycle.requestId}` : null;
  if (lifecycle) ledger.markAdmitted(lifecycle);
  let responseEnded = false;
  const finalize = (input) => {
    if (!lifecycle || lifecycle.finalized) return;
    ledger.finalizeRequest(lifecycle, input);
  };
  const proxyReq = http.request(
    { host: CCR_HOST, port: CCR_PORT, method: req.method, path: req.url, headers },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      const attemptStarted = Date.now();
      if (lifecycle) {
        ledger.recordAttempt({
          attemptId,
          requestId: lifecycle.requestId,
          provider: "CCR",
          model: lifecycle.model,
          outcome: "started",
          correlationQuality: "exact",
        });
      }
      proxyRes.on("data", (chunk) => observer.push(chunk));
      proxyRes.on("end", () => {
        responseEnded = true;
        const outcome = statusOutcome(proxyRes.statusCode);
        if (proxyRes.statusCode === 429 || observer.quotaFailure()) ledger.recordQuotaFailure();
        if (lifecycle) {
          ledger.recordAttempt({
            attemptId,
            requestId: lifecycle.requestId,
            provider: "CCR",
            model: lifecycle.model,
            outcome,
            statusCode: proxyRes.statusCode,
            durationMs: Date.now() - attemptStarted,
            correlationQuality: "exact",
          });
        }
        finalize({ outcome, statusCode: proxyRes.statusCode, outputTokens: observer.outputTokens() });
      });
      proxyRes.on("aborted", () => finalize({ outcome: "upstream_unavailable", statusCode: proxyRes.statusCode }));
      proxyRes.pipe(res);
    },
  );
  proxyReq.on("error", (e) => {
    if (responseEnded) return;
    finalize({ outcome: "upstream_unavailable", statusCode: 502 });
    if (!res.headersSent) {
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: { type: "admission_proxy_upstream_error", message: `CCR unreachable: ${e.message}` } }));
    }
  });
  res.on("close", () => {
    if (!responseEnded) finalize({ outcome: "cancelled", statusCode: 499, outputTokens: observer.outputTokens() });
  });
  if (bodyBuf && bodyBuf.length > 0) proxyReq.write(bodyBuf);
  proxyReq.end();
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && requestPath(req.url) === "/metrics") {
    const body = ledger.prometheusMetrics();
    res.writeHead(200, { "content-type": "text/plain; version=0.0.4; charset=utf-8" });
    res.end(body);
    return;
  }

  const inferenceRequest = isInferencePath(req.method, req.url);

  if (!inferenceRequest) {
    // Non-inference: pipe through without buffering
    const proxyReq = http.request(
      { host: CCR_HOST, port: CCR_PORT, method: req.method, path: req.url, headers: req.headers },
      (proxyRes) => { res.writeHead(proxyRes.statusCode, proxyRes.headers); proxyRes.pipe(res); },
    );
    proxyReq.on("error", () => {
      if (!res.headersSent) { res.writeHead(502); res.end("CCR unreachable"); }
    });
    req.pipe(proxyReq);
    return;
  }

  const requestId = req.headers["x-request-id"] || `proxy-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  req.headers["x-request-id"] = requestId;
  const lifecycle = ledger.createRequest({ requestId });

  // Inference path: buffer body, check admission, forward or reject
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const bodyBuf = Buffer.concat(chunks);
    let body;
    try { body = JSON.parse(bodyBuf.toString("utf-8")); } catch {
      // Malformed JSON — let CCR handle the error
      forwardToCCR(req, bodyBuf, res, lifecycle);
      return;
    }

    const rawEstimate = estimateTokens(body);
    const prepared = prepareAdmissionBody(body);
    const shapedBody = prepared.body;
    const shapedBuf = Buffer.from(JSON.stringify(shapedBody), "utf8");
    const { inputEstimate, maxTokens, total } = estimateTokens(shapedBody);
    const model = requestModel(body);
    ledger.updateRequest(lifecycle, { model, inputTokensEstimate: inputEstimate });

    const entry = {
      ts: new Date().toISOString(),
      request_id: requestId,
      nominal_model: model,
      raw_input_token_estimate: rawEstimate.inputEstimate,
      raw_total_estimate: rawEstimate.total,
      input_token_estimate: inputEstimate,
      output_budget: maxTokens,
      total_estimate: total,
      context_shaper: prepared.telemetry,
      safe_ceiling: SAFE_CEILING,
      decision: "unknown",
      reason: null,
    };

    // Forward all requests to CCR. The SAFE_CEILING comparison is retained
    // only for the decision label (FORWARDED vs FORWARDED_OVER_CEILING) so
    // the ledger can still show when requests exceed the former threshold.
    // It does not gate forwarding — all requests pass through regardless.
    const overCeiling = total > SAFE_CEILING;
    entry.decision = overCeiling ? "FORWARDED_OVER_CEILING" : "FORWARDED";
    entry.reason = overCeiling
      ? `total ${total} > ceiling ${SAFE_CEILING} — forwarded (ceiling disabled)`
      : `total ${total} <= ceiling ${SAFE_CEILING}`;
    logAdmission(entry);
    if (overCeiling) {
      try { process.stderr.write(`[admission-proxy] OVER CEILING: ${entry.reason} (model=${model}, req=${requestId})\n`); } catch {}
    }
    forwardToCCR(req, shapedBuf, res, lifecycle);
  });
  req.on("aborted", () => ledger.finalizeRequest(lifecycle, { outcome: "cancelled", statusCode: 499 }));
  req.on("error", () => {
    ledger.finalizeRequest(lifecycle, { outcome: "failed", statusCode: 400 });
    if (!res.headersSent) { res.writeHead(400); res.end("request read error"); }
  });
});

if (require.main === module) {
  try {
    validateConfiguredRoutes();
  } catch (error) {
    process.stderr.write(`[admission-proxy] REFUSING TO START: ${error.message}\n`);
    process.exitCode = 1;
    return;
  }
  server.listen(PROXY_PORT, "127.0.0.1", () => {
    process.stderr.write(`[admission-proxy] listening on :${PROXY_PORT}, forwarding to ${CCR_HOST}:${CCR_PORT}\n`);
    process.stderr.write(`[admission-proxy] safe ceiling: ${SAFE_CEILING} (global limit=${GLOBAL_CONTEXT_LIMIT}, reserve=${OUTPUT_RESERVE})\n`);
  });
}

module.exports = {
  server,
  estimateTokens,
  SAFE_CEILING,
  GLOBAL_CONTEXT_LIMIT,
  VERIFIED_ROUTE_LIMITS,
  ROUTES_HANDLED_OUTSIDE_CLOUD_PROXY,
  OUTPUT_RESERVE,
  CHAR_PER_TOKEN,
  collectRoutes,
  getConfiguredRoutes,
  getUnverifiedConfiguredRoutes,
  validateConfiguredRoutes,
  getSystemScopes,
  prepareAdmissionBody,
};
