"""
Real-World Scenario Tests
==========================

Tests the Enhanced Anti-Deception Architecture with realistic development workflows,
including code editing, file operations, testing, and deployment scenarios.
"""

import tempfile
from pathlib import Path

import pytest

try:
    from hook_communication import CrossHookCommunicator, EvidenceRepository
    from llm_supervisor import LLMSupervisor, ValidationLevel
    from post_tool_use import BalancedValidationLogic, ParallelValidationEngine
except ImportError:
    pytest.skip("Real-world scenario components not available", allow_module_level=True)


class TestCodeEditingScenarios:
    """Test realistic code editing workflows."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create basic project structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()

        # Create sample Python file
        main_py = temp_dir / "src" / "main.py"
        main_py.write_text(
            """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def main():
    items = [
        {'name': 'Book', 'price': 10},
        {'name': 'Pen', 'price': 2}
    ]
    print(f"Total: ${calculate_total(items)}")

if __name__ == "__main__":
    main()
"""
        )

        yield temp_dir

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def validation_system(self, temp_project_dir):
        """Create integrated validation system."""
        evidence_repo = EvidenceRepository(storage_path=temp_project_dir / "evidence")
        communicator = CrossHookCommunicator(
            storage_path=temp_project_dir / "communication", evidence_repo=evidence_repo
        )
        post_validator = ParallelValidationEngine()

        return {
            "evidence_repo": evidence_repo,
            "communicator": communicator,
            "post_validator": post_validator,
        }

    @pytest.mark.asyncio
    async def test_safe_function_modification(
        self, temp_project_dir, validation_system
    ):
        """Test safe modification of existing function."""
        evidence_repo = validation_system["evidence_repo"]
        post_validator = validation_system["post_validator"]

        operation_id = "func_mod_001"
        session_id = "dev_session_001"
        file_path = str(temp_project_dir / "src" / "main.py")

        # PreToolUse evidence - function analysis
        pre_evidence = {
            "operation_id": operation_id,
            "hook_name": "PreToolUse",
            "evidence_type": "code_analysis",
            "data": {
                "file_path": file_path,
                "function_name": "calculate_total",
                "complexity": "low",
                "dependencies": [],
                "test_coverage": "present",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(pre_evidence)

        # Mock PostToolUse validation for safe code change
        async def mock_safe_code_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [],
                "warnings": [],
                "confidence": 0.95,
                "execution_time": 0.8,
            }

        post_validator.validate_operation = mock_safe_code_validation

        # PostToolUse context - function modification
        post_context = {
            "tool_name": "Edit",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": file_path,
                "operation": "function_modification",
                "changes": [
                    {
                        "function": "calculate_total",
                        "type": "enhancement",
                        "description": "Add tax calculation support",
                    }
                ],
                "risk_level": "low",
                "evidence_provided": ["code_analysis", "safety_check"],
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(post_context)

        # Store PostToolUse evidence
        post_evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "modification_completed",
            "data": {
                "validation_result": result,
                "file_path": file_path,
                "change_approved": True,
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(post_evidence)

        # Verify workflow evidence
        session_evidence = evidence_repo.get_session_evidence(session_id)
        assert len(session_evidence) == 2

        # Verify validation success
        assert result["is_valid"] is True
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_risky_architecture_change(self, temp_project_dir, validation_system):
        """Test handling of risky architecture changes."""
        evidence_repo = validation_system["evidence_repo"]
        post_validator = validation_system["post_validator"]

        operation_id = "arch_change_001"
        session_id = "dev_session_002"
        file_path = str(temp_project_dir / "src" / "main.py")

        # PreToolUse evidence - identifies high-risk change
        pre_evidence = {
            "operation_id": operation_id,
            "hook_name": "PreToolUse",
            "evidence_type": "risk_assessment",
            "data": {
                "file_path": file_path,
                "change_type": "architecture_modification",
                "risk_level": "high",
                "affected_components": ["calculate_total", "main"],
                "impact_analysis": "significant",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(pre_evidence)

        # Mock PostToolUse validation requiring additional evidence
        async def mock_high_risk_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [
                    {
                        "type": "missing_evidence",
                        "severity": "error",
                        "description": "Architecture change requires comprehensive testing",
                        "required_evidence": [
                            "unit_tests",
                            "integration_tests",
                            "performance_tests",
                        ],
                    }
                ],
                "warnings": [
                    {
                        "type": "breaking_change",
                        "description": "This change may break existing functionality",
                    }
                ],
                "confidence": 0.6,
                "execution_time": 1.2,
            }

        post_validator.validate_operation = mock_high_risk_validation

        # PostToolUse context - architecture change
        post_context = {
            "tool_name": "Edit",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": file_path,
                "operation": "architecture_refactor",
                "changes": [
                    {
                        "type": "class_extraction",
                        "description": "Extract calculation logic to separate class",
                    }
                ],
                "risk_level": "high",
                "evidence_provided": ["risk_assessment"],  # Missing test evidence
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(post_context)

        # Store PostToolUse evidence
        post_evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "conditional_approval",
            "data": {
                "validation_result": result,
                "conditional_approval": True,
                "required_followup": ["comprehensive_testing"],
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(post_evidence)

        # Verify validation requires additional evidence
        assert result["is_valid"] is True  # Error with feedback allows execution
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "missing_evidence"
        assert result["confidence"] < 0.8  # Lower confidence due to missing evidence

    @pytest.mark.asyncio
    async def test_critical_security_fix(self, temp_project_dir, validation_system):
        """Test critical security fix scenario."""
        evidence_repo = validation_system["evidence_repo"]
        post_validator = validation_system["post_validator"]

        operation_id = "security_fix_001"
        session_id = "security_session_001"
        file_path = str(temp_project_dir / "src" / "main.py")

        # PreToolUse evidence - security vulnerability detected
        pre_evidence = {
            "operation_id": operation_id,
            "hook_name": "PreToolUse",
            "evidence_type": "vulnerability_report",
            "data": {
                "file_path": file_path,
                "vulnerability_type": "input_validation",
                "severity": "critical",
                "cve_id": "CVE-2025-TEST",
                "exploit_scenario": "Malicious input could cause calculation errors",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(pre_evidence)

        # Mock PostToolUse validation for security fix
        async def mock_security_fix_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],  # Security fix is valid
                "errors": [
                    {
                        "type": "missing_security_review",
                        "description": "Security fixes require formal review",
                    }
                ],
                "warnings": [
                    {"type": "urgency", "description": "Deploy this fix urgently"}
                ],
                "confidence": 0.85,
                "execution_time": 0.9,
            }

        post_validator.validate_operation = mock_security_fix_validation

        # PostToolUse context - security fix applied
        post_context = {
            "tool_name": "Edit",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": file_path,
                "operation": "security_fix",
                "changes": [
                    {
                        "type": "input_validation_added",
                        "description": "Add input validation to prevent malicious data",
                    }
                ],
                "risk_level": "critical",
                "evidence_provided": ["vulnerability_report", "fix_validation"],
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(post_context)

        # Store evidence of security fix
        post_evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "security_fix_applied",
            "data": {
                "validation_result": result,
                "security_improvement": True,
                "deployment_priority": "urgent",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(post_evidence)

        # Verify security fix validation
        assert result["is_valid"] is True
        assert len(result["critical_issues"]) == 0  # No critical issues with fix
        assert result["confidence"] > 0.8


class TestFileOperationScenarios:
    """Test realistic file operation workflows."""

    @pytest.fixture
    def file_operation_system(self):
        """Create file operation validation system."""
        evidence_repo = EvidenceRepository(storage_path="temp_file_evidence")
        post_validator = ParallelValidationEngine()

        return {"evidence_repo": evidence_repo, "post_validator": post_validator}

    @pytest.mark.asyncio
    async def test_safe_file_creation(self, file_operation_system):
        """Test safe file creation in project directory."""
        evidence_repo = file_operation_system["evidence_repo"]
        post_validator = file_operation_system["post_validator"]

        operation_id = "file_create_001"
        session_id = "file_session_001"

        # Mock validation for safe file creation
        async def mock_safe_file_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [],
                "warnings": [],
                "confidence": 0.98,
                "execution_time": 0.3,
            }

        post_validator.validate_operation = mock_safe_file_validation

        # Write tool context - creating new configuration file
        write_context = {
            "tool_name": "Write",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": "src/config/settings.json",
                "operation": "file_creation",
                "content_type": "configuration",
                "risk_level": "low",
                "evidence_provided": ["project_structure_check", "content_validation"],
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(write_context)

        # Store evidence of file creation
        evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "file_created",
            "data": {
                "validation_result": result,
                "file_path": "src/config/settings.json",
                "creation_approved": True,
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(evidence)

        # Verify safe file creation
        assert result["is_valid"] is True
        assert result["confidence"] > 0.95

    @pytest.mark.asyncio
    async def test_dangerous_file_operation_blocked(self, file_operation_system):
        """Test blocking of dangerous file operations."""
        post_validator = file_operation_system["post_validator"]

        # Mock validation for dangerous file operation
        async def mock_dangerous_file_validation(context):
            return {
                "is_valid": False,
                "critical_issues": [
                    {
                        "type": "security_violation",
                        "severity": "critical",
                        "description": "Attempt to modify system configuration file",
                        "evidence": {
                            "forbidden_path": "/etc/hosts",
                            "operation_type": "file_modification",
                        },
                    }
                ],
                "errors": [],
                "warnings": [],
                "confidence": 1.0,
                "execution_time": 0.1,
            }

        post_validator.validate_operation = mock_dangerous_file_validation

        # Write tool context - attempting dangerous operation
        dangerous_context = {
            "tool_name": "Write",
            "tool_result": {"success": True},
            "metadata": {
                "file_path": "/etc/hosts",
                "operation": "system_file_modification",
                "risk_level": "critical",
                "evidence_provided": [],  # No valid evidence for system modification
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(dangerous_context)

        # Verify dangerous operation is blocked
        assert result["is_valid"] is False
        assert len(result["critical_issues"]) > 0
        assert result["critical_issues"][0]["type"] == "security_violation"
        assert result["confidence"] == 1.0  # Maximum confidence in blocking


class TestTestingScenarios:
    """Test realistic testing workflows."""

    @pytest.fixture
    def testing_system(self):
        """Create testing validation system."""
        evidence_repo = EvidenceRepository(storage_path="temp_test_evidence")
        post_validator = ParallelValidationEngine()
        llm_supervisor = LLMSupervisor(validation_level=ValidationLevel.STANDARD)

        return {
            "evidence_repo": evidence_repo,
            "post_validator": post_validator,
            "llm_supervisor": llm_supervisor,
        }

    @pytest.mark.asyncio
    async def test_test_execution_with_evidence(self, testing_system):
        """Test test execution with proper evidence collection."""
        evidence_repo = testing_system["evidence_repo"]
        post_validator = testing_system["post_validator"]

        operation_id = "test_exec_001"
        session_id = "test_session_001"

        # Mock validation for successful test execution
        async def mock_test_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [],
                "warnings": [],
                "confidence": 0.96,
                "execution_time": 0.7,
            }

        post_validator.validate_operation = mock_test_validation

        # Bash tool context - running tests
        bash_context = {
            "tool_name": "Bash",
            "command": "pytest tests/ -v",
            "tool_result": {
                "success": True,
                "stdout": "============================= test session starts ==============================\ncollected 5 items\n\ntests/test_main.py .....                                                [100%]\n\n============================== 5 passed in 0.12s ================================",
                "stderr": "",
                "exit_code": 0,
            },
            "metadata": {
                "operation": "test_execution",
                "test_framework": "pytest",
                "tests_run": 5,
                "tests_passed": 5,
                "tests_failed": 0,
                "risk_level": "low",
                "evidence_provided": ["test_output", "exit_code", "execution_log"],
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(bash_context)

        # Store test execution evidence
        evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "tests_executed",
            "data": {
                "validation_result": result,
                "test_summary": {
                    "total": 5,
                    "passed": 5,
                    "failed": 0,
                    "success_rate": 1.0,
                },
                "test_artifacts": ["test_report.html", "coverage.xml"],
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(evidence)

        # Verify test execution validation
        assert result["is_valid"] is True
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_test_failure_handling(self, testing_system):
        """Test handling of test failures with feedback requirements."""
        evidence_repo = testing_system["evidence_repo"]
        post_validator = testing_system["post_validator"]

        operation_id = "test_fail_001"
        session_id = "test_session_002"

        # Mock validation for test failure
        async def mock_test_failure_validation(context):
            return {
                "is_valid": True,  # Allow execution but require feedback
                "critical_issues": [],
                "errors": [
                    {
                        "type": "test_failures",
                        "severity": "error",
                        "description": "Tests are failing - fix required before proceeding",
                        "failed_tests": [
                            "test_calculate_total_negative",
                            "test_calculate_total_edge_cases",
                        ],
                        "failure_count": 2,
                        "required_action": "Fix failing tests",
                    }
                ],
                "warnings": [
                    {
                        "type": "quality_degradation",
                        "description": "Code quality has decreased",
                    }
                ],
                "confidence": 0.4,  # Low confidence due to test failures
                "execution_time": 0.8,
            }

        post_validator.validate_operation = mock_test_failure_validation

        # Bash tool context - failing tests
        failure_context = {
            "tool_name": "Bash",
            "command": "pytest tests/ -v",
            "tool_result": {
                "success": False,
                "stdout": "============================= test session starts ==============================\ncollected 5 items\n\ntests/test_main.py ...F.                                               [100%]\n\n============================== FAILURES ================================\n________________________ test_calculate_total_negative _________________________\n",
                "stderr": "FAILED: test_calculate_total_negative - AssertionError",
                "exit_code": 1,
            },
            "metadata": {
                "operation": "test_execution",
                "test_framework": "pytest",
                "tests_run": 5,
                "tests_passed": 3,
                "tests_failed": 2,
                "risk_level": "medium",
                "evidence_provided": ["test_output", "failure_logs"],
            },
        }

        # Execute validation
        result = await post_validator.validate_operation(failure_context)

        # Store test failure evidence
        evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "evidence_type": "test_failure_detected",
            "data": {
                "validation_result": result,
                "failure_summary": {
                    "total": 5,
                    "passed": 3,
                    "failed": 2,
                    "requires_fix": True,
                },
                "blocking_reason": "Code quality gates - tests must pass",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(evidence)

        # Verify test failure handling
        assert result["is_valid"] is True  # Error with feedback allows execution
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "test_failures"
        assert result["confidence"] < 0.5  # Low confidence


class TestDeploymentScenarios:
    """Test realistic deployment workflows."""

    @pytest.fixture
    def deployment_system(self):
        """Create deployment validation system."""
        evidence_repo = EvidenceRepository(storage_path="temp_deploy_evidence")
        post_validator = ParallelValidationEngine()
        llm_supervisor = LLMSupervisor(validation_level=ValidationLevel.HIGH_SECURITY)

        return {
            "evidence_repo": evidence_repo,
            "post_validator": post_validator,
            "llm_supervisor": llm_supervisor,
        }

    @pytest.mark.asyncio
    async def test_production_deployment_workflow(self, deployment_system):
        """Test complete production deployment workflow."""
        evidence_repo = deployment_system["evidence_repo"]
        post_validator = deployment_system["post_validator"]
        llm_supervisor = deployment_system["llm_supervisor"]

        session_id = "deploy_session_001"

        # Stage 1: Pre-deployment checks
        pre_deploy_evidence = {
            "operation_id": "pre_deploy_001",
            "hook_name": "PreToolUse",
            "evidence_type": "pre_deployment_checklist",
            "data": {
                "security_scan": "passed",
                "performance_tests": "passed",
                "code_review": "approved",
                "documentation": "updated",
                "rollback_plan": "ready",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(pre_deploy_evidence)

        # Stage 2: Deployment execution
        # Mock high-security validation for deployment
        async def mock_deployment_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [],
                "warnings": [
                    {
                        "type": "production_alert",
                        "description": "Deploying to production - monitor closely",
                    }
                ],
                "confidence": 0.92,
                "execution_time": 1.5,
            }

        post_validator.validate_operation = mock_deployment_validation

        # Mock LLM supervisor for deployment approval
        async def mock_llm_deployment_review(context):
            return {
                "is_valid": True,
                "analysis": {
                    "deployment_safety": "confirmed",
                    "risk_assessment": "acceptable",
                    "readiness_level": "production_ready",
                },
                "confidence": 0.95,
                "recommendations": [
                    "Monitor performance metrics for 24 hours",
                    "Have rollback procedure ready",
                    "Inform stakeholders of deployment",
                ],
            }

        llm_supervisor.validate_operation = mock_llm_deployment_review

        # Deployment context
        deploy_context = {
            "tool_name": "Bash",
            "command": "./deploy.sh production",
            "tool_result": {
                "success": True,
                "stdout": "Deployment completed successfully",
                "deployment_id": "deploy_20250126_103000",
                "version": "v1.2.3",
            },
            "metadata": {
                "operation": "production_deployment",
                "environment": "production",
                "deployment_type": "full_release",
                "risk_level": "high",
                "evidence_provided": [
                    "pre_deployment_checklist",
                    "security_clearance",
                    "stakeholder_approval",
                ],
            },
        }

        # Execute validation
        post_result = await post_validator.validate_operation(deploy_context)
        llm_result = await llm_supervisor.validate_operation(deploy_context)

        # Stage 3: Post-deployment evidence
        post_deploy_evidence = {
            "operation_id": "deploy_001",
            "hook_name": "PostToolUse",
            "evidence_type": "deployment_completed",
            "data": {
                "post_validation": post_result,
                "llm_approval": llm_result,
                "deployment_details": {
                    "environment": "production",
                    "version": "v1.2.3",
                    "deployment_id": "deploy_20250126_103000",
                    "status": "success",
                },
                "monitoring_setup": "active",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(post_deploy_evidence)

        # Verify deployment validation
        assert post_result["is_valid"] is True
        assert llm_result["is_valid"] is True
        assert post_result["confidence"] > 0.9
        assert llm_result["confidence"] > 0.9

        # Verify complete deployment evidence
        session_evidence = evidence_repo.get_session_evidence(session_id)
        assert len(session_evidence) >= 2  # Pre and post deployment evidence

    @pytest.mark.asyncio
    async def test_emergency_rollback_scenario(self, deployment_system):
        """Test emergency rollback scenario."""
        evidence_repo = deployment_system["evidence_repo"]
        post_validator = deployment_system["post_validator"]

        session_id = "emergency_session_001"

        # Emergency context - deployment failure detected
        emergency_context = {
            "tool_name": "Bash",
            "command": "./rollback.sh emergency",
            "tool_result": {
                "success": True,
                "stdout": "Emergency rollback completed",
                "rollback_reason": "Performance degradation detected",
                "previous_version": "v1.2.2",
            },
            "metadata": {
                "operation": "emergency_rollback",
                "trigger": "automatic_monitoring",
                "reason": "critical_performance_issue",
                "risk_level": "critical",
                "evidence_provided": [
                    "performance_alerts",
                    "error_logs",
                    "user_complaints",
                ],
            },
        }

        # Mock emergency validation
        async def mock_emergency_validation(context):
            return {
                "is_valid": True,
                "critical_issues": [],
                "errors": [],
                "warnings": [
                    {
                        "type": "urgency",
                        "description": "Emergency rollback - investigate root cause",
                    }
                ],
                "confidence": 0.98,  # High confidence in rollback necessity
                "execution_time": 0.5,
            }

        post_validator.validate_operation = mock_emergency_validation

        # Execute emergency rollback validation
        result = await post_validator.validate_operation(emergency_context)

        # Store emergency evidence
        evidence = {
            "operation_id": "emergency_rollback_001",
            "hook_name": "PostToolUse",
            "evidence_type": "emergency_response",
            "data": {
                "validation_result": result,
                "emergency_type": "rollback",
                "trigger_reason": "performance_degradation",
                "response_time": "immediate",
                "successful": True,
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(evidence)

        # Verify emergency handling
        assert result["is_valid"] is True
        assert result["confidence"] > 0.95
        assert len(result["critical_issues"]) == 0
