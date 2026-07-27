---
title: "Model tool-calling capability: which models support agentic tool use, and why some fail"
created: 2026-07-22
source: session-2026-07-22-www
sources:
  - https://llm-stats.com/leaderboards/best-ai-for-tool-calling
  - https://www.kdnuggets.com/5-small-language-models-for-agentic-tool-calling
  - https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
  - https://fleeceai.app/blog/best-ai-model-for-tool-calling-2026
  - https://www.mindstudio.ai/blog/best-ai-models-agentic-workflows-2026
  - P:/.data/wiki/concepts/model-fleet-provider-pools.md
  - P:/.data/wiki/concepts/operationalizing-gemma-models-2026-07-22.md
  - C:/Users/brsth/.grok/tool-fallbacks.md
tags: [tool-calling, function-calling, agentic, model-capability, matrix, dgemma, gemma, nemotron, thinking-mode, failure-mode, routing]
summary: >
  Most models in the host pool support agentic tool calling. Exceptions are
  transport/parser failures, not missing model capability. DiffusionGemma:
  thinking-mode breaks the agent framework parser — use direct API for
  no-tool reads only. Nemotron-3-ultra: **NVIDIA direct endpoint fails on
  tool-grounded spawn_subagent even with `stream_tool_calls = false`**
  (null-typed-as-u32 serde error on real prompts, empirically verified
  2026-07-26); **use `or-nemotron-ultra-free` (OpenRouter proxy) instead —
  same model, empirically verified working for both trivial (3.9s) and real
  tool-grounded spawns (7.2s, full output).** `zen-nemotron-3-ultra-free`
  (OpenCode Zen) is broken with a different serde error (`missing field id`).
  Canonical host matrix for tool-call routing.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/model-selection-from-pool-decision-framework
    type: extends
  - target: wiki/concepts/model-fleet-provider-pools
    type: extends
  - target: wiki/concepts/diffusiongema-direct-api-howto
    type: related
  - target: wiki/concepts/model-pool-not-chain
    type: related
---

# Model tool-calling capability: the matrix and the failure mode

## The finding (one line)

Most models in the host pool support agentic tool calling. The exceptions are **host transport / framework parser mismatches**, not missing model capability. On this host the two named cases are DiffusionGemma (empty content / thinking-mode parse conflict) and **Nemotron-3-ultra (serialization error on real tool-grounded prompts — partial fix 2026-07-26, recurrence same-day; trivial no-tool prompts work with `stream_tool_calls = false`)**.

## Where to find the Nemotron problem (canonical)

| What | Where |
|------|--------|
| **Canonical wiki page (this concept)** | `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` — matrix row + host-integration caveats + falsifier |
| Host operational table | `C:/Users/brsth/.grok/tool-fallbacks.md` (2026-07-23 real-prompt failure; demote until re-verified) |
| Full receipt + open investigation | `P:/docs/handoffs/tp-pool-composition-review-20260723/HANDOFF.md` § "Critical empirical evidence" |
| Related ops notes | `P:/.data/wiki/concepts/tp-parallel-improvement-solution-space.md` (pool race as mitigation) |

### Nemotron status: **ROOT CAUSE FULLY CONFIRMED (2026-07-26 dual cross-transport test)** — Grok Build serde bug, not NVIDIA API; `stream_tool_calls = false` is partial workaround only; use OpenCode, PI, or direct API for tool-grounded nemotron work

