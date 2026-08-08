---
thread_id: grok-enforcement-cold-start-20260807
parent_handoff_path: P:/docs/handoffs/agentic-sdlc-control-plane-design-20260807/HANDOFF.md
produced_at: 2026-08-07
status: open
handoff_type: cold-start-briefing
accurate_as_of_grok_head: 6ad018646c5878dc5bf329a6f621c9c6634c8c4f
implemented_slice_commit: c97837f
---

# Cold-start briefing: Grok enforcement control plane

## Objective

Continue the staged hardening of Grok Build's enforcement surface so that
workflow phase, verification, and integration authority are machine-checkable.
The immediate work is the shipping-path slice; the longer-term target is a
Grok-native mutation broker and host-adapted control plane.

This handoff is a briefing and continuation packet. It does not authorize
global config changes, ACL/sandbox changes, API quota use, authentication,
push, merge, or deployment.

## Current status

**PARTIAL - first slice implemented and verified; broader authority work not
started.**

Implemented in `c97837f`:

- Updated the stale receipt test from `<LLM:...>` to the current `<DISPLAY:...>`
  contract in `C:/Users/brsth/.grok/skills/ship-rhai/tests/test_ship_receipt.py`.
- Added a subprocess-level test for the live phase hook at
  `C:/Users/brsth/.grok/hooks/scripts/tests/test_ship_phase_gate.py`.
- The focused suite passed: `69 passed`.
- Ruff passed for the changed test files.

The current shared checkout is not clean. At handoff creation:

- repository: `C:/Users/brsth/.grok`
- branch: `main`
- current head: `6ad018646c5878dc5bf329a6f621c9c6634c8c4f`
- `c97837f` is an ancestor, not the current head;
  `6ad0186` was committed by another concurrent workstream.
- dirty paths observed: 87

Never reset, clean, stash, checkout, or overwrite this checkout to make it
appear clean.

## Why this work exists

The reviewed Grok session had strong written rules but moved from handoff
cleanup into architecture and implementation without a durable phase boundary.
The important failure class was policy without active authority:

- preflight and source/caller discovery were advisory rather than mandatory;
- Claude-side authority plugins were not active in Grok Build;
- receipt and lint hooks ran after mutation and fail open on errors/timeouts;
- the model could make writes, deletes, Git operations, and external calls
  without one path-scoped mutation capability;
- passing focused tests was treated as stronger evidence than live routing and
  runtime activation.

The long-term design is described in:

- `P:/docs/handoffs/agentic-sdlc-control-plane-design-20260807/HANDOFF.md`
- `P:/docs/handoffs/greenfield-enforcement-layer-grok-build-2026-08-04/HANDOFF.md`

Those documents are design inputs, not proof that the proposed broker exists.

## Live runtime facts

Read `C:/Users/brsth/.grok/active-surface.last.md` before making activation
claims. It was generated at `2026-08-07 22:28:47 UTC`.

Verified active pieces include:

- `~/.grok/hooks/ship-phase-gate` on `run_terminal_command`;
- `C:/Users/brsth/.grok/hooks/PreToolUse_ship_phase_gate.py`;
- quality-gate mutation/verification receipt hooks;
- `PreToolUse_verify_before_write.py` for a narrow class of external-sourced
  config constants;
- `/ship-py` and `/ship-rhai` phase orchestration.

Important limits:

- `claude.hooks` is OFF in the active Grok surface;
- the `cc-aca-*` authority/epistemic/investigation hook chain is not firing;
- the phase hook blocks only `git push` during `review` or `verify`;
- `PreToolUse_ship_phase_gate.py` explicitly fails open for missing/corrupt
  state, parse errors, and unresolved session identity;
- `quality_gate.py` defaults to receipt mode `shadow` unless
  `GROK_RECEIPT_GATE_MODE` is explicitly set;
- no universal mutation broker has been verified in the live path;
- no OS/worktree sandbox has been verified as the governing enforcement layer.

## Start here

Read these in order:

1. This file.
2. `P:/docs/handoffs/agentic-sdlc-control-plane-design-20260807/HANDOFF.md`.
3. `P:/docs/handoffs/greenfield-enforcement-layer-grok-build-2026-08-04/HANDOFF.md`.
4. `C:/Users/brsth/.grok/active-surface.last.md`.
5. The implementation and tests:
   - `C:/Users/brsth/.grok/hooks/PreToolUse_ship_phase_gate.py`
   - `C:/Users/brsth/.grok/hooks/ship-phase-gate.json`
   - `C:/Users/brsth/.grok/skills/ship-py/__lib/ship_orchestrator.py`
   - `C:/Users/brsth/.grok/skills/ship-rhai/__lib/ship_receipt.py`
   - `C:/Users/brsth/.grok/hooks/scripts/tests/test_ship_phase_gate.py`
   - `C:/Users/brsth/.grok/skills/ship-rhai/tests/test_ship_receipt.py`

