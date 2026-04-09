---
name: q
description: "Strategic quality check with GoT+ToT enhancement - architectural soundness, design patterns, technology fit, over/under-engineering detection with requirement constraint analysis and branching question scenarios"
version: 1.0.0
status: stable
category: quality
enforcement: advisory
triggers:
  - /q
aliases:
  - /q

suggest:
  - /sqa
  - /arch
  - /planning

depends_on_skills: []
workflow_steps:
  - resolve_scope: Q1 - Determine what to analyze (session activity, conversation history, git status)
  - strategic_collection: Q2 - Launch 4 parallel subagents (Architecture, Design Patterns, Tech Fit, Library Strategy)
  - strategic_analysis: Q3 - Synthesize findings, normalize schema, assess health
  - render_output: Q4 - Produce strategic assessment report (Sound/Concerning/Critical)
  - persist_findings: Q5 - Store strategic findings to CKS
  - meta_analysis_handoff: Q6 - Create strategic→tactical handoff packet for /p consumption

parameters:
  - name: phase
    description: "Run specific phase (1-6). Omit to run full pipeline."
    type: string
    required: false

test_prompts:
  - description: "Full pipeline execution"
    prompt: "/q"
    expected_behavior: "Runs Q1-Q6, produces strategic health assessment with findings and next steps"
  - description: "Single phase execution"
    prompt: "/q --phase=1"
    expected_behavior: "Runs only Q1 (ScopeResolver), outputs scope object with target files/topics and complexity_class"
  - description: "Deep analysis mode"
    prompt: "/q --deep"
    expected_behavior: "Runs full pipeline with DDD deep analysis in Q5, produces comprehensive fix plan"
  - description: "Backward compatibility"
    prompt: "/q3"
    expected_behavior: "Runs Q3 via legacy shorthand, equivalent to /q --phase=3"

hooks:
  Stop:
    - matcher: ".*"
      hooks:
        - type: command
          command: python "$CLAUDE_PROJECT_DIR/.claude/skills/q/hooks/StopHook_q_completion_validator.py"
          timeout: 10
  PreToolUse:
    - matcher: "Bash|Task"
      hooks:
        - type: command
          command: python "$CLAUDE_PROJECT_DIR/.claude/skills/q/hooks/PreToolUse_q_phase_gate.py"
          timeout: 5
  PostToolUse:
    - matcher: "Bash|Task"
      hooks:
        - type: command
          command: python "$CLAUDE_PROJECT_DIR/.claude/skills/q/hooks/PostToolUse_q_state_tracker.py"
          timeout: 5

do_not:
  - use "lock ordering" or "enterprise-grade" patterns
  - suggest background services or real-time metrics
  - suggest autonomous execution or self-healing
  - require team approval
  - confuse strategic quality with tactical implementation (that's /p's job)
  - recommend re-running /q as a next step (validation loops waste time)

---

## GoT + ToT Integration

/q integrates Graph-of-Thought (Q3 requirement constraint analysis) and Tree-of-Thought (Q2/Q4 question branching). See [references/got-tot-integration.md](references/got-tot-integration.md) for details and opt-out flags.

---

# /q - Strategic Quality Check

## Purpose

**Strategic quality assessment:** "Did we do the right thing?" — Architectural soundness, design validation, technology fit, and engineering balance.

**Scope boundary:**
- `/q` = Strategic quality (did we do the right thing?)
- `/p` = Tactical implementation (did we implement correctly?)
- `/r` = Omissions check (what did we forget?)
- `/s` = Alternatives (what are our options?)

**Anti-pattern:** Don't use `/q` for bug hunting, syntax errors, or test coverage. That's `/p`'s job.

## Unique Value vs Strategic Reasoning Library

`/q` provides a **complete strategic health check orchestration** that no other skill offers:

| What | Where | Purpose |
|------|-------|---------|
| **Strategic reasoning patterns** | `P:/.claude/skills/__lib/strategic_reasoning.md` | Internal thinking tools (GoT, ToT, Strategic Questioning, Technology Fit) available to individual skills |
| **`/q` workflow** | This skill | Coordinated 6-phase pipeline that synthesizes across strategic dimensions and produces a health verdict |

**Strategic reasoning patterns** are tools that skills like `/planning`, `/arch`, `/rca`, `/skill-audit`, and `/sqa` use internally.

**`/q`** is the orchestrator that:
- Runs 4 parallel subagents (Architecture, Design Patterns, Tech Fit, Library Strategy)
- Synthesizes findings into a health assessment (`Sound/Concerning/Critical`)
- Persists strategic findings to CKS for cross-session recall
- Creates strategic→tactical handoff packets for `/p` consumption

**Analogy:** Strategic reasoning patterns are like algorithms that a calculator uses. `/q` is the complete calculator that runs those algorithms across multiple dimensions and gives you a final answer.

