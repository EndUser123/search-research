# Plan Review Guide - Consolidated Skill Reference

**Version:** 1.0.1
**Created:** 2026-02-05
**Updated:** 2026-04-15
**Purpose:** Single reference document consolidating all skills for reviewing and improving plans.

---

## Overview

This guide consolidates 10+ skills involved in plan creation, review, and improvement into a unified reference. Use this guide to:

1. **Select the right skill** for your current review phase
2. **Understand workflows** from plan creation through completion
3. **Avoid redundancy** by knowing which skills overlap
4. **Combine skills effectively** for comprehensive plan analysis

The `/planning` skill now includes an evidence-first cross-file consistency gate. Plan review is not complete if a claim is only true in prose; it must also be true in the current workspace.

`/planning` is the canonical entry point. It creates the draft and then verifies it before promoting readiness.

### When to Use Which Skill

| Goal | Primary Skill | Alternatives |
|------|--------------|--------------|
| **Create new plan** | `/planning` | `/arch → /plan-workflow` (for features needing research) |
| **Quick plan validation** | `/planning review <file>` | `/r "validate plan <file>"` (deterministic pre-mortem) |
| **Comprehensive plan review** | `/adversarial-review` | `/s --mode heavy` |
| **Strategic analysis** | `/r` | `/llm-cli` (multi-LLM perspective) |
| **Pre-mortem checks** | `/r` | `/skeptic` (AI output validation) |
| **Optimize existing plan** | `/r` | `/nse` (next steps) |
| **Architecture validation** | `/arch` | `/s --mode heavy` |
| **Mark plan complete** | `/finalize` | N/A |
| **Review implementation gaps** | `/r "validate plan <file>"` | `/tdd` (verification) |
| **Find next steps** | `/nse` | `/dne` (past-to-future analysis) |

### Workflow Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLAN LIFECYCLE PHASES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FAST (< 30s)          PARALLEL (< 2min)        DEEP (> 5min)              │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ┌─────────────┐      ┌──────────────────┐      ┌────────────────────┐    │
│  │  1. CREATE  │  →   │  2. QUICK SCAN   │  →   │  3. DEEP REVIEW    │    │
│  │             │      │                  │      │                    │    │
│  │ /planning   │      │ /q               │      │ /adversarial-review│    │
│  │ /arch → /plan-workflow     │      │ /r "validate plan"│      │ /s --mode heavy │    │
│  └─────────────┘      │ /nse (minimal)   │      │ /llm-cli          │    │
│                       └──────────────────┘      │ /llm-debate         │    │
│                                                 │ /arch               │    │
│  ┌─────────────┐      ┌──────────────────┐      └────────────────────┘    │
│  │ 4. SYNTHESIS│  →   │ 5. ACTION ITEMS  │                                  │
│  │             │      │                  │                                  │
│  │ Aggregate   │      │ /r             │                                  │
│  │ findings    │      │ /nse             │                                  │
│  │ Prioritize  │      │ /finalize        │                                  │
│  └─────────────┘      └──────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Skill Reference

### 1. `/planning` - Structured Planning

**Purpose:** Create 7-section implementation plans for non-trivial tasks.

**Triggers:** `/planning <objective>`

**Key Components:**
- 7-section format (Problem, Context, Solution, Implementation, Risk, Success, Dependencies)
- Plan co-location with implementation (not centralized `plans/` directory)
- TDD integration (test discovery before implementation)
- Existing code discovery (avoid duplication)
- Evidence-first cross-file consistency checks before readiness is accepted
- Mechanical claim validation for env vars, gates, severity rules, selectors, and fallbacks
- Pre-mortem integration via `/r "validate plan <file>"`

**Output Format:**
```markdown
1. PROBLEM STATEMENT
2. CONTEXT ANALYSIS (Reversibility, Blast Radius, Evidence Tier, Assumptions)
2.5. EXISTING IMPLEMENTATION DISCOVERY
2.6. TEST DISCOVERY (TDD Integration)
3. PROPOSED SOLUTION (Options A, B, C)
4. IMPLEMENTATION PLAN (Phases with TDD markers)
5. RISK ASSESSMENT (Pre-mortem from /r)
6. SUCCESS CRITERIA + DOCUMENTATION
7. DEPENDENCIES
```

