"""
BugJail API Endpoints

REST API endpoints for bug detection and analysis.
"""

import asyncio
from datetime import datetime
from typing import Any

from ..core.analyzer import BugJailAnalyzer
from ..core.detector import BugJailDetector
from ..core.types import BugJailConfig


class BugJailAPI:
    """
    REST API for BugJail bug detection system.

    Provides endpoints for:
    - Bug and vulnerability scanning
    - Analysis reports
    - Integration with CWO12 and RCA
    - Configuration management
    """

    def __init__(self, config: BugJailConfig | None = None):
        """Initialize BugJail API."""
        self.config = config or BugJailConfig()
        self.analyzer = BugJailAnalyzer(self.config)
        self.detector = BugJailDetector(self.config)

    def scan_path(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Scan a path for bugs and vulnerabilities.

        Request body:
        {
            "path": "/path/to/scan",
            "options": {
                "include_patterns": ["**/*.py"],
                "exclude_patterns": ["**/test/**"],
                "min_severity": "medium",
                "enable_vulnerabilities": true,
                "parallel": true
            }
        }

        Returns:
            Analysis report
        """
        try:
            # Extract parameters
            path = request.get("path")
            if not path:
                return self._error_response("Path is required")

            options = request.get("options", {})

            # Create configuration
            scan_config = self._create_scan_config(options)

            # Perform scan
            report = self.detector.analyze_path(path)

            # Convert to API response
            return self._success_response({
                "report_id": report.id,
                "target_path": report.target_path,
                "scan_time": report.duration_seconds,
                "summary": {
                    "total_issues": report.total_issues,
                    "bugs": len(report.bugs),
                    "vulnerabilities": len(report.vulnerabilities),
                    "files_analyzed": len(report.files_analyzed),
                    "files_with_issues": len(report.files_with_issues)
                },
                "bugs": [self._serialize_bug(b) for b in report.bugs],
                "vulnerabilities": [self._serialize_vulnerability(v) for v in report.vulnerabilities],
                "recommendations": [self._serialize_recommendation(r) for r in report.recommendations],
                "compliance": {
                    "level": report.constitutional_compliance.value,
                    "summary": report.compliance_summary
                },
                "generated_at": report.generated_at.isoformat()
            })

        except Exception as e:
            return self._error_response(f"Scan failed: {str(e)}")

    def get_scan_report(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Get details of a scan report.

        Request body:
        {
            "report_id": "report-uuid"
        }

        Returns:
            Detailed scan report
        """
        # In a real implementation, reports would be stored in a database
        # For now, return a placeholder
        report_id = request.get("report_id")
        if not report_id:
            return self._error_response("Report ID is required")

        return self._error_response("Report storage not implemented in this demo")

    def trigger_cwo12_analysis(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Trigger CWO12 workflow analysis.

        Request body:
        {
            "project_path": "/path/to/project",
            "step": "step5" | "step7",
            "step7_tasks": ["task1", "task2"]  # Only for step7
        }

        Returns:
            CWO12 enhancement results
        """
        try:
            project_path = request.get("project_path")
            step = request.get("step")

            if not project_path or not step:
                return self._error_response("project_path and step are required")

            # Run analysis based on step
            if step == "step5":
                result = asyncio.run(
                    self.analyzer.trigger_cwo12_step5_enhancement(project_path)
                )
            elif step == "step7":
                tasks = request.get("step7_tasks", [])
                result = asyncio.run(
                    self.analyzer.trigger_cwo12_step7_precomputation(project_path, tasks)
                )
            else:
                return self._error_response("Invalid step. Must be 'step5' or 'step7'")

            return self._success_response(result)

        except Exception as e:
            return self._error_response(f"CWO12 analysis failed: {str(e)}")

    def enhance_rca(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Enhance RCA with bug detection.

        Request body:
        {
            "error_info": {
                "type": "ErrorType",
                "message": "Error message",
                "file_path": "/path/to/file",
                "line_number": 42
            },
            "codebase_path": "/path/to/codebase"
        }

        Returns:
            Enhanced RCA analysis
        """
        try:
            error_info = request.get("error_info")
            codebase_path = request.get("codebase_path")

            if not error_info or not codebase_path:
                return self._error_response("error_info and codebase_path are required")

            result = asyncio.run(
                self.analyzer.enhance_rca_analysis(error_info, codebase_path)
            )

            return self._success_response(result)

        except Exception as e:
            return self._error_response(f"RCA enhancement failed: {str(e)}")

    def get_statistics(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Get BugJail statistics.

        Returns:
            System statistics and performance metrics
        """
        try:
            detector_stats = self.detector.get_statistics()
            integration_status = self.analyzer.get_integration_status()

            return self._success_response({
                "detector": detector_stats,
                "integration": integration_status,
                "config": {
                    "bug_detection_enabled": self.config.enable_bug_detection,
                    "vulnerability_scanning_enabled": self.config.enable_vulnerability_scanning,
                    "constitutional_compliance_enabled": self.config.enable_constitutional_compliance,
                    "parallel_analysis": self.config.parallel_analysis,
                    "max_workers": self.config.max_workers
                },
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return self._error_response(f"Failed to get statistics: {str(e)}")

    def update_config(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Update BugJail configuration.

        Request body:
        {
            "min_severity": "medium",
            "include_patterns": ["**/*.py", "**/*.js"],
            "exclude_patterns": ["**/test/**"],
            "parallel_analysis": true,
            "max_workers": 4
        }

        Returns:
            Updated configuration
        """
        try:
            # Update configuration
            for key, value in request.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Reinitialize analyzer with new config
            self.analyzer = BugJailAnalyzer(self.config)
            self.detector = BugJailDetector(self.config)

            return self._success_response({
                "message": "Configuration updated successfully",
                "config": self._serialize_config()
            })

        except Exception as e:
            return self._error_response(f"Failed to update configuration: {str(e)}")

    def get_patterns(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Get bug detection patterns.

        Query params:
        - language: Filter by language
        - category: Filter by bug category
        - severity: Filter by severity

        Returns:
            List of detection patterns
        """
        try:
            language = request.get("language")
            category = request.get("category")
            severity = request.get("severity")

            # Get patterns from library
            patterns = []
            if language:
                from ..patterns.library import PatternLibrary
                library = PatternLibrary()
                library.load_builtin_patterns()
                lang_patterns = library.get_patterns_for_language(language)

                # Apply filters
                for pattern in lang_patterns:
                    if category and pattern.category.value != category:
                        continue
                    if severity and pattern.severity.value != severity:
                        continue
                    patterns.append(self._serialize_pattern(pattern))

            return self._success_response({
                "patterns": patterns,
                "count": len(patterns),
                "filters": {
                    "language": language,
                    "category": category,
                    "severity": severity
                }
            })

        except Exception as e:
            return self._error_response(f"Failed to get patterns: {str(e)}")

    def add_custom_pattern(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Add a custom detection pattern.

        Request body:
        {
            "name": "Custom Pattern",
            "category": "null_pointer",
            "severity": "high",
            "pattern": "regex-pattern",
            "language": "python",
            "description": "Pattern description"
        }

        Returns:
            Added pattern details
        """
        try:
            from ..core.types import BugCategory, BugSeverity
            from ..patterns.library import DetectionPattern, PatternLibrary

            # Create pattern
            pattern = DetectionPattern(
                id=f"custom_{datetime.now().timestamp()}",
                name=request["name"],
                category=BugCategory(request["category"]),
                severity=BugSeverity(request["severity"]),
                pattern=request["pattern"],
                language=request["language"],
                description=request.get("description", ""),
                tags=request.get("tags", [])
            )

            # Add to library
            library = PatternLibrary()
            library.add_pattern(pattern)

            return self._success_response({
                "message": "Custom pattern added successfully",
                "pattern": self._serialize_pattern(pattern)
            })

        except Exception as e:
            return self._error_response(f"Failed to add pattern: {str(e)}")

    def _create_scan_config(self, options: dict[str, Any]) -> BugJailConfig:
        """Create scan configuration from options."""
        config = BugJailConfig()

        # Apply options
        if "include_patterns" in options:
            config.include_patterns = options["include_patterns"]
        if "exclude_patterns" in options:
            config.exclude_patterns = options["exclude_patterns"]
        if "min_severity" in options:
            from ..core.types import BugSeverity
            config.min_severity_level = BugSeverity(options["min_severity"])
        if "enable_vulnerabilities" in options:
            config.enable_vulnerability_scanning = options["enable_vulnerabilities"]
        if "parallel" in options:
            config.parallel_analysis = options["parallel"]

        return config

    def _serialize_bug(self, bug) -> dict[str, Any]:
        """Serialize bug to JSON."""
        return {
            "id": bug.id,
            "type": bug.type.value,
            "severity": bug.severity.value,
            "message": bug.message,
            "description": bug.description,
            "file_path": bug.file_path,
            "line_number": bug.line_number,
            "column_number": bug.column_number,
            "code_snippet": bug.code_snippet,
            "function_name": bug.function_name,
            "class_name": bug.class_name,
            "confidence": bug.confidence,
            "rule_id": bug.rule_id,
            "rule_name": bug.rule_name,
            "tags": list(bug.tags),
            "detected_at": bug.detected_at.isoformat()
        }

    def _serialize_vulnerability(self, vuln) -> dict[str, Any]:
        """Serialize vulnerability to JSON."""
        base = self._serialize_bug(vuln)
        base.update({
            "vulnerability_type": vuln.vulnerability_type.value,
            "owasp_reference": vuln.owasp_reference,
            "cwe_id": vuln.cwe_id,
            "cvss_score": vuln.cvss_score,
            "exploitability": vuln.exploitability,
            "impact": vuln.impact,
            "constitutional_compliance": vuln.constitutional_compliance.value,
            "compliance_violations": vuln.compliance_violations
        })
        return base

    def _serialize_recommendation(self, rec) -> dict[str, Any]:
        """Serialize recommendation to JSON."""
        return {
            "title": rec.title,
            "description": rec.description,
            "code_fix": rec.code_fix,
            "explanation": rec.explanation,
            "priority": rec.priority.value,
            "effort_estimate": rec.effort_estimate,
            "automation_possible": rec.automation_possible,
            "automated_fix": rec.automated_fix,
            "before_example": rec.before_example,
            "after_example": rec.after_example,
            "references": rec.references,
            "learn_more_links": rec.learn_more_links
        }

    def _serialize_pattern(self, pattern) -> dict[str, Any]:
        """Serialize pattern to JSON."""
        return {
            "id": pattern.id,
            "name": pattern.name,
            "category": pattern.category.value,
            "severity": pattern.severity.value,
            "pattern": pattern.pattern,
            "language": pattern.language,
            "description": pattern.description,
            "enabled": pattern.enabled,
            "confidence_threshold": pattern.confidence_threshold,
            "tags": list(pattern.tags)
        }

    def _serialize_config(self) -> dict[str, Any]:
        """Serialize configuration to JSON."""
        return {
            "enable_bug_detection": self.config.enable_bug_detection,
            "enable_vulnerability_scanning": self.config.enable_vulnerability_scanning,
            "enable_constitutional_compliance": self.config.enable_constitutional_compliance,
            "min_severity_level": self.config.min_severity_level.value,
            "include_patterns": self.config.include_patterns,
            "exclude_patterns": self.config.exclude_patterns,
            "parallel_analysis": self.config.parallel_analysis,
            "max_workers": self.config.max_workers,
            "generate_recommendations": self.config.generate_recommendations
        }

    def _success_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create successful API response."""
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    def _error_response(self, message: str, code: str = "error") -> dict[str, Any]:
        """Create error API response."""
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }


# API Factory
def create_api(config: BugJailConfig | None = None) -> BugJailAPI:
    """Create BugJail API instance."""
    return BugJailAPI(config)
