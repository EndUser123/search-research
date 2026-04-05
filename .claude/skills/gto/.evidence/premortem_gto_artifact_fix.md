# Pre-Mortem: GTO Skill Artifact Fix

**Analysis Date:** 2026-03-25
**Target:** GTO SKILL.md artifact fix (adding `--format both` to EXECUTE command)
**Analyst:** Claude Code

---

## Step 0: Project Constraints (from CLAUDE.md)

- **Solo developer environment**: 75-85% reliability target
- **Evidence-first**: Verification > confidence
- **Fail fast**: Surface problems immediately
- **Reversibility 1.0-1.25**: Config/feature flag changes — proceed directly
- **Sequential file ops**: Read -> Write -> Verify -> Next (no batching)
- **Skill invocation protocol**: Load -> Execute -> Report (no prose substitution)

---

## Step 0.7: Kill Criteria

If any of these occur, the approach should be reconsidered:
1. GTO assertions fail consistently after fix
2. JSON artifact saving causes disk space issues (>100MB/hour)
3. The `--format both` flag causes performance degradation >5 seconds per run
4. A new bug is introduced (e.g., markdown output breaks)

---

## Step 1: Failure Scenario

**"It's 6 months later. The GTO artifact fix FAILED. Why?"**

The fix (adding `--format both` to SKILL.md line 41) was supposed to ensure JSON artifacts are saved so the A1 assertion passes. Instead, the system is broken and GTO no longer works correctly.

---

## Step 1.5: Fix Side Effects Analysis

**The fix:** Changed SKILL.md line 41 from:
```
python P:/.claude/skills/gto/gto_orchestrator.py --project-root "P:\.claude\skills\gto"
```
to:
```
python P:/.claude/skills/gto/gto_orchestrator.py --project-root "P:\.claude\skills\gto" --format both
```

**NEW risks introduced:**
1. **Performance**: `--format both` generates both JSON and markdown — additional processing time
2. **Disk space**: Two outputs per run instead of one — faster accumulation of `.evidence` files
3. **Backward compatibility**: If another script parses SKILL.md and expects the old format, it may break
4. **Terminal ID staleness**: The assertions check `gto-state-{terminal_id}/` which may not exist if GTO not run via skill

---

## Step 2: Brainstorm Failure Causes (10+)

### People
1. User runs GTO via different entry point (monorepo script) that doesn't respect `--format both`
2. User forgets to run assertions after changes

### Process
3. SKILL.md not updated in all places (e.g., documentation references old command)
4. Assertions not run as part of CI/CD or pre-commit
5. Fix not communicated to other terminals/users

### Tech
6. `--format both` has bugs in `save_json_artifact()` or `save_markdown_artifact()`
7. Artifact directory (`.evidence/gto-outputs/`) has permission issues or disk full
8. Terminal ID mismatch still exists and wasn't actually fixed (user said "not the terminal ID code")
9. JSON artifact is saved but with wrong timestamp (stale, outside 1-hour window)
10. The `save_json_artifact()` method has a path bug that saves to wrong location
11. Git operations interfere with artifact file timestamps
12. The 1-hour window in A1 assertion is too tight for slow systems

### External
13. Disk space exhausted — artifact saving silently fails
14. Antivirus/interceptor blocks file writes to `.evidence/` directory

---

## Step 2.5: Cascade Analysis (Risks ≥6)

**RISK-006 (Disk full → artifact save fails):**
1. Disk space exhausted
2. → `save_json_artifact()` throws exception or silently fails
3. → No JSON artifact created
4. → A1 assertion fails

**RISK-012 (1-hour window too tight):**
1. GTO run takes >1 hour (slow system or large codebase)
2. → Artifact timestamp is now >1 hour old
3. → A1 assertion fails even though artifact exists
4. → False negative — system is working but assertion is too strict

---

## Step 2.6: AI/LLM-Specific Failure Modes

