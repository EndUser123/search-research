---
title: "Skill management in agentic systems: research survey and what the field has formalized"
created: 2026-07-27
source: session-2026-07-27 (/www research on skill management in agentic systems)
sources:
  - external: https://arxiv.org/html/2605.10923v1 (SLIM — Dynamic Skill Lifecycle Management, Shen et al. 2026, CUHK + UF)
  - external: https://arxiv.org/html/2602.12430v3 (SoK: Agent Skills for LLMs — Architecture, Acquisition, Security)
  - external: https://arxiv.org/abs/2605.25430 (CODESKILL — Self-evolving skill bank as learnable management policy)
  - external: https://github.com/addyosmani/agent-skills/blob/main/skills/deprecation-and-migration/SKILL.md (industry deprecation pattern)
  - external: https://aiquinta.ai/blog/versioning-agent-skills-semver-compatibility-deprecation/ (SemVer for skills)
  - external: https://arxiv.org/html/2603.22455v2 (SkillRouter — Skill Routing for LLM Agents at Scale)
  - external: https://openreview.net/pdf?id=kym0qvjrvm (When Single-Agent with Skills Replace Multi-Agent Systems — hierarchical routing limits)
  - external: https://arxiv.org/html/2604.08224 (Externalization in LLM Agents: unified review of memory, skills, protocols, harness engineering)
  - internal: P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md (our lifecycle mapping)
  - internal: P:/.data/wiki/concepts/skill-lifecycle-toolkit.md (our 5 transferable techniques)
  - internal: P:/.data/wiki/concepts/wiki-integrated-skills-query-save-pattern.md (the closed-loop pattern)
tags: [skill-management, skill-lifecycle, agentic-systems, research-survey, marginal-contribution, retain-retire-expand, routing-at-scale, skill-bank, harness-engineering]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  The field has formalized skill management as a first-class problem. SLIM
  (Shen et al. 2026) defines dynamic skill lifecycle management with three
  operations — retain, retire, expand — driven by leave-one-skill-out marginal
  contribution estimation. CODESKILL reformulates skill-bank maintenance as a
  learnable management policy. SkillRouter addresses routing accuracy at scale.
  The unified review (Zhou et al. 2026) frames skills as one externalization
  mode alongside memory, protocols, and harness engineering. The key insight
  for our workspace: our "create/audit/improve/retire" lifecycle is the static
  instance of what the field treats as a DYNAMIC optimization variable — the
  active skill set should evolve based on measured marginal contribution, not
  be fixed at creation time. Our /skill-dev gap is real but narrower than we
  framed it: the missing piece is not "create" (covered) or "audit/retire"
  (covered by skill-prune) but "dynamic marginal-contribution evaluation" —
  the closed-loop measurement that tells us which skills to keep active.
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: extends — adds the dynamic-lifecycle research layer to our static mapping
  - target: wiki/concepts/skill-lifecycle-toolkit.md
    type: refines — our 5 techniques are the static instance; SLIM is the dynamic generalization
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern.md
    type: related — the query-save loop is one instance of marginal-contribution feedback
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: adjacent — both about adaptive system behavior under gating constraints
---

# Skill management in agentic systems: research survey

## Decision context

**Why this research was needed:** the operator asked "is there research or repos or info on skill management in agentic systems?" after a /tp session concluded our /skill-dev gap is the missing "improve-mode closed loop." The real question: *has the field formalized skill management as a discipline, and what does it say we should do?*

**What the research changed:** confirmed the field HAS formalized this (SLIM, CODESKILL, SkillRouter, Externalization review). The key reframing: skill management is not a static lifecycle (create → audit → improve → retire) but a **dynamic optimization** where the active skill set evolves based on measured marginal contribution. Our gap is narrower and sharper than "build /skill-dev" — the missing capability is marginal-contribution evaluation, not another lifecycle skill.

## The research landscape

### 1. SLIM — Dynamic Skill Lifecycle Management (Shen et al. 2026, CUHK + UF)

**arxiv 2605.10923** — the most directly relevant paper. Repo: https://github.com/ejhshen/SLIM

**Core contribution:** formalizes skill management as a dynamic optimization variable updated during agent training. Three lifecycle operations driven by **leave-one-skill-out marginal contribution estimation**:

