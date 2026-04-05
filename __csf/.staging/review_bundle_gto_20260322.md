# GTO System Review Bundle

**Generated**: 2026-03-22
**Scope**: GTO (Gap/Task/Opportunity) Analysis System
**File Count**: ~64 source files (gto + gto_v2 combined)
**Execution Mode**: 4-agents (50+ files)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

GTO is a gap/task/opportunity analysis skill for Claude Code that analyzes chat transcripts and codebases to identify:
- Missing test coverage
- Documentation gaps
- Code quality issues (TODO, FIXME markers)
- Dependency health problems
- Git state issues (uncommitted changes)
- Error patterns in conversation history

Two versions exist in parallel:
- **gto/** (v1.0): Legacy three-layer system with Python detectors + AI subagents
- **gto_v2/** (v2.0): Streamlined transcript-focused system with GapFinder + HealthCalculator subagents

### Scale Metrics
- **LOC**: ~3000+ (combined gto + gto_v2)
- **Major subsystems**: 3 (gto detectors, gto_v2 subagents, shared hooks)
- **Deployment scope**: User-level Claude Code skill
- **Change frequency**: Active development (recent bug fixes through TASK-GTO-008)

### Your Environment
- **OS**: Windows 11 Pro 10.0.26200
- **Shell**: bash (Unix syntax on Windows)
- **Primary languages**: Python 3.14+
- **Package managers**: pip, uv

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GTO v1 (gto/) - Legacy                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: Claude Orchestrator (gto_orchestrator.py)        │   │
│  │  /gto skill invocation → ViabilityGate → Detectors →       │   │
│  │  Subagents → ResultsBuilder → NextStepsFormatter → Output  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: AI Subagents (subagents/)                        │   │
│  │  GapFinderSubagent, HealthCalculatorSubagent                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: Python Deterministic (lib/)                      │   │
│  │  viability_gate, chain_integrity, session_goal_detector    │   │
│  │  unfinished_business_detector, code_marker_scanner         │   │
│  │  test_presence_checker, docs_presence_checker              │   │
│  │  dependency_checker, state_manager, results_builder         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    GTO v2 (gto_v2/) - Current                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Orchestrator (gto_orchestrator.py)                        │   │
│  │  - Handoff chain traversal (MAX_CHAIN_DEPTH=50)            │   │
│  │  - GapFinder + HealthCalculator + GitContext subagents     │   │
│  │  - Result envelopes with artifact files                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  lib/ (subagents.py, health_scoring.py, git_context.py)    │   │
│  │  - GapFinderSubagent: transcript error pattern matching    │   │
│  │  - HealthCalculatorSubagent: weighted category scoring     │   │
│  │  - GitContextSubagent: git repo state analysis            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  hooks/ (validate_format.py, checklist_gate.py,            │   │
│  │           session_summary.py)                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Differences: gto vs gto_v2

| Aspect | gto (v1) | gto_v2 (v2) |
|--------|----------|--------------|
| Focus | Codebase gap detection | Transcript-based gap analysis |
| Architecture | 3-layer (detectors + subagents + orchestrator) | 2-phase (gaps → health) |
| State | Terminal-scoped state files | Result envelopes + artifacts |
| Session handling | Single transcript | Handoff chain traversal |
| Git integration | Via detectors | Via GitContext subagent |

---

## 3. EXECUTION AND DATA FLOW

### GTO v2 Execution Flow

```
User invokes /gto
    ↓
gto_orchestrator.py:main()
    ↓
get_transcript_path() → transcript_path
    ↓
get_all_transcript_paths(terminal_id)
    - Follows handoff chain via HandoffFileStorage
    - Extracts resume_snapshot.transcript_path from each session
    - Detects circular references (CIRCUIT_BREAKER_THRESHOLD=3)
    ↓
run_analysis(terminal_id)
    ├→ GapFinderSubagent.run() [per transcript]
    │   - Parses transcript.jsonl
    │   - Pattern matching: CRITICAL/HIGH/MEDIUM/LOW patterns
    │   - Writes artifact: gap_finder_{terminal_id}_{timestamp}.md
    │   ↓
    │   ResultEnvelope(status="done", artifact=path, gaps_found=N)
    │
    ├→ GitContextSubagent.run()
    │   - git.Repo analysis
    │   - Modified files, recent commits, branch
    │   ↓
    │   ResultEnvelope(status="done", artifact=path, dirty=bool)
    │
    └→ HealthCalculatorSubagent.run(gaps, git_context)
        - HealthScoringEngine.calculate_health_score()
        - 5 categories: tests(30%), documentation(20%), git(20%),
        │              dependencies(15%), code_quality(15%)
        - Severity deductions: critical=-20, high=-10, medium=-5, low=-2
        ↓
        ResultEnvelope(status="done", artifact=path, overall_score=N)
    ↓
print_compact_snapshot(results)
    - "=== GTO SNAPSHOT ==="
    - Health score + status emoji
    - Git dirty/clean
    - Artifact paths
```

### State Management

**Multi-terminal isolation**:
- Terminal-scoped evidence directories: `.evidence/gto_*-{terminal_id}/`
- Timestamp-based artifact naming prevents collisions
- No shared mutable state between terminals

**Handoff chain traversal**:
- SessionStart hook injects `resume_snapshot.transcript_path`
- Traversal follows chain from current to oldest session
- Circuit breaker at 3 circular detections
- Max chain depth: 50 sessions

---

## 4. COMPONENT INVENTORY

### Core Files

#### gto/ (v1 - Legacy)

| File | Responsibility |
|------|---------------|
| `gto_orchestrator.py` | Main entry, viability gate, detector orchestration |
| `SKILL.md` | Skill definition (v3.0.0) |
| `references/architecture.md` | Architecture diagrams, data flow |
| `references/api.md` | API reference |
| `references/error-patterns.md` | Error severity classifications |
| `references/conversation-patterns.md` | User feedback patterns |
| `references/health-thresholds.md` | Health score thresholds |
| `references/output-template.md` | Output formatting |

#### gto/lib/ (v1 - Deterministic Detectors)

| File | Responsibility |
|------|---------------|
| `viability_gate.py` | Precondition checking (git exists, clean dir) |
| `chain_integrity_checker.py` | Execution chain validation |
| `session_goal_detector.py` | Session goal from transcript |
| `unfinished_business_detector.py` | Prior run unfinished items |
| `code_marker_scanner.py` | TODO/FIXME/HACK marker scanning |
| `test_presence_checker.py` | Test file coverage checking |
| `docs_presence_checker.py` | Documentation presence checking |
| `dependency_checker.py` | Dependency health checking |
| `skill_self_health_checker.py` | Self-diagnostic |
| `state_manager.py` | Multi-terminal state, atomic writes |
| `results_builder.py` | Gap consolidation, deduplication |
| `next_steps_formatter.py` | Recommended steps formatting |
| `history_scanner.py` | Chat history scanning |
| `adjacent_file_scanner.py` | Adjacent file analysis |

#### gto_v2/ (v2 - Current)

| File | Responsibility |
|------|---------------|
| `gto_orchestrator.py` | Handoff chain, subagent orchestration, artifact management |
| `health_scoring.py` | HealthScoringEngine, 5-category weighted scoring |
| `git_context.py` | Git repo context (branch, dirty, commits, patterns) |
| `skill_cache.py` | Skill metadata caching |
| `quality_log_reader.py` | Quality log analysis |
| `SKILL.md` | Skill definition |
| `references/gto-workflow.md` | Complete execution workflow |
| `references/error-patterns.md` | Error severity patterns |
| `references/conversation-patterns.md` | User feedback patterns |
| `references/git-context-integration.md` | Git integration guide |

#### gto_v2/lib/

| File | Responsibility |
|------|---------------|
| `subagents.py` | GapFinderSubagent, HealthCalculatorSubagent, GitContextSubagent |
| `result_envelope.py` | Envelope creation, artifact writing |
| `monitor.py` | SubagentMonitor with retry logic |
| `subagent_monitor.py` | Monitoring utilities |

#### Shared Components

| Path | Responsibility |
|------|---------------|
| `gto/hooks/validate_format.py` | Output format validation |
| `gto/hooks/checklist_gate.py` | Checklist enforcement |
| `gto/hooks/session_summary.py` | Session summary generation |
| `gto_v2/hooks/validate_format.py` | (same) |
| `gto_v2/hooks/checklist_gate.py` | (same) |
| `gto_v2/hooks/session_summary.py` | (same) |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Multi-terminal safety**: Each terminal gets isolated state, no shared mutable state
2. **Transcript-first analysis**: gto_v2 analyzes conversation transcripts, not just codebase
3. **Handoff chain awareness**: Sessions can be resumed via handoff system
4. **Artifact-based output**: Heavy results written to files, light envelopes returned
5. **Circuit breaker protection**: Prevent infinite loops in handoff chain traversal

### Technology Constraints

- **Python 3.14+**: Type hints, dataclasses, modern patterns
- **GitPython**: For git context (optional import with fallback)
- **No external API calls**: All analysis is local
- **Atomic writes**: State files use temp-file + replace pattern

### Performance SLAs

- **Handoff chain traversal**: 5-second timeout per transcript extraction
- **Subagent execution**: 5-second timeout via `timeout_handler` decorator
- **Chain depth limit**: 50 sessions max
- **Artifact retention**: 7 days before cleanup

### Things That Must NOT Change

1. **Terminal isolation**: State directories must remain terminal-scoped
2. **Timestamp artifacts**: Artifact naming must include timestamp to prevent collisions
3. **Circuit breaker**: Circular reference detection must block infinite loops
4. **Import safety**: GitPython must remain optional (try/except import)

---

## 6. KNOWN ISSUES

All historical bugs (TASK-GTO-001 through TASK-GTO-008) have been **completed**:

| Task ID | Issue | Fix |
|---------|-------|-----|
| TASK-GTO-001 | INV-001 - MD5 hash semantic equivalence bug | Fixed |
| TASK-GTO-002 | INV-002 - Deduplication loses multi-source metadata | Fixed |
| TASK-GTO-003 | INV-003 - Unknown severities silently dropped | Fixed |
| TASK-GTO-004 | LOGIC-002 - Uninitialized tmp_path in exception handler | Fixed |
| TASK-GTO-005 | STATE-001 - Race condition in append_history() | Fixed |
| TASK-GTO-006 | FM-001 - Atomic write race between terminals | Fixed |
| TASK-GTO-007 | STATE-002 - TOCTOU bug in temp file cleanup | Fixed |
| TASK-GTO-008 | SEC-001 - Path traversal via symlink bypass | Fixed |

### ADR Implementation

- **ADR-20260321**: GTO viability gate security fixes - implemented
- **ADR-20260321**: GTO viability gate performance and validation - PENDING (TASK-2341)

---

## 7. INTEGRATION POINTS

### Hooks

Both gto and gto_v2 have identical hook sets:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `validate_format.py` | Pre-response | Validates GTO output format |
| `checklist_gate.py` | Pre-response | Enforces checklist items |
| `session_summary.py` | Post-response | Generates session summary |

### Handoff System Integration

```
SessionStart hook
    ↓ (injects resume_snapshot)
handoff_store.py (per terminal)
    ↓ (provides transcript_path chain)
gto_orchestrator.py:get_all_transcript_paths()
    ↓ (extracts from SessionStart messages)
HandoffFileStorage.load_raw_handoff()
```

### Evidence Artifacts

| Artifact | Format | Content |
|----------|--------|---------|
| `gap_finder_{terminal}_{timestamp}.md` | Markdown | Gap analysis by severity |
| `health_{terminal}_{timestamp}.md` | Markdown | Health score breakdown |
| `git_context_{terminal}_{timestamp}.md` | Markdown | Git repository state |

---

## 8. APPENDIX: KEY DATA STRUCTURES

### GapFinderSubagent Pattern Matching

```python
CRITICAL_PATTERNS = [
    (r"ImportError.*No module named", "import_error"),
    (r"Hook error.*IMPORT_FAIL", "hook_import_fail"),
    (r"Hook error.*", "hook_error"),
    (r"NameError.*not defined", "name_error"),
]

HIGH_PATTERNS = [
    (r"TypeError.*unsupported operand", "type_error"),
    (r"AttributeError.*has no attribute", "attribute_error"),
    (r"FAILED|ERROR", "test_failure"),
    (r"AssertionError.*", "assertion_error"),
    (r"Exit code [1-9]", "exit_code_error"),
    (r"tool_use_error", "tool_error"),
]
```

### Health Scoring Categories

| Category | Weight | Deduction per Gap |
|----------|--------|-------------------|
| tests | 30% | critical=-20, high=-10, medium=-5, low=-2 |
| documentation | 20% | (same) |
| git | 20% | (same) |
| dependencies | 15% | (same) |
| code_quality | 15% | (same) |

### ResultEnvelope

```python
@dataclass
class ResultEnvelope:
    status: str           # "done", "blocked", "failed"
    artifact: str         # Path to artifact file
    summary: str          # Brief summary
    metrics: dict         # Status-specific metrics
    attempts: int         # Retry attempts
    duration_ms: int      # Execution time
```

---

## ASSUMPTIONS

1. **gto_v2 is the current version**: gto/ appears to be legacy v1
2. **Both versions are active**: Git status shows modifications to gto_orchestrator.py in gto/
3. **Handoff package path**: gto_v2 references `packages/handoff` for chain traversal
4. **Evidence cleanup**: 7-day retention for artifact files

---

*Bundle prepared for LLM context gathering about GTO system architecture and components.*
