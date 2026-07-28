---
name: nlm-bulk-ingest
description: >
  Cluster a large list of URLs (YouTube videos, web pages, PDFs) into themed
  NotebookLM notebooks under the per-notebook source cap, then bulk-add them
  in one call per notebook with crash-resumable checkpointing. Handles source
  caps from 50 (free) to 300+ (paid), semantic clustering with bounded cluster
  size, and the cosmetic first-URL error that panics naive scripts. Use when
  you have more URLs than one notebook can hold and want them organized by
  theme rather than dumped in arbitrary chunks.
host: both
---

# nlm-bulk-ingest

Partition a large URL list into themed NotebookLM notebooks, then bulk-add
each cluster to its own notebook in a single API call per notebook.

Built from a verified 4116-video → 15-notebook run (2026-07-25). The full
design rationale lives in three wiki concepts this skill depends on:

- `[[notebooklm-source-limits-free-vs-paid]]` — why the cap is 300, not 50
- `[[notebooklm-cli-operational-gotchas]]` — bulk-add, cosmetic errors, auth
- `[[semantic-clustering-bounded-size]]` — the four-stage clustering pipeline

## When to use

- You have **more items than one notebook's source cap** (50 free / 300 paid)
- You want them organized into **themed notebooks** (not arbitrary chunks)
- The items have **semantic content to cluster on** (title + channel/author)

## When NOT to use

| Situation | Use instead |
|---|---|
| Single notebook, under cap | `notebooklm` skill directly (`source add --youtube ...`) |
| One source | `nlm source add <nb> --url <u>` |
| Non-NotebookLM destination | not this skill |
| Items have no semantic structure (raw UUIDs, filenames) | sort by metadata, split into chunks — clustering won't help |

## Workflow (5 stages)

```
INPUT                  NORMALIZE              DEDUP + FILTER
youtube JSON,          ──────────────►        ──────────────►
CSV, JSONL, RSS,       normalize.py           (inside normalize.py)
plain URL list

         │
         ▼  canonical.jsonl: [{id, title, url, source}, ...]

       CLUSTER
       ──────────────►
       cluster.py       bounded-size semantic partition
                        (≤ K per cluster, min notebooks)

         │
         ▼  clusters.json: [{cluster_id, name, count, videos}, ...]

       PILOT (one cluster end-to-end)
       ──────────────►
       ingest.py --pilot <id>   create 1 notebook, bulk-add, verify

         │
         ▼  (operator approves pilot result)

       INGEST + VERIFY (remaining clusters, crash-resumable)
       ──────────────►
       ingest.py --all          checkpoint after each notebook,
                                 verify source_count matches claimed
```

## The five scripts (invoke in order)

```bash
# Stage 1-2: normalize + dedup + filter
python P:/.agents/skills/nlm-bulk-ingest/scripts/normalize.py \
    <input.json|.csv|.txt|.jsonl|.xml> \
    [--format auto|youtube-wl|csv|jsonl|json-array|url-list|rss] \
    [--id-field <name>] [--title-field <name>] \
    [--url-field <name>] [--source-field <name>] \
    [--drop-dead] \
    -o canonical.jsonl

# Stage 3: cluster
python P:/.agents/skills/nlm-bulk-ingest/scripts/cluster.py \
    canonical.jsonl \
    --max-size 300 --min-size 5 \
    -o clusters.json

# Stage 4: pilot (one cluster, end-to-end)
python P:/.agents/skills/nlm-bulk-ingest/scripts/ingest.py \
    clusters.json --pilot <cluster-id> \
    --prefix "WL: " --profile a.hominidae

# Stage 5: ingest remaining (crash-resumable)
python P:/.agents/skills/nlm-bulk-ingest/scripts/ingest.py \
    clusters.json --all \
    --prefix "WL: " --profile a.hominidae \
    --state run-state.json
```

## Decision points

