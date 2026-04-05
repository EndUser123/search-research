# Cognitive Steering Framework (CSF) – Solution Design & Migration Plan

> Single-source design + implementation guide for organizing CLAUDE.md, Skills, and Hooks for Claude Code on Windows 11.
>
> **Last Updated:** 2025-01-16
> **Status:** Design Draft - Rollback procedures are theoretical and require validation

---

## 1. Solution Design

### 1.1 Current State vs Target State

#### 1.1.1 Current State (Organic CSF)

- **Environment**
  - OS: Windows 11
  - Drive: `P:` used as primary workspace
  - Claude Code installed and using default locations under `P:\.claude`
- **Global Cognitive Infrastructure**
  - A mature but organically-grown `CLAUDE.md` (Constitution v7.3) with:
    - 11+ **constitutional principles** (truthfulness, no sycophancy, evidence-first, etc.)
    - Solo developer constraints (no continuous monitoring, no self-healing, etc.)
  - Mixed content: constitutional rules, operational standards, and project-ish details live side-by-side.
- **Skills**
  - Located under `P:\.claude\skills\` (Claude Code native location)
  - Existing cognitive skills:
    - `execution-clarity\`
    - `response-atomicity\`
    - `sequential-thinking\`
    - `subagent-first\`
    - `value-maximization\`
    - `solo-dev-authority\`
  - Each skill has a SKILL.md and supporting documents, but structure is not yet standardized across all skills.
  - **Known Issue:** Skill discovery is not consistently reliable. Manual verification may be required.
- **Hooks**
  - Located under `P:\.claude\hooks\`
  - You already have:
    - Scanners (e.g., hallucination scanner, reflection validator)
    - Validators (TDD compliance, anti-lazy verification)
    - Repositories (checkpoint state, task context, project context)
  - Hooks are event-based, leveraging Claude Code's `settings.json` and specific events (`PreToolUse`, `PostToolUse`, etc.).
  - Logic has grown organically and is tightly coupled to existing paths and naming.
- **Projects**
  - Live under `P:\Projects\...`
  - Project-specific `CLAUDE.md` files and other cognitive documents exist
  - Inheritance of CLAUDE.md works as per Claude Code defaults, but there is **no explicit convention** documented for:
    - What belongs in global vs project CLAUDE.md
    - How project settings integrate with hooks/skills.

#### 1.1.2 Target State (Structured CSF)

- **Top-level layout (Windows 11)**
  ```text
  P:\
  ├── __csf\                      # Framework docs & scripts (human-facing)
  │   ├── docs\                   # Design documentation (this file)
  │   └── scripts\                # PowerShell utilities for setup & validation
  │
  ├── .claude\                    # Claude Code's canonical runtime location
  │   ├── CLAUDE.md               # Single source of truth for global constitution
  │   ├── skills\                 # All cognitive skills (auto-discovered)
  │   └── hooks\                  # Hook executables + config
  │
  └── Projects\                   # Project workspaces
      ├── project-alpha\
      │   ├── CLAUDE.md           # Project-specific append-only rules
      │   └── .claude\ (optional) # Project-local skills/hooks if needed
      └── ...
  ```

- **Architecture Note: `__csf` vs `.claude`**
  - `P:\__csf\` and `P:\.claude\` serve **different purposes**:
    - `__csf\` contains framework documentation and setup scripts (human-facing design docs)
    - `.claude\` is the Claude Code runtime location (machine-facing, auto-loaded)
  - `.claude\` sits "over" both `__csf\` and `Projects\` - it's the workspace-level overlay
  - This is not an either/or choice—both directories are needed for their distinct roles

- **Global CLAUDE.md (Optimized)**
  - Contains **only**:
    - Core constitutional principles (**all existing constitutional amendments are preserved**)
    - Short meta-guidance on using skills ("skills hold the detailed patterns")
  - No long operational standards or project-specific rules.
  - **IMPORTANT:** No consolidation or filtering of constitutional amendments—preserve everything.

- **Standards as Skills**
  - `standards.md` (operational rules) becomes **skills**, primarily:
    - `validation-standards\`
    - `assumption-auditing\`
    - `uncertainty-expression\`
    - `error-handling-cascade\`
    - `risk-adjusted-reasoning\`

- **Hooks**
  - Cleaner structure and naming under `P:\.claude\hooks\`
  - Consistent pattern: scanners, validators, repositories, and a thin orchestration layer
  - Configuration centralized in `P:\.claude\settings.json` with documented behavior

- **Projects**
  - `P:\Projects\<project>\CLAUDE.md` contains project-specific rules only
  - Inherits global CLAUDE.md automatically via Claude Code
  - Optional `P:\Projects\<project>\.claude\` for per-project skills/hooks if needed

---

### 1.2 What's Changing & Why

1. **Global CLAUDE.md Slimming**
   - **From:** Monolithic document mixing principles, standards, and project details.
   - **To:** Lean constitution with only high-level cognitive & behavioral rules.
   - **Why:**
     - Makes it easier for Claude to *actually internalize* the constitution.
     - Reduces context bloat in every session.
   - **Note:** All constitutional amendments are preserved—this is about removing operational standards, not principles.

2. **Standards → Skills**
   - **From:** Separate standards.md & scattered rules in CLAUDE.md.
   - **To:** One or more skills (e.g., `validation-standards\`) that Claude can explicitly `/use` and which hooks can reference.
   - **Why:**
     - Aligns with Claude Code's native abstraction (skills).
     - Increases reusability and discoverability across projects.
   - **Caveat:** Skill discovery has reliability issues. Plan for manual skill invocation when needed.

3. **Hooks Consolidation**
   - **From:** Organic, path-specific hooks scattered under `hooks\`.
   - **To:** A coherent set with clear naming and roles (scanners, validators, repositories) and a stable `settings.json`.
   - **Why:**
     - Makes hook behavior predictable and maintainable.
     - Allows reuse across projects with minimal configuration changes.

4. **Documentation & Scripts in `__csf`**
   - **From:** Mental model and scattered notes.
   - **To:** Concrete docs + PowerShell scripts under `P:\__csf\`.
   - **Why:**
     - Keeps framework documentation visible (top of tree).
     - Provides one-command bootstrapping for new or migrated projects.

---

### 1.3 Target Architecture & Benefits

#### 1.3.1 Directory & Responsibility Layout

```text
P:\
├── __csf\                    # Framework layer (human-facing)
│   ├── docs\                 # Design docs like this file
│   └── scripts\              # Setup & validation scripts
│
├── .claude\                  # Runtime layer (machine-facing)
│   ├── CLAUDE.md             # Global cognitive constitution
│   ├── skills\               # Cognitive skills (thinking patterns)
│   └── hooks\                # Enforcement & observability
│
└── Projects\                 # Workspaces
    ├── project-alpha\
    │   ├── CLAUDE.md         # Project-specific rules
    │   └── .claude\          # Optional local overrides
    └── ...
