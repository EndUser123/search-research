# `research-run.v1` Phase 2A evaluation

Observed: 2026-07-13. This is the Phase 2A experiment only; Phase 1 policy was treated as an accepted baseline and was not reimplemented.

## Decision and scope

The experiment asked whether bounded, claim-specific disconfirmation improves eight consequential prior research decisions. Each case was compared in two modes:

1. affirmative-only: the existing Phase 1E baseline action;
2. affirmative plus two bounded falsifier searches, one through MMX and one through Brave, with QMD context, source opening, assessment, and claim-status reconciliation.

No new provider was added and `agy` was not invoked. The corpus contains eight cases and sixteen applicable falsifiers. Each falsifier has a decision-specific statement, query, relevance, evidence terms, claim-specific anchor terms, contradiction terms, and intended decision effect. Generic ceremonial risks were rejected by the contract and were not run.

## Minimal Phase 2A contract change

`tools/research_run_v1/phase2a.py` adds only the fields needed by this experiment:

- falsifier: `falsifier_id`, `claim_id`, `statement`, `query`, `decision_relevance`, `evidence_terms`, `anchor_terms`, `contradiction_terms`, and `outcome`;
- reconciliation: `claim_id`, `original_action`, `revised_action`, `outcome`, `changed`, `basis_falsifier_ids`, `noisy_falsifier_ids`, `false_contradiction_count`, `additional_evidence_required`, and `limitation`.

An apparent contradiction is `anchor_confirmed` in substance: it requires a claim-specific anchor, at least two evidence terms, and a contradiction term in an opened source. A broad contradiction word without the anchor is counted as noisy/false contradiction evidence, not as a general `verified` result.

## Case comparison

| Case | Affirmative-only action | After bounded disconfirmation | Reconciliation |
|---|---|---|---|
| maintained-agentic-repositories | `continue_targeted_use` | `continue_targeted_use` | survived |
| feature-implementation-evidence | `continue_targeted_use` | `continue_targeted_use` | survived |
| windows-lifecycle-defects | `continue_targeted_use` | `continue_with_explicit_guardrail` | added tests/guardrails |
| official-source-comparison | `continue_targeted_use` | `do_not_authorize_broader_use` | reduced authorization |
| abandoned-library | `continue_targeted_use` | `gather_more_evidence` | required more evidence |
| authoritative-missed-source | `require_more_evidence` | `continue_only_with_primary_verification` | reduced confidence |
| insufficient-evidence | `require_more_evidence` | `gather_more_evidence` | required more evidence |
| implementation-not-concept | `continue_targeted_use` | `continue_targeted_use` | survived |

Aggregate reconciliation: 3 survived; 1 added tests/guardrails; 1 reduced authorization; 1 reduced confidence; 2 required more evidence; 0 narrowed scope; 0 rejected the conclusion. Five of eight decisions changed action or authorization.

## Measured burden and quality

- total wall time: 109,494 ms (about 109.5 s);
- disconfirmation search wall time: 18,310 ms;
- additional opened sources: 27;
- source-opening failures: 3;
- additional source-opening time: 20,115 ms;
- noisy falsifiers: 5/16;
- false-contradiction hits: 8;
- known top-level MMX falsifier calls: 8; the paired Brave calls were bounded in parallel with them;
- QMD context was executed once per case through the existing path.

False contradictions were not silently discarded: they were retained in each case record and excluded from the direct contradiction basis unless the claim-specific anchor and evidence conditions also held. The main noisy patterns were generic “fixed/resolved/unrelated” language, broad sources unrelated to the exact claim, and one source-open failure. The experiment therefore measured disconfirmation value, but also demonstrated that lexical assessment is not authoritative source interpretation.

MMX readiness was `ready` before and after. The shared interval moved from 49% to 48% and weekly remained 100%; because this account may have concurrent consumers, the artifact explicitly marks attribution as indeterminate and does not claim that this run consumed the one-percent delta.

## Evidence and authorization

The live artifact is [phase2a-evaluation.json](P:/tmp/.codex/state/phase2a-evaluation-20260713/phase2a-evaluation.json). It preserves per-case queries, provider status, opened sources, source-opening failures, anchor/evidence/contradiction counts, assessments, claim status, reconciliation, and timing.

The result is `PASS_TARGETED_DISCONFIRMATION`: bounded disconfirmation changed five of eight actual actions or authorization levels and added concrete guardrails or evidence requirements, with a measurable but bounded latency/opening cost. This is not authorization for unbounded disconfirmation. The next permitted use is targeted disconfirmation only for consequential decisions where a specific falsifier can change the action; generic risk lists and broad contradiction matching remain disallowed.

## Limitations and untouched areas

The reference evaluator uses deterministic lexical rules over opened source text. It does not prove factual truth, backend identity, source completeness, or semantic contradiction. The experiment did not invoke `agy`, add a provider, test production routing, or establish a universal cost model. MMX quota attribution remains unknown under concurrent use. The source-authority audit found no active Phase 2 owner; its `needs_review` result reflects the existing implementation/evaluator naming overlap, not an authorization to treat historical reports as current authority.

Verification attempted: `python -m py_compile` passed for the Phase 2A modules; the live evaluator completed and validated all eight records. The focused pytest command could not run in the current Python environment because that environment has no installed `pytest` module.
