---
title: "AI thought-partner landscape: OpenClaw/Hermes, multi-agent debate research, and /tp improvement directions"
created: 2026-07-24
source: session-2026-07-24 (/www research on thought-partner landscape)
sources:
  - https://arxiv.org/pdf/2502.08788 (Stop Overvaluing Multi-Agent Debate, Zhang et al 2025, 26 citations)
  - https://arxiv.org/html/2509.05396v1 (Understanding Failure Modes in Multi-Agent Debate, 2025)
  - https://arxiv.org/pdf/2505.22960 (Revisiting MAD as Test-Time Scaling, Yang et al 2025, 15 citations)
  - https://openreview.net/forum?id=NHxwxc3ql6 (COALITION: Second Opinions for Smaller LLMs, Patnaik et al, 3 citations)
  - https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide (Self-Improving AI Agents 2026)
  - https://www.turingpost.com/p/hermes (Hermes Agent vs OpenClaw comparison)
  - https://www.eurekalert.org/news-releases/1120832 (Sycophantic AI reinforcing harmful beliefs, 2026)
  - https://www.theatlantic.com/technology/archive/2025/08/ai-job-loss-human-enhancement-google/683963/ (Negative correlation AI use and critical thinking)
tags: [thought-partner, critical-friend, multi-agent-debate, openclaw, hermes, tp, improvement, sycophancy, mad, verification]
agent: grok
host: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  The AI thought-partner pattern (/tp) is NOT part of OpenClaw or Hermes —
  those are personal AI assistant/agent runtimes, not critique systems. The
  academic equivalent is Multi-Agent Debate (MAD), which has strong results
  but also documented failure modes (degenerate consensus, diminishing returns).
  Three improvement directions for /tp: (1) critique memory to avoid re-critiquing
  settled questions, (2) lightweight pre-critique triage to reduce fatigue, (3)
  outcome tracking to measure whether critiques actually improved decisions.
  The research validates /tp's existing design choices (cross-model diversity,
  verification gate, disconfirmation slot) while flagging alert fatigue as the
  primary risk.
relations:
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later
    type: extends
  - target: wiki/concepts/llm-council-and-model-fusion
    type: complement
  - target: wiki/concepts/llm-defensiveness-under-pushback-structural-fix
    type: related
---

# AI thought-partner landscape and /tp improvements

## Decision context

**Why this research was needed:** the operator asked whether the
thought-partner pattern (/tp) is part of known projects like OpenClaw or
Hermes, what the internet thinks about this topic, and how to improve /tp.

**What was explored:**
- Whether OpenClaw or Hermes contain thought-partner/critical-friend features
- The academic literature on Multi-Agent Debate (MAD) as the research analog
- Failure modes and limitations documented in the MAD literature
- Improvement directions from the self-improving agents and sycophancy research

**What the research changed:** validated /tp's core design (cross-model
diversity, verification gate) against academic evidence, identified three
concrete improvement directions, and confirmed that no existing personal
AI assistant framework has a built-in critical-friend mode.

## Is /tp part of OpenClaw, Hermes, or another project?

**No.** `/tp` is unique — no major personal AI assistant framework has a
built-in critical-friend/thought-partner mode.

| Project | What it is | Has critical-friend mode? |
|---------|-----------|--------------------------|
| **OpenClaw** | Self-hosted AI agent workforce (280K GitHub stars). Skills are human-written modular plugins: automation, communication, scheduling. [turingpost.com, o-mega.ai] | ❌ No critique/thought-partner skill in their 5,798-skill directory |
| **Hermes Agent** (Nous Research) | Autonomous agent runtime with persistent memory, self-improving skill loops (task → reflection → SKILL creation). [turingpost.com, hermes-agent.nousresearch.com] | ⚠️ Has "reflection" but it's self-reflection on task execution, not external critical-friend critique of the user's reasoning |
| **Claude Code** | Coding agent with skills, hooks, MCP. Has `/review` (code review) and brainstorming skills. | ❌ Code review ≠ thought-partner critique. No equivalent to /tp's premise/framing challenge |
| **ChatGPT** | Chat + agents. | ❌ Sycophancy-prone (documented below); no structured critical-friend mode |

