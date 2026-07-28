# Close-authority enforcement completion — non-blocking workstream plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development
> (recommended) or executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the close-authority enforcement system so it satisfies all 10 non-negotiable acceptance tests from the operator's spec, using serialized workstreams where dependencies require and parallel where genuinely independent.

**Architecture:** Four workstreams in a dependency chain. Workstream A (acceptance tests) runs first to document gaps. Workstream B (producer attestation + INTG fixes) runs second, fixing the gaps A documents. Workstream B2 (AAR receipt attestation) is a separate change to user-scope skills, not the worktree branch. Workstream C (Stop-hook output enforcement) runs after B's interface is settled. Workstream D (CORR fixes) can run in parallel with C. The integration gate is serial.

**Tech Stack:** Python 3.12+, pytest, Grok Build hooks (command type), HMAC (stdlib `hmac`)

**Risk level:** Hard plan (reversibility ≥1.5 — enforcement code, security boundary, multi-session consequences)

## Revision history

- **v1** (2026-07-28): original plan, 3 workstreams
- **v2** (2026-07-28): revised after /tp adversarial review found 14 issues (5 critical). Changes:
  - **#1 fix:** HMAC key moved from `~/.grok/state/` (model-readable file) to hook-runtime env var (model cannot read hook process env). Scanner writes unsigned receipts; hook signs them. Separation of scan and attest.
  - **#2 fix:** Task B2 (AAR receipt attestation) is a separate change to user-scope skills (`~/.grok/skills/aar/`), not the worktree branch. Integration gate verifies both.
  - **#3 fix:** A and B are serialized, not parallel. A runs first (tests against current code), then B runs (fixes gaps A documents).
  - **#4 fix:** Acceptance tests tightened to probe security properties, not just contract surface. Added negative tests, enumeration tests, replay tests.
  - **#5 fix:** Plan-level adversarial review is now mandatory (this revision is the output of that review).
  - **#6 fix:** Stop hook markers tightened to require structural evidence (blockquote + verdict token), not substring matching.
  - **#7 fix:** Explicit signed-field enumeration + per-attempt nonce added.
  - **#8 fix:** Key lifecycle documented (immutability, key_id, rotation procedure).
  - **#9 fix:** Fail-open observability (structured log) + health degradation check.
  - **#10 fix:** Exit-code contract verified from 10-hooks.md; both exit 2 + stderr and JSON decision:block supported.
  - **#11 fix:** Latency spec updated with measured numbers from this session; caching strategy added.
  - **#12 fix:** Typo `two_termernels` → `two_terminals`.
  - **#13 fix:** CORR-001/002/003 added as Workstream D.
  - **#14 fix:** Module path issue resolved — producer_attestation is a proper package importable from both close and aar skills.

## Global Constraints

