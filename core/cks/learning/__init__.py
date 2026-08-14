"""CKS Learning System - Citation tracking and diagnostic findings.

This module provides structured citation parsing and diagnostic finding storage
for the Constitutional Knowledge System (CKS).

Example:
    from src.cks.learning import extract_citations, DiagnosticFinding, store_finding

    # Parse file:line citations from text
    citation = extract_citations("Bug in file.py:123")

    # Store diagnostic findings with file references
    finding = DiagnosticFinding(
        category="BUG",
        file_path="file.py",
        line_number=123,
        summary="Null pointer dereference",
        details="Function doesn't check for None",
        skill_source="rca",
    )
    store_finding(finding)

"""

from __future__ import annotations

from src.cks.learning.citation_parser import extract_citations
from src.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding

__all__ = ["DiagnosticFinding", "extract_citations", "store_finding"]
