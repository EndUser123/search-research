# Review Bundle: debugRCA

**Generated**: 2025-02-17
**Scope**: P:/packages/debugRCA
**File Count**: 80+ Python files, 24 test files
**Test Coverage**: 849 tests
**Execution Mode**: 4-agent hybrid (comprehensive scan)

---

## 1. PROJECT CONTEXT

### Domain & Purpose
debugRCA is an AI-assisted Root Cause Analysis toolkit for Claude Code. It provides hypothesis-driven debugging with Evidence Tiering (confidence ceilings), Flow-of-Action tracing, and Phase State Management. The library integrates with CSF NIP's unified search system (CDS, Grep, CHS, CKS, HDMA) for architectural context and knowledge retrieval.

### Scale Metrics
- **LOC**: ~15,000+ lines of Python code
- **Major subsystems**: 8 (Evidence Tiering, Flow Tracing, Meta-RAG, Metrics, Session, Cognitive, Integration, Core)
- **Deployment**: pip package + Claude Code skill
- **Change frequency**: Active development (recent: Change Intelligence, CKS integration)

### Your Environment
- **OS**: Windows 11 (primary), Unix-compatible
- **Languages**: Python 3.12+ (tested on 3.14)
- **Package Manager**: pip/hatchling
- **Dependencies**: Zero runtime dependencies (optional dev/test deps)
- **External Services**: CSF search (unified_router), CKS knowledge base, CHS chat history

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                        debugRCA CLI                             │
│                    (cli.py: main entry)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Evidence    │  │   Flow-of-   │  │  Meta-RAG    │
│  Tiering     │  │   Action      │  │  Engine      │
│              │  │   Tracer      │  │              │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ EvidenceSource│  │ActionTracer  │  │SimpleRCA     │
│ EvidenceTier  │  │ActionGraph   │  │Engine        │
│ EvidenceLedger│  │FlowVisualizer│  │- Fishbone    │
│ classify_     │  │ConvergeValid.│  │- Fault Tree  │
│ get_conf_     │  │DebugPyClient │  │- Causal Loop │
└──────┬────────┘  └──────┬────────┘  └──────┬────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   CSF Search  │  │     CKS      │  │   Metrics    │
│   Integration │  │  Knowledge   │  │  Tracking    │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ unified_router│ │cks_auto_     │  │RCASession    │
│ (CDS,Grep,    │ │extractor     │  │RCAMetrics    │
│  CHS,HDMA)    │ │store_rca_    │  │PhaseState    │
│               │ │finding       │  │enforce_      │
│ search_arch_  │ │PatternReg.   │  │verification  │
│ context()     │ │FixReg.       │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Subsystem Details

#### Evidence Tiering (evidence_tier.py)
- **Purpose**: Enforce confidence ceilings based on evidence quality
- **Files**: `evidence_tier.py`, tests in `test_evidence_tier.py`
- **Entry**: `classify_evidence()`, `get_confidence_ceiling()`, `apply_ceiling()`
- **Tiers**: TIER_1 (95%), TIER_2 (85%), TIER_3 (75%), TIER_4 (50%)
- **Integration**: Wired to CKS via `store_rca_finding()`

#### Flow-of-Action Tracing (action_tracer.py)
- **Purpose**: Track debugging workflow, detect divergences from expected paths
- **Files**: `action_tracer.py`, `flow_visualizer.py`, `converge_validator.py`
- **Entry**: `create_tracer_for_session()`, `get_expected_path()`
- **Outputs**: ActionGraph with divergence detection

#### Meta-RAG Engine (simple_rca_engine.py)
- **Purpose**: Unified RCA using multiple methodologies + unified search
- **Methodologies**: Fishbone (6M), Fault Tree, Causal Loop
- **Search Integration**: `search_architectural_context()` via unified_router
- **Change Intelligence**: Git log correlation for recent changes
- **CKS Integration**: Knowledge patterns included in synthesis

#### Metrics & Session (metrics_tracker.py, session.py)
- **Purpose**: Track RCA sessions, enforce verification gates
- **Features**: Problem hashing, regression detection, CHS/CKS search wrappers
- **Verification Gate**: Blocks fixes without verification when confidence > 0.7

---

## 3. EXECUTION AND DATA FLOW

### CLI Commands

```bash
# RCA analysis with architectural search
debug-rca arch "database timeout" --backends cds,cks --limit 10

# Evidence tiering operations
debug-rca evidence classify stack_trace --description "Error in auth.py"
debug-rca evidence ceiling --source "stack_trace:..."
debug-rca evidence tiers  # List all tier definitions

# Record findings
debug-rca record --outcome resolved --problem "..." --root-cause "..." --fix "..."

# Legacy (deprecated paths)
debug-rca analyze "error message"
debug-rca hypothesis "issue description"
```

### analyze_issue() Flow

