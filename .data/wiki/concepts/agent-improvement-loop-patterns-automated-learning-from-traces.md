---
title: "Agent improvement loop patterns: automated learning from traces, corrections, and failures"
created: 2026-08-05
source: session-019fa8f8 (/www research on automated improvement loops)
tags: [agent-improvement, self-evolving, reflexion, retroformer, trace-driven, automated-learning, pattern-catalog, external-research]
summary: >
  Three industry patterns for automated agent improvement from operational
  traces. All trigger on events (not schedules), connect detection to
  storage to improvement automatically, and treat agent traces as the
  primary evidence source. Our workspace has detection (/aar detectors)
  and storage (wiki/handoffs) but the connection between them is manual.
agent: grok
host: grok
cognitive_load: 2
verification: inferred
relations:
  - target: wiki/concepts/non-use-signals-deployment-failure-not-capability-failure.md
    type: related — the improvement loop must be automated to fire; manual invocation is the deployment failure
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: complement — enforcement should be mechanical; so should learning capture
  - target: wiki/concepts/claims-require-receipts-narrative-sufficiency-is-not-verification.md
    type: adjacent — agent improvement requires evidence from traces, not narrative
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends — that concept catalogued workspace gaps; this fills the research backing
---

# Agent improvement loop patterns

## Decision context

The operator asked: "how do we reliably capture durable lessons without relying on manual invocation?" The existing `/aar` skill has a detection engine (12 signal detectors in `detectors.py`) that finds corrections, errors, and friction patterns in transcripts. But the step between detection and capture (writing a wiki concept or AGENTS.md rule) is manual — the operator has to notice and ask.

Research question: what do practitioners do to automate this loop?

## The three patterns (research-backed)

### 1. Reflexion (Shinn et al., NeurIPS 2023)

**How it works:** Agent attempts a task → fails → generates a verbal self-reflection ("this failed because X") → stores the reflection in memory → next attempt uses stored reflections as context.

**Trigger:** task failure signal (wrong answer, exception, timeout).

**Key insight:** the reflection is a *semantic signal* — natural language describing what went wrong — not a score or gradient. It's stored verbatim and injected into the prompt on the next attempt.

**Our gap:** `/aar` detects failures mechanically but doesn't auto-store the lesson for the next session. The lesson lives in an AAR report that nobody reads until they explicitly look.

### 2. Retroformer (Yao et al., ICLR 2024)

**How it works:** A retrospective model runs alongside the main agent. When the main agent fails, the retrospective model generates feedback ("try a different approach because X"), which tunes the agent's prompt via policy gradient optimization.

**Trigger:** environment feedback (success/failure signal from the task environment).

**Key insight:** the retrospective model is separate from the actor — it observes the actor's trace and generates targeted improvement. The improvement is applied automatically, not requiring human review.

**For code/tool errors specifically:** Retroformer's approach is directly applicable — when a tool call fails (exit code != 0), the system can generate a structured reflection ("this command failed because the path doesn't exist" / "this Python import failed because the module isn't installed") and store it so the next session avoids the same error.

**Our gap:** we have the failure detection (`detect_tool_result_errors`) but no automatic reflection generation or prompt tuning. The agent re-derives the same lesson from scratch each session.

### 3. Agent Improvement Loop (LangChain/OpenAI, 2026)

**How it works:** A five-stage flywheel:
1. **Traces** — capture what happened (from staging, tests, production, local dev)
2. **Human feedback** — annotate traces with judgments ("this went wrong", "this was great")
3. **Evals** — automated checks that codify what the system should do
4. **Harness changes** — update prompts, instructions, code based on trace+feedback+eval evidence
5. **Flywheel** — each session contributes evidence toward the next improvement

**Trigger:** any trace from any source. The loop is always running, not triggered by a specific event.

**Key insight:** the loop connects traces to feedback to changes automatically. HALO (LangChain's tool) takes traces + feedback and produces *ranked* harness changes — prioritized improvements backed by evidence.

**Our gap:** we have traces (session transcripts) and feedback (operator corrections). We have the detection layer (`/aar` detectors). We even have the eval layer (wiki-worthy gate). But the connection — "take detected patterns, run the wiki-worthy gate, auto-capture passing patterns" — is manual.

## Common thread: event-triggered, not scheduled

All three patterns trigger on **events** (failures, corrections, traces), not schedules (time-based reviews). This is why `/dream` (scheduled/suggested) and manual `/aar` (operator-invoked) underperform — they're the wrong trigger model.

The right trigger for our workspace: **operator corrections detected in the transcript.** The `/aar` detector `detect_user_corrections` already finds these mechanically. The missing connection is: detected correction → three-layer decomposition → wiki-worthy gate → auto-capture.

## What we already have vs. what's missing

| Loop stage | What we have | Gap |
|---|---|---|
| Trace capture | Session transcripts, git history | ✅ |
| Signal detection | `/aar` detectors.py (12 detectors) | ✅ |
| Human feedback | Operator corrections in transcript | ✅ (detected by `detect_user_corrections`) |
| Reflection/extraction | `/tp` did it manually this session | ❌ Manual only — no auto-trigger |
| Evaluation | Wiki-worthy gate (6 checks) | ✅ |
| Capture | `/wiki` | ✅ |
| Application | AGENTS.md, SKILL.md, hooks | ✅ |

**The entire gap is the arrow between "detection" and "capture."** Everything else works. This is the structural fix: when `/aar` detects a correction, automatically run the decomposition + wiki-worthy gate and capture passing patterns.

## References

- Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," NeurIPS 2023. arxiv:2303.11366
- Yao et al., "Retroformer: Retrospective Large Language Agents with Policy Gradient Optimization," ICLR 2024. arxiv:2308.02151
- LangChain, "The Agent Improvement Loop Starts with a Trace," 2026. https://www.langchain.com/blog/traces-start-agent-improvement-loop
- OpenAI, "Build an Agent Improvement Loop with Traces, Evals, and Codex," 2026. https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- "A Survey of Self-Evolving Agents," arxiv:2507.21046, 2025

## Falsifier

This pattern set is wrong if:
- Our operators' corrections are too session-specific to generalize (most corrections produce no wiki-worthy lesson)
- The wiki-worthy gate has too high a bar (most corrections that are actually valuable don't pass all 6 checks)
- The detection→capture loop adds too much latency to `/aar` to be worth the value
