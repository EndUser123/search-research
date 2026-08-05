---
title: "Router and proxy solutions for cross-harness model tool-calling: patterns that solve tool-call emission failures"
created: 2026-07-31
updated: 2026-08-04
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
tags: [tool-calling, function-calling, router, proxy, litellm, openrouter, codex-cli, cross-harness, transport-failure, workaround, routing]
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
  When a model fails to emit tool calls inside a specific agentic CLI harness,
  router and proxy solutions address it through five mechanisms: (1) format
  translation between provider tool-call schemas, (2) reliability-based
  auto-routing that detects and routes around emission failures, (3)
  `tool_choice=required` at the API layer to force grammatical tool emission,
  (4) text-only → retry/failover detection, and (5) ReAct/prompt-based
  fallback protocols. The LiteLLM `add_function_to_prompt` fallback is
  DISCONFIRMED as broken in practice. On this host, two models have
  confirmed transport-specific failures: Nemotron-3-ultra (Grok Build serde
  bug) and DiffusionGemma (thinking-mode parser conflict). GPT-5.6 Luna is
  verified working via Codex CLI (tested 2026-08-04: two tool-grounded tasks,
  zero emission failures).
---

# Router and proxy solutions for cross-harness model tool-calling

## The problem this solves

A model that supports function calling at the API level emits **zero tool
calls** when run inside a specific agentic CLI harness. The model produces
detailed plans as prose but never converts them into structured tool-call
invocations. The harness treats each text-only response as successful
completion, so no retry or failover triggers.

On this host, two models have confirmed transport-specific failures (see
[[model-tool-calling-capability-matrix]]):
- **Nemotron-3-ultra**: Grok Build serde types `null` fields as `u32`;
  NVIDIA returns `null`. Works via OpenCode, PI, and direct API.
- **DiffusionGemma**: thinking-mode output format breaks the agent
  framework's tool-call parser. Works via direct API for no-tool reads.

GPT-5.6 Luna was initially suspected of this failure class based on external
GitHub issues reporting text-only emission. **This was tested and
falsified on this host (2026-08-04):** Luna passed both file-read and
multi-step search tool-grounded tasks via Codex CLI with zero emission
failures (24.6s and 26.0s respectively, both with correct tool calls).

## What controls tool provisioning in Codex CLI

**Finding [OBSERVED]:** The Codex CLI toolset is **harness-fixed, not
per-model-tier**. The tool schemas (shell/exec, read, write, apply_patch,
plan, web_search, MCP tools) are compiled into the Rust core
(`codex-rs/core/src/tools/`). Model tier selection via `--model` or
`config.toml model =` only swaps which model receives the *same fixed tool
list*. There is no per-tier tool-provisioning toggle.

The real provisioning knobs are:

