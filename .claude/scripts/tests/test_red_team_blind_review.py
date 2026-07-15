from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "red_team_blind_review.py"

spec = importlib.util.spec_from_file_location("red_team_blind_review", SCRIPT)
rtbr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rtbr)


class FakeProc:
    """Minimal Popen stand-in for testing run_opencode_model."""

    def __init__(self, stdout="", stderr="", returncode=0, timeout=False, pid=99999):
        self.pid = pid
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self._timeout = timeout
        self._communicate_count = 0
        self.communicate_timeout = None
        self.killed = False

    def communicate(self, timeout=None):
        self._communicate_count += 1
        self.communicate_timeout = timeout
        if self._timeout and self._communicate_count == 1:
            raise subprocess.TimeoutExpired(cmd="opencode", timeout=timeout)
        return (self._stdout, self._stderr)

    def kill(self):
        self.killed = True


# --- Tests: _parse_opencode_json_events ---


def test_json_event_parsing_multiple_text_events():
    stdout = "\n".join(
        [
            '{"type":"start","part":{"type":"start"}}',
            '{"type":"text","part":{"type":"text","text":"First part "}}',
            '{"type":"text","part":{"type":"text","text":"second part"}}',
            '{"type":"end","part":{"type":"end"}}',
        ]
    )
    assert rtbr._parse_opencode_json_events(stdout) == "First part second part"


def test_json_event_parsing_skips_non_json_lines():
    stdout = "\n".join(
        [
            "not json at all",
            '{"type":"text","part":{"type":"text","text":"kept"}}',
            "{broken",
            "",
        ]
    )
    assert rtbr._parse_opencode_json_events(stdout) == "kept"


def test_json_event_parsing_empty_input():
    assert rtbr._parse_opencode_json_events("") == ""
    assert rtbr._parse_opencode_json_events(None) == ""


def test_json_event_parsing_no_text_events():
    assert rtbr._parse_opencode_json_events('{"type":"other"}') == ""


# --- Tests: run_opencode_model normal completion ---


def test_normal_completion():
    stdout = '{"type":"text","part":{"type":"text","text":"Review findings here"}}'
    fake = FakeProc(stdout=stdout, returncode=0)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert result["reviewer"] == "model"
    assert result["model_id"] == "test/model"
    assert result["raw_response"] == "Review findings here"
    assert "error" not in result


def test_nonzero_exit_code():
    fake = FakeProc(stderr="boom", returncode=1)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert "error" in result
    assert "exit 1" in result["error"]
    assert "boom" in result["error"]


def test_no_text_in_output():
    fake = FakeProc(stdout='{"type":"other"}', returncode=0)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert "error" in result
    assert "no text" in result["error"]


def test_file_not_found():
    with patch.object(rtbr.subprocess, "Popen", side_effect=FileNotFoundError):
        result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert "error" in result
    assert "not found" in result["error"]


# --- Tests: timeout classification and tree kill ---


def test_timeout_classification():
    fake = FakeProc(timeout=True, pid=12345)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        with patch.object(rtbr, "_kill_process_tree", return_value={"ok": True, "error": None}):
            result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert "error" in result
    assert "timeout" in result["error"]
    assert "210" in result["error"]
    assert result["timeout_duration"] == 210
    assert result["cleanup_ok"] is True
    assert "cleanup_error" not in result


def test_timeout_calls_kill_tree_with_pid():
    fake = FakeProc(timeout=True, pid=77777)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        with patch.object(
            rtbr, "_kill_process_tree", return_value={"ok": True, "error": None}
        ) as mock_kill:
            rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    mock_kill.assert_called_once_with(77777)


def test_timeout_includes_cleanup_error_on_failure():
    fake = FakeProc(timeout=True, pid=12345)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        with patch.object(
            rtbr,
            "_kill_process_tree",
            return_value={"ok": False, "error": "taskkill.exe not found"},
        ):
            result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert result["cleanup_ok"] is False
    assert result["cleanup_error"] == "taskkill.exe not found"


# --- Tests: _kill_process_tree exception safety ---


def test_kill_process_tree_returns_ok_on_success():
    fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(rtbr.subprocess, "run", return_value=fake_result):
            result = rtbr._kill_process_tree(54321)
    assert result == {"ok": True, "error": None}


def test_kill_process_tree_handles_file_not_found():
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(rtbr.subprocess, "run", side_effect=FileNotFoundError):
            result = rtbr._kill_process_tree(54321)
    assert result["ok"] is False
    assert "taskkill.exe not found" in result["error"]


def test_kill_process_tree_handles_timeout_expired():
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(
            rtbr.subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="tk", timeout=30)
        ):
            result = rtbr._kill_process_tree(54321)
    assert result["ok"] is False
    assert "timed out" in result["error"]


