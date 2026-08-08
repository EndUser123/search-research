# Handoff — batch skill code-defect cleanup (155 defects across 9 skills)

## Status
RESOLVED — all 8 skills scan clean (0 findings) as of 2026-08-08.

154 of 155 defects were fixed across multiple sessions since this handoff
was written (2026-08-06), via commits like `a217183` (resolve remaining 13
fleet-wide), `dad92ff` (batch 86→14), `f36282c` (todo SILENT-NO-OP fixes),
`58d3bf8` (BROKEN-PATH FP tuning), and skill-specific SILENT-NO-OP / CRAFT
cleanups. The final defect (LLM-FILLABLE false positive — a comment in
close_accounting.py referencing the `<LLM:>` pattern) was resolved by a
scanner root-cause fix: `check_llm_fillable` now skips comment lines, since
comments are documentation, never validation fields.

## Objective

The `script_scan.py` mechanical scanner found 155 code-level defects across
9 skills. These are unused variables, missing identity references, broken
path literals, collected-but-never-read fields — structural debt, not
hand-reviewed bugs. A batch `/maintain` or `/skill-dev measure` pass should
triage them.

## Defect counts by skill

| Skill | Defects | Highest-priority finding |
|-------|---------|------------------------|
| close | 62 | COLLECTED-BUT-UNUSED: `wiki_save` assigned at close_accounting.py:2160 but never read |
| ship-rhai | 21 | COLLECTED-BUT-UNUSED: `test_files` at ship_receipt.py:245 |
| aar | 13 | BROKEN-PATH: string literal looks like a file path (completion_receipt.py:38) |
| model-web | 13 | CRAFT-NO-TRIGGERS: description lacks trigger phrases |
| ship-py | 12 | COLLECTED-BUT-UNUSED: `started_at` at ship_orchestrator.py:177 |
| todo | 11 | CRAFT-SECOND-PERSON: 'you should' at SKILL.md:98 |
| handoff | 9 | MISSING-IDENTITY: script produces output but references no terminal/session |
| skill-dev | 7 | SILENT-NO-OP: returns [] inside 'if not' block (script_scan.py:872) |
| tp | 5 | CRAFT-NO-TRIGGERS: description lacks trigger phrases |

## Acceptance criteria

- Run `/maintain` or `/skill-dev measure` on each skill
- Fix defects that indicate real bugs (broken paths, silent no-ops, unused variables that should be used)
- Skip defects that are false positives or acceptable patterns (e.g., collected-but-unused may be intentional for future use)
- Commit per-skill with clear messages

## How to run the scanner

```powershell
python ~/.grok/skills/skill-dev/__lib/script_scan.py ~/.grok/skills/<skill-name>
python ~/.grok/skills/skill-dev/__lib/script_scan.py ~/.grok/skills/<skill-name> --json
```

## Provenance

- Discovered via /todo scanner session 019fd42f (2026-08-06)
- Source: `scan_functions.py` → `skill_scripts` source

## Handoff is wrong if
- The scanner has high false-positive rate (many findings are acceptable patterns)
- The defects are already known and triaged in prior sessions
