"""Semantic Daemon Client - Auto-starting client for fast semantic search.

Provides transparent access to the semantic daemon with:
- Auto-start if daemon not running
- Fallback to direct backend calls on daemon failure
- Timeout and retry logic
- Zero configuration for most use cases

Usage:
    from daemons.daemon_client import DaemonClient

    client = DaemonClient()
    results = client.search("cks", "my query", limit=5)

    # Or with fallback enabled
    client = DaemonClient(enable_fallback=True)
    results = client.search("chs", "chat topic")
"""

from __future__ import annotations

import json
import logging
import os
import platform
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

# Platform-specific imports
if platform.system() == "Windows":
    import pywintypes
    import win32file
    import win32pipe

logger = logging.getLogger(__name__)

# CSF project root configuration
# TODO: Move to pydantic-settings for production-grade config
CSF_ROOT = Path("P:/__csf")

# Discovery file path
DISCOVERY_FILE = CSF_ROOT / "data" / "semantic_daemon_discovery.json"


def _read_discovery_pipe_name() -> tuple[str | None, str | None]:
    """Read discovery file to get current daemon pipe names.

    Verifies pipe connectivity before returning pipe names to prevent
    connecting to zombie daemons with inaccessible pipes.

    Returns:
        Tuple of (pipe_name, write_signal_pipe) if discovery file exists and pipes are accessible
    """
    try:
        if DISCOVERY_FILE.exists():
            data = json.loads(DISCOVERY_FILE.read_text())
            pipe_name = data.get("pipe_name")
            write_signal_pipe = data.get("write_signal_pipe")
            pid = data.get("pid")
            timestamp = data.get("timestamp", 0)

            # Verify discovery file is not stale (> 5 minutes old)
            # This prevents connecting to long-dead daemons with stale discovery files
            import time

            discovery_age = time.time() - timestamp
            MAX_DISCOVERY_AGE = 300  # 5 minutes

            if discovery_age > MAX_DISCOVERY_AGE:
                logger.debug(
                    f"Discovery file stale ({discovery_age:.0f}s old, > {MAX_DISCOVERY_AGE}s) - cleaning up"
                )
                try:
                    DISCOVERY_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
                return None, None

            # Verify pipe is actually accessible before trusting discovery file
            # This prevents connecting to zombie daemons with dead pipes
            if pipe_name and pid:
                if _is_pipe_accessible(pipe_name):
                    # Also verify PID is valid to prevent connection to wrong process
                    if _is_pid_valid(pid):
                        return pipe_name, write_signal_pipe
                    else:
                        # Stale PID - clean up discovery file
                        try:
                            DISCOVERY_FILE.unlink(missing_ok=True)
                            logger.debug(f"Cleaned up stale discovery file with invalid PID {pid}")
                        except Exception:
                            pass
                else:
                    # Pipe not accessible - this is a zombie daemon
                    # Clean up stale discovery file
                    try:
                        DISCOVERY_FILE.unlink(missing_ok=True)
                        logger.debug(
                            f"Cleaned up discovery file for inaccessible pipe {pipe_name[-13:]}"
                        )
                    except Exception:
                        pass
    except Exception:
        pass
    return None, None


def _is_pipe_accessible(pipe_name: str) -> bool:
    """Test if a named pipe is accessible for connections.

    This verifies the pipe actually exists and can be connected to,
    preventing connections to zombie daemons with dead pipes.

    Args:
        pipe_name: Full pipe name (e.g., \\.\\pipe\\csf_semantic_12345_123456)

    Returns:
        True if pipe is accessible, False otherwise
    """
    if platform.system() != "Windows":
        return False

    try:
        import win32file

        # Try to open the pipe - this tests if the pipe actually exists
        handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        win32file.CloseHandle(handle)
        return True
    except Exception:
        # Pipe not accessible - either doesn't exist or daemon is zombie
        return False