**Integration Points:**
- Uses `/search` for existing code discovery
- Uses code-backed traceability to compare every relevant execution path before plan approval
- Uses `/r "validate plan <file>"` for pre-mortem analysis
- Uses `/adversarial-review` for 7-perspective plan review
- Uses `/tdd` for test-first implementation
- Uses `/finalize` for completion and archival

**Best For:**
- Non-trivial tasks requiring structured approach
- Features needing TDD integration
- Implementation plans that will be reviewed by others

**See Also:** `/arch → /plan-workflow` (for features needing external research)

---

### 2. `/q` - Adaptive Quality Gate

**Purpose:** Meta-orchestrator that adapts output based on issues found. Fast when clean, thorough when broken.

**Triggers:** `/q`

**Key Features:**
- Adaptive thresholds: 0 issues (Strategic), 1-6 issues (Mixed), 7+ issues (Problem)
- Session-scoped analysis (WT_SESSION-based, not git-only)
- Writes context to `q_context.json` for downstream skills
- Artifact audit integration (pending PRD, ARD, CHANGELOG, README)

**Output Modes:**

| Issues | Mode | Focus | Shows |
|--------|------|-------|-------|
| 0 | Strategic | Future | Pre-mortem questions, up to 7 priorities |
| 1-6 | Mixed | Fix + Plan | Issues + NSE fills gaps |
| 7+ | Problem | Fix | Full DUF-style findings |

**Integration Points:**
- Writes context for `/s`, `/arch`, `/nse`, `/r`
- Delegates to `/arch`, `/test` (semantic scan responsibilities are handled by `/p --phase=2` and `/p --phase=3`)
- Uses `/artifact-audit` for pending artifact detection

**Best For:**
- Quick health check before continuing work
- Adaptive analysis based on actual issues found
- Session-scoped quality assessment (not git-diff only)

---

### 3. `/s` - Consolidated Strategic Thinking

**Purpose:** Unified strategic analysis combining convergent and divergent thinking. Replaces deprecated `/think`, `/llm-brainstorm`, `/llm-debate`.

**Triggers:** `/s`

**Modes:**

**Lite Mode (default, < 5 seconds):**
- Parallel subagents: SecurityAgent, PerformanceAgent, DesignAgent, OpportunityAgent
- Auto-escalation to Heavy mode when critical findings detected
- Context-aware: Reads `/q` context and WT_SESSION state

**Heavy Mode (< 3 minutes):**
- Phase 1 (Diverge): Innovator + Pragmatist
- Phase 2 (Discuss): Critic + Expert
- Phase 3 (Converge): Synthesizer
- Cognitive frameworks: Cynefin, Inversion, Hanlon's Razor, Chesterton's Fence

**Output Format:**
```yaml
## Strategic Analysis: [target]

### Lite Mode (Executive Summary)
[Overall health, critical/warning/info counts]

### Heavy Mode (Multi-Phase)
Phase 1: Ideation (Innovator → Pragmatist)
Phase 2: Stress-Test (Critic → Expert)
Phase 3: Synthesis (Recommendations with pros/cons)
```

**Integration Points:**
- Reads `/q` context for session-aware analysis
- Integrates with `/arch`, `/nse`, `/r`
- Replaces `/think`, `/llm-brainstorm`, `/llm-debate`

**Best For:**
- Fast strategic analysis (Lite mode)
- Deep multi-phase brainstorming (Heavy mode)
- Decision alignment on complex issues

---

### 4. `/r` - Remember + Refine (Deterministic Pre-Mortem)

**Purpose:** Cognitive pre-mortem framework with 19 checks to catch blind spots before committing.

**Triggers:** `/r`

**Modes:**
- Standard: All 19 checks based on change classification
- `--minimal`: Pre-mortem, Rollback, Secret Leak only (2 min)
- `--plan <file>`: Plan validation mode (Mode A: Implementation vs Plan, Mode B: Plan Quality)

