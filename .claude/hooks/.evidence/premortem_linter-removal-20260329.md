# Pre-Mortem: Linter Hook Removal (v2 — Post-Adversarial Review)

**Date:** 2026-03-29
**Target:** Linter hook removal — disabling automatic ruff/mypy that stripped TF-IDF code during sequential edits
**Analysis conducted by:** Claude Code (solo dev)
**Adversarial Review:** 8 agents completed — compliance, logic, performance, security, testing, quality, critic, QA

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• CRIT-001 | Wrong hook was targeted for removal (Risk 9)
  [causes: CRIT-002]
  • PreToolUse_auto_format.py is advisory-only — does NOT run ruff --fix
  • Actual code-stripping hook: lint_hook.py:32 (`ruff check --fix`) — still registered
  • PreToolUse_auto_format.py was removed for the wrong reason
  • Evidence: `lint_hook.py:32` vs `PreToolUse_auto_format.py:8-11` (no ruff invocation)

• CRIT-002 | lint_hook.py still in dispatch chain — only flag-based disable (Risk 9)
  [causes: CRIT-001]
  • `default_enabled=False` is NOT structural — env var `LINT_ROUTER_ENABLED=true` overrides
  • Hook still registered in `posttooluse/__init__.py:148`
  • Env override path: `base.py:56` reads `os.environ.get(self.env_var, str(default_enabled))`
  • Evidence: `lint_hook.py:26-27` + `base.py:50-57`

• CRIT-003 | Dead hook files remain on disk (Risk 8)
  • `PreToolUse_auto_format.py` and `PreToolUse_mypy_type_check.py` NOT deleted
  • Only commented out of dispatch — files still exist at 4595 and 5952 bytes
  • Future edit could uncomment and re-enable
  • Violates CLAUDE.md "Hook Edit Verification" — dead files create false editing targets
  • Evidence: Glob confirms files still exist

• CRIT-004 | Orphaned test file imports deleted module (Risk 9)
  • `tests/test_code_quality_checks.py:17` imports `PostToolWrite_code_quality` (deleted)
  • Test will fail on import — creates false negative in test suite
  • Evidence: `adversarial-qa:QA-002`

## 🟠 HIGH-RISK BEHAVIOR

• RISK-005 | No integration test for sequential-edit linter race (Risk 9)
  [causes: CRIT-001, CRIT-002]
  • T-005 prevention action listed but never implemented
  • No test verifies Edit/Write doesn't trigger ruff between sequential edits
  • Env var override not tested
  • Evidence: `adversarial-testing:TEST-001, TEST-003, TEST-004`

• RISK-006 | Kill criteria doesn't match failure mode (Risk 8)
  • Rollback trigger: "If removal breaks syntax validation"
  • Actual failure: ruff --fix strips TF-IDF code WITHOUT breaking syntax
  • pytest passes while code is silently corrupted
  • Evidence: `adversarial-logic:LOGIC-002`

• RISK-007 | ~30% reversion rate is unverified estimate (Risk 6)
  • Presented as "estimated from prior incidents" — no citation
  • Tier 4 evidence per CLAUDE.md Evidence Tiers
  • Evidence: `adversarial-critic:BIAS-3`

• RISK-008 | T-002 listed but not risk-rated (Risk 6)
  • "Hook files on disk — could be re-registered" in Step 2, missing from Step 4 risk table
  • Evidence: `adversarial-critic:CONTRADICTION-1`

**Dependency annotations:**
- `[causes]` → CRIT-001 directly creates CRIT-002 (wrong hook targeted → actual risk remains)
- `[caused-by]` → CRIT-002 caused by CRIT-001 (misdiagnosis led to incomplete fix)

---

## 🧠 BLIND SPOTS & CONTRADICTIONS

• **BLIND SPOT 1** | No verification TF-IDF corruption was actually caused by linters
  • Pre-mortem assumes causation without git history evidence
  • Could be misdiagnosis — ruff may have been correctly identifying unused imports
  • Evidence: `adversarial-critic:BLIND SPOT 1` (70% confidence)

• **BLIND SPOT 2** | Confirmation bias — analysis done AFTER decision to remove
  • All risks framed as "how removal could fail" not "should we remove at all"
  • No alternatives considered (configure ruff --extend-ignore? use advisory-only mode?)
  • Evidence: `adversarial-critic:BIAS-2` (85% confidence)

