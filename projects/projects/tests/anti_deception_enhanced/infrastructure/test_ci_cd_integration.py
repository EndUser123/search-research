"""
CI/CD Integration Testing

This module implements comprehensive testing for CI/CD integration including
test automation, continuous integration workflows, deployment pipelines, and
infrastructure as code. It validates the DevOps integration capabilities.

Test Categories:
1. Test Automation Framework
2. Continuous Integration Testing
3. Deployment Pipeline Testing
4. Infrastructure as Code Testing
5. Kubernetes Integration Testing
6. Docker Integration Testing
7. Cloud Provider Integration Testing
8. Security and Compliance Testing
"""

import pytest
import time
import json
import yaml
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union, Tuple
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import asyncio
import os
import subprocess
import docker
import kubernetes
import boto3
from pathlib import Path

from anti_deception_enhanced.utils.infrastructure import (
    CICDIntegration, TestAutomation, DeploymentPipeline,
    InfrastructureAsCode, SecurityScanner, ComplianceChecker
)


@dataclass
class TestAutomationScenario:
    """Test scenario for test automation"""
    name: str
    test_type: str
    test_file: str
    expected_result: str
    execution_time: float = 5.0
    dependencies: List[str] = field(default_factory=list)


@dataclass
class CICDPipelineScenario:
    """Test scenario for CI/CD pipeline"""
    name: str
    pipeline_name: str
    trigger_event: str
    expected_stages: List[str]
    expected_result: str
    execution_time: float = 30.0


class TestTestAutomationFramework:
    """Test test automation framework"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_automation = TestAutomation(self.temp_dir)
        self.test_scenarios = [
            TestAutomationScenario(
                name="unit_tests",
                test_type="unit",
                test_file="test_example.py",
                expected_result="success",
                dependencies=["pytest", "coverage"]
            ),
            TestAutomationScenario(
                name="integration_tests",
                test_type="integration",
                test_file="test_integration.py",
                expected_result="success",
                dependencies=["docker", "requests"]
            ),
            TestAutomationScenario(
                name="security_tests",
                test_type="security",
                test_file="test_security.py",
                expected_result="success",
                dependencies["bandit", "safety"]
            ),
            TestAutomationScenario(
                name="performance_tests",
                test_type="performance",
                test_file="test_performance.py",
                expected_result="success",
                dependencies=["locust", "pytest-benchmark"]
            )
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_test_execution(self):
        """Test test execution"""
        for scenario in self.test_scenarios:
            # Create test file
            test_file_path = os.path.join(self.temp_dir, scenario.test_file)
            with open(test_file_path, 'w') as f:
                f.write(self._generate_test_content(scenario.test_type))

            # Execute tests
            result = self.test_automation.execute_tests(
                scenario.test_type,
                test_file_path,
                scenario.dependencies
            )

            # Validate result
            assert result["status"] == scenario.expected_result
            assert result["execution_time"] <= scenario.execution_time
            assert result["test_file"] == scenario.test_file

    def test_test_dependency_resolution(self):
        """Test test dependency resolution"""
        test_file = "test_with_deps.py"
        test_file_path = os.path.join(self.temp_dir, test_file)

        with open(test_file_path, 'w') as f:
            f.write(self._generate_test_content("unit"))

        # Check dependencies
        dependencies = self.test_automation.resolve_dependencies(test_file_path)
        assert "pytest" in dependencies
        assert "coverage" in dependencies

    def test_test_coverage_analysis(self):
        """Test test coverage analysis"""
        test_file = "test_coverage.py"
        test_file_path = os.path.join(self.temp_dir, test_file)

        with open(test_file_path, 'w') as f:
            f.write(self._generate_coverage_test())

        # Analyze coverage
        coverage_result = self.test_automation.analyze_coverage(test_file_path)

        assert coverage_result["total_coverage"] >= 0.0
        assert coverage_result["total_coverage"] <= 1.0
        assert coverage_result["file_coverage"] >= 0.0
        assert coverage_result["file_coverage"] <= 1.0

    def test_test_report_generation(self):
        """Test test report generation"""
        test_results = [
            {
                "test_file": "test_unit.py",
                "status": "passed",
                "execution_time": 0.5,
                "coverage": 0.95
            },
            {
                "test_file": "test_integration.py",
                "status": "failed",
                "execution_time": 2.0,
                "coverage": 0.80
            }
        ]

        # Generate report
        report_path = self.test_automation.generate_report(test_results)

        assert os.path.exists(report_path)
        assert report_path.endswith(".html")

        # Validate report content
        with open(report_path, 'r') as f:
            report_content = f.read()
            assert "Test Results" in report_content
            assert "Coverage Analysis" in report_content
            assert "Summary" in report_content

    def _generate_test_content(self, test_type: str) -> str:
        """Generate test content based on type"""
        if test_type == "unit":
            return """
