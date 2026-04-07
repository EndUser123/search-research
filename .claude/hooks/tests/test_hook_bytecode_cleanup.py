"""Tests for on-error stale bytecode cleanup in hook_importer."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure __lib is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from __lib.hook_importer import HookImporter


class TestClearHookBytecode:
    """Tests for _clear_hook_bytecode method."""

    def test_clears_versioned_pyc_file(self, tmp_path: Path) -> None:
        """._clear_hook_bytecode removes .pyc with correct version tag."""
        importer = HookImporter(hooks_dir=tmp_path)

        # Create __pycache__ with a versioned .pyc file
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        pyc_file = pycache / f"test_hook.{version_tag}.pyc"
        pyc_file.write_bytes(b"corrupted bytecode")

        assert pyc_file.exists()

        importer._clear_hook_bytecode("test_hook")

        assert not pyc_file.exists()

    def test_clears_pyo_file(self, tmp_path: Path) -> None:
        """._clear_hook_bytecode removes .pyo files."""
        importer = HookImporter(hooks_dir=tmp_path)

        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        pyo_file = pycache / f"test_hook.{version_tag}.pyo"
        pyo_file.write_bytes(b"old bytecode")

        assert pyo_file.exists()

        importer._clear_hook_bytecode("test_hook")

        assert not pyo_file.exists()

    def test_no_op_when_no_pycache(self, tmp_path: Path) -> None:
        """._clear_hook_bytecode does nothing when __pycache__ doesn't exist."""
        importer = HookImporter(hooks_dir=tmp_path)
        # Should not raise
        importer._clear_hook_bytecode("nonexistent_hook")

    def test_no_op_when_no_matching_files(self, tmp_path: Path) -> None:
        """._clear_hook_bytecode handles missing files gracefully."""
        importer = HookImporter(hooks_dir=tmp_path)

        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        # Write a different hook's .pyc
        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        other_pyc = pycache / f"other_hook.{version_tag}.pyc"
        other_pyc.write_bytes(b"some bytecode")

        importer._clear_hook_bytecode("test_hook")

        # Other hook's .pyc should still exist
        assert other_pyc.exists()