```

#### 1.3.2 Benefits

- **Cognitive clarity**
  - Global CLAUDE.md is short and high-signal.
  - Detailed patterns live in skills, which Claude can pull when relevant.
- **Scalability**
  - Adding new cognitive techniques = add skill(s), no need to rewrite CLAUDE.md.
- **Maintainability**
  - Hooks & skills are clearly separated by responsibility.
  - Migration scripts make structure reproducible across machines/projects.
- **Portability**
  - You can copy `P:\.claude\skills` + `P:\.claude\hooks` to new environments easily.

---

### 1.4 Key Metrics & Improvements

Suggested metrics to track qualitatively/quantitatively:

1. **Context Size Reduction**
   - Before: Average tokens of global CLAUDE.md + project CLAUDE.md.
   - After: Reduced global CLAUDE.md token size; more selective use of skills.

2. **Error / Misbehavior Incidents**
   - Frequency of:
     - Hallucinated file paths
     - Ignored TDD rules
     - Violations of solo-dev constraints
   - Expectation: Reduction due to more focused hooks & skills.

3. **Hook Intervention Rate**
   - Count how often hooks block or warn.
   - Expectation: Initially high during tuning, then stabilized at "healthy" level.

4. **Skill Usage**
   - Track which skills are invoked most (`execution-clarity`, `validation-standards`, etc.).
   - Expectation: Over time, you refine or merge skills based on actual usage.
   - **Note:** Given skill discovery reliability issues, manual invocation may be necessary.

5. **Migration Overhead**
   - Time to onboard a *new project* with CSF active.
   - Expectation: After scripts, should be minutes instead of manual hours.

---

### 1.5 Known Limitations & Risks

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **Skill discovery is unreliable** | Claude may not consistently find relevant skills | Manual skill invocation (`/use skill-name`) as fallback |
| **Rollback procedures untested** | Migration failures may be harder to recover from | Test migration on throwaway workspace first; create backup before starting |
| **No feature flag strategy** | Changes are atomic, not gradual | Proceed phase-by-phase with verification between steps |

---

## 2. Implementation Guide (All Code Inline)

> All paths assume Windows 11, `P:` drive.

### 2.1 File List Overview

We will define or refactor the following key files:

1. Global Constitution & Docs
   - `P:\.claude\CLAUDE.md`
   - `P:\__csf\docs\CONSTITUTIONAL_PRINCIPLES.md`

2. Skills (new/updated)
   - `P:\.claude\skills\validation-standards\SKILL.md`
   - `P:\.claude\skills\validation-standards\PROHIBITED_PATTERNS.md`
   - `P:\.claude\skills\validation-standards\VALIDATION_CHECKLIST.md`
   - `P:\.claude\skills\assumption-auditing\SKILL.md`
   - `P:\.claude\skills\assumption-auditing\ASSUMPTION_FRAMEWORK.md`
   - `P:\.claude\skills\uncertainty-expression\SKILL.md`
   - `P:\.claude\skills\uncertainty-expression\WHEN_TO_SAY_UNKNOWN.md`
   - `P:\.claude\skills\error-handling-cascade\SKILL.md`
   - `P:\.claude\skills\error-handling-cascade\SUBAGENT_FAILURE_PATTERNS.md`
   - `P:\.claude\skills\error-handling-cascade\RECOVERY_PROTOCOLS.md`
   - `P:\.claude\skills\risk-adjusted-reasoning\SKILL.md`
   - `P:\.claude\skills\risk-adjusted-reasoning\DECISION_FRAMEWORK.md`

3. Hooks & Config
   - `P:\.claude\settings.json`  (global settings)
   - `P:\.claude\hooks\validators\tdd_validator.py` (example)
   - `P:\.claude\hooks\scanners\hallucination_scanner.py` (example)
   - `P:\.claude\hooks\scanners\assumption_auditor.py` (new)

4. Project Templates
   - `P:\Projects\_template\CLAUDE.md`
   - `P:\Projects\_template\.claude\settings.json`

5. Scripts
   - `P:\__csf\scripts\init-csf.ps1`
   - `P:\__csf\scripts\init-project.ps1`
   - `P:\__csf\scripts\validate-csf.ps1`
   - `P:\__csf\scripts\backup-csf.ps1` (NEW - backup before migration)
   - `P:\__csf\scripts\test-rollback.ps1` (NEW - test rollback procedures)

---

### 2.2 Global CLAUDE.md (Slim Constitution)

**File:** `P:\.claude\CLAUDE.md`

```markdown
# Cognitive Constitution (Global CLAUDE.md)

