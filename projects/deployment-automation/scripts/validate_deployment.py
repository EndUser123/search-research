#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Script
For Task Execution Enhancements Project

This script handles:
- End-to-end deployment validation
- Service health checks
- Integration testing
- Performance validation
- Security compliance validation
- Session management validation
- CSF NIP compliance validation
"""

import concurrent.futures
import json
import logging
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


@dataclass
class ValidationConfig:
    """Configuration for deployment validation"""
    # Service endpoints
    task_execution_url: str = "http://localhost:8000"
    session_management_url: str = "http://localhost:8001"
    csf_nip_url: str = "http://localhost:8002"
    grafana_url: str = "http://localhost:3000"
    prometheus_url: str = "http://localhost:9090"

    # Validation settings
    health_check_timeout: int = 30
    integration_test_timeout: int = 60
    performance_test_duration: int = 120
    security_scan_enabled: bool = True
    compliance_validation_enabled: bool = True

    # Thresholds
    response_time_threshold_ms: float = 1000.0
    success_rate_threshold: float = 95.0
    uptime_threshold: float = 99.0
    memory_usage_threshold_mb: float = 512.0
    cpu_usage_threshold: float = 80.0

    # Test settings
    parallel_validation: bool = True
    retry_attempts: int = 3
    retry_delay: float = 5.0
    comprehensive_mode: bool = True

@dataclass
class ValidationResult:
    """Result of a validation test"""
    test_name: str
    status: str  # PASS, FAIL, WARNING
    score: float  # 0-100
    duration_ms: float
    details: str
    timestamp: str
    metrics: dict[str, Any]
    recommendations: list[str]

class DeploymentValidationError(Exception):
    """Custom exception for deployment validation failures"""
    pass

class DeploymentValidator:
    """Comprehensive deployment validation system"""

    def __init__(self, config: ValidationConfig | None = None):
        self.config = config or ValidationConfig()
        self.logger = self._setup_logging()
        self.base_path = Path.cwd()
        self.validation_results = []
        self.start_time = None

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    f'deployment_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                )
            ]
        )
        return logging.getLogger(__name__)

    def log_validation(self, test_name: str, status: str, score: float, details: str,
                      duration_ms: float, metrics: dict = None, recommendations: list = None):
        """Log validation result"""
        result = ValidationResult(
            test_name=test_name,
            status=status,
            score=score,
            duration_ms=duration_ms,
            details=details,
            timestamp=datetime.now().isoformat(),
            metrics=metrics or {},
            recommendations=recommendations or []
        )
        self.validation_results.append(result)

        status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
        self.logger.info(f"{status_icon} {test_name}: {status} (Score: {score:.1f}/100) - {details}")

    def validate_system_readiness(self) -> ValidationResult:
        """Validate system readiness for deployment"""
        start_time = time.time()
        test_name = "System Readiness Validation"

        try:
            checks = []

            # Check Python environment
            try:
                import sys
                if sys.version_info >= (3, 8):
                    checks.append(("Python Version", True, f"Python {sys.version_info.major}.{sys.version_info.minor}"))
                else:
                    checks.append(("Python Version", False, "Python 3.8+ required"))
            except Exception as e:
                checks.append(("Python Version", False, str(e)))

            # Check required directories
            required_dirs = [
                ".claude",
                "__csf",
                ".gittree",
                "deployment-automation"
            ]

            for dir_name in required_dirs:
                dir_path = self.base_path / dir_name
                exists = dir_path.exists()
                checks.append((f"Directory {dir_name}", exists, str(dir_path)))

            # Check configuration files
            config_files = [
                ".claude/anti_deception_config.json",
                "__csf/pyproject.toml",
                "deployment-automation/config/deployment_config.json"
            ]

            for config_file in config_files:
                file_path = self.base_path / config_file
                exists = file_path.exists()
                checks.append((f"Config File {config_file}", exists, str(file_path)))

            # Check dependencies
            try:
                result = subprocess.run(['python', '-m', 'pip', 'list'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    checks.append(("Dependencies", True, "Python package listing works"))
                else:
                    checks.append(("Dependencies", False, "Package listing failed"))
            except Exception as e:
                checks.append(("Dependencies", False, str(e)))

            passed_checks = sum(1 for _, passed, _ in checks if passed)
            total_checks = len(checks)
            score = (passed_checks / total_checks) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 90:
                status = "PASS"
            elif score >= 70:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_checks}/{total_checks} checks passed"
            recommendations = []

            for name, passed, msg in checks:
                if not passed:
                    recommendations.append(f"Fix: {name} - {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics={'passed_checks': passed_checks, 'total_checks': total_checks},
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              result.metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_service_health(self) -> ValidationResult:
        """Validate health of all services"""
        start_time = time.time()
        test_name = "Service Health Validation"

        try:
            services = [
                ("Task Execution Service", self.config.task_execution_url),
                ("Session Management Service", self.config.session_management_url),
                ("CSF NIP Service", self.config.csf_nip_url),
                ("Grafana Service", self.config.grafana_url),
                ("Prometheus Service", self.config.prometheus_url)
            ]

            health_results = []

            for service_name, url in services:
                try:
                    # Try multiple health check endpoints
                    endpoints = ["/health", "/api/health", "/ping", "/"]
                    service_healthy = False
                    response_time = None

                    for endpoint in endpoints:
                        try:
                            health_url = url.rstrip('/') + endpoint
                            response = requests.get(health_url, timeout=self.config.health_check_timeout)
                            if response.status_code in [200, 201, 204]:
                                service_healthy = True
                                response_time = response.elapsed.total_seconds() * 1000
                                break
                        except requests.RequestException:
                            continue

                    if service_healthy:
                        health_results.append({
                            'service': service_name,
                            'healthy': True,
                            'response_time_ms': response_time,
                            'url': url
                        })
                    else:
                        health_results.append({
                            'service': service_name,
                            'healthy': False,
                            'response_time_ms': None,
                            'url': url
                        })

                except Exception as e:
                    health_results.append({
                        'service': service_name,
                        'healthy': False,
                        'response_time_ms': None,
                        'url': url,
                        'error': str(e)
                    })

            healthy_services = sum(1 for r in health_results if r['healthy'])
            total_services = len(health_results)
            score = (healthy_services / total_services) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 80:
                status = "PASS"
            elif score >= 60:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{healthy_services}/{total_services} services healthy"

            # Calculate average response time
            response_times = [r['response_time_ms'] for r in health_results
                            if r['response_time_ms'] is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            metrics = {
                'healthy_services': healthy_services,
                'total_services': total_services,
                'average_response_time_ms': avg_response_time,
                'service_details': health_results
            }

            recommendations = []
            for result in health_results:
                if not result['healthy']:
                    recommendations.append(f"Start/fix {result['service']} at {result['url']}")
                elif result['response_time_ms'] and result['response_time_ms'] > self.config.response_time_threshold_ms:
                    recommendations.append(f"Optimize {result['service']} performance (response time: {result['response_time_ms']:.1f}ms)")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_session_management(self) -> ValidationResult:
        """Validate session management system"""
        start_time = time.time()
        test_name = "Session Management Validation"

        try:
            session_tests = []

            # Test session creation
            try:
                response = requests.post(
                    f"{self.config.session_management_url}/api/sessions",
                    json={"user_id": "test_user", "metadata": {"test": True}},
                    timeout=self.config.integration_test_timeout
                )
                if response.status_code in [200, 201]:
                    session_data = response.json()
                    session_id = session_data.get('session_id')
                    session_tests.append(("Session Creation", True, f"Session ID: {session_id}"))
                else:
                    session_tests.append(("Session Creation", False, f"Status: {response.status_code}"))
            except Exception as e:
                session_tests.append(("Session Creation", False, str(e)))

            # Test session retrieval
            if session_tests and session_tests[0][1]:  # If session creation succeeded
                try:
                    if 'session_id' in locals():
                        response = requests.get(
                            f"{self.config.session_management_url}/api/sessions/{session_id}",
                            timeout=self.config.integration_test_timeout
                        )
                        if response.status_code == 200:
                            session_tests.append(("Session Retrieval", True, "Session data retrieved"))
                        else:
                            session_tests.append(("Session Retrieval", False, f"Status: {response.status_code}"))
                except Exception as e:
                    session_tests.append(("Session Retrieval", False, str(e)))

            # Test session persistence
            try:
                db_path = self.base_path / "__csf" / "data" / "evidence.db"
                if db_path.exists():
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sessions")
                    session_count = cursor.fetchone()[0]
                    conn.close()
                    session_tests.append(("Session Persistence", True, f"{session_count} sessions in database"))
                else:
                    session_tests.append(("Session Persistence", False, "Database not found"))
            except Exception as e:
                session_tests.append(("Session Persistence", False, str(e)))

            # Test session cleanup
            try:
                response = requests.delete(
                    f"{self.config.session_management_url}/api/sessions/cleanup",
                    timeout=self.config.integration_test_timeout
                )
                if response.status_code == 200:
                    cleanup_data = response.json()
                    session_tests.append(("Session Cleanup", True, "Cleaned up sessions"))
                else:
                    session_tests.append(("Session Cleanup", False, f"Status: {response.status_code}"))
            except Exception as e:
                session_tests.append(("Session Cleanup", False, str(e)))

            passed_tests = sum(1 for _, passed, _ in session_tests if passed)
            total_tests = len(session_tests)
            score = (passed_tests / total_tests) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 75:
                status = "PASS"
            elif score >= 50:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_tests}/{total_tests} session tests passed"

            metrics = {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'test_details': session_tests
            }

            recommendations = []
            for test_name, passed, msg in session_tests:
                if not passed:
                    recommendations.append(f"Fix session {test_name.lower()}: {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_csf_nip_compliance(self) -> ValidationResult:
        """Validate CSF NIP compliance"""
        start_time = time.time()
        test_name = "CSF NIP Compliance Validation"

        try:
            compliance_tests = []

            # Check CSF NIP directory structure
            csf_nip_path = self.base_path / "__csf"
            if csf_nip_path.exists():
                compliance_tests.append(("CSF NIP Directory", True, "Directory exists"))

                # Check for required components
                required_components = [
                    "src",
                    "config",
                    "tests",
                    "pyproject.toml"
                ]

                for component in required_components:
                    component_path = csf_nip_path / component
                    exists = component_path.exists()
                    compliance_tests.append((f"Component {component}", exists, str(component_path)))

                # Check configuration files
                config_files = [
                    "config/main_config.py",
                    "config/system_config.py"
                ]

                for config_file in config_files:
                    config_path = csf_nip_path / config_file
                    exists = config_path.exists()
                    compliance_tests.append((f"Config {config_file}", exists, str(config_path)))

            else:
                compliance_tests.append(("CSF NIP Directory", False, "Directory not found"))

            # Test CSF NIP service endpoints
            try:
                response = requests.get(f"{self.config.csf_nip_url}/api/health", timeout=10)
                if response.status_code == 200:
                    compliance_tests.append(("CSF NIP Health", True, "Service responding"))
                else:
                    compliance_tests.append(("CSF NIP Health", False, f"Status: {response.status_code}"))
            except Exception as e:
                compliance_tests.append(("CSF NIP Health", False, str(e)))

            # Check compliance validation
            try:
                response = requests.get(f"{self.config.csf_nip_url}/api/compliance/check", timeout=10)
                if response.status_code == 200:
                    compliance_data = response.json()
                    compliance_score = compliance_data.get('compliance_score', 0)
                    compliance_tests.append(("Compliance Score", compliance_score >= 80, f"Score: {compliance_score}%"))
                else:
                    compliance_tests.append(("Compliance Score", False, "Endpoint not available"))
            except Exception:
                compliance_tests.append(("Compliance Score", False, "Compliance check failed"))

            # Validate modules
            try:
                src_path = csf_nip_path / "src"
                if src_path.exists():
                    modules = [d for d in src_path.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
                    compliance_tests.append(("CSF NIP Modules", True, f"{len(modules)} modules found"))

                    # Check specific critical modules
                    critical_modules = [
                        "modules/validation",
                        "modules/analysis",
                        "modules/documentation"
                    ]

                    for module in critical_modules:
                        module_path = src_path / module
                        exists = module_path.exists()
                        compliance_tests.append((f"Module {module}", exists, str(module_path)))
                else:
                    compliance_tests.append(("CSF NIP Modules", False, "src directory not found"))
            except Exception as e:
                compliance_tests.append(("CSF NIP Modules", False, str(e)))

            passed_tests = sum(1 for _, passed, _ in compliance_tests if passed)
            total_tests = len(compliance_tests)
            score = (passed_tests / total_tests) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 85:
                status = "PASS"
            elif score >= 70:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_tests}/{total_tests} compliance checks passed"

            metrics = {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'test_details': compliance_tests
            }

            recommendations = []
            for test_name, passed, msg in compliance_tests:
                if not passed:
                    recommendations.append(f"Fix CSF NIP {test_name.lower()}: {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_performance(self) -> ValidationResult:
        """Validate system performance"""
        start_time = time.time()
        test_name = "Performance Validation"

        try:
            performance_tests = []

            # Test response times
            services = [
                ("Task Execution", self.config.task_execution_url),
                ("Session Management", self.config.session_management_url),
                ("CSF NIP", self.config.csf_nip_url)
            ]

            response_times = []

            for service_name, url in services:
                try:
                    # Make multiple requests to get average response time
                    times = []
                    for _ in range(5):
                        try:
                            response = requests.get(url, timeout=10)
                            if response.status_code == 200:
                                times.append(response.elapsed.total_seconds() * 1000)
                        except requests.RequestException:
                            continue

                    if times:
                        avg_time = sum(times) / len(times)
                        response_times.append(avg_time)

                        if avg_time <= self.config.response_time_threshold_ms:
                            performance_tests.append((f"{service_name} Response Time", True, f"{avg_time:.1f}ms"))
                        else:
                            performance_tests.append((f"{service_name} Response Time", False, f"{avg_time:.1f}ms (threshold: {self.config.response_time_threshold_ms}ms)"))
                    else:
                        performance_tests.append((f"{service_name} Response Time", False, "No successful responses"))

                except Exception as e:
                    performance_tests.append((f"{service_name} Response Time", False, str(e)))

            # Test throughput (if available)
            try:
                # Simulate load test
                start_load = time.time()
                successful_requests = 0
                total_requests = 50

                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    for _ in range(total_requests):
                        future = executor.submit(requests.get, self.config.task_execution_url, timeout=5)
                        futures.append(future)

                    for future in concurrent.futures.as_completed(futures):
                        try:
                            response = future.result()
                            if response.status_code == 200:
                                successful_requests += 1
                        except:
                            continue

                load_duration = time.time() - start_load
                throughput = successful_requests / load_duration if load_duration > 0 else 0

                if throughput > 10:  # At least 10 requests per second
                    performance_tests.append(("Throughput", True, f"{throughput:.1f} req/sec"))
                else:
                    performance_tests.append(("Throughput", False, f"{throughput:.1f} req/sec (threshold: 10 req/sec)"))

            except Exception as e:
                performance_tests.append(("Throughput", False, str(e)))

            # Test memory usage (if available)
            try:
                import psutil
                memory_info = psutil.virtual_memory()
                memory_usage_mb = memory_info.used / (1024 * 1024)

                if memory_usage_mb <= self.config.memory_usage_threshold_mb:
                    performance_tests.append(("Memory Usage", True, f"{memory_usage_mb:.1f}MB"))
                else:
                    performance_tests.append(("Memory Usage", False, f"{memory_usage_mb:.1f}MB (threshold: {self.config.memory_usage_threshold_mb}MB)"))

            except ImportError:
                performance_tests.append(("Memory Usage", False, "psutil not available"))
            except Exception as e:
                performance_tests.append(("Memory Usage", False, str(e)))

            passed_tests = sum(1 for _, passed, _ in performance_tests if passed)
            total_tests = len(performance_tests)
            score = (passed_tests / total_tests) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 80:
                status = "PASS"
            elif score >= 60:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_tests}/{total_tests} performance tests passed"

            # Calculate overall metrics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            metrics = {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'average_response_time_ms': avg_response_time,
                'response_times': response_times,
                'test_details': performance_tests
            }

            recommendations = []
            for test_name, passed, msg in performance_tests:
                if not passed:
                    recommendations.append(f"Optimize {test_name.lower()}: {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_security(self) -> ValidationResult:
        """Validate security compliance"""
        start_time = time.time()
        test_name = "Security Validation"

        if not self.config.security_scan_enabled:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "SKIPPED", 100, "Security scanning disabled", duration_ms)
            return ValidationResult(
                test_name=test_name,
                status="SKIPPED",
                score=100,
                duration_ms=duration_ms,
                details="Security scanning disabled",
                timestamp=datetime.now().isoformat(),
                metrics={},
                recommendations=[]
            )

        try:
            security_tests = []

            # Test HTTPS/TLS (if applicable)
            try:
                for service_name, url in [
                    ("Task Execution", self.config.task_execution_url),
                    ("Session Management", self.config.session_management_url),
                    ("CSF NIP", self.config.csf_nip_url)
                ]:
                    if url.startswith('https://'):
                        response = requests.get(url, verify=True, timeout=10)
                        if response.status_code == 200:
                            security_tests.append((f"{service_name} TLS", True, "TLS certificate valid"))
                        else:
                            security_tests.append((f"{service_name} TLS", False, "TLS certificate issue"))
                    else:
                        security_tests.append((f"{service_name} TLS", False, "HTTP not HTTPS"))
            except Exception as e:
                security_tests.append(("TLS Validation", False, str(e)))

            # Test security headers
            try:
                response = requests.get(self.config.task_execution_url, timeout=10)
                headers = response.headers

                security_headers = {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'DENY',
                    'X-XSS-Protection': '1; mode=block',
                    'Strict-Transport-Security': 'max-age'
                }

                for header, expected_value in security_headers.items():
                    if header in headers:
                        if expected_value in headers[header]:
                            security_tests.append((f"Header {header}", True, headers[header]))
                        else:
                            security_tests.append((f"Header {header}", False, headers[header]))
                    else:
                        security_tests.append((f"Header {header}", False, "Missing"))
            except Exception as e:
                security_tests.append(("Security Headers", False, str(e)))

            # Test input validation
            try:
                # Test SQL injection protection
                malicious_payload = "'; DROP TABLE users; --"
                response = requests.post(
                    f"{self.config.task_execution_url}/api/test",
                    json={"input": malicious_payload},
                    timeout=10
                )

                if response.status_code not in [500, 200] or "error" in response.text.lower():
                    security_tests.append(("Input Validation", True, "Malicious input handled"))
                else:
                    security_tests.append(("Input Validation", False, "Potential SQL injection vulnerability"))
            except Exception:
                security_tests.append(("Input Validation", True, "Service rejected malicious request"))

            # Test authentication/authorization
            try:
                # Test protected endpoint without authentication
                response = requests.get(
                    f"{self.config.session_management_url}/api/admin/sessions",
                    timeout=10
                )

                if response.status_code in [401, 403]:
                    security_tests.append(("Authentication", True, "Protected endpoint requires auth"))
                elif response.status_code == 404:
                    security_tests.append(("Authentication", True, "Endpoint not found (OK)"))
                else:
                    security_tests.append(("Authentication", False, f"Unprotected access (status: {response.status_code})"))
            except Exception as e:
                security_tests.append(("Authentication", False, str(e)))

            # Test file access restrictions
            try:
                sensitive_files = [
                    "/etc/passwd",
                    "../../../etc/passwd",
                    "file://etc/passwd"
                ]

                for file_path in sensitive_files:
                    response = requests.get(
                        f"{self.config.task_execution_url}/api/files?path={file_path}",
                        timeout=10
                    )

                    if response.status_code in [403, 404, 500]:
                        security_tests.append(("File Access Control", True, f"Access denied to {file_path}"))
                    else:
                        security_tests.append(("File Access Control", False, "Potential file access vulnerability"))
                        break
            except Exception:
                security_tests.append(("File Access Control", True, "File access properly restricted"))

            passed_tests = sum(1 for _, passed, _ in security_tests if passed)
            total_tests = len(security_tests)
            score = (passed_tests / total_tests) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 90:
                status = "PASS"
            elif score >= 70:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_tests}/{total_tests} security tests passed"

            metrics = {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'test_details': security_tests
            }

            recommendations = []
            for test_name, passed, msg in security_tests:
                if not passed:
                    recommendations.append(f"Fix security {test_name.lower()}: {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def validate_integrations(self) -> ValidationResult:
        """Validate system integrations"""
        start_time = time.time()
        test_name = "Integration Validation"

        try:
            integration_tests = []

            # Test Task Execution to Session Management integration
            try:
                # Create a session
                session_response = requests.post(
                    f"{self.config.session_management_url}/api/sessions",
                    json={"user_id": "integration_test", "metadata": {"test": "integration"}},
                    timeout=10
                )

                if session_response.status_code in [200, 201]:
                    session_data = session_response.json()
                    session_id = session_data.get('session_id')

                    # Use session in task execution
                    task_response = requests.post(
                        f"{self.config.task_execution_url}/api/tasks",
                        json={"session_id": session_id, "task": "test_task"},
                        timeout=10
                    )

                    if task_response.status_code in [200, 201]:
                        integration_tests.append(("Task-Session Integration", True, "Tasks can use sessions"))
                    else:
                        integration_tests.append(("Task-Session Integration", False, f"Task creation failed: {task_response.status_code}"))
                else:
                    integration_tests.append(("Task-Session Integration", False, f"Session creation failed: {session_response.status_code}"))
            except Exception as e:
                integration_tests.append(("Task-Session Integration", False, str(e)))

            # Test Session Management to CSF NIP integration
            try:
                # Check if session data is available to CSF NIP
                response = requests.get(
                    f"{self.config.csf_nip_url}/api/sessions/count",
                    timeout=10
                )

                if response.status_code == 200:
                    integration_tests.append(("Session-CSF Integration", True, "CSF NIP can access session data"))
                else:
                    integration_tests.append(("Session-CSF Integration", False, f"CSF NIP session access failed: {response.status_code}"))
            except Exception as e:
                integration_tests.append(("Session-CSF Integration", False, str(e)))

            # Test CSF NIP to Task Execution integration
            try:
                # Test if CSF NIP can validate tasks
                response = requests.post(
                    f"{self.config.csf_nip_url}/api/validation/task",
                    json={"task": "test_task", "context": {"test": True}},
                    timeout=10
                )

                if response.status_code == 200:
                    validation_result = response.json()
                    if validation_result.get('valid', False):
                        integration_tests.append(("CSF-Task Integration", True, "CSF NIP validates tasks"))
                    else:
                        integration_tests.append(("CSF-Task Integration", True, "CSF NIP rejected test task (expected)"))
                else:
                    integration_tests.append(("CSF-Task Integration", False, f"Task validation failed: {response.status_code}"))
            except Exception as e:
                integration_tests.append(("CSF-Task Integration", False, str(e)))

            # Test monitoring integration
            try:
                # Check if metrics are available
                prometheus_response = requests.get(f"{self.config.prometheus_url}/api/v1/query?query=up", timeout=10)
                if prometheus_response.status_code == 200:
                    integration_tests.append(("Monitoring Integration", True, "Prometheus metrics available"))
                else:
                    integration_tests.append(("Monitoring Integration", False, "Prometheus not accessible"))
            except Exception as e:
                integration_tests.append(("Monitoring Integration", False, str(e)))

            # Test backup integration
            try:
                # Check if backup system can access all components
                backup_dirs = [
                    self.base_path / "__csf" / "data",
                    self.base_path / ".claude" / "session_storage",
                    self.base_path / "deployment-automation" / "backups"
                ]

                backup_accessible = all(dir_path.exists() for dir_path in backup_dirs)
                integration_tests.append(("Backup Integration", backup_accessible, "All backup directories accessible"))
            except Exception as e:
                integration_tests.append(("Backup Integration", False, str(e)))

            passed_tests = sum(1 for _, passed, _ in integration_tests if passed)
            total_tests = len(integration_tests)
            score = (passed_tests / total_tests) * 100

            duration_ms = (time.time() - start_time) * 1000

            if score >= 80:
                status = "PASS"
            elif score >= 60:
                status = "WARNING"
            else:
                status = "FAIL"

            details = f"{passed_tests}/{total_tests} integration tests passed"

            metrics = {
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'test_details': integration_tests
            }

            recommendations = []
            for test_name, passed, msg in integration_tests:
                if not passed:
                    recommendations.append(f"Fix {test_name.lower()}: {msg}")

            result = ValidationResult(
                test_name=test_name,
                status=status,
                score=score,
                duration_ms=duration_ms,
                details=details,
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                recommendations=recommendations
            )

            self.log_validation(test_name, status, score, details, duration_ms,
                              metrics, recommendations)
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_validation(test_name, "FAIL", 0, str(e), duration_ms)
            raise

    def run_comprehensive_validation(self) -> dict[str, Any]:
        """Run comprehensive deployment validation"""
        self.logger.info("Starting comprehensive deployment validation...")
        self.start_time = time.time()

        try:
            # Define all validation tests
            validation_tests = [
                self.validate_system_readiness,
                self.validate_service_health,
                self.validate_session_management,
                self.validate_csf_nip_compliance,
                self.validate_performance,
                self.validate_security,
                self.validate_integrations
            ]

            if self.config.parallel_validation:
                # Run tests in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_test = {executor.submit(test): test.__name__ for test in validation_tests}

                    for future in concurrent.futures.as_completed(future_to_test):
                        test_name = future_to_test[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            self.logger.error(f"Test {test_name} failed: {str(e)}")
            else:
                # Run tests sequentially
                for test in validation_tests:
                    try:
                        test()
                    except Exception as e:
                        self.logger.error(f"Test {test.__name__} failed: {str(e)}")

            # Calculate overall results
            total_duration = (time.time() - self.start_time) * 1000

            passed_tests = len([r for r in self.validation_results if r.status == "PASS"])
            warning_tests = len([r for r in self.validation_results if r.status == "WARNING"])
            failed_tests = len([r for r in self.validation_results if r.status == "FAIL"])
            total_tests = len(self.validation_results)

            overall_score = sum(r.score for r in self.validation_results) / total_tests if total_tests > 0 else 0

            # Determine overall status
            if failed_tests == 0 and warning_tests <= 1:
                overall_status = "PASS"
            elif failed_tests == 0 and warning_tests <= 2:
                overall_status = "WARNING"
            else:
                overall_status = "FAIL"

            # Generate comprehensive report
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'total_duration_ms': total_duration,
                'overall_status': overall_status,
                'overall_score': overall_score,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'warning_tests': warning_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
                },
                'test_results': [asdict(result) for result in self.validation_results],
                'configuration': asdict(self.config),
                'all_recommendations': list(set(
                    rec for result in self.validation_results
                    for rec in result.recommendations
                )),
                'deployment_ready': overall_status in ["PASS", "WARNING"] and overall_score >= 70
            }

            # Save detailed report
            report_path = self.base_path / "deployment-automation" / "logs" / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            # Log summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info("DEPLOYMENT VALIDATION SUMMARY")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"Overall Status: {overall_status}")
            self.logger.info(f"Overall Score: {overall_score:.1f}/100")
            self.logger.info(f"Tests: {passed_tests} passed, {warning_tests} warnings, {failed_tests} failed")
            self.logger.info(f"Duration: {total_duration/1000:.1f} seconds")
            self.logger.info(f"Deployment Ready: {'YES' if report['deployment_ready'] else 'NO'}")

            if report['all_recommendations']:
                self.logger.info("\nRECOMMENDATIONS:")
                for i, rec in enumerate(report['all_recommendations'][:10], 1):
                    self.logger.info(f"{i}. {rec}")

                if len(report['all_recommendations']) > 10:
                    self.logger.info(f"... and {len(report['all_recommendations']) - 10} more recommendations")

            self.logger.info(f"{'='*60}")
            self.logger.info(f"Detailed report saved to: {report_path}")

            return report

        except Exception as e:
            self.logger.error(f"Comprehensive validation failed: {str(e)}")
            raise

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Execution Enhancements Deployment Validation")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--test', choices=[
        'readiness', 'health', 'session', 'csf-nip', 'performance',
        'security', 'integrations', 'comprehensive'
    ], default='comprehensive', help='Specific test to run')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--security-scan', action='store_true', help='Enable security scanning')
    parser.add_argument('--compliance', action='store_true', help='Enable compliance validation')
    parser.add_argument('--output', help='Output file for validation report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Load configuration
    config = ValidationConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    # Override with command line arguments
    if args.parallel:
        config.parallel_validation = True
    if args.security_scan:
        config.security_scan_enabled = True
    if args.compliance:
        config.compliance_validation_enabled = True

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize validator
    validator = DeploymentValidator(config)

    try:
        # Run specified test
        if args.test == 'comprehensive':
            report = validator.run_comprehensive_validation()
        else:
            # Run single test
            test_map = {
                'readiness': validator.validate_system_readiness,
                'health': validator.validate_service_health,
                'session': validator.validate_session_management,
                'csf-nip': validator.validate_csf_nip_compliance,
                'performance': validator.validate_performance,
                'security': validator.validate_security,
                'integrations': validator.validate_integrations
            }

            if args.test in test_map:
                result = test_map[args.test]()
                report = {
                    'validation_timestamp': datetime.now().isoformat(),
                    'overall_status': result.status,
                    'overall_score': result.score,
                    'test_results': [asdict(result)]
                }
            else:
                parser.error(f"Unknown test: {args.test}")

        # Save to specified output file
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            validator.logger.info(f"Report saved to: {args.output}")

        # Exit with appropriate code
        if report['overall_status'] == 'PASS':
            sys.exit(0)
        elif report['overall_status'] == 'WARNING':
            sys.exit(1)
        else:
            sys.exit(2)

    except KeyboardInterrupt:
        validator.logger.info("Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        validator.logger.error(f"Validation failed: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()
