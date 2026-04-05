# Review Bundle: Planning Skill

**Generated**: 2026-03-23
**Scope**: `P:/.claude/skills/planning/` + `P:/.claude/agents/adversarial-*.md`
**File Count**: 34 files (9 .md + 25 .py)
**Execution Mode**: 2-agent (10-50 files)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

| Field | Value |
|-------|-------|
| Skill name | `planning` |
| Version | 4.2.3 |
| Skill root | `P:/.claude/skills/planning/` |
| Adversarial agents | `P:/.claude/agents/adversarial-*.md` (6 agents, separate directory) |

### Domain & Purpose

The `/planning` skill creates and verifies implementation plans with automatic quality checks. It is the primary planning workflow for solo-dev sessions: accepts a topic string or ADR file path, builds a structured plan with canonical sections, runs deterministic verification (section completeness, solo-dev constraints, RTM coverage), auto-fixes structural issues, dispatches 6 adversarial subagents in parallel, and presents findings with GTO-style Recommended Next Actions.

### Scale Metrics

| Metric | Value |
|--------|-------|
| SKILL.md | ~450 lines |
| auto_verify.py | ~1110 lines |
| Supporting modules | 7 Python files (225–334 lines each) |
| Test files | 15 test files |
| Adversarial agents | 6 agents (separate `P:/.claude/agents/`) |
| Version history | v2.13 (2026-03-16) → v4.2.3 (2026-03-20) — 8 versions in 4 days |

### Environment

- **OS**: Windows 11 Pro (NTFS, PowerShell)
- **Primary language**: Python 3.14
- **Package managers**: None (self-contained skill)
- **External services**: None

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /planning "do X" or /planning <ADR-path>
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  SKILL.md (orchestrator)                                    │
│  Claude assembles plan → calls scripts → Task() agents      │
│  Presents findings with GTO Recommended Next Actions         │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 1: CREATE PLAN (Claude writes plan file)               │
│  Output: ~/.claude/plans/plan-{slug}.md                      │
│  Canonical sections:                                          │
│    Problem, Context, Existing Implementation,                 │
│    Test Coverage, Solution, Implementation Plan,              │
│    Risks, Success Criteria, Dependencies                      │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 2: auto_verify.py (deterministic checks)               │
│  Input: plan file path                                       │
│  Checks:                                                     │
│    • Format normalization (ADR/transcript/free-text → plan)   │
│    • Section completeness (6 required + 3 alternatives)      │
│    • Solo-dev violations (7 regex patterns)                 │
│    • Implementation completeness (IMPL-001, GAP-001)         │
│    • Consumer impact (CONS-001)                              │
│    • RTM coverage (requirements → tasks mapping)            │
│  Output: {plan_path}.review.result.json                      │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 3: auto_fix.py (automatic corrections)                 │
│  Adds missing sections with placeholder content               │
│  Canonicalizes section names via alias mapping                 │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 4: 6 adversarial Task() agents (parallel dispatch)      │
│  Pre-create: mkdir -p P:/.claude/plans/adversarial/         │
│  Each agent writes findings to JSON, returns ONLY file path    │
│  Token savings: ~50 tokens vs ~2-4KB inline JSON (~80%)      │
│                                                              │
│  Agent           File Written                    Default Path │
│  ─────────────────────────────────────────────────────────────────│
│  compliance      P:/.claude/plans/adversarial/   state/      │
│  logic          P:/.claude/plans/adversarial/   state/      │
│  testing        P:/.claude/plans/adversarial/   state/      │
│  security       P:/.claude/plans/adversarial/   state/       │
│  failure-modes  P:/.claude/plans/adversarial/  state/      │
│  critic         P:/.claude/plans/adversarial/  state/       │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 5: Claude reads findings files, presents results        │
│  GTO-style: domain-numbered actions (1a, 1b, 2a...)          │
│  Final line: full Windows path to plan file                   │
└──────────────────────────────────────────────────────────────┘
```

### ADR-Aware Flow

```
ADR input (ADR-002-chs-consolidation.md)
         │
         ▼
adr_path_mapper.is_adr_file() → True
adr_path_mapper.get_plan_path_for_adr()
    → ~/.claude/plans/plan-adr-002-chs-consolidation.md
         │
         ▼
normalize_adr_to_plan() in auto_verify.py
    • Context → Problem + Context Analysis
    • Decision → Proposed Solution
    • Consequences (+) → Solution
    • Consequences (-) → Risks
    • Implementation Checklist → TASK-XXX with acceptance criteria
