# Review Bundle: /hook-audit Skill
**Generated**: 2026-03-26T19:20:00Z
**Scope**: P:/.claude/skills/hook-audit/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: hook-audit
- **Description**: Hook behavioral compliance monitoring - tracks LLM compliance with hook injections, blocking rates, and escalation decisions
- **Category**: observability
- **Trigger**: `/hook-audit`, "hook compliance", "hook health", "behavioral audit"
- **Aliases**: `/hook-audit`

### Domain & Purpose
Monitor and analyze LLM behavioral compliance with hook system interventions. Tracks whether injected instructions are followed, measures blocking effectiveness, and recommends Phase 1 → Phase 2 escalations.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Python
- **Key Integration**: `P:/.claude/hooks/hook_audit_dashboard.py`

---

## 2. EXECUTION DIRECTIVE

**When invoked, run the hook audit dashboard:**

```bash
# Default: Full dashboard
python P:/.claude/hooks/hook_audit_dashboard.py

# With subcommand
python P:/.claude/hooks/hook_audit_dashboard.py blocks
python P:/.claude/hooks/hook_audit_dashboard.py assumptions
python P:/.claude/hooks/hook_audit_dashboard.py attribution
python P:/.claude/hooks/hook_audit_dashboard.py health
python P:/.claude/hooks/hook_audit_dashboard.py escalation
python P:/.claude/hooks/hook_audit_dashboard.py replay
python P:/.claude/hooks/hook_audit_dashboard.py reasoning

# Custom time period
python P:/.claude/hooks/hook_audit_dashboard.py --days 14

# Terminal filtering (v2.1)
python P:/.claude/hooks/hook_audit_dashboard.py --terminal
python P:/.claude/hooks/hook_audit_dashboard.py --all
```

---

## 3. SUBCOMMANDS

### Default (no args) - Decision Pattern Monitoring
Shows next step pattern detection effectiveness:
- Decision type distribution (validates 86%/10%/3%/2% assumptions)
- Option extraction rates
- Actual vs expected pattern accuracy
- Recommendations for fine-tuning detection patterns

### blocks
Blocking effectiveness metrics

### assumptions
Assumption compliance tracking

### attribution
Attribution accuracy monitoring

### health
Overall hook system health

### escalation
Phase 1 → Phase 2 escalation rates

### replay
Decision replay analysis

### reasoning
Reasoning pattern analysis

---

## 4. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Error Handling | GOOD | Dashboard-based execution |
| Documentation | GOOD | 80+ line SKILL.md with subcommands |
| Hook Integration | EXCELLENT | Monitors hook compliance |

### SQA Relevance
- **HIGH** — Observability skill for hook system
- Tracks LLM compliance with hook interventions
- Measures blocking effectiveness
- Identifies behavioral issues
