# Intent/Goal System Audit (T-016)

**Date:** 2026-02-25
**Scope:** Contract system optimization v6.0 - Change E
**Status:** Complete

## Summary

Audit of all intent/goal tracking files in the codebase. Found **4 actively wired systems** and **3 dormant/deprecated systems**.

## Actively Wired Systems

### 1. Command Intent Validation Gate
**File:** `PreToolUse_command_intent_gate.py`
**Status:** ✅ ACTIVE
**Registration:** Registered in `PreToolUse.py`
**Purpose:** Validates that bash commands match user intent when executing slash commands
**Architecture:**
- State file: `P:/.claude/hooks/state/pending_command_intent_{session_id}.json`
- Stores: `{skill, prompt}` when slash command detected
- TTL: 5 minutes, auto-cleanup
- Used by: UserPromptSubmit_router.py (sets), PreToolUse_command_intent_gate.py (consumes)

**Example Problem Solved:**
```
User says: /ask-cli4 "review the plan"
Claude executes: python ask_cli.py "..." --qwen-only  ← BLOCKED
```

### 2. Narrative Intent Detector
**File:** `narrative_intent_detector.py`
**Status:** ✅ ACTIVE
**Registration:** Imported in `Stop.py`
**Purpose:** Detects un-hedged design-intent/author-motivation narratives presented as fact
**Scope:** Rationale claims ("The author included X because...") requiring evidence or hedging
**Phase:** Warn-only (Phase 1)
**Used by:** Stop hook (PostToolUse)

**Pattern Examples:**
- ✅ Checks: "The author added this because users forget"
- ✗ Skips: "This function crashes because it mutates state" (code reasoning)

### 3. Intent Drift Scanner
**File:** `scanners/intent_drift_scanner.py`
**Status:** ✅ ACTIVE
**Registration:** Imported in `constitutional_enforcer.py`
**Purpose:** Detects when model actions drift from original user intent
**Features:**
- Computes drift score (0.0 = aligned, 1.0 = drifted)
- Tracks intent trajectory across session
- Warns when drift exceeds threshold (default 0.6)
- State file: `P:/.claude/session_data/intent_state.json`

**Scope Expansion Patterns:**
- "also create/implement/build"
- "additionally, meanwhile, furthermore"
- "while we're at it / since we're here"
- "might as well / could also"
- "let's also / we should also"

### 4. Unified Intent Classifier
**File:** `shared/intent_classifier.py`
**Status:** ⚠️ DORMANT (no active usage)
**Purpose:** Embedding-based semantic classification using sentence-transformers
**Categories:** search, read, write, analyze, research, code, test, git, web, existence_claim, other
**Performance:** Fast (~10ms), local
**Usage:** **NOT actively imported** in current hooks (only in archived code)

## Dormant/Deprecated Systems

### 1. Goal State Files
**Files:**
- `P:/.claude/session_data/goal_state.json`
- `P:/.claude/session_data/intent_state.json`
- Terminal-specific: `terminals/terminal_*/goal_state.json`

**Status:** ⚠️ ORPHANED (files exist but no active readers/writers)
**Content Example:**
```json
{
  "primary_goal": "Respond to user request",
  "goal_scope": "analysis",
  "goal_confidence": 0.5,
  "active_command": "tmp",
  "timestamp": "2026-01-11T01:42:26.325734"
}
```

**Finding:** No active hooks read or write these files. Legacy from earlier goal tracking system.

### 2. Archived Intent Handlers
**Files:** `_archive/intent_handlers.py`, `_archive/intent_utils.py`
**Status:** ❌ DEPRECATED
**Note:** Superseded by narrative_intent_detector.py

### 3. Test Files
**Files:**
- `tests/deprecated/test_intent_classifier.py`
- `tests/test_narrative_intent_detector.py`
- `tests/test_command_intent_gate.py`
- `UserPromptSubmit/tests/test_intent_classification.py`
- `UserPromptSubmit/tests/test_intent_handlers.py`

**Status:** ✅ Tests maintained for active systems

## Integration Points

### Data Flow

```
UserPromptSubmit (router)
    ↓
_store_command_intent() → pending_command_intent_{session_id}.json
    ↓
PreToolUse_command_intent_gate.py (validates bash commands)
    ↓
Stop hook → narrative_intent_detector.py (warns on un-hedged intent claims)
```

### Constitutional Enforcement

```
constitutional_enforcer.py
    ↓
IntentDriftScanner (threshold=0.6)
    ↓
Warns on scope expansion patterns
```

## Recommendations

### Immediate Actions
1. ✅ **No action required** - Active systems are properly wired and documented

### Future Considerations
1. **Unified Intent Classifier** (shared/intent_classifier.py)
   - Status: High-quality implementation, no current usage
   - Options: (a) Integrate for smarter hook routing, (b) Archive as unused
   - Recommendation: Keep dormant (good code, may be useful later)

2. **Goal State Files** (session_data/goal_state.json)
   - Status: Orphaned files
   - Options: (a) Re-implement goal tracking, (b) Clean up files
   - Recommendation: Clean up (no active readers/writers)

## Test Coverage

All active systems have test coverage:
- `test_command_intent_gate.py` ✅
- `test_narrative_intent_detector.py` ✅
- IntentDriftScanner tested via constitutional_enforcer tests ✅

## Appendix: Complete File Inventory

### Active Files (4)
- `PreToolUse_command_intent_gate.py` (✅ wired)
- `narrative_intent_detector.py` (✅ wired)
- `scanners/intent_drift_scanner.py` (✅ wired)
- `shared/intent_classifier.py` (⚠️ dormant)

### State Files (3)
- `session_data/goal_state.json` (⚠️ orphaned)
- `session_data/intent_state.json` (✅ used by IntentDriftScanner)
- `hooks/state/pending_command_intent_*.json` (✅ used by command_intent_gate)

### Archived Files (7)
- `_archive/goal_anchor.py`
- `_archive/goal_anchor_obs.py`
- `_archive/goal_anchor_v4.py`
- `_archive/intent_handlers.py`
- `_archive/intent_utils.py`
- `_archive/PreToolUse_intent_validation_gate.py`
- `_archive/UserPromptSubmit_intent_classifier.py`

### Test Files (5)
- `tests/deprecated/test_intent_classifier.py`
- `tests/test_narrative_intent_detector.py`
- `tests/test_command_intent_gate.py`
- `UserPromptSubmit/tests/test_intent_classification.py`
- `UserPromptSubmit/tests/test_intent_handlers.py`

---

**Next Step:** T-017 - Document findings in CLAUDE.md
