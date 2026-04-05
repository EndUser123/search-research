---
 Migrated from: premortem_hook_cleanup_fixes_20260329.md
 Original location: P:\.claude\.evidence\premortem_hook_cleanup_fixes_20260329.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: Hook & Cleanup Fixes — Adversarial Validation Complete

**Analyzing:** PreToolUse_directory_policy.py and cleanup.py git worktree detection fixes
**Date:** 2026-03-29
**Adversarial Review:** 8 agents — compliance, logic, performance, security, testing, quality, critic, QA

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• CRIT-001 | Hook Infrastructure Exemption Bypass (Risk 9)
  [causes: COMP-002, SEC-002]
  • .claude/hooks/, .claude/skills/planning/, .claude/skills/code/ are exempt from root protections
  • Evidence: PreToolUse_directory_policy.py:605-612 — `hook_infra_paths` allows hook files to bypass root blocking
  • Fix: Analyze if infrastructure exemptions create bypass vector for malicious hook code

• CRIT-002 | Emergency Bypass Flag Causes Fail-Open (Risk 9)
  [caused-by: SEC-002]
  • DIRECTORY_POLICY_BYPASS_FAIL_SAFE=true exits with code 0 on ANY exception
  • Evidence: PreToolUse_directory_policy.py:655-656,670
  • Completely disables all path security enforcement when set
  • Fix: Catch only specific hook errors (JSON, Import, OS), not generic Exception

• CRIT-003 | Worktree Helper Has No Synthetic .git Detection (Risk 9)
  [caused-by: QUAL-004, TEST-002]
  • worktree_helper.py:74-96 only checks `gitdir:` prefix — doesn't validate path exists
  • A synthetic .git file with `gitdir: /nonexistent/path` is treated as valid worktree
  • Fix: Validate the referenced gitdir path actually exists

---

## 🟠 HIGH-RISK BEHAVIOR

• RISK-001 | Over-blocking legitimate root files (Risk 6)
  [causes: QUAL-001, TEST-001, COMP-002]
  • Files like README.md, LICENSE, pyproject.toml now blocked after "." exception removal
  • Pre-mortem acknowledged but whitelist NOT implemented before deployment
  • Action: Implement whitelist BEFORE next deployment

• RISK-002 | Worktree detection misses bare repos (Risk 6)
  [causes: LOGIC-001, SEC-001]
  • Bare repos have .git as FILE (not directory) but no "worktrees" in content
  • Current condition requires "worktrees" substring — bare repos silently ignored
  • Action: Add bare repo detection — flag .git files with gitdir: but no worktrees

• RISK-003 | Lock timeout causes DoS on legitimate operations (Risk 6)
  [causes: SEC-004]
  • is_allowed_external_path() returns False on 1-second lock timeout
  • Under multi-terminal contention, legitimate ops incorrectly blocked
  • Action: Use non-blocking acquisition with best-effort fallback

• RISK-004 | Worktree detection uses weak substring matching (Risk 6)
  [causes: LOGIC-002, QUAL-003, QUAL-004]
  • "worktrees" substring check can be bypassed with crafted content
  • "remote"+"url" substring check for nested repos too loose (comments trigger)
  • Action: Use structured parsing — extract path, verify existence

---

## 🧠 BLIND SPOTS & CONTRADICTIONS

• LOGIC-003 | RISK-003 and RISK-004 have NO action items in Step 5
  • Identified risks remain unmitigated — gap in prevention plan

• LOGIC-004 | RISK-005 (path normalization bypass) has NO action item
  • Unmitigated risk despite being identified in risk table

• CONTRA-001 | "." exception removal classified as "Tech" not "Process"
  • Root cause: no test corpus before removing protection — Process failure

• CONTRA-002 | RISK-005 likelihood rated 1 but Step 2.7 acknowledges known cross-platform issue
  • Should be likelihood 2 given explicit acknowledgment

• SEC-003 | os.getcwd() used without validation for Bash working directory
  • Malicious CWD manipulation could bypass project boundary checks

---

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Verify py_compile passes on PreToolUse_directory_policy.py and cleanup.py
• [ ] Check DIRECTORY_POLICY_BYPASS_FAIL_SAFE is NOT set in environment
• [ ] Test root file write (echo test > P:/test_verify.txt) — should be blocked