| Decision | Default | When to change |
|---|---|---|
| Source cap (`--max-size`) | 300 (paid) | 50 if free account; check `[[notebooklm-source-limits-free-vs-paid]]` if unsure |
| Min cluster size (`--min-size`) | 5 | Raise to 10+ for fewer, larger notebooks; lower to surface small themes |
| Notebook title prefix (`--prefix`) | `"WL: "` (watch-later) | Empty for general use; `""` gives raw cluster names |
| Pilot cluster | smallest coherent one | Pilot validates clustering quality + API path before full commitment |
| Profile (`--profile`) | `a.hominidae` on this host | The NotebookLM account to use; see `~/.grok/tool-fallbacks.md` for the auth recipe |
| Cluster auto-names | top-3 tokens by TF weighted 2:1 (title:source) | **Always spot-check** — auto-names are rough; the grouping is much better than the label |

## Pilot-before-full-run pattern (mandatory for ≥5 clusters)

Creating N notebooks with M bulk-adds is an irreversible commitment. Always
run one cluster end-to-end first:

1. Pick a cluster that's small enough to inspect every member (~150 items)
2. Create its notebook, bulk-add, verify `source_count` matches
3. Open the notebook in the NotebookLM UI; confirm the sources look right
4. **Only then** run `--all` for the rest

The pilot costs ~2 minutes. Skipping it on a 15-notebook run risks 30+
minutes of API time producing notebooks you don't want.

## Crash-resumable state

`ingest.py --state <path>` checkpoints after each notebook:

```json
{
  "notebooks": {
    "0": {"cluster_id": 0, "title": "...", "notebook_id": "...",
          "expected": 295, "actual": 295, "status": "ok"}
  },
  "completed": [0, 1, 2],
  "failed": []
}
```

Re-running `--all` skips completed clusters and retries failed ones. Safe to
Ctrl+C at any point.

## Operational gotchas (DO NOT rediscover these)

Three traps the bulk-ingest path hits every time. All documented in
`[[notebooklm-cli-operational-gotchas]]` — read that page if any of these
surprise you.

1. **`nlm login --check` lies.** It returns `network_error` even when auth is
   fine. Real test: `nlm notebook list`. Recovery: `nlm login --profile <name>`
   (silent CDP re-auth, no user interaction).

2. **`--youtube` / `--url` is repeatable for bulk.** One CLI call per notebook
   ingests all URLs. Do NOT loop per-video.

3. **First-URL "Error: Failed to add URL source" is cosmetic.** The bulk
   always continues and lands all sources; exit code 1 is misleading. Verify
   via `nlm notebook get <id>` `source_count`, NOT via exit code.

## Input formats

`normalize.py` auto-detects and accepts explicit `--format`:

- `youtube-wl` — YouTube watch-later JSON export (`[{videoId, title, channel, url}, ...]`)
- `csv` — any CSV; auto-detect url/title columns or `--columns url,title`
- `jsonl` — one JSON object per line; specify fields via `--id/title/url/source-field`
- `json-array` — JSON array of objects; same field flags
- `url-list` — one URL per line; title derived from URL or "Item N"
- `rss` — `<item>` with `<title>` and `<link>`

See `references/input-formats.md` for worked examples of each.

## Host-side prerequisites

- `nlm` CLI installed (`pip install notebooklm-mcp-cli`) — verified on 0.9.0
- Python 3.11+ with `sentence-transformers`, `sklearn>=1.3` (for HDBSCAN)
- A cached nlm profile (run `nlm login --profile <name>` once interactively)

## Verification discipline (DO NOT skip)

After every bulk-add:

```python
time.sleep(30)  # let NotebookLM register sources
info = json.loads(subprocess.run(["nlm", "notebook", "get", nb, "--json"], ...).stdout)
actual = info["source_count"]
assert actual == expected, f"{actual}/{expected}"
```

The bulk-add call's exit code is **not** the verification signal. The
`source_count` field from `notebook get` is. `ingest.py` does this
automatically; manual operators must too.

## References

- `references/input-formats.md` — worked examples for each input shape
- `references/decisions.md` — fuller discussion of the decision points
- `[[notebooklm-cli-operational-gotchas]]` — gotchas
- `[[notebooklm-source-limits-free-vs-paid]]` — capacity
- `[[semantic-clustering-bounded-size]]` — clustering algorithm
- `P:/tmp/wl_notebooks_run.log` — worked example from the 2026-07-25 run
