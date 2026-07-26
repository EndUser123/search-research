---
title: "Parallel-Safe Solution Decomposition: DSM + Critical Path + Completeness Verification"
created: 2026-07-20
source: session-2026-07-20 (/www research on parallel decomposition mental models)
tags: [decomposition, parallel-execution, critical-path, design-structure-matrix, completeness, design-skill, go-skill]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Three established frameworks answer the question "decompose steps, find
  parallelism without quality loss, verify completeness." The Design Structure
  Matrix (DSM) maps dependencies and algorithmically partitions tasks into
  parallel/sequential/coupled groups. The Critical Path Method (CPM) identifies
  the longest dependency chain and the tasks with slack. Wardley Mapping adds
  evolutionary context (which components are stable vs. evolving). Together they
  form a complete decomposition methodology. Our `/go` and `/design` skills
  already implement a lightweight version (H4 parallel wave, grok-parallel).
  The missing piece is the completeness verification — a checklist that
  confirms the decomposed pattern retains all necessary components.
relations:
  - target: wiki/concepts/design-doc-spec-system-patterns
    type: related
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: related
---

## Summary

The user asked for a mental model that (1) decomposes all steps, (2) identifies what can run in parallel without quality loss, and (3) verifies the resulting pattern has all necessary components. Three established frameworks answer different parts of this question:

| Framework | What it solves | Origin |
|---|---|---|
| **Design Structure Matrix (DSM)** | Step 1 (decompose) + Step 2 (find parallelism) — maps dependencies into a square matrix, then algorithmically partitions into parallel/sequential/coupled groups | MIT, 1960s; formalized by Steward 1981 |
| **Critical Path Method (CPM)** | Step 2 (find parallelism) — identifies the longest dependency chain; tasks not on the critical path have slack and can run in parallel | DuPont, 1957 |
| **Completeness Checklist** | Step 3 (verify all components) — derived from Spec Kit's template checklists and our own design_lint.py pattern | GitHub Spec Kit, 2026 |

## The Design Structure Matrix (DSM)

The DSM is the most directly applicable framework. It's a square N×N matrix where:
- Rows and columns represent tasks/components
- An `X` in cell (i,j) means task i depends on task j (or receives input from j)
- The matrix reveals three relationship types:
  - **Parallel** (empty rows/columns): tasks are independent and can run concurrently
  - **Sequential** (marks only above or below diagonal): one-way dependency; task B must wait for task A
  - **Coupled** (marks both above and below diagonal): circular dependency; tasks must be done together iteratively

### The partitioning algorithm (Steward's path searching)

1. Activities with empty rows (no inputs) go first — order at top
2. Activities with empty columns (no outputs) go last — order at bottom
3. Find cycles in remaining elements via depth-first search
4. Group cyclic activities together as a single coupled step
5. Result: an upper-triangular matrix with minimal feedback loops

This is exactly what `/go`'s H4 parallel wave does informally: identify independent tasks, dispatch them in parallel, and group coupled tasks. The DSM makes it formal.

### Applied to our `/design` skill

The design-review workflow decomposed as a DSM:

| Task | Write | Lint | Review-Arch | Review-Enforce | Review-Depth | Revise | Consistency | Re-review | CritFriend |
|---|---|---|---|---|---|---|---|---|---|
| **Write** | W | | | | | | | | |
| **Lint** | ← | L | | | | | | | |
| **Review-Arch** | ← | ← | R | | | | | | |
| **Review-Enforce** | ← | | | R | | | | | |
| **Review-Depth** | ← | | | | R | | | | |
| **Revise** | | ← | ← | ← | ← | V | | | |
| **Consistency** | | | | | | ← | C | | |
| **Re-review** | | | | | | ← | ← | R | |
| **CritFriend** | | | | | | ← | | | C |

**Reading the DSM:** Write must happen first (everything depends on it). Lint depends on Write. The three reviewers all depend on Write + Lint but NOT on each other — they're parallel. Revise depends on all three reviewers. Consistency depends on Revise. Re-review depends on Revise + Consistency. CritFriend depends on Re-review.

**Parallel groups identified by DSM partitioning:**
- Group 1: Write (sequential, alone)
- Group 2: Lint (sequential, after Write)
- Group 3: Review-Arch, Review-Enforce, Review-Depth (parallel, after Lint)
- Group 4: Revise (sequential, after all reviews)
- Group 5: Consistency sweep (sequential, after Revise)
- Group 6: Re-review (sequential, after Consistency)
- Group 7: Critical friend (sequential, after Re-review)

**Coupled tasks:** None — the workflow is acyclic. If it weren't (e.g., if the reviewer's findings could trigger new domain research), those two tasks would be coupled and would need to run iteratively.

## The Critical Path Method (CPM)

CPM identifies the longest chain of dependent tasks (the "critical path"). Tasks not on the critical path have "slack" — they can take longer without delaying the overall timeline.

