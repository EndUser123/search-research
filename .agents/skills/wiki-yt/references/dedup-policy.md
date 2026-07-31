# Dedup policy — the refines branching

When `reconcile.py` finds an existing wiki concept similar to a candidate,
the new page is written with `relations: type: refines` rather than
skipped or merged. This document explains why and how.

## The threshold

`reconcile.py --threshold 0.75` (default). The threshold is on qmd's
similarity score, which is a normalized value (0-1, higher = more similar)
derived from Qwen3-Embedding-0.6B cosine similarity.

| Threshold | Behavior | Use case |
|---|---|---|
| 0.60 | Aggressive branching; many existing concepts matched | Tight corpus where most things overlap |
| 0.75 (default) | Balanced; matches clearly-the-same-topic concepts | General use |
| 0.85 | Conservative; only near-identical matches match | Loose corpus where you want mostly-new pages |

Tune via `sync.py` → `reconcile.py` (currently no surface flag; edit
`reconcile.py` default or pass `--threshold` if running it standalone).

## Why branch (not skip or merge)

Three options on collision. Branching wins for two reasons.

### Skip with log

**Don't write the new page.** Loses the new notebook's framing of the
concept. If NotebookLM notebook A says "X is a tool for Y" and notebook
B says "X is a tool for Y, with new evidence Z," skipping on B loses Z.

### Merge into existing

**Append new content to existing page.** Risks:
- Conflicting framings on a single page (confusing)
- Bloat — the page grows monotonically
- Loss of provenance — the page no longer points to a single source
- Silent overwrite if the merger is naive

The wiki skill explicitly warns against silent overwrite in its SCHEMA
§13.6 "Never fabricate" and the broader "no silent success" pattern
throughout `~/.grok/AGENTS.md`.

### Branch as refines (chosen)

**Write the new page; add `relations: type: refines` to both directions.**

Pros:
- Both framings survive; reader sees the dialogue
- Each page keeps clean provenance (single notebook)
- Re-syncs are stable (a re-synced page either matches its prior self or branches)
- Matches the wiki skill's existing retirement-check convention
  (`P:/.data/wiki/SCHEMA.md` and `~/.grok/skills/wiki/SKILL.md` §"Retirement check")

Cons:
- More pages in the vault
- Reader has to follow the `refines` link to see the other framing

The trade-off favors branching: provenance integrity and stable re-syncs
outweigh vault-size concerns at this corpus size.

## How matching works

`reconcile.py` runs qmd search for each candidate using
`{title} {definition[:200]}` as the query. The first result above
threshold becomes the `refines` target. The target's slug is stored in
`refines_target` on the candidate; `write_pages.py` emits it as
`relations.target: wiki/concepts/<slug>.md`.

This is best-effort semantic matching, not exact. False positives
(unrelated concepts flagged as refines) and false negatives (related
concepts missed) are both possible. The operator should spot-check the
`refines` decisions in the sync summary before relying on them.

## Cross-notebook reconciliation

When syncing multiple notebooks (--all or --from-clusters), each notebook
is reconciled independently against the *current* state of the vault.
This means:

- Notebook 1's concept "Foo" is written as new
- Notebook 2's concept "Foo" (synced second) is reconciled against the
  vault, sees Notebook 1's "Foo" page, and is written as `refines`

The ordering is sequential, so later notebooks see earlier notebooks'
pages. This is the intended behavior — but it means the *first* notebook
synced has no refines targets, which can feel asymmetric.

## Re-sync reconciliation

When a notebook is re-synced (source_ids changed), each concept is
re-reconciled:

- If the concept already exists in the vault (from prior sync of this
  notebook) and the definition matches → skip
- If the concept exists but the definition changed → write the new
  version as `refines` of the prior version (creating a chronological
  chain: v1 ← refines ← v2)
- If the concept is new → write as `new`

This makes re-syncs safe to schedule. The vault grows monotonically with
branch-on-conflict; nothing is silently overwritten.

## Limitations

The current implementation does NOT:

- Detect when a `refines` target itself gets refines'd (no chain walking)
- Cross-reference `refines` targets across the entire vault (only within
  a single qmd search call per candidate)
- Use semantic similarity below the title+definition level (full-body
  matching is deferred to v2)
- Auto-resolve conflicts (e.g. when two prior pages both claim to be the
  canonical version) — that's an operator decision

These are deliberate v1 scope cuts. They can be added if real usage
shows they're needed.
