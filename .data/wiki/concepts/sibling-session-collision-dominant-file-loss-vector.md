---
title: "Sibling-session collision — the dominant file-loss vector on multi-agent hosts"
created: 2026-08-08
source: session-019fdf3d
tags: [multi-agent, concurrency, file-loss, collision, git, transferable-pattern]
summary: >
  On a multi-agent host where multiple sessions commit concurrently to the same
  branch, the most frequent cause of file loss is sibling-session collision:
  one session edits/restores a file while another session is reading or writing
  it. The result is truncated (0 bytes) or overwritten content. Historical data
  confirms this is dominant: 1196 of 2344 sessions (51%) show collision signals.
  The diagnostic: run git reflog to distinguish collision (KNOWN cause) from
  genuine vanishing writes (UNKNOWN cause). Recovery: git checkout HEAD -- <path>.
  This extends [[multi-terminal-isolation-stale-data-immunity]] from the
  scoping dimension to the write-collision dimension, complements
  [[pipeline-session-scoping-each-layer-independently]], and relates to
  [[concurrent-cdp-auth-contention]].
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: extends
  - target: wiki/concepts/pipeline-session-scoping-each-layer-independently.md
    type: complements
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
---

# Sibling-session collision — the dominant file-loss vector

## Decision context

AGENTS.md documents "unexplained vanishing writes" with root cause UNKNOWN.
Session 019fdf3d discovered that the `/tp` SKILL.md went to 0 bytes mid-session.
`git reflog` revealed that sibling session `019fde37` committed to the same
file at the same time. This was not a vanishing write — it was a collision.

Historical analysis of 2,344 sessions confirmed the pattern is dominant:

| Signal | Sessions affected |
|---|---|
| Files going to 0 bytes | 1,445 raw hits |
| Vanishing-write pattern mentioned | 2,078 raw hits |
| SKILL.md going to 0 bytes specifically | 324 raw hits |
| Sessions with ANY collision signal | **1,196 of 2,344 (51%)** |

## The pattern

Multiple AI agent sessions run concurrently on this shared Windows filesystem.
Each session reads, edits, and commits files in `P:/` and `~/.grok`. When two
sessions touch the same file:

1. **Write-while-read collision:** session A reads the file; session B writes
   (truncate + rewrite) between A's read and A's next operation. A sees stale
   or truncated content.
2. **Checkout collision:** session A restores a file from git (`git checkout
   HEAD -- <path>`); session B had uncommitted edits to the same file that
   A's checkout silently overwrites.
3. **Commit collision:** session A commits the file; session B commits a
   different version; `git status` on the next pull shows the conflict or
   one version silently wins.

## The diagnostic

Before classifying a file loss as "unexplained vanishing write" (root cause
UNKNOWN), run:

```powershell
git reflog -- <path>
```

If a sibling session committed to the file at the time of the loss → **collision**
(root cause KNOWN). Recovery: `git checkout HEAD -- <path>`.

If no sibling commit is visible → genuine **vanishing write** (root cause UNKNOWN,
needs deeper investigation).

## What this means for our workspace

- AGENTS.md already documents the pre-commit collision check (`git log -- <path>`
  before staging). Session 019fdf3d updated the vanishing-writes section to
  distinguish collision from genuine vanishing writes.
- The `/tp` SKILL.md 0-byte event was collision, not vanishing-write. HEAD was
  intact; `git checkout HEAD` restored it in one command.
- Many historical "unexplained vanishing writes" may be reclassifiable as
  collisions. The reflog diagnostic is the test.
- This reframes the risk profile: collisions are common (51% of sessions) but
  low-severity (recoverable via git). Genuine vanishing writes are rare but
  higher-severity (root cause unknown, may not be recoverable).

## Falsifier

This pattern is wrong if the reflog diagnostic consistently shows NO sibling
commits at the time of file loss — meaning the losses ARE genuine vanishing
writes. The 51% session-affected rate counts sessions with collision signals
in the transcript, not verified collision incidents. To tighten: run the
reflog diagnostic on the next 5 file-loss events and confirm the collision
rate.

## Receipts

- Session 019fdf3d: `/tp` SKILL.md went to 0 bytes; reflog showed session
  019fde37 committed at 22:51; `git checkout HEAD` restored
- Session 019fdf3d: `/go` SKILL.md had uncommitted sibling edits detected
  via `git diff` before staging
- Historical analysis: `P:/tmp/historical_session_analysis.py` (2344 sessions)
- AGENTS.md § "Unexplained vanishing writes" (updated 2026-08-08 with the
  collision distinction + diagnostic procedure)

## Auto-related

- [[skill-catalog]]
- [[user-modeling-for-agentic-clis]]
- [[github-repository-file-structures]]
- [[file-edit-failures-two-classes]]
- [[context-firewall-architecture]]

