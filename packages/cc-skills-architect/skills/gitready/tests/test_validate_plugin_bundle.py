"""Tests for validate_plugin_bundle.py"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.validate_plugin_bundle import (
    check_manifest,
    check_paths,
    check_bundle,
    smoke_test,
)


class TestCheckManifest:
    def test_missing_manifest(self, tmp_path):
        ok, errors = check_manifest(tmp_path)
        assert not ok
        assert "Missing .claude-plugin/plugin.json" in errors

    def test_manifest_missing_name(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text("{}")
        ok, errors = check_manifest(tmp_path)
        assert not ok
        assert "missing required 'name' field" in errors[0]

    def test_manifest_minimal_passes(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        ok, errors = check_manifest(tmp_path)
        assert ok
        assert errors == []

    def test_manifest_invalid_json(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text("not json")
        ok, errors = check_manifest(tmp_path)
        assert not ok
        assert "Invalid JSON" in errors[0]


class TestCheckPaths:
    def test_no_hardcoded_paths(self, tmp_path):
        (tmp_path / "test.py").write_text('path = "${CLAUDE_PLUGIN_ROOT}/scripts"')
        ok, errors = check_paths(tmp_path)
        assert ok
        assert errors == []

    def test_detects_p_drive(self, tmp_path):
        (tmp_path / "test.py").write_text('path = "P:\\\\packages\\test"')
        ok, errors = check_paths(tmp_path, scope="repo")
        assert not ok
        assert any("P:" in e for e in errors)

    def test_detects_c_drive(self, tmp_path):
        (tmp_path / "test.py").write_text('path = "C:\\\\Users\\test"')
        ok, errors = check_paths(tmp_path, scope="repo")
        assert not ok
        assert any("C:" in e for e in errors)

    def test_detects_users_home(self, tmp_path):
        (tmp_path / "test.py").write_text('path = "/Users/brsth/plugin"')
        ok, errors = check_paths(tmp_path, scope="repo")
        assert not ok
        assert any("/Users/" in e for e in errors)

    def test_excludes_pycache(self, tmp_path):
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.pyc").write_text('path = "P:\\\\packages"')
        ok, errors = check_paths(tmp_path)
        assert ok
        assert errors == []

    def test_bundle_scope_excludes_internal_scripts(self, tmp_path):
        # Internal script with hardcoded path should be ignored in bundle scope
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "create_github_repo.py").write_text('path = "P:\\\\packages\\test"')
        ok, errors = check_paths(tmp_path, scope="bundle")
        assert ok
        assert errors == []

    def test_repo_scope_includes_internal_scripts(self, tmp_path):
        # Internal script with hardcoded path should be flagged in repo scope
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "create_github_repo.py").write_text('path = "P:\\\\packages\\test"')
        ok, errors = check_paths(tmp_path, scope="repo")
        assert not ok
        assert any("create_github_repo.py" in e for e in errors)


class TestCheckBundle:
    def test_missing_readme(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        ok, errors = check_bundle(tmp_path)
        assert not ok
        assert any("README.md" in e for e in errors)

    def test_missing_license(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        (tmp_path / "README.md").write_text("# Test")
        ok, errors = check_bundle(tmp_path)
        assert not ok
        assert any("LICENSE" in e for e in errors)

    def test_passes_with_required_files(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "LICENSE").write_text("MIT")
        ok, errors = check_bundle(tmp_path)
        assert ok
        assert errors == []

    def test_detects_pyproject_toml(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "LICENSE").write_text("MIT")
        (tmp_path / "pyproject.toml").write_text("[project]")
        ok, errors = check_bundle(tmp_path)
        assert not ok
        assert any("pyproject.toml" in e for e in errors)

    def test_detects_core_directory(self, tmp_path):
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "LICENSE").write_text("MIT")
        (tmp_path / "core").mkdir()
        ok, errors = check_bundle(tmp_path)
        assert not ok
        assert any("core/" in e for e in errors)


class TestSmokeTest:
    def test_no_scripts_dir_passes(self, tmp_path):
        ok, errors = smoke_test(tmp_path)
        assert ok

    def test_init_py_compiles(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "__init__.py").write_text("# empty")
        ok, errors = smoke_test(tmp_path)
        assert ok

    def test_syntax_error_fails(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "__init__.py").write_text("def ")
        ok, errors = smoke_test(tmp_path)
        assert not ok
        assert errors[0] != ""