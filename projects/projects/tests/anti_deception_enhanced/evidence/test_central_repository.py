"""
Evidence System Tests for Central Repository

This module implements comprehensive testing for the central evidence repository
and cross-hook communication functionality. It validates evidence collection,
storage, retrieval, analysis, and system-wide evidence coordination.

Test Categories:
1. Central Repository Functionality
2. Evidence Collection and Validation
3. Cross-Hook Evidence Communication
4. Evidence Analysis and Correlation
5. Evidence Persistence and Recovery
6. Evidence Performance and Scalability
7. Evidence Security and Integrity
8. Evidence API and Integration
"""

import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pytest

from anti_deception_enhanced.hooks import AntiDeceptionHook
from anti_deception_enhanced.hooks.communication_system import CommunicationSystem
from anti_deception_enhanced.hooks.post_tool_use import PostToolUse
from anti_deception_enhanced.hooks.pre_tool_use import PreToolUse
from anti_deception_enhanced.utils.evidence import (
    EvidenceAnalyzer,
    EvidenceCorrelator,
    EvidenceEntry,
    EvidenceLevel,
    EvidenceRepository,
)
from anti_deception_enhanced.utils.mock_llm import MockLLMSupervisor, TestLLMScenario


@dataclass
class TestEvidenceScenario:
    """Test scenario for evidence collection"""

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


