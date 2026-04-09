---
tags: [reasoning, strategy, architecture, planning, rca, got-tot, decision-quality]
created: 2025-04-09
sources:
  - P:/.claude/skills/__lib/strategic_reasoning.md
  - P:/.claude/skills/q/SKILL.md
summary: Canonical definitions for Graph-of-Thought (GoT), Tree-of-Thought (ToT), and strategic questioning frameworks used across strategy-heavy skills. Internal reasoning patterns that enhance decision quality in architecture, planning, RCA, and audit skills.
---

# Strategic Reasoning Patterns

Canonical definitions for Graph-of-Thought (GoT), Tree-of-Thought (ToT), and strategic questioning frameworks used across strategy-heavy skills.

These are **internal reasoning patterns**, not user-facing slash commands. They enhance decision quality in architecture, planning, RCA, and audit skills.

## Purpose

Strategic reasoning patterns improve decision quality by:
- Testing design space before committing (what problem are we solving?)
- Exploring alternatives through structured branching scenarios
- Challenging assumptions through adversarial reasoning
- Preventing implicit decisions from becoming execution artifacts

## When to Use

**Good use cases:**
- `/arch` - Architecture decision validation before ADR creation
- `/planning` - Plan quality assurance through branching scenario analysis
- `/rca` - Competing-cause hypothesis generation and testing
- `/skill-audit` - Blind-spot detection for audit completeness
- Strategy-heavy decisions where shallow reasoning would miss root causes

**Not for:**
- Rote transforms, formatting, or deterministic edits
- Simple syntax fixes or lint corrections
- Any task where the "right answer" is already known

---

## 1. Graph-of-Thought (GoT) - Constraint Analysis

### Purpose
Model decision constraints as nodes in a graph, trace dependency chains, and detect circular reasoning or hidden contradictions.

### When to Use
- Architecture decisions with multiple competing constraints
- Requirements with conflicting stakeholder priorities
- Trade-off analysis where options have subtle dependencies

### Internal Prompt Pattern

```
Graph-of-Thought constraint analysis:

What constraints are active?
What are their dependencies (A requires B, B conflicts with C)?
What constraint is the root blocker?
What hidden contradictions exist between stated constraints?
What happens if constraint X is relaxed or re-prioritized?

Build constraint graph:
Nodes = constraints, Edges = dependencies/conflicts
Detect: circular dependencies, orphaned constraints, unreachable goals
```

### Output Schema
```json
{
  "constraints": [{"id": "C1", "name": "...", "priority": "HIGH/MEDIUM/LOW"}],
  "dependencies": [{"from": "C1", "to": "C2", "type": "requires|blocks|conflicts"}],
  "contradictions": [{"c1": "C1", "c2": "C3", "description": "..."}],
  "root_blocker": "C1",
  "resolution_path": ["relax C3", "re-prioritize C1"]
}
```

### Source
- Origin: `/q` skill - Q3 requirement constraint analysis
- Reference: `P:/.claude/skills/q/references/got-tot-integration.md`

---

## 2. Tree-of-Thought (ToT) - Branching Scenario Analysis

### Purpose
Generate multiple solution branches, explore consequences, and synthesize across branches before committing.

### When to Use
- Strategic decisions with 2+ plausible paths
- "What if we did X instead?" scenarios
- Failure mode exploration (what breaks if this assumption is wrong?)

### Internal Prompt Pattern

```
Tree-of-Thought branching analysis:

Branch 1: [current proposal]
  - What works?
  - What breaks?
  - What assumptions must hold?

Branch 2: [alternative A]
  - Same questions

Branch 3: [alternative B]
  - Same questions

Synthesis:
  - Which branch survives stress testing?
  - What assumptions are shared across all branches?
  - What combination of branch ideas creates a better option?
```

### Output Schema
```json
{
  "branches": [
    {"id": "B1", "name": "current proposal", "pros": [], "cons": [], "assumptions": []},
    {"id": "B2", "name": "alternative A", "pros": [], "cons": [], "assumptions": []}
  ],
  "synthesis": "B1 + B2 hybrid: ...",
  "shared_assumptions": ["A1", "A2"],
  "recommended": "B1"
}
```

### Source
- Origin: `/q` skill - Q2/Q4 question branching
- Reference: `P:/.claude/skills/q/references/got-tot-integration.md`

---

## 3. Strategic Questioning Framework

### Purpose
Prevent implicit decisions through structured questioning before execution.

### Core Questions

**Problem Definition:**
- What problem are we actually trying to solve?
- What would a better outcome look like?
- If this skill did not exist, what would we build instead?

