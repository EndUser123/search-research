---
 Migrated from: premortem_ai-cli_skill_update_20260402_154430.md
 Original location: P:\.claude\.evidence\premortem_ai-cli_skill_update_20260402_154430.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: /ai-cli Skill Enhancement (--hide-prompt flag + rename)

**Date:** 2026-04-02
**Target:** `/ai-cli` skill — added `--hide-prompt` flag to suppress enhanced prompt; renamed `ask_cli.py` → `ai_cli.py`

**Implementation note:** Design decision to use `--hide-prompt` (suppress-on) rather than `--show-prompt` (show-on) for better UX — prompt displays by default without requiring a flag.
**Analyst:** Claude Code (solo dev)

---

## Step 0: Project Constraints (from CLAUDE.md)

- **Solo dev context**: ROI over risk-aversion, pragmatic solutions
- **Sequential file operations**: Execute modifications ONE AT A TIME — race conditions from parallel Edit/Write
- **Verification before claiming**: Unverified absence claims prohibited
- **Edit verification**: Run Read after Edit to confirm persistence
- **Python dev**: Always add type hints, use pytest
- **Evidence tiers**: Claims need Tier 1/2 evidence for high-stakes

---

## Step 0.7: Kill Criteria

- If import errors appear in test run after rename → revert and abort
- If any test fails that was passing before rename → identify specific breakage
- If `--show-prompt` flag doesn't work when tested → fix before moving on

---

## Step 1: Failure Scenario

"It's 6 months later. The `/ai-cli` skill broke silently. CLIs fail to launch, or wrong prompts get sent, or test suite is red. Why?"

---

## Step 1.5: Fix Side Effects (What NEW risks do these changes introduce?)

### Change 1: `--show-prompt` flag addition
- NEW: `getattr(args, "show_prompt", False)` — minor, low risk
- NEW: print statements to stdout — could interfere with JSON output parsing if `--output-format json` is combined with `--show-prompt`

### Change 2: `ask_cli.py` → `ai_cli.py` rename
- NEW: All test imports must reference `ai_cli` not `ask_cli` — broken imports = entire test suite fails
- NEW: All doc references must update — stale docs cause confusion
- NEW: Companion modules (`file_context.py`, `prompt_templates.py`, etc.) may have relative imports that break

---

## Step 2: Brainstorm Causes (Multi-Perspective)

### People
1. **P1**: Developer forgets to update one of the 10 test files' imports after rename
2. **P2**: Stale doc references in `context-handling.md` or `examples.md` cause user confusion
3. **P3**: `@patch` decorators in `test_complexity_characterization.py` missed during bulk sed

### Process
4. **PROC1**: Bulk sed used for import updates — may miss edge cases (e.g., string literals, comments)
5. **PROC2**: No test run after rename to verify suite still passes
6. **PROC3**: Concurrent file writes during rename caused partial persistence (Windows WSL issue)

### Tech
7. **T1**: `getattr(args, "show_prompt", False)` — if argparse doesn't recognize the flag, silently falls back to False
8. **T2**: `--show-prompt` print goes to stdout — corrupts JSON output when both flags are used together
9. **T3**: Companion modules use `from ask_cli import` internally (not in tests) — haven't been checked
10. **T4**: Python module caching — old `ask_cli.pyc` bytecode still loaded if `.pyc` exists
11. **T5**: SKILL.md execution path not fully updated — partial path still pointing to `ask_cli.py`
12. **T6**: Circular import risk if `ai_cli.py` imports from companion modules that import back from it

### External
13. **E1**: Windows path case-insensitivity — `ask_cli.py` and `ai_cli.py` considered same file by git but different by Python

---

## Step 2.5: Cascade Analysis (Likelihood ≥ 2)

### T1 (argparse flag silent fallback) — Likelihood: 2, Impact: 2
- **sure**: `--show-prompt` silently does nothing → user thinks flag works, no error raised
- **sure**: User relies on `--show-prompt` output for debugging → wastes time investigating wrong prompt
- **maybe**: User combines with `--output-format json` → stdout noise corrupts JSON parse → pipeline breaks

### P1 (missed import update) — Likelihood: 3, Impact: 3
- **sure**: Test fails on import with `ImportError: cannot import name 'main' from 'ai_cli'`
- **sure**: Entire test suite red → no signal on actual functionality
- **sure**: Developer doesn't notice until next manual run → silent regression

