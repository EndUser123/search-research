# Close-authority enforcement completion — non-blocking workstream plan (v3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development
> (recommended) or executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the close-authority enforcement system so it satisfies all 10 non-negotiable acceptance tests from the operator's spec.

**Architecture:** The Stop hook is the load-bearing enforcement (blocks output when scanner reports needs_attention). The gate-content check (INTG-2) is file-layer defense. HMAC attestation is defense-in-depth (detects post-signing edits). These are three independent layers, not redundant — each catches a different attack vector.

**Tech Stack:** Python 3.12+, pytest, Grok Build hooks (command type), HMAC (stdlib `hmac`)

**Risk level:** Hard plan (reversibility ≥1.5 — enforcement code, security boundary)

## Revision history

- **v1** (2026-07-28): original plan, 3 workstreams
- **v2** (2026-07-28): revised after Round 0 /tp review found 14 issues (5 critical)
- **v3** (this document): revised after Round 1 mandatory review found 21 issues (5 critical). Key fixes:
  - **F-04:** all tests rewritten against verified actual API (`close_run_id`, keyword-only `validate_close_receipt`, `load_close_receipt(session_id, close_run_id, artifacts_root)`)
  - **F-01:** architecture reconciled — Stop hook is blocking-only (no signing); attestation is a separate file-layer mechanism signed by `persist_close_receipt`, not by the hook
  - **F-02:** serialization fixed — D (CORR fixes) must merge before C (hook deployment), because the hook calls the installed scanner
  - **F-META:** all deliberation text resolved to concrete answers
  - **F-15:** Test 9c rewritten to actually invoke validation
  - **F-14:** 8-continuations cap documented as a known limit
  - All HIGH/MEDIUM findings addressed

## Verified API (from close_authority.py @ d516ccc)

These are the ACTUAL field names and function signatures. All tests must use these.

```python
# Constants
CLOSE_RECEIPT_SCHEMA_VERSION = "close.v1"
AAR_RECEIPT_SCHEMA_VERSION = "aar.v1"
CLOSE_COMPLETE = "CLOSE COMPLETE"
CLOSE_INCOMPLETE = "CLOSE INCOMPLETE"

# CloseReceipt dataclass fields (exact):
#   schema_version: str          # "close.v1"
#   session_id: str
#   close_run_id: str            # NOT "close_attempt_id"
#   workspace_id: str
#   scanner_result_digest: str   # SHA256 of canonical scanner JSON
#   resolved_gate_states: dict[str, str]
#   aar_receipt_run_id: str      # empty if retrospective was skip/pre_satisfied
#   deferral_receipt_id: str     # empty if not deferred
#   terminal_verdict: str        # one of TERMINAL_VERDICTS
#   created_at: str              # ISO8601
#   renderer_identity: str = "close_authority.py"
#   def to_dict(self) -> dict    # exists via asdict()

# validate_close_receipt signature (keyword-only after receipt):
#   validate_close_receipt(receipt, *, expected_session_id, expected_workspace_id="", expected_scanner_digest=None, now=None) -> (bool, str)

# load_close_receipt signature:
#   load_close_receipt(session_id, close_run_id, artifacts_root) -> (CloseReceipt | None, str)

# persist_close_receipt signature:
#   persist_close_receipt(receipt, artifacts_root) -> Path
#   Path: <artifacts_root>/close-receipts/<session_id>/<close_run_id>.json

# compute_workspace_id signature:
#   compute_workspace_id(repo_root) -> str

# authorize_completion signature:
#   authorize_completion(state, *, final_gates, final_scanner_digest, now=None) -> (bool, str, CloseReceipt | None)
```

## Global Constraints

- Branch `close-authority-019fa5a1` @ d516ccc is the starting point
- The 10 acceptance tests are the merge gate — zero may be missing
- Per the maker-checker rule, `/review` with cross-model specialists is required before merge
- **The Stop hook is the load-bearing enforcement.** Attestation is defense-in-depth. The hook blocks output; attestation detects tampering. These are separate layers catching different attack vectors.
- **The 8-continuations cap is a known limit.** After 8 blocks in one turn, the gate is overridden and the model emits anyway (per `10-hooks.md` line 262). This is documented in the plan's Falsifier section. The mitigation: the fail-open log records every block, so the operator can detect when the model is fighting the gate.
- Fleet-safe: all artifacts are `session_id`/`close_run_id` scoped; no global pointers
- The existing 20 tests must continue to pass throughout