For our design-review workflow:
- **Critical path:** Write → Lint → Review-Arch → Revise → Consistency → Re-review → CritFriend
- **Tasks with slack:** Review-Enforce (36s) and Review-Depth (100s) run in parallel with Review-Arch (191s). They finish first but must wait for Review-Arch before Revise can start.
- **Implication:** the wall-clock time is limited by the slowest reviewer (191s), not the sum of all reviewers (327s). This is exactly what we observed.

## The Completeness Verification

This is the piece our skills are missing. DSM tells you what can be parallel; CPM tells you what's on the critical path; but neither confirms the decomposed pattern retains all necessary components.

### What "completeness" means for a decomposed workflow

After decomposing into parallel groups, verify:

1. **Every required step is assigned to exactly one group** (no gaps)
2. **Every dependency edge in the DSM is respected** (no task starts before its inputs are ready)
3. **Every parallel group has a defined merge point** (where do results converge?)
4. **Every merge point has a defined merge strategy** (how are findings consolidated?)
5. **The critical path produces the required output** (does the final step actually emit the deliverable?)
6. **No parallel task duplicates work done by another** (no redundant computation)
7. **Failure of any single parallel task doesn't corrupt the whole** (graceful degradation)

### The checklist as code

Our `design_lint.py` already implements #1 (required sections present) and #6 (naming consistency detects duplicates). The remaining checks are:
- #2-3: the orchestrator's dispatch manifest (which we saw in `/red-team`)
- #4: the critic's consolidation step
- #5: the final report
- #7: the "DEFERRED" pattern from `/red-team`

## Should we implement this in our skills?

### What we already have

| DSM/CPM concept | Our implementation | Quality |
|---|---|---|
| Task decomposition | `/go` H4 parallel wave + `/grok-parallel` skill | Informal — no DSM matrix, just heuristic grouping |
| Parallel dispatch | `spawn_subagent` with `background: true` | Good — native parallelism |
| Dependency tracking | Todo list with status tracking | Basic — no formal dependency graph |
| Critical path awareness | `/go` Step 5 ("adaptive") — enable H4 when multi-file becomes clear | Reactive — doesn't compute the path up front |
| Completeness check | `design_lint.py` + `/close` 13 gates | Partial — checks structure, not workflow completeness |
| Merge strategy | Orchestrator reads all findings, consolidates manually | Manual — no defined merge protocol |

### What's missing (and worth building)

| Gap | Impact | Effort |
|---|---|---|
| **Dependency graph before dispatch** | Would prevent launching a subagent before its inputs are ready | Medium — the orchestrator already knows dependencies; formalize them |
| **Completeness checklist per workflow type** | Would catch missing steps (like the skipped critical friend in this session) | Low — adapt `design_lint.py` to check workflow completion, not just document structure |
| **Defined merge protocol for parallel findings** | Would prevent the "I trusted the reviewer's verdict without reading" failure | Low — one paragraph in each skill that dispatches parallel agents |
| **CPM-aware timeout setting** | Would set per-task timeouts based on whether the task is on the critical path (longer) or has slack (shorter) | Medium — requires knowing task durations from telemetry |

### Recommendation

**Implement the completeness checklist.** It's the highest-impact, lowest-effort gap. The DSM and CPM concepts are useful as mental models for the orchestrator when deciding how to decompose work, but they don't need to be formalized as code — the orchestrator (the LLM) can apply them heuristically, as it already does in `/go`'s H4 wave. What needs to be formalized is the verification that the decomposition didn't miss anything.

The implementation: add a **workflow completeness check** to each skill that dispatches parallel agents. The check runs after dispatch and before merge:

```python
def verify_workflow_completeness(workflow_type, dispatched_tasks, required_steps):
    """Verify all required steps are covered by dispatched tasks."""
    missing = required_steps - {t.role for t in dispatched_tasks}
    if missing:
        return {"complete": False, "missing": missing}
    return {"complete": True}
```

For `/design`: required_steps = {write, lint, review, revise, consistency_sweep, re_review, critical_friend}
For `/go`: required_steps = {safe_git, route, discover, plan, implement, verify}
For `/red-team`: required_steps = {planner, claim_refuter, gate_reviewer, workflow_reviewer, critic}

Each skill defines its required steps; the check runs before the merge point. If a step is missing, the orchestrator is warned — not blocked (the LLM may have intentionally skipped it), but warned.

## Sources

- Design Structure Matrix: https://dsmweb.org/introduction-to-dsm/
- DSM for software architecture: https://sookocheff.com/post/dsm/improving-software-architecture-using-design-structure-matrix/
- DSM MIT lecture: https://ocw.mit.edu/courses/esd-36-system-project-management-fall-2012/
- Critical Path Method: https://en.wikipedia.org/wiki/Critical_path_method
- Wardley Mapping: https://www.wardleymaps.com/
- Value Stream Mapping: https://www.atlassian.com/continuous-delivery/principles/value-stream-mapping
- GitHub Spec Kit (template checklists as completeness verification): https://github.com/github/spec-kit

## Auto-related

- [[python-behavior-tree-framework-for-autonomous-llm-agents--technical-specificatio]]

