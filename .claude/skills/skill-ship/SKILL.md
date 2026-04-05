---
name: skill-ship
description: Master coordinator for skill creation and improvement workflows. MUST BE USED when user asks to "create/build/write/develop a skill". Use PROACTIVELY for "improve/optimize/fix/enhance a skill". Consider for "audit/review/validate a skill". Coordinates discovery, creation, evaluation (3a: spec, 3b: quality, 3c: integration), optimization, and distribution. Integrates skill-creator evals, skill-development guidance, and quality gates via testing-skills, av, similarity, doc-to-skill, sharing-skills.
version: 1.10.0
status: stable
category: orchestration
triggers:
  - /skill-ship
  - "complete skill"
  - "skill completion"
aliases:
  - /skill-ship
  - /sc
suggest:
  - /skill-creator
  - /skill-development
  - /similarity
  - /doc-to-skill
  - /sharing-skills
depends_on_skills: []
enforcement: advisory
workflow_steps:
  - phase_0_context: Lightweight session scan (read recent turns for correction signals, check .claude/hooks/.evidence/gto-state-* for prior GTO outputs — no external /gto invocation)
  - phase_1_discovery: Understand user intent, auto-invoke /similarity for conflict detection with result envelope pattern, extract requirements
  - phase_1_5_knowledge_retrieval:
      description: "Intelligent NotebookLM scan (semantic notebook discovery via describe+match or inverted query routing; functional quality inference (robustness/computational efficiency/token efficiency/safety/observability/concurrency/recoverability/self-improvement); 5-query per notebook: enforcement, agents/sub-agents, triggers, output, gaps), CKS semantic search, existing skills/plugins pattern scan, and memory.md for relevant patterns/lessons before building"
      enforcement: required
      blocks_phase_2: true
      skip_when:
        - simple_skill: "Skill has <5 steps and straightforward execution — user can override by requesting full retrieval"
        - user_declined: "User explicitly declined knowledge retrieval"
        - no_existing_entries: "Domain has no existing CKS/memory/notebook entries (verified via /search)"
      violation_message: "Phase 1.5 skipped without logged reason — Phase 2 blocked until reason is documented"
  - phase_2_creation: "Create or update skill structure using skill-creator and skill-development guidance WITH constitutional filter (no enterprise patterns), plan-and-review for complex skills (>5 steps). REQUIRES: Phase 1.5 output present in workflow state or conversation — if Phase 1.5 was skipped, its skip reason must be documented before Phase 2 begins."
  - phase_3a_spec_compliance: Verify implementation follows plan with completion evidence (RED/GREEN/REGRESSION/VERIFY) - blocks 3b until SPEC_PASS
  - phase_3b_code_quality: Validate YAML frontmatter, trigger accuracy, quality gates, context bloat prevention - blocks 3c until critical issues resolved
  - phase_3c_integration_verification: Test skill invocation and execution paths - blocks Phase 4 until integration passes
  - phase_3_5_evaluation: Run eval suite with skill-creator including benchmarks and variance analysis (skip for simple skills)
  - phase_4_optimization: Add hooks for mechanical continuation, validation patterns (PostToolUse/state transition), enforce standardized formatting via output-style-extractor (internal: av2)
  - phase_5_distribution: Package skill for sharing via GitHub PR workflow using sharing-skills
---

# Skill Complete

Master coordinator for comprehensive skill creation and improvement workflows.

## Purpose

Coordinate the entire skill lifecycle from inception to deployment, ensuring proper creation methodology, consistent output formatting, quality validation, optimization, and distribution.

## When to Use

| Strength | When This Applies |
|----------|-------------------|
| **MUST BE USED** | "create a skill", "build a new skill", "write a skill from scratch" |
| **Use PROACTIVELY** | "fix my skill", "improve this skill", "optimize a skill", "skill isn't working" |
| **Consider using** | "how do I create skills", "what's wrong with this skill", "review my skill" |

**Decision:** "create/new/build" → MUST USE | "fix/broken/error" → PROACTIVE | "improve/review/audit" → Consider

## Orchestrated Skills

### Context Phase
- **gto**: Session gap analysis - detect user corrections, learning signals, broken windows

### Creation Phase
- **skill-creator**: (external plugin) Full iterative development loop with evals, benchmarks, description optimization
- **skill-development**: SKILL.md structure, progressive disclosure, plugin-specific best practices
- **doc-to-skill**: Convert documentation into skills

### Analysis Phase
- **similarity**: Find similar/redundant skills (auto-invoked in Phase 1)
- **av** (internal): Analyze and generate hook files
- **testing-skills** (internal): Quality gate validation

### Optimization Phase
- **av2** (internal): Mechanical continuation enforcement
- **output-style-extractor**: Extract display formatting patterns

### Distribution Phase
- **sharing-skills**: GitHub PR workflow automation
- **github-public-posting**: Pre-publish checklist