## Purpose

This file defines non-negotiable cognitive and behavioral principles for all Claude Code sessions on this machine.
Project-specific CLAUDE.md files may extend these rules but must not violate them.

## Core Principles

1. **Fail Fast**
   - Surface problems and uncertainties immediately.
   - Never silently degrade behavior.

2. **Truthfulness Over Agreement**
   - Prioritize accurate, evidence-based responses over agreeable or reassuring ones.

3. **No Sycophancy**
   - Do not flatter, sugar-coat, or provide unearned praise.
   - Maintain a neutral, analytical tone.

4. **Thoroughness Over Speed**
   - Prefer complete, well-reasoned answers over faster but shallow ones.

5. **Evidence-First**
   - Verify before claiming.
   - When making factual or empirical claims, state whether they are:
     - Verified (with evidence),
     - Inferred from patterns, or
     - Speculative.

6. **Investigation Before Diagnosis**
   - For debugging or analysis tasks, follow this order:
     1. Inspect the environment and files.
     2. Gather relevant evidence.
     3. Only then propose diagnoses and fixes.

7. **Reality Verification**
   - Before referencing a file, path, or symbol, verify that it actually exists in the workspace.

8. **Assumption Awareness**
   - When a task depends on non-obvious assumptions, state them explicitly before committing to a solution.

9. **Respect Solo-Developer Constraints**
   - Assume limited time, attention, and infrastructure.
   - Avoid proposing systems that require continuous monitoring, self-healing, or complex distributed orchestration unless explicitly requested.

10. **User Observation Priority**
    - If user observations conflict with tool output, treat the user's direct observations as the primary signal and reconcile the discrepancy.

11. **Skill-First Deep Thinking**
    - When a problem is complex, ambiguous, or multi-stage, actively use the relevant skills (e.g., execution-clarity, sequential-thinking, assumption-auditing) before producing final output.

## Skills & Hooks

- **Skills**
  - Detailed cognitive patterns and workflows are defined as Claude Code Agent Skills under `~\.claude\skills\` on this system.
  - When a task matches a skill's description, consult and apply that skill before responding.
  - **Note:** Skill discovery may not be reliable. You can explicitly invoke skills using `/use <skill-name>` if needed.

- **Hooks**
  - Hooks under `~\.claude\hooks\` may enforce additional checks (e.g., hallucination scanning, TDD validation).
  - Treat hook feedback as a strong signal to adjust or correct your plan.
```

---

### 2.3 Skills – Definitions & Content

Below are copy-paste-ready skill files. Adjust phrasing as desired, but the structure is ready to drop into `P:\.claude\skills\`.

#### 2.3.1 validation-standards Skill

**File:** `P:\.claude\skills\validation-standards\SKILL.md`

```markdown
# Skill: validation-standards

## Purpose

Apply validation and guardrail standards to prevent low-quality, unsafe, or impractical solutions.

## When to Use

- Before proposing architectural changes.
- Before suggesting long-running or autonomous processes.
- When generating code that writes to disk, modifies state, or calls external tools.

## Behavior

When this skill is active:

1. Check for **solo-developer constraints**:
   - Avoid designing systems that require continuous monitoring.
   - Avoid self-healing daemons or autonomous background processes unless explicitly authorized.

2. Apply **prohibited patterns**:
   - Reject or heavily qualify solutions that rely on:
     - "continuous monitoring"
     - "self-healing system"
     - "autonomous execution"
     - "enterprise-grade" complexity without clear necessity

