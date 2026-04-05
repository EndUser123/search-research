# Review Bundle: /critique Skill

**Generated**: 2026-03-22
**Scope**: `P:\.claude\skills\critique\`
**File Count**: 4 files
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill name**: critique
- **Category**: analysis
- **Version**: 1.0.0
- **Trigger**: `/critique`
- **Enforcement**: advisory
- **Parallel agents**: true

### Domain & Purpose
Three-phase adversarial critique workflow for any work product (plan, design, document, policy, prompt, or skill). The skill executes three sequential phases via subagents: initial critical review (Phase 1), meta-critique of Phase 1 output (Phase 2), and synthesized refined critique (Phase 3). Phase 1 and Phase 2 run in parallel; Phase 3 runs after both complete.

### Scale Metrics
- 4 files, ~327 lines total
- 3 phase prompt files + 1 SKILL.md orchestrator
- No Python code — purely prompt-based skill

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /critique
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  SKILL.md — orchestrator                             │
│  1. Capture work input (context-aware resolution)    │
│  2. Spawn Phase 1 + Phase 2 in parallel           │
│  3. Spawn Phase 3 after both complete               │
│  4. Deliver Phase 3 output                          │
└─────────────────────────────────────────────────────┘
         │
         ▼
    Phase 1 Agent          Phase 2 Agent
    (parallel)              (parallel)
         │                       │
         ▼                       ▼
    p1_initial_review.md    p2_meta_critique.md
    - 7-section critique    - Critique quality issues
    - Understand-first      - Missed angles
    - Precision/recall      - Improvements
         │                       │
         └───────────┬───────────┘
                     ▼
              Phase 3 Agent
              (sequential)
                     │
                     ▼
             p3_synthesis.md
             - RNS format
             - Health score
             - Sorted severity
```

### Phase Definitions

| Phase | File | Purpose |
|-------|------|---------|
| 1 | `p1_initial_review.md` | Expert critical review of the work |
| 2 | `p2_meta_critique.md` | Critique of the Phase 1 critique quality |
| 3 | `p3_synthesis.md` | Synthesized refined critique with RNS format |

---

## 3. EXECUTION AND DATA FLOW

### Workflow Sequence

1. **Capture input**: Determine target work via context-aware resolution (args > recent session > ask)
2. **Parallel execution**: Spawn Phase 1 and Phase 2 agents simultaneously
3. **Sequential synthesis**: After both complete, spawn Phase 3 with Phase 1 + Phase 2 outputs
4. **Deliver**: Present Phase 3 synthesized critique as final output

### Context-Aware Resolution (Step 1)
Priority order:
1. Args specify target (e.g., `/critique on /critique`)
2. Recent session focus (last-edited skill/file)
3. Ask user if genuinely ambiguous

### Agent Execution
- All phases use `general-purpose` agent type
- Phase 1 and Phase 2 run as background agents in parallel
- Phase 3 runs after both complete (foreground)

---

## 4. COMPONENT INVENTORY

### SKILL.md (176 lines)
**Path**: `P:\.claude\skills\critique\SKILL.md`
**Responsibility**: Main orchestrator — defines workflow, agent architecture, phase table, and output structure
**Entry points**: `/critique`, `/critique on <target>`
**Key functions**:
- Context-aware target resolution
- Parallel subagent spawning for Phases 1+2
- Sequential Phase 3 spawning
- Output structure enforcement (7-section + RNS + Health Score)

### Phase 1 Prompt (60 lines)
**Path**: `P:\.claude\skills\critique\phases\p1_initial_review.md`
**Responsibility**: Generate initial critical review
**Sections**: Brief Intent Summary, Logical Gaps & Inconsistencies, Hidden Assumptions & Fragile Dependencies, Missing Obvious Actions / Best Practices, Risks and Edge Cases, Concrete Recommendations, Open Questions / Unknowns
**Key additions** (vs original):
- Process/methodology review when target is a process description
- Understand-first requirement (restate target before critiquing)
- Precision/Recall framing for critique quality

