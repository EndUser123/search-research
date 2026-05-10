# Exclude patched modules from pytest collection
import sys
from pathlib import Path

import pytest

# Add hooks directory to sys.path for imports
# This must be at module level (not in a fixture) so it's available during test collection
_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

# Ignore deprecated and legacy test directories
# _legacy: tests for permanently removed features, source modules no longer exist.
# _legacy_stop_router: tests for Stop_router.py (deleted in 2026-05-07 consolidation)
collect_ignore = ["deprecated", "_legacy", "_legacy_stop_router"]


def pytest_collection_modifyitems(config, items):
    """Prevent collection of tests from patched modules."""
    # Remove any items that come from pre_tool_use module (which we patch)
    items[:] = [item for item in items if item.module.__name__ != "pre_tool_use"]


@pytest.fixture(autouse=True)
def isolate_notifications(tmp_path):
    """Redirect notification_queue to temp file during tests.

    Prevents test notifications from polluting the production
    ~/.claude/notifications.json file.

    Tests can still call add_notification() and verify behavior,
    but all writes go to a temp file that's cleaned up automatically.
    """
    # Import here to avoid import-time side effects
    hooks_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(hooks_dir))

    import notification_queue

    # Save original and redirect to temp
    original_file = notification_queue.NOTIFICATION_FILE
    test_file = tmp_path / "test_notifications.json"
    notification_queue.NOTIFICATION_FILE = test_file

    # Ensure clean state at test start
    test_file.unlink(missing_ok=True)
    try:
        yield
    finally:
        notification_queue.NOTIFICATION_FILE = original_file


@pytest.fixture(autouse=True)
def enable_dependency_verification_gate():
    """Enable the dependency verification gate for tests.

    The hook defaults to disabled, but tests expect it to be enabled.
    This fixture ensures the hook is active during test runs.
    """
    import os

    os.environ["DEPENDENCY_VERIFICATION_ENABLED"] = "true"

    yield

    # Clean up
    os.environ.pop("DEPENDENCY_VERIFICATION_ENABLED", None)


@pytest.fixture(autouse=True)
def clean_test_state():
    """Clean up test state before each test to prevent cross-test pollution.

    This fixture runs automatically before every test to ensure:
    1. All spool files are removed
    2. State files are reset

    This prevents tests from polluting each other when run in the same process.
    """
    # Clean evidence spool (before test)
    spool_dir = Path("P:/.claude/hooks/session_data/evidence_spool")
    if spool_dir.exists():
        # Remove ALL spool files (*.json)
        for spool_file in spool_dir.glob("*.json"):
            spool_file.unlink(missing_ok=True)

    # Clean PreToolUse state files (before test)
    state_dir = Path("P:/.claude/hooks/state")
    if state_dir.exists():
        for state_file in state_dir.glob("file_existence_decision_test-*.json"):
            state_file.unlink(missing_ok=True)
        for state_file in state_dir.glob("dependency_verification_test-*.json"):
            state_file.unlink(missing_ok=True)

    try:
        yield  # Test runs here
    finally:
        # Cleanup after test (same as before)
        if spool_dir.exists():
            for spool_file in spool_dir.glob("*.json"):
                spool_file.unlink(missing_ok=True)

        if state_dir.exists():
            for state_file in state_dir.glob("file_existence_decision_test-*.json"):
                state_file.unlink(missing_ok=True)
            for state_file in state_dir.glob("dependency_verification_test-*.json"):
                state_file.unlink(missing_ok=True)


def real_claim_from_text(text: str, index: int = 0):
    """Return a real Claim object by running the full extract_claims() pipeline.

    Use this instead of Mock(type=..., confidence=...) for any test covering
    code that CONSUMES Claim objects produced by claims.py.

    Cross-module contracts exercised:
      - claims.py uppercases .type via _raw_claim_to_claim()
      - _calculate_confidence() applies a -0.2 hedge penalty for hedged sentences

    Returns None if the verification module is unavailable.
    """
    hooks_dir = Path(__file__).resolve().parent.parent
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))
    try:
        from verification import extract_claims
    except ImportError:
        return None
    claims = extract_claims(text)
    if not claims:
        return None
    return claims[index]


@pytest.fixture
def make_real_claim():
    """Pytest fixture: factory that builds real Claim objects via the full extract_claims() pipeline.

    Use this instead of Mock(type=..., confidence=...) for any test covering
    code that CONSUMES Claim objects produced by claims.py.

    Cross-module contracts exercised:
      - claims.py uppercases .type via _raw_claim_to_claim()
      - _calculate_confidence() applies a -0.2 hedge penalty for hedged sentences

    Skips the test if the verification module is unavailable.
    """
    hooks_dir = Path(__file__).resolve().parent.parent
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))
    try:
        from verification import extract_claims
    except ImportError:
        pytest.skip("verification module unavailable — skipping integration boundary test")

    def _factory(text: str, index: int = 0):
        claims = extract_claims(text)
        assert claims, f"extract_claims produced no claims for: {text!r}"
        return claims[index]

    return _factory
