# Review Bundle: Code Review & Quality Ecosystem

**Generated**: 2026-03-10
**Scope**: P:/.claude/ (code review and quality assurance)
**File Count**: 275 components (154 skills, 104 hooks, 17 agents)
**Execution Mode**: 4-agent parallel analysis

---

## 1. PROJECT CONTEXT

### Bundle Metadata

This bundle provides comprehensive context for the Claude Code code review and quality assurance ecosystem, encompassing all skills, hooks, and agents used for validating code quality, security, performance, and architectural soundness.

### Domain & Purpose

**Purpose**: Provide automated, multi-perspective code quality validation for solo development environments.

**Who uses it**:
- Solo developers practicing pragmatic software development
- Claude Code AI assistant (automatic invocation via skills/hooks)
- Manual invocation for targeted analysis (/q, /r, /adversarial-review, etc.)

**Why critical**:
- Prevents bugs, security vulnerabilities, and architectural drift
- Enforces coding standards and best practices
- Provides automated peer review in solo-dev environments
- Catches issues NotebookLM found: import path mismatches, path traversal vulnerabilities, brittleness, anti-patterns, documentation contradictions

### Scale Metrics

- **Total Components**: 275 (154 skills, 104 hooks, 17 agents)
- **Major Subsystems**:
  - Adversarial review system (8 parallel perspectives)
  - Quality check system (6-phase GoT+ToT analysis)
  - Code simplification and refactoring
  - Standards compliance validation
  - Testing and test coverage analysis
  - Security vulnerability scanning
  - Performance bottleneck detection
- **Deployment Scope**: Local Claude Code environment (P:/.claude/)
- **Change Frequency**: Active development (new skills/hooks added regularly)

### Your Environment

**OS and shell**: Windows 11 Pro, bash (Git Bash/WSL)

**Primary languages and frameworks**:
- Python 3.14 (hooks, skills, agents)
- Markdown (SKILL.md documentation)
- JSON (state files, logs)

**Package managers and build tools**:
- None (skills are symlinked to P:/.claude/skills/)
- Hooks executed directly via python command

**Databases or external services**:
- CHS (Chat History Search): P:/__csf/src/features/chs/
- CKS (Constitutional Knowledge System): P:/__csf/src/features/cks/
- TaskMaster: P:/__csf/src/features/taskmaster/
- NotebookLM CLI (external): nlm commands for media generation

---

## 2. ARCHITECTURE OVERVIEW

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INVOCATION                              │
│  /q, /r, /adversarial-review, /trace, /diagnose, /simplify    │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │   SKILL ENTRY POINT     │
            │  (SKILL.md → main logic) │
            └────────────┬────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   ┌────▼─────┐                    ┌─────▼──────┐
   │  SKILL   │                    │   HOOKS   │
   │  LOGIC   │                    │ (Gates/    │
   │          │                    │ Validators)│
   └────┬─────┘                    └─────┬──────┘
        │                               │
        └─────────────┬─────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼────────┐        ┌───────▼────────┐
    │  AGENTS     │        │   DIRECT       │
    │  (Subagents)│        │   EXECUTION    │
    └─────────────┘        └────────────────┘
         │
    ┌────▼────────┐
    │  TOOLS      │
    │  (Read,     │
    │   Grep,     │
    │   Glob,     │
    │   Bash)     │
    └─────────────┘
