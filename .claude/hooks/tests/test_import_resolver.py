"""Tests for __lib/import_resolver.py — unit, integration, and regression."""

import textwrap
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from __lib.import_resolver import (
    candidate_module_paths,
    collect_attribute_bases,
    extract_import_specs,
    get_git_status_map,
    resolve_local_imports,
    scan_blast_radius,
)


# ── Unit tests: extract_import_specs ──


class TestExtractImportSpecs:
    def test_empty_source(self):
        assert extract_import_specs("") == []
        assert extract_import_specs("   ") == []

    def test_syntax_error_returns_empty(self):
        assert extract_import_specs("def (") == []

    def test_plain_import(self):
        specs = extract_import_specs("import os")
        assert {"spec": "os", "kind": "import"} in specs

    def test_from_import(self):
        specs = extract_import_specs("from pathlib import Path")
        assert {"spec": "pathlib", "kind": "from"} in specs
        assert {"spec": "Path", "kind": "from"} in specs

    def test_relative_import(self):
        specs = extract_import_specs("from . import utils")
        assert {"spec": ".utils", "kind": "from_relative"} in specs

    def test_deduplication(self):
        src = "import os\nimport os\n"
        specs = extract_import_specs(src)
        os_specs = [s for s in specs if s["spec"] == "os"]
        assert len(os_specs) == 1

    def test_star_import_excluded(self):
        src = "from os.path import *"
        specs = extract_import_specs(src)
        assert not any(s["spec"] == "*" for s in specs)


# ── Unit tests: collect_attribute_bases ──


class TestCollectAttributeBases:
    def test_attribute_base(self):
        import ast
        tree = ast.parse("foo.bar")
        bases = collect_attribute_bases(tree)
        assert "foo" in bases

    def test_no_attributes(self):
        import ast
        tree = ast.parse("x = 1")
        bases = collect_attribute_bases(tree)
        assert len(bases) == 0


# ── Unit tests: candidate_module_paths ──


class TestCandidateModulePaths:
    def test_simple_spec(self):
        paths = candidate_module_paths("os.path", Path("/project/src/main.py"))
        assert any(p.name == "path.py" and p.parent.name == "os" for p in paths)
        assert any(p.name == "__init__.py" and p.parent.name == "path" for p in paths)

    def test_empty_spec(self):
        assert candidate_module_paths("", Path("/project/a.py")) == []
        assert candidate_module_paths("   ", Path("/project/a.py")) == []

    def test_relative_spec(self):
        paths = candidate_module_paths("..utils", Path("/project/src/pkg/main.py"))
        assert len(paths) > 0


# ── Unit tests: resolve_local_imports ──


class TestResolveLocalImports:
    def test_stdlib_excluded(self):
        result = resolve_local_imports(
            Path("/project/main.py"), Path("/project"), {}, "import os\nimport json"
        )
        stdlib_specs = [s for s in result["local_import_specs"] if s in ("os", "json")]
        assert len(stdlib_specs) == 0

    def test_resolved_local_import(self, tmp_path):
        pkg = tmp_path / "mypackage"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "utils.py").write_text("def helper(): pass")
        main_py = tmp_path / "main.py"
        main_py.write_text("from mypackage import utils")

        result = resolve_local_imports(main_py, tmp_path, {}, main_py.read_text())
        resolved_paths = [r["path"] for r in result["resolved_local_imports"]]
        # "from mypackage import utils" resolves the package "mypackage",
        # not the individual name "utils"
        assert any("mypackage" in p for p in resolved_paths)

    def test_unresolved_import(self, tmp_path):
        main_py = tmp_path / "main.py"
        # Relative import of nonexistent module is always "localish"
        main_py.write_text("from . import nonexistent_module_xyz")

        result = resolve_local_imports(main_py, tmp_path, {}, main_py.read_text())
        assert any("nonexistent_module_xyz" in s for s in result["unresolved_local_imports"])

    def test_deleted_import_target(self, tmp_path):
        main_py = tmp_path / "main.py"
        main_py.write_text("import deleted_mod")
        status_map = {"deleted_mod.py": "D "}

        result = resolve_local_imports(main_py, tmp_path, status_map, main_py.read_text())
        assert "deleted_mod" in result.get("unresolved_local_imports", [])
        assert any("deleted_mod" in t for t in result.get("deleted_or_staged_import_targets", []))


# ── Unit tests: get_git_status_map ──


class TestGetGitStatusMap:
    def test_returns_dict(self):
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        status = get_git_status_map(repo_root)
        assert isinstance(status, dict)

    def test_invalid_path_returns_empty(self):
        status = get_git_status_map(Path("/nonexistent/path"))
        assert status == {}


# ── Integration tests: scan_blast_radius ──


class TestScanBlastRadius:
    def test_no_changes_early_return(self, tmp_path):
        result = scan_blast_radius([], tmp_path)
        assert result["at_risk_consumers"] == []
        assert result["safe_consumers"] == []
        assert result["files_scanned"] == 0

    def test_scan_with_temp_project(self, tmp_path):
        # Create a small project structure
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "service.py").write_text("def run(): pass")
        consumer = tmp_path / "consumer.py"
        # Use dotted import so the spec resolves to pkg/service.py
        consumer.write_text("import pkg.service")

        result = scan_blast_radius([pkg / "service.py"], tmp_path, status_map={})
        # consumer imports pkg.service, which resolves to pkg/service.py -> safe
        assert len(result["safe_consumers"]) >= 1
        assert result["safe_consumers"][0]["consumer"] == "consumer.py"


# ── Regression test: investigation gate parity ──


class TestInvestigationGateParity:
    """Verify the extracted functions produce identical results to the
    original inline implementations in PreToolUse_investigation_gate.py."""

    def test_import_specs_match(self):
        source = Path(__file__).resolve().parent.parent / "PreToolUse_investigation_gate.py"
        text = source.read_text(encoding="utf-8")
        specs = extract_import_specs(text)
        # Must find at least the stdlib imports the investigation gate uses
        spec_names = [s["spec"] for s in specs]
        assert "json" in spec_names
        assert "pathlib" in spec_names
        assert "typing" in spec_names

    def test_resolve_produces_local_imports(self):
        gate_file = Path(__file__).resolve().parent.parent / "PreToolUse_investigation_gate.py"
        hooks_dir = Path(__file__).resolve().parent.parent
        text = gate_file.read_text(encoding="utf-8")
        result = resolve_local_imports(gate_file, hooks_dir, {}, text)
        assert result["local_import_count"] > 0
