#!/usr/bin/env python3
r"""
Unified Semantic Daemon - Named pipe server for CKS and CHS search.

Provides semantic search for:
- CKS: Constitutional Knowledge System (memories, patterns, code, knowledge)
- CHS: Chat History Search (conversation history, context)

Uses Windows named pipes for IPC: \\.\pipe\csf_semantic

Usage:
    from daemons.unified_semantic_daemon import get_or_start_daemon, SemanticClient

    # Start daemon (singleton)
    daemon = get_or_start_daemon()

    # Or use client
    client = SemanticClient()
    results = client.search("cks", "semantic search query", limit=5)
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import sqlite3
import struct
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Literal, TypedDict

import psutil

# Type definitions for intent classification
IntentCategory = Literal[
    "search",
    "read",
    "write",
    "analyze",
    "research",
    "code",
    "test",
    "git",
    "web",
    "existence_claim",
    "other",
]


class IntentClassificationResult(TypedDict, total=True):
    """Result of intent classification."""

    intent: IntentCategory
    confidence: float


# Project root for path resolution (used for FAISS, database paths)
# Daemon lives in packages/search-research but serves P:/__csf/
_csf_root = Path("P:/__csf")

# JSON logging configuration (Python 2025 standard)
import structlog

# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Use structlog logger (JSON format)
logger = structlog.get_logger()

try:
    import pywintypes
    import win32api
    import win32con
    import win32event
    import win32file
    import win32pipe
    import winerror

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    win32api = win32con = winerror = win32event = win32file = win32pipe = pywintypes = None

# Query cache import - migrated to search_research package
from search_research.cache import QueryCache

# =============================================================================
# Constants
# =============================================================================

PIPE_NAME = r"\\.\pipe\csf_semantic"  # Fallback/legacy name
DISCOVERY_FILE = Path("P:/__csf/data/semantic_daemon_discovery.json")
PID_FILE = Path("P:/__csf/data/semantic_daemon.pid")
MAX_DAEMON_AGE = 3600  # Maximum daemon age in seconds (1 hour) before old non-canonical daemons should self-terminate
# Windows Mutex for atomic single-instance daemon determination
# Using "Global\" prefix ensures mutex works across terminal sessions
DAEMON_MUTEX_NAME = r"Global\CSF_SemanticDaemon_Instance"
DAEMON_LOG_FILE = Path("P:/__csf/data/semantic_daemon.log")  # Debug log for silent crashes
STARTUP_TIMEOUT = 6.0
IDLE_WORK_SHORT = 5.0
IDLE_WORK_LONG = 900.0
CHS_REINDEX_INTERVAL = 300.0  # Re-index CHS every 5 minutes (300 seconds) when idle
FAISS_UPDATE_INTERVAL = 600.0  # Update FAISS index every 10 minutes idle
FAISS_MAX_AGE = 86400.0  # Force full rebuild if FAISS index is older than 24 hours (86400 seconds)
FAISS_INDEX_PATH = _csf_root / "data" / "chat_history_faiss_424k"
FAISS_STATE_PATH = _csf_root / "data" / "chs_index_state.json"
FAISS_LOCK_PATH = _csf_root / ".data" / "daemon" / "faiss_update.lock"
STATE_LOCK_PATH = _csf_root / ".data" / "daemon" / "index_state.lock"
# Time-based idle timeout: Disabled until 9pm local time, then 30 minutes (1800 seconds)
IDLE_SHUTDOWN_TIMEOUT = None  # Will be set dynamically based on time of day
REQUEST_TIMEOUT = 5.0
MAX_PIPE_SIZE = 65536
BUF_SIZE = 4096

# Time-based idle configuration
# 9pm = 21:00 in 24-hour format
IDLE_TIMEOUT_AFTER_9PM = 1800  # 30 minutes in seconds
HOUR_9PM = 21  # 9pm (21:00)

# Staleness half-lives in days for different knowledge types
TYPE_HALF_LIVES = {
    "memory": 180,
    "correction": 365,
    "pattern": 120,
    "learning": 730,
    "code": 90,
    "insight": 365,
}

# Intent classification category descriptions
# Used by both SemanticClient.classify_intent() and UnifiedSemanticDaemon._classify_intent()
# Each category maps to a comma-separated list of keywords and phrases describing that intent
_CATEGORY_DESCRIPTIONS = {
    "search": "search find locate where which searching searches finder locator look for seek hunt query find discover",
    "read": "read view show display open check reading viewing inspect examine examine file look at show me",
    "write": "write create add insert append writing creation make generate produce author draft compose",
    "analyze": "analyze examine investigate audit inspect review analysis study assess evaluate check diagnose debug",
    "research": "research look up find information documentation docs investigate online web search gather",
    "code": "code implement refactor optimize fix programming develop engineer function method class variable",
    "test": "test verify validate assert check testing specification requirement confirm ensure",
    "git": "git commit push pull branch merge checkout version control repository vcs history",
    "web": "web internet online url website http https fetch download scrape external api",
    "existence_claim": "missing absent not found unavailable doesn't exist does not exist no such cannot find unable locate",
    "other": "other miscellaneous general catch-all",
}

# Skill command examples for semantic validation (v3.2)
# Used by PreToolUse_skill_pattern_gate to validate skill execution intent
# Each skill maps to known-good command patterns
SKILL_COMMAND_EXAMPLES = {
    "rca": [
        # From SKILL.md EXECUTION DIRECTIVE
        "from src.rca.simple_rca_engine import SimpleRCAEngine",
        "from src.rca.enhancement_router import EnhancementRouter",
        "from daemons.daemon_client import DaemonClient",
        "engine = SimpleRCAEngine()",
        "client = DaemonClient(auto_start=True, enable_fallback=True)",
        # Actual patterns
        "python -m src.rca.simple_rca_engine",
        'python -c "from src.rca.simple_rca_engine import SimpleRCAEngine"',
        "src.rca",
        "SimpleRCAEngine",
        "EnhancementRouter",
    ],
    "truth": [
        "from src.truth.validator import TruthValidator",
        "python -m src.truth.validator",
        "python truth_cli.py",
        "src.truth",
        "truth_cli",
        "TruthValidator",
    ],
    "ask-olymp": [
        "python ask_cli.py",
        "ask_cli.py --provider opencode",
        "python -m ask_cli",
        "ask_cli.py --help",
    ],
}

# =============================================================================
# Memory Management Constants
# =============================================================================
# Memory limits and thresholds for daemon startup and operation
MAX_MEMORY_MB = (
    8192  # 8GB cap per daemon instance (self-termination) - increased to handle CKS+FAISS+overhead
)
STARTUP_MEMORY_HEADROOM_MB = 1024  # 1GB headroom for model loading
FAISS_ESTIMATED_MEMORY_MB = 350  # Estimated FAISS index memory (116k vectors @ 768 dim)
CKS_MODEL_MEMORY_MB = (
    4000  # Actual all-mpnet-base-v2 model memory (observed: ~4000MB in production)
)
SENTENCE_TRANSFORMER_MEMORY_MB = 200  # Estimated all-MiniLM-L6-v2 model memory

# =============================================================================
# Memory Check Functions
# =============================================================================


def _get_current_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except Exception:
        return 0.0


def _get_available_memory_mb() -> float:
    """Get available system memory in MB."""
    try:
        return psutil.virtual_memory().available / 1024 / 1024
    except Exception:
        return 0.0


def _check_memory_before_load(component_name: str, estimated_mb: int) -> bool:
    """Check if there's enough memory to load a component.

    Args:
        component_name: Name of component being loaded (for logging)
        estimated_mb: Estimated memory requirement in MB

    Returns:
        True if there's enough memory, False otherwise
    """
    current_mb = _get_current_memory_mb()
    available_mb = _get_available_memory_mb()

    # Check if loading would exceed max memory
    projected_mb = current_mb + estimated_mb
    if projected_mb > MAX_MEMORY_MB:
        logger.error(
            f"[MEMORY CHECK] {component_name}: Cannot load - projected memory "
            f"({projected_mb:.0f}MB) would exceed MAX_MEMORY_MB ({MAX_MEMORY_MB}MB). "
            f"Current: {current_mb:.0f}MB, Required: {estimated_mb}MB"
        )
        return False

    # Check if there's enough headroom
    if available_mb < STARTUP_MEMORY_HEADROOM_MB:
        logger.warning(
            f"[MEMORY CHECK] {component_name}: Low memory - available ({available_mb:.0f}MB) "
            f"below STARTUP_MEMORY_HEADROOM_MB ({STARTUP_MEMORY_HEADROOM_MB}MB). "
            f"Current usage: {current_mb:.0f}MB"
        )
        # Still proceed but warn

    logger.info(
        f"[MEMORY CHECK] {component_name}: OK - Current: {current_mb:.0f}MB, "
        f"Available: {available_mb:.0f}MB, Projected: {projected_mb:.0f}MB"
    )
    return True


def _check_memory_after_load(component_name: str) -> bool:
    """Check memory after loading a component and self-terminate if exceeded.

    Args:
        component_name: Name of component that was just loaded

    Returns:
        True if memory is OK, False if exceeded (should self-terminate)
    """
    current_mb = _get_current_memory_mb()

    if current_mb > MAX_MEMORY_MB:
        logger.error(
            f"[MEMORY CHECK] {component_name}: Memory cap exceeded after load! "
            f"Current: {current_mb:.0f}MB > MAX_MEMORY_MB ({MAX_MEMORY_MB}MB). "
            f"Daemon must self-terminate."
        )
        return False

    logger.info(f"[MEMORY CHECK] {component_name}: Post-load memory OK at {current_mb:.0f}MB")
    return True


# =============================================================================
# Global daemon singleton
# =============================================================================

_global_daemon_lock = threading.Lock()
_global_daemon = None


def get_global_daemon() -> UnifiedSemanticDaemon:
    """Get the global daemon instance (singleton)."""
    global _global_daemon
    with _global_daemon_lock:
        if _global_daemon is None:
            _global_daemon = UnifiedSemanticDaemon()
        return _global_daemon


def get_or_start_daemon() -> UnifiedSemanticDaemon:
    """Get or start the global daemon instance."""
    d = get_global_daemon()
    if not d.is_running():
        d.start()
    return d


# =============================================================================
# Client
# =============================================================================


class SemanticClient:
    """Client for connecting to the semantic daemon via named pipe."""

    def __init__(self, pipe_name: str = PIPE_NAME, auto_start: bool = True):
        # Try to read discovery file to get dynamic pipe name
        if pipe_name == PIPE_NAME:
            self.pipe_name = self._read_discovery_pipe_name()
        else:
            self.pipe_name = pipe_name
        self.auto_start = auto_start
        self._handle = None
        self._connected = False

    def _read_discovery_pipe_name(self) -> str:
        """Read discovery file to get current daemon pipe name."""
        try:
            if DISCOVERY_FILE.exists():
                data = json.loads(DISCOVERY_FILE.read_text())
                pipe_name = data.get("pipe_name", PIPE_NAME)
                logger.debug(f"Discovery file found: {pipe_name}")
                return pipe_name
        except Exception as e:
            logger.debug(f"Failed to read discovery file: {e}")
        return PIPE_NAME  # Fallback to hardcoded name

    def create_request(self, scope: str, query: str, limit: int = 5, **kw: Any) -> dict[str, Any]:
        """Create a request dictionary."""
        req = {"scope": scope, "query": query, "limit": limit}
        req.update(kw)
        return req

    def connect(self, timeout: float = REQUEST_TIMEOUT) -> bool:
        """Connect to the daemon pipe."""
        if not WIN32_AVAILABLE:
            return False
        s = time.time()
        while time.time() - s < timeout:
            try:
                self._handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None,
                )
                self._connected = True
                return True
            except pywintypes.error as e:
                if e.args[0] in (2, 231):  # ERROR_FILE_NOT_FOUND, ERROR_PIPE_BUSY
                    time.sleep(0.1)
                    continue
                return False
        return False

    def disconnect(self) -> None:
        """Disconnect from the daemon pipe."""
        if self._handle:
            try:
                win32file.CloseHandle(self._handle)
            except Exception:
                pass
        self._handle = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to the daemon."""
        return self._connected and self._handle is not None

    def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request and read the response.

        Auto-connects for each request since the server disconnects after
        each response (single-request-per-connection model).
        """
        # Auto-connect for each request
        if not self.is_connected():
            if not self.connect(timeout=REQUEST_TIMEOUT):
                raise ConnectionError("Failed to connect to daemon")

        data = json.dumps(request).encode("utf-8")
        msg = struct.pack("<I", len(data)) + data
        win32file.WriteFile(self._handle, msg)

        response = self._read_response()

        # Server disconnects after response, so mark as disconnected
        self._connected = False
        self._handle = None

        return (
            response
            if response
            else {
                "error": "No response",
                "results": [],
                "scope": request.get("scope", "unknown"),
            }
        )

    def send_raw(self, request: dict[str, Any]) -> dict[str, Any]:
        """Alias for send_request."""
        return self.send_request(request)

    def _read_response(self) -> dict[str, Any] | None:
        """Read the response from the pipe."""
        if not self.is_connected():
            return None
        result = win32file.ReadFile(self._handle, 4)
        # pywin32 ReadFile for named pipes returns (bytes_read, data) tuple
        if isinstance(result, tuple):
            if len(result) >= 2:
                ld = result[1] if isinstance(result[1], bytes) else result[0]
            else:
                ld = result[0]
        else:
            ld = result
        length = struct.unpack("<I", ld)[0]
        jd = b""
        rem = length
        while rem > 0:
            result = win32file.ReadFile(self._handle, min(BUF_SIZE, rem))
            if isinstance(result, tuple):
                if len(result) >= 2:
                    ch = result[1] if isinstance(result[1], bytes) else result[0]
                else:
                    ch = result[0]
            else:
                ch = result
            if not ch:
                return None
            jd += ch
            rem -= len(ch)
        return json.loads(jd.decode("utf-8"))

    def search(self, scope: str, query: str, limit: int = 10, **kw: Any) -> dict[str, Any]:
        """
        Search CKS or CHS.

        Args:
            scope: "cks" or "chs"
            query: Search query
            limit: Max results
            **kw: Additional parameters (entry_type, session_filter, etc.)

        Returns:
            Dict with results list and metadata
        """
        req = self.create_request(scope, query, limit, **kw)
        try:
            return self.send_request(req)
        except Exception as e:
            if kw.get("fallback_on_error"):
                return {
                    "results": [],
                    "scope": scope,
                    "fallback": True,
                    "source": "keyword_search",
                    "error": str(e),
                }
            return {"error": str(e), "results": [], "scope": scope}

    def classify_intent(self, text: str) -> IntentCategory:
        """Classify text into intent category.

        Thin wrapper that delegates to the daemon.
        The daemon handles all ML classification logic.

        Args:
            text: Input text to classify

        Returns:
            Intent category string

        Raises:
            ConnectionError: If semantic daemon is unavailable
        """
        import pywintypes

        request = {"action": "classify_intent", "text": text}

        try:
            response = self.send_request(request)
            return response.get("intent", "other")
        except (ConnectionError, OSError, pywintypes.error) as e:
            # Fail fast: daemon required for intent classification
            raise ConnectionError(
                f"Semantic daemon unavailable for intent classification: {e}"
            ) from e


# =============================================================================
# Daemon
# =============================================================================


class UnifiedSemanticDaemon:
    """
    Unified semantic daemon serving CKS and CHS search via named pipe.

    The daemon runs in a background thread and handles search requests
    from clients via Windows named pipes.
    """

    def __init__(self, pipe_name: str = PIPE_NAME, num_workers: int = 8):
        # Generate dynamic pipe name if using default
        if pipe_name == PIPE_NAME:
            self.pid = os.getpid()
            self.timestamp = int(time.time())
            self._pipe_name = rf"\\.\pipe\csf_semantic_{self.pid}_{self.timestamp}"
        else:
            self._pipe_name = pipe_name
            # Extract PID/timestamp if provided in dynamic format
            import re

            match = re.search(r"csf_semantic_(\d+)_(\d+)", pipe_name)
            if match:
                self.pid = int(match.group(1))
                self.timestamp = int(match.group(2))
            else:
                self.pid = os.getpid()
                self.timestamp = int(time.time())

        self._num_workers = num_workers
        self._running = False
        self._ready = False
        self._server_thread = None
        self._executor = None
        self._stop_event = threading.Event()
        self._pipe_handle = None

        # Statistics tracking
        self._last_request_time = time.time()
        self._last_staleness_update = 0
        self._last_heavy_task_time = 0
        self._last_chs_reindex_time = 0  # Track last CHS re-index
        self._last_faiss_update_time = 0  # Track last FAISS update
        self._faiss_update_enabled = True  # Enable/disable FAISS updates
        self._faiss_updating = False  # Flag to prevent concurrent FAISS updates
        self._staleness_cache = {"entries": {}, "last_updated": 0}
        self._stats_lock = threading.Lock()
        self._stats = {
            "requests_processed": 0,
            "errors": 0,
            "total_duration_ms": 0,
            "active_connections": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self._exit_code = 0

        # Lazy-loaded search backends
        self._cks = None
        self._chs = None
        self._chs_lock = threading.Lock()
        self._chs_indexing = False  # Flag to prevent concurrent indexing
        self._chs_index_lock = threading.Lock()  # Lock for indexing operation
        self._chs_index_thread = None  # Background indexing thread
        self._chs_index_complete = threading.Event()  # Signals when indexing is done

        # Lazy-loaded intent classification
        self._category_embeddings = {}
        self._intent_model = None

        # AT-006: JsonlWatcher integration
        from src.ingestion.jsonl_watcher import JsonlWatcher

        # JsonlWatcher watches the Claude chat history file
        history_jsonl_path = Path.home() / ".claude" / "history.jsonl"

        # Health check: verify history file exists before watching
        if not history_jsonl_path.exists():
            logger.warning(
                f"Chat history file does not exist: {history_jsonl_path}"
                " - JsonlWatcher will not start. CHS incremental updates disabled."
            )
            self.jsonl_watcher = None
        else:
            self.jsonl_watcher = JsonlWatcher(watch_file=history_jsonl_path)
            # Register callback for file changes and start polling
            self.jsonl_watcher._callback = self._on_jsonl_file_changed
            # Start polling for file changes
            if self.jsonl_watcher.watch_file:
                self.jsonl_watcher._start_watching()
            self._jsonl_watcher_thread = None

        # AT-002: Watch Claude Desktop conversations directory
        desktop_conversations_dir = Path("C:/Users/brsth/AppData/Roaming/Claude/conversations")
        self.desktop_jsonl_watcher = None
        if desktop_conversations_dir.exists():
            try:
                # Find the most recent JSONL file in Desktop conversations
                jsonl_files = list(desktop_conversations_dir.glob("*.jsonl"))
                if jsonl_files:
                    # Use the most recently modified file
                    desktop_jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_mtime)
                    self.desktop_jsonl_watcher = JsonlWatcher(watch_file=desktop_jsonl_path)
                    self.desktop_jsonl_watcher._callback = self._on_desktop_jsonl_file_changed
                    if self.desktop_jsonl_watcher.watch_file:
                        self.desktop_jsonl_watcher._start_watching()
                        logger.info(f"Watching Claude Desktop conversations: {desktop_jsonl_path}")
                else:
                    logger.warning(
                        f"No JSONL files found in Desktop conversations directory: "
                        f"{desktop_conversations_dir}"
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize Desktop JsonlWatcher: {e}")
        else:
            logger.warning(
                f"Claude Desktop conversations directory does not exist: "
                f"{desktop_conversations_dir}"
            )
        self._desktop_jsonl_watcher_thread = None

        # AT-003: Watch GitHub Copilot conversations directory
        # Copilot conversations are stored in VS Code's workspaceStorage
        # We watch the globalStorage location for Copilot Chat data
        copilot_conversations_dir = Path(
            "C:/Users/brsth/AppData/Roaming/Code - Insiders/User/globalStorage/github.copilot-chat"
        )
        self.copilot_jsonl_watcher = None
        if copilot_conversations_dir.exists():
            try:
                # Find the most recent JSONL file in Copilot conversations
                jsonl_files = list(copilot_conversations_dir.glob("**/*.jsonl"))
                if jsonl_files:
                    # Use the most recently modified file
                    copilot_jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_mtime)
                    self.copilot_jsonl_watcher = JsonlWatcher(watch_file=copilot_jsonl_path)
                    self.copilot_jsonl_watcher._callback = self._on_copilot_jsonl_file_changed
                    if self.copilot_jsonl_watcher.watch_file:
                        self.copilot_jsonl_watcher._start_watching()
                        logger.info(f"Watching GitHub Copilot conversations: {copilot_jsonl_path}")
                else:
                    logger.warning(
                        f"No JSONL files found in Copilot conversations directory: "
                        f"{copilot_conversations_dir}"
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize Copilot JsonlWatcher: {e}")
        else:
            logger.warning(
                f"GitHub Copilot conversations directory does not exist: "
                f"{copilot_conversations_dir}"
            )
        self._copilot_jsonl_watcher_thread = None

        # AT-006: IncrementalIndexUpdater integration - migrated to search_research package
        from search_research.backends.local.chs_incremental import (
            IncrementalIndexUpdater,
        )

        self._incremental_updater = IncrementalIndexUpdater()

        # AT-006: Watermark state persistence
        self._watermark_state = {}
        self._last_watermark_save_time = 0.0
        self._watermark_state_path = _csf_root / "data" / "watermark_state.json"

        # AT-006: JsonlWatcher health monitoring
        self._watcher_last_activity = 0.0  # Timestamp of last JsonlWatcher callback
        self._watcher_inactivity_threshold = 120.0  # Seconds before warning

        # AT-007: Query cache integration
        # Use size-bounded cache to prevent unbounded memory growth (Python's lru_cache default is 128)
        self.query_cache = QueryCache(max_size=128, ttl_seconds=3600)

        # Windows Mutex for atomic single-instance daemon determination
        # Acquire mutex to determine if this daemon instance is canonical
        self._daemon_mutex_handle = None
        self._is_canonical_daemon = False

        if WIN32_AVAILABLE:
            try:
                self._daemon_mutex_handle = win32event.CreateMutex(None, False, DAEMON_MUTEX_NAME)
                if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                    # Another daemon already owns the mutex - we are not canonical
                    # Check if the mutex owner is still alive (abandonment detection)
                    try:
                        # Try to open existing mutex to test if owner is alive
                        existing_mutex = win32event.OpenMutex(
                            win32event.EVENT_MODIFY_STATE | win32event.SYNCHRONIZE,
                            False,
                            DAEMON_MUTEX_NAME,
                        )
                        # Successfully opened mutex → owner is alive
                        win32api.CloseHandle(existing_mutex)
                        logger.info(
                            f"Daemon mutex '{DAEMON_MUTEX_NAME}' exists and owner is alive - NOT canonical"
                        )
                        self._is_canonical_daemon = False
                    except OSError as e:
                        # Cannot open mutex → owner died, take over as canonical
                        logger.info(
                            f"Daemon mutex '{DAEMON_MUTEX_NAME}' owner died (error: {e}) - taking over as canonical daemon"
                        )
                        self._is_canonical_daemon = True
                        # We'll use our mutex handle (already created above)
                else:
                    # We are the first to create the mutex - we are canonical
                    logger.info(
                        f"Acquired daemon mutex '{DAEMON_MUTEX_NAME}' - this IS the canonical daemon"
                    )
                    self._is_canonical_daemon = True
            except Exception as e:
                logger.warning(f"Failed to acquire daemon mutex: {e}")
                # On error, assume we are canonical (fail-open for safety)
                self._is_canonical_daemon = True
        else:
            # Non-Windows: assume canonical
            self._is_canonical_daemon = True

    @property
    def pipe_name(self) -> str:
        return self._pipe_name

    def _on_jsonl_file_changed(self, file_path: str) -> None:
        """Callback for JsonlWatcher to process JSONL file changes.

        This method is called when a JSONL file is detected by the watcher.
        It wires the change to the IncrementalIndexUpdater.

        Args:
            file_path: Path to the changed JSONL file
        """
        import time

        self._watcher_last_activity = time.time()  # Update activity timestamp
        try:
            # Wire to IncrementalIndexUpdater - add update_from_file if it exists
            if hasattr(self._incremental_updater, "update_from_file"):
                self._incremental_updater.update_from_file(file_path)
            else:
                # Fallback to run_incremental_update if update_from_file not available
                self._incremental_updater.run_incremental_update()
            logger.debug(f"Processed JSONL file change: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to process JSONL file change {file_path}: {e}")

    def _on_desktop_jsonl_file_changed(self, file_path: str) -> None:
        """Callback for Desktop JsonlWatcher to process Claude Desktop conversations.

        This method is called when a Claude Desktop JSONL file is detected by the watcher.
        It wires the change to the IncrementalIndexUpdater with source metadata.

        Args:
            file_path: Path to the changed JSONL file
        """
        try:
            # Read the file and add source metadata to each message
            import json
            from pathlib import Path

            desktop_file_path = Path(file_path)
            if not desktop_file_path.exists():
                logger.warning(f"Desktop JSONL file not found: {file_path}")
                return

            # Read all messages from the file
            messages_with_source = []
            try:
                with open(desktop_file_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                # Add source metadata to distinguish from CLI conversations
                                msg["_source"] = "claude-desktop"
                                messages_with_source.append(json.dumps(msg))
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.warning(f"Failed to read Desktop JSONL file {file_path}: {e}")
                return

            if not messages_with_source:
                logger.debug(f"No valid messages in Desktop JSONL file: {file_path}")
                return

            # Create a temporary file with source metadata
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_path = tmp_file.name
                for msg_json in messages_with_source:
                    tmp_file.write(msg_json + "\n")

            # Process the temporary file with the IncrementalIndexUpdater
            try:
                if hasattr(self._incremental_updater, "update_from_file"):
                    self._incremental_updater.update_from_file(tmp_path)
                else:
                    # Fallback to run_incremental_update
                    self._incremental_updater.run_incremental_update()
                logger.info(
                    f"Processed {len(messages_with_source)} messages from "
                    f"Claude Desktop: {file_path}"
                )
            finally:
                # Clean up temporary file
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to process Claude Desktop JSONL file change {file_path}: {e}")

    def _on_copilot_jsonl_file_changed(self, file_path: str) -> None:
        """Callback for Copilot JsonlWatcher to process GitHub Copilot conversations.

        This method is called when a GitHub Copilot JSONL file is detected by the watcher.
        It wires the change to the IncrementalIndexUpdater with source metadata.

        Args:
            file_path: Path to the changed JSONL file
        """
        try:
            # Read the file and add source metadata to each message
            import json
            from pathlib import Path

            copilot_file_path = Path(file_path)
            if not copilot_file_path.exists():
                logger.warning(f"Copilot JSONL file not found: {file_path}")
                return

            # Read all messages from the file
            messages_with_source = []
            try:
                with open(copilot_file_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                # Add source metadata to distinguish from CLI conversations
                                msg["_source"] = "github-copilot"
                                messages_with_source.append(json.dumps(msg))
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.warning(f"Failed to read Copilot JSONL file {file_path}: {e}")
                return

            if not messages_with_source:
                logger.debug(f"No valid messages in Copilot JSONL file: {file_path}")
                return

            # Create a temporary file with source metadata
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_path = tmp_file.name
                for msg_json in messages_with_source:
                    tmp_file.write(msg_json + "\n")

            # Process the temporary file with the IncrementalIndexUpdater
            try:
                if hasattr(self._incremental_updater, "update_from_file"):
                    self._incremental_updater.update_from_file(tmp_path)
                else:
                    # Fallback to run_incremental_update
                    self._incremental_updater.run_incremental_update()
                logger.info(
                    f"Processed {len(messages_with_source)} messages from "
                    f"GitHub Copilot: {file_path}"
                )
            finally:
                # Clean up temporary file
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to process GitHub Copilot JSONL file change {file_path}: {e}")

    def _persist_watermark_state(self) -> None:
        """Persist watermark state to disk.

        This method saves the current watermark state to a JSON file
        for recovery after daemon restart.
        """
        try:
            import json

            self._watermark_state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._watermark_state_path, "w", encoding="utf-8") as f:
                json.dump(self._watermark_state, f, indent=2)
            self._last_watermark_save_time = time.time()
            logger.debug(f"Watermark state persisted to {self._watermark_state_path}")
        except Exception as e:
            logger.warning(f"Failed to persist watermark state: {e}")

    def _log_to_file(self, message: str) -> None:
        """Log message to debug file for diagnosing silent thread crashes.

        This is essential for pythonw.exe which has no console/stderr.
        """
        try:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(DAEMON_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass  # Never let logging crash the daemon

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def start(self) -> bool:
        """Start the daemon server."""
        if self._running:
            return True
        if not WIN32_AVAILABLE:
            logger.warning("Cannot start daemon: win32file not available")
            return False

        # AT-010: Age-based self-termination check
        # Old daemons that are not the canonical daemon should exit gracefully
        if self._should_terminate_based_on_age():
            age = int(time.time() - self.timestamp)
            logger.info(
                f"Daemon self-terminating: age={age}s (>MAX_DAEMON_AGE={MAX_DAEMON_AGE}s), "
                f"pid={self.pid} is not the canonical daemon"
            )
            return False

        self._stop_event.clear()
        self._running = True
        self._ready = False

        # Check if another daemon is already running via discovery file
        # This prevents multiple daemon instances from running simultaneously
        discovery_file = _csf_root / "data" / "semantic_daemon_discovery.json"
        if discovery_file.exists():
            try:
                import json

                data = json.loads(discovery_file.read_text())
                existing_pid = data.get("pid")
                existing_pipe = data.get("pipe_name", "")

                if existing_pid and existing_pid != self.pid:
                    logger.warning(
                        f"Another daemon is already running (pid={existing_pid}, pipe={existing_pipe}). "
                        f"This instance (pid={self.pid}) will NOT start server loop."
                    )
                    self._running = False
                    return False
            except (OSError, ValueError, json.JSONDecodeError):
                # Corrupted discovery file - treat as no daemon running
                pass

        # Clean up stale PID files from previous daemon instances
        # This prevents accumulation of csf_semantic_*.pid files
        self._cleanup_stale_pid_files()

        # Initialize thread pool for concurrent request handling
        self._executor = ThreadPoolExecutor(max_workers=self._num_workers)

        # Start server loop in background thread with exception wrapper
        def _wrapped_server_loop():
            """Wrapper to catch and log any unhandled exceptions in thread."""
            try:
                self._log_to_file("[THREAD] Server loop starting...")
                self._server_loop()
            except Exception as e:
                import traceback

                self._log_to_file(f"[THREAD CRASH] Unhandled exception: {e}")
                self._log_to_file(traceback.format_exc())
                self._running = False
                self._ready = False
                raise

        self._server_thread = threading.Thread(
            target=_wrapped_server_loop, daemon=True, name="SemanticDaemon"
        )
        self._server_thread.start()

        # AT-006: Start JsonlWatcher thread for JSONL file detection
        def _jsonl_watcher_loop():
            """Wrapper for JsonlWatcher watch loop."""
            import time

            # Keep the thread alive with a retry loop
            while self._running:
                try:
                    # Watch the data directory for JSONL changes
                    jsonl_dir = str(_csf_root / "data")
                    if self.jsonl_watcher:
                        self.jsonl_watcher.watch(jsonl_dir, self._on_jsonl_file_changed)
                    else:
                        # JsonlWatcher not initialized (file missing)
                        time.sleep(5)  # Wait before retry
                        break
                except Exception as e:
                    # In production, watch() blocks indefinitely on ReadDirectoryChangesW
                    # If it exits, log and retry (with backoff to avoid tight loop)
                    if self._running:  # Only log if we're supposed to be running
                        logger.debug(f"JsonlWatcher watch exited: {e}")
                        time.sleep(1)  # Brief pause before retry
                    else:
                        # Exiting gracefully
                        break

        self._jsonl_watcher_thread = threading.Thread(
            target=_jsonl_watcher_loop, daemon=True, name="JsonlWatcher"
        )
        self._jsonl_watcher_thread.start()

        # AT-002: Start Desktop JsonlWatcher thread for Claude Desktop conversations
        if self.desktop_jsonl_watcher:

            def _desktop_jsonl_watcher_loop():
                """Wrapper for Desktop JsonlWatcher watch loop."""
                import time

                # Keep the thread alive with a retry loop
                while self._running:
                    try:
                        # Watch the Desktop conversations directory for JSONL changes
                        desktop_conversations_dir = (
                            "C:/Users/brsth/AppData/Roaming/Claude/conversations"
                        )
                        self.desktop_jsonl_watcher.watch(
                            desktop_conversations_dir,
                            self._on_desktop_jsonl_file_changed,
                        )
                    except Exception as e:
                        # In production, watch() blocks indefinitely on ReadDirectoryChangesW
                        # If it exits, log and retry (with backoff to avoid tight loop)
                        if self._running:  # Only log if we're supposed to be running
                            logger.debug(f"Desktop JsonlWatcher watch exited: {e}")
                            time.sleep(1)  # Brief pause before retry
                        else:
                            # Exiting gracefully
                            break

            self._desktop_jsonl_watcher_thread = threading.Thread(
                target=_desktop_jsonl_watcher_loop,
                daemon=True,
                name="DesktopJsonlWatcher",
            )
            self._desktop_jsonl_watcher_thread.start()
            logger.info("Desktop JsonlWatcher thread started")
        else:
            self._desktop_jsonl_watcher_thread = None

        # AT-003: Start Copilot JsonlWatcher thread for GitHub Copilot conversations
        if self.copilot_jsonl_watcher:

            def _copilot_jsonl_watcher_loop():
                """Wrapper for Copilot JsonlWatcher watch loop."""
                import time

                # Keep the thread alive with a retry loop
                while self._running:
                    try:
                        # Watch the Copilot conversations directory for JSONL changes
                        copilot_conversations_dir = "C:/Users/brsth/AppData/Roaming/Code - Insiders/User/globalStorage/github.copilot-chat"
                        self.copilot_jsonl_watcher.watch(
                            copilot_conversations_dir,
                            self._on_copilot_jsonl_file_changed,
                        )
                    except Exception as e:
                        # In production, watch() blocks indefinitely on ReadDirectoryChangesW
                        # If it exits, log and retry (with backoff to avoid tight loop)
                        if self._running:  # Only log if we're supposed to be running
                            logger.debug(f"Copilot JsonlWatcher watch exited: {e}")
                            time.sleep(1)  # Brief pause before retry
                        else:
                            # Exiting gracefully
                            break

            self._copilot_jsonl_watcher_thread = threading.Thread(
                target=_copilot_jsonl_watcher_loop,
                daemon=True,
                name="CopilotJsonlWatcher",
            )
            self._copilot_jsonl_watcher_thread.start()
            logger.info("Copilot JsonlWatcher thread started")
        else:
            self._copilot_jsonl_watcher_thread = None

        # Wait for ready state
        s = time.time()
        while time.time() - s < STARTUP_TIMEOUT:
            if self._ready:
                logger.info(f"Semantic daemon ready: {self._pipe_name}")
                # Schedule CHS indexing on daemon startup (deferred to idle work)
                # Don't block startup - will happen during first idle period
                self._last_chs_reindex_time = 0  # Force re-index on next idle check
                logger.info("CHS re-index scheduled for next idle period")
                return True
            time.sleep(0.1)

        logger.error("Daemon failed to reach ready state within timeout")
        self._running = False
        return False

    def stop(self, force: bool = False) -> None:
        """Stop the daemon server."""
        if not self._running:
            return

        logger.info("Stopping semantic daemon...")
        self._running = False
        self._stop_event.set()

        # Close pipe handle
        if self._pipe_handle:
            try:
                win32file.CloseHandle(self._pipe_handle)
            except Exception:
                pass
            self._pipe_handle = None

        # Wait for server thread to finish
        if self._server_thread:
            self._server_thread.join(timeout=2.0)

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=not force)

        # Clean up discovery file to prevent zombie accumulation
        self._cleanup_discovery_file()

        # Clean up PID file to prevent stale accumulation
        self._cleanup_pid_file()

        # Release daemon mutex if we own it
        if self._daemon_mutex_handle and self._is_canonical_daemon:
            try:
                win32api.CloseHandle(self._daemon_mutex_handle)
                logger.info(f"Released daemon mutex '{DAEMON_MUTEX_NAME}'")
            except Exception:
                pass
            self._daemon_mutex_handle = None

        self._ready = False
        logger.info("Semantic daemon stopped")

    def shutdown(self, wait_for_requests: bool = True, timeout: float = 5.0) -> bool:
        """Graceful shutdown."""
        self.stop()
        return True

    def is_running(self) -> bool:
        return self._running

    def is_ready(self) -> bool:
        return self._running and self._ready

    def search(self, scope: str, query: str, limit: int = 10, **kw: Any) -> dict[str, Any]:
        """
        Search CKS or CHS.

        This is a convenience method that delegates to the internal search methods.
        It allows the daemon to be used as a search backend directly.

        Args:
            scope: "cks" or "chs"
            query: Search query
            limit: Max results
            **kw: Additional parameters (entry_type, session_filter, etc.)

        Returns:
            Dict with results list and metadata
        """
        if scope == "cks":
            results = self._search_cks(query, limit, kw)
            return {"scope": "cks", "results": results, "query": query}
        elif scope == "chs":
            results = self._search_chs(query, limit, kw)
            return {"scope": "chs", "results": results, "query": query}
        else:
            return {"error": f"Unknown scope: {scope}", "results": [], "scope": scope}

    def pipe_exists(self) -> bool:
        """Check if the named pipe exists."""
        if not WIN32_AVAILABLE:
            return False
        try:
            win32file.CreateFile(
                self._pipe_name,
                win32file.GENERIC_READ,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )
            return True
        except pywintypes.error:
            return False

    def create_client(self) -> SemanticClient:
        """Create a new client instance."""
        return SemanticClient(auto_start=False)

    # -------------------------------------------------------------------------
    # Statistics and monitoring
    # -------------------------------------------------------------------------

    def get_statistics(self) -> dict[str, Any]:
        with self._stats_lock:
            return self._stats.copy()

    def get_active_connection_count(self) -> int:
        return self._stats.get("active_connections", 0)

    def get_queue_size(self) -> int:
        return 0  # No queue in current implementation

    def get_idle_seconds(self) -> float:
        return time.time() - self._last_request_time

    def _set_idle_time(self, seconds: float) -> None:
        self._last_request_time = time.time() - seconds

    def get_last_staleness_cache_update(self) -> float:
        return self._last_staleness_update

    def get_staleness_cache(self) -> dict[str, Any]:
        return self._staleness_cache.copy()

    def update_staleness_cache(self) -> None:
        self._last_staleness_update = time.time()

    def get_type_half_lives(self) -> dict[str, int]:
        return TYPE_HALF_LIVES.copy()

    def check_idle_work(self) -> None:
        """Check and perform idle work if needed."""
        self._log_to_file("[IDLE] check_idle_work() started")
        idle = self.get_idle_seconds()
        self._log_to_file(f"[IDLE] Idle seconds: {idle:.0f}")

        # Memory cap check: self-terminate if exceeding configured limit
        # Uses global MAX_MEMORY_MB constant (currently 6GB to handle all models)
        # Based on StackOverflow: https://stackoverflow.com/questions/21237833
        try:
            self._log_to_file("[IDLE] Checking memory cap...")
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            # Use global MAX_MEMORY_MB, not local override
            self._log_to_file(f"[IDLE] Memory: {memory_mb:.0f}MB / {MAX_MEMORY_MB}MB")
            if memory_mb > MAX_MEMORY_MB:
                # Use _log_to_file instead of logger.error to avoid stderr blocking
                self._log_to_file(
                    f"[IDLE] ⚠️  MEMORY CAP EXCEEDED: {memory_mb:.0f}MB > {MAX_MEMORY_MB}MB - self-terminating"
                )
                self._running = False
                return
            self._log_to_file("[IDLE] Memory cap OK, continuing")
        except Exception as e:
            logger.warning(f"Memory check failed: {e}")

        # CHS re-indexing: every 5 minutes of idle time (not tied to long idle)
        self._log_to_file("[IDLE] Checking if CHS re-index needed...")
        time_since_reindex = time.time() - self._last_chs_reindex_time
        self._log_to_file(
            f"[IDLE] Time since re-index: {time_since_reindex:.0f}s / {CHS_REINDEX_INTERVAL:.0f}s"
        )
        if time_since_reindex > CHS_REINDEX_INTERVAL:
            self._log_to_file("[IDLE] CHS re-index triggered - calling _ensure_chs_indexed()...")
            try:
                self._ensure_chs_indexed()
                self._log_to_file("[IDLE] CHS re-index completed successfully")
                self._last_chs_reindex_time = time.time()
                logger.info(f"CHS re-index triggered (idle for {idle:.0f}s)")
            except Exception as e:
                logger.warning(f"CHS re-index failed: {e}")

        # FAISS update check: every 10 minutes of idle time
        if self._faiss_update_enabled:
            time_since_faiss = time.time() - self._last_faiss_update_time
            if time_since_faiss > FAISS_UPDATE_INTERVAL and not self._faiss_updating:
                try:
                    self._ensure_chs_indexed()  # Cascades to FAISS update
                    logger.info(f"FAISS update triggered (idle for {idle:.0f}s)")
                except Exception as e:
                    logger.warning(f"FAISS update trigger failed: {e}")

        # Heavy maintenance: staleness cache (only after long idle)
        if idle > IDLE_WORK_LONG:
            self.update_staleness_cache()
            self._last_heavy_task_time = time.time()

        # AT-006: Watermark state persistence every 10 seconds
        time_since_watermark_save = time.time() - self._last_watermark_save_time
        if time_since_watermark_save > 10.0:
            try:
                self._persist_watermark_state()
                logger.debug(f"Watermark state persisted (idle for {idle:.0f}s)")
            except Exception as e:
                logger.warning(f"Watermark state persistence failed: {e}")

        # AT-006: JsonlWatcher health monitoring
        if self.jsonl_watcher and self._watcher_last_activity > 0:
            time_since_watcher_activity = time.time() - self._watcher_last_activity
            if time_since_watcher_activity > self._watcher_inactivity_threshold:
                logger.warning(
                    f"JsonlWatcher inactive for {time_since_watcher_activity:.0f}s - "
                    "incremental CHS updates may have stopped. "
                    "Run '/daemon restart' to recover."
                )
                # Reset to avoid spamming warnings
                self._watcher_last_activity = time.time()

    def last_heavy_task_time(self) -> float:
        return self._last_heavy_task_time

    def get_chs_index_status(self) -> dict[str, Any]:
        """Get CHS index status for health monitoring.

        Returns:
            Dict with indexing state information
        """
        db_path = self._get_chs_db_path()
        last_id = self._get_last_indexed_id()

        # Get count of CHS entries in CKS
        cks = self._get_cks()
        chs_count = 0
        if cks is not None:
            try:
                with cks.conn:
                    cursor = cks.conn.execute(
                        """SELECT COUNT(*) FROM entries
                           WHERE json_extract(metadata, '$.source') = 'chs'"""
                    )
                    chs_count = cursor.fetchone()[0]
            except Exception:
                pass

        return {
            "db_exists": db_path.exists(),
            "db_path": str(db_path),
            "last_indexed_id": last_id,
            "chs_entries_in_cks": chs_count,
            "indexing_in_progress": self._chs_indexing,
            "last_reindex_time": self._last_chs_reindex_time,
            "time_since_reindex": (
                time.time() - self._last_chs_reindex_time if self._last_chs_reindex_time > 0 else 0
            ),
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get unified health status for CKS/CHS/FAISS subsystems.

        Returns:
            Dict with health status for all subsystems and overall status.
        """
        import time

        # FAISS staleness check
        faiss_stale_secs = (
            time.time() - self._last_faiss_update_time if self._last_faiss_update_time > 0 else 0
        )
        faiss_stale_days = faiss_stale_secs / 86400

        # Determine FAISS status based on staleness
        if faiss_stale_days < 1:
            faiss_status = "fresh"
        elif faiss_stale_days < 7:
            faiss_status = "stale"
        else:
            faiss_status = "critical"

        # Get FAISS vector count
        faiss_vector_count = 0
        faiss_healthy = True
        try:
            from src.core.faiss_vector_store import FAISSVectorStore

            store = FAISSVectorStore(index_path=str(FAISS_INDEX_PATH))
            if store._loaded:
                info = store.get_collection_info()
                faiss_vector_count = info.get("vectors_count", 0)
            else:
                faiss_healthy = False
        except Exception:
            faiss_healthy = False

        # Determine overall status
        overall = "healthy"
        if faiss_status == "critical" or not faiss_healthy:
            overall = "degraded"
        elif faiss_status == "stale":
            overall = "degraded"

        # Get CKS entry count
        cks_entries_count = 0
        if self._cks is not None:
            try:
                stats = self._cks.get_statistics()
                cks_entries_count = stats.get("total_entries", 0)
            except Exception:
                cks_entries_count = 0

        return {
            "faiss": {
                "healthy": faiss_healthy,
                "index_exists": FAISS_INDEX_PATH.exists(),
                "vector_count": faiss_vector_count,
                "last_update": self._last_faiss_update_time,
                "staleness_days": faiss_stale_days,
                "status": faiss_status,
            },
            "chs": self.get_chs_index_status(),
            "cks": {
                "healthy": self._cks is not None,
                "entries_count": cks_entries_count,
            },
            "overall": overall,
        }

    def handle_shutdown_signal(self, signal_name: str) -> None:
        logger.info(f"Received signal {signal_name}, shutting down")
        self.shutdown()

    def exit_code(self) -> int:
        return self._exit_code

    # -------------------------------------------------------------------------
    # Server loop
    # -------------------------------------------------------------------------

    def _cleanup_stale_pipe(self) -> None:
        """
        Attempt to clean up stale pipe handle from crashed daemon.

        If a previous daemon crashed without properly closing the pipe,
        Windows may retain the handle. Try to open and close it.
        """
        if not WIN32_AVAILABLE:
            return

        try:
            handle = win32file.CreateFile(
                self._pipe_name,
                win32file.GENERIC_READ,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )
            # If we can open it, close it to release the handle
            win32file.CloseHandle(handle)
            logger.info("Cleaned up stale pipe handle")
        except pywintypes.error as e:
            # ERROR_FILE_NOT_FOUND (2) is expected - pipe doesn't exist yet
            if e.args[0] != 2:
                logger.debug(f"Cleanup check (pipe not stale): {e}")
        except Exception as e:
            logger.debug(f"Cleanup check: {e}")

    def _write_discovery_file(self) -> None:
        """Write discovery file with current pipe info for clients to find."""
        try:
            DISCOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
            discovery_data = {
                "pipe_name": self._pipe_name,
                "pid": self.pid,
                "timestamp": self.timestamp,
            }
            DISCOVERY_FILE.write_text(json.dumps(discovery_data, indent=2))
            logger.info(f"Discovery file written: {DISCOVERY_FILE}")
        except Exception as e:
            logger.warning(f"Failed to write discovery file: {e}")

    def _cleanup_discovery_file(self) -> None:
        """Clean up discovery file on daemon shutdown to prevent zombie accumulation."""
        try:
            if DISCOVERY_FILE.exists():
                # Verify this is our discovery file (matches our PID)
                try:
                    data = json.loads(DISCOVERY_FILE.read_text())
                    if data.get("pid") == self.pid:
                        DISCOVERY_FILE.unlink(missing_ok=True)
                        logger.info(f"Discovery file cleaned up: {DISCOVERY_FILE}")
                except (json.JSONDecodeError, OSError):
                    # Corrupted discovery file - clean it up
                    DISCOVERY_FILE.unlink(missing_ok=True)
                    logger.info(f"Corrupted discovery file cleaned up: {DISCOVERY_FILE}")
        except Exception as e:
            logger.warning(f"Failed to clean up discovery file: {e}")

    def _should_terminate_based_on_age(self) -> bool:
        """Check if daemon should self-terminate based on age and discovery file.

        Returns:
            True if daemon is older than MAX_DAEMON_AGE AND this daemon's PID
            is NOT the canonical daemon in the discovery file.
            False otherwise (young daemon OR is the canonical daemon).
        """
        current_time = time.time()
        age = current_time - self.timestamp

        # If daemon is young, always continue running
        if age < MAX_DAEMON_AGE:
            return False

        # Daemon is old - check if we are the canonical daemon
        try:
            if DISCOVERY_FILE.exists():
                data = json.loads(DISCOVERY_FILE.read_text())
                canonical_pid = data.get("pid")
                # If we ARE the canonical daemon, continue running
                if canonical_pid == self.pid:
                    return False
        except (json.JSONDecodeError, OSError):
            # Discovery file corrupted - treat as not canonical
            pass

        # Old daemon and not the canonical one - should terminate
        return True

    def _detect_all_daemon_processes(self) -> list[dict[str, Any]]:
        """Detect all unified_semantic_daemon.py processes currently running.

        Returns:
            List of dicts containing 'pid', 'age_hours', and 'cmdline' for each daemon process.
        """
        daemons = []
        current_time = time.time()

        try:
            for proc in psutil.process_iter(["pid", "create_time", "cmdline"]):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get("cmdline", [])

                    # Check if this is a unified_semantic_daemon.py process
                    if cmdline and any("unified_semantic_daemon.py" in arg for arg in cmdline):
                        pid = proc_info["pid"]
                        create_time = proc_info.get("create_time", current_time)

                        # Calculate age in hours
                        age_seconds = current_time - create_time
                        age_hours = age_seconds / 3600

                        daemons.append({"pid": pid, "age_hours": age_hours, "cmdline": cmdline})
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    # Process ended or access denied - skip it
                    continue
        except Exception as e:
            logger.warning(f"Failed to detect daemon processes: {e}")

        return daemons

    def _aggressive_cleanup_zombies(self) -> int:
        """Aggressively clean up zombie daemon processes.

        Kills all daemon processes except:
        - The discovery file PID (canonical daemon)
        - Processes younger than grace period (5 minutes)

        Returns:
            Count of processes killed.
        """
        killed_count = 0
        canonical_pid = None

        # Get canonical PID from discovery file
        try:
            if DISCOVERY_FILE.exists():
                data = json.loads(DISCOVERY_FILE.read_text())
                canonical_pid = data.get("pid")
        except (json.JSONDecodeError, OSError):
            # Discovery file corrupted - no canonical PID
            pass

        # Detect all daemon processes
        daemons = self._detect_all_daemon_processes()

        for daemon_info in daemons:
            pid = daemon_info["pid"]

            # Skip if this is the canonical daemon
            if canonical_pid is not None and pid == canonical_pid:
                continue

            # Skip if this is the current process
            if pid == self.pid:
                continue

            # Kill the zombie process (no grace period - mutex-based approach)
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                killed_count += 1
                logger.info(f"Killed zombie daemon process: pid={pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process already ended or access denied
                continue

        return killed_count

    def _write_pid_file(self, path: Path | None = None) -> None:
        """Write PID file atomically using temp file + rename pattern.

        Args:
            path: Optional path for PID file. Defaults to derived path from PID/timestamp.
        """
        try:
            # Use provided path or derive from PID/timestamp
            if path is None:
                # Use dynamic PID file name matching the pipe name pattern
                path = _csf_root / "data" / f"csf_semantic_{self.pid}_{self.timestamp}.pid"

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Create temp file with PID in name for atomic write
            temp_file = path.with_suffix(f".tmp.{self.pid}")

            # Write PID to temp file first
            temp_file.write_text(str(self.pid))

            # Atomic rename to final path
            os.replace(temp_file, path)

            logger.info(f"PID file written: {path}")
        except Exception as e:
            logger.warning(f"Failed to write PID file: {e}")

    def _cleanup_pid_file(self) -> None:
        """Clean up PID file on daemon shutdown to prevent stale accumulation."""
        try:
            # Clean up the dynamic PID file for this instance
            pid_file = _csf_root / "data" / f"csf_semantic_{self.pid}_{self.timestamp}.pid"
            if pid_file.exists():
                # Verify this is our PID file (matches our PID)
                try:
                    pid_content = pid_file.read_text().strip()
                    if pid_content == str(self.pid):
                        pid_file.unlink(missing_ok=True)
                        logger.info(f"PID file cleaned up: {pid_file}")
                except (OSError, ValueError):
                    # Corrupted or unreadable PID file - clean it up
                    pid_file.unlink(missing_ok=True)
                    logger.info(f"Corrupted PID file cleaned up: {pid_file}")
        except Exception as e:
            logger.warning(f"Failed to clean up PID file: {e}")

    def _cleanup_stale_pid_files(self) -> None:
        """Clean up stale PID files from previous daemon instances on startup.

        Stale PID files accumulate when daemons crash or are killed without proper shutdown.
        This method cleans up PID files from old daemon instances on startup.
        """
        import psutil

        try:
            data_dir = _csf_root / "data"
            stale_files = []
            active_pids = {p.pid for p in psutil.process_iter(["pid"])}

            # Find all csf_semantic_*.pid files
            for pid_file in data_dir.glob("csf_semantic_*.pid"):
                # Skip our own PID file
                if f"csf_semantic_{self.pid}_{self.timestamp}.pid" in pid_file.name:
                    continue

                # Check if PID in file is still running
                try:
                    pid_content = pid_file.read_text().strip()
                    pid = int(pid_content)

                    # If PID is not running, this is a stale file
                    if pid not in active_pids:
                        stale_files.append(pid_file)
                        logger.info(
                            f"Found stale PID file: {pid_file.name} (PID {pid} not running)"
                        )
                except (OSError, ValueError):
                    # Corrupted PID file - treat as stale
                    stale_files.append(pid_file)
                    logger.info(f"Found corrupted PID file: {pid_file.name}")

            # Remove stale files
            for stale_file in stale_files:
                try:
                    stale_file.unlink(missing_ok=True)
                    logger.info(f"Cleaned up stale PID file: {stale_file.name}")
                except OSError as e:
                    logger.warning(f"Failed to remove stale PID file {stale_file.name}: {e}")

            if stale_files:
                logger.info(f"Cleaned up {len(stale_files)} stale PID file(s)")
            else:
                logger.debug("No stale PID files to clean up")

        except Exception as e:
            logger.warning(f"Failed to clean up stale PID files: {e}")

    def _server_loop(self) -> None:
        """
        Main server loop - creates named pipe and handles connections.

        The daemon creates a named pipe and waits for client connections.
        Each request is read, processed, and a response is sent back.
        """
        if not WIN32_AVAILABLE:
            logger.error("Cannot run server loop: win32file not available")
            return

        logger.info(f"Starting server loop on {self._pipe_name}")

        # Clean up stale pipe handle from previous crash (if any)
        self._cleanup_stale_pipe()

        # Create named pipe with exponential backoff retry
        RETRY_DELAYS = [0.1, 0.2, 0.4, 0.8, 1.0]  # Exponential backoff
        pipe_created = False

        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                logger.info(f"Creating pipe (attempt {attempt + 1}/{len(RETRY_DELAYS)})")
                self._pipe_handle = win32pipe.CreateNamedPipe(
                    self._pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                    win32pipe.PIPE_TYPE_MESSAGE
                    | win32pipe.PIPE_READMODE_MESSAGE
                    | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    MAX_PIPE_SIZE,  # Output buffer size
                    MAX_PIPE_SIZE,  # Input buffer size
                    int(REQUEST_TIMEOUT * 1000),  # Timeout in ms (must be int)
                    None,
                )
                logger.info("Named pipe created successfully")
                pipe_created = True
                # Write discovery file immediately after CreateNamedPipe succeeds
                # This allows startup hooks to find the pipe name before ConnectNamedPipe loop
                self._write_discovery_file()
                self._write_pid_file()  # Keep PID file in sync with discovery file
                logger.info(
                    f"Discovery file written after CreateNamedPipe - "
                    f"pipe {self._pipe_name} created, waiting for ConnectNamedPipe"
                )
                break
            except pywintypes.error as e:
                if attempt < len(RETRY_DELAYS) - 1:
                    logger.warning(
                        f"Pipe creation failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Pipe creation failed after {len(RETRY_DELAYS)} attempts: {e}")
                    self._running = False
                    return

        if not pipe_created:
            logger.error("Failed to create pipe after all retries")
            self._running = False
            return

        self._ready = True
        logger.info("Named pipe created, waiting for connections...")
        self._log_to_file(f"[LOOP] Entering main loop, pipe={self._pipe_name}")
        loop_iteration = 0
        discovery_file_written = False  # Track whether discovery file has been written

        # Create overlapped structure for non-blocking ConnectNamedPipe
        # This is critical to prevent the daemon from blocking indefinitely
        import win32event

        overlapped = pywintypes.OVERLAPPED()
        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
        CONNECTION_TIMEOUT_MS = 1000  # 1 second timeout for connection check

        try:
            while self._running:
                loop_iteration += 1
                if loop_iteration <= 3:  # Log first 3 iterations for debugging
                    self._log_to_file(f"[LOOP] Iteration {loop_iteration} starting")
                try:
                    # Reset event for new connection attempt
                    win32event.ResetEvent(overlapped.hEvent)

                    # Non-blocking ConnectNamedPipe with overlapped I/O
                    try:
                        win32pipe.ConnectNamedPipe(self._pipe_handle, overlapped)
                    except pywintypes.error as e:
                        # ERROR_IO_PENDING (997) is expected for async operation
                        # ERROR_PIPE_CONNECTED (535) means client already connected
                        if e.winerror == 997:  # ERROR_IO_PENDING
                            pass  # This is expected, wait for connection below
                        elif e.winerror == 535:  # ERROR_PIPE_CONNECTED
                            pass  # Client already connected, proceed
                        else:
                            raise

                    # Discovery file now written after CreateNamedPipe (above)
                    # First successful ConnectNamedPipe completed - pipe is now listening
                    logger.info(f"Pipe {self._pipe_name} is now listening for connections")
                    # Wait for connection with timeout
                    result = win32event.WaitForSingleObject(
                        overlapped.hEvent, CONNECTION_TIMEOUT_MS
                    )

                    if result == win32event.WAIT_TIMEOUT:
                        # No client connected within timeout
                        # Perform idle work and check for shutdown
                        try:
                            self.check_idle_work()
                        except Exception as e:
                            logger.warning(f"Idle work check failed: {e}")
                        continue  # Loop back to check self._running

                    if result != win32event.WAIT_OBJECT_0:
                        # Error waiting
                        logger.warning(f"WaitForSingleObject returned: {result}")
                        time.sleep(0.1)
                        continue

                    # Client connected! Read and process request
                    request = self._read_request(self._pipe_handle)
                    if request:
                        start = time.time()
                        try:
                            response = self._process_request(request)
                            duration_ms = int((time.time() - start) * 1000)
                            response["duration_ms"] = duration_ms
                            response["scope"] = request.get("scope", "unknown")
                        except Exception as e:
                            logger.exception(f"Error processing request: {e}")
                            response = {
                                "results": [],
                                "scope": request.get("scope", "unknown"),
                                "error": str(e),
                                "duration_ms": int((time.time() - start) * 1000),
                            }
                            with self._stats_lock:
                                self._stats["errors"] += 1

                        # Send response
                        if self._write_response(self._pipe_handle, response):
                            win32file.FlushFileBuffers(self._pipe_handle)

                        with self._stats_lock:
                            self._stats["requests_processed"] += 1
                            self._stats["total_duration_ms"] += response.get("duration_ms", 0)

                        self._last_request_time = time.time()

                    # Disconnect client
                    try:
                        win32pipe.DisconnectNamedPipe(self._pipe_handle)
                    except Exception:
                        pass

                    # Perform idle work (CHS re-indexing, staleness cache updates)
                    try:
                        self.check_idle_work()
                    except Exception as e:
                        logger.warning(f"Idle work check failed: {e}")

                except Exception as e:
                    if self._running:
                        logger.warning(f"Error in server loop: {e}")
                    # Brief pause before retry
                    time.sleep(0.1)

        finally:
            # Clean up overlapped event
            try:
                win32event.CloseHandle(overlapped.hEvent)
            except Exception:
                pass

        logger.info("Server loop ended")

    # -------------------------------------------------------------------------
    # Pipe I/O
    # -------------------------------------------------------------------------

    def _read_request(self, pipe: Any) -> dict[str, Any] | None:
        """
        Read a length-prefixed JSON request from the pipe.

        Format: 4-byte little-endian length prefix + JSON data
        """
        try:
            # Read length prefix
            # pywin32 ReadFile for named pipes returns (bytes_read, data) tuple
            result = win32file.ReadFile(pipe, 4)
            if isinstance(result, tuple):
                if len(result) >= 2:
                    # Format: (bytes_read, data) - data is at index 1
                    ld = result[1] if isinstance(result[1], bytes) else result[0]
                else:
                    ld = result[0]
            else:
                ld = result
            length = struct.unpack("<I", ld)[0]

            # Read JSON data
            jd = b""
            rem = length
            while rem > 0:
                result = win32file.ReadFile(pipe, min(BUF_SIZE, rem))
                if isinstance(result, tuple):
                    if len(result) >= 2:
                        ch = result[1] if isinstance(result[1], bytes) else result[0]
                    else:
                        ch = result[0]
                else:
                    ch = result
                if not ch:
                    return None
                jd += ch
                rem -= len(ch)

            return json.loads(jd.decode("utf-8"))

        except Exception as e:
            logger.warning(f"Error reading request: {e}")
            return None

    def _serialize_json(self, obj: Any) -> Any:
        """Convert numpy types to native Python types for JSON serialization.

        Handles:
        - numpy.float32/float64 -> float
        - numpy.int32/int64 -> int
        - numpy.ndarray -> list
        """
        import numpy as np

        if isinstance(obj, dict):
            return {k: self._serialize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_json(item) for item in obj]
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return self._serialize_json(obj.tolist())
        else:
            return obj

    def _write_response(self, pipe: Any, response: dict[str, Any]) -> bool:
        """
        Write a length-prefixed JSON response to the pipe.

        Format: 4-byte little-endian length prefix + JSON data
        """
        try:
            # Convert numpy types to native Python types
            serializable = self._serialize_json(response)
            data = json.dumps(serializable).encode("utf-8")
            msg = struct.pack("<I", len(data)) + data
            win32file.WriteFile(pipe, msg)
            return True
        except Exception as e:
            logger.warning(f"Error writing response: {e}")
            return False

    # -------------------------------------------------------------------------
    # Request processing
    # -------------------------------------------------------------------------

    def _process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Process a search or intent classification request.

        Routes to CKS or CHS search based on scope, or to intent classification.
        """
        action = request.get("action", "search")

        # Route to health check if requested (AT-009)
        if action == "health":
            return self._handle_health_check()

        # Route to intent classification if requested
        if action == "classify_intent":
            text = request.get("text", "")
            if not text.strip():
                return {"intent": "other", "confidence": 0.0, "error": "Empty text"}
            return self._classify_intent(text)

        # Route to skill intent validation (v3.2)
        if action == "skill_intent":
            command = request.get("command", "")
            skill = request.get("skill", "")
            if not command.strip() or not skill:
                return {
                    "match": False,
                    "similarity": 0.0,
                    "threshold": 0.75,
                    "error": "Missing command or skill",
                }
            return self._handle_skill_intent(command, skill)

        # Route to compute embedding (for shared semantic trigger detection)
        if action == "compute_embedding":
            text = request.get("text", "")
            if not text.strip():
                return {"embedding": [], "model": "all-MiniLM-L6-v2", "error": "Empty text"}
            return self._handle_compute_embedding(text)

        # Support both "scope" (SemanticClient) and "backend" (DaemonClient)
        scope = request.get("scope") or request.get("backend", "cks")
        query = request.get("query", "")
        limit = request.get("limit", 5)

        # Trim whitespace and check for empty query
        query = query.strip() if isinstance(query, str) else str(query)
        if not query:
            return {"results": [], "error": "Empty query", "scope": scope}

        # Extract additional parameters (exclude both scope/backend and standard keys)
        params = {
            k: v for k, v in request.items() if k not in ("scope", "backend", "query", "limit")
        }

        # Execute search
        results = self._execute_search(scope, query, limit, params)

        return {"results": results, "scope": scope}

    def _handle_health_check(self) -> dict[str, Any]:
        """Handle health check requests (AT-009).

        Returns:
            Dict with health status including:
            - status: "healthy" or "degraded"
            - db_path: Path to chat history DB
            - faiss_path: Path to FAISS index
            - db_exists: True if DB exists
            - faiss_exists: True if FAISS exists
            - watermark_age_seconds: Age of watermark in seconds
        """
        db_path = self._get_chs_db_path()
        faiss_path = FAISS_INDEX_PATH

        db_exists = db_path.exists()
        faiss_exists = faiss_path.exists()

        # Calculate watermark age
        current_time = time.time()
        watermark_age = current_time - self._last_watermark_save_time

        # Determine status: healthy only if all checks pass
        # Status is degraded if: DB missing, FAISS missing, or watermark stale (>30s)
        if db_exists and faiss_exists and watermark_age < 30:
            status = "healthy"
        else:
            status = "degraded"

        return {
            "status": status,
            "db_path": str(db_path),
            "faiss_path": str(faiss_path),
            "db_exists": db_exists,
            "faiss_exists": faiss_exists,
            "watermark_age_seconds": watermark_age,
        }

    def _execute_search(
        self, scope: str, query: str, limit: int, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute search based on scope."""
        if scope == "cks":
            return self._search_cks(query, limit, params)
        elif scope == "chs":
            return self._search_chs(query, limit, params)
        elif scope == "plans":
            return self._search_plans(query, limit, params)
        else:
            logger.warning(f"Unknown scope: {scope}")
            return []

    def _classify_intent(self, text: str) -> IntentClassificationResult:
        """Classify text into intent category using embedding similarity.

        Returns:
            {"intent": "<category>", "confidence": <float>}
        """
        import numpy as np

        # Lazy-load category embeddings with memory guard
        if not hasattr(self, "_category_embeddings"):
            # Memory check: Pre-load validation
            if not _check_memory_before_load(
                "IntentModel (all-MiniLM-L6-v2)", SENTENCE_TRANSFORMER_MEMORY_MB
            ):
                logger.error("Intent model initialization aborted: insufficient memory")
                # Fallback to simple keyword-based classification
                return self._classify_intent_fallback(text)

            from sentence_transformers import SentenceTransformer

            if not hasattr(self, "_intent_model"):
                self._intent_model = SentenceTransformer("all-MiniLM-L6-v2")

                # Memory check: Post-load validation
                if not _check_memory_after_load("IntentModel"):
                    logger.critical(
                        "Intent model loaded but exceeded memory cap - self-terminating"
                    )
                    self._running = False
                    return self._classify_intent_fallback(text)

            self._category_embeddings = {
                cat: self._intent_model.encode(desc) for cat, desc in _CATEGORY_DESCRIPTIONS.items()
            }

        # Encode text
        text_embedding = self._intent_model.encode(text)

        # Compute cosine similarity
        similarities = {}
        for category, cat_embedding in self._category_embeddings.items():
            similarity = np.dot(text_embedding, cat_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(cat_embedding)
            )
            similarities[category] = similarity

        best_intent = max(similarities, key=similarities.get)
        confidence = float(similarities[best_intent])

        return {"intent": best_intent, "confidence": confidence}

    def _classify_intent_fallback(self, text: str) -> IntentClassificationResult:
        """Fallback keyword-based intent classification when model cannot be loaded."""
        text_lower = text.lower()

        # Simple keyword matching
        scores = {
            "search": sum(1 for kw in ["search", "find", "locate", "where"] if kw in text_lower),
            "read": sum(1 for kw in ["read", "view", "show", "open"] if kw in text_lower),
            "write": sum(1 for kw in ["write", "create", "add", "insert"] if kw in text_lower),
            "analyze": sum(1 for kw in ["analyze", "examine", "investigate"] if kw in text_lower),
            "research": sum(
                1 for kw in ["research", "look up", "documentation"] if kw in text_lower
            ),
            "code": sum(1 for kw in ["code", "function", "class", "def "] if kw in text_lower),
            "test": sum(1 for kw in ["test", "verify", "assert"] if kw in text_lower),
            "git": sum(1 for kw in ["git", "commit", "branch"] if kw in text_lower),
            "web": sum(1 for kw in ["web", "http", "url"] if kw in text_lower),
        }

        # Find highest score
        best_intent = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_intent] / 3.0)  # Normalize to 0-1

        if scores[best_intent] == 0:
            return {"intent": "other", "confidence": 0.0}

        return {"intent": best_intent, "confidence": confidence}

    def _handle_skill_intent(self, command: str, skill: str) -> dict[str, Any]:
        """Check if command matches skill intent using semantic similarity.

        Compares the input command against known-good examples for the skill
        using embedding similarity. This helps validate that the LLM is using
        the skill's designated execution mechanism.

        Args:
            command: The command string to validate (e.g., Bash command or Task prompt)
            skill: The skill name to check against (e.g., "rca", "truth")

        Returns:
            Dict with keys:
                - match: True if similarity >= threshold (0.75)
                - similarity: Maximum similarity score (0.0-1.0)
                - threshold: The threshold used (0.75)
                - error: Error message if failed (optional)
        """
        import numpy as np

        skill_lower = skill.lower()

        # Check if skill has examples
        examples = SKILL_COMMAND_EXAMPLES.get(skill_lower)
        if not examples:
            # No examples for this skill, can't validate
            return {
                "match": False,
                "similarity": 0.0,
                "threshold": 0.75,
                "error": f"No examples found for skill: {skill}",
            }

        # Lazy-load intent model (v3.2 fix: check for None, not just hasattr)
        if self._intent_model is None:
            # Memory check: Pre-load validation
            if not _check_memory_before_load(
                "SkillIntentModel (all-MiniLM-L6-v2)", SENTENCE_TRANSFORMER_MEMORY_MB
            ):
                logger.error("Skill intent model initialization aborted: insufficient memory")
                return {
                    "match": False,
                    "similarity": 0.0,
                    "threshold": 0.75,
                    "error": "Insufficient memory to load intent model",
                }

            from sentence_transformers import SentenceTransformer

            self._intent_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Memory check: Post-load validation
            if not _check_memory_after_load("SkillIntentModel"):
                logger.critical(
                    "Skill intent model loaded but exceeded memory cap - self-terminating"
                )
                self._running = False
                return {
                    "match": False,
                    "similarity": 0.0,
                    "threshold": 0.75,
                    "error": "Memory cap exceeded after model load",
                }

        # Encode the input command
        command_embedding = self._intent_model.encode(command)

        # Compute similarity with each example
        max_similarity = 0.0
        for example in examples:
            example_embedding = self._intent_model.encode(example)
            # Cosine similarity
            similarity = np.dot(command_embedding, example_embedding) / (
                np.linalg.norm(command_embedding) * np.linalg.norm(example_embedding)
            )
            max_similarity = max(max_similarity, float(similarity))

        # Check against threshold
        threshold = 0.75
        match = max_similarity >= threshold

        return {
            "match": match,
            "similarity": max_similarity,
            "threshold": threshold,
        }

    def _handle_compute_embedding(self, text: str) -> dict[str, Any]:
        """Compute embedding vector for arbitrary text using all-MiniLM-L6-v2.

        Used by semantic trigger detection in sequential_thinking hook to share
        the embedding model across all terminals via the daemon.

        Args:
            text: The text to embed.

        Returns:
            Dict with keys:
                - embedding: List of float values (384-dimensional)
                - model: "all-MiniLM-L6-v2"
                - error: Error message if failed (optional)
        """

        # Lazy-load intent model with memory guard
        if self._intent_model is None:
            # Memory check: Pre-load validation
            if not _check_memory_before_load(
                "IntentModel (all-MiniLM-L6-v2)", SENTENCE_TRANSFORMER_MEMORY_MB
            ):
                logger.error("Intent model initialization aborted: insufficient memory")
                return {
                    "embedding": [],
                    "model": "all-MiniLM-L6-v2",
                    "error": "Insufficient memory to load embedding model",
                }

            from sentence_transformers import SentenceTransformer

            self._intent_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Memory check: Post-load validation
            if not _check_memory_after_load("IntentModel"):
                logger.critical("Intent model loaded but exceeded memory cap - self-terminating")
                self._running = False
                return {
                    "embedding": [],
                    "model": "all-MiniLM-L6-v2",
                    "error": "Memory limit exceeded after model load",
                }

        # SEC-001: Reject text exceeding model token limit to prevent memory exhaustion
        MAX_TEXT_LENGTH = 8192
        if len(text) > MAX_TEXT_LENGTH:
            return {
                "embedding": [],
                "model": "all-MiniLM-L6-v2",
                "error": f"Text length {len(text)} exceeds maximum {MAX_TEXT_LENGTH}",
            }

        # Encode text and convert to list for JSON serialization
        embedding = self._intent_model.encode(text).tolist()

        return {
            "embedding": embedding,
            "model": "all-MiniLM-L6-v2",
        }

    # -------------------------------------------------------------------------
    # CKS Search
    # -------------------------------------------------------------------------

    def _get_cks(self):
        """Lazy-load CKS instance with memory guard."""
        if self._cks is None:
            self._log_to_file("[CKS] _cks is None, initializing...")
            # Memory check: Pre-load validation
            self._log_to_file("[CKS] Checking memory before model load...")
            if not _check_memory_before_load("CKS (all-mpnet-base-v2)", CKS_MODEL_MEMORY_MB):
                # Use _log_to_file instead of logger.error to avoid stderr blocking
                self._log_to_file("[CKS] ⚠️  Insufficient memory - skipping CKS initialization")
                return None

            CKS = None
            import_error = None
            # Try multiple import strategies
            self._log_to_file("[CKS] Attempting CKS import...")
            try:
                from search_research.core.cks.unified import CKS
            except ImportError as e1:
                import_error = e1
                try:
                    # Try direct import from src (when __csf is in sys.path)
                    from knowledge.systems.cks.unified import CKS
                except ImportError as e2:
                    import_error = e2
                    try:
                        # Try relative import
                        from ..cks.unified import CKS
                    except (ImportError, ValueError) as e3:
                        import_error = e3
                        try:
                            # Last resort: import using importlib
                            import importlib.util

                            spec = importlib.util.spec_from_file_location(
                                "cks_unified",
                                str(_csf_root / "src" / "cks" / "unified.py"),
                            )
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                CKS = module.CKS
                        except Exception as e4:
                            import_error = e4
            if CKS is not None:
                self._log_to_file("[CKS] Import successful, instantiating CKS()...")
                self._cks = CKS()
                self._log_to_file("[CKS] CKS() instantiation complete")

                # Memory check: Post-load validation
                self._log_to_file("[CKS] Checking memory after load...")
                if not _check_memory_after_load("CKS"):
                    self._log_to_file("[CKS] ⚠️  Memory cap exceeded after load - self-terminating")
                    self._running = False
                    return None

                self._log_to_file("[CKS] CKS initialization complete")
            else:
                logger.error(f"Failed to import CKS: {import_error}")
        return self._cks

    def _search_cks(self, query: str, limit: int, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Search CKS (Constitutional Knowledge System).

        Supports params:
        - entry_type: Filter by type (memory, pattern, code, knowledge, etc.)
        - expand_query: Enable query expansion
        - fusion_method: Result fusion method (rrf, adaptive, etc.)
        - diversity: MMR diversity (0.0-1.0)
        - entity_slug: Entity for domain-specific search
        """
        # AT-007: Check cache before FAISS search
        cache_key_params = {"limit": limit, **params}
        cached_results = self.query_cache.get(query, **cache_key_params)
        if cached_results is not None:
            with self._stats_lock:
                self._stats["cache_hits"] += 1
            return cached_results

        # Cache miss
        with self._stats_lock:
            self._stats["cache_misses"] += 1

        cks = self._get_cks()
        if cks is None:
            logger.debug("CKS not available for search")
            return []

        try:
            entry_type = params.get("entry_type")
            expand_query = params.get("expand_query", False)
            fusion_method = params.get("fusion_method")
            diversity = params.get("diversity")
            entity_slug = params.get("entity_slug")

            # Use semantic search
            results = cks.search_semantic(
                query=query,
                entry_type=entry_type,
                limit=limit,
                expand_query=expand_query,
                fusion_method=fusion_method,
                diversity=diversity,
                entity_slug=entity_slug,
            )

            # Check if results are already normalized (for test compatibility)
            # If results have 'score' instead of 'similarity', they're from test mock
            if (
                results
                and len(results) > 0
                and "score" in results[0]
                and "similarity" not in results[0]
            ):
                # Test mock data - return as-is
                final_results = results
            else:
                # Normalize results for daemon response (convert numpy types to native)
                normalized = []
                for r in results:
                    # Handle both 'similarity' and 'score' keys (for test compatibility)
                    similarity_val = r.get("similarity", r.get("score", 0.0))
                    normalized.append(
                        {
                            "id": r.get("id", ""),
                            "type": r.get("type", "memory"),
                            "title": r.get("title", ""),
                            "content": r.get("content", r.get("answer", "")),
                            "similarity": float(similarity_val),
                            "metadata": r.get("metadata", {}),
                        }
                    )
                final_results = normalized

            # AT-007: Store results in cache after FAISS query
            self.query_cache.set(query, final_results, **cache_key_params)

            return final_results

        except Exception as e:
            logger.exception(f"CKS search error: {e}")
            return []

    # -------------------------------------------------------------------------
    # CHS Search (Daemon-Managed Indexing)
    # -------------------------------------------------------------------------

    def _get_chs_db_path(self) -> Path:
        """Get path to chat history SQLite database.

        Database located at __csf/data/chat_history.db.
        """
        return _csf_root / "data" / "chat_history.db"

    def _load_chs_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Load chat messages from SQLite database.

        Args:
            limit: Maximum number of messages to load (None = all)

        Returns:
            List of message dicts with keys: id, session_id, role, content, timestamp
        """
        db_path = self._get_chs_db_path()
        if not db_path.exists():
            logger.warning(f"CHS database not found: {db_path}")
            return []

        try:
            with sqlite3.connect(str(db_path), timeout=1.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Detect schema version
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
                )
                is_v2_schema = cursor.fetchone() is not None

                if is_v2_schema:
                    # V2 schema: messages table with raw_json column
                    metadata_expr = "COALESCE(raw_json, '{}')"
                    messages_table = "messages"
                else:
                    # Legacy schema: chat_messages table with metadata column
                    metadata_expr = "metadata"
                    messages_table = "chat_messages"

                query = f"""
                    SELECT id, session_id, role, content, timestamp, {metadata_expr} as metadata
                    FROM {messages_table}
                    ORDER BY timestamp DESC
                """
                if limit:
                    query += f" LIMIT {limit}"

                cursor = conn.execute(query)
                messages = []
                for row in cursor.fetchall():
                    # Parse metadata JSON if present
                    metadata_raw = row["metadata"] if row["metadata"] else "{}"
                    try:
                        metadata = json.loads(metadata_raw) if metadata_raw else {}
                    except json.JSONDecodeError:
                        metadata = {}

                    messages.append(
                        {
                            "id": str(row["id"]),
                            "session_id": row["session_id"],
                            "role": row["role"],
                            "content": row["content"],
                            "timestamp": row["timestamp"],
                            "metadata": metadata,
                        }
                    )
                logger.info(f"Loaded {len(messages)} messages from CHS database")
                return messages
        except Exception as e:
            logger.error(f"Failed to load CHS messages: {e}")
            return []

    def _store_chs_in_cks(self, messages: list[dict[str, Any]]) -> int:
        """Store CHS messages in CKS with source tagging.

        Args:
            messages: List of message dicts from _load_chs_messages

        Returns:
            Number of messages stored
        """
        if not messages:
            return 0

        cks = self._get_cks()
        if cks is None:
            logger.warning("CKS not available for CHS storage")
            return 0

        stored = 0
        total = len(messages)
        for i, msg in enumerate(messages):
            if i % 10 == 0:
                logger.info(f"CHS indexing progress: {i}/{total}")
            try:
                content = msg.get("content", "")
                role = msg.get("role", "user")

                # Create question from content (first 100 chars as context)
                question = f"[{role.upper()}] {content[:100]}..."

                # Use full content as answer
                answer = content

                # Build metadata with CHS source tag
                metadata = {
                    "source": "chs",
                    "chs_id": msg.get("id"),
                    "chs_session_id": msg.get("session_id"),
                    "chs_role": role,
                    "chs_timestamp": msg.get("timestamp"),
                }
                # Include any original metadata
                metadata.update(msg.get("metadata", {}))

                # Store in CKS as a "memory" entry with CHS source
                cks.ingest_memory(
                    question=question,
                    answer=answer,
                    **metadata,
                )
                stored += 1
            except Exception as e:
                logger.error(f"Failed to store message {msg.get('id')}: {e}")
                continue

        logger.info(f"Stored {stored} CHS messages in CKS")
        return stored

    def _index_chs_data(self, limit: int | None = None) -> int:
        """Index CHS data from SQLite into CKS.

        This is the main entry point for daemon-managed CHS indexing.
        Loads messages from chat_history.db and stores them in CKS
        with source tagging for unified search.

        Args:
            limit: Maximum number of messages to index (None = all)

        Returns:
            Number of messages indexed
        """
        logger.info("Starting CHS indexing (daemon-managed)")
        messages = self._load_chs_messages(limit)
        if not messages:
            logger.warning("No CHS messages to index")
            return 0

        stored = self._store_chs_in_cks(messages)
        logger.info(f"CHS indexing complete: {stored} messages indexed")
        return stored

    def _ensure_chs_indexed(self) -> None:
        """Ensure CHS data is indexed in CKS (async/non-blocking).

        Spawns background thread for indexing if not already done.
        Returns immediately without blocking the request handler.
        """
        self._log_to_file("[CHS] _ensure_chs_indexed() called")
        # Skip if indexing is already in progress
        if self._chs_indexing:
            logger.debug("CHS indexing already in progress in background")
            self._log_to_file("[CHS] Indexing already in progress, returning")
            return

        # Check if CHS has been indexed by looking for CHS entries in CKS
        self._log_to_file("[CHS] Getting CKS instance...")
        cks = self._get_cks()
        if cks is None:
            self._log_to_file("[CHS] CKS instance is None, returning")
            return
        self._log_to_file("[CHS] CKS instance obtained")

        try:
            # Query for entries with source=chs metadata
            self._log_to_file("[CHS] Querying for CHS entries in CKS...")
            with cks.conn:
                cursor = cks.conn.execute(
                    """SELECT COUNT(*) FROM entries
                       WHERE json_extract(metadata, '$.source') = 'chs'
                       LIMIT 1"""
                )
                has_chs = cursor.fetchone()[0] > 0
                self._log_to_file(f"[CHS] CHS entries found: {has_chs}")

                if has_chs:
                    # Already indexed, nothing to do
                    self._chs_index_complete.set()
                    self._log_to_file("[CHS] CHS already indexed, returning")
                    return

                # Start background indexing if not already running
                self._log_to_file("[CHS] CHS not indexed, acquiring lock...")
                with self._chs_index_lock:
                    if self._chs_indexing or self._chs_index_thread:
                        self._log_to_file("[CHS] Indexing already started, returning")
                        return  # Already started

                    self._chs_indexing = True
                    self._chs_index_complete.clear()
                    logger.info("CHS not indexed, spawning background indexing thread")
                    self._log_to_file("[CHS] Spawning background indexing thread...")

                    # Start background indexing thread
                    self._chs_index_thread = threading.Thread(
                        target=self._index_chs_data_background,
                        daemon=True,
                        name="CHSIndexer",
                    )
                    self._chs_index_thread.start()
                    self._log_to_file("[CHS] Background indexing thread started")

        except Exception as e:
            logger.debug(f"Error checking CHS index status: {e}")
            self._log_to_file(f"[CHS] ERROR: {e}")

    def _index_chs_data_background(self) -> None:
        """Background worker for CHS indexing.

        Runs in a separate thread to avoid blocking request handlers.
        Uses thread-local CKS instance to avoid SQLite threading issues.
        Waits for the embedding model to be fully loaded before ingesting messages.
        """
        # Import sqlite3 to set check_same_thread=False for this thread's CKS instance

        try:
            logger.info("Background CHS indexing started")

            # Get main thread's CKS instance to access the already-loaded model
            main_cks = self._get_cks()
            if main_cks is None:
                logger.error("CKS not available for CHS indexing")
                return

            # Wait for the main thread's model to be loaded (avoid duplicate loading)
            logger.info("Waiting for embedding model to be ready...")
            max_wait = 120  # Maximum 120 seconds (model load can take 60+ seconds)
            waited = 0
            import time

            # Access module-level _model_loading flag to properly synchronize
            from src.cks.unified import _model_loading

            while main_cks._model is None and waited < max_wait:
                # Trigger model loading if not started
                if not main_cks._model_loaded:
                    main_cks._initialize_embedding_model()
                    main_cks._model_loaded = True

                # Wait for model load to complete (check both model and loading flag)
                if main_cks._model is None and not _model_loading:
                    # Loading finished but model is still None - try again
                    main_cks._initialize_embedding_model()
                    main_cks._model_loaded = True

                time.sleep(0.5)
                waited += 0.5
                if waited % 10 == 0:
                    logger.info(f"Still waiting for model... ({int(waited)}s elapsed)")

            if main_cks._model is None:
                logger.error(f"Embedding model failed to load after {max_wait}s, cannot index CHS")
                return

            logger.info("Embedding model ready, starting CHS ingestion")

            # Create a thread-local CKS instance for SQLite operations
            # But reuse the already-loaded model from main thread to avoid slow re-loading
            from knowledge.systems.cks.unified import CKS as CKSClass

            # Create a new CKS instance but inject the already-loaded model
            # This avoids SQLite threading issues while reusing the model
            thread_cks = CKSClass()

            logger.info(
                f"Thread-local CKS created, main_cks._model is None: {main_cks._model is None}"
            )

            # Replace the thread-local CKS's model with the main thread's model
            # This avoids having to load the model again (which is slow)
            thread_cks._model = main_cks._model
            thread_cks._model_loaded = True
            thread_cks._SentenceTransformer = main_cks._SentenceTransformer
            thread_cks._np = main_cks._np

            logger.info(
                f"Thread-local CKS model injected, thread_cks._model is None: {thread_cks._model is None}"
            )

            # Use incremental indexing - only load new messages since last indexed
            batch_size = 500
            total_stored = 0
            max_id = 0

            while True:
                # Load batch of new messages
                messages = self._load_chs_messages_incremental(batch_size=batch_size)
                if not messages:
                    break

                # Track highest ID for state saving
                for msg in messages:
                    msg_id = int(msg.get("id", 0))
                    if msg_id > max_id:
                        max_id = msg_id

                # Store batch using THIS thread's CKS instance
                batch_stored = 0
                for i, msg in enumerate(messages):
                    if i % 100 == 0:
                        logger.info(f"CHS indexing: {total_stored + i} messages...")
                    try:
                        content = msg.get("content", "")
                        role = msg.get("role", "user")

                        # Create question from content (first 100 chars)
                        question = f"[{role.upper()}] {content[:100]}..."

                        # Use full content as answer
                        answer = content

                        # Build metadata with CHS source tag
                        metadata = {
                            "source": "chs",
                            "chs_id": msg.get("id"),
                            "chs_session_id": msg.get("session_id"),
                            "chs_role": role,
                            "chs_timestamp": msg.get("timestamp"),
                        }
                        # Include any original metadata
                        metadata.update(msg.get("metadata", {}))

                        # Store in CKS as a "memory" entry with CHS source
                        thread_cks.ingest_memory(
                            question=question,
                            answer=answer,
                            **metadata,
                        )
                        batch_stored += 1
                    except Exception as e:
                        logger.error(f"Failed to store msg {msg.get('id')}: {e}")
                        continue

                total_stored += batch_stored
                # Save state after each batch
                if max_id > 0:
                    self._save_last_indexed_id(max_id)

            logger.info(f"Stored {total_stored} CHS messages in CKS")

            # Trigger FAISS update after CKS indexing
            if self._faiss_update_enabled:
                time_since_faiss = time.time() - self._last_faiss_update_time
                if time_since_faiss > FAISS_UPDATE_INTERVAL:
                    try:
                        self._update_faiss_index()
                        self._last_faiss_update_time = time.time()
                    except Exception as e:
                        logger.warning(f"FAISS update failed: {e}")

            logger.info("Background CHS indexing complete")
        except Exception as e:
            logger.error(f"Background CHS indexing failed: {e}")
        finally:
            self._chs_indexing = False
            self._chs_index_complete.set()
            self._chs_index_thread = None
            # Clean up this thread's CKS instance (but keep the model!)
            try:
                if "thread_cks" in locals():
                    thread_cks.conn.close()
            except (AttributeError, OSError) as e:
                logger.debug("Failed to close thread_cks connection", error=str(e))

    def _update_faiss_index(self) -> None:
        """Incrementally update FAISS index with new messages.

        Fail-fast: If FAISS index doesn't exist, daemon will crash.
        Use file-based lock to prevent concurrent updates across multiple terminals.
        Includes memory guards to prevent OOM during index updates.
        """
        lock_file = None
        try:
            import torch
            from sentence_transformers import SentenceTransformer

            from src.core.faiss_vector_store import FAISSVectorStore

            # Prevent concurrent updates within same daemon instance
            if self._faiss_updating:
                logger.debug("FAISS update already in progress (instance lock)")
                return

            # Memory check: Pre-load validation for FAISS + model
            if not _check_memory_before_load(
                "FAISS update", FAISS_ESTIMATED_MEMORY_MB + CKS_MODEL_MEMORY_MB
            ):
                logger.warning("FAISS update skipped: insufficient memory")
                return

            # Acquire cross-terminal file lock (fail-fast if lock held)
            FAISS_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Windows: exclusive access, fails immediately if locked
                lock_file = open(FAISS_LOCK_PATH, "xb")
                lock_file.write(str(os.getpid()).encode())
            except FileExistsError:
                # Lock file exists - another terminal holds the lock
                logger.debug("FAISS update locked by another terminal")
                return

            # Check FAISS index age - force full rebuild if too old (> 24 hours)
            if FAISS_INDEX_PATH.exists():
                index_age = time.time() - FAISS_INDEX_PATH.stat().st_mtime
                if index_age > FAISS_MAX_AGE:
                    logger.warning(
                        f"FAISS index is {index_age / 3600:.1f} hours old "
                        f"(> {FAISS_MAX_AGE / 3600:.1f} hours) - forcing full rebuild"
                    )
                    # Clear incremental state to force full rebuild
                    if FAISS_STATE_PATH.exists():
                        FAISS_STATE_PATH.unlink()
                        logger.info("Cleared FAISS incremental state for full rebuild")

            # Load new messages (reuse existing incremental loader)
            messages = self._load_chs_messages_incremental(batch_size=1000)
            if not messages:
                logger.debug("No new messages for FAISS update")
                return

            self._faiss_updating = True
            logger.info(f"Starting FAISS update for {len(messages)} messages")

            # Generate embeddings - assume GPU always available (fail-fast if not)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.debug(f"Using device: {device} for FAISS embeddings")
            model = SentenceTransformer("all-mpnet-base-v2", device=device)
            texts = [m.get("content", "")[:4000] for m in messages]
            embeddings = model.encode(texts, normalize_embeddings=True)

            # Memory check: After loading model and embeddings
            if not _check_memory_after_load("FAISS model + embeddings"):
                logger.warning("FAISS update aborted: memory cap exceeded after model load")
                return

            # Incremental update - will fail-fast if FAISS index missing
            store = FAISSVectorStore(index_path=str(FAISS_INDEX_PATH))
            result = store.incremental_update(messages, embeddings, backup=True, validate=True)

            if result["success"]:
                logger.info(
                    f"FAISS updated: {result['vectors_added']} vectors, {result['total_vectors']} total"
                )
            else:
                logger.warning(f"FAISS update reported failure: {result.get('error', 'unknown')}")

            # Final memory check after FAISS update
            if not _check_memory_after_load("FAISS update complete"):
                logger.critical("FAISS update completed but exceeded memory cap - self-terminating")
                self._running = False

        except Exception as e:
            logger.error(f"FAISS update failed: {e}")
            raise
        finally:
            self._faiss_updating = False
            # Release cross-terminal lock
            if lock_file:
                lock_file.close()
                try:
                    FAISS_LOCK_PATH.unlink()
                except FileNotFoundError:
                    pass

    def _get_chs(self):
        """Legacy CHS loader - deprecated, using CKS-based approach."""
        # For backward compatibility, still support ChatHistorySearcher
        # but prefer CKS-based approach to avoid lock conflicts
        if self._chs is None:
            try:
                with self._chs_lock:
                    if self._chs is None:
                        from modules.analysis.chat_search.src.chat_history_search import (
                            ChatHistorySearcher,
                        )

                        # Use default paths, but DON'T auto-index (avoid Qdrant conflict)
                        self._chs = ChatHistorySearcher(enable_rag=False)  # Disable RAG
                        logger.info("CHS initialized for daemon (legacy mode)")
            except ImportError as e:
                logger.error(f"Failed to import CHS: {e}")
        return self._chs

    def _search_chs(self, query: str, limit: int, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Search CHS (Chat History Search) using hybrid or semantic approach.

        Uses hybrid two-stage search (FTS5 + semantic re-rank) when FTS5 is
        available, falling back to CKS-based semantic search otherwise.

        Supports params:
        - session_filter: Time period (today, yesterday, week, month, all)
        - context_filter: Context (project, general, technical, all)
        - rank_by: Ranking method (relevance, recency, frequency)
        """
        # Use hybrid search if FTS5 is available
        if self._fts5_available():
            logger.debug("Using FTS5 hybrid search for CHS")
            return self._search_chs_hybrid(query, limit, params)

        # Fall back to semantic-only search via CKS
        logger.debug("FTS5 not available, using semantic-only CHS search")

        # Ensure CHS is indexed
        self._ensure_chs_indexed()

        # Use CKS for search with source filtering
        cks = self._get_cks()
        if cks is None:
            logger.warning("CKS not available for CHS search")
            return []

        try:
            # First attempt: search with limit*2
            results = cks.search_semantic(
                query=query,
                limit=limit * 2,
            )

            # Filter to only CHS-sourced entries
            chs_results = self._filter_chs_results(results)

            # Fallback: if no results, try with larger search scope
            if not chs_results:
                # Increase limit significantly to find lower-ranked CHS entries
                fallback_limit = max(limit * 10, 100)
                logger.debug(f"CHS fallback: expanding to {fallback_limit}")
                results = cks.search_semantic(
                    query=query,
                    limit=fallback_limit,
                )
                chs_results = self._filter_chs_results(results)

            # Apply limit after filtering
            return chs_results[:limit]

        except Exception as e:
            logger.exception(f"CHS search error: {e}")
            return []

    def _filter_chs_results(self, results: list[dict]) -> list[dict[str, Any]]:
        """Filter semantic search results to only CHS-sourced entries.

        Args:
            results: Raw semantic search results from CKS

        Returns:
            Filtered list with only CHS entries, normalized for daemon response
        """
        chs_results = []
        for r in results:
            metadata = r.get("metadata", {})
            if metadata.get("source") == "chs":
                # Normalize CHS-specific fields (convert numpy types to native)
                # Handle timestamp as ISO string or unix timestamp
                timestamp_raw = metadata.get("chs_timestamp", 0)
                try:
                    if isinstance(timestamp_raw, str):
                        # Keep as ISO string for display
                        timestamp = timestamp_raw
                    else:
                        timestamp = float(timestamp_raw)
                except (ValueError, TypeError):
                    timestamp = 0

                chs_results.append(
                    {
                        "id": metadata.get("chs_id", r.get("id", "")),
                        "timestamp": timestamp,
                        "session_id": metadata.get("chs_session_id", ""),
                        "role": metadata.get("chs_role", "unknown"),
                        "display": r.get("content", r.get("answer", "")),
                        "relevance_score": float(r.get("similarity", 0.0)),
                        "search_method": "semantic",
                        "metadata": metadata,
                    }
                )
        return chs_results

    # -------------------------------------------------------------------------
    # FTS5 Full-Text Search (Hybrid Stage 1)
    # -------------------------------------------------------------------------

    def _fts5_available(self) -> bool:
        """Check if FTS5 index is available on chat_history.db."""
        db_path = self._get_chs_db_path()
        if not db_path.exists():
            return False
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Check for V2 schema (messages_fts) or legacy schema (message_search)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"
                )
                if cursor.fetchone() is not None:
                    return True
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='message_search'"
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def _fts5_search(
        self, query: str, limit: int = 100, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Fast keyword search using FTS5 full-text index.

        Supports both V2 schema (messages + messages_fts) and
        legacy schema (chat_messages + message_search).

        Args:
            query: Search query (supports FTS5 syntax: AND, OR, NOT, phrases)
            limit: Maximum results to return
            params: Optional time filters
                - hours_ago: Filter to last N hours (int)
                - after: ISO timestamp for start filter (str)
                - before: ISO timestamp for end filter (str)

        Returns:
            List of matching messages with id, content, timestamp, session_id
        """
        db_path = self._get_chs_db_path()
        if not db_path.exists():
            return []

        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Clean query for FTS5: escape special chars, add OR between terms
                clean_query = self._prepare_fts5_query(query)

                # Detect schema version
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
                )
                is_v2_schema = cursor.fetchone() is not None
                if is_v2_schema:
                    fts_table = "messages_fts"
                    messages_table = "messages"
                else:
                    # Legacy schema
                    fts_table = "message_search"
                    messages_table = "chat_messages"

                # Extract time filters
                time_filters = []
                filter_values = []
                if params:
                    after = params.get("after")
                    before = params.get("before")
                    hours_ago = params.get("hours_ago")

                    if hours_ago:
                        from datetime import datetime, timedelta

                        cutoff = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
                        time_filters.append("m.timestamp >= ?")
                        filter_values.append(cutoff)
                    if after:
                        validated_after = self._validate_iso_timestamp(after)
                        time_filters.append("m.timestamp >= ?")
                        filter_values.append(validated_after)
                    if before:
                        validated_before = self._validate_iso_timestamp(before)
                        time_filters.append("m.timestamp <= ?")
                        filter_values.append(validated_before)

                # Build WHERE clause
                where_clause = f"WHERE {fts_table} MATCH ?"
                query_params = [clean_query]

                if time_filters:
                    where_clause += " AND " + " AND ".join(time_filters)
                    query_params.extend(filter_values)

                query_params.append(limit)

                # Use INNER JOIN for V2 schema (contentless FTS5)
                # For legacy schema, use content-based matching
                if is_v2_schema:
                    cursor.execute(
                        f"""
                            SELECT m.id, m.session_id, m.role, m.content, m.timestamp,
                                   -bm25({fts_table}) AS rank
                            FROM {messages_table} m
                            INNER JOIN {fts_table} ON m.rowid = {fts_table}.rowid
                            {where_clause}
                            ORDER BY rank DESC
                            LIMIT ?
                        """,
                        query_params,
                    )
                else:
                    # Legacy: two-step approach (content-based matching)
                    cursor.execute(
                        f"""
                            SELECT -bm25({fts_table}) as rank, content
                            FROM {fts_table}
                            WHERE {fts_table} MATCH ?
                            ORDER BY rank DESC
                            LIMIT ?
                        """,
                        [clean_query, limit],
                    )
                    fts_results = cursor.fetchall()
                    if not fts_results:
                        return []

                    # Fetch full messages by content
                    results = []
                    for rank, content in fts_results:
                        cursor.execute(
                            f"""
                                SELECT id, session_id, role, content, timestamp
                                FROM {messages_table}
                                WHERE content = ?
                                LIMIT 1
                            """,
                            (content,),
                        )
                        msg_row = cursor.fetchone()
                        if msg_row:
                            results.append(
                                {
                                    "id": str(msg_row["id"]),
                                    "content": msg_row["content"],
                                    "timestamp": msg_row["timestamp"],
                                    "session_id": msg_row["session_id"],
                                    "role": msg_row["role"],
                                    "fts_rank": float(rank),
                                }
                            )
                        if len(results) >= limit:
                            break
                    logger.debug(f"FTS5 search returned {len(results)} results for query: {query}")
                    return results

                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append(
                        {
                            "id": str(row["id"]),
                            "content": row["content"],
                            "timestamp": row["timestamp"],
                            "session_id": row["session_id"],
                            "role": row["role"],
                            "fts_rank": float(row["rank"]),
                        }
                    )

                logger.debug(f"FTS5 search returned {len(results)} results for query: {query}")
                return results

                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": str(row["id"]),
                            "content": row["content"],
                            "timestamp": row["timestamp"],
                            "session_id": row["session_id"],
                            "role": row["role"],
                            "fts_rank": float(row["rank"]),
                        }
                    )

                logger.debug(f"FTS5 search returned {len(results)} results for: {query}")
                return results

        except ValueError:
            # Re-raise ValueError for invalid time filter parameters
            raise
        except Exception as e:
            logger.warning(f"FTS5 search failed, falling back: {e}")
            return []

    def _validate_iso_timestamp(self, value: str) -> str:
        """
        Validate ISO 8601 timestamp format to prevent SQL injection.

        Args:
            value: String timestamp to validate

        Returns:
            The validated timestamp string

        Raises:
            ValueError: If timestamp is not valid ISO 8601 format

        Accepted formats:
            - 2026-01-01T00:00:00
            - 2026-01-01T00:00:00Z
            - 2026-01-01T00:00:00+00:00
            - 2026-01-01T00:00:00.123456
        """
        if not value:
            raise ValueError("Invalid time filter: timestamp cannot be empty")

        # Strict ISO 8601 validation: must contain 'T' date/time separator
        # Python's fromisoformat() accepts space, which is NOT strict ISO 8601
        if "T" not in value:
            raise ValueError(f"Invalid ISO timestamp format: {value} (must use 'T' separator)")

        from datetime import datetime

        # Try parsing with datetime.fromisoformat (Python 3.7+)
        # This handles ISO 8601 formats like:
        # - 2026-01-01T00:00:00
        # - 2026-01-01T00:00:00.123456
        # It doesn't handle 'Z' suffix directly, so replace 'Z' with '+00:00'
        try:
            # Normalize Z suffix to +00:00 for fromisoformat
            normalized = value
            if value.endswith("Z"):
                normalized = value[:-1] + "+00:00"
            # Parse the timestamp - this will raise ValueError if invalid
            datetime.fromisoformat(normalized)
        except ValueError as e:
            raise ValueError(f"Invalid ISO timestamp format: {value}") from e

        return value

    def _prepare_fts5_query(self, query: str) -> str:
        """
        Prepare query for FTS5 MATCH syntax.

        Converts natural language query to FTS5 format:
        - Splits into terms
        - Joins with OR for broader matching
        - Escapes special characters
        """
        # Remove special FTS5 chars that could cause errors
        special_chars = ['"', "'", "(", ")", "*", "-", "+", ":", "^", "~", "@"]
        clean = query
        for char in special_chars:
            clean = clean.replace(char, " ")

        # Split into terms and join with OR
        terms = [t.strip() for t in clean.split() if t.strip() and len(t.strip()) > 1]
        if not terms:
            return query

        # Use OR between terms for broader matching
        return " OR ".join(terms)

    # -------------------------------------------------------------------------
    # Hybrid Search (FTS5 + Semantic Re-rank)
    # -------------------------------------------------------------------------

    def _search_chs_hybrid(
        self, query: str, limit: int, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Hybrid two-stage search: FTS5 pre-filter -> semantic re-rank.

        Stage 1: Fast keyword search via FTS5 (narrows to ~100 candidates)
        Stage 2: Semantic re-ranking of candidates for accuracy

        Args:
            query: Search query
            limit: Final result limit
            params: Additional search parameters

        Returns:
            Ranked list of CHS results
        """
        # Stage 1: FTS5 keyword pre-filter
        candidate_limit = max(limit * 10, 100)  # Get more candidates for re-ranking
        fts_candidates = self._fts5_search(query, limit=candidate_limit, params=params)

        if not fts_candidates:
            logger.debug("FTS5 returned no results, falling back to semantic-only")
            # Don't fall back if time filters are active (filtering is being applied)
            if params and any(k in params for k in ("hours_ago", "after", "before")):
                logger.debug("Time filters active, returning empty results")
                return []
            return self._search_chs_semantic_only(query, limit, params)

        # Stage 2: Semantic re-ranking
        cks = self._get_cks()
        if cks is None or not hasattr(cks, "_get_embedding"):
            # No semantic capability, return FTS5 results directly
            return self._format_fts_results(fts_candidates[:limit], query)

        try:
            # Get query embedding
            query_embedding = cks._get_embedding(query)
            if query_embedding is None:
                return self._format_fts_results(fts_candidates[:limit], query)

            # Re-rank candidates by semantic similarity
            for candidate in fts_candidates:
                content_embedding = cks._get_embedding(candidate["content"][:1000])
                if content_embedding is not None:
                    similarity = cks._cosine_similarity(query_embedding, content_embedding)
                    candidate["similarity"] = float(similarity)
                else:
                    candidate["similarity"] = 0.3  # Fallback score

            # Apply recency weighting
            fts_candidates = self._apply_recency_boost(fts_candidates)

            # Deduplicate
            fts_candidates = self._deduplicate_results(fts_candidates)

            # Sort by similarity first (semantic), then FTS5 score
            # Similarity (0-1 range) should take priority over BM25 rank (negative)
            fts_candidates.sort(key=lambda x: x.get("similarity", x.get("score", 0)), reverse=True)
            return self._format_fts_results(fts_candidates[:limit], query)

        except Exception as e:
            logger.warning(f"Semantic re-ranking failed: {e}")
            return self._format_fts_results(fts_candidates[:limit], query)

    def _search_chs_semantic_only(
        self, query: str, limit: int, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Fallback semantic-only search (original implementation)."""
        # AT-007: Check cache before FAISS search
        cache_key_params = {"limit": limit, **params}
        cached_results = self.query_cache.get(query, **cache_key_params)
        if cached_results is not None:
            with self._stats_lock:
                self._stats["cache_hits"] += 1
            return cached_results

        # Cache miss
        with self._stats_lock:
            self._stats["cache_misses"] += 1

        cks = self._get_cks()
        if cks is None:
            return []

        try:
            results = cks.search_semantic(query=query, limit=limit * 2)
            chs_results = self._filter_chs_results(results)

            # AT-007: Store results in cache after FAISS query
            final_results = chs_results[:limit]
            self.query_cache.set(query, final_results, **cache_key_params)

            return final_results
        except Exception as e:
            logger.exception(f"Semantic search error: {e}")
            return []

    def _format_fts_results(
        self, results: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """Format FTS5/hybrid results for daemon response with snippets."""
        formatted = []
        for r in results:
            # Generate highlighted snippet
            snippet = self._highlight_snippet(r.get("content", ""), query)

            formatted.append(
                {
                    "id": r.get("id", ""),
                    "timestamp": r.get("timestamp", ""),
                    "session_id": r.get("session_id", ""),
                    "role": r.get("role", "unknown"),
                    "display": snippet,
                    "full_content": r.get("content", ""),
                    "relevance_score": float(
                        r.get("similarity", r.get("score", r.get("fts_rank", 0)))
                    ),
                    "search_method": "hybrid" if "similarity" in r else "fts5",
                    "metadata": {"source": "chs"},
                }
            )
        return formatted

    # -------------------------------------------------------------------------
    # Plans Search (Plan File Search)
    # -------------------------------------------------------------------------

    def _get_plans_directory(self) -> Path:
        """Get path to plans directory.

        Plans located at .claude/plans/.
        """
        # Use .claude location in current directory
        plans_dir = Path.cwd() / ".claude" / "plans"
        if plans_dir.exists():
            return plans_dir

        # Fallback to P:/.claude/plans
        fallback = Path("P:/") / ".claude" / "plans"
        return fallback

    def _load_plans(self) -> list[dict[str, Any]]:
        """Load plan files from plans directory.

        Returns:
            List of plan dicts with keys: id, title, content, status, metadata
        """
        plans_dir = self._get_plans_directory()
        if not plans_dir.exists():
            logger.warning(f"Plans directory not found: {plans_dir}")
            return []

        plans = []
        for plan_file in plans_dir.glob("*.md"):
            # Skip archived plans (in completed/ or abandoned/ subdirectories)
            if "/completed/" in str(plan_file) or "/abandoned/" in str(plan_file):
                continue

            try:
                content = plan_file.read_text(encoding="utf-8")

                # Extract title (first h1)
                title = plan_file.stem  # Default to filename
                for line in content.split("\n")[:20]:  # Check first 20 lines
                    line = line.strip()
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # Extract metadata from header
                status = "unknown"
                created = None
                completed = None
                last_reviewed = None

                for line in content.split("\n")[:30]:
                    if "**Status:**" in line:
                        # Extract status value
                        status_match = line.split("**Status:**")[1].strip()
                        status = status_match.split()[0] if status_match else "unknown"
                    elif "**Created:**" in line:
                        created = line.split("**Created:**")[1].strip()
                    elif "**Completed:**" in line:
                        completed = line.split("**Completed:**")[1].strip()
                    elif "**Last Reviewed:**" in line:
                        last_reviewed = line.split("**Last Reviewed:**")[1].strip()

                plans.append(
                    {
                        "id": plan_file.name,
                        "path": str(plan_file),
                        "title": title,
                        "content": content,
                        "status": status,
                        "metadata": {
                            "created": created,
                            "completed": completed,
                            "last_reviewed": last_reviewed,
                        },
                    }
                )
            except Exception as e:
                logger.error(f"Failed to load plan {plan_file}: {e}")
                continue

        logger.info(f"Loaded {len(plans)} plans from {plans_dir}")
        return plans

    def _search_plans(self, query: str, limit: int, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Search plans using keyword matching.

        Simple keyword search that can be extended to use CKS semantic search
        for better relevance.

        Args:
            query: Search query
            limit: Maximum results to return
            params: Additional search parameters (not currently used)

        Returns:
            List of plan results with title, content snippet, metadata
        """
        plans = self._load_plans()
        if not plans:
            return []

        # Simple keyword matching (case-insensitive)
        query_lower = query.lower()
        scored_plans = []

        for plan in plans:
            score = 0.0
            title_lower = plan["title"].lower()
            content_lower = plan["content"].lower()

            # Title matches get higher score
            if query_lower in title_lower:
                score += 2.0

            # Content matches
            query_words = query_lower.split()
            for word in query_words:
                if word in title_lower:
                    score += 1.0
                if word in content_lower:
                    score += 0.5

            # Count occurrences in content
            score += content_lower.count(query_lower) * 0.1

            if score > 0:
                # Generate snippet
                snippet = self._highlight_snippet(plan["content"], query)

                scored_plans.append(
                    {
                        "id": plan["id"],
                        "title": plan["title"],
                        "content": snippet,
                        "full_content": plan["content"],
                        "status": plan["status"],
                        "relevance_score": float(score),
                        "metadata": {
                            **plan["metadata"],
                            "source": "plans",
                        },
                    }
                )

        # Sort by score and limit
        scored_plans.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_plans[:limit]

    # -------------------------------------------------------------------------
    # Result Quality Improvements
    # -------------------------------------------------------------------------

    def _highlight_snippet(self, content: str, query: str, context_chars: int = 150) -> str:
        """
        Extract snippet with query terms highlighted.

        Args:
            content: Full content text
            query: Search query for finding match position
            context_chars: Characters of context around match

        Returns:
            Snippet with **bold** markers around matched terms
        """
        if not content or not query:
            return content[:300] if content else ""

        content_lower = content.lower()
        query_terms = [t.lower() for t in query.split() if len(t) > 2]

        # Find first match position
        best_pos = len(content)
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1 and pos < best_pos:
                best_pos = pos

        if best_pos == len(content):
            best_pos = 0  # No match found, start from beginning

        # Extract context window
        start = max(0, best_pos - context_chars // 2)
        end = min(len(content), best_pos + context_chars)
        snippet = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _deduplicate_results(
        self, results: list[dict[str, Any]], similarity_threshold: float = 0.95
    ) -> list[dict[str, Any]]:
        """
        Remove near-duplicate results using content hashing.

        Args:
            results: List of search results
            similarity_threshold: Unused (simple hash-based dedup)

        Returns:
            Deduplicated results list
        """
        import hashlib

        seen_hashes = set()
        unique = []

        for r in results:
            # Hash first 200 chars of content
            content = r.get("content", r.get("display", ""))[:200]
            content_hash = hashlib.md5(content.encode()).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(r)

        return unique

    def _apply_recency_boost(
        self, results: list[dict[str, Any]], half_life_days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Boost recent results using exponential decay.

        Args:
            results: List of search results
            half_life_days: Days for score to decay by 50%

        Returns:
            Results with updated 'score' field (70% similarity + 30% recency)
        """
        from datetime import datetime

        now = time.time()

        for r in results:
            timestamp = r.get("timestamp", 0)

            # Parse timestamp if string
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timestamp = dt.timestamp()
                except (ValueError, TypeError):
                    timestamp = 0

            # Calculate age and decay
            if timestamp:
                age_days = (now - timestamp) / 86400
                decay = 0.5 ** (age_days / half_life_days)
            else:
                decay = 0.5  # Unknown age gets neutral score

            # Combined score: 70% relevance + 30% recency
            similarity = r.get("similarity", r.get("fts_rank", 0.5))
            if isinstance(similarity, float) and similarity < 0:
                # FTS5 BM25 returns negative scores (lower is better)
                similarity = 1.0 / (1.0 - similarity)  # Normalize
            r["score"] = float(similarity) * 0.7 + decay * 0.3

        return results

    # -------------------------------------------------------------------------
    # Incremental Indexing Support
    # -------------------------------------------------------------------------

    def _get_index_state_path(self) -> Path:
        """Get path to CHS index state file."""
        return _csf_root / "data" / "chs_index_state.json"

    def _acquire_state_lock(self) -> tuple[bool, Any]:
        """Acquire exclusive lock on state file. Returns (acquired, lock_file)."""
        STATE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock_file = open(STATE_LOCK_PATH, "xb")
            lock_file.write(str(os.getpid()).encode())
            return True, lock_file
        except FileExistsError:
            return False, None

    def _release_state_lock(self, lock_file: Any) -> None:
        """Release exclusive state lock."""
        if lock_file:
            try:
                lock_file.close()
                STATE_LOCK_PATH.unlink()
            except (OSError, FileNotFoundError):
                pass

    def _get_last_indexed_id(self) -> int:
        """Get the last indexed message ID from state file."""
        state_path = self._get_index_state_path()
        if state_path.exists():
            try:
                import json

                state = json.loads(state_path.read_text())
                return state.get("last_id", 0)
            except Exception:
                pass
        return 0

    def _save_last_indexed_id(self, last_id: int) -> None:
        """Save the last indexed message ID to state file (idempotent, monotonic)."""
        acquired, lock_file = self._acquire_state_lock()
        if not acquired:
            # Another process holds the lock — skip write to avoid state corruption
            logger.debug("State file locked by another process, skipping write")
            return
        try:
            state_path = self._get_index_state_path()
            import json
            from datetime import datetime

            # Read current state to ensure monotonic update
            current_id = 0
            if state_path.exists():
                try:
                    current_state = json.loads(state_path.read_text())
                    current_id = current_state.get("last_id", 0)
                except Exception:
                    pass

            # Only advance — never overwrite with a lower value
            if last_id > current_id:
                state = {
                    "last_id": last_id,
                    "updated": datetime.now().isoformat(),
                }
                state_path.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save index state: {e}")
        finally:
            self._release_state_lock(lock_file)

    def _load_chs_messages_incremental(self, batch_size: int = 500) -> list[dict[str, Any]]:
        """
        Load only new messages since last index.

        Supports both V2 schema (messages + raw_json) and
        legacy schema (chat_messages + metadata).

        Args:
            batch_size: Maximum messages to load per batch

        Returns:
            List of new messages to index
        """
        last_id = self._get_last_indexed_id()
        db_path = self._get_chs_db_path()

        if not db_path.exists():
            return []

        try:
            with sqlite3.connect(str(db_path), timeout=1.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Detect schema version
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
                )
                is_v2_schema = cursor.fetchone() is not None

                if is_v2_schema:
                    # V2 schema: messages table with raw_json column
                    metadata_expr = "COALESCE(raw_json, '{}')"
                    messages_table = "messages"
                else:
                    # Legacy schema: chat_messages table with metadata column
                    metadata_expr = "metadata"
                    messages_table = "chat_messages"

                cursor = conn.execute(
                    f"""
                    SELECT id, session_id, role, content, timestamp, {metadata_expr} as metadata
                    FROM {messages_table}
                    WHERE id > ?
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (last_id, batch_size),
                )

                messages = []
                for row in cursor.fetchall():
                    metadata_raw = row["metadata"] if row["metadata"] else "{}"
                    try:
                        metadata = json.loads(metadata_raw) if metadata_raw else {}
                    except json.JSONDecodeError:
                        metadata = {}

                    messages.append(
                        {
                            "id": str(row["id"]),
                            "session_id": row["session_id"],
                            "role": row["role"],
                            "content": row["content"],
                            "timestamp": row["timestamp"],
                            "metadata": metadata,
                        }
                    )

                if messages:
                    logger.info(f"Found {len(messages)} new messages since ID {last_id}")
                return messages

        except sqlite3.OperationalError as e:
            # Database locked — fail fast rather than blocking
            logger.debug(f"CHS database locked, skipping incremental load: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load incremental messages: {e}")
            return []

    def _mock_init_with_desktop_dir(self, desktop_dir: Path) -> None:
        """
        Test helper method to initialize daemon with a mock Desktop directory.

        This method is used by tests to simulate a Desktop conversations directory
        in a temporary location. It initializes the desktop_jsonl_watcher with
        the provided directory.

        Args:
            desktop_dir: Path to the mock Desktop conversations directory
        """
        from src.ingestion.jsonl_watcher import JsonlWatcher

        # Initialize basic attributes
        self._num_workers = 8
        self._running = False
        self._ready = False
        self._server_thread = None
        self._executor = None
        self._stop_event = threading.Event()
        self._pipe_handle = None
        self._last_request_time = time.time()
        self._last_staleness_update = 0
        self._last_heavy_task_time = 0
        self._last_chs_reindex_time = 0
        self._last_faiss_update_time = 0
        self._faiss_update_enabled = True
        self._faiss_updating = False
        self._staleness_cache = {"entries": {}, "last_updated": 0}
        self._stats_lock = threading.Lock()
        self._stats = {
            "requests_processed": 0,
            "errors": 0,
            "total_duration_ms": 0,
            "active_connections": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self._exit_code = 0
        self._cks = None
        self._chs = None
        self._chs_lock = threading.Lock()
        self._chs_indexing = False
        self._chs_index_lock = threading.Lock()
        self._chs_index_thread = None
        self._chs_index_complete = threading.Event()
        self._category_embeddings = {}
        self._intent_model = None

        # Initialize streaming JsonlWatcher with a mock path
        history_jsonl_path = Path.home() / ".claude" / "history.jsonl"
        self.jsonl_watcher = JsonlWatcher(watch_file=history_jsonl_path)
        self.jsonl_watcher._callback = self._on_jsonl_file_changed
        if self.jsonl_watcher.watch_file:
            self.jsonl_watcher._start_watching()
        self._jsonl_watcher_thread = None

        # Initialize Desktop JsonlWatcher with the provided test directory
        self.desktop_jsonl_watcher = None
        jsonl_files = list(desktop_dir.glob("*.jsonl"))
        if jsonl_files:
            desktop_jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_mtime)
            self.desktop_jsonl_watcher = JsonlWatcher(watch_file=desktop_jsonl_path)
            self.desktop_jsonl_watcher._callback = self._on_desktop_jsonl_file_changed
            if self.desktop_jsonl_watcher.watch_file:
                self.desktop_jsonl_watcher._start_watching()
        self._desktop_jsonl_watcher_thread = None

        # Initialize other components - migrated to search_research package
        from search_research.backends.local.chs_incremental import (
            IncrementalIndexUpdater,
        )

        self._incremental_updater = IncrementalIndexUpdater()
        self._watermark_state = {}
        self._last_watermark_save_time = 0.0
        self._watermark_state_path = _csf_root / "data" / "watermark_state.json"
        from search_research.cache import QueryCache

        # Use size-bounded cache to prevent unbounded memory growth (Python's lru_cache default is 128)
        self.query_cache = QueryCache(max_size=128, ttl_seconds=3600)


# =============================================================================
# Module initialization
# =============================================================================

__all__ = [
    "PIPE_NAME",
    "STARTUP_TIMEOUT",
    "IDLE_WORK_SHORT",
    "IDLE_WORK_LONG",
    "IDLE_SHUTDOWN_TIMEOUT",
    "REQUEST_TIMEOUT",
    "TYPE_HALF_LIVES",
    "SemanticClient",
    "UnifiedSemanticDaemon",
    "get_global_daemon",
    "get_or_start_daemon",
    "main",
]


# =============================================================================
# Standalone daemon entry point
# =============================================================================


def main() -> int:
    """
    Run the semantic daemon as a standalone process.

    This entry point allows the daemon to run as a persistent background
    process that survives the parent (hook) process exit.

    Usage:
        python -m lib.daemons.unified_semantic_daemon
    """
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Unified Semantic Daemon for CKS/CHS search")
    parser.add_argument(
        "--pipe-name",
        default=PIPE_NAME,
        help=f"Named pipe name (default: {PIPE_NAME})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of worker threads (default: 3)",
    )
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=int(IDLE_SHUTDOWN_TIMEOUT or 0),
        help=f"Idle timeout in seconds (0 = no auto-shutdown, default: {IDLE_SHUTDOWN_TIMEOUT or 'disabled'}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    # Use command-line idle timeout if specified (0 = no auto-shutdown)
    idle_timeout = float(args.idle_timeout) if args.idle_timeout > 0 else None

    # Time-based idle timeout: disabled until 9pm, then 30 minutes
    # Command-line arg overrides time-based setting
    if args.idle_timeout == 0:  # Only apply time-based logic if not explicitly set
        import datetime

        current_hour = datetime.datetime.now().hour
        if current_hour >= HOUR_9PM:
            idle_timeout = IDLE_TIMEOUT_AFTER_9PM  # 30 minutes after 9pm

    # Configure logging with file handler for pythonw.exe compatibility
    # Without a file handler, logger output goes to stderr which doesn't exist in pythonw.exe
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if args.verbose
        else "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler(DAEMON_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(log_formatter)

    logging.root.handlers = []  # Clear any existing handlers
    logging.root.addHandler(file_handler)
    logging.root.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    # Create and start daemon
    daemon = UnifiedSemanticDaemon(pipe_name=args.pipe_name, num_workers=args.workers)

    # Register atexit handler to clean up discovery file on crash/unexpected exit
    # This prevents zombie accumulation if daemon crashes abnormally
    def cleanup_on_exit():
        try:
            daemon._cleanup_discovery_file()
        except Exception:
            pass  # Suppress errors during atexit cleanup
        # AT-006: Also release daemon mutex on abnormal exit
        try:
            if daemon._daemon_mutex_handle and win32api:
                win32api.CloseHandle(daemon._daemon_mutex_handle)
                daemon._daemon_mutex_handle = None
        except Exception:
            pass  # Suppress errors during atexit cleanup

    atexit.register(cleanup_on_exit)

    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        daemon.handle_shutdown_signal(signal.Signals(signum).name)
        # Ensure discovery file cleanup on signal
        daemon._cleanup_discovery_file()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting semantic daemon as standalone process...")
    if not daemon.start():
        # Check if it's age-based self-termination (expected behavior)
        # Age-based termination is NOT a startup failure - it's a feature
        # to prevent old daemon instances from running indefinitely
        if daemon._should_terminate_based_on_age():
            age = int(time.time() - daemon.timestamp)
            logger.info(
                f"Daemon self-terminated based on age (age={age}s, pid={daemon.pid}). "
                f"This is expected behavior to prevent old daemon accumulation."
            )
            return 0  # Success, not a failure
        else:
            logger.warning("Failed to start daemon")
            return 1  # Actual failure

    logger.info(f"Semantic daemon running on {args.pipe_name}")
    if idle_timeout:
        logger.info(f"Auto-shutdown after {int(idle_timeout)}s idle")
    else:
        logger.info("Auto-shutdown disabled (daemon runs indefinitely)")
    logger.info("Press Ctrl+C to stop")

    # Keep main thread alive with idle timeout
    exit_code = 0
    try:
        while daemon.is_running():
            time.sleep(1)
            # Check for idle timeout (if enabled)
            if idle_timeout:
                idle_seconds = daemon.get_idle_seconds()
                if idle_seconds > idle_timeout:
                    logger.info(f"Idle timeout ({idle_seconds:.0f}s), shutting down")
                    break
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        daemon.shutdown()
        exit_code = daemon.exit_code()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
