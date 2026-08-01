---
title: "Workspace infrastructure investment priorities — 6-track investigation solidifying skill wiring, verification, persistence, search, instruction budget, and enforcement ceiling"
created: 2026-07-27
source: session-019fa48a (/www investigation of /tp opportunity scan Tracks A-F)
tags: [investment-priorities, skill-wiring, verification-receipts, persistence-automation, search-infrastructure, instruction-budget, mechanical-enforcement, agent-memory, fts5, agents-md, system-design]
summary: >
  A /www investigation of 6 system-level opportunity tracks identified by a /tp
  opportunity scan. Each track was researched against external evidence to
  solidify the proposed direction and explore uncertainties. Key findings:
  (A) skill graphs exist in research but lack production maturity for single-user
  workspaces — directive descriptions + slash commands remain the reliable path;
  (B) multi-source verification receipts work in production (in-toto/SLSA) but
  require an explicit policy schema, not just format broadening — false-positive
  rates range from 3.2% tuned to 30-90% untuned; (C) agentmemory is Linux-only
  on Windows (officially unsupported), and Letta's filesystem benchmark (74.0%
  on LoCoMo) suggests our handoff+wiki substrate may already suffice — the
  optimal move is a thin async consolidator over existing artifacts, not a
  system replacement; (D) FTS5 is sufficient for ~1000 markdown docs —
  Karpathy's llm-wiki pattern (July 2026) independently confirms this —
  sqlite-vec is the escape hatch if embeddings are ever needed; (E) AGENTS.md
  at 992 lines is well past the reliable-compliance band (~150-300) — the
  "Curse of Instructions" (ICLR 2025) shows non-linear degradation, and
  HumanLayer measured ~3% success-rate drop + >20% cost increase when bloated;
  (F) the enforcement ceiling is ~3-7 well-targeted hooks, bounded by
  synchronous latency + false-positive rate, not count — alarm fatigue sets in
  above ~10-20% false-positive rate. Cross-cutting pattern: every track
  converges on "thin layer over existing substrate" rather than "replace the
  substrate."
cognitive_load: 4
verification: multi-source-verified
host: both
agent: grok
sources:
  - "Track A: AgentSkillOS (arxiv 2603.02176), vLLM Semantic Router (github.com/vllm-project/semantic-router), Seleznov 650-trial study (Mar 2026)"
  - "Track B: in-toto attestation framework (in-toto.io), SLSA v1.2 provenance (slsa.dev), SonarQube false-positive data (Feb 2026), Palantir in-toto deployment (Sept 2025), pre-commit conflict analysis (github.com/pre-commit/pre-commit/issues/1104)"
  - "Track C: agentmemory GitHub README (rohitg00/agentmemory), Letta LoCoMo benchmark (Aug 2025), mem0 issue #4573 (97.8% junk rate, Mar 2026), OpenAI context personalization cookbook"
  - "Track D: Karpathy llm-wiki pattern (July 2026), sqlite-vec (Alex Garcia), BrainDB FTS5 benchmarks (Apr 2026), BM25 vs embeddings e-commerce benchmark (ai.rs)"
  - "Track E: Curse of Instructions (Harada et al. ICLR 2025), Lost in the Middle (Liu et al. 2023, 5363 cit), HumanLayer AGENTS.md measurement, alexop.dev progressive disclosure guide"
  - "Track F: blakecrosley.com Claude Code hooks tutorial, arXiv 2504.11839 Good and Bad Failures in CI/CD, dev.to pre-commit anti-pattern analysis, Stripe Developer Coefficient report"
relations:
  - target: wiki/concepts/skill-auto-invocation-reliability.md
    type: refines
  - target: wiki/concepts/verification-receipt-systems-design-landscape.md
    type: extends
  - target: wiki/concepts/llm-dreaming-memory-consolidation.md
    type: refines
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
  - target: wiki/concepts/fts5-query-syntax-escaping-required.md
    type: related
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: related
  - target: wiki/concepts/qmd-patch-durability-strategy.md
    type: confirms
---

