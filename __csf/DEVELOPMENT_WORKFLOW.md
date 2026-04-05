# Development Workflow Clarification

## Context: Heavy AI-Assisted Development

This document clarifies what development patterns are appropriate for the CSF NIP project.

### Project Reality

- **User Role**: Technical director/architect - provides requirements, reviews work, guides direction
- **AI Role**: Primary developer - writes code, tests, documentation under user guidance
- **Team Size**: 1 human director + multiple AI agents (Claude, subagents, MCP servers)
- **Quality Priority**: Thoroughness > speed. Correctness > velocity.
- **Code Authorship**: 95%+ AI-generated under human direction

## What This Means for Tool Design

### ✅ Appropriate: Director + AI Workforce Patterns

These patterns support the director model:

**LLM-Generated Tests**
- AI creates functional tests, integration scenarios, performance checks
- DSLs and guardrails prevent hallucination
- Verification cycles ensure tests actually fail on bad code
- **Why appropriate**: You don't write tests manually. AI does it under your direction.

**Quality-First Tooling**
- Thorough functional verification (import modules, call functions, assert results)
- Complete integration flows (test end-to-end workflows)
- Risk-aware testing (test what changed based on impact analysis)
- **Why appropriate**: You care about correctness, not speed. "Does it work?" is the first question.

**Risk Engines and Context Models**
- Compute risk scores based on what changed
- Decide test depth based on module criticality (core vs peripheral)
- Trigger integration flows when boundaries are crossed
- **Why appropriate**: Guides AI workforce on what to test. Not autonomous — you trigger `/t`, it computes plan.

**DSLs for LLM Output**
- Constrained YAML/JSON schemas for test scenarios
- Prevents LLM hallucination
- Makes tests reviewable (you read YAML, not Python)
- **Why appropriate**: Smart AI management. You approve scenarios, AI generates code.

**Integration Flow Definitions**
- YAML files defining complete workflows (e.g., "edit file → run hook → check output")
- Living documentation that also tests
- Updated by AI when architecture changes
- **Why appropriate**: Knowledge capture + testing in one. You review, AI maintains.

**Performance Baselines**
- Quality gates for critical paths (e.g., "TDD-95 planning <150ms")
- Prevents performance rot over time
- **Why appropriate**: Quality monitoring, not "real-time metrics" (which are forbidden)

### ❌ Inappropriate: True Anti-Patterns

These patterns violate constraints:

**Background Autonomous Services**
- Services running without user oversight/trigger
- Self-healing systems that modify code without human approval
- Always-on monitoring daemons
- **Why wrong**: Autonomous execution without human direction violates constitutional constraints

**Self-Modifying Code**
- Code that updates itself based on runtime learning
- Auto-expanding test suites without review
- **Why wrong**: You lose control. AI should propose, you approve.

**Real-Time Monitoring Dashboards**
- Always-running metrics collection
- Live performance graphs
- **Why wrong**: Requires background service. Use query-based metrics instead.

**Team Approval Gates**
- Consensus processes for single-director workflow
- Multi-person review committees
- **Why wrong**: You're solo. "Team approval" is an enterprise pattern.

**Enterprise Concurrency Patterns**
- Lock-free multi-terminal coordination
- Distributed transactions
- Complex message queues for local operations
- **Why wrong**: Over-engineering for single-developer workflow.

## The Critical Distinction

### ✅ User-Directed AI Execution
```
You: /t research_fetcher.py
AI: Computes risk → Plans tests → Runs functional → Checks coverage → Reports
You: Review results → Approve or request changes
```
This is **appropriate**. You trigger, AI executes, you review.

### ❌ Autonomous Background Execution
```
System: Watching files... detected change... auto-running tests... auto-fixing...
```
This is **wrong**. No human in the loop.

## Practical Examples

### Appropriate: `/t` Command with Risk Engine

```python
# You invoke:
/t shared_libs/

# System does:
1. Compute risk: "core modules changed → high impact"
2. Plan tests: T1 (functional) + T2 (coverage) + T3 (integration)
3. Execute: Run tests, collect results
4. Report: "15 tests passed, 0 failed. Systems functional."

# You review results and decide next steps
```

**Why this works**: You're in control. The risk engine is a **decision support tool**, not an autonomous agent.

### Inappropriate: Self-Healing Test System

```python
# Bad pattern:
test_daemon:
  watch: ["src/**/*.py"]
  on_change:
    - run_tests
    - if_failing:
      - ai_generate_fix
      - apply_fix
      - commit
```

**Why this fails**: No human approval. Autonomous execution. Violates "no background services" rule.

## Guideline for AI Agents

When building tools for this workflow:

### DO:
- Create tools that **assist** AI agents under user direction
- Use LLM generation with **guardrails** (DSLs, validation, verification)
- Build **quality-first** tooling (thorough > fast)
- Design **decision support** (risk engines, context models)
- Enable **user review** (show plans, request approval)

### DON'T:
- Build **autonomous** systems (run without trigger)
- Create **background services** (always-on daemons)
- Implement **self-modifying** code (auto-updates without approval)
- Use **enterprise patterns** (complex when simple works)
- Remove **human oversight** (you must be in the loop)

## Summary

Your workflow is **director + AI workforce**, not traditional solo dev. Tools should:

1. **Support AI labor** (test generation, scenario creation, code synthesis)
2. **Maintain your control** (you trigger, you review, you approve)
3. **Prioritize quality** (thoroughness > speed, correctness > velocity)
4. **Use smart constraints** (DSLs, validation, verification cycles)

The "solo-dev constraints" in `slc.md` apply to **autonomous background systems**, not **AI-directed development**.