```

### Data Flow

1. **Invocation**: User invokes skill (e.g., `/q`, `/adversarial-review`)
2. **Skill Execution**: SKILL.md main logic runs, may invoke hooks
3. **Hook Gates**: Hooks validate/modify tool use (PreToolUse, PostToolUse, Stop)
4. **Agent Spawning**: Skill spawns subagents for parallel analysis
5. **Tool Use**: Agents use Read/Grep/Glob/Bash to analyze code
6. **Findings**: Results compiled, confidence-scored, presented to user

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Adversarial Review Flow**:
```
/adversarial-review [path]
→ Parse mode (--security, --performance, etc.)
→ Spawn 8 adversarial-* agents in parallel
→ Each agent analyzes from specialized perspective
→ Quality gate filters findings by confidence (80+ threshold)
→ Present aggregated findings with severity classification
```

**Quality Check (/q) Flow**:
```
/q [path]
→ Q1: ScopeResolver (what to analyze)
→ Q2: QuickCollectors (parallel data gathering)
→ Q3: IssueNormalizer (categorize findings)
→ Q4: ModePlanner (determine analysis depth)
→ Q5: Strategic renderer (GoT-enhanced requirements analysis)
→ Q6: ContextSink (persist findings)
→ Hooks track completion state, enforce phase progression
```

**Remember/Refine (/r) Flow**:
```
/r [path]
→ Deterministic improvement pass
→ Read files, identify omissions
→ Apply structured improvements
→ Write updated files
→ Track completion state
```

### State Management

**State Stores**:
- `P:/.claude/state/`: Terminal-scoped state files
  - `breadcrumbs_{terminal_id}/`: Breadcrumb trails for skill execution
  - `skill_execution_{terminal_id}/`: Skill execution state
  - Tool history in `P:/.claude/logs/tool-history.jsonl`

**Ownership**:
- Skills own their state during execution
- Hooks validate tool use but don't own state
- Agents are stateless (fresh invocation each time)

**Consistency Model**:
- Terminal-scoped isolation (prevents cross-terminal contamination)
- Session ID changes during compaction (not used for state keys)
- Automatic cleanup on SessionEnd and PreCompact

### Error Handling

**Fail-open vs fail-closed**:
- **Fail-closed**: Security gates (PreToolUse_authorization_gate, PreToolUse_dependency_verification_gate)
- **Fail-open**: Quality checks (/q, /r) - warnings don't block execution

**Retry/timeout behavior**:
- Hooks have timeout (5-10 seconds)
- No retry - hook failure is logged but doesn't block skill execution
- Agents have no timeout (run until completion or context limit)

---

## 4. COMPONENT INVENTORY

### Skills (154 total)

#### Core Quality & Review Skills

| Skill | Purpose | Key Functions | Files |
|-------|---------|---------------|-------|
| **/q** (6 phases) | Strategic quality check | GoT+ToT requirement analysis, constraint extraction | `P:/.claude/skills/q/` |
| **/r** | Remember/Refine pass | Deterministic code improvement, omissions detection | `P:/.claude/skills/r/` |
| **/adversarial-review** | 8-perspective parallel review | Spawns adversarial-* agents | `P:/.claude/skills/adversarial-review/` |
| **/trace** | Manual trace-through verification | Step-by-step execution verification | `P:/.claude/skills/trace/` |
| **/diagnose** | Structured diagnostic protocol | Hypothesis testing, evidence gathering | `P:/.claude/skills/diagnose/` |
| **/simplify** | Code simplification | Refactor for clarity, consistency | `P:/.claude/skills/simplify/` |

#### Adversarial Perspectives (8 skills)

| Skill | Perspective | Finds |
|-------|-------------|-------|
| **/adversarial-security** | Security analysis | Data leaks, access control gaps, injection vectors |
| **/adversarial-performance** | Performance analysis | Timeouts, bottlenecks, N+1 patterns |
| **/adversarial-compliance** | Specification validation | Schema compliance, contract violations |
| **/adversarial-quality** | Maintainability analysis | Technical debt, code rot risks |
| **/adversarial-testing** | Test coverage analysis | Missing scenarios, brittle tests, gaps |
| **/adversarial-qa** | QA analysis | Coverage gaps, missing scenarios |
| **/adversarial-rca** | Root cause analysis | Multi-agent reasoning for failures |
| **/adversarial-failure-modes** | Failure mode discovery | Domain-aware anti-patterns |

#### Code Standards & Validation

| Skill | Purpose | Standards |
|-------|---------|-----------|
| **/code-python** | Python standards validation | uv, ruff, type hints, Python 3.12+ |
| **/code-standards** | Multi-language standards | DRY principles, SOLID, patterns |
| **/code-typescript** | TypeScript standards | Node 22+, strict types, async |
| **/comply** | Unified standards validation | Constitutional compliance |
| **/quality-gate** | Final confidence filter | 80+ threshold for findings |
| **/spec-compliance** | Specification following | Protocol validation |
| **/validate-safety-patterns** | Safety pattern validation | Evidence-based validation |

#### Specialized Analysis

| Skill | Purpose | Focus |
|-------|---------|-------|
| **/aid** (AI Distiller) | Code analysis templates | Single/multi-file docs, diagrams |
| **/av**, **/av2** | Skill analyzer/optimizer | Mechanical continuation, skill quality |
| **/cognitive-*** | Cognitive frameworks | RCA, architecture, patterns |
| **/disler-*** | Disler observability | Performance monitoring |
| **/perf** | Performance tracing wrapper | Detect bottlenecks, async issues |
| **/test-analyzer** | Unified test analysis | Coverage, gaps, patterns |
| **/truth**, **/truth-av** | Assertion verification | Validate claims against code |

#### Development Workflow

| Skill | Purpose | Integration |
|-------|---------|-------------|
| **/p** | Code maturation pipeline | Orchestrates development workflow |
| **/refactor** | Multi-file refactoring | Synergy detection, orchestration |
| **/multi-file-refactor** | Refactor with synergy | Detect cross-file improvements |
| **/arch** | Architecture advisor | Template-based system design |
| **/flow** | Workflow orchestration | Pipeline coordination |
| **/orchestrator-*** | Multi-agent coordination | Task scheduling, consensus |

### Hooks (104 total)

#### PreToolUse Hooks (Validation Gates)

| Hook | Purpose | Validates |
|------|---------|----------|
| **PreToolUse_authorization_gate** | Command authorization | User permission for dangerous operations |
| **PreToolUse_bulk_delete_gate** | Prevent mass deletion | Detects destructive file operations |
| **PreToolUse_command_intent_gate** | Intent validation | Ensures commands match declared intent |
| **PreToolUse_dependency_verification_gate** | Dependency checking | Validates imports before use |
| **PreToolUse_investigation_gate** | Investigation gating | Controls investigation vs execution |
| **PreToolUse_observe_before_act_gate** | Observation requirement | Forces analysis before changes |
| **PreToolUse_path_validator** | Path validation | Prevents directory traversal |
| **PreToolUse_python_c_validator** | C code validation | Checks C code quality |
| **PreToolUse_python_import_gate** | Import validation | Validates Python imports |
| **PreToolUse_risk_tier_gate** | Risk assessment | Blocks high-risk operations |
| **PreToolUse_syntax_gate** | Syntax validation | Checks code syntax before execution |

#### PostToolUse Hooks (Quality Checks)

| Hook | Purpose | Checks |
|------|---------|--------|
| **PostToolUse_artifact_validator** | Artifact tracking | Validates artifact updates |
| **PostToolUse_bash_syntax_gate** | Bash syntax validation | Checks bash command syntax |
| **PostToolUse_documentation_validator** | Documentation quality | Validates doc updates |
| **PostToolUse_p2_filter_gate** | P2 filtering | Filters P2 phase outputs |
| **PostToolWrite_code_quality** | Code quality check | Validates code after write |

#### Stop Hooks (Completion Validation)

| Hook | Purpose | Validates |
|------|---------|----------|
| **Stop_behavior_gates** | Behavior validation | Ensures behaviors followed |
| **Stop_lazy_workaround_gate** | Workaround detection | Blocks workaround anti-patterns |
| **StopHook_strawberry_validator** | Strawberry validation | Custom validation logic |

#### SessionStart Hooks (Health Checks)

| Hook | Purpose | Monitors |
|------|---------|----------|
| **SessionStart_hook_health_check** | Hook health | Checks hook system status |

### Agents (17 total)

#### Core Analysis Agents

| Agent | Purpose | Tools | Mode |
|-------|---------|-------|------|
| **code-critic** | Independent diagnostic review | Read, Grep, Glob, Bash | plan |
| **quality-gate** | Final confidence filter | Read, Grep, Glob | inherit |
| **rca-specialist** | Root cause analysis | Read, Grep, Glob, Bash | inherit |
| **test-analyzer** | Unified test analysis | Read, Grep, Glob, Bash | inherit |

#### Adversarial Agents (8 perspectives)

| Agent | Perspective | Focus |
|-------|-------------|-------|
| **adversarial-security** | Security | OWASP Top 10, injection vectors |
| **adversarial-performance** | Performance | N+1 patterns, bottlenecks |
| **adversarial-compliance** | Compliance | Specification validation |
| **adversarial-quality** | Quality | Maintainability, technical debt |
| **adversarial-testing** | Testing | Test coverage, scenarios |
| **adversarial-rca** | RCA | Multi-agent reasoning |

#### Specialized Agents

| Agent | Purpose | Specialization |
|-------|---------|----------------|
| **simplifier** | Code simplification | Language-agnostic simplification |
| **python-simplifier** | Python 3.12+ simplification | Modern Python patterns |
| **tdd-test-writer** | TDD test generation | Test-first development |
| **csf-nip-constitution-specialist** | CSF NIP governance | Constitutional compliance |
| **csf-nip-quality** | CSF NIP quality | Quality standards |
| **csf-nip-security** | CSF NIP security | Security validation |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Multi-perspective analysis**: No single tool finds all issues - parallel adversarial perspectives catch different bug classes
2. **Confidence-based filtering**: Findings below 80% confidence are filtered out to reduce noise
3. **Hook-based enforcement**: Skills can enforce execution patterns via hooks (e.g., /q has phase gates)
4. **Agent isolation**: Each adversarial agent runs independently to avoid groupthink
5. **Terminal-scoped state**: State is isolated per terminal to prevent cross-contamination
6. **Automatic cleanup**: State files cleaned up on SessionEnd and PreCompact

### Technology Constraints

1. **Python 3.12+**: All hooks and skills must use Python 3.12+ syntax
2. **No external dependencies**: Skills/hooks must run with standard library + requests
3. **Symlink-based deployment**: Skills are symlinked to `P:/.claude/skills/`
4. **Hook registration**: Hooks registered in `P:/.claude/settings.json`
5. **No database**: State stored in JSON files (no SQLite, Redis, etc.)

### Performance SLAs

- **Skill invocation**: < 2 seconds for simple skills
- **Hook execution**: < 5 seconds (timeout enforced)
- **Agent spawning**: Parallel agents run concurrently
- **Context window**: Agents limited to 200K tokens

### Things That Must NOT Change

1. **Terminal-scoped state isolation**: Never use session_id for state keys (changes during compaction)
2. **Hook timeout enforcement**: Hooks must complete within 5-10 seconds
3. **Confidence threshold**: Findings below 80% confidence must be filtered
4. **Multi-perspective approach**: Never consolidate to single-perspective analysis
5. **Fail-closed security gates**: Security hooks must block on failure
6. **Anti-pattern detection**: System must detect and report workarounds over root causes

---

## 6. KNOWN ISSUES

### Issues Found by NotebookLM Multi-Source Analysis (2026-03-10)

**Context**: NotebookLM analyzed skill-guard package with 15 source files (README, source code, tests, pyproject.toml) and found 5 real issues that our code review skills did NOT catch:

#### Issue #1: Incorrect Import Paths (HIGH)

**Location**: `src/skill_guard/breadcrumb/tracker.py:34`

**Problem**:
- Code imports: `from skill_guard.terminal_detection`
- Actual file: `src/skill_guard/utils/terminal_detection.py`
- Result: Always falls back to `skill_execution_state.detect_terminal_id`

**Impact**: Silent performance degradation, redundant implementation

**Why our skills missed it**:
- **/trace** would have found it IF explicitly invoked on breadcrumb/tracker.py
- **/adversarial-review** would have found it IF run in security mode
- Neither was invoked before media generation

**Fix needed**: Correct import to `from skill_guard.utils.terminal_detection`

---

#### Issue #2: Path Traversal Vulnerability (CRITICAL - SECURITY)

**Location**: `src/skill_guard/breadcrumb/tracker.py:61`

**Problem**:
```python
skill_lower = skill_name.lower().replace("/", "_").replace(" ", "_")
```
- Only strips `/` and spaces, NOT `.` or `..`
- Attack vector: Skill name `../../../etc/passwd` writes outside breadcrumbs directory

**Impact**: Could write state files anywhere on filesystem (SECURITY RISK)

**Why our skills missed it**:
- **/adversarial-security** IF run would have found this
- **PreToolUse_path_validator** hook exists but wasn't triggered
- We skipped PHASE 4.5 (Code Review) in /package

**Fix needed**: Add validation for `.` and `..` in skill names

---

#### Issue #3: Brittle Path Injection (HIGH)

**Location**: `src/skill_guard/skill_execution_state.py:44`

**Problem**:
```python
sys.path.insert(0, str(Path(__file__).parent / "PreToolUse"))
```
- Assumes `PreToolUse/` directory exists next to file
- Breaks if library installed differently
- Tightly coupled to hook structure

**Impact**: System breaks if directory structure changes

**Why our skills missed it**:
- **/trace** IF run would have found this
- **/arch** (architecture advisor) IF run would have flagged this
- Neither was invoked

**Fix needed**: Use proper package imports instead of sys.path manipulation

---

#### Issue #4: Disk I/O on Import (MEDIUM - ANTI-PATTERN)

**Location**: `src/skill_guard/skill_execution_state.py:334-337`

**Problem**:
```python
# Auto-migrate on import
try:
    migrate_legacy_state()
