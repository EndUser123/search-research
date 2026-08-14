"""CHS v2 Search Implementation (FTS + Semantic + Fusion)."""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any

import numpy as np

from .clustering import ClusteredSearchResults, cluster_results, filter_results_by_cluster
from .embeddings import bytes_to_vector, cosine_similarity
from .schema_compat import CHSSchemaCompat
from .search_session import SearchSession, SearchSessionManager
from .utils import adaptive_lambda, escape_fts5_syntax

if TYPE_CHECKING:
    pass
import sqlite3
_session_manager: SearchSessionManager | None = None


def search_semantic_sessions(
    db: sqlite3.Connection,
    query: str,
    embed_client,
    limit: int = 10,
    threshold: float = 0.65,
    expected_model: str | None = None,
) -> list[dict]:
    """Search sessions by semantic similarity using sessions.embedding.

    Model/dim aware: the query dimension is inferred from the query embedding
    (bytes / 4, float32) instead of a hardcoded 384. Rows whose embedding_dim
    differs from the query dim — or whose embedding_model differs from
    expected_model when given — are excluded with a WARNING (cosine over
    mismatched spaces is meaningless, not just inaccurate). If rows exist but
    ALL are mismatched, raises ValueError: that is a misconfiguration, not an
    empty result.

    Args:
        db: Database connection
        query: Natural language query
        embed_client: EmbedClient instance for encoding query
        limit: Max results
        threshold: Minimum cosine similarity
        expected_model: If set, only score rows tagged with this
            embedding_model (rows with NULL embedding_model are scored on
            dim match alone, for pre-provenance legacy rows)

    Returns:
        List of dicts with session_id, first_prompt, summary_short, score

    Raises:
        ValueError: embedded rows exist but none match the query dim /
            expected model — the store and the query model are incompatible.
    """
    if not query or not query.strip():
        return []

    query_embedding_bytes = embed_client.embed_texts([query])[0]
    query_dim = len(query_embedding_bytes) // 4  # float32
    query_vector = bytes_to_vector(query_embedding_bytes, dim=query_dim)

    cursor = db.execute(
        "SELECT id, first_prompt, summary_short, embedding, embedding_model, embedding_dim"
        " FROM sessions WHERE embedding IS NOT NULL"
    )
    scored = []
    usable = 0
    mismatched = 0
    for session_id, first_prompt, summary_short, embedding_blob, row_model, row_dim in cursor.fetchall():
        if embedding_blob is None:
            continue
        effective_dim = row_dim or len(embedding_blob) // 4
        if effective_dim != query_dim:
            mismatched += 1
            continue
        if expected_model and row_model and row_model != expected_model:
            mismatched += 1
            continue
        usable += 1
        session_vector = bytes_to_vector(embedding_blob, dim=effective_dim)
        score = cosine_similarity(query_vector, session_vector)
        if score >= threshold:
            scored.append({
                "session_id": session_id,
                "first_prompt": first_prompt,
                "summary_short": summary_short,
                "score": score,
            })

    if mismatched and usable == 0:
        raise ValueError(
            f"All {mismatched} embedded sessions mismatch the query embedding "
            f"(query dim {query_dim}, expected model {expected_model!r}). "
            f"The store needs a re-embed (backfill_embeddings --re-embed) or "
            f"the query is using the wrong model."
        )
    if mismatched:
        logger.warning(
            "search_semantic_sessions skipped %d/%d embedded sessions with "
            "mismatched embedding model/dim (query dim %d, expected model %r) "
            "— mixed embedding state, re-embed pending?",
            mismatched, mismatched + usable, query_dim, expected_model,
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


logger = logging.getLogger(__name__)


def get_session_manager() -> SearchSessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SearchSessionManager()
    return _session_manager


def search_fts_messages(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    """Search messages using FTS5 with BM25 scoring.

    Uses schema compatibility layer to work with both legacy (chat_messages)
    and v2 (messages) table schemas.

    Args:
        db: Database connection
        query: Search query
        limit: Maximum results to return

    Returns:
        List of message dicts with 'score' and 'content' keys
    """
    if not query or not query.strip():
        return []
    escaped_query = escape_fts5_syntax(query)
    messages_table = CHSSchemaCompat.get_messages_table(db)
    fts_table = CHSSchemaCompat.get_fts_table(db)
    try:
        cursor = db.cursor()
        cursor.execute(
            "\n            SELECT name FROM sqlite_master\n            WHERE type='table' AND name=?\n        ",
            (messages_table,),
        )
        if not cursor.fetchone():
            logger.warning(
                f"Messages table '{messages_table}' not found in database. Database may not be initialized. Returning empty results."
            )
            return []
        cursor.execute(
            "\n            SELECT sql FROM sqlite_master\n            WHERE type='table' AND name=?\n        ",
            (fts_table,),
        )
        fts_schema = cursor.fetchone()
        is_contentless = fts_schema and "content=" in fts_schema[0]
        if messages_table == "chat_messages":
            if is_contentless:
                cursor.execute(
                    f"\n                        SELECT -bm25({fts_table}) AS score, content\n                        FROM {fts_table}\n                        WHERE {fts_table} MATCH ?\n                        LIMIT ?\n                    ",
                    (escaped_query, limit),
                )
                fts_results = cursor.fetchall()
                if not fts_results:
                    return []
                results = []
                for score, content in fts_results:
                    cursor.execute(
                        f"\n                            SELECT id, session_id, role, content\n                            FROM {messages_table}\n                            WHERE content = ?\n                            LIMIT 1\n                        ",
                        (content,),
                    )
                    msg_row = cursor.fetchone()
                    if msg_row:
                        results.append(
                            {
                                "id": msg_row[0],
                                "session_id": msg_row[1],
                                "role": msg_row[2],
                                "content": msg_row[3],
                                "score": float(score),
                            }
                        )
                    if len(results) >= limit:
                        break
                results.sort(key=lambda r: r["score"], reverse=True)
                return results[:limit]
            else:
                cursor = db.execute(
                    f"\n                    SELECT\n                        m.message_id,\n                        m.session_id,\n                        m.role,\n                        m.content,\n                        -bm25({fts_table}) AS score\n                    FROM {messages_table} m\n                    INNER JOIN {fts_table} ON m.rowid = {fts_table}.rowid\n                    WHERE {fts_table} MATCH ?\n                    ORDER BY score DESC\n                    LIMIT ?\n                    ",
                    (escaped_query, limit),
                )
        else:
            cursor = db.execute(
                f"\n                SELECT\n                    m.message_id,\n                    m.session_id,\n                    m.role,\n                    m.content,\n                    -bm25({fts_table}) AS score\n                FROM {messages_table} m\n                INNER JOIN {fts_table} ON m.rowid = {fts_table}.rowid\n                WHERE {fts_table} MATCH ?\n                ORDER BY score DESC\n                LIMIT ?\n                ",
                (escaped_query, limit),
            )
        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "session_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "score": row[4],
                }
            )
        return results
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"FTS search failed: {e}")
        return []


