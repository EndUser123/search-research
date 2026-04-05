"""
Test utilities for Enhanced Anti-Deception Architecture testing suite.
"""

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
try:
    from anti_deception_hook import AntiDeceptionHook
except ImportError:
    # Fallback for testing
    AntiDeceptionHook = None


class MockLLMResponse:
    """Mock LLM response for testing."""

    def __init__(self, response_text: str, cost: float = 0.0, is_safe: bool = True):
        self.response_text = response_text
        self.cost = cost
        self.is_safe = is_safe
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_text": self.response_text,
            "cost": self.cost,
            "is_safe": self.safe,
            "timestamp": self.timestamp,
        }


class TestConfigHelper:
    """Helper class for creating test configurations."""

    @staticmethod
    def create_minimal_config() -> dict[str, Any]:
        """Create a minimal configuration for testing."""
        return {
            "evidence_requirements": {
                "file_operations": True,
                "code_changes": True,
                "task_completion": True,
            },
            "completion_checklist": {
                "evidence_provided": False,
                "tests_written": False,
                "tests_pass": False,
                "code_reviewed": False,
            },
            "file_blocking": {
                "enabled": True,
                "dangerous_patterns": [r"rm\s+-rf\s+/"],
                "allowed_paths": ["P:\\__csf\\"],
            },
            "validation_rules": {
                "require_evidence_for_completion": True,
                "block_premature_completion": True,
                "validate_file_operations": True,
                "enforce_checklist": True,
            },
        }

    @staticmethod
    def create_strict_config() -> dict[str, Any]:
        """Create a strict configuration for testing."""
        return {
            "evidence_requirements": {
                "file_operations": True,
                "code_changes": True,
                "task_completion": True,
                "performance_claims": True,
                "bug_fixes": True,
                "test_results": True,
                "security_improvements": True,
                "architecture_changes": True,
            },
            "completion_checklist": {
                "evidence_provided": True,
                "tests_written": True,
                "tests_pass": True,
                "code_reviewed": True,
                "documentation_updated": True,
                "files_created": True,
                "safety_validated": True,
                "performance_validated": True,
                "security_checked": True,
            },
            "file_blocking": {
                "enabled": True,
                "dangerous_patterns": [
                    r"rm\s+-rf\s+/",
                    r"sudo\s+rm",
                    r"\.bashrc$",
                    r"\.profile$",
                    r"\.zshrc$",
                    r"\.ssh/",
                    r"/etc/",
                    r"systemctl\s+stop",
                    r"shutdown\s+",
                    r"reboot\s+",
                    r"format\s+",
                    r"mkfs\.",
                ],
                "allowed_paths": ["P:\\__csf\\"],
            },
            "validation_rules": {
                "require_evidence_for_completion": True,
                "block_premature_completion": True,
                "validate_file_operations": True,
                "enforce_checklist": True,
                "require_test_evidence": True,
                "require_performance_evidence": True,
                "require_security_evidence": True,
            },
        }

    @staticmethod
    def create_loose_config() -> dict[str, Any]:
        """Create a loose configuration for testing."""
        return {
            "evidence_requirements": {
                "file_operations": False,
                "code_changes": False,
                "task_completion": False,
                "performance_claims": False,
                "bug_fixes": False,
                "test_results": False,
                "security_improvements": False,
                "architecture_changes": False,
            },
            "completion_checklist": {
                "evidence_provided": False,
                "tests_written": False,
                "tests_pass": False,
                "code_reviewed": False,
                "documentation_updated": False,
                "files_created": False,
                "safety_validated": False,
                "performance_validated": False,
                "security_checked": False,
            },
            "file_blocking": {
                "enabled": False,
                "dangerous_patterns": [],
                "allowed_paths": ["/"],
            },
            "validation_rules": {
                "require_evidence_for_completion": False,
                "block_premature_completion": False,
                "validate_file_operations": False,
                "enforce_checklist": False,
                "require_test_evidence": False,
                "require_performance_evidence": False,
                "require_security_evidence": False,
            },
        }


