---
title: "Skill-step receipts checked by hooks: per-step evidence-gated lifecycle control"
created: 2026-07-27
source: session-019fa276 (/www on receipt-checked skill steps + Proof-or-Stop research)
tags: [receipt, skill-enforcement, stop-hook, mandatory-step, closure-pressure, evidence-gating, proof-or-stop, per-step-receipt, source-state-binding, micro-scale]
summary: >
  REVISED: the load-bearing design choice is one receipt per step (not
  per skill), each carrying what that step actually produced. Per-skill
  receipts catch "didn't do it at all"; per-step receipts catch "did it
  badly" by requiring step-specific evidence (e.g., Phase 2 receipt must
  include disconfirmation_queries > 0). The Proof-or-Stop paper (arxiv
  2607.14890, Jul 2026) validates this empirically: a 9,240-cell powered
  ablation showed evidence-gated lifecycle control reduces visible-pass/
  hidden-fail amplification from 1.72% to 0.11% (15x reduction) while
  costing only 1.2x more tokens. The key comparison: same review signal,
  advisory vs enforced — enforcement is what made the difference (14
  amplified vs 2). Our wiki_state.py already implements a simplified
  version; the gap is source-state binding (materialHash), per-step
  output digests, and gate predicates per step.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - "https://arxiv.org/html/2607.14890v1" (Proof-or-Stop, Huang et al., Jul 2026 — powered 9,240-cell ablation)
  - "P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md" (foundational principle)
  - "P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md" (micro-scale gap)
  - "P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md" (visible output for silent steps)
  - "P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md" (receipts prove "ran" not "correct" — partial limitation, addressed by per-step evidence)
  - "P:/.data/wiki/concepts/wiki-lifecycle-state-file.md" (existing per-step state tracking)
  - "P:/.data/wiki/concepts/fabrication-ceremony-tax-compounding-cost.md" (ceremony cost)
  - "P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md" (existing hook infrastructure)
  - "https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/" (IETF agent audit trail draft, Mar 2026)
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: applies
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: implements
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: extends
  - target: wiki/concepts/lexical-vs-semantic-verification-gap.md
    type: partially_resolves
---

# Skill-step receipts checked by hooks: per-step evidence-gated control

## Decision context

**Why this analysis was needed:** during this session, the agent invoked
`/www` twice and both times skipped Phase 3 (persist to wiki), asking
"want me to persist?" instead of doing it. The operator asked whether a
hook that checks for skill-step receipts would catch this automatically.

**What changed during research:** the operator corrected the initial
framing — "are you assuming one receipt per skill? rather than one per
generation step, verification step, discovery step?" This correction was
load-bearing. Research then found the Proof-or-Stop paper (arxiv
2607.14890, July 2026), which formalizes and empirically validates exactly
the per-step evidence-gated pattern.

## The core design choice: per-step receipts, not per-skill

### Why per-step granularity matters

A per-skill receipt (`{completed: true}`) only catches "didn't do it at
all." A per-step receipt, each carrying step-specific evidence, catches
"did it badly":

| Step | Per-skill receipt | Per-step receipt (what we need) |
|---|---|---|
| Phase 1: query | `{skill: "www", completed: true}` | `{phase: 1, concepts_found: 5, gaps: 3, assumptions_to_check: 2}` |
| Phase 2: research | (same blob) | `{phase: 2, sources_cited: 4, disconfirmation_queries: 2, shape: "dos-and-donts"}` |
| Phase 3: persist | (same blob) | `{phase: 3, concept_path: "...", validation: "PASS", lines: 85}` |

With per-step receipts, the hook checks a **chain of evidence**, not just
file existence. "Phase 2 ran but `disconfirmation_queries: 0`" catches
"skipped the mandatory sub-step," which a per-skill receipt cannot.

### The lexical-to-semantic bridge

Per [[lexical-vs-semantic-verification-gap]], receipts prove "ran" not
"correct." But per-step receipts with step-specific content **partially
resolve this gap**: a Phase 2 receipt that shows `disconfirmation_queries:
0` is a semi-semantic signal (the disconfirmation step was structurally
skipped), not just a lexical one (a file exists). It's not full semantic
verification (the queries might be bad), but it's substantially stronger
than "a wiki concept file was created."

## Empirical validation: Proof-or-Stop (arxiv 2607.14890, July 2026)

The Proof-or-Stop paper formalizes this pattern as **evidence-gated
lifecycle control** with the thesis: **"Don't trust the agent, trust the
evidence."** Every lifecycle claim (tested, reviewed, done) is a *claim*;
the lifecycle advances only when fresh, structured, source-state-bound
evidence satisfies a *gate predicate*.

### What each receipt contains

