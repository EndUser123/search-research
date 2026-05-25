"""Optional types and helpers for upstream prompt/agent integration.

Non-authoritative — the pipeline is correct even if these are never used.
Not blocking, not mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from verification.coverage import CoverageReport
    from verification.engine import EnrichedVerdict

__all__ = [
    "DecompositionHint",
    "format_decomposition_hint",
    "format_coverage_summary",
]


@dataclass(frozen=True)
class DecompositionHint:
    """Hint for prompt builders about claim decomposition."""

    claim_text: str
    sub_obligations: tuple[str, ...]
    coverage_summary: str


def format_decomposition_hint(enriched: EnrichedVerdict) -> DecompositionHint | None:
    """Format an enriched verdict as a hint for prompt/agent consumption.

    Returns None if no decomposition occurred.
    """
    if enriched.decomposition is None or not enriched.decomposition.is_compound:
        return None

    sub_texts = tuple(sc.text for sc in enriched.decomposition.sub_claims)
    coverage_text = format_coverage_summary(enriched.coverage) if enriched.coverage else "no coverage data"

    return DecompositionHint(
        claim_text=enriched.decomposition.original_claim_id,
        sub_obligations=sub_texts,
        coverage_summary=coverage_text,
    )


def format_coverage_summary(report: CoverageReport | None) -> str:
    """Format coverage report as human-readable summary."""
    if report is None:
        return "no coverage analysis"

    dims = "; ".join(
        f"{d.name}={d.score:.2f} ({d.detail})"
        for d in report.dimensions
    )
    return f"recommendation={report.recommendation}, score={report.overall_score:.3f} [{dims}]"
