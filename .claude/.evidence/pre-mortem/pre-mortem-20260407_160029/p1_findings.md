# Phase 1 Findings: skill_metadata_advisory.py Pre-Mortem

## Triage Classification
**hook** — UserPromptSubmit module that injects frontmatter advisories when skills lack proper workflow_steps/enforcement metadata.

## Dispatched Specialists
- **adversarial-security**: Path injection, command execution, information leakage, YAML DoS
- **adversarial-compliance**: Hook registration, API contracts, event type compliance
- **adversarial-io-validation**: File operations, path validation, exception handling

---

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities (path injection, information disclosure, DoS)
**Key findings:**
- [HIGH] SEC-001: Path traversal vulnerability — skill_name used in path construction without validation (skill_metadata_advisory.py:32-33)
- [MEDIUM] SEC-002: Broad exception handling hides security events (skill_metadata_advisory.py:55-56)
- [LOW] SEC-003: YAML-based DoS potential via explosive data structures (skill_metadata_advisory.py:43)
- [INFO] SEC-004: Missing rate limiting causes warning fatigue (skill_metadata_advisory.py:118)

### adversarial-compliance
**Domain:** Hook registration compliance, API contract adherence
**Key findings:**
- [HIGH] COMP-001: Event type documentation violation — work.md describes PreToolUse but implementation is UserPromptSubmit (work.md:10)
- [MEDIUM] COMP-002: Registration documentation misleading — @register_hook IS the router pattern (work.md:12)
- [MEDIUM] COMP-003: API contract undocumented — context.data['userMessage'] key not specified in HookContext (base.py:61, skill_metadata_advisory.py:101)
- [LOW] COMP-004: Test expectation wrong — /arch expected to trigger but has workflow_steps (skill_metadata_advisory.py:130)
- [MEDIUM] COMP-005: Return value ambiguity — HookResult vs raw text in PROTOCOL.md (skill_metadata_advisory.py:120)
- [LOW] COMP-006: Silent failures violate "fail fast" principle (skill_metadata_advisory.py:55)

### adversarial-io-validation
**Domain:** File I/O validation, exception handling, path safety
**Key findings:**
- [HIGH] IO-001: Path traversal via '../escape' pattern — skill_name not sanitized (skill_metadata_advisory.py:32-33)
- [MEDIUM] IO-002: Broad exception swallowing masks YAML parse failures (skill_metadata_advisory.py:55-56)
- [MEDIUM] IO-003: No validation that enforcement value is in allowed set {strict, advisory, none} (skill_metadata_advisory.py:51-53)
- [LOW] IO-004: UTF-8 errors='replace' silently corrupts non-UTF-8 content (skill_metadata_advisory.py:39)
- [LOW] IO-005: TOCTOU pattern — exists() check before read (skill_metadata_advisory.py:35-39)

---

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance) — Event type documentation mismatch. work.md describes PreToolUse deletion but actual implementation is UserPromptSubmit. UserPromptSubmit cannot block tool execution; it only injects content. (work.md:10, skill_metadata_advisory.py:7)

1.2. [HIGH] (source: adversarial-security, adversarial-io-validation) — Path traversal vulnerability duplicates. SEC-001 and IO-001 are identical issues: skill_name from regex match is used directly in Path construction without validation for '../' sequences. (skill_metadata_advisory.py:32-33, 108)

1.3. [MEDIUM] (source: adversarial-compliance) — Test expectation invalid. Test case expects '/arch' to trigger advisory but /arch has workflow_steps defined, so should not trigger. Test passes for wrong reason. (skill_metadata_advisory.py:130)

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-compliance) — API contract assumption. Hook assumes context.data contains 'userMessage' key but this is not documented in HookContext specification. If UserPromptSubmit event data structure changes, hook breaks silently. (base.py:61, skill_metadata_advisory.py:101)

2.2. [MEDIUM] (source: adversarial-io-validation) — Enforcement value format assumed. Code stores enforcement values without validating they match allowed set {strict, advisory, none}. Case sensitivity issues ('STRICT' vs 'strict') not handled. (skill_metadata_advisory.py:51-53)

2.3. [LOW] (source: adversarial-io-validation) — UTF-8 encoding assumed. errors='replace' silently corrupts non-UTF-8 files. No diagnostic for users with incompatible encodings. (skill_metadata_advisory.py:39)

2.4. [LOW] (source: adversarial-io-validation) — File existence assumed stable. TOCTOU pattern between exists() check and read_text(). Safe only because broad exception handler catches FileNotFoundError. (skill_metadata_advisory.py:35-39)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-security, adversarial-io-validation) — No path sanitization. skill_name from user input should be validated with whitelist regex before use in path construction. Missing basic security practice. (skill_metadata_advisory.py:32-33)

3.2. [MEDIUM] (source: adversarial-security, adversarial-compliance, adversarial-io-validation) — No logging on errors. Broad exception handler (except Exception: pass) swallows YAML parse errors, file access failures, and security-relevant events. Violates "fail fast" principle. (skill_metadata_advisory.py:55-56)

