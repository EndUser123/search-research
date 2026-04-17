# Quality Gates Architecture

## Overview

Two-tier quality system with automatic escalation based on failure severity, plus opportunity tracking.

```
COMMIT → 🔔 /r (preventive self-review)
       → 💡 /brainstorm (heavyweight analysis)
       → 📝 opportunities.md (pattern-based suggestions)

FAILURE → 🚨 /r
              ├── Single failure → Phase 1 (self-diagnostic)
              └── Loop (3+ failures) → Phase 2 (auto @code-critic)
```

## Commands

| Command | Trigger | Purpose | Weight |
|---------|---------|---------|--------|
| `/r` | 🔔 after commit or 🚨 failure | Deterministic pre-mortem + failure triage | Self → @code-critic |
| `/q` | Manual | Fast opportunity/risk surface from current session | Light (single pass) |
| `/brainstorm` | 💡 after commit | Multi-persona opportunity analysis | Heavy (LLM personas) |

## Escalation Logic

| Condition | Response |
|-----------|----------|
| Single edit failure | `/r` Phase 1 (self-review) |
| Loop: 3+ failures on same file in 3min | `/r` Phase 2 → auto-spawn `@code-critic` |
| Pattern check = "recurring" | `/r` Phase 2 → auto-spawn `@code-critic` |
| Uncertainty after Phase 1 | Manual escalation to `@code-critic` |

## Agent

| Agent | Purpose | When Invoked |
|-------|---------|--------------|
| `@code-critic` | Independent diagnostic with fresh context | Loop detected, recurring pattern, or manual escalation |

## Files

| File | Location | Purpose |
|------|----------|---------|
| `/r` command | `P:\.claude\skills\r\SKILL.md` | Deterministic pre-mortem, refine, and failure triage |
| `/q` command | `P:\.claude\skills\q\SKILL.md` | Fast opportunity/risk surface |
| `/brainstorm` command | `P:\__csf\src\commands\nip\brainstorm.md` | Multi-persona opportunity analysis |
| `@code-critic` agent | `P:\.claude\agents\code-critic.md` | Independent review for escalated cases |
| Poka-yoke hook | `P:\.claude\hooks\poka-yoke.py` | Detects failures, adds 🚨 notifications |
| Auto-commit hook | `P:\.claude\hooks\auto_commit_hook.py` | Commits, adds 🔔💡 notifications, logs opportunities |
| Opportunities log | `P:\.claude\logs\opportunities.md` | Accumulated suggestions from commits |

## Notifications

| Icon | Type | Source | Meaning |
|------|------|--------|---------|
| 🔔 | `duf` | `auto_commit` | Session ended with commit. Run `/r`. |
| 💡 | `brainstorm` | `auto_commit` | Session complete. Run `/brainstorm` for deep analysis. |
| 🚨 | `warning` | `poka_yoke` | Edit failure or loop detected. Run `/r`. |

## Opportunity Tiers

| Tier | Command | What It Does |
|------|---------|--------------|
| Light | `/q` | View pattern-matched suggestions from git diff |
| Heavy | `/brainstorm` | Multi-persona AI analysis with adversarial debate |

## Opportunities Detection (Light)

Auto-commit analyzes git changes and logs suggestions to `opportunities.md`:

| Pattern | Opportunity |
|---------|-------------|
| New `.py` file (not test) | Consider adding tests |
| New command `.md` | Add to command index |
| New hook file | Verify registered in settings.json |
| Config/settings changed | Validate config, migration notes |
| 3+ files in same dir | Consider shared module/refactor |
| Deleted file | Verify no stale references |
| Hook modified | Test hook behavior |

## Feedback Loop

```
@code-critic findings
        │
        ├── recommended_additions.to_r  → Improve /r checks
        ├── recommended_additions.to_oops → Improve /r checks  
        └── new_hook                      → Structural prevention
```

## Cognitive Techniques Used

### /r (Preventive)
- **Pre-mortem**: "It's next week. Something broke. What was it?"
- **Inversion**: "What's the easiest way this could fail?"
- **Blast radius**: "What depends on what I changed?"
- **Assumption audit**: "What did I assume without verifying?"

### /r (Failure Triage)
- **Five Whys**: Dig to root cause, not symptom
- **Assumption audit**: Find the false belief
- **Pattern check**: Detect recurring mistakes
- **Counterfactual**: "What would have caught this earlier?"

### @code-critic (Independent)
- **Fresh Five Whys**: Ignore prior analysis, start from evidence
- **CHS lookup**: Check for similar past issues
- **Independent verification**: Actually run tests/checks
- **Structural prevention**: Prevent category, not just instance

### /brainstorm (Heavy)
- **Multi-persona**: Innovator, Pragmatist, Critic perspectives
- **Adversarial debate**: Ideas challenged and refined
- **Context inference**: Auto-detects topic from session if not provided
- **Actionable output**: Next steps with executable commands

## Design Principles

1. **Severity-based routing**: Single failure = self-review; Loop = escalate
2. **Remove decision points**: Biased self shouldn't decide whether to escalate
3. **Structural over behavioral**: Hooks > instructions
4. **Feedback integration**: Findings improve future checks
5. **Opportunity tiers**: Light (pattern) vs Heavy (LLM) analysis options
