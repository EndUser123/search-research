#!/usr/bin/env python3
"""
Tests for Full State Verifier - Source→Logic→Read verification protocol.

Tests verify that:
1. Source definition correctly characterizes state sources
2. Logic execution verification detects operation completion
3. Separate read operation retrieves actual state
4. State comparison detects mismatches accurately
5. Convenience functions work for common scenarios
"""

import json
import tempfile
from pathlib import Path

from tiers.full_state_verifier import (
    FullStateVerifier,
    SourceDefinition,
    StateVerificationResult,
    verify_file_written,
    verify_state_transition,
)


class TestSourceDefinition:
    """Test SourceDefinition dataclass."""

    def test_source_definition_creation(self):
        """Test creating SourceDefinition with all fields."""
        source_def = SourceDefinition(
            source_type="file",
            location="/path/to/file.txt",
            exists=True,
            readable=True,
            writable=True,
            metadata={"size_bytes": 1024},
        )

        assert source_def.source_type == "file"
        assert source_def.location == "/path/to/file.txt"
        assert source_def.exists is True
        assert source_def.readable is True
        assert source_def.writable is True
        assert source_def.metadata["size_bytes"] == 1024

    def test_source_definition_with_empty_metadata(self):
        """Test SourceDefinition with default empty metadata."""
        source_def = SourceDefinition(
            source_type="directory",
            location="/path/to/dir",
            exists=False,
            readable=False,
            writable=False,
            metadata={},
        )

        assert source_def.metadata == {}


class TestStateVerificationResult:
    """Test StateVerificationResult dataclass."""

    def test_verification_result_creation_pass(self):
        """Test creating passing StateVerificationResult."""
        result = StateVerificationResult(
            status="pass",
            target_type="file",
            target_name="test.txt",
            source_definition=SourceDefinition(
                source_type="file",
                location="/test.txt",
                exists=True,
                readable=True,
                writable=True,
                metadata={},
            ),
            logic_verification={"verified": True},
            expected_state={"exists": True},
            actual_state={"exists": True},
            state_match=True,
            differences=[],
            timestamp="2026-03-17T12:00:00",
        )

        assert result.status == "pass"
        assert result.state_match is True
        assert len(result.differences) == 0

    def test_verification_result_creation_fail(self):
        """Test creating failing StateVerificationResult."""
        result = StateVerificationResult(
            status="fail",
            target_type="file",
            target_name="test.txt",
            source_definition=SourceDefinition(
                source_type="file",
                location="/test.txt",
                exists=False,
                readable=False,
                writable=False,
                metadata={},
            ),
            logic_verification={"verified": False},
            expected_state={"exists": True},
            actual_state={"exists": False},
            state_match=False,
            differences=["Existence mismatch: expected=True, actual=False"],
            timestamp="2026-03-17T12:00:00",
        )

        assert result.status == "fail"
        assert result.state_match is False
        assert len(result.differences) == 1


class TestFullStateVerifierInitialization:
    """Test FullStateVerifier initialization and basic setup."""

    def test_verifier_initialization(self):
        """Test verifier initializes with empty history."""
        verifier = FullStateVerifier()

        assert verifier.get_verification_history() == []

    def test_clear_history(self):
        """Test clearing verification history."""
        verifier = FullStateVerifier()

        # Add a mock result to history
        result = StateVerificationResult(
            status="pass",
            target_type="file",
            target_name="test",
            source_definition=SourceDefinition(
                source_type="file",
                location="",
                exists=False,
                readable=False,
                writable=False,
                metadata={},
            ),
            logic_verification={},
            expected_state={},
            actual_state={},
            state_match=True,
            differences=[],
            timestamp="2026-03-17T12:00:00",
        )
        verifier._verification_history.append(result)

        assert len(verifier.get_verification_history()) == 1

        verifier.clear_history()

        assert verifier.get_verification_history() == []


