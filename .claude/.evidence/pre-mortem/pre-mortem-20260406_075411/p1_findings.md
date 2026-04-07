# Phase 1 Findings — /rca Skill Pre-Mortem

## Triage Classification

**skill** — RCA (Root Cause Analysis) Claude Code skill at `P:/.claude/skills/rca/`. Contains SKILL.md, tools/, references/, hooks/, and documentation files.

## Dispatched Specialists

- **adversarial-critic**: Meta-critique analyzing the other two specialists' quality, blind spots, contradictions, and calibration
- **adversarial-compliance**: YAML frontmatter, hook registration, schema, path consistency across RCA documentation
- **adversarial-quality**: Maintainability, silent failures, import fragility, concurrency safety in RCA hook files

## Specialist Findings Summary

### adversarial-critic
**Domain:** Meta-critique of Phase 1 dispatch quality
**Key findings:**
- **Consensus (verified):** FileLock fallback silently proceeds without lock — both compliance and quality flagged this as HIGH
- **[CRITICAL] Blind spot:** Hook error detection bypass via stderr suppression — sys.stderr.write() triggers Claude Code hook error cascade, masking actual root cause
- **[HIGH] Blind spot:** SKILL.md path resolution vs actual hook location — hooks exist but `$CLAUDE_PROJECT_DIR` may not resolve at runtime
- **[HIGH] Blind spot:** pytest.ini rootdir points to non-existent `debugRCA` directory
- **[MEDIUM] Blind spot:** Evidence tier definitions conflict across documents
- **Contradiction:** COMP-003 claims hooks don't exist — but hooks DO exist at `P:/.claude/skills/rca/hooks/`. The issue is path resolution, not absence.
- **Calibration:** COMP-003 was overconfident (hooks DO exist); QUAL-001 and COMP-004 were appropriately calibrated
- 6 of 12 meta-findings had no specific file:line citation

### adversarial-compliance
**Domain:** Schema, spec, API contract compliance
**Key findings:**
- [HIGH] COMP-001: pytest.ini rootdir = `debugRCA` but actual directory is `rca`
- [MEDIUM] COMP-002: Evidence tier definitions conflict (SKILL.md Tier 1-4 vs GENERIC_PROTOCOL.md Tier 0-4)
- [HIGH] COMP-003: SKILL.md:53 uses `$CLAUDE_PROJECT_DIR` for hook paths — may not resolve at runtime
- [HIGH] COMP-004: FileLock fallback silently proceeds without lock (corroborated by QUAL-001)

### adversarial-quality
**Domain:** Maintainability, tech debt, silent failures
**Key findings:**
- [HIGH] QUAL-001: FileLock fallback silently proceeds without acquiring lock — data corruption risk
- [HIGH] QUAL-002: pytest.ini rootdir points to non-existent `debugRCA` directory
- [MEDIUM] QUAL-003: Evidence tier definitions conflict (corroborates COMP-002)
- [MEDIUM] QUAL-004: sys.stderr.write() for error reporting creates catch-22 error cascade
- [MEDIUM] QUAL-005: SKILL.md hook path uses `$CLAUDE_PROJECT_DIR` (corroborates COMP-003)
- [LOW] QUAL-006: Silent import fallbacks create hidden missing functionality
- [LOW] QUAL-007: conftest.py has hardcoded absolute paths
- [LOW] QUAL-008: detect_phase_from_output has inefficient nested loop with repeated regex compilation

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-compliance COMP-001, adversarial-quality QUAL-002) — pytest.ini rootdir = `P:\.claude\skills\debugRCA` but actual directory is `P:/.claude/skills/rca`. Tests will fail to run from configured root. (`P:/.claude/skills/rca/pytest.ini:5`)

1.2. [HIGH] (source: adversarial-compliance COMP-003, adversarial-quality QUAL-005, adversarial-critic blind spot) — SKILL.md:53 references hooks at `$CLAUDE_PROJECT_DIR/.claude/skills/rca/hooks/` but hooks exist at `P:/.claude/skills/rca/hooks/`. Path resolution may fail at runtime. Adversarial-critic notes: compliance agent claimed hooks don't exist, but they DO exist — the issue is the env var, not absence.

1.3. [MEDIUM] (source: adversarial-compliance COMP-002, adversarial-quality QUAL-003, adversarial-critic blind spot) — Conflicting evidence tier definitions. SKILL.md:130-138 defines Tier 1-4 (95%/85%/75%/50%), GENERIC_PROTOCOL.md:17-27 defines Tier 0-4 (20%/40%/60%/85%/95%). RCA findings from different sessions have incomparable confidence levels.

### Hidden Assumptions & Fragile Dependencies

2.1. [CRITICAL] (source: adversarial-critic blind spot, adversarial-quality QUAL-004) — Hook error reporting uses sys.stderr.write(), but Claude Code treats ANY stderr as a hook error. This creates a catch-22 where error reporting triggers error cascade, masking the actual root cause. No mechanism exists to report errors without triggering hook failure. (`P:/.claude/skills/rca/hooks/hook_error_rca.py:104`)

