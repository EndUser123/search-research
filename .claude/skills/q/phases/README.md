# /q Phase Pipeline Overview

## Architecture

/q executes a 6-phase strategic quality check pipeline following the `/p` skill pattern:
- Single orchestrator (SKILL.md)
- Phase files in `phases/` directory
- Hook-based enforcement (PreToolUse, PostToolUse, Stop)
- Terminal-isolated state tracking

## Pipeline Flow

```
Q1: ScopeResolver → Q2: QuickCollectors → Q3: IssueNormalizer → Q4/Q5: Renderer → Q6: ContextSink
```

| Phase | Name | Purpose | Output |
|-------|------|---------|--------|
| Q1 | ScopeResolver | Determine what to analyze | `scope` object |
| Q2 | QuickCollectors | Gather signals in parallel | `raw_checks` |
| Q3 | IssueNormalizer | Normalize findings + compute mode | `scan_state.mode` |
| Q4 | Strategic Path | Clean output renderer | Strategic priorities |
| Q5 | Problem Renderer | Mixed/problem output + deep analysis | Fix plans |
| Q6 | ContextSink | Persist context for downstream | Handoff JSON |

## Mode Decision Tree

Q3 computes mode based on issue count:
```
0 issues   → strategic mode  → Q4 (clean output)
1-6 issues → mixed mode      → Q5 (fixes + forward steps)
7+ issues  → problem mode    → Q5 (full fix plan + DDD)
```

## Phase Files

- **q1.md** - Scope resolution (session > conversation > git)
- **q2.md** - Parallel collection (architecture, patterns, tech fit, libraries)
- **q3.md** - Issue normalization + mode computation
- **q4.md** - Strategic output for clean runs
- **q5.md** - Mixed/problem output with optional deep analysis
- **q6.md** - Context persistence

## Refactoring History

**March 2026**: Consolidated 7 separate /qN sub-skills into unified phase-based architecture

This refactoring:
- Removed duplicate SKILL.md files (7 → 1)
- Created phase files following `/p` pattern
- Maintained backward compatibility (`/q1`..`/q6` still work)
- Integrated decomposed skills (/triage → Q1, /investigate → Q2, /library-first → Q3, /ddd → Q5)

See individual phase files for "Decomposed from" sections documenting the source.

## GoT + ToT Integration

- **Graph-of-Thought (GoT)**: Requirement constraint analysis (Q3)
- **Tree-of-Thought (ToT)**: Question branching scenarios (Q2, Q4)

See [GoT integration](../docs/got-integration.md) and [ToT integration](../docs/tot-integration.md) for details.

## Hook Architecture

- **PreToolUse**: `PreToolUse_q_phase_gate.py` - Blocks phase skipping
- **PostToolUse**: `PostToolUse_q_state_tracker.py` - Tracks phase completion
- **Stop**: `StopHook_q_completion_validator.py` - Validates completion markers

Hooks enforce terminal-isolated state via `P:/.claude/state/q-pipeline-{terminal_id}.json`
