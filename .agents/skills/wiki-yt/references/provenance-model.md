# Provenance model — the 4-hop chain

Every wiki page emitted by `nlm-to-wiki` carries provenance that lets a
reader trace any claim back to the original source material. This is the
core differentiator from `nlm notebook query | tee wiki.md`, which loses
all provenance.

## The chain

```
Wiki concept page
    │
    │  frontmatter.provenance.chain[0]
    ▼
Notebook (NotebookLM)
    │
    │  frontmatter.provenance.chain[1]
    ▼
Cluster (from nlm-bulk-ingest)        ◄── only present with --from-clusters
    │
    │  frontmatter.provenance.chain[2]
    ▼
Source URL (original YouTube video, PDF, web page, etc.)
```

## Why each hop matters

### Hop 1: Concept → Notebook

Without this, a reader has no way to know *which* NotebookLM notebook
produced a concept. The page would be unfalsifiable — no way to re-derive
or verify.

The notebook link is `https://notebooklm.google.com/notebook/<uuid>`. A
click takes the reader to the actual notebook with all its sources, where
they can re-query, regenerate artifacts, or check the original sources.

### Hop 2: Notebook → Cluster

Without this (when coming from `nlm-bulk-ingest`), there's no connection
between the concept and the original URL list. A cluster contains 50-300
URLs that were semantically related; knowing which cluster a concept came
from tells the reader "this concept emerged from videos about X."

The cluster itself is identified by `cluster_id` + `name` from
`clusters.json`. The original list of URLs in that cluster is in
`clusters.json` under `videos[].url`.

### Hop 3: Cluster → Source URL

The deepest hop. Through the `citations` block on each concept page, a
reader can identify the specific source (notebook source UUID) that
supports a specific claim. Cross-referencing the cluster gives them the
specific original URL.

## When the chain is shorter

| Sync mode | Chain depth |
|---|---|
| `--notebook <id>` (no bulk-ingest context) | 2 hops: concept → notebook |
| `--from-clusters clusters.json` | 3 hops: concept → notebook → cluster |
| `--from-clusters clusters.json` + Data-Table's `primary_source_id` matched to cluster's `videos[].url` | 4 hops: concept → notebook → cluster → source URL |

The 4-hop chain requires matching the NotebookLM source UUID (which
NotebookLM assigns when you bulk-add a URL) back to the original URL in
`clusters.json`. This matching is not automatic — NotebookLM doesn't
expose a "source URL → source UUID" mapping directly. The current
implementation stops at hop 3 and documents the cluster's URL list in
the cluster record; an operator following provenance can manually match
by re-listing sources through the canonical YTIS direct client and matching
titles.

## Falsifiability across the chain

The chain makes every concept falsifiable:

- **At the concept level:** is the definition grounded in the cited source?
- **At the notebook level:** did the notebook actually have this source?
- **At the cluster level:** does this concept fit the cluster's theme?
- **At the URL level:** does the original video actually say this?

A reader can reject a claim at any level. Without the chain, only the
concept-level check is possible ("does this seem right?"), which is
exactly the failure mode `~/.grok/AGENTS.md` warns about under
"Claims require receipts."

## Manifest enables re-sync integrity

`P:/.data/wiki/_state/nlm-sync-manifest.json` records `{notebook_id,
source_hash, source_ids, concept_slugs, last_synced_at}`. On re-sync:

- Source hash unchanged → skip extraction, page is still valid
- Source hash changed → re-extract, then compare new concepts to existing
  slugs. New slugs → new pages. Existing slugs with changed definition →
  mark as refines (don't silently overwrite the prior page)

This makes the chain stable across re-syncs: a reader who saw concept X
on day 1 will find either X (unchanged) or X-refines-X (refined), never
silently-replaced X.
