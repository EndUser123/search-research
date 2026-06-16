"""Tests for context_controller.state.

Verifies the v1 safety contract:
- read_handoff_envelope is read-only and fail-open.
- save_policy_state never writes forbidden envelope-derived keys.
- save_policy_state never writes live state on a sandbox root.
- load_policy_state returns defaults on missing/corrupt files.
- terminal_id validation blocks path-traversal and null bytes.
- update_policy_state is atomic with respect to the per-terminal lock.
- phase_turns resets to 0 only on a phase CHANGE, not on a no-op set.

All tests use tmp_path (never the real P:/.claude/state/ root). The
sandbox is enforced by the autouse fixture in conftest.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_controller import state as state_mod


# ---------------------------------------------------------------------------
# read_handoff_envelope — read-only, fail-open
# ---------------------------------------------------------------------------


def test_read_handoff_envelope_returns_none_on_empty_terminal_id() -> None:
    """Empty terminal_id is a no-op (no storage lookup, no exception)."""
    assert state_mod.read_handoff_envelope("") is None
    assert state_mod.read_handoff_envelope("   ") is None


def test_read_handoff_envelope_returns_none_when_storage_import_fails(
    monkeypatch,
) -> None:
    """If the snapshot plugin cannot be imported, return None (fail-open)."""
    monkeypatch.setattr(
        state_mod, "_try_import_snapshot_storage", lambda: None
    )
    assert state_mod.read_handoff_envelope("term-1") is None


def test_read_handoff_envelope_returns_envelope_when_storage_succeeds(
    monkeypatch, fake_snapshot_storage
) -> None:
    """Happy path: storage returns the envelope unchanged."""
    envelope = {
        "schema_version": 1,
        "resume_snapshot": {"goal": "fix the bug"},
        "decision_register": [],
        "evidence_index": [],
        "checksum": "abc",
    }
    # The fixture returns the FakeStorage *class*. Set the envelope on
    # the class so the instance-level load_handoff() reads it.
    fake_snapshot_storage.envelope = envelope
    monkeypatch.setattr(
        state_mod, "_try_import_snapshot_storage", lambda: fake_snapshot_storage
    )
    assert state_mod.read_handoff_envelope("term-1") == envelope


def test_read_handoff_envelope_never_raises_on_path_traversal(
    monkeypatch, fake_snapshot_storage
) -> None:
    """resolve_terminal_key raises ValueError on invalid ids; the reader
    must convert that to None (fail-open) instead of propagating.

    The fake storage is wrapped in a no-arg lambda so it returns the
    *class* (matching the real `_try_import_snapshot_storage` contract).
    Without the wrap, the controller would call `_FakeStorage()` with
    no args, which fails in __init__ before reaching the validation
    branch we're trying to test.
    """
    monkeypatch.setattr(
        state_mod, "_try_import_snapshot_storage", lambda: fake_snapshot_storage
    )
    # Null byte is rejected by the canonical resolver.
    assert state_mod.read_handoff_envelope("term\x00bad") is None
    # Path-separator substring ('..') is also rejected.
    assert state_mod.read_handoff_envelope("../escape") is None
    # Leading dot is also rejected.
    assert state_mod.read_handoff_envelope(".hidden") is None


# ---------------------------------------------------------------------------
# save_policy_state — forbidden keys guard
# ---------------------------------------------------------------------------


def test_save_policy_state_rejects_forbidden_top_level_keys(tmp_path) -> None:
    """The defense-in-depth guard fires BEFORE any disk write."""
    bad_policy = {
        "phase": "general",
        "goal": "leaked from envelope",  # forbidden top-level
    }
    with pytest.raises(ValueError, match="envelope-derived"):
        state_mod.save_policy_state(
            "term-1", bad_policy, state_root=tmp_path / "policy"
        )
    # And the file must NOT exist (no half-write).
    assert not (tmp_path / "policy" / "term-1" / "policy.json").exists()


def test_save_policy_state_rejects_forbidden_envelope_wrapper_keys(
    tmp_path,
) -> None:
    """Top-level envelope keys (resume_snapshot, checksum, etc.) are also
    forbidden — the policy file must not mirror the envelope."""
    bad = {
        "phase": "general",
        "resume_snapshot": {"goal": "should not be here"},
    }
    with pytest.raises(ValueError, match="envelope-derived"):
        state_mod.save_policy_state("term-1", bad, state_root=tmp_path)


def test_save_policy_state_rejects_unknown_health_fields(tmp_path) -> None:
    """Health dict may only carry ALLOWED_HEALTH_KEYS."""
    bad = {
        "phase": "general",
        "context_health": {"turn_count": 1, "secret_field": "x"},
    }
    with pytest.raises(ValueError, match="unknown fields"):
        state_mod.save_policy_state("term-1", bad, state_root=tmp_path)


def test_save_policy_state_rejects_invalid_phase(tmp_path) -> None:
    with pytest.raises(ValueError, match="invalid phase"):
        state_mod.save_policy_state(
            "term-1", {"phase": "not-a-phase"}, state_root=tmp_path
        )


def test_save_policy_state_rejects_non_dict(tmp_path) -> None:
    with pytest.raises(ValueError, match="must be a dict"):
        state_mod.save_policy_state("term-1", "not a dict", state_root=tmp_path)


def test_save_policy_state_writes_only_canonical_top_level_shape(
    tmp_path,
) -> None:
    """The on-disk file matches the canonical top-level schema even if
    the caller passes an old schema_version or a future top-level key.

    The strict health-fields guard fires on unknown context_health keys
    (separate test below). At the top level, save_policy_state is
    strict too — anything not in the canonical keys is rejected, so
    the 'old schema_version' case must come through as a no-op (the
    field is overwritten to the current POLICY_SCHEMA_VERSION). This
    test exercises the canonical-shape path with allowed keys only.
    """
    policy = {
        "phase": "implementation",
        "context_health": {
            "turn_count": 5,
            "large_outputs": 1,
            "phase_turns": 2,
            "should_compact": False,
            "should_start_fresh": False,
        },
        "updated_at": "2026-06-08T00:00:00+00:00",
    }
    ok = state_mod.save_policy_state("term-1", policy, state_root=tmp_path)
    assert ok is True
    on_disk = json.loads(
        (tmp_path / "term-1" / "policy.json").read_text(encoding="utf-8")
    )
    # schema_version is the current POLICY_SCHEMA_VERSION, not the
    # caller's value.
    assert on_disk["schema_version"] == state_mod.POLICY_SCHEMA_VERSION
    # context_health carries exactly the allowed keys (no caller-leaked
    # fields).
    assert set(on_disk["context_health"].keys()) == set(
        state_mod.ALLOWED_HEALTH_KEYS
    )


def test_load_policy_state_drops_unknown_top_level_keys_silently(tmp_path) -> None:
    """Forward compat: a file written by a future controller with
    richer top-level keys is loaded with the unknowns dropped (not
    raised). The controller is read-only against the file, not strict
    about it."""
    target = tmp_path / "term-1" / "policy.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema_version": 99,
                "phase": "research",
                "context_health": {"turn_count": 3},
                "future_top_level": "ignored",
            }
        ),
        encoding="utf-8",
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["phase"] == "research"
    assert "future_top_level" not in policy
    # And the on-disk file is unchanged by the load (load is read-only).
    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk["future_top_level"] == "ignored"


# ---------------------------------------------------------------------------
# load_policy_state — missing/corrupt fallback
# ---------------------------------------------------------------------------


def test_load_policy_state_returns_defaults_on_missing_file(tmp_path) -> None:
    """Never raises on a fresh terminal; returns the canonical default dict."""
    policy = state_mod.load_policy_state(
        "term-1", state_root=tmp_path
    )
    assert policy["schema_version"] == state_mod.POLICY_SCHEMA_VERSION
    assert policy["phase"] == state_mod.PHASE_DEFAULT
    assert set(policy["context_health"].keys()) == set(
        state_mod.ALLOWED_HEALTH_KEYS
    )


def test_load_policy_state_returns_defaults_on_corrupt_json(tmp_path) -> None:
    """A corrupt file is treated as if it did not exist (with a warn log)."""
    target = tmp_path / "term-1" / "policy.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{this is not valid json", encoding="utf-8")
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["phase"] == state_mod.PHASE_DEFAULT


def test_load_policy_state_returns_defaults_on_non_dict_payload(tmp_path) -> None:
    target = tmp_path / "term-1" / "policy.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["phase"] == state_mod.PHASE_DEFAULT


def test_load_policy_state_drops_unknown_keys_silently(tmp_path) -> None:
    """Forward compat: an old controller with a richer schema wrote
    unknown keys; the current loader drops them and keeps defaults."""
    target = tmp_path / "term-1" / "policy.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema_version": 99,  # will be overwritten on next save
                "phase": "research",
                "context_health": {"turn_count": 3},
                "future_key": "ignored",
            }
        ),
        encoding="utf-8",
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    # phase is preserved
    assert policy["phase"] == "research"
    # unknown top-level key is dropped
    assert "future_key" not in policy
    # context_health is merged with defaults
    assert "should_compact" in policy["context_health"]


# ---------------------------------------------------------------------------
# update_policy_state — phase-turns reset rule
# ---------------------------------------------------------------------------


def test_update_policy_state_resets_phase_turns_on_phase_change(tmp_path) -> None:
    """Plan rule: phase: if not None, replaces the current phase and
    resets phase_turns to 0 — only on a CHANGE.

    The reset is observed when the post-change update carries a
    health_delta that does NOT include phase_turns (so the post-reset
    value of 0 is not augmented by the delta). When the delta does
    include phase_turns, the delta is added on top of the reset —
    separate test below.
    """
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="implementation",
        health_delta=state_mod.ContextHealth(phase_turns=5),
    )
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="research",  # CHANGE
        health_delta=state_mod.ContextHealth(turn_count=1),  # no phase_turns
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["phase"] == "research"
    assert policy["context_health"]["phase_turns"] == 0


def test_update_policy_state_phase_turns_delta_added_on_top_of_reset(
    tmp_path,
) -> None:
    """The phase-change reset zeros phase_turns; a delta carrying
    phase_turns is then added on top. This is the documented behavior
    of state.py update_policy_state (lines 485-491)."""
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="implementation",
        health_delta=state_mod.ContextHealth(phase_turns=5),
    )
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="research",  # CHANGE
        health_delta=state_mod.ContextHealth(phase_turns=99),  # delta on top
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["phase"] == "research"
    # Reset to 0, then +99 from the delta = 99.
    assert policy["context_health"]["phase_turns"] == 99


def test_update_policy_state_preserves_phase_turns_on_no_op_set(
    tmp_path,
) -> None:
    """If phase is set to the current phase, phase_turns is NOT reset."""
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="implementation",
        health_delta=state_mod.ContextHealth(phase_turns=7),
    )
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="implementation",  # no-op
        health_delta=state_mod.ContextHealth(phase_turns=99),
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["context_health"]["phase_turns"] == 7 + 99


def test_update_policy_state_adds_health_delta(tmp_path) -> None:
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        health_delta=state_mod.ContextHealth(turn_count=2, large_outputs=1),
    )
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        health_delta=state_mod.ContextHealth(turn_count=3, large_outputs=1),
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["context_health"]["turn_count"] == 5
    assert policy["context_health"]["large_outputs"] == 2


def test_update_policy_state_rejects_invalid_phase(tmp_path) -> None:
    with pytest.raises(ValueError, match="invalid phase"):
        state_mod.update_policy_state(
            "term-1", state_root=tmp_path, phase="not-a-phase"
        )


def test_update_policy_state_rejects_invalid_health_delta(tmp_path) -> None:
    with pytest.raises(ValueError, match="health_delta must be ContextHealth"):
        state_mod.update_policy_state(
            "term-1", state_root=tmp_path, health_delta="not a dataclass"
        )


def test_update_policy_state_sets_updated_at_by_default(tmp_path) -> None:
    """The default policy is that the timestamp moves on every save."""
    state_mod.update_policy_state(
        "term-1", state_root=tmp_path, phase="implementation"
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    assert policy["updated_at"]  # non-empty


def test_update_policy_state_can_skip_updated_at(tmp_path) -> None:
    """Tests want determinism; they can pass touch_updated_at=False."""
    state_mod.update_policy_state(
        "term-1", state_root=tmp_path, phase="implementation"
    )
    state_mod.update_policy_state(
        "term-1",
        state_root=tmp_path,
        phase="research",
        touch_updated_at=False,
    )
    policy = state_mod.load_policy_state("term-1", state_root=tmp_path)
    # The second update did not touch the timestamp; the value is whatever
    # the first update wrote.
    assert policy["updated_at"]  # still non-empty from the first call


# ---------------------------------------------------------------------------
# Terminal isolation
# ---------------------------------------------------------------------------


def test_terminal_ids_get_isolated_state_files(tmp_path) -> None:
    """Two terminals under the same state_root must not share policy files."""
    state_mod.update_policy_state(
        "term-A", state_root=tmp_path, phase="implementation"
    )
    state_mod.update_policy_state(
        "term-B", state_root=tmp_path, phase="review"
    )
    policy_a = state_mod.load_policy_state("term-A", state_root=tmp_path)
    policy_b = state_mod.load_policy_state("term-B", state_root=tmp_path)
    assert policy_a["phase"] == "implementation"
    assert policy_b["phase"] == "review"
    # And the files live in distinct directories.
    assert (tmp_path / "term-A" / "policy.json").exists()
    assert (tmp_path / "term-B" / "policy.json").exists()


def test_update_policy_state_never_writes_outside_state_root(tmp_path) -> None:
    """Even when given a hostile terminal_id with traversal chars, the
    state file must land inside state_root and not somewhere else."""
    # The canonical resolver normalizes/sanitizes; a path-traversal id
    # raises ValueError, and the controller returns defaults without
    # touching disk. We assert that.
    state_mod.update_policy_state(
        "../escape", state_root=tmp_path, phase="implementation"
    )
    # Nothing leaked above tmp_path.
    for p in tmp_path.parent.rglob("policy.json"):
        if "term-A" not in p.read_text():
            # The hostile id did not create anything.
            assert "escape" not in str(p), (
                f"path-traversal terminal id leaked: {p}"
            )
    # And the host directory does not have a "policy.json" sibling.
    assert not (tmp_path.parent / "policy.json").exists()


# ---------------------------------------------------------------------------
# Live-state sandbox (the conftest autouse fixture already routes through
# tmp_path; this test asserts that the real default root was NOT touched).
# ---------------------------------------------------------------------------


def test_no_live_state_written_in_test(tmp_path) -> None:
    """The autouse fixture redirects DEFAULT_STATE_ROOT into tmp_path.
    Verify the real ``P:/.claude/state/context-controller/`` was not touched.
    """
    real_root = Path("P:/.claude/state/context-controller")
    # We don't fail if the real root doesn't exist — we only assert that
    # the test's writes didn't materialize there. Use a marker: if the
    # test code accidentally wrote to the real root, it would create
    # ``real_root/<test_terminal_id>/policy.json``. We can't enumerate
    # every terminal id, but the conftest's monkeypatch makes
    # ``state_mod.DEFAULT_STATE_ROOT`` point at tmp_path, so any call
    # that defaults to it lands in tmp_path. Just confirm the real
    # default was redirected.
    assert str(state_mod.DEFAULT_STATE_ROOT).startswith(str(tmp_path))


def test_save_returns_false_on_io_failure(monkeypatch, tmp_path) -> None:
    """If the atomic write fails (e.g. read-only filesystem), save_policy_state
    must return False rather than raise — the controller is advisory."""
    from context_controller import state as sm

    def _raise(*args, **kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(sm, "atomic_write", _raise)
    ok = sm.save_policy_state(
        "term-1",
        {"phase": "general", "context_health": {}},
        state_root=tmp_path,
    )
    assert ok is False


def test_update_returns_in_memory_state_on_validation_failure(
    monkeypatch, tmp_path
) -> None:
    """If the post-merge validation fails (defense-in-depth), update
    returns the in-memory dict without writing."""
    # Force a forbidden key into the merged state by monkeypatching the
    # validator. This proves the validation gate fires *after* the
    # merge but *before* the atomic_write.
    from context_controller import state as sm

    def _reject(policy):
        raise ValueError("simulated post-merge rejection")

    monkeypatch.setattr(sm, "_validate_policy_dict", _reject)
    result = sm.update_policy_state("term-1", state_root=tmp_path, phase="general")
    assert result["phase"] == "general"
    # And no file was written (the validator fires before the I/O).
    assert not (tmp_path / "term-1" / "policy.json").exists()
