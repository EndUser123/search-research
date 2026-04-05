# Workspace Task Store DB Addendum

## Purpose
Move from per-TSK tasks.json files to a single workspace-level task store (DB), while keeping triplet files in their project TSK folders. JSON indexes are deprecated; tasks.db is canonical.

## Locations
- Workspace task store (SQLite): P:/.speckit/taskmaster/tasks.db (canonical)
- Per-project triplets: <project>/.speckit/memory/TSK-<project>-<id>/
  - plan.md
  - data_model.md
  - (legacy) tasks.json export during transition
  - docs/, reports/ (optional)
- Index.json: deprecated; leave only a stub if needed for legacy callers.

## Schema (workspace DB)
- tsk: id, project, path, active, created_at, updated_at
- task: id, tsk_id, title, description, status, priority, phase, task_type, assigned_to, estimated_duration, actual_duration, created_at, started_at, completed_at, last_activity, source, parent_task_id, tags (JSON text), acceptance_criteria (JSON text), verification_status (JSON text), completion_percentage, migration_date, entities (JSON text), validation_rules (JSON text)
- evidence (optional): id, task_id, kind, path, created_at

## Access Layer
- DAL: P:/.speckit/taskmaster/db.py
  - Manage active_tsk, list/add/update tasks, export/import per-TSK tasks.json if needed during transition

## Migration (workspace-wide)
1) Ensure per-project triplets exist under TSK folders (plan.md, data_model.md, tasks.json export).
2) Create tasks.db with the schema above.
3) For each TSK (from discovery or legacy index): register in tsk table (project, path, active flag) and import tasks.json rows into task table.
4) Set active_tsk in the DB (tsk.active=1). If a stub index.json is kept, it should only point to the DB, not track tasks.
5) Switch /task to use the DB; provide an export command for any tool still on JSON.
6) /exec resolves active TSK via DB, loads triplet from TSK folder; data_model cross-check can consume tasks from DB or an export.

## Compatibility
- Keep a stub index.json only if a legacy caller requires the file; do not store task state in JSON.
- Export/import utilities bridge JSON tools during transition.

## Benefits
- Single source for all tasks; no drift across JSON files.
- Triplets remain per project/TSK for /exec.
- Easier queries and data-link enforcement (entities/validation_rules) in DB.

## Risks & Mitigations
- Tooling drift: supply export/import to per-TSK tasks.json during transition.
- Migration errors: back up tasks.json before import; validate per-TSK counts.
- Overhead: DAL kept minimal; SQLite avoids external deps.
