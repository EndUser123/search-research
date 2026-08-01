---
thread_id: none
parent_handoff_path: none
current_session_id: none
current_terminal_id: none
produced_at: 2026-07-25T08:10:52-06:00
status: open
handoff_type: implementation
accurate_as_of_head: 42a0203a429ff77dcee1dfd359a6e06622b9300d
---

# HANDOFF — Implement the Instruction-to-State Closure Gap design

## Problem name

**Instruction-to-State Closure Gap (ISCG)**

Root-cause label: **conversation-centric completion**.

## Objective

Design and implement the smallest durable mechanism that connects an explicit
instruction to its required end state, current observed state, owner/session,
and fresh completion evidence. Use a narrow desired-state manifest for stable
runtime configuration and a session-scoped obligation ledger for task-specific
postconditions.

## Status

OPEN — architecture documented; implementation not started by this handoff.

## Read-first list

1. `P:/.data/wiki/concepts/instruction-to-state-closure-gap-obligation-ledger.md`
2. `P:/.data/wiki/concepts/external-state-cross-check-as-structural-fix.md`
3. `P:/.data/wiki/concepts/verification-state-tracking-content-identity-vs-temporal-proxies.md`
4. `C:/Users/brsth/.grok/hooks/scripts/quality_gate.py`
5. `C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py`
6. `C:/Users/brsth/.grok/active-surface.last.md`
7. `C:/Users/brsth/.grok/docs/user-guide/10-hooks.md`

## Verified facts

- The current quality gate is centered on modified-code verification and
  receipt freshness.
- The receipt writer records session-scoped modified files and fingerprints.
- The active-surface snapshot describes configuration observed at SessionStart
  and warns that it can be stale after mid-session changes.
- The current system therefore has evidence and runtime-surface primitives but
  this handoff does not assume it has a generic instruction-obligation schema.
  That absence must be confirmed during implementation preflight.

## Task packets

### ISCG-01: Inventory the smallest missing contract

- **goal:** Determine whether existing receipt, mutation, active-surface, and
  hook-state schemas can represent arbitrary task postconditions.
- **in scope:** read-only schema and caller inventory.
- **out of scope:** changing runtime behavior.
- **acceptance:** document the exact missing fields and the smallest compatible
  extension; identify authoritative paths and generated/cache copies.
- **falsifier:** if existing schemas already support the required lifecycle,
  implement adapters/consumers instead of creating duplicate state.
- **verification:** static inspection plus focused schema tests.

### ISCG-02: Define the obligation ledger

- **goal:** Define a versioned schema with instruction ID, session ID, owner,
  scope, expected state, verifier, evidence fingerprint, timestamps, and
  status (`OPEN`, `SATISFIED`, `BLOCKED`, `SUPERSEDED`).
- **acceptance:** malformed, missing, cross-session, and stale records have
  explicit behavior; status transitions are append-only or otherwise
  recoverable.
- **non-goal:** infer obligations from arbitrary completion prose.

### ISCG-03: Implement observed-state verification

- **goal:** Compare the obligation’s expected state with live configuration and
  active runtime state, rather than trusting a prior snapshot.
- **acceptance:** a removed hook cannot remain `SATISFIED` if it is recreated;
  a missing/malformed verifier result is not success; ownership conflicts are
  visible.
- **falsifier:** a state change after verification is not detected.

### ISCG-04: Integrate completion enforcement

- **goal:** Make the Stop gate consult obligation status and fresh evidence in
  addition to existing code-verification logic.
- **acceptance:** open/stale/blocked obligations prevent completion claims with
  actionable diagnostics; satisfied obligations do not add noise; loop and
  fail-open behavior follow the verified Grok hook contract.
- **non-goal:** replace the existing quality gate wholesale.

### ISCG-05: Add hermetic lifecycle tests

- **goal:** Test hook discovery, block behavior, re-entry/continuation behavior,
  cleanup, and recreation detection in isolated temporary configuration/state.
- **acceptance:** each test records invocation telemetry, observed state,
  decision, and cleanup result; no persistent diagnostic can be mistaken for
  live runtime evidence.
- **falsifier:** the test passes while the real active surface omits the hook or
  while the persistent configuration remains contaminated.

## Proposed acceptance criteria for the whole task

1. An explicit instruction creates or references a durable obligation.
2. The obligation names its scope and verifier.
3. The verifier reads current external state and binds evidence to it.
4. A stale or missing evidence record cannot authorize completion.
5. Recreating a previously removed artifact reopens or fails the obligation.
6. A clean unrelated turn is not blocked.
7. A canary test is isolated and cleanup is independently verified.
8. Existing code-verification behavior remains passing.

## Hard constraints

- Inspect the live source of truth before editing; do not edit caches or stale
  copies.
- Preserve concurrent work in `C:/Users/brsth/.grok` and `P:/`.
- Do not delete diagnostic evidence before it is copied or dispositioned.
- Do not treat direct hook invocation as proof of live Grok invocation.
- Do not make a session-start snapshot the sole current-state authority.
- Do not turn AGENTS.md into a volatile inventory.
- No destructive git operations, staging, or commit without authorization.

## Open decisions

- Exact storage location and ownership boundary for the obligation ledger.
- Whether the stable desired-state manifest covers all hooks or only managed
  Grok-native hooks first.
- Whether the first implementation should use JSONL append-only events plus a
  materialized current-state view, or a transactional single-record format.
- How Stop should behave when the obligation verifier is unavailable: block,
  explicit degraded state, or a separately authorized fail-open mode.

## Explicit non-goals

- Do not redesign all Grok hooks, skills, MCPs, or AGENTS.md in one change.
- Do not build a general Terraform-like reconciler for the whole workstation.
- Do not infer semantic intent from completion language as the primary source.
- Do not claim runtime enforcement until an isolated live test proves it.

## Resumption protocol

1. Read this handoff and the linked wiki concept.
2. Run ISCG-01 against the live Grok artifacts.
3. Produce the schema and state-ownership decision before implementation.
4. Implement the smallest end-to-end obligation path.
5. Run focused tests, then an isolated live hook test.
6. Update this handoff with files changed, evidence, remaining risks, and the
   final disposition.

## Evidence standard

Use the claim ledger format:

`Claim | Type | Evidence | Verification method | Confidence | Falsifier | Action allowed`

Do not promote an inferred architectural gap into a broad rewrite until ISCG-01
confirms the precise missing contract.
