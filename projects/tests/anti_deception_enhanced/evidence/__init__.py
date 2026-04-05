"""
Evidence System Testing Package

This package provides comprehensive testing infrastructure for the central evidence repository
and evidence analysis capabilities. It validates evidence collection, storage, analysis, and
cross-hook communication functionality.

Package Structure:
- test_central_repository.py: Central repository functionality and evidence persistence
- test_evidence_analysis.py: Pattern detection, correlation, risk assessment, and anomaly detection
- evidence_utils.py: Utility classes and helpers for evidence testing
"""

import asyncio
import json
import shutil
import sqlite3
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from anti_deception_enhanced.hooks import AntiDeceptionHook
from anti_deception_enhanced.hooks.communication_system import CommunicationSystem
from anti_deception_enhanced.hooks.llm_supervisor import LLMSupervisor
from anti_deception_enhanced.hooks.post_tool_use import PostToolUse
from anti_deception_enhanced.hooks.pre_tool_use import PreToolUse
from anti_deception_enhanced.utils.evidence import (
    AnomalyDetector,
    EvidenceAnalyzer,
    EvidenceCorrelator,
    EvidenceEntry,
    EvidenceLevel,
    EvidenceManager,
    EvidenceRepository,
    PatternDetector,
    RiskAssessor,
)
from anti_deception_enhanced.utils.mock_llm import MockLLMSupervisor, TestLLMScenario


@dataclass
class TestEvidenceScenario:
    """Test scenario configuration for evidence collection"""

    name: str
    operation: str
    content: str
    level: EvidenceLevel
    metadata: dict[str, Any]
    expected_validation: bool
    risk_score: float = 0.0

    def to_entry(self) -> EvidenceEntry:
        """Convert to evidence entry"""
        return EvidenceEntry(
            operation=self.operation,
            content=self.content,
            level=self.level,
            metadata=self.metadata,
        )


@dataclass
class EvidenceTestResult:
    """Test result for evidence validation"""

    scenario_name: str
    validation_result: bool
    evidence_entry: EvidenceEntry
    processing_time: float
    error_message: str | None = None


@dataclass
class PatternTestScenario:
    """Test scenario for pattern detection"""

    name: str
    evidence_sequence: list[EvidenceEntry]
    expected_pattern: str
    expected_confidence: float
    pattern_type: str = "temporal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "evidence_sequence": [e.to_dict() for e in self.evidence_sequence],
            "expected_pattern": self.expected_pattern,
            "expected_confidence": self.expected_confidence,
            "pattern_type": self.pattern_type,
        }


@dataclass
class RiskTestScenario:
    """Test scenario for risk assessment"""

    name: str
    evidence_entry: EvidenceEntry
    expected_risk_score: float
    expected_risk_level: EvidenceLevel
    risk_factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "evidence_entry": self.evidence_entry.to_dict(),
            "expected_risk_score": self.expected_risk_score,
            "expected_risk_level": self.expected_risk_level.name,
            "risk_factors": self.risk_factors,
        }