**Change Classification:**

| Magnitude | Criteria | Checks to Run |
|-----------|----------|--------------|
| Trivial | <10 operations, 1 file | 1, 9 |
| Moderate | 10-100 operations, <5 files | 1,2,5,6,9,13,14,18 |
| Significant | 100-500 operations, API change | 1,2,3,5,6,7,8,9,11,12,13,14,16,18,19 |
| Major | >500 operations, DB migration | ALL 19 |

**The 10 Core Checks:**
1. Pre-mortem (Future Hindsight)
2. Inversion (Flip the Question)
3. Second-Order Thinking (Then What?)
4. Red Team (Adversarial View)
5. The Empty Test (Does Zero Work?)
6. Blast Radius (Dependencies)
7. Observability (Silent Failures)
8. Assumption Audit (Surface Beliefs)
9. Rollback Sim (Reversibility)
10. Value Reveal (Upside Focus)

**Extended Checks (11-19):**
- Race Condition Hunter, Injection Probe, Secret Leak Scan, Config Drift Detector, Resource Exhaustion Test, Integration Contract Check, Bias Mirror, Barrier Check, State Integrity Check

**Plan Validation Mode:**
- **Mode A (Implementation vs Plan):** Validates implementation achieved plan's goal, checks components, deviations, acceptance criteria
- **Mode B (Plan Quality Review):** Validates plan completeness, dependencies, gaps, opportunities, risks

**Integration Points:**
- Plan validation integrates with `/planning` workflow
- Pre-mortem results populate plan Risk Assessment section
- Session activity tracker for scope enforcement

**Best For:**
- Pre-commit review (catch blind spots)
- Plan validation (before or after implementation)
- Session summary review (what did I just do?)

---

### 5. `/dne` - DUF-NSE (Past to Future Analysis)

**Purpose:** Combined workflow: Run DUF checks on recent work, then propose NSE next steps.

**Triggers:** `/dne`

**Philosophy:** "What did I just do?" (DUF) → "Is it safe?" (DUF) → "What's next?" (NSE)

**Workflow:**
```
STEP 1: DUF (Past)
    ↓ Check recent changes (session activity tracker + git intersection)
    ↓ Run cognitive checks (blast radius, rollback, etc.)
    ↓ Generate action items for any risks found
    ↓ FILTER: Remove constitutional violations
    ↓
STEP 2: NSE (Future)
    ↓ If DUF passes: propose next steps
    ↓ If DUF finds issues: fix first, then next steps
    ↓
OUTPUT: Combined assessment + action items
```

**Output Format:**
```yaml
## DUF-NSE Analysis: [change description]

**Classification:** [Trivial/Moderate/Significant/Major]
**Checks Run:** [list of checks performed]

### Findings
• Pre-mortem: [failure scenario]
• Inversion: [obvious risk]
• Rollback: [revert strategy]

### Action Items
**🔴 Priority (Critical/Fixes)**
**1** - [Highest Priority Fix] - [WHY it matters]

**🟡 Maintenance (Cleanup/Tech Debt)**
**3** - [Cleanup Task] - [WHY]

**🔵 Suggestions (Optional)**
**5** - /arch - [Why architectural review is needed]

**⚪ Git Operations**
**c** - commit (if uncommitted changes exist)
**d** - push (if unpushed commits exist)
```

**Integration Points:**
- Session activity tracker (WT_SESSION-scoped) as PRIMARY source
- Git status as SECONDARY verification only
- Constitutional filter for prohibited patterns

**Best For:**
- End-of-session review before stopping
- Before commit: ensure nothing was forgotten
- Between tasks: reset and plan next steps

---

### 6. `/llm-cli` - Parallel Multi-LLM Command

**Purpose:** Run qwen, gemini, codex, vibe, opencode, glm-4.7-flash in parallel for multi-perspective analysis.

**Triggers:** `/llm-cli`

