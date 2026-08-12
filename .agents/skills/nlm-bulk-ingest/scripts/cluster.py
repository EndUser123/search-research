#!/usr/bin/env python3
"""cluster.py — Stage 3: bounded-size semantic clustering.

Reads canonical.jsonl from normalize.py, embeds titles+sources, clusters via
two-pass HDBSCAN + KNN-assign + greedy merge + recursive split.

Outputs clusters.json: [{cluster_id, name, count, videos:[{id,title,url,source}]}]

Verified 2026-07-25 on 4116 videos → 15 clusters of 154-300 each.
See [[semantic-clustering-bounded-size]] for the algorithm rationale.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np


def load_canonical(path: Path):
    items = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def embed(items, model_name="all-MiniLM-L6-v2"):
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    print(f"Loading embedding model: {model_name}", file=sys.stderr)
    model = SentenceTransformer(model_name)
    texts = [f"{it.get('title', '')} by {it.get('source', '')}".strip() for it in items]
    print(f"Encoding {len(texts)} texts...", file=sys.stderr)
    emb = model.encode(
        texts,
        batch_size=128,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(f"Embedded in {time.time() - t0:.1f}s. Shape: {emb.shape}", file=sys.stderr)
    return emb


def cluster_hdbscan(emb, min_cluster_size, min_samples):
    from sklearn.cluster import HDBSCAN

    hdb = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="cosine",
        cluster_selection_method="eom",
        n_jobs=-1,
    )
    return hdb.fit_predict(emb)


def two_pass_cluster(emb):
    """Two-pass HDBSCAN + KNN-assign for residual."""
    print("Pass 1: HDBSCAN (min_cluster_size=8, min_samples=3)", file=sys.stderr)
    labels = cluster_hdbscan(emb, 8, 3)
    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    print(f"  clusters: {n_clusters}, noise: {n_noise}", file=sys.stderr)

    # Pass 2: re-cluster noise with softer params
    noise_mask = labels == -1
    if noise_mask.sum() > 0:
        noise_idx = np.where(noise_mask)[0]
        print(
            f"Pass 2: re-clustering {len(noise_idx)} noise points (min_cluster_size=4, min_samples=1)",
            file=sys.stderr,
        )
        labels2 = cluster_hdbscan(emb[noise_idx], 4, 1)
        offset = labels.max() + 1
        for j, gi in enumerate(noise_idx):
            if labels2[j] != -1:
                labels[gi] = labels2[j] + offset
        n_noise2 = int((labels == -1).sum())
        print(f"  remaining noise: {n_noise2}", file=sys.stderr)

    # KNN-assign residual to nearest cluster centroid
    final_noise = labels == -1
    if final_noise.sum() > 0:
        cluster_ids = sorted(set(labels) - {-1})
        centroids = np.array([emb[labels == c].mean(axis=0) for c in cluster_ids])
        norms = np.linalg.norm(centroids, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        centroids_n = centroids / norms
        noise_idx = np.where(final_noise)[0]
        sims = emb[noise_idx] @ centroids_n.T
        best = sims.argmax(axis=1)
        for pos, gi in enumerate(noise_idx):
            labels[gi] = cluster_ids[best[pos]]
        print(f"  KNN-assigned {len(noise_idx)} residual points", file=sys.stderr)

    return labels


def merge_tiny(labels, emb, min_size):
    """Merge clusters smaller than min_size into nearest larger cluster."""
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(i)

    merged = 0
    while True:
        small = [lab for lab, idxs in groups.items() if len(idxs) < min_size]
        big = [lab for lab, idxs in groups.items() if len(idxs) >= min_size]
        if not small or not big:
            break
        for slab in sorted(small, key=lambda l: len(groups[l])):
            if not big:
                break
            sc = emb[groups[slab]].mean(axis=0)
            sc_n = sc / (np.linalg.norm(sc) + 1e-9)
            best_big = max(
                big,
                key=lambda bl: float(
                    sc_n
                    @ (
                        emb[groups[bl]].mean(axis=0)
                        / (np.linalg.norm(emb[groups[bl]].mean(axis=0)) + 1e-9)
                    )
                ),
            )
            groups[best_big].extend(groups.pop(slab))
            merged += 1
            big.remove(best_big)
            if slab in big:
                big.remove(slab)
    print(f"Merged {merged} tiny clusters", file=sys.stderr)

    # Reassign labels
    new_labels = np.full_like(labels, -1)
    for new_id, (old_lab, idxs) in enumerate(
        sorted(groups.items(), key=lambda kv: -len(kv[1]))
    ):
        for i in idxs:
            new_labels[i] = new_id
    return new_labels


def split_oversized(labels, emb, max_size):
    """Recursively split clusters larger than max_size via KMeans.

    Falls back to even sequential splitting when k-means collapses (all points
    land in one cluster). This happens on semantically homogeneous input like
    a single YouTube channel — without the fallback, split_recurse infinite-
    loops and Python dies with RecursionError. Incident: session 2026-08-12,
    @moondevonyt at free-tier 50-cap (982 recursions before stack overflow).
    """
    from sklearn.cluster import KMeans

    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(i)

    final: list[list[int]] = []

    def split_recurse(idxs, depth=0):
        if len(idxs) <= max_size:
            final.append(idxs)
            return
        if depth > 100:
            # Safety net; the sequential fallback below should prevent this.
            final.append(idxs)
            return

        n_split = max(
            int(np.ceil(len(idxs) / max_size)),
            int(np.ceil(len(idxs) / (max_size * 0.85))),
        )
        km = KMeans(n_clusters=n_split, n_init=10, random_state=0)
        sub = km.fit_predict(emb[idxs])
        sub_groups: dict[int, list[int]] = {}
        for j, s in enumerate(sub):
            sub_groups.setdefault(int(s), []).append(idxs[j])

        # Collapse-detection: if k-means put nearly everything in one bucket
        # (one sub-group still > max_size while others are tiny/empty), the
        # recursive call on that bucket won't shrink it — infinite loop.
        # Fall back to an even sequential split that is guaranteed to terminate.
        largest = max((len(v) for v in sub_groups.values()), default=0)
        if largest > max_size and len(sub_groups) < n_split:
            print(
                f"  k-means collapsed (1/{len(sub_groups)} buckets); "
                f"sequential fallback",
                file=sys.stderr,
            )
            chunk = int(np.ceil(len(idxs) / n_split))
            for i in range(0, len(idxs), chunk):
                piece = idxs[i : i + chunk]
                if piece:
                    split_recurse(piece, depth + 1)
            return

        for s in sorted(sub_groups.keys()):
            sub_idxs = sub_groups[s]
            if sub_idxs:
                split_recurse(sub_idxs, depth + 1)

    for lab, idxs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(idxs) > max_size:
            print(f"  split cluster {lab} ({len(idxs)})", file=sys.stderr)
        split_recurse(idxs)

    return final


def greedy_merge(pieces, emb, max_size):
    """Greedily merge most-similar cluster pairs while size allows."""
    print(f"Pre-merge: {len(pieces)} clusters", file=sys.stderr)
    rounds = 0
    while True:
        centroids, sizes = [], []
        for idxs in pieces:
            c = emb[idxs].mean(axis=0)
            n = np.linalg.norm(c)
            centroids.append(c / n if n > 0 else c)
            sizes.append(len(idxs))
        centroids = np.array(centroids)

        best_sim, best_pair = -1.0, None
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                if sizes[i] + sizes[j] > max_size:
                    continue
                sim = float(centroids[i] @ centroids[j])
                if sim > best_sim:
                    best_sim, best_pair = sim, (i, j)
        if best_pair is None:
            break
        i, j = best_pair
        pieces[i] = pieces[i] + pieces[j]
        del pieces[j]
        rounds += 1
    print(f"Post-merge: {len(pieces)} clusters ({rounds} merges)", file=sys.stderr)
    return pieces


# ---------- naming ----------

STOP = set(
    """a an the of to in on for and or with by from how what why when is are was
