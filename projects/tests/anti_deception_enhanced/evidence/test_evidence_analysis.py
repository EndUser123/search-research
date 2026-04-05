"""
Evidence Analysis Testing

This module implements comprehensive testing for evidence analysis capabilities
including pattern detection, correlation, risk assessment, and anomaly detection.
It validates the intelligence layer of the evidence system.

Test Categories:
1. Pattern Detection Analysis
2. Evidence Correlation
3. Risk Assessment Algorithms
4. Anomaly Detection
5. Behavioral Analysis
6. Threat Intelligence Integration
7. Machine Learning Analysis
8. Real-time Analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pytest

from anti_deception_enhanced.utils.evidence import (
    AnomalyDetector,
    EvidenceAnalyzer,
    EvidenceCorrelator,
    EvidenceEntry,
    EvidenceLevel,
    EvidenceRepository,
    PatternDetector,
    RiskAssessor,
)


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


class TestPatternDetection:
    """Test pattern detection algorithms"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.pattern_detector = PatternDetector()
        self.test_scenarios = [
            PatternTestScenario(
                name="attack_chain_pattern",
                evidence_sequence=[
                    EvidenceEntry(
                        operation="file_access",
                        content="Accessed /etc/passwd",
                        level=EvidenceLevel.WARNING,
                        metadata={"file_path": "/etc/passwd", "access_type": "read"},
                    ),
                    EvidenceEntry(
                        operation="network_request",
                        content="Data transmission to suspicious IP",
                        level=EvidenceLevel.WARNING,
                        metadata={"remote_ip": "192.168.1.100", "port": 443},
                    ),
                    EvidenceEntry(
                        operation="system_modified",
                        content="Modified /etc/hosts",
                        level=EvidenceLevel.CRITICAL,
                        metadata={
                            "config_path": "/etc/hosts",
                            "modification_type": "overwrite",
                        },
                    ),
                ],
                expected_pattern="attack_chain",
                expected_confidence=0.95,
                pattern_type="attack_sequence",
            ),
            PatternTestScenario(
                name="normal_workflow",
                evidence_sequence=[
                    EvidenceEntry(
                        operation="file_created",
                        content="Created user document",
                        level=EvidenceLevel.INFO,
                        metadata={
                            "file_path": "/home/user/document.txt",
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
                        },
                    ),
                    EvidenceEntry(
                        operation="file_modified",
                        content="Updated document",
                        level=EvidenceLevel.INFO,
                        metadata={
                            "file_path": "/home/user/document.txt",
                            "edit_type": "text",
                        },
                    ),
                ],
                expected_pattern="normal_workflow",
                expected_confidence=0.90,
                pattern_type="workflow",
            ),
            PatternTestScenario(
                name="brute_force_pattern",
                evidence_sequence=[
                    EvidenceEntry(
                        operation="login_attempt",
                        content="Failed login attempt",
                        level=EvidenceLevel.WARNING,
                        metadata={
                            "username": "admin",
                            "ip": "192.168.1.50",
                            "success": False,
                        },
                    ),
                    EvidenceEntry(
                        operation="login_attempt",
                        content="Failed login attempt",
                        level=EvidenceLevel.WARNING,
                        metadata={
                            "username": "admin",
                            "ip": "192.168.1.50",
                            "success": False,
                        },
                    ),
                    EvidenceEntry(
                        operation="login_attempt",
                        content="Failed login attempt",
                        level=EvidenceLevel.WARNING,
                        metadata={
                            "username": "admin",
                            "ip": "192.168.1.50",
                            "success": False,
                        },
                    ),
                    EvidenceEntry(
                        operation="login_attempt",
                        content="Successful login attempt",
                        level=EvidenceLevel.ERROR,
                        metadata={
                            "username": "admin",
                            "ip": "192.168.1.50",
                            "success": True,
                        },
                    ),
                ],
                expected_pattern="brute_force",
                expected_confidence=0.98,
                pattern_type="authentication",
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pattern_detection_algorithms(self):
        """Test pattern detection algorithms"""
        for scenario in self.test_scenarios:
            # Store evidence sequence
            evidence_ids = self.repository.store_evidence_batch(
                scenario.evidence_sequence
            )

            # Detect patterns
            detected_patterns = self.pattern_detector.detect_patterns(
                scenario.evidence_sequence, pattern_type=scenario.pattern_type
            )

            # Validate detection
            assert len(detected_patterns) > 0
            assert scenario.expected_pattern in detected_patterns

            detected_pattern = detected_patterns[scenario.expected_pattern]
            assert detected_pattern["confidence"] >= scenario.expected_confidence * 0.8
            assert detected_pattern["type"] == scenario.pattern_type

    def test_pattern_matching(self):
        """Test pattern matching algorithms"""
        test_patterns = {
            "attack_chain": {
                "indicators": ["file_access", "network_request", "system_modified"],
                "sequence_order": [0, 1, 2],
                "threshold": 0.9,
            },
            "normal_workflow": {
                "indicators": ["file_created", "network_request", "file_modified"],
                "sequence_order": [0, 1, 2],
                "threshold": 0.8,
            },
            "brute_force": {
                "indicators": ["login_attempt"],
                "frequency_threshold": 3,
                "success_rate": 0.0,
            },
        }

        for pattern_name, pattern_config in test_patterns.items():
            # Create test evidence sequence
            evidence_sequence = []
            for i, indicator in enumerate(pattern_config["indicators"]):
                if indicator == "login_attempt":
                    evidence_sequence.append(
                        EvidenceEntry(
                            operation=indicator,
                            content=f"Login attempt {i}",
                            level=EvidenceLevel.WARNING,
                            metadata={"attempt": i, "success": False},
                        )
                    )
                else:
                    evidence_sequence.append(
                        EvidenceEntry(
                            operation=indicator,
                            content=f"{indicator} event",
                            level=EvidenceLevel.INFO,
                            metadata={"event_id": i},
                        )
                    )

            # Test pattern matching
            match_result = self.pattern_detector.match_pattern(
                evidence_sequence, pattern_name, pattern_config
            )

            assert match_result["matched"] is True
            assert match_result["confidence"] >= pattern_config.get("threshold", 0.7)

    def test_pattern_confidence_calculation(self):
        """Test pattern confidence calculation"""
        test_cases = [
            ("perfect_match", 1.0),
            ("strong_match", 0.9),
            ("moderate_match", 0.7),
            ("weak_match", 0.5),
            ("no_match", 0.0),
        ]

        for match_type, expected_confidence in test_cases:
            # Create test evidence
            evidence_sequence = [
                EvidenceEntry(
                    operation="test_operation",
                    content=f"Test {match_type}",
                    level=EvidenceLevel.INFO,
                    metadata={"match_type": match_type},
                )
            ]

            # Calculate confidence
            confidence = self.pattern_detector.calculate_pattern_confidence(
                evidence_sequence, "test_pattern"
            )

            # Validate confidence
            assert confidence >= expected_confidence * 0.8
            assert confidence <= expected_confidence * 1.2

    def test_pattern_learning(self):
        """Test pattern learning from historical data"""
        # Create historical evidence data
        historical_data = []
        for i in range(100):
            if i < 70:  # Normal patterns
                historical_data.append(
                    EvidenceEntry(
                        operation="normal_operation",
                        content=f"Normal operation {i}",
                        level=EvidenceLevel.INFO,
                        metadata={"operation_id": i, "type": "normal"},
                    )
                )
            else:  # Anomalous patterns
                historical_data.append(
                    EvidenceEntry(
                        operation="suspicious_operation",
                        content=f"Suspicious operation {i}",
                        level=EvidenceLevel.WARNING,
                        metadata={"operation_id": i, "type": "suspicious"},
                    )
                )

        # Learn patterns
        learned_patterns = self.pattern_detector.learn_patterns(historical_data)

        # Validate learning
        assert len(learned_patterns) > 0
        assert "normal_operation" in learned_patterns
        assert "suspicious_operation" in learned_patterns

        # Test pattern recognition
        test_evidence = EvidenceEntry(
            operation="normal_operation",
            content="Test normal operation",
            level=EvidenceLevel.INFO,
            metadata={"test": True},
        )

        recognition_result = self.pattern_detector.recognize_pattern(
            test_evidence, learned_patterns
        )

        assert recognition_result["recognized"] is True
        assert recognition_result["pattern_type"] == "normal_operation"


class TestEvidenceCorrelation:
    """Test evidence correlation algorithms"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.correlator = EvidenceCorrelator()
        self.test_correlation_scenarios = [
            {
                "name": "multistage_attack_correlation",
                "evidence_set": [
                    EvidenceEntry(
                        operation="scanning",
                        content="Network scanning detected",
                        level=EvidenceLevel.WARNING,
                        metadata={
                            "scan_type": "port_scan",
                            "target": "internal_network",
                        },
                    ),
                    EvidenceEntry(
                        operation="exploitation",
                        content="Exploitation attempt detected",
                        level=EvidenceLevel.ERROR,
                        metadata={
                            "exploit_type": "buffer_overflow",
                            "target": "web_server",
                        },
                    ),
                    EvidenceEntry(
                        operation="persistence",
                        content="Persistence mechanism detected",
                        level=EvidenceLevel.CRITICAL,
                        metadata={"persistence_type": "backdoor", "target": "system"},
                    ),
                ],
                "expected_correlation_strength": 0.95,
                "correlation_type": "attack_chain",
            },
            {
                "name": "user_behavior_correlation",
                "evidence_set": [
                    EvidenceEntry(
                        operation="login",
                        content="User login",
                        level=EvidenceLevel.INFO,
                        metadata={"user": "admin", "ip": "192.168.1.100"},
                    ),
                    EvidenceEntry(
                        operation="file_access",
                        content="File access by user",
                        level=EvidenceLevel.INFO,
                        metadata={"user": "admin", "file_path": "/etc/passwd"},
                    ),
                    EvidenceEntry(
                        operation="system_command",
                        content="System command execution",
                        level=EvidenceLevel.WARNING,
                        metadata={"user": "admin", "command": "whoami"},
                    ),
                ],
                "expected_correlation_strength": 0.80,
                "correlation_type": "user_behavior",
            },
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evidence_correlation_algorithms(self):
        """Test evidence correlation algorithms"""
        for scenario in self.test_correlation_scenarios:
            # Store evidence
            evidence_ids = self.repository.store_evidence_batch(
                scenario["evidence_set"]
            )

            # Correlate evidence
            correlation_result = self.correlator.correlate_evidence(evidence_ids)

            # Validate correlation
            assert (
                correlation_result["correlation_strength"]
                >= scenario["expected_correlation_strength"]
            )
            assert (
                correlation_result["correlation_type"] == scenario["correlation_type"]
            )

    def test_temporal_correlation(self):
        """Test temporal correlation analysis"""
        # Create time-ordered evidence
        base_time = datetime.now()
        time_ordered_evidence = [
            EvidenceEntry(
                operation="phase1",
                content="Initial attack phase",
                level=EvidenceLevel.WARNING,
                metadata={"phase": 1, "timestamp": base_time},
                timestamp=base_time,
            ),
            EvidenceEntry(
                operation="phase2",
                content="Attack escalation",
                level=EvidenceLevel.ERROR,
                metadata={"phase": 2, "timestamp": base_time + timedelta(minutes=5)},
                timestamp=base_time + timedelta(minutes=5),
            ),
            EvidenceEntry(
                operation="phase3",
                content="Final attack phase",
                level=EvidenceLevel.CRITICAL,
                metadata={"phase": 3, "timestamp": base_time + timedelta(minutes=10)},
                timestamp=base_time + timedelta(minutes=10),
            ),
        ]

        # Test temporal correlation
        temporal_result = self.correlator.analyze_temporal_correlation(
            time_ordered_evidence
        )

        assert temporal_result["has_temporal_pattern"] is True
        assert temporal_result["time_intervals"] == [5, 5]  # 5 minutes between phases
        assert temporal_result["temporal_confidence"] > 0.8

    def test_semantic_correlation(self):
        """Test semantic correlation analysis"""
        # Create semantically related evidence
        semantic_evidence = [
            EvidenceEntry(
                operation="file_access",
                content="Accessed sensitive configuration",
                level=EvidenceLevel.WARNING,
                metadata={"file_path": "/etc/passwd", "content_type": "sensitive"},
            ),
            EvidenceEntry(
                operation="file_download",
                content="Downloaded sensitive data",
                level=EvidenceLevel.ERROR,
                metadata={"file_path": "/tmp/data_dump", "content_type": "sensitive"},
            ),
            EvidenceEntry(
                operation="network_transmission",
                content="Transmitted sensitive data",
                level=EvidenceLevel.CRITICAL,
                metadata={"remote_host": "attacker.com", "content_type": "sensitive"},
            ),
        ]

        # Test semantic correlation
        semantic_result = self.correlator.analyze_semantic_correlation(
            semantic_evidence
        )

        assert semantic_result["semantic_similarity"] > 0.7
        assert semantic_result["common_themes"] == ["sensitive"]
        assert semantic_result["semantic_confidence"] > 0.8

    def test_structural_correlation(self):
        """Test structural correlation analysis"""
        # Create structurally related evidence
        structural_evidence = [
            EvidenceEntry(
                operation="user_login",
                content="User authentication",
                level=EvidenceLevel.INFO,
                metadata={"user": "admin", "auth_type": "password"},
            ),
            EvidenceEntry(
                operation="privilege_escalation",
                content="Privilege escalation detected",
                level=EvidenceLevel.WARNING,
                metadata={"user": "admin", "escalation_type": "sudo"},
            ),
            EvidenceEntry(
                operation="system_access",
                content="System access gained",
                level=EvidenceLevel.ERROR,
                metadata={"user": "admin", "access_level": "root"},
            ),
        ]

        # Test structural correlation
        structural_result = self.correlator.analyze_structural_correlation(
            structural_evidence
        )

        assert structural_result["structural_similarity"] > 0.6
        assert structural_result["common_actor"] == "admin"
        assert structural_result["structural_confidence"] > 0.7


class TestRiskAssessment:
    """Test risk assessment algorithms"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.risk_assessor = RiskAssessor()
        self.test_risk_scenarios = [
            RiskTestScenario(
                name="low_risk_operation",
                evidence_entry=EvidenceEntry(
                    operation="file_created",
                    content="Created user document",
                    level=EvidenceLevel.INFO,
                    metadata={
                        "file_path": "/home/user/document.txt",
                        "safe_operation": True,
                    },
                ),
                expected_risk_score=0.1,
                expected_risk_level=EvidenceLevel.INFO,
                risk_factors={
                    "user_operation": 0.0,
                    "system_file": 0.0,
                    "network_activity": 0.0,
                },
            ),
            RiskTestScenario(
                name="medium_risk_operation",
                evidence_entry=EvidenceEntry(
                    operation="network_request",
                    content="Connected to external service",
                    level=EvidenceLevel.WARNING,
                    metadata={"remote_host": "external-service.com", "port": 80},
                ),
                expected_risk_score=0.5,
                expected_risk_level=EvidenceLevel.WARNING,
                risk_factors={"external_connection": 0.3, "data_exfiltration": 0.2},
            ),
            RiskTestScenario(
                name="high_risk_operation",
                evidence_entry=EvidenceEntry(
                    operation="system_modified",
                    content="Modified system configuration",
                    level=EvidenceLevel.CRITICAL,
                    metadata={
                        "config_path": "/etc/passwd",
                        "modification_type": "overwrite",
                    },
                ),
                expected_risk_score=0.9,
                expected_risk_level=EvidenceLevel.CRITICAL,
                risk_factors={
                    "system_file": 0.4,
                    "privilege_escalation": 0.3,
                    "data_breach": 0.2,
                },
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        for scenario in self.test_risk_scenarios:
            # Calculate risk score
            risk_score = self.risk_assessor.calculate_risk_score(
                scenario.evidence_entry
            )

            # Validate risk score
            assert abs(risk_score - scenario.expected_risk_score) <= 0.2
            assert 0.0 <= risk_score <= 1.0

    def test_risk_level_assessment(self):
        """Test risk level assessment"""
        test_risk_levels = [
            (0.0, 0.2, EvidenceLevel.DEBUG),
            (0.2, 0.4, EvidenceLevel.INFO),
            (0.4, 0.7, EvidenceLevel.WARNING),
            (0.7, 0.9, EvidenceLevel.ERROR),
            (0.9, 1.0, EvidenceLevel.CRITICAL),
        ]

        for min_score, max_score, expected_level in test_risk_levels:
            # Create test evidence
            evidence_entry = EvidenceEntry(
                operation="risk_test",
                content="Risk level test",
                level=EvidenceLevel.INFO,
                metadata={"risk_range": f"{min_score}-{max_score}"},
            )

            # Calculate risk score
            risk_score = self.risk_assessor.calculate_risk_score(evidence_entry)

            # Normalize to test range
            normalized_score = (risk_score - 0.0) / (1.0 - 0.0)
            normalized_score = min(max(normalized_score, 0.0), 1.0)

            # Assess risk level
            assessed_level = self.risk_assessor.assess_risk_level(normalized_score)

            assert assessed_level == expected_level

    def test_risk_factor_analysis(self):
        """Test risk factor analysis"""
        test_factors = [
            "user_privilege_level",
            "file_sensitivity",
            "network_destination",
            "operation_type",
            "time_of_day",
            "historical_behavior",
            "system_vulnerability",
            "data_classification",
        ]

        for factor in test_factors:
            # Analyze risk factor
            factor_analysis = self.risk_assessor.analyze_risk_factor(
                factor, {"test": True}
            )

            # Validate analysis
            assert "weight" in factor_analysis
            assert "impact" in factor_analysis
            assert "confidence" in factor_analysis
            assert 0.0 <= factor_analysis["weight"] <= 1.0
            assert 0.0 <= factor_analysis["impact"] <= 1.0
            assert 0.0 <= factor_analysis["confidence"] <= 1.0

    def test_aggregated_risk_assessment(self):
        """Test aggregated risk assessment"""
        # Create multiple evidence entries for aggregation
        evidence_entries = [
            EvidenceEntry(
                operation="suspicious_operation_1",
                content="Suspicious operation 1",
                level=EvidenceLevel.WARNING,
                metadata={"risk_score": 0.6},
            ),
            EvidenceEntry(
                operation="suspicious_operation_2",
                content="Suspicious operation 2",
                level=EvidenceLevel.ERROR,
                metadata={"risk_score": 0.8},
            ),
            EvidenceEntry(
                operation="suspicious_operation_3",
                content="Suspicious operation 3",
                level=EvidenceLevel.CRITICAL,
                metadata={"risk_score": 0.9},
            ),
        ]

        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(evidence_entries)

        # Perform aggregated risk assessment
        aggregated_risk = self.risk_assessor.assess_aggregated_risk(evidence_ids)

        # Validate aggregated risk
        assert "mean_risk" in aggregated_risk
        assert "max_risk" in aggregated_risk
        assert "risk_trend" in aggregated_risk
        assert "overall_risk_level" in aggregated_risk

        assert aggregated_risk["mean_risk"] >= 0.7
        assert aggregated_risk["max_risk"] >= 0.9
        assert aggregated_risk["overall_risk_level"] in EvidenceLevel


class TestAnomalyDetection:
    """Test anomaly detection algorithms"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.anomaly_detector = AnomalyDetector()
        self.normal_behavior_data = []
        self.anomalous_data = []

        # Generate normal behavior data
        for i in range(100):
            self.normal_behavior_data.append(
                {
                    "operation": "normal_operation",
                    "duration": np.random.normal(0.1, 0.02),  # Normal duration
                    "file_size": np.random.normal(1024, 100),  # Normal file size
                    "network_bytes": np.random.normal(512, 50),  # Normal network bytes
                    "timestamp": datetime.now() - timedelta(minutes=i),
                }
            )

        # Generate anomalous data
        for i in range(10):
            self.anomalous_data.append(
                {
                    "operation": "suspicious_operation",
                    "duration": np.random.normal(5.0, 1.0),  # Very long duration
                    "file_size": np.random.normal(1000000, 100000),  # Very large file
                    "network_bytes": np.random.normal(
                        1000000, 100000
                    ),  # Very large network bytes
                    "timestamp": datetime.now() - timedelta(minutes=i),
                }
            )

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection"""
        # Combine normal and anomalous data
        all_data = self.normal_behavior_data + self.anomalous_data

        # Detect anomalies
        anomalies = self.anomaly_detector.detect_statistical_anomalies(all_data)

        # Validate anomaly detection
        assert len(anomalies) > 0
        assert len(anomalies) <= len(self.anomalous_data)

        # Check that anomalies are correctly identified
        for anomaly in anomalies:
            assert anomaly["is_anomaly"] is True
            assert "anomaly_score" in anomaly
            assert anomaly["anomaly_score"] > 0.5

    def test_ml_based_anomaly_detection(self):
        """Test machine learning based anomaly detection"""
        # Prepare training data
        X_train = np.array(
            [
                [d["duration"], d["file_size"], d["network_bytes"]]
                for d in self.normal_behavior_data
            ]
        )

        # Prepare test data
        X_test = np.array(
            [[d["duration"], d["file_size"], d["network_bytes"]] for d in all_data]
        )

        # Detect anomalies using ML
        ml_anomalies = self.anomaly_detector.detect_ml_anomalies(
            X_train, X_test, algorithm="isolation_forest"
        )

        # Validate ML anomaly detection
        assert len(ml_anomalies) > 0
        assert all(0 <= anomaly["anomaly_score"] <= 1 for anomaly in ml_anomalies)

        # Check that anomalous data has higher anomaly scores
        normal_scores = [
            a["anomaly_score"] for a in ml_anomalies[: len(self.normal_behavior_data)]
        ]
        anomalous_scores = [
            a["anomaly_score"] for a in ml_anomalies[len(self.normal_behavior_data) :]
        ]

        assert np.mean(anomalous_scores) > np.mean(normal_scores)

    def test_behavioral_anomaly_detection(self):
        """Test behavioral anomaly detection"""
        # Create user behavior profiles
        user_profiles = {
            "user1": {
                "login_times": ["09:00", "17:00"],
                "typical_operations": ["file_access", "email"],
                "common_files": ["/home/user1/doc.txt"],
            },
            "user2": {
                "login_times": ["14:00", "22:00"],
                "typical_operations": ["code_edit", "database_access"],
                "common_files": ["/home/user2/project.py"],
            },
        }

        # Create test behavior data
        test_behavior = {
            "user": "user1",
            "login_time": "02:00",  # Unusual time for user1
            "operation": "system_command",  # Unusual operation for user1
            "file_path": "/etc/passwd",  # Unusual file for user1
        }

        # Detect behavioral anomalies
        behavioral_anomalies = self.anomaly_detector.detect_behavioral_anomalies(
            test_behavior, user_profiles
        )

        # Validate behavioral anomaly detection
        assert len(behavioral_anomalies) > 0
        assert all(anomaly["severity"] >= "low" for anomaly in behavioral_anomalies)

    def test_realtime_anomaly_detection(self):
        """Test real-time anomaly detection"""
        # Create real-time data stream
        data_stream = []
        for i in range(50):
            if i < 40:  # Normal data
                data_stream.append(
                    {
                        "timestamp": datetime.now() + timedelta(seconds=i),
                        "value": np.random.normal(0, 1),
                        "anomaly_score": 0.1,
                    }
                )
            else:  # Anomalous data
                data_stream.append(
                    {
                        "timestamp": datetime.now() + timedelta(seconds=i),
                        "value": np.random.normal(5, 1),  # Significant deviation
                        "anomaly_score": 0.8,
                    }
                )

        # Perform real-time anomaly detection
        realtime_anomalies = self.anomaly_detector.detect_realtime_anomalies(
            data_stream
        )

        # Validate real-time detection
        assert len(realtime_anomalies) > 0
        assert len(realtime_anomalies) <= len(
            [d for d in data_stream if d["anomaly_score"] > 0.5]
        )

        # Check that anomalies are flagged correctly
        for anomaly in realtime_anomalies:
            assert anomaly["is_realtime_anomaly"] is True
            assert "detection_time" in anomaly
            assert anomaly["detection_delay"] < 5.0  # Should detect quickly


class TestMachineLearningAnalysis:
    """Test machine learning analysis capabilities"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.ml_analyzer = EvidenceAnalyzer()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ml_model_training(self):
        """Test ML model training on evidence data"""
        # Create training data
        training_data = []
        for i in range(1000):
            if i < 800:  # Normal behavior
                training_data.append(
                    {
                        "features": [0.1, 0.2, 0.3],  # Low risk features
                        "label": "normal",
                    }
                )
            else:  # Anomalous behavior
                training_data.append(
                    {
                        "features": [0.8, 0.9, 1.0],  # High risk features
                        "label": "anomaly",
                    }
                )

        # Train ML model
        trained_model = self.ml_analyzer.train_ml_model(training_data)

        # Validate training
        assert trained_model is not None
        assert hasattr(trained_model, "predict")

    def test_ml_prediction(self):
        """Test ML prediction on new evidence"""
        # Create test data
        test_data = [
            {"features": [0.1, 0.2, 0.3], "expected_label": "normal"},
            {"features": [0.8, 0.9, 1.0], "expected_label": "anomaly"},
            {"features": [0.5, 0.5, 0.5], "expected_label": "uncertain"},
        ]

        # Train simple model
        from sklearn.ensemble import RandomForestClassifier

        X_train = [[0.1, 0.2, 0.3], [0.8, 0.9, 1.0], [0.5, 0.5, 0.5]]
        y_train = ["normal", "anomaly", "uncertain"]

        model = RandomForestClassifier(n_estimators=10)
        model.fit(X_train, y_train)

        # Test predictions
        for test_case in test_data:
            features = test_case["features"]
            prediction = model.predict([features])[0]
            probabilities = model.predict_proba([features])[0]

            # Validate prediction
            assert prediction in ["normal", "anomaly", "uncertain"]
            assert len(probabilities) == 3
            assert sum(probabilities) == 1.0

    def test_feature_importance_analysis(self):
        """Test feature importance analysis"""
        # Create feature importance data
        feature_importance = {
            "operation_type": 0.4,
            "file_path": 0.3,
            "network_destination": 0.2,
            "timestamp": 0.1,
        }

        # Analyze feature importance
        importance_analysis = self.ml_analyzer.analyze_feature_importance(
            feature_importance
        )

        # Validate analysis
        assert len(importance_analysis["top_features"]) > 0
        assert importance_analysis["most_important_feature"] == "operation_type"
        assert importance_analysis["importance_distribution"] == "highly_skewed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