**Key Features:**
- **EXECUTION skill** - Must run external command, not provide own analysis
- Parallel execution of 5-6 LLM CLIs
- Auto-calculated timeout (180s base + 1s per MB context)
- Context handling with `--context` and `--target` flags

**Options:**
| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--output-format json` | Machine-readable JSON output |

**CLI Characteristics:**
| CLI | Speed | Best For |
|-----|-------|----------|
| qwen | Fastest (~63s) | Code gen, debugging |
| gemini | Medium (~160s) | Concise answers |
| codex | Fast | Code reviews |
| vibe | Fast | Python tasks |
| opencode | Fast | Alternative perspectives |
| glm-4.7-flash | Fast (~60s API) | Additional perspective |

**Best For:**
- Getting multiple LLM perspectives on a question
- Investigating issues with diverse reasoning approaches
- Consensus building on controversial decisions

---

### 7. `/llm-debate` - LLM Debate Council (DEPRECATED)

**Status:** **DEPRECATED** - Use `/s --mode heavy` instead.

**Replacements:**
- `/llm-debate` → `/s --mode heavy` (Discuss phase covers debate functionality)
- `/s` consolidates `/think`, `/llm-brainstorm`, and `/llm-debate` into unified system

**Historical Reference:**
Multi-provider LLM debate council with async parallel execution and consensus building. Used REST API providers (chutes, groq, mistral, openrouter, zai-claude) and CLI providers (qwen-cli, gemini-cli, gh-cli).

---

### 8. `/adversarial-review` - 7-Perspective Parallel Review

**Purpose:** Parallel adversarial code review with 7 specialized analysis perspectives.

**Triggers:** `/adversarial-review [files] --mode [all|security|performance|compliance|quality|testing|rca|qa] --depth [light|standard|deep]`

**Subagents (Parallel Execution):**
- **adversarial-security** - Data leaks, access control gaps, injection vectors
- **adversarial-performance** - Timeouts, bottlenecks, N+1 patterns
- **adversarial-compliance** - Specification and schema compliance
- **adversarial-quality** - Maintainability risks and technical debt
- **adversarial-testing** - Missing test scenarios, brittle tests, coverage gaps
- **code-critic** - Root cause analysis with multi-agent reasoning
- **qa-engineer** - Test generation and execution verification

**Workflow:**
1. Parse input & detect context (git diff or chat context)
2. Select perspectives based on `--mode`
3. Parallel execution (CRITICAL: use Task tool with `prompt` parameter)
4. Aggregate & display (PostToolUse hook auto-aggregates)
5. Results saved to `.claude/state/adversarial-review-latest.json`
6. Gated output (Stop hook applies quality gates)

**Best For:**
- Comprehensive code review before commit
- Finding security vulnerabilities
- Identifying performance bottlenecks
- Test coverage analysis

---

### 9. `/r` - Solution Optimization Review

**Purpose:** Quick optimization review using cognitive frameworks and agent delegation for simplification and efficiency.

**Triggers:** `/r`, "optimize this", "is this optimal", "can this be simpler"

**3-Phase Process:**

**Phase 1: Cognitive Analysis**
- Inversion: "What if this is over-engineered?"
- Devil's Advocate: "What's the simplest alternative?"
- Cynefin: Clear vs Complicated vs Complex domain classification

**Phase 2: Agent Delegation (Parallel)**
- `code-simplifier` - Direct simplification opportunities
- `code-reviewer` - Inefficiencies, anti-patterns
- `code-architect` - Structural concerns (optional)
- `perf` - Performance analysis (if relevant)

**Phase 3: Action Items**
DUF-style numbered choices:
```
**1** - [Optimization opportunity]
**2** - [Optimization opportunity]
**4** - /code-simplifier (delegate autonomous simplification)
**5** - /arch (delegate architecture review)
**7** - All (apply all optimizations)
**8** - None (skip optimizations)
```

**Constitutional Compliance (REQUIRED):**
All optimization recommendations MUST be filtered against solo-dev constitutional constraints. Auto-filter prohibited patterns: continuous monitoring, lock ordering, self-healing, scalability requirements.

**Best For:**
- Quick optimization check
- Simplification opportunities
- Efficiency review before commit

---

### 10. `/nse` - Next Step Engine (Unified)

**Purpose:** Analyzes context and proposes action-oriented next steps with confidence scoring, effort estimates, and constitutional filtering.

**Triggers:** `/nse`, "next step", "what's next", "recommend"

**Key Features:**
- Session-scoped analysis (WT_SESSION-based)
- Git state verification (fresh, not cached)
- Constitutional filter integration
- Confidence scoring and effort estimates

**Actions Reference:**
- **Standard:** debug, optimize, refactor, test, review, plan, deploy, security
- **Phase 2 Orchestrator:** orchestrator, health-mon, phase2-ready, load-test, scale, db-perf, correlation

**Enhanced Features:**
- Probability analysis (root cause breakdowns)
- Alternative comparison (`--compare` flag)
- Expected value scoring
- Minimal output format (`--minimal` flag)

**Best For:**
- What-to-do-next recommendations
- Debug-focused suggestions
- Optimization-focused recommendations

---

### 11. Supporting Skills

#### `/finalize` - Plan Completion & Archival

**Purpose:** Mark plans as completed or abandoned, run truth validation, and archive.

**Triggers:** `/finalize <plan-path>`

**Key Features:**
- Updates plan status header metadata
- Archives to `plans/completed/` or `plans/abandoned/`
- Runs truth validation on completion claims
- Generates completion report

#### `/skeptic` - AI Output Validation

**Purpose:** Skeptical reviewer of AI-generated plans, diffs, and analyses.

**Triggers:** `/skeptic`, "challenge this plan", "verify AI output"

**Key Checks:**
- Evidence (claims without support)
- Coverage (missing tests, edge cases)
- Overreach (changes beyond scope)
- Hallucination (references to non-existent files)

#### `/arch → /plan-workflow` - Technical Ideation & Planning

**Purpose:** Intent-adaptive ideation workflow transforming vague requests into concrete plan.md.

**Triggers:** `/arch → /plan-workflow <feature_idea>`

**Two Modes:**
- **ADVISORY:** Quick evaluation via `/arch`, save to `advisory.md`
- **PLANNING:** Full pipeline (TRIAGE → DEFINE → DISCOVER → SOLVE → PLAN)

**5-Step Loop:**
1. TRIAGE (scope)
2. DEFINE (/specify)
3. DISCOVER (/search, /research, /notebooklm)
4. SOLVE (/brainstorm, /arch)
5. PLAN (/breakdown)

#### `/tdd` - Test-Driven Development

**Purpose:** TDD for new features and refactoring with PARALLEL subagent delegation.

**Triggers:** `/tdd`

**Workflow:**
```
0. DISCOVER → Understand code
1. RED → Write failing test (PARALLEL tdd-test-writer)
2. GREEN → Implement minimal code (PARALLEL tdd-implementer)
3. VERIFY → Run actual command
4. REGRESSION → Run related tests
5. REFACTOR → Clean up (PARALLEL tdd-refactorer)
```

---

## Workflows

### For NEW Plans (Before Implementation)

```mermaid
graph TD
    A[Start: Feature Idea] --> B{Need Research?}
    B -->|Yes| C[/arch → /plan-workflow - Planning Mode]
    B -->|No| D[/planning]

    C --> E[specify.md + context.md]
    D --> F[Plan with 7 sections]

    E --> G[/arch - Validate Decisions]
    F --> G

    G --> H[brainstorm + breakdown]
    H --> I[plan.md created]

    I --> J[/r "validate plan plan.md"]
    J --> K[Pre-mortem analysis]

    K --> L[/adversarial-review plan.md]
    L --> M[7-perspective review]

    M --> N{Plan Quality?}
    N -->|Gaps| O[Revise plan]
    N -->|Good| P[/tdd - Write tests]

    O --> J
    P --> Q[Implementation ready]
