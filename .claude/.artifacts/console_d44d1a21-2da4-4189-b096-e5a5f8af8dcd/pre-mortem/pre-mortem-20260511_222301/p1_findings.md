## Triage Classification
**hook** — Claude Code hook system for delegation enforcement (UserPromptSubmit prospector + PreToolUse gate + PostToolUse task tracker)

## Dispatched Specialists
- **adversarial-security**: Sensitive data redaction, file permissions, credential exposure
- **adversarial-compliance**: Terminal ID alignment between hooks, exit code contracts, telemetry
- **adversarial-logic**: Block message routing, exit code paths, TTL edge cases
- **adversarial-testing**: Test coverage gaps, weak assertions, integration coverage
- **adversarial-io-validation**: State file isolation, cross-terminal pollution, fail-open behavior

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [CRITICAL] (source: adversarial-compliance, adversarial-security) — **Terminal ID source mismatch defeats enforcement** (`delegation_prospector.py:144-146` vs `PreToolUse_delegation_gate.py:33-42`)
   - Prospector extracts `terminal_id` from `HookContext.data`; gate re-detects from `WT_SESSION` directly
   - When context-derived and env-derived IDs diverge, prospector writes to path A, gate reads from path B
   - **Enforcement fails silently** — tools proceed without blocking even when delegation was expected
   - Fix: Gate must accept `terminal_id` from input data, not re-detect independently

1.2. [HIGH] (source: adversarial-security) — **matched_pattern not redacted before persisting to state file** (`delegation_prospector.py:178`)
   - `_write_delegation_state()` passes `prompt_snippet` through `_redact_sensitive()` but writes `matched_pattern` raw
   - Detection pattern strings may contain fragments of user prompts or inferred intent
   - Fix: Apply `_redact_sensitive()` to `matched_pattern` before writing

1.3. [HIGH] (source: adversarial-compliance) — **_log_gate_event() is dead code** (`PreToolUse_delegation_gate.py:81-97`)
   - Function is defined but never called from `main()`
   - All gate telemetry is silently dropped — no observable evidence of blocked tools or bypass usage
   - Fix: Add calls at each gate decision point (bypass_used, blocked, allowed)

1.4. [HIGH] (source: adversarial-testing) — **No end-to-end integration test** (`tests/test_delegation_gate.py:375`)
   - `_run_gate()` uses synthetic stdin instead of actual hook execution
   - State path mismatch (COMP-001) would not be caught by current test suite
   - Fix: Add integration test exercising real hook entry points

1.5. [MEDIUM] (source: adversarial-logic) — **Block message routed to wrong channel** (`PreToolUse_delegation_gate.py:108-121`)
   - `_build_block_message()` prints to stderr only; modern Claude Code expects stdout JSON contract
   - On v3.14+ stderr-only blocks may be treated as warnings, not hard blocks
   - Fix: Print `{"decision": "deny", "reason": "..."}` to stdout and exit 0; reserve exit 2 for actual hard failures

### Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-io-validation) — **No terminal_id validation on state file read** (`PreToolUse_delegation_gate.py:52-68`)
   - State file stores `terminal_id` from time of write; no validation that it matches current detection on read
   - Cross-terminal state bleed possible if env var appears mid-session
   - Fix: On read, verify loaded `terminal_id` matches current `_detect_terminal_id()`. Mismatch = treat as stale, clear state.

2.2. [MEDIUM] (source: adversarial-security) — **Truncation applied before redaction** (`delegation_prospector.py:161, 179`)
   - `prompt_snippet[:200]` cuts credential patterns mid-match before `_redact_sensitive()` runs
   - Fix: Apply `_redact_sensitive(prompt_snippet)[:200]` — redact before truncate

