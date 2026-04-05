"""
Tests for automatic artifact completion detection in /doc command.

RED phase: These tests define the desired behavior.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
import sys
import tempfile
import shutil
import time

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "commands"))
sys.path.insert(0, str(Path("P:/__csf/src")))


def setup_test_pending_item(test_dir: Path, item_id: str = "TSK-999"):
    """Create a test database with a pending item."""
    import artifact_core
    import artifact_init

    # Use test-specific database
    test_db = test_dir / "test_artifacts.db"

    # Patch DB_PATH in both modules before ensuring schema
    original_ac_path = artifact_core.DB_PATH
    original_ai_path = artifact_init.DB_PATH
    artifact_core.DB_PATH = test_db
    artifact_init.DB_PATH = test_db

    try:
        # Ensure schema
        artifact_init.ensure_schema()

        # Create artifact file
        changelog = test_dir / "CHANGELOG.md"
        changelog.write_text("# Changelog\n")

        # Add pending item
        success, msg = artifact_core.add_pending_item(
            project_root=test_dir,
            item_id=item_id,
            summary="Test task",
            change_type="feature",
            files_changed=["src/test.py"],
            source="test"
        )

        if not success:
            raise Exception(f"Failed to add pending item: {msg}")
    finally:
        # Restore paths
        artifact_core.DB_PATH = original_ac_path
        artifact_init.DB_PATH = original_ai_path

    return test_db, changelog


def test_auto_mark_detects_modified_artifact():
    """
    GIVEN: A pending item TSK-999 with changelog artifact pending
    AND: The CHANGELOG.md file was modified after item creation
    WHEN: _check_and_auto_mark_done() is called
    THEN: The artifact is auto-marked as done
    AND: A success message is returned
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        import artifact_core
        import artifact_init

        test_db = test_dir / "test_artifacts.db"

        # Patch DB_PATH in both modules
        original_ac_path = artifact_core.DB_PATH
        original_ai_path = artifact_init.DB_PATH
        artifact_core.DB_PATH = test_db
        artifact_init.DB_PATH = test_db

        try:
            # Ensure schema
            artifact_init.ensure_schema()

            # Create artifact file
            changelog = test_dir / "CHANGELOG.md"
            changelog.write_text("# Changelog\n")

            # Add pending item
            success, msg = artifact_core.add_pending_item(
                project_root=test_dir,
                item_id="TSK-999",
                summary="Test task",
                change_type="feature",
                files_changed=["src/test.py"],
                source="test"
            )
            assert success, f"Failed to add pending item: {msg}"

            # Get creation time
            pending = artifact_core.get_pending_items(test_dir)
            assert len(pending) == 1, "Should have 1 pending item"
            created_at_str = pending[0]['created_at']

            # Must be timezone-aware to match verify_artifact_modified API contract
            # SQLite stores naive datetime, so we add UTC timezone
            # Reference: doc_command.py:1240
            created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)

            # Wait and modify the file (simulate user edit)
            time.sleep(0.01)
            changelog.write_text("# Changelog\n\n## v1.0.0\n- Test feature\n")

            # Verify file was modified
            assert artifact_core.verify_artifact_modified(changelog, created_at), "File should be modified"
        finally:
            # Restore paths
            artifact_core.DB_PATH = original_ac_path
            artifact_init.DB_PATH = original_ai_path

        # Run auto-mark check
        from commands.nip.doc_command import UnifiedDocCLI
        import asyncio
        from unittest.mock import patch

        async def run_test():
            cli = UnifiedDocCLI()
            import artifact_core as ac_module
            original_db_path = ac_module.DB_PATH
            ac_module.DB_PATH = test_db

            try:
                # Patch find_project_root to return test_dir instead of cwd
                with patch('artifact_core.find_project_root', return_value=test_dir):
                    auto_marked = await cli._check_and_auto_mark_done()
                    return auto_marked
            finally:
                ac_module.DB_PATH = original_db_path

        result = asyncio.run(run_test())
        assert len(result) == 1, f"Should have 1 auto-marked item, got {len(result)}"
        assert "Auto-marked TSK-999/changelog" in result[0], f"Wrong message: {result[0]}"


