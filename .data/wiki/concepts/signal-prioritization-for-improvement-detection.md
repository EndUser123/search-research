# Signal Prioritization for Improvement Detection Skills

**Date:** 2026-08-07
**Session:** 019fd820
**Status:** ACTIVE — research findings for `/insight` signal-quality improvement
**Research method:** `/www` (DDG + web fetch, alert-fatigue + signal-triage domain)

## Context

The `/tp` critique of `/insight` improvement directions identified a blind
spot: all 6 proposed directions assumed the problem was signal *scarcity*
(finding more improvements). The real risk is signal *overflow* — the
skill's own falsifier lists "operator skips /insight because it's too slow
or noisy (over-firing)." Adding capabilities makes overflow worse.

This concept documents research from SRE alert-fatigue management and agent
notification intelligence — fields that have solved the signal-overflow
problem at scale — and translates the patterns to `/insight`.

## Sources

1. **incident.io — SRE alerting best practices** (2026-03): alert fatigue is
   systemic, not engineer failure. 2000+ alerts/week, only 3% need action.
   Key patterns: actionability gate, SLO-based alerting, alert-to-incident
   conversion rate tracking.
2. **Zylos Research — Agent Notification Intelligence** (2026-04): the field
   directly applicable to AI agent improvement-finding. Key thesis: treat
   notifications as a scarce resource. ML-driven priority scoring. Group
   before dispatch. Measure and adjust. 6 production patterns documented.

## The actionability gate (the most important pattern)

**Source:** incident.io, Zylos Pattern 1.

The most effective noise reduction is not filtering — it is architectural.
Design the skill so that non-actionable events are never surfaced as
interruptions. Log them, include them in digests — but don't surface them.

**The test:** "if the operator cannot take a specific action in response to
this finding, it should not be surfaced as a finding."

Applied to `/insight`:

| Finding type | Actionable? | Treatment |
|---|---|---|
| Operator correction with clear rule to add | YES | Surface as Tier-1 auto-capture |
| Friction pattern with known fix | YES | Surface with fix recommendation |
| "System gap" that's actually an architecture constraint | NO — no action possible | Log in digest, don't surface |
| Unverified assertion that's been superseded by later evidence | NO — already resolved | Suppress |
| Repeated manual step that's inherent to the workflow | NO — cannot be automated | Log, don't surface |
| Architectural decision that's already documented | NO — already captured | Suppress |

**Current state:** `/insight` surfaces all findings it finds. The actionability
gate is missing entirely.

## Signal-to-action conversion rate (the metric that matters)

**Source:** incident.io, Zylos Pattern 6.

SRE teams measure "alert-to-incident conversion rate" — what % of alerts
become investigated incidents. The target operating range is 30-50%. Below
20% = noise problem.

The `/insight` equivalent: **insight-to-action conversion rate** — what %
of surfaced findings get picked up by the operator (acted on, committed,
or routed to a handoff)?

**The `/tp` critique's blind-spot finding maps directly:** "before implementing
any direction, audit the task backlog and handoffs for items that originated
from `/insight` runs — count how many were created, how many were picked up.
If pickup rate is <30%, the bottleneck is signal-to-action, not signal-to-signal."

**Proposed measurement (low effort):**
```powershell
# Count findings routed to tasks/handoffs by /insight in the last 30 days
rg.exe -l "INSIGHT SCAN\|insight:" P:/docs/handoffs/ | Measure-Object
# Count how many of those handoffs are CLOSED (picked up and resolved)
rg.exe "status: CLOSED\|status: RESOLVED" <insight-routed-handoffs> | Measure-Object
# Conversion rate = resolved / total routed
```

If the conversion rate is low, the fix is NOT "find more findings" — it's
"surface fewer, higher-quality findings."

## Group before dispatch (correlation pattern)

**Source:** Zylos Pattern 3, Datadog intelligent correlation, Rootly AI
noise reduction.

Before surfacing any finding, check whether it's related to an existing
open finding or recent cluster. A single contextualized finding about a
complex pattern is far more actionable than 5 individual findings about
symptoms.

Rootly reports AI-powered clustering can cut alert volume by 70%.

**Applied to `/insight`:** when Step 2 finds 5 correction patterns that all
stem from the same root cause (e.g., the agent didn't read the wiki before
proposing — produces corrections in 5 different areas), group them into
one finding: "Wiki-not-queried-before-proposing pattern caused N corrections
across these areas."

**Current state:** `/insight` finds and surfaces each category independently.
No grouping step exists.

## Priority scoring (confidence × impact)

**Source:** Mandiant/Google Cloud, Unit21, Zylos Pattern 2.

Modern alert scoring separates **confidence** (how certain is the system
that this is genuinely a finding?) from **severity** (if it is real, what
is the potential impact?). Combine into a composite priority score.

**Applied to `/insight`:** each finding already has implicit confidence
(single-source vs multi-evidence) and impact (correction vs friction vs
informational). Make the scoring explicit:

```
finding_score = confidence × impact
  confidence: 1.0 (≥3 instances across sessions), 0.7 (2 instances), 0.4 (1 instance)
  impact: 2.0 (caused session failure), 1.5 (operator correction), 1.0 (friction), 0.5 (informational)
```

Findings below a threshold (e.g., score < 0.7) go to digest, not surface.

## Batching at breakpoints

**Source:** Microsoft Research CHI 2016, CMU human-centered interruption
management, Zylos Pattern 5.

Notification batching at natural task breakpoints improves cognitive
performance. Constant interruptions raise workload, decrease heart-rate
variability, and worsen task accuracy.

**Applied to `/insight`:** `/insight` already runs at session boundaries
(via `/close`) rather than mid-session. This is correct — session-end is
the natural breakpoint. The `/notice` skill handles mid-session surfacing
(T10/T11/T13 triggers). The division is sound: `/notice` for mid-session
nudges; `/insight` for end-of-session deep scan.

**No change needed here** — but document the rationale: `/insight` at
session-end is the batched-delivery pattern from notification science.

## What to implement (prioritized)

| Pattern | Effort | Impact on signal quality | Priority |
|---------|--------|--------------------------|----------|
| **Actionability gate** | LOW (add a Step 4.5 filter) | HIGH — removes non-actionable findings from surfaced output | **Do first** |
| **Group before dispatch** | MED (add clustering step) | HIGH — reduces N findings to 1 pattern | **Do second** |
| **Priority scoring** | MED (explicit score formula) | MED — makes threshold tuning possible | **Do third** |
| **Conversion-rate measurement** | LOW (grep audit) | MED — tells us if the problem is overflow or scarcity | **Do as measurement** |
| **Batching at breakpoints** | NONE (already implemented via /close timing) | — | Already done |

## Falsifier

These recommendations are wrong if:
- The actionability gate removes findings the operator would have wanted to see
  (false negatives from over-filtering) — calibration needed
- The conversion-rate measurement shows pickup rate is already >50% (meaning
  overflow isn't the problem after all) — would invalidate the overflow framing
- Grouping merges findings that needed separate treatment (false positive
  grouping) — loses signal instead of reducing noise

## Related

- `[[insight-skill-improvement-directions]]` — the original 6 directions (Directions 1+4 implemented, 2+5 dropped, 3 deferred)
- `[[proactive-improvement-opportunity-scanner]]` — the original /capture concept
- `[[self-improving-agent-systems-techniques-and-workspace-gaps]]` — workspace failure patterns
