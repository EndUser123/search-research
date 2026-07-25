# Decision points — fuller discussion

The SKILL.md table gives defaults. This page explains *why* and *when to change*.

## Source cap (`--max-size`)

**Default: 300** (paid NotebookLM Plus account).

| Tier | Cap |
|---|---|
| Free | 50 |
| Plus | 300 |
| Pro | 300 (per Google's published tiers as of 2026-07) |
| Ultra | 600 ( rumored ; verify on your account ) |

The CLI does not enforce these — Google does, server-side. If you exceed the
cap, sources past the limit silently fail to register. Always verify via
`nlm notebook get <id> source_count`.

**Verification recipe** (from [[notebooklm-source-limits-free-vs-paid]]):

```bash
nb=$(nlm notebook create "capacity-test" --json | python -c "import json,sys; print(json.load(sys.stdin)['notebook_id'])")
# Bulk-add 60 URLs (above free cap, below paid)
nlm source add $nb --youtube u1 --youtube u2 ...   # 60 URLs
sleep 30
nlm notebook get $nb --json | python -c "import json,sys; print('count:', json.load(sys.stdin).get('source_count'))"
nlm notebook delete $nb --confirm
# If count == 60: paid (cap ≥ 300). If count == 50: free.
```

## Min cluster size (`--min-size`)

**Default: 5.** Below this, clusters are merged into their nearest neighbor.

| Value | Effect |
|---|---|
| 3 | Surfaces small themes (e.g. "5 videos on a niche topic") |
| 5 (default) | Balances coverage vs notebook sprawl |
| 10 | Fewer, larger notebooks; loses small themes |
| 20 | Aggressive consolidation; use only if clustering is producing too many notebooks |

## Notebook title prefix (`--prefix`)

**Default: `""`** (empty).

Common prefixes:

| Prefix | When |
|---|---|
| `""` | General use — cluster name only |
| `"WL: "` | Watch-later imports — distinguishes from other notebooks |
| `"Research: "` | Curated research collections |
| `"Podcast: "` | Notebook intended for podcast generation |

## Pilot cluster selection

**Always pilot before `--all`** when creating ≥5 notebooks. The pilot validates:

1. **Clustering quality** — does the grouping make sense for this corpus?
2. **API path** — does bulk-add actually land all sources in this environment?
3. **Title quality** — is the auto-name acceptable, or do you need to override?

**How to pick the pilot:**

- Smallest coherent cluster (~150 items) — easy to spot-check every member
- A cluster whose theme you can verify by eye (e.g. "all videos from one channel")
- NOT the largest cluster (longer pilot time, harder to verify)

**Pilot pass criteria:**

- `source_count` matches expected (status `ok`)
- Opening the notebook in NotebookLM UI shows sensible sources
- Cluster auto-name isn't egregiously wrong

## Profile selection (`--profile`)

**Default on this host: `codex`** (paid account, cached Google login).

The profile determines which Google account owns the notebooks. Each profile
has its own cookies and NotebookLM quota. To switch:

```bash
nlm login switch <profile-name>
```

To list available profiles:

```bash
nlm login profile list
```

If you don't know which profile to use and the operator is on a paid plan,
`codex` is the safe default on this host. See `~/.grok/tool-fallbacks.md`
under "CLI auth + bulk recipes" for the recovery recipe when auth fails.

## Cluster auto-names — always spot-check

The auto-naming algorithm: tokenize titles (weight 2) + sources (weight 1),
drop stopwords, take top-3 tokens by frequency, join with `-`.

**Honest assessment (from the 2026-07-25 run):**

- ~60% of auto-names are good: `options-market-trading`, `canada-carney-trump`, `fat-thomas-delauer`
- ~25% are noisy but usable: `agent-hermes-agents`, `podcast-google-claude`
- ~15% are bad: `women-hfy-men` (a residual cluster that mixed unrelated content)

**Mitigation:** after clustering, read the first 10-15 video titles from each
cluster (cluster.py prints these to `clusters.md` if you add that output).
If the auto-name badly misrepresents the cluster, override it manually in
`clusters.json` before running `ingest.py`.

## When to skip the pilot

Only safe when ALL apply:

- You've used this exact pipeline on this corpus type before
- Source count per cluster is well below the cap (≤200, not ≤300)
- The corpus is homogeneous (all from one source, e.g. one channel's uploads)
- A failure is recoverable without significant API time (≤5 notebooks)

If any of those are false, pilot first. The pilot costs ~2 minutes; skipping
on a 15-notebook run risks ~30 minutes of API time producing unwanted
notebooks.

## Resume-on-crash

`ingest.py --all --state run.json` checkpoints after each notebook. If the
process dies (Ctrl+C, network outage, system reboot):

```bash
# Just re-run the same command
python ingest.py clusters.json --all --state run.json --prefix "WL: " --profile codex
```

It skips `completed` clusters and retries `failed` ones. Safe to interrupt
and resume any number of times.

**Notebook creations are NOT rolled back on partial failure.** If you Ctrl+C
mid-bulk-add, the notebook exists on NotebookLM with partial sources. The
state file records `status: partial` and the cluster goes into `failed`,
which means re-running will create a NEW notebook for the same cluster. To
clean up duplicates, manually delete the partial notebooks via `nlm notebook
delete <id> --confirm` before resuming.