2.3. [LOW] (source: adversarial-io-validation) — **Fail-open on empty/malformed stdin** (`PreToolUse_delegation_gate.py:156-164`)
   - Empty stdin → `json.loads("")` raises `JSONDecodeError` → caught → returns None → gate exits 0 (allow)
   - Violates fail-secure principle
   - Fix: Warn to stderr when raw is empty for non-exempt tools

2.4. [LOW] (source: adversarial-logic) — **Bypass flag semantics unclear** (`PreToolUse_delegation_gate.py:100-105`)
   - `--allow-inline` name does not convey "bypass delegation enforcement" semantics
   - Fix: Rename to `--skip-delegation-check` or `--allow-inline-delegation`

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-security) — **Incomplete sensitive data redaction patterns** (`delegation_prospector.py:44-48`)
   - Only 3 patterns defined: labeled credentials, `sk-*` keys, PEM headers
   - Missing: GitHub tokens (`ghp_*`, `gho_*`), AWS keys (`AKIA*`), JWT tokens (`eyJ...`)
   - Fix: Expand patterns to cover `gh[pousr]_[A-Za-z0-9_]{36,}`, `AKIA[0-9A-Z]{16}`, `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`

3.2. [MEDIUM] (source: adversarial-security) — **No explicit file permissions on state files** (`delegation_prospector.py:173, 182`)
   - State files use default permissions; readable by other users on multi-user systems
   - Fix: `os.chmod(state_file, stat.S_IRUSR | stat.S_IWUSR)` after write

3.3. [LOW] (source: adversarial-security) — **Temp file persists if os.replace() fails** (`delegation_prospector.py:182-187`)
   - No cleanup on exception — orphaned temp file with sensitive content
   - Fix: Add try/except/finally to remove temp file on failure

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-io-validation) — **unknown terminal_id causes cross-terminal state pollution**
   - When `WT_SESSION` absent, both hooks fall back to `unknown` as isolation key
   - All sessions without `WT_SESSION` share one state directory
   - Fix: Fallback chain should be `WT_SESSION` → `CLAUDE_TERMINAL_ID` → `hash(PID + cwd)`. Never bare `unknown`.

4.2. [LOW] (source: adversarial-logic) — **_log_gate_event silently swallows OSError** (`PreToolUse_delegation_gate.py:81-97`)
   - Telemetry lost on read-only filesystem or disk full with no warning
   - Fix: Fallback to stderr warning when primary logging fails

4.3. [LOW] (source: adversarial-compliance) — **TTL constant duplicated in two files** (`PreToolUse_delegation_gate.py:23`, `delegation_prospector.py:38`)
   - `DELEGATION_TTL_SECONDS=300` in both files; desync risk on future edits
   - Fix: Extract to `__lib/shared_constants.py` and import from both

4.4. [LOW] (source: adversarial-compliance) — **Test state isolation not mocked in prospector tests** (`tests/test_delegation_gate.py:288-322`)
   - `_get_state_dir` not patched; tests write to real `.artifacts/` directory
   - Fix: Mock `_get_state_dir` to return `temp_dir` in `TestDelegationProspectorState`

### Concrete Recommendations

5.1. Fix terminal ID alignment first — this is the single failure mode that defeats the entire mechanism
5.2. Wire `_log_gate_event()` into `main()` — without telemetry, blocked/bypassed events are invisible
5.3. Expand `_SENSITIVE_PATTERNS` — current coverage misses common credential formats
5.4. Add integration test for real hook execution path — current tests use synthetic stdin
5.5. Validate `terminal_id` on state file read — cross-terminal bleed possible without this check

### Open Questions / Unknowns

6.1. What determines the `terminal_id` in `context.data`? Is it guaranteed to match `WT_SESSION`?
6.2. What Claude Code version introduced stdout JSON contract? Is exit 2 + stderr still reliably blocking?
6.3. Are there integration tests that verify blocking behavior end-to-end with actual Claude Code execution?
6.4. Is `WT_SESSION` guaranteed in all Claude Code terminal environments? Risk is real in CI/containerized scenarios.