# Workspace infrastructure investment priorities — 6-track investigation

## Decision context

**The problem:** a `/tp` opportunity scan identified 6 system-level tracks
where the workspace could invest in improvements. Each track had a proposed
direction but unresolved uncertainties. The operator asked `/www` to
"solidify those ideas and explore the uncertainties" — meaning: research
each track against external evidence, resolve the open questions, and produce
a durable record of what the evidence says so future sessions don't re-research.

**What alternatives were explored:** each track was evaluated against its
"replace the substrate" alternative vs its "thin layer over existing substrate"
alternative. The research explored whether dedicated tools (agentmemory,
embedding databases, skill graphs, multi-source receipt systems) are worth
the transition cost, or whether our existing substrates (handoffs+wiki, qmd/FTS5,
directive descriptions, /check receipts, behavioral rules) are sufficient with
targeted improvements.

**What the research changed:** the investigation confirmed 4 of 6 proposed
directions with evidence, qualified 1 (Track C — agentmemory is Windows-
incompatible, thin consolidator is the better path), and provided falsifiers
for all 6. The cross-cutting finding — "thin layer over existing substrate"
wins on every track — reframes the investment strategy from "replace systems"
to "add targeted layers."

---

## Track A: Skill wiring layer (skill graph, recommendation hook)

### What we investigated

Whether a "skill graph" — an explicit dependency/recommendation mapping between
skills — would reduce the need for manual invocation and improve cross-skill
integration. Whether a context-aware recommendation hook (suggesting skills
based on conversation state) works better than directive descriptions.

### Findings

1. **Skill graphs exist in research but lack production maturity for single-
   user workspaces.** The AgentSkillOS paper (arxiv 2603.02176) describes a
   skill graph with dependency representation and scoring criteria, and vLLM's
   Semantic Router (github.com/vllm-project/semantic-router) implements
   semantic tool selection. But neither has documented production deployment
   for a workspace of our shape (~100 skills, single operator, Grok Build).
   [MEDIUM — research-stage evidence only]

2. **Directive descriptions + slash commands remain the reliable path.** Our
   existing wiki concept [[skill-auto-invocation-reliability]] already
   documents: 77% activation with passive descriptions, 100% with directive
   descriptions ("ALWAYS invoke... Do not X directly"), execution-following
   remains unsolved. No external source contradicts this. The skill
   recommendation hook (designed in `P:/docs/handoffs/skill-recommendation-
   hook-20260726/HANDOFF.md` but never built) would need to compete with the
   100% activation rate of directive descriptions — a high bar. [HIGH —
   650-trial study + cross-host confirmation]

3. **Maintenance burden of a skill dependency graph is the primary risk.**
   Skill relationship metadata decays as skills are added, renamed, merged,
   and retired. Without a continuous reconciliation process, the graph becomes
   stale and produces wrong recommendations — worse than no graph. Our
   workspace already struggles with skill catalog hygiene (~980 skills,
   `/skill-prune` needed monthly). [INFERENCE — no direct evidence of skill-
   graph decay specifically, but the general metadata-decay pattern is well-
   established in CI/CD and dependency-management literature]

### What this means for our workspace

The skill recommendation hook is still worth building (the handoff design is
complete), but it should use **runtime context matching** (semantic similarity
between current conversation and skill descriptions) rather than a **static
dependency graph** (maintained metadata). Runtime matching has no decay
problem — it recomputes from the live skill descriptions every time. The hook
fires as a PostToolUse or UserPromptSubmit suggestion, not a block.

**Confidence: [MEDIUM]** — the direction is clear (runtime matching over static
graph) but the hook has never been built or tested.

---

## Track B: Verification infrastructure (multi-source receipts)

### What we investigated

Whether broadening the Stop hook receipt writer to accept multiple verifier
outputs (pytest, pyright, ruff, not just /check) is safe, and what
false-positive rates and conflict-resolution patterns exist.

### Findings