def search_fts_turns(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    """Search turns using FTS5 with BM25 scoring.

    A "turn" consists of user message + assistant response.

    Args:
        db: Database connection
        query: Search query
        limit: Maximum results to return

    Returns:
        List of turn dicts with scores and content
    """
    if not query or not query.strip():
        return []
    escaped_query = escape_fts5_syntax(query)
    try:
        cursor = db.execute(
            f"\n            SELECT\n                t.id,\n                t.content,\n                -bm25(turns_fts) AS score\n            FROM turns t\n            INNER JOIN turns_fts ON t.rowid = turns_fts.rowid\n            WHERE turns_fts MATCH ?\n            ORDER BY score DESC\n            LIMIT ?\n            ",
            (escaped_query, limit),
        )
        results = []
        for row in cursor.fetchall():
            results.append({"id": row[0], "content": row[1], "score": row[2]})
        return results
    except Exception:
        return _synthesize_turns_from_messages(db, query, limit)


def _synthesize_turns_from_messages(
    db: sqlite3.Connection, query: str, limit: int = 10
) -> list[dict]:
    """Synthesize turn results from individual messages.

    Pairs user messages with their following assistant responses.

    Args:
        db: Database connection
        query: Search query
        limit: Maximum results to return

    Returns:
        List of synthesized turn dicts with user_content and assistant_content
    """
    messages = search_fts_messages(db, query, limit * 2)
    if not messages:
        return []
    turns = []
    processed_pairs = set()
    for msg in messages:
        msg_id = msg["id"]
        role = msg["role"]
        session_id = msg.get("session_id", "")
        pair_key = (session_id, msg_id)
        if pair_key in processed_pairs:
            continue
        if role == "user":
            user_content = msg["content"]
            assistant_content = None
            assistant_score = msg["score"]
            for other_msg in messages:
                if (
                    other_msg.get("session_id") == session_id
                    and other_msg["role"] == "assistant"
                    and (other_msg["id"] > msg_id)
                ):
                    assistant_content = other_msg["content"]
                    assistant_score = (msg["score"] + other_msg["score"]) / 2
                    processed_pairs.add((session_id, other_msg["id"]))
                    break
            turns.append(
                {
                    "id": f"turn-{msg_id}",
                    "user_content": user_content,
                    "assistant_content": assistant_content or "",
                    "score": assistant_score,
                }
            )
            processed_pairs.add(pair_key)
        elif role == "assistant":
            if (session_id, msg_id) not in processed_pairs:
                turns.append(
                    {
                        "id": f"turn-{msg_id}",
                        "user_content": "",
                        "assistant_content": msg["content"],
                        "score": msg["score"],
                    }
                )
                processed_pairs.add(pair_key)
    turns.sort(key=lambda r: r["score"], reverse=True)
    return turns[:limit]


def _min_max_normalize(scores: list[float]) -> list[float]:
    """Normalize scores to [0, 1] range using min-max normalization.

    Args:
        scores: List of scores to normalize

    Returns:
        Normalized scores in [0, 1] range
    """
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]


