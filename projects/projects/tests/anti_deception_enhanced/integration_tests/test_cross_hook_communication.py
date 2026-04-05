"""
Integration Tests for Cross-Hook Communication
==============================================

Tests the communication system between different hooks (UserPromptSubmit,
PreToolUse, PostToolUse, Stop) and the evidence repository.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Import cross-hook communication components
try:
    from hook_communication import CrossHookCommunicator, EvidenceRepository, HookEvent
except ImportError:
    pytest.skip(
        "Cross-hook communication components not available", allow_module_level=True
    )


class TestEvidenceRepository:
    """Test EvidenceRepository functionality."""

    @pytest.fixture
    def evidence_repo(self):
        """Create EvidenceRepository instance for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        repo = EvidenceRepository(storage_path=temp_dir / "evidence")
        yield repo
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_evidence(self):
        """Sample evidence for testing."""
        return {
            "operation_id": "op_12345",
            "hook_name": "PostToolUse",
            "tool_name": "Edit",
            "evidence_type": "code_change",
            "data": {
                "file_path": "src/test.py",
                "change_summary": "Added validation logic",
                "safety_check": "passed",
                "performance_impact": "minimal",
            },
            "timestamp": "2025-01-26T10:30:00Z",
            "session_id": "sess_abc123",
        }

    def test_evidence_storage(self, evidence_repo, sample_evidence):
        """Test storing evidence in repository."""
        success = evidence_repo.store_evidence(sample_evidence)

        assert success is True

        # Verify evidence was stored
        retrieved = evidence_repo.get_evidence(sample_evidence["operation_id"])
        assert retrieved is not None
        assert retrieved["tool_name"] == "Edit"
        assert retrieved["evidence_type"] == "code_change"

    def test_evidence_retrieval_by_operation(self, evidence_repo, sample_evidence):
        """Test retrieving evidence by operation ID."""
        evidence_repo.store_evidence(sample_evidence)

        evidence = evidence_repo.get_evidence(sample_evidence["operation_id"])

        assert evidence is not None
        assert evidence["operation_id"] == sample_evidence["operation_id"]
        assert "data" in evidence
        assert evidence["data"]["file_path"] == "src/test.py"

    def test_evidence_retrieval_by_session(self, evidence_repo, sample_evidence):
        """Test retrieving evidence by session ID."""
        # Store multiple evidence items for the same session
        evidence_repo.store_evidence(sample_evidence)

        second_evidence = {
            "operation_id": "op_67890",
            "hook_name": "PreToolUse",
            "tool_name": "Bash",
            "evidence_type": "test_execution",
            "data": {"test_command": "pytest", "result": "passed"},
            "timestamp": "2025-01-26T10:31:00Z",
            "session_id": sample_evidence["session_id"],
        }
        evidence_repo.store_evidence(second_evidence)

        session_evidence = evidence_repo.get_session_evidence(
            sample_evidence["session_id"]
        )

        assert len(session_evidence) == 2
        operation_ids = [e["operation_id"] for e in session_evidence]
        assert "op_12345" in operation_ids
        assert "op_67890" in operation_ids

    def test_evidence_query_by_type(self, evidence_repo, sample_evidence):
        """Test querying evidence by type."""
        evidence_repo.store_evidence(sample_evidence)

        code_change_evidence = evidence_repo.get_evidence_by_type("code_change")

        assert len(code_change_evidence) == 1
        assert code_change_evidence[0]["evidence_type"] == "code_change"

    def test_evidence_persistence(self, evidence_repo, sample_evidence):
        """Test evidence persistence across repository instances."""
        # Store evidence in first instance
        evidence_repo.store_evidence(sample_evidence)

        # Create new instance with same storage path
        new_repo = EvidenceRepository(storage_path=evidence_repo.storage_path)

        # Should retrieve stored evidence
        evidence = new_repo.get_evidence(sample_evidence["operation_id"])
        assert evidence is not None
        assert evidence["operation_id"] == sample_evidence["operation_id"]

    def test_evidence_validation(self, evidence_repo):
        """Test evidence validation before storage."""
        invalid_evidence = {
            # Missing required fields
            "hook_name": "PostToolUse",
            "tool_name": "Edit",
        }

        success = evidence_repo.store_evidence(invalid_evidence)
        assert success is False


