from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import PostToolUse_claim_verifier_smoke as smoke


def _make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_irrelevant_write_skips_smoke(monkeypatch) -> None:
    called = False

    def _run(*args, **kwargs):  # noqa: ANN001
        nonlocal called
        called = True
        return _make_result()

    monkeypatch.setattr(smoke.subprocess, "run", _run)

    result = smoke.run(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/tmp/notes.txt"},
        }
    )

    assert result["skipped"] is True
    assert called is False


def test_relevant_write_runs_pytest(monkeypatch) -> None:
    captured = {}

    def _run(command, **kwargs):  # noqa: ANN001
        captured["command"] = command
        captured["kwargs"] = kwargs
        return _make_result(0, stdout="6 passed", stderr="")

    monkeypatch.setattr(smoke.subprocess, "run", _run)

    result = smoke.run(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/.claude/hooks/unified_claim_verifier.py"},
        }
    )

    assert result["passed"] is True
    assert result["smoke_checked"] is True
    assert result["reason"] == "CLAIM_VERIFIER_SMOKE_PASSED"
    assert captured["command"][2] == "pytest"
    assert "test_claim_verifier_runtime_assertions.py" in captured["command"][3]
    assert captured["kwargs"]["cwd"].endswith(r".claude\hooks")


def test_registry_change_runs_pytest(monkeypatch) -> None:
    calls = []

    def _run(command, **kwargs):  # noqa: ANN001
        calls.append((command, kwargs))
        return _make_result(0, stdout="6 passed", stderr="")

    monkeypatch.setattr(smoke.subprocess, "run", _run)

    result = smoke.run(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": "P:/.claude/hooks/posttooluse/__init__.py"},
        }
    )

    assert result["passed"] is True
    assert result["smoke_checked"] is True
    assert calls, "Expected pytest to run for registry changes"


def test_multiedit_triggers_when_any_relevant_path_is_present(monkeypatch) -> None:
    calls = []

    def _run(command, **kwargs):  # noqa: ANN001
        calls.append((command, kwargs))
        return _make_result(0, stdout="6 passed", stderr="")

    monkeypatch.setattr(smoke.subprocess, "run", _run)

    result = smoke.run(
        {
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "P:/tmp/notes.txt"},
                    {"file_path": "P:/.claude/settings.json"},
                ]
            },
        }
    )

    assert result["passed"] is True
    assert result["smoke_checked"] is True
    assert calls, "Expected pytest to run for relevant MultiEdit path"


def test_failed_smoke_blocks(monkeypatch) -> None:
    def _run(command, **kwargs):  # noqa: ANN001
        return _make_result(1, stdout="FAILED", stderr="assertion failed")

    monkeypatch.setattr(smoke.subprocess, "run", _run)

    result = smoke.run(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": "P:/.claude/hooks/stop_router.py"},
        }
    )

    assert result["decision"] == "block"
    assert result["reason"] == "CLAIM_VERIFIER_SMOKE_FAILED"
    assert result["smoke_checked"] is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
