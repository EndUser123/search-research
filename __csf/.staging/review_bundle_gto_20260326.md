# Review Bundle: /gto Skill
**Generated**: 2026-03-26T19:10:00Z
**Scope**: P:/.claude/skills/gto/
**File Count**: ~50 files (excluding .evidence, .git)
**Execution Mode**: 4-agents (large skill)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: gto
- **Version**: 3.4.0
- **Category**: analysis
- **Enforcement**: strict
- **Trigger**: `/gto`, "gap analysis", "health check", "analyze project state"

### Domain & Purpose
Gap/Task/Opportunity analysis with self-verifying completion enforcement. Analyzes codebase to identify gaps, tasks, and opportunities across test coverage, documentation, code quality, dependency health, and project health metrics.

### Scale Metrics
- **Skill LOC**: ~500+ lines (SKILL.md)
- **Modules**: 15+ library modules
- **Hooks**: 5 hook files
- **Tests**: 20+ test files
- **Subagents**: 2 (gap_finder, health_calculator)

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Python
- **Key Integration**: gto_orchestrator.py CLI

---

## 2. ARCHITECTURE OVERVIEW

```
                    ┌──────────────────────────────────────────────────────┐
                    │                      /gto SKILL                        │
                    │  Gap/Task/Opportunity Analysis + Self-Verification  │
                    └──────────────────────────┬───────────────────────────┘
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         ▼                                     ▼                                     ▼
┌─────────────────┐               ┌─────────────────┐               ┌─────────────────┐
│ Layer 1        │               │ Layer 2         │               │ Layer 3        │
│ Detectors      │               │ AI Subagents   │               │ Self-Verification│
│ (tests, docs,  │               │ (gap_finder,   │               │ (viability_gate,│
│  deps, markers)│               │  health_calc)  │               │  checklist_gate)│
└────────┬────────┘               └────────┬────────┘               └────────┬────────┘
         │                                 │                                 │
         └─────────────────────────────────┴─────────────────────────────────┘
                                           │
                          ┌─────────────────┴─────────────────┐
                          │      gto_orchestrator.py         │
                          │  (CLI entry point)              │
                          └─────────────────┬───────────────┘
                                            │
                          ┌─────────────────┴─────────────────┐
                          │      Health Score + Gap List     │
                          │      JSON artifact output        │
                          └─────────────────────────────────┘
```

### Module Structure

| Module | Purpose |
|--------|---------|
| gto_orchestrator.py | Main CLI orchestrator |
| run_gto_monorepo.py | Monorepo variant |
| lib/state_manager.py | State management |
| lib/viability_gate.py | Viability verification |
| lib/skill_self_health_checker.py | Skill health checks |
| lib/test_presence_checker.py | Test coverage detection |
| lib/docs_presence_checker.py | Documentation checks |
| lib/dependency_checker.py | Dependency analysis |
| lib/code_marker_scanner.py | TODO/FIXME detection |
| lib/unfinished_business_detector.py | Unfinished work detection |
| lib/gap_skill_mapper.py | Gap-to-skill mapping |
| lib/skill_coverage_detector.py | Skill coverage analysis |
| lib/skill_registry_bridge.py | Registry integration |
| lib/entry_point_checker.py | Entry point validation |
| lib/results_builder.py | Results formatting |
| lib/next_steps_formatter.py | Next steps formatting |
| subagents/gap_finder_subagent.py | AI gap finding |
| subagents/health_calculator_subagent.py | Health calculation |

### Hooks

| Hook | Phase | Purpose |
|------|-------|---------|
| hooks/checklist_gate.py | PreToolUse | Checklist enforcement |
| hooks/gto_failure_capture.py | PostToolUse | Failure capture |
| hooks/session_summary.py | SessionEnd | Session summary |
| hooks/validate_format.py | Various | Format validation |
| hooks/gto_verify_wrapper.py | Various | Verification wrapper |

---

## 3. EXECUTION AND DATA FLOW

### CLI Usage
```bash
python P:/.claude/skills/gto/gto_orchestrator.py --project-root "P:\.claude\skills\gto" --format both
```

