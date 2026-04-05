# Review Bundle: /gto Skill System

**Generated**: 2026-03-21
**Scope**: P:\.claude\skills\gto\ (skill + Python + hooks)
**File Count**: ~50 files (core: ~15, evidence artifacts: ~20, state: ~10, others: ~5)
**Execution Mode**: 2-agents (10-50 file range)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

/gto ("Gap, Task, Opportunity") analyzes chat transcripts to identify:
- **Gaps**: Errors, failures, issues that occurred
- **Tasks**: Pending work, cleanup, commits needed
- **Opportunities**: Learning moments, documentation needs, improvements

**Perfect for**: Picking up work after breaks, overnight, or context loss. The skill does NOT scan code/files—only analyzes the chat transcript.

### Scale Metrics

- **LOC**: ~2,500 lines Python (core), ~500 lines hooks
- **Major subsystems**: 3 (Gap detection, Health scoring, Git context)
- **Deployment scope**: Local Claude Code skill (solo developer environment)
- **Change frequency**: Active development (recent: uncommitted files detection, handoff chain traversal)

### Your Environment

- **OS/Shell**: Windows 11, bash (POSIX-compliant tools)
- **Languages**: Python 3.14 (main), bash scripts
- **Dependencies**: GitPython (optional, for git context)
- **External services**: None (local-only, multi-terminal safe)

---

## 2. ARCHITECTURE OVERVIEW

```
                    USER INVOCATION
                           │
                           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  LAYER 1: CLAUDE (Orchestrator)                              │
    │  Reads SKILL.md workflow instructions                        │
    │  Invokes: python gto_orchestrator.py --terminal-id $TERMID   │
    └──────────────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  LAYER 2: gto_orchestrator.py (Python Entry Point)          │
    │  - get_all_transcript_paths() - Handoff chain traversal     │
    │  - monitor.execute_with_retry() - Subagent orchestration    │
    │  - print_compact_snapshot() - Output formatting             │
    └──────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ GapFinder   │ │ GitContext  │ │HealthCalc   │
    │ Subagent    │ │ Subagent    │ │ Subagent    │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           ▼               ▼               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  LAYER 4: Artifacts (.evidence/)                              │
    │  - gap_finder_*.md - Detected gaps by turn/severity           │
    │  - git_context_*.md - Branch, status, modified files          │
    │  - health_*.md - Overall score, category breakdowns           │
    └──────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. GapFinderSubagent (lib/subagents.py)

**Purpose**: Detect errors, test failures, and user frustration in transcripts

**Key files**:
- `lib/subagents.py` (lines 25-282)
- `references/error-patterns.md` - Pattern definitions
- `references/conversation-patterns.md` - Frustration patterns

**Entry point**: `GapFinderSubagent.run(transcript_path, scope, terminal_id, working_dir)`

**Dependencies**:
- Upstream: None (reads transcript directly)
- Downstream: HealthCalculatorSubagent (consumes gap list)

**Critical invariants**:
- Returns lightweight envelope, protects context
- Artifact written to `.evidence/gap_finder_{terminal_id}_{timestamp}.md`
- No line numbers or file paths captured (TODO)

#### 2. HealthCalculatorSubagent (lib/subagents.py)

**Purpose**: Calculate aggregate health score from detected gaps

**Key files**:
- `lib/subagents.py` (lines 285-362)
- `health_scoring.py` - Scoring engine

**Entry point**: `HealthCalculatorSubagent.run(gaps, git_context, terminal_id)`

**Dependencies**:
- Upstream: GapFinderSubagent, GitContextSubagent
- Downstream: None (final output)

**Critical invariants**:
- Category weights: Tests 30%, Docs 20%, Git 20%, Deps 15%, Code Quality 15%
- Severity deductions: Critical -20, High -10, Medium -5, Low -2
- Adds synthetic gap for uncommitted files (NEW in latest version)

#### 3. GitContextSubagent (lib/subagents.py)

**Purpose**: Extract git repository state for analysis

**Key files**:
- `lib/subagents.py` (lines 365-460)
- `git_context.py` - Git repo reader

**Entry point**: `GitContextSubagent.run(working_directory, terminal_id)`

**Dependencies**:
- Upstream: None (reads git repo directly)
- Downstream: HealthCalculatorSubagent (for synthetic gap)

**Critical invariants**:
- Multi-terminal safe: No caching, always fresh reads
- Git repo is shared source of truth
- Returns None if git unavailable (graceful degradation)

#### 4. Hook System (hooks/)

**Purpose**: Validate output, track checklists, session summaries

**Key files**:
- `hooks/validate_format.py` - PostToolUse: Validates /gto output format
- `hooks/checklist_gate.py` - Stop: Reminds pending items before session end
- `hooks/session_summary.py` - SessionEnd: Shows summary and cleanup

**Critical invariants**:
- State stored in `.state/gto_checklist_{terminal_id}.json`
- Non-blocking (warnings only, never blocks execution)
- Terminal-scoped state (multi-terminal isolation)

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequence

```
User: /gto
  │
  ├─> Claude reads SKILL.md workflow instructions
  │
  ├─> Claude invokes: python gto_orchestrator.py --terminal-id $TERMID
  │
  ├─> gto_orchestrator.py:
  │   ├─> get_all_transcript_paths(terminal_id)
  │   │   └─> Follow handoff chain (max depth: 50)
  │   │
  │   ├─> For each transcript:
  │   │   └─> GapFinderSubagent.run()
  │   │       ├─> Parse transcript JSON lines
  │   │       ├─> Detect error patterns
  │   │       └─> Write .evidence/gap_finder_*.md
  │   │
  │   ├─> GitContextSubagent.run()
  │   │   ├─> get_git_context(working_dir)
  │   │   └─> Write .evidence/git_context_*.md
  │   │
  │   ├─> HealthCalculatorSubagent.run()
  │   │   ├─> calculate_health_score(gaps, git_context)
  │   │   │   ├─> Add synthetic gap for uncommitted files
  │   │   │   ├─> Categorize gaps
  │   │   │   └─> Calculate weighted score
  │   │   └─> Write .evidence/health_*.md
  │   │
  │   └─> print_compact_snapshot(results)
  │       └─> Output to stdout
  │
  ├─> Claude returns output to user
  │
  └─> PostToolUse hook: validate_format.py
      ├─> Validates required sections present
      ├─> Saves checklist items to state
      └─> Returns warnings (non-blocking)