### T2 (stdout print corrupts JSON) — Likelihood: 2, Impact: 2
- **maybe**: JSON output has `=== ENHANCED PROMPT ===` text prepended → parse fails downstream
- **maybe**: No error in CLI itself → silent data corruption in consuming pipeline

### E1 (Windows case-insensitivity) — Likelihood: 1, Impact: 3
- **impossible**: git mv handles this correctly, Python sees both files distinct

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **AI-1**: LLM (me) relied on grep output showing "no stale references" — but grep didn't check `@patch` decorator strings (found separately)
- **AI-2**: Bulk sed may have missed `@patch("ask_cli.xxx")` patterns in `test_complexity_characterization.py` — fixed after explicit check
- **AI-3**: Edit verification hook flagged the rename as requiring import_update verification — I verified via grep twice

---

## Step 2.7: Temporal Failure Modes

- **Temp-1**: Context compaction could cause me to forget that `test_complexity_characterization.py` needed special handling for `@patch` decorators
- **Temp-2**: Earlier bulk sed for `from ask_cli import` didn't catch `@patch` decorators — discovered via separate grep check

---

## Step 2.8: Interruption/Handoff/Contract Failure Modes

- **H1**: The "import_update" outstanding verification from the PostToolUse hook is stale — I verified imports are clean via grep, but the hook hasn't re-run confirmation
- **H2**: No actual test run was executed to verify the rename works end-to-end

---

## Step 3: Categorization

| ID | Category |
|----|----------|
| P1 | Tech (test breakage) |
| P2 | Tech (doc staleness) |
| P3 | Tech (patch decorators) |
| PROC1 | Process (bulk sed gaps) |
| PROC2 | Process (no test after rename) |
| T1 | Tech (argparse silent fallback) |
| T2 | Tech (stdout corrupts JSON) |
| T3 | Tech (companion module imports) |
| T4 | Tech (.pyc cache) |
| T5 | Tech (SKILL.md partial update) |
| E1 | External (Windows path) |

---

## Step 3.8: Operational Verification

**VERIFY THIS BEFORE CLAIMING SUCCESS:**

1. **Run test suite**: `pytest P:/.claude/skills/ai-cli/tests/ -v --tb=short` — must pass
2. **Test `--show-prompt` flag**: `python ai_cli.py "test" --show-prompt` — must print prompt
3. **Test `--show-prompt` + `--output-format json`**: Must not corrupt JSON
4. **Verify companion imports**: `python -c "from ai_cli import *"` from skill directory

---

## Step 4: Risk Ratings

| Risk | Likelihood | Impact | Score | Confidence |
|------|-----------|--------|-------|-----------|
| P1 (test import breakage) | 3 | 3 | 9 | 85% |
| T1 (show-prompt argparse silent) | 2 | 2 | 4 | 70% |
| T2 (stdout corrupts JSON) | 2 | 2 | 4 | 60% |
| PROC2 (no test after rename) | 3 | 2 | 6 | 90% |
| T3 (companion module imports) | 1 | 2 | 2 | 80% |
| T5 (SKILL.md partial update) | 1 | 2 | 2 | 75% |

---

## Step 5: Top 3 Risks + Actions

### TOP 1: PROC2 — No test run after rename (Risk 6)
**Action**: Run pytest immediately to verify suite passes

### TOP 2: P1 — Test imports may still reference old `ask_cli` (Risk 9)
**Action**: Re-verify ALL test files for `from ask_cli import` and `@patch("ask_cli.` patterns

### TOP 3: T2 — `--show-prompt` stdout corrupts JSON output (Risk 4)
**Action**: Print to stderr instead of stdout, or skip print when `--output-format json`

---

## Step 6: Warning Signs

- **PROC2**: Any test failure after rename → `ImportError` or `ModuleNotFoundError`
- **T2**: JSON output starts with `=== ENHANCED PROMPT ===` text
- **P1**: pytest output shows `ImportError` on collection

---

## Evidence Files

- `P:/.claude/.evidence/premortem_ai-cli_skill_update_20260402_154430.md` (this file)

## Status

**IN PROGRESS — Pending adversarial validation (Step 7)**
