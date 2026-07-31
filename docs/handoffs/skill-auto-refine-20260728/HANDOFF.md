---
thread_id: skill-auto-refine-improvements
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: console_019fa8f8
produced_at: 2026-07-28T17:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: fae5c2a
---

# Check that /why and other skills use /refine automatically for high-confidence improvements

## Objective (one sentence)

Audit the skill catalog to find skills that produce improvement findings
(`/why`, `/check`, `/review`, `/aar`, `/debrief`, `/skill-dev`) and add
auto-routing to `/refine` when the findings are high-confidence and
actionable — so the next session doesn't just document the problem but
prepares the fix.

## Producing context

This session (019fa8f8) ran the full SDLC pipeline on the model-benchmark
skill: `/tp` → implement → `/check` → `/review` → `/refactor` → `/close`.
At multiple points, skills produced findings that were high-confidence
and actionable but required manual routing to a fix:

- `/why` root cause analysis of the "symptom-anchored fix placement" error
  produced a clear root cause + a one-line layer-selection check. The finding
  was high-confidence, but there was no auto-route to `/refine` to tighten
  the finding into an implementation-ready task.
- `/review` found 17 findings, 3 critical. The criticals were fixed inline,
  but the medium findings (score_deep_reasoning fraction handling, passkey
  hallucination risk, etc.) would benefit from `/refine` packaging.
- `/check` found 3 integration bugs. Same pattern — fixed inline, but the
  pattern (missing context_window parsing) could be refined into a general
  "check new fields are wired" test.

The operator's observation: if a skill produces a high-confidence finding
with an obvious fix, it should auto-invoke `/refine` rather than just
listing the finding and waiting for manual routing.

## What to check

For each skill that produces findings or improvement recommendations:

1. **Does it have a "save step" or "feedback step" where findings are
   persisted?** (e.g., `/why` Step 15 wiki-save gate, `/review` FINDINGS.md,
   `/aar` opportunity landscape, `/check` issue list, `/skill-dev` mode 2)

2. **Does the save step currently route to `/refine`?** Or does it just
   write the finding and stop?

3. **What's the threshold for auto-routing vs. suggesting?** The
   `/go` skill already has a delegation-packet classifier (score ≥4 = auto,
   2-3 = hybrid, ≤1 = full). A similar confidence gate could work here:
   if the finding has a specific file:line, a clear fix, and high
   confidence → auto-refine. If ambiguous → suggest only.

## Skills to audit

| Skill | Produces findings? | Current auto-route? |
|------|-------------------|-------------------|
| `/why` | Yes — root cause + fix suggestion (Step 15 wiki gate) | No — writes to wiki, stops |
| `/review` | Yes — FINDINGS.md with severity + suggestion | No — writes artifact, stops |
| `/check` | Yes — verifier issues with severity + suggestion | No — reports issues, stops |
| `/aar` | Yes — opportunity landscape (OPP-N items) | No — writes report, stops |
| `/debrief` | Yes — lens findings + actionable items | No — writes summary, stops |
| `/skill-dev` | Yes — mode 2 "improve" proposes targeted improvements | No — proposes, stops |
| `/tp session` | Yes — NOW/NEXT/LATER/FILTER items | No — actionable list, stops |
| `/close` | Yes — gate findings + actionable insights | No — close summary, stops |

## Acceptance criteria

1. At least `/why`, `/review`, and `/check` have a "high-confidence auto-refine"
   step that packages actionable findings into `/refine` tasks
2. The confidence threshold is documented (what makes a finding "high-confidence")
3. The auto-refine is non-blocking — if `/refine` fails or the operator declines,
   the finding is still persisted to its normal artifact (wiki, FINDINGS.md, etc.)
4. The pattern is consistent across skills (same threshold, same routing mechanism)
5. Tests verify the auto-refine gate fires on high-confidence findings

## Constraints

- `/refine` does NOT write code. It tightens a task into implementation-ready
  form. So auto-refining a `/why` finding produces a refined handoff, not a fix.
- The auto-refine should NOT fire on every finding — only on findings that
  meet a confidence + actionability threshold. Low-confidence or ambiguous
  findings stay as listed items.
- Do not modify `/refine` itself — this is about adding routing FROM other
  skills TO `/refine`, not changing what `/refine` does.
- The `/go` skill already has an adaptive prompt enhancement step (Step B)
  that adds inferred acceptance criteria. The auto-refine pattern should
  complement this, not duplicate it.

## Read-first list

- `~/.grok/skills/why/SKILL.md` — Step 15 wiki-save gate (the "should this
  finding auto-route to a fix?" moment)
- `~/.grok/skills/refine/SKILL.md` — what `/refine` accepts as input
- `~/.grok/skills/go/SKILL.md` — Step B "adaptive prompt enhancement" (the
  existing pattern for auto-improving task prompts)
- `~/.grok/skills/review/SKILL.md` — FINDINGS.md format + severity levels
- `P:/.grok/skills/check/SKILL.md` — verifier issue format
- `~/.grok/skills/aar/SKILL.md` — opportunity landscape format
- `~/.grok/skills/close/SKILL.md` — gate resolution tier system (Tier 1 =
  auto-resolve, which is the same concept as auto-refine)

## Next steps (when this thread resumes)

1. Read `/refine` SKILL.md to understand its input contract
2. Read `/go` SKILL.md Step B for the existing auto-enhancement pattern
3. Design the confidence threshold (what makes a finding "high-confidence")
4. Implement the auto-refine step in `/why` first (highest signal)
5. Roll out to `/review`, `/check`, `/aar` if the pattern works

## Falsifier

This task is wrong if `/refine` is already auto-invoked by any of these
skills (check before designing). Or if the operator would prefer manual
routing for all findings (the auto-refine adds ceremony without value).
