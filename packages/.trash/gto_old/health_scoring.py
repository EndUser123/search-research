"""
Health Scoring for /gto

Calculates aggregate health score from detected gaps across categories.

Scoring Categories:
- Test Coverage (30%): Missing tests, failing tests, coverage gaps
- Documentation (20%): Outdated docs, missing README, incomplete SKILL.md
- Git State (20%): Uncommitted changes, stale branches, merge conflicts
- Dependencies (15%): Outdated packages, security issues
- Code Quality (15%): Linting issues, type errors, complexity

Score: 0-100 scale, where 100 = no critical/high gaps detected
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CategoryScore:
    """Score breakdown for a single category."""

    name: str
    score: int
    max_score: int
    weight: float
    gap_count: int  # Total gaps in this category
    critical_count: int  # Critical severity gaps
    high_count: int  # High severity gaps
    medium_count: int  # Medium severity gaps
    low_count: int  # Low severity gaps


@dataclass
class HealthScore:
    """Aggregate health score with category breakdowns."""

    overall_score: int
    max_score: int
    categories: list[CategoryScore]
    total_gaps: int
    critical_gaps: int
    high_gaps: int
    recommendation: str


class HealthScoringEngine:
    """
    Calculate project health score from detected gaps.

    Scoring methodology:
    - Start with 100 points per category
    - Deduct points based on gap severity:
      - Critical: -20 points
      - High: -10 points
      - Medium: -5 points
      - Low: -2 points
    - Category floor: 0 (can't go negative)
    - Overall score: weighted average of categories
    """

    # Category weights (must sum to 1.0)
    CATEGORY_WEIGHTS = {
        "tests": 0.30,  # Test coverage
        "documentation": 0.20,  # Documentation completeness
        "git": 0.20,  # Git state cleanliness
        "dependencies": 0.15,  # Dependency freshness
        "code_quality": 0.15,  # Code quality indicators
    }

    # Severity point deductions
    SEVERITY_DEDUCTIONS = {
        "critical": -20,
        "high": -10,
        "medium": -5,
        "low": -2,
    }

    def calculate_health_score(
        self,
        gaps: list[dict[str, Any]],
        git_context: dict[str, Any] | None = None,
    ) -> HealthScore:
        """
        Calculate health score from detected gaps.

        Args:
            gaps: List of detected gaps, each with 'severity' and 'category' keys
            git_context: Optional git state from git_context.py

        Returns:
            HealthScore with overall score and category breakdowns
        """
        # Add synthetic gap for uncommitted files before categorization
        all_gaps = list(gaps)
        if git_context and git_context.get("has_uncommitted_changes", False):
            modified_files = git_context.get("modified_files", [])
            # Format file list for the gap message
            if modified_files:
                file_list = ", ".join(modified_files[:5])  # Show up to 5 files
                if len(modified_files) > 5:
                    file_list += f" (+{len(modified_files) - 5} more)"
                message = f"{len(modified_files)} uncommitted file(s): {file_list}"
            else:
                message = "Uncommitted changes detected"

            all_gaps.append(
                {
                    "type": "uncommitted_files",
                    "severity": "high",
                    "message": message,
                    "turn": 0,
                }
            )

        # Categorize gaps (including synthetic ones)
        categorized_gaps = self._categorize_gaps(all_gaps)

        # Calculate category scores
        categories = []
        for category_name, weight in self.CATEGORY_WEIGHTS.items():
            category_gaps = categorized_gaps.get(category_name, [])
            category_score = self._calculate_category_score(
                category_name,
                category_gaps,
                weight,
                git_context,
            )
            categories.append(category_score)

        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(categories)

        # Generate recommendation
        recommendation = self._generate_recommendation(overall_score, categories)

        # Count total gaps by severity (from all_gaps including synthetic)
        critical_count = sum(1 for gap in all_gaps if gap.get("severity") == "critical")
        high_count = sum(1 for gap in all_gaps if gap.get("severity") == "high")

        return HealthScore(
            overall_score=overall_score,
            max_score=100,
            categories=categories,
            total_gaps=len(all_gaps),
            critical_gaps=critical_count,
            high_gaps=high_count,
            recommendation=recommendation,
        )

    def _categorize_gaps(
        self, gaps: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Categorize gaps into health scoring categories.

        Gap categories determined by severity and gap type:
        - tests: Test-related gaps (missing tests, failing tests, coverage)
        - documentation: Doc-related gaps (README, SKILL.md, CLAUDE.md)
        - git: Git state gaps (uncommitted, conflicts, stale branches)
        - dependencies: Dependency gaps (outdated packages, security)
        - code_quality: Quality gaps (linting, types, complexity)
        """
        categorized = {
            "tests": [],
            "documentation": [],
            "git": [],
            "dependencies": [],
            "code_quality": [],
        }

        for gap in gaps:
            gap_type = gap.get("type", "").lower()
            severity = gap.get("severity", "low").lower()

            # Categorize based on gap type and severity
            if any(
                keyword in gap_type for keyword in ["test", "coverage", "pytest", "tdd"]
            ):
                categorized["tests"].append(gap)
            elif any(
                keyword in gap_type
                for keyword in ["doc", "readme", "skill.md", "claude.md"]
            ):
                categorized["documentation"].append(gap)
            elif any(
                keyword in gap_type for keyword in ["git", "commit", "branch", "merge"]
            ):
                categorized["git"].append(gap)
            elif any(
                keyword in gap_type
                for keyword in ["dependenc", "package", "pip", "npm"]
            ):
                categorized["dependencies"].append(gap)
            elif any(
                keyword in gap_type
                for keyword in ["lint", "type", "complex", "ruff", "mypy"]
            ):
                categorized["code_quality"].append(gap)
            else:
                # Default to code_quality for unspecified gaps
                categorized["code_quality"].append(gap)

        return categorized

    def _calculate_category_score(
        self,
        category_name: str,
        gaps: list[dict[str, Any]],
        weight: float,
        git_context: dict[str, Any] | None = None,
    ) -> CategoryScore:
        """Calculate score for a single category."""
        # Start with perfect score
        score = 100

        # Count gaps by severity
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for gap in gaps:
            severity = gap.get("severity", "low").lower()
            if severity in counts:
                counts[severity] += 1

        # Apply deductions (with category floor at 0)
        for severity, count in counts.items():
            deduction = self.SEVERITY_DEDUCTIONS.get(severity, 0)
            score += deduction * count

        score = max(0, score)  # Floor at 0

        return CategoryScore(
            name=category_name.capitalize(),
            score=score,
            max_score=100,
            weight=weight,
            gap_count=len(gaps),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
        )

    def _calculate_overall_score(self, categories: list[CategoryScore]) -> int:
        """Calculate weighted overall score from categories."""
        total_weighted_score = sum(cat.score * cat.weight for cat in categories)
        return int(total_weighted_score)

    def _generate_recommendation(
        self,
        overall_score: int,
        categories: list[CategoryScore],
    ) -> str:
        """Generate text recommendation based on score."""
        if overall_score >= 90:
            return "Excellent health - no immediate action needed"
        elif overall_score >= 80:
            return "Good health - address high-priority gaps when convenient"
        elif overall_score >= 70:
            return "Fair health - recommend addressing high-severity gaps soon"
        elif overall_score >= 60:
            return "Declining health - critical and high gaps need attention"
        else:
            # Find worst category
            worst_category = min(categories, key=lambda c: c.score)
            return f"Poor health - focus on {worst_category.name.lower()} ({worst_category.score}/100)"

    def format_health_score(self, health: HealthScore) -> str:
        """
        Format health score for display.

        Returns multi-line string with score and category breakdowns.
        """
        lines = [
            f"**Project Health: {health.overall_score}/100**",
            "",
            "**Category Breakdown:**",
        ]

        for cat in health.categories:
            gap_summary = []
            if cat.critical_count > 0:
                gap_summary.append(f"{cat.critical_count} critical")
            if cat.high_count > 0:
                gap_summary.append(f"{cat.high_count} high")
            if cat.medium_count > 0:
                gap_summary.append(f"{cat.medium_count} medium")
            if cat.low_count > 0:
                gap_summary.append(f"{cat.low_count} low")

            gap_str = ", ".join(gap_summary) if gap_summary else "No gaps"

            # Format: "Tests: 80/100 (weight: 30%) - 3 gaps (1 critical, 2 high)"
            lines.append(
                f"- {cat.name}: {cat.score}/100 "
                f"(weight: {int(cat.weight * 100)}%) - "
                f"{cat.gap_count} gaps ({gap_str})"
            )

        lines.append("")
        lines.append(f"**Recommendation**: {health.recommendation}")

        # Add urgency indicator
        if health.critical_gaps > 0:
            lines.append("")
            lines.append(
                f"⚠️  {health.critical_gaps} critical gap(s) require immediate attention"
            )
        elif health.high_gaps > 0:
            lines.append("")
            lines.append(
                f"⚡ {health.high_gaps} high-severity gap(s) should be addressed soon"
            )

        return "\n".join(lines)


# Convenience function for quick scoring
def calculate_health_score(
    gaps: list[dict[str, Any]],
    git_context: dict[str, Any] | None = None,
) -> HealthScore:
    """
    Quick access to health scoring.

    Args:
        gaps: List of detected gaps with 'severity' and 'category' keys
        git_context: Optional git state from git_context.py

    Returns:
        HealthScore with overall score and breakdowns
    """
    engine = HealthScoringEngine()
    return engine.calculate_health_score(gaps, git_context)


def format_health_score(health: HealthScore) -> str:
    """
    Format health score for display.

    Args:
        health: HealthScore object

    Returns:
        Multi-line formatted string
    """
    engine = HealthScoringEngine()
    return engine.format_health_score(health)