3. Use the **validation checklist**:
   - Confirm the solution is:
     - Testable
     - Observable
     - Maintainable by one developer
     - Proportionate to the problem's scale

## Goal

Raise the floor of solution quality and prevent over-engineered or operationally expensive designs that do not fit a solo developer context.
```

**File:** `P:\.claude\skills\validation-standards\PROHIBITED_PATTERNS.md`

```markdown
# Validation Standards – Prohibited Patterns

The following phrases and concepts are red flags in this environment and should trigger extra scrutiny or rejection:

- "continuous monitoring" (without a clear, low-overhead implementation)
- "self-healing system" or "self-healing infrastructure"
- "autonomous execution" or "runs on its own with no supervision"
- "enterprise-grade" when used to justify unnecessary complexity
- Any design that assumes a dedicated SRE/DevOps team
```

**File:** `P:\.claude\skills\validation-standards\VALIDATION_CHECKLIST.md`

```markdown
# Validation Standards – Checklist

For significant design or implementation decisions, verify:

1. **Scope Fit**
   - Solution complexity matches the actual problem.

2. **Solo-Developer Maintainability**
   - One person can understand, modify, and operate it.

3. **Operational Overhead**
   - No hidden need for 24/7 monitoring or complex orchestration.

4. **Testability**
   - There is a clear way to test the behavior locally.

5. **Failure Modes**
   - Common failure scenarios are identified and at least minimally addressed.
```

#### 2.3.2 assumption-auditing Skill

**File:** `P:\.claude\skills\assumption-auditing\SKILL.md`

```markdown
# Skill: assumption-auditing

## Purpose

Make hidden assumptions explicit before committing to a solution, especially for architectural or long-lived decisions.

## When to Use

- When designing or modifying architecture.
- When recommending tools, frameworks, or storage strategies.
- When performance, cost, or reliability are part of the decision.

## Behavior

When this skill is active:

1. List at least 3 key assumptions behind the recommendation.
2. Classify each assumption:
   - Low-risk (likely true, cheap to verify)
   - Medium-risk (uncertain, moderate impact)
   - High-risk (uncertain, high impact)
3. Highlight any high-risk assumptions and, where possible, propose a quick test or experiment that the user could run to validate them.

## Goal

Reduce the chance of committing to a design that rests on unexamined or fragile assumptions.
```

**File:** `P:\.claude\skills\assumption-auditing\ASSUMPTION_FRAMEWORK.md`

```markdown
# Assumption Auditing Framework

Use this template when applying assumption-auditing:

1. **Context Summary**
   - Briefly restate the decision or recommendation.

2. **Assumptions**
   1. Assumption A – [risk level]
   2. Assumption B – [risk level]
   3. Assumption C – [risk level]

3. **High-Risk Assumptions**
   - Highlight which assumptions are high-risk and why.

4. **Validation Ideas**
   - For each high-risk assumption, suggest a minimal experiment or measurement the user could run.
```

#### 2.3.3 uncertainty-expression Skill

**File:** `P:\.claude\skills\uncertainty-expression\SKILL.md`

```markdown
# Skill: uncertainty-expression

## Purpose

Express uncertainty clearly and appropriately instead of overconfident guessing.

## When to Use

- When data is missing, ambiguous, or contradictory.
- When asked about very recent events, niche tools, or private systems.
- When the model is extrapolating beyond training or clear patterns.

## Behavior

When this skill is active:

1. Explicitly mark uncertainty:
   - Use phrases like "I'm not certain", "This is an inference", or "This is speculative".

2. Separate knowns from unknowns:
   - Clearly state what is known with high confidence, and what is not.

3. Offer next steps:
   - Suggest concrete actions for the user to reduce uncertainty (e.g., run a command, check logs, inspect a file).

## Goal

Prevent misleading confidence and support collaborative investigation when information is incomplete.
```

**File:** `P:\.claude\skills\uncertainty-expression\WHEN_TO_SAY_UNKNOWN.md`

```markdown
# When to Say "I Don't Know"

Say "I don't know" (with explanation) when:

- The question depends on real-time data you cannot access.
- The answer depends on private, user-specific context you do not see.
- Evidence is conflicting and you cannot reasonably reconcile it.

In these cases, combine:
- A clear statement of uncertainty, and
- One or more suggestions for how the user could obtain the missing information.
```

#### 2.3.4 error-handling-cascade Skill

**File:** `P:\.claude\skills\error-handling-cascade\SKILL.md`

```markdown
# Skill: error-handling-cascade

## Purpose

Handle failures and errors in multi-step or multi-agent workflows without compounding the damage.

## When to Use

- When sub-agents, tools, or scripts fail.
- When a later step reveals that an earlier assumption was wrong.

## Behavior

When this skill is active:

1. Stop and summarize the failure.
2. Identify which previous steps depend on the failed assumption or result.
3. Propose a minimal rollback or corrective action.
4. Avoid proceeding with the workflow until the failure is addressed or explicitly accepted by the user.

## Goal

