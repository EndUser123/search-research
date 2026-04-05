# Hook Logging & Observability System - Review Bundle

## Generated Location
`P:\.claude\reviews\hook_observability.md`

## Overview
Comprehensive architectural review of hook logging and observability for Claude Code. Consolidates 40+ hooks into 9 routers with event tracking, diagnostic logging, and notifications.

## Execution Map
```
User Prompt → UserPromptSubmit Router (19 hooks → 1)
    ├─→ TDD Eval, Concern Detection, Unified Injector
    └─→ Context Injection

Tool Use → PreToolUse / PostToolUse Routers
    ├─→ Pre: TDD Blocker, Deny Root Write, Safety Gates
    └─→ Post: Failure Escalation, Poka-Yoke, Tool Tracker

Response → Stop Router
    ├─→ Success Validator
    ├─→ Empirical Claims Gate
    └─→ Artifact Gate

All Hooks → Observability
    ├─→ Performance Tracker
    ├─→ CC Diagnostic Logger
    ├─→ Event Queue → SQLite Database
    └─→ Notification Queue
```

## Source Code

### P:\.claude\hooks\UserPromptSubmit_router.py
[461 lines - consolidates 19 hooks into 1 process, ~800ms savings per prompt]

### P:\.claude\hooks\performance_tracker.py
[161 lines - decorator for tracking hook execution timing and output size]

### P:\.claude\hooks\cc_diagnostic_logger.py
[466 lines - centralized logging infrastructure with 5 log files]

### P:\.claude\hooks\sendevent.py
[289 lines - event database handler with batch processing]

### P:\.claude\hooks\event_queue.py
[135 lines - on-demand event batching, C.1 compliant]

### P:\.claude\hooks\notification_queue.py
[190 lines - terminal-scoped user notifications]

### P:\.claude\hooks\hook_bridge.py
[250 lines - W3C tracecontext propagation adapter]

### P:\.claude\hooks\PostToolUse_all_router.py
[180 lines - universal PostToolUse consolidation]

### P:\.claude\hooks\Stop_router.py
[248 lines - response validation router]

## External Dependencies

### Environment Variables
- CC_DIAGNOSTICS_ENABLED - Enable/disable logging (default: true)
- CC_DIAGNOSTICS_DIR - Log directory (default: P:/.claude/hooks/logs/diagnostics)
- ROUTER_DEBUG - Router debug output (default: false)
- TRACEPARENT - W3C trace context for distributed tracing

### Data Files
- ~/.claude/events.db - SQLite database for constitutional events
- ~/.claude/notifications.json - User notifications queue
- P:/.claude/hooks/logs/diagnostics/*.jsonl - Structured logs

### Python Dependencies
Standard library only: json, sqlite3, subprocess, pathlib, threading, time, datetime, hashlib, uuid

### Optional Integrations
- CKS (Chat Knowledge System) - Historical context injection
- CHS (Chat History Search) - Transcript search
- TaskMaster - Task artifact tracking

## Performance
- UserPromptSubmit: ~100ms (vs ~900ms pre-consolidation)
- Log growth: ~1KB per prompt, 50MB rotation threshold
- RAM: <50MB per session
