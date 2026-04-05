"""
CI/CD system adapters for evidence validation.

This module provides specialized adapters for continuous integration
and continuous deployment systems like GitHub Actions, GitLab CI,
Jenkins, and CircleCI.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import HTTPAdapter, WebSocketAdapter
from ..models.schemas import EvidenceType, CacheStrategy


class CIPlatformAdapter:
    """
    Adapter for CI platforms like GitHub Actions, GitLab CI, CircleCI.

    Integrates evidence validation into continuous integration
    pipelines with build, test, and artifact validation.
    """

    def __init__(
        self,
        ci_platform: str,
        base_url: str,
        api_key: Optional[str] = None,
        validate_builds: bool = True,
        validate_tests: bool = True,
        validate_artifacts: bool = True
    ):
        """Initialize CI platform adapter.

        Args:
            ci_platform: Name of the CI platform
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_builds: Validate build execution evidence
            validate_tests: Validate test execution evidence
            validate_artifacts: Validate build artifact evidence
        """
        self.ci_platform = ci_platform
        self.validate_builds = validate_builds
        self.validate_tests = validate_tests
        self.validate_artifacts = validate_artifacts

        # Initialize WebSocket adapter for real-time CI monitoring
        self.ws_adapter = WebSocketAdapter(
            component_name=f"{ci_platform}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def connect(self):
        """Connect to validation service with WebSocket."""
        await self.ws_adapter.connect()

        # Set up message handlers for CI-specific events
        self.ws_adapter.add_message_handler(
            "validation_completed",
            self._handle_ci_validation_completed
        )

    async def validate_build_execution(
        self,
        build_id: str,
        project_name: str,
        branch: str,
        commit_hash: str,
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        build_number: Optional[str] = None,
        build_config: Optional[Dict[str, Any]] = None,
        logs: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Validate CI build execution evidence.

        Args:
            build_id: Build identifier
            project_name: Project/repository name
            branch: Git branch
            commit_hash: Git commit hash
            status: Build status (success, failure, cancelled)
            start_time: Build start time
            end_time: Build end time
            build_number: Build number
            build_config: Build configuration
            logs: Build logs
            error_message: Error message if build failed
        """
        evidence_data = {
            "build_id": build_id,
            "project_name": project_name,
            "branch": branch,
            "commit_hash": commit_hash,
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "build_number": build_number,
            "build_config": build_config,
            "logs": logs,
            "error_message": error_message,
            "ci_platform": self.ci_platform,
        }

        evidence_type = EvidenceType.TASK_EXECUTION if status == "success" else EvidenceType.ERROR_LOG

        metadata = {
            "workflow_id": project_name,
            "task_id": build_id,
            "tags": ["ci", "build", project_name, self.ci_platform],
            "priority": 8,  # High priority for CI builds
            "severity": "low" if status == "success" else "high",
        }

        validation_rules = []
        if self.validate_builds:
            if status == "success":
                validation_rules = ["build_integrity", "config_validity", "dependency_check"]
            else:
                validation_rules = ["build_failure_analysis", "error_detection"]

        response = await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

        # Subscribe to real-time updates for running builds
        if end_time is None:
            await self.ws_adapter.subscribe_to_validation(
                response.request_id,
                lambda data: self._handle_build_validation(data, build_id)
            )

        return response

    async def validate_test_execution(
        self,
        test_suite_id: str,
        build_id: str,
        project_name: str,
        test_framework: str,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        skipped_tests: int,
        test_results: Optional[List[Dict[str, Any]]] = None,
        coverage_report: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ):
        """Validate test execution evidence.

        Args:
            test_suite_id: Test suite identifier
            build_id: Associated build ID
            project_name: Project name
            test_framework: Test framework used (pytest, jest, etc.)
            total_tests: Total number of tests
            passed_tests: Number of passed tests
            failed_tests: Number of failed tests
            skipped_tests: Number of skipped tests
            test_results: Detailed test results
            coverage_report: Code coverage report
            execution_time: Test execution time in seconds
        """
        evidence_data = {
            "test_suite_id": test_suite_id,
            "build_id": build_id,
            "project_name": project_name,
            "test_framework": test_framework,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "test_results": test_results,
            "coverage_report": coverage_report,
            "execution_time": execution_time,
            "ci_platform": self.ci_platform,
        }

        metadata = {
            "workflow_id": project_name,
            "task_id": test_suite_id,
            "tags": ["ci", "test", test_framework, project_name, self.ci_platform],
            "priority": 7,
        }

        validation_rules = []
        if self.validate_tests:
            validation_rules = [
                "test_coverage_analysis",
                "test_quality_metrics",
                "failure_pattern_analysis"
            ]
            if coverage_report:
                validation_rules.append("coverage_standards")

        response = await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.TEST_RESULT,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

        return response

    async def validate_build_artifact(
        self,
        artifact_id: str,
        build_id: str,
        project_name: str,
        artifact_name: str,
        artifact_type: str,
        artifact_size: int,
        artifact_hash: Optional[str] = None,
        download_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Validate build artifact evidence.

        Args:
            artifact_id: Artifact identifier
            build_id: Associated build ID
            project_name: Project name
            artifact_name: Name of the artifact
            artifact_type: Type of artifact (docker_image, binary, package, etc.)
            artifact_size: Artifact size in bytes
            artifact_hash: SHA-256 hash of artifact
            download_url: Artifact download URL
            metadata: Additional artifact metadata
        """
        evidence_data = {
            "artifact_id": artifact_id,
            "build_id": build_id,
            "project_name": project_name,
            "artifact_name": artifact_name,
            "artifact_type": artifact_type,
            "artifact_size": artifact_size,
            "artifact_hash": artifact_hash,
            "download_url": download_url,
            "metadata": metadata or {},
            "ci_platform": self.ci_platform,
        }

        request_metadata = {
            "workflow_id": project_name,
            "task_id": artifact_id,
            "tags": ["ci", "artifact", artifact_type, project_name, self.ci_platform],
            "priority": 6,
        }

        validation_rules = []
        if self.validate_artifacts:
            validation_rules = [
                "artifact_integrity",
                "size_validation",
                "security_scan"
            ]
            if artifact_hash:
                validation_rules.append("hash_verification")

        return await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.FILE_OPERATION,
            metadata=request_metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

    async def _handle_ci_validation_completed(self, data: Dict[str, Any]):
        """Handle CI validation completion."""
        print(f"CI validation completed: {data.get('request_id')}")

    async def _handle_build_validation(self, data: Dict[str, Any], build_id: str):
        """Handle build-specific validation updates."""
        print(f"Build validation update for {build_id}: {data}")

    async def close(self):
        """Close adapter connections."""
        await self.ws_adapter.disconnect()
        await self.ws_adapter.close()


class CDPlatformAdapter:
    """
    Adapter for CD platforms like ArgoCD, Flux, Spinnaker,
    or GitHub Deployments.

    Integrates evidence validation into continuous deployment
    with deployment risk assessment and rollback validation.
    """

    def __init__(
        self,
        cd_platform: str,
        base_url: str,
        api_key: Optional[str] = None,
        validate_deployments: bool = True,
        validate_rollback: bool = True
    ):
        """Initialize CD platform adapter.

        Args:
            cd_platform: Name of the CD platform
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_deployments: Validate deployment evidence
            validate_rollback: Validate rollback evidence
        """
        self.cd_platform = cd_platform
        self.validate_deployments = validate_deployments
        self.validate_rollback = validate_rollback

        # Initialize WebSocket adapter for real-time deployment monitoring
        self.ws_adapter = WebSocketAdapter(
            component_name=f"{cd_platform}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def connect(self):
        """Connect to validation service with WebSocket."""
        await self.ws_adapter.connect()

    async def validate_deployment(
        self,
        deployment_id: str,
        application_name: str,
        environment: str,
        version: str,
        strategy: str,  # rolling, blue-green, canary, etc.
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        previous_version: Optional[str] = None,
        rollout_status: Optional[Dict[str, Any]] = None,
        health_checks: Optional[List[Dict[str, Any]]] = None,
        rollback_available: bool = False,
        error_message: Optional[str] = None
    ):
        """Validate deployment evidence.

        Args:
            deployment_id: Deployment identifier
            application_name: Application name
            environment: Deployment environment (prod, staging, dev)
            version: Application version being deployed
            strategy: Deployment strategy
            status: Deployment status
            start_time: Deployment start time
            end_time: Deployment end time
            previous_version: Previous application version
            rollout_status: Detailed rollout status
            health_checks: Health check results
            rollback_available: Whether rollback is available
            error_message: Error message if deployment failed
        """
        evidence_data = {
            "deployment_id": deployment_id,
            "application_name": application_name,
            "environment": environment,
            "version": version,
            "strategy": strategy,
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "previous_version": previous_version,
            "rollout_status": rollout_status,
            "health_checks": health_checks,
            "rollback_available": rollback_available,
            "error_message": error_message,
            "cd_platform": self.cd_platform,
        }

        evidence_type = EvidenceType.TASK_EXECUTION if status == "success" else EvidenceType.ERROR_LOG

        metadata = {
            "workflow_id": application_name,
            "task_id": deployment_id,
            "tags": ["cd", "deployment", application_name, environment, self.cd_platform],
            "priority": 9,  # Highest priority for deployments
            "severity": self._get_deployment_severity(status, environment),
        }

        validation_rules = []
        if self.validate_deployments:
            if status == "success":
                validation_rules = [
                    "deployment_safety",
                    "health_check_validation",
                    "rollback_capability",
                    "environment_consistency"
                ]
            else:
                validation_rules = [
                    "deployment_failure_analysis",
                    "impact_assessment",
                    "recovery_procedures"
                ]

        response = await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

        # Subscribe to real-time updates for ongoing deployments
        if end_time is None:
            await self.ws_adapter.subscribe_to_validation(
                response.request_id,
                lambda data: self._handle_deployment_validation(data, deployment_id)
            )

        return response

    async def validate_rollback(
        self,
        rollback_id: str,
        deployment_id: str,
        application_name: str,
        environment: str,
        from_version: str,
        to_version: str,
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        rollback_reason: str,
        impact_assessment: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Validate rollback evidence.

        Args:
            rollback_id: Rollback identifier
            deployment_id: Original deployment ID
            application_name: Application name
            environment: Deployment environment
            from_version: Version being rolled back from
            to_version: Version being rolled back to
            status: Rollback status
            start_time: Rollback start time
            end_time: Rollback end time
            rollback_reason: Reason for rollback
            impact_assessment: Rollback impact assessment
            error_message: Error message if rollback failed
        """
        evidence_data = {
            "rollback_id": rollback_id,
            "deployment_id": deployment_id,
            "application_name": application_name,
            "environment": environment,
            "from_version": from_version,
            "to_version": to_version,
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "rollback_reason": rollback_reason,
            "impact_assessment": impact_assessment,
            "error_message": error_message,
            "cd_platform": self.cd_platform,
        }

        evidence_type = EvidenceType.TASK_EXECUTION if status == "success" else EvidenceType.ERROR_LOG

        metadata = {
            "workflow_id": application_name,
            "task_id": rollback_id,
            "tags": ["cd", "rollback", application_name, environment, self.cd_platform],
            "priority": 10,  # Highest priority for rollbacks
            "severity": "medium" if status == "success" else "critical",
        }

        validation_rules = []
        if self.validate_rollback:
            if status == "success":
                validation_rules = [
                    "rollback_safety",
                    "version_reversion",
                    "service_recovery",
                    "data_consistency"
                ]
            else:
                validation_rules = [
                    "rollback_failure_analysis",
                    "emergency_procedures",
                    "escalation_required"
                ]

        return await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.LONG_TERM
        )

    async def validate_deployment_risk(
        self,
        deployment_id: str,
        application_name: str,
        environment: str,
        risk_factors: Dict[str, Any],
        risk_score: float,
        recommendations: List[str],
        timestamp: Optional[datetime] = None
    ):
        """Validate deployment risk assessment.

        Args:
            deployment_id: Deployment identifier
            application_name: Application name
            environment: Deployment environment
            risk_factors: Risk factors assessment
            risk_score: Overall risk score (0.0-1.0)
            recommendations: Risk mitigation recommendations
            timestamp: Risk assessment timestamp
        """
        evidence_data = {
            "deployment_id": deployment_id,
            "application_name": application_name,
            "environment": environment,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "recommendations": recommendations,
            "timestamp": timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
            "cd_platform": self.cd_platform,
        }

        metadata = {
            "workflow_id": application_name,
            "task_id": deployment_id,
            "tags": ["cd", "risk_assessment", application_name, environment, self.cd_platform],
            "priority": 8,
        }

        validation_rules = [
            "risk_assessment_accuracy",
            "recommendation_relevance",
            "deployment_safety"
        ]

        return await self.ws_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.SECURITY_ASSESSMENT,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

    def _get_deployment_severity(self, status: str, environment: str) -> str:
        """Get deployment severity based on status and environment."""
        if status != "success":
            if environment in ["prod", "production"]:
                return "critical"
            elif environment in ["staging", "pre-prod"]:
                return "high"
            else:
                return "medium"
        return "low"

    async def _handle_deployment_validation(self, data: Dict[str, Any], deployment_id: str):
        """Handle deployment-specific validation updates."""
        print(f"Deployment validation update for {deployment_id}: {data}")

    async def close(self):
        """Close adapter connections."""
        await self.ws_adapter.disconnect()
        await self.ws_adapter.close()