class TestDefineSource:
    """Test source definition characterization."""

    def test_define_source_existing_file(self):
        """Test defining an existing file source."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            source_def = verifier._define_source(temp_path)

            assert source_def.source_type == "file"
            assert source_def.exists is True
            assert source_def.readable is True
            assert source_def.location == temp_path
            assert "size_bytes" in source_def.metadata
        finally:
            Path(temp_path).unlink()

    def test_define_source_nonexistent_file(self):
        """Test defining a non-existent file source."""
        verifier = FullStateVerifier()

        source_def = verifier._define_source("/nonexistent/path/file.txt")

        assert source_def.exists is False
        assert source_def.readable is False
        # Should still identify as file type due to no trailing slash
        assert source_def.source_type in ("file", "unknown")

    def test_define_source_existing_directory(self):
        """Test defining an existing directory source."""
        verifier = FullStateVerifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_def = verifier._define_source(tmpdir)

            assert source_def.source_type == "directory"
            assert source_def.exists is True
            assert source_def.readable is True
            assert "entry_count" in source_def.metadata

    def test_define_source_nonexistent_directory(self):
        """Test defining a non-existent directory source."""
        verifier = FullStateVerifier()

        source_def = verifier._define_source("/nonexistent/directory/")

        assert source_def.exists is False
        assert source_def.readable is False


class TestVerifyLogicExecuted:
    """Test logic execution verification."""

    def test_verify_write_operation_success(self):
        """Test verifying successful write operation."""
        verifier = FullStateVerifier()

        source_def = SourceDefinition(
            source_type="file",
            location="/test.txt",
            exists=True,
            readable=True,
            writable=True,
            metadata={},
        )

        result = verifier._verify_logic_executed("write file", source_def)

        assert result["verified"] is True
        assert "exists after write" in result["details"][0]

    def test_verify_write_operation_failure(self):
        """Test verifying failed write operation."""
        verifier = FullStateVerifier()

        source_def = SourceDefinition(
            source_type="file",
            location="/test.txt",
            exists=False,
            readable=False,
            writable=False,
            metadata={},
        )

        result = verifier._verify_logic_executed("write file", source_def)

        assert result["verified"] is False
        assert "does not exist" in result["details"][0]

    def test_verify_edit_operation_success(self):
        """Test verifying successful edit operation."""
        verifier = FullStateVerifier()

        source_def = SourceDefinition(
            source_type="file",
            location="/test.txt",
            exists=True,
            readable=True,
            writable=True,
            metadata={},
        )

        result = verifier._verify_logic_executed("edit file", source_def)

        assert result["verified"] is True
        assert "readable" in result["details"][0]

    def test_verify_delete_operation_success(self):
        """Test verifying successful delete operation."""
        verifier = FullStateVerifier()

        source_def = SourceDefinition(
            source_type="file",
            location="/test.txt",
            exists=False,
            readable=False,
            writable=False,
            metadata={},
        )

        result = verifier._verify_logic_executed("delete file", source_def)

        assert result["verified"] is True
        assert "removed" in result["details"][0]


class TestReadActualState:
    """Test separate read operation for actual state."""

    def test_read_actual_state_text_file(self):
        """Test reading actual state from text file."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content for verification")
            temp_path = f.name

        try:
            source_def = SourceDefinition(
                source_type="file",
                location=temp_path,
                exists=True,
                readable=True,
                writable=True,
                metadata={},
            )

            actual_state = verifier._read_actual_state(temp_path, source_def)

            assert actual_state["exists"] is True
            assert actual_state["source_type"] == "file"
            assert actual_state["data"] == "test content for verification"
            assert actual_state["format"] == "text"
            assert actual_state["error"] is None
        finally:
            Path(temp_path).unlink()

    def test_read_actual_state_json_file(self):
        """Test reading actual state from JSON file."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"key": "value", "number": 42}, f)
            temp_path = f.name

        try:
            source_def = SourceDefinition(
                source_type="file",
                location=temp_path,
                exists=True,
                readable=True,
                writable=True,
                metadata={},
            )

            actual_state = verifier._read_actual_state(temp_path, source_def)

            assert actual_state["exists"] is True
            assert actual_state["format"] == "json"
            assert actual_state["data"]["key"] == "value"
            assert actual_state["data"]["number"] == 42
        finally:
            Path(temp_path).unlink()

    def test_read_actual_state_directory(self):
        """Test reading actual state from directory."""
        verifier = FullStateVerifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files in directory
            Path(tmpdir, "file1.txt").touch()
            Path(tmpdir, "file2.txt").touch()

            source_def = SourceDefinition(
                source_type="directory",
                location=tmpdir,
                exists=True,
                readable=True,
                writable=True,
                metadata={},
            )

            actual_state = verifier._read_actual_state(tmpdir, source_def)

            assert actual_state["exists"] is True
            assert actual_state["source_type"] == "directory"
            assert actual_state["data"]["entry_count"] == 2
            assert "file1.txt" in actual_state["data"]["entries"]
            assert "file2.txt" in actual_state["data"]["entries"]

    def test_read_actual_state_nonexistent(self):
        """Test reading actual state from non-existent source."""
        verifier = FullStateVerifier()

        source_def = SourceDefinition(
            source_type="file",
            location="/nonexistent/file.txt",
            exists=False,
            readable=False,
            writable=False,
            metadata={},
        )

        actual_state = verifier._read_actual_state("/nonexistent/file.txt", source_def)

        assert actual_state["exists"] is False
        assert "does not exist" in actual_state["error"]


class TestCompareStates:
    """Test expected vs actual state comparison."""

    def test_compare_states_match(self):
        """Test comparing matching states."""
        verifier = FullStateVerifier()

        expected = {"exists": True, "key": "value"}
        actual = {"exists": True, "key": "value", "data": "content"}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is True
        assert len(differences) == 0

    def test_compare_states_mismatch_exists(self):
        """Test comparing states with existence mismatch."""
        verifier = FullStateVerifier()

        expected = {"exists": True}
        actual = {"exists": False}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is False
        assert any("Existence mismatch" in d for d in differences)

    def test_compare_states_key_mismatch(self):
        """Test comparing states with key value mismatch."""
        verifier = FullStateVerifier()

        expected = {"key1": "value1", "key2": "value2"}
        actual = {"key1": "value1", "key2": "different"}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is False
        assert any("key2" in d for d in differences)

    def test_compare_states_missing_key(self):
        """Test comparing states with missing key in actual."""
        verifier = FullStateVerifier()

        expected = {"key1": "value1", "key2": "value2"}
        actual = {"key1": "value1"}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is False
        assert any("key2" in d for d in differences)

    def test_compare_states_with_comparison_keys(self):
        """Test comparing states with specific keys only."""
        verifier = FullStateVerifier()

        expected = {"key1": "value1", "key2": "value2", "key3": "value3"}
        actual = {"key1": "value1", "key2": "WRONG", "key3": "value3"}

        # Only compare key1 and key3
        state_match, differences = verifier._compare_states(
            expected, actual, comparison_keys=["key1", "key3"]
        )

        assert state_match is True
        assert len(differences) == 0

    def test_compare_states_content_string_match(self):
        """Test comparing string content in expected state."""
        verifier = FullStateVerifier()

        expected = {"exists": True, "content": "expected text"}
        actual = {"exists": True, "data": "this contains expected text here"}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is True

    def test_compare_states_content_string_mismatch(self):
        """Test comparing string content with mismatch."""
        verifier = FullStateVerifier()

        expected = {"exists": True, "content": "needle"}
        actual = {"exists": True, "data": "this does not contain it"}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is False
        assert any("Content mismatch" in d for d in differences)

    def test_compare_states_content_dict_match(self):
        """Test comparing dict content in expected state."""
        verifier = FullStateVerifier()

        expected = {"exists": True, "content": {"key1": "value1"}}
        actual = {"exists": True, "data": {"key1": "value1", "key2": "value2"}}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is True

    def test_compare_states_content_dict_mismatch(self):
        """Test comparing dict content with mismatch."""
        verifier = FullStateVerifier()

        expected = {"exists": True, "content": {"key1": "value1"}}
        actual = {"exists": True, "data": {"key1": "WRONG"}}

        state_match, differences = verifier._compare_states(expected, actual)

        assert state_match is False
        assert any("key1" in d for d in differences)


class TestVerifyFullPath:
    """Test full verify_full_state method."""

    def test_verify_full_state_file_exists_pass(self):
        """Test full verification of existing file."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = verifier.verify_full_state(
                target_type="file",
                target_name="test.txt",
                state_source=temp_path,
                logic_operation="write",
                expected_state={"exists": True},
            )

            assert result.status == "pass"
            assert result.state_match is True
            assert len(result.differences) == 0
            assert result.source_definition.exists is True
        finally:
            Path(temp_path).unlink()

    def test_verify_full_state_file_not_exists_fail(self):
        """Test full verification of non-existent file."""
        verifier = FullStateVerifier()

        result = verifier.verify_full_state(
            target_type="file",
            target_name="missing.txt",
            state_source="/nonexistent/missing.txt",
            logic_operation="write",
            expected_state={"exists": True},
        )

        assert result.status == "fail"
        assert result.state_match is False
        assert len(result.differences) > 0

    def test_verify_full_state_with_content_check(self):
        """Test full verification with content check."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("specific content here")
            temp_path = f.name

        try:
            result = verifier.verify_full_state(
                target_type="file",
                target_name="test.txt",
                state_source=temp_path,
                logic_operation="write",
                expected_state={"exists": True, "content": "specific content"},
            )

            assert result.status == "pass"
            assert result.state_match is True
        finally:
            Path(temp_path).unlink()

    def test_verify_full_state_tracks_history(self):
        """Test that verifications are tracked in history."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            verifier.verify_full_state(
                target_type="file",
                target_name="test.txt",
                state_source=temp_path,
                logic_operation="write",
                expected_state={"exists": True},
            )

            history = verifier.get_verification_history()

            assert len(history) == 1
            assert history[0].target_name == "test.txt"
        finally:
            Path(temp_path).unlink()


