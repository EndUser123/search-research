"""RSN Formatter - Shared Recommended Next Steps formatter.

Priority: P0 (shared infrastructure)
Purpose: Unified RSN output format for /critique, /gto, and /uci skills

Format: Dynamic section critique structure
    - Sections are created lazily (only when findings exist for them)
    - Domain taxonomy from DEFAULT_SECTIONS defines what sections CAN exist
    - Severity ordering: CRITICAL > HIGH > MEDIUM > LOW within each section
    - Sequential numbering (1., 1a., 1b.) — gaps eliminated automatically

Usage:
    from __lib.rsn_formatter import RSNFormatter, RSNFinding

    formatter = RSNFormatter()
    result = formatter.format(findings)
    print(formatter.render_text(result))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Severity ordering
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Action type routing
ActionType = Literal["Manual", "Use /skill", "Use Agent"]


@dataclass
class RSNFinding:
    """A single finding within an RSN section."""

    id: str  # e.g., "SEC-001", "PERF-001"
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    message: str  # What to fix
    file_ref: str | None = None  # "path/to/file.py:123"
    action_type: ActionType = "Manual"
    effort_minutes: int = 5
    blast_radius: int | None = None  # Who else is affected (reverse mobility)
    reversibility: float | None = None  # Reversibility score (1.0=trivial, 2.0=irreversible)
    evidence_tier: int | None = None  # 1=high confidence (Tier 1), 4=low confidence (Tier 4)
    domain: str | None = None  # e.g., "security", "performance"

    def __post_init__(self) -> None:
        # Normalize severity
        if self.severity:
            self.severity = self.severity.upper()  # type: ignore[assignment]


@dataclass
class RSNSection:
    """A named section containing related findings."""

    name: str  # e.g., "Logical Gaps & Inconsistencies"
    key: str  # e.g., "logical_gaps"
    findings: list[RSNFinding] = field(default_factory=list)

    def add(self, finding: RSNFinding) -> None:
        self.findings.append(finding)

    def sort_by_severity(self) -> None:
        # Sort by severity first, then by blast_radius descending (higher impact first within tier)
        self.findings.sort(
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), -(f.blast_radius or 0), f.id)
        )

    def is_empty(self) -> bool:
        return len(self.findings) == 0


@dataclass
class RSNResult:
    """Complete RSN output with all sections."""

    intent_summary: str = ""
    sections: list[RSNSection] = field(default_factory=list)
    total_critical: int = 0
    total_high: int = 0
    total_medium: int = 0
    total_low: int = 0

    def section(self, key: str) -> RSNSection | None:
        for s in self.sections:
            if s.key == key:
                return s
        return None

    def count_severity(self) -> None:
        self.total_critical = sum(
            1 for s in self.sections for f in s.findings if f.severity == "CRITICAL"
        )
        self.total_high = sum(1 for s in self.sections for f in s.findings if f.severity == "HIGH")
        self.total_medium = sum(
            1 for s in self.sections for f in s.findings if f.severity == "MEDIUM"
        )
        self.total_low = sum(1 for s in self.sections for f in s.findings if f.severity == "LOW")

    @property
    def total_findings(self) -> int:
        return self.total_critical + self.total_high + self.total_medium + self.total_low

    @property
    def has_findings(self) -> bool:
        return self.total_findings > 0


# Default section definitions in order
DEFAULT_SECTIONS: list[tuple[str, str]] = [
    ("Logical Gaps & Inconsistencies", "logical_gaps"),
    ("Hidden Assumptions & Fragile Dependencies", "hidden_assumptions"),
    ("Missing Obvious Actions / Best Practices", "missing_actions"),
    ("Risks and Edge Cases", "risks"),
    ("Concrete Recommendations", "recommendations"),
    ("Open Questions / Unknowns", "open_questions"),
]


# Type alias: section definitions mapping domain → (section_name, section_key)
SectionDefinitions = dict[str, tuple[str, str]]


class RSNFormatter:
    """
    Format findings into dynamic section critique structure.

    Section names are determined by the domains present in findings — skills can
    pass custom section definitions to override the default 6-section taxonomy.

    Works with any finding set that has:
    - id, severity, message, file_ref fields
    - Optionally: action_type, effort_minutes, domain

    Supports both dict-style and dataclass-style findings.
    """

    def __init__(self, section_definitions: SectionDefinitions | None = None) -> None:
        """
        Initialize formatter.

        Args:
            section_definitions: Optional custom domain → (section_name, section_key) mapping.
                When provided, these take precedence over the default routing.
                Example: {"test": ("Test Coverage Gaps", "test_gaps"), "docs": ("Doc Gaps", "doc_gaps")}
        """
        self._section_definitions = section_definitions or {}

    def _normalize_finding(self, raw: dict | RSNFinding) -> RSNFinding:
        """Convert a raw finding (dict or dataclass) to RSNFinding."""
        if isinstance(raw, RSNFinding):
            return raw

        # Dict-style
        return RSNFinding(
            id=raw.get("id", raw.get("gap_id", "unknown")),
            severity=(raw.get("severity") or "LOW"),
            message=raw.get("message", raw.get("description", "")),
            file_ref=raw.get("file_ref", raw.get("file_path", "")),
            action_type=raw.get("action_type", "Manual"),
            effort_minutes=raw.get("effort_minutes", raw.get("effort_estimate_minutes", 5)),
            blast_radius=raw.get("blast_radius"),
            reversibility=raw.get("reversibility"),
            evidence_tier=raw.get("evidence_tier"),
            domain=raw.get("domain", raw.get("type")),
        )

    def create_result(
        self,
        intent_summary: str = "",
        findings: list[dict | RSNFinding] | None = None,
    ) -> RSNResult:
        """
        Create an empty RSNResult (no pre-populated sections).

        Sections are created lazily when findings are added via add_findings().
        This implements the "minimum-viable with dynamic extension" principle —
        only sections with findings are rendered.

        Args:
            intent_summary: One-line description of what was analyzed
            findings: Optional list of raw findings to categorize

        Returns:
            RSNResult with no pre-populated sections
        """
        result = RSNResult(intent_summary=intent_summary)

        if findings:
            self._categorize_findings(result, findings)

        result.count_severity()
        return result

    def _categorize_findings(self, result: RSNResult, findings: list[dict | RSNFinding]) -> None:
        """Distribute findings into appropriate sections by domain/type.

        Uses custom section definitions if provided, otherwise falls back to default routing.
        Section names are dynamically determined by the domains present in findings.
        """
        for raw in findings:
            finding = self._normalize_finding(raw)
            domain = (finding.domain or "").lower()
            severity = finding.severity

            # Check custom section definitions first
            if domain in self._section_definitions:
                section_name, section_key = self._section_definitions[domain]
            else:
                # Default routing based on domain
                if domain in ("security", "inv", "invariant", "logic", "api"):
                    section_name, section_key = "Logical Gaps & Inconsistencies", "logical_gaps"
                elif domain in ("performance", "concurrency", "reliability"):
                    section_name, section_key = (
                        "Hidden Assumptions & Fragile Dependencies",
                        "hidden_assumptions",
                    )
                elif domain in ("test", "testing", "coverage", "quality", "maintainability"):
                    section_name, section_key = (
                        "Missing Obvious Actions / Best Practices",
                        "missing_actions",
                    )
                elif domain in ("risk", "edge_case"):
                    section_name, section_key = "Risks and Edge Cases", "risks"
                elif domain in ("docs", "documentation"):
                    section_name, section_key = "Concrete Recommendations", "recommendations"
                else:
                    # Default routing based on severity
                    if severity in ("CRITICAL", "HIGH"):
                        section_name, section_key = "Logical Gaps & Inconsistencies", "logical_gaps"
                    elif severity == "MEDIUM":
                        section_name, section_key = (
                            "Hidden Assumptions & Fragile Dependencies",
                            "hidden_assumptions",
                        )
                    else:
                        section_name, section_key = "Open Questions / Unknowns", "open_questions"

            section = result.section(section_key)
            if not section:
                # Lazily create the section — implements dynamic domain extension
                section = RSNSection(name=section_name, key=section_key)
                result.sections.append(section)
            section.add(finding)

    def add_findings(self, result: RSNResult, findings: list[dict | RSNFinding]) -> None:
        """Add findings to an existing result, re-categorizing."""
        self._categorize_findings(result, findings)
        # Re-sort all sections
        for section in result.sections:
            section.sort_by_severity()
        result.count_severity()

    def sort_all_sections(self, result: RSNResult) -> None:
        """Sort all sections by severity."""
        for section in result.sections:
            section.sort_by_severity()
        result.count_severity()

    def render_text(
        self,
        result: RSNResult,
        include_execution_directive: bool = True,
    ) -> str:
        """
        Render RSNResult as plain text.

        Format:
            Recommended Next Steps

            1. Logical Gaps & Inconsistencies
               1a. [SEC-001] Fix YAML unsafe_load (path:12)
               1b. [SEC-002] Add regex bypass protection (path:45)

            ...

            0 — Do ALL Recommended Next Steps

        Args:
            result: RSNResult to render
            include_execution_directive: Whether to add the "0 —" footer

        Returns:
            Formatted text string
        """
        lines: list[str] = []

        lines.append("Recommended Next Steps")
        lines.append("")

        section_num = 1
        for section in result.sections:
            if section.is_empty():
                continue

            lines.append(f"{section_num}. {section.name}")
            sub_num = 1
            for finding in section.findings:
                # Sub-item: 1a, 1b, etc.
                sub_label = f"{section_num}{chr(97 + sub_num - 1)}"  # 1a, 1b, 1c...
                severity_tag = f"[{finding.severity}]" if finding.severity else ""

                # Tags: blast_radius, reversibility, evidence_tier
                tags: list[str] = []
                if finding.blast_radius is not None:
                    tags.append(f"blast:{finding.blast_radius:>2}")
                if finding.reversibility is not None:
                    tags.append(f"rev:{finding.reversibility:>5.2f}")
                if finding.evidence_tier is not None:
                    conf_label = {1: "H", 2: "M", 3: "L", 4: "L"}.get(finding.evidence_tier, "?")
                    tags.append(f"conf:{conf_label}")
                tag_str = f"[{', '.join(tags)}]" if tags else ""

                parts = [f"   {sub_label}. {severity_tag}{tag_str} {finding.message}".strip()]
                if finding.file_ref:
                    parts.append(f"({finding.file_ref})")
                if finding.action_type and finding.action_type != "Manual":
                    parts.append(f"— {finding.action_type}")

                lines.append(" ".join(parts))
                sub_num += 1

            lines.append("")
            section_num += 1

        if include_execution_directive and result.has_findings:
            lines.append("0 — Do ALL Recommended Next Steps")

        return "\n".join(lines)

    def render_markdown(
        self,
        result: RSNResult,
        include_execution_directive: bool = True,
    ) -> str:
        """
        Render RSNResult as markdown (same as text for this format).

        Args:
            result: RSNResult to render
            include_execution_directive: Whether to add the "0 —" footer

        Returns:
            Formatted markdown string
        """
        return self.render_text(result, include_execution_directive)

    def render_toon(self, result: RSNResult) -> str:
        """
        Render RSNResult as TOON (Token-Oriented Object Notation) — machine-parseable.

        Format:
            {RSN}
              [section_key]
                (finding_id) severity @domain
                  message: ...
                  ref: path/to/file.py:123
                  action: Manual | Use /skill | Use Agent
                  effort: 5
                  blast: 3
                  rev: 1.25
                  conf: H
              [/section_key]
            {/RSN}

        Args:
            result: RSNResult to render

        Returns:
            Machine-parseable TOON string
        """
        lines: list[str] = ["{RSN}"]

        if result.intent_summary:
            lines.append(f"  intent: {result.intent_summary}")

        lines.append(
            f"  severity_totals: CRITICAL={result.total_critical} HIGH={result.total_high} MEDIUM={result.total_medium} LOW={result.total_low}"
        )

        for section in result.sections:
            if section.is_empty():
                continue
            lines.append(f"  [{section.key}]")
            for finding in section.findings:
                lines.append(f"    ({finding.id}) {finding.severity} @{finding.domain or '_'}")
                lines.append(f"      message: {finding.message}")
                if finding.file_ref:
                    lines.append(f"      ref: {finding.file_ref}")
                if finding.action_type:
                    lines.append(f"      action: {finding.action_type}")
                lines.append(f"      effort: {finding.effort_minutes}")
                if finding.blast_radius is not None:
                    lines.append(f"      blast: {finding.blast_radius}")
                if finding.reversibility is not None:
                    lines.append(f"      rev: {finding.reversibility:.2f}")
                if finding.evidence_tier is not None:
                    conf_label = {1: "H", 2: "M", 3: "L", 4: "L"}.get(finding.evidence_tier, "?")
                    lines.append(f"      conf: {conf_label}")
            lines.append(f"  [/{section.key}]")

        lines.append("{/RSN}")
        return "\n".join(lines)

    def validate(self, result: RSNResult) -> list[str]:
        """
        Validate RSNResult for common quality issues.

        Checks:
        - Duplicate finding IDs
        - Empty messages
        - Section overflow (>20 findings per section — cognitive load risk)
        - Unused custom section definitions

        Args:
            result: RSNResult to validate

        Returns:
            List of validation error messages (empty if clean)
        """
        errors: list[str] = []
        seen_ids: set[str] = set()

        for section in result.sections:
            if len(section.findings) > 20:
                errors.append(
                    f"Section [{section.key}] has {len(section.findings)} findings "
                    f"(cognitive overflow — consider splitting)"
                )
            for finding in section.findings:
                if finding.id in seen_ids:
                    errors.append(f"Duplicate finding ID: {finding.id}")
                seen_ids.add(finding.id)
                if not finding.message.strip():
                    errors.append(f"Empty message in finding {finding.id}")

        return errors


# Convenience function
def format_rsn(
    findings: list[dict | RSNFinding],
    intent_summary: str = "",
) -> str:
    """
    Quick RSN formatting from a list of finding dicts.

    Args:
        findings: List of finding dictionaries with keys:
            - id: finding identifier
            - severity: CRITICAL/HIGH/MEDIUM/LOW
            - message: description
            - file_ref: optional "path:line"
            - domain: optional category
        intent_summary: What was analyzed

    Returns:
        Formatted RSN text
    """
    formatter = RSNFormatter()
    result = formatter.create_result(intent_summary=intent_summary, findings=findings)
    formatter.sort_all_sections(result)
    return formatter.render_text(result)


__all__ = [
    "RSNFormatter",
    "RSNFinding",
    "RSNSection",
    "RSNResult",
    "format_rsn",
    "SEVERITY_ORDER",
]
