# Triplet & Task Migration Guide

## What This Does
- Moves all CWO12 triplets and task stores into project-scoped .speckit/memory/TSK-* folders.
- Establishes a single active TSK per project for /task, /planning, and /exec.

## Prereqs
- Workspace constitution: P:/.speckit/memory/constitution.md.
- Per-project scope: use <project>/.speckit (including P:/__csf.nip/.speckit).

## Migration Steps

1) Prepare Structure
- Ensure <project>/.speckit exists.
- Add/update <project>/.speckit/constitution.md with inheritance:
  “This project constitution inherits from P:/.speckit/memory/constitution.md; conflicts resolve to the workspace constitution.”

2) Inventory Existing Triplets
- Find plan.md, tasks.json, data_model.md outside .speckit/memory/TSK-*.
- Map each set to a TSK ID (create if needed): TSK-<project>-<id>.

3) Create TSK Folders
- Create <project>/.speckit/memory/TSK-<project>-<id>/.
- Move (or copy) plan.md, data_model.md, tasks.json into that folder.
- Optional: docs/, reports/ under the same TSK.

4) Register in Workspace DB (canonical)
- Insert TSK into P:/.speckit/taskmaster/tasks.db with fields:
  - id, project, path (.speckit/memory/TSK-<project>-<id>), active flag
- Optionally keep a minimal index.json stub, but do not track tasks in JSON; tasks.db is canonical.

5) Lock Down Discovery
- CWO12 config: remove root fallback; scope to .speckit/memory;
  {
    "artifact_root": ".speckit/memory",
    "discovery": {
      "allowed_roots": [".speckit/memory"],
      "on_multiple_candidates": "block_and_ask"
    }
  }
- /exec resolves active TSK via the workspace DB; ignores root-level artifacts.

6) Add Data-Link Enforcement
- In tasks.json (export) or DB rows, add per-task fields: entities: [...], validation_rules: [...].
- In data_model.md, define Entities, Relationships, Validation Rules with names matching those values.
- Validator check: tasks referencing entities/validation_rules must exist in data_model.md; tasks that touch data must list at least one entity.

7) Update Commands
- /task: require active TSK; use workspace DB (tasks.db) for reads/writes; export tasks.json only if needed for compatibility.
- /planning: require active TSK; write plan.md in the TSK folder.
- /exec: require active TSK; validate only that triplet; block otherwise.
- Helpers: /tsk.set <id>, /tsk.new <id> (registers in DB).

8) Clean Up Legacy
- After verifying migration, delete or archive root-level triplets.
- Keep a short compatibility note pointing to the new TSK paths; avoid JSON tracking of tasks.

## Validation Checklist
- active_tsk recorded in P:/.speckit/taskmaster/tasks.db (and optional stub index.json if needed for legacy callers).
- Triplet present in the active TSK folder: plan.md, data_model.md, tasks.json (export).
- /exec validation points only to .speckit/memory/TSK-*.
- /task and /planning refuse to write outside the active TSK.
- Project constitution references P:/.speckit/memory/constitution.md.
- Tasks referencing entities/validation_rules match names in data_model.md.
