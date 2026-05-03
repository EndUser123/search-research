## Triage Classification
hook — UserPromptSubmit hook (user_prompt_submit_hook.py) for skill-guard

## Dispatched Specialists
- adversarial-security: hardcoded paths, subprocess safety, symlink targets
- adversarial-compliance: hook registration, schema compliance, path resolution bugs
- adversarial-io-validation: file operations, external calls, path existence checks

## Specialist Findings Summary

### adversarial-security
**Domain:** Data access, path injection, command execution
**Key findings:**
- [MEDIUM] Plugin name not sanitized in subprocess calls (plugin-audit-and-fix.py:667)
- [LOW] SKILL.md inline Python placeholder '<name>' not validated before settings.json write
- [INFO] readlink target path not validated for symlink/junction creation

### adversarial-compliance
**Domain:** Schema, hook registration, exit code handling
**Key findings:**
- [HIGH] hooks.json at plugin root instead of hooks/hooks.json (COMP-001 — false positive: plugin-installer has hooks/hooks.json at line 118)
- [HIGH] UserPromptSubmit hook not implemented (COMP-002 — FALSE POSITIVE: hook IS implemented in skill-guard plugin at P:/packages/.claude-marketplace/plugins/skill-guard/src/skill_guard/user_prompt_submit_hook.py)
- [MEDIUM] Audit script path-resolution bug: naive string replace on Path (plugin-audit-and-fix.py:161)
- [LOW] Skills enforcement field is 'advisory' — may need blocking for validate

### adversarial-io-validation
**Domain:** Path validation, file existence, external calls
**Key findings:**
- [blocker] ExecutionRuntime.create_run() does not exist (IO-001 — FALSE POSITIVE: ExecutionRuntime IS implemented in skill-guard at execution_runtime.py)
- [blocker] execution-state.json directory creation not validated (IO-002 — FALSE POSITIVE: ArtifactsExecutionStore calls mkdir(parents=True, exist_ok=True) before write)
- [high] Skill path existence not validated before read (IO-003 — PARTIALLY VALID: get_skill_config() returns empty config, hook handles via `not config.get("discovered")` check at line 134)
- [medium] JSON serialization error handling not described (IO-004 — valid observation, no try/except around json.dump in create_run path)
- [low] terminal_id may contain invalid filename characters (IO-005 — valid: detect_terminal_id() can return colons on Windows)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance, COMP-002) — specialists reviewing plugin-installer scope but work.md describes skill-guard hook. Target plugin misidentified. (skill-guard plugin, not plugin-installer)
1.2. [HIGH] (source: adversarial-io-validation, IO-001) — same misidentification — ExecutionRuntime exists in skill-guard, not plugin-installer

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-io-validation, IO-005) — terminal_id may contain `:` or other Windows-invalid filename chars. Path construction could fail for edge-case IDs.
2.2. [MEDIUM] (source: adversarial-security, SEC-002) — Plugin names from `iterdir()` not validated as safe identifiers before subprocess use. Shell metacharacters in plugin names could affect command execution.

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (source: adversarial-compliance, COMP-004) — audit script uses `Path(str(script_path).replace(...))` for env var expansion. Naive string replace can corrupt paths containing the env var name as substring. Use `os.path.expandvars()` instead. (plugin-audit-and-fix.py:161)
3.2. [LOW] (source: adversarial-compliance, COMP-005) — validate skill has `enforcement: advisory`. Consider `blocking` to prevent non-compliant plugin installation.

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-io-validation, IO-004) — No try/except around JSON serialization in `create_run()`. Type errors or circular refs raise uncaught. execution-state.json could be partially written.
4.2. [LOW] (source: adversarial-security, SEC-003) — `<name>` placeholder in install SKILL.md inline Python not validated before writing to settings.json. Malformed entries possible if placeholder not replaced.

### Concrete Recommendations
5.1. [MEDIUM] (source: adversarial-compliance) — Fix env var expansion in audit script: replace `Path(str(script_path).replace(f"${var}", replacement))` with `Path(os.path.expandvars(str(script_path)))`. (plugin-audit-and-fix.py:161)
5.2. [MEDIUM] (source: adversarial-io-validation) — Add `try/except (TypeError, ValueError)` around `json.dump` in the store's write path to handle serialization failures gracefully.
5.3. [LOW] (source: adversarial-io-validation) — Sanitize terminal_id in path construction: filter Windows-invalid chars (`:`, `<`, `>`, `|`) before using as path component. (execution_store.py path construction)

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-compliance) — Should plugin-installer self-audit itself with `--scan-paths`, or exclude itself? Currently hardcoded paths in SKILL.md would trigger findings on the auditor itself.
6.2. [LOW] (source: adversarial-security) — Should plugin names be restricted to `[\w-]+` pattern? Current iteration includes all names not starting with `.`.
