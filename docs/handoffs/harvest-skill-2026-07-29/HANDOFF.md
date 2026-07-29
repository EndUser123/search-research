# Handoff: /harvest skill implementation

**Session:** 2026-07-28 to 2026-07-29
**Status:** Shipped — 6 commits, 72/72 tests, 21/21 crash tests, ruff F-clean
**Skill path:** `~/.grok/skills/harvest/`

## What was built

`/harvest` is an event-sourced value-tracking skill for recovering unrealized
obligations — work already produced but not yet collected. Distinct from `/todo`
(which chooses work to undertake) and `/handoff` (which is continuation).

### Architecture
- **Event store** (`store.py`): one immutable JSON file per event, ULID-based,
  parent-linked causal chains, claim files for parent-level arbitration
- **CLI** (`harvest.py`): show, add, capture, arm, verify, collect, mark-retire,
  keep, close, reopen, supersede, doctor
- **Storage** at `P:/.data/harvest/`: events/, claims/, pending/, quarantine/

### Key design decisions
1. **Publish-before-claim ordering** — event is published FIRST, then claim
   attempted. Eliminates orphan-claim crash window. Reducer falls back to ULID
   sort if claim missing.
2. **os.replace atomicity** — events written to pending/ + fsync, then
   atomically renamed to events/. NOT O_EXCL (which broke torn-read atomicity).
3. **Claim is per-parent-head** — not per-event-type. Two siblings of any type
   racing on the same head: exactly one wins via O_CREAT|O_EXCL.
4. **`claimed` field is CLI hint** — on-disk value is placeholder True. Claim
   file is authoritative. Reducer ignores the event's claimed field.

## Commit history

| Commit | Description |
|--------|-------------|
| `21f92d7` | Original implementation (8 review corrections applied) |
| `d71d5aa` | F401 fix (unused import) |
| `920ec3b` | Crash-recovery fix (publish before claim + fsync + ULID validation) |
| `f547572` | 6 fixes (O_EXCL, error distinction, warnings, conflict detail, doctor metrics) |
| `9c56cdc` | Structural refactor (revert C4, fix docs, DRY, capture, observability) |
| `47637b8` | Capture tests + SKILL.md routing + seed 3 items |

## Verification performed

- Independent 11-section verification audit (§1-§11)
- Verdict: PASS_WITH_NONBLOCKING_GAPS after fixes
- 3× consecutive full suite runs (72/72)
- 21 crash acceptance tests on real P:\ NTFS
- 2× /review runs (initial + post-fix regression check)
- /refactor dry-run + execution

## Known gaps (non-blocking)

| Gap | Section | Impact |
|-----|---------|--------|
| G1 | §7 | Shell contract: only shell=True (cmd.exe), no pwsh/cmd mode dispatch |
| G2 | §8 | schema_version is metadata only — no dispatch/validation |
| G6 | §6 | Race coverage matrix (6 scenarios) not executable-tested |
| G7 | §4 | No claim cleanup mechanism |

## Seeded items (3)

1. Claim→publish ordering in concurrency primitives (GENERALIZE, recurrences=2)
2. Narrative sufficiency substituting for verification (GENERALIZE, recurrences=3)
3. One-error-class quarantine data loss (GENERALIZE, recurrences=1)

## Next steps for a future session

- Wire `/why` → `harvest capture` auto-suggestion when cross-session patterns found
- Add `harvest compact` subcommand for old conflict events (G7)
- Run the 6-scenario race matrix (§6) — low risk but spec-required
