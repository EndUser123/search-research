# CCR Task Context Shaper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce oversized CCR requests by removing only provably stale tool outputs and safely selecting explicitly tagged task-relevant system sections before admission counting, while preserving the original request for recovery and fail-open behavior.

**Architecture:** Add a small pure Node module in front of CCR. It receives an Anthropic `/v1/messages` JSON body, produces a shaped copy plus telemetry, and never mutates the caller's body. The first implementation is conservative: it compacts repeated tool results by resource identity and filters only system content blocks carrying an explicit task-scope marker; opaque system text, user messages, tool schemas, and tool-call/result pairing remain untouched. The admission proxy shapes first, recounts the shaped body, and forwards the shaped body. On any shaper error, it forwards the original body.

**Tech Stack:** Node.js CommonJS, `node:test`, `node:assert/strict`, existing CCR admission proxy.

## Global Constraints

- Do not modify the active live files until the disposable copy passes all checks.
- Preserve the existing admission proxy's fail-closed size gate and fail-open behavior for malformed JSON or shaper failures.
- Never split an assistant tool call from its matching tool result.
- Never remove opaque system content, user messages, tool definitions, or write/edit/task state in the first slice.
- Use only deterministic transformations; no additional LLM call is introduced.
- Keep the original request available in memory for same-request fallback and log only hashes/metadata, not raw prompt contents.
- Preserve unrelated user changes in the dirty workspace.

---

### Task 1: Create an isolated copy and establish the baseline

**Files:**
- Create: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-admission-proxy.js`
- Create: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.js`
- Create: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.test.js`

**Interfaces:**
- `shapeAnthropicRequest(body, options?) -> { body, changed, telemetry }`
- `estimateTokens(body) -> { inputEstimate, maxTokens, total }` remains compatible with the existing proxy.

- [x] Copy the live admission proxy into the isolated directory without changing the live source.
- [x] Add a minimal shaper module exporting the public function and returning an unchanged deep copy.
- [x] Add baseline tests for unchanged requests, malformed/non-array messages, and deep-copy non-mutation.
- [x] Run `node --check` and `node --test` in the isolated directory.

Expected: baseline tests pass before behavior is added.

### Task 2: Implement stale tool-result compaction

**Files:**
- Modify: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.js`
- Test: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.test.js`

**Interfaces:**
- Resource identity is derived only from the matching assistant tool-use block: tool name plus normalized `file_path`/`path`, command, query, or tool-call id.
- The newest result for an identity remains verbatim; older results become a compact explicit stub.

- [x] Add a test proving two reads of the same file preserve the newest output and replace only the older output.
- [x] Add a test proving different pagination ranges are not treated as duplicates.
- [x] Add a test proving unknown/unpaired tool results remain unchanged.
- [x] Add a test proving write/edit/task tool results are protected.
- [x] Implement identity extraction and stale-result replacement with telemetry for `compacted_count`, `bytes_saved`, `resource_count`, and `failed_open`.
- [x] Run the focused shaper tests and syntax checks.

Expected: only superseded, non-protected tool outputs are replaced; all tool-call/result pairs remain structurally present.

### Task 3: Add explicitly scoped system-section filtering

**Files:**
- Modify: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.js`
- Test: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.test.js`

**Interfaces:**
- A system content block is eligible only when it is an object with `cache_control`-independent text containing an explicit marker such as `<context-scope task="...">...</context-scope>`.
- Unmarked system strings, ordinary system blocks, user messages, and tools are preserved exactly.

- [x] Add tests for marked relevant and irrelevant sections.
- [x] Add tests proving unmarked system text and all tools remain byte-equivalent.
- [x] Implement filtering only when `CCR_CONTEXT_SYSTEM_SCOPES` is explicitly configured; default remains preserve-all.
- [x] Ensure filtering telemetry records selected/dropped section hashes without raw contents.
- [x] Run the focused tests and inspect serialized request shape.

Expected: the first live rollout can enable stale-result pruning while leaving system filtering opt-in and inert unless explicitly configured.

### Task 4: Wire shaping into the isolated admission proxy

**Files:**
- Modify: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-admission-proxy.js`
- Test: `P:/tmp/ccr-context-shaper-20260712/.claude/provider-configs/ccr-context-shaper.test.js`

**Interfaces:**
- The proxy parses JSON, shapes a copy, estimates shaped size, logs raw/shaped estimates, then forwards the shaped JSON.
- If shaping fails, the proxy logs `failed_open=true` and forwards the original body for normal admission handling.

- [x] Add a replay test with a request whose raw estimate exceeds the local-safe threshold but whose stale tool output compacts below it.
- [x] Add a replay test proving a genuinely oversized request is still rejected after shaping.
- [x] Add a replay test proving shaper failure forwards the original request and does not silently bypass admission.
- [x] Wire shaping before `estimateTokens` and preserve existing HTTP status/error behavior.
- [x] Run syntax checks, focused unit tests, and a local HTTP replay against the isolated proxy.

Expected: the isolated proxy forwards shaped requests only when the shaped body passes the existing gate; otherwise it preserves the existing rejection path.

### Task 5: Promote the verified copy to live source

**Files:**
- Modify: `P:/.claude/provider-configs/ccr-admission-proxy.js`
- Create or modify: `P:/.claude/provider-configs/ccr-context-shaper.js`
- Create or modify: `P:/.claude/provider-configs/ccr-context-shaper.test.js`

- [x] Compare isolated and live diffs, excluding unrelated workspace changes.
- [x] Apply only the verified files to the live source path.
- [x] Run `node --check` on live files.
- [x] Run `node --test .claude/provider-configs/ccr-context-shaper.test.js`.
- [x] Run the existing CCR router test suite.
- [x] Run `git diff --check` and inspect the final diff for secrets, prompt leakage, and unrelated edits.
- [x] Report exact verification results and remaining runtime restart limitation; live behavior requires the proxy process to be restarted.

Expected: live source has the verified implementation, existing routing tests remain green, and the admission log exposes raw versus shaped counts without raw content. Runtime activation remains pending a CCR/admission-proxy restart.
