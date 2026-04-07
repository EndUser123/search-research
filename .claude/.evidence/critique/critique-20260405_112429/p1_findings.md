## Triage Classification
**skill** — SQA is a multi-layer quality orchestration skill with Agent-based and CLI-based layers. The review focuses on skill structure, schema compliance, and implementation gaps.

## Dispatched Specialists
- **adversarial-critic**: Phase logic, trigger matching, execution contract gaps
- **adversarial-compliance**: YAML frontmatter, schema compliance, non-existent agent references
- **adversarial-quality**: Maintainability, stub implementations, Agent-vs-CLI confusion
- **adversarial-testing**: Test coverage gaps, untested orchestration logic

## Specialist Findings Summary

### adversarial-critic
**Domain:** reasoning quality, phase logic, trigger matching

**Key findings:**
- [HIGH] L0 Predictive layer claims agent dispatch but layer0_predictive.py returns empty list — execution gap (SKILL.md:106-113; layer0_predictive.py:31-99)
- [HIGH] Phase detection table claims state-machine routing with no implementation (SKILL.md:79-88)
- [HIGH] Health score formula in SKILL.md differs materially from findings/models.py implementation (SKILL.md:157; findings/models.py:114-155)
- [MEDIUM] Auto-detect has two conflicting resolution hierarchies (lines 58-68 vs 70-77)
- [MEDIUM] Layer 7 contract integrity checks are underspecified vs. what tools actually verify
- [LOW] Deduplication key uses title (fragile) and allows optional location (breaks deduplication)

### adversarial-compliance
**Domain:** YAML frontmatter, hook registration, schema compliance

**Key findings:**
- [HIGH] Non-standard frontmatter fields not in SKILL_SCHEMA: `version`, `status`, `entry_type`, `requires_target`, `enforcement`
- [HIGH] Missing `execution` block — required by schema but absent
- [HIGH] Layer 0 references 7 non-existent skill agents (adversarial-logic, adversarial-quality, adversarial-io-validation, adversarial-security, adversarial-performance, adversarial-testing, adversarial-state-machine)
- [HIGH] Layer 5 references non-existent `adversarial-security` agent (SKILL.md:100)
- [HIGH] Layer 6 references non-existent `adversarial-performance` agent (SKILL.md:101)
- [MEDIUM] `enforcement: none` has unclear semantics — field not defined in schema
- [LOW] Missing `do_not` prohibited actions block

### adversarial-quality
**Domain:** maintainability, skill structure

**Key findings:**
- [HIGH] Layer 0 is a pure stub — cannot dispatch Agent subagents, returns empty list
- [HIGH] L5/L6 share identical Agent-vs-CLI confusion: `_run_adversarial_*` checks `shutil.which()` then calls `subprocess.run()` — always fails silently
- [HIGH] No actual adversarial skills exist — `adversarial-*` are Agent names, not skill names
- [MEDIUM] ALLOWED_COMMANDS duplicated in orchestrator.py and layer5_security.py with inconsistent content
- [MEDIUM] SKILL.md Target Resolution section duplicated verbatim (lines 58-67 and 70-77)
- [LOW] SKILL.md at 327 lines too large for single-file maintainability

### adversarial-testing
**Domain:** test coverage, missing scenarios, brittle tests

**Key findings:**
- [HIGH] L2→L4 hard dependency skip logic has empty `pass` tests — no actual verification
- [HIGH] L0 PREDICTIVE layer dispatch has zero tests
- [HIGH] `--halt-on` raw-count behavior has no tests (critical distinction from deduplicated health score)
- [HIGH] Phase/State Detection table has no tests
- [HIGH] `--fix-all` iterative loop has no tests
- [MEDIUM] L3/L7 tests only assert "returns a list" — no behavioral verification
- [MEDIUM] Focus lens propagation to Agent-based layers (L0/L5/L6) has no tests

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-critic) — **L0 execution gap**: SKILL.md declares L0 dispatches 7 adversarial agents via Agent tool; layer0_predictive.py is a stub that returns empty list. The skill defines a capability the Python implementation cannot deliver. (SKILL.md:106-113; layer0_predictive.py:71-99)

1.2. [HIGH] (source: adversarial-compliance) — **9 non-existent agent references**: Layer 0 references 7 adversarial agents, Layer 5 references `adversarial-security`, Layer 6 references `adversarial-performance` — none exist in `P:/.claude/skills/`. These are Agent subagent names, not skill invocations. (SKILL.md:95, 100-101)

1.3. [HIGH] (source: adversarial-critic) — **Health score formula mismatch**: SKILL.md documents `100 - unique_CRITICAL*20 - unique_HIGH*10...` but implementation uses deduplication + evidence tier weighting (T1=1.0x, T2=0.75x, T3=0.5x, T4=0.25x). Not equivalent. (SKILL.md:157; findings/models.py:114-155)

1.4. [HIGH] (source: adversarial-quality) — **L5/L6 Agent-vs-CLI confusion**: `_run_adversarial_security` and `_run_adversarial_performance` check `shutil.which('adversarial-X')` then call `subprocess.run(['adversarial-X', ...])` — always fails silently. adversarial-* are Agent subagents, not CLI commands. (layer5_security.py:182-227; layer6_performance.py:110-157)

1.5. [HIGH] (source: adversarial-compliance) — **Missing execution block**: SKILL_SCHEMA requires `execution.directive/default_args/examples`; SQA has no execution block. (SKILL.md:1-12)

