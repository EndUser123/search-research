# Review Bundle: /planning Skill

**Generated**: 2026-03-21
**Scope**: `P:\.claude\skills\planning/`
**Core File Count**: ~30 files (excluding cache/state)
**Execution Mode**: Single-agent (well-scoped, defined boundaries)

---

## 1. PROJECT CONTEXT

### Domain & Purpose
The `/planning` skill creates and verifies implementation plans with automatic quality checks. It is ADR-aware, creating separate plan artifacts for Architecture Decision Records. The skill enforces solo-dev constraints, validates plan structure, and orchestrates adversarial review via parallel subagent dispatch.

### Scale Metrics
- **LOC**: ~3,500 lines (core: auto_verify.py ~1,300 lines, state_manager ~400 lines, adr_path_mapper ~200 lines)
- **Major subsystems**: 4 (verification, state management, ADR handling, auto-fix)
- **Deployment scope**: Claude Code skill (local execution only)
- **Change frequency**: Active development (recent task completeness checks added)

### Your Environment
- **OS**: Windows 11 Pro (WSL/git bash compatible)
- **Languages**: Python 3.14
- **Frameworks**: pytest for testing, standard library only (no external deps for core logic)
- **Build tools**: None (direct Python execution)

---

## 2. ARCHITECTURE OVERVIEW