| Receipt field | What it proves |
|---|---|
| `materialHash` | Bound to the exact source state at time of evidence |
| `headHash` | Git commit identity |
| `cmd`, `args`, `exit`, `outputDigest` | The actual command, its exit code, output hash |
| `reviewer identity`, `lane`, `round` | Who reviewed, in which lane, which round |
| `policyHash`, `commandSetHash` | Exact policy/command configuration in effect |

When the source tree changes, prior receipts become **stale** (their
`materialHash` no longer matches) — auto-rejected. This freshness binding
prevents "the receipt exists but it's from before I changed the code."

### Powered ablation result (9,240 cells)

| Control loop | Amplified (shipped wrong) | Tokens |
|---|---|---|
| Prompt-only (no loop) | 13/1,440 (0.90%) | 168K |
| Naive retry (blind ×3) | 18/1,800 (1.00%) | 169K |
| Compute-budgeted naive | 31/1,800 (1.72%) | 170K |
| Review-only (**advisory**) | 14/1,800 (0.78%) | 200K |
| **Proof-or-Stop (enforced)** | **2/1,800 (0.11%)** | 204K |

**Key comparison (A3 vs A4):** same review signal, nearly same cost
(200K vs 204K tokens), but advisory review amplified 14 cells while
enforced review amplified 2. **The enforcement of the gate — not the
review itself — is what made the difference.** H1 not-amplified +1.6pp
[0.8, 2.5], CI excludes zero.

### What this means

- The pattern **works empirically**, not just in theory. 15x reduction in
  visible-pass/hidden-fail amplification at 1.2x token cost.
