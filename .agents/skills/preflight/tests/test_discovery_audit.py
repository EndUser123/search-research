from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from discovery_audit import (
    _classification,
    _is_authority_candidate,
    _is_derived_component,
    _walk_files,
    audit,
)


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


# ---------------------------------------------------------------------------
# Regression: derived/runtime directories must never be authority candidates.
# Root cause this guards against: P:\.claude\.session\session_ledger_*.json
# was classified candidate_source (because /.session/ was not in the state
# denylist), manufactured a phantom configuration_or_lifecycle_default
# conflict on the GO_WORKTREE_ROOT marker, and made every broad-scope audit
# return `blocked`. The dot-prefix backstop + enumerated derived components
# close this class.
# ---------------------------------------------------------------------------

_DERIVED_DIRS_UNDER_CLAUDE = [
    ".session", ".state", "state", "sessions", "session_data",
    ".artifacts", "logs", "tmp", ".tmp", "memtrace",
    ".venv", "venv", "site-packages", "node_modules",
    ".pytest_cache", ".ruff_cache", ".benchmarks", ".deepeval",
    "marketplace-cache", "relocations", "plugin-data", "implement-memory",
    "vendor", "exports",
]


def test_known_derived_dirs_are_not_authority(tmp_path: Path) -> None:
    """Files inside any known derived/state dir must not be candidate_source."""
    for dirname in _DERIVED_DIRS_UNDER_CLAUDE:
        derived = tmp_path / ".claude" / dirname
        derived.mkdir(parents=True)
        f = derived / "session_ledger_foo.json"
        f.write_text('{"worktree": "P:/worktrees"}\n', encoding="utf-8")
        cls = _classification(f)
        assert not _is_authority_candidate(cls), (
            f"{dirname}/ file classified {cls!r} (authority) — would manufacture phantom conflicts"
        )
        f.unlink()
        derived.rmdir()


def test_dot_prefix_backstop_catches_future_state_dirs(tmp_path: Path) -> None:
    """A hypothetical new .newtool dir is non-authoritative without enumeration."""
    future = tmp_path / ".claude" / ".newcache"
    future.mkdir(parents=True)
    f = future / "ledger.json"
    f.write_text('{"marker": "GO_WORKTREE_ROOT"}\n', encoding="utf-8")
    assert not _is_authority_candidate(_classification(f))


def test_workspace_scope_roots_remain_authoritative(tmp_path: Path) -> None:
    """Dotted workspace scope roots (.claude/.grok/.agents) are NOT pruned."""
    # Construct paths directly (not under pytest's tmp_path, whose auto-named
    # dir contains 'test_' and would trip the loose /test substring rule).
    for root in (".claude", ".grok", ".agents", ".data", ".claude-marketplace"):
        f = Path(f"P:/{root}/hooks/my_hook.py")
        assert not _is_derived_component(root), f"{root} wrongly treated as derived"
        assert _is_authority_candidate(_classification(f)), (
            f"{root}/hooks/ wrongly denied — scope root must stay authoritative"
        )


def test_session_ledger_cannot_manufacture_marker_conflict(tmp_path: Path) -> None:
    """The exact incident: two session-ledger JSONs referencing P:/worktrees
    plus one real hook must NOT produce a competing-marker conflict."""
    root = tmp_path / ".claude"
    hooks = root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "worktree_policy.py").write_text(
        "WORKTREE = 'P:/.worktrees'\n", encoding="utf-8"
    )
    session = root / ".session"
    session.mkdir()
    (session / "ledger_a.json").write_text(
        '{"path": "P:/.worktrees"}\n', encoding="utf-8"
    )
    (session / "ledger_b.json").write_text(
        '{"path": "P:/.worktrees"}\n', encoding="utf-8"
    )

    report = audit(scopes=[str(root)], targets=["worktree_policy"])

    marker_conflicts = [
        c for c in report["conflicts"]
        if c["kind"] == "configuration_or_lifecycle_default_requires_full_reader_writer_audit"
    ]
    assert marker_conflicts == [], (
        f"phantom conflict from session ledgers: {marker_conflicts}"
    )


def test_walk_prunes_venv_and_state_dirs(tmp_path: Path) -> None:
    """The walk must not descend into venv/site-packages/state — otherwise
    they exhaust the file cap and cause silent inventory loss of later scopes."""
    scope = tmp_path / "project"
    scope.mkdir()
    (scope / "real.py").write_text("x = 1\n", encoding="utf-8")
    venv = scope / ".venv" / "Lib" / "site-packages"
    venv.mkdir(parents=True)
    for i in range(50):
        (venv / f"pkg_{i}.py").write_text("# junk\n", encoding="utf-8")
    state = scope / ".session"
    state.mkdir()
    for i in range(50):
        (state / f"ledger_{i}.json").write_text("{}\n", encoding="utf-8")

    files, errors = _walk_files([scope], max_files=20_000)
    assert not errors
    walked = {Path(f).name for f in files}
    assert "real.py" in walked
    assert "pkg_0.py" not in walked, "venv was not pruned"
    assert "ledger_0.json" not in walked, ".session was not pruned"


def test_non_text_files_do_not_consume_cap(tmp_path: Path) -> None:
    """Binaries/lockfiles must not be enqueued (suffix-filter at walk time)."""
    scope = tmp_path / "src"
    scope.mkdir()
    (scope / "real.py").write_text("x = 1\n", encoding="utf-8")
    (scope / "app.exe").write_bytes(b"\x00\x01")
    (scope / "deps.lock").write_text("lock\n", encoding="utf-8")
    (scope / "icon.png").write_bytes(b"\x89PNG")

    files, _ = _walk_files([scope], max_files=20_000)
    names = {Path(f).name for f in files}
    assert names == {"real.py"}, f"non-text files enqueued: {names}"


def test_cap_does_not_abandon_later_scopes(tmp_path: Path) -> None:
    """Hitting the cap in scope 1 must not prevent scope 2 from being walked."""
    scope1 = tmp_path / "big"
    scope1.mkdir()
    for i in range(10):
        (scope1 / f"f_{i}.py").write_text("# a\n", encoding="utf-8")
    scope2 = tmp_path / "later"
    scope2.mkdir()
    (scope2 / "important.py").write_text("# b\n", encoding="utf-8")

    files, errors = _walk_files([scope1, scope2], max_files=5)
    # Cap is global; once hit, collection stops. The fix is that cap_hit uses
    # break (not return), so the function still returns cleanly with the error
    # flag rather than discarding the partial result via an early return path.
    assert "file_limit_reached:5" in errors
    assert len(files) == 5