class PerformanceTimer:
    """Utility class for performance timing."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed * 1000


class EvidenceGenerator:
    """Utility class for generating test evidence."""

    @staticmethod
    def create_file_evidence(file_paths: list[str]) -> list[str]:
        """Create file-based evidence strings."""
        evidence = []
        for file_path in file_paths:
            evidence.append(f"File created: {file_path}")
            evidence.append(f"Path exists: {file_path}")
            evidence.append(f"File size: {os.path.getsize(file_path)} bytes")
        return evidence

    @staticmethod
    def create_test_evidence(test_results: str) -> list[str]:
        """Create test-based evidence strings."""
        return [
            f"Test results: {test_results}",
            "pytest execution completed",
            "All tests PASSED",
            "0 failures, 0 errors",
        ]

    @staticmethod
    def create_code_evidence(code_changes: list[str]) -> list[str]:
        """Create code-based evidence strings."""
        evidence = []
        for change in code_changes:
            evidence.append(f"Code modified: {change}")
            evidence.append("def function_name():")
            evidence.append("import library")
            evidence.append("TODO: implement feature")
        return evidence

    @staticmethod
    def create_performance_evidence(optimizations: list[str]) -> list[str]:
        """Create performance-based evidence strings."""
        evidence = []
        for opt in optimizations:
            evidence.append(f"Optimization: {opt}")
            evidence.append("Benchmark time: 1.2s")
            evidence.append("Performance improvement: 15%")
        return evidence


class TemporaryDirectory:
    """Context manager for temporary directories."""

    def __init__(self, prefix: str = "test_"):
        self.prefix = prefix
        self.temp_dir = None

    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix=self.prefix)
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


class MockEvidenceLog:
    """Mock evidence log for testing."""

    def __init__(self):
        self.log = []

    def add_evidence(
        self, evidence_type: str, details: str, file_paths: list[str] = None
    ):
        """Add evidence to the log."""
        entry = {
            "type": evidence_type,
            "details": details,
            "file_paths": file_paths or [],
            "timestamp": time.time(),
        }
        self.log.append(entry)

    def get_evidence_by_type(self, evidence_type: str) -> list[dict[str, Any]]:
        """Get evidence by type."""
        return [entry for entry in self.log if entry["type"] == evidence_type]

    def clear(self):
        """Clear the evidence log."""
        self.log.clear()

    @property
    def count(self) -> int:
        """Get total evidence count."""
        return len(self.log)


class MockFailureTracker:
    """Mock failure tracker for testing."""

    def __init__(self):
        self.failures = []

    def add_failure(self, failure_type: str, message: str):
        """Add a failure."""
        failure = {"type": failure_type, "message": message, "timestamp": time.time()}
        self.failures.append(failure)

    def clear(self):
        """Clear failures."""
        self.failures.clear()

    @property
    def count(self) -> int:
        """Get failure count."""
        return len(self.failures)

    @property
    def recent_failures(self) -> list[dict[str, Any]]:
        """Get recent failures."""
        return self.failures[-5:]  # Last 5 failures


# Mock LLM class for testing
class MockLLM:
    """Mock LLM for testing supervisor integration."""

    def __init__(
        self, safe_responses: list[str] = None, unsafe_responses: list[str] = None
    ):
        self.safe_responses = safe_responses or [
            "The operation appears to be safe and valid.",
            "No security concerns detected.",
            "Operation validated successfully.",
        ]
        self.unsafe_responses = unsafe_responses or [
            "Security risk detected: Potential malicious operation.",
            "Operation blocked due to safety concerns.",
            "Warning: This operation could be dangerous.",
        ]
        self.cost = 0.0
        self.call_count = 0

    def validate_operation(self, operation: str, context: str = "") -> MockLLMResponse:
        """Mock operation validation."""
        self.call_count += 1

        # Simulate some logic for determining safety
        is_safe = "delete" not in operation.lower() or "temp" in operation.lower()
        response = random.choice(
            self.safe_responses if is_safe else self.unsafe_responses
        )
        cost = random.uniform(0.001, 0.01)  # Simulate cost

        return MockLLMResponse(response, cost, is_safe)

    def get_cost_summary(self) -> float:
        """Get total cost."""
        return self.cost + (self.call_count * 0.005)  # Base cost per call


# Mock communication system
class MockCommunicationSystem:
    """Mock communication system for testing."""

    def __init__(self):
        self.messages = []
        self.connected = True

    def send_message(
        self, hook_id: str, message: str, priority: str = "normal"
    ) -> bool:
        """Send a message to another hook."""
        msg = {
            "from": "test_hook",
            "to": hook_id,
            "message": message,
            "priority": priority,
            "timestamp": time.time(),
        }
        self.messages.append(msg)
        return True

    def receive_message(self) -> dict[str, Any]:
        """Receive a message."""
        return self.messages.pop(0) if self.messages else None

    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)

    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()


# Performance benchmark utility
class PerformanceBenchmark:
    """Utility for performance benchmarking."""

    def __init__(self, target_ms: float = 2000.0):
        self.target_ms = target_ms  # 2 seconds target
        self.results = []

    def run_benchmark(self, func, *args, **kwargs):
        """Run a benchmark on a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        passed = elapsed_ms <= self.target_ms

        benchmark_result = {
            "function": func.__name__,
            "elapsed_ms": elapsed_ms,
            "target_ms": self.target_ms,
            "passed": passed,
            "timestamp": time.time(),
        }

        self.results.append(benchmark_result)
        return result, benchmark_result

    def get_summary(self) -> dict[str, Any]:
        """Get benchmark summary."""
        if not self.results:
            return {}

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        avg_time = sum(r["elapsed_ms"] for r in self.results) / total_tests
        max_time = max(r["elapsed_ms"] for r in self.results)

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": (passed_tests / total_tests) * 100,
            "average_time_ms": avg_time,
            "max_time_ms": max_time,
            "target_ms": self.target_ms,
            "all_results": self.results,
        }


# Import required modules
import random