| Operation | When | Signal |
|-----------|------|--------|
| **Retain** | Skill's smoothed marginal external contribution (MEC) ≥ τ_keep | Skill still provides external value the policy hasn't internalized |
| **Retire** | Skill's MEC < τ_retire AND sufficient exposure AND stable low-contribution streak | Skill may have been internalized, become redundant, or become noisy |
| **Expand** | Persistent failures in a routed task region where existing skills don't help AND current performance < τ_expand | Missing capability coverage detected |

**Key insight:** the optimal active skill set is **non-monotonic** — it should grow AND shrink based on measured value, not follow a fixed lifecycle. SLIM subsumes two prior paradigms as boundary cases:
- **SkillRL** (persistent accumulation) = SLIM with retirement disabled → degrades due to routing noise from too many skills
- **Skill0** (forced zero-skill inference) = SLIM with expansion disabled and retirement forced → violates finite-capacity constraint, drops long-tail capabilities

**Results:** +7.1 points average over best baselines on ALFWorld + SearchQA. Ablations show removing retirement drops 14 points; removing expansion drops 8.6 points; random audit drops 18.7 points. The contribution-aware decision is essential — not just the operation space.

**Why this matters for us:** our "create/audit/improve/retire" lifecycle is the **static instance** of SLIM's dynamic formulation. We treat skills as created once, audited occasionally, retired explicitly. SLIM says the active set should be continuously evaluated for marginal contribution. Our `/skill-prune` is the closest analog but it runs on-demand, not continuously.

### 2. CODESKILL — Self-evolving skill bank (Li et al. 2026)

**arxiv 2605.25430**

**Core contribution:** reformulates skill extraction and skill-bank maintenance as a **learnable management policy**. Instead of a human (or a /skill-dev skill) deciding which skills to add/remove, a management LLM learns the policy from task outcomes.

**Relevance to us:** this is the "autonomous self-enhancement" boundary we correctly avoid (per the /notice v1.2 self-improvement boundary and the self-improvement-loops research from earlier this session). CODESKILL represents Rung 5-6 of the optimization ladder — the system rewrites its own skill bank. We stay at Rung 2-3 (human/curated edits with external quality gates). But the management-policy framing is useful: it tells us what a /skill-dev improve mode would need to approximate without crossing into autonomy.

### 3. SkillRouter — Routing at scale (Zheng et al. 2026)

**arxiv 2603.22455**

**Core contribution:** addresses the routing-accuracy problem when the skill bank is large. As the active skill set grows, the description-based routing signal degrades — the model can't distinguish between N similar skills. SkillRouter uses a learned router model separate from the task model.

**Relevance to us:** our `/go` is a hand-built router (route-by-task-shape). At 39 user-scope skills, we're near the threshold where description-based routing starts to degrade (the wiki concept `agentic-sdlc-skill-lifecycle-architecture` flagged this: "too many skills blur agent attention"). SkillRouter suggests the fix is a learned router, but that's beyond our scope. The practical takeaway: **keep the active set compact** — which validates our DEPRECATED-description convention and /skill-prune.

### 4. Externalization in LLM Agents (Zhou et al. 2026)

**arxiv 2604.08224** — the unified review.

**Core contribution:** frames skills as one of four externalization modes:
1. **Memory** — episodic/semantic context injected at inference
2. **Skills** — procedural guidance injected as modular units
3. **Protocols** — interaction contracts (tool schemas, API specs)
4. **Harness engineering** — all infrastructure around the model (context management, verification, recovery)

**Relevance to us:** our workspace spans all four. Skills (SKILL.md files), memory (wiki, handoffs), protocols (MCP tool schemas, plugin manifests), harness (AGENTS.md, hooks, close scanner). The unified view says skill management can't be isolated from memory management and harness engineering — they're all externalization with different lifecycles. This is why `/skill-dev` as a standalone skill felt wrong in the /tp critique: skill management is one mode of a broader externalization management problem.

### 5. Industry deprecation patterns

**addyosmani/agent-skills** (80k stars) has an explicit `deprecation-and-migration` skill. **aiquinta.ai** proposes SemVer for skills with compatibility rules and deprecation policies. Our DEPRECATED-description convention matches industry practice.

### 6. When single-agent-with-skills replaces multi-agent (Li et al., OpenReview)

**Key finding:** hierarchical routing mitigates scaling limits for skill-based single agents. Single-agent-with-skills can replace multi-agent systems up to a scaling ceiling, beyond which multi-agent is needed again. The ceiling is determined by routing accuracy under skill-bank size.

## What this means for our workspace

### The reframing: static lifecycle → dynamic marginal contribution

Our current model:
```
CREATE (once) → AUDIT (occasionally) → IMPROVE (never) → RETIRE (explicitly)
```

