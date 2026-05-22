---
name: prompt-refiner
description: Executable prompt specification system with constitutional compliance and cognitive techniques
category: strategy
triggers:
  - /prompt-refiner
aliases:
  - /prompt-refiner
---

# Prompt Refiner v14.0

Meta-prompt system for high-reliability LLM systems with executable specifications and constitutional compliance.

**Main Implementation:** `P:\\\\\\__csf/src/csf/cli/nip/prompt_refiner.md`

## Quick Start

```bash
/prompt-refiner analyze "your prompt here"      # Analyze and refine
/prompt-refiner triage "task description"       # Rapid triage routing
/prompt-refiner template                        # Show triage template
```

## Rapid Triage

Answer three questions to route to appropriate cognitive technique:

**Q1: Reversibility?**
- 1.0-1.25 (trivial) → MIN-EFFORT: CoT only
- 1.5-1.75 (moderate) → STANDARD: ToT + Self-Consistency
- 2.0 (irreversible) → MAXIMUM-SAFETY: Multi-Agent + Full Matrix

**Q2: Dependencies?**
- 0-1 → Chain-of-Thought
- 2-4 → Tree-of-Thoughts + Self-Consistency
- 5+ → Multi-Agent Debate

**Q3: Evidence available?**
- YES → Tier 1 ceiling 95%
- NO → Tier 3 ceiling 75%
- UNCERTAIN → Tier 4 ceiling 50%

## Cognitive Techniques

- **Chain-of-Thought** - For trivial reversibility, low dependencies
- **Tree-of-Thoughts** - For moderate complexity with self-consistency checking
- **Multi-Agent Debate** - For high complexity and irreversible operations

## PHASE STRUCTURE

```
PHASE 1: TRIAGE (Generation) — Apply Q1-Q3 decision matrix for method selection
    ↓ STOP: Present routing decision before applying template
PHASE 2: APPLY (Generation) — Generate prompt using appropriate cognitive technique template
    ↓ STOP: Present enhanced prompt before compliance check
PHASE 3: VALIDATE (Validation) — Ensure constitutional compliance and quality
```

**STOP conditions:**
- Between PHASE 1 and PHASE 2: STOP after technique selected (confirm routing)
- Between PHASE 2 and PHASE 3: STOP after prompt generated (present for review)
- Between PHASE 3 and end: STOP after compliance verified (user sees result)

**Key separation**: Triage is Generation. Template application is Generation. Compliance validation is Validation.
