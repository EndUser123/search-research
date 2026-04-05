"""
Tests for doc_consistency analyzer.

Tests verify:
- Symbol signature comparison with documentation
- Code snippet validation in docs
- Documentation rot detection (outdated signatures, missing symbols)
- Structured findings with severity
"""

import tempfile
from pathlib import Path

from lib.analysis_unit.analyzers.doc_consistency import DocConsistencyAnalyzer


class TestDocConsistencyAnalyzer:
    """Test suite for DocConsistencyAnalyzer."""

    def test_analyzer_initialization(self):
        """Test analyzer can be initialized with manifest."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {"items": []},
            "symbol_graph": {"nodes": [], "edges": []},
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        analyzer = DocConsistencyAnalyzer(manifest)
        assert analyzer.manifest == manifest
        assert analyzer.findings == []

    def test_compare_symbol_signatures_with_docs(self):
        """Test comparing symbol signatures with documentation."""
        # Create a manifest with a function signature
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "utils.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-process_data",
                        "name": "process_data",
                        "type": "function",
                        "file": "utils.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        # Create a temporary Python file with the function
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "utils.py"
            test_file.write_text("""
def process_data(data: str, count: int) -> dict:
    '''Process the data.

    Args:
        data: The data string
        count: Number of items

    Returns:
        Processed data dictionary
    '''
    return {"data": data, "count": count}
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should not flag signature mismatch when docstring matches
            sig_findings = [f for f in findings if f["category"] == "signature_mismatch"]
            assert len(sig_findings) == 0

    def test_detect_outdated_signature_in_docs(self):
        """Test detection of outdated signatures in documentation."""
        # Create a manifest
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "calculator.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-add",
                        "name": "add",
                        "type": "function",
                        "file": "calculator.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        # Create a file with outdated docstring (wrong parameter name)
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "calculator.py"
            test_file.write_text("""
def add(a: int, b: int) -> int:
    '''Add two numbers.

    Args:
        x: First number (WRONG - should be 'a')
        y: Second number (WRONG - should be 'b')

    Returns:
        Sum of the numbers
    '''
    return a + b
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should detect signature mismatch
            sig_findings = [f for f in findings if f["category"] == "signature_mismatch"]
            assert len(sig_findings) > 0
            assert sig_findings[0]["severity"] == "MEDIUM"
            assert "add" in sig_findings[0]["message"]

    def test_validate_code_snippets_in_docs(self):
        """Test validation of code snippets in documentation."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "example.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-my_function",
                        "name": "my_function",
                        "type": "function",
                        "file": "example.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        # Create a file with valid code example in docstring
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "example.py"
            test_file.write_text("""
def my_function(value: int) -> int:
    '''My function.

    Example:
        >>> my_function(5)
        10
    '''
    return value * 2
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should not flag valid code snippets
            snippet_findings = [f for f in findings if f["category"] == "invalid_snippet"]
            assert len(snippet_findings) == 0

    def test_detect_invalid_code_snippets(self):
        """Test detection of invalid code snippets in docs."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "bad_example.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-broken_func",
                        "name": "broken_func",
                        "type": "function",
                        "file": "bad_example.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        # Create a file with syntactically invalid example
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "bad_example.py"
            test_file.write_text("""
def broken_func(x: int) -> int:
    '''Broken function.

    Example:
        >>> broken_func(()
        10
    '''
    return x * 2
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should detect invalid code snippet
            snippet_findings = [f for f in findings if f["category"] == "invalid_snippet"]
            assert len(snippet_findings) > 0
            assert snippet_findings[0]["severity"] == "LOW"

    def test_detect_missing_symbols_in_docs(self):
        """Test detection of symbols missing from documentation."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "module.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-undocumented_func",
                        "name": "undocumented_func",
                        "type": "function",
                        "file": "module.py"
                    },
                    {
                        "id": "symbol-2-documented_func",
                        "name": "documented_func",
                        "type": "function",
                        "file": "module.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        # Create a file where one function has no docstring
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "module.py"
            test_file.write_text("""
def undocumented_func(x: int) -> int:
    return x * 2

def documented_func(x: int) -> int:
    '''Documented function.

    Args:
        x: Input value

    Returns:
        Result
    '''
    return x * 3
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should detect missing documentation
            missing_findings = [f for f in findings if f["category"] == "missing_documentation"]
            assert len(missing_findings) > 0
            assert "undocumented_func" in missing_findings[0]["message"]
            assert missing_findings[0]["severity"] == "LOW"

    def test_return_structured_findings_with_severity(self):
        """Test that findings are structured with proper severity."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "multi_issues.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-func1",
                        "name": "func1",
                        "type": "function",
                        "file": "multi_issues.py"
                    },
                    {
                        "id": "symbol-2-func2",
                        "name": "func2",
                        "type": "function",
                        "file": "multi_issues.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "multi_issues.py"
            test_file.write_text("""
def func1(a: int) -> int:
    '''Func with wrong doc param.

    Args:
        x: Wrong param name
    '''
    return a

def func2(b: int) -> int:
    return b * 2
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # All findings should have required fields
            for finding in findings:
                assert "category" in finding
                assert "severity" in finding
                assert "message" in finding
                assert "file" in finding
                assert finding["severity"] in ["HIGH", "MEDIUM", "LOW"]

    def test_handle_missing_package_root(self):
        """Test graceful handling when package root is not set."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {"items": []},
            "symbol_graph": {"nodes": [], "edges": []},
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        analyzer = DocConsistencyAnalyzer(manifest)
        findings = analyzer.analyze()

        # Should return empty findings without crashing
        assert findings == []

    def test_ignore_private_symbols(self):
        """Test that private symbols are not checked for documentation."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "privates.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-_private_func",
                        "name": "_private_func",
                        "type": "function",
                        "file": "privates.py"
                    },
                    {
                        "id": "symbol-2-public_func",
                        "name": "public_func",
                        "type": "function",
                        "file": "privates.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "privates.py"
            test_file.write_text("""
def _private_func(x: int) -> int:
    return x

def public_func(x: int) -> int:
    return x * 2
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should only flag public function
            missing_findings = [f for f in findings if f["category"] == "missing_documentation"]
            assert len(missing_findings) == 1
            assert "public_func" in missing_findings[0]["message"]

    def test_analyze_returns_consistent_format(self):
        """Test that analyze() returns consistently formatted results."""
        manifest = {
            "metadata": {"package_name": "test-package"},
            "file_inventory": {
                "items": [
                    {
                        "path": "format_test.py",
                        "content_hash": "abc123",
                        "language": "python"
                    }
                ]
            },
            "symbol_graph": {
                "nodes": [
                    {
                        "id": "symbol-1-test_func",
                        "name": "test_func",
                        "type": "function",
                        "file": "format_test.py"
                    }
                ],
                "edges": []
            },
            "import_relationships": {"nodes": [], "edges": [], "types": []},
            "test_associations": {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "format_test.py"
            test_file.write_text("""
def test_func(x: int) -> int:
    '''Test function.

    Args:
        x: Input

    Returns:
        Output
    '''
    return x
""")

            analyzer = DocConsistencyAnalyzer(manifest)
            analyzer._set_package_root(Path(tmpdir))
            findings = analyzer.analyze()

            # Should return a list
            assert isinstance(findings, list)

            # Each finding should be a dict
            for finding in findings:
                assert isinstance(finding, dict)
