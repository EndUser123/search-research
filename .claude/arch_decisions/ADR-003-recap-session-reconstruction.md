# ADR-003: Enhance /recap Session Reconstruction

**Date:** 2026-04-11
**Status:** Proposed
**Decider:** Bruce Thomson

## Context

`/recap` is intended to provide "terminal-wide session catch-up" by reconstructing what happened in prior sessions. However, the current implementation fails when session chain traversal returns subagent transcripts instead of the actual prior session, and when it falls back to the wrong transcript file.

### Failure Observed

When `/recap` was invoked in a resumed session (post-compaction), it showed:
- **Goal**: "# HOD - Enhanced Session Continuity and Handover System" (startup framework, not actual work)
- **Total Sessions**: 1 (the current session only)
- **Missing**: All prior session work (8h 59m session ending at 07:02)

The prior session's work was captured in the session summary block at transcript startup, but `/recap` never extracted it.

### Root Causes (3-Bug Analysis)

**B1 — Subagent Transcript as Standalone Session:**
`walk_session_chain()` returned 1 chain entry pointing to a subagent transcript (`agent-ae7b34...jsonl`) that exists and is valid. Because it returned a non-empty result, the fallback to direct transcript scanning was skipped. The subagent's transcript contained only the current session's startup content.

**B2 — sessions-index.json parentUuid Absent:**
The `sessions-index.json` entries have no `parentUuid` field populated. The mtime-gap heuristic (MAX_MTIME_GAP_SECS=120s) couldn't reliably link the current session to its prior, since the main transcript and subagent transcript have nearly identical mtimes (~5 sec apart).

**B3 — Session Summary Block Never Parsed:**
The compaction handoff captures the prior session's work in a structured block:
```
## Last Session Summary
**When:** 2026-04-11T07:02:43.190608+00:00
**Duration:** ~8h 59m
```
This block is present at the START of the current transcript but is treated as plain transcript content, not a structured handoff artifact.

### Contract Boundaries

**Boundary 1: Transcript Selection**
- Producer: `session_chain.py` (via `walk_session_chain`)
- Consumer: `recap/__init__.py` (`_load_all_sessions_via_history_index`)
- Input: current session ID
- Output: list of chain entries with transcript_path
- Required: transcript_path must be a `.jsonl` file at project level, not a subagent path
- Freshness: transcript must exist and contain user/assistant entries
- Failure: if chain is empty or all paths invalid → fallback to sessions-index scan

**Boundary 2: Session Summary Handoff**
- Producer: `PreCompact` hook (emits session summary block at compaction)
- Consumer: `recap/__init__.py` (`_summarize_session`)
- Input: transcript entries with `## Last Session Summary` block
- Output: structured dict with goal, duration, work summary
- Required: `**When:**`, `**Duration:**` > 0, content > 50 chars
- Quality gate: content must not be solely a markdown heading or < 50 chars
- Freshness: stale if current transcript has multiple session IDs
- Failure: degrade to mtime-based transcript if quality gate fails
- Precedence: summary = prior session; post-summary entries = current session. Show both.

## Decision

Implement three targeted fixes:

### Fix R1: Transcript Path Validation in Chain Walk Consumer

In `recap/__init__.py::_load_all_sessions_via_history_index`, after `walk_session_chain` returns:

1. **Filter** — Remove all entries whose `transcript_path` is a subagent transcript:
   - Semantic rule: A path is a subagent transcript if it is a `.jsonl` file in a `subagents/` subdirectory of a session folder, OR its filename starts with `agent-`.
   - Not a raw string heuristic — classification must use structural path analysis.
2. **Validate** — For remaining entries, verify:
   - Exists on disk
   - Contains user/assistant transcript entries (via `_is_transcript_file`)
3. **Handle results**:
   - If ALL entries filtered/validated to empty → treat as empty chain → trigger fallback
   - If MIXED (some valid, some invalid) → return only the valid entries, preserving chain order
   - If ALL valid → return full chain

This ensures partial chain failures degrade gracefully without losing valid entries.

### Fix R2: Session Summary Block as Primary Fallback Signal

In `recap/__init__.py::_load_all_sessions_via_history_index`, when falling back to direct transcript scan, add a new step BEFORE finding the "most recent transcript by mtime":

