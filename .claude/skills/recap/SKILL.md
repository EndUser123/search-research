---
name: recap
description: Catch up on all sessions in this terminal via checkpoint chain traversal and surface unresolved assumptions, contract gaps, Contract Authority Packet gaps, and resume risks
version: 1.2.0
status: stable
category: session
triggers:
  - /recap
execution:
  directive: Run the recap CLI to show terminal session history
  default_args: ""
  examples:
    - "/recap"
    - "/recap brief"
---

# /recap — Terminal-Wide Session Catch-Up

**Problem solved:** "I have 10 sessions compaction-deep in this terminal and I need to know what happened."

## Core Concept

`/recap` aggregates context from ALL sessions in this terminal by directly analyzing the transcript file. Session boundaries are detected via `sessionId` changes in the transcript. No handoff files required — works independently.

## How It Works

1. **Find transcript file**: Searches terminal file registry, project-local, and user-level transcript locations
2. **Parse transcript**: Loads JSONL transcript file directly
3. **Detect session boundaries**: Identifies sessions by `sessionId` changes in transcript
4. **Aggregate context**: Extracts goals, message counts from each session
5. **Present summary**: Shows chronological session history

## Output Structure

The script extracts structured data via regex. The responding LLM then synthesizes it.

### Script Output (regex-extracted facts)
```
# Terminal Recap: {terminal_id}

## Session History
**Total Sessions**: {count}

[Session 1] {session_id}
- Entries: {n}
- User messages: {n} / Assistant messages: {n}
- Last goal: {goal}
- Problem: {extracted problem}       # from **What was the problem?**
- Fix: {extracted fix}               # from **What was the fix?**
- Action: {extracted action}         # from **What did we do?**
- Decision: {decision if found}
- Outcome: {outcome if found}
```

### Response Synthesis (LLM task after script output)

When responding to `/recap`, apply reasoning to the script output plus the raw transcript context. For each session, synthesize:

**Problem**: What was the underlying issue? Not just the symptom — the root cause.

**What was done**: What actually changed (file edits, hooks, skills, configs). Be specific about the actual action.

**Optimal fix**: What would the ideal solution have been? This may differ from what was done. Consider:
- Was the fix a workaround vs. root cause resolution?
- Was the approach optimal given the constraints?
- Was anything missed or left incomplete?

**Contract/resume gaps**: What assumptions were left unstated or unverified? Explicitly surface:
- unresolved producer/consumer assumptions
- incomplete handoff or restore logic
- “discussed” vs “actually verified”
- missing proof that resume/consumer paths really worked
- missing, stale, or ignored `Contract Authority Packet` state for contract-sensitive work

Present synthesis as a per-session narrative in the response, not replacing the script output but complementing it.

## Usage

```bash
/recap                    # Show full terminal recap (current + history)
/recap brief              # Show brief catch-up summary only
```

## Routing Behavior

`/recap` may suggest lower skills when the reconstructed session history shows missing gates:

- suggest `/gto` when current gaps or stale assumptions are unclear
- suggest `/arch` when unresolved state or contract decisions appear in prior sessions
- suggest `/verify` when work was discussed or implemented but not actually proven

`/recap` should not implement fixes itself.

## Implementation Notes

- Finds transcript files via terminal file registry (`/term` skill) or common locations
- Parses JSONL transcript files directly (no handoff package dependency)
- Detects session boundaries via `sessionId` field changes
- Independent of handoff hooks and task tracker files
- Semantic extraction (problem/fix/action) via regex against structured output patterns (bugfixes.md format)
- Synthesis (optimal fix reasoning) is performed by the responding LLM — not in preprocessing