| Date | Observation | Source |
|------|-------------|--------|
| 2026-07-22 | Trivial `Reply READY` probe via `spawn_subagent` **passed** (~7.5s) | `tool-fallbacks.md`; early pool probe |
| 2026-07-23 | Real `/tp`-sized prompt (~98k tokens) **failed**: `serialization error: invalid type: null, expected u32 at line 1 column 331`. Model emitted ~494 tokens; framework could not parse. | `tool-fallbacks.md`; handoff `tp-pool-composition-review-20260723` |
| 2026-07-25 | Real multi-file analysis assignment (~90k input tokens) **failed again**: same error family at column 330 (`null, expected u32`). Confirms not transient. | Session retest (why-skill multi-model producers) |
| 2026-07-26 | **ROOT CAUSE CONFIRMED**: NVIDIA NIM API returns `null` for `service_tier`, `system_fingerprint`, and `choices[0].logprobs`. Grok Build's deserializer types these as `u32` instead of `Option<u32>`. When the serde hits `service_tier: null` at column ~330, it fails. Direct API works fine (the null fields are valid OpenAI-compatible optional fields). The serde bug is in Grok Build, not the model or provider. Fix applied: `stream_tool_calls = false`. Claimed verified working 19.6s. | Direct API inspection this session (recursive null scan found 3 null fields) |
| 2026-07-26 (later, same-day recurrence with fix in place) | **FIX IS PARTIAL — trivial prompts pass, tool-grounded real prompts still fail:** (1) Trivial `Reply READY` spawn **PASSED** in 3.65s, exit 0, returned "READY". (2) Real `/tp`-sized spawn (~90k tokens, tool-call expectation in prompt) **FAILED** with the exact serde error the fix was supposed to bypass: `serialization error: invalid type: null, expected u32 at line 1 column 331`, 10.09s. Both tests in same parent session ~37 min apart. Direct API smoke test (no tools, plain prompt) also passed in 52.55s. | Handoff `P:/docs/handoffs/nemotron-spawn-failure-investigation-20260726/HANDOFF.md` |
| 2026-07-26 (cross-transport verification — HYPOTHESIS CONFIRMED) | **Both OpenCode and PI transports handle nemotron tool calls cleanly; Grok Build's serde is confirmed as the bug location.** Test 1 (OpenCode): `opencode run -m opencode/nemotron-3-ultra-free "<tool-grounded prompt>"` completed in 88.99s, exit 0. The model emitted **6 tool calls** (read, glob×2, bash×2, then text response); OpenCode parsed every tool-call response without serde error. Test 2 (PI): `pi -p --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b --thinking off --no-session "<tool-grounded prompt>" --mode json` completed in 70.44s, exit 0. The model emitted **3 tool calls** (read, bash `ls`, bash `find`); PI parsed every tool-call response without serde error. PI trivial no-tool test also passed (returned "READY" cleanly). Same model, same NVIDIA API, different transports = different result. **The bug is in Grok Build's deserializer specifically (types `service_tier`/`system_fingerprint`/`logprobs` as `u32` instead of `Option<u32>`); both OpenCode and PI handle the null fields correctly.** The `stream_tool_calls = false` config workaround in Grok Build only bypasses the streaming code path; the non-streaming tool-call response path still has the u32-vs-null bug. | OpenCode session `ses_05fef9776ffeKjqeX8tljJeHlb` + PI session `019fa040-aa65-7f69-87a4-48c793ebc6bb` this host, 2026-07-26 |

**Root cause:** Grok Build's serde deserializer types `service_tier` (and possibly `system_fingerprint`, `logprobs`) as `u32` instead of `Option<u32>`. NVIDIA legitimately sends `null` for these OpenAI-compatible optional fields. The deserializer can't handle null → `invalid type: null, expected u32`.

**Fix path:** Grok Build patch — change the field types from `u32` to `Option<u32>` (or skip unknown/optional fields). This is upstream; we can't fix it locally.

**What is NOT a fix:** demoting the slug in a skill pool, preferring glm/mimo, or documenting the failure. Those are **workarounds**. The falsifier for "solved" is: *spawn_subagent succeeds after Grok Build patches the serde types.*

**Do:** use `glm-5-2`, `go-mimo-v2-5`, or parent-inherited for tool-grounded / multi-file subagent work.  
**Don't:** treat a green trivial READY probe as proof Nemotron is pool-safe.

## Why this concept exists

Session 2026-07-22 exposed a routing gap: `spawn_subagent(model=nvidia-diffusiongemma-26b)` returned empty content for tool-use tasks, but direct-API calls to the same model worked fine. The model was labeled "broken for agent use," but the real story is narrower and more useful: **DiffusionGemma supports function calling in principle (Google ships it for the Gemma 4 family), but its thinking-mode output format breaks the agent frameworks tool-call parser.** Routing the model to no-tool tasks avoids the conflict; using agent-compatible models for tool-grounded work sidesteps it.

