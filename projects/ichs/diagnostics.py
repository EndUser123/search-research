import logging
from datetime import datetime, timedelta
from typing import Any

import openai

from .config import EnhancedConfig as Config
from .database import Database

logger = logging.getLogger(__name__)


class Diagnostics:
    """AI-powered failure analysis for iCHS."""

    def __init__(self, config: Config, database: Database):
        """Initialize the diagnostics module.

        Args:
            config: Configuration object
            database: Database instance for accessing historical data
        """
        self.config = config
        self.database = database

        # Initialize OpenAI client if configured
        self.openai_client: Any | None = None
        api_key = config.get("ai", "openai_api_key", "")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.ai_enabled = True
        else:
            self.ai_enabled = False
            logger.warning("OpenAI API key not configured - AI features disabled")

        # Configure AI model
        self.ai_model = config.get("ai", "model", "gpt-3.5-turbo")
        self.max_tokens = config.get("ai", "max_tokens", 1000)

    def analyze_failure(self, run_id: int) -> dict[str, Any]:
        """Analyze a specific failed run.

        Args:
            run_id: ID of the failed run to analyze

        Returns:
            Dictionary containing failure analysis results
        """
        logger.info(f"Analyzing failure for run {run_id}")

        # Get run details
        run = self.database.get_run_by_id(run_id)
        if not run:
            return {
                "run_id": run_id,
                "error": "Run not found",
                "analysis": None,
                "recommendations": [],
            }

        # Get issues for this run
        issues = self.database.get_issues_by_run(run_id)

        # Analyze the failure
        analysis = self._analyze_failure_pattern(run, issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(run, issues, analysis)

        # Try AI analysis if enabled
        ai_analysis = None
        if self.ai_enabled and issues:
            try:
                ai_analysis = self._ai_analyze_failure(run, issues)
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")

        return {
            "run_id": run_id,
            "run_details": run,
            "issues": issues,
            "analysis": analysis,
            "ai_analysis": ai_analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }

    def _analyze_failure_pattern(
        self, run: dict[str, Any], issues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze failure patterns.

        Args:
            run: Run dictionary
            issues: List of issue dictionaries

        Returns:
            Dictionary with pattern analysis
        """
        analysis = {
            "failure_type": self._determine_failure_type(run, issues),
            "severity_distribution": self._analyze_severity_distribution(issues),
            "category_distribution": self._analyze_category_distribution(issues),
            "file_distribution": self._analyze_file_distribution(issues),
            "rule_distribution": self._analyze_rule_distribution(issues),
            "complexity_indicators": self._analyze_complexity_indicators(issues),
            "recurring_issues": self._find_recurring_issues(issues),
        }

        return analysis

    def _determine_failure_type(
        self, run: dict[str, Any], issues: list[dict[str, Any]]
    ) -> str:
        """Determine the type of failure.

        Args:
            run: Run dictionary
            issues: List of issue dictionaries

        Returns:
            Failure type string
        """
        exit_code = run.get("exit_code", 0)

        if exit_code != 0:
            return "execution_error"

        if not issues:
            return "no_issues"

        # Check for critical issues
        critical_issues = [i for i in issues if i.get("severity") == "error"]
        if critical_issues:
            return "critical_issues"

        # Check for warnings
        warning_issues = [i for i in issues if i.get("severity") == "warning"]
        if warning_issues:
            return "warning_issues"

        return "info_issues"

    def _analyze_severity_distribution(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Analyze distribution of issue severities.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with severity counts
        """
        distribution: dict[str, int] = {}
        for issue in issues:
            severity = issue.get("severity", "info")
            distribution[severity] = distribution.get(severity, 0) + 1

        return distribution

    def _analyze_category_distribution(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Analyze distribution of issue categories.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with category counts
        """
        distribution: dict[str, int] = {}
        for issue in issues:
            category = issue.get("parser", "unknown")
            distribution[category] = distribution.get(category, 0) + 1

        return distribution

    def _analyze_file_distribution(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Analyze distribution of issues by file.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with file issue counts
        """
        distribution: dict[str, int] = {}
        for issue in issues:
            file_path = issue.get("file_path", "unknown")
            distribution[file_path] = distribution.get(file_path, 0) + 1

        return distribution

    def _analyze_rule_distribution(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Analyze distribution of rules.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with rule counts
        """
        distribution: dict[str, int] = {}
        for issue in issues:
            rule_id = issue.get("rule_id", "unknown")
            distribution[rule_id] = distribution.get(rule_id, 0) + 1

        return distribution

    def _analyze_complexity_indicators(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze complexity indicators in the issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with complexity indicators
        """
        indicators = {
            "total_issues": len(issues),
            "unique_files": len(set(i.get("file_path", "") for i in issues)),
            "unique_rules": len(set(i.get("rule_id", "") for i in issues)),
            "average_issues_per_file": 0.0,
            "complexity_score": 0,
        }

        if indicators["unique_files"] > 0:
            indicators["average_issues_per_file"] = (
                indicators["total_issues"] / indicators["unique_files"]
            )

        # Calculate complexity score (0-10)
        if indicators["total_issues"] == 0:
            indicators["complexity_score"] = 0
        elif indicators["total_issues"] <= 5:
            indicators["complexity_score"] = 2
        elif indicators["total_issues"] <= 15:
            indicators["complexity_score"] = 4
        elif indicators["total_issues"] <= 30:
            indicators["complexity_score"] = 6
        elif indicators["total_issues"] <= 50:
            indicators["complexity_score"] = 8
        else:
            indicators["complexity_score"] = 10

        return indicators

    def _find_recurring_issues(
        self, issues: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find recurring issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            List of recurring issue dictionaries
        """
        issue_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for issue in issues:
            rule_id = str(issue.get("rule_id", ""))
            file_path = str(issue.get("file_path", ""))
            key = (rule_id, file_path)
            if key not in issue_groups:
                issue_groups[key] = []
            issue_groups[key].append(issue)

        # Flatten groups and return only issues from groups with more than one occurrence
        return [
            issue
            for group in issue_groups.values()
            for issue in group
            if len(group) > 1
        ]

    def _generate_recommendations(
        self,
        run: dict[str, Any],
        issues: list[dict[str, Any]],
        analysis: dict[str, Any],
    ) -> list[str]:
        """Generate recommendations based on failure analysis.

        Args:
            run: Run dictionary
            issues: List of issue dictionaries
            analysis: Failure analysis results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # General failure type recommendations
        failure_type = analysis.get("failure_type", "unknown")
        if failure_type == "execution_error":
            recommendations.append(
                "Command execution failed. Check command syntax and dependencies."
            )
        elif failure_type == "critical_issues":
            recommendations.append("Critical issues found. Address these immediately.")
        elif failure_type == "warning_issues":
            recommendations.append(
                "Warning issues detected. Consider fixing these to improve code quality."
            )

        # Complexity-based recommendations
        complexity = analysis.get("complexity_indicators", {})
        if complexity.get("complexity_score", 0) >= 8:
            recommendations.append(
                "High complexity detected. Consider refactoring and breaking down large files."
            )

        # Recurring issues recommendations
        recurring = analysis.get("recurring_issues", [])
        if recurring:
            recommendations.append(
                f"Found {len(recurring)} recurring issue(s). Focus on fixing root causes."
            )

        # Category-specific recommendations
        categories = analysis.get("category_distribution", {})
        for category, count in categories.items():
            if category == "ruff" and count > 10:
                recommendations.append(
                    "Many Ruff issues found. Consider running Ruff auto-fix for safe fixes."
                )
            elif category == "bandit" and count > 0:
                recommendations.append(
                    "Security issues detected. Review and fix these immediately."
                )

        return recommendations

    def _ai_analyze_failure(
        self, run: dict[str, Any], issues: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Use AI to analyze the failure.

        Args:
            run: Run dictionary
            issues: List of issue dictionaries

        Returns:
            AI analysis results or None if failed
        """
        if not self.ai_enabled:
            return None

        try:
            # Prepare prompt
            prompt = self._prepare_ai_prompt(run, issues)

            # Call OpenAI API (guarded)
            client = self.openai_client
            if client is None:
                return None
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python code quality analyst. Analyze the provided code quality issues and provide insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,
            )

            # Parse response
            ai_content = response.choices[0].message.content
            return {
                "analysis": ai_content,
                "model_used": self.ai_model,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    def _prepare_ai_prompt(
        self, run: dict[str, Any], issues: list[dict[str, Any]]
    ) -> str:
        """Prepare prompt for AI analysis.

        Args:
            run: Run dictionary
            issues: List of issue dictionaries

        Returns:
            Formatted prompt string
        """
        # Group issues by file for better analysis
        issues_by_file: dict[str, list[dict[str, Any]]] = {}
        for issue in issues:
            file_path = issue.get("file_path", "unknown")
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)

        # Format issues for prompt
        formatted_issues = []
        for file_path, file_issues in issues_by_file.items():
            formatted_issues.append(f"File: {file_path}")
            for issue in file_issues[:10]:  # Limit to first 10 issues per file
                formatted_issues.append(
                    f"  - {issue.get('rule_id', 'N/A')}: {issue.get('message', 'N/A')} (Line {issue.get('line_number', 'N/A')})"
                )

        # Create prompt
        prompt = f"""
Analyze the following code quality issues and provide insights:

Command: {run.get("command", "N/A")}
Exit Code: {run.get("exit_code", "N/A")}
Duration: {run.get("duration", "N/A")}s

Issues Found:
{chr(10).join(formatted_issues)}

Please provide:
1. Overall assessment of the code quality issues
2. Most critical issues that need immediate attention
3. Potential root causes of these issues
4. Specific recommendations for improvement
5. Suggestions for preventing similar issues in the future

Be concise and actionable in your response.
"""

        return prompt

    def get_failure_summary(self, days: int = 7) -> dict[str, Any]:
        """Get summary of failures over the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with failure summary
        """
        logger.info(f"Getting failure summary for the last {days} days")

        # Get recent runs
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_runs = self.database.get_runs_by_date_range(cutoff_date, datetime.now())

        # Analyze failures
        failed_runs = [run for run in recent_runs if not run.get("success", True)]

        summary: dict[str, Any] = {
            "period_days": days,
            "total_runs": len(recent_runs),
            "failed_runs": len(failed_runs),
            "failure_rate": (len(failed_runs) / len(recent_runs) * 100)
            if recent_runs
            else 0,
            "failure_types": {},
            "common_issues": {},
            "ai_insights": [],
        }

        # Analyze failure types
        for run in failed_runs:
            issues = self.database.get_issues_by_run(run["id"])
            failure_type = self._determine_failure_type(run, issues)
            summary["failure_types"][failure_type] = (
                summary["failure_types"].get(failure_type, 0) + 1
            )

            # Count common issues
            for issue in issues:
                rule_id = issue.get("rule_id", "unknown")
                summary["common_issues"][rule_id] = (
                    summary["common_issues"].get(rule_id, 0) + 1
                )

        # Get AI insights for top failures
        if self.ai_enabled and failed_runs:
            top_failures = sorted(
                failed_runs, key=lambda x: x.get("duration", 0), reverse=True
            )[:3]
            for run in top_failures:
                issues = self.database.get_issues_by_run(run["id"])
                if issues:
                    ai_analysis = self._ai_analyze_failure(run, issues)
                    if ai_analysis:
                        summary["ai_insights"].append(
                            {"run_id": run["id"], "ai_analysis": ai_analysis}
                        )

        return summary