```
1. Classify problem type (session.py: classify_problem_type)
2. Detect error type (session.py: detect_error_type)
3. Run regression check (session.py: run_regression_check)
4. Get recent git changes (Change Intelligence)
5. Execute methodologies:
   - Fishbone Analysis (_execute_fishbone_analysis)
   - Fault Tree Analysis (_execute_fault_tree_analysis)
   - Causal Loop Analysis (_execute_causal_loop_analysis)
6. Search knowledge patterns via CKS (_search_knowledge_patterns)
7. Search unified search backends (search_architectural_context)
8. Synthesize results (_synthesize_analysis)
   - Collect root causes from all methodologies
   - Collect recommendations + CKS patterns + recent changes
   - Generate final actionable_recommendations
```

### State Management

**Phase State Persistence** (`phase_state_manager.py`):
- Stored in: `~/.claude/state/rca/rca_workflow.json`
- Fields: session_id, phase, root_cause_found, outcome_recorded, etc.

**Evidence Ledger** (`evidence_tier.py`):
- In-memory ledger of evidence sources with tier classification
- Used for confidence ceiling calculations

**Metrics Tracking** (`metrics_tracker.py`):
- SQLite database: `~/.claude/state/rca/metrics.db`
- Tracks: sessions, fixes, verifications, search operations

---

## 4. COMPONENT INVENTORY

### Core Logic (src/debug_rca/)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `simple_rca_engine.py` | Main RCA engine | `SimpleRCAEngine`, `RCAAnalysis`, `RCAMethodologyResult` |
| `evidence_tier.py` | Confidence ceilings | `EvidenceTier`, `EvidenceSource`, `classify_evidence` |
| `action_tracer.py` | Workflow tracing | `ActionTracer`, `ActionGraph`, `EXPECTED_PATHS` |
| `session.py` | Session management | `classify_problem_type`, `search_cks_history` |
| `metrics_tracker.py` | Metrics & verification | `RCAMetricsTracker`, `enforce_verification_gate` |
| `confidence_tracker.py` | Bayesian confidence | `ConfidenceTracker`, hypothesis updates |
| `hypothesis_generator.py` | Hypothesis generation | `generate_hypotheses()` |
| `stack_trace_fingerprint.py` | Stack trace analysis | `StackTraceFingerprint`, similarity matching |
| `error_signature.py` | Error signatures | `ErrorSignature`, blame info |

### Cognitive Layer

| File | Purpose |
|------|---------|
| `cognitive_meta_agent.py` | Meta-agent for cognitive orchestration |
| `cognitive_mode_selector.py` | Select cognitive mode based on issue |
| `mental_model_selector.py` | Mental model selection |

### Integration Layer (integration/)

| File | Purpose |
|------|---------|
| `cks_pattern_integration.py` | CKS knowledge pattern search |
| `explore_integration.py` | Explore agent integration |
| `rca_specialist_integration.py` | RCA specialist agent |
| `taskmaster_integration.py` | TaskMaster integration |

### Core Utilities (core/)

| File | Purpose |
|------|---------|
| `context_analyzer.py` | Context analysis for RCA |
| `performance_optimizer.py` | Performance optimization |
| `tool_selector.py` | Tool selection based on issue |
| `rca_enhancer.py` | RCA result enhancement |

### Configuration & Infrastructure

| File | Purpose |
|------|---------|
| `cli.py` | CLI entry point |
| `config.py` | Configuration management |
| `hook_launcher.py` | Hook execution |
| `outcome_recorder.py` | Outcome tracking |
| `fix_registry.py` | Known fixes registry |
| `pattern_registry.py` | Known patterns registry |
| `local_fallback_mode.py` | Graceful degradation |
| `local_tool_adapter.py` | Local tool wrappers |

### Tests (tests/)

24 test files covering all major components:
- `test_simple_rca_engine.py` - Core engine tests (81 tests)
- `test_evidence_tier.py` - Evidence tiering
- `test_action_tracer.py` - Flow tracing
- `test_confidence_tracker.py` - Bayesian confidence
- `test_metrics_tracker.py` - Metrics & verification gates
- `test_session.py` - Session management
- Performance tests: `test_performance_perf001.py`, `perf003.py`
- Security tests: `test_sec001_hook_path_validation.py`, `sec002_metrics_input_validation.py`

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Evidence-Based**: Confidence must reflect evidence quality (tier system)
2. **Flow-Conscious**: Debugging workflows follow expected paths; divergences are flagged
3. **Knowledge-Integrated**: Learnings from previous incidents (CKS) inform current analysis
4. **Change-Aware**: Recent git commits are correlated with failures (Change Intelligence)
5. **Verification-Gated**: High-confidence fixes require verification before acceptance

### Technology Constraints
- Python 3.12+ required (uses modern type hints)
- Zero runtime dependencies (CSF integration optional)
- Graceful degradation when CSF unavailable

### Things That Must NOT Change
- **Evidence Tier ceilings**: TIER_1 = 95%, TIER_2 = 85%, TIER_3 = 75%, TIER_4 = 50%
- **Verification gate**: Confidence > 0.7 requires verification
- **CKS learning loop**: `store_rca_finding()` must write to CKS for resolved issues
- **Change Intelligence**: Git correlation must be path-filtered for multi-terminal safety

