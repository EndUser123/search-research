## Triage Classification
skill — GTO Correctness Subagents rewrite: SKILL.md Agent tool dispatch workflow, orchestrator correctness infrastructure removal, new merge_agent_results.py script

## Dispatched Specialists
- adversarial-critic: meta-critique, consensus, blind spots across specialist panel
- adversarial-compliance: schema conformance, hook registration, test import paths
- adversarial-quality: tech debt, maintainability, skill structure
- adversarial-logic: off-by-one, wrong operators, conditionals, merge logic

## Specialist Findings Summary

### adversarial-critic
**Domain:** Meta-critique, consensus, blind spots
**Key findings:**
- No significant issues found in meta-critique domain.

### adversarial-compliance
**Domain:** Schema conformance, API contracts, specs
**Key findings:**
- [HIGH] SKILL.md Agent tool dispatch for gto-logic/gto-quality/gto-code-critic subagents not implemented in gto_orchestrator.py (SKILL.md:134, gto_orchestrator.py:453)
- [HIGH] Test file has incorrect sys.path manipulation causing import failures — tests fail at collection (test_gto_orchestrator.py:8)
- [MEDIUM] test_default_values assertion incorrect — enable_subagents default is False not True (test_gto_orchestrator.py:27 vs gto_orchestrator.py:168)
- [MEDIUM] SKILL.md references _run_correctness_subagents() but grep finds no matches — documentation doesn't match implementation state (SKILL.md vs gto_orchestrator.py:453)

### adversarial-quality
**Domain:** Tech debt, maintainability, structure
**Key findings:**
- [HIGH] SKILL.md dispatches non-existent correctness subagents (gto-logic, gto-quality, gto-code-critic) — subagents/ directory only contains gap_finder_subagent.py and health_calculator_subagent.py (SKILL.md:134)
- [MEDIUM] merge_agent_results.py is orphaned from execution flow — gto_orchestrator.py never calls it; GapFinderSubagent used instead (SKILL.md:179, gto_orchestrator.py:453)
- [MEDIUM] Test expects enable_subagents=True but default is False (test_gto_orchestrator.py:27, gto_orchestrator.py:168)
- [LOW] merge_agent_results.py has hardcoded validation fields misaligned with Gap dataclass (merge_agent_results.py:10, results_builder.py:88)
- [LOW] gap_finder_subagent.py uses MD5 hash-based gap IDs inconsistent with signature-based deduplication (gap_finder_subagent.py:36)

### adversarial-logic
**Domain:** Pure logic errors, merge logic, polling loop
**Key findings:**
- [HIGH] merge_agent_results.py split-index parsing is fragile — silent continue on malformed filenames loses agent results (merge_agent_results.py:81-84)
- [HIGH] Polling loop exits on file existence without verifying agent exit codes — crashed agent with non-zero exit goes undetected (SKILL.md:148-165)
- [MEDIUM] merge_gaps() discards description and evidence fields from agent findings — rich diagnostic info lost (merge_agent_results.py:44-53)
- [MEDIUM] merge_gaps() has no deduplication logic — duplicate gap IDs possible in merged output (merge_agent_results.py)
- [MEDIUM] VALID_SEVERITIES = {HIGH, MEDIUM, LOW} but GTO uses {critical, high, medium, low} — agents cannot express CRITICAL severity (merge_agent_results.py:30-32)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance) — SKILL.md dispatches Agent tool for gto-logic/gto-quality/gto-code-critic subagents but these subagent types do not exist anywhere in the codebase. The registered subagents at P:/.claude/agents/ are adversarial-* variants, not gto-* variants. (SKILL.md:134-138, gto_orchestrator.py:453)
1.2. [HIGH] (source: adversarial-logic) — Polling loop breaks on file existence without calling wait() on agent PIDs to verify success — a crashed agent writes its output file then segfaults and the overall operation reports success. (SKILL.md:148-165)
1.3. [MEDIUM] (source: adversarial-compliance) — _run_correctness_subagents() referenced in work.md but grep finds no matches in codebase — never existed or fully removed without SKILL.md update. (gto_orchestrator.py:453)
1.4. [MEDIUM] (source: adversarial-quality) — merge_agent_results.py is never invoked by gto_orchestrator.py; the orchestrator only calls GapFinderSubagent and saves JSON directly. (gto_orchestrator.py:453, SKILL.md:179)

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-logic) — merge_agent_results.py silently skips files whose names don't match gto-correctness-{type}-{terminal_id}.json pattern. Agent results can be lost with no warning. (merge_agent_results.py:81-84)
2.2. [MEDIUM] (source: adversarial-quality) — merge_agent_results.py REQUIRED_FIELDS = {id, severity, location, title} but Gap dataclass uses {gap_id, severity, file_path, line_number, message}. Field names don't align. (merge_agent_results.py:10, results_builder.py:88-107)
2.3. [LOW] (source: adversarial-quality) — gap_finder_subagent.py generates gap_id via MD5 hash of concatenated string. Same gap gets different IDs across runs if file content order changes, breaking signature-based deduplication. (gap_finder_subagent.py:36-37)
2.4. [MEDIUM] (source: adversarial-logic) — Severity vocabulary mismatch: agents use {HIGH/MEDIUM/LOW}, GTO uses {critical/high/medium/low}. Agents cannot express CRITICAL severity. Findings with severity=critical are silently dropped. (merge_agent_results.py:30-32)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-compliance) — Fix sys.path in test_gto_orchestrator.py: current path resolves to P:\.claude but module is at P:\.claude\skills\gto\. Tests fail at collection. (test_gto_orchestrator.py:8)
3.2. [MEDIUM] (source: adversarial-compliance, adversarial-quality) — Fix test assertion: config.enable_subagents is True vs actual default False. Two separate specialists flagged this. (test_gto_orchestrator.py:27, gto_orchestrator.py:168)
3.3. [MEDIUM] (source: adversarial-logic) — Add deduplication in merge_gaps() by gap ID to prevent duplicate IDs in consolidated output. (merge_agent_results.py)
3.4. [MEDIUM] (source: adversarial-logic) — Preserve all fields from agent findings in merge_gaps() — spread finding dict instead of selective field extraction to keep evidence and description. (merge_agent_results.py:44-53)

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-logic) — Agent results silently lost when filename stem has unexpected part count during split-index extraction. No warning printed to user. (merge_agent_results.py:85)
4.2. [MEDIUM] (source: adversarial-logic) — validate_finding() treats severity mismatch as warning only (logs to stderr) and returns False — the finding is dropped silently. Most critical findings never reach GTO output. (merge_agent_results.py:30-32)
4.3. [LOW] (source: adversarial-quality) — merge_agent_results.py orphaned from actual execution flow means SKILL.md step 5 (merge) would fail if enable_subagents=True path were ever wired. (SKILL.md:176-188)

