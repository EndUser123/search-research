---
title: "Novel skill improvement approaches beyond extraction and code orchestration"
created: 2026-08-06
source: session-20260806
tags: [skill-design, skill-improvement, telemetry, environment-contracts, cache-aware, decomposition, research]
summary: >
  Research into improvement approaches NOT already explored (progressive
  disclosure, code orchestration, MCPs, hooks, external optimizers). Found 5
  genuinely novel directions: (1) environment contracts/self-validating skills,
  (2) cache-aware skill design, (3) AgentLTL trace-verification telemetry,
  (4) skill-comply prompt-independence compliance curves, (5) admission-gated
  skill evolution. Plus critical disconfirming evidence: GraSP shows that
  splitting skills can HURT if the routing structure isn't deterministic.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
relations:
  - target: wiki/concepts/go-structural-transformation-code-orchestration-2026.md
    type: extends
  - target: wiki/concepts/skill-bloat-research-thresholds-and-techniques-2026.md
    type: extends
  - target: wiki/concepts/adaptive-orchestration-task-shape-classification.md
    type: related
---

# Novel skill improvement approaches

## Decision context

The operator asked: what ideas have I NOT mentioned? This research deliberately excludes progressive disclosure, code orchestration, MCPs, hooks, and external optimizer tools — all already explored this session.

## Related concepts

- [[go-structural-transformation-code-orchestration-2026]] — code orchestration approach (the predecessor to this research)
- [[skill-bloat-research-thresholds-and-techniques-2026]] — thresholds and text-extraction techniques
- [[adaptive-orchestration-task-shape-classification]] — prior wiki concept identifying /go as code-orchestration candidate
- [[behavioral-compliance-gap-agent-skips-instructed-steps-without-verifying]] — the exact failure telemetry would expose

## The meta-finding (reframes the whole space)

**SkillsBench (arXiv:2602.12670):** human-curated skills help (+16.2pp pass rate), but **self-generated skills HURT (-1.3pp)**. This validates the workspace's existing bias toward gated, evidence-based skill material and warns against naive automated skill generation.

## Five novel approaches

### 1. Environment contracts / self-validating skills (SkillGuard, arXiv:2605.10990)

**What:** Skills carry testable assumptions about their environment (paths exist, model slugs are valid, hooks are registered). SkillGuard extracts only *role-bearing* assumptions and validates them against live state. Zero false alarms on 599 hard negatives; 100% precision, up to 76% recall.

**Why it's novel:** This doesn't move text or code — it turns the skill's own prose into executable assertions that detect their own decay. It's a maintenance/validity layer.

**For /go:** A `contracts:` frontmatter block listing operational assumptions (pick_model.py exists, spawn_model_gate.py registered, model slugs valid) + a `validate_contracts.py` script run by `/skill-dev measure` or `/check`. Targets the documented chronic pain: 197 dangling paths, stale slugs, dead hook scopes.

### 2. AgentLTL trace-verification telemetry (arXiv:2607.02599)

**What:** Express procedural rules over agent execution traces using First-Order Linear Temporal Logic. A spec drives: (a) scoring completed traces for compliance (deterministic, no LLM judge), and (b) online gating — blocking non-compliant tool calls in real time via PreToolUse hooks.

**Why it's novel:** Deterministic, judge-free compliance measurement + online enforcement. Measures *runtime behavior*, not static text. Closes the `/skill-dev` "Tier 3 ceiling" (which explicitly states it would need live telemetry to reach Tier 1).

**For /go:** Author LTL specs for procedural invariants (e.g., "cannot dispatch subagents before discovery artifact exists"). A PostToolUse/Stop hook replays the session trace against the spec → per-rule compliance score. Rules that never fire across N sessions are dead instructions to cut.

### 3. Skill-comply: prompt-independence compliance curves

**What:** Auto-generate test scenarios at decreasing prompt-strictness levels. A robust instruction is followed even under a competing prompt; a weak one only fires when the user's prompt echoes it.

**Why it's novel:** Produces a compliance *curve* per instruction, not a binary. Distinguishes "dead instruction" (followed only when prompted) from "live instruction" (followed regardless). Low-compliance instructions are candidates for hook promotion.

**For /go:** Point skill-comply at SKILL.md → it auto-derives the step spec → generate scenarios → run /go → capture tool-call trace → compliance report identifies weak steps.

### 4. Cache-aware skill design

**What:** Structure skill content so the byte-stable core forms the prefix and dynamic material sits in the suffix, maximizing KV-cache reuse (~90% cost discount on cached reads).

**Why it's novel:** Controls byte-order and mutability of what's already in context — the inverse of extraction (ordering and determinism, not presence/absence). A skill can be fully progressively disclosed and still be cache-hostile if a timestamp lands early.