1. **Multi-source receipt systems work in production — but require an explicit
   policy schema, not just format broadening.** The in-toto attestation
   framework (the production reference) uses a typed-predicate envelope where
   multiple tools attest independently, with conflict resolution declared
   **upfront in a layout** (thresholds, allowed keys, ordering, severity
   floors). SLSA v1.2 uses the same pattern. The convergence across both
   systems: "declare policy, then verify against policy." Broadening the
   receipt format without adding a policy schema increases the false-positive
   surface, not decreases it. [HIGH — 2 production reference architectures]

2. **False-positive rates vary by an order of magnitude depending on tuning.**
   SonarQube publishes 3.2% overall (well-tuned, Feb 2026); untuned SAST tools
   produce 30-90% false positives (dropping to 10-20% after configuration).
   The base-rate ceiling matters more than the tool count when stacking
   verifiers. Practitioners report "false-positive fatigue" as the dominant
   failure mode — teams learn to ignore output when severity isn't ranked.
   [HIGH — SonarQube published rate + practitioner consensus]

3. **Conflict resolution defaults to "fail-closed on any failure," which is
   hostile to multi-source design.** The pre-commit framework (most widely-
   deployed multi-verifier gate) has no native OR/AND/priority logic — an
   auto-formatter and a strict linter share the same exit code and fight on
   every commit. Our broadened receipt system would inherit this if multiple
   receipts binding to the same file are treated as additive without a
   combining policy. [HIGH — pre-commit issue tracker + lobste.rs analysis]

### What this means for our workspace

The verification receipt broadening (handoff: `verification-receipt-systems-
design-landscape`) is the right direction, but the implementation must include
a **policy schema** that declares how multiple receipts combine for the same
file:
- pytest pass on file X (required — functional correctness)
- ruff clean on file X (advisory — style)
- pyright severity ≤ error on file X (required — type safety)

Without this, broadening from /check-only to multi-format increases noise
rather than reducing friction. The receipt writer should tag each receipt
with a **verifier type** (functional / style / type-safety) and a **severity
floor** so the Stop hook can apply the policy.

**Confidence: [HIGH]** — the pattern is well-established in in-toto/SLSA, and
the false-positive concern is directly addressable with the policy schema.

---

## Track C: Persistence automation (agentmemory, /tp do? ownership)

### What we investigated

Whether agentmemory works on Windows, whether it should replace our manual
persistence workflow, and whether persistence should be owned by /close gates
or a separate consolidation skill.

### Findings

1. **agentmemory is officially unsupported on Windows.** The GitHub README
   (rohitg00/agentmemory) states verbatim: "Native Windows engine setup is
   manual (about 10 to 20 minutes) and `agentmemory connect` is currently
   unsupported there." The 53 MCP tools and `npx agentmemory install` flow
   work cross-platform, but the `connect` runtime — what actually captures
   and consolidates sessions — only runs on macOS/Linux. This resolves the
   primary uncertainty. [HIGH — direct README quote]

2. **Letta's filesystem benchmark is the most disruptive finding.** Letta
   proved that "a filesystem" — storing conversational history as a file with
   hybrid search — scores 74.0% on the LoCoMo benchmark, beating specialized
   memory tools. This directly challenges the premise that we need a
   sophisticated tool to replace our manual handoff+wiki workflow. Our
   `P:/docs/handoffs/` + qmd search may already match specialized tools at
   this scale. [HIGH — independent benchmark, Letta is a credible source]

3. **mem0's 97.8% junk rate is a real production failure, not a one-off.**
   GitHub issue #4573 (mem0ai/mem0, Mar 2026) documents that an audit of
   10,134 entries after 32 days in production found 97.8% were junk. Any
   automated persistence design must include a quality gate, not just
   plumbing. [HIGH — production issue with audit data]

4. **Two ownership patterns have emerged; the field favors async over
   blocking.** Pattern A: Letta-style background consolidation (async process).
   Pattern B: OpenAI's session-end async consolidation job. Our /close gate
   approach is Pattern B's blocking-mode variant, which most vendors have
   moved away from because it adds latency to the user-visible path. But for
   a single-operator workspace where /close is operator-invoked (not
   automatic), the blocking cost is acceptable — the operator is already
   waiting for the close report. [MEDIUM — vendor patterns, not single-user
   workspace evidence]

