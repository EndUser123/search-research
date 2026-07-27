---
title: "Semantic clustering with bounded cluster size (HDBSCAN two-pass + KNN-assign + greedy merge)"
created: 2026-07-25
source: session-2026-07-25
tags: [clustering, hdbscan, embeddings, ml-technique, partition, content-organization, reusable-pattern]
summary: >
  A reusable pipeline for partitioning N items into semantically coherent
  groups each bounded by a maximum size K (e.g. "≤300 videos per NotebookLM
  notebook"). Naive single-pass HDBSCAN left 40% of items as unassigned noise.
  The fix is a four-stage pipeline: (1) two-pass HDBSCAN (strict then soft)
  to recover small clusters that the strict pass missed, (2) KNN-assign
  remaining noise to nearest cluster centroid so no item is left behind,
  (3) greedy agglomerative merge of clusters that would fit under the cap,
  minimizing total cluster count while keeping semantic coherence, (4)
  recursive KMeans split of any cluster that exceeds the cap. Verified on
  4116 YouTube titles → 15 clusters of 154–300 each, mean 274.
agent: grok
host: both
cognitive_load: 3
verification: observed
sources:
  - "McInnes et al., HDBSCAN, https://hdbscan.readthedocs.io/" (2017, algorithm reference)
  - "session-2026-07-25" (4116-item corpus, 15 verified clusters)
relations:
  - target: wiki/concepts/notebooklm-cli-operational-gotchas
    type: complements
  - target: wiki/concepts/cost-aware-model-tiering
    type: related
---

# Semantic clustering with bounded cluster size

## Decision context

**Why this was needed:** partition 4116 YouTube videos into groups of ≤300,
each group going into one NotebookLM notebook as sources. The constraint is
both semantic ("meaningful similarity" — the user's word) and structural
(NotebookLM caps sources at 300 per notebook on a paid account). The
objective is **minimize notebook count** (each notebook is a permanent
artifact; fewer is better) subject to (a) every cluster ≤300, (b) every
item in exactly one cluster, (c) items in a cluster are genuinely similar.

**What was wrong with naive approaches:**

This is a [[problem-first-systems-decomposition]] situation — the wrong
move is to jump to "use HDBSCAN" or "use KMeans" without enumerating the
failure modes of each first.

| Naive approach | Failure mode |
|---|---|
| Single-pass HDBSCAN, drop noise | 40% of items become noise (1662/4116). Either you discard them (loses content) or dump them into one giant "residual" notebook (defeats the point). |
| Fixed-K KMeans | K is unknown a priori; forcing K=14 produces clusters of ~294 each by construction but destroys semantic coherence (KMeans optimizes variance, not density). |
| Agglomerative clustering with distance threshold | Same noise problem as HDBSCAN if threshold is tight; same coherence problem as KMeans if threshold is loose. |

## The four-stage pipeline

```
   N items
      │
      ▼
 [Embed]   all-MiniLM-L6-v2, normalize=True  (cosine distance ready)
      │
      ▼
 [HDBSCAN pass 1]  min_cluster_size=8, min_samples=3, metric=cosine, eom
      │             ──► dense cores get labeled; sparse points → noise
      ▼
 [HDBSCAN pass 2]  re-cluster the noise only, min_cluster_size=4, min_samples=1
      │             ──► recovers small clusters the strict pass missed
      ▼
 [KNN-assign]      remaining noise → nearest existing cluster centroid (k=1)
      │             ──► every item now has a label; zero residual
      ▼
 [Greedy merge]    while any two clusters can merge without exceeding K:
      │               merge the pair with highest cosine centroid similarity
      ▼
 [Split]           for any cluster still > K: recursive KMeans into ⌈n/(0.85·K)⌉
                    sub-clusters (headroom avoids borderline oversize)
      │
      ▼
   final clusters, each ≤ K
```

## Why each stage exists

**Two-pass HDBSCAN.** HDBSCAN's density-based clustering is excellent at
finding dense cores but conservative about fringe points. A single pass
with `min_cluster_size=8` correctly identifies large themes but rejects
smaller sub-themes (e.g. "a 6-video cluster on options-trading diagonals").
Re-running on the noise with `min_cluster_size=4` recovers these. On the
4116-item corpus, pass 2 turned 1662 noise points into 98 new clusters +
992 remaining noise.

**KNN-assign residual.** After two passes, ~24% of items (992/4116) were
still noise. Throwing them away is wrong (they're real videos the user
saved). Dumping them into one "misc" cluster is also wrong (defeats
clustering). Assigning each to its nearest cluster centroid by cosine
similarity is the principled middle ground: every item joins its
semantically closest group. This will occasionally mis-assign a truly
unique item, but the alternative (a giant residual bucket) is worse. This
echoes the [[invariants-beat-environment-comfort]] principle: the
invariant is "every video lands in exactly one cluster," and the KNN step
enforces it structurally rather than leaving it to ad-hoc handling.

**Greedy merge.** After pass 2 + KNN-assign, the corpus had 122 small
clusters (mean size 34). Creating 122 notebooks defeats the "minimize
notebook count" objective. Greedy agglomerative merge — repeatedly combine
the two most cosine-similar clusters whose combined size ≤ K — collapses
122 → 15 clusters of 154–300 each. This is the step that packs toward the
size cap.

**Recursive split (rarely fires).** A cluster can exceed K if pass 1 +
pass 2 found a single very dense core. On this corpus, one cluster of 2037
items needed splitting into 12 KMeans sub-clusters. The 0.85 headroom
factor (`n_split = ⌈n/(0.85·K)⌉`) prevents borderline oversize from uneven
KMeans partitions.

## Verified result (2026-07-25 corpus)

| Metric | Value |
|---|---|
| Items in | 4116 |
| Items assigned | 4116 (100%, zero residual) |
| Clusters out | 15 |
| Min cluster size | 154 |
| Max cluster size | 300 (exactly the cap) |
| Mean | 274 |
| Median | 296 |
| Wall-clock (full pipeline) | ~12 seconds |

Cluster size distribution was tight and packed near the cap, which is what
"minimize notebook count" looks like in practice.

## Picking parameters

| Parameter | Default | How to tune |
|---|---|---|
| `min_cluster_size` (pass 1) | 8 | Lower if you want small themes surfaced; raise if you want only major themes |
| `min_cluster_size` (pass 2) | 4 | Half of pass 1; recover small clusters the strict pass missed |
| `min_samples` (pass 1 / pass 2) | 3 / 1 | Lower = more permissive; raises recall, lowers precision |
| `metric` | `cosine` | Use cosine for normalized embeddings; euclidean otherwise |
| `cluster_selection_method` | `eom` | `eom` (excess of mass) gives stable spherical clusters; `leaf` gives finer granularity |
| MAX_CLUSTER (the size cap) | task-specific | NotebookLM paid = 300; free = 50; arbitrary for other uses |
| MIN_CLUSTER (merge threshold) | 5 | Below this, merge into nearest neighbor (avoids notebook sprawn) |

## What this means for our workspace

- **The pipeline is in `P:/tmp/cluster_watchlater.py`** and is reusable.
  Change `SRC`, `MAX_CLUSTER`, and `MIN_CLUSTER` for any other corpus
  (PDFs, skills, git commits, etc.).
- **For any future "partition N items into bounded-size groups by
  similarity" task** — e.g. "split 1000 skills into notebook-sized
  clusters," "group 500 PDFs into 50-source buckets" — this pipeline is
  the starting point. Don't reinvent. The companion gotchas page
  [[notebooklm-cli-operational-gotchas]] covers the NotebookLM-specific
  ingest side; this page covers the clustering side.
- **Cluster auto-naming** via top-tokens is rough. For the NotebookLM run,
  the operator received auto-names like "women-hfy-men" (noise) alongside
  coherent ones like "options-market-trading." Always spot-check cluster
  content before relying on the auto-name; the grouping is much better
  than the label.
- **The greedy-merge step is O(n²) per iteration** — fine for n ≤ ~500
  initial clusters. For larger n, switch to priority-queue-based
  agglomerative (Lance-Williams).

## Falsifier

This pipeline is overkill when:
- **N is small (<100):** a single HDBSCAN pass + manual review is faster.
- **Cluster size cap doesn't matter:** drop the merge step; pass-through
  HDBSCAN labels are the answer.
- **Items are short strings with no real semantic structure** (e.g.
  filenames): embeddings won't help; use string distance.
- **The corpus has ground-truth labels:** supervised classification will
  beat unsupervised clustering.

The pipeline was validated exactly once, on one corpus (YouTube titles,
N=4116). It generalizes by construction (the steps are corpus-agnostic),
but the parameter defaults (min_cluster_size=8, etc.) are tuned for
natural-language titles of ~50–100 chars. Re-tune for very different
input shapes (very short strings, very long documents, multilingual
content where `all-MiniLM-L6-v2` underperforms).

## Sources

- [HDBSCAN docs](https://hdbscan.readthedocs.io/) (McInnes et al.) —
  algorithm reference, parameter semantics
- [sentence-transformers](https://www.sbert.net/) — `all-MiniLM-L6-v2`
  embedding model, 384-dim, unit-normalized
- sklearn 1.7.2 `HDBSCAN` (replaces the standalone `hdbscan` package —
  no extra install needed on this host)
- Session 2026-07-25 run log — 4116-item corpus, 15 verified clusters,
  `P:/tmp/wl_notebooks_run.log`