```

### State Management Architecture

Two independent state systems exist:

```
plan_state_manager.py          state_manager.py
─────────────────────          ─────────────────
State dir:                    State dir:
  ~/.claude/hooks/state/        ~/.claude/state/
  pr_workflow_{tid}.json        planning/terminals/
                                {tid}/plan_review_state.json

Terminal ID source:           Terminal ID source:
  hook_base.get_terminal_id()  CLAUDE_TERMINAL_ID |
  WT_SESSION env var           TERMINAL_ID env var |
  PID + timestamp hash         TERM env var (PROBLEM)

Used by: SKILL.md reference   Used by: unknown
Cleanup: cleanup_all_         Cleanup: mark_verification_
  stale_states()                 complete() + is_plan_locked()
```

---

## 3. EXECUTION AND DATA FLOW

### Input → Output

| Input Type | Detection | Output Plan Path |
|-----------|-----------|-----------------|
| Topic string (`"do X"`) | Direct argument | `~/.claude/plans/plan-{slug}.md` |
| ADR path (`ADR-002.md`) | Filename pattern + content | `~/.claude/plans/plan-adr-002-{title}.md` |
| Chat transcript | Timestamp pattern in content | `~/.claude/plans/plan-extracted-from-transcript.md` |
| Free text | Catch-all | `~/.claude/plans/plan-free-text-input.md` |

### Adversarial Agent Dispatch Protocol

SKILL.md (lines 203–267) documents:
1. `mkdir -p P:/.claude/plans/adversarial/` (pre-create)
2. Dispatch all 6 `Task()` agents in **one message** (parallel)
3. Each agent returns **only its output file path** (~50 tokens)
4. Claude reads all 6 files after collection

**Actual adversarial agent output paths** differ from SKILL.md documentation:

| Agent | SKILL.md Says | Agent Actually Writes |
|-------|-------------|---------------------|
| compliance | `P:/.claude/plans/adversarial/compliance-findings.json` | `~/.claude/state/adversarial-compliance-{datetime}.json` |
| logic | `P:/.claude/plans/adversarial/logic-findings.json` | `~/.claude/state/adversarial-logic-{datetime}.json` |
| testing | `P:/.claude/plans/adversarial/testing-findings.json` | `~/.claude/state/adversarial-testing-{datetime}.json` |
| security | `P:/.claude/plans/adversarial/security-findings.json` | `~/.claude/state/adversarial-security-{datetime}.json` |
| failure-modes | `P:/.claude/plans/adversarial/failure-modes-findings.json` | `~/.claude/state/adversarial-failure-modes-{datetime}.json` |
| critic | `P:/.claude/plans/adversarial/critic-findings.json` | `~/.claude/state/adversarial-critic-{datetime}.json` |

**ASSUMPTION**: SKILL.md documents the intended path (`P:/.claude/plans/adversarial/`), but agent definitions write to `~/.claude/state/`. This discrepancy may cause the orchestrator to fail to read findings if the file-path return pattern was implemented expecting `P:/.claude/plans/adversarial/`.

### Error Handling

- **FileNotFoundError** in auto_verify.py → returns `status: "BLOCKED"` with ERROR-002
- **PermissionError** on state writes → returns `False` silently, workflow continues
- **Invalid JSON** in agent findings → skipped with warning, partial analysis continues
- **Missing adversarial agent** → would fail at Task() dispatch time, not at verification time

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Lines | Responsibility | Key Functions/Classes |
|------|-------|---------------|----------------------|
| `SKILL.md` | ~450 | Orchestration workflow, commands, ADR behavior, GTO output | Workflow steps, state management, pre-mortem questioning |
| `__lib/auto_verify.py` | ~1110 | Deterministic plan validation, format normalization | `verify_plan()`, `detect_format()`, `normalize_*_to_plan()`, `check_*()` |
| `__lib/auto_fix.py` | ~254 | Automatic structural fixes | `fix_plan()`, `add_missing_sections()`, `get_placeholder()` |
| `__lib/format_findings.py` | ~225 | GTO-style Recommended Next Actions | `format_recommended_actions()`, `group_findings_by_domain()`, `skill_for_finding()` |

### Utilities

| File | Lines | Responsibility | Key Functions |
|------|-------|---------------|--------------|
| `__lib/adr_path_mapper.py` | ~211 | ADR detection, plan path generation | `get_plan_path_for_adr()`, `is_adr_file()`, `extract_adr_identifier()` |
| `__lib/plan_state_manager.py` | ~334 | Terminal-scoped state, crash recovery | `PlanStateManager` class, `cleanup_all_stale_states()` |
| `__lib/state_manager.py` | ~272 | Terminal-isolated state, lock detection | `get_resume_context()`, `is_plan_locked()`, `mark_verification_complete()` |
| `__lib/cleanup.py` | ~156 | Artifact retention, cleanup | `cleanup_plan_artifacts()`, `cleanup_adversarial_reviews()` |
| `__lib/__init__.py` | — | Package init | — |

### Schema

| File | Lines | Responsibility |
|------|-------|---------------|
| `FINDINGS_SCHEMA.md` | ~148 | JSON schema for all findings (id, category, priority, title, description, recommendation) |

### Adversarial Agents (external)

Located at `P:/.claude/agents/adversarial-*.md` — 6 agents, each is a custom subagent type:

| Agent | Purpose | Severity Format | Output Path |
|-------|---------|----------------|-------------|
| `adversarial-compliance.md` | Spec violations, solo-dev constraints | `HIGH\|CRITICAL` | `~/.claude/state/adversarial-compliance-{datetime}.json` |
| `adversarial-logic.md` | Logic errors, race conditions, off-by-one | `blocker\|high\|medium\|low` | `~/.claude/state/adversarial-logic-{datetime}.json` |
| `adversarial-testing.md` | Coverage gaps, brittle tests | `HIGH\|CRITICAL` | `~/.claude/state/adversarial-testing-{datetime}.json` |
| `adversarial-security.md` | Data leaks, access control | `CRITICAL\|HIGH` | `~/.claude/state/adversarial-security-{datetime}.json` |
| `adversarial-failure-modes.md` | Domain failure risks + web research | `blocker\|high\|medium\|low` | `~/.claude/state/adversarial-failure-modes-{datetime}.json` |
| `adversarial-critic.md` | Meta-analysis: consensus, blind spots, calibration | N/A | `~/.claude/state/adversarial-critic-{datetime}.json` |

**Distinctive trait**: `adversarial-failure-modes` uses `WebSearch`/`WebFetch` for domain-specific anti-pattern research. `adversarial-critic` runs AFTER all other agents and aggregates their outputs into meta-findings.

### Tests

15 test files in `tests/`:
`test_adversarial_review_coordinator.py`, `test_auto_fix.py`, `test_auto_verify_new_checks.py`, `test_auto_verify_rtm_integration.py`, `test_auto_verify_wording.py`, `test_design_formalization.py`, `test_markdown_summary.py`, `test_opt_out_flags.py`, `test_plan_state_manager.py`, `test_plan_topic_guard_validation.py`, `test_plan_update_coordinator.py`, `test_plan_update_integration.py`, `test_plan_visualizer_edge_cases.py`, `test_plan_visualizer_regex.py`, `test_plan_visualizer_story_points.py`, `test_rtm.py`, `test_state_schema_validation.py`, `test_state_tracker_schema_validation.py`, `test_planning_integration.py`

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Claude-as-orchestrator**: Claude reads plan, calls scripts, dispatches agents, presents results — scripts are deterministic tools, not AI agents
2. **Token efficiency**: Adversarial agents write findings to files and return paths, not inline JSON (~80% token reduction)
3. **Format-agnostic input**: Any format (ADR, transcript, free-text) normalizes to canonical plan structure before validation
4. **Solo-dev constraints**: Plans must not contain team coordination patterns (enforced by 7 regex patterns)
5. **ADR separation**: ADRs are source-of-truth; plan reviews live in separate artifacts at `~/.claude/plans/plan-adr-*.md`

### Solo-Dev Violation Patterns (auto_verify.py:76-85)

```python
SOLO_DEV_VIOLATIONS = [
    r"stakeholder\s+approval",
    r"team\s+coordination",
    r"consensus\s+required",
    r"team\s+review",
    r"collaborative\s+effort",
    r"multi-?\s*team",
    r"cross-?\s*team",
    r"team\s+lead\s+approval",
]
```
Negated forms ("no team coordination") are excluded via 20-char lookbehind.

### Required Plan Sections (auto_verify.py:38-73)

Canonical names: Problem, Context, Existing Implementation, Test Coverage, Solution, Implementation Plan.
Alternatives (at least one required): "Risks, Success Criteria, Dependencies" (combined) OR separate Risks / Success Criteria / Dependencies.

Section aliases allow flexible naming: "Design" → "Solution", "Tests" → "Test Coverage", "Current State" → "Existing Implementation".

### Things That Must NOT Change

- Task dispatch must remain parallel in a single message (token efficiency)
- Plan files must remain in `~/.claude/plans/` (state manager dependency)
- ADR normalization must preserve original ADR content while restructuring into plan format
- Solo-dev violation detection must exclude negated forms

---

## 6. KNOWN ISSUES

### Issue 1: Adversarial Agent Output Path Mismatch [HIGH]

**Files**: SKILL.md:217-253 vs `P:/.claude/agents/adversarial-*.md`

**Scenario**: SKILL.md documents that adversarial agents should write findings to `P:/.claude/plans/adversarial/{agent}-findings.json`, but agent definitions specify `~/.claude/state/adversarial-{agent}-{datetime}.json`.

**Expected**: Orchestrator creates `P:/.claude/plans/adversarial/` and reads findings from there after agent dispatch.
**Actual**: Agents write to `~/.claude/state/`. The `mkdir -p P:/.claude/plans/adversarial/` pre-creation step is correct, but agents write to a different directory.

**Impact**: Orchestrator may not find findings files after agent dispatch. The Step 3c Read() calls in SKILL.md (lines 260-266) target the wrong directory.

**Current workaround**: Unknown — if this is a real bug, adversarial findings would silently fail to be read.

---

### Issue 2: Duplicate State Management Systems [MEDIUM]

**Files**: `__lib/plan_state_manager.py` vs `__lib/state_manager.py`

Two independent state management systems with different:
- State file locations (`hooks/state/` vs `state/planning/terminals/`)
- Terminal ID detection (see Issue 3)
- Session boundary detection approaches
- Phase completion models

**Impact**: Maintenance confusion; potential for divergent behavior across terminals; `plan_state_manager.py` appears newer (has `cleanup_all_stale_states()`) but `state_manager.py` has `mark_verification_complete()` which `plan_state_manager.py` lacks.

**Current workaround**: SKILL.md references `plan_state_manager.py`; `state_manager.py` appears unused by the main workflow.

---

### Issue 3: `TERM` Env Var as Terminal Identifier [MEDIUM]

**File**: `__lib/state_manager.py:30`

```python
for var in ("CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM"):
    value = os.environ.get(var)
    if value:
        return value