1.6. [MEDIUM] (source: adversarial-critic) — **Auto-detect has two conflicting hierarchies**: Auto-Detect Target (58-68) vs Target Resolution table (70-77) use different names for similar concepts. Additionally Phase/State Detection describes a SEPARATE state machine not integrated with either. (SKILL.md:58-88)

1.7. [MEDIUM] (source: adversarial-critic) — **L4 hard dependency conflates test failures with requirements**: L2 runs pytest; L4 validates spec. Test failures can be environment-related, not requirements-related. Requirements validation should potentially run even when tests fail. (SKILL.md:175-176)

### Hidden Assumptions & Fragile Dependencies

2.1. [HIGH] (source: adversarial-compliance) — **Non-standard frontmatter fields**: `version`, `status`, `entry_type`, `requires_target`, `enforcement` are not defined in SKILL_SCHEMA. Future schema validation may reject these. (SKILL.md:1-12)

2.2. [MEDIUM] (source: adversarial-quality) — **ALLOWED_COMMANDS duplication**: orchestrator.py and layer5_security.py define separate copies with inconsistent content. Changes may not propagate. (orchestrator.py:88-100; layer5_security.py:69-81)

2.3. [MEDIUM] (source: adversarial-critic) — **Layer 7 contract checks are aspirational**: SKILL.md lists 7 items L7 must verify; implementation tools (verify --tier=2, hook-audit, hook-inventory, recursive_failure_detector) verify none of them. (SKILL.md:264-272; layer7_operational.py:16-160)

2.4. [LOW] (source: adversarial-critic) — **Deduplication key uses title**: Different wording bypasses deduplication; optional location field means issues without location never deduplicate. (findings/models.py:75-81)

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-testing) — **L2→L4 hard dependency has empty tests**: `test_layer4_skipped_when_layer2_has_high_findings` and `test_layer4_runs_when_layer2_has_no_critical_findings` are both `pass` — no actual verification. (test_degradation.py:16-26)

3.2. [HIGH] (source: adversarial-testing) — **L0 dispatch has zero tests**: No tests exist for the 7-agent parallel dispatch that is the first layer executed. (N/A)

3.3. [HIGH] (source: adversarial-testing) — **`--halt-on` raw-count behavior untested**: Critical behavioral distinction (raw vs deduplicated counts) has no verification. (N/A)

3.4. [HIGH] (source: adversarial-testing) — **Phase/State Detection table untested**: Decision table mapping signals to layers has no implementation or test. (SKILL.md:79-88)

3.5. [HIGH] (source: adversarial-testing) — **`--fix-all` iterative loop untested**: WHILE loop with max-5-iteration guard and convergence criteria has no tests. (SKILL.md:32)

3.6. [MEDIUM] (source: adversarial-quality) — **Remove SKILL.md duplication**: Target Resolution section appears verbatim at lines 58-67 and 70-77. Consolidate to one authoritative section.

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-quality) — **L5 path traversal uses fragile regex**: Without AST grounding, regex-only detection produces false negatives on validated paths and false positives on unvalidated ones. (layer5_security.py:96-142)

4.2. [MEDIUM] (source: adversarial-testing) — **L3/L7 tests trivially shallow**: Only assert "returns a list" — complete implementation returning empty would pass. (test_layer3.py:16-18; test_layer7.py:16-23)

4.3. [LOW] (source: adversarial-quality) — **Layer 3 silently skips if external skills missing**: meta-review, harden, apply_safety_patterns not on PATH returns zero findings — no user notification. (layer3_structural.py:36-124)

### Concrete Recommendations

5.1. [HIGH] (source: adversarial-compliance) — **Align frontmatter with SKILL_SCHEMA**: Remove non-standard fields (`version`, `status`, `entry_type`, `requires_target`, `enforcement`) or document them as extensions.

5.2. [HIGH] (source: adversarial-quality) — **Fix L5/L6 subprocess.run calls**: Either invoke via Agent tool (if adversarial-* are valid agent names) or remove the subprocess.run attempt that always fails.

5.3. [HIGH] (source: adversarial-critic) — **Align health score formula in SKILL.md with findings/models.py**: Document the actual deduplication + evidence tier weighting formula, or fix the implementation to match the documented formula.

5.4. [HIGH] (source: adversarial-testing) — **Write actual tests for L2→L4 hard dependency**: Replace empty `pass` statements with assertions that verify L4 skips when L2 has failures.

5.5. [HIGH] (source: adversarial-critic) — **Implement or remove phase detection table**: The state-machine routing described has no implementation. Either implement state tracking or remove the table from SKILL.md.

5.6. [MEDIUM] (source: adversarial-quality) — **Remove SKILL.md duplication**: Merge lines 58-67 and 70-77 into single authoritative auto-detect section.

5.7. [MEDIUM] (source: adversarial-compliance) — **Add execution block**: Define `execution.directive`, `default_args`, `examples` per SKILL_SCHEMA.

### Open Questions / Unknowns

6.1. [LOW] (source: adversarial-critic) — **What is `enforcement: none` supposed to mean?** Field not defined in SKILL_SCHEMA. Clarify semantics or remove.

6.2. [LOW] (source: adversarial-quality) — **Are `adversarial-*` valid Agent subagent names?** If yes, the skill should use Agent tool to dispatch them. If no, remove all references.

6.3. [LOW] (source: adversarial-testing) — **Does --fix-all iterative loop work as designed?** No tests exist to verify the 5-iteration max and convergence criteria.