# Pre-Mortem: Directory Policy Relative Path Fix - Final Report

**Date**: 2026-03-23
**Target**: PreToolUse_directory_policy.py relative path detection fix
**Status**: COMPLETE with adversarial validation

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• **SEC-001** | Path traversal via string concatenation (Risk 9)
  [causes: TEST-002]
  • Line 246: `f"{working_dir}/{path}"` - no validation of `../` sequences
  • **Evidence**: `PreToolUse_directory_policy.py:246` + pre-mortem section 2.5
  • **Action**: Use `Path.resolve()` with boundary check

• **SEC-002** | Access control bypass via Write/Edit tools (Risk 9)
  [causes: COMP-002]
  • Lines 249-251: Write/Edit tools skip path extraction entirely
  • **Evidence**: `PreToolUse_directory_policy.py:249` + pre-mortem section 2.6
  • **Action**: Apply same normalization to all tools

• **LOGIC-001** | Cascade tracing contradiction (Risk 9)
  [causes: RISK-003]
  • Pre-mortem Step 2.5: Command chaining scenario has logical error
  • **Evidence**: `premortem_directory_policy_fix.md:77-82`
  • **Action**: Fix cascade description to match actual failure mode

• **TEST-004** | Existing test suite broken (Risk 9)
  [causes: All path validation tests]
  • test_extract_paths_from_bash.py fails with import error
  • **Evidence**: pytest shows `ModuleNotFoundError: __lib.hook_base`
  • **Action**: Fix sys.path manipulation in test file

• **COMP-004** | Terminal isolation not implemented (Risk 9)
  [causes: RISK-002, working_dir contamination]
  • working_dir uses os.getcwd() without terminal_id scoping
  • **Evidence**: `PreToolUse_directory_policy.py:219` + CLAUDE.md concurrency principle
  • **Action**: Use tool_input['cwd'] instead of os.getcwd()

## 🟠 HIGH-RISK BEHAVIOR

• **RISK-001** | Pattern false positives (Risk 9)
  [causes: TEST-001, QUAL-001]
  • 19 regex patterns match command flags as file paths
  • **Evidence**: Lines 112-115, no negative tests in test suite
  • **Action**: Create test corpus with 100+ real commands, add negative test cases

• **RISK-002** | Working directory mismatch (Risk 9)
  [causes: COMP-004, TEST-002, QUAL-004]
  • os.getcwd() returns worktree path, not P:/, causing false blocks
  • **Evidence**: Line 219, pre-mortem section 2.5
  • **Action**: Add worktree detection, use CLAUDE_PROJECT_DIR fallback

• **SEC-003** | Command injection via regex patterns (Risk 8)
  [causes: QUAL-001]
  • Pattern `[^/\s"';&|]+` doesn't validate for shell metacharacters
  • **Evidence**: Line 112, pre-mortem section 1.5
  • **Action**: Add `is_safe_path_component()` validator

## 🧠 BLIND SPOTS & CONTRADICTIONS

• **BLIND-SPOT-001** | Terminal ID propagation not analyzed
  • Pre-mortem identifies "Terminal ID not propagated" but doesn't analyze working_dir state keying
  • **Evidence**: adversarial-critic meta-analysis
  • **Confidence**: 85% (Tier 3 - Static analysis)

• **BLIND-SPOT-002** | Hook ordering dependencies not analyzed
  • No analysis of which hooks should run before/after directory_policy
  • **Evidence**: adversarial-critic meta-analysis
  • **Confidence**: 75% (Tier 3 - Logical derivation)

• **BLIND-SPOT-003** | TDD constitutional violation
  • Test corpus treated as Step 5 (prevention), not Step 0 (prerequisite)
  • **Evidence**: adversarial-critic + CLAUDE.md TDD requirement
  • **Confidence**: 95% (Tier 2 - Constitutional reference)

• **CONTRADICTION-001** | Kill criteria vs. "fail fast" principle
  • "If >3 false positive reports" violates "fail fast" (should be 1)
  • **Evidence**: Kill criteria line 25 vs CLAUDE.md principle
  • **Confidence**: 90% (Tier 2 - Policy conflict)

• **CONTRADICTION-002** | Performance budget without baseline
  • 100ms threshold set but current latency never measured
  • **Evidence**: Kill criteria line 25 vs Step 3.8
  • **Confidence**: 95% (Tier 1 - Logical contradiction)

• **CONTRADICTION-003** | TDD order violated
  • Pre-mortem Step 5 lists test corpus as prevention, not prerequisite
  • **Evidence**: Step 5.1 vs CLAUDE.md TDD requirement
  • **Confidence**: 95% (Tier 2 - Constitutional requirement)

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run (before committing hook changes)**
- [ ] Run `pytest tests/test_extract_paths_from_bash.py` (currently broken - fix first)
- [ ] Test with 100-command corpus from real user sessions
- [ ] Verify worktree scenarios don't false block
- [ ] Benchmark latency (must be <100ms per command)

**Cadence (weekly monitoring)**
- [ ] Check for false positive reports in user feedback
- [ ] Verify test coverage remains >80%
- [ ] Monitor for new files appearing at P:/ root (indicates fix not working)

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