2.2. [HIGH] (source: adversarial-quality QUAL-001, adversarial-compliance COMP-004, adversarial-critic consensus) — FileLock fallback in all 5 hook files (__enter__ returns self without acquiring lock). Concurrent multi-terminal writes are NOT protected, risking rca_workflow.json corruption.

2.3. [MEDIUM] (source: adversarial-quality QUAL-006) — Silent import fallbacks: `record_delegation_event` and `should_trigger_research` become None when rca package imports fail, with no user warning. Auto-research and delegation metrics silently stop working.

2.4. [LOW] (source: adversarial-quality QUAL-007) — conftest.py has hardcoded absolute paths (`P:/packages/rca/src`, `P:/__csf/src`) that may not exist in all environments.

### Missing Obvious Actions / Best Practices

3.1. [HIGH] — Update pytest.ini rootdir from `debugRCA` to `rca` (`P:/.claude/skills/rca/pytest.ini:5`)

3.2. [HIGH] — Verify or fix `$CLAUDE_PROJECT_DIR` hook path resolution in SKILL.md. Use `CLAUDE_PLUGIN_ROOT` or absolute paths instead.

3.3. [CRITICAL] — Replace sys.stderr.write() error reporting with logger.warning() or collected stdout warnings to prevent hook error cascade.

3.4. [MEDIUM] — Unify evidence tier system: adopt GENERIC_PROTOCOL.md's 5-tier (Tier 0-4) as canonical, update SKILL.md and output-format.md to match.

3.5. [MEDIUM] — Add `_acquired` flag to FileLock fallback and assert after __enter__, or make portalocker a hard dependency.

3.6. [MEDIUM] — Add stderr warning when optional rca package imports fail (QUAL-006 fix).

3.7. [LOW] — Precompile regex patterns in detect_phase_from_output at module load time instead of per-call.

3.8. [LOW] — Replace hardcoded absolute paths in conftest.py with relative path discovery.

### Risks and Edge Cases

4.1. [HIGH] — Multi-terminal concurrent RCA sessions risk state file corruption due to no-op FileLock fallback. No warning given to users.

4.2. [MEDIUM] — When rca is pip-installed (non-dev mode), all metrics tracking and action tracing silently stop working. User gets no feedback.

4.3. [MEDIUM] — Hook path resolution via `$CLAUDE_PROJECT_DIR` may fail silently on different Claude Code installations or configurations.

4.4. [LOW] — Inefficient regex compilation in detect_phase_from_output adds minor overhead per tool use.

### Concrete Recommendations

5.1. [HIGH] (adversarial-compliance COMP-001, adversarial-quality QUAL-002) — Fix pytest.ini: `rootdir = P:/.claude/skills/rca`

5.2. [HIGH] (adversarial-compliance COMP-003, adversarial-quality QUAL-005) — Audit all `$CLAUDE_PROJECT_DIR` references in SKILL.md and replace with verified paths or environment variables

5.3. [CRITICAL] (adversarial-quality QUAL-004) — Replace sys.stderr.write() with logger.warning() or collected stdout warnings in hook_error_rca.py and all hook files

5.4. [HIGH] (adversarial-quality QUAL-001, adversarial-compliance COMP-004) — Add `_acquired` flag to FileLock fallback:
   ```python
   assert self._acquired, 'FileLock: portalocker unavailable, proceeding without lock'
   ```

5.5. [MEDIUM] (adversarial-compliance COMP-002, adversarial-quality QUAL-003) — Unify evidence tier system to GENERIC_PROTOCOL.md 5-tier canonical

5.6. [MEDIUM] (adversarial-quality QUAL-006) — Add stderr warning on import fallback:
   ```python
   except ImportError as e:
       sys.stderr.write(f'[RCA] Optional import failed: {e}. Metrics disabled.\n')
   ```

5.7. [LOW] (adversarial-quality QUAL-008) — Precompile regex patterns at module level in detect_phase_from_output

5.8. [LOW] (adversarial-quality QUAL-007) — Use relative path discovery in conftest.py

### Open Questions / Unknowns

6.1. [MEDIUM] — Where do the actual RCA hooks register? SKILL.md references `$CLAUDE_PROJECT_DIR/.claude/skills/rca/hooks/` but hooks exist at `P:/.claude/skills/rca/hooks/`. Is `$CLAUDE_PROJECT_DIR` documented to resolve to `P:/`?

6.2. [LOW] — Was the debugRCA → rca rename ever fully cleaned up? pytest.ini still references `debugRCA`. Any other stale references?

6.3. [LOW] — adversarial-critic found 6 of 12 meta-findings had no specific file:line citation. Does this affect the reliability of the meta-critique itself?