Then run, read-only:

```powershell
git -C C:/Users/brsth/.grok status --short
git -C C:/Users/brsth/.grok log -8 --oneline --decorate
python -m pytest C:/Users/brsth/.grok/hooks/scripts/tests/test_ship_phase_gate.py -q
$env:PYTHONPATH = 'C:/Users/brsth/.grok/hooks/scripts;C:/Users/brsth/.grok/skills/ship-rhai/__lib;C:/Users/brsth/.grok/skills/ship-py/__lib'
python -m pytest C:/Users/brsth/.grok/hooks/scripts/tests/test_ship_phase_gate.py C:/Users/brsth/.grok/skills/ship-rhai/tests/test_ship_receipt.py C:/Users/brsth/.grok/skills/ship-py/tests/test_ship_orchestrator.py -q
```

Expected focused result at the time of this handoff: `69 passed`. A different
result is a new finding; do not overwrite the tests to restore the number.

## Worktree and write boundary

The shared checkout is dirty. Before any implementation:

1. Record `git status --short` and the current head.
2. Identify whether the intended files are already modified by another agent.
3. If the write scope overlaps dirty paths, stop and report the collision.
4. Otherwise create an isolated worktree from the current head, or obtain an
   explicit parent decision to edit the shared checkout.

Allowed first-slice files (already committed):

- `hooks/scripts/tests/test_ship_phase_gate.py`
- `skills/ship-rhai/tests/test_ship_receipt.py`

Do not modify these without a new, explicit scope decision:

- `C:/Users/brsth/.grok/AGENTS.md`
- `C:/Users/brsth/.grok/config.toml`
- active hook registration files outside the named slice;
- ACL/sandbox/security settings;
- production databases, API credentials, browser state, or quota settings;
- unrelated dirty files in the `.grok` checkout.

## Remaining phases

### Phase 1 - Preserve and re-verify the implemented slice

Objective: confirm the commit and live registration still match the current
runtime.

Allowed: read-only status/log/config inspection and the focused tests above.

Stop if: target files are dirty, the active surface is stale after a config
change, or the controlled gate test no longer passes.

Exit evidence: command output, current head, active-surface timestamp, and a
statement distinguishing test behavior from live hook activation.

### Phase 2 - Receipt-authority decision

Objective: determine whether and how to move `quality_gate.py` from `shadow` to
an authoritative mode.

Do not change the default in the shared environment automatically. First add a
controlled live test for a missing/stale verification receipt and document the
failure/timeout behavior.

Parent decision required: choose `shadow`,
`receipt_authoritative_with_old_fail_safe`, or `receipt_authoritative`, and
define the rollback condition.

### Phase 3 - Mutation-authority design

Objective: design a general capability/lease that covers path writes, deletes,
Git, databases, network/API calls, and integration actions.

Use the existing design handoff as the starting point. Do not jump directly to
a large broker implementation. Specify manifest fields, issuer authority,
scope matching, expiry, invalid-state behavior, audit records, and the
fail-closed boundary first.

Stop if the proposal cannot distinguish requested authority from granted
authority, or if it relies only on model compliance.

### Phase 4 - Broker MVP and adversarial verification

Only after Phase 3 is accepted:

- implement in an isolated worktree;
- test out-of-scope writes, destructive Git, quota/network calls, missing
  broker state, malformed input, timeout, and concurrent sessions;
- verify the active Grok registration and a controlled live deny/re-entry test;
- run `/review` or the equivalent code-review skill before integration.

No automatic push, merge, ACL change, or production activation is implied.

## Acceptance criteria for the next agent

The next agent may report `ready_for_parent_review` only when:

- the current dirty worktree was preserved;
- every changed file has a declared owner and scope;
- focused tests pass and at least one controlled live hook test passes;
- active-surface evidence proves the intended hook is loaded;
- receipt mode and fail-open/fail-closed behavior are explicitly recorded;
- the claim ledger separates verified facts from inferences;
- no general broker or production enforcement claim is made without a live
  registration and deny-path receipt.

Otherwise report `partial`, `needs_fix`, or `blocked` with the exact next
command.

## Parent decisions still required

1. Should receipt authority be enabled globally, or only per ship workflow?
2. Should the mutation broker be built as a Grok-native hook/broker, a process
   supervisor, or a worktree/ACL service with a thin hook adapter?
3. What operations require explicit parent approval: API quota, auth, delete,
   stage/commit, push, merge, and live benchmark?
4. Which dirty worktree paths belong to the current concurrent workstreams?

## Handoff state

- Decision: the shipping path has a tested phase gate; general enforcement is
  still partial.
- Files changed by the preceding slice: two test files only.
- Verification: `69 passed`; Ruff passed.
- Current repository state: shared checkout dirty; do not clean it.
- Next recommended action: Phase 1 re-verification, then a parent decision and
  controlled test for receipt-authority mode.
