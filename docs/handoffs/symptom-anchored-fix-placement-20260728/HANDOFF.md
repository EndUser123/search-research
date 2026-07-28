---
thread_id: symptom-anchored-fix-placement
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: console_019fa8f8
produced_at: 2026-07-28T18:40:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d6052ee
---

# Add layer-selection check to prevent symptom-anchored fix placement

## Objective (one sentence)

Add a cognitive check — "does this rule govern behavior only when this skill
is invoked, or across the session?" — that fires before writing any rule to a
SKILL.md file, preventing the pattern where a general rule triggered by a
specific symptom gets placed in the skill where the symptom appeared rather
than in AGENTS.md where the rule applies.

## Producing context

Session 019fa8f8 produced a `/why` root cause analysis of an error the model
made: placing a command-timeout rule in `/close` SKILL.md (only read at
session end) instead of `~/.grok/AGENTS.md` (always loaded). The operator
caught the error immediately: "I don't understand how a change that should
start with the session is best placed as a prose reminder in a skill that
gets used at the end of a session."

The `/why` analysis identified the root cause as **symptom-anchored fix
placement** — the model anchored on where the symptom manifested (the
`/close` scanner auto-backgrounded) rather than where the rule applies (all
Python+git commands, session-wide). The fix was correct in content but wrong
in layer.

### Second instance (same session, same pattern)

The operator asked `/www` whether a `UserPromptSubmit` hook could auto-detect
`/handoff` and pre-create a handoff file. The research found one limitation:
stdout is ignored on Grok Build passive events (no context injection back to
the model). The model anchored on this single limitation and concluded "the
whole approach is non-viable" — writing a wiki concept titled "UserPromptSubmit
hooks cannot auto-invoke skills on Grok Build."

The operator corrected: "I thought userpromptsubmit could run python?" The
hook CAN run Python, read stdin, and write files. Only the context-injection
path is blocked; the file-pre-creation path works fine. The model had taken
one constraint and generalized it to kill the entire approach.

This is the same pattern class: anchoring on a single symptom (stdout ignored)
and over-generalizing the conclusion (approach non-viable), when the constraint
only blocked one of several viable paths.

## The pattern (named)

**Symptom-anchored fix placement:** when a general rule is triggered by a
specific symptom, the model places the fix where the symptom appeared rather
than where the rule applies.

**Broader form:** anchoring on a single observed constraint and generalizing
it to block the entire approach, when the constraint only blocks one of
several viable paths.

This is the mirror of the wiki's documented anti-pattern #10 in
`context-file-deduplication-agents-md-as-source.md` ("stuffing task workflows
that should be skills"). Same root cause (wrong layer), opposite direction:

- **Documented:** general context → task-specific file (bloats always-loaded context)
- **This error:** general rule → task-specific file (hides always-needed rule behind on-demand load)

## The proposed fix

A **layer-selection check** that fires at write time, before adding any rule
to a SKILL.md file:

> Before adding a rule to a SKILL.md, ask: "Does this rule govern behavior
> only when this skill is invoked, or does it govern behavior across the
> session?" If the latter, it goes in AGENTS.md, not SKILL.md.

This is a one-line cognitive gate — like the "could I be wrong?" prompt from
Hills 2026. It doesn't need a hook. But it needs to be **salient at the
moment of deciding where to write**, not at the moment of deciding what to
write. The principle exists in the wiki but was not loaded at decision time.

## What to decide

1. **Where does the check live?** Options:
   - AGENTS.md (always-loaded, but bloats if every micro-check is added)
   - The wiki concept `context-file-deduplication-agents-md-as-source.md`
     (already documents the principle, but on-demand load)
   - A new wiki concept specifically for this pattern (more findable via `/why`)

2. **Is the check the right fix, or should the pattern be a Stop hook?**
   - A Stop hook could scan for SKILL.md edits that contain general rules
     and flag them. But "general rule" detection is fuzzy — false positives
     likely.
   - A cognitive check is cheaper but less reliable (same failure class as
     all behavioral rules — doesn't fire under closure pressure).

3. **Should the check be added to the File editing protocol section of
   AGENTS.md?** That section already has rules about "before editing a
   skill, verify the path exists" — a layer check would fit alongside.

## Acceptance criteria

1. The layer-selection check is documented somewhere the model will encounter
   it at write-decision time (not just in a wiki concept searched on demand)
2. The check is one sentence, not a paragraph
3. The pattern is named ("symptom-anchored fix placement") so it can be
   referenced in future `/why` investigations
4. The falsifier from the `/why` analysis is preserved (the analysis is wrong
   if the pattern never recurs without a structural fix)

## Read-first list

- `~/.grok/AGENTS.md` § "File editing protocol" — where skill-editing rules live
- `~/.grok/AGENTS.md` § "Skill locations (one scope per skill)" — the existing
  layer rules
- `P:/.data/wiki/concepts/context-file-deduplication-agents-md-as-source.md`
  item #10 — the documented anti-pattern this mirrors
- The `/why` analysis from session 019fa8f8 (in the conversation transcript)

## Constraints

- Do not add more than 2-3 lines to AGENTS.md — it's already large
- The check must be a cognitive gate (like "could I be wrong?"), not a hook
- The pattern name "symptom-anchored fix placement" should be preserved for
  future `/why` queries

## Falsifier (from the /why analysis)

This analysis is wrong if:
- The model actually knew the rule was general but chose SKILL.md for a
  specific reason (it didn't — there was no reason)
- The real cause was something else (e.g., not knowing AGENTS.md existed —
  false, the model had been reading from it all session)
- The pattern doesn't recur (if the model never makes this error again
  without a structural fix, the analysis was over-attributed to a pattern
  when it was a one-off slip)
- **Note:** the pattern recurred twice in the same session (close-timeout
  layer error + UserPromptSubmit over-generalization), which strengthens the
  pattern hypothesis. A one-off slip would not recur twice.

## Next steps (when this thread resumes)

1. Read AGENTS.md § "File editing protocol" to find the right insertion point
2. Decide: AGENTS.md bullet vs. wiki concept vs. both
3. Add the layer-selection check with the pattern name
4. Consider whether the `context-file-deduplication-agents-md-as-source.md`
   concept should be updated to document the mirror pattern (general rule →
   skill file) alongside its existing item #10 (general context → skill file)