class ExtendedEvidenceAnalyzer(EvidenceAnalyzer):
    """Extended evidence analyzer for testing"""

    def __init__(self):
        super().__init__()
        self.ml_model = None
        self.feature_scaler = StandardScaler()

    def train_ml_model(self, training_data: list[dict[str, Any]]) -> Any:
        """Train ML model on evidence data"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler

            # Prepare training data
            X_train = [data["features"] for data in training_data]
            y_train = [data["label"] for data in training_data]

            # Train model
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X_train, y_train)

            self.ml_model = model
            return model
        except Exception:
            # Fallback to simple model
            self.ml_model = Mock()
            self.ml_model.predict = lambda x: ["normal"] * len(x)
            return self.ml_model

    def predict_evidence_risk(self, evidence_entry: EvidenceEntry) -> dict[str, Any]:
        """Predict risk using ML model"""
        if self.ml_model is None:
            # Simple rule-based prediction as fallback
            return {
                "prediction": "normal"
                if evidence_entry.level.value <= 1
                else "anomaly",
                "confidence": 0.7,
                "model_version": "fallback",
            }

        # Extract features from evidence
        features = self.extract_features(evidence_entry)
        features_scaled = self.feature_scaler.transform([features])

        # Make prediction
        prediction = self.ml_model.predict(features_scaled)[0]
        probabilities = self.ml_model.predict_proba(features_scaled)[0]

        return {
            "prediction": prediction,
            "confidence": max(probabilities),
            "probabilities": probabilities.tolist(),
            "model_version": "ml_v1",
        }

    def extract_features(self, evidence_entry: EvidenceEntry) -> list[float]:
        """Extract features from evidence entry"""
        # Simple feature extraction for testing
        features = [
            evidence_entry.level.value / 10.0,  # Normalized level
            len(evidence_entry.content) / 100.0,  # Content length
            len(evidence_entry.operation) / 20.0,  # Operation length
            len(evidence_entry.metadata) / 10.0,  # Metadata complexity
        ]

        # Add binary features for specific patterns
        features.append(1.0 if "system" in evidence_entry.content.lower() else 0.0)
        features.append(1.0 if "network" in evidence_entry.content.lower() else 0.0)
        features.append(1.0 if "file" in evidence_entry.content.lower() else 0.0)

        return features


class EvidenceTestingUtilities:
    """Utilities for evidence system testing"""

    @staticmethod
    def create_test_repository() -> EvidenceRepository:
        """Create test repository in temporary directory"""
        temp_dir = tempfile.mkdtemp()
        return EvidenceRepository(temp_dir)

    @staticmethod
    def cleanup_test_repository(repository: EvidenceRepository):
        """Cleanup test repository"""
        if repository:
            repository.close()
            shutil.rmtree(repository.path, ignore_errors=True)

    @staticmethod
    def generate_test_evidence(count: int = 100) -> list[EvidenceEntry]:
        """Generate test evidence data"""
        evidence_entries = []
        operations = [
            "file_created",
            "file_modified",
            "network_request",
            "system_command",
            "user_login",
        ]
        levels = [
            EvidenceLevel.INFO,
            EvidenceLevel.WARNING,
            EvidenceLevel.ERROR,
            EvidenceLevel.CRITICAL,
        ]
        contents = [
            "Created user document",
            "Modified system configuration",
            "Connected to external service",
            "Executed system command",
            "User authentication successful",
            "File access detected",
            "Network connection established",
            "System modification detected",
        ]

        for i in range(count):
            evidence_entry = EvidenceEntry(
                operation=operations[i % len(operations)],
                content=contents[i % len(contents)],
                level=levels[i % len(levels)],
                metadata={"test_id": i, "batch": "test_batch", "generated": True},
            )
            evidence_entries.append(evidence_entry)

        return evidence_entries

    @staticmethod
    def validate_evidence_storage(
        repository: EvidenceRepository, evidence_entries: list[EvidenceEntry]
    ) -> bool:
        """Validate evidence storage and retrieval"""
        try:
            # Store evidence
            evidence_ids = repository.store_evidence_batch(evidence_entries)
            if len(evidence_ids) != len(evidence_entries):
                return False

            # Retrieve evidence
            for i, evidence_id in enumerate(evidence_ids):
                retrieved_entry = repository.get_evidence(evidence_id)
                if retrieved_entry is None:
                    return False
                if retrieved_entry.operation != evidence_entries[i].operation:
                    return False
                if retrieved_entry.content != evidence_entries[i].content:
                    return False

            return True
        except Exception as e:
            print(f"Evidence storage validation failed: {e}")
            return False

    @staticmethod
    def measure_evidence_performance(
        repository: EvidenceRepository, iterations: int = 100
    ) -> dict[str, float]:
        """Measure evidence system performance"""
        test_evidence = EvidenceTestingUtilities.generate_test_evidence(10)
        evidence_ids = repository.store_evidence_batch(test_evidence)

        # Measure storage performance
        start_time = time.time()
        for _ in range(iterations):
            test_ids = repository.store_evidence_batch(test_evidence)
        storage_time = (time.time() - start_time) / iterations

        # Measure query performance
        start_time = time.time()
        for _ in range(iterations):
            repository.query_evidence(limit=10)
        query_time = (time.time() - start_time) / iterations

        # Measure analysis performance
        analyzer = ExtendedEvidenceAnalyzer()
        start_time = time.time()
        for _ in range(iterations):
            for evidence_id in evidence_ids:
                evidence = repository.get_evidence(evidence_id)
                if evidence:
                    analyzer.analyze_evidence_content(evidence)
        analysis_time = (time.time() - start_time) / iterations

        return {
            "storage_time": storage_time,
            "query_time": query_time,
            "analysis_time": analysis_time,
            "total_time": storage_time + query_time + analysis_time,
        }

    @staticmethod
    def test_evidence_integrity(repository: EvidenceRepository) -> dict[str, Any]:
        """Test evidence system integrity"""
        test_evidence = EvidenceTestingUtilities.generate_test_evidence(50)
        evidence_ids = repository.store_evidence_batch(test_evidence)

        # Test data integrity
        integrity_result = repository.verify_data_integrity()

        # Test evidence consistency
        consistency_results = []
        for evidence_id in evidence_ids:
            original_evidence = repository.get_evidence(evidence_id)
            if original_evidence:
                # Test serialization/deserialization
                serialized = original_evidence.to_dict()
                deserialized = EvidenceEntry.from_dict(serialized)
                consistency = (
                    deserialized.operation == original_evidence.operation
                    and deserialized.content == original_evidence.content
                    and deserialized.level == original_evidence.level
                )
                consistency_results.append(consistency)

        consistency_rate = (
            sum(consistency_results) / len(consistency_results)
            if consistency_results
            else 0
        )

        return {
            "integrity_valid": integrity_result["is_valid"],
            "integrity_issues": integrity_result["corrupted_entries"],
            "consistency_rate": consistency_rate,
            "total_entries": len(evidence_ids),
        }

    @staticmethod
    def simulate_attack_pattern(repository: EvidenceRepository) -> list[EvidenceEntry]:
        """Simulate attack pattern for testing"""
        attack_sequence = [
            EvidenceEntry(
                operation="reconnaissance",
                content="Network scanning detected",
                level=EvidenceLevel.WARNING,
                metadata={
                    "scan_type": "port_scan",
                    "target": "internal_network",
                    "attacker_ip": "192.168.1.100",
                },
            ),
            EvidenceEntry(
                operation="exploitation",
                content="Exploitation attempt detected",
                level=EvidenceLevel.ERROR,
                metadata={
                    "exploit_type": "buffer_overflow",
                    "target": "web_server",
                    "vulnerability": "CVE-2023-1234",
                },
            ),
            EvidenceEntry(
                operation="privilege_escalation",
                content="Privilege escalation detected",
                level=EvidenceLevel.CRITICAL,
                metadata={
                    "escalation_type": "sudo",
                    "target_user": "root",
                    "method": "password_spray",
                },
            ),
            EvidenceEntry(
                operation="data_exfiltration",
                content="Data exfiltration detected",
                level=EvidenceLevel.CRITICAL,
                metadata={
                    "exfiltration_type": "file_transfer",
                    "destination_ip": "10.0.0.50",
                    "data_volume": "10GB",
                },
            ),
        ]

        return attack_sequence

    @staticmethod
    def simulate_normal_workflow(repository: EvidenceRepository) -> list[EvidenceEntry]:
        """Simulate normal workflow for testing"""
        normal_sequence = [
            EvidenceEntry(
                operation="user_login",
                content="User login successful",
                level=EvidenceLevel.INFO,
                metadata={
                    "user": "john.doe",
                    "ip": "192.168.1.10",
                    "auth_method": "password",
                },
            ),
            EvidenceEntry(
                operation="file_created",
                content="Created document",
                level=EvidenceLevel.INFO,
                metadata={
                    "file_path": "/home/john.doe/document.txt",
                    "file_size": "2KB",
                    "safe_operation": True,
                },
            ),
            EvidenceEntry(
                operation="network_request",
                content="Connected to cloud storage",
                level=EvidenceLevel.INFO,
                metadata={
                    "remote_host": "cloud.example.com",
                    "protocol": "https",
                    "safe_connection": True,
                },
            ),
            EvidenceEntry(
                operation="file_modified",
                content="Updated document",
                level=EvidenceLevel.INFO,
                metadata={
                    "file_path": "/home/john.doe/document.txt",
                    "edit_type": "text",
                    "safe_operation": True,
                },
            ),
        ]

        return normal_sequence


# Pytest fixtures
@pytest.fixture
def test_repository():
    """Fixture for test repository"""
    repository = EvidenceTestingUtilities.create_test_repository()
    yield repository
    EvidenceTestingUtilities.cleanup_test_repository(repository)


@pytest.fixture
def test_evidence_entries():
    """Fixture for test evidence entries"""
    return EvidenceTestingUtilities.generate_test_evidence(50)


@pytest.fixture
def test_attack_pattern():
    """Fixture for test attack pattern"""
    temp_dir = tempfile.mkdtemp()
    repository = EvidenceRepository(temp_dir)
    attack_evidence = EvidenceTestingUtilities.simulate_attack_pattern(repository)
    yield attack_evidence
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_normal_workflow():
    """Fixture for test normal workflow"""
    temp_dir = tempfile.mkdtemp()
    repository = EvidenceRepository(temp_dir)
    normal_evidence = EvidenceTestingUtilities.simulate_normal_workflow(repository)
    yield normal_evidence
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def extended_analyzer():
    """Fixture for extended evidence analyzer"""
    return ExtendedEvidenceAnalyzer()


# Test markers
pytest.mark.evidence_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.performance_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.integration_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)


# Test helpers
def validate_evidence_entry(entry: EvidenceEntry) -> bool:
    """Validate evidence entry structure"""
    required_fields = ["operation", "content", "level", "metadata"]
    for field in required_fields:
        if not hasattr(entry, field):
            return False
        if getattr(entry, field) is None:
            return False

    if not isinstance(entry.level, EvidenceLevel):
        return False

    if not isinstance(entry.metadata, dict):
        return False

    return True


def compare_evidence_entries(entry1: EvidenceEntry, entry2: EvidenceEntry) -> bool:
    """Compare two evidence entries"""
    return (
        entry1.operation == entry2.operation
        and entry1.content == entry2.content
        and entry1.level == entry2.level
        and entry1.metadata == entry2.metadata
    )


def validate_evidence_analysis(analysis_result: dict[str, Any]) -> bool:
    """Validate evidence analysis result"""
    required_fields = ["risk_score", "risk_level", "confidence"]
    for field in required_fields:
        if field not in analysis_result:
            return False

    if not (0.0 <= analysis_result["risk_score"] <= 1.0):
        return False

    if not (0.0 <= analysis_result["confidence"] <= 1.0):
        return False

    return True


def run_evidence_performance_test(
    repository: EvidenceRepository, iterations: int = 100
) -> dict[str, float]:
    """Run evidence performance test"""
    return EvidenceTestingUtilities.measure_evidence_performance(repository, iterations)


def run_evidence_integrity_test(repository: EvidenceRepository) -> dict[str, Any]:
    """Run evidence integrity test"""
    return EvidenceTestingUtilities.test_evidence_integrity(repository)


# Test configuration
EVIDENCE_TEST_CONFIG = {
    "max_evidence_count": 1000,
    "max_processing_time": 1.0,
    "min_confidence_threshold": 0.7,
    "max_risk_score": 1.0,
    "min_integrity_score": 0.95,
    "performance_threshold": {
        "storage_time": 0.01,
        "query_time": 0.005,
        "analysis_time": 0.01,
        "total_time": 0.05,
    },
}


# Integration test helpers
def test_evidence_system_integration(repository: EvidenceRepository):
    """Test evidence system integration"""
    # Create test evidence
    test_evidence = EvidenceTestingUtilities.generate_test_evidence(10)

    # Store evidence
    evidence_ids = repository.store_evidence_batch(test_evidence)
    assert len(evidence_ids) == len(test_evidence)

    # Query evidence
    retrieved_entries = repository.query_evidence(limit=10)
    assert len(retrieved_entries) > 0

    # Analyze evidence
    analyzer = ExtendedEvidenceAnalyzer()
    for entry in retrieved_entries:
        analysis = analyzer.analyze_evidence_content(entry)
        assert validate_evidence_analysis(analysis)

    # Test evidence correlation
    correlator = EvidenceCorrelator()
    correlation_result = correlator.correlate_evidence(evidence_ids)
    assert "correlation_strength" in correlation_result
    assert "correlation_type" in correlation_result


def test_evidence_pattern_detection(
    repository: EvidenceRepository, attack_pattern: list[EvidenceEntry]
):
    """Test evidence pattern detection"""
    # Store attack pattern
    attack_ids = repository.store_evidence_batch(attack_pattern)

    # Test pattern detection
    pattern_detector = PatternDetector()
    detected_patterns = pattern_detector.detect_patterns(attack_pattern)

    # Validate patterns
    assert len(detected_patterns) > 0
    assert "attack_chain" in detected_patterns
    assert detected_patterns["attack_chain"]["confidence"] > 0.8


def test_evidence_risk_assessment(
    repository: EvidenceRepository, test_evidence_entries: list[EvidenceEntry]
):
    """Test evidence risk assessment"""
    # Store evidence
    evidence_ids = repository.store_evidence_batch(test_evidence_entries)

    # Risk assessment
    risk_assessor = RiskAssessor()
    for evidence_id in evidence_ids:
        evidence = repository.get_evidence(evidence_id)
        if evidence:
            risk_score = risk_assessor.calculate_risk_score(evidence)
            assert 0.0 <= risk_score <= 1.0

            # Aggregated risk assessment
            aggregated_risk = risk_assessor.assess_aggregated_risk(evidence_ids)
            assert "mean_risk" in aggregated_risk
            assert "max_risk" in aggregated_risk
            assert "overall_risk_level" in aggregated_risk


def test_evidence_anomaly_detection(repository: EvidenceRepository):
    """Test evidence anomaly detection"""
    # Create normal behavior data
    normal_evidence = EvidenceTestingUtilities.simulate_normal_workflow(repository)
    normal_ids = repository.store_evidence_batch(normal_evidence)

    # Create anomalous evidence
    anomalous_evidence = EvidenceTestingUtilities.simulate_attack_pattern(repository)
    anomalous_ids = repository.store_evidence_batch(anomalous_evidence)

    # Test anomaly detection
    anomaly_detector = AnomalyDetector()
    anomalies = anomaly_detector.detect_statistical_anomalies(
        normal_evidence + anomalous_evidence
    )

    # Validate anomaly detection
    assert len(anomalies) > 0
    assert len(anomalies) <= len(anomalous_evidence)

    # Check that anomalies have high scores
    anomaly_scores = [a["anomaly_score"] for a in anomalies]
    assert max(anomaly_scores) > 0.5


# Performance test helpers
def benchmark_evidence_storage(
    repository: EvidenceRepository, batch_sizes: list[int] = [10, 50, 100, 500]
):
    """Benchmark evidence storage performance"""
    results = {}

    for batch_size in batch_sizes:
        test_evidence = EvidenceTestingUtilities.generate_test_evidence(batch_size)

        # Measure storage time
        start_time = time.time()
        evidence_ids = repository.store_evidence_batch(test_evidence)
        storage_time = time.time() - start_time

        results[batch_size] = {
            "storage_time": storage_time,
            "throughput": batch_size / storage_time if storage_time > 0 else 0,
            "evidence_count": batch_size,
            "evidence_ids": evidence_ids,
        }

    return results


def benchmark_evidence_query(repository: EvidenceRepository, query_patterns: list[str]):
    """Benchmark evidence query performance"""
    results = {}

    for pattern in query_patterns:
        # Query by operation
        start_time = time.time()
        results_by_operation = repository.query_evidence(operation=pattern, limit=100)
        operation_time = time.time() - start_time

        # Query by level
        start_time = time.time()
        results_by_level = repository.query_evidence(
            level=EvidenceLevel.INFO, limit=100
        )
        level_time = time.time() - start_time

        # Query with filters
        start_time = time.time()
        results_filtered = repository.query_evidence(
            operation=pattern, level=EvidenceLevel.INFO, limit=100
        )
        filtered_time = time.time() - start_time

        results[pattern] = {
            "operation_query_time": operation_time,
            "level_query_time": level_time,
            "filtered_query_time": filtered_time,
            "operation_results": len(results_by_operation),
            "level_results": len(results_by_level),
            "filtered_results": len(results_filtered),
        }

    return results


# Stress test helpers
def run_evidence_stress_test(
    repository: EvidenceRepository, evidence_count: int = 5000
):
    """Run evidence system stress test"""
    try:
        # Generate large amount of evidence
        stress_evidence = EvidenceTestingUtilities.generate_test_evidence(
            evidence_count
        )

        # Measure storage performance
        start_time = time.time()
        evidence_ids = repository.store_evidence_batch(stress_evidence)
        storage_time = time.time() - start_time

        # Query performance under load
        start_time = time.time()
        for _ in range(100):
            repository.query_evidence(limit=100)
        query_time = time.time() - start_time

        # Memory usage check
        import psutil

        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB

        return {
            "evidence_count": evidence_count,
            "storage_time": storage_time,
            "query_time": query_time,
            "memory_usage_mb": memory_usage,
            "throughput": evidence_count / storage_time if storage_time > 0 else 0,
            "success": True,
        }
    except Exception as e:
        return {"evidence_count": evidence_count, "error": str(e), "success": False}


# Test configuration
PYTEST_CONFIG = {
    "addopts": "-v --tb=short --strict-markers",
    "testpaths": ["."],
    "python_files": ["test_*.py"],
    "python_classes": ["Test*"],
    "python_functions": ["test_*"],
    "markers": {
        "evidence_testing": "Evidence system testing markers",
        "performance_testing": "Performance testing markers",
        "integration_testing": "Integration testing markers",
        "stress_testing": "Stress testing markers",
        "slow": "Slow running tests",
    },
}


__all__ = [
    "TestEvidenceScenario",
    "EvidenceTestResult",
    "PatternTestScenario",
    "RiskTestScenario",
    "ExtendedEvidenceAnalyzer",
    "EvidenceTestingUtilities",
    "validate_evidence_entry",
    "compare_evidence_entries",
    "validate_evidence_analysis",
    "run_evidence_performance_test",
    "run_evidence_integrity_test",
    "test_evidence_system_integration",
    "test_evidence_pattern_detection",
    "test_evidence_risk_assessment",
    "test_evidence_anomaly_detection",
    "benchmark_evidence_storage",
    "benchmark_evidence_query",
    "run_evidence_stress_test",
]