From `references/ai-llm-failures.md`:
1. **Skill substitution**: Prose analysis instead of actual GTO execution (mitigated by StopHook_skill_execution_gate)
2. **Stale context**: Assertions run with cached results from before fix
3. **Misattribution**: Blaming wrong component for A1 failure (user already corrected this)

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| 1 | User uses wrong entry point | People |
| 2 | Forgets to run assertions | People |
| 3 | SKILL.md not updated everywhere | Process |
| 4 | No CI/CD assertion check | Process |
| 5 | Not communicated to others | Process |
| 6 | `--format both` has bugs | Tech |
| 7 | Permission/disk issues | Tech |
| 8 | Terminal ID mismatch persists | Tech |
| 9 | Wrong artifact timestamp | Tech |
| 10 | Path bug in save_json_artifact | Tech |
| 11 | Git corrupts timestamps | Tech |
| 12 | 1-hour window too tight | Tech |
| 13 | Disk full silent fail | External |
| 14 | Antivirus blocks writes | External |

---

## Step 3.5: Reference Class Forecasting

Similar fixes in this codebase (from memory):
- `gto_gitready_gap_fix_lessons.md`: Script path resolution, assertions CLI, pointer validation
- Pattern: One-line config fix to SKILL.md often masks deeper issues
- Base rate: ~20% of SKILL.md fixes require follow-up adjustment within 1 week

---

## Step 3.6: Success Theater Detection

- **A1 assertion "passes"**: Score 100/100 may indicate test suite doesn't catch edge cases
- **JSON artifact created**: Doesn't verify artifact content is valid, only that file exists
- **Health score 79%**: No visibility into what 21% gap represents or whether it matters

---

## Step 3.8: Operational Verification

**Verified in this session:**
- `gto_assertions.py` output shows `gto-artifact-20260325_191201.json` exists (A1)
- Health score 79% reported (A2)
- Assertions pass with score 100/100

**NOT verified:**
- Content validity of the JSON artifact
- Whether `--format both` works correctly on subsequent runs
- Whether the fix persists across terminal restarts

---

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score |
|----|------|-----------|--------|-------|
| 6 | `--format both` has bugs | 2 | 3 | 6 |
| 7 | Permission/disk issues | 2 | 3 | 6 |
| 10 | Path bug in save_json_artifact | 2 | 3 | 6 |
| 12 | 1-hour window too tight | 3 | 2 | 6 |
| 3 | SKILL.md not updated everywhere | 2 | 2 | 4 |
| 4 | No CI/CD assertion check | 2 | 2 | 4 |
| 9 | Wrong artifact timestamp | 1 | 3 | 3 |

---

## Step 4.5: Dependency Cascades (OPTIONAL)

**RISK-006 (disk full) causes RISK-007 (permission issues) and RISK-010 (path bug surfaces):**
- When disk is full or slow, error handling paths get exercised that normally aren't
- These are distinct failure modes sharing a common root cause

---

## Step 5: Prevent Top 3 Risks + Map to Actions

### Risk 6, 7, 10 (Tech): `--format both` bugs, permission issues, path bugs
**Action:** Run GTO 3 times on different targets to verify consistent artifact creation
- Evidence: `gto_orchestrator.py:530-570` (save_json_artifact method)

### Risk 12 (Tech): 1-hour window too tight
**Action:** Check if `gto_assertions.py` A1 window is configurable or should be extended
- Evidence: `evals/gto_assertions.py` (A1 check logic)

### Risk 3 (Process): SKILL.md not updated everywhere
**Action:** Grep for old command pattern in all skill files
- Evidence: `grep "gto_orchestrator.py" --format markdown` pattern

---

## Step 6: Warning Signs to Monitor

- GTO assertions fail with "No recent artifacts"
- `.evidence/gto-outputs/` grows >10MB per day
- Health score drops below 50%
- A2 (health score) fails but A1 passes

---

## Step 7: Adversarial Validation (8 agents - COMPLETED)

**Execution:** 8 agents ran in parallel. Key findings merged below.

---

## 🔴 WHAT'S ACTUALLY BROKEN

