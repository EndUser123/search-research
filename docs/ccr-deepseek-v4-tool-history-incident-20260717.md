# CCR / OpenCode Go / DeepSeek V4 Tool-History Incident

## Review purpose

This document records the Claude Code → admission proxy → CCR → OpenCode Go failure involving `opencode-go/deepseek-v4-flash`, the task self-documentation errors observed in the same session, the research performed, the fixes attempted, the current safe routing decision, and the remaining review questions.

It is written for independent review. Facts, measurements, inferences, hypotheses, and unresolved questions are separated deliberately.

## Status

**Current status:** mitigated in the custom router; live end-to-end confirmation is still required after restarting CCR.

**Date:** 2026-07-17

**Affected path:** Claude Code tool-use requests routed through CCR to OpenCode Go DeepSeek V4 Flash.

**Current mitigation:** requests that combine an OpenCode Go route with tools and active thinking or prior assistant tool/reasoning history are rerouted to `minimax,MiniMax-M3[1m]`.

## Executive summary

The visible HTTP 400 was not caused by Claude authentication, local llama.cpp VRAM, or the task self-documentation hook. It was a provider-format compatibility failure in the DeepSeek V4 tool/reasoning path.

DeepSeek V4 requires reasoning state to be replayed on subsequent assistant/tool turns. In the OpenAI-compatible form this is `assistant.reasoning_content`; in the Anthropic-compatible form it is a `thinking` content block. The CCR/OpenCode Go conversion path can lose that state, and related paths can also emit malformed tool schemas.

The first attempted JavaScript fix handled only one part of the problem: it removed top-level `thinking` for tool-bearing OpenCode Go requests, including `adaptive` thinking. That was insufficient for multi-turn replay because deleting the thinking block does not provide the required `reasoning_content` history.

Research indicates that the ideal fix belongs inside the provider transformer or the response/history conversion layer. The custom CCR router runs before the relevant CCR transformation and cannot guarantee that an arbitrary injected `message.reasoning_content` field survives. The current mitigation therefore routes unsafe DeepSeek tool-history requests to MiniMax M3, which has the required context capacity and a compatible Anthropic route.

## User-visible symptoms

### Provider error

```text
API Error: 400 Error from provider(opencode-go,deepseek-v4-flash: 400):
{"error":{"message":"Error from provider (Console Go): Upstream request failed",
"type":"invalid_request_error","param":null,"code":"invalid_request_error"}}
```

The CCR stack terminated in the installed router bundle:

```text
C:\Users\brsth\AppData\Roaming\npm\node_modules\@musistudio\claude-code-router\dist\cli.js
```

### Task self-documentation errors

The same session also showed repeated local hook failures:

```text
Task self-documentation incomplete.
Missing: Problem (...), Situation (...), Symptom (...)
```

These were separate. The local hook blocked TaskCreate/TaskUpdate calls because its validator searched for indicator words while the documentation described labelled fields. This was not the cause of the provider 400.

## Verified local facts

### Routing evidence

The local route log recorded requests selected for OpenCode Go because the local model was unavailable or the request exceeded the local effective context:

```text
effective_route_alias: opencode-go,deepseek-v4-flash
backend_provider: opencode-go
backend_model: deepseek-v4-flash
decision_source: local-fail-fallback
reason: over-ctx: 93736 > 58982 local ctx
body_has_tools: true
body_thinking_type: adaptive
body_has_thinking_blocks: true
```

Relevant local evidence:

- `P:/.claude/state/ccr-route-log.jsonl`
- `C:/Users/brsth/.claude-code-router/logs/`
- `C:/Users/brsth/.claude-code-router/config.json`

### CCR configuration

The active configuration contains:

```text
opencode-go/deepseek-v4-flash
```

as the local-failure and background fallback, with fallback chains including OpenCode Zen free. MiniMax M3 and Z.ai GLM-5.2 are also configured as 1M-context cloud routes.

### Task-validator authority

The active hook is:

- `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py`
- `P:/.claude/hooks/__lib/task_self_doc_validator.py`
- `P:/.claude/hooks/tests/test_task_self_doc_gate.py`

