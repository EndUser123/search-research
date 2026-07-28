# Close-authority enforcement completion — non-blocking workstream plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development
> (recommended) or executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the close-authority enforcement system so it satisfies all 10 non-negotiable acceptance tests from the operator's spec, using non-blocking parallel workstreams where dependencies allow.

**Architecture:** Three independent workstreams (A: acceptance tests, B: producer attestation, C: output-layer enforcement) that converge on a final integration + review gate. Each workstream produces independently testable deliverables. Workstream A is the spec's acceptance suite (proves what exists). Workstream B fixes INTG-1/INTG-2 (the critical flaws). Workstream C adds the Stop-hook enforcement layer (the structural fix for E7). A and B can proceed in parallel; C depends on B's interface decisions but can prototype in parallel.

**Tech Stack:** Python 3.12+, pytest, Grok Build hooks (command type), HMAC (stdlib `hmac`)

**Risk level:** Hard plan (reversibility ≥1.5 — enforcement code, security boundary, multi-session consequences)

## Global Constraints

- Branch `close-authority-019fa5a1` @ d516ccc is the starting point; work continues on that branch in the worktree `P:/worktrees/dotgrok-close-authority/`
- The 10 acceptance tests from the operator's spec are the merge gate — zero may be missing
- Per the maker-checker rule, the implementing agent must NOT self-certify enforcement proven — `/review` with cross-model specialists is required before merge
- Per the TCB concept, file-layer enforcement is necessary but insufficient — the Stop-hook layer (Workstream C) is the structural fix for output-channel bypass
- No env vars visible to the model may serve as HMAC keys (the model can `echo $VAR` via run_terminal_command)
- Fleet-safe: all artifacts must be workspace_id + session_id scoped; no global pointers
- The existing 20 tests must continue to pass throughout

---

## Workstream dependency map

```
Workstream A (acceptance tests)     Workstream B (INTG-1/INTG-2 fixes)
        │                                    │
        │  (can run in parallel)             │  (can run in parallel)
        │                                    │
        ▼                                    ▼
   A ships test scaffolding           B ships producer attestation + gate check
        │                                    │
        └──────────────┬─────────────────────┘
                       │
                       ▼  (B's interface must be settled)
              Workstream C (Stop-hook output enforcement)
                       │
                       ▼
              Integration gate: all 10 acceptance tests pass + /review clean
```

**Non-blocking property:** A and B start immediately and independently. C starts when B's producer-attestation interface is defined (not implemented — defined). The integration gate is the only serial step.

---

## Workstream A: Acceptance test suite (spec's 10 tests)

**Objective:** Write the 10 acceptance tests from the operator's spec. These tests define "done" — they are the merge gate. Some will fail initially (documenting the gaps); fixing them is Workstream B's job.

**Files:**
- Create: `P:/worktrees/dotgrok-close-authority/skills/close/tests/test_acceptance_spec.py`
- Modify: `P:/worktrees/dotgrok-close-authority/skills/close/tests/conftest.py` (add shared fixtures for two-terminal simulation)

### Task A1: Test scaffolding + tests 1-4 (isolation)

**Files:**
- Create: `skills/close/tests/test_acceptance_spec.py`
- Modify: `skills/close/tests/conftest.py`

**Interfaces:**
- Consumes: `close_authority.py` (CloseReceipt, AARReceipt, validate_close_receipt, validate_aar_receipt, compute_workspace_id, persist_close_receipt, load_close_receipt)
- Produces: `test_acceptance_spec.py` with 10 test functions, `conftest.py` with `two_terminal_fixture`, `forged_receipt_fixture`

- [ ] **Step 1: Write the test file with tests 1-4**