were be been being this that these those it its as at into your you i my me we they
them he she his her their our 1 2 3 new best top vs use using build make making
review test actually really part ep episode pt full guide tutorial will can do does
don didn could would should up out over under more most less much many few all any
some no not yes here there now then than only just also too very about after before
during through between across within without""".split()
)


def name_cluster(items, top_n=3):
    c = Counter()
    for it in items:
        for tok in re.findall(r"[a-z0-9]+", (it.get("title") or "").lower()):
            if tok not in STOP and len(tok) > 2:
                c[tok] += 2
        for tok in re.findall(r"[a-z0-9]+", (it.get("source") or "").lower()):
            if tok not in STOP and len(tok) > 2:
                c[tok] += 1
    return "-".join(w for w, _ in c.most_common(top_n)) if c else "misc"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("input", type=Path, help="canonical.jsonl from normalize.py")
    ap.add_argument("--max-size", type=int, default=300)
    ap.add_argument("--min-size", type=int, default=5)
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
    ap.add_argument("-o", "--output", type=Path, default=Path("clusters.json"))
    args = ap.parse_args()

    items = load_canonical(args.input)
    print(f"Loaded {len(items)} items", file=sys.stderr)
    if not items:
        raise SystemExit("no items to cluster")

    emb = embed(items, args.model)

    labels = two_pass_cluster(emb)
    labels = merge_tiny(labels, emb, args.min_size)
    pieces = split_oversized(labels, emb, args.max_size)
    pieces = greedy_merge(pieces, emb, args.max_size)

    clusters_out = []
    for new_id, idxs in enumerate(pieces):
        cluster_items = [items[i] for i in idxs]
        clusters_out.append(
            {
                "cluster_id": new_id,
                "name": name_cluster(cluster_items),
                "count": len(cluster_items),
                "videos": [
                    {
                        "id": it.get("id"),
                        "title": it.get("title"),
                        "url": it.get("url"),
                        "source": it.get("source"),
                    }
                    for it in cluster_items
                ],
            }
        )

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(clusters_out, f, ensure_ascii=False, indent=2)

    print(file=sys.stderr)
    print(f"Clusters: {len(clusters_out)}", file=sys.stderr)
    for c in clusters_out:
        print(f"  [{c['cluster_id']:2d}] {c['count']:4d}  {c['name']}", file=sys.stderr)
    print(f"\nOutput: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
