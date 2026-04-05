# Core Patterns Analysis - Representative Skills Deep Dive

**Generated**: 2026-03-09
**Analyst**: Core Reader Agent
**Task**: #1552 - Deep dive representative skills

---

## Executive Summary

This document analyzes the core architectural and execution patterns of the CSF skills ecosystem based on deep dives into representative skills from major categories.

**Total Skills Analyzed**: 9 representative skills
**Categories Covered**: development, cognitive, infrastructure, documentation, quality, workflow
**Key Finding**: Skills follow a **hybrid execution model** combining:
1. **Pure LLM instruction skills** (no code)
2. **Script-backed skills** (Python execution)
3. **Hook-enforced skills** (mechanical continuation)
4. **Orchestration skills** (multi-agent coordination)

---

## 1. Skill Architecture Patterns

### Pattern 1: Pure LLM Instruction Skills

**Representatives**: `/adf`, `/acef`, `/ask`, `/agentic-validation`

**Structure**:
```
skill-name/
├── SKILL.md          # Complete instruction document
├── resources/        # Optional: reference docs, templates
└── (no code files)
```

**Execution Flow**:
1. User invokes trigger (e.g., `/adf`)
2. LLM loads SKILL.md
3. LLM follows documented workflow steps
4. Output returned directly to user

**Key Characteristics**:
- Single source of truth: SKILL.md
- No external dependencies
- Execution depends entirely on LLM compliance
- Relies on "behavioral enforcement" (text directives)

**Examples**:
- **ADF**: Architecture Decision Framework - 8-step decision tree with CKS integration
- **ACEF**: Agentic Command Engineering Framework - Framework documentation with external reference
- **ASK**: Universal CLI router - Complex triage/route logic with 5-step workflow
- **Agentic-validation**: Pattern reference - Shows code examples but doesn't execute them

---

### Pattern 2: Script-Backed Skills

**Representatives**: `/artifact-audit`, `/async-bugs`

**Structure**:
```
skill-name/
├── SKILL.md                    # User-facing documentation
└── resources/
    └── scripts/
        └── skill_script.py     # Executable implementation
```

**Execution Flow**:
1. User invokes trigger
2. LLM reads SKILL.md for usage
3. LLM invokes Python script via Bash tool
4. Script executes actual logic
5. Results returned to user

**Key Characteristics**:
- Separation of concerns: docs vs. implementation
- Deterministic execution (script output)
- Can be tested independently
- Exit codes for automation

**Code Pattern - artifact_audit.py**:
```python
def audit(args=None) -> int:
    # 1. Parse arguments
    # 2. Ensure schema exists
    # 3. Find project root
    # 4. Get pending items
    # 5. Group by severity
    # 6. Format output
    # 7. Return exit code (1 if pending, 0 if clean)
```

**Examples**:
- **artifact-audit**: Python script scans JSON state, groups by severity, returns exit code
- **async-bugs**: AST-based analysis engine with 4 detection categories

---

### Pattern 3: Hook-Enforced Skills (av2 Pattern)

**Representative**: `/av2`

**Structure**:
```
skill-name/
├── SKILL.md                                # Documentation
├── hooks/
│   ├── StopHook_{skill}_continuation.py    # BLOCKS premature stops
│   └── PostToolUse_{skill}_state_tracker.py # Updates progress
└── scripts/
    ├── optimize.py                         # Main entry point
    └── constitutional_check.py             # Validation
```

**Execution Flow**:
```
User invokes skill
    ↓
LLM begins executing stages
    ↓
LLM tries to stop prematurely
    ↓
StopHook fires → Reads state file
    ↓
IF incomplete:
    exit(2) + stderr "MANDATORY: Continue"
    ↓
LLM MUST continue to next stage
```

**Key Characteristics**:
- **Mechanical enforcement**: Cannot be bypassed by LLM discretion
- **State tracking**: JSON files track current stage
- **Exit code 2**: Signals LLM to continue
- **Session isolation**: Prevents cross-session bleed

