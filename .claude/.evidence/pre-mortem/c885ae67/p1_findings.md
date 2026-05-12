## Triage Classification
hook — Three hook scripts for subagent delegation policy (UserPromptSubmit, Stop, CLI analysis)

## Dispatched Specialists
- adversarial-security: path traversal, input validation, sensitive data logging
- adversarial-compliance: hook registration, exit code handling, schema compliance
- adversarial-io-validation: file I/O patterns, silent failure handling, TOCTOU

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities
**Key findings:**
- [HIGH] SEC-001: Path traversal via terminal_id/session_id in file paths (Stop_subagent_opportunity.py:37,49)
- [MEDIUM] SEC-002: Sensitive data logging without redaction (delegation_prospector.py:85)
- [MEDIUM] SEC-003: No input validation on tool_events structure (Stop_subagent_opportunity.py:79,88,168)

### adversarial-compliance
**Domain:** Hook registration and schema compliance
**Key findings:**
- [CRITICAL] REG-001: delegation_prospector.py is DEAD CODE — @register_hook decorator present but _load_hooks() never imports the module. Hook never executes.
- [LOW] SCHEMA-001: _save_session_opportunities() missing mkdir before state file write (Stop_subagent_opportunity.py:47-55)
- [INFO] REG-002: Stop_subagent_opportunity.py correctly registered in IN_PROCESS_GATES (Stop.py:103,2752)

### adversarial-io-validation
**Domain:** File I/O patterns and error handling
**Key findings:**
- [MEDIUM] IO-001: delegation_prospector.py silently drops telemetry on I/O failure (delegation_prospector.py:78-89)
- [MEDIUM] IO-002: Identical silent-drop pattern in Stop_subagent_opportunity.py (Stop_subagent_opportunity.py:69-72)
- [LOW] IO-003: tune_subagent_gate.py silently skips corrupted history.jsonl entries (tune_subagent_gate.py:61-89)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [CRITICAL] (source: adversarial-compliance) — delegation_prospector.py is dead code. The @register_hook decorator self-registers into HOOKS dict, but registry.py:_load_hooks() never imports the module. The hook exists but never executes. (UserPromptSubmit_modules/delegation_prospector.py:93)
1.2. [HIGH] (source: adversarial-security) — Path traversal: terminal_id/session_id used directly in file paths without sanitization. A path like `../../etc/passwd` could escape _LOG_DIR. (Stop_subagent_opportunity.py:37,49)

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-security) — Prompt content is logged without redaction. API keys, tokens, or passwords in user prompts are written to plaintext .jsonl files. (delegation_prospector.py:85)
2.2. [MEDIUM] (source: adversarial-io-validation) — Silent OSError suppression means telemetry events are dropped without any signal. No fallback path, no warning. (delegation_prospector.py:89, Stop_subagent_opportunity.py:71)

### Missing Obvious Actions / Best Practices
3.1. [CRITICAL] (source: adversarial-compliance) — Hook must be added to core_hook_modules in registry.py to actually execute. This is the standard registration path for UserPromptSubmit hooks.
3.2. [LOW] (source: adversarial-compliance) — _save_session_opportunities() should call _LOG_DIR.mkdir before writing. Mirrors the pattern in _log_opportunity_event() line 61. (Stop_subagent_opportunity.py:47-55)

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-security) — No type validation on tool_events list. Malformed input causes silent failure. (Stop_subagent_opportunity.py:79,88,168)
4.2. [LOW] (source: adversarial-io-validation) — Corrupted history.jsonl lines silently skipped in get_agent_usage(). Tuning decisions may be based on incomplete data. (tune_subagent_gate.py:61-89)

### Concrete Recommendations
5.1. [CRITICAL] Add delegation_prospector to core_hook_modules in registry.py — without this, the hook never fires
5.2. [HIGH] Sanitize terminal_id/session_id with regex before file path construction
5.3. [MEDIUM] Add sensitive data redaction before logging prompts
5.4. [MEDIUM] Replace `except OSError: pass` with warning emission
5.5. [LOW] Add mkdir(parents=True) to _save_session_opportunities()

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-io-validation) — Are there other callers expecting guaranteed telemetry delivery? Silent drops may violate undocumented contracts.
