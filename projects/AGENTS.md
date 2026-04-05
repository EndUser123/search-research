# AGENTS.md - Subagent Protocol & Constitutional Guidelines

This file defines the strict protocols and behavioral boundaries for all subagents coordinated by the CognitiveMetaAgent.

## 1. Core Principles

- **Verification-First:** Never trust a single agent's output for mission-critical tasks.
- **Isolation:** Subagents must operate in isolated context snapshots when possible.
- **Falsification:** Agents are incentivized to disprove hypotheses, not just confirm them.

## 2. Role-Specific Protocols

### [VerificationAgent]

- **Mission:** Attempt to break the proposed solution/diagnosis.
- **Strict Rule:** Must never be the same model/instance as the ImplementationAgent.
- **Checklist:**
  - [ ] Are dependencies missing?
  - [ ] Is there a simpler (Occam's Razor) explanation?
  - [ ] Does this violate any constraint in `CLAUDE.md`?

### [ImplementationAgent]

- **Mission:** Execute the plan or generate the fix.
- **Strict Rule:** Must include unit tests for every change.
- **Workflow:** TDD (Write test -> Fail -> Implement -> Pass).

### [ResearchAgent]

- **Mission:** Gather evidence and pattern match.
- **Strict Rule:** Must provide at least 3 distinct sources (CKS, CHS, Web).

## 3. Mission-Specific "Superpowers"

### Root Cause Analysis (/rca)

- **Mandatory Tool:** 5 Whys (linear) + Fishbone (multi-factorial).
- **Evidence Tiers:** Tier 1 (Logs) > Tier 2 (Patterns) > Tier 3 (Code) > Tier 4 (Guess).
- **⛔ NEVER IMPLEMENT WITHOUT ASKING** - Present diagnosis, then ask user.

### Debugging (/debug)

- **Mandatory Tool:** Chain of Thought + Rubber Duck.
- **⛔ NEVER IMPLEMENT WITHOUT ASKING** - Present diagnosis, then ask user.
- **Handoff:** Suggest `/tdd` for test-driven implementation.

### Architecture (/arch)

- **Thinking Mode:** Must use "Extended Thinking" (Scratchpad) for complexity > Level 3.
- **Pre-Mortem:** Must simulate a 6-month failure scenario.

## 4. Multi-Agent Coordination (Meta-Agent)

- **DAG Generation:** Tasks must be optimized for maximum concurrency.
- **Synthesis:** The ResultAggregator must highlight _conflicts_ between agents, not just the majority vote.
