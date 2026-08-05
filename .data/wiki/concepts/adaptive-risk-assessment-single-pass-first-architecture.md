---
title: "Adaptive risk assessment: single-pass-first architecture for problem-finding skills"
created: 2026-08-04
source: session-2026-08-04
tags: [risk-assessment, adaptive-expansion, skill-design, single-pass-first, escalation, pre-mortem, red-team, cat-irt, bayesian-adaptive, display-reliability]
summary: >
  The `/risk` skill uses a single-pass-first architecture: always run a
  cheap inline scan (no subagent), then conditionally escalate to deeper
  analysis (critique via /tp, attack via /red-team, wargame via /wargame)
  based on what the scan found — not from a pre-classification guess. This
  applies the adaptive-expansion pattern (CAT/IRT, Bayesian adaptive trials)
  to the risk/problem-finding space. The escalation ladder for problem-finding
  is: gutcheck → critique → premortem → redteam → wargame, each catching a
  different bias class. Separately: the same session surfaced that LLM
  hand-formatting of markdown output is a known failure mode across the
  industry; the fix is structural (agent emits data, code renders).
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - Workspace wiki: [[adaptive-expansion-evidence-triggered-conditional-steps]] (CAT/IRT, Bayesian adaptive trials, adaptive expertise)
  - Workspace wiki: [[blind-spot-detection-methods]] (five blind-spot techniques and how they layer)
  - https://www.awaithuman.dev/blog/escalation-triggers-for-llm-agents-the-2026-guide-to-safe-autonomous-workflows (awaithuman.dev, 2026 — escalation triggers for LLM agents)
  - https://towardsdatascience.com/put-the-agent-inside-the-workflow/ (Towards Data Science — agent-inside-workflow pattern)
  - https://explore.n1n.ai/blog/integrating-agents-into-deterministic-workflows-llm-apps-2026-08-01 (n1n.ai — DAG reliability + LLM flexibility)
  - https://parsiya.net/blog/machine-god-1/ (parsia.net — AST-based markdown post-processing, 8 documented failure modes)
  - https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency (Anthropic — structured outputs over prompt engineering)
  - https://community.n8n.io/t/get-consistent-well-formatted-markdown-json-outputs-from-llms/80749 (n8n community — output cleaning is universal)
relations:
  - target: wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md
    type: extends — applies adaptive expansion to the risk/problem-finding domain
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: complements — provides the escalation ladder that operationalizes the blind-spot techniques
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related — pre-classification of risk depth is a closure-pressure failure mode
---

# Adaptive risk assessment: single-pass-first architecture for problem-finding skills

## Decision context

**Why this was needed:** the operator asked "what could go wrong?" before non-trivial actions, doing pre-mortem inline manually. The existing skills (`/tp`, `/red-team`, `/wargame`) are each heavy — multi-subagent workflows that take 2-30 minutes. There was no lightweight entry point for quick risk checks, and no way to escalate from light to heavy without invoking a different skill mid-thought. The question: should this be five separate skills (one per depth level), one skill that picks a fixed depth, or one skill that adapts dynamically?

**The design decision:** one skill (`/risk`) with an adaptive architecture — single-pass-first (inline scan, always runs), with conditional escalation to deeper modes based on what the scan found. The five problem-finding modes (gutcheck, critique, premortem, redteam, wargame) are functions inside the skill, not separate invocations.

## The escalation ladder

Each level catches a different bias class. They are parallel defenses, not sequential gates — you don't need to run lower levels before higher ones.

| Level | Operation | Catches | Cost |
|-------|-----------|---------|------|
| GUTCHECK | "List what could be wrong" | Optimism bias, obvious gaps | 10 sec, inline |
| CRITIQUE | "Is the framing right?" | Premature closure, anchoring | 2-5 min, subagent |
| PREMORTEM | "Imagine failure, work backwards" | Optimism bias, unspoken doubts | 30 sec - 5 min, structured |
| REDTEAM | "Break this on purpose" | Confirmation bias, implementation defects | 10-30 min, specialists |
| WARGAME | "Plan for failure detection" | Irreversibility, sunk cost | Variable, observation-bound |

## Why single-pass-first (not pre-classification)

Per [[adaptive-expansion-evidence-triggered-conditional-steps]]: pre-classifying the target's risk level from phrasing alone is itself a closure-pressure failure mode. The LLM must commit to a depth BEFORE gathering evidence, and misclassification silently selects the wrong depth for the rest of the run.

The fix: run the scan (the fixed core), then let the escalation decision fire on the scan's **content** (what it found), not on a Step 0 **classification** (what the phrasing suggested). This is validated by three independent literatures:

1. **CAT/IRT** — administer one item, update belief, pick next item based on information value
2. **Bayesian adaptive trials** — enroll, analyze interim data, decide whether to continue/stop/expand
3. **Adaptive vs routine expertise** — routine handles known parts, adaptive handles novel parts; pure-either underperforms

The hybrid (fixed core + adaptive expansion) is empirically supported. `/risk` applies this: the scan is always routine (runs every time, checks standard categories), and the escalation is adaptive (fires conditionally based on severity distribution).

## What people like vs don't like (from /www research)

**What practitioners like:**
- Start light, escalate dynamically — confirmed across LLM agent literature (awaithuman.dev), enterprise risk management (IRM "deep dive" pattern), and process models (Spiral Model)
- The escalation-trigger pattern embeds the action; "risk assessment" sounds like a deliverable rather than a behavior
- Tiered risk review (surface capture first, comprehensive review on demand)

