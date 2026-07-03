"""Tests for RSNFormatter and StopHook_rsn_display_gate.

Covers:
- RSNFormatter: create_result, add_findings, render_text, render_toon, validate
- StopHook_rsn_display_gate: duplicate IDs, empty messages, section overflow
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# ── RSNFormatter unit tests ──────────────────────────────────────────────────

hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from __lib.rsn_formatter import (
    RSNFinding,
    RSNFormatter,
    RSNResult,
    RSNSection,
    format_rsn,
)


class TestRSNFinding:
    def test_severity_uppercase_normalization(self):
        f = RSNFinding(id="TEST-001", severity="critical", message="Fix X")
        assert f.severity == "CRITICAL"

    def test_all_required_fields(self):
        f = RSNFinding(
            id="TEST-001",
            severity="HIGH",
            message="Fix Y",
            file_ref="path:10",
            action_type="Use /skill",
            effort_minutes=15,
            blast_radius=3,
            reversibility=1.5,
            evidence_tier=2,
            domain="security",
        )
        assert f.severity == "HIGH"
        assert f.file_ref == "path:10"
        assert f.blast_radius == 3


class TestRSNSection:
    def test_add_and_sort(self):
        sec = RSNSection(name="Logical Gaps", key="logical_gaps")
        sec.add(RSNFinding(id="B", severity="LOW", message="b"))
        sec.add(RSNFinding(id="A", severity="CRITICAL", message="a"))
        sec.add(RSNFinding(id="C", severity="HIGH", message="c"))
        sec.sort_by_severity()
        assert sec.findings[0].severity == "CRITICAL"
        assert sec.findings[1].severity == "HIGH"
        assert sec.findings[2].severity == "LOW"

    def test_is_empty(self):
        sec = RSNSection(name="Empty", key="empty")
        assert sec.is_empty() is True
        sec.add(RSNFinding(id="X", severity="LOW", message="x"))
        assert sec.is_empty() is False


class TestRSNResult:
    def test_severity_counts(self):
        result = RSNResult()
        sec = RSNSection(name="Test", key="test")
        sec.add(RSNFinding(id="C1", severity="CRITICAL", message="c1"))
        sec.add(RSNFinding(id="C2", severity="CRITICAL", message="c2"))
        sec.add(RSNFinding(id="H1", severity="HIGH", message="h1"))
        sec.add(RSNFinding(id="M1", severity="MEDIUM", message="m1"))
        sec.add(RSNFinding(id="L1", severity="LOW", message="l1"))
        result.sections.append(sec)
        result.count_severity()
        assert result.total_critical == 2
        assert result.total_high == 1
        assert result.total_medium == 1
        assert result.total_low == 1
        assert result.total_findings == 5
        assert result.has_findings is True

    def test_section_lookup(self):
        result = RSNResult()
        sec = RSNSection(name="Logical Gaps", key="logical_gaps")
        result.sections.append(sec)
        found = result.section("logical_gaps")
        assert found is not None
        assert found.key == "logical_gaps"
        assert result.section("nonexistent") is None


class TestRSNFormatterDomainRouting:
    """Test domain → section routing."""

    def test_security_routes_to_logical_gaps(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "SEC-001", "severity": "HIGH", "message": "Fix X", "domain": "security"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "logical_gaps"

    def test_performance_routes_to_hidden_assumptions(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {
                    "id": "PERF-001",
                    "severity": "MEDIUM",
                    "message": "Fix X",
                    "domain": "performance",
                },
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "hidden_assumptions"

    def test_test_coverage_routes_to_missing_actions(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "TEST-001", "severity": "MEDIUM", "message": "Fix X", "domain": "test"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "missing_actions"

    def test_risk_routes_to_risks(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "RISK-001", "severity": "LOW", "message": "Edge case", "domain": "risk"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "risks"

    def test_docs_routes_to_recommendations(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "DOC-001", "severity": "LOW", "message": "Add doc", "domain": "docs"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "recommendations"

    def test_unknown_domain_critical_routes_to_logical_gaps(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "X-001", "severity": "CRITICAL", "message": "Fix X", "domain": "unknown"},
            ]
        )
        assert result.sections[0].key == "logical_gaps"

    def test_unknown_domain_low_routes_to_open_questions(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "X-001", "severity": "LOW", "message": "Question", "domain": "unknown"},
            ]
        )
        assert result.sections[0].key == "open_questions"

    def test_custom_section_definitions_override(self):
        formatter = RSNFormatter(
            section_definitions={
                "test": ("Test Coverage Gaps", "test_gaps"),
            }
        )
        result = formatter.create_result(
            findings=[
                {"id": "TEST-001", "severity": "MEDIUM", "message": "Fix X", "domain": "test"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "test_gaps"
        assert result.sections[0].name == "Test Coverage Gaps"

    def test_lazy_section_creation(self):
        """Only sections with findings are created."""
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "SEC-001", "severity": "CRITICAL", "message": "Fix X", "domain": "security"},
            ]
        )
        assert len(result.sections) == 1
        assert result.sections[0].key == "logical_gaps"


class TestRSNFormatterRender:
    """Test text and TOON rendering."""

    def test_render_text_empty(self):
        formatter = RSNFormatter()
        result = formatter.create_result(intent_summary="No findings")
        text = formatter.render_text(result)
        assert "Recommended Next Steps" in text
        assert "0 — Do ALL" not in text  # No findings → no footer

    def test_render_text_single_finding(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {
                    "id": "SEC-001",
                    "severity": "CRITICAL",
                    "message": "Fix YAML unsafe_load",
                    "file_ref": "path:12",
                },
            ]
        )
        text = formatter.render_text(result)
        assert "Recommended Next Steps" in text
        assert "1. Logical Gaps" in text
        assert "SEC-001" not in text  # Finding IDs only appear in TOON, not text format
        assert "[CRITICAL]" in text
        assert "path:12" in text
        assert "0 — Do ALL Recommended Next Steps" in text

    def test_render_text_with_tags(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {
                    "id": "SEC-001",
                    "severity": "HIGH",
                    "message": "Fix X",
                    "blast_radius": 3,
                    "reversibility": 1.5,
                    "evidence_tier": 1,
                },
            ]
        )
        text = formatter.render_text(result)
        assert "blast: 3" in text
        assert "rev: 1.50" in text
        assert "conf:H" in text

    def test_render_toon_basic(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            intent_summary="Hook audit",
            findings=[
                {
                    "id": "SHIP-CONTEXT_-a3f2",
                    "severity": "CRITICAL",
                    "message": "Fix YAML unsafe_load",
                    "file_ref": "path:12",
                    "action_type": "Manual",
                    "effort_minutes": 5,
                    "blast_radius": 3,
                    "reversibility": 1.5,
                    "evidence_tier": 1,
                    "domain": "security",
                },
            ],
        )
        toon = formatter.render_toon(result)
        assert "{RSN}" in toon
        assert "{/RSN}" in toon  # Closing tag
        assert "SHIP-CONTEXT_-a3f2" in toon
        assert "severity_totals: CRITICAL=1" in toon
        assert "intent: Hook audit" in toon
        assert "message: Fix YAML unsafe_load" in toon
        assert "ref: path:12" in toon
        assert "[logical_gaps]" in toon

    def test_render_toon_mixed_case_ids(self):
        """Mixed-case finding IDs like SHIP-CONTEXT_-a3f2 render correctly in TOON."""
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {
                    "id": "SHIP-CONTEXT_-a3f2",
                    "severity": "CRITICAL",
                    "message": "Fix A",
                    "domain": "security",
                },
                {
                    "id": "SHIP-BLAST_-b7c1",
                    "severity": "HIGH",
                    "message": "Fix B",
                    "domain": "security",
                },
            ]
        )
        toon = formatter.render_toon(result)
        assert "SHIP-CONTEXT_-a3f2" in toon
        assert "SHIP-BLAST_-b7c1" in toon


class TestRSNFormatterValidate:
    """Test validate() method."""

    def test_validate_clean(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "SEC-001", "severity": "CRITICAL", "message": "Fix X"},
            ]
        )
        errors = formatter.validate(result)
        assert errors == []

    def test_validate_duplicate_ids(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "SEC-001", "severity": "CRITICAL", "message": "Fix A"},
                {"id": "SEC-001", "severity": "HIGH", "message": "Fix B"},
            ]
        )
        errors = formatter.validate(result)
        assert any("Duplicate" in e and "SEC-001" in e for e in errors)

    def test_validate_empty_message(self):
        formatter = RSNFormatter()
        result = formatter.create_result(
            findings=[
                {"id": "SEC-001", "severity": "CRITICAL", "message": "   "},
            ]
        )
        errors = formatter.validate(result)
        assert any("Empty message" in e for e in errors)

    def test_validate_section_overflow(self):
        formatter = RSNFormatter()
        findings = [
            {
                "id": f"SEC-{i:03d}",
                "severity": "LOW",
                "message": f"Fix {i}",
                "domain": "security",
            }
            for i in range(25)
        ]
        result = formatter.create_result(findings=findings)
        errors = formatter.validate(result)
        assert any("cognitive overflow" in e for e in errors)


class TestFormatRsn:
    """Test convenience function."""

    def test_format_rsn_single(self):
        result = format_rsn(
            [{"id": "SEC-001", "severity": "CRITICAL", "message": "Fix X"}],
            intent_summary="Audit",
        )
        assert "Recommended Next Steps" in result
        assert "SEC-001" not in result  # Finding IDs only appear in TOON, not text format
        assert "[CRITICAL]" in result


# ── StopHook_rsn_display_gate integration tests ────────────────────────────────

STOP_GATE = hooks_dir / "StopHook_rsn_display_gate.py"


class TestStopHookRsnDisplayGate:
    """Test the quality gate end-to-end via subprocess."""

    def _run_gate(self, response: str) -> dict:
        """Run the gate as subprocess and return parsed JSON."""
        env = os.environ.copy()
        env["RSN_DISPLAY_GATE_ENABLED"] = "true"
        proc = subprocess.run(
            [sys.executable, str(STOP_GATE)],
            input=json.dumps({"response": response}),
            capture_output=True,
            text=True,
            env=env,
        )
        return json.loads(proc.stdout)

    def test_clean_response_returns_none(self):
        response = "Here is some code that works fine."
        result = self._run_gate(response)
        assert result["allow"] is True
        assert "warning" not in result

    def test_clean_rsn_text_no_issues(self):
        response = """Recommended Next Steps

