# nlm-to-wiki Sensitivity Analysis Experiment Plan

**Goal:** determine which of the 7 pipeline parameters actually affect output quality, not just speed. This tells us where to focus optimization effort.

## Parameters to sweep

| # | Parameter | Current default | Sweep values | What it controls |
|---|---|---|---|---|
| 1 | `--max-subtopics` | 10 | 5, 10, 15, 20 | Cluster granularity |
| 2 | `--min-cluster-size` | 5 | 3, 5, 8, 12 | HDBSCAN sensitivity |
| 3 | `--per-member-chars` | 1200 | 500, 1200, 2000, 3000 | How much transcript the LLM sees |
| 4 | `--max-members` | 20 | 10, 20, 30, 50 | How many transcripts per cluster prompt |
| 5 | `--synth-backend` | mmx | mmx, dgemma | LLM quality vs cost |
| 6 | `--spacing` | 1.5s | 0.5, 1.5, 3.0 | Export pacing (affects rate-limit risk) |
| 7 | `--threshold` (reconcile) | 0.75 | 0.60, 0.75, 0.85 | Dedup aggressiveness |

## Measurement metrics (from report.py)

| Metric | What it tells us | Target |
|---|---|---|
| `citation_rate` | Are all transcripts cited? | ≥95% |
| `avg_citations_per_page` | Evidence density | ≥5 |
| `n_concept_pages` | Productivity | ≥8 per notebook |
| `validation_rate` | Quality gate | 100% |
| Cluster balance (max/min ratio) | Distribution health | <10x |
| Total citations | Evidence volume | ≥50 per notebook |

## Experiment design

**One-at-a-time (OAT) sweep** — vary one parameter at a time, hold others at default. This is cheaper than full factorial (4^7 = 16,384 runs) and sufficient for identifying which parameters matter.

**Pilot notebook:** `23bf4931-d0cb-4550-9d11-f9b38843254a` (188 sources, transcripts already cached → export is instant, so each run only costs cluster+synthesize time = ~7 min).

**Total runs:** 4 values × 7 parameters = 28 runs × ~7 min = ~3.3 hours.

**The sweep driver** (`sensitivity_sweep.py`):
1. For each parameter, for each sweep value:
   - Clear the notebook's manifest entry (force re-sync)
   - Run `sync.py --notebook <pilot> --profile codex` with the varied parameter
   - Capture `report.py --json` output
   - Record parameter + value + metrics
2. After all runs, compute: for each parameter, what's the delta between best and worst metric values?
3. Rank parameters by max delta → the ones with large deltas are the ones that matter.

## Expected results (hypotheses)

| Parameter | Expected impact | Why |
|---|---|---|
| `--max-subtopics` | HIGH on cluster balance, MEDIUM on pages | More clusters = finer granularity but smaller clusters |
| `--min-cluster-size` | HIGH on cluster count | Lower = more clusters, higher = fewer but larger |
| `--per-member-chars` | MEDIUM on citation quality | More context = better synthesis but more tokens |
| `--max-members` | LOW (most clusters < 20 members) | Only matters for mega-clusters |
| `--synth-backend` | HIGH on quality | mmx vs dgemma quality difference |
| `--spacing` | ZERO on quality (only affects speed) | Pure throughput parameter |
| `--threshold` | LOW (most pages are "new", not "refines") | Only matters when wiki has overlapping content |

## Implementation

~100 lines for `sensitivity_sweep.py`:
- Reads the parameter sweep table
- Runs sync.py + report.py per configuration
- Writes results to `P:/tmp/sensitivity-results.json`
- Produces a summary table ranking parameters by impact

The measurement infrastructure already exists (report.py --json). Only the sweep driver needs writing.

## When to run

After the bulk run completes (so the pilot notebook's transcripts are cached and the cluster-filter fix is proven). The sweep runs are fast (~7 min each) since export is skipped.
