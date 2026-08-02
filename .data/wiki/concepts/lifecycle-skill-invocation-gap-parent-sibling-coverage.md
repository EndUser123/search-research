---
title: "Lifecycle skill invocation gap pattern — parent-sibling mechanical sweep coverage"
created: 2026-08-02
source: session-019fa111-5dcb-7ff1-a4f5-415ad29bbe9e
tags: [lifecycle-skills, close-check, parent-orchestration, mechanical-sweep, coverage-gap, session-architecture]
summary: >
  When parent sessions invoke /wiki (or other lifecycle skills as sub-agents) but
  fail to independently invoke /harvest, /friction, /trace at the right point,
  the close-check mechanical sweep sibling sub-agent covers for the gap. This is
  a recurring pattern observed in session 019fa111 (2026-08-01/02) where all
  three lifecycle skills were flagged as "not invoked by parent — covered by
  mechanical-sweep sibling sub-agent." The pattern is non-obvious: most sessions
  don't realize the safety net exists, and the fallback masks parent
  orchestration discipline gaps rather than surfacing them.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
tier: warm
relations:
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: extends
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related
  - target: wiki/concepts/close-check-invokes-capture.md
    type: related
  - target: wiki/concepts/accumulation-problem-resolution-rate-binding-constraint.md
    type: related
---

# Lifecycle skill invocation gap pattern — parent-sibling mechanical sweep coverage

## Decision context

**Why this finding was captured:** session 019fa111 (2026-08-01/02) was a `/wiki` invocation that produced pre-packed evidence including a `lifecycle-skill-coverage` warning set with 3 specific findings. The pattern was distinct enough from existing concepts (it is not the same as `close-check-invokes-capture` which is about /close-check invoking /capture; it is not the same as `lifecycle-skill-remediation-modes` which classifies skills by output handling) to warrant its own concept.

**The specific observation:** the sweep emitted three WARN-level findings in a row:

```
[warn] lifecycle-skill-coverage: [SESSION] gap: /harvest not invoked by parent — covered by mechanical-sweep sibling sub-agent
[warn] lifecycle-skill-coverage: [SESSION] gap: /friction not invoked by parent — covered by mechanical-sweep sibling sub-agent
[warn] lifecycle-skill-coverage: [SESSION] gap: /trace not invoked by parent — covered by wiki-fmea sibling sub-agent (free-tier B nim-openai-gpt-oss-20b)
```

All three lifecycle skills (per `lifecycle-skill-remediation-modes-auto-act-vs-surface-only`) that produce durable or surfacing output were not invoked by the parent session — but each was covered by a sibling sub-agent.

## The pattern

**Parent invocation gap:** when a parent session invokes `/wiki` (or `/handoff`, `/capture`, etc.) as a sub-agent, the parent may not invoke the full lifecycle skill set at the right time. The parent is responsible for triggering `/harvest`, `/friction`, `/trace` — but in practice these are often skipped when the parent's primary task is a single output (e.g., "distill this transcript into wiki concepts").

**Sibling coverage as safety net:** the close-check workflow's mechanical sweep includes sub-agents that cover for these gaps. Specifically:
- `/harvest` not invoked → mechanical-sweep sibling invokes it
- `/friction` not invoked → mechanical-sweep sibling invokes it
- `/trace` not invoked → `wiki-fmea` sibling (free-tier B, `nim-openai-gpt-oss-20b`) invokes it

The coverage works because close-check Phase 3 runs these skills as part of its pipeline regardless of whether the parent invoked them. The safety net is structural, not behavioral.

**Why this is non-obvious:** most sessions treat lifecycle skill invocation as a discipline question ("did the parent remember to call /friction?"). They don't realize that the close-check Phase 3 pipeline provides automatic coverage. The fallback masks parent orchestration gaps rather than surfacing them as failures.

## What this means for our workspace

### For parent sessions

The pattern is a **soft signal, not a failure**. When a session sees the `lifecycle-skill-coverage` WARN finding, it does NOT mean the lifecycle skills were skipped — it means the parent didn't invoke them directly, but the sweep sibling covered. The session can still produce valid output.

However, the pattern does suggest a discipline improvement opportunity: parent sessions should explicitly invoke /harvest, /friction, /trace at the appropriate points in their workflow, rather than relying on close-check to cover for them. The reasons:

1. **Coverage timing differs.** Close-check runs at session end, but /friction and /trace findings are most actionable when surfaced mid-session (so the parent can act on them). Mechanical-sweep sibling coverage produces findings too late for in-session action.
2. **Coverage tier differs.** The wiki-fmea sibling uses `nim-openai-gpt-oss-20b` (free-tier B), which may produce lower-quality /trace output than the parent's primary model. Quality trade-off is silent.
3. **Coverage attribution is lost.** When the parent didn't invoke, the session loses the opportunity to attach its own context, decisions, and constraints to the lifecycle skill output. The sibling runs with generic context.

### For orchestrator design

This is a structural pattern that applies beyond close-check. Any orchestrator that runs lifecycle skills as part of its pipeline provides implicit coverage for parent invocation gaps. The design choice:

- **Coverage as safety net (current):** orchestrator covers for gaps; WARN findings surface the gap; parent can improve over time
- **Strict invocation requirement (alternative):** orchestrator fails if parent didn't invoke; harder discipline, fewer mid-session findings
- **Hybrid (recommended):** orchestrator covers but logs the gap explicitly (as `lifecycle-skill-coverage` does); the WARN level + naming the specific skill + naming the covering sibling gives the parent enough signal to improve without blocking the workflow

The hybrid is what we have. This concept documents it so future orchestrator design doesn't accidentally regress to "strict requirement" (which would surface the gaps as failures) or "silent coverage" (which would hide them entirely).

### Detection signals

Other orchestrators can detect this pattern with the same shape:
1. Parent invocation record (did the parent call the skill?)
2. Sibling coverage record (did the orchestrator's sub-agent cover for it?)
3. WARN-level finding emitted (logged, not blocked)

If all three exist for the same skill in the same session, this pattern fired.

## Falsifier

This concept is wrong or obsolete if:

- **Close-check Phase 3 stops running /harvest, /friction, /trace** — the safety net disappears; parent invocation becomes mandatory. If this happens, the pattern becomes a hard failure, not a soft signal.
- **Parent invocation becomes enforced by orchestrator contract** — the gap becomes structurally impossible. The pattern is moot.
- **Sibling coverage is removed in favor of parent-only invocation** — the pattern no longer exists; coverage gaps become hard failures. Future sessions would need different guidance.

If none of these fire, the pattern is durable: parent sessions will continue to occasionally miss lifecycle skill invocations, and the orchestrator's sibling coverage will continue to fill the gap. The signal is worth keeping.

## Receipts

- Session 019fa111 lifecycle-skill-coverage raw evidence: `transcript signals.json` lines referencing the three WARN findings; transcript segments where `/tp`, `/go`, `/wiki`, `/handoff`, `/close-check` were invoked but `/harvest`, `/friction`, `/trace` were not
- `~/.grok/workflows/close-check.rhai` Phase 3 (Remediate) — the structural source of sibling coverage
- `wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md` — the lifecycle skill classification that defines which skills are auto-act vs surface-only
- `wiki/concepts/close-check-invokes-capture.md` — the related (but distinct) finding about /close-check needing to invoke /capture (RESOLVED 2026-08-01)