**For /go:** Audit for anything that mutates per-invocation before the static workflow core. **Caveat: [UNKNOWN] whether Grok Build exposes cache_control breakpoints to skill authors.** Verify before refactoring.

### 5. Admission-gated skill evolution (EvoSkills, arXiv:2604.01687)

**What:** Skills grow/improve from execution traces, but only admit a change when it improves measured pass-rate by a threshold. A co-evolving surrogate verifier synthesizes test cases so admission doesn't need ground-truth access.

**Why it's novel:** Grows and revises library content from successes, gated by outcome measurement. Distinct from the workspace's refuted learning ledger (that tried to learn routing weights from a bimodal signal; this learns new procedure content from traces).

**For /go:** Maintain a `_fragments/` directory of proven mini-procedures. Each carries `provenance:` and `admission: needs >=2 successful invocations`. New fragments are proposed by `/skill-dev` from `/why` traces but never auto-admitted — they require delta-outcome receipts.

## Critical disconfirming evidence

**GraSP (arXiv:2604.17870):** "More skills does not monotonically improve performance — focused sets of 2-3 skills outperform comprehensive documentation, and excessive skills actually hurt."

**Implication for /go splitting:** If /go is split into sub-skills, they must form a **deterministic dispatch tree** (thin router picks exactly one path), NOT a flat menu the model re-evaluates. Otherwise GraSP predicts net regression.

## What doesn't apply to Grok Build

| Approach | Why not |
|---|---|
| Parametric skills (context distillation into weights) | No weight access on Grok Build |
| Generative composition planner (3.9M param model) | Over-engineered for 5-sub-skill cardinality |
| SkillWeaver SAD (99% context reduction) | Retrieval machinery overkill for small skill set |

## What this means for our workspace

1. **Build environment contracts first** — the lowest-effort, highest-certainty improvement. A `contracts:` frontmatter block + `validate_contracts.py` catches the documented chronic issues (197 dangling paths, stale slugs) deterministically. Fits existing `/check` and `/skill-dev measure`.
2. **Build the telemetry layer next** — AgentLTL-style trace specs + replay hooks close the `/skill-dev` Tier-3 ceiling. This is the measurement infrastructure that tells us WHERE to invest in structural changes.
3. **Measure before splitting** — the GraSP finding means naive /go decomposition risks net regression. Run telemetry first, split only where measurement proves prose is failing.
4. **Verify cache exposure before optimizing for caching** — Grok Build's cache_control behavior is [UNKNOWN]. 10 minutes of verification before refactoring.

## Falsifier

If building environment contracts and telemetry infrastructure produces no measurable improvement in skill compliance or defect detection, the telemetry-first approach is not worth the maintenance cost. The AgentLTL evidence is from benchmark tasks, not from a real fleet's diverse skill set — transferability to Grok Build's multi-skill, multi-session, multi-terminal environment is [INFERENCE].

## Receipts

- SkillsBench (arXiv:2602.12670): +16.2pp curated, -1.3pp self-generated (cited by subagent from web_search)
- SkillGuard (arXiv:2605.10990): 0 false alarms / 599 negatives, 100% precision, 76% recall (cited by subagent)
- AgentLTL (arXiv:2607.02599): +38pp compliance from block-and-warn gating on 5/7 models (cited by subagent)
- GraSP (arXiv:2604.17870): "focused sets of 2-3 skills outperform comprehensive" (cited by subagent)
- EvoSkills (arXiv:2604.01687): 71.1% SkillsBench, outperformed human-curated skills (cited by subagent)
- skill-comply (github.com/sh20raj/30tools): runnable tool, prompt-independence measurement (read by subagent)
- [INFERENCE] Cache-aware design applies to Grok Build — cache_control exposure unverified
- file:///C:/Users/brsth/.grok/skills/skill-dev/SKILL.md:451 — "would require live A/B or per-skill telemetry to reach Tier 1"

## Sources

- SkillGuard (arXiv:2605.10990) — environment contracts for skills
- AgentLTL (arXiv:2607.02599) — trace verification with online gating
- skill-comply (github.com/sh20raj/30tools) — prompt-independence compliance curves
- GraSP (arXiv:2604.17870) — excessive skills hurt (disconfirming evidence)
- EvoSkills (arXiv:2604.01687) — admission-gated skill evolution
- SkillsBench (arXiv:2602.12670) — curated helps, self-generated hurts
- SkillWeaver (arXiv:2606.18051) — decomposition is the bottleneck
- Code-First Agents (code-first-agents.com) — three-level extraction framework
- usaif, "Keep Claude Skills Lean" (Medium, May 2026) — unit test rule

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[codebase-knowledge-graph-mapping]]
- [[claude-code-hooks]]

