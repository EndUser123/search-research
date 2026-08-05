---
title: "Trace-eval-improve loops for agent fleets: from transcripts to measurable improvement"
created: 2026-08-05
source: session-2026-08-05 (/www research on self-improving agent patterns we don't have)
sources:
  - external: https://www.langchain.com/blog/traces-start-agent-improvement-loop (LangChain, Mar 2026)
  - external: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop (OpenAI Cookbook, May 2026)
  - external: https://github.com/context-labs/HALO (HALO, MIT license)
  - external: https://github.com/promptfoo/promptfoo (Promptfoo, acquired by OpenAI Mar 2026)
  - external: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents (Anthropic evals, Jan 2026)
  - external: https://arxiv.org/abs/2507.19457 (GEPA, evolutionary prompt optimization)
  - external: https://arxiv.org/abs/2509.25370 (Agent Error Taxonomy / MAST, NeurIPS 2025)
  - external: https://github.com/open-telemetry/semantic-conventions-genai (OpenTelemetry GenAI SemConv)
  - external: https://www.braintrust.dev/articles/ai-agent-evaluation-framework (Braintrust, Feb 2026)
  - external: https://codex.danielvaughan.com/2026/05/18/codex-cli-agent-improvement-loop-traces-evals-harness-engineering-flywheel/ (Codex CLI flywheel, May 2026)
tags: [trace-eval-improve, agent-observability, evaluation-harness, trajectory-analysis, eval-driven-development, agent-improvement-loop, otel-genai, promptfoo, halo, failure-taxonomy]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  A formalized trace→eval→improve loop turns agent harness engineering from
  ad-hoc craft into data-driven discipline. The loop: collect execution traces
  (JSONL with tool calls, decisions, errors, outcomes), enrich with eval scores
  (deterministic + LLM-as-judge + human), diagnose failure patterns, propose
  ONE harness change, implement via coding agent, validate against eval suite,
  repeat. Key tools: HALO (RLM-based trace decomposition), Promptfoo (trace →
  eval test cases), GEPA (evolutionary prompt optimization). The workspace
  already has the raw materials (JSONL transcripts, behavioral correction
  tracking, /aar terminal-outcome comparison) but lacks the formalized loop:
  no structured eval harness, no automated trajectory analysis, no eval ratchet
  that prevents regressions. The critical insight from Huang 2024: pure
  intrinsic self-correction fails — the loop must ground on tool/test feedback,
  not vibes. The receipt rule and verification hooks are the external signals.
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/cross-session-transcript-mining-continuous-improvement.md
    type: extends
  - target: wiki/concepts/behavioral-reset-pattern-reflexion-and-external-critique.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
  - target: wiki/concepts/structured-behavioral-memory-architecture.md
    type: related
  - target: wiki/concepts/token-optimization-patterns-for-agent-fleets.md
    type: related
---

# Trace-eval-improve loops for agent fleets: from transcripts to measurable improvement

## Decision context

**Why this research was needed:** the operator asked about "agent improvement loops with traces and evals" as a pattern the workspace doesn't have. The workspace accumulates session transcripts, tracks behavioral corrections, and runs /aar reviews — but these are not chained into a formalized loop with structured evaluation harnesses and automated trajectory analysis. The pieces exist; they aren't connected.

**The fundamental loop:**
```
Run agent → Collect traces (JSONL)
    → Enrich with eval scores (deterministic + LLM-judge + human)
    → Diagnose failure patterns (taxonomy + clustering)
    → Propose ONE harness change
    → Implement via coding agent
    → Run eval suite (validate — does it pass?)
    → Commit → Repeat
```

Each cycle adds new eval test cases, creating a **monotonic ratchet** that prevents regressions.

## Key Findings

### The four architecture patterns

**Pattern A: HALO Loop (Automated Harness Optimization)**
```
Traces (OTel JSONL) → HALO RLM Engine (failure decomposition)
    → Ranked harness change report → Coding agent implements
    → Redeploy → New traces → repeat
```
HALO uses a specialized RLM (not a general LLM) because traces are extremely long and general models overfit to single-trace errors. Source: [context-labs/HALO](https://github.com/context-labs/HALO)

**Pattern B: The Flywheel (OpenAI/Codex CLI)**
```
Agent run → Traces + feedback → Generate evals (Promptfoo YAML)
    → Diagnose patterns → Rank changes → Codex handoff
    → Implement ONE change → Run eval suite → Commit → repeat
```
Key: one recommendation per cycle. Each cycle produces a durable artifact. Eval suite grows monotonically. Source: [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop)

**Pattern C: Dual Loop (Arize/Phoenix)**
```
Agent loop (frequent, live data): fetch → score → generate → trace
Improvement loop (less frequent, human-in-loop): retrieve failed traces
    → cluster → propose smallest safe change → human review → deploy
```
Two loops at different timescales. Source: [Arize Phoenix](https://phoenix.arize.com/)

**Pattern D: Pydantic Self-Improving**
```
Agent acts → output guardrail (retry/fail) → trace to SQLite
    → conversation search over past runs → managed prompts (versioned)
    → online evals on sampled traffic → GEPA optimizer proposes changes
    → human approves → new prompt version live
```
Source: [pydantic.dev/articles/when-agents-improve-agents](https://pydantic.dev/articles/when-agents-improve-agents)

### Multi-layer eval grading

| Layer | Type | Speed | Catches |
|-------|------|-------|---------|
| **Code-based** | Deterministic (assertions, regex, schema) | Fast | Format errors, missing fields, wrong types |
| **Model-based** | LLM-as-judge (rubric scoring) | Medium | Quality, completeness, hallucination |
| **Human** | Expert review | Slow | Nuance, domain correctness, edge cases |

Key insight from Anthropic (Jan 2026): LLM-as-judge graders must be **calibrated against human experts**. Grade each dimension in isolation, prefer binary pass/fail over Likert scales, randomize order to avoid position bias.

### Agent failure taxonomy (MAST)

The MAST taxonomy (Cemri et al., NeurIPS 2025) classifies 14 failure modes from 1,642 annotated traces across 5 categories: memory, reflection, planning, action, and system-level. This enables systematic diagnosis rather than ad-hoc debugging.

**Workspace mapping:** the workspace's behavioral correction tracking (`scan_corrections.ps1`) already clusters corrections — but by symptom, not by the MAST taxonomy. Adopting a structured failure taxonomy would make clustering more actionable.

### OpenTelemetry GenAI semantic conventions

The `gen_ai.*` attribute namespace provides vendor-neutral tracing across all LLM providers: operation names, token metrics, latency, model metadata, agent trace hierarchy, tool invocations, MCP calls, quality evaluation as span attributes.

**Workspace relevance:** the workspace's JSONL transcripts are custom-formatted. Adopting OTel GenAI conventions would make traces portable across observability backends (Langfuse, Phoenix, LangSmith) and would standardize what gets logged.

### GEPA: evolutionary prompt optimization

GEPA (arXiv 2507.19457) uses reflection to evolve text components (prompts, code, configs). It uses an evaluator you provide, then iteratively mutates and selects the best-performing variants. Outperforms MIPROv2 by 10%+ on benchmarks. Can optimize **any text artifact** — not just prompts.

**Workspace relevance:** GEPA could automate the improvement step where HALO or manual analysis identifies what to change. Instead of a human writing the improved AGENTS.md rule, GEPA proposes and tests variants against the eval suite.

### Eval-driven development (EDD)

EDD treats evals as the primary release contract:
1. Define success criteria before writing code
2. Curate a golden dataset (~100 examples with expected outputs)
3. Write eval tests that measure functional quality
4. Run evals automatically on every commit
5. Use failures as new test cases (the ratchet)

Source: [DeepEval](https://deepeval.com/blog/eval-driven-development)

## Honest trade-offs

**Like:** the loop makes improvement measurable and prevents regressions; the eval ratchet means each improvement is permanent; OTel standardization makes traces portable; HALO/Promptfoo/GEPA are mature open-source tools.

**Dislike:** building an eval harness is significant upfront investment; LLM-as-judge has known biases (position, verbosity, self-preference); golden datasets require ongoing maintenance; the workspace's queries are highly contextual, making generic eval suites less useful; the Huang 2024 caveat means any loop without external grounding is unreliable.

## Falsifier

This concept is wrong if, within 6 months:
- The loop is implemented but eval scores don't improve (the loop is theater)
- Eval-driven changes cause regressions that the eval suite doesn't catch (the evals are insufficient)
- A vendor ships built-in agent observability that makes custom trace infrastructure obsolete
- The golden dataset becomes stale and produces false confidence (eval rot)

## What this means for our workspace

**What we already have (the raw materials):**

| Component | Workspace equivalent | Gap |
|-----------|---------------------|-----|
| Trace collection | JSONL session transcripts | Not OTel-formatted; no token/latency metrics |
| Eval scoring | /aar terminal-outcome comparison | Not automated; no eval suite |
| Failure diagnosis | `scan_corrections.ps1` pattern clustering | Human-driven; not taxonomy-structured |
| Harness changes | AGENTS.md rule additions + hook updates | Manual; no validation against eval suite |
| Eval ratchet | None | **Missing entirely** |
| Golden dataset | None | **Missing entirely** |

**Recommended implementation path:**

1. **Start with the eval ratchet** — convert the workspace's existing correction clusters into Promptfoo test cases. Each past correction = one eval assertion. This creates the regression-prevention floor with zero new infrastructure.

2. **Add OTel GenAI conventions to trace format** — enhance JSONL transcript writing to include `gen_ai.*` attributes. Makes traces compatible with Langfuse/Phoenix for visualization.

3. **Adopt MAST failure taxonomy** — reclassify existing behavioral correction clusters into the MAST 5-category taxonomy. Makes diagnosis systematic rather than ad-hoc.

4. **Run the loop quarterly** — don't try to run it continuously (the workspace's volume doesn't justify real-time). A quarterly batch: collect 3 months of traces, run HALO-style analysis, propose ranked changes, implement top 3, validate against eval suite.

5. **GEPA for prompt optimization** — once the eval suite exists, GEPA can automatically propose improved AGENTS.md rules and test them against the evals. This is the automated improvement step.

**Critical constraint:** any loop must ground on external signals (test results, hook outputs, command exit codes) — not on LLM self-assessment. The Huang 2024 caveat is binding. The workspace's receipt rule and verification hooks are the external grounding that makes this safe.

## Related

- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@extends — this concept extends the survey with the formalized trace→eval→improve loop
- [[cross-session-transcript-mining-continuous-improvement]]@extends — transcript mining is the data source for the loop
- [[behavioral-reset-pattern-reflexion-and-external-critique]]@related — Reflexion as the reflection step in the loop
- [[mechanical-enforcement-over-behavioral-reminder]]@related — mechanical eval gates beat behavioral rules for catching regressions
- [[structured-behavioral-memory-architecture]]@related — accumulated behavioral data feeds the eval suite
- [[token-optimization-patterns-for-agent-fleets]]@related — traces also serve token optimization analysis

## Sources

**Improvement loop frameworks:**
- LangChain: Traces Start Agent Improvement Loop — https://www.langchain.com/blog/traces-start-agent-improvement-loop
- OpenAI Cookbook: Agent Improvement Loop — https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- Codex CLI Flywheel — https://codex.danielvaughan.com/2026/05/18/codex-cli-agent-improvement-loop-traces-evals-harness-engineering-flywheel/

**Tools:**
- HALO — https://github.com/context-labs/HALO
- Promptfoo — https://github.com/promptfoo/promptfoo
- GEPA — https://arxiv.org/abs/2507.19457 / https://github.com/gepa-ai/gepa
- Langfuse — https://langfuse.com
- Arize Phoenix — https://phoenix.arize.com/
- Braintrust — https://www.braintrust.dev/articles/ai-agent-evaluation-framework

**Evaluation methodology:**
- Anthropic: Demystifying Evals for AI Agents — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- DeepEval: Eval-Driven Development — https://deepeval.com/blog/eval-driven-development

**Self-correction grounding:**
- LLMs Cannot Self-Correct Yet (Huang 2024, 600+ citations) — https://arxiv.org/abs/2310.01798

**Failure taxonomy:**
- MAST Taxonomy (NeurIPS 2025) — https://arxiv.org/abs/2509.25370
- Microsoft MAST v2.0 — https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/security/Taxonomy-of-Failure-Modes-in-Agentic-AI-Systems-v2-0.pdf

**Observability:**
- OpenTelemetry GenAI SemConv — https://github.com/open-telemetry/semantic-conventions-genai

**Research method:** /www pipeline, parallel or-ling-3-flash-free subagent + parent DDG practitioner signal, 25+ sourced findings synthesized.