```

### State Management

**State stores**:
- `.state/gto_checklist_{terminal_id}.json` - Checklist items from last /gto run
- `.state/gto_session_{terminal_id}.json` - Session flag for Stop hook
- `.evidence/` - Artifacts (gap_finder_*.md, git_context_*.md, health_*.md)

**Consistency model**:
- Terminal-scoped state isolation (per-terminal directories)
- Git repo is shared source of truth (safe for multi-terminal)
- Artifacts use timestamp collision prevention (multi-terminal safe)

**Isolation boundaries**:
- Each terminal has isolated state directory
- Evidence artifacts include terminal_id in filename
- Git context is shared but read-only (no conflicts)

### Error Handling

**Fail-open policy**:
- GitContextSubagent: Returns None if git unavailable (continues without git data)
- GapFinderSubagent: Continues on malformed transcript lines (JSON decode errors)
- HealthCalculatorSubagent: Handles missing git_context gracefully

**Retry behavior** (via SubagentMonitor):
- MAX_RETRIES = 3
- RETRY_DELAY_MS = 100
- On exhaustion: Returns error envelope, doesn't crash

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Key Functions/Classes | Responsibility | Inputs/Outputs | Limitations |
|------|----------------------|----------------|----------------|-------------|
| `gto_orchestrator.py` | `run_analysis()`, `get_all_transcript_paths()` | Main entry point, handoff chain traversal | terminal_id → results dict | No Recommended Next Steps generation |
| `lib/subagents.py` | `GapFinderSubagent`, `GitContextSubagent`, `HealthCalculatorSubagent` | Subagent implementations | Various → envelope dict | GapFinder has no line number validation |
| `health_scoring.py` | `HealthScoringEngine.calculate_health_score()` | Health scoring engine | gaps, git_context → HealthScore | Categorization is keyword-based |
| `git_context.py` | `get_git_context()` | Git repo reader | working_directory → git dict | Returns None if git unavailable |

### Utilities/Helpers

| File | Key Functions/Classes | Responsibility | Inputs/Outputs |
|------|----------------------|----------------|----------------|
| `lib/monitor.py` | `SubagentMonitor.execute_with_retry()` | Retry logic, health monitoring | func, kwargs → MonitorResult |
| `lib/result_envelope.py` | `create_envelope()`, `write_artifact()`, `read_artifact()` | Artifact I/O | content → file, file → content |
| `lib/subagent_monitor.py` | `SubagentMonitor` | Duplicate of monitor.py | (deprecated) |

### Configuration

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill metadata, workflow instructions, hook definitions |
| `.skill_cache.json` | Skill execution cache |
| `references/error-patterns.md` | CRITICAL/HIGH/MEDIUM/LOW pattern definitions |
| `references/conversation-patterns.md` | User frustration patterns |
| `references/git-context-integration.md` | Git context integration docs |

### Infrastructure

| File/Dir | Purpose |
|----------|---------|
| `.evidence/` | Subagent artifacts (gap_finder_*.md, git_context_*.md, health_*.md) |
| `.state/` | Terminal-scoped state (checklist, session flags) |
| `.claude/state/sessions/` | Intent state tracking |
| `hooks/` | PostToolUse, Stop, SessionEnd hooks |
| `tests/` | Integration tests |
| `examples/` | Usage examples |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Context Protection**: Subagents write artifacts, return lightweight envelopes
2. **Multi-Terminal Safety**: Terminal-scoped state, shared git repo (read-only)
3. **Graceful Degradation**: Missing git, malformed transcripts don't crash
4. **Non-Blocking Hooks**: All hooks are advisory (warnings only)

### Technology Constraints

- **Python 3.14** as main language
- **GitPython optional** (graceful degradation if missing)
- **Stdlib-only** for core functionality (no external deps required)
- **Local-only** (no network calls, multi-terminal safe)

### Things That Must NOT Change

1. **Subagent envelope pattern** - Protects orchestrator context
2. **Multi-terminal isolation** - Terminal-scoped state directories
3. **Non-blocking hooks** - Never block user workflow
4. **Handoff chain traversal** - Critical for context across sessions
5. **Git repo as shared source** - Safe for multi-terminal (read-only)

---

## 6. KNOWN ISSUES

### Issue 1: No Recommended Next Steps Generation

**Scenario**: SKILL.md specifies Recommended Next Steps template format (lines 690-842), but current implementation doesn't generate them.

**Expected**:
```
**Recommended Next Steps**
1 - Commit uncommitted files
- 1a: Stage modified files
- 1b: Commit with descriptive message

