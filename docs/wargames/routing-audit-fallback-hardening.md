---
mission_id: routing-audit-fallback-hardening
title: Harden CCR fleet fallback behavior with audit-evidence guarantees
executor: any (model-agnostic)
domain: software
status: draft-v1
wargame_skill_version: 1.0
---

# Wargame: CCR fleet fallback hardening

## Mission doctrine

This is a **wargame, not an execution plan.** Every move below declares what
an executor should observe on success and on failure, the most likely failure
mode, the signals that distinguish it, the countermove, branch triggers, and
an abort condition. A downstream executor (Claude, Grok, Codex, or a local
model) should be able to run any move and know what to look for, when to
branch, and when to stop — without re-deriving the plan.

The forcing function for this wargame: the CCR fleet
(`P:/.claude/provider-configs/`) is the routing layer for multi-provider LLM
access on this host. Failures here are **high-blast-radius** (every downstream
session loses model access) and **hard-to-attribute without evidence** (was it
the provider, the admission proxy, the router, or the supervisor?). The
current state has fallback logging (`ccr-fallback-log.ps1`) and a request
ledger (`ccr-request-ledger.js`); the open question is whether fallback
*behavior* and *audit evidence* are coupled tightly enough that any future
failure is reproducible from artifacts alone.

## System under wargame (ground truth from recon)

Files observed in `P:/.claude/provider-configs/`:

| File | Probable role | Verified? |
|---|---|---|
| `cc-ccr.ps1` | Unified launcher (CCR + admission proxy + supervisor) | Inferred from AGENTS.md |
| `ccr-admission-proxy.js` | Admission proxy (request gatekeeping) | Inferred from name + integration test |
| `ccr-custom-router.js` | Routing logic | Inferred from name + test |
| `ccr-request-ledger.js` | Request audit trail | Inferred from name + test |
| `ccr-fallback-log.ps1` | Fallback event logging | Inferred from name |
| `ccr-route-metadata.js` | Route metadata (per-provider) | Inferred from name |
| `ccr-context-shaper.js` | Request context transformation | Inferred from name + test |

**Unverified:** actual fallback ordering, ledger schema, what counts as an
"auditable" event, whether the supervisor auto-respawns the dashboard (per
AGENTS.md note: it does not reliably).

## Preconditions (must be true before Move 1)

- CCR fleet is currently running and reachable via `cc-ccr.ps1`.
- At least two providers are configured (so fallback is meaningful).
- The request ledger is being written to on every request, not just failures.
- No other agent is actively editing `provider-configs/` (multi-stream guard).

---

## Move 1: Establish baseline evidence — capture a known-good trace

- **Goal:** Prove the current audit trail is sufficient to reconstruct a
  request end-to-end. If it isn't, every later move inherits the gap.
- **Preconditions:** CCR running; ledger file path known.
- **Action:** Send one canonical test request through the admission proxy.
  Capture: the request payload, the route chosen, the provider response, the
  ledger entry written, the fallback-log entry (if any), and the route
  metadata applied. Do not change any code.
- **Observe if success:** All five artifacts exist and can be correlated by a
  single request-id (or equivalent). Timestamps are monotonic across the
  chain. The ledger entry names the provider, the route, and the outcome.
- **Observe if failure:** One or more artifacts is missing, or they cannot be
  correlated by a shared id.
- **Most likely failure:** The ledger writes on completion but not on
  admission, so a request that hangs between admission and completion has no
  ledger trace.
- **Failure signals:** Ledger row count < expected; missing request-id field;
  timestamp gaps > expected request latency.
- **Countermove:** If the ledger is missing admission-time entries, that
  becomes a dedicated finding — flag for Move 4 (do not fix inline).
- **Branch triggers:**
  - If all five artifacts correlate cleanly → skip Move 4's "ledger schema"
    sub-investigation; focus on fallback behavior.
  - If artifacts do not correlate → Move 4 becomes the critical path.
- **Abort condition:** Cannot send a test request at all (CCR unreachable,
  no provider responds). Classify as environment blocker; do not proceed to
  code changes.

---

## Move 2: Inject a synthetic provider failure during a live request

- **Goal:** Observe what fallback *actually* does today, before any change.
  The wargame's core question lives here.
- **Preconditions:** Move 1 baseline captured; ability to force one provider
  to fail without breaking the others (e.g., point one route at an invalid
  endpoint, or revoke its key temporarily).
