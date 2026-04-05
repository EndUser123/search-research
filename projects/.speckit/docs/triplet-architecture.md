# Triplet & Task Architecture (Speckit-Scoped)

## Goals
- Eliminate root writes and ambiguity in /exec artifact selection.
- Co-locate tasks (Taskmaster-style) and CWO12 triplets under one project-scoped root.
- Enforce hierarchy: workspace constitution -> project constitution -> task scope.

## Canonical Locations
- Workspace constitution: P:\.speckit\memory\constitution.md (parent)
- Per-project root: <project>/.speckit/
- Per-task workspace (TSK): <project>/.speckit/memory/TSK-<project>-<id>/
  - plan.md
  - data_model.md
  - tasks.json (canonical task store)
  - docs/ (PRDs, notes) [optional]
  - reports/ (validation/analysis) [optional]

## Task Store (Workspace DB)
- Workspace DB (canonical): P:/.speckit/taskmaster/tasks.db
- Tracks all TSKs (ids, project, path) and active_tsk
- Per-TSK export (optional): <project>/.speckit/memory/TSK-<project>-<id>/tasks.json (compatibility only)

## Discovery & Enforcement (CWO12)
/exec must:
- Read active TSK from the workspace DB (tasks.db) or explicit override.
- Search only that TSK folder for the triplet (plan.md, data_model.md, tasks.json export if needed).
- Reject root-level artifacts and non-TSK locations.
Config:
- Remove "." from allowed_roots.
- allowed_roots: [".speckit/memory"]
- on_multiple_candidates: block_and_ask (but scope prevents ambiguity).

## Constitutions
- Workspace: P:/.speckit/memory/constitution.md
- Project: <project>/.speckit/constitution.md
  - Preamble: “Inherits from P:/.speckit/memory/constitution.md; conflicts resolved in favor of the workspace constitution.”

## Command Behaviors
- /task: requires active TSK; reads/writes via workspace DB (tasks.db); optional export to tasks.json if needed for compatibility; refuses root writes.
- /plan: requires active TSK; writes/updates plan.md in that TSK folder.
- /exec: requires active TSK; validates only that triplet; blocks if missing or outside TSK.
- Helper: /tsk.set <id> sets active TSK in the DB; /tsk.new creates TSK folder scaffold and registers in DB.

## Folder Blueprint (per TSK)
- plan.md
- data_model.md
- tasks.json
- docs/ (optional)
- reports/ (optional)

## Data Model Expectations (to improve outcomes)
- data_model.md should define:
  - Entities (name, purpose, key fields)
  - Relationships (A->B, cardinality)
  - Validation rules (named, e.g., USR-EMAIL-UNIQUE)
- tasks.json should reference these with fields like:
  - entities: ["User", "Order"]
  - validation_rules: ["USR-EMAIL-UNIQUE"]
- Simple validation: tasks referencing entities/validation_rules must match names in data_model.md; tasks that touch data should list at least one entity.

## Optional Code-Aware Validation
- Add a discovery/inventory step (e.g., tree-sitter or static model scan) to seed data_model.md.
- Cross-check tasks’ entities against code-derived entities for stronger /exec validation.

## Prohibited
- Writing triplets or tasks to repository root.
- Discovering artifacts outside .speckit/memory/TSK-*.