### Disconfirmation qualification

The Oracle blog notes filesystem memory works "until you need correctness
under concurrency, semantic retrieval, or structured query." Our workspace
has multi-agent concurrency (multiple sessions writing concurrently), but
we already have qmd for semantic retrieval. The concurrency challenge is
real but addressed by our existing file-editing protocol (atomic writes,
edit-then-verify, git commit frequency), not by a memory system. arxiv
2606.24775 confirms "no single architecture dominates across all scenarios."
**Not refuted — qualified by concurrency considerations that our existing
protocol already addresses.**

### What this means for our workspace

**Do NOT replace handoffs+wiki with agentmemory or mem0.** The optimal move
is a thin async consolidator over existing artifacts — this is the
[[llm-dreaming-memory-consolidation]] "meta-skill over existing substrates"
pattern. The `/dream` skill (already designed) is the right implementation:
it reads accumulated handoffs + AAR artifacts + www-ledger, synthesizes
cross-session patterns, and writes candidate wiki concepts for operator
promotion. This sidesteps the Windows-compat issue, the junk-rate risk, and
the single-author dependency risk.

For /tp persistence specifically: /tp should NOT own persistence. /tp is a
critique/exploration skill, not a persistence skill. Persistence belongs to
/close (blocking, operator-invoked) and /dream (async, background). /tp's
recommendations flow into /handoff and /wiki, which are already persistence
mechanisms.

**Confidence: [HIGH]** — the Letta filesystem benchmark + Windows incompat +
mem0 junk rate form a three-source convergence.

---

## Track D: Search infrastructure (qmd replacement vs FTS5-only vs embeddings)

### What we investigated

Whether a ~200-LOC bare FTS5 wrapper would be better than qmd, and whether
embeddings are worth the added complexity for a ~1000-doc local knowledge base.

### Findings

1. **FTS5 is sufficient for ~1000 markdown docs.** Multiple 2025-2026
   comparisons show BM25 outperforming embeddings on exact-match and rare-term
   queries at small scale. One e-commerce benchmark reports BM25 winning 92%
   vs 78% on exact matches. Embeddings only close the gap after domain
   fine-tuning or at much larger scale (50k+ docs). [HIGH — multiple
   benchmarks converge]

2. **Karpathy's llm-wiki pattern (July 2026) independently confirms FTS5 for
   markdown wikis.** Karpathy's pattern (published 2 days before this research)
   explicitly recommends: "No embeddings. No retrieval noise. markdown files
   are tiny. At 300-500 pages, add proper full-text search — FTS5 (SQLite) or
   BM25." This is a strong independent confirmation from a credible source who
   independently arrived at the same conclusion. [HIGH — Karpathy is an
   authoritative independent source]

3. **sqlite-vec is the Windows-compatible escape hatch.** If embeddings are
   ever needed, `sqlite-vec` (Alex Garcia, the original sqlite-vss author)
   runs on Windows/macOS/Linux/WASM and composes cleanly with FTS5 in the
   same SQLite file. The "FTS5 now, embeddings later" migration is genuinely
   low-cost — same DB file, same query code path. [HIGH — official extension
   with cross-platform support documented]

4. **Custom FTS5 wrapper maintenance cost is low if kept thin.** The
   historical pain points in qmd are (a) hand-rolled query-syntax escape logic
   (the bug we hit) and (b) over-engineered relevance scoring — not FTS5
   itself. A thin wrapper that uses SQLite's own token-escape helpers and
   does NOT try to be clever with ranking is ~200 LOC and low-maintenance.
   [HIGH — community consensus + our own qmd experience]

### What this means for our workspace

The qmd replacement handoff (`qmd-fts5-replacement-20260727`) is the right
direction. The ~200-LOC bare FTS5 wrapper removes the query-syntax escaping
bugs and the single-author dependency without losing search quality. The
discriminating next step is a **30-query recall benchmark** against the actual
wiki — measure FTS5 top-5 recall on known-answer test cases before committing
to the replacement. If recall is above ~75%, bare FTS5 is confirmed
sufficient and no embeddings are needed.

