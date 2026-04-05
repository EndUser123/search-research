# Tree-of-Thought (ToT) Integration

## Overview

/q integrates Tree-of-Thought (ToT) reasoning for enhanced question branching and scenario exploration.

## What This Does

Automatically generate branching scenarios for strategic quality questions to discover alternative analysis paths beyond manual question enumeration.

## Question Branch Types

### Architecture Analysis Branches

- **sure**: Standard layer separation, clear module boundaries
- **maybe**: Mixed concerns, fuzzy boundaries, some coupling
- **unlikely**: God object, tight coupling, no layer separation

### Design Pattern Branches

- **sure**: Appropriate patterns, no anti-patterns detected
- **maybe**: Some anti-patterns, pattern misuse risks
- **unlikely**: Widespread anti-patterns, cargo cult programming

### Technology Fit Branches

- **sure**: Right tool for problem, balanced engineering
- **maybe**: Over-engineering signals or under-engineering risks
- **unlikely**: Wrong technology, major engineering imbalance

## Integration Point

Q2 (Strategic Collection) subagent analysis (automatic enhancement):

```
Q2: Strategic Collection
  ├─ Subagent A: Architecture → ToT branching scenarios
  ├─ Subagent B: Design Patterns → ToT branching scenarios
  ├─ Subagent C: Technology Fit → ToT branching scenarios
  └─ Subagent D: Library Strategy → ToT branching scenarios
```

Q4 (Render Output) branch selection by health level:

**Sound Health Branch:**
- Architecture analysis → Design patterns → Technology fit → Opportunities → Next steps

**Concerning Health Branch:**
- Strategic risks table → Analysis sections → Recommended actions → Next steps

**Critical Health Branch:**
- Critical risks table with impact → All concerns (priority order) → Immediate actions → Next steps

## Example Output

```
ToT Analysis: Question Branching
==================================

Architecture Analysis:
  Branch 1 (sure): Layer separation detected, clear boundaries - 75% confidence
  Branch 2 (maybe): Mixed concerns in service layer - 20% confidence
  Branch 3 (unlikely): God object pattern - 5% confidence

Selected: Branch 1 (sure) with Branch 2 (maybe) as secondary

Technology Fit:
  Branch 1 (sure): Appropriate technology choices - 80% confidence
  Branch 2 (maybe): Over-engineering risk (Redis for simple cache) - 15% confidence
  Branch 3 (unlikely): Wrong technology (SQL for unstructured data) - 5% confidence

Selected: Branch 1 (sure)

Output Format: Concerning Health Branch
```

## What This Catches

- Unexplored architectural scenarios (edge cases in layer separation)
- Alternative design pattern interpretations
- Technology fit what-if scenarios (what if we used X instead of Y)
- Hidden over/under-engineering signals

## Opt-Out Flag

Disable ToT enhancement:
```bash
export Q_NO_TOT=true
```