**Relationship to other skills:**
- `/sqa` uses strategic reasoning patterns (Domain Patterns, Library Strategy, Technology Fit) within its L0 PREDICTIVE layer
- `/planning` uses GoT+ToT for constraint analysis and branching scenarios
- `/arch` uses GoT+ToT for architecture alternatives and Technology Fit for validation
- `/rca` uses GoT constraint analysis and Strategic Questioning for blind-spot detection
- `/skill-audit` uses Strategic Questioning for blind-spot detection before finalizing audits

None of these skills replace `/q`'s role as the strategic health orchestrator.

## How This Skill Works

**PROCEDURE-type skill** — Claude reads this SKILL.md and executes the workflow. No external CLI tool.

**6-Phase Pipeline:** Q1 (scope) → Q2 (collect) → Q3 (analyze) → Q4 (report) → Q5 (persist) → Q6 (handoff)

Sub-phases: `/q1` through `/q6` can run individually.

## Error Handling

Every error becomes a visible finding — never halt the pipeline. Degrade gracefully.

| Error | Behavior |
|-------|----------|
| Session scope unreadable | Fall back to conversation scope |
| Web search unavailable | Continue without domain patterns, note degraded analysis |
| Subtask failure | Continue with completed subtasks + "analysis degraded" finding |
| CKS unavailable | Skip storage/query, continue with subagent findings only |

## Your Workflow

### Step 0: Parse Phase Parameters

**Check for explicit --phase flag:**
- If `/q --phase=1` through `/q --phase=6` → run only that phase, skip to Step 4 (Dispatch)
- If `/q` with no phase flag → run full pipeline (Q1→Q2→Q3→Q4→Q5→Q6)

**Why:** Allows users to run individual phases for debugging or targeted analysis.

### Step 1: Emit Phase Boundary Markers

Emit phase start/end markers around each phase. See [references/workflow-details.md](references/workflow-details.md) for format and examples.

### Step 2: Resolve Scope

Determine what to analyze. Priority order:

1. **Primary:** Session activity tracker (WT_SESSION-scoped files)
2. **Secondary:** Conversation history analysis (what was discussed)
3. **Tertiary:** Git status (verification only, cross-reference with session)

**CRITICAL:** Git-only analysis is PROHIBITED in multi-terminal environments.

### Q2: Strategic Collection (PARALLEL)

Launch 4 parallel Task subagents (**sonnet model**) for: Architecture & Structure, Design Patterns & Domain, Technology Fit & Engineering Balance, and Library Strategy. See [references/subagent-prompts.md](references/subagent-prompts.md) for full prompts.

Wait for all 4 subagents, then merge into one `strategic_findings` object. If `.claude/config/solo-dev-context.yaml` exists, filter out enterprise-style findings.

### Q3: Strategic Analysis

Synthesize findings from all subagents. Normalize into `{id, severity, category, message, file_path, line_number}` schema, assess health (Sound/Concerning/Critical), identify risks, generate recommendations. See [references/workflow-details.md](references/workflow-details.md) for health thresholds.

### Q4: Render Output

Produce strategic assessment report. Structure varies by health level. See [references/workflow-details.md](references/workflow-details.md) for required output format and templates.

**CRITICAL:** Never recommend "re-run /q to validate fixes" -- that creates validation loops.

### Q5: Persist Findings (ContextSink)

Store strategic findings to CKS. See [references/workflow-details.md](references/workflow-details.md) for code. If CKS unavailable, skip -- findings are already in the report.

### Q6: Meta-Analysis & Handoff

Save strategic handoff to `P:/__csf/.handoffs/q_to_p_handoff.json` for `/p` to consume. See [references/workflow-details.md](references/workflow-details.md) for schema.

### Step 3: Dispatch Phase Subagent

Read the phase file from `P:/.claude/skills/q/phases/qN.md` and dispatch as an Agent subagent. See [references/workflow-details.md](references/workflow-details.md) for dispatch protocol and phase file mapping.

### Report Completion

After each run, report:
- **Strategic health**: Sound/Concerning/Critical
- **Key findings**: Top 3 strategic concerns or opportunities
- **Next steps**: Highest-value concrete action (fix X, then build Y — NOT "re-run /q")

## Strategic Quality Dimensions

| Dimension | What It Checks |
|-----------|----------------|
| **Architectural Soundness** | Structure, layering, boundaries |
| **Design Pattern Review** | Pattern appropriateness, anti-patterns |
| **Domain Patterns** | Industry best practices for problem domain |
| **Technology Fit** | Right tool for the job? |
| **Engineering Balance** | Over/under-engineering detection |
| **Library Strategy** | Dependency freshness, CVEs, deprecated APIs, modern alternatives |
| **Strategic Alignment** | Alignment with project goals |

## What This Does NOT Do

- Does NOT check tactical implementation (tests, lint, bugs) — that's `/p`
- Does NOT check for omissions — that's `/r`
- Does NOT brainstorm alternatives — that's `/s`
- Does NOT HALT — errors degrade gracefully
- Does NOT recommend re-running itself — user controls validation cadence