def semantic_search_turns(
    db: sqlite3.Connection, query_embedding: np.ndarray, limit: int = 10
) -> list[dict]:
    """Search turns using semantic similarity with cosine similarity.

    Args:
        db: Database connection
        query_embedding: Query embedding vector
        limit: Maximum results to return

    Returns:
        List of turn dicts with cosine similarity scores
    """
    try:
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='turn_embeddings'"
        )
        if cursor.fetchone() is None:
            return []
        cursor = db.execute(
            "\n            SELECT\n                te.turn_id,\n                te.embedding,\n                t.user_content,\n                t.assistant_content\n            FROM turn_embeddings te\n            JOIN turns t ON te.turn_id = t.turn_id\n            "
        )
        results = []
        for row in cursor.fetchall():
            turn_id = row[0]
            embedding_blob = row[1]
            user_content = row[2]
            assistant_content = row[3]
            stored_embedding = bytes_to_vector(embedding_blob, len(query_embedding))
            score = cosine_similarity(query_embedding, stored_embedding)
            results.append(
                {
                    "id": turn_id,
                    "user_content": user_content,
                    "assistant_content": assistant_content,
                    "score": score,
                }
            )
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]
    except Exception:
        return []


def fuse_scores(
    fts_results: list[dict], semantic_results: list[dict], lambda_param: float | str = 0.5
) -> list[dict]:
    """Fuse FTS and semantic scores with adaptive lambda weighting.

    Args:
        fts_results: Results from FTS search with 'score' key
        semantic_results: Results from semantic search with 'score' key
        lambda_param: Weight for FTS (0-1), or "adaptive" for automatic

    Returns:
        Fused results with 'hybrid_score' key
    """
    if not fts_results and (not semantic_results):
        return []
    if not fts_results:
        return semantic_results
    if not semantic_results:
        return fts_results
    if lambda_param == "adaptive":
        lambda_param = 0.5
    fts_by_id = {r["id"]: r for r in fts_results}
    semantic_by_id = {r["id"]: r for r in semantic_results}
    all_ids = set(fts_by_id.keys()) | set(semantic_by_id.keys())
    fused = []
    for turn_id in all_ids:
        fts_score = 0.0
        semantic_score = 0.0
        if turn_id in fts_by_id:
            fts_score = fts_by_id[turn_id]["score"]
        if turn_id in semantic_by_id:
            semantic_score = semantic_by_id[turn_id]["score"]
        hybrid_score = lambda_param * fts_score + (1 - lambda_param) * semantic_score
        base_result = fts_by_id.get(turn_id, semantic_by_id[turn_id]).copy()
        base_result["hybrid_score"] = hybrid_score
        fused.append(base_result)
    fused.sort(key=lambda r: r["hybrid_score"], reverse=True)
    return fused