### Concrete Recommendations
5.1. [HIGH] (source: adversarial-compliance, adversarialquality) — Update SKILL.md Step 3 to dispatch correct subagent types: use adversarial-logic, adversarial-quality, adversarial-critic (or gap_finder) instead of non-existent gto-logic/gto-quality/gto-code-critic. Registered subagents at P:/.claude/agents/ are adversarial-* variants.
5.2. [HIGH] (source: adversarial-compliance) — Fix test import path: sys.path.insert(0, str(Path(__file__).parent.parent.parent)) then from skills.gto.gto_orchestrator import ... (test_gto_orchestrator.py:8)
5.3. [HIGH] (source: adversarial-logic) — After breaking on all-files-present in polling loop, add final wait loop to verify all agent PIDs exited with code 0. (SKILL.md:148-165)
5.4. [MEDIUM] (source: adversarial-quality) — Either remove merge_agent_results.py from SKILL.md step 5 (if not used) or wire it into gto_orchestrator.py workflow. Currently orphaned.
5.5. [MEDIUM] (source: adversarial-compliance) — Fix test assertion: assert config.enable_subagents is False to match actual default. (test_gto_orchestrator.py:27)
5.6. [MEDIUM] (source: adversarial-logic) — Replace bare continue with warning print or regex validation for filename pattern matching in merge_agent_results.py. (merge_agent_results.py:85)
5.7. [MEDIUM] (source: adversarial-logic) — Expand VALID_SEVERITIES in merge_agent_results.py to include critical/high/medium/low or map agent severities to GTO vocabulary before validation. (merge_agent_results.py:30-32)
5.8. [MEDIUM] (source: adversarial-logic) — Add deduplication by ID in merge_gaps(), preferring agent findings over L1 when IDs collide. Log a warning when deduplication occurs. (merge_agent_results.py)
5.9. [MEDIUM] (source: adversarial-logic) — Change gap dict construction in merge_gaps() from selective field extraction to {**finding, 'source': source} to preserve all fields. (merge_agent_results.py:44-53)
5.10. [LOW] (source: adversarial-quality) — Align Gap field names in merge_agent_results.py REQUIRED_FIELDS with Gap dataclass fields: gap_id, severity, file_path, line_number, message. (merge_agent_results.py:10, results_builder.py:88)

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-logic) — Was _run_correctness_subagents() ever actually in gto_orchestrator.py, or was the work.md description inaccurate? Need historical git check.
6.2. [LOW] (source: adversarial-quality) — Is merge_agent_results.py a net-new file or a replacement for an older merge script? If replacement, what happened to the old file?
6.3. [LOW] (source: adversarial-logic) — AGENT_PIDS array is set via Agent tool dispatch with & and PIDS=($!). If agents run synchronously or if shell doesn't support $! for Agent tool, PIDs array would be empty. Does Agent tool dispatch actually populate AGENT_PIDS?