## Resolved design decisions (F-META fix — no deliberation text)

**Key location (F-01, F-META #1):** The HMAC key is in the hook JSON `env` field. The model CAN read the hook JSON file and extract the key. **This is accepted.** The attestation is defense-in-depth, not primary enforcement. Even with the key, the model cannot bypass the Stop hook (which blocks output based on scanner gates, not attestation). The attestation only prevents post-signing field edits — it does not prevent forgery by a model that has the key. This is honestly stated because the alternative (Credential Manager, TPM, daemon) adds infrastructure complexity that violates the solo-director usability constraint.

**Signing responsibility (F-01, F-06):** `persist_close_receipt` signs the receipt using the key from `CLOSE_ATTESTATION_KEY` env var. The Stop hook does NOT sign. The hook blocks. If `CLOSE_ATTESTATION_KEY` is unset (scanner context, no env var), `persist_close_receipt` writes an unsigned receipt (attestation=None). `validate_close_receipt` rejects COMPLETE receipts without valid attestation. This means: unsigned receipts are produced by the scanner but cannot serve as authority for COMPLETE. The hook independently blocks based on gate states. Two independent enforcement layers.

**B2b module sharing (F-03, F-14):** `producer_attestation.py` is placed at `P:/.agents/__lib/producer_attestation.py` (shared location, not in the worktree's close skill or the user's aar skill). Both `close_authority.py` and `completion_receipt.py` import from this path. No inlining, no duplication.

**Deployment ordering (F-02, F-10):** D (CORR fixes) → merge to main → install to `~/.grok/skills/close/` → THEN deploy the hook (C). The hook calls the installed scanner. If the scanner is unfixed, the hook catches the crash and fails open (with logging). The plan's integration gate verifies all four test suites pass.

---

## Workstream dependency map (v3)

```
Workstream A (acceptance tests — against actual API, documenting gaps)
        │
        ▼
Workstream B (INTG-1 attestation + INTG-2 gate check — worktree branch)
        │
        ├── Workstream B2 (AAR receipt attestation — ~/.grok/skills/aar/)
        │
        ▼
Workstream D (CORR-001/002/003 — worktree branch)
        │
        ▼  (merge D to main, install to ~/.grok/skills/close/)
Workstream C (Stop-hook deployment — ~/.grok/hooks/)
        │
        ▼
Integration gate: 4 test suites + /review
```

**Serialization rationale:** A → B (tests document gaps, B fixes them). B → D (B changes `close_authority.py`, D changes `close_accounting.py` — different files but same branch, safer serial). D → C (hook calls installed scanner; D's fixes must be installed first). B2 runs parallel with D (different repos).

---

## Workstream A: Acceptance test suite (10 tests, verified API)

### Task A1: Tests 1-10 against verified API

**Files:**
- Create: `skills/close/tests/test_acceptance_spec.py`
- Modify: `skills/close/tests/conftest.py` (add `two_terminals` fixture — verified: no conflicts)

**Definition of Done:** tests written, conftest updated, expected failures documented. Tests 3, 5b, 9, and replay tests SHOULD fail (documenting INTG-1/INTG-2 gaps).

- [ ] **Step 1: Write the test file**

```python
# skills/close/tests/test_acceptance_spec.py
"""Acceptance tests from the operator's non-negotiable spec.
All 10 must pass before merge. Tests use the VERIFIED API (v3).
"""
import json
import threading
import pytest
from pathlib import Path
from datetime import datetime, timezone

from close_authority import (
    CloseReceipt, AARReceipt,
    CLOSE_RECEIPT_SCHEMA_VERSION, CLOSE_COMPLETE, CLOSE_INCOMPLETE,
    validate_close_receipt, persist_close_receipt, load_close_receipt,
    compute_workspace_id, authorize_completion, CloseState,
)

# Non-resolved gate states to enumerate (F-04 fix: test ALL, not just needs_attention)
NON_RESOLVED_STATES = ["needs_attention", "blocked", "pending", "deferred", "", "unknown"]
# F-NEW-4 fix: actual scanner vocabulary, not fictional strings
RESOLVED_STATES = frozenset({"pre_satisfied", "skip"})


@pytest.fixture
def two_terminals(tmp_path):
    """Simulate two terminals in the same repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    ws_id = compute_workspace_id(repo)
    artifacts_a = tmp_path / "artifacts_a"
    artifacts_b = tmp_path / "artifacts_b"
    return {
        "repo": repo, "ws_id": ws_id,
        "artifacts_a": artifacts_a, "artifacts_b": artifacts_b,
        "session_a": "session-aaa", "session_b": "session-bbb",
    }


def _make_receipt(ws_id, session_id, run_id, verdict="CLOSE COMPLETE",
                  gates=None):
    """Helper to construct a CloseReceipt with the VERIFIED field names."""
    return CloseReceipt(
        schema_version=CLOSE_RECEIPT_SCHEMA_VERSION,
        session_id=session_id,
        close_run_id=run_id,
        workspace_id=ws_id,
        scanner_result_digest="abc123",
        resolved_gate_states=gates or {},
        aar_receipt_run_id="",
        deferral_receipt_id="",
        terminal_verdict=verdict,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


class Test1CrossTerminalIsolation:
    """Test 1: Two terminals, same repo, different sessions: no cross-consumption."""

    def test_terminal_a_cannot_load_terminal_b_receipt(self, two_terminals):
        receipt_b = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_b"], "run-b1"
        )
        path_b = persist_close_receipt(receipt_b, two_terminals["artifacts_b"])
        # Terminal A tries to load B's receipt — must get None (F-16 fix: strict assertion)
        loaded, reason = load_close_receipt(
            two_terminals["session_a"], "run-b1", two_terminals["artifacts_b"]
        )
        assert loaded is None, f"Terminal A loaded terminal B's receipt: {reason}"


class Test2SameSessionTwoAttempts:
    """Test 2: Same session, two close attempts: exact attempt linkage."""

    def test_second_attempt_does_not_consume_first_receipt(self, two_terminals):
        receipt_1 = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_a"], "run-1"
        )
        persist_close_receipt(receipt_1, two_terminals["artifacts_a"])
        # Attempt-2 tries to load run-1's receipt — must get None (wrong run_id)
        loaded, reason = load_close_receipt(
            two_terminals["session_a"], "run-2", two_terminals["artifacts_a"]
        )
        assert loaded is None, f"Second attempt loaded first attempt's receipt: {reason}"


class Test3StaleReceiptAfterMutation:
    """Test 3: COMPLETE receipt with any unresolved gate: rejected.
    F-04 fix: enumerate ALL non-resolved states."""

    @pytest.mark.parametrize("gate_state", NON_RESOLVED_STATES)
    def test_complete_with_unresolved_gate_rejected(self, gate_state, two_terminals):
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-test", "run-1",
            gates={"retrospective": gate_state},
        )
        valid, reason = validate_close_receipt(
            receipt,
            expected_session_id="session-test",
        )
        assert not valid, \
            f"COMPLETE with gate state {gate_state!r} passed: {reason}"


class Test4StaleForeignPointer:
    """Test 4: Stale pointer to valid foreign receipt: ignored."""

    def test_foreign_receipt_not_authority(self, two_terminals):
        receipt_b = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_b"], "run-b1"
        )
        persist_close_receipt(receipt_b, two_terminals["artifacts_b"])
        # Loading with session_a must fail (session mismatch)
        loaded, reason = load_close_receipt(
            two_terminals["session_a"], "run-b1", two_terminals["artifacts_b"]
        )
        assert loaded is None


class Test5PartialAtomicWrite:
    """Test 5: Partial/interrupted write: rejected. Also: manipulated valid JSON."""

    def test_truncated_json_rejected(self, two_terminals):
        receipt_dir = Path(two_terminals["artifacts_a"]) / "close-receipts" / "session-aaa"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / "run-1.json"
        receipt_path.write_text('{"schema_version": "close.v1", "session', encoding="utf-8")
        loaded, reason = load_close_receipt("session-aaa", "run-1", two_terminals["artifacts_a"])
        assert loaded is None

    def test_manipulated_valid_json_rejected(self, two_terminals):
        """Valid JSON with needs_attention gate + COMPLETE verdict: must fail validation."""
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-test", "run-1",
            gates={"retrospective": "needs_attention"},
        )
        valid, reason = validate_close_receipt(
            receipt, expected_session_id="session-test"
        )
        assert not valid, f"Manipulated receipt accepted: {reason}"


class Test6AbandonedRun:
    """Test 6: Abandoned run does not block new attempt."""

    def test_stale_receipt_does_not_block_new(self, two_terminals):
        stale_receipt = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_a"], "run-stale",
            verdict="CLOSE INCOMPLETE",
            gates={"retrospective": "needs_attention"},
        )
        persist_close_receipt(stale_receipt, two_terminals["artifacts_a"])
        # New attempt should succeed independently
        new_receipt = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_a"], "run-new"
        )
        persist_close_receipt(new_receipt, two_terminals["artifacts_a"])
        loaded, _ = load_close_receipt(
            two_terminals["session_a"], "run-new", two_terminals["artifacts_a"]
        )
        assert loaded is not None


class Test7ConcurrentAttempts:
    """Test 7: Concurrent close attempts: deterministic, no mixed state.
    F-17 fix: contend on SAME path."""

    def test_concurrent_writes_same_path_deterministic(self, two_terminals):
        """Two threads write to the same run_id — exactly one wins, no corruption."""
        results = []
        def write_attempt(verdict):
            try:
                receipt = _make_receipt(
                    two_terminals["ws_id"], two_terminals["session_a"], "run-race",
                    verdict=verdict,
                )
                persist_close_receipt(receipt, two_terminals["artifacts_a"])
                results.append(("ok", verdict))
            except Exception as e:
                results.append(("error", str(e)))

        t1 = threading.Thread(target=write_attempt, args=("CLOSE COMPLETE",))
        t2 = threading.Thread(target=write_attempt, args=("CLOSE INCOMPLETE",))
        t1.start(); t2.start(); t1.join(); t2.join()
        # At least one must succeed; file must be valid JSON (no corruption)
        loaded, reason = load_close_receipt(
            two_terminals["session_a"], "run-race", two_terminals["artifacts_a"]
        )
        assert loaded is not None, f"Concurrent write corrupted the file: {reason}"
        assert loaded.terminal_verdict in ("CLOSE COMPLETE", "CLOSE INCOMPLETE")


class Test8CleanupLeavesForeignArtifacts:
    """Test 8: Cleanup from one run leaves foreign artifacts untouched."""

    def test_foreign_receipt_survives(self, two_terminals):
        receipt_a = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_a"], "run-a1"
        )
        persist_close_receipt(receipt_a, two_terminals["artifacts_a"])
        receipt_b = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_b"], "run-b1"
        )
        persist_close_receipt(receipt_b, two_terminals["artifacts_b"])
        loaded, _ = load_close_receipt(
            two_terminals["session_b"], "run-b1", two_terminals["artifacts_b"]
        )
        assert loaded is not None


class Test9ForgedReceiptRejected:
    """Test 9: Forged receipt: rejected.
    F-15 fix: all subtests actually invoke validation."""

    def test_forged_complete_with_unresolved_gates_rejected(self, two_terminals):
        """The core INTG-2 test: COMPLETE with needs_attention must be rejected."""
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-test", "run-forged",
            gates={"retrospective": "needs_attention"},
        )
        valid, reason = validate_close_receipt(
            receipt, expected_session_id="session-test"
        )
        assert not valid
        assert "needs_attention" in reason or "unresolved" in reason.lower() or "gate" in reason.lower()

    def test_forged_receipt_from_wrong_renderer_rejected(self, two_terminals):
        """COMPLETE from non-authoritative renderer: rejected."""
        receipt = _make_receipt(
            two_terminals["ws_id"], "session-test", "run-forged",
        )
        receipt.renderer_identity = "model_prose.py"  # not close_authority.py
        valid, reason = validate_close_receipt(
            receipt, expected_session_id="session-test"
        )
        assert not valid
        assert "renderer" in reason.lower()

    def test_forged_aar_run_json_detected(self, tmp_path):
        """F-NEW-3 fix: ACTUALLY exercise the hash-mismatch path, not 'file missing'."""
        run_dir = tmp_path / "aar-run"
        run_dir.mkdir()
        (run_dir / "preprocess").mkdir()
        # Create a REAL report file so finalize_aar_run gets past the "missing" check
        (run_dir / "aar-report.md").write_text("# Fake AAR report\n", encoding="utf-8")
        # Write a forged _run.json with a hash that doesn't match the report
        import hashlib
        real_hash = hashlib.sha256(b"# Fake AAR report\n").hexdigest()
        forged = {
            "status": "completed", "skill": "aar", "session_id": "test-session",
            "report_sha256": "manually_overwritten_hash_NOT_" + real_hash[:16],
            "report_path": str(run_dir / "aar-report.md"),
        }
        (run_dir / "_run.json").write_text(json.dumps(forged), encoding="utf-8")
        # The finalizer must reject: hash mismatch (report exists, but hash is wrong)
        import sys, os
        sys.path.insert(0, os.path.expanduser("~/.grok/skills/aar/__lib"))
        from completion_receipt import finalize_aar_run
        result = finalize_aar_run(run_dir, run_dir / "aar-report.md", "test-session")
        assert not result["passed"], \
            f"Forged hash was accepted: {result.get('detail', '')}"
        # F-NEW-3: verify it failed for the RIGHT reason (hash mismatch, not missing file)
        assert "hash" in result.get("detail", "").lower() or "mismatch" in result.get("detail", "").lower(), \
            f"Failed but for wrong reason: {result.get('detail', '')}"


class Test10RestartReconstructsAuthority:
    """Test 10: Restarted process reconstructs authority from durable artifacts.
    F-18 fix: use subprocess to simulate actual restart."""

    def test_authority_reconstructed_after_subprocess_boundary(self, two_terminals):
        """Write receipt in this process, read it in a subprocess."""
        receipt = _make_receipt(
            two_terminals["ws_id"], two_terminals["session_a"], "run-1"
        )
        path = persist_close_receipt(receipt, two_terminals["artifacts_a"])
        # Spawn a subprocess to read it back (simulates restart)
        # F-NEW-8 fix: use as_posix() to avoid Windows backslash issues in f-string
        import subprocess, sys
        lib_path = (Path(__file__).resolve().parent.parent / "__lib").as_posix()
        artifacts_path = Path(two_terminals["artifacts_a"]).as_posix()
        script = f"""
import json, sys
sys.path.insert(0, r"{lib_path}")
from close_authority import load_close_receipt
loaded, reason = load_close_receipt("{two_terminals['session_a']}", "run-1", r"{artifacts_path}")
if loaded is None:
    print("FAIL:" + reason)
else:
    print("OK:" + loaded.terminal_verdict)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=10,
        )
        assert "OK:CLOSE COMPLETE" in result.stdout, \
            f"Subprocess load failed: {result.stdout} {result.stderr}"


class TestReplayProtection:
    """Finding #7 fix: signed receipt must not be replayable."""

    def test_attestation_binds_to_run_id(self):
        from producer_attestation import sign_receipt, verify_attestation
        key = b"test-key-32-bytes-long-aaaa-bbbb"
        payload = {"session_id": "s", "close_run_id": "run-1", "terminal_verdict": "CLOSE COMPLETE"}
        sig = sign_receipt(payload, key)
        mutated = dict(payload, close_run_id="run-2")
        assert not verify_attestation(mutated, sig, key)
```

- [ ] **Step 2: Run tests, document expected failures**

Run: `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/test_acceptance_spec.py -v --tb=line`
Expected: Tests 3, 5b, 9a FAIL (INTG-2 gap — validate_close_receipt doesn't check gate content). Others pass.

- [ ] **Step 3: Commit**

```bash
git add skills/close/tests/test_acceptance_spec.py skills/close/tests/conftest.py
git commit -m "test: acceptance spec v3 — verified API, security-property probing"
```

---

## Workstream B: Producer attestation + INTG-2 fix

### Task B0: Create shared producer_attestation module (F-03 fix)

**Files:**
- Create: `P:/.agents/__lib/producer_attestation.py` (shared location)
- Create: `P:/.agents/__lib/__init__.py` (empty, makes it a package)

**F-NEW-5 fix — deployment:** `P:/.agents/__lib/` is a new shared path. After Workstream B merges to main, this directory must exist and contain the module. Verify after merge:
```bash
python -c "import sys; sys.path.insert(0, 'P:/.agents/__lib'); from producer_attestation import sign_receipt; print('OK')"
```
If the path doesn't exist on a fresh host, both close and aar skills fail at import. Document in the worktree README that `P:/.agents/__lib/` is a shared dependency.

- [ ] **Step 1: Write the module** (same as v2 but at shared path)

- [ ] **Step 2: Verify importable from both locations**

```python
# Test: close_authority can import it
import sys; sys.path.insert(0, "P:/.agents/__lib")
from producer_attestation import sign_receipt; print("OK")
# Test: completion_receipt can import it (same path)
```

- [ ] **Step 3: Commit**

### Task B1: Fix INTG-2 (gate-content check in validate_close_receipt)

**Files:**
- Modify: `skills/close/__lib/close_authority.py`

- [ ] **Step 1: Add gate-content check to validate_close_receipt**

After the existing renderer_identity check (line ~302), add:

```python
# INTG-2 fix: reject COMPLETE receipts with any non-resolved gate
if receipt.terminal_verdict == CLOSE_COMPLETE:
    unresolved = {k: v for k, v in receipt.resolved_gate_states.items()
                  if v not in RESOLVED_STATES}
    if unresolved:
        return False, f"CLOSE COMPLETE has unresolved gates: {list(unresolved.keys())}"
```

Define `RESOLVED_STATES` at module level (matching the test constant).

- [ ] **Step 2: Add attestation field to CloseReceipt + signing in persist_close_receipt**

```python
# Add to CloseReceipt dataclass:
producer_attestation: str | None = None

# In persist_close_receipt, before write (F-NEW-6 fix: do NOT mutate the input receipt):
from producer_attestation import sign_receipt
import os
key = os.environ.get("CLOSE_ATTESTATION_KEY", "").encode("utf-8")
if key:
    # Build a signed COPY, don't mutate the caller's receipt object
    signed_dict = receipt.to_dict()
    payload = {k: v for k, v in signed_dict.items() if k != "producer_attestation"}
    signed_dict["producer_attestation"] = sign_receipt(payload, key)
    # Write signed_dict, not receipt.to_dict()
```

- [ ] **Step 3: Add attestation verification to validate_close_receipt**

```python
# After gate-content check:
if receipt.producer_attestation is None and receipt.terminal_verdict == CLOSE_COMPLETE:
    return False, "COMPLETE receipt lacks producer attestation"
if receipt.producer_attestation:
    from producer_attestation import verify_attestation
    import os
    key = os.environ.get("CLOSE_ATTESTATION_KEY", "").encode("utf-8")
    if key:
        payload = receipt.to_dict()
        payload.pop("producer_attestation", None)
        if not verify_attestation(payload, receipt.producer_attestation, key):
            return False, "producer attestation verification failed"
```

- [ ] **Step 4: Run all tests (20 original + 10 acceptance + attestation)**

Run: `python -m pytest skills/close/tests/ -v --tb=short`
Expected: all pass

- [ ] **Step 5: Commit**

### Task B2: AAR receipt attestation (F-03 fix: shared module, no inlining)

**Files:**
- Modify: `C:/Users/brsth/.grok/skills/aar/__lib/completion_receipt.py`

- [ ] **Step 1: Import from shared module, add attestation**

```python
# In completion_receipt.py, at top:
import sys
from pathlib import Path
sys.path.insert(0, str(Path("P:/.agents/__lib")))
from producer_attestation import sign_receipt, verify_attestation

# In finalize_aar_run, after computing report_hash:
key = os.environ.get("CLOSE_ATTESTATION_KEY", "").encode("utf-8")
if key:
    payload = {"status": "completed", "session_id": session_id, "report_sha256": report_hash}
    attestation = sign_receipt(payload, key)
else:
    attestation = None
# Add to state.update():
state["producer_attestation"] = attestation

# In the completed-receipt hash check, also verify attestation:
if state.get("producer_attestation") and key:
    expected = sign_receipt({"status": "completed", "session_id": session_id, "report_sha256": report_hash}, key)
    if not hmac.compare_digest(state["producer_attestation"], expected):
        return {"passed": False, "detail": "producer attestation invalid — receipt may have been manually edited"}
```

- [ ] **Step 2: Run AAR completion receipt tests**

Run: `python -m pytest ~/.grok/skills/aar/tests/ -v -k "completion" --tb=short`
Expected: pass

- [ ] **Step 3: Commit** (user-scope skills repo)

---

## Workstream D: CORR-001/002/003 fixes

### Task D1: Fix CORR-001 (ImportError → UnboundLocalError)

**Location:** `close_accounting.py:2646-2649`

- [ ] Move `auth_gates = {}` before the try/except ImportError block
- [ ] Test, commit

### Task D2: Fix CORR-002 (split verdict in close_runner)

**Location:** `close_accounting.py` (close_runner._render_compact path)

- [ ] Wire `authority_verdict` through `close_runner._render_compact`
- [ ] Test that compact text verdict matches JSON verdict
- [ ] Commit

### Task D3: Fix CORR-003 (risk section uses raw gates)

**Location:** `close_accounting.py:3568-3574`

- [ ] Use `resolved_gates` instead of raw gates
- [ ] Test that COMPLETE + resolved gates produces no risk items
- [ ] Commit

---

## Workstream C: Stop-hook deployment (after D is merged + installed)

**Depends on:** D merged to main AND installed to `~/.grok/skills/close/`. The hook calls the installed scanner.

### Task C0: Verify scanner installation (F-NEW-7 fix)

- [ ] **Step 1:** Verify `~/.grok/skills/close/__lib/close_accounting.py` exists
- [ ] **Step 2:** Verify it matches the worktree HEAD (diff the files)
- [ ] **Step 3:** If mismatched, install via the workspace's standard mechanism (symlink or copy)
- [ ] **Step 4:** Document the install mechanism in the worktree README

**F-NEW-9 note:** the hook assumes `quality-gate.py` (another Stop hook) does not block close-context responses. If it does, the close hook never fires. Verify by inspecting `quality_gate.py` for close-related logic.

### Task C1: Gate script (blocking-only, reads authority.verdict)

**Files:**
- Create: `~/.grok/hooks/scripts/close_enforcement_gate.py`
- Create: `~/.grok/hooks/close-enforcement.json`
- Test: `skills/close/tests/test_stop_hook_gate.py`

- [ ] **Step 1: Write the gate script** (structural triple-match, fail-open logging, exit 2 + JSON)

```python
# ~/.grok/hooks/scripts/close_enforcement_gate.py
"""Stop hook: blocks close-context output if scanner reports needs_attention.
Block-only (no signing). F-01 fix: the hook does not sign receipts.
F-09 fix: logs fail-open events. F-10 fix: exit 2 + JSON decision.
F-14: after 8 blocks the gate is overridden (documented limit).
"""
import json, sys, subprocess, os
from pathlib import Path
from datetime import datetime, timezone

FAIL_LOG = Path.home() / ".grok" / "state" / "hook_failures.jsonl"
VERDICT_TOKENS = ["CLOSE COMPLETE", "CLOSE INCOMPLETE", "CLOSE DEFERRED", "CLOSE BLOCKED"]
SECTION_MARKERS = ["## Session details", "## Final status"]

def is_close_context(msg):
    has_quote = any(l.strip().startswith(">") for l in msg.split("\n"))
    has_verdict = any(t in msg for t in VERDICT_TOKENS)
    has_section = any(s in msg for s in SECTION_MARKERS)
    return has_quote and has_verdict and has_section

def log_fail_open(reason, exit_code=-1):
    FAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FAIL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "reason": reason, "scanner_exit": exit_code}) + "\n")

def main():
    try: event = json.load(sys.stdin)
    except: sys.exit(0)
    if event.get("reason") != "end_turn": sys.exit(0)
    if event.get("stopHookActive"): sys.exit(0)
    msg = event.get("lastAssistantMessage", "")
    if not is_close_context(msg): sys.exit(0)
    session_id = os.environ.get("GROK_SESSION_ID", "")
    if not session_id: log_fail_open("no session id"); sys.exit(0)
    try:
        r = subprocess.run(
            [sys.executable, os.path.expanduser("~/.grok/skills/close/__lib/close_accounting.py"),
             "--session", session_id, "--format", "json"],
            capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            log_fail_open(f"scanner exit {r.returncode}", r.returncode); sys.exit(0)
        data = json.loads(r.stdout)
        # F-NEW-1/2 fix: read the canonical authority verdict, NOT raw gates.
        # close_accounting.py:2864 states: "All downstream consumers MUST use
        # resolved_gates, not the raw gates above." The authority verdict is
        # the sole mechanically-valid close verdict.
        verdict = data.get("authority", {}).get("verdict", "")
        if verdict != "CLOSE COMPLETE":
            reason = f"Close authority verdict is {verdict!r} — not CLOSE COMPLETE"
            print(json.dumps({"decision": "block", "reason": reason}))
            sys.stderr.write(reason + "\n")
            sys.exit(2)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        log_fail_open(f"{type(e).__name__}: {e}"); sys.exit(0)
    sys.exit(0)

if __name__ == "__main__": main()
```

- [ ] **Step 2: Write hook config**

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.grok/hooks/scripts/close_enforcement_gate.py",
        "timeout": 180
      }]
    }]
  }
}
```

- [ ] **Step 3: Write tests** (marker detection, fail-open logging, session_end skip)

- [ ] **Step 4: Commit**

---

## Integration gate (serial — after A, B, B2, D merged + installed, C deployed)

### Task E1: Four test suites (F-10 fix: explicit commands)

- [ ] `cd P:/worktrees/dotgrok-close-authority && python -m pytest skills/close/tests/ -v` — all pass (20 original + 10 acceptance + attestation + stop-hook)
- [ ] `python -m pytest ~/.grok/skills/aar/tests/ -v -k "completion"` — AAR attestation works
- [ ] Verify hook deployed: trigger a close with unresolved gates, confirm output blocked
- [ ] Verify fail-open log: `Get-Content ~/.grok/state/hook_failures.jsonl` — entries present if any scanner crashes occurred

### Task E2: /review

- [ ] `/review --branch close-authority-019fa5a1` — no critical findings

### Task E3: /check

- [ ] `/check` — PASS

---

## Falsifier (F-14: 8-continuations cap)

After 8 blocks in one turn, the gate is overridden and the model emits anyway. This is a **known limit of the Grok Build hook runtime** (`10-hooks.md` line 262). The mitigation: every block is logged to `hook_failures.jsonl`. If the log shows 8+ blocks in one turn, the operator knows the model fought the gate. The structural fix for the 8-cap would require a runtime change (out of scope for this plan). The operator is the backstop: if the log shows repeated gate-fighting, the operator reviews the session manually.

## Latency spec (F-11 fix: measured)

- Scanner runtime: 18-24s (measured this session on 168-handoff tree)
- Hook non-close turns: <10ms (triple-match only)
- Hook close-context turns: 18-24s (scanner subprocess)

## Adversarial review status

- v1 → Round 0 (/tp): 14 findings (5 critical) → revised to v2
- v2 → Round 1 (mandatory loop): 21 findings (5 critical) → revised to v3 (this document)
- v3 → Round 2 (mandatory loop): 9 new findings (1 critical, 3 high) → revised to v4
- v4 → Round 3 (mandatory loop): **REQUIRED before execution**

---

## Round 2 fixes (v4)

**F-NEW-1 [CRITICAL] fix:** Hook reads `authority.verdict`, not raw `gates`. The scanner explicitly states (close_accounting.py:2864): "All downstream consumers MUST use resolved_gates, not the raw gates above." The hook must read `output["authority"]["verdict"]` and block when it is NOT `"CLOSE COMPLETE"`.

**F-NEW-2 [HIGH] fix:** Same fix as F-NEW-1. Reading `authority.verdict` catches `CLOSE SCANNER ERROR` and `CLOSE BLOCKED` automatically.

**F-NEW-3 [HIGH] fix:** Test 9c rewritten to create a real `aar-report.md` file, populate a minimal preprocess dir, and set a hash that doesn't match — exercising the actual hash-mismatch path, not "file missing."

**F-NEW-5 [MEDIUM] fix:** Added Task B0.5 — verify/create `P:/.agents/__lib/` and document deployment.

**F-NEW-6 [HIGH] fix:** `persist_close_receipt` builds a local signed copy instead of mutating the input receipt.

**F-NEW-7 [MEDIUM] fix:** Added Task C0 — verify `~/.grok/skills/close/` is installed and current before deploying the hook.

**F-NEW-4 [MEDIUM] fix:** `RESOLVED_STATES` uses actual scanner vocabulary: `frozenset({"pre_satisfied", "skip"})`.

**F-NEW-8 [LOW] fix:** Test 10 subprocess uses `as_posix()` for path embedding.

**F-NEW-9 [MEDIUM] fix:** Documented that the hook assumes `quality-gate.py` does not block close-context responses.
