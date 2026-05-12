#!/usr/bin/env python3
"""Analyze Stop telemetry for Phase 2 category-aware enforcement model."""
from pathlib import Path
import json

stop_log = Path(r'P:/.claude/hooks/logs/diagnostics/task_contract_telemetry.jsonl')
events = []
with stop_log.open(encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

print(f"Total events: {len(events)}")
recent = events[-100:]
print(f"Last 100: {len(recent)}")

# All event types
event_types = {}
for e in recent:
    event_types[e.get('event', '?')] = event_types.get(e.get('event', '?'), 0) + 1
print("\n=== Event types ===")
for k, v in sorted(event_types.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}  {k}")

# Reason codes per event type
for evt in ['silent', 'check', 'block', 'auto_clear', 'autoclear']:
    reasons = {}
    for e in recent:
        if e.get('event') == evt:
            r = e.get('reason', '')
            reasons[r] = reasons.get(r, 0) + 1
    if reasons:
        print(f"\n=== {evt} reasons ===")
        for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"  {v:3d}  [{k}]")

# Turn modes
turn_modes = {}
for e in recent:
    tm = e.get('turn_mode', '')
    turn_modes[tm] = turn_modes.get(tm, 0) + 1
print("\n=== Turn modes ===")
for k, v in sorted(turn_modes.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}  [{k}]")

# Contract present
cp = {}
for e in recent:
    v = str(e.get('contract_present', '?'))
    cp[v] = cp.get(v, 0) + 1
print("\n=== contract_present ===")
for k, v in sorted(cp.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}  [{k}]")