def test_auto_mark_skips_unmodified_artifact():
    """
    GIVEN: A pending item with changelog artifact pending
    AND: The CHANGELOG.md file was NOT modified after item creation
    WHEN: _check_and_auto_mark_done() is called
    THEN: The artifact is NOT marked as done
    AND: No message is returned for this artifact
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        import artifact_core
        import artifact_init

        test_db = test_dir / "test_artifacts.db"

        # Patch DB_PATH in both modules
        original_ac_path = artifact_core.DB_PATH
        original_ai_path = artifact_init.DB_PATH
        artifact_core.DB_PATH = test_db
        artifact_init.DB_PATH = test_db

        try:
            # Ensure schema
            artifact_init.ensure_schema()

            # Create artifact file
            changelog = test_dir / "CHANGELOG.md"
            changelog.write_text("# Changelog\n")

            # Add pending item
            success, msg = artifact_core.add_pending_item(
                project_root=test_dir,
                item_id="TSK-998",
                summary="Test task 2",
                change_type="feature",
                files_changed=["src/test.py"],
                source="test"
            )
            assert success, f"Failed to add pending item: {msg}"

            # File is NOT modified after creation
        finally:
            # Restore paths
            artifact_core.DB_PATH = original_ac_path
            artifact_init.DB_PATH = original_ai_path

        # Run auto-mark check
        from commands.nip.doc_command import UnifiedDocCLI
        import asyncio

        async def run_test():
            cli = UnifiedDocCLI()
            import artifact_core as ac_module
            original_db_path = ac_module.DB_PATH
            ac_module.DB_PATH = test_db

            try:
                auto_marked = await cli._check_and_auto_mark_done()
                return auto_marked
            finally:
                ac_module.DB_PATH = original_db_path

        result = asyncio.run(run_test())
        assert len(result) == 0, f"Should have 0 auto-marked items, got {len(result)}"


def test_auto_mark_handles_missing_artifact_file():
    """
    GIVEN: A pending item with readme artifact pending
    AND: The README.md file does not exist
    WHEN: _check_and_auto_mark_done() is called
    THEN: The artifact is NOT marked as done
    AND: No error is raised
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        import artifact_core
        import artifact_init

        test_db = test_dir / "test_artifacts.db"

        # Patch DB_PATH in both modules
        original_ac_path = artifact_core.DB_PATH
        original_ai_path = artifact_init.DB_PATH
        artifact_core.DB_PATH = test_db
        artifact_init.DB_PATH = test_db

        try:
            artifact_init.ensure_schema()

            # Add pending item WITHOUT creating README.md
            success, msg = artifact_core.add_pending_item(
                project_root=test_dir,
                item_id="TSK-997",
                summary="Test task 3",
                change_type="feature",
                files_changed=["src/test.py"],
                source="test"
            )
            assert success, f"Failed to add pending item: {msg}"
        finally:
            artifact_core.DB_PATH = original_ac_path
            artifact_init.DB_PATH = original_ai_path

        # Run auto-mark check
        from commands.nip.doc_command import UnifiedDocCLI
        import asyncio

        async def run_test():
            cli = UnifiedDocCLI()
            import artifact_core as ac_module
            original_db_path = ac_module.DB_PATH
            ac_module.DB_PATH = test_db

            try:
                auto_marked = await cli._check_and_auto_mark_done()
                return auto_marked
            finally:
                ac_module.DB_PATH = original_db_path

        result = asyncio.run(run_test())
        assert len(result) == 0, f"Should have 0 auto-marked items, got {len(result)}"


def test_auto_mark_returns_correct_message_format():
    """
    GIVEN: An artifact was auto-marked
    WHEN: _check_and_auto_mark_done() is called
    THEN: Returns message in format "✓ Auto-marked {item_id}/{artifact_type}"
    """
    # This tests the output format specifically
    # Implementation in GREEN phase
    pass


if __name__ == "__main__":
    # Run tests to confirm they fail (RED phase)
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])


# Auto-generated docstring templates

"""Brief description of run_test.

"""
"""Brief description of run_test.

"""

# Auto-generated docstring templates

"""Brief description of run_test.

"""
"""Brief description of run_test.

"""