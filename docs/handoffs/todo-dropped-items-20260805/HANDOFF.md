# Handoff — dropped /todo LATER items (session 019fa8f8)

## Status
OPEN — these items were surfaced by `/todo` but dropped without disposition.

## Objective

Resolve three LATER items from the 2026-08-05 `/todo` scan that were silently
dropped during the NOW/NEXT execution wave.

## Items

### 1. Skill code defects (162 total across 10 skills)

`script_scan.py` found code defects in `__lib/` scripts:

| Skill | Defects | Worst finding |
|-------|---------|---------------|
| close | 62 | COLLECTED-BUT-UNUSED (field collected but never read) |
| ship-rhai | 21 | COLLECTED-BUT-UNUSED |
| ship-py | 13 | COLLECTED-BUT-UNUSED |
| aar | 13 | BROKEN-PATH (string literal looks like file path) |
| model-web | 13 | CRAFT-NO-TRIGGERS (description lacks trigger phrases) |
| todo | 11 | CRAFT-SECOND-PERSON (use imperative form) |
| handoff | 9 | MISSING-IDENTITY (no terminal/session reference) |
| skill-dev | 7 | SILENT-NO-OP (returns [] inside if-not block) |
| tp | 5 | CRAFT-NO-TRIGGERS |
| packet | 2 | NO-WIKI-PERSISTENCE |

**Action:** Run `/skill-dev measure` to batch-triage. Most are CRAFT findings
(style, not bugs). The COLLECTED-BUT-UNUSED and BROKEN-PATH findings in close/
ship-rhai/ship-py/aar are higher priority.

### 2. Dream proposals (7 pending, 1-10 days old)

Files at `P:/docs/dreams/`:
- `2026-08-04-dream-external-synthesis.md` (1d)
- `2026-08-04-dream-session-019fcb53.md` (1d)
- `2026-08-02-dream.md` (3d)
- `2026-08-01-dream-session-019fb933.md` (4d)
- `2026-08-01-dream.md` (4d)
- `2026-07-26-dream-incremental.md` (9d)
- `2026-07-26-dream.md` (10d)

**Action:** Operator decision — promote via `/wiki` or archive. Dreams older
than 7 days without promotion are likely stale.

### 3. Harvest pending items (3)

**Note:** harvest skill is being removed. These items need re-homing into
handoffs or explicit rejection:

- NEXT_ACTION_PACKET prototype in /www — replace prose skill suggestion with
  structured packet
- tool_choice=required injection in /codex skill for Luna/mini-class models
- Luna no-auto-pool update not applied to model-tool-calling-capability-matrix.md

**Action:** Each becomes its own small handoff, or gets explicitly rejected.

## Provenance

Surfaced by `/todo` scan on 2026-08-05. Dropped during execution of NOW/NEXT
items 1-5. Operator caught the drop and asked "did you do these?"

## Handoff is wrong if

- The skill defects are all CRAFT-level noise (no real bugs to fix)
- The dreams have already been reviewed and rejected in another session
