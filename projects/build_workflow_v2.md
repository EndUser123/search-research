# /build Workflow Review Bundle - v2.0.0 (Improved)

**Generated:** 2026-01-12  
**Workflow:** `/build` — AI-assisted feature development (Idea to PR)  
**Status:** Enhanced (v2.0.0)  
**Scope:** 5-phase feature development workflow with improved gates, rollback, and observability  

---

## Executive Summary

**Purpose:** Transform an idea into a production-ready feature through systematic 5-phase workflow with quantified gates, explicit approval checkpoints, and comprehensive error recovery.

**Core Workflow:** TRIAGE → BOOTSTRAP → ALIGN → DESIGN → BUILD → SHIP

**Key Improvements (v2.0):**
- ✅ **Quantified complexity thresholds** (TRIAGE gates with LOC/file counts)
- ✅ **Explicit phase approval gates** (who decides, when, how)
- ✅ **Context fork protocol** (when to fork, handoff mechanics, merge strategy)
- ✅ **Error recovery playbooks** (spec drift, unknown escalation, test regression)
- ✅ **Checkpoint operationalization** (naming, triggers, restore mechanics)
- ✅ **Telemetry & observability** (metrics, rework tracking, success rates)
- ✅ **Skill versioning** (dependency constraints, breaking change handling)
- ✅ **Unknown discovery path** (mid-Phase 3 escalation to /arch reevaluation)

**Key Integration Points:**
- TaskMaster (TSK) for project tracking
- Git worktree for feature isolation
- TDD enforcement for quality
- CKS for knowledge persistence
- Checkpoint system for state recovery

---

## Table of Contents