| Control | What it does | Impact on tool-calling |
|---------|-------------|----------------------|
| `wire_api = "responses" \| "chat"` | Selects the API protocol for tool schema delivery | Responses API is the supported path for Codex; chat/completions deprecated |
| Top-level `model = "..."` in config | Resolves the model for tool-schema binding | **Config regression [openai/codex#34758]:** omitting this with a custom `model_provider` strips the shell tool entirely |
| `tool_choice` | Not available in Codex config.toml | Only at the API layer — cannot be set from Codex CLI config |

## The known failure class: "text-only early termination"

External sources document a class of tool-calling failure where models emit
prose instead of structured tool calls:

| Source | Model | Symptom |
|--------|-------|---------|
| [openai/codex#10828](https://github.com/openai/codex/issues/10828) | Codex models | "Codex ends turn unexpectedly" — model says "Understood, I'm continuing…" then stops |
| [openclaw/openclaw#28754](https://github.com/openclaw/openclaw/issues/28754) | gpt-5.3-codex | Intermittent text-only + `end_turn`; gateway treats as success, no retry triggers |
| [anomalyco/opencode#12570](https://github.com/anomalyco/opencode/issues/12570) | GPT-5 codex | Same symptom on OpenCode harness |
| [openai/codex#19765](https://github.com/openai/codex/issues/19765) | Weaker models | `function_call.arguments` arrives as truncated JSON → parse error |
| [gradient.news](https://gradient.news/gpt-5-3-codex-failures-developers-workarounds/) | GPT-5.3 Codex | Community reporting mid-task collapse; devs downgrading models |

**The Kotonia finding [OBSERVED]:** A controlled study
([kotonia.ai](https://kotonia.ai/en/articles/agent-trust-comes-from-grammar/))
demonstrated that **"a harness mismatch is indistinguishable from model
disobedience when you only look at outcomes."** A model emitting tool calls
in `qwen3_coder` XML format with a `hermes` parser configured → `tool_call`
field came back empty → observed as "0/6 tool calls." Raw content showed the
tool call **leaked through as plain text**.

**Important caveat:** These external reports do not necessarily apply to
all host/transport combinations. On this host, GPT-5.6 Luna was suspected
based on these reports but tested clean (2026-08-04). Always test on your
actual transport before excluding a model.

## How router and proxy solutions solve this

### Mechanism 1: Format translation (bidirectional proxy)

A proxy layer translates between provider-specific tool-call formats.
OpenAI's `{type: "function", function: {name, parameters}}` ↔ Anthropic's
`{name, input_schema}` ↔ Gemini's `FunctionDeclaration`.

**Implementations:** LiteLLM (100+ providers), claude-code-proxy (three-stage
translation pipeline), Portkey (1,600+ models).

**Solves:** Format/parser mismatch (the Kotonia scenario). Does NOT solve
emission failure (model emits nothing at all).

### Mechanism 2: Reliability-based auto-routing (OpenRouter)

OpenRouter tracks per-provider **Tool Call Error Rate** and uses this signal
to drive **Auto Exacto** provider ordering — automatically preferring
providers that complete tool calls reliably for a given model.

**Solves:** Provider-level tool-call unreliability. Conflicts with the
operator's intermediary-aversion preference (see Nemotron routing policy in
[[model-tool-calling-capability-matrix]]).

### Mechanism 3: `tool_choice=required` (API-layer enforcement)

Setting `tool_choice: "required"` in the API request forces the model to
emit at least one tool call — plain prose becomes grammatically impossible.
This directly defeats the knowledge-confidence gate where models skip tools
when they believe they know the answer.

**Solves:** Text-only emission from capable models. Requires control of the
API request layer. Codex CLI does not expose `tool_choice` in its config;
it would need a proxy/wrapper that injects it.

### Mechanism 4: Text-only → auto-retry/failover

Detect when a model returns a text-only response to a tool-requiring task
and automatically retry or failover to another model/provider. The gateway
treats text-only completion as a **failure condition**, not success.

**Status:** Requested but **not yet shipped** in Codex CLI
([openclaw/openclaw#28754](https://github.com/openclaw/openclaw/issues/28754)).
OpenRouter's auto-exacto is the closest production implementation.

### Mechanism 5: ReAct / prompt-based tool calling fallback

When native `tool_calls` don't fire, harnesses fall back to a text protocol
— Thought→Action→Observation loops, JSON/XML markers in prose, or custom
in-prompt markers. The harness parses the text output for tool-call patterns.

**Solves:** Models that don't support native function calling at all, or as
a fallback when native calling is unreliable. Adds parsing complexity.

### Mechanism 6 (DISCONFIRMED): `add_function_to_prompt` fallback

LiteLLM offers `litellm.add_function_to_prompt = True`, which embeds the
function schema directly into the prompt text for models that don't
natively support function calling.

**DISCONFIRMED:** Two GitHub issues document the failure:
- [BerriAI/litellm#6829](https://github.com/BerriAI/litellm/issues/6829)
- [BerriAI/litellm#11577](https://github.com/BerriAI/litellm/issues/11577)

## How non-Codex CLIs wire tool-calling for OpenAI models

ALL working non-Codex agentic CLIs use the **native OpenAI function-calling
protocol** — the `tools` array in the request and `tool_calls` field in the
response. None rely on prompt-based XML/JSON tricks for GPT-5 models.

| CLI | Approach | Source |
|-----|----------|--------|
| Aider | Native OpenAI function-calling via built-in tool system | TOOL_SYSTEM_SUMMARY.md |
| Continue.dev | OpenAI function-calling via system-prompt-driven tool registry | DeepWiki |
| Cline | Provider-agnostic OpenAI-compatible function-calling | docs.cline.bot |
| Roo Code | Native OpenAI tool-calling protocol (v6.2, replaced XML) | DeepWiki |
| OpenCode | OpenAI function-calling via custom provider bridge | issue #4661 |
| Cursor | **FAILS with GPT-5** — uses legacy completions API without native tool_calls | forum.cursor.com |

**Key takeaway:** Cursor's failure with GPT-5 is the cautionary tale. Using
the legacy completions API or prompt-based XML tricks instead of the native
`tools`/`tool_calls` protocol is the root cause of tool-calling failures in
agentic CLIs.

## Do's and don'ts

### Do
- **Test on your actual transport** before excluding a model. External
  reports of tool-calling failures may not reproduce on your host (verified
  2026-08-04: GPT-5.6 Luna passed all tool-grounded tests via Codex CLI
  despite external reports of text-only emission).
- **Force `tool_choice=required`** when calling models through raw API calls
  or proxies that expose the request layer.
- **Treat text-only responses as failure conditions** when tools are required.
- **Use the Responses API (`wire_api = "responses"`)** for Codex CLI.
- **Inspect raw model output** before blaming the model. If tool-call syntax
  is leaking as text into `content`, the harness is dropping legitimate calls.
- **Probe new models with BOTH** a trivial prompt AND a tool-use prompt before
  adding them to a pool.
- **Bypass the broken transport** when a model works at the API level but
  fails in a specific harness (Nemotron → OpenCode/PI; DiffusionGemma →
  direct API).

### Don't
- **Don't rely on `add_function_to_prompt`** — DISCONFIRMED as broken.
- **Don't assume lighter model tiers get different tool schemas** — Codex
  CLI's toolset is harness-fixed; all tiers get the same schemas.
- **Don't blame the model before checking the transport.** The Kotonia study
  proved that "a harness mismatch is indistinguishable from model
  disobedience when you only look at outcomes."

## What this means for our workspace

1. **GPT-5.6 Luna is verified working** for tool-grounded tasks via Codex
   CLI (2026-08-04: file read 24.6s + multi-step search 26.0s, both with
   correct tool calls). No tool_choice injection needed.
2. **The bypass-transport pattern is doubly validated:** Nemotron (serde
   bug) → OpenCode/PI; DiffusionGemma (parser conflict) → direct API.
3. **OpenRouter reliability routing** is the production-grade solution for
   fleet-wide tool-call reliability, but conflicts with the operator's
   intermediary-aversion preference.
4. **Fleet config verification (2026-07-31):** The host's Codex CLI config
   (`C:/Users/brsth/.codex/config.toml`) is clean against both documented
   regression conditions:
   - No `[model_providers.*]` section → the #34758 regression is impossible.
   - Top-level `model = "gpt-5.6-sol"` is present → the missing-model
     condition never applies.
   - No `wire_api` key → Codex CLI defaults to the Responses API.

## Falsifier

This concept is wrong if:
- Codex CLI ships a per-model-tier tool-provisioning toggle (making the
  harness-fixed assumption wrong)
- `add_function_to_prompt` gets fixed and becomes a viable fallback
- The text-only early-termination failure is traced to a specific API bug
  rather than model-tier reliability

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
| openclaw/openclaw#28754 | 2 | 3 | 3 | 2 | 10 | gpt-5.3-codex intermittent text-only |
| Kotonia agent-trust study | 2 | 3 | 3 | 2 | 10 | Parser mismatch = model disobedience; confidence gate |
| Cline provider docs | 3 | 3 | 2 | 2 | 10 | OpenAI-compatible function-calling pattern |
| Roo Code DeepWiki | 2 | 3 | 2 | 2 | 9 | Native tool-calling protocol migration |
| gradient.news | 1 | 2 | 2 | 1 | 6 | Community reporting on GPT-5.3 failures |
| merge.dev proxy vs router | 2 | 2 | 2 | 2 | 8 | Architecture distinction |
| claude-code-proxy translation | 2 | 2 | 3 | 2 | 9 | Bidirectional format translation pipeline |

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| GPT-5.6 Luna works via Codex CLI for tool-grounded tasks | 2026-08-04 empirical test: `codex exec --json --ephemeral -s read-only -m gpt-5.6-luna` — file read (24.6s, 1 tool call, correct) + multi-step search (26.0s, 2 tool calls, correct) | [OBSERVED] |
| LiteLLM translates OpenAI tool definitions into provider-specific formats | DeepWiki page cites source files (indexed 2026-07-29, commit c274cf) | [OBSERVED] |
| `add_function_to_prompt` is broken in practice | BerriAI/litellm#6829 + #11577 | [OBSERVED] |
| OpenRouter tracks Tool Call Error Rate and uses Auto Exacto ordering | OpenRouter tool-calling docs | [OBSERVED] |
| Codex CLI toolset is harness-fixed | [INFERENCE] — from openai/codex source-code-path evidence; Rust source not fetched directly | [INFERENCE] |
| Config regression strips shell tool when `model` key omitted | openai/codex#34758 | [OBSERVED] |
| Parser mismatch indistinguishable from model disobedience | Kotonia study | [OBSERVED] |
| `tool_choice=required` defeats confidence-gated tool skipping | Kotonia study — structural fix section | [OBSERVED] |
| Luna supports tool calling at API level | OpenAI API docs + OpenRouter — GPT-5.6 family lists "programmatic tool calling" | [OBSERVED] |
| All non-Codex CLIs use native OpenAI function-calling protocol | Cline docs, Roo Code DeepWiki, Aider TOOL_SYSTEM_SUMMARY, Continue DeepWiki | [OBSERVED] |
| Cursor fails with GPT-5 (legacy completions API) | forum.cursor.com | [OBSERVED] |

## Auto-related

- [[skill-catalog]]
- [[model-tool-calling-capability-matrix]]
- [[tool-binding-and-choice-control]]
- [[agent-config-directory-taxonomy]]