except Exception:
    pass
```
- Performs file read/write/delete during module import
- Hidden side effects before application initialization

**Impact**: Violates import isolation principle, unexpected I/O operations

**Why our skills missed it**:
- **/trace** IF run would have found this
- **/simplify** IF run would have flagged this anti-pattern
- **Python core** agent (python-core) IF run would have found this

**Fix needed**: Remove auto-migration, require explicit invocation

---

#### Issue #5: Contradictory Documentation (LOW)

**Location**: `src/skill_guard/breadcrumb/tracker.py:21-22`

**Problem**:
- Line 21: "Age-based cleanup for orphaned trails (>2 hours old)"
- Line 22: "No TTL - cleanup based on lifecycle events, not time"
- Line 45: `MAX_TRAIL_AGE_SECONDS = 7200` (which IS a TTL)

**Impact**: Confusing maintenance, docs don't match code

**Why our skills missed it**:
- **/r** (remember/refine) IF run would have fixed this
- **/docs-validate** IF run would have caught this

**Fix needed**: Remove "No TTL" claim or remove MAX_TRAIL_AGE_SECONDS

---

### Root Cause: Why We Didn't Find These Issues

**1. Scope Specification Required**: Our skills need explicit invocation
- `/adversarial-review P:/packages/skill-guard` would have found #2 (security)
- `/trace P:/packages/skill-guard/src/skill_guard/` would have found #1, #3, #4
- We didn't invoke these skills

**2. PHASE 4.5 Skipped**: /package has automatic code review in PHASE 4.5
- We went straight to PHASE 4.7 (Media Generation)
- Code review was never run

**3. Multi-Source Gap**: Our skills analyze single files at a time
- NotebookLM had 15 sources (README, source code, tests, pyproject.toml)
- Could cross-reference imports, docs vs code, architecture
- Our skills lack this cross-file context

**4. Missing Specialized Scanners**:
- No cross-file import verification tool
- No path traversal vulnerability scanner
- No documentation consistency checker
- No import anti-pattern detector

---

## 7. INTEGRATION POINTS

### For Adding New Code Review Skills

**Location**: `P:/.claude/skills/[skill-name]/`

**Required files**:
- `SKILL.md` - Main documentation and workflow
- `hooks/` - Optional hook scripts for enforcement
- `scripts/` - Optional utility scripts

**Hook integration**:
```json
// In P:/.claude/settings.json
"hooks": {
  "PreToolUse": [
    {
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "python \"P:/.claude/skills/my-skill/hooks/validator.py\""
      }]
    }
  ]
}
```

**Agent invocation**:
```python
# In skill logic
from Agent import Agent

