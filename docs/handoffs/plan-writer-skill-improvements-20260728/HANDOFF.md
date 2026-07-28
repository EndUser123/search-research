---
thread_id: plan-writer-skill-improvements-20260728
parent_handoff_path: none
current_session_id: 019fa5a1-0446-7e02-9766-bd2457ee58c3
current_terminal_id: grok-build-primary
produced_at: 2026-07-28T07:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Handoff — plan-writer skill improvements (4 remaining from /www research)

## Objective

Run `/skill-dev improve plan-writer` to apply 4 remaining improvements identified by the `/www` field survey of spec-driven development tools. Two improvements (decomposition checkpoint + mandatory review loop) were already applied directly in session 019fa5a1 because the evidence was this session's own failure. The remaining 4 need held-out validation per `/skill-dev` Mode 2 Step 4.

## Why this exists

Session 019fa5a1 produced a close-authority plan that went through 4 revision rounds (47 total findings), growing to ~900 lines with 4 workstreams. The operator challenged: "do you really feel it is much better?" The answer was no — attestation was over-engineering. The `/www` research surveyed external SDD tools (GitHub Spec Kit, AWS Kiro, Tessl) and practitioner workflows (Addy Osmani, Birgitta Böckeler/Thoughtworks) to identify what others do well that we're missing. The wiki concept `spec-driven-development-tools-and-planning-workflows.md` documents the full survey.

## Already applied (2 of 6) — no action needed

| Improvement | Commit | What it does |
|---|---|---|
| Decomposition checkpoint | `9ce0bff` | Between file structure and task structure, asks: necessary? mergeable? droppable? simpler? Prevents over-engineering before writing tasks |
| Mandatory review loop | `1266bad` + `705e9b2` | For hard plans (reversibility ≥1.5), spawns a fresh `general-purpose` subagent with adversarial review prompt. Loops until 0 critical/high findings |

## Remaining improvements (4) — for `/skill-dev improve` to apply

### Improvement 3: Problem-size gate

**Source:** Böckeler (Thoughtworks) — found Kiro and Spec Kit were "a sledgehammer to crack a nut" for small problems.

**Failure mode:** plan-writer applies the full readiness gate + completeness checks + review loop even to trivially small tasks that don't need a plan.

**Proposed change:** add a check BEFORE the readiness gate:
```
## Problem-size check (before readiness gate)

Is this problem big enough for a plan?
- Single-file fix, <20 lines changed → just do it, no plan
- One config change → just do it
- 2-3 files, clear path → soft plan (--lite), skip review loop
- Multi-file, architectural, or unclear → full plan

If the problem is too small for a plan, say so and route to /go or "just do it."
```

**Held-out validation:** check sessions where plan-writer was used for small problems. Would the problem-size gate have saved time without losing quality?

### Improvement 4: Plan length budget

**Source:** Böckeler — "I'd rather review code than all these markdown files." Spec Kit creates 8+ files per spec.

**Failure mode:** plans grow unboundedly (v1-v4 was ~900 lines). The review loop finds bugs but doesn't flag verbosity.

**Proposed change:** after self-review, check plan line count:
```
## Plan length check (after self-review)

- Hard plans: target ≤400 lines. If >500, the decomposition checkpoint fires again — something can be dropped.
- Soft plans: target ≤200 lines. If >300, simplify.
- If the plan exceeds the budget, the review loop prompt adds: "This plan is [N] lines. Can any workstream be dropped or simplified?"
```

**Held-out validation:** check sessions where the plan was good and ≤300 lines. Would the budget have helped or added ceremony?

### Improvement 5: AGENTS.md consistency check

**Source:** Spec Kit's "constitution" — immutable principles checked at every phase.

**Failure mode:** plan tasks can violate AGENTS.md rules (e.g., proposing destructive git, skipping edit-then-verify) without the plan-writer catching it.

**Proposed change:** extend completeness check #6 (internal consistency) to also check:
```
**6b. AGENTS.md consistency.** Read each task and verify it doesn't violate:
- Destructive git rules (no reset --hard, force-push, clean -fd)
- Edit-then-verify protocol
- No deferred persistence rule
- File editing protocol (no full-file write on existing files)
- Auto-commit standing policy (commit after logical unit)
If any task violates, flag it.
```

**Held-out validation:** check sessions where plan tasks violated AGENTS.md. Would this check have caught it?

### Improvement 6: Traceability matrix + spec-anchored flag

**Source:** Spec Kit (tasks trace back to requirement numbers), Tessl (spec-as-source with `// GENERATED FROM SPEC`).

**Failure mode:** once code is written, the plan is dead weight — no reverse traceability to understand why code exists.

**Proposed change:** add to the plan template:
```
## Traceability Matrix (Appendix — mandatory for hard plans)

| Task | Implements requirement | Spec section |
|------|----------------------|--------------|

## Spec lifecycle

- [ ] This plan is **spec-first** (disposable after implementation — the code becomes truth)
- [ ] This plan is **spec-anchored** (maintain alongside the code — update when code changes)

Default: spec-first. Promote to spec-anchored only for architectural decisions that future sessions will re-litigate.
```

**Held-out validation:** check sessions where a future session needed to understand why code was written a certain way. Would the traceability matrix have helped?

## Read-first list

1. This handoff
2. `P:/.data/wiki/concepts/spec-driven-development-tools-and-planning-workflows.md` — the full field survey with sources
3. `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md` — the current skill (with decomposition checkpoint + review loop already applied)
4. `C:/Users/brsth/.grok/skills/skill-dev/SKILL.md` — the skill to run (Mode 2: improve)
5. `P:/docs/handoffs/session-observations-019fa5a1-20260727/HANDOFF.md` — session evidence (over-engineering pattern, Verschlimmbesserung)
6. `P:/docs/superpowers/plans/2026-07-28-close-authority-completion.md` — the plan that went v1→v5 (the case study)

## Suggested next

```bash
/skill-dev improve plan-writer
```

Use Mode 2 with:
- **Training sessions** (motivated the improvements): session 019fa5a1 (over-engineering), the wiki concept's 6 improvements
- **Held-out sessions** (where plan-writer worked): check prior plan-writer invocations in `P:/docs/superpowers/plans/` — find sessions where the plan was good and ≤300 lines
- Apply each improvement with held-out validation per Mode 2 Step 4

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing — improvements are additive
- **Non-blocking to:** all other workstreams

## Falsifier

This handoff would be wrong if the 4 improvements don't survive held-out validation (they regress on sessions where plan-writer worked well). That's exactly what `/skill-dev` Mode 2 is designed to check.

## Last user message (verbatim)

> "ok, create the handoff"

## Epistemic labels

- [FACT] 2 of 6 improvements already shipped (commits `9ce0bff`, `1266bad`, `705e9b2`)
- [FACT] 4 improvements identified from 5 independent external sources (wiki concept with citations)
- [INFERENCE] the 4 remaining improvements need held-out validation — they're grounded in external practice but not yet validated against our specific context
