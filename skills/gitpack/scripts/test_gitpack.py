"""Stdlib-only self-check for gitpack._skill_companions.

Builds a temp plugin-shaped tree and asserts the companion resolver returns
the plugin-root docs + agents/ + commands/, and excludes sibling skills/.
Run: `python test_gitpack.py`.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gitpack import _skill_companions  # noqa: E402


def _build_fake_plugin(root: Path) -> Path:
    skills_dir = root / "skills" / "demo"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("# demo\n")
    for name in ("README.md", "OUTPUT_SCHEMA.md", "HOOKS_AVAILABLE.md",
                 "CLAUDE.md", "AGENTS.md", "config.json"):
        (root / name).write_text(f"# {name}\n")
    (root / "agents").mkdir()
    (root / "agents" / "specialist.md").write_text("# agent\n")
    (root / "commands").mkdir()
    (root / "commands" / "demo.md").write_text("# command\n")
    # Siblings that must NOT be picked up
    (root / "skills" / "other").mkdir()
    (root / "skills" / "other" / "SKILL.md").write_text("# other\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "hook.py").write_text("# hook\n")
    return skills_dir


def test_companions_includes_plugin_root_docs_and_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "demo-plugin"
        root.mkdir()
        skill_dir = _build_fake_plugin(root)
        companions = _skill_companions(skill_dir)
        names = [Path(c).name for c in companions]
        assert "README.md" in names, names
        assert "OUTPUT_SCHEMA.md" in names, names
        assert "HOOKS_AVAILABLE.md" in names, names
        assert "CLAUDE.md" in names, names
        assert "agents" in names, names
        assert "commands" in names, names
        # Sibling skills/ and scripts/ must not leak in
        assert "other" not in names, names
        assert "scripts" not in names, names
        assert "hook.py" not in names, names


def test_companions_empty_for_lone_skill_dir():
    with tempfile.TemporaryDirectory() as tmp:
        lone = Path(tmp) / "lone-skill"
        lone.mkdir()
        (lone / "SKILL.md").write_text("# lone\n")
        assert _skill_companions(lone) == []


def test_companions_skips_missing_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "plugin"
        (root / "skills" / "demo").mkdir(parents=True)
        (root / "skills" / "demo" / "SKILL.md").write_text("# demo\n")
        # Only README exists; the rest are absent
        (root / "README.md").write_text("# readme\n")
        companions = _skill_companions(root / "skills" / "demo")
        assert companions == [str(root / "README.md")], companions


if __name__ == "__main__":
    test_companions_includes_plugin_root_docs_and_dirs()
    test_companions_empty_for_lone_skill_dir()
    test_companions_skips_missing_files()
    print("OK: 3/3 _skill_companions tests passed")
