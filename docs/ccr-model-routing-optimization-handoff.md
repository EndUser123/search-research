# Cold-Start Handoff: CCR Model Roles, Routing, and Fallback Optimization

**Status:** safe baseline implemented and live-verified; provider-quality and context-error retry ordering still require evidence
**Created:** 2026-07-15  
**Scope:** Claude Code → admission proxy → CCR → configured model providers  
**Primary question:** optimize model roles and fallback order using evidence, without confusing normal routing with error recovery.

**Accuracy correction (2026-07-16):** The active M3 route uses
`minimax,MiniMax-M3[1m]`. An interim unsuffixed entry was an agent
misstatement, not a user-validated preference. The context-admission work is a
separate concern and does not qualify this route choice.

**Context-admission correction (2026-07-16):** A live 1,108,432-token CCR
count was routed to `deepseek-v4-flash` after Ornith rejected it as over-local-
context. The edge proxy had already estimated 1,569,286 total tokens against a
983,616 safe ceiling but forwarded because admission was advisory. The proxy
now uses its cheap estimate only as a prefilter, obtains CCR's exact local
`count_tokens` result above that threshold, and returns a Claude-compatible
`Prompt is too long` error before provider selection when the exact total still
exceeds the common configured cloud ceiling.

---

## 1. Read this first

Do not begin by assigning “coding,” “reasoning,” or “background” labels to
fallback arrays. In the installed CCR runtime, `Router` and `fallback` have
different meanings:

- `Router.<scenario>` selects the normal provider/model route.
- `fallback.<scenario>` is consulted after a provider response failure.
- Fallback entries are attempted in listed order.
- The first successful fallback response is returned.
- A fallback model is not automatically a model specialized for the original
  workload; it is merely the next recovery candidate.

This behavior was verified by inspecting the installed CCR runtime at:

`C:/Users/brsth/AppData/Roaming/npm/node_modules/@musistudio/claude-code-router/dist/cli.js`

The relevant runtime function selects `config.fallback` using
`scenarioType`, catches `provider_response_error`, iterates the configured
array, and returns the first successful response.

Do not promote a hypothesis about model quality, tool compatibility, or
fallback behavior into configuration without a controlled test.

## 2. Canonical artifacts and authority

| Artifact | Authority / purpose |
|---|---|
| `C:/Users/brsth/.claude-code-router/config.json` | Active CCR provider, Router, and fallback configuration |
| `P:/.claude/provider-configs/ccr-custom-router.js` | Per-request custom routing authority loaded by CCR |
| `P:/.claude/provider-configs/ccr-route-metadata.js` | Canonical context-limit metadata consumed by router and admission proxy |
| `P:/.claude/provider-configs/ccr-admission-proxy.js` | Canonical edge authentication, exact-duplicate shaping, transport bounds, and exact-on-threshold cloud context admission |
| `P:/.claude/provider-configs/cc-ccr.ps1` | Launcher, proxy wiring, environment, and lifecycle |
| `P:/.claude/provider-configs/ccr-custom-router.test.js` | Router and route-integrity tests |
| `P:/.claude/provider-configs/ccr-context-shaper.test.js` | Context-shaper tests; proves only byte-identical earlier tool results are compacted |
| `C:/Users/brsth/AppData/Roaming/npm/node_modules/@musistudio/claude-code-router/dist/cli.js` | Installed CCR implementation; inspect before claiming fallback semantics |
| `P:/.env` | Credential source; never print or persist secret values |

The CCR configuration is user-owned runtime state. Do not treat generated
logs, cached plugin copies, old backups, worktrees, or prior chat summaries as
current routing authority.

## 3. Current normal routes

Current `Router` entries are:

| CCR scenario / model label | Current normal route | Meaning |
|---|---|---|
| `claude-opus-4-8` | `zai,glm-5.2` | high-end reasoning/strategic label |
| `claude-sonnet-5` | `minimax,MiniMax-M3[1m]` | primary general/coding cloud route |
| `claude-sonnet-4-6` | `minimax,MiniMax-M3[1m]` | compatibility route |
| `claude-haiku-4-5` | `opencode-go,deepseek-v4-flash` | fast/background-oriented route |
| `claude-haiku-4-5-20251001` | `opencode-go,deepseek-v4-flash` | compatibility route |
| `claude-local-ornith` | `llama-cpp,ornith-1.0-9b` | explicit local route |
| `think` | `zai,glm-5.2` | reasoning route |
| `default` | `minimax,MiniMax-M3[1m]` | CCR default |
| `background` | `opencode-go,deepseek-v4-flash` | background route |
| `longContext` | `opencode-go,mimo-v2.5` | long-context route |

The custom router adds an important layer:

- coding is local-first when the local model is healthy, idle, and within its
  effective context budget;
- general or unknown work stays on the M3 cloud route and does not probe Ornith;
- routing hints are one-shot and are removed when consumed, preventing a prior
  coding classification from leaking into the next request;
- model-router recommendations are read only when that one-shot hint supplies
  the same session ID; unhinted requests never scan unrelated sessions;
- local failure falls to `opencode-go,deepseek-v4-flash`;
- reasoning/planning normally uses GLM 5.2;
- background generally falls through to CCR’s `Router.background`;
- explicit pins can override automatic decisions.

Read the comments and decision branches in
`P:/.claude/provider-configs/ccr-custom-router.js` before changing this policy.

## 4. Current fallback arrays

The active fallback configuration is:

```json
{
  "longContext": [
    "zai,glm-5.2",
    "minimax,MiniMax-M3[1m]",
    "opencode-zen-free,opencode/minimax-m3-free",
    "nvidia-free,nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia-free,nvidia/nemotron-3-super-120b-a12b"
  ],
  "default": [
    "opencode-go,deepseek-v4-flash",
    "opencode-zen-free,opencode/minimax-m3-free"
  ],
  "background": [
    "opencode-zen-free,opencode/minimax-m3-free"
  ],
  "think": [
    "minimax,MiniMax-M3[1m]",
    "opencode-zen-free,opencode/minimax-m3-free"
  ]
}
```

These arrays should be reviewed for recovery suitability, not described as
the model’s workload role.

## 5. Current context-limit facts

The current canonical metadata contains these active cloud routes with a
1,000,000-token reference ceiling used for telemetry, not universal admission:

- `zai,glm-5.2`
- `opencode-go,deepseek-v4-flash`
- `opencode-go,mimo-v2.5`
- `minimax,MiniMax-M3[1m]` (user-preferred, proven route identifier; MiniMax
  documents M3 with a 1,000,000-token context window)
- `nvidia-free,nvidia/nemotron-3-ultra-550b-a55b`
- `nvidia-free,nvidia/nemotron-3-super-120b-a12b`
- `opencode-zen-free,opencode/minimax-m3-free`

The local Ornith route is separate and has a much smaller live context
budget. Do not describe every provider model listed in `Providers` as an
active CCR route; provider inventory and Router/fallback reachability are
different sets.

NVIDIA model-capability evidence:

- [Nemotron 3 Ultra technical report](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Ultra-Technical-Report.pdf)
- [Nemotron 3 Super announcement](https://developer.nvidia.com/blog/introducing-nemotron-3-super-an-open-hybrid-mamba-transformer-moe-for-agentic-reasoning/)

The endpoint was live-probed on 2026-07-15 using `NVIDIA_FREE_KEY` from
`P:/.env`:

| Model | Result | Approximate latency | What this proves |
|---|---:|---:|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | HTTP 200 | 11.5 s | credential, endpoint, and exact model ID work |
| `nvidia/nemotron-3-super-120b-a12b` | HTTP 200 | 0.36 s | credential, endpoint, and exact model ID work |

Those were tiny prompts. They do **not** prove full 1M request acceptance,
tool compatibility, reasoning compatibility, sustained latency, or quality.

## 6. What was already disproven or corrected

### Incorrect: “fallback order equals model role”

Fallback is error recovery. It does not establish that a model is the best
reasoning, coding, or background model.

### Unsupported: “Super should handle coding and Ultra should handle reasoning”

This is a plausible hypothesis based on model descriptions, not a verified
CCR behavior or benchmark result. The latency difference above is from one
small availability probe and is not a quality or production-latency ranking.

### Unsafe: changing all role primaries immediately

Changing normal `Router` routes changes live behavior for every request in the
scenario. Do not do this as a side effect of optimizing fallback recovery.

### Known architecture fact: admission is separate

The custom router returns a route or null; null means CCR’s built-in routing,
not rejection. The edge proxy therefore owns pre-provider rejection. It
enforces authentication and a 32 MiB transport memory bound, uses its
character/token estimate only as a cheap prefilter, and calls CCR's local
`/v1/messages/count_tokens` endpoint for requests over the shared reference
ceiling. Confirmed oversize requests receive an Anthropic-shaped 400
`invalid_request_error` containing `Prompt is too long`; they are not sent to a
provider. Large requests whose exact count fits are forwarded. Local Ornith
retains its separate, route-aware live context gate.

CCR 2.0.0 proves generic HTTP/quota fallback, but the installed runtime does
not yet prove all three properties required for automatic context recovery:
explicit pre-generation context-error classification, exclusion of the failed
route, and a single-retry cap. No additional context retry loop was enabled.

## 7. Required investigation for the next LLM

### A. Establish actual scenario behavior

For each scenario, capture:

- incoming Claude model label;
- `scenarioType` seen by CCR;
- custom-router decision;
- selected normal route;
- provider response status and error class;
- whether CCR entered the fallback loop;
- fallback candidate attempted;
- successful route or final failure.

Use correlation IDs. Do not infer fallback behavior from the config display
alone.

### B. Test each model in each relevant workload shape

Run the same bounded test corpus through candidate routes:

1. plain text response;
2. coding request requiring file/tool calls;
3. reasoning request with extended thinking enabled;
4. background request with the actual background prompt shape;
5. long-context request at several sizes;
6. streaming response;
7. malformed/unsupported request to exercise fallback;
8. provider timeout or controlled failure where safely possible.

Record at minimum:

```text
run_id
timestamp
CCR revision/package version
config hash
scenario
requested model label
selected route
fallback route
HTTP status
error category
time to first byte
total latency
input/output token counts if available
tool-call success
thinking success
context size
final outcome
```

### C. Score candidates by role

Do not use one global ranking. Score separately for:

- reasoning correctness and instruction adherence;
- coding correctness, tool use, and edit safety;
- background throughput and failure recovery;
- long-context retrieval and instruction retention;
- provider compatibility and streaming behavior;
- latency and quota availability.

### D. Optimize fallback order by failure mode

A good fallback is not merely “another smart model.” It must also:

- accept the transformed request shape;
- support the required tools/thinking/streaming combination;
- have sufficient context;
- be available under the current quota;
- avoid repeating the same provider failure class;
- preserve user data-policy expectations;
- return a compatible response format.

Use distinct fallback policies for:

- context overflow;
- provider 4xx request incompatibility;
- provider 5xx/timeout;
- quota exhaustion;
- local-model unavailability.

Do not retry a 4xx blindly across providers unless the error is known to be
provider-specific and the transformed request is compatible.

## 8. Candidate hypotheses, not decisions

These are starting hypotheses for testing:

| Candidate | Hypothesis | Required falsifier |
|---|---|---|
| Nemotron Super | May be a useful general/background/large-context fallback | It fails tool, thinking, streaming, or latency tests at an unacceptable rate |
| Nemotron Ultra | May be useful for high-effort reasoning or architecture fallback | It provides no quality gain, is too slow, or fails the request shape |
| M3 | Strong general fallback for normal Claude-shaped requests | Controlled provider-failure tests show incompatibility or quota weakness |
| DeepSeek Flash | Fast background/coding recovery route | Repeated real subagent/tool payloads still produce 400s |
| Local Ornith | Useful only for bounded local-first work | Live readiness/context/quality tests show unsafe or unreliable behavior |

No candidate should be promoted to a primary role solely from model-card
claims.

## 9. Acceptance criteria before changing live role order

- [ ] Actual CCR fallback loop observed in logs for at least one controlled
  failure.
- [ ] Scenario-to-fallback mapping confirmed for `default`, `think`,
  `background`, and `longContext`.
- [ ] Super and Ultra tested with real Claude-shaped tool payloads.
- [ ] Super and Ultra tested with thinking payloads if they may receive
  `think` recovery traffic.
- [ ] Streaming behavior verified.
- [ ] No request-shape incompatibility or transform regression.
- [ ] Fallback ordering justified separately for each scenario.
- [ ] Existing primary routes remain unchanged unless explicitly approved.
- [ ] Targeted CCR tests pass.
- [ ] A bounded live canary confirms the chosen fallback path.
- [ ] Rollback is one config restoration and CCR restart.

## 10. Useful commands

```powershell
# Inspect active config
Get-Content C:\Users\brsth\.claude-code-router\config.json

# Run route-integrity tests
node --test P:\.claude\provider-configs\ccr-custom-router.test.js

# Run context-shaper tests separately
node --test P:\.claude\provider-configs\ccr-context-shaper.test.js

# Search CCR logs without reading large files wholesale
Select-String -Path C:\Users\brsth\.claude-code-router\logs\ccr-*.log `
  -Pattern 'fallback|provider_response_error|Trying fallback model|Fallback model'

# Inspect current route metadata
Get-Content P:\.claude\provider-configs\ccr-route-metadata.js
```

## 11. Handoff instruction to the next LLM

Start with this document, the active config, the custom router, and the
installed CCR fallback implementation. Produce an evidence packet with:

1. verified current behavior;
2. measured model/workload results;
3. separate primary-routing and fallback recommendations;
4. failure-mode-specific fallback order;
5. risks and rollback;
6. a minimal proposed diff only after the evidence supports it.

Do not silently edit live configuration while still operating on hypotheses.
If evidence is incomplete, report `needs_fix` or `partial` and name the next
discriminating test.
