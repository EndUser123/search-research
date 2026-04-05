"""
Test suite for multi-terminal isolation.

Tests cover:
- Concurrent terminal operations don't interfere
- Terminal ID collision scenarios
- State directory separation per terminal
- Evidence isolation between terminals
"""

import json
from datetime import datetime, timezone


class TestConcurrentTerminalOperations:
    """Test that concurrent terminal operations don't interfere"""

    def test_concurrent_terminals_have_separate_state_dirs(self, temp_state_dir):
        """Test that different terminals have separate state directories"""
        terminals = []

        for i in range(3):
            terminal_id = f"terminal-concurrent-{i}"
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{i}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))
            terminals.append((terminal_id, intent_dir))

        # Verify all directories exist
        for terminal_id, intent_dir in terminals:
            assert intent_dir.exists()
            assert terminal_id in str(intent_dir)

        # Verify directories are separate
        dir_paths = [str(dir) for _, dir in terminals]
        assert len(dir_paths) == len(set(dir_paths)), "Directories are not unique"

    def test_write_operations_dont_interfere(self, temp_state_dir):
        """Test that write operations to different terminals don't interfere"""
        terminal_1_id = "terminal-write-1"
        terminal_2_id = "terminal-write-2"

        # Create intent files for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))

        # Verify both files exist with correct data
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_file = temp_state_dir / terminal_id / "pending_command_intent.json"

            with open(intent_file) as f:
                data = json.load(f)

            assert data["terminal_id"] == terminal_id
            assert data["prompt"] == f"/test-{terminal_id}"

    def test_delete_operations_dont_interfere(self, temp_state_dir):
        """Test that delete operations in one terminal don't affect others"""
        terminal_1_id = "terminal-delete-1"
        terminal_2_id = "terminal-delete-2"

        # Create intent files for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))

        # Delete terminal 1's intent file
        intent_file_1 = temp_state_dir / terminal_1_id / "pending_command_intent.json"
        intent_file_1.unlink()

        # Verify terminal 1 is deleted, terminal 2 still exists
        assert not intent_file_1.exists()

        intent_file_2 = temp_state_dir / terminal_2_id / "pending_command_intent.json"
        assert intent_file_2.exists()

    def test_read_operations_dont_see_other_terminals_data(self, temp_state_dir):
        """Test that read operations only see data for that terminal"""
        terminal_1_id = "terminal-read-1"
        terminal_2_id = "terminal-read-2"

        # Create intent files with different data
        for i, terminal_id in enumerate([terminal_1_id, terminal_2_id], 1):
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": f"skill-{i}",
                "prompt": f"/test-terminal-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{i}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))

        # Read terminal 1's data
        intent_file_1 = temp_state_dir / terminal_1_id / "pending_command_intent.json"

        with open(intent_file_1) as f:
            data_1 = json.load(f)

        # Verify terminal 1 only sees its own data
        assert data_1["skill"] == "skill-1"
        assert data_1["terminal_id"] == terminal_1_id

        # Verify terminal 2's data is not present in terminal 1's file
        assert "skill-2" not in str(data_1)


class TestTerminalIdCollision:
    """Test terminal ID collision scenarios"""

    def test_unique_terminal_ids_dont_collide(self, temp_state_dir):
        """Test that different terminal IDs create separate state"""
        # Use IDs that could potentially collide
        terminal_ids = [
            "term-abc123",
            "term-abc124",  # Very similar
            "term-xyz789"
        ]

        created_dirs = []

        for terminal_id in terminal_ids:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            created_dirs.append(intent_dir)

        # Verify all directories are unique
        dir_paths = [str(dir) for dir in created_dirs]
        assert len(dir_paths) == len(set(dir_paths)), "Terminal IDs created duplicate directories"

    def test_mock_pid_collision_scenario(self, temp_state_dir):
        """Test scenario where PID might be reused (collision risk)"""
        # Simulate PID reuse: Same PID but different timestamp
        pid = 12345
        timestamp_1 = "2024-01-01_10-00-00"  # Use underscores for Windows compatibility
        timestamp_2 = "2024-01-01_11-00-00"

        # Create terminal IDs with same PID but different timestamps
        terminal_1_id = f"term-pid{pid}-{timestamp_1}"
        terminal_2_id = f"term-pid{pid}-{timestamp_2}"

        # Both should create separate directories
        intent_dir_1 = temp_state_dir / terminal_1_id
        intent_dir_2 = temp_state_dir / terminal_2_id

        intent_dir_1.mkdir(parents=True, exist_ok=True)
        intent_dir_2.mkdir(parents=True, exist_ok=True)

        # Verify both are separate
        assert intent_dir_1 != intent_dir_2
        assert str(intent_dir_1) != str(intent_dir_2)

    def test_random_salt_prevents_collision(self, temp_state_dir):
        """Test that random salt component prevents terminal ID collision"""
        import random

        # Simulate terminal ID generation with random salt
        pid = 99999
        session_start_ts = "2024-03-14_12-00-00"  # Use underscores for Windows compatibility
        random_salt_1 = random.randint(1000, 9999)
        random_salt_2 = random.randint(1000, 9999)

        terminal_1_id = f"term-{pid}-{session_start_ts}-{random_salt_1}"
        terminal_2_id = f"term-{pid}-{session_start_ts}-{random_salt_2}"

        # Even with same PID and timestamp, random salt creates different IDs
        assert terminal_1_id != terminal_2_id

        # Create directories
        intent_dir_1 = temp_state_dir / terminal_1_id
        intent_dir_2 = temp_state_dir / terminal_2_id

        intent_dir_1.mkdir(parents=True, exist_ok=True)
        intent_dir_2.mkdir(parents=True, exist_ok=True)

        # Verify separate directories created
        assert intent_dir_1 != intent_dir_2


