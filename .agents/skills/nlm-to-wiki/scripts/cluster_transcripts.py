#!/usr/bin/env python3
"""cluster_transcripts.py — Stage B (v3): sub-topic clustering of transcripts.

Embeds each exported transcript (all-MiniLM-L6-v2 on transcript text, not
title) and clusters them into 5-15 sub-topics per notebook via the same
HDBSCAN two-pass + merge algorithm proven by nlm-bulk-ingest's cluster.py —
adapted for transcript-length inputs and a target cluster COUNT (max-subtopics)
rather than only a size bound.

Rationale: embedding "title + channel" (nlm-bulk-ingest) groups videos by
broad theme across the whole corpus. Embedding transcript text groups by
*content* within a single notebook, surfacing the actual sub-topics the
videos discuss. See [[semantic-clustering-bounded-size]] and
[[video-to-wiki-pipeline-transcript-extraction-multimodal]] § "BERT+KMeans
clustering is proven for transcript sub-topic extraction".

Usage:
  python cluster_transcripts.py --transcripts-dir P:/.data/wiki/sources/transcripts/ \\
      --max-subtopics 10 -o P:/tmp/subtopics.json
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

# --- transcript loading --------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_transcript(path: Path) -> dict:
    """Read a transcript .md, returning {meta, text}. meta = frontmatter fields."""
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    m = FRONTMATTER_RE.match(raw)
    text = raw
    if m:
        block = m.group(1)
        text = raw[m.end():]
        for line in block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")
    # Strip a leading "# Title" heading line from the body for cleaner embedding
    text = re.sub(r"^#\s+.*\n", "", text, count=1)
    return {"meta": meta, "text": text.strip(), "path": str(path), "source_id": meta.get("source_id", path.stem)}


def embed_text(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    print(f"Loading embedding model: {model_name}", file=sys.stderr)
    model = SentenceTransformer(model_name)
    print(f"Encoding {len(texts)} transcripts...", file=sys.stderr)
    emb = model.encode(texts, batch_size=64, show_progress_bar=True,
                       convert_to_numpy=True, normalize_embeddings=True)
    print(f"Embedded in {time.time() - t0:.1f}s. Shape: {emb.shape}", file=sys.stderr)
    return emb


# --- HDBSCAN + merge (adapted from nlm-bulk-ingest/scripts/cluster.py) ---

def cluster_hdbscan(emb: np.ndarray, min_cluster_size: int, min_samples: int) -> np.ndarray:
    from sklearn.cluster import HDBSCAN
    hdb = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="cosine",
        cluster_selection_method="eom",
        n_jobs=-1,
    )
    return hdb.fit_predict(emb)


def two_pass_cluster(emb: np.ndarray, min_cluster_size: int) -> np.ndarray:
    """Two-pass HDBSCAN + KNN-assign for residual noise."""
    print(f"Pass 1: HDBSCAN (min_cluster_size={min_cluster_size}, min_samples=3)", file=sys.stderr)
    labels = cluster_hdbscan(emb, min_cluster_size, 3)
    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    print(f"  clusters: {n_clusters}, noise: {n_noise}", file=sys.stderr)

    noise_mask = labels == -1
    if noise_mask.sum() > 0:
        noise_idx = np.where(noise_mask)[0]
        print(f"Pass 2: re-clustering {len(noise_idx)} noise (min_cluster_size=4, min_samples=1)", file=sys.stderr)
        labels2 = cluster_hdbscan(emb[noise_idx], 4, 1)
        offset = labels.max() + 1
        for j, gi in enumerate(noise_idx):
            if labels2[j] != -1:
                labels[gi] = labels2[j] + offset
        print(f"  remaining noise: {int((labels == -1).sum())}", file=sys.stderr)

    final_noise = labels == -1
    if final_noise.sum() > 0 and n_clusters > 0:
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


def cluster_pieces(labels: np.ndarray) -> list[list[int]]:
    """Group label array into lists of indices."""
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(i)
    return list(groups.values())


def merge_to_max_count(pieces: list[list[int]], emb: np.ndarray, max_count: int) -> list[list[int]]:
    """Greedy merge most-similar cluster pairs until count <= max_count."""
    if len(pieces) <= max_count:
        return pieces
    print(f"Merging {len(pieces)} -> <= {max_count} clusters (greedy by centroid cosine)", file=sys.stderr)
    rounds = 0
    while len(pieces) > max_count:
        centroids = []
        for idxs in pieces:
            c = emb[idxs].mean(axis=0)
            n = np.linalg.norm(c)
            centroids.append(c / n if n > 0 else c)
        centroids = np.array(centroids)
        best_sim, best_pair = -1.0, None
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                sim = float(centroids[i] @ centroids[j])
                if sim > best_sim:
                    best_sim, best_pair = sim, (i, j)
        if best_pair is None:
            break
        i, j = best_pair
        pieces[i] = pieces[i] + pieces[j]
        del pieces[j]
        rounds += 1
    print(f"  {rounds} merges -> {len(pieces)} clusters", file=sys.stderr)
    return pieces


# --- naming (top tokens across member transcripts) ----------------------

STOP = set("""a an the of to in on for and or with by from how what why when is are was
were be been being this that these those it its as at into your you i my me we they
them he she his her their our 1 2 3 new best top vs use using build make making
review test actually really part ep episode pt full guide tutorial will can do does
don didn could would should up out over under more most less much many few all any
some no not yes here there now then than only just also too very about after before
during through between across within without like so but if because while what which
who whom whose that this these those there here then than""".split())


def name_cluster(transcripts: list[dict], top_n: int = 3) -> str:
    """Name a cluster from the most frequent non-stop tokens across member transcripts."""
    c = Counter()
    for t in transcripts:
        title = t["meta"].get("title", "")
        for tok in re.findall(r"[a-z][a-z0-9]+", title.lower()):
            if tok not in STOP and len(tok) > 2:
                c[tok] += 3
        # Sample the first 800 chars of transcript body for topic tokens
        body = t["text"][:800].lower()
        for tok in re.findall(r"[a-z][a-z0-9]+", body):
            if tok not in STOP and len(tok) > 3:
                c[tok] += 1
    return "-".join(w for w, _ in c.most_common(top_n)) if c else "misc"


# --- main ----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts-dir", type=Path, required=True)
    ap.add_argument("--max-subtopics", type=int, default=10, help="target max cluster count (default 10)")
    ap.add_argument("--min-subtopics", type=int, default=3, help="natural floor; report if fewer natural clusters")
    ap.add_argument("--min-cluster-size", type=int, default=5, help="HDBSCAN min_cluster_size (transcripts default 5)")
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
    ap.add_argument("--notebook", default=None, help="optional notebook_id to annotate output")
    ap.add_argument("-o", "--output", type=Path, default=Path("subtopics.json"))
    args = ap.parse_args()

    files = sorted(args.transcripts_dir.glob("*.md"))
    if not files:
        print(f"FATAL: no transcripts in {args.transcripts_dir}", file=sys.stderr)
        return 2
    print(f"Loaded {len(files)} transcript files", file=sys.stderr)

    transcripts = [parse_transcript(p) for p in files]
    # Embed title + first ~1500 chars of transcript body. MiniLM truncates at
    # 256 tokens; leading transcript text carries the topic signal.
    embed_inputs = []
    for t in transcripts:
        title = t["meta"].get("title", "")
        body = t["text"][:1500]
        embed_inputs.append(f"{title}. {body}".strip())
    emb = embed_text(embed_inputs, args.model)

    labels = two_pass_cluster(emb, args.min_cluster_size)
    pieces = cluster_pieces(labels)
    pieces.sort(key=lambda idxs: -len(idxs))
    pieces = merge_to_max_count(pieces, emb, args.max_subtopics)

    clusters_out = []
    for new_id, idxs in enumerate(pieces):
        members = [transcripts[i] for i in idxs]
        centroid = emb[idxs].mean(axis=0).tolist()
        clusters_out.append({
            "cluster_id": new_id,
            "name": name_cluster(members),
            "count": len(idxs),
            "member_source_ids": [m["source_id"] for m in members],
            "members": [
                {"source_id": m["source_id"], "title": m["meta"].get("title", ""),
                 "url": m["meta"].get("url", "").strip() or None,
                 "type": m["meta"].get("type", "unknown")}
                for m in members
            ],
            "centroid": centroid,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "notebook_id": args.notebook,
        "transcripts_dir": str(args.transcripts_dir),
        "model": args.model,
        "total_transcripts": len(transcripts),
        "cluster_count": len(clusters_out),
        "clusters": clusters_out,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(file=sys.stderr)
    print(f"Clusters: {len(clusters_out)} (target max {args.max_subtopics})", file=sys.stderr)
    for c in clusters_out:
        print(f"  [{c['cluster_id']:2d}] {c['count']:4d}  {c['name']}", file=sys.stderr)
    # AC-2 check: each cluster >=3 members, none unassigned
    too_small = [c["cluster_id"] for c in clusters_out if c["count"] < 3]
    if too_small:
        print(f"WARN: clusters with <3 members: {too_small}", file=sys.stderr)
    print(f"\nOutput: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
