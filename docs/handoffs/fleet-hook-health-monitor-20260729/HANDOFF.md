# Handoff: Fleet Hook-Health Monitor

**Status:** OPEN — design needed, not started. Surfaced from the PGM silently-dead incident.
**Date:** 2026-07-29
**Source:** session 019fa48a, wiki concept `silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap`

## Problem

PGM was enabled in config.toml, had 117 passing tests, and was silently dead at runtime for its entire production life. Its `extract_response_text()` read the wrong payload field name, causing every real session to hit an empty-text guard and produce zero detections. No monitoring caught this because:

1. The hook exited 0 (success) on every invocation — fail-open produced no errors
2. Tests used a test fixture (`conftest.py:make_stop_payload`) with the wrong field name — tests confirmed the code worked as written, but the code didn't match the runtime payload
3. PGM wrote `dispatch_received` events to `stop.jsonl` telemetry, but nobody was reading them
4. PGM's README said "orphaned" while config.toml had it enabled as the first plugin

This is not unique to PGM — any Stop hook with a fail-open design can be silently dead without anyone knowing.

## Objective

Build a lightweight fleet hook-health monitor that detects silently dead hooks within 1 session of failure.

## Acceptance criteria

1. The monitor checks each enabled Stop/PostToolUse hook for non-zero dispatch events across the last N sessions
2. If a hook has zero dispatch events across ≥3 sessions, it surfaces as "silently dead"
3. The monitor runs as a `/workspace-health` check (extends existing skill) or a SessionStart hook
4. The monitor does NOT require any change to individual hooks — it reads existing telemetry
5. False positive rate <10% (a hook that legitimately never fires because the agent never triggers its condition should not be flagged)

## Design questions

- **Where does it run?** Options: (a) `/workspace-health` check, (b) SessionStart hook, (c) `/maintain` diagnostic, (d) standalone script run by operator
- **What telemetry does it read?** PGM writes `stop.jsonl`; behavioral_check writes `behavioral-check-log.jsonl`; quality_gate writes its own state files. Each hook has different telemetry. The monitor needs a registry of "what telemetry each hook produces" and "what a healthy dispatch count looks like."
- **What about hooks with no telemetry?** Hooks like `dbr_language_check.py` and `dbr_file_check.py` don't write telemetry files. The monitor can only check hooks that produce observable output. This is itself a finding — hooks without telemetry are undetectable.

## Approach

1. Inventory all enabled hooks and their telemetry outputs
2. Build a registry mapping: hook → telemetry file → expected event types → minimum healthy dispatch rate
3. Write a scanner that checks each registry entry against actual telemetry
4. Surface "silently dead" hooks in `/workspace-health` or `/maintain`

## Dependencies

- None blocking. Can start independently.
- The PGM Unit 3 (fp_measurement telemetry) will add a new telemetry source to monitor.

## Related

- Wiki concept: `silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap`
- Wiki concept: `stop-hook-lastassistantmessage-payload-field-2026`
- PGM handoff: `pgm-payload-fix-and-scope-extension-20260729`
