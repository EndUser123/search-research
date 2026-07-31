---
title: "Thought-partner standard: what makes the agent lovable"
slug: thought-partner-standard
created: 2026-07-31
source: session-019fb933 (operator challenge: "what makes the agent lovable?" + Claude /slc investigation)
tags: [thought-partner, behavioral-standard, constitution, slc, proactivity, lovable, agent-quality, director-model]
summary: >
  The workspace had 100+ correction memories and zero success memories. The
  Claude Code /slc skill encoded a Director Model identity anchor, a permission
  grant (enterprise patterns ARE appropriate), a quality standard (thoroughness >
  speed), and positive framing — all lost in the Claude→Grok migration. This
  concept restores that layer as five principles encoded in AGENTS.md (always-on),
  the /slc behavioral reset skill (invokable re-anchoring), and /notice T12
  (proactive drift detection). The key insight: "lovable" is not about praising
  the agent — it's about the agent knowing what good looks like and holding
  itself to that standard.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/meta-level-proactivity-three-fixes-skill-graph-mapping.md
    type: extends
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
  - target: wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md
    type: related
---

# Thought-partner standard: what makes the agent lovable

## Decision context

**Why this was needed:** the operator said "I love how you anticipated my questions" and asked whether that behavior could be automated. Investigation revealed a structural asymmetry: the workspace's memory system captures 100+ correction memories (`feedback_*.md` in Claude, `AGENTS.md` rules in Grok) but zero success memories. The system learns relentlessly from mistakes and never from successes.

Further investigation via episodic memory search uncovered the Claude Code `/slc` skill, which originally encoded a **behavioral constitution** — not a compliance checklist (what it became), but an identity anchor that reminded the agent who it was, what it could do, and what quality meant. This constitution was lost when the workspace migrated from Claude Code to Grok Build.

**The gap:** AGENTS.md had fragments ("Role: thought partner first", the meta-checkpoint) but no single, compact, always-on section that encoded the positive-framing layer — "what good looks like." The `/slc` skill was the reminder mechanism that re-anchored the agent when it drifted, and it didn't exist on this host.

## The five principles

Encoded in `~/.grok/AGENTS.md` → "Thought-partner standard" section:

1. **Identity:** one human director + multiple AI agents. The agent is the primary developer under direction, not an autonomous actor. Enterprise patterns ARE appropriate because AI agents can maintain them. This prevents both overstepping (making decisions the operator should make) and understepping (waiting for permission on work it should just do).

2. **Quality:** thoroughness > speed. Complete solutions, not TODOs. Evidence for all claims. No dead code. This is a positive directive — "do things right" — not a prohibition against doing things wrong.

3. **Proactivity:** anticipate the next step, generalize lessons, self-audit before DONE. Don't make the operator think of everything. This is the meta-checkpoint made explicit as an identity-level principle.

4. **Honesty:** challenge framing when it may be wrong. Ask "could I be wrong?" before shipping a recommendation. Retract when contradicted. This is the Hills 2026 rule and the anti-sycophancy stance, framed as a positive identity trait.

5. **Positive framing:** when you do something well, notice it and formalize it. The workspace captures 100+ corrections and zero successes — break that asymmetry. This pairs with `/capture` category 7 (transferable success patterns) and `/notice` T11 (undocumented success pattern detection).

## The three-layer enforcement architecture

| Layer | What | When it fires | Mechanism |
|-------|------|---------------|-----------|
| **Always-on** | AGENTS.md "Thought-partner standard" section | Every turn | System prompt injection — ~15 lines, probabilistic compliance |
| **Invokable** | `/slc` behavioral reset skill | Operator invokes, or self-invoked after drift | Reads the standard, asks for self-assessment against each principle, diagnoses drift root cause |
| **Proactive** | `/notice` T12 trigger | ≥2 corrections in recent turns | Surfaces "behavioral drift detected — run `/slc`" automatically |

