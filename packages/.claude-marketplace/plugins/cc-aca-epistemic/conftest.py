"""conftest.py — sys.path setup for cc-aca-epistemic test suite.

lazy_closure_detector imports from __lib.anti_lazy_policy, which lives in
P:/.claude/hooks/__lib/. That directory must appear in sys.path BEFORE the
plugin root so that `from __lib.anti_lazy_policy` resolves to the global
hooks __lib/, not the plugin's own __lib/ package.

pytest.ini's pythonpath entries (including '.') are injected before conftest
runs, so we use pytest_configure (earliest hook) and also evict any stale
__lib entry from sys.modules so the re-import picks up the correct package.
"""
import sys


def pytest_configure(config) -> None:  # noqa: ANN001
    """Insert global hooks dir at the front of sys.path before any imports."""
    _GLOBAL_HOOKS = "P:/.claude/hooks"
    # Remove the global hooks dir if already present (may be mid-list from pytest.ini)
    if _GLOBAL_HOOKS in sys.path:
        sys.path.remove(_GLOBAL_HOOKS)
    # Insert at position 0 so __lib from hooks wins over the plugin's own __lib/
    sys.path.insert(0, _GLOBAL_HOOKS)
    # Evict any stale __lib cached from the plugin root so the next import
    # resolves against the hooks __lib/ that contains anti_lazy_policy.
    sys.modules.pop("__lib", None)
