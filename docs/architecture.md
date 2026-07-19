# AI Lane Controller — Architecture

## Purpose

A minimal Windows-first local service/library that enables a single
controller Claude Code session to coordinate up to eight isolated
worker lanes. Each lane contains a web/ChatGPT session and a separate
PowerShell 7 terminal running Claude Code.

**This is NOT an agent framework.** There is no autonomous reasoning, model
routing, browser automation, MCP, or Claude-specific coupling beyond the
Claude Code transport mechanism.

Control-plane primitives:

  - lane identity
  - durable message contracts
  - routing isolation
  - audit trail
  - recovery behavior
  - lane claiming (M2 — binds a live process to a lane identity)
  - process liveness verification (M3A)
  - terminal/session/workspace identity and fencing epochs (M4)
  - multi-lane registry (M5 — lane-01 through lane-08)
  - controller identity and command validation (M5)
  - per-lane handoff queues and UI-input mutex (M5)
  - capability-attestation window binding (M5)

---

## Proven vs unproven behavior

| Capability | Status | Evidence |
|---|---|---|
| Lane claim with PID, nonce, start time, fencing | **PROVEN** | 15 M2 tests + 18 M4 fencing tests |
| Process liveness validation via kernel32 | **PROVEN** | 10 M3A tests |
| Terminal/workspace/session identity isolation | **PROVEN** | 18 M4 tests |
| Atomic claim-file writes | **PROVEN** | M4 tests: `test_atomic_write_*` |
| Eight-lane registry (lane-01..lane-08) | **PROVEN** | 3 M5 registry tests |
| Controller identity, epoch, idempotency keys | **PROVEN** | 7 M5 controller tests |
| Per-lane serialized handoff queues (in-memory) | **PROVEN** | 6 M5 scheduler tests |
| UI mutex (filesystem lock, cross-process, PID+start-time validation) | **PROVEN** | 6 mutex tests including real subprocess |
| `[Console]::Title` capability attestation | **PROVEN** | Binding challenge experiment (PASS) |
| HWND enumeration + unique binding | **PROVEN** | Binding challenge experiment |
| Stale/nonce/epoch mismatch rejection | **PROVEN** | M4 fencing + M5 controller tests |
| Clipboard set + hash verification | **PROVEN** | Experiment verified SHA-256 |
| Window activation from separate controller | **UNPROVEN** | Last attempt blocked by foreground lock + re-entrancy |
| AHK delivery from separate controller process | **UNPROVEN** | `general-delivery.ahk` written but not executed from controller window |
| Two-lane live acceptance (distinct prompts, distinct ack) | **UNPROVEN** | Requires interactive controller window |
| Persistent queue durability across restart | **NOT IMPLEMENTED** | Scheduler/LaneQueue are memory-only |
| Browser automation, ChatGPT upload, correction loops | **OUT OF SCOPE** | Explicit exclusions |

---

## Package layout

```
tools/ai_lane_controller/
  __init__.py         Public API exports (M1-M5)
  registry.py         Lane registry + create_standard_lanes() (M1, M5)
  messages.py         Message contract — lane-message.v1 (M1)
  router.py           Local routing — verify, create, log (M1)
  storage.py          Filesystem persistence — survive restart (M1)
  recovery.py         Recovery — pending, acknowledge, recover (M1)
  claim.py            Lane claiming, fencing, liveness (M2, M3A, M4)
  controller.py       Controller identity + command validation (M5)
  scheduler.py        UIMutex, LaneQueue, Scheduler (M5)

tests/ai_lane_controller/
  test_lane_identity.py        19 tests (M1)
  test_message_routing.py      11 tests (M1)
  test_recovery.py              7 tests (M1)
  test_claim.py                15 tests (M2)
  test_claim_routing.py         5 tests (M2)
  test_liveness.py             10 tests (M3A)
  test_fencing.py              18 tests (M4)
  test_multilane.py            16 tests (M5)
  test_mutex.py                 6 tests (M5 multi-process)

docs/
  architecture.md              This file
```

---

## Storage layout

```
P:\.ai-lanes\
  lanes\<lane_id>\sessions\<lane_session_nonce>\
    claim.json
    window-binding.json
    events.jsonl
    commands\
    handoffs\<handoff_id>\

  controller\sessions\<controller_session_id>\
    identity.json
    commands\
    events.jsonl
```

All readers must receive exact identifiers and paths. Never discover current
state through globbing, newest-file logic, or modification time.

---

## Milestones

### M1 — Message artifacts

- Lane registry (`lane-a`, `lane-b`)
- `lane-message.v1` contract
- Filesystem storage under `.ai-lanes/`
- Router with fail-closed validation
- Append-only event log
- Recovery for pending messages

### M2 — Lane claims

- `claim_lane()` binds a process to a lane
- Identity: `lane_id`, `session_nonce`, `pid`, `process_start_time`, `created_at`, `heartbeat_at`
- Filesystem `claim.lock` with exclusive-create mutual exclusion
- Router validates claim nonce before message submission

### M3A — Process liveness

