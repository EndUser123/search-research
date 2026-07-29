"""Tests for trace_check.py — definition completeness check."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "__lib" / "trace_check.py"


def _run(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, timeout=10,
    )
    return r.returncode, r.stdout.strip()


def test_clean_file(tmp_path):
    """File with all method calls defined → no findings."""
    f = tmp_path / "clean.py"
    f.write_text("""
class App:
    def run(self):
        self._setup()
        self._teardown()

    def _setup(self):
        pass

    def _teardown(self):
        pass
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert code == 0
    assert "clean" in stdout


def test_missing_method(tmp_path):
    """File calling self._missing() where method is not defined → 1 finding."""
    f = tmp_path / "broken.py"
    f.write_text("""
class App:
    def run(self):
        self._existing()
        self._missing()  # this method doesn't exist

    def _existing(self):
        pass
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert code == 0  # advisory
    assert "1 called-but-undefined" in stdout
    assert "_missing" in stdout


def test_dunder_methods_skipped(tmp_path):
    """__init__, __str__ etc. are framework-provided — skip them."""
    f = tmp_path / "dunders.py"
    f.write_text("""
class App:
    def run(self):
        self.__str__()
        self.__repr__()
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert "clean" in stdout


def test_multiple_findings(tmp_path):
    """Multiple missing methods → multiple findings."""
    f = tmp_path / "multi.py"
    f.write_text("""
class App:
    def run(self):
        self._foo()
        self._bar()
        self._baz()
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert "3 called-but-undefined" in stdout


def test_output_json(tmp_path):
    """JSON output contains structured findings."""
    f = tmp_path / "broken.py"
    f.write_text("""
class App:
    def run(self):
        self._missing()
""", encoding="utf-8")
    out = tmp_path / "result.json"
    code, _ = _run(["--paths", str(f), "--output", str(out)])
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["finding_count"] == 1
    assert result["findings"][0]["method"] == "_missing"


def test_mark_row_scenario(tmp_path):
    """The exact _mark_row incident: 5 callers, 0 definitions."""
    f = tmp_path / "ksc.py"
    f.write_text("""
class KeepSmallerCopyApp:
    def _do_process_worker(self):
        self._mark_row("1", "DRY")
        self._mark_row("2", "OK")
        self._mark_row("3", "ERR")
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert "3 called-but-undefined" in stdout
    assert "_mark_row" in stdout


def test_inheritance_not_flagged(tmp_path):
    """Method defined on base class should NOT be flagged on subclass."""
    f = tmp_path / "inherit.py"
    f.write_text("""
class Base:
    def _helper(self):
        pass

class Child(Base):
    def run(self):
        self._helper()  # inherited from Base — should be OK
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert "clean" in stdout


def test_syntax_error_reported(tmp_path):
    """File with syntax error should produce a finding, not silent skip."""
    f = tmp_path / "broken.py"
    f.write_text("""
class App:
    def run(self):
        self._ok()
        def (  # syntax error
""", encoding="utf-8")
    code, stdout = _run(["--paths", str(f)])
    assert "SyntaxError" in stdout
