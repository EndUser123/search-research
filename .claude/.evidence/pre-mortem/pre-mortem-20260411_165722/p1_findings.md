## Triage Classification
hook — Three stop/pre-tool hooks under optimization review

## Dispatched Specialists
- adversarial-logic: Logic-preserving refactor verification
- adversarial-quality: Tech debt and maintainability
- adversarial-io-validation: File I/O, path validation, race conditions
- adversarial-compliance: Hook registration and exit code handling
- adversarial-security: Terminal isolation, evidence cache, PII handling

## Specialist Findings Summary

### adversarial-logic
**Domain:** Off-by-one, operators, conditionals
**Key findings:**
- No logic errors detected in the three proposed changes
- 3 open questions raised about threshold comparison operators, bare-hook pattern scope, and regex equivalence

### adversarial-quality
**Domain:** Tech debt, maintainability
**Key findings:**
- No significant issues found

### adversarial-io-validation
**Domain:** Path validation, file operations, race conditions
**Key findings:**
- [MEDIUM] IO-001: Hardcoded event limit 25 (should be configurable)
- [MEDIUM] IO-002: Silent failure pattern — evidence load failure silently bypasses drift detection
- [LOW] IO-003: LOG_DIR.mkdir can fail silently at module load
- [HIGH] IO-004: TOCTOU race in _read_pending_state — state file read without locking
- [MEDIUM] IO-005: Multiple sys.path.insert calls causing path accumulation
- [MEDIUM] IO-006: Hardcoded P:-prefixed paths — Windows-specific and fragile
- [LOW] IO-007: Log file write without atomic operation
- [LOW] IO-008: JSON decode without try/except in _read_pending_state

### adversarial-compliance
**Domain:** Hook registration, schema compliance
**Key findings:**
- No significant issues found

### adversarial-security
**Domain:** Terminal isolation, PII, cache integrity
**Key findings:**
- [HIGH] SEC-001: Evidence Cache Terminal Isolation Failure — _EVIDENCE_CACHE uses session_id only, ignoring terminal_id. Cross-terminal contamination possible.
- [MEDIUM] SEC-002: Potential None elements in combined events list
- [LOW] SEC-003: Incomplete PII redaction in log sanitization
- [LOW] SEC-004: Exception swallowing in audit logger call
- [INFO] SEC-005: Tool events trust from hook input (low risk given trusted hook runner)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [MEDIUM] (source: adversarial-io-validation) — Hardcoded event limit 25 not configurable (StopHook_drift_sentinel.py:87)

### Hidden Assumptions & Fragile Dependencies
2.1. [HIGH] (source: adversarial-security, adversarial-io-validation) — Terminal isolation violation: _EVIDENCE_CACHE keyed on session_id alone allows cross-terminal evidence contamination. SEC-001 in StopHook_unverified_stance.py:381. IO-004 in PreToolUse_skill_pattern_gate.py:276-298 — TOCTOU race in state file read without locking.
2.2. [MEDIUM] (source: adversarial-io-validation) — Silent failure pattern: evidence load failure returns empty list and bypasses drift detection entirely with no user-visible indication (StopHook_drift_sentinel.py:88-90)
2.3. [LOW] (source: adversarial-security) — Incomplete PII redaction: only claim_text is sanitized; targets and tool_event_ids written directly to logs (StopHook_unverified_stance.py:235)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-security) — Add terminal_id to _EVIDENCE_CACHE key for proper multi-terminal isolation
3.2. [MEDIUM] (source: adversarial-io-validation) — Add try/except around json.loads in _read_pending_state to handle corrupted state files gracefully
3.3. [MEDIUM] (source: adversarial-io-validation) — Add atomic file operations or lock file for _read_pending_state to prevent TOCTOU races

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-io-validation) — If session generates >25 tool events, drift detection operates on truncated stream — false negatives possible (StopHook_drift_sentinel.py:87)
4.2. [MEDIUM] (source: adversarial-io-validation) — Multiple sys.path.insert calls without dedup check — path accumulation in long-running processes (PreToolUse_skill_pattern_gate.py:56, 253, 284, 392, 519)
4.3. [LOW] (source: adversarial-security) — Exception swallowing in audit logger call — audit failures masked (StopHook_unverified_stance.py:69, 255)
4.4. [LOW] (source: adversarial-io-validation) — Log file write without atomic operation — JSONL corruption on power loss or OOM (PreToolUse_skill_pattern_gate.py:324-325)

### Concrete Recommendations
5.1. [HIGH] (source: adversarial-security) — Change _EVIDENCE_CACHE key from session_id to tuple(session_id, terminal_id)
5.2. [MEDIUM] (source: adversarial-io-validation) — Wrap _read_pending_state in try/except JSONDecodeError; add FileNotFoundError handling
5.3. [MEDIUM] (source: adversarial-io-validation) — Use atomic read or locking for state file access in PreToolUse_skill_pattern_gate.py
5.4. [LOW] (source: adversarial-io-validation) — Add environment-variable fallback for event limit: DRIFT_SENTINEL_EVENT_LIMIT
5.5. [LOW] (source: adversarial-security) — Filter None elements after combining events in load_tool_events_for_context
5.6. [LOW] (source: adversarial-security) — Apply path redaction to claim.targets and tool_event_ids before logging

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-logic) — What comparison operator does StopHook_drift_sentinel.py use for event count threshold? If strict inequality (count > 25 vs count >= 25), off-by-one behavior changes at boundary.
6.2. [LOW] (source: adversarial-logic) — What is the bare-hook pattern being removed from overconfidence_detector.py? If it catches Exception vs specific types, scope of caught errors changes.
6.3. [LOW] (source: adversarial-logic) — Was the extract_command_name regex originally different from the one being reused? Behavioral equivalence should be verified.
6.4. [LOW] (source: adversarial-io-validation) — Is P: drive the only supported platform, or should PreToolUse_skill_pattern_gate.py support cross-platform?