- **Action:** With one provider forced to fail, send the same canonical
  request. Capture the same five artifacts plus the fallback-log output.
- **Observe if success:** Fallback occurs; the request completes via the
  secondary provider; the ledger records *both* the failed attempt and the
  fallback attempt; the fallback-log names the failure cause.
- **Observe if failure:** Request fails entirely, OR succeeds but with no
  record that a fallback occurred.
- **Most likely failure:** Silent fallback — the request completes but the
  ledger records only the successful provider, erasing the failure from the
  audit trail. This is the highest-risk finding because it makes future
  root-cause analysis impossible.
- **Failure signals:** Ledger has one row for a request that the fallback-log
  shows involved two providers; or fallback-log is empty despite a failure
  being forced.
- **Countermove:** If silent fallback is observed, Move 3's scope expands
  from "harden behavior" to "couple behavior to evidence." Do not proceed to
  Move 5 (rollout) until this is resolved.
- **Branch triggers:**
  - If fallback is fully evidenced → Move 3 is a polish pass, not a redesign.
  - If fallback is silent → Move 3 must define an "auditable fallback"
    invariant and implement it.
  - If fallback doesn't occur at all (request just fails) → Move 3 must first
    establish *whether* a fallback chain exists, before hardening anything.
- **Abort condition:** Forced failure bricks the entire fleet (supervisor
  dies, dashboard dies, no provider recovers). Roll back the forced failure
    immediately; classify as "fallback misconfiguration caused cascade."

---

## Move 3: Define and implement the auditable-fallback invariant

- **Goal:** Every provider switch must produce a ledger entry naming the
  failed provider, the cause, the fallback chosen, and the rationale. No
  silent fallbacks. No successful requests that hid a failure.
- **Preconditions:** Move 2 produced a concrete observation of current
  behavior (whether good or bad).
- **Action:** Add the invariant as a contract in `ccr-custom-router.js` (or
  wherever the fallback decision is made), with the ledger write occurring
  *at the moment of fallback decision*, not after completion. Add a test that
  asserts the ledger entry exists whenever the fallback-log entry exists.
- **Observe if success:** Test passes; manual replay of Move 2 now produces
  the correlated ledger+fallback-log pair.
- **Observe if failure:** Test passes in isolation but fails under concurrent
  load (race between fallback decision and ledger write).
- **Most likely failure:** The ledger write is async and the fallback-log is
  sync (or vice-versa), so under load the two diverge.
- **Failure signals:** Test passes serially; flaky under parallel runs;
  ledger row timestamps drift behind fallback-log timestamps.
- **Countermove:** Make both writes sync (or both async with a shared
  correlation id written atomically). Prefer the latter for throughput.
- **Branch triggers:**
  - If the invariant already holds after Move 2 → Move 3 reduces to adding
    the regression test, not changing behavior.
  - If the ledger write path is the bottleneck → consider the atomic
    `.tmp` + `os.replace` pattern from CLAUDE.md "Atomic JSON Writing."
- **Abort condition:** Implementing the invariant requires touching the
  admission proxy contract (not just the router). Stop and write a separate
  wargame for the admission-proxy change — do not expand scope mid-move.

---

## Move 4: Verify the audit trail reproduces the failure

- **Goal:** A second person (or model) who did not see Move 2 should be able
  to read the artifacts alone and correctly reconstruct what happened.
- **Preconditions:** Move 3 complete; fresh forced-failure run.
- **Action:** Hand the artifacts (ledger, fallback-log, route metadata) to a
  fresh context with no other information. Ask: "what failed, when, and why?"
  Compare their answer to ground truth.
- **Observe if success:** The reader's reconstruction matches ground truth on
  all three questions.
- **Observe if failure:** The reader can identify *that* something failed but
  not *why*; or can identify *why* but misattributes *which provider*.
- **Most likely failure:** Cause is recorded as a generic category ("timeout")
  rather than a specific signal ("TCP RST after 30s with 0 bytes received").
- **Failure signals:** The "cause" field is one of a small enum rather than
  a structured object; the reader asks clarifying questions instead of
  answering.
- **Countermove:** Expand the cause schema to include signal, latency, byte
  count, and provider-side error code where available.