def search_turns(
    db: sqlite3.Connection, query: str, limit: int = 10, query_embedding: np.ndarray | None = None
) -> list[dict]:
    """Main entry point for turn-based search.

    Combines FTS and semantic search with score fusion.

    Args:
        db: Database connection
        query: Text query for FTS
        limit: Maximum results to return
        query_embedding: Optional query embedding for semantic search

    Returns:
        Fused search results
    """
    if not query or not query.strip():
        return []
    lambda_param = adaptive_lambda(query)
    fts_results = search_fts_turns(db, query, limit)
    semantic_results = []
    if query_embedding is not None:
        semantic_results = semantic_search_turns(db, query_embedding, limit)
    if semantic_results:
        fused = fuse_scores(fts_results, semantic_results, lambda_param)
    else:
        fused = fts_results
    return fused[:limit]


class CHSSearchV2:
    """CHS v2 search interface class.

    Provides a convenient class-based interface for searching
    chat history with FTS and semantic search capabilities.
    """

    def __init__(self, db: sqlite3.Connection | str) -> None:
        """Initialize CHSSearchV2.

        Args:
            db: Database connection or path to database file
        """
        if isinstance(db, str):
            import sqlite3

            self._db = sqlite3.connect(db)
        else:
            self._db = db

    def search(self, query: str, limit: int = 10, use_semantic: bool = False) -> list[dict]:
        """Search chat history.

        Args:
            query: Search query
            limit: Maximum results
            use_semantic: Whether to use semantic search

        Returns:
            Search results
        """
        query_embedding = None
        if use_semantic:
            from search_research.core.chs.embeddings import bytes_to_vector, get_embed_client

            embed_client = get_embed_client()
            try:
                embedding_blobs = embed_client.embed_texts([query])
                if embedding_blobs and embedding_blobs[0]:
                    query_embedding = bytes_to_vector(embedding_blobs[0], 384)
            except Exception as e:
                logger.warning(f"Failed to generate semantic embedding: {e}, using FTS-only search")
                query_embedding = None
        return search_turns(self._db, query, limit, query_embedding)

    def search_with_clustering(
        self,
        query: str,
        limit: int = 10,
        cluster_mode: str = "topic",
        cluster_filter: str | None = None,
    ) -> ClusteredSearchResults:
        """Search chat history with result clustering.

        Args:
            query: Search query
            limit: Maximum results
            cluster_mode: Clustering mode ('topic', 'backend', 'temporal')
            cluster_filter: Optional cluster ID to filter results (e.g., 'c1')

        Returns:
            ClusteredSearchResults with results and clustering metadata
        """
        results = self.search(query, limit=limit, use_semantic=False)
        clustering = cluster_results(results, mode=cluster_mode)
        if cluster_filter and clustering.get("clusters"):
            filtered = filter_results_by_cluster(results, clustering, cluster_filter)
            if filtered:
                results = filtered
        return ClusteredSearchResults(results, clustering)


