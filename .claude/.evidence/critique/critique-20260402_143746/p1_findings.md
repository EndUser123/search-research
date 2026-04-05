# Phase 1 Findings — /critique Skill Review

## Triage Classification

**skill** — The /critique skill (adaptive adversarial multi-agent review framework)

## Dispatched Specialists

- **adversarial-critic**: Reasoning quality, phase logic, trigger matching, structural consistency
- **adversarial-compliance**: YAML frontmatter, path references, function signatures, schema compliance
- **adversarial-quality**: Maintainability, skill structure, code complexity, hardcoded paths

## Specialist Findings Summary

### adversarial-critic (10 findings: 2 HIGH, 4 MEDIUM, 4 LOW)
**Domain:** Reasoning quality, phase logic, dispatch mechanism

Key findings:
- **[HIGH]** Bash cat command in idempotency check contradicts Read-tool pattern (p1_initial_review.md:60)
- **[HIGH]** Task dispatch uses Bash heredoc syntax mixing shell and Task tool conventions (p1_initial_review.md:68-80)
- **[MEDIUM]** Health Score formula references CRITICAL severity but schema only defines HIGH/MEDIUM/LOW
- **[MEDIUM]** Context-Aware Resolution underspecified for recursive `/critique on /critique` case

### adversarial-compliance (8 findings: 2 HIGH, 2 MEDIUM, 4 LOW)
**Domain:** YAML schema, path references, function signatures, contract compliance

Key findings:
- **[HIGH]** `_append_skill_coverage` called with wrong arg signature — missing `project_root` keyword arg (lib/critique_io.py:276-281)
- **[HIGH]** Agent dispatch path `P:/.claude/agents/{specialist}.md` referenced but subagent received wrong path `P:/skills/critique/` (path corruption in orchestrator template)
- **[MEDIUM]** Path traversal guard uses string prefix matching instead of `relative_to()` (lib/critique_io.py:169)
- **[MEDIUM]** Idempotency check uses global paths but Phase 1 dispatches to session-scoped paths

### adversarial-quality (10 findings: 4 HIGH, 4 MEDIUM, 2 LOW)
**Domain:** Maintainability, structure, hardcoded paths, execution flow

Key findings:
- **[HIGH]** Path inconsistency: p1 says `P:/{session_dir}/specialists/` but agents write to `P:/.claude/plans/adversarial/` (p1_initial_review.md:56-66)
- **[HIGH]** Step 8a confirmation gate does NOT pause — "0" directive auto-executes without user confirmation (SKILL.md:233-289)
- **[HIGH]** Hardcoded P:/ drive paths for gto lib and skill_guard imports — not portable (critique_io.py:44-47, 69-75)
- **[HIGH]** Idempotency check always skips because path `P:/{session_dir}/specialists/` never exists

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. **[HIGH]** (source: adversarial-critic, adversarial-quality) — Idempotency check path mismatch: Step 3 checks `P:/{session_dir}/specialists/` but agents write to `P:/.claude/plans/adversarial/{name}-findings.json`. Check always skips, always re-dispatches. (p1_initial_review.md:56-66, QUAL-002)

1.2. **[HIGH]** (source: adversarial-compliance) — Path corruption in dispatch template: subagents received `P:/skills/critique/` (missing `.claude` segment) instead of `P:/.claude/skills/critique/`. The `{WORK_FILE}` variable in the dispatch template gets substituted from work.md content. (p1_initial_review.md:78, COMP-001)

1.3. **[MEDIUM]** (source: adversarial-critic) — Task dispatch uses Bash heredoc syntax (`Task(\n  subagent_type="general-purpose",\n  description=..."`) which mixes shell heredoc format with Task tool syntax. Should use explicit Task tool syntax. (p1_initial_review.md:68-80, CRIT-002)

1.4. **[MEDIUM]** (source: adversarial-compliance) — p2_meta_critique.md lists only 4 fixed specialist paths but Phase 1 dispatches up to 10 specialist types. Phase 2 reads a hardcoded subset, missing outputs from other dispatched specialists. (p2_meta_critique.md:16-20, CRIT-005)

1.5. **[MEDIUM]** (source: adversarial-quality) — `_get_terminal_id()` fallback uses `fallback_{pid}_{md5hash}` which is not stable — on Windows `os.getpid()` can be reused across process lifetimes, causing ID collisions. (critique_io.py:56-86, QUAL-008)