def test_kill_process_tree_handles_oserror():
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(rtbr.subprocess, "run", side_effect=OSError("boom")):
            result = rtbr._kill_process_tree(54321)
    assert result["ok"] is False
    assert "OSError" in result["error"]


def test_kill_process_tree_captures_nonzero_exit():
    fake_result = subprocess.CompletedProcess(
        args=[], returncode=128, stdout="", stderr="ERROR: process not found"
    )
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(rtbr.subprocess, "run", return_value=fake_result):
            result = rtbr._kill_process_tree(54321)
    assert result["ok"] is False
    assert "exit 128" in result["error"]
    assert "process not found" in result["error"]


# --- Tests: exact taskkill invocation ---


def test_exact_taskkill_invocation():
    fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch.object(rtbr.os, "name", "nt"):
        with patch.object(rtbr.subprocess, "run", return_value=fake_result) as mock_run:
            rtbr._kill_process_tree(54321)
    mock_run.assert_called_once_with(
        ["taskkill.exe", "/PID", "54321", "/T", "/F"],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_taskkill_not_called_on_non_windows():
    with patch.object(rtbr.os, "name", "posix"):
        with patch.object(rtbr.subprocess, "run") as mock_run:
            with patch.object(rtbr.os, "kill") as mock_kill:
                rtbr._kill_process_tree(54321)
    mock_run.assert_not_called()
    mock_kill.assert_called_once()
    assert mock_kill.call_args[0][0] == 54321


# --- Tests: 210-second timeout preservation ---


def test_210s_timeout_preservation():
    fake = FakeProc(stdout='{"type":"text","part":{"type":"text","text":"ok"}}', returncode=0)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert fake.communicate_timeout == 210


def test_210s_timeout_preservation_via_env_override():
    fake = FakeProc(stdout='{"type":"text","part":{"type":"text","text":"ok"}}', returncode=0)
    with patch.dict(os.environ, {"RED_TEAM_OPENCODE_TIMEOUT": "300"}):
        rtbr_2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rtbr_2)
        with patch.object(rtbr_2.subprocess, "Popen", return_value=fake):
            rtbr_2.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert fake.communicate_timeout == 330


# --- Windows integration test: real process tree kill ---


