"use strict";

// Conservative request shaping for Anthropic-compatible CCR traffic.
// Only superseded non-mutating tool results and explicitly scoped system
// blocks are eligible. Opaque system text, user content, tool definitions,
// and write/edit/task state remain untouched.

const PROTECTED_TOOLS = new Set([
  "write", "edit", "task", "skill", "todowrite", "todoread",
  "plan_enter", "plan_exit", "compress", "batch",
]);
const RESOURCE_KEYS = [
  "file_path", "filepath", "path", "filename", "AbsolutePath",
  "TargetFile", "target_file", "command", "CommandLine", "cmd",
  "query", "Query", "pattern",
];
const PAGINATION_KEYS = [
  "offset", "start_line", "StartLine", "line_offset", "from_line",
  "limit", "max_lines", "MaxLines", "end_line", "EndLine", "num_lines", "count",
];

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function asObject(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value;
  if (typeof value !== "string") return null;
  try { return asObject(JSON.parse(value)); } catch { return null; }
}

function normalizeValue(value) {
  return String(value).trim().replace(/\\/g, "/").replace(/\/+/g, "/").toLowerCase();
}

function extractToolName(block) {
  return typeof block?.name === "string" ? block.name.trim().toLowerCase() : null;
}

function extractResourceKey(toolUse) {
  const input = asObject(toolUse?.input);
  if (!input) return null;
  for (const key of RESOURCE_KEYS) {
    const value = input[key];
    if (typeof value === "string" && value.trim()) {
      const pagination = PAGINATION_KEYS
        .filter((paginationKey) => input[paginationKey] !== undefined)
        .map((paginationKey) => `${paginationKey}=${normalizeValue(input[paginationKey])}`)
        .join("&");
      const base = `${extractToolName(toolUse) || "unknown"}:${normalizeValue(value)}`;
      return pagination ? `${base}?${pagination}` : base;
    }
  }
  return null;
}

function indexToolUses(messages) {
  const index = new Map();
  for (const message of messages) {
    if (message?.role !== "assistant" || !Array.isArray(message.content)) continue;
    for (const block of message.content) {
      if (block?.type === "tool_use" && typeof block.id === "string") index.set(block.id, block);
    }
  }
  return index;
}

function filterScopedSystemContent(system, scopes) {
  if (!Array.isArray(system) || !Array.isArray(scopes) || scopes.length === 0) {
    return { system, dropped: 0, droppedHashes: [] };
  }
  const crypto = require("node:crypto");
  const allowed = new Set(scopes.map((scope) => String(scope).trim().toLowerCase()).filter(Boolean));
  const droppedHashes = [];
  const filtered = [];
  for (const block of system) {
    const text = typeof block?.text === "string" ? block.text : "";
    const match = text.match(/<ccr-context\s+scope="([^"]+)"\s*>[\s\S]*?<\/ccr-context>/i);
    if (!match || allowed.has(match[1].trim().toLowerCase())) {
      filtered.push(block);
      continue;
    }
    droppedHashes.push(crypto.createHash("sha256").update(text).digest("hex").slice(0, 16));
  }
  return { system: filtered, dropped: droppedHashes.length, droppedHashes };
}

function shapeAnthropicRequest(body, options = {}) {
  const original = body && typeof body === "object" ? body : {};
  const shaped = cloneJson(original);
  const originalBytes = Buffer.byteLength(JSON.stringify(original), "utf8");
  const messages = Array.isArray(shaped.messages) ? shaped.messages : [];
  const toolUses = indexToolUses(messages);
  const protectedTools = new Set(options.protectedTools || PROTECTED_TOOLS);
  const occurrences = new Map();

  for (let messageIndex = 0; messageIndex < messages.length; messageIndex += 1) {
    const message = messages[messageIndex];
    if (message?.role !== "user" || !Array.isArray(message.content)) continue;
    for (let blockIndex = 0; blockIndex < message.content.length; blockIndex += 1) {
      const block = message.content[blockIndex];
      if (block?.type !== "tool_result" || typeof block.tool_use_id !== "string") continue;
      const toolUse = toolUses.get(block.tool_use_id);
      const toolName = extractToolName(toolUse);
      const resourceKey = extractResourceKey(toolUse);
      if (!toolUse || !toolName || !resourceKey || protectedTools.has(toolName)) continue;
      const list = occurrences.get(resourceKey) || [];
      list.push({ messageIndex, blockIndex, toolUseId: block.tool_use_id, toolName });
      occurrences.set(resourceKey, list);
    }
  }

  let compactedCount = 0;
  let bytesSaved = 0;
  const compactedResources = [];
  for (const [resourceKey, list] of occurrences.entries()) {
    if (list.length < 2) continue;
    const latest = list[list.length - 1];
    let replaced = 0;
    for (const occurrence of list.slice(0, -1)) {
      const message = messages[occurrence.messageIndex];
      const block = message.content[occurrence.blockIndex];
      const before = JSON.stringify(block.content ?? "");
      const stub = `[CCR-COMPACTED] Earlier ${occurrence.toolName} result for ${resourceKey} was superseded by a newer result later in this request.`;
      const after = JSON.stringify(stub);
      const saved = Buffer.byteLength(before, "utf8") - Buffer.byteLength(after, "utf8");
      if (saved <= 0) continue;
      message.content[occurrence.blockIndex] = { ...block, content: stub };
      compactedCount += 1;
      bytesSaved += saved;
      replaced += 1;
    }
    if (replaced > 0) compactedResources.push({ resourceKey, retainedToolUseId: latest.toolUseId, replaced });
  }

  const systemResult = filterScopedSystemContent(shaped.system, options.systemScopes);
  if (systemResult.dropped > 0) shaped.system = systemResult.system;
  const shapedBytes = Buffer.byteLength(JSON.stringify(shaped), "utf8");
  return {
    body: shaped,
    changed: compactedCount > 0 || systemResult.dropped > 0,
    telemetry: {
      failed_open: false,
      raw_bytes: originalBytes,
      shaped_bytes: shapedBytes,
      bytes_saved: Math.max(0, originalBytes - shapedBytes),
      compacted_count: compactedCount,
      compacted_resources: compactedResources,
      system_blocks_dropped: systemResult.dropped,
      system_blocks_dropped_hashes: systemResult.droppedHashes,
    },
  };
}

module.exports = { PROTECTED_TOOLS, shapeAnthropicRequest };
