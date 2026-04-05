---
name: disler_stop
description: Stop disler observability stack services
version: "1.0.0"
status: "stable"
category: development
triggers:
  - /disler-stop
aliases:
  - /disler-stop

suggest:
  - /disler-start
  - /obs
  - /health-monitor
---

# Disler Stop

Stop all disler observability services.

## Purpose

Stop disler observability stack server and client services.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- On-demand execution only
- Non-critical system (hooks fail gracefully when stopped)

### Technical Context
- Stops server on port 4000
- Stops client on port 5173
- Terminates all bun.exe processes
- Event data preserved in apps/server/events.db

### Architecture Alignment
- Part of CSF NIP observability tools
- Complements /disler-start
- Integrates with /health-monitor workflow

## Your Workflow

1. Ensure you have saved any important observations
2. Run /disler-stop to terminate services
3. Verify ports are released
4. Restart with /disler-start when needed

## Validation Rules

- Event data is preserved across stop/start cycles
- Hooks fail gracefully when disler is stopped
- All bun.exe processes terminated

## Usage

```bash
/disler-stop
```

**Stops:**
- Server on port 4000
- Client on port 5173
- All bun.exe processes

## Notes

- Event data is preserved in `apps/server/events.db`
- Events resume when `/disler-start` is invoked
- Hooks fail gracefully when disler is stopped (non-critical)
