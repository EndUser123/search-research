---
title: "Triage/discovery architecture: convergent validity between independent proposal and workspace-validated principles"
created: 2026-08-07
source: session-2026-08-07-www
tags: [triage, discovery, finding-lifecycle, multi-agent, evidence-anchoring, risk-scoring, mcp, architecture, convergent-validity]
summary: >
  Evaluated a ChatGPT-produced architecture proposal for an LLM triage/discovery
  system (finder→triage→TODO→MCP pipeline, challenged by a counter-proposal of
  one-lifecycle-with-stage-contracts → immutable evidence → validated index →
  user-authorized promotion → verified execution). The counter-proposal's core
  principles are STRONGLY CORROBORATED by workspace-validated research: the
  workspace has independently arrived at the same conclusions (orthogonal
  severity×confidence, anti-premature-agentization, self-correction limits,
  MCP-as-adapter). Both arxiv citations are real. The convergence itself is
  evidence the principles are robust. Three workspace-specific refinements
  tighten the proposal: (1) promote idempotency/stale-state to Phase 1, not
  Phase 2; (2) apply the trust-escalation authority model, not blanket
  user-promotion; (3) name the pipeline-agentization vs adversarial-multi-model
  distinction explicitly.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
confidence: 0.85
last_verified: 2026-08-07
half_life_days: 180
relations:
  - target: wiki/concepts/skill-techniques-index.md
    type: supports
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md
    type: supports
  - target: wiki/concepts/multi-agent-coordination-failure-modes-practitioner-and-research-2026.md
    type: supports
  - target: wiki/concepts/agentic-self-correction-and-context-management.md
    type: supports
  - target: wiki/concepts/confidence-scoring-for-static-analysis-fp-suppression.md
    type: refines
  - target: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md
    type: related
---

# Triage/discovery architecture: convergent validity evaluation

## Decision context

**Why this research was needed:** the operator received a ChatGPT architecture
proposal (`C:\Users\brsth\Downloads\Architecture-I-would-implement.md`) for an
LLM triage/discovery system and asked: "does this solution make sense?" The
document is itself a critique of an earlier proposal (a finder→triage→TODO→MCP
multi-agent pipeline) and recommends instead a single evaluable triage lifecycle
with explicit stage contracts, immutable evidence artifacts, a validated finding
index, user-authorized task promotion, and verified execution. The real question
behind the request: are these architectural principles sound, and where does
this workspace's hard-won experience refine or contradict them?

**What the research changed:** confirmed the counter-proposal is architecturally
sound and aligns with workspace-validated principles; surfaced three refinements
that tighten it for this fleet's specific failure history.

## Key findings

### Claim-by-claim verification (each independently checked)

| # | Document claim | Verification | Confidence | Receipt |
|---|---|---|---|---|
| 1 | Discover-first, classify-second beats category-bounded discovery | SUPPORTED (anchoring research supports the principle; specific workflow = by-analogy) | MEDIUM | arXiv:2505.15392; Springer 2025; IEEE 2025 |
| 2 | Impact × confidence is wrong; use routing rules with orthogonal dimensions | STRONGLY SUPPORTED — workspace already validated | HIGH | [[skill-techniques-index]] §severity-vs-confidence; [[confidence-scoring-for-static-analysis-fp-suppression]] |
| 3 | Orthogonal taxonomy (kind/impact/cause/disposition/relations) beats mixed categories | SOUND — aligns with FMEA + static-analysis convention | MEDIUM-HIGH | [[fmea]] skill; pylint/pyright/vulture tiered-confidence convention |
| 4 | Don't build 3 separately-deployed agents; one pipeline with stage contracts | SUPPORTED for the triage domain | HIGH | [[multi-agent-coordination-failure-modes-practitioner-and-research-2026]] ("offensively simple" for triage); [[delegation-optimization-chunking-output-backend-discipline]] (coordination cost quadratic) |
| 5 | MCP is an adapter, not the solution; stdio is per-client, shared needs Streamable HTTP | CONFIRMED — factual claim verified against spec | HIGH | modelcontextprotocol.io spec; Truefoundry; IBM Bob |
| 6 | Self-reported bias metrics are output telemetry, not bias proof; LLM self-correction is mixed | STRONGLY SUPPORTED | HIGH | [[agentic-self-correction-and-context-management]]; Self-Correction Bench (arXiv:2507.02778, 64.5% blind spot); arXiv:2606.23196; Huang et al. ICLR 2024 |
| 7 | SQLite WAL lifecycle index + immutable evidence files (CQRS-like) | SOUND — established pattern | HIGH | sqlite.org/wal.html; standard event-sourcing/CQRS |
| 8 | Both arxiv citations (2606.23196, 2607.20526) | REAL — not fabricated | HIGH | DDG + arxiv abstract pages verified this session |