**Constitutional Requirements** (av2):
1. Continuation Enforcement (StopHook + exit(2))
2. Gate Enforcement (block unauthorized paths)
3. Explicit Halt Gates (defined stop conditions)
4. Execution Directive ("EXECUTE, don't describe")
5. Complete Stage Sequence (clear start→finish)
6. Intermediate Step Enforcement (layer gating)

**State File Format**:
```json
{
  "current_stage": 3,
  "max_stage": 7,
  "complete": false,
  "halted": false,
  "halt_reason": null
}
```

**Examples**:
- **av2**: Transforms skills into mechanically-enforced pipelines
- **Production examples**: skill_enforcement_gate.py (referenced in agentic-validation)

---

### Pattern 4: Orchestrator Skills

**Representatives**: `/cwo`, `/cco`

**Structure**:
```
skill-name/
├── SKILL.md                    # Orchestration logic
└── (may reference external modules)
```

**Execution Flow**:
```
User invokes orchestrator
    ↓
Orchestrator analyzes request
    ↓
Decomposes into sub-tasks
    ↓
Spawns parallel sub-agents (via Task tool)
    ↓
Monitors completion
    ↓
Synthesizes results
```

**Key Characteristics**:
- **Dynamic parallelism**: No specified parallelism counts
- **Sub-agent orchestration**: Coordinate, don't execute
- **Tool usage verification**: Every sub-agent MUST use tools
- **Queue-based spawning**: Let task queue manage concurrency

**Examples**:
- **CWO**: 16-step unified orchestration with 5 phases (Pre-Execution → Post-Completion)
- **CCO**: Decomposes tasks into granular, parallelizable sub-tasks

---

## 2. Input/Output Patterns

### Input Specification

**Method 1: Direct Arguments**
```yaml
execution:
  default_args: "."
  examples:
    - "/async-bugs src/messaging/async_handler.py"
```

**Method 2: Execution Directive Block**
```yaml
execution:
  directive: |
    Detect async Python bugs using AST analysis.
    1. Check Session History
    2. Identify Target
    3. Run Detectors
    4. Present Results
```

**Method 3: Inline in SKILL.md**
```markdown
## Usage

```bash
python P:/.claude/skills/artifact-audit/resources/scripts/artifact_audit.py --project-root P:/
```
```

### Output Templates

**Structured Output** (async-bugs):
```markdown
## Async Bugs Detected: [File Path]

**Scanned:** [number] files
**Bugs Found:** [number]

### Summary
[High-level summary by severity and category]

### Detailed Report
[Each bug with line number, severity, code snippet, and fix]

### Recommendations
[Prioritized fixes with severity order]
```

**Grouped Output** (artifact-audit):
```
CRITICAL (1)
--------------------------------------------------
  TSK-001: Add user authentication
    ⏳ard ⏳changelog ⏳prd ?readme

STANDARD (1)
--------------------------------------------------
  TSK-002: Fix login bug
    ⏳changelog
```

---

## 3. Key Execution Patterns

### Pattern A: Sequential Multi-Stage

**Used by**: `/av2`, `/cwo`

**Flow**: Stage 1 → Stage 2 → ... → Stage N → Complete

**Enforcement**:
- Mechanical: StopHook + state files
- Behavioral: "MANDATORY" language, text markers

**Example - CWO**:
```
Phase 0 (Pre-Execution) → Phase 1 (Discovery) → Phase 2 (Planning)
→ Phase 3 (Execution) → Phase 4 (Completion) → Phase 5 (Post-Completion)
```

### Pattern B: Conditional Routing

**Used by**: `/ask`, `/adf`

**Flow**: Parse input → Evaluate condition → Route to appropriate handler

**Example - ADF Scope Check**:
```
IF (new boundaries/abstractions):
    Apply ADF
ELSE IF (sharing existing capabilities):
    Skip ADF, evaluate integration
```