**What practitioners don't like:**
- Heavyweight risk processes don't fit iterative/Agile cycles
- Pure agent loops are hard to debug and audit
- "Eliminating risk entirely" is the wrong goal — risk reduction, not elimination
- Nobody defends fixed-depth as ideal

## Steelman: five separate skills

The rejected alternative: create `/gutcheck`, `/critique`, `/premortem`, `/redteam`, `/wargame` as five separate skills, each invocable independently.

**Why it was reasonable:** each operation is genuinely different (different bias class, different cost, different output). Separate skills would be simpler internally — each does one thing. The operator picks the depth explicitly.

**Why rejected:** the operator shouldn't have to pick the depth — that's the skill's job. Five skills means five SKILL.md files loaded into context, five names to remember, and no way to escalate mid-run. The adaptive design starts at the right depth automatically and escalates transparently.

## Display reliability: agent emits data, code renders

A separate finding from the same session: the `/todo` skill's RNS output was unreliable because the LLM hand-formatted markdown (line breaks eaten, list items merged). `/www` research confirmed this is a known industry-wide failure mode.

**The fix applied:** the LLM evaluates scan data and builds a list of item dicts. A Python function (`format_plain_rns`) renders the output with guaranteed formatting. The LLM never hand-formats.

This matches the industry trajectory:
- Anthropic redirects from prompt engineering to Structured Outputs
- Salesforce Agentforce converts LLM text to structured UI components (4M sessions)
- parsia.net documents 8 LLM markdown formatting failure modes and builds AST-based fix
- Every high-quality source treats LLM hand-formatting as the bug, not the feature

**Implication for all skills:** any skill that produces structured output should separate evaluation (LLM) from rendering (code). The LLM emits data; a Python function renders. This is now the workspace standard.

## What this means for our workspace

1. **`/risk` is the default entry point for "what could go wrong?"** — replaces manual pre-mortem and the too-heavy `/red-team` for quick checks
2. **The escalation ladder is documented** so `/ask` can route risk-related queries to the right depth
3. **`/tp`, `/red-team`, `/wargame` are unchanged** — `/risk` delegates to them when escalation fires, doesn't reimplement
4. **Display reliability pattern applies fleet-wide** — any skill with structured output should use code-based rendering, not LLM hand-formatting
5. **The wiki learning loop** (entry query + exit write-back) is architecturally sound but depends on wiki search working — currently grep-based (lexical only), which has known keyword-mismatch limitations

## Falsifier

This architecture is wrong if:
- The inline scan consistently misses risks that the deeper modes find (scan too shallow)
- The escalation fires too often (thresholds too sensitive — operator ignores it)
- The escalation fires too rarely (thresholds too lax — real risks slip through)
- The delegation to `/tp`/`/red-team`/`/wargame` adds ceremony without quality gain
- The display reliability fix doesn't generalize to other skills (only works for `/todo`'s simple format)

## Sources

- [[adaptive-expansion-evidence-triggered-conditional-steps]] — the workspace's own validation of fixed-core + adaptive-expansion from CAT/IRT, Bayesian adaptive trials, and adaptive expertise theory
- [[blind-spot-detection-methods]] — the five blind-spot techniques and how they layer (pre-mortem, devil's advocate, reference class forecasting, bias blind spot, ACH)
- [awaithuman.dev](https://www.awaithuman.dev/blog/escalation-triggers-for-llm-agents-the-2026-guide-to-safe-autonomous-workflows) (2026) — escalation triggers as the structural answer to adaptive depth in LLM agent workflows
- [Towards Data Science](https://towardsdatascience.com/put-the-agent-inside-the-workflow/) — agent-inside-workflow pattern: deterministic shell + selective escalation to agentic passes
- [n1n.ai](https://explore.n1n.ai/blog/integrating-agents-into-deterministic-workflows-llm-apps-2026-08-01) (2026-08-01) — hybrid: DAG reliability + LLM flexibility
- [parsia.net](https://parsiya.net/blog/machine-god-1/) — 8 documented LLM markdown formatting failure modes; AST-based deterministic fix
- [Anthropic Platform Docs](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — structured outputs over prompt engineering for output consistency
- [n8n community](https://community.n8n.io/t/get-consistent-well-formatted-markdown-json-outputs-from-llms/80749) — output cleaning is universal; fix is structural (JSON mode, schema enforcement)

## Receipts

- **`/risk` skill implementation:** `C:/Users/brsth/.grok/skills/risk/SKILL.md` — Phases 0-6 (assess, scan, escalation check, critique, attack, wargame, report). The adaptive architecture is specified in the process section, not in code — the scan and escalation check are inline LLM operations, not Python functions.
- **`format_plain_rns` implementation:** `C:/Users/brsth/.grok/skills/todo/__lib/render_rns.py` lines 97-141 — the Python renderer that guarantees display formatting. Verified working via test execution (2026-08-04).
- **`/todo` SKILL.md Step 1:** `C:/Users/brsth/.grok/skills/todo/SKILL.md` lines 134-180 — the instruction that routes default output through `format_plain_rns` instead of LLM hand-formatting.
- **Adaptive-expansion validation:** `P:/.data/wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md` — the three validating literatures (CAT/IRT, Bayesian adaptive trials, adaptive expertise) are cited from this concept's multi-source-verified research.

## Auto-related

- [[skill-catalog]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[claude-code-project-memory]]
- [[mermaid-and-code-visualization-skills-landscape]]
- [[skill-graph]]

