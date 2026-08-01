---
title: "Behavioral reset improvements: Reflexion pattern + external critique step"
slug: behavioral-reset-pattern-reflexion-and-external-critique
created: 2026-07-31
source: session-019fb933 (/www research on improving /slc)
tags: [behavioral-reset, reflexion, self-correction, external-critique, slc, thought-partner, constitutional-ai, mcp, research-finding]
summary: >
  /www research identified two highest-leverage improvements for /slc-style
  behavioral resets: (1) persistent drift log (Reflexion pattern, Shinn et al.
  2023) — each reset writes drift findings to a searchable log that reveals
  recurring patterns over time; (2) external critique step — spawn a fresh
  subagent for the drift assessment instead of self-assessment, mirroring /tp's
  two-lens pattern. Validated across three independent repos (rohansx/reflect,
  Gulenoor-Khalid/Self-Governing-LLM-Agents, CognitiveThoughtEngine/
  constitutional-agent-governance) and the academic literature.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://github.com/rohansx/reflect (Rohan Sharma, 2026) — Reflexion MCP server
  - https://github.com/Gulenoor-Khalid/Self-Governing-LLM-Agents (2026) — Constitutional AI critique-and-revision chains
  - https://github.com/CognitiveThoughtEngine/constitutional-agent-governance (2026) — Epistemic Gate pattern
  - https://github.com/TsinghuaC3I/Awesome-Self-Improving-Agents (Tsinghua, 2026) — academic survey
relations:
  - target: wiki/concepts/thought-partner-standard.md
    type: extends
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: complements
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
  - target: wiki/concepts/structural-success-detection-over-lexical-praise.md
    type: related
---

# Behavioral reset improvements: Reflexion pattern + external critique step

## Decision context

**Why this research was needed:** the `/slc` behavioral reset skill (shipped this session) uses self-assessment — the agent reads the thought-partner standard and evaluates itself against each principle. But `/tp`'s core insight applies: *"You cannot refocus your own glasses"* (Costa & Kallick, 1993). A self-applied critique thinks harder through the same lens, which is structurally weaker than a critique from a different lens. The `/slc` self-assessment step may be the weakest link. This is the same principle documented in [[thought-partner-standard]] and [[mechanical-enforcement-over-behavioral-reminder]]: behavioral rules guide probabilistically, but structural enforcement (external lens, persistent log) catches what self-assessment misses.

The operator asked `/www` to research what ideas exist for improving `/slc`, whether repos do this, and what practitioners like.

## Key findings

### Finding 1: Persistent drift log (Reflexion pattern)

