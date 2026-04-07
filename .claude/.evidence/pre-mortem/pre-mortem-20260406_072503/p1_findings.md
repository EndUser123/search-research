# Phase 1 Findings — /rca Skill Pre-Mortem

## Triage Classification

**skill** — RCA (Root Cause Analysis) Claude Code skill at `P:/.claude/skills/rca/`. Contains SKILL.md, tools/, references/, hooks/, and documentation files.

## Dispatched Specialists

- **adversarial-critic**: Meta-critique of Phase 1 dispatch quality — dispatched with wrong target (pre-mortem skill instead of RCA). Findings relate to SQA skill review, not RCA review. Marked as dispatch error.
- **adversarial-compliance**: YAML frontmatter, hook registration, schema, path consistency across RCA documentation
- **adversarial-quality**: Maintainability, silent failures, import fragility, concurrency safety in RCA hook files

## Specialist Findings Summary

### adversarial-critic
**Domain:** Meta-critique of Phase 1 dispatch
**Key findings:**
- Dispatch error: Target was pre-mortem skill, not RCA. The `work at: P:/.claude/skills/pre-mortem/` instruction was correct, but the agents it reviewed (adversarial-logic, adversarial-security, etc.) were SQA skill findings, not RCA findings.
- LOGIC-001 and LOGIC-002 (off-by-one errors in layer files) are NON_REPRODUCIBLE — code doesn't match claims
- SEC-005 verified but severity inflated (LOW not HIGH)
- 25 of 29 findings had no specific file:line citation

### adversarial-compliance
**Domain:** Schema, spec, API contract compliance
**Key findings:**
- [HIGH] Conflicting evidence tier definitions across documents (COMP-001)
- [HIGH] pytest.ini points to non-existent directory debugRCA (COMP-002)
- [HIGH] SKILL.md references non-existent hook directory (COMP-003)
- [HIGH] Workflow state file path inconsistency (COMP-004)
- [MEDIUM] Phase/Step terminology inconsistency (COMP-005)
- [MEDIUM] Search templates reference wrong directory src/ (COMP-006)
- [MEDIUM] INTEGRATION_SUMMARY.md references deprecated paths (COMP-007)
- [MEDIUM] Environment variable naming inconsistency DEBUGRCA_ (COMP-008)
- [LOW] Template selection guidance missing (COMP-009)
- [LOW] Weight constants duplicated in plan and code (COMP-010)

### adversarial-quality
**Domain:** Maintainability, tech debt, silent failures
**Key findings:**
- [HIGH] FileLock fallback silently proceeds without lock — data corruption risk (QUAL-001)
- [MEDIUM] Import path fragility causes silent fallback to None (QUAL-002)
- [MEDIUM] Module-level _settings_cache not thread-safe (QUAL-003)
- [LOW] Duplicate docstring in check_recent_errors (QUAL-004)
- [LOW] Inconsistent error reporting style across hooks (QUAL-005)

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-compliance) — Conflicting evidence tier definitions. SKILL.md:130-138 defines Tier 1-4 (95%/85%/75%/50%), GENERIC_PROTOCOL.md:17-27 defines Tier 0-4 (20%/40%/60%/85%/95%). Investigators using different docs get different confidence levels.

1.2. [HIGH] (source: adversarial-compliance) — pytest.ini rootdir = `P:\.claude\skills\debugRCA` but actual directory is `rca`. Tests will fail to run from configured root.

1.3. [HIGH] (source: adversarial-compliance) — SKILL.md:53 references hooks at `$CLAUDE_PROJECT_DIR/.claude/skills/rca/hooks/` but no hooks/ subdirectory exists in `P:/.claude/skills/rca/`. RCA enforcement hooks are non-functional.

1.4. [HIGH] (source: adversarial-compliance) — workflow-state-validation.md:6 specifies `~/.claude/state/rca/rca_workflow.json` but inspect_runtime_state.py:32 defaults to `P:/.claude/hooks/state`. State management is split across two paths.

### Hidden Assumptions & Fragile Dependencies

2.1. [HIGH] (source: adversarial-quality) — FileLock fallback in all 5 hook files (__enter__ returns self without acquiring lock). Concurrent multi-terminal writes are NOT protected, risking rca_workflow.json corruption.

2.2. [MEDIUM] (source: adversarial-quality) — Import path fragility: `sys.path.insert` for rca package fails silently when pip-installed (not dev mode), falling back to `None` with no user warning. Metrics/tracking silently disabled.

2.3. [MEDIUM] (source: adversarial-quality) — _settings_cache module-level dict in hook_error_rca.py:192 accessed without locking. ThreadPoolExecutor in _stage2_test() can cause race conditions.

