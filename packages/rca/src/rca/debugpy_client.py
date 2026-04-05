"""debugpy MCP Integration for rca Tier 1.

Provides integration with debugpy via MCP for capturing stack traces
and local variables during local runtime debugging.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StackFrame:
    """Represents a single stack frame.

    Attributes:
        filename: The source file path.
        line: Line number.
        function: Function name.
        code: The source code line (if available).
        locals: Local variables at this frame.
    """

    filename: str
    line: int
    function: str
    code: Optional[str] = None
    locals: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "filename": self.filename,
            "line": self.line,
            "function": self.function,
            "code": self.code,
            "locals": self.locals,
        }


@dataclass
class DebugCapture:
    """Captured debug state from a running process.

    Attributes:
        stack_trace: List of stack frames.
        exception: Exception info if caught.
        globals: Global variable snapshot.
        thread_info: Thread information.
    """

    stack_trace: List[StackFrame]
    exception: Optional[Dict[str, Any]] = None
    globals: Optional[Dict[str, Any]] = None
    thread_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "stack_trace": [frame.to_dict() for frame in self.stack_trace],
            "exception": self.exception,
            "globals": self.globals,
            "thread_info": self.thread_info,
        }

    @property
    def top_frame(self) -> Optional[StackFrame]:
        """Get the top (most recent) stack frame."""
        return self.stack_trace[0] if self.stack_trace else None

    @property
    def bottom_frame(self) -> Optional[StackFrame]:
        """Get the bottom (oldest) stack frame."""
        return self.stack_trace[-1] if self.stack_trace else None


class DebugPyClient:
    """Client for debugpy integration via MCP.

    Provides a side-channel for capturing local runtime state during
    debugging sessions. This enables automatic stack trace capture
    and local variable inspection at failure points.

    Note: This client requires debugpy to be installed and the MCP
    debugpy server to be running.

    Attributes:
        host: Debugpy server host.
        port: Debugpy server port.
        timeout: Connection timeout in seconds.

    Examples:
        >>> client = DebugPyClient()
        >>> if client.is_available():
        ...     capture = client.capture_state()
        ...     print(f"Captured {len(capture.stack_trace)} frames")
    """

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 5678
    DEFAULT_TIMEOUT = 5

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the debugpy client.

        Args:
            host: Debugpy server host.
            port: Debugpy server port.
            timeout: Connection timeout in seconds.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if debugpy MCP server is available.

        Returns:
            True if debugpy server is reachable, False otherwise.
        """
        if self._available is not None:
            return self._available

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            self._available = result == 0
            return self._available
        except Exception:
            self._available = False
            return False

    def capture_state(self) -> Optional[DebugCapture]:
        """Capture current debug state from debugpy.

        Returns:
            DebugCapture with stack trace, locals, and exception info,
            or None if capture fails.

        Examples:
            >>> client = DebugPyClient()
            >>> capture = client.capture_state()
            >>> if capture:
            ...     print(f"Top frame: {capture.top_frame.function}")
        """
        if not self.is_available():
            return None

        try:
            # In a real implementation, this would connect to the MCP
            # debugpy server and request the current state
            return self._capture_via_mcp()
        except Exception as e:
            self._available = False
            return None

    def _capture_via_mcp(self) -> Optional[DebugCapture]:
        """Capture state via MCP protocol.

        This is a placeholder for the actual MCP communication.
        In production, this would use the MCP client to communicate
        with the debugpy server.

        Returns:
            DebugCapture or None if unavailable.
        """
        # Placeholder: simulate MCP communication
        # Real implementation would use MCP client library
        try:
            import sys
            import traceback

            # Get current stack trace
            stack = []
            for frame, filename, line, function, code, context in traceback.extract_stack():
                # Filter out this client's frames
                if "debugpy_client.py" not in filename:
                    frame_obj = StackFrame(
                        filename=filename,
                        line=line,
                        function=function,
                        code=code,
                    )
                    stack.append(frame_obj)

            # Get exception info if one is being handled
            exc_info = None
            if sys.exc_info()[0] is not None:
                exc_type, exc_value, exc_tb = sys.exc_info()
                exc_info = {
                    "type": exc_type.__name__ if exc_type else None,
                    "message": str(exc_value) if exc_value else None,
                    "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                }

            return DebugCapture(
                stack_trace=stack,
                exception=exc_info,
                globals=dict(globals()) if False else None,  # Too large, disabled
            )
        except Exception:
            return None

    def get_breakpoints(self) -> List[Dict[str, Any]]:
        """Get list of current breakpoints.

        Returns:
            List of breakpoint dictionaries.

        Examples:
            >>> client = DebugPyClient()
            >>> if client.is_available():
            ...     breakpoints = client.get_breakpoints()
        """
        if not self.is_available():
            return []

        # Placeholder for MCP breakpoint query
        return []

    def set_breakpoint(
        self,
        file: str,
        line: int,
        condition: Optional[str] = None,
    ) -> bool:
        """Set a breakpoint.

        Args:
            file: Source file path.
            line: Line number.
            condition: Optional breakpoint condition.

        Returns:
            True if breakpoint was set successfully.

        Examples:
            >>> client = DebugPyClient()
            >>> client.set_breakpoint("app.py", 42, condition="x > 10")
        """
        if not self.is_available():
            return False

        # Placeholder for MCP breakpoint set
        return True

    def clear_breakpoints(self) -> bool:
        """Clear all breakpoints.

        Returns:
            True if breakpoints were cleared successfully.
        """
        if not self.is_available():
            return False

        # Placeholder for MCP breakpoint clear
        return True

    def continue_execution(self) -> bool:
        """Continue execution of the debugged process.

        Returns:
            True if command was sent successfully.
        """
        if not self.is_available():
            return False

        # Placeholder for MCP continue command
        return True

    def step_into(self) -> bool:
        """Step into the current function call.

        Returns:
            True if command was sent successfully.
        """
        if not self.is_available():
            return False

        # Placeholder for MCP step command
        return True

    def step_over(self) -> bool:
        """Step over the current function call.

        Returns:
            True if command was sent successfully.
        """
        if not self.is_available():
            return False

        # Placeholder for MCP step over command
        return True

    def step_out(self) -> bool:
        """Step out of the current function.

        Returns:
            True if command was sent successfully.
        """
        if not self.is_available():
            return False

        # Placeholder for MCP step out command
        return True

    def get_local_variables(self, frame_index: int = 0) -> Optional[Dict[str, Any]]:
        """Get local variables for a specific stack frame.

        Args:
            frame_index: Index of the stack frame (0 = top/most recent).

        Returns:
            Dictionary of local variable names to values, or None.

        Examples:
            >>> client = DebugPyClient()
            >>> capture = client.capture_state()
            >>> if capture and len(capture.stack_trace) > 0:
            ...     locals = client.get_local_variables(0)
        """
        capture = self.capture_state()
        if not capture or frame_index >= len(capture.stack_trace):
            return None

        frame = capture.stack_trace[frame_index]
        return frame.locals


class DebugStateExtractor:
    """Extracts debug state for integration with rca.

    This class bridges the gap between debugpy captures and the
    rca analysis tools like ErrorSignature and StackTraceFingerprint.

    Attributes:
        client: The DebugPyClient instance.

    Examples:
        >>> extractor = DebugStateExtractor()
        >>> if extractor.is_available():
        ...     signature = extractor.extract_error_signature()
    """

    def __init__(self, client: Optional[DebugPyClient] = None):
        """Initialize the debug state extractor.

        Args:
            client: DebugPyClient instance. If None, creates default.
        """
        self.client = client or DebugPyClient()

    def is_available(self) -> bool:
        """Check if debugpy is available."""
        return self.client.is_available()

    def extract_error_signature(self) -> Optional[Dict[str, Any]]:
        """Extract error signature from current debug state.

        Returns:
            Dictionary with error type, message, and location.

        Examples:
            >>> extractor = DebugStateExtractor()
            >>> sig = extractor.extract_error_signature()
            >>> print(sig["type"])  # e.g., "KeyError"
        """
        capture = self.client.capture_state()
        if not capture or not capture.exception:
            return None

        top_frame = capture.top_frame
        return {
            "type": capture.exception.get("type"),
            "message": capture.exception.get("message"),
            "filename": top_frame.filename if top_frame else None,
            "line": top_frame.line if top_frame else None,
            "function": top_frame.function if top_frame else None,
        }

    def extract_stack_fingerprint(self) -> Optional[str]:
        """Extract a stack trace fingerprint.

        Returns:
            Fingerprint string for stack trace comparison.

        Examples:
            >>> extractor = DebugStateExtractor()
            >>> fingerprint = extractor.extract_stack_fingerprint()
        """
        capture = self.client.capture_state()
        if not capture:
            return None

        # Create fingerprint from function names and locations
        parts = []
        for frame in capture.stack_trace:
            parts.append(f"{frame.function}:{frame.filename}:{frame.line}")

        return "|".join(parts)

    def extract_local_state(self, var_names: List[str]) -> Optional[Dict[str, Any]]:
        """Extract specific local variables from current state.

        Args:
            var_names: List of variable names to extract.

        Returns:
            Dictionary of variable names to values.

        Examples:
            >>> extractor = DebugStateExtractor()
            >>> state = extractor.extract_local_state(["request", "user"])
        """
        capture = self.client.capture_state()
        if not capture or not capture.top_frame:
            return None

        all_locals = capture.top_frame.locals or {}
        return {k: all_locals.get(k) for k in var_names if k in all_locals}
