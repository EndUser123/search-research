"""Gap analysis and follow-up query generation for saturation detection."""

from dataclasses import dataclass, field
from typing import List, Set
from enum import Enum


class GapType(Enum):
    """Types of coverage gaps."""
    MISSING_SOURCE_TYPE = "missing_source_type"
    LOW_DOMAIN_DIVERSITY = "low_domain_diversity"
    LOW_TOPIC_COVERAGE = "low_topic_coverage"


@dataclass
class CoverageGap:
    """A gap in research coverage."""
    gap_type: GapType
    description: str
    severity: float  # 0.0 to 1.0
    metadata: dict = field(default_factory=dict)


class GapAnalyzer:
    """Analyze coverage gaps and generate follow-up queries."""

    # Minimum thresholds for healthy coverage
    MIN_SOURCE_TYPES = 3
    MIN_DOMAINS = 3
    MIN_TOPICS = 2

    # Source type priority for gap filling
    SOURCE_TYPE_PRIORITY = {
        "academic": "paper research academic arxiv study",
        "docs": "documentation official guide reference",
        "community": "stackoverflow reddit discussion community",
        "video": "video tutorial youtube course",
        "blog": "blog article tutorial guide",
        "vendor": "official vendor documentation guide",
    }

    def detect_gaps(
        self,
        results,
        topics: Set[str],
        source_types: Set[str],
        domains: Set[str]
    ) -> List[CoverageGap]:
        """Detect coverage gaps from current results."""
        gaps = []

        # Check source type diversity
        if len(source_types) < self.MIN_SOURCE_TYPES:
            missing_types = self._get_missing_source_types(source_types)
            for missing in missing_types:
                gaps.append(CoverageGap(
                    gap_type=GapType.MISSING_SOURCE_TYPE,
                    description=f"Missing {missing} sources",
                    severity=0.7,
                    metadata={"missing_type": missing}
                ))

        # Check domain diversity
        if len(domains) < self.MIN_DOMAINS:
            severity = 0.5 + (1.0 - len(domains) / self.MIN_DOMAINS) * 0.4
            gaps.append(CoverageGap(
                gap_type=GapType.LOW_DOMAIN_DIVERSITY,
                description=f"Low domain diversity ({len(domains)} domains)",
                severity=severity,
                metadata={"domain_count": len(domains), "domains": list(domains)}
            ))

        # Check topic coverage
        if len(topics) < self.MIN_TOPICS:
            severity = 0.6 + (1.0 - len(topics) / self.MIN_TOPICS) * 0.3
            gaps.append(CoverageGap(
                gap_type=GapType.LOW_TOPIC_COVERAGE,
                description=f"Low topic coverage ({len(topics)} topics)",
                severity=severity,
                metadata={"topic_count": len(topics)}
            ))

        return sorted(gaps, key=lambda g: g.severity, reverse=True)

    def _get_missing_source_types(self, current_types: Set[str]) -> List[str]:
        """Get missing high-priority source types."""
        priority_order = ["academic", "docs", "community", "video", "blog", "vendor"]
        missing = [t for t in priority_order if t not in current_types]
        return missing[:3]  # Return top 3 missing

    def generate_follow_up_query(self, original_query: str, gap: CoverageGap) -> str:
        """Generate a follow-up query to address a specific gap."""
        if gap.gap_type == GapType.MISSING_SOURCE_TYPE:
            return self._generate_source_type_query(original_query, gap)
        elif gap.gap_type == GapType.LOW_DOMAIN_DIVERSITY:
            return self._generate_domain_diversity_query(original_query, gap)
        elif gap.gap_type == GapType.LOW_TOPIC_COVERAGE:
            return self._generate_topic_exploration_query(original_query, gap)
        return original_query

    def _generate_source_type_query(self, original_query: str, gap: CoverageGap) -> str:
        """Generate query targeting missing source type."""
        missing_type = gap.metadata.get("missing_type", "academic")
        type_terms = self.SOURCE_TYPE_PRIORITY.get(missing_type, missing_type)

        # For academic, add research-focused terms
        if missing_type == "academic":
            return f"{original_query} paper research academic arxiv"
        elif missing_type == "video":
            return f"{original_query} video tutorial youtube"
        elif missing_type == "community":
            return f"{original_query} stackoverflow reddit discussion"
        else:
            return f"{original_query} {type_terms}"

    def _generate_domain_diversity_query(self, original_query: str, gap: CoverageGap) -> str:
        """Generate query seeking diverse sources."""
        # Add "alternative" or "different" to seek new perspectives
        variations = [
            f"{original_query} alternative",
            f"{original_query} different sources",
            f"{original_query} tutorial guide",
        ]
        return variations[0]  # Return first variation

    def _generate_topic_exploration_query(self, original_query: str, gap: CoverageGap) -> str:
        """Generate broader query to explore more topics."""
        # Add exploratory terms to broaden coverage
        variations = [
            f"{original_query} overview",
            f"{original_query} guide tutorial",
            f"{original_query} examples",
        ]
        return variations[0]  # Return first variation
