---
title: "Brain skill improvement: tools, repos, MCP servers, skills, and research (2026)"
created: 2026-08-12
source: session-2026-08-12 (/www on improving /brain quantity + quality)
sources:
  - https://github.com/spranab/brainstorm-mcp
  - https://github.com/karpathy/llm-council
  - https://github.com/origo-labs/separate-then-together
  - https://github.com/Lum1104/agent-brainstorm
  - https://github.com/mobilema-cell/collective-brainstorming
  - https://arxiv.org/abs/2510.01218
  - https://arxiv.org/abs/2512.23601
  - https://arxiv.org/abs/2409.14634
  - https://arxiv.org/abs/2509.21043
  - https://arxiv.org/abs/2511.11306
  - https://github.com/aixstar/llm-research-idea-evaluation
  - https://arxiv.org/abs/2606.11762
  - https://arxiv.org/abs/2412.14626
  - https://github.com/yansheng-qiu/AI_Idea_Bench_2025
tags: [brainstorming, ideation, brain-skill, multi-agent, mcp-server, claude-skill, llm-creativity, divergent-thinking, convergent-thinking, idea-evaluation, selective-temperature, persona-diversity, research-survey, tool-catalog]
host: both
agent: grok
cognitive_load: 4
verification: multi-source-verified
summary: >
  Catalog of tools, repos, MCP servers, Claude/Grok skills, and research papers
  (2025-2026) that can improve /brain's idea quantity and quality. Organized into
  five categories: (1) MCP servers and skills practitioners like, (2) multi-model
  persona brainstorming repos, (3) 2025-2026 research techniques, (4) convergent
  thinking / idea evaluation tools, (5) highest-leverage actionable techniques.
  Key qualifier: same-model persona diversity barely beats N=1 per existing wiki
  [[multi-agent-correlated-errors]]; the multi-model advantage requires orthogonal
  model families (Grok + Gemini + Codex), not same-model personas.
---

# Brain skill improvement: tools, repos, MCP servers, skills, and research (2026)

## Decision context

**Why this research was needed:** the operator asked what existing tools, repos,
skills, plugins, MCP servers, and research can improve /brain's idea quantity
and quality — noting the fleet has multiple LLM models that can take on different
personalities. /brain currently runs a single-model diamond process (diverge →
converge on problem → diverge → converge on design) and combinatorial ideation
(TRIZ, SCAMPER, cross-domain recombination). The gap: no multi-model dispatch,
no structured convergence beyond "present 2-3 approaches," and no novelty
verification.

**What alternatives were explored:** four parallel research angles — (1) MCP
servers/skills practitioners like, (2) multi-model persona repos, (3) 2025-2026
research papers, (4) convergent thinking / idea evaluation tools. The search
covered 30+ searches across DDG, HN Algolia, Reddit, GitHub Issues. No tool was
found that perfectly matches /brain's gap (multi-LLM judge convergence for
brainstorming outputs) — the closest are building blocks, not turnkey solutions.

**What the research changed:** identified 5 highest-leverage techniques that are
directly implementable, 3 repos worth evaluating for integration, and critical
qualifications from existing wiki concepts that constrain how multi-persona
approaches should be applied.

## Existing wiki coverage (do not duplicate)

- [[brainstorming-ideation-with-llms]] — comprehensive landscape survey (mental
  models, MECE, morphological analysis, SCAMPER, Claude Code ultrathink/ultracode,
  6 workflow patterns, fleet repos). This concept extends it with concrete tools.
- [[adhd-parallel-frame-divergent-ideation-integration]] — ADHD N-frame divergence.
- [[multi-agent-correlated-errors]] — persona diversity alone doesn't help;
  frame diversity and orthogonal-model critics do.
- [[llm-council-and-model-fusion]] — MoA, OpenRouter Fusion, Karpathy council.
- [[ai-thought-partner-landscape-and-tp-improvements-2026]] — MAD research.
- [[persona-injection-across-dispatch-paths]] — persona format constraints.
- [[creative-reasoning-as-reusable-skill-graph-functions]] — /brain's reference files.
- [[thought-collapse-in-llms]] — structural mode collapse in LLM reasoning.

