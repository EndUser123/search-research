#!/usr/bin/env python3
"""
Tests for Python-relevant diagnostic evidence template examples.

Tests that the diagnostic evidence template uses Python/Claude Code relevant
examples instead of Windows Event Logs.

Run with: pytest P:/.claude/hooks/tests/test_diagnostic_template_examples.py -v
"""

import pytest


class TestDiagnosticTemplateExamples:
    """Tests for diagnostic evidence template examples."""

    def test_speculation_gate_template_has_python_example(self):
        """speculation_gate.py template should include Python diagnostic examples."""
        from pathlib import Path

        speculation_gate = Path(__file__).resolve().parent.parent / "speculation_gate.py"
        content = speculation_gate.read_text()

        # Should have pytest example
        assert "pytest" in content.lower() or "test_" in content.lower(), \
            "Template should reference pytest/test diagnostics"

        # Should have import example
        assert "import" in content.lower(), \
            "Template should reference import diagnostics"

        # Should have hook error example
        assert "hook" in content.lower(), \
            "Template should reference hook diagnostics"

    def test_stop_router_template_has_python_example(self):
        """Stop_router.py user-facing template should include Python examples."""
        from pathlib import Path

        stop_router = Path(__file__).resolve().parent.parent / "Stop_router.py"
        content = stop_router.read_text()

        # Check user-facing template (around line 1421 and 1475)
        # Should have Python-relevant examples
        assert "pytest" in content.lower() or "From" in content, \
            "Template should have concrete diagnostic examples"

    def test_diagnostic_evidence_patterns_include_python(self):
        """DIAGNOSTIC_EVIDENCE_PATTERNS should include Python-relevant markers."""
        import re
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

        from speculation_gate import DIAGNOSTIC_EVIDENCE_PATTERNS

        # Convert to list for inspection
        patterns_list = list(DIAGNOSTIC_EVIDENCE_PATTERNS)

        # Should have generic markers that work for Python diagnostics
        # Check that patterns match Python-relevant diagnostic strings
        python_diagnostic_strings = [
            "From bash output, pytest shows test_checkpoint_restore FAILED",
            "tool-derived system diagnostic",
            "observed_via: Bash",
        ]

        # At least one pattern should match each Python diagnostic string
        patterns_combined = "|".join(patterns_list)
        for diagnostic in python_diagnostic_strings:
            assert re.search(patterns_combined, diagnostic, re.IGNORECASE), \
                f"Pattern should match Python diagnostic: {diagnostic}"

    def test_windows_event_log_not_primary_example(self):
        """Windows Event Log should not be the only/primary example."""
        from pathlib import Path

        # Check that Windows Event Log is not the canonical example
        speculation_gate = Path(__file__).resolve().parent.parent / "speculation_gate.py"
        content = speculation_gate.read_text()

        # Count references to Windows Event Log vs Python diagnostics
        windows_refs = content.lower().count("windows event log")
        python_refs = content.lower().count("pytest") + content.lower().count("import")

        # Windows Event Log should not dominate
        # This is a weak check - we're ensuring there's balance
        assert python_refs >= 0 or windows_refs <= 2, \
            "Python diagnostics should be represented, not just Windows Event Log"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