- The **enforcement** (gate blocks advancement) is the mechanism, not the
  evidence itself. Advisory evidence (A3: review runs but doesn't block)
  provides minimal improvement over naive retry.
- The paper is **honest about boundaries**: "proof" = gate-admissible
  evidence under a stated trust model, NOT semantic correctness. Receipts
  prove the step ran with the right inputs and outputs; they do not prove
  the step was semantically correct.

## What we already have vs what we need

| Component | Our status | Proof-or-Stop equivalent | Gap |
|---|---|---|---|
| Per-step state tracking | ✅ `wiki_state.py`: `discovered → ingesting → linking → linting → complete` | Lifecycle phases with gate predicates | We track phases; we don't gate transitions |
| Code-change receipts | ✅ `verification_receipt_writer.py` + `quality_gate.py` | Receipt identity (cmd, args, exit, outputDigest) | We have receipts for code changes, not skill steps |
| Source-state binding | ❌ Missing | `materialHash` / `headHash` freshness | Stale receipts not auto-rejected |
| Per-step output content | ❌ Missing | Step-specific evidence (queries run, sources cited, etc.) | We check "file exists" not "step produced evidence" |
| Gate predicates per step | ❌ Missing | `Admissible(E, c, H)` — multi-conjunct check per claim | No predicate beyond "file exists" |
| Micro-scale accounting | ⚠ Partial — `close_accounting.py` | `__lib/<skill>_accounting.py` per skill | Close has it; other skills don't |

## Implementation path (revised from the operator's correction)

### The right design: per-step receipts with gate predicates

For each skill with mandatory steps, define a receipt schema:

```json
{
  "skill": "www",
  "session": "<session_id>",
  "step": "phase2_research",
  "evidence": {
    "sources_cited": 4,
    "disconfirmation_queries": 2,
    "wiki_contradictions_checked": true,
    "shape": "dos-and-donts"
  },
  "source_state": {
    "head_hash": "<git HEAD>",
    "timestamp": "<ISO>"
  },
  "gate_predicate": "sources_cited >= 2 AND disconfirmation_queries >= 1"
}
```

The Stop hook reads `.artifacts/<session>/skill-receipts/` and checks each
receipt's `gate_predicate` against its `evidence`. If any receipt's
predicate evaluates false, block with the specific failed step + predicate.

**Stale detection:** if `head_hash` doesn't match current HEAD, the receipt
is stale (the skill ran before a code change). Mark as `needs_rerun`.

### Which skills to instrument first

Per the ceremony-cost analysis ([[fabrication-ceremony-tax-compounding-cost]]):

| Skill | Critical step | Receipt evidence | Gate predicate | Priority |
|---|---|---|---|---|
| `/www` | Phase 3 persist | `concept_path`, `validation` | `concept_exists AND validation == "PASS"` | ✅ NOW (2 skips this session) |
| `/www` | Phase 2 disconfirmation | `disconfirmation_queries` | `disconfirmation_queries >= 1` | ✅ NOW |
| `/handoff` | Write file | `handoff_path`, `bytes_written` | `file_exists AND bytes > 500` | ✅ NOW (observed non-writes) |
| `/check` | Verify claims | `claims_checked`, `claims_passed` | `claims_checked >= 1` | ✅ NOW |
| `/wiki` | Validate | Already enforced by `wiki_state.py` | — | ✅ DONE |
| `/red-team` | Root-cause clustering | `findings_clustered` | `findings_clustered >= 1` | ⚠ Later |
| `/close` | All gates | Already enforced by `close_accounting.py` | — | ✅ DONE |

### Cost estimate

- ~15 lines per skill step (receipt writer) — the skill writes the receipt
  as it completes each step, using the same pattern as `wiki_state.py`
- ~40 lines for the Stop hook extension — reads all receipts, evaluates
  predicates, blocks on failure with specific step + reason
- Zero additional dependencies — pure Python, file-based
- Runtime cost: ~5ms per Stop event (read N small JSON files + eval predicates)

## Receipts

- **"Proof-or-Stop reduces amplification 15x":** receipt —
  [arxiv.org/html/2607.14890v1](https://arxiv.org/html/2607.14890v1), Table 11:
  A4 amplified 2/1800 vs A2' 31/1800. H1 not-amplified +1.6pp [0.8, 2.5].
- **"Enforcement (not review) is the mechanism":** receipt — same table,
  A3 (review-only, advisory) amplified 14/1800 vs A4 (enforced) 2/1800 at
  nearly identical token cost (200K vs 204K).
- **"wiki_state.py already does per-step tracking":** receipt —
  [[wiki-lifecycle-state-file]] documents the `discovered → ingesting →
  linking → linting → complete` state machine with `wiki_ingest.py`
  refusing exit-0 on lifecycle tracking failure.
- **"close_accounting.py is the micro-scale reference":** receipt —
  [[code-orchestrates-model-judges-skill-scale]] line 91: "Skill's
  __lib/*.py gates the LLM through mandatory steps."
- **"/www Phase 3 skipped twice this session":** receipt — this session's
  transcript; operator corrected: "I used the /www skill, thus it should
  have already been persisted."
- **"IETF agent audit trail draft":** receipt —
  [datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/](https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/)
  (March 2026).

## Falsifier

Per-step receipt checking is over-engineering if:
- **The step-skip rate is low.** Observed: `/www` Phase 3 skipped 2/2 times
  this session. Not low.
- **Enforcement doesn't help beyond advisory.** Proof-or-Stop ablation
  disproves this: A3 (advisory) amplified 14 cells; A4 (enforced) amplified
  2. Enforcement is the mechanism.
- **The ceremony cost exceeds value.** Testable: track false-positive blocks
  vs real-skip catches over 3 months. Ratio <1:3 → retire.
- **Source-state binding is unnecessary.** Testable: does a skill step ever
  produce stale receipts that pass without binding? If the skill writes the
  receipt immediately after the step, staleness is unlikely within a single
  session. Cross-session staleness (resume from prior session) is the real
  risk — and that's where binding earns its cost.

## Sources

- [Proof-or-Stop: Don't Trust the Agent, Trust the Evidence](https://arxiv.org/html/2607.14890v1)
  (Huang et al., Jul 2026) — evidence-gated lifecycle control with powered
  9,240-cell ablation. Open-source implementation with 565 stories / 1007
  findings.
- [IETF Agent Audit Trail draft](https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/)
  (Sharif, Mar 2026) — standard logging format for autonomous AI systems.
- `mandatory-step-enforcement-code-over-prose.md` — move enforcement from
  prose to code (foundational principle)
- `code-orchestrates-model-judges-skill-scale.md` — micro-scale gap
- `visible-output-contracts-for-behavioral-skill-steps.md` — silent steps
  need visible output
- `lexical-vs-semantic-verification-gap.md` — receipts prove "ran" not
  "correct" (partially resolved by per-step evidence content)
- `wiki-lifecycle-state-file.md` — existing per-step state tracking
- `fabrication-ceremony-tax-compounding-cost.md` — ceremony cost warning
- `grok-build-stop-hook-patterns-and-feedback-mechanism.md` — existing hook
  infrastructure

## Auto-related

- [[mandatory-step-enforcement-code-over-prose]] — the principle this implements
- [[code-orchestrates-model-judges-skill-scale]] — the micro-scale gap this fills
- [[visible-output-contracts-for-behavioral-skill-steps]] — visible output for silent steps
- [[lexical-vs-semantic-verification-gap]] — partially resolved by per-step evidence
- [[wiki-lifecycle-state-file]] — the existing pattern to extend
- [[fabrication-ceremony-tax-compounding-cost]] — the cost tradeoff
- [[systematic-problem-anticipation-methods-and-existing-tools]] — FMEA and formal methods for failure enumeration