Detailed adversarial agent findings stored in `.evidence/`:
- `premortem_directory_policy_fix.md` - Initial pre-mortem analysis
- `adversarial_compliance.json` - Compliance violations
- `adversarial_logic.json` - Logic errors and contradictions
- `adversarial_performance.json` - Performance benchmarks
- `adversarial_security.json` - Security vulnerabilities
- `adversarial_testing.json` - Testing gaps
- `adversarial_quality.json` - Quality issues
- `adversarial_critic.json` - Meta-analysis
- `adversarial_qa.json` - QA findings

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format**: Each action links to verified adversarial finding with evidence.

**1 (SECURITY)** - Fix CRITICAL security vulnerabilities
  1a: Fix path traversal → Use Path.resolve() with boundary check - Evidence (SEC-001: PreToolUse_directory_policy.py:246)
  1b: Fix Write/Edit bypass → Apply path normalization to all tools - Evidence (SEC-002: PreToolUse_directory_policy.py:249)
  1c: Add command injection validator → Implement is_safe_path_component() - Evidence (SEC-003: PreToolUse_directory_policy.py:112)

**2 (CONCURRENCY)** - Fix terminal isolation violation
  2a: Use tool_input['cwd'] instead of os.getcwd() - Evidence (COMP-004: PreToolUse_directory_policy.py:219)
  2b: Add worktree detection logic - Evidence (QUAL-004: PreToolUse_directory_policy.py:217-222)

**3 (TESTING)** - Fix broken test suite
  3a: Fix import error in test_extract_paths_from_bash.py - Evidence (TEST-004: tests/test_extract_paths_from_bash.py:11)
  3b: Add tests for 4 new relative path patterns - Evidence (TEST-001: PreToolUse_directory_policy.py:112-115)
  3c: Add worktree scenario tests with mocked cwd - Evidence (TEST-002: pre-mortem section 2.5)
  3d: Add concurrent access tests - Evidence (TEST-003: pre-mortem Step 0)

**4 (CONSTITUTIONAL)** - Fix arbitrary thresholds
  4a: Remove arbitrary kill criteria (>2 hours, >3 reports, >100ms) - Evidence (COMP-001: premortem line 23)
  4b: Replace with evidence-based criteria from actual measurements - Evidence (COMP-001: CLAUDE.md principle)

**5 (CONSTITUTIONAL)** - Fix TDD order violation
  5a: Create test corpus FIRST before any pattern changes - Evidence (BLIND-SPOT-003: CLAUDE.md TDD requirement)
  5b: Verify baseline failures before implementing fixes - Evidence (CONTRADICTION-003: Step 5.1)

**6 (DOCUMENTATION)** - Fix pre-mortem logic errors
  6a: Fix RISK-003 cascade tracing contradiction - Evidence (LOGIC-001: pre-mortem lines 77-82)
  6b: Remove unverified base rates (60%, 40% claims) - Evidence (LOGIC-006: pre-mortem line 113)

**7 (LEARNING)** - Capture lessons to CKS
  7a: Extract lessons → Use `/learn` - Capture regex false positive patterns, terminal isolation patterns
  7b: Reflect on corrections → Use `/reflect pre-mortem` - Document arbitrary threshold avoidance, TDD-first principle

**0** - Execute ALL recommended next steps (1-7) in order

---

## Evidence-Based Confidence Calibration

| Risk Category | Pre-Mortem Confidence | Meta-Analysis Confidence | Final Assessment |
|---------------|----------------------|--------------------------|-----------------|
| Pattern False Positives | 9/9 | 7/9 | **7/9** (High-Medium) |
| Working Directory Mismatch | 9/9 | 6/9 | **6/9** (Medium) |
| Command Chaining | 6/9 | 6/9 | **6/9** (Medium) |
| Performance Regression | 4/9 | 2/9 (INFO) | **2/9** (Low - MITIGATED) |
| Terminal Isolation | Not scored | 7/9 | **7/9** (High-Medium) |
| TDD Compliance | Not scored | 9/9 | **9/9** (High - VIOLATION) |

**Key Insight**: Adversarial validation downgraded 3 risks and identified 3 critical blind spots not in original pre-mortem. Performance concerns (RISK-004) were UNFOUNDED - benchmark proves 0.068ms overhead (1470× under threshold).

---

## Success Criteria Verification

- ✅ 10+ failure modes identified (12 original + 3 from adversarial)
- ✅ Fix side effects analyzed (Step 1.5 complete)
- ✅ Adversarially validated (8-agent multi-perspective analysis)
- ✅ Cascade depth traced (all risks ≥6 have 3-step minimum)
- ✅ AI/LLM risks checked (Step 2.6 complete)
- ✅ Success theater detected (Step 3.6 complete)
- ✅ Operationally verified (PERF-001 proves performance acceptable)
- ✅ Kill criteria defined (Step 0.7 complete - needs revision for arbitrariness)
- ✅ Dependency cascades mapped (Step 4.5 - RISK-001 causes RISK-004)
- ✅ Top priorities mapped to actions (7 domains, 15 specific actions)

**Overall Assessment**: Pre-mortem framework successfully identified major risks, but adversarial validation revealed critical gaps (terminal isolation, TDD violation) and corrected overestimates (performance). Fix requires security hardening before deployment.
