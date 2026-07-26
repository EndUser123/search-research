---
thread_id: skill-recommendation-hook-20260726
parent_handoff_path: P:/docs/handoffs/session-019f9f48-shipped-work-20260726/HANDOFF.md
current_session_id: 019f9f48-5ad0-7a01-9f1e-e70d0788d383
current_terminal_id: grok-019f9f48
produced_at: 2026-07-26T21:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: eb25425
---

# Skill recommendation hook — surface "you should use /X here" at the right moment

## Objective

Build a mechanism that proactively surfaces skill recommendations at the moment a skill would be most valuable — without being intrusive. The hook observes session state (what was said, what was done, what claims were made) and recommends a skill when its trigger conditions are met. Example: after the agent ships code changes and claims "done," the hook recommends `/check`. After the agent endorses a deployment pattern, it recommends `/review`. After a multi-file refactor, it recommends `/refactor --focus maintainability`.

This is the **skill-recommendation** sibling of `/notice` (which surfaces observations). `/notice` answers "did you notice anything?"; this hook answers "should you be using a different skill right now?"

## Background

### Why this matters

The operator manages a fleet of AI coders and uses ~30+ skills across the workspace. Skills are powerful but only when invoked at the right moment. Three failure modes recur:

1. **Skill not invoked when it would have caught a problem.** This session: the close-format-enforcement gate was bypassed because `/check` wasn't run until the very end. If `/check` had been recommended mid-session after the validator code shipped, the format spec violation would have been caught earlier.
2. **Skill invoked too late.** `/review` auto-fires at `/check` time (Step 6.2) — but by then the session is at close. Recommending `/review` *earlier* (when load-bearing changes first land) would catch issues before they compound.
3. **Skill not known to exist.** The skill catalog has 978 skills. The operator can't hold them all in working memory. A recommendation surface that says "there's a skill for this" closes the discovery gap.

### What already exists (don't duplicate)

