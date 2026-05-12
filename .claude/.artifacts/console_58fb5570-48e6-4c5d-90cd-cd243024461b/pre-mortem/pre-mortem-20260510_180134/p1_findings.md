## Triage Classification
hook — Plugin hook namespacing implementation across fact-guard, snapshot, skill-guard

## Dispatched Specialists
- adversarial-security: Path injection, command execution, I/O safety
- adversarial-compliance: Hook registration, exit code handling, schema compliance
- adversarial-io-validation: File operations, external calls, path validation

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities (injection, auth, data exposure)
**Key findings:**
- No specification violations found
- Hook namespacing is a refactoring — no new vulnerabilities introduced
- All three plugins correctly use `$CLAUDE_PLUGIN_ROOT` in commands

### adversarial-compliance
**Domain:** Compliance, schema, registration, exit code
**Key findings:**
- [LOW] SEC-001: PostToolUse records sensitive content from config files (fact_guard/fact_extraction.py:23)
- [LOW] SEC-002: Contamination detection false positives on legitimate shared values (fact_guard/contamination.py:57)
- [INFO] SEC-003: External LLM subprocess no network isolation (fact-guard_PreToolUse.py:150)
- [INFO] SEC-004: State files stored unencrypted (fact_guard/state.py:30)

### adversarial-io-validation
**Domain:** I/O safety, path validation, file operations
**Key findings:**
- [MEDIUM] IO-001: Malformed JSON in snapshot_SessionStart.py causes silent exit(0) (snapshot/scripts/hooks/snapshot_SessionStart.py:31-33)
- [MEDIUM] IO-002: Hardcoded Windows path P:\.claude in SessionEnd_tldr.py:29
- [MEDIUM] IO-003: snapshot_v2 import failure silent in UserPromptSubmit (snapshot/scripts/hooks/snapshot_UserPromptSubmit.py:198-206)
- [LOW] IO-004: Hardcoded absolute paths in skill-guard PreToolUse/Stop (skill-guard/src/skill_guard/skill-guard_PreToolUse.py:10)
- [LOW] IO-005: Generic exception handler in fact-guard PreToolUse (fact-guard/hooks/fact-guard_PreToolUse.py:65-68)

## Consolidated Findings

### Logical Gaps & Inconsistencies
No logical gaps found. Namespacing implementation is consistent across all three plugins.

### Hidden Assumptions & Fragile Dependencies
1.1. [MEDIUM] (source: adversarial-io-validation) — snapshot_SessionStart.py:31-33: Assumes JSON input is always well-formed. Malformed input silently exits 0, losing handoff context.
1.2. [MEDIUM] (source: adversarial-io-validation) — SessionEnd_tldr.py:29: Assumes P: drive is always available. Silent failure on unavailable drive loses session summaries.
1.3. [LOW] (source: adversarial-io-validation) — skill-guard entrypoints: Assumes P:\packages\skill-guard and P:\.claude\hooks paths are stable. Hardcoded paths not relocatable.

### Missing Obvious Actions / Best Practices
2.1. [MEDIUM] (source: adversarial-compliance) — fact_guard/state.py:30: State files (observed_facts.json) stored in plaintext with no encryption or restricted permissions.
2.2. [MEDIUM] (source: adversarial-compliance) — fact_guard/fact_extraction.py:23: PostToolUse extracts facts from ALL Read outputs including sensitive config files with no path-based filtering.

### Risks and Edge Cases
3.1. [MEDIUM] (source: adversarial-io-validation) — snapshot_UserPromptSubmit.py:198-206: snapshot_v2 import failure silently produces empty recovery context. Intra-session compaction loses automatic recovery with no signal.
3.2. [LOW] (source: adversarial-compliance) — fact_guard/contamination.py:57: Contamination detector flags legitimate shared values (quota tier, region) as copied, causing false positives.
3.3. [INFO] (source: adversarial-compliance) — fact-guard_PreToolUse.py:150: External LLM subprocess call has no network isolation or AIR_GAP mode.

### Concrete Recommendations
4.1. [MEDIUM] Log stderr warning before silent exit(0) in snapshot_SessionStart.py — preserves diagnostics without blocking session start.
4.2. [MEDIUM] Add platform-aware path resolution in SessionEnd_tldr.py — fall back to cwd or user home rather than hardcoded P:\.claude.
4.3. [MEDIUM] Add diagnostic HookResult when snapshot_v2 import fails in UserPromptSubmit — failure becomes visible rather than silent.
4.4. [LOW] Add sensitive path filtering before fact extraction in fact_guard/fact_extraction.py — exclude config files, .env, credentials paths.
4.5. [LOW] Add SKIP_FIELDS list in contamination.py for expected shared values (quota, tier, region).
4.6. [INFO] Add file permissions 0o600 in fact_guard/state.py after write — os.chmod or equivalent.
4.7. [INFO] Add AIR_GAP env var check in fact-guard_PreToolUse.py for offline verification mode.

### Open Questions / Unknowns
5.1. [MEDIUM] (source: adversarial-io-validation) — What is the expected behavior when P: drive is unavailable for snapshot SessionEnd? Fall back or error?
5.2. [LOW] (source: adversarial-compliance) — Are there integration tests covering renamed hooks after the namespacing refactor?
5.3. [LOW] (source: adversarial-compliance) — Has hook function been verified end-to-end after the file rename?