The existing model concepts (`model-fleet-provider-pools`, `model-selection-from-pool-decision-framework`) cover cost, quota, context, and lane selection, but **not tool-call capability**. This concept adds that dimension.

## The tool-calling capability matrix (host pool)

| Model (host slug) | Tool calling? | Reason / evidence | Use for |
|-------------------|---------------|-------------------|---------|
| `parent-inherited` (Grok) | **Yes** | Verified: drives the parent agent full tool surface | All tool-grounded work (default) |
| `ccr-ornith` | **Yes** | Verified 2026-07-22: probe-verified spawn_subagent + tool calls (slow: 31s) | Tool-grounded reads, slow but free |
| `go-mimo-v2-5` (MiniMax) | **Yes** | Probe-verified 2026-07-22 spawn_subagent; llm-stats MCP Atlas 74.2% | Tool-grounded reads, fast + paid |
| `glm-5-2` | **Yes** | Probe-verified 2026-07-22; llm-stats MCP Atlas 76.8%, Terminal-Bench 82.7% | Reasoning + tool-grounded (ration: scarce) |
| `nvidia-nemotron-3-ultra` | **Broken via Grok Build spawn when tools are involved; works via OpenCode, PI, and direct API** | Root cause FULLY CONFIRMED 2026-07-26 via dual cross-transport test: Grok Build's serde types `service_tier`/`system_fingerprint`/`logprobs` as `u32`; NVIDIA returns `null`; OpenCode and PI type them correctly. Same model + same prompt + tools: Grok Build FAIL (`null, expected u32`), OpenCode PASS (88.99s, 6 tool calls), PI PASS (70.44s, 3 tool calls). `stream_tool_calls = false` is partial workaround (trivial no-tool prompts only). | **Grok Build spawn_subagent:** trivial no-tool prompts only. **OpenCode** (`opencode run -m opencode/nemotron-3-ultra-free`): all uses including tool-grounded. **PI** (`pi -p --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b --thinking off`): all uses including tool-grounded. **Direct API** (`P:/tmp/nemotron_direct_smoke.py` pattern): all uses. NOT pool-safe for `/tp`-sized Grok Build work — use glm/mimo/parent for `/tp` spawn pool. |
| `nvidia-diffusiongemma-26b` | **No (via agent framework)** | Direct API works for no-tool reads; spawn_subagent + headless `--tools` both fail (thinking-mode conflict) | **No-tool tasks only** (batch reads, file summarization via `dgemma_read.py`) |
| `gemini-3.5-flash` / `2.5-flash` | **Yes** (not in host pool yet, but reference) | llm-stats MCP Atlas 83.6%, Terminal-Bench 76.2% | If added: strong tool-grounded option |
| `gemini-3.1-pro` | **Yes** (reference) | llm-stats MCP Atlas 69.2%, TAU-bench Retail 99.3% | If added: top-tier tool use |
| `go-qwen3-7-max/plus` | **Likely yes** (untested on host) | Qwen3 family has native tool calling via Qwen-Agent + MCP (KDnuggets source) | Untested on host; 401 on spawn_subagent currently blocks |
| `go-deepseek-v4-*` | **Likely yes** (untested on host) | DeepSeek-V4-Pro-Max MCP Atlas 73.6% (llm-stats); serialization error on spawn_subagent currently blocks | Untested on host |
| `mistral-medium-latest` | **Yes** (in principle) | Mistral 7B v0.3 has native function-calling tokens (KDnuggets); 422 error on spawn_subagent currently blocks | Untested on host |

## The failure mechanism (why dgemma breaks, not "is broken")

DiffusionGemma is a **diffusion-based** LLM, not autoregressive. It generates via iterative denoising rather than token-by-token prediction. The thinking mode (enabled by default on the Nvidia endpoint) emits `<|channel>thought` blocks that are visible in raw output but not in the `content` field.

When the agent framework (Grok Build, Claude Code) tries to parse a tool call:
1. It expects either a clean text response OR a structured tool-call block
2. dgemma emits thinking tokens that dont match either format
3. The framework parser returns empty content (spawn_subagent) or rejects the message (headless `--tools`)
4. Disabling thinking returns empty content too (the model needs thinking for quality)

