"""Structured diagnostic findings storage for CKS.

Intended for use by diagnostic skills: /rca, /debug, /tdd, /arch

Provides DiagnosticFinding dataclass and store_finding() function for
writing structured findings with file references to CKS.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class DiagnosticFinding:
    """Structured finding for CKS storage.

    Categories: FIX, BUG, VULNERABILITY, PATTERN, DISCOVERY
    """

    category: str  # "FIX", "BUG", "VULNERABILITY", "PATTERN", "DISCOVERY"
    file_path: str | None
    line_number: int | None
    summary: str
    details: str
    skill_source: str  # "rca", "debug", "tdd", "arch", "security"

    def to_metadata(self) -> dict[str, str | int]:
        """Convert to CKS metadata format."""
        metadata: dict[str, str | int] = {
            "category": self.category,
            "source": f"diagnostic_{self.skill_source}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if self.file_path:
            metadata["file_path"] = self.file_path
        if self.line_number:
            metadata["line_number"] = self.line_number
        return metadata

    def to_cks_entry(self) -> tuple[str, str, dict]:
        """Return (title, content, metadata) for CKS ingestion."""
        title = f"[{self.category}] {self.summary}"
        if self.file_path:
            title += f" — {self.file_path}"

        content = f"{self.summary}\n\n{self.details}"
        return title, content, self.to_metadata()


def store_finding(finding: DiagnosticFinding) -> bool:
    """Store diagnostic finding to CKS.

    Args:
        finding: DiagnosticFinding instance to store

    Returns:
        True if successfully stored, False on error
    """
    try:
        sys.path.insert(0, "P:\\\\__csf")
        from src.cks.unified import CKS

        title, content, metadata = finding.to_cks_entry()

        with CKS() as cks:
            cks.ingest_pattern(title=title, content=content, metadata=metadata)
        return True
    except Exception as e:
        print(f"[diagnostic_writer] CKS error: {e}", file=sys.stderr)
        return False
