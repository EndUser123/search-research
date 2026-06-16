"use strict";

const fs = require("node:fs");
const http = require("node:http");
const https = require("node:https");
const path = require("node:path");

const DEFAULT_PORT = 3005;
const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_UPSTREAM = "http://localhost:8080";
const DEFAULT_DEEPSEEK_MODELS = [
  "claude-haiku-4-5",
  "claude-haiku-4-5-20251001",
  "claude-sonnet-4-6",
  "deepseek-v4-flash",
  "deepseek-v4-pro",
  "opencode-go/deepseek-v4-flash",
  "opencode-go/deepseek-v4-pro",
];

function parseList(value, fallback) {
  if (!value || !value.trim()) return fallback;
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function isDeepseekRequest(payload, deepseekModels) {
  const model = typeof payload?.model === "string" ? payload.model : "";
  if (!model) return false;
  const normalized = model.toLowerCase();
  return deepseekModels.some((candidate) => normalized === candidate.toLowerCase());
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizePayload(payload, options = {}) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { payload, changed: false, actions: [] };
  }

  const result = cloneJson(payload);
  const actions = [];
  const deepseek = Boolean(options.deepseek);

  if (Array.isArray(result.tools)) {
    const tools = [];
    for (const tool of result.tools) {
      if (!tool || typeof tool !== "object" || Array.isArray(tool)) {
        tools.push(tool);
        continue;
      }

      const nextTool = { ...tool };
      if (
        deepseek &&
        nextTool.name &&
        nextTool.input_schema &&
        !nextTool.type &&
        !nextTool.function
      ) {
        tools.push({
          type: "function",
          function: {
            name: nextTool.name,
            description: nextTool.description || "",
            parameters: nextTool.input_schema,
          },
        });
        actions.push("converted_anthropic_tool");
        continue;
      }

      if (nextTool.type === "function") {
        const fn = nextTool.function;

        if (nextTool.name && (!fn || !fn.name)) {
          nextTool.function = { ...(fn || {}), name: nextTool.name };
          delete nextTool.name;
          actions.push("filled_function_name");
        }

        if (
          nextTool.function &&
          typeof nextTool.function === "object" &&
          !Array.isArray(nextTool.function) &&
          Object.keys(nextTool.function).length === 0
        ) {
          actions.push("dropped_empty_function_tool");
          continue;
        }
      }

      tools.push(nextTool);
    }
    result.tools = tools;
  }

  if (deepseek && result.tool_choice && typeof result.tool_choice === "object") {
    const forcedTypes = new Set(["tool", "any", "required"]);
    if (forcedTypes.has(result.tool_choice.type)) {
      result.tool_choice = "auto";
      actions.push("downgraded_tool_choice");
    }
  }

  return {
    payload: actions.length > 0 ? result : payload,
    changed: actions.length > 0,
    actions,
  };
}

function buildUpstreamUrl(upstreamOrigin, requestUrl) {
  const upstream = new URL(upstreamOrigin);
  const target = new URL(requestUrl, upstream);
  return target.toString();
}

function ensureLogDir(logPath) {
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
}

function appendLog(logPath, event) {
  if (!logPath) return;
  ensureLogDir(logPath);
  fs.appendFileSync(logPath, `${JSON.stringify({ ts: new Date().toISOString(), ...event })}\n`);
}

function createServer(config = {}) {
  const upstreamOrigin = config.upstreamOrigin || process.env.BIFROST_TOOL_SHIM_UPSTREAM || DEFAULT_UPSTREAM;
  const deepseekModels = parseList(
    config.deepseekModels || process.env.BIFROST_TOOL_SHIM_DEEPSEEK_MODELS,
    DEFAULT_DEEPSEEK_MODELS,
  );
  const mode = config.mode || process.env.BIFROST_TOOL_SHIM_MODE || "normalize";
  const logPath =
    config.logPath ||
    process.env.BIFROST_TOOL_SHIM_LOG ||
    path.join(process.env.APPDATA || process.cwd(), "bifrost", "tool-shim.log");

  return http.createServer((req, res) => {
    if (req.method === "OPTIONS") {
      res.writeHead(204, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "*",
      });
      res.end();
      return;
    }

    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const originalBody = Buffer.concat(chunks);
      let outboundBody = originalBody;
      let actions = [];
      let payloadModel = "";

      if (req.method === "POST" && originalBody.length > 0) {
        try {
          const parsed = JSON.parse(originalBody.toString("utf8"));
          payloadModel = typeof parsed?.model === "string" ? parsed.model : "";
          const deepseek = isDeepseekRequest(parsed, deepseekModels);
          const normalized = normalizePayload(parsed, { deepseek });

          if (mode === "normalize" && normalized.changed) {
            outboundBody = Buffer.from(JSON.stringify(normalized.payload));
          }
          actions = normalized.actions;
        } catch (error) {
          appendLog(logPath, {
            level: "warn",
            path: req.url,
            error: `invalid_json: ${error.message}`,
          });
        }
      }

      const headers = { ...req.headers };
      delete headers.host;
      delete headers["content-length"];
      delete headers["Content-Length"];
      if (outboundBody.length > 0) {
        headers["content-length"] = Buffer.byteLength(outboundBody);
      }

      const targetUrl = buildUpstreamUrl(upstreamOrigin, req.url);
      const target = new URL(targetUrl);
      const client = target.protocol === "https:" ? https : http;

      appendLog(logPath, {
        level: "info",
        mode,
        method: req.method,
        path: req.url,
        upstream: targetUrl,
        model: payloadModel,
        actions,
      });

      const proxyReq = client.request(
        target,
        {
          method: req.method,
          headers,
        },
        (proxyRes) => {
          res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
          proxyRes.pipe(res);
        },
      );

      proxyReq.on("error", (error) => {
        appendLog(logPath, {
          level: "error",
          path: req.url,
          error: error.message,
        });
        res.writeHead(502, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: `Bifrost tool shim proxy error: ${error.message}` }));
      });

      if (outboundBody.length > 0) {
        proxyReq.write(outboundBody);
      }
      proxyReq.end();
    });
  });
}

function main() {
  const host = process.env.BIFROST_TOOL_SHIM_HOST || DEFAULT_HOST;
  const port = Number.parseInt(process.env.BIFROST_TOOL_SHIM_PORT || `${DEFAULT_PORT}`, 10);
  const server = createServer();

  server.listen(port, host, () => {
    console.log(`Bifrost tool shim listening on http://${host}:${port}`);
  });
}

module.exports = {
  buildUpstreamUrl,
  createServer,
  isDeepseekRequest,
  normalizePayload,
};

if (require.main === module) {
  main();
}