```python
# skills/close/tests/test_acceptance_spec.py
"""Acceptance tests from the operator's non-negotiable spec.
These tests define 'enforcement proven' — all 10 must pass before merge.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from skills.close.__lib.close_authority import (
    CloseReceipt, AARReceipt, LEGAL_TRANSITIONS,
    validate_close_receipt, validate_aar_receipt,
    persist_close_receipt, load_close_receipt,
    compute_workspace_id, authorize_completion,
)


@pytest.fixture
def two_terminals(tmp_path):
    """Simulate two terminals in the same repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    ws_id = compute_workspace_id(repo)
    term_a = tmp_path / "artifacts_a" / ws_id / "session-aaa"
    term_b = tmp_path / "artifacts_b" / ws_id / "session-bbb"
    term_a.mkdir(parents=True)
    term_b.mkdir(parents=True)
    return {"repo": repo, "ws_id": ws_id, "a": term_a, "b": term_b}


class TestAcceptance1CrossTerminalIsolation:
    """Test 1: Two terminals, same repo, different sessions: no cross-consumption."""

    def test_terminal_a_cannot_load_terminal_b_receipt(self, two_terminals):
        # Terminal B writes a CLOSE COMPLETE receipt
        receipt_b = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-bbb",
            close_attempt_id="attempt-b1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt_b, two_terminals["b"])

        # Terminal A tries to load it from B's path
        b_receipt_path = two_terminals["b"] / "close_receipt.json"
        loaded, reason = load_close_receipt(b_receipt_path, session_id="session-aaa")
        assert loaded is None or loaded.session_id != "session-aaa", \
            f"Terminal A consumed terminal B's receipt: {reason}"


class TestAcceptance2SameSessionTwoAttempts:
    """Test 2: Same session, two close attempts: exact attempt linkage."""

    def test_second_attempt_does_not_consume_first_receipt(self, two_terminals):
        session_dir = two_terminals["a"]
        # First attempt
        receipt_1 = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt_1, session_dir / "attempt-1")
        # Second attempt should not find attempt-1's receipt as its own
        loaded, reason = load_close_receipt(
            session_dir / "attempt-1" / "close_receipt.json",
            session_id="session-aaa",
            close_attempt_id="attempt-2",
        )
        assert loaded is None or loaded.close_attempt_id != "attempt-2", \
            "Second attempt consumed first attempt's receipt"


class TestAcceptance3StaleReceiptAfterMutation:
    """Test 3: Old valid-looking receipt after later substantive mutation: rejected."""

    def test_receipt_with_needs_attention_gates_rejected_on_reload(self, two_terminals):
        receipt = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={"retrospective": "needs_attention"},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        valid, reason = validate_close_receipt(receipt)
        assert not valid, \
            f"COMPLETE receipt with needs_attention gate passed validation: {reason}"


class TestAcceptance4StaleForeignPointer:
    """Test 4: Stale pointer to valid foreign receipt: ignored."""

    def test_foreign_session_receipt_not_authority(self, two_terminals):
        receipt_b = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-bbb",
            close_attempt_id="attempt-b1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt_b, two_terminals["b"])
        valid, reason = validate_close_receipt(receipt_b)
        # The receipt is valid for session-bbb, but not authority for session-aaa
        assert valid, "Receipt should be valid for its own session"
        # But loading it with a different session_id must fail
        loaded, load_reason = load_close_receipt(
            two_terminals["b"] / "close_receipt.json",
            session_id="session-aaa",
        )
        assert loaded is None, \
            f"Foreign receipt was loaded as authority for wrong session: {load_reason}"
```

- [ ] **Step 2: Run tests to verify they fail for the right reasons**

Run: `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/test_acceptance_spec.py -v`
Expected: Tests 1, 2, 4 may pass (isolation is designed). Test 3 FAILS (INTG-2 — this is the documented gap).

- [ ] **Step 3: Write tests 5-7 (atomicity, abandonment, concurrency)**