1. **Parse session summary blocks** from the current transcript's early entries (first 200 lines or first 50 entries)
2. **Validate quality** — A session summary is usable only if ALL of:
   - Contains `**When:**` field with a timestamp
   - Contains `**Duration:**` field with value > 0
   - Content between `## Last Session Summary` and next `##` is > 50 chars
3. **Precedence rule** — If valid summary exists:
   - The summary block captures the PRIOR session's work
   - Current transcript entries AFTER the summary block represent current-session work
   - Show BOTH: prior session (from summary) AND current session (from post-summary entries)
   - If post-summary entries contain user/assistant messages → current session had active work
4. **Degradation** — If no valid summary:
   - Fall back to current behavior (most recent transcript by mtime)

Session summary block regex:
```
##\s*Last\s*Session\s*Summary\s*\n(?:.*?\n)*?(?=\n##|\Z)
```
Fields to extract: `When`, `Duration`, and all content between the header and the next `##`.

**Quality heuristic** — If extracted content starts with `#` (markdown heading) or is < 50 chars, treat as failed parse and fall back to mtime transcript.

### Fix R3: Semantic Subagent Path Classification

In `recap/__init__.py::_load_all_sessions_via_history_index`, classify a path as a subagent transcript using **structural path analysis**, not raw string matching:

A transcript path is a subagent transcript if it matches ANY of:
1. The filename (not full path) starts with `agent-` (e.g., `agent-ae7b34cfd803699a.jsonl`)
2. The path contains `/subagents/` or `\subagents\` as a path component (not substring — use `Path().parts`)
3. The parent directory name is `subagents`

**Implementation** — Add helper `_is_subagent_transcript(path: Path) -> bool` that uses structural checks:
```python
def _is_subagent_transcript(path: Path) -> bool:
    parts = path.parts
    # Component-level check, not substring
    if "subagents" in parts:
        return True
    # Filename prefix check
    if path.name.startswith("agent-"):
        return True
    return False
```

This replaces the raw substring check `/subagents/` with semantic path analysis that is robust to normalization and Windows/Unix path differences.

## Consequences

**Positive:**
- Prior session summary is captured even when chain traversal fails
- Fallback correctly prioritizes the handoff signal over recency
- Subagent transcripts no longer pollute the session chain

**Negative:**
- Additional parsing step adds slight latency on fallback path
- Session summary parsing depends on consistent block format

**Alternatives Considered:**

1. **Fix `sessions-index.json` parentUuid population** — This is a deeper fix in Claude Code itself, outside the scope of `/recap` enhancement. Bypassed.
2. **Always read current transcript first, then chain** — Current behavior already does this. The issue is that the current transcript is the compacted session, and the prior session data is in the summary block, not in a separate file.
3. **Use handoff file directly** — The handoff file contains the prior session summary, but it may not always exist. Session summary block in transcript is more universally available.

**Follow-up (Out of Scope):**
- **Structured JSON handoff** — Codex recommended replacing the regex-parsed session summary block with a structured JSON artifact emitted by PreCompact. This is the correct long-term fix but requires modifying PreCompact. A separate ADR should address this after the immediate fixes are implemented.

## Implementation Notes

**File:** `P:/.claude/skills/recap/__init__.py`

**Changes:**
1. In `_load_all_sessions_via_history_index` (around line 1029): Add subagent path filter before returning `chain_sessions`
2. In `_load_all_sessions_via_history_index` fallback block: Add session summary parsing step
3. In `_summarize_session`: Extract session summary block from early transcript entries and use as `last_goal` if available

**Test Cases:**
- T1: Current session chain returns subagent-only → fallback triggers, session summary is extracted
- T2: Session summary block exists with actual prior work → that work is shown in recap
- T3: Session summary is absent → fallback to most recent transcript (existing behavior)
- T4: Chain returns valid main-session transcript → subagent paths filtered out, chain used directly
- T5: Mixed chain (valid + subagent) → valid entries preserved in chain order, subagent dropped
- T6: Both summary block AND current-session work in same transcript → show both, not just summary
- T7: Summary block present but empty/stale (no Duration, < 50 chars) → fallback to mtime transcript
- T8: Path normalization — Windows separators, case variants → subagent filter correctly classifies
- T9: Malformed summary block with extra markdown headings inside → quality heuristic rejects, falls back
