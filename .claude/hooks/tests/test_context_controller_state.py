"""Tests for context_controller.state (controller-only I/O).

Read-only by default: every test passes state_root=tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Inject context_controller dir so `import state` resolves to the
# context_controller package, not the top-level P:/.claude/hooks/state/
# namespace package. Must run before any `import state` below.
_CONTEXT_CONTROLLER_DIR = str(Path(__file__).resolve().parent.parent / "context_controller")
if _CONTEXT_CONTROLLER_DIR not in sys.path:
    sys.path.insert(0, _CONTEXT_CONTROLLER_DIR)

# Import via the explicit `context_controller.state` path so pytest's
# module cache cannot resolve `state` to the top-level runtime state
# directory at P:/.claude/hooks/state/ (which is an implicit namespace
# package and shadows the real module).
import pytest

from context_controller import state as state_mod  # noqa: E402

# Module-level imports (resolved at runtime via the explicit import above).
ALLOWED_HEALTH_KEYS = state_mod.ALLOWED_HEALTH_KEYS
ContextHealth = state_mod.ContextHealth
DEFAULT_PROJECT_ROOT = state_mod.DEFAULT_PROJECT_ROOT
DEFAULT_STATE_ROOT = state_mod.DEFAULT_STATE_ROOT
FORBIDDEN_POLICY_KEYS = state_mod.FORBIDDEN_POLICY_KEYS
PHASE_DEFAULT = state_mod.PHASE_DEFAULT
POLICY_SCHEMA_VERSION = state_mod.POLICY_SCHEMA_VERSION
VALID_PHASES = state_mod.VALID_PHASES
_try_import_snapshot_storage = state_mod._try_import_snapshot_storage
load_policy_state = state_mod.load_policy_state
read_handoff_envelope = state_mod.read_handoff_envelope
save_policy_state = state_mod.save_policy_state
update_policy_state = state_mod.update_policy_state


class TestSchemaConstants:
    def test_valid_phases_is_seven(self) -> None:
        assert len(VALID_PHASES) == 7
        assert VALID_PHASES == frozenset(
            {"research", "planning", "implementation", "review",
             "debugging", "handoff", "general"}
        )

    def test_phase_default_is_general(self) -> None:
        assert PHASE_DEFAULT == "general"

    def test_schema_version_is_one(self) -> None:
        assert POLICY_SCHEMA_VERSION == 1

    def test_forbidden_keys_cover_envelope_fields(self) -> None:
        for k in ("goal", "next_step", "active_files", "blockers",
                  "open_questions", "recent_decisions", "resume_snapshot",
                  "decision_register", "evidence_index", "checksum"):
            assert k in FORBIDDEN_POLICY_KEYS, f"{k!r} must be forbidden"

    def test_allowed_health_keys_minimal(self) -> None:
        assert ALLOWED_HEALTH_KEYS == frozenset(
            {"turn_count", "large_outputs", "phase_turns",
             "should_compact", "should_start_fresh"}
        )

    def test_default_paths(self) -> None:
        assert str(DEFAULT_STATE_ROOT).endswith("context-controller")
        # Path() normalizes "P:/" to "P:\\" on Windows; assert the drive
        # letter and the trailing separator, not the exact string.
        assert Path(str(DEFAULT_PROJECT_ROOT)).drive == "P:"

    def test_no_envelope_keys_in_allowed(self) -> None:
        assert ALLOWED_HEALTH_KEYS.isdisjoint(FORBIDDEN_POLICY_KEYS)


class TestLoadPolicyState:
    def test_missing_file_returns_defaults(self, tmp_path):
        state = load_policy_state("t1", state_root=tmp_path)
        assert state["schema_version"] == POLICY_SCHEMA_VERSION
        assert state["phase"] == PHASE_DEFAULT
        assert state["context_health"] == {
            "turn_count": 0, "large_outputs": 0, "phase_turns": 0,
            "should_compact": False, "should_start_fresh": False,
        }
        assert state["updated_at"] == ""

    def test_corrupt_json_returns_defaults(self, tmp_path):
        d = tmp_path / "t1"
        d.mkdir(parents=True)
        (d / "policy.json").write_text("not-json", encoding="utf-8")
        state = load_policy_state("t1", state_root=tmp_path)
        assert state["phase"] == PHASE_DEFAULT

    def test_non_dict_json_returns_defaults(self, tmp_path):
        d = tmp_path / "t1"
        d.mkdir(parents=True)
        (d / "policy.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        state = load_policy_state("t1", state_root=tmp_path)
        assert state["phase"] == PHASE_DEFAULT

    def test_invalid_phase_in_file_is_overridden(self, tmp_path):
        d = tmp_path / "t1"
        d.mkdir(parents=True)
        (d / "policy.json").write_text(
            json.dumps({"phase": "not-a-phase", "context_health": {}}),
            encoding="utf-8",
        )
        state = load_policy_state("t1", state_root=tmp_path)
        assert state["phase"] == PHASE_DEFAULT

    def test_unknown_context_health_keys_dropped(self, tmp_path):
        d = tmp_path / "t1"
        d.mkdir(parents=True)
        (d / "policy.json").write_text(
            json.dumps({"phase": "research", "context_health": {
                "turn_count": 5, "surprise": 999}}),
            encoding="utf-8",
        )
        state = load_policy_state("t1", state_root=tmp_path)
        assert "surprise" not in state["context_health"]
        assert state["context_health"]["turn_count"] == 5


class TestSavePolicyState:
    def test_roundtrip_persists_phase_and_health(self, tmp_path):
        # Pass a dict for context_health (the on-disk shape). The
        # validator requires a dict; save_policy_state's internal
        # coercion is exercised separately.
        assert save_policy_state(
            "t1",
            {"phase": "research",
             "context_health": {"turn_count": 4},
             "updated_at": "2026-06-08T00:00:00Z"},
            state_root=tmp_path,
        ) is True
        loaded = load_policy_state("t1", state_root=tmp_path)
        assert loaded["phase"] == "research"
        assert loaded["context_health"]["turn_count"] == 4
        assert loaded["updated_at"] == "2026-06-08T00:00:00Z"

    def test_save_rejects_forbidden_key(self, tmp_path):
        with pytest.raises(ValueError, match="envelope-derived"):
            save_policy_state(
                "t1",
                {"phase": "research", "context_health": {}, "goal": "x"},
                state_root=tmp_path,
            )
        assert not (tmp_path / "t1" / "policy.json").exists()

    def test_save_rejects_top_level_forbidden(self, tmp_path):
        with pytest.raises(ValueError, match="envelope-derived"):
            save_policy_state(
                "t1",
                {"phase": "research", "resume_snapshot": {"goal": "x"}},
                state_root=tmp_path,
            )

    def test_save_rejects_unknown_health_key(self, tmp_path):
        with pytest.raises(ValueError, match="unknown fields"):
            save_policy_state(
                "t1",
                {"phase": "research", "context_health": {
                    "turn_count": 1, "hacked": 99}},
                state_root=tmp_path,
            )

    def test_save_rejects_invalid_phase(self, tmp_path):
        with pytest.raises(ValueError, match="invalid phase"):
            save_policy_state(
                "t1",
                {"phase": "not-a-phase", "context_health": {}},
                state_root=tmp_path,
            )

    def test_save_rejects_non_dict(self, tmp_path):
        with pytest.raises(ValueError, match="must be a dict"):
            save_policy_state("t1", ["not", "a", "dict"], state_root=tmp_path)

    def test_save_creates_terminal_subdir(self, tmp_path):
        save_policy_state(
            "fresh",
            {"phase": "general", "context_health": {}},
            state_root=tmp_path,
        )
        assert (tmp_path / "fresh" / "policy.json").exists()


class TestUpdatePolicyState:
    def test_first_update_sets_phase(self, tmp_path):
        out = update_policy_state(
            "t1", state_root=tmp_path, phase="research", touch_updated_at=False
        )
        assert out["phase"] == "research"
        assert out["context_health"]["phase_turns"] == 0
        assert out["updated_at"] == ""

    def test_phase_change_resets_phase_turns(self, tmp_path):
        save_policy_state(
            "t1",
            {"phase": "research", "context_health": {"phase_turns": 8},
             "updated_at": ""},
            state_root=tmp_path,
        )
        out = update_policy_state("t1", state_root=tmp_path, phase="implementation")
        assert out["phase"] == "implementation"
        assert out["context_health"]["phase_turns"] == 0

    def test_same_phase_keeps_phase_turns(self, tmp_path):
        save_policy_state(
            "t1",
            {"phase": "research", "context_health": {"phase_turns": 5},
             "updated_at": ""},
            state_root=tmp_path,
        )
        out = update_policy_state("t1", state_root=tmp_path, phase="research")
        assert out["context_health"]["phase_turns"] == 5

    def test_health_delta_is_elementwise_added(self, tmp_path):
        save_policy_state(
            "t1",
            {"phase": "research",
             "context_health": {"turn_count": 2, "large_outputs": 1, "phase_turns": 2},
             "updated_at": ""},
            state_root=tmp_path,
        )
        out = update_policy_state(
            "t1", state_root=tmp_path,
            health_delta=ContextHealth(turn_count=1, large_outputs=1, phase_turns=1),
        )
        h = out["context_health"]
        assert h["turn_count"] == 3
        assert h["large_outputs"] == 2
        assert h["phase_turns"] == 3

    def test_invalid_phase_raises(self, tmp_path):
        with pytest.raises(ValueError, match="invalid phase"):
            update_policy_state("t1", state_root=tmp_path, phase="bogus")

    def test_invalid_health_delta_type_raises(self, tmp_path):
        with pytest.raises(ValueError, match="ContextHealth"):
            update_policy_state(
                "t1", state_root=tmp_path,
                health_delta={"turn_count": 1},
            )

    def test_updated_at_touched_by_default(self, tmp_path):
        out = update_policy_state("t1", state_root=tmp_path, phase="research")
        assert out["updated_at"] != ""
        assert "T" in out["updated_at"]


class TestContextHealth:
    def test_default_values_are_zero(self):
        h = ContextHealth()
        assert (h.turn_count, h.large_outputs, h.phase_turns) == (0, 0, 0)
        assert (h.should_compact, h.should_start_fresh) == (False, False)

    def test_addition_is_elementwise(self):
        a = ContextHealth(turn_count=2, large_outputs=1, phase_turns=3)
        b = ContextHealth(turn_count=5, large_outputs=2, phase_turns=1)
        c = a + b
        assert (c.turn_count, c.large_outputs, c.phase_turns) == (7, 3, 4)
        assert (c.should_compact, c.should_start_fresh) == (False, False)

    def test_addition_ors_booleans(self):
        a = ContextHealth(should_compact=True)
        b = ContextHealth(should_start_fresh=True)
        c = a + b
        assert c.should_compact is True
        assert c.should_start_fresh is True

    def test_addition_with_non_dataclass_returns_notimplemented(self):
        h = ContextHealth()
        result = h.__add__(42)
        assert result is NotImplemented

    def test_frozen(self):
        h = ContextHealth(turn_count=1)
        with pytest.raises(Exception):
            h.turn_count = 99


class TestReadHandoffEnvelope:
    def test_returns_none_when_import_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("state._try_import_snapshot_storage", lambda: None)
        assert read_handoff_envelope("t1", project_root=tmp_path) is None

    def test_returns_none_for_empty_terminal_id(self, tmp_path):
        assert read_handoff_envelope("", project_root=tmp_path) is None
        assert read_handoff_envelope("   ", project_root=tmp_path) is None

    def test_returns_envelope_via_fake_storage(self, tmp_path, monkeypatch):
        canned = {"resume_snapshot": {"goal": "x"}, "checksum": "abc"}

        class FakeStorage:
            def __init__(self, project_root, terminal_id):
                self.project_root = project_root
                self.terminal_id = terminal_id

            def load_handoff(self):
                return canned

        # Patch the real module (context_controller.state), not the bare
        # name "state" — that resolves to the P:/.claude/hooks/state/
        # namespace package and the patch silently no-ops.
        monkeypatch.setattr(state_mod, "_try_import_snapshot_storage", lambda: FakeStorage)
        out = read_handoff_envelope("t1", project_root=tmp_path)
        assert out == canned

    def test_returns_none_when_storage_raises(self, tmp_path, monkeypatch):
        class ExplodingStorage:
            def __init__(self, *a, **kw):
                pass

            def load_handoff(self):
                raise RuntimeError("boom")

        monkeypatch.setattr(
            "state._try_import_snapshot_storage", lambda: ExplodingStorage
        )
        assert read_handoff_envelope("t1", project_root=tmp_path) is None

    def test_returns_none_on_invalid_terminal_id(self, tmp_path, monkeypatch):
        class FakeStorage:
            def __init__(self, *a, **kw):
                pass

            def load_handoff(self):
                return {"ok": True}

        monkeypatch.setattr("state._try_import_snapshot_storage", lambda: FakeStorage)
        monkeypatch.setattr(
            "state.resolve_terminal_key",
            lambda _id: (_ for _ in ()).throw(ValueError("bad id")),
        )
        assert read_handoff_envelope("../escape", project_root=tmp_path) is None


class TestTryImportSnapshotStorage:
    def test_returns_none_on_import_error(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "snapshot_files":
                raise ImportError("blocked by test")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert _try_import_snapshot_storage() is None