- `verify_process_liveness()` via kernel32 `GetProcessTimes`
- Detects dead PID (`process_not_found`) and PID reuse (`pid_recycled`)
- Heartbeat refreshes stale claim
- Router rejects dead/recycled claim before routing

### M4 — Terminal isolation and fencing

- Claims carry `terminal_id`, `session_id`, `workspace_id`, `fencing_epoch`
- Writer identity validation before heartbeat, release, replacement
- Stale writers rejected via epoch, nonce, terminal, session, workspace checks
- Atomic writes: temp file + `os.replace()` — readers never see partial JSON
- Lock reclamation requires verifiable dead holder

### M5 — Multi-lane controller foundation

- Eight explicit lane slots (`lane-01` through `lane-08`)
- Controller identity: `controller_session_id`, `controller_claim_nonce`, fencing epoch, PID, workspace
- Controller commands carry `command_id`, `idempotency_key`, target lane, expected epoch
- Validation rejects stale epochs, wrong sessions, duplicate idempotency keys, invalid lanes
- `LaneQueue`: one active handoff per lane, concurrent across lanes
- `UIMutex`: cross-process filesystem lock with PID + process-start-time validation
- `general-delivery.ahk`: HWND activation, clipboard paste, Enter — reads authorization artifact
- Stale-state rejection: wrong nonce, wrong epoch, expired binding, duplicate HWND all fail closed

---

## Authority chain

```
Controller Claude (session_id, nonce, epoch)
    │
    ├── issues ControllerCommand (validated by identity fields)
    │
    ▼
Local controller process (UIMutex, per-lane queue)
    │
    ├── validates command: session match, nonce match, epoch ≥ current,
    │                     idempotency key unique, target lane valid
    ├── acquires UI mutex (machine-wide, cross-process)
    ├── revalidates target lane claim + epoch
    ├── activates exact bound HWND
    ├── verifies GetForegroundWindow() matches
    ├── pastes (reverify foreground)
    ├── Enter (reverify foreground)
    ├── releases UI mutex
    └── waits for acknowledgement at exact handoff path
    │
    ▼
Target lane (lane-01..lane-08, claim, epoch, binding)
```

---

## Identity binding (not cryptographic signing)

Controller commands carry **identity fields validated at enforcement time**:
`controller_session_id`, `controller_claim_nonce`, `controller_fencing_epoch`.
There is no cryptographic signature on commands. Authority is proven by:
1. Matching session/nonce/epoch against the authoritative identity artifact.
2. Rejecting older epochs (fencing), duplicate idempotency keys, and
   foreign session/workspace IDs.

---

## Window binding

The capability-attestation pattern:

1. Target lane generates a fresh random binding challenge.
2. Lane's console-attached PowerShell sets `[Console]::Title` to
   `AI-LANE-BIND-<full_random_challenge>`.
3. Lane writes a session-scoped binding attestation.
4. External controller requires exactly one exact title match.
5. Controller records the HWND.
6. Every delivery revalidates claim, epoch, nonce, title, expiry, HWND, uniqueness.

This is proven by live experiment. The binding proves the lane
possesses both its filesystem-bound claim state and the unique visible
challenge title — it does not prove a direct ConPTY-to-HWND mapping.

---

## UI mutex

`UIMutex` is machine-wide: uses a filesystem lock file with NTFS-atomic
exclusive-create (`open("x")`). The lock file records PID, process start
time, and workspace ID. Stale locks are recovered only when the holder
process is verifiably dead (not by mtime alone). Release requires the
original PID. Cross-process tests confirm isolation.

### Canonical mutex path

The canonical mutex path is `P:/.ai-lanes/controller/locks/ui-input.lock`,
derived from `AI_LANE_ROOT` (always absolute). Callers cannot create two
valid mutex paths — different CWDs resolve to the same absolute path.
A call to `UIMutex()` with no argument always resolves to the canonical
path. Override via `UIMutex(path=...)` is supported but the non-canonical
path will not be recognized by default controllers.

### Workspace enforcement

The lock file carries a `workspace_id` derived from the SHA-256 hash of
`AI_LANE_ROOT`. Any mutex acquisition that finds a lock with a mismatched
`workspace_id` raises `SchedulerError("workspace mismatch")`. This prevents
cross-project lock confusion. Verified by mutation testing
(skip_mutex_workspace mutant killed).

---

## Scheduling and Durable Commands

`Scheduler` is the durable command authority. Commands (issued by a
`ControllerCommand` with validated session/nonce/epoch identity) are
persisted atomically to `P:/.ai-lanes/controller/sessions/{session_id}/commands/{command_id}/command.json`
via temp-file + os.replace pattern.

### Durable command authority

Every `DurableCommand` carries the issuing controller's session_id,
claim_nonce, and fencing_epoch. The state machine governs transitions
through 12 states:

```
CREATED → VALIDATED → QUEUED → ACTIVE → UI_AUTHORIZED → DELIVERED
  → AWAITING_ACK → VERIFIED
```

Terminal states: `VERIFIED`, `FAILED`, `CANCELLED`, `STALE_REJECTED`.
Recovery state: `RECOVERY_REQUIRES_RECONCILIATION` (for uncertain delivery).

