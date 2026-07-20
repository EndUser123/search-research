from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from discovery_audit import audit


def test_finds_existing_entrypoints_defaults_and_active_plan(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "go_safe.py").write_text("def main(): pass\n", encoding="utf-8")
    (source / "orchestrate.py").write_text("GO_WORKTREE_ROOT = 'P:/worktrees'\n", encoding="utf-8")
    (source / "worktree_safety.py").write_text("GO_MANAGED_WORKTREE_ROOT = 'P:/worktrees'\n", encoding="utf-8")
    (source / "active-plan.json").write_text('{"task": "replace go_safe.py"}\n', encoding="utf-8")

    report = audit(
        scopes=[str(source)],
        targets=["go_safe", "orchestrate", "worktree", "active-plan", "GO_WORKTREE_ROOT"],
    )

    paths = {item["path"] for item in report["matching_files"]}
    assert any(path.endswith("go_safe.py") for path in paths)
    assert report["active_plans"]
    assert report["conflicts"]
    assert report["decision"] == "needs_review"


def test_clean_scope_can_proceed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "single.py").write_text("value = 1\n", encoding="utf-8")

    report = audit(scopes=[str(source)], targets=["missing-entrypoint"])

    assert report["matching_files"] == []
    assert report["conflicts"] == []
    assert report["decision"] == "proceed_with_discovery"


def test_documentation_and_tests_are_references_not_runtime_owners(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text(
        "Use go_safe.py and GO_WORKTREE_ROOT in the discovery example.\n",
        encoding="utf-8",
    )
    tests = source / "tests"
    tests.mkdir()
    (tests / "test_go_safe.py").write_text(
        "assert 'go_safe.py' in 'go_safe.py'\n",
        encoding="utf-8",
    )

    report = audit(
        scopes=[str(source)],
        targets=["go_safe", "GO_WORKTREE_ROOT"],
    )

    assert report["matching_files"]
    assert report["default_hits"]
    assert report["conflicts"] == []
    assert report["decision"] == "proceed_with_discovery"