```

`TERM` is a generic shell variable (e.g., `xterm-256color`, `bash`, `powershell`). Using it as a terminal identifier creates **high collision risk** across multiple Claude Code terminals running in different shell sessions on the same machine.

`plan_state_manager.py` uses `WT_SESSION` (Windows Terminal) or PID+timestamp hash, which is more specific.

**Impact**: Multi-terminal state isolation may fail if `TERM` is the only available identifier. Two terminals in `xterm-256color` shells would share state.

**Current workaround**: If `WT_SESSION` is set (Windows Terminal), it takes precedence. Collision only occurs on generic terminals without `CLAUDE_TERMINAL_ID` or `WT_SESSION`.

---

### Issue 4: `validate_adversarial_agents()` Is Dead Code [LOW]

**File**: `__lib/auto_verify.py:645-680`

`validate_adversarial_agents()` checks that all 6 required agents exist on disk, but `verify_plan()` (line 966) calls all check functions and builds the result **without ever calling** `validate_adversarial_agents()`.

**Impact**: Missing adversarial agents would fail at Task() dispatch time, not at verification time. The early-warning check is implemented but not wired in.

**Current workaround**: None needed — failure mode is graceful (will fail at dispatch).

---

### Issue 5: `workflow_steps` Declares 7 Steps But "How It Works" Describes 4 [LOW]

**File**: `SKILL.md:19-26` vs `SKILL.md:134-158`

```yaml
workflow_steps:
  - detect_topic
  - build_plan
  - run_verification
  - auto_fix
  - adversarial_review
  - present_results
  - cleanup_artifacts   # ← declared but not described
