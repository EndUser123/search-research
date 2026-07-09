# Handoff: Fix CCR → opencode-go interop (400 on subagent payloads)

**Status:** open · **Created:** 2026-07-08 · **Scope:** claude-code-router 2.0.0 ↔ opencode-go provider
**Severity:** Med — blocks all haiku/background subagent dispatch; main-loop and other providers unaffected.

---

## 1. The problem (one paragraph)

Subagent dispatches that route to the `opencode-go` provider fail with HTTP 400 `{"message":"Error from provider (Console Go): Upstream request failed","type":"invalid_request_error"}`. This kills any `Agent(...)` call whose resolved model slot maps to opencode-go (currently `claude-haiku-4-5` and `background`, per `config.json:116-121`). The error is **deterministic for subagent payloads** — four consecutive retries all 400'd identically — while a plain `curl` chat-completions call to the same endpoint succeeds in the same minute. So the provider is up; the request shape CCR sends for subagents is what's rejected.

## 2. The exact error

```
API Error: 400 Error from provider(opencode-go,deepseek-v4-flash: 400):
{"error":{"message":"Error from provider (Console Go): Upstream request failed",
 "type":"invalid_request_error","param":null,"code":"invalid_request_error"}}
    at qn (...\@musistudio\claude-code-router\dist\cli.js:582:7451)
```
Note `"param":null` — opencode-go does not name the offending field. That's the thing to surface.

## 3. What is RULED OUT (do not re-investigate)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| CCR ignores the `model` override | **REFUTED** | `~/.claude-code-router/config.json:116` maps `claude-haiku-4-5 → opencode-go,deepseek-v4-flash`. Pinning `model:"haiku"` is honored; the slot itself points at opencode-go. Backup `before_haiku_deepseek_20260608-130819` shows this is intentional config. |
| opencode-go endpoint is down | **REFUTED** | Direct `curl` (PowerShell `Invoke-RestMethod`) to `https://opencode.ai/zen/go/v1/chat/completions` with model `deepseek-v4-flash` returned HTTP 200 + valid completion during the same window the subagents were 400'ing. |
| Transient provider hiccup | **UNLIKELY** | 4 consecutive retries (haiku-pinned) over several minutes all failed identically; the plain curl succeeded between them. |

## 4. The remaining hypothesis (what to actually test)

**CCR's Anthropic→OpenAI transform produces a request body that opencode-go rejects for subagent-shaped payloads.** Subagent requests differ from a small chat call in three ways that are each candidate culprits:

1. **Tool definitions** — subagent payloads carry large `tools` arrays (Read/Grep/Glob/Bash/etc.). opencode-go may reject the tool schema shape (e.g. a field CCR emits that the provider doesn't accept, or a tool whose JSON schema is malformed after transform).
2. **System prompt size / structure** — subagents get a large system block; opencode-go's `deepseek-v4-flash` returned `reasoning_content` in the successful curl (it's a reasoning model), so prompt-cache / reasoning fields may interact badly with the transform.
3. **Streaming + `reasoning_content`** — the working curl used non-streaming; CCR may stream, and opencode-go's streaming response shape (with `reasoning_content`) may trip CCR's parser, surfacing as a 400 from CCR's own validation, not the provider.

`"param":null` in the error means we don't yet know which of these it is. **The whole investigation hinges on getting the real rejected request body.**

## 5. Where everything lives (verified paths)

| Artifact | Path |
|---|---|
| CCR config | `C:/Users/brsth/.claude-code-router/config.json` (line 116 = haiku slot, line 121 = background slot, line 131 = default fallback chain) |
| CCR binary | `@musistudio/claude-code-router` v2.0.0, installed at `C:/Users/brsth/AppData/Roaming/npm/node_modules/@musistudio/claude-code-router/` (stack trace → `dist/cli.js:582`) |
| Custom router | `P:/.claude/provider-configs/ccr-custom-router.js` (19060 bytes; referenced via `CUSTOM_ROUTER_PATH` at config line 142) — **read this first**, it's where request transform/routing logic the user controls lives |
| CCR logs | `C:/Users/brsth/.claude-code-router/logs/ccr-20260708011322.log` — **314 MB**, do NOT cat; grep it (see §6) |
| Provider endpoint | `https://opencode.ai/zen/go/v1/chat/completions`, OpenAI-compatible, key from `$OPENCODE_KEY` (User env) |
| Provider models | includes `deepseek-v4-flash` (1M context, reasoning model), `glm-5.2`, `kimi-k2.7-code`, etc. (config lines 43-57) |

