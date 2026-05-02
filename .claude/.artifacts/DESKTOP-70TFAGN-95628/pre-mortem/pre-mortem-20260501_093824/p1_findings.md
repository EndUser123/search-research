## Triage Classification
code — Python service (bf_v3_service.py) + skill (bf SKILL.md v4.0.0)

## Dispatched Specialists
- adversarial-logic: LangGraph flow, termination conditions, mode dispatch
- adversarial-security: API key handling, path traversal, JSON execution
- adversarial-io-validation: path validation, file I/O, HTTP calls, response validation
- adversarial-compliance: API schema, port binding, mode validation consistency

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pure logic, control flow, termination
**Key findings:**
- [BLOCKER] (LOGIC-001): compare mode missing from VALID_RUN_MODES — HTTP 400 on all compare dispatches
- [HIGH] (LOGIC-002): empty/whitespace model names pass list validation, create invalid worker nodes
- [MEDIUM] (LOGIC-003): unreachable error fallback chain ('unknown error' is always truthy)
- [LOW] (LOGIC-004): CodeRequest.mode field unused

### adversarial-security
**Domain:** Auth, secrets, injection, path guards
**Key findings:**
- [HIGH] (SEC-001): TOCTOU in _resolve_allowed_path — symlink can be swapped between check and actual file op
- [HIGH] (SEC-002): raw model JSON output executed as tool actions without schema validation — prompt injection vector
- [MEDIUM] (SEC-003): API key potentially logged via str(e) in exception handler
- [MEDIUM] (SEC-004): /health discloses BF_ALLOWED_ROOT and internal config to unauthenticated clients
- [LOW] (SEC-005): mkdir(parents=True) allows arbitrary directory creation within allowed root

### adversarial-io-validation
**Domain:** I/O operations, path validation, HTTP responses
**Key findings:**
- [HIGH] (IO-001): BF_ALLOWED_ROOT never validated to exist at startup — misconfiguration passes silently
- [HIGH] (IO-003): tool_write_file calls mkdir outside the containment check window
- [MEDIUM] (IO-002): resolved path and BF_ALLOWED_ROOT checked on different Path objects — symlink/junction bypass window
- [MEDIUM] (IO-004): Bifrost response content not validated — malformed responses return empty text silently
- [MEDIUM] (IO-006): glob builds full list before applying containment filter — memory + silent discard
- [LOW] (IO-005): timeout=0 from env var causes indefinite hangs
- [LOW] (IO-007): log_event JSON serialization can raise TypeError from non-serializable extra fields

### adversarial-compliance
**Domain:** API contracts, schema, port binding
**Key findings:**
- [HIGH] (COMP-001): SKILL.md routes to port 8091; service binds to default port 8000 — all dispatches fail connection refused
- [HIGH] (COMP-002): VALID_RUN_MODES missing compare/code — consistent with separate endpoints but undocumented
- [MEDIUM] (COMP-003): CompareRequest.mode accepted but never used
- [LOW] (COMP-004): enforcement: advisory field is inert
- [LOW] (COMP-005): CompareRequest.models not validated against VALID_MODELS
- [LOW] (COMP-006): CodeRequest.mode is str not Literal, accepted but unused

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [BLOCKER] (source: adversarial-logic COMP-001+adversarial-compliance COMP-001) — Port mismatch and mode validation gap combine to make /bf completely non-functional. SKILL.md routes to 8091; service binds 8000. VALID_RUN_MODES excludes compare. Both must be fixed for any dispatch to succeed.

### Hidden Assumptions & Fragile Dependencies
2.1. [HIGH] (source: adversarial-security SEC-001 + adversarial-io-validation IO-001,IO-002,IO-003) — TOCTOU path traversal is a multi-specialist confirmed systemic issue. The path guard is check-then-act on resolved paths with a race window. Combined with mkdir outside the check, SEC-001+IO-003 create a path-escape vector.
2.2. [HIGH] (source: adversarial-security SEC-002) — Model output treated as trusted JSON. The code agent loop passes raw model text to json.loads then executes actions. If model output is attacker-controlled (prompt injection or compromised model), arbitrary file ops follow.
2.3. [MEDIUM] (source: adversarial-io-validation IO-004) — Bifrost response validation absent. Silent empty text on malformed response could mask injection or manipulation.

### Missing Obvious Actions / Best Practices
3.1. [BLOCKER] (source: adversarial-compliance COMP-001) — Port binding must be configured for 8091 or SKILL.md updated. Without this, zero requests succeed.
3.2. [HIGH] (source: adversarial-security SEC-001, IO-001) — Startup validation for BF_ALLOWED_ROOT existence + type check missing. Add at module init: assert BF_ALLOWED_ROOT.exists() and BF_ALLOWED_ROOT.is_dir().
3.3. [HIGH] (source: adversarial-logic LOGIC-001) — 'compare' missing from VALID_RUN_MODES. Add to VALID_RUN_MODES set.
3.4. [MEDIUM] (source: adversarial-security SEC-003) — API key sanitization missing from error logging. Strip Bearer tokens from exception messages before log_event.
3.5. [MEDIUM] (source: adversarial-compliance COMP-003, COMP-005) — CompareRequest.mode dead field; models not validated. Clean up or implement.

### Risks and Edge Cases
4.1. [HIGH] (source: adversarial-security SEC-002) — Prompt injection in code agent loop. Model JSON output executes directly without schema validation.
4.2. [MEDIUM] (source: adversarial-io-validation IO-006) — Glob collects full results before filtering. Large directories cause memory pressure.
4.3. [MEDIUM] (source: adversarial-io-validation IO-005) — timeout=0 silently accepted. Infinite hang on all Bifrost calls.
4.4. [MEDIUM] (source: adversarial-security SEC-004) — /health discloses security config to unauthenticated clients.

### Concrete Recommendations
5.1. (source: adversarial-compliance COMP-001) — Add uvicorn port binding to bf_v3_service.py: `uvicorn.run(app, host="127.0.0.1", port=8091)`
5.2. (source: adversarial-logic LOGIC-001) — Add 'compare' to VALID_RUN_MODES
5.3. (source: adversarial-security SEC-001+IO-001) — Add startup validation: `assert BF_ALLOWED_ROOT.exists() and BF_ALLOWED_ROOT.is_dir()`
5.4. (source: adversarial-security SEC-002) — Add Pydantic model for tool actions with Literal action whitelist
5.5. (source: adversarial-security SEC-003) — Sanitize error messages before logging
5.6. (source: adversarial-logic LOGIC-002) — Filter empty/whitespace model names: `models = [m for m in (req.models or DEFAULT_MODELS) if m and m.strip()]`
5.7. (source: adversarial-security SEC-004) — Remove sensitive fields from /health response

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-logic) — Is LangGraph Send fan-out verified to wait for ALL parallel workers before synthesize? Needs integration test with slow model.
6.2. [LOW] (source: adversarial-compliance COMP-004) — enforcement: advisory field in SKILL.md — is this intentionally inert or should it be removed?
6.3. [LOW] (source: adversarial-io-validation IO-002) — Does Windows junction/symlink behavior on BF_ALLOWED_ROOT affect the TOCTOU window in practice?