class CodeQualityAdapter:
    """
    Adapter for code quality tools like SonarQube, CodeClimate,
    or GitHub Code Scanning.

    Integrates evidence validation into code quality analysis
    with security vulnerability detection.
    """

    def __init__(
        self,
        quality_tool: str,
        base_url: str,
        api_key: Optional[str] = None,
        validate_security: bool = True,
        validate_quality: bool = True
    ):
        """Initialize code quality adapter.

        Args:
            quality_tool: Name of the quality tool
            base_url: Evidence validation API base URL
            api_key: Optional API key
            validate_security: Validate security scan results
            validate_quality: Validate code quality metrics
        """
        self.quality_tool = quality_tool
        self.validate_security = validate_security
        self.validate_quality = validate_quality

        # Initialize HTTP adapter
        self.http_adapter = HTTPAdapter(
            component_name=f"{quality_tool}_adapter",
            component_version="1.0.0")
            base_url=base_url,
            api_key=api_key
        )

    async def validate_code_analysis(
        self,
        analysis_id: str,
        project_name: str,
        branch: str,
        commit_hash: str,
        quality_metrics: Dict[str, Any],
        security_vulnerabilities: List[Dict[str, Any]],
        code_smells: List[Dict[str, Any]],
        coverage: Optional[float] = None,
        duplication: Optional[float] = None,
        maintainability_rating: Optional[str] = None
    ):
        """Validate code analysis evidence.

        Args:
            analysis_id: Analysis identifier
            project_name: Project name
            branch: Git branch
            commit_hash: Git commit hash
            quality_metrics: Overall quality metrics
            security_vulnerabilities: List of security vulnerabilities
            code_smells: List of code smells
            coverage: Code coverage percentage
            duplication: Code duplication percentage
            maintainability_rating: Maintainability rating
        """
        evidence_data = {
            "analysis_id": analysis_id,
            "project_name": project_name,
            "branch": branch,
            "commit_hash": commit_hash,
            "quality_metrics": quality_metrics,
            "security_vulnerabilities": security_vulnerabilities,
            "code_smells": code_smells,
            "coverage": coverage,
            "duplication": duplication,
            "maintainability_rating": maintainability_rating,
            "quality_tool": self.quality_tool,
        }

        metadata = {
            "workflow_id": project_name,
            "task_id": analysis_id,
            "tags": ["code_quality", "analysis", project_name, self.quality_tool],
            "priority": 6,
        }

        validation_rules = []
        if self.validate_security:
            validation_rules.extend(["security_vulnerability_analysis", "cvss_scoring"])
        if self.validate_quality:
            validation_rules.extend([
                "code_quality_standards",
                "maintainability_assessment",
                "test_coverage_validation"
            ])

        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=EvidenceType.CODE_ANALYSIS,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=True,
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

    async def close(self):
        """Close adapter connections."""
        await self.http_adapter.close()
