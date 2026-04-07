"""Action Tracer for rca Flow-of-Action Paradigm.

Records investigation actions as a directed graph, enabling divergence detection
and visualization of the investigation path.

Author: CSF Development Team
Version: 1.0.0
Task: #986
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# State directory - use env var if set, matching session.py pattern
_CLAUDE_HOME = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
DEBUG_RCA_STATE_DIR = os.environ.get("DEBUG_RCA_STATE_DIR")
STATE_DIR = Path(DEBUG_RCA_STATE_DIR) if DEBUG_RCA_STATE_DIR else _CLAUDE_HOME / "state" / "rca"
ACTIONS_FILE = STATE_DIR / "rca_actions.json"


class ActionType(Enum):
    """Types of actions in RCA investigation.

    Categories:
    - Information gathering: Reading files, searching code
    - Analysis: Tracing symbols, inspecting state
    - Investigation: Forming and verifying hypotheses
    - External: Historical search, documentation lookup
    - Meta: Synthesis and recording
    """

    # Information gathering
    READ_FILE = "read_file"
    SEARCH_CODE = "search_code"
    LIST_DIR = "list_dir"

    # Analysis
    TRACE_SYMBOL = "trace_symbol"
    INSPECT_VARIABLE = "inspect_variable"
    EXECUTE_TEST = "execute_test"

    # Investigation
    FORM_HYPOTHESIS = "form_hypothesis"
    VERIFY_HYPOTHESIS = "verify_hypothesis"
    ELIMINATE_CAUSE = "eliminate_cause"

    # External
    SEARCH_HISTORY = "search_history"
    FETCH_DOCS = "fetch_docs"

    # Meta
    SYNTHESIZE = "synthesize"
    RECORD_OUTCOME = "record_outcome"

    # Unknown/Other
    UNKNOWN = "unknown"


@dataclass
class Action:
    """A single action in the RCA investigation graph.

    Attributes:
        action_id: Unique identifier for this action
        action_type: Type of action performed
        timestamp: When the action occurred
        tool_used: Tool name (Read, Grep, Bash, etc.)
        tool_input: Serialized tool input (truncated)
        tool_output_hash: Hash of full tool output (for storage optimization)
        tool_output_preview: First 1KB of tool output
        evidence_refs: IDs of evidence items produced
        parent_action_id: Previous action in sequence (None for first action)
        phase: RCA phase when action occurred (-1 to 6)
        session_id: RCA session identifier
        terminal_id: Terminal ID for multi-terminal safety
    """

    action_id: str
    action_type: ActionType
    timestamp: str
    tool_used: str
    tool_input: dict[str, Any]
    tool_output_hash: str
    tool_output_preview: str
    evidence_refs: list[str] = field(default_factory=list)
    parent_action_id: str | None = None
    phase: int = 0
    session_id: str = ""
    terminal_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "timestamp": self.timestamp,
            "tool_used": self.tool_used,
            "tool_input": self.tool_input,
            "tool_output_hash": self.tool_output_hash,
            "tool_output_preview": self.tool_output_preview,
            "evidence_refs": self.evidence_refs,
            "parent_id": self.parent_action_id,
            "phase": self.phase,
            "session_id": self.session_id,
            "terminal_id": self.terminal_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        """Create Action from dictionary."""
        return cls(
            action_id=data["action_id"],
            action_type=ActionType(data["action_type"]),
            timestamp=data["timestamp"],
            tool_used=data["tool_used"],
            tool_input=data["tool_input"],
            tool_output_hash=data["tool_output_hash"],
            tool_output_preview=data["tool_output_preview"],
            evidence_refs=data.get("evidence_refs", []),
            parent_action_id=data.get("parent_id"),
            phase=data.get("phase", 0),
            session_id=data.get("session_id", ""),
            terminal_id=data.get("terminal_id", ""),
        )


@dataclass
class ActionGraph:
    """Directed graph of actions in an RCA session.

    The graph represents the sequence of investigation actions taken,
    enabling divergence detection and visualization.

    Attributes:
        session_id: RCA session identifier
        actions: List of all actions in order
        divergence_point: Action where actual diverged from expected (if any)
        expected_path_type: Problem type used for expected path
        terminal_id: Terminal ID for multi-terminal safety
        created_at: When session started
        updated_at: When last action was recorded
    """

    session_id: str
    actions: list[Action] = field(default_factory=list)
    divergence_point: Action | None = None
    expected_path_type: str | None = None
    terminal_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "actions": [a.to_dict() for a in self.actions],
            "divergence_point": self.divergence_point.to_dict() if self.divergence_point else None,
            "expected_path": self.expected_path_type,
            "terminal_id": self.terminal_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionGraph":
        """Create ActionGraph from dictionary."""
        actions = [Action.from_dict(a) for a in data.get("actions", [])]

        divergence_data = data.get("divergence_point")
        divergence = Action.from_dict(divergence_data) if divergence_data else None

        return cls(
            session_id=data["session_id"],
            actions=actions,
            divergence_point=divergence,
            expected_path_type=data.get("expected_path"),
            terminal_id=data.get("terminal_id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def classify_action(tool_name: str, tool_input: dict[str, Any], tool_output: str) -> ActionType:
    """Classify a tool invocation as an ActionType.

    Uses heuristic pattern matching on tool name and input/output content.

    Args:
        tool_name: Name of the tool used (Read, Grep, Bash, etc.)
        tool_input: Serialized tool input parameters
        tool_output: Tool output content

    Returns:
        Classified ActionType

    Examples:
        >>> classify_action("Read", {"file_path": "test.py"}, "")
        ActionType.READ_FILE
        >>> classify_action("Skill", {"skill": "search"}, "")
        ActionType.SEARCH_HISTORY
    """
    tool_lower = tool_name.lower()
    input_str = json.dumps(tool_input, default=str).lower()
    output_str = tool_output.lower() if tool_output else ""

    # Check for Serena MCP symbolic tools (code navigation = data flow tracing)
    if "serena" in tool_lower:
        if "find_referencing" in tool_lower or "referencing" in input_str:
            return ActionType.TRACE_SYMBOL
        if "find_symbol" in tool_lower or "symbol" in input_str:
            return ActionType.SEARCH_CODE
        if "symbols_overview" in tool_lower:
            return ActionType.SEARCH_CODE
        return ActionType.SEARCH_CODE

    # Check for search tools
    if tool_lower in ("grep", "search"):
        return ActionType.SEARCH_CODE

    # Check for file reading
    if tool_lower == "read":
        return ActionType.READ_FILE

    # Check for directory listing
    if tool_lower in ("list", "glob", "ls"):
        return ActionType.LIST_DIR

    # Check for execution (tests, commands)
    if tool_lower == "bash":
        cmd = tool_input.get("command", "")
        if isinstance(cmd, str):
            if any(t in cmd.lower() for t in ("pytest", "test", "unittest")):
                return ActionType.EXECUTE_TEST
            if any(t in cmd.lower() for t in ("python", "node", "cargo")):
                return ActionType.EXECUTE_TEST
        return ActionType.EXECUTE_TEST  # Default Bash to test execution

    # Check for research/history tools
    if tool_lower == "skill":
        skill = tool_input.get("skill", "") or tool_input.get("skill_name", "")
        if isinstance(skill, str):
            if any(s in skill.lower() for s in ("search", "progressive", "cks", "chs")):
                return ActionType.SEARCH_HISTORY
            if any(s in skill.lower() for s in ("context7", "webfetch", "websearch")):
                return ActionType.FETCH_DOCS

    # Check for WebSearch/WebFetch directly
    if tool_lower in ("websearch", "webfetch"):
        return ActionType.FETCH_DOCS

    # Check for MCP research tools
    if "web_reader" in tool_lower or "web-search" in tool_lower:
        return ActionType.FETCH_DOCS

    if "context7" in tool_lower:
        return ActionType.FETCH_DOCS

    if "claude-mem" in tool_lower:
        return ActionType.SEARCH_HISTORY

    # Check for Task delegation
    if tool_lower == "task":
        return ActionType.VERIFY_HYPOTHESIS

    # Check for synthesis indicators in output
    if any(p in output_str for p in ("synthesis", "checkpoint", "findings gathered")):
        return ActionType.SYNTHESIZE

    if any(p in output_str for p in ("record outcome", "rca record")):
        return ActionType.RECORD_OUTCOME

    # Check for hypothesis formation in output
    if any(p in output_str for p in ("hypothesis:", "possible cause:", "root cause:")):
        return ActionType.FORM_HYPOTHESIS

    return ActionType.UNKNOWN


def hash_output(output: str) -> str:
    """Create a hash identifier for tool output.

    Uses a simple hash function for output identification.
    Full output is not stored to save space.

    Args:
        output: The tool output string

    Returns:
        Hex hash string
    """
    # Simple hash: use first/last 32 chars + length
    # This is enough for deduplication without expensive hashing
    if not output:
        return "empty"

    preview = output[:32] + output[-32:] if len(output) > 64 else output
    return f"{len(output)}:{preview}"


class ActionTracer:
    """Records and manages actions during RCA investigation.

    The tracer builds a directed graph of investigation actions,
    enabling divergence detection and flow visualization.

    Usage:
        >>> tracer = ActionTracer(session_id="rca_123", terminal_id="term_abc")
        >>> action = tracer.record_action(
        ...     action_type=ActionType.READ_FILE,
        ...     tool_used="Read",
        ...     tool_input={"file_path": "test.py"},
        ...     tool_output="# Test file\\n...",
        ...     phase=1,
        ... )
        >>> graph = tracer.get_action_graph()
        >>> tracer.save()  # Persist to disk
    """

    def __init__(
        self,
        session_id: str = "",
        terminal_id: str = "",
        state_dir: Path | None = None,
    ):
        """Initialize the ActionTracer.

        Args:
            session_id: RCA session identifier
            terminal_id: Terminal ID for multi-terminal safety
            state_dir: Custom state directory (default: ~/.claude/state/rca)
        """
        self.session_id = session_id
        self.terminal_id = terminal_id
        self._state_dir = Path(state_dir) if state_dir else STATE_DIR
        self._actions_file = self._state_dir / f"actions_{session_id}.json" if session_id else ACTIONS_FILE

        # Load existing graph or create new
        self._graph = self._load_or_create_graph()

    def _load_or_create_graph(self) -> ActionGraph:
        """Load existing graph from disk or create new one."""
        if self._actions_file.exists():
            try:
                data = json.loads(self._actions_file.read_text(encoding="utf-8"))
                # Verify it belongs to this terminal
                if data.get("terminal_id") == self.terminal_id:
                    return ActionGraph.from_dict(data)
            except (json.JSONDecodeError, IOError):
                pass

        # Create new graph
        now = datetime.now().isoformat()
        return ActionGraph(
            session_id=self.session_id,
            terminal_id=self.terminal_id,
            created_at=now,
            updated_at=now,
        )

    def record_action(
        self,
        action_type: ActionType,
        tool_used: str,
        tool_input: dict[str, Any],
        tool_output: str,
        phase: int,
    ) -> Action:
        """Record a new action and return it.

        Args:
            action_type: Type of action performed
            tool_used: Tool name (Read, Grep, Bash, etc.)
            tool_input: Serialized tool input parameters
            tool_output: Tool output content
            phase: RCA phase when action occurred (-1 to 6)

        Returns:
            The created Action object
        """
        now = datetime.now().isoformat()

        # Create action
        action = Action(
            action_id=f"act_{uuid.uuid4().hex[:8]}",
            action_type=action_type,
            timestamp=now,
            tool_used=tool_used,
            tool_input=self._sanitize_input(tool_input),
            tool_output_hash=hash_output(tool_output),
            tool_output_preview=tool_output[:1024],  # First 1KB
            parent_action_id=self._graph.actions[-1].action_id if self._graph.actions else None,
            phase=phase,
            session_id=self.session_id,
            terminal_id=self.terminal_id,
        )

        # Add to graph
        self._graph.actions.append(action)
        self._graph.updated_at = now

        return action

    def _sanitize_input(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Sanitize tool input for storage.

        Removes or truncates sensitive/large fields.

        Args:
            tool_input: Raw tool input

        Returns:
            Sanitized input dict
        """
        sanitized = {}
        for key, value in tool_input.items():
            # Convert to string if not already
            value_str = str(value)

            # Truncate long values
            if len(value_str) > 500:
                sanitized[key] = value_str[:500] + "... (truncated)"
            else:
                sanitized[key] = value

        return sanitized

    def get_action_graph(self) -> ActionGraph:
        """Get the complete action graph for this session.

        Returns:
            The ActionGraph containing all recorded actions
        """
        return self._graph

    def get_actions_by_phase(self, phase: int) -> list[Action]:
        """Get all actions from a specific phase.

        Args:
            phase: Phase number (-1 to 6)

        Returns:
            List of actions in the phase
        """
        return [a for a in self._graph.actions if a.phase == phase]

    def get_actions_by_type(self, action_type: ActionType) -> list[Action]:
        """Get all actions of a specific type.

        Args:
            action_type: The ActionType to filter by

        Returns:
            List of actions of that type
        """
        return [a for a in self._graph.actions if a.action_type == action_type]

    def find_divergence_point(
        self,
        expected_path: list[ActionType],
    ) -> Action | None:
        """Find where actual execution diverged from expected path.

        Compares the sequence of action types against an expected path
        and identifies the first divergence point.

        Args:
            expected_path: List of expected ActionTypes in order

        Returns:
            The Action where divergence occurred, or None if no divergence
        """
        # Get actual action types
        actual_types = [a.action_type for a in self._graph.actions]

        # Find first mismatch
        for i, (expected, actual) in enumerate(zip(expected_path, actual_types)):
            if expected != actual:
                # Found divergence
                if i < len(self._graph.actions):
                    diverging_action = self._graph.actions[i]
                    self._graph.divergence_point = diverging_action
                    return diverging_action

        # Check if actual is shorter than expected
        if len(actual_types) < len(expected_path):
            if self._graph.actions:
                # Divergence is ending early
                return self._graph.actions[-1]

        # No divergence found
        self._graph.divergence_point = None
        return None

    def get_action_sequence(self) -> list[ActionType]:
        """Get the sequence of action types in order.

        Returns:
            List of ActionTypes representing the investigation path
        """
        return [a.action_type for a in self._graph.actions]

    def save(self) -> None:
        """Persist the action graph to disk."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._actions_file.write_text(
            json.dumps(self._graph.to_dict(), indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        session_id: str,
        terminal_id: str = "",
        state_dir: Path | None = None,
    ) -> "ActionTracer":
        """Load an existing ActionTracer from disk.

        Args:
            session_id: RCA session identifier
            terminal_id: Terminal ID for verification
            state_dir: Custom state directory

        Returns:
            Loaded ActionTracer instance
        """
        tracer = cls(session_id=session_id, terminal_id=terminal_id, state_dir=state_dir)
        return tracer


def create_tracer_for_session(
    session_id: str,
    terminal_id: str = "",
) -> ActionTracer:
    """Convenience function to create an ActionTracer.

    Args:
        session_id: RCA session identifier
        terminal_id: Terminal ID (from CLAUDE_TERMINAL_ID env var)

    Returns:
        Configured ActionTracer instance
    """
    return ActionTracer(session_id=session_id, terminal_id=terminal_id)


# Expected investigation paths for each problem type
EXPECTED_PATHS = {
    "error": [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.TRACE_SYMBOL,
        ActionType.FORM_HYPOTHESIS,
        ActionType.VERIFY_HYPOTHESIS,
    ],
    "test": [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.EXECUTE_TEST,
        ActionType.INSPECT_VARIABLE,
        ActionType.FORM_HYPOTHESIS,
    ],
    "crash": [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.TRACE_SYMBOL,
        ActionType.SEARCH_CODE,
        ActionType.FORM_HYPOTHESIS,
    ],
    "performance": [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.INSPECT_VARIABLE,
        ActionType.SEARCH_CODE,
        ActionType.FORM_HYPOTHESIS,
    ],
    "behavior": [
        ActionType.SEARCH_HISTORY,
        ActionType.READ_FILE,
        ActionType.TRACE_SYMBOL,
        ActionType.FORM_HYPOTHESIS,
        ActionType.VERIFY_HYPOTHESIS,
    ],
}


def get_expected_path(problem_type: str) -> list[ActionType]:
    """Get the expected investigation path for a problem type.

    Args:
        problem_type: Problem type string (error, test, crash, etc.)

    Returns:
        List of expected ActionTypes
    """
    return EXPECTED_PATHS.get(problem_type.lower(), EXPECTED_PATHS["error"])
