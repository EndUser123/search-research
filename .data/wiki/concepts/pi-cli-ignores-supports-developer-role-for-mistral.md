---
title: "PI CLI ignores supportsDeveloperRole: false for some models"
created: 2026-08-06
source: session-20260806
tags: [pi, provider-config, mistral, developer-role, api-compatibility, bug]
sources:
  - https://docs.mistral.ai/studio-api/conversations/chat-completion (Mistral, 2026)
summary: >
  PI CLI sends role='developer' in message arrays even when supportsDeveloperRole
  is set to false at both provider and model level in models.json. Mistral's API
  rejects 'developer' role with 422 because it only accepts system/user/assistant/
  tool. The PI config flag appears to be non-functional for this case.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/dedicated-quota-first-dispatch-routing.md
    type: related
  - target: wiki/concepts/provider-rate-limits-and-benchmarking-strategies.md
    type: related
---

# PI CLI ignores supportsDeveloperRole: false

## Decision context

Mistral models failed every benchmark task via PI with "422 status code (no
body)." Direct API testing showed Mistral works fine with standard roles.
Investigation revealed PI sends `role: "developer"` which Mistral rejects.

## Key findings

### Mistral API accepted roles (verified)

Only: `system`, `user`, `assistant`, `tool`. The `developer` role is
OpenAI-specific (used in o-series models). Mistral returns 422 with:
`{"detail":[{"type":"union_tag_invalid","loc":["body","messages",0],
"msg":"Input tag 'developer' found using 'role' does not match any of the
expected tags"}]}`

Source: [Mistral chat completion docs](https://docs.mistral.ai/studio-api/conversations/chat-completion)

### PI config flag is non-functional

Tested with `supportsDeveloperRole: false` at:
- Provider level (`providers.mistral.compat.supportsDeveloperRole: false`)
- Model level (`providers.mistral.models[0].compat.supportsDeveloperRole: false`)

Both levels set to false. PI still sends `role: "developer"`. The 422 persists.

### What works

Mistral works fine via:
- Direct HTTP API (verified: 200 OK with `role: "system"`)
- OpenCode (verified: 33-67s latency)
- PI is the only broken path

This is documented in [[tool-fallbacks]] as a known PI transport issue.
The broader pattern of provider-specific API incompatibilities is tracked in
[[model-fleet-provider-pools]].

## What this means for our workspace

- Mistral models should use HTTP or OpenCode as primary dispatch, not PI
- The `supportsDeveloperRole` flag in PI models.json should not be trusted
  as a reliable config mechanism — it may work for some providers but not others
- fleet-models.json dispatch_paths for Mistral should reflect this: PI is
  broken for Mistral until PI fixes the bug
- The PI error handler swallows the response body, showing "422 no body" —
  making diagnosis harder. The actual body contains the useful error message.
- Related: [[tool-fallbacks]] documents this as a known PI failure mode.
  [[dedicated-quota-first-dispatch-routing]] covers the dispatch path strategy.

## Receipts

- `~/.pi/agent/models.json` — PI config with `supportsDeveloperRole: false`
  at both provider and model level for Mistral, verified ineffective 2026-08-06
- Direct API test: `POST https://api.mistral.ai/v1/chat/completions` with
  `role: "developer"` → HTTP 422 with `union_tag_invalid` error
- Direct API test: same endpoint with `role: "system"` → HTTP 200 OK
- PI probe: `pi -p --provider mistral --model mistral-medium-latest "OK"` →
  "422 status code (no body)" despite correct config

## Falsifier

If a future PI version respects `supportsDeveloperRole: false` and sends
`role: "system"` instead of `role: "developer"`, Mistral PI dispatch will
start working. Re-test after PI updates. Check: `pi --version` and test with
`pi -p --provider mistral --model mistral-medium-latest "OK"`.

## Sources

- Direct API test (2026-08-06): confirmed developer role → 422 on Mistral
- [Mistral chat API docs](https://docs.mistral.ai/studio-api/conversations/chat-completion) — accepted roles list
- PI models.json at `~/.pi/agent/models.json` — config verified but ineffective

## Auto-related

- [[quantization-and-memory-optimization-for-local-ai-models]]
- [[model-fleet-provider-pools]]
- [[uncensored-ai-models]]
- [[free-open-source-ai-coding-models]]
- [[local-llm-inference-engines]]