```

**Quick Start Commands:**
```bash
# Option 1: Full design pipeline (with research)
/arch → /plan-workflow "implement feature X"

# Option 2: Direct plan creation
/planning "implement feature X"

# Then validate:
/r "validate plan plan-YYYYMMDD-feature.md"

# Then review:
/adversarial-review plan-YYYYMMDD-feature.md

# Then start TDD:
/tdd "implement phase 1 of plan-YYYYMMDD-feature.md"
```

### For EXISTING Plans (After Code)

```mermaid
graph TD
    A[Start: Existing Plan + Code] --> B[/r "validate plan plan.md"]
    B --> C{Mode Selection}

    C -->|Mode A| D[Implementation vs Plan]
    C -->|Mode B| E[Plan Quality Review]

    D --> F[Goal Achievement Check]
    F --> G[Component Completeness]
    G --> H[Approach Deviation]
    H --> I[Acceptance Criteria]

    E --> J[Completeness Check]
    J --> K[Dependency Analysis]
    K --> L[Gap Analysis]
    L --> M[Risk Assessment]

    I --> N[Findings Summary]
    M --> N

    N --> O{Gaps Found?}
    O -->|Yes| P[/nse - Generate fixes]
    O -->|No| Q[/finalize - Mark complete]

    P --> R[Implement fixes]
    R --> B