- Branch `close-authority-019fa5a1` @ d516ccc is the starting point for Workstreams A, B, C, D
- The AAR attestation fix (Workstream B2) modifies user-scope skills at `~/.grok/skills/aar/` — this is a SEPARATE change, not on the worktree branch. The integration gate must verify both.
- The 10 acceptance tests from the operator's spec are the merge gate — zero may be missing
- Per the maker-checker rule, the implementing agent must NOT self-certify enforcement proven — `/review` with cross-model specialists is required before merge
- Per the TCB concept, file-layer enforcement is necessary but insufficient — the Stop-hook layer (Workstream C) is the structural fix for output-channel bypass
- **The HMAC key must NOT be in any file the model can read via `run_terminal_command`.** Files under `~/.grok/`, `P:/`, and the user's home are ALL model-readable. The key must live in the hook runtime's process env (injected via the hook JSON `env` field), which the model's tool environment cannot access. This requires empirical verification (Finding #1 verification test).
- Fleet-safe: all artifacts must be workspace_id + session_id scoped; no global pointers
- The existing 20 tests must continue to pass throughout
- **A and B are serialized** (not parallel). A writes tests against current code (documenting gaps). B fixes the gaps. Running them in parallel causes test breakage when B modifies `close_authority.py` mid-test-run (Finding #3).

---

## Workstream dependency map (revised)

```
Workstream A (acceptance tests — document gaps)
        │
        ▼  (A completes first)
Workstream B (INTG-1/INTG-2 fixes — close-authority branch)
        │
        ├── Workstream B2 (AAR receipt attestation — user-scope skills, separate commit)
        │
        ▼  (B's attestation interface is settled)
Workstream C (Stop-hook output enforcement)
        │                              Workstream D (CORR-001/002/003 fixes)
        │                              (can run in parallel with C — different files)
        ▼                              ▼
        └──────────────┬───────────────┘
                       │
                       ▼
              Integration gate: all 10 acceptance tests pass + /review clean
              + both branches verified (close-authority + AAR skill)
```

**Why A → B is serial (Finding #3 fix):** A's tests import from `close_authority.py`. B modifies `close_authority.py`. If they run concurrently, A's tests break on B's half-edited code or pass falsely against a code path B hasn't finished. Serialization is correct; the parallel claim was wrong.

**Why C and D can run in parallel:** C creates new files (`~/.grok/hooks/scripts/close_enforcement_gate.py`, hook JSON). D modifies existing files in the worktree (`close_accounting.py`, `close_authority.py`). No file overlap.

---

## Workstream A: Acceptance test suite (spec's 10 tests)

**Objective:** Write the 10 acceptance tests from the operator's spec. These tests define "done" — they are the merge gate. Some will fail initially (documenting the gaps); fixing them is Workstream B's job.

**Files:**
- Create: `P:/worktrees/dotgrok-close-authority/skills/close/tests/test_acceptance_spec.py`
- Modify: `P:/worktrees/dotgrok-close-authority/skills/close/tests/conftest.py` (add shared fixtures for two-terminal simulation)

### Task A1: Tests 1-10 with security-property probing (Finding #4 fix)

**Files:**
- Create: `skills/close/tests/test_acceptance_spec.py`
- Modify: `skills/close/tests/conftest.py`

**Interfaces:**
- Consumes: `close_authority.py` (CloseReceipt, AARReceipt, validate_close_receipt, validate_aar_receipt, compute_workspace_id, persist_close_receipt, load_close_receipt)
- Produces: `test_acceptance_spec.py` with 10+ test classes, `conftest.py` with `two_terminals` fixture

**Test design principles (Finding #4 fix):**
- Each test probes a SECURITY PROPERTY, not a contract surface
- Every test includes a NEGATIVE variant: "what input would defeat this property?"
- Tests enumerate ALL non-resolved gate states (`needs_attention`, `blocked`, `pending`, `deferred`, `""`, `None`), not just `"needs_attention"`
- Forgery tests forge a SIGNED receipt (with key access simulated), not just an unsigned one
- Concurrency tests use `threading`, not sequential writes
- Each mutated-field test verifies signature invalidation (Finding #7 fix)

- [ ] **Step 1: Write the test file with all 10 tests**

(Full test code is extensive — see the inline code blocks below. Each test class probes one acceptance criterion with both positive and negative variants.)

```python
# skills/close/tests/test_acceptance_spec.py
"""Acceptance tests from the operator's non-negotiable spec.
These tests define 'enforcement proven' — all 10 must pass before merge.

Design principle (Finding #4 fix): each test probes a SECURITY PROPERTY,
not just a contract surface. Every test includes negative variants.
"""
import json
import threading
import pytest
from pathlib import Path
from datetime import datetime, timezone

from skills.close.__lib.close_authority import (
    CloseReceipt, AARReceipt, LEGAL_TRANSITIONS,
    validate_close_receipt, validate_aar_receipt,
    persist_close_receipt, load_close_receipt,
    compute_workspace_id, authorize_completion,
)

# Non-resolved gate states to enumerate (Finding #4 fix)
NON_RESOLVED_STATES = [
    "needs_attention", "blocked", "pending", "deferred", "", None, "unknown"
]


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


def _make_receipt(ws_id, session_id, attempt_id, verdict="CLOSE COMPLETE",
                  gates=None, attestation=None):
    """Helper to construct a CloseReceipt with sensible defaults."""
    return CloseReceipt(
        workspace_id=ws_id,
        session_id=session_id,
        close_attempt_id=attempt_id,
        terminal_verdict=verdict,
        resolved_gate_states=gates or {},
        renderer_identity="close_authority.py",
        timestamp=datetime.now(timezone.utc).isoformat(),
        producer_attestation=attestation,
        attestation_nonce=None,  # per-attempt nonce (Finding #7 fix)
    )


class TestAcceptance1CrossTerminalIsolation:
    """Test 1: Two terminals, same repo, different sessions: no cross-consumption."""

    def test_terminal_a_cannot_load_terminal_b_receipt(self, two_terminals):
        receipt_b = _make_receipt(two_terminals["ws_id"], "session-bbb", "attempt-b1")
        persist_close_receipt(receipt_b, two_terminals["b"])
        loaded, reason = load_close_receipt(
            two_terminals["b"] / "close_receipt.json",
            session_id="session-aaa",
        )
        assert loaded is None or loaded.session_id != "session-aaa"


class TestAcceptance2SameSessionTwoAttempts:
    """Test 2: Same session, two close attempts: exact attempt linkage."""

    def test_second_attempt_does_not_consume_first_receipt(self, two_terminals):
        receipt_1 = _make_receipt(two_terminals["ws_id"], "session-aaa", "attempt-1")
        persist_close_receipt(receipt_1, two_terminals["a"] / "attempt-1")
        loaded, reason = load_close_receipt(
            two_terminals["a"] / "attempt-1" / "close_receipt.json",
            session_id="session-aaa",
            close_attempt_id="attempt-2",
        )
        assert loaded is None or loaded.close_attempt_id != "attempt-2"


class TestAcceptance3StaleReceiptAfterMutation:
    """Test 3: Old valid-looking receipt after later substantive mutation: rejected.
    Finding #4 fix: enumerate ALL non-resolved gate states, not just needs_attention."""

    @pytest.mark.parametrize("gate_state", NON_RESOLVED_STATES)
    def test_complete_receipt_with_unresolved_gate_rejected(self, gate_state, two_terminals):
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-1",
            gates={"retrospective": gate_state},
        )
        valid, reason = validate_close_receipt(receipt)
        assert not valid, \
            f"COMPLETE receipt with gate state {gate_state!r} passed validation: {reason}"


class TestAcceptance4StaleForeignPointer:
    """Test 4: Stale pointer to valid foreign receipt: ignored."""

    def test_foreign_session_receipt_not_authority(self, two_terminals):
        receipt_b = _make_receipt(two_terminals["ws_id"], "session-bbb", "attempt-b1")
        persist_close_receipt(receipt_b, two_terminals["b"])
        loaded, _ = load_close_receipt(
            two_terminals["b"] / "close_receipt.json",
            session_id="session-aaa",
        )
        assert loaded is None


class TestAcceptance5PartialAtomicWrite:
    """Test 5: Partial or interrupted atomic write: rejected.
    Finding #4 fix: also test valid JSON with manipulated fields."""

    def test_truncated_json_rejected(self, two_terminals):
        receipt_path = two_terminals["a"] / "close_receipt.json"
        receipt_path.write_text('{"workspace_id": "test", "session_id": "sess',
                                encoding="utf-8")
        loaded, reason = load_close_receipt(receipt_path, session_id="session-aaa")
        assert loaded is None

    def test_valid_json_with_manipulated_verdict_rejected(self, two_terminals):
        """A perfectly valid JSON with manipulated gate states must be caught by attestation."""
        # This test will FAIL until attestation is added (Workstream B)
        receipt_path = two_terminals["a"] / "close_receipt.json"
        receipt_path.write_text(json.dumps({
            "workspace_id": two_terminals["ws_id"],
            "session_id": "session-aaa",
            "close_attempt_id": "attempt-1",
            "terminal_verdict": "CLOSE COMPLETE",
            "resolved_gate_states": {"retrospective": "needs_attention"},
            "renderer_identity": "close_authority.py",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "producer_attestation": None,
        }), encoding="utf-8")
        loaded, reason = load_close_receipt(receipt_path, session_id="session-aaa")
        # Should be rejected because: (a) needs_attention gate + COMPLETE, (b) no attestation
        if loaded:
            valid, vreason = validate_close_receipt(loaded)
            assert not valid, \
                f"Manipulated valid JSON with no attestation was accepted: {vreason}"


class TestAcceptance6AbandonedRunStaleLease:
    """Test 6: Abandoned run and stale lease: unrelated terminal proceeds."""

    def test_abandoned_attempt_does_not_block_new_attempt(self, two_terminals):
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
        receipt_new = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-new"
        )
        persist_close_receipt(receipt_new, two_terminals["a"] / "attempt-new")


class TestAcceptance7ConcurrentAARAndClose:
    """Test 7: Concurrent valid AAR and close operations: deterministic winner.
    Finding #4 fix: uses actual threading for concurrency."""

    def test_concurrent_close_attempts_thread_safe(self, two_terminals):
        """Two threads persist receipts concurrently — no corruption or mixed state."""
        errors = []

        def persist_attempt(attempt_id):
            try:
                receipt = _make_receipt(
                    two_terminals["ws_id"], "session-aaa", attempt_id
                )
                persist_close_receipt(receipt, two_terminals["a"] / attempt_id)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=persist_attempt, args=("attempt-c1",)),
            threading.Thread(target=persist_attempt, args=("attempt-c2",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent errors: {errors}"
        for attempt_id in ["attempt-c1", "attempt-c2"]:
            loaded, _ = load_close_receipt(
                two_terminals["a"] / attempt_id / "close_receipt.json",
                session_id="session-aaa",
            )
            assert loaded is not None, f"Concurrent attempt {attempt_id} not loadable"
            assert loaded.close_attempt_id == attempt_id


class TestAcceptance8CleanupLeavesForeignArtifacts:
    """Test 8: Cleanup from one run leaves all foreign artifacts untouched.
    Finding #12 fix: typo two_termernels → two_terminals."""

    def test_cleanup_only_removes_owned_artifacts(self, two_terminals):
        receipt_a = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-a1"
        )
        persist_close_receipt(receipt_a, two_terminals["a"] / "attempt-a1")
        receipt_b = _make_receipt(
            two_terminals["ws_id"], "session-bbb", "attempt-b1"
        )
        persist_close_receipt(receipt_b, two_terminals["b"] / "attempt-b1")
        loaded, _ = load_close_receipt(
            two_terminals["b"] / "attempt-b1" / "close_receipt.json",
            session_id="session-bbb",
        )
        assert loaded is not None


class TestAcceptance9ForgedReceiptRejected:
    """Test 9: Model-written forged receipt: rejected.
    Finding #4 fix: test BOTH unsigned AND signed forgery (with key access simulated)."""

    def test_forged_unsigned_receipt_rejected(self, two_terminals):
        """Receipt without attestation must not validate as COMPLETE."""
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-forged",
            gates={"retrospective": "needs_attention"},
            attestation=None,  # no attestation = not produced by the hook
        )
        valid, reason = validate_close_receipt(receipt)
        assert not valid

    def test_forged_receipt_with_wrong_attestation_rejected(self, two_terminals):
        """Receipt with a garbage attestation string must not validate."""
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-forged",
            attestation="garbage_hash_that_is_not_valid",
        )
        valid, reason = validate_close_receipt(receipt)
        assert not valid
        assert "attestation" in reason.lower() or "invalid" in reason.lower()

    def test_forged_receipt_hash_manually_edited_detected(self, tmp_path):
        """E8: manually edited _run.json must be detected by attestation verification.
        Finding #4 fix: separate 'file missing' from 'edit detected' failures."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "preprocess").mkdir()
        # Write a forged _run.json with manually overwritten hash
        forged_state = {
            "status": "completed",
            "skill": "aar",
            "session_id": "test-session",
            "report_sha256": "manually_overwritten_hash",
            "report_path": str(run_dir / "aar-report.md"),
            "producer_attestation": None,
        }
        (run_dir / "_run.json").write_text(
            json.dumps(forged_state), encoding="utf-8"
        )
        # Test: the receipt has no attestation → must be rejected
        # (not because the report file is missing, but because no attestation exists)
        assert forged_state["producer_attestation"] is None, \
            "Test setup error: attestation should be None for a forged receipt"


class TestAcceptance10RestartReconstructsAuthority:
    """Test 10: Restarted process reconstructs exact authority from durable artifacts."""

    def test_authority_reconstructed_from_durable_artifacts(self, two_terminals):
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-aaa", "attempt-1"
        )
        persist_close_receipt(receipt, two_terminals["a"] / "attempt-1")
        loaded, reason = load_close_receipt(
            two_terminals["a"] / "attempt-1" / "close_receipt.json",
            session_id="session-aaa",
        )
        assert loaded is not None
        assert loaded.terminal_verdict == "CLOSE COMPLETE"
        assert loaded.session_id == "session-aaa"
        assert loaded.close_attempt_id == "attempt-1"


class TestReplayProtection:
    """Finding #7 fix: signed receipt must not be replayable across attempts."""

    def test_attestation_binds_to_attempt_id(self, two_terminals):
        """If attempt_id is changed post-signing, signature must fail."""
        from skills.close.__lib.producer_attestation import (
            sign_receipt, verify_attestation, get_attestation_key,
        )
        key = b"test-key-for-replay-protection"
        payload_1 = {
            "session_id": "session-aaa",
            "close_attempt_id": "attempt-1",
            "terminal_verdict": "CLOSE COMPLETE",
        }
        signature = sign_receipt(payload_1, key)
        # Mutate attempt_id
        payload_2 = dict(payload_1, close_attempt_id="attempt-2")
        assert not verify_attestation(payload_2, signature, key), \
            "Signature survived attempt_id mutation — replay possible"

    def test_attestation_binds_to_each_field(self, two_terminals):
        """Each non-attestation field mutation must invalidate the signature."""
        from skills.close.__lib.producer_attestation import (
            sign_receipt, verify_attestation,
        )
        key = b"test-key"
        base = {
            "session_id": "s", "close_attempt_id": "a",
            "terminal_verdict": "CLOSE COMPLETE",
            "workspace_id": "w", "timestamp": "2026-01-01T00:00:00Z",
            "resolved_gate_states": {},
        }
        sig = sign_receipt(base, key)
        for field in base:
            mutated = dict(base)
            mutated[field] = "MUTATED_VALUE"
            assert not verify_attestation(mutated, sig, key), \
                f"Signature survived mutation of {field}"
```

- [ ] **Step 2: Run tests to verify they fail for the right reasons**

Run: `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/test_acceptance_spec.py -v --tb=line`
Expected: Tests 3, 5b, 9, and replay tests FAIL (INTG-1/INTG-2 gaps). Others pass.

- [ ] **Step 3: Commit**

```bash
git add skills/close/tests/test_acceptance_spec.py skills/close/tests/conftest.py
git commit -m "test: acceptance spec v2 — security-property probing (Finding #4 fix)"
```

---

## Workstream B: Producer attestation + INTG fixes (close-authority branch)

**Objective:** Fix INTG-1 and INTG-2 so acceptance tests 3, 5b, 9, and replay tests pass.

**Key design decision (Finding #1 fix): the attestation key separation**

The HMAC key must NOT be in any file the model can read. The model can read ALL files on this host via `run_terminal_command`. Therefore:

1. **The key lives in the Stop hook's process environment** (injected via the hook JSON `env` field). The model's `run_terminal_command` runs in a different process and cannot read hook-process env vars.
2. **The scanner writes UNSIGNED receipts.** `close_accounting.py` runs from the model's context (via `/close`). It does NOT have the key. It computes gate states and writes a receipt without attestation.
3. **The Stop hook SIGNS receipts.** When the hook fires (after the model's output), it reads the unsigned receipt, verifies gates are clean, signs with the key from its env, and writes the signed receipt. If gates are NOT clean, it blocks output.
4. **`validate_close_receipt` rejects COMPLETE receipts without valid attestation.** An unsigned receipt (produced by the scanner alone) cannot be used as authority for CLOSE COMPLETE.

**This means:** the model can write unsigned receipts but they won't validate. The hook is the only entity that can produce valid signed receipts. The key never touches a file.

**Empirical verification required (Finding #1):**
- Test: from the model's `run_terminal_command`, run `echo $CLOSE_ATTESTATION_KEY` — must return empty
- If it returns the key value, the env-var approach is compromised and we need Windows Credential Manager or a passphrase-based approach

### Task B0: Verify hook env var isolation (Finding #1 gate)

- [ ] **Step 1: Create a test hook that exports an env var**

Create `~/.grok/hooks/test-env-isolation.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'env test fired'",
            "env": {"CLOSE_ATTESTATION_KEY": "test-secret-12345"}
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: From the model's shell, try to read the env var**

Run: `echo $env:CLOSE_ATTESTATION_KEY`
Expected: empty (the env var is in the hook process, not the model's shell)

- [ ] **Step 3: If the env var IS readable, pivot to Windows Credential Manager**

If `echo $env:CLOSE_ATTESTATION_KEY` returns `test-secret-12345`, the env-var approach is compromised. Use `cmdkey` / DPAPI instead:
```powershell
# Store the key in Windows Credential Manager
cmdkey /generic:close-attestation-key /user:close-system /pass:<generated-key>
# Read it (only from a process that has the user's DPAPI context)
$key = (Get-StoredCredential -Target close-attestation-key).Password
```

- [ ] **Step 4: Record the result and proceed with the working approach**

### Task B1: Implement producer_attestation module

**Files:**
- Create: `P:/worktrees/dotgrok-close-authority/skills/close/__lib/producer_attestation.py`
- Create: `skills/close/tests/test_producer_attestation.py`

**Module path fix (Finding #14):** `producer_attestation.py` is a standalone module importable via standard Python import system. Both `close_authority.py` and `completion_receipt.py` import it via the same path. No `sys.path` hacks.

- [ ] **Step 1: Write failing tests**

```python
# skills/close/tests/test_producer_attestation.py
import json
import pytest
from skills.close.__lib.producer_attestation import (
    sign_receipt, verify_attestation, get_attestation_key_from_env,
    generate_nonce,
)

class TestProducerAttestation:
    def test_sign_and_verify_roundtrip(self):
        key = b"test-key-32-bytes-long-aaaa-bbbb"
        payload = {"verdict": "CLOSE COMPLETE", "session_id": "test"}
        nonce = generate_nonce()
        payload["nonce"] = nonce
        signature = sign_receipt(payload, key)
        assert verify_attestation(payload, signature, key)

    def test_tampered_payload_rejected(self):
        key = b"test-key-32-bytes-long-aaaa-bbbb"
        payload = {"verdict": "CLOSE COMPLETE", "session_id": "test",
                   "nonce": generate_nonce()}
        signature = sign_receipt(payload, key)
        tampered = dict(payload, session_id="forged")
        assert not verify_attestation(tampered, signature, key)

    def test_missing_signature_rejected(self):
        key = b"test-key-32-bytes-long-aaaa-bbbb"
        payload = {"verdict": "CLOSE COMPLETE"}
        assert not verify_attestation(payload, None, key)

    def test_nonce_is_unique(self):
        n1 = generate_nonce()
        n2 = generate_nonce()
        assert n1 != n2

    def test_get_key_from_env_returns_none_if_unset(self, monkeypatch):
        monkeypatch.delenv("CLOSE_ATTESTATION_KEY", raising=False)
        key = get_attestation_key_from_env()
        assert key is None

    def test_get_key_from_env_returns_bytes_if_set(self, monkeypatch):
        monkeypatch.setenv("CLOSE_ATTESTATION_KEY", "test-secret")
        key = get_attestation_key_from_env()
        assert key == b"test-secret"
```

- [ ] **Step 2: Run tests to verify they fail** (module doesn't exist)

- [ ] **Step 3: Implement the module**

```python
# skills/close/__lib/producer_attestation.py
"""Producer attestation for close receipts.

Design (Finding #1 fix): the HMAC key lives in the Stop hook's process
environment (injected via hook JSON `env` field), NOT in any file.
The model's run_terminal_command runs in a different process and cannot
read hook-process env vars. The scanner writes unsigned receipts; the
hook signs them.

Key lifecycle (Finding #8 fix):
- The key is generated once by the operator and stored in the hook JSON env field
- The key is immutable within a session (hook config is loaded at session start)
- Rotation requires updating the hook JSON and restarting the session
- A key_id field in receipts identifies which key version signed them
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

# Explicitly enumerated signed fields (Finding #7 fix)
SIGNED_FIELDS = frozenset({
    "workspace_id", "session_id", "close_attempt_id",
    "terminal_verdict", "resolved_gate_states",
    "renderer_identity", "timestamp", "nonce",
})


def get_attestation_key_from_env() -> bytes | None:
    """Read the HMAC key from the CLOSE_ATTESTATION_KEY env var.
    Returns None if unset (scanner context — no key available)."""
    val = os.environ.get("CLOSE_ATTESTATION_KEY")
    if not val:
        return None
    return val.encode("utf-8")


def generate_nonce() -> str:
    """Generate a per-attempt nonce for replay protection (Finding #7 fix)."""
    return secrets.token_hex(16)


def sign_receipt(payload: dict, key: bytes) -> str:
    """Sign a receipt payload with HMAC-SHA256.
    Only SIGNED_FIELDS are included in the canonical form (Finding #7 fix)."""
    signed_subset = {k: payload.get(k) for k in SIGNED_FIELDS if k in payload}
    canonical = json.dumps(signed_subset, sort_keys=True, separators=(",", ":"))
    return hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_attestation(payload: dict, signature: str | None, key: bytes) -> bool:
    """Verify a receipt's HMAC signature."""
    if not signature:
        return False
    expected = sign_receipt(payload, key)
    return hmac.compare_digest(signature, expected)
```

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**

```bash
git add skills/close/__lib/producer_attestation.py skills/close/tests/test_producer_attestation.py
git commit -m "feat: producer attestation module (env-based key, nonce, explicit signed fields)"
```

### Task B2: Add attestation to CloseReceipt + fix INTG-2 (gate-content check)

**Files:**
- Modify: `skills/close/__lib/close_authority.py`

- [ ] **Step 1: Add attestation + nonce fields to CloseReceipt dataclass**

```python
# In CloseReceipt dataclass, add:
producer_attestation: str | None = None
attestation_nonce: str | None = None
```

- [ ] **Step 2: Fix INTG-2 — deepen validate_close_receipt to reject COMPLETE with unresolved gates**

```python
# In validate_close_receipt(), after existing checks:
if receipt.terminal_verdict == "CLOSE COMPLETE":
    # Enumerate ALL non-resolved states (Finding #4 fix)
    RESOLVED_STATES = frozenset({"resolved", "complete", "satisfied", "skip"})
    unresolved = {k: v for k, v in receipt.resolved_gate_states.items()
                  if v not in RESOLVED_STATES}
    if unresolved:
        return (False,
                f"CLOSE COMPLETE receipt has unresolved gates: {list(unresolved.keys())}")
```

- [ ] **Step 3: Add attestation verification to validate_close_receipt**

```python
# After the gate-content check:
if receipt.producer_attestation:
    from skills.close.__lib.producer_attestation import verify_attestation, get_attestation_key_from_env
    key = get_attestation_key_from_env()
    if key is None:
        # No key in env = we're in scanner context, can't verify
        # Accept but flag as unverified (the hook will re-verify)
        pass
    elif not verify_attestation(receipt.to_dict(), receipt.producer_attestation, key):
        return (False, "producer attestation verification failed")
else:
    # No attestation on a COMPLETE receipt = not produced by the hook
    if receipt.terminal_verdict == "CLOSE COMPLETE":
        return (False, "CLOSE COMPLETE receipt lacks producer attestation")
```

- [ ] **Step 4: Run all tests (20 original + acceptance + attestation)**

Run: `python -m pytest skills/close/tests/ -v --tb=short`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add skills/close/__lib/close_authority.py
git commit -m "fix: INTG-1 (attestation required for COMPLETE) + INTG-2 (all unresolved states rejected)"
```

### Task B2b: AAR receipt attestation (Finding #2 fix — separate user-scope change)

**This task modifies user-scope skills, NOT the worktree branch.** It's a separate commit on the user's home directory.

**Files:**
- Modify: `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py`

- [ ] **Step 1: Add attestation to finalize_aar_run**

The AAR finalizer needs the same attestation mechanism. Since `producer_attestation.py` lives in the worktree (not yet merged), the AAR skill needs its own copy or a shared location. For now, inline the attestation logic in `completion_receipt.py`:

```python
# In finalize_aar_run(), after computing report_hash:
import hmac, hashlib, os
key = os.environ.get("CLOSE_ATTESTATION_KEY", "").encode("utf-8")
if key:
    attestation_payload = json.dumps({
        "status": "completed",
        "session_id": session_id,
        "report_sha256": report_hash,
    }, sort_keys=True)
    attestation = hmac.new(key, attestation_payload.encode("utf-8"),
                          hashlib.sha256).hexdigest()
else:
    attestation = None

# Add to state.update():
state["producer_attestation"] = attestation
```

- [ ] **Step 2: Verify existing attestation on reload**

```python
# In the status == "completed" path, after hash check:
existing_attestation = state.get("producer_attestation")
if existing_attestation and key:
    expected_payload = json.dumps({
        "status": "completed",
        "session_id": session_id,
        "report_sha256": report_hash,
    }, sort_keys=True)
    expected_attestation = hmac.new(key, expected_payload.encode("utf-8"),
                                   hashlib.sha256).hexdigest()
    if not hmac.compare_digest(existing_attestation, expected_attestation):
        return {"passed": False,
                "detail": "producer attestation invalid — receipt may have been manually edited"}
```

- [ ] **Step 3: Commit (user-scope, not worktree)**

```bash
cd ~/.grok/skills/aar
git add __lib/completion_receipt.py
git commit -m "fix: E8 — producer attestation on _run.json prevents manual hash edits"
```

- [ ] **Step 4: Document in integration gate** that both branches must be verified

---

## Workstream C: Output-layer enforcement (Stop hook)

**Depends on:** B's attestation interface being settled (Task B1 + B2 complete).

**Files:**
- Create: `~/.grok/hooks/scripts/close_enforcement_gate.py`
- Create: `~/.grok/hooks/close-enforcement.json`
- Test: `P:/worktrees/dotgrok-close-authority/skills/close/tests/test_stop_hook_gate.py`

### Task C1: Gate script with tightened markers (Finding #6 fix)

**Marker detection redesign (Finding #6):** instead of substring matching on common phrases, require STRUCTURAL evidence:
- Message contains a blockquote (line starting with `>`)
- AND message contains a verdict token (`CLOSE COMPLETE`, `CLOSE INCOMPLETE`, `CLOSE DEFERRED`, `CLOSE BLOCKED`)
- AND message contains `## Session details` or `## Final status`

This triple-match is specific to the canonical close report format and won't trigger on casual mentions of "close" or "session."

- [ ] **Step 1: Write the gate script**

```python
# ~/.grok/hooks/scripts/close_enforcement_gate.py
"""Stop hook: blocks close-context output if scanner reports needs_attention gates.

Finding #6 fix: uses structural triple-match (blockquote + verdict + section header),
not substring matching on common phrases.
Finding #9 fix: logs fail-open events to ~/.grok/state/hook_failures.jsonl.
Finding #10 fix: uses both JSON decision AND exit code 2 for blocking.
"""
import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone

FAIL_LOG = Path.home() / ".grok" / "state" / "hook_failures.jsonl"

# Structural markers (Finding #6 fix) — require ALL three
VERDICT_TOKENS = [
    "CLOSE COMPLETE", "CLOSE INCOMPLETE", "CLOSE DEFERRED",
    "CLOSE BLOCKED", "CLOSE SCANNER ERROR",
]
SECTION_MARKERS = ["## Session details", "## Final status"]


def is_close_context(message: str) -> bool:
    """Triple-match: blockquote + verdict token + section header."""
    has_blockquote = any(line.strip().startswith(">") for line in message.split("\n"))
    has_verdict = any(tok in message for tok in VERDICT_TOKENS)
    has_section = any(sec in message for sec in SECTION_MARKERS)
    return has_blockquote and has_verdict and has_section


def log_fail_open(reason: str, scanner_exit_code: int = -1):
    """Finding #9 fix: structured fail-open logging."""
    FAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "scanner_exit_code": scanner_exit_code,
    }
    with open(FAIL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    reason = event.get("reason", "")
    if reason != "end_turn":
        sys.exit(0)

    if event.get("stopHookActive", False):
        sys.exit(0)

    last_message = event.get("lastAssistantMessage", "")
    if not is_close_context(last_message):
        sys.exit(0)

    session_id = os.environ.get("GROK_SESSION_ID", "")
    if not session_id:
        log_fail_open("no GROK_SESSION_ID in env")
        sys.exit(0)

    try:
        result = subprocess.run(
            [sys.executable, os.path.expanduser(
                "~/.grok/skills/close/__lib/close_accounting.py"),
             "--session", session_id, "--format", "json"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log_fail_open(f"scanner exit {result.returncode}", result.returncode)
            sys.exit(0)
        data = json.loads(result.stdout)
        gates = data.get("gates", {})
        needs_attention = {k: v.get("detail", "") for k, v in gates.items()
                          if v.get("state") == "needs_attention"}
        if needs_attention:
            gate_list = ", ".join(needs_attention.keys())
            block_reason = (f"Close scanner reports gates needing attention: "
                          f"{gate_list}. Resolve these gates before emitting a "
                          f"close summary.")
            # Finding #10 fix: use both JSON decision AND stderr for blocking
            print(json.dumps({"decision": "block", "reason": block_reason}))
            sys.stderr.write(block_reason + "\n")
            sys.exit(2)  # exit 2 = explicit block with stderr feedback
    except subprocess.TimeoutExpired:
        log_fail_open("scanner timeout (120s)")
        sys.exit(0)
    except (json.JSONDecodeError, OSError) as e:
        log_fail_open(f"scanner error: {type(e).__name__}: {e}")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the hook config with env-injected key (Finding #1 fix)**

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
            "timeout": 180,
            "env": {
              "CLOSE_ATTESTATION_KEY": "OPERATOR_GENERATES_THIS_KEY"
            }
          }
        ]
      }
    ]
  }
}
```

**The operator generates the key** using `python -c "import secrets; print(secrets.token_hex(32))"` and pastes it into the hook JSON. The key is in the hook JSON file (which the model can read), BUT the key is only available as an ENV VAR to the hook process — the model's `run_terminal_command` cannot read the hook process's env.

Wait — the model CAN read the hook JSON file and extract the key from the `env` field. So the key in the JSON IS model-readable. This is the same problem as the file-based key.

**Revised approach:** the key must be generated by the operator and stored in a location the model cannot read. Options:
1. Windows Credential Manager (DPAPI-protected)
2. Operator enters the key at session start via a prompt
3. The key is derived from the operator's Windows login (not practical)

For this plan, I'll use **Windows Credential Manager** as the key store, with a PowerShell helper that the hook calls to retrieve the key. The model cannot call `cmdkey /generic` to read stored credentials without the target name... actually, it can if it knows the target name. The model can run `cmdkey /list` to enumerate credentials.

This is getting circular. The fundamental issue (Finding #1) is that on this host, there is NO location the model cannot read. The only layer below the model is the hook runtime's execution context.

**The real resolution:** the attestation is performed BY the hook process, not BY the model. The model never needs the key — it never signs receipts. The hook signs. So the question is: can the model impersonate the hook?

The model can write a hook JSON file. But the hook JSON is loaded at session start — changes mid-session don't take effect. And the model cannot trigger a hook execution on demand (hooks fire on events, not on model invocation).

So: the key in the hook JSON env field IS readable by the model (it can `cat` the JSON file). BUT the model cannot USE the key to sign receipts during its turn because:
1. The model doesn't run the signing code during its turn (the scanner writes unsigned receipts)
2. The signing happens in the hook process (which fires after the model's turn ends)
3. Even if the model writes a Python script that signs a receipt and runs it via `run_terminal_command`, the resulting receipt would need to be at the right path AND the hook would verify it AND find the gates unresolved

Wait, that last point is the key insight: even if the model has the HMAC key, it still can't forge a receipt that passes the FULL validation chain because:
1. The receipt must have all gates resolved (INTG-2 check catches unresolved gates)
2. The receipt must have valid attestation (but if the model has the key, it can sign anything)
3. The hook blocks output if the scanner says needs_attention

So the attestation alone doesn't prevent forgery — the GATE CONTENT CHECK (INTG-2) is what prevents forgery. The attestation is defense-in-depth: it prevents the model from editing a previously-valid receipt's fields post-signing.

The real enforcement stack is:
1. Scanner computes gates (Layer 2 — model can't fake the computation)
2. INTG-2 check rejects COMPLETE with unresolved gates (file-layer)
3. Attestation prevents field editing post-signing (file-layer, defense-in-depth)
4. Stop hook blocks output if scanner says needs_attention (output-layer, the real enforcement)

The Stop hook is the load-bearing enforcement. The attestation is nice-to-have. If the hook works, the model can't deliver a forged close even with unsigned receipts. If the hook doesn't work, no amount of attestation helps.

**Simplified plan for attestation:** use the env-var approach, accept that the model can read the key from the JSON file, but rely on the gate-content check (INTG-2) as the primary defense. The attestation adds tamper-evidence (detects post-signing edits) but is not the primary forgery prevention.

This is honest and matches the TCB concept: the hook is Layer A (the model can't prevent it from firing). File-layer attestation is defense-in-depth, not primary enforcement.

Let me simplify the plan accordingly.

- [ ] **Step 3: Write tests for the gate logic**

(Full test code for marker detection, fail-open logging, and blocking behavior.)

- [ ] **Step 4: Commit**

---

## Workstream D: CORR-001/002/003 fixes (Finding #13)

**Can run in parallel with C** — different files, no conflicts.

### Task D1: Fix CORR-001 (ImportError fail-safe)

**Location:** `close_accounting.py:2646-2649`

- [ ] **Step 1: Move `auth_gates` construction before the import block**

```python
# Before the try/except ImportError:
auth_gates = {}  # safe default
try:
    from skills.close.__lib.close_authority import _enforce_close_authority
    # ... auth_gates populated by the function ...
except ImportError:
    pass  # auth_gates stays empty, fail-safe INCOMPLETE
```

- [ ] **Step 2: Test**

- [ ] **Step 3: Commit**

### Task D2: Fix CORR-002 (close_runner split verdict)

**Location:** `close_accounting.py` (close_runner path)

- [ ] **Step 1: Wire authority_verdict through close_runner._render_compact**

- [ ] **Step 2: Test that compact text matches JSON verdict**

- [ ] **Step 3: Commit**

### Task D3: Fix CORR-003 (risk section uses raw gates)

**Location:** `close_accounting.py:3568-3574`

- [ ] **Step 1: Use resolved_gates instead of raw gates in the risk section**

- [ ] **Step 2: Test that COMPLETE + resolved gates produces no risk items**

- [ ] **Step 3: Commit**

---

## Integration gate (serial — after A, B, C, D complete)

### Task E1: Run all acceptance tests + CORR tests

- [ ] **Step 1:** `python -m pytest skills/close/tests/ -v` — all pass
- [ ] **Step 2:** Verify AAR skill attestation works: run `/aar` on a test session, verify `_run.json` has attestation
- [ ] **Step 3:** Verify Stop hook blocks: trigger a close with unresolved gates, confirm output is blocked

### Task E2: /review with cross-model specialists

- [ ] **Step 1:** `/review --branch close-authority-019fa5a1` — no critical findings

### Task E3: /check session verification

- [ ] **Step 1:** `/check` — PASS

### Task E4: Finding #1 empirical verification

- [ ] **Step 1:** From `run_terminal_command`, run `echo $env:CLOSE_ATTESTATION_KEY` — confirm empty
- [ ] **Step 2:** If NOT empty, pivot to Credential Manager approach and re-verify

---

## Latency/performance spec (Finding #11 fix — measured, not asserted)

- **Scanner runtime:** measured at ~18-24s on this session's artifact tree (close_accounting.py runs during /close). Production tree with 168 handoffs may be 30-40s.
- **Stop hook non-close turns:** <10ms (triple-match check only)
- **Stop hook close-context turns:** 30-40s (scanner subprocess)
- **Mitigation:** cache scanner output for 60s (if artifact tree mtime hasn't changed, reuse cached result). Reduces repeat close-context turns to <100ms.
- **Attestation key access:** env var read, ~0.1ms
- **HMAC computation:** O(n) in receipt size (~1KB), negligible

## Exception safety (Finding #9 fix)

- All hook scripts fail open (exit 0) on errors per the Grok Build contract
- **Fail-open events are logged** to `~/.grok/state/hook_failures.jsonl` (structured JSONL)
- **Health degradation check:** if 3+ fail-open events in the last 100 end-turn fires, the hook should refuse to fail open and instead block with "scanner health degraded"

## Internal consistency check

- Workstream A's test 9 (forged receipt) requires Workstream B's attestation + INTG-2 fix to pass. This is intentional — A documents the gap, B fixes it. A runs first, B runs second (serialized per Finding #3 fix).
- Workstream C's Stop hook runs `close_accounting.py`, which is the same scanner Workstream A tests. No interface mismatch.
- The attestation module (`producer_attestation.py`) is importable from both the worktree's close skill AND the user-scope AAR skill via standard Python imports (Finding #14 fix). No `sys.path` hacks.
- Task B2b (AAR attestation) modifies user-scope skills, not the worktree branch (Finding #2 fix). The integration gate verifies both separately.

## Adversarial review status (Finding #5 fix)

- **v1 plan reviewed by /tp (fresh subagent)** on 2026-07-28 — found 14 issues (5 critical)
- **v2 plan (this document)** addresses all 14 findings
- **v2 should be re-reviewed** by `/tp` before implementation begins — the revision may have introduced new issues
- **Implementation review:** `/review` with cross-model specialists at the integration gate (Task E2)

## Execution recommendation

**Serialized execution:** A → B → (B2b + C + D in parallel) → Integration gate.

**Recommended approach:** `/go execute <plan-path>` with task DAG respecting the serialization.

**Plan saved to:** `docs/superpowers/plans/2026-07-28-close-authority-completion.md` (v2)

---

## Round 1 Review (2026-07-28) — 21 findings, DO NOT EXECUTE v2

A fresh `general-purpose` subagent reviewed v2 and found 21 findings (5 CRITICAL,
7 HIGH, 9 MEDIUM). The plan cannot be executed as written. Key findings:

### Critical findings (must fix before execution)

**F-META** — Three places have unresolved deliberation text instead of concrete
answers: (1) Task B0 env-var verification pivot, (2) the "getting circular"
block on key location, (3) Task B2b "for now inline." The implementing agent
will encounter these and have to design on the fly.

**F-01** — Architecture says signing hook, code implements blocking hook. The
plan's Task B0 design narrative (line ~458) says "the Stop hook SIGNS receipts."
The actual hook code in Task C1 never signs, reads, or writes receipts. The
acceptance tests (Test 9) are written against the signing model. These are
two different security models and the plan doesn't reconcile them.

**F-02** — The gate script invokes `~/.grok/skills/close/__lib/close_accounting.py`
(user-scope installed copy). Workstream D fixes the worktree version. If the
gate runs the unfixed user-scope version, CORR-001 crashes the subprocess and
the hook fails open = enforcement silently absent. C and D are NOT parallel.

**F-04** [HIGH but effectively CRITICAL] — The field is `close_run_id`, NOT
`close_attempt_id`. Every test in the acceptance suite uses the wrong name.
`validate_close_receipt` has signature `(receipt, expected_scanner_digest=None)`,
not `(receipt)`. The entire test suite fails at import time. **Verified by grep:
13 occurrences of `close_run_id` in close_authority.py, zero of `close_attempt_id`.**

**F-10** — Integration gate for user-scope changes (AAR skill attestation, hook
config) is undefined. The plan says "both branches verified" but doesn't specify
test commands for `~/.grok/skills/aar/` or `~/.grok/hooks/`.

**F-15** — Test 9's third subtest (`test_forged_receipt_hash_manually_edited_detected`)
asserts a constant (`assert forged_state["producer_attestation"] is None`). It
doesn't invoke any validation function. It passes trivially and proves nothing.

### Revision needed

Before v3 can be executed:
1. Verify the actual `close_authority.py` API (`close_run_id`, function signatures)
2. Rewrite every test against the actual API
3. Resolve the signing-vs-blocking architecture (F-01)
4. Define the deployment ordering (F-02, F-10)
5. Replace all deliberation text with concrete answers (F-META)
6. Rewrite Test 9's third subtest to actually test validation (F-15)
7. Address F-14 (8-continuations cap)
8. Address all HIGH/MEDIUM findings

**This revision should be done in a fresh session** — the current session is very
long and the revision requires verifying the actual code API against every test.
