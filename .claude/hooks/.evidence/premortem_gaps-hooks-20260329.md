# Pre-Mortem: Hooks Directory Gap Analysis

**Date:** 2026-03-29
**Target:** Hooks directory systemic gaps (GTO: 653 gaps, 84% health)
**Health Score:** 56% reported / 84% actual (critic calibration)

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**

• **CRIT-SEC-001 | Session state corruption on concurrent writes (Risk 9)**
  [causes: CRIT-SEC-002]
  • `session_manager.py:90` — `save_session_state()` writes JSON without FileLock
  • Multiple terminals write `current_session.json` simultaneously → silent data corruption
  • Evidence: `__lib/session_manager.py:90` — no lock, no atomic write

• **CRIT-SEC-002 | Terminal state isolation fundamentally broken (Risk 9)**
  [caused-by: CRIT-SEC-001, causes: CRIT-LOGIC-001]
  • `skill_guard.skill_execution_state` is phantom import — no package exists
  • All imports silently fail via `try/except ImportError` + `type: ignore`
  • `detect_terminal_id()` returns empty string → state files named `skill_execution_.json`
  • Two terminals overwrite each other's state
  • Evidence: `skill_execution_state.py:86`, `__lib/terminal_detection.py`

• **CRIT-LOGIC-001 | Phantom `skill_guard` imports bypass enforcement silently (Risk 9)**
  [caused-by: CRIT-SEC-002]
  • `from skill_guard.Skill_execution_state import X` — `skill_guard/` does not exist
  • 8+ files use this phantom namespace
  • Hooks silently treat sessions as "no skill loaded" → enforcement bypassed
  • Evidence: `PreToolUse_observe_before_act_gate.py:130`, `skill_execution_state.py:86`

• **CRIT-LOGIC-002 | TOCTOU race in file_lock — proceeds without lock on timeout (Risk 9)**
  [causes: CRIT-SEC-001]
  • `ledger.py:128` — timeout yields `False` instead of raising exception
  • Operations continue WITHOUT lock protection after timeout
  • State ledger entries silently corrupted on concurrent timeout
  • Evidence: `investigation-ledger/ledger.py:128-131` — explicit "proceed without lock" comment

• **CRIT-LOGIC-003 | GTO assertions check wrong directory — A1 ALWAYS fails (Risk 9)**
  [causes: CRIT-QA-001]
  • `gto_assertions.py:63` checks `C:\Users\brsth\.evidence`
  • Actual evidence lives at `P:\.claude\hooks\.evidence`
  • Permanent path mismatch → A1 never passes regardless of artifact state
  • Evidence: `evals/gto_assertions.py:63` — `Path.home() / ".evidence"`

## 🟠 HIGH-RISK BEHAVIOR

• **RISK-001 | 508 of 622 hook modules untested — 81.7% coverage gap (Risk 8)**
  [causes: RISK-002]
  • 508 modules have zero test coverage
  • Critical hooks: `PreToolUse_require_plan_for_features.py`, `StopHook_commitment_tracker.py`, `SessionStart_hook_health_check.py`
  • Evidence: Testing agent analysis — static coverage count

• **RISK-002 | No regression CI pipeline (Risk 6)**
  [caused-by: RISK-001]
  • No `.github/workflows/` — pytest never runs on commits
  • `test_hook_registration.py` only runs manually
  • Evidence: No CI files in repository

• **RISK-003 | 625+ `type: ignore` entries mask real import errors (Risk 7)**
  • `# type: ignore` used to suppress而不是修复 real errors
  • `1704 total occurrences` across 44 files
  • Evidence: `__lib/binary_assertions.py`, multiple hook files

• **RISK-004 | GTO performs 3x sequential rglob scans — 450K line reads (Risk 6)**
  • `gap_finder_subagent.py:320,193,273` — three separate `rglob('*.py')` calls
  • Each scan reads all file contents for regex matching
  • Evidence: `subagents/gap_finder_subagent.py`

• **RISK-005 | GTO state files accumulate without automatic cleanup (Risk 4)**
  • `.evidence/gto-state-{terminal_id}/` dirs created every run, never cleaned
  • `cleanup_state.py` exists but requires manual invocation
  • Evidence: `lib/state_manager.py:98`

• **RISK-006 | Commitment tracker non-atomic rename on Windows (Risk 6)**
  • `commitment_tracker.py:266` uses `Path.replace()` — NOT atomic on Windows
  • Concurrent saves can result in lost commitment data
  • Evidence: `__lib/commitment_tracker.py:266`

• **RISK-007 | Hook edit verification structurally disabled (Risk 6)**
  • `PreToolUse_hook_edit_gate.py` archived to `_archive/`
  • Edits to dead files produce no error, fixes never run
  • Evidence: `PreToolUse.py:562`

