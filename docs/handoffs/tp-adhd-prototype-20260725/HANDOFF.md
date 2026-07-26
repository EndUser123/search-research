# HANDOFF: /tp --adhd prototype (N-frame divergent ideation)

**Status:** ready-to-implement (deferred — after qmd track stabilizes)
**Created:** 2026-07-25
**Session:** 019f9bfe-1b89-7602-9384-0212224ff30b
**Priority:** MEDIUM (feature prototype, not blocking)
**Assignee:** fresh session (cold-start LLM)
**Parent handoff:** none
**Thread:** tp-adhd-prototype-20260725

---

## Objective (one sentence)

Prototype an `--adhd` mode for `/tp` that spawns N (default 3) deliberately-distorted-frame subagents instead of 1 fresh subagent, then clusters/prunes/deepens via the existing verification step — evaluating whether N-frame divergence produces options that single-frame critique misses.

## Why this session (not the current one)

The analysis is done (see `P:/.data/wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md`); the prototype is a separate workstream. Stacking it on the qmd track muddies signal — the operator's preference is to land qmd architecture first, then evaluate this with a clean baseline.

## Scope

### In scope
1. Add `--adhd` flag to `/tp` (`~/.grok/skills/tp/SKILL.md` + `protocol.md`)
2. Spawn N=3 fresh subagents with deliberately distorted frames (frame list below)
3. Add cluster/prune/deepen convergence to the verification synthesis step
4. Extract trap detection as a standalone critic question (fires regardless of `--adhd`)

### Out of scope
- Expanding to `/design`, `/red-team`, or `brainstorming` — evaluate after `/tp --adhd` proves ROI on 5+ real uses
- Creating a standalone `/adhd` skill — overlaps with `/tp`, would create parallel paths

---

## The design (from the wiki concept)

### N-frame distortion (the key innovation)

Current `/tp` spawns 1 fresh subagent with neutral framing ("critical friend"). `--adhd` spawns N=3 with deliberately distorted frames:

| Frame | Distortion | Why |
|---|---|---|
| **Adversarial** | "Argue the opposite of the leading recommendation. Assume it's wrong." | Surfaces the steelman of rejection |
| **Domain-shifted** | "Approach this from [adjacent domain] — what would a [SRE / product manager / security engineer] see?" | Cross-domain pattern transfer |
| **Frame-skeptical** | "Assume the user's framing is wrong. What question are they actually asking?" | Catches silent reframes |

Frame count is configurable (`--adhd N=5`); 3 is the default for cost/quality balance.

### Cluster/prune/deepen convergence (replaces naive "pick best")

After N frames return:
1. **Cluster** by similarity (which findings overlap across frames?)
2. **Prune traps** — findings that look right but are plausible narratives substituting for evidence (operationalizes `[[narrative-as-signal]]`)
3. **Deepen survivors** — for non-overlapping findings, drill with the existing verification step

This is the convergence discipline raw brainstorming lacks.

### Trap detection (extracted, fires regardless of `--adhd`)

After generating any critique, explicitly ask: "which of these findings is a plausible narrative substituting for evidence?" This captures ADHD's highest-value technique without the N-frame cost. Maps directly to `[[narrative-as-signal]]` and `[[reactive-pattern-matching-and-closure-pressure]]` — patterns we've documented behaviorally but not operationalized structurally.

---

## Evidence base

- **Source:** [UditAkhourii/adhd](https://github.com/UditAkhourii/adhd) (ingested at `P:/.data/wiki/sources/github.com/000-UditAkhourii-adhd.md`)
- **Analysis:** `P:/.data/wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md` — full integration analysis with ROI ranking
- **Existing workspace patterns** (observe before proposing):
  - `/tp` default: 1 fresh subagent, neutral framing
  - `/design` Step 5.5: 1 fresh subagent, critical-friend posture
  - `/red-team`: N specialists (failure-modes, security, logic, testing) — tests a proposal, doesn't generate options
  - `brainstorming`: decomposes problem (MECE), doesn't diverge on solutions

---

## Acceptance criteria

1. `/tp --adhd <question>` spawns 3 distorted-frame subagents and produces a clustered/pruned/deepened critique
2. `/tp <question>` (no flag) now includes the trap-detection critic question
3. The falsifier is tracked: after 5 real uses, does N-frame divergence produce options single-frame missed? If not, revert to single-frame and keep only trap detection.

---

## Constraints

- **Model pool:** use the existing `/tp` pool (`glm-5-2`, `nvidia-inkling`, `go-mimo-v2-5`, etc.). For N=3, prefer 3 different families if quota allows (genuine cross-family diversity).
- **Cost:** N=3 roughly triples `/tp`'s spawn cost. Default to N=3, allow `--adhd N=2` for cost-constrained cases.
- **Do NOT replace** existing `/tp` default. `--adhd` is opt-in.

## Files to read first

- `P:/.data/wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md` — the full analysis
- `P:/.data/wiki/sources/github.com/000-UditAkhourii-adhd.md` — the source README
- `~/.grok/skills/tp/SKILL.md` — current `/tp` implementation
- `~/.grok/skills/tp/protocol.md` — current subagent prompt template

## Falsifier

The wiki concept's falsifier (revisit after 5 uses):
- N-frame divergence never produces an option single-frame missed → revert to N=1
- Deliberately distorted frames produce worse critiques than neutral fresh-subagent → distortion adds noise
- Cluster/prune/deepen converges on the same answer as "pick best" → convergence discipline unnecessary

If any hold, keep only the trap-detection extraction.

## Prerequisite

Land the qmd architecture decision first (see handoff `qmd-viability-evaluation-20260725`). The wiki concept recommends evaluating `/tp --adhd` after the qmd track is stable to avoid stacking experiments.
