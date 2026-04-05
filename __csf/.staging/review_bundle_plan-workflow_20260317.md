# Review Bundle: /plan-workflow Skill

**Generated**: 2026-03-17
**Scope**: `P:/.claude/skills/plan-workflow/`
**File Count**: 49 files (excluding cache)
**Execution Mode**: 2-agents (10-50 files range)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: plan-workflow
- **Version**: 2.14.0
- **Category**: planning
- **Primary Directory**: `P:/.claude/skills/plan-workflow/`

### Domain & Purpose
Build and verify implementation plans with automatic quality checks. Enforces plan mode (editing restrictions), runs adversarial review (8-agent pipeline), tracks review state through phases 0-7, and validates requirements traceability. Critical for preventing premature implementation before plan completion.

### Scale Metrics
- **LOC**: ~8,000+ Python (core) + ~3,000 tests
- **Major Subsystems**: 6 (hooks, lib/validators, lib/visualizers, state tracking, adversarial coordination, test suite)
- **Deployment Scope**: Claude Code skill (global hooks)
- **Change Frequency**: Active (recent updates: RTM enforcer, quality calibration, semantic RTM validation)

### Your Environment
- **OS**: Windows 11
- **Shell**: bash (Git Bash/WSL)
- **Languages**: Python 3.12+, Markdown
- **Key Dependencies**: jsonschema, pathlib, re, dataclasses
- **External Services**: None (local hooks)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    /plan-workflow Skill                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐    ┌──────────────────────────────────────┐  │
│  │   SKILL.md    │    │       Hook Registration               │  │
│  │  (Frontmatter)│    │  (settings.json + hooks/             │  │
│  │               │    │   UserPromptSubmit, PreToolUse,      │  │
│  │  Triggers:    │    │   PostToolUse, Stop)                 │  │
│  │  - /plan-work │    │                                      │  │
│  │  - "plan for" │    │  ┌─────────────────────────────────┐  │  │
│  │  - "implement"│    │  │   PreToolUse_plan_mode_guard    │  │  │
│  └───────┬───────┘    │  │   Blocks Edit/Write during      │  │  │
│          │            │  │   plan mode (only plan file)    │  │  │
│          │            │  └─────────────────────────────────┘  │  │
│          ▼            │                                      │  │
│  ┌───────────────┐    │  ┌─────────────────────────────────┐  │  │
│  │   Inline      │    │  │ UserPromptSubmit_plan_topic_guard│ │  │
│  │   Execution   │    │  │ Detects topic switch during     │  │  │
│  │   (Plan       │    │  │ active plan (keyword overlap)   │  │  │
│  │    Mode)      │    │  └─────────────────────────────────┘  │  │
│  └───────────────┘    │                                      │  │
│                       │  ┌─────────────────────────────────┐  │  │
│                       │  │PostToolUse_plan_review_tracker  │  │  │
│                       │  │Tracks phases 0-7, detects HALT  │  │  │
│                       │  │Validates quality gates per phase│  │  │
│                       │  └─────────────────────────────────┘  │  │
│                       │                                      │  │
│                       │  ┌─────────────────────────────────┐  │  │
│                       │  │StopHook_plan_completion_gate   │  │  │
│                       │  │Blocks narrative early exit     │  │  │
│                       │  │Requires all phases executed    │  │  │
│                       │  └─────────────────────────────────┘  │  │
│                       └──────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    lib/ (Core Modules)                      ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                               ││
│  │  ┌──────────────────┐  ┌──────────────────┐                ││
│  │  │  auto_verify.py  │  │ rtm_enforcer.py  │                ││
│  │  │  - verify_plan() │  │  - RTMEnforcer   │                ││
│  │  │  - auto_fix_plan│  │  - Gap detection │                ││
│  │  │  - Structure V  │  │  - Orphan reqs   │                ││
│  │  │  - Solo-dev V   │  │  - Missing AC    │                ││
│  │  └──────────────────┘  └──────────────────┘                ││
│  │                                                               ││
│  │  ┌──────────────────────────────┐  ┌──────────────────────┐ ││
│  │  │ adversarial_review_coordinator│  │ plan_update_prompts  │ ││
│  │  │  - 8-agent orchestration     │  │  - Gap resolution    │ ││
│  │  │  - Quality calibration       │  │  - Opportunity impl.  │ ││
│  │  │  - Low-value filtering       │  │  - Subagent routing   │ ││
│  │  │  - Targeted context extract  │  │                      │ ││
│  │  └──────────────────────────────┘  └──────────────────────┘ ││
│  │                                                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    State & Persistence                      ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  ~/.claude/plans/*.md               (Active plan file)       ││
│  │  ~/.claude/hooks/state/pr_workflow.json (Review progress)   ││
│  │  <plan>.review.result.json         (Verification output)    ││
│  │  ~/.claude/state/policy_gate/      (Intent analysis cache)  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. Plan Mode Guard (PreToolUse)
- **Purpose**: Enforce separation between planning and implementation
- **Files**: `hooks/PreToolUse_plan_mode_guard.py`
- **Entry Point**: Hook intercepts Edit/Write tool calls
- **Dependencies**: `~/.claude/plans/` directory (plan file existence)
- **Invariants**: Only plan file editable when plan mode active

#### 2. Topic Guard (UserPromptSubmit)
- **Purpose**: Prevent mixing unrelated topics into active plan
- **Files**: `hooks/UserPromptSubmit_plan_topic_guard.py`
- **Entry Point**: Hook intercepts user prompts
- **Dependencies**: Plan file topic extraction (first line)
- **Invariants**: <30% keyword overlap triggers warning

#### 3. Review State Tracker (PostToolUse)
- **Purpose**: Track 8-phase review pipeline execution
- **Files**: `hooks/PostToolUse_plan_review_state_tracker.py` (v2.0, ~1600 LOC)
- **Entry Point**: Hook intercepts Bash/Task/Skill tool results
- **Dependencies**: `~/.claude/hooks/state/pr_workflow.json`
- **Invariants**: Phase 0-7 sequence, HALT detection, quality gates

#### 4. Completion Gate (StopHook)
- **Purpose**: Block narrative early exit without execution
- **Files**: `hooks/StopHook_plan_review_completion_gate.py`
- **Entry Point**: Hook intercepts response before session end
- **Dependencies**: `pr_workflow.json` completed_phases list
- **Invariants**: All required phases must execute before completion claim

#### 5. Auto Verify (lib/)
- **Purpose**: Run format validation + structure checks
- **Files**: `lib/auto_verify.py`, `lib/rtm_enforcer.py`
- **Entry Point**: Called from skill inline code
- **Dependencies**: Plan content, plan_visualizer
- **Invariants**: Auto-fix applied before validation

#### 6. Adversarial Coordinator (lib/)
- **Purpose**: Orchestrate 8-agent review pipeline
- **Files**: `lib/adversarial_review_coordinator.py`
- **Entry Point**: Called from skill via Agent tool
- **Dependencies**: 8 adversarial subagent types
- **Invariants**: Phase 1 (parallel) → Phase 2 (critic) sequence

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Plan Mode Entry**:
```
User: "create a plan for X"
  → EnterPlanMode tool (built-in)
  → Creates ~/.claude/plans/plan-<session>.md
  → PreToolUse_plan_mode_guard activates
  → All Edit/Write blocked except plan file
```

**Plan Review Pipeline**:
```
/plan-workflow or /plan-review <plan>
  → Phase 0: Auto-fix format issues
  → Phase 0.5: Codebase consistency check
  → Phase 1: Structure validation
  → Phase 2: Dependency validation
  → Phase 3: Test coverage analysis
  → Phase 4: Adversarial review (8 agents)
  → Phase 5: RTM validation
  → Phase 6: Final status determination
  → Phase 7: Task breakdown (if READY-FOR-IMPLEMENTATION)
  → Writes <plan>.review.result.json
```

**Adversarial Review (2-Phase)**:
```
Phase 1: Parallel execution
  → adversarial-compliance
  → adversarial-performance
  → adversarial-quality
  → adversarial-security
  → adversarial-testing
  → code-critic
  → qa-engineer
  → Each writes JSON to ~/.claude/state/

Phase 2: Meta-analysis (after Phase 1 completes)
  → adversarial-critic reads 7 JSON files
  → Quality calibration (confidence adjustments)
  → Consensus/blind spot detection
```

### State Management

**State Files**:
- `~/.claude/plans/*.md` - Active plan (created by EnterPlanMode)
- `~/.claude/hooks/state/pr_workflow.json` - Review progress
- `<plan>.review.result.json` - Verification output
- `~/.claude/state/policy_gate/<session>/analysis_cache.json` - Intent cache

**State Schema** (pr_workflow.json):
```json
{
  "plan_path": "path/to/plan.md",
  "plan_checksum": "sha256",
  "completed_phases": [0, 1, 2, 3, 4, 5, 6],
  "halt_phase": null,
  "status": "READY-FOR-IMPLEMENTATION",
  "quality_gates": {...}
}
```

### Error Handling

**Fail-Open Policy** (hooks):
- Invalid JSON → allow
- Plan file missing → allow
- State file corruption → allow (reset on Phase 0)

**Fail-Closed Policy** (completion gate):
- Missing phases → block
- HALT detected → block
- No result file → warn

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Key Functions | Responsibility | Inputs/Outputs |
|------|---------------|----------------|----------------|
| `hooks/PreToolUse_plan_mode_guard.py` | `main()`, `is_plan_mode_active()` | Block non-plan edits during plan mode | Tool payload → continue(bool) |
| `hooks/UserPromptSubmit_plan_topic_guard.py` | `calculate_overlap()`, `extract_plan_topic()` | Detect topic switch | User prompt → injection |
| `hooks/PostToolUse_plan_review_state_tracker.py` | `detect_phase()`, `update_state()`, `check_quality_gates()` | Track review progress, validate gates | Tool result → state update |
| `hooks/StopHook_plan_review_completion_gate.py` | `main()` | Block narrative early exit | Response → block/allow |
| `lib/auto_verify.py` | `verify_plan()`, `auto_fix_plan()` | Format validation, auto-fix | Plan content → result dict |
| `lib/rtm_enforcer.py` | `RTMEnforcer.validate()` | Requirements traceability | RTM dict → validation result |
| `lib/adversarial_review_coordinator.py` | `run_subagent_review()`, `extract_targeted_context()` | Orchestrate 8-agent review | Plan → filtered findings |
| `lib/plan_update_prompts.py` | `generate_gap_update_prompt()` | Generate prompts for plan updates | Finding → prompt string |

### Validators

| File | Responsibility |
|------|----------------|
| `lib/section_validator.py` | Validate section numbering (##, ###) |
| `lib/algorithmic_gate.py` | Validate algorithmic specifications |
| `lib/testability_gate.py` | Validate testability of tasks |
| `lib/api_completeness.py` | Check API completeness |
| `lib/consistency_checker.py` | Codebase consistency checks |
| `lib/security_verification.py` | Security verification |
| `lib/verify_command_validator.py` | Validate /verify command |
| `lib/context_inference.py` | Infer context from plan |

### Configuration

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill frontmatter, workflow steps, hook registration |
| `.claude/` | Local state (sessions, policy gate cache) |
| `tests/conftest.py` | Pytest fixtures |

### Infrastructure

| File | Purpose |
|------|---------|
| `hooks/__lib/hook_base.py` | Hook decorator `@hook_main` |
| `lib/__init__.py` | Lib package exports |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Separation of Concerns**: Planning vs Implementation enforced by PreToolUse guard
2. **Evidence-Based Review**: All findings must reference plan content
3. **Multi-Agent Verification**: 8 adversarial perspectives reduce blind spots
4. **State Persistence**: Review progress survives Claude restarts

### Technology Constraints
- **Python 3.12+**: Type hints required
- **Hooks**: stdin/stdout JSON protocol (Claude Code contract)
- **No external deps**: jsonschema is only external dependency
- **Windows + Unix**: Must run on both (path handling)

### Performance SLAs
- **Hook latency**: <500ms for guards (PreToolUse, UserPromptSubmit)
- **State tracker**: <2s for PostToolUse (large plan handling)
- **Review pipeline**: 5-30s (8-agent parallel execution)

### Things That Must NOT Change
1. **Plan file location**: `~/.claude/plans/` (hard-coded in multiple hooks)
2. **Phase sequence**: 0→7 order is mandatory
3. **State file schema**: Backward compatibility required
4. **Hook registration**: UserPromptSubmit, PreToolUse, PostToolUse, Stop
5. **Fail-open for guards**: Invalid input must allow (not block)

---

## 6. KNOWN ISSUES

| Issue | Expected | Actual | Impact | Workaround |
|-------|----------|--------|--------|------------|
| Circular import (plan_visualizer) | Clean import | Import at end of auto_verify.py | Test isolation issues | Import inline in function |
| Hook timeout on large plans | <10s | Sometimes exceeds | Hook may be killed | Reduce plan size before review |
| State corruption on crash | Valid JSON | Sometimes truncated | Review restart required | Delete pr_workflow.json manually |
| Adversarial critic not finding JSON files | JSON in ~/.claude/state/ | "No findings" | Calibration skipped | Ensure phase 1 agents write files |

---

## 7. INTEGRATION POINTS

### Existing Hooks
```
UserPromptSubmit → UserPromptSubmit_plan_topic_guard
PreToolUse → PreToolUse_plan_mode_guard
PostToolUse → PostToolUse_plan_review_state_tracker
Stop → StopHook_plan_review_completion_gate
```

### Invocation Model
```
User: "/plan-workflow" or "create a plan for X"
  → EnterPlanMode tool (built-in)
  → Skill inline code execution
  → Edit plan file (only file allowed)
  → /finalize to exit plan mode
```

### Data Exchange Contracts
**Hook Input** (stdin):
```json
{
  "tool_name": "Edit|Write",
  "tool_input": {"file_path": "..."},
  "prompt": "user message",
  "response": "assistant response"
}
```

**Hook Output** (stdout):
```json
{
  "continue": true|false,
  "reason": "block message",
  "hookSpecificOutput": {
    "additionalContext": "injection text"
  }
}
```

### Output Expectations
- **Plan file**: Markdown with ## sections
- **Result JSON**: `<plan>.review.result.json` with status, action_items, statistics
- **State JSON**: `pr_workflow.json` with completed_phases, status

---

## 8. APPENDIX: KEY FILES

### Test Files
- `tests/test_opt_out_flags.py` - Bypass flag tests
- `tests/test_plan_update_integration.py` - Update workflow tests
- `tests/test_rtm.py` - RTM validation tests
- `tests/test_auto_verify_rtm_integration.py` - RTM integration tests
- `tests/test_state_schema_validation.py` - State schema tests
- `tests/test_plan_topic_guard_validation.py` - Topic guard tests

### Plan Files (Internal)
- `plans/plan-20260314-skill-first-enforcement-tests.md` - Test enforcement plan
- `plans/plan-20260316-unified-code-review.md` - Code review plan

### Research Documents
- `fibonacci-validation-research.md` - Story point validation research
- `plan-premortem-mitigations.md` - Pre-mortem analysis

### State Directories
- `.claude/state/` - Session state, intent state
- `.claude/state/policy_gate/` - Intent analysis cache
- `.pytest_cache/` - Pytest cache (gitignored)

---

## END OF BUNDLE

This bundle contains all essential context for LLM question-answering about the /plan-workflow skill.
Generated: 2026-03-17 | File Count: 49 | Execution Mode: 2-agents
