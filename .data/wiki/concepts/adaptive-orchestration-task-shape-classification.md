---
title: "Adaptive orchestration for AI agent skills: task-shape classification over ceremony defaults"
created: 2026-07-26
source: session-019f9d1f (/www research on /go intelligence + transcript analysis)
sources:
  - https://zylos.ai/research/2026-03-14-metacognition-ai-agent-self-monitoring-adaptive-control/ (Zylos, Mar 2026 — Nelson-Narens framework + MAPE-K + Reflexion/Self-Refine/Voyager)
  - https://arxiv.org/html/2604.12147v1 (Liu et al., Apr 2026 — "From Plan to Action: How Well Do Agents Follow the Plan?", 16,991 trajectories)
  - https://arxiv.org/html/2602.16873 (AdaptOrch, Feb 2026 — task-adaptive multi-agent orchestration)
  - https://tianpan.co/blog/2026-04-16-intent-classification-agent-routers (Tian Pan, Apr 2026 — intent classification cascade)
  - https://arxiv.org/html/2605.14186v1 (May 2026 — "LLMs Know When They Know" metacognitive harness)
  - P:/.data/wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md (existing)
  - P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md (existing)
  - P:/.data/wiki/concepts/intent-based-routing-for-ai-agent-skills-2026.md (existing)
  - P:/.data/wiki/concepts/grok-build-workflows-rhai-orchestration.md (existing)
  - P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md (existing)
tags: [adaptive-orchestration, task-shape-classification, ceremony-waste, metacognition, plan-compliance, delegation-packet, skill-design, code-orchestrates-model-judges]
agent: grok
host: grok
cognitive_load: 3
verification: transcript-data-validated
summary: >
  When an orchestrator skill (like /go) applies the same ceremony level to
  every task, it wastes tokens on well-specified prompts that don't need
  discovery, planning, or parallel phases. Transcript analysis of 1,074
  sessions showed 83% of /go invocations were delegation packets (prompts
  containing ≥4 of: acceptance criteria, file paths, verification commands,
  safety constraints, sequential dependencies). The fix is task-shape
  classification: score the prompt mechanically, strip ceremony for
  well-specified tasks, keep full ceremony for underspecified ones. The
  signal is bimodal and stable (not learned — classified). Cross-session
  learning was refuted by the data. The "From Plan to Action" paper (16,991
  trajectories) confirms that agents routinely ignore plan instructions,
  and that a bad plan is worse than no plan — validating the "strip
  ceremony on well-specified tasks" approach over "add more plan steps."
relations:
  - target: wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps
    type: extends — same principle (evidence-triggered conditional steps) applied to orchestration
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: applies — the classifier is the "code orchestrates" layer; pack selection is the "model judges" layer
  - target: wiki/concepts/intent-based-routing-for-ai-agent-skills-2026
    type: related — task-shape classification is a form of intent routing at the skill-internal level
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration
    type: complements — workflows handle macro-scale parallelism; task-shape classification handles per-invocation ceremony
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: applies — the 6-signal classifier implements Pattern 6 (receipt-first framing) mechanically
---

# Adaptive orchestration for AI agent skills: task-shape classification

## Decision context

**Problem:** the operator's `/go` orchestrator skill applies the same ceremony level (discovery, planning, parallel fan-out, verification) to every task. For well-specified prompts that already contain acceptance criteria, file paths, and verification commands, this ceremony wastes ~200 tokens of announcements and occasionally wastes entire phases (discovery that re-finds what the prompt already named).

**What the research changed:** the initial proposal was a three-layer system (mechanical classifier + LLM phase selection + cross-session learning ledger). Transcript analysis of 1,074 sessions refuted the learning ledger (signal is stable from session 1, bimodal, no drift to learn from) and the LLM phase selection (classifier routing is already obvious). The validated solution is the classifier alone.

**What alternatives were explored:**
- **Narrative self-reflection** ("let me consider whether ceremony adds value...") — rejected: inconsistent, adds token cost, produces no deterministic routing
- **Learning ledger** (cross-session outcome tracking) — refuted by transcript data: the signal is stable and bimodal; there's nothing to learn
- **LangGraph integration** — rejected for current use case: loses session integration, tool access, and TUI streaming; correct tool only when orchestrating across multiple model families
- **`--lite` flag** — data showed 0/66 invocations ever used it; the operator never opted out manually

## The evidence (transcript analysis, 1,074 sessions)

| Metric | Value |
|--------|-------|
| Transcripts scanned | 1,074 (910 Grok + 164 Claude) |
| Sessions with `/go` | 21 |
| Total `/go` invocations | 66 |
| Task shapes scored "execution" (score ≥4) | 55/66 (**83%**) |
| Task shapes scored "full" (score ≤1) | 10/66 (15%) |
| `--lite` flags used | **0** |
| `--skip-*` flags used | **0** |
| Pushback correlated with execution-mode | **100%** (all identifiable pushback came from sessions with score ≥4) |

The distribution is **bimodal**: 83% at score 5-6, 15% at score 0-1, almost nothing in between. There is no ambiguous middle ground where adaptive learning would help.