class TestConvenienceMethods:
    """Test convenience verification methods."""

    def test_verify_file_exists_pass(self):
        """Test verify_file_exists with existing file."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            result = verifier.verify_file_exists(temp_path, "test.txt")

            assert result.status == "pass"
            assert result.state_match is True
        finally:
            Path(temp_path).unlink()

    def test_verify_file_exists_fail(self):
        """Test verify_file_exists with non-existent file."""
        verifier = FullStateVerifier()

        result = verifier.verify_file_exists("/nonexistent/file.txt", "missing.txt")

        assert result.status == "fail"
        assert result.state_match is False

    def test_verify_file_content_pass(self):
        """Test verify_file_content with matching content."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("expected content string")
            temp_path = f.name

        try:
            result = verifier.verify_file_content(temp_path, "expected content", "test.txt")

            assert result.status == "pass"
            assert result.state_match is True
        finally:
            Path(temp_path).unlink()

    def test_verify_file_content_fail(self):
        """Test verify_file_content with non-matching content."""
        verifier = FullStateVerifier()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("different content")
            temp_path = f.name

        try:
            result = verifier.verify_file_content(temp_path, "expected content", "test.txt")

            assert result.status == "fail"
            assert result.state_match is False
        finally:
            Path(temp_path).unlink()

    def test_verify_directory_exists_pass(self):
        """Test verify_directory_exists with existing directory."""
        verifier = FullStateVerifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = verifier.verify_directory_exists(tmpdir, "test_dir")

            assert result.status == "pass"
            assert result.state_match is True

    def test_verify_directory_exists_fail(self):
        """Test verify_directory_exists with non-existent directory."""
        verifier = FullStateVerifier()

        result = verifier.verify_directory_exists("/nonexistent/dir", "missing_dir")

        assert result.status == "fail"
        assert result.state_match is False


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_verify_file_written_function(self):
        """Test verify_file_written convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            result = verify_file_written(temp_path)

            assert result.status == "pass"
            assert result.state_match is True
        finally:
            Path(temp_path).unlink()

    def test_verify_file_written_with_content(self):
        """Test verify_file_written with content check."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("specific content here")
            temp_path = f.name

        try:
            result = verify_file_written(temp_path, "specific content")

            assert result.status == "pass"
            assert result.state_match is True
        finally:
            Path(temp_path).unlink()

    def test_verify_state_transition_function(self):
        """Test verify_state_transition convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            result = verify_state_transition(temp_path, {"exists": True, "content": "test"})

            assert result.status == "pass"
            assert result.target_type == "state"
        finally:
            Path(temp_path).unlink()


class TestErrorHandling:
    """Test error handling in FullStateVerifier."""

    def test_verify_full_state_error_on_invalid_path(self):
        """Test error handling for invalid path."""
        verifier = FullStateVerifier()

        # Use None as invalid path to trigger error
        result = verifier.verify_full_state(
            target_type="file",
            target_name="test",
            state_source=None,  # Invalid path
            logic_operation="write",
            expected_state={"exists": True},
        )

        assert result.status == "error"
        assert result.error_message is not None
        assert result.state_match is False
