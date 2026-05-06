# Phase 1 Findings — bf skill improvements

## Triage Classification
**skill** — A Claude Code skill (SKILL.md) backed by a Python library (bf_agent.py). Changes span routing, discovery, and route management functions.

## Dispatched Specialists
- **adversarial-critic**: Meta-analysis of consensus, blind spots, contradictions across Phase 1
- **adversarial-compliance**: YAML frontmatter, default mismatches, API contracts, port configuration
- **adversarial-quality**: Tech debt, maintainability, structural issues
- **adversarial-security**: API key handling, SQL injection, auth, file write sanitization
- **adversarial-io-validation**: Module import paths, path resolution, pre-flight checks

## Specialist Findings Summary

### adversarial-critic
**Domain:** Meta-analysis across all other specialists
**Key findings:**
- CRITICAL consensus: API key written to stdout logs via log_event() (SEC-001)
- HIGH consensus: SQL injection via f-string in add_route() (SEC-002)
- HIGH consensus: No auth on local Bifrost HTTP (SEC-003)
- MEDIUM consensus: File write without sanitization (SEC-004)
- LOW consensus: No audit trail for route changes (SEC-005)
- HIGH blind spot: VALID_MODELS removal leaves no fallback validation if Bifrost is unreachable

### adversarial-compliance
**Domain:** Config consistency, API contracts, defaults
**Key findings:**
- COMP-001 [HIGH]: Default model mismatch — run_simple() hardcodes DSv4-flash, SKILL.md says M27
- COMP-002 [HIGH]: BIFROST_BASE_URL=8081 vs BIFROST_HTTP_PORT=8080 — two different services
- COMP-003 [MEDIUM]: run_code max_turns has redundant fallback logic vs module-level BF_CODE_MAX_TURNS
- COMP-004 [MEDIUM]: add_route idempotency doesn't re-enable disabled rules
- COMP-005 [LOW]: delete_route has no explicit transaction wrapping

### adversarial-quality
**Domain:** Tech debt, maintainability
**Key findings:**
- QUAL-001 [MEDIUM]: DB path hardcoded in 4 separate locations — no shared constant
- QUAL-002 [MEDIUM]: No validation of max_turns parameter in run_code()
- QUAL-003 [LOW]: tool_read_file() calls read_text() twice (line 660 waste + line 661 real)
- QUAL-004 [LOW]: delete_route() silently returns on failure — no log_event on exception

### adversarial-security
**Domain:** Auth, injection, data exposure
**Key findings:**
- SEC-001 [CRITICAL]: BIFROST_VK (API key) included in log_event() JSON to stdout — any stdout capture exposes the key
- SEC-002 [HIGH]: f-string `f'model == "{model}"'` in add_route() allows quote injection — CEL expression stored without escaping, could break Bifrost routing or bypass duplicate check
- SEC-003 [HIGH]: Bifrost HTTP on localhost has no local auth — any local process can trigger LLM calls
- SEC-004 [MEDIUM]: tool_write_file() writes raw content with no CRLF/null-byte sanitization
- SEC-005 [LOW]: No user/session identity in log events for route add/delete

### adversarial-io-validation
**Domain:** Import paths, path resolution, file existence
**Key findings:**
- IO-001 [BLOCKER — INCORRECT]: Claims bf_agent module does not exist. bf_agent.py exists at P:/tools/mcp/bf_agent.py (verified by test suite at P:/tests/test_bf_agent.py). Agent searched skills/bf/ instead of the actual module path.
- IO-002 [BLOCKER — INCORRECT]: Claims bf_agent.py not found anywhere. File exists at P:/tools/mcp/bf_agent.py. Same lookup error as IO-001.
- IO-003 [HIGH]: P:/ hardcoded in PowerShell path — fragile if installation root changes
- IO-004 [MEDIUM]: No pre-flight daemon reachability check before probe_routes()

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance — COMP-001): Default model inconsistency — run_simple() defaults to `DSv4-flash` (bf_agent.py:1032) but SKILL.md non-compare default is `M27`. Users calling run_simple without explicit model get DSv4-flash instead of documented M27. FIX: align on M27 or use env-overrideable DEFAULT_MODEL.

1.2. [HIGH] (source: adversarial-compliance — COMP-002): Port mismatch — BIFROST_BASE_URL defaults to `http://localhost:8081` for bifrost_call() but new catalog/probe functions use BIFROST_HTTP_PORT=8080. These are two different HTTP services. bifrost_call (existing model calls) goes to 8081; list_catalog_models/probe_model (new discovery) go to 8080. FIX: unify on one port or make BIFROST_BASE_PORT env override apply to all.

