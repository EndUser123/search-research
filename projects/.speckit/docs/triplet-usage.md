# Daily Usage: Tasks, Plans, Exec

## One-Time per Project
- Create or pick a TSK ID: TSK-<project>-<id>.
- Register/set active in workspace DB: P:/.speckit/taskmaster/tasks.db (via DAL or /tsk.set).
- Ensure triplet files exist in .speckit/memory/TSK-<project>-<id>/:
  - plan.md
  - data_model.md
  - tasks.json (export if needed; DB is canonical)

## Pre-Work Discovery (recommended for data-aware work)
- Run a quick inventory of models/schemas (e.g., tree-sitter/static scan) to seed data_model.md.
- Keep data_model.md concise: Entities, Relationships, Validation Rules.

## Commands Flow
- /tsk.new <id>: scaffold .speckit/memory/TSK-<project>-<id>/, register in DB; optional tasks.json export.
- /tsk.set <id>: switch active_tsk in DB.
- /task ... : reads/writes via workspace DB; refuses root writes; export tasks.json only if required for a legacy tool.
- /plan ... : reads/writes plan.md in the active TSK folder; refuses root writes.
- /exec ... : resolves active TSK from DB; validates only that triplet; blocks if missing/incomplete; no root fallback.

## Data-Task Linking
- In DB rows (or exported tasks.json), add per-task fields when data is involved:
  - entities: ["User", "Order"]
  - validation_rules: ["USR-EMAIL-UNIQUE"]
- In data_model.md, define matching names:
  - Entities (name, purpose, key fields)
  - Relationships (A->B, cardinality)
  - Validation rules (named)
- Simple validation: tasks’ entities/validation_rules must exist in data_model.md; tasks that touch data must list at least one entity.

## Rules
- Never place triplets or tasks in repo root.
- Keep one active TSK per project; change via /tsk.set (DB).
- If multiple TSKs exist, /exec must be pointed explicitly (active_tsk or flag).
- Constitutions: project `.speckit/constitution.md` inherits from workspace `P:/.speckit/memory/constitution.md`.
- State lives in DB (tasks.db); index.json, if present, is only an optional stub for legacy callers.

## Troubleshooting
- /exec cannot find artifacts: set active TSK in DB, ensure triplet files exist in that TSK folder, verify config allowed_roots excludes ".".
- Ambiguous triplets: with scoping, should not occur; if multiple TSKs are valid, switch active_tsk in DB explicitly.
- Legacy files in root: move them into a TSK folder and register in DB.
- Entities/rules mismatch: align DB/exported tasks fields to names in data_model.md.