### Phase 2 Prompt (37 lines)
**Path**: `P:\.claude\skills\critique\phases\p2_meta_critique.md`
**Responsibility**: Critique the Phase 1 critique quality — not the original work
**Sections**: Critique Quality Issues, Missed Angles, Improvements to the Critique
**Scope**: Evaluates Phase 1 analysis quality, does not find new issues in original work

### Phase 3 Prompt (54 lines)
**Path**: `P:\.claude\skills\critique\phases\p3_synthesis.md`
**Responsibility**: Synthesize Phase 1 + Phase 2 into refined critique with RNS format
**Sections**: Intent Summary, Health Score, Logical Gaps & Inconsistencies, Hidden Assumptions & Fragile Dependencies, Missing Obvious Actions / Best Practices, Risks and Edge Cases, Concrete Recommendations, Open Questions / Unknowns, Recommended Next Steps
**Format**: GTO-style RNS with numbered items, severity tags, "0 - Do ALL Recommended Next Steps"

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
- **Adversarial depth**: Three phases ensure critique is challenged and refined, not just produced
- **Parallel + sequential**: Phase 1 and 2 in parallel saves time; Phase 3 sequential ensures synthesis uses both outputs
- **Context-aware**: LLM-native understanding of target, not brittle pattern matching
- **Understand-before-critique**: Phase 1 must restate target before evaluating
- **Precision/Recall framing**: Critique quality has two independent dimensions — correctness vs completeness

### Technology Constraints
- No Python code — pure prompt-based skill
- No external tools or APIs
- No state persistence between invocations
- Advisory enforcement (not blocking)

### Things That Must NOT Change
- Phase 1 and Phase 2 must remain parallel (performance requirement)
- Phase 2 must critique Phase 1 quality, not find new issues in original work (scope boundary)
- Output must use 7-section structure with severity tags and RNS format
- Context-aware resolution must use LLM-native understanding, not regex patterns

---

## 6. KNOWN ISSUES

### Historical Issue: Phase 2 Self-Contradiction (Fixed)
- **Scenario**: Original Phase 2 prompt said "critique the critique — not the original work" but item 1 asked for "important problems in the original work that Phase 1 failed to catch"
- **Impact**: Phase 2 was asked to do two contradictory things simultaneously
- **Fix**: Phase 2 scope clarified — critiques Phase 1 quality only; original work issues belong in Phase 3 synthesis

---

## 7. INTEGRATION POINTS

### Invocation
- `/critique` — critique last-worked-on item (context-detected)
- `/critique on <target>` — critique specific skill/path

### Related Skills
- `/adversarial-review` — suggest (parallel adversarial review)
- `/adversarial-critic` — suggest (meta-analysis)

### Output Consumers
- Phase 3 output is the final deliverable
- Formatted with proper markdown (not raw syntax)
- Includes Health Score, severity-tagged items, RNS with "0 - Do ALL"

---

## 8. APPENDIX: OUTPUT SCHEMA (Phase 3)

```
## Intent Summary
[2-3 sentences]

## Health Score: XX%
[Healthy ≥80%, Warning 50-79%, Critical <50%]

## Logical Gaps & Inconsistencies
1.1. [HIGH] issue (file:line)
1.2. [MEDIUM] issue

## Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] issue

## Missing Obvious Actions / Best Practices
3.1. [HIGH] issue

## Risks and Edge Cases
4.1. [MEDIUM] issue

## Concrete Recommendations
5.1. [MEDIUM] specific change

## Open Questions / Unknowns
6.1. [LOW] uncertainty

## Recommended Next Steps
[All items sorted by severity]

1.1. [HIGH] Fix thing in file:line
1.2. [MEDIUM] Address thing

0 - Do ALL Recommended Next Steps (N items)
```