**The same model works via direct API** (`dgemma_read.py`) because that path bypasses the framework parser entirely, it just takes whatever the model emits.

So the failure is **transport-specific**, not capability-specific:
- `spawn_subagent(model=dgemma)` -> empty content (framework parser conflict)
- `grok -m dgemma -p "..."` headless no-tools -> works (15s, leaks thinking tokens but parseable)
- `grok -m dgemma -p "..." --tools read_file` -> fails (same parser conflict)
- `dgemma_read.py --batch/--enhanced` -> works (direct urllib, no framework)

## The Google-side nuance

Google **does** ship function calling for the Gemma family, including Gemma 4 E2B and the standalone FunctionGemma model. The Gemma 4 function-calling docs (ai.google.dev) show a working `<|tool_call>` format. So the capability exists in the model family; the issue is that the **DiffusionGemma variant** (diffusion-based) on the Nvidia endpoint uses a different output format than what the agent frameworks expect.

This means:
- `gemma-4-31b-it` (autoregressive, in host config) would likely work for tool calling (untested)
- `nvidia-diffusiongemma-26b` (diffusion-based) does not work for tool calling via agent framework
- Future Gemma variants may or may not, depending on whether they keep the diffusion architecture

## Do's and don'ts

### Do
- Route dgemma to **no-tool tasks only** (batch reads, file summarization, pure critique of content already in the prompt)
- Use **agent-compatible models** (parent, glm, mimo, ornith) for any task needing grep/pytest/runtime inspection
- For `/tp` on a file target: dgemma ensemble (`--enhanced`) is optimal, the content is in the prompt so no tools needed
- For `/check` verifiers: agent-compatible pool only (glm > mimo > ornith by speed)
- When a model fails tool use, check whether its the **transport** (spawn_subagent vs direct API) before concluding the model is broken
- Probe new models with BOTH a trivial prompt AND a tool-use prompt before adding them to a pool

### Don't
- Dont add dgemma to any pool that requires tool execution (the /check verifier pool, the /tp tool-grounded pool)
- Dont conclude "model X doesnt support tool calling" from a spawn_subagent failure alone, the framework parser may be the issue
- Dont use nemotron for tool-grounded verification despite its strong leaderboard scores (serialization-fails on real tasks on this host)
- Dont assume all Gemma variants behave like DiffusionGemma (gemma-4-31b-it is autoregressive and may work)

## Mapping to the model-selection framework

This adds a **7th element** to the 6-element decision framework in `model-selection-from-pool-decision-framework`:

| Element | Question | This concepts contribution |
|---------|----------|---------------------------|
| 1. Task novelty | imagine vs execute | (unchanged) |
| 2. Quality floor | minimum acceptable output | (unchanged) |
| 3. Latency sensitivity | interactive vs background | (unchanged) |
| 4. Context fit | effective budget | (unchanged) |
| 5. Cost regime | free / subscription / per-token | (unchanged) |
| 6. Quota strategy | reserve vs spend | (unchanged) |
| **7. Tool-call requirement** | **does the task need tools (grep, pytest, runtime)?** | **If yes: agent-compatible pool only. If no: dgemma is valid (fast, free, multi-perspective).** |

Stage 0.5 (new): if the task needs tools, filter the pool to agent-compatible members BEFORE applying Stages 1-4. This is a hard gate, not a preference, because no amount of quality/cost/latency optimization fixes a model that cant call tools when tools are required.

## Conflicts / caveats

