# ADR-006: Compact Session Handoff — Verbatim Last User Message Field

**Date:** 2026-04-16
**Status:** Accepted
**Decider:** Bruce Thomson

## Context and Problem Statement

When a session is compacted mid-workflow, the SessionStart hook generates a `last_session.md` summary that promotes discussion topics to "outstanding work items." This conflates questions with directives — the summarizer model has no turn-type classification, so a question like "what does skill-creator optimize?" gets framed as an open task rather than a completed query.

The post-compact agent receives the summary and interprets the "Open items" framing as authorization to continue work that was never authorized. This is the compact handoff misframing problem.

Four solutions were evaluated:
1. **Verbatim field** — Add `**Last user message:**` verbatim capture to `last_session.md`
2. **Discussed/decided split** — Separate "discussed" vs "decided" sections in summary
3. **Turn-type classifier** — Classify last message as question/directive/statement in compact hook
4. **Recovery downstream** — Accept misframing and rely on downstream correction

Solution 1 was identified as optimal for this environment.

## Decision

Add a `**Last user message:**` verbatim capture to `SessionStart_tldr.py` output. The field is appended as a new section in `last_session.md` alongside `When`, `Duration`, `Accomplished`, `Files changed`, and `Open items`.

The verbatim text eliminates ambiguity about what the user actually said before compaction. Downstream agents can compare `Open items` framing against the verbatim field to detect misframing.

## Implementation

**File:** `P:/.claude/hooks/SessionStart_tldr.py`

**Change:** Append `**Last user message:** {verbatim}` to summary output, where `{verbatim}` is the last `role="user"` message content from the conversation transcript.

**Data format validated (Tier 1 evidence):**
- Input: conversation transcript (message list with `role` and `content` fields)
- Output: sectioned markdown with `**Last user message:**` line appended
- Extraction: walk transcript backward, find last `role="user"`, return `content` stripped

**Sample output (after):**
```markdown
## Session Summary
**When:** 2026-04-16T21:56:37.688061+00:00
**Duration:** ~11m
**Accomplished:** - (no activity recorded)
**Files changed:** - (none)
**Last user message:** what does skill-creator optimize?
```

## Contract Boundary

| Field | Value |
|-------|-------|
| Boundary | SessionStart hook → post-compact agent handoff |
| Producer | `SessionStart_tldr.py` |
| Consumer | Post-compact agent (via session handoff) |
| Input schema | Full conversation transcript |
| Output schema | Sectioned markdown with new `Last user message` field |
| Required fields | None (field is optional — existing sections remain mandatory) |
| Freshness authority | SessionStart hook (session end) |
| Invalidation trigger | New session_start event overwrites `last_session.md` |
| Failure behavior | Graceful degradation — consumer falls back to `Open items` framing if field absent |
| Transcript-vs-artifact precedence | `last_user_message` verbatim field beats `Open items` framing |

## Why Not the Other Solutions

**Solution 2 (discussed/decided split):** Addresses a different ambiguity — the meaning of `Accomplished` and `Open items` labels. Does not solve the verbatim question problem. More complex schema change with downstream parsing implications.

**Solution 3 (turn-type classifier):** Addresses the root cause but requires classification logic that is brittle to implement and validate. Misclassification still produces misleading output. Edge cases for "what counts as decided" are unresolved.

**Solution 4 (recovery downstream):** Correctly identifies that the fix should be at generation, not recovery. Does not provide a recovery mechanism in the meantime. Agrees with Solutions 1 and 3 being the upstream fixes.

## Consequences

**Added:**
- New `**Last user message:**` section in `last_session.md`
- `extract_last_user_message()` function in `SessionStart_tldr.py`

**No existing functionality removed.** The change is purely additive — all existing sections remain.

**Backwards compatible:** Existing parsers that don't recognize the new section will ignore it (markdown prose behavior). No schema migration required.

## Verification

```bash
# After implementation, verify:
# 1. last_session.md contains the new field
# 2. Field contains verbatim text of last user message (not summarized)
# 3. No existing sections were modified or removed
```

## Follow-Up

After implementing the verbatim field, if `Open items` still contains misframed items, a downstream recovery rule can be added:
- Compare `Open items` content against `Last user message` verbatim
- If clear mismatch detected, prefer verbatim and discard Open items framing
- This is a separate implementation step, not part of this ADR