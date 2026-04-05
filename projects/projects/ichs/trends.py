import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd  # type: ignore[import-untyped]
import seaborn as sns  # type: ignore[import-untyped]

from .config import EnhancedConfig as Config
from .database import Database

logger = logging.getLogger(__name__)


class Trends:
    """Handles trend analysis with pandas for iCHS."""

    def __init__(self, config: Config, database: Database):
        """Initialize the trends module.

        Args:
            config: Configuration object
            database: Database instance for accessing historical data
        """
        self.config = config
        self.database = database
        self.cache_dir = Path(config.get("trends", "cache_dir", "trends_cache"))
        self.cache_dir.mkdir(exist_ok=True)

        # Set up plotting style
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")

    def analyze_trends(self, days: int = 30) -> dict[str, Any]:
        """Analyze trends over the specified number of days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing trend analysis results
        """
        logger.info(f"Analyzing trends for the last {days} days")

        # Get performance summary (kept for possible future use)
        _ = self.database.get_performance_summary(days)

        # Get recent runs with detailed data
        recent_runs = self.database.get_recent_runs(limit=100)

        # Convert to DataFrame for analysis
        df = self._runs_to_dataframe(recent_runs)

        if df.empty:
            return {
                "period_days": days,
                "total_runs": 0,
                "trends": {},
                "recommendations": [],
                "timestamp": datetime.now().isoformat(),
            }

        # Filter to specified date range
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df["timestamp"] >= cutoff_date]

        # Analyze various trends
        trends = {
            "success_rate": self._analyze_success_rate_trend(df),
            "performance": self._analyze_performance_trend(df),
            "issue_trends": self._analyze_issue_trends(df),
            "category_trends": self._analyze_category_trends(df),
            "file_trends": self._analyze_file_trends(df),
        }

        # Generate recommendations
        recommendations = self._generate_trend_recommendations(trends)

        return {
            "period_days": days,
            "total_runs": len(df),
            "trends": trends,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }

    def _runs_to_dataframe(self, runs: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert runs list to pandas DataFrame.

        Args:
            runs: List of run dictionaries

        Returns:
            pandas DataFrame with run data
        """
        if not runs:
            return pd.DataFrame()

        # Convert timestamp strings to datetime objects
        df_data = []
        for run in runs:
            try:
                timestamp = datetime.fromisoformat(
                    run["timestamp"].replace("Z", "+00:00")
                )
                df_data.append(
                    {
                        "id": run["id"],
                        "timestamp": timestamp,
                        "command": run["command"],
                        "exit_code": run["exit_code"],
                        "duration": run["duration"],
                        "success": run["success"],
                        "cwd": run.get("cwd", ""),
                    }
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse run data: {e}")
                continue

        return pd.DataFrame(df_data)

    def _analyze_success_rate_trend(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze success rate trends.

        Args:
            df: DataFrame with run data

        Returns:
            Dictionary with success rate analysis
        """
        if df.empty:
            return {"current_rate": 0, "trend": "stable", "change": 0}

        # Calculate success rate by day
        df["date"] = df["timestamp"].dt.date
        daily_success = df.groupby("date")["success"].agg(["mean", "count"])

        # Calculate trend
        if len(daily_success) >= 7:
            # Compare last 7 days with previous 7 days
            recent = daily_success.tail(7)["mean"].mean()
            previous = (
                daily_success.head(7)["mean"].mean()
                if len(daily_success) >= 14
                else recent
            )

            change = ((recent - previous) / previous * 100) if previous > 0 else 0

            if change > 5:
                trend = "improving"
            elif change < -5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            recent = daily_success["mean"].mean()
            change = 0
            trend = "insufficient_data"

        return {
            "current_rate": round(recent * 100, 1),
            "trend": trend,
            "change": round(change, 1),
            "daily_rates": daily_success["mean"].tolist()[-30:],  # Last 30 days
        }

    def _analyze_performance_trend(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze performance (duration) trends.

        Args:
            df: DataFrame with run data

        Returns:
            Dictionary with performance analysis
        """
        if df.empty:
            return {"avg_duration": 0, "trend": "stable", "change": 0}

        # Calculate average duration by day
        df["date"] = df["timestamp"].dt.date
        daily_duration = df.groupby("date")["duration"].agg(["mean", "count"])

        # Calculate trend
        if len(daily_duration) >= 7:
            recent = daily_duration.tail(7)["mean"].mean()
            previous = (
                daily_duration.head(7)["mean"].mean()
                if len(daily_duration) >= 14
                else recent
            )

            change = ((recent - previous) / previous * 100) if previous > 0 else 0

            if change > 10:
                trend = "slowing"
            elif change < -10:
                trend = "improving"
            else:
                trend = "stable"
        else:
            recent = daily_duration["mean"].mean()
            change = 0
            trend = "insufficient_data"

        return {
            "avg_duration": round(recent, 2),
            "trend": trend,
            "change": round(change, 1),
            "daily_durations": daily_duration["mean"].tolist()[-30:],  # Last 30 days
        }

    def _analyze_issue_trends(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze issue count trends.

        Args:
            df: DataFrame with run data

        Returns:
            Dictionary with issue analysis
        """
        if df.empty:
            return {"avg_issues": 0, "trend": "stable", "change": 0}

        # Get issues for each run
        issue_counts = []
        for _, run in df.iterrows():
            issues = self.database.get_issues_by_run(run["id"])
            issue_counts.append(len(issues))

        df["issue_count"] = issue_counts

        # Calculate average issues by day
        df["date"] = df["timestamp"].dt.date
        daily_issues = df.groupby("date")["issue_count"].agg(["mean", "count"])

        # Calculate trend
        if len(daily_issues) >= 7:
            recent = daily_issues.tail(7)["mean"].mean()
            previous = (
                daily_issues.head(7)["mean"].mean()
                if len(daily_issues) >= 14
                else recent
            )

            change = ((recent - previous) / previous * 100) if previous > 0 else 0

            if change > 20:
                trend = "increasing"
            elif change < -20:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            recent = daily_issues["mean"].mean()
            change = 0
            trend = "insufficient_data"

        return {
            "avg_issues": round(recent, 1),
            "trend": trend,
            "change": round(change, 1),
            "daily_issues": daily_issues["mean"].tolist()[-30:],  # Last 30 days
        }

    def _analyze_category_trends(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze trends by issue category.

        Args:
            df: DataFrame with run data

        Returns:
            Dictionary with category analysis
        """
        category_trends: dict[str, dict[str, Any]] = {}

        # Get all runs with their issues
        for _, run in df.iterrows():
            issues = self.database.get_issues_by_run(run["id"])

            # Categorize issues
            for issue in issues:
                category = issue.get("parser", "unknown")
                if category not in category_trends:
                    category_trends[category] = {
                        "total": 0,
                        "by_severity": {},
                        "dates": [],
                    }

                category_trends[category]["total"] += 1

                severity = issue.get("severity", "info")
                if severity not in category_trends[category]["by_severity"]:
                    category_trends[category]["by_severity"][severity] = 0
                category_trends[category]["by_severity"][severity] += 1

                category_trends[category]["dates"].append(run["timestamp"].date())

        # Calculate trends for each category
        for category, data in category_trends.items():
            if len(data["dates"]) >= 14:
                recent_count = len([d for d in data["dates"][-7:]])
                previous_count = len([d for d in data["dates"][-14:-7]])

                change = (
                    ((recent_count - previous_count) / previous_count * 100)
                    if previous_count > 0
                    else 0
                )

                if change > 50:
                    trend = "increasing"
                elif change < -50:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
                change = 0

            category_trends[category]["trend"] = trend
            category_trends[category]["change"] = round(change, 1)
            category_trends[category]["recent_count"] = len(
                [d for d in data["dates"][-7:]]
            )

        return category_trends

    def _analyze_file_trends(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze trends by file.

        Args:
            df: DataFrame with run data

        Returns:
            Dictionary with file analysis
        """
        file_trends: dict[str, dict[str, Any]] = {}

        # Get all runs with their issues
        for _, run in df.iterrows():
            issues = self.database.get_issues_by_run(run["id"])

            # Group issues by file
            for issue in issues:
                file_path = issue.get("file_path", "unknown")
                if file_path not in file_trends:
                    file_trends[file_path] = {
                        "total": 0,
                        "by_severity": {},
                        "dates": [],
                        "rules": set(),
                    }

                file_trends[file_path]["total"] += 1

                severity = issue.get("severity", "info")
                if severity not in file_trends[file_path]["by_severity"]:
                    file_trends[file_path]["by_severity"][severity] = 0
                file_trends[file_path]["by_severity"][severity] += 1

                file_trends[file_path]["dates"].append(run["timestamp"].date())
                file_trends[file_path]["rules"].add(issue.get("rule_id", "unknown"))

        # Calculate top problematic files
        sorted_files = sorted(
            file_trends.items(), key=lambda x: x[1]["total"], reverse=True
        )[:10]

        return {
            "top_files": [
                {
                    "file": file,
                    "total_issues": data["total"],
                    "unique_rules": len(data["rules"]),
                    "recent_issues": len([d for d in data["dates"][-7:]]),
                    "severities": data["by_severity"],
                }
                for file, data in sorted_files
            ]
        }

    def _generate_trend_recommendations(self, trends: dict[str, Any]) -> list[str]:
        """Generate recommendations based on trend analysis.

        Args:
            trends: Dictionary containing trend analysis results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Success rate recommendations
        success_trend = trends.get("success_rate", {})
        if success_trend.get("trend") == "declining":
            recommendations.append(
                "Success rate is declining. Investigate recent changes and potential issues."
            )
        elif success_trend.get("trend") == "improving":
            recommendations.append(
                "Success rate is improving. Continue current practices."
            )

        # Performance recommendations
        perf_trend = trends.get("performance", {})
        if perf_trend.get("trend") == "slowing":
            recommendations.append(
                "Command execution is slowing. Consider optimizing processes or investigating performance bottlenecks."
            )
        elif perf_trend.get("trend") == "improving":
            recommendations.append(
                "Command execution is getting faster. Performance optimizations are working."
            )

        # Issue count recommendations
        issue_trend = trends.get("issue_trends", {})
        if issue_trend.get("trend") == "increasing":
            recommendations.append(
                "Issue count is increasing. Review code quality and consider implementing preventive measures."
            )
        elif issue_trend.get("trend") == "decreasing":
            recommendations.append(
                "Issue count is decreasing. Code quality improvements are effective."
            )

        # Category recommendations
        category_trends = trends.get("category_trends", {})
        for category, data in category_trends.items():
            if data.get("trend") == "increasing" and data.get("recent_count", 0) > 5:
                recommendations.append(
                    f"Significant increase in {category} issues. Focus on this area for improvement."
                )

        # File recommendations
        file_trends = trends.get("file_trends", {})
        top_files = file_trends.get("top_files", [])
        for file_data in top_files[:3]:  # Top 3 problematic files
            if file_data["recent_issues"] > 3:
                recommendations.append(
                    f"File '{file_data['file']}' has recurring issues. Consider refactoring or additional review."
                )

        return recommendations

    def generate_trend_report(
        self, days: int = 30, output_file: str | None = None
    ) -> str:
        """Generate a comprehensive trend analysis report.

        Args:
            days: Number of days to analyze
            output_file: Optional output file path

        Returns:
            Path to generated report file
        """
        logger.info(f"Generating trend report for the last {days} days")

        # Analyze trends
        trends_data = self.analyze_trends(days)

        # Create report
        report_lines = [
            "# iCHS Trend Analysis Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Analysis Period: {days} days",
            f"Total Runs Analyzed: {trends_data['total_runs']}",
            "",
            "## Executive Summary",
            "",
        ]

        # Add key findings
        success_trend = trends_data["trends"].get("success_rate", {})
        perf_trend = trends_data["trends"].get("performance", {})
        issue_trend = trends_data["trends"].get("issue_trends", {})

        report_lines.extend(
            [
                f"- Success Rate: {success_trend.get('current_rate', 0)}% ({success_trend.get('trend', 'unknown')})",
                f"- Average Duration: {perf_trend.get('avg_duration', 0)}s ({perf_trend.get('trend', 'unknown')})",
                f"- Average Issues: {issue_trend.get('avg_issues', 0)} ({issue_trend.get('trend', 'unknown')})",
                "",
            ]
        )

        # Add recommendations
        if trends_data["recommendations"]:
            report_lines.extend(["## Recommendations", ""])
            for rec in trends_data["recommendations"]:
                report_lines.append(f"- {rec}")
            report_lines.append("")

        # Add detailed analysis
        report_lines.extend(["## Detailed Analysis", ""])

        # Category trends
        category_trends = trends_data["trends"].get("category_trends", {})
        if category_trends:
            report_lines.extend(["### Category Trends", ""])
            for category, data in category_trends.items():
                report_lines.append(
                    f"- **{category}**: {data.get('total', 0)} total issues, "
                    f"trend: {data.get('trend', 'unknown')} "
                    f"({data.get('change', 0)}% change)"
                )
            report_lines.append("")

        # Top problematic files
        file_trends = trends_data["trends"].get("file_trends", {})
        top_files = file_trends.get("top_files", [])
        if top_files:
            report_lines.extend(["### Top Problematic Files", ""])
            for file_data in top_files[:5]:
                report_lines.append(
                    f"- **{file_data['file']}**: {file_data['total_issues']} total issues, "
                    f"{file_data['recent_issues']} recent issues, "
                    f"{file_data['unique_rules']} unique rules"
                )
            report_lines.append("")

        # Add timestamp
        report_lines.extend([f"Report generated on: {datetime.now().isoformat()}", ""])

        # Write report
        report_content = "\n".join(report_lines)

        if output_file:
            report_path = Path(output_file)
        else:
            report_path = (
                self.cache_dir
                / f"trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

        report_path.write_text(report_content, encoding="utf-8")

        logger.info(f"Trend report generated: {report_path}")
        return str(report_path)