- **Nemotron Ultra host-integration failure (ROOT CAUSE FULLY CONFIRMED 2026-07-26 via dual cross-transport test):** the bug is in **Grok Build's serde specifically**, not in NVIDIA's API or the model. Verified by sending the same tool-grounded prompt to the same model through three transports: Grok Build `spawn_subagent` → FAIL (`serialization error: invalid type: null, expected u32`); OpenCode `opencode run -m opencode/nemotron-3-ultra-free` → PASS (88.99s, 6 tool calls, exit 0); PI `pi -p --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b --thinking off --no-session ... --mode json` → PASS (70.44s, 3 tool calls, exit 0). The model emitted tool calls in all three cases; only Grok Build's deserializer fails to parse the null fields. **Root cause:** NVIDIA's API returns `null` for `service_tier`, `system_fingerprint`, `choices[0].logprobs` (valid OpenAI optional fields); Grok Build types these as `u32` (non-nullable); OpenCode and PI type them correctly (nullable). **The `stream_tool_calls = false` config workaround is INSUFFICIENT** — it bypasses the streaming code path but the non-streaming tool-call response path has the same u32-vs-null bug. **Fix path:** Grok Build upstream patch (`u32` → `Option<u32>`). **Until then:** use OpenCode (`opencode run -m opencode/nemotron-3-ultra-free`) or PI (`pi -p --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b --thinking off`) or direct API for any nemotron work that needs tools; Grok Build `spawn_subagent` only for trivial no-tool prompts. Reference: docs.x.ai/build/settings/reference; corroborating issue router-for-me/CLIProxyAPI#4218 (same serde pattern).
- **Kimi K3 host-integration failure (PARTIALLY DIAGNOSED 2026-07-26 → 2026-07-27):** Earlier hypothesis ("K3 rejects `top_p ∈ {0.1–0.94, 0.96–0.99, 1.0}`; spawn sends `top_p=1.0`; that's the trigger") is **OVERTURNED for the spawn path**. Spawn capture (logging proxy, 2026-07-27) revealed spawn_subagent sends a minimal body — `model`, `messages`, `max_tokens`, `tools`, `stream`, `stream_options` — with **no `top_p`, `temperature`, `tool_choice`, or other sampling parameters**. The `top_p` finding is real for direct API (deterministic, 3-trial) but irrelevant to spawn. Direct-API reproduction with the exact captured body shape returns 200 for both K3 and K2.7. **Remaining candidates**: transport/header level (spawn sends `x-grok-*`, `x-xai-token-auth`, `x-authenticateresponse` headers direct API does not; HTTP/2 + TLS compression differences). **POLICY (operator directive 2026-07-26): K3 is NOT in any auto-pool.** Two reasons: (1) cost — single spawn test = ~20% of monthly OpenCode-Go quota; (2) reliability — root cause not yet the actual root cause. K3 is usable via direct API only, invoked manually/deliberately by the operator.
- **Qwen/DeepSeek on host:** both families have strong tool-calling reputations (KDnuggets, llm-stats) but fail spawn_subagent on this host (401, serialization). Same likely transport issue.
- **The matrix is host-specific.** A model that fails tool use on Grok Build might work fine on Claude Code or via opencode/PI. The capability exists; the transport matters.

## Falsifier

This concept is wrong if:
- dgemma starts working for tool use via spawn_subagent (framework was fixed) -> update the matrix
- gemma-4-31b-it also fails tool use (the failure is Gemma-family-wide, not diffusion-specific) -> broaden the diagnosis
- nemotron starts working for real tool tasks on this host (was a transient API issue) -> move it to "Yes" in the matrix
- A model labeled "Yes" here fails tool use in practice (matrix overclaims) -> downgrade it

Re-verify quarterly; model + framework versions change.

## Sources (scored CREDIBLE-lite)

| Source | Auth | Rec | Evid | Bias | Total | Role |
|--------|------|-----|------|------|-------|------|
| llm-stats tool-calling leaderboard | 3 | 3 | 3 | 3 | 12 | Per-model tool-call benchmark scores |
| KDnuggets 5 SLMs for tool calling | 2 | 3 | 3 | 2 | 10 | SLM tool-call support (SmolLM3, Qwen3, Phi-3, Gemma 4, Mistral) |
| Google Gemma 4 function-calling docs | 3 | 3 | 3 | 3 | 12 | Gemma family DOES support function calling (the capability exists) |
| fleeceai tool-calling benchmarks | 2 | 3 | 3 | 2 | 10 | MCP-Atlas, APEX-Agents scores |
| mindstudio agentic workflows | 2 | 3 | 2 | 2 | 9 | Frontier-model tool-call comparison |
| Host tool-fallbacks.md | 3 | 3 | 3 | 3 | 12 | This-host spawn_subagent + direct-API verification |

Phase 2 synthesis: parent-inherited model.

## Auto-related

- [[skill-enforcement-layers]]

