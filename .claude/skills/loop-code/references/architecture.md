# Architecture

## Loop Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ /loop-code Skill                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Detect      │───→│ Read State   │───→│ Load Config  │  │
│  │ terminal_id │    │ (state_mgr)  │    │ (loop_policy)│  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         │                                      │           │
│         │         ┌──────────────┐             │           │
│         └────────→│ Parse Plan   │←────────────┘           │
│                   │ (loop_policy)│                         │
│                   └──────────────┘                         │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Execute /code│                          │
│                   └──────┬──────┘                          │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Update State│                          │
│                   │ + Log Event │                          │
│                   └──────┬──────┘                          │
│                          │                                 │
│                   ┌──────┴──────┐                          │
│                   │ Check Exit  │                          │
│                   │ (should_exit)│                         │
│                   └──────┬──────┘                          │
│                          │                                 │
│               ┌──────────┴──────────┐                      │
│               │                     │                      │
│          Exit true             Exit false                  │
│               │                     │                      │
│          ┌────┴────┐         ┌─────┴─────┐               │
│          │  EXIT   │         │  CONTINUE  │               │
│          └─────────┘         └───────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## File Layout

```
~/.claude/state/terminals/<terminal_id>/
├── loop_state.json          # Current loop state (validated)
├── loop_metrics.json        # Performance metrics (best-effort)
└── logs/
    └── decision.log         # Decision log (JSON lines)
```

## Module Dependencies

- **Policy module**: `P:/packages/loop-core/scripts/loop_policy.py`
- **Observability module**: `P:/packages/loop-core/scripts/loop_observability.py`
- **State manager**: `P:/packages/loop-core/scripts/state_manager.py`
- **Plan parser**: `P:/packages/loop-core/scripts/plan_parser.py`
- **Config schema**: `P:/packages/loop-core/scripts/config_schema.py`
- **Documentation**: `P:/packages/loop-core/README.md`, `P:/packages/loop-core/ARCHITECTURE.md`