```

**Quick Start Commands:**
```bash
# Validate implementation against plan
/r "validate plan plan-YYYYMMDD-feature.md"

# Or review plan quality
/r "validate plan plan-YYYYMMDD-feature.md"

# Check if implementation matches plan
# (Mode A: Implementation vs Plan - automatic)

# Generate next steps
/nse

# Mark complete if all criteria met
/finalize plan-YYYYMMDD-feature.md
```

### Quick Review vs. Comprehensive Review

| Aspect | Quick Review | Comprehensive Review |
|--------|-------------|---------------------|
| **Time** | < 2 minutes | 5-15 minutes |
| **Skills** | `/q` | `/adversarial-review` + `/s` |
| **Focus** | Critical risks only | All perspectives |
| **Output** | Action items (Priority only) | Full findings + alternatives |
| **When** | Small changes, trusted code | Major changes, security-sensitive |

**Quick Review Pattern:**
```bash
# Fast pre-commit check
/q

# Or adaptive quality gate
/q

# Or next steps only
/nse --minimal
```

**Comprehensive Review Pattern:**
```bash
# Full adversarial review
/adversarial-review

# Strategic analysis
/s --mode heavy

# Multi-LLM perspective
/llm-cli "review this plan" --context plan.md --aggregate

# Optimization check
/r
```

---

## Atomic Components

### What Each Skill Uniquely Contributes

| Skill | Unique Contribution | Cannot Be Replaced By |
|-------|--------------------|----------------------|
| `/planning` | 7-section structured format + TDD integration | `/arch → /plan-workflow` (research-heavy) |
| `/q` | Adaptive output based on issue count | Any single-skill review |
| `/s` | Convergent + divergent thinking in one | Deprecated `/llm-debate` |
| `/r` | Deterministic pre-mortem + refine + plan validation | `/skeptic` (AI-focused only) |
| `/dne` | Past-to-future analysis (R + NSE) | Separate `/r` + `/nse` |
| `/llm-cli` | External LLM CLI execution (6 providers) | Internal analysis |
| `/adversarial-review` | 7 parallel specialized subagents | Any single-perspective review |
| `/r` | Optimization focus with constitutional filter | Generic reviews |
| `/nse` | Next step proposals with confidence scoring | Static action lists |
| `/finalize` | Plan archival + truth validation | Manual status updates |

### Redundancy to Avoid

| Redundant Combination | Better Alternative |
|---------------------|-------------------|
| `/r` + `/dne` | `/dne` already includes deterministic pre-mortem |
| `/s` + `/llm-debate` | `/s --mode heavy` replaces `/llm-debate` |
| `/q` + `/r` | `/q` already includes DUF-lite checks |
| `/adversarial-review` (all) + `/r` | Run `/adversarial-review` first, then `/r` only if optimization needed |
| `/nse` + `/dne` | `/dne` includes NSE phase, `/nse` for standalone use |
| `/planning` + `/arch → /plan-workflow` | Use `/planning` for direct creation, `/arch → /plan-workflow` only for research-heavy features |

### Ideal Combinations

| Goal | Ideal Combination | Order |
|------|-------------------|-------|
| **New feature plan** | `/arch → /plan-workflow` → `/r "validate plan <file>"` → `/adversarial-review` | 1→2→3 |
| **Pre-commit check** | `/q` → `/nse` (if issues found) | 1→2 |
| **Strategic decision** | `/s --mode heavy` → `/llm-cli` | 1→2 |
| **Code review** | `/adversarial-review` → `/r` | 1→2 |
| **Session wrap-up** | `/dne` → `/finalize` | 1→2 |
| **Plan validation** | `/r "validate plan <file>"` → `/skeptic` | 1→2 |
| **Quality gate** | `/q` → `/r` | 1→2 |

---

## Quick Reference Table

| Goal | Use | Alternative | Notes |
|------|-----|-------------|-------|
| **Create plan** | `/planning` | `/arch → /plan-workflow` | Use `/arch → /plan-workflow` for research-heavy features |
| **Validate plan** | `/r "validate plan <file>"` | `/skeptic` | Deterministic implementation-vs-plan checks |
| **Quick health check** | `/q` | `/r` | Adaptive + deterministic follow-up |
| **Strategic analysis** | `/r` | `/llm-cli` | Deterministic < 5s, Heavy < 3min |
| **Deep review** | `/adversarial-review` | `/s --mode heavy` | 7 perspectives vs 3-phase |
| **Pre-mortem** | `/r` | `/skeptic` | Deterministic checks vs AI validation |
| **Optimize** | `/r` | `/nse` | Optimization vs next steps |
| **Multi-LLM view** | `/llm-cli` | `/s --mode heavy` | External CLIs vs internal personas |
| **Next steps** | `/nse` | `/dne` | Standalone vs past-to-future |
| **Mark complete** | `/finalize` | N/A | Includes truth validation |
| **TDD workflow** | `/tdd` | `/test` | RED→GREEN→REFACTOR cycle |
| **Architecture decision** | `/arch` | `/s` | Architecture Decision Framework |
| **Session summary** | `/dne` | `/q` + `/nse` | Combined DUF + NSE |

---

## Integration Flows

### Plan Creation to Completion Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PLAN LIFECYCLE FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CREATION                                                                │
│     ├── /arch → /plan-workflow (research-heavy) OR /planning (direct)                     │
│     └── Output: plan.md with 7 sections                                    │
│                                                                             │
│  2. VALIDATION                                                              │
│     ├── /r "validate plan plan.md" (pre-mortem, gaps, risks)                │
│     ├── /adversarial-review plan.md (7-perspective analysis)                │
│     └── /skeptic plan.md (AI output validation)                             │
│                                                                             │
│  3. APPROVAL                                                                │
│     ├── Review findings from validation                                     │
│     ├── Revise plan if gaps found                                          │
│     └── Mark ready for implementation                                      │
│                                                                             │
│  4. IMPLEMENTATION (TDD)                                                    │
│     ├── /tdd "write tests for plan.md" (RED phase)                          │
│     ├── /tdd "implement phase 1" (GREEN phase)                              │
│     └── /tdd "refactor" (REFACTOR phase)                                    │
│                                                                             │
│  5. VERIFICATION                                                            │
│     ├── /r "validate plan plan.md" (Mode A: impl vs plan)                   │
│     ├── /adversarial-review (code review)                                   │
│     └── /q (quality gate)                                                   │
│                                                                             │
│  6. COMPLETION                                                              │
│     ├── /nse (generate next steps if needed)                                │
│     └── /finalize plan.md (mark complete, archive)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quality Gates Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUALITY GATES FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTER WORK → /q (Adaptive Gate)                                           │
│                  │                                                          │
│                  ├── 0 issues → Strategic Mode (pre-mortem questions)       │
│                  │        ├── /r (fast parallel)            │
│                  │        └── /nse (next steps)                             │
│                  │                                                          │
│                  ├── 1-6 issues → Mixed Mode (fixes + planning)            │
│                  │        ├── Fix issues from /q                            │
│                  │        ├── /nse fills remaining slots                    │
│                  │        └── /r for deterministic deeper analysis           │
│                  │                                                          │
│                  └── 7+ issues → Problem Mode (fix first)                  │
│                           ├── Fix critical issues                           │
│                           ├── /adversarial-review (full analysis)           │
│                           └── /r (optimization after fixes)               │
│                                                                             │
│  CONTINUE WORK → Session Complete → /dne (past-to-future)                  │
│                                       ├── DUF checks on recent work          │
│                                       ├── NSE next steps                    │
│                                       └── /finalize if plan complete        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Constitutional Compliance

All plan review skills MUST filter action items against `SoloDevConstitutionalFilter`.

### Prohibited Patterns (Auto-Filter)

| Pattern | Filter Because | Alternative |
|---------|---------------|-------------|
| `lock ordering`, `acquisition order` | Enterprise bloat | Use single RLock per object |
| `continuous monitoring`, `real-time metrics` | Background service prohibited | Use on-demand `/health` |
| `self-healing` | Autonomous execution prohibited | Manual fix with approval |
| `autonomous execution` | Autonomous execution prohibited | Step-by-step with confirmation |
| `enterprise-grade`, `scalability requirement` | Enterprise pattern prohibited | Use simple solution |
| `team approval`, `stakeholder consensus` | Consensus process prohibited | Singular dev decides |

### Required Filter Step

**Before generating action items, ALWAYS run:**

```python
# Import the constitutional filter
from src.core.solo_dev_constitutional_filter import SoloDevConstitutionalFilter