## The classifier (6 signals, mechanical, zero LLM cost)

| Signal | Detection heuristic |
|--------|-------------------|
| A. Acceptance criteria | Numbered list with "prove", "verify that", "required result", or explicit pass/fail |
| B. Explicit file paths | `path/to/file.py` pattern (not inside code blocks) |
| C. Verification commands | `python ...`, `pytest`, `git log/diff/status/commit` as instructions |
| D. Stop conditions | "Stop only for", "Stop when", "do not stop because" |
| E. Safety constraints | "Never:", "Do not:", "Forbidden:" with enumerated rules |
| F. Sequential dependencies | Explicit ordered steps or phase numbering |

```
score ≥ 4  →  DELEGATION_PACKET: strip ceremony (H2/H3/H4 off)
score 2-3  →  HYBRID: keep H1 + H6, skip H2/H3/H4
score ≤ 1  →  FULL: standard ceremony (default)
```

**Anti-over-firing guard:** shared-infrastructure tasks (hooks, settings.json, dispatch chains) keep H3 (discovery) ON regardless of score.

## What the web research adds (theory backing)

### "From Plan to Action" (Liu et al., Apr 2026, 16,991 trajectories)

The single most relevant finding: **agents routinely ignore plan instructions, and a bad plan is worse than no plan.** Key results:

1. **Standard plan compliance varies across models** (Finding 1) — some follow strictly, others adaptively skip steps based on difficulty
2. **A subpar plan hurts performance even more than no plan at all** (Finding 8) — validates ceremony-stripping for well-specified tasks
3. **Periodic plan reminders reduce violations and improve performance** (Finding 12) — suggests lighter ceremony repeated is better than heavy ceremony once
4. **Augmenting plans with phases that don't align with the model's internal strategy degrades performance** (Finding 10) — this is the failure mode of adding H3 Discover to a prompt that already named the files

**Implication for `/go`:** the classifier doesn't just save tokens — it prevents the "bad plan" failure mode. When `/go` adds discovery to a delegation packet, it's augmenting the plan with a phase the model's internal strategy doesn't need, which the research shows actively degrades performance.

### Metacognitive monitoring (Zylos, Mar 2026; Nelson & Narens 1990)

The Nelson-Narens framework distinguishes **monitoring** (meta-level reads from object-level) from **control** (meta-level writes to object-level). For `/go`:

- **Monitoring**: the 6-signal classifier reads the prompt's shape (meta-level observation)
- **Control**: the routing decision strips or keeps ceremony packs (meta-level directive to the execution layer)

The key insight from Self-Refine's **correlated failure problem** (§2.2): when the same model is both actor and critic, they share biases. For `/go`, this means: if the LLM decides which ceremony to apply (narrative self-reflection), it inherits the same biases that produced the ceremony in the first place. A mechanical classifier avoids this — the routing decision is deterministic, not subject to the model's tendency to over-apply its own ceremony.

### Adaptive expertise (Hatano & Inagaki 1986; Gamborg 2023)

The wiki's existing [[adaptive-expansion-evidence-triggered-conditional-steps]] concept documents this for diagnostic skills: run a fixed lightweight core, then let conditional steps fire inline based on evidence. The same principle applies to orchestration: run a fixed lightweight core (H0 safe-git + H1 think + H6 verify), then let ceremony phases (H2 plan, H3 discover, H4 parallel) fire only when evidence warrants.

## What was NOT implemented (and why the data refuted it)

| Proposed layer | Why rejected | Evidence |
|---|---|---|
| Cross-session learning ledger | Signal is stable from session 1, bimodal | 1,074 transcripts: 83% score ≥4 across 21 sessions over weeks |
| LLM phase-selection step | Classifier routing is already obvious | Bimodal distribution; no ambiguous middle ground |
| LangGraph integration | Loses session integration, tool access, TUI | Current use case is single-session, single-model |
| Narrative self-reflection | Inconsistent, adds cost, produces no deterministic routing | "From Plan to Action" shows LLMs unreliable at knowing which steps they'll need |

## Falsifier

This approach is wrong if, within 6 months:

- The classifier causes `/go` to skip discovery on a task that needed it (false positive on delegation packet)
- The 6-signal heuristics produce inconsistent scores across different prompt styles (regex ambiguity)
- The bimodal distribution shifts to trimodal (ambiguous middle emerges) — this would justify the learning ledger
- Operators of OTHER skill orchestrators (not `/go`) find the 6 signals don't generalize to their task mix

## Honest trade-offs

**What people would like:**
- Zero ceremony on well-specified tasks (the classifier delivers this)
- Data-validated, not opinion-based (1,074 transcripts)
- Simple (30 lines in SKILL.md, no new runtime)

**What people would dislike:**
- Regex-based heuristics can false-positive (e.g., a prompt that mentions file paths in code examples but doesn't actually specify the task's target files)
- SKILL.md instructions are advisory (the LLM may ignore the classifier's routing — the "From Plan to Action" paper's Finding 1)
- No learning means no adaptation to future task-mix shifts (if the operator's tasks evolve, the threshold may need manual adjustment)
