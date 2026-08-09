---
title: "Stateful scanner coordination: read artifact body, not file existence"
sources:
  - date: 2026-08-09
    host: grok
    session: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
provenance: session-observation
last_verified: 2026-08-09
---

# Stateful scanner coordination: read artifact body, not file existence

## The pattern

When a scanner (todo, coverage, health check) surfaces artifacts for action, it must read the artifact's **consumption state** from its body or frontmatter, not from file existence alone. A file that exists may have already been consumed (promoted, resolved, closed) — flagging it wastes the operator's attention and erodes trust in the scanner.

## The failure mode

The `/todo` scanner's `scan_dreams()` function checked only:
1. Does the file exist in `docs/dreams/`?
2. Is it <30 days old?

If both were true, it flagged the dream as a pending action item. But dream files persist after their candidates are promoted — the dream skill writes status (`PROMOTED`, `DEFERRED`, `RESOLVED`) in the file body and expects the operator to delete post-hoc. Nobody deletes. Result: every session saw 5 dream files and re-recommended `/dream`, even though 4 of the 5 were fully consumed.

The operator noticed: "I've had a couple of sessions recommend the dream action. Why? If one session does the dream action, shouldn't the other ones then know to stop?"

## Root cause

The scanner treated artifact existence as a proxy for artifact state. This works for handoffs (which are deleted on close) and check receipts (which are overwritten). It fails for artifacts that persist after consumption — dreams, wiki concepts, ADRs. These need a content-aware scan.

## The fix

Read the artifact body and check for consumption markers before flagging:

```python
body = f.read_text(encoding="utf-8")
if not has_unresolved_candidates(body):
    continue  # All candidates resolved — don't flag
```

For dreams, "consumption" = every `Status:` line contains a terminal state (`PROMOTED`, `DEFERRED`, `DORMANT`, `RESOLVED`, `WONTFIX`). Any non-terminal status (`UNVERIFIED`, `pending`, missing) keeps the dream flagged.

## When this applies

Any scanner that surfaces artifacts for action where:
- The artifact persists after consumption (not deleted on close)
- The consumption state is recorded in the body/frontmatter
- Multiple sessions share the scanner output

Known instances in this workspace:
- `/todo` dream scanner (fixed 2026-08-09)
- `/todo` wiki debt scanner (reads debt score — already content-aware)
- `/close` handoff scanner (reads `status:` field — already content-aware)
- `/todo` research scanner (reads `consumed` field — already content-aware)

## Falsifier

If the scanner starts missing genuinely unresolved artifacts because the status markers are misformatted, ambiguous, or use states not in the terminal set, the fix is too aggressive. Monitor for false negatives (unresolved artifacts not surfaced) — they are worse than false positives (resolved artifacts re-flagged) because the operator can dismiss a false positive but cannot discover a false negative.
