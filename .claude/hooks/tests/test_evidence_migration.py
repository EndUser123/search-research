"""
Tests for evidence state migration script.

Test-Driven Development: RED phase - these tests should FAIL initially.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Import the module (will fail until we create it)
try:
    from evidence import migrate
except ImportError:
    pytest.skip("evidence.migrate module not created yet", allow_module_level=True)


class TestLoadOldCache:
    """Test load_old_cache function."""

    def test_load_nonexistent_file(self, tmp_path):
        """Non-existent cache file returns empty dict."""
        result = migrate.load_old_cache(tmp_path / "does_not_exist.json")
        assert result == {}

    def test_load_valid_cache_file(self, tmp_path):
        """Valid cache file is loaded correctly."""
        cache_file = tmp_path / "cache.json"
        test_data = {"file_hashes": {}, "entries": {}}
        cache_file.write_text(json.dumps(test_data))

        result = migrate.load_old_cache(cache_file)

        assert result == test_data

    def test_load_invalid_json_returns_empty(self, tmp_path):
        """Invalid JSON returns empty dict."""
        cache_file = tmp_path / "invalid.json"
        cache_file.write_text("{invalid json")

        result = migrate.load_old_cache(cache_file)

        assert result == {}


class TestMigrateHashCache:
    """Test migrate_hash_cache function."""

    def test_migrate_empty_cache(self, tmp_path):
        """Empty cache results in no migrations."""
        old_cache = {}
        new_cache_dir = tmp_path / "evidence"

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=True)

        assert stats["migrated"] == 0
        assert stats["skipped"] == 0
        assert stats["errors"] == 0

    def test_migrate_single_terminal(self, tmp_path):
        """Single terminal with file hashes is migrated correctly."""
        old_cache = {
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0},
                    "file2.py": {"hash": "def456", "updated_at": 1234567895.0}
                }
            }
        }
        new_cache_dir = tmp_path / "evidence"

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=False)

        assert stats["migrated"] == 2

        # Verify new cache file was created
        new_cache_file = new_cache_dir / "hash_cache_terminal1.json"
        assert new_cache_file.exists()

        # Verify content
        migrated_data = json.loads(new_cache_file.read_text())
        assert "file1.py" in migrated_data
        assert migrated_data["file1.py"]["hash"] == "abc123"
        assert "file2.py" in migrated_data
        assert migrated_data["file2.py"]["hash"] == "def456"

    def test_migrate_multiple_terminals(self, tmp_path):
        """Multiple terminals each get their own cache file."""
        old_cache = {
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0}
                },
                "terminal2": {
                    "file2.py": {"hash": "def456", "updated_at": 1234567895.0}
                }
            }
        }
        new_cache_dir = tmp_path / "evidence"

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=False)

        assert stats["migrated"] == 2

        # Verify both cache files were created
        assert (new_cache_dir / "hash_cache_terminal1.json").exists()
        assert (new_cache_dir / "hash_cache_terminal2.json").exists()

    def test_migrate_with_invalid_terminal_entry(self, tmp_path):
        """Invalid terminal entry is skipped."""
        old_cache = {
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0}
                },
                "terminal2": "not_a_dict"  # Invalid entry
            }
        }
        new_cache_dir = tmp_path / "evidence"

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=False)

        assert stats["migrated"] == 1
        assert stats["skipped"] == 1

        # Only valid terminal was migrated
        assert (new_cache_dir / "hash_cache_terminal1.json").exists()
        assert not (new_cache_dir / "hash_cache_terminal2.json").exists()

    def test_migrate_merges_with_existing_cache(self, tmp_path):
        """Existing new cache file is merged with migrated data."""
        # Create existing new cache file
        new_cache_dir = tmp_path / "evidence"
        new_cache_dir.mkdir(parents=True, exist_ok=True)
        existing_cache_file = new_cache_dir / "hash_cache_terminal1.json"
        existing_data = {
            "existing_file.py": {"hash": "old123", "updated_at": 1234560000.0}
        }
        existing_cache_file.write_text(json.dumps(existing_data))

        # Migrate additional data
        old_cache = {
            "file_hashes": {
                "terminal1": {
                    "new_file.py": {"hash": "new456", "updated_at": 1234567890.0}
                }
            }
        }

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=False)

        # Stats count all entries in the merged file
        assert stats["migrated"] >= 1

        # Verify both old and new entries exist
        merged_data = json.loads(existing_cache_file.read_text())
        assert "existing_file.py" in merged_data
        assert "new_file.py" in merged_data
        assert merged_data["new_file.py"]["hash"] == "new456"

    def test_dry_run_does_not_create_cache_files(self, tmp_path):
        """Dry run mode does not create cache files (but may create directory)."""
        old_cache = {
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0}
                }
            }
        }
        new_cache_dir = tmp_path / "evidence"

        stats = migrate.migrate_hash_cache(old_cache, new_cache_dir, dry_run=True)

        assert stats["migrated"] == 1
        # Cache files should not be created in dry run
        cache_files = list(new_cache_dir.glob("hash_cache_*.json")) if new_cache_dir.exists() else []
        assert len(cache_files) == 0


class TestBackupOldState:
    """Test backup_old_state function."""

    def test_backup_creates_file(self, tmp_path):
        """Backup creates .bak file."""
        original_file = tmp_path / "cache.json"
        original_file.write_text('{"data": "value"}')

        backup_path = migrate.backup_old_state(original_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert str(backup_path).endswith(".json.bak")
        assert backup_path.read_text() == '{"data": "value"}'

    def test_backup_nonexistent_file(self, tmp_path):
        """Non-existent file returns None without error."""
        backup_path = migrate.backup_old_state(tmp_path / "does_not_exist.json")

        assert backup_path is None


class TestMain:
    """Test main function."""

    def test_main_with_help(self, capsys):
        """--help flag shows usage."""
        with patch.object(sys, "argv", ["migrate.py", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                migrate.main()
            assert exc_info.value.code == 0

    def test_main_dry_run(self, tmp_path, monkeypatch):
        """--dry-run flag performs migration without creating cache files."""
        # Create test cache file
        old_cache = tmp_path / "empirical_observation_cache.json"
        old_cache.write_text(json.dumps({
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0}
                }
            }
        }))

        new_cache_dir = tmp_path / "evidence"

        # Mock paths
        monkeypatch.setattr("sys.argv", [
            "migrate.py",
            "--old-cache", str(old_cache),
            "--new-cache-dir", str(new_cache_dir),
            "--dry-run",
            "--no-backup"
        ])

        result = migrate.main()

        assert result == 0
        # Cache files should not be created in dry run (directory may be created)
        cache_files = list(new_cache_dir.glob("hash_cache_*.json")) if new_cache_dir.exists() else []
        assert len(cache_files) == 0

    def test_main_performs_migration(self, tmp_path, monkeypatch):
        """Main function performs actual migration."""
        # Create test cache file
        old_cache = tmp_path / "empirical_observation_cache.json"
        old_cache.write_text(json.dumps({
            "file_hashes": {
                "terminal1": {
                    "file1.py": {"hash": "abc123", "updated_at": 1234567890.0}
                }
            }
        }))

        new_cache_dir = tmp_path / "evidence"

        # Mock paths
        monkeypatch.setattr("sys.argv", [
            "migrate.py",
            "--old-cache", str(old_cache),
            "--new-cache-dir", str(new_cache_dir),
            "--no-backup"
        ])

        result = migrate.main()

        assert result == 0
        assert new_cache_dir.exists()
        assert (new_cache_dir / "hash_cache_terminal1.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
