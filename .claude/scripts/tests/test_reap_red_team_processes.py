"""Tests for reap_red_team_processes.py and red_team_markers.py.

These tests verify the marker/deadline backstop for OpenCode red-team processes
that survive because the Python supervisor itself was terminated.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent

# Load red_team_markers module and register it in sys.modules so that
# reap_red_team_processes can import it by name.
markers_spec = importlib.util.spec_from_file_location(
    "red_team_markers", SCRIPTS_DIR / "red_team_markers.py"
)
markers = importlib.util.module_from_spec(markers_spec)
sys.modules["red_team_markers"] = markers
markers_spec.loader.exec_module(markers)

# Load reap_red_team_processes module (will import red_team_markers from sys.modules)
reaper_spec = importlib.util.spec_from_file_location(
    "reap_red_team_processes", SCRIPTS_DIR / "reap_red_team_processes.py"
)
reaper = importlib.util.module_from_spec(reaper_spec)
reaper_spec.loader.exec_module(reaper)


# --- Helpers ---


def make_marker(
    task_id="test-task",
    reviewer="testmodel",
    model_id="test/model",
    root_pid=99999,
    command=None,
    cwd="P:/",
    deadline_offset=0,
    creation_time=None,
):
    """Build a marker dict for testing."""
    if command is None:
        command = ["opencode", "run", "-m", model_id, "--format", "json", "review this"]
    now = time.time()
    if creation_time is None:
        creation_time = now
    return {
        "schema_version": "1",
        "task_id": task_id,
        "reviewer": reviewer,
        "model_id": model_id,
        "root_pid": root_pid,
        "process_creation_time": creation_time,
        "start_time": now - 300,
        "start_time_iso": "2026-01-01T00:00:00",
        "deadline": now + deadline_offset,
        "deadline_iso": "2026-01-01T00:05:00",
        "cwd": cwd,
        "command": [str(a) for a in command],
        "command_fingerprint": markers._command_fingerprint(command),
    }


def write_test_marker(marker_dir: Path, marker: dict) -> Path:
    """Write a marker dict directly to a test marker directory."""
    marker_dir.mkdir(parents=True, exist_ok=True)
    path = marker_dir / f"{marker['task_id']}.json"
    path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    return path


# --- Tests: marker creation and atomic writing ---


def test_marker_creation_includes_all_required_fields():
    marker = markers.create_marker(
        task_id="test-123",
        reviewer="model",
        model_id="test/model",
        root_pid=os.getpid(),
        command=["opencode", "run", "-m", "test/model", "--format", "json", "prompt"],
        cwd="P:/",
        deadline_seconds=210,
    )
    required = {
        "schema_version",
        "task_id",
        "reviewer",
        "model_id",
        "root_pid",
        "process_creation_time",
        "start_time",
        "start_time_iso",
        "deadline",
        "deadline_iso",
        "cwd",
        "command",
        "command_fingerprint",
    }
    assert required.issubset(set(marker.keys()))
    assert marker["schema_version"] == "1"
    assert marker["root_pid"] == os.getpid()
    assert marker["deadline"] > marker["start_time"]


def test_atomic_marker_write_no_tmp_left(tmp_path):
    marker_dir = tmp_path / "markers"
    marker = make_marker()
    marker["task_id"] = "atomic-test"

    with patch.object(markers, "MARKER_DIR", marker_dir):
        markers.write_marker(marker)

    assert marker_dir.exists()
    marker_file = marker_dir / "atomic-test.json"
    assert marker_file.exists()
    tmp_files = list(marker_dir.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_marker_write_then_read_roundtrip(tmp_path):
    marker_dir = tmp_path / "markers"
    marker = make_marker(task_id="roundtrip-test")
    marker["process_creation_time"] = 1234567890.0

    with patch.object(markers, "MARKER_DIR", marker_dir):
        markers.write_marker(marker)
        read_back = markers.read_marker(marker_dir / "roundtrip-test.json")

    assert read_back is not None
    assert read_back["task_id"] == "roundtrip-test"
    assert read_back["root_pid"] == 99999
    assert read_back["process_creation_time"] == 1234567890.0


def test_marker_removal(tmp_path):
    marker_dir = tmp_path / "markers"
    write_test_marker(marker_dir, make_marker(task_id="remove-me"))

    with patch.object(markers, "MARKER_DIR", marker_dir):
        removed = markers.remove_marker("remove-me")
        not_found = markers.remove_marker("nonexistent")

    assert removed is True
    assert not_found is False
    assert not (marker_dir / "remove-me.json").exists()


# --- Tests: marker removal on success/timeout (via run_opencode_model) ---


def test_marker_removed_on_success(tmp_path):
    """Verify marker is removed when run_opencode_model completes normally."""
    red_team_script = SCRIPTS_DIR / "red_team_blind_review.py"
    rtbr_spec = importlib.util.spec_from_file_location("rtbr_test", red_team_script)
    rtbr = importlib.util.module_from_spec(rtbr_spec)
    rtbr_spec.loader.exec_module(rtbr)

    marker_dir = tmp_path / "markers"

    class FakeProc:
        pid = 88888
        returncode = 0

        def communicate(self, timeout=None):
            return ('{"type":"text","part":{"type":"text","text":"ok"}}', "")

        def kill(self):
            pass

    with patch.object(rtbr.markers, "MARKER_DIR", marker_dir):
        with patch.object(rtbr.subprocess, "Popen", return_value=FakeProc()):
            rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")

    if marker_dir.exists():
        files = list(marker_dir.glob("*.json"))
        assert len(files) == 0, f"marker files should be removed, found: {files}"


def test_marker_removed_on_timeout(tmp_path):
    """Verify marker is removed when run_opencode_model times out."""
    red_team_script = SCRIPTS_DIR / "red_team_blind_review.py"
    rtbr_spec = importlib.util.spec_from_file_location("rtbr_test2", red_team_script)
    rtbr = importlib.util.module_from_spec(rtbr_spec)
    rtbr_spec.loader.exec_module(rtbr)

    marker_dir = tmp_path / "markers"

    class FakeProc:
        pid = 77777
        returncode = 0
        _count = 0

        def communicate(self, timeout=None):
            FakeProc._count += 1
            if FakeProc._count == 1:
                raise subprocess.TimeoutExpired(cmd="opencode", timeout=timeout)
            return ("", "")

        def kill(self):
            pass

    with patch.object(rtbr.markers, "MARKER_DIR", marker_dir):
        with patch.object(rtbr.subprocess, "Popen", return_value=FakeProc()):
            with patch.object(rtbr, "_kill_process_tree", return_value={"ok": True, "error": None}):
                rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")

    if marker_dir.exists():
        files = list(marker_dir.glob("*.json"))
        assert len(files) == 0, f"marker files should be removed after timeout, found: {files}"


# --- Tests: reaper selection logic ---


def test_expired_matching_process_is_selected(tmp_path):
    """An expired marker with a live, matching process should be killed."""
    marker_dir = tmp_path / "markers"
    own_pid = os.getpid()
    own_creation = markers._get_process_creation_time(own_pid)

    # Use a command that passes the interactive check, and patch cmdline
    # verification to match.
    fake_cmd = ["opencode", "run", "-m", "test/model", "--format", "json", "prompt"]
    marker = make_marker(
        task_id="expired-alive",
        root_pid=own_pid,
        deadline_offset=-300,
        creation_time=own_creation,
        command=fake_cmd,
    )
    write_test_marker(marker_dir, marker)

    killed_pids = []

    def fake_kill(pid):
        killed_pids.append(pid)
        return {"ok": True, "error": None}

    # is_process_alive is called twice: once before kill (True), once after (False).
    with patch.object(markers, "kill_process_tree", side_effect=fake_kill):
        with patch.object(markers, "is_process_alive", side_effect=[True, False]):
            with patch.object(markers, "verify_command_fingerprint", return_value=True):
                result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["killed"] == 1
    assert own_pid in killed_pids
    assert result["summary"]["markers_removed"] == 1


def test_non_expired_process_is_not_selected(tmp_path):
    """A marker whose deadline hasn't passed should be skipped."""
    marker_dir = tmp_path / "markers"
    marker = make_marker(task_id="not-expired", deadline_offset=+600)
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_not_expired"] == 1
    assert result["summary"]["killed"] == 0
    mock_kill.assert_not_called()


