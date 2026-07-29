---
title: "persistent-task-store"
node_type: capability
created: 2026-07-28
domain: fleet-ops
---

# persistent-task-store

**Inputs:** task subject/description (Problem/Situation/Symptom schema)
**Outputs:** task JSON at ~/.claude/tasks/project-main-tasks/

## Procedure

Write/read/update JSON files. Persist across sessions. All agents see same data.