• **CONTRADICTION** | Cascade severity vs risk rating misalignment
  • T-003 labeled "CRIT-CASCADE" in Step 2.5 but scores only 6 in Step 4
  • Evidence: `adversarial-critic:CONTRADICTION-2`

---

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Run `grep -r "LINT_ROUTER_ENABLED" P:/.claude/settings.json` — should NOT be present or set to "false"
• [ ] Run `grep -r "PreToolUse_auto_format\|PreToolUse_mypy_type_check" P:/.claude/hooks/PreToolUse.py` — should show only comments
• [ ] Verify `tests/test_code_quality_checks.py` no longer exists or no longer imports deleted module

**Cadence**
• [ ] Before any hook modification: verify dispatch chain state
• [ ] After compaction: re-run dispatch chain verification

---

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

| File | Agent | Key Finding |
|------|-------|-------------|
| `premortem_linter-removal-20260329.md` | adversarial-compliance | COMP-001: Wrong hook targeted |
| `premortem_linter-removal-20260329.md` | adversarial-security | SEC-001: Env var override |
| `premortem_linter-removal-20260329.md` | adversarial-quality | QUAL-002: Dead files not deleted |
| `premortem_linter-removal-20260329.md` | adversarial-testing | TEST-001/003/004: No integration tests |
| `premortem_linter-removal-20260329.md` | adversarial-logic | LOGIC-001/002: Kill criteria mismatch |
| `premortem_linter-removal-20260329.md` | adversarial-qa | QA-001/002/006: Orphaned test, no acceptance criteria |
| `premortem_linter-removal-20260329.md` | adversarial-critic | Multiple contradictions and blind spots |
| `premortem_linter-removal-20260329.md` | adversarial-performance | PERF-001: No performance analysis (informational) |

---

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format (v5.0)**

N – Capture lessons and patterns (automatic)
  Na: Auto-invoke `/learn` — Capture failure patterns to CKS
  Nb: Auto-invoke `/reflect pre-mortem` — Document lessons from this analysis

1 (STRUCTURAL FIX) — Delete dead hook files and fully disable lint_hook.py
  → COMP-001 → Evidence: `adversarial-compliance:COMP-001:1-60` (PreToolUse_auto_format.py has no ruff)
  → COMP-002 → Evidence: `adversarial-security:SEC-001:26-27` (default_enabled=False overridable)
  → COMP-003 → Evidence: `adversarial-compliance:COMP-003` (files still on disk, violate CLAUDE.md)
  Actions:
    1. `rm P:/.claude/hooks/PreToolUse_auto_format.py` (was never the culprit — advisory only)
    2. `rm P:/.claude/hooks/PreToolUse_mypy_type_check.py` (removed from dispatch but file remains)
    3. In `posttooluse/__init__.py`: comment out or delete `registry.register("lint", LintHook())` at line 148 — make removal structural

2 (ORphaned test) — Fix or delete broken test file
  → QA-002 → Evidence: `adversarial-qa:QA-002` (test imports deleted module)
  Action: `rm P:/.claude/hooks/tests/test_code_quality_checks.py` or convert to test lint_hook disabled state

3 (VERIFICATION) — Add integration test for sequential-edit linter prevention
  → TEST-001/003/004 → Evidence: `adversarial-testing:TEST-001:line 178` (T-005 prevention unimplemented)
  → SEC-001 → Evidence: `adversarial-security:SEC-001:26-27` (env var override path)
  Action: Create `tests/test_linter_hooks_disabled.py` that:
    1. Performs sequential Edit operations
    2. Verifies no ruff/mypy subprocess is spawned between edits
    3. Explicitly tests that `LINT_ROUTER_ENABLED=true` does NOT re-enable hook

4 (KILL CRITERIA) — Fix kill criteria to match actual failure mode
  → LOGIC-002 → Evidence: `adversarial-logic:LOGIC-002` (ruff strips code without breaking syntax)
  Action: Change kill criteria from "syntax validation breaks" to "pytest fails on TF-IDF tests OR grep TF-IDF reveals missing code"

5 (DOCUMENTATION) — Document removal in hooks/CLAUDE.md Systemic Issues
  → QUAL-005 → Evidence: `adversarial-quality:QUAL-005:line 571` (comments only, no ADR)
  → COMP-004 → Evidence: `adversarial-compliance:COMP-004` (no root cause analysis)
  Action: Add entry to Systemic Issues section explaining WHY lint hooks were removed

0 - Do ALL Recommended Next Steps
