"""
BugJail Analyzer

Orchestrates bug detection analysis and integrates with exploration workflow.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from .detector import BugJailDetector
from .types import AnalysisReport, BugJailConfig, ExplorationIntegration


class BugJailAnalyzer:
    """
    BugJail analysis orchestrator with exploration workflow integration.

    Provides high-level analysis interface with support for:
    - CWO12 workflow integration
    - RCA enhancement
    - Pre-commit hooks
    - Real-time monitoring
    """

    def __init__(self, config: BugJailConfig | None = None):
        """Initialize BugJail analyzer."""
        self.config = config or BugJailConfig()
        self.detector = BugJailDetector(self.config)
        self.exploration_integrations: dict[str, ExplorationIntegration] = {}

        # Initialize default integrations
        self._setup_default_integrations()

    def analyze_path(self, target_path: str) -> AnalysisReport:
        """
        Analyze a path for bugs and vulnerabilities.

        Args:
            target_path: Path to analyze

        Returns:
            Comprehensive analysis report
        """
        return self.detector.analyze_path(target_path)

    async def analyze_with_exploration(
        self,
        target_path: str,
        workflow_step: str = "manual",
        trigger_event: str = "scan"
    ) -> AnalysisReport:
        """
        Analyze with exploration workflow integration.

        Args:
            target_path: Path to analyze
            workflow_step: CWO12 workflow step (e.g., "cwo12_step5")
            trigger_event: Trigger event (e.g., "file_change")

        Returns:
            Enhanced analysis report
        """
        # Get integration configuration
        integration_key = f"{workflow_step}_{trigger_event}"
        integration = self.exploration_integrations.get(integration_key)

        # Create analysis configuration
        analysis_config = self._create_integration_config(integration)

        # Perform analysis
        report = self.analyze_path(target_path)

        # Apply integration-specific processing
        if integration:
            report = await self._apply_integration_processing(report, integration)

        return report

    def setup_cwo12_integration(self):
        """Setup integration with CWO12 workflow."""
        # Step 5 integration - architecture analysis
        step5_integration = ExplorationIntegration(
            workflow_step="cwo12_step5",
            trigger_event="architecture_analysis",
            analysis_types=["structure", "symbols", "dependencies"],
            priority_files=["**/*.py", "**/config/**"],
            on_detection_callback="cwo12_step5_bug_handler"
        )

        # Step 7 integration - pre-implementation analysis
        step7_integration = ExplorationIntegration(
            workflow_step="cwo12_step7",
            trigger_event="pre_implementation",
            analysis_types=["bugs", "vulnerabilities", "compliance"],
            exclude_patterns=["**/tests/**", "**/docs/**"],
            on_vulnerability_callback="cwo12_vulnerability_handler"
        )

        # Register integrations
        self.exploration_integrations["cwo12_step5_architecture_analysis"] = step5_integration
        self.exploration_integrations["cwo12_step7_pre_implementation"] = step7_integration

    def setup_rca_integration(self):
        """Setup integration with RCA (Root Cause Analysis)."""
        rca_integration = ExplorationIntegration(
            workflow_step="rca_enhancement",
            trigger_event="error_detected",
            analysis_types=["bug_localization", "symbols", "data_flow"],
            priority_files=["**/src/**"],
            on_detection_callback="rca_bug_handler",
            exclude_patterns=["**/tests/**"]
        )

        self.exploration_integrations["rca_enhancement_error_detected"] = rca_integration

    def setup_pre_commit_integration(self):
        """Setup pre-commit hook integration."""
        pre_commit_integration = ExplorationIntegration(
            workflow_step="pre_commit",
            trigger_event="file_change",
            analysis_types=["bugs", "vulnerabilities"],
            exclude_patterns=["**/tests/**", "**/docs/**", "**/__pycache__/**"],
            on_vulnerability_callback="pre_commit_vulnerability_block"
        )

        self.exploration_integrations["pre_commit_file_change"] = pre_commit_integration

    async def trigger_cwo12_step5_enhancement(self, project_path: str) -> dict[str, Any]:
        """
        Trigger enhanced bug detection for CWO12 Step 5.

        Args:
            project_path: Path to CWO12 project

        Returns:
            Enhancement results with bug analysis
        """
        # Analyze with Step 5 integration
        report = await self.analyze_with_exploration(
            project_path,
            workflow_step="cwo12_step5",
            trigger_event="architecture_analysis"
        )

        # Extract architecture-relevant findings
        architecture_issues = self._filter_architecture_issues(report)

        # Create enhancement data
        enhancement = {
            "status": "completed",
            "architecture_analysis": {
                "total_issues": len(architecture_issues),
                "critical_issues": [i for i in architecture_issues if i.severity.value == "critical"],
                "security_issues": [i for i in architecture_issues if hasattr(i, 'vulnerability_type')],
                "recommendations": [r for r in report.recommendations if r.priority.value in ["critical", "high"]]
            },
            "bug_metrics": {
                "by_category": report.bugs_by_category,
                "by_severity": report.bugs_by_severity,
                "files_with_issues": report.files_with_issues
            },
            "compliance_status": {
                "level": report.constitutional_compliance.value,
                "violations": len([v for v in report.vulnerabilities if v.constitutional_compliance.value != "compliant"])
            },
            "enhanced_at": report.generated_at
        }

        return enhancement

    async def trigger_cwo12_step7_precomputation(
        self,
        project_path: str,
        task_list: list[str]
    ) -> dict[str, Any]:
        """
        Trigger precomputation analysis for CWO12 Step 7.

        Args:
            project_path: Path to CWO12 project
            task_list: List of upcoming tasks

        Returns:
            Precomputation results with risk assessment
        """
        # Extract files from tasks
        affected_files = self._extract_files_from_tasks(project_path, task_list)

        # Analyze affected files
        all_reports = []
        risk_assessment = {
            "high_risk_files": [],
            "security_issues": [],
            "blocking_issues": []
        }

        for file_path in affected_files:
            if Path(file_path).exists():
                report = await self.analyze_with_exploration(
                    file_path,
                    workflow_step="cwo12_step7",
                    trigger_event="pre_implementation"
                )

                all_reports.append(report)

                # Assess risk
                if report.total_issues > 0:
                    critical_issues = [i for i in report.bugs if i.severity.value == "critical"]
                    if critical_issues:
                        risk_assessment["high_risk_files"].append(file_path)
                        risk_assessment["blocking_issues"].extend(critical_issues)

                if report.vulnerabilities:
                    risk_assessment["security_issues"].extend(report.vulnerabilities)

        # Create precomputation result
        precomputation = {
            "status": "completed",
            "analyzed_files": affected_files,
            "total_issues": sum(r.total_issues for r in all_reports),
            "risk_assessment": risk_assessment,
            "recommendations": {
                "review_first": risk_assessment["high_risk_files"],
                "security_review": len(risk_assessment["security_issues"]) > 0,
                "implementation_ready": len(risk_assessment["blocking_issues"]) == 0
            },
            "precomputed_at": asyncio.get_event_loop().time()
        }

        return precomputation

    async def enhance_rca_analysis(self, error_info: dict[str, Any], codebase_path: str) -> dict[str, Any]:
        """
        Enhance RCA analysis with bug detection.

        Args:
            error_info: Error information from RCA
            codebase_path: Path to codebase

        Returns:
            Enhanced RCA analysis
        """
        # Extract error location
        error_file = error_info.get("file_path")
        error_line = error_info.get("line_number", 0)

        if not error_file or not Path(error_file).exists():
            return {"status": "failed", "reason": "Invalid error location"}

        # Analyze error location
        report = await self.analyze_with_exploration(
            error_file,
            workflow_step="rca_enhancement",
            trigger_event="error_detected"
        )

        # Find related bugs
        related_bugs = self._find_related_bugs(report, error_line, error_info)

        # Create enhancement
        enhancement = {
            "status": "completed",
            "error_info": error_info,
            "related_bugs": [
                {
                    "id": bug.id,
                    "type": bug.type.value,
                    "severity": bug.severity.value,
                    "description": bug.description,
                    "line": bug.line_number,
                    "distance_from_error": abs(bug.line_number - error_line)
                }
                for bug in related_bugs
            ],
            "suggested_causes": self._analyze_suggested_causes(related_bugs, error_info),
            "recommendations": self._generate_rca_recommendations(related_bugs, error_info),
            "enhanced_at": report.generated_at
        }

        return enhancement

    def _setup_default_integrations(self):
        """Setup default exploration integrations."""
        self.setup_cwo12_integration()
        self.setup_rca_integration()
        self.setup_pre_commit_integration()

    def _create_integration_config(self, integration: ExplorationIntegration | None) -> dict[str, Any]:
        """Create analysis configuration from integration."""
        if not integration:
            return {}

        return {
            "include_patterns": integration.priority_files,
            "exclude_patterns": integration.exclude_patterns,
            "analysis_types": integration.analysis_types,
            "integration_metadata": {
                "workflow_step": integration.workflow_step,
                "trigger_event": integration.trigger_event
            }
        }

    async def _apply_integration_processing(
        self,
        report: AnalysisReport,
        integration: ExplorationIntegration
    ) -> AnalysisReport:
        """Apply integration-specific processing to report."""
        # Add integration metadata to report
        report.metadata = report.metadata or {}
        report.metadata["integration"] = {
            "workflow_step": integration.workflow_step,
            "trigger_event": integration.trigger_event,
            "processed_at": report.generated_at
        }

        # Trigger callbacks if configured
        if integration.on_detection_callback and report.bugs:
            await self._trigger_callback(integration.on_detection_callback, report.bugs[:5])

        if integration.on_vulnerability_callback and report.vulnerabilities:
            await self._trigger_callback(integration.on_vulnerability_callback, report.vulnerabilities[:5])

        return report

    async def _trigger_callback(self, callback_name: str, items: list[Any]):
        """Trigger integration callback."""
        # This would integrate with the exploration orchestrator
        # For now, just log the callback
        logging.info(f"Triggering callback {callback_name} with {len(items)} items")

    def _filter_architecture_issues(self, report: AnalysisReport) -> list[Any]:
        """Filter issues relevant to architecture analysis."""
        all_issues = report.bugs + report.vulnerabilities

        # Focus on issues that affect architecture
        architecture_relevant = [
            issue for issue in all_issues
            if issue.type.value in [
                "resource_leak", "concurrent_access", "api_misuse",
                "data_inconsistency", "race_condition"
            ] or (hasattr(issue, 'vulnerability_type') and
                  issue.vulnerability_type.value in [
                      "broken_access_control", "insecure_design",
                      "security_misconfiguration"
                  ])
        ]

        return architecture_relevant

    def _extract_files_from_tasks(self, project_path: str, task_list: list[str]) -> list[str]:
        """Extract file paths from task descriptions."""
        files = set()
        project_path = Path(project_path)

        for task in task_list:
            # Simple extraction - look for file extensions
            import re
            file_patterns = re.findall(r'\b[\w\-/]+\.(py|js|ts|java|cpp|c|h)\b', task)

            for pattern in file_patterns:
                # Try to find the file
                for file_path in project_path.rglob(f"*{pattern}"):
                    if file_path.is_file():
                        files.add(str(file_path))

        return list(files)

    def _find_related_bugs(self, report: AnalysisReport, error_line: int, error_info: dict) -> list[Any]:
        """Find bugs related to the error location."""
        all_issues = report.bugs + report.vulnerabilities

        # Find bugs within 10 lines of the error
        related = [
            issue for issue in all_issues
            if abs(issue.line_number - error_line) <= 10
        ]

        # Sort by distance from error
        related.sort(key=lambda x: abs(x.line_number - error_line))

        return related[:10]  # Return top 10 related bugs

    def _analyze_suggested_causes(self, bugs: list[Any], error_info: dict) -> list[str]:
        """Analyze suggested causes from related bugs."""
        causes = []

        if not bugs:
            return ["No related bugs detected"]

        # Analyze bug types
        bug_types = [b.type.value for b in bugs]

        if "null_pointer" in bug_types:
            causes.append("Possible null reference or uninitialized variable")

        if "api_misuse" in bug_types:
            causes.append("Incorrect API usage or missing error handling")

        if "resource_leak" in bug_types:
            causes.append("Resource management issue or missing cleanup")

        if "race_condition" in bug_types:
            causes.append("Concurrent access or threading issue")

        return causes or ["Unknown cause - requires manual investigation"]

    def _generate_rca_recommendations(self, bugs: list[Any], error_info: dict) -> list[str]:
        """Generate recommendations based on related bugs."""
        recommendations = []

        if not bugs:
            return ["Review code manually around error location"]

        # General recommendations based on bug types
        recommendations.append("Review the error location and surrounding 10 lines")
        recommendations.append("Add proper error handling and validation")

        # Specific recommendations
        for bug in bugs[:3]:  # Top 3 bugs
            if hasattr(bug, 'description'):
                recommendations.append(f"Address: {bug.description}")

        return recommendations

    def get_integration_status(self) -> dict[str, Any]:
        """Get status of exploration integrations."""
        return {
            "configured_integrations": list(self.exploration_integrations.keys()),
            "detector_stats": self.detector.get_statistics(),
            "config": self.config
        }