0 - Do ALL Recommended Next Steps
```

**Actual**: `print_compact_snapshot()` outputs only:
```
=== GTO SNAPSHOT ===
- Status: ✅ Health 85/100, 2 gaps found
- Git: dirty
```

**Impact**: HIGH - Core feature documented but not implemented

**Workaround**: None (feature missing)

**Root cause**: Implementation gap - Claude (orchestrator) should format findings into template, but doesn't

### Issue 2: GapFinder Has No Line Number Validation

**Scenario**: GapFinderSubagent detects errors but doesn't capture file paths or line numbers.

**Expected**: `### SKILL.md:42 - ImportError detected`

**Actual**: `### Turn 42: import_error` (no file path, no line number)

**Impact**: MEDIUM - Harder to investigate issues without location

**Workaround**: Read full artifact and search manually

### Issue 3: Learning Opportunity Detection Not Implemented

**Scenario**: SKILL.md mentions learning opportunities (lines 253-268, 867, 889), suggests `/learn` or `/reflect` as next steps.

**Expected**: Detect learning patterns and suggest /learn or /reflect

**Actual**: No code detects learning opportunities

**Impact**: LOW - Documented feature, never implemented

**Workaround**: Manual recognition of learning moments

### Issue 4: Documentation/Code Mismatch

**Scenario**: SKILL.md describes features that don't exist in code

**Examples**:
- Learning opportunity detection (documented, not implemented)
- Recommended Next Steps format (documented, not generated)
- "Did You Forget Anything?" checklist (documented, partially implemented)

**Impact**: LOW - Misleading documentation

**Workaround**: Read code to verify capabilities

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### 1. Add New Gap Detection Pattern

**Location**: `lib/subagents.py`, `GapFinderSubagent`

**Pattern definitions**:
```python
CRITICAL_PATTERNS = [
    (r"ImportError.*No module named", "import_error"),
    # Add new patterns here
]
```

**Invocation**: Automatic on next /gto run

#### 2. Add New Health Category

**Location**: `health_scoring.py`, `HealthScoringEngine`

**Category weights**:
```python
CATEGORY_WEIGHTS = {
    "tests": 0.30,
    "documentation": 0.20,
    "git": 0.20,
    "dependencies": 0.15,
    "code_quality": 0.15,
    # Add new category here (ensure sum = 1.0)
}
```

**Categorization**: Update `_categorize_gaps()` to map gaps to new category

#### 3. Add Recommended Next Steps Generator

**Location**: NEW module or add to `gto_orchestrator.py`

**Interface**:
```python
def format_recommended_next_steps(results: dict) -> str:
    """Format findings into Recommended Next Steps template."""
    # Read artifacts
    # Parse gaps by severity
    # Generate domain-organized next steps
    # Return formatted markdown
```

**Invocation**: Call from `print_compact_snapshot()` or add new mode

#### 4. Add Line Number Capture

**Location**: `lib/subagents.py`, `GapFinderSubagent._detect_tool_errors()`

**Change**: Parse error output for file:line patterns

**Example**:
```python
def _extract_error(self, output: str) -> tuple[str, str | None, int | None]:
    """Extract (message, file_path, line_number) from output."""
    # Parse "File 'path', line N" patterns
    # Return tuple with location info
```

#### 5. Add Learning Opportunity Detection

**Location**: NEW subagent or add to `GapFinderSubagent`

**Pattern**: Detect phrases like "I learned", "Now I understand", "That's interesting"