Prevent cascading failures and wasted effort after a critical error is detected.
```

**File:** `P:\.claude\skills\error-handling-cascade\SUBAGENT_FAILURE_PATTERNS.md`

```markdown
# Subagent Failure Patterns

Common patterns to watch for:

- Subagent returns incomplete or obviously inconsistent output.
- Subagent times out repeatedly on the same step.
- Subagent's view of the world conflicts with the main session (e.g., missing files).

In these cases, prefer:
- Diagnose-and-fix over "try again until it works".
```

**File:** `P:\.claude\skills\error-handling-cascade\RECOVERY_PROTOCOLS.md`

```markdown
# Recovery Protocols

For a failed step in a multi-step workflow:

1. Identify the earliest step that depends on the failed result.
2. Re-run from that step, not from the very beginning unless necessary.
3. Log or summarize what changed compared to the previous attempt.
4. Confirm with the user before taking irreversible actions.
```

#### 2.3.5 risk-adjusted-reasoning Skill

**File:** `P:\.claude\skills\risk-adjusted-reasoning\SKILL.md`

```markdown
# Skill: risk-adjusted-reasoning

## Purpose

Adjust the depth and rigor of reasoning based on the risk and impact of the decision.

## When to Use

- When a decision affects production systems, data integrity, or large time investments.
- When choosing long-lived technologies, storage formats, or infrastructure patterns.

## Behavior

When this skill is active:

1. Classify the decision impact:
   - Low: Easy to reverse, low cost of failure.
   - Medium: Some migration effort, moderate cost.
   - High: Hard to reverse, high cost if wrong.

2. Match reasoning depth to impact:
   - Low: Reasonable heuristics + quick validation is enough.
   - Medium: Combine heuristics with at least one concrete validation.
   - High: Use first-principles reasoning, assumption-auditing, and uncertainty-expression together.

## Goal

Ensure that high-impact decisions receive proportionally deeper analysis and explicit handling of risk.
```

**File:** `P:\.claude\skills\risk-adjusted-reasoning\DECISION_FRAMEWORK.md`

```markdown
# Decision Framework

Template for risk-adjusted decisions:

1. Impact level: [Low | Medium | High]
2. Options considered: [Option A, Option B, ...]
3. Key trade-offs: [performance, cost, complexity, flexibility]
4. Recommendation and rationale.
5. Follow-up checks or safeguards.
```

---

### 2.4 Hooks & Settings

#### 2.4.1 Global Hook Settings

**File:** `P:\.claude\settings.json`

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PreToolUse": [
        "hallucination_scanner",
        "tdd_validator",
        "assumption_auditor"
      ],
      "PostToolUse": [
        "reality_verifier"
      ],
      "SessionStart": [],
      "UserPromptSubmit": []
    }
  }
}
```

> Adjust events and hook names to match your actual hook files; this is a template.

#### 2.4.2 Example Hook – hallucination_scanner

**File:** `P:\.claude\hooks\scanners\hallucination_scanner.py`

```python
import json
import sys

"""Simple hallucination scanner hook.

Reads a JSON payload from stdin with fields:
- "prompt": user message
- "model_reply": model's draft reply

If potential hallucinations are detected (e.g., referencing files that don't exist
in the workspace listing), the hook can:
- Emit a warning message
- Suggest that the main process ask the model to verify paths

This is intentionally minimal; integrate with your actual hook protocol.
"""


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    data = json.loads(raw)
    prompt = data.get("prompt", "")
    reply = data.get("model_reply", "")

    warnings = []

    # Very basic heuristic: flag phrases that often accompany fabricated details.
    suspect_phrases = [
        "for example, consider the file",
        "you can find this in",
        "as defined in the file",
    ]

    for phrase in suspect_phrases:
        if phrase.lower() in reply.lower():
            warnings.append(f"Reply contains potentially fabricated reference: '{phrase}'")

    output = {
        "warnings": warnings,
        "ok": len(warnings) == 0
    }

    sys.stdout.write(json.dumps(output))


if __name__ == "__main__":
    main()
```

#### 2.4.3 Example Hook – assumption_auditor

**File:** `P:\.claude\hooks\scanners\assumption_auditor.py`

```python
import json
import sys

"""Assumption auditor hook.

Goal: detect when a model reply makes non-trivial recommendations without
explicitly stating assumptions.

Heuristic: if the reply is long and contains architectural language but
no words like "assumption" or "assume", we warn.
"""


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    data = json.loads(raw)
    reply = data.get("model_reply", "")

    architectural_terms = [
        "architecture",
        "microservice",
        "orchestration",
        "pipeline",
        "event-driven",
        "distributed",
    ]

    mentions_architecture = any(t in reply.lower() for t in architectural_terms)
    mentions_assumptions = "assumption" in reply.lower() or "assume" in reply.lower()

    warnings = []

    if len(reply) > 400 and mentions_architecture and not mentions_assumptions:
        warnings.append("Long architectural reply without explicit assumptions.")

    output = {
        "warnings": warnings,
        "ok": len(warnings) == 0
    }

    sys.stdout.write(json.dumps(output))


if __name__ == "__main__":
    main()
```