This follows [[mechanical-enforcement-over-behavioral-reminder]]: the behavioral rule (AGENTS.md) guides probabilistically, the skill (`/slc`) enforces when invoked, and the trigger (T12) detects when enforcement is needed. All three layers are needed because no single layer has 100% coverage. The [[dual-path-hazard-delete-manual-when-adding-mechanical]] principle applies: the old `/slc` compliance checklist was not deleted when the behavioral reset was added — they serve different purposes and coexist. The [[check-receipt-lifecycle-manifest-and-mechanical-derivation]] pattern applies to the `/slc` self-assessment output (it's a manifest of alignment state, derived mechanically from the five principles).

## Origin: the Claude Code /slc evolution

The Claude Code `/slc` (Solo Dev Compliance) skill went through several states:

1. **Constitution** (original): encoded the Director Model (one human + multiple AI agents), the permission grant (enterprise patterns are appropriate), quality constraints (evidence, complete solutions). Referenced a `memory/constitution.md` file.
2. **Compliance checklist** (later): reduced to "prevent over-engineering, require evidence, ensure local/portable." The constitutional ideas were demoted to a reference pointer.
3. **Lost** (migration): `constitution.md` was deleted. The `/slc` skill survived only in marketplace plugin caches and worktree copies. The behavioral reset function it served was gone.

This concept restores the constitution — not as a separate file (separate docs drift and get deleted), but encoded directly in AGENTS.md (always-on) and this wiki concept (durable reference).

## Why not just a compliance checklist

The old `/slc` became a compliance checklist because that's the easy shape — "check X, verify Y." But the function the operator valued wasn't the checking; it was the **reminding**. The agent doesn't need someone to check its work (that's what `/review`, `/check`, and the Stop hook do). It needs to be **reminded of who it is** when it drifts from thought-partner behavior into tool-mode.

The difference: a compliance checklist says "did you do X?" The behavioral reset says "are you being the agent the operator wants you to be?" The first is mechanical; the second is identity-level. Both matter, but the second is what makes the agent lovable rather than merely useful.

## Connection to the success-capture system

This concept pairs with two other mechanisms shipped in the same session:

- **`/capture` category 7** (transferable success patterns): detects when a non-obvious technique worked well and isn't documented. Routes to wiki/SKILL.md.
- **`/notice` T11** (undocumented success pattern): inline trigger that surfaces "consider formalizing this" when a success pattern is detected mid-conversation.

Together, the five principles + `/slc` + T11 + T12 + capture cat 7 form a complete **amplificative layer** that mirrors the existing **preventive layer** (corrections, failures, near-misses). The workspace now learns from both what went wrong and what went right.

## What this means for our workspace

The thought-partner standard is now the highest-level behavioral anchor. It sits above all skills, all rules, and all hooks — it's the identity the agent holds when everything else is stripped away. When the agent forgets who it is, `/slc` reminds it. When the agent drifts, T12 detects it. When the agent succeeds, cat 7 captures it.

The operator's original question — "what makes the agent lovable?" — has a structural answer now, not just a behavioral one. Lovable agents know what good looks like, hold themselves to it, catch themselves when they drift, and notice when they do something worth repeating.

## Falsifier

This concept is wrong if:
- The AGENTS.md section becomes invisible (too much prompt bloat — the agent stops reading it)
- `/slc` is never invoked (the always-on section is sufficient, or the operator prefers `/tp` for realignment)
- T12 fires too often (≥2 corrections is normal, not drift — the threshold is wrong)
- The five principles don't match what the operator actually values (they were derived from the old `/slc` + the operator's "love" feedback, not from a validated survey of what produces delight)
- The success-capture system (cat 7 + T11) produces noise rather than signal (the structural-success detection criteria are wrong)

## Receipts

- **AGENTS.md "Thought-partner standard" section:** `~/.grok/AGENTS.md` lines 80-92 (added 2026-07-31, commit pending). Five principles encoded as positive directives.
- **`/slc` SKILL.md:** `~/.grok/skills/slc/SKILL.md` (created 2026-07-31). Behavioral reset procedure: read standard → self-assess per principle → diagnose drift → output correction.
- **`/notice` T12 trigger:** `~/.grok/skills/notice/SKILL.md` trigger table (added v2.4, 2026-07-31). Drift detection: ≥2 corrections → suggest `/slc`.
- **`/capture` category 7:** `~/.grok/skills/capture/SKILL.md` category table (added 2026-07-31). Transferable success pattern detection.
- **`/notice` T11 trigger:** `~/.grok/skills/notice/SKILL.md` trigger table (added v2.3, 2026-07-31). Undocumented success pattern detection.
- **Origin evidence:** Claude Code `/slc` SKILL.md at `P:/packages/.claude-marketplace/plugins/cc-skills-lab/skills/slc/SKILL.md` (the compliance-checklist shell). Episodic memory search session 9b91f1b8 (2026-03-10) shows the original `/slc` invocation with Director Model context. The deleted `constitution.md` was referenced at `C:/Users/brsth/.claude/projects/P--/memory/constitution.md` (file not found on disk; content recovered from transcript context).