class TestCentralRepositoryFunctionality:
    """Test central repository functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.test_scenarios = [
            TestEvidenceScenario(
                name="file_creation",
                operation="file_created",
                content="Created safe file: test.py",
                level=EvidenceLevel.INFO,
                metadata={"file_path": "test.py", "file_size": 1024},
                expected_validation=True,
                risk_score=0.1,
            ),
            TestEvidenceScenario(
                name="system_modification",
                operation="system_modified",
                content="Modified system configuration",
                level=EvidenceLevel.WARNING,
                metadata={"config_path": "/etc/config", "backup_created": True},
                expected_validation=False,
                risk_score=0.7,
            ),
            TestEvidenceScenario(
                name="data_processing",
                operation="data_processed",
                content="Processed user data securely",
                level=EvidenceLevel.INFO,
                metadata={"data_type": "user_data", "records_count": 100},
                expected_validation=True,
                risk_score=0.2,
            ),
            TestEvidenceScenario(
                name="network_activity",
                operation="network_request",
                content="Made external API call",
                level=EvidenceLevel.WARNING,
                metadata={
                    "api_endpoint": "https://api.example.com",
                    "response_code": 200,
                },
                expected_validation=False,
                risk_score=0.5,
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repository_initialization(self):
        """Test repository initialization"""
        # Test repository creation
        assert self.repository.path == self.temp_dir
        assert self.repository.is_initialized()

        # Test database tables creation
        with self.repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "evidence_entries",
                "evidence_metadata",
                "evidence_analysis",
            ]
            for table in expected_tables:
                assert table in tables

    def test_evidence_storage_and_retrieval(self):
        """Test evidence storage and retrieval"""
        for scenario in self.test_scenarios:
            evidence_entry = scenario.to_entry()

            # Store evidence
            evidence_id = self.repository.store_evidence(evidence_entry)
            assert evidence_id is not None
            assert isinstance(evidence_id, int)

            # Retrieve evidence
            retrieved_entry = self.repository.get_evidence(evidence_id)
            assert retrieved_entry is not None
            assert retrieved_entry.operation == evidence_entry.operation
            assert retrieved_entry.content == evidence_entry.content
            assert retrieved_entry.level == evidence_entry.level

    def test_evidence_query_and_filtering(self):
        """Test evidence querying and filtering"""
        # Store all test scenarios
        for scenario in self.test_scenarios:
            evidence_entry = scenario.to_entry()
            self.repository.store_evidence(evidence_entry)

        # Test query by operation
        file_creation_entries = self.repository.query_evidence(
            operation="file_created", limit=10
        )
        assert len(file_creation_entries) == 1
        assert file_creation_entries[0].operation == "file_created"

        # Test query by level
        warning_entries = self.repository.query_evidence(
            level=EvidenceLevel.WARNING, limit=10
        )
        warning_count = len(
            [s for s in self.test_scenarios if s.level == EvidenceLevel.WARNING]
        )
        assert len(warning_entries) == warning_count

        # Test query by time range
        recent_entries = self.repository.query_evidence(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            limit=10,
        )
        assert len(recent_entries) == len(self.test_scenarios)

        # Test query with multiple filters
        info_entries = self.repository.query_evidence(
            level=EvidenceLevel.INFO, operation="file_created", limit=10
        )
        assert len(info_entries) == 1
        assert info_entries[0].level == EvidenceLevel.INFO

    def test_evidence_update_and_deletion(self):
        """Test evidence update and deletion"""
        scenario = self.test_scenarios[0]
        evidence_entry = scenario.to_entry()

        # Store evidence
        evidence_id = self.repository.store_evidence(evidence_entry)

        # Update evidence
        updated_content = "Updated evidence content"
        updated_metadata = {"updated": True, "timestamp": time.time()}
        success = self.repository.update_evidence(
            evidence_id, content=updated_content, metadata=updated_metadata
        )
        assert success is True

        # Verify update
        retrieved_entry = self.repository.get_evidence(evidence_id)
        assert retrieved_entry.content == updated_content
        assert retrieved_entry.metadata["updated"] is True

        # Delete evidence
        deletion_success = self.repository.delete_evidence(evidence_id)
        assert deletion_success is True

        # Verify deletion
        deleted_entry = self.repository.get_evidence(evidence_id)
        assert deleted_entry is None

    def test_evidence_batch_operations(self):
        """Test evidence batch operations"""
        # Batch store evidence
        evidence_entries = [scenario.to_entry() for scenario in self.test_scenarios]
        evidence_ids = self.repository.store_evidence_batch(evidence_entries)
        assert len(evidence_ids) == len(evidence_entries)

        # Verify batch storage
        for i, evidence_id in enumerate(evidence_ids):
            retrieved_entry = self.repository.get_evidence(evidence_id)
            assert retrieved_entry.operation == evidence_entries[i].operation

        # Batch query evidence
        all_entries = self.repository.query_evidence_batch(evidence_ids)
        assert len(all_entries) == len(evidence_ids)

        # Batch delete evidence
        deletion_success = self.repository.delete_evidence_batch(evidence_ids)
        assert deletion_success is True

        # Verify batch deletion
        for evidence_id in evidence_ids:
            deleted_entry = self.repository.get_evidence(evidence_id)
            assert deleted_entry is None


class TestEvidenceCollectionAndValidation:
    """Test evidence collection and validation"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.post_tool_use = PostToolUse()
        self.pre_tool_use = PreToolUse()
        self.test_scenarios = [
            TestEvidenceScenario(
                name="safe_file_operation",
                operation="file_created",
                content="Created safe file: example.py",
                level=EvidenceLevel.INFO,
                metadata={
                    "file_path": "example.py",
                    "file_size": 2048,
                    "safe_operation": True,
                },
                expected_validation=True,
                risk_score=0.1,
            ),
            TestEvidenceScenario(
                name="dangerous_file_operation",
                operation="file_deleted",
                content="Deleted system file: /etc/passwd",
                level=EvidenceLevel.CRITICAL,
                metadata={
                    "file_path": "/etc/passwd",
                    "system_file": True,
                    "dangerous_operation": True,
                },
                expected_validation=False,
                risk_score=0.95,
            ),
            TestEvidenceScenario(
                name="network_connection",
                operation="network_request",
                content="Connected to external server",
                level=EvidenceLevel.WARNING,
                metadata={
                    "remote_host": "malicious.com",
                    "port": 80,
                    "protocol": "http",
                },
                expected_validation=False,
                risk_score=0.8,
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evidence_collection_validation(self):
        """Test evidence collection and validation"""
        results = []

        for scenario in self.test_scenarios:
            evidence_entry = scenario.to_entry()

            # Collect evidence
            start_time = time.time()
            collected_evidence = self.post_tool_use.collect_evidence(evidence_entry)
            processing_time = time.time() - start_time

            # Validate evidence
            validation_result = self.repository.validate_evidence(collected_evidence)

            # Create test result
            test_result = EvidenceTestResult(
                scenario_name=scenario.name,
                validation_result=validation_result,
                evidence_entry=collected_evidence,
                processing_time=processing_time,
            )
            results.append(test_result)

            # Validate results
            assert validation_result == scenario.expected_validation
            assert test_result.processing_time < 1.0

        # Summary validation
        safe_operations = [r for r in results if r.validation_result]
        dangerous_operations = [r for r in results if not r.validation_result]

        assert len(safe_operations) == len(
            [s for s in self.test_scenarios if s.expected_validation]
        )
        assert len(dangerous_operations) == len(
            [s for s in self.test_scenarios if not s.expected_validation]
        )

    def test_evidence_content_analysis(self):
        """Test evidence content analysis"""
        test_contents = [
            "Created safe file: test.py",
            "Deleted system file: /etc/passwd",
            "Modified user data",
            "Read configuration file: config.json",
            "Made external API call to api.example.com",
        ]

        for content in test_contents:
            evidence_entry = EvidenceEntry(
                operation="test_operation",
                content=content,
                level=EvidenceLevel.INFO,
                metadata={"test": True},
            )

            # Analyze content
            analysis = self.repository.analyze_evidence_content(evidence_entry)

            # Validate analysis
            assert "risk_score" in analysis
            assert "content_type" in analysis
            assert "security_indicators" in analysis
            assert analysis["risk_score"] >= 0.0
            assert analysis["risk_score"] <= 1.0

    def test_evidence_metadata_validation(self):
        """Test evidence metadata validation"""
        test_metadata = [
            {"file_path": "safe_file.txt", "safe_operation": True},
            {"file_path": "/etc/passwd", "system_file": True},
            {"remote_host": "example.com", "connection_type": "https"},
            {"user_input": "safe_data", "validation_passed": True},
            {"script_content": "malicious code", "dangerous_operation": True},
        ]

        for metadata in test_metadata:
            evidence_entry = EvidenceEntry(
                operation="test_operation",
                content="Test content",
                level=EvidenceLevel.INFO,
                metadata=metadata,
            )

            # Validate metadata
            validation_result = self.repository.validate_evidence_metadata(
                evidence_entry
            )
            assert isinstance(validation_result, bool)

    def test_evidence_level_assessment(self):
        """Test evidence level assessment"""
        test_cases = [
            ("Safe file operation", EvidenceLevel.INFO),
            ("Suspicious network activity", EvidenceLevel.WARNING),
            ("Potential security breach", EvidenceLevel.CRITICAL),
            ("System modification", EvidenceLevel.WARNING),
            ("User data access", EvidenceLevel.INFO),
        ]

        for content, expected_level in test_cases:
            evidence_entry = EvidenceEntry(
                operation="test_operation",
                content=content,
                level=EvidenceLevel.INFO,
                metadata={"test": True},
            )

            # Assess evidence level
            assessed_level = self.repository.assess_evidence_level(evidence_entry)
            assert assessed_level == expected_level


class TestCrossHookEvidenceCommunication:
    """Test cross-hook evidence communication"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.hook = AntiDeceptionHook()
        self.communication_system = CommunicationSystem()
        self.mock_supervisor = MockLLMSupervisor()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evidence_between_hooks(self):
        """Test evidence communication between hooks"""
        test_evidence = [
            TestEvidenceScenario(
                name="pre_to_post",
                operation="file_validated",
                content="File path validation passed",
                level=EvidenceLevel.INFO,
                metadata={"validation_type": "path", "result": "passed"},
                expected_validation=True,
            ),
            TestEvidenceScenario(
                name="post_to_llm",
                operation="file_processed",
                content="File processed successfully",
                level=EvidenceLevel.INFO,
                metadata={"processing_type": "normal", "success": True},
                expected_validation=True,
            ),
            TestEvidenceScenario(
                name="llm_to_communication",
                operation="llm_validated",
                content="LLM validation completed",
                level=EvidenceLevel.INFO,
                metadata={"validation_type": "llm", "result": "approved"},
                expected_validation=True,
            ),
        ]

        # Test evidence flow between hooks
        for i, scenario in enumerate(test_evidence):
            evidence_entry = scenario.to_entry()

            # Simulate evidence passing between hooks
            if i == 0:  # Pre to Post
                pre_result = self.hook.pre_tool_use.validate_file_path("test_file")
                post_result = self.hook.post_tool_use.collect_evidence(evidence_entry)
            elif i == 1:  # Post to LLM
                post_result = self.hook.post_tool_use.collect_evidence(evidence_entry)
                llm_scenario = TestLLMScenario(
                    name="llm_comm_test",
                    user_prompt=evidence_entry.content,
                    controlled_response="LLM validation approved",
                    expected_confidence=0.90,
                    expected_cost=0.002,
                    expected_validation=True,
                )
                self.mock_supervisor.set_scenario(llm_scenario)
                llm_result = self.mock_supervisor.validate_user_input(
                    evidence_entry.content
                )
            else:  # LLM to Communication
                llm_result = self.mock_supervisor.validate_user_input(
                    evidence_entry.content
                )
                comm_result = self.communication_system.send_message(
                    "llm_validation", evidence_entry.to_dict()
                )

            # Validate evidence integrity
            assert evidence_entry.operation == scenario.operation
            assert evidence_entry.content == scenario.content
            assert evidence_entry.level == scenario.level

    def test_evidence_synchronization(self):
        """Test evidence synchronization between hooks"""
        test_evidence = EvidenceEntry(
            operation="sync_test",
            content="Synchronization test",
            level=EvidenceLevel.INFO,
            metadata={"sync_test": True},
        )

        # Store evidence in repository
        evidence_id = self.repository.store_evidence(test_evidence)

        # Test synchronization across hooks
        sync_results = []

        def synchronize_evidence(hook_name, evidence_entry):
            """Simulate evidence synchronization"""
            # Store in hook's local cache
            cache_key = f"{hook_name}_{evidence_id}"
            cache_value = {
                "evidence_id": evidence_id,
                "hook_name": hook_name,
                "timestamp": time.time(),
            }
            return cache_key, cache_value

        # Synchronize with multiple hooks
        hooks = [
            "pre_tool_use",
            "post_tool_use",
            "llm_supervisor",
            "communication_system",
        ]
        for hook_name in hooks:
            cache_key, cache_value = synchronize_evidence(hook_name, test_evidence)
            sync_results.append((cache_key, cache_value))

        # Validate synchronization
        assert len(sync_results) == len(hooks)
        for i, (cache_key, cache_value) in enumerate(sync_results):
            expected_key = f"{hooks[i]}_{evidence_id}"
            assert cache_key == expected_key
            assert cache_value["evidence_id"] == evidence_id
            assert cache_value["hook_name"] == hooks[i]

    def test_evidence_priority_handling(self):
        """Test evidence priority handling in communication"""
        priority_test_cases = [
            ("critical_security_event", 10, EvidenceLevel.CRITICAL),
            ("high_risk_operation", 8, EvidenceLevel.WARNING),
            ("normal_operation", 5, EvidenceLevel.INFO),
            ("low_priority_event", 2, EvidenceLevel.DEBUG),
        ]

        for event_type, priority, level in priority_test_cases:
            evidence_entry = EvidenceEntry(
                operation=event_type,
                content=f"Test {event_type}",
                level=level,
                metadata={"priority": priority, "event_type": event_type},
            )

            # Test priority-based communication
            priority_score = self.communication_system.calculate_priority(
                evidence_entry
            )
            assert priority_score == priority

            # Test priority routing
            routing_result = self.communication_system.route_message(
                "evidence", evidence_entry.to_dict(), priority_score
            )
            assert routing_result["priority"] == priority

    def test_evidence_message_formatting(self):
        """Test evidence message formatting for communication"""
        test_evidence = EvidenceEntry(
            operation="format_test",
            content="Message formatting test",
            level=EvidenceLevel.INFO,
            metadata={"format_test": True, "test_id": 123},
        )

        # Test message formatting
        formatted_message = self.communication_system.format_evidence_message(
            test_evidence
        )
        assert formatted_message["operation"] == test_evidence.operation
        assert formatted_message["content"] == test_evidence.content
        assert formatted_message["level"] == test_evidence.level.name
        assert formatted_message["metadata"] == test_evidence.metadata

        # Test message serialization
        serialized_message = json.dumps(formatted_message)
        deserialized_message = json.loads(serialized_message)
        assert deserialized_message == formatted_message


class TestEvidenceAnalysisAndCorrelation:
    """Test evidence analysis and correlation"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.analyzer = EvidenceAnalyzer()
        self.correlator = EvidenceCorrelator()
        self.test_scenarios = [
            TestEvidenceScenario(
                name="suspicious_file_chain",
                operation="file_access",
                content="Accessed sensitive file",
                level=EvidenceLevel.WARNING,
                metadata={"file_path": "/etc/passwd", "access_type": "read"},
                expected_validation=False,
                risk_score=0.8,
            ),
            TestEvidenceScenario(
                name="network_connection",
                operation="network_request",
                content="Connected to suspicious IP",
                level=EvidenceLevel.WARNING,
                metadata={"remote_ip": "192.168.1.100", "port": 443},
                expected_validation=False,
                risk_score=0.7,
            ),
            TestEvidenceScenario(
                name="system_modification",
                operation="system_modified",
                content="Modified system configuration",
                level=EvidenceLevel.CRITICAL,
                metadata={
                    "config_path": "/etc/hosts",
                    "modification_type": "overwrite",
                },
                expected_validation=False,
                risk_score=0.9,
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evidence_pattern_analysis(self):
        """Test evidence pattern analysis"""
        # Store test evidence
        evidence_entries = [scenario.to_entry() for scenario in self.test_scenarios]
        evidence_ids = self.repository.store_evidence_batch(evidence_entries)

        # Analyze patterns
        patterns = self.analyzer.analyze_patterns(evidence_entries)

        # Validate patterns
        assert len(patterns) > 0
        assert "suspicious_chain" in patterns
        assert patterns["suspicious_chain"]["risk_level"] == "high"
        assert patterns["suspicious_chain"]["confidence"] > 0.8

    def test_evidence_correlation(self):
        """Test evidence correlation"""
        # Create related evidence entries
        related_evidence = [
            EvidenceEntry(
                operation="file_access",
                content="Accessed sensitive file",
                level=EvidenceLevel.WARNING,
                metadata={"file_path": "/etc/passwd", "access_type": "read"},
            ),
            EvidenceEntry(
                operation="network_request",
                content="Transmitted file data",
                level=EvidenceLevel.WARNING,
                metadata={"remote_ip": "192.168.1.100", "data_size": 1024},
            ),
            EvidenceEntry(
                operation="system_modified",
                content="Modified system configuration",
                level=EvidenceLevel.CRITICAL,
                metadata={
                    "config_path": "/etc/hosts",
                    "modification_type": "overwrite",
                },
            ),
        ]

        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(related_evidence)

        # Correlate evidence
        correlations = self.correlator.correlate_evidence(evidence_ids)

        # Validate correlations
        assert len(correlations) > 0
        assert "attack_chain" in correlations
        assert correlations["attack_chain"]["strength"] > 0.7

    def test_evidence_trend_analysis(self):
        """Test evidence trend analysis"""
        # Create evidence with timestamps
        current_time = datetime.now()
        time_series_evidence = [
            EvidenceEntry(
                operation="file_access",
                content="File access event",
                level=EvidenceLevel.INFO,
                metadata={"timestamp": current_time - timedelta(hours=3)},
                timestamp=current_time - timedelta(hours=3),
            ),
            EvidenceEntry(
                operation="network_request",
                content="Network request",
                level=EvidenceLevel.INFO,
                metadata={"timestamp": current_time - timedelta(hours=2)},
                timestamp=current_time - timedelta(hours=2),
            ),
            EvidenceEntry(
                operation="system_modified",
                content="System modification",
                level=EvidenceLevel.INFO,
                metadata={"timestamp": current_time - timedelta(hours=1)},
                timestamp=current_time - timedelta(hours=1),
            ),
        ]

        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(time_series_evidence)

        # Analyze trends
        trends = self.analyzer.analyze_trends(evidence_ids)

        # Validate trends
        assert "temporal_pattern" in trends
        assert trends["temporal_pattern"]["frequency"] > 0

    def test_evidence_risk_scoring(self):
        """Test evidence risk scoring"""
        test_risk_cases = [
            (EvidenceLevel.DEBUG, 0.1),
            (EvidenceLevel.INFO, 0.3),
            (EvidenceLevel.WARNING, 0.6),
            (EvidenceLevel.ERROR, 0.8),
            (EvidenceLevel.CRITICAL, 1.0),
        ]

        for level, expected_risk in test_risk_cases:
            evidence_entry = EvidenceEntry(
                operation="risk_test",
                content="Risk testing",
                level=level,
                metadata={"test": True},
            )

            # Calculate risk score
            risk_score = self.analyzer.calculate_risk_score(evidence_entry)

            # Validate risk score
            assert risk_score >= expected_risk * 0.8
            assert risk_score <= expected_risk * 1.2


class TestEvidencePersistenceAndRecovery:
    """Test evidence persistence and recovery"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repository = EvidenceRepository(self.temp_dir)
        self.test_evidence = [
            EvidenceEntry(
                operation="persistence_test_1",
                content="Persistence test 1",
                level=EvidenceLevel.INFO,
                metadata={"test": True, "id": 1},
            ),
            EvidenceEntry(
                operation="persistence_test_2",
                content="Persistence test 2",
                level=EvidenceLevel.WARNING,
                metadata={"test": True, "id": 2},
            ),
            EvidenceEntry(
                operation="persistence_test_3",
                content="Persistence test 3",
                level=EvidenceLevel.ERROR,
                metadata={"test": True, "id": 3},
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evidence_persistence(self):
        """Test evidence persistence across sessions"""
        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(self.test_evidence)
        assert len(evidence_ids) == len(self.test_evidence)

        # Close repository
        self.repository.close()

        # Create new repository instance
        new_repository = EvidenceRepository(self.temp_dir)

        # Verify evidence persistence
        for i, evidence_id in enumerate(evidence_ids):
            retrieved_entry = new_repository.get_evidence(evidence_id)
            assert retrieved_entry is not None
            assert retrieved_entry.operation == self.test_evidence[i].operation
            assert retrieved_entry.content == self.test_evidence[i].content
            assert retrieved_entry.level == self.test_evidence[i].level

        new_repository.close()

    def test_evidence_recovery_after_failure(self):
        """Test evidence recovery after failure"""
        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(self.test_evidence)

        # Simulate failure (close connection abruptly)
        self.repository.close()

        # Recover repository
        recovered_repository = EvidenceRepository(self.temp_dir)

        # Verify recovery
        recovered_count = 0
        for evidence_id in evidence_ids:
            retrieved_entry = recovered_repository.get_evidence(evidence_id)
            if retrieved_entry is not None:
                recovered_count += 1

        # Validate recovery rate
        recovery_rate = recovered_count / len(evidence_ids)
        assert recovery_rate >= 0.95  # 95% recovery rate

        recovered_repository.close()

    def test_evidence_backup_and_restore(self):
        """Test evidence backup and restore"""
        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(self.test_evidence)

        # Create backup
        backup_dir = tempfile.mkdtemp()
        backup_success = self.repository.create_backup(backup_dir)
        assert backup_success is True

        # Verify backup files exist
        assert self.repository.backup_exists(backup_dir)

        # Restore from backup
        restore_dir = tempfile.mkdtemp()
        restore_success = self.repository.restore_from_backup(backup_dir, restore_dir)
        assert restore_success is True

        # Verify restore
        restored_repository = EvidenceRepository(restore_dir)
        for evidence_id in evidence_ids:
            retrieved_entry = restored_repository.get_evidence(evidence_id)
            assert retrieved_entry is not None

        restored_repository.close()
        shutil.rmtree(backup_dir, ignore_errors=True)
        shutil.rmtree(restore_dir, ignore_errors=True)

    def test_evidence_data_integrity(self):
        """Test evidence data integrity"""
        # Store evidence
        evidence_ids = self.repository.store_evidence_batch(self.test_evidence)

        # Verify data integrity
        integrity_check = self.repository.verify_data_integrity()
        assert integrity_check["is_valid"] is True
        assert integrity_check["corrupted_entries"] == 0
        assert integrity_check["total_entries"] == len(self.test_evidence)

        # Simulate corruption
        with self.repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE evidence_entries SET content = NULL WHERE id = ?",
                (evidence_ids[0],),
            )
            conn.commit()

        # Check integrity after corruption
        integrity_check = self.repository.verify_data_integrity()
        assert integrity_check["is_valid"] is False
        assert integrity_check["corrupted_entries"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