**Source:** [rohansx/reflect](https://github.com/rohansx/reflect) (Rust MCP server, implements Shinn et al. 2023)

The Reflexion paper's core insight: agent failures (and corrections) should be turned into **persistent, searchable lessons** that prevent the same mistakes across sessions. Applied to `/slc`: each reset writes `{timestamp, principles_drifted, root_cause, correction}` to `~/.grok/state/slc-drift-log.jsonl`. After N runs, patterns emerge: "this agent always drifts on Proactivity after 20+ turns" → weight that principle harder or surface it more aggressively.

The fork [ckorhonen/reflect](https://github.com/ckorhonen/reflect) articulates the friction-evaporation problem this solves: *"Every session produces two things: the work, and a trail of friction. The work ships. The friction evaporates, and you pay for it again tomorrow."*

**What people like:** persistent lessons that compound over time, not one-shot corrections that evaporate.

### Finding 2: External critique step (two-lens reset)

**Source:** [Gulenoor-Khalid/Self-Governing-LLM-Agents](https://github.com/Gulenoor-Khalid/Self-Governing-LLM-Agents) (Constitutional AI framework)

This framework enforces constitutional principles through **critique-and-revision chains** — a separate LLM call critiques the output, then the original revises. The key architectural decision: the critic is a different process from the actor.

Applied to `/slc`: when `/slc` runs, spawn a fresh `explore` subagent to do the drift assessment. The fresh agent sees drift the drifted agent can't — same two-lens pattern as `/tp`. The `/slc` invocation becomes: present standard → spawn external critic → integrate critique → output correction.

**What people like:** the agent catches its own blind spots through an external lens, not by thinking harder through the same lens.

### Finding 3: Targeted re-anchoring (Epistemic Gate)

**Source:** [CognitiveThoughtEngine/constitutional-agent-governance](https://github.com/CognitiveThoughtEngine/constitutional-agent-governance) (pip package)

The Epistemic Gate (EG) enforces reasoning quality **before execution**, and it targets specific failure modes rather than applying all rules uniformly. Applied to `/slc`: instead of always presenting all 5 principles, diagnose which principles are drifting and present only those. If the drift signal is "operator corrected framing 3×" → pull Honesty + Identity, skip Quality + Positive.

**What people like:** less ceremony, more signal. The reset feels targeted, not bureaucratic.

### Finding 4: Drift pattern mining (learned rules)

**Source:** [agentpatterns.ai/learned-review-rules](https://www.agentpatterns.ai/code-review/learned-review-rules/) + academic survey [TsinghuaC3I/Awesome-Self-Improving-Agents](https://github.com/TsinghuaC3I/Awesome-Self-Improving-Agents)

Code review agents that extract rules from accepted/rejected PR feedback and apply them to future reviews. Applied to `/slc`: after N runs, mine the drift log for patterns. "This agent's most common drift is Quality (shipping incomplete work)" → weight that principle more heavily in the AGENTS.md section. The constitution evolves based on observed drift.

**What people like:** the system gets smarter about the specific agent's weaknesses over time, rather than applying a static standard.

## What people don't like (from practitioner signal)

- **Full critique-and-revision chains are too heavy** for a reset skill (Self-Governing-LLM-Agents style). The external critique step alone is enough; the full revision loop adds latency without proportional value. **NOT built.** `/tp` and `/review` use fork-join (critique → integrate), not chains (critique → revise → re-critique). Do not claim this feature as wired — it was explicitly rejected by this research.
- **Autonomous self-modification degrades silently** (documented in `/notice` SKILL.md from the Self-Harness research). `/slc` must stay operator-invoked or T12-suggested, not auto-firing.
- **Pure metrics can't replace LLM judgment** — correction count and turn count are triggers, not assessments. The Reflexion pattern's persistent lessons are LLM-generated, not mechanically extracted.

## Practitioner sentiment items (mapped)

From the Reddit/HN signal pass — these were identified but require explicit mapping:

- **"Cohesion matters more than feature count"** (faros.ai review of Windsurf): honored as a meta-principle. The rejection of Feature 2 (full critique-revision chains) IS this principle in action — adding it would inflate feature count without serving cohesion.
- **"Template system for agent personalities"** (Reddit/Orban): **partially exists, explicitly deferred.** The SKILL.md `host: grok | claude | both` frontmatter field is a proto-template. Full personality composition (runtime injection of per-workspace personas, conditional activation) is out of scope for `/slc` — that's a workspace-architecture concern, not a behavioral-reset concern.
- **"Developers care about scaffolding, economics, and failure modes"** (Reddit AI agent mood): `/slc` IS scaffolding. The economics concern (token cost per reset) is addressed by the `--self-assess` fallback (cheaper than spawning a subagent). The failure-modes concern is the entire purpose of `/slc`.

## Feature coverage audit (2026-07-31, post-/tp critique)

A `/tp` critique identified that the original coverage claim was overconfident. Corrections:

| Feature | Original claim | Corrected status |
|---|---|---|
| Persistent failure lessons (reflect) | "wiki + /why Step 0.5 already exist" | **Partial.** /why Step 0.5 is consumer-only (reads wiki patterns). Producer is the drift log (Feature 7). Do not double-count. |
| Critique-revision chains | "/tp, /review already do this" | **Retracted.** Neither implements chains; research rejected them. /slc implements external-critique *half* only. |
| Epistemic Gate | "AGENTS.md receipts + /go H1" | **Partial.** These are probabilistic priming + post-hoc enforcement, not a tight pre-execution gate. |
| Workspace identity overrides | "NOT implemented" | **Already implemented** via AGENTS.md scope hierarchy (10+ scoped files with nested precedence). No additional mechanism needed. |
| Friction evaporation | "/capture + /notice T10" | **Partial.** Strongest functional match is `/friction` (dedicated skill for friction detection + automation scoring). /capture and /notice T10 are adjacent, not equivalent. |
| Persistent drift log | "/slc writes jsonl ✅" | **Spec-only.** File does not exist on disk — /slc has not been invoked live. Write path unverified. |
| Drift pattern mining | "/harvest reads drift log ✅" | **Spec-only.** Downstream of unverified drift log. |

**Live-verified:** Features 8 (external critique), 9 (targeted re-anchoring) — spec-correct in SKILL.md, pending live invocation.
**Spec-only (pending live verification):** Features 7, 5 — correct in SKILL.md text, unverified at runtime.
**Retracted:** Feature 2.
**Already existed:** Feature 6 (via AGENTS.md scope hierarchy).
**Partial:** Features 1, 3, 10, 4.

## What this means for our workspace

The four improvements, ranked by value-to-effort:

1. **External critique step** (highest value) — spawn fresh subagent for drift assessment. ~10 lines in SKILL.md. Mirrors `/tp` pattern.
2. **Persistent drift log** (high value) — JSONL append per `/slc` run. ~5 lines. Turns `/slc` from one-shot reset into learning system.
3. **Targeted re-anchoring** (medium value) — T12 passes which principles are implicated. Moderate effort.
4. **Drift pattern mining** (lower value, higher effort) — batch script that analyzes drift log. Deferred until drift log has N entries.

These are **identified improvements, not yet implemented**. The current `/slc` (self-assessment only) is functional but structurally weaker than it could be. The external critique step is the single highest-value change. The [[structural-success-detection-over-lexical-praise]] concept is a related design decision: both are about what the agent detects about itself and how it avoids self-deception. The [[self-improving-agent-systems-techniques-and-workspace-gaps]] survey covers the broader landscape of self-improvement patterns these improvements draw from.

## Falsifier

These improvements are wrong if:
- The self-assessment consistently catches real drift without needing an external lens (the `/tp` concern doesn't apply to `/slc` specifically)
- The persistent drift log produces noise rather than patterns (each session's drift is too context-specific to generalize)
- The external critique step adds latency without proportional quality gain (the fresh subagent doesn't see anything the original missed)
- Targeted re-anchoring reduces ceremony but misses cross-principle interactions (drift on Quality is actually caused by drift on Identity)

## Sources

- [rohansx/reflect](https://github.com/rohansx/reflect) (Rohan Sharma, 2026) — Reflexion MCP server, persistent failure lessons
- [Gulenoor-Khalid/Self-Governing-LLM-Agents](https://github.com/Gulenoor-Khalid/Self-Governing-LLM-Agents) (2026) — Constitutional AI critique-and-revision chains
- [CognitiveThoughtEngine/constitutional-agent-governance](https://github.com/CognitiveThoughtEngine/constitutional-agent-governance) (2026) — Epistemic Gate, targeted enforcement
- [TsinghuaC3I/Awesome-Self-Improving-Agents](https://github.com/TsinghuaC3I/Awesome-Self-Improving-Agents) (Tsinghua, 2026) — academic survey confirming Reflexion as state-of-the-art
- [agentpatterns.ai/learned-review-rules](https://www.agentpatterns.ai/code-review/learned-review-rules/) (2026) — learned rules from accepted/rejected feedback
- [ckorhonen/reflect](https://github.com/ckorhonen/reflect) (2026) — friction-evaporation framing

## Receipts

- **`/slc` current self-assessment:** `~/.grok/skills/slc/SKILL.md` Step 2 (created 2026-07-31, commit `9222360`) — the self-assessment procedure that the external critique step would replace
- **`/tp` two-lens pattern:** `~/.grok/skills/tp/SKILL.md` § "Core insight" — the "cannot refocus your own glasses" principle that motivates the external critique
- **`/notice` T12 trigger:** `~/.grok/skills/notice/SKILL.md` trigger table v2.4 (added 2026-07-31, commit `9222360`) — the drift detection that would feed the persistent drift log
- **AGENTS.md "Thought-partner standard":** `~/.grok/AGENTS.md` lines 80-92 (added 2026-07-31, commit `9222360`) — the five principles that `/slc` assesses against