---

## Category 1: MCP servers and skills practitioners like

### MCP servers

| Server | What it does | Signal | URL |
|--------|-------------|--------|-----|
| **spranab/brainstorm-mcp** | Multi-round AI brainstorming debates between GPT, Gemini, DeepSeek, Groq, Claude. Structured debate + synthesis, red-team/Socratic modes. "Don't trust one AI. Make them argue." | 67 stars; broad registry presence (mcp.so, mcpservers.org, mcpbeat, PulseMCP) | https://github.com/spranab/brainstorm-mcp |
| **theodorstorm/brainstorm-mcp** | Multi-agent collaboration via structured communication, shared resources, persistent state. | Listed on mcpservers.org; low signal | https://mcpservers.org/servers/theodorstorm/brainstorm-mcp |
| **MrLesk/agents-council** | Connect Claude, Codex, and Local Agents via MCP for council-style deliberation. | HN Show HN post (3pts); directly relevant to fleet's cross-model capability | https://github.com/MrLesk/agents-council |

### Claude Code / Grok skills

| Skill | What it does | Signal (installs) | URL |
|-------|-------------|-------------------|-----|
| **obra/superpowers brainstorming** | Hard-gates implementation behind Socratic design refinement. One-question-at-a-time dialogue. "You MUST use this before any creative work." | 261K installs / 268K repo stars — highest signal of any tool surveyed | https://github.com/obra/superpowers |
| **mattpocock/grill-me** | Relentless one-question-at-a-time adversarial interview. Walks decision trees branch-by-branch. Surfaces weak points through systematic questioning. | **812K installs** — highest-mass brainstorming-adjacent tool | https://www.skills.sh/mattpocock/skills/grill-me |
| **Keith-cclarity/brainstorming-skill** | Stress-tests ideas through 7 fixed reasoning prompts, each forcing a different mode. Synthesis step ties all 7 together. | Low signal; referenced by skill indexes | https://github.com/Keith-cclarity/brainstorming-skill |
| **yonatangross/orchestkit brainstorm** | Multi-stage phase workflow with explicit "When NOT to Use" gating. Part of 114-skill toolkit. | 191 stars parent; 757 installs (ui-components) | https://github.com/yonatangross/orchestkit |
| **umputun/cc-thingz brainstorm** | Custom-rules-injection: free-form markdown rules loaded at skill invocation time, applied alongside built-in behavior. | 432 stars | https://github.com/umputun/cc-thingz |
| **robertguss/claude-code-toolkit brainstorm** | Multi-session ideation projects spanning days/weeks. Includes writing-dna-discovery (captures writer's voice). | Broad index presence | https://github.com/robertguss/claude-code-toolkit |

**Key methodology caveat** (from levelup.gitconnected.com): GitHub stars misrepresent
skill adoption — install counts from skills.sh are more reliable. When evaluating
tools, prioritize install count over star count.

---

## Category 2: Multi-model persona brainstorming repos

These repos implement the "different models, different personalities" pattern the
operator specifically mentioned. Critically assessed against
[[multi-agent-correlated-errors]]: same-model-different-persona barely beats N=1.

### Tier 1 — Persona-based multi-agent ideation

**origo-labs/separate-then-together** (https://github.com/origo-labs/separate-then-together)
Reference implementation of arXiv 2512.04488 (Meta Reality Labs, Dec 2025). Two
phases: **Separate** (agents see only their own output for N turns, maximizing
diversity via epistemic isolation) → **Together** (agents share full history for
synthesis). Persona selection uses cosine-similarity on embeddings to pick
maximally *dissimilar* pairs. OpenAI-compatible API (works with Ollama, OpenRouter).
**Why it matters:** the epistemic isolation during divergence is the structural
fix for diversity collapse — agents can't anchor on each other's outputs.

**Lum1104/agent-brainstorm** (https://github.com/Lum1104/agent-brainstorm)
6-stage pipeline: Context Generation → Assemble Team (4 expert personas via Preview
Agent) → Divergent Ideation (5 ideas/persona) → Red Team Critique → Convergent
Evaluation → Final Plan. Roles assigned by *topic*, not free-form. Gemini-only
(single model family). **Limitation:** single-model — needs cross-family dispatch
to realize the diversity advantage per [[multi-agent-correlated-errors]].

**mobilema-cell/collective-brainstorming** (https://github.com/mobilema-cell/collective-brainstorming)
4-phase: Parallel (3 agents: Architect / DevOps-SRE / DX-Product) → Debate
(commitment + steelman each other) → Review (tri-gate: exact quote + failure
mechanism + survives synthesis) → Synthesize. **Why it matters:** the tri-gate
reviewer is exactly what [[multi-agent-correlated-errors]] flagged as missing in
typical multi-agent brainstorming.

**lawraa/LLM-Discussion** (https://github.com/lawraa/LLM-Discussion, paper arXiv 2405.06373)
Three-phase: Initiation → Discussion → Convergence. Roles auto-generated for
diversity; each LLM reminded of persona each round to fight drift. 4 agents × 5
rounds was the sweet spot. Anti-drift technique (persona re-injection each round)
maps onto /go subagent dispatch.

### Tier 2 — Council / jury pattern (multi-MODEL)

**karpathy/llm-council** (https://github.com/karpathy/llm-council)
FastAPI + React. Each member model answers independently. Members then
**anonymously review and rank** each other's answers. A **chairman** synthesizes
the final answer from rankings + originals. ~23.8K stars. **Why it matters:** the
anonymous-review → chairman pattern is the missing third step in /brain's Diamond 2
— current /brain produces approaches but has no cross-evaluation step.

**machine-theory/lm-council** (https://github.com/machine-theory/lm-council, NAACL 2025)
Council of N models (deepseek-r1, gemini-2.5-flash-lite, grok-3-mini,
llama-3.1-8b-instruct) democratically evaluate each other. **Why it matters:**
the validated cross-family model list maps directly to the fleet's available
models — /brain could dispatch to Grok + Gemini (via /agy) + Codex (via /codex)
+ MiniMax (via /mmx).

---

## Category 3: 2025-2026 research techniques (new since last survey)

### Generation techniques

**Selective Temperature Sampling** (arXiv 2510.01218, Oct 2025)
Addresses the core trade-off: high temperature increases diversity but lowers
quality; low temperature increases quality but kills diversity. Solution:
generate at high temperature, then filter for quality. **Most concrete single
technique for /brain** — implementable in ~30 minutes. Generate N ideas at temp
1.2, score each with a quality rubric, keep the diverse survivors.

**CreativeDC** (arXiv 2512.23601, Dec 2025)
Two-phase prompting grounded in Wallas's creativity theory and Guilford's
divergent-convergent framework. Explicitly scaffolds LLM reasoning into distinct
divergent (broad) and convergent (filter/refine) phases. **Directly importable**
— /brain could adopt CreativeDC as its default phase structure. Strongest single
paper for /brain workflow design.

**Scideator** (arXiv 2409.14634)
Extracts facets (purposes, mechanisms, evaluations) from papers + related work;
users interactively recombine facets with logical-compatibility checks. User
study showed significantly higher creativity support than baseline LLM. **Fits
/brain's recombine mode** — the facet extraction → recombination pattern maps to
/brain's combinatorial ideation, with built-in novelty verification.

**Combinatorial Creativity** (arXiv 2509.21043, 2412.14141)
Cross-domain knowledge discovery via generalization-level retrieval + structured
combinatorial process. Distinguishes novelty from value (both required). **Fits
/brain's cross-domain analogy** — could pull from adjacent wiki concepts as the
cross-domain knowledge source.

**CreativityNeuro** (arXiv 2607.01433, Jul 2026)
Steers language model weights (activation-level intervention) to improve
divergent thinking and reduce mode collapse. No fine-tuning required. **Future
option** — requires weights/activations access, not available via closed APIs.

### Diversity collapse solutions

**iMAD** (arXiv 2511.11306, Nov 2025)
Multi-agent debate that **selectively triggers debate only when beneficial**.
Avoids the cost of always-on debate. **Highly relevant gate for /brain** —
shouldn't always spawn multi-agent debate; needs a heuristic for when to escalate.

**PM Loop** (https://github.com/kphatak001/pm-loop)
Multi-agent pipeline with directed graph of AI agents with opposing incentives.
Topology of disagreement forces quality convergence. Typed feedback loops.
**Concrete importable pattern** — typed feedback between opposing-incentive
agents is implementable as a workflow today.

**Examining Barriers to Diversity** (arXiv 2602.20408)
Identifies engineering decisions that preserve multi-agent diversity (3
conditions). Maps directly to /brain if multi-agent mode is added — apply the 3
conditions as design constraints.

### Key finding: LLM novelty judgments diverge from human experts

**"Is This Idea Novel?" benchmark** (LREC 2026, 1,381 human experts + 9 automated
metrics): LLM novelty judgments diverge from human-expert judgments. **This means
/brain should NEVER rely on a single LLM-as-judge for novelty.** Needs structured
disagreement (multiple judges from different families) or human judgment for the
novelty axis. Feasibility/usefulness can be LLM-judged; novelty requires more.

---

## Category 4: Convergent thinking / idea evaluation tools

### Drop-in rubrics for /brain's convergence phase

**aixstar/llm-research-idea-evaluation** (https://github.com/aixstar/llm-research-idea-evaluation)
Open-source 8-axis rubric: grounding, known-gap recovery, future-direction
alignment, method concreteness, testability, feasibility, novelty, diversity.
**Drop-in rubric structure** for /brain's convergence step — explicit axes
already designed for LLM scoring.

**LDC** (arXiv 2412.14626)
Dynamic controllers for novelty vs. feasibility with explicit scoring guidelines.
Table 5 shows tuning the novelty controller shifts the trade-off curve.
**Scoring definitions are liftable verbatim** — Novelty / Feasibility /
Effectiveness rubric.

**IdeaBench** (ACM KDD 2025, arXiv 2411.02429)
Profiles LLMs as domain-specific researchers. Key finding: **LLMs excel at
novelty but struggle with feasibility.** Trained a reward model with real-world
ideas to address this gap.

### Semantic entropy for diversity measurement

**Automated Creativity Evaluation** (ACL 2026 Main, arXiv 2606.11762,
code: https://github.com/tanminsen/creativity-eval)
Domain-general framework: divergent creativity via semantic entropy, convergent
creativity via retrieval-based multi-agent judge. Separates measurement from
creative task. **Most directly applicable single paper** — implements both phases
with explicit methods, has open-source code, ACL 2026 Main.

**Semantic entropy clustering** (Thoughtworks walkthrough):
Cluster outputs into semantic equivalence groups, compute entropy over cluster
probabilities. Low entropy = many surface variations of one idea (low real
diversity); high entropy = genuinely diverse. **/brain could use this as a
diversity check** — "are these N ideas really different?"

### Jury vs. judge

**Juries, Not Judges!** (NeurIPS Expo 2025): dynamic LLM juries outperform single
judges for industry-scale evaluation. **The Crowd Without People** (Springer
Group Decision 2026): multiple LLMs each evaluate independently, scores averaged.
Validates "LLM-as-crowd" as a stand-in for human panels. **Supports treating
/brain's evaluator as a small jury (3 models from different families) rather than
one prompt.**

---

## Category 5: Highest-leverage actionable techniques (ranked)

Assessed against workspace observations and existing wiki constraints.

### 1. Selective temperature sampling [SUPPORTED] [UNTESTED]
**Technique:** Generate N ideas at high temperature (1.2+), score each with a
quality rubric, keep diverse survivors. Most concrete single technique.
**Evidence basis:** single-paper (arXiv 2510.01218).
**Applicability:** passes 4/5 dimensions (open system, multi-model possible,
graded quality, same domain). Only mismatch: evidence type (fixed vs investigative).
**Workspace constraint check:** no host invariant violation.
**Implementation:** add a `--diverse` flag to /brain that sets high temperature
for the divergent phase and applies a quality filter before convergence.

### 2. CreativeDC divergent→convergent scaffold [SUPPORTED] [UNTESTED]
**Technique:** explicitly separate divergent (broad generation) from convergent
(filter/refine) phases with distinct prompting strategies for each.
**Evidence basis:** single-paper (arXiv 2512.23601).
**Applicability:** passes 5/5 dimensions.
**Implementation:** /brain already does this structurally (diamond process), but
the prompting within each phase could be sharpened using CreativeDC's specific
scaffolding.

### 3. Cross-family council for convergence [SUPPORTED] [UNTESTED]
**Technique:** after /brain generates approaches, dispatch each to a different
model family (Grok + Gemini via /agy + Codex via /codex) for independent
evaluation, then synthesize via chairman.
**Evidence basis:** multi-source (karpathy/llm-council 23.8K stars, machine-theory/lm-council
NAACL 2025, Juries Not Judges NeurIPS 2025, Crowd Without People Springer 2026).
**Applicability:** passes 5/5 dimensions. The workspace already has /agy, /codex,
/mmx for cross-model dispatch — no new infrastructure needed.
**Critical constraint:** per [[multi-agent-correlated-errors]], must use
orthogonal model families, not same-model personas. The fleet's cross-family
capability is the key enabler.

### 4. Novelty verification via RAG against wiki/codebase [SUPPORTED] [UNTESTED]
**Technique:** before declaring an idea "novel," run a retrieval pass against the
wiki + codebase + package docs to check whether it already exists.
**Evidence basis:** multi-source (Idea Novelty Checker ACL 2025, Scideator
arXiv 2409.14634, Creativity Eval ACL 2026).
**Applicability:** passes 4/5 dimensions. Mismatch: our "literature" is the wiki
+ codebase, not academic papers — but the technique transfers.
**Implementation:** /brain's convergence phase could call search_wiki with each
idea's key terms and flag matches as "already exists in workspace."

### 5. iMAD-style selective debate gate [SUPPORTED] [UNTESTED]
**Technique:** only escalate to multi-agent debate when a heuristic detects
benefit (ambiguity, high stakes, operator uncertainty). Not always-on.
**Evidence basis:** single-paper (arXiv 2511.11306).
**Applicability:** passes 4/5 dimensions. Mismatch: the heuristic for "when to
escalate" is not yet defined — needs operator input.
**Implementation:** add a gate to /brain that checks stakes/ambiguity before
spawning the cross-family council.

---

## Workspace-counterexample check

| Recommendation | Counterexample check | Result |
|---|---|---|
| Cross-family council | [[multi-agent-correlated-errors]]: persona diversity alone doesn't help | ✅ Accounts for it — explicitly requires orthogonal model families, not same-model personas |
| Selective temperature | [[thought-collapse-in-llms]]: structural mode collapse | ⚠️ Partial — temperature helps but can't fully solve structural collapse. Weight-level intervention (CreativityNeuro) is the deeper fix, but not API-accessible |
| LLM-as-judge convergence | [[brainstorming-ideation-with-llms]]: LLMs worst at novelty assessment | ⚠️ Qualified — LLM judges OK for feasibility/usefulness, NOT for novelty. Novelty requires multi-judge or human judgment |
| Multi-persona ideation | [[multi-agent-correlated-errors]]: N=3 same-model barely beats N=1 | ✅ Accounts for it — all multi-persona recommendations require cross-family dispatch |
| CreativeDC scaffold | No counterexample found | ✅ Proceed |

---

## Host invariant check

| Recommendation | Invariant check | Status |
|---|---|---|
| Cross-family council | Multi-terminal isolation: subagent dispatch must be session-scoped | ✅ /agy, /codex, /mmx already handle this correctly |
| Cross-family council | DDG-first for searches | ✅ No search needed — dispatch is direct |
| Cross-family council | No live browser state contention | ✅ No browser access needed |
| Novelty RAG verification | search_wiki is FTS5, session-safe | ✅ Already used by /www |
| Selective temperature | No MCP tool contention | ✅ Pure model config |

No host invariant violations detected.

---

## Decision contract

<decision-contract>
schema_version: 1

decision_contract:
  required: false
  reason: research_survey_with_actionable_recommendations

decision:
  state: SPIKE_REQUIRED
  proposed_action: SPIKE

outcome_without_mechanism: "improve /brain's idea quantity and quality using existing tools, research, and the fleet's multi-model capability"

discovery:
  direct_alternatives:
    - candidate: spranab/brainstorm-mcp
      receipt: https://github.com/spranab/brainstorm-mcp
      disposition: investigate
      reason: multi-model debate MCP server; evaluate whether to integrate as MCP dependency or extract pattern
    - candidate: karpathy/llm-council
      receipt: https://github.com/karpathy/llm-council
      disposition: investigate
      reason: 23.8K stars; anonymous-review + chairman pattern is the missing convergence step
    - candidate: origo-labs/separate-then-together
      receipt: https://github.com/origo-labs/separate-then-together
      disposition: investigate
      reason: epistemic isolation during divergence is the structural fix for diversity collapse
  adjacent_alternatives:
    - candidate: mattpocock/grill-me (812K installs)
      receipt: https://www.skills.sh/mattpocock/skills/grill-me
      disposition: investigate
      reason: adversarial interrogation mode could complement /brain as a downstream step
    - candidate: aixstar/llm-research-idea-evaluation
      receipt: https://github.com/aixstar/llm-research-idea-evaluation
      disposition: reuse
      reason: 8-axis rubric is directly liftable into /brain's convergence phase
  capability_reuse:
    - capability: cross_model_dispatch
      candidate: /agy + /codex + /mmx skills
      receipt: ~/.grok/skills/agy/SKILL.md, ~/.grok/skills/codex/SKILL.md, ~/.grok/skills/mmx/SKILL.md
    - capability: novelty_verification
      candidate: search_wiki MCP tool
      receipt: search_wiki__query tool in this session's MCP server list
  workspace_existing:
    - candidate: /brain skill
      receipt: ~/.grok/skills/brain/SKILL.md
    - candidate: /tp skill (critique mode)
      receipt: ~/.grok/skills/tp/SKILL.md

best_reuse_candidate:
  candidate: aixstar/llm-research-idea-evaluation rubric + cross-family council via /agy//codex//mmx
  receipt: https://github.com/aixstar/llm-research-idea-evaluation, ~/.grok/skills/agy/SKILL.md
  disposition: REUSE

search_falsifier:
  killer_counterexample: "an existing Grok Build skill or plugin that already implements multi-model council brainstorming with idea evaluation"
  search_executed: true
  receipts:
    - "DDG: 'MCP server brainstorming ideation creative thinking' — found spranab/brainstorm-mcp, no Grok-native equivalent"
    - "DDG: 'Claude Code skill brainstorming ideation github stars' — found obra/superpowers (261K installs), no multi-model council skill"
    - "search_wiki: 'brainstorming ideation LLM multi-agent divergent thinking creative techniques' — no existing concept covers concrete tool integration"

decision_reversing_unknowns:
  - id: cross-family-cost
    status: OPEN
    falsification: "measure wall-clock latency + token cost of dispatching /brain convergence to 3 model families; if >60s or >$0.50 per run, the cost exceeds the diversity benefit"
  - id: novelty-judge-reliability
    status: OPEN
    falsification: "test whether cross-family jury novelty scores correlate better with operator judgment than single-model scores; needs 5+ real /brain sessions with operator scoring"
  - id: operator-adoption
    status: OPEN
    falsification: "the operator may prefer /brain's current speed over added ceremony; needs operator decision on which techniques to implement"

evidence_requirements:
  - claim: "cross-family council improves convergence quality"
    evidence_required: [runtime, live_ui]
    evidence_present: [document]
    discriminates_competing_explanations: false
  - claim: "selective temperature sampling increases idea diversity without quality loss"
    evidence_required: [runtime]
    evidence_present: [document]
    discriminates_competing_explanations: false
</decision-contract>

---

## What this means for our workspace

1. **/brain should add a `--diverse` mode** that uses selective temperature sampling
   (generate at temp 1.2+, filter by quality rubric, keep diverse survivors). This
   is the lowest-cost, highest-signal single technique — implementable in ~30 minutes.
2. **/brain's convergence phase should dispatch to cross-family models** via /agy
   (Gemini), /codex (Codex), /mmx (MiniMax) rather than relying on the parent model.
   The fleet already has this infrastructure. Per [[multi-agent-correlated-errors]],
   this must be cross-family, not same-model personas.
3. **/brain should add a novelty verification step** using search_wiki against the
   workspace's wiki + codebase before declaring an idea "novel." LLM novelty
   judgments diverge from human experts (LREC 2026, 1,381 experts) — retrieval
   grounding compensates.
4. **The 8-axis rubric from aixstar/llm-research-idea-evaluation should be adopted**
   as /brain's convergence scoring structure. It replaces ad-hoc "present 2-3
   approaches" with structured multi-dimensional evaluation.
5. **/brain should NOT adopt same-model persona switching** (Six Thinking Hats,
   role-play within one model) — per [[multi-agent-correlated-errors]], N=3
   same-model barely beats N=1. The diversity must come from orthogonal model
   families.
6. **No existing tool is a turnkey solution** — the gap between "multi-model council
   for code review" (which exists) and "multi-model council for creative ideation
   with novelty verification" (which doesn't) requires composition of existing
   building blocks. /brain is the natural integration point.

## Key findings (what people like and don't like)

**What practitioners like:**
- obra/superpowers brainstorming (261K installs): hard-gate before implementation,
  one-question-at-a-time dialogue. The "MUST use before creative work" enforcement.
- mattpocock/grill-me (812K installs): adversarial interrogation that surfaces weak
  points systematically. Decision-tree-walking approach.
- spranab/brainstorm-mcp (67 stars): "Don't trust one AI. Make them argue." The
  multi-model debate pattern resonates.
- karpathy/llm-council (23.8K stars): anonymous peer review + chairman synthesis.

**What practitioners don't like (limitations):**
- GitHub stars misrepresent skill adoption — install counts (skills.sh) are the
  reliable metric (levelup.gitconnected.com methodology critique).
- LLM novelty judgments diverge from human experts — can't trust single-model
  novelty scoring (LREC 2026, 1,381 experts).
- Multi-agent debate has known failure modes: persuasion-driven adversarial
  dynamics (Nature s41598-026-42705-7), degenerate consensus (MAD research).
- Same-model different-persona doesn't prevent diversity collapse (ACL 2026,
  arXiv 2602.20408) — the most common implementation of "multi-persona" is the
  one that doesn't work.
- Creativity is not correlated with general intelligence (LiveIdeaBench) — a
  "smart" model is not necessarily a creative one.

## Receipts

Claims about local skill mechanisms, labeled by inspection status:

- **/brain currently runs single-model diamond process without multi-model dispatch** —
  [OBSERVED] read `~/.grok/skills/brain/SKILL.md` this session (lines 1-80). No
  spawn_subagent or cross-model dispatch step exists in the skill body.
- **/brain's recombine mode uses TRIZ/SCAMPER/cross-domain recombination** —
  [OBSERVED] read `~/.grok/skills/brain/references/combinatorial-ideation.md`,
  `creative-techniques.md`, `ideation-heuristics.md` (file listing confirmed).
- **The workspace has /agy, /codex, /mmx for cross-model dispatch** — [OBSERVED]
  these skills are in the session skill catalog with paths at
  `C:\Users\brsth\.grok\skills\{agy,codex,mmx}\SKILL.md`.
- **search_wiki MCP tool is available for novelty verification** — [OBSERVED] used
  `search_wiki__query` this session; returns FTS5 results from 990+ concepts.
- **[[multi-agent-correlated-errors]] documents that persona diversity alone
  doesn't help** — [OBSERVED] read via search_wiki this session; summary confirms
  "N=3 barely beats N=1" for same-model persona switching.
- **spranab/brainstorm-mcp has 67 stars and multi-model debate** — [INFERENCE]
  from subagent search results (mcpbeat, agentindex); star count not verified on
  GitHub directly this session.
- **karpathy/llm-council has ~23.8K stars** — [INFERENCE] from subagent search
  results (third-party sourceforge summary); primary GitHub page not fetched directly.
- **Selective temperature sampling is the most concrete technique** — [INFERENCE]
  from reading the arXiv abstract only (2510.01218); not tested on this workspace.
- **CreativeDC divergent-convergent scaffold is directly importable** — [INFERENCE]
  from reading the arXiv abstract only (2512.23601); not tested on this workspace.
- **All 5 recommended techniques are [UNTESTED]** — none were implemented or
  measured on this workspace during this research run. Applicability assessments
  are based on reading papers/repositories, not runtime verification.

## Falsifier

This research is wrong if, after implementing the top 3 techniques (selective
temperature, CreativeDC scaffold, cross-family council):

1. **Selective temperature** produces more diverse but consistently lower-quality
ideas than default temperature — the quality filter doesn't compensate.
2. **Cross-family council** takes >60s per convergence and the operator abandons
it for speed — the latency cost exceeds the diversity benefit.
3. **The cross-family council never produces a recommendation that the single-model
/brain didn't already produce** — the multi-model overhead was unnecessary for
this workspace's typical ideation tasks.
4. **Novelty RAG verification** has >30% false-positive rate (flags ideas as
"already exists" when they don't) — the retrieval is too fuzzy for novelty claims.

If all four hold after 5+ real uses, revert to current /brain and keep only the
CreativeDC scaffold refinement.

## Sources

- [spranab/brainstorm-mcp](https://github.com/spranab/brainstorm-mcp) — multi-model debate MCP server (67 stars)
- [karpathy/llm-council](https://github.com/karpathy/llm-council) — LLM council with anonymous review + chairman (~23.8K stars)
- [origo-labs/separate-then-together](https://github.com/origo-labs/separate-then-together) — epistemic isolation framework (arXiv 2512.04488)
- [Lum1104/agent-brainstorm](https://github.com/Lum1104/agent-brainstorm) — 6-stage multi-agent pipeline
- [mobilema-cell/collective-brainstorming](https://github.com/mobilema-cell/collective-brainstorming) — parallel → debate → review → synthesize
- [MrLesk/agents-council](https://github.com/MrLesk/agents-council) — Claude + Codex + Local Agents council via MCP
- [mattpocock/grill-me](https://www.skills.sh/mattpocock/skills/grill-me) — adversarial interview skill (812K installs)
- [obra/superpowers](https://github.com/obra/superpowers) — Socratic design refinement (261K installs)
- [aixstar/llm-research-idea-evaluation](https://github.com/aixstar/llm-research-idea-evaluation) — 8-axis idea evaluation rubric
- [yansheng-qiu/AI_Idea_Bench_2025](https://github.com/yansheng-qiu/AI_Idea_Bench_2025) — idea generation benchmark
- [tanminsen/creativity-eval](https://github.com/tanminsen/creativity-eval) — semantic entropy creativity evaluation (ACL 2026)
- [kphatak001/pm-loop](https://github.com/kphatak001/pm-loop) — structured disagreement convergence
- [Selective Temperature Sampling](https://arxiv.org/abs/2510.01218) — diverse + high-quality via selective sampling (Oct 2025)
- [CreativeDC](https://arxiv.org/abs/2512.23601) — divergent-convergent thinking scaffold (Dec 2025)
- [Scideator](https://arxiv.org/abs/2409.14634) — facet extraction + recombination for ideation
- [Combinatorial Creativity](https://arxiv.org/abs/2509.21043) — cross-domain knowledge discovery
- [iMAD](https://arxiv.org/abs/2511.11306) — selective multi-agent debate (Nov 2025)
- [LDC](https://arxiv.org/abs/2412.14626) — dynamic novelty vs feasibility control
- [Juries Not Judges](https://neurips.cc/virtual/2025/loc/san-diego/128660) — NeurIPS Expo 2025
- [IdeaBench](https://arxiv.org/html/2411.02429) — ACM KDD 2025
- [[brainstorming-ideation-with-llms]] — existing workspace concept (extended by this)
- [[multi-agent-correlated-errors]] — key qualifier on persona diversity
- [[thought-collapse-in-llms]] — structural mode collapse limitation
- [[adhd-parallel-frame-divergent-ideation-integration]] — N-frame divergence
- [[persona-injection-across-dispatch-paths]] — persona format constraints