@pytest.mark.skipif(os.name != "nt", reason="Windows-only taskkill integration test")
def test_integration_taskkill_kills_real_process_tree():
    """Spawn a real parent+grandchild tree, kill via _kill_process_tree, verify both die.

    Uses a Python launcher that spawns a long-running child and writes both PIDs
    to a temp file. This creates a two-level process tree identical in structure
    to opencode.CMD -> node.exe, and avoids relying on wmic (deprecated on newer
    Windows builds).
    """
    import tempfile

    pid_file = Path(tempfile.gettempdir()) / f"red_team_test_tree_{os.getpid()}.txt"

    # Python launcher: starts a child (also long-running), writes both PIDs,
    # then waits forever. Both processes will be killed by taskkill /T /F.
    # Uses chr(10) for newline to avoid f-string brace/newline escaping issues.
    launcher_code = (
        f"import subprocess, sys, os\n"
        f"child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],"
        f" stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        f"with open(r'{pid_file}', 'w') as f:\n"
        f"    f.write(str(os.getpid()) + chr(10) + str(child.pid))\n"
        f"child.wait()\n"
    )

    parent = subprocess.Popen(
        [sys.executable, "-c", launcher_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    parent_pid = parent.pid
    grandchild_pid = None

    try:
        # Wait for the launcher to write the PID file.
        deadline = time.time() + 10
        while time.time() < deadline:
            if pid_file.exists():
                lines = pid_file.read_text().strip().splitlines()
                if len(lines) >= 2:
                    parent_pid = int(lines[0])
                    grandchild_pid = int(lines[1])
                break
            time.sleep(0.3)

        if grandchild_pid is None:
            pytest.skip("Launcher did not write PID file in time")

        assert _process_is_alive(parent_pid), "parent should be alive before kill"
        assert _process_is_alive(grandchild_pid), "grandchild should be alive before kill"

        result = rtbr._kill_process_tree(parent_pid)
        assert result["ok"] is True, f"taskkill failed: {result.get('error')}"

        # taskkill /T /F is synchronous, but give the OS a moment to reap.
        deadline = time.time() + 10
        while time.time() < deadline:
            if not _process_is_alive(parent_pid) and not _process_is_alive(grandchild_pid):
                break
            time.sleep(0.5)

        assert not _process_is_alive(parent_pid), "parent should be dead after taskkill /T /F"
        assert not _process_is_alive(grandchild_pid), (
            "grandchild should be dead after taskkill /T /F"
        )
    finally:
        # Safety net: ensure nothing leaks even if assertions fail.
        if _process_is_alive(parent_pid):
            subprocess.run(
                ["taskkill.exe", "/PID", str(parent_pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
            )
        try:
            parent.wait(timeout=5)
        except Exception:
            pass
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass


def _process_is_alive(pid: int) -> bool:
    """Return True if a process with the given PID is still running."""
    try:
        result = subprocess.run(
            ["tasklist.exe", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return str(pid) in (result.stdout or "")
    except Exception:
        return False


# --- Tests: marker lifecycle in run_opencode_model ---


@pytest.fixture
def temp_marker_dir(tmp_path, monkeypatch):
    """Redirect marker directory to a temp path for isolation."""
    marker_dir = tmp_path / "markers"
    monkeypatch.setattr(rtbr.markers, "MARKER_DIR", marker_dir)
    return marker_dir


def test_marker_created_on_popen_success(temp_marker_dir):
    """A marker file should exist while the process is running."""
    fake = FakeProc(stdout='{"type":"text","part":{"type":"text","text":"ok"}}', returncode=0)
    marker_files_before = list(temp_marker_dir.glob("*.json")) if temp_marker_dir.exists() else []
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    # Marker should be removed after completion — no files should remain.
    marker_files_after = list(temp_marker_dir.glob("*.json")) if temp_marker_dir.exists() else []
    assert len(marker_files_after) == 0, "marker should be removed on normal completion"


def test_marker_removed_on_normal_completion(temp_marker_dir):
    """Marker is written during Popen and removed after successful completion."""
    fake = FakeProc(stdout='{"type":"text","part":{"type":"text","text":"ok"}}', returncode=0)
    captured_markers = []

    original_write = rtbr.markers.write_marker
    original_remove = rtbr.markers.remove_marker

    def track_write(marker):
        captured_markers.append(marker)
        return original_write(marker)

    def track_remove(task_id):
        return original_remove(task_id)

    with patch.object(rtbr.markers, "write_marker", side_effect=track_write):
        with patch.object(rtbr.markers, "remove_marker", side_effect=track_remove) as mock_remove:
            with patch.object(rtbr.subprocess, "Popen", return_value=fake):
                rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")

    assert len(captured_markers) == 1, "marker should be written once"
    assert captured_markers[0]["root_pid"] == fake.pid
    assert captured_markers[0]["model_id"] == "test/model"
    assert captured_markers[0]["schema_version"] == "1"
    assert mock_remove.call_count == 1


def test_marker_removed_on_timeout(temp_marker_dir):
    """Marker should be removed even when the job times out."""
    fake = FakeProc(timeout=True, pid=44444)
    with patch.object(rtbr.markers, "write_marker") as mock_write:
        with patch.object(rtbr.markers, "remove_marker") as mock_remove:
            with patch.object(rtbr, "_kill_process_tree", return_value={"ok": True, "error": None}):
                with patch.object(rtbr.subprocess, "Popen", return_value=fake):
                    rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert mock_write.call_count == 1
    assert mock_remove.call_count == 1


def test_marker_removed_on_error(temp_marker_dir):
    """Marker should be removed when communicate raises a non-timeout exception."""
    fake = FakeProc(stdout="ok", returncode=0)
    fake.communicate = lambda timeout=None: (_ for _ in ()).throw(RuntimeError("pipe broken"))

    with patch.object(rtbr.markers, "write_marker") as mock_write:
        with patch.object(rtbr.markers, "remove_marker") as mock_remove:
            with patch.object(rtbr, "_kill_process_tree", return_value={"ok": True, "error": None}):
                with patch.object(rtbr.subprocess, "Popen", return_value=fake):
                    result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")

    assert mock_write.call_count == 1
    assert mock_remove.call_count == 1
    assert "RuntimeError" in result["error"]


def test_marker_removed_on_nonzero_exit(temp_marker_dir):
    """Marker should be removed on nonzero exit code."""
    fake = FakeProc(stderr="fail", returncode=1)
    with patch.object(rtbr.markers, "write_marker") as mock_write:
        with patch.object(rtbr.markers, "remove_marker") as mock_remove:
            with patch.object(rtbr.subprocess, "Popen", return_value=fake):
                rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert mock_remove.call_count == 1


def test_marker_atomic_write(temp_marker_dir):
    """Marker write should not leave .tmp files behind."""
    fake = FakeProc(stdout='{"type":"text","part":{"type":"text","text":"ok"}}', returncode=0)
    with patch.object(rtbr.subprocess, "Popen", return_value=fake):
        rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    if temp_marker_dir.exists():
        tmp_files = list(temp_marker_dir.glob("*.tmp"))
        assert len(tmp_files) == 0, "no .tmp files should remain after atomic write"


def test_marker_not_written_on_popen_failure(temp_marker_dir):
    """If Popen raises FileNotFoundError, no marker should be written."""
    with patch.object(rtbr.subprocess, "Popen", side_effect=FileNotFoundError):
        with patch.object(rtbr.markers, "write_marker") as mock_write:
            result = rtbr.run_opencode_model("test/model", "doc.md", "glm-5.2")
    assert mock_write.call_count == 0
    assert "not found" in result["error"]