class TestCrossHookCommunicator:
    """Test CrossHookCommunicator functionality."""

    @pytest.fixture
    def communicator(self):
        """Create CrossHookCommunicator instance for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        communicator = CrossHookCommunicator(storage_path=temp_dir / "communication")
        yield communicator
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_hook_event(self):
        """Sample hook event for testing."""
        return HookEvent(
            hook_name="PostToolUse",
            event_type="validation_completed",
            data={
                "operation_id": "op_12345",
                "tool_name": "Edit",
                "validation_result": {
                    "is_valid": True,
                    "confidence": 0.95,
                    "issues": [],
                },
            },
            timestamp="2025-01-26T10:30:00Z",
        )

    @pytest.mark.asyncio
    async def test_event_broadcasting(self, communicator, sample_hook_event):
        """Test broadcasting events to other hooks."""
        # Mock event handlers
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        # Register handlers
        communicator.register_handler("PreToolUse", handler1)
        communicator.register_handler("UserPromptSubmit", handler2)

        # Broadcast event
        await communicator.broadcast_event(sample_hook_event)

        # Both handlers should be called
        handler1.assert_called_once_with(sample_hook_event)
        handler2.assert_called_once_with(sample_hook_event)

    @pytest.mark.asyncio
    async def test_targeted_event_sending(self, communicator, sample_hook_event):
        """Test sending events to specific hooks."""
        # Mock handlers
        target_handler = AsyncMock()
        other_handler = AsyncMock()

        # Register handlers
        communicator.register_handler("PreToolUse", target_handler)
        communicator.register_handler("UserPromptSubmit", other_handler)

        # Send event to specific hook
        await communicator.send_to_hook("PreToolUse", sample_hook_event)

        # Only target handler should be called
        target_handler.assert_called_once_with(sample_hook_event)
        other_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_event_filtering(self, communicator, sample_hook_event):
        """Test event filtering based on event type."""
        # Mock handler that only accepts specific event types
        filtered_handler = AsyncMock()

        # Register handler with filter
        communicator.register_handler(
            "PreToolUse", filtered_handler, event_types=["validation_completed"]
        )

        # Broadcast matching event
        await communicator.broadcast_event(sample_hook_event)

        # Handler should be called
        filtered_handler.assert_called_once_with(sample_hook_event)

        # Reset and test non-matching event
        filtered_handler.reset_mock()
        different_event = HookEvent(
            hook_name="PostToolUse", event_type="different_event", data={"test": "data"}
        )

        await communicator.broadcast_event(different_event)

        # Handler should not be called for non-matching event
        filtered_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_hook_state_synchronization(self, communicator):
        """Test synchronization of hook states."""
        # Set initial state
        await communicator.set_hook_state(
            "PostToolUse",
            {
                "validation_count": 5,
                "last_validation": "2025-01-26T10:30:00Z",
                "error_count": 0,
            },
        )

        # Retrieve state
        state = await communicator.get_hook_state("PostToolUse")

        assert state["validation_count"] == 5
        assert state["error_count"] == 0

    @pytest.mark.asyncio
    async def test_session_wide_state_management(self, communicator):
        """Test session-wide state management."""
        session_id = "test_session_123"

        # Set session state
        await communicator.set_session_state(
            session_id,
            {"total_operations": 10, "active_validations": 2, "risk_level": "medium"},
        )

        # Retrieve session state
        state = await communicator.get_session_state(session_id)

        assert state["total_operations"] == 10
        assert state["active_validations"] == 2

    def test_event_serialization(self, communicator, sample_hook_event):
        """Test event serialization and deserialization."""
        # Serialize event
        serialized = communicator._serialize_event(sample_hook_event)

        assert isinstance(serialized, dict)
        assert serialized["hook_name"] == sample_hook_event.hook_name
        assert serialized["event_type"] == sample_hook_event.event_type

        # Deserialize event
        deserialized = communicator._deserialize_event(serialized)

        assert deserialized.hook_name == sample_hook_event.hook_name
        assert deserialized.event_type == sample_hook_event.event_type
        assert deserialized.data == sample_hook_event.data


class TestHookIntegrationWorkflows:
    """Test realistic hook integration workflows."""

    @pytest.fixture
    def integrated_system(self):
        """Create integrated system for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        evidence_repo = EvidenceRepository(storage_path=temp_dir / "evidence")
        communicator = CrossHookCommunicator(
            storage_path=temp_dir / "communication", evidence_repo=evidence_repo
        )

        yield {
            "evidence_repo": evidence_repo,
            "communicator": communicator,
            "temp_dir": temp_dir,
        }

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_pre_to_post_tool_use_workflow(self, integrated_system):
        """Test workflow from PreToolUse to PostToolUse."""
        evidence_repo = integrated_system["evidence_repo"]
        communicator = integrated_system["communicator"]

        operation_id = "op_workflow_123"
        session_id = "sess_workflow_456"

        # PreToolUse stores initial evidence
        pre_evidence = {
            "operation_id": operation_id,
            "hook_name": "PreToolUse",
            "tool_name": "Edit",
            "evidence_type": "pre_validation",
            "data": {
                "validation_passed": True,
                "risk_assessment": "low",
                "safety_checks": "completed",
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(pre_evidence)

        # PreToolUse broadcasts validation start
        pre_event = HookEvent(
            hook_name="PreToolUse",
            event_type="validation_started",
            data={"operation_id": operation_id, "tool_name": "Edit"},
        )
        await communicator.broadcast_event(pre_event)

        # PostToolUse receives event and stores completion evidence
        post_evidence = {
            "operation_id": operation_id,
            "hook_name": "PostToolUse",
            "tool_name": "Edit",
            "evidence_type": "post_validation",
            "data": {
                "validation_completed": True,
                "final_result": "success",
                "performance_ok": True,
            },
            "session_id": session_id,
        }
        evidence_repo.store_evidence(post_evidence)

        # Verify complete workflow evidence
        session_evidence = evidence_repo.get_session_evidence(session_id)

        assert len(session_evidence) == 2
        evidence_types = [e["evidence_type"] for e in session_evidence]
        assert "pre_validation" in evidence_types
        assert "post_validation" in evidence_types

    @pytest.mark.asyncio
    async def test_error_propagation_workflow(self, integrated_system):
        """Test error propagation between hooks."""
        communicator = integrated_system["communicator"]

        # Mock error handler in PostToolUse
        error_handler = AsyncMock()
        communicator.register_handler("PostToolUse", error_handler)

        # PreToolUse detects error and broadcasts
        error_event = HookEvent(
            hook_name="PreToolUse",
            event_type="validation_error",
            data={
                "operation_id": "op_error_123",
                "error_type": "safety_violation",
                "error_message": "Dangerous operation detected",
                "severity": "critical",
            },
        )
        await communicator.broadcast_event(error_event)

        # PostToolUse should receive and handle error
        error_handler.assert_called_once()
        received_event = error_handler.call_args[0][0]

        assert received_event.event_type == "validation_error"
        assert received_event.data["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_session_lifecycle_management(self, integrated_system):
        """Test session lifecycle across multiple hooks."""
        evidence_repo = integrated_system["evidence_repo"]
        communicator = integrated_system["communicator"]

        session_id = "lifecycle_test_session"

        # UserPromptSubmit starts session
        session_start_event = HookEvent(
            hook_name="UserPromptSubmit",
            event_type="session_started",
            data={"session_id": session_id, "user_request": "test request"},
        )
        await communicator.broadcast_event(session_start_event)

        # Multiple operations occur
        for i in range(3):
            operation_id = f"op_{i}"
            evidence = {
                "operation_id": operation_id,
                "hook_name": "PostToolUse",
                "tool_name": "Edit",
                "evidence_type": "operation_completed",
                "data": {"operation": i, "result": "success"},
                "session_id": session_id,
            }
            evidence_repo.store_evidence(evidence)

        # Stop hook ends session
        session_end_event = HookEvent(
            hook_name="Stop",
            event_type="session_ended",
            data={"session_id": session_id, "total_operations": 3},
        )
        await communicator.broadcast_event(session_end_event)

        # Verify complete session evidence
        session_evidence = evidence_repo.get_session_evidence(session_id)

        assert len(session_evidence) == 3  # Three operations
        for evidence in session_evidence:
            assert evidence["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_cross_hook_validation_coordination(self, integrated_system):
        """Test coordination of validation between hooks."""
        communicator = integrated_system["communicator"]

        # Mock validation coordinators
        pre_validator = AsyncMock()
        post_validator = AsyncMock()

        communicator.register_handler("PreToolUse", pre_validator)
        communicator.register_handler("PostToolUse", post_validator)

        operation_id = "coordination_test_op"

        # PreToolUse requests enhanced validation
        validation_request = HookEvent(
            hook_name="PreToolUse",
            event_type="enhanced_validation_requested",
            data={
                "operation_id": operation_id,
                "validation_level": "high",
                "reason": "critical_file_modification",
            },
        )
        await communicator.broadcast_event(validation_request)

        # PostToolUse acknowledges and performs enhanced validation
        validation_response = HookEvent(
            hook_name="PostToolUse",
            event_type="enhanced_validation_completed",
            data={
                "operation_id": operation_id,
                "validation_result": {
                    "passed": True,
                    "confidence": 0.98,
                    "additional_checks": ["security_scan", "performance_analysis"],
                },
            },
        )
        await communicator.broadcast_event(validation_response)

        # Verify coordination
        pre_validator.assert_called_once()
        post_validator.assert_called_once()

        # Check that post_validator received the enhanced validation request
        post_call_args = post_validator.call_args[0][0]
        assert post_call_args.data.get("validation_level") == "high"

    @pytest.mark.asyncio
    async def test_evidence_aggregation_workflow(self, integrated_system):
        """Test evidence aggregation across hook lifecycle."""
        evidence_repo = integrated_system["evidence_repo"]

        operation_id = "aggregation_test_op"
        session_id = "aggregation_test_session"

        # Store evidence from different hooks
        evidence_items = [
            {
                "operation_id": operation_id,
                "hook_name": "UserPromptSubmit",
                "evidence_type": "request_analysis",
                "data": {"intent": "code_modification", "complexity": "medium"},
                "session_id": session_id,
            },
            {
                "operation_id": operation_id,
                "hook_name": "PreToolUse",
                "evidence_type": "pre_execution_check",
                "data": {"safety_check": "passed", "permissions": "ok"},
                "session_id": session_id,
            },
            {
                "operation_id": operation_id,
                "hook_name": "PostToolUse",
                "evidence_type": "execution_result",
                "data": {
                    "success": True,
                    "performance": "acceptable",
                    "files_modified": 1,
                },
                "session_id": session_id,
            },
        ]

        for evidence in evidence_items:
            evidence_repo.store_evidence(evidence)

        # Aggregate evidence for operation
        aggregated = evidence_repo.get_operation_evidence(operation_id)

        assert len(aggregated) == 3
        evidence_types = [e["evidence_type"] for e in aggregated]
        assert "request_analysis" in evidence_types
        assert "pre_execution_check" in evidence_types
        assert "execution_result" in evidence_types

        # Verify evidence completeness
        assert all(e["session_id"] == session_id for e in aggregated)