```

The main "How It Works" section describes 4 steps: Create Plan, Auto-Verify, Adversarial Review, Present Results. `cleanup_artifacts` is declared in `workflow_steps` but is never explained as a user-facing step. `cleanup.py` exists but `hooks: {}` is empty in frontmatter.

**Impact**: Documentation inconsistency; no functional issue detected.

---

### Issue 6: SKILL.md File Locations Section Outdated [LOW]

**File**: `SKILL.md:366-384`

The file tree shows `__lib/` with 4 files but 7 exist. Also references `.claude/agents/` structure from pre-v3.1 (when subprocess-based `adversarial_runner.py` existed).

**Impact**: Misleading for someone reading SKILL.md to understand the codebase.

---

## 7. INTEGRATION POINTS

### Plan File Paths

| Context | Path | Source |
|---------|------|--------|
| Default plans | `~/.claude/plans/plan-{slug}.md` | SKILL.md:78, adr_path_mapper.py:34 |
| ADR plans | `~/.claude/plans/plan-adr-{id}-{title}.md` | SKILL.md:102 |
| Review results | `{plan_path}.review.result.json` | auto_verify.py:1086 |
| Adversarial findings (intended) | `P:/.claude/plans/adversarial/{agent}-findings.json` | SKILL.md:217-253 |
| Adversarial findings (actual) | `~/.claude/state/adversarial-{agent}-{datetime}.json` | Agent definitions |

### How Claude Dispatches Adversarial Agents

SKILL.md lines 209-254 — **all 6 agents dispatched in one message**:

```python
Task(subagent_type="adversarial-compliance",
     description="Compliance review",
     prompt="""Review plan at <plan_path> for specification violations...
1. Write JSON findings to: P:/.claude/plans/adversarial/compliance-findings.json
2. Return ONLY: "P:/.claude/plans/adversarial/compliance-findings.json" """)
# ... 5 more agents in same message
```

After all agents return paths, Claude reads all 6 files (SKILL.md lines 260-266).

### Format Normalization Pipeline

```
Input format detection:
  ADR pattern       → "adr"
  Transcript pattern → "transcript"
  Has Problem/Solution sections → "plan"
  Catch-all        → "free_text"
         ↓
