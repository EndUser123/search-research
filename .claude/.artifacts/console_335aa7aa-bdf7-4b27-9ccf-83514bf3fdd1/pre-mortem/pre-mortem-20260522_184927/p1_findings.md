## Triage Classification
code + document — Bifrost v1.5.2 PowerShell wrapper (cc-bifrost.ps1) and its provider/routing documentation (bifrost_configured_providers.md). Helper scripts routes_probe.py and bifrost_db.py also reviewed.

## Project Profile Applied
none found

## Missing Profile Sections
- operational invariants for daemon process management
- historical regression notes for hardcoded credential fallback patterns
- validation commands for live/production-readiness (the --sync write path has no verification)

## Dispatched Specialists
- `adversarial-logic`: CEL routing, function scope, credential handling, restart bootstrap
- `adversarial-security`: hardcoded tokens, .env loading, PID race, temp file exposure
- `adversarial-io-validation`: file existence, temp file cleanup, PID detection, path resolution
- `adversarial-compliance`: SQL priority ordering, clean_sync model validation, restart exit codes

## Specialist Findings Summary

### adversarial-logic
**Domain:** Control flow, scope, CEL expression evaluation, credential handling
**Key findings:**
- [blocker] Show-BifrostDashboard references $proc never defined in function scope — always fails (cc-bifrost.ps1:360)
- [HIGH] Hardcoded live credentials embedded in source — BIFROST_API_KEY line 46, ANTHROPIC_AUTH_TOKEN line 50
- [HIGH] Sync-BifrostConfig silently succeeds when rules are empty — writes empty config.json and reports success (cc-bifrost.ps1:201-205)
- [MEDIUM] Get-BifrostProcess drains jobs via Output.Count filter that can race
- [LOW] Status probe hardcodes routing keys (M27, GLM-5.1) not catalog names — gives false confidence when routing is disabled

### adversarial-security
**Domain:** Secrets, path injection, process lifecycle, credential exposure
**Key findings:**
- [CRITICAL] Live Bifrost API key hardcoded at line 46 — committed to source control
- [CRITICAL] Live ANTHROPIC_AUTH_TOKEN hardcoded at line 50 — full Anthropic API access
- [HIGH] .env loading has no path allowlist — any ancestor .env can inject credentials
- [MEDIUM] TOCTOU race in PID file read-and-kill (cc-bifrost.ps1:255)
- [MEDIUM] Error log to predictable shared TEMP path — unprivileged user can pre-place
- [LOW] Binary fallback chain with no integrity check — PATH hijack risk
- [LOW] Routing table not validated at load time — corrupted DB can produce malformed CEL

### adversarial-io-validation
**Domain:** File operations, temp files, process detection, path resolution
**Key findings:**
- [blocker] Required env vars used without validation after .env load — silent hardcoded fallback instead of error
- [HIGH] Temp file cleanup not guaranteed on error path — python probe code leaks to disk (cc-bifrost.ps1:475-478, 493-496)
- [HIGH] PID-based process detection unreliable — 'bifrost' substring match can kill wrong process
- [HIGH] config.json write has no success verification — silent failure if APPDATA unset
- [HIGH] $PSScriptRoot resolution can fail silently in dot-source or -Command invocation
- [MEDIUM] Backup path collision within same second — second --sync overwrites first
- [MEDIUM] Binary fallback chain has no verification it actually started
- [MEDIUM] netstat parsing for port detection fails on non-English locales

### adversarial-compliance
**Domain:** Schema compliance, SQL ordering, validation coverage
**Key findings:**
- [HIGH] SQL ORDER BY r.priority ASC — inverts routing priority (higher number = higher priority in Bifrost) (routes_probe.py:368, bifrost_db.py:28)
- [HIGH] clean_sync validates provider names but not model field — invalid models silently pass to config.json
- [MEDIUM] Hardcoded ANTHROPIC_AUTH_TOKEN — silent fallback when .env missing
- [MEDIUM] Restart loop returns after 70s with warning but no error exit code
- [MEDIUM] Show-BifrostDashboard uses undefined $proc variable
- [MEDIUM] DB path hardcoded to single Windows user — not portable

## Consolidated Findings

## Investigation Coverage
- Static artifacts reviewed: cc-bifrost.ps1 (773 lines), bifrost_configured_providers.md, routes_probe.py, bifrost_db.py
- Non-static probes run: none (helper scripts reviewed statically)
- Non-static probes recommended but not run: live --sync write verification, PID collision test, .env path injection test

## Static Test Coverage
- Static checks already present: Test-Path on binary paths, --help flag verification
- Static checks missing: env var presence validation after .env load, config.json write verification, APPDATA existence check
- Static checks insufficient without live/plugin validation: SQL priority ordering requires DB query to confirm actual behavior

