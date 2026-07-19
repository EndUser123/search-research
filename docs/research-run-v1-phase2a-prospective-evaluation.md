# Prospective provider-equivalent Phase 2A evaluation

Observed: 2026-07-14. This is a new prospective evaluation; it does not use the lost historical Phase 2A artifact as a controlled baseline and does not integrate any workflow.

## Evaluation identity and artifacts

- Evaluation namespace: `phase2a-prospective-evaluation-20260714-a78bb33f3b6e`
- Baseline run: `phase2a-prospective-baseline-20260714-a78bb33f3b6e`
- Candidate run: `phase2a-prospective-candidate-20260714-a78bb33f3b6e`
- Baseline manifest SHA-256: `8aa5cf03814ee523da6a0d7c4b8c16fce1fba7f980b59a9c5aa2b71603df1996`
- Candidate manifest SHA-256: `f41db43a25f8520aeef98a58f9309d53695b1a90938a622846c0361796981b8e`
- Comparison: `P:\tmp\.codex\state\immutable-evaluations\phase2a-prospective-evaluation-20260714-a78bb33f3b6e\comparison.json`

Each run is immutable and separately retained. The candidate binds each case's reused affirmative evidence to the baseline run ID, baseline manifest hash, and baseline case hash. The historical Phase 2A artifact remains explicitly unreconstructable.

## Corpus and trigger policy

Eight new agentic-coding cases were evaluated: repository adoption, Windows compatibility, runtime activation, native capability versus a new layer, production readiness, maintenance risk, process containment, and a low-impact official-page lookup.

Seven consequential cases were expected to trigger targeted disconfirmation; the low-impact reversible lookup was expected not to trigger. The trigger implementation derives only from impact, reversibility, and omission sensitivity. It does not read the expected result. Observed trigger precision and recall against the predeclared case criteria were both 100%: 7 expected/7 produced, 0 false positives, 0 false negatives.

## Provider equivalence

MMX, Brave, and QMD were used in both variants. MMX was ready with the same executable path and version (`mmx 1.0.16`); Brave was ready in both. The affirmative candidate portion reused the exact baseline evidence rather than repeating it. Candidate disconfirmation used 13 admitted falsifiers: 7 MMX and 6 Brave calls. QMD ran for the seven triggered candidate cases; the low-impact case reused baseline context.

| Dimension | Classification |
|---|---|
| Provider set | directly comparable |
| Corpus | directly comparable; equal corpus hash |
| Policy | directly comparable; equal policy hash |
| Affirmative query budget | directly comparable; candidate reuses baseline evidence |
| Result/source limits and timeouts | directly comparable by implementation |
| Live readiness/quota/timing | partially comparable |
| Search results and opened-source identities | partially comparable; live retrieval varies |

No Exa, DuckDuckGo, `agy`, or other provider was used.

## Case outcomes

| Case | Baseline action | Candidate action | Outcome |
|---|---|---|---|
| repository adoption | continue targeted use | continue targeted use | survived |
| Windows compatibility | continue targeted use | continue targeted use | survived |
| runtime activation | continue targeted use | continue only with primary verification | confidence reduced |
| native capability | require more evidence | require more evidence | survived unresolved state |
| production readiness | continue targeted use | do not authorize broader use | authorization reduced |
| maintenance risk | continue targeted use | continue targeted use | survived |
| containment lifecycle | continue targeted use | gather more evidence | more evidence required |
| low-impact lookup | continue targeted use | continue targeted use | survived; no trigger |

Three candidate actions materially changed: runtime activation, production readiness, and containment lifecycle. Four cases survived without action change, including the low-impact non-trigger case. No conclusion was rejected.

## Burden and safety signals

- Baseline: 12 opened sources, 3 provider/source failures, 106.6 seconds total.
- Candidate: 28 recorded opened sources, 0 provider/source failures, 129.6 seconds total.
- Candidate added 13 falsifier calls and approximately 23.0 seconds of aggregate case latency.
- Candidate produced 5 noisy falsifiers and 6 false-contradiction hits.
- All noisy/false hits were blocked from the direct contradiction basis; no false rejection or false authorization reduction was observed under the reference criteria.

The noise rate and partially variable live source results do not support automatic use. The production-readiness change also demonstrates why primary-authority requirements must remain a human/manual review boundary for now.

## Evidence authority

Reference criteria were authored in the prospective corpus before execution. Reconciliation used opened run-bound sources, deterministic anchor/evidence rules, authority classification, and the existing claim aggregation path. Candidate prose was not treated as gold truth. “No counterevidence found” remains bounded to the performed searches and source-opening budget.

## Verification

Canonical command:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `61 passed`.

Prospective command:

```text
python -m tools.research_run_v1.evaluate_phase2a_prospective
```

## Verdict and boundary

Verdict: `PASS_MANUAL_ONLY`.

Targeted disconfirmation retains repeatable decision value and correctly skips the low-impact case, but the observed noisy/false-contradiction burden and partially variable live source results do not justify a bounded automatic pilot. Keep it manual, advisory, read-only, and limited to consequential decisions with explicit human review of action-changing evidence.

Deferred: `/go` and `/search` integration, automatic routing, adaptive trigger learning, new providers, `agy`, and production use.
