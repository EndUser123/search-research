# Skill __lib/ Code Defect Cleanup

## Status
OPEN — ready for execution

## Session
session-019fcd47 (2026-08-05)

## Objective

Fix code-level defects detected by `script_scan.py` across 7 skills. The defects
are style/maintainability findings (collected-but-unused fields, undocumented
functions, silent no-ops, missing identity) — not runtime bugs. The goal is to
bring each skill's `__lib/` scripts to zero findings.

## Evidence

Run the scanner to see current state:
```powershell
python "C:\Users\brsth\.grok\skills\skill-dev\__lib\script_scan.py" "C:\Users\brsth\.grok\skills\<skill-name>" --json
```

## Defect counts by skill (as of 2026-08-05)

| Skill | Defects | Primary pattern |
|-------|---------|-----------------|
| close | 62 | COLLECTED-BUT-UNUSED fields in close_accounting.py (40) + continuation_coverage.py (11) |
| ship-rhai | 21 | COLLECTED-BUT-UNUSED in ship_receipt.py |
| aar | 12 | Mixed: collected-but-unused, undocumented functions |
| model-web | 11 | fusion_orchestrate.py + run_state.py |
| handoff | 9 | Mixed across scripts |
| tp | 4 | agy_lens.py, tp_critique_log.py, tp_dispatch.py |
| todo | 1 | SKILL.md craft finding |

## Scope

For each skill, in order of defect count (largest first):

1. Run `script_scan.py` to get the current findings
2. For each finding:
   - **COLLECTED-BUT-USED**: either use the field in output rendering, or remove the collection line. If the field was collected for a future feature that was never built, remove it.
   - **UNDOCUMENTED-FUNCTION**: add a one-line docstring or mention in SKILL.md
   - **SILENT-NO-OP**: either return a meaningful value, or add a comment explaining why None is correct
   - **MISSING-IDENTITY**: add terminal/session env var references if the script produces session-scoped output
3. Re-run `script_scan.py` to verify 0 findings
4. Commit with message: `fix: clear N script_scan findings in <skill> __lib/`

## Acceptance criteria

1. `script_scan.py` reports 0 findings for all 7 skills
2. No runtime regressions (run the skill's existing tests if any)
3. Each skill committed separately with descriptive message

## Verification path

```powershell
# After fixing each skill:
python "C:\Users\brsth\.grok\skills\skill-dev\__lib\script_scan.py" "C:\Users\brsth\.grok\skills\<skill-name>" --json
# total_findings should be 0
```

## Constraints

- Do NOT change runtime behavior — only fix the scanner findings
- Do NOT refactor while fixing — keep changes minimal (remove dead code, add docstrings, add identity)
- Follow AGENTS.md file editing protocol (read → edit → verify)
- The `close` skill's close_accounting.py is 2200+ lines — work carefully

## Claim

Claim this handoff with:
```powershell
python ~/.grok/skills/handoff/__lib/claim_handoff.py P:/docs/handoffs/skill-code-defects-cleanup-20260805/HANDOFF.md --session $env:GROK_SESSION_ID --host grok
```
