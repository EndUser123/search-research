"""Regression test for the 2026-07-03 collection-exclusion shadowing bug.

Root cause: root conftest.py defines its own `pytest_ignore_collect` hookimpl.
Because that hook is `firstresult=True`, pytest calls conftest-registered
implementations (this one) before its own norecursedirs/collect_ignore
handling for the same path, so this function's answer is final. A hardcoded
`ignored_dirs` set used to live here, duplicating pytest.ini's
`norecursedirs`; when "_quarantine" was dropped from that hardcoded set,
pytest.ini's own (still-correct-looking) `norecursedirs` entry silently did
nothing, because it was never actually consulted. The fix: read
`norecursedirs` from `config.getini(...)` at runtime instead of duplicating
it, so pytest.ini is the only place this can be edited.

These tests fail loudly if a hardcoded directory-name set is reintroduced.
"""
from __future__ import annotations

from pathlib import Path

import conftest as root_conftest

HOOKS_DIR = Path(root_conftest.__file__).resolve().parent


def test_norecursedirs_entries_are_all_ignored(request):
    """Every directory in pytest.ini's norecursedirs must be excluded.

    Uses the REAL runtime config (request.config), not a hand-built list, so
    this test exercises the exact code path pytest uses during collection.
    """
    norecursedirs = request.config.getini("norecursedirs")
    assert norecursedirs, "pytest.ini norecursedirs is empty — nothing to verify"

    for dirname in norecursedirs:
        fake_path = HOOKS_DIR / "tests" / dirname / "test_synthetic.py"
        assert root_conftest.pytest_ignore_collect(fake_path, request.config) is True, (
            f"'{dirname}' is listed in pytest.ini norecursedirs but "
            f"pytest_ignore_collect() did not exclude it — the two have "
            f"drifted apart again (see 2026-07-03 regression)."
        )


def test_quarantine_directory_specifically_excluded(request):
    """Regression lock for the exact bug reported 2026-07-03."""
    norecursedirs = request.config.getini("norecursedirs")
    assert "_quarantine" in norecursedirs, (
        "'_quarantine' was removed from pytest.ini norecursedirs — "
        "this is the exact regression from 2026-07-03."
    )
    fake_path = HOOKS_DIR / "tests" / "_quarantine" / "test_something.py"
    assert root_conftest.pytest_ignore_collect(fake_path, request.config) is True


def test_exclusion_is_config_driven_not_hardcoded():
    """Prove the exclusion set comes from config, not a shadow copy.

    If pytest_ignore_collect() ignores what `config.getini()` returns and
    instead hardcodes its own directory names again, this test catches it:
    a fake config claiming "_quarantine" is NOT in norecursedirs must result
    in the path being collected (not ignored).
    """

    class _FakeConfig:
        def getini(self, name: str) -> list[str]:
            assert name == "norecursedirs"
            return ["some_other_dir"]  # deliberately omits "_quarantine"

    fake_path = HOOKS_DIR / "tests" / "_quarantine" / "test_something.py"
    assert root_conftest.pytest_ignore_collect(fake_path, _FakeConfig()) is False, (
        "pytest_ignore_collect() ignored '_quarantine' even though the "
        "config it was given does not list it — the exclusion has been "
        "hardcoded again instead of reading from config."
    )
