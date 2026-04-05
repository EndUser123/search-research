"""Tests for lib/critique_io.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from critique_io import (
    CritiqueSession,
)


class TestCritiqueSessionInit:
    """Test CritiqueSession initialization."""

    def test_init_creates_timestamp_and_session_dir(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        assert session.session_dir is not None
        assert session.session_dir.parent == tmp_path
        assert session.session_dir.name.startswith("critique-")

    def test_init_uses_provided_staging_root(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        assert session.staging_root == tmp_path

    def test_init_uses_default_staging_root(self):
        session = CritiqueSession()
        from critique_io import STAGING_ROOT

        assert session.staging_root == STAGING_ROOT

    def test_files_dict_starts_empty(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        assert session._files == {}


class TestSetup:
    """Test setup() method."""

    def test_setup_creates_session_dir(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        assert not session.session_dir.exists()
        session.setup()
        assert session.session_dir.exists()
        assert session.session_dir.is_dir()

    def test_setup_initializes_files_dict(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        assert "work" in session._files
        assert "p1" in session._files
        assert "p2" in session._files
        assert "p3" in session._files

    def test_setup_initializes_files_dict_with_correct_paths(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        # setup() initializes _files dict with Path objects but does NOT create files on disk
        assert session._files["work"].name == "work.md"
        assert session._files["p1"].name == "p1_findings.md"
        assert session._files["p2"].name == "p2.md"
        assert session._files["p3"].name == "p3.md"
        assert session._files["work"].parent == session.session_dir

    def test_setup_returns_self_for_chaining(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        result = session.setup()
        assert result is session


class TestWriteReadWork:
    """Test work file write/read via public methods."""

    def test_write_and_read_work(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_work("# Test Work\n\nSome content here.")
        work_file = session.get_work_file()
        content = work_file.read_text(encoding="utf-8")
        assert content == "# Test Work\n\nSome content here."

    def test_write_work_creates_file(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_work("content")
        assert session.get_work_file().exists()

    def test_read_work_after_write(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_work("test content")
        assert session.read_work() == "test content"


class TestWriteReadPhase:
    """Test phase file write/read."""

    def test_write_and_read_phase_1(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(1, "# Phase 1 Findings\n\nFinding 1.")
        content = session.get_phase_file(1).read_text(encoding="utf-8")
        assert content == "# Phase 1 Findings\n\nFinding 1."

    def test_write_and_read_phase_2(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(2, "# Phase 2\n\nMeta critique.")
        content = session.get_phase_file(2).read_text(encoding="utf-8")
        assert content == "# Phase 2\n\nMeta critique."

    def test_write_and_read_phase_3(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(3, "# Phase 3\n\nSynthesis.")
        content = session.get_phase_file(3).read_text(encoding="utf-8")
        assert content == "# Phase 3\n\nSynthesis."

    def test_read_phase_via_method(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(1, "phase 1 content")
        assert session.read_phase(1) == "phase 1 content"

    def test_write_phase_2_verifies_filename(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(2, "# Phase 2 Meta-Critique\n\nContent here.")
        p2_path = session.get_phase_file(2)
        assert p2_path.name == "p2.md"
        assert p2_path.read_text(encoding="utf-8") == "# Phase 2 Meta-Critique\n\nContent here."

    def test_write_phase_3_verifies_filename(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_phase(3, "# Phase 3 Synthesis\n\nFinal output.")
        p3_path = session.get_phase_file(3)
        assert p3_path.name == "p3.md"
        assert p3_path.read_text(encoding="utf-8") == "# Phase 3 Synthesis\n\nFinal output."


class TestGetSessionDir:
    """Test session directory access."""

    def test_get_session_dir_returns_session_dir(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        assert session.get_session_dir() == session.session_dir


class TestGetSpecialistsDir:
    """Test specialists subdirectory creation."""

    def test_get_specialists_dir_creates_if_missing(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        specialists = session.get_specialists_dir()
        assert specialists == session.session_dir / "specialists"
        assert specialists.exists()


class TestCleanup:
    """Test session cleanup."""

    def test_cleanup_removes_session_dir(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        session.write_work("test")
        assert session.session_dir.exists()

        result = session.cleanup()
        assert isinstance(result, dict)
        assert "removed" in result
        assert not session.session_dir.exists()

    def test_cleanup_returns_dict_with_removed_and_errors(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        session.setup()
        result = session.cleanup()
        assert "removed" in result
        assert "errors" in result
        assert isinstance(result["removed"], list)
        assert isinstance(result["errors"], list)


class TestTerminalId:
    """Test terminal ID detection."""

    def test_get_terminal_id_returns_string(self):
        from critique_io import _get_terminal_id

        tid = _get_terminal_id()
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_get_terminal_id_deterministic(self):
        from critique_io import _get_terminal_id

        tid1 = _get_terminal_id()
        tid2 = _get_terminal_id()
        assert tid1 == tid2


class TestEnsureFiles:
    """Test _ensure_files lazy initialization."""

    def test_ensure_files_calls_setup_if_files_empty(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        # Don't call setup(), but write_work triggers _ensure_files
        assert session._files == {}
        session.write_work("lazy init")
        assert session._files != {}
        assert session.get_work_file().exists()

    def test_write_phase_also_ensures_files(self, tmp_path: Path):
        session = CritiqueSession(staging_root=tmp_path)
        assert session._files == {}
        session.write_phase(1, "content")
        assert session._files != {}
        assert session.get_phase_file(1).exists()
