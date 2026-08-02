# Handoff: Session review skill division — /recap, /todo, /tp boundaries

**Status:** OPEN — architecture decided, boundaries need implementation  
**Created:** 2026-08-01  
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9  
**Operator directive:** 2026-08-01, "So we need a recap skill and we need a to-do skill. TP can call to-do or recap as needed."

## Architecture (operator-decided)

Three skills with clean boundaries. No skill produces another's output.

| Skill | Question | Direction | Scope |
|-------|----------|-----------|-------|
| **/recap-grok** | "What happened?" | Backward (reconstruction) | Session transcript chain |
| **/todo** | "What's next?" | Forward (action) | Fleet-wide open work |
| **/tp** | "Is this good?" | Evaluative (judgment) | Whatever the operator asks about |

**/tp is the orchestrator that can call /recap or /todo when it needs their output.** Not the other way around. /recap doesn't call /tp. /todo doesn't call /recap.

## Current overlap (what needs to be eliminated)

### /recap-grok currently produces:
- Causation chains ✅ (keep — this is reconstruction)
- Meta-level narrative ✅ (keep — this is reconstruction)
- Quality assessment ⚠️ (boundary question — see below)
- **Pending work items + Next Session Checklist** ❌ (remove — this is /todo's job)
- **Cross-invocation suggestions (/handoff, /debrief, /wiki)** ❌ (remove — /tp's job when it calls /recap)

### /todo currently produces:
- Coverage scan (open handoffs) ✅ (keep — this is fleet scanning)
- Git status / at-risk items ✅ (keep)
- Email scan ✅ (keep)
- **Self-reflection "what else?" prompt** ⚠️ (should use /tp's mechanical transcript scan instead)
- Action list ✅ (keep — this is the output)

### /tp session currently produces:
- Transcript friction scan (mechanical pattern counting) ⚠️ (this is evaluation, but /recap could use it for causation chains)
- Session arc (topics) ⚠️ (this is reconstruction — overlaps with /recap)
- Git commit scan ⚠️ (overlaps with both /recap and /todo)
- CROSS-DOMAIN NOTICES ✅ (keep — this is evaluation)
- NOW/NEXT/LATER findings + actionable recommendations ✅ (keep — but route action items to /todo)
- Dynamic skill recommendation pass ✅ (keep)
- **Compaction segment analysis** ⚠️ (overlaps with /recap — both read segments)

## Boundary questions to resolve during implementation

### Question 1: Where does "started but not completed" go?
A recap naturally surfaces "this task was started but not finished." That's pending work, which is /todo's domain. Options:
- **A:** /recap notes it as a fact ("Task X was started, commit abc123, not merged") without producing an action item. /todo picks it up from the handoff/commit evidence.
- **B:** /recap produces a "noted but not actionable" section. /todo reads /recap's output when called next.
- **Recommendation:** A — /recap states facts, /todo produces actions. The boundary is "facts vs actions," not "past vs future."

### Question 2: Does /tp session survive as a mode?
If /recap handles reconstruction and /todo handles actions, /tp session's remaining unique value is: CROSS-DOMAIN NOTICES, quality assessment (CONTINUE/STOP/FRICTION/SURPRISE), and the mechanical transcript friction scan. Options:
- **A:** /tp session survives but calls /recap for reconstruction data instead of doing its own transcript reading. It focuses on evaluation only.
- **B:** /tp session is removed. /recap absorbs the friction scan (it's part of "what happened"). /tp (default critique mode) handles evaluation when asked.
- **Recommendation:** A — /tp session stays but becomes thinner. It consumes /recap's output and evaluates it, rather than re-reading the transcript.

### Question 3: /tp's actionable recommendations
/tp session currently produces a numbered action list with dispositions (DO_NOW, NEW_HANDOFF, etc.). If /todo is the action list skill, /tp shouldn't duplicate. Options:
- **A:** /tp produces findings with dispositions but no action list. It recommends "run /todo to get your action list" at the end.
- **B:** /tp calls /todo internally, feeds it the findings, and /todo produces the unified action list.
- **Recommendation:** B — /tp calls /todo. One action list, not two.

## What this eliminates

- Three overlapping action lists at session end → one (/todo)
- Three overlapping transcript reads → one (/recap, consumed by /tp if needed)
- Three overlapping git scans → /todo for fleet, /recap for this session
- The operator running 3 commands and mentally merging outputs → run /recap, then /todo, or let /tp call both

## What this does NOT change

- /tp (default critique mode) — unchanged
- /tp explore — unchanged
- /tp quick — unchanged
- /handoff — unchanged (writes work artifacts, not session reviews)
- /close — calls /tp session which calls /recap + /todo internally

## Research grounding

Practitioner source (DEV Community, "My Coding Agent Remembered Sessions, Not Work"):
> "Sessions are implementation details. Work is the product surface."
> "What are you summarizing *into*?"

The insight: the unit should be work, not conversation. Our three skills are conversation-shaped (all read transcripts). The division above moves toward work-shaped: /recap answers "what work was done," /todo answers "what work remains," /tp answers "is the work good."

## Acceptance criteria

1. /recap-grok produces reconstruction only — no action items, no cross-invocation suggestions
2. /todo produces action items only — no reconstruction, no evaluation
3. /tp session consumes /recap output instead of re-reading transcripts
4. /tp session calls /todo for action items instead of producing its own
5. The operator can run /recap → /todo (or just /tp session which calls both) and get one coherent view

## Constraints

- Do NOT create a 4th skill. Merge boundaries, not create new surfaces.
- Do NOT remove /tp session — make it thinner by delegating to /recap and /todo.
- The operator has too many skills. This should reduce surface area, not increase it.