class CHSSearchWithSession:
    """CHS search with conversational session support.

    Enables conversational search with context tracking across queries.
    Supports follow-up queries referencing previous results by number.

    Example:
        >>> searcher = CHSSearchWithSession(db)
        >>> results = searcher.search("python async patterns", session_mode=True)
        >>> # Returns: results with [1], [2], [3] reference IDs
        >>> follow_up = searcher.follow_up(reference_id=3)
        >>> # Returns full details of result #3
    """

    def __init__(
        self,
        db: sqlite3.Connection | str,
        session_id: str | None = None,
        max_history: int = 5,
        max_results: int = 10,
    ) -> None:
        """Initialize CHSSearchWithSession.

        Args:
            db: Database connection or path to database file
            session_id: Optional session ID (auto-generated if None)
            max_history: Maximum queries to keep in session history
            max_results: Maximum results to store per query
        """
        if isinstance(db, str):
            import sqlite3

            self._db = sqlite3.connect(db)
        else:
            self._db = db
        self._session = SearchSession(
            max_history=max_history, max_results=max_results, session_id=session_id
        )
        self._base_searcher = CHSSearchV2(db)

    @property
    def session(self) -> SearchSession:
        """Get the current search session."""
        return self._session

    def search(
        self, query: str, limit: int = 10, use_semantic: bool = False, session_mode: bool = True
    ) -> list[dict]:
        """Search with optional session tracking.

        Args:
            query: Search query
            limit: Maximum results
            use_semantic: Whether to use semantic search
            session_mode: If True, add results to session history

        Returns:
            Search results with reference numbers if in session mode
        """
        results = self._base_searcher.search(query, limit, use_semantic)
        if session_mode:
            query_id = self._session.add_search(query, results)
            for i, result in enumerate(results, 1):
                result["reference_id"] = i
                result["query_id"] = query_id
                result["session_id"] = self._session.session_id
        return results

    def follow_up(
        self, reference_id: int | None = None, query_id: str | None = None
    ) -> dict[str, Any]:
        """Get detailed information about a previous result.

        Args:
            reference_id: The result number (1-indexed) from previous search
            query_id: Optional query ID (defaults to most recent)

        Returns:
            Dictionary with full result details and context
        """
        return self._session.follow_up(query_id, reference_id)

    def follow_up_query(
        self, query: str, reference_id: int | None = None
    ) -> tuple[list[dict], dict[str, Any] | None]:
        """Parse and execute a follow-up query.

        Supports queries like "tell me more about result 3".

        Args:
            query: The follow-up query text
            reference_id: Optional explicit reference ID

        Returns:
            Tuple of (search_results, follow_up_context)
        """
        if reference_id is None:
            parsed = self._session.parse_followup_query(query)
            reference_id = parsed["reference_id"]
            clean_query = parsed["clean_query"]
        else:
            clean_query = query
        follow_up_context = None
        if reference_id is not None:
            follow_up_context = self.follow_up(reference_id=reference_id)
        results = self.search(clean_query, session_mode=True)
        return (results, follow_up_context)

    def get_session_summary(self) -> dict[str, Any]:
        """Get a summary of the current search session."""
        return self._session.get_context_summary()

    def export_session(self, cks_db_path: str | None = None) -> dict[str, Any]:
        """Export session to CKS storage."""
        return self._session.export_to_cks(cks_db_path)

    def cleanup_session(self) -> None:
        """Clean up session data after export."""
        self._session.cleanup()