## Review Lens Coverage
- Lenses applied: logic, security, io-validation, compliance
- Lenses skipped or deferred: performance (no hot paths), testing (no test suite found)
- Reason skipped lenses are safe to defer: no loops or DB queries in the PowerShell script itself; routes_probe.py and bifrost_db.py are Python helpers reviewed statically

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance) — SQL ORDER BY r.priority ASC inverts routing priority. Higher priority numbers should match first, but ASC returns low values first. Affects routes_probe.py:368 and bifrost_db.py:28. Fix: `ORDER BY r.priority DESC`.
1.2. [HIGH] (source: adversarial-logic) — Show-BifrostDashboard uses undefined $proc variable. Function scope never sets $proc — always reports NOT RUNNING even when daemon is active (cc-bifrost.ps1:360).
1.3. [HIGH] (source: adversarial-logic) — Sync-BifrostConfig writes empty config.json silently when rules are empty. Lines 201-205 warn but don't prevent the write. User sees "Synced 0 rules" which looks like success.
1.4. [MEDIUM] (source: adversarial-compliance) — clean_sync model validation gap. Provider names checked but model field not validated. Invalid model names silently pass to config.json, causing runtime 404 errors at routing time.
1.5. [LOW] (source: adversarial-logic) — Status probe uses routing keys (M27, GLM-5.1) not catalog names. If M27 rule is disabled, probe sends M27 to default provider and reports OK — false confidence.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-security) — .env loading assumes the file is at P:\.env and contains expected keys. If .env is absent, script proceeds with hardcoded credentials silently — no error, no warning beyond the initial [WARN].
2.2. [MEDIUM] (source: adversarial-io-validation) — $PSScriptRoot is assumed to be set in all PowerShell invocation contexts. In dot-source or -Command mode it may be empty/null, causing bifrost_db.py path to be invalid with silent failure.
2.3. [MEDIUM] (source: adversarial-io-validation) — PID file is trusted as the sole daemon identity mechanism. Windows PIDs are recycled aggressively; the 'bifrost' substring check is loose and can match unrelated processes.
2.4. [LOW] (source: adversarial-io-validation) — Binary fallback chain assumes versioned paths exist. If all four checked paths fail, script prints error but the error log is in a shared temp location readable by all users.

### Missing Obvious Actions / Best Practices
3.1. [CRITICAL] (source: adversarial-security) — Remove hardcoded BIFROST_API_KEY (line 46) and ANTHROPIC_AUTH_TOKEN (line 50). Both are live operational secrets embedded in source. Require environment or .env with no fallback.
3.2. [HIGH] (source: adversarial-io-validation) — Add env var validation after .env loading. If ANTHROPIC_AUTH_TOKEN or BIFROST_API_KEY are still the hardcoded defaults, error and exit instead of proceeding silently.
3.3. [HIGH] (source: adversarial-io-validation) — Add APPDATA existence check before WriteAllText in Sync-BifrostConfig. Verify the file was actually written to the expected location before printing success.
3.4. [HIGH] (source: adversarial-security) — Restrict .env loading to a known prefix path rather than loading from any ancestor directory.
3.5. [MEDIUM] (source: adversarial-compliance) — Add exit 1 after 70s restart timeout instead of returning with a warning.
3.6. [MEDIUM] (source: adversarial-io-validation) — Use try/finally for temp file cleanup in Show-BifrostStatus and Verify-BifrostRouting.
3.7. [MEDIUM] (source: adversarial-io-validation) — Use Get-CimInstance or Get-NetTCPConnection instead of netstat text parsing for port detection.
3.8. [LOW] (source: adversarial-compliance) — Document LATENCY_TTL rationale or make configurable.

### Risks and Edge Cases
4.1. [HIGH] (source: adversarial-io-validation) — PID race between concurrent cc-bf invocations. One process can delete another's PID file during the stale check, causing split-brain daemon detection.
4.2. [HIGH] (source: adversarial-security) — Token rotation gap. If ANTHROPIC_AUTH_TOKEN was ever a real credential and was committed, it should be treated as potentially compromised — no rotation mechanism exists.
4.3. [MEDIUM] (source: adversarial-io-validation) — config.json write silently fails if APPDATA is unset. WriteAllText writes to current working directory, Bifrost reads wrong file, user sees "Synced N rules" with no actual effect.
4.4. [MEDIUM] (source: adversarial-logic) — Binary exists but is wrong architecture — Start-BifrostDaemon reports "Running" but HTTP server never starts. Error buried in temp log file; user sees confusing "Bifrost API not responding after 70s".
4.5. [LOW] (source: adversarial-io-validation) — Backup file collision if --sync called twice in same second from different terminals. Second invocation overwrites first backup with no warning.

### Concrete Recommendations
5.1. (source: adversarial-security) Remove hardcoded BIFROST_API_KEY default at line 46 — require external env or .env.
5.2. (source: adversarial-security) Remove hardcoded ANTHROPIC_AUTH_TOKEN default at line 50 — require external env or .env.
5.3. (source: adversarial-compliance) Change `ORDER BY r.priority` to `ORDER BY r.priority DESC` in routes_probe.py:368 and bifrost_db.py:28.
5.4. (source: adversarial-logic) Add `$proc = Get-BifrostProcess` at start of Show-BifrostDashboard function (before line 360 check).
5.5. (source: adversarial-io-validation) After .env loading, validate required env vars are not still the hardcoded defaults — exit with error if they are.
5.6. (source: adversarial-io-validation) Add APPDATA existence check + file write verification in Sync-BifrostConfig before reporting success.
5.7. (source: adversarial-compliance) Add model validation to Test-BifrostRuleTarget — check that model field is non-empty.
5.8. (source: adversarial-compliance) Add `exit 1` after 70s restart wait loop when ready is false.
5.9. (source: adversarial-io-validation) Use try/finally for temp file cleanup in Show-BifrostStatus and Verify-BifrostRouting.
5.10. (source: adversarial-io-validation) Add file locking around PID file access to prevent concurrent race.

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-logic) — Is there a mechanism to invalidate PID file when PowerShell session ends and background job is auto-cleaned? Could leave stale PID pointing to non-bifrost process.
6.2. [MEDIUM] (source: adversarial-io-validation) — Is $PSScriptRoot reliably set in all PowerShell invocation contexts (direct run, dot-source, -Command)?
6.3. [LOW] (source: adversarial-security) — Has ANTHROPIC_AUTH_TOKEN ever been rotated? Should be treated as potentially compromised if ever committed with real value.
6.4. [LOW] (source: adversarial-compliance) — Is there any integration test that validates --sync writes valid config.json that Bifrost can read back?