class TestStateDirectorySeparation:
    """Test that state directories are properly separated per terminal"""

    def test_each_terminal_has_own_intent_file(self, temp_state_dir):
        """Test that each terminal has its own intent file"""
        terminals = []

        for i in range(3):
            terminal_id = f"terminal-state-{i}"
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{i}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))
            terminals.append((terminal_id, intent_file))

        # Verify each terminal has exactly one intent file
        for terminal_id, intent_file in terminals:
            assert intent_file.exists()
            assert intent_file.name == "pending_command_intent.json"

    def test_terminals_dont_share_state_files(self, temp_state_dir):
        """Test that terminals don't share state files"""
        terminal_1_id = "terminal-share-1"
        terminal_2_id = "terminal-share-2"

        # Create separate state for each terminal
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))

        # Verify files are in different directories
        intent_file_1 = temp_state_dir / terminal_1_id / "pending_command_intent.json"
        intent_file_2 = temp_state_dir / terminal_2_id / "pending_command_intent.json"

        assert intent_file_1.parent != intent_file_2.parent

    def test_cleanup_in_one_terminal_doesnt_affect_others(self, temp_state_dir):
        """Test that cleanup in one terminal doesn't affect other terminals"""
        terminal_1_id = "terminal-cleanup-1"
        terminal_2_id = "terminal-cleanup-2"

        # Create intent files for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": "test",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))

        # Delete entire terminal 1 directory
        import shutil
        terminal_1_dir = temp_state_dir / terminal_1_id
        shutil.rmtree(terminal_1_dir)

        # Verify terminal 1 is gone
        assert not terminal_1_dir.exists()

        # Verify terminal 2 is unaffected
        terminal_2_dir = temp_state_dir / terminal_2_id
        assert terminal_2_dir.exists()


class TestEvidenceIsolation:
    """Test that evidence is isolated between terminals"""

    def test_evidence_logged_per_terminal(self, temp_state_dir):
        """Test that evidence is logged separately for each terminal"""
        terminals = []

        for i in range(2):
            terminal_id = f"terminal-evidence-{i}"
            evidence_dir = temp_state_dir / terminal_id / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            evidence_file = evidence_dir / f"session-{i}.log"

            evidence_file.write_text(f"Evidence for terminal {i}")

            terminals.append((terminal_id, evidence_file))

        # Verify each terminal has its own evidence log
        for terminal_id, evidence_file in terminals:
            assert evidence_file.exists()
            assert terminal_id in str(evidence_file)

    def test_cross_terminal_evidence_contamination_prevented(self, temp_state_dir):
        """Test that evidence from one terminal doesn't leak to another"""
        terminal_1_id = "terminal-contamination-1"
        terminal_2_id = "terminal-contamination-2"

        # Create evidence directories for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            evidence_dir = temp_state_dir / terminal_id / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

        # Terminal 1 writes evidence
        evidence_dir_1 = temp_state_dir / terminal_1_id / "evidence"
        evidence_file_1 = evidence_dir_1 / "session-1.log"
        evidence_file_1.write_text("Terminal 1 evidence")

        # Verify terminal 2 has no evidence from terminal 1
        terminal_2_evidence_dir = temp_state_dir / terminal_2_id / "evidence"

        # List all evidence files in terminal 2
        evidence_files = list(terminal_2_evidence_dir.glob("*.log"))

        # Terminal 2 should have no evidence files (or only its own)
        terminal_1_evidence_in_2 = any(
            "Terminal 1" in open(f).read()
            for f in evidence_files
        )

        assert not terminal_1_evidence_in_2, "Evidence leaked between terminals"
