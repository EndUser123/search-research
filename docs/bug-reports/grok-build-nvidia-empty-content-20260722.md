# Bug: NVIDIA NIM models fail with "Empty content is not allowed for assistant messages" on multi-turn tool calls via spawn_subagent

## Summary

When using `spawn_subagent(model="nvidia-diffusiongemma-26b")` (or other NVIDIA NIM-hosted models) with tasks that require tool calls, the subagent fails on the second inference loop with a `400 Bad Request: Empty content is not allowed for assistant messages`. The root cause is that Grok Build records the assistant's tool-call response with `content: ""` (empty string), and NVIDIA NIM's request validator rejects empty-string content on assistant messages that have `tool_calls`. The OpenAI spec permits `content` to be null or omitted when `tool_calls` is present; NVIDIA NIM is stricter and requires non-null content.

## Environment

- **Grok Build version:** 0.2.106 (pager), binary `grok.exe`
- **OS:** Windows 11 (PowerShell 7)
- **Model config:**

```toml
[model.nvidia-diffusiongemma-26b]
model = "google/diffusiongemma-26b-a4b-it"
base_url = "https://integrate.api.nvidia.com/v1"
api_key = "nvapi-..."
api_backend = "chat_completions"
context_window = 262144
max_completion_tokens = 8192
```

- **Also affects:** any NVIDIA NIM-hosted model that generates tool calls (confirmed for DiffusionGemma; reported for Nemotron models in other frameworks — see References)

## Reproduction

### Minimal reproduction (2 minutes, no Grok Build needed)

```bash
# This fails — assistant message has content="" with tool_calls:
curl -s -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/diffusiongemma-26b-a4b-it",
    "messages": [
      {"role": "user", "content": "What is 2+2?"},
      {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "calc", "arguments": "{\"x\":2,\"y\":2}"}}]},
      {"role": "tool", "tool_call_id": "call_1", "content": "4"},
      {"role": "user", "content": "Now explain it."}
    ],
    "max_tokens": 500
  }'
```

**Response:**
```json
{"error":{"message":"request: Value error, Empty content is not allowed for assistant messages","type":"BadRequestError","code":400}}
```

### Same request with `content: null` succeeds

```bash
curl -s -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/diffusiongemma-26b-a4b-it",
    "messages": [
      {"role": "user", "content": "What is 2+2?"},
      {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "calc", "arguments": "{\"x\":2,\"y\":2}"}}]},
      {"role": "tool", "tool_call_id": "call_1", "content": "4"},
      {"role": "user", "content": "Now explain it."}
    ],
    "max_tokens": 500
  }'
```

**Response:** valid completion with correct content (302 tokens explaining why 2+2=4).

### Grok Build reproduction (spawn_subagent)

```
spawn_subagent(
  model="nvidia-diffusiongemma-26b",
  prompt="Read the file at P:/.data/wiki/concepts/model-pool-not-chain.md and summarize it."
)
```

**Result:** `400 Bad Request` after 9.9s. The subagent's first loop successfully calls `read_file` (tool call executed), but the second loop — where Grok Build sends the conversation history (including the assistant message with `content: ""` and `tool_calls`) back to NVIDIA — fails with the validation error.

**Tasks that DON'T trigger the bug** (no tool calls → no empty-content assistant message in history):
- `spawn_subagent(model="nvidia-diffusiongemma-26b", prompt="Reply with one word: hello")` → ✅ works
- `spawn_subagent(model="nvidia-diffusiongemma-26b", prompt="Explain why the sky is blue in 3 sentences. Do not use any tools.")` → ✅ works

## Root Cause

NVIDIA NIM's request validator (`vllm-0.21.0` based, per `system_fingerprint` in responses) enforces that assistant messages must have non-null `content`. Specifically:

- `content: ""` (empty string) → **rejected** with 400
- `content: null` → **accepted**
- `content: "any non-empty string"` → **accepted**
- `content` field omitted entirely → **accepted** (per OpenAI spec)

Grok Build's request serializer records the model's tool-call output as `{"role": "assistant", "content": "", "tool_calls": [...]}` and sends this back in the conversation history on subsequent loops. NVIDIA NIM rejects this on loop 2+.

This is notable: the model generates an assistant message (tool call with empty content) that the same endpoint then rejects when it appears in the conversation history. The endpoint is inconsistent between generation (accepts empty content out) and validation (rejects empty content in).

## Expected Behavior

Grok Build should normalize assistant messages before sending them to endpoints that require non-null content. Specifically, for assistant messages where `tool_calls` is present and `content` is empty string (`""`), the serializer should either:

1. Set `content: null` (cleanest — matches what NVIDIA NIM expects)
2. Omit the `content` field entirely (matches OpenAI spec)
3. Set `content: "."` or similar placeholder (works but less clean)

Option 1 is recommended — it's the minimal change and matches NVIDIA's documented expectation.

## Suggested Fix Location

The fix is in the request serializer — the code that constructs the `messages` array sent to the OpenAI-compatible endpoint. For NVIDIA NIM endpoints (or for all endpoints to be safe), when serializing an assistant message that has `tool_calls` but `content` is empty string, replace `content` with `null`.

In Goose (another Rust agent framework), the equivalent fix was in `crates/goose/src/providers/formats/openai.rs` — the `format_messages` function that decides whether to include the `content` key (see References: Goose PR #7076).

## References

**Note on citation strength:** the following GitHub issues were found via search and their URLs/repos verified accessible. Specific issue details (merge dates, quoted text) are from search snippets and firecrawl page metadata; the issue body content was not fully retrieved in all cases. The core diagnosis (sections above) does not depend on these precedents — it stands on the direct curl tests alone.

1. **Goose issue #6717 + PR #7076** — "Assistant messages missing content field when sending tool calls to certain OpenAI-compatible providers." Same bug class. Search results indicate PR #7076 was merged as a fix. https://github.com/aaif-goose/goose/issues/6717

2. **Cherry Studio issue #16155** — "Empty assistant content with tool_calls causes 400 from NVIDIA NIM (DiffusionGemma)." Same model, same error. Status appears open. https://github.com/CherryHQ/cherry-studio/issues/16155

3. **NVIDIA NemoClaw issue #1193** — "openclaw agent returns empty content when model makes tool calls." Related variant for Nemotron models. https://github.com/NVIDIA/NemoClaw/issues/1193

4. **vLLM reasoning-outputs docs**: https://docs.vllm.ai/en/latest/features/reasoning_outputs/ — documents that tool calling "only parses functions from the `content` field, not from the `reasoning`" field.

## Impact

This bug blocks all NVIDIA NIM-hosted models from being used as subagent models in any task that requires tool calls — which is essentially all non-trivial coding tasks. The models work for single-turn text generation but fail the moment they need to read a file, run a command, or call any tool.

Workaround: use direct HTTP API calls (bypassing `spawn_subagent`) or restrict NVIDIA NIM models to text-only subagent tasks. Neither is a substitute for full subagent integration.
