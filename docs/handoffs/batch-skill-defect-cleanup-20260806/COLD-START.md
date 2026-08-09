# Cold-start prompt: batch skill-defect cleanup (155 defects across 9 skills)

Copy-paste this into a fresh session:

---

/go fix the 155 script defects from the batch-skill-defect-cleanup handoff.

Handoff: `P:/docs/handoffs/batch-skill-defect-cleanup-20260806/HANDOFF.md`

Scanner: `python ~/.grok/skills/skill-dev/__lib/script_scan.py --skill <skill-name>`

Defect counts by skill:
| Skill | Defects | Highest-priority |
|-------|---------|-----------------|
| close | 62 | COLLECTED-BUT-UNUSED: wiki_save at close_accounting.py:2160 |
| aar | 13 | BROKEN-PATH: completion_receipt.py:38 |
| model-web | 13 | CRAFT-NO-TRIGGERS |
| ship-py | 12 | COLLECTED-BUT-UNUSED: started_at at ship_orchestrator.py:177 |
| todo | 11 | CRAFT-SECOND-PERSON |
| handoff | 9 | MISSING-IDENTITY |
| skill-dev | 7 | SILENT-NO-OP: script_scan.py:872 |
| tp | 5 | CRAFT-NO-TRIGGERS |

Note: ship-rhai (21 defects) was deleted 2026-08-08 — skip it, it's gone.

Rules:
- Fix real bugs (broken paths, silent no-ops, unused vars that should be used)
- Skip false positives or acceptable patterns (collected-but-unused may be intentional)
- Commit per-skill with clear messages
- Run the scanner after each fix to confirm the defect count drops