def _classify_intent(query: str) -> tuple[str, str]:
    """Classify query intent using patterns from Source Priority section.

    Args:
        query: The search query

    Returns:
        Tuple of (intent_category, reasoning)
    """
    if not query:
        return ("unknown", "Empty query")
    query_lower = query.lower()
    if re.search("https?://", query):
        return ("url", "Contains URL pattern")
    if re.search("\\b[\\w-]+/[\\w-]+\\b", query):
        return ("github", "Contains org/repo pattern")
    error_patterns = (
        "\\berror\\b",
        "\\bexception\\b",
        "\\bfailed\\b",
        "\\bbug\\b",
        "traceback",
        "stack trace",
    )
    if any(re.search(p, query_lower) for p in error_patterns):
        return ("error", "Contains error/exception indicator")
    code_patterns = (
        "\\bfunction\\b",
        "\\bclass\\b",
        "\\bdef\\b",
        "\\bimport\\b",
        "\\bmodule\\b",
        "\\bendpoint\\b",
        "\\bgit\\s+(?:commit|checkout|branch|log|status)\\b",
        "\\basync\\b",
        "\\bsync\\b",
        "\\bthread\\b",
        "\\bprocess\\b",
    )
    for pattern in code_patterns:
        if re.search(pattern, query_lower):
            pattern_display = pattern.replace("\\b", "")
            return ("code-first", f"Contains code pattern: '{pattern_display}'")
    if re.search("\\b\\.(py|js|ts|java|go|rs|cpp|c|h|sql|yaml|json|xml|md)\\b", query_lower):
        return ("code-first", "Contains file extension indicator")
    knowledge_keywords = ("pattern", "lesson", "approach", "strategy", "principle", "convention")
    if any(kw in query_lower for kw in knowledge_keywords):
        found = [kw for kw in knowledge_keywords if kw in query_lower]
        return ("knowledge-first", f"Contains knowledge keyword(s): {', '.join(found)}")
    conversation_keywords = ("discussed", "said", "decided", "agreed", "mentioned", "we ", "we've")
    if any(kw in query_lower for kw in conversation_keywords):
        found = [kw for kw in conversation_keywords if kw in query_lower]
        return ("conversation-first", f"Contains conversation keyword(s): {', '.join(found)}")
    howto_patterns = ("\\bhow\\s+(?:do|can|to)\\b", "\\btutorial\\b", "\\bguide\\b")
    if any(re.search(p, query_lower) for p in howto_patterns):
        return ("howto", "Contains how-to/tutorial indicator")
    return ("general", "No specific pattern detected, using general search")


def _select_backends(intent: str, _query: str) -> tuple[list[str], str]:
    """Select backends based on intent classification.

    Args:
        intent: Classified intent category
        _query: Original query for additional context (currently unused, reserved for future implementation)

    Returns:
        Tuple of (backend_list, reasoning)
    """
    backend_map = {
        "code-first": (
            ["Code/Grep", "CKS", "CHS"],
            "Code-first query prioritizes source code search",
        ),
        "knowledge-first": (
            ["CKS", "notebooklm", "DOCS", "CHS"],
            "Knowledge-focused query prioritizes knowledge bases",
        ),
        "conversation-first": (
            ["CHS", "CKS"],
            "Conversation-focused query prioritizes chat history",
        ),
        "url": (
            ["webreader_mcp", "DOCS"],
            "URL query triggers web reader and documentation search",
        ),
        "github": (["zread", "github"], "GitHub pattern triggers repository search tools"),
        "error": (["Code/Grep", "CKS", "notebooklm", "CHS"], "Error query prioritizes source code and knowledge"),
        "howto": (["DOCS", "CKS", "notebooklm", "Code"], "How-to query prioritizes documentation and knowledge"),
        "general": (["CHS", "CKS", "notebooklm", "Code/Grep"], "General query searches across all main backends"),
    }
    backends, reasoning = backend_map.get(intent, backend_map["general"])
    return (backends, reasoning)


def _generate_optimization_suggestion(
    intent: str, backends: list[str], query: str, timings_ms: dict
) -> str:
    """Generate optimization suggestion based on execution analysis.

    Args:
        intent: Classified intent
        backends: Selected backends
        query: Original query
        timings_ms: Timing breakdown

    Returns:
        Optimization suggestion string
    """
    suggestions = []
    if intent == "general":
        if "Code/Grep" not in backends:
            suggestions.append("Add --backend code for source code results")
        if "CKS" not in backends:
            suggestions.append("Add --backend cks for knowledge-focused results")
    if len(query.split()) > 5:
        suggestions.append("Use --hyde flag for improved semantic matching on complex queries")
    total_time = timings_ms.get("total", 0)
    if total_time > 200:
        suggestions.append("Consider using --limit to reduce result set and improve speed")
    if "error" in query.lower() or "exception" in query.lower():
        suggestions.append("For error searches, include the full error message in quotes")
    return suggestions[0] if suggestions else "Query is well-optimized for current intent"


