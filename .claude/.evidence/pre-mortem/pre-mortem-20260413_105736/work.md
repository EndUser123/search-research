# GTO Improvement Plan — Pre-Mortem Review

## Work Under Review: GTO Retro Action Items

Three systemic improvements identified in GTO retro SELF-CONTRAST:

### 1. Staleness Check Fix (HIGH — CAUSE-001)
**File:** `skill_coverage_detector.py:631`
**Issue:** Uses `entries[0]` (OLDEST timestamp) instead of `entries[-1]` (MOST RECENT) for git freshness check
**Fix:** Sort entries by timestamp, then use `entries[-1]` for freshness check
**Why it matters:** Currently flags skills as stale even when they were run after the last file change

### 2. Replace Manual stdlib Frozenset (HIGH — QUAL-001)
**File:** `skill_registry_bridge.py`
**Issue:** 88-entry manual frozenset `_PYTHON_STDLIB_MODULES` 
**Fix:** Replace with `importlib.stdlib_module_names` (available in Python 3.10+)
**Why it matters:** Eliminates maintenance burden, ensures completeness

### 3. Justify Arbitrary Thresholds (MEDIUM — QUAL-003, QUAL-013)
**File:** `gto_self_health_detector.py`, `session_chain_analyzer.py`
**Issues:**
- Health thresholds 0.20/0.40/0.50 with no justification
- MAX_CHAIN_DEPTH=10 without rationale
**Fix:** Add docstrings explaining derivation, or make configurable via environment variable

---

## Files to Examine

- `P:/.claude/skills/gto/__lib/skill_coverage_detector.py` — staleness check at line 631
- `P:/.claude/skills/gto/__lib/skill_registry_bridge.py` — stdlib frozenset at lines 73-79
- `P:/.claude/skills/gto/__lib/gto_self_health_detector.py` — arbitrary health thresholds
- `P:/.claude/skills/gto/__lib/session_chain_analyzer.py` — MAX_CHAIN_DEPTH=10

---

## Review Focus

For each fix, assess:
1. What failure mode still exists even if the happy path passes?
2. What hidden assumption would break under stale data or multi-terminal use?
3. What edge case could cause the fix to produce wrong results?
4. Does the fix reduce one failure mode but create another?