**Integration**: Add learning gaps to gap list, suggest `/learn` or `/reflect` in next steps

### Data Exchange Contracts

#### Subagent → Orchestrator

```python
{
    "status": "done" | "blocked" | "retry",
    "artifact": ".evidence/gap_finder_console_20260321_123456.md",
    "summary": "Found 8 gaps: 2 critical, 3 high",
    "metrics": {
        "gaps_found": 8,
        "critical": 2,
        "high": 3,
        # ... additional metrics
    }
}
```

#### Orchestrator → Artifact

**Format**: Markdown with structured sections

**Example** (gap_finder artifact):
```markdown
# Gap Analysis

## Critical Gaps (2)

### Turn 42: import_error
ImportError: No module named 'requests' occurred during pip install

## High Gaps (3)

### Turn 17: test_failure
test_auth.py::test_login failed - AssertionError
```

### Output/Exit Code Expectations

- **Exit code 0**: Success (even if gaps found)
- **Exit code 1**: Error condition (transcript not found, fatal error)
- **Stdout**: Structured markdown (compact or verbose format)
- **Stderr**: Progress messages (chain discovery, subagent execution)

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample Run: Compact Mode

```
$ python gto_orchestrator.py --terminal-id console
🔗 Discovered 1 session(s) in handoff chain
  1. a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl
🔍 Detecting gaps in session scope across 1 session(s)...
  [1/1] Analyzing a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl...
🌳 Checking git context...
💓 Calculating health score...

=== GTO SNAPSHOT ===
- Sessions analyzed: 1
- Status: ✅ Health 85/100, 2 gaps found
- Git: clean

**Transcript Chain:**
  1. a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl

**Detailed Analysis Artifacts:**
- Gaps: .evidence/gap_finder_console_20260321_123456.md
- Git: .evidence/git_context_console_20260321_123456.md
- Health: .evidence/health_console_20260321_123456.md
```

### Sample Run: Verbose Mode

```
$ python gto_orchestrator.py --terminal-id console --verbose
🔗 Discovered 1 session(s) in handoff chain
  1. a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl
🔍 Detecting gaps in session scope across 1 session(s)...
  [1/1] Analyzing a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl...
🌳 Checking git context...
💓 Calculating health score...

=== GTO SNAPSHOT ===
- Sessions analyzed: 1
- Status: ✅ Health 85/100, 2 gaps found
- Git: clean

**Transcript Chain:**
  1. a8dd496e-cc6d-4503-91f3-be60b41f4ac5.jsonl

**Detailed Analysis Artifacts:**
- Gaps: .evidence/gap_finder_console_20260321_123456.md
- Git: .evidence/git_context_console_20260321_123456.md
- Health: .evidence/health_console_20260321_123456.md

**Gap Details:**
# Gap Analysis

## Critical Gaps (1)

### Turn 42: import_error
ImportError: No module named 'requests' occurred during package installation

## High Gaps (1)

### Turn 17: test_failure
test_auth.py::test_login failed - AssertionError: Expected 200, got 401

... (truncated, see artifact for full details)
```

### Sample Artifact: health_*.md

```markdown
# Health Score Analysis

**Overall Score**: 85/100

**Recommendation**: Good health - address high-priority gaps when convenient

## Score Breakdown

- **Tests**: 80/100 (weight: 0.3, gaps: 1)
- **Documentation**: 100/100 (weight: 0.2, gaps: 0)
- **Git**: 100/100 (weight: 0.2, gaps: 0)
- **Dependencies**: 100/100 (weight: 0.15, gaps: 0)
- **Code Quality**: 70/100 (weight: 0.15, gaps: 1)

**Total Gaps**: 2
**Critical Gaps**: 1
**High Gaps**: 1
```

### Sample Artifact: git_context_*.md

```markdown
# Git Context

**Repository**: P:\.claude\skills\gto
**Branch**: main
**Status**: clean

## Modified Files
(no modified files)

## Recent Commits

- e81a2508bd feat(chs): merge feature/chs-consolidation branch
- 5b0d61f617 feat(chs): ATOMIC COMMIT 3 - Remove sys.path manipulation
- 32fc60097c feat(chs): ATOMIC COMMIT 2 - Update all import paths
- 7853d033ea feat(chs): atomic migration - move CHS core
- 89b8f447b7 feat(hooks): add E2E test for [SEQ] tag

**Development Activity**: HIGH
```

---

## END OF REVIEW BUNDLE

This bundle provides comprehensive context for:
- Understanding /gto architecture and data flow
- Identifying integration points for new features
- Diagnosing issues and planning improvements
- Onboarding new developers to the /gto skill system

**Next steps**:
1. Review Known Issues section for priority improvements
2. Use Integration Points section for adding new features
3. Refer to Component Inventory for file locations
4. Follow Execution Sequence for debugging workflows
