# Review Bundle: debugRCA

**Generated**: 2026-02-17
**Scope**: P:\packages\debugRCA
**File Count**: ~211 files (42 Python sources, 25 tests, 12 skill tests)
**Execution Mode**: 4 parallel agents

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Package**: debugRCA
- **Version**: 1.0.0
- **License**: MIT
- **Python**: 3.12+
- **Runtime Dependencies**: None (zero-dep design)

### Domain & Purpose
debugRCA is a Tier 1 Root Cause Analysis framework that provides systematic debugging workflows for Claude Code. It combines:

1. **Python library** for evidence tracking, hypothesis scoring, and RCA methodologies
2. **Claude Code skill** (`/debugRCA`, aliases `/r`, `/verify`, `/fix`) for AI-assisted investigation
3. **Flow-of-Action paradigm** for tracing investigation paths and detecting divergence
4. **Evidence tiering system** (Tiers 1-4) with confidence ceilings to prevent overconfidence
5. **CKS integration** for historical knowledge storage and semantic pattern matching
6. **Local fallback mode** for offline operation without external dependencies

### Scale Metrics
- **LOC**: ~8,000+ Python lines (core), ~3,000 lines (tests)
- **Major Subsystems**: 7 (Core, Integration, Evidence, Hypothesis, Flow, Metrics, Hooks)
- **Deployment Scope**: Claude Code local development environments
- **Change Frequency**: Active development (commit 5db735ee92)

### Your Environment
- **OS**: Windows 11 Pro
- **Shell**: bash
- **Package Manager**: pip/uv
- **Databases**: SQLite (TaskMaster, Evidence ledger)
- **External Services**: CKS (optional), CHS (optional), DaemonClient (optional)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Claude Code Interface                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ /debug   │    │  /rca    │    │ /verify  │    │   /fix   │      │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘      │
│       │               │               │               │            │
│       └───────────────┴───────────────┴───────────────┘            │
│                           │                                        │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Skill Hooks Layer                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                 │  │
│  │  │ PostToolUse_     │  │ StopHook_        │                 │  │
│  │  │ rca_init         │  │ rca_enforcement  │                 │  │
│  │  │ rca_phase_       │  │                  │                 │  │
│  │  │   tracker        │  │ SessionEnd_      │                 │  │
│  │  │ rca_action_      │  │   rca_cleanup    │                 │  │
│  │  │   tracker        │  │                  │                 │  │
│  │  └──────────────────┘  └──────────────────┘                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                        │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Core RCA Engine                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│  │  │ Evidence    │  │ Hypothesis │  │  Simple    │            │  │
│  │  │ Tier       │  │ Scorer     │  │ RCA Engine │            │  │
│  │  └────────────┘  └────────────┘  └────────────┘            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│  │  │ Confidence  │  │ Action     │  │ Flow       │            │  │
│  │  │ Tracker    │  │ Tracer     │  │ Visualizer │            │  │
│  │  └────────────┘  └────────────┘  └────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                        │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Integration Layer                           │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │  │
│  │  │   CKS  │  │   CHS  │  │ Serena │  │Context7│           │  │
│  │  │ (opt)  │  │ (opt)  │  │  MCP   │  │  MCP   │           │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                        │
│                           ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   State Persistence                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│  │  │ rca/       │  │ TaskMaster │  │ Evidence   │            │  │
│  │  │ state/     │  │ SQLite     │  │ Ledger     │            │  │
│  │  └────────────┘  └────────────┘  └────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### Core RCA Components
- **Location**: `src/debug_rca/`
- **Purpose**: Core analysis logic
- **Key Files**:
  - `simple_rca_engine.py` - Meta-RAG codebase indexer with Fishbone, Fault Tree, Causal Loop
  - `evidence_tier.py` - 4-tier evidence classification (TIER_1: 95%, TIER_2: 85%, TIER_3: 75%, TIER_4: 50%)
  - `hypothesis_scorer.py` - Bayesian hypothesis ranking (Reproducibility 0.3, Recency 0.2, Impact 0.5)
  - `confidence_tracker.py` - Bayesian probability updates
  - `session.py` - Problem classification and session management