| Mechanism | What it does | Gap this hook fills |
|---|---|---|
| `/check` Step 6.2 auto-/review triggers | Auto-fires `/review` when load-bearing triggers fire at check time | Fires at the END (check time), not when the trigger condition first arises |
| `/notice` | Surfaces observations mid-conversation (contradictions, drift, friction) | Observations, not skill recommendations. Different content type. |
| `/close` SKILL.md verification suggestion rule | Recommends `/check` or `/review` at end of turn when triggers fire | End-of-turn only; doesn't fire mid-task or at task boundaries |
| AGENTS.md "Proactive verification suggestions" | Same as /close rule — end-of-turn recommendation | Same gap |
| Skill catalog (`index_skills.py`) | Lists all 978 skills with descriptions | Passive — requires the agent to search, doesn't push |
| `advisory-vs-mandatory-triggers` wiki concept | Design principle: mandatory for data-loss prevention, advisory for context surfacing | This hook is advisory (per the concept's blast-radius rule) |

### The design tension

This is **advisory, not mandatory** (per `advisory-vs-mandatory-triggers` — skill recommendations don't prevent data loss; they surface useful context). Advisory mechanisms have a known failure mode: they get ignored under closure pressure. The `/notice` skill documents this (Chen et al. CHI 2025: preference dropped 80→47% when suggestion frequency increased). So the hook must be:

- **Rare** (max 1 per 10 turns, like `/notice`)
- **Precise** (low false-positive rate — recommending `/check` when no code shipped would train the operator to ignore it)
- **Deferent** (one line, "Ignore if not relevant," no multi-paragraph intervention)
- **Trigger-grounded** (fires on mechanical signals, not vibes)

## Open questions (what needs deciding)

### 1. Hook type: Stop hook vs. UserPromptSubmit hook vs. skill

Three candidate mechanisms:

| Mechanism | Pros | Cons |
|---|---|---|
| **Stop hook** (scans assistant output before turn ends) | Fires after every turn; can see what was done | Adds latency to every turn; Stop hooks are already load-bearing (don't want to overload) |
| **UserPromptSubmit hook** (scans user input before agent responds) | Can recommend a skill BEFORE the agent starts working | Can't see what the agent did; only sees the user's prompt |
| **Skill** (like `/notice` — invoked manually or auto-suggested) | No latency cost; operator controls when to check | Doesn't fire proactively; requires the operator to remember to invoke |

**Recommendation: Stop hook** — it sees both what the agent did AND can recommend before the next turn. The latency cost is manageable if the trigger detection is cheap (regex/keyword matching, not LLM inference). This is the same architecture as the existing Stop hooks (cross-validator, fake-done-detector).

### 2. Trigger taxonomy: what signals warrant a skill recommendation?

Candidate triggers (to be refined during implementation):

| Signal | Skill to recommend | Rationale |
|---|---|---|
| Agent claims "done" / "fixed" / "complete" on code changes | `/check` | Session-grounded verification before moving on |
| Agent endorses a deployment/configuration pattern across ≥2 tools | `/review` | Fresh-eyes review of the endorsement (the receipt-misattribution pattern) |
| Agent touches hooks/plugins/schemas/contracts | `/review` | Load-bearing surface trigger (same as /check Step 6.2) |
| Agent makes a causal claim ("X happens because Y") about workspace code | `/why` | RCA discipline before the claim ships |
| Agent proposes a multi-file change without a plan | `/plan` or `/go` | Plan-before-execute pattern |
| Agent responds to operator correction with theatrical contrition | (meta) | Flag for the anti-fawning pattern — not a skill rec, but a behavior signal |
| Agent writes a wiki concept with endorsement language | (existing validator) | Already covered by `validate_disconfirmation.py --www-recommendations` |
| Session exceeds N turns without any verification skill invoked | `/check` | Stale-verification signal |

### 3. Output format

Per `/notice` research (Chen et al., Harari & Amir): one line, deferent, non-blocking.

```
Skill suggestion: /check — code was modified but not verified this session. Run /check before moving on? Ignore if not relevant.
```

- One line
- Names the skill with `/` prefix
- Names the trigger (why this skill, now)
- Ends with "Ignore if not relevant"
- Never more than 1 per 10 turns (cooldown, same as `/notice`)

### 4. Cooldown and calibration

Same as `/notice`:
- Default: max 1 per 10 turns
- Hard floor: never twice in 5 turns
- State file: `~/.grok/state/skill-rec-cooldown.json`
- Operator can adjust with a calibration flag

### 5. Where the trigger rules live

| Option | Pros | Cons |
|---|---|---|
| Hardcoded in the hook script | Fast, no parser dependency | Rules changes require code edit |
| TOML/JSON config file (`~/.grok/skill-rec-triggers.toml`) | Operator can tune without code change | Adds a config parser; another file to maintain |
| Read from each skill's SKILL.md frontmatter (`triggers:` field) | Self-documenting; skills own their own triggers | Requires every skill to declare triggers; parser complexity |

**Recommendation: hardcoded for v1, config file for v2.** The trigger list is small (8-12 entries); hardcoding is simpler. If the list grows past ~20, promote to config.

## Scope

### What this handoff covers

- Design of the skill-recommendation hook
- Trigger taxonomy
- Output format and cooldown discipline
- Integration with existing `/notice`, `/check` auto-/review, and AGENTS.md rules

### What this handoff does NOT cover

- Building new skills (the hook recommends existing skills, doesn't create them)
- Replacing `/check` Step 6.2 auto-/review (that stays — this hook fires earlier and more broadly)
- Replacing the `/notice` skill (different content type — observations vs. skill recs)
- The anti-fawning fix (separate handoff at `anti-fawning-opportunity-20260726`)

## Acceptance criteria

1. A Stop hook fires after each turn and checks trigger conditions
2. When a trigger matches, the hook outputs one line: `Skill suggestion: /<skill> — <reason>. Ignore if not relevant.`
3. Cooldown enforced (max 1 per 10 turns, hard floor 1 per 5)
4. Trigger detection is mechanical (regex/keyword, not LLM) — sub-100ms latency
5. False-positive rate <20% in the first 10 sessions (measure and calibrate)
6. The hook does NOT fire on: first turn of session, mid-implementation (`/go` running), acceleration mode (same hard-skip rules as `/notice`)
7. State file tracks cooldown and observation log (for `/aar` synthesis)

## Recommended approach

1. Read `/notice` SKILL.md — it's the architectural sibling. Same hard-skip rules, same cooldown, same output format, same deferent stance
2. Read `advisory-vs-mandatory-triggers` — confirms this is advisory (not mandatory)
3. Read `/check` SKILL.md Step 6.2 — the existing auto-/review trigger logic. This hook generalizes it
4. Read the existing Stop hooks (`~/.grok/hooks/*.json` for Stop events) to understand the dispatch pattern
5. Implement as a Stop hook at `~/.grok/hooks/scripts/skill_recommendation.py` with a JSON registration in `~/.grok/hooks/skill-recommendation.json`
6. Start with 3-5 triggers (the highest-signal ones from the taxonomy above); expand after calibration
7. Test: simulate each trigger condition and verify the hook fires the right recommendation

## Evidence (why this is worth building)

- **Session 019f9f48**: the close-format enforcement gate was bypassed because `/check` wasn't run until the end. A mid-session `/check` recommendation (after the validator code shipped) would have caught it earlier.
- **Session 019f9f48**: `/review` auto-fires only at `/check` time — by then the session is at close. Earlier recommendation (when AGENTS.md and close/SKILL.md were edited) would have caught the format issue before close.
- **The workspace has 978 skills.** The operator can't hold them all in working memory. A push mechanism (the hook recommends) is more reliable than a pull mechanism (the operator remembers to search).
- **`/notice` validated the architecture.** The research base (Chen et al. CHI 2025, Pu et al. CHI 2025, Harari & Amir 2025) applies directly. The cooldown, hard-skip, and deferent-output rules are already designed.

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing — non-blocking to other work
- **Non-blocking to:** all other skill/hook improvement workstreams

## Read-first list

1. `C:/Users/brsth/.grok/skills/notice/SKILL.md` — architectural sibling (cooldown, hard-skip, output format, research base)
2. `P:/.data/wiki/concepts/advisory-vs-mandatory-triggers.md` — design principle (this is advisory)
3. `P:/.grok/skills/check/SKILL.md` Step 6.2 — existing auto-/review trigger logic to generalize
4. `~/.grok/AGENTS.md` § "Proactive verification suggestions" — existing end-of-turn rule
5. `P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md` — research base for proactive surfacing

## Status

OPEN. Not started. Design captured; implementation deferred to fresh session.

## Decisions made

- **Advisory, not mandatory.** Per `advisory-vs-mandatory-triggers`: skill recommendations don't prevent data loss; they surface useful context. Blast radius is low; enforcement should match.
- **Stop hook, not UserPromptSubmit or skill.** Stop hook sees both what the agent did and can recommend before the next turn. Latency is manageable with mechanical trigger detection.
- **Hardcoded triggers for v1.** Small list (8-12), simple to maintain. Promote to config if it grows past ~20.
- **Same cooldown as `/notice`.** Max 1 per 10 turns, hard floor 1 per 5. Chen et al. showed preference collapse at higher frequency.

## Related wiki concepts (qmd grounding)

- `proactive-ai-volunteering-mechanisms` — research base (mechanism 2 is `/notice`; this would be mechanism 3)
- `advisory-vs-mandatory-triggers` — design principle
- `theatrical-contrition-and-over-apologetic-response-patterns` — related (the hook could flag the anti-fawning pattern as a behavior signal)

## Other outstanding streams (named for awareness)

- **Anti-fawning structural fix** → `anti-fawning-opportunity-20260726/HANDOFF.md` (research done, implementation deferred)
- **Close format enforcement gate** → `close-format-enforcement-gate-20260726/HANDOFF.md` (validator extension for canonical renderer)
- **Recommendation-receipt validator scope gap** → recorded as known limitation in `session-019f9f48-shipped-work-20260726/HANDOFF.md`

## Last user message (verbatim)

> /handoff for a hook that can tell us when we should use a specific skill, like '/check' or '/review', or anything else we have.

## Falsifier

This handoff is wrong if:
- The hook fires too often and the operator disables it within 30 days (same falsifier as `/notice`)
- The trigger taxonomy produces >30% false positives in practice (recommending skills when they're not needed)
- The existing mechanisms (`/check` Step 6.2, AGENTS.md end-of-turn rule) are actually sufficient and this hook adds noise without value
- A vendor ships a native skill-recommendation feature that makes this obsolete

If any pattern appears, iterate the hook or retire it.
