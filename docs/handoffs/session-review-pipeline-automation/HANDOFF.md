---
title: "Session-Review Pipeline Automation: close-check → recap → todo → tp"
current_session_id: 019fbf26-08f9-7f12-ace1-15ce7541c140
produced_at: 2026-08-01
status: OPEN — design needed
priority: MED
tags: [automation, session-review, close-check, recap, todo, tp, skill-composition]
---

# Session-Review Pipeline Automation

## The pattern

The operator manually ran 4 commands in sequence at session end:

1. `/close-check` — mechanical readiness sweep (git, harvest, wiki, hooks, lifecycle skills)
2. `/recap-grok` — narrative session recap (what happened, causation chains, meta-level)
3. `/todo` — prioritized action list (decide, at risk, in progress, ready)
4. `/tp do?` — reflective evaluation (what matters, what's missing, recommendations)

This composition is **the natural session-end review pipeline**. The operator
runs it every time, manually. Each skill feeds the next:
- close-check produces the mechanical evidence → recap synthesizes it narratively
- recap produces the story → todo extracts actionable items from it
- todo produces the priorities → tp evaluates what matters and what's missing

## The gap

No automation connects these. The operator manually invokes each skill, reads
its output, then manually invokes the next. This is the "manual skill composition"
pattern documented in `[[inter-skill-output-bridges-and-temporal-surfacing-layers]]`.

## Proposed automation

### Option A: close-check Phase 4.5 (recommended)

Add a Phase 4.5 to the `close-check.rhai` workflow that chains into recap+todo
after the remediation phase completes. The workflow already runs lifecycle skills
in Phase 3; Phase 4.5 would add the narrative+actionable layer.

```
Phase 1: Sweep (mechanical)
Phase 2: Synthesize (readiness verdict)
Phase 3: Remediate (lifecycle skills: capture, friction, handoff, trace, wiki)
Phase 4: Finalize (completion engine — already exists)
Phase 4.5: Review (recap-grok + todo + tp do?)  ← NEW
```

**Pro:** One command (`/close-check`) runs the full pipeline.
**Con:** Close-check becomes very long (already 20+ min); adding recap+todo+tp
could push it to 30+ min. May need to make Phase 4.5 optional.

### Option B: Wrapper skill `/review-session`

A new skill that orchestrates the 4-skill pipeline:
```
/review-session → close-check → recap-grok → todo → tp do?
```

**Pro:** Clean separation; close-check stays focused on mechanical readiness.
**Con:** New skill to maintain; one more command for the operator to remember.

### Option C: `/close-check --full` flag

Add a `--full` flag to close-check that includes the recap+todo+tp phases.
Default (no flag) stays as-is.

**Pro:** Backward-compatible; operator opts in.
**Con:** Flag discovery problem; the operator already runs all 4 manually.

## Recommendation

**Option A (Phase 4.5)** with a `--no-review` flag to skip it when speed matters.
The pipeline is already the operator's default session-end behavior — making it
automatic is the structural fix for the manual-composition pattern.

## Acceptance criteria

- [ ] `/close-check` produces recap-style narrative + todo-style action list + tp-style recommendations
- [ ] `--no-review` flag skips Phase 4.5 for fast mechanical-only runs
- [ ] Phase 4.5 output is appended to the same `pre-close-report.md` (single artifact)
- [ ] Total runtime stays under 30 min for typical sessions

## Cross-references

- [[inter-skill-output-bridges-and-temporal-surfacing-layers]] — the composition pattern
- [[command-wrapper-pattern-for-workflows]] — close-check already uses this pattern
- Session `019fbf26` — the session where this pipeline was manually demonstrated