#### Flow-of-Action System
- **Location**: `src/debug_rca/`
- **Purpose**: Track investigation paths, detect divergence
- **Key Files**:
  - `action_tracer.py` - Records actions as directed graph
  - `flow_visualizer.py` - Generates Mermaid diagrams
  - `converge_validator.py` - Evidence convergence validation

#### Integration Layer
- **Location**: `src/debug_rca/integration/`
- **Purpose**: External service connections
- **Key Files**:
  - `cks_pattern_integration.py` - CKS pattern registry
  - `explore_integration.py` - External search integration
  - `rca_specialist_integration.py` - RCA specialist bridge

#### Skill Hooks
- **Location**: `skill/hooks/`
- **Purpose**: Claude Code integration
- **Key Files**:
  - `PostToolUse_rca_init.py` - Initialize RCA workflow
  - `PostToolUse_rca_phase_tracker.py` - Track investigation phases (-1 to 6)
  - `PostToolUse_rca_action_tracker.py` - Record tool usage
  - `StopHook_rca_enforcement.py` - Enforce RCA completion
  - `SessionEnd_rca_cleanup.py` - Archive findings

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

#### Debug Workflow (`/debug`)
```
1. User invokes /debug with problem description
2. PostToolUse_rca_init creates workflow state
3. Problem classified: ERROR | TEST | CRASH | PERFORMANCE | BEHAVIOR
4. CKS history search (if available)
5. Evidence collection phase
6. Hypothesis generation and scoring
7. Fix attempt
8. Verification
9. SessionEnd archives findings to CKS
```

#### RCA Workflow (`/rca`)
```
1. User invokes /rca with problem description
2. Phase -1: History check (CKS/CHS search)
3. Phase 0: System context check
4. Phase 1: Data flow trace (Read, Grep, Serena)
5. Phase 2: Hypothesis ledger
6. Phase 3: Five Whys analysis
7. Phase 4: Invariant check
8. Phase 4: Counterfactual test
9. Phase 6: Timeboxing escalation (--debate, --challenge)
10. Synthesis checkpoint after 3-5 findings
11. StopHook enforcement validates completion
```

### State Management

#### State Locations
- **Active Session**: `P:/.claude/state/rca/active_session.json`
- **Workflow State**: `P:/.claude/state/rca/rca_workflow.json`
- **Action Graph**: `~/.claude/state/rca/actions_{session_id}.json`
- **Metrics DB**: `.speckit/taskmaster/tasks.db`
- **Evidence Ledger**: `.claude/session_data/evidence.db`

#### Consistency Model
- **Session TTL**: 8 hours
- **Multi-terminal isolation**: Uses `CLAUDE_TERMINAL_ID` (not session_id)
- **Phase persistence**: CKS-backed or local JSON fallback
- **Write-behind caching**: PERF-001 pattern queue for CKS storage

### Error Handling

#### Fail-Open Policy
All external integrations (CKS, CHS, DaemonClient, Serena MCP) are **optional** with graceful fallback:

```python
try:
    from daemons.daemon_client import DaemonClient
    DAEMON_AVAILABLE = True
except ImportError:
    DAEMON_AVAILABLE = False
    # Continue without daemon functionality
```

#### Retry Behavior
- **Session Budget**: 100,000 tokens default (~$2.00)
- **Max Retries**: 3 before escalation
- **Timeboxing**: Escalation to --debate mode after phase 6

---

## 4. COMPONENT INVENTORY

### Core Logic

