---
title: "Skill usability audit: cold-read critique to catch LLM-followability problems"
created: 2026-07-31
source: session-019fb177 (/tp cold-read of /ship skill caught 3 HIGH-severity issues)
tags: [skill-design, usability, cold-read, critique, transferable-technique, llm-behavior, quality-assurance]
summary: >
  Skills are instructions for LLMs, but their authors review them through the
  lens of already knowing the design intent — the same "cannot refocus your own
  glasses" problem that /tp exists to solve. A cold-read usability audit (spawn
  a fresh subagent with no shared framing, give it only the skill files, ask it
  to report what's confusing, ambiguous, or contradictory) catches problems the
  author can't see. This session's audit caught: dual-path confusion (manual
  instructions coexisting with a script), missing script path in the alias, and
  blocker output too thin to act on. Run this after any significant skill edit
  or new skill creation.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "Session 019fb177: /tp cold-read critique of /ship skill (explore subagent, 72s, 3 tool calls, 10 findings)"
relations:
  - target: wiki/concepts/dual-path-hazard-delete-manual-when-adding-mechanical.md
    type: produced
  - target: wiki/concepts/ship-receipt-mechanical-generation-from-per-check-results.md
    type: produced
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Skill usability audit: cold-read critique to catch LLM-followability problems

## Decision context

**Why this was needed:** after building `ship_receipt.py` and wiring it into `/go ship`'s Phase 3, the author (parent agent) reviewed the work and declared it done. The `/ship` run produced a clean SHIP DONE. But a fresh subagent reading the same skill files cold (no shared framing, no session context) found 10 usability problems — 3 of them HIGH severity. The author couldn't see these problems because it already knew the design intent: it knew the script was the primary path, it knew `--health-check` meant "no merge," it knew which `<LLM>` fields to fill. A cold-start LLM doesn't have any of that context.

This is the same structural problem that `/tp` exists to solve for proposals and decisions: **you cannot refocus your own glasses.** The fix is the same: spawn a fresh lens.

## The technique

### When to run

Run a cold-read usability audit after:
- **Any new skill creation** — the skill has never been tested by an LLM that didn't write it
- **Any significant edit to an existing skill** — especially when replacing manual steps with mechanical ones (see [[dual-path-hazard-delete-manual-when-adding-mechanical]])
- **Any skill where the operator reports confusion or friction** — the operator's confusion is downstream of the LLM's confusion; catching it at the skill level is cheaper than catching it at the session level

### How to run

1. **Spawn a fresh subagent** (`explore` type — read-only, no write capability, no shared framing). Do NOT pass `resume_from` — the whole point is a clean lens.
2. **Give it only the skill files** — the SKILL.md(s), any referenced scripts, the alias if one exists. Do NOT give it session context, design rationale, or prior decisions. The cold LLM should have exactly what a real invocation would provide.
3. **Ask specific usability questions** — not "is this good?" but structured dimensions:
   - Can you figure out what command to run?
   - If the script says FAIL, what do you do next?
   - Are there any sections where two different instruction sets cover the same task?
   - What's ambiguous about the `<LLM>` fields?
   - Is anything missing that you'd need to complete the task?
4. **Have the same agent verify** the findings against actual code — don't trust the critique blindly, but don't dismiss it either. The parent agent integrates.

### Label taxonomy for findings

Ask the subagent to label each finding:
- **[FRICTION]** — makes correct usage harder than it should be
- **[AMBIGUOUS]** — can be interpreted multiple ways
- **[MISSING]** — the skill should address this but doesn't
- **[CLEAN]** — works well (important to know what NOT to change)

## What this session's audit caught

| # | Finding | Severity | Would have caused |
|---|---------|----------|-------------------|
| 1 | Manual 12-item list coexists with script instructions | HIGH | LLM runs both paths → contradictory lint scope |
| 2 | Blocker output lacks test names / tracebacks | HIGH | LLM enters fix-loop blind, can't find failing test |
| 3 | Ship alias doesn't mention script or `<LLM>` fields | HIGH | Cold `/ship` skips the script entirely |
| 4 | `--since` placeholder contradicts auto-detect | MEDIUM | LLM wastes a turn computing merge-base manually |
| 5 | No "re-run after fix" recipe | MEDIUM | LLM doesn't re-verify after Phase 2 fixes |

All 5 were fixed in commit `85d87bd`. The author reviewed the skill before the audit and found none of them — because the author already knew the answers.

## Why the author can't see these problems

The author has three things the cold LLM doesn't:

1. **Design intent** — the author knows the script is the primary path and the 12-item list is historical. The cold LLM sees two equal-weight instruction blocks.
2. **Session context** — the author knows what `--health-check` means in this session (on main, auto-commit policy). The cold LLM reads the flag description literally.
3. **Goal anchoring** — the author is anchored on "ship this successfully." The cold LLM is anchored on "can I follow these instructions?" — a fundamentally different question.

This is why self-review of skills is structurally weaker than cold-read review, just as self-applied critique is structurally weaker than external critique (Costa & Kallick 1993, the origin of the "critical friend" concept).

## Steelman of the rejected alternative

**Rejected: add a validator that checks skill quality mechanically (line count, field presence, link density).**

**Why it was reasonable:** validators are already used for wiki entries (`validate_wiki_entry.py`) and close receipts (`validate_close_receipt.py`). A `validate_skill_usability.py` could check: script path exists, no duplicate instruction blocks, `<LLM>` fields documented, etc.

**Why it loses:** validators check structure, not semantics. The dual-path hazard (#1) is a semantic problem — both blocks are well-formed individually; the problem is their coexistence. A validator would need to understand "these two sections cover the same task" — that's LLM judgment, not regex. The cold-read audit is the right tool because the LLM is the consumer; the LLM should be the reviewer.

## Falsifier

This technique is wrong if:
- The cold-read subagent produces findings that are all low-severity or already-known — meaning the author's self-review was sufficient
- The findings are wrong (the subagent misreads the skill and reports false problems) — mitigated by having the parent verify
- The audit takes longer than the problems it catches — at 72s for this session's audit (3 tool calls, 1 subagent), the ROI is extremely high
- The skill is so simple that usability problems can't exist — true for trivial skills, but those don't need audits

## What this means for our workspace

Add cold-read usability audits to the skill lifecycle:
- After **`/create-skill`** or **`/create-skill-equivalent`** work — before declaring the skill done
- After **any significant skill edit** — especially adding/removing scripts, changing Phase structure, or replacing manual steps with mechanical ones
- The audit is cheap (one subagent, ~60-90s) and catches problems that would otherwise surface as operator friction, session corrections, or silent failures

This is a **transferable technique**, not a skill to build. Any session that edits a skill can run the audit inline: spawn `explore`, pass the skill files, ask the usability questions. No special tooling needed.

Related: [[mechanical-enforcement-over-behavioral-reminder]] — the parent principle. Skills that rely on behavioral instructions (the LLM remembering to do X) are weaker than mechanical enforcement. The usability audit catches when a skill's mechanical path is undermined by residual behavioral instructions.

## Receipts

- `/tp` critique output: subagent `019fb6a2-2230-7df2-b85d-ed774cbae710` (explore type, 72.7s, 3 tool calls, 10 findings)
- Fix commit: `85d87bd` (5 fixes applied: H1-H3 + M1-M2)
- Existing concept produced: [[dual-path-hazard-delete-manual-when-adding-mechanical]] (finding #1 → transferable pattern)
