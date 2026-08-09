# Overnight Run Report

- Run: yt-is-offline-autonomous-overnight-pi2-20260808
- Status: failed
- Updated: 2026-08-08T05:25:47.434Z
- Run count: 4

## done
- implementation: completed
- adversarial-review: completed

## partial
- local-verification: failed - {"failure_class":"nonzero_exit","exit_code":1,"artifact_failures":[]}

## blocked
- none

## not started
- none

## Guardrails
- Completed phases are not replayed unless their state or receipts are manually replaced.
- Auth, quota, external network, live benchmark, destructive, commit, and push capabilities require explicit manifest authorization.
- This runner is an orchestration boundary, not an OS sandbox; commands must still be trusted and isolated by the operator.
