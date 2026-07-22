# Goal: Continuously reduce user-initiated meta-actions

**Established:** 2026-07-20
**Status:** Active (standing goal, no end date)
**Owner:** system (all skills, all sessions)

---

## Objective

Continuously reduce user-initiated meta-actions by converting them into system defaults, auto-triggers, or durable artifacts.

## Why

The user should not have to remember to do things the system can do itself. Every time the user corrects, reminds, or manually triggers something, that's a signal that the system failed to do something it should have. Each instance should become a system improvement, not a one-off correction.

## Success criteria

Over time, the user invokes fewer explicit reminders, corrections, and manual meta-actions. The system does more on its own.

## Mechanism

When a user corrects, reminds, or manually triggers something the system could have done itself:
1. **Capture** the instance (what did the user do that the system should have done?)
2. **Classify** it:
   - **Behavior** — the system produced a wrong default → fix the skill/config that produces that behavior
   - **Trigger** — the system should have auto-fired a skill/check → add the trigger condition
   - **Knowledge** — the system should have known a fact → capture it durably (wiki, AGENTS.md, goal file)
3. **Absorb** it into the appropriate system surface so it doesn't recur

## Categories and their homes

| Type of user meta-action | Where the automation lives |
|---|---|
| Corrected a repeated behavior ("stop recommending minimal") | Skill / config that produces that behavior |
| Invoked a skill the system should have suggested (`/check`, `/review`, `/tp`) | Auto-trigger when the trigger condition fires |
| Remembered a fact the system should have known ("we solved this before") | Durable artifact: wiki, AGENTS.md, or code |
| Reminded the system of a preference ("transition effort doesn't matter") | Preference files (Claude.md, AGENTS.md, skill preference sections) |

## What the user does NOT do

- Remember to run retrospectives on whether edits worked
- Remember to check if preferences are being honored
- Remember to invoke skills that should have auto-fired
- Remember facts that were established in prior sessions but not captured durably

## Instances captured (append-only log)

| Date | Instance | Classification | Resolution |
|---|---|---|---|
| 2026-07-20 | User corrected "minimal change" framing ≥5 times in one session | Behavior | Updated Claude.md, AGENTS.md, 5 skills to "optimal long-term" default |
| 2026-07-20 | User reminded "transition effort doesn't matter" multiple times | Behavior | Added to Implementation Principles in Claude.md and AGENTS.md |
| 2026-07-20 | User had to say "check github issues" and "we have another library" | Knowledge | Not yet captured durably — these were session-specific |
| 2026-07-20 | User had to invoke `/check` and `/review` manually | Trigger | `/check` already has auto-review escalation; `/review` is user-invoked by design |
| 2026-07-20 | User had to say "update the skills so they do what I said" | Behavior | Skills updated with preference sections |

---

## Standing rule (also in ~/.grok/AGENTS.md)

When the user corrects, reminds, or manually triggers something the system could have done itself: propose automating it. Don't just comply with the correction — ask "should this be automated, and where does the automation live?"