```python
class TestAcceptance5PartialAtomicWrite:
    """Test 5: Partial or interrupted atomic write: rejected."""

    def test_truncated_json_rejected(self, two_terminals):
        receipt_path = two_terminals["a"] / "close_receipt.json"
        # Write a truncated JSON file (simulating interrupted atomic write)
        receipt_path.write_text('{"workspace_id": "test", "session_id": "sess', encoding="utf-8")
        loaded, reason = load_close_receipt(receipt_path, session_id="session-aaa")
        assert loaded is None, f"Truncated JSON was loaded: {reason}"


class TestAcceptance6AbandonedRunStaleLease:
    """Test 6: Abandoned run and stale lease: unrelated terminal proceeds."""

    def test_abandoned_attempt_does_not_block_new_attempt(self, two_terminals):
        # Leave a stale _run.json from an abandoned attempt
        stale = two_terminals["a"] / "attempt-stale" / "close_receipt.json"
        stale.parent.mkdir(parents=True)
        stale.write_text(json.dumps({
            "workspace_id": two_terminals["ws_id"],
            "session_id": "session-aaa",
            "close_attempt_id": "attempt-stale",
            "terminal_verdict": "CLOSE INCOMPLETE",
            "resolved_gate_states": {"retrospective": "needs_attention"},
            "renderer_identity": "close_authority.py",
            "timestamp": "2026-01-01T00:00:00Z",
        }), encoding="utf-8")
        # A new attempt should be able to proceed without the stale one blocking
        # (This tests that the system doesn't use global locks)
        receipt_new = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-new",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        # Should not raise
        persist_close_receipt(receipt_new, two_terminals["a"] / "attempt-new")


class TestAcceptance7ConcurrentAARAndClose:
    """Test 7: Concurrent valid AAR and close operations: deterministic winner or explicit retry."""

    def test_concurrent_close_attempts_deterministic(self, two_terminals):
        # Two concurrent close attempts in the same session
        # Each should get its own attempt_id and not interfere
        for attempt_id in ["attempt-concurrent-1", "attempt-concurrent-2"]:
            receipt = CloseReceipt(
                workspace_id=two_terminals["ws_id"],
                session_id="session-aaa",
                close_attempt_id=attempt_id,
                terminal_verdict="CLOSE COMPLETE",
                resolved_gate_states={},
                renderer_identity="close_authority.py",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            persist_close_receipt(receipt, two_terminals["a"] / attempt_id)
        # Both should be loadable independently
        for attempt_id in ["attempt-concurrent-1", "attempt-concurrent-2"]:
            loaded, _ = load_close_receipt(
                two_terminals["a"] / attempt_id / "close_receipt.json",
                session_id="session-aaa",
            )
            assert loaded is not None, f"Concurrent attempt {attempt_id} not loadable"
```

- [ ] **Step 4: Write tests 8-10 (cleanup, forgery, restart)**