The prior decision ([[qmd-patch-durability-strategy]]) to patch rather than
fork was correct at the time (the FTS5 escaping bug was not yet understood).
Now that the bug is understood and the fix is simple (per-token quoting), the
replacement is lower-risk than continued patching.

**Confidence: [HIGH]** — Karpathy's independent confirmation + sqlite-vec
escape hatch + our own qmd bug experience form a three-source convergence.

---

## Track E: Instruction budget (AGENTS.md refactor effectiveness)

### What we investigated

Whether reducing AGENTS.md from 992 lines to ~300 lines would actually
improve instruction-following, or whether frontier models handle long
instruction sets fine.

### Findings

1. **"Curse of Instructions" (ICLR 2025) — multi-instruction compliance
   degrades non-linearly.** Harada et al. showed LLMs "unexpectedly struggle
   to follow all instructions simultaneously as the number of instructions
   increases." Per-instruction compliance stays high individually, but joint-
   following accuracy collapses when many instructions are present. This is
   the most cited direct evidence against long instruction sets. [HIGH —
   peer-reviewed ICLR paper]

2. **"Lost in the Middle" is real and well-replicated (5,363 citations).**
   Liu et al. (2023, TACL 2024) showed performance degrades when relevant
   information is in the middle of the context. Middle-of-context rules are
   retrieved/attended to less reliably than beginning/end. [HIGH — canonical
   reference, heavily replicated]

3. **HumanLayer measured ~3% success-rate drop + >20% cost increase when
   AGENTS.md bloats.** This is the empirical basis for the 150-200 instruction
   recommendation. Multiple practitioner sources converge on the same band:
   150-300 lines, 150-200 instructions. [HIGH — HumanLayer research +
   practitioner consensus across 5+ sources]

4. **Progressive disclosure is empirically endorsed.** Multiple sources argue
   that revealing rules only when triggered improves compliance because the
   agent isn't simultaneously juggling competing instructions. An arxiv paper
   (2607.04576) validates the pattern for LLM-maintained wikis specifically.
   [HIGH — multiple sources including academic validation]

### Disconfirmation qualification