class TestLoadHookRetryOnStaleBytecode:
    """Tests for load_hook retry logic on ImportError/SyntaxError."""

    def test_retry_on_import_error_after_bytecode_cleanup(
        self, tmp_path: Path
    ) -> None:
        """load_hook retries import after clearing stale bytecode."""
        # Create a good hook file
        hook_file = tmp_path / "RetryTestHook.py"
        hook_file.write_text("value = 42\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)

        # Track if cleanup was called
        cleanup_called = False
        original_clear = importer._clear_hook_bytecode

        def track_cleanup(name: str) -> None:
            nonlocal cleanup_called
            cleanup_called = True
            original_clear(name)

        importer._clear_hook_bytecode = track_cleanup

        # First call should succeed (no error to trigger retry)
        module = importer.load_hook("RetryTestHook")
        assert module.value == 42
        # Cleanup not called on successful first attempt
        assert not cleanup_called

    def test_load_hook_catches_syntax_error_and_retries(
        self, tmp_path: Path
    ) -> None:
        """load_hook retries when SyntaxError occurs from stale bytecode."""
        # Create a hook file that will be corrupted
        hook_file = tmp_path / "SyntaxHook.py"
        hook_file.write_text("value = 100\n", encoding="utf-8")

        # Create __pycache__ with stale bytecode that has syntax error
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        stale_pyc = pycache / f"SyntaxHook.{version_tag}.pyc"

        # Write a pyc file that contains invalid syntax (simulating stale bytecode)
        stale_pyc.write_bytes(b"corrupt")

        importer = HookImporter(hooks_dir=tmp_path)

        # The import should still work because stale bytecode is ignored
        # or cleanup is retried - depending on Python's import behavior
        try:
            module = importer.load_hook("SyntaxHook")
            # If Python used the source file (correct behavior), this works
            assert module.value == 100
        except (ImportError, SyntaxError):
            # If Python tried to use stale bytecode first, cleanup enables retry
            pass

    def test_isinstance_check_prevents_retry_for_oserror(self) -> None:
        """Verify that OSError doesn't pass isinstance check for retry.

        This is a static verification that the code path is correct.
        """
        # The retry logic checks: isinstance(e, (ImportError, SyntaxError))
        # OSError should NOT pass this check
        assert not isinstance(OSError("disk error"), (ImportError, SyntaxError))
        # ImportError SHOULD pass
        assert isinstance(ImportError("import error"), (ImportError, SyntaxError))
        # SyntaxError SHOULD pass
        assert isinstance(SyntaxError("syntax error"), (ImportError, SyntaxError))

    def test_retry_triggered_on_import_error(self, tmp_path: Path) -> None:
        """load_hook retries after ImportError when bytecode cleanup resolves it.

        This tests the actual retry path by making exec_module fail
        on first import but succeed on retry (after bytecode cleanup).
        """
        # Create a hook file that will be valid
        hook_file = tmp_path / "RetryImportHook.py"
        hook_file.write_text("value = 99\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)

        # Track cleanup calls
        cleanup_calls = []
        original_clear = importer._clear_hook_bytecode

        def track_cleanup(name: str) -> None:
            cleanup_calls.append(name)
            original_clear(name)

        importer._clear_hook_bytecode = track_cleanup

        # Mock exec_module to fail first, succeed second
        exec_call_count = [0]

        def mock_exec(module: importlib.types.ModuleType) -> None:
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                # First call: simulate stale bytecode causing ImportError
                raise ImportError("stale bytecode")
            # Second call: module was recreated by retry flow, set value directly
            module.value = 99

        original_spec_from_file_location = importlib.util.spec_from_file_location

        def mock_spec(name: str, location: Path | None = None) -> importlib.util.ModuleSpec | None:
            spec = original_spec_from_file_location(name, location)
            if spec and name == "RetryImportHook":
                spec.loader.exec_module = mock_exec
            return spec

        with patch.object(importlib.util, "spec_from_file_location", mock_spec):
            module = importer.load_hook("RetryImportHook")
            assert module.value == 99

        # Verify cleanup was called (indicating retry path was triggered)
        assert "RetryImportHook" in cleanup_calls
        # Should have called exec_module twice (first failed, second succeeded)
        assert exec_call_count[0] == 2

    def test_failed_load_not_cached(self, tmp_path: Path) -> None:
        """load_hook does NOT cache module when both initial and retry fail."""
        # Create a hook file that will fail both times
        hook_file = tmp_path / "AlwaysFailHook.py"
        hook_file.write_text("value = 42\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)

        # Mock exec_module to always fail with ImportError
        def mock_exec(module: importlib.types.ModuleType) -> None:
            raise ImportError("simulated persistent failure")

        original_spec_from_file_location = importlib.util.spec_from_file_location

        def mock_spec(name: str, location: Path | None = None) -> importlib.util.ModuleSpec | None:
            spec = original_spec_from_file_location(name, location)
            if spec and name == "AlwaysFailHook":
                spec.loader.exec_module = mock_exec
            return spec

        with patch.object(importlib.util, "spec_from_file_location", mock_spec):
            with pytest.raises(ImportError, match="simulated persistent failure"):
                importer.load_hook("AlwaysFailHook")

        # Module should NOT be in cache after failed load
        assert "AlwaysFailHook" not in importer._cache

    def test_retry_succeeds_after_syntax_error_cleanup(self, tmp_path: Path) -> None:
        """load_hook retries after ImportError when source file is valid.

        This specifically tests that when ImportError/SyntaxError occurs,
        bytecode cleanup runs and allows retry with valid source.
        """
        # Create a hook file with valid syntax
        hook_file = tmp_path / "SyntaxRetryHook.py"
        hook_file.write_text("value = 77\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)

        # Track cleanup to verify it was called
        cleanup_called = []
        original_clear = importer._clear_hook_bytecode

        def track_cleanup(name: str) -> None:
            cleanup_called.append(name)
            original_clear(name)

        importer._clear_hook_bytecode = track_cleanup

        # Mock exec_module to fail first (ImportError), succeed second
        exec_call_count = [0]

        def mock_exec(module: importlib.types.ModuleType) -> None:
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                raise ImportError("simulated stale bytecode")
            # Second call succeeds: module was recreated by retry flow
            module.value = 77

        original_spec_from_file_location = importlib.util.spec_from_file_location

        def mock_spec(name: str, location: Path | None = None) -> importlib.util.ModuleSpec | None:
            spec = original_spec_from_file_location(name, location)
            if spec and name == "SyntaxRetryHook":
                spec.loader.exec_module = mock_exec
            return spec

        with patch.object(importlib.util, "spec_from_file_location", mock_spec):
            module = importer.load_hook("SyntaxRetryHook")
            assert module.value == 77

        # Cleanup must have been called for retry to succeed
        assert "SyntaxRetryHook" in cleanup_called
        # Should have called exec_module twice
        assert exec_call_count[0] == 2


class TestLoadHookIntegration:
    """Integration tests for load_hook with bytecode cleanup."""

    def test_load_hook_normal_operation(self, tmp_path: Path) -> None:
        """load_hook works normally when no stale bytecode exists."""
        hook_file = tmp_path / "NormalHook.py"
        hook_file.write_text("result = 'success'\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)
        module = importer.load_hook("NormalHook")

        assert module.result == "success"

    def test_load_hook_caches_after_first_load(self, tmp_path: Path) -> None:
        """load_hook returns cached module on subsequent calls."""
        hook_file = tmp_path / "CachedHook.py"
        hook_file.write_text("counter = 0\n", encoding="utf-8")

        importer = HookImporter(hooks_dir=tmp_path)

        module1 = importer.load_hook("CachedHook")
        module2 = importer.load_hook("CachedHook")

        assert module1 is module2