**Critical failures (must fix before further use)**
• CRIT-001 | `--format both` does NOT save markdown artifact (Risk 9)
  [causes: QA-001, TEST-001]
  • Pre-mortem incorrectly assumed `save_markdown_artifact()` exists — it does NOT
  • `--format both` prints markdown to stdout, saves JSON to file only
  • Evidence: `gto_orchestrator.py:687-695` — format_output returns string, not Path

• CRIT-002 | A1 assertion only checks file existence, not JSON content validity (Risk 9)
  [causes: TEST-002, QUAL-001]
  • Empty JSON `{}` passes A1 even if GTO failed completely
  • A malformed artifact with truncated JSON passes if timestamp is recent
  • Evidence: `gto_assertions.py:60-81` — no json.load() or field validation

• CRIT-003 | SKILL.md `--terminal` flag does not exist in assertions CLI (Risk 8)
  [causes: QA-005, COMP-002]
  • SKILL.md line 157 says `--terminal $TERMINAL_ID` but gto_assertions.py uses env vars
  • User following instructions gets "unrecognized argument: --terminal"
  • Evidence: `gto_assertions.py:26-47` — _get_default_terminal_id() reads env vars only

**High-risk behavior**
• RISK-001 | Terminal ID unsanitized in direct Python invocation (Risk 7)
  • Shell hook sanitizes, but direct invocation bypasses hook
  • Path injection: `CLAUDE_TERMINAL_ID='../../etc'` could escape .evidence/
  • Evidence: `gto_assertions.py:35-38` — no sanitization on env var values

• RISK-002 | N+1 pattern in A2 health score check — 4 separate rglob calls (Risk 6)
  • 4 rglob traversals of .evidence/ instead of single pass
  • Evidence: `gto_assertions.py:85,106,143,187` — PERF-001

• RISK-003 | Full project Python scan in health calculator — could exceed 5s kill criterion (Risk 6)
  • `_calculate_code_quality()` does `project_root.rglob("*.py")` on ALL files
  • Evidence: `health_calculator_subagent.py:256` — PERF-002

---

## 🟠 HIGH-RISK BEHAVIOR

• RISK-004 | 1-hour A1 window hardcoded, not configurable (Risk 6)
  [causes: LOGIC-004, QA-003]
  • Pre-mortem identified RISK-012 but no fix implemented
  • GTO is fast (deterministic detectors) so this is low-priority unless system is very slow
  • Evidence: `gto_assertions.py:62` — `timedelta(hours=1)` hardcoded

• RISK-005 | `run_gto_monorepo.py` lacks `--format` argument (Risk 6)
  [causes: TEST-005]
  • Users following SKILL.md line 47 get no JSON artifact
  • Evidence: `run_gto_monorepo.py:16-52` — no --format in argparse

• RISK-006 | Duplicate state_dir.exists() check in A5 — unreachable code (Risk 4)
  • Lines 268 and 274 both check exists() — second is unreachable
  • Evidence: `gto_assertions.py:268,274` — LOGIC-003

• RISK-007 | Pre-mortem self-contradiction on verification (Risk 5)
  [causes: COMP-004, LOGIC-001]
  • Section 3.6 warns "assertion-passing doesn't prove fix works"
  • Section 3.8 uses "assertions pass with score 100/100" as proof fix works
  • Document directly contradicts itself

**Dependency annotations:**
- `[causes: ID]` → This risk directly creates another risk
- `[blocks: ID]` → This risk prevents another risk from starting
- `[caused-by: ID]` → This risk is caused by another risk

---

## 🧠 BLIND SPOTS & CONTRADICTIONS

• **Self-defeating analysis**: Pre-mortem warns (3.6) that A1 passing is insufficient evidence, then uses it (3.8) as proof of success — COMP-004, LOGIC-001
• **Health score discrepancy**: Pre-mortem says 79%, actual report shows 80% — COMP-003
• **Wrong code citation**: Pre-mortem cites `gto_orchestrator.py:530-570` for save_json_artifact, but this range contains format_output() — save_json_artifact is at 530-571 — COMP-001
• **Step 7 never executed**: Pre-mortem said "To be executed after saving" but this was never done — QA-004