filter_obj = SoloDevConstitutionalFilter()

# Check each proposed action
for action in proposed_actions:
    result = filter_obj.check_action_item(action)
    if result.violates_constitution:
        # Skip this action - don't suggest it
        continue
```

---

## Tips and Best Practices

### For Plan Reviewers

1. **Start with `/q`** - Adaptive gate tells you if deeper review is needed
2. **Use session-scoped analysis** - Skills respect WT_SESSION, not git-diff only
3. **Combine complementary skills** - `/s` (cognitive) + `/planning review` (deterministic) + `/adversarial-review` (technical)
4. **Trace claims to code** - If a plan mentions a gate, flag, or selector, verify where it is read and enforced
5. **Filter constitutional violations** - All skills should auto-filter prohibited patterns
6. **Respect evidence tiers** - High-stakes require Tier 1/2 evidence

### For Plan Creators

1. **Use `/planning` for structure** - 7-section format ensures completeness
2. **Add TDD integration** - Test discovery before implementation
3. **Search existing code** - Avoid duplication with `/search`
4. **Trace every claim across files** - If multiple paths touch the same input, verify they agree or explain the divergence
5. **Run `/planning review <file>`** - Evidence-first verification before committing to plan
6. **Use `/planning review <file>` for draft checks** - verify an existing draft before treating it as ready
7. **Get adversarial review** - 7 perspectives catch blind spots

### Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Git-only analysis** | Reviews files from other terminals | Use session-scoped skills (`/q`, `/nse`) |
| **Redundant reviews** | Running `/r` + `/dne` | `/dne` includes deterministic pre-mortem |
| **Cross-file drift** | Same gate behaves differently in two paths | Use `/planning review` and verify both paths in code |
| **Ignoring constitution** | Enterprise pattern suggestions | All skills must filter via `SoloDevConstitutionalFilter` |
| **Missing verification** | "Should work" claims | Run actual commands, provide evidence |
| **Orphaned plans** | Plans not co-located with code | Use `/planning` co-location standard |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-05 | Initial consolidation of 10+ plan review skills |
| 1.0.1 | 2026-04-15 | Added evidence-first cross-file consistency guidance for `/planning` |

---

**See Also:**
- `CLAUDE.md` - Constitutional principles and constraints
- `TDD_SYSTEM.md` - Test-driven development workflow
- `skills_transition_guide.md` - Skills migration reference