### Hidden Assumptions & Fragile Dependencies

2.1. **[HIGH]** (source: adversarial-quality) — Hardcoded P:/ drive paths: (1) gto lib imported from `P:/.claude/skills/gto/lib`, (2) skill_guard imported dynamically. If Claude Code runs from a different drive or .claude is relocated, skill coverage logging silently fails. (critique_io.py:44-47, 69-75, QUAL-004)

2.2. **[MEDIUM]** (source: adversarial-compliance) — Path traversal guard uses `str(resolved_dir).startswith(str(resolved_root) + str(Path('/')))`. On Windows, `Path('/')` produces `\` (backslash), but Unix paths use `/` (forward slash). The string concatenation produces `C:\path\StartsWith(C:\root\` which may not catch actual traversal. Use `resolved_dir.relative_to(resolved_root)` instead. (critique_io.py:169, COMP-003)

2.3. **[LOW]** (source: adversarial-quality) — Timestamp collision loop in `CritiqueSession.__init__` has no max-iterations guard. If filesystem quirks cause persistent collisions, loop runs forever. (critique_io.py:100-104, QUAL-009)

2.4. **[LOW]** (source: adversarial-compliance) — GTO library import hardcodes `P:/.claude/skills` as sys.path entry. No fallback if directory is relocated. (critique_io.py:44-47, COMP-008)

### Missing Obvious Actions / Best Practices

3.1. **[HIGH]** (source: adversarial-quality) — Step 8a confirmation gate text says it "requires acknowledgment" but implementation does not pause. The "0 — Do ALL" directive auto-executes without user confirmation, violating the stated gate. (SKILL.md:233-289, QUAL-003)

3.2. **[HIGH]** (source: adversarial-compliance) — `_append_skill_coverage` called with 5 positional args but function signature requires `project_root` as keyword-only. Import error is silently caught by bare `except Exception`, causing skill coverage to never be logged. (lib/critique_io.py:276-281, COMP-002)

3.3. **[MEDIUM]** (source: adversarial-critic) — Health Score formula references `CRITICAL×20` but the 7-section output schema only defines HIGH/MEDIUM/LOW. Formula produces wrong results if any finding is tagged CRITICAL. (SKILL.md:190, CRIT-003)

3.4. **[MEDIUM]** (source: adversarial-critic) — Context-Aware Resolution has no recursion guard for `/critique on /critique`. Could cause infinite dispatch loop. (SKILL.md:82-96, CRIT-004)

3.5. **[MEDIUM]** (source: adversarial-quality) — "Blinded Consumer Review" section says "Phase 1 must include" but no phase file implements it as a checklist item or specialist dispatch. (SKILL.md:54-63 + p1_initial_review.md, QUAL-005)

3.6. **[LOW]** (source: adversarial-compliance) — `suggest: []` in SKILL.md frontmatter is empty but routing section lists valid suggestions (/verify, /pre-mortem, /reflect). (SKILL.md:9, COMP-005)

3.7. **[LOW]** (source: adversarial-compliance) — Health Score thresholds (>=80% healthy, 50-79% warning, <50% critical) have no evidence citation or derivation. Should be marked [UNVERIFIED] per constitutional rules. (SKILL.md:186-188, COMP-006)

3.8. **[LOW]** (source: adversarial-compliance) — Output format says filename `p1.md` but Step 3 says `p1_findings.md`. Inconsistent. (p1_initial_review.md:99, COMP-007)

### Risks and Edge Cases

4.1. **[MEDIUM]** (source: adversarial-quality) — Phase 2 hardcoded to only 4 specialist types but Phase 1 can dispatch 10+. If Phase 1 dispatches security or testing for code targets, Phase 2 silently ignores those outputs. (p2_meta_critique.md:17-20, QUAL-007)

4.2. **[LOW]** (source: adversarial-critic) — Routing suggestions (/verify, /pre-mortem, /reflect) have no trigger criteria. Could suggest wrong skill for given finding type. (SKILL.md:295-301, CRIT-010, QUAL-010)

4.3. **[LOW]** (source: adversarial-critic) — "Blinded Consumer Review" is mandated but has no implementation guide. May be ignored or implemented inconsistently. (SKILL.md:54-63, CRIT-009)

4.4. **[LOW]** (source: adversarial-critic) — Phase 3 synthesis mandatory verification step says "Pick 3 file:line citations from Phase 1/2 output and verify they exist" — but skill/document findings cite section names not file:line. Verification approach is mismatched to finding types. (p3_synthesis.md:13-22, CRIT-006)

4.5. **[LOW]** (source: adversarial-quality) — GTO lib imported at module level creates startup dependency. If gto package has issues, entire critique skill fails to load. Should be lazy import inside function. (critique_io.py:44-47, QUAL-010, CRIT-007)

### Concrete Recommendations

5.1. **[HIGH]** Fix idempotency check path: Change Step 3 to check `P:/.claude/plans/adversarial/{name}-findings.json` (the actual output path) instead of `P:/{session_dir}/specialists/`. (p1_initial_review.md:56-66)

5.2. **[HIGH]** Fix dispatch path substitution: The dispatch template's `{WORK_FILE}` substitutes content from work.md which contained `P:/skills/critique/`. Template should use canonical path directly, not a variable that resolves to a wrong path. (p1_initial_review.md:78)

5.3. **[HIGH]** Fix Step 8a confirmation gate: Add an explicit `AskUserQuestion` or confirm directive that PAUSES before any file modification. Current text describes blocking but doesn't implement it. (SKILL.md:233-289)

5.4. **[HIGH]** Fix `_append_skill_coverage` call: Add `project_root=Path.cwd()` as keyword arg. Change `except Exception` to `except (ImportError, AttributeError)` to catch only the specific failure mode. (lib/critique_io.py:276-281)

5.5. **[HIGH]** Replace hardcoded P:/ paths with dynamic resolution: Use `importlib.util.find_spec` or settings-based path to locate gto lib and skill_guard. (critique_io.py:44-47, 69-75)

5.6. **[MEDIUM]** Replace string-prefix path traversal check with `relative_to()`: `resolved_dir.relative_to(resolved_root)` raises `ValueError` if outside root — cleaner and cross-platform. (lib/critique_io.py:169)

5.7. **[MEDIUM]** Add CRITICAL to Health Score schema or remove from formula: The formula uses `CRITICAL×20` but schema has no CRITICAL tier. Either add CRITICAL to schema or cap at `HIGH×10`. (SKILL.md:190)

5.8. **[MEDIUM]** Add recursion guard for `/critique on /critique`: If target equals current skill name or matches current skill path, treat as display-only and do not dispatch. (SKILL.md:82-96)

5.9. **[MEDIUM]** Make Phase 2 file list dynamic: Read what files actually exist in `P:/.claude/plans/adversarial/` rather than hardcoding 4 fixed names. (p2_meta_critique.md:16-20)

5.10. **[MEDIUM]** Add `_get_terminal_id()` stability fix: Include timestamp or thread ID in fallback to prevent pid reuse collisions. (critique_io.py:56-86)

5.11. **[MEDIUM]** Implement Blinded Consumer Review as explicit checklist item in p1_initial_review.md, not just a note in SKILL.md. (p1_initial_review.md + SKILL.md:54-63)

5.12. **[LOW]** Populate `suggest: ["verify", "pre-mortem", "reflect"]` in SKILL.md frontmatter. (SKILL.md:9)

5.13. **[LOW]** Fix p1_findings.md filename inconsistency: Change schema output reference from `p1.md` to `p1_findings.md`. (p1_initial_review.md:99)

5.14. **[LOW]** Add max-iterations to timestamp collision loop. (critique_io.py:100-104)

5.15. **[LOW]** Distinguish verification scope in Phase 3: file:line for code findings, section-existence for skill/plan findings. (p3_synthesis.md:13-22)

### Open Questions / Unknowns

6.1. **[MEDIUM]** (source: adversarial-critic) — The "Blinded Consumer Review" section: is it meant to be a separate specialist agent or an inline checklist? Affects how it should be implemented in Phase 1. (CRIT-009)

6.2. **[MEDIUM]** (source: adversarial-quality) — Is the P:/ drive hardcoding intentional (deploy constraint) or should paths be resolved dynamically? If intentional, should be documented in SKILL.md constraints. (QUAL-004)

6.3. **[LOW]** (source: adversarial-compliance) — Health Score thresholds (80/50/50) have no derivation. Are these empirical, copied from elsewhere, or arbitrary? Need evidence source or should be marked [UNVERIFIED]. (COMP-006)

6.4. **[LOW]** (source: adversarial-critic) — Routing suggestions (/verify, /pre-mortem, /reflect) — should there be a fourth option for when findings are purely about process/workflow, not code? (CRIT-010)