---

## 6. KNOWN ISSUES

### Current Workarounds

| Issue | Expected | Actual | Workaround |
|-------|----------|--------|------------|
| Multi-level caching | Available | "No module named 'src.modules'" | Not critical - feature degraded gracefully |
| Auto-learning expansion | Available | Not available | Manual query expansion |

### Recently Fixed (2025-02-17)
- **CKS synthesis bug**: Knowledge patterns searched but not included in recommendations → Fixed in `_synthesize_analysis()`
- **CLI backend filtering**: Backend names case-sensitive → Fixed with `parse_backends()` normalizer
- **Git path filter**: Used `**` wildcard incorrectly → Fixed to use git's path format
- **Test expectations**: Context empty check → Updated to expect `recent_changes`

---

## 7. INTEGRATION POINTS

### CSF Search (unified_router.py)

**Import paths** (tried in order):
1. `P:/__csf/src/knowledge/search/unified_router.py` (new)
2. `P:/__csf/src/search/unified_router.py` (old, deprecated)

**Backends used**:
- **CDS**: Code Documentation Search (function/class signatures)
- **Grep**: Code pattern search
- **CHS**: Chat History Search
- **CKS**: Constitutional Knowledge System
- **HDMA**: Architectural analysis (components, dependencies, anti-patterns)

**Method**: `search_architectural_context(issue, component_name, backends)`

**Returns**: `{"components": [], "dependencies": [], "anti_patterns": [], "similar_issues": [], "code_patterns": []}`

### CKS Integration

**Import**: `from cks import CKS`

**Methods**:
- `CKS.search(query, limit)` - Search knowledge base
- `store_rca_finding()` - Auto-extractor for resolved issues

**Storage**: CKS SQLite database at `~/.claude/state/cks/cks.db`

### NotebookLM Integration

**Notebook**: "debug-rca Package"

**Usage**: Store research papers, architecture docs, this review bundle for AI-assisted context retrieval.

---

## 8. APPENDIX: KEY ALGORITHMS

### Evidence Tiering Algorithm

```python
def get_confidence_ceiling(sources: list[EvidenceSource]) -> float:
    """Calculate confidence ceiling from evidence sources."""
    if not sources:
        return 0.5  # Default ceiling for no evidence

    # Get lowest tier among all sources
    lowest_tier = get_lowest_tier(sources)

    # Special case: only Tier 4 = flag as unverified
    if len(sources) == 1 and lowest_tier == EvidenceTier.TIER_4:
        return 0.5

    return lowest_tier.confidence_ceiling()
```

### Change Intelligence Algorithm

```python
def _get_recent_changes(
    time_window_hours: int = 2,
    path_filter: str | None = None,
    repo_root: str | None = None,
) -> list[dict]:
    """Get recent git commits for correlation."""
    cmd = ["git", "log", f"--since={since_format}", "--format=%H|%an|%s|%ct", "--no-merges"]
    if path_filter:
        cmd.extend(["--", path_filter])
    result = subprocess.run(cmd, cwd=repo_root or None, ...)
```

### CKS Learning Loop Integration

```python
def _synthesize_analysis(analysis: RCAAnalysis):
    # Collect CKS knowledge patterns
    if analysis.knowledge_patterns:
        for pattern in analysis.knowledge_patterns:
            lesson = pattern.get("lesson", "")
            if lesson:
                all_recommendations.append(f"[From CKS] {lesson}")

    # Collect recent changes
    for change in recent_changes[:5]:
        all_recommendations.append(f"[Recent Change] {commit_msg}... ({commit_hash})")
```

---

## 9. TEST SUMMARY

**Total Tests**: 849 (847 passed, 2 skipped)

**Key Test Files**:
- `test_simple_rca_engine.py`: 81 tests (full analysis workflow)
- `test_action_tracer.py`: 29 tests (flow tracing, divergence detection)
- `test_confidence_tracker.py`: 60+ tests (Bayesian updates)
- `test_evidence_tier.py`: Evidence tier classification
- `test_metrics_tracker.py`: Session tracking, verification gates

**Run**: `pytest tests/ -v`

---

## 10. QUICK START FOR REVIEWERS

```python
# Basic usage
from debug_rca import SimpleRCAEngine, classify_evidence, get_confidence_ceiling

# Run analysis
engine = SimpleRCAEngine()
analysis = engine.analyze_issue("Service crashes on startup")

# Check recommendations
print(analysis.actionable_recommendations)

# Evidence tiering
source = classify_evidence("stack_trace", "Error in auth.py line 42")
ceiling = get_confidence_ceiling([source])  # 0.95 for TIER_1

# Change Intelligence (automatic)
recent = analysis.context.get("recent_changes", [])
print(f"Found {len(recent)} recent changes for correlation")
```

**CLI Quick Test**:
```bash
debug-rca arch "authentication timeout" --backends cds,cks
```

---

**End of Review Bundle**