> Integrate with your existing hook protocol; this is structured to be easily adapted.

---

### 2.5 Project Template

#### 2.5.1 Template Project CLAUDE.md

**File:** `P:\Projects\_template\CLAUDE.md`

```markdown
# Project CLAUDE.md – Template

## Purpose

This file defines project-specific conventions and constraints.
It automatically appends to the global Cognitive Constitution from `~\.claude\CLAUDE.md`.

## Project-Specific Rules

- Describe project naming conventions.
- Describe preferred folder layout.
- Describe any project-only constraints (e.g., tools or libraries to avoid).

## Recommended Skills

When working in this project, the following skills are especially relevant:

- execution-clarity
- sequential-thinking
- validation-standards
- assumption-auditing
- risk-adjusted-reasoning
```

#### 2.5.2 Template Project Settings

**File:** `P:\Projects\_template\.claude\settings.json`

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PreToolUse": [
        "hallucination_scanner",
        "tdd_validator",
        "assumption_auditor"
      ],
      "PostToolUse": [
        "reality_verifier"
      ]
    }
  }
}
```

> Copy this into each new project's `.claude\` folder if you decide to use project-local hook settings.

---

### 2.6 Scripts (PowerShell)

#### 2.6.1 Backup Before Migration

**File:** `P:\__csf\scripts\backup-csf.ps1`

```powershell
param(
    [string]$RootDrive = "P:",
    [string]$BackupRoot = "P:\__csf\backups"
)

$claudeRoot = Join-Path $RootDrive ".claude"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $BackupRoot "claude_backup_$timestamp"

Write-Host "[CSF] Creating backup of .claude directory..." -ForegroundColor Cyan

if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot | Out-Null
}

if (Test-Path $claudeRoot) {
    Copy-Item -Path $claudeRoot -Destination $backupPath -Recurse
    Write-Host "[CSF] Backup created at: $backupPath" -ForegroundColor Green
} else {
    Write-Host "[CSF] No .claude directory found at $claudeRoot" -ForegroundColor Yellow
}
```

#### 2.6.2 Initialize Global CSF Structure

**File:** `P:\__csf\scripts\init-csf.ps1`

```powershell
param(
    [string]$RootDrive = "P:"
)

$csfRoot     = Join-Path $RootDrive "__csf"
$claudeRoot  = Join-Path $RootDrive ".claude"
$csfDocs     = Join-Path $csfRoot "docs"
$csfScripts  = Join-Path $csfRoot "scripts"

Write-Host "[CSF] Initializing Cognitive Steering Framework at $RootDrive" -ForegroundColor Cyan

# Ensure directories exist
$dirs = @($csfRoot, $claudeRoot, $csfDocs, $csfScripts, (Join-Path $claudeRoot "skills"), (Join-Path $claudeRoot "hooks"))
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "[CSF] Creating directory: $dir" -ForegroundColor DarkGray
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

# Create a default global CLAUDE.md if missing
$globalClaude = Join-Path $claudeRoot "CLAUDE.md"
if (-not (Test-Path $globalClaude)) {
    Write-Host "[CSF] Creating default global CLAUDE.md at $globalClaude" -ForegroundColor Yellow
    @"
# Cognitive Constitution (Global CLAUDE.md)

(placeholder – replace with your curated constitution)
"@ | Set-Content -Path $globalClaude -Encoding UTF8
}

Write-Host "[CSF] Initialization complete." -ForegroundColor Green
```

#### 2.6.3 Initialize a New Project

**File:** `P:\__csf\scripts\init-project.ps1`

```powershell
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [string]$RootDrive = "P:"
)

$projectsRoot = Join-Path $RootDrive "Projects"
$projectPath  = Join-Path $projectsRoot $ProjectName
$templateRoot = Join-Path $projectsRoot "_template"

if (-not (Test-Path $projectsRoot)) {
    New-Item -ItemType Directory -Path $projectsRoot | Out-Null
}

if (-not (Test-Path $templateRoot)) {
    Write-Host "[CSF] Template project not found at $templateRoot. Please create it first." -ForegroundColor Red
    exit 1
}

if (Test-Path $projectPath) {
    Write-Host "[CSF] Project already exists at $projectPath" -ForegroundColor Yellow
} else {
    Write-Host "[CSF] Creating project at $projectPath" -ForegroundColor Cyan
    Copy-Item -Path $templateRoot -Destination $projectPath -Recurse
}

Write-Host "[CSF] Project '$ProjectName' initialized." -ForegroundColor Green
```

#### 2.6.4 Validate CSF Structure

**File:** `P:\__csf\scripts\validate-csf.ps1`

```powershell
param(
    [string]$RootDrive = "P:"
)

$claudeRoot = Join-Path $RootDrive ".claude"

$expectedPaths = @(
    (Join-Path $claudeRoot "CLAUDE.md"),
    (Join-Path $claudeRoot "skills"),
    (Join-Path $claudeRoot "hooks")
)

$errors = @()