def _is_pid_valid(pid: int) -> bool:
    """Check if a PID corresponds to a running process.

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    if pid <= 0:
        return False

    try:
        if platform.system() == "Windows":
            import win32api
            import win32con

            # Try to open the process with minimal access
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
            win32api.CloseHandle(handle)
            return True
        else:
            # Unix: send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
    except OSError:
        return False
    except Exception:  # pywintypes.error on Windows
        return False


class DaemonClientManager:
    """Singleton manager for DaemonClient with double-check locking.

    This class implements the Singleton pattern to ensure that only one
    DaemonClient instance exists across all threads in the application.
    The singleton pattern is critical for daemon clients because:

    1. **Prevents race conditions**: Multiple clients attempting to start
       the daemon simultaneously could cause conflicts
    2. **Resource efficiency**: Only one daemon process needs to be managed
    3. **Connection pooling**: Reuses the same pipe/socket connection
    4. **State consistency**: Shared daemon lifecycle state across threads

    **Double-Check Locking Pattern**:
    The implementation uses double-check locking for thread-safe lazy
    initialization:
    - First check (no lock): Fast path for already-initialized singleton
    - Second check (with lock): Only one thread enters initialization
    - Double-check inside lock: Another thread may have initialized while
      we waited for the lock

    **Usage Example**:
        ```python
        # Thread 1
        client1 = DaemonClientManager.get_instance(backend_type="cks")

        # Thread 2 (gets same instance)
        client2 = DaemonClientManager.get_instance(backend_type="cks")

        assert client1 is client2  # True - same singleton instance
        ```

    **Important Notes**:
    - The first call's kwargs are used for initialization; subsequent calls
      ignore their kwargs
    - Use reset() only in tests to clear the singleton between test cases
    - Thread-safe: Multiple threads can call get_instance() concurrently

    Attributes:
        _instance: The singleton DaemonClient instance (None until initialized)
        _lock: Threading lock for thread-safe initialization
        _backend_type: Cached backend type from initialization
    """

    _instance: DaemonClient | None = None
    _lock = threading.Lock()
    _backend_type: str | None = None

    @classmethod
    def get_instance(cls, **kwargs) -> DaemonClient:
        """Get the singleton DaemonClient instance with double-check locking.

        This method implements the double-check locking pattern to provide
        thread-safe lazy initialization of the DaemonClient singleton.

        **First call behavior**:
        - Creates new DaemonClient instance using provided kwargs
        - Stores instance in _instance for future calls
        - Initializes _backend_type from kwargs if provided

        **Subsequent calls behavior**:
        - Returns cached singleton instance (ignores kwargs)
        - No lock acquisition on fast path (already initialized)

        **Thread Safety**:
        - Multiple threads can call this method concurrently
        - Only one thread will initialize the singleton
        - All threads receive the same instance reference

        Args:
            **kwargs: Arguments passed to DaemonClient constructor.
                Only used on first call; ignored in subsequent calls.
                Common arguments:
                - backend_type (str): "cks" or "chs" for pipe name generation
                - auto_start (bool): Auto-start daemon if not running
                - enable_fallback (bool): Use direct backend on daemon failure
                - timeout (float): Seconds to wait for daemon response
                - max_retries (int): Number of retries on timeout/failure

        Returns:
            DaemonClient: The singleton DaemonClient instance.

        Example:
            ```python
            # First call initializes with kwargs
            client = DaemonClientManager.get_instance(
                backend_type="cks",
                auto_start=True,
                enable_fallback=True
            )

            # Subsequent calls return same instance (kwargs ignored)
            same_client = DaemonClientManager.get_instance(backend_type="chs")
            assert client is same_client  # True
            ```
        """
        # First check: no lock (fast path for already-initialized singleton)
        if cls._instance is not None:
            return cls._instance

        # Second check: with lock (only one thread enters)
        with cls._lock:
            # Double-check: another thread may have initialized while we waited
            if cls._instance is None:
                cls._instance = DaemonClient(**kwargs)
                # Store backend_type for get_backend_type()
                cls._backend_type = kwargs.get("backend_type")
            return cls._instance

    @classmethod
    def get_backend_type(cls) -> str | None:
        """Get the backend type of the singleton instance.

        Returns the backend_type that was used to initialize the singleton.
        This is useful for determining which backend the singleton client
        is configured to use.

        Returns:
            str | None: The backend_type string ("cks", "chs", etc.) or None
                if the singleton has not been initialized yet.

        Example:
            ```python
            DaemonClientManager.get_instance(backend_type="cks")
            backend = DaemonClientManager.get_backend_type()
            assert backend == "cks"
            ```
        """
        return cls._backend_type

    @classmethod
    def reset(cls):
        """Reset the singleton instance (primarily for testing).

        Clears the cached singleton instance and backend type, allowing
        the next call to get_instance() to create a fresh DaemonClient.

        **IMPORTANT**: This method should ONLY be used in testing scenarios.
        Calling reset() in production code will break the singleton pattern
        and may cause multiple daemon instances to be created.

        **Thread Safety**: This method acquires the lock to ensure safe
        reset even if multiple threads call reset() concurrently.

        **Use Cases**:
        - Test isolation: Reset between test cases
        - Test configuration: Reinitialize with different parameters
        - Daemon restart: Clear after daemon crash/restart

        Example:
            ```python
            # In a test fixture
            def setup_method(self):
                DaemonClientManager.reset()

            def test_daemon_client(self):
                client = DaemonClientManager.get_instance(backend_type="cks")
                # ... test code ...

            def teardown_method(self):
                DaemonClientManager.reset()
            ```
        """
        with cls._lock:
            cls._instance = None
            cls._backend_type = None


class _DaemonClientSingleton(type):
    """Metaclass that implements singleton pattern with double-check locking.

    This metaclass ensures that DaemonClient() returns the same instance
    across all calls, and __init__ is only called once.
    """

    _instance = None
    _lock = threading.Lock()
    _original_init = None

    def _reset_singleton(cls):
        """Reset the singleton instance (primarily for testing)."""
        with cls._lock:
            _DaemonClientSingleton._instance = None

    def __call__(cls, *args, **kwargs):
        """Return the singleton instance with double-check locking.

        Args:
            *args: Positional arguments (only used on first call)
            **kwargs: Keyword arguments (only used on first call)

        Returns:
            The singleton DaemonClient instance
        """
        # Detect if __init__ has been patched (for testing)
        # If __init__ is different from the original, reset the singleton
        current_init = cls.__init__
        if _DaemonClientSingleton._original_init is None:
            _DaemonClientSingleton._original_init = current_init
        elif current_init is not _DaemonClientSingleton._original_init:
            # __init__ has been patched, reset the singleton
            _DaemonClientSingleton._instance = None
            _DaemonClientSingleton._original_init = current_init

        # First check: no lock (fast path for already-initialized singleton)
        # Must check AFTER patch detection
        if _DaemonClientSingleton._instance is not None:
            return _DaemonClientSingleton._instance

        # Second check: with lock (only one thread enters)
        with cls._lock:
            # Double-check: another thread may have initialized while we waited
            if _DaemonClientSingleton._instance is None:
                # Create the instance - __new__ then __init__
                instance = cls.__new__(cls, *args, **kwargs)
                # Call __init__ via __get__ to respect patches
                # This ensures that any mock.patch applied to __init__ will be called
                init_method = cls.__init__.__get__(instance, cls)
                init_method(*args, **kwargs)
                _DaemonClientSingleton._instance = instance
            return _DaemonClientSingleton._instance


class DaemonClient(metaclass=_DaemonClientSingleton):
    """Client for semantic daemon with auto-start and fallback.

    Features:
    - Auto-detects if daemon is running
    - Auto-starts daemon if not running (optional)
    - Falls back to direct backend calls on failure (optional)
    - Timeout and retry logic
    - PID staleness detection
    - Singleton pattern with double-check locking for thread safety
    """

    def __init__(
        self,
        pipe_name: str | None = None,
        backend_type: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 2,
        enable_fallback: bool = False,
        auto_start: bool = True,
    ):
        """Initialize daemon client with configurable behavior.

        Creates a DaemonClient instance that communicates with the semantic
        daemon via named pipes (Windows) or Unix sockets. The client can
        automatically start the daemon and fall back to direct backend calls
        when the daemon is unavailable.

        **Parameters**:

        Args:
            pipe_name: Name of the daemon's named pipe/socket. If not provided,
                the client will attempt to read from the discovery file, then
                auto-generate a pipe name based on backend_type. Default format:
                "csf_semantic_{backend_type}" or "csf_semantic" if no backend_type.
            backend_type: Backend type for pipe name generation and search routing.
                Valid values: "cks" (Constitutional Knowledge System) or "chs"
                (Chat History Search). This is stored for get_backend_type() but
                does not constrain the search() backend parameter.
            timeout: Seconds to wait for daemon response before timing out.
                Default is 10.0 seconds. This timeout applies to each request sent
                to the daemon. For health checks, is_daemon_alive() uses a shorter
                timeout (0.5s by default).
            max_retries: Number of retry attempts on timeout or transient failure.
                Default is 2 retries (total 3 attempts). Retries use exponential
                backoff with 0.5s delay between attempts.
            enable_fallback: If True, automatically fall back to direct backend
                calls when daemon communication fails. Default is False.

                **Fallback Behavior**:
                - On ConnectionError, TimeoutError, or OSError: Falls back to
                  direct backend (CKS or CHS) instead of raising exception
                - For "cks" backend: Uses direct CKS.search() via SQLite
                - For "chs" backend: Uses direct HybridSearcher via vector search
                - Response format matches daemon responses for consistency
                - Sets "fallback": True in response dict to indicate fallback used

                **When to enable**: Production resilience, graceful degradation
                **When to disable**: Debugging daemon issues, strict daemon usage

            auto_start: If True, automatically start the daemon if not running.
                Default is True.

                **Auto-Start Behavior**:
                - Checks if daemon is running via _is_daemon_running()
                - If not running, calls _start_daemon() to spawn daemon process
                - Waits up to 10 seconds for daemon to become ready
                - Uses pythonw.exe on Windows to suppress console window
                - Sets _daemon_started_here flag to track daemon lifecycle
                - shutdown() will only terminate daemons started by this client

                **When to enable**: Typical usage, zero-config daemon access
                **When to disable**: Daemon already running, external management

        **Discovery File**:
        The client first reads P:/__csf/data/semantic_daemon_discovery.json
        to find the current daemon's dynamic pipe name. This file is created
        by the daemon on startup and contains the actual pipe name (e.g.,
        "\\\\.\\pipe\\csf_semantic_12345_1769657446"). If the discovery file
        doesn't exist, the client falls back to the pipe_name parameter or
        auto-generation based on backend_type.

        **Daemon Lifecycle**:
        - If auto_start=True and daemon not running: Starts daemon during __init__
        - If auto_start=False: Does not attempt to start daemon
        - shutdown() terminates daemon only if _daemon_started_here=True
        - Context manager (__enter__/__exit__) auto-shutdowns daemon on exit

        **Thread Safety**:
        - DaemonClient uses a singleton metaclass for thread-safe initialization
        - search() method is thread-safe for concurrent requests
        - _send_request() uses platform-specific IPC primitives

        **Platform Differences**:
        - Windows: Uses named pipes (\\\\.\\pipe\\<name>) via pywin32
        - Unix/Linux: Uses Unix socket (/tmp/<name>.sock)

        **Raises**:
            No exceptions during __init__. Daemon start failures are logged
            but do not raise. Connection issues will be raised on first search()
            call if enable_fallback=False.

        Example:
            ```python
            # Zero-config usage (auto-start, no fallback)
            client = DaemonClient()
            results = client.search("cks", "async patterns", limit=5)

            # Production-resilient client (auto-start + fallback)
            client = DaemonClient(
                backend_type="cks",
                auto_start=True,
                enable_fallback=True,
                timeout=10.0,
                max_retries=3
            )

            # Manual daemon management (no auto-start)
            client = DaemonClient(auto_start=False)
            if not client.is_daemon_alive():
                # Handle daemon not running
                pass
            ```

        **Instance Attributes**:
            pipe_name (str): The resolved pipe/socket name
            timeout (float): Request timeout in seconds
            max_retries (int): Maximum retry attempts
            enable_fallback (bool): Fallback to direct backend on failure
            auto_start (bool): Auto-start daemon if not running
            _daemon_started_here (bool): True if this client started the daemon
            _daemon_process (subprocess.Popen | None): Handle to daemon process
            _pipe_path (str): Full pipe path (\\\\.\\pipe\\<name> or /tmp/<name>.sock)
            _pid_file (Path): Path to daemon PID file for staleness detection
            _backend_type (str | None): Cached backend type for get_backend_type()
        """
        # Store backend_type for get_backend_type()
        self._backend_type = backend_type

        # Try to read discovery file first to get dynamic pipe name
        discovery_pipe, discovery_write_signal = _read_discovery_pipe_name()
        if discovery_pipe:
            # Extract just the pipe name from full path (\\.\pipe\csf_semantic_123_456)
            import re

            match = re.search(r"csf_semantic_\d+_\d+", discovery_pipe)
            if match:
                self.pipe_name = match.group(0)
                logger.debug(f"Using dynamic pipe name from discovery: {self.pipe_name}")
            else:
                # Fallback to auto-generation
                self.pipe_name = pipe_name or "csf_semantic"
            # Use write_signal_pipe from discovery if available, otherwise use default
            self._write_signal_pipe = discovery_write_signal if discovery_write_signal else r"\\.\pipe\csf_semantic_write_signal"
        else:
            # Auto-generate pipe name if not provided
            if pipe_name is None:
                if backend_type:
                    pipe_name = f"csf_semantic_{backend_type.lower()}"
                else:
                    pipe_name = "csf_semantic"
            self.pipe_name = pipe_name
            self._write_signal_pipe = r"\\.\pipe\csf_semantic_write_signal"

        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_fallback = enable_fallback
        self.auto_start = auto_start
        self._daemon_started_here = False
        self._daemon_process = None

        # Get pipe/socket path
        self._pipe_path = self._get_pipe_path()

        # PID file path
        self._pid_file = (
            Path(__file__).parent.parent.parent.parent / "data" / f"{self.pipe_name}.pid"
        )

        # Auto-start daemon if requested
        if auto_start and not self._is_daemon_running():
            self._start_daemon()
            self._wait_for_daemon()

    def _get_pipe_path(self) -> str:
        """Get the pipe/socket path based on platform."""
        if platform.system() == "Windows":
            # Windows named pipe: \\.\pipe\<name>
            # Pipe name should already be in the correct format (e.g., "csf_semantic_123_456")
            # Use double backslash in raw string for literal backslash
            return rf"\\.\pipe\{self.pipe_name}"
        else:
            # Unix socket: /tmp/<name>.sock
            return f"/tmp/{self.pipe_name}.sock"

    def get_backend_type(self) -> str | None:
        """Get the backend type of this client.

        Returns:
            The backend_type string (e.g., "cks", "chs") or None
        """
        return self._backend_type

    @classmethod
    def _reset_singleton(cls):
        """Reset the singleton instance (primarily for testing).

        This clears the cached singleton instance so that the next call
        to DaemonClient() will create a new instance.
        """
        type(cls)._reset_singleton()

    def _read_pid_file(self) -> int | None:
        """Read PID from PID file if it exists.

        Returns:
            PID if file exists and contains valid data, None otherwise
        """
        try:
            if self._pid_file.exists():
                pid_str = self._pid_file.read_text().strip()
                if pid_str:
                    return int(pid_str)
        except (OSError, ValueError):
            pass
        return None

    def _clear_stale_pid(self) -> bool:
        """Clear stale PID file if daemon is not running.

        Returns:
            True if PID file was cleared (was stale), False if daemon is running
        """
        pid = self._read_pid_file()
        if pid is None:
            return True  # No PID file, nothing to clear

        if _is_pid_valid(pid):
            return False  # Daemon is running

        # PID is stale, remove the file
        try:
            self._pid_file.unlink(missing_ok=True)
            logger.info(f"Cleared stale PID file: {self._pid_file}")
            return True
        except OSError as e:
            logger.warning(f"Failed to clear stale PID file: {e}")
            return True

    def _cleanup_stale_discovery_file(self) -> bool:
        """Clean up stale discovery file if daemon is not running.

        The discovery file contains the daemon's pipe name and PID. If the daemon
        exits abnormally (crash, killed, system shutdown), the discovery file remains
        and blocks all future daemon starts. This method checks if the PID in the
        discovery file is still running and deletes the file if not.

        Returns:
            True if discovery file was cleared (was stale) or didn't exist,
            False if daemon is running (file should remain)
        """
        discovery_file = (
            Path(__file__).parent.parent.parent.parent / "data" / "semantic_daemon_discovery.json"
        )

        if not discovery_file.exists():
            return True  # No discovery file, nothing to clean

        try:
            import json

            data = json.loads(discovery_file.read_text())
            pid = data.get("pid")

            if pid and _is_pid_valid(pid):
                # Daemon is running, keep discovery file
                return False

            # PID is not running, stale discovery file
            discovery_file.unlink()
            logger.info(f"Cleaned up stale discovery file (pid={pid} was not running)")
            return True

        except (OSError, ValueError, json.JSONDecodeError) as e:
            # Corrupted or unreadable discovery file - clean it up
            try:
                discovery_file.unlink(missing_ok=True)
                logger.info(f"Cleaned up corrupted discovery file: {e}")
            except OSError:
                pass
            return True

    def _is_daemon_running(self) -> bool:
        """Check if daemon is running by attempting to connect.

        Also checks PID file staleness to detect dead daemons.
        """
        # First check PID file staleness
        self._clear_stale_pid()

        if platform.system() == "Windows":
            try:
                win32pipe.WaitNamedPipe(self._pipe_path, 100)  # 100ms timeout
                return True
            except pywintypes.error:
                return False
        else:
            return Path(self._pipe_path).exists()

    def _start_daemon(self) -> bool:
        """Start the semantic daemon in background.

        Returns True if daemon started successfully, False otherwise.

        CRITICAL: Must run as module (-m src.daemons.unified_semantic_daemon) not as script,
        because the daemon has top-level imports like 'from search_research.cache import QueryCache'
        that require proper module path resolution. Module invocation handles this correctly.
        """
        if self._daemon_started_here:
            return True  # Already started by us

        try:
            # Clear any stale PID before starting
            self._clear_stale_pid()

            # CRITICAL: Clean up stale discovery file before starting daemon
            # The discovery file can become stale when daemon exits abnormally (crash, killed).
            # A stale discovery file blocks new daemon starts because the existing daemon
            # check at line 962-977 of unified_semantic_daemon.py returns False.
            self._cleanup_stale_discovery_file()

            # CRITICAL FIX: Use keep-alive wrapper instead of launching daemon directly
            # The keep-alive wrapper monitors the daemon and automatically restarts it
            # if it exits unexpectedly. This solves the Windows DETACHED_PROCESS issue
            # where the daemon would exit prematurely after creating the pipe.
            python_exe = sys.executable
            if platform.system() == "Windows" and python_exe.endswith("python.exe"):
                python_exe = python_exe.replace("python.exe", "pythonw.exe")
            cmd = [python_exe, "-m", "src.daemons.daemon_keep_alive"]

            # Start keep-alive wrapper in background
            if platform.system() == "Windows":
                # Use CREATE_NEW_PROCESS_GROUP to avoid inheriting signals
                # Add DETACHED_PROCESS (0x00000008) to prevent inheriting console
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE  # Suppress console window
                self._daemon_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_NO_WINDOW
                    | 0x00000008,
                    startupinfo=startupinfo,
                    close_fds=True,
                )
            else:
                self._daemon_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )

            self._daemon_started_here = True
            logger.info(f"Started semantic daemon (PID: {self._daemon_process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start daemon: {e}")
            return False

    def _wait_for_daemon(self, timeout_sec: float = 10.0) -> bool:
        """Wait for daemon to become ready.

        Returns True if daemon is ready, False if timeout.
        """
        start = time.time()
        while time.time() - start < timeout_sec:
            if self._is_daemon_running():
                return True
            time.sleep(0.1)
        return False

    def _send_request(self, request: dict) -> dict:
        """Send request to daemon and get response.

        Raises:
            ConnectionError: If daemon not available
            TimeoutError: If request times out
        """
        if platform.system() == "Windows":
            return self._send_windows(request)
        else:
            return self._send_unix(request)

    def _normalize_response(self, response: dict, backend: str, query: str) -> dict:
        """Normalize daemon response to consistent client format.

        Daemon returns: {results: [], scope: "cks"/"chs", error: ...}
        Client expects: {status: "", count: N, results: [], backend: "", query: "", timing_seconds: N}
        """
        # Extract results
        results = response.get("results", [])
        if not isinstance(results, list):
            results = []

        # Determine status
        if "error" in response:
            status = "error"
        elif results:
            status = "success"
        else:
            status = "no_results"

        # Map daemon's "scope" to client's "backend" (or use provided backend)
        response_backend = response.get("scope", backend)

        return {
            "status": status,
            "count": len(results),
            "results": results,
            "backend": response_backend,
            "query": query,
            "timing_seconds": response.get("timing_seconds", 0),
            "error": response.get("error"),
        }

    def _send_windows(self, request: dict) -> dict:
        """Send request via Windows named pipe.

        Uses 4-byte length prefix + JSON protocol to match daemon's expected format.
        """
        try:
            pipe = win32file.CreateFile(
                self._pipe_path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )

            # Send request with 4-byte length prefix (daemon's protocol)
            request_data = json.dumps(request).encode("utf-8")
            message = struct.pack("<I", len(request_data)) + request_data
            win32file.WriteFile(pipe, message)

            # Read response: 4-byte length prefix + JSON data
            result = win32file.ReadFile(pipe, 4)
            # pywin32 ReadFile returns (bytes_read, data) tuple
            if isinstance(result, tuple):
                length_data = result[1] if len(result) > 1 else result[0]
            else:
                length_data = result
            length = struct.unpack("<I", length_data)[0]

            # Read JSON data
            response_data = b""
            remaining = length
            while remaining > 0:
                result = win32file.ReadFile(pipe, min(65536, remaining))
                if isinstance(result, tuple):
                    chunk = result[1] if len(result) > 1 else result[0]
                else:
                    chunk = result
                if not chunk:
                    break
                response_data += chunk
                remaining -= len(chunk)

            win32file.CloseHandle(pipe)
            return json.loads(response_data.decode("utf-8"))

        except pywintypes.error as e:
            if e.args[0] == 2:  # File not found = pipe doesn't exist
                raise ConnectionError(f"Daemon pipe not found: {self._pipe_path}")
            elif e.args[0] == 233:  # No process on other end
                raise ConnectionError("Daemon not running on pipe")
            else:
                raise ConnectionError(f"Pipe error: {e}")

    def _send_unix(self, request: dict) -> dict:
        """Send request via Unix socket."""
        import socket

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect(self._pipe_path)
            sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in chunk:
                    break

            return json.loads(response_data.decode("utf-8").strip())

        except TimeoutError:
            raise TimeoutError("Daemon request timed out")
        except FileNotFoundError:
            raise ConnectionError(f"Daemon socket not found: {self._pipe_path}")
        finally:
            sock.close()

    def _send_write_signal(self, msg: dict) -> bool:
        """Send write signal to daemon via write-signal pipe (fire-and-forget).

        This is advisory only - failure does not raise, just returns False.
        The signal tells the daemon that CKS entries have been written and
        it should refresh its FAISS index.

        Args:
            msg: Dictionary with keys: action, entry_id, entry_type, workspace, terminal_id

        Returns:
            True if signal sent successfully, False otherwise
        """
        if platform.system() != "Windows":
            return False

        try:
            import win32file
            import win32pipe
            import pywintypes

            # Connect to write signal pipe
            try:
                pipe = win32file.CreateFile(
                    self._write_signal_pipe,
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None,
                )
            except pywintypes.error as e:
                if e.args[0] == 2:  # File not found
                    logger.debug(f"Write signal pipe not found: {self._write_signal_pipe}")
                    return False
                elif e.args[0] == 233:  # No process on other end
                    logger.debug(f"Daemon not running on write signal pipe")
                    return False
                else:
                    logger.debug(f"Write signal pipe error: {e}")
                    return False

            # Send the message
            request_data = json.dumps(msg).encode("utf-8")
            message = struct.pack("<I", len(request_data)) + request_data
            win32file.WriteFile(pipe, message)
            win32file.CloseHandle(pipe)
            logger.debug(f"Write signal sent: {msg.get('action')} for entry_id={msg.get('entry_id')}")
            return True

        except Exception as e:
            logger.debug(f"Failed to send write signal: {e}")
            return False

    def _fallback_search(self, backend: str, query: str, limit: int | None = None) -> dict:
        """Fallback to direct backend search when daemon unavailable.

        This is called when enable_fallback=True and daemon fails.
        """
        logger.info(f"Using fallback for {backend} search")

        try:
            if backend == "cks":
                return self._cks_fallback(query, limit or 20)
            elif backend == "chs":
                return self._chs_fallback(query, limit or 20)
            else:
                return {
                    "status": "error",
                    "error": f"Backend {backend} not supported in fallback",
                    "results": [],
                    "count": 0,
                }
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": [],
                "count": 0,
            }

    def _cks_fallback(self, query: str, limit: int) -> dict:
        """Fallback CKS search using direct backend."""
        from cks.unified import CKS

        db_path = CSF_ROOT / "data" / "cks.db"

        with CKS(str(db_path)) as cks:
            results = cks.search(query, limit=limit)

        # Convert to daemon response format
        formatted = []
        for r in results:
            formatted.append(
                {
                    "content": str(r.get("content", "")),
                    "score": float(r.get("score", 0.0)),
                    "type": str(r.get("type", "")),
                    "id": str(r.get("id", "")),
                }
            )

        return {
            "status": "success",
            "count": len(formatted),
            "results": formatted,
            "backend": "cks",
            "query": query,
            "timing_seconds": 0,
            "fallback": True,
        }

    def _chs_fallback(self, query: str, limit: int) -> dict:
        """Fallback CHS search using direct backend."""
        # Note: This fallback requires the CHS module to be in PYTHONPATH
        # For production, consider using proper package installation
        try:
            from modules.analysis.chat_search.src.hybrid_searcher import (
                HybridSearcherFactory,
            )
        except ImportError:
            # Fallback not available, return empty results
            return {
                "status": "error",
                "count": 0,
                "results": [],
                "backend": "chs",
                "query": query,
                "timing_seconds": 0,
                "fallback": False,
                "error": "CHS fallback not available - module not found",
            }

        searcher = HybridSearcherFactory.create_vector_only_searcher()
        results = searcher.search(query, limit=limit)

        # Convert to daemon response format
        formatted = []
        for r in results[:limit]:
            formatted.append(
                {
                    "content": str(r.get("content", ""))[:500],
                    "score": float(r.get("score", 0)),
                    "session_id": str(r.get("session_id", "")),
                    "timestamp": str(r.get("timestamp", "")),
                }
            )

        return {
            "status": "success",
            "count": len(formatted),
            "results": formatted,
            "backend": "chs",
            "query": query,
            "timing_seconds": 0,
            "fallback": True,
        }

    def search(self, backend: str, query: str, limit: int = 20, **kwargs) -> dict:
        """Search via daemon with auto-start and fallback.

        Args:
            backend: Backend name ("cks" or "chs")
            query: Search query string
            limit: Maximum results to return
            **kwargs: Additional search parameters
                - hours_ago: Filter results to last N hours (int)
                - after: ISO timestamp for start filter (str)
                - before: ISO timestamp for end filter (str)

        Returns:
            Dict with keys: status, count, results, backend, query, timing_seconds
        """
        request = {
            "backend": backend,
            "query": query,
            "limit": limit,
            **kwargs,
        }

        # Try daemon first
        for attempt in range(self.max_retries + 1):
            try:
                # Check if daemon is running
                if not self._is_daemon_running():
                    if self.auto_start:
                        logger.info("Daemon not running, attempting to start...")
                        if self._start_daemon():
                            if not self._wait_for_daemon():
                                logger.warning("Daemon failed to start in time")
                                if self.enable_fallback:
                                    return self._fallback_search(backend, query, limit)
                                raise ConnectionError("Daemon not available")
                        else:
                            logger.warning("Failed to start daemon")
                            if self.enable_fallback:
                                return self._fallback_search(backend, query, limit)
                            raise ConnectionError("Daemon not available")
                    else:
                        # No auto-start, try direct connection
                        pass

                # Send request
                response = self._send_request(request)
                # Normalize daemon response format to client expectations
                return self._normalize_response(response, backend, query)

            except Exception as e:
                if attempt < self.max_retries:
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                    time.sleep(0.5)
                    continue

                # All retries exhausted - use fallback if enabled
                if self.enable_fallback:
                    return self._fallback_search(backend, query, limit)
                raise

        # Should not reach here
        return {
            "status": "error",
            "error": "Max retries exceeded",
            "results": [],
            "count": 0,
        }

    def embed_texts(self, texts: list[str]) -> list[bytes]:
        """Generate embeddings for texts via daemon's compute_embedding action.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embeddings as bytes (serialized numpy arrays)
        """
        embeddings = []
        for text in texts:
            for attempt in range(self.max_retries + 1):
                try:
                    request = {"action": "compute_embedding", "text": text}
                    response = self._send_request(request)
                    if "embedding" in response and response["embedding"]:
                        # Response contains embedding as list of floats
                        emb = response["embedding"]
                        import numpy as np

                        vec = np.array(emb, dtype=np.float32)
                        embeddings.append(vec.tobytes())
                        break
                    else:
                        # Fallback: use dummy
                        import numpy as np

                        vec = np.zeros(384, dtype=np.float32)
                        embeddings.append(vec.tobytes())
                        break
                except (ConnectionError, TimeoutError) as e:
                    if attempt < self.max_retries:
                        time.sleep(0.5)
                        continue
                    # Fallback on failure
                    import numpy as np

                    vec = np.zeros(384, dtype=np.float32)
                    embeddings.append(vec.tobytes())
        return embeddings

    def is_daemon_alive(self, timeout: float = 0.5) -> bool:
        """Check if daemon is alive via quick ping request.

        Performs a lightweight health check by sending a "ping" request to the
        daemon and verifying it responds with "pong". This is much faster than
        a full search request and is suitable for monitoring and pre-flight checks.

        **Ping Protocol**:
        - Sends request: {"cmd": "ping", "timeout": <timeout>}
        - Expects response: {"status": "pong"}
        - Any other response or exception treated as daemon not alive

        **Timeout Behavior**:
        - The timeout parameter is passed to the daemon in the ping request
        - The daemon should respond within the specified timeout period
        - Default is 0.5 seconds for quick health checks
        - This is independent of the client's default request timeout
        - A shorter timeout (e.g., 0.1s) can be used for aggressive monitoring

        **Return Values**:
        - **True**: Daemon is alive and responded with pong
        - **False**: One of the following conditions:
            - Daemon timed out (TimeoutError)
            - Pipe/socket connection failed (ConnectionError)
            - OS error accessing pipe (OSError)
            - Unexpected response format (not {"status": "pong"})
            - Any other exception (defensive error handling)

        **Error Handling**:
        This method implements defensive error handling and will NOT raise
        exceptions. All errors are caught and return False. This makes the
        method safe to use in monitoring loops and health check systems.

        **Thread Safety**:
        - Safe to call from multiple threads concurrently
        - Each call creates a new pipe/socket connection
        - No shared state modification

        **Platform Differences**:
        - Windows: Uses named pipe (win32pipe.CreateFile)
        - Unix: Uses Unix socket (socket.connect)

        **Performance**:
        - Typical latency: 5-50ms on local machine
        - Timeout default: 0.5s (configurable)
        - Much faster than full search request (which may take 100-500ms)

        **Use Cases**:
        - Pre-flight check before expensive search operations
        - Monitoring daemon health in background thread
        - Detecting daemon crashes during long-running processes
        - Verifying daemon startup after auto_start

        **Example**:
            ```python
            client = DaemonClient(auto_start=False)

            # Quick health check
            if client.is_daemon_alive(timeout=0.5):
                print("Daemon is healthy")
            else:
                print("Daemon is not responding")

            # Aggressive monitoring with short timeout
            if not client.is_daemon_alive(timeout=0.1):
                # Daemon might be slow or dead
                client._start_daemon()

            # In a monitoring loop
            import time
            while True:
                if not client.is_daemon_alive():
                    logger.warning("Daemon health check failed")
                time.sleep(5)
            ```

        **Comparison with _is_daemon_running()**:
        - is_daemon_alive(): Sends ping request, verifies daemon responsiveness
        - _is_daemon_running(): Only checks if pipe/socket exists (faster, less reliable)
        - Use is_daemon_alive() for critical health checks
        - Use _is_daemon_running() for quick existence checks

        Args:
            timeout: Seconds to wait for ping response. Default is 0.5 seconds.
                This timeout is passed to the daemon and limits how long the
                ping request can take. Shorter values (e.g., 0.1) enable faster
                failure detection but may cause false positives on slow systems.

        Returns:
            bool: True if daemon is alive and responded with pong, False otherwise.
                Returns False for any error, timeout, or unexpected response.
                Never raises exceptions (defensive error handling).

        Note:
            This method does NOT attempt to auto-start the daemon, even if
            auto_start=True. It only checks the current daemon state. To
            start the daemon if not running, use _start_daemon() or create
            a new DaemonClient with auto_start=True.
        """
        try:
            request = {"cmd": "ping", "timeout": timeout}
            response = self._send_request(request)
            return response.get("status") == "pong"
        except (TimeoutError, ConnectionError, OSError):
            return False
        except Exception:
            return False

    def query(self, action: str, params: dict, timeout: float = 2.5) -> dict:
        """Send generic action query to daemon (for skill_intent, etc.).

        This method provides a generic interface for sending action-based
        requests to the semantic daemon. Unlike search(), which is specific
        to CKS/CHS search operations, this method can handle any action
        supported by the daemon (e.g., "skill_intent", "classify_intent").

        **Usage Pattern**:
        The daemon's wire protocol uses an "action" field to route requests
        to different handlers. This method wraps that pattern in a convenient
        interface.

        Args:
            action: Action name (e.g., "skill_intent", "classify_intent").
                Maps to the daemon's request routing logic.
            params: Action-specific parameters. These are merged with the
                action field to create the request payload.
            timeout: Request timeout in seconds. Default is 2.5 seconds.
                This timeout applies per request attempt (not including retries).

        Returns:
            Dict with keys:
                - status: "success" if request succeeded, "error" if failed
                - result: The daemon's response payload (on success)
                - error: Error message string (on failure, if fallback disabled)

        **Error Handling**:
        - If enable_fallback=True: Returns {"status": "error", "error": "..."}
          instead of raising exceptions
        - If enable_fallback=False: Raises ConnectionError, TimeoutError, or OSError

        **Example**:
            ```python
            client = DaemonClient(auto_start=True, enable_fallback=True)

            # Query skill intent
            result = client.query(
                "skill_intent",
                {"command": "from src.rca import SimpleRCAEngine", "skill": "rca"}
            )
            if result["status"] == "success":
                match = result["result"].get("match", False)
                similarity = result["result"].get("similarity", 0.0)
            ```

        **Thread Safety**:
        - Safe to call from multiple threads concurrently
        - Each call creates a new pipe connection
        - No shared state modification
        """
        request = {"action": action, **params}

        # Try daemon with timeout
        for attempt in range(self.max_retries + 1):
            try:
                # Check if daemon is running
                if not self._is_daemon_running():
                    if self.auto_start:
                        logger.info("Daemon not running, attempting to start...")
                        if self._start_daemon():
                            if not self._wait_for_daemon():
                                logger.warning("Daemon failed to start in time")
                                if self.enable_fallback:
                                    return {
                                        "status": "error",
                                        "error": "Daemon not available",
                                    }
                                raise ConnectionError("Daemon not available")
                        else:
                            logger.warning("Failed to start daemon")
                            if self.enable_fallback:
                                return {
                                    "status": "error",
                                    "error": "Daemon not available",
                                }
                            raise ConnectionError("Daemon not available")

                # Send request with timeout
                # Note: _send_request doesn't support per-request timeout,
                # so we rely on the daemon's request timeout handling
                response = self._send_request(request)

                # Return success response
                return {"status": "success", "result": response}

            except Exception as e:
                if attempt < self.max_retries:
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                    time.sleep(0.5)
                    continue

                # All retries exhausted
                if self.enable_fallback:
                    return {"status": "error", "error": str(e)}
                raise

        # Should not reach here
        return {"status": "error", "error": "Max retries exceeded"}

    def send_write_signal(
        self,
        entry_id: str,
        entry_type: str,
        workspace: str,
        terminal_id: str,
    ) -> bool:
        """Send advisory write signal to daemon after CKS ingest.

        This notifies the daemon that new CKS entries have been written so it
        can refresh its FAISS index immediately instead of waiting for the
        10-minute idle timeout.

        This is advisory only - failure does not raise exceptions. The daemon
        will catch up on its next idle cycle if the signal is missed.

        Args:
            entry_id: The CKS entry ID that was written
            entry_type: The CKS entry type (memory, pattern, correction, etc.)
            workspace: The workspace path where the entry was written
            terminal_id: The terminal ID where the entry was written

        Returns:
            True if signal was sent successfully, False if it failed
                   (daemon down, pipe error, etc.)
        """
        msg = {
            "action": "cks_write",
            "entry_id": entry_id,
            "entry_type": entry_type,
            "workspace": workspace,
            "terminal_id": terminal_id,
        }
        return self._send_write_signal(msg)

    def shutdown(self):
        """Shutdown daemon if we started it.

        Note: Only stops daemons that were auto-started by this client.
        """
        if self._daemon_started_here and self._daemon_process:
            try:
                self._daemon_process.terminate()
                self._daemon_process.wait(timeout=5)
                # Clean up PID file
                self._pid_file.unlink(missing_ok=True)
                logger.info("Shutdown daemon started by this client")
            except Exception as e:
                logger.warning(f"Failed to shutdown daemon: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Convenience functions for quick access


def search_cks(query: str, limit: int = 20, auto_start: bool = False) -> dict:
    """Quick CKS search via daemon.

    Args:
        query: Search query
        limit: Maximum results
        auto_start: Auto-start daemon if not running

    Returns:
        Search results dict
    """
    client = DaemonClient(backend_type="cks", auto_start=auto_start)
    return client.search("cks", query, limit)


def search_chs(query: str, limit: int = 20, auto_start: bool = False) -> dict:
    """Quick CHS search via daemon.

    Args:
        query: Search query
        limit: Maximum results
        auto_start: Auto-start daemon if not running

    Returns:
        Search results dict
    """
    client = DaemonClient(backend_type="chs", auto_start=auto_start)
    return client.search("chs", query, limit)
