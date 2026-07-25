"""Verifier tests for index_skills.py plugin-state annotation.

Run: pytest P:/.data/wiki/scripts/test_index_skills_state.py -v

Covers:
  - Module imports cleanly
  - Config parsers load correct data from real config files
  - compute_plugin_state() returns correct (grok, claude) state across
    all scope/plugin/host combinations
  - scan_scope() annotates entries with state
  - End-to-end: script runs and produces catalog with G/C columns
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("P:/.data/wiki/scripts/index_skills.py")


@pytest.fixture(scope="module")
def module():
    """Load index_skills.py as a module (it has no package)."""
    spec = importlib.util.spec_from_file_location("index_skills", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --- Module structure ---

def test_module_imports(module):
    assert hasattr(module, "SCOPES")
    assert hasattr(module, "CLAUDE_SCOPE_SOURCE")
    assert hasattr(module, "load_grok_disabled")
    assert hasattr(module, "load_claude_enabled")
    assert hasattr(module, "compute_plugin_state")
    assert hasattr(module, "scan_scope")


def test_scope_source_mapping_covers_claude_scopes(module):
    """Every claude-* scope with plugin_rel should be in CLAUDE_SCOPE_SOURCE."""
    claude_scopes = [s for s in module.SCOPES if s[0].startswith("claude-") and s[2]]
    for scope_name, _, _ in claude_scopes:
        assert scope_name in module.CLAUDE_SCOPE_SOURCE, f"missing source mapping for {scope_name}"


# --- Config parsers (against real config files) ---

def test_load_grok_disabled_returns_set(module):
    result = module.load_grok_disabled()
    assert isinstance(result, set)
    # cc-skills-media is known to be disabled per config inspection
    assert "cc-skills-media" in result


def test_load_claude_enabled_returns_dict(module):
    result = module.load_claude_enabled()
    assert isinstance(result, dict)
    # cc-skills-media@local is known to be enabled per settings.json
    assert result.get("cc-skills-media@local") is True


# --- compute_plugin_state (opt-out Grok, opt-in Claude) ---

def test_state_direct_grok_skill(module):
    """Direct skill at grok-agents (no plugin) → enabled for Grok, n/a for Claude."""
    g, c = module.compute_plugin_state("grok-agents", None, set(), {})
    assert (g, c) == ("✓", "—")


def test_state_direct_claude_skill(module):
    """Direct skill at claude-user (no plugin) → n/a for Grok, enabled for Claude."""
    g, c = module.compute_plugin_state("claude-user", None, set(), {})
    assert (g, c) == ("—", "✓")


def test_state_codex_scope_both_na(module):
    """Codex scope → n/a for both (we don't track Codex plugin state)."""
    g, c = module.compute_plugin_state("codex-user", None, set(), {})
    assert (g, c) == ("—", "—")


def test_state_grok_plugin_enabled_when_not_in_disabled(module):
    """Grok: plugin absent from disabled-list = enabled."""
    g, c = module.compute_plugin_state("marketplace", "some-plugin", set(), {})
    assert g == "✓"


def test_state_grok_plugin_disabled_when_in_disabled(module):
    """Grok: plugin in disabled-list = disabled."""
    g, c = module.compute_plugin_state("marketplace", "cc-skills-media",
                                        {"cc-skills-media"}, {})
    assert g == "✗"


def test_state_claude_plugin_enabled_when_in_enabled(module):
    """Claude: plugin@source in enabledPlugins with true = enabled."""
    ce = {"cc-skills-media@local": True}
    g, c = module.compute_plugin_state("claude-cache-local", "cc-skills-media/1.0.7",
                                        set(), ce)
    assert c == "✓"


def test_state_claude_plugin_disabled_when_absent_from_enabled(module):
    """Claude: plugin@source absent from enabledPlugins = disabled (opt-in)."""
    g, c = module.compute_plugin_state("claude-cache-local", "cc-skills-media/1.0.7",
                                        set(), {"other-plugin@local": True})
    assert c == "✗"


def test_state_claude_plugin_disabled_when_false(module):
    """Claude: plugin@source explicitly false = disabled."""
    ce = {"cc-skills-media@local": False}
    g, c = module.compute_plugin_state("claude-cache-local", "cc-skills-media",
                                        set(), ce)
    assert c == "✗"


def test_state_claude_unknown_scope_is_na(module):
    """Claude scope not in CLAUDE_SCOPE_SOURCE → n/a (we can't compute)."""
    g, c = module.compute_plugin_state("claude-unknown-scope", "plugin",
                                        set(), {"plugin@x": True})
    assert c == "—"


def test_state_marketplace_scope_tracked_for_both(module):
    """marketplace scope is checked for both hosts."""
    # In both disabled and not enabled → disabled for both
    g, c = module.compute_plugin_state("marketplace", "x", {"x"}, {})
    assert g == "✗"
    assert c == "✗"


def test_state_plugin_name_strips_version_hash(module):
    """Bare plugin name extracted before lookup (cc-skills-media/1.0.7 → cc-skills-media)."""
    g, c = module.compute_plugin_state("claude-cache-local", "cc-skills-media/1.0.7",
                                        {"cc-skills-media"}, {"cc-skills-media@local": True})
    assert g == "—"  # claude scope is n/a for grok
    assert c == "✓"


# --- Integration: scan_scope annotates entries ---

def test_scan_scope_annotates_state(module, tmp_path):
    """scan_scope should populate grok_state/claude_state on each SkillEntry."""
    # Build a minimal fake scope
    fake_root = tmp_path / "fake-skill-root"
    fake_skill = fake_root / "myplugin" / "skills" / "myskill"
    fake_skill.mkdir(parents=True)
    (fake_skill / "SKILL.md").write_text(
        "---\nname: myskill\ndescription: test skill\n---\n# myskill\n", encoding="utf-8")

    entries = module.scan_scope(
        scope="claude-cache-local",
        root=fake_root,
        plugin_rel="skills",
        grok_disabled={"myplugin"},
        claude_enabled={"myplugin@local": True})
    assert len(entries) == 1
    e = entries[0]
    assert e.name == "myskill"
    assert e.plugin == "myplugin"
    assert e.grok_state == "—"  # claude scope, n/a for grok
    assert e.claude_state == "✓"


# --- End-to-end: running the script produces expected output ---

def test_script_runs_and_produces_catalog_with_state_columns():
    """End-to-end: invoking the script regenerates catalog with G/C columns."""
    r = subprocess.run(
        ["python", str(SCRIPT)],
        capture_output=True, text=True, timeout=120, encoding="utf-8")
    assert r.returncode == 0, f"script failed: {r.stderr[:500]}"
    # Catalog exists and has the new column header
    catalog = Path("P:/.data/wiki/concepts/skill-catalog.md")
    assert catalog.exists()
    text = catalog.read_text(encoding="utf-8")
    assert "| Skill | G | C | Description" in text, "catalog table header missing G/C columns"
    assert "**G / C columns:**" in text, "legend missing"


def test_catalog_has_correct_nlm_to_wiki_states():
    """The nlm-to-wiki entries in catalog should reflect known config state."""
    catalog = Path("P:/.data/wiki/concepts/skill-catalog.md")
    text = catalog.read_text(encoding="utf-8")
    # Find the three nlm-to-wiki rows
    rows = [line for line in text.splitlines() if "nlm-to-wiki" in line and line.startswith("| **")]
    assert len(rows) >= 3, f"expected ≥3 nlm-to-wiki rows, got {len(rows)}"
    # v2 at .agents/skills: G=✓ C=—
    assert any("✓" in r.split("|")[2] and "—" in r.split("|")[3] and ".agents" in r for r in rows), \
        "missing v2 row with G=✓ C=—"
    # Claude cache: G=— C=✓
    assert any("—" in r.split("|")[2] and "✓" in r.split("|")[3] and "cache" in r for r in rows), \
        "missing cache row with G=— C=✓"
    # Marketplace: G=✗ C=✓ (cc-skills-media disabled in Grok, enabled in Claude)
    assert any("✗" in r.split("|")[2] and "✓" in r.split("|")[3] and "marketplace" in r.replace("…", "") for r in rows), \
        "missing marketplace row with G=✗ C=✓"


def test_stubs_have_enabled_state_frontmatter():
    """Stub files should have grok_enabled/claude_enabled frontmatter fields."""
    stubs_dir = Path("P:/.data/wiki/sources/skills")
    # Sample one direct skill and one plugin-sourced skill
    samples = [
        ("grok-agents-nlm-to-wiki.md", "true", "n/a"),       # v2: Grok ✓, Claude —
        ("marketplace-cc-skills-media-nlm-to-wiki.md", "false", "true"),  # disabled in G, enabled in C
    ]
    for filename, exp_grok, exp_claude in samples:
        stub = stubs_dir / filename
        assert stub.exists(), f"missing stub: {filename}"
        content = stub.read_text(encoding="utf-8")
        assert f"grok_enabled: {exp_grok}" in content, \
            f"{filename}: expected grok_enabled: {exp_grok}"
        assert f"claude_enabled: {exp_claude}" in content, \
            f"{filename}: expected claude_enabled: {exp_claude}"
