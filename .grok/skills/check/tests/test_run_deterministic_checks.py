"""Tests for run_deterministic_checks.py — the 9-layer orchestrator."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

SCRIPT = Path(__file__).parent.parent / "__lib" / "run_deterministic_checks.py"


def _import_module():
    """Import the module fresh (it's not a package)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_deterministic_checks", str(SCRIPT)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _import_module()


# === _run helper ===

def test_run_success(mod):
    """_run returns (exit_code, stdout, stderr) on success."""
    code, out, err = mod._run([sys.executable, "-c", "print('hello')"])
    assert code == 0
    assert "hello" in out


def test_run_failure(mod):
    """_run returns non-zero exit code on command failure."""
    code, out, err = mod._run([sys.executable, "-c", "import sys; sys.exit(1)"])
    assert code == 1


def test_run_missing_executable(mod):
    """_run returns (-1, '', '') when executable doesn't exist."""
    code, out, err = mod._run(["__nonexistent_tool_xyz__"])
    assert code == -1
    assert out == ""


def test_run_timeout(mod):
    """_run returns (-1, '', '') on timeout."""
    code, out, err = mod._run(
        [sys.executable, "-c", "import time; time.sleep(10)"], timeout=1
    )
    assert code == -1


# === _parse_json_safe ===

def test_parse_json_valid(mod):
    assert mod._parse_json_safe('{"key": "value"}') == {"key": "value"}


def test_parse_json_invalid(mod):
    assert mod._parse_json_safe("not json") is None


def test_parse_json_empty(mod):
    assert mod._parse_json_safe("") is None


def test_parse_json_none(mod):
    assert mod._parse_json_safe(None) is None


# === Empty py_files guards ===

def test_run_ruff_empty(mod):
    result = mod.run_ruff([])
    assert result["status"] == "skipped"


def test_run_pyright_empty(mod):
    result = mod.run_pyright([])
    assert result["status"] == "skipped"


def test_run_pylint_empty(mod):
    result = mod.run_pylint([])
    assert result["status"] == "skipped"


def test_run_trace_check_empty(mod):
    result = mod.run_trace_check([])
    assert result["status"] == "skipped"


def test_run_bandit_empty(mod):
    result = mod.run_bandit([])
    assert result["status"] == "skipped"


def test_run_radon_empty(mod):
    result = mod.run_radon([])
    assert result["status"] == "skipped"


def test_run_vulture_empty(mod, tmp_path):
    result = mod.run_vulture([], tmp_path)
    assert result["status"] == "skipped"


# === Tool not installed guards ===

def test_run_ruff_not_installed(mod):
    with patch("shutil.which", return_value=None):
        result = mod.run_ruff(["some_file.py"])
    assert result["status"] == "skipped"
    assert "ruff" in result["reason"]


def test_run_pylint_not_installed(mod):
    with patch("shutil.which", return_value=None):
        result = mod.run_pylint(["some_file.py"])
    assert result["status"] == "skipped"


def test_run_bandit_not_installed(mod):
    with patch("shutil.which", return_value=None):
        result = mod.run_bandit(["some_file.py"])
    assert result["status"] == "skipped"


# === pip-audit file detection ===

def test_pip_audit_no_requirements(mod):
    """pip-audit skips when no requirements file in scope."""
    result = mod.run_pip_audit(["some_code.py", "README.md"])
    assert result["status"] == "skipped"


def test_pip_audit_pyproject_precedence(mod, tmp_path):
    """pyproject.toml is preferred over requirements.txt."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='test'\n", encoding="utf-8")
    reqs = tmp_path / "requirements.txt"
    reqs.write_text("requests\n", encoding="utf-8")
    with patch("shutil.which", return_value="/fake/pip-audit"):
        with patch.object(mod, "_run", return_value=(0, '{"results": []}', "")):
            result = mod.run_pip_audit(
                [str(reqs), str(pyproject)]
            )
    # Should have been called with pyproject.toml (first in priority)
    # The mock _run returns fake clean output
    assert result.get("results") == []


# === diff-cover conditional ===

def test_diff_cover_no_coverage_xml(mod, tmp_path):
    """diff-cover skips when coverage.xml doesn't exist."""
    result = mod.run_diff_cover(tmp_path)
    assert result["status"] == "skipped"
    assert "coverage.xml" in result["reason"]


def test_diff_cover_not_installed(mod, tmp_path):
    """diff-cover skips when tool not installed."""
    cov = tmp_path / "packets" / "coverage.xml"
    cov.parent.mkdir(parents=True, exist_ok=True)
    cov.write_text("<coverage/>", encoding="utf-8")
    with patch("shutil.which", return_value=None):
        result = mod.run_diff_cover(tmp_path)
    assert result["status"] == "skipped"


# === Radon JSON parsing ===

def test_radon_json_parsing(mod):
    """radon -j output is parsed into structured hotspots."""
    fake_json = json.dumps({
        "/fake/file.py": [
            {"name": "complex_func", "complexity": 15, "rank": "C"},
            {"name": "simple_func", "complexity": 5, "rank": "A"},
        ]
    })
    with patch("shutil.which", return_value="/fake/radon"):
        with patch.object(mod, "_run", return_value=(0, fake_json, "")):
            result = mod.run_radon(["/fake/file.py"])
    assert result["hotspot_count"] == 1  # only complex_func is C+
    assert result["hotspots"][0]["name"] == "complex_func"
    assert result["hotspots"][0]["rank"] == "C"


# === trace_check exit code propagation ===

def test_trace_check_exit_code_propagated(mod):
    """If trace_check.py subprocess crashes, status should be 'error'."""
    script = mod._SKILL_LIB / "trace_check.py"
    with patch.object(mod, "_run", return_value=(1, "", "crash")):
        with patch("pathlib.Path.exists", return_value=True):
            result = mod.run_trace_check(["file.py"])
    assert result["status"] == "error"
    assert result["exit_code"] == 1


# === main() return code ===

def test_main_returns_zero_on_clean(mod, tmp_path):
    """main() returns 0 when no errors found."""
    with patch("shutil.which", return_value=None):
        # All tools will be skipped
        exit_code = mod.main([
            "--py-files", str(tmp_path / "fake.py"),
            "--run-dir", str(tmp_path),
        ])
    assert exit_code == 0


def test_main_creates_run_dir(mod, tmp_path):
    """main() creates run_dir if it doesn't exist."""
    new_dir = tmp_path / "new_run_dir"
    with patch("shutil.which", return_value=None):
        mod.main([
            "--py-files", str(tmp_path / "fake.py"),
            "--run-dir", str(new_dir),
        ])
    assert new_dir.exists()


# === Summary in JSON packet ===

def test_summary_in_packet(mod, tmp_path):
    """The merged JSON packet contains a summary section."""
    output = tmp_path / "result.json"
    with patch("shutil.which", return_value=None):
        mod.main([
            "--py-files", str(tmp_path / "fake.py"),
            "--run-dir", str(tmp_path),
            "--output", str(output),
        ])
    result = json.loads(output.read_text(encoding="utf-8"))
    assert "summary" in result
    assert "has_errors" in result["summary"]
    assert "bandit_medium_high" in result["summary"]
    assert "radon_count" in result["summary"]
    assert "vulture_count" in result["summary"]


# === Full packet structure ===

def test_packet_has_all_layer_keys(mod, tmp_path):
    """The merged packet contains all 9 layer keys."""
    output = tmp_path / "result.json"
    with patch("shutil.which", return_value=None):
        mod.main([
            "--py-files", str(tmp_path / "fake.py"),
            "--run-dir", str(tmp_path),
            "--output", str(output),
        ])
    result = json.loads(output.read_text(encoding="utf-8"))
    expected_keys = {
        "ruff", "pyright", "pylint", "trace_check",
        "bandit", "radon_advisory", "vulture_advisory",
        "pip_audit_advisory", "diff_cover_advisory",
    }
    assert expected_keys.issubset(result.keys())


def test_coverage_gap_detection(mod, tmp_path):
    """When a __lib/*.py has no tests/test_*.py, the packet flags it."""
    # Simulate: P:/fake_pkg/__lib/widget.py with no tests/test_widget.py
    fake_pkg = tmp_path / "fake_pkg"
    fake_lib = fake_pkg / "__lib"
    fake_lib.mkdir(parents=True)
    fake_file = fake_lib / "widget.py"
    fake_file.write_text("# fake", encoding="utf-8")

    output = tmp_path / "result.json"
    with patch("shutil.which", return_value=None):
        mod.main([
            "--py-files", str(fake_file),
            "--run-dir", str(tmp_path),
            "--output", str(output),
        ])
    result = json.loads(output.read_text(encoding="utf-8"))
    gaps = result.get("test_coverage_gaps", [])
    assert len(gaps) == 1
    assert "widget.py" in gaps[0]["message"]


def test_coverage_gap_none_when_test_exists(mod, tmp_path):
    """When tests/test_*.py exists, no gap is reported."""
    fake_pkg = tmp_path / "fake_pkg"
    fake_lib = fake_pkg / "__lib"
    fake_lib.mkdir(parents=True)
    fake_file = fake_lib / "widget.py"
    fake_file.write_text("# fake", encoding="utf-8")
    # Create the test file
    test_dir = fake_pkg / "tests"
    test_dir.mkdir()
    (test_dir / "test_widget.py").write_text("# test", encoding="utf-8")

    output = tmp_path / "result.json"
    with patch("shutil.which", return_value=None):
        mod.main([
            "--py-files", str(fake_file),
            "--run-dir", str(tmp_path),
            "--output", str(output),
        ])
    result = json.loads(output.read_text(encoding="utf-8"))
    gaps = result.get("test_coverage_gaps", [])
    assert len(gaps) == 0