1. Logical Gaps & Inconsistencies
   1a. [SEC-001] Fix YAML unsafe_load (path:12)

0 — Do ALL Recommended Next Steps"""
        result = self._run_gate(response)
        assert result["allow"] is True

    def test_clean_toon_format_no_issues(self):
        response = """{RSN}
  severity_totals: CRITICAL=1 HIGH=0 MEDIUM=0 LOW=0
  [logical_gaps]
    (SHIP-CONTEXT_-a3f2) CRITICAL @security
      message: Fix YAML unsafe_load
      ref: path:12
      action: Manual
      effort: 5
      blast: 3
      rev: 1.50
      conf: H
  [/logical_gaps]
{/RSN}"""
        result = self._run_gate(response)
        assert result["allow"] is True

    def test_detects_duplicate_ids_in_toon(self):
        response = """{RSN}
  severity_totals: CRITICAL=2 HIGH=0 MEDIUM=0 LOW=0
  [logical_gaps]
    (SHIP-CONTEXT_-a3f2) CRITICAL @security
      message: Fix A
    (SHIP-CONTEXT_-a3f2) HIGH @security
      message: Fix B
  [/logical_gaps]
{/RSN}"""
        result = self._run_gate(response)
        assert "allow" in result
        assert "warning" in result
        assert "SHIP-CONTEXT_-a3f2" in result["warning"]
        assert "Duplicate" in result["warning"]

    def test_detects_duplicate_ids_in_text(self):
        response = """Recommended Next Steps

