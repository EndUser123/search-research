#!/usr/bin/env python3
"""Behavior tests for the investigation gate discovery model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import PreToolUse_investigation_gate as gate


@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    """Create a workspace-like temp tree and keep git lookups deterministic."""
    monkeypatch.setattr(gate, "_resolve_repo_root", lambda path_hint=None: tmp_path)
    monkeypatch.setattr(
        gate,
        "_parse_git_status",
        lambda repo_root, target_path: {
            "available": False,
            "changed_paths": [],
            "status_map": {},
            "has_deleted_files": False,
            "has_staged_deletions": False,
            "has_conflicts": False,
            "has_renames": False,
            "dirty_same_dir": False,
        },
    )
    return tmp_path


def test_low_risk_auto_read_once(isolated_workspace):
    workspace = isolated_workspace
    target = workspace / "notes.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8")

    state = gate.fresh_state("term-low")
    risk_context = gate._build_risk_context("Write", {"path": str(target)}, state, "term-low")

    allowed, reason = gate.check_write_permission("Write", {"path": str(target)}, state, risk_context)

    assert allowed is True
    assert reason.startswith("[AUTO-READ LOW RISK]")
    assert str(target.resolve(strict=False)) in state["targets_auto_read_once"]
    assert any(Path(p).resolve(strict=False) == target.resolve(strict=False) for p in state["files_read"])


def test_medium_python_requires_explicit_discovery(isolated_workspace):
    workspace = isolated_workspace
    pkg = workspace / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    dep = pkg / "dep.py"
    dep.write_text("def helper():\n    return 1\n", encoding="utf-8")
    target = pkg / "router.py"
    target.write_text("from .dep import helper\n\nvalue = helper()\n", encoding="utf-8")

    state = gate.fresh_state("term-medium")
    state["files_read"] = [str(target)]
    risk_context = gate._build_risk_context("Edit", {"path": str(target)}, state, "term-medium")

    assert risk_context["risk_tier"] == gate.MEDIUM_RISK
    allowed, reason = gate.check_write_permission("Edit", {"path": str(target)}, state, risk_context)

    assert allowed is False
    assert "EXPLICIT_DISCOVERY_REQUIRED" in reason
    assert "Coverage: 1/2" in reason


def test_tombstone_dependency_blocks_write(isolated_workspace, monkeypatch):
    workspace = isolated_workspace
    pkg = workspace / "core"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    target = pkg / "router_async.py"
    target.write_text("from .tracing import QueryTracer\n", encoding="utf-8")

    def fake_git_status(repo_root, target_path):
        return {
            "available": True,
            "changed_paths": ["core/tracing.py"],
            "status_map": {"core/tracing.py": " D"},
            "has_deleted_files": True,
            "has_staged_deletions": False,
            "has_conflicts": False,
            "has_renames": False,
            "dirty_same_dir": True,
        }

    monkeypatch.setattr(gate, "_parse_git_status", fake_git_status)

    state = gate.fresh_state("term-high")
    state["files_read"] = [str(target)]
    risk_context = gate._build_risk_context("Edit", {"path": str(target)}, state, "term-high")

    assert risk_context["risk_tier"] == gate.HIGH_RISK
    assert "tracing" in " ".join(risk_context["dependencies"]["unresolved_local_imports"])
    assert "core/tracing.py" in risk_context["dependencies"]["deleted_or_staged_import_targets"]

    allowed, reason = gate.check_write_permission("Edit", {"path": str(target)}, state, risk_context)

    assert allowed is False
    assert "MISSING_DEPENDENCY_DISCOVERY" in reason or "IMPORT_TARGET_DELETED_OR_STAGED" in reason


def test_core_import_alias_used_as_module_resolves(isolated_workspace):
    workspace = isolated_workspace
    pkg = workspace / "core"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "tracing.py").write_text("class QueryTracer:\n    pass\n", encoding="utf-8")
    target = pkg / "router.py"
    target.write_text("from core import tracing\n\ntracing.QueryTracer()\n", encoding="utf-8")

    state = gate.fresh_state("term-alias")
    state["files_read"] = [str(target)]
    risk_context = gate._build_risk_context("Edit", {"path": str(target)}, state, "term-alias")

    assert "core.tracing" in [entry["spec"] for entry in risk_context["dependencies"]["resolved_local_imports"]]
    assert risk_context["dependencies"]["unresolved_local_imports"] == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
