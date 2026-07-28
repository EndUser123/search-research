---
title: "Deferred and rejected skill improvements registry"
created: 2026-07-28
source: session-019fa94a (close-out)
tags: [skill-improvement, deferral-registry, skill-lifecycle, anti-re-litigation]
summary: >
  Fleet-wide registry of skill improvements that were proposed, evaluated, and
  either deferred (with re-evaluation trigger) or rejected (with rationale).
  Prevents re-litigation of settled decisions and surfaces deferrals when
  their trigger conditions fire. `/skill-dev improve <skill>` and `/tp` Step 0.5
  should query this concept before proposing new improvements.
agent: grok
host: grok
cognitive_load: 1
verification: observed
relations:
  - target: wiki/concepts/skill-development-portfolio.md
    type: complements
  - target: wiki/concepts/held-out-data-already-on-disk-count-artifacts-not-invocations.md
    type: related
  - target: wiki/concepts/spec-driven-development-tools-and-planning-workflows.md
    type: related
---

# Deferred and rejected skill improvements registry

## Decision context

**Why this exists:** skill improvements are proposed, evaluated, and either
applied, deferred, or rejected. Without a registry, deferred items get
re-proposed by future sessions that don't know the prior decision was made,
and rejected items get re-litigated. This registry is the fleet-wide memory
for those decisions — the skill-improvement equivalent of `tool-fallbacks.md`.

**How to use it:**
- **Before proposing a skill improvement**, query this concept (via `/tp`
  Step 0.5 wiki query or `/skill-dev improve`) to check whether the
  improvement was already evaluated.
- **After evaluating an improvement**, add an entry with the disposition,
  rationale, and (for deferrals) the re-evaluation trigger.
- **When a deferral's trigger fires**, re-evaluate and update the entry.

This registry complements [[skill-development-portfolio]] (which covers
*how* to evaluate improvements) and [[held-out-data-already-on-disk-count-artifacts-not-invocations]]
(which covers *where to find validation data*). The registry itself is the
"what was already decided" layer.

## Registry format

Each entry has:

| Field | Meaning |
|---|---|
| **Skill** | Which skill the improvement targets |
| **Improvement** | One-line description |
| **Disposition** | `DEFERRED` (has trigger) / `REJECTED` (rationale permanent) / `DROPPED` (redundant) |
| **Date** | When the decision was made |
| **Rationale** | Why it was deferred/rejected/dropped |
| **Trigger** | For DEFERRED: what observation would re-open evaluation. For REJECTED/DROPPED: "none" |
| **Source** | Session ID or handoff path where the decision was made |

## Entries

### plan-writer

| Skill | Improvement | Disposition | Date | Rationale | Trigger | Source |
|---|---|---|---|---|---|---|
| plan-writer | Problem-size gate (route trivial tasks before readiness gate) | DROPPED | 2026-07-28 | Redundant: skill already routes trivial tasks in 3 places (SKILL.md lines 32, 68, 123-130). A 4th mechanism is accretion. | none — unless evidence shows the 3 existing mechanisms are failing to route | session-019fa94a |
| plan-writer | Plan length budget (hard ≤400, soft ≤200 lines) | REJECTED | 2026-07-28 | Operator preference: "I really don't care about plan length, it should be as long as it needs to be. Using an arbitrary plan length looks like a footgun." Arbitrary thresholds become targets (Goodhart's law). 6 of 24 existing plans exceed 400 lines and were fine. | none — operator preference is durable | session-019fa94a |
| plan-writer | AGENTS.md consistency check (scan plan tasks for forbidden patterns) | DEFERRED | 2026-07-28 | Zero AGENTS.md violations across 24 plans on disk. Runtime hooks already enforce these rules at execution time. | Evidence of the failure mode: a plan-writer-generated plan proposing destructive git or AGENTS.md violations. If a code hook is needed later, ~30 lines scanning plan markdown for forbidden git patterns is the reliable implementation. | session-019fa94a |
| plan-writer | Traceability matrix (task → requirement → spec section) | DEFERRED | 2026-07-28 | Zero traceability markers in any plan. Plans ARE referenced by handoffs when future sessions need them (3 confirmed cases). The handoff→plan link serves the function. | Evidence of need: a future session that needed reverse traceability from code to spec and couldn't find it. The spec-anchored flag (disposable vs maintained) is cheap (2 checkbox lines) and can be added independently if desired. | session-019fa94a |
| plan-writer | Spec-anchored flag (disposable vs maintained plan lifecycle) | DEFERRED | 2026-07-28 | No evidence of need. Can be added independently of the traceability matrix. | Same trigger as traceability matrix — a future session needing to know whether a plan is disposable or maintained. | session-019fa94a |

## Maintenance

- **Append-only:** new entries are added, never removed. When a deferral is
  re-evaluated and applied, update the disposition to `APPLIED` with the date.
- **Re-evaluation cadence:** the `/skill-dev improve <skill>` workflow reads
  this registry as part of its Step 0.5 wiki query. If a deferral's trigger
  has fired, it surfaces for re-evaluation.
- **No re-litigation of REJECTED items** without new evidence that overturns
  the rationale. The rejection entry's rationale is the reference; a future
  session that disagrees must cite what changed.
- This follows the same fleet-wide tracking pattern as
  [[spec-driven-development-tools-and-planning-workflows]] § "What this means
  for our workspace" (resolution status per improvement).

## Falsifier

This registry would be wrong if: (a) deferred items never get re-evaluated
(the registry becomes a graveyard, not a tracking mechanism) — mitigated by
`/skill-dev` reading it at Step 0.5; (b) rejected items get re-litigated
anyway because the registry isn't checked — mitigated by `/tp` Step 0.5 wiki
query surfacing it during critiques; (c) the registry grows unbounded with
trivial entries — mitigated by the "significant effort to rediscover" filter
(nothing trivial goes in).

## Receipts

- **24-plan scan:** `python P:/tmp/plan_analysis.py` scanned all files in
  `P:/docs/superpowers/plans/`. Zero matches for destructive git, full-file
  write, or AGENTS.md violation patterns across all 24. Receipt: commit
  context in `80b3b93`.
- **3 existing routing mechanisms:** `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md`
  lines 32, 68, 123-130. Verified by grep and read_file.
- **Operator rejection of length budget:** session transcript, user message
  3: "I really don't care about plan length..."
- **Handoff→plan references:** 3 confirmed cases (exec-gate plan, yt-is
  migration plan, close-authority plan) — grep of `P:/docs/handoffs/` for
  `superpowers/plans/`.
