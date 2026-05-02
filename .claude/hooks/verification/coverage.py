"""Deterministic coverage checks on weak/indirect verdicts.

Assesses evidence quality across four dimensions: peer coverage, direct-vs-indirect
evidence, staleness, and contradiction. Rule-based only — no LLM, no subprocess.

Only called for SILENT or weak verdicts. SUPPORTED/SELF_VERIFIED verdicts skip coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "CoverageDimension",
    "CoverageReport",
    "assess_coverage",
]

# ---------------------------------------------------------------------------
# Dimension weights (must sum to 1.0)
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "peer_coverage": 0.35,
    "direct_vs_indirect": 0.30,
    "staleness": 0.15,
    "contradiction": 0.20,
}

# Tools that mutate files — used for staleness detection
_MUTATION_TOOLS = frozenset({"Edit", "Write"})

# Tools that read artifacts — evidence from these can go stale
_ARTIFACT_TOOLS = frozenset({"Read", "Grep", "Glob"})

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoverageDimension:
    """Single dimension of evidence coverage."""

    name: str
    score: float  # 0.0 to 1.0
    detail: str


@dataclass(frozen=True)
class CoverageReport:
    """Coverage analysis for a single verdict."""

    verdict_id: str | int
    overall_score: float
    dimensions: tuple[CoverageDimension, ...]
    recommendation: str  # "sufficient" | "weak" | "insufficient" | "contradicted"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_coverage(
    verdict: Any,
    claim: Any,
    all_verdicts: list[Any],
    tool_events: list[dict[str, Any]],
) -> CoverageReport:
    """Run all coverage dimensions for a single verdict.

    Called only for SILENT or weak verdicts (not SUPPORTED/SELF_VERIFIED).

    Args:
        verdict: VerificationVerdict with .claim_id, .status
        claim: Claim object with .id, .text, .targets
        all_verdicts: All verdicts from the same build_verdicts() call
        tool_events: Tool event dictionaries for evidence inspection
    """
    verdict_id = getattr(verdict, "claim_id", "")

    dimensions = (
        _check_peer_coverage(claim, verdict, all_verdicts),
        _check_direct_vs_indirect(claim, tool_events),
        _check_staleness(claim, tool_events),
        _check_contradiction(claim, all_verdicts),
    )

    # Check for contradiction override first
    contradiction_dim = dimensions[3]
    if contradiction_dim.score < 0.5 and "contradict" in contradiction_dim.detail.lower():
        return CoverageReport(
            verdict_id=verdict_id,
            overall_score=0.0,
            dimensions=dimensions,
            recommendation="contradicted",
        )

    # Weighted score
    overall = sum(
        _WEIGHTS[dim.name] * dim.score
        for dim in dimensions
        if dim.name in _WEIGHTS
    )

    if overall >= 0.7:
        rec = "sufficient"
    elif overall >= 0.4:
        rec = "weak"
    else:
        rec = "insufficient"

    return CoverageReport(
        verdict_id=verdict_id,
        overall_score=round(overall, 3),
        dimensions=dimensions,
        recommendation=rec,
    )


# ---------------------------------------------------------------------------
# Dimension checks
# ---------------------------------------------------------------------------


def _check_peer_coverage(
    claim: Any,
    verdict: Any,
    all_verdicts: list[Any],
) -> CoverageDimension:
    """Do sibling claims (from the same response) have SUPPORTED verdicts?

    If a compound claim was decomposed and 3/4 sub-claims are SUPPORTED,
    the 4th gets peer_coverage reflecting that ratio.
    """
    if not all_verdicts or len(all_verdicts) <= 1:
        return CoverageDimension("peer_coverage", 0.0, "no peer claims")

    supported = 0
    total = 0
    my_id = getattr(verdict, "claim_id", None)

    for v in all_verdicts:
        v_id = getattr(v, "claim_id", None)
        if v_id == my_id:
            continue
        total += 1
        status = _status_str(v)
        if status == "SUPPORTED" or status == "SELF_VERIFIED":
            supported += 1

    if total == 0:
        return CoverageDimension("peer_coverage", 0.0, "no peer claims")

    ratio = supported / total
    return CoverageDimension(
        "peer_coverage",
        round(ratio, 3),
        f"{supported}/{total} peer claims supported",
    )


def _check_direct_vs_indirect(
    claim: Any,
    tool_events: list[dict[str, Any]],
) -> CoverageDimension:
    """Classify evidence as direct vs indirect.

    Direct: claim targets appear in tool output text.
    Indirect: related entities appear but not the specific targets.
    None: no relevant events at all.
    """
    if not tool_events:
        return CoverageDimension("direct_vs_indirect", 0.0, "no tool events")

    targets = [t.lower() for t in getattr(claim, "targets", []) if t]
    if not targets:
        return CoverageDimension("direct_vs_indirect", 0.0, "no targets in claim")

    direct_hit = False
    indirect_hit = False

    for evt in tool_events:
        output = str(evt.get("output", "")).lower()
        command = str(evt.get("command", "")).lower()
        combined = output + " " + command

        for t in targets:
            if t in combined:
                direct_hit = True
                break

        if not direct_hit:
            # Check for partial/indirect matches — shared path components, etc.
            for t in targets:
                parts = t.replace("/", " ").replace("\\", " ").split()
                if any(p in combined for p in parts if len(p) > 3):
                    indirect_hit = True

    if direct_hit:
        return CoverageDimension("direct_vs_indirect", 0.8, "direct target match in evidence")
    if indirect_hit:
        return CoverageDimension("direct_vs_indirect", 0.4, "indirect/partial target match")
    return CoverageDimension("direct_vs_indirect", 0.0, "no target match in evidence")


def _check_staleness(
    claim: Any,
    tool_events: list[dict[str, Any]],
) -> CoverageDimension:
    """Detect stale evidence: tool events that predate the most recent file mutation.

    Evidence from Read/Glob/Grep is stale if a subsequent Edit/Write targeted
    the same path.
    """
    if not tool_events:
        return CoverageDimension("staleness", 0.5, "no events to check")

    # Find mutation timestamps by target path
    mutated_paths: dict[str, str] = {}
    read_timestamps: dict[str, str] = {}

    for evt in tool_events:
        tool = evt.get("name", "")
        timestamp = evt.get("timestamp", "")
        target = str(evt.get("target", "") or evt.get("command", "")).lower()

        if tool in _MUTATION_TOOLS and target:
            mutated_paths[target] = timestamp
        elif tool in _ARTIFACT_TOOLS and target:
            read_timestamps[target] = timestamp

    if not mutated_paths:
        return CoverageDimension("staleness", 1.0, "no mutations detected")

    # Check if any read target was subsequently mutated
    stale_reads = 0
    total_reads = max(len(read_timestamps), 1)

    for read_path, read_ts in read_timestamps.items():
        for mut_path, mut_ts in mutated_paths.items():
            if _paths_overlap(read_path, mut_path) and read_ts < mut_ts:
                stale_reads += 1
                break

    if stale_reads == 0:
        return CoverageDimension("staleness", 1.0, "no stale evidence detected")

    freshness_ratio = 1.0 - (stale_reads / total_reads)
    return CoverageDimension(
        "staleness",
        round(freshness_ratio, 3),
        f"{stale_reads}/{total_reads} reads may be stale",
    )


def _check_contradiction(
    claim: Any,
    all_verdicts: list[Any],
) -> CoverageDimension:
    """Scan for REFUTED sibling claims that contradict this claim."""
    my_text = getattr(claim, "text", "").lower()
    my_id = getattr(claim, "id", None)

    for v in all_verdicts:
        if getattr(v, "claim_id", None) == my_id:
            continue
        status = _status_str(v)
        if status == "REFUTED":
            return CoverageDimension(
                "contradiction",
                0.0,
                "refuted sibling claim detected",
            )

    return CoverageDimension("contradiction", 1.0, "no contradictions")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _status_str(verdict: Any) -> str:
    """Extract status string from a verdict."""
    status = getattr(verdict, "status", None)
    if status is None:
        return ""
    if isinstance(status, str):
        return status
    return str(status.value) if hasattr(status, "value") else str(status)


def _paths_overlap(a: str, b: str) -> bool:
    """Check if two paths share a meaningful prefix (overlap detection)."""
    # Normalize separators
    a_norm = a.replace("\\", "/").rstrip("/")
    b_norm = b.replace("\\", "/").rstrip("/")

    if a_norm in b_norm or b_norm in a_norm:
        return True

    # Check shared filename
    a_file = a_norm.rsplit("/", 1)[-1] if "/" in a_norm else a_norm
    b_file = b_norm.rsplit("/", 1)[-1] if "/" in b_norm else b_norm
    return a_file == b_file and len(a_file) > 3
