"""Tests for the cc-lazy-closure-debt Stop hook.

The Stop hook imports cc-aca-epistemic's lazy_closure_detector. We mock the
detector at the import boundary so these tests are hermetic.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "stop"))


def _install_mock_detector(monkeypatch, deferral_match=False, phrase="defer that"):
    """Mock the lazy_closure_detector import inside the Stop hook."""
    # Pop the hook + its debt_store dependency so the new env var takes effect.
    for mod in ("cc_lazy_closure_debt_Stop", "debt_store", "__lib__"):
        sys.modules.pop(mod, None)
    fake_pkg = types.ModuleType("anti_sycophancy")
    fake_inner = types.ModuleType("anti_sycophancy.lazy_closure_detector")
    if deferral_match:
        sentinel = MagicMock()
        sentinel.pattern_type = "deferral"
        sentinel.matched = phrase
        fake_inner.detect_lazy_closure = MagicMock(return_value=sentinel)
    else:
        fake_inner.detect_lazy_closure = MagicMock(return_value=None)
    sys.modules["anti_sycophancy"] = fake_pkg
    sys.modules["anti_sycophancy.lazy_closure_detector"] = fake_inner
    return fake_inner


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("CC_LAZY_CLOSURE_DEBT_STATE_DIR", str(tmp_path))
    return tmp_path


class TestStopHook:
    def test_deferral_appends_jsonl(self, monkeypatch, state_dir):
        _install_mock_detector(monkeypatch, deferral_match=True, phrase="defer that")
        hook = importlib.import_module("cc_lazy_closure_debt_Stop")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal")
        data = {"response": "We can defer that since it is a minor cleanup."}
        result = hook.run(data)
        assert result == {"continue": True}
        path = state_dir / "cc-lazy-closure-debt" / "test_terminal.jsonl"
        assert path.exists()
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["terminal_id"] == "test_terminal"
        assert obj["phrase"] == "defer that"
        assert obj["transcript_excerpt"].startswith("We can defer that")
        assert "ts" in obj and isinstance(obj["ts"], int)

    def test_non_deferral_writes_nothing(self, monkeypatch, state_dir):
        _install_mock_detector(monkeypatch, deferral_match=False)
        hook = importlib.import_module("cc_lazy_closure_debt_Stop")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal")
        data = {"response": "The hook fires correctly. I tested it with pytest."}
        result = hook.run(data)
        assert result == {"continue": True}
        path = state_dir / "cc-lazy-closure-debt" / "test_terminal.jsonl"
        assert not path.exists()

    def test_empty_response_writes_nothing(self, monkeypatch, state_dir):
        _install_mock_detector(monkeypatch, deferral_match=True)
        hook = importlib.import_module("cc_lazy_closure_debt_Stop")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal")
        result = hook.run({})
        assert result == {"continue": True}
        path = state_dir / "cc-lazy-closure-debt" / "test_terminal.jsonl"
        assert not path.exists()

    def test_other_pattern_types_ignored(self, monkeypatch, state_dir):
        """pattern_type != 'deferral' must not be persisted to debt store."""
        sys.modules.pop("cc_lazy_closure_debt_Stop", None)
        fake_inner = types.ModuleType("anti_sycophancy.lazy_closure_detector")
        sentinel = MagicMock()
        sentinel.pattern_type = "lazy_justification"
        sentinel.matched = "is appropriate"
        fake_inner.detect_lazy_closure = MagicMock(return_value=sentinel)
        sys.modules["anti_sycophancy"] = types.ModuleType("anti_sycophancy")
        sys.modules["anti_sycophancy.lazy_closure_detector"] = fake_inner
        hook = importlib.import_module("cc_lazy_closure_debt_Stop")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_terminal")
        result = hook.run({"response": "The approach is appropriate for the use case."})
        assert result == {"continue": True}
        path = state_dir / "cc-lazy-closure-debt" / "test_terminal.jsonl"
        assert not path.exists()

    def test_terminal_id_from_data(self, monkeypatch, state_dir):
        _install_mock_detector(monkeypatch, deferral_match=True)
        hook = importlib.import_module("cc_lazy_closure_debt_Stop")
        data = {
            "response": "We can defer that.",
            "session": {"terminal_id": "from_data_terminal"},
        }
        result = hook.run(data)
        assert result == {"continue": True}
        path = state_dir / "cc-lazy-closure-debt" / "from_data_terminal.jsonl"
        assert path.exists()