**Key distinction:** OpenClaw and Hermes are *agent runtimes* — they execute
tasks, manage memory, and automate workflows. `/tp` is a *reasoning quality
gate* — it challenges the user's framing before commitment. These are
orthogonal capabilities. The operator's Grok Build setup is closer to a
personal AI assistant (with skills, hooks, memory, scheduling via monitor)
but with `/tp` adding the critical-friend layer that OpenClaw/Hermes lack.

## The academic equivalent: Multi-Agent Debate (MAD)

`/tp`'s two-lens architecture (fresh subagent + synthesis) is structurally
a lightweight Multi-Agent Debate system. The MAD literature is the closest
research analog.

### What the research validates in /tp's design

| /tp design choice | Research support | Source |
|---|---|---|
| **Cross-model diversity** (spawn pool uses different model families) | Same-model debate shows "degenerate consensus" — agents converge on the same wrong answer. Cross-model diversity is the fix. | Zhang et al 2025 (26 citations); Yang et al 2025 (15 citations) |
| **Verification gate** (Step 3: check subagent findings against evidence) | "MAD can sometimes degrade performance" — verification is more effective than pure debate at catching errors | arxiv 2509.05396 (Understanding Failure Modes in MAD) |
| **Single round, not iterative debate** | Iterative debate shows diminishing returns after 2 rounds; most value is in the first exchange | Yang et al 2025; Smit et al (123 citations) |
| **Disconfirmation slot** | Sycophancy is the #1 documented failure of AI advisory interactions. Explicit disconfirmation is the structural fix | Eurekalert 2026; Atlantic 2025 |

### What the research warns about (failure modes /tp should watch)

| Risk | Evidence | /tp's current defense | Gap |
|------|----------|----------------------|-----|
| **Degenerate consensus** — agents agree for the wrong reasons | Zhang et al 2025: "MAD methods often don't outperform single agents when you account for cost" | Cross-model spawn pool | ⚠️ If pool degrades to parent-only, the defense is gone |
| **Sycophancy reinforcement** — the critique validates the user's framing instead of challenging it | Eurekalert 2026: "AI chatbots that offer advice may quietly reinforce harmful beliefs" | Disconfirmation slot + self-rationalization check | ✅ Adequate |
| **Cognitive offloading** — user stops thinking critically because the AI "checked it" | Atlantic 2025: "negative correlation between frequent AI use and critical-thinking skills" | Step 3 requires user-facing synthesis with explicit reasoning | ⚠️ The synthesis might be read as "validated" without user engagement |
| **Alert fatigue** — too many critiques → operator ignores them | Industry pattern (alert fatigue in monitoring); Smit et al on diminishing returns | No mechanism currently | ❌ Gap — see improvement 2 below |
| **Self-improvement requires verifiable outcomes** — but /tp's outcomes are qualitative | o-mega.ai 2026: "Self-improvement only works reliably in domains where outcomes are objectively verifiable" | No outcome tracking | ❌ Gap — see improvement 3 below |

## Three improvement directions for /tp

### 1. Critique memory — avoid re-critiquing settled questions

**Problem:** `/tp` has no memory of what has already been critiqued. The same
framing question can be re-critiqued in a later session, producing the same
findings, wasting compute and operator attention.

**Research basis:** Hermes Agent's persistent memory and self-improving skill
loops (task → reflection → SKILL creation) demonstrate the value of durable
state across sessions. OpenClaw's cross-chat memory serves the same purpose.

**Proposed mechanism:** a lightweight log at `~/.grok/state/tp-critique-log.jsonl`
recording: date, target summary (1 sentence), verdict (PROCEED/REVISE/BLOCK),
key findings (bullet points), horizon. Before spawning a subagent, /tp checks
whether a similar target was critiqued recently. If yes (fuzzy match on target
summary), surface the prior critique and ask whether to re-critique.

**Cost:** ~50 lines of Python, one JSONL append per /tp run, one read per /tp run.
**Benefit:** prevents duplicate critiques, builds a searchable history of
"what framing questions have been examined."