Transition validation is enforced: terminal states never revert to active.
State machine transition map (`_CMD_TRANS`) is verified by mutation testing
(permit_any_transition mutant killed).

### Idempotency semantics

Each command carries an `idempotency_key`. Before accepting a new command,
the scheduler checks for an existing record with the same key in the same
session. Two outcomes:

1. **Same content** (command_hash matches) → duplicate, rejected with
   "duplicate idempotency key" error.
2. **Different content** (hash mismatch) → conflict, rejected with
   "reused with different content" error.

Idempotency files are stored at
`P:/.ai-lanes/controller/sessions/{session_id}/idempotency/{key}.json`.
Both duplicate and conflict checks are verified by mutation testing
(no_idempotency_conflict and no_duplicate_detect mutants killed).

### Active operation ownership

At most one active operation per `(lane, session_nonce)` pair. An attempt
to set a second active operation with a different command_id raises
`SchedulerError`. This is verified by mutation testing
(allow_two_active mutant killed). Previously the guard was silently
swallowed by `except: pass` — corrected to re-raise `SchedulerError`.

### Reconstruction behavior

`Scheduler.reconstruct(lanes, controller_session_id)` scans exactly one
session directory. It does NOT fall back to newest-directory or mtime
heuristics:

- Non-terminal commands are restored to their last persisted state.
- If the command has a handoff_id and the lane queue is idle, the handoff
  is restored (lane marked `DELIVERING` or `AWAITING_OUTPUT`).
- Orphan active-operation records (no matching command file) flag the
  lane as `RECOVERY_REQUIRES_RECONCILIATION`.
- Corrupted artifact files (truncated JSON, empty, missing fields,
  unknown schemas) are skipped gracefully with no crash.
- Foreign session directories do not affect reconstruct results.
- Temporary (.tmp) files from interrupted atomic writes are not read
  as command files.

### Uncertain-delivery recovery

When delivery outcome is uncertain, the state machine enters
`RECOVERY_REQUIRES_RECONCILIATION`. This state must be manually
reconciled (user decides: VERIFIED, FAILED, or CANCELLED). There is
no automatic retry of uncertain delivery. This invariant is verified
by mutation testing.

---

## Live acceptance blocker

The two-lane acceptance test requires a plain PowerShell 7 window acting
as the controller process. This session's Claude Code instance cannot be
both controller and a target lane (re-entrancy). The experiment package
at `P:.data/ai-lane-controller/general-delivery.ahk` and the delivery
authorization/acknowledgement infrastructure are prepared, but execution
requires:

1. Open a new PowerShell 7 window (not a Claude terminal).
2. Run `controller-delivery.ps1` (from the experiment package) or
   manually invoke AHK targeting the bound HWNDs.
3. Keep two Claude Code terminals as target lanes.
4. Keep a third as a foreign isolation control.

This has not been done yet.

---

## Remaining limitations

1. **No browser integration** — ChatGPT session interactions not implemented.
2. **No correction loop** — bounded corrective interaction not implemented.
3. **No MCP** — not yet a safe controller command surface.
4. **Window activation depends on foreground rules** — may require
   interactive user process depending on OS lock state.
5. **No Property-based invariant testing on full scheduler state** —
   Hypothesis stateful tests cover active-op invariants, idempotency,
   and reconstruct, but do not yet exercise the full state machine
   across all 12 states with random sequencing.
6. **Defect found — fixed**: `_set_active_op` had a bug where
   `except: pass` silently caught the `SchedulerError` guard against
   overlapping active operations. Fixed by re-raising `SchedulerError`
   before the bare except.

## Mutation testing results

**Targeted mutation testing** was performed on authority/fencing/
idempotency/mutex surfaces in `controller.py`, `scheduler.py`, and
`claim.py`. Ten critical mutants were applied and verified:

| Mutant | File | Result |
|--------|------|--------|
| Invert controller epoch check | controller.py | KILLED |
| Remove session check | controller.py | KILLED |
| Remove nonce check | controller.py | KILLED |
| Remove idempotency hash conflict | scheduler.py | KILLED |
| Never detect duplicate | scheduler.py | KILLED |
| Permit any state transition | scheduler.py | KILLED |
| Allow two active ops | scheduler.py | KILLED |
| Remove mutex workspace check | scheduler.py | KILLED |
| Invert lane epoch check | claim.py | KILLED |
| No epoch increment | claim.py | KILLED |

**Score: 10/10 KILLED (100%)** on critical authority mutants. Zero
survivors in authority, fencing, idempotency conflict, exclusive mutex,
and no-auto-redelivery logic.

### Test suite composition

- Original suite (113 tests): M1 identity, M2 claims, M3A liveness,
  M4 fencing, M5 multilane/scheduling/controller, durability
- 36 authority/fencing/idempotency/mutex behavioral tests (new)
- 7 multi-process race tests using real OS subprocesses (new)
- 1 Hypothesis stateful machine test with 12 rules (new)
- 16 corrupt/hostile artifact tests (new)
- 8 crash-point tests (all 9 enumerated positions, new)