foreach ($p in $expectedPaths) {
    if (-not (Test-Path $p)) {
        $errors += "Missing expected path: $p"
    }
}

if ($errors.Count -eq 0) {
    Write-Host "[CSF] Structure validation passed." -ForegroundColor Green
} else {
    Write-Host "[CSF] Structure validation failed:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}
```

#### 2.6.5 Test Rollback Procedure

**File:** `P:\__csf\scripts\test-rollback.ps1`

```powershell
param(
    [string]$RootDrive = "P:",
    [string]$BackupRoot = "P:\__csf\backups"
)

<#
.SYNOPSIS
    Tests rollback procedure by restoring from a backup.

.DESCRIPTION
    This script allows testing the rollback flow without affecting the actual
    .claude directory. Use this to validate that backups can be restored
    successfully before doing the actual migration.

.NOTES
    WARNING: This will OVERWRITE your current .claude directory with the backup.
    Only use on a test workspace or when you're certain you want to rollback.
#>

$claudeRoot = Join-Path $RootDrive ".claude"

Write-Host "[CSF] Rollback Test - Available backups:" -ForegroundColor Cyan

if (-not (Test-Path $BackupRoot)) {
    Write-Host "[CSF] No backups found at $BackupRoot" -ForegroundColor Red
    exit 1
}

# List available backups
$backups = Get-ChildItem -Path $BackupRoot -Directory | Sort-Object LastWriteTime -Descending

if ($backups.Count -eq 0) {
    Write-Host "[CSF] No backups found" -ForegroundColor Yellow
    exit 0
}

for ($i = 0; $i -lt $backups.Count; $i++) {
    Write-Host "  [$i] $($backups[$i].Name) - $($backups[$i].LastWriteTime)" -ForegroundColor DarkGray
}

$selection = Read-Host "Enter backup number to restore (or 'c' to cancel)"

if ($selection -eq 'c') {
    Write-Host "[CSF] Rollback cancelled" -ForegroundColor Yellow
    exit 0
}

$selectedIndex = [int]$selection
if ($selectedIndex -lt 0 -or $selectedIndex -ge $backups.Count) {
    Write-Host "[CSF] Invalid selection" -ForegroundColor Red
    exit 1
}

$selectedBackup = $backups[$selectedIndex].FullName

Write-Host "[CSF] WARNING: This will REPLACE $claudeRoot with $selectedBackup" -ForegroundColor Red
$confirm = Read-Host "Type 'yes' to confirm"

if ($confirm -ne 'yes') {
    Write-Host "[CSF] Rollback cancelled" -ForegroundColor Yellow
    exit 0
}

# Remove existing .claude and restore from backup
Remove-Item -Path $claudeRoot -Recurse -Force
Copy-Item -Path $selectedBackup -Destination $claudeRoot -Recurse

Write-Host "[CSF] Rollback complete. .claude restored from backup." -ForegroundColor Green
```

---

## 3. Migration Plan (Simplified - No Feature Flags)

> This plan proceeds phase-by-phase with atomic changes. No feature flags are used.
> Each phase completes before moving to the next.

### 3.1 Pre-Migration Checklist

- [ ] Run `P:\__csf\scripts\backup-csf.ps1` to create a backup
- [ ] Run `P:\__csf\scripts\test-rollback.ps1` on a throwaway workspace to validate rollback
- [ ] Document any custom hooks or skills not covered in this design

### 3.2 Phase 1: Create Structure (Non-Breaking)

**Goal:** Set up directories without changing existing files.

1. Run `P:\__csf\scripts\init-csf.ps1` to create directory structure
2. Copy this design document to `P:\__csf\docs\CSF_SOLUTION_DESIGN.md`
3. Verify structure with `P:\__csf\scripts\validate-csf.ps1`

**Rollback:** Delete `P:\__csf\` directory. No other changes made.

### 3.3 Phase 2: Add New Skills (Non-Breaking)

**Goal:** Create new skills without modifying existing ones.

1. Create skill directories under `P:\.claude\skills\`:
   - `validation-standards\`
   - `assumption-auditing\`
   - `uncertainty-expression\`
   - `error-handling-cascade\`
   - `risk-adjusted-reasoning\`

2. Copy SKILL.md and supporting files from section 2.3

**Rollback:** Delete the new skill directories. Existing skills untouched.

### 3.4 Phase 3: Update Global CLAUDE.md (Breaking)

**Goal:** Slim the constitution while preserving all amendments.

1. Backup current `P:\.claude\CLAUDE.md`
2. Replace with slim version from section 2.2
3. **IMPORTANT:** Verify all constitutional amendments are preserved

**Rollback:** Restore from backup or run `P:\__csf\scripts\test-rollback.ps1`

### 3.5 Phase 4: Create Project Template (Non-Breaking)

**Goal:** Establish template for new projects.

1. Create `P:\Projects\_template\` directory
2. Add `CLAUDE.md` from section 2.5.1
3. Add `.claude\settings.json` from section 2.5.2

**Rollback:** Delete `P:\Projects\_template\` directory.

### 3.6 Phase 5: Migrate Existing Projects (Optional)

**Goal:** Apply CSF structure to existing projects.

For each existing project:
1. Add project-specific CLAUDE.md if needed
2. Copy template `.claude\settings.json` if project-local hooks are desired

**Rollback:** Remove added files on a per-project basis.

---

## 4. Step-by-Step Setup

1. **Create backup**
   - Open PowerShell as your user.
   - Run:
     ```powershell
     P:\__csf\scripts\backup-csf.ps1
     ```

2. **Run CSF initializer**
   - Run:
     ```powershell
     P:\__csf\scripts\init-csf.ps1
     ```
   - Confirm `P:\.claude\CLAUDE.md` exists and contains your constitution.

3. **Create or refine global CLAUDE.md**
   - Replace the placeholder content with the slim constitution provided above (2.2).

4. **Create skills directories & files**
   - Under `P:\.claude\skills\`, create the new skill directories and paste in the corresponding `SKILL.md` and support files from section 2.3.

5. **Configure hooks**
   - Create or update `P:\.claude\settings.json` with the template in section 2.4.1.
   - Ensure your hook executable names match those listed in `settings.json`.

6. **Create project template**
   - Under `P:\Projects\_template\`, create `CLAUDE.md` and `.claude\settings.json` from section 2.5.

7. **Initialize a new project**
   - Run:
     ```powershell
     P:\__csf\scripts\init-project.ps1 -ProjectName MyNewProject
     ```
   - This will create `P:\Projects\MyNewProject\` with the template files.

8. **Open Claude Code in the new project directory**
   - Work inside `P:\Projects\MyNewProject\` so that project CLAUDE.md and global CLAUDE.md both apply.

---

## 5. Configuration Reference

- **Global Configuration**
  - `P:\.claude\CLAUDE.md` – cognitive constitution
  - `P:\.claude\settings.json` – hook events and mapping
  - `P:\.claude\skills\` – cognitive skills
  - `P:\.claude\hooks\` – scanners, validators, repositories

- **Framework Documentation**
  - `P:\__csf\docs\` – design documents (this file)
  - `P:\__csf\scripts\` – setup and validation scripts

- **Project Configuration**
  - `P:\Projects\<name>\CLAUDE.md` – project-specific rules
  - `P:\Projects\<name>\.claude\settings.json` – optional per-project hook overrides

---

## 6. Testing Patterns

1. **Global CLAUDE.md Load Test**
   - Start Claude Code in any directory.
   - Ask: "Summarize the global cognitive constitution you see."
   - Verify principles match `P:\.claude\CLAUDE.md`.

2. **Skill Discovery Test**
   - Ask: "What skills are available?" or describe a task that should trigger a skill, e.g.:
     - "Design an architecture; please make assumptions explicit."
   - **Note:** Skill discovery is not always reliable. You may need to manually invoke:
     - `/use assumption-auditing`

3. **Hook Firing Test**
   - Craft a reply or scenario that should trigger `hallucination_scanner` or `assumption_auditor`.
   - Verify the hook output is logged or surfaced according to your integration.

4. **Project Inheritance Test**
   - In a project directory, ask Claude to summarize:
     - Global principles
     - Project-specific rules
   - Confirm both are visible and consistent.

5. **Rollback Test**
   - On a test workspace, run the migration phases.
   - Run `P:\__csf\scripts\test-rollback.ps1` to verify you can restore from backup.

---

## 7. Troubleshooting

1. **Skill Not Being Used**
   - Check that the skill directory name and `SKILL.md` are correct under `P:\.claude\skills\`.
   - Ensure the SKILL description actually matches the kind of task you're doing.
   - **Try manual invocation:** `/use <skill-name>`
   - Restart Claude Code so it reloads available skills.

2. **Hook Not Firing**
   - Confirm `P:\.claude\settings.json` has the hook name under the correct event.
   - Verify the executable file exists at the path referenced by Claude Code.
   - Add simple logging (e.g., write to a log file) inside the hook to confirm execution.

3. **CLAUDE.md Not Updating**
   - Verify you are editing `P:\.claude\CLAUDE.md`, not a reference copy.
   - Restart Claude Code to force re-loading of CLAUDE.md files.

4. **Project Rules Not Seen**
   - Ensure you have opened Claude Code from within `P:\Projects\<name>\`.
   - Confirm that `CLAUDE.md` in the project directory is valid Markdown and not empty.

5. **Rollback Failed**
   - Check that backup exists in `P:\__csf\backups\`
   - Manually copy backup contents to `P:\.claude\` if script fails
   - Report issues with rollback scripts for future improvements

---

## 8. Revision History

| Date | Change | Author |
|------|--------|--------|
| 2025-01-16 | Initial design draft | Claude + User |
| 2025-01-16 | Added clarifications: skill discovery reliability, untested rollback, __csf vs .claude distinction, removed feature flags | Claude + User |
| 2025-01-16 | Updated all paths to Windows backslash format | Claude + User |

---

**End of Document**
