"""Tests for ddgs_search.py — the PowerShell-safe DDG wrapper."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("P:/.agents/scripts/ddgs_search.py")


def run_script(*args, stdin_input=None):
    """Run ddgs_search.py with args, return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        input=stdin_input,
    )
    return result.returncode, result.stdout, result.stderr


class TestScriptInterface:
    """Interface and argument handling."""

    def test_no_args_errors_cleanly(self):
        """No query and no --stdin should error, not crash."""
        code, out, err = run_script()
        assert code != 0
        assert "error" in out.lower() or "error" in err.lower()

    def test_help_works(self):
        """--help should succeed and show usage."""
        code, out, err = run_script("--help")
        assert code == 0
        assert "query" in out.lower()

    def test_stdin_mode(self):
        """--stdin reads query from piped input."""
        code, out, err = run_script("--stdin", stdin_input="python testing")
        assert code == 0
        # Should produce valid JSON
        data = json.loads(out)
        assert isinstance(data, list)


class TestSearchOutput:
    """Search output format and correctness."""

    def test_json_output_valid(self):
        """JSON output is a list of dicts with title/href/body keys."""
        code, out, err = run_script("python refactoring", "--max", "3")
        assert code == 0, f"Script failed: {err}"
        data = json.loads(out)
        assert isinstance(data, list)
        if data:  # may be empty if DDG has no results
            for item in data:
                assert "title" in item
                assert "href" in item
                assert "body" in item

    def test_text_output_format(self):
        """--text produces human-readable output with TITLE/URL/BODY labels."""
        code, out, err = run_script("python testing", "--max", "2", "--text")
        assert code == 0
        assert "TITLE:" in out or "URL:" in out or len(out.strip()) == 0

    def test_site_restriction(self):
        """--site prepends site: to the query."""
        code, out, err = run_script("AI agent", "--site", "reddit.com", "--max", "2")
        assert code == 0
        data = json.loads(out)
        assert isinstance(data, list)
        # If results returned, URLs should be from reddit.com
        if data:
            for item in data:
                assert "reddit.com" in item.get("href", "") or "reddit" in item.get("body", "").lower()

    def test_max_results_respected(self):
        """--max limits the number of results."""
        code, out, err = run_script("python programming", "--max", "2")
        assert code == 0
        data = json.loads(out)
        assert len(data) <= 2


class TestRobustness:
    """Edge cases and error handling."""

    def test_empty_query_via_stdin(self):
        """Empty stdin query should not crash with traceback."""
        code, out, err = run_script("--stdin", stdin_input="")
        # DDGS may return empty or error — either is fine, no traceback
        assert "Traceback" not in err or code == 0

    def test_special_characters_in_query(self):
        """Query with special characters doesn't break."""
        code, out, err = run_script("python 'quotes' and \"double\"", "--max", "1")
        assert code == 0
        json.loads(out)  # valid JSON either way

    def test_script_compiles(self):
        """Script has no syntax errors."""
        code = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT)],
            capture_output=True,
        )
        assert code.returncode == 0, f"Syntax error: {code.stderr.decode()}"
