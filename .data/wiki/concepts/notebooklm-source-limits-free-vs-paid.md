---
title: "NotebookLM source limits — free vs paid (300 cap)"
created: 2026-07-25
source: session-2026-07-25
tags: [notebooklm, source-limit, capacity, account-tier, fact]
summary: >
  NotebookLM caps sources per notebook by account tier: **free accounts = 50
  sources**, **paid (Plus) accounts = 300 sources**. Each YouTube video, PDF,
  Google Doc, pasted text, etc. counts as one source. The 50-source figure is
  the one most LLMs default to (it was the universal limit for years and is
  over-represented in training data); on a paid account, the real cap is 300.
  Don't trust stale memory here — verify with a test bulk-add at the target
  size before planning a partition.
agent: grok
host: both
cognitive_load: 1
verification: observed
sources:
  - "Operator correction, session-2026-07-25" (paid account, 300 confirmed)
  - "P:/tmp/wl_notebooks_run.log" (cluster 10 hit 300 sources with no error)
  - "https://support.google.com/notebooklm/" (Google NotebookLM Help — official limits page; re-check for current tier table)
relations:
  - target: wiki/concepts/notebooklm-cli-operational-gotchas
    type: referenced-by
  - target: wiki/concepts/semantic-clustering-bounded-size
    type: related
  - target: wiki/concepts/claims-require-receipts
    type: related
---

# NotebookLM source limits — free vs paid

## The fact

| Account tier | Sources per notebook |
|---|---|
| Free | 50 |
| Plus (paid) | **300** |

Each source is one item: one YouTube video, one PDF, one Google Doc, one
pasted text block, one uploaded audio file, etc. Sources are not pages or
chunks — one file = one source, regardless of size.

## The trap

Most LLMs (including me, earlier in this same session) default to "NotebookLM
caps at 50 sources" because:

1. That was the universal limit for years.
2. It's over-represented in training data.
3. The free-tier 50 is the number most blog posts and forum threads cite.

On a paid account, the real cap is **300**. Stating "50" as a universal fact
is wrong and will cause bad planning (e.g. proposing 80 notebooks when 15
would do, or refusing to plan a 200-source notebook at all).

## How to verify before planning

Don't trust this page either — it could go stale. Verify with one test:

```powershell
# Create a throwaway notebook
$nb = (nlm notebook create "capacity-test" --json | ConvertFrom-Json).notebook_id
# Bulk-add a number near your target (e.g. 200)
nlm source add $nb --youtube u1 --youtube u2 ...  # 200 URLs
# Check what landed
nlm notebook get $nb --json | ConvertFrom-Json | Select-Object source_count
# Clean up
nlm notebook delete $nb --confirm
```

If `source_count` matches what you sent, the cap is at or above your target.
If it truncates at 50, you're on a free account.

## What this means for our workspace

- **Default to 300** for any planning on this host — the operator has a paid
  account (confirmed 2026-07-25).
- **The 300 figure was confirmed empirically** in the 2026-07-25 run: cluster
  10 hit exactly 300 sources with no error, clusters 2/4/8/11/12 hit 299.
  See `P:/tmp/wl_notebooks_run.log`.
- **For partition planning** (splitting N items into notebook-sized groups),
  use 300 as the cluster size cap. The pipeline at
  [[semantic-clustering-bounded-size]] is parameterized on this.
- **Re-verify if the operator's account tier changes** (downgrade to free,
  upgrade to a higher tier if Google adds one).
- **Apply the [[claims-require-receipts]] rule** to this page itself: if a
  future session states "NotebookLM caps at 50" as fact, the receipt is the
  capacity test above, not this page. This page is a memory aid, not
  evidence.

## Falsifier

- Google changes the cap (raise or lower) — re-run the capacity test above.
- Account tier changes — re-run the capacity test.
- This page is from 2026-07-25; if you're reading it months later, treat the
  numbers as stale until verified.

## Sources

- Operator correction (session 2026-07-25): "I have a paid account, it's up
  to 300 sources per notebook."
- Empirical confirmation: `P:/tmp/wl_notebooks_run.log`, cluster 10 = 300/300.
- See [[notebooklm-cli-operational-gotchas]] for the broader operational
  context in which this was discovered.
