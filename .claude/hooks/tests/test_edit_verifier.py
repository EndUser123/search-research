"""
Tests for posttooluse/edit_verifier.py

Covers:
- verify_write: memory file exemption from exact-match check
- verify_write: non-memory files still blocked on content mismatch
- verify_write: empty file still blocked regardless of path
- verify_edit: new_string presence check
"""

import sys
from pathlib import Path

# Ensure hooks root is on path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from posttooluse.edit_verifier import verify_edit, verify_write


# ---------------------------------------------------------------------------
# verify_write — memory file exemption
# ---------------------------------------------------------------------------


class TestVerifyWriteMemoryExemption:
    """Memory files (.claude/projects/*/memory/) bypass exact-match check.

    Claude Code's native memory system appends originSessionId to frontmatter
    after the Write tool completes, so exact-match will always fail for those
    files. We verify existence + non-empty only.
    """

    def test_memory_file_allows_content_mismatch(self, tmp_path: Path) -> None:
        """Memory file with appended originSessionId must not block."""
        # Simulate the Claude Code memory path structure
        mem_dir = tmp_path / ".claude" / "projects" / "P--" / "memory"
        mem_dir.mkdir(parents=True)
        mem_file = mem_dir / "feedback_direct_answers.md"

        written_content = "---\nname: test\ntype: feedback\n---\nBody text.\n"
        # Claude Code appends originSessionId — disk content differs from written
        disk_content = written_content.rstrip("\n") + "\noriginSessionId: abc-123\n"
        mem_file.write_text(disk_content, encoding="utf-8")

        success, reason, _ = verify_write(str(mem_file), written_content)

        assert success is True, f"Memory file should be exempt from exact-match: {reason}"

    def test_memory_file_still_blocks_when_empty(self, tmp_path: Path) -> None:
        """Memory file that is empty must still block regardless of exemption."""
        mem_dir = tmp_path / ".claude" / "projects" / "P--" / "memory"
        mem_dir.mkdir(parents=True)
        mem_file = mem_dir / "empty.md"
        mem_file.write_text("", encoding="utf-8")

        success, reason, _ = verify_write(str(mem_file), "expected content")

        assert success is False
        assert "empty" in reason.lower()

    def test_memory_file_passes_when_content_matches_exactly(self, tmp_path: Path) -> None:
        """Exact match on memory file also passes (no regression)."""
        mem_dir = tmp_path / ".claude" / "projects" / "P--" / "memory"
        mem_dir.mkdir(parents=True)
        mem_file = mem_dir / "exact.md"
        content = "---\nname: x\n---\nBody.\n"
        mem_file.write_text(content, encoding="utf-8")

        success, _, _ = verify_write(str(mem_file), content)

        assert success is True


# ---------------------------------------------------------------------------
# verify_write — non-memory files still enforce exact-match
# ---------------------------------------------------------------------------


class TestVerifyWriteNonMemory:
    def test_non_memory_file_blocks_on_content_mismatch(self, tmp_path: Path) -> None:
        """Non-memory file with content mismatch must block (regression guard)."""
        f = tmp_path / "some_hook.py"
        disk_content = "# original\n"
        expected_content = "# different\n"
        f.write_text(disk_content, encoding="utf-8")

        success, reason, _ = verify_write(str(f), expected_content)

        assert success is False
        assert "mismatch" in reason.lower()

    def test_non_memory_file_passes_on_exact_match(self, tmp_path: Path) -> None:
        content = "# correct content\n"
        f = tmp_path / "hook.py"
        f.write_text(content, encoding="utf-8")

        success, _, _ = verify_write(str(f), content)

        assert success is True

    def test_non_memory_file_blocks_when_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")

        success, reason, _ = verify_write(str(f), "expected")

        assert success is False
        assert "empty" in reason.lower()


# ---------------------------------------------------------------------------
# verify_write — path edge cases
# ---------------------------------------------------------------------------


class TestVerifyWritePathEdgeCases:
    def test_missing_file_blocks(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.md"
        success, _, _ = verify_write(str(missing), "content")
        assert success is False

    def test_empty_file_path_blocks(self) -> None:
        success, _, _ = verify_write("", "content")
        assert success is False

    def test_directory_path_blocks(self, tmp_path: Path) -> None:
        success, _, _ = verify_write(str(tmp_path), "content")
        assert success is False


# ---------------------------------------------------------------------------
# verify_edit
# ---------------------------------------------------------------------------


class TestVerifyEdit:
    def test_new_string_present_passes(self, tmp_path: Path) -> None:
        f = tmp_path / "file.py"
        f.write_text("def foo():\n    return 42\n", encoding="utf-8")
        success, _, _ = verify_edit(str(f), "return 1", "return 42")
        assert success is True

    def test_new_string_absent_blocks(self, tmp_path: Path) -> None:
        f = tmp_path / "file.py"
        f.write_text("def foo():\n    return 1\n", encoding="utf-8")
        success, reason, _ = verify_edit(str(f), "return 1", "return 42")
        assert success is False
        assert "not found" in reason.lower()

    def test_missing_old_or_new_string_skips(self, tmp_path: Path) -> None:
        f = tmp_path / "file.py"
        f.write_text("content", encoding="utf-8")
        success, reason, _ = verify_edit(str(f), "", "new")
        assert success is True
        assert "skipped" in reason.lower()