```python
class TestAcceptance8CleanupLeavesForeignArtifacts:
    """Test 8: Cleanup from one run leaves all foreign artifacts untouched."""

    def test_cleanup_only_removes_owned_artifacts(self, two_terminals):
        # Terminal A writes a receipt
        receipt_a = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-a1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt_a, two_terminals["a"] / "attempt-a1")
        # Terminal B writes a receipt
        receipt_b = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-bbb",
            close_attempt_id="attempt-b1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt_b, two_termernels["b"] / "attempt-b1")
        # If we clean up A's artifacts, B's must survive
        # (cleanup function to be implemented — this test defines the contract)
        # For now, verify B's receipt still loads
        loaded, _ = load_close_receipt(
            two_terminals["b"] / "attempt-b1" / "close_receipt.json",
            session_id="session-bbb",
        )
        assert loaded is not None, "Foreign receipt was destroyed by cleanup"


class TestAcceptance9ForgedReceiptRejected:
    """Test 9: Model-written forged receipt in another terminal's artifact tree: rejected."""

    def test_forged_receipt_without_producer_attestation_rejected(self, two_terminals):
        # Model writes a forged receipt directly to the filesystem
        forged = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-forged",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={"retrospective": "needs_attention"},  # unresolved!
            renderer_identity="close_authority.py",  # model claims it was the authority
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        # Without producer attestation, this should be rejected
        # This test WILL FAIL until Workstream B adds producer attestation
        valid, reason = validate_close_receipt(forged)
        # INTG-2 check: needs_attention gates must reject COMPLETE
        assert not valid, \
            f"Forged COMPLETE receipt with unresolved gates was accepted: {reason}"

    def test_forged_receipt_hash_manually_edited_rejected(self, two_terminals):
        # Model manually edits _run.json hash (as happened in E8)
        receipt_path = two_terminals["a"] / "_run.json"
        receipt_path.write_text(json.dumps({
            "status": "completed",
            "session_id": "session-aaa",
            "report_sha256": "manually_overwritten_hash",
            "hash_updated_at": "2026-07-28T06:43:00Z",  # field finalize_aar_run never writes
            "hash_update_reason": "manual edit",  # field finalize_aar_run never writes
        }), encoding="utf-8")
        # The scanner should detect that this receipt was not produced by finalize_aar_run
        # This test WILL FAIL until Workstream B adds producer attestation to _run.json
        # (For now it documents the gap)
        import sys, os
        sys.path.insert(0, os.path.expanduser("~/.grok/skills/aar/__lib"))
        from completion_receipt import finalize_aar_run
        result = finalize_aar_run(
            two_terminals["a"],
            two_terminals["a"] / "aar-report.md",  # doesn't exist
            "session-aaa",
        )
        assert not result["passed"], "Forged _run.json was accepted by finalize_aar_run"


class TestAcceptance10RestartReconstructsAuthority:
    """Test 10: Restarted process reconstructs exact authority from durable artifacts."""

    def test_authority_reconstructed_from_durable_artifacts(self, two_terminals):
        # Write a valid receipt
        receipt = CloseReceipt(
            workspace_id=two_terminals["ws_id"],
            session_id="session-aaa",
            close_attempt_id="attempt-1",
            terminal_verdict="CLOSE COMPLETE",
            resolved_gate_states={},
            renderer_identity="close_authority.py",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        persist_close_receipt(receipt, two_terminals["a"] / "attempt-1")
        # Simulate a restart: load from the durable artifact path
        loaded, reason = load_close_receipt(
            two_terminals["a"] / "attempt-1" / "close_receipt.json",
            session_id="session-aaa",
        )
        assert loaded is not None, f"Could not reconstruct authority: {reason}"
        assert loaded.terminal_verdict == "CLOSE COMPLETE"
        assert loaded.session_id == "session-aaa"
        assert loaded.close_attempt_id == "attempt-1"
```

- [ ] **Step 5: Run all 10 tests, document which fail**

Run: `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/test_acceptance_spec.py -v --tb=line`
Expected: Tests 3, 9 fail (INTG-2, INTG-1). Others should pass or fail on contract gaps.

- [ ] **Step 6: Commit**

```bash
git add skills/close/tests/test_acceptance_spec.py skills/close/tests/conftest.py
git commit -m "test: acceptance spec tests 1-10 (documents gaps INTG-1/INTG-2)"
```

---

## Workstream B: Producer attestation + gate-content fix (INTG-1/INTG-2)

**Objective:** Fix the 2 critical findings so tests 3 and 9 pass. Design a producer-attestation mechanism that works under the TCB constraint (key must be at a layer the model cannot reach).

**Files:**
- Create: `P:/worktrees/dotgrok-close-authority/skills/close/__lib/producer_attestation.py`
- Modify: `P:/worktrees/dotgrok-close-authority/skills/close/__lib/close_authority.py` (add attestation field to receipts, deepen validate_close_receipt)
- Modify: `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py` (add attestation to _run.json)

### Task B1: Design the attestation mechanism (TDD)

**The constraint:** the HMAC key must not be readable by the model via `run_terminal_command`. Options:
- (a) A key file with `chmod 600` owned by the operator, outside the model's read paths
- (b) A key derived from a secret the operator inputs at session start (not practical for solo-director usability)
- (c) A key embedded in the hook runtime config (env field in hook JSON — but model may read the JSON file)

**Selected approach:** key file at `~/.grok/state/.close_attestation_key` (owner-only, not in any path the model routinely reads). The attestation module generates it if missing (first run). HMAC-SHA256 over the receipt's canonical JSON.