1. [Complexity Scoring & Triage](#complexity-scoring--triage)
2. [Core Build Skill](#core-build-skill)
3. [Feature Development Flow with Gates](#feature-development-flow-with-gates)
4. [Dependency Commands](#dependency-commands)
5. [Checkpoint System (Operationalized)](#checkpoint-system-operationalized)
6. [Context Fork Protocol](#context-fork-protocol)
7. [Error Recovery Playbooks](#error-recovery-playbooks)
8. [Phase Approval Gates](#phase-approval-gates)
9. [Unknown Discovery Path](#unknown-discovery-path)
10. [Skill Versioning Strategy](#skill-versioning-strategy)
11. [Telemetry & Observability](#telemetry--observability)
12. [Supporting Systems](#supporting-systems)
13. [Execution Map](#execution-map)
14. [Integration Points](#integration-points)

---

## Complexity Scoring & Triage

### Quantified TRIAGE Decision Tree

**TRIAGE runs at start of `/build <feature_description>` to route to correct path.**

#### Step 1: Score Feature Complexity

Use this scoring matrix to quantify complexity:

| Dimension | Trivial | Moderate | Complex | Architectural |
|-----------|---------|----------|---------|---------------|
| **Scope (LOC)** | ≤50 | 50-500 | 500-2000 | >2000 |
| **File count** | 1 | 2-5 | 6-15 | 16+ |
| **External deps** | 0 | 1-2 | 3-5 | 6+ |
| **System scope** | Single function | Single module | Multi-module | Multi-system |
| **New patterns?** | None | Known patterns | 1-2 new | 3+ new patterns |
| **Integration?** | Self-contained | Within domain | Cross-domain | External API |
| **Unknowns** | 0 | 1-2 | 3+ | Significant |

**Scoring:**
- **0-5 points** = TRIVIAL
- **6-12 points** = MODERATE
- **13-18 points** = COMPLEX
- **19+ points** = ARCHITECTURAL

#### Step 2: Detect Complexity Signals

High-confidence signals that upgrade complexity:

| Signal | Upgrade | Reason |
|--------|---------|--------|
| "integrate X" | +3 pts | Cross-system boundary |
| "refactor Y" | +2 pts | Existing code changes |
| "new system" | +4 pts | Architectural decision |
| "migration" | +3 pts | Multi-phase work |
| "backward compat" | +2 pts | Constraint complexity |
| "performance" | +2 pts | Non-functional requirement |
| "security" | +2 pts | High risk domain |
| Multiple unknowns | +2 pts | Per unknown |

#### Step 3: Select Execution Path

| Complexity | Path | Entry Point | Approvals | Estimated Duration |
|------------|------|-------------|-----------|-------------------|
| **TRIVIAL** (≤5 pts) | FAST | Phase 3 (BUILD) | None | 15-30 min |
| **MODERATE** (6-12 pts) | STANDARD | Phase 0 (BOOTSTRAP) | Spec approval | 1-3 hours |
| **COMPLEX** (13-18 pts) | CAREFUL | Phase 1 (ALIGN) | Spec + arch approval | 3-8 hours |
| **ARCHITECTURAL** (19+ pts) | DESIGN_REVIEW | Phase 2 (DESIGN) | Design approval + peer review | 8+ hours |

**Decision Command:**
```bash
/triage "<feature_description>"
```

Output:
```
[TRIAGE] Scoring analysis...
┌─────────────────────────────────────────┐
│ COMPLEXITY SCORE: 14/25 → COMPLEX       │
├─────────────────────────────────────────┤
│ Suggested Path: CAREFUL                 │
│ Entry Point: Phase 1 (ALIGN)            │
│ Required Approvals: Spec, Architecture  │
│ Est. Duration: 4-6 hours                │
│ Recommended: /specify → review → /arch  │
└─────────────────────────────────────────┘
```

---

## Core Build Skill

### 1. Build Skill Definition (v2.0)

**Source:** `P:\.claude\skills\build\SKILL.md`

```yaml
---
name: build
version: 2.0.0
description: AI-assisted feature development workflow (Idea to PR) with quantified gates and error recovery.
category: development
domain: development
subdomain: feature-lifecycle

triggers:
  - "build feature"
  - "new feature"
  - "implement feature"
  - "start development"
aliases:
  - /build
  - /feature
  - /develop
argument-hint: "<feature_description>"

context: main
user-invocable: true
status: stable

# NEW: Explicit skill versioning with constraints
depends_on_skills:
  - /triage@^2.0         # TRIAGE must be v2.0+
  - /tm@^1.0             # TaskMaster v1.0+
  - /specify@^1.0        # Spec command v1.0+
  - /plan@^2.0           # Plan with challenge/debate v2.0+
  - /tdd@^1.5            # TDD state guard v1.5+
  - /exec@^1.0           # CWO15 exec v1.0+
  - /verify@^1.0         # Verification v1.0+
  - /learn@^1.0          # Unified learning v1.0+
  - /git@^1.0            # Smart git v1.0+
  - /checkpoint@^2.0     # Enhanced checkpoint system v2.0+
  - /arch@^2.0           # ADF-enabled architecture v2.0+

requires_tools:
  - python@^3.11
  - git@^2.40
  - pytest@^7.0

---
```

### 2. Phase Structure (v2.0)

| Phase | Goal | Entry Conditions | Key Tools | Exit Criteria |
|-------|------|------------------|-----------|---------------|
| **0. TRIAGE** | Pre-flight complexity scoring | Always | `/triage`, `/discover` | Complexity score ≤25, path selected |
| **1. BOOTSTRAP** | Ensure system ready | All paths | `/tm`, `/git worktree`, `/checkpoint` | TSK created, worktree active, clean state |
| **2. ALIGN** | Define problem clearly | MODERATE+ | `/specify`, human review | spec.md approved, questions resolved |
| **3. DESIGN** | Plan solution | COMPLEX+ | `/brainstorm`, `/arch`, `/plan`, `/checkpoint` | plan.md approved, arch validated |
| **4. BUILD** | TDD-driven implementation | All paths | `/ralph`, `/tdd`, `/exec`, `/verify` | All tasks ✓, tier 1-2 tests pass |
| **5. SHIP** | Certify & finalize | All paths | `/verify --tier 1,2,3`, `/learn`, `/tm close` | Tier 1-3 tests pass, knowledge saved |

**Success Criteria (Updated):**
- [ ] TRIAGE complexity scored and path selected
- [ ] TSK session created and active
- [ ] Feature branch isolated in git worktree
- [ ] Appropriate approvals obtained per path
- [ ] All checkpoints created at phase boundaries
- [ ] All tasks in `plan.md` marked complete
- [ ] Tests pass: `/verify --tier 1,2,3`
- [ ] Knowledge updated via `/learn`
- [ ] Telemetry recorded (duration, path, rework count)

---

## Feature Development Flow with Gates

### PHASE 0: TRIAGE (Pre-Routing)

**Objective:** Assess complexity and select execution path using quantified scoring.

**Execution:**
```bash
/triage "<feature_description>"
```

**Output:** Complexity score, recommended path, estimated duration

**Success Condition:** Complexity scored ≤25, path selected by AI or confirmed by user

**No Gate** — Automatic progression to Phase 1 (BOOTSTRAP)

---

### PHASE 1: BOOTSTRAP

**Objective:** Ensure system is ready for development.

**Checklist:**
1. Create/Attach TaskMaster session
   ```bash
   /tm
   ```
2. Create feature worktree
   ```bash
   /git worktree add -b <feature-branch> .git/worktrees/<feature-name> main
   ```
3. Verify worktree is clean and active
   ```bash
   cd .git/worktrees/<feature-name>
   git status
   ```
4. Create Phase 0 checkpoint
   ```bash
   /checkpoint "Phase 0: Bootstrap complete"
   ```

**No Gate** — Automatic progression to Phase 2 (ALIGN)

---

### PHASE 2: ALIGN

**Objective:** Define the problem clearly. (For TRIVIAL path: SKIP to Phase 4)

**Execution:**
1. Draft specification
   ```bash
   /specify "<feature_description>"
   ```
2. Review specification artifacts
   - `specify.md` — Requirements, user stories, acceptance criteria
   - `project.json` — Metadata

**⚠️ APPROVAL GATE 1: Specification Approval**

**Responsibility:** User/Human

**Approval Checklist:**
- [ ] Requirements are clear and unambiguous
- [ ] User stories have measurable acceptance criteria
- [ ] Success metrics are testable
- [ ] Open questions are resolved or documented
- [ ] No scope creep (in-scope vs out-of-scope clear)
- [ ] Technical considerations are complete
- [ ] Edge cases identified

**Decision Options:**
```
✅ /approve-spec
   → Auto-tag TSK as "spec_approved"
   → Progress to Phase 3 (DESIGN)
   → Record approval timestamp

🔄 /refine-spec "<feedback>"
   → Loop back to /specify
   → Incorporate feedback
   → Return to approval gate

❌ /reject-spec "<reason>"
   → Mark TSK as "spec_rejected"
   → Store rejection rationale in TSK journal
   → Ask if user wants to pivot or restart
```

---

### PHASE 3: DESIGN

**Objective:** Plan the solution before coding. (For TRIVIAL path: SKIP to Phase 4)

**Execution:**
1. Optional brainstorming (3+ novel approaches)
   ```bash
   /brainstorm "approaches for <feature>"
   ```
2. Validate architecture with ADF
   ```bash
   /arch "Should we use <pattern> for <feature>?"
   ```
   Output: 13 mandatory artifacts (see /arch docs)

3. Decompose into granular tasks
   ```bash
   /plan "<feature>" --challenge
   ```
   Output: `plan.md` with 2-5 minute tasks

4. Create Phase 3 checkpoint
   ```bash
   /checkpoint "Phase 3: Design complete"
   ```

**⚠️ APPROVAL GATE 2: Design & Plan Approval**

**Responsibility:** User/Human

**Approval Checklist:**
- [ ] Architecture is sound (no SOLID violations)
- [ ] Tasks are granular (2-5 min each)
- [ ] Dependencies between tasks are clear
- [ ] Risk matrix is acceptable (<3 "Critical" items)
- [ ] Rollback plan is credible
- [ ] Technical debt estimation is realistic
- [ ] ADF findings acknowledged

**Decision Options:**
```
✅ /approve-plan
   → Auto-tag TSK as "plan_approved"
   → Progress to Phase 4 (BUILD)
   → Record approval timestamp

🔄 /refine-plan "<feedback>"
   → Loop back to /plan
   → Adjust task decomposition
   → Return to approval gate

⚠️  /escalate-design "<concern>"
   → Return to /arch reevaluation
   → Address architectural concern
   → Re-run /plan
   → Return to approval gate
```

---

### PHASE 4: BUILD

**Objective:** TDD-driven implementation of each task.

**Execution Pattern (per task in plan.md):**

1. **Start task**
   ```bash
   /ralph "<current_task>"
   ```

2. **TDD Cycle (RED → GREEN → REFACTOR)**
   - **RED:** Write failing test
     ```bash
     /tdd
     ```
   - **GREEN:** Implement code
     ```bash
     /exec "implement <task>"
     ```
   - **REFACTOR:** Clean up
     ```bash
     /refactor "<area>"
     ```

3. **Verify task completion**
   ```bash
   /verify --tier 1,2 <affected_files>
   ```

4. **Mark task complete in plan.md**
   ```markdown
   - [x] <task_name>
   ```

**No Gate** — Automatic progression to Phase 5 (SHIP) when all tasks complete

**Mid-Build Unknown Discovery (NEW):**
If `/ralph` reveals architectural unknowns during BUILD:
1. Pause current task (checkpoint)
   ```bash
   /checkpoint "Pausing task due to unknown"
   ```
2. Escalate to `/arch --reevaluate`
   - This returns you to Phase 3 (DESIGN)
   - Ad-hoc architecture validation
   - Decide: continue, pivot, or restructure
3. Update `plan.md` with new findings
4. Resume Phase 4 from next task

---

### PHASE 5: SHIP

**Objective:** Certify system ready for production and finalize.

**Execution:**

1. **Full verification (all tiers)**
   ```bash
   /verify --tier 1,2,3
   ```

2. **Conventional commit**
   ```bash
   git commit -m "feat: <description>

   - <key change 1>
   - <key change 2>
   
   Closes TSK-<YYMMDD>-<Name>"
   ```

3. **Unified learning ingest**
   ```bash
   /learn
   ```
   (Automatically ingests to CKS.unified with searchable lessons)

4. **Close TaskMaster session**
   ```bash
   /tm close
   ```
   (Records duration, path taken, metrics)

5. **Clean worktree**
   ```bash
   /git worktree remove .git/worktrees/<feature-name>
   ```

**Final Telemetry:**
- Total duration (Phase 0 → Phase 5)
- Path taken (FAST/STANDARD/CAREFUL/DESIGN_REVIEW)
- Rework count (returns to earlier phases)
- Test coverage (final /verify output)
- Knowledge ingested (CKS.unified entry count)

---

## Dependency Commands

### 3. /triage — Complexity Scoring & Path Selection (NEW in v2.0)

**Source:** `P:\.claude\commands\triage.md`

**Purpose:** Pre-routing complexity assessment using quantified scoring.

**Usage:**
```bash
/triage "<feature_description>"
```

**Output:**
- Complexity score (0-25 points)
- Recommended path (TRIVIAL/MODERATE/COMPLEX/ARCHITECTURAL)
- Entry point (which phase)
- Required approvals
- Estimated duration
- Next command to run

**Algorithm:**
1. Parse feature description for scope/dependencies/signals
2. Score across 7 dimensions (LOC, files, deps, scope, patterns, integration, unknowns)
3. Apply signal multipliers (integrate +3, refactor +2, etc.)
4. Determine path based on score bands
5. Output recommendation with confidence %

---

### 4. /specify — Create TSK and Specification

**Source:** `P:\.claude\commands\specify.md`

**Purpose:** Phase 2 command - Create TSK project and specification.

**Key Actions:**
1. Query TaskMaster for existing active TSK
2. Create new TSK if needed (format: `TSK-YYMMDD-FeatureName-HHMM`)
3. Create context-aware TSK directory
4. Generate `specify.md` with requirements
5. Generate `project.json` with metadata
6. Update TaskMaster with TSK as active

**Template Sections:**
- Overview
- Requirements (Functional/Non-Functional)
- User Stories with acceptance criteria
- Scope (In/Out)
- Success Criteria
- Technical Considerations
- Open Questions
- Dependencies

**Output:** `specify.md` ready for Phase 2 Approval Gate

---

### 5. /arch — Architecture Validation with ADF

**Source:** `P:\.claude\commands\arch.md`

**Purpose:** Phase 3 command - Comprehensive architectural analysis.

**Key Features:**
- Mental model application
- Pre-mortem analysis
- Risk matrix
- Forced alternatives (3+ approaches)
- Rollback plan
- Tech debt estimation
- Timeline estimation
- Constitutional compliance check
- ADR auto-draft
- Adversarial challenge

**Mandatory Output Artifacts (13 total):**
1. Mental Model Application
2. Pre-Mortem Analysis
3. Risk Matrix
4. Forced Alternatives (3+ approaches)
5. Rollback Plan
6. Tech Debt Estimation
7. Timeline Estimation
8. Constitutional Compliance
9. Auto-Draft ADR
10. CWO Cognitive Checklist
11. CKS Knowledge Handoff
12. Confidence Calibration
13. Adversarial Challenge

**Output:** `arch_decision.md` ready for Phase 3 Approval Gate

---

### 6. /brainstorm — AI-Powered Opportunity Analysis

**Source:** `P:\.claude\commands\llm-brainstorm.md`

**Purpose:** Phase 3 command - Generate and rank diverse approaches.

**Execution Steps:**
1. **PARSE** → Extract topic and constraints
2. **VALIDATE** → Check orchestrator is ready
3. **RUN** → Execute brainstorm with tracking
4. **REPORT** → Display results ranked by feasibility
5. **TRACK** → Record performance data

**Personas Available:**
- **innovator:** Creative, unconventional ideas
- **pragmatist:** Practical, implementable solutions
- **critic:** Critical analysis, identifies risks

**Output:** `brainstorm_results.md` with 15 ranked approaches

---

### 7. /plan — Granular Implementation Planning

**Source:** `P:\.claude\commands\plan.md`

**Purpose:** Phase 3 command - Task decomposition into 2-5 minute increments.

**Enhancement Modes:**
```bash
/plan "<feature>" --challenge        # Prevent over-engineering
/plan "<feature>" --debate           # High-stakes planning
/plan "<feature>" --synthesize       # Research-backed planning
```

**Output:** `plan.md` with sequential tasks, dependencies, and checkpoints

---

### 8. /ralph — Task Decomposition and Inner Loop

**Source:** `P:\.claude\commands\ralph.md`

**Purpose:** Phase 4 command - Interactive TDD-driven development loop.

**Usage:**
```bash
/ralph "<current_task>"
```

**Inner Loop:**
1. Understand current task
2. Identify test requirements
3. Write failing test (RED)
4. Implement to pass (GREEN)
5. Refactor for quality (REFACTOR)
6. Verify (tier 1-2)
7. Mark complete
8. Move to next task

---

### 9. /tdd — TDD State Guard Management

**Source:** `P:\.claude\commands\tdd.md`

**Purpose:** Phase 4 command - Manage TDD enforcement state.

**Subcommands:**
```bash
/tdd status                    # Show current state
/tdd approve <test_file>       # 5-min approval bypass
/tdd reset                     # Clear all state → IDLE
/tdd reset <test_file>         # Clear state for specific file
/tdd on                        # Enable TDD enforcement
/tdd off                       # Disable TDD enforcement
```

**State Directory:** `P:/.claude/hooks/.state/tdd-state/`

**Audit Log:** `P:/.claude/hooks/.state/tdd-state/tdd_audit.log`

---

### 10. /exec — CWO15 Execution Entry

**Source:** `P:\.claude\commands\exec.md`

**Purpose:** Phase 4 command - Context-aware code execution.

**Key Behavior:**
- Analyzes context automatically (conversation, git, errors, active TSK)
- Proposes execution based on context
- Proceeds if clear, asks if ambiguous

**Usage:**
```bash
/exec                              # Context-aware mode
/exec "implement auth system"       # Explicit task
/exec "feature" --continue         # Continue through phase
/exec "hotfix" --force             # Bypass validation
```

---

### 11. /verify — System Certification

**Source:** `P:\.claude\commands\verify.md`

**Purpose:** Phase 4-5 command - Multi-tier verification and certification.

**Verification Tiers:**
| Tier | Check | Tool | Fail = |
|------|-------|------|--------|
| 1 | Syntax | `ast.parse()` | Broken code |
| 2 | Types/Lint | `mypy --strict`, `ruff` | Type errors, style |
| 3 | Tests | `pytest <related>` | Functional regression |

**Usage:**
```bash
/verify --tier 1              # Syntax only (fast)
/verify --tier 1,2            # Syntax + types (no tests)
/verify --tier 1,2,3          # Full verification
/verify --review              # Show metrics, evaluate process
/verify <file_path>           # Verify specific file
```

---

### 12. /learn — Unified Session Learning

**Source:** `P:\.claude\commands\learn.md`

**Purpose:** Phase 5 command - Extract and ingest lessons.

**Auto-Ingests via CKS.unified:**
```python
from features.cks.unified import ingest_memory

entry_id = ingest_memory(
    question=question,
    answer=answer,
    tags=["lesson", "technical", ...],
    knowledge_type="lesson",
    title=lesson_title,
    category="technical_lessons",
)
```

**Critical:** Use `CKS.unified` (not `DirectCKSIngestion`) for searchable lessons.

**Output:** CKS entry ID and confirmation

---

### 13. /git — Smart Git Workflow

**Source:** `P:\.claude\commands\git.md`

**Purpose:** Git workflow guidance and worktree management.

**Worktree Creation Best Practices:**
```bash
# Step 1: Clean current state
git status
git worktree prune

# Step 2: Create worktree with proper branch
git worktree add -b <new-branch> <path> <base-branch>

# Step 3: Verify worktree creation
git worktree list -v

# Step 4: Navigate and verify
cd <path>
git status
```

**TSK-First Workflow:**
```bash
# 1. Create TSK first
/tm

# 2. Create worktree for TSK
git worktree add -b <feature-branch> .git/worktrees/<feature-name> main

# 3. Navigate to worktree
cd .git/worktrees/<feature-name>

# 4. Start working
/triage "<feature>"
```

---

### 14. /discover — Intelligent Codebase Discovery

**Source:** `P:\.claude\commands\discover.md`

**Purpose:** TRIAGE command - Pre-routing codebase discovery.

**Key Features:**
- Hybrid Pattern Detection (95%+ accuracy)
- GPU Acceleration (20x faster for large codebases)
- Intelligent Caching (71.4% cache hit rate)
- Semantic Understanding (GraphCodeBERT + CodeT5)
- RAG Integration

**Thoroughness Levels:**
| Mode | Time | Coverage | Use Case |
|------|------|----------|----------|
| `quick` | <1 min | Core patterns | Fast answers |
| `medium` | 5-15 min | Comprehensive | Deep analysis |
| `very_thorough` | 30-60 min | ML + GPU | Large codebases |

---

## Checkpoint System (Operationalized)

### Checkpoint Mechanics (v2.0)

**Purpose:** State recovery and session continuity across interruptions.

#### Auto-Checkpoint Triggers (NEW)

Checkpoints are created automatically at these points:

| Trigger | Checkpoint Name | Phase |
|---------|-----------------|-------|
| After Phase 1 completes | `cp_phase_1_<timestamp>` | BOOTSTRAP |
| After Phase 2 completes | `cp_phase_2_<timestamp>` | ALIGN |
| After Phase 3 completes | `cp_phase_3_<timestamp>` | DESIGN |
| Before unknown escalation | `cp_unknown_escalation_<timestamp>` | BUILD |
| Every 25 completed tasks | `cp_task_batch_<N>_<timestamp>` | BUILD |
| Before Phase transition | `cp_pre_phase_<N>_<timestamp>` | Any |
| User-requested | `cp_manual_<timestamp>` | Any |

#### Checkpoint Naming Convention

```
cp_<event>_<timestamp>
│   │       │
│   │       └─ ISO 8601 timestamp (20260112_143022)
│   └─ Event type (phase_1, unknown_escalation, manual, etc.)
└─ Checkpoint prefix
```

**Examples:**
- `cp_phase_1_20260112_143022.json`
- `cp_unknown_escalation_20260112_145511.json`
- `cp_task_batch_25_20260112_150003.json`
- `cp_manual_20260112_151545.json`

#### Checkpoint Metadata Structure

```json
{
  "schema_version": "2.3.2",
  "checkpoint_name": "cp_phase_1_20260112_143022",
  "created_at": "2026-01-12T14:30:22Z",
  "commit_hash": "a1b2c3d",
  "branch": "feature-auth-system",
  "tsk_id": "TSK-260112-AuthSystem-1430",
  "type": "phase_transition",
  "source": "auto_phase_1_complete",
  "message": "Phase 1 (BOOTSTRAP) complete - system ready",
  "phase": 1,
  "modified_files": [
    "src/auth/models.py",
    "tests/test_auth.py"
  ],
  "validation_checklist": {
    "worktree_active": true,
    "tsk_created": true,
    "git_clean": true,
    "dependencies_installed": true
  },
  "metrics": {
    "duration_minutes": 12,
    "tasks_completed": 0,
    "test_count": 0
  }
}
```

#### Restore Command

```bash
/checkpoint-restore <checkpoint_name>

# Examples:
/checkpoint-restore cp_phase_1_20260112_143022
/checkpoint-restore cp_unknown_escalation_20260112_145511
```

**Restore Behavior:**
1. Validates checkpoint exists and is valid
2. Backs up current state (pre-restore)
3. Rolls back working directory to checkpoint commit
4. Rolls back modified files to checkpoint state
5. Preserves TSK journal (append-only)
6. Updates TSK with restore note
7. Logs restore action to audit trail

**Storage Location:** `C:\Users\<user>\.claude\checkpoints\`

**Retention Policy:** Last 20 checkpoints per project only (older auto-deleted)

---

## Context Fork Protocol

### When to Fork

Context fork should be triggered when:

| Condition | Threshold | Trigger Command |
|-----------|-----------|-----------------|
| TSK size | >50 KB | `/fork-context --task-heavy` |
| Codebase files | >200 loaded | `/fork-context --code-heavy` |
| Session duration | >4 hours | `/fork-context --time-heavy` |
| Phase 3 loop duration | >2 hours | `/fork-context --build-heavy` |
| Conversation turns | >150 | `/fork-context --chat-heavy` |

### Fork Handoff Protocol (NEW)

**Before forking, execute:**

```bash
/checkpoint "Pre-fork checkpoint"
/fork-context --task-heavy
```

**Parent → Child handoff includes:**
```
✅ TSK directory (full)
✅ plan.md (current state with checkmarks)
✅ specify.md (requirements reference)
✅ All created tests
✅ Current implementation state (git commit SHA)
✅ Checkpoint list (for restoration)
✅ TSK journal (append-only)

❌ Full codebase (use file pruning in child)
❌ Archived code
❌ Old checkpoint files
```

**Child context receives:**
- Clear task queue (next N tasks)
- Current git branch and commit
- Test results summary
- Known blockers

### Fork Merge-Back Procedure

**Child → Parent return when context reclaimed:**

```bash
/fork-context --merge-back --target=<parent_session_id>
```

**Merge validation:**
1. Verify no conflicting edits (file-level)
2. Test child's changes locally
3. Commit child work to branch
4. Append child journal entries to parent TSK
5. Restore parent context with child's latest checkpoint
6. Continue Phase 3/4 from next task

**Result:** Seamless continuation in parent context

---

## Error Recovery Playbooks

### Error Case 1: Spec Drift (Phase 3+)

**Definition:** Implementation diverges from approved specification.

**Detection:**
- Acceptance criteria in spec.md not met by implementation
- User reports feature doesn't match spec
- `/verify --review` flags implementation against spec

**Recovery Steps:**

1. **Assess drift severity**
   ```bash
   /validate-spec --against plan.md
   ```
   Output: Detailed drift analysis with impact

2. **Decision tree:**
   - **Minor drift** (1-2 criteria affected):
     - Fix implementation to match spec
     - Update plan.md
     - Resume Phase 4
   
   - **Major drift** (3+ criteria affected):
     - Create checkpoint
       ```bash
       /checkpoint "Spec drift detected - escalating"
       ```
     - Return to Phase 2 (ALIGN)
       ```bash
       /refine-spec "Updated requirements: ..."
       ```
     - Re-run `/arch` to reassess design
     - Update `plan.md`
     - Resume Phase 4 with new plan

3. **Log drift event**
   - Record in TSK journal
   - Tag TSK with `spec_drift_detected`
   - Update telemetry

---

### Error Case 2: Test Regression (Phase 4+)

**Definition:** Previously passing tests now fail.

**Detection:**
- `/verify --tier 3` shows test failures
- `/tdd` catches test regression

**Recovery Steps:**

1. **Identify regressed tests**
   ```bash
   /verify --tier 3 --show-failures
   ```

2. **Determine cause**
   - Recent code change caused it?
   - Dependency upgrade?
   - Test was flaky?

3. **Fix regression**
   - Option A: Revert recent change
     ```bash
     /checkpoint "Pre-revert checkpoint"
     git revert <commit_sha>
     ```
   - Option B: Fix implementation
     ```bash
     /exec "fix regression in <module>"
     ```

4. **Verify fix**
   ```bash
   /verify --tier 1,2,3
   ```

5. **Continue or escalate**
   - If regression fixed: Resume Phase 4
   - If unfixable: 
     ```bash
     /checkpoint "Unresolvable regression - escalating"
     /arch --reevaluate "Regression root cause analysis"
     ```

---

### Error Case 3: Unknown Discovery During BUILD

**Definition:** During Phase 4 (BUILD), `/ralph` reveals architectural unknowns.

**Example scenarios:**
- Assumed API doesn't exist
- Expected database schema incompatible
- Performance constraint makes approach infeasible
- Security requirement conflicts with design

**Recovery Steps:**

1. **Pause current task**
   ```bash
   /checkpoint "Unknown discovered: <description>"
   ```

2. **Escalate to architecture reevaluation**
   ```bash
   /arch --reevaluate "Unknown: <description>"
   ```
   (This launches Phase 3 DESIGN loop within Phase 4 context)

3. **Arch decision:**
   - **Continue as-is:** Risk acceptable, proceed
   - **Pivot approach:** Different pattern works
   - **Restructure:** Return to Phase 2 (ALIGN)

4. **Update plan.md**
   - Modify affected tasks
   - Add new tasks if needed
   - Adjust timeline estimates

5. **Resume Phase 4**
   - Start `/ralph` on next task
   - Continue TDD cycle

---

### Error Case 4: Context Overload (Any Phase)

**Definition:** Token budget approaching limit, context getting fragmented.

**Detection:**
- Token counter shows >80% capacity
- Context window showing warning
- Conversation becoming hard to follow

**Recovery:**

**Option A: Trigger context fork (recommended)**
```bash
/checkpoint "Pre-fork - context full"
/fork-context --task-heavy
```

**Option B: Archive and restart**
```bash
/checkpoint "Pre-archive - full context"
/tm save-session
# Start fresh session with `/tm load-session <id>`
```

**Option C: Switch to text-based summary**
- Dump current state to `context_snapshot.md`
- Continue in limited context with snapshot as reference

---

### Error Case 5: External Dependency Failure

**Definition:** External service/API/library that design depends on is unavailable/deprecated.

**Example:** API endpoint the feature was designed to call is deprecated.

**Recovery:**

1. **Identify failure**
   - During implementation
   - During testing
   - During `/verify`

2. **Assess scope**
   - Can we work around it?
   - Does it require redesign?
   - Can we abstract it?

3. **Decision:**
   - **Workaround:** Implement alternative approach
     ```bash
     /exec "implement workaround for <dependency>"
     ```
   - **Redesign:** Return to Phase 3
     ```bash
     /checkpoint "Dependency failure - redesign needed"
     /arch --reevaluate "Dependency <X> failed/deprecated"
     ```

4. **Update plan.md** and resume Phase 4

---

## Phase Approval Gates

### Gate Template (Used at Phase 2 & 3)

**Responsibility:** User/Human (final decision)

**Timing:** At end of phase, before progression

**Format:** Explicit `/approve-X` or `/reject-X` or `/refine-X` command

---

### Gate 1: Specification Approval (End of Phase 2: ALIGN)

**What's being approved:** `specify.md` document

**Approver:** User/Product Owner

**Checklist:**
```
□ Requirements are clear (no ambiguous language)
□ User stories have measurable acceptance criteria
□ Success metrics are testable
□ No unresolved open questions
□ Scope is explicit (in/out)
□ Technical considerations complete
□ Edge cases identified
□ Dependencies listed
```

**Approval Commands:**
```bash
✅ /approve-spec
   → TSK tagged: spec_approved
   → Progress to Phase 3

🔄 /refine-spec "<feedback>"
   → Loop back to /specify
   → Incorporate feedback
   → Return to this gate

❌ /reject-spec "<reason>"
   → Mark: spec_rejected
   → Store rejection reason in TSK
   → Ask: restart or pivot?
```

---

### Gate 2: Design & Plan Approval (End of Phase 3: DESIGN)

**What's being approved:**
- `arch_decision.md` (architecture)
- `plan.md` (task decomposition)
- Risk matrix and rollback plan

**Approver:** User/Technical Lead

**Checklist:**
```
□ Architecture follows SOLID principles
□ No unresolved architectural concerns
□ Tasks are granular (2-5 min each)
□ Task dependencies are clear
□ Risk matrix shows acceptable risk (<3 Critical)
□ Rollback plan is credible
□ Tech debt estimation is reasonable
□ Timeline estimate is realistic
□ Adversarial challenge response is sound
```

**Approval Commands:**
```bash
✅ /approve-plan
   → TSK tagged: plan_approved
   → Progress to Phase 4 (BUILD)

🔄 /refine-plan "<feedback>"
   → Loop back to /plan
   → Adjust task decomposition
   → Possibly re-run /arch
   → Return to this gate

⚠️  /escalate-design "<concern>"
   → Return to /arch reevaluation
   → Address specific architectural concern
   → Re-run /plan
   → Return to this gate

❌ /reject-plan "<reason>"
   → Mark: plan_rejected
   → Store rejection reason
   → Ask: refine or restart?
```

---

## Unknown Discovery Path

### Detecting Unknowns During BUILD (NEW)

**Unknowns typically manifest as:**
- Test failures that suggest architectural mismatch
- Code that doesn't "fit" the design
- API/library behavior differs from assumption
- Performance/constraint violation
- Security implication discovered

**Example:**
```
During /ralph on "Implement user auth":
  → Write test for OAuth login
  → Test reveals OAuth endpoint expects different response format
  → Assumption about API contract was wrong
  → This is an "Unknown"
```

### Recovery Flow

**Step 1: Pause and Checkpoint**
```bash
/checkpoint "Unknown: OAuth response format assumption incorrect"
```

**Step 2: Escalate to Architecture Reevaluation**
```bash
/arch --reevaluate "OAuth API contract differs from assumption"
```

**Output from /arch --reevaluate:**
- Pre-mortem on original assumption
- Alternative approaches (wrapper, adapter, different API)
- Risk assessment per approach
- Recommended path forward

**Step 3: Decide**
| Decision | Action |
|----------|--------|
| Continue with wrapper | Update implementation, resume Phase 4 |
| Pivot to different API | Update design, re-run /plan, resume Phase 4 |
| Restructure approach | Return to Phase 2 (ALIGN), handle as spec drift |

**Step 4: Update Documentation**
- Update `plan.md` with new findings
- Add lessons to TSK journal
- Log unknown to telemetry

**Step 5: Resume**
```bash
# Mark task as paused
- [ ] ~~Implement user auth with OAuth~~ → Paused due to unknown

# Add new task with solution
- [ ] Implement user auth with OAuth adapter wrapper

# Continue Phase 4
/ralph "Implement user auth with OAuth adapter wrapper"
```

---

## Skill Versioning Strategy

### Version Constraint Syntax

```yaml
depends_on_skills:
  - /tm@^1.0              # Major version must be 1
  - /specify@^1.0         # 1.0, 1.1, 1.2 OK; 2.0 not OK
  - /plan@^2.0            # 2.0, 2.1, 2.2 OK; 1.x or 3.x not OK
  - /arch@~2.5            # 2.5.x only; not 2.4 or 2.6
  - /verify@2.1.3         # Exact version only
```

**Semantics:**
- `^X.Y` = Major version X, any minor/patch ≥Y
- `~X.Y` = Major version X, Minor version Y, any patch
- `X.Y.Z` = Exact version
- No prefix = any compatible version

### Breaking Change Handling

**When a skill has breaking changes:**

1. **Update major version** (e.g., 1.0 → 2.0)
2. **In SKILL.md:** Update `depends_on_skills` with new version constraint
3. **Migration guide:** Document in skill's CHANGELOG
4. **Backward compat period:** (optional) Support both versions for 1 month

**Example:**
```yaml
# Before (v1.0)
/plan "feature" --challenge

# After (v2.0 with breaking change)
/plan "feature" --challenge --mode=aggressive
                                    ↑ new required parameter

# SKILL.md update:
depends_on_skills:
  - /plan@^2.0    # Enforce new version
```

---

## Telemetry & Observability

### Metrics Captured (NEW)

**Automatic telemetry recorded in TSK journal and central telemetry DB:**

| Metric | Captured At | Data Collected |
|--------|------------|-----------------|
| **Total duration** | Phase 5 complete | Start → End timestamp |
| **Path taken** | Phase 0 complete | FAST/STANDARD/CAREFUL/DESIGN_REVIEW |
| **Complexity score** | Phase 0 complete | 0-25 score + breakdown |
| **Phase durations** | Each phase transition | Time spent in each phase |
| **Rework count** | Each phase return | N regressions to earlier phases |
| **Approval gates** | Each gate approval | Gate type + decision (approve/refine/reject) |
| **Test coverage** | Phase 5 | Final `/verify --review` output |
| **CKS entries** | Phase 5 | Knowledge ingested count + quality score |
| **Checkpoint count** | Phase 5 | Total checkpoints created + restores |
| **Unknown discoveries** | Each /arch reevaluation | Count + recovery path |

### Querying Telemetry

```bash
# Show metrics for this feature
/metrics --session <tsk_id>

# Show metrics by path
/metrics --by-path
→ TRIVIAL: avg 18 min, 5 completions
→ STANDARD: avg 142 min, 12 completions
→ CAREFUL: avg 287 min, 8 completions
→ DESIGN_REVIEW: avg 520 min, 2 completions

# Show rework analysis
/metrics --rework
→ Phase 2 → Phase 1 regressions: 3 (15% of sessions)
→ Phase 4 → Phase 3 regressions: 8 (23% of sessions)
→ Most common: Spec drift (5), Unknown discoveries (3)

# Show gate decision distribution
/metrics --gates
→ Approvals: 23 (79%)
→ Refinements: 5 (17%)
→ Rejections: 1 (3%)
```

### Using Telemetry to Improve

**Quarterly review process:**

1. **Analyze rework patterns**
   - Which phases see most regressions?
   - Are approvals too loose (missing drift)?
   - Are gates too strict (causing unnecessary refinement)?

2. **Improve TRIAGE thresholds**
   - Is complexity scoring accurate?
   - Are some paths finishing faster than estimated?
   - Should paths be rebalanced?

3. **Optimize checkpoint policy**
   - Are checkpoints helping or just noise?
   - Should auto-checkpoint triggers change?

4. **Skill updates**
   - Which skills need improvement?
   - Are version constraints too loose?

---

## Supporting Systems

### 15. /triage-audit — Complexity Audit Trail

**Purpose:** Review TRIAGE decisions made during session.

**Usage:**
```bash
/triage-audit
→ Shows all TRIAGE decisions in session
→ Scoring breakdown
→ Path recommendations vs. actual path taken
→ Why different path was chosen (if user overrode)
```

---

### 16. /validate-spec — Spec Compliance Checker

**Purpose:** (NEW) Verify implementation matches specification.

**Usage:**
```bash
/validate-spec --against plan.md
```

**Output:**
```
[VALIDATE-SPEC] Checking implementation against specify.md...

✅ Requirement 1: User can login via email
✅ Requirement 2: Password is hashed
❌ Requirement 3: Two-factor auth (not implemented)
⚠️  User story: "As admin I can reset user password" (partial)

Drift severity: MAJOR (1 not implemented, 1 partial)
Recommendation: Return to Phase 2 (ALIGN) to reassess scope
```

---

### 17. /metrics — Telemetry Query and Analysis

**Purpose:** (NEW) Query session metrics and historical analysis.

**Usage:**
```bash
/metrics --session <tsk_id>          # This session
/metrics --by-path                   # Historical by path
/metrics --rework                    # Rework patterns
/metrics --gates                     # Approval gate outcomes
/metrics --knowledge                 # CKS integration metrics
```

---

## Execution Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                     /build WORKFLOW v2.0                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                      │
│  │   STEP 0     │                                                      │
│  │   TRIAGE     │  /triage <feature>                                   │
│  │              │  ↓ Score complexity (0-25)                           │
│  │ /discover    │  ↓ Select path (FAST/STANDARD/CAREFUL/DESIGN_REVIEW)│
│  └──────────────┘                                                      │
│         ↓                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │   PHASE 0    │    │   PHASE 1    │    │   PHASE 2    │            │
│  │  BOOTSTRAP   │───▶│    ALIGN     │───▶│   DESIGN     │            │
│  │              │    │              │    │              │            │
│  │ /tm          │    │ /specify     │    │ /brainstorm  │            │
│  │ /git worktree│    │              │    │ /arch [ADF]  │            │
│  │ /checkpoint  │    │ [GATE 1] ✅  │    │ /plan        │            │
│  └──────────────┘    └──────────────┘    │ /checkpoint  │            │
│                             ▲              │              │            │
│                             │              │ [GATE 2] ✅  │            │
│                      /refine-spec          └──────────────┘            │
│                                                   ↓                     │
│                                          ┌──────────────┐              │
│                                          │   PHASE 3    │              │
│                                          │    BUILD     │              │
│                                          │              │              │
│                                          │ /ralph       │              │
│                                          │   ├─ RED     │              │
│                                          │   ├─ GREEN   │              │
│                                          │   └─ REFACTOR│              │
│                                          │ /exec        │              │
│                                          │ /verify 1,2  │              │
│                                          │              │              │
│                          ┌─Unknown──────▶│ /arch        │              │
│                          │  Discovery   │ --reevaluate │              │
│                          │              │ (escalate)   │              │
│                          │              └──────────────┘              │
│                          │                      ↓                      │
│                          │              ┌──────────────┐              │
│                          └──────────────│   PHASE 4    │              │
│                                          │    SHIP      │              │
│                                          │              │              │
│                                          │ /verify 1,2,3               │
│                                          │ git commit   │              │
│                                          │ /learn       │              │
│                                          │ /tm close    │              │
│                                          │ worktree rm  │              │
│                                          │              │              │
│                                          │ [TELEMETRY]  │              │
│                                          └──────────────┘              │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

GATES & DECISION POINTS:
  [GATE 1] - Specification Approval (Phase 2→3)
    ✅ /approve-spec → Continue to Phase 3
    🔄 /refine-spec → Loop back to /specify
    ❌ /reject-spec → End or restart

  [GATE 2] - Design & Plan Approval (Phase 3→4)
    ✅ /approve-plan → Continue to Phase 4
    🔄 /refine-plan → Loop back to /plan
    ⚠️  /escalate-design → Return to /arch
    ❌ /reject-plan → End or restart

FAST PATH (TRIVIAL complexity):
  /triage → skip Phase 1,2,3 → Phase 4 (BUILD) → Phase 5 (SHIP)

CHECKPOINT STRATEGY:
  Auto-checkpoints at:
  • Phase transition (pre/post)
  • Unknown escalation
  • Every 25 tasks completed
  • User-requested (/checkpoint)

ERROR RECOVERY:
  Spec Drift → /validate-spec → refine or loop back to Phase 1
  Test Regression → /verify → fix or escalate
  Unknown Discovery → /arch --reevaluate → decide path
  Context Overload → /fork-context → merge-back when ready
```

---

## Integration Points

### TaskMaster Integration

**Commands that create/update TSK:**
- `/specify` — Creates TSK and Phase 2 specification
- `/tm` — Direct TaskMaster access

**Commands that use active TSK:**
- `/exec` — Context-aware execution uses TSK context
- `/plan` — Task decomposition linked to TSK
- `/verify` — Validation against TSK requirements
- `/learn` — Lessons tagged with TSK ID
- `/metrics` — All metrics recorded under TSK

### Git Integration

**Worktree Management:**
- Phase 1: Create feature worktree with `/git worktree add`
- Phase 5: Remove worktree with `/git worktree remove`

**Commit Conventions:**
- Phase 5: Conventional commit format with TSK reference
  ```
  feat: <description>
  
  Closes TSK-<YYMMDD>-<Name>
  ```

### Checkpoint System

**Checkpoint Points:**
- Auto: Phase transitions, unknown discoveries, every 25 tasks
- Manual: User-triggered `/checkpoint <message>`

**Restore Recovery:**
- `/checkpoint-restore <name>` rolls back to checkpoint state
- Preserves TSK journal (append-only audit trail)

### Knowledge Systems

**CKS Integration:**
- `/learn` in Phase 5 ingests to `CKS.unified`
- `/arch` queries CKS for architectural patterns
- Lessons are searchable and reusable

**CHS Integration:**
- `/brainstorm` infers topic from chat history
- `/discover` uses semantic code search

---

## Known Issues & Future Work

### v2.0 Known Issues

1. **`/triage` command** — Needs implementation (referenced but may not exist)
2. **`/validate-spec` command** — Needs implementation (new in v2.0)
3. **`/metrics` command** — Needs implementation (new in v2.0)
4. **Context fork protocol** — Needs `/fork-context` command implementation
5. **Skill versioning** — Needs enforcement in skill loader

### Future Enhancements (v2.1+)

- [ ] Machine learning for complexity scoring (learn from telemetry)
- [ ] Parallel task execution in Phase 4 (when independent)
- [ ] Rollback suggestions based on historical patterns
- [ ] Automated spec validation (lint specify.md)
- [ ] Phase parallelization for large teams
- [ ] Integration with CI/CD pipelines
- [ ] AI-powered code review before SHIP
- [ ] Automated rollback on test failure

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-01 | Initial release |
| 2.0.0 | 2026-01-12 | Quantified gates, error recovery, checkpoints, observability |

---

**Maintained by:** Claude Code  
**Last Updated:** 2026-01-12 @ 8:44 PM MST  
**Format:** review_bundle_v2  
**File:** `build_workflow_v2.md`