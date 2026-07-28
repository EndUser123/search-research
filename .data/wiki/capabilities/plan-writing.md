---
title: "plan-writing"
node_type: capability
created: 2026-07-28
domain: design
---

# plan-writing

**Inputs:** `spec` (requirements or design doc), `constraints` (list, optional)
**Outputs:** `plan_path` (implementation plan with TDD task format, exact file paths, bite-sized steps)

## Procedure

1. Read the spec/requirements
2. Decompose into ordered tasks (topological sort for dependencies)
3. Each task: file path, what to change, test command, acceptance criteria
4. Write plan to `P:/docs/plans/<slug>.md`

Full spec: `~/.grok/skills/plan-writer/SKILL.md`
