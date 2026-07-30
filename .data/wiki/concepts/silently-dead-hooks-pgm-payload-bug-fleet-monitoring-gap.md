---
title: "Silently dead hooks: PGM payload bug went undetected for weeks"
created: 2026-07-29
source: session-019fa48a
tags: [hook-health, fail-open, payload-mismatch, proposal-grounding-monitor, fleet-monitoring]
summary: >
  The proposal-grounding-monitor (PGM) plugin was enabled in config.toml and had
  117 passing tests, but was silently dead at runtime for its entire production life.
  Its stop_detect.py read the wrong payload field name, causing every real session
  to hit an empty-text guard and produce zero detections. No telemetry surfaced this
  because the hook's fail-open behavior produced no errors — just silent non-detection.
  This is a fleet hook-health monitoring gap.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/stop-hook-lastassistantmessage-payload-field-2026.md
    type: extends
  - target: wiki/concepts/multi-subagent-orchestration-workflow-failure-patterns.md
    type: related
---

# Silently dead hooks: PGM payload bug went undetected for weeks

## Decision context

A `/design` run for the search-before-proposing hook discovered that PGM — the existing enforcement mechanism — was silently dead. The plugin was enabled in config.toml (first entry in the `enabled` array), had 117 passing tests, and appeared healthy from the outside. But every real session produced zero detections because the payload extraction function read the wrong field name.

This raised a fleet monitoring question: how do we detect when an enabled, tested hook is silently non-functional at runtime?

## What happened

### The bug

`stop_detect.py:extract_response_text()` checked:
```python
for key in ("response", "last_assistant_message"):
```

But the Grok Build Stop payload provides `lastAssistantMessage` (camelCase), per `user-guide/10-hooks.md:262`. Neither key matched. The function returned `""`, the `detect()` body hit its `if not response: return None` guard, and no proposals were ever detected.

### Why it went undetected

1. **Tests passed.** The test fixture (`conftest.py:make_stop_payload`) used `{"response": text}` — the legacy field name. All 117 tests exercised the fallback tier, not the canonical tier. Tests confirmed the code worked as written, but the code didn't match the runtime payload.

2. **Fail-open produced no errors.** The hook exited 0 (success) on every invocation. No traceback, no stderr, no error log. The plugin appeared healthy in every monitoring surface.

3. **No runtime detection telemetry.** PGM wrote `dispatch_received` events to `stop.jsonl`, but nobody was reading them. There was no alert for "dispatch_received count = 0 across all sessions" or "gate_decision events absent."

4. **README was stale.** PGM's README said "orphaned (not enabled in config.toml)" but config.toml had it as the first enabled plugin. This contradiction delayed diagnosis — the design team wasn't sure whether PGM was even active.

### The systemic pattern

This is the same bug that affected `behavioral_check.py` and `wiki_persistence_check.py` earlier in the same session — three separate hooks with the same camelCase/snake_case field mismatch. The pattern: code written for one payload format (Claude Code snake_case) ported to a different runtime (Grok Build camelCase) without verifying the payload contract.

See [[stop-hook-lastassistantmessage-payload-field-2026]] for the canonical 4-tier extraction pattern that fixes all three hooks.

## What this means for our workspace

### Hook health monitoring gap

There is currently no mechanism to detect silently dead hooks. The fleet needs:

1. **Per-hook heartbeat telemetry.** Each Stop hook should write a `dispatch_received` event on every invocation. An external monitor checks whether each enabled hook has non-zero dispatch events across the last N sessions. If zero, the hook is silently dead.

2. **Test fixture = runtime contract.** Test helpers like `make_stop_payload` must use the canonical runtime field, not a legacy fallback. The conftest fix (PGM-002) updated the fixture, but this principle applies to every hook with a test suite.

3. **Stale README detection.** PGM's README claimed "orphaned" while config.toml enabled it. README claims about enablement state should be derived from config, not hand-maintained. A simple `grep "plugin-name" config.toml` would have caught this.

### The three-hooks-same-bug incident

Three independent hooks (`behavioral_check.py`, `wiki_persistence_check.py`, `proposal-grounding-monitor/stop_detect.py`) all had the same `lastAssistantMessage` field mismatch. This is not a coincidence — it's a systematic pattern from porting Claude Code hook code to Grok Build without verifying the payload contract.

**Prevention:** any new Stop hook should be tested against a real payload captured from the runtime, not a synthetic one constructed from documentation assumptions. A "payload capture" utility that writes the actual stdin JSON to a temp file on first invocation would let test fixtures use real payloads.

### Broader implication: the test-runtime contract gap

The root issue is that test fixtures and runtime payloads can diverge silently. Tests pass because the fixture provides the field the code expects. Runtime fails because the actual payload provides a different field. This is not caught by:
- Unit tests (they use the fixture)
- Integration tests (they also use the fixture)
- Type checking (payloads are `dict[str, Any]`)
- Linting (no static analysis for field-name mismatches across a process boundary)

The only detection mechanism is **runtime telemetry**: the hook writes what it actually received, and a monitor checks whether the received data matches expectations. PGM had telemetry infrastructure (`stop.jsonl`) but nobody was reading it. The gap is not "no telemetry" — it's "telemetry exists but no consumer validates it."

This connects to the broader pattern in [[enforcement-hierarchy-and-compaction-strategy]]: the enforcement hierarchy classifies "is the hook actually running?" as a hook-level concern, but the detection of silent failure requires a meta-monitor that sits above individual hooks. That meta-monitor does not exist yet.

## Falsifier

This fleet monitoring gap is resolved when:
- A hook-health monitor exists that would have detected PGM's zero-detection state within 1 session
- The three hooks that had the payload bug have been running live for ≥1 session without silent failure
- A payload-capture utility exists for new hooks to validate against real runtime payloads

If after 30 days of live PGM operation the detection rate is non-zero and stable, the "silently dead" state is confirmed as fixed.

## Receipts

- `~/.grok/plugins/proposal-grounding-monitor/scripts/stop_detect.py:64` — the bug (verified by direct read)
- `~/.grok/plugins/proposal-grounding-monitor/tests/conftest.py:64` — test fixture using wrong field (verified, fixed in commit `0ab0e09`)
- `~/.grok/docs/user-guide/10-hooks.md:262` — documented field name (verified by direct read)
- `~/.grok/config.toml:120` — PGM enabled (verified by grep)
- `~/.grok/plugins/proposal-grounding-monitor/README.md` — stale "orphaned" claim (verified by read)
- Commit `0f5ce16` — the fix
- Commit `6cfc5fb` — PGM-001 + PGM-003 fixes (SDK compat + content blocks)
- `~/.grok/hooks/state/behavioral-check-log.jsonl` — 42 detections showing the same pattern in behavioral_check.py (verified by analysis)

## Related concepts

- [[stop-hook-lastassistantmessage-payload-field-2026]] — the canonical extraction pattern that fixes all three hooks
- [[multi-subagent-orchestration-workflow-failure-patterns]] — same session, skill design patterns
- [[regex-cannot-detect-context-dependent-behavioral-patterns]] — same session, behavioral detection limits
- [[enforcement-hierarchy-and-compaction-strategy]] — the enforcement hierarchy that classifies hook-health monitoring
- [[mechanical-enforcement-over-behavioral-reminder]] — why mechanical monitoring beats hoping someone checks
