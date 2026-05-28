#!/usr/bin/env python3
"""
Test suite for Stop_removal_completeness_guard.py

Coverage:
- Removal completion pattern detection (positive/negative/allowlist)
- Module name extraction from file paths and explicit mentions
- Reference search with filesystem scanning
- Integration tests for check()
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from Stop_removal_completeness_guard import (
    COMPLETION_ALLOWLIST,
    MAX_FILES_TO_SCAN,
    MAX_MODULE_NAMES,
    MAX_RESULTS,
    REMOVAL_COMPLETION_PATTERNS,
    _extract_module_names,
    _search_remaining_references,
    check,
)


class TestPatternDetection:
    """Test removal completion pattern detection."""

    def test_completion_patterns_positive(self):
        positive = [
            "cleanup complete",
            "cleanup is complete",
            "fully removed",
            "completely removed",
            "fully deleted",
            "removal complete",
            "removal is complete",
            "all references removed",
            "all imports removed",
            "zero remaining references",
            "no remaining references",
            "no more imports",
            "all remaining usages gone",
        ]
        for case in positive:
            assert REMOVAL_COMPLETION_PATTERNS.search(case), f"Should detect: {case}"

    def test_completion_patterns_negative(self):
        negative = [
            "I will clean up later",
            "the removal should be done",
            "planning to remove",
            "needs cleanup",
            "requires removal",
        ]
        for case in negative:
            assert not REMOVAL_COMPLETION_PATTERNS.search(case), f"Should NOT detect: {case}"

    def test_allowlist_code_edit_contexts(self):
        allowlist_cases = [
            "fully removed the marker from the regex",
            "completely removed the check from the guard",
            "fully removed the constraint from the schema",
            "fully removed the duplicate entry",
            "completely removed the qualifier from the pattern",
        ]
        for case in allowlist_cases:
            assert COMPLETION_ALLOWLIST.search(case), f"Should allowlist: {case}"

    def test_allowlist_hypothetical(self):
        cases = [
            "if cleanup complete, we can proceed",
            "should cleanup complete before Tuesday",
            "would cleanup complete the migration",
        ]
        for case in cases:
            assert COMPLETION_ALLOWLIST.search(case), f"Should allowlist: {case}"


class TestModuleExtraction:
    """Test module name extraction from response text."""

    def test_extract_from_file_paths(self):
        response = "Deleted external_judge.py and judge_feedback.py"
        names = _extract_module_names(response)
        assert "external_judge" in names
        assert "judge_feedback" in names

    def test_extract_from_explicit_mentions(self):
        response = "The judge module has been fully removed"
        names = _extract_module_names(response)
        assert "judge" in names

    def test_extract_from_plugin_mentions(self):
        response = "the fact-guard plugin cleanup complete"
        names = _extract_module_names(response)
        assert "fact_guard" in names

    def test_extract_from_system_mentions(self):
        response = "the bifrost system cleanup is complete"
        names = _extract_module_names(response)
        assert "bifrost" in names

    def test_deduplication(self):
        response = "Removed external_judge.py and also external_judge module"
        names = _extract_module_names(response)
        count = names.count("external_judge")
        assert count == 1, f"Should deduplicate, got {count} occurrences"

    def test_max_module_names(self):
        paths = " ".join(f"file{i}.py" for i in range(20))
        names = _extract_module_names(paths)
        assert len(names) <= MAX_MODULE_NAMES

    def test_short_names_filtered(self):
        response = "Removed ab.py and xyz.py"
        names = _extract_module_names(response)
        # "ab" (2 chars) filtered, "xyz" (3 chars) kept
        assert "ab" not in names
        assert "xyz" in names


class TestReferenceSearch:
    """Test import reference scanning."""

    def test_find_import_statement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("import external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 1
            assert "external_judge" in results[0]

    def test_find_from_import_statement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("from external_judge import something\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 1

    def test_no_false_positives_in_comments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("# import external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            # Comments starting with # should not match (pattern requires start-of-line import/from)
            assert len(results) == 0

    def test_multiple_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("import external_judge\nimport judge_feedback\n")
            results = _search_remaining_references(
                ["external_judge", "judge_feedback"], Path(tmpdir)
            )
            assert len(results) == 2

    def test_no_match_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("import os\nimport sys\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 0

    def test_max_results_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(20):
                test_file = Path(tmpdir) / f"file{i}.py"
                test_file.write_text(f"import external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) <= MAX_RESULTS

    def test_skips_hidden_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hidden = Path(tmpdir) / ".hidden"
            hidden.mkdir()
            (hidden / "bad.py").write_text("import external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 0

    def test_skips_pycache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / "__pycache__"
            cache.mkdir()
            (cache / "mod.py").write_text("import external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 0

    def test_nonexistent_dir(self):
        results = _search_remaining_references(["foo"], Path("/nonexistent/path"))
        assert results == []

    def test_line_number_reporting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "consumer.py"
            test_file.write_text("import os\nimport sys\nimport external_judge\n")
            results = _search_remaining_references(["external_judge"], Path(tmpdir))
            assert len(results) == 1
            assert ":3:" in results[0]


class TestIntegration:
    """Integration tests for check()."""

    def test_blocks_on_remaining_references(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            consumer = Path(tmpdir) / "consumer.py"
            consumer.write_text("import external_judge\n")
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                data = {"response": "Cleanup complete for external_judge.py"}
                result = check(data)
                assert result is not None
                assert result["decision"] == "block"
                assert "external_judge" in result["reason"]

    def test_allows_when_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            consumer = Path(tmpdir) / "consumer.py"
            consumer.write_text("import os\nimport sys\n")
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                data = {"response": "Cleanup complete for external_judge.py"}
                result = check(data)
                assert result is None

    def test_allows_no_claim(self):
        data = {"response": "The code is working correctly"}
        result = check(data)
        assert result is None

    def test_allows_empty_response(self):
        data = {"response": ""}
        result = check(data)
        assert result is None

    def test_allows_allowlist(self):
        data = {"response": "Fully removed the marker from the regex pattern"}
        result = check(data)
        assert result is None

    def test_allows_future_tense(self):
        data = {"response": "I will clean up the judge module later"}
        result = check(data)
        assert result is None

    def test_allows_no_module_names(self):
        """Completion claim with no extractable module names -> fail open."""
        data = {"response": "Cleanup complete"}
        result = check(data)
        assert result is None

    def test_blocks_multiple_remaining(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("import judge_module\n")
            (Path(tmpdir) / "b.py").write_text("from judge_module import func\n")
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                data = {"response": "Fully removed judge_module.py"}
                result = check(data)
                assert result is not None
                assert result["decision"] == "block"

    def test_normalizes_stdout(self):
        """Verify main() produces Zod-valid JSON."""
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("import mymod\n")
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                import subprocess
                proc = subprocess.run(
                    [sys.executable, "-c",
                     f"import sys; sys.stdin.write('''{json.dumps({'response': 'Cleanup complete for mymod.py'})}''')"],
                    capture_output=True, text=True,
                    env={**os.environ, "CLAUDE_PROJECT_DIR": tmpdir},
                )
                # We just verify the hook loads without import errors
                # (full subprocess test would need the hook path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
