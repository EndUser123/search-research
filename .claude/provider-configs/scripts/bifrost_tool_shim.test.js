const assert = require("node:assert/strict");
const test = require("node:test");

const {
  buildUpstreamUrl,
  normalizePayload,
} = require("./bifrost_tool_shim.js");

test("buildUpstreamUrl preserves the Claude Code path under the Bifrost origin", () => {
  assert.equal(
    buildUpstreamUrl("http://localhost:8080", "/anthropic/v1/messages?x=1"),
    "http://localhost:8080/anthropic/v1/messages?x=1",
  );
});

test("normalizePayload fills missing function.name from a top-level function tool name", () => {
  const payload = {
    model: "claude-haiku-4-5",
    tools: [
      {
        type: "function",
        name: "Read",
        function: {
          description: "Read a file",
          parameters: { type: "object" },
        },
      },
    ],
  };

  const result = normalizePayload(payload, { deepseek: true });

  assert.equal(result.changed, true);
  assert.equal(result.payload.tools[0].function.name, "Read");
  assert.equal(Object.hasOwn(result.payload.tools[0], "name"), false);
});

test("normalizePayload does not rewrite native Anthropic input_schema tools", () => {
  const payload = {
    model: "claude-haiku-4-5",
    tools: [
      {
        name: "Read",
        description: "Read a file",
        input_schema: { type: "object" },
      },
    ],
  };

  const result = normalizePayload(payload, { deepseek: false });

  assert.equal(result.changed, false);
  assert.deepEqual(result.payload, payload);
});

test("normalizePayload converts native Anthropic input_schema tools for DeepSeek requests", () => {
  const payload = {
    model: "claude-haiku-4-5-20251001",
    tools: [
      {
        name: "Read",
        description: "Read a file",
        input_schema: { type: "object", properties: {} },
      },
    ],
  };

  const result = normalizePayload(payload, { deepseek: true });

  assert.equal(result.changed, true);
  assert.deepEqual(result.payload.tools[0], {
    type: "function",
    function: {
      name: "Read",
      description: "Read a file",
      parameters: { type: "object", properties: {} },
    },
  });
});

test("normalizePayload drops empty OpenAI function tools", () => {
  const payload = {
    model: "claude-haiku-4-5",
    tools: [
      { type: "function", function: {} },
      {
        type: "function",
        function: { name: "Bash", parameters: { type: "object" } },
      },
    ],
  };

  const result = normalizePayload(payload, { deepseek: true });

  assert.equal(result.changed, true);
  assert.equal(result.payload.tools.length, 1);
  assert.equal(result.payload.tools[0].function.name, "Bash");
});

test("normalizePayload downgrades forced tool_choice only for DeepSeek requests", () => {
  const payload = {
    model: "claude-haiku-4-5",
    tool_choice: { type: "tool", name: "WebSearch" },
  };

  const deepseekResult = normalizePayload(payload, { deepseek: true });
  const nonDeepseekResult = normalizePayload(payload, { deepseek: false });

  assert.equal(deepseekResult.changed, true);
  assert.equal(deepseekResult.payload.tool_choice, "auto");
  assert.equal(nonDeepseekResult.changed, false);
  assert.deepEqual(nonDeepseekResult.payload, payload);
});
