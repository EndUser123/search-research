"""Tests for skill-from-docs/scripts/_validate_template.py.

Validates that the template itself works as a gate for the 6 pitfalls.
Tests use a temp skill fixture: a 'good' skill (passes) and a 'bad' skill
(fails on the pitfall each test targets).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TEMPLATE = Path(__file__).parent.parent / "_validate_template.py"


def _load_template() -> object:
    spec = importlib.util.spec_from_file_location("_validate_template", TEMPLATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_skill(tmp_path: Path, *, name: str = "test-skill", scripts: dict[str, str] | None = None) -> Path:
    """Build a minimal skill fixture under tmp_path/name/."""
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()

    body = (
        "## When to use\nfor testing\n\n"
        "## When NOT to use\nfor testing\n\n"
        "## Output contract\nfor testing\n\n"
        "## Related skills\nfor testing\n\n"
        "## Anti-patterns\n"
        "| Trap | Symptom | Mitigation |\n"
        "|------|---------|------------|\n"
        "| Test | Test | Test |\n"
    )

    fm = (
        "---\n"
        f"name: {name}\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill that has nothing of value but is structured correctly. "
        "It exists to validate the validator template, not to be used in production.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
    )
    if scripts:
        for fname, content in scripts.items():
            (scripts_dir / fname).write_text(content, encoding="utf-8")
        fm += "    script: scripts/" + next(iter(scripts.keys())) + "\n"

    fm += "---\n\n# " + name + "\n\n" + body
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")
    return skill_dir


def test_template_passes_on_good_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A well-structured skill should pass all gates."""
    skill_dir = _build_skill(tmp_path, scripts={"phase1.py": "print('ok')\n"})
    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 0, "expected 0 (pass), got " + str(rc)
    failed = [r for r in mod.results if r[1] == "FAIL"]
    assert not failed, "unexpected failures: " + str(failed)


def test_template_flags_missing_script_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 1: frontmatter `script:` resolves to a nonexistent file -> FAIL."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "scripts").mkdir()
    fm = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill whose frontmatter references a script that doesn't exist. "
        "Used to verify the validator catches the frontmatter-vs-disk contract violation.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
        "    script: scripts/does_not_exist.py\n"
        "---\n\n# test\n"
        "## When to use\nx\n\n## When NOT to use\nx\n\n"
        "## Output contract\nx\n\n## Related skills\nx\n\n"
        "## Anti-patterns\n| Trap | Symptom | Mitigation |\n|---|---|---|\n| x | x | x |\n"
    )
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 1, "expected 1 (fail), got " + str(rc)
    failed_names = [r[0] for r in mod.results if r[1] == "FAIL"]
    assert any("script resolves" in n for n in failed_names), failed_names


def test_template_flags_body_header_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 2: body code-block header `# scripts/foo.py` not in frontmatter scripts -> FAIL."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "real.py").write_text("print('ok')\n", encoding="utf-8")
    fm = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill whose body has a code-block header that disagrees with the "
        "frontmatter script key. Used to verify the validator catches the drift.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
        "    script: scripts/real.py\n"
        "---\n\n# test\n"
        "## When to use\nx\n\n## When NOT to use\nx\n\n"
        "## Output contract\nx\n\n## Related skills\nx\n\n"
        "## Anti-patterns\n| Trap | Symptom | Mitigation |\n|---|---|---|\n| x | x | x |\n\n"
        "```python\n"
        "# scripts/different_name.py\n"  # drift: not in frontmatter
        "print('hi')\n"
        "```\n"
    )
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 1, "expected 1 (fail), got " + str(rc)
    failed_names = [r[0] for r in mod.results if r[1] == "FAIL"]
    assert any("body code-block headers" in n for n in failed_names), failed_names


def test_template_flags_absolute_paths_in_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 5: hardcoded absolute paths in body prose -> FAIL."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "scripts").mkdir()
    fm = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill that hardcodes absolute paths in body prose. "
        "Used to verify the portability check flags the leak.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
        "---\n\n# test\n"
        "## When to use\nx\n\n## When NOT to use\nx\n\n"
        "## Output contract\nx\n\n## Related skills\nx\n\n"
        "## Anti-patterns\n| Trap | Symptom | Mitigation |\n|---|---|---|\n| x | x | x |\n\n"
        "Use the brain dir at C:/Users/brsth/.gemini/antigravity-cli/brain to find files.\n"
    )
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 1, "expected 1 (fail), got " + str(rc)
    failed_names = [r[0] for r in mod.results if r[1] == "FAIL"]
    assert any("absolute paths" in n for n in failed_names), failed_names


def test_template_flags_session_uuid_in_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 5: session UUID leaked into body -> FAIL."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "scripts").mkdir()
    fm = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill with a session UUID leaked into body. "
        "Used to verify the validator catches the leak outside frontmatter.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
        "---\n\n# test\n"
        "## When to use\nx\n\n## When NOT to use\nx\n\n"
        "## Output contract\nx\n\n## Related skills\nx\n\n"
        "## Anti-patterns\n| Trap | Symptom | Mitigation |\n|---|---|---|\n| x | x | x |\n\n"
        "The source session was 599e210f-ac5e-43c9-b9c7-d7d97026c6f6 (a real UUID).\n"
    )
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 1, "expected 1 (fail), got " + str(rc)
    failed_names = [r[0] for r in mod.results if r[1] == "FAIL"]
    assert any("session UUIDs" in n for n in failed_names), failed_names


def test_template_flags_no_antipatterns_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pitfall 6: missing anti-patterns table -> FAIL (no structural check)."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "scripts").mkdir()
    fm = (
        "---\n"
        "name: test-skill\n"
        "version: 0.1.0\n"
        "enforcement: advisory\n"
        "description: A test skill with no anti-patterns section. "
        "Used to verify the validator flags the missing structural check.\n"
        "workflow_steps:\n"
        "  - id: phase1\n"
        "    name: Phase 1\n"
        "    description: do phase 1\n"
        "---\n\n# test\n"
        "## When to use\nx\n\n## When NOT to use\nx\n\n"
        "## Output contract\nx\n\n## Related skills\nx\n"
    )
    (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["_validate_template", "--root", str(skill_dir)])
    mod = _load_template()
    rc = mod.main()
    assert rc == 1, "expected 1 (fail), got " + str(rc)
    failed_names = [r[0] for r in mod.results if r[1] == "FAIL"]
    assert any("Anti-patterns" in n for n in failed_names), failed_names