**Example - ASK Triage**:
```
Reversibility 1.0-1.25 → FAST PATH
Reversibility 1.5-1.75 → STANDARD PATH
Reversibility 2.0 → CAREFUL PATH
```

### Pattern C: Analysis + Report

**Used by**: `/async-bugs`, `/artifact-audit`

**Flow**: Scan target → Detect patterns → Format report → Return

**Characteristics**:
- No modification of target
- Read-only analysis
- Structured output format

### Pattern D: Parallel Decomposition

**Used by**: `/cco`

**Flow**: Decompose → Spawn all → Monitor → Synthesize

**Key**: Dynamic queue-based spawning (no hardcoded parallelism)

---

## 4. Cross-Cutting Patterns

### CKS Integration

Multiple skills integrate with CKS (Constitutional Knowledge System):

**ADF**:
```markdown
## CKS: Extended Reference Documentation

Query: `/cks "architecture-decision-framework: Step 1 — Clarify the proposal"`
```

**Purpose**: Offload detailed documentation to knowledge system

### Evidence-Based Validation

**ASK** implements evidence tiers:
```
Tier 1: 95% confidence (logs, test output, git diff)
Tier 2: 85% confidence (documentation, specs, file existence)
Tier 3: 75% confidence (static analysis, code inspection)
Tier 4: 50% confidence (comments, unverified assertions)
```

**Blocking Logic**:
```python
IF truth_score < 0.7:
    BLOCK with evidence gaps
```

### Session Context Awareness

**ask** and **cwo** maintain session context:
- Auto-create sessions for multi-step workflows
- Track routing decisions
- Preserve context across handoffs

### State Management

**Hook-enforced skills** use state files:
```
P:/.claude/hooks/state/
    ├── {skill}_workflow.json        # av2 format
    └── {skill}-stage-progress.json  # Legacy format
```

**Session isolation** prevents cross-session bleed.

---

## 5. Validation & Enforcement Patterns

### Mechanical Enforcement (Strongest)

**Implementation**: StopHook + exit(2)

**Cannot be bypassed** by LLM discretion.

**Example - av2**:
```python
# In StopHook
if not complete:
    sys.exit(2)  # Forces continuation
```

### Behavioral Enforcement (Weaker)

**Implementation**: Text directives in SKILL.md

**Can be ignored** by LLM (attention decay, compression).

**Example**:
```markdown
## ⚡ EXECUTION DIRECTIVE

DO NOT summarize this file. Execute these steps in order.
```

### Hybrid Enforcement (Recommended)

**Combination**: Mechanical + Behavioral

**Example - agentic-validation**:
```python
# Mechanical: State transition hook
if state["phase"] == "draft" and validate(file):
    write_state(phase="review", allowed_tools=["Edit"])

# Behavioral: Text warnings
## ⚠️ CRITICAL: Skipping validation invalidates results
```

---

## 6. Integration Patterns

### Script Import Sharing

**artifact-audit** imports from shared `artifact` module:
```python
# artifact-audit/resources/scripts/artifact_audit.py
artifact_skill_dir = Path(__file__).parent.parent.parent.parent / "artifact" / "resources" / "scripts"
sys.path.insert(0, str(artifact_skill_dir))
from artifact_core import get_pending_items, find_project_root
```

**Pattern**: Shared code in sibling skill directories

### Hook Registration

**Hook-enforced skills** require registration in settings.json:
```json
{
  "hooks": {
    "Stop": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "python P:/.claude/skills/v/hooks/StopHook_v_continuation.py",
        "layer": "-3_v_continuation",
        "critical": true
      }]
    }]
  }
}
```

**Layer `-3`**: Ensures hook fires before other Stop hooks

### External Tool Integration

**async-bugs** uses AST analysis:
```python
import ast

def detect_async_bugs(file_path):
    tree = ast.parse(file_path.read_text())
    # AST traversal for bug detection
```

**av2** uses regex pattern matching for validation:
```python
def check_continuation_enforcement(skill_content):
    has_exit_2 = 'sys.exit(2)' in hook_content
    has_blocking = bool(re.search(r'BLOCK|MANDATORY', hook_content, re.I))
```

