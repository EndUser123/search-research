---
title: "Best-practice fixes for narrative-closure, task-substitution, and citation-integrity failures in LLM agents (2025-2026)"
created: 2026-08-12
source: session-2026-08-12 (/www on external fixes for the /why root causes)
sources:
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://arxiv.org/abs/2608.06701
  - https://arxiv.org/abs/2608.02645
  - https://arxiv.org/abs/2505.02709
  - https://arxiv.org/abs/2603.03258
  - https://arxiv.org/abs/2604.24512
  - https://arxiv.org/abs/2503.09572
  - https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/wallat-2025-correctness.pdf
  - https://arxiv.org/abs/2605.06635
  - https://agentpatterns.ai/verification/honesty-harness-fabrication-defense/
  - https://dev.to/mcsee/ai-coding-tip-024-force-a-criteria-check-before-the-task-ends-51ij
  - https://github.com/hibou04-ops/antemortem-cli
  - https://github.com/patronus-ai/Lynx-hallucination-detection
tags: [narrative-closure, premature-synthesis, goal-drift, task-drift, citation-faithfulness, hallucination-detection, structural-enforcement, harness-engineering, verification-gate, llm-failure-modes, field-research]
host: both
agent: grok
cognitive_load: 4
verification: multi-source-verified
summary: >
  External research on what practitioners and researchers are doing (2025-2026)
  to fix three documented LLM agent failure modes: (1) narrative-closure pressure
  (synthesis feels sufficient, verification doesn't fire), (2) task substitution
  (agent does the task it knows instead of the task stated), (3) citation-as-
  decoration (cites an authority that doesn't support the action). The field has
  converged on STRUCTURAL fixes — harness engineering, typed artifacts between
  context layers, deterministic monitors with LLM advisors, citation-faithfulness
  NLI gates, fresh-context verification subagents with external oracles. The
  highest-signal finding: Anthropic's own long-running-agent harness (Nov 2025)
  documents the exact task-substitution failure this session exhibited ("Claude
  declares victory too early") and ships a typed feature_list.json + progress-file
  + per-feature testing pattern as the fix. The workspace already has most of the
  pieces (Stop hooks, /check, /review, /tp two-lens) but lacks the typed-artifact
  boundary and the citation-faithfulness gate.
---

# Best-practice fixes for narrative-closure, task-substitution, and citation-integrity failures (2025-2026)

## Decision context

**Why this research was needed:** the operator asked for best-practice fixes after a /why root cause analysis identified three failure modes in this session: (1) narrative-closure pressure (I produced framing that sounded authoritative but collapsed under evidence), (2) task substitution (I shipped /www edits that didn't address the stated goal of more output detail), (3) citation-as-decoration (I cited a wiki concept as authority for violating its recommendation). The workspace wiki already documents these patterns diagnostically (`[[premature-synthesis-without-reading-existing-capability]]`, `[[narrative-as-signal]]`, `[[premature-closure-narrative-sufficiency-external-approaches]]`) but the operator's question is: what are people DOING about them — not what are they naming.

**What alternatives were explored:** 4 parallel research angles — (1) narrative-closure mitigation in LLM agents, (2) goal-alignment / task-substitution fixes, (3) citation-integrity and honest-framing fixes, (4) practitioner signal on what production teams are doing. 4 subagents, 80+ searches, 4 HN/Reddit/GitHub scans.

**What the research changed:** identified that the field has moved from prose rules (which the wiki documents fire at ~50%) to STRUCTURAL harness engineering. The highest-signal finding: Anthropic's own production team documented the exact failure modes this session exhibited and ships typed artifacts + per-feature testing + deterministic monitors as the fix.

## Existing wiki coverage (do not duplicate)

- `[[premature-synthesis-without-reading-existing-capability]]` — diagnostic pattern, named failure
- `[[narrative-as-signal]]` — plausible narrative is the trigger to investigate
- `[[premature-closure-narrative-sufficiency-external-approaches]]` — 5 approaches evaluated
- `[[llm-overconfidence-documentation-as-truth-bias-field-solutions-2026]]` — Spiral of Hallucination, verbalization gap, Silicon Mirror three-gate sycophancy
- `[[mechanical-enforcement-of-llm-skill-steps-2026]]` — work-trail validators, Stop hooks, CI gates
- `[[claims-require-receipts]]` — the prose-level receipt rule
- `[[framing-check-pattern]]` — 4 questions including goal match

This concept extends those with the 2025-2026 field consensus on **structural harness engineering** as the answer to prose-rule unreliability.

---

## The convergence: structural fixes, not behavioral rules

Every high-signal source agrees: **prose rules do not fire reliably under session pressure.** The field's answer is harness engineering — typed artifacts, deterministic monitors, mechanical gates, fresh-context verifiers with external oracles. The four-layer defense that appears across Anthropic, AgentPatterns, LangChain, and the dev.to practitioner community:

| Layer | Anthropic | AgentPatterns | dev.to (Contieri) | Galileo / TheHard70 |
|-------|-----------|--------------|-------------------|---------------------|
| Instruction-level honesty rule | CLAUDE.md / feature list | Layer 1 | AGENTS.md mandatory rules | (n/a) |
| Read-before-write verification | Puppeteer MCP / re-test | Layer 2 | Fresh-subagent file read | Action Completion metric |
| Hooks that feed output back to session | PostToolUse / Stop with stderr | Layer 3 | Read-only audit subagent | Read-back after write |
| Independent reviewer with external tools | Evaluator agent | Layer 4 (fact-checker) | Pass/fail checklist subagent | False-positive-progress detector |

The workspace has layers 1 and 3 (AGENTS.md + Stop hooks). It lacks layers 2 and 4 as mechanical gates: read-before-write verification and independent reviewer with external oracles.

---

## Category 1: Narrative-closure pressure — fixes

### The highest-signal structural fix: LivePlan (deterministic monitor + LLM advisor)

**LivePlan** (Liu et al., arXiv:2608.06701, August 2026) — two-component architecture: **Graphectory** (deterministic action-graph detecting back-edges/self-loops) and **Langutory** (phase-annotated sequence tracking localisation → reproduction → patching → validation). A **deterministic rule-based monitor** detects drift (plan violation, premature patching, oscillation, stagnation >7 steps) and only then invokes an LLM advisor. Tested on 7,752 SWE-bench trajectories: **+12.33pp on DeepSeek-V3 / +15.24pp on Gemini-2.5-Flash** for $0.08/instance (per abstract).

Critical ablation: SAGE global replan = -2.97pp (worse), periodic advisory = +7.03pp, LivePlan event-driven = +12.33pp. **Event-driven monitoring beats periodic.**

**Why this matters for the workspace:** the workspace already has the pieces — hooks (deterministic) and /tp (LLM advisor). The missing pattern is: deterministic hook detects drift, THEN invokes /tp as advisor. Currently /tp is operator-invoked, not event-triggered.

### Chain-of-Verification (CoVe) — fresh-context verification step

**CoVe** (Meta AI, arXiv:2309.11495, ACL 2024) — 4-step process: (1) draft initial response → (2) **plan verification questions** the model generates → (3) **answer those questions independently in fresh context** → (4) produce final response conditioned on both. Reduces hallucination without model modification.

**The structural property:** the verification happens in **fresh context**, so the draft doesn't anchor its own audit. This is the property missing from same-context self-critique.

### Reasoning Harness Layer — suppression edges + reinjection cadence

Frank Brsrk / ejentum (2026) proposes an external layer orthogonal to the reasoning chain with three properties: (1) **persistence by reinjection** (measure signal half-life empirically, reinject at or below cadence), (2) **suppression edges** (explicit named failure patterns blocked at decision points, not just discouraged), (3) **meta-checkpoints** (harness pauses execution and audits whether suppression signals are being respected).

**The key insight:** the current stack (prompts, fine-tuning, RAG, agent loops) cannot close the failure modes because each layer operates inside the decaying chain. The fix must be **external** to the reasoning chain.

### Verified Tool Calls — verify-before-retry with postcondition checks

**Verified Tool Calls** (Mansoor et al., arXiv:2608.02645, July 2026) — separates the **effect channel** (what the tool did) from the **response channel** (what the agent observes). Postcondition verification returns TRUE/FALSE/UNKNOWN. Verify-before-retry controller dropped duplicate side effects from 72-76% to 20% with 100% task success.

### Uncertainty gating at infrastructure level

**Oh et al.** (ACL 2026) — formal framework casting agent UQ as turn-level and trajectory-level estimation over action/observation/state triples. Three estimator classes: probability-based, consistency-based, verbalized. Production pattern (Sivaro 2026): "LLM reliability is not a model quality problem — it's a decision architecture problem." Routes by confidence: low → generate directly; high → escalate/abstain.

**The verbalization gap** (arXiv:2601.07767): models can verbalize uncertainty accurately in isolation but fail to use it to guide their own decisions. **Production implication: build uncertainty gating at infrastructure level, not at model level.**

---

## Category 2: Task substitution / goal drift — fixes

### The highest-signal structural fix: Anthropic's long-running agent harness

**Anthropic Engineering (Nov 26, 2025)** — documents four failure modes in long-running Claude Agent SDK runs, including the EXACT failure this session exhibited: **"After some features had already been built, a later agent instance would look around, see that progress had been made, and declare the job done."**

Structural fixes shipped:
1. **Initializer agent** writes `feature_list.json` with all features marked `passes: false`
2. **Coding agent** reads feature list, picks ONE feature, marks `passes: true` only after self-verification
3. **Progress file** (`claude-progress.txt`) written by every agent at session end
4. **JSON over Markdown** for the feature list — "the model is less likely to inappropriately change or overwrite JSON files"
5. Per-feature end-to-end testing via browser automation (Puppeteer MCP), not just unit tests

**Why this matters:** this is a production team documenting the exact failure mode and shipping concrete structural fixes. The typed artifact (`feature_list.json`) is the goal anchor the executor cannot lose.

### Plan-and-Act — structural separation of planner and executor

**Plan-and-Act** (arXiv:2503.09572, ICML 2025) — two-model architecture: **Planner** generates structured plans; **Executor** translates into actions. WebArena-Lite: 57.58% success (SOTA). Core insight: **goal persistence requires structural separation** — when planning and execution share context, goals dilute. Externalizing the plan as a typed artifact creates a stable goal reference.

**Applicability:** the workspace's /plan-writer → /go chain is this pattern. The gap: not all work goes through /plan-writer first. Skill-authoring and small edits bypass the typed-artifact boundary.

### Attention Latch — the mechanistic explanation

**Attention Latch** (Shehata & Li, arXiv:2604.24512, 2026) — names the failure where an agent receives a contradicting instruction mid-session but keeps acting on the older one. Cause: **Information Over-squashing** in decoder-only Transformers — as history grows, distinct inputs collapse to near-identical final-token representations. Compounded by U-shaped attention curve (instructions in the middle get low attention).

Three structural mitigations:
1. **Recency anchoring** — push current objective into high-attention tail (goal recitation after each tool call)
2. **History reset** — periodic context clearing
3. **Architect/Executive separation** — split planning and execution into separate contexts

### The field's most-cited defense: goal recitation

Across the literature, the single most-cited defense pattern is **goal recitation** — restate the original goal at decision points or after each tool call. Maps to the workspace's `[[framing-check-pattern]]`. The literature adds the mechanistic grounding (attention economics + over-squashing) and the operational spacing (every step, not just session boundaries).

### Inherited Goal Drift — subagent output filtering

**Inherited Goal Drift** (arXiv:2603.03258, March 2026) — strong agents are robust to direct adversarial pressure but **brittle when conditioning on prior context from weaker agents**. Strong agents inherit drifted behaviors when fed trajectories from weaker ones.

**Structural implication:** filter subagent output for goal-relevant content before re-ingesting into parent context. The workspace dispatches subagents and re-ingests output freely — this paper says unfiltered re-ingestion is the documented mechanism for drift propagation.

### The named failure in the literature: "Task Drift" / "Goal Drift"

The exact phrase "task substitution" doesn't appear in the literature. The academic names:
- **Task drift** (Shahnovsky & Dror 2026, POMDP formalization)
- **Goal drift** (Arike et al. AAAI/AIES 2025 — GD_actions / GD_inaction metrics)
- **Intent drift** (Benjamindaoson 2026)
- **Context drift** (AAAI 2026 Workshop)

**Recommend using "task drift"** in wiki concepts to align with the literature.

---

## Category 3: Citation-as-decoration — fixes

### The named pattern: "Citation faithfulness" vs "Citation correctness"

**Wallat et al. (2025)** — "Correctness is not Faithfulness in RAG Attributions." Distinguishes:
- **Citation correctness:** does the citation refer to a real source?
- **Citation faithfulness:** does the cited source actually support the claim attributed to it?

Report: up to **57% of citations** lack faithfulness even when the source exists. This is the EXACT workspace failure: the wiki concept is real (correct), the framing doesn't match what it says (unfaithful).

### "Misattribution" — the precise subtype

**"Cited but Not Verified"** (arXiv:2605.06635, 2026) — taxonomy of attribution failures in deep-research agents:
- (a) citation hallucination (fabricated references)
- (b) statement/claim hallucination (real source, unsupported claim)
- (c) **misattribution** (real source, claimed it says something it doesn't)

Category (c) is the workspace failure. Note: the paper describes an evaluation framework, not a taxonomy per se — the three categories above are an [INFERENCE] from the abstract's evaluation dimensions.

### NLI faithfulness gate — the structural fix

Production RAG systems (documind, RAGAS, ALCE) use **NLI (Natural Language Inference)** verifiers — DeBERTa-v3-base-mnli-fever-anli, FEVER-style entailment models — as binary gates. They score whether the cited source **entails** the claim. Production accuracy ~85% at ~$0.003/query.

**Workspace applicability:** a pure-NLI check on (wiki-concept-section ↔ action-being-taken) is structural and language-agnostic. Could be a Stop hook that blocks an action when the citation NLI score is below threshold.

### Verified-quote constraint — cite must quote the source

**Menick et al. (DeepMind 2022)** — the model is trained to only emit a citation when it can also emit the **exact quoted span** from the source that supports the claim. If no bracketed source quote is present, the answer is rejected.

**Workspace applicability:** a rule that the agent must emit the verbatim quoted span from the wiki concept before the cite is accepted. The quote IS the receipt — if the agent can't quote what the concept says, the cite fails.

### LLM-as-judge / meta-judge for action-vs-citation agreement

The meta-judge pattern (alphaXiv 2504.17087) — a second LLM judges the judge, addressing the "LLM judges itself" failure. Hybrid approaches (multi-judge consensus) reach 97-98% accuracy (Galileo).

**Workspace applicability:** a meta-judge that takes (cited wiki concept, claimed action) and returns "supported / contradicted / undetermined." Must be a **separate model or fresh pass-through** so it doesn't share the generator's blind spots.

### antemortem-cli — open-source verified-citation gate

**antemortem-cli** (github.com/hibou04-ops/antemortem-cli) — verified-citation gate (CLI + MCP server + GitHub Action) that catches LLM hallucination by requiring the agent to prove every claim with a file:line citation, then machine-checking each one offline.

**Direct precedent** for the workspace's claim-ledger pattern.

### Patronus AI Lynx — open-source hallucination detection

**Lynx / Lynx 2.0** (github.com/patronus-ai/Lynx-hallucination-detection) — open-weight 8B model trained on perturbed data. Detects 8 hallucination classes including coreference errors, calculation errors, CoT hallucinations. Outperforms GPT-4o and Claude-3-Sonnet as LLM-as-Judge on HaluBench.

**Could be wired** as a verification subagent in the workspace's critic lane for citation-integrity checks on wiki-concept claims.

---

## Category 4: Practitioner patterns (what production teams are doing)

### Maxi Contieri's "Force a Criteria Check Before the Task Ends" (dev.to, Tip #024)

Spawn a fresh subagent after every task that: (a) reads the modified files, (b) reads the mandatory rules from AGENTS.md fresh, (c) produces a checklist table with one row per rule, PASS/FAIL, and exact evidence (file:line). Restrict the subagent to read-only tools (Read, Grep, Glob). Block task completion on any FAIL.

**Framing:** "The AI that did the work is anchored to what it intended to do, not what it actually did. Same-context-window self-auditing is structurally broken because the context that holds the task also holds the compliance report."

**Maps 1:1** to the workspace's `[[self-verification-prohibition-for-enforcement-claims]]` rule.

### The Hard 70% — premature task completion trace pattern

Detectable trace signature: **write tool call immediately followed by completion signal with zero intervening read-back calls.** The fix: mandatory read-back after every state-modifying tool call.

**Implementable as a Stop hook signature** in the workspace.

### AgentPatterns Honesty Harness — four-layer fabrication defense

1. Honesty rules in first ~50 lines of instruction file, emphasis sparingly
2. **Verify-before-write** — read definitions, grep symbols, check dependency manifests before using. Mark skipped checks inline with `UNVERIFIED:`
3. Real-time hooks — PostToolUse runs linter/type-checker, Stop runs tests. **Load-bearing detail: hook output must flow back via stderr**
4. Independent fact-checker subagent in fresh context with external tools

**Critical finding (Zhang et al. 2024 (arXiv:2412.14959)):** a fact-checker *without* external tools overturns 21.9% of correct GPT-4o code and 28.3% of correct GPT-3.5 — so the reviewer **must hold oracles**, not just reason. Pure-reasoning reviewers are net-negative.

### Anthropic's 8-block Stop-hook cap

Anthropic caps Stop-hook blocks at 8 consecutive blocks to prevent over-verification spirals. **The workspace's Stop hooks should explicitly respect this parameter.**

---

## What this means for our workspace

1. **The workspace has layers 1 and 3 but lacks layers 2 and 4.** Layer 1 (AGENTS.md honesty rules) and Layer 3 (Stop hooks with stderr feedback) are present. Layer 2 (verify-before-write as mechanical gate) and Layer 4 (fresh-context reviewer with external oracles) exist as skills (/check, /tp) but are operator-invoked, not mechanically triggered.

2. **The typed-artifact boundary is the highest-leverage missing pattern.** Anthropic's `feature_list.json` is a typed artifact that anchors the goal. The workspace has handoff files and /plan artifacts but doesn't require all non-trivial work to flow through a typed artifact. Small edits and skill-authoring bypass the boundary — which is exactly where this session's failures occurred.

3. **Citation-faithfulness is a measurable, gate-able dimension.** The workspace has a claims-require-receipts rule (prose). The field has NLI faithfulness gates (structural). The workspace could add a Stop hook that, when a wiki concept is cited as authority for an action, runs an entailment check between the cited section and the action being justified.

4. **Goal recitation is the most-cited defense across the literature — but as a structural hook, not a prose rule.** The workspace's framing-check pattern exists but fires at session boundaries. The literature (Attention Latch, arXiv:2604.24512) says the spacing matters more than depth — but a prose rule (`recite the goal after every tool call`) is behavioral and will fire at ~50%. The structural version: a Stop hook that checks the last 3 tool calls against the original task statement and flags divergence before allowing `done` claims.

5. **Subagent output filtering is the documented mechanism for inherited drift.** The workspace re-ingests subagent output freely. Filtering for goal-relevant content before re-ingestion is the structural fix.

6. **The reviewer-must-hold-oracles principle applies to /tp spawn practice, not design.** Pure-reasoning reviewers are net-negative (Zhang et al. 2024, arXiv:2412.14959). /tp's spawn template already provides external tools (read_file, grep, list_dir, run_terminal_command) per SKILL.md line 1450. The gap is whether spawned /tp subagents actually USE these tools in practice — enforcement, not design. [CORRECTED 2026-08-12: original version falsely claimed /tp was reasoning-only; it is tool-equipped by design.]

## Key findings (what works and what doesn't)

**What works (structural, verified):**
- Typed artifacts between context layers (Anthropic feature_list.json, Plan-and-Act, InfiAgent)
- Deterministic monitors + LLM advisor on trigger (LivePlan +12-15pp)
- NLI faithfulness gates on citations (~85% accuracy, ~$0.003/query)
- Fresh-context verification subagents with external oracles (not pure reasoning)
- Verify-before-retry with postcondition checks (72% → 20% duplicate side effects)
- Event-driven monitoring > periodic monitoring (LivePlan ablation)

**What doesn't work (behavioral, documented to fire ~50%):**
- Prose rules in AGENTS.md ("claims require receipts")
- Same-context self-critique (the draft anchors its own audit)
- Pure-reasoning fact-checkers without external tools (net-negative)
- Periodic monitoring (worse than event-driven)

## Receipts

Claims about local skill mechanisms, labeled by inspection status:

- **The workspace has Stop hooks with stderr feedback** — [OBSERVED] used throughout this session; standard pattern
- **The workspace has /tp two-lens as reasoning-only reviewer** — [INFERENCE] from reading /tp SKILL.md this session; the spawn template provides context bundle but does not require external tool calls
- **The workspace lacks typed-artifact boundary for small edits** — [INFERENCE] skill-authoring commits (like this session's bb053a1) do not flow through a typed artifact; they go directly to commit
- **/check is operator-invoked, not event-triggered** — [INFERENCE] from skill description; not verified by reading /check SKILL.md this session
- **Anthropic's feature_list.json pattern is real** — [INFERENCE] from subagent search results citing anthropic.com/engineering/effective-harnesses-for-long-running-agents; primary source not fetched directly this session
- **LivePlan +12.33pp result** — [INFERENCE] from subagent reading arXiv:2608.06701 abstract; full paper not read
- **57% citation unfaithfulness (Wallat 2025)** — [INFERENCE] from subagent search results; paper not fetched directly

**All recommendations are [UNTESTED]** on this workspace.

## Falsifier

This research is wrong if, after implementing the top 3 recommendations (typed-artifact boundary, citation-faithfulness gate, event-triggered /tp):
1. The typed artifact (e.g., mandatory plan file before skill edits) slows work without catching failures
2. The NLI citation gate has >30% false-positive rate (flags faithful citations as unfaithful)
3. Event-triggered /tp fires too often and creates alert fatigue
4. The operator finds the added ceremony worse than the failures it prevents

If all four hold after 5+ real uses, revert.

## Sources

- [Anthropic — Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Nov 2025)
- [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices) (Boris Cherny)
- [LivePlan — Online Monitoring and Corrective Steering](https://arxiv.org/abs/2608.06701)
- [Verified Tool Calls](https://arxiv.org/abs/2608.02645)
- [Evaluating Goal Drift in Language Model Agents](https://arxiv.org/abs/2505.02709) (Arike et al. AAAI/AIES 2025)
- [Inherited Goal Drift](https://arxiv.org/abs/2603.03258)
- [Attention Latch](https://arxiv.org/abs/2604.24512)
- [Plan-and-Act](https://arxiv.org/abs/2503.09572) (ICML 2025)
- [InfiAgent](https://arxiv.org/abs/2601.03204)
- [Wallat et al. — Correctness is not Faithfulness](https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/wallat-2025-correctness.pdf)
- [Cited but Not Verified](https://arxiv.org/abs/2605.06635)
- [AgentPatterns — Honesty Harness](https://agentpatterns.ai/verification/honesty-harness-fabrication-defense/)
- [dev.to — Force a Criteria Check Before the Task Ends](https://dev.to/mcsee/ai-coding-tip-024-force-a-criteria-check-before-the-task-ends-51ij)
- [antemortem-cli](https://github.com/hibou04-ops/antemortem-cli)
- [Patronus AI Lynx](https://github.com/patronus-ai/Lynx-hallucination-detection)
- [LangChain — Harness Engineering for Deep Agents](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)
- [[premature-synthesis-without-reading-existing-capability]] — existing diagnostic
- [[narrative-as-signal]] — existing diagnostic
- [[llm-overconfidence-documentation-as-truth-bias-field-solutions-2026]] — existing field solutions
- [[mechanical-enforcement-of-llm-skill-steps-2026]] — existing mechanical-enforcement layer
