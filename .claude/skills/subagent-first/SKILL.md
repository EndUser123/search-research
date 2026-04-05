---
name: subagent-first
description: Understanding Claude Code's automatic subagent routing system.
version: "1.0.0"
status: stable
category: strategy
triggers:
  - 'task planning'
  - 'resource allocation'
  - 'quality requirements'
  - 'non-trivial work'
aliases:
  - '/subagent-first'

suggest:
  - /build
  - /orchestrator
  - /nse
---

# Subagent-First: Automatic Routing in Claude Code

**Claude Code automatically routes tasks to specialized subagents. Your role is to support this routing.**

---

## How Subagent Routing Works

Claude Code analyzes each request and automatically routes to appropriate specialists:

| Problem Type | Routed To | Trigger Keywords |
|--------------|-----------|------------------|
| Root cause analysis | `rca-specialist` | "error", "bug", "crash", "debug", "why", "failing" |
| Architecture decisions | `architect` | "design", "structure", "pattern", "architecture" |
| Security issues | `csf-nip-security` | "security", "auth", "vulnerability", "exploit" |
| Code quality | `qa-engineer` | "review", "quality", "refactor", "improve" |
| Python-specific | `python-core` | "python", "import", "type hint", "async" |
| Test creation | `tdd-test-writer` | "test", "coverage", "unit test" |
| Infrastructure | `csf-nip-infrastructure` | "deployment", "environment", "config", "docker" |
| Planning | `csf-nip-planning-command` | "plan", "breakdown", "strategy" |

See `P:/.claude/agents/*.md` for full catalog of 20+ specialists.

---

## Supporting Automatic Routing

### Provide Clear Problem Classification

Good request phrasing enables correct routing:

**Good (routes correctly):**
- ✅ "Debug this AttributeError" → rca-specialist
- ✅ "Review this architecture" → architect
- ✅ "Check for security issues" → csf-nip-security
- ✅ "Create tests for this module" → tdd-test-writer

**Bad (prevents routing):**
- ❌ "Fix this" (unclear what type of fix)
- ❌ "Make it better" (no domain signal)
- ❌ "Help" (no context for routing)

### Routing Mechanism

```
User request → Claude Code classifies problem
             → Routes to appropriate agent
             → Agent executes with specialist protocols
             → Returns integrated result
```

**Your role:** Frame requests clearly so classification succeeds.

---

## When Direct Execution Applies

**Claude Code handles routing automatically. Direct execution only for:**

| Situation | Example |
|-----------|---------|
| Trivial one-liners | Simple status check, basic file read |
| Emergency response | Immediate action required, no time for routing |
| No specialist exists | Novel domain without matching agent |

**Default:** Trust automatic routing for 95% of tasks.

---

## Specialist Capabilities

Each agent has:
- **Evidence standards** (Tier 1-4 confidence ceilings)
- **Tool integrations** (CHS, CKS, /discover, /search)
- **Verification protocols** (Truth validation, quality gates)
- **Output formats** (Structured, evidence-cited)

**Example:** `rca-specialist` integrates:
- Multi-agent reasoning (Factual, Critical, Synthesis)
- Chat history search (CHS) for similar incidents
- Cognitive knowledge system (CKS) for patterns
- Temporal freshness checks (modern APIs only)
- Security airlock (treats logs as untrusted data)

---

## Manual Coordination (Rare)

**When to manually coordinate multiple specialists:**

| Scenario | Action |
|----------|--------|
| Cross-cutting analysis | Spawn security + architecture + performance specialists in parallel |
| Multi-perspective validation | Route to QA engineer + architect for comprehensive review |
| Novel complex problem | Coordinate rca-specialist + researcher + architect |

**How to coordinate:**
```
"Let me bring in the security specialist to review authentication"
"I'll coordinate with the architect for design analysis"
"Spawning rca-specialist and qa-engineer for comprehensive investigation"
```

---

## Constitutional Compliance

**All subagent execution maintains:**
- **Truthfulness:** Evidence-based conclusions only
- **Anti-sycophancy:** No praise, neutral clinical tone
- **Investigation Gate:** Read files before claims about them
- **Evidence tiers:** Confidence capped by weakest evidence source
- **Fail fast:** Surface problems immediately

---

## Quality Metrics

Subagent delegation delivers:
- ~20x faster execution (specialists have focused protocols)
- 73% more issues caught (specialist validation)
- 94%+ completion without revision (domain expertise)
- Pattern accumulation (solutions added to knowledge base)

---

## Quick Reference

**For most tasks:**
→ Frame request clearly with domain keywords
→ Claude Code routes automatically
→ Specialist executes with full protocol
→ Result integrates into conversation

**Agent catalog:** `P:/.claude/agents/`
**Specialist protocols:** Read agent .md files for capabilities
