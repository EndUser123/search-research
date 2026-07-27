"""Tests for the --full-body flag and write_stub full_body parameter in index_skills.py."""
import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

# Load index_skills module by absolute path (not a package)
_SPEC = importlib.util.spec_from_file_location(
    "index_skills", "P:/.data/wiki/scripts/index_skills.py"
)
index_skills = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(index_skills)
SkillEntry = index_skills.SkillEntry
write_stub = index_skills.write_stub
STUBS_DIR = index_skills.STUBS_DIR


def _make_entry(name="test-fb", path="nonexistent/SKILL.md"):
    return SkillEntry(
        scope="test-scope",
        plugin=None,
        name=name,
        path=path,
        description="A test skill.",
        grok_state="✓",
        claude_state="—",
    )


class TestFullBodyParameter:
    """Tests for write_stub(full_body=...) parameter."""

    def test_default_is_frontmatter_only(self):
        """full_body=False (default) produces frontmatter-only stub — original behavior preserved."""
        entry = _make_entry()
        p = write_stub(entry, full_body=False)
        try:
            content = p.read_text(encoding="utf-8")
            assert "## Full body" not in content, "frontmatter-only stub must NOT have body section"
            assert "A test skill." in content, "stub must contain description"
        finally:
            if p.exists():
                p.unlink()

    def test_full_body_true_on_missing_file_is_graceful(self):
        """full_body=True on a nonexistent source file produces stub without body section."""
        entry = _make_entry(path="nonexistent/MISSING.md")
        p = write_stub(entry, full_body=True)
        try:
            content = p.read_text(encoding="utf-8")
            assert "## Full body" not in content, "missing file should NOT produce body section"
            assert "A test skill." in content, "stub must still have description"
        finally:
            if p.exists():
                p.unlink()

    def test_full_body_true_on_real_file_includes_body(self):
        """full_body=True on a real SKILL.md includes the body with actual content."""
        real_skill = Path("C:/Users/brsth/.grok/skills/why/SKILL.md")
        if not real_skill.exists():
            pytest.skip("why/SKILL.md not available for test")
        entry = _make_entry(name="why-real", path=str(real_skill))
        p = write_stub(entry, full_body=True)
        try:
            content = p.read_text(encoding="utf-8")
            assert "## Full body" in content, "real file SHOULD produce body section"
            assert "Step 0" in content, "body should contain actual skill content"
            assert len(content) > 500, "full-body stub should be substantially larger than frontmatter"
        finally:
            if p.exists():
                p.unlink()

    def test_full_body_caps_at_8000_chars(self):
        """Body section caps at ~8000 chars when source exceeds the limit."""
        big_path = Path(tempfile.gettempdir()) / "test_big_skill.md"
        big_body = "x" * 20000  # 20K chars
        big_path.write_text(f"---\nname: big\n---\n\n{big_body}", encoding="utf-8")
        try:
            entry = _make_entry(name="big-skill", path=str(big_path))
            p = write_stub(entry, full_body=True)
            try:
                content = p.read_text(encoding="utf-8")
                if "## Full body" in content:
                    body_section = content.split("## Full body", 1)[1]
                    assert len(body_section) <= 8100, (
                        f"body section should be capped near 8000 chars, got {len(body_section)}"
                    )
            finally:
                if p.exists():
                    p.unlink()
        finally:
            if big_path.exists():
                big_path.unlink()


class TestArgparseFlag:
    """Tests for the --full-body CLI flag."""

    def test_flag_present_in_source(self):
        """The source file contains the --full-body argument."""
        src = Path("P:/.data/wiki/scripts/index_skills.py").read_text(encoding="utf-8")
        assert "--full-body" in src, "source must contain --full-body argument"
        assert "full_body" in src, "source must contain full_body parameter"

    def test_write_stub_has_full_body_param(self):
        """write_stub accepts a full_body keyword parameter."""
        import inspect
        sig = inspect.signature(write_stub)
        assert "full_body" in sig.parameters, "write_stub must have full_body parameter"
        assert sig.parameters["full_body"].default is False, "full_body default must be False"
