---
name: disler_start
description: Start disler observability stack server and client
version: "1.0.0"
status: "stable"
category: development
triggers:
  - /disler-start
aliases:
  - /disler-start

suggest:
  - /disler-stop
  - /health-monitor
  - /obs
---

# Disler Start

Start the disler observability stack - server and client services.

## Purpose

Start disler observability stack server and client for hook event monitoring and visualization.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- On-demand execution (background tasks with idle timeout)
- Non-critical system (hooks fail gracefully when stopped)

### Technical Context
- Server on port 4000 receives events from hooks
- Client on port 5173 provides dashboard
- Bun runtime for TypeScript services
- SQLite database for event storage

### Architecture Alignment
- Part of CSF NIP observability tools
- Integrates with hooks system
- Supports /health-monitor and /obs workflows

## Your Workflow

1. Ensure port 4000 and 5173 are available
2. Run /disler-start to create background tasks
3. Access dashboard at http://localhost:5173
4. View events at http://localhost:4000/events/recent
5. Use /disler-stop when done

## Validation Rules

- Check for port conflicts before starting
- Verify bun.exe is available
- Tasks run in background (non-blocking)
- Event data preserved in apps/server/events.db

## Quick Reference

| Service | Port | Purpose |
|---------|------|---------|
| Server | 4000 | Receives events from hooks |
| Client | 5173 | Dashboard for viewing events |

## Usage

```bash
/disler-start
```

**Background tasks created:**
- Server: Runs `bun run src/index.ts` in observability/apps/server
- Client: Runs `bun run dev` in observability/apps/client

## Locations

- Install: `P:/__csf/tools/claude-code-hooks-multi-agent-observability`
- Bun binary: `P:/__csf/tools/bun/bun-windows-x64/bun.exe`
- Database: `apps/server/events.db`

## Troubleshooting

If port conflicts:
```bash
taskkill //F //IM bun.exe
/disler-start
```

If dashboard doesn't load:
- Check http://localhost:4000/events/recent
- Verify server task is running
