# Review Relay operational contract

The canonical implementation is
`P:\packages\codex-external-delegation\src\review-relay.mjs`, exposed through
`P:\packages\codex-external-delegation\bin\review-relay.mjs`. The Codex and
Grok `review-relay` skills are host adapters for this controller. They do not
duplicate the state machine and they do not spawn models.

## Normal operator interface

The normal invocation is filename-only:

```text
/review-relay P:/docs/designs/proposal.md P:/docs/designs/review-criteria.md
```

The host adapter supplies the current actor (`codex` or `grok`) and calls the
controller's `start-or-join` operation. The operator does not provide a review
ID, artifact root, lease ID, or review prompt. The controller derives a
review key from the input file paths (not content), so editing the proposal
between turns continues the same review session rather than fragmenting into
a new one. The content hash is recorded per-snapshot for audit but does not
determine session identity.

The registry is coordination metadata only:

```text
P:\tmp\review-relay\registry\<input-set-sha256>\<review-id>.json
P:\tmp\review-relay\sessions\<review-id>\...
```

It is not a `LATEST` pointer. Discovery requires an exact input-set hash and a
valid manifest. If more than one active session matches, the controller fails
closed with candidate IDs. If an input's content changes, its hash no longer
matches the old session and it cannot silently attach.

Multiple input files are frozen into a deterministic `review-input-bundle.v1`
snapshot. Single-file snapshots retain their original bytes. Registry and
relay artifacts are controller-owned temporary coordination state; partner
writes remain restricted to the declared relay result scratchpad.

Every successful `start-or-join` response also contains a
`review-relay-handoff.v1` object. Host skills must print its paths in a visible
handoff block:

```text
SEND TO PARTNER:      handoff.send_to_partner.input_paths[]
RECEIVE RESULT:       handoff.receive_from_partner.result_path
RECEIVE RECEIPT:      handoff.receive_from_partner.receipt_path
READ THIS TURN:       handoff.current_turn.read_paths.turn_input
READ PRIOR RESULT:    handoff.current_turn.read_paths.previous_result
WRITE THIS SCRATCHPAD: handoff.current_turn.write_paths.result_input
```

The send list is the exact input path list the other host must pass to its
skill. The receive paths are only authoritative after the controller has
committed the attempt and written its receipt. A missing receive path means
the partner has not claimed a turn yet; it is not permission to search for a
newest result.

## Authority and identity

The operator chooses one unique `artifact_root` per review conversation and
terminal. The controller owns the manifest, proposal snapshot, turn claims,
committed results, receipts, and event records. The partner/model may write
only the active turn's `result-input.json` (and an optional heartbeat through
the controller). No PID, newest-file rule, global `LATEST` pointer, or prompt
text is authoritative.

The durable identity is:

```text
review_id + proposal_revision + turn_id + turn_number + attempt_id + lease_id
```

The actor IDs are normally `codex` and `grok`. Provider, model, harness, and
invocation method belong in the review payload when known; they do not replace
the controller identity. A changed proposal produces a new review ID/root.

## Files and ownership

```text
<artifact_root>/
  manifest.json
  proposal-v1.snapshot
  turns/0001/active/
    claim.json             # controller
    input.json             # controller
    result-input.json      # partner scratchpad
    heartbeat.json         # controller API, when used
  turns/0001/attempt-<attempt_id>/
    claim.json
    input.json
    result-input.json
    result.json             # controller-wrapped payload
    receipt.json            # controller validation receipt
  events/<actor>/<YYYY-MM-DD>/<event_id>.json
  handoff-candidate.v1.json # optional controller scratchpad
```

The registry record is outside `<artifact_root>` because it is the rendezvous
index used by a fresh host. It contains only session identity, input hashes,
actor list, expiry, and artifact-root location; it never contains model output.
The artifact root remains the authority for the manifest, turn state, results,
receipts, and event history.

The snapshot is immutable and its SHA-256 is recorded in the manifest. Every
controller write uses a unique temporary file followed by an atomic rename.
Temporary files are ignored by readers. Final malformed claims/results fail
closed with `needs_review`/malformed error status; they are never guessed or
silently repaired.

Events are immutable, scoped to one review root, partitioned by actor and UTC
date, and retained with the review evidence. This is per-conversation
partitioning rather than a shared append log. There is no automatic deletion
of evidence; an operator may archive or remove a whole expired review root
after its retention decision.

## Result contract

The partner writes one JSON object to the exact `result_input_path` returned by
`tick`:

