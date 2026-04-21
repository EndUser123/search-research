### P:\packages\search-research\contrib\__init__.py

```python

```


### P:\packages\search-research\contrib\semantic_daemon\__init__.py

```python
from .daemon_client import DaemonClient
from .unified_semantic_daemon import SemanticClient, UnifiedSemanticDaemon
__all__ = [
    "UnifiedSemanticDaemon",
    "SemanticClient",
    "DaemonClient",
]
```


### P:\packages\search-research\contrib\semantic_daemon\build_impl.py

```python
from pathlib import Path
p = Path("src/lib/daemons/unified_semantic_daemon.py")
header = p.read_text(encoding="utf-8")
lines = header.split("\\n")
lines = lines[:i]
```


### P:\packages\search-research\contrib\semantic_daemon\cks_daemon_discovery.py

```python
import sys
from pathlib import Path
query_cks_daemon(query: str, limit: int = 5) -> dict | None
test_queries = [
        "git multi-terminal race condition",
        "questioning patterns",
        "working principles",
    ]
response = query_cks_daemon(query, limit=2)
results = response.get("results", [])
title = r.get("title", "No title")
content = r.get("content", "")[:150]
```


### P:\packages\search-research\contrib\semantic_daemon\daemon_client.py

```python
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
import pywintypes
import win32file
import win32pipe
logger = logging.getLogger(__name__)
CSF_ROOT = Path("P:/__csf")
DISCOVERY_FILE = CSF_ROOT / "data" / "semantic_daemon_discovery.json"

class DaemonClientManager:
    @classmethod
    get_instance(cls) -> DaemonClient
    @classmethod
    get_backend_type(cls) -> str | None
    @classmethod
    reset(cls)

class DaemonClient:
    __init__(self, pipe_name: str | None = None, backend_type: str | None = None, timeout: float = 10.0, max_retries: int = 2, enable_fallback: bool = False, auto_start: bool = True)
    get_backend_type(self) -> str | None
    search(self, backend: str, query: str, limit: int = 20) -> dict
    embed_texts(self, texts: list[str]) -> list[bytes]
    is_daemon_alive(self, timeout: float = 0.5) -> bool
    query(self, action: str, params: dict, timeout: float = 2.5) -> dict
    shutdown(self)
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
search_cks(query: str, limit: int = 20, auto_start: bool = False) -> dict
search_chs(query: str, limit: int = 20, auto_start: bool = False) -> dict
```


### P:\packages\search-research\contrib\semantic_daemon\daemon_keep_alive.py

```python
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final
signal_handler(signum: int, frame) -> None
setup_signal_handlers() -> None
get_pid_file_path() -> Path
write_pid_file() -> None
remove_pid_file() -> None
is_keep_alive_running() -> bool
start_daemon_process() -> subprocess.Popen | None
calculate_respawn_delay(attempt: int) -> float
run_keep_alive_loop(idle_timeout: int) -> None
parse_args() -> argparse.Namespace
main() -> int
```


### P:\packages\search-research\contrib\semantic_daemon\unified_semantic_daemon.py

```python
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

class IntentClassificationResult(TypedDict):
    intent = IntentCategory
    confidence = float
import structlog
logger = structlog.get_logger()
import pywintypes
import win32api
import win32con
import win32event
import win32file
import win32pipe
import winerror
WIN32_AVAILABLE = True
WIN32_AVAILABLE = False
win32api = win32con = winerror = win32event = win32file = win32pipe = pywintypes = None
from search_research.cache import QueryCache
PIPE_NAME = r"\\.\pipe\csf_semantic"
DISCOVERY_FILE = Path("P:/__csf/data/semantic_daemon_discovery.json")
PID_FILE = Path("P:/__csf/data/semantic_daemon.pid")
MAX_DAEMON_AGE = 3600
DAEMON_MUTEX_NAME = r"Global\CSF_SemanticDaemon_Instance"
DAEMON_LOG_FILE = Path("P:/__csf/data/semantic_daemon.log")
STARTUP_TIMEOUT = 6.0
IDLE_WORK_SHORT = 5.0
IDLE_WORK_LONG = 900.0
CHS_REINDEX_INTERVAL = 300.0
FAISS_UPDATE_INTERVAL = 600.0
FAISS_MAX_AGE = 86400.0
FAISS_INDEX_PATH = _csf_root / "data" / "chat_history_faiss_424k"
FAISS_STATE_PATH = _csf_root / "data" / "chs_index_state.json"
FAISS_LOCK_PATH = _csf_root / ".data" / "daemon" / "faiss_update.lock"
STATE_LOCK_PATH = _csf_root / ".data" / "daemon" / "index_state.lock"
IDLE_SHUTDOWN_TIMEOUT = None
REQUEST_TIMEOUT = 5.0
MAX_PIPE_SIZE = 65536
BUF_SIZE = 4096
IDLE_TIMEOUT_AFTER_9PM = 1800
HOUR_9PM = 21
TYPE_HALF_LIVES = {
    "memory": 180,
    "correction": 365,
    "pattern": 120,
    "learning": 730,
    "code": 90,
    "insight": 365,
}
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
MAX_MEMORY_MB = (
    8192  # 8GB cap per daemon instance (self-termination) - increased to handle CKS+FAISS+overhead
)
STARTUP_MEMORY_HEADROOM_MB = 1024
FAISS_ESTIMATED_MEMORY_MB = 350
CKS_MODEL_MEMORY_MB = (
    4000  # Actual all-mpnet-base-v2 model memory (observed: ~4000MB in production)
)
SENTENCE_TRANSFORMER_MEMORY_MB = 200
get_global_daemon() -> UnifiedSemanticDaemon
get_or_start_daemon() -> UnifiedSemanticDaemon

class SemanticClient:
    __init__(self, pipe_name: str = PIPE_NAME, auto_start: bool = True)
    create_request(self, scope: str, query: str, limit: int = 5) -> dict[str, Any]
    connect(self, timeout: float = REQUEST_TIMEOUT) -> bool
    disconnect(self) -> None
    is_connected(self) -> bool
    send_request(self, request: dict[str, Any]) -> dict[str, Any]
    send_raw(self, request: dict[str, Any]) -> dict[str, Any]
    search(self, scope: str, query: str, limit: int = 10) -> dict[str, Any]
    classify_intent(self, text: str) -> IntentCategory

class UnifiedSemanticDaemon:
    __init__(self, pipe_name: str = PIPE_NAME, num_workers: int = 8)
    @property
    pipe_name(self) -> str
    start(self) -> bool
    stop(self, force: bool = False) -> None
    shutdown(self, wait_for_requests: bool = True, timeout: float = 5.0) -> bool
    is_running(self) -> bool
    is_ready(self) -> bool
    search(self, scope: str, query: str, limit: int = 10) -> dict[str, Any]
    pipe_exists(self) -> bool
    create_client(self) -> SemanticClient
    get_statistics(self) -> dict[str, Any]
    get_active_connection_count(self) -> int
    get_queue_size(self) -> int
    get_idle_seconds(self) -> float
    get_last_staleness_cache_update(self) -> float
    get_staleness_cache(self) -> dict[str, Any]
    update_staleness_cache(self) -> None
    get_type_half_lives(self) -> dict[str, int]
    check_idle_work(self) -> None
    last_heavy_task_time(self) -> float
    get_chs_index_status(self) -> dict[str, Any]
    get_health_status(self) -> dict[str, Any]
    handle_shutdown_signal(self, signal_name: str) -> None
    exit_code(self) -> int
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
main() -> int
```


### P:\packages\search-research\contrib\semantic_daemon\write_full.py

```python
from pathlib import Path
content = Path("src/lib/daemons/unified_semantic_daemon.py").read_text(encoding="utf-8")
```


### P:\packages\search-research\core\__init__.py

```python
__version__ = "0.1.0"
from .analysis import (
    Contradiction, ContradictionDetector, CoverageGap, DensityCalculator, GapAnalyzer, GapType, NoveltyTracker, TopicClusterer, TopicSignature, )
from .backends import (
    BACKEND_KG, BACKEND_NAME, BACKEND_PERSONA, KGBackend, PersonaMemoryBackend, RLMBackend, SecurityError, )
from .chat_search_security import (
    ChatSearchSecurityManager, InputValidator, RateLimiter, ResourceMonitor, SecurityEvent, SecurityEventType, SecurityLevel, SecurityMonitor, )
from .config import ResearchConfig
from .enhancement import (
    ExecutionStatus, LearningSystem, ModeCombination, ModeExecutionResult, ModeRelationshipMapper, MultiModeOrchestrator, OptimizationResult, OrchestratedResult, PatternInsight, QualityPredictor, QueryDependencies, ResearchDepth, ResearchFeedback, ResearchMode, SimplifiedDependencyAnalyzer, )
from .hybrid_ensemble import (
    EnsembleResult, HybridEnsembleConfig, SearchResult, run_hybrid_ensemble, )
from .hyde import apply_hyde, enhance_query, extract_key_phrases
from .hyde_chapters import HydeChapter, HydeChapterConfig, generate_hyde_chapters
from .hyde_chapters_comprehensive import (
    HydeChapter as HydeChapterComprehensive, )
from .hyde_chapters_comprehensive import (
    HydeChapterConfig as HydeChapterConfigComprehensive, )
from .hyde_chapters_comprehensive import (
    generate_hyde_chapters as generate_hyde_chapters_comprehensive, )
from .hyde_multi_perspective import (
    HypotheticalDocument, MultiHyDEConfig, MultiHypotheticalDocuments, generate_multi_hypothetical_documents, )
from .hyde_multi_perspective_comprehensive import (
    MultiHyDEConfig as MultiHyDEConfigComprehensive, )
from .hyde_multi_perspective_comprehensive import (
    MultiHypotheticalDocuments as MultiHypotheticalDocumentsComprehensive, )
from .hyde_multi_perspective_comprehensive import (
    generate_multi_hypothetical_documents as generate_multi_hypothetical_documents_comprehensive, )
from .hyde_retrieval import (
    HyDERetrievalConfig, HyDERetrievalResult, extract_retrieval_query, search_with_hyde, )
from .hyde_single import (
    HyDEConfig, create_hypothetical_document, generate_hypothetical_document, )
from .hyde_single import (
    HypotheticalDocument as HypotheticalDocumentSingle, )
from .models import EnhancedQuery, ResearchResult
from .models import SearchResult as SearchResultV2
from .modes import Mode
from .orchestration import CostTracker, PhaseController, PhaseResult
from .orchestrator import ResearchEngine
from .processing import NormalizedResult as ProcessingResult
from .processing import ResultNormalizer, SourceType
from .quality_checker import QualityConfig, is_satisfactory
from .query import (
    QueryExpander, expand_query_if_enabled, get_abbreviation_mappings, get_query_suggestions, get_synonym_mappings, )
from .result_merger import FusedResult
from .result_merger import reciprocal_rank_fusion as reciprocal_rank_fusion_merger
from .result_normalizer import NormalizedResult, normalize_result
from .results import (
    DeduplicationProcessor, RankingProcessor, ResultProcessingPipeline, SynthesisProcessor, apply_temporal_boosting, calculate_temporal_boost, maximal_marginal_relevance, reciprocal_rank_fusion, weighted_average_fusion, )
from .results import (
    EnsembleResult as EnsembleResultV2, )
from .results import (
    HybridEnsembleConfig as HybridEnsembleConfigV2, )
from .results import (
    run_hybrid_ensemble as run_hybrid_ensemble_v2, )
from .router_async import AsyncSearchRouter, create_async_router
from .unified_router import UnifiedAsyncRouter
UnifiedRouter = UnifiedAsyncRouter
SearchRouter = UnifiedAsyncRouter
__all__ = [
    "AsyncSearchRouter",
    "UnifiedAsyncRouter",
    "UnifiedRouter",  # Compatibility alias
    "SearchRouter",  # Compatibility alias
    "SearchResult",
    "create_async_router",
    "Mode",
    "__version__",
    # Backends
    "BACKEND_KG",
    "BACKEND_NAME",
    "BACKEND_PERSONA",
    "KGBackend",
    "PersonaMemoryBackend",
    "RLMBackend",
    "SecurityError",
    # Core research engine
    "ResearchEngine",
    "ResearchConfig",
    "ResearchResult",
    "EnhancedQuery",
    "SearchResultV2",
    # HyDE core functions
    "apply_hyde",
    "extract_key_phrases",
    "enhance_query",
    # HyDE multi-chapter (simple)
    "HydeChapter",
    "HydeChapterConfig",
    "generate_hyde_chapters",
    # HyDE multi-chapter (comprehensive)
    "HydeChapterComprehensive",
    "HydeChapterConfigComprehensive",
    "generate_hyde_chapters_comprehensive",
    # HyDE multi-perspective (simple)
    "HypotheticalDocument",
    "MultiHyDEConfig",
    "MultiHypotheticalDocuments",
    "generate_multi_hypothetical_documents",
    # HyDE multi-perspective (comprehensive)
    "MultiHyDEConfigComprehensive",
    "MultiHypotheticalDocumentsComprehensive",
    "generate_multi_hypothetical_documents_comprehensive",
    # HyDE single document
    "HypotheticalDocumentSingle",
    "HyDEConfig",
    "create_hypothetical_document",
    "generate_hypothetical_document",
    # HyDE retrieval
    "HyDERetrievalConfig",
    "HyDERetrievalResult",
    "extract_retrieval_query",
    "search_with_hyde",
    # Hybrid ensemble
    "HybridEnsembleConfig",
    "SearchResult",
    "EnsembleResult",
    "run_hybrid_ensemble",
    # Query processing
    "NormalizedResult",
    "normalize_result",
    "FusedResult",
    "reciprocal_rank_fusion_merger",
    "ProcessingResult",
    "ResultNormalizer",
    "SourceType",
    "QualityConfig",
    "is_satisfactory",
    "QueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    "get_synonym_mappings",
    "get_abbreviation_mappings",
    # Results processing
    "DeduplicationProcessor",
    "RankingProcessor",
    "SynthesisProcessor",
    "ResultProcessingPipeline",
    "maximal_marginal_relevance",
    "apply_temporal_boosting",
    "calculate_temporal_boost",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "EnsembleResultV2",
    "HybridEnsembleConfigV2",
    "run_hybrid_ensemble_v2",
    # Analysis & Quality Components
    "GapAnalyzer",
    "CoverageGap",
    "GapType",
    "ContradictionDetector",
    "Contradiction",
    "DensityCalculator",
    "TopicClusterer",
    "TopicSignature",
    "NoveltyTracker",
    # Orchestration Components
    "PhaseController",
    "PhaseResult",
    "CostTracker",
    # Enhancement Components
    "SimplifiedDependencyAnalyzer",
    "QueryDependencies",
    "ResearchDepth",
    "LearningSystem",
    "PatternInsight",
    "ResearchFeedback",
    "ModeRelationshipMapper",
    "ResearchMode",
    "ModeCombination",
    "MultiModeOrchestrator",
    "ExecutionStatus",
    "ModeExecutionResult",
    "OrchestratedResult",
    "QualityPredictor",
    "OptimizationResult",
    # Security Components (migrated from chat_search_security)
    "ChatSearchSecurityManager",
    "InputValidator",
    "RateLimiter",
    "ResourceMonitor",
    "SecurityEvent",
    "SecurityEventType",
    "SecurityLevel",
    "SecurityMonitor",
]
```


### P:\packages\search-research\core\analysis\__init__.py

```python
from .contradiction_detector import Contradiction, ContradictionDetector
from .density_calculator import DensityCalculator
from .gap_analyzer import CoverageGap, GapAnalyzer, GapType
from .topic_clusterer import NoveltyTracker, TopicClusterer, TopicSignature
__all__ = [
    "GapAnalyzer",
    "CoverageGap",
    "GapType",
    "ContradictionDetector",
    "Contradiction",
    "DensityCalculator",
    "TopicClusterer",
    "TopicSignature",
    "NoveltyTracker",
]
```


### P:\packages\search-research\core\analysis\contradiction_detector.py

```python
import logging
import re
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class ResearchResult:
    title = str
    url = str
    content = str
    source = str

@total_ordering
@dataclass
class Contradiction:
    topic = str
    description = str
    sources_conflicting = list[str]
    __lt__(self, other: Contradiction) -> bool

class ContradictionDetector:
    CONTRADICTION_PATTERNS = [
        (r"(only supports?|only|仅支持|目前\s+仅支持|目前\s+仅)", "exclusive_claim"),
        (r"(not supported|unsupported|不支持|cannot|无法)", "negative_claim"),
        (r"(supports?|支持)\s+(both|and|和|or|或)", "inclusive_claim"),
        (r"(currently|目前|at this time)\s+(only|仅|not)", "temporal_claim"),
    ]
    __init__(self) -> None
    detect_contradictions(self, results: list[ResearchResult] | list[dict[str, Any]], query: str) -> list[Contradiction]
    get_contradiction_summary(self, contradictions: list[Contradiction]) -> str
```


### P:\packages\search-research\core\analysis\density_calculator.py

```python
from re import findall

class DensityCalculator:
    TECHNICAL_TERMS = {
        "api", "endpoint", "json", "xml", "sql", "database", "query",
        "async", "await", "thread", "process", "protocol", "http",
        "config", "timeout", "connection", "pool", "serial", "format",
        "parse", "serialize", "deserialize", "encode", "decode",
        "authentication", "authorization", "token", "session", "cookie",
        "function", "method", "class", "object", "interface", "type",
        "variable", "parameter", "argument", "return", "exception",
        "error", "warning", "debug", "log", "trace", "profile",
    }
    compute_numeric_density(self, results: list) -> float
    compute_technical_density(self, results: list) -> float
    compute_density(self, results: list) -> float
```


### P:\packages\search-research\core\analysis\gap_analyzer.py

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class GapType(Enum):
    MISSING_SOURCE_TYPE = "missing_source_type"
    LOW_DOMAIN_DIVERSITY = "low_domain_diversity"
    LOW_TOPIC_COVERAGE = "low_topic_coverage"

@dataclass
class CoverageGap:
    gap_type = GapType
    description = str
    severity = float

class GapAnalyzer:
    MIN_SOURCE_TYPES = 3
    MIN_DOMAINS = 3
    MIN_TOPICS = 2
    SOURCE_TYPE_PRIORITY = {
        "academic": "paper research academic arxiv study",
        "docs": "documentation official guide reference",
        "community": "stackoverflow reddit discussion community",
        "video": "video tutorial youtube course",
        "blog": "blog article tutorial guide",
        "vendor": "official vendor documentation guide",
    }
    detect_gaps(self, results: Any, topics: set[str], source_types: set[str], domains: set[str]) -> list[CoverageGap]
    generate_follow_up_query(self, original_query: str, gap: CoverageGap) -> str
```


### P:\packages\search-research\core\analysis\topic_clusterer.py

```python
from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
from re import findall
from typing import Any

@dataclass
class TopicSignature:
    topic_id = str
    keyword_hash = int
    keywords = set[str]

@dataclass
class CoverageState:
    pass

class TopicClusterer:
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these",
        "those", "it", "its", "get", "use", "make", "when", "what", "how",
        "all", "each", "more", "some", "such", "only", "own", "same", "so",
        "than", "too", "very", "just", "also", "now", "new", "first", "last",
        "into"
    }
    __init__(self) -> None
    extract_keywords(self, text: str, top_n: int = 6) -> set[str]
    cluster_results(self, results: Any) -> dict[str, TopicSignature]

class NoveltyTracker:
    __init__(self, novelty_threshold: float = 0.05)
    compute_coverage_state(self, results: Any, clusters: dict[str, TopicSignature]) -> CoverageState
    extract_keywords(self, text: str, top_n: int = 6) -> set[str]
    compute_novelty(self, current: CoverageState, previous: CoverageState) -> float
    should_continue(self, current_state: CoverageState) -> bool
```


### P:\packages\search-research\core\backend_health.py

```python
import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
from .terminal_id import canonical_terminal_id
HealthStatus = Literal["ready", "degraded", "down"]

@dataclass
class BackendHealth:
    name = str
    status = HealthStatus
    consecutive_failures = int
    last_error = str | None
    next_retry = float
    should_retry(self) -> bool
    record_success(self) -> None
    record_failure(self, error: str) -> None

class BackendHealthRegistry:
    __init__(self)
    get_status(self, backend: str) -> BackendHealth | None
    get_all_status(self) -> dict[str, BackendHealth]
    is_available(self, backend: str) -> bool
    record_result(self, backend: str, success: bool, error: str | None = None) -> None
```


### P:\packages\search-research\core\backends\__init__.py

```python
from .kg import BACKEND_KG, KGBackend
from .persona import BACKEND_PERSONA, PersonaMemoryBackend
from .rlm import BACKEND_NAME, RLMBackend, SecurityError
__all__ = [
    # KG backend
    "BACKEND_KG",
    "KGBackend",
    # Persona backend
    "BACKEND_PERSONA",
    "PersonaMemoryBackend",
    # RLM backend
    "BACKEND_NAME",
    "RLMBackend",
    "SecurityError",
]
```


### P:\packages\search-research\core\backends\base\__init__.py

```python
from .code_analysis_backend import CodeAnalysisBackend
__all__ = ["CodeAnalysisBackend"]
```


### P:\packages\search-research\core\backends\base\code_analysis_backend.py

```python
import logging
from abc import ABC, abstractmethod
from typing import Any
logger = logging.getLogger(__name__)

class CodeAnalysisBackend(ABC):
    @abstractmethod
    get_dependents(self, entity_id: str, limit: int = 0) -> list[str]
    @abstractmethod
    get_dependencies(self, entity_id: str, limit: int = 0) -> list[str]
    @abstractmethod
    get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]
    @abstractmethod
    get_entity(self, entity_id: str) -> dict[str, Any] | None
    @abstractmethod
    search(self, query: str, limit: int = 10) -> list[dict[str, Any]]
    get_related(self, entity_id: str, limit: int = 20) -> list[str]
    impact_analysis(self, entity_id: str) -> dict[str, Any]
    get_related_multi_hop(self, entity_id: str, depth: int = 2, limit: int = 50) -> dict[str, list[str]]
    get_impact_summary(self, entity_ids: list[str]) -> dict[str, Any]
    find_common_dependencies(self, entity_ids: list[str], limit: int = 10) -> list[tuple[str, int]]
    validate_entity_exists(self, entity_id: str) -> bool
    get_entity_context(self, entity_id: str, include_depth: int = 1) -> dict[str, Any]
__all__ = [
    "CodeAnalysisBackend",
]
```


### P:\packages\search-research\core\backends\kg.py

```python
from pathlib import Path
from typing import Any
from ..config import config
SearchResult = dict[str, Any]
BACKEND_KG = "KG"

class KGBackend:
    __init__(self, kg_data_path: str | None = None)
    @property
    kg_data_path(self)
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
__all__ = ["BACKEND_KG", "KGBackend"]
```


### P:\packages\search-research\core\backends\local\__init__.py

```python
from .cds_backend import CDSBackend
from .chs_incremental import IncrementalIndexUpdater
from .cks_metadata_backend import (
    BACKEND_CKS_METADATA, CKSMetadataBackend, create_cks_metadata_backend, )
from .claude_history_backend import (
    BACKEND_CLAUDE_HISTORY, ClaudeHistoryBackend, create_claude_history_backend, )
from .enhanced_cds_backend import EnhancedCDSBackend
from .grep_backend import GrepBackend
from .kg_backend import BACKEND_KG, KGBackend
from .multilang_backend import (
    BACKEND_MULTILANG, SOURCE_RELIABILITY_MULTILANG, MultiLangCodeBackend, create_multilang_backend, )
from .notebooklm_backend import (
    BACKEND_NOTEBOOKLM, NotebookLMBackend, create_notebooklm_backend, )
from .rlm_backend import (
    BACKEND_RLM, RLMBackend, create_rlm_backend, is_rlm_available, )
from .skills_backend import BACKEND_SKILLS, SkillsBackend
from .ast_code_backend import ASTCodeBackend, create_ast_backend, BACKEND_AST_CODE
from .call_graph_backend import CallGraphBackend, BACKEND_NAME_CALL_GRAPH
from .cpg_backend import CPGBackend, CPG_AVAILABLE
from .hdma_backend import HDMABackend, HDMA_AVAILABLE
from .lsp_backend import LSPSymbolBackend, create_lsp_backend, BACKEND_LSP_SYMBOL
from .dependency_backend import DependencyBackend, DEP_GRAPH_AVAILABLE
from .qmd_wiki_backend import QMDWikiBackend
from .yt_is_backend import YtIsBackend
BACKEND_QMD_WIKI = "QMD_WIKI"
BACKEND_YT_IS = "yt-is"
__all__ = [
    # Core backends
    "CDSBackend",
    "EnhancedCDSBackend",
    "GrepBackend",
    "MultiLangCodeBackend",
    "SkillsBackend",
    "IncrementalIndexUpdater",
    "CKSMetadataBackend",
    "KGBackend",
    "RLMBackend",
    "ClaudeHistoryBackend",
    "NotebookLMBackend",
    # Extended backends (graceful degradation)
    "ASTCodeBackend",
    "CallGraphBackend",
    "CPGBackend",
    "HDMABackend",
    "LSPSymbolBackend",
    "DependencyBackend",
    "QMDWikiBackend",
    "YtIsBackend",
    # Backend constants
    "BACKEND_NOTEBOOKLM",
    "BACKEND_SKILLS",
    "BACKEND_CKS_METADATA",
    "BACKEND_KG",
    "BACKEND_MULTILANG",
    "BACKEND_RLM",
    "BACKEND_CLAUDE_HISTORY",
    "BACKEND_AST_CODE",
    "BACKEND_LSP_SYMBOL",
    "BACKEND_NAME_CALL_GRAPH",
    "BACKEND_QMD_WIKI",
    "BACKEND_YT_IS",
    "SOURCE_RELIABILITY_MULTILANG",
    # Factory functions
    "create_cks_metadata_backend",
    "create_notebooklm_backend",
    "create_multilang_backend",
    "create_rlm_backend",
    "create_claude_history_backend",
    "create_ast_backend",
    "create_lsp_backend",
    # Availability flags
    "CPG_AVAILABLE",
    "HDMA_AVAILABLE",
    "DEP_GRAPH_AVAILABLE",
]
```


### P:\packages\search-research\core\backends\local\ast_code_backend.py

```python
import ast
import logging
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)
BACKEND_AST_CODE = "AST_CODE"
SOURCE_RELIABILITY_AST = 0.80

class ASTCodeBackend:
    __init__(self, root_paths: list[str] | None = None)
    build_index(self) -> None
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    asearch(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_dependents(self, entity_id: str, limit: int = 50) -> list[str]
    get_dependencies(self, entity_id: str, limit: int = 50) -> list[str]
    get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]
    get_related(self, entity_id: str, limit: int = 50) -> list[str]
    analyze_impact(self, entity_id: str) -> dict[str, Any]
    get_context(self, file_path: str) -> str
create_ast_backend(root_paths: list[str] | None = None) -> ASTCodeBackend
__all__ = [
    "ASTCodeBackend",
    "create_ast_backend",
    "BACKEND_AST_CODE",
    "SOURCE_RELIABILITY_AST",
]
```


### P:\packages\search-research\core\backends\local\base_local_backend.py

```python
from pathlib import Path
from typing import Any
from ...config import config
SearchResult = dict[str, Any]

class BaseLocalBackend:
    DEFAULT_EXCLUDE_PATTERNS = {
        "_archive",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "node_modules",
        ".git",
        "dist",
        "build",
        "*.egg-info",
    }
    __init__(self, root_paths: list[str] | None = None, exclude_patterns: set[str] | None = None) -> None
    build_index(self) -> None
```


### P:\packages\search-research\core\backends\local\call_graph_backend.py

```python
from typing import Any
from modules.discover.static_call_graph import CallGraph, StaticCallGraphBuilder
STATIC_GRAPH_AVAILABLE = True
STATIC_GRAPH_AVAILABLE = False
StaticCallGraphBuilder = None
CallGraph = None
from ...backend_health import BackendHealthRegistry
BACKEND_NAME_CALL_GRAPH = "CALL_GRAPH"

class CallGraphBackend:
    __init__(self, root_paths: list[str] | None = None, enable_health_tracking: bool = True)
    has_index(self) -> bool
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\cds_backend.py

```python
import ast
import hashlib
import hmac
import json
import pickle
import subprocess
import time
from pathlib import Path
from typing import Any
from .base_local_backend import BaseLocalBackend
SearchResult = dict[str, Any]

class CDSBackend(BaseLocalBackend):
    __init__(self, root_paths: list[str] | None = None, cache_dir: str | None = None, enable_cache: bool = True, exclude_patterns: set[str] | None = None) -> None
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
    find_importers(self, module_name: str) -> list[str]
    find_definition(self, symbol_name: str, file_path: str) -> dict[str, Any] | None
    clear_cache(self) -> None
    get_cache_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\chs_incremental.py

```python
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from ...config import config
logger = logging.getLogger(__name__)
import faiss
import numpy as np
HAS_FAISS = True
HAS_FAISS = False

class IncrementalIndexUpdater:
    __init__(self, db_path: str | None = None, index_path: str | None = None, state_path: str | None = None) -> None
    get_new_messages(self, limit: int = 1000) -> list[dict[str, Any]]
    update_index(self, messages: list[dict[str, Any]]) -> dict
    update_from_jsonl(self, session_path: str, watermark_pos: int) -> tuple[int, int]
    run_incremental_update(self, limit: int = 1000) -> dict
```


### P:\packages\search-research\core\backends\local\cks_metadata_backend.py

```python
import json
import sqlite3
from pathlib import Path
from typing import Any
from ...config import config
BACKEND_CKS_METADATA = "CKS_METADATA"

class CKSMetadataBackend:
    __init__(self, db_path: str | None = None) -> None
    search(self, query: str, limit: int = 20, file_path: str | None = None, category: str | None = None, skill_source: str | None = None, line_number: int | None = None) -> list[dict[str, Any]]
    query_file_history(self, file_path: str, limit: int = 100) -> list[dict[str, Any]]
create_cks_metadata_backend(db_path: str | None = None) -> CKSMetadataBackend
```


### P:\packages\search-research\core\backends\local\claude_history_backend.py

```python
import json
import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Any
from .base_local_backend import BaseLocalBackend
SearchResult = dict[str, Any]
logger = logging.getLogger(__name__)
FTS5_SCORE_MIN = 0.7
FTS5_SCORE_SPREAD = 0.3
FTS5_RANK_DEFAULT = 0.5
LIKE_SCORE_EXACT_PREFIX = 0.9
LIKE_SCORE_WORD_BOUNDARY = 0.8
LIKE_SCORE_CONTAINS = 0.7
DIVERSIFICATION_MAX_PER_SESSION = 2
FETCH_LIMIT_MULTIPLIER = 3
FETCH_LIMIT_MAX = 100
SNIPPET_LENGTH = 200
SOURCE_JSONL = "jsonl"
SOURCE_DB = "db"

class ClaudeHistoryBackend(BaseLocalBackend):
    name = "claude-history"
    description = "Fast keyword search for Claude Code chat history using SQLite FTS5"
    source_types = ["chat", "history"]
    __init__(self, root_paths: list[str] | None = None, exclude_patterns: set[str] | None = None, cli_path: str | None = None, db_path: str | None = None, default_source: str = "db")
    build_index(self) -> None
    search(self, query: str, limit: int = 10, source: str | None = None, project: str | None = None) -> list[SearchResult]
    get_session(self, session_id: str) -> list[SearchResult]
    list_sessions(self, project: str | None = None, sort: str = "recent", limit: int = 20) -> list[dict[str, Any]]
    stats(self) -> dict[str, Any]
create_claude_history_backend() -> ClaudeHistoryBackend
BACKEND_CLAUDE_HISTORY = {
    "name": "claude-history",
    "class": ClaudeHistoryBackend,
    "factory": create_claude_history_backend,
    "description": "Fast keyword search for Claude Code chat history",
    "source_types": ["chat", "history"],
}
```


### P:\packages\search-research\core\backends\local\cpg_backend.py

```python
from pathlib import Path
from typing import Any
from modules.discover.code_property_graph import (
        CPGBuilder, CodePropertyGraph, SemanticCPGBuilder, SemanticCPG, )
CPG_AVAILABLE = True
CPG_AVAILABLE = False
CPGBuilder = None
CodePropertyGraph = None
SemanticCPGBuilder = None
SemanticCPG = None
from ...backend_health import BackendHealthRegistry

class CPGBackend:
    __init__(self, root_paths: list[str] | None = None, enable_health_tracking: bool = True, language: str = "python") -> None
    has_index(self) -> bool
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\dependency_backend.py

```python
from pathlib import Path
from typing import Any
from quality.core.dependency_graph import (
        DependencyGraph, DependencyGraphBuilder, build_dependency_graph, Symbol, EdgeKind, )
DEP_GRAPH_AVAILABLE = True
DEP_GRAPH_AVAILABLE = False
DependencyGraph = None
DependencyGraphBuilder = None
build_dependency_graph = None
Symbol = None
EdgeKind = None
from ...backend_health import BackendHealthRegistry

class DependencyBackend:
    __init__(self, root_paths: list[str] | None = None, enable_health_tracking: bool = True) -> None
    has_index(self) -> bool
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\enhanced_cds_backend.py

```python
from pathlib import Path
from typing import Any
from .cds_backend import CDSBackend
SearchResult = dict[str, Any]

class EnhancedCDSBackend(CDSBackend):
    __init__(self, root_paths: list[str] | None = None, cache_dir: str | None = None, enable_cache: bool = True, exclude_patterns: set[str] | None = None)
    discover(self) -> list[dict[str, Any]]
    search(self, query: str, limit: int = 10) -> list[dict[str, Any]]
    retrieve(self, symbol_id: str) -> dict[str, Any]
    metadata(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\grep_backend.py

```python
import ast
import logging
from pathlib import Path
from typing import Any
from .base_local_backend import BaseLocalBackend
SearchResult = dict[str, Any]
logger = logging.getLogger(__name__)

class GrepBackend(BaseLocalBackend):
    __init__(self, root_paths: list[str] | None = None, exclude_patterns: set[str] | None = None) -> None
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
```


### P:\packages\search-research\core\backends\local\hdma_backend.py

```python
import logging
from pathlib import Path
from typing import Any
from knowledge.analysis.hdma.analyzer import (
        ArchitecturalAntiPattern, ArchitecturalComponent, ComponentRelationship, HDMAAnalyzer, IssueSeverity, )
HDMA_AVAILABLE = True
HDMA_AVAILABLE = False
HDMAAnalyzer = None
ArchitecturalComponent = None
ArchitecturalAntiPattern = None
ComponentRelationship = None
IssueSeverity = None
from ...backend_health import BackendHealthRegistry
logger = logging.getLogger(__name__)

class HDMABackend:
    __init__(self, root_paths: list[str] | None = None, enable_health_tracking: bool = True) -> None
    has_index(self) -> bool
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\backends\local\kg_backend.py

```python
from ...config import config
import json
import logging
from pathlib import Path
from typing import Any
SearchResult = dict[str, Any]
BACKEND_KG = "KG"
logger = logging.getLogger(__name__)

class KGBackend:
    __init__(self, kg_data_path: str | None = None) -> None
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
```


### P:\packages\search-research\core\backends\local\lsp_backend.py

```python
import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final, NotRequired, TypedDict
from collections.abc import Mapping
from code_intelligence.lsp.client import LSPClientManager

class LSPSymbolMetadata(TypedDict):
    file_path = str
    line = int
    symbol_name = str
    symbol_kind = int
    symbol_kind_name = str
    type = str
    search_method = str

class LSPSearchResult(TypedDict):
    id = str
    source = str
    title = str
    content = str
    score = float
    metadata = LSPSymbolMetadata

class LSPSymbolInfo(TypedDict):
    name = str
    kind = int
    file = str
    line = int
    detail = NotRequired[str]

class LSPSymbolKind:
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26
logger = logging.getLogger(__name__)

class LSPSymbolBackend:
    __init__(self, root_paths: list[str] | None = None) -> None
    build_index(self) -> None
    search(self, query: str, limit: int = 50) -> list[LSPSearchResult]
    workspace_symbols(self, query: str = "", limit: int = 50) -> list[dict[str, str | int]]
create_lsp_backend(root_paths: list[str] | None = None) -> LSPSymbolBackend
```


### P:\packages\search-research\core\backends\local\multilang_backend.py

```python
import ast
import logging
from pathlib import Path
from typing import Any
from search_research.backends.base.code_analysis_backend import CodeAnalysisBackend
from search_research.utils.tree_sitter_utils import (
    LanguageRegistry, TreeSitterParser, is_available, )
logger = logging.getLogger(__name__)
BACKEND_MULTILANG = "MULTILANG"
SOURCE_RELIABILITY_MULTILANG = 0.85
LANGUAGE_EXTENSIONS = {
    **LanguageRegistry.LANGUAGE_EXTENSIONS,  # Base extensions from tree_sitter_utils
    ".pyi": "python",  # Type stubs
    ".tsx": "tsx",  # TypeScript JSX
    ".css": "css",  # CSS stylesheets
    # HTML docs excluded - too many, causes memory exhaustion
    # ".html": "html",
    # ".htm": "html",
}

class MultiLangCodeBackend(CodeAnalysisBackend):
    SOURCE_RELIABILITY_MULTILANG = 0.85
    DEFAULT_EXCLUDE_PATTERNS = {
        "_archive",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "node_modules",
        ".git",
        "dist",
        "build",
        "*.egg-info",
    }
    __init__(self, root_paths: list[str] | None = None, use_tree_sitter: bool = True, exclude_patterns: set[str] | None = None)
    build_index(self) -> None
    search(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    asearch(self, query: str, limit: int = 20) -> list[dict[str, Any]]
    get_dependents(self, entity_id: str, limit: int = 0) -> list[str]
    get_dependencies(self, entity_id: str, limit: int = 0) -> list[str]
    get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]
    analyze_impact(self, entity_id: str) -> dict[str, Any]
    impact_analysis(self, entity_id: str) -> dict[str, Any]
    get_entity(self, entity_id: str) -> dict[str, Any] | None
create_multilang_backend(root_paths: list[str] | None = None, use_tree_sitter: bool = True) -> MultiLangCodeBackend
__all__ = [
    "MultiLangCodeBackend",
    "create_multilang_backend",
    "BACKEND_MULTILANG",
    "SOURCE_RELIABILITY_MULTILANG",
    "_TREE_SITTER_AVAILABLE",
]
```


### P:\packages\search-research\core\backends\local\notebooklm_backend.py

```python
import warnings
import asyncio
import json
import logging
import subprocess
from typing import Any
from ..query_intent import QueryIntent
from .base_local_backend import BaseLocalBackend
SearchResult = dict[str, Any]
logger = logging.getLogger(__name__)
BACKEND_NOTEBOOKLM = "notebooklm"
NLM_LIST_TIMEOUT = 10
NLM_QUERY_TIMEOUT = 60

class NotebookLMBackend(BaseLocalBackend):
    name = BACKEND_NOTEBOOKLM
    description = "Long-form research synthesis from NotebookLM notebooks"
    source_types = ["notebook", "research"]
    TIMEOUT = 60
    AUTH_ERROR_PATTERNS = ("Authentication Error", "Authentication expired")
    __init__(self, root_paths: list[str] | None = None, exclude_patterns: set[str] | None = None, notebook_id: str | None = None)
    search_async(self, query: str, limit: int = 5) -> list["SearchResult"]
    search(self, query: str, limit: int = 5) -> list[SearchResult]
    supports_intent(self, intent: QueryIntent) -> bool
create_notebooklm_backend(notebook_id: str | None = None) -> NotebookLMBackend
```


### P:\packages\search-research\core\backends\local\qmd_wiki_backend.py

```python
import asyncio
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING
from ...config import config
from .base_local_backend import BaseLocalBackend
from ...models import SearchResult
logger = logging.getLogger(__name__)
MAX_FILE_READ = 1024 * 1024
VAULT_MTIME_CACHE_TTL = 5.0
REBUILD_FAILURE_LIMIT = 3
REBUILD_COOLDOWN = 60.0
MAX_QUERY_LENGTH = 500
QMD_CONFIG_PATH = Path.home() / ".config" / "qmd" / "index.yml"

class QMDWikiBackend(BaseLocalBackend):
    BACKEND_NAME = "QMD_WIKI"
    TIMEOUT = 0.5
    __init__(self, vault_path: str | None = None, qmd_scope: str | None = None)
    search_batch_async(self, queries: list[str], limit: int = 10) -> list["SearchResult"]
    search_async(self, query: str, limit: int = 10) -> list["SearchResult"]
    build_index(self) -> None
```


### P:\packages\search-research\core\backends\local\rlm_backend.py

```python
import asyncio
import importlib
import json
import logging
import re
from io import StringIO
from pathlib import Path
from typing import Any
BACKEND_RLM = "RLM"
SOURCE_RELIABILITY_RLM = 0.85
logger = logging.getLogger(__name__)

class CodeTemplate:
    PATTERNS = {
        "how": ["how", "does", "do", "work", "implement", "handle"],
        "what": ["what", "definition", "mean", "is", "are", "describe"],
        "where": ["where", "located", "find", "which"],
        "why": ["why", "reason", "purpose", "motivation"],
        "list": ["list", "show", "all", "enumerate"],
        "compare": ["compare", "difference", "vs", "versus", "between"],
        "trace": ["trace", "flow", "call", "execution", "invoke"],
    }
    TEMPLATES = {
        "search": """import re

query_keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    for keyword in query_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            # Find context around the match
            lines = content.split('\\n')
            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = '\\n'.join(lines[context_start:context_end])
                    findings.append(f'{{path}}:{i+1}: {{keyword}} found\\n{{context}}\\n')
                    break  # One match per file per keyword

return_value = {{
    'summary': f'Found {{len(findings)}} matches for keywords: {{", ".join(query_keywords)}}',
    'findings': findings[:20],
    'files_analyzed': list(codebase.keys())
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:10]:
    print(f"- {{f[:100]}}")
""",
        "explain": """import re

keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            # Find class/function definitions related to keyword
            class_matches = re.findall(r'class\\s+(\\w+.*?{keyword}[^\\n]*)', content)
            func_matches = re.findall(r'def\\s+(\\w+.*?{keyword}[^\\n]*)', content)

            if class_matches:
                findings.append(f'Class in {{path}}: {{", ".join(class_matches)}}')
            if func_matches:
                findings.append(f'Function in {{path}}: {{", ".join(func_matches)}}')

return_value = {{
    'summary': f'Analysis of {{", ".join(keywords)}}: {{len(findings)}} definitions found',
    'findings': findings,
    'files_analyzed': list(codebase.keys())
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:10]:
    print(f"- {{f}}")
""",
        "default": """import re

keywords = {keywords}
findings = []

for path, content in codebase.items():
    content_lower = content.lower()
    matched = False
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in content_lower:
            matched = True
            break

    if matched:
        findings.append(path)

return_value = {{
    'summary': f'Search for {{", ".join(keywords)}}: {{len(findings)}} matches',
    'findings': findings,
    'files_analyzed': list(codebase.keys())
}}

print(f"{{return_value['summary']}}")
for f in findings[:20]:
    print(f"- {{f}}")
""",
    }
    @classmethod
    extract_keywords(cls, query: str) -> list[str]
    @classmethod
    detect_query_type(cls, query: str) -> str
    @classmethod
    generate_code(cls, query: str) -> str

class RLMBackend:
    BACKEND_NAME = BACKEND_RLM
    __init__(self, root_paths: list[str] | None = None, enable_by_default: bool = True, max_file_reads: int = 50, execution_timeout: float = 30.0) -> None
    @property
    available(self) -> bool
    @property
    provider_name(self) -> str
    search(self, query: str, limit: int = 10) -> list[dict[str, Any]]
    health_check(self)
create_rlm_backend() -> RLMBackend
is_rlm_available() -> bool
```


### P:\packages\search-research\core\backends\local\skills_backend.py

```python
import re
from pathlib import Path
from typing import Any
import yaml
YAML_AVAILABLE = True
YAML_AVAILABLE = False
from ...config import config
SearchResult = dict[str, Any]
BACKEND_SKILLS = "SKILLS"

class SkillsBackend:
    __init__(self, skills_dirs: list[str] | None = None, commands_dirs: list[str] | None = None, enable_cache: bool = True, use_defaults: bool = True) -> None
    build_index(self) -> None
    has_index(self) -> bool
    search(self, query: str, limit: int = 20) -> list[SearchResult]
    get_all_skills(self) -> list[SearchResult]
    get_all_commands(self) -> list[SearchResult]
    get_by_name(self, name: str) -> SearchResult | None
```


### P:\packages\search-research\core\backends\local\yt_is_backend.py

```python
import asyncio
import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import TYPE_CHECKING
from ...models import SearchResult
logger = logging.getLogger(__name__)
REBUILD_FAILURE_LIMIT = 3
REBUILD_COOLDOWN = 60.0
MAX_QUERY_LENGTH = 500
MAX_SNIPPET = 300

class YtIsBackend:
    BACKEND_NAME = "yt-is"
    TIMEOUT = 5.0
    BATCH_SIZE = 100
    __init__(self) -> None
    search_async(self, query: str, limit: int = 10) -> list[SearchResult]
    build_index(self) -> None
```


### P:\packages\search-research\core\backends\notebooklm\__init__.py

```python

```


### P:\packages\search-research\core\backends\persona.py

```python
from pathlib import Path
from typing import Any
BACKEND_PERSONA = "PERSONA"

class PersonaMemoryBackend:
    __init__(self, db_path: str | Path | None = None)
    @property
    available(self) -> bool
    search(self, query: str, limit: int = 10, persona: str | None = None) -> list[dict[str, Any]]
    query_by_persona(self, persona: str, limit: int = 20) -> list[dict[str, Any]]
    query_by_min_impact(self, min_impact: int, limit: int = 20) -> list[dict[str, Any]]
    get_stats(self) -> dict[str, Any] | None
    close(self) -> None
    __enter__(self)
    __exit__(self) -> None
__all__ = ["BACKEND_PERSONA", "PersonaMemoryBackend"]
```


### P:\packages\search-research\core\backends\query_intent.py

```python
from core.query_intent import QueryIntent
__all__ = ["QueryIntent"]
```


### P:\packages\search-research\core\backends\rlm.py

```python
import json
import re
import sys
from io import StringIO
from typing import Any
from jinja2 import Environment, StrictUndefined
BACKEND_NAME = "RLM_INTERNET"

class SecurityError(Exception):
    pass

class RLMBackend:
    BACKEND_NAME = BACKEND_NAME
    QUERY_PATTERNS = {
        "news": ["news", "latest", "recent", "breaking", "today", "update", "headline"],
        "academic": ["research", "paper", "study", "academic", "journal", "publication", "thesis"],
        "technical": ["implement", "code", "tutorial", "api", "function", "class", "programming"],
    }
    CODE_TEMPLATES = {
        "news": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    title = item.get("title", "")
    content = item.get("content", "")
    findings.append({{"source": item.get("source", "unknown"), "title": title, "url": item.get("url", "")}})

return_value = {{
    "summary": f"Found {{len(findings)}} news articles about {{query}}",
    "findings": findings,
    "query_type": "news"
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:5]:
    print(f" - {{f['title'][:80]}}")
""",
        "academic": """import json

results = {search_results}
query = "{query}"

papers = []
for item in results:
    title = item.get("title", "")
    if any(kw in title.lower() for kw in ["research", "paper", "study"]):
        papers.append({{"title": title, "url": item.get("url", ""), "snippet": item.get("content", "")[:200]}})

return_value = {{
    "summary": f"Found {{len(papers)}} academic papers related to {{query}}",
    "papers": papers,
    "query_type": "academic"
}}

print(f"Summary: {{return_value['summary']}}")
""",
        "technical": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    content = item.get("content", "").lower()
    title = item.get("title", "")
    findings.append({{"title": title, "url": item.get("url", ""), "has_code": "implement" in content or "code" in content}})

return_value = {{
    "summary": f"Found {{len(findings)}} technical resources for {{query}}",
    "findings": findings,
    "query_type": "technical"
}}

print(f"Summary: {{return_value['summary']}}")
""",
        "general": """import json

results = {search_results}
query = "{query}"

findings = []
for item in results:
    findings.append({{"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("content", "")[:150]}})

return_value = {{
    "summary": f"Found {{len(findings)}} results for {{query}}",
    "findings": findings,
    "query_type": "general"
}}

print(f"Summary: {{return_value['summary']}}")
for f in findings[:5]:
    print(f" - {{f['title'][:80]}}")
""",
    }
    STOP_WORDS = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "to",
        "for",
        "of",
        "with",
        "in",
        "on",
        "at",
        "from",
        "by",
        "about",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "and",
        "but",
        "if",
        "or",
        "because",
        "until",
        "while",
        "although",
        "though",
        "explain",
        "describe",
        "show",
        "tell",
        "give",
        "me",
        "find",
        "list",
        "search",
        "look",
        "get",
        "what",
        "which",
    }
    __init__(self, provider_configs: dict[str, Any] | None = None, enable_hyde: bool = True, max_results: int = 10, default_provider: str | None = None, exa_integration: Any = None, tavily_client: Any = None, serper_client: Any = None, github_client: Any = None, brave_client: Any = None, glm_client: Any = None, hyde_engine: Any = None, hyde_enabled: bool = True, timeout_seconds: float = 30.0, enable_reliability_scoring: bool = True)
    @property
    available(self) -> bool
    extract_search_query(self, query: str) -> str
    extract_keywords(self, query: str) -> list[str]
    detect_query_type(self, query: str) -> str
    generate_analysis_code(self, query: str, search_results: list[dict] | None = None, query_type: str | None = None, results: list[dict] | None = None) -> str
    execute_in_sandbox(self, code: str, context: dict[str, Any] | None = None, timeout: int = 5) -> dict[str, Any]
    search(self, query: str, limit: int = 10, providers: list[str] | None = None) -> list[dict[str, Any]]
    research(self, query: str, max_results: int = 10) -> dict[str, Any]
    research_with_analysis(self, query: str, max_results: int = 10, enable_code_analysis: bool = True) -> dict[str, Any]
__all__ = ["RLMBackend", "BACKEND_NAME", "SecurityError"]
```


### P:\packages\search-research\core\backends\web\__init__.py

```python

```


### P:\packages\search-research\core\cache.py

```python
import hashlib
import json
import math
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .terminal_id import canonical_terminal_id

@dataclass
class CachedQuery:
    query = str
    embedding = list[float]
    result = dict[str, Any]
    cached_from = str
    timestamp = float
    to_jsonl(self) -> str
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "CachedQuery"

class EmbeddingCache:
    __init__(self, log_dir: str = "logs", ttl_seconds: int = 3600, initial_threshold: float = 0.95)
    @property
    threshold(self) -> float
    find_similar(self, embedding: list[float]) -> "CachedQuery | None"
    store(self, query: str, embedding: list[float], result: dict[str, Any]) -> None

class QueryCache:
    __init__(self, max_size: int = 1000, ttl_seconds: int = 3600)
    get(self, query: str) -> list[dict[str, Any]] | None
    set(self, query: str, results: list[dict[str, Any]]) -> None
    invalidate(self) -> None
    clear(self) -> None
    get_stats(self) -> dict[str, Any]
```


### P:\packages\search-research\core\chat_search_security.py

```python
import hashlib
import json
import logging
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from .chat_search_config import get_config
CONFIG_AVAILABLE = True
CONFIG_AVAILABLE = False

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    SUSPICIOUS_QUERY = "suspicious_query"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INJECTION_ATTEMPT = "injection_attempt"
    SEARCH_EXECUTED = "search_executed"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

@dataclass
class SecurityEvent:
    event_type = SecurityEventType
    severity = SecurityLevel
    timestamp = datetime
    __post_init__(self)

class InputValidator:
    __init__(self, logger: logging.Logger | None = None)
    validate_query(self, query: str, source_ip: str | None = None) -> tuple[bool, list[str]]
    validate_max_results(self, max_results: int) -> tuple[bool, str]
    sanitize_query(self, query: str) -> str

class RateLimiter:
    __init__(self, max_requests_per_minute: int | None = None, max_requests_per_hour: int | None = None, logger: logging.Logger | None = None)
    is_allowed(self, identifier: str) -> tuple[bool, str | None]
    get_stats(self) -> dict[str, Any]

class ResourceMonitor:
    __init__(self, max_memory_mb: int | None = None, max_concurrent_searches: int | None = None, logger: logging.Logger | None = None)
    can_start_search(self) -> tuple[bool, str | None]
    start_search(self, estimated_memory_mb: int | None = None) -> bool
    end_search(self, estimated_memory_mb: int | None = None)
    get_status(self) -> dict[str, Any]

class SecurityMonitor:
    __init__(self, logger: logging.Logger | None = None)
    log_event(self, event: SecurityEvent)
    get_security_summary(self) -> dict[str, Any]

class ChatSearchSecurityManager:
    __init__(self, config_overrides: dict[str, Any] | None = None)
    validate_and_authorize_search(self, query: str, max_results: int, source_ip: str | None = None, user_id: str | None = None) -> tuple[bool, str | None]
    start_search(self, estimated_memory_mb: int | None = None) -> bool
    end_search(self, estimated_memory_mb: int | None = None)
    get_security_status(self) -> dict[str, Any]
    get_sanitized_query(self, query: str) -> str
```


### P:\packages\search-research\core\chs\__init__.py

```python
__version__ = "2.0.0-dev"
from .clustering import cluster_results, filter_results_by_cluster
from .critical import CHSIndexer, CHSMigrator, CHSSearcher, CHSValidator
from .intelligent_defaults import (
    IntelligentDefaults, get_feature_config, should_cluster, should_enable_session, should_explain, )
from .normalized import (
    get_events_by_hash, query_opportunities, query_tasks, upsert_event, )
from .projections import (
    health_check, query_events, query_events_by_session, )
from .task_projection import open_tasks, resolve_task
from .search import (
    CHSSearchV2, CHSSearchWithSession, SearchSession, SearchSessionManager, get_session_manager, search_turns, )
from .verify_backup import (
    BackupMetadata, compute_directory_sha256, compute_sha256, create_backup_metadata, get_exact_message_count, set_restrictive_permissions, verify_database_backup, verify_database_integrity, verify_faiss_backup, )
__all__ = [
    "BackupMetadata",
    "CHSIndexer",
    "CHSValidator",
    "CHSSearcher",
    "CHSMigrator",
    "CHSSearchV2",
    "CHSSearchWithSession",
    "SearchSession",
    "SearchSessionManager",
    "cluster_results",
    "compute_directory_sha256",
    "compute_sha256",
    "create_backup_metadata",
    "filter_results_by_cluster",
    "get_events_by_hash",
    "get_exact_message_count",
    "get_feature_config",
    "get_session_manager",
    "health_check",
    "IntelligentDefaults",
    "query_events",
    "query_events_by_session",
    "query_opportunities",
    "query_tasks",
    "open_tasks",
    "resolve_task",
    "search_turns",
    "set_restrictive_permissions",
    "should_cluster",
    "should_enable_session",
    "should_explain",
    "upsert_event",
    "verify_database_backup",
    "verify_database_integrity",
    "verify_faiss_backup",
]
```


### P:\packages\search-research\core\chs\archive.py

```python
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from filelock import FileLock
append_raw_event(provider_id: str, source_id: str, event: dict[str, Any]) -> str
write_watermark(provider_id: str, source_id: str, terminal_id: str, watermark: dict[str, Any]) -> None
read_watermark(provider_id: str, source_id: str, terminal_id: str) -> dict[str, Any] | None
```


### P:\packages\search-research\core\chs\clustering.py

```python
import logging
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING
import numpy as np
import sqlite3
logger = logging.getLogger(__name__)
MIN_RESULTS_FOR_CLUSTERING = 10
DEFAULT_EMBEDDING_DIM = 384
TOPIC_SIMILARITY_THRESHOLD = 0.75
MIN_CLUSTER_SIZE = 2
cluster_results(results: list[dict], mode: str = "topic", n_clusters: int | None = None) -> dict
filter_results_by_cluster(results: list[dict], clustering_output: dict, cluster_id: str) -> list[dict]
interactive_cluster_selection(clustering_output: dict) -> str | None

class ClusteredSearchResults:
    __init__(self, results: list[dict], clustering: dict | None = None)
    get_clusters(self) -> list[dict]
    filter_by_cluster(self, cluster_id: str) -> list[dict]
    get_cluster_summary(self) -> str
extract_embeddings_from_results(results: list[dict], db: sqlite3.Connection | None = None) -> list[np.ndarray | None]
```


### P:\packages\search-research\core\chs\config.py

```python
import os
from pathlib import Path

class Config:
    DEFAULT_DB_PATH = Path("P:/__csf/data/chat_history.db")
    DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
    DEFAULT_EMBEDDING_DIMENSIONS = 768
    DEFAULT_JSONL_DIR = Path("P:/__csf/logs/chats")
    __init__(self) -> None
get_chs_db_path() -> str
```


### P:\packages\search-research\core\chs\critical.py

```python
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

class SearchResultContainer(list):
    __init__(self, results: list, metadata: dict)
    get(self, key: str, default = None)

class CHSIndexer:
    __init__(self, jsonl_path: str | Path, db_path: str | Path, checkpoint_path: str | Path)
    index(self) -> dict

class CHSValidator:
    __init__(self, db_path: str | Path)
    validate_embedding_blob(self, embedding_blob: bytes, expected_dim: int) -> None

class CHSSearcher:
    __init__(self, db_path: str | Path, model_dim: int)
    search(self, query: str, limit: int = 10) -> SearchResultContainer

class CHSMigrator:
    __init__(self, db_path: str | Path)
    check_migration_required(self, current_model_dim: int) -> dict
```


### P:\packages\search-research\core\chs\db.py

```python
import sqlite3
from pathlib import Path
get_connection(db_path: Path | str) -> sqlite3.Connection
database_is_initialized(db_path: Path | str) -> bool
init_db(db_path: Path | str) -> None
load_embeddings_config(db_path: Path | str) -> dict | None
set_embeddings_config(db_path: Path | str, model_name: str, embedding_dim: int) -> None
```


### P:\packages\search-research\core\chs\embeddings.py

```python
import logging
import time
from typing import TYPE_CHECKING
import numpy as np
logger = logging.getLogger(__name__)
DEFAULT_EMBEDDING_DIM = 384
MAX_RETRIES = 3
INITIAL_DELAY = 0.5

class EmbedClient:
    __init__(self, daemon_client)
    embed_texts(self, texts: list[str]) -> list[bytes]
validate_embedding_blob(blob: bytes, expected_dim: int) -> None
validate_embedding_array(array: np.ndarray, expected_dim: int) -> None
bytes_to_vector(blob: bytes, dim: int) -> np.ndarray
cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float
get_embed_client() -> EmbedClient
reset_embed_client() -> None
```


### P:\packages\search-research\core\chs\indexer.py

```python
import asyncio
import logging
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.chs.db import get_connection
from core.chs.utils import file_identity, parse_jsonl_line
logger = logging.getLogger(__name__)

class ChatIndexer:
    __init__(self, db_path: str | Path = ":memory:", conn: sqlite3.Connection | None = None)
    daemon_loop(self, jsonl_dir: str | Path, poll_interval: float = 1.0, idle_timeout: int = 3600) -> None
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
```


### P:\packages\search-research\core\chs\intelligent_defaults.py

```python
import os
import re
from typing import Any
should_explain(query: str, execution_time_ms: float = 0, backend_count: int = 1, result_count: int | None = None) -> bool
should_enable_session() -> bool
should_cluster(results: list[dict[str, Any]], min_results: int = 10, min_source_diversity: int = 2) -> bool
get_feature_config(query: str = "", execution_time_ms: float = 0, backend_count: int = 1, result_count: int | None = None, results: list[dict[str, Any]] | None = None) -> dict[str, Any]

class IntelligentDefaults:
    __init__(self, explain_threshold_ms: float = 2000, explain_query_length: int = 100, cluster_min_results: int = 10, cluster_min_sources: int = 2) -> None
    should_explain(self, query: str, execution_time_ms: float = 0, backend_count: int = 1, result_count: int | None = None) -> bool
    should_use_session(self) -> bool
    should_cluster(self, results: list[dict[str, Any]]) -> bool
    get_config(self, query: str = "", execution_time_ms: float = 0, backend_count: int = 1, result_count: int = 0, results: list[dict[str, Any]] | None = None) -> dict[str, Any]
```


### P:\packages\search-research\core\chs\normalized.py

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from core.chs.db import get_connection
DB_PATH = Path("P:/__csf/data/chat_history.db")
upsert_event(event: dict[str, Any]) -> bool
query_tasks(provider_id: str | None = None, since: str | None = None, until: str | None = None) -> list[dict]
query_opportunities(provider_id: str | None = None, since: str | None = None, until: str | None = None) -> list[dict]
get_events_by_hash(provider_id: str, source_id: str, content_hash: str) -> list[dict]
```


### P:\packages\search-research\core\chs\projections.py

```python
from pathlib import Path
from typing import Any
from core.chs.db import get_connection
from core.chs.providers import discover_all
DB_PATH = Path("P:/__csf/data/chat_history.db")
health_check() -> dict[str, bool]
query_events(provider_id: str | None = None, source_id: str | None = None, since: str | None = None, until: str | None = None, limit: int = 100) -> list[dict[str, Any]]
query_events_by_session(provider_id: str, source_id: str, limit: int = 1000) -> list[dict[str, Any]]
```


### P:\packages\search-research\core\chs\providers\__init__.py

```python
from core.chs.providers.base import Provider
register(provider_id: str, provider_class: type[Provider]) -> None
discover(provider_id: str) -> Provider
discover_all() -> list[Provider]
ingest_since(provider_id: str, watermark: dict | None = None) -> list[dict]
from core.chs.providers.claude_code_raw import ClaudeCodeRawProvider
from core.chs.providers.codex_desktop import CodexDesktopProvider
from core.chs.providers.claude_log import ClaudeLogProvider
```


### P:\packages\search-research\core\chs\providers\base.py

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

@dataclass(frozen=True)
class ProviderCapabilities:
    supports_incremental = bool
    supports_backfill = bool
    has_task_events = bool
    has_tool_events = bool

@dataclass(frozen=True)
class NormalizedEvent:
    provider_id = str
    source_id = str
    event_id = str
    conversation_id = str | None
    session_id = str | None
    terminal_id = str | None
    turn_id = str | None
    occurred_at = str
    content_hash = str
    raw_payload_path = str
    metadata_json = str

@runtime_checkable
class Provider(Protocol):
    @property
    provider_id(self) -> str
    @property
    capabilities(self) -> ProviderCapabilities
    discover(self) -> list[dict]
    ingest_since(self, watermark: dict | None) -> list[dict]
    fetch_session(self, source_id: str) -> dict
    fetch_message(self, source_id: str, message_id: str) -> dict
```


### P:\packages\search-research\core\chs\providers\claude_code_raw.py

```python
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from filelock import FileLock
from core.chs.archive import append_raw_event
from core.chs.providers.base import ProviderCapabilities
HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"

class ClaudeCodeRawProvider:
    discover(self) -> list[dict]
    ingest_since(self, watermark: dict | None = None, terminal_id: str | None = None) -> list[dict]
    fetch_session(self, source_id: str) -> dict
    fetch_message(self, source_id: str, message_id: str) -> dict
```


### P:\packages\search-research\core\chs\providers\claude_log.py

```python
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from filelock import FileLock
from core.chs.archive import append_raw_event
from core.chs.providers.base import ProviderCapabilities
HISTORY_JSONL = Path.home() / "claude-log.jsonl"

class ClaudeLogProvider:
    discover(self) -> list[dict]
    ingest_since(self, watermark: dict | None = None, terminal_id: str | None = None) -> list[dict]
    fetch_session(self, source_id: str) -> dict
    fetch_message(self, source_id: str, message_id: str) -> dict
```


### P:\packages\search-research\core\chs\providers\codex_desktop.py

```python
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from filelock import FileLock
from core.chs.archive import append_raw_event
from core.chs.providers.base import ProviderCapabilities
HISTORY_JSONL = Path.home() / ".codex" / "history.jsonl"

class CodexDesktopProvider:
    discover(self) -> list[dict]
    ingest_since(self, watermark: dict | None = None, terminal_id: str | None = None) -> list[dict]
    fetch_session(self, source_id: str) -> dict
    fetch_message(self, source_id: str, message_id: str) -> dict
```


### P:\packages\search-research\core\chs\schema_compat.py

```python
import sqlite3
from typing import TYPE_CHECKING

class SchemaVersion:
    LEGACY = "legacy"
    V2 = "v2"

class CHSSchemaCompat:
    LEGACY_MESSAGES = "chat_messages"
    LEGACY_SESSIONS = "chat_sessions"
    LEGACY_FTS = "message_search"
    V2_MESSAGES = "messages"
    V2_SESSIONS = "sessions"
    V2_TURNS = "turns"
    V2_MESSAGES_FTS = "messages_fts"
    V2_TURNS_FTS = "turns_fts"
    @staticmethod
    detect_schema_version(db: sqlite3.Connection | str) -> str
    @staticmethod
    get_messages_table(db: sqlite3.Connection) -> str
    @staticmethod
    get_sessions_table(db: sqlite3.Connection) -> str
    @staticmethod
    get_fts_table(db: sqlite3.Connection) -> str
    @staticmethod
    validate_required_tables(db: sqlite3.Connection) -> dict[str, bool]
    @staticmethod
    get_schema_health_message(db: sqlite3.Connection | str) -> str | None
```


### P:\packages\search-research\core\chs\scripts\__init__.py

```python

```


### P:\packages\search-research\core\chs\scripts\backfill_embeddings.py

```python
import argparse
import sys
from pathlib import Path
from core.chs.config import get_chs_db_path
from core.chs.db import get_connection
from core.chs.embeddings import get_embed_client
backfill(db_path: str, dry_run: bool = False) -> int
main() -> None
```


### P:\packages\search-research\core\chs\scripts\chs_cli.py

```python
import argparse
import json
import sys
format_result_human(result: dict) -> str
main() -> int
```


### P:\packages\search-research\core\chs\scripts\health_check.py

```python
import argparse
import sys
from datetime import datetime
from pathlib import Path
format_timestamp(ts: int | None) -> str
main() -> int
```


### P:\packages\search-research\core\chs\scripts\init_db.py

```python
import argparse
import sys
from pathlib import Path
main() -> int
```


### P:\packages\search-research\core\chs\scripts\merge_history_jsonl.py

```python
import argparse
import json
import logging
import sys
from pathlib import Path
logger = logging.getLogger(__name__)
parse_args() -> argparse.Namespace
main() -> int
```


### P:\packages\search-research\core\chs\scripts\refactor_imports.py

```python
import ast
from pathlib import Path

class CHSImportRefactor(ast.NodeTransformer):
    OLD_PREFIX = "knowledge.systems.chs.v2"
    NEW_PREFIX = "search_research.core.chs"
    visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None
    visit_Import(self, node: ast.Import) -> ast.Import
refactor_file(file_path: Path) -> bool
refactor_directory(root_dir: Path) -> list[Path]
main() -> int
```


### P:\packages\search-research\core\chs\scripts\reindex_from_jsonl.py

```python
import argparse
import json
import logging
import sys
import time
from pathlib import Path
logger = logging.getLogger(__name__)
HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"
DEFAULT_DB_PATH = Path("P:/__csf/data/chat_history.db")
CLAUDE_CODE_PROJECT_LABEL = "Claude Code"
CLAUDE_CODE_PROJECT_PATH = "~/.claude"
BATCH_SIZE = 1000
extract_text_content(message) -> str
parse_claude_timestamp(ts) -> int

class HistoryReindexer:
    __init__(self, db_path: Path | str)
    init_schema(self) -> None
    get_or_create_project(self) -> int
    get_or_create_session(self, project_id: int, session_key: str, started_at: int) -> int
    ingest_message(self, project_id: int, session_id: int, message_id: str, timestamp: int, role: str, content: str) -> bool
    build_turns_for_session(self, session_id: int, project_id: int) -> int
    reindex(self, history_path: Path, dry_run: bool = False, limit: int | None = None, commit_every: int = BATCH_SIZE) -> dict
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
main() -> int
```


### P:\packages\search-research\core\chs\scripts\run_indexer.py

```python
import argparse
import os
import sys
import time
from pathlib import Path
acquire_lock(lock_path: Path) -> bool
main() -> int
```


### P:\packages\search-research\core\chs\search.py

```python
import logging
import re
import time
from typing import TYPE_CHECKING, Any
import numpy as np
from .clustering import ClusteredSearchResults, cluster_results, filter_results_by_cluster
from .embeddings import bytes_to_vector, cosine_similarity
from .schema_compat import CHSSchemaCompat
from .search_session import SearchSession, SearchSessionManager
from .utils import adaptive_lambda, escape_fts5_query
import sqlite3
search_semantic_sessions(db: sqlite3.Connection, query: str, embed_client, limit: int = 10, threshold: float = 0.65) -> list[dict]
logger = logging.getLogger(__name__)
get_session_manager() -> SearchSessionManager
search_fts_messages(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]
search_fts_turns(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]
semantic_search_turns(db: sqlite3.Connection, query_embedding: np.ndarray, limit: int = 10) -> list[dict]
fuse_scores(fts_results: list[dict], semantic_results: list[dict], lambda_param: float | str = 0.5) -> list[dict]
search_turns(db: sqlite3.Connection, query: str, limit: int = 10, query_embedding: np.ndarray | None = None) -> list[dict]

class CHSSearchV2:
    __init__(self, db: sqlite3.Connection | str) -> None
    search(self, query: str, limit: int = 10, use_semantic: bool = False) -> list[dict]
    search_with_clustering(self, query: str, limit: int = 10, cluster_mode: str = "topic", cluster_filter: str | None = None) -> ClusteredSearchResults

class CHSSearchWithSession:
    __init__(self, db: sqlite3.Connection | str, session_id: str | None = None, max_history: int = 5, max_results: int = 10) -> None
    @property
    session(self) -> SearchSession
    search(self, query: str, limit: int = 10, use_semantic: bool = False, session_mode: bool = True) -> list[dict]
    follow_up(self, reference_id: int | None = None, query_id: str | None = None) -> dict[str, Any]
    follow_up_query(self, query: str, reference_id: int | None = None) -> tuple[list[dict], dict[str, Any] | None]
    get_session_summary(self) -> dict[str, Any]
    export_session(self, cks_db_path: str | None = None) -> dict[str, Any]
    cleanup_session(self) -> None
explain_execution_plan(query: str, options: dict | None = None) -> dict
```


### P:\packages\search-research\core\chs\search_fts_compat.py

```python
from typing import TYPE_CHECKING
from search_research.core.chs.schema_compat import CHSSchemaCompat
from search_research.core.chs.utils import escape_fts5_query
import sqlite3
search_fts_messages(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]
```


### P:\packages\search-research\core\chs\search_session.py

```python
import json
import os
import re
import sqlite3
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

class SearchSession:
    __init__(self, max_history: int = 5, max_results: int = 10, session_id: str | None = None) -> None
    add_search(self, query: str, results: list[dict[str, Any]]) -> str
    follow_up(self, query_id: str | None = None, reference_id: int | None = None) -> dict[str, Any]
    get_context_summary(self) -> dict[str, Any]
    export_to_cks(self, cks_db_path: str | None = None) -> dict[str, Any]
    cleanup(self) -> None
    parse_followup_query(self, query: str) -> dict[str, Any]
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> SearchSession

class SearchSessionManager:
    __init__(self, storage_dir: str | None = None) -> None
    @property
    active_session(self) -> SearchSession | None
    create_session(self, max_history: int = 5, max_results: int = 10, session_id: str | None = None) -> SearchSession
    get_or_create_session(self, session_id: str | None = None) -> SearchSession
    save_session(self, session: SearchSession) -> bool
    load_session(self, session_id: str) -> SearchSession | None
    list_sessions(self) -> list[dict[str, Any]]
    delete_session(self, session_id: str) -> bool
    cleanup_old_sessions(self, max_age_hours: int = 24) -> int
```


### P:\packages\search-research\core\chs\summarizer.py

```python
import logging
logger = logging.getLogger(__name__)
SUMMARIZER_PROMPT = """Given this Claude Code conversation, write a 1-sentence summary (max 80 chars) covering the main topic or goal. Focus on what was decided, built, or debugged.

Recent messages:
{preview}

Summary (1 sentence, max 80 chars):"""
generate_session_summary(messages: list[dict], max_preview_chars: int = 600) -> str
```


### P:\packages\search-research\core\chs\task_projection.py

```python
from core.chs.db import get_connection
from pathlib import Path
DB_PATH = Path("P:/__csf/data/chat_history.db")
open_tasks(provider_id: str | None = None) -> list[dict]
resolve_task(task_id: str, resolved_at: str | None = None) -> bool
```


### P:\packages\search-research\core\chs\topics.py

```python
import re
import sqlite3
TOPIC_PATTERNS = {
    "python": {"pattern": "\\bpython\\b", "description": "Python programming language"},
    "async": {"pattern": "\\basync\\b", "description": "Asynchronous programming"},
    "django": {"pattern": "\\bdjango\\b", "description": "Django web framework"},
    "fastapi": {"pattern": "\\bfastapi\\b", "description": "FastAPI web framework"},
    "react": {"pattern": "\\breact\\b", "description": "React JavaScript library"},
    "typescript": {"pattern": "\\btypescript\\b", "description": "TypeScript programming language"},
    "pytest": {"pattern": "\\bpytest\\b", "description": "Python testing framework"},
    "sql": {"pattern": "\\bsql\\b", "description": "SQL database queries"},
    "javascript": {"pattern": "\\bjavascript\\b", "description": "JavaScript programming language"},
    "java": {"pattern": "\\bjava\\b", "description": "Java programming language"},
    "golang": {"pattern": "\\bgolang\\b", "description": "Go programming language"},
    "rust": {"pattern": "\\brust\\b", "description": "Rust programming language"},
    "csharp": {"pattern": "\\bcsharp\\b", "description": "C# programming language"},
    "ruby": {"pattern": "\\bruby\\b", "description": "Ruby programming language"},
    "php": {"pattern": "\\bphp\\b", "description": "PHP programming language"},
    "swift": {"pattern": "\\bswift\\b", "description": "Swift programming language"},
    "kotlin": {"pattern": "\\bkotlin\\b", "description": "Kotlin programming language"},
}
extract_topics(text: str, max_topics: int = 10) -> dict[str, float]
update_session_topics(conn: sqlite3.Connection, session_id: int, topics: dict[str, float]) -> None
```


### P:\packages\search-research\core\chs\utils.py

```python
import hashlib
import json
import re
from pathlib import Path
file_identity(file_path: Path | str) -> str
parse_jsonl_line(line: str) -> dict | None
discover_chat_logs(directory: Path | str) -> list[Path]
adaptive_lambda(query: str) -> float
escape_fts5_query(query: str) -> str
```


### P:\packages\search-research\core\chs\verify_backup.py

```python
import hashlib
import json
import logging
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING
logger = logging.getLogger(__name__)

@dataclass
class BackupMetadata:
    source_db = str
    backup_db = str
    message_count = int
    db_checksum = str
    faiss_path = str | None
    faiss_checksum = str | None
    faiss_vector_count = int | None
    faiss_dimension = int | None
    to_json(self, file_path: str | Path) -> None
    @classmethod
    from_json(cls, file_path: str | Path) -> BackupMetadata
compute_sha256(file_path: str | Path) -> str
compute_directory_sha256(directory: str | Path) -> str
get_exact_message_count(db_path: str | Path) -> int
verify_database_integrity(db_path: str | Path) -> tuple[bool, str]
verify_database_backup(backup_db_path: str | Path, expected_count: int | None = None, expected_checksum: str | None = None) -> tuple[bool, dict]
verify_faiss_backup(backup_faiss_path: str | Path, expected_vector_count: int | None = None, expected_dimension: int | None = 768, expected_checksum: str | None = None) -> tuple[bool, dict]
create_backup_metadata(source_db: str | Path, backup_db: str | Path, faiss_source: str | Path | None = None, faiss_backup: str | Path | None = None) -> BackupMetadata
set_restrictive_permissions(file_path: str | Path) -> tuple[bool, str]
verify_database_backup = verify_database_backup
verify_faiss_backup = verify_faiss_backup
create_backup_metadata = create_backup_metadata
main() -> int
import logging
import os
```


### P:\packages\search-research\core\chunking\__init__.py

```python
from .smart_chunker import SmartChunker, BreakPointScore
__all__ = ["SmartChunker", "BreakPointScore"]
```


### P:\packages\search-research\core\chunking\smart_chunker.py

```python
import re
from enum import IntEnum
from typing import List, Tuple

class BreakPointScore(IntEnum):
    H1 = 100
    H2 = 90
    H3 = 80
    CODE_FENCE = 80
    HORIZONTAL_RULE = 60
    BLANK_LINE = 20
    LIST_ITEM = 5
    LINE_BREAK = 1

class SmartChunker:
    __init__(self, overlap: bool = True)
    chunk(self, text: str) -> List[str]
__all__ = ["SmartChunker", "BreakPointScore"]
```


### P:\packages\search-research\core\cks\__init__.py

```python

```


### P:\packages\search-research\core\cks\analyze_fts_performance.py

```python
import random
import sqlite3
import statistics
import time
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
get_database_stats(db_path: Path) -> dict
benchmark_fts_search(db_path: Path, queries: list[str], iterations: int = 10) -> dict
create_test_databases(source_db: Path, output_dir: Path, scales: list[float] = [0.2, 0.4, 0.6, 0.8, 1.0]) -> list[Path]
analyze_fts5_complexity()
main() -> None
```


### P:\packages\search-research\core\cks\cks_add_cli.py

```python
import logging
import re
import sys
from pathlib import Path
from typing import Literal
from cks.unified import CKS
from src.cli.ingest_cli import main as ingest_cli
logger = logging.getLogger(__name__)
ContentType = Literal["pattern", "memory", "code", "document"]
CODE_EXTENSIONS = (".py", ".js", ".ts")
DOCUMENT_EXTENSIONS = (".md", ".txt", ".rst")
PATTERN_KEYWORDS = ("Results:", "Anti-pattern:")
PATTERN_INDICATORS = ("%", "reduction")
MEMORY_QUESTION_STARTERS = (
    "What",
    "How",
    "Why",
    "When",
    "Where",
    "Who",
    "Which",
    "Can",
    "Does",
    "Is",
)
CODE_KEYWORDS = ("def ", "class ", "function ", "interface ")
ERROR_PATTERNS = (
    r"Traceback \(most recent call last\):",
    r"Exception\s+occurred",
    r"Exception:",
    r"\bException\b",
    r"Error:",
    r"\bError\b",
    r"\bFile\s+\"[^\"]+\",\s+line\s+\d+",
    r"\b[A-Z]\w+Error:",
    r"raise\s+\w+",
    r"except\s+\w+",
)
DECISION_MARKERS = (
    "DECISION:",
    "DECIDED:",
    "RESOLVED:",
    "APPROVED:",
    "RATIONALE:",
    "ALTERNATIVES CONSIDERED:",
    "CONTEXT:",
    "OUTCOME:",
)
METRIC_PATTERNS = (
    r"\d+th\s+percentile",
    r"\d+%(?:\s+reduction|\s+improvement|\s+increase)?",
    r"\d+\s*(?:ms|seconds?|minutes?)",
    r"(?:latency|throughput|memory|cpu|disk):\s*\d+",
    r"\d+\s*requests?/?\s*second",
)
CODE_BLOCK_PATTERNS = (
    r"```(?:python|js|typescript|java|go|rust|bash|shell)",
    r"def\s+\w+\s*\(",
    r"class\s+\w+",
    r"interface\s+\w+",
    r"function\s+\w+",
)
DEFAULT_SOURCE_TYPE = "paste"
DEFAULT_DOCUMENT_TITLE = "Document"
COMPRESSION_THRESHOLD = 500
is_high_value(text: str) -> bool
compress_content(text: str) -> str
classify_content(text: str, source_type: str = DEFAULT_SOURCE_TYPE) -> ContentType
cks_add(text: str, source_type: str = DEFAULT_SOURCE_TYPE, force_mode: ContentType | None = None) -> str
main()
```


### P:\packages\search-research\core\cks\cks_cli.py

```python
import sys
from pathlib import Path
from typing import Any
from .unified import CKS as UnifiedCKS
from .session_lesson_extractor import extract_session_lessons
extract_session_lessons = None

class CKSCLI:
    __init__(self) -> None
    connect(self) -> bool
    show_statistics(self) -> dict[str, Any]
    query_tdd_content(self) -> list[dict[str, Any]]
    search(self, query: str, graph_type: str = "knowledge") -> list[dict[str, Any]]
    interactive_mode(self) -> None
    rebuild_index(self, entry_type: str | None = None) -> bool
    backfill_embeddings(self, batch_size: int = 100) -> dict[str, int]
    extract_session(self, session_file: str | None = None) -> dict[str, Any]
    detect_content_type(self, content: str) -> str
    add_content(self, content: str, title: str | None = None, content_type: str | None = None) -> dict[str, Any]
    add_from_file(self, file_path: str) -> dict[str, Any]
    show_help(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\cks_query_interface.py

```python
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any
DB_PATH = Path(__file__).parent.parent.parent / "data/cks.db"

class CKSQueryInterface:
    __init__(self, db_path: Path = DB_PATH) -> None
    connect(self) -> bool
    close(self) -> None
    search_knowledge_graph(self, query: str, limit: int = 10) -> list[dict[str, Any]]
    search_vector_nodes(self, query: str, limit: int = 10) -> list[dict[str, Any]]
    find_cross_graph_relationships(self, entity_id: str, source_graph: str) -> list[dict[str, Any]]
    get_tdd_repositories(self) -> list[dict[str, Any]]
    get_architecture_patterns(self) -> list[dict[str, Any]]
    semantic_search_across_graphs(self, query: str, limit: int = 20) -> dict[str, list[dict[str, Any]]]
    get_entity_insights(self, entity_id: str, graph_type: str) -> dict[str, Any]
    get_system_statistics(self) -> dict[str, Any]
    interactive_query(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\cks_spec.py

```python
import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from .entity_filter import CKSEntityFilter
from .unified import CKS

@dataclass
class CKSSearchSpec:
    query = str
    validate(self) -> tuple[bool, list[str]]

@dataclass
class CKSAddSpec:
    question = str
    answer = str
    validate(self) -> tuple[bool, list[str]]

@dataclass
class CKSListSpec:
    validate(self) -> tuple[bool, list[str]]

@dataclass
class CKSEntitySpec:
    action = str
    validate(self) -> tuple[bool, list[str]]

class CKSCommandExecutor:
    __init__(self, db_path: str | None = None) -> None
    execute_search(self, spec: CKSSearchSpec) -> dict[str, Any]
    execute_add(self, spec: CKSAddSpec) -> dict[str, Any]
    execute_list(self, spec: CKSListSpec) -> dict[str, Any]
    execute_stats(self) -> dict[str, Any]
    execute_entities(self, spec: CKSEntitySpec) -> dict[str, Any]
format_output(result: dict[str, Any], json_output: bool = False) -> str
create_parser() -> argparse.ArgumentParser
main() -> int
```


### P:\packages\search-research\core\cks\cli\__init__.py

```python

```


### P:\packages\search-research\core\cks\cli\dream_journal.py

```python
import json
import sqlite3
import time
from datetime import datetime, timedelta
import click
from ..consolidation.dreaming_cycle import DreamingService
get_db_connection(db_path: str, timeout: int = 10)
@click.group()
dream() -> None
@dream.command()
@click.option("--last", type=int, default=7, help="Last N days")
status(last: int) -> None
@dream.command()
@click.option("--limit", type=int, default=10, help="Show N pending relations")
pending(limit: int) -> None
@dream.command()
@click.option("--id", type=int, required=True, help="Relation ID from pending list")
@click.option("--approve", is_flag=True, help="Approve this relation")
@click.option("--reject", is_flag=True, help="Reject this relation")
@click.option("--notes", type=str, help="Review notes")
review(id: int, approve: bool, reject: bool, notes: str) -> None
@dream.command()
commit() -> None
```


### P:\packages\search-research\core\cks\commands\__init__.py

```python

```


### P:\packages\search-research\core\cks\commands\_make.py

```python

```


### P:\packages\search-research\core\cks\commands\auto_learning_expander.py

```python
import asyncio
import logging
import re
import sys
from pathlib import Path
import fcntl
HAVE_FCNTL = True
HAVE_FCNTL = False
import msvcrt
HAVE_MSVCRT = True
HAVE_MSVCRT = False
logger = logging.getLogger(__name__)

class AutoLearningQueryExpander:
    ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")
    DEFAULT_SIMILARITY_THRESHOLD = 0.3
    DEFAULT_MIN_RESULTS = 2
    __init__(self, dry_run: bool = False, cks_path: Path | None = None) -> None
    @property
    query_expander(self)
    detect_unknown_terms(self, query: str, results: list[dict], similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> list[str]
    extract_definition(self, content: str, term: str) -> str
    add_mapping(self, term: str, expansion: str, source: str = "auto_learned", confidence: float = 0.5) -> dict
    search_and_learn(self, query: str, results: list[dict], cks_client = None) -> dict
    get_learned_mappings(self) -> dict[str, dict]
    list_learned_terms(self) -> list[dict]
    remove_learned_term(self, term: str) -> bool
    suggest_expansion(self, query: str) -> list[str]
auto_learn_from_search(query: str, results: list[dict], cks_client = None, dry_run: bool = False) -> dict
```


### P:\packages\search-research\core\cks\commands\cks_migrate.py

```python
import argparse
import logging
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
src_dir = project_root / "src"
logger = logging.getLogger(__name__)
MODEL_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "bge-base-en-v1.5": 768,
    "bge-large-en-v1.5": 1024,
    "bge-small-en-v1.5": 384,  # Same as MiniLM - drop-in replacement
}
QUERY_EXPANSION_UPDATES = {
    "abbreviations": {
        "hyde": "hypothetical document embeddings",
        "octocode": "github repository search",
        "tavily": "tavily search api",
        "serper": "google search api",
        "glm": "glm chat model zhipu ai",
        "zai": "zai search",
    },
    "synonyms": {
        "search": ["search", "query", "retrieve", "lookup", "semantic search", "vector search"],
        "embed": ["embed", "embedding", "vectorize", "encode"],
        "ingest": ["ingest", "store", "save", "index", "add"],
    },
    "domain_terms": {
        "research": ["research", "documentation", "analysis", "investigation"],
        "github": ["github", "repository", "repo", "code", "open source"],
        "adapter": ["adapter", "wrapper", "client", "interface"],
    },
}

class ProgressTracker:
    __init__(self, total: int) -> None
    update(self, n: int = 1) -> dict
    print_progress(self, prefix: str = "Progress") -> None

class CKSModelMigration:
    __init__(self, target_model: str = "bge-large-en-v1.5", dry_run: bool = False, backup: bool = True, incremental: bool = False, use_gpu: bool = False, backup_dir: str | None = None, verbose: bool = False) -> None
    get_current_model_info(self) -> dict
    backup_database(self) -> Path
    load_new_model(self) -> None
    update_query_expansion(self) -> None
    migrate_embeddings(self, batch_size: int = 32) -> None
    rebuild_rag_index(self) -> None
    verify_migration(self) -> bool
    rollback(self) -> bool
    run(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\commands\design_prompt_cks_integration.py

```python
create_enhanced_cks_schema() -> str
store_prompt_standards_in_cks()
create_cks_prompt_retrieval_system() -> str
design_llm_integration_pattern() -> str
main() -> None
```


### P:\packages\search-research\core\cks\commands\file_history.py

```python
import json
import sqlite3
import sys
query_file_history(file_path: str) -> list[dict]
```


### P:\packages\search-research\core\cks\commands\fix_cks_validation_commands.py

```python
import asyncio
from standards_spec import StandardsKnowledgeSystem
fix_validation_commands() -> None
```


### P:\packages\search-research\core\cks\commands\ingest_coding_standards.py

```python
import argparse
import re
import sys
from pathlib import Path
from typing import Any
from ..unified import CKS

class CodingStandardsParser:
    @staticmethod
    parse_markdown_table(lines: list[str]) -> list[dict[str, str]]
    @staticmethod
    parse_anti_patterns(lines: list[str]) -> list[str]
    @staticmethod
    extract_focus_area(standard: str) -> str
    @staticmethod
    extract_tools(standard: str, do_this: str) -> list[str]

class CodingStandardsIngestion:
    __init__(self) -> None
    ingest_python_standards(self) -> dict[str, Any]
    ingest_typescript_standards(self) -> dict[str, Any]
    show_stats(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\commands\smart_review_cks_fixed.py

```python
import asyncio
import logging
import re
import subprocess
from pathlib import Path
from typing import Any
from standards_spec import StandardEntry, StandardsKnowledgeSystem
from cli.subprocess_helper import run_subprocess
logger = logging.getLogger(__name__)

class CKSStandardsChecker:
    __init__(self) -> None
    initialize(self) -> None
    detect_language(self, file_path: Path) -> str | None
    check_file_compliance(self, file_path: Path) -> list[dict[str, Any]]
    get_compliance_summary(self, violations: list[dict[str, Any]]) -> dict[str, Any]
test_cks_checker() -> None
```


### P:\packages\search-research\core\cks\commands\test_auto_learning_expander.py

```python
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent.parent
test_import() -> bool | None
test_initialization()
test_unknown_term_detection() -> bool
test_definition_extraction() -> bool
test_mapping_persistence() -> bool
test_search_and_learn() -> bool
tests = [
        ("Import", test_import),
        ("Initialization", test_initialization),
        ("Unknown Term Detection", test_unknown_term_detection),
        ("Definition Extraction", test_definition_extraction),
        ("Mapping Persistence", test_mapping_persistence),
        ("Search and Learn", test_search_and_learn),
    ]
failed = []
result = test_func()
```


### P:\packages\search-research\core\cks\commands\test_cks_migrate.py

```python
import sys
import tempfile
from pathlib import Path
src_dir = Path(__file__).parent.parent.parent
test_import() -> bool | None
test_migration_initialization()
test_model_dimensions() -> bool
test_backup_creation() -> bool
test_query_expansion_update() -> bool
tests = [
        ("Import", test_import),
        ("Initialization", test_migration_initialization),
        ("Model Dimensions", test_model_dimensions),
        ("Backup Creation", test_backup_creation),
        ("Query Expansion Update", test_query_expansion_update),
    ]
failed = []
result = test_func()
```


### P:\packages\search-research\core\cks\commands\test_unified_ingest.py

```python
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent.parent
test_import() -> bool | None
test_initialization()
test_extract_title() -> bool
test_ingest_pattern() -> bool
test_search() -> bool
tests = [
        ("Import", test_import),
        ("Initialization", test_initialization),
        ("Extract Title", test_extract_title),
        ("Ingest Pattern", test_ingest_pattern),
        ("Search", test_search),
    ]
failed = []
result = test_func()
```


### P:\packages\search-research\core\cks\commands\unified_ingest.py

```python
import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
src_dir = project_root / "src"
logger = logging.getLogger(__name__)
VALID_ENTRY_TYPES = [
    "memory",
    "pattern",
    "code",
    "knowledge",
    "correction",
    "decision",
    "commitment",
    "insight",
    "learning",
    "docs",
]
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".rst": "rst",
    ".txt": "text",
}

class UnifiedCKSIngestion:
    __init__(self, enable_semantic: bool = True, db_path: str | Path | None = None) -> None
    ingest_file(self, file_path: str | Path, title: str | None = None, entry_type: str = "knowledge", tags: list[str] | None = None, category: str | None = None) -> dict[str, str]
    ingest_memory(self, question: str, answer: str, tags: list[str] | None = None, category: str | None = None) -> dict[str, str]
    ingest_pattern(self, title: str, content: str, entry_type: str = "pattern", tags: list[str] | None = None, category: str | None = None) -> dict[str, str]
    search(self, query: str, semantic: bool = True, expand: bool = False, spell_correct: bool = False, limit: int = 10, entry_type: str | None = None, fusion_method: str | None = None, diversity: float | None = None) -> list[dict]
    get_statistics(self) -> dict
format_result(result: dict, show_similarity: bool = False) -> str
ingest_multiple_files(ingestion: UnifiedCKSIngestion, pattern: str, entry_type: str, category: str | None = None, tags: list[str] | None = None, recursive: bool = False) -> list[dict]
main() -> None
```


### P:\packages\search-research\core\cks\consolidation\__init__.py

```python

```


### P:\packages\search-research\core\cks\consolidation\check_env.py

```python
import os
from pathlib import Path
env_path = Path("P:") / ".env"
content = env_path.read_text(encoding="utf-8")
line = line.strip()
key = line.split("=")[0].strip()
val = os.getenv(key)
```


### P:\packages\search-research\core\cks\consolidation\dreaming_cycle.py

```python
import asyncio
import json
import logging
import os
import sqlite3
import time
from enum import Enum
from typing import Any
import psutil
from pydantic import BaseModel, Field
from ..core.vector_manager import VectorKnowledgeManager
import instructor
LLM_AVAILABLE = True
LLM_AVAILABLE = False
logger = logging.getLogger(__name__)
import google.generativeai as genai
from instructor import from_gemini
GOOGLE_AVAILABLE = True
GOOGLE_AVAILABLE = False
from anthropic import AsyncAnthropic
ANTHROPIC_AVAILABLE = True
ANTHROPIC_AVAILABLE = False
logger = logging.getLogger(__name__)

class ConsolidationMode(str, Enum):
    FULLY_AUTOMATIC = "fully_automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    STRICT_REVIEW = "strict_review"

class RelationHypothesis(BaseModel):
    source_id = str
    target_id = str

class ResourceGuard:
    __init__(self, cpu_limit: float = 60.0, mem_limit: float = 80.0) -> None
    set_idle_priority(self) -> None
    check_health(self) -> bool

class DreamingService:
    __init__(self, mode: ConsolidationMode = ConsolidationMode.SEMI_AUTOMATIC, db_path: str = "data/knowledge.db") -> None
    get_orphans(self, limit: int = 10) -> list[dict[str, Any]]
    run_cycle(self, max_orphans: int = 5) -> None
    hypothesize_connections(self, orphan_text: str, orphan_id: str, candidates: list[str], candidate_ids: list[str]) -> RelationHypothesis | None
    validate_and_process(self, hypothesis: RelationHypothesis) -> None
```


### P:\packages\search-research\core\cks\consolidation\inspect_gemini.py

```python
from instructor import from_gemini
```


### P:\packages\search-research\core\cks\consolidation\inspect_instructor.py

```python
import instructor
from instructor import providers
```


### P:\packages\search-research\core\cks\consolidation\run_daemon.py

```python
import logging
import os
import sys
from pathlib import Path
import asyncio
LOG_DIR = Path(__file__).parents[3] / "logs"
logger = logging.getLogger("CKS_Daemon")
from dotenv import load_dotenv
env_path = Path(r"P:\.env")
from .dreaming_cycle import DreamingService
main() -> None
```


### P:\packages\search-research\core\cks\consolidation\simple_inspect.py

```python
import instructor
from instructor import providers
from instructor.providers import google
```


### P:\packages\search-research\core\cks\consolidation\test_dotenv.py

```python
import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(r"P:\.env")
val = os.getenv("GEMINI_API_KEY")
```


### P:\packages\search-research\core\cks\core\__init__.py

```python
import re
from .storage_manager import StorageConfig, StorageManager
__all__ = ["StorageConfig", "StorageManager"]
```


### P:\packages\search-research\core\cks\core\faiss_pytorch_adapter.py

```python
import logging
import warnings
from typing import Any
import numpy as np
import torch
from .pytorch_vector_storage import PyTorchStorageConfig, create_pytorch_vector_storage
import faiss
FAISS_AVAILABLE = True
FAISS_AVAILABLE = False

class FaissToPyTorchAdapter:
    __init__(self, dimension: int = 768, enable_gpu: bool = True, config: PyTorchStorageConfig | None = None) -> None
    add(self, vectors: np.ndarray) -> None
    search(self, queries: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]
    reconstruct(self, idx: int) -> np.ndarray
    reset(self) -> None
    save(self, file_path: str, allowed_dir: str | None = None) -> None
    load(self, file_path: str, allowed_dir: str | None = None) -> None
    @property
    ntotal(self) -> int
    get_device(self) -> str
    get_stats(self) -> dict[str, Any]
IndexFlatIP(dimension: int) -> FaissToPyTorchAdapter
IndexFlatL2(dimension: int) -> FaissToPyTorchAdapter
index_cpu_to_gpu(gpu_resources, device_id, index) -> FaissToPyTorchAdapter
StandardGpuResources() -> None

class FaissMigrationHelper:
    @staticmethod
    validate_faiss_code(code_path: str) -> dict[str, Any]
    @staticmethod
    generate_migration_script(original_path: str, output_path: str, allowed_dir: str | None = None) -> str
replace_faiss_with_pytorch(faiss_object) -> FaissToPyTorchAdapter
__faiss_compatible__ = True
__pytorch_backend__ = True
__migration_version__ = "1.0.0"
```


### P:\packages\search-research\core\cks\core\gpu_manager.py

```python
import builtins
import gc
import logging
import threading
import time
import warnings
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from typing import Any
import numpy as np
from ..utils.constitutional_validator import ConstitutionalValidator
import pynvml
NVML_AVAILABLE = True
NVML_AVAILABLE = False
import faiss
FAISS_AVAILABLE = True
FAISS_AVAILABLE = False
import cupy as cp
CUPY_AVAILABLE = True
CUPY_AVAILABLE = False
import cudf
import cuml
RAPIDS_AVAILABLE = True
RAPIDS_AVAILABLE = False

@dataclass
class GPUMemoryConfig:
    __post_init__(self)

@dataclass
class GPUMemoryStats:
    pass

class GPUMemoryManager:
    __init__(self, config: GPUMemoryConfig) -> None
    initialize(self) -> None
    get_memory_stats(self) -> GPUMemoryStats
    check_memory_availability(self, required_memory_mb: float) -> bool
    allocate_gpu_array(self, shape: tuple[int, ...], dtype: np.dtype = np.float32) -> np.ndarray | Any
    create_gpu_dataframe(self, data: dict[str, Any]) -> Any | pd.DataFrame
    create_faiss_index(self, dimension: int, index_type: str = "flat") -> Any
    cleanup_gpu_memory(self, force: bool = False) -> float
    get_performance_stats(self) -> dict[str, Any]
    @contextmanager
    gpu_context(self, required_memory_mb: float = 0)
    get_constitutional_compliance_score(self) -> float
    shutdown(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
```


### P:\packages\search-research\core\cks\core\multi_graph_engine.py

```python
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from ..utils.constitutional_validator import ConstitutionalValidator
from .gpu_manager import GPUMemoryConfig, GPUMemoryManager
from .storage_manager import StorageConfig, StorageManager
import faiss
FAISS_AVAILABLE = True
FAISS_AVAILABLE = False
from sentence_transformers import SentenceTransformer
SENTENCE_TRANSFORMERS_AVAILABLE = True
SENTENCE_TRANSFORMERS_AVAILABLE = False

class GraphType(Enum):
    KNOWLEDGE = "knowledge"
    VECTOR = "vector"
    CAUSAL = "causal"
    SOCIAL = "social"
    SYSTEM = "system"

class RelationshipType(Enum):
    SEMANTIC_SIMILARITY = "semantic_similarity"
    CAUSAL_INFLUENCE = "causal_influence"
    SOCIAL_DEPENDENCY = "social_dependency"
    SYSTEM_WORKFLOW = "system_workflow"
    KNOWLEDGE_REPRESENTATION = "knowledge_representation"
    TEMPORAL_SEQUENCE = "temporal_sequence"

@dataclass
class MultiGraphConfig:
    __post_init__(self)

class GraphNode:
    __init__(self, node_id: str, graph_type: GraphType, content: str, node_type: str, metadata: dict[str, Any] | None = None) -> None
    update_content(self, new_content: str, metadata_update: dict[str, Any] | None = None) -> None
    get_compliance_score(self) -> float
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "GraphNode"

class GraphEdge:
    __init__(self, edge_id: str, source_id: str, target_id: str, relationship: str, graph_type: GraphType, strength: float = 1.0, confidence: float = 1.0, metadata: dict[str, Any] | None = None) -> None
    update_strength(self, new_strength: float) -> None
    update_confidence(self, new_confidence: float) -> None
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "GraphEdge"

class CrossGraphRelationship:
    __init__(self, rel_id: str, source_graph: GraphType, source_id: str, target_graph: GraphType, target_id: str, relationship_type: RelationshipType, confidence: float = 0.8, strength: float = 0.7, metadata: dict[str, Any] | None = None) -> None
    to_dict(self) -> dict[str, Any]

class KnowledgeGraphOperations:
    __init__(self, storage_manager: StorageManager) -> None
    create_concept(self, concept: str, definition: str, category: str = "general", metadata: dict[str, Any] | None = None) -> str
    create_fact(self, subject: str, predicate: str, obj: str, confidence: float = 1.0, source: str | None = None, metadata: dict[str, Any] | None = None) -> str
    create_rule(self, condition: str, conclusion: str, confidence: float = 0.8, rule_type: str = "implication", metadata: dict[str, Any] | None = None) -> str
    create_relationship(self, source_id: str, target_id: str, relationship: str, strength: float = 1.0, metadata: dict[str, Any] | None = None) -> str
    query_concepts(self, category: str | None = None, name_pattern: str | None = None, limit: int = 100) -> list[dict[str, Any]]
    semantic_similarity(self, concept1_id: str, concept2_id: str) -> float

class VectorGraphOperations:
    __init__(self, storage_manager: StorageManager, config: MultiGraphConfig) -> None
    create_embedding(self, text: str, vector_id: str | None = None, metadata: dict[str, Any] | None = None) -> str
    search_similar(self, query_text: str, k: int = 10, similarity_threshold: float = 0.5) -> list[tuple[str, float]]
    find_semantic_clusters(self, vectors: list[str], min_cluster_size: int = 3) -> list[list[str]]
    batch_create_embeddings(self, texts: list[str], vector_ids: list[str] | None = None) -> list[str]

class CausalGraphOperations:
    __init__(self, storage_manager: StorageManager, config: MultiGraphConfig) -> None
    create_causal_event(self, event_name: str, event_type: str, timestamp: datetime | None = None, metadata: dict[str, Any] | None = None) -> str
    create_causal_relationship(self, cause_id: str, effect_id: str, strength: float = 0.8, confidence: float = 0.7, delay_ms: int = 0, metadata: dict[str, Any] | None = None) -> str
    find_causal_chains(self, start_event_id: str, max_depth: int = 5) -> list[list[str]]
    calculate_causal_strength(self, cause_id: str, effect_id: str) -> float
    predict_effects(self, cause_id: str, time_horizon_ms: int = 5000) -> list[tuple[str, float]]

class SocialGraphOperations:
    __init__(self, storage_manager: StorageManager, config: MultiGraphConfig) -> None
    create_entity(self, entity_name: str, entity_type: str, attributes: dict[str, Any] | None = None) -> str
    create_relationship(self, source_id: str, target_id: str, relationship_type: str, strength: float = 1.0, metadata: dict[str, Any] | None = None) -> str
    calculate_influence(self, entity_id: str, max_hops: int = 3) -> float
    find_communities(self, min_size: int = 3) -> list[list[str]]
    get_relationship_path(self, source_id: str, target_id: str, max_depth: int = 5) -> list[str]

class SystemGraphOperations:
    __init__(self, storage_manager: StorageManager, config: MultiGraphConfig) -> None
    create_component(self, component_name: str, component_type: str, status: str = "active", metadata: dict[str, Any] | None = None) -> str
    create_dependency(self, source_id: str, target_id: str, dependency_type: str, priority: int = 1, metadata: dict[str, Any] | None = None) -> str
    get_execution_order(self, component_ids: list[str]) -> list[str]
    find_bottlenecks(self) -> list[tuple[str, int]]
    validate_system_state(self) -> dict[str, Any]

class MultiGraphEngine:
    __init__(self, config: MultiGraphConfig = None) -> None
    initialize(self) -> None
    create_cross_graph_relationship(self, source_graph: GraphType, source_id: str, target_graph: GraphType, target_id: str, relationship_type: RelationshipType, confidence: float = 0.8, strength: float = 0.7, metadata: dict[str, Any] | None = None) -> str
    query_across_graphs(self, query: str, graph_types: list[GraphType] | None = None, max_results: int = 50) -> list[dict[str, Any]]
    get_cross_graph_insights(self, entity_id: str, source_graph: GraphType, max_depth: int = 3) -> dict[str, Any]
    semantic_reasoning(self, premise: str, context: dict[str, Any] | None = None) -> dict[str, Any]
    get_engine_metrics(self) -> dict[str, Any]
    optimize_performance(self) -> dict[str, Any]
    validate_constitutional_compliance(self) -> dict[str, Any]
    export_data(self, output_path: str, graph_types: list[GraphType] | None = None, include_relationships: bool = True) -> bool
    import_data(self, input_path: str, overwrite: bool = False) -> bool
    cleanup(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
create_engine(config: MultiGraphConfig = None) -> MultiGraphEngine
quick_semantic_search(query: str, engine: MultiGraphEngine = None, max_results: int = 10) -> list[dict[str, Any]]
```


### P:\packages\search-research\core\cks\core\multi_graph_engine_instrumented.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\core\pytorch_vector_storage.py

```python
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any
import numpy as np
import psutil
from ..utils.constitutional_validator import ConstitutionalValidator
import torch
import torch.nn.functional as F
TORCH_AVAILABLE = True
TORCH_AVAILABLE = False

@dataclass
class PyTorchStorageConfig:
    __post_init__(self)

class DeviceManager:
    __init__(self, prefer_gpu: bool = True, memory_threshold: float = 0.9) -> None
    execute_with_fallback(self, operation)

class PyTorchVectorStorage:
    __init__(self, config: PyTorchStorageConfig) -> None
    store_vector(self, vector_id: str, vector: np.ndarray, metadata: dict | None = None) -> bool
    search_similar_vectors(self, query_vector: np.ndarray, k: int = 10) -> list[tuple[str, float]]
    get_vector(self, vector_id: str) -> np.ndarray | None
    delete_vector(self, vector_id: str) -> bool
    get_stats(self) -> dict[str, Any]
    cleanup(self) -> None
    __del__(self) -> None
create_pytorch_vector_storage(config: PyTorchStorageConfig | None = None) -> PyTorchVectorStorage
```


### P:\packages\search-research\core\cks\core\pytorch_vector_storage_instrumented.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\core\semantic_analyzer.py

```python
import logging
import re
from typing import Any
import yake
YAKE_AVAILABLE = True
YAKE_AVAILABLE = False
logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    __init__(self, language: str = "en", n_gram: int = 2, top_k: int = 10) -> None
    extract_keywords(self, text: str) -> list[tuple]
    extract_entities(self, text: str) -> dict[str, list[str]]
    analyze(self, text: str) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\core\storage_manager.py

```python
import gc
import json
import logging
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
get_import(name: str)

@dataclass
class StorageConfig:
    __post_init__(self)

class StorageManager:
    __init__(self, config: StorageConfig) -> None
    initialize(self) -> None
    create_knowledge_node(self, node_data: dict[str, Any]) -> str
    get_knowledge_node(self, node_id: str) -> dict[str, Any] | None
    update_knowledge_node(self, node_id: str, update_data: dict[str, Any]) -> bool
    create_knowledge_edge(self, edge_data: dict[str, Any]) -> str
    store_vector(self, vector_id: str, vector) -> bool
    get_vector(self, vector_id: str)
    search_similar_vectors(self, query_vector, k: int = 10) -> list[tuple[str, float]]
    create_cross_graph_relationship(self, relationship_data: dict[str, Any]) -> str
    get_cross_graph_relationships(self, source_graph: str | None = None, source_id: str | None = None, target_graph: str | None = None, target_id: str | None = None) -> list[dict[str, Any]]
    batch_create_knowledge_nodes(self, node_data_list: list[dict[str, Any]]) -> list[str]
    batch_store_vectors(self, vector_ids: list[str], vectors) -> bool
    create_causal_node(self, node_data: dict[str, Any]) -> str
    get_memory_usage(self) -> float
    get_storage_stats(self) -> dict[str, Any]
    cleanup(self) -> None
    @contextmanager
    transaction(self)
    get_constitutional_compliance_score(self) -> float
    get_audit_trail(self) -> list[dict[str, Any]]
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
    @property
    db_connection(self)
    @property
    faiss_index(self)
```


### P:\packages\search-research\core\cks\core\storage_manager_optimized.py

```python
import gc
import json
import logging
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
get_import(name: str)

@dataclass
class StorageConfig:
    __post_init__(self)

class StorageManager:
    __init__(self, config: StorageConfig) -> None
    initialize(self) -> None
    create_knowledge_node(self, node_data: dict[str, Any]) -> str
    get_knowledge_node(self, node_id: str) -> dict[str, Any] | None
    update_knowledge_node(self, node_id: str, update_data: dict[str, Any]) -> bool
    create_knowledge_edge(self, edge_data: dict[str, Any]) -> str
    store_vector(self, vector_id: str, vector) -> bool
    get_vector(self, vector_id: str)
    search_similar_vectors(self, query_vector, k: int = 10) -> list[tuple[str, float]]
    create_cross_graph_relationship(self, relationship_data: dict[str, Any]) -> str
    get_cross_graph_relationships(self, source_graph: str | None = None, source_id: str | None = None, target_graph: str | None = None, target_id: str | None = None) -> list[dict[str, Any]]
    batch_create_knowledge_nodes(self, node_data_list: list[dict[str, Any]]) -> list[str]
    batch_store_vectors(self, vector_ids: list[str], vectors) -> bool
    create_causal_node(self, node_data: dict[str, Any]) -> str
    get_memory_usage(self) -> float
    get_storage_stats(self) -> dict[str, Any]
    cleanup(self) -> None
    @contextmanager
    transaction(self)
    get_constitutional_compliance_score(self) -> float
    get_audit_trail(self) -> list[dict[str, Any]]
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
    @property
    db_connection(self)
    @property
    faiss_index(self)
```


### P:\packages\search-research\core\cks\core\storage_manager_original.py

```python
import gc
import json
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
import numpy as np
import psutil
from ..utils.constitutional_validator import ConstitutionalValidator
from .faiss_pytorch_adapter import FaissToPyTorchAdapter, IndexFlatIP
FAISS_AVAILABLE = True
PYTORCH_AVAILABLE = True
FAISS_AVAILABLE = False
PYTORCH_AVAILABLE = False

@dataclass
class StorageConfig:
    __post_init__(self)

class StorageManager:
    __init__(self, config: StorageConfig) -> None
    initialize(self) -> None
    create_knowledge_node(self, node_data: dict[str, Any]) -> str
    get_knowledge_node(self, node_id: str) -> dict[str, Any] | None
    update_knowledge_node(self, node_id: str, update_data: dict[str, Any]) -> bool
    create_knowledge_edge(self, edge_data: dict[str, Any]) -> str
    store_vector(self, vector_id: str, vector: np.ndarray) -> bool
    get_vector(self, vector_id: str) -> np.ndarray | None
    search_similar_vectors(self, query_vector: np.ndarray, k: int = 10) -> list[tuple[str, float]]
    create_cross_graph_relationship(self, relationship_data: dict[str, Any]) -> str
    get_cross_graph_relationships(self, source_graph: str | None = None, source_id: str | None = None, target_graph: str | None = None, target_id: str | None = None) -> list[dict[str, Any]]
    batch_create_knowledge_nodes(self, node_data_list: list[dict[str, Any]]) -> list[str]
    batch_store_vectors(self, vector_ids: list[str], vectors: np.ndarray) -> bool
    create_causal_node(self, node_data: dict[str, Any]) -> str
    get_memory_usage(self) -> float
    get_storage_stats(self) -> dict[str, Any]
    cleanup(self) -> None
    @contextmanager
    transaction(self)
    get_constitutional_compliance_score(self) -> float
    get_audit_trail(self) -> list[dict[str, Any]]
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
```


### P:\packages\search-research\core\cks\core\vector_manager.py

```python
import logging
import uuid
from pathlib import Path
from typing import Any
from pydantic_settings import BaseSettings
import faiss
import numpy as np
FAISS_AVAILABLE = True
FAISS_AVAILABLE = False
from fastembed import TextEmbedding
FASTEMBED_AVAILABLE = True
FASTEMBED_AVAILABLE = False
from sentence_transformers import SentenceTransformer
SENTENCE_AVAILABLE = True
SENTENCE_AVAILABLE = False
logger = logging.getLogger(__name__)

class VectorConfig(BaseSettings):
    pass

class EmbeddingRouter:
    __init__(self, config: VectorConfig) -> None
    embed_query(self, text: str, mode: str = "fast") -> list[float]
    embed_documents(self, texts: list[str], mode: str = "fast") -> list[list[float]]

class VectorKnowledgeManager:
    __init__(self, config: VectorConfig | None = None) -> None
    ingest(self, id: str, text: str, metadata: dict[str, Any] | None = None) -> bool
    search(self, query: str, limit: int = 10, threshold: float = 0.7) -> list[dict[str, Any]]
    close(self) -> None
```


### P:\packages\search-research\core\cks\decision_extractor.py

```python
import re
from dataclasses import dataclass, field

@dataclass
class ExtractedDecision:
    problem_statement = str
    to_cks_content(self) -> str
    to_cks_metadata(self) -> dict

class DecisionExtractor:
    PATTERNS = {
        "problem": [
            r"##?\s*Problem\s+(?:Definition|:).*?\n+(.+?)(?:\n\n|\n(?=##)|$)",
            r"\bProblem:?\s+(.+?)(?:\n\n|\n(?=[A-Z])|$)",
            r"##?\s*Issue.*?\n+(.+?)(?:\n\n|\n(?=##)|$)",
        ],
        "hypotheses": [
            r"##?\s*Hypothesis(?:s|\s+Testing)?:?\s*\n+(.+?)(?:\n\n|\n(?=##?\s+[A-Z])|$)",
            r"\bHypothes(?:is|es):?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
            r"\bCould\s+be:?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
            r"\bPossible\s+causes?:?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
        ],
        "decision": [
            r"\bRecommend:?\s+(.+?)(?:\n|$)",
            r"\bDecision:?\s+(.+?)(?:\n|$)",
            r"\bChoose:?\s+(.+?)(?:\n|$)",
            r"\bGoing\s+with:?\s+(.+?)(?:\n|$)",
        ],
        "alternatives": [
            r"\bOption\s+([A-Z]):\s+(.+?)(?:\n|$)",
            r"\bAlternative:?\s+(.+?)(?:\n|$)",
        ],
        "rationale": [
            r"\bRationale:?\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)",
            r"\bBecause:?\s+(.+?)(?:\n|$)",
        ],
        "outcome": [
            r"\bVerif(?:ied|ication):?\s+(.+?)(?:\n|$)",
            r"\bOutcome:?\s+(.+?)(?:\n|$)",
        ],
        "reversibility": [
            r"\bR:?([0-2])",
        ],
    }
    DECISION_TYPE_KEYWORDS = {
        "ARCHITECTURAL": ["architect", "design", "pattern", "structure", "schema"],
        "DEBUGGING": ["debug", "fix", "error", "bug", "broken", "fail", "crash"],
        "IMPLEMENTATION": ["implement", "build", "create", "write", "add", "use"],
        "PROCESS": ["test", "verify", "workflow", "process", "workflow"],
    }
    __init__(self, min_confidence: float = 0.60)
    extract_from_transcript(self, transcript: str) -> list[ExtractedDecision]
extract_decisions_from_transcript(transcript: str, min_confidence: float = 0.60) -> list[ExtractedDecision]
```


### P:\packages\search-research\core\cks\document_ingest.py

```python
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    LOCATION = "location"
    TECHNOLOGY = "technology"

@dataclass(frozen=True)
class DocumentEntity:
    name = str
    type = EntityType
    start_char = int
    end_char = int
    to_dict(self) -> dict[str, Any]

@dataclass
class DocumentChunk:
    text = str
    index = int
    parent_id = str
    start_char = int
    end_char = int
    @property
    size(self) -> int

class DocumentChunker:
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_OVERLAP = 50
    SENTENCE_BOUNDARY = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$|(?<=\n)\s*",
        re.MULTILINE,
    )
    __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> None
    chunk_text(self, text: str) -> list[DocumentChunk]

class DocumentEntityExtractor:
    CAPITALIZED_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
    TECH_PATTERNS = [
        r"\bPython\b",
        r"\bJavaScript\b",
        r"\bTypeScript\b",
        r"\bSQL\b",
        r"\bFAISS\b",
        r"\bSQLite\b",
        r"\bPostgreSQL\b",
        r"\bReact\b",
        r"\bDocker\b",
        r"\bk8s\b",
        r"\bKubernetes\b",
        r"\bGit\b",
        r"\bAPI\b",
    ]
    ORG_PATTERNS = [
        r"\bGoogle\b",
        r"\bOpenAI\b",
        r"\bAnthropic\b",
        r"\bMicrosoft\b",
        r"\bMeta\b",
    ]
    __init__(self) -> None
    extract(self, text: str) -> list[DocumentEntity]

@dataclass
class IngestResult:
    parent_id = str
    chunk_count = int
    entities_found = int

class MultiGraphDocumentIngester:
    __init__(self, storage: Any | None = None, vector_manager: Any | None = None, chunker: DocumentChunker | None = None, extractor: DocumentEntityExtractor | None = None) -> None
    ingest(self, text: str, title: str, source: str = "user_paste", tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> IngestResult
```


### P:\packages\search-research\core\cks\documentation_manager.py

```python
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class DocMetadata:
    title = str
    category = str
    feature = str
    author = str
    created_at = datetime
    file_path = str
    doc_type = str
    version = str
    tags = list[str]
    cross_references = list[str]
    file_hash = str

class CKSDocumentationManager:
    __init__(self) -> None
    store_documentation(self, doc_path: str, feature_name: str, doc_type: str = "user_guide", cross_references: list[str] | None = None, tags: list[str] | None = None) -> bool
    store_directory(self, docs_dir: str, feature_name: str, pattern: str = "*.md") -> dict[str, bool]
    validate_documentation_coverage(self, feature_name: str, required_docs: list[str]) -> dict[str, Any]
    query_documentation(self, query: str, feature: str | None = None, doc_type: str | None = None, limit: int = 10) -> list[dict]
store_documentation_directory(docs_dir: str, feature_name: str)
validate_documentation(feature_name: str, required_docs: list[str])
search_documentation(query: str)
```


### P:\packages\search-research\core\cks\entity_filter.py

```python
import re
from datetime import UTC, datetime
from uuid import uuid4

class CKSEntityFilter:
    KNOWN_ENTITIES = {
        "cks": "Constitutional Knowledge System",
        "desktop-commander": "Desktop Commander",
        "claude-code": "Claude Code",
        "nse": "Next Step Engine",
        "cwo12": "CWO12 Workflow Engine",
        "taskmaster": "TaskMaster",
    }
    __init__(self, cks_instance) -> None
    create_entity(self, slug: str, name: str, entity_type: str) -> str
    link_entity(self, entry_id: str, entity_slug: str) -> bool
    unlink_entity(self, entry_id: str, entity_slug: str) -> bool
    get_entities_for_entry(self, entry_id: str) -> list[dict]
    get_all_entities(self, entity_type: str | None = None) -> list[dict]
    search_with_entity_filter(self, query: str, entity_slug: str | None = None, entry_type: str | None = None, limit: int = 5, auto_detect: bool = True) -> list[dict]
    log_recall(self, session_id: str, query: str, results: list[dict], entity_slug: str | None = None) -> None
    get_recall_history(self, session_id: str | None = None, entity_slug: str | None = None, limit: int = 100) -> list[dict]
    prune_old_recall_logs(self, days: int = 90) -> None
search_entities(query: str, entity: str | None = None, limit: int = 5) -> list[dict]
```


### P:\packages\search-research\core\cks\examples\__init__.py

```python

```


### P:\packages\search-research\core\cks\examples\gpu_manager_examples.py

```python
import logging
import time
import numpy as np
from core.gpu_manager import GPUMemoryConfig, GPUMemoryManager
from core.storage_manager import StorageConfig, StorageManager
logger = logging.getLogger(__name__)
example_1_basic_gpu_management() -> None
example_2_rapids_integration() -> None
example_3_faiss_gpu_operations() -> None
example_4_memory_monitoring_and_cleanup() -> None
example_5_integrated_storage_and_gpu() -> None
example_6_solo_developer_optimization() -> None
main() -> None
```


### P:\packages\search-research\core\cks\examples\multi_graph_engine_examples.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\fts_performance_analysis.py

```python
import math
import random
import sqlite3
import statistics
import time
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
analyze_database(db_path: Path) -> None
db_path = PROJECT_ROOT / "__csf" / "data" / "cks.db"
```


### P:\packages\search-research\core\cks\graph.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal, TypeVar
from collections.abc import Callable, Iterable, Iterator
T = TypeVar("T")

@dataclass(frozen=True)
class EntityId:
    value = str
    __post_init__(self) -> None
    __str__(self) -> str
    @classmethod
    parse(cls, value: str) -> EntityId

@dataclass(frozen=True)
class Entity:
    id = EntityId
    label = str
    entity_type = str
    @property
    degree(self) -> int
    with_property(self, key: str, value: str | int | float | bool) -> Entity

@dataclass(frozen=True)
class Relation:
    source = EntityId
    target = EntityId
    relation_type = str
    __post_init__(self) -> None
    @property
    key(self) -> str
    reverse(self) -> Relation

class Graph(ABC):
    __init__(self, directed: bool = True) -> None
    @abstractmethod
    add_entity(self, entity: Entity) -> bool
    @abstractmethod
    add_relation(self, relation: Relation) -> bool
    @abstractmethod
    get_entity(self, entity_id: EntityId) -> Entity | None
    @abstractmethod
    get_relation(self, source: EntityId, target: EntityId, relation_type: str) -> Relation | None
    @abstractmethod
    neighbors(self, entity_id: EntityId, relation_type: str | None = None) -> Iterable[tuple[EntityId, Relation]]
    @abstractmethod
    traverse(self, start: EntityId, direction: Literal["out", "in", "both"] = "out", max_depth: int = 3, visitor: Callable[[EntityId, int], bool] | None = None) -> Iterable[EntityId]
    @abstractmethod
    find_paths(self, source: EntityId, target: EntityId, max_length: int = 5) -> Iterable[list[EntityId]]
    @abstractmethod
    query(self, entity_type: str | None = None, relation_type: str | None = None, properties: dict[str, str | int | float | bool] | None = None) -> Iterable[Entity]
    @property
    entity_count(self) -> int
    @property
    relation_count(self) -> int
    @abstractmethod
    degree(self, entity_id: EntityId, direction: Literal["in", "out", "both"] = "both") -> int
    clear(self) -> None

class MutableGraph(Graph):
    __init__(self, directed: bool = True) -> None
    add_entity(self, entity: Entity) -> bool
    add_relation(self, relation: Relation) -> bool
    get_entity(self, entity_id: EntityId) -> Entity | None
    get_relation(self, source: EntityId, target: EntityId, relation_type: str) -> Relation | None
    neighbors(self, entity_id: EntityId, relation_type: str | None = None) -> Iterator[tuple[EntityId, Relation]]
    traverse(self, start: EntityId, direction: Literal["out", "in", "both"] = "out", max_depth: int = 3, visitor: Callable[[EntityId, int], bool] | None = None) -> Iterator[EntityId]
    find_paths(self, source: EntityId, target: EntityId, max_length: int = 5) -> Iterator[list[EntityId]]
    query(self, entity_type: str | None = None, relation_type: str | None = None, properties: dict[str, str | int | float | bool] | None = None) -> Iterator[Entity]
    degree(self, entity_id: EntityId, direction: Literal["in", "out", "both"] = "both") -> int
    clear(self) -> None
```


### P:\packages\search-research\core\cks\hybrid_search_patch.py

```python
import json
from .reranking import apply_length_aware_reranking, reciprocal_rank_fusion
patch_hybrid_search(cks_class: type) -> type
search_hybrid(self, query: str, entry_type: str | None = None, limit: int = 5, fts_weight: float = 0.5, semantic_weight: float = 0.5, fusion_method: str = "rrf") -> list[dict]
```


### P:\packages\search-research\core\cks\hyde.py

```python
import logging
from typing import Any
logger = logging.getLogger(__name__)

class HyDEQueryExpander:
    __init__(self, enable_cache: bool = True) -> None
    generate_hypothetical(self, query: str, query_type: str = "general") -> str
    expand_query(self, query: str, query_type: str = "general") -> str
    get_cache_stats(self) -> dict[str, Any]
get_hypothetical_document(query: str, query_type: str = "general") -> str
__all__ = [
    "HyDEQueryExpander",
    "get_hypothetical_document",
]
```


### P:\packages\search-research\core\cks\hyde_integration.py

```python
import logging
from typing import Any
logger = logging.getLogger(__name__)
from .hyde import HyDEQueryExpander
HYDE_AVAILABLE = True
HYDE_AVAILABLE = False
detect_query_type(query: str) -> str
hyde_search_semantic(cks_instance: Any, query: str, entry_type: str | None = None, limit: int = 10, enable_hyde: bool = True) -> list[dict]
hyde_search_with_boost(cks_instance: Any, query: str, entry_type: str | None = None, limit: int = 10, boost_factor: float = 1.1) -> list[dict]
__all__ = [
    "detect_query_type",
    "hyde_search_semantic",
    "hyde_search_with_boost",
]
```


### P:\packages\search-research\core\cks\ingester_adapter.py

```python
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from .document_ingest import (
    DocumentChunker, DocumentEntityExtractor, )
logger = logging.getLogger(__name__)
__all__ = ["AdapterIngestResult", "CKSIngesterAdapter"]

@dataclass
class AdapterIngestResult:
    chunk_count = int
    entities_found = int

class CKSIngesterAdapter:
    __init__(self, cks, chunk_size: int = 500, overlap: int = 50) -> None
    ingest_document(self, text: str, title: str, tags: list[str] | None = None, source: str = "adapter", chunk_size: int | None = None, overlap: int | None = None) -> AdapterIngestResult
```


### P:\packages\search-research\core\cks\initialize_cks_direct.py

```python
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
DB_PATH = DATA_DIR / "cks_hypergraph.db"

class CKSDirectInitializer:
    __init__(self) -> None
    initialize_database(self) -> bool
    migrate_tdd_data(self) -> bool
    migrate_multi_agent_research(self) -> bool
    migrate_memory_bank_sample(self) -> bool
    create_semantic_relationships(self) -> bool
    generate_statistics(self) -> dict[str, Any]
    save_system_info(self) -> bool
    run(self) -> bool
main() -> None
```


### P:\packages\search-research\core\cks\initialize_cks_hypergraph.py

```python
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent
from .core.gpu_manager import GPUMemoryConfig
from .core.multi_graph_engine import (
        GraphType, MultiGraphConfig, MultiGraphEngine, RelationshipType, create_engine, )
from .core.storage_manager import StorageConfig
from .utils.constitutional_validator import ConstitutionalValidator
logger = logging.getLogger(__name__)

class CKSHyperGraphInitializer:
    __init__(self, reset: bool = False) -> None
    create_config(self) -> MultiGraphConfig
    initialize_engine(self) -> bool
    migrate_tdd_enforcement_data(self) -> bool
    migrate_multi_agent_research(self) -> bool
    migrate_memory_bank_research(self) -> bool
    create_cross_graph_relationships(self) -> bool
    validate_system(self) -> bool
    persist_configuration(self) -> bool
    run_initialization(self) -> bool
main() -> None
```


### P:\packages\search-research\core\cks\integration\.csf_nip\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\__init__.py

```python
import re
from datetime import date
from .adapter_factory import cks_adapter_factory
from .integration_manager import OperationMetrics, cks_integration_manager
from .interfaces.base_adapter import (
    BaseCKSAdapter, CKSContext, IntegrationResult, IntegrationType, adapter_registry, )
__version__ = "1.0.0"
__all__ = [
    "BaseCKSAdapter",
    "CKSContext",
    "IntegrationResult",
    # Core classes
    "IntegrationType",
    # Registry
    "adapter_registry",
    # Factory and manager
    "cks_adapter_factory",
    "cks_integration_manager",
]
```


### P:\packages\search-research\core\cks\integration\adapter_factory.py

```python
import logging
from typing import Any
from .interfaces.base_adapter import (
    BaseCKSAdapter, CKSContext, IntegrationResult, IntegrationType, adapter_registry, )
logger = logging.getLogger(__name__)

class CKSAdapterFactory:
    __init__(self) -> None
    register_adapter_class(self, integration_type: IntegrationType, adapter_class: type[BaseCKSAdapter]) -> None
    set_default_config(self, integration_type: IntegrationType, config: dict[str, Any]) -> None
    create_adapter(self, integration_type: IntegrationType, config: dict[str, Any] | None = None) -> IntegrationResult
    create_context(self, integration_type: IntegrationType, operation_id: str, metadata: dict[str, Any] | None = None) -> CKSContext
    get_available_integrations(self) -> list[IntegrationType]
    initialize_all_adapters(self, configs: dict[IntegrationType, dict[str, Any]] | None = None) -> dict[IntegrationType, IntegrationResult]
    get_adapter_metrics(self) -> dict[str, Any]
cks_adapter_factory = CKSAdapterFactory()
```


### P:\packages\search-research\core\cks\integration\adapters\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\adapters\agent_coordinator.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\automated_fix_suggestions_integration.py

```python
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from modules.knowledge_system.agent_interface import EnhancedAgentInterface
from ..utils.logging_utils import setup_logging
project_root = Path(__file__).parent.parent.parent.parent.parent

class CKSSearchType(Enum):
    SOLUTION_PATTERNS = "solution_patterns"
    BEST_PRACTICES = "best_practices"
    ISSUE_INSIGHTS = "issue_insights"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    EXPERT_RECOMMENDATIONS = "expert_recommendations"
    SIMILAR_IMPLEMENTATIONS = "similar_implementations"

@dataclass
class CKSSearchRequest:
    search_type = CKSSearchType
    query = str

@dataclass
class CKSSearchResult:
    success = bool
    patterns = list[dict[str, Any]]
    total_found = int
    search_time = float
    confidence = float

class CKSIntegration:
    __init__(self, log_level: str = "INFO") -> None
    search_solution_patterns(self, fix_type: Any, language: str, domain: str) -> list[dict[str, Any]]
    get_issue_insights(self, context: Any) -> dict[str, Any]
    search_best_practices(self, language: str, domain: str, topic: str) -> list[dict[str, Any]]
    find_similar_implementations(self, code: str, language: str) -> list[dict[str, Any]]
    get_expert_recommendations(self, issue_type: str, domain: str) -> list[dict[str, Any]]
    store_fix_pattern(self, fix_pattern: dict[str, Any]) -> bool
    get_statistics(self) -> dict[str, Any]
    clear_cache(self) -> None
    health_check(self) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\integration\adapters\constitutional_compliance_monitor.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\constitutional_compliance_validator.py

```python
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    CRITICAL = 0.95
    HIGH = 0.90
    MEDIUM = 0.80
    LOW = 0.70

class ViolationSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ArticleReference(Enum):
    ARTICLE_3_1 = "Article 3.1: Evidence-Based Claims"
    ARTICLE_3_2 = "Article 3.2: Performance-Based Validation"
    ARTICLE_3_3 = "Article 3.3: Anti-Exaggeration Requirements"
    ARTICLE_3_4 = "Article 3.4: Truth-Based Reporting"
    ARTICLE_4_1 = "Article 4.1: Quality Gate Enforcement"
    ARTICLE_4_2 = "Article 4.2: Compliance Monitoring"
    ARTICLE_4_3 = "Article 4.3: Violation Remediation"

class CSFStandard(Enum):
    SECURITY_FIRST = "Security First"
    VULNERABILITY_TRANSPARENCY = "Vulnerability Transparency"
    AUTHENTICATION_INTEGRITY = "Authentication Integrity"
    THREAT_MODEL_COMPLIANCE = "Threat Model Compliance"
    CONTINUOUS_VALIDATION = "Continuous Validation"

@dataclass
class ComplianceViolation:
    violation_id = str
    violation_type = str
    severity = ViolationSeverity
    article_reference = ArticleReference
    description = str
    evidence_required = list[str]
    suggested_remediation = str

@dataclass
class ComplianceScore:
    overall_score = float
    article_scores = dict[ArticleReference, float]
    csf_scores = dict[CSFStandard, float]
    confidence_level = float

@dataclass
class ComplianceReport:
    is_compliant = bool
    compliance_level = ComplianceLevel
    overall_score = float
    violations = list[ComplianceViolation]
    recommendations = list[str]
    evidence_gaps = list[str]
    auto_remediation_actions = list[str]

class CKSConstitutionalComplianceValidator:
    __init__(self, compliance_threshold: float = 0.95, enable_auto_remediation: bool = True, log_level: str = "INFO") -> None
    validate_compliance(self, context: dict[str, Any], evidence: dict[str, Any] | None = None, validation_level: ComplianceLevel = ComplianceLevel.CRITICAL) -> ComplianceReport
    get_performance_metrics(self) -> dict[str, Any]
    clear_cache(self) -> None
create_cks_constitutional_compliance_validator(compliance_threshold: float = 0.95, enable_auto_remediation: bool = True, log_level: str = "INFO") -> CKSConstitutionalComplianceValidator
validate_cks_constitutional_compliance(context: dict[str, Any], evidence: dict[str, Any] | None = None, validation_level: ComplianceLevel = ComplianceLevel.CRITICAL, compliance_threshold: float = 0.95) -> ComplianceReport
main() -> None
```


### P:\packages\search-research\core\cks\integration\adapters\error_recovery_system.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\evidence_integration.py

```python
import hashlib
import json
import logging
import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)

class CKSPatternType(Enum):
    WORKFLOW_PATTERN = "workflow_pattern"
    TASK_PATTERN = "task_pattern"
    ERROR_PATTERN = "error_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    COMPLIANCE_PATTERN = "compliance_pattern"
    CONSTITUTIONAL_PATTERN = "constitutional_pattern"
    ANTI_MOCK_PATTERN = "anti_mock_pattern"
    QUALITY_PATTERN = "quality_pattern"
    RESEARCH_PROTOCOL_PATTERN = "research_protocol_pattern"
    EXPLORATION_PATTERN = "exploration_pattern"
    EVIDENCE_COLLECTION_PATTERN = "evidence_collection_pattern"
    CONTEXT_AWARENESS_PATTERN = "context_awareness_pattern"

class CKSConfidenceLevel(Enum):
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class CKSPattern:
    id = str
    name = str
    pattern_type = CKSPatternType
    pattern_regex = str
    description = str
    __post_init__(self)
    match(self, text: str) -> tuple[bool, float, list[str]]

@dataclass
class CKSEnrichment:
    evidence_id = str
    patterns_matched = list[tuple[str, float]]
    knowledge_correlations = list[dict[str, Any]]
    constitutional_insights = dict[str, Any]
    quality_assessments = dict[str, float]
    enhancement_timestamp = datetime
    __post_init__(self)

class CKSIntegrator:
    __init__(self, cks_db_path: str, knowledge_base_path: str) -> None
    enrich_evidence(self, evidence_id: str, evidence_data: dict[str, Any], evidence_text: str | None = None) -> CKSEnrichment
    get_enrichment_statistics(self) -> dict[str, Any]
    add_custom_pattern(self, pattern: CKSPattern) -> bool
    get_enrichment_for_evidence(self, evidence_id: str) -> CKSEnrichment | None
    validate_research_methodology(self, evidence_data: dict[str, Any], evidence_text: str | None = None) -> dict[str, Any]
    get_pattern_effectiveness(self) -> dict[str, dict[str, Any]]
```


### P:\packages\search-research\core\cks\integration\adapters\instrumentation.py

```python
import asyncio
import threading
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any
from ..core.universal_instrumentation import get_global_instrumentation
from ..models.event_models import SystemCategory
from ..utils.performance_tracker import PerformanceTracker

class CKSOperationType(Enum):
    CHAT_SEARCH = "chat_search"
    CHAT_PATTERN_DETECTION = "chat_pattern_detection"
    CHAT_ANALYSIS = "chat_analysis"
    CHAT_RETRIEVAL = "chat_retrieval"
    GRAPH_QUERY = "graph_query"
    GRAPH_INFERENCE = "graph_inference"
    SEMANTIC_REASONING = "semantic_reasoning"
    CROSS_GRAPH_ANALYSIS = "cross_graph_analysis"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    VECTOR_STORE = "vector_store"
    VECTOR_RETRIEVE = "vector_retrieve"
    VECTOR_SEARCH = "vector_search"
    VECTOR_BATCH_OPERATION = "vector_batch_operation"
    EMBEDDING_GENERATION = "embedding_generation"
    RAG_ORCHESTRATION = "rag_orchestration"
    DOCUMENT_PROCESSING = "document_processing"
    CONTEXT_AUGMENTATION = "context_augmentation"
    RESPONSE_GENERATION = "response_generation"
    COMPONENT_COORDINATION = "component_coordination"
    WORKFLOW_CORRELATION = "workflow_correlation"
    ERROR_RECOVERY = "error_recovery"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"

class CKSComponentType(Enum):
    CHAT_HISTORY_CLIENT = "ChatHistoryClient"
    MULTI_GRAPH_ENGINE = "MultiGraphEngine"
    VECTOR_STORAGE = "VectorStorage"
    RAG_WORKFLOW = "RAGWorkflow"
    RAG_INTEGRATION_COORDINATOR = "CKSRAGIntegrationCoordinator"
    STORAGE_MANAGER = "StorageManager"
    PYTORCH_VECTOR_STORAGE = "PyTorchVectorStorage"

@dataclass
class CKSMetrics:
    pass

@dataclass
class WorkflowContext:
    add_step(self, component: str, operation: str) -> None
    to_dict(self) -> dict[str, Any]

class CKSInstrumentation:
    __init__(self) -> None
    track_cks_operation(self, component_type: CKSComponentType, operation_type: CKSOperationType, execution_time_ms: float, success: bool = True, workflow_context: WorkflowContext | None = None, additional_metadata: dict[str, Any] | None = None) -> bool
    create_workflow_context(self, session_id: str | None = None, correlation_id: str | None = None, user_context: dict[str, Any] | None = None) -> WorkflowContext
    update_workflow_context(self, workflow_id: str, component: str, operation: str, additional_metadata: dict[str, Any] | None = None) -> WorkflowContext
    get_workflow_context(self, workflow_id: str) -> WorkflowContext | None
    complete_workflow(self, workflow_id: str) -> WorkflowContext | None
    @contextmanager
    track_operation(self, component_type: CKSComponentType, operation_type: CKSOperationType, workflow_context: WorkflowContext | None = None, metadata: dict[str, Any] | None = None)
    @asynccontextmanager
    track_async_operation(self, component_type: CKSComponentType, operation_type: CKSOperationType, workflow_context: WorkflowContext | None = None, metadata: dict[str, Any] | None = None)
    track_error_recovery(self, component_type: CKSComponentType, error_type: str, recovery_action: str, recovery_successful: bool, workflow_context: WorkflowContext | None = None) -> None
    get_cks_metrics(self) -> dict[str, Any]
    get_workflow_analytics(self) -> dict[str, Any]
    shutdown(self) -> None
get_cks_instrumentation() -> CKSInstrumentation
instrument_cks_component(component_type: CKSComponentType, operation_type: CKSOperationType, track_workflow: bool = True)
instrument_chat_search(track_workflow: bool = True)
instrument_vector_search(track_workflow: bool = True)
instrument_graph_query(track_workflow: bool = True)
instrument_rag_orchestration(track_workflow: bool = True)
```


### P:\packages\search-research\core\cks\integration\adapters\knowledge_constitutional_validator.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\knowledge_input_validator.py

```python
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from .cks_constitutional_validator import CKSConstitutionalValidator
logger = logging.getLogger(__name__)

class CKSCommand(Enum):
    CKS = "cks"
    QUERY = "query"
    LEARN = "learn"

class ValidationLevel(Enum):
    NOTE = "note"
    CONCERN = "concern"
    ISSUE = "issue"
    VIOLATION = "violation"

@dataclass
class ValidationResult:
    is_valid = bool
    command = CKSCommand
    validation_level = ValidationLevel
    issues = list[str]
    recommendations = list[str]
    sanitized_parameters = dict[str, Any]
    evidence = dict[str, Any]

class CKSInputValidator:
    __init__(self) -> None
    validate_command_input(self, command: str, parameters: dict[str, Any], user_context: dict[str, Any] | None = None) -> ValidationResult
    get_validation_summary(self) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\integration\adapters\monitoring_analytics.py

```python
import asyncio
import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from dataclasses_json import dataclass_json
from ..constitutional_compliance.cwo12_cks_compliance_validator import (
        CWO12CKSConstitutionalValidator, )
from ..knowledge_system.cks_constitutional_validator import (
        CKSConstitutionalValidator, )
from ..orchestration.cks_agent_coordinator import CKSAgentCoordinator
from ..performance.cks_performance_optimizer import CKSPreformanceOptimizer
from ..resilience.cks_fallback_error_handler import CKSFallbackErrorHandler
logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATIO = "ratio"
    RATE = "rate"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TimeGranularity(Enum):
    REAL_TIME = "real_time"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

@dataclass_json
@dataclass
class MetricPoint:
    metric_name = str
    metric_type = MetricType
    value = int | float | dict[str, Any]
    timestamp = datetime
    component = str
    operation = str
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "MetricPoint"

@dataclass_json
@dataclass
class Alert:
    alert_id = str
    severity = AlertSeverity
    title = str
    description = str
    component = str
    metric_name = str
    threshold_value = float
    current_value = float
    condition = str
    timestamp = datetime

@dataclass_json
@dataclass
class UserExperienceMetrics:
    session_id = str
    user_id = str | None
    start_time = datetime
    end_time = datetime | None

@dataclass_json
@dataclass
class ComplianceTrend:
    timestamp = datetime
    component = str
    compliance_score = float
    violations_count = int
    constitutional_sections = list[str]
    cks_integration_score = float

@dataclass_json
@dataclass
class PerformanceInsight:
    insight_id = str
    category = str
    severity = AlertSeverity
    title = str
    description = str
    current_metrics = dict[str, float]
    predicted_impact = str
    recommended_actions = list[str]
    estimated_improvement = dict[str, float]
    confidence_score = float
    timestamp = datetime
    applies_to = list[str]

class MetricsCollector:
    __init__(self, max_memory_points: int = 10000) -> None
    collect_metric(self, metric_point: MetricPoint) -> None
    get_real_time_metrics(self, component: str | None = None) -> dict[str, Any]
    get_metrics_for_time_range(self, start_time: datetime, end_time: datetime, component: str | None = None) -> list[MetricPoint]

class AlertManager:
    __init__(self) -> None
    add_alert_rule(self, rule_id: str, component: str, metric_name: str, condition: str, threshold: float, severity: AlertSeverity, title: str, description: str, recommended_actions: list[str] | None = None) -> None
    evaluate_alerts(self, metrics: list[MetricPoint]) -> list[Alert]
    acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool
    resolve_alert(self, alert_id: str, resolved_by: str) -> bool
    get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]
    get_alert_statistics(self) -> dict[str, Any]

class TrendAnalyzer:
    __init__(self) -> None
    analyze_trend(self, metric_points: list[MetricPoint], time_window_hours: int = 24) -> dict[str, Any]

class UserExperienceTracker:
    __init__(self) -> None
    start_session(self, session_id: str, user_id: str | None = None) -> None
    end_session(self, session_id: str, satisfaction_score: float | None = None) -> UserExperienceMetrics | None
    record_interaction(self, session_id: str, operation: str, success: bool, response_time_ms: float, feature: str | None = None, compliance_violation: bool = False) -> None
    get_user_experience_summary(self, time_window_hours: int = 24) -> dict[str, Any]

class CKSMonitoringAnalytics:
    __init__(self, data_dir: str = ".cks_monitoring") -> None
    start_monitoring(self) -> None
    stop_monitoring(self) -> None
    register_component_monitoring(self, component_name: str, metrics_callback: Callable[[], dict[str, float]], health_check: Callable[[], dict[str, Any]] | None = None) -> None
    collect_metric(self, metric_name: str, metric_type: MetricType, value: int | float | dict[str, Any], component: str, operation: str, user_id: str | None = None, session_id: str | None = None, tags: dict[str, str] | None = None, metadata: dict[str, Any] | None = None) -> None
    track_user_interaction(self, session_id: str, operation: str, success: bool, response_time_ms: float, user_id: str | None = None, feature: str | None = None, compliance_violation: bool = False) -> None
    end_user_session(self, session_id: str, satisfaction_score: float | None = None) -> UserExperienceMetrics | None
    get_real_time_dashboard(self) -> dict[str, Any]
    get_analytics_report(self, start_time: datetime, end_time: datetime, components: list[str] | None = None) -> dict[str, Any]
__all__ = [
    "Alert",
    "AlertManager",
    "AlertSeverity",
    "CKSMonitoringAnalytics",
    "ComplianceTrend",
    "MetricPoint",
    "MetricType",
    "MetricsCollector",
    "PerformanceInsight",
    "TimeGranularity",
    "TrendAnalyzer",
    "UserExperienceMetrics",
    "UserExperienceTracker",
]
```


### P:\packages\search-research\core\cks\integration\adapters\performance_optimizer.py

```python
import asyncio
import hashlib
import json
import logging
import os
import pickle
import threading
import time
from collections import OrderedDict, defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
import diskcache as dc
DISKCACHE_AVAILABLE = True
DISKCACHE_AVAILABLE = False
logger = logging.getLogger(__name__)
from ..constitutional_compliance.cwo12_cks_compliance_validator import (
        CWO12CKSConstitutionalValidator, CWO12WorkflowStep, )
from ..knowledge_system.cks_constitutional_validator import (
        CKSConstitutionalValidator, )
from ..orchestration.cks_agent_coordinator import CKSAgentCoordinator
from modules.constitutional_compliance.cwo12_cks_compliance_validator import (
        CWO12CKSConstitutionalValidator, CWO12WorkflowStep, )
from modules.knowledge_system.cks_constitutional_validator import (
        CKSConstitutionalValidator, )
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"
    L2_DISK = "l2_disk"
    L3_DISTRIBUTED = "l3_distributed"

class QueryType(Enum):
    SIMILARITY_SEARCH = "similarity_search"
    COMPLIANCE_VALIDATION = "compliance_validation"
    PATTERN_MATCHING = "pattern_matching"
    AGENT_RECOMMENDATION = "agent_recommendation"
    WORKFLOW_COORDINATION = "workflow_coordination"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"

@dataclass
class CacheEntry:
    key = str
    value = Any
    is_expired(self) -> bool
    update_access(self) -> None

@dataclass
class PerformanceMetrics:
    pass

class MemoryCache:
    __init__(self, max_size: int = 1000, max_memory_mb: int = 512) -> None
    get(self, key: str) -> CacheEntry | None
    put(self, key: str, entry: CacheEntry) -> bool
    clear(self) -> None
    get_stats(self) -> dict[str, Any]

class DiskCache:
    __init__(self, cache_dir: str, max_size_gb: int = 10) -> None
    get(self, key: str) -> CacheEntry | None
    put(self, key: str, entry: CacheEntry) -> bool
    clear(self) -> None
    get_stats(self) -> dict[str, Any]

class LoadBalancer:
    __init__(self, max_workers: int = 4) -> None
    submit_request(self, request_func: Callable, priority: int = 0) -> Any
    get_load_balance_stats(self) -> dict[str, Any]

class CKSPreformanceOptimizer:
    __init__(self, memory_cache_size: int = 1000, memory_cache_mb: int = 512, disk_cache_gb: int = 10, max_workers: int = 4) -> None
    get_cached_result(self, query_type: QueryType, query_data: dict[str, Any], cks_context: dict[str, Any] | None = None) -> Any | None
    cache_result(self, query_type: QueryType, query_data: dict[str, Any], result: Any, cks_context: dict[str, Any] | None = None, ttl_seconds: int = 3600) -> bool
    execute_with_optimization(self, query_type: QueryType, query_func: Callable, query_data: dict[str, Any], cks_context: dict[str, Any] | None = None, ttl_seconds: int = 3600) -> Any
    optimize_cks_query(self, query_type: QueryType, query_data: dict[str, Any], cks_validator: CKSConstitutionalValidator | None = None, cwo12_validator: CWO12CKSConstitutionalValidator | None = None) -> dict[str, Any]
    get_performance_statistics(self) -> dict[str, Any]
    clear_all_caches(self) -> dict[str, Any]
    start_background_optimization(self) -> None
    stop_background_optimization(self) -> None
__all__ = [
    "CKSPreformanceOptimizer",
    "CacheEntry",
    "CacheLevel",
    "DiskCache",
    "LoadBalancer",
    "MemoryCache",
    "PerformanceMetrics",
    "QueryType",
]
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\__init__.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\adapter.py

```python
import logging
from typing import TYPE_CHECKING, Any
from pathlib import Path
from .repositories.base_repository import RepositoryResult
from .repositories.checkpoint_repository import (
        CheckpointRepository, ContextCheckpoint, )
from .repositories.project_context_repository import (
        ProjectContext, ProjectContextRepository, )
from .validation.validators import (
        ValidationError, validate_tsk_id, validate_worktree_path, )
from repositories.base_repository import RepositoryResult
from repositories.checkpoint_repository import (
        CheckpointRepository, ContextCheckpoint, )
from repositories.project_context_repository import (
        ProjectContext, ProjectContextRepository, )
logger = logging.getLogger(__name__)

class ProjectContextCKSAdapter:
    __init__(self, db_path: str | Path) -> None
    create_context(self, tsk_id: str, worktree_path: str, description: str = "", metadata: dict[str, Any] | None = None) -> RepositoryResult
    get_context(self, tsk_id: str) -> ProjectContext | None
    get_active_context(self) -> ProjectContext | None
    set_active_context(self, tsk_id: str) -> RepositoryResult
    list_contexts(self) -> list[ProjectContext]
    update_context(self, tsk_id: str) -> RepositoryResult
    delete_context(self, tsk_id: str) -> RepositoryResult
    validate_operation(self, operation_type: str, operation_target: str = "", operation_description: str = "") -> tuple[bool, str]
    create_checkpoint(self, checkpoint_name: str, description: str = "", tsk_id: str | None = None, checkpoint_data: dict[str, Any] | None = None) -> RepositoryResult
    list_checkpoints(self, tsk_id: str | None = None, limit: int = 100) -> list[ContextCheckpoint]
    detect_context_from_path(self, file_path: str) -> str | None
    detect_context_from_operation(self, operation_type: str, description: str) -> str | None
    get_operation_log(self, tsk_id: str, limit: int = 100, offset: int = 0) -> list[Any]
    close(self) -> None
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\cks_client.py

```python
import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent.parent

@dataclass
class Entity:
    entity_type = str
    entity_id = str
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_row(cls, row: dict[str, Any]) -> Entity

@dataclass
class TaskEntity(Entity):
    __init__(self, name: str, status: str = "pending", progress_pct: int = 0, description: str = "", priority: str = "medium", strategic_context: dict[str, Any] | None = None) -> None

@dataclass
class SessionCheckpointEntity(Entity):
    __init__(self, task_name: str, session_id: str, progress_pct: int, blocker: dict[str, Any] | None = None, files_modified: list[str] | None = None, next_steps: list[str] | None = None, session_summary: str = "", terminal_id: str | None = None) -> None

@dataclass
class BlockerEntity(Entity):
    __init__(self, task_name: str, description: str, severity: str = "medium", investigation: str = "", workaround: str = "") -> None

@dataclass
class DecisionEntity(Entity):
    __init__(self, task_name: str, what: str, answer: str, reasoning: str, alternatives_considered: list[str] | None = None) -> None

class CKSHyperGraphClient:
    __init__(self, db_path: str | Path) -> None
    add_entity(self, entity: Entity) -> bool
    get_entity(self, entity_type: str, entity_id: str) -> Entity | None
    hyper_graph_query(self, entity_type: str | None = None, filter: dict[str, Any] | None = None, limit: int = 100) -> list[dict[str, Any]]
    semantic_search(self, query: str, entity_type: str | None = None, limit: int = 10) -> list[dict[str, Any]]
    get_related_entities(self, entity_id: str, relationship_type: str | None = None) -> list[dict[str, Any]]
    delete_entity(self, entity_type: str, entity_id: str) -> bool
    update_entity_attributes(self, entity_type: str, entity_id: str, attributes: dict[str, Any]) -> bool
    get_supported_entity_types(self) -> list[str]
    store_lesson_learned(self, trigger_phrase: str, context: str, what_to_do: str, severity: str = "medium", category: str = "general") -> bool
    get_lesson_by_trigger(self, trigger_phrase: str) -> dict[str, Any] | None
    get_all_lessons_learned(self) -> list[dict[str, Any]]
    find_lessons_by_trigger_fuzzy(self, trigger_phrase: str) -> list[dict[str, Any]]
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
create_task_entity(name: str, status: str = "pending", progress_pct: int = 0, description: str = "", priority: str = "medium", strategic_context: dict[str, Any] | None = None) -> TaskEntity
create_checkpoint_entity(task_name: str, session_id: str, progress_pct: int, blocker: dict[str, Any] | None = None, files_modified: list[str] | None = None, next_steps: list[str] | None = None, session_summary: str = "", terminal_id: str | None = None) -> SessionCheckpointEntity
client = CKSHyperGraphClient(
        "P:/__csf/src/features/cks/integration/adapters/project_context/test_cks.db"
    )
task = create_task_entity(
        name="CWO12",
        status="in_progress",
        progress_pct=35,
        description="Alternative Platform Support",
        priority="high",
        strategic_context={
            "goal": "Enable Claude Code on alternative platforms",
            "success_criteria": ["MacOS ARM64", "WSL2", "Linux"],
            "approach": "Abstract platform detection",
        },
    )
tasks = client.hyper_graph_query(
        entity_type="Task",
        filter={"status": "in_progress"},
    )
checkpoint = create_checkpoint_entity(
        task_name="CWO12",
        session_id="session_12345",
        progress_pct=35,
        blocker={
            "description": "AsyncBridge integration incomplete",
            "severity": "high",
        },
        next_steps=["Complete AsyncBridge", "Test on MacOS", "Update docs"],
    )
related = client.get_related_entities(checkpoint.entity_id, "belongs_to_task")
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\context_manager_cks.py

```python
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
current_dir = Path(__file__).parent
from ...unified import CKS

@dataclass
class ProjectContext:
    tsk_id = str
    name = str
    base_repository = str
    focus = str
    worktree_path = str
    last_activity = float
    session_id = str

class SessionContextManagerCKS:
    __init__(self, cks_db_path: str | None = None, memory_base: str = ".speckit/memory") -> None
    detect_active_tsk_projects(self) -> list[dict]
    get_worktree_context(self) -> str | None
    set_active_context(self, tsk_id: str, force: bool = False) -> bool
    validate_current_operation(self, operation_description: str = "") -> tuple[bool, str | None]
    pre_operation_check(self, operation_description: str) -> bool
    get_context_summary(self) -> str
    clear_context(self) -> None
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\migrate_to_cks.py

```python
import json
import sqlite3
import sys
from pathlib import Path
current_dir = Path(__file__).parent
from csf.cks_client import (
    CKSHyperGraphClient, create_checkpoint_entity, create_task_entity, )

class MigrationToCKS:
    __init__(self, source_db: str | Path = "P:/.cks/storage/cks.db", target_db: str | Path = "P:/__csf/data/cks.db") -> None
    migrate_tasks(self) -> int
    migrate_session_checkpoints(self) -> int
    migrate_project_contexts(self) -> int
    run(self)
main() -> int
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\task_identity_manager.py

```python
import hashlib
import json
import logging
import os
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypeAlias
from cli.subprocess_helper import run_subprocess
terminal_detection_path = (
    Path(__file__).parent.parent.parent.parent / ".claude" / "hooks" / "terminal_detection.py"
)
import sys
from terminal_detection import detect_terminal_id
detect_terminal_id() -> str
logger = logging.getLogger(__name__)

@dataclass(slots=True)
class TaskMetadata:
    task_name = str
    task_id = str
    started = str
    checksum = str
    source = str

class TaskIdentityManager:
    __init__(self, project_root: Path | None = None, terminal_id: str | None = None) -> None
    get_current_task(self) -> str | None
    set_current_task(self, task_name: str) -> bool
    store_compact_metadata(self, task_name: str, checkpoint_id: str) -> bool
    register_task_worktree_mapping(self, task_name: str, branch: str) -> bool
    cleanup_stale_terminal_files(self, max_age_hours: int = 24) -> int
manager = TaskIdentityManager()
task = manager.get_current_task()
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\validation\__init__.py

```python
import sys
from pathlib import Path
from validators import (
    ValidationError, detect_context_from_operation, detect_context_from_path, validate_checkpoint_name, validate_description, validate_metadata, validate_operation_description, validate_operation_target, validate_operation_type, validate_tsk_id, validate_worktree_path, )
__all__ = [
    "ValidationError",
    "detect_context_from_operation",
    "detect_context_from_path",
    "validate_checkpoint_name",
    "validate_description",
    "validate_metadata",
    "validate_operation_description",
    "validate_operation_target",
    "validate_operation_type",
    "validate_tsk_id",
    "validate_worktree_path",
]
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\validation\config.py

```python
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ValidationConfig:
    @classmethod
    from_env(cls) -> ValidationConfig
    @classmethod
    from_file(cls, config_path: Path | None = None) -> ValidationConfig
    to_file(self, config_path: Path | None = None) -> None
get_config() -> ValidationConfig
set_config(config: ValidationConfig) -> None
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\validation\config_cli.py

```python
from pathlib import Path
parent = Path(__file__).parent
from features.config import get_config, set_config
cmd_show(args) -> None
cmd_enable_blocking(args) -> None
cmd_disable_blocking(args) -> None
cmd_enable_auto(args) -> None
cmd_disable_auto(args) -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\adapters\project_context\validation\validators.py

```python
import logging
import re
from dataclasses import dataclass
from pathlib import Path
logger = logging.getLogger(__name__)

@dataclass
class ValidationError(Exception):
    message = str
validate_tsk_id(tsk_id: str) -> str
validate_worktree_path(worktree_path: str) -> str
validate_checkpoint_name(checkpoint_name: str) -> str
validate_operation_type(operation_type: str) -> str
validate_operation_description(description: str) -> str
validate_operation_target(target: str) -> str
validate_description(description: str | None) -> str | None
validate_metadata(metadata: dict | None) -> str | None
detect_context_from_path(file_path: str) -> str | None
detect_context_from_operation(operation_type: str, description: str) -> str | None
```


### P:\packages\search-research\core\cks\integration\adapters\rag_integration_coordinator.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\resilience_error_handler.py

```python
import asyncio
import logging
import random
import threading
import time
import traceback
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from ..constitutional_compliance.cwo12_cks_compliance_validator import (
        CWO12CKSConstitutionalValidator, )
from ..knowledge_system.cks_constitutional_validator import CKSConstitutionalValidator
from ..orchestration.cks_agent_coordinator import CKSAgentCoordinator
from ..performance.cks_performance_optimizer import CKSPreformanceOptimizer
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"

class FallbackStrategy(Enum):
    DEGRADED_FUNCTIONALITY = "degraded_functionality"
    ALTERNATIVE_SERVICE = "alternative_service"
    CACHED_RESPONSE = "cached_response"
    DEFAULT_RESPONSE = "default_response"
    SILENT_FAILURE = "silent_failure"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class ErrorContext:
    error_id = str
    error_type = str
    severity = ErrorSeverity
    category = ErrorCategory
    message = str
    exception = Exception | None
    timestamp = datetime
    operation = str
    component = str

@dataclass
class FallbackConfig:
    strategy = FallbackStrategy
    activation_threshold = int
    timeout_ms = int
    max_retries = int
    backoff_base_ms = int
    backoff_max_ms = int
    jitter_ms = int
    degraded_functionality_level = float

@dataclass
class ResilienceMetrics:
    pass

class CircuitBreaker:
    __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60, half_open_max_calls: int = 3) -> None
    call(self, func: Callable) -> Any
    get_state(self) -> dict[str, Any]

class RetryHandler:
    __init__(self, max_retries: int = 3, base_delay_ms: int = 100, max_delay_ms: int = 5000, jitter_ms: int = 100, backoff_multiplier: float = 2.0) -> None
    execute_with_retry(self, func: Callable, retry_on: tuple[type, ...] | None = None) -> Any
    get_retry_statistics(self) -> dict[str, Any]

class HealthMonitor:
    __init__(self, check_interval_seconds: int = 30) -> None
    register_component(self, component_name: str, health_check: Callable[[], dict[str, Any]]) -> None
    start_monitoring(self) -> None
    stop_monitoring(self) -> None
    get_system_health(self) -> dict[str, Any]
    is_component_healthy(self, component_name: str) -> bool

class CKSFallbackErrorHandler:
    __init__(self) -> None
    register_component_resilience(self, component_name: str, config: FallbackConfig | None = None) -> None
    execute_with_resilience(self, component_name: str, operation: str, func: Callable) -> Any
    get_resilience_statistics(self) -> dict[str, Any]
    start_resilience_monitoring(self) -> None
    stop_resilience_monitoring(self) -> None
    register_component_health_check(self, component_name: str, health_check_func: Callable[[], dict[str, Any]]) -> None
    is_system_healthy(self) -> bool
    get_component_circuit_breaker_state(self, component_name: str) -> dict[str, Any] | None
__all__ = [
    "CKSFallbackErrorHandler",
    "CircuitBreaker",
    "CircuitBreakerState",
    "ErrorCategory",
    "ErrorContext",
    "ErrorSeverity",
    "FallbackConfig",
    "FallbackStrategy",
    "HealthMonitor",
    "ResilienceMetrics",
    "RetryHandler",
]
```


### P:\packages\search-research\core\cks\integration\adapters\session_integration_coordinator.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\adapters\task_management_integration.py

```python
import asyncio
import logging
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from .cwo12_task_manager import CWO12Task

class CKSOptimizationType(Enum):
    TASK_DECOMPOSITION = "task_decomposition"
    DEPENDENCY_OPTIMIZATION = "dependency_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    QUALITY_ENHANCEMENT = "quality_enhancement"
    RISK_MITIGATION = "risk_mitigation"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    PATTERN_RECOGNITION = "pattern_recognition"

class CKSIntegrationLevel(Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    ADVANCED = "advanced"
    AUTONOMOUS = "autonomous"

@dataclass
class CKSOptimization:
    id = str
    optimization_type = CKSOptimizationType
    target_task_ids = list[str]
    description = str
    recommendation = str
    expected_improvement = dict[str, float]
    confidence_score = float

@dataclass
class CKSKnowledgeQuery:
    id = str
    query_type = str
    query_text = str
    context = dict[str, Any]

@dataclass
class CKSKnowledgeResult:
    query_id = str
    knowledge_items = list[dict[str, Any]]
    confidence_scores = list[float]
    relevance_scores = list[float]
    processing_time_ms = float

@dataclass
class CKSPatternMatch:
    id = str
    pattern_type = str
    matched_tasks = list[str]
    pattern_description = str
    similarity_score = float

class CKSTaskOptimizer:
    __init__(self, task_manager, cks_engine, log_level: int = logging.INFO) -> None
    optimize_task_with_cks(self, task_id: str, optimization_types: list[CKSOptimizationType] | None = None, integration_level: CKSIntegrationLevel | None = None) -> list[CKSOptimization]
    query_cks_knowledge(self, query_text: str, query_type: str = "search", context: dict[str, Any] | None = None, filters: dict[str, Any] | None = None) -> CKSKnowledgeResult
    recognize_patterns(self, task_ids: list[str] | None = None, pattern_types: list[str] | None = None) -> list[CKSPatternMatch]
    apply_optimization(self, optimization_id: str, application_context: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]
    learn_from_execution(self, task_id: str, execution_results: dict[str, Any], feedback: dict[str, Any] | None = None) -> None
    get_optimization_recommendations(self, task_ids: list[str] | None = None, optimization_types: list[CKSOptimizationType] | None = None, min_confidence: float = 0.7) -> list[CKSOptimization]
    generate_cks_report(self) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\integration\cks_integration_module.py

```python
import json
import logging
import statistics
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from ..core.pytorch_vector_storage import DeviceManager, PyTorchStorageConfig
from ..core.storage_manager import StorageConfig, StorageManager
from .session_memory_adapter import SessionMemoryAdapter
CKS_COMPONENTS_AVAILABLE = True
CKS_COMPONENTS_AVAILABLE = False
SessionMemoryAdapter = None
StorageManager = None
StorageConfig = None
PyTorchStorageConfig = None
DeviceManager = None
from ..integration.integration_manager import CKSIntegrationManager
from ..integration.interfaces.base_adapter import CKSContext, IntegrationResult
INTEGRATION_MANAGER_AVAILABLE = True
INTEGRATION_MANAGER_AVAILABLE = False
CKSIntegrationManager = None
IntegrationResult = None
CKSContext = None
logger = logging.getLogger(__name__)

class IndexingStrategy(Enum):
    BASIC = "basic"
    SESSION_AWARE = "session_aware"
    CROSS_SESSION = "cross_session"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"

class OptimizationLevel(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"

class CorrelationMethod(Enum):
    COSINE_SIMILARITY = "cosine_similarity"
    SEMANTIC_OVERLAP = "semantic_overlap"
    TEMPORAL_PROXIMITY = "temporal_proximity"
    PATTERN_MATCHING = "pattern_matching"
    HYBRID = "hybrid"

@dataclass
class SessionIndexingConfig:
    session_id = str

@dataclass
class CorrelationConfig:
    pass

@dataclass
class OptimizationMetrics:
    storage_reduction_percent = float
    indexing_speedup_percent = float
    query_latency_reduction_ms = float
    memory_efficiency_percent = float
    optimization_time_seconds = float

@dataclass
class CorrelationResult:
    session_id = str
    correlated_sessions = list[dict[str, Any]]
    similarity_scores = dict[str, float]
    correlation_strength = float
    correlation_metadata = dict[str, Any]
    processing_time_ms = float

@dataclass
class PerformanceMetrics:
    operation = str
    execution_time_ms = float
    success = bool
    memory_used_mb = float
    vectors_processed = int
    cache_hit_rate = float

class CKSIntegrationModule:
    __init__(self, session_memory_adapter: SessionMemoryAdapter | None = None, storage_manager: StorageManager | None = None, integration_manager: CKSIntegrationManager | None = None, cache_size_mb: int = 100, enable_advanced_features: bool = True, config_path: str | None = None) -> None
    validate_cks_session(self, session_id: str) -> bool
    get_ks_vector_store(self) -> Any | None
    register_session_with_cks(self, session_id: str, metadata: dict) -> bool
    perform_ks_indexing(self, session_id: str, content: dict) -> bool
    optimize_vector_store_for_sessions(self, vector_store: Any) -> OptimizationMetrics
    create_optimized_index_schema(self) -> dict
    implement_session_specific_indexing(self) -> bool
    configure_vector_store_for_performance(self, vector_store: Any) -> dict
    create_session_memory_index(self, session_id: str) -> bool
    manage_cross_session_correlation(self) -> dict
    implement_session_isolation(self) -> bool
    handle_session_data_consistency(self, session_id: str) -> bool
    find_related_sessions(self, session_id: str) -> list[str]
    calculate_session_similarity(self, session1: str, session2: str) -> float
    build_session_correlation_graph(self) -> dict
    maintain_correlation_metadata(self) -> bool
    get_performance_metrics(self) -> dict[str, Any]
    clear_caches(self, cache_type: str | None = None) -> bool
__all__ = [
    "CKSIntegrationModule",
    "CorrelationConfig",
    "CorrelationMethod",
    "CorrelationResult",
    "IndexingStrategy",
    "OptimizationLevel",
    "OptimizationMetrics",
    "PerformanceMetrics",
    "SessionIndexingConfig",
]
```


### P:\packages\search-research\core\cks\integration\clients\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\clients\chat_history_client.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\clients\chat_history_client_instrumented.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\clients\example_session_aware_usage.py

```python
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from chat_history_client import (
    ChatHistoryClient, ChatMessage, IntegrationConfig, MessageRole, SecurityLevel, )

class SessionAwareDemo:
    __init__(self) -> None
    setup_client(self) -> None
    create_debugging_session(self) -> dict[str, Any]
    create_architecture_session(self) -> dict[str, Any]
    create_learning_session(self) -> dict[str, Any]
    demonstrate_session_indexing(self) -> None
    demonstrate_cross_session_queries(self) -> None
    demonstrate_pattern_preservation(self) -> None
    demonstrate_relevance_analysis(self) -> None
    demonstrate_performance_monitoring(self) -> None
    demonstrate_session_management(self) -> None
    cleanup(self) -> None
    run_demo(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\clients\hdma_client.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\clients\serena_client.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\clients\test_session_aware_chat_history_client.py

```python
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import pytest
from ..exceptions.integration_exceptions import ValidationException
from .chat_history_client import (
    ChatHistoryClient, ChatMessage, IntegrationConfig, MessageRole, SecurityLevel, SessionContext, SessionContextType, SessionPattern, )

class TestSessionAwareChatHistoryClient:
    @pytest.fixture
    integration_config(self)
    @pytest.fixture
    sample_messages(self)
    @pytest.fixture
    sample_context_data(self, sample_messages)
    @pytest.fixture
    chat_client(self, integration_config)
    @pytest.mark.asyncio
    test_session_context_indexing_success(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_session_context_indexing_validation(self, chat_client) -> None
    @pytest.mark.asyncio
    test_cross_session_context_query(self, chat_client, sample_messages) -> None
    @pytest.mark.asyncio
    test_cross_session_context_query_disabled(self, chat_client) -> None
    @pytest.mark.asyncio
    test_create_session_memory_index(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_preserve_conversation_patterns(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_analyze_session_relevance(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_analyze_session_relevance_no_context(self, chat_client) -> None
    @pytest.mark.asyncio
    test_message_embedding_generation(self, chat_client, sample_messages) -> None
    @pytest.mark.asyncio
    test_text_embedding_generation(self, chat_client) -> None
    test_cosine_similarity_calculation(self, chat_client) -> None
    test_session_checksum_calculation(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_fallback_embedding_storage(self, chat_client, sample_messages) -> None
    @pytest.mark.asyncio
    test_session_aware_components_initialization(self, integration_config) -> None
    @pytest.mark.asyncio
    test_performance_target_context_indexing(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_performance_target_cross_session_query(self, chat_client, sample_context_data) -> None
    @pytest.mark.asyncio
    test_cleanup_session_aware_components(self, chat_client) -> None
    @pytest.mark.asyncio
    test_session_awareness_disabled(self, integration_config) -> None
    @pytest.mark.asyncio
    test_error_handling_in_session_operations(self, chat_client) -> None
    @pytest.mark.asyncio
    test_integration_with_session_memory_bridge(self, chat_client, sample_context_data) -> None
```


### P:\packages\search-research\core\cks\integration\clients\web_content_client.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\commands\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\commands\cache_knowledge_simple.py

```python
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)

class SimpleCacheKnowledgeIntegrator:
    __init__(self) -> None
    integrate_all_findings(self) -> dict[str, Any]
    save_knowledge_base(self, output_path: str | None = None) -> str
main() -> int | None
import asyncio
```


### P:\packages\search-research\core\cks\integration\commands\cache_research_knowledge_integration.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\commands\cks_knowledge_integration.py

```python
import asyncio
import hashlib
import json
import logging
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import aiofiles
import requests
from bs4 import BeautifulSoup
from .co.learn_spec_2025 import CKSConfig, KnowledgeEntry, KnowledgeManager, QueryRequest
CKS_AVAILABLE = True
CKS_AVAILABLE = False
KnowledgeEntry = None
QueryRequest = None
CKSConfig = None
KnowledgeManager = None
logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    WEBSITE = "website"
    FLAT_FILE = "flat_file"
    CONVERSATION = "conversation"
    DIRECT_TEXT = "direct_text"
    CODE_SNIPPET = "code_snippet"
    COMMAND_OUTPUT = "command_output"
    ERROR_LOG = "error_log"
    DOCUMENTATION = "documentation"

class ProcessingResult:
    __init__(self, success: bool, message: str, data: dict[str, Any] | None = None) -> None

@dataclass
class KnowledgeContext:
    source_type = KnowledgeType
    source_identifier = str
    original_input = str
    processed_content = str
    metadata = dict[str, Any]
    relationships = list[str]
    tags = list[str]

class ContextDetector:
    __init__(self) -> None
    detect_type(self, content: str) -> tuple[KnowledgeType, float]

class ContentProcessor:
    __init__(self) -> None
    process_website(self, url_or_content: str) -> ProcessingResult
    process_flat_file(self, file_path: str) -> ProcessingResult
    process_conversation(self, conversation: str) -> ProcessingResult
    process_direct_text(self, text: str) -> ProcessingResult

class CKSKnowledgeIntegration:
    __init__(self, config: CKSConfig = None) -> None
    ingest_knowledge(self, input_data: str, category: str | None = None, title: str | None = None, user_context: str | None = None) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\compact_skills.py

```python
import re
from pathlib import Path
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
compact_testing_skills() -> None
compact_sharing_skills() -> None
compact_writing_skills() -> None
compact_session_handoff() -> None
compact_architecture_decision_framework() -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\direct_knowledge_ingestion.py

```python
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
DB_PATH = DATA_DIR / "cks_hypergraph.db"

class DirectCKSIngestion:
    __init__(self) -> None
    initialize_database(self) -> bool
    generate_entry_id(self, title: str, category: str) -> str
    ingest_knowledge(self, title: str, content: str, category: str, knowledge_type: str = "implementation", metadata: dict[str, Any] | None = None, tags: list | None = None) -> dict[str, Any]
    search_knowledge(self, query: str, limit: int = 5) -> list
    get_statistics(self) -> dict
    close(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\ml_integration_knowledge_ingestion.py

```python
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from .cks_knowledge_integration import (
    CKSKnowledgeIntegration, )
logger = logging.getLogger(__name__)

class MLKnowledgeCategory(Enum):
    ML_INFRASTRUCTURE = "ml_infrastructure"
    GPU_ACCELERATION = "gpu_acceleration"
    VECTOR_MANAGEMENT = "vector_management"
    EMBEDDING_SYSTEMS = "embedding_systems"
    CODEBERT_INTEGRATION = "codebert_integration"
    HYBRID_ANALYSIS = "hybrid_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ACCURACY_ENHANCEMENT = "accuracy_enhancement"
    ARCHITECTURE_PATTERNS = "architecture_patterns"
    RISK_MITIGATION = "risk_mitigation"
    VALIDATION_FRAMEWORKS = "validation_frameworks"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    EXPLORE_COMMAND = "explore_command"
    DEAD_CODE_DETECTION = "dead_code_detection"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    IMPLEMENTATION_EVIDENCE = "implementation_evidence"
    PERFORMANCE_BENCHMARKS = "performance_benchmarks"
    FEASIBILITY_ANALYSIS = "feasibility_analysis"

@dataclass
class MLResearchFinding:
    title = str
    category = MLKnowledgeCategory
    confidence_level = float
    evidence_sources = list[str]
    key_insights = list[str]
    implementation_impact = str
    priority_level = str
    dependencies = list[str]
    risks = list[str]
    timeline_estimate = str
    code_patterns = list[str]

class MLKnowledgeProcessor:
    __init__(self) -> None
    ingest_step3_research_findings(self) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\ml_knowledge_retrieval_system.py

```python
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent.parent
from ...core.vector_manager import VectorConfig, VectorKnowledgeManager
VECTOR_MANAGER_AVAILABLE = True
VECTOR_MANAGER_AVAILABLE = False
logger = logging.getLogger(__name__)

class RetrievalMode(Enum):
    SEMANTIC_SEARCH = "semantic_search"
    EXACT_MATCH = "exact_match"
    CATEGORY_FILTER = "category_filter"
    PRIORITY_FILTER = "priority_filter"
    CONFIDENCE_FILTER = "confidence_filter"
    IMPLEMENTATION_TIMELINE = "implementation_timeline"
    EVIDENCE_BASED = "evidence_based"

@dataclass
class SemanticRelationship:
    source_concept = str
    target_concept = str
    relationship_type = str
    strength = float
    evidence = list[str]
    implementation_impact = str

class MLKnowledgeRetrievalSystem:
    __init__(self) -> None
    build_semantic_relationships(self) -> dict[str, Any]
    synthesize_knowledge(self, query_context: str | None = None) -> dict[str, Any]
    organize_and_index_knowledge(self) -> dict[str, Any]
    create_evidence_based_enhancement(self) -> dict[str, Any]
    retrieve_knowledge(self, query: str, mode: RetrievalMode = RetrievalMode.SEMANTIC_SEARCH, filters: dict[str, Any] | None = None, limit: int = 10) -> dict[str, Any]
    generate_knowledge_retrieval_patterns(self) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\neural_cache_migration.py

```python
import hashlib
import json
import logging
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
logger = logging.getLogger(__name__)

class EntryType(Enum):
    FIX = "FIX"
    PATTERN = "PATTERN"
    SUCCESS = "SUCCESS"
    INSIGHT = "INSIGHT"
    ANTIPATTERN = "ANTIPATTERN"
    PRACTICE = "PRACTICE"
    UX = "UX"
    PERF = "PERF"
    ARCH = "ARCH"
    DISPLAY = "DISPLAY"
    BUG = "BUG"
    DOCS = "DOCS"
    LESSON = "LESSON"
    @classmethod
    from_string(cls, value: str) -> "EntryType | None"

@dataclass
class NeuralCacheEntry:
    entry_type = str
    date = str
    topic = str
    description = str
    file_reference = str | None
    original_line = str

@dataclass
class MigrationStats:
    total_entries = int
    entries_by_type = dict[str, int]
    entries_with_file_refs = int
    date_range = tuple[str, str]

@dataclass
class MigrationResult:
    success = bool

class NeuralCacheParser:
    ENTRY_PATTERN = re.compile(
        r"^-\s*\[([A-Z]+)\s+(\d{4}-\d{2}-\d{2})\]\s+\*\*([^*]+)\*\*:\s*(.+?)(?:\s*-\s*([^\s]+(?:\:\d+(?:-\d+)?)?))?$",
    )
    __init__(self, skill_file: str | Path) -> None
    parse(self) -> list[NeuralCacheEntry]
    get_stats(self) -> MigrationStats

class NeuralCacheMigrator:
    DB_PATH = PROJECT_ROOT / "__csf" / "data" / "cks.db"
    CATEGORY_MAPPING = {
        "FIX": "bug_fix",
        "PATTERN": "design_pattern",
        "SUCCESS": "success_case",
        "INSIGHT": "insight",
        "ANTIPATTERN": "anti_pattern",
        "PRACTICE": "best_practice",
        "UX": "user_experience",
        "PERF": "performance",
        "ARCH": "architecture",
        "DISPLAY": "display",
        "BUG": "bug_report",
        "DOCS": "documentation",
        "LESSON": "lesson_learned",
    }
    __init__(self, db_path: Path | None = None) -> None
    ingest_entries(self, entries: list[NeuralCacheEntry], dry_run: bool = False) -> MigrationResult
    migrate_from_skill_file(self, skill_file: Path, dry_run: bool = False) -> MigrationResult
    get_db_stats(self) -> dict[str, Any]
    close(self) -> None
print_stats(stats: dict[str, Any]) -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\nse_task_awareness_knowledge_ingestion.py

```python
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/cks_hypergraph"
NSE_DOCS_DIR = PROJECT_ROOT / "docs/nse_task_awareness"
NSE_MEMORY_DIR = PROJECT_ROOT / ".speckit/memory/TSK-121720-NSETaskAwareness-1725"
DB_PATH = DATA_DIR / "cks_hypergraph.db"

class NSETaskAwarenessKnowledgeIntegrator:
    __init__(self) -> None
    initialize_database(self) -> bool
    generate_node_id(self, title: str, category: str) -> str
    ingest_nse_documentation(self) -> dict[str, Any]
    search_nse_knowledge(self, query: str, limit: int = 10) -> list[dict]
    get_nse_statistics(self) -> dict
    close(self) -> None
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\real_cks_integration.py

```python
import asyncio
import hashlib
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent
from co.learn_spec_2025 import CKSConfig, KnowledgeEntry, KnowledgeManager
REAL_CKS_AVAILABLE = True
REAL_CKS_AVAILABLE = False
KnowledgeManager = None
KnowledgeEntry = None
CKSConfig = None
from simple_cks_test import ContextDetector, KnowledgeType
ContextDetector = None
KnowledgeType = None

@dataclass
class CKSIntegrationResult:
    success = bool

class RealCKSIntegration:
    __init__(self) -> None
    ingest_knowledge(self, input_data: str, category: str | None = None, title: str | None = None, user_context: str | None = None) -> CKSIntegrationResult
    get_cks_status(self) -> dict[str, Any]
test_real_cks_integration()
```


### P:\packages\search-research\core\cks\integration\commands\refactoring_template_library_storage.py

```python
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from .cks_knowledge_integration import (
    CKSKnowledgeIntegration, )
logger = logging.getLogger(__name__)

class RefactoringTemplateCategory(Enum):
    PRODUCTION_PROVEN = "production_proven"
    SOLO_DEV_OPTIMIZED = "solo_dev_optimized"
    PROTOCOL_BASED = "protocol_based_design"
    SEPARATION_OF_CONCERNS = "separation_of_concerns"
    OUTPUT_FORMATTER = "output_formatter_pattern"
    WORKFLOW_EXECUTION = "workflow_execution_pattern"
    DATA_EXTRACTION = "data_extraction_pattern"
    VALIDATION_PROCESSOR = "validation_processor_pattern"
    MESSAGE_FORMATTER = "message_formatter_pattern"
    API_CLIENT_PATTERN = "api_client_pattern"
    IMPLEMENTATION_GUIDE = "implementation_guide"
    SUCCESS_METRICS = "success_metrics"
    USAGE_EXAMPLES = "usage_examples"
    SELECTION_CRITERIA = "selection_criteria"

@dataclass
class RefactoringTemplate:
    name = str
    category = RefactoringTemplateCategory
    description = str
    success_metrics = dict[str, Any]
    evidence_sources = list[str]
    implementation_code = str
    test_coverage = float
    performance_metrics = dict[str, float]
    usage_count = int
    complexity_level = str
    dependencies = list[str]
    benefits = list[str]
    implementation_time = str
    solo_dev_optimized = bool

class RefactoringTemplateKnowledgeProcessor:
    __init__(self) -> None
    store_refactoring_template_library(self) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\simple_cks_test.py

```python
import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    WEBSITE = "website"
    FLAT_FILE = "flat_file"
    CONVERSATION = "conversation"
    DIRECT_TEXT = "direct_text"

@dataclass
class SimpleKnowledgeEntry:
    id = str
    title = str
    content = str
    knowledge_type = str
    category = str
    timestamp = str
    tags = list[str]
    metadata = dict[str, Any]

class ContextDetector:
    __init__(self) -> None
    detect_type(self, content: str) -> tuple[KnowledgeType, float]

class SimpleCKSProcessor:
    __init__(self) -> None
    ingest_knowledge(self, input_data: str, category: str | None = None, title: str | None = None, user_context: str | None = None) -> dict[str, Any]
test_cks_integration() -> None
```


### P:\packages\search-research\core\cks\integration\commands\simplified_ml_knowledge_ingestion.py

```python
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent.parent
from ...core.vector_manager import VectorConfig, VectorKnowledgeManager
VECTOR_MANAGER_AVAILABLE = True
VECTOR_MANAGER_AVAILABLE = False
logger = logging.getLogger(__name__)

class SimplifiedMLKnowledgeIngestion:
    __init__(self) -> None
    ingest_ml_knowledge(self) -> dict[str, Any]
    search_ml_knowledge(self, query: str, limit: int = 5) -> list[dict]
main() -> None
```


### P:\packages\search-research\core\cks\integration\commands\skill_migration.py

```python
import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
CKS_DB_PATH = PROJECT_ROOT / "__csf" / "data" / "cks.db"

class SectionType(Enum):
    FRONTMATTER = "frontmatter"
    RESPONSE_FORMAT = "response_format"
    OBJECTIVE = "objective"
    ACTIVATION = "activation"
    ROLE = "role"
    PROTOCOL = "protocol"
    TEMPLATE = "template"
    CHECKLIST = "checklist"
    EXAMPLE = "example"
    PATTERN = "pattern"
    INTEGRATION = "integration"
    NEURAL_CACHE = "neural_cache"
    METADATA = "metadata"
    OTHER = "other"

@dataclass
class SkillSection:
    title = str
    content = str
    section_type = SectionType

@dataclass
class MigrationStats:
    pass

@dataclass
class SkillConfig:
    name = str
    path = Path
    @classmethod
    for_skill(cls, skill_name: str, skills_dir: Path) -> "SkillConfig"

class SkillParser:
    __init__(self, skill_path: Path) -> None
    parse(self) -> list[SkillSection]
    get_stats(self) -> dict

class SkillMigrator:
    __init__(self, db_path: Path | None = None, dry_run: bool = False) -> None
    ingest_section(self, skill_name: str, section: SkillSection, config: SkillConfig) -> bool
    migrate_skill(self, config: SkillConfig) -> MigrationStats
    compact_skill(self, config: SkillConfig) -> bool
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
list_skills(skills_dir: Path) -> None
main() -> int
```


### P:\packages\search-research\core\cks\integration\examples\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\examples\usage_examples.py

```python
from pathlib import Path
from ...integration import IntegrationType, cks_integration_manager
project_root = Path(__file__).resolve().parent.parent.parent.parent
example_constitutional_compliance() -> None
example_monitoring() -> None
example_orchestration() -> None
example_system_metrics() -> None
example_factory_usage() -> None
MIGRATION_TEMPLATE() -> None
```


### P:\packages\search-research\core\cks\integration\exceptions\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\exceptions\integration_exceptions.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    CONSTITUTIONAL = "constitutional"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    integration_source = str
    operation_name = str

class IntegrationException(Exception):
    __init__(self, message: str, context: ErrorContext, severity: ErrorSeverity = ErrorSeverity.MEDIUM, category: ErrorCategory = ErrorCategory.UNKNOWN, original_exception: Exception | None = None, error_code: str | None = None) -> None
    __str__(self) -> str
    to_dict(self) -> dict[str, Any]

class AuthenticationException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, original_exception: Exception | None = None, error_code: str | None = None) -> None

class AuthorizationException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, required_permission: str | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class NetworkException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, endpoint: str | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class TimeoutException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, timeout_seconds: float | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class RateLimitException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, limit: int | None = None, window_seconds: int | None = None, retry_after_seconds: int | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class ValidationException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, validation_errors: list[str] | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class ConfigurationException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, configuration_errors: list[str] | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class SecurityException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, security_policy: str | None = None, threat_level: str | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class ConstitutionalException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, violated_articles: list[str] | None = None, constitutional_score: float | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None

class DependencyException(IntegrationException):
    __init__(self, message: str, context: ErrorContext, dependency_name: str | None = None, required_version: str | None = None, current_version: str | None = None, original_exception: Exception | None = None, error_code: str | None = None) -> None
create_authentication_error(message: str, integration_source: str, operation_name: str, original_exception: Exception | None = None) -> AuthenticationException
create_rate_limit_error(message: str, integration_source: str, operation_name: str, limit: int, retry_after_seconds: int) -> RateLimitException
create_constitutional_violation(message: str, integration_source: str, operation_name: str, violated_articles: list[str], constitutional_score: float) -> ConstitutionalException
```


### P:\packages\search-research\core\cks\integration\integration_manager.py

```python
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4
from .adapter_factory import cks_adapter_factory
from .interfaces.base_adapter import CKSContext, IntegrationResult, IntegrationType
logger = logging.getLogger(__name__)

@dataclass
class OperationMetrics:
    operation_id = str
    integration_type = str
    start_time = datetime

@dataclass
class SystemMetrics:
    pass

class CKSIntegrationManager:
    __init__(self) -> None
    initialize_all_integrations(self, configs: dict[IntegrationType, dict[str, Any]] | None = None) -> IntegrationResult
    create_context(self, integration_type: IntegrationType, operation_id: str, metadata: dict[str, Any] | None = None) -> CKSContext
    process_with_integration(self, integration_type: IntegrationType, operation_data: dict[str, Any], config: dict[str, Any] | None = None) -> IntegrationResult
    get_system_metrics(self) -> dict[str, Any]
    get_active_operations(self) -> list[dict[str, Any]]
    list_available_integrations(self) -> list[str]
    shutdown(self) -> None
cks_integration_manager = CKSIntegrationManager()
```


### P:\packages\search-research\core\cks\integration\interfaces\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\interfaces\base_adapter.py

```python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    ORCHESTRATION = "orchestration"
    MONITORING = "monitoring"
    PERFORMANCE = "performance"
    TASK_MANAGEMENT = "task_management"
    KNOWLEDGE_SYSTEM = "knowledge_system"
    RESILIENCE = "resilience"
    UNIVERSAL_INSTRUMENTATION = "universal_instrumentation"
    AGENT_COORDINATION = "agent_coordination"
    ERROR_RECOVERY = "error_recovery"
    KNOWLEDGE_VALIDATION = "knowledge_validation"
    AUTOMATED_FIXES = "automated_fixes"
    EVIDENCE_INTEGRATION = "evidence_integration"
    RAG_COORDINATION = "rag_coordination"
    SESSION_INTEGRATION = "session_integration"

@dataclass
class IntegrationResult:
    success = bool

@dataclass
class CKSContext:
    integration_type = IntegrationType
    operation_id = str

class BaseCKSAdapter(ABC):
    __init__(self, integration_type: IntegrationType) -> None
    @abstractmethod
    initialize(self, config: dict[str, Any]) -> IntegrationResult
    @abstractmethod
    process_context(self, context: CKSContext) -> IntegrationResult
    validate_context(self, context: CKSContext) -> bool
    log_operation(self, operation: str, context: CKSContext, result: IntegrationResult) -> None
    get_metrics(self) -> dict[str, Any]

class AdapterRegistry:
    __init__(self) -> None
    register_adapter(self, adapter: BaseCKSAdapter) -> None
    get_adapter(self, integration_type: IntegrationType) -> BaseCKSAdapter | None
    list_adapters(self) -> list[IntegrationType]
    initialize_all(self, configs: dict[IntegrationType, dict[str, Any]]) -> dict[IntegrationType, IntegrationResult]
adapter_registry = AdapterRegistry()
```


### P:\packages\search-research\core\cks\integration\interfaces\integration_interfaces.py

```python
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar
from collections.abc import Awaitable
T = TypeVar("T")
ResultType = TypeVar("ResultType")

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

class SecurityLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class IntegrationConfig:
    __post_init__(self)

@dataclass
class IntegrationResult:
    success = bool
    @classmethod
    create_success(cls, data: ResultType, integration_source: str, metadata: dict[str, Any] | None = None, execution_time_seconds: float = 0.0, cached: bool = False) -> IntegrationResult[ResultType]
    @classmethod
    create_error(cls, error: str, integration_source: str, status_code: int | None = None, metadata: dict[str, Any] | None = None, execution_time_seconds: float = 0.0) -> IntegrationResult[ResultType]

@dataclass
class HealthCheck:
    status = IntegrationStatus
    response_time_ms = float
    @property
    is_healthy(self) -> bool

class BaseIntegrationClient(ABC):
    __init__(self, config: IntegrationConfig, integration_name: str) -> None
    @abstractmethod
    initialize(self) -> bool
    @abstractmethod
    health_check(self) -> HealthCheck
    @abstractmethod
    cleanup(self) -> None
    execute_operation(self, operation_name: str, operation_func: Awaitable[T], operation_metadata: dict[str, Any] | None = None) -> IntegrationResult[T]
    get_performance_statistics(self) -> dict[str, Any]
    clear_cache(self) -> None
    reset_statistics(self) -> None

class IntegrationClientFactory(ABC):
    @abstractmethod
    create_client(self, config: IntegrationConfig) -> BaseIntegrationClient
    @abstractmethod
    get_default_config(self) -> IntegrationConfig
    @abstractmethod
    validate_config(self, config: IntegrationConfig) -> bool
```


### P:\packages\search-research\core\cks\integration\knowledge_artifacts\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\knowledge_artifacts\expertise\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\knowledge_query_validator.py

```python
import json
from datetime import datetime
from pathlib import Path
from typing import Any

class KnowledgeQueryValidator:
    __init__(self, knowledge_dir: Path | None = None) -> None
    load_knowledge(self, knowledge_type: str) -> dict[str, Any] | None
    validate_structure(self) -> dict[str, Any]
    query_by_category(self, category: str) -> list[dict[str, Any]]
    query_by_tags(self, tags: list[str]) -> list[dict[str, Any]]
    query_integration_patterns(self, orchestrator_type: str | None = None) -> list[dict[str, Any]]
    query_performance_data(self, metric_type: str | None = None) -> dict[str, Any]
    query_risk_assessments(self, risk_level: str | None = None) -> list[dict[str, Any]]
    get_related_knowledge(self, item_id: str, item_type: str) -> dict[str, list[dict[str, Any]]]
    search_knowledge(self, query: str) -> list[dict[str, Any]]
    generate_knowledge_report(self) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\migration\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\migration\update_imports.py

```python
import argparse
import re
from pathlib import Path

class ImportUpdater:
    MIGRATION_MAP = {
        # Constitutional Compliance
        "from modules.constitutional_compliance.cks_compliance_monitor import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        "from modules.constitutional_compliance.cks_constitutional_compliance_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        "from modules.constitutional_compliance.cwo12_cks_compliance_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        # Orchestration
        "from modules.orchestration.cks_agent_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.ORCHESTRATION",
        },
        # Monitoring
        "from modules.monitoring.cks_monitoring_analytics import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.MONITORING",
        },
        # Performance
        "from modules.performance.cks_performance_optimizer import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.PERFORMANCE",
        },
        # Task Management
        "from modules.task_management.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.TASK_MANAGEMENT",
        },
        # Knowledge System
        "from modules.knowledge_system.cks_constitutional_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.KNOWLEDGE_SYSTEM",
        },
        "from modules.knowledge_system.cks_input_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.KNOWLEDGE_SYSTEM",
        },
        # Resilience
        "from modules.resilience.cks_fallback_error_handler import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.RESILIENCE",
        },
        # Universal Instrumentation
        "from modules.universal_instrumentation.integrations.cks_error_recovery_system import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_instrumentation import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_rag_integration_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_session_integration_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        # Other integrations
        "from modules.automated_fix_suggestions.integration.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.AUTOMATED_FIX_SUGGESTIONS",
        },
        "from modules.integration.cks_tasks_9_12_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.INTEGRATION",
        },
        "from modules.unified_systems.evidence.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIFIED_SYSTEMS",
        },
    }
    __init__(self, project_root: Path) -> None
    scan_for_migration_candidates(self, directory: Path) -> list[dict[str, str]]
    generate_migration_plan(self, candidates: list[dict[str, str]]) -> list[dict[str, str]]
    update_file(self, file_path: Path, line_number: int, old_line: str, new_line: str) -> bool
    create_migration_guide(self, candidates: list[dict[str, str]]) -> str
main() -> None
```


### P:\packages\search-research\core\cks\integration\orchestrator_observability_knowledge_integration.py

```python
import json
import logging
import sys
from datetime import datetime
from typing import Any
from ..core.multi_graph_engine import (
        GraphType, MultiGraphConfig, MultiGraphEngine, RelationshipType, )
from ..core.storage_manager import StorageConfig

class OrchestratorObservabilityKnowledgeIntegrator:
    __init__(self, config: MultiGraphConfig | None = None) -> None
    initialize(self) -> None
    store_research_findings(self) -> dict[str, str]
    store_integration_patterns(self) -> dict[str, str]
    store_performance_data(self) -> dict[str, str]
    store_risk_assessments(self) -> dict[str, str]
    create_cross_references(self, findings_ids: dict, patterns_ids: dict, performance_ids: dict, risk_ids: dict) -> None
    run_integration(self) -> dict[str, Any]
main() -> None
```


### P:\packages\search-research\core\cks\integration\orchestrator_observability_knowledge_simple.py

```python
import json
from datetime import datetime
from pathlib import Path
from typing import Any

class OrchestratorObservabilityKnowledgeCreator:
    __init__(self, output_dir: Path | None = None) -> None
    create_research_findings(self) -> dict[str, Any]
    create_integration_patterns(self) -> dict[str, Any]
    create_performance_knowledge(self) -> dict[str, Any]
    create_risk_assessments(self) -> dict[str, Any]
    create_cross_references(self) -> dict[str, Any]
    create_knowledge_summary(self) -> dict[str, Any]
    save_all_knowledge(self) -> dict[str, Path]
main() -> None
```


### P:\packages\search-research\core\cks\integration\session_memory_adapter.py

```python
import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import statistics
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from .chat_history_client import (
        ChatHistoryClient, ChatMessage, MessageRole, SessionContext, SessionContextType, SessionMemoryIndex, SessionPattern, )
from .chat_history_client import (
        ConversationPattern as ChatConversationPattern, )
CHAT_HISTORY_AVAILABLE = True
CHAT_HISTORY_AVAILABLE = False
ChatHistoryClient = None
from ...core.session_memory.models import (
        CompactionBridge, EvidenceReference, SessionTracking, TaskContext, )
from ...core.session_memory.models import (
        ConversationPattern as BridgeConversationPattern, )
from ...core.session_memory.session_memory_bridge import SessionMemoryBridge
SESSION_MEMORY_BRIDGE_AVAILABLE = True
SESSION_MEMORY_BRIDGE_AVAILABLE = False
SessionMemoryBridge = None
from ...core.storage_manager import StorageManager
CKS_STORAGE_AVAILABLE = True
CKS_STORAGE_AVAILABLE = False
StorageManager = None
from ...core.pytorch_vector_storage import DeviceManager, PyTorchStorageConfig
PYTORCH_STORAGE_AVAILABLE = True
PYTORCH_STORAGE_AVAILABLE = False
PyTorchStorageConfig = None
DeviceManager = None
from ..adapters.rag_integration_coordinator import (
        ComponentHealthStatus, CoordinatorConfig, CoordinatorState, InstrumentedCKSRAGIntegrationCoordinator, )
RAG_INTEGRATION_AVAILABLE = True
RAG_INTEGRATION_AVAILABLE = False
InstrumentedCKSRAGIntegrationCoordinator = None
CoordinatorConfig = None
from ...core.multi_graph_engine import MultiGraphEngine
MULTI_GRAPH_ENGINE_AVAILABLE = True
MULTI_GRAPH_ENGINE_AVAILABLE = False
MultiGraphEngine = None
from ...core.gpu_manager import GPUManager
GPU_MANAGER_AVAILABLE = True
GPU_MANAGER_AVAILABLE = False
GPUManager = None
logger = logging.getLogger(__name__)

class PatternComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    NESTED = "nested"

class IntentType(Enum):
    QUESTION = "question"
    COMMAND = "command"
    EXPLANATION = "explanation"
    COLLABORATION = "collaboration"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    REVIEW = "review"
    LEARNING = "learning"

class ContextSwitchType(Enum):
    NO_SWITCH = "no_switch"
    TOPIC_SWITCH = "topic_switch"
    TASK_SWITCH = "task_switch"
    DOMAIN_SWITCH = "domain_switch"
    MODE_SWITCH = "mode_switch"

@dataclass
class PatternEvolution:
    pattern_id = str
    evolution_steps = list[dict[str, Any]]
    confidence_trend = list[float]
    frequency_trend = list[float]
    complexity_trend = list[PatternComplexity]
    last_evolution = datetime
    evolution_summary = str

@dataclass
class IntentAnalysis:
    primary_intent = IntentType
    confidence = float
    secondary_intents = list[tuple[IntentType, float]]
    intent_keywords = list[str]
    context_relevance = float

@dataclass
class ContextSwitch:
    switch_point = int
    switch_type = ContextSwitchType
    from_context = str
    to_context = str
    confidence = float
    bridging_phrases = list[str]

@dataclass
class PatternCluster:
    cluster_id = str
    patterns = list[str]
    cluster_center = list[float]
    cluster_radius = float
    semantic_coherence = float
    common_keywords = list[str]
    dominant_intent = IntentType

@dataclass
class ReconstructionQuality:
    completeness_score = float
    accuracy_score = float
    consistency_score = float
    semantic_fidelity = float
    structural_integrity = float
    overall_quality = float
    missing_elements = list[str]
    quality_issues = list[str]

@dataclass
class RAGContextInjection:
    session_id = str
    injected_context = dict[str, Any]
    relevance_scores = dict[str, float]
    filtering_results = dict[str, Any]
    performance_metrics = dict[str, float]
    injection_timestamp = datetime
    context_overlap_score = float
    semantic_similarity_score = float

@dataclass
class HybridContext:
    rag_context = dict[str, Any]
    session_context = dict[str, Any]
    merged_context = dict[str, Any]
    confidence_weights = dict[str, float]
    semantic_bridges = list[dict[str, Any]]
    integration_quality = float
    processing_overhead_ms = float

@dataclass
class IntelligentFilter:
    filter_id = str
    session_relevance_threshold = float
    semantic_noise_threshold = float
    context_mismatch_penalty = float
    filter_results = dict[str, Any]
    performance_metrics = dict[str, float]
    filter_timestamp = datetime

@dataclass
class SemanticBridge:
    bridge_id = str
    source_vectors = list[str]
    target_vectors = list[str]
    bridge_strength = float
    semantic_mappings = dict[str, list[str]]
    cross_references = dict[str, Any]
    maintenance_status = str
    last_updated = datetime

class SessionMemoryAdapter:
    __init__(self, chat_history_client: ChatHistoryClient | None = None, session_memory_bridge: SessionMemoryBridge | None = None, storage_manager: StorageManager | None = None, device_manager: DeviceManager | None = None, rag_coordinator: InstrumentedCKSRAGIntegrationCoordinator | None = None, multi_graph_engine: MultiGraphEngine | None = None, gpu_manager: GPUManager | None = None, cache_size_mb: int = 100, enable_rag_integration: bool = True, enable_hybrid_context: bool = True, enable_intelligent_filtering: bool = True, context_injection_timeout_ms: float = 50.0, pattern_reconstruction_timeout_ms: float = 100.0) -> None
    detect_conversation_patterns(self, messages: list[dict[str, Any]], session_id: str | None = None) -> list[dict[str, Any]]
    analyze_pattern_importance(self, pattern: dict[str, Any], messages: list[dict[str, Any]]) -> float
    identify_key_decisions(self, messages: list[dict[str, Any]], patterns: list[dict[str, Any]] | None = None) -> list[str]
    track_pattern_evolution(self, pattern: dict[str, Any], new_messages: list[dict[str, Any]]) -> PatternEvolution
    calculate_semantic_similarity(self, pattern1: dict[str, Any], pattern2: dict[str, Any]) -> float
    cluster_related_patterns(self, patterns: list[dict[str, Any]], max_clusters: int = 10) -> dict[str, list[str]]
    find_similar_historical_patterns(self, pattern: dict[str, Any], similarity_threshold: float = 0.8, max_results: int = 20) -> list[dict[str, Any]]
    reconstruct_conversation_context(self, patterns: list[dict[str, Any]], bridge_data: dict[str, Any]) -> dict[str, Any]
    validate_pattern_reconstruction(self, original_patterns: list[dict[str, Any]], reconstructed: dict[str, Any]) -> ReconstructionQuality
    fill_missing_pattern_elements(self, patterns: list[dict[str, Any]]) -> list[dict[str, Any]]
    preserve_patterns_across_compaction(self, session_id: str, patterns: list[dict[str, Any]], criticality_threshold: float = 0.7) -> bool
    restore_patterns_from_compaction(self, bridge_id: str) -> list[dict[str, Any]]
    inject_context_logic(self, session_id: str, context_data: dict[str, Any]) -> dict[str, Any]
    pattern_reconstruction_algorithms(self, patterns: list[dict[str, Any]]) -> dict[str, Any]
    work_with_cks_integration(self) -> bool
    optimize_vector_store_for_sessions(self) -> dict[str, Any]
    get_performance_metrics(self) -> dict[str, Any]
    cleanup(self) -> None
__all__ = [
    "ContextSwitch",
    "ContextSwitchType",
    "HybridContext",
    "IntelligentFilter",
    "IntentAnalysis",
    "IntentType",
    "PatternCluster",
    "PatternComplexity",
    "PatternEvolution",
    "RAGContextInjection",
    "ReconstructionQuality",
    "SemanticBridge",
    "SessionMemoryAdapter",
]
```


### P:\packages\search-research\core\cks\integration\standalone_test.py

```python
import logging
import time
from datetime import datetime
from pathlib import Path
logger = logging.getLogger(__name__)
test_cks_integration_module_standalone() -> bool | None
success = test_cks_integration_module_standalone()
```


### P:\packages\search-research\core\cks\integration\test_cks_integration_module.py

```python
import logging
import time
from datetime import datetime
logger = logging.getLogger(__name__)
test_cks_integration_module() -> bool | None
test_performance_requirements() -> None
run_all_tests()
```


### P:\packages\search-research\core\cks\integration\test_session_memory_adapter.py

```python
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
import pytest
from .session_memory_adapter import (
    PatternEvolution, ReconstructionQuality, SessionMemoryAdapter, )
@pytest.fixture
sample_messages()
@pytest.fixture
complex_conversation()
@pytest.fixture
session_memory_adapter()

class TestPatternDetectionAlgorithms:
    @pytest.mark.asyncio
    test_detect_conversation_patterns_basic(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_detect_conversation_patterns_complex(self, session_memory_adapter: SessionMemoryAdapter, complex_conversation: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_analyze_pattern_importance(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_identify_key_decisions(self, session_memory_adapter: SessionMemoryAdapter, complex_conversation: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_track_pattern_evolution(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None

class TestSemanticSimilarityScoring:
    @pytest.mark.asyncio
    test_calculate_semantic_similarity(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_calculate_semantic_similarity_performance(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_cluster_related_patterns(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_find_similar_historical_patterns(self, session_memory_adapter: SessionMemoryAdapter) -> None

class TestPatternReconstructionAlgorithms:
    @pytest.mark.asyncio
    test_reconstruct_conversation_context(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_validate_pattern_reconstruction(self, session_memory_adapter: SessionMemoryAdapter, sample_messages: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_fill_missing_pattern_elements(self, session_memory_adapter: SessionMemoryAdapter) -> None

class TestSessionMemoryBridgeIntegration:
    @pytest.mark.asyncio
    test_preserve_patterns_across_compaction(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_restore_patterns_from_compaction(self, session_memory_adapter: SessionMemoryAdapter) -> None

class TestPerformanceValidation:
    @pytest.mark.asyncio
    test_pattern_analysis_performance_target(self, session_memory_adapter: SessionMemoryAdapter, complex_conversation: list[dict[str, Any]]) -> None
    @pytest.mark.asyncio
    test_similarity_calculation_performance_target(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_pattern_reconstruction_performance_target(self, session_memory_adapter: SessionMemoryAdapter, complex_conversation: list[dict[str, Any]]) -> None
    test_memory_overhead_validation(self, session_memory_adapter: SessionMemoryAdapter) -> None

class TestEdgeCasesAndErrorHandling:
    @pytest.mark.asyncio
    test_empty_message_list(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_invalid_message_format(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_null_pattern_handling(self, session_memory_adapter: SessionMemoryAdapter) -> None
    @pytest.mark.asyncio
    test_malformed_embeddings(self, session_memory_adapter: SessionMemoryAdapter) -> None
    test_cleanup_resources(self, session_memory_adapter: SessionMemoryAdapter) -> None
@pytest.mark.asyncio
test_complete_workflow_integration(session_memory_adapter: SessionMemoryAdapter, complex_conversation: list[dict[str, Any]]) -> None
@pytest.mark.asyncio
test_performance_benchmark(session_memory_adapter: SessionMemoryAdapter) -> None
```


### P:\packages\search-research\core\cks\integration\test_session_memory_adapter_rag.py

```python
import asyncio
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
import pytest
from .session_memory_adapter import (
    HybridContext, IntelligentFilter, RAGContextInjection, SemanticBridge, SessionMemoryAdapter, )

class MockRAGCoordinator:
    __init__(self) -> None
    initialize(self) -> None
    coordinate_rag_workflow(self, query, documents = None, context = None, workflow_config = None)

class MockStorageManager:
    __init__(self) -> None
    store_vector(self, vector_id, vector) -> None
    retrieve_vector(self, vector_id)

class MockSessionMemoryBridge:
    __init__(self) -> None
    preserve_session_context(self, session_id, criticality_threshold = 0.7)
    restore_session_context(self, bridge_id)

class MockCompactionBridge:
    __init__(self, session_id, criticality_threshold) -> None
    add_preserved_pattern(self, pattern) -> None

class MockRestorationResult:
    __init__(self, success = True) -> None

class TestSessionMemoryAdapterRAGIntegration:
    @pytest.fixture
    adapter(self)
    @pytest.mark.asyncio
    test_adapter_initialization(self, adapter) -> None
    @pytest.mark.asyncio
    test_context_injection_logic_performance(self, adapter) -> None
    @pytest.mark.asyncio
    test_pattern_reconstruction_algorithms_performance(self, adapter) -> None
    @pytest.mark.asyncio
    test_cks_integration_functionality(self, adapter) -> None
    @pytest.mark.asyncio
    test_vector_store_optimization(self, adapter) -> None
    @pytest.mark.asyncio
    test_intelligent_filtering_system(self, adapter) -> None
    @pytest.mark.asyncio
    test_hybrid_context_management(self, adapter) -> None
    @pytest.mark.asyncio
    test_semantic_bridge_functionality(self, adapter) -> None
    @pytest.mark.asyncio
    test_performance_optimization_with_caching(self, adapter) -> None
    @pytest.mark.asyncio
    test_rag_query_overhead_target(self, adapter) -> None
    @pytest.mark.asyncio
    test_error_handling_and_fallbacks(self, adapter) -> None
    @pytest.mark.asyncio
    test_concurrent_operations(self, adapter) -> None
    @pytest.mark.asyncio
    test_memory_usage_and_cleanup(self, adapter) -> None

class TestSessionMemoryAdapterDataStructures:
    test_rag_context_injection_dataclass(self) -> None
    test_hybrid_context_dataclass(self) -> None
    test_intelligent_filter_dataclass(self) -> None
    test_semantic_bridge_dataclass(self) -> None

class TestSessionMemoryAdapterPerformance:
    @pytest.mark.asyncio
    test_performance_benchmarks(self) -> None
```


### P:\packages\search-research\core\cks\integration\utils\__init__.py

```python

```


### P:\packages\search-research\core\cks\integration\utils\integration_factory.py

```python
__all__ = []
```


### P:\packages\search-research\core\cks\integration\validate_rag_integration.py

```python
import asyncio
import sys
import time
import session_memory_adapter as adapter_module
from session_memory_adapter import (
        HybridContext, IntelligentFilter, RAGContextInjection, SemanticBridge, SessionMemoryAdapter, )

class MockCoordinatorState:
    ACTIVE = "active"
    INITIALIZING = "initializing"

class MockRAGCoordinator:
    __init__(self) -> None
    initialize(self) -> None
    coordinate_rag_workflow(self, query, documents = None, context = None, workflow_config = None)

class MockStorageManager:
    __init__(self) -> None
    store_vector(self, vector_id, vector) -> None
    retrieve_vector(self, vector_id)

class MockSessionMemoryBridge:
    preserve_session_context(self, session_id, criticality_threshold = 0.7)
    restore_session_context(self, bridge_id)

class MockCompactionBridge:
    __init__(self, session_id, criticality_threshold) -> None
    add_preserved_pattern(self, pattern) -> None

class MockRestorationResult:
    __init__(self, success = True) -> None
validate_basic_functionality() -> bool
main() -> None
```


### P:\packages\search-research\core\cks\learning\__init__.py

```python
from src.cks.learning.citation_parser import extract_citations
from src.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding
__all__ = ["DiagnosticFinding", "extract_citations", "store_finding"]
```


### P:\packages\search-research\core\cks\learning\citation_parser.py

```python
import re
from typing import Any
extract_citations(text: str) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\learning\continuous_learner.py

```python
import hashlib
import json
import logging
import sqlite3
import statistics
import threading
import time
import asyncio
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np
from ...lib.core_utils.config_manager import get_config
from ..utils.constitutional_validator import ConstitutionalValidator
CSF_NIP_AVAILABLE = True
CSF_NIP_AVAILABLE = False
logger = logging.getLogger(__name__)

@dataclass
class UsagePattern:
    pattern_id = str
    component = str
    operation = str
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "UsagePattern"

@dataclass
class QualityMetrics:
    knowledge_id = str
    calculate_overall_score(self) -> float
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "QualityMetrics"

@dataclass
class LearningInsight:
    insight_id = str
    insight_type = str
    title = str
    description = str
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> "LearningInsight"

@dataclass
class LearningConfig:
    __post_init__(self)

class UsagePatternTracker:
    __init__(self, config: LearningConfig) -> None
    track_operation(self, component: str, operation: str, duration: float, success: bool = True, metadata: dict[str, Any] | None = None) -> None
    get_pattern(self, pattern_id: str) -> UsagePattern | None
    get_patterns_by_component(self, component: str) -> list[UsagePattern]
    get_top_patterns(self, limit: int = 10) -> list[UsagePattern]

class AdaptiveOptimizer:
    __init__(self, config: LearningConfig, pattern_tracker: UsagePatternTracker) -> None
    generate_optimizations(self) -> list[LearningInsight]
    get_optimization_history(self, limit: int = 50) -> list[dict[str, Any]]

class KnowledgeQualityScorer:
    __init__(self, config: LearningConfig) -> None
    assess_knowledge_quality(self, knowledge_id: str, evidence: list[dict[str, Any]] | None = None) -> QualityMetrics
    get_quality_metrics(self, knowledge_id: str) -> QualityMetrics | None
    get_top_quality_knowledge(self, limit: int = 10) -> list[QualityMetrics]
    get_low_quality_knowledge(self, threshold: float = 0.5, limit: int = 10) -> list[QualityMetrics]

class EvidenceBasedLearning:
    __init__(self, config: LearningConfig, pattern_tracker: UsagePatternTracker, quality_scorer: KnowledgeQualityScorer, optimizer: AdaptiveOptimizer) -> None
    get_insights(self, insight_type: str | None = None, limit: int = 50) -> list[LearningInsight]
    get_learning_history(self, limit: int = 50) -> list[dict[str, Any]]

class ContinuousLearner:
    __init__(self, config: LearningConfig | None = None) -> None
    track_usage(self, component: str, operation: str, duration: float, success: bool = True, metadata: dict[str, Any] | None = None) -> None
    assess_quality(self, knowledge_id: str, evidence: list[dict[str, Any]] | None = None) -> QualityMetrics
    get_insights(self, insight_type: str | None = None, limit: int = 50) -> list[LearningInsight]
    get_patterns(self, component: str | None = None, limit: int = 50) -> list[UsagePattern]
    get_quality_metrics(self, knowledge_id: str | None = None, top_k: int = 10) -> list[QualityMetrics]
    get_system_status(self) -> dict[str, Any]
    optimize(self, force: bool = False) -> list[LearningInsight]
    shutdown(self) -> None
create_continuous_learner(config: LearningConfig | None = None) -> ContinuousLearner
@contextmanager
continuous_learning_session(config: LearningConfig | None = None)
```


### P:\packages\search-research\core\cks\learning\diagnostic_writer.py

```python
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

@dataclass
class DiagnosticFinding:
    category = str
    file_path = str | None
    line_number = int | None
    summary = str
    details = str
    skill_source = str
    to_metadata(self) -> dict[str, str | int]
    to_cks_entry(self) -> tuple[str, str, dict]
store_finding(finding: DiagnosticFinding) -> bool
```


### P:\packages\search-research\core\cks\learning\findings_helper.py

```python
from src.knowledge.systems.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding
rca_finding(summary: str, details: str, category: str = "BUG", file_path: str | None = None, line_number: int | None = None, confidence: str = "medium") -> DiagnosticFinding
debug_finding(summary: str, details: str, category: str = "BUG", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
tdd_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
arch_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
security_finding(summary: str, details: str, category: str = "VULNERABILITY", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
quality_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None, confidence: str = "medium") -> DiagnosticFinding
q_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None, confidence: str = "medium") -> DiagnosticFinding
p_finding(summary: str, details: str, category: str = "BUG", file_path: str | None = None, line_number: int | None = None, confidence: str = "medium") -> DiagnosticFinding
store_quick_finding(skill: str, summary: str, details: str, category: str = "DISCOVERY", file_path: str | None = None, line_number: int | None = None) -> bool
batch_findings(findings: list[DiagnosticFinding]) -> dict[str, bool]
__all__ = [
    "DiagnosticFinding",
    "arch_finding",
    "batch_findings",
    "debug_finding",
    "p_finding",
    "q_finding",
    "quality_finding",
    "rca_finding",
    "security_finding",
    "store_finding",
    "store_quick_finding",
    "tdd_finding",
]
```


### P:\packages\search-research\core\cks\learning\validation.py

```python
import logging
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    component = str
    requirement = str
    compliance_level = ComplianceLevel
    severity = ValidationSeverity
    message = str
    to_dict(self) -> dict[str, Any]

@dataclass
class ComplianceReport:
    framework_name = str
    add_result(self, result: ValidationResult) -> None
    get_summary(self) -> dict[str, Any]

class ConstitutionalValidator:
    CONSTITUTIONAL_REQUIREMENTS = {
        "solo_developer_optimization": {
            "description": "Zero background services, on-demand processing",
            "validations": [
                "no_background_threads_running",
                "on_demand_processing_only",
                "single_pc_deployment",
            ],
        },
        "evidence_based_implementation": {
            "description": "TDD approach, real data validation",
            "validations": [
                "tdd_implementation",
                "real_data_validation",
                "no_synthetic_test_data",
            ],
        },
        "force_multiplier_integration": {
            "description": "Multi-graph capability, adaptive learning",
            "validations": [
                "multi_graph_support",
                "adaptive_learning",
                "scalable_architecture",
            ],
        },
        "no_enterprise_bloat": {
            "description": "Simple, direct implementation",
            "validations": [
                "minimal_dependencies",
                "direct_implementation",
                "no_complex_abstractions",
            ],
        },
    }
    __init__(self) -> None
    validate_constitutional_compliance(self, learning_framework) -> ComplianceReport

class CSFNIPValidator:
    CSF_NIP_STANDARDS = {
        "python_standards": {
            "description": "PEP 8 compliance with 79-char line limit",
            "validations": [
                "line_length_compliance",
                "naming_conventions",
                "documentation_standards",
            ],
        },
        "anti_mock_philosophy": {
            "description": "No mocks in production code",
            "validations": [
                "no_production_mocks",
                "real_implementation_only",
            ],
        },
        "modern_path_management": {
            "description": "Modern Python path management",
            "validations": [
                "editable_installs",
                "relative_imports",
            ],
        },
        "quality_assurance": {
            "description": "Comprehensive QA validation",
            "validations": [
                "test_coverage",
                "validation_gates",
                "continuous_integration",
            ],
        },
    }
    __init__(self) -> None
    validate_csf_nip_compliance(self, learning_framework) -> ComplianceReport
validate_learning_framework_compliance(learning_framework) -> tuple[ComplianceReport, ComplianceReport]
```


### P:\packages\search-research\core\cks\memory_efficient_rag.py

```python
import logging
import json
import logging
from pathlib import Path
from sqlite3 import Connection
from typing import Any
import faiss
import numpy as np
logger = logging.getLogger(__name__)

class CKSMemoryEfficientRAG:
    __init__(self, vector_dim: int = 384, nlist: int = 100, m: int = 48) -> None
    build_from_sqlite(self, conn: Connection, entry_type: str | None = None, min_entries_for_training: int = 3900) -> bool
    search(self, query_embedding: np.ndarray, k: int = 10, entry_type: str | None = None) -> list[dict[str, Any]]
    save(self, path: Path) -> bool
    load(self, path: Path) -> bool
    get_statistics(self) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\metadata.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from collections.abc import Iterable

class Category(str, Enum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    SKILL = "skill"
    SESSION = "session"
    CONFIGURATION = "configuration"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    MEMORY = "memory"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Citation:
    file_path = str
    line_number = int
    __post_init__(self) -> None
    @property
    is_multiline(self) -> bool
    @property
    line_range(self) -> range
    format_location(self, style: Literal["short", "full", "url"] = "short") -> str
    __str__(self) -> str

@dataclass(frozen=True)
class FileMetadata:
    path = str
    category = Category
    __post_init__(self) -> None
    @property
    filename(self) -> str
    @property
    extension(self) -> str | None
    with_category(self, new_category: Category) -> FileMetadata
    add_tags(self, new_tags: Iterable[str]) -> FileMetadata
    mark_indexed(self) -> FileMetadata
    increment_citations(self, delta: int = 1) -> FileMetadata

@dataclass
class KnowledgeItem:
    id = str
    content = str
    citations = frozenset[Citation]
    metadata = FileMetadata
    @property
    primary_citation(self) -> Citation | None
    @property
    source_files(self) -> frozenset[str]
    add_citation(self, citation: Citation) -> KnowledgeItem
    with_embedding(self, embedding: list[float]) -> KnowledgeItem
```


### P:\packages\search-research\core\cks\migrations\__init__.py

```python

```


### P:\packages\search-research\core\cks\migrations\migrate_project_context.py

```python
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..unified import CKS
logger = logging.getLogger(__name__)
get_source_entities(source_db_path: str, entity_type: str | None = None) -> list[dict[str, Any]]
migrate_task_entity(cks: CKS, entity: dict[str, Any]) -> str | None
migrate_project_context_entity(cks: CKS, entity: dict[str, Any]) -> str | None
migrate_checkpoint_entity(cks: CKS, entity: dict[str, Any]) -> str | None
migrate_blocker_entity(cks: CKS, entity: dict[str, Any]) -> str | None
migrate_decision_entity(cks: CKS, entity: dict[str, Any]) -> str | None
run_migration(source_db_path: str = "P:/.cks/storage/cks.db", target_db_path: str = None, dry_run: bool = False) -> dict[str, int]
main()
```


### P:\packages\search-research\core\cks\migrations\migrate_to_2025.py

```python
from dataclasses import field
from datetime import datetime
from pathlib import Path
import asyncio
import json
import logging
import os
import re
import statistics
import sys
from pydantic import BaseModel, ValidationError
import shutil
import sqlite3
import structlog
logger = structlog.get_logger(__name__)

class MigrationConfig(BaseModel):
    source_db_path = str
    target_db_path = str

class LegacyEntry(BaseModel):
    id = int | None
    timestamp = str
    category = str
    title = str
    content = str
    tags = str

class CKSMigrator:
    __init__(self, config: MigrationConfig) -> None
    migrate(self) -> bool
main() -> int
```


### P:\packages\search-research\core\cks\optimized_search.py

```python
from typing import TYPE_CHECKING
from collections.abc import Callable
from .unified import CKS
search_optimized(self: CKS, query: str, entry_type: str | None = None, limit: int = 5, expand_query: bool = True, use_mmr: bool = True, mmr_lambda: float = 0.7, fusion_method: str = "rrf") -> list[dict]
patch_optimized_search(cks_class: type) -> type
search_parallel_backends(query: str, backends: dict[str, Callable], limit: int = 10, use_mmr: bool = True, mmr_lambda: float = 0.7) -> list[dict]
```


### P:\packages\search-research\core\cks\quality.py

```python
import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent

@dataclass
class QualityStats:
    to_dict(self) -> dict[str, Any]
calculate_decay_score(entry: dict[str, Any]) -> float
get_quality_statistics(db_path: str | Path = "P:/__csf/data/cks.db") -> QualityStats
format_stats_terminal(stats: QualityStats) -> str
sample_archival_candidates(db_path: str | Path = "P:/__csf/data/cks.db", limit: int = 10) -> list[dict]
main() -> None
```


### P:\packages\search-research\core\cks\query_expansion.py

```python
import re
from functools import lru_cache
from typing import Any

class EntityData:
    synonyms = dict[str, list[str]]
    related_concepts = list[str]

class QueryExpander:
    __init__(self) -> None
    expand_query(self, query: str, entity_slug: str | None = None, max_variations: int = 5) -> list[str]
get_query_suggestions(query: str, limit: int = 5) -> list[str]
expand_query_if_enabled(query: str, enabled: bool = True) -> list[str]
```


### P:\packages\search-research\core\cks\reranking.py

```python
import math
from datetime import UTC, datetime
from search_research.diversity import mmr_rerank
MMR_AVAILABLE = True
MMR_AVAILABLE = False
reciprocal_rank_fusion(result_sets: list[list[dict]], k: int = 60, limit: int | None = None) -> list[dict]
maximal_marginal_relevance(query: str, results: list[dict], lambda_param: float = 0.7, get_similarity_func = None, limit: int | None = None) -> list[dict]
calculate_temporal_boost(entry: dict, base_boost: float = 1.0, decay_rates: dict[str, float] | None = None) -> float
adaptive_decay_thresholds(query_type: str, entry_type: str, base_threshold: float = 0.50) -> float

class SearchResultsMerger:
    @staticmethod
    merge_results(result_sets: list[list[dict]], merge_strategy: str = "rrf") -> list[dict]
weighted_average_fusion(result_sets: list[list[dict]], weights: list[float] | None = None, limit: int | None = None) -> list[dict]
combsum_fusion(result_sets: list[list[dict]], limit: int | None = None) -> list[dict]
adaptive_fusion(result_sets: list[list[dict]], query_type: str = "balanced", limit: int | None = None) -> list[dict]
detect_query_type(query: str) -> str
calculate_content_density(entry: dict) -> float
apply_length_aware_reranking(results: list[dict], base_score_field: str = "rrf_score", density_weight: float = 0.3, type_boost: float = 0.15, query: str = "", enable_mmr: bool = False, mmr_lambda: float = 0.5) -> list[dict]
enhance_fts_with_density(results: list[dict], limit: int = 5) -> list[dict]
```


### P:\packages\search-research\core\cks\session_lesson_extractor.py

```python
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from cks.unified import CKS
logger = logging.getLogger(__name__)

@dataclass
class ExtractedLesson:
    entry_type = str
    title = str
    content = str
    metadata = dict[str, Any]
    source_file = str
    extracted_at = str
    store(self, cks: CKS) -> str

class SessionLessonExtractor:
    LEARNING_PATTERNS = [
        r"(?:learned|discovered|found|realized|note|remember)[:\s]+(.+?)(?:\.|$)",
        r"(?:serper|serpapi|tavily|brave|exa)[\s]+is\s+(?:\d+x\s+)?(?:cheaper|faster|better)(.+?)(?:\.|$)",
        r"(?:verif?ied|confirmed)[\s]+(.+?)(?:\.|$)",
        r"(?:claim|statement)[\s]+(.+?)[:\s]+(?:true|correct|accurate)",
        r"(?:free tier[:\s]+.+?)(?:\.|$)",
    ]
    INSIGHT_PATTERNS = [
        r"(?:realized|noticed|observed)[\s]+(.+?)(?:\.|$)",
        r"(?:issue|problem|error)[\s+was[:\s]+(?:caused|due to)[\s]+(.+?)(?:\.|$)",
        r"(?:root cause|reason|because)[\s]+(?:was|is)[:\s]+(.+?)(?:\.|$)",
    ]
    CORRECTION_PATTERNS = [
        r"(?:fixed|corrected|resolved)[\s]+(.+?)[:\s]+by\s+(.+?)(?:\.|$)",
        r"(?:mistake|error|bug|issue)[\s]+(.+?)[:\s]+(.+?)(?:\.|$)",
        r"(?:wrong|incorrect|broken)[\s]+(.+?)[:\s]+(.+?)(?:\.|$)",
    ]
    PATTERN_PATTERNS = [
        r"(?:use|need|require)[:\s]+(.+?)(?:\.|$)",
        r"(?:windows|cmd|npx|wrapper|script|bash|shell)[:\s]+(.+?)(?:\.|$)",
        r"(?:solution|fix|workaround)[:\s]+(.+?)(?:\.|$)",
        r"(?:pattern|approach|method|strategy)[:\s]+(.+?)(?:\.|$)",
        r"(?:config|configuration|settings)[:\s]+(.+?)(?:\.|$)",
    ]
    SECTION_HEADERS = [
        "summary",
        "conclusions",
        "lessons learned",
        "findings",
        "results",
        "recommendations",
        "action items",
        "next steps",
    ]
    __init__(self)
    extract_session(self, session_file: Path | str) -> list[ExtractedLesson]
    extract_and_store(self, session_file: Path | str) -> dict[str, Any]
find_current_session() -> Path | None
extract_session_lessons(session_file: Path | str | None = None) -> dict[str, Any]
main()
```


### P:\packages\search-research\core\cks\spell_correction.py

```python
import pickle
import re
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "__csf" / "data"
CACHE_FILE = CACHE_DIR / "symspell_cache.pkl"
from symspellpy import SymSpell, Verbosity
SYMSPELL_AVAILABLE = True
SYMSPELL_AVAILABLE = False

class QuerySpellCorrector:
    __init__(self, max_edit_distance: int = 2, prefix_length: int = 7, learn_from_cks: bool = True) -> None
    initialize(self, cks_db_path: str | None = None) -> None
    correct_query(self, query: str) -> str
    is_correction_needed(self, original: str, corrected: str) -> bool
correct_spell(query: str, cks_db_path: str | None = None) -> str
suggest_query_alternatives(query: str, max_suggestions: int = 3, min_confidence: float = 0.3, cks_db_path: str | None = None) -> list[dict]
corrector = QuerySpellCorrector()
test_cases = [
        "databse timeout",  # typo: databse -> database
        "authentiction error",  # typo: authentiction -> authentication
        "conection pool",  # typo: conection -> connection
        "cks api search",  # no correction needed
    ]
corrected = corrector.correct_query(test)
changed = corrector.is_correction_needed(test, corrected)
status = "✓ CHANGED" if changed else "  OK"
```


### P:\packages\search-research\core\cks\storage.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable

@dataclass
class StorageConfig:
    path = str

class KnowledgeStorage(ABC):
    __init__(self, config: StorageConfig) -> None
    @abstractmethod
    store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> bool
    @abstractmethod
    retrieve(self, key: str) -> Any | None
    @abstractmethod
    search(self, query: str, limit: int = 10, filters: dict[str, Any] | None = None) -> Iterable[dict[str, Any]]
    @abstractmethod
    delete(self, key: str) -> bool
    initialize(self) -> None
    close(self) -> None
    __enter__(self) -> KnowledgeStorage
    __exit__(self) -> None

class VectorStorage(KnowledgeStorage):
    @abstractmethod
    store_vector(self, key: str, vector: list[float], metadata: dict[str, Any] | None = None) -> bool
    @abstractmethod
    similarity_search(self, query_vector: list[float], limit: int = 10, threshold: float = 0.0) -> Iterable[tuple[str, float, dict[str, Any] | None]]
    @abstractmethod
    batch_store(self, items: Iterable[tuple[str, list[float], dict[str, Any] | None]]) -> int
```


### P:\packages\search-research\core\cks\test_dry_run.py

```python
import asyncio
import logging
import os
from unittest.mock import AsyncMock, MagicMock
from .consolidation.dreaming_cycle import DreamingService, RelationHypothesis
from .core.vector_manager import VectorConfig, VectorKnowledgeManager
logger = logging.getLogger(__name__)
run_dry_run() -> None
```


### P:\packages\search-research\core\cks\test_multi_signal_ranking.py

```python
from datetime import UTC, datetime, timedelta
from .unified import CKS
test_multi_signal_scoring() -> None
```


### P:\packages\search-research\core\cks\unified.py

```python
import json
import math
import os
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
from .commands.auto_learning_expander import AutoLearningQueryExpander
from .hybrid_search_patch import patch_hybrid_search
from .optimized_search import patch_optimized_search
from .query_expansion import QueryExpander, expand_query_if_enabled
from .reranking import (
        SearchResultsMerger, adaptive_fusion, calculate_temporal_boost, combsum_fusion, detect_query_type, maximal_marginal_relevance, reciprocal_rank_fusion, weighted_average_fusion, )
from .spell_correction import QuerySpellCorrector
PHASE1_AVAILABLE = True
PHASE2_AVAILABLE = True
PHASE1_AVAILABLE = True
PHASE2_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = True
QUERY_TYPE_THRESHOLDS = {
    "technical": 0.20,  # Lowered - 0.35 was too high (max obs ~0.28)
    "balanced": 0.15,  # Lowered - 0.30 was too high
    "preference": 0.12,  # Lowered - 0.25 was too high
}
QUERY_TYPE_KEYWORDS = {
    "technical": [
        "code",
        "function",
        "class",
        "api",
        "implement",
        "debug",
        "error",
        "syntax",
        "compile",
        "test",
        "refactor",
    ],
    "preference": [
        "prefer",
        "like",
        "want",
        "should",
        "opinion",
        "think",
        "feel",
        "believe",
        "usually",
        "typically",
    ],
}
VALID_ENTRY_TYPES = [
    "memory",  # Generic memories (existing)
    "pattern",  # Repeating patterns (existing)
    "code",  # Code snippets (existing)
    "knowledge",  # Factual knowledge (existing)
    "correction",  # Mistakes and fixes (NEW)
    "decision",  # Choices made and why (NEW)
    "commitment",  # Promises/resolutions (NEW)
    "insight",  # Realizations and aha moments (NEW)
    "learning",  # Lessons learned (NEW)
    "task",  # Task entities for project context (Consolidation Phase 1)
    "checkpoint",  # Session checkpoint entities (Consolidation Phase 1)
    "blocker",  # Blocker entities (Consolidation Phase 1)
    "docs",  # Documentation files
]
QUERY_INTENT_BOOSTS = {
    "decisions?|chose|choice|selected|picked|what.*did": ["memory", "decision"],
    "prefer|like|want|should": ["memory"],
    "mistakes?|wrong|error|fail|bug|issues?": ["pattern", "correction"],
    "problem|fix": ["pattern", "correction"],
    "pattern|habit|routine": ["pattern"],
    "learn|discover|realize|found|explain|concept": ["knowledge", "learning", "insight"],
    "commits?|promise|resolves?": ["commitment"],
    "code|function|class": ["code"],
}

class CKS:
    __init__(self, db_path: str | Path | None = None, enable_semantic: bool = True, enable_spell_correction: bool | None = None, enable_auto_learning: bool = True, auto_learning_threshold: float = 0.4, use_fp16: bool = True, use_scalar_quantization: bool = True) -> None
    clear_query_cache(self) -> None
    get_cache_stats(self) -> dict[str, int | float]
    detect_intent(self, query: str) -> str
    get_all_intents(self) -> list[str]
    ingest_memory(self, question: str, answer: str, source_chunk: str | None = None) -> str
    search_memories(self, query: str, limit: int = 5) -> list[dict]
    search_keyword_fts5(self, query: str, limit: int = 10, entry_type: str | None = None) -> list[dict]
    ingest_pattern(self, title: str, content: str, entry_type: str = "pattern", source_chunk: str | None = None) -> str
    search_patterns(self, query: str, limit: int = 5) -> list[dict]
    ingest_correction(self, title: str, content: str) -> str
    ingest_decision(self, title: str, content: str) -> str
    ingest_commitment(self, title: str, content: str) -> str
    ingest_insight(self, title: str, content: str) -> str
    ingest_learning(self, title: str, content: str) -> str
    extract_and_ingest_decisions(self, transcript: str, min_confidence: float = 0.60, session_id: str | None = None) -> dict
    ingest_memories_batch(self, items: list[dict[str, str]], batch_size: int = 32) -> list[str]
    ingest_patterns_batch(self, items: list[dict[str, str]], entry_type: str = "pattern", batch_size: int = 32) -> list[str]
    search(self, query: str, entry_type: str | None = None, limit: int = 5) -> list[dict]
    ingest_task(self, name: str, status: str = "pending", progress_pct: int = 0, description: str = "", priority: str = "medium", strategic_context: dict[str, Any] | None = None) -> str
    ingest_checkpoint(self, task_name: str, session_id: str, progress_pct: int, blocker: dict[str, Any] | None = None, files_modified: list[str] | None = None, next_steps: list[str] | None = None, session_summary: str = "") -> str
    ingest_blocker(self, task_name: str, description: str, severity: str = "medium", investigation: str = "", workaround: str = "") -> str
    add_relationship(self, from_entry_id: str, to_entry_id: str, relationship_type: str, metadata: dict[str, Any] | None = None) -> bool
    get_relationships(self, entry_id: str, relationship_type: str | None = None, direction: str = "both") -> list[dict[str, Any]]
    get_tasks(self, status: str | None = None, priority: str | None = None, limit: int = 100) -> list[dict[str, Any]]
    search_semantic(self, query: str, entry_type: str | None = None, limit: int = 5, expand_query: bool = False, fusion_method: str | None = None, diversity: float | None = None, entity_slug: str | None = None, spell_correct: bool | None = None) -> list[dict]
    record_usage(self, entry_id: str, success: bool = True) -> bool
    record_feedback(self, entry_id: str, feedback: str) -> bool
    update_usage_count(self, entry_id: str) -> bool
    get_success_boost(self, entry_id: str) -> float
    backfill_embeddings(self, batch_size: int = 100) -> dict[str, int]
    get_statistics(self) -> dict[str, Any]
    query_by_time_range(self, start_time: datetime, end_time: datetime, limit: int = 100) -> list[dict]
    query_evolution_by_topic(self, topic: str, limit: int = 100) -> list[dict]
    query_beliefs_at_time(self, target_time: datetime, limit: int = 100) -> list[dict]
    query_conflicts_over_time(self, topic: str, limit: int = 100) -> list[dict]
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
CKS = patch_hybrid_search(CKS)
CKS = patch_optimized_search(CKS)
migrate_from_legacy(source_db_paths: list[Path]) -> dict[str, int]
get_cks() -> CKS
ingest_memory(question: str, answer: str, source_chunk: str | None = None) -> str
ingest_pattern(title: str, content: str, source_chunk: str | None = None) -> str
search(query: str, entry_type: str | None = None, limit: int = 5) -> list[dict]
search_semantic(query: str, entry_type: str | None = None, limit: int = 5, expand_query: bool = False, fusion_method: str | None = None, diversity: float | None = None) -> list[dict]
ingest_correction(title: str, content: str) -> str
ingest_decision(title: str, content: str) -> str
ingest_commitment(title: str, content: str) -> str
ingest_insight(title: str, content: str) -> str
ingest_learning(title: str, content: str) -> str
from .optimized_search import patch_optimized_search
CKS = patch_optimized_search(CKS)
import warnings
```


### P:\packages\search-research\core\cks\usage_tracker.py

```python
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from search_research.contrib.semantic_daemon.daemon_client import DaemonClient
DEFAULT_STALE_DAYS = int(os.environ.get("CKS_STALE_DAYS", "90"))
get_stale_entries(days: int | None = None, limit: int = 50) -> list[dict]
format_stale_report(stale_entries: list[dict]) -> str
record_access(entry_ids: list[str]) -> None
import argparse
parser = argparse.ArgumentParser(description="Detect stale CKS entries")
args = parser.parse_args()
stale = get_stale_entries(days=args.days, limit=args.limit)
```


### P:\packages\search-research\core\cks\utils\__init__.py

```python
from .constitutional_validator import ConstitutionalValidator
from .dual_sink_logger import (
    DualSinkLogger, get_dual_sink_logger, get_logger, log_operation, log_technical_error, log_user_message, shutdown_logging, )
__all__ = [
    "ConstitutionalValidator",
    "DualSinkLogger",
    "get_dual_sink_logger",
    "get_logger",
    "log_operation",
    "log_technical_error",
    "log_user_message",
    "shutdown_logging",
]
```


### P:\packages\search-research\core\cks\utils\constitutional_validator.py

```python
import logging
import time
from dataclasses import dataclass
from typing import Any

@dataclass
class ConstitutionalMetric:
    name = str
    value = float
    threshold = float
    description = str
    constitutional_basis = str

class ConstitutionalValidator:
    __init__(self) -> None
    validate_storage_config(self, config) -> bool
    calculate_storage_compliance_score(self, storage_manager) -> float
    validate_operation(self, operation_type: str, operation_data: dict[str, Any]) -> dict[str, Any]
    get_compliance_report(self) -> dict[str, Any]
```


### P:\packages\search-research\core\cks\utils\dual_sink_logger.py

```python
import json
import logging
import logging.handlers
import os
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import rich.console
import rich.logging
sanitize_error_context(context: dict) -> dict

class StructuredFileFormatter(logging.Formatter):
    format(self, record: logging.LogRecord) -> str

class CleanConsoleFormatter(logging.Formatter):
    __init__(self) -> None
    format(self, record: logging.LogRecord) -> str

class DualSinkLogger:
    __init__(self, log_dir: Path | None = None, console: rich.console.Console | None = None, debug_enabled: bool | None = None) -> None
    get_logger(self, name: str) -> logging.Logger
    log_user_message(self, level: int, message: str) -> None
    log_technical_error(self, error: Exception, context: dict[str, Any] | None = None) -> None
    log_operation(self, operation: str, message: str, level: int = logging.DEBUG) -> None
    shutdown(self) -> None
get_dual_sink_logger() -> DualSinkLogger
get_logger(name: str) -> logging.Logger
log_user_message(level: int, message: str) -> None
log_technical_error(error: Exception, context: dict[str, Any] | None = None) -> None
log_operation(operation: str, message: str, level: int = logging.DEBUG) -> None
shutdown_logging() -> None
```


### P:\packages\search-research\core\cli.py

```python
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from .config import ResearchConfig, config
core_root = Path(__file__).resolve().parent
from core.config import ResearchConfig, config
from research_skill.cli_shared import (
        _create_timing_result, format_result_as_json, save_result_to_file, )
format_result_as_json(result: dict) -> str
save_result_to_file(result: dict, filepath: str) -> None
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
args_to_config(args: argparse.Namespace) -> ResearchConfig
create_research_engine(args: argparse.Namespace | None = None) -> Any

class SaturationDetector:
    __init__(self, query: str, min_results: int = 5, saturation_threshold: float = 0.15)
    add_result(self, title: str, content: str) -> dict
    get_status(self) -> dict

class CoreResearchCommand:
    __init__(self, fast_mode: bool = False) -> None
    create_parser(self) -> argparse.ArgumentParser
    execute_research(self, query: str, mode: str = "auto") -> dict[str, Any]
```


### P:\packages\search-research\core\config.py

```python
import logging
import os
from pathlib import Path
logger = logging.getLogger(__name__)

class Config:
    @property
    ENV_PATHS(self) -> list[str]
    @classmethod
    validate_path(cls, path_str: str, context: str = "") -> bool
    @classmethod
    get_validated_paths(cls, path_strs: list[str], context: str = "") -> list[Path]
config = Config()
__all__ = ["Config", "ResearchConfig", "config"]
from dataclasses import dataclass, field

@dataclass
class ResearchConfig:
    __post_init__(self)
    validate(self) -> list[str]
```


### P:\packages\search-research\core\diversity.py

```python
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class DiversityConfig:
    pass
compute_similarity(result1: dict[str, Any], result2: dict[str, Any], content_field: str = "content") -> float
mmr_rerank(results: list[dict[str, Any]], lambda_param: float = 0.7, content_field: str = "content", similarity_fn: Callable[[dict[str, Any], dict[str, Any]], float] | None = None, add_metadata: bool = False) -> list[dict[str, Any]]
filter_redundant(results: list[dict[str, Any]], threshold: float = 0.9, content_field: str = "content") -> list[dict[str, Any]]
get_diverse_subset(results: list[dict[str, Any]], n: int, lambda_param: float = 0.5, content_field: str = "content") -> list[dict[str, Any]]
```


### P:\packages\search-research\core\enhancement\__init__.py

```python
from .enhanced_dependency_analyzer import (
    QueryDependencies, ResearchDepth, SimplifiedDependencyAnalyzer, )
from .learning_system import LearningSystem, PatternInsight, ResearchFeedback
from .mode_relationship_mapper import ModeCombination, ModeRelationshipMapper, ResearchMode
from .multi_mode_orchestrator import (
    ExecutionStatus, ModeExecutionResult, MultiModeOrchestrator, OrchestratedResult, )
from .quality_optimizer import OptimizationResult, QualityPredictor
__all__ = [
    "SimplifiedDependencyAnalyzer",
    "QueryDependencies",
    "ResearchDepth",
    "LearningSystem",
    "PatternInsight",
    "ResearchFeedback",
    "ModeRelationshipMapper",
    "ResearchMode",
    "ModeCombination",
    "MultiModeOrchestrator",
    "ExecutionStatus",
    "ModeExecutionResult",
    "OrchestratedResult",
    "QualityPredictor",
    "OptimizationResult",
]
```


### P:\packages\search-research\core\enhancement\enhanced_dependency_analyzer.py

```python
import re
from dataclasses import dataclass
from enum import Enum

class ResearchDepth(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class QueryDependencies:
    __post_init__(self) -> None

class SimplifiedDependencyAnalyzer:
    __init__(self) -> None
    analyze_dependencies(self, query: str, tsk_context: dict | None = None) -> QueryDependencies
    get_dependency_summary(self, dependencies: QueryDependencies) -> dict
analyzer = SimplifiedDependencyAnalyzer()
test_queries = [
        "react hooks implementation example",
        "github repository microservices architecture",
        "machine learning research papers comparison",
        "best practices for API security",
        "academic study on distributed systems scalability",
        "how to implement oauth2 with jwt tokens",
        "docker production deployment strategies",
        "typescript typescript generic types tutorial"
    ]
deps = analyzer.analyze_dependencies(query)
summary = analyzer.get_dependency_summary(deps)
```


### P:\packages\search-research\core\enhancement\learning_system.py

```python
import json
import os
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, cast

@dataclass
class ResearchFeedback:
    research_id = str
    query = str
    modes_used = list[str]
    predicted_quality = float
    actual_quality_rating = float
    helpful_aspects = list[str]
    improvement_suggestions = list[str]
    sources_helpful = list[str]
    sources_missing = list[str]
    timestamp = datetime
    session_duration = float
    user_expertise_level = str
    research_domain = str

@dataclass
class PatternInsight:
    pattern_type = str
    confidence = float
    recommendation = str
    supporting_evidence = list[str]
    last_updated = datetime

class LearningSystem:
    __init__(self, feedback_file: str = "research_feedback.json")
    collect_feedback(self, research_id: str, query: str, modes_used: list[str], predicted_quality: float, actual_quality_rating: float, helpful_aspects: list[str] | None = None, improvement_suggestions: list[str] | None = None, sources_helpful: list[str] | None = None, sources_missing: list[str] | None = None, session_duration: float = 0.0, user_expertise_level: str = "intermediate", research_domain: str = "general") -> None
    get_pattern_based_recommendation(self, query: str, candidate_modes: list[str], domain: str | None = None, expertise: str | None = None) -> dict | None
    get_mode_performance_stats(self) -> dict[str, dict]
    get_recent_feedback(self, days: int = 30) -> list[ResearchFeedback]
    get_learning_summary(self) -> dict[str, Any]
    export_patterns(self, filename: str | None = None) -> str
learning_system = LearningSystem("test_feedback.json")
test_feedback = [
        {
            "query": "react hooks implementation example",
            "modes": ["octocode"],
            "predicted_quality": 0.85,
            "actual_rating": 4.2,
            "helpful": ["code examples", "github repos"],
            "domain": "technical",
            "expertise": "intermediate"
        },
        {
            "query": "microservices security best practices",
            "modes": ["octocode", "web", "multi-model"],
            "predicted_quality": 0.92,
            "actual_rating": 4.7,
            "helpful": ["diverse perspectives", "comprehensive coverage"],
            "domain": "technical",
            "expertise": "expert"
        },
        {
            "query": "machine learning academic papers",
            "modes": ["web"],
            "predicted_quality": 0.78,
            "actual_rating": 3.8,
            "missing": ["more recent papers", "comprehensive analysis"],
            "domain": "academic",
            "expertise": "expert"
        },
        {
            "query": "docker tutorial beginner",
            "modes": ["web", "octocode"],
            "predicted_quality": 0.88,
            "actual_rating": 4.5,
            "helpful": ["step by step guide", "practical examples"],
            "domain": "technical",
            "expertise": "beginner"
        },
        {
            "query": "react hooks implementation example",
            "modes": ["octocode", "web"],
            "predicted_quality": 0.90,
            "actual_rating": 4.6,
            "helpful": ["comprehensive coverage", "multiple examples"],
            "domain": "technical",
            "expertise": "intermediate"
        }
    ]
test_queries = [
        ("react hooks example", ["octocode", "web"], "technical", "intermediate"),
        ("microservices security patterns", ["octocode", "web", "multi-model"], "technical", "expert"),
        ("docker tutorial", ["web", "octocode"], "technical", "beginner")
    ]
recommendation = learning_system.get_pattern_based_recommendation(
            query, candidate_modes, domain, expertise
        )
summary = learning_system.get_learning_summary()
mode_stats = learning_system.get_mode_performance_stats()
export_file = learning_system.export_patterns("test_patterns.json")
```


### P:\packages\search-research\core\enhancement\mode_relationship_mapper.py

```python
from dataclasses import dataclass
from enum import Enum
from .enhanced_dependency_analyzer import QueryDependencies, ResearchDepth

class ResearchMode(Enum):
    OCTOCODE = "octocode"
    WEB = "web"
    MULTI_MODEL = "multi-model"
    COGNITIVE = "cognitive-enhanced"

@dataclass
class ModeCombination:
    modes = list[ResearchMode]
    predicted_quality = float
    estimated_cost = float
    redundancy_score = float
    coverage_score = float

class ModeRelationshipMapper:
    __init__(self) -> None
    find_optimal_combination(self, dependencies: QueryDependencies, budget_limit: float | None = None) -> ModeCombination
    explain_selection(self, combination: ModeCombination, dependencies: QueryDependencies) -> dict
from .enhanced_dependency_analyzer import SimplifiedDependencyAnalyzer
mapper = ModeRelationshipMapper()
analyzer = SimplifiedDependencyAnalyzer()
test_scenarios = [
        "react hooks implementation example",
        "github repository microservices architecture comparison",
        "machine learning research papers best practices",
        "docker production deployment enterprise security",
    ]
deps = analyzer.analyze_dependencies(query)
combination = mapper.find_optimal_combination(deps)
explanation = mapper.explain_selection(combination, deps)
```


### P:\packages\search-research\core\enhancement\multi_mode_orchestrator.py

```python
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from .mode_relationship_mapper import ModeCombination, ResearchMode

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class ModeExecutionResult:
    mode = ResearchMode
    status = ExecutionStatus
    execution_time = float
    sources_found = int
    results = list[dict[str, Any]]
    confidence = float

@dataclass
class OrchestratedResult:
    query = str
    modes_executed = list[ResearchMode]
    individual_results = dict[str, ModeExecutionResult]
    synthesized_results = dict[str, Any]
    execution_summary = dict[str, Any]
    orchestration_metadata = dict[str, Any]

class MultiModeOrchestrator:
    __init__(self, timeout_per_mode: int = 60, max_parallel_modes: int = 4)
    execute_research(self, query: str, combination: ModeCombination, tsk_context: dict | None = None) -> OrchestratedResult
    get_execution_statistics(self) -> dict[str, Any]
from .mode_relationship_mapper import ModeCombination
orchestrator = MultiModeOrchestrator()
single_mode_combo = ModeCombination(
        modes=[ResearchMode.OCTOCODE],
        predicted_quality=0.85,
        estimated_cost=1.5,
        redundancy_score=0.0,
        coverage_score=0.8
    )
multi_mode_combo = ModeCombination(
        modes=[ResearchMode.OCTOCODE, ResearchMode.WEB, ResearchMode.MULTI_MODEL],
        predicted_quality=0.92,
        estimated_cost=5.5,
        redundancy_score=0.3,
        coverage_score=0.95
    )
test_orchestration() -> None
```


### P:\packages\search-research\core\enhancement\quality_optimizer.py

```python
from dataclasses import dataclass
from .enhanced_dependency_analyzer import QueryDependencies, ResearchDepth
from .mode_relationship_mapper import ModeCombination, ResearchMode

@dataclass
class OptimizationResult:
    recommended_combination = ModeCombination
    alternatives = list[ModeCombination]
    optimization_reasoning = str
    budget_usage = float
    quality_vs_cost_tradeoff = str

class QualityPredictor:
    __init__(self) -> None
    predict_combination_quality(self, combination: ModeCombination, dependencies: QueryDependencies, domain: str | None = None) -> float

class CostBenefitOptimizer:
    __init__(self) -> None
    optimize_for_budget(self, combinations: list[ModeCombination], dependencies: QueryDependencies, budget_limit: float, domain: str | None = None) -> OptimizationResult
    optimize_for_value(self, combinations: list[ModeCombination], budget_limit: float, dependencies: QueryDependencies) -> OptimizationResult
from .enhanced_dependency_analyzer import SimplifiedDependencyAnalyzer
from .mode_relationship_mapper import ModeCombination, ModeRelationshipMapper
analyzer = SimplifiedDependencyAnalyzer()
mapper = ModeRelationshipMapper()
quality_predictor = QualityPredictor()
optimizer = CostBenefitOptimizer()
test_cases = [
        {
            "query": "react hooks implementation example",
            "budget": 2.0,
            "domain": "technical"
        },
        {
            "query": "enterprise microservices security patterns comparison",
            "budget": 5.0,
            "domain": "analysis"
        },
        {
            "query": "academic papers on machine learning ethics",
            "budget": 2.5,
            "domain": "academic"
        }
    ]
deps = analyzer.analyze_dependencies(query)
candidate_modes = mapper._get_candidate_modes(deps)
combinations = mapper._generate_combinations(candidate_modes, deps)
scored_combinations = []
temp_combination = ModeCombination(
                modes=combo_modes,
                predicted_quality=0.0,
                estimated_cost=sum(optimizer.cost_factors.get(mode, 1.0) for mode in combo_modes),
                redundancy_score=0.0,
                coverage_score=0.0
            )
result = optimizer.optimize_for_budget(scored_combinations, deps, budget, domain)
```


### P:\packages\search-research\core\faceted.py

```python
import logging
from datetime import datetime
from typing import Any
logger = logging.getLogger(__name__)
filter_results(results: list[Any], sources: list[str] | None = None, types: list[str] | None = None, after: datetime | None = None, before: datetime | None = None, min_score: float | None = None, custom_filter: callable | None = None, file_paths: list[str] | None = None, categories: list[str] | None = None, skill_sources: list[str] | None = None) -> list[Any]
get_facets(results: list[Any]) -> dict[str, dict[str, int]]
```


### P:\packages\search-research\core\faiss_lock.py

```python
import time
from pathlib import Path
import faiss

class FAISSLockTimeoutError(PermissionError):
    __init__(self, path: str | Path, attempts: int, elapsed: float)
faiss_open_read(path: str | Path, timeout: float = 5.0) -> faiss.Index
```


### P:\packages\search-research\core\fetchers\__init__.py

```python
from .batch import BatchURLFetcher, FetchedContent
from .validator import ContentSecurityValidator
from .vision import VisionAnalyzer, VisionAnalysisResult
__all__ = [
    "BatchURLFetcher",
    "FetchedContent",
    "ContentSecurityValidator",
    "VisionAnalyzer",
    "VisionAnalysisResult",
]
```


### P:\packages\search-research\core\fetchers\batch.py

```python
import asyncio
from dataclasses import dataclass

@dataclass
class FetchedContent:
    content = str | None
    url = str
    fetch_time = float

class BatchURLFetcher:
    __init__(self, max_concurrent: int = 5, timeout: int = 10, max_size: int | None = None)
    fetch_urls(self, urls: list[str]) -> dict[str, tuple[str | None, float]]
    get_statistics(self) -> dict[str, int]
    reset_statistics(self) -> None
```


### P:\packages\search-research\core\fetchers\validator.py

```python
import re

class ContentSecurityValidator:
    DANGEROUS_PATTERNS = [
        r"onclick\s*=",
        r"onerror\s*=",
        r"onload\s*=",
        r"onmouseover\s*=",
        r"eval\s*\(",
        r"<script[^>]*>",
        r"javascript:",
        r"vbscript:",
        r"data:",
    ]
    BLOCKED_DOMAINS = {
        "ads.doubleclick.net",
        "doubleclick.net",
        "googleads.com",
        "googlesyndication.com",
        "facebook.com/tr",
        "facebookpixel.com",
        "tracking.example.com",
    }
    SAFE_CONTENT_TYPES = {
        "text/html",
        "text/plain",
        "text/markdown",
        "text/xml",
        "application/json",
        "application/xml",
        "text/css",
        "text/javascript",
        "application/javascript",
    }
    UNSAFE_PROTOCOLS = {
        "file:",
        "javascript:",
        "data:",
        "ftp:",
        "vbscript:",
        "mailto:",
        "telnet:",
    }
    __init__(self, max_url_length: int = 2048, max_content_size: int = 1024 * 1024)
    validate_url(self, url: str | None) -> tuple[bool, str | None]
    validate_content(self, content: str, content_type: str = "text/html") -> tuple[bool, str | None]
```


### P:\packages\search-research\core\fetchers\vision.py

```python
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin
logger = logging.getLogger(__name__)

@dataclass
class VisionAnalysis:
    image_url = str
    description = str
    detected_text = str
    confidence = float
    metadata = dict[str, Any]
    __post_init__(self)

class VisionAnalyzer:
    __init__(self, api_key: str | None = None)
    analyze_images(self, html_content: str, base_url: str, max_images: int = 3) -> list[VisionAnalysis]
    analyze_with_llm(self, image_url: str, prompt: str = "Describe this image in detail.") -> VisionAnalysis | None
extract_and_analyze_images(html_content: str, base_url: str, max_images: int = 3) -> list[VisionAnalysis]
VisionAnalysisResult = VisionAnalysis
```


### P:\packages\search-research\core\handoff_chain.py

```python
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

@dataclass
class HandoffChainEntry:
    session_id = str
    transcript_path = Path
    parent_transcript_path = Path | None
    created = datetime | None

@dataclass
class HandoffChainResult:
    entries = list[HandoffChainEntry]
    depth = int
    origin_session_id = str | None
walk_handoff_chain(session_id: str, terminal_id: str | None = None, max_depth: int = 20) -> HandoffChainResult
walk_handoff_chain_simple(session_id: str, terminal_id: str | None = None, max_depth: int = 20) -> HandoffChainResult
```


### P:\packages\search-research\core\health_status.py

```python
from dataclasses import asdict, dataclass
from typing import Any, Literal

@dataclass
class HealthStatus:
    status = Literal["pass", "warning", "fail"]
    reachable = bool
    working = bool
    has_data = bool
    message = str
    details = dict[str, Any]
    to_dict(self) -> dict[str, Any]
```


### P:\packages\search-research\core\history_chain.py

```python
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

@dataclass
class ChainEntry:
    uuid = str
    parent_uuid = str | None
    session_id = str
    entry_type = str
    message = str | dict | None
    summary = str | None
    leaf_uuid = str | None
    created = datetime | None

@dataclass
class ChainWalkResult:
    entries = list[ChainEntry]
    depth = int
    origin_session_id = str | None
    compacted_sessions = set[str]
    index_age = datetime | None

class UUIDIndex:
    __init__(self, history_path: Path | None = None) -> None
    @property
    built_at(self) -> datetime | None
    build(self) -> None
    get(self, uuid: str) -> dict[str, Any] | None
load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict[str, Any]]
session_file_exists(session_id: str, project_path: str | Path | None = None, _sessions_index: dict[str, dict[str, Any]] | None = None) -> bool
walk_chain(start_uuid: str | None = None, session_id: str | None = None, index: UUIDIndex | None = None, project_path: str | Path | None = None, depth: int = 200, summary_only: bool = False) -> ChainWalkResult
format_chain_summary(result: ChainWalkResult) -> str
get_index() -> UUIDIndex
walk_chain_simple(session_id: str | None = None, start_uuid: str | None = None, depth: int = 200, summary_only: bool = True) -> ChainWalkResult
```


### P:\packages\search-research\core\http_client.py

```python
from typing import Any, Final
import httpx
get_async_client() -> httpx.AsyncClient
```


### P:\packages\search-research\core\hybrid_ensemble.py

```python
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from .hyde_multi_perspective_comprehensive import (
    MultiHyDEConfig, MultiHypotheticalDocuments, generate_multi_hypothetical_documents, )
from .hyde_single import (
    HypotheticalDocument, generate_hypothetical_document, )
from .models import SearchResult

@dataclass
class EnsembleResult:
    combined_results = list[SearchResult]
    sources_used = dict[str, int]

@dataclass
class HybridEnsembleConfig:
    __post_init__(self)
reciprocal_rank_fusion(results_lists: list[list[SearchResult]], k: int = 60, max_results: int | None = None) -> list[SearchResult]
weighted_average_fusion(results_lists: list[list[SearchResult]], weights: dict[str, float] | None = None, max_results: int | None = None) -> list[SearchResult]
run_hybrid_ensemble(query: str, config: HybridEnsembleConfig | None = None) -> EnsembleResult
__all__ = [
    "SearchResult",
    "EnsembleResult",
    "HybridEnsembleConfig",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "run_hybrid_ensemble",
]
```


### P:\packages\search-research\core\hyde.py

```python
import logging
import re
import functools
logger = logging.getLogger(__name__)
extract_key_phrases(doc: str) -> list[str]
enhance_query(query: str, key_phrases: list[str]) -> str
@functools.lru_cache(maxsize=128)
apply_hyde(query: str, hyde_content: str | None = None) -> tuple[str, bool]
```


### P:\packages\search-research\core\hyde_chapters.py

```python
from dataclasses import dataclass

@dataclass
class HydeChapterConfig:
    pass

@dataclass
class HydeChapter:
    title = str
    content = str
    search_focus = str
generate_hyde_chapters(query: str, num_chapters: int = 3, detail_level: str = "medium", enable_diversity: bool = True) -> list[HydeChapter]
```


### P:\packages\search-research\core\hyde_chapters_comprehensive.py

```python
from dataclasses import dataclass

@dataclass
class HydeChapter:
    title = str
    content = str
    search_focus = str
    __eq__(self, other: object) -> bool
    __repr__(self) -> str

@dataclass
class HydeChapterConfig:
    pass
generate_hyde_chapters(query: str, num_chapters: int = 3, detail_level: str = "medium", enable_diversity: bool = True, use_web_search: bool = False, model_type: str = "glm") -> list[HydeChapter]
```


### P:\packages\search-research\core\hyde_engine\__init__.py

```python
from .engine import HyDEEngine
__all__ = [
    "HyDEEngine",
]
```


### P:\packages\search-research\core\hyde_engine\engine.py

```python
from typing import Any
import functools
import asyncio

class HyDEResearchEngine:
    enhance_query(self, query: str, mode: str = "confidence") -> dict[str, Any]

class HyDEEngine:
    __init__(self, mode: str = "confidence")
    get_available_modes(self) -> list[str]
    enhance_query(self, query: str) -> "EnhancedQuery"
```


### P:\packages\search-research\core\hyde_engine\generator.py

```python
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

@dataclass(frozen=True)
class QueryIntent:
    category = str
    domain = str
    complexity = str
    keywords = tuple[str, ...]
    entities = tuple[str, ...]
    has_code_context = bool

class QueryAnalyzer:
    __slots__ = ()
    @classmethod
    analyze(cls, query: str) -> QueryIntent

@dataclass(slots=True)
class DocumentTemplate:
    intent = QueryIntent
    generate_content(self, query: str) -> str

@dataclass(slots=True)
class HyDEGenerator:
    generate(self, query: str, context: str = "", max_length: int = 500) -> str
    batch_generate(self, queries: list[str], context: str = "") -> list[str]
get_default_generator() -> HyDEGenerator
generate_hyde(query: str, context: str = "", max_length: int = 500) -> str
```


### P:\packages\search-research\core\hyde_engine\scoring.py

```python
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

class PhraseExtractor:
    __slots__ = ()
    @classmethod
    extract(cls, text: str, count: int = 5, min_length: int = 3, max_length: int = 30) -> list[str]

@dataclass
class RelevanceMetrics:
    semantic_overlap = float
    length_score = float
    specificity = float
    coherence = float
    technical_depth = float
    overall_score = float
    __slots__ = (
        "semantic_overlap",
        "length_score",
        "specificity",
        "coherence",
        "technical_depth",
        "overall_score",
    )
    to_dict(self) -> dict[str, float]

class HyDEQualityScorer:
    __slots__ = ()
    @classmethod
    score(cls, query: str, hyde: str, weights: dict[str, float] | None = None) -> RelevanceMetrics

class QueryEnhancer:
    __slots__ = ()
    @classmethod
    enhance(cls, query: str, hyde_doc: str | None = None, phrase_count: int = 5) -> str
extract_key_phrases(hyde_doc: str, count: int = 5, min_length: int = 3, max_length: int = 30) -> list[str]
enhance_query(query: str, hyde_doc: str | None = None, phrase_count: int = 5) -> str
score_hyde_quality(query: str, hyde: str, weights: dict[str, float] | None = None) -> float
get_detailed_metrics(query: str, hyde: str, weights: dict[str, float] | None = None) -> RelevanceMetrics
```


### P:\packages\search-research\core\hyde_multi_perspective.py

```python
import time
from dataclasses import dataclass, field

@dataclass
class MultiHyDEConfig:
    pass

@dataclass
class HypotheticalDocument:
    query = str
    content = str

@dataclass
class MultiHypotheticalDocuments:
    query = str
    documents = list[HypotheticalDocument]
    perspectives = list[str]
    get_document_by_perspective(self, perspective: str) -> HypotheticalDocument | None
    get_combined_content(self) -> str
generate_multi_hypothetical_documents(query: str, config: MultiHyDEConfig | None = None) -> MultiHypotheticalDocuments
```


### P:\packages\search-research\core\hyde_multi_perspective_comprehensive.py

```python
import time
from dataclasses import dataclass, field
from .hyde_single import (
    HypotheticalDocument, _count_tokens, _count_words, )
import importlib.util
GLM_AVAILABLE = importlib.util.find_spec("csf.llm_providers") is not None
GLM_AVAILABLE = False

@dataclass
class MultiHypotheticalDocuments:
    query = str
    __repr__(self)
    get_document_by_perspective(self, perspective: str) -> HypotheticalDocument | None
    get_combined_content(self, separator: str = "\n\n---\n\n") -> str

@dataclass
class MultiHyDEConfig:
    __post_init__(self)
generate_multi_hypothetical_documents(query: str, config: MultiHyDEConfig | None = None) -> MultiHypotheticalDocuments
__all__ = [
    "MultiHypotheticalDocuments",
    "MultiHyDEConfig",
    "generate_multi_hypothetical_documents",
    "_get_perspective_prompt",
    "GLM_AVAILABLE",
]
```


### P:\packages\search-research\core\hyde_retrieval.py

```python
from typing import TYPE_CHECKING, Any
from .hyde_single import HypotheticalDocument
import time
from dataclasses import dataclass, field

@dataclass
class HyDERetrievalConfig:
    pass

@dataclass
class HyDERetrievalResult:
    results = list[dict[str, Any]]
    hypothetical_document = dict[str, Any]
    original_query = str
    hyde_used_for_retrieval = bool
    retrieval_query = str
    __repr__(self) -> str
extract_retrieval_query(hypothetical_document: HypotheticalDocument, config: HyDERetrievalConfig) -> str
baseline_search(query: str, limit: int = 10) -> list[dict[str, Any]]
search_with_hyde(query: str, config: HyDERetrievalConfig | None = None) -> HyDERetrievalResult
```


### P:\packages\search-research\core\hyde_single.py

```python
from dataclasses import dataclass

@dataclass
class HypotheticalDocument:
    query = str
    content = str
    __repr__(self)

@dataclass
class HyDEConfig:
    pass
create_hypothetical_document(query: str, content: str, config: HyDEConfig | None = None) -> HypotheticalDocument
generate_hypothetical_document(query: str, content: str | None = None, config: HyDEConfig | None = None) -> HypotheticalDocument
```


### P:\packages\search-research\core\intent_classifier.py

```python
import json
from pathlib import Path
from typing import Literal
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
classify_intent(text: str) -> IntentCategory
__all__ = ["classify_intent", "IntentCategory"]
```


### P:\packages\search-research\core\kg\__init__.py

```python

```


### P:\packages\search-research\core\kg\backend.py

```python
import json
import logging
from pathlib import Path
from typing import Any
SearchResult = dict[str, Any]
BACKEND_KG = "KG"
logger = logging.getLogger(__name__)
DEFAULT_KG_PATH = "P:/projects/kg_builder/knowledge_graph_output"

class KGBackend:
    __init__(self, kg_data_path: str | None = None)
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
```


### P:\packages\search-research\core\kg\kg_boosting.py

```python
import json
import os
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any
DEFAULT_ALLOWED_ENTITY_TYPES = {"TECHNOLOGY", "COMMAND", "CSF"}
load_kg_affinity_data(kg_data_path: str) -> dict[str, set[str]]
load_kg_entity_type_data(kg_data_path: str) -> dict[str, str]
get_allowed_entity_types() -> set[str]
calculate_affinity_boost(result_entities: list[str], query_entities: list[str], entity_to_convs: dict[str, set[str]]) -> float
extract_entities_from_query(query: str, known_entities: set[str]) -> list[str]
filter_entities_by_type(entities: list[str], entity_to_types: dict[str, str], allowed_types: set[str]) -> list[str]
get_boost_alpha() -> float
apply_kg_boosting(results: list[dict[str, Any]], query: str, entity_to_convs: dict[str, set[str]], entity_to_types: dict[str, str] | None = None, boosting_enabled: bool | None = None, debug_mode: bool = False) -> list[dict[str, Any]]
```


### P:\packages\search-research\core\kg\research_backend.py

```python
from pathlib import Path
from typing import Any
SearchResult = dict[str, Any]
BACKEND_KG = "KG"
DEFAULT_KG_PATH = "P:/projects/kg_builder/knowledge_graph_output"

class KGBackend:
    __init__(self, kg_data_path: str | None = None)
    @property
    kg_data_path(self)
    build_index(self) -> None
    search(self, query: str, limit: int = 10) -> list[SearchResult]
__all__ = ["BACKEND_KG", "KGBackend"]
```


### P:\packages\search-research\core\kg_boosting.py

```python
import json
import os
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Set, Any
DEFAULT_ALLOWED_ENTITY_TYPES = {"TECHNOLOGY", "COMMAND", "CSF"}
load_kg_affinity_data(kg_data_path: str) -> Dict[str, Set[str]]
load_kg_entity_type_data(kg_data_path: str) -> Dict[str, str]
get_allowed_entity_types() -> Set[str]
calculate_affinity_boost(result_entities: List[str], query_entities: List[str], entity_to_convs: Dict[str, Set[str]]) -> float
extract_entities_from_query(query: str, known_entities: Set[str]) -> List[str]
filter_entities_by_type(entities: List[str], entity_to_types: Dict[str, str], allowed_types: Set[str]) -> List[str]
get_boost_alpha() -> float
apply_kg_boosting(results: List[Dict[str, Any]], query: str, entity_to_convs: Dict[str, Set[str]], entity_to_types: Dict[str, str] | None = None, boosting_enabled: bool | None = None, debug_mode: bool = False) -> List[Dict[str, Any]]
```


### P:\packages\search-research\core\llm\__init__.py

```python
from core.hyde_engine.generator import HyDEGenerator
from .provider_manager import get_research_llm_manager
__all__ = [
    "HyDEGenerator",
    "get_research_llm_manager",
]
```


### P:\packages\search-research\core\llm\provider_manager.py

```python
from typing import Any
import logging
logger = logging.getLogger(__name__)
get_research_llm_manager() -> Any
generate_with_fallback(prompt: str, system_prompt: str | None = None, max_tokens: int = 2000, temperature: float = 0.7) -> tuple[str, bool]
```


### P:\packages\search-research\core\mcp_server.py

```python
import functools
import logging
import time
from collections.abc import Callable
from typing import Any
from mcp.server.fastmcp import FastMCP
from .cks.unified import CKS
from .quality_checker import QualityConfig
from .router_async import AsyncSearchRouter, SearchResult
from .unified_router import UnifiedAsyncRouter
logger = logging.getLogger(__name__)
mcp = FastMCP("search-research")
@mcp.tool(description="Unified search across local and web sources with intelligent routing")
unified_search(query: str, mode: str = "auto", limit: int = 30, min_score: float = 0.5, min_results: int = 3) -> str
@mcp.tool(description="Fast local-only search across codebase, knowledge base, and docs")
local_search(query: str, limit: int = 30, min_score: float = 0.0) -> str
@mcp.tool(description="Web-only search across multiple providers (Tavily, Serper, Exa, Brave)")
web_search(query: str, limit: int = 30) -> str
@mcp.tool(description="Search the Constitutional Knowledge System (CKS) using full-text search")
cks_search(query: str, entry_type: str | None = None, limit: int = 10) -> str
@mcp.tool(description="Search CKS using semantic/vector search with embeddings")
cks_search_semantic(query: str, entry_type: str | None = None, limit: int = 10, expand_query: bool = False) -> str
@mcp.tool(description="Ingest knowledge into the Constitutional Knowledge System")
cks_ingest(content: str, title: str | None = None, entry_type: str = "knowledge", category: str | None = None) -> str
@mcp.tool(description="Get statistics about the Constitutional Knowledge System")
cks_stats() -> str
main() -> None
```


### P:\packages\search-research\core\metrics.py

```python
import json
import queue
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

class ComponentName(str, Enum):
    QMD_WIKI = "QMD_WIKI"
    YT_IS = "YT_IS"
    CLAUDE_HISTORY = "CLAUDE_HISTORY"
    HYDE = "HYDE"
    SEARCH_PROVIDER = "SEARCH_PROVIDER"
    SYNTHESIS = "SYNTHESIS"
    CONTRADICTION = "CONTRADICTION"
    COVERAGE_GATE = "COVERAGE_GATE"
    CRAG_GRADE = "CRAG_GRADE"

@dataclass
class ComponentMetric:
    timestamp = str
    component = ComponentName
    latency_ms = float
    tokens_used = int
    cache_hit = bool
    output_quality = float
    to_jsonl(self) -> str

class MetricsLogger:
    __init__(self, log_path: str = "logs/metrics.jsonl", max_size_mb: float = 10, queue_size: int = 1000)
    log(self, metric: ComponentMetric) -> None
    log_component(self, component: ComponentName, latency_ms: float, tokens_used: int = 0, quality: float = 0.0, cache_hit: bool = False, branch: str = "main") -> None
    flush(self) -> None
```


### P:\packages\search-research\core\models.py

```python
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class SearchResult:
    title = str
    content = str
    source = str
    score = float
    __post_init__(self)
    @property
    id(self) -> str
    to_dict(self) -> dict[str, Any]
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> SearchResult
    @classmethod
    from_web_result(cls, url: str, title: str, content: str, source: str, score: float, fetched: bool = False, fetch_time: float | None = None, metadata: dict[str, Any] | None = None) -> SearchResult
    @classmethod
    from_local_result(cls, file_path: str, title: str, content: str, source: str, score: float, line_number: int | None = None, metadata: dict[str, Any] | None = None) -> SearchResult

@dataclass
class ResearchResult:
    query = str
    enhanced_query = str | None
    expanded_queries = list[str]
    results = list[SearchResult]
    sources_used = list[str]
    fetched_urls = int
    vision_analysis = list[dict[str, Any]]
    synthesis = str
    processing_time = float
    hyde_enabled = bool
    hyde_mode = str | None
    multi_hyde_enabled = bool
    chapters_enabled = bool
    ensemble_enabled = bool
    ensemble_method = str | None
    metadata = dict[str, Any]

@dataclass
class EnhancedQuery:
    original = str
    enhanced = str
    hypothetical_document = str
    vector = list[float]
    confidence = float
```


### P:\packages\search-research\core\modes.py

```python
from enum import Enum

class Mode(Enum):
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"
    __str__(self) -> str
    @property
    is_fast(self) -> bool
    @property
    is_comprehensive(self) -> bool
    @property
    is_custom(self) -> bool
    @property
    timeout(self) -> float
    @property
    includes_web(self) -> bool
    @property
    includes_local(self) -> bool
    @property
    uses_hyde(self) -> bool
FAST = Mode.FAST
COMPREHENSIVE = Mode.COMPREHENSIVE
CUSTOM = Mode.CUSTOM
```


### P:\packages\search-research\core\orchestration\__init__.py

```python
from .cost_tracker import CostTracker
from .phase_controller import PhaseController, PhaseResult
__all__ = [
    "PhaseController",
    "PhaseResult",
    "CostTracker",
]
```


### P:\packages\search-research\core\orchestration\cost_tracker.py

```python
from dataclasses import dataclass

@dataclass
class CostTracker:
    budget = float
    __post_init__(self) -> None
    track_search(self, provider: str, num_results: int = 0, num_requests: int = 1) -> bool
    is_budget_exceeded(self) -> bool
    reset(self) -> None
    get_remaining(self) -> float
```


### P:\packages\search-research\core\orchestration\phase_controller.py

```python
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any
from ..analysis.density_calculator import DensityCalculator
from ..analysis.gap_analyzer import CoverageGap, GapAnalyzer
from ..analysis.topic_clusterer import NoveltyTracker, TopicClusterer
from ..query import NormalizedResult, ResultNormalizer
from .cost_tracker import CostTracker
logger = logging.getLogger(__name__)

@dataclass
class PhaseResult:
    phase = int
    total_results = int
    iterations = int
    cost = float
    novelty_score = float
    density_score = float

class PhaseController:
    __init__(self, search_provider: Any, normalizer: ResultNormalizer | None = None, budget: float = 1.0, max_iterations: int = 5, novelty_threshold: float = 0.05, results_per_iteration: int = 20) -> None
    execute_phase_one(self, query: str) -> PhaseResult
    execute_phase_two(self, query: str) -> PhaseResult
    research(self, query: str) -> PhaseResult
```


### P:\packages\search-research\core\orchestrator.py

```python
import asyncio
import logging
import time
from typing import Any
logger = logging.getLogger(__name__)
from .config import ResearchConfig
from .fetchers.batch import BatchURLFetcher
from .fetchers.validator import ContentSecurityValidator
from .hyde_engine import HyDEEngine
from .models import ResearchResult
from .processors.ensemble import HybridEnsembleConfig
from .query.expander import QueryExpander

class ResearchEngine:
    __init__(self, config: ResearchConfig | None = None)
    register_backend(self, backend: Any) -> None
    register_provider(self, provider: Any) -> None
    research(self, query: str) -> ResearchResult
```


### P:\packages\search-research\core\processing\__init__.py

```python
from .result_normalizer import NormalizedResult, ResultNormalizer, SourceType
__all__ = [
    "ResultNormalizer",
    "NormalizedResult",
    "SourceType",
]
```


### P:\packages\search-research\core\processing\got_analysis.py

```python
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class GotNode:
    text = str
    node_type = str
    source_result_id = str

@dataclass
class GotEdge:
    from_id = str
    to_id = str
    edge_type = str
    strength = float

@dataclass
class GotCluster:
    cluster_id = str
    label = str
    result_ids = list[str]
    nodes = list[GotNode]
    confidence = float

class GotAnalyzer:
    CONSTRAINT_PATTERNS = [
        r'\bmust\b', r'\bshould\b', r'\brequired\b', r'\bneed\b',
        r'\bonly\b', r'\bnever\b', r'\balways\b'
    ]
    IDEA_PATTERNS = [
        r'\bcan\b', r'\bcould\b', r'\bmight\b', r'\bmay\b',
        r'\bsuggest\b', r'\brecommend\b', r'\bpropose\b'
    ]
    RISK_PATTERNS = [
        r'\brisk\b', r'\bdanger\b', r'\bwarning\b', r'\bcaution\b',
        r'\bproblem\b', r'\bissue\b', r'\berror\b', r'\bfail\b'
    ]
    __init__(self, min_cluster_size: int = 2, min_edge_strength: float = 0.3)
    extract_nodes_from_result(self, result: Any, result_id: str) -> list[GotNode]
    analyze_results(self, results: list[Any]) -> dict[str, Any]
    format_results_with_got(self, results: list[Any], got_analysis: dict[str, Any]) -> str
```


### P:\packages\search-research\core\processing\result_normalizer.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

class SourceType(Enum):
    DOCS = "docs"
    ACADEMIC = "academic"
    COMMUNITY = "community"
    NEWS = "news"
    VENDOR = "vendor"
    VIDEO = "video"
    BLOG = "blog"
    UNKNOWN = "unknown"

@dataclass
class NormalizedResult:
    title = str
    snippet = str
    url = str
    domain = str
    source_type = SourceType
    provider = str

class ResultNormalizer:
    DOMAIN_TRUST = {
        "docs.python.org": 0.95,
        "developer.mozilla.org": 0.95,
        "python.org": 0.90,
        "arxiv.org": 0.90,
        "ieee.org": 0.90,
        "acm.org": 0.90,
        "github.com": 0.80,
        "stackoverflow.com": 0.75,
        "reddit.com": 0.60,
        "medium.com": 0.50,
    }
    VIDEO_PATTERNS = ["youtube.com", "vimeo.com", "video."]
    ACADEMIC_PATTERNS = ["arxiv.org", "ieee.org", "acm.org", "springer.com", "sciencedirect.com"]
    COMMUNITY_PATTERNS = ["reddit.com", "stackoverflow.com", "github.com", "discord.com"]
    NEWS_PATTERNS = ["news", "bbc.com", "cnn.com", "reuters.com", "apnews.com", "npr.org"]
    DOCS_PATTERNS = ["docs.", "documentation", "/docs/", "/doc/"]
    VENDOR_PATTERNS = ["cloud.google.com", "aws.amazon.com", "azure.microsoft.com", "developer.vmware.com"]
    BLOG_PATTERNS = ["/blog/", "medium.com", "dev.to", "hashnode.dev", "substack.com"]
    __init__(self) -> None
    normalize(self, raw_result: dict, provider: str) -> NormalizedResult
    normalize_batch(self, raw_results: list[dict], provider: str) -> list[NormalizedResult]
```


### P:\packages\search-research\core\processors\__init__.py

```python
from .ensemble import (
    HybridEnsembleConfig, EnsembleResult, reciprocal_rank_fusion, weighted_average_fusion, run_hybrid_ensemble, )
from .reranking import (
    maximal_marginal_relevance, apply_temporal_boosting, calculate_temporal_boost, )
from .deduplication import DeduplicationProcessor
from .synthesis import SynthesisProcessor
from .ranking import RankingProcessor
from .pipeline import ResultProcessingPipeline
__all__ = [
    "HybridEnsembleConfig",
    "EnsembleResult",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "run_hybrid_ensemble",
    "maximal_marginal_relevance",
    "apply_temporal_boosting",
    "calculate_temporal_boost",
    "DeduplicationProcessor",
    "SynthesisProcessor",
    "RankingProcessor",
    "ResultProcessingPipeline",
]
```


### P:\packages\search-research\core\processors\deduplication.py

```python
from collections import defaultdict

class DeduplicationProcessor:
    __init__(self, similarity_threshold: float = 0.6, normalize_urls: bool = True)
    deduplicate_by_url(self, results: list, aggregate_sources: bool = False) -> list
    deduplicate_by_title(self, results: list) -> list
    deduplicate_by_content(self, results: list) -> list
    deduplicate(self, results: list) -> list
```


### P:\packages\search-research\core\processors\ensemble.py

```python
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

@dataclass
class HybridEnsembleConfig:
    __post_init__(self)

@dataclass
class EnsembleResult:
    combined_results = list
    sources_used = dict
reciprocal_rank_fusion(result_lists: list[list], k: int = 60, max_results: int | None = None) -> list
weighted_average_fusion(result_lists: list[list], weights: dict[str, float] | None = None, max_results: int | None = None) -> list
run_hybrid_ensemble(query: str, config: HybridEnsembleConfig | None = None) -> EnsembleResult
```


### P:\packages\search-research\core\processors\pipeline.py

```python
from typing import Any
from .deduplication import DeduplicationProcessor
from .ensemble import EnsembleResult
from .ranking import RankingProcessor
from .synthesis import SynthesisProcessor

class ResultProcessingPipeline:
    __init__(self, enable_deduplication: bool = True, enable_ranking: bool = True, enable_temporal_boosting: bool = False, dedup_similarity_threshold: float = 0.6, source_weights: dict[str, float] | None = None, freshness_half_life: int = 180)
    process(self, results: list, query: str = "", skip_errors: bool = False) -> list
    process_with_synthesis(self, results: list, query: str = "", use_fetched_content: bool = False) -> dict[str, Any]
    process_ensemble_result(self, ensemble_result: EnsembleResult, query: str = "") -> list
```


### P:\packages\search-research\core\processors\ranking.py

```python
from datetime import datetime, timezone
import math

class RankingProcessor:
    __init__(self, source_weights: dict[str, float] | None = None, freshness_half_life: int = 180)
    rank_by_relevance(self, results: list, limit: int | None = None) -> list
    rank_by_source_quality(self, results: list) -> list
    rank_by_freshness(self, results: list, limit: int | None = None) -> list
    rank_combined(self, results: list, weights: dict[str, float] | None = None, limit: int | None = None) -> list
```


### P:\packages\search-research\core\processors\reranking.py

```python
from datetime import datetime, timezone
from typing import Any, Callable
import math
maximal_marginal_relevance(query: str, results: list, lambda_param: float = 0.5, limit: int | None = None, get_similarity_func: Callable[[Any, Any], float] | None = None) -> list
calculate_temporal_boost(entry: dict[str, Any], half_life_days: int = 180) -> float
apply_temporal_boosting(results: list, half_life_days: int = 180) -> list
```


### P:\packages\search-research\core\processors\synthesis.py

```python
import re
from typing import Any

class SynthesisProcessor:
    __init__(self, max_summary_length: int = 500, max_insights: int = 5)
    combine_results(self, results: list, query: str = "") -> str
    generate_summary(self, results: list, max_length: int | None = None) -> str
    extract_key_insights(self, results: list, max_insights: int | None = None) -> list[str]
    synthesize_with_fetched(self, results: list, query: str = "") -> str
    synthesize_structured(self, results: list, query: str = "") -> dict[str, Any]
    synthesize_with_citations(self, results: list, query: str = "") -> str
```


### P:\packages\search-research\core\providers\__init__.py

```python
from .base_web import BaseWebBackend, ProviderError, ProviderNotAvailableError
from .bing import BingBackend
from .brave import BraveBackend
from .exa import ExaBackend
from .google import GoogleBackend
from .kagi import KagiBackend
from .mojeek import MojeekBackend
from .serper import SerperBackend
from .tavily import TavilyBackend
from .you import YouBackend
__all__ = [
    "BaseWebBackend",
    "ProviderError",
    "ProviderNotAvailableError",
    "TavilyBackend",
    "SerperBackend",
    "ExaBackend",
    "BraveBackend",
    "BingBackend",
    "GoogleBackend",
    "KagiBackend",
    "YouBackend",
    "MojeekBackend",
]
```


### P:\packages\search-research\core\providers\base_web.py

```python
import abc
import logging
import os
from typing import Any
from .provider_health import ProviderHealthStatus
logger = logging.getLogger(__name__)

class BaseWebBackend(abc.ABC):
    @property
    @abc.abstractmethod
    name(self) -> str
    @property
    @abc.abstractmethod
    requires_api_key(self) -> bool
    @property
    @abc.abstractmethod
    api_key_env_var(self) -> str
    @abc.abstractmethod
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict[str, Any]]
    validate_api_key(self) -> bool
    is_available(self) -> bool
    check_health(self, timeout: float = 5.0) -> dict[str, Any]
    close(self) -> None

class ProviderError(Exception):
    __init__(self, provider: str, message: str)

class ProviderNotAvailableError(ProviderError):
    __init__(self, provider: str, api_key_env_var: str)
```


### P:\packages\search-research\core\providers\bing.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .bing_client import BingClient as BingClientImpl
logger = logging.getLogger(__name__)

class BingBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    validate_api_key(self) -> bool
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\bing_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class BingSearchResult:
    title = str
    url = str
    content = str

@dataclass
class BingSearchResponse:
    query = str
    results = list[BingSearchResult]

class BingClient:
    API_BASE = "https://api.bing.microsoft.com/v7.0/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None) -> BingSearchResponse
    close(self)
    @staticmethod
    validate_api_key_format(api_key: str | None = None) -> bool
search(query: str, api_key: str | None = None, max_results: int = 10) -> BingSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> BingSearchResponse
```


### P:\packages\search-research\core\providers\brave.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .brave_client import BraveClient as BraveClientImpl
logger = logging.getLogger(__name__)

class BraveBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\brave_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class BraveSearchResult:
    title = str
    url = str
    content = str

@dataclass
class BraveSearchResponse:
    query = str
    results = list[BraveSearchResult]

class BraveClient:
    API_BASE = "https://api.search.brave.com/res/v1/web/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None, timeout: float | None = None) -> BraveSearchResponse
    close(self)
search(query: str, api_key: str | None = None, max_results: int = 10) -> BraveSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> BraveSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\exa.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .exa_client import ExaClient as ExaClientImpl
logger = logging.getLogger(__name__)

class ExaBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    validate_api_key(self) -> bool
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\exa_client.py

```python
import logging
import os
from dataclasses import dataclass
from typing import Any
from exa_py import Exa as ExaSDK
logger = logging.getLogger(__name__)

@dataclass
class ExaSearchResult:
    title = str
    url = str
    score = float

@dataclass
class ExaSearchResponse:
    query = str
    results = list[ExaSearchResult]

class ExaClient:
    DEFAULT_MAX_RESULTS = 10
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS)
    search(self, query: str, max_results: int | None = None) -> ExaSearchResponse
    close(self)
search(query: str, api_key: str | None = None, max_results: int = 10) -> ExaSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> ExaSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\google.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .google_client import GoogleClient as GoogleClientImpl
logger = logging.getLogger(__name__)

class GoogleBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    validate_api_key(self) -> bool
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\google_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class GoogleSearchResult:
    title = str
    url = str
    content = str

@dataclass
class GoogleSearchResponse:
    query = str
    results = list[GoogleSearchResult]

class GoogleClient:
    API_BASE = "https://www.googleapis.com/customsearch/v1"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0
    __init__(self, api_key: str | None = None, cx: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None) -> dict[str, Any]
    close(self)
search(query: str, api_key: str | None = None, cx: str | None = None, max_results: int = 10) -> dict[str, Any]
search_sync(query: str, api_key: str | None = None, cx: str | None = None, max_results: int = 10) -> dict[str, Any]
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\kagi.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .kagi_client import KagiClient as KagiClientImpl
logger = logging.getLogger(__name__)

class KagiBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    validate_api_key(self) -> bool
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\kagi_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class KagiSearchResult:
    title = str
    url = str
    content = str

@dataclass
class KagiSearchResponse:
    query = str
    results = list[KagiSearchResult]

class KagiClient:
    API_BASE = "https://kagi.com/api/v0/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT, limit: str = "kagi")
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None) -> KagiSearchResponse
    close(self)
search(query: str, api_key: str | None = None, max_results: int = 10) -> KagiSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> KagiSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\mojeek.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .mojeek_client import MojeekClient as MojeekClientImpl
logger = logging.getLogger(__name__)

class MojeekBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\mojeek_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class MojeekSearchResult:
    title = str
    url = str
    content = str

@dataclass
class MojeekSearchResponse:
    query = str
    results = list[MojeekSearchResult]

class MojeekClient:
    API_BASE = "https://api.mojeek.com/search/api"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None, timeout: float | None = None) -> MojeekSearchResponse
    close(self)
search(query: str, api_key: str | None = None, max_results: int = 10) -> MojeekSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> MojeekSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\provider_health.py

```python
from dataclasses import dataclass

@dataclass
class ProviderHealthStatus:
    healthy = bool
    latency_ms = float
```


### P:\packages\search-research\core\providers\serper.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .serper_client import SerperClient as SerperClientImpl
logger = logging.getLogger(__name__)

class SerperBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    validate_api_key(self) -> bool
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\serper_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
from search_research.http_client import get_async_client
logger = logging.getLogger(__name__)

@dataclass
class SerperSearchResult:
    title = str
    url = str
    content = str

@dataclass
class SerperSearchResponse:
    query = str
    results = list[SerperSearchResult]

class SerperClient:
    API_BASE = "https://google.serper.dev/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None) -> SerperSearchResponse
search(query: str, api_key: str | None = None, max_results: int = 10) -> SerperSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> SerperSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\tavily.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .tavily_client import TavilyClient as TavilyClientImpl
logger = logging.getLogger(__name__)

class TavilyBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\tavily_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
from search_research.http_client import get_async_client
logger = logging.getLogger(__name__)

@dataclass
class TavilySearchResult:
    title = str
    url = str
    content = str

@dataclass
class TavilySearchResponse:
    query = str
    results = list[TavilySearchResult]

class TavilyClient:
    API_BASE = "https://api.tavily.com/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT, search_depth: str = "basic", include_answer: bool = False, include_raw_content: bool = False, include_images: bool = False, include_image_descriptions: bool = False)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None, search_depth: str | None = None) -> TavilySearchResponse
search(query: str, api_key: str | None = None, max_results: int = 10) -> TavilySearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> TavilySearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\providers\you.py

```python
import logging
import os
from .base_web import BaseWebBackend
from .you_client import YouClient as YouClientImpl
logger = logging.getLogger(__name__)

class YouBackend(BaseWebBackend):
    @property
    name(self) -> str
    @property
    requires_api_key(self) -> bool
    @property
    api_key_env_var(self) -> str
    __init__(self, api_key: str | None = None, max_results: int = 10)
    search(self, query: str, max_results: int = 10, timeout: float = 5.0) -> list[dict]
    close(self)
```


### P:\packages\search-research\core\providers\you_client.py

```python
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any
import httpx
logger = logging.getLogger(__name__)

@dataclass
class YouSearchResult:
    title = str
    url = str
    content = str

@dataclass
class YouSearchResponse:
    query = str
    results = list[YouSearchResult]

class YouClient:
    API_BASE = "https://api.you.com/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0
    __init__(self, api_key: str | None = None, max_results: int = DEFAULT_MAX_RESULTS, timeout: float = DEFAULT_TIMEOUT)
    __aenter__(self)
    __aexit__(self)
    search(self, query: str, max_results: int | None = None) -> YouSearchResponse
    close(self)
search(query: str, api_key: str | None = None, max_results: int = 10) -> YouSearchResponse
search_sync(query: str, api_key: str | None = None, max_results: int = 10) -> YouSearchResponse
validate_api_key(api_key: str | None = None) -> bool
```


### P:\packages\search-research\core\quality_checker.py

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
BOUNDARY_TOLERANCE_SECONDS = 1.0
SECONDS_PER_HOUR = 3600.0

@dataclass
class QualityConfig:
    pass
is_satisfactory(result: dict[str, Any], config: QualityConfig | None = None) -> bool
```


### P:\packages\search-research\core\query\__init__.py

```python
from .abbreviations import get_abbreviation_mappings
from .expander import (
    QueryExpander, expand_query_if_enabled, get_query_suggestions, )
from .normalizer import (
    NormalizedResult, ResultNormalizer, SourceType, )
from .synonyms import get_synonym_mappings
__all__ = [
    # Normalizer
    "NormalizedResult",
    "ResultNormalizer",
    "SourceType",
    # Expander
    "QueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    # Mappings
    "get_synonym_mappings",
    "get_abbreviation_mappings",
]
```


### P:\packages\search-research\core\query\abbreviations.py

```python
get_abbreviation_mappings() -> dict[str, str]
expand_abbreviation(abbr: str) -> str
```


### P:\packages\search-research\core\query\expander.py

```python
import re
import functools
from .abbreviations import get_abbreviation_mappings
from .synonyms import get_synonym_mappings

class QueryExpander:
    __init__(self, custom_synonyms: dict[str, list[str]] | None = None)
    @functools.lru_cache(maxsize=128)
    expand_query(self, query: str, entity_slug: str | None = None, max_variations: int = 5) -> list[str]
expand_query_if_enabled(query: str, enabled: bool = True) -> list[str]
get_query_suggestions(partial: str, limit: int = 5) -> list[str]
__all__ = [
    "QueryExpander",
    "ENTITY_TERMS",
    "DOMAIN_EXPANSIONS",
    "expand_query_if_enabled",
    "get_query_suggestions",
]
```


### P:\packages\search-research\core\query\expansion\__init__.py

```python
from .expander import QueryExpander, expand_query_if_enabled, get_query_suggestions
from .synonyms import get_synonym_mappings
from .abbreviations import get_abbreviation_mappings, expand_abbreviation
from .auto_learning import AutoLearningQueryExpander
__all__ = [
    "QueryExpander",
    "AutoLearningQueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    "get_synonym_mappings",
    "get_abbreviation_mappings",
    "expand_abbreviation",
]
```


### P:\packages\search-research\core\query\expansion\abbreviations.py

```python
from typing import Dict
get_abbreviation_mappings() -> Dict[str, str]
expand_abbreviation(abbr: str) -> str
```


### P:\packages\search-research\core\query\expansion\auto_learning.py

```python
import re
from typing import Any, Dict, List
from dataclasses import dataclass

@dataclass
class LearnedMapping:
    term = str
    expansion = str
    source_url = str
    confidence = float
    occurrences = int

class AutoLearningQueryExpander:
    ABBREV_PATTERN = re.compile(r"\b([A-Z]{2,})\s*\(([^)]+)\)")
    __init__(self, dry_run: bool = False)
    learn_from_results(self, query: str, successful_results: List[Any]) -> Dict[str, Any]
    get_learned_mappings(self) -> Dict[str, Dict[str, Any]]
    list_learned_terms(self) -> List[Dict[str, Any]]
```


### P:\packages\search-research\core\query\expansion\expander.py

```python
import re
from typing import Dict, List
from .synonyms import get_synonym_mappings
from .abbreviations import get_abbreviation_mappings

class QueryExpander:
    __init__(self, custom_synonyms: Dict[str, List[str]] | None = None)
    expand_query(self, query: str, entity_slug: str | None = None, max_variations: int = 5) -> List[str]
expand_query_if_enabled(query: str, enabled: bool = True) -> List[str]
get_query_suggestions(partial: str, limit: int = 5) -> List[str]
```


### P:\packages\search-research\core\query\expansion\synonyms.py

```python
from typing import Dict, List
get_synonym_mappings() -> Dict[str, List[str]]
```


### P:\packages\search-research\core\query\normalizer.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

class SourceType(Enum):
    DOCS = "docs"
    ACADEMIC = "academic"
    COMMUNITY = "community"
    NEWS = "news"
    VENDOR = "vendor"
    VIDEO = "video"
    BLOG = "blog"
    UNKNOWN = "unknown"

@dataclass
class NormalizedResult:
    title = str
    snippet = str
    url = str
    domain = str
    source_type = SourceType
    provider = str

class ResultNormalizer:
    DOMAIN_TRUST = {
        "docs.python.org": 0.95,
        "developer.mozilla.org": 0.95,
        "python.org": 0.90,
        "arxiv.org": 0.90,
        "ieee.org": 0.90,
        "acm.org": 0.90,
        "github.com": 0.80,
        "stackoverflow.com": 0.75,
        "reddit.com": 0.60,
        "medium.com": 0.50,
    }
    VIDEO_PATTERNS = ["youtube.com", "vimeo.com", "video."]
    ACADEMIC_PATTERNS = ["arxiv.org", "ieee.org", "acm.org", "springer.com", "sciencedirect.com"]
    COMMUNITY_PATTERNS = ["reddit.com", "stackoverflow.com", "github.com", "discord.com"]
    NEWS_PATTERNS = ["news", "bbc.com", "cnn.com", "reuters.com", "apnews.com", "npr.org"]
    DOCS_PATTERNS = ["docs.", "documentation", "/docs/", "/doc/"]
    VENDOR_PATTERNS = ["cloud.google.com", "aws.amazon.com", "azure.microsoft.com", "developer.vmware.com"]
    BLOG_PATTERNS = ["/blog/", "medium.com", "dev.to", "hashnode.dev", "substack.com"]
    __init__(self)
    normalize(self, raw_result: dict, provider: str) -> NormalizedResult
    normalize_batch(self, raw_results: list[dict], provider: str) -> list[NormalizedResult]
```


### P:\packages\search-research\core\query\synonyms.py

```python
get_synonym_mappings() -> dict[str, list[str]]
```


### P:\packages\search-research\core\query_intent.py

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import sys
from pathlib import Path
from shared.intent_classifier import classify_intent, IntentCategory

class IntentType(Enum):
    NAVIGATIONAL = "navigational"
    INFORMATIONAL = "informational"
    TECHNICAL = "technical"
    EXPLORATORY = "exploratory"
    UNKNOWN = "unknown"

@dataclass
class IntentClassification:
    intent = IntentType
classify_query_intent(query: str) -> IntentClassification
get_intent_description(intent: IntentType) -> str

class QueryIntent(Enum):
    CODE = "code"
    KNOWLEDGE = "knowledge"
    CHS = "chs"
    GREP = "grep"

@dataclass
class IntentDetection:
    primary = QueryIntent

class QueryIntentDetector:
    __init__(self)
    detect(self, query: str) -> IntentDetection
    get_preferred_backends(self, intent: IntentDetection) -> list[str]
```


### P:\packages\search-research\core\ranking\__init__.py

```python

```


### P:\packages\search-research\core\research\__init__.py

```python
__all__ = []
```


### P:\packages\search-research\core\research\ai_distiller_health_check.py

```python
import importlib
import sys
from pathlib import Path
from typing import Any
project_root = Path(__file__).resolve().parent.parent.parent.parent
check_ai_distiller_health() -> dict[str, Any]
check_ai_distiller_module() -> dict[str, Any]
check_knowledge_processing() -> dict[str, Any]
check_distillation_pipelines() -> dict[str, Any]
check_knowledge_base_connectivity() -> dict[str, Any]
main()
```


### P:\packages\search-research\core\research\citations.py

```python
import re
from typing import Any
extract_citations(text: str) -> dict[str, Any]
```


### P:\packages\search-research\core\research\findings.py

```python
from src.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding
rca_finding(summary: str, details: str, category: str = "BUG", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
debug_finding(summary: str, details: str, category: str = "BUG", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
tdd_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
arch_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
security_finding(summary: str, details: str, category: str = "VULNERABILITY", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
quality_finding(summary: str, details: str, category: str = "PATTERN", file_path: str | None = None, line_number: int | None = None) -> DiagnosticFinding
store_quick_finding(skill: str, summary: str, details: str, category: str = "DISCOVERY", file_path: str | None = None, line_number: int | None = None) -> bool
batch_findings(findings: list[DiagnosticFinding]) -> dict[str, bool]
__all__ = [
    "rca_finding",
    "debug_finding",
    "tdd_finding",
    "arch_finding",
    "security_finding",
    "quality_finding",
    "store_quick_finding",
    "batch_findings",
    "DiagnosticFinding",
    "store_finding",
]
```


### P:\packages\search-research\core\research\helpers.py

```python
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

@dataclass
class DiagnosticFinding:
    category = str
    file_path = str | None
    line_number = int | None
    summary = str
    details = str
    skill_source = str
    to_metadata(self) -> dict[str, str | int]
    to_cks_entry(self) -> tuple[str, str, dict]
store_finding(finding: DiagnosticFinding) -> bool
```


### P:\packages\search-research\core\research\history.py

```python
import json
import sqlite3
import sys
query_file_history(file_path: str) -> list[dict]
```


### P:\packages\search-research\core\research\integration\__init__.py

```python
from .core import KnowledgeIntegrationEngine
from .models import (
    AdaptationStrategy, ApproachPrediction, ConfidenceLevel, EvidenceBasedRecommendation, ImplementationResult, ImplementationRoadmap, IntegrationStatus, KnowledgeIntegrationError, KnowledgePattern, KnowledgeQuery, PatternType, QueryResult, ReusablePattern, SessionContext, )
from .strategies import (
    PatternMatchingStrategy, SemanticPatternMatcher, StatisticalPatternMatcher, )
from .utils import (
    create_knowledge_integration_engine, get_recommendations_for_context, ingest_implementation_results, )
__version__ = "1.0.0"
__author__ = "CSF Team"
__all__ = [
    # Core classes
    "KnowledgeIntegrationEngine",
    "KnowledgeIntegrationError",
    # Pattern matching
    "PatternMatchingStrategy",
    "StatisticalPatternMatcher",
    "SemanticPatternMatcher",
    # Data models
    "ImplementationResult",
    "KnowledgePattern",
    "EvidenceBasedRecommendation",
    "KnowledgeQuery",
    "ReusablePattern",
    "ImplementationRoadmap",
    "ApproachPrediction",
    "AdaptationStrategy",
    # Enums and constants
    "IntegrationStatus",
    "PatternType",
    "ConfidenceLevel",
    # Utility classes
    "QueryResult",
    "SessionContext",
    # Factory functions
    "create_knowledge_integration_engine",
    "ingest_implementation_results",
    "get_recommendations_for_context",
]
```


### P:\packages\search-research\core\research\integration\core\__init__.py

```python
import json
import logging
import os
import re
import sqlite3
import statistics
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any
from ....lib.core_utils.knowledge.knowledge_query_engine import (
        KnowledgeQueryEngine, KnowledgeQueryError, )
from ....lib.helpfulness import HelpfulnessPattern
csf_AVAILABLE = True
csf_AVAILABLE = False
logger = logging.getLogger(__name__)

class KnowledgeIntegrationError(Exception):
    __init__(self, message: str, error_code: str | None = None, context: dict[str, Any] | None = None)

class IntegrationStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()

class PatternType(Enum):
    ARCHITECTURAL = "architectural"
    IMPLEMENTATION = "implementation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class ImplementationResult:
    implementation_id = str
    agent_type = str
    task_description = str
    outcome = str
    execution_time = float
    patterns_observed = list[str]
    techniques_used = list[str]
    challenges_faced = list[str]
    lessons_learned = list[str]
    code_metrics = dict[str, Any]

@dataclass
class KnowledgePattern:
    pattern_id = str
    pattern_type = PatternType
    name = str
    description = str
    confidence_score = float
    success_rate = float
    evidence = list[str]
    prerequisites = list[str]
    benefits = list[str]
    risks = list[str]
    implementation_examples = list[str]
    related_patterns = list[str]
    created_at = str
    last_updated = str

@dataclass
class EvidenceBasedRecommendation:
    recommendation_id = str
    title = str
    description = str
    confidence_level = ConfidenceLevel
    supporting_evidence = list[str]
    expected_outcome = str
    implementation_steps = list[str]
    risk_assessment = str
    alternatives = list[str]
    related_patterns = list[str]
    source_implementations = list[str]
    created_at = str

@dataclass
class KnowledgeQuery:
    query_id = str
    search_terms = list[str]
    context = str
    pattern_types = list[PatternType]
    confidence_threshold = float
    time_range = tuple[str, str]
    implementation_filter = dict[str, Any]
    sort_by = str
    limit = int
    include_metadata = bool

class PatternMatchingStrategy(ABC):
    @abstractmethod
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class StatisticalPatternMatcher(PatternMatchingStrategy):
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class SemanticPatternMatcher(PatternMatchingStrategy):
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class KnowledgeIntegrationEngine:
    __init__(self, helpful_engine: HelpfulnessPattern | None = None, knowledge_query_engine: KnowledgeQueryEngine | None = None, storage_path: str | None = None)
    automatic_knowledge_ingestion(self, implementation_results: ImplementationResult | list[ImplementationResult]) -> dict[str, Any]
    pattern_matching_algorithms(self, implementation_data: ImplementationResult | None = None) -> dict[str, Any]
    cross_implementation_learning(self, analysis_parameters: dict[str, Any] | None = None) -> dict[str, Any]
    evidence_based_recommendations(self, context: str, confidence_threshold: float = 0.5, limit: int = 10) -> dict[str, Any]
    knowledge_base_query(self, query: KnowledgeQuery | str | dict[str, Any]) -> dict[str, Any]
    get_integration_statistics(self) -> dict[str, Any]
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
```


### P:\packages\search-research\core\research\integration\strategies\__init__.py

```python
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import UTC, datetime
from ..models import (
    ImplementationResult, KnowledgePattern, PatternType, )

class PatternMatchingStrategy(ABC):
    @abstractmethod
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class StatisticalPatternMatcher(PatternMatchingStrategy):
    __init__(self)
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class SemanticPatternMatcher(PatternMatchingStrategy):
    __init__(self)
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]
```


### P:\packages\search-research\core\research\integration\utils\__init__.py

```python
import logging
from pathlib import Path
from ..core import KnowledgeIntegrationEngine
from ..models import (
    ImplementationResult, )
logger = logging.getLogger(__name__)
create_knowledge_integration_engine(helpful_engine = None, knowledge_query_engine = None, storage_path: str | None = None) -> KnowledgeIntegrationEngine
ingest_implementation_results(engine: KnowledgeIntegrationEngine, implementation_results: ImplementationResult | list[ImplementationResult]) -> dict[str, any]
get_recommendations_for_context(engine: KnowledgeIntegrationEngine, context: str, confidence_threshold: float = 0.5, limit: int = 10) -> dict[str, any]
```


### P:\packages\search-research\core\research\integration_engine.py

```python
import json
import logging
import sqlite3
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from ...lib.core_utils.knowledge.knowledge_query_engine import (
        KnowledgeQueryEngine, KnowledgeQueryError, )
from ...lib.helpfulness import HelpfulnessPattern
csf_AVAILABLE = True
csf_AVAILABLE = False
logger = logging.getLogger(__name__)

class KnowledgeIntegrationError(Exception):
    __init__(self, message: str, error_code: str = "INTEGRATION_ERROR", details: dict | None = None)
    __str__(self) -> str

class IntegrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"
    INDEXED = "indexed"

class PatternType(Enum):
    IMPLEMENTATION = "implementation"
    ARCHITECTURAL = "architectural"
    PERFORMANCE = "performance"
    SECURITY = "security"
    WORKFLOW = "workflow"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

class ConfidenceLevel(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

@dataclass
class ImplementationResult:
    implementation_id = str
    agent_type = str
    task_description = str
    outcome = str
    execution_time = float
    patterns_observed = list[str]
    techniques_used = list[str]
    challenges_faced = list[str]
    lessons_learned = list[str]
    code_metrics = dict[str, Any]
    user_feedback = str
    artifacts_created = list[str]
    dependencies_added = list[str]
    timestamp = str
    metadata = dict[str, Any]

@dataclass
class KnowledgePattern:
    pattern_id = str
    pattern_type = PatternType
    name = str
    description = str
    confidence_score = float
    success_rate = float
    evidence = list[str]
    prerequisites = list[str]
    benefits = list[str]
    risks = list[str]
    implementation_examples = list[str]
    related_patterns = list[str]
    created_at = str
    last_updated = str
    usage_count = int

@dataclass
class EvidenceBasedRecommendation:
    recommendation_id = str
    title = str
    description = str
    confidence_level = ConfidenceLevel
    supporting_evidence = list[str]
    expected_outcome = str
    implementation_steps = list[str]
    risk_assessment = str
    alternatives = list[str]
    related_patterns = list[str]
    source_implementations = list[str]
    created_at = str
    expires_at = str
    tags = list[str]

@dataclass
class KnowledgeQuery:
    query_id = str
    search_terms = list[str]
    context = str
    pattern_types = list[PatternType]
    confidence_threshold = float
    time_range = tuple[str, str]
    implementation_filter = dict[str, Any]
    sort_by = str
    limit = int
    include_metadata = bool

class PatternMatchingStrategy(ABC):
    @abstractmethod
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class StatisticalPatternMatcher(PatternMatchingStrategy):
    __init__(self)
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class SemanticPatternMatcher(PatternMatchingStrategy):
    __init__(self)
    match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]

class KnowledgeIntegrationEngine:
    __init__(self, helpful_engine: HelpfulnessPattern | None = None, knowledge_query_engine: KnowledgeQueryEngine | None = None, storage_path: str | None = None)
    automatic_knowledge_ingestion(self, implementation_results: ImplementationResult | list[ImplementationResult]) -> dict[str, Any]
    pattern_matching_algorithms(self, implementation_data: ImplementationResult | None = None) -> dict[str, Any]
    cross_implementation_learning(self, analysis_parameters: dict[str, Any] | None = None) -> dict[str, Any]
    evidence_based_recommendations(self, context: str, confidence_threshold: float = 0.5, limit: int = 10) -> dict[str, Any]
    knowledge_base_query(self, query: KnowledgeQuery | str | dict[str, Any]) -> dict[str, Any]
    get_integration_statistics(self) -> dict[str, Any]
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)

@dataclass
class ReusablePattern:
    pattern_id = str
    name = str
    description = str
    pattern_type = PatternType
    success_rate = float
    usage_count = int
    contexts = list[str]
    adaptation_complexity = float
    last_updated = datetime
    tags = set[str]
    to_dict(self) -> dict[str, Any]

@dataclass
class ImplementationRoadmap:
    roadmap_id = str
    title = str
    description = str
    target_pattern = str
    steps = list[dict[str, Any]]
    dependencies = list[str]
    estimated_duration = timedelta
    success_criteria = list[str]
    risk_factors = list[str]
    confidence_score = float
    created_at = datetime
    to_dict(self) -> dict[str, Any]

@dataclass
class ApproachPrediction:
    prediction_id = str
    context = str
    recommended_approach = str
    alternative_approaches = list[str]
    confidence_score = float
    success_probability = float
    reasoning = list[str]
    constraints = list[str]
    benefits = list[str]
    risks = list[str]
    historical_evidence = list[str]
    predicted_at = datetime
    to_dict(self) -> dict[str, Any]

@dataclass
class AdaptationStrategy:
    strategy_id = str
    source_pattern = str
    target_context = str
    adaptations = list[dict[str, Any]]
    impact_assessment = dict[str, float]
    implementation_guide = list[str]
    validation_criteria = list[str]
    rollback_strategy = str
    adaptation_complexity = float
    success_probability = float
    created_at = datetime
    to_dict(self) -> dict[str, Any]

class FutureImplementationEnabler:
    __init__(self, knowledge_engine: KnowledgeIntegrationEngine | None = None, ml_model_path: str | None = None, learning_rate: float = 0.01)
    identify_reusable_patterns(self, implementation_data: list[dict[str, Any]], context_domain: str, min_success_rate: float = 0.7) -> list[ReusablePattern]
    generate_implementation_roadmaps(self, target_patterns: list[str], context_requirements: dict[str, Any], complexity_preference: str = "balanced") -> list[ImplementationRoadmap]
    predict_optimal_approaches(self, implementation_context: dict[str, Any], available_patterns: list[str], constraints: dict[str, Any] | None = None) -> list[ApproachPrediction]
    enable_knowledge_transfer(self, source_patterns: list[str], target_contexts: list[str], transfer_strategy: str = "adaptive") -> dict[str, Any]
    create_adaptation_strategies(self, source_pattern: str, target_context: str, adaptation_needs: list[dict[str, Any]] | None = None) -> list[AdaptationStrategy]
    get_learning_metrics(self) -> dict[str, Any]
    provide_feedback(self, prediction_id: str, actual_outcome: str, feedback_score: float | None = None, comments: str | None = None) -> bool
    close(self) -> None
create_knowledge_integration_engine(helpful_engine: HelpfulnessPattern | None = None, knowledge_query_engine: KnowledgeQueryEngine | None = None, storage_path: str | None = None) -> KnowledgeIntegrationEngine
ingest_implementation_results(engine: KnowledgeIntegrationEngine, implementation_results: ImplementationResult | list[ImplementationResult]) -> dict[str, Any]
get_recommendations_for_context(engine: KnowledgeIntegrationEngine, context: str, confidence_threshold: float = 0.5, limit: int = 10) -> dict[str, Any]
__all__ = [
    "AdaptationStrategy",
    "ApproachPrediction",
    "ConfidenceLevel",
    "EvidenceBasedRecommendation",
    "FutureImplementationEnabler",
    "ImplementationResult",
    "ImplementationRoadmap",
    "IntegrationStatus",
    "KnowledgeIntegrationEngine",
    "KnowledgeIntegrationError",
    "KnowledgePattern",
    "KnowledgeQuery",
    "PatternType",
    "ReusablePattern",
    "create_knowledge_integration_engine",
    "get_recommendations_for_context",
    "ingest_implementation_results",
]
```


### P:\packages\search-research\core\research\knowledge_query_engine.py

```python
__all__ = []
```


### P:\packages\search-research\core\research\library_knowledge_service.py

```python
import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from ..database.sqlite_database_manager import SQLiteDatabaseManager
logger = logging.getLogger(__name__)

class LibraryKnowledgeError(Exception):
    __init__(self, message: str, error_code: str = "LIBRARY_ERROR", details: dict | None = None)
    __str__(self)

@dataclass
class LibraryPattern:
    library_name = str
    pattern_type = str
    title = str
    description = str
    __post_init__(self)
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> LibraryPattern
    to_dict(self) -> dict[str, Any]
    validate(self) -> None

@dataclass
class LibraryPatternSearchFilter:
    validate(self) -> None

@dataclass
class LibraryPatternCategory:
    name = str
    display_name = str
    description = str
    count = int
    last_updated = str

class LibraryKnowledgeService:
    __init__(self, db_manager: SQLiteDatabaseManager)
    create_pattern(self, pattern_data: dict[str, Any]) -> dict[str, Any]
    get_pattern_by_id(self, pattern_id: str) -> dict[str, Any] | None
    update_pattern(self, pattern_id: str, update_data: dict[str, Any]) -> dict[str, Any]
    delete_pattern(self, pattern_id: str) -> dict[str, Any]
    search_patterns(self, filter_config: LibraryPatternSearchFilter | None = None) -> dict[str, Any]
    get_pattern_categories(self) -> list[dict[str, Any]]
    batch_create_patterns(self, patterns_data: list[dict[str, Any]]) -> dict[str, Any]
    get_statistics(self) -> dict[str, Any]
    get_database_info(self) -> dict[str, Any]
    create_pattern_async(self, pattern_data: dict[str, Any]) -> dict[str, Any]
    get_pattern_by_id_async(self, pattern_id: str) -> dict[str, Any] | None
    update_pattern_async(self, pattern_id: str, update_data: dict[str, Any]) -> dict[str, Any]
    delete_pattern_async(self, pattern_id: str) -> dict[str, Any]
    search_patterns_async(self, filter_config: LibraryPatternSearchFilter | None = None) -> dict[str, Any]
    close(self) -> None
    __enter__(self)
    __exit__(self, exc_type, exc_val, exc_tb)
```


### P:\packages\search-research\core\research\orchestration_knowledge_service.py

```python
import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from ..database.sqlite_database_manager import SQLiteDatabaseManager
logger = logging.getLogger(__name__)

class OrchestrationKnowledgeError(Exception):
    __init__(self, message: str, error_code: str = "ORCHESTRATION_ERROR", details: dict | None = None)

@dataclass
class OrchestrationPattern:
    id = str
    pattern_type = str
    agents_involved = str
    description = str
    trigger_conditions = str
    coordination_logic = str
    success_criteria = str

@dataclass
class OrchestrationExecutionHistory:
    id = str
    pattern_id = str
    execution_timestamp = str
    execution_context = str
    agents_participated = str
    execution_result = str
    performance_metrics = str

@dataclass
class AgentCoordinationPattern:
    id = str
    primary_agent = str
    coordinating_agents = str
    coordination_type = str
    communication_protocol = str
    coordination_rules = str
    performance_optimization = str

@dataclass
class OrchestrationPatternSearchFilter:
    pass

class OrchestrationKnowledgeService:
    VALID_PATTERN_TYPES = {"coordination", "workflow", "collaboration", "routing"}
    VALID_COORDINATION_TYPES = {
        "hierarchical",
        "peer_to_peer",
        "event_driven",
        "message_queue",
        "shared_memory",
    }
    __init__(self, db_manager: SQLiteDatabaseManager)
    create_orchestration_pattern(self, pattern_data: dict[str, Any]) -> OrchestrationPattern
    get_orchestration_pattern_by_id(self, pattern_id: str) -> OrchestrationPattern
    update_orchestration_pattern(self, pattern_id: str, update_data: dict[str, Any]) -> OrchestrationPattern
    delete_orchestration_pattern(self, pattern_id: str) -> bool
    search_orchestration_patterns(self, search_filter: OrchestrationPatternSearchFilter) -> list[OrchestrationPattern]
    list_orchestration_patterns(self, limit: int = 50, offset: int = 0) -> list[OrchestrationPattern]
    get_patterns_by_workflow_type(self, workflow_type: str) -> list[OrchestrationPattern]
    increment_pattern_usage(self, pattern_id: str) -> OrchestrationPattern
    get_popular_patterns(self, limit: int = 10) -> list[OrchestrationPattern]
    record_execution_history(self, execution_data: dict[str, Any]) -> OrchestrationExecutionHistory
    get_execution_history(self, pattern_id: str, limit: int = 50) -> list[OrchestrationExecutionHistory]
    create_agent_coordination_pattern(self, coord_data: dict[str, Any]) -> AgentCoordinationPattern
    get_agent_coordination_pattern(self, pattern_id: str) -> AgentCoordinationPattern
    create_orchestration_pattern_async(self, pattern_data: dict[str, Any]) -> OrchestrationPattern
    get_orchestration_pattern_by_id_async(self, pattern_id: str) -> OrchestrationPattern
    search_orchestration_patterns_async(self, search_filter: OrchestrationPatternSearchFilter) -> list[OrchestrationPattern]
    record_execution_history_async(self, execution_data: dict[str, Any]) -> OrchestrationExecutionHistory
```


### P:\packages\search-research\core\research\research_flash\__init__.py

```python
from .query_engine import QueryResult, ResearchFlashEngine, ResearchResult
QueryEngine = ResearchFlashEngine
__all__ = [
    "QueryEngine",
    "QueryResult",
    "ResearchFlashEngine",
    "ResearchResult",
]
```


### P:\packages\search-research\core\research\research_flash\benchmark_models.py

```python
import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
import httpx
from dotenv import load_dotenv
PROMPT = (
    "Explain the difference between a mutex and a semaphore in operating systems. "
    "Include a practical code example in Python. Keep the response under 200 words."
)
GLM_CONFIG = {
    "name": "GLM-4.7 (Z.AI Max)",
    "model": "glm-4.7",
    "endpoint": "https://api.z.ai/api/coding/paas/v4/chat/completions",
    "api_key": os.environ.get("Z_AI_API_KEY", ""),  # Z_AI_API_KEY is the real key
    "headers": {
        "Authorization": f"Bearer {os.environ.get('Z_AI_API_KEY', '')}",
        "Content-Type": "application/json",
    },
}
MM_CONFIG = {
    "name": "MiniMax-M2.7",
    "model": "MiniMax-M2.7",
    "endpoint": "https://api.minimax.io/v1/chat/completions",
    "api_key": os.environ.get("MINIMAX_API_KEY", ""),
    "headers": {
        "Authorization": f"Bearer {os.environ.get('MINIMAX_API_KEY', '')}",
        "Content-Type": "application/json",
    },
}
TRIALS = 10
TRIM_PERCENT = 0.1

@dataclass
class TrialResult:
    ttft_ms = float
    total_ms = float
trim_mean(values: list[float], trim_pct: float) -> float
run_trial(client: httpx.Client, config: dict) -> TrialResult | None
run_benchmark(config: dict) -> dict[str, float]
compare_responses(model_a: dict, res_a: TrialResult, model_b: dict, res_b: TrialResult) -> None
main() -> None
```


### P:\packages\search-research\core\research\research_flash\glm_integration.py

```python
import logging
from dataclasses import dataclass, field
from typing import Any
from query_engine import QueryResult

@dataclass
class QueryResult:
    source = str
    title = str
    content = str

@dataclass(frozen=True)
class GLMConfig:
    pass

class GLMFlashIntegration:
    __init__(self, config: GLMConfig | None = None) -> None
    search_research(self, query: str, max_results: int = 10, source_types: list[str] | None = None) -> list[QueryResult]
    @property
    is_available(self) -> bool
    @property
    model_info(self) -> dict[str, Any]
```


### P:\packages\search-research\core\research\research_flash\query_engine.py

```python
import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent.parent

class MockCKSSource:
    __init__(self)
    search(self, query, max_results = 10)
from features.cks.cks_query_interface import CKSQueryInterface
CKS_AVAILABLE = True
CKS_AVAILABLE = False
CKSQueryInterface = MockCKSSource

class CHSSource:
    __init__(self)
    search(self, query, max_results = 10)
CHS_AVAILABLE = True

class ResultRanker:
    rank_results(self, results)

class ResultDeduplicator:
    deduplicate(self, results)

class ResultSynthesizer:
    __init__(self)
    synthesize(self, query, results, source_results = None)

class ResearchConfig:
    __init__(self)

@dataclass
class QueryResult:
    source = str
    title = str
    content = str

@dataclass
class ResearchResult:
    query = str
    sources_used = list[str]
    results = list[QueryResult]
    synthesis = str
    processing_time = float
    source_performance = dict[str, float]

class ResearchFlashEngine:
    __init__(self, config: ResearchConfig | None = None)
    query(self, query_text: str, sources: list[str] | None = None, max_results_per_source: int | None = None) -> ResearchResult
    format_results_markdown(self, result: ResearchResult) -> str
    get_available_sources(self) -> list[str]
    get_source_status(self) -> dict[str, bool]
```


### P:\packages\search-research\core\research\research_flash\query_engine_clean.py

```python
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from query_engine import QueryResult

@dataclass
class QueryResult:
    source = str
    title = str
    content = str

class MockCKSSource:
    __init__(self)
    connect(self)
    search(self, query, max_results = 5)

class MockCHSSource:
    __init__(self)
    search(self, query, max_results = 5)

class ResultRanker:
    rank_results(self, results)

class ResultDeduplicator:
    deduplicate(self, results)

class ResultSynthesizer:
    __init__(self)
    synthesize(self, query, results, source_results = None)

class ResearchConfig:
    __init__(self)

@dataclass
class ResearchResult:
    query = str
    sources_used = list[str]
    results = list[QueryResult]
    synthesis = str
    processing_time = float
    source_performance = dict[str, float]

class ResearchFlashEngine:
    __init__(self, config: ResearchConfig | None = None)
    query(self, query_text: str, sources: list[str] | None = None, max_results_per_source: int | None = None) -> ResearchResult
    get_available_sources(self) -> list[str]
    get_source_status(self) -> dict[str, bool]
    format_results_markdown(self, result: ResearchResult) -> str
```


### P:\packages\search-research\core\research\research_flash\test_integration.py

```python
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
project_root = Path(__file__).parent.parent.parent.parent

class IntegrationTester:
    __init__(self)
    log_test(self, test_name: str, passed: bool, message: str = "", details: dict = None)
    test_imports(self) -> bool
    test_cks_python_standards(self) -> bool
    test_glm_integration(self) -> bool
    test_research_engine(self) -> bool
    test_error_handling(self) -> bool
    run_all_tests(self) -> dict[str, Any]
main()
exit_code = asyncio.run(main())
```


### P:\packages\search-research\core\research\standards_knowledge_service.py

```python
import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from ..database.sqlite_database_manager import SQLiteDatabaseManager
logger = logging.getLogger(__name__)

class StandardsKnowledgeError(Exception):
    __init__(self, message: str, error_code: str = "STANDARDS_ERROR", details: dict[str, Any] | None = None)
    __str__(self) -> str

@dataclass
class StandardRule:
    standard_category = str
    rule_name = str
    description = str
    validation_logic = dict[str, Any]
    severity = str
    __post_init__(self) -> None
    @classmethod
    from_dict(cls, data: dict[str, Any]) -> StandardRule
    to_dict(self) -> dict[str, Any]
    validate(self) -> None

@dataclass
class StandardRuleSearchFilter:
    validate(self) -> None

@dataclass
class ValidationResult:
    rule_id = str
    rule_name = str
    passed = bool
    severity = str
    message = str
    details = dict[str, Any]
    execution_time = float
    timestamp = str
    to_dict(self) -> dict[str, Any]

@dataclass
class ComplianceReport:
    context = str
    total_rules = int
    passed_rules = int
    failed_rules = int
    error_count = int
    warning_count = int
    info_count = int
    overall_status = str
    validation_results = list[ValidationResult]
    execution_time = float
    timestamp = str
    to_dict(self) -> dict[str, Any]

class StandardsKnowledgeServiceInterface:
    create_rule(self, rule_data: dict[str, Any]) -> dict[str, Any]
    get_rule_by_id(self, rule_id: str) -> dict[str, Any] | None
    get_rule_by_name(self, standard_category: str, rule_name: str) -> dict[str, Any] | None
    update_rule(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]
    delete_rule(self, rule_id: str) -> dict[str, Any]
    search_rules(self, filter_config: StandardRuleSearchFilter | None = None) -> dict[str, Any]
    get_rules_by_context(self, context: str, active_only: bool = True) -> list[dict[str, Any]]
    get_rules_by_category(self, standard_category: str, active_only: bool = True) -> list[dict[str, Any]]
    validate_context(self, context: str, data: dict[str, Any]) -> ComplianceReport
    execute_validation_logic(self, rule: dict[str, Any], data: dict[str, Any]) -> ValidationResult
    get_statistics(self) -> dict[str, Any]
    batch_create_rules(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]

class StandardsKnowledgeService(StandardsKnowledgeServiceInterface):
    __init__(self, db_manager: SQLiteDatabaseManager)
    create_rule(self, rule_data: dict[str, Any]) -> dict[str, Any]
    get_rule_by_id(self, rule_id: str) -> dict[str, Any] | None
    get_rule_by_name(self, standard_category: str, rule_name: str) -> dict[str, Any] | None
    update_rule(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]
    delete_rule(self, rule_id: str) -> dict[str, Any]
    search_rules(self, filter_config: StandardRuleSearchFilter | None = None) -> dict[str, Any]
    get_rules_by_context(self, context: str, active_only: bool = True) -> list[dict[str, Any]]
    get_rules_by_category(self, standard_category: str, active_only: bool = True) -> list[dict[str, Any]]
    validate_context(self, context: str, data: dict[str, Any]) -> ComplianceReport
    execute_validation_logic(self, rule: dict[str, Any], data: dict[str, Any]) -> ValidationResult
    get_statistics(self) -> dict[str, Any]
    batch_create_rules(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]
    get_database_info(self) -> dict[str, Any]
    create_rule_async(self, rule_data: dict[str, Any]) -> dict[str, Any]
    get_rule_by_id_async(self, rule_id: str) -> dict[str, Any] | None
    get_rule_by_name_async(self, standard_category: str, rule_name: str) -> dict[str, Any] | None
    update_rule_async(self, rule_id: str, update_data: dict[str, Any]) -> dict[str, Any]
    delete_rule_async(self, rule_id: str) -> dict[str, Any]
    search_rules_async(self, filter_config: StandardRuleSearchFilter | None = None) -> dict[str, Any]
    get_rules_by_context_async(self, context: str, active_only: bool = True) -> list[dict[str, Any]]
    get_rules_by_category_async(self, standard_category: str, active_only: bool = True) -> list[dict[str, Any]]
    validate_context_async(self, context: str, data: dict[str, Any]) -> ComplianceReport
    get_statistics_async(self) -> dict[str, Any]
    batch_create_rules_async(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]
    close(self) -> None
    __enter__(self) -> StandardsKnowledgeService
    __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool
```


### P:\packages\search-research\core\result_merger.py

```python
from dataclasses import dataclass, field
from typing import Any
from .result_normalizer import NormalizedResult, normalize_result

@dataclass
class FusedResult:
    id = str
    rrf_score = float
    to_dict(self) -> dict[str, Any]
reciprocal_rank_fusion(results_list: list[list[NormalizedResult]], k: int = _DEFAULT_RRF_K, max_per_source: int = _DEFAULT_MAX_PER_SOURCE) -> list[FusedResult]
```


### P:\packages\search-research\core\result_normalizer.py

```python
from typing import Any, Final, Protocol, runtime_checkable

@runtime_checkable
class NormalizedResult(Protocol):
    id = str
    score = float
    source = str
    to_dict(self) -> dict[str, Any]
normalize_result(result: Any) -> NormalizedResult
```


### P:\packages\search-research\core\results\__init__.py

```python
from .deduplication import DeduplicationProcessor
from .ensemble import (
    EnsembleResult, HybridEnsembleConfig, reciprocal_rank_fusion, run_hybrid_ensemble, weighted_average_fusion, )
from .pipeline import ResultProcessingPipeline
from .ranking import RankingProcessor
from .reranking import (
    apply_temporal_boosting, calculate_temporal_boost, maximal_marginal_relevance, )
from .synthesis import SynthesisProcessor
__all__ = [
    "HybridEnsembleConfig",
    "EnsembleResult",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "run_hybrid_ensemble",
    "maximal_marginal_relevance",
    "apply_temporal_boosting",
    "calculate_temporal_boost",
    "DeduplicationProcessor",
    "SynthesisProcessor",
    "RankingProcessor",
    "ResultProcessingPipeline",
]
```


### P:\packages\search-research\core\results\deduplication.py

```python
from collections import defaultdict

class DeduplicationProcessor:
    __init__(self, similarity_threshold: float = 0.6, normalize_urls: bool = True)
    deduplicate_by_url(self, results: list, aggregate_sources: bool = False) -> list
    deduplicate_by_title(self, results: list) -> list
    deduplicate_by_content(self, results: list) -> list
    deduplicate(self, results: list) -> list
```


### P:\packages\search-research\core\results\ensemble.py

```python
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

@dataclass
class HybridEnsembleConfig:
    __post_init__(self)

@dataclass
class EnsembleResult:
    combined_results = list
    sources_used = dict
reciprocal_rank_fusion(result_lists: list[list], k: int = 60, max_results: int | None = None) -> list
weighted_average_fusion(result_lists: list[list], weights: dict[str, float] | None = None, max_results: int | None = None) -> list
run_hybrid_ensemble(query: str, config: HybridEnsembleConfig | None = None) -> EnsembleResult
```


### P:\packages\search-research\core\results\pipeline.py

```python
from typing import Any
from .deduplication import DeduplicationProcessor
from .ensemble import EnsembleResult
from .ranking import RankingProcessor
from .synthesis import SynthesisProcessor

class ResultProcessingPipeline:
    __init__(self, enable_deduplication: bool = True, enable_ranking: bool = True, enable_temporal_boosting: bool = False, dedup_similarity_threshold: float = 0.6, source_weights: dict[str, float] | None = None, freshness_half_life: int = 180)
    process(self, results: list, query: str = "", skip_errors: bool = False) -> list
    process_with_synthesis(self, results: list, query: str = "", use_fetched_content: bool = False) -> dict[str, Any]
    process_ensemble_result(self, ensemble_result: EnsembleResult, query: str = "") -> list
```


### P:\packages\search-research\core\results\ranking.py

```python
import math
from datetime import datetime, timezone

class RankingProcessor:
    __init__(self, source_weights: dict[str, float] | None = None, freshness_half_life: int = 180)
    rank_by_relevance(self, results: list, limit: int | None = None) -> list
    rank_by_source_quality(self, results: list) -> list
    rank_by_freshness(self, results: list, limit: int | None = None) -> list
    rank_combined(self, results: list, weights: dict[str, float] | None = None, limit: int | None = None) -> list
```


### P:\packages\search-research\core\results\reranking.py

```python
import math
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
maximal_marginal_relevance(query: str, results: list, lambda_param: float = 0.5, limit: int | None = None, get_similarity_func: Callable[[Any, Any], float] | None = None) -> list
calculate_temporal_boost(entry: dict[str, Any], half_life_days: int = 180) -> float
apply_temporal_boosting(results: list, half_life_days: int = 180) -> list
```


### P:\packages\search-research\core\results\synthesis.py

```python
import re
from typing import Any
from ..processing.got_analysis import GotAnalyzer
HAS_GOT = True
HAS_GOT = False

class SynthesisProcessor:
    __init__(self, max_summary_length: int = 500, max_insights: int = 5)
    combine_results(self, results: list, query: str = "") -> str
    generate_summary(self, results: list, max_length: int | None = None) -> str
    extract_key_insights(self, results: list, max_insights: int | None = None) -> list[str]
    synthesize_with_fetched(self, results: list, query: str = "") -> str
    synthesize_structured(self, results: list, query: str = "") -> dict[str, Any]
    synthesize_with_got(self, results: list, query: str = '') -> dict[str, Any]
    synthesize_with_citations(self, results: list, query: str = "") -> str
```


### P:\packages\search-research\core\router_async.py

```python
import asyncio
import inspect
import logging
from collections.abc import AsyncIterator
from typing import Any
from datetime import datetime
import time as time_module
from .backend_health import BackendHealthRegistry
from .cache import QueryCache
from .chs.utils import escape_fts5_query
from .config import config
from .hyde import apply_hyde
from .metrics import MetricsLogger, ComponentName
from .models import SearchResult
from .modes import Mode
from .tracing import QueryTracer, QueryTrace
logger = logging.getLogger(__name__)
BackendList = list[str]

class AsyncSearchRouter:
    __init__(self, mode: str | Mode = "fast", cache_ttl: int = 3600, enable_cache: bool = True, enable_jmri: bool = True, web: bool | None = None, hyde: bool | None = None, backend_weights: dict[str, float] | None = None) -> None
    @property
    web(self) -> bool
    @property
    hyde(self) -> bool
    get_cache_stats(self) -> dict[str, Any]
    get_backend_weights(self) -> dict[str, float]
    set_backend_weights(self, weights: dict[str, float]) -> None
    search_async(self, query: str, limit: int = 10, backends: BackendList | None = None, hyde_content: str | None = None) -> list[SearchResult]
    search_async_stream(self, query: str, limit: int = 10, backends: BackendList | None = None, hyde_content: str | None = None) -> AsyncIterator[SearchResult]
    search_async_stream_batch(self, query: str, limit: int = 10, batch_size: int = 5, backends: BackendList | None = None, hyde_content: str | None = None) -> AsyncIterator[list[SearchResult]]
    search_web_providers_async(self, query: str, limit: int = 10, providers: list[str] | None = None) -> list[SearchResult]
create_async_router(mode: str | Mode = "fast", cache_ttl: int = 3600, enable_cache: bool = True, enable_jmri: bool = True, web: bool | None = None, hyde: bool | None = None, backend_weights: dict[str, float] | None = None) -> AsyncSearchRouter
```


### P:\packages\search-research\core\security.py

```python
import os
import re
from pathlib import Path
IS_WINDOWS = os.name == "nt"
redact_api_key(key: str) -> str
validate_chs_path(path: str, root_dir: str | None = None) -> bool
validate_ipc_socket_path(path: str) -> bool
validate_api_key_format(key: str, provider: str) -> bool
is_safe_path(path: str, allowed_dir: str | None = None) -> bool
sanitize_log_string(text: str, max_length: int = 1000) -> str
```


### P:\packages\search-research\core\session_chain.py

```python
import json
import logging
import time
import asyncio
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class SessionChainEntry:
    session_id = str
    transcript_path = Path
    parent_transcript_path = Path | None

@dataclass
class SessionChainResult:
    pass
walk_handoff_chain(session_id: str, max_depth: int = 50) -> SessionChainResult
load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict[str, Any]]
walk_sessions_index_chain(session_id: str, project_path: Path | None = None, max_depth: int = 50) -> SessionChainResult
walk_semantic_chain(session_id: str, project_path: Path | None = None, threshold: float = 0.5, window_days: int = 7, max_entries: int = 20) -> SessionChainResult
walk_session_chain(session_id: str, project_path: Path | None = None, max_depth: int = 50, newest_first: bool = False) -> SessionChainResult
get_all_chain_files(session_id: str, project_path: Path | None = None, newest_first: bool = False) -> list[Path]
```


### P:\packages\search-research\core\session_graph.py

```python
import argparse
import json
import math
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict]
load_handoff_graph() -> dict[str, str]
build_inferred_edges(sessions_index: dict[str, dict]) -> dict[str, str]
build_session_graph()
render_graph(G: nx.DiGraph, sessions_index: dict, output_path: Path, html_path: Path) -> None
main() -> None
```


### P:\packages\search-research\core\sync_wrapper.py

```python
import asyncio
import warnings
from .router_async import AsyncSearchRouter, SearchResult

class SyncSearchWrapper:
    __init__(self, cache_ttl: int = 3600, enable_cache: bool = True, enable_jmri: bool = True) -> None
    search(self, query: str, limit: int = 10, backends: list[str] | None = None) -> list[SearchResult]
```


### P:\packages\search-research\core\task_manager.py

```python
import json
import subprocess
from cli.subprocess_helper import run_subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class TaskInfo:
    name = str
    state = str
    last_run_time = str | None
    next_run_time = str | None
    last_run_result = int | None
    author = str | None
    description = str | None
    @property
    is_enabled(self) -> bool
    @property
    is_running(self) -> bool

class TaskManager:
    CSF_TASKS = {
        "\\CHS One-Time Rebuild": "CHS One-Time Rebuild",
        "\\CSF_CHS_Incremental_Update": "CHS Incremental Update",
        "\\CKS_Dreaming_Daemon": "CKS Dreaming Daemon",
        "\\CSF_LogRotation": "CSF Log Rotation",
        "\\CSF_DatabaseMaintenance": "CSF Database Maintenance",
        "\\CSF_MLTraining": "CSF ML Training",
    }
    CSF_TASK_SHORT_NAMES = {
        "chs-rebuild": "\\CHS One-Time Rebuild",
        "chs-inc": "\\CSF_CHS_Incremental_Update",
        "cks": "\\CKS_Dreaming_Daemon",
        "log": "\\CSF_LogRotation",
        "db": "\\CSF_DatabaseMaintenance",
        "ml": "\\CSF_MLTraining",
    }
    __init__(self, task_folder: str = "\\")
    get_task_info(self, task_name: str) -> TaskInfo | None
    get_all_tasks(self) -> dict[str, TaskInfo]
    enable_task(self, task_name: str) -> tuple[bool, str]
    disable_task(self, task_name: str) -> tuple[bool, str]
    trigger_task(self, task_name: str) -> tuple[bool, str]
    end_task(self, task_name: str) -> tuple[bool, str]
    format_status(self, tasks: dict[str, TaskInfo] | None = None) -> str
    get_incremental_status(self) -> dict[str, Any]
```


### P:\packages\search-research\core\terminal_id.py

```python
import hashlib
import os
import socket
from pathlib import Path
canonical_terminal_id() -> str
```


### P:\packages\search-research\core\tracing.py

```python
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

@dataclass
class QueryTrace:
    query_id = str
    timestamp = str
    question = str
    path_taken = str
    backend_hits = dict[str, int]
    sources = list[str]
    final_quality = float
    contradiction_detected = bool
    to_jsonl(self) -> str

@dataclass
class DecisionAuditEntry:
    decision_id = str
    timestamp = str
    page_id = str
    decision_type = str
    query_id = str
    quality_score = float
    sources = list[str]
    reason = str
    to_jsonl(self) -> str

class QueryTracer:
    __init__(self, log_path: str = "logs/query_log.jsonl") -> None
    start_trace(self, question: str) -> str
    log_trace(self, trace: QueryTrace) -> None

class DecisionAuditor:
    __init__(self, log_path: str = "logs/decision_audit_log.jsonl") -> None
    log_decision(self, entry: DecisionAuditEntry) -> None
    record_wiki_update(self, page_id: str, decision_type: str, query_id: str, quality_score: float, sources: list[str], reason: str) -> str
```


### P:\packages\search-research\core\unified_router.py

```python
import asyncio
import logging
import math
import re
import functools
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .hybrid_ensemble import reciprocal_rank_fusion
from .models import SearchResult
from .quality_checker import QualityConfig, is_satisfactory
from .router_async import AsyncSearchRouter
logger = logging.getLogger(__name__)

class UnifiedAsyncRouter:
    __init__(self, mode: str = "auto", enable_jmri: bool = True, rrf_k: int = 60, quality_config: QualityConfig | None = None, local_router: AsyncSearchRouter | None = None, web_router: AsyncSearchRouter | None = None, topic_alignment_threshold: float = DEFAULT_TOPIC_ALIGNMENT_THRESHOLD)
    search_async(self, query: str, limit: int = 10) -> list[SearchResult]
```


### P:\packages\search-research\core\utils\__init__.py

```python
from .clustering import CoverageState, NoveltyTracker, TopicClusterer, TopicSignature
from .cost_tracker import CostTracker
from .density import DensityCalculator
from .gap_analysis import CoverageGap, GapAnalyzer, GapType
from .hyde_measurement import HyDEMeasurement
from .tree_sitter_utils import (
    FallbackBackend, LanguageRegistry, QueryEngine, TreeSitterError, TreeSitterParser, create_query_engine, get_parser, is_available, parse_code, parse_file, )
__all__ = [
    # Clustering
    "TopicSignature",
    "CoverageState",
    "TopicClusterer",
    "NoveltyTracker",
    # Cost tracking
    "CostTracker",
    # Density analysis
    "DensityCalculator",
    # Gap analysis
    "CoverageGap",
    "GapAnalyzer",
    "GapType",
    # HyDE measurement
    "HyDEMeasurement",
    # Tree-sitter utilities
    "TreeSitterParser",
    "LanguageRegistry",
    "QueryEngine",
    "FallbackBackend",
    "TreeSitterError",
    "is_available",
    "get_parser",
    "parse_code",
    "parse_file",
    "create_query_engine",
]
```


### P:\packages\search-research\core\utils\clustering.py

```python
from dataclasses import dataclass, field
from typing import Dict, Set
from re import findall
from collections import Counter
from hashlib import sha256

@dataclass
class TopicSignature:
    topic_id = str
    keyword_hash = int
    keywords = Set[str]

@dataclass
class CoverageState:
    pass

class TopicClusterer:
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these",
        "those", "it", "its", "get", "use", "make", "when", "what", "how",
        "all", "each", "more", "some", "such", "only", "own", "same", "so",
        "than", "too", "very", "just", "also", "now", "new", "first", "last",
        "make", "into"
    }
    __init__(self)
    extract_keywords(self, text: str, top_n: int = 6) -> Set[str]
    cluster_results(self, results) -> Dict[str, TopicSignature]

class NoveltyTracker:
    __init__(self, novelty_threshold: float = 0.05)
    compute_coverage_state(self, results, clusters: Dict[str, TopicSignature]) -> CoverageState
    extract_keywords(self, text: str, top_n: int = 6) -> Set[str]
    compute_novelty(self, current: CoverageState, previous: CoverageState) -> float
    should_continue(self, current_state: CoverageState) -> bool
```


### P:\packages\search-research\core\utils\cost_tracker.py

```python
from dataclasses import dataclass

@dataclass
class CostTracker:
    budget = float
    __post_init__(self)
    track_search(self, provider: str, num_results: int = 0, num_requests: int = 1) -> bool
    is_budget_exceeded(self) -> bool
    reset(self)
    get_remaining(self) -> float
```


### P:\packages\search-research\core\utils\density.py

```python
from typing import List
from re import findall

class DensityCalculator:
    TECHNICAL_TERMS = {
        "api", "endpoint", "json", "xml", "sql", "database", "query",
        "async", "await", "thread", "process", "protocol", "http",
        "config", "timeout", "connection", "pool", "serial", "format",
        "parse", "serialize", "deserialize", "encode", "decode",
        "authentication", "authorization", "token", "session", "cookie",
        "function", "method", "class", "object", "interface", "type",
        "variable", "parameter", "argument", "return", "exception",
        "error", "warning", "debug", "log", "trace", "profile",
    }
    compute_numeric_density(self, results: List) -> float
    compute_technical_density(self, results: List) -> float
    compute_density(self, results: List) -> float
```


### P:\packages\search-research\core\utils\gap_analysis.py

```python
from dataclasses import dataclass, field
from typing import List, Set
from enum import Enum

class GapType(Enum):
    MISSING_SOURCE_TYPE = "missing_source_type"
    LOW_DOMAIN_DIVERSITY = "low_domain_diversity"
    LOW_TOPIC_COVERAGE = "low_topic_coverage"

@dataclass
class CoverageGap:
    gap_type = GapType
    description = str
    severity = float

class GapAnalyzer:
    MIN_SOURCE_TYPES = 3
    MIN_DOMAINS = 3
    MIN_TOPICS = 2
    SOURCE_TYPE_PRIORITY = {
        "academic": "paper research academic arxiv study",
        "docs": "documentation official guide reference",
        "community": "stackoverflow reddit discussion community",
        "video": "video tutorial youtube course",
        "blog": "blog article tutorial guide",
        "vendor": "official vendor documentation guide",
    }
    detect_gaps(self, results, topics: Set[str], source_types: Set[str], domains: Set[str]) -> List[CoverageGap]
    generate_follow_up_query(self, original_query: str, gap: CoverageGap) -> str
```


### P:\packages\search-research\core\utils\hyde_measurement.py

```python
import time
from dataclasses import dataclass
from typing import Any
from ..hyde import apply_hyde, extract_key_phrases

@dataclass
class HyDEMeasurement:
    original_query = str
    enhanced_query = str
    hyde_applied = bool
    enhancement_latency_ms = float
    result_count = int
    to_dict(self) -> dict[str, Any]
measure_hyde_effectiveness(query: str, hyde_content: str | None = None) -> HyDEMeasurement
track_hyde_metrics(measurement: HyDEMeasurement, results: list[Any]) -> dict[str, Any]
```


### P:\packages\search-research\core\utils\tree_sitter_utils.py

```python
from functools import lru_cache
from typing import Any
TREE_SITTER_AVAILABLE = True
from tree_sitter import Language, Parser, Query
TREE_SITTER_AVAILABLE = False
Language = None
Parser = None
Query = None
import tree_sitter_python as tsp
import tree_sitter_javascript as tjs
import tree_sitter_typescript as tts
import tree_sitter_go as tg
import tree_sitter_rust as tr
import tree_sitter_java as tj
import tree_sitter_php as tp
tsp = _LANGUAGE_PACKAGES.get("python")
tjs = _LANGUAGE_PACKAGES.get("javascript")
tts = _LANGUAGE_PACKAGES.get("typescript")
tg = _LANGUAGE_PACKAGES.get("go")
tr = _LANGUAGE_PACKAGES.get("rust")
tj = _LANGUAGE_PACKAGES.get("java")
tp = _LANGUAGE_PACKAGES.get("php")

class TreeSitterError(Exception):
    pass

class TreeSitterParser:
    __init__(self, language: str)
    @property
    language_name(self) -> str
    @property
    parser(self) -> Parser
    parse(self, source_code: str)
    parse_bytes(self, source_bytes: bytes)
    query(self, pattern: str, source_code: str)
    extract_functions(self, source_code: str)
@lru_cache(maxsize=128)
get_parser(language: str) -> TreeSitterParser

class LanguageRegistry:
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".php": "php",
    }
    @classmethod
    get_language_from_path(cls, file_path: str) -> str | None
    @classmethod
    is_supported(cls, file_path: str) -> bool

class QueryEngine:
    QUERIES = {
        "all_functions": "(function_definition) @func",
        "all_classes": "(class_definition) @class",
        "methods_with_db_param": "(function_definition parameters: (parameter (identifier) @param)) @func",
        "test_functions": "(function_definition name: (identifier) @name) @func",
        "async_functions": "(function_definition async: (async) @async) @func",
        "decorators": "(decorator) @decorator",
    }
    __init__(self, language: str | TreeSitterParser)
    query(self, pattern: str, source_code: str)
    get_prebuilt_query(self, name: str) -> str
    run_prebuilt_query(self, name: str, source_code: str)

class FallbackBackend:
    @staticmethod
    detect_fallback_needed() -> bool
    @staticmethod
    parse_with_ast(source_code: str)
    @staticmethod
    is_available() -> bool
parse_code(source_code: str, language: str)
parse_file(file_path: str) -> Any
create_query_engine(language: str) -> QueryEngine
is_available() -> bool
TreeSitterQueryEngine = QueryEngine
benchmark_parse(file_paths: list, iterations: int = 5)
```


### P:\packages\search-research\diagram_mermaid.min.js

```javascript

```


### P:\packages\search-research\modules\discover\__init__.py

```python
from .static_call_graph import CallGraph, StaticCallGraphBuilder
__all__ = ["CallGraph", "StaticCallGraphBuilder"]
```


### P:\packages\search-research\modules\discover\static_call_graph.py

```python
import ast
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CallNode:
    name = str
    file = str
    line = int
    __hash__(self) -> int

@dataclass
class CallGraph:
    add_function(self, node: CallNode) -> None
    add_call(self, caller_key: str, callee_key: str) -> None
    get_callers(self, func_name: str) -> list[str]
    get_callees(self, func_name: str) -> list[str]
    get_entry_points(self) -> list[str]

class StaticCallGraphBuilder:
    __init__(self, root_paths: list[str] | None = None)
    analyze(self) -> None
    get_graph(self) -> CallGraph
get_callers(func_name: str) -> list[str]
get_callees(func_name: str) -> list[str]
get_entry_points() -> list[str]
```


### P:\packages\search-research\scripts\__init__.py

```python

```


### P:\packages\search-research\scripts\baseline_benchmark.py

```python
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any
unified_search_path = Path(__file__).parents[2] / "unified-search" / "src"
from unified_search import EnhancedUnifiedSearchRouter
import subprocess
result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(unified_search_path.parent)],
        capture_output=True,
        text=True
    )
from unified_search import EnhancedUnifiedSearchRouter
SAMPLE_QUERIES = [
    # Code search patterns
    "async function implementation",
    "class inheritance pattern",
    "error handling try except",
    "type hints annotations",
    "decorator function wrapper",

    # Documentation search
    "authentication flow",
    "database connection",
    "API endpoint configuration",
    "environment variables setup",
    "logging configuration",

    # Chat history patterns
    "how to fix import error",
    "debugging memory leak",
    "optimizing performance",
    "testing async code",
    "dependency injection",

    # Skills and commands
    "git commit workflow",
    "pytest test configuration",
    "docker container setup",
    "CI/CD pipeline",
    "deployment strategy",

    # Fuzzy matching scenarios
    "autentication",  # typo: authentication
    "data base",  # should match: database
    "preformance",  # typo: performance
    "asynchronous",  # variation: async
    "deploymnt",  # typo: deployment
]
measure_search_latency(router: EnhancedUnifiedSearchRouter, query: str, iterations: int = 10) -> dict[str, Any]
measure_cache_performance(router: EnhancedUnifiedSearchRouter, queries: list[str], iterations: int = 100) -> dict[str, Any]
run_benchmark(num_queries: int = 1000, latency_iterations: int = 10, cache_iterations: int = 100, backend_filter: list[str] | None = None) -> dict[str, Any]
save_baseline_md(results: dict[str, Any], output_path: Path) -> None
main()
```


### P:\packages\search-research\scripts\baseline_benchmark_simple.py

```python
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any
unified_search_src = Path(__file__).parents[2] / "unified-search" / "src"
import importlib.util
import sys
cache_path = unified_search_src / "unified_search" / "cache.py"
cache_spec = importlib.util.spec_from_file_location("unified_search.cache", cache_path)
cache_module = importlib.util.module_from_spec(cache_spec)
QueryCache = cache_module.QueryCache
health_path = unified_search_src / "unified_search" / "backend_health.py"
health_spec = importlib.util.spec_from_file_location("unified_search.backend_health", health_path)
health_module = importlib.util.module_from_spec(health_spec)
BackendHealthRegistry = health_module.BackendHealthRegistry
BackendHealth = health_module.BackendHealth
import traceback
benchmark_cache_performance() -> dict[str, Any]
benchmark_backend_health() -> dict[str, Any]
save_baseline_md(results: dict[str, Any], output_path: Path) -> None
main()
```


### P:\packages\search-research\scripts\benchmark_connection_pooling.py

```python
import asyncio
import time
import httpx
benchmark_new_client(iterations: int = 10) -> float
benchmark_shared_client(iterations: int = 10) -> float
main() -> int
import sys
```


### P:\packages\search-research\scripts\ingest_hooks_doc_to_cks.py

```python
import re
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from core.cks.unified import CKS
chunk_markdown(text: str, max_chunk_size: int = 2000) -> list[tuple[str, str]]
main() -> int
```


### P:\packages\search-research\search_research\__init__.py

```python
from core.hyde import (
    apply_hyde, enhance_query, extract_key_phrases, )
from core.models import (
    EnhancedQuery, ResearchResult, SearchResult, )
from core.modes import Mode
from core.session_chain import (
    SessionChainEntry, SessionChainResult, get_all_chain_files, walk_handoff_chain, walk_session_chain, )
from core.unified_router import (
    AsyncSearchRouter, UnifiedAsyncRouter, )
__all__ = [
    # Models
    "SearchResult",
    "EnhancedQuery",
    "ResearchResult",
    # Routers
    "AsyncSearchRouter",
    "UnifiedAsyncRouter",
    # Enums
    "Mode",
    # HyDE
    "apply_hyde",
    "enhance_query",
    "extract_key_phrases",
]
```


### P:\packages\search-research\search_research\metrics.py

```python
from core.metrics import (
    ComponentMetric, ComponentName, MetricsLogger, )
__all__ = ["ComponentName", "ComponentMetric", "MetricsLogger"]
```


### P:\packages\search-research\skills\__init__.py

```python

```


### P:\packages\search-research\skills\all\__init__.py

```python
from .adaptive_limits import get_adaptive_config
from .agent_filter import apply_agent_filtering
from .layer2_filter import should_apply_context_filter
from .query_complexity import calculate_complexity_score, get_complexity_label
from .search_executor import execute_search
from .semantic_cluster import apply_semantic_clustering
__all__ = [
    "execute_search",
    "apply_semantic_clustering",
    "calculate_complexity_score",
    "get_complexity_label",
    "get_adaptive_config",
    "apply_agent_filtering",
    "should_apply_context_filter",
]
```


### P:\packages\search-research\skills\all\adaptive_limits.py

```python
from typing import Any
TOKENS_PER_RESULT = 150
TOKENS_PER_METADATA = 30
LAYER2_SAFE_TOKEN_LIMIT = 8000
LAYER2_WARNING_THRESHOLD = 7000
get_adaptive_limit(complexity_score: int) -> int
estimate_tokens(result_count: int, avg_content_length: int = 300, has_metadata: bool = True) -> int
check_token_limit(result_count: int, avg_content_length: int = 300, limit: int = LAYER2_SAFE_TOKEN_LIMIT) -> dict[str, Any]
get_adaptive_config(complexity_score: int, result_count: int, avg_content_length: int = 300) -> dict[str, Any]
recommend_layer2_limit(complexity_score: int, result_count: int, avg_content_length: int = 300) -> int
```


### P:\packages\search-research\skills\all\agent_filter.py

```python
import json
import os
from typing import Any
from . import layer2_filter
from . import query_complexity
is_skill_context() -> bool
sanitize_for_prompt(text: str) -> str
estimate_tokens_from_results(results: list[Any], avg_content_length: int = 300) -> int
get_adaptive_insight_count(complexity_score: int, result_count: int) -> int
create_enhanced_layer2_prompt(query: str, results: list[Any], complexity_score: int, insight_count: int) -> str
parse_agent_response(response: str, max_depth: int = 3) -> dict[str, Any] | None
apply_agent_filtering(query: str, results: list[Any], trigger_reason: str = "auto", complexity_score: int = 50) -> dict[str, Any]
create_agent_filter_summary(query: str, original_count: int, filtered_count: int, complexity_score: int, trigger_reason: str) -> dict[str, Any]
```


### P:\packages\search-research\skills\all\complete_three_layer_implementation.py

```python
import asyncio
import sys
from pathlib import Path
from typing import Any
src_path = Path(__file__).parent.parent.parent.parent / "src"
from search_research import UnifiedAsyncRouter
from search_research.models import SearchResult
from search_research.quality_checker import QualityConfig
layer1_python_filtering(query: str, limit: int = 30) -> list[SearchResult]
layer2_trigger_detection(results: list[SearchResult], query: str, threshold: int = 20) -> tuple[bool, str]
layer2_semantic_filtering(results: list[SearchResult], query: str) -> dict[str, Any]
layer3_formatting(filtered_results: Any, query: str, layer2_applied: bool) -> str
execute_complete_search(query: str, limit: int = 30) -> str
main()
```


### P:\packages\search-research\skills\all\execute_three_layer_search.py

```python
import asyncio
import sys
from pathlib import Path
from typing import Any
src_path = Path(__file__).parent.parent.parent.parent / "src"
skills_path = Path(__file__).parent
from filtering import (
    format_output, should_apply_context_filter, )
from search_research import UnifiedAsyncRouter
from search_research.models import SearchResult
from search_research.quality_checker import QualityConfig
execute_three_layer_search(query: str, mode: str = "auto", limit: int = 10, enable_layer2: bool = True, context_threshold: int = 20, format_type: str = "human") -> str
main()
```


### P:\packages\search-research\skills\all\explore.py

```python
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any
src_path = Path(__file__).parent.parent.parent.parent / "src"
skills_path = Path(__file__).parent
import layer2_filter
import search_executor
apply_layer2_filtering = layer2_filter.apply_layer2_filtering
should_apply_context_filter = layer2_filter.should_apply_context_filter
parse_args() -> argparse.Namespace
search_universal_with_filtering(query: str, mode: str = "auto", limit: int = 10, rrf_k: int = 60, min_score: float = 0.5, min_results: int = 3, enable_jmri: bool = True, enable_layer2: bool = True, disable_layer2: bool = False, context_threshold: int = 20, force_layer2: bool = False) -> tuple[list, bool, Any]
main() -> int
```


### P:\packages\search-research\skills\all\filtering.py

```python
from typing import Any
has_context_hints(query: str) -> bool
should_apply_context_filter(results: list[Any], query: str, threshold: int = 20) -> tuple[bool, str]
apply_context_filter(results: list[Any], query: str) -> dict[str, Any]
format_standard_results(results: list[Any], query: str) -> str
format_themed_results(filtered_results: dict[str, Any], query: str) -> str
format_output(results: Any, query: str, layer2_applied: bool, format_type: str = "human") -> str
```


### P:\packages\search-research\skills\all\layer2_filter.py

```python
from typing import Any
from . import agent_filter
from . import query_complexity
THEME_KEYWORDS = {
    "Async Programming": frozenset(["async", "await", "asyncio", "coroutine"]),
    "Frameworks & APIs": frozenset(["api", "framework", "library", "flask", "fastapi"]),
    "Best Practices": frozenset(["pattern", "practice", "best", "guide", "tutorial"]),
    "Error Handling": frozenset(["error", "exception", "handling", "debug"]),
    "Search Architecture": frozenset(["search", "router", "backend", "frontend"]),
    "Testing": frozenset(["test", "testing", "pytest", "unittest"]),
}
has_context_hints(query: str) -> bool
should_apply_context_filter(results: list[Any], query: str, threshold: int = 20) -> tuple[bool, str | None]
create_layer2_prompt(query: str, results: list[Any]) -> str
apply_layer2_filtering(query: str, results: list[Any]) -> dict[str, Any]
```


### P:\packages\search-research\skills\all\orchestration.py

```python
import asyncio
import sys
from pathlib import Path
from typing import Any
src_path = Path(__file__).parent.parent.parent / "src"
skills_path = Path(__file__).parent
import skills.explore.adaptive_limits as adaptive_limits
import skills.explore.query_complexity as query_complexity
import skills.explore.semantic_cluster as semantic_cluster
import skills.explore.search_executor as search_executor
import skills.explore.agent_filter as agent_filter
import skills.explore.layer2_filter as layer2_filter
format_themed_results(filtered_data: dict[str, Any], query: str) -> str
format_standard_results(results: list[Any], query: str, limit: int = 30) -> str
execute_unified_search(query: str) -> str
main(query: str) -> str
```


### P:\packages\search-research\skills\all\production_three_layer.py

```python
import asyncio
import sys
from pathlib import Path
from typing import Any
src_path = Path(__file__).parent.parent.parent.parent / "src"
PRODUCTION_MODE = False
layer1_python_filtering(query: str, limit: int = 30) -> list
layer2_trigger_detection(results: list, query: str, threshold: int = 20) -> tuple[bool, str]
layer2_semantic_filtering_real(results: list, query: str) -> dict[str, Any]
layer3_formatting(filtered_results: Any, query: str, layer2_applied: bool) -> str
execute_complete_search(query: str, limit: int = 30) -> str
main()
```


### P:\packages\search-research\skills\all\query_complexity.py

```python
import re
TECHNICAL_TERMS = {
    # Programming languages/frameworks
    'python', 'javascript', 'typescript', 'java', 'rust', 'go', 'ruby', 'php',
    'react', 'vue', 'angular', 'svelte', 'django', 'flask', 'fastapi', 'express',
    'async', 'await', 'promise', 'observable', 'coroutine', 'thread', 'process',

    # Technical concepts
    'api', 'rest', 'graphql', 'grpc', 'websocket', 'http', 'https', 'tcp', 'udp',
    'sql', 'nosql', 'database', 'orm', 'migration', 'schema', 'query', 'index',
    'algorithm', 'data structure', 'complexity', 'optimization', 'performance',
    'authentication', 'authorization', 'oauth', 'jwt', 'session', 'cookie',
    'docker', 'kubernetes', 'container', 'deployment', 'ci/cd', 'testing',

    # File/protocol formats
    'json', 'xml', 'yaml', 'csv', 'markdown', 'pdf', 'html', 'css',
}
MULTI_WORD_TECHNICAL_TERMS = [
    'machine learning', 'natural language processing', 'deep learning',
    'neural network', 'computer vision', 'data science', 'software engineering',
    'system design', 'web development', 'mobile development', 'cloud computing',
    'devops engineering', 'site reliability', 'unit testing', 'integration testing',
    'continuous integration', 'continuous deployment', 'version control',
    'agile methodology', 'scrum framework', 'kanban board',
]
AMBIGUITY_INDICATORS = [
    r'\bhow\b',  # "how to", "how does"
    r'\bwhat\b',  # "what is", "what are"
    r'\bwhich\b',  # "which one", "which approach"
    r'\bwhere\b',  # "where to", "where can"
    r'\bwhen\b',  # "when to", "when should"
    r'\bwhy\b',  # "why use", "why does"
    r'\bbest\b',  # "best practice", "best way"
    r'\bbetter\b',  # "better approach", "better performance"
    r'\bcompare\b',  # "compare different approaches"
    r'\bdifferent\b',  # "different approaches", "different ways"
    r'\bversus\b',  # "versus", "vs"
    r'\bvs\b',  # "versus", "vs"
]
NEGATION_PATTERNS = [
    r'\bnot\s+\w+',  # "not python", "not async"
    r'\bwithout\s+\w+',  # "without docker"
    r'\bexcept\s+\w+',  # "except react"
    r'\bno\s+\w+',  # "no database"
]
CONTEXT_HINTS = [
    'discuss', 'mention', 'talk about', 'cover', 'explain',
    'compare', 'difference', 'versus', 'vs',
    'example', 'tutorial', 'guide', 'how to',
    'is',  # Added: "what is X" queries (TASK-011 v2)
    'are',  # Added: "what are X" queries (TASK-011 v2)
    'practices',  # Added: "best practices for X" (TASK-011 v2)
    'best',  # Added: "best X" queries (TASK-011 v2)
]
COMPILED_AMBIGUITY_PATTERNS = [re.compile(p) for p in AMBIGUITY_INDICATORS]
COMPILED_NEGATION_PATTERNS = [re.compile(p) for p in NEGATION_PATTERNS]
calculate_complexity_score(query: str) -> int
get_layer2_threshold(complexity_score: int) -> int
should_trigger_layer2(query: str, result_count: int, context_threshold: int = 20) -> tuple[bool, str, int]
get_complexity_label(complexity_score: int) -> str
get_adaptive_limit(complexity_score: int) -> int
```


### P:\packages\search-research\skills\all\search_executor.py

```python
import json
import sys
from pathlib import Path
from typing import Any
search_research_path = Path("P:/packages/search-research").resolve()
from core.quality_checker import QualityConfig
from search_research import UnifiedAsyncRouter
execute_search(query: str, mode: str = "auto", limit: int = 10, rrf_k: int = 60, min_score: float = 0.5, min_results: int = 3, enable_jmri: bool = True) -> list
apply_layer1_rule_based_filtering(results: list) -> list
format_results_human(query: str, results: list, mode: str, layer2_applied: bool = False, filtered_results: Any = None) -> str
format_results_json(query: str, results: list, mode: str) -> str
```


### P:\packages\search-research\skills\all\semantic_cluster.py

```python
import re
from dataclasses import dataclass
from typing import Any

@dataclass
class Cluster:
    cluster_id = int
    items = list[Any]
    similarity_threshold = float
normalize_text(text: str) -> str
calculate_similarity(text1: str, text2: str) -> float
cluster_results(results: list[Any], similarity_threshold: float = 0.4) -> list[Cluster]
select_top_from_cluster(cluster: Cluster, max_items: int = 2) -> list[Any]
apply_semantic_clustering(results: list[Any], similarity_threshold: float = 0.4, max_results: int = 25) -> list[Any]
get_clustering_stats(original_count: int, results: list[Any], similarity_threshold: float = 0.4) -> dict[str, Any]
```


### P:\packages\search-research\skills\chs\scripts\chs_cli.py

```python
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
CHS_SEARCH_AVAILABLE = False
CHS_DB_AVAILABLE = False
FAISS_AVAILABLE = False
from core.chs import db as chs_db
from core.chs import search as chs_search
from core.chs.db import database_is_initialized
CHS_SEARCH_AVAILABLE = True
chs_db_path = Path(os.getenv("CHS_DB_PATH", "P:/__csf/data/chat_history.db")).expanduser()
CHS_DB_AVAILABLE = database_is_initialized(chs_db_path)
import faiss
FAISS_AVAILABLE = True
SQLITE_AVAILABLE = True

class CHSConfig:
    __init__(self)
    save_config(self)
    get_workspace_aliases(self) -> dict[str, list[str]]
    resolve_workspace_alias(self, alias: str) -> list[str]
    get_metrics_db_path(self) -> Path

class CHSMetrics:
    __init__(self, db_path: Path | None = None)
    record_session(self, session_id: str, workspace: str, branch: str, terminal_id: str, message_count: int, tool_usage: dict[str, int], timestamp: float, duration: float)
    get_stats(self, workspace: str | None = None, since: datetime | None = None) -> dict[str, Any]

class CHSSearch:
    __init__(self, config: CHSConfig)
    get_backend_status(self) -> dict[str, bool]
    search_stage1(self, query: str, workspace: str | None = None, branch: str | None = None, tool: str | None = None, limit: int = 20) -> list[dict[str, Any]]
    search_stage2(self, query: str, workspace: str | None = None, branch: str | None = None, tool: str | None = None, limit: int = 20) -> list[dict[str, Any]]

class CHSSummarizer:
    __init__(self)
    summarize(self, session_data: dict[str, Any], mode: str) -> str

class CHSExporter:
    __init__(self, exclude_thinking: bool = False, include_tool_results: bool = False)
    get_current_session_id(self) -> str | None
    export_chain(self, session_id: str | None = None, output_path: Path | None = None) -> Path

class CHSContext:
    show_context(self, session_file: Path, match_line: int, context_lines: int = 10) -> str
main()
```


### P:\packages\search-research\src\__init__.py

```python

```


### P:\packages\search-research\src\daemons\__init__.py

```python

```


### P:\packages\search-research\src\daemons\unified_semantic_daemon.py

```python
import sys
from pathlib import Path
import contrib.semantic_daemon.unified_semantic_daemon as _actual_daemon
from contrib.semantic_daemon.unified_semantic_daemon import (
    CKS_MODEL_MEMORY_MB, DISCOVERY_FILE, FAISS_ESTIMATED_MEMORY_MB, FAISS_INDEX_PATH, FAISS_LOCK_PATH, FAISS_STATE_PATH, FAISS_UPDATE_INTERVAL, IDLE_SHUTDOWN_TIMEOUT, MAX_MEMORY_MB, PIPE_NAME, REQUEST_TIMEOUT, SENTENCE_TRANSFORMER_MEMORY_MB, STARTUP_TIMEOUT, SemanticClient, UnifiedSemanticDaemon, __all__, )
__all__ = [
    "UnifiedSemanticDaemon",
    "SemanticClient",
    "PIPE_NAME",
    "DISCOVERY_FILE",
    "FAISS_INDEX_PATH",
    "FAISS_STATE_PATH",
    "FAISS_LOCK_PATH",
    "STARTUP_TIMEOUT",
    "REQUEST_TIMEOUT",
    "IDLE_SHUTDOWN_TIMEOUT",
    "FAISS_UPDATE_INTERVAL",
    "MAX_MEMORY_MB",
    "CKS_MODEL_MEMORY_MB",
    "FAISS_ESTIMATED_MEMORY_MB",
    "SENTENCE_TRANSFORMER_MEMORY_MB",
]
```


### P:\packages\search-research\src\ingestion\__init__.py

```python

```


### P:\packages\search-research\src\ingestion\jsonl_watcher.py

```python
import os
import threading
import time
from pathlib import Path
from typing import Callable

class JsonlWatcher:
    __init__(self, watch_file: str | Path) -> None
    watch(self, dir_path: str | Path, callback: Callable[[str], None] | None = None) -> None
```


### P:\packages\search-research\src\query_intent.py

```python
import logging
from typing import Literal
logger = logging.getLogger(__name__)
IntentType = Literal["keyword", "semantic", "hybrid", "existential", "other"]

class QueryIntent:
    __init__(self) -> None
    classify(self, query: str) -> dict
```
