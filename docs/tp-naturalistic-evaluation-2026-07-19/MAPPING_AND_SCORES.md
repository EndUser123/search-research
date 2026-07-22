# Prior Evaluation — Condition Mapping (recovered 2026-07-19)

**Source:** Recovered from session transcript into durable form.
**Original evaluation run:** 2026-07-19T19:18:00-06:00 (corpus frozen).

## Corpus hash
SHA-256 of `01_corpus.json`: `445bd38140887d7d67e1e75d282105ffb692f8473e37019c59c6aa7bc7199860`

## Condition-to-response-slot mapping (hidden from judges)

| Case | Response A = | Response B = |
|---|---|---|
| C01 | baseline | /tp |
| C02 | /tp | baseline |
| C03 | /tp | baseline |
| C04 | baseline | /tp |
| C05 | /tp | baseline |
| C06 | /tp | baseline |
| C07 | baseline | /tp |
| C08 | /tp | baseline |
| C09 | baseline | /tp |
| C10 | baseline | /tp |
| C11 | /tp | baseline |
| C12 | baseline | /tp |

Randomization was generated before response generation using an alternating-with-noise pattern (no judge saw the mapping).

## Per-case pairwise scores (unblinded after judging)

| Case | /tp score (/50) | Baseline score (/50) | Diff | Winner | Subagent IDs (baseline, /tp) |
|---|---|---|---|---|---|
| C01 | 28 | 37 | -9 | baseline | 019f7d19-810b (orig) / 019f7d1c-cfe7 (retry used); /tp: 019f7d1f-e8cc |
| C02 | 33 | 36 | -3 | baseline | baseline retry: 019f7d1c-cfe7; /tp: 019f7d1f-e8cd |
| C03 | 40 | 37 | +3 | /tp | baseline: 019f7d19-810c; /tp: 019f7d1f-e8ce |
| C04 | 42 | 35 | +7 | /tp | baseline: 019f7d19-810d; /tp: 019f7d1f-e8ce (2812 variant) |
| C05 | 38 | 27 | +11 | /tp | baseline: 019f7d19-810e; /tp: 019f7d1f-e8cf |
| C06 | 46 | 36 | +10 | /tp | baseline: 019f7d1c-cfe8 (retry); /tp: 019f7d1f-e8d0 |
| C07 | 38 | 31 | +7 | /tp | baseline: 019f7d19-8110; /tp: 019f7d1f-e8d0 (5410 variant) |
| C08 | 45 | 47 | -2 | baseline | baseline: 019f7d1c-cfe9 (retry); /tp: 019f7d1f-e8d1 |
| C09 | 44 | 35 | +9 | /tp | baseline: 019f7d19-8112; /tp: 019f7d1f-e8d2 |
| C10 | 44 | 45 | -1 | baseline | baseline: 019f7d1c-cfea (retry); /tp: 019f7d1f-e8d2 (dfc2 variant) |
| C11 | 46 | 41 | +5 | /tp | baseline: 019f7d19-8114; /tp: 019f7d1f-e8d3 |
| C12 | 47 | 39 | +8 | /tp | baseline: 019f7d19-8115; /tp: 019f7d1f-e8d4 |

**Late-arriving originals (4 cases):** B-C02 (`019f7d19-810b` variant mismatch — actually the original B-C02 was `019f7d19-8111-...` no, let me restate. The four late arrivals were:
- B-C06 original `019f7d19-810f-7270-b04b-153b9f15b9da` — near-identical to retry, no material difference
- B-C02 original `019f7d19-810b-71f1-b873-7e4427604a88` — near-identical to retry, marginally more grounded
- B-C10 original `019f7d19-8113-7063-b9a9-5ad20be7ea89` — near-identical to retry, marginally better-written
- B-C08 original `019f7d19-8111-7ee3-8656-bcbd0510241a` — near-identical to retry, marginally more grounded (cited specific file:line)

All four preserved in session transcript; none would have flipped the verdict.

## Judge subagent IDs (one per case)

| Case | Judge subagent |
|---|---|
| C01 | 019f7d24-fbbf-7480-9c7e-18a3596e90a6 |
| C02 | 019f7d24-fbc0-7c73-bd42-0ef03e2b2fd9 |
| C03 | 019f7d24-fbc1-7882-9952-3196aab0b898 |
| C04 | 019f7d24-fbc3-7370-87d0-96cf352f6820 |
| C05 | 019f7d26-99e1-7421-8f83-56c7d1e35c17 |
| C06 | 019f7d26-99e2-7e91-9da7-4c7a734787c8 |
| C07 | 019f7d26-99e3-70e0-815e-1f9d03946051 |
| C08 | 019f7d26-99e4-7420-ad1a-f98c891d924a |
| C09 | 019f7d26-99e5-72a2-8c61-295f15ac8600 |
| C10 | 019f7d26-99e5-72a2-8c61-2967c6cc5426 |
| C11 | 019f7d26-99e6-7112-8aa5-f138e308c9a9 |
| C12 | 019f7d26-99e7-7931-a019-f5b870ad82f3 |

## Threats to validity (see FINAL_REPORT.md §10)

Single-judge limitation, same-model bias, condition leakage via formatting, no historical outcomes.