normalize_to_plan_format(plan, format_type)
  normalize_adr_to_plan()     # Maps Context→Problem+Context, Decision→Solution, etc.
  normalize_transcript_to_plan()
  normalize_free_text_to_plan()
  plan format → return unchanged
```

ADR normalization also converts checkbox items (`- [ ]`) to **`TASK-XXX`** format with acceptance criteria extracted from indented lines.

### Script Invocation Pattern

All scripts called via `python .claude/skills/planning/__lib/{script}.py <plan_path>` from SKILL.md documentation.

### Adversarial Agent Findings Schema Summary

All 6 agents use different JSON schemas:

| Agent | Root Fields | Finding Fields | Unique Fields |
|-------|------------|----------------|---------------|
| compliance | `findings[]` | id, severity, title, description, evidence, impact, recommendation, confidence | — |
| logic | `findings[]`, `handoff`, `summary`, `open_questions` | id, severity, location, problem, adversarial_scenario, impact, recommendation | `adversarial_scenario` |
| testing | `findings[]` | id, severity, title, description, evidence, impact, recommendation, confidence | `customer_visible` in impact |
| security | `findings[]` | id, severity, title, description, evidence, impact, recommendation, confidence | `regulatory_impact` in impact |
| failure-modes | `findings[]`, `handoff`, `summary`, `open_questions` | id, severity, location, problem, adversarial_scenario, impact, recommendation, reference | `reference`, `research_sources` in summary |
| critic | `review_metadata`, `meta_findings[]` | N/A (meta-findings) | Consensus, blind spots, bias, contradictions, calibration |

---

## 8. APPENDIX: VERSION HISTORY SUMMARY

| Version | Date | Key Change |
|---------|------|-----------|
| v4.2.3 | 2026-03-20 | GTO-style Recommended Next Actions; removed user approval prompt |
| v4.2.2 | 2026-03-20 | User approval required for adversarial findings |
| v4.2.1 | 2026-03-20 | Final output line must be full Windows path |
| v4.2.0 | 2026-03-20 | Unified workflow (auto-verify + adversarial by default); build-only mode |
| v4.1.0 | 2026-03-20 | ADR-aware plan file separation |
| v4.0.0 | 2026-03-19 | Fully automated with auto_fix.py; section aliases system |
| v3.1.0 | 2026-03-18 | Replaced subprocess dispatch with Agent tool; removed `lib.` → `__lib.`; ~80% file size reduction |
| v2.13.0 | 2026-03-16 | Added state management |

**Evolution trajectory**: Rapid iteration on orchestration model. Key changes: subprocess→Task dispatch (v3.1), inline JSON→file-path return (v4.2.x), ADR in-place→ADR separate (v4.1), manual→auto-fix (v4.0).

---

## ASSUMPTIONS

1. `~/.claude/plans/` resolves per-platform via `Path.home() / ".claude" / "plans"` — correct on Windows (`C:/Users/brsth/.claude/plans/`)
2. Adversarial agent dispatch uses `Task()` tool with `subagent_type` matching filename (without `.md`) in `P:/.claude/agents/`
3. The `P:/.claude/plans/adversarial/` pre-creation step (SKILL.md:203-205) is executed before agent dispatch
4. `cleanup_artifacts` in `workflow_steps` may be aspirational — `cleanup.py` exists but no hook invocation found in SKILL.md (hooks: {} is empty)
5. SKILL.md documents intended adversarial output paths; agent definitions show actual paths — Issue 1 may represent a real bug if file-path return was recently implemented
