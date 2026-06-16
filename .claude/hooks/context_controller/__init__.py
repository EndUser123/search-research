"""Context controller: thin policy layer over the snapshot plugin.

Phases 1-3 of the 2026-06-07 context-controller plan:

- `state.py`   - envelope reader + policy.json I/O (atomic, per-terminal)
- `policy.py`  - deterministic phase classification + context-health evaluation
- `render.py`  - compact packet rendering for compact/session-start injection

Hook wiring (Phases 4-7) is intentionally NOT in this package yet.
"""
