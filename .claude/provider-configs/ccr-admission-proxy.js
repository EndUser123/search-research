// ccr-admission-proxy.js — pre-CCR HTTP admission gate.
//
// PROBLEM: CCR's custom-router API returns a route string or null. Null is
// fall-through to CCR's built-in router (B6), NOT rejection. There is no
// structured rejection API. Therefore the custom router CANNOT prevent a
// provider request — it can only choose which provider.
//
// This proxy sits BEFORE CCR in the request path:
//   Claude Code → admission-proxy (:3458) → CCR (:3456) → providers
//
// It rejects oversized requests with HTTP 413 before any forwarding. Safe
// requests pass through to CCR untouched (CCR makes the routing decision).
//
// TOKEN ESTIMATE: heuristic — chars / CHAR_PER_TOKEN on the full request body.
// This is NOT the same as CCR's tiktoken cl100k_base count (which tokenizes
// per-message). It is a conservative over-estimate: cl100k_base averages
// ~4 chars/token for English prose and ~3 chars/token for code-dense content.
// Using 3 chars/token (CHAR_PER_TOKEN=3) over-counts for prose, which is the
// safe direction (false-positive rejection > false-negative admission).
//
// OUTPUT BUDGET: max_tokens from the request body (if present). Added to the
// input estimate. This is a real derived value, not a heuristic.
//
// LIMITS: the proxy applies a blanket ceiling — the maximum verified limit
// across all configured backends, minus OUTPUT_RESERVE. It does NOT determine
// the per-request candidate backend (that happens in CCR after forwarding).
// If the request is below the ceiling, CCR picks the right backend. If above,
// no configured backend can handle it → reject. This is correct because all
// configured backends share the same 1M-class limit. If backends with
// different limits are added, per-backend routing precision in the proxy
// becomes necessary (see "Remaining limitations" in the report).
//
// WIRING: cc-ccr.ps1 sets ANTHROPIC_BASE_URL to this proxy's port (:3458)
// instead of CCR directly (:3456). The proxy forwards to CCR (:3456).

const http = require("http");
const fs = require("fs");
const path = require("path");

const PROXY_PORT = parseInt(process.env.CCR_ADMISSION_PORT || "3458", 10);
const CCR_HOST = process.env.CCR_HOST || "127.0.0.1";
const CCR_PORT = parseInt(process.env.CCR_PORT || "3456", 10);

// --- Verified backend limits (same source as ccr-custom-router.js) ---
const MAX_VERIFIED_LIMIT = 1_000_000; // all configured backends are 1M-class
const OUTPUT_RESERVE = 16_384; // heuristic reserve for serialization/tokenizer delta
const SAFE_CEILING = MAX_VERIFIED_LIMIT - OUTPUT_RESERVE;

// Conservative char-to-token ratio. cl100k_base averages ~4 chars/token for
// prose, ~3 for code. Using 3 over-counts for prose (safe direction).
const CHAR_PER_TOKEN = 3;

const LOG_FILE = process.env.CCR_ADMISSION_LOG || "P:/.claude/state/ccr-admission-log.jsonl";

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

function forwardToCCR(req, bodyBuf, res) {
  const proxyReq = http.request(
    { host: CCR_HOST, port: CCR_PORT, method: req.method, path: req.url, headers: req.headers },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );
  proxyReq.on("error", (e) => {
    if (!res.headersSent) {
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: { type: "admission_proxy_upstream_error", message: `CCR unreachable: ${e.message}` } }));
    }
  });
  if (bodyBuf && bodyBuf.length > 0) proxyReq.write(bodyBuf);
  proxyReq.end();
}

const server = http.createServer((req, res) => {
  // Only gate POST /v1/messages (the Claude inference path). Other paths
  // (health, etc.) pass through without admission logic.
  const isInferencePath = req.method === "POST" && (req.url === "/v1/messages" || req.url === "/v1/messages/");

  if (!isInferencePath) {
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

  // Inference path: buffer body, check admission, forward or reject
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const bodyBuf = Buffer.concat(chunks);
    let body;
    try { body = JSON.parse(bodyBuf.toString("utf-8")); } catch {
      // Malformed JSON — let CCR handle the error
      forwardToCCR(req, bodyBuf, res);
      return;
    }

    const { inputEstimate, maxTokens, total } = estimateTokens(body);
    const requestId = req.headers["x-request-id"] || `proxy-${Date.now()}`;
    const model = body?.model || "unknown";

    const entry = {
      ts: new Date().toISOString(),
      request_id: requestId,
      nominal_model: model,
      input_token_estimate: inputEstimate,
      output_budget: maxTokens,
      total_estimate: total,
      safe_ceiling: SAFE_CEILING,
      decision: "unknown",
      reason: null,
    };

    if (total > SAFE_CEILING) {
      entry.decision = "REJECTED";
      entry.reason = `total ${total} > ceiling ${SAFE_CEILING} (limit=${MAX_VERIFIED_LIMIT}, reserve=${OUTPUT_RESERVE})`;
      logAdmission(entry);
      try { process.stderr.write(`[admission-proxy] REJECTED: ${entry.reason} (model=${model}, req=${requestId})\n`); } catch {}
      res.writeHead(413, { "content-type": "application/json" });
      res.end(JSON.stringify({
        error: {
          type: "admission_proxy_context_exceeded",
          message: `Request rejected by admission proxy: estimated ${total} tokens (input ${inputEstimate} + output ${maxTokens}) exceeds the safe ceiling of ${SAFE_CEILING} (backend limit ${MAX_VERIFIED_LIMIT} minus ${OUTPUT_RESERVE} reserve). No configured backend can handle this request. Reduce context size.`,
          admission_details: entry,
        },
      }));
      return;
    }

    entry.decision = "FORWARDED";
    entry.reason = `total ${total} <= ceiling ${SAFE_CEILING}`;
    logAdmission(entry);
    forwardToCCR(req, bodyBuf, res);
  });
  req.on("error", () => {
    if (!res.headersSent) { res.writeHead(400); res.end("request read error"); }
  });
});

if (require.main === module) {
  server.listen(PROXY_PORT, "127.0.0.1", () => {
    process.stderr.write(`[admission-proxy] listening on :${PROXY_PORT}, forwarding to ${CCR_HOST}:${CCR_PORT}\n`);
    process.stderr.write(`[admission-proxy] safe ceiling: ${SAFE_CEILING} (limit=${MAX_VERIFIED_LIMIT}, reserve=${OUTPUT_RESERVE})\n`);
  });
}

module.exports = { server, estimateTokens, SAFE_CEILING, MAX_VERIFIED_LIMIT, OUTPUT_RESERVE, CHAR_PER_TOKEN };