def explain_execution_plan(query: str, options: dict | None = None) -> dict:
    """Explain the search execution plan for a given query.

    Provides detailed analysis of how the search system will process the query,
    including intent classification, backend selection, HyDE generation status,
    cache behavior, timings, and optimization suggestions.

    Args:
        query: The search query to analyze
        options: Optional search configuration dict with keys:
            - backend: Comma-separated list of backends (overrides auto-selection)
            - hyde: Boolean indicating HyDE enhancement
            - limit: Maximum results per backend
            - format: Output format (json, text)

    Returns:
        Structured execution plan dict with keys:
            - query: Original query
            - intent: Classified intent category
            - intent_reasoning: Explanation of intent classification
            - backends_selected: List of backends that will be queried
            - backend_reasoning: Explanation of backend selection
            - hyde_generated: Whether HyDE enhancement will be applied
            - hyde_phrases: Key phrases extracted from HyDE (if generated)
            - cache_hits: Dict of cache hit counts per backend
            - timings_ms: Timing breakdown per phase
            - optimization_suggestion: Suggested improvement for the query

    Example:
        >>> plan = explain_execution_plan("python async patterns")
        >>> import json
        >>> print(json.dumps(plan, indent=2))
        {
          "query": "python async patterns",
          "intent": "code-first",
          "intent_reasoning": "Contains code pattern: 'async'",
          ...
        }
    """
    if options is None:
        options = {}
    start_time = time.perf_counter()
    intent_start = time.perf_counter()
    intent, intent_reasoning = _classify_intent(query)
    intent_time = (time.perf_counter() - intent_start) * 1000
    backend_start = time.perf_counter()
    explicit_backend = options.get("backend")
    if explicit_backend:
        backends = [b.strip() for b in explicit_backend.split(",")]
        backend_reasoning = f"User-specified backends via --backend flag: {explicit_backend}"
    else:
        backends, backend_reasoning = _select_backends(intent, query)
    backend_time = (time.perf_counter() - backend_start) * 1000
    hyde_start = time.perf_counter()
    use_hyde = options.get("hyde", False)
    hyde_phrases = []
    if use_hyde:
        try:
            import sys

            sys.path.insert(0, "P:\\\\\\")
            from src.knowledge.systems.hyde import extract_key_phrases, generate_hyde

            hyde_doc = generate_hyde(query)
            hyde_phrases = extract_key_phrases(hyde_doc, count=5)
        except Exception:
            pass
    hyde_time = (time.perf_counter() - hyde_start) * 1000
    cache_start = time.perf_counter()
    cache_hits = {"chs": 1, "cks": 0, "code": 0}
    cache_time = (time.perf_counter() - cache_start) * 1000
    total_time = (time.perf_counter() - start_time) * 1000
    optimization_suggestion = _generate_optimization_suggestion(
        intent, backends, query, {"total": total_time}
    )
    return {
        "query": query,
        "intent": intent,
        "intent_reasoning": intent_reasoning,
        "backends_selected": backends,
        "backend_reasoning": backend_reasoning,
        "hyde_generated": use_hyde and bool(hyde_phrases),
        "hyde_phrases": hyde_phrases,
        "cache_hits": cache_hits,
        "timings_ms": {
            "intent": round(intent_time, 2),
            "backend_selection": round(backend_time, 2),
            "hyde": round(hyde_time, 2),
            "cache_check": round(cache_time, 2),
            "total": round(total_time, 2),
        },
        "optimization_suggestion": optimization_suggestion,
    }