---

## 7. Quality Assurance Patterns

### Constitutional Validation

**av2** validates skills against 6 invariants:
```python
CHECKS = [
    ("continuation_enforcement", check_continuation_enforcement),
    ("gate_enforcement", check_gate_enforcement),
    ("explicit_halt_gates", check_explicit_halt_gates),
    ("execution_directive", check_execution_directive),
    ("complete_stage_sequence", check_complete_stage_sequence),
    ("intermediate_step_enforcement", check_intermediate_step_enforcement),
]
```

### Exit Code Conventions

```python
return 0  # Success / Clean
return 1  # Pending items / Check failed
return 2  # Error / Not found
```

### Testing Patterns

**av2** includes end-to-end tests:
```bash
# Test hook behavior
python P:/.claude/skills/av2/test_stophook_e2e.py

# Verify state reading
python P:/.claude/skills/av2/test_state_bridge.py
```

---

## 8. Discovery & Routing Patterns

### Trigger Patterns

**Direct triggers**: `/adf`, `/av2`
**Phrase triggers**: "async bugs", "artifact audit"
**Context triggers**: Auto-invoked by `/code` when async detected

### Intent-Based Routing

**ask** implements intent matching:
```
"should I extract X" → /adf
"architecture design" → /arch
"why does X fail" → /rca
"research X" → /research
```

### Command Discovery

**ask** integrates with skill_registry:
```python
# Use /search with skills backend
cd "P:/__csf" && python src/csf/cli/nip/search.py "query" --backend skills --layer 3
```

---

## 9. Documentation Patterns

### SKILL.md Structure

**Common sections**:
```markdown
---
name: skill-name
description: Brief description
category: category
triggers:
  - /skill
aliases:
  - /skill
suggest:
  - /related-skill
---

# Skill Name

## Purpose
## Project Context
## Your Workflow
## Validation Rules
## Usage
## Examples
```

### External References

**ACEF** references external documentation:
```markdown
**See main documentation:** `P:/__csf/src/csf/cli/nip/acef.md`
```

**ADF** references CKS:
```markdown
## CKS: Extended Reference Documentation

Detailed documentation stored in CKS. Use `/cks` to query.
```

---

## 10. Anti-Patterns & Prohibited Actions

### Skill-Level Prohibitions

**ADF**:
- NEVER block without evidence
- NEVER approve aesthetics-only changes
- NEVER skip complexity tax calculation

**av2**:
- Does NOT compress skills (destroys behavioral specs)
- Does NOT extract code (orthogonal to enforcement)
- Does NOT modify SKILL.md (preserves working text)

**agentic-validation**:
- DO NOT execute hooks without testing
- DO NOT modify production without validation

### Architecture Constraints

**Solo-dev constraints** (from CLAUDE.md):
- No enterprise patterns
- No background autonomous execution
- No self-healing systems
- LLM-generated code under user direction

---

## Summary: Core Patterns Taxonomy

| Pattern | Skills | Key Characteristic |
|---------|--------|-------------------|
| Pure LLM Instruction | adf, acef, ask, agentic-validation | No code, behavioral enforcement |
| Script-Backed | artifact-audit, async-bugs | Python execution, deterministic |
| Hook-Enforced | av2 | Mechanical enforcement via StopHook |
| Orchestrator | cwo, cco | Multi-agent coordination, dynamic parallelism |
| Router | ask | Intent-based routing, triage levels |
| Analyzer | async-bugs, artifact-audit | Read-only analysis, structured output |

---

## File Locations Summary

**Skills Directory**: `P:/.claude/skills/`

**Hook State**: `P:/.claude/hooks/state/`

**Shared Code**: Sibling skill directories (`artifact/resources/scripts/`)

**External Docs**: `P:/__csf/src/csf/cli/nip/` (ACEF, etc.)

---

**End of Core Patterns Analysis**
