---
title: "NVIDIA NIM rejects empty content on assistant messages with tool_calls — the DiffusionGemma spawn_subagent root cause"
created: 2026-07-22
source: session-2026-07-22
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
tags: [nvidia-nim, diffusiongemma, spawn-subagent, empty-content, tool-calls, openai-compat, validator, root-cause, grok-build, bug-report]
summary: >
  NVIDIA NIM's OpenAI-compatible validator rejects assistant messages where content is empty string ("")
  when tool_calls is present — stricter than the OpenAI spec, which permits content to be null or omitted.
  This causes spawn_subagent to fail on loop 2+ of any tool-use task for NVIDIA-hosted models
  (DiffusionGemma, Nemotron). The fix: send content: null instead of content: "". Verified via
  direct curl, with 3 independent GitHub precedents (Cherry Studio, Goose, NemoClaw).

---

# NVIDIA NIM rejects empty content on assistant messages with tool_calls

## The failure

When using `spawn_subagent(model="nvidia-diffusiongemma-26b")` (or other NVIDIA NIM-hosted models) with tasks requiring tool calls, the subagent fails on the second inference loop:

```
API error (status 400 Bad Request): BadRequestError: request: Value error,
Empty content is not allowed for assistant messages
```

## Root cause (HIGH confidence, verified via direct curl)

**NVIDIA NIM's request validator is stricter than the OpenAI spec.** It rejects assistant messages where `content` is empty string (`""`) when `tool_calls` is present. The OpenAI spec permits `content` to be null or omitted in this case.

**How it triggers:**
1. Loop 1: model emits a tool call with empty content (standard OpenAI convention)
2. Grok Build records: `{"role":"assistant","content":"","tool_calls":[...]}`
3. Loop 2: Grok sends conversation history back to NVIDIA
4. NVIDIA rejects its own previous output

**Why trivial tasks work:** no tool calls → no empty-content assistant messages in history → no validation failure.

## Verified fix (direct curl, 2026-07-22)

| Request shape | Result |
|---|---|
| `content: ""` + `tool_calls` | ❌ 400: Empty content is not allowed |
| `content: null` + `tool_calls` | ✅ Works (302 tokens, correct response) |
| `content: "placeholder"` + `tool_calls` | ✅ Works |
| `content` omitted + `tool_calls` | ✅ Works (per OpenAI spec) |

**Recommended fix:** `content: null` (cleanest — matches what NVIDIA NIM expects).

## Layer isolation (the breakthrough test)

Direct curl to `https://integrate.api.nvidia.com/v1/chat/completions` with no Grok Build in the loop reproduces the exact same 400 error. **The failure is at NVIDIA NIM, not at Grok Build's serializer.** Grok faithfully sends what the model generated; NVIDIA rejects its own output when it appears in conversation history.

## GitHub precedents (3 independent frameworks, same bug class)

| Repo | Issue | Status | Match |
|---|---|---|---|
| `CherryHQ/cherry-studio#16155` | Exact same model (DiffusionGemma), exact same error | Open, inactive | Direct match |
| `aaif-goose/goose#6717` | Same pattern for strict OpenAI-compat providers | **Closed via PR #7076** (merged Feb 11, 2026) | Fix proven |
| `NVIDIA/NemoClaw#1193` | Same pattern for Nemotron models | Closed via PR #2380 (Apr 23, 2026) | Related variant |

**No existing issue in `xai-org/grok-build`** for this bug. Bug report drafted at `P:/docs/bug-reports/grok-build-nvidia-empty-content-20260722.md`.

## Hypotheses eliminated (with receipts)

| Hypothesis | Why wrong | Test that refuted it |
|---|---|---|
| Thinking-mode conflict | `reasoning_tokens: 0` but trivial tasks succeed | spawn_subagent trivial test returned "hello" successfully |
| Tool-calling pattern mismatch | Tool calls work fine; it's the history that triggers the validator | read_file succeeded on loop 1; failure was on loop 2 |
| `max_tokens < 256` | Config has 8192; failure persists | `dgemma-gemini-flash-operational-tests-2026-07-22.md` documented this |
| `<\|channel\|>thought` format causes the 400 | Markers leak into SUCCESS cases too | Multi-turn no-tools test succeeded WITH markers visible |
| `force_nonempty_content` parameter | All 3 placements (root, extra_body, chat_template_kwargs) still 400 | Direct curl tests 1-3 |
| Failure at Grok Build's serializer | Direct curl reproduces with no Grok in the loop | Layer isolation test |

## Fix paths

| Path | Mechanism | Effort | Dependency |
|---|---|---|---|
| **A (recommended)** | Grok Build patches serializer: `content: null` when assistant has tool_calls + empty content | One-line fix in request builder | xAI ships the patch |
| B | Local HTTP proxy that rewrites `content: ""` → `null` | ~50 lines Python | Self-hosted; maintenance |
| C | NVIDIA relaxes validator to match OpenAI spec | One bug report to NVIDIA | NVIDIA ships (slow) |

## Methodology lessons

1. **Layer isolation is the foundation test.** The testing-methodology-both-outcomes-informative wiki page explicitly requires it. Skipping it led to 4 turns of wrong hypotheses before the direct curl test revealed the failure is at NVIDIA.
2. **`/tp` critique caught real gaps.** The fresh subagent identified that layer isolation wasn't performed, that two failure modes were being conflated, and that the NeMoClaw citation was initially unverified. All three were correct.
3. **Wiki pages may already document the answer.** `dgemma-gemini-flash-operational-tests-2026-07-22.md` had already documented the max_tokens fix and flagged "not yet tested via spawn_subagent." The investigation re-derived what the wiki already knew before discovering the deeper cause.

## Related

- [[dgemma-gemini-flash-operational-tests-2026-07-22]] — operational test results including the max_tokens<256 finding
- [[diffusiongemma-direct-api-howto]] — direct API workaround (bypasses spawn_subagent)
- [[diffusiongemma-optimal-usage-dos-and-donts]] — general DGemma best practices
- [[model-lanes-vs-roles]] — where DGemma fits in the model fleet
- [[testing-methodology-both-outcomes-informative]] — the layer-isolation methodology that should have been applied from the start

## Sources

- Direct curl tests to `https://integrate.api.nvidia.com/v1/chat/completions` (5 tests, 2026-07-22)
- `C:\Users\brsth\.grok\logs\unified.jsonl` — spawn_subagent failure logs (4 failures, 4 successes)
- `P:/docs/bug-reports/grok-build-nvidia-empty-content-20260722.md` — full bug report with repro
- GitHub: CherryHQ/cherry-studio#16155, aaif-goose/goose#6717 (PR #7076), NVIDIA/NemoClaw#1193 (PR #2380)
- `P:/.data/wiki/concepts/testing-methodology-both-outcomes-informative.md` — layer isolation methodology

## Auto-related

- [[python-behavior-tree-framework-for-autonomous-llm-agents--technical-specificatio]]