• **RISK-008 | GTO assertions time-dependent — 1hr window causes false negatives (Risk 5)**
  • `gto_assertions.py:69` — `if mtime >= time_threshold` excludes files at exact boundary
  • Artifacts older than 60 minutes treated as non-existent
  • Evidence: `evals/gto_assertions.py:69`

## 🧠 BLIND SPOTS & CONTRADICTIONS

• **CRIT mismatch**: Pre-mortem reported 56% health, GTO evidence shows 84% — health score was stale from prior run
• **Gap count inflation**: GTO shows 653 gaps but 583 are "missing docs" in `.archive/` files — not operational risk
• **Test coverage theater**: 337 test files exist but 100 are deprecated in `tests/deprecated/` — inflated coverage perception
• **Confirmation bias**: Pre-mortem analysis was done AFTER linter removal decision — framing confirmed removal

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Run `pytest tests/test_linter_hooks_disabled.py` after any hook registry change
• [ ] Verify GTO artifacts saved to correct path after running GTO

**Cadence**
• [ ] Monthly: Run `cleanup_state.py` to purge old GTO state files
• [ ] Weekly: Check `tests/deprecated/` for test file count growth
• [ ] On CI: Run `python evals/gto_assertions.py --project-root P:\.claude\hooks` with correct `--evidence-dir`

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

- `P:\.claude\hooks\.evidence\premortem_linter-removal-20260329.md` — Prior pre-mortem (linter removal)
- Quality findings: `adversarial-quality` agent (5 HIGH findings)
- Security findings: `adversarial-security` agent (5 findings, 2 CRITICAL)
- Logic findings: `adversarial-logic` agent (4 findings, 3 HIGH/blocker)
- Testing findings: `adversarial-testing` agent (6 findings, 3 HIGH)
- Performance findings: `adversarial-performance` agent (5 findings, 1 CRITICAL)
- QA findings: `adversarial-qa` agent (5 findings, 2 blocker)
- Compliance findings: `adversarial-compliance` agent (8 findings)
- Critic calibration: `adversarial-critic` agent (meta-analysis)

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format (v5.0)**: Each action links to verified adversarial finding.

**N – Capture lessons and patterns (automatic)**
  Na: Auto-invoke `/learn` — Capture multi-terminal state corruption pattern
  Nb: Auto-invoke `/reflect hooks-gap-premortem` — Document gap analysis lessons

**1 (CRIT-SEC) — Fix session state corruption**
  → CRIT-SEC-001 → Evidence: `__lib/session_manager.py:90` → Wrap `save_session_state()` with FileLock + atomic write (temp file + replace)

**2 (CRIT-LOGIC) — Fix phantom `skill_guard` imports**
  → CRIT-LOGIC-001 → Evidence: `skill_execution_state.py:86` → Replace `from skill_guard.X` with correct relative imports `from skill_execution_state import ...`

**3 (CRIT-LOGIC) — Fix TOCTOU race in file_lock**
  → CRIT-LOGIC-002 → Evidence: `investigation-ledger/ledger.py:128` → Raise TimeoutError instead of yielding False on lock timeout

**4 (CRIT-QA) — Fix GTO assertions path mismatch**
  → CRIT-LOGIC-003 → Evidence: `evals/gto_assertions.py:63` → Add `--evidence-dir` override parameter, default to project-root `.evidence`

**5 (RISK-001) — Add tests for critical untested hooks**
  → RISK-001 → Evidence: Testing agent (508/622 untested) → Create tests for `PreToolUse_require_plan_for_features.py`, `StopHook_commitment_tracker.py`, `SessionStart_hook_health_check.py`

**6 (RISK-002) — Create CI pipeline or document manual verification**
  → RISK-002 → Evidence: No `.github/workflows/` found → Document manual verification steps in CLAUDE.md testing section

**7 (RISK-003) — Audit 625+ type:ignore entries**
  → RISK-003 → Evidence: `__lib/binary_assertions.py`, 44 files → Categorize by: (a) legitimate Windows compat, (b) suppressible with proper types, (c) masking phantom imports

**8 (RISK-004) — Deduplicate GTO filesystem scans**
  → RISK-004 → Evidence: `subagents/gap_finder_subagent.py:320,193,273` → Single rglob call, pass file list to all three scan functions

**9 (RISK-005) — Add automatic cleanup to GTO orchestrator**
  → RISK-005 → Evidence: `lib/state_manager.py:98` → Call `cleanup_old_state_files(retention_days=7)` on each GTO run

**0 — Do ALL Recommended Next Steps

*Prioritization: CRIT items (1-4) block all others — multi-terminal state corruption silently loses data. RISK items (5-9) are cleanup/quality-of-life.*