The validator originally used indicators such as `bug`, `error`, `when`, `returns`, and `exception`. The local contract in `C:/Users/brsth/.claude/CLAUDE.md` documented explicit `Problem:`, `Situation:`, and `Symptom:` fields. The validator was updated to recognize those labels while retaining legacy indicator compatibility.

## Reproduction model

The failure is most likely after a tool call, not on a simple first request:

```text
Turn 1: user request
  → DeepSeek V4 returns reasoning_content + tool_calls

Turn 2: tool result is returned with prior assistant history
  → conversion loses reasoning_content
  → DeepSeek validates thinking-mode history
  → HTTP 400
```

The key trigger is assistant tool/reasoning history. A request containing tools alone may still work if it has no prior assistant tool/reasoning turn.

## Internet research

### DeepSeek V4 / CCR issue #1378

[CCR issue #1378](https://github.com/musistudio/claude-code-router/issues/1378) reports the same DeepSeek V4 Pro/Flash failure. Its reproduction and analysis state that, after tool use, DeepSeek requires `reasoning_content` on the OpenAI endpoint or a `thinking` block on the Anthropic endpoint. A direct request with `reasoning_content: ""` reportedly succeeds.

The issue also reports that, on the affected `/v1/messages` tool-use path:

- the configured DeepSeek transformer may not run;
- custom transformers may not be registered;
- an `api_base_url` proxy may not receive the request;
- the request may go through a hard-coded provider path.

The issue proposes either a built-in DeepSeek transformer fix or making the configured transformer/endpoint extensibility work on that path.

### OpenCode issue #24190

[OpenCode issue #24190](https://github.com/anomalyco/opencode/issues/24190) independently reports DeepSeek V4 Pro/Flash failures beginning on the second turn after tool use. It identifies loss of `reasoning_content` while reconstructing assistant history as the cause and recommends preserving the field verbatim or supplying an empty field where appropriate.

### OpenCode issue #24224

[OpenCode issue #24224](https://github.com/anomalyco/opencode/issues/24224) reports another OpenCode Go / DeepSeek V4 tool failure: `tools[0].function.name` is missing after Anthropic-to-OpenAI conversion. Direct DeepSeek works, MiniMax through OpenCode Go works, but DeepSeek V4 through the affected proxy path fails.

### Other related model failures

The same class of boundary problem appears elsewhere:

- Kimi K2.6 and Qwen3-Coder can reject a generic `reasoning` field that CCR emits even when the model does not support it. See the CCR issue index and issue #1411.
- Qwen 3 reasoning/tool-call streaming can corrupt tool-call argument deltas. See CCR issue #1397.
- Gemini tool calls can require a `thought_signature` that is lost during conversion. See [CCR issue #1018](https://github.com/musistudio/claude-code-router/issues/1018).
- Some Kimi paths fail when assistant tool-call history does not preserve reasoning content. See CCR issue #1404.
- OpenClaw reports both DeepSeek tool-schema failures and a separate risk where fallback reasoning text leaks into the user-visible response. See [OpenClaw issue #71683](https://github.com/openclaw/openclaw/issues/71683).

These are not all the same provider bug. They share a common architectural pattern: an Anthropic request is converted into provider-specific OpenAI/tool/reasoning semantics, but the conversion is lossy or provider capability assumptions are too broad.

## Remediation options considered

### Option A: Inject `reasoning_content` in the custom router

**Benefit:** small and directly matches the DeepSeek requirement.

**Risk:** the custom router executes before CCR’s provider transformation. The field may be dropped when CCR constructs its internal OpenAI message. It is therefore not sufficient evidence of a fix unless verified against a real multi-turn provider request.

**Decision:** not selected as the sole mitigation.

### Option B: Patch the installed CCR bundle

**Benefit:** can modify the exact transformer path that constructs outbound messages.

**Risk:** the installed `dist/cli.js` is generated package code; upgrades overwrite the patch, and it creates an untracked runtime fork.

**Decision:** rejected as the production solution; acceptable only as a temporary diagnostic experiment.

### Option C: Add a true custom provider transformer/proxy

**Benefit:** architectural fix if CCR reliably invokes it; can preserve `reasoning_content`, normalize tools, and keep DeepSeek available.

**Risk:** research reports that the affected tool-use path may bypass custom transformer and `api_base_url` hooks. It also requires a response/history capture mechanism, not just request mutation.

**Decision:** best long-term fix if CCR’s path can be proven to invoke it; requires a separate integration experiment.

### Option D: Capability-aware route away from unsafe DeepSeek histories

**Benefit:** deterministic, reversible, does not mutate chain-of-thought, uses an existing 1M-context provider, and does not depend on an unreliable transformer hook.

**Cost:** DeepSeek V4 is unavailable for affected tool-history requests, and MiniMax quota is consumed instead.

**Decision:** selected as the current production mitigation.

## Current implementation

The custom router is:

- `P:/.claude/provider-configs/ccr-custom-router.js`

The router detects an OpenCode Go route combined with:

- tools plus active `thinking`/`adaptive` mode; or
- assistant `tool_calls`; or
- assistant `thinking`, `redacted_thinking`, or `tool_use` history.

It changes the route to:

```text
minimax,MiniMax-M3[1m]
```

and logs a reason containing:

```text
DeepSeek tool-history compatibility fallback
```

The regression tests are in:

- `P:/.claude/provider-configs/ccr-custom-router.test.js`

The test suite verifies both:

1. unsafe adaptive/tool-history requests route to MiniMax;
2. simple tool requests without unsafe history retain the economical DeepSeek fallback.

## Quota and fallback policy

This incident is a 400 compatibility failure, not a quota failure.

Quota failures should be identified separately through CCR provider response logs:

- HTTP `429`;
- `rate_limit_error`;
- quota/usage-limit text;
- provider request ID;
- CCR fallback events such as `Request failed ... trying fallback models`.

The intended policy is:

```text
429 from provider
  → record provider cooldown
  → skip provider temporarily
  → choose task/context-compatible alternate provider
  → do not blindly retry the exhausted provider
```

The current static fallback chains are sensible but do not yet implement a persistent provider circuit breaker. That is a separate follow-up work item.

## Verification completed

Before this document was written:

- Python task-validator tests: 65 passed.
- CCR Node tests after the routing mitigation: 48 passed.
- CCR PowerShell/Pester tests: 11 passed.
- Python and JavaScript syntax checks passed.
- `git diff --check` passed for focused files.

These tests prove routing decisions and local transformations. They do **not** prove that a live Claude Code multi-turn request succeeds through OpenCode Go or MiniMax.

## Required live verification

Because CCR loads the custom router into the running Node process, restart CCR after changing the JavaScript:

```powershell
cc-ccr -Stop
cc-ccr
```

Then run a controlled Claude Code task that performs at least one tool call and a follow-up turn. Verify:

1. The request does not return the DeepSeek 400.
2. The CCR route log records `provider-compatibility` and MiniMax for unsafe history.
3. The MiniMax response completes the tool-use turn.
4. A simple no-history tool request still uses DeepSeek if desired.
5. A genuine 429 produces a different classification from the 400 compatibility fallback.

## Review questions for the next LLM

1. Can the installed CCR version be configured so the DeepSeek request transformer is guaranteed to run on `/v1/messages` tool-history requests?
2. Can a response-aware, upgrade-safe transformer preserve actual `reasoning_content` rather than supplying an empty placeholder?
3. Does MiniMax M3 preserve Claude Code tool semantics across the same multi-turn workload?
4. Should all DeepSeek V4 tool-bearing requests be routed away, or only requests with prior assistant tool/reasoning history?
5. Should the provider capability matrix become a shared authority consumed by CCR router, admission proxy, and display?
6. Can quota state be recorded with cooldown and provider-specific circuit breaking without creating cross-terminal races?
7. Are fallback responses guaranteed not to expose internal reasoning text to the user?

## Bottom line

The internet-reported root cause matches the local evidence: DeepSeek V4 tool-history requests require reasoning-state round-trip, and the current CCR conversion path can lose it. The selected mitigation is capability-aware routing to MiniMax for unsafe histories. A true permanent fix requires changing or replacing the CCR transformer path that constructs the outbound provider request, followed by a live multi-turn verification.
