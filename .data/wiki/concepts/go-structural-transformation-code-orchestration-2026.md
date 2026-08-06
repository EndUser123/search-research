---
title: "/go structural transformation: code orchestration + tool landscape"
created: 2026-08-06
source: session-20260806
tags: [skill-design, code-orchestration, skill-bloat, /go, research, VMAO, progressive-disclosure]
summary: >
  The operator asked whether /go's bloat should be solved by structural
  transformation (moving deterministic logic to code) rather than text
  extraction. Research found two converging approaches: (1) the Code-First
  Agents three-level framework (Data/Classification/Procedure) identifies
  4 high-ROI extraction targets in /go that should become a Python helper;
  (2) 8 external repos provide novel optimization techniques (SkillReducer's
  DDMIN delta debugging, trigger auditing, attention placement scoring).
  The recommendation: build `__lib/go_router.py` for deterministic routing,
  shrinking SKILL.md to ~400-500 lines of pure judgment instructions.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
relations:
  - target: wiki/concepts/skill-bloat-research-thresholds-and-techniques-2026.md
    type: extends
  - target: wiki/concepts/adaptive-orchestration-task-shape-classification.md
    type: extends
  - target: wiki/concepts/risks-skill-improvement-research-2026.md
    type: related
---

# /go structural transformation: code orchestration + tool landscape

## Decision context

The operator pointed out that prior /www research and /skill-dev focused on text extraction (moving sections to reference files), which only saved 95 lines. The operator asked about a fundamentally different approach: moving deterministic logic OUT of SKILL.md prose INTO code scripts, as we've done with ship-py's `ship_orchestrator.py` and ship-rhai's Rhai workflows.

## The converging principle

All 5 code-orchestration sources frame the same split: **"Stabilize the routine (script it), strategize the uncertain (policy it)"** (HuggingFace, Sep 2025). The LLM is never removed — it is demoted from orchestrator to a node the script calls. Control flow moves to code; the LLM keeps judgment.

The usaif heuristic: **"If the logic could have a unit test, it belongs in Python."**

## The Code-First Agents three-level extraction framework

The cleanest framework for a single-skill orchestrator (from code-first-agents.com):

| Level | What | Where /go applies |
|---|---|---|
| **Data** | LLM interprets raw signals (judgment) | State-file reads, wiki discovery hits — KEEP as-is |
| **Classification** | Tool returns a label; skill branches on it | Profile inference, delegation scoring, readiness gate — EXTRACT |
| **Procedure** | Tool returns filled template; LLM follows verbatim | Spawn envelope, GO announcements, pack selection — EXTRACT |

## Extraction targets for /go (ranked by ROI)

| Rank | What to extract | Current form | Code pattern | Evidence |
|---|---|---|---|---|
| 1 | Delegation-packet scoring (6-signal regex → score) | reference/delegation-detection.md | Classification — regex counting → integer → routing | Validated on 1,074 transcripts |
| 2 | Profile inference (18-row table + 9 tie-breakers) | Step 1, ~36 lines | Classification — keyword match → label | Clear cases HIGH, full automation MEDIUM |
| 3 | Horsepower pack selection (profile + score → pack set) | Step 2, ~40 lines | Procedure — truth table → flag set | Pure deterministic once inputs fixed |
| 4 | Spawn envelope generation (template + model selection) | H4, ~40 lines | Procedure — prompt factory | Eliminates the "subagent lacked pointers" failure |
| 5 | State-file path derivation + staleness | Step 0.5/6.5, ~40 lines | Pure path/date logic | Already PowerShell embedded in prose |
| 6 | Readiness-gate skip conditions | Step 0.9, ~20 lines | Partial — skip conditions are deterministic | Dimensions stay LLM |
| 7 | GO announcement format blocks | Various | Procedure — derived from computed state | Lowest ROI, nearly free after 1-3 |

**Expected outcome:** `__lib/go_router.py` handles ranks 1-4 (~150 lines of Python); SKILL.md shrinks from 926 to ~500-600 lines. The remaining content is pure judgment: H1 Think lenses, alternatives gate content, mid-flight adaptation, discovery conflict resolution.

## What to KEEP as LLM instructions

- H1 Think Pack (5-lens reasoning) — pure judgment
- Alternatives gate content (architectural profile) — highest-value judgment
- Step 5 mid-flight adaptation — reactive policy decisions
- Discovery conflict/ownership resolution — reading + synthesis
- Debug/critic reasoning — highest-effort judgment