The field's model (SLIM):
```
ACTIVE SET (dynamic) ↔ MEASURE MEC → retain/retire/expand continuously
```

The gap isn't "we lack an improve-mode skill." The gap is **we don't measure marginal contribution**. We create skills, use them, and retire them when they're obviously stale. We never measure whether an active skill is still providing value vs. has been internalized vs. is adding routing noise.

### What a marginal-contribution measurement would look like for us

We can't run RL training loops (SLIM's method). But we CAN approximate the measurement:

1. **Retrospective MEC**: when a skill fires, was its output used or ignored? (Telemetry from /aar, /tp critique log)
2. **Leave-one-skill-out for skills**: would the session have gone differently without the skill? (Counterfactual — hard to measure, but /aar can approximate)
3. **Routing accuracy**: when the skill fires, is it the right skill for the task? (Misrouting incidents, tracked in /tp critique log)
4. **Description drift**: does the skill's description still match what it does? (/skill-prune already detects this)

### The narrower /skill-dev shape

Based on this research + the /tp critique, /skill-dev should NOT be a 3-mode create/audit/improve skill. It should be:

| Mode | What it does | Existing coverage |
|------|-------------|-------------------|
| **measure** | Evaluate marginal contribution of active skills (the SLIM-inspired missing piece) | NONE — this is the real gap |
| **create** | Scaffold new skills | create-skill (existing) |
| **audit/retire** | Detect stale/duplicate/drifted | skill-prune (existing at .agents scope) |
| **improve** | Propose targeted improvements from measured MEC | /tp (partial), /aar (partial), /dream Pass 5 (new) |

The **measure** mode is the high-value addition. It closes the loop: measure → decide → act. Without measurement, "improve" is unsighted.

## How this changes the /skill-dev recommendation

**Before this research:** build /skill-dev improve as a skill that reads techniques-index and proposes validated improvements.

**After this research:** build /skill-dev **measure** as a skill that evaluates marginal contribution of active skills using retrospective evidence (aar, tp critique log, routing incidents). The "improve" mode consumes the measurement. This is the SLIM pattern adapted to our non-RL context: we can't do leave-one-skill-out training, but we CAN do leave-one-skill-out retrospective analysis ("would this session have gone differently without /notice?").

## Falsifier

This survey is wrong if:
- **SLIM's dynamic lifecycle doesn't apply to non-RL agent systems** (our context — we don't train, we route). The marginal-contribution signal may be too noisy without RL's reward structure to measure against. Test: try retrospective MEC on 5 skills; if the signal is indistinguishable from noise, the dynamic approach doesn't transfer.
- **Our skill count (39) is below the routing-degradation threshold.** SkillRouter's problem may not be our problem yet. Test: measure misrouting incidents from the /tp critique log; if near-zero, routing accuracy isn't the constraint.
- **The "measure" mode requires infrastructure we don't have.** Retrospective MEC needs per-skill session traces (which skill fired, was its output used). We may not log this. Test: check whether /aar or /tp critique log captures per-skill usage.

## Cold-start protocol

```powershell
# 1. Check current skill count and routing signal quality
Get-ChildItem C:/Users/brsth/.grok/skills -Directory | Measure-Object | Select-Object Count

# 2. Check /tp critique log for misrouting or ignored-skill patterns
python P:/.data/tp_critique_log.py auto --limit 20

# 3. Check /aar artifacts for skill-usage telemetry
Get-ChildItem P:/.artifacts -Recurse -Filter "*skill*" -ErrorAction SilentlyContinue | Select-Object -First 10

# 4. If skill count >30 AND misrouting signals exist → routing degradation is real
# 5. If per-skill usage isn't logged → "measure" mode needs instrumentation first
# 6. If both are clean → the gap is narrower than the research suggests
```

## Related concepts

- [[agentic-sdlc-skill-lifecycle-architecture]] — our lifecycle mapping; this concept adds the dynamic-research layer
- [[skill-lifecycle-toolkit]] — our 5 techniques; SLIM is the dynamic generalization of technique 2 (held-out validation)
- [[wiki-integrated-skills-query-save-pattern]] — the query-save loop is one instance of marginal-contribution feedback
- [[proactive-ai-volunteering-mechanisms]] — both about adaptive system behavior under gating constraints
- [[self-improving-agent-systems-techniques-and-workspace-gaps]] — the optimization ladder; CODESKILL and SLIM map to Rungs 4-6
