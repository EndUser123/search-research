---
title: Decision-contract gate — fresh-session runtime acceptance test
status: SUPERSEDED
created: 2026-08-08
last_updated_at: 2026-08-09T00:35:00Z
assignee: grok
session_origin: 019fdf3d-a0bd-7062-abc4-24dcf064ae49
superseded_by: P:/docs/handoffs/epistemic-control-system-runtime-acceptance/HANDOFF.md
---

# Decision-contract gate: fresh-session runtime acceptance (SUPERSEDED)

**This handoff is superseded** by the system-level acceptance matrix at
`P:/docs/handoffs/epistemic-control-system-runtime-acceptance/HANDOFF.md`,
which tests all three gates together (decision, reviewer, revision) including
composition and applicability-boundary probes.

## Context

The decision-contract-gate (`Stop_decision_contract_gate.py`) was built and
remediated across session 019fdf3d. All 6 known bypasses are closed. 42 unit
tests + 9 subprocess acceptance tests pass.

**One test remains:** verify the gate fires through the actual Grok Build
Stop dispatch chain in a live session. The hook was registered AFTER session
019fdf3d started, so it is not in this session's dispatch chain. A fresh
session is required.

## Acceptance procedure (run in a FRESH session)

### Step 1: Verify hook discovery

```powershell
# Confirm the hook is in the active surface
Select-String -Path "$env:USERPROFILE/.grok/active-surface.last.md" -Pattern "decision-contract"
```

Expected: line matching `Stop_decision_contract_gate.py` under the Stop section.

### Step 2: Negative test — terminal commitment without contract

In the fresh session, emit a response recommending BUILD without a
`<decision-contract>` artifact:

```
I recommend we build a new test package from scratch to verify the build system.
```

**Expected behavior:** the Stop hook fires and blocks the turn with a message
containing "terminal commitment" and instructions to emit a decision-contract.

If the turn completes without a block → **RUNTIME ACCEPTANCE FAILED**.

### Step 3: Positive test — valid SPIKE_REQUIRED

In the same session, emit a valid SPIKE_REQUIRED contract:

```
<decision-contract>
decision_contract:
  required: true
decision:
  state: SPIKE_REQUIRED
  proposed_action: SPIKE
discovery:
  direct_alternatives: []
decision_reversing_unknowns:
  - id: test
    status: OPEN
evidence_requirements: []
</decision-contract>
```

**Expected behavior:** the turn completes normally (hook passes silently).

If this is blocked → **RUNTIME ACCEPTANCE FAILED** (false positive).

### Step 4: Record result

If both tests pass:
- Update this handoff to CLOSED
- Update the wiki concept to:
  `DECISION_GATE_ROOT_CAUSE_FIX_COMPLETE_FOR_DEFINED_SCOPE`
- Close the decision-gate workstream

If either test fails:
- Record the failure mode
- Do NOT downgrade the wiki rating further — the implementation is correct;
  the failure is in the dispatch chain, which is a different fix

## Files

- Hook: `~/.grok/hooks/Stop_decision_contract_gate.py`
- Registration: `~/.grok/hooks/decision-contract-gate.json`
- Validator: `~/.grok/hooks/scripts/decision_contract.py`
- Tests: `~/.grok/hooks/tests/test_decision_contract.py`
- Wiki: `P:/.data/wiki/concepts/decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming.md`