### Session Context Detection (Priority Order)
1. Recent file edits — session modified files in specific skill/package
2. Skill invocation target — explicit target of skill chain
3. Handoff/RESTORE_CONTEXT — from transcript_path or current_goal
4. Recent evidence files — premortem, adversarial review artifacts
5. Last resort: cwd

### Output Formats
- `--format json`: JSON artifact to `.evidence/gto-outputs/`
- `--format markdown`: Markdown to stdout
- `--format both`: Both JSON and markdown

---

## 4. COMPONENT INVENTORY

### Core

| File | Purpose |
|------|---------|
| SKILL.md | Main skill definition (v3.4.0) |
| gto_orchestrator.py | Main orchestrator CLI |
| run_gto_monorepo.py | Monorepo variant |

### Library Modules (15+)

| File | Purpose |
|------|---------|
| lib/state_manager.py | State management |
| lib/viability_gate.py | Viability gate |
| lib/skill_self_health_checker.py | Skill health |
| lib/test_presence_checker.py | Test detection |
| lib/docs_presence_checker.py | Docs detection |
| lib/dependency_checker.py | Dependency analysis |
| lib/code_marker_scanner.py | TODO/FIXME scan |
| lib/unfinished_business_detector.py | Unfinished work |
| lib/gap_skill_mapper.py | Gap mapping |
| lib/skill_coverage_detector.py | Coverage analysis |
| lib/skill_registry_bridge.py | Registry bridge |
| lib/entry_point_checker.py | Entry point check |
| lib/results_builder.py | Results format |
| lib/next_steps_formatter.py | Next steps format |
| lib/history_scanner.py | History analysis |
| lib/adjacent_file_scanner.py | Adjacent file scan |
| lib/git_context.py | Git context |

### Subagents

| File | Purpose |
|------|---------|
| subagents/gap_finder_subagent.py | AI gap finding |
| subagents/health_calculator_subagent.py | Health calculation |

### Hooks (5)

| File | Purpose |
|------|---------|
| hooks/checklist_gate.py | Checklist enforcement |
| hooks/gto_failure_capture.py | Failure capture |
| hooks/session_summary.py | Session summary |
| hooks/validate_format.py | Format validation |
| hooks/gto_verify_wrapper.py | Verification wrapper |

### Tests (20+)

| Directory | Files |
|-----------|-------|
| tests/ | test_orchestrator.py, test_lib.py, test_subagents.py, test_integration.py |
| tests/lib/ | test_*.py (15+ files) |
| tests/hooks/ | test_*.py (5 files) |
| tests/subagents/ | test_*.py (2 files) |
| tests/scripts/ | test_cleanup_state.py |
| evals/ | test_gto_assertions.py |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Self-verification** — Completion enforcement via viability gate
2. **Layered analysis** — Layer 1 detectors → Layer 2 AI → Layer 3 verification
3. **Evidence-based** — All findings backed by concrete evidence
4. **Health scoring** — Quantitative project health metrics

### Things That Must NOT Change
- **Viability gate** — Self-verification depends on it
- **State manager** — Gap tracking depends on state format
- **Output artifact format** — Downstream tools depend on JSON schema

---

## 6. KNOWN ISSUES

No critical issues documented. Active development with comprehensive test suite.

---

## 7. INTEGRATION POINTS

### With Other Skills
- `/critique` — Gap analysis after critique
- `/pre-mortem` — Pre-mortem integration
- `/debugRCA` — RCA integration
- Skill registry — Gap-to-skill mapping

### Evidence Output
- `.evidence/gto-outputs/gto-artifact-{timestamp}.json`
- `.evidence/gto-outputs/gto-report-{timestamp}.md`

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | EXCELLENT | 20+ test files |
| Error Handling | GOOD | Graceful degradation |
| Documentation | GOOD | 500+ line SKILL.md |
| Hook Integration | GOOD | 5 hooks registered |
| Parallel Safety | GOOD | Independent subagents |

### SQA Relevance
- **HIGH** — This IS an SQA skill (Gap/Task/Opportunity Analysis)
- Identifies missing test coverage
- Detects documentation gaps
- Code quality issue detection
- Self-verifying completion enforcement
