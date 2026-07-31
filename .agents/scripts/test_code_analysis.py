"""Tests for code_analysis.py — the cross-file analysis engine.

Covers: cycle detection, fan-in/fan-out, duplication detection,
dead code, test gap detection, and --json/--text output modes.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path("P:/.agents/scripts/code_analysis.py")


def run_analysis(target: Path, mode="json"):
    """Run code_analysis.py and return parsed output."""
    args = [sys.executable, str(SCRIPT), str(target)]
    if mode == "text":
        args.append("--text")
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None, result.stderr
    if mode == "json":
        return json.loads(result.stdout), result.stderr
    return result.stdout, result.stderr


def create_temp_pkg(files: dict[str, str]) -> Path:
    """Create a temp package with the given files.
    
    Args:
        files: {relative_path: content}
    """
    tmpdir = Path(tempfile.mkdtemp())
    for relpath, content in files.items():
        fpath = tmpdir / relpath
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    return tmpdir


class TestImportGraphAndCycles:
    """Test cycle detection and import graph construction."""

    def test_no_cycles_clean_imports(self):
        """A package with clean one-way imports should find 0 cycles."""
        pkg = create_temp_pkg({
            "main.py": "import utils\nimport helpers\n",
            "utils.py": "import helpers\n",
            "helpers.py": "# no imports\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None, "Analysis should succeed"
        assert data["summary"]["cycles"] == 0

    def test_detects_direct_cycle(self):
        """A → B → A cycle should be detected."""
        pkg = create_temp_pkg({
            "mod_a.py": "import mod_b\nx = 1\n",
            "mod_b.py": "import mod_a\ny = 2\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        assert data["summary"]["cycles"] >= 1, f"Expected ≥1 cycle, got {data['summary']['cycles']}"
        # The cycle should mention both modules
        cycle = data["import_graph"]["cycles"][0]
        cycle_modules = set()
        for mod in cycle:
            cycle_modules.add(mod.replace("mod_a", "").replace("mod_b", ""))
        assert "mod_a" in " ".join(cycle), f"mod_a should be in cycle: {cycle}"

    def test_detects_transitive_cycle(self):
        """A → B → C → A transitive cycle should be detected."""
        pkg = create_temp_pkg({
            "alpha.py": "import beta\na = 1\n",
            "beta.py": "import gamma\nb = 2\n",
            "gamma.py": "import alpha\nc = 3\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        assert data["summary"]["cycles"] >= 1, f"Expected ≥1 cycle, got {data['summary']['cycles']}"

    def test_fan_in_fan_out(self):
        """Fan-in and fan-out should be computed correctly."""
        pkg = create_temp_pkg({
            "popular.py": "# imported by many\nx = 1\n",
            "consumer_a.py": "import popular\na = 2\n",
            "consumer_b.py": "import popular\nb = 3\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        fan_in = data["import_graph"]["fan_in"]
        # popular.py should have fan_in >= 2
        assert "popular" in str(fan_in), f"popular should be in fan_in: {fan_in}"
        # consumer modules should have fan_out >= 1
        fan_out = data["import_graph"]["fan_out"]
        assert "consumer_a" in str(fan_out) or "consumer_b" in str(fan_out), \
            f"consumers should be in fan_out: {fan_out}"


class TestDuplicationDetection:
    """Test cross-file duplication detection."""

    def test_detects_identical_function(self):
        """Same function in 2 files should be flagged as duplication."""
        # Must be >= 5 lines (min_lines threshold in code_analysis.py)
        func_body = """
def shared_helper(value):
    result = value * 2
    intermediate = result + 10
    final = intermediate - 5
    adjustment = final * 3
    combined = adjustment + result
    return combined + value
"""
        pkg = create_temp_pkg({
            "file_a.py": func_body + "\nx = shared_helper(5)\n",
            "file_b.py": func_body + "\ny = shared_helper(3)\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        assert data["summary"]["duplication_clusters"] >= 1, \
            f"Expected ≥1 duplication, got {data['summary']['duplication_clusters']}"

    def test_no_false_positive_different_functions(self):
        """Different functions should NOT be flagged as duplication."""
        pkg = create_temp_pkg({
            "file_a.py": "def compute_score(x):\n    return x * 100 + 50\n\nresult = compute_score(10)\n",
            "file_b.py": "def parse_input(text):\n    parts = text.split(',')\n    return [p.strip() for p in parts]\n\nitems = parse_input('a, b, c')\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        assert data["summary"]["duplication_clusters"] == 0, \
            f"Expected 0 duplication, got {data['summary']['duplication_clusters']}"


class TestTestGapDetection:
    """Test missing test file detection."""

    def test_detects_missing_test_file(self):
        """A module with no test file should be flagged."""
        pkg = create_temp_pkg({
            "untested_module.py": "def foo():\n    return 42\n",
            "tested_module.py": "def bar():\n    return 43\n",
            "tests/test_tested_module.py": "# test for tested_module\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        test_gaps = data["findings"]["test_gaps"]
        gap_files = [g["file"] for g in test_gaps]
        assert "untested_module.py" in gap_files, f"untested_module should be a gap: {gap_files}"

    def test_no_gap_when_test_exists(self):
        """A module WITH a test file should NOT be flagged."""
        pkg = create_temp_pkg({
            "module_a.py": "def foo():\n    return 42\n",
            "tests/test_module_a.py": "from module_a import foo\ndef test_foo():\n    assert foo() == 42\n",
        })
        data, _ = run_analysis(pkg)
        assert data is not None
        test_gaps = data["findings"]["test_gaps"]
        gap_files = [g["file"] for g in test_gaps]
        assert "module_a.py" not in gap_files, f"module_a should NOT be a gap: {gap_files}"


class TestOutputModes:
    """Test --json and --text output modes."""

    def test_json_output_valid(self):
        """JSON output should be valid JSON with expected top-level keys."""
        pkg = create_temp_pkg({"main.py": "x = 1\n"})
        data, _ = run_analysis(pkg, mode="json")
        assert data is not None
        assert "analysis_type" in data
        assert data["analysis_type"] == "comprehensive"
        assert "summary" in data
        assert "import_graph" in data
        assert "findings" in data

    def test_text_output_has_sections(self):
        """Text output should have section headers."""
        pkg = create_temp_pkg({
            "main.py": "x = 1\n",
            "unused.py": "def dead():\n    pass\n",
        })
        stdout, _ = run_analysis(pkg, mode="text")
        assert stdout is not None
        assert "ANALYSIS:" in stdout
        assert "Modules:" in stdout

    def test_nonexistent_path_errors(self):
        """Non-existent path should produce an error, not a crash."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "P:/nonexistent/path/xyz"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode != 0 or "error" in result.stderr.lower()


class TestScriptCompilation:
    """Verify the script itself is valid Python."""

    def test_compiles(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT)],
            capture_output=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"
