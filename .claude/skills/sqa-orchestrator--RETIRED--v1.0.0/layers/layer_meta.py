"""Meta-Synthesis Layer: consensus detection, blind-spot detection, evidence quality."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from findings.models import EvidenceTier, Finding, Layer, Severity, _severity_order


def run_meta(all_findings: list[Finding]) -> list[Finding]:
    """Run meta-synthesis on all findings from all layers.

    1. Consensus detection: 2+ layers agree on same file:line:category
    2. Blind-spot detection: layer was available but found nothing
    3. Evidence quality check per evidence-tiers
    """
    meta_findings: list[Finding] = []

    # Consensus detection
    consensus_findings = _detect_consensus(all_findings)
    meta_findings.extend(consensus_findings)

    # Blind-spot detection
    blind_findings = _detect_blind_spots(all_findings)
    meta_findings.extend(blind_findings)

    # Evidence quality check
    quality_findings = _check_evidence_quality(all_findings)
    meta_findings.extend(quality_findings)

    return meta_findings


def _detect_consensus(all_findings: list[Finding]) -> list[Finding]:
    """Find findings agreed on by 2+ layers at same file:line:category."""
    # Group by (file, line, category)
    groups: dict[tuple, list[Finding]] = defaultdict(list)
    for f in all_findings:
        if f.location:
            groups[(f.location, f.category)].append(f)

    consensus_findings: list[Finding] = []
    for (loc, cat), finds in groups.items():
        layers = {f.layer for f in finds}
        if len(layers) >= 2:
            max_severity = max(finds, key=lambda f: _severity_order(f.severity)).severity
            consensus_findings.append(
                Finding(
                    finding_id=f"META-CONSENSUS-{loc}-{cat}".replace(":", "-").replace("/", "-"),
                    severity=max_severity,  # Use highest severity from consensus
                    layer=Layer.META,
                    title=f"Consensus: {len(layers)} layers agree on same issue",
                    description=f"Issue at {loc} (category={cat}) found by {len(layers)} layers: {', '.join(l.value for l in layers)}",
                    location=loc,
                    evidence_tier=EvidenceTier.T3,
                    consensus=len(layers),
                    category=cat,
                )
            )
    return consensus_findings


def _detect_blind_spots(all_findings: list[Finding]) -> list[Finding]:
    """Detect quality categories where a layer WAS available but found nothing.

    A blind-spot finding is NOT generated when a layer was skipped via D5 graceful degradation.
    We only flag when a layer ran but produced zero findings for its expected categories.
    """
    meta_findings: list[Finding] = []

    # Categories each layer should cover
    layer_categories = {
        Layer.L1_SYNTACTIC: {"syntax", "type", "structure"},
        Layer.L2_SEMANTIC: {"test", "diagnosis"},
        Layer.L3_STRUCTURAL: {"structure", "security", "safety"},
        Layer.L4_REQUIREMENTS: {"requirements"},
        Layer.L5_SECURITY: {"security", "safety"},
        Layer.L6_PERFORMANCE: {"performance"},
        Layer.L7_OPERATIONAL: {"operational"},
    }

    # What categories were actually found by each layer
    layer_found_categories: dict[Layer, set[str]] = defaultdict(set)
    for f in all_findings:
        if f.layer in layer_categories:
            layer_found_categories[f.layer].add(f.category)

    # Check for blind spots
    for layer, expected_cats in layer_categories.items():
        found_cats = layer_found_categories.get(layer, set())
        missing_cats = expected_cats - found_cats
        if missing_cats:
            # Layer ran but found nothing in these categories
            for cat in missing_cats:
                meta_findings.append(
                    Finding(
                        finding_id=f"META-BLIND-{layer.value}-{cat}",
                        severity=Severity.MEDIUM,
                        layer=Layer.META,
                        title=f"Blind-spot: {layer.value} available but found no {cat} issues",
                        description=f"Layer {layer.value} was available but produced no findings for category '{cat}'. Available categories: {expected_cats}, Found: {found_cats}",
                        evidence_tier=EvidenceTier.T4,
                        category=cat,
                    )
                )

    return meta_findings


def _check_evidence_quality(all_findings: list[Finding]) -> list[Finding]:
    """Cap confidence per evidence-tiers spec."""
    quality_findings: list[Finding] = []

    for f in all_findings:
        if f.evidence_tier == EvidenceTier.T4:
            # Heuristic finding — flag for review
            quality_findings.append(
                Finding(
                    finding_id=f"META-EVIDENCE-Q-{f.finding_id}",
                    severity=Severity.LOW,
                    layer=Layer.META,
                    title=f"Evidence quality cap: {f.finding_id} uses T4 heuristic",
                    description=f"Finding {f.finding_id} capped at T4 (heuristic) — verify with T1/T2 evidence",
                    evidence_tier=EvidenceTier.T4,
                    category="evidence",
                )
            )

    return quality_findings