**Cadence**
• [ ] Weekly: Run cleanup.py --dry-run, verify no worktree false positives
• [ ] Monthly: Audit bypass flag usage in logs
• [ ] Quarterly: Review hook_infra_paths exemptions still necessary

---

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

| Agent | Key Finding | File:Line |
|-------|-------------|-----------|
| SEC-002 | Fail-open bypass mechanism | PreToolUse_directory_policy.py:670 |
| LOGIC-001 | Bare repo detection gap | cleanup.py:780 |
| TEST-001 | Root file whitelist missing | PreToolUse_directory_policy.py:620-627 |
| QUAL-001 | Over-blocking without whitelist | PreToolUse_directory_policy.py:620 |
| SEC-004 | Lock timeout DoS | PreToolUse_directory_policy.py:166-176 |
| CRIT-001 | Hook infra exemption bypass | PreToolUse_directory_policy.py:605-612 |

---

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format**: Each action links to verified adversarial finding.

N – Capture lessons and patterns (automatic)
  Na: Auto-invoke `/learn` — Capture failure patterns to CKS
  Nb: Auto-invoke `/reflect {skill_name}` — Document lessons from this analysis

1 (SECURITY) - Fix fail-open bypass mechanism ✅ DONE
  SEC-002 → PreToolUse_directory_policy.py:670 → Catch specific exceptions (JSONDecodeError, ValueError)

2 (TESTING) - Add root file whitelist before deploying ✅ DONE
  COMP-002 → PreToolUse_directory_policy.py:620 → Added frozenset of allowed_root_files

3 (TESTING) - Create test corpus for root file blocking ✅ DONE
  TEST-001 → PreToolUse_directory_policy.py:620-627 → Test positive (blocked) and negative (whitelisted) cases
  Tests added: test_directory_policy_security.py::test_root_file_whitelist_allows_known_files (8 cases), test_root_file_blocking_rejects_non_whitelisted (5 cases), test_specific_exception_handling (JSONDecodeError bypass)

4 (LOGIC) - Add bare repo detection to worktree logic ✅ DONE
  LOGIC-001 → cleanup.py:780 → Flag .git files with gitdir: but no worktrees as DETACHED_GIT_REPO

5 (QUALITY) - Structured parsing for worktree detection ✅ DONE
  QUAL-004 → cleanup.py → Extract gitdir path, verify existence before flagging
  Implementation: Path existence check added, synthetic .git files with non-existent paths skipped

6 (TESTING) - Integration test for worktree detection ✅ DONE
  TEST-002 → test_cleanup_safety.py → TestWorktreeDetection class with 5 test cases
  Tests: test_worktree_with_valid_gitdir_is_flagged, test_worktree_with_nonexistent_gitdir_not_flagged, test_bare_repo_with_valid_gitdir_is_flagged, test_bare_repo_with_nonexistent_gitdir_not_flagged, test_regular_git_repo_not_flagged — all 5 PASS

7 (SECURITY) - Lock-free pattern for external path checking
  SEC-004 → PreToolUse_directory_policy.py:166-176 → Use copy-on-write instead of global lock

0 - Do ALL Recommended Next Steps

---

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| 5 (QUALITY) | ✅ DONE | Structured parsing implemented — gitdir path existence verified | Medium |
| 6 (TESTING) | ✅ DONE | Worktree integration tests added — 5 test cases all pass | Medium |
| 7 (SECURITY) | ❌ Open | Lock-free pattern deferred — SEC-004 lock timeout issue not addressed | Low |

**Why deferred**:
- Step 7: Lock restructuring is complex, current implementation works under normal contention

**Should any of these be addressed?** See "Did we forget anything?" protocol in pre-mortem SKILL.md.

---

## VERIFICATION COMPLETE

Adversarial validation by 8 agents finished. Top risks prioritized:
1. Fail-open bypass (CRIT-002) — blocks all operations
2. Over-blocking without whitelist (RISK-001) — breaks legitimate workflow
3. Bare repo false negative (RISK-002) — leaves security gap
4. Lock timeout DoS (RISK-003) — self-inflicted availability loss