| Component | Path | Responsibility |
|-----------|------|----------------|
| **SimpleRCAEngine** | `simple_rca_engine.py` | Meta-RAG with Fishbone, Fault Tree, Causal Loop |
| **EvidenceTier** | `evidence_tier.py` | 4-tier classification with confidence ceilings |
| **EvidenceLedger** | `evidence_tier.py` | Accumulate evidence for investigation |
| **HypothesisScorer** | `hypothesis_scorer.py` | Bayesian hypothesis ranking |
| **ConfidenceTracker** | `confidence_tracker.py` | Bayesian probability updates |
| **Session** | `session.py` | Problem classification, session management |
| **ActionTracer** | `action_tracer.py` | Record investigation actions |
| **FlowVisualizer** | `flow_visualizer.py` | Mermaid diagram generation |
| **ConvergeValidator** | `converge_validator.py` | Evidence convergence validation |

### Utilities/Helpers

| Component | Path | Responsibility |
|-----------|------|----------------|
| **ErrorSignature** | `error_signature.py` | Stack trace fingerprinting |
| **QualityEstimator** | `quality_estimator.py` | Evidence quality assessment |
| **LocalToolAdapter** | `local_tool_adapter.py` | Fallback tool implementations |
| **ToolChecker** | `tool_checker.py` | Tool availability validation |
| **Config** | `config.py` | Configuration management |

### Integration

| Component | Path | Responsibility |
|-----------|------|----------------|
| **CKSPatternRegistry** | `integration/cks_pattern_integration.py` | CKS-backed pattern fixes |
| **CKSAutoExtractor** | `cks_auto_extractor.py` | Auto-store learnings |
| **ExploreIntegration** | `integration/explore_integration.py` | External search bridge |
| **RCASpecialistIntegration** | `integration/rca_specialist_integration.py` | Specialist signature bridge |

### Infrastructure

| Component | Path | Responsibility |
|-----------|------|----------------|
| **MetricsTracker** | `metrics_tracker.py` | KPI tracking (CHS usage, fix success, recurrence) |
| **PhaseStateManager** | `phase_state_manager.py` | Investigation phase persistence |
| **HookLauncher** | `hook_launcher.py` | Portable hook execution |
| **CLI** | `cli.py` | Command-line interface |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Zero Dependency Runtime**: No external runtime dependencies; all integrations optional
2. **Evidence-Based Confidence**: Confidence ceilings based on evidence tier quality
3. **Structured Investigation**: Enforced 10-step methodology with phase tracking
4. **Knowledge Capture**: Automatic CKS ingestion of resolved investigations
5. **Flow-of-Action**: Trace investigation paths to detect divergence from expected patterns

### Technology Constraints

- **Python 3.12+** required (modern type hints, pattern matching)
- **SQLite** for metrics and evidence persistence
- **Claude Code hooks** for integration (PostToolUse, Stop, SessionEnd)
- **MCP servers** (Serena, Context7) are optional external dependencies

### Performance SLAs

- **Hook timeout**: 10 seconds (PostToolUse), 5 seconds (Stop)
- **Session TTL**: 8 hours inactivity
- **Synthesis checkpoint**: After 3-5 findings or when converged

### Things That Must NOT Change

1. **Evidence tier ceiling logic**: TIER_4 alone must flag as [UNVERIFIED]
2. **Multi-terminal isolation**: Must use `CLAUDE_TERMINAL_ID` not session_id
3. **Fail-open integration**: All external services must be optional
4. **Phase enforcement**: StopHook must validate engine execution and delegation
5. **Synthesis protocol**: Must stop and synthesize after 3-5 findings

---

## 6. KNOWN ISSUES

| Severity | Scenario | Expected vs Actual | Impact | Workaround |
|----------|----------|-------------------|--------|------------|
| LOW | `local_tool_adapter.py` | 24% test coverage | Edge cases untested | Tested via integration |
| LOW | `quality_estimator.py` | 22% test coverage | Edge cases untested | Manual review |
| LOW | `tool_checker.py` | 0% direct coverage | No unit tests | Tested via hooks |

### Resolved Issues (from INTEGRATION_SUMMARY.md)

