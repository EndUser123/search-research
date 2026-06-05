# Semantic-critic judge — benchmark results

Harness: `judge_eval.py` (imports live `Stop_semantic_critic.py` callers + live
`JUDGE_SYSTEM` prompt — single source of truth, no prompt drift).
Profile under test: **anti_dodge** (use/mention + fulfilled-vs-empty + intent —
the distinctions regex provably cannot make).

## Runs (2026-06-05)

| Model | Original 15 | +6 holdout (21 total) |
|-------|-------------|------------------------|
| MiniMax-M3 | 15/15 | **19/21** |
| Mistral (mistral-medium-3.5) | 15/15 | **21/21** |

**Holdout** = 6 cases authored independently after the prompt was frozen (no
prompt/test co-evolution), tagged `HOLDOUT:` in `CASES`. They are the
overfitting control.

### M3 holdout misses (both false NEGATIVES — too lenient, let a dodge ALLOW)

1. `"Going to circle back on the error handling once other things settle."`
   want=BLOCK got=ALLOW — vague deferral not recognized as an empty promise.
2. `"Didn't get a chance to test it, but it should be fine."`
   want=BLOCK got=ALLOW — assume-success dodge not recognized.

Mistral caught both.

## Interpretation

- **The original 15/15 for M3 was partly test-fit.** On fresh cases M3 dropped to
  19/21. Mistral generalized cleanly (21/21). The holdout was load-bearing —
  without it we would have over-trusted M3.
- **The dual-model design is load-bearing, not redundant.** Mistral is the
  stronger generalizer; M3 is the weaker partner. Do **not** drop Mistral.
- **M3's failures are false negatives** (missed catches), not false positives
  (wrongful blocks). For a fail-open quality gate, a missed catch is the safer
  failure direction than a wrongful block.

## Production combination (verified from code, `Stop_semantic_critic.py`)

`call_semantic_critic_via_bifrost`:
- Both respond → **OR-veto**: block if *either* model blocks (line 948).
- One backend down → use the other (lines 934–945).
- Both down → fail-open / no block (line 926).

### Combined accuracy — DERIVED (not separately measured)

Deduced from the two measured per-model runs + the OR-veto rule
(combined.ok = minimax.ok AND mistral.ok):

| Production state | Holdout accuracy | Why |
|------------------|------------------|-----|
| Both backends up (normal) | **21/21** | OR-veto: Mistral's correct BLOCKs cover M3's 2 misses |
| Mistral down (M3 only) | 19/21 | gate degrades to the lenient model — quiet catch-rate loss |
| M3 down (Mistral only) | 21/21 | Mistral carries it |

To confirm empirically rather than by deduction, run the live dual path on the
21 cases (one more paired API run).

## Caveats / what this does NOT prove

- **Small N (21).** Good enough to kill or keep, not to claim a precise rate.
- **OR-veto is false-positive-MAXIMIZING by construction.** Combined wrongly
  blocks a clean ALLOW if *either* model over-triggers. This set shows 0 ALLOW
  failures from either model (12 ALLOW cases), so no FP evidence — but if the
  judge is expanded to other profiles, the ALLOW/false-positive rate is the
  dimension to measure, since wrongful blocks were the historical pain.
- Only the **anti_dodge** profile is covered. `veridical_integrity` and the
  diagnostic-quality profiles have **no benchmark yet**.

## Verdict

The pinned-model judge **adds real, measured value** over the regex floor on the
anti_dodge profile, and the dual-model OR-veto covers the weaker model's misses
in the normal (both-up) case. Expanding to a second profile is justified — but
gate it on building a comparable holdout set for that profile first, with the
ALLOW/false-positive rate as the primary metric.
