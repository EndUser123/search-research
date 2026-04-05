# Review Bundle: debugRCA

**Generated**: 2026-03-25
**Scope**: `P:/packages/debugRCA/` (entire package)
**File Count**: 59 Python source files + SKILL.md + examples
**Execution Mode**: 4-agent parallel (large scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Package**: debugRCA v2.5.0/v2.11.0 (dual versioning — `__init__.py` exports v2.5.0; SKILL.md declares v2.11.0)
- **Location**: `P:/packages/debugRCA/`
- **Owner**: Solo developer workflow system
- **Criticality**: Core debugging/repair workflow for Claude Code sessions

### Domain & Purpose
AI-assisted Root Cause Analysis system for debugging. Implements evidence saturation detection, multi-methodology RCA (Fishbone/Fault Tree/Causal Loop), hypothesis generation/scoring, phase state persistence, and action tracing. Used when errors, crashes, or performance issues occur during development. Enforced via Stop hook — sessions cannot complete `/rca` invocations without executing the RCA engine.

### Scale Metrics
- 59 Python source files across `src/`, `skill/`, and `tests/` directories
- 8 major subsystems: RCA engine, hypothesis management, evidence tiering, pattern registry, cognitive modes, integrations, skill hooks, and metrics
- Packages: `debugRCA` (pip-installable via pyproject.toml), `debugRCA.skill` (hooks), `debugRCA.examples`
- Change frequency: Active development — 10+ open tasks in tracker

### Your Environment
- **OS**: Windows 11 Pro (bash shell, Unix paths like `P:/`)
- **Python**: 3.10+ (debugRCA src), 3.11+ (hooks)
- **Package manager**: `pip install -e packages/debugRCA`
- **Key integrations**: CKS (Compact Knowledge Store), CHS (Chat History Search), HDMA, CDS, UnifiedSearchRouter, DaemonClient, SQLite

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              debugRCA Package                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Input (error/crash/behavioral issue)                                   │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────┐                                │
│  │         SimpleRCAEngine                  │  ← Main RCA orchestrator      │
│  │  (Fishbone + FaultTree + CausalLoop)   │    (simple_rca_engine.py)     │
│  │  + Meta-RAG search + Change Intel       │                                │
│  └──────────────┬──────────────────────────┘                                │
│                 │                                                           │
│       ┌─────────┴─────────────────────────────────────────┐                │
│       │                                                       │             │
│       ▼                                                       ▼             │
│  ┌─────────────────┐                            ┌──────────────────┐     │
│  │ ContextAnalyzer  │                            │  CognitiveMode   │     │
│  │ (problem type,  │                            │  Selector        │     │
│  │  complexity,     │                            │  (thinking mode  │     │
│  │  scope)          │                            │   recommendation)│     │
│  └────────┬────────┘                            └────────┬─────────┘     │
│           │                                                 │              │
│           ▼                                                 ▼              │
│  ┌─────────────────┐                            ┌──────────────────┐        │
│  │  ToolSelector   │                            │  EvidenceSat    │        │
│  │ (tool strategy: │                            │  Detector        │        │
│  │  systematic/     │                            │  (saturation     │        │
│  │  deep_scan/      │                            │   threshold)     │        │
│  │  exploratory/    │                            └────────┬─────────┘        │
│  │  council)        │                                     │                │
│  └────────┬────────┘                                     │                │
│           │                                               │                │
│           ▼                                               ▼                │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    PerformanceOptimizer                           │      │
│  │           (LRU cache, parallel execution, tool pruning)          │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│  ─── Supporting Infrastructure ───                                         │
│                                                                            │
│  hypothesis_generator ──► hypothesis_scorer ──► converge_validator       │
│       │                            │                    │                    │
│       │                            ▼                    │                    │
│       │                    confidence_tracker            │                    │
│       │                    + evidence_tier (ceiling)     │                    │
│       │                                                       │                │
│  pattern_registry ──► error_signature ──► fix_registry              │
│  (CKS-backed)                                                      │
│                                                                            │
│  ─── RCA Skill Hooks (registered in settings.json) ───                  │
│                                                                            │
│  PostToolUse_rca_phase_tracker ──► tracks phase progress                │
│  PostToolUse_rca_action_tracker ──► records action graph               │
│  PostToolUse_rca_search_validator ──► validates search-before-diagnose │
│  PostToolUse_rca_init ──► session initialization                       │
│  PostToolUse_rca_research_storage ──► stores auto-research results    │
│  SessionEnd_rca_cleanup ──► cleanup on session end                      │
│  StopHook_rca_enforcement ──► BLOCKED until RCA workflow complete      │
│                                                                            │
│  ─── State / Persistence ───                                             │
│                                                                            │
│  SQLite: metrics_tracker (fix success rates, recurrence)                   │
│          outcome_recorder (fix outcome tracking)                           │
│          taskmaster DB (deprecated, ~20 files)                            │
│  CKS: phase_state_manager (resumable RCA sessions)                       │
│  JSON: rca_workflow.json, active_session.json                            │
│  Files: P:/.claude/state/rca/                                            │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. EXECUTION AND DATA FLOW

### `/debugRCA` Invocation Flow

```
User types /debugRCA [issue]
       │
       ▼
SessionStart: /debugRCA skill loaded (SKILL.md)
       │
       ▼
session_preflight.classify_problem_type() ──► ProblemType enum
       │
       ▼
cognitive_mode_selector ──► Thinking modes (five_whys, first_principles, etc.)
       │
       ▼
SimpleRCAEngine.analyze_issue()
       │
       ├─► Fishbone (6M analysis)
       ├─► Fault Tree (top-down decomposition)
       ├─► Causal Loop (feedback loop identification)
       ├─► MetaRAG search (HDMA, CDS, CKS, CHS, Grep)
       └─► Git Change Intelligence (recent changes)
       │
       ▼
hypothesis_generator ──► HypothesisSet (12 categories)
       │
       ▼
hypothesis_scorer ──► Bayesian scoring + evidence tiers
       │
       ▼
evidence_saturation.check_saturation() ──► if saturated, proceed to fix
       │
       ▼
converge_validator.validate() ──► score > 0.7 + 100% tests pass
       │
       ▼
fix_registry / pattern_registry ──► apply known fix OR register new fix
       │
       ▼
outcome_recorder.record_outcome() + metrics_tracker ──► close the loop
```

### State Management

| State File | Location | Purpose | TTL |
|-----------|----------|---------|-----|
| `rca_workflow.json` | `P:/.claude/state/rca/` | Phase tracking, execution/delegation status | 10 min stale threshold |
| `active_session.json` | `P:/.claude/state/rca/` | Preflight session state | 8 hours |
| `metrics.db` | `~/.speckit/taskmaster/tasks.db` | Fix success rates, recurrence | Permanent |
| `outcome.db` | Package-local SQLite | Fix outcome RESOLVED/FAILED/PARTIAL/UNKNOWN | Permanent |
| `pattern_registry.json` | `P:/__csf/.data/rca/` | Pattern-level fix registry | Permanent |

### Error Handling
- **Fail-open**: Most CKS/CSF integrations use lazy imports with graceful fallback (logged warning, continue without feature)
- **Fail-closed**: StopHook_rca_enforcement hard-blocks session completion if RCA workflow incomplete
- **No crash**: External exceptions in hooks are caught and logged; RCA engine never crashes the parent session

---

## 4. COMPONENT INVENTORY

### Core RCA Engine

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/simple_rca_engine.py` | Multi-methodology RCA orchestrator | `SimpleRCAEngine.analyze_issue()`, `search_architectural_context()`, `flush_pending_patterns()` |
| `src/debug_rca/cli.py` | CLI entry point (`debug-rca` command) | 7 subcommands: record, analyze, hypothesis, search, doctor, evidence, arch |
| `src/debug_rca/session.py` | Preflight utilities (shared by /debug and /rca) | `classify_problem_type()`, `detect_error_type()`, `search_cks_history()`, `manage_active_session()` |
| `src/debug_rca/config.py` | Environment/settings access | `get_local_only_mode()`, `get_saturation_threshold()`, `LocalFallbackMode` context manager |

### Hypothesis Management

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/hypothesis_generator.py` | Generate hypotheses from error type | `generate_hypotheses()`, `HypothesisCategory` enum (12 categories) |
| `src/debug_rca/hypothesis_scorer.py` | Bayesian scoring with evidence tiers | `HypothesisScorer.add_hypothesis()`, `rank()`, `is_verification_ready()` |
| `src/debug_rca/confidence_tracker.py` | Bayesian prior/posterior updates | `ConfidenceTracker.update()` — Bayes' rule: `P(H|E) = (LR*P(H))/(LR*P(H)+P(~H))` |
| `src/debug_rca/converge_validator.py` | Validate solution convergence | `ConvergeValidator.validate()` — requires score > 0.7 AND 100% tests pass |

### Evidence & Pattern System

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/evidence_tier.py` | 5-tier evidence classification with confidence ceilings | `EvidenceTier`, `classify_evidence()` |
| `src/debug_rca/evidence_saturation.py` | Detect when sufficient evidence gathered | `EvidenceSaturationDetector.check_saturation()`, `detect_diminishing_returns()` |
| `src/debug_rca/error_signature.py` | Pattern-level error signatures (location-agnostic) | `ErrorSignature`, `extract_signature()`, `match_to_pattern()` |
| `src/debug_rca/stack_trace_fingerprint.py` | Location-specific error fingerprints | `StackTraceFingerprint`, `fingerprint_from_error()` |
| `src/debug_rca/pattern_registry.py` | CKS-backed pattern fix registry (JSON persistence) | `PatternRegistry.add_pattern_fix()`, `find_match()`, `get_stats()` |
| `src/debug_rca/fix_registry.py` | Location-specific fix registry | Similar API to pattern_registry |

### Intelligence Layer (Phase 2 enhancements)

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/core/context_analyzer.py` | Problem classification (type, complexity, scope) | `ContextAnalyzer.analyze_context()` |
| `src/debug_rca/core/tool_selector.py` | Optimal tool strategy selection | `ToolSelector.select_optimal_tools()` — strategies: systematic/deep_scan/exploratory/council |
| `src/debug_rca/core/performance_optimizer.py` | LRU cache + parallel execution planning | `PerformanceOptimizer.optimize_execution()` |
| `src/debug_rca/core/rca_enhancer.py` | Orchestrates Phase 2 components | `EnhancedRCACommand.execute_rca()` — fallback to legacy mode |

### Cognitive & Reasoning

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/cognitive_mode_selector.py` | Thinking mode recommendation | `CognitiveModeSelector.classify_problem()` |
| `src/debug_rca/cognitive_meta_agent.py` | **DEPRECATED** — facade for `features.uaf` | All functions deprecated wrappers |
| `src/debug_rca/auto_research.py` | Auto-research trigger for external libraries | `should_trigger_research()`, `build_research_query()` — 42 fast-moving libraries tracked |

### Action Tracing & Metrics

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/action_tracer.py` | Directed graph of investigation actions | `ActionTracer.record_action()`, `find_divergence_point()` |
| `src/debug_rca/metrics_tracker.py` | Aggregate metrics (fix success, recurrence, CHS usage) | `RCAMetricsTracker.record_fix_attempt()`, `get_metrics()` |
| `src/debug_rca/outcome_recorder.py` | Per-fix outcome tracking | `OutcomeRecorder.record_outcome()`, `get_summary()` |
| `src/debug_rca/phase_state_manager.py` | CKS-backed resumable phase persistence | `PhaseStateManager.save()`, `restore()`, `get_resume_point()` |

### Integrations

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/integration/explore_integration.py` | /explore command enhancement | `ExploreIntegration.enhance_tool_selection()` |
| `src/debug_rca/integration/rca_specialist_integration.py` | Error signature ↔ CKS bridge | `RCASpecialistSignatureBridge.analyze()`, `register_fix()` |
| `src/debug_rca/integration/cks_pattern_integration.py` | CKS-backed pattern registry (replaces JSON) | `CKSPatternRegistry.lookup()`, `lookup_semantic()` |
| `src/debug_rca/integration/taskmaster_integration.py` | **DEPRECATED** — SQLite storage superseded by CKS | N/A |
| `src/debug_rca/integration/cks_pattern_integration.py` | CKS-backed pattern fix storage | `register_fix()`, `lookup()`, `lookup_semantic()` |

### RCA Skill Hooks

| File | Event | Purpose |
|------|-------|---------|
| `skill/hooks/PostToolUse_rca_phase_tracker.py` | PostToolUse | Tracks RCA phases (-1 history → 6 escalation) via tool usage patterns |
| `skill/hooks/PostToolUse_rca_action_tracker.py` | PostToolUse | Records action graph (divergence detection) |
| `skill/hooks/PostToolUse_rca_search_validator.py` | PostToolUse | Validates search-before-diagnose protocol |
| `skill/hooks/PostToolUse_rca_init.py` | PostToolUse | Session initialization |
| `skill/hooks/PostToolUse_rca_research_storage.py` | PostToolUse | Stores auto-research results |
| `skill/hooks/SessionEnd_rca_cleanup.py` | SessionEnd | Cleanup on session end |
| `skill/hooks/StopHook_rca_enforcement.py` | Stop | **BLOCKS** session until RCA workflow complete |

### Utilities

| File | Purpose | Key APIs |
|------|---------|---------|
| `src/debug_rca/hook_launcher.py` | Hook execution + diagnostics | `python -m debug_rca.hook_launcher <hook> [--doctor]` |
| `src/debug_rca/run_hook.py` | Compatibility shim | `python -m debug_rca.run_hook <hook>` |
| `src/debug_rca/temporal_check.py` | Deprecation API validation | `TemporalCheck.check()` — VALID/REJECTED/UNKNOWN |
| `src/debug_rca/quality_estimator.py` | Tool coverage estimation | `QualityEstimator.calculate_coverage()` — 0.0-1.0 |
| `src/debug_rca/fault_localization.py` | SBFL algorithms (Ochiai, Tarantula, DStar) | `rank_suspicious_locations()` |
| `src/debug_rca/golden_set_runner.py` | Temporal check regression tests | `GoldenSetRunner.run_all()` |
| `src/debug_rca/research_with_cache.py` | Library docs caching for auto-research | `research_library_docs()` |
| `src/debug_rca/library_docs_cache.py` | Library documentation cache | `get_library_cache()` |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Evidence tier confidence ceilings** — No hypothesis can exceed the ceiling of its lowest-tier evidence
2. **Write-behind caching** — Pattern writes batched (PERF-001) to avoid per-analysis I/O
3. **Local-first fallback** — `DEBUGRCA_LOCAL_ONLY=true` enables fully offline operation
4. **Graceful degradation** — Optional CKS/CSF integrations fail open with warnings, never crash
5. **Stop-hook enforcement** — Sessions cannot complete `/rca` invocations without running the engine

### Technology Constraints
- **Python 3.10+** for core package, **3.11+** for hooks
- **No external LLM calls in hooks** — hooks are synchronous, fast, no network
- **SQLite for local persistence** — metrics, outcomes, pattern registry
- **CKS for cross-session knowledge** — phase state, pattern fixes
- **Thread-safe singletons** — `PatternRegistry`, `RCAMetricsTracker` use locks

### Performance SLAs
- Hook execution: <5 seconds per hook
- Evidence saturation check: <100ms (with CKS semantic fallback to Jaccard)
- Phase state save/restore: <500ms
- Pattern registry lookup: <50ms (JSON file)

### Things That Must NOT Change
1. **StopHook_rca_enforcement blocking** — RCA workflow enforcement must remain hard-block
2. **Evidence tier ceilings** — Tier 4 (speculation) ceiling of 0.5 is the floor for all hypotheses
3. **Phase ordering** — Gather → Isolate → Hypothesize → Test → Fix is the canonical flow
4. **Error signature hash stability** — Changing hash algorithm breaks pattern registry lookups
5. **Hook CLI invocation model** — `python -m debug_rca.hook_launcher <hook>` is the contract

---

## 6. KNOWN ISSUES

### OPEN — Task #2402: debugRCA skill not canonical commitment format
- **Issue**: SKILL.md not yet updated to canonical EVL commitment format
- **Impact**: Commitment tracking incomplete for RCA sessions
- **Workaround**: None — in progress

### OPEN — Task #2404: StopHook_rca_contract lacks structure validation
- **Issue**: RCA contract gate doesn't validate structure of root cause statements
- **Impact**: Hand-wavy root causes may pass the gate
- **Workaround**: Manual review required

### OPEN — Task #2405: evidence_store needs commitment/binding tables
- **Issue**: evidence_store.py not extended with commitment and binding table schema
- **Impact**: Binding validation incomplete for RCA claims
- **Workaround**: None

### OPEN — Task #2341: GTO viability gate performance
- **Issue**: GTO viability gate has performance and validation issues
- **Impact**: False negatives/positives in viability assessment
- **Workaround**: Manual override available

### OPEN — Task #2414: No self_documentation_check() validator in __lib/
- **Issue**: Missing validator for skill self-documentation
- **Impact**: Documentation rot unchecked
- **Workaround**: Manual review

### OPEN — debugRCA skill NOT in SKILL_EXECUTION_REGISTRY
- **Issue**: `debugRCA.skill` not registered in `SKILL_EXECUTION_REGISTRY` (found during investigation)
- **Impact**: Skill enforcement bypass possible
- **Workaround**: Register in `skill_enforcer.py` HOOK_PRIORITY dict

### DEPRECATED — taskmaster_integration.py
- **Issue**: Superseded by `cks_pattern_integration.py`
- **Impact**: Dead code in codebase
- **Workaround**: Can be deleted after migration verified

### DEPRECATED — cognitive_meta_agent.py
- **Issue**: Thin facade to `features.uaf`, all functions deprecated wrappers
- **Impact**: Confusing to maintainers
- **Workaround**: All RCA cognitive decomposition now uses `features.uaf` directly

### KNOWN — SEC-001 path traversal in verify_evidence_freshness
- **File**: `P:/packages/debugRCA/src/debug_rca/integration/`
- **Issue**: Path traversal vulnerability (was fixed in #2318)
- **Status**: FIXED

### KNOWN — SEC-002 ReDoS in meta regex patterns
- **File**: `P:/packages/debugRCA/src/debug_rca/integration/`
- **Issue**: ReDoS vulnerability in meta regex (was fixed in #2319)
- **Status**: FIXED

---

## 7. INTEGRATION POINTS

### Where to plug in new RCA methodologies
- Add to `simple_rca_engine.py` `_execute_<methodology>()` pattern
- Implement `_synthesize_analysis()` to combine with existing results
- Add result dataclass for the new methodology

### Where to add new evidence tiers
- Edit `evidence_tier.py` — `EvidenceTier` enum and `get_confidence_ceiling()` mapping
- Update `hypothesis_scorer.py` if scoring formula changes

### Where to add new problem types
- Edit `cognitive_mode_selector.py` — `_determine_problem_type()` keyword map
- Add to `ProblemType` enum in `session.py` and `cognitive_mode_selector.py`
- Add `ISSUE_TYPE_WEIGHTS` entry in `quality_estimator.py`

### Where to register new pattern backends
- Edit `rca_specialist_integration.py` — `SignatureAnalysisResult` fields
- Edit `CKSPatternRegistry` in `cks_pattern_integration.py`

### Hook invocation contract
```bash
python -m debug_rca.hook_launcher <hook_name> [args]
python -m debug_rca.run_hook <hook_name> [args]  # compatibility shim
```

### Environment variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `DEBUGRCA_LOCAL_ONLY` | `false` | Enable offline-only mode |
| `DEBUGRCA_SATURATION_DISABLED` | `false` | Disable saturation detection |
| `DEBUGRCA_STATE_DIR` | `P:/.claude/state/debugrca/` | State directory |
| `DEBUG_RCA_HOOK_ROOT` | (auto-detect) | Override hook location |
| `DEBUG_RCA_CSF_SRC` | `P:/__csf/src` | CSF monorepo location |

---

## 8. APPENDIX: SKILL.md REGISTRATION

debugRCA is invoked via `/debugRCA` (aliases: `/r`, `/verify`, `/fix`). The SKILL.md registers these hooks in `settings.json`:

```json
"PostToolUse": [
  { "matcher": ".*", "hooks": [
    { "command": "python -m debug_rca.hook_launcher PostToolUse_rca_init" },
    { "command": "python -m debug_rca.hook_launcher PostToolUse_rca_phase_tracker" },
    { "command": "python -m debug_rca.hook_launcher PostToolUse_rca_action_tracker" },
    { "command": "python -m debug_rca.hook_launcher PostToolUse_rca_search_validator" },
    { "command": "python -m debug_rca.hook_launcher PostToolUse_rca_research_storage" }
  ]}
],
"SessionEnd": [
  { "matcher": ".*", "hooks": [
    { "command": "python -m debug_rca.hook_launcher SessionEnd_rca_cleanup" }
  ]}
],
"Stop": [
  { "matcher": ".*", "hooks": [
    { "command": "python -m debug_rca.hook_launcher StopHook_rca_enforcement" }
  ]}
]
```

### Evidence Tiers (confidence ceilings)

| Tier | Source | Ceiling |
|------|--------|---------|
| Tier 0 | Direct observation | 1.0 |
| Tier 1 | Verified by agent execution (passing test, successful Bash) | 0.9 |
| Tier 2 | Tool output (Grep, Read, Bash with result) | 0.7 |
| Tier 3 | CKS/CHS search result | 0.6 |
| Tier 4 | Speculation/assumption | 0.5 |
| Tier 5 | Failing test (pre-fix) | TBD |

---

## 9. FILE MANIFEST

### src/debug_rca/ (46 files)
```
__init__.py              — Package facade, re-exports 21 public classes
cli.py                   — CLI entry point (debug-rca command)
session.py               — Preflight utilities
config.py                — Environment/settings
simple_rca_engine.py     — Core RCA orchestrator (Fishbone/FaultTree/CausalLoop)
auto_research.py         — Auto-research trigger
cognitive_meta_agent.py   — DEPRECATED facade to features.uaf
cognitive_mode_selector.py — Thinking mode recommendation
confidence_tracker.py     — Bayesian hypothesis tracking
converge_validator.py    — Convergence criteria validation
action_tracer.py         — Action graph tracing
metrics_tracker.py       — Aggregate metrics
outcome_recorder.py      — Per-fix outcome tracking
phase_state_manager.py    — CKS-backed resumable sessions
hypothesis_generator.py  — Hypothesis generation
hypothesis_scorer.py    — Bayesian hypothesis scoring
evidence_tier.py         — Evidence classification
evidence_saturation.py   — Saturation detection
error_signature.py       — Pattern-level signatures
stack_trace_fingerprint.py — Location-level fingerprints
fix_registry.py          — Location-specific fix registry
pattern_registry.py      — Pattern-level fix registry (JSON)
fault_localization.py    — SBFL algorithms
temporal_check.py        — Deprecation API validation
quality_estimator.py     — Tool coverage estimation
flow_visualizer.py       — Investigation flow visualization
walkthrough_generator.py — Step-by-step fix walkthrough
tool_checker.py         — Tool availability checking
golden_set_runner.py     — Temporal check regression tests
library_docs_cache.py   — Library documentation cache
research_with_cache.py  — Cached auto-research
debugpy_client.py        — DebugPy integration
log_discovery.py         — Log discovery engine
evidence_saturation.py   — Already listed
hypothesis_generator.py  — Already listed
hypothesis_scorer.py     — Already listed
core/context_analyzer.py — Problem classification
core/tool_selector.py   — Tool strategy selection
core/performance_optimizer.py — Cache + parallelization
core/rca_enhancer.py    — Phase 2 orchestrator
core/__init__.py
integration/explore_integration.py
integration/rca_specialist_integration.py
integration/taskmaster_integration.py — DEPRECATED
integration/cks_pattern_integration.py
integration/cks_pattern_integration.py
cks_auto_extractor.py
```

### skill/hooks/ (8 files)
```
SKILL.md
hooks/PostToolUse_rca_phase_tracker.py
hooks/PostToolUse_rca_action_tracker.py
hooks/PostToolUse_rca_search_validator.py
hooks/PostToolUse_rca_init.py
hooks/PostToolUse_rca_research_storage.py
hooks/SessionEnd_rca_cleanup.py
hooks/StopHook_rca_enforcement.py
hooks/hook_error_rca.py
hooks/hook_path_utils.py
hooks/pattern_extractor.py
hooks/cks_integration.py
scripts/session_preflight.py
tests/conftest.py + 8 test files
```

### tests/ (39 files)
```
test_cli.py, test_session.py, test_config.py
test_hypothesis_generator.py, test_hypothesis_scorer.py
test_evidence_saturation.py, test_evidence_tier.py
test_fault_localization.py, test_fix_registry.py
test_pattern_registry.py, test_confidence_tracker.py
test_converge_validator.py, test_outcome_recorder.py
test_metrics_tracker.py (+ session_budget, verification_gate variants)
test_phase_state_manager.py, test_auto_research.py
test_cognitive_mode_selector.py
test_full_integration.py, test_integration_e2e.py
test_golden_set_runner.py
test_flow_visualizer.py
test_error_signature.py
test_core_performance_optimizer.py
test_performance_perf001.py, test_performance_perf003.py
test_sec001_hook_path_validation.py
test_sec002_metrics_input_validation.py
test_cks_auto_extractor.py
```

### examples/ (3 files)
```
basic_usage.py, advanced_config.py, real_world.py
```
