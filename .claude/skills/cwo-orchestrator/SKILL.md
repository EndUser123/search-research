---
name: cwo_orchestrator
description: CWO Orchestrator - Terminal A monitoring for parallel subagent coordination
version: "1.0.0"
status: "stable"
category: orchestration
triggers:
  - /cwo-orchestrator
aliases:
  - /cwo-orchestrator

suggest:
  - /cwo
  - /nse
  - /workflow
---

# /cwo-orchestrator — Terminal A Monitor

## Purpose

Terminal A monitoring for parallel subagent coordination during CWO workflow. Continuous loop reads ORCHESTRATION.md, parses phase status, checks heartbeats, displays progress, and generates launch commands for ready phases.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **Multi-terminal coordination**: Monitor parallel subagents across terminals
- **Evidence-based monitoring**: Parse actual ORCHESTRATION.md, don't assume state
- **Heartbeat detection**: >10 min stale = agent warning

### Technical Context
- **Poll interval**: 30 seconds (customizable via --poll-interval)
- **Phases**: A (Test-Writer), B (Research), C (Implementer), D (Reviewer), E (Docs)
- **Status indicators**: ⏸️ TODO, ▶️ IN_PROGRESS, ✅ DONE, ⚠️ BLOCKED, ⚠️ STALE
- **Dependencies**: A||B → C → D, E → DONE (A&B parallel, E parallel with D)
- **Closure**: Generates closure.json when all phases complete

### Architecture Alignment
- Integrates with /cwo (full workflow), /workflow-status (progress display)
- Links to /nse (next steps based on phase status)
- Part of CWO orchestration ecosystem

## Your Workflow

1. **FIND ACTIVE TSK** — Locate current TaskMaster session
2. **READ ORCHESTRATION.md** — Parse phase definitions and dependencies
3. **START MONITOR LOOP** — Continuous polling (default 30s interval)
4. **PARSE PHASE STATUS** — Read TODO/IN_PROGRESS/DONE/BLOCKED for each phase
5. **CHECK HEARTBEATS** — Detect stale agents (>10 min = warning)
6. **DISPLAY STATUS** — Show progress indicators, current phase, last update
7. **GENERATE LAUNCH COMMANDS** — Provide commands for next ready phase
8. **DETECT COMPLETION** — Generate closure.json when all phases DONE

## Validation Rules

- **Before monitoring**: Verify active TSK session exists
- **Each poll**: Parse actual ORCHESTRATION.md state, don't cache
- **Before launching**: Check phase dependencies are satisfied
- **Stale detection**: Warn if agent heartbeat >10 min old

### Prohibited Actions

- Assuming phase state without reading ORCHESTRATION.md
- Launching phases with unmet dependencies
- Ignoring stale agent warnings
- Skipping heartbeat checks
- Reading agent output inline into the monitor context instead of reading only file paths and status fields
- Launching high-output phases in parallel — stagger so only one large artifact phase runs at a time

## Subagent Output Routing Rules

### Subagent Result Envelope

Every agent this orchestrator monitors must write output to disk and expose a Result Envelope. See canonical spec: `.claude/skills/shared/result-envelope.md`.

```json
{
  "status": "done" | "blocked" | "retry",
  "artifact": "relative/path/to/output/file.ext",
  "summary": "≤3 short lines — no code, no diffs, no large analysis",
  "metrics": { "artifact_bytes": 4821, "files_read": 3 }
}
```

The orchestrator monitor reads only envelopes and status fields; it never inlines full artifact content into its own context.

### Parallelism rules

- Tasks that produce large artifacts (full diffs, complete analyses, module rewrites) are high-output — launch sequentially, wait for Result Envelope before launching the next.
- Tasks that produce only metadata, heartbeat files, or short structured JSON are low-output and may run in parallel.
- When in doubt, treat a phase as high-output.

## Usage

```bash
# Start orchestrator monitor (30 second poll interval)
/cwo-orchestrator

# With custom poll interval
/cwo-orchestrator --poll-interval 60
```

## What Happens

```
/cwo-orchestrator

1. Finding active TSK...
   TSK: TSK-ARCH-TIER1-20260103-075037

2. Reading ORCHESTRATION.md...
   Found: Phases A-E

3. Starting monitor...
   ============================================================
     /cwo ORCHESTRATOR - Terminal A Monitor
   ============================================================

   TSK: TSK-ARCH-TIER1-20260103-075037
   Last Update: 2026-01-05T12:34:56Z
   Current Phase: A

   ## Phase Status

     Phase A (Test Writing - TDD RED) ⏸️ 0/5
     Phase B (Research & Analysis) ⏸️ 0/2
     Phase C (Implementation - TDD GREEN) ⏸️ 0/8
     Phase D (Code Review & Quality Check) ⏸️ 0/3
     Phase E (Documentation Generation) ⏸️ 0/2

   ## Ready to Launch Phases A & B (Parallel)

   ### Terminal B - Test-Writer (Phase A)
   ### Terminal C - Research-Analyst (Phase B)

   Next poll: 12:35:26
```

## Monitor Loop

The orchestrator runs in a continuous loop:

1. **Read ORCHESTRATION.md** (every 30 seconds)
2. **Parse phase status** (TODO/IN_PROGRESS/DONE/BLOCKED)
3. **Check heartbeats** (>10 min = stale agent warning)
4. **Display status** with progress indicators
5. **Generate launch commands** for next ready phase
6. **Detect completion** and generate closure.json

## Status Indicators

| Symbol | Meaning |
|--------|---------|
| ⏸️ TODO | Phase not started |
| ▶️ IN_PROGRESS | Phase actively running |
| ✅ DONE | Phase complete |
| ⚠️ BLOCKED | Phase blocked by dependencies |
| ⚠️ STALE | Agent heartbeat >10 min old |

## Phase Dependencies

```
Phase A (Test-Writer) ─┐
                       ├─→ Phase C (Implementer) ─→ Phase D (Reviewer)
Phase B (Research)     ─┘                              └→ Phase E (Docs) ─→ DONE
```

- **A & B**: Parallel (no dependencies)
- **C**: Waits for A (tests must exist before implementation)
- **D**: Waits for C (code must exist before review)
- **E**: Waits for C (code must exist before docs), runs parallel with D

## See Also

- `/cwo` — Full 16-step workflow orchestration
- `/workflow-status` — Display workflow progress
