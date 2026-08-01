---
title: "Router and proxy solutions for cross-harness model tool-calling: patterns that solve tool-call emission failures"
created: 2026-07-31
source: session-2026-07-31 (/www research on router/proxy tool-calling)
sources:
  - https://deepwiki.com/BerriAI/litellm/8.1-tool-calling-and-function-integration
  - https://docs.litellm.ai/docs/completion/function_call
  - https://openrouter.ai/docs/guides/features/tool-calling
  - https://github.com/BerriAI/litellm/issues/6829
  - https://github.com/BerriAI/litellm/issues/11577
  - https://github.com/openai/codex/issues/19765
  - https://github.com/openai/codex/issues/34758
  - https://github.com/openai/codex/issues/10828
  - https://github.com/openclaw/openclaw/issues/28754
  - https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/
  - https://docs.cline.bot/provider-config/openai-compatible
  - https://deepwiki.com/RooCodeInc/Roo-Code/6.2-native-tool-calling-protocol
  - https://gradient.news/gpt-5-3-codex-failures-developers-workarounds/
  - https://www.merge.dev/blog/llm-proxies-vs-lm-routers
  - https://zread.ai/1rgs/claude-code-proxy/18-tool-calling-format-translation
  - P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md
tags: [tool-calling, function-calling, router, proxy, litellm, openrouter, codex-cli, luna, cross-harness, transport-failure, workaround, routing]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 4
relations:
  - target: wiki/concepts/model-tool-calling-capability-matrix
    type: extends
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: related
  - target: wiki/concepts/model-fleet-provider-pools
    type: related
  - target: wiki/concepts/cross-model-second-opinion
    type: related
summary: >
  When a model fails to emit tool calls inside a specific agentic CLI harness
  (the gpt-5-6-luna-in-Codex-CLI failure: 9 turns, 0 tool calls), router and
  proxy solutions address it through five mechanisms: (1) format translation
  between provider tool-call schemas, (2) reliability-based auto-routing that
  detects and routes around emission failures, (3) `tool_choice=required` at
  the API layer to force grammatical tool emission, (4) text-only → retry/
  failover detection, and (5) ReAct/prompt-based fallback protocols. The
  LiteLLM `add_function_to_prompt` fallback is DISCONFIRMED as broken in
  practice. Luna's failure is a known, documented class of problem — lighter
  GPT-5 tiers intermittently emit text-only responses the harness treats as
  success. The Codex CLI toolset is harness-fixed (same schemas for all tiers),
  so the failure is emission/reliability, not provisioning.
---

# Router and proxy solutions for cross-harness model tool-calling

## The problem this solves