- ~~HDMA indexing missing `--analyze` flag~~ → Fixed (Task #1034)
- ~~terminal_id vs session_id confusion~~ → Fixed (Task #1035)
- ~~CLI bugs~~ → Fixed (Task #1039)
- ~~EvidenceLedger not wired to CKS~~ → Fixed (Task #1019)

---

## 7. INTEGRATION POINTS

### Claude Code Hooks

```json
{
  "PostToolUse": [
    {
      "matcher": "Skill",
      "hooks": [{"type": "command", "command": "python .../PostToolUse_rca_init.py"}]
    }
  ],
  "Stop": [
    {
      "matcher": ".*",
      "hooks": [{"type": "command", "command": "python .../StopHook_rca_enforcement.py"}]
    }
  ],
  "SessionEnd": [
    {
      "matcher": ".*",
      "hooks": [{"type": "command", "command": "python .../SessionEnd_rca_cleanup.py"}]
    }
  ]
}
```

### Python API

```python
from debug_rca import SimpleRCAEngine, EvidenceTier, HypothesisScorer

# Run RCA analysis
engine = SimpleRCAEngine()
analysis = engine.analyze_issue("Error: KeyError on startup")

# Evidence tiering
from debug_rca.evidence_tier import EvidenceLedger, EvidenceSource
ledger = EvidenceLedger()
ledger.add(EvidenceSource.TIER_1, "Direct observation", "file:line")

# Hypothesis scoring
scorer = HypothesisScorer()
scorer.add_hypothesis("Missing import", reproducibility=0.9, recency=0.8, impact=0.7)
top = scorer.get_top_hypotheses(n=3)
```

### CLI Commands

```bash
debug-rca analyze "Error description"
debug-rca hypothesis "Problem description"
debug-rca search "KeyError pattern"
debug-rca record --outcome resolved --problem "..." --root-cause "..." --fix "..."
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEBUG_RCA_STATE_DIR` | `P:/.claude/state/rca` | State directory |
| `DEBUGRCA_LOCAL_ONLY` | false | Local-only mode |
| `DEBUGRCA_SATURATION_THRESHOLD` | 0.75 | Evidence saturation threshold |
| `CKS_STORAGE_DISABLED` | unset | Disable CKS storage |
| `DEBUG_RCA_CSF_SRC` | `P:/__csf/src` | CSF source path |

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample RCA Session (from sample_rca.json)

```json
{
  "problem_type": "database_connection_timeout",
  "severity": "high",
  "phases": {
    "-1": "history_check": "CKS search found 2 similar incidents",
    "1": "data_flow_trace": "Traced connection pool → database layer",
    "3": "five_whys": ["Why timeout?", "Why pool exhausted?", "Why no cleanup?"]
  },
  "root_cause": "Connection leak in auth module (file: auth.py:142)",
  "fix_applied": "Added context manager for connection handling",
  "verification": "pytest tests/conftest.py::test_auth_connection - PASSED"
}
```

### Evidence Tier Example

```python
# TIER_1: Direct observation (95% ceiling)
EvidenceSource.TIER_1, "Debugger showed variable = None", "debugger:main.py:45"

# TIER_2: Strong indirect (85% ceiling)
EvidenceSource.TIER_2, "Log shows exception before crash", "logfile:app.log:1234"

# TIER_3: Weak indirect (75% ceiling)
EvidenceSource.TIER_3, "Code review found potential race", "review:PR#42"

# TIER_4: Unverified (50% ceiling, flags [UNVERIFIED])
EvidenceSource.TIER_4, "Seems like a timing issue", "hypothesis"
```

---

## END OF REVIEW BUNDLE

**Generated by**: /review_bundle debugRCA
**Agent Execution**: 4 parallel agents (Explorer, Core Reader, Skill Reader, Dependency Scanner)
**Total Duration**: ~313 seconds
**Total Tokens**: ~418,000

For questions or issues, refer to:
- `P:\packages\debugRCA\README.md` - Complete module reference
- `P:\packages\debugRCA\skill\SKILL.md` - Skill documentation
- `P:\packages\debugRCA\skill\INTEGRATION_SUMMARY.md` - Implementation summary
