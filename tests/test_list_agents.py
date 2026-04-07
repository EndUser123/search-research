"""Tests for list_agents.py"""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from list_agents import (
    extract_frontmatter,
    scan_user_agents,
    scan_plugin_agents,
    BUILTIN_AGENTS,
    main,
)


class TestExtractFrontmatter:
    def test_parses_name_and_description(self):
        text = "---" + chr(10) + "name: test-agent" + chr(10) + "description: A test agent" + chr(10) + "---" + chr(10) + "# Body"
        fm = extract_frontmatter(text)
        assert fm["name"] == "test-agent"
        assert fm["description"] == "A test agent"

    def test_returns_empty_dict_for_no_frontmatter(self):
        assert extract_frontmatter("No frontmatter here") == {}

    def test_handles_missing_description(self):
        text = "---" + chr(10) + "name: no-desc" + chr(10) + "---" + chr(10) + "# Body"
        fm = extract_frontmatter(text)
        assert fm["name"] == "no-desc"
        # Missing key returns None from dict.get()
        assert fm.get("description") is None


class TestScanUserAgents:
    def test_finds_agents_in_directory(self, tmp_path):
        # Name/subagent_type come from filename stem; description from frontmatter
        agent_file = tmp_path / "my_agent.md"
        agent_file.write_text("---" + chr(10) + "description: Test agent desc" + chr(10) + "---" + chr(10) + "# Test")
        agents = scan_user_agents(tmp_path)
        assert len(agents) == 1
        assert agents[0]["name"] == "my_agent"
        assert agents[0]["subagent_type"] == "my_agent"
        assert agents[0]["description"] == "Test agent desc"
        assert agents[0]["source_type"] == "user"

    def test_skips_readme_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("---" + chr(10) + "name: readme" + chr(10) + "description: skip me" + chr(10) + "---" + chr(10))
        (tmp_path / "_README.md").write_text("---" + chr(10) + "name: _README" + chr(10) + "description: skip me" + chr(10) + "---" + chr(10))
        agents = scan_user_agents(tmp_path)
        assert len(agents) == 0

    def test_returns_empty_for_nonexistent_dir(self):
        agents = scan_user_agents(Path("/nonexistent/path"))
        assert agents == []


class TestBuiltinAgents:
    def test_builtin_agents_exist(self):
        assert len(BUILTIN_AGENTS) > 0
        names = [a["name"] for a in BUILTIN_AGENTS]
        assert "general-purpose" in names
        assert "Explore" in names


class TestMainOutput:
    def test_main_produces_valid_json(self, capsys):
        main([])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert "total" in data
        assert "by_source" in data
        assert "agents" in data
        assert data["total"] == len(data["agents"])

    def test_names_flag_prints_one_per_line(self, capsys):
        main(["--names"])
        captured = capsys.readouterr().out
        lines = captured.strip().splitlines()
        assert len(lines) > 0
        for line in lines:
            assert " " not in line

    def test_filter_reduces_results(self, capsys):
        main(["--filter", "code"])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert all(
            "code" in a["name"].lower() or "code" in a["description"].lower()
            for a in data["agents"]
        )

    def test_source_filter_works(self, capsys):
        main(["--source", "builtin"])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert all(a["source_type"] == "builtin" for a in data["agents"])
