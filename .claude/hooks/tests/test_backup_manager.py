"""
Test suite for BackupManager class - RED phase tests.

These tests are written BEFORE the BackupManager class exists.
All tests should fail with ImportError initially.
"""

from backup_manager import BackupManager


class TestBackupManager:
    """Test suite for BackupManager backup rotation and restoration."""

    def test_rotate_backups_creates_generations(self, tmp_path):
        """
        Test that rotate_backups creates incremental backup generations.

        Given: Primary file exists, count=3
        When: rotate_backups() called
        Then: .json.1 has old primary, .json.2 has old .json.1, .json.3 has old .json.2
        """
        # Setup: Create primary file with known content
        primary = tmp_path / "evidence.db"
        primary.write_text("original content")

        backup_1 = tmp_path / "evidence.db.1"
        backup_2 = tmp_path / "evidence.db.2"
        backup_3 = tmp_path / "evidence.db.3"

        # Create initial backup generations
        backup_1.write_text("gen1 content")
        backup_2.write_text("gen2 content")
        backup_3.write_text("gen3 content")

        # Execute rotation
        manager = BackupManager(primary, count=3)
        manager.rotate_backups()

        # Verify rotation sequence:
        # - Old .json.3 should be removed (count=3)
        # - Old .json.2 → new .json.3
        # - Old .json.1 → new .json.2
        # - Old primary → new .json.1
        assert not backup_3.exists() or backup_3.read_text() == "gen2 content"
        assert backup_2.read_text() == "gen1 content"
        assert backup_1.read_text() == "original content"

    def test_rotate_backups_removes_oldest(self, tmp_path):
        """
        Test that rotate_backups removes oldest backup beyond count.

        Given: .json.3 exists, count=3
        When: rotate_backups() called
        Then: .json.3 is removed before rotation
        """
        primary = tmp_path / "evidence.db"
        primary.write_text("new content")

        backup_1 = tmp_path / "evidence.db.1"
        backup_2 = tmp_path / "evidence.db.2"
        backup_3 = tmp_path / "evidence.db.3"

        # Create all 3 generations
        backup_1.write_text("gen1")
        backup_2.write_text("gen2")
        backup_3.write_text("gen3")

        # Track .json.3 before rotation
        gen3_existed_before = backup_3.exists()

        manager = BackupManager(primary, count=3)
        manager.rotate_backups()

        # After rotation, old .json.3 should be gone or replaced
        # (removed before rotation, then recreated from old .json.2)
        assert gen3_existed_before
        assert backup_3.exists()
        assert backup_3.read_text() == "gen2"  # Old .json.2 became new .json.3

    def test_find_latest_backup_finds_most_recent(self, tmp_path):
        """
        Test that find_latest_backup identifies the newest backup.

        Given: .json.1 (old), .json.2 (newer), .json.3 (newest)
        When: find_latest_backup() called with count=3
        Then: Returns path to .json.3
        """
        primary = tmp_path / "evidence.db"
        primary.write_text("primary")

        backup_1 = tmp_path / "evidence.db.1"
        backup_2 = tmp_path / "evidence.db.2"
        backup_3 = tmp_path / "evidence.db.3"

        # Create backup generations with different timestamps
        backup_1.write_text("oldest")
        backup_2.write_text("middle")
        backup_3.write_text("newest")

        manager = BackupManager(primary, count=3)
        latest = manager.find_latest_backup()

        assert latest == backup_3
        assert latest.read_text() == "newest"

    def test_find_latest_backup_returns_none_if_missing(self, tmp_path):
        """
        Test that find_latest_backup returns None when no backups exist.

        Given: No backup files exist
        When: find_latest_backup() called
        Then: Returns None
        """
        primary = tmp_path / "evidence.db"
        primary.write_text("primary content")

        manager = BackupManager(primary, count=3)
        latest = manager.find_latest_backup()

        assert latest is None

    def test_restore_from_backup_copies_file(self, tmp_path):
        """
        Test that restore_from_backup copies backup to primary.

        Given: backup.json exists, primary corrupted
        When: restore_from_backup() called
        Then: primary file contains backup content
        """
        primary = tmp_path / "evidence.db"
        backup = tmp_path / "evidence.db.1"

        # Simulate corrupted primary
        primary.write_text("corrupted data")
        backup.write_text("good backup data")

        manager = BackupManager(primary, count=3)
        manager.restore_from_backup(backup)

        assert primary.read_text() == "good backup data"
        assert backup.exists()  # Backup should still exist
        assert backup.read_text() == "good backup data"  # Backup unchanged

    def test_restore_from_specific_backup_generation(self, tmp_path):
        """
        Test restoring from a specific backup generation.

        Given: Multiple backup generations exist
        When: restore_from_backup() called with specific generation
        Then: Primary contains that generation's content
        """
        primary = tmp_path / "evidence.db"
        backup_1 = tmp_path / "evidence.db.1"
        backup_2 = tmp_path / "evidence.db.2"

        primary.write_text("corrupted")
        backup_1.write_text("backup generation 1")
        backup_2.write_text("backup generation 2")

        manager = BackupManager(primary, count=3)
        manager.restore_from_backup(backup_2)

        assert primary.read_text() == "backup generation 2"

    def test_rotate_backups_creates_first_generation(self, tmp_path):
        """
        Test that rotate_backups creates first generation when none exist.

        Given: Primary exists, no backups exist, count=3
        When: rotate_backups() called
        Then: .json.1 is created with primary content
        """
        primary = tmp_path / "evidence.db"
        primary.write_text("initial content")

        backup_1 = tmp_path / "evidence.db.1"

        manager = BackupManager(primary, count=3)
        manager.rotate_backups()

        assert backup_1.exists()
        assert backup_1.read_text() == "initial content"

    def test_rotate_backups_with_custom_count(self, tmp_path):
        """
        Test that rotate_backups respects custom count parameter.

        Given: count=5, existing backups up to .5
        When: rotate_backups() called
        Then: Rotation proceeds through all 5 generations
        """
        primary = tmp_path / "evidence.db"
        primary.write_text("primary")

        # Create 5 backup generations
        for i in range(1, 6):
            backup_file = tmp_path / f"evidence.db.{i}"
            backup_file.write_text(f"generation {i}")

        manager = BackupManager(primary, count=5)
        manager.rotate_backups()

        # Verify rotation through all 5
        backup_5 = tmp_path / "evidence.db.5"
        assert backup_5.exists()
        assert backup_5.read_text() == "generation 4"  # Old gen4 moved to gen5