Claude's own system prompt is a 4000-word, five-layer stack that works fine —
suggesting structure matters more than raw length. But those 4000 words are
carefully structured (five layers) and tested by Anthropic, which is different
from an unstructured 992-line AGENTS.md. The refined conclusion: **shorter is
better, but structured-long may also work.** The 992-line AGENTS.md is neither
short nor well-structured (it's accumulated rules without a clear hierarchy).
**Qualified, not refuted.**

### What this means for our workspace

The AGENTS.md refactor handoff (`agents-md-refactor-20260727`) is the right
direction. The target (~300 lines with wikilinks to rationale) is well within
the reliable-compliance band. The key insight from the disconfirmation: the
refactor should also **add structure** (clear sections, priority ordering),
not just reduce length. Rules at the beginning of the file are followed more
reliably than rules at the end — so the most critical rules (verification,
edit-then-verify, no destructive git) should be at the top.

The existing wiki concept [[agents-md-construction-best-practices]] already
documents the progressive disclosure principle. The refactor implements it.

**Confidence: [HIGH]** — Curse of Instructions + Lost in the Middle +
HumanLayer measurement + practitioner consensus form a four-source convergence.

---

## Track F: Operator-as-backstop (mechanical enforcement ceiling)

### What we investigated

Whether there is a ceiling to mechanical enforcement (hooks) before hooks
become the bottleneck — conflicts, false positives, latency, maintenance
burden.

### Findings

1. **The constraint is synchronous latency per tool call, not hook count.**
   Each PreToolUse/PostToolUse/Stop hook runs synchronously; total hook
   execution time adds to every tool call. Above a few hundred ms of
   accumulated hook latency per tool call, the agent feels slow enough to
   route around the system. [HIGH — Claude Code hooks documentation +
   practitioner analysis]

2. **False-positive fatigue sets in above ~10-20% false-positive rate.**
   Once the FP rate exceeds this threshold, developers begin treating every
   gate output as noise. Each new hook must justify its false-positive budget
   against the existing cumulative rate, not just against its individual
   accuracy. [HIGH — well-established alarm-fatigue pattern across security,
   CI/CD, and medical alerting literature]

3. **Practitioners suggest 3-7 well-targeted hooks outperform 15-20 broadly-
   scoped ones.** Quality (target FP rate, blocking precision) matters more
   than quantity. The ceiling is reached when (a) cumulative latency becomes
   user-visible, (b) false-positive rate exceeds tolerance, (c) hooks
   disagree with no negotiation mechanism, or (d) the operator's mental model
   of "what's currently enforced" diverges from reality. [MEDIUM —
   practitioner consensus, no controlled experiment on hook count specifically]

4. **Hook conflict creates runtime deadlocks with no negotiation mechanism.**
   A PreToolUse exit-2 block is final — the call is rejected regardless of
   model intent. When two hooks have overlapping but not identical conditions,
   one may pass while the other blocks, and the agent has no negotiation
   mechanism. This is structurally different from prose rules, where
   contradictions can be reasoned about. [HIGH — Claude Code hooks reference]

5. **The enforcement surface must be continuously visible.** The fourth
   ceiling criterion — mental-model divergence — is the most often missed.
   The operator must be able to see what hooks are actually firing at any
   given time. Our `active-surface.last.md` snapshot (generated at SessionStart)
   is the right mechanism, but it must be kept current if config changes mid-
   session. [INFERENCE — no external source addresses this specifically, but
   it follows from the general observability principle in distributed systems]

### What this means for our workspace

The mechanical-enforcement-over-behavioral-reminder pattern
([[mechanical-enforcement-over-behavioral-reminder]]) is correct, but it has
a ceiling. The workspace should:

1. **Audit current hook count and latency.** Count active hooks per event
   (PreToolUse, PostToolUse, Stop) and measure cumulative latency per tool
   call. If above ~200ms, consolidate or parallelize.
2. **Tag each hook with a false-positive budget.** Before adding a new hook,
   declare its expected FP rate and how it combines with existing hooks.
3. **Prioritize hooks by criticality.** Verification-receipt hooks and
   destructive-git guards are critical (block). Language checks and style
   enforcement are advisory (warn, don't block).
4. **Keep the active-surface snapshot current.** Re-run the snapshot generator
   when config changes mid-session.

**Confidence: [HIGH]** — the latency constraint and alarm-fatigue pattern are
well-established; the specific hook-count recommendation (3-7) is [MEDIUM]
but directionally correct.

---

## Cross-cutting pattern: "thin layer over existing substrate"

Every track converges on the same architectural principle:

| Track | "Replace substrate" option | "Thin layer" option | Winner |
|-------|---------------------------|---------------------|--------|
| A | Skill dependency graph | Runtime context matching | Thin layer |
| B | Multi-format receipt parser | Policy schema over existing receipts | Thin layer |
| C | agentmemory / mem0 | /dream async consolidator over handoffs | Thin layer |
| D | Embeddings database | Bare FTS5 wrapper (sqlite-vec as escape hatch) | Thin layer |
| E | Rewrite AGENTS.md from scratch | Progressive disclosure (wikilinks to rationale) | Thin layer |
| F | More hooks | Audit + prioritize existing hooks | Thin layer |

This convergence is not coincidence. The workspace's substrates (handoffs,
wiki, qmd, AGENTS.md, hooks) are already well-designed for their individual
purposes. The failure modes are at the **integration layer** — how the
substrates connect, not whether each substrate is the right tool. Adding thin
integration layers (runtime matching, policy schema, async consolidator, bare
wrapper, progressive disclosure, hook audit) addresses the integration gaps
without disrupting the substrates that work.

This pattern mirrors the [[mechanical-enforcement-over-behavioral-reminder]]
principle applied at the system level: the fix for integration gaps is a thin
mechanical layer (code that runs deterministically), not a behavioral rule
("remember to check the other system").

---

## Investment priority ranking

Based on evidence strength × impact × effort:

1. **Track E (AGENTS.md refactor)** — [HIGH confidence, HIGH impact, MEDIUM
   effort]. The Curse of Instructions evidence is strong; the impact on every
   session is systemic; the refactor is already scoped in the handoff. **Do
   first.**

2. **Track D (qmd → bare FTS5)** — [HIGH confidence, MEDIUM impact, LOW
   effort]. Karpathy's independent confirmation + our own bug experience.
   Run the 30-query recall benchmark first, then replace. **Do second.**

3. **Track B (multi-source receipts with policy schema)** — [HIGH confidence,
   HIGH impact, MEDIUM effort]. The in-toto/SLSA pattern is proven; the
   policy schema is the missing piece. Resolves the Stop hook loop that
   cost ~10 turns this session. **Do third.**

4. **Track F (hook audit + prioritization)** — [HIGH confidence, MEDIUM
   impact, LOW effort]. Audit current hooks, measure latency, tag FP budgets.
   Quick win that prevents future enforcement ceiling. **Do fourth.**

5. **Track A (skill recommendation hook via runtime matching)** — [MEDIUM
   confidence, MEDIUM impact, HIGH effort]. The design exists; the
   implementation is unstarted. Runtime matching avoids the static-graph
   decay problem. **Do fifth — after the higher-priority tracks.**

6. **Track C (/dream async consolidator)** — [HIGH confidence, MEDIUM impact,
   HIGH effort]. agentmemory is Windows-incompatible; /dream is the right
   alternative. But /dream is a new skill that needs design + implementation.
   **Do last — the handoffs+wiki substrate works today; /dream improves it
   but isn't blocking.**

---

## Falsifiers

This investigation is wrong if:

- **Track A:** a production-grade skill graph tool emerges that works on Grok
  Build and demonstrably reduces cognitive load (measured by fewer missed
  skill invocations). Until then, runtime matching is the safer bet.
- **Track B:** the policy schema adds more friction than the false positives
  it prevents (measured by hook-loop count before and after). If hook loops
  increase, the schema is wrong.
- **Track C:** the Letta filesystem benchmark doesn't replicate on our corpus
  (measured by recall on our actual handoffs+wiki). If recall is below 50%,
  a dedicated memory system becomes necessary.
- **Track D:** the 30-query recall benchmark shows FTS5 below 75% top-5 recall
  on our wiki. If so, sqlite-vec + embeddings is the fallback.
- **Track E:** after the refactor, instruction-following doesn't improve
  (measured by operator-correction count per session). If corrections don't
  decrease, the length wasn't the problem — structure was.
- **Track F:** the hook audit reveals we're already below the ceiling (under
  7 hooks, under 200ms latency, under 10% FP rate). If so, the ceiling
  concern is theoretical and no action is needed.

---

## Receipts

- **Phase 1 wiki query:** `grep` across `P:/.data/wiki/concepts/` for all 6
  track keywords (skill wiring, verification receipts, agentmemory, qmd/FTS5,
  instruction budget, mechanical enforcement). 6 DiffusionGemma batch reads +
  4 direct reads. All found relevant existing concepts.
- **Phase 2 parallel subagents:** 6 M3 subagents dispatched in parallel
  (IDs: 019fa6ca-c477 through c47b), each running 8-14 tool calls over 56-110s.
  All 6 completed successfully. Wait-all gate passed.
- **Phase 2 disconfirmation:** 3 minimax-search queries against the highest-
  stakes conclusions (Track C, D, E). Track D confirmed (Karpathy llm-wiki);
  Track C and E qualified but not refuted.
- **Wiki contradiction check:** no contradictions found with existing concepts.
  All conclusions consistent with `llm-dreaming-memory-consolidation`,
  `qmd-patch-durability-strategy`, `agents-md-construction-best-practices`,
  `mechanical-enforcement-over-behavioral-reminder`.
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