### 2. Lightweight pre-critique triage — reduce alert fatigue

**Problem:** `/tp` runs full depth on every invocation regardless of whether
the framing question is novel or routine. The MAD literature shows diminishing
returns — not every question benefits from the full domain walk.

**Research basis:** Smit et al (123 citations): "we explore the trade-offs
between critical factors such as factual accuracy, time and cost." Not every
question warrants the cost.

**Proposed mechanism:** add a 10-second pre-critique check to Step 0.5:
- Has this question (or a near-identical one) been critiqued before? (checks critique memory)
- Is the decision reversible? (reversibility ≤1.25 → lighter critique)
- Is the framing novel or a repeat of a known pattern?
If all three say "low value for full critique," surface: "This looks like a
routine question we've covered before. Run full /tp anyway, or take the quick
answer?"

**Cost:** one JSONL read + one heuristic check. Zero added latency to full /tp.
**Benefit:** reduces alert fatigue; reserves full-depth critique for questions that benefit.

### 3. Outcome tracking — measure whether critiques actually helped

**Problem:** `/tp` has no feedback loop. The operator acts on (or ignores)
critique findings, and /tp never learns whether the critique was useful.

**Research basis:** o-mega.ai 2026: "Self-improvement only works reliably in
domains where outcomes are objectively verifiable." /tp's outcomes are
qualitative, but a simple "did you act on this?" signal is enough to calibrate.

**Proposed mechanism:** the critique log (improvement 1) includes an optional
`outcome` field the operator can fill in later: "acted on" / "ignored" /
"partially applied." Over time, /tp can surface patterns: "you've ignored 80%
of pre-mortem findings in the last 10 critiques — consider skipping that domain."

**Cost:** optional field; no enforcement. The operator fills it in when they want.
**Benefit:** creates a calibration signal; identifies which domains produce
actionable vs. ignorable findings.

## What NOT to change (research validates current design)

| Current design | Why it's right |
|---|---|
| Single-round critique (not iterative debate) | Yang et al 2025: diminishing returns after first exchange |
| Cross-model spawn pool | Zhang et al 2025: same-model debate → degenerate consensus |
| Verification gate (Step 3) | arxiv 2509.05396: verification > debate for error catching |
| No auto-trigger (explicit invocation only) | Alert fatigue risk; user controls depth |
| Disconfirmation slot | Sycophancy is the #1 documented failure of AI advisory |
| Session-state carve-out | Empirically grounded (188.7s incident) |

## Relationship to existing concepts

- **Extends** [[ai-thought-partner-industry-expectations-and-now-next-later]] — adds the project landscape (OpenClaw/Hermes comparison) and academic research (MAD literature)
- **Complements** [[llm-council-and-model-fusion]] — MoA/Fusion is the ensemble counterpart; /tp is the deliberative counterpart
- **Related** [[llm-defensiveness-under-pushback-structural-fix]] — sycophancy and defensiveness are opposite poles of the same axis

## Sources

- Zhang et al, "Stop Overvaluing Multi-Agent Debate" (arxiv 2502.08788, 2025, 26 citations)
- Yang et al, "Revisiting MAD as Test-Time Scaling" (arxiv 2505.22960, 2025, 15 citations)
- "Understanding Failure Modes in Multi-Agent Debate" (arxiv 2509.05396, 2025)
- Smit et al, "Should we be going MAD?" (ICML 2024, 123 citations)
- Patnaik et al, "COALITION: Second Opinions for Smaller LLMs" (OpenReview, 3 citations)
- o-mega.ai, "Self-Improving AI Agents: The 2026 Guide" (Mar 2026)
- turingpost.com, "Hermes Agent vs OpenClaw" (2026)
- Eurekalert, "Sycophantic AI reinforcing harmful beliefs" (Mar 2026)
- The Atlantic, "Negative correlation AI use and critical thinking" (Aug 2025)

## Staleness

The MAD literature is evolving rapidly (2024-2026 surge). Re-check for new
failure mode papers every 6 months. The OpenClaw/Hermes comparison is current
as of July 2026 but both projects are actively developing.

## Auto-related

- [[multi-agent-correlated-errors]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