## External tools and repos

| Tool | What it does | Novel technique | Applicability |
|---|---|---|---|
| **SkillReducer** (arXiv 2603.29919) | DDMIN description compression + taxonomy-driven body classification | Systematically delete words that don't break routing; classify content actionable vs non-actionable | HIGH — 48% desc / 39% body compression with +2.8% quality |
| **hqhq1025/skill-optimizer** (⭐154) | Trigger auditing + token economics from session history | Detects under/over-trigger from real data | HIGH — closes wiki measurement gaps |
| **geuneda/claude-md-optimizer** (⭐3) | Attention placement scoring + session cost estimation | U-shaped attention model verifies critical content position | MEDIUM-HIGH — portable scoring engine |
| **agent-skill-creator** (⭐2159) | Eval infrastructure: canary-judge, holdout-case, per-model comparison | Known-bad canary must fail or judge is invalid | MEDIUM — eval rigor reference |

## What this means for our workspace

1. **Build `__lib/go_router.py`** — the VMAO pattern already proven by ship-py's `ship_orchestrator.py`. The router handles delegation scoring, profile inference, pack selection, and spawn envelope generation. The SKILL.md becomes a thin shell calling the router and following its output.

2. **The SKILL.md shrinks to judgment-only** — ~500-600 lines of: H1 Think lenses, alternatives gate, mid-flight adaptation, discovery, plan authoring, debug/critic. No more deterministic tables, scoring heuristics, or template-filling prose.

3. **Consider SkillReducer's DDMIN technique** for description compression — systematically delete words from the description field that don't break routing accuracy. The paper reports 48% description compression with improved quality.

4. **Port geuneda's session-cost estimation** into skill-dev — `per-request tokens × turns` compounding model makes the cost of a 926-line skill visible: ~14K tokens × 30 turns = 420K tokens per session.

## Falsifier

If building `go_router.py` and shrinking SKILL.md to ~500 lines produces no measurable improvement in task accuracy or consistency (via A/B eval), the code-orchestration approach is not worth the maintenance cost for a single-skill orchestrator. The ship-py precedent (which DID improve quality) suggests it will work, but ship-py is a pipeline (5 phases, state machine), while /go is an adaptive orchestrator with mid-flight judgment — a different shape.

## Related concepts

- [[skill-bloat-research-thresholds-and-techniques-2026]] — prior research on thresholds and text-extraction techniques (this concept extends it with code orchestration)
- [[adaptive-orchestration-task-shape-classification]] — prior wiki concept that identified /go as the canonical code-orchestration candidate
- [[risks-skill-improvement-research-2026]] — the progressive-disclosure research that preceded both bloat concepts

## Receipts

- usaif "Keep Claude Skills Lean" (Medium, May 2026): SKILL.md 2,800 → 600 words via Python extraction (read by subagent)
- Code-First Agents "Skill Orchestration" (code-first-agents.com): three-level Data/Classification/Procedure framework (read by subagent)
- SkillReducer (arXiv 2603.29919): 48% desc / 39% body compression, +2.8% quality, 55K-skill study (cited by subagent)
- [INFERENCE] /go at 926 lines has ~400-500 lines of extractable deterministic logic — not yet verified by building the helper
- file:///P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md — prior wiki concept reaching the same conclusion (micro-scale = the gap, /go = canonical candidate)

## Sources

- usaif, "Keep Claude Skills Lean: Move Deterministic Logic to Python" (Medium, May 2026)
- Code-First Agents, "Skill Orchestration for LLM Agents" (code-first-agents.com, 2026)
- HuggingFace, "Workflow vs Agent: a Policy-vs-Script Perspective" (Sep 2025)
- Qi et al., "LLM-as-Code" (arXiv 2606.15874, KDD 2026 AgenticSE Workshop)
- Microsoft, "Conductor: Deterministic orchestration" (GitHub, May 2026)
- SkillReducer (arXiv 2603.29919) — DDMIN + taxonomy-driven classification
- hqhq1025/skill-optimizer (GitHub ⭐154) — trigger auditing + token economics
- geuneda/claude-md-optimizer (GitHub ⭐3) — attention placement + session cost

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[context-management-in-claude-code]]
- [[claude-code-hooks]]