> `/av`, `/av2`, and `/testing-skills` are internal. Users should invoke `/skill-ship` directly.

## References

| Category | Files |
|----------|-------|
| **Core** | `references/workflow-phases.md` (detailed phase instructions), `references/skill-frontmatter-fields.md` (frontmatter reference), `references/config-file-conventions.md` (config template pattern) |
| **Workflow** | `references/agent-tool-usage.md`, `references/knowledge-retrieval.md`, `references/plan-and-review.md` |
| **Quality** | `references/phase3-validation-details.md`, `references/skill-quality-gates.md`, `references/context-bloat-prevention.md` |
| **Evaluation** | `references/eval-guide.md`, `references/eval-complete-reference.md`, `references/description-optimization-guide.md` |
| **Agent Patterns** | `references/subagent-result-envelope.md`, `references/anti-false-done-patterns.md`, `references/agentic-validation-hooks.md`, `references/constitutional-filter.md`, `references/agent-failure-modes.md`, `references/agent-command-templates.md` |
| **Output** | `references/output-format-templates.md` (7 templates), `references/format-compliance-guidance.md`, `references/recommended-next-steps-format.md` |
| **Hooks** | `references/skill-based-hooks.md`, `references/hooks-implementation-guide.md`, `references/hooks-design-patterns.md`, `references/procedure-type-skills-embedded-enforcement.md` |
| **Examples** | `examples/WORKFLOW-EXAMPLES.md` (3 complete workflows), `examples/eval-example.json` (eval suite template) |

**External Docs:** `P:/.claude/hooks/PROTOCOL.md` | `P:/.claude/hooks/ARCHITECTURE.md` | `P:/.claude/hooks/SKILL_AUTHORS_GUIDE.md`

## Workflow Phases Overview

**Detailed instructions:** `references/workflow-phases.md`

| Phase | Goal | Key Skills | Skip When |
|-------|------|------------|-----------|
| **0. Context** | Session awareness, detect patterns | session scan | Fresh sessions |
| **1. Discovery** | Understand user intent, auto-detect conflicts | similarity (auto) | Never |
| **1.5. Knowledge** | Retrieve existing patterns/lessons | notebooklm, cks, memory | Simple skills, user declines |
| **2. Creation** | Build skill structure with progressive disclosure | skill-creator, skill-development | Never |
| **3a. Spec** | Verify implementation follows plan | testing-skills (spec) | Never |
| **3b. Quality** | Validate YAML, triggers, quality gates | av, testing-skills (quality) | Simple skills (<100 lines) |
| **3c. Integration** | Test skill invocation and execution | testing-skills (integration) | Never |
| **3d. Artifact** | Validate artifact quality (conditional) | artifact rubric | Non-artifact skills |
| **3.5. Evaluation** | Empirical testing with evals/benchmarks | skill-creator (evals) | Simple skills, user declines |
| **4. Optimization** | Add hooks, enforce formatting | av2, output-style-extractor | Single-phase workflows |
| **5. Distribution** | Prepare for sharing/shipping | sharing-skills | Local skills only |

### Phase Summaries

**Phase 0:** Lightweight session scan — read recent turns for correction signals, check gto-state-* files and workflow-state.json for interrupted work. Skip for fresh sessions.

**Phase 1:** Extract user intent. Auto-invoke `/similarity` for conflict detection (>=80% → enhance vs create). **Critical**: Check for possessive repair phrases before assuming new creation ("my skill isn't working" = REPAIR, not CREATE). See `references/workflow-phases.md#phase-1` for intent extraction rules.

**Phase 1.5:** Query NotebookLM, CKS, and memory.md for relevant patterns. See `references/knowledge-retrieval.md` for query patterns. Skip for simple skills (<5 steps).

**Phase 2:** Create SKILL.md with proper frontmatter (including `enforcement` field). Apply progressive disclosure (<500 lines). See `references/workflow-phases.md#phase-2` and `references/skill-frontmatter-fields.md`.

**Phase 3 (Quality):** Three sub-phases run sequentially with fresh subagents (no state sharing between phases). Each spawns a fresh subagent with minimal context to prevent bias.

- **3a Spec:** Did implementation follow the plan? Output: `SPEC_PASS`/`SPEC_FAIL`. Blocks 3c. Never skip.
- **3b Quality:** YAML completeness, trigger accuracy, context bloat prevention. Blocks 3c until critical issues resolved. Skip for simple skills (<100 lines).
- **3c Integration:** Test skill invocation, execution paths, runtime behavior. Blocks Phase 4. Never skip.
- **3d Artifact (conditional):** Activate when skill emits durable artifacts (plans, reports). See `references/phase3-validation-details.md` for tables, processes, gate criteria.

See `references/phase3-validation-details.md` for complete validation tables, absence claim workflow, and Phase 3d artifact activation criteria.