```
User Input (topic or ADR path)
        ↓
┌─────────────────────────────────────────────────────────────┐
│                    SKILL ENTRY POINT                         │
│  Claude parses SKILL.md workflow_steps                       │
│  - detect_input_type (ADR vs topic)                          │
│  - detect_topic (conversation history)                        │
│  - build_plan                                                │
│  - run_verification                                         │
│  - auto_fix                                                  │
│  - adversarial_review (6 parallel agents)                    │
│  - present_results                                          │
└─────────────────────────────────────────────────────────────┘
        ↓                       ↓
┌──────────────────┐    ┌──────────────────────────────────────┐
│  adr_path_mapper  │    │        plan_state_manager            │
│  - ADR detection  │    │  - Terminal-scoped state files      │
│  - Plan path gen  │    │  - Multi-terminal collision prevent  │
└──────────────────┘    │  - Session boundary detection       │
        └───────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    auto_verify.py                            │
│  1. Format detection & normalization (ADR → canonical plan)   │
│  2. Section completeness check (7 required sections)          │
│  3. Solo-dev violations (team coordination patterns)          │
│  4. Implementation completeness (doc → impl ratio)             │
│  5. Task sequencing gaps (doc before impl)                    │
│  6. Consumer impact (deprecation migration strategy)         │
│  7. Task completeness (impl details, output formats)          │
│  8. RTM coverage (requirements → tasks mapping)                │
│                                                              │
│  Output: <plan>.review.result.json                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    auto_fix.py                               │
│  - Add missing sections                                       │
│  - Rename to canonical names                                  │
│  - Write back to plan file                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────┬─────────┬─────────┬─────────┬─────────┐
        ↓         ↓         ↓         ↓         ↓         ↓
    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
    │comply│ │logic │ │test │ │security│ │failure│ │critic│
    │iance│ │      │ │     │ │       │ │_modes│ │      │
    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
    (6 adversarial subagents via Agent tool - PARALLEL)
        │         │         │         │         │         │
        └─────────┴─────────┴─────────┴─────────┴─────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              format_findings.py (output formatter)              │
│  - Aggregate findings                                       │
│  - Generate GTO-style Recommended Next Actions               │
│  - Priority grouping (HIGH/MEDIUM/LOW)                        │
└─────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. Verification Engine (`auto_verify.py`)
- **Purpose**: Deterministic plan validation before adversarial review
- **Files**: `__lib/auto_verify.py`
- **Entry Point**: `verify_plan(plan_path: str) -> dict`
- **Dependencies**: None (stdlib only)
- **Output**: `<plan_path>.review.result.json` with findings list
- **Critical Invariants**:
  - Always returns valid JSON with `status`, `action_items`, `summary` keys
  - Finds are written to disk before adversarial review

#### 2. State Management (`plan_state_manager.py`)
- **Purpose**: Multi-terminal isolation, crash recovery, session boundaries
- **Files**: `__lib/plan_state_manager.py`
- **Entry Point**: `PlanStateManager` class with `load_state()`, `save_state()`, `cleanup_state()`
- **Dependencies**: `hook_base.get_terminal_id()` (fallback to WT_SESSION env var)
- **State Location**: `~/.claude/hooks/state/pr_workflow_{terminal_id}.json`
- **Critical Invariants**:
  - State files scoped to terminal ID (prevents collision)
  - Max age: 24 hours (stale state rejected)
  - Cleanup on workflow completion

#### 3. ADR Path Mapper (`adr_path_mapper.py`)
- **Purpose**: Detect ADR files, generate plan paths, extract metadata
- **Files**: `__lib/adr_path_mapper.py`
- **Key Functions**: `is_adr_file()`, `get_plan_path_for_adr()`, `extract_adr_identifier()`
- **ADR Patterns**: `ADR-XXX`, `XXX-title`, `arch_decisions/`, content headers
- **Plan Output**: `~/.claude/plans/plan-adr-XXX-title.md`
- **Critical Invariants**: ADR files are NEVER modified in-place

#### 4. Auto-Fix (`auto_fix.py`)
- **Purpose**: Automatically correct structural plan issues
- **Files**: `__lib/auto_fix.py`
- **Entry Point**: `fix_plan(plan_path: str) -> dict`
- **Operations**: Add missing sections, rename to canonical names
- **Returns**: `{"status": "FIXED"|"NO_FIXES_NEEDED", "fixes_applied": [...], "sections_added": [...]}`
- **Critical Invariants**: Writes back to original plan file (destructive)

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Topic-based workflow** (user provides topic like "implement X"):
```
1. SKILL.md invoked → Claude creates plan document
2. auto_verify.py runs → produces .review.result.json
3. auto_fix.py runs → fixes structural issues
4. Claude dispatches 6 adversarial agents in PARALLEL via Agent tool
5. format_findings.py aggregates results → displays GTO-style actions
6. User selects actions → Claude applies improvements
```

**ADR-based workflow** (user provides ADR path):
```
1. adr_path_mapper detects ADR → generates plan path
2. auto_verify.py normalizes ADR → canonical plan format
3. (same as topic workflow from step 2)
```

**Context-aware workflow** (no argument provided):
```
1. Detect most recent plan from ~/.claude/plans/*.md
2. Check verification status → skip if already complete
3. Check multi-terminal lock → wait or use different plan
4. Resume from appropriate phase
```

### State Management

**State File Schema** (`pr_workflow_{terminal_id}.json`):
```json
{
  "plan_path": "path/to/plan.md",
  "status": "IN_PROGRESS"|"VERIFIED"|"ADVERSARIAL_REVIEW_COMPLETE",
  "completed_phases": [0, 1, 2, ...],
  "terminal_id": "unique_terminal_identifier",
  "session_start_ts": 1234567890,
  "last_update_ts": 1234567890
}
```

**Isolation Boundaries**:
- Each terminal gets isolated state directory
- State files scoped to terminal ID (not session)
- Session boundary detection via `session_start_ts` field

### Error Handling

**Fail-open vs fail-closed**:
- **Verification**: Fail-open (continues with findings even if checks error)
- **State manager**: Fail-closed (rejects stale/corrupted state)
- **ADR detection**: Fail-open (treats unrecognized as topic-based plan)

**Retry behavior**:
- No automatic retries (single-pass verification)
- State manager validates age before loading (no retry for stale state)

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Key Functions/Classes | Responsibility | Inputs | Outputs | Known Limitations |
|------|----------------------|---------------|---------|---------|-------------------|
| `auto_verify.py` | `verify_plan()`, `check_section_completeness()`, `check_solo_dev_violations()`, `check_rtm_coverage()`, `check_task_completeness()` | 8-check validation pipeline | Plan path string | JSON result with findings | Requires canonical plan format (normalizes ADR first) |
| `plan_state_manager.py` | `PlanStateManager.load_state()`, `save_state()`, `cleanup_state()` | Terminal-scoped state management | None (reads terminal ID from env/hook_base) | State dict | Fallback to PID/timestamp if hook_base unavailable |
| `adr_path_mapper.py` | `is_adr_file()`, `get_plan_path_for_adr()`, `extract_adr_identifier()` | ADR detection and path generation | File path | Boolean / Plan path | Limited to ADR filename patterns (content check fallback) |
| `auto_fix.py` | `fix_plan()`, `add_missing_sections()` | Automatic structural corrections | Plan path string | Fix result dict | Destructive (overwrites original file) |
| `format_findings.py` | `format_recommended_actions()` | GTO-style output formatting | Findings list | Markdown string | Not used by core skill (helper utility) |

### Utilities/Helpers

| File | Purpose |
|------|---------|
| `cleanup.py` | Cleanup utility for old state files |
| `state_manager.py` | Generic state management (imported by plan_state_manager) |

### Configuration

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition, workflow steps, triggers |
| `FINDINGS_SCHEMA.md` | Findings JSON schema documentation |

### Test Files

| File | Coverage |
|------|----------|
| `test_auto_fix.py` | Auto-fix behavior (32 tests) |
| `test_auto_verify_new_checks.py` | New verification checks (25 tests) |
| `test_planning_integration.py` | End-to-end workflow (8 tests) |
| `test_adversarial_review_coordinator.py` | Adversarial agent coordination (BROKEN - missing module) |
| `test_plan_update_coordinator.py` | Plan updates (BROKEN - missing module) |
| `test_rtm.py` | RTM coverage validation |
| `test_markdown_summary.py` | Markdown output formatting |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Claude as Orchestrator**: Claude calls tools, manages workflow, dispatches agents. Tools do NOT orchestrate themselves.
2. **ADR Immutability**: ADR files are NEVER modified in-place. Separate plan artifacts are created.
3. **Terminal Isolation**: Each terminal gets isolated state to prevent multi-terminal collision.
4. **Parallel Adversarial Review**: All 6 adversarial agents dispatched in ONE message via Agent tool.

### Technology Constraints
- **No external dependencies**: Core verification uses Python stdlib only
- **File-based state**: State stored in JSON files (not databases)
- **Markdown format**: Plans use GitHub Flavored Markdown

### Performance SLAs
- **Verification**: <2 seconds for typical plans
- **Auto-fix**: <1 second for structural corrections
- **State cleanup**: Automatic on workflow completion

### Things That Must NOT Change
- **ADR modification prohibition**: Never write to ADR files
- **Parallel agent dispatch**: Adversarial agents must be dispatched in single message, not sequentially
- **Findings schema**: All findings must include `id`, `category`, `priority`, `title`, `description`, `recommendation`
- **Terminal-scoped state**: State files must be scoped to terminal ID, not session ID

---

## 6. KNOWN ISSUES

### High Impact

| Issue | Expected vs Actual | Impact | Workaround |
|-------|------------------|--------|------------|
| `test_adversarial_review_coordinator.py` imports missing module | ImportError: `No module named '__lib.adversarial_review_coordinator'` | Test cannot run | Skip this test file |
| `test_plan_update_coordinator.py` imports missing module | ImportError: `No module named 'plan_update_coordinator'` | Test cannot run | Skip this test file |

### Medium Impact

| Issue | Expected vs Actual | Impact | Workaround |
|-------|------------------|--------|------------|
| TASK-005 file creation check too permissive | "Create reference files" with "for" passes content check | May miss missing content specifications | None currently (documented in test) |
| State cleanup not automatic in all exit paths | State files may accumulate if workflow interrupted | Manual cleanup needed | Run `cleanup.py` periodically |

### Low Impact

| Issue | Expected vs Actual | Impact | Workaround |
|-------|------------------|--------|------------|
| No integration test for adversarial agent dispatch | Adversarial agents not tested in integration | Adversarial coordination may have bugs | Manual testing only |

---

## 7. INTEGRATION POINTS

### Adding New Verification Checks
**Location**: `__lib/auto_verify.py` (check functions)
**Pattern**:
```python
def check_new_category(plan: str) -> list[dict[str, Any]]:
    findings = []
    # ... validation logic ...
    if issue_detected:
        findings.append({
            "id": "PREFIX-001",
            "category": "category_code",
            "priority": "HIGH",
            "title": "Short description",
            "description": "Full details",
            "recommendation": "Fix action"
        })
    return findings
```
**Integration**: Add to `all_findings.extend(check_new_category(plan))` in `verify_plan()`

### Adding New Adversarial Agents
**Location**: `.claude/agents/` (agent definitions)
**Invocation**: Via Agent tool in SKILL.md workflow
**Contract**: Agent must return findings matching FINDINGS_SCHEMA.md format

### State Extension
**Location**: `__lib/plan_state_manager.py` (PlanStateManager class)
**Pattern**: Add new fields to state dict, update validation if needed

### Output Formatting
**Location**: `__lib/format_findings.py`
**Usage**: Call `format_recommended_actions(findings)` to generate GTO-style output

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Successful Verification Run
```bash
$ python .claude/skills/planning/__lib/auto_verify.py test-plan.md
# Output: test-plan.review.result.json created
{
  "status": "FINDINGS",
  "action_items": [
    {
      "id": "TASK-001",
      "category": "task_completeness",
      "priority": "HIGH",
      "title": "Missing implementation details: TASK-001",
      "description": "Task 'Implement ViabilityGate' mentions implementing code but lacks specific details...",
      "recommendation": "Add: 'Add XClass to filename.py' or 'Implement function_name() in module.py'"
    }
  ],
  "summary": {
    "total_findings": 1,
    "high_priority": 1,
    "requirements_found": 0,
    "tasks_found": 1
  }
}
```

### State File Example
```json
{
  "plan_path": "P:\\.claude\\plans\\test-plan.md",
  "status": "VERIFIED",
  "completed_phases": [0, 1],
  "terminal_id": "wt_0123456789ab",
  "session_start_ts": 1742553600,
  "last_update_ts": 1742553650
}
```

### Test Results (2026-03-21)
```
test_auto_fix.py: 32 passed
test_auto_verify_new_checks.py: 25 passed
test_planning_integration.py: 8 passed
Total: 65 passed
```

---

## 9. FILE MANIFEST

### Core Files (Production)
```
P:\.claude\skills\planning\
├── SKILL.md                           # Skill definition
├── FINDINGS_SCHEMA.md                  # Findings schema documentation
├── __lib/
│   ├── __init__.py
│   ├── auto_verify.py                  # Main verification engine (8 checks)
│   ├── auto_fix.py                     # Auto-fix structural issues
│   ├── adr_path_mapper.py              # ADR detection & path generation
│   ├── plan_state_manager.py           # Terminal-scoped state management
│   ├── state_manager.py                # Generic state utilities
│   ├── cleanup.py                      # State cleanup utility
│   └── format_findings.py              # Output formatting helper
└── tests/
    ├── test_auto_fix.py                # Auto-fix tests (32 tests)
    ├── test_auto_verify_new_checks.py # New verification tests (25 tests)
    ├── test_planning_integration.py    # Integration tests (8 tests)
    ├── test_rtm.py                     # RTM coverage tests
    ├── test_markdown_summary.py        # Output formatting tests
    └── [other test files]              # See Component Inventory
```

### State Directories
```
~/.claude/
├── hooks/state/
│   └── pr_workflow_{terminal_id}.json  # Terminal-scoped state
├── plans/
│   └── plan-adr-XXX-title.md           # ADR-generated plans
└── state/
    └── sessions/                       # Session-specific state
```

---

**END OF REVIEW BUNDLE**
