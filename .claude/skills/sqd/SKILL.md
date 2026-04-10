---
name: sqd
description: "Strategic + Deterministic Quality - intelligent orchestration combining strategic assessment and deterministic refinement with auto-routing"
version: 1.2.0
status: stable
category: quality
enforcement: advisory
triggers:
  - /sqd
  - /sqd --strategic-only
  - /sqd --refine-only
aliases:
  - /sqd

suggest:
  - /sqa
  - /s
  - /p
  - /rns

depends_on_skills: []
workflow_steps:
  - auto_route: QR0 - Detect scope and select applicable checks
  - strategic_checks: QR1 - Run strategic quality (architecture, patterns, tech fit) if applicable
  - deterministic_checks: QR2 - Run deterministic refinement (omissions, plan validation) if applicable
  - synthesize: QR3 - Merge findings, assess health, generate improvements
  - render_output: QR4 - Produce /rns-formatted output
  - decide_next: QR5 - Escalation decisions (/s, /p, /rns)

parameters:
  - name: mode
    description: "Run specific mode: strategic-only, refine-only, or full (auto)"
    type: string
    required: false
  - name: target
    description: "Target path or topic to analyze"
    type: string
    required: false

test_prompts:
  - description: "Full intelligent pipeline"
    prompt: "/sqd"
    expected_behavior: "Auto-detects scope, runs applicable strategic+deterministic checks, outputs /rns-formatted findings"
  - description: "Strategic only"
    prompt: "/sqd --strategic-only"
    expected_behavior: "Runs only /q-style strategic checks (architecture, patterns, tech fit), skips deterministic refinement"
  - description: "Refine only"
    prompt: "/sqd --refine-only"
    expected_behavior: "Runs only /r-style deterministic checks (omissions, plan validation), skips strategic analysis"

do_not:
  - use "lock ordering" or "enterprise-grade" patterns
  - suggest background services or real-time metrics
  - suggest autonomous execution or self-healing
  - require team approval
  - recommend re-running /sqd as a next step (validation loops waste time)
  - run all checks regardless - use intelligent routing

---

# /sqd - Intelligent Quality Orchestration

## Purpose

**Intelligent quality orchestration** that combines strategic quality assessment (/q) and deterministic refinement (/r) with auto-routing to skip unnecessary work.

**What it does:**
- Auto-detects scope and runs only applicable checks
- Strategic: architecture soundness, design patterns, technology fit
- Deterministic: omissions, plan validation, improvements
- Outputs /rns-formatted actions

**Scope boundary:**
- `/sqd` = Intelligent strategic + deterministic quality
- `/sqa` = Code-focused 8-layer pipeline (syntax, semantic, structural, etc.)
- `/arch` = Architecture decisions and routing
- `/p` = Tactical implementation quality

**Anti-pattern:** Don't use `/sqd` for tactical implementation bugs. That's `/p`'s job.

## Auto-Routing Logic

**QR0: Scope Detection determines which checks run:**

| Condition | Strategic Checks | Deterministic Checks |
|-----------|------------------|---------------------|
| Architecture/migration scope | ✓ | ✓ |
| New feature implementation | ✓ | ✓ |
| Bug fix only | ✗ | ✓ (omissions) |
| Documentation only | ✗ | ✓ (completeness) |
| Plan review only | ✓ | ✓ |
| Code review only | ✓ | ✓ |

**Override flags:**
- `--strategic-only`: Force strategic checks only
- `--refine-only`: Force deterministic checks only
- No flag: Auto-route based on scope detection

## Your Workflow

### QR0: Auto-Route (Scope Detection)

Detect what we're analyzing:

```python
# Scope detection signals
has_architecture = any(
    signal in prompt.lower()
    for signal in ["architecture", "design", "structure", "layer", "boundary"]
)
has_plan = any(
    signal in prompt.lower()
    for signal in ["plan", "spec", "requirement", "implementation"]
)
has_code = any(
    signal in prompt.lower()
    for signal in ["code", "implement", "function", "class", "file"]
)
is_bug_fix = any(
    signal in prompt.lower()
    for signal in ["bug", "fix", "error", "broken", "fail"]
)

# Route to applicable checks
run_strategic = has_architecture or has_plan or (has_code and not is_bug_fix)
run_deterministic = True  # Always useful for omissions
```

### QR1: Strategic Checks (if routed)

From /q - Run 4 parallel subagents via Agent tool:
- Architecture & Structure
- Design Patterns & Domain
- Technology Fit & Engineering Balance
- Library Strategy

Synthesize findings, assess health (Sound/Concerning/Critical).

### QR2: Deterministic Checks (if routed)

From /r - Run applicable checks:
- Omission checklist from context/session
- Scope classification (trivial|moderate|significant|major)
- DUF-derived checks (Distributed, Undoable, Fault-tolerant)
- SRPI protocol (Searched? Read? Planned? Minimal?)
- Library-first checks
- Plan validation (if plan intent present)
- Standards audit (if metadata in scope)

### QR3: Synthesize

Merge strategic and deterministic findings:
- Dedupe by (file, line, category)
- Resolve severity conflicts
- Detect consensus (2+ checks agree)
- Generate deterministic improvements

### QR4: Render Output

**Always output /rns format:**

```
1 🔧 QUALITY (N)
  1a [recover/high] ...
  1b [prevent/med] ...

2 📄 DOCS (N)
  2a [realize/low] ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 — Do ALL Recommended Next Steps (N items)
```

### QR5: Decide Next

Emit escalation decision:
- `escalate_to_s: yes/no + reason` (if architecture/migration scope)
- `suggest_sqa: yes/no` (if code quality issues found)
- `next_commands: [/arch, /planning, /rns, /p, /sqa]`

## Escalation Rules

Set `escalate_to_s: yes` when:
- Architecture/migration/rewrite scope is implied
- Multiple high-risk signals are present
- Deterministic pass has low confidence or conflicting tradeoffs

Suggest `/sqa` when:
- Code quality issues are found (syntax, semantic, structural)
- Test coverage gaps detected
- Implementation verification needed

## Backward Compatibility

Legacy shorthands still work:
- `/sqd` → Full intelligent pipeline
- `/sqd1` or `/sqd --strategic-only` → Strategic checks only
- `/sqd2` or `/sqd --refine-only` → Deterministic checks only

## What This Does NOT Do

- Does NOT check tactical implementation (tests, lint, bugs) — that's `/p` or `/sqa`
- Does NOT check for omissions in isolation — that's what deterministic checks are for
- Does NOT HALT — errors degrade gracefully
- Does NOT recommend re-running itself — user controls validation cadence
- Does NOT run all checks regardless — uses intelligent routing