Agent(
    subagent_type="general-purpose",
    prompt="Analyze this code for security vulnerabilities...",
    permission_mode="plan"
)
```

### For Adding New Hooks

**Location**: `P:/.claude/hooks/[HookPoint]_[hook-name].py`

**Hook points**:
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `PostToolWrite` - After file write
- `Stop` - At skill completion
- `SessionStart` - At session initialization

**Hook signature**:
```python
#!/usr/bin/env python3
import sys
import json

def main():
    # Read hook input from stdin
    input_data = json.loads(sys.stdin.read())

    # Perform validation
    # ...

    # Write modified input (or raise exception to block)
    print(json.dumps(input_data))

if __name__ == "__main__":
    main()
```

### For Adding New Agents

**Location**: `P:/.claude/agents/[agent-name].md`

**Agent metadata** (frontmatter):
```yaml
---
name: my-agent
description: What this agent does
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: plan/acceptEdits/default
---
```

**Agent invocation**:
```python
Agent(
    subagent_type="my-agent",  # Matches filename without .md
    prompt="Task description...",
    permission_mode="plan"
)
```

### Data Exchange Contracts

**Skill → Hook**:
- Hook reads from stdin (JSON)
- Hook writes to stdout (JSON)
- Non-zero exit code blocks operation

**Skill → Agent**:
- Agent receives prompt string
- Agent returns text output
- Agent has isolated context (no skill state)

**Hook → State File**:
- State stored in `P:/.claude/state/`
- JSON format
- Terminal-scoped isolation

### Output/Exit Code Expectations

**Hooks**:
- Exit code 0: Allow operation
- Exit code non-zero: Block operation
- stdout: Modified input data (JSON)
- stderr: Log messages (non-blocking)

**Skills**:
- Return to user with findings
- Write state files if needed
- Spawn agents for parallel work

**Agents**:
- Return text output to skill
- No side effects (stateless)
- Context window limited

---

## 8. APPENDIX: Key Learnings from NotebookLM Analysis

### Why Multi-Source Upload Matters

**Single README upload** (previous approach):
- Generated generic assets lacking technical depth
- Missed cross-file issues (imports, docs vs code)
- Produced inaccurate video content (described as "auto-discovery" instead of "enforcement")

**Multi-source upload** (15 files):
- README.md + source code + tests + pyproject.toml
- Found 5 real issues (1 security vulnerability)
- Generated accurate, detailed content
- Cross-referenced imports across files

### Missing Capabilities

**What we need but don't have**:
1. **Cross-file import verification**: Check imports match actual file locations
2. **Path traversal vulnerability scanner**: Detect `..` in user input
3. **Documentation consistency checker**: Validate docs match code
4. **Import anti-pattern detector**: Flag sys.path manipulation, side effects on import
5. **Multi-source code review**: Analyze complete packages, not single files

**Potential solutions**:
1. Run `/adversarial-review` BEFORE media generation (add to /package PHASE 4.5)
2. Create `/vdate` variant for multi-source package validation
3. Add cross-file analysis to existing adversarial agents
4. Create specialized scanner for import paths and vulnerabilities
5. Enhance NotebookLM integration for regular validation (not just media)

### Recommended Workflow Changes

**For /package**:
1. Run PHASE 4.5 (Code Review) before PHASE 4.7 (Media Generation)
2. Use multi-source upload for all NotebookLM operations
3. Add security review to mandatory PHASE 4.5 checks

**For development**:
1. Run `/adversarial-review --mode security` before committing code
2. Run `/trace` on critical files before deployment
3. Use `/r` to fix documentation and anti-patterns
4. Run `/q` for strategic quality assessment of major features

**For continuous validation**:
1. Add `PreToolUse_path_validator` to all skills accepting file paths
2. Enable `PostToolWrite_code_quality` for all code writes
3. Run `/comply` before pushing to GitHub
4. Use `/testing-skills` or `/test-analyzer` for test coverage validation

---

## END OF REVIEW BUNDLE

**Next Steps**:
1. Use this bundle to understand the complete code review ecosystem
2. Identify gaps in current tooling (cross-file analysis, vulnerability scanning)
3. Run appropriate skills before code commits
4. Integrate findings into development workflow

**For questions about specific components**, refer to individual SKILL.md files or agent definitions.