**Phase 3.5:** Run eval suite with `evals/evals.json`. See `references/eval-guide.md`. Skip for simple skills.

**Phase 4:** Invoke internal av2 for StopHook, output-style-extractor for formatting. Pattern synthesis from `P:/memory/skill_optimization_patterns.md`. See `references/workflow-phases.md#phase-4`.

**Phase 5:** Fork, commit with conventional commits, open PR. See `references/workflow-phases.md#phase-5`.

---

## Iteration Escalation Ladder

When iterating on a skill (Phase 4 optimization or improvement cycles), classify the iteration depth:

| Level | Signal | Example |
|-------|--------|---------|
| **Band-Aid** | Patches a specific complaint | Fix a typo, adjust wording, add a missing flag |
| **Local Optimum** | Polishes within current design | Improve frontmatter, add references, restructure sections |
| **Reframe** | Questions the skill's purpose | "Should this be 3 smaller skills?" "Is the trigger wrong?" |
| **Redesign** | Changes fundamental structure | Split procedural into phase-based, merge overlapping skills |

**3-Band-Aid rule**: If 3+ iterations on the same skill are all Band-Aid level, flag: `"ITERATION DEBT: {skill} has {N} surface-level patches. Consider Reframe or Redesign iteration."`

## Multi-Criteria Quality Evaluation

During Phase 3b (Quality) and Phase 3.5 (Evaluation), score skills across weighted dimensions:

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Completeness | 0.25 | All workflow steps covered, no gaps in execution path |
| Clarity | 0.25 | Unambiguous instructions, examples for complex steps |
| Usability | 0.20 | Correct triggers, suggests bidirectional, progressive disclosure |
| Testability | 0.15 | Verification steps defined, acceptance criteria concrete |
| Robustness | 0.15 | Error handling guidance, edge cases documented |

**Score**: Each dimension 1-5. Weighted sum = quality score (max 5.0).

**Sensitivity check**: If changing any dimension score by ±1 would change the pass/fail outcome, flag as `FRAGILE QUALITY: {dimension} score is decisive — verify carefully.`

---

## Output Formatting

All skill outputs use templates from `references/output-format-templates.md`:

| Template | Use Case |
|----------|----------|
| 1: Strict Analysis | API responses, test results, RCA |
| 2: Executive Summary | Analysis reports, most skills default |
| 3: Hypothesis Testing | Debugging, investigation |
| 4: Comparison | Tool selection, architecture decisions |
| 5: Workflow Progress | Long-running tasks, phase tracking |
| 6: Error Analysis | Bug reports, debug findings |
| 7: Research Findings | Research tasks, doc analysis |

For skills producing gap-based findings (like `/gto`), use the **dynamic RNS format** — see `/gto SKILL.md` "Recommended Next Steps (RNS)" section.

### Enforcing Output Display in Skills

For skills with specific output format requirements (CLI output, config displays, etc.), use the **external template pattern**:

1. **Create** `references/output-template.md` with exact format specification
2. **Reference** it in SKILL.md: `See [references/output-template.md](references/output-template.md) for exact format`
3. **Keep** the template short (<50 lines) with concrete examples

**Why this works:** Inline format instructions are ignored ~50% of the time (GitHub #6450). External template files are read as content, not instructions, achieving much higher compliance.

See `references/format-compliance-guidance.md` for full options (Option A: template files, Option B: hook gates, Option C: both).

---

## Execution Directive

When `/skill-ship` is invoked:

1. **CONTEXT**: Phase 0 — lightweight session scan (no external `/gto`)
2. **DISCOVER**: Phase 1 — understand intent, auto-invoke `/similarity`
3. **CLASSIFY**: Determine skill type, complexity, output format
4. **COORDINATE**: Invoke appropriate specialized skills
5. **FORMAT**: Apply output format templates from `references/output-format-templates.md`
6. **VALIDATE 3a + 3b IN PARALLEL**: Two fresh subagents — 3a for spec compliance (blocks 3c), 3b for YAML/context-bloat (independent)
7. **VALIDATE 3c**: Fresh subagent tests invocation. Blocks Phase 4 until pass.
8. **EVALUATE**: Phase 3.5 evals (skip for simple skills)
9. **OPTIMIZE**: Phase 4 hooks/formatting if workflow warrants
10. **DISTRIBUTE**: Phase 5 sharing if upstreaming

**Quality Gate Protocol**: Each phase spawns FRESH subagents. Previous verdicts are NOT shared.

---

## Recommended Next Steps

When analysis is complete, present next steps in structured domain/action format. See `references/recommended-next-steps-format.md` for complete format specification, including machine-parseable format for downstream skill chaining.

---

## Agent Tool Usage

**CRITICAL**: `subagent_type` and `model` are different parameters. `model="haiku"` is correct; `(haiku model)` gets misinterpreted as `subagent_type="haiku"` causing errors.

See `references/agent-tool-usage.md` for complete parameter reference and examples.