## 6. Minimal first step (the discriminating test)

The `"param":null` error is the blocker. Get the **actual rejected request body**. Two routes:

**A. CCR log grep (cheapest):**
```bash
# 314MB file — pipe through grep, never cat
grep -aE 'opencode-go|deepseek-v4-flash|invalid_request|400|Upstream request failed' \
  "C:/Users/brsth/.claude-code-router/logs/ccr-20260708011322.log" \
  | tail -50
```
CCR at v2.0.0 logs the outbound request body on error in most configs. Look for the `tools:` / `system:` / `stream:` fields of the failing request.

**B. Reproduce via the custom router's probe script** (if A is empty): there's already `P:/.claude/provider-configs/scripts/routes_probe.py` and `test_routing.ps1` in that folder — check if they emit the transformed payload before send. If not, add a one-line `console.log(JSON.stringify(body))` in `ccr-custom-router.js` right before the opencode-go fetch, restart CCR (`~/.claude-code-router/.claude-code-router.pid`), fire one subagent, capture the body.

## 7. Likely fix shapes (pick after §6 identifies the rejected field)

- **If tools schema is the issue:** strip/normalize the `tools[].function.parameters` JSON schema before forwarding (CCR's Anthropic→OpenAI tool transform may emit `input_schema` instead of `parameters`, or vice-versa). opencode-go is strict; the working curl sent no tools.
- **If `reasoning_content` / streaming:** force `stream:false` for opencode-go, or add `reasoning_content` to CCR's expected response fields.
- **If system-prompt size:** opencode-go may cap system-block size differently than Anthropic; truncate or split.
- **Defensive (do regardless):** add a CCR fallback so a 400 from opencode-go on a haiku/background slot falls through to a known-good provider (minimax or zai) instead of failing the whole subagent. The `fallback` block (config lines 124-141) already lists alternates for `default` but **`background` has no useful fallback** (line 134-136 → only opencode-zen-free). Add `minimax,minimax-m2.7` as a background fallback.

## 8. Do NOT do this

- Do not chase "opencode-go is down" — disproven (§3).
- Do not edit `config.json` haiku/background slots to point elsewhere as the *fix* — that hides the transform bug. It's a valid **workaround** but not the root-cause fix. If you do it as a workaround, leave a `//` comment naming this doc.
- Do not assume the provider error message is accurate. `"param":null` is a generic opencode-go rejection; the real reason is in the request body, which §6 surfaces.

## 9. Falsification condition

This whole diagnosis (request-shape rejection) is wrong **if** the §6 grep shows a clean, minimal, valid-looking OpenAI request body that opencode-go still 400'd. In that case the bug is upstream (opencode-go rejecting valid payloads — file with them, not fixable here) OR in CCR's response parser (treating a non-error response as a 400). Either way §6's captured body is the evidence that decides it.

## 10. Minimal acceptance criteria

- [ ] §6 grep produces the failing request body (or confirms none logged → instrument custom router)
- [ ] Rejected field identified
- [ ] Fix applied (transform OR fallback)
- [ ] Re-run the behavioral subagent test that prompted this (see §11) — a single `Agent(model:"haiku", ...)` dispatch completes without 400
- [ ] Regression: a plain `curl` chat call still succeeds (don't break the working path)

## 11. Prompting context (why this came up)

A `/task verify` subcommand was built (cc-skills-sdlc 1.0.190, `skills/task/scripts/verify_completed.py`) and needed a behavioral smoke-test via a fresh subagent. Every `Agent(model:"haiku", ...)` dispatch died with this 400. The `/task verify` skill itself is structurally complete and unaffected; the subagent test is what's blocked. Once §10 passes, re-run that smoke-test to close the behavioral-validation gap on `/task verify`. The skill's cached SKILL.md is at `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/1.0.190/skills/task/SKILL.md` (verify subcommand at lines 86, 87, 121, 123, 130, 143).
