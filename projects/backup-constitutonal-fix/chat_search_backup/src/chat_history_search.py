from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""Advanced Chat History Search (CHS) for CSF NIP
Intelligent cross-session chat history search with semantic understanding.
"""



# Add CSF NIP paths - use absolute path to avoid path issues
csf_nip_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib" / "core_utils"))

# Import GPU environment manager
try:
    from src.lib.core_utils.gpu_environment_manager import GPUEnvironmentManager
    from src.lib.core_utils.process_lock import ProcessLockImplementation

    GPU_ENVIRONMENT_AVAILABLE = True
except ImportError:
    GPU_ENVIRONMENT_AVAILABLE = False
    ProcessLockImplementation = None

# Import RAG components
try:
    # Try using CSF NIP paths
    from src.modules.analysis.chat_search.src.hybrid_searcher import (
        HybridSearcherFactory,
    )
    from src.modules.analysis.chat_search.src.simple_chunker import (
        ConversationChunkerFactory,
    )

    RAG_AVAILABLE = True
except ImportError:
    try:
        # Fall back to relative import
        from .hybrid_searcher import HybridSearcherFactory
        from .simple_chunker import ConversationChunkerFactory

        RAG_AVAILABLE = True
    except ImportError as e:
        logging.warning(f"RAG components not available: {e}")
        RAG_AVAILABLE = False

# Import multi-level caching system
try:
    # Try relative import first
    from multi_level_cache import MultiLevelCache
    CACHING_AVAILABLE = True
except ImportError:
    try:
        # Fallback to absolute import
        from modules.analysis.chat_search.src.multi_level_cache import MultiLevelCache
        CACHING_AVAILABLE = True
    except ImportError as e:
        logging.warning(f"Multi-level caching not available: {e}")
        CACHING_AVAILABLE = False


class ChatHistorySearcher:
    """Advanced chat history search with intelligent ranking and filtering
    Enhanced with RAG capabilities for semantic understanding.
    """

    def __init__(
        self,
        chat_history_path: Path | None = None,
        index_dir: Path | None = None,
        enable_rag: bool = True,
        rag_backend: str = "hybrid",
        use_sqlite: bool = True,
    ) -> None:
        self.logger = logging.getLogger(__name__)

        # Initialize GPU environment manager
        self.gpu_env_manager = None
        if GPU_ENVIRONMENT_AVAILABLE:
            try:
                self.gpu_env_manager = GPUEnvironmentManager()
                self.logger.info("GPU environment manager initialized")
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize GPU environment manager: {e}"
                )
        else:
            self.logger.info("GPU environment manager not available")

        # Initialize SQLite database (preferred over file-based storage)
        self.use_sqlite = use_sqlite
        self.chat_db = None

        if index_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            index_dir = project_root / ".ToolRegistry" / "chat_search_index"

        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        if self.use_sqlite:
            try:
                # Import ChatHistoryDB - add current directory to path for imports
                current_dir = Path(__file__).parent
                if str(current_dir) not in sys.path:
                    sys.path.insert(0, str(current_dir))
                from chat_history_db import ChatHistoryDB

                # Use CSF NIP data directory for consistency
                db_path = Path(__file__).parent.parent.parent.parent / ".data" / "chat_history.db"
                self.chat_db = ChatHistoryDB(db_path)
                self.logger.info("SQLite chat history database initialized")

                # Keep legacy path for compatibility but don't require it
                self.chat_history_path = Path(chat_history_path) if chat_history_path else Path.home() / ".claude" / "history.jsonl"

            except ImportError as e:
                self.logger.warning(f"SQLite database not available: {e}, falling back to file-based storage")
                self.use_sqlite = False
                self.chat_db = None
                self._init_file_based_storage(chat_history_path, index_dir)
        else:
            self._init_file_based_storage(chat_history_path, index_dir)

        # Common initialization for both SQLite and file-based storage
        self._initialize_common_components(enable_rag, rag_backend)

    def _initialize_common_components(self, enable_rag: bool, rag_backend: str) -> None:
        """Initialize components common to both SQLite and file-based storage."""
        # Index files
        self.index_file = self.index_dir / "chat_index.json"
        self.vocabulary_file = self.index_dir / "vocabulary.json"
        self.metadata_file = self.index_dir / "metadata.json"
        self.rag_metadata_file = self.index_dir / "rag_metadata.json"

        # Load or initialize index
        self.index = self._load_index()
        self.vocabulary = self._load_vocabulary()
        self.metadata = self._load_metadata()

        # RAG components
        self.enable_rag = enable_rag and RAG_AVAILABLE
        self.rag_backend = rag_backend
        self.hybrid_searcher = None
        self.chunker = None
        self.rag_metadata = self._load_rag_metadata()

        # Multi-level caching system
        self.enable_caching = CACHING_AVAILABLE
        self.cache = None

        # Enhanced workflow optimization components
        self.workflow_optimization_enabled = True
        self.enhanced_cache = None
        self.pattern_recognizer = None
        self.session_monitor = None
        self.context_manager = None

        if self.enable_rag:
            self._initialize_rag_components()

        # Initialize enhanced caching and workflow optimization
        if self.enable_caching:
            try:
                # Import enhanced components
                from context_aware_session import ContextAwareSessionManager
                from enhanced_cache_manager import EnhancedCacheManager
                from query_pattern_recognition import QueryPatternRecognizer
                from session_duration_monitor import SessionDurationMonitor

                # Use enhanced cache manager instead of basic multi-level cache
                self.enhanced_cache = EnhancedCacheManager(cache_dir=self.index_dir)
                self.cache = self.enhanced_cache  # Maintain compatibility

                # Initialize optimization components
                self.pattern_recognizer = QueryPatternRecognizer(self.index_dir)
                self.session_monitor = SessionDurationMonitor(self.index_dir)
                self.context_manager = ContextAwareSessionManager(self.index_dir)

                self.logger.info("Enhanced workflow optimization system initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize enhanced optimization system: {e}")
                # Fallback to basic caching
                self.cache = MultiLevelCache(cache_dir=self.index_dir)
                self.workflow_optimization_enabled = False

    def _init_file_based_storage(self, chat_history_path: Path | None, index_dir: Path | None) -> None:
        """Initialize traditional file-based chat history storage."""
        if chat_history_path is None:
            self.chat_history_path = Path.home() / ".claude" / "history.jsonl"
        else:
            self.chat_history_path = Path(chat_history_path)

    def _load_index(self) -> dict[str, Any]:
        """Load chat index from file."""
        try:
            if self.index_file.exists():
                with open(self.index_file, encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to load index: {e}")
            return {}

    def _load_vocabulary(self) -> dict[str, dict[str, Any]]:
        """Load vocabulary data for TF-IDF."""
        try:
            if self.vocabulary_file.exists():
                with open(self.vocabulary_file, encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to load vocabulary: {e}")
            return {}

    def _load_metadata(self) -> dict[str, Any]:
        """Load metadata about the index."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, encoding="utf-8") as f:
                    return json.load(f)
            return {"last_updated": None, "total_entries": 0, "index_version": "1.0"}
        except Exception as e:
            self.logger.warning(f"Failed to load metadata: {e}")
            return {"last_updated": None, "total_entries": 0, "index_version": "1.0"}

    def _load_rag_metadata(self) -> dict[str, Any]:
        """Load RAG-specific metadata."""
        try:
            if self.rag_metadata_file.exists():
                with open(self.rag_metadata_file, encoding="utf-8") as f:
                    return json.load(f)
            return {"rag_enabled": False, "last_rag_index": None, "rag_version": "1.0"}
        except Exception as e:
            self.logger.warning(f"Failed to load RAG metadata: {e}")
            return {"rag_enabled": False, "last_rag_index": None, "rag_version": "1.0"}

    def _initialize_rag_components(self) -> None:
        """Initialize RAG components."""
        try:
            self.logger.info("Initializing RAG components...")

            # Initialize chunker
            self.chunker = ConversationChunkerFactory.create_default_chunker()

            # Initialize hybrid searcher
            if self.rag_backend == "hybrid":
                self.hybrid_searcher = HybridSearcherFactory.create_default_searcher()
            else:
                self.logger.warning(
                    f"Unknown RAG backend: {self.rag_backend}, using hybrid"
                )
                self.hybrid_searcher = HybridSearcherFactory.create_default_searcher()

            self.logger.info("RAG components initialized successfully")

        except Exception as e:
            self.logger.exception(f"Failed to initialize RAG components: {e}")
            self.enable_rag = False

    def _save_rag_metadata(self) -> None:
        """Save RAG metadata to file."""
        try:
            self.rag_metadata["last_updated"] = datetime.now().isoformat()
            with open(self.rag_metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.rag_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception(f"Failed to save RAG metadata: {e}")

    def _save_index(self) -> None:
        """Save index to file."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception(f"Failed to save index: {e}")

    def _save_vocabulary(self) -> None:
        """Save vocabulary to file."""
        try:
            with open(self.vocabulary_file, "w", encoding="utf-8") as f:
                json.dump(self.vocabulary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception(f"Failed to save vocabulary: {e}")

    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            self.metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception(f"Failed to save metadata: {e}")

    def _load_chat_entries_from_sqlite(self) -> list[dict[str, Any]]:
        """Load chat entries from SQLite database."""
        try:
            # Get recent sessions from database
            sessions = self.chat_db.get_recent_sessions(limit=100)  # Load last 100 sessions
            chat_entries = []

            for session in sessions:
                session_id = session["session_id"]
                full_session = self.chat_db.get_session(session_id)

                if full_session and "messages" in full_session:
                    # Convert each message to CHS format
                    for message in full_session["messages"]:
                        entry = {
                            "display": message["content"],
                            "timestamp": self._parse_timestamp_to_epoch(message["timestamp"]),
                            "project": session.get("metadata", {}).get("project", ""),
                            "pasted_contents": {},  # SQLite schema doesn't track pasted contents
                            "id": f"{session_id}_{message['id']}",
                            "session_id": session_id,
                            "role": message["role"],
                            "message_index": message["message_index"],
                        }
                        chat_entries.append(entry)

            # Sort by timestamp (most recent first) for better indexing
            chat_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            return chat_entries

        except Exception as e:
            self.logger.exception(f"Failed to load chat entries from SQLite: {e}")
            return []

    def _parse_timestamp_to_epoch(self, timestamp_str: str) -> int:
        """Parse timestamp string to epoch time."""
        try:
            if timestamp_str.isdigit():
                return int(timestamp_str)
            else:
                # Parse ISO format timestamp
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                return int(dt.timestamp())
        except Exception:
            return int(datetime.now().timestamp())

    def _parse_chat_entry(self, line: str) -> dict[str, Any] | None:
        """Parse a single chat entry from JSONL."""
        try:
            entry = json.loads(line.strip())
            return {
                "display": entry.get("display", ""),
                "timestamp": entry.get("timestamp", 0),
                "project": entry.get("project", ""),
                "pasted_contents": entry.get("pastedContents", {}),
                "id": hashlib.sha256(line.encode()).hexdigest()[:16],
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse chat entry: {e}")
            return None

    def _tokenize_text(self, text: str) -> list[str]:
        """Tokenize text for processing."""
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())
        # Filter out common stop words
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "but",
            "or",
            "if",
            "they",
            "he",
            "she",
            "it",
            "we",
            "you",
            "i",
            "this",
            "that",
            "these",
            "those",
            "am",
            "been",
            "being",
        }
        return [token for token in tokens if token not in stop_words and len(token) > 2]

    def _calculate_tf_idf(self, tokens: list[str]) -> dict[str, float]:
        """Calculate TF-IDF scores for tokens."""
        if not self.vocabulary:
            return {}

        tf_scores = Counter(tokens)
        tfidf_scores = {}

        for token, tf in tf_scores.items():
            if token in self.vocabulary:
                # Prevent math domain error
                total_entries = self.metadata.get("total_entries", 1)
                doc_freq = self.vocabulary[token]["doc_freq"]
                if total_entries > 0:
                    idf_value = total_entries / (1 + doc_freq)
                    idf = math.log(idf_value) if idf_value > 0 else 0.0
                else:
                    idf = 0.0
                tfidf_scores[token] = tf * idf

        return tfidf_scores

    def _build_vocabulary(self, chat_entries: list[dict[str, Any]]) -> None:
        """Build vocabulary for TF-IDF calculation."""
        self.logger.info("Building vocabulary...")

        # Count document frequency for each term
        doc_freq = defaultdict(int)
        total_entries = len(chat_entries)

        for entry in chat_entries:
            text = entry.get("display", "")
            tokens = set(self._tokenize_text(text))
            for token in tokens:
                doc_freq[token] += 1

        # Store vocabulary with document frequencies
        self.vocabulary = {}
        for token, freq in doc_freq.items():
            # Prevent math domain error
            if total_entries > 0:
                idf_value = total_entries / (1 + freq)
                idf = math.log(idf_value) if idf_value > 0 else 0.0
            else:
                idf = 0.0

            self.vocabulary[token] = {
                "doc_freq": freq,
                "idf": idf,
            }

        self.metadata["total_entries"] = total_entries
        self._save_vocabulary()
        self.logger.info(f"Built vocabulary with {len(self.vocabulary)} terms")

    def index_chat_history(
        self, rebuild: bool = False, force_rag_index: bool = False
    ) -> bool:
        """Index chat history for fast searching with optional RAG."""
        # Add process lock to prevent concurrent indexing
        lock = (
            ProcessLockImplementation("chs_index", timeout=300)
            if ProcessLockImplementation
            else None
        )

        try:
            if lock:
                with lock:
                    return self._perform_indexing(rebuild, force_rag_index)
            else:
                return self._perform_indexing(rebuild, force_rag_index)

        except Exception as e:
            self.logger.exception(f"Failed to index chat history: {e}")
            return False

    def _perform_indexing(self, rebuild: bool, force_rag_index: bool) -> bool:
        """Perform the actual indexing operation."""
        # Load chat entries from SQLite or file
        chat_entries = []

        if self.use_sqlite and self.chat_db:
            self.logger.info("Loading chat entries from SQLite database...")
            chat_entries = self._load_chat_entries_from_sqlite()
            if not chat_entries:
                self.logger.warning("No chat entries found in SQLite database")
                return False
        else:
            # Fall back to file-based loading
            if not self.chat_history_path.exists():
                self.logger.error(f"Chat history file not found: {self.chat_history_path}")
                return False

            # Check if rebuild is needed
            if not rebuild and self.metadata.get("last_updated"):
                # Check if chat history has been modified since last index
                history_mtime = datetime.fromtimestamp(
                    self.chat_history_path.stat().st_mtime
                )
                last_indexed = datetime.fromisoformat(self.metadata["last_updated"])
                if history_mtime < last_indexed and not force_rag_index:
                    self.logger.info("Chat history index is up to date")
                    # Still check if RAG index needs updating
                    if self.enable_rag and self._needs_rag_reindex():
                        return self._index_rag_data(chat_entries=[])
                    return True

            self.logger.info("Indexing chat history from files...")

            # Load and parse chat entries
            with open(self.chat_history_path, encoding="utf-8") as f:
                for line in f:
                    entry = self._parse_chat_entry(line)
                    if entry:
                        chat_entries.append(entry)

            if not chat_entries:
                self.logger.warning("No valid chat entries found")
                return False

        self.logger.info(f"Loaded {len(chat_entries)} chat entries for indexing")

        # Build vocabulary
        self._build_vocabulary(chat_entries)

        # Build inverted index
        self.index = {
            "entries": {},
            "word_index": defaultdict(list),
            "date_index": defaultdict(list),
            "project_index": defaultdict(list),
        }

        for entry in chat_entries:
            entry_id = entry["id"]
            self.index["entries"][entry_id] = entry

            # Word index
            text = entry.get("display", "")
            tokens = self._tokenize_text(text)
            tfidf_scores = self._calculate_tf_idf(tokens)

            for token, score in tfidf_scores.items():
                self.index["word_index"][token].append((entry_id, score))

            # Date index
            timestamp = entry.get("timestamp", 0)
            date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
            self.index["date_index"][date].append(entry_id)

            # Project index
            project = entry.get("project", "general")
            self.index["project_index"][project].append(entry_id)

        # Sort word index by TF-IDF score
        for token in self.index["word_index"]:
            self.index["word_index"][token].sort(key=lambda x: x[1], reverse=True)

        # Save index and metadata
        self._save_index()
        self._save_metadata()

        # Index RAG data if enabled
        if self.enable_rag:
            self._index_rag_data(chat_entries)

        self.logger.info(f"Indexed {len(chat_entries)} chat entries")
        return True

    def _needs_rag_reindex(self) -> bool:
        """Check if RAG reindexing is needed."""
        if not self.enable_rag or not self.rag_metadata.get("last_rag_index"):
            return True

        last_rag_index = datetime.fromisoformat(self.rag_metadata["last_rag_index"])
        history_mtime = datetime.fromtimestamp(self.chat_history_path.stat().st_mtime)
        return history_mtime > last_rag_index

    def _index_rag_data(self, chat_entries: list[dict[str, Any]]) -> bool:
        """Index chat data for RAG search."""
        try:
            if not self.enable_rag or not self.chunker or not self.hybrid_searcher:
                return False

            self.logger.info("Indexing RAG data...")

            # If no entries provided, load them
            if not chat_entries:
                with open(self.chat_history_path, encoding="utf-8") as f:
                    for line in f:
                        entry = self._parse_chat_entry(line)
                        if entry:
                            chat_entries.append(entry)

            if not chat_entries:
                return False

            # Chunk conversations
            chunks = self.chunker.chunk_conversation_history(chat_entries)
            self.logger.info(f"Created {len(chunks)} chunks for RAG indexing")

            # Prepare documents for hybrid searcher
            documents = []
            for chunk in chunks:
                doc = {
                    "text": chunk["text"],
                    "metadata": {
                        **chunk["metadata"],
                        "chunk_id": chunk["chunk_id"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                    },
                }
                documents.append(doc)

            # Add to hybrid searcher
            self.hybrid_searcher.add_documents(documents)

            # Update RAG metadata
            self.rag_metadata.update(
                {
                    "rag_enabled": True,
                    "last_rag_index": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "rag_version": "1.0",
                },
            )
            self._save_rag_metadata()

            self.logger.info(f"Successfully indexed {len(documents)} RAG documents")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to index RAG data: {e}")
            return False

    def _filter_by_session(
        self, entry_ids: list[str], session_filter: str
    ) -> list[str]:
        """Filter entries by session/time period."""
        if session_filter == "all":
            return entry_ids

        filtered_ids = []
        now = datetime.now()

        for entry_id in entry_ids:
            entry = self.index["entries"].get(entry_id)
            if not entry:
                continue

            timestamp = entry.get("timestamp", 0)
            entry_time = datetime.fromtimestamp(timestamp / 1000)

            if session_filter == "today":
                if entry_time.date() == now.date():
                    filtered_ids.append(entry_id)
            elif session_filter == "yesterday":
                yesterday = now.date() - timedelta(days=1)
                if entry_time.date() == yesterday:
                    filtered_ids.append(entry_id)
            elif session_filter == "week":
                if entry_time >= now - timedelta(days=7):
                    filtered_ids.append(entry_id)
            elif session_filter == "month" and entry_time >= now - timedelta(days=30):
                filtered_ids.append(entry_id)

        return filtered_ids

    def _filter_by_context(
        self, entry_ids: list[str], context_filter: str
    ) -> list[str]:
        """Filter entries by context (project, general, etc.)."""
        if context_filter == "all":
            return entry_ids

        filtered_ids = []
        for entry_id in entry_ids:
            entry = self.index["entries"].get(entry_id)
            if not entry:
                continue

            project = entry.get("project", "general")

            if (context_filter == "project" and project) or (
                context_filter == "general" and not project
            ):
                filtered_ids.append(entry_id)
            elif context_filter == "technical":
                # Simple heuristic for technical content
                text = entry.get("display", "").lower()
                tech_keywords = [
                    "error",
                    "code",
                    "python",
                    "bash",
                    "command",
                    "script",
                    "file",
                    "directory",
                ]
                if any(keyword in text for keyword in tech_keywords):
                    filtered_ids.append(entry_id)

        return filtered_ids

    def _calculate_relevance_score(
        self, query_tokens: list[str], entry: dict[str, Any]
    ) -> float:
        """Calculate relevance score for entry against query."""
        text = entry.get("display", "").lower()
        tokens = self._tokenize_text(text)

        # Exact phrase match bonus
        query_text = " ".join(query_tokens)
        exact_match_bonus = 2.0 if query_text in text else 0.0

        # Token matching with TF-IDF
        tfidf_scores = self._calculate_tf_idf(tokens)
        score = 0.0

        for token in query_tokens:
            if token in tfidf_scores:
                score += tfidf_scores[token]

        # Recency bonus (entries from last 24 hours get boost)
        timestamp = entry.get("timestamp", 0)
        entry_time = datetime.fromtimestamp(timestamp / 1000)
        if datetime.now() - entry_time < timedelta(hours=24):
            score *= 1.2

        return score + exact_match_bonus

    def search(
        self,
        query: str,
        session_filter: str = "all",
        context_filter: str = "all",
        rank_by: str = "relevance",
        limit: int = 20,
        use_rag: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Search chat history with intelligent ranking, optional RAG, and multi-level caching.

        Args:
        ----
            query: Search query
            session_filter: Time period filter (today, yesterday, week, month, all)
            context_filter: Context filter (project, general, technical, all)
            rank_by: Ranking method (relevance, recency, frequency, semantic)
            limit: Maximum number of results
            use_rag: Force RAG on/off (None uses default setting)

        Returns:
        -------
            List of search results with metadata

        """
        try:
            # Prepare cache filters
            cache_filters = {
                "session_filter": session_filter,
                "context_filter": context_filter,
                "rank_by": rank_by,
                "limit": limit
            }

            # Check cache first (if enabled)
            if self.enable_caching and self.cache:
                cached_results = self.cache.get(query, cache_filters)
                if cached_results:
                    self.logger.debug(f"Cache hit for query: {query[:50]}...")
                    # Add cache metadata
                    for result in cached_results:
                        result["cached"] = True
                        result["cache_timestamp"] = datetime.now().isoformat()
                    return cached_results

            # Determine if RAG should be used
            should_use_rag = use_rag if use_rag is not None else self.enable_rag

            # Perform search
            if self.use_sqlite and self.chat_db:
                self.logger.debug("Using SQLite database search")
                try:
                    results = self._sqlite_search(
                        query, session_filter, context_filter, rank_by, limit
                    )
                except Exception as e:
                    self.logger.warning(f"SQLite search failed, falling back to traditional: {e}")
                    results = self._traditional_search(
                        query, session_filter, context_filter, rank_by, limit
                    )
            elif should_use_rag and self.hybrid_searcher:
                results = self._rag_search(
                    query, session_filter, context_filter, rank_by, limit
                )
            else:
                results = self._traditional_search(
                    query, session_filter, context_filter, rank_by, limit
                )

            # Cache results (if enabled and successful)
            if self.enable_caching and self.cache and results:
                try:
                    self.cache.set(query, cache_filters, results)
                    self.logger.debug(f"Cached results for query: {query[:50]}...")
                except Exception as e:
                    self.logger.warning(f"Failed to cache results: {e}")

            # Record query for workflow optimization if enabled
            if self.workflow_optimization_enabled and self.pattern_recognizer:
                try:
                    # Generate a session ID if not available (for tracking)
                    session_id = getattr(self, '_current_session_id',
                                      f"session_{int(datetime.now().timestamp())}")

                    execution_time = 0.1  # Placeholder - would track actual time
                    results_count = len(results)

                    # Record for pattern recognition
                    self.pattern_recognizer.record_query(
                        session_id, query, results_count, execution_time, success=len(results) > 0
                    )

                    # Record for session monitoring
                    if self.session_monitor:
                        if not hasattr(self.session_monitor, 'active_sessions') or session_id not in self.session_monitor.active_sessions:
                            self.session_monitor.start_session(session_id)

                        self.session_monitor.record_query(
                            session_id, query, execution_time, results_count,
                            cache_hit=False, success=len(results) > 0
                        )

                    # Store session ID for subsequent queries
                    self._current_session_id = session_id

                except Exception as e:
                    self.logger.warning(f"Failed to record query for optimization: {e}")

            # Add search metadata
            for result in results:
                result["cached"] = False
                result["search_timestamp"] = datetime.now().isoformat()

            # Add workflow optimization suggestions if available
            optimization_suggestions = []
            if self.workflow_optimization_enabled and self.pattern_recognizer:
                try:
                    session_id = getattr(self, '_current_session_id', 'default')
                    suggestions = self.pattern_recognizer.get_intelligent_suggestions(query, session_id, limit=2)
                    optimization_suggestions = [
                        {
                            "suggested_query": s.suggested_query,
                            "confidence": s.confidence,
                            "reasoning": s.reasoning,
                            "estimated_time_savings": s.estimated_time_savings
                        }
                        for s in suggestions
                    ]
                except Exception as e:
                    self.logger.warning(f"Failed to get optimization suggestions: {e}")

            # Return enhanced results if optimizations are enabled
            if self.workflow_optimization_enabled and optimization_suggestions:
                return {
                    "results": results,
                    "optimization_suggestions": optimization_suggestions,
                    "optimization_enabled": True,
                    "query_analyzed": True
                }

            return results

        except Exception as e:
            self.logger.exception(f"Search failed: {e}")
            return []

    def _perform_hybrid_search(
        self,
        query: str,
        session_filter: str,
        context_filter: str,
        rank_by: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search using the integrated hybrid searcher."""
        try:
            # Use the hybrid searcher for combined TF-IDF + vector search
            results = self.hybrid_searcher.search(
                query=query,
                limit=limit,
                score_threshold=0.1
            )

            # Convert hybrid search results to CHS format
            chs_results = []
            for result in results:
                chs_result = {
                    "text": result.get("text", ""),  # Primary text field
                    "display": result.get("text", ""),  # Display field for compatibility
                    "content": result.get("text", ""),  # Content field
                    "timestamp": 0,  # Will be updated from original entry if available
                    "project": result.get("metadata", {}).get("project", ""),
                    "pasted_contents": result.get("metadata", {}).get("pasted_contents", {}),
                    "id": result.get("document_id", ""),
                    "relevance_score": result.get("combined_score", 0.0),
                    "matched_tokens": result.get("matched_tokens", []),
                    "search_method": "hybrid",
                    "source": "hybrid_searcher",
                    "cached": False,
                    "vector_score": result.get("vector_score", 0.0),
                    "tfidf_score": result.get("tfidf_score", 0.0),
                    "metadata": {  # Add metadata for consistent format
                        "vector_score": result.get("vector_score", 0.0),
                        "tfidf_score": result.get("tfidf_score", 0.0),
                        **result.get("metadata", {})
                    }
                }
                chs_results.append(chs_result)

            # Apply additional filtering if needed
            if session_filter != "all":
                chs_results = [
                    result for result in chs_results
                    if self._passes_session_filter(result, session_filter)
                ]

            if context_filter != "all":
                chs_results = [
                    result for result in chs_results
                    if self._passes_context_filter(result, context_filter)
                ]

            # Sort and limit results
            chs_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            self.logger.info(f"Hybrid search returned {len(chs_results[:limit])} results")
            return chs_results[:limit]

        except Exception as e:
            self.logger.exception(f"Hybrid search failed: {e}")
            return []

    def _rag_search(
        self,
        query: str,
        session_filter: str,
        context_filter: str,
        rank_by: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """CSF NIP Compliant RAG Search.

        Replaced problematic fallback implementation with CSF NIP architectural patterns.
        Uses proper strategy pattern with existing CSF NIP components.
        """
        try:
            # Import CSF NIP components (lazy import to avoid circular dependencies)
            import sys
            from pathlib import Path

            # Add CSF NIP path
            csf_nip_root = Path(__file__).parent.parent.parent.parent.parent
            if str(csf_nip_root) not in sys.path:
                sys.path.append(str(csf_nip_root))

            try:
                from src.lib.application.chat_search_service import (
                    ChatSearchContext,
                    ChatSearchService,
                    SearchMethod,
                )

                # Initialize CSF NIP chat search service
                search_service = ChatSearchService()

                # Create search context
                context = ChatSearchContext(
                    project_path=str(Path(__file__).parent.parent.parent.parent.parent),
                    search_preferences={
                        "enable_semantic_search": True,
                        "enable_keyword_search": True,
                    },
                )

                # Execute search using CSF NIP architecture
                search_method = SearchMethod.HYBRID  # Use hybrid for best results
                results = search_service.search_chat_history(
                    query_text=query,
                    search_method=search_method,
                    max_results=limit,
                    context_filter=context_filter,
                    session_filter=session_filter,
                    context=context,
                )

                # Convert CSF NIP results to CHS format
                chs_results = []
                for result in results:
                    chs_result = {
                        "display": result.content,
                        "timestamp": result.metadata.get("timestamp", 0),
                        "project": result.metadata.get("project", ""),
                        "pasted_contents": result.metadata.get("pasted_contents", {}),
                        "id": result.metadata.get("id", ""),
                        "relevance_score": result.relevance_score,
                        "matched_tokens": result.highlights,
                        "search_method": result.search_method.value,
                        "source": result.source,
                        "status": result.status.value,
                        "csf_nip_architecture": True,  # Mark as CSF NIP compliant
                    }
                    chs_results.append(chs_result)

                # Sort by relevance score
                chs_results.sort(key=lambda x: x["relevance_score"], reverse=True)

                self.logger.info(
                    f"CSF NIP RAG search returned {len(chs_results)} results"
                )
                return chs_results

            except ImportError as e:
                self.logger.exception(f"CSF NIP components not available: {e}")
                self.logger.warning(
                    "Falling back to traditional search due to missing CSF NIP components"
                )
                return self._traditional_search(
                    query, session_filter, context_filter, rank_by, limit
                )

        except Exception as e:
            self.logger.exception(
                f"CSF NIP RAG search failed, falling back to traditional search: {e}"
            )
            return self._traditional_search(
                query, session_filter, context_filter, rank_by, limit
            )

    def _sqlite_search(
        self,
        query: str,
        session_filter: str,
        context_filter: str,
        rank_by: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search directly in SQLite database."""
        try:
            # Search in SQLite database
            sql_results = self.chat_db.search_messages(query, limit=limit)

            # Convert SQLite results to CHS format
            results = []
            for result in sql_results:
                chs_result = {
                    "text": result["content"],  # Primary text field for compatibility
                    "display": result["content"],  # Display field for backward compatibility
                    "content": result["content"],  # Original content field
                    "timestamp": self._parse_timestamp_to_epoch(result["timestamp"]),
                    "project": result.get("session_start_time", "").split("T")[0],  # Extract date as project
                    "pasted_contents": {},
                    "id": result["id"],
                    "session_id": result["session_id"],
                    "role": result["role"],
                    "relevance_score": 1.0,  # SQLite search gives relevance by matching
                    "matched_tokens": query.split(),
                    "search_method": "sqlite",
                    "source": "sqlite_database",
                    "cached": False,
                    "metadata": {  # Add metadata for consistent format
                        "role": result["role"],
                        "session_id": result["session_id"],
                        "original_timestamp": result["timestamp"]
                    }
                }
                results.append(chs_result)

            # Apply session filter if needed
            if session_filter != "all":
                results = [
                    result for result in results
                    if self._passes_session_filter(result, session_filter)
                ]

            # Apply context filter if needed
            if context_filter != "all":
                results = [
                    result for result in results
                    if self._passes_context_filter(result, context_filter)
                ]

            # Sort by ranking method
            if rank_by == "recency":
                results.sort(key=lambda x: x["timestamp"], reverse=True)
            elif rank_by == "relevance":
                results.sort(key=lambda x: x["relevance_score"], reverse=True)
            # For frequency, we'd need more data from SQLite

            # Limit results
            results = results[:limit]

            self.logger.info(f"SQLite search found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            self.logger.exception(f"SQLite search failed: {e}")
            return []

    def _traditional_search(
        self,
        query: str,
        session_filter: str,
        context_filter: str,
        rank_by: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Perform traditional TF-IDF search."""
        try:
            # Ensure index exists
            if not self.index and not self.index_chat_history():
                return []

            # Tokenize query
            query_tokens = self._tokenize_text(query)
            if not query_tokens:
                return []

            # Find matching entries
            matching_entry_ids = set()

            for token in query_tokens:
                if token in self.index["word_index"]:
                    for entry_id, _ in self.index["word_index"][token]:
                        matching_entry_ids.add(entry_id)

            # Apply filters
            matching_entry_ids = self._filter_by_session(
                list(matching_entry_ids), session_filter
            )
            matching_entry_ids = self._filter_by_context(
                matching_entry_ids, context_filter
            )

            # Calculate scores and create results
            results = []
            for entry_id in matching_entry_ids:
                entry = self.index["entries"].get(entry_id)
                if not entry:
                    continue

                if rank_by == "relevance":
                    score = self._calculate_relevance_score(query_tokens, entry)
                elif rank_by == "recency":
                    timestamp = entry.get("timestamp", 0)
                    score = timestamp  # Higher timestamp = more recent
                elif rank_by == "frequency":
                    text = entry.get("display", "").lower()
                    # Optimized: use Counter for O(n) instead of O(n²)
                    text_words = text.split()
                    word_counts = Counter(text_words)
                    score = sum(word_counts.get(token, 0) for token in query_tokens)
                else:
                    score = self._calculate_relevance_score(query_tokens, entry)

                entry_text = entry.get("display", "").lower()
                result = entry.copy()
                result["relevance_score"] = score
                result["matched_tokens"] = [
                    token for token in query_tokens if token in entry_text
                ]
                result["search_method"] = "traditional"
                results.append(result)

            # Sort by score and limit results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]

        except Exception as e:
            self.logger.exception(f"Traditional search failed: {e}")
            return []

    def _passes_session_filter(
        self, entry: dict[str, Any], session_filter: str
    ) -> bool:
        """Check if entry passes session filter."""
        return self._filter_by_session([entry.get("id", "")], session_filter) == [
            entry.get("id", "")
        ]

    def _passes_context_filter(
        self, entry: dict[str, Any], context_filter: str
    ) -> bool:
        """Check if entry passes context filter."""
        return self._filter_by_context([entry.get("id", "")], context_filter) == [
            entry.get("id", "")
        ]

    def analyze_patterns(
        self,
        pattern_analysis: bool = True,
        trend_analysis: bool = True,
        topic_modeling: bool = True,
    ) -> dict[str, Any]:
        """Analyze chat patterns and trends."""
        try:
            if not self.index and not self.index_chat_history():
                return {"error": "Failed to index chat history"}

            analysis = {"timestamp": datetime.now().isoformat()}

            if pattern_analysis:
                # Find most common tokens
                all_tokens = []
                for entry_id, entry in self.index["entries"].items():
                    tokens = self._tokenize_text(entry.get("display", ""))
                    all_tokens.extend(tokens)

                token_freq = Counter(all_tokens)
                analysis["most_common_tokens"] = token_freq.most_common(20)

                # Find recurring patterns
                analysis["pattern_analysis"] = {
                    "total_tokens": len(all_tokens),
                    "unique_tokens": len(set(all_tokens)),
                    "top_keywords": token_freq.most_common(10),
                }

            if trend_analysis:
                # Analyze chat frequency over time
                date_counts = defaultdict(int)
                for date, entry_ids in self.index["date_index"].items():
                    date_counts[date] = len(entry_ids)

                sorted_dates = sorted(date_counts.items())
                analysis["trend_analysis"] = {
                    "daily_activity": dict(sorted_dates[-30:]),  # Last 30 days
                    "most_active_day": (
                        max(date_counts.items(), key=lambda x: x[1])
                        if date_counts
                        else None
                    ),
                    "total_days_analyzed": len(date_counts),
                }

            if topic_modeling:
                # Simple topic modeling based on word co-occurrence
                topic_words = {}
                for token in list(self.vocabulary.keys())[:50]:  # Top 50 tokens
                    # Find entries containing this token
                    if token in self.index["word_index"]:
                        related_tokens = []
                        for entry_id, _ in self.index["word_index"][token][
                            :5
                        ]:  # Top 5 entries
                            entry = self.index["entries"].get(entry_id)
                            if entry:
                                tokens = self._tokenize_text(entry.get("display", ""))
                                related_tokens.extend([t for t in tokens if t != token])

                        topic_words[token] = Counter(related_tokens).most_common(5)

                analysis["topic_modeling"] = topic_words

            return analysis

        except Exception as e:
            self.logger.exception(f"Pattern analysis failed: {e}")
            return {"error": str(e)}

    def _parse_time_threshold(self, threshold_str: str) -> timedelta:
        """Parse time threshold string like '1h', '30m', '2d' into timedelta."""
        if not threshold_str:
            return timedelta(hours=1)  # Default to 1 hour

        threshold_str = threshold_str.lower().strip()

        # Map units to timedelta parameters
        units = {
            "m": "minutes",
            "h": "hours",
            "d": "days",
            "w": "weeks",
        }

        # Extract number and unit
        import re

        match = re.match(r"^(\d+)([mhdw])$", threshold_str)
        if match:
            value, unit = match.groups()
            unit_param = units.get(unit, "hours")
            kwargs = {unit_param: int(value)}
            return timedelta(**kwargs)

        # Default fallback
        return timedelta(hours=1)

    def needs_refresh(self, threshold: timedelta) -> bool:
        """Check if index needs refreshing based on time threshold."""
        try:
            last_updated_str = self.metadata.get("last_updated", "Never")
            if last_updated_str == "Never":
                return True

            # Parse ISO format timestamp
            if isinstance(last_updated_str, str):
                last_updated = datetime.fromisoformat(
                    last_updated_str.replace("Z", "+00:00")
                )
            else:
                last_updated = last_updated_str

            now = datetime.now(last_updated.tzinfo) or datetime.now()
            return (now - last_updated) > threshold

        except Exception as e:
            self.logger.warning(f"Could not determine if refresh needed: {e}")
            return True  # Err on the side of refreshing

    def auto_refresh_if_needed(self, threshold: timedelta) -> bool:
        """Auto-refresh index if it's older than the threshold."""
        if self.needs_refresh(threshold):
            self.logger.info(f"Index is older than {threshold}, auto-refreshing...")
            return self.index_chat_history(rebuild=False)
        return False

    def get_status(self) -> dict[str, Any]:
        """Get system status including RAG and GPU information."""
        try:
            status = {
                "chat_history_available": self.chat_history_path.exists(),
                "chat_history_size": (
                    f"{self.chat_history_path.stat().st_size / 1024:.1f} KB"
                    if self.chat_history_path.exists()
                    else "N/A"
                ),
                "index_status": "built" if self.index else "not_built",
                "total_entries_indexed": len(self.index.get("entries", {})),
                "vocabulary_size": len(self.vocabulary),
                "last_indexed": self.metadata.get("last_updated", "Never"),
                "index_version": self.metadata.get("index_version", "Unknown"),
                "index_directory": str(self.index_dir),
            }

            if self.index:
                # Calculate additional statistics
                total_words = sum(
                    len(lists) for lists in self.index["word_index"].values()
                )
                status.update(
                    {
                        "total_word_occurrences": total_words,
                        "unique_words_indexed": len(self.index["word_index"]),
                        "date_range_indexed": (
                            f"{min(self.index['date_index'].keys())} to {max(self.index['date_index'].keys())}"
                            if self.index["date_index"]
                            else "N/A"
                        ),
                        "projects_indexed": len(self.index["project_index"]),
                    },
                )

            # Add RAG status
            status.update(
                {
                    "rag_enabled": self.enable_rag,
                    "rag_available": RAG_AVAILABLE,
                    "rag_backend": self.rag_backend if self.enable_rag else None,
                    "rag_status": (
                        "indexed"
                        if self.rag_metadata.get("rag_enabled")
                        else "not_indexed"
                    ),
                    "rag_chunks": self.rag_metadata.get("total_chunks", 0),
                    "rag_last_indexed": self.rag_metadata.get(
                        "last_rag_index", "Never"
                    ),
                    "rag_version": self.rag_metadata.get("rag_version", "Unknown"),
                },
            )

            # Add RAG component statistics if available
            if self.enable_rag and self.hybrid_searcher:
                try:
                    rag_stats = self.hybrid_searcher.get_statistics()
                    status["rag_statistics"] = rag_stats
                except Exception as e:
                    status["rag_statistics_error"] = str(e)

            # Add GPU environment information
            if self.gpu_env_manager:
                try:
                    gpu_env_summary = self.gpu_env_manager.get_environment_summary()
                    status["gpu_environment"] = {
                        "total_environments": gpu_env_summary["total_environments"],
                        "cuda_available": gpu_env_summary["cuda_available"],
                        "best_environment": {
                            "name": (
                                gpu_env_summary["best_environment"]["name"]
                                if gpu_env_summary["best_environment"]
                                else None
                            ),
                            "type": (
                                gpu_env_summary["best_environment"].get(
                                    "type", "unknown"
                                )
                                if gpu_env_summary["best_environment"]
                                else None
                            ),
                            "cuda_available": (
                                gpu_env_summary["best_environment"].get(
                                    "cuda_available", False
                                )
                                if gpu_env_summary["best_environment"]
                                else False
                            ),
                            "device": (
                                gpu_env_summary["best_environment"].get("device", "cpu")
                                if gpu_env_summary["best_environment"]
                                else "cpu"
                            ),
                            "gpu_memory_gb": (
                                gpu_env_summary["best_environment"].get("gpu_memory_gb")
                                if gpu_env_summary["best_environment"]
                                else None
                            ),
                            "pytorch_version": (
                                gpu_env_summary["best_environment"].get(
                                    "pytorch_version"
                                )
                                if gpu_env_summary["best_environment"]
                                else None
                            ),
                            "python_version": (
                                gpu_env_summary["best_environment"].get(
                                    "python_version"
                                )
                                if gpu_env_summary["best_environment"]
                                else None
                            ),
                        },
                    }
                except Exception as e:
                    status["gpu_environment_error"] = str(e)
            else:
                status["gpu_environment"] = {
                    "message": "GPU environment manager not available",
                    "cuda_available": False,
                }

            # Add multi-level caching statistics
            cache_stats = self.get_cache_stats()
            status["cache_system"] = cache_stats

            return status

        except Exception as e:
            self.logger.exception(f"Failed to get status: {e}")
            return {"error": str(e)}

    def export_results(
        self,
        search_query: str | None = None,
        format: str = "json",
        output_file: str | None = None,
    ) -> bool:
        """Export search results or all data."""
        try:
            if search_query:
                data = self.search(search_query, limit=1000)
            else:
                data = list(self.index.get("entries", {}).values())

            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"chat_export_{timestamp}.{format}"

            output_path = Path(output_file)

            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format == "csv":
                import csv

                if data:
                    with open(output_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            elif format == "markdown":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("# Chat Export\n\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                    if search_query:
                        f.write(f"Search Query: {search_query}\n\n")
                    f.write(f"Total Entries: {len(data)}\n\n")

                    for i, entry in enumerate(data, 1):
                        f.write(f"## Entry {i}\n\n")
                        f.write(f"**Timestamp:** {entry.get('timestamp', 'N/A')}\n\n")
                        f.write(f"**Project:** {entry.get('project', 'N/A')}\n\n")
                        f.write(f"**Content:** {entry.get('display', 'N/A')}\n\n")
                        f.write("---\n\n")
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False

            self.logger.info(f"Exported {len(data)} entries to {output_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Export failed: {e}")
            return False

    def get_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive caching statistics."""
        if not self.enable_caching or not self.cache:
            return {
                "cache_enabled": False,
                "message": "Multi-level caching not available"
            }

        try:
            return self.cache.get_comprehensive_stats()
        except Exception as e:
            self.logger.exception(f"Failed to get cache stats: {e}")
            return {
                "cache_enabled": True,
                "error": str(e)
            }

    def clear_cache(self, level: str | None = None) -> dict[str, Any]:
        """Clear cache at specified level or all levels."""
        if not self.enable_caching or not self.cache:
            return {
                "success": False,
                "message": "Multi-level caching not available"
            }

        try:
            if level:
                level = level.upper()
                if level == "L1":
                    cleared = self.cache.l1_cache.clear()
                    return {
                        "success": True,
                        "cleared_levels": ["L1"],
                        "entries_cleared": cleared
                    }
                elif level == "L2":
                    cleared = self.cache.l2_cache.clear()
                    return {
                        "success": True,
                        "cleared_levels": ["L2"],
                        "entries_cleared": cleared
                    }
                elif level == "L3":
                    stats = self.cache.l3_cache.get_stats()
                    size = stats.get("size", 0)
                    # For L3, we need to delete the patterns file
                    if self.cache.l3_cache.patterns_file.exists():
                        self.cache.l3_cache.patterns_file.unlink()
                    return {
                        "success": True,
                        "cleared_levels": ["L3"],
                        "entries_cleared": size
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Invalid cache level: {level}. Use L1, L2, L3, or None for all."
                    }
            else:
                # Clear all levels
                cleared = self.cache.clear_all()
                return {
                    "success": True,
                    "cleared_levels": ["L1", "L2", "L3"],
                    "entries_cleared": cleared
                }

        except Exception as e:
            self.logger.exception(f"Failed to clear cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def invalidate_cache_query(self, query: str, session_filter: str = "all",
                             context_filter: str = "all", rank_by: str = "relevance",
                             limit: int = 20) -> dict[str, Any]:
        """Invalidate cached results for specific query."""
        if not self.enable_caching or not self.cache:
            return {
                "success": False,
                "message": "Multi-level caching not available"
            }

        try:
            filters = {
                "session_filter": session_filter,
                "context_filter": context_filter,
                "rank_by": rank_by,
                "limit": limit
            }

            invalidated = self.cache.invalidate_query(query, filters)
            return {
                "success": True,
                "query": query,
                "filters": filters,
                "invalidated": invalidated
            }

        except Exception as e:
            self.logger.exception(f"Failed to invalidate cache query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def cache_health_check(self) -> dict[str, Any]:
        """Perform health check on caching system."""
        if not self.enable_caching or not self.cache:
            return {
                "cache_enabled": False,
                "message": "Multi-level caching not available"
            }

        try:
            return self.cache.health_check()
        except Exception as e:
            self.logger.exception(f"Cache health check failed: {e}")
            return {
                "overall_status": "error",
                "error": str(e)
            }

    def get_workflow_optimization_analytics(self) -> dict[str, Any]:
        """Get comprehensive workflow optimization analytics."""
        if not self.workflow_optimization_enabled:
            return {
                "optimization_enabled": False,
                "message": "Workflow optimization not available"
            }

        try:
            analytics = {
                "optimization_enabled": True,
                "pattern_recognition": {},
                "session_monitoring": {},
                "cache_performance": {},
                "context_management": {}
            }

            # Get pattern recognition statistics
            if self.pattern_recognizer:
                analytics["pattern_recognition"] = self.pattern_recognizer.get_statistics()

            # Get session monitoring statistics
            if self.session_monitor:
                analytics["session_monitoring"] = self.session_monitor.get_session_statistics()
                analytics["active_sessions"] = self.session_monitor.get_active_session_status()

            # Get enhanced cache statistics
            if self.enhanced_cache:
                analytics["cache_performance"] = self.enhanced_cache.get_preload_statistics()
                analytics["cache_optimization"] = self.enhanced_cache.optimize_preload_strategy()

            # Get context management statistics
            if self.context_manager:
                analytics["context_management"] = self.context_manager.get_context_statistics()

            # Get optimization opportunities
            if self.session_monitor:
                analytics["optimization_opportunities"] = self.session_monitor.get_optimization_opportunities()

            return analytics

        except Exception as e:
            self.logger.exception(f"Failed to get workflow optimization analytics: {e}")
            return {
                "optimization_enabled": True,
                "error": str(e)
            }

    def get_optimization_recommendations(self) -> dict[str, Any]:
        """Get optimization recommendations based on current performance."""
        if not self.workflow_optimization_enabled:
            return {
                "optimization_enabled": False,
                "message": "Workflow optimization not available"
            }

        try:
            recommendations = {
                "immediate_actions": [],
                "performance_tips": [],
                "configuration_suggestions": []
            }

            # Get analytics for recommendations
            analytics = self.get_workflow_optimization_analytics()

            # Pattern recognition recommendations
            pattern_stats = analytics.get("pattern_recognition", {})
            if pattern_stats.get("pattern_hit_rate", 0) < 0.5:
                recommendations["performance_tips"].append(
                    "Consider using more consistent search terms to improve pattern recognition"
                )

            # Session monitoring recommendations
            session_stats = analytics.get("session_monitoring", {})
            if "duration_stats" in session_stats:
                avg_duration = session_stats["duration_stats"].get("average", 0)
                if avg_duration > 300:  # 5 minutes
                    recommendations["immediate_actions"].append(
                        "Sessions are running long - consider taking breaks or refining search strategy"
                    )

            # Cache performance recommendations
            cache_stats = analytics.get("cache_performance", {})
            if cache_stats.get("preload_enabled", False):
                if cache_stats.get("queue_statistics", {}).get("size", 0) > 50:
                    recommendations["configuration_suggestions"].append(
                        "Preload queue is getting full - consider increasing confidence threshold"
                    )

            # Context management recommendations
            context_stats = analytics.get("context_management", {})
            if context_stats.get("average_optimization_score", 100) < 70:
                recommendations["performance_tips"].append(
                    "Session optimization score is low - try using the provided search suggestions"
                )

            return recommendations

        except Exception as e:
            self.logger.exception(f"Failed to get optimization recommendations: {e}")
            return {
                "optimization_enabled": True,
                "error": str(e)
            }


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Advanced Cross-Session Chat History Search"
    )
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search chat history")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--session-filter",
        choices=["today", "yesterday", "week", "month", "all"],
        default="all",
        help="Filter by session",
    )
    search_parser.add_argument(
        "--context-filter",
        choices=["project", "general", "technical", "all"],
        default="all",
        help="Filter by context",
    )
    search_parser.add_argument(
        "--rank-by",
        choices=["relevance", "recency", "frequency", "semantic"],
        default="relevance",
        help="Ranking method",
    )
    search_parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    search_parser.add_argument(
        "--use-rag", action="store_true", help="Use RAG-enhanced search"
    )
    search_parser.add_argument(
        "--no-rag", action="store_true", help="Disable RAG search"
    )
    search_parser.add_argument("--output", help="Output file")
    search_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format",
    )
    search_parser.add_argument(
        "--refresh", action="store_true", help="Force refresh index before searching"
    )
    search_parser.add_argument(
        "--auto-refresh",
        action="store_true",
        help="Auto-refresh if index is older than threshold",
    )
    search_parser.add_argument(
        "--threshold",
        default="1h",
        help="Auto-refresh time threshold (e.g., 1h, 30m, 2d)",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze chat patterns")
    analyze_parser.add_argument(
        "--pattern-analysis", action="store_true", help="Include pattern analysis"
    )
    analyze_parser.add_argument(
        "--trend-analysis", action="store_true", help="Include trend analysis"
    )
    analyze_parser.add_argument(
        "--topic-modeling", action="store_true", help="Include topic modeling"
    )
    analyze_parser.add_argument("--output", help="Output file")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index chat history")
    index_parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild entire index"
    )
    index_parser.add_argument(
        "--incremental", action="store_true", help="Incremental index update"
    )
    index_parser.add_argument(
        "--optimize", action="store_true", help="Optimize existing index"
    )
    index_parser.add_argument(
        "--rag-only", action="store_true", help="Only rebuild RAG index"
    )
    index_parser.add_argument(
        "--force-rag", action="store_true", help="Force RAG reindexing"
    )

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export search results")
    export_parser.add_argument(
        "--format",
        choices=["json", "csv", "markdown"],
        default="json",
        help="Export format",
    )
    export_parser.add_argument("--output", help="Output filename")
    export_parser.add_argument("--search-query", help="Export specific search results")
    export_parser.add_argument(
        "--all", action="store_true", help="Export all indexed content"
    )

    # Cache management commands
    cache_parser = subparsers.add_parser("cache", help="Cache management operations")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", help="Cache operations")

    # Cache stats command
    cache_subparsers.add_parser("stats", help="Show cache statistics")

    # Cache clear command
    cache_clear_parser = cache_subparsers.add_parser("clear", help="Clear cache")
    cache_clear_parser.add_argument(
        "--level",
        choices=["L1", "L2", "L3"],
        help="Specific cache level to clear (default: all levels)"
    )

    # Cache invalidate command
    cache_invalidate_parser = cache_subparsers.add_parser("invalidate", help="Invalidate specific query from cache")
    cache_invalidate_parser.add_argument("query", help="Query to invalidate")
    cache_invalidate_parser.add_argument("--session-filter", default="all", help="Session filter")
    cache_invalidate_parser.add_argument("--context-filter", default="all", help="Context filter")
    cache_invalidate_parser.add_argument("--rank-by", default="relevance", help="Ranking method")
    cache_invalidate_parser.add_argument("--limit", type=int, default=20, help="Result limit")

    # Cache health command
    cache_subparsers.add_parser("health", help="Check cache system health")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Initialize searcher with RAG options
    enable_rag = not args.no_rag if hasattr(args, "no_rag") else True
    searcher = ChatHistorySearcher(enable_rag=enable_rag)

    # Execute command
    if args.command == "search":
        # Handle refresh options
        if hasattr(args, "refresh") and args.refresh:
            searcher.index_chat_history(rebuild=False)
        elif hasattr(args, "auto_refresh") and args.auto_refresh:
            threshold = searcher._parse_time_threshold(getattr(args, "threshold", "1h"))
            if searcher.needs_refresh(threshold):
                searcher.index_chat_history(rebuild=False)

        # Determine RAG usage
        use_rag = None
        if hasattr(args, "use_rag") and args.use_rag:
            use_rag = True
        elif hasattr(args, "no_rag") and args.no_rag:
            use_rag = False

        results = searcher.search(
            args.query,
            session_filter=args.session_filter,
            context_filter=args.context_filter,
            rank_by=args.rank_by,
            limit=args.limit,
            use_rag=use_rag,
        )

        if args.format == "json":
            output = json.dumps(results, indent=2, ensure_ascii=False)
        elif args.format == "markdown":
            output = f"# Search Results for: {args.query}\n\n"
            output += f"Found {len(results)} results\n\n"
            for i, result in enumerate(results, 1):
                timestamp = datetime.fromtimestamp(
                    result.get("timestamp", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
                output += f"## {i}. Score: {result.get('relevance_score', 0):.2f}\n\n"
                output += f"**Time:** {timestamp}\n\n"
                output += f"**Project:** {result.get('project', 'N/A')}\n\n"
                output += f"**Content:** {result.get('display', 'N/A')}\n\n"
                output += "---\n\n"
        else:
            output = f"Search Results for: {args.query}\n"
            output += f"Found {len(results)} results\n\n"
            for i, result in enumerate(results, 1):
                timestamp = datetime.fromtimestamp(
                    result.get("timestamp", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")

                # Extract content with fallbacks
                content = (
                    result.get("text") or
                    result.get("content") or
                    result.get("display", "")[:200]
                )

                # Extract role from metadata
                role = result.get("metadata", {}).get("role", result.get("role", "unknown"))

                output += f"{i}. [{timestamp}] Role: {role}\n"
                output += f"   Score: {result.get('relevance_score', 0):.2f}\n"
                output += f"   Method: {result.get('search_method', 'unknown')}\n"
                output += f"   Content: {content}...\n\n"

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)

    elif args.command == "analyze":
        analysis = searcher.analyze_patterns(
            pattern_analysis=args.pattern_analysis,
            trend_analysis=args.trend_analysis,
            topic_modeling=args.topic_modeling,
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
        else:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))

    elif args.command == "index":
        if args.optimize:
            pass
        elif args.rag_only:
            success = searcher._index_rag_data(chat_entries=[])
            if success:
                pass
            else:
                pass
        else:
            success = searcher.index_chat_history(
                rebuild=args.rebuild, force_rag_index=args.force_rag
            )
            if success:
                pass
            else:
                pass

    elif args.command == "status":
        status = searcher.get_status()
        for _key, _value in status.items():
            pass

    elif args.command == "export":
        search_query = args.search_query if not args.all else None
        success = searcher.export_results(
            search_query=search_query,
            format=args.format,
            output_file=args.output,
        )
        if success:
            pass
        else:
            pass

    elif args.command == "cache":
        if hasattr(args, 'cache_command') and args.cache_command:
            if args.cache_command == "stats":
                stats = searcher.get_cache_stats()
                if args.verbose:
                    import pprint
                    pprint.pprint(stats)
                else:
                    # Print summary
                    if stats.get("cache_enabled", False):
                        hit_rates = stats.get("hit_rates", {})
                        total_requests = stats.get("performance_stats", {}).get("total_requests", 0)
                        print("Cache System: Enabled")
                        print(f"Overall Hit Rate: {hit_rates.get('overall', 0):.1%}")
                        print(f"Total Requests: {total_requests}")
                        print(f"L1 (Memory) Hit Rate: {hit_rates.get('l1', 0):.1%}")
                        print(f"L2 (Session) Hit Rate: {hit_rates.get('l2', 0):.1%}")
                        print(f"L3 (Persistent) Hit Rate: {hit_rates.get('l3', 0):.1%}")
                    else:
                        print(f"Cache System: {stats.get('message', 'Not enabled')}")
                        if 'cache_enabled' in stats:
                            print(f"Cache Available: {stats.get('cache_enabled', False)}")

            elif args.cache_command == "clear":
                result = searcher.clear_cache(level=getattr(args, 'level', None))
                if result["success"]:
                    cleared_levels = ", ".join(result["cleared_levels"])
                    print(f"Cache cleared successfully: {cleared_levels}")
                    if "entries_cleared" in result:
                        print(f"Entries cleared: {result['entries_cleared']}")
                else:
                    print(f"Failed to clear cache: {result.get('message', result.get('error', 'Unknown error'))}")

            elif args.cache_command == "invalidate":
                result = searcher.invalidate_cache_query(
                    query=args.query,
                    session_filter=getattr(args, 'session_filter', 'all'),
                    context_filter=getattr(args, 'context_filter', 'all'),
                    rank_by=getattr(args, 'rank_by', 'relevance'),
                    limit=getattr(args, 'limit', 20)
                )
                if result["success"]:
                    status = "invalidated" if result["invalidated"] else "not found"
                    print(f"Query cache {status}: {args.query[:50]}{'...' if len(args.query) > 50 else ''}")
                else:
                    print(f"Failed to invalidate cache: {result.get('error', 'Unknown error')}")

            elif args.cache_command == "health":
                health = searcher.cache_health_check()
                status = health.get("overall_status", "unknown")
                print(f"Cache Health: {status.upper()}")

                if health.get("issues"):
                    print("\nIssues found:")
                    for issue in health["issues"]:
                        print(f"  - {issue}")

                if health.get("recommendations"):
                    print("\nRecommendations:")
                    for rec in health["recommendations"]:
                        print(f"  - {rec}")

                if status == "healthy":
                    print("All cache systems operating normally")

            else:
                parser.print_help()
        else:
            parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