```json
{
  "status": "submitted",
  "findings": [],
  "claim_ledger": [],
  "unresolved": [],
  "proposed_changes": [],
  "runtime": {"orchestrator": "codex", "harness": "pi"}
}
```

Allowed statuses are `submitted` (continue), `needs_fix`, `partial`,
`blocked`, `failed`, `timed_out`, and `ready_for_parent_review` (terminal).
Use `submitted` for a normal completed partner turn, even when that partner
has no further comments. `ready_for_parent_review` means the relay's
structural convergence gate has been reached: the current result plus
committed results cover every declared actor. The controller rejects an early
terminal result with `premature_terminal_status`; correct the scratchpad to
`submitted` and resubmit before the lease expires. This gate proves turn
coverage, not proposal acceptance or semantic agreement; the parent/user
still makes the final decision.
Findings should distinguish `verified_fact`, `measured_metric`, `inference`,
`hypothesis`, `historical_context`, and `unsupported`. The controller adds
review/manifest/proposal/turn/attempt/lease identity, timestamps, and a
content hash; do not fabricate those fields in the scratchpad.

## Lease and failure behavior

- `tick` claims exactly one expected actor/turn using an expiring lease.
- A concurrent claimant waits; it cannot create a second active attempt.
- A brief half-created active directory is reported as pending. After the
  configured grace period it is preserved as an orphan and the turn can be
  reclaimed with a new attempt ID.
- An expired lease is preserved under `orphaned-<attempt_id>`; it is not
  silently counted as a successful review.
- Repeating the identical submission is idempotent. A different payload for
  the same attempt is `conflicting_duplicate`/`needs_review`.
- Proposal, manifest, actor, turn, attempt, lease, or content-hash mismatch
  stops the affected operation with a stale/identity error.
- `ready_for_parent_review` is rejected until every declared actor has a
  committed turn; `next_turn` is only a counter and never proves that the
  session is still active.
- `converged` is not a partner result status. A caller must not manufacture it
  to bypass the parent-review gate.
- An event-log write failure is returned in the operation/receipt as an audit
  failure but does not convert an already committed result into worker failure.

## Scheduling and handoff

The skill normally invokes `start-or-join` and then performs one bounded turn.
The low-level `tick` command may still be invoked manually for recovery. A
recurring host scheduler must use the controller's `watch` operation rather
than repeatedly calling `start-or-join`:

```text
node P:\packages\codex-external-delegation\bin\review-relay.mjs watch \
  --actor <codex|grok> <the same absolute input paths>
```

`watch` re-reads the exact input files and computes their content hash on every
poll. It attaches to the one matching active session, returns `terminal`
without restarting an unchanged terminal session, and creates a new isolated
session only when the current content hash has not been reviewed before. A
file that is being written is rejected as an unstable capture and can be
retried on the next poll. Multiple matching active or terminal sessions fail
closed; the watcher never chooses a newest directory or `LATEST` pointer.

Each invocation claims at most one bounded model turn. The review is not
limited to a normal six-turn wave: committed `submitted` turns may continue
until a real result reaches the parent-review gate, the manifest expires, or a
worker reports a terminal failure. There is no default turn-count limit.
`--max-turns` is an optional explicit emergency fuse for an operator who wants
one; if that fuse is reached first, the controller returns `partial` with
`reason: "turn_budget_exhausted"`. It never reports `converged` or treats the
review as successful.
New manifests store `max_turns: null`; older manifests with a numeric value
retain that value as an explicit legacy fuse.

Grok Build may use its documented recurring scheduler or `/loop` at a minimum
60-second interval to re-invoke the Grok-side `watch` prompt. Codex uses a
Codex-app heartbeat attached to the current task at the same cadence. The
heartbeat prompt embeds the exact input paths, actor, registry root, and
session root; it must stop immediately on the top-level `terminal` response or
on `blocked`, `needs_fix`, `partial`, `failed`, `timed_out`, `expired`, or
`needs_review`. In particular, a `partial` response with
`reason: "turn_budget_exhausted"` is an incomplete safety stop, not
convergence, and the watcher must not silently restart it. A scheduler does
not prove a model turn completed: it must still require a committed result and
receipt from the controller.

`handoff-candidate` writes only inside the relay root and is allowed only at a
terminal state unless `--allow-checkpoint` is explicit. It never invokes Grok
`/handoff` and never writes `P:\docs\handoffs`. After review, the human may
explicitly invoke Grok `/handoff` with the unique review topic/path.