def test_pid_reuse_or_creation_time_mismatch_is_skipped(tmp_path):
    """If the PID's creation time doesn't match, the reaper should skip it."""
    marker_dir = tmp_path / "markers"
    own_pid = os.getpid()

    marker = make_marker(
        task_id="pid-reuse",
        root_pid=own_pid,
        deadline_offset=-300,
        creation_time=1.0,
        command=["opencode", "run", "-m", "test/model", "--format", "json", "prompt"],
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_pid_mismatch"] == 1
    assert result["summary"]["killed"] == 0
    mock_kill.assert_not_called()


def test_interactive_opencode_command_is_skipped(tmp_path):
    """A marker whose command looks like an interactive session should be skipped."""
    marker_dir = tmp_path / "markers"
    marker = make_marker(
        task_id="interactive",
        root_pid=os.getpid(),
        deadline_offset=-300,
        command=["opencode"],
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_interactive"] == 1
    assert result["summary"]["killed"] == 0
    mock_kill.assert_not_called()


def test_interactive_opencode_without_run_subcommand_skipped(tmp_path):
    """A command with 'opencode' but no 'run' subcommand is interactive."""
    marker_dir = tmp_path / "markers"
    marker = make_marker(
        task_id="interactive-no-run",
        root_pid=os.getpid(),
        deadline_offset=-300,
        command=["opencode", "--model", "test"],
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_interactive"] == 1
    mock_kill.assert_not_called()


def test_malformed_marker_is_ignored(tmp_path):
    """A file that isn't valid JSON should be skipped, not crash the reaper."""
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_malformed"] == 1
    assert result["summary"]["killed"] == 0
    mock_kill.assert_not_called()


def test_dry_run_never_kills(tmp_path):
    """--dry-run should report what would be killed but never actually kill."""
    marker_dir = tmp_path / "markers"
    own_pid = os.getpid()
    own_cmdline = markers._get_process_cmdline(own_pid)
    own_creation = markers._get_process_creation_time(own_pid)

    # The marker command must pass the interactive check (must contain 'run'
    # and '--format json'). But the cmdline fingerprint must also match the
    # live process. So we patch verify_command_fingerprint to return True.
    fake_cmd = ["opencode", "run", "-m", "test/model", "--format", "json", "prompt"]
    marker = make_marker(
        task_id="dry-run-target",
        root_pid=own_pid,
        deadline_offset=-300,
        creation_time=own_creation,
        command=fake_cmd,
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        with patch.object(markers, "verify_command_fingerprint", return_value=True):
            result = reaper.scan_and_reap(marker_dir, dry_run=True)

    assert mock_kill.call_count == 0
    assert any(d["action"] == "would_kill" for d in result["details"])


def test_dead_pid_marker_is_cleaned_up(tmp_path):
    """If the PID is no longer alive, the marker should be removed without killing."""
    marker_dir = tmp_path / "markers"
    marker = make_marker(
        task_id="dead-pid",
        root_pid=999999,
        deadline_offset=-300,
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "is_process_alive", return_value=False):
        with patch.object(markers, "kill_process_tree") as mock_kill:
            result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_pid_dead"] == 1
    assert result["summary"]["markers_removed"] == 1
    mock_kill.assert_not_called()
    assert not (marker_dir / "dead-pid.json").exists()


def test_cmdline_mismatch_is_skipped(tmp_path):
    """If the command line no longer matches, the reaper should skip it."""
    marker_dir = tmp_path / "markers"
    own_pid = os.getpid()
    own_creation = markers._get_process_creation_time(own_pid)

    # The marker command must pass the interactive check (has 'run' + '--format json'),
    # but the fingerprint must NOT match the live process's actual cmdline.
    marker = make_marker(
        task_id="cmdline-mismatch",
        root_pid=own_pid,
        deadline_offset=-300,
        creation_time=own_creation,
        command=[
            "opencode",
            "run",
            "-m",
            "different/model",
            "--format",
            "json",
            "different prompt",
        ],
    )
    write_test_marker(marker_dir, marker)

    with patch.object(markers, "kill_process_tree") as mock_kill:
        result = reaper.scan_and_reap(marker_dir, dry_run=False)

    assert result["summary"]["skipped_cmdline_mismatch"] == 1
    assert result["summary"]["killed"] == 0
    mock_kill.assert_not_called()


def test_reaper_handles_empty_directory(tmp_path):
    """An empty marker directory should produce all-zero counts."""
    marker_dir = tmp_path / "empty"
    marker_dir.mkdir(parents=True, exist_ok=True)
    result = reaper.scan_and_reap(marker_dir, dry_run=False)
    s = result["summary"]
    assert s["scanned"] == 0
    assert s["killed"] == 0


def test_reaper_handles_nonexistent_directory(tmp_path):
    """A nonexistent marker directory should not crash."""
    marker_dir = tmp_path / "does-not-exist"
    result = reaper.scan_and_reap(marker_dir, dry_run=False)
    assert result["summary"]["scanned"] == 0