import pytest

def test_example():
    assert 1 + 1 == 2

def test_another():
    assert "hello" + "world" == "helloworld"
"""
        elif test_type == "integration":
            return """
import requests

def test_api_endpoint():
    response = requests.get("https://api.example.com/health")
    assert response.status_code == 200
"""
        elif test_type == "security":
            return """
import bandit

def test_security_scan():
    # Security test logic
    assert True
"""
        elif test_type == "performance":
            return """
import pytest
import time

def test_performance():
    start_time = time.time()
    # Performance test logic
    end_time = time.time()
    assert end_time - start_time < 1.0
"""
        return ""

    def _generate_coverage_test(self) -> str:
        """Generate coverage test"""
        return """
import sys
import os

sys.path.append(os.path.dirname(__file__))

def function_to_test(x, y):
    return x + y

def test_function():
    assert function_to_test(1, 2) == 3
    assert function_to_test(0, 0) == 0
    assert function_to_test(-1, 5) == 4
"""


class TestContinuousIntegration:
    """Test continuous integration functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.ci_integration = CICDIntegration(self.temp_dir)
        self.pipeline_scenarios = [
            CICDPipelineScenario(
                name="main_branch_pipeline",
                pipeline_name="main-branch-ci",
                trigger_event="push",
                expected_stages=["build", "test", "security", "deploy"],
                expected_result="success"
            ),
            CICDPipelineScenario(
                name="pull_request_pipeline",
                pipeline_name="pr-validation",
                trigger_event="pull_request",
                expected_stages=["lint", "test", "security"],
                expected_result="success"
            ),
            CICDPipelineScenario(
                name="release_pipeline",
                pipeline_name="release-deploy",
                trigger_event="tag",
                expected_stages=["build", "test", "security", "package", "deploy"],
                expected_result="success"
            )
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pipeline_execution(self):
        """Test pipeline execution"""
        for scenario in self.pipeline_scenarios:
            # Create pipeline configuration
            pipeline_config = self._create_pipeline_config(scenario)

            # Execute pipeline
            result = self.ci_integration.execute_pipeline(
                scenario.pipeline_name,
                scenario.trigger_event,
                pipeline_config
            )

            # Validate result
            assert result["status"] == scenario.expected_result
            assert len(result["executed_stages"]) == len(scenario.expected_stages)

            for expected_stage in scenario.expected_stages:
                assert expected_stage in result["executed_stages"]

    def test_pipeline_triggers(self):
        """Test pipeline triggers"""
        trigger_scenarios = [
            ("push", "main", True),
            ("pull_request", "feature-branch", True),
            ("tag", "v1.0.0", True),
            ("schedule", "daily", True),
            ("manual", "trigger", True)
        ]

        for trigger_type, trigger_value, should_trigger in trigger_scenarios:
            should_execute = self.ci_integration.should_trigger_pipeline(
                trigger_type, trigger_value
            )
            assert should_execute == should_trigger

    def test_pipeline_stage_execution(self):
        """Test individual stage execution"""
        stage_configs = [
            {
                "name": "build",
                "command": "python setup.py build",
                "timeout": 300,
                "continue_on_failure": False
            },
            {
                "name": "test",
                "command": "pytest --cov=.",
                "timeout": 600,
                "continue_on_failure": False
            },
            {
                "name": "security",
                "command": "bandit -r .",
                "timeout": 900,
                "continue_on_failure": False
            }
        ]

        for stage_config in stage_configs:
            result = self.ci_integration.execute_stage(stage_config)

            assert result["stage_name"] == stage_config["name"]
            assert "status" in result
            assert "output" in result
            assert "execution_time" in result

    def test_pipeline_monitoring(self):
        """Test pipeline monitoring"""
        # Create mock pipeline execution
        pipeline_id = "test-pipeline-123"
        execution_data = {
            "pipeline_id": pipeline_id,
            "status": "running",
            "stages": [
                {"name": "build", "status": "completed", "duration": 45},
                {"name": "test", "status": "running", "start_time": time.time()},
                {"name": "security", "status": "pending", "duration": 0}
            ],
            "start_time": time.time(),
            "current_stage": "test"
        }

        # Monitor pipeline
        monitoring_result = self.ci_integration.monitor_pipeline(pipeline_id)

        assert monitoring_result["pipeline_id"] == pipeline_id
        assert monitoring_result["status"] == "running"
        assert monitoring_result["progress_percentage"] > 0
        assert monitoring_result["estimated_completion_time"] > 0

    def test_pipeline_artifacts(self):
        """Test pipeline artifacts management"""
        pipeline_id = "test-pipeline-artifacts"
        artifacts = [
            {"name": "build-artifact.tar.gz", "type": "build", "size": 1024000},
            {"name": "test-report.html", "type": "test", "size": 512000},
            {"name": "security-scan.json", "type": "security", "size": 256000}
        ]

        # Store artifacts
        for artifact in artifacts:
            artifact_path = self.ci_integration.store_artifact(
                pipeline_id, artifact["name"], artifact["type"]
            )
            assert os.path.exists(artifact_path)

        # List artifacts
        stored_artifacts = self.ci_integration.list_artifacts(pipeline_id)
        assert len(stored_artifacts) == len(artifacts)

        # Download artifact
        for artifact in artifacts:
            downloaded_path = self.ci_integration.download_artifact(
                pipeline_id, artifact["name"]
            )
            assert os.path.exists(downloaded_path)

    def _create_pipeline_config(self, scenario: CICDPipelineScenario) -> Dict[str, Any]:
        """Create pipeline configuration"""
        return {
            "name": scenario.pipeline_name,
            "trigger": scenario.trigger_event,
            "stages": [
                {
                    "name": stage,
                    "commands": [f"echo 'Executing {stage}'"],
                    "timeout": 300,
                    "continue_on_failure": False
                }
                for stage in scenario.expected_stages
            ],
            "artifacts": [],
            "notifications": []
        }


class TestDeploymentPipeline:
    """Test deployment pipeline functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.deployment_pipeline = DeploymentPipeline(self.temp_dir)

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deployment_strategies(self):
        """Test deployment strategies"""
        deployment_configs = [
            {
                "name": "blue_green_deployment",
                "strategy": "blue-green",
                "expected_stages": ["build", "deploy-green", "switch-traffic", "cleanup-blue"],
                "rollback_supported": True
            },
            {
                "name": "rolling_deployment",
                "strategy": "rolling",
                "expected_stages": ["build", "deploy-incremental", "health-check"],
                "rollback_supported": True
            },
            {
                "name": "canary_deployment",
                "strategy": "canary",
                "expected_stages": ["build", "deploy-canary", "test-canary", "promote-canary"],
                "rollback_supported": True
            }
        ]

        for config in deployment_configs:
            # Execute deployment
            result = self.deployment_pipeline.deploy(
                config["name"],
                config["strategy"],
                {}
            )

            # Validate result
            assert result["status"] == "success"
            assert len(result["executed_stages"]) == len(config["expected_stages"])

            for expected_stage in config["expected_stages"]:
                assert expected_stage in result["executed_stages"]

            # Test rollback
            if config["rollback_supported"]:
                rollback_result = self.deployment_pipeline.rollback(config["name"])
                assert rollback_result["status"] == "success"

    def test_deployment_health_checks(self):
        """Test deployment health checks"""
        health_check_scenarios = [
            {
                "name": "http_health_check",
                "type": "http",
                "endpoint": "https://api.example.com/health",
                "expected_status": 200
            },
            {
                "name": "tcp_health_check",
                "type": "tcp",
                "host": "localhost",
                "port": 8080,
                "expected_result": "success"
            },
            {
                "name": "custom_health_check",
                "type": "custom",
                "command": "python health_check.py",
                "expected_output": "healthy"
            }
        ]

        for scenario in health_check_scenarios:
            result = self.deployment_pipeline.perform_health_check(scenario)

            assert result["check_name"] == scenario["name"]
            assert result["status"] == "success"
            assert "execution_time" in result

    def test_deployment_rollback(self):
        """Test deployment rollback functionality"""
        deployment_name = "test-deployment"

        # Simulate deployment
        deployment_result = self.deployment_pipeline.deploy(deployment_name, "blue-green", {})
        assert deployment_result["status"] == "success"

        # Simulate failure
        failure_scenarios = [
            "health_check_failed",
            "deployment_timeout",
            "resource_unavailable",
            "configuration_error"
        ]

        for failure_type in failure_scenarios:
            # Mark deployment as failed
            self.deployment_pipeline.mark_deployment_failed(deployment_name, failure_type)

            # Perform rollback
            rollback_result = self.deployment_pipeline.rollback(deployment_name)

            assert rollback_result["status"] == "success"
            assert rollback_result["rollback_reason"] == failure_type

    def test_deployment_scaling(self):
        """Test deployment scaling"""
        scaling_configs = [
            {
                "name": "horizontal_scaling",
                "type": "horizontal",
                "current_replicas": 3,
                "target_replicas": 5,
                "expected_duration": 60
            },
            {
                "name": "vertical_scaling",
                "type": "vertical",
                "current_memory": "2Gi",
                "target_memory": "4Gi",
                "expected_duration": 120
            }
        ]

        for config in scaling_configs:
            result = self.deployment_pipeline.scale_deployment(config)

            assert result["scaling_type"] == config["type"]
            assert result["status"] == "success"
            assert result["execution_time"] <= config["expected_duration"]

    def test_deployment_monitoring(self):
        """Test deployment monitoring"""
        deployment_name = "test-deployment"

        # Mock deployment metrics
        metrics_data = {
            "deployment_name": deployment_name,
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "request_rate": 125.3,
            "error_rate": 0.5,
            "response_time": 125.0
        }

        # Get deployment metrics
        metrics = self.deployment_pipeline.get_deployment_metrics(deployment_name)

        assert metrics["deployment_name"] == deployment_name
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "health_status" in metrics

        # Check deployment health
        health_status = self.deployment_pipeline.get_deployment_health(deployment_name)
        assert health_status["status"] in ["healthy", "unhealthy", "degraded"]

        # Monitor deployment events
        events = self.deployment_pipeline.monitor_deployment_events(deployment_name)
        assert isinstance(events, list)
        assert len(events) >= 0


class TestInfrastructureAsCode:
    """Test infrastructure as code functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.infra_as_code = InfrastructureAsCode(self.temp_dir)
        self.test_configs = [
            {
                "name": "kubernetes_deployment",
                "type": "kubernetes",
                "file": "deployment.yaml",
                "content": self._generate_k8s_deployment()
            },
            {
                "name": "terraform_infrastructure",
                "type": "terraform",
                "file": "main.tf",
                "content": self._generate_terraform_config()
            },
            {
                "name": "docker_compose",
                "type": "docker",
                "file": "docker-compose.yml",
                "content": self._generate_docker_compose()
            }
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_infrastructure_validation(self):
        """Test infrastructure code validation"""
        for config in self.test_configs:
            # Create infrastructure file
            config_path = os.path.join(self.temp_dir, config["file"])
            with open(config_path, 'w') as f:
                f.write(config["content"])

            # Validate infrastructure
            validation_result = self.infra_as_code.validate_infrastructure(
                config["type"], config_path
            )

            assert validation_result["is_valid"] is True
            assert validation_result["file_type"] == config["type"]

    def test_infrastructure_deployment(self):
        """Test infrastructure deployment"""
        for config in self.test_configs:
            # Create infrastructure file
            config_path = os.path.join(self.temp_dir, config["file"])
            with open(config_path, 'w') as f:
                f.write(config["content"])

            # Deploy infrastructure
            deployment_result = self.infra_as_code.deploy_infrastructure(
                config["type"], config_path
            )

            assert deployment_result["status"] == "success"
            assert deployment_result["deployment_id"] is not None
            assert "resources_created" in deployment_result

    def test_infrastructure_templating(self):
        """Test infrastructure templating"""
        template_configs = [
            {
                "name": "k8s_template",
                "template": self._generate_k8s_template(),
                "variables": {
                    "app_name": "test-app",
                    "replicas": 3,
                    "image": "test-image:latest"
                }
            },
            {
                "name": "terraform_template",
                "template": self._generate_terraform_template(),
                "variables": {
                    "aws_region": "us-east-1",
                    "instance_type": "t3.micro",
                    "environment": "test"
                }
            }
        ]

        for config in template_configs:
            # Render template
            rendered_path = self.infra_as_code.render_template(
                config["template"], config["variables"]
            )

            assert os.path.exists(rendered_path)

            # Validate rendered content
            with open(rendered_path, 'r') as f:
                rendered_content = f.read()

            for variable_name, variable_value in config["variables"].items():
                assert str(variable_value) in rendered_content

    def test_infrastructure_state_management(self):
        """Test infrastructure state management"""
        # Initialize state
        state_init_result = self.infra_as_code.initialize_state("terraform")
        assert state_init_result["success"] is True

        # Get state
        state_data = self.infra_as_code.get_state("terraform")
        assert state_data is not None
        assert "resources" in state_data

        # Lock state
        lock_result = self.infra_as_code.lock_state("terraform")
        assert lock_result["success"] is True

        # Unlock state
        unlock_result = self.infra_as_code.unlock_state("terraform")
        assert unlock_result["success"] is True

    def test_infrastructure_drift_detection(self):
        """Test infrastructure drift detection"""
        # Create infrastructure
        config_path = os.path.join(self.temp_dir, "test.tf")
        with open(config_path, 'w') as f:
            f.write(self._generate_terraform_config())

        # Deploy infrastructure
        self.infra_as_code.deploy_infrastructure("terraform", config_path)

        # Simulate drift by modifying configuration
        modified_content = self._generate_terraform_config_modified()
        with open(config_path, 'w') as f:
            f.write(modified_content)

        # Detect drift
        drift_result = self.infra_as_code.detect_drift("terraform", config_path)

        assert drift_result["drift_detected"] is True
        assert len(drift_result["drifted_resources"]) > 0

    def _generate_k8s_deployment(self) -> str:
        """Generate Kubernetes deployment configuration"""
        return """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: test-container
        image: nginx:latest
        ports:
        - containerPort: 80
"""

    def _generate_terraform_config(self) -> str:
        """Generate Terraform configuration"""
        return """
provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket"
}
"""

    def _generate_docker_compose(self) -> str:
        """Generate Docker Compose configuration"""
        return """
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: example
"""

    def _generate_k8s_template(self) -> str:
        """Generate Kubernetes template"""
        return """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .app_name }}
spec:
  replicas: {{ .replicas }}
  selector:
    matchLabels:
      app: {{ .app_name }}
  template:
    metadata:
      labels:
        app: {{ .app_name }}
    spec:
      containers:
      - name: {{ .app_name }}
        image: {{ .image }}
"""

    def _generate_terraform_template(self) -> str:
        """Generate Terraform template"""
        return """
provider "aws" {
  region = "{{ .aws_region }}"
}

resource "aws_instance" "{{ .environment }}_instance" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "{{ .instance_type }}"
}

resource "aws_s3_bucket" "{{ .environment }}_bucket" {
  bucket = "{{ .environment }}-example-bucket"
}
"""

    def _generate_terraform_config_modified(self) -> str:
        """Generate modified Terraform configuration"""
        return """
provider "aws" {
  region = "us-west-2"  # Changed region to simulate drift
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"  # Changed instance type
}

resource "aws_s3_bucket" "example" {
  bucket = "example-bucket"
}
"""


class TestSecurityAndCompliance:
    """Test security and compliance functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.security_scanner = SecurityScanner(self.temp_dir)
        self.compliance_checker = ComplianceChecker(self.temp_dir)

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_security_scanning(self):
        """Test security scanning"""
        # Create test files with potential security issues
        test_files = [
            ("insecure_file.py", self._generate_insecure_python_code()),
            ("vulnerable_config.json", self._generate_vulnerable_config()),
            ("weak_passwords.txt", self._generate_weak_passwords())
        ]

        for filename, content in test_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)

            # Perform security scan
            scan_result = self.security_scanner.scan_file(file_path)

            assert scan_result["file_path"] == file_path
            assert "security_score" in scan_result
            assert "vulnerabilities" in scan_result
            assert len(scan_result["vulnerabilities"]) > 0

    def test_compliance_validation(self):
        """Test compliance validation"""
        compliance_frameworks = [
            "cis_benchmark",
            "nist_csf",
            "soc2",
            "iso27001",
            "gdpr"
        ]

        for framework in compliance_frameworks:
            # Validate compliance
            compliance_result = self.compliance_checker.validate_compliance(framework)

            assert compliance_result["framework"] == framework
            assert "compliance_score" in compliance_result
            assert "failed_controls" in compliance_result
            assert "passed_controls" in compliance_result

    def test_vulnerability_management(self):
        """Test vulnerability management"""
        # Create vulnerability database
        vuln_database = {
            "cve_2021_44228": {
                "severity": "critical",
                "affected_versions": ["1.0", "1.1", "2.0"],
                "fix_available": True,
                "fix_version": "2.1"
            },
            "cve_2021_45046": {
                "severity": "high",
                "affected_versions": ["1.0", "1.1"],
                "fix_available": True,
                "fix_version": "1.2"
            }
        }

        # Check for vulnerabilities
        vulnerabilities = self.security_scanner.check_vulnerabilities(
            "test-package", "1.0", vuln_database
        )

        assert len(vulnerabilities) > 0
        assert vulnerabilities[0]["cve_id"] == "cve_2021_44228"
        assert vulnerabilities[0]["severity"] == "critical"

        # Generate remediation report
        remediation_report = self.security_scanner.generate_remediation_report(vulnerabilities)

        assert "vulnerabilities" in remediation_report
        assert "recommended_actions" in remediation_report
        assert "remediation_priority" in remediation_report

    def test_audit_logging(self):
        """Test audit logging"""
        # Create audit log configuration
        audit_config = {
            "log_level": "info",
            "log_format": "json",
            "log_retention_days": 90,
            "log_rotation": True
        }

        # Configure audit logging
        config_result = self.security_scanner.configure_audit_logging(audit_config)

        assert config_result["success"] is True
        assert "audit_log_path" in config_result

        # Generate audit events
        audit_events = [
            {
                "event_type": "user_login",
                "user": "test_user",
                "timestamp": datetime.now().isoformat(),
                "result": "success"
            },
            {
                "event_type": "file_access",
                "user": "test_user",
                "file_path": "/etc/passwd",
                "timestamp": datetime.now().isoformat(),
                "result": "denied"
            }
        ]

        for event in audit_events:
            log_result = self.security_scanner.log_audit_event(event)
            assert log_result["success"] is True

        # Retrieve audit logs
        audit_logs = self.security_scanner.get_audit_logs(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )

        assert len(audit_logs) >= 0

    def _generate_insecure_python_code(self) -> str:
        """Generate insecure Python code for testing"""
        return """
import subprocess
import os

def execute_command(user_input):
    # Vulnerable to command injection
    os.system(f"rm -rf {user_input}")

def weak_encryption():
    # Weak encryption
    secret = "secret_key".encode()
    encrypted = base64.b64encode(secret)
    return encrypted

def hard-coded_password():
    # Hard-coded password
    password = "admin123"
    return password
"""

    def _generate_vulnerable_config(self) -> str:
        """Generate vulnerable configuration for testing"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "weak_password",  # Weak password
                "ssl_enabled": False  # SSL disabled
            },
            "api": {
                "rate_limit": 10000,  # Very high rate limit
                "authentication": "none",  # No authentication
                "cors_enabled": True  # CORS enabled without restrictions
            }
        }

    def _generate_weak_passwords(self) -> str:
        """Generate weak passwords for testing"""
        return """
123456
password
123456789
qwerty
abc123
admin
welcome
"""

    def test_policy_validation(self):
        """Test policy validation"""
        security_policies = [
            {
                "name": "password_policy",
                "rules": [
                    {"type": "min_length", "value": 8},
                    {"type": "require_numbers", "value": True},
                    {"type": "require_special_chars", "value": True}
                ]
            },
            {
                "name": "access_control_policy",
                "rules": [
                    {"type": "principle_of_least_privilege", "value": True},
                    {"type": "role_based_access", "value": True}
                ]
            }
        ]

        for policy in security_policies:
            # Test policy validation
            validation_result = self.security_scanner.validate_policy(policy)

            assert validation_result["policy_name"] == policy["name"]
            assert "validation_score" in validation_result
            assert "violations" in validation_result

    def test_security_compliance_reporting(self):
        """Test security and compliance reporting"""
        # Generate comprehensive security report
        security_report = self.security_scanner.generate_security_report()

        assert "overall_security_score" in security_report
        assert "vulnerabilities_summary" in security_report
        assert "compliance_status" in security_report
        assert "recommendations" in security_report

        # Generate compliance report
        compliance_report = self.compliance_checker.generate_compliance_report()

        assert "compliance_score" in compliance_report
        assert "frameworks_compliance" in compliance_report
        assert "remediation_plan" in compliance_report


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
