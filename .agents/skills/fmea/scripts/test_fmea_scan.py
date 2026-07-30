"""Tests for fmea_scan.py — AST-based FMEA scanner."""
import sys
import ast
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fmea_scan import BoundaryVisitor, scan_file, scan_pipeline, generate_failure_modes, format_table


def test_visitor_finds_glob():
    """BoundaryVisitor detects rglob/glob calls."""
    source = "from pathlib import Path\nfor f in Path('.').rglob('*.py'):\n    pass\n"
    tree = ast.parse(source)
    v = BoundaryVisitor("test.py")
    v.visit(tree)
    types = [b.boundary_type for b in v.boundaries]
    assert "glob" in types, f"Expected glob in {types}"


def test_visitor_finds_subprocess():
    """BoundaryVisitor detects subprocess.run calls."""
    source = "import subprocess\nsubprocess.run(['ls'], capture_output=True)\n"
    tree = ast.parse(source)
    v = BoundaryVisitor("test.py")
    v.visit(tree)
    types = [b.boundary_type for b in v.boundaries]
    assert "subprocess" in types, f"Expected subprocess in {types}"


def test_visitor_finds_file_read():
    """BoundaryVisitor detects read_text() calls."""
    source = "from pathlib import Path\ndata = Path('file.txt').read_text()\n"
    tree = ast.parse(source)
    v = BoundaryVisitor("test.py")
    v.visit(tree)
    types = [b.boundary_type for b in v.boundaries]
    assert "file_read" in types, f"Expected file_read in {types}"


def test_visitor_finds_file_write():
    """BoundaryVisitor detects write_text() calls."""
    source = "from pathlib import Path\nPath('out.txt').write_text('data')\n"
    tree = ast.parse(source)
    v = BoundaryVisitor("test.py")
    v.visit(tree)
    types = [b.boundary_type for b in v.boundaries]
    assert "file_write" in types, f"Expected file_write in {types}"


def test_visitor_finds_shared_dir():
    """BoundaryVisitor detects /tmp/ path patterns."""
    source = "from pathlib import Path\nf = Path('P:/tmp/data.json')\n"
    tree = ast.parse(source)
    v = BoundaryVisitor("test.py")
    v.visit(tree)
    types = [b.boundary_type for b in v.boundaries]
    assert "shared_dir" in types, f"Expected shared_dir in {types}"


def test_scan_file_returns_modes():
    """scan_file returns FailureMode objects with RPN."""
    modes = scan_file(Path(__file__).parent / "fmea_scan.py")
    assert len(modes) > 0
    assert all(m.rpn > 0 for m in modes)
    assert all(m.rpn == m.severity * m.occurrence * m.detection for m in modes)


def test_scan_pipeline_sorts_by_rpn():
    """scan_pipeline sorts modes by RPN descending."""
    modes = scan_pipeline(Path(__file__).parent)
    assert len(modes) > 0
    rpns = [m.rpn for m in modes]
    assert rpns == sorted(rpns, reverse=True), "Modes not sorted by RPN descending"


def test_format_table_handles_empty():
    """format_table handles empty list gracefully."""
    result = format_table([])
    assert "clean" in result.lower() or "no" in result.lower()


def test_format_table_produces_markdown():
    """format_table produces markdown table format."""
    modes = scan_file(Path(__file__).parent / "fmea_scan.py")
    result = format_table(modes)
    assert "| Component |" in result
    assert "RPN" in result


def test_high_rpn_boundary_is_glob():
    """The highest-RPN boundary type should be glob (contamination risk)."""
    modes = scan_file(Path(__file__).parent / "fmea_scan.py")
    top = max(modes, key=lambda m: m.rpn)
    assert top.rpn >= 400, f"Top RPN {top.rpn} should be >= 400"
    assert top.boundary.boundary_type == "glob", f"Top type should be glob, got {top.boundary.boundary_type}"
