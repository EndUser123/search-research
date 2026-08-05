# Dream Proposal Triage

## Status
OPEN — ready for execution

## Session
session-019fcd47 (2026-08-05)

## Objective

Read and evaluate 7 dream proposals in `P:/docs/dreams/`. For each, determine
whether the cross-session pattern synthesis is still relevant, and recommend
PROMOTE (to wiki concept via /wiki) or ARCHIVE (pattern no longer applies or
was superseded).

## Dream proposals (newest first)

| # | File | Age |
|---|------|-----|
| 1 | 2026-08-04-dream-external-synthesis.md | 0d |
| 2 | 2026-08-04-dream-session-019fcb53.md | 0d |
| 3 | 2026-08-02-dream.md | 2d |
| 4 | 2026-08-01-dream-session-019fb933.md | 3d |
| 5 | 2026-08-01-dream.md | 3d |
| 6 | 2026-07-26-dream-incremental.md | 9d |
| 7 | 2026-07-26-dream.md | 10d |

## Scope

For each dream:

1. Read the proposal
2. Summarize: what cross-session pattern does it identify?
3. Check: has this pattern already been addressed? (Search wiki for related concepts, check if handoffs closed the gap)
4. Recommend: PROMOTE or ARCHIVE
   - PROMOTE if the pattern is genuine, not yet captured in wiki, and actionable
   - ARCHIVE if already addressed, superseded, or not actionable
5. For PROMOTE recommendations: write a draft wiki concept or note what the /wiki write should cover
6. For ARCHIVE: note why (one sentence)

## Output

A table:
| # | Dream | Pattern | Status | Recommendation | Reason |

Followed by: for each PROMOTE, a 3-4 sentence draft of what the wiki concept should capture.

The operator makes the final PROMOTE/ARCHIVE decision.

## Acceptance criteria

1. All 7 dreams read and evaluated
2. Each has a clear PROMOTE or ARCHIVE recommendation with reason
3. PROMOTE items have draft wiki concept summaries

## Claim

```powershell
python ~/.grok/skills/handoff/__lib/claim_handoff.py P:/docs/handoffs/dream-triage-20260805/HANDOFF.md --session $env:GROK_SESSION_ID --host grok
```
