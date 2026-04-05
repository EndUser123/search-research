#!/usr/bin/env python3
"""
Unit tests for tdd95_core.py

Tests:
- Path canonicalization (Windows-safe)
- State enum operations
- File <-> test mapping (Python + TypeScript)
- Critical hook detection
- Configuration loading
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from tdd95_core import (
    TDD95State,
    canonicalize_path,
    get_critical_hook_tests,
    get_test_candidates,
    is_exempt,
    is_impl_file,
    is_test_file,
    load_config,
    load_critical_hooks_manifest,
    path_from_posix,
    path_matches_tier,
    path_to_posix,
)


def test_path_canonicalization() -> None:
    """Test path canonicalization on Windows."""
    # Test backslash handling
    p = canonicalize_path("P:/project/src/module.py")
    assert str(p).endswith("module.py")

    # Test POSIX conversion for storage
    posix = path_to_posix(p)
    assert "/" in posix  # Should have forward slashes
    assert "\\" not in posix  # No backslashes

    # Test reconstruction
    p2 = path_from_posix(posix)
    assert p2 == p


def test_state_enum() -> None:
    """Test TDD95State enum."""
    # Test string parsing
    assert TDD95State.from_string("none") == TDD95State.NONE
    assert TDD95State.from_string("test_exists") == TDD95State.TEST_EXISTS
    assert TDD95State.from_string("failing") == TDD95State.FAILING
    assert TDD95State.from_string("passing") == TDD95State.PASSING
    assert TDD95State.from_string("complete") == TDD95State.COMPLETE

    # Test legacy value conversion
    assert TDD95State.from_string("idle") == TDD95State.NONE
    assert TDD95State.from_string("green_confirmed") == TDD95State.PASSING

    # Test invalid values
    assert TDD95State.from_string("bogus") == TDD95State.NONE

    # Test state methods
    assert TDD95State.FAILING.can_edit_impl() == True
    assert TDD95State.PASSING.can_edit_impl() == True
    assert TDD95State.NONE.can_edit_impl() == False


def test_file_detection() -> None:
    """Test file type detection."""
    config = load_config()

    # Test implementation file
    impl_path = canonicalize_path("src/module.py")
    assert is_impl_file(impl_path, config)
    assert not is_test_file(impl_path, config)

    # Test test file
    test_path = canonicalize_path("tests/test_module.py")
    assert is_test_file(test_path, config)
    assert not is_impl_file(test_path, config)

    # Test exempt file
    doc_path = canonicalize_path("README.md")
    assert is_exempt(doc_path, config)


def test_python_test_mapping() -> None:
    """Test Python file to test mapping."""
    # Create a temporary project structure with .git to establish project root
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        # Create .git to establish project root
        (project_dir / ".git").mkdir()

        # Create the implementation file
        impl_path = src_dir / "calculator.py"
        impl_path.write_text("# calculator module\n")

        # Test with full path
        candidates = get_test_candidates(impl_path)
        candidate_strs = [str(c) for c in candidates]

        # Should find tests/test_calculator.py
        # Note: paths will be temp paths, so check for the pattern
        found = any("test_calculator.py" in s for s in candidate_strs)
        assert found, f"Expected to find test_calculator.py in {candidate_strs}"


def test_typescript_test_mapping() -> None:
    """Test TypeScript file to test mapping."""
    # Create a temporary project structure with .git and package.json
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        src_dir = project_dir / "src"
        src_dir.mkdir()
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        # Create .git and package.json to establish project root
        (project_dir / ".git").mkdir()
        (project_dir / "package.json").write_text("{}")

        # Create the implementation file
        impl_path = src_dir / "component.ts"
        impl_path.write_text("// component\n")

        # Test with full path
        candidates = get_test_candidates(impl_path)
        candidate_strs = [str(c) for c in candidates]

        # Should find tests/component.test.ts
        # Note: paths will be temp paths, so check for the pattern
        found = any("component.test.ts" in s for s in candidate_strs)
        assert found, f"Expected to find component.test.ts in {candidate_strs}"


def test_tier_matching() -> None:
    """Test tier pattern matching."""
    config = load_config()

    # Test TIER0 patterns
    py_path = canonicalize_path("src/module.py")
    assert path_matches_tier(py_path, "**/*.py")

    # Test TIER1 directory patterns
    src_path = canonicalize_path("src/subdir/file.py")
    assert path_matches_tier(src_path, "src/**")


def test_critical_hooks() -> None:
    """Test critical hooks manifest loading."""
    manifest = load_critical_hooks_manifest()

    # Test that manifest is a dict
    assert isinstance(manifest, dict)

    # Test getting critical hook tests
    hook_tests = get_critical_hook_tests("assumption_audit_v2")
    if hook_tests:
        assert hasattr(hook_tests, "required_tests")


def test_config_loading() -> None:
    """Test configuration loading."""
    config = load_config()

    # Test top-level keys
    assert "enabled" in config
    assert "autoscaffold" in config
    assert "gate" in config
    assert "tiers" in config

    # Test autoscaffold config
    assert config["autoscaffold"]["enabled"] in (True, False)
    assert config["autoscaffold"]["template"] in ("minimal", "full")

    # Test gate config
    assert config["gate"]["check_test_exists"] in (True, False)
    assert isinstance(config["gate"]["check_test_recency_minutes"], int)


def test_bypass_flag() -> None:
    """Test TDD_BYPASS environment variable."""
    # Set bypass flag
    old_value = os.environ.get("TDD_BYPASS", "")
    os.environ["TDD_BYPASS"] = "1"

    try:
        from tdd95_core import get_bypass_flag
        assert get_bypass_flag() == True
    finally:
        # Restore
        if old_value:
            os.environ["TDD_BYPASS"] = old_value
        else:
            os.environ.pop("TDD_BYPASS", None)


def test_in_maintenance_mode() -> None:
    """Test maintenance mode detection via env var."""
    # Clean env first
    old_value = os.environ.get("TDD95_MAINTENANCE", "")
    try:
        os.environ.pop("TDD95_MAINTENANCE", None)

        from tdd95_core import in_maintenance_mode
        assert in_maintenance_mode() == False

        # Set and test
        os.environ["TDD95_MAINTENANCE"] = "1"
        assert in_maintenance_mode() == True
    finally:
        # Restore
        if old_value:
            os.environ["TDD95_MAINTENANCE"] = old_value
        else:
            os.environ.pop("TDD95_MAINTENANCE", None)


def test_is_in_maintenance_scope() -> None:
    """Test maintenance scope path checking."""
    import os

    from tdd95_core import (
        canonicalize_path,
        is_in_maintenance_scope,
        maintenance_scope_paths,
    )

    # Set maintenance mode for testing
    old_value = os.environ.get("TDD95_MAINTENANCE", "")
    try:
        os.environ["TDD95_MAINTENANCE"] = "1"

        # Test core files are in scope
        for raw_path in maintenance_scope_paths():
            p = canonicalize_path(raw_path)
            assert is_in_maintenance_scope(p) == True, f"{raw_path} should be in maintenance scope"

        # Test non-scope file is not in scope
        assert is_in_maintenance_scope(canonicalize_path("README.md")) == False
    finally:
        # Restore
        if old_value:
            os.environ["TDD95_MAINTENANCE"] = old_value
        else:
            os.environ.pop("TDD95_MAINTENANCE", None)


def test_record_maintenance_edit() -> None:
    """Test maintenance edit tracking in TDD95StateManager."""
    import tempfile

    # Create temp state directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Import after temporary directory context to avoid STATE_DIR override
        from tdd95_core import TDD95StateManager

        # Create a minimal state manager using the temp directory
        # We create a custom manager with state_dir set to tmpdir
        class TestStateManager(TDD95StateManager):
            def __init__(self):
                # Override just the state_dir, keeping terminal_id detection
                self.terminal_id = "test_terminal"
                # Use tmpdir as state directory
                self.state_dir = Path(tmpdir) / "tdd95" / self.terminal_id
                self.state_dir.mkdir(parents=True, exist_ok=True)

        state_mgr = TestStateManager()

        # Record a maintenance edit
        # tmpdir is a string on Windows, convert to Path
        tmpdir_path = Path(tmpdir)
        hooks_dir = tmpdir_path / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        test_impl = hooks_dir / "tdd95_core.py"
        test_impl.write_text("# test\n")

        state_mgr.record_maintenance_edit(test_impl)

        # Verify it was recorded
        edits = state_mgr.list_maintenance_edits()
        impl_key = str(test_impl).replace("\\", "/").replace("P:/", "")

        assert impl_key in edits, f"Edit to {impl_key} should be tracked"

        # Verify needs_test flag
        assert edits[impl_key]["needs_test"] is True


def main():
    """Run all tests."""
    import pytest

    # Run pytest on this file
    exit_code = pytest.main([__file__, "-v"])

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