**Assumption Testing:**
- What assumptions are we making about scope, triggers, or enforcement?
- Where is the design fighting the workflow instead of fitting it?
- What would make this skill/feature unnecessary?

**Failure Analysis:**
- What failure would be most embarrassing six months from now?
- What breaks under multi-terminal concurrency, stale-data exposure, or stale state?
- What important failure mode is still being left to reviewer interpretation?

**Decision Quality:**
- What decisions are still implicit but materially affect downstream execution?
- What would a weaker or faster model most likely misunderstand here?
- What is the strongest objection or counterexample to my current recommendation?

### Role-Specific Question Sets

**For RCA-heavy skills:**
- What competing causes exist?
- What evidence would falsify this diagnosis?
- Are we treating symptoms or root causes?

**For Implementation-heavy skills (/code, /skill-ship):**
- What implementation risk is still unaddressed?
- What breaks under refactoring?
- Are we fixing the right thing?

**For Architecture/Planning skills (/arch, /planning):**
- What downstream execution semantics must be explicit?
- What boundaries are still named but not operationally closed?
- What would a planner need to know that the ADR leaves implicit?

**For Advisory/Extraction skills (/rns, /gto):**
- What action item is still a finding rather than a next step?
- What recommendation is too vague to select and execute?
- What part of this output would be hard to reverse if wrong?

### Source
- Origin: `/q` skill - Strategic questioning framework
- Origin: `/skill-audit` skill - Blind-spot prompts

---

## 4. Technology Fit Assessment

### Purpose
Validate whether chosen technology stack fits the problem domain.

### When to Use
- Architecture decisions involving framework/language selection
- "Should we use X for Y?" questions
- Migration or re-architecture decisions

### Assessment Dimensions

| Dimension | Questions |
|-----------|-----------|
| **Problem Match** | Does this technology solve the actual problem? What edge cases does it miss? |
| **Scalability** | Can this handle expected load? What breaks at 10x current scale? |
| **Maintainability** | Is the team familiar with this? What's the learning curve? |
| **Ecosystem** | Are libraries active? Is the project abandoned? |
| **Operational** | Can we run this in production? What monitoring/debugging tools exist? |

### Output Schema
```json
{
  "technology": "name",
  "problem_domain": "description",
  "fit_score": "HIGH/MEDIUM/LOW",
  "concerns": ["concern 1", "concern 2"],
  "alternatives": ["alt 1", "alt 2"],
  "recommendation": "USE / AVOID / CAUTION"
}
```

### Source
- Origin: `/q` skill - Technology Fit Assessment dimension

---

## Import Guidance for Skills

### When to Import These Patterns

**Import GoT+ToT if:**
- Skill is architecture-heavy, routing-heavy, or policy-heavy
- Skill involves transfer/reuse analysis with multiple plausible targets
- Skill is high-blast-radius, stateful, hook-heavy, or contract-sensitive

**Import Strategic Questioning if:**
- Skill needs internal self-check mechanism
- Skill is strategy-heavy (architecture, planning, RCA, audit)
- Skill needs to prevent implicit decisions from becoming execution artifacts

**Import Technology Fit if:**
- Skill validates technical choices
- Skill assesses whether tools fit problem domains

### How to Import

```markdown
## Strategic Reasoning

This skill uses strategic reasoning patterns from `P:/.claude/skills/__lib/strategic_reasoning.md`:

- **GoT+ToT**: [when used]
- **Strategic Questioning**: [when used]
- **Technology Fit**: [when used]

Internal blind-spot checks are run before final recommendations.
```

### Effort Configuration

Skills using strategic reasoning should configure `effort: high` or `effort: max` in frontmatter:
```yaml
---
effort: high
---
```

Shallow reasoning on strategic decisions produces poor outcomes.

---

## Opt-Out Flags

Users can disable strategic reasoning for faster execution:

```bash
/skill-name --no-got-tot     # Skip Graph-of-Thought and Tree-of-Thought
/skill-name --fast            # Shallow reasoning, skip strategic checks
```

Skills MUST respect these flags and degrade gracefully without breaking.

---

## Related Pages

- [[P:/.claude/skills/__lib/sdlc_internal_modes.md]]@refines - SDLC internal modes (trace, challenge, emerge, graduate)
- [[P:/.claude/skills/q/SKILL.md]]@supersedes - Original source of GoT+ToT and strategic questioning
- [[P:/.claude/skills/skill-audit/SKILL.md]]@uses - Blind-spot prompts framework

---

## Version History

- **v1.0** (2025-04-09) - Initial extraction from `/q` skill for cross-skill reuse