3.3. [INFO] (source: adversarial-security) — No rate limiting on warnings. Same advisory shown on every skill invocation. Creates warning fatigue, users ignore security messages. (skill_metadata_advisory.py:118)

3.4. [LOW] (source: adversarial-security) — No YAML parsing limits. File size, nesting depth, or parse time limits allow potential DoS via malicious SKILL.md. (skill_metadata_advisory.py:43)

### Risks and Edge Cases
4.1. [HIGH] (source: adversarial-security) — Path traversal exploit. User invokes '/../etc/passwd' or similar to read arbitrary files from P: drive. Could expose credentials, config, user data. Verified: '../escape' resolves to 'P:\.claude\escape\SKILL.md'. (skill_metadata_advisory.py:32-33, 108)

4.2. [MEDIUM] (source: adversarial-io-validation) — Malformed YAML causes silent failure. SKILL.md with invalid YAML syntax is parsed but yaml.safe_load() raises ParserError that gets swallowed. No diagnostic for user. (skill_metadata_advisory.py:43, 55-56)

4.3. [MEDIUM] (source: adversarial-io-validation) — Invalid enforcement values propagate. 'enforcement: INVALID' or 'enforcement: STRICT' (wrong case) stored without validation. Downstream enforcement logic may fail unexpectedly. (skill_metadata_advisory.py:51-53)

4.4. [LOW] (source: adversarial-io-validation) — Non-UTF-8 files corrupted. SKILL.md with Latin-1 or UTF-16 encoding has bytes replaced with '�', breaking YAML parsing invisibly. (skill_metadata_advisory.py:39)

4.5. [LOW] (source: adversarial-security) — YAML DoS via explosive structures. Deep nesting or recursive anchors in SKILL.md consume CPU/memory during parsing. Could delay hook execution. (skill_metadata_advisory.py:43)

### Concrete Recommendations
5.1. [Add path sanitization] (source: adversarial-security, adversarial-io-validation) — Validate skill_name with regex before path construction: `if not re.match(r'^[a-zA-Z0-9_-]+$', skill_name): return {"workflow_steps": [], "enforcement": None}`. Also resolve path and verify it stays within skills directory. (skill_metadata_advisory.py:32-33)

5.2. [Replace broad exception handler] (source: adversarial-security, adversarial-compliance, adversarial-io-validation) — Catch specific exceptions: `(OSError, yaml.YAMLError) as e`. Add logging: `logger.warning(f"Failed to load {skill_name}: {e}")`. Follow "fail fast" principle. (skill_metadata_advisory.py:55-56)

5.3. [Validate enforcement values] (source: adversarial-io-validation) — Check value is in allowed set: `if enforcement and enforcement.lower() in {'strict', 'advisory', 'none'}: result['enforcement'] = enforcement.lower()`. Log warning for invalid values. (skill_metadata_advisory.py:51-53)

5.4. [Fix test expectation] (source: adversarial-compliance) — Change `/arch` test case from `True` to `False`, or use a skill that actually lacks workflow_steps. (skill_metadata_advisory.py:130)

5.5. [Document API contract] (source: adversarial-compliance) — Add to HookContext docstring: `data: For UserPromptSubmit events, contains {"userMessage": str, ...}`. (base.py:61)

5.6. [Add YAML parsing limits] (source: adversarial-security) — Add MAX_YAML_SIZE constant (100KB), check content length before parsing. Add depth validation for nested structures. (skill_metadata_advisory.py:39-43)

5.7. [Add rate limiting] (source: adversarial-security) — Track shown warnings in terminal-scoped state file. Show each advisory once per session or 24-hour period. (skill_metadata_advisory.py:118)

5.8. [Fix UTF-8 handling] (source: adversarial-io-validation) — Try UTF-8 read, catch UnicodeDecodeError and log warning: `f'{skill_file} is not UTF-8 encoded'`. Don't silently corrupt with errors='replace'. (skill_metadata_advisory.py:39)

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-io-validation) — Expected behavior when skill directory exists but SKILL.md is missing? Currently returns empty metadata (no warning). Should this surface a diagnostic?

6.2. [MEDIUM] (source: adversarial-io-validation) — Should hook validate YAML structure more strictly (e.g., ensure workflow_steps is list of strings, not just `isinstance(list)`)?

6.3. [LOW] (source: adversarial-io-validation) — Is the enforcement tier system (strict|advisory|none) documented centrally that hook could reference for validation?

6.4. [LOW] (source: adversarial-compliance) — Why was PreToolUse version deleted? Was the move to UserPromptSubmit intentional or due to the display issue? The event type choice affects capabilities (UserPromptSubmit cannot block tools).

---

## Phase 1 Completion Status
✅ All dispatched specialists produced valid JSON
✅ p1_findings.md consolidated

**Next Step:** Phase 2 — Cross-Agent Meta-Critique