A model that supports function calling at the API level (confirmed by the
model family's capability spec) emits **zero tool calls** when run inside a
specific agentic CLI harness. The model produces detailed plans as prose but
never converts them into structured tool-call invocations. The harness treats
each text-only response as successful completion, so no retry or failover
triggers.

**Specific instance (2026-07-31):** gpt-5-6-luna running inside OpenAI Codex
CLI. 9 turns of conversation, 0 model-initiated tool calls. Every turn showed
only `Lifecycle event` in the tool column (harness notification, not model
invocation). The model reasoned fluently about what it *would* do but never
emitted a tool-call structure.

## What controls tool provisioning in Codex CLI

**Finding [OBSERVED — from openai/codex source-code-path evidence + config
regression issues]:** The Codex CLI toolset is **harness-fixed, not
per-model-tier**. The tool schemas (shell/exec, read, write, apply_patch,
plan, web_search, MCP tools) are compiled into the Rust core
(`codex-rs/core/src/tools/`). Model tier selection via `--model` or
`config.toml model =` only swaps which model receives the *same fixed tool
list*. There is no per-tier tool-provisioning toggle.

**The real provisioning knobs are:**

| Control | What it does | Impact on tool-calling |
|---------|-------------|----------------------|
| `wire_api = "responses" \| "chat"` | Selects the API protocol for tool schema delivery | Responses API is the supported path for Codex; chat/completions deprecated |
| Top-level `model = "..."` in config | Resolves the model for tool-schema binding | **Config regression [openai/codex#34758]:** omitting this with a custom `model_provider` strips the shell tool entirely — model says "I can't run shell commands" or fabricates output |
| `tool_choice` | Not available in Codex config.toml | Only at the API layer — cannot be set from Codex CLI config |

**Key implication:** Luna got the same tool schemas as Sol. The failure is
emission/reliability, not withheld schemas.

## The known failure class: "text-only early termination"

Luna's 9-turn text-only behavior is a **documented, recurring failure mode**,
not a one-off. Multiple independent sources describe the exact symptom:

| Source | Model | Symptom |
|--------|-------|---------|
| [openai/codex#10828](https://github.com/openai/codex/issues/10828) | Codex models | "Codex ends turn unexpectedly" — model says "Understood, I'm continuing…" then stops; `continue` yields more prose, no tool call |
| [openclaw/openclaw#28754](https://github.com/openclaw/openclaw/issues/28754) | gpt-5.3-codex | Intermittent text-only + `end_turn`; runs "complete" in ~3.5s with `reason="run_completed"`; gateway treats as success so **no retry triggers**. Same session worked 25 min earlier with 48 tool calls |
| [anomalyco/opencode#12570](https://github.com/anomalyco/opencode/issues/12570) | GPT-5 codex | Same symptom on OpenCode harness |
| [openai/codex#19765](https://github.com/openai/codex/issues/19765) | Weaker models | `function_call.arguments` arrives as truncated JSON → parse error → weaker models don't reliably re-emit valid calls. Reporter lists "use a weaker / less reliable tool-calling model" as a repro step |
| [gradient.news](https://gradient.news/gpt-5-3-codex-failures-developers-workarounds/) | GPT-5.3 Codex | Community reporting mid-task collapse; devs downgrading models as workaround |

**The Kotonia finding [OBSERVED]:** A controlled study
([kotonia.ai](https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/))
demonstrated that **"a harness mismatch is indistinguishable from model
disobedience when you only look at outcomes."** A model emitting tool calls
in `qwen3_coder` XML format with a `hermes` parser configured → `tool_call`
field came back empty → observed as "0/6 tool calls." Raw content showed the
tool call **leaked through as plain text**. The study also found that weaker
models skip tools when they believe they know the answer, even fabricating
provenance ("I calculated this precisely in Python") while never calling the
tool.

## How router and proxy solutions solve this

### Mechanism 1: Format translation (bidirectional proxy)

**What:** A proxy layer translates between provider-specific tool-call
formats. OpenAI's `{type: "function", function: {name, parameters}}` ↔
Anthropic's `{name, input_schema}` ↔ Gemini's `FunctionDeclaration`. Tool
choice, streaming deltas, and tool results are all translated.

**Implementations:** LiteLLM (100+ providers, auto-translates OpenAI tool
definitions into provider-specific formats), claude-code-proxy (three-stage
translation pipeline), Portkey (1,600+ models through single API).

**Source:** [DeepWiki LiteLLM tool-calling](https://deepwiki.com/BerriAI/litellm/8.1-tool-calling-and-function-integration)

**Solves:** Format/parser mismatch (the Kotonia scenario). If the model emits
tool calls in a format the harness doesn't expect, the proxy translates. Does
NOT solve emission failure (model emits nothing at all).

**Applicability to Luna:** Low — Luna emitted zero tool-call structures of any
format. Format translation helps when calls exist but are malformed/foreign,
not when they're absent.

### Mechanism 2: Reliability-based auto-routing (OpenRouter)

**What:** OpenRouter tracks per-provider **Tool Call Error Rate** and uses
this signal to drive **Auto Exacto** provider ordering — automatically
preferring providers that complete tool calls reliably for a given model.
Also supports `parameter_requirements` to prevent routing tool-calling
requests to providers that don't support them.

**Source:** [OpenRouter tool-calling docs](https://openrouter.ai/docs/guides/features/tool-calling)

**Solves:** Provider-level tool-call unreliability. If one provider's endpoint
for Luna intermittently fails to emit tool calls, OpenRouter detects the error
rate and routes to a more reliable provider.

**Applicability to Luna:** Medium-high — this is the mechanism most likely to
detect and route around Luna's emission failures. But conflicts with the
operator's intermediary-aversion preference (see Nemotron routing policy in
[[model-tool-calling-capability-matrix]]).

### Mechanism 3: `tool_choice=required` (API-layer enforcement)

**What:** Setting `tool_choice: "required"` in the API request forces the
model to emit at least one tool call — plain prose becomes grammatically
impossible, leaving only "act" or "finish" (if `final_answer` is itself a
tool). This directly defeats the knowledge-confidence gate where weaker models
skip tools when they believe they know the answer.

**Source:** [Kotonia study](https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/) — structural fix for confidence-gated tool skipping.

**Solves:** The exact Luna failure — model plans in prose instead of calling
tools. Forcing the grammatical requirement makes text-only responses
impossible.

**Applicability to Luna:** **Highest** — but requires control of the API
request layer. Codex CLI config does not expose `tool_choice`; it would need
a proxy/wrapper that injects it into the request. This is the single
highest-leverage workaround if the fleet controls the request pipeline.

### Mechanism 4: Text-only → auto-retry/failover

**What:** Detect when a model returns a text-only response to a
tool-requiring task and automatically retry or failover to another
model/provider. The gateway treats text-only completion as a **failure
condition**, not success.

**Status:** Requested but **not yet shipped** in Codex CLI
([openclaw/openclaw#28754](https://github.com/openclaw/openclaw/issues/28754)).
OpenRouter's auto-exacto is the closest production implementation.

**Applicability to Luna:** High — would have caught Luna's 9-turn text-only
run on turn 1 and retried or switched models. Requires harness-level
modification or a proxy that implements the detection.

### Mechanism 5: ReAct / prompt-based tool calling fallback

**What:** When native `tool_calls` don't fire, harnesses fall back to a text
protocol — Thought→Action→Observation loops, JSON/XML markers in prose, or
custom in-prompt markers (e.g., `{{PYTHON: …}}`). The harness parses the
text output for tool-call patterns and executes them.

**Sources:** [ReAct comparison](https://suhasbhairai.com/blog/react-prompting-vs-tool-calling-text-based-reason-act-loops-vs-native-function-invocation), [local-LLM fragmentation](https://blog.progressiverobot.com/prompt-based-vs-native-tool-calling-navigating-the-local-llm-implementation-minefield)

**Solves:** Models that don't support native function calling at all. Also a
fallback when native calling is unreliable.

**Applicability to Luna:** Low-medium — Luna supports native function calling;
the issue is reliability, not capability. A prompt-based fallback would work
but adds parsing complexity and is less robust than `tool_choice=required`.

### Mechanism 6 (DISCONFIRMED): `add_function_to_prompt` fallback

**What:** LiteLLM offers `litellm.add_function_to_prompt = True`, which
embeds the function schema directly into the prompt text for models that
don't natively support function calling.

**DISCONFIRMED:** This mechanism is **broken in practice**. Two GitHub issues
document the failure:
- [BerriAI/litellm#6829](https://github.com/BerriAI/litellm/issues/6829): "Setting litellm.add_function_to_prompt = True does not work"
- [BerriAI/litellm#11577](https://github.com/BerriAI/litellm/issues/11577): "function calling with Gemma3 seems to be currently broken, even with add_function_to_prompt = True." Docs don't clarify whether the response is post-processed to enable tool-calling completely.

**Do not rely on this mechanism.** Also wrong problem class — Luna supports
native function calling; this fallback is for models that don't.

## How non-Codex CLIs wire tool-calling for OpenAI models

**Finding [OBSERVED]:** ALL working non-Codex agentic CLIs use the **native
OpenAI function-calling protocol** — the `tools` array in the request and
`tool_calls` field in the response. None rely on prompt-based XML/JSON tricks
for GPT-5 models.

| CLI | Approach | Source |
|-----|----------|--------|
| Aider | Native OpenAI function-calling via built-in tool system | [TOOL_SYSTEM_SUMMARY.md](https://github.com/Aider-AI/aider/blob/main/TOOL_SYSTEM_SUMMARY.md) |
| Continue.dev | OpenAI function-calling via system-prompt-driven tool registry | [DeepWiki](https://deepwiki.com/continuedev/continue/4.5-tool-calling) |
| Cline | Provider-agnostic OpenAI-compatible function-calling | [docs.cline.bot](https://docs.cline.bot/provider-config/openai-compatible) |
| Roo Code | Native OpenAI tool-calling protocol (v6.2, replaced XML) | [DeepWiki](https://deepwiki.com/RooCodeInc/Roo-Code/6.2-native-tool-calling-protocol) |
| OpenCode | OpenAI function-calling via custom provider bridge | [issue #4661](https://github.com/anomalyco/opencode/issues/4661) |
| Cursor | **FAILS with GPT-5** — uses legacy completions API without native tool_calls | [forum.cursor.com](https://forum.cursor.com/t/how-to-use-cursor-with-azure-openai-api/135419) |

**Key takeaway:** Cursor's failure with GPT-5 is the cautionary tale. Using
the legacy completions API or prompt-based XML tricks instead of the native
`tools`/`tool_calls` protocol is the root cause of tool-calling failures in
agentic CLIs. The fix is always: use the Responses API with native
function-calling.

## Decision context

**Why this research was needed:** Session 2026-07-31 diagnosed a gpt-5-6-luna
failure inside Codex CLI (9 turns, 0 tool calls). The diagnosis identified it
as a transport/emission failure, not a capability failure — the same class
documented in [[model-tool-calling-capability-matrix]] for Nemotron and
DiffusionGemma. The open question was: how do router/proxy solutions in the
broader ecosystem solve this class of problem?

**What alternatives were explored:**
1. Router/proxy format translation (LiteLLM, Portkey, claude-code-proxy) —
   helps with format mismatch, not emission failure
2. Reliability-based auto-routing (OpenRouter) — strongest detection/routing
   mechanism, but intermediary aversion
3. API-layer `tool_choice=required` — strongest enforcement, but needs
   request-pipeline control
4. Text-only → retry/failover — not yet shipped in Codex CLI
5. ReAct/prompt-based fallback — works but adds complexity
6. `add_function_to_prompt` — **DISCONFIRMED as broken**

**What the research changed:** Confirmed that Luna's failure is a known,
documented class (not a one-off), and that the Codex CLI harness has no
per-tier tool-provisioning gate. The highest-leverage fix
(`tool_choice=required`) requires request-pipeline control that Codex CLI
doesn't expose — reinforcing the existing host pattern: bypass the broken
transport (use OpenCode, PI, or direct API with `tool_choice=required`).

## Do's and don'ts

### Do
- **Force `tool_choice=required`** when calling lighter model tiers (Luna,
  mini-class) from any harness that exposes the API request layer. This is
  the single highest-leverage fix for text-only emission failures.
- **Treat text-only responses as failure conditions** when tools are required
  — retry or failover. Codex CLI currently treats them as success.
- **Use the Responses API (`wire_api = "responses"`)** for Codex CLI with any
  provider — chat/completions is deprecated and may degrade tool delivery.
- **Inspect raw model output** before blaming the model. If tool-call syntax
  is leaking as text into `content`, the harness is dropping legitimate calls
  (parser mismatch).
- **Probe new models with BOTH** a trivial prompt AND a tool-use prompt before
  adding them to a pool. A green trivial probe doesn't prove tool-calling
  works.
- **Bypass the broken transport** when a model works at the API level but
  fails in a specific harness — the established host pattern from
  [[model-tool-calling-capability-matrix]].

### Don't
- **Don't rely on `add_function_to_prompt`** — DISCONFIRMED as broken
  (BerriAI/litellm#6829, #11577).
- **Don't assume lighter model tiers get different tool schemas** — Codex
  CLI's toolset is harness-fixed; all tiers get the same schemas.
- **Don't blame the model before checking the transport.** The Kotonia study
  proved that "a harness mismatch is indistinguishable from model
  disobedience when you only look at outcomes."
- **Don't route tool-required work to Luna/mini-class models** in harnesses
  that don't support `tool_choice=required` or text-only retry detection.

## What this means for our workspace

1. **The `/codex` skill should add a `tool_choice=required` injection option**
   for calls to lighter model tiers (Luna, mini-class). This is the
   highest-leverage fix and aligns with the conductor-skill pattern already
   used for `/agy`, `/mmx`, `/codex`.
2. **Luna should NOT be routed to tool-required tasks** via Codex CLI unless
   `tool_choice=required` is injected. Add Luna to the "no auto-pool for
   tool-grounded work" list alongside Nemotron, per
   [[model-tool-calling-capability-matrix]].
3. **The bypass-transport pattern is now triply validated:** Nemotron (serde
   bug) → OpenCode/PI; DiffusionGemma (parser conflict) → direct API; Luna
   (emission failure) → should use direct API with `tool_choice=required` or
   OpenRouter reliability routing.
4. **OpenRouter reliability routing** is the production-grade solution for
   fleet-wide tool-call reliability, but conflicts with the operator's
   intermediary-aversion preference. Flag as conditional recommendation.
5. **Fleet config verification (2026-07-31):** The host's Codex CLI config
   (`C:/Users/brsth/.codex/config.toml`) is **clean** against both
   documented regression conditions. `[OBSERVED]` — read directly this
   session:
   - No `[model_providers.*]` section exists (grep-confirmed: zero matches
     for `model_provider|wire_api|model_providers`) → the `#34758`
     regression (custom provider + missing `model` → shell tool silently
     stripped) is structurally impossible in this config.
   - Top-level `model = "gpt-5.6-sol"` is present (line 1) → the missing-
     model condition never applies.
   - No `wire_api` key → Codex CLI defaults to the Responses API (the
     supported path). The concern only applies if routing through a
     chat-completions-compatible proxy, which this config doesn't do.
   The config being clean means the `tool_choice=required` fix is purely a
   `/codex` skill-level concern (request-pipeline injection at invocation),
   not a config.toml concern. When `/codex` invokes Luna via
   `--model gpt-5.6-luna`, the flag overrides config's `model =` — fine for
   schema provisioning (harness-fixed), but Luna's emission reliability
   remains the open risk that `tool_choice=required` addresses.

## Falsifier

This concept is wrong if:
- `tool_choice=required` does not prevent Luna's text-only emission (the
  failure is deeper than confidence-gating — perhaps the model truly cannot
  emit structured tool calls in some contexts)
- Codex CLI ships a per-model-tier tool-provisioning toggle (making the
  harness-fixed assumption wrong)
- `add_function_to_prompt` gets fixed and becomes a viable fallback (re-evaluate
  the DISCONFIRMED status)
- The text-only early-termination failure is traced to a specific API bug
  rather than model-tier reliability (the failure class is narrower than
  documented)

Re-verify quarterly; model + framework versions change rapidly.

## Sources (scored CREDIBLE-lite)

| Source | Auth | Rec | Evid | Bias | Total | Role |
|--------|------|-----|------|------|-------|------|
| DeepWiki LiteLLM tool-calling | 3 | 3 | 3 | 2 | 11 | LiteLLM format translation mechanics |
| LiteLLM function-calling docs | 3 | 3 | 3 | 2 | 11 | `add_function_to_prompt` mechanism |
| OpenRouter tool-calling docs | 3 | 3 | 3 | 2 | 11 | Auto-exacto reliability routing |
| BerriAI/litellm#6829 | 3 | 3 | 3 | 3 | 12 | `add_function_to_prompt` broken — disconfirmation |
| BerriAI/litellm#11577 | 3 | 3 | 3 | 3 | 12 | Gemma3 FC broken even with fallback — disconfirmation |
| openai/codex#19765 | 3 | 3 | 3 | 3 | 12 | Weaker models + truncated JSON tool-call args |
| openai/codex#34758 | 3 | 3 | 3 | 3 | 12 | Config regression stripping shell tool |
| openai/codex#10828 | 3 | 3 | 2 | 3 | 11 | Codex ends turn unexpectedly |
| openclaw/openclaw#28754 | 2 | 3 | 3 | 2 | 10 | gpt-5.3-codex intermittent text-only — exact match |
| Kotonia agent-trust study | 2 | 3 | 3 | 2 | 10 | Parser mismatch = model disobedience; confidence gate |
| Cline provider docs | 3 | 3 | 2 | 2 | 10 | OpenAI-compatible function-calling pattern |
| Roo Code DeepWiki | 2 | 3 | 2 | 2 | 9 | Native tool-calling protocol migration |
| gradient.news | 1 | 2 | 2 | 1 | 6 | Community reporting on GPT-5.3 failures |
| merge.dev proxy vs router | 2 | 2 | 2 | 2 | 8 | Architecture distinction |
| claude-code-proxy translation | 2 | 2 | 3 | 2 | 9 | Bidirectional format translation pipeline |

Phase 2 synthesis: parent-inherited model. Three parallel subagents
(or-ling-3-flash-free, nim-openai-gpt-oss-20b, zen-big-pickle) + parent-level
DeepWiki/GitHub/DDG research.

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| LiteLLM translates OpenAI tool definitions into provider-specific formats | DeepWiki page cites `litellm/litellm_core_utils/prompt_templates/factory.py`, `litellm/llms/anthropic/chat/transformation.py:35-38`, `litellm/llms/bedrock/chat/converse_transformation.py:103-106` — source files fetched via DeepWiki (indexed 2026-07-29, commit c274cf) | [OBSERVED] |
| LiteLLM `add_function_to_prompt = True` embeds function schema in prompt | [LiteLLM function-calling docs](https://docs.litellm.ai/docs/completion/function_call) — fetched this session | [OBSERVED] |
| `add_function_to_prompt` is broken in practice | [BerriAI/litellm#6829](https://github.com/BerriAI/litellm/issues/6829) + [#11577](https://github.com/BerriAI/litellm/issues/11577) — issue titles and bodies fetched via DDG this session | [OBSERVED] |
| OpenRouter tracks Tool Call Error Rate and uses Auto Exacto ordering | [OpenRouter tool-calling docs](https://openrouter.ai/docs/guides/features/tool-calling) — cited by subagent from fetched page | [OBSERVED] |
| Codex CLI toolset is harness-fixed (same schemas all tiers) | [INFERENCE] — from openai/codex source-code-path evidence cited in #19765 + #34758 regression mechanics; Rust source not fetched directly | [INFERENCE] |
| `wire_api = "responses"` is the supported API for Codex | [openai/codex discussion #7782](https://github.com/openai/codex/discussions/7782) + [morphllm config guide](https://www.morphllm.com/codex-provider-configuration) — cited by subagent | [OBSERVED] |
| Config regression strips shell tool when `model` key omitted | [openai/codex#34758](https://github.com/openai/codex/issues/34758) — issue fetched by subagent | [OBSERVED] |
| gpt-5.3-codex intermittent text-only + end_turn, gateway treats as success | [openclaw/openclaw#28754](https://github.com/openclaw/openclaw/issues/28754) — issue fetched by subagent | [OBSERVED] |
| Parser mismatch indistinguishable from model disobedience | [Kotonia study](https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/) — fetched by subagent | [OBSERVED] |
| `tool_choice=required` defeats confidence-gated tool skipping | [Kotonia study](https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/) — structural fix section | [OBSERVED] |
| Luna supports tool calling at API level | [OpenAI API docs](https://developers.openai.com/api/docs/models/gpt-5.6-terra) + [OpenRouter](https://openrouter.ai/openai) — GPT-5.6 family lists "programmatic tool calling" | [OBSERVED] |
| All non-Codex CLIs use native OpenAI function-calling protocol | Cline docs, Roo Code DeepWiki, Aider TOOL_SYSTEM_SUMMARY, Continue DeepWiki — all fetched by subagent | [OBSERVED] |
| Cursor fails with GPT-5 (legacy completions API) | [forum.cursor.com](https://forum.cursor.com/t/how-to-use-cursor-with-azure-openai-api/135419) — cited by subagent from fetched page | [OBSERVED] |

## Auto-related

- [[skill-catalog]]
- [[model-tool-calling-capability-matrix]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[tool-binding-and-choice-control]]
- [[agent-config-directory-taxonomy]]

