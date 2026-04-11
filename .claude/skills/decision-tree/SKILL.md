---
name: decision-tree
description: Enhanced decision tree framework for complex architectural decisions.
version: "1.0.0"
status: stable
category: strategy
enforcement: advisory
triggers:
  - 'architecture decisions'
  - 'resource lifecycle questions'
  - 'multi-phase workflows'
  - 'complex tradeoffs'
aliases:
  - '/decision-tree'

suggest: []

workflow_steps:
  - Identify the decision requiring analysis
  - Apply 5-dimensional framework (options, states, lifecycles, phases, purpose)
  - Map state transitions for each option
  - Analyze resource lifecycles (persistent/ephemeral/mixed)
  - Consider operation phases (before/during/after/never)
  - Clarify purpose for each resource involved
  - Generate recommendation with explicit justification
---

# Decision Tree - Enhanced Framework

**Systematic decision-making for complex architectural problems.**

---

## When to Use This Framework

Use the 5-dimensional decision tree for:
- **Architecture decisions** - System design, component boundaries, data flow
- **Resource management** - Storage, caching, cleanup strategies, lifecycle planning
- **Multi-phase workflows** - Operations with time dependencies, state transitions
- **Integration planning** - Connecting systems with different lifecycles
- **Tradeoff analysis** - Comparing approaches with state machine modeling

**When simple trees suffice:**
- Binary choices (flag on/off, single parameter)
- Stateless operations (no resource lifecycle concerns)
- Routine decisions (well-understood patterns, no novelty)

---

## Quick Reference

**For complex decisions:**
→ Apply all 5 dimensions systematically
→ Model state transitions explicitly
→ Question lifecycle assumptions
→ Consider multi-phase timing
→ Clarify purpose before recommending

**Framework documentation:** `references/enhanced_decision_tree.md`
**Case studies:** `references/examples/` (coming soon)

---

## Core Principle

> **Decisions are state transitions, not static choices.**

Every decision involves:
- Current state → Next state → Final state
- Resources with lifecycles (persistent/ephemeral)
- Timing considerations (before/during/after)
- Purpose-driven design (WHY does this exist?)

Traditional decision trees miss options by treating decisions as "A vs B" choices. Enhanced trees model state transitions, lifecycles, and phases to catch hidden options.

---

## References

- **Enhanced framework:** `references/enhanced_decision_tree.md` — Complete 5-dimensional framework with case studies
- **Related:** `P:/.claude/skills/subagent-first/DECISION_TREE.md` — When to use subagents vs direct execution