1.3. [HIGH] (source: adversarial-security — SEC-002): add_route() f-string injection — `f'model == "{model}"'` embeds model directly without sanitization. Malicious model (e.g., containing `"` or `\`) could: (a) break the CEL expression causing Bifrost routing failures, (b) bypass the duplicate-check SELECT since the malformed CEL won't match existing entries. SQL injection is constrained (parameterized query for INSERT) but CEL expression integrity is compromised. FIX: validate/sanitize model — reject if contains `"` or `\`.

1.4. [MEDIUM] (source: adversarial-compliance — COMP-004): add_route() idempotency is misleading — SKILL.md calls it idempotent, but if a disabled rule exists with the same CEL expression, calling add_route(enabled=True) rejects instead of re-enabling. User must manually delete then recreate. FIX: update existing disabled rule instead of rejecting.

1.5. [MEDIUM] (source: adversarial-compliance — COMP-003): run_code() has redundant max_turns fallback — `turns_limit = max_turns or BF_CODE_MAX_TURNS` duplicates logic already at module level. Not wrong, just redundant. FIX: `turns_limit = max_turns if max_turns is not None else BF_CODE_MAX_TURNS`.

### Hidden Assumptions & Fragile Dependencies
2.1. [HIGH] (source: adversarial-critic blind spot): VALID_MODELS removal (P1 change) leaves no defensive validation — if Bifrost is unreachable or returns an unexpected error format, malformed model names pass straight through to the HTTP endpoint with no early validation. FIX: add model format validation as a lightweight guard before the Bifrost call.

2.2. [MEDIUM] (source: adversarial-security — SEC-003): Localhost HTTP has no auth — any local process can call Bifrost endpoints. This is acceptable for single-user solo-dev but is an unstated assumption. If the environment changes to multi-user (e.g., shared workstation), there is no access control. FIX: document as single-user-only assumption.

2.3. [MEDIUM] (source: adversarial-io-validation — IO-003): P:/ hardcoded as installation root — `P:/.claude/provider-configs/cc-bifrost.ps1` is a fixed absolute path. If the Claude Code installation is moved, all management commands break. Unlikely but possible for a portable install.

2.4. [LOW] (source: adversarial-security — SEC-005): No caller attribution in log events — log_event() for route add/delete has no user/session identity. Accountability gap if logs are used for audit purposes.

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (source: adversarial-quality — QUAL-001): DB path duplicated in 4 locations — `os.getenv("BIFROST_DB", r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")` appears at lines 313, 388, 454, 488 in probe_routes, add_route, delete_route, list_routes. Should be one module-level constant. Minimal change, high maintainability value.

3.2. [MEDIUM] (source: adversarial-quality — QUAL-002): No max_turns validation — run_code() accepts negative or zero max_turns without error. `range(0)` produces empty (no iterations); `range(-1)` produces `range(0, -1)` which is also empty in Python. Caller passing 0 or negative silently gets zero turns. FIX: validate `max_turns > 0`.

3.3. [LOW] (source: adversarial-quality — QUAL-003): tool_read_file() double read — line 660 calls `p.read_text()` and discards the result; line 661 immediately calls it again. Wasteful on every file read. FIX: delete line 660.

3.4. [LOW] (source: adversarial-quality — QUAL-004): delete_route() silent failure — exception handler returns error dict without logging, unlike add_route() which logs on failure. Makes debugging harder. FIX: add log_event on exception.

### Risks and Edge Cases
4.1. [CRITICAL] (source: adversarial-security — SEC-001): BIFROST_VK written to stdout via log_event() — any log interceptor, log shipper, or stdout redirection exposes the API key in plaintext. log_event() JSON payload at lines 108-127 includes model/provider fields without field-level redaction. The API key itself is in BIFROST_VK and gets sent as Bearer token in HTTP headers. If debug logging is enabled or stdout is captured, key is on disk. FIX: add field-level redaction in log_event() for any payload that includes auth-related data.

4.2. [MEDIUM] (source: adversarial-io-validation — IO-004): No daemon pre-flight check — if Bifrost daemon is not running, probe_routes() fails with generic connection error. User gets no actionable "run /bf start first" guidance. FIX: add a quick reachability check before probe_routes() that surfaces the startup command on failure.

4.3. [MEDIUM] (source: adversarial-security — SEC-004): CRLF injection in tool_write_file() — raw model output written to files without CRLF sanitization. If file is later served by a web server, CRLF sequences could enable HTTP response splitting. Low risk in code-agent sandbox but still CWE-93. FIX: strip or encode CRLF before write.

4.4. [LOW] (source: adversarial-compliance — COMP-005): delete_route() no transaction — two separate DELETE statements. If second fails, orphaned routing_targets remain. Low probability but possible on disk-full or corruption. FIX: wrap in explicit `BEGIN IMMEDIATE` transaction.

### Concrete Recommendations
5.1. [MEDIUM] Extract `BIFROST_DB` to module-level constant — one line change, eliminates 3 hardcoded path copies.

5.2. [MEDIUM] Add `max_turns > 0` validation in run_code() — prevents silent zero-turn behavior.

5.3. [MEDIUM] Add model format validation in add_route() — reject model names containing `"` or `\`.

5.4. [MEDIUM] Add re-enable logic to add_route() for existing disabled rules.

5.5. [LOW] Remove duplicate `p.read_text()` call in tool_read_file().

5.6. [LOW] Add log_event on delete_route() exception.

5.7. [LOW] Wrap delete_route() DELETEs in explicit transaction.

5.8. [LOW] Document single-user localhost-only assumption for Bifrost HTTP.

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-compliance): Why does bifrost_call use port 8081 while catalog/probe use 8080? Is this intentional (two separate services) or an oversight? If Bifrost HTTP daemon serves both the messages endpoint (8081) and catalog endpoint (8080), they should use the same base URL.

6.2. [LOW] (source: adversarial-io-validation): IO-001 and IO-002 were false positives — bf_agent.py exists at P:/tools/mcp/bf_agent.py and is verified importable by the test suite. However, the adversarial-io-validation agent's concern about the import path in SKILL.md (importing from `bf_agent` without adding P:/tools/mcp to sys.path) may still be valid if SKILL.md executes as a subprocess rather than with P:/tools/mcp pre-injected.

6.3. [LOW] (source: adversarial-critic): Is log_event() actually writing BIFROST_VK to stdout? Code inspection shows log_event payload includes model/provider fields but not the auth header itself. However, in debug logging scenarios or if correlation_id or other fields were logged alongside the call, the auth token could leak. Requires verification by running the actual code and checking stdout.

6.4. [LOW] (source: adversarial-quality): QUAL-001 says the DB path hardcodes username `brsth`. This is in the default fallback path. Is this intentional (private workstation install) or should it use a system-standard path like `%APPDATA%`?