### The convergence finding (the non-obvious takeaway)

The remarkable result: an independently-produced ChatGPT proposal re-derives
principles this workspace arrived at through its own research and incidents —
orthogonal severity×confidence, anti-premature-agentization, the limits of LLM
self-correction, MCP-as-adapter-not-solution. This **convergent validity** is
itself evidence the principles are robust (they survive independent derivation
from different starting points). The document is not novel relative to the
workspace; it is a faithful re-statement of workspace-validated architecture
applied to the triage/finding domain.

### Disconfirmation pass (what could be wrong)

The multi-agent picture is **contested in 2026**, not settled: Anthropic's data
shows multi-agent Claude at 72% vs 48% single-agent on SWE-bench; the Agyn paper
(arXiv:2602.01465) shows multi-agent winning on SWE tasks. This *refines* rather
than *overturns* the document: multi-agent wins for **parallelizable cognitive
labor and adversarial review**, but the document is correct that **pipeline-stage
agentization** (finder→triage→TODO as separate deployed agents) is premature.
Crucially, "The Case Against Multi-Agent Frameworks (2026)" explicitly states one
agent is "often enough for **support triage**" — the document's exact domain. The
document already hedges correctly ("different models can execute selected stages
when useful"), so the disconfirmation does not invalidate it.

## Workspace-counterexample check

- Routing-rules-over-blended-score: no counterexample — [[skill-techniques-index]] and [[confidence-scoring-for-static-analysis-fp-suppression]] confirm.
- Anti-multi-agent-for-triage: no counterexample — [[multi-agent-coordination-failure-modes-practitioner-and-research-2026]] confirms "offensively simple" for triage specifically.
- Self-correction-limits: no counterexample — [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]] confirms pure self-evaluation doesn't catch performative compliance.

## Three workspace-specific refinements (where experience tightens the proposal)

1. **Promote idempotency/stale-state to Phase 1.** The document defers idempotency keys + concurrent-client tests to Phase 2. This workspace's incident history (stale `DevToolsActivePort`, duplicate prompt submission, concurrent-write collisions, stale-reference propagation) shows concurrent-state integrity is where ~80% of the pain lives. Start it in Phase 1, not Phase 2.

2. **Apply the trust-escalation authority model.** The document treats "user promotion" as the single authority gate. This workspace operates a runged trust ladder (auto-commit at Rung 1, auto-escalation at Rung 2-3, operator-invoked close at Rung 4). Map the proposal's "promotion" step onto the existing authority rungs rather than inventing a parallel gate.

3. **Name the pipeline-agentization vs adversarial-multi-model distinction.** The document implies but does not state the key distinction: pipeline-stages-as-separate-deployed-agents (premature, high coordination cost) vs adversarial/parallel-multi-model-verification (evidence-backed, recommended). Making this explicit prevents a future reader from over-generalizing "don't use multi-agent."

## Falsifier

This evaluation (and the document) is wrong if a measured eval on this workspace's
real session/finding corpus shows: (a) discover-first does NOT improve recall over
category-bounded discovery, OR (b) a multi-agent triage pipeline measurably
outperforms the single-lifecycle-with-stage-contracts design on this fleet's actual
workload. Until such an eval runs, the architecture is [SUPPORTED] but [UNTESTED]
on this workspace — the document itself correctly calls for this acceptance evidence.

## Provenance

Evaluated via `/www` (wiki→web→wiki). Phase 1: search_wiki + grep across 990+
concepts surfaced 6+ directly-validating concepts. Phase 2: DDG verified both
arxiv citations (real), the MCP transport claim (per spec), the discover-first
principle (anchoring research), and a disconfirmation pass on the multi-agent
question. No prior www-ledger entry on triage/discovery/finding-lifecycle — this
is a fresh research thread.

Sources: arXiv:2505.15392 (anchoring), arXiv:2507.02778 (Self-Correction Bench),
arXiv:2606.23196 (intrinsic self-correction), arXiv:2607.20526 (ConfidenceBench),
arXiv:2602.01465 (Agyn), modelcontextprotocol.io (transports), sqlite.org/wal,
"The Case Against Multi-Agent Frameworks" (alatirok.com, 2026), Anthropic agentic
coding trends (udit.co).