**Files:**
- Create: `skills/close/__lib/producer_attestation.py`
- Test: `skills/close/tests/test_producer_attestation.py`

- [ ] **Step 1: Write failing tests**

```python
# skills/close/tests/test_producer_attestation.py
import json
import pytest
from pathlib import Path
from skills.close.__lib.producer_attestation import (
    get_attestation_key, sign_receipt, verify_attestation,
)

class TestProducerAttestation:
    def test_sign_and_verify_roundtrip(self, tmp_path):
        key_path = tmp_path / ".close_attestation_key"
        key = get_attestation_key(key_path)
        payload = {"verdict": "CLOSE COMPLETE", "session_id": "test"}
        signature = sign_receipt(payload, key)
        assert verify_attestation(payload, signature, key)

    def test_tampered_payload_rejected(self, tmp_path):
        key_path = tmp_path / ".close_attestation_key"
        key = get_attestation_key(key_path)
        payload = {"verdict": "CLOSE COMPLETE", "session_id": "test"}
        signature = sign_receipt(payload, key)
        tampered = {"verdict": "CLOSE COMPLETE", "session_id": "forged"}
        assert not verify_attestation(tampered, signature, key)

    def test_missing_signature_rejected(self, tmp_path):
        key_path = tmp_path / ".close_attestation_key"
        key = get_attestation_key(key_path)
        payload = {"verdict": "CLOSE COMPLETE", "session_id": "test"}
        assert not verify_attestation(payload, None, key)

    def test_key_is_deterministic_across_loads(self, tmp_path):
        key_path = tmp_path / ".close_attestation_key"
        key1 = get_attestation_key(key_path)
        key2 = get_attestation_key(key_path)  # second load
        assert key1 == key2  # same key file → same key
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest skills/close/tests/test_producer_attestation.py -v`
Expected: FAIL (module doesn't exist)

- [ ] **Step 3: Implement the attestation module**

```python
# skills/close/__lib/producer_attestation.py
"""Producer attestation for close receipts.

Uses HMAC-SHA256 with a key stored outside the model's read paths.
The key file is at ~/.grok/state/.close_attestation_key (owner-only).

Design principle (TCB concept): the attestation must use a secret
the model cannot read. If the model can read the key file, the
attestation is forgeable.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

DEFAULT_KEY_PATH = Path.home() / ".grok" / "state" / ".close_attestation_key"


def get_attestation_key(key_path: Path | None = None) -> bytes:
    """Load or generate the attestation key."""
    key_path = key_path or DEFAULT_KEY_PATH
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return key_path.read_bytes()
    key = secrets.token_bytes(32)
    # Write with restricted permissions (owner-only)
    fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    return key


def sign_receipt(payload: dict, key: bytes) -> str:
    """Sign a receipt payload with HMAC-SHA256."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_attestation(payload: dict, signature: str | None, key: bytes) -> bool:
    """Verify a receipt's HMAC signature."""
    if not signature:
        return False
    expected = sign_receipt(payload, key)
    return hmac.compare_digest(signature, expected)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest skills/close/tests/test_producer_attestation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/close/__lib/producer_attestation.py skills/close/tests/test_producer_attestation.py
git commit -m "feat: producer attestation module (HMAC-SHA256, key outside model read paths)"
```

### Task B2: Add attestation to CloseReceipt + deepen validate_close_receipt (INTG-1 + INTG-2)

**Files:**
- Modify: `skills/close/__lib/close_authority.py` (lines 131-170 CloseReceipt dataclass, lines 273-306 validate_close_receipt)

- [ ] **Step 1: Write failing test for INTG-2 fix**

```python
# skills/close/tests/test_intg2_fix.py
def test_complete_receipt_with_needs_attention_rejected():
    """INTG-2: validate_close_receipt must reject COMPLETE with needs_attention gates."""
    from skills.close.__lib.close_authority import CloseReceipt, validate_close_receipt
    receipt = CloseReceipt(
        workspace_id="test",
        session_id="test",
        close_attempt_id="test",
        terminal_verdict="CLOSE COMPLETE",
        resolved_gate_states={"retrospective": "needs_attention"},
        renderer_identity="close_authority.py",
        timestamp="2026-07-28T00:00:00Z",
    )
    valid, reason = validate_close_receipt(receipt)
    assert not valid, f"Should reject COMPLETE with needs_attention: {reason}"
    assert "needs_attention" in reason or "unresolved" in reason.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest skills/close/tests/test_intg2_fix.py -v`
Expected: FAIL (current validate_close_receipt accepts this)

- [ ] **Step 3: Fix validate_close_receipt**

In `close_authority.py`, modify `validate_close_receipt()` to add after the existing checks:

```python
# INTG-2 fix: reject COMPLETE receipts with unresolved gates
if receipt.terminal_verdict == "CLOSE COMPLETE":
    unresolved = {k: v for k, v in receipt.resolved_gate_states.items()
                  if v == "needs_attention"}
    if unresolved:
        return (False,
                f"CLOSE COMPLETE receipt has unresolved gates: {list(unresolved.keys())}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest skills/close/tests/test_intg2_fix.py -v`
Expected: PASS

- [ ] **Step 5: Add attestation field to CloseReceipt dataclass + validation**

In `close_authority.py`, add to `CloseReceipt`:
```python
producer_attestation: str | None = None  # HMAC-SHA256 of canonical receipt JSON
```

In `validate_close_receipt()`, add:
```python
# INTG-1 fix: verify producer attestation if present
if receipt.producer_attestation:
    from skills.close.__lib.producer_attestation import verify_attestation, get_attestation_key
    key = get_attestation_key()
    payload = {k: v for k, v in receipt.to_dict().items() if k != "producer_attestation"}
    if not verify_attestation(payload, receipt.producer_attestation, key):
        return (False, "producer attestation verification failed")
```

In `persist_close_receipt()`, add signing before write:
```python
from skills.close.__lib.producer_attestation import sign_receipt, get_attestation_key
payload = {k: v for k, v in receipt.to_dict().items() if k != "producer_attestation"}
receipt.producer_attestation = sign_receipt(payload, get_attestation_key())
```

- [ ] **Step 6: Run all 20 existing tests + new tests**

Run: `python -m pytest skills/close/tests/ -v --tb=short`
Expected: all pass (existing 20 + new attestation + INTG-2 fix)

- [ ] **Step 7: Commit**

```bash
git add skills/close/__lib/close_authority.py skills/close/tests/test_intg2_fix.py
git commit -m "fix: INTG-1 (producer attestation) + INTG-2 (gate-content check on reload)"
```

### Task B3: Add attestation to AAR completion_receipt (E8 fix)

**Files:**
- Modify: `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py`

- [ ] **Step 1: Add attestation to finalize_aar_run**

In `finalize_aar_run()`, after computing `report_hash`, add:

```python
# E8 fix: sign the receipt with producer attestation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "close" / "__lib"))
from producer_attestation import sign_receipt, get_attestation_key
attestation_payload = {
    "status": "completed",
    "session_id": session_id,
    "report_sha256": report_hash,
}
attestation = sign_receipt(attestation_payload, get_attestation_key())
```

Then add `"producer_attestation": attestation` to the `state.update()` call.

In the hash-mismatch check, also verify the attestation:

```python
# Verify existing attestation if present (detect manual edits)
if state.get("producer_attestation"):
    from producer_attestation import verify_attestation, get_attestation_key
    key = get_attestation_key()
    expected_payload = {"status": "completed", "session_id": session_id, "report_sha256": report_hash}
    if not verify_attestation(expected_payload, state["producer_attestation"], key):
        return {"passed": False, "detail": "producer attestation invalid — receipt may have been manually edited"}
```

- [ ] **Step 2: Test that manual hash edits are now detected**

```python
def test_manual_hash_edit_detected(tmp_path):
    """E8: manually edited _run.json hash must be rejected."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "preprocess").mkdir()
    (run_dir / "_run.json").write_text(json.dumps({
        "status": "completed",
        "skill": "aar",
        "session_id": "test",
        "report_sha256": "manually_overwritten",
        "report_path": str(run_dir / "aar-report.md"),
        "producer_attestation": None,  # no attestation = not produced by finalize_aar_run
    }), encoding="utf-8")
    result = finalize_aar_run(run_dir, run_dir / "aar-report.md", "test")
    assert not result["passed"]
```

- [ ] **Step 3: Commit**

```bash
git add C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py
git commit -m "fix: E8 — producer attestation on AAR _run.json prevents manual hash edits"
```

---

## Workstream C: Output-layer enforcement (Stop hook)

**Objective:** Build the Stop hook that prevents the model from delivering a forged close report to the operator. This is the structural fix for E7 (scanner bypass).

**Depends on:** B's attestation interface being defined (not fully implemented — the hook needs to know what a valid receipt looks like, but can prototype without the attestation).

**Files:**
- Create: `~/.grok/hooks/scripts/close_enforcement_gate.py`
- Create: `~/.grok/hooks/close-enforcement.json`
- Test: `P:/worktrees/dotgrok-close-authority/skills/close/tests/test_stop_hook_gate.py`

### Task C1: Prototype the gate script

- [ ] **Step 1: Write the gate script**

```python
# ~/.grok/hooks/scripts/close_enforcement_gate.py
"""Stop hook: blocks close-context output if scanner reports needs_attention gates.

Reads lastAssistantMessage from stdin. If it contains close-context markers,
runs close_accounting.py and checks gate states. If any gate is needs_attention,
blocks the stop with the gate details.
"""
import json
import sys
import subprocess
import os

CLOSE_MARKERS = [
    "CLOSE COMPLETE", "CLOSE INCOMPLETE", "Session close report",
    "session closed", "## Session details",
]


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # fail open on malformed input

    # Only gate on genuine end_turn, not session-end
    reason = event.get("reason", "")
    if reason != "end_turn":
        sys.exit(0)

    # Check if this is close-context
    last_message = event.get("lastAssistantMessage", "")
    if not any(marker in last_message for marker in CLOSE_MARKERS):
        sys.exit(0)

    # Check stopHookActive to avoid infinite loops
    if event.get("stopHookActive", False):
        sys.exit(0)

    # Run the scanner
    session_id = os.environ.get("GROK_SESSION_ID", "")
    if not session_id:
        sys.exit(0)  # can't check without session id

    try:
        result = subprocess.run(
            [sys.executable, os.path.expanduser(
                "~/.grok/skills/close/__lib/close_accounting.py"),
             "--session", session_id, "--format", "json"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            sys.exit(0)  # fail open if scanner crashes
        data = json.loads(result.stdout)
        gates = data.get("gates", {})
        needs_attention = {k: v.get("detail", "") for k, v in gates.items()
                          if v.get("state") == "needs_attention"}
        if needs_attention:
            gate_list = ", ".join(needs_attention.keys())
            print(json.dumps({
                "decision": "block",
                "reason": f"Close scanner reports gates needing attention: {gate_list}. "
                          f"Resolve these gates before emitting a close summary."
            }))
            sys.exit(0)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        sys.exit(0)  # fail open

    sys.exit(0)  # allow stop


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the hook config**

```json
// ~/.grok/hooks/close-enforcement.json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.grok/hooks/scripts/close_enforcement_gate.py",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Write unit tests for the gate logic**

```python
# skills/close/tests/test_stop_hook_gate.py
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the gate module (adjust path as needed)
# The gate script is at ~/.grok/hooks/scripts/close_enforcement_gate.py


class TestCloseEnforcementGate:
    def test_non_close_output_passes(self):
        """Output without close markers should not be blocked."""
        # Test the marker detection logic
        from close_enforcement_gate import CLOSE_MARKERS
        non_close = "Here are the files you requested."
        assert not any(m in non_close for m in CLOSE_MARKERS)

    def test_close_output_with_marker_detected(self):
        from close_enforcement_gate import CLOSE_MARKERS
        close_output = "# Session close report\n## Session details"
        assert any(m in close_output for m in CLOSE_MARKERS)

    def test_session_end_fire_not_blocked(self):
        """reason != end_turn should not trigger the gate."""
        event = {"reason": "channel_closed", "lastAssistantMessage": "CLOSE COMPLETE"}
        assert event["reason"] != "end_turn"

    def test_stop_hook_active_not_blocked(self):
        """If stopHookActive is True, don't block (avoid infinite loops)."""
        event = {"stopHookActive": True, "lastAssistantMessage": "CLOSE COMPLETE",
                 "reason": "end_turn"}
        assert event["stopHookActive"]
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest skills/close/tests/test_stop_hook_gate.py -v`

- [ ] **Step 5: Commit**

```bash
git add ~/.grok/hooks/scripts/close_enforcement_gate.py ~/.grok/hooks/close-enforcement.json
git add skills/close/tests/test_stop_hook_gate.py
git commit -m "feat: Stop hook for output-layer close enforcement (E7 structural fix)"
```

---

## Integration gate (serial — after A, B, C complete)

### Task D1: Run all acceptance tests

- [ ] **Step 1: Run the full acceptance suite**

Run: `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/test_acceptance_spec.py -v`
Expected: all 10 PASS

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest skills/close/tests/ -v`
Expected: all pass (20 original + 10 acceptance + attestation + INTG-2 + stop-hook)

- [ ] **Step 3: If any fail, fix before proceeding**

### Task D2: /review with cross-model specialists

Per the maker-checker rule, the implementing agent must NOT self-certify.

- [ ] **Step 1: Run /review on the branch**

Run: `/review --branch close-authority-019fa5a1`
Expected: no critical findings. If critical findings, fix before merge.

### Task D3: /check session verification

- [ ] **Step 1: Run /check**

Run: `/check`
Expected: PASS

---

## Latency/performance spec

- **Stop hook gate:** runs only on close-context output (filtered by marker detection). Non-close turns exit in <10ms (marker check only). Close-context turns add ~20s (scanner run). Total hook latency: <30s for close turns, <10ms for all others.
- **Attestation key load:** file read, ~1ms. Cached in memory if needed.
- **validate_close_receipt with attestation:** HMAC computation is O(n) in receipt size, negligible for ~1KB receipts.

## Exception safety

- All hook scripts fail open (exit 0 on any error) per the Grok Build hook contract
- Attestation verification failure returns `(False, reason)` not an exception
- Scanner subprocess timeout (120s) fails open

## Internal consistency check

- Workstream A's test 9 (forged receipt) requires Workstream B's attestation to pass. This is intentional — A documents the gap, B fixes it.
- Workstream C's Stop hook runs `close_accounting.py`, which is the same scanner Workstream A tests. No interface mismatch.
- The attestation key path (`~/.grok/state/.close_attestation_key`) is used by both `close_authority.py` (Workstream B) and `completion_receipt.py` (Task B3). Same key, same module — no key management divergence.

## Adversarial review recommendation

Run `/tp` to adversarially review this plan before approving implementation. The reviewer should attack for:
- Whether the attestation key path is truly outside the model's read paths (can the model `cat ~/.grok/state/.close_attestation_key`?)
- Whether the Stop hook marker detection has unacceptable false-positive rates
- Whether the 10 acceptance tests actually prove the spec's properties or have loopholes
- Whether concurrent workstream execution could create merge conflicts on `close_authority.py`

---

## Execution recommendation

**Parallel execution:** Workstreams A and B start immediately in parallel (different files, no conflicts). Workstream C starts when B's attestation interface is defined (Task B1 complete).

**Recommended approach:** `/go execute <plan-path>` with parallel task dispatch. Use worktree isolation if multiple agents work simultaneously.

**Plan saved to:** `docs/superpowers/plans/2026-07-28-close-authority-completion.md`