1. Logical Gaps & Inconsistencies
   1a. [SHIP-CONTEXT_-a3f2] Fix A (path:12)
   1b. [SHIP-CONTEXT_-a3f2] Fix B (path:45)

0 — Do ALL Recommended Next Steps"""
        result = self._run_gate(response)
        assert "allow" in result
        assert "Duplicate" in result.get("warning", "")

    def test_detects_empty_message_in_toon(self):
        response = """{RSN}
  severity_totals: CRITICAL=1 HIGH=0 MEDIUM=0 LOW=0
  [logical_gaps]
    (SEC-001) CRITICAL @security
      message:
      ref: path:12
  [/logical_gaps]
{/RSN}"""
        result = self._run_gate(response)
        assert "Empty message" in result.get("warning", "")

    def test_detects_section_overflow_in_toon(self):
        findings = "\n".join(
            f"    (ID-{i:03d}) LOW @unknown\n      message: Issue {i}" for i in range(25)
        )
        response = f"""{{RSN}}
  severity_totals: CRITICAL=0 HIGH=0 MEDIUM=0 LOW=25
  [open_questions]
{findings}
  [/open_questions]
{{/RSN}}"""
        result = self._run_gate(response)
        assert "cognitive overflow" in result.get("warning", "")

    def test_detects_section_overflow_in_text(self):
        lines = ["1. Open Questions / Unknowns"]
        for i in range(25):
            lines.append(f"   1{chr(97 + i)}. [ID-{i:03d}] Issue {i} (path:{i})")
        lines.append("0 — Do ALL Recommended Next Steps")
        response = "\n".join(lines)
        result = self._run_gate(response)
        assert "cognitive overflow" in result.get("warning", "")

    def test_mixed_case_id_detected_in_toon(self):
        """SHIP-CONTEXT_-a3f2 mixed-case ID is correctly captured."""
        response = """{RSN}
  severity_totals: CRITICAL=1 HIGH=1 MEDIUM=0 LOW=0
  [logical_gaps]
    (SHIP-CONTEXT_-a3f2) CRITICAL @security
      message: Fix A
    (SHIP-BLAST_-b7c1) HIGH @security
      message: Fix B
  [/logical_gaps]
{/RSN}"""
        result = self._run_gate(response)
        # No duplicates → no warning
        assert result.get("warning", "") == ""

    def test_mixed_case_id_with_duplicate_detected(self):
        """Duplicate mixed-case IDs are detected."""
        response = """{RSN}
  severity_totals: CRITICAL=2 HIGH=0 MEDIUM=0 LOW=0
  [logical_gaps]
    (SHIP-CONTEXT_-a3f2) CRITICAL @security
      message: Fix A
    (SHIP-CONTEXT_-a3f2) CRITICAL @logic
      message: Fix B
  [/logical_gaps]
{/RSN}"""
        result = self._run_gate(response)
        assert "Duplicate" in result.get("warning", "")
        assert "SHIP-CONTEXT_-a3f2" in result.get("warning", "")

    def test_disabled_via_env_var(self):
        response = """Recommended Next Steps

1. Logical Gaps & Inconsistencies
   1a. [SEC-001] Fix YAML unsafe_load (path:12)

0 — Do ALL Recommended Next Steps"""
        proc = subprocess.run(
            [sys.executable, str(STOP_GATE)],
            input=json.dumps({"response": response}),
            capture_output=True,
            text=True,
            env={**os.environ, "RSN_DISPLAY_GATE_ENABLED": "false"},
        )
        result = json.loads(proc.stdout)
        assert result == {"allow": True}