2.4. [MEDIUM] (source: adversarial-compliance) — Search templates in references/search-templates.md assume `src/` directory. RCA operates on `P:/.claude/` hooks and skills — investigators will search non-existent paths.

2.5. [MEDIUM] (source: adversarial-compliance) — INTEGRATION_SUMMARY.md:15 references `P:\.claude\skills\debugrca\` (deprecated), misleading anyone following it for setup.

### Missing Obvious Actions / Best Practices

3.1. [HIGH] — Create the missing `P:/.claude/skills/rca/hooks/` directory with the hooks SKILL.md references, OR update SKILL.md to point to actual hook locations if they exist elsewhere.

3.2. [HIGH] — Update pytest.ini rootdir from `debugRCA` to `rca`.

3.3. [MEDIUM] — Add stderr warning when optional rca package imports fail (QUAL-002 fix). Currently silent degradation.

3.4. [MEDIUM] — Unify workflow state file path: choose `~/.claude/state/rca/` as canonical and update inspect_runtime_state.py and workflow-state-validation.md to match.

3.5. [MEDIUM] — Add `assert self._acquired` after FileLock.__enter__ to fail fast when portalocker unavailable, rather than silently proceeding without protection.

3.6. [MEDIUM] — Update search-templates.md to reference `P:/.claude/` instead of `src/`.

3.7. [MEDIUM] — Update INTEGRATION_SUMMARY.md deprecated `debugrca` path references to `rca`.

3.8. [MEDIUM] — Update SKILL.md to consistently use `DEBUGRCA_` prefix for all environment variables.

### Risks and Edge Cases

4.1. [MEDIUM] — Multi-terminal concurrent RCA sessions risk state file corruption due to no-op FileLock fallback. No warning given to users.

4.2. [MEDIUM] — When rca is pip-installed (non-dev mode), all metrics tracking and action tracing silently stop working. User gets no feedback.

4.3. [LOW] — Duplicate docstring in check_recent_errors (hook_error_rca.py:580) causes maintenance confusion.

4.4. [LOW] — Inconsistent error reporting (sys.stderr.write vs logger.warning vs logger.error) makes hook debugging harder.

### Concrete Recommendations

5.1. [HIGH] (adversarial-compliance) — Fix pytest.ini rootdir: `rootdir = P:\.claude\skills\rca`

5.2. [HIGH] (adversarial-compliance) — Audit all path references in RCA documentation. Update SKILL.md hooks path, INTEGRATION_SUMMARY.md deprecated paths, search-templates.md src/ references.

5.3. [HIGH] (adversarial-quality) — Add `_acquired` flag to FileLock fallback and assert after __enter__:
   ```python
   assert self._acquired, 'FileLock: portalocker unavailable, proceeding without lock'
   ```

5.4. [MEDIUM] (adversarial-compliance) — Unify evidence tier system: adopt GENERIC_PROTOCOL.md's 5-tier as canonical, update SKILL.md and output-format.md.

5.5. [MEDIUM] (adversarial-quality) — Add stderr warning on import fallback:
   ```python
   except ImportError as e:
       sys.stderr.write(f'[RCA] Optional import failed: {e}. Metrics disabled.\n')
   ```

5.6. [MEDIUM] (adversarial-compliance) — Add threading.Lock around _settings_cache or accept O(1) re-read per call.

5.7. [LOW] (adversarial-quality) — Consolidate duplicate check_recent_errors docstring Args sections.

5.8. [LOW] (adversarial-quality) — Standardize error reporting: sys.stderr.write for '[MODULE] message' format, logger for multi-line.

### Open Questions / Unknowns

6.1. [LOW] — Where do the actual RCA hooks live? SKILL.md references `$CLAUDE_PROJECT_DIR/.claude/skills/rca/hooks/` but Glob found no hooks/ subdir in rca/. Are hooks defined elsewhere (e.g., in the main hooks/ directory)?

6.2. [LOW] — Was the debugRCA → rca rename ever fully cleaned up? INTEGRATION_SUMMARY.md still references old paths. Any other stale references?

6.3. [LOW] — adversarial-critic noted 25 of 29 findings had no specific file:line citation. This limits verifiability — RCA reviews may produce findings that can't be actioned.

---

## Dispatch Error Note

The adversarial-critic agent was instructed to review `P:/.claude/skills/pre-mortem/` (the pre-mortem skill) rather than `P:/.claude/skills/rca/` (the RCA skill). Its findings relate to SQA skill layer files, not RCA code. The dispatch instruction used the pre-mortem path instead of the RCA path. The Phase 1 Completion Gate still passed (3 specialist JSONs existed) so this error was not caught. Consider adding a target verification step to the gate.
