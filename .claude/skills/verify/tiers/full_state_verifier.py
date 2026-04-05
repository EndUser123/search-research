#!/usr/bin/env python3
"""
Full State Verifier - Source→Logic→Read verification protocol.

Implements comprehensive state verification using the "Source of Truth →
Run Logic → Separate Read Operation" methodology to detect state mismatches,
stale data, and write failures.

The Full State Verification protocol prevents:
- Assuming state was written correctly without verification
- Caching stale data instead of reading fresh state
- Silent write failures (permission errors, disk full, etc.)
- Race conditions between write and read operations
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


@dataclass
class SourceDefinition:
    """Definition of a state source with its properties."""

    source_type: Literal["file", "directory", "database", "api", "memory"]
    location: str
    exists: bool
    readable: bool
    writable: bool
    metadata: dict[str, Any]


@dataclass
class StateVerificationResult:
    """Result of full state verification."""

    status: Literal["pass", "fail", "error"]
    target_type: str
    target_name: str
    source_definition: SourceDefinition
    logic_verification: dict[str, Any]
    expected_state: dict[str, Any]
    actual_state: dict[str, Any]
    state_match: bool
    differences: list[str]
    timestamp: str
    error_message: str | None = None


class FullStateVerifier:
    """
    Verifier for Source→Logic→Read state verification protocol.

    Protocol:
    1. Define Source of Truth - Identify and characterize the state source
    2. Run Logic - Verify the logic operation executed (already happened)
    3. Separate Read Operation - Read actual state independently
    4. Compare Expected vs Actual - Detect mismatches and differences

    Use Cases:
    - Verifying file writes created expected content
    - Confirming state changes applied correctly
    - Detecting silent write failures
    - Validating cache invalidation
    - Checking multi-terminal state isolation
    """

    def __init__(self):
        """Initialize the full state verifier."""
        self._verification_history: list[StateVerificationResult] = []

    def verify_full_state(
        self,
        target_type: str,
        target_name: str,
        state_source: str | Path,
        logic_operation: str,
        expected_state: dict[str, Any],
        comparison_keys: list[str] | None = None,
    ) -> StateVerificationResult:
        """
        Verify full state: define source → run logic → separate read.

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target being verified
            state_source: Source of truth (file path, directory path, etc.)
            logic_operation: Operation performed (write, edit, delete, update)
            expected_state: Expected state after operation
            comparison_keys: Optional list of specific keys to compare
                           (if None, compares entire state dict)

        Returns:
            StateVerificationResult with detailed verification status
        """
        timestamp = datetime.now().isoformat()

        try:
            # Step 1: Define Source of Truth
            source_definition = self._define_source(state_source)

            # Step 2: Verify Logic Executed
            logic_verification = self._verify_logic_executed(logic_operation, source_definition)

            # Step 3: Separate Read Operation
            actual_state = self._read_actual_state(state_source, source_definition)

            # Step 4: Compare Expected vs Actual
            state_match, differences = self._compare_states(
                expected_state, actual_state, comparison_keys
            )

            result = StateVerificationResult(
                status="pass" if state_match else "fail",
                target_type=target_type,
                target_name=target_name,
                source_definition=source_definition,
                logic_verification=logic_verification,
                expected_state=expected_state,
                actual_state=actual_state,
                state_match=state_match,
                differences=differences,
                timestamp=timestamp,
            )

            # Store in history
            self._verification_history.append(result)

            return result

        except Exception as e:
            # Return error result
            return StateVerificationResult(
                status="error",
                target_type=target_type,
                target_name=target_name,
                source_definition=SourceDefinition(
                    source_type="unknown",
                    location=str(state_source),
                    exists=False,
                    readable=False,
                    writable=False,
                    metadata={},
                ),
                logic_verification={},
                expected_state=expected_state,
                actual_state={},
                state_match=False,
                differences=[f"Verification error: {str(e)}"],
                timestamp=timestamp,
                error_message=str(e),
            )

    def _define_source(self, state_source: str | Path) -> SourceDefinition:
        """
        Define and characterize the state source.

        Args:
            state_source: Path or identifier of the state source

        Returns:
            SourceDefinition with source properties
        """
        source_path = Path(state_source)

        # Determine source type
        if source_path.is_file():
            source_type = "file"
        elif source_path.is_dir():
            source_type = "directory"
        elif source_path.parent.exists():
            # Parent exists but source doesn't - likely a file that doesn't exist yet
            source_type = "file"
        else:
            source_type = "unknown"

        # Check existence
        exists = source_path.exists()

        # Check readability
        readable = False
        if exists:
            try:
                if source_type == "file":
                    readable = source_path.is_file()
                elif source_type == "directory":
                    readable = source_path.is_dir()
            except Exception:
                readable = False

        # Check writability
        writable = False
        try:
            if exists:
                writable = os.access(source_path, os.W_OK)
            elif source_type == "file":
                # For non-existent files, check parent dir writability
                writable = os.access(source_path.parent, os.W_OK)
        except Exception:
            writable = False

        # Gather metadata
        metadata = {}
        if exists and source_type == "file":
            try:
                metadata["size_bytes"] = source_path.stat().st_size
                metadata["modified_time"] = source_path.stat().st_mtime
            except Exception:
                pass
        elif exists and source_type == "directory":
            try:
                metadata["entry_count"] = len(list(source_path.iterdir()))
            except Exception:
                pass

        return SourceDefinition(
            source_type=source_type,
            location=str(source_path),
            exists=exists,
            readable=readable,
            writable=writable,
            metadata=metadata,
        )

    def _verify_logic_executed(
        self, logic_operation: str, source_definition: SourceDefinition
    ) -> dict[str, Any]:
        """
        Verify that the logic operation executed successfully.

        Args:
            logic_operation: Description of operation performed
            source_definition: Characterized source information

        Returns:
            Dict with verification status and details
        """
        verification = {"operation": logic_operation, "verified": False, "details": []}

        # For write operations, check if source exists now
        if "write" in logic_operation.lower() or "create" in logic_operation.lower():
            if source_definition.exists:
                verification["verified"] = True
                verification["details"].append("Source exists after write operation")
            else:
                verification["details"].append("Source does not exist after write operation")

        # For edit operations, check if source is readable
        elif "edit" in logic_operation.lower() or "update" in logic_operation.lower():
            if source_definition.readable:
                verification["verified"] = True
                verification["details"].append("Source is readable after edit operation")
            else:
                verification["details"].append("Source is not readable after edit operation")

        # For delete operations, check if source doesn't exist
        elif "delete" in logic_operation.lower() or "remove" in logic_operation.lower():
            if not source_definition.exists:
                verification["verified"] = True
                verification["details"].append("Source removed successfully")
            else:
                verification["details"].append("Source still exists after delete operation")

        else:
            # Unknown operation type - assume verified
            verification["verified"] = True
            verification["details"].append(f"Unknown operation type: {logic_operation}")

        return verification

    def _read_actual_state(
        self, state_source: str | Path, source_definition: SourceDefinition
    ) -> dict[str, Any]:
        """
        Perform separate read operation to get actual state.

        Args:
            state_source: Path to the state source
            source_definition: Characterized source information

        Returns:
            Dict with actual state read from source
        """
        actual_state = {
            "source_type": source_definition.source_type,
            "location": source_definition.location,
            "exists": source_definition.exists,
            "data": None,
            "error": None,
        }

        source_path = Path(state_source)

        # Read based on source type
        if source_definition.source_type == "file" and source_definition.readable:
            try:
                with open(source_path, encoding="utf-8") as f:
                    content = f.read()

                # Try to parse as JSON
                try:
                    actual_state["data"] = json.loads(content)
                    actual_state["format"] = "json"
                except json.JSONDecodeError:
                    # Not JSON, store as text
                    actual_state["data"] = content
                    actual_state["format"] = "text"

                actual_state["size_bytes"] = len(content)

            except Exception as e:
                actual_state["error"] = f"Read error: {str(e)}"

        elif source_definition.source_type == "directory" and source_definition.readable:
            try:
                entries = list(source_path.iterdir())
                actual_state["data"] = {
                    "entry_count": len(entries),
                    "entries": [str(e.name) for e in entries],
                }
            except Exception as e:
                actual_state["error"] = f"Directory read error: {str(e)}"

        elif not source_definition.exists:
            actual_state["error"] = "Source does not exist"

        else:
            actual_state["error"] = (
                f"Source type {source_definition.source_type} not supported for reading"
            )

        return actual_state

    def _compare_states(
        self,
        expected_state: dict[str, Any],
        actual_state: dict[str, Any],
        comparison_keys: list[str] | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Compare expected vs actual state.

        Args:
            expected_state: State that was expected
            actual_state: State that was actually read
            comparison_keys: Optional list of keys to compare (if None, compare all)

        Returns:
            Tuple of (state_match: bool, differences: List[str])
        """
        differences = []

        # Check for errors in actual state
        if actual_state.get("error"):
            differences.append(f"Actual state has error: {actual_state['error']}")
            return False, differences

        # Determine which keys to compare
        if comparison_keys:
            keys_to_compare = comparison_keys
        else:
            # Compare all top-level keys in expected_state (except "content" which is handled separately)
            keys_to_compare = [k for k in expected_state.keys() if k not in ("exists", "content")]

            # Also check existence match when not using comparison_keys
            expected_exists = expected_state.get("exists", True)
            actual_exists = actual_state.get("exists", False)
            if expected_exists != actual_exists:
                differences.append(
                    f"Existence mismatch: expected={expected_exists}, actual={actual_exists}"
                )

            # If source doesn't exist and wasn't expected to, no further comparison
            if not actual_exists and not expected_exists:
                return len(differences) == 0, differences

        # Compare each key
        for key in keys_to_compare:
            expected_value = expected_state.get(key)
            actual_value = actual_state.get(key)

            if expected_value != actual_value:
                differences.append(
                    f"Key '{key}' mismatch: expected={expected_value}, actual={actual_value}"
                )

        # Check for actual data content if specified in expected
        if "content" in expected_state:
            expected_content = expected_state["content"]
            actual_content = actual_state.get("data")

            if isinstance(expected_content, str):
                # String comparison
                if isinstance(actual_content, str):
                    if expected_content not in actual_content:
                        differences.append(
                            f"Content mismatch: expected '{expected_content}' not found in actual"
                        )
                else:
                    differences.append(
                        f"Content type mismatch: expected str, got {type(actual_content).__name__}"
                    )

            elif isinstance(expected_content, dict):
                # Dict comparison
                if isinstance(actual_content, dict):
                    for sub_key, sub_value in expected_content.items():
                        if sub_key not in actual_content:
                            differences.append(f"Missing key in actual: {sub_key}")
                        elif actual_content[sub_key] != sub_value:
                            differences.append(
                                f"Dict key '{sub_key}' mismatch: "
                                f"expected={sub_value}, actual={actual_content.get(sub_key)}"
                            )
                else:
                    differences.append(
                        f"Content type mismatch: expected dict, got {type(actual_content).__name__}"
                    )

        state_match = len(differences) == 0
        return state_match, differences

    def verify_file_exists(
        self, file_path: str | Path, target_name: str = "file"
    ) -> StateVerificationResult:
        """
        Quick verification that a file exists.

        Args:
            file_path: Path to file to verify
            target_name: Name of target for reporting

        Returns:
            StateVerificationResult with existence check
        """
        return self.verify_full_state(
            target_type="file",
            target_name=target_name,
            state_source=file_path,
            logic_operation="create",
            expected_state={"exists": True},
            comparison_keys=["exists"],
        )

    def verify_file_content(
        self, file_path: str | Path, expected_content: str, target_name: str = "file"
    ) -> StateVerificationResult:
        """
        Verify a file exists and contains expected content.

        Args:
            file_path: Path to file to verify
            expected_content: Content that should be in the file
            target_name: Name of target for reporting

        Returns:
            StateVerificationResult with content verification
        """
        return self.verify_full_state(
            target_type="file",
            target_name=target_name,
            state_source=file_path,
            logic_operation="write",
            expected_state={"exists": True, "content": expected_content},
            comparison_keys=["exists"],
        )

    def verify_directory_exists(
        self, dir_path: str | Path, target_name: str = "directory"
    ) -> StateVerificationResult:
        """
        Quick verification that a directory exists.

        Args:
            dir_path: Path to directory to verify
            target_name: Name of target for reporting

        Returns:
            StateVerificationResult with existence check
        """
        return self.verify_full_state(
            target_type="directory",
            target_name=target_name,
            state_source=dir_path,
            logic_operation="create",
            expected_state={"exists": True},
            comparison_keys=["exists"],
        )

    def get_verification_history(self) -> list[StateVerificationResult]:
        """Get history of all verifications performed."""
        return self._verification_history.copy()

    def clear_history(self) -> None:
        """Clear verification history."""
        self._verification_history.clear()


# Convenience functions for common verification scenarios
def verify_file_written(
    file_path: str | Path, expected_content: str | None = None
) -> StateVerificationResult:
    """
    Verify that a file was written successfully.

    Args:
        file_path: Path to file that should exist
        expected_content: Optional content that should be in file

    Returns:
        StateVerificationResult with verification status
    """
    verifier = FullStateVerifier()

    if expected_content:
        return verifier.verify_file_content(file_path, expected_content)
    else:
        return verifier.verify_file_exists(file_path)


def verify_state_transition(
    state_source: str | Path, expected_state: dict[str, Any]
) -> StateVerificationResult:
    """
    Verify that a state transition completed successfully.

    Args:
        state_source: Path to state file or directory
        expected_state: Expected state after transition

    Returns:
        StateVerificationResult with verification status
    """
    verifier = FullStateVerifier()

    return verifier.verify_full_state(
        target_type="state",
        target_name=str(state_source),
        state_source=state_source,
        logic_operation="update",
        expected_state=expected_state,
    )
