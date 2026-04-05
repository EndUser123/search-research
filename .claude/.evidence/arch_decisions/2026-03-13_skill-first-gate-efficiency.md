# Architecture Decision: Fix Skill-First Gate Historical Context Bug

**Date**: 2026-03-13
**Template**: fast (LOW complexity, Generic domain)
**Intent Type**: IMPROVE_SYSTEM

---

## Decision Statement

Fix the skill-first gate's historical context bug that causes false blocks when legitimate slash commands are issued after previous slash commands in the same session. The gate incorrectly checks `transcript[-5:]` (previous messages) instead of only the current turn's intent, wasting ~370 tokens per false block incident.

---

## Options

### Option A: Remove Historical Context Check

**Proposed change**: Delete lines 521-535 in `PreToolUse_skill_pattern_gate.py` that check `transcript[-5:]` for Skill usage. Rely solely on current `user_message` parsing (lines 500-518) which correctly extracts slash command intent.

- **Pro**: Eliminates false blocks, prevents wasted generation (~370 tokens per incident)
- **Con**: Removes ability to detect Skill usage earlier in current response (edge case)
- **Differs on**: Context scope (current turn vs historical)

### Option B: Add Current-Turn Tool Tracking

**Proposed change**: Enhance gate to track tool call sequence within current response, not across historical messages.

- **Pro**: More accurate skill-first detection for multi-tool responses
- **Con**: More complex, requires current-turn state tracking
- **Differs on**: Implementation complexity

---

## Recommendation

**Option A** is better than Option B because the current `user_message` parsing (lines 500-518) already correctly identifies slash command intent. The historical check is the bug, not a missing feature. Option B adds complexity for an edge case that doesn't exist in practice.

---

## Implementation

### Before (lines 521-535 in PreToolUse_skill_pattern_gate.py)
```python
# Check if this is the first tool call in the response
try:
    transcript = data.get("transcript", [])
    if transcript:
        # Check if Skill tool was already used in this response
        for item in transcript[-5:]:  # BUG: Checks historical messages
            if isinstance(item, dict):
                content = item.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Skill":
                                # Skill tool was already used - allow other tools
                                return {}
except Exception:
    pass
```

### After (remove entire section)
```python
# REMOVED: Historical context check causes false blocks
# Current user_message parsing (lines 500-518) is sufficient
# Template-based skills (/arch, /verify, etc.) use Read/Grep/Glob directly
```

**Rollback**: Restore lines 521-535 if historical context check is needed

---

## Quick Ramifications

- **Break anything?**: No - removes buggy code, doesn't change correct behavior
- **Edge cases?**: Multi-tool responses in same turn will still work (Skill tool check at lines 508-518 is correct)
- **Constraints?**: Performance improvement (fewer transcript iterations), no new dependencies

---

## Confidence

**Confidence**: 85% — Root cause identified at specific line numbers (521-535), fix is straightforward removal of buggy code. Current `user_message` parsing already correctly handles slash command intent.

**Evidence basis:**
- Codebase analysis: `PreToolUse_skill_pattern_gate.py:521-535` read and analyzed
- Memory entries: `feedback_skill_first_slash_commands.md`, `hook_architecture.md`
- User feedback: Multiple "SLASH COMMAND IGNORED" blocks for `/arch` after `/pre-mortem`
- Test coverage: Existing `test_stateless_skill_first_gate.py` will catch regressions

---

## Adversarial Self-Review

**Weakest assumption**: That removing historical context check won't break legitimate use cases where Skill tool was used earlier in current response.

**If wrong**: Multi-tool responses might be blocked incorrectly.

**Mitigation**: Lines 508-518 already check if Skill tool matches slash command in current tool call, which covers the primary use case. Historical check was meant to handle "Skill used earlier in response" edge case, but this doesn't apply because PreToolUse runs before each tool sequentially.
