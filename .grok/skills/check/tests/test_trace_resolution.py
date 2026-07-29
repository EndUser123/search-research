"""Test import-aware resolution in trace_check."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "__lib" / "trace_check.py"


def _run(args):
    r = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, timeout=10,
    )
    return r.returncode, r.stdout.strip()


def test_external_method_confirmed_defined(tmp_path):
    """When the external base IS installed and HAS the method,
    the finding should be SUPPRESSED (resolution=defined)."""
    f = tmp_path / "test.py"
    # dict has .keys() — trace_check should suppress this
    f.write_text("""
class MyDict(dict):
    def run(self):
        self.keys()
""", encoding="utf-8")
    out = tmp_path / "result.json"
    code, _ = _run(["--paths", str(f), "--output", str(out)])
    result = json.loads(out.read_text(encoding="utf-8"))
    # keys() is defined on dict — should NOT be a finding
    assert result["finding_count"] == 0


def test_external_method_confirmed_undefined(tmp_path):
    """When the external base IS installed but does NOT have the method,
    the finding should be confidence=high (confirmed bug)."""
    f = tmp_path / "test.py"
    # dict does NOT have ._nonexistent_method()
    f.write_text("""
class MyDict(dict):
    def run(self):
        self._nonexistent_method()
""", encoding="utf-8")
    out = tmp_path / "result.json"
    code, _ = _run(["--paths", str(f), "--output", str(out)])
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["finding_count"] == 1
    finding = result["findings"][0]
    assert finding["confidence"] == "high"
    assert finding["resolution"] == "undefined"


def test_external_method_unresolvable_package(tmp_path):
    """When the external base package is NOT installed,
    the finding should be confidence=low (advisory)."""
    f = tmp_path / "test.py"
    f.write_text("""
from nonexistent_pkg import SomeBase

class MyClass(SomeBase):
    def run(self):
        self._maybe_inherited()
""", encoding="utf-8")
    out = tmp_path / "result.json"
    code, _ = _run(["--paths", str(f), "--output", str(out)])
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["finding_count"] == 1
    finding = result["findings"][0]
    assert finding["confidence"] == "low"
    assert finding["resolution"] == "unresolved"


def test_same_file_inheritance_no_external_resolution(tmp_path):
    """Same-file inheritance should not trigger import resolution at all."""
    f = tmp_path / "test.py"
    f.write_text("""
class Base:
    def _exists(self):
        pass

class Child(Base):
    def run(self):
        self._exists()
        self._missing()
""", encoding="utf-8")
    out = tmp_path / "result.json"
    code, _ = _run(["--paths", str(f), "--output", str(out)])
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["finding_count"] == 1
    finding = result["findings"][0]
    assert finding["confidence"] == "high"
    assert "_missing" in finding["method"]