---

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Verify JSON artifact contains valid fields (not just exists)
• [ ] Check --format both produces JSON to .evidence/ AND markdown to stdout

**Cadence**
• [ ] Weekly: Run GTO assertions on multiple targets to verify consistent behavior
• [ ] Monthly: Verify .evidence/ directory size — should not grow >10MB/day

---

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

Detailed findings stored in `.evidence/` directory from 8 adversarial agents:
- compliance findings: this file
- logic findings: Section 7 above
- performance findings: PERF-001 through PERF-004
- security findings: SEC-001 through SEC-004
- testing findings: TEST-001 through TEST-008
- quality findings: QUAL-001 through QUAL-007
- critic findings: Section 6 above (consensus gaps, blind spots)
- QA findings: QA-001 through QA-007

---

## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format (v5.0)**: Each action MUST link to verified adversarial finding with evidence.

N – Capture lessons and patterns (automatic)
  Na: Auto-invoke `/learn` - Capture failure patterns to CKS
  Nb: Auto-invoke `/reflect {skill_name}` - Document lessons from this analysis

1 (GTO Assertions) - Fix A1 content validation
  1a: Add JSON content validation to A1 — Verify artifact contains required fields (gaps, timestamp, metadata) — Evidence: TEST-002, gto_assertions.py:60-81 **[DONE 2026-03-25]**
  1b: Remove duplicate exists() check at line 274 — Evidence: LOGIC-003, gto_assertions.py:274 **[DONE 2026-03-25]**

2 (SKILL.md) - Fix documentation to match implementation
  2a: Remove `--terminal $TERMINAL_ID` from verification command — Use env var instead — Evidence: QA-005, gto_assertions.py:26-47 **[DONE 2026-03-25]**
  2b: Document that `--format both` prints markdown to stdout, not to file — Evidence: QA-001, gto_orchestrator.py:687-695 **[DONE 2026-03-25]**

3 (Security) - Add terminal ID sanitization
  3a: Add sanitization to _get_default_terminal_id() — Regex [a-zA-Z0-9_-]{1,64} — Evidence: SEC-001, gto_assertions.py:35-38 **[DONE 2026-03-25]**

4 (Performance) - Fix N+1 rglob pattern
  4a: Combine 4 rglob loops in A2 into single pass — Evidence: PERF-001, gto_assertions.py:85,106,143,187 **[DEFERRED - complex refactoring, low impact in solo-dev]**

5 (Integration) - Add test coverage for --format both
  5a: Add CLI integration test for --format both — Verify JSON file created AND markdown stdout — Evidence: TEST-001, gto_orchestrator.py:647 **[DEFERRED - test file creation]**
  5b: Add test for run_gto_monorepo.py equivalent artifact creation — Evidence: TEST-005, run_gto_monorepo.py:16-52 **[DEFERRED - test file creation]**

0 - Do ALL Recommended Next Steps

---

## Adversarial Agent Summary (8 agents ran)

| Agent | Key Finding |
|-------|-------------|
| compliance | Evidence citation wrong range (530-570 vs 530-571) |
| logic | Self-contradiction on verification (3.6 vs 3.8) |
| performance | N+1 pattern: 4 rglob calls in A2; full project scan in health calc |
| security | Terminal ID unsanitized; path traversal via --project-root |
| testing | No --format both test; A1 doesn't validate content |
| quality | Timestamp mismatch; duplicate check; hardcoded 1-hour window |
| critic | 7 risks missing from scoring; success theater ignored |
| QA | BLOCKER: markdown is stdout only, not file; --terminal flag missing |

**Files referenced:**
- `gto_orchestrator.py:530-571` — save_json_artifact method
- `gto_assertions.py:60-81` — A1 check (no content validation)
- `gto_assertions.py:26-47` — _get_default_terminal_id (no sanitization)
- `run_gto_monorepo.py:16-52` — monorepo entry (no --format arg)
