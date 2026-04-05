# Pre-Mortem Compact Snapshot: ADR-20260321 Stale State File Cleanup

**Analysis Date**: 2026-03-22
**Target**: ADR-20260321-stale-state-file-cleanup.md
**Status**: ABANDON - Problem already solved by existing implementation

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• **ADR-001 | Wrong Target File** (Risk 9)
  • ADR references `StopHook_negative_existence_guard.py` (lines 105, 130) but actual file is `Stop_negative_existence_guard.py`
  • Evidence: ADR-20260321-stale-state-file-cleanup.md:130, P:\.claude\hooks\Stop_negative_existence_guard.py exists

• **ADR-002 | Implementation Already Exists** (Risk 9)
  • `SessionStart_verification_cleanup.py` already implements cleanup with 24-hour TTL (lines 60-85)
  • ADR proposes 30-day TTL, making it redundant and less aggressive
  • Evidence: P:\.claude\hooks\SessionStart_verification_cleanup.py:60-85

• **ADR-003 | Dead Coordination Path** (Risk 7)
  • Stop hook checks for decision=='allow' but PreToolUse_file_existence_guard.py only writes 'allow_new', 'deny', or 'allow_with_justification'
  • The coordination path never executes - dead code
  • Evidence: P:\.claude\hooks\Stop_negative_existence_guard.py:267, P:\.claude\hooks\PreToolUse_file_existence_guard.py:183/207/222

• **ADR-004 | State Files Lack Terminal Scope** (Risk 6)
  • State files use `{session_id}` naming, not `{terminal_id}_{session_id}`
  • Cross-terminal contamination possible when same session_id used across terminals
  • Evidence: P:\.claude\hooks\state\ file naming pattern, ADR-20260321-handoff-post-restore-directive.md:39-47

---

## 🟠 HIGH-RISK BEHAVIOR

• **ADR-005 | Unnecessary Implementation** (Risk 6)
  • Creating validate_state_file() when cleanup already exists in SessionStart hook
  • Duplicates existing functionality, violating "discovery before implementation" principle

• **ADR-006 | Multi-Terminal TOCTOU Vulnerability** (Risk 6)
  • Path.exists() check followed by unlink() creates time-of-check/time-of-use window
  • Two terminals can both see file exists, then both attempt unlink → race condition
  • Evidence: ADR-20260321-stale-state-file-cleanup.md:159-161

• **ADR-007 | No Backup Before Deletion** (Risk 6)
  • State files deleted without backup copy
  • False positive deletion causes permanent data loss
  • Evidence: ADR-20260321-stale-state-file-cleanup.md:160 (unlink without backup)

---

## 🧠 BLIND SPOTS & CONTRADICTIONS

• **Existing Solution Not Discovered**: ADR was created without searching for existing cleanup implementations. `SessionStart_verification_cleanup.py` already solves this problem with more aggressive TTL (24 hours vs 30 days).

• **Constitutional Violation - Multi-Terminal Safety**: State files lack terminal_id scope, violating terminal isolation principle. ADR does not address this gap.

• **Success Theater Indicators**: ADR claims "<10ms per hook" without profiling, "Multi-terminal safe" without concurrent access tests, "All tests pass" without pytest output.

• **Architecture Decision Redundancy**: Creating an ADR for functionality that already exists upstream. The correct action is to document existing solution, not create new implementation.

---

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Verify existing SessionStart cleanup is working: `ls P:\.claude\hooks\state\file_existence_decision_*.json`
• [ ] Check if validate_checklist.py error still occurs after existing cleanup runs
• [ ] Verify state files have proper terminal_id scope

**Cadence**
• [ ] Monitor state directory for orphaned files accumulating (should be cleaned by SessionStart hook within 24 hours)
• [ ] Watch for "allow_new" messages dominating logs (indicates existing cleanup working correctly)

---

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

Detailed findings stored in:
• `P:\.claude\.evidence\premortem_stale_state_cleanup_analysis.md` - Full 7-step pre-mortem analysis
• `P:\.claude\arch_decisions\ADR-20260321-stale-state-file-cleanup.md` - Original ADR (abandoned)
• `P:\.claude\hooks\SessionStart_verification_cleanup.py` - Existing solution (lines 60-85)
• `P:\.claude\hooks\Stop_negative_existence_guard.py` - Actual hook file (note: NOT StopHook_ variant)
• `P:\.claude\hooks\PreToolUse_file_existence_guard.py` - State file writer (dead coordination path)

---

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format**: Each action links to verified finding with evidence.

**1 - ABANDON ADR-20260321-stale-state-file-cleanup.md**
  1a: Mark ADR as "Superseded by existing implementation" → Manual - Evidence (ADR-002: SessionStart_verification_cleanup.py:60-85 already solves problem)
  1b: Document existing solution → Use `/arch "document the existing SessionStart cleanup mechanism"` or Manual - Evidence (ADR-002: 24-hour TTL cleanup already operational)

**2 - VERIFY EXISTING CLEANUP IS WORKING**
  2a: Check state directory age → Manual - `ls -la P:\.claude\hooks\state\file_existence_decision_*.json` - Evidence (ADR-002: SessionStart cleanup should remove files older than 24 hours)
  2b: Verify validate_checklist.py error is resolved → Manual - Run hook execution and check logs - Evidence (ADR-001: Original error was from stale state file that existing cleanup should remove)

**3 - FIX DEAD COORDINATION PATH**
  3a: Update Stop hook to check 'allow_new' instead of 'allow' → Manual - Evidence (ADR-003: Stop_negative_existence_guard.py:267 checks 'allow' but writer never writes it)
  3b: Or remove dead code path entirely → Manual - Evidence (ADR-003: Coordination path never executes due to mismatch)

**4 - ADDRESS MULTI-TERMINAL SCOPE GAP**
  4a: Add terminal_id to state file naming → Use `/code-python-2025` - Evidence (ADR-004: State files lack terminal_id scope, violating terminal isolation)
  4b: Reference ADR-20260321-handoff-post-restore-directive.md:39-47 for pattern → Manual - Evidence (ADR-004: Handoff ADR shows correct terminal-scoped state file pattern)

**5 - CAPTURE LESSONS**
  5a: Extract "discovery before implementation" lesson → Use `/learn` - Capture pattern: Always search for existing solutions before creating ADRs
  5b: Reflect on ADR creation process → Use `/reflect pre-mortem` - What caused this ADR to be created without discovering existing solution?

**0 - Do ALL Recommended Next Steps**