- **Branch triggers:**
  - If reconstruction matches on all three → audit-evidence guarantee met;
    proceed to Move 5.
  - If only *which* and *when* match but *why* doesn't → loop back to Move 3
    and tighten the cause schema, then re-run Move 4.
- **Abort condition:** Reader cannot even identify *that* a failure occurred
  from the artifacts. This means Move 3 didn't land; do not proceed to
  rollout.

---

## Move 5: Roll out under live multi-stream conditions

- **Goal:** Confirm the hardening holds when multiple agents/sessions are
  using the fleet simultaneously, not just under synthetic test.
- **Preconditions:** Moves 1–4 green; no other stream actively editing
  `provider-configs/`.
- **Action:** Roll the change forward via the standard launcher
  (`cc-ccr.ps1`). Run for a bounded observation window (e.g., 30 minutes)
  with at least one forced failure injected mid-window.
- **Observe if success:** Live requests continue to route correctly; the
  injected failure produces the expected ledger+fallback-log pair under live
  load; no dashboard child deaths; no supervisor respawn issues.
- **Observe if failure:** Performance regression (latency spike from sync
  ledger writes), OR dashboard child dies and does not respawn, OR ledger
  write errors under contention.
- **Most likely failure:** The dashboard child dies under load (per AGENTS.md
  note: this has happened before and the supervisor does not reliably
  respawn).
- **Failure signals:** Dashboard window missing; supervisor log shows child
  exit; users report "no dashboard" but routing still works.
- **Countermove:** If routing still works and only the dashboard is dead,
  treat the dashboard issue as a separate finding (it pre-exists this
  change). If routing is degraded, roll back via `cc-ccr.ps1` restart with
  the previous config.
- **Branch triggers:**
  - If only the dashboard dies → file a separate finding, do not roll back
    the hardening.
  - If routing degrades → roll back immediately; the sync write path is the
    suspect.
  - If supervisor itself dies → this is a critical regression; roll back and
    write a new wargame scoped to supervisor stability.
- **Abort condition:** Any data loss in the ledger (entries dropped under
  load). Roll back; the invariant is violated; do not ship.

---

## Refinement pass notes (applied to this draft)

- **Move 1 + Move 4 are deliberately symmetric:** establish baseline →
  verify reproduction. This is intentional — the value is in the closure, not
  the individual moves.
- **Second-order consequence addressed in Move 3:** sync-vs-async ledger
  writes as a flaky-test source under concurrency.
- **Third-order consequence addressed in Move 5:** dashboard child death is
  pre-existing (per AGENTS.md) but surfaces under any change to the fleet —
  the branch trigger prevents misattributing it to this change.
- **Cosmetic branches removed:** originally had a Move 6 for "document the
  new schema." That is not a separate move; it is part of Move 3's
  implementation. Removed.
- **Abort conditions tightened** to specific observables (unreachable CCR,
  silent fallback, scope creep into admission proxy, ledger data loss)
  rather than "if something seems wrong."

---

## Unresolved (must be answered before execution)

These are the gaps this wargame surfaced. They are the wargame's primary
output — proof the method works.

1. **`{{ledger_file_path}}`** — where does `ccr-request-ledger.js` actually
   write? Need to read the source to ground Move 1's artifact capture.
2. **`{{fallback_order}}`** — is fallback ordering declared in
   `ccr-route-metadata.js`, in `ccr-custom-router.js`, or in a config file?
   Determines where Move 3's invariant lives.
3. **`{{admission_proxy_contract}}`** — what does `ccr-admission-proxy.js`
   guarantee about request-id assignment? Determines whether Move 1's
   correlation-by-id is even possible today.
4. **`{{supervisor_respawn_behavior}}`** — does the supervisor auto-respawn
   the dashboard child? AGENTS.md says "did not auto-respawn" in a prior
   session; need to confirm current state before Move 5's branch trigger is
   trustworthy.
5. **`{{existing_test_coverage}}`** — what do
   `ccr-admission-proxy.integration.test.js`, `ccr-custom-router.test.js`,
   and `ccr-request-ledger.test.js` already cover? Determines whether Move 3
   adds a new test or extends an existing one.

## Falsifier for this wargame

This draft earned its keep if resolving the five Unresolved items changes at
least one move's actions or abort conditions. If all five resolve trivially
with no change to the moves, the system was simpler than it appeared and the
wargame was over-engineered — narrow the trigger thresholds in
`~/.grok/skills/wargame/SKILL.md`.
