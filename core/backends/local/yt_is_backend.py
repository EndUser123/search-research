"""YouTube Transcript Backend - searches cached transcripts via FTS5."""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from ...models import SearchResult

logger = logging.getLogger(__name__)

# DB paths
_TRANSCRIPT_DB = Path("P:\\\\\\__csf/.data/yt-is/transcripts.sqlite")
_BATCH_DB = Path("P:\\\\\\__csf/.data/yt-is/batch_status.sqlite")
_FTS_TABLE = "transcript_fts"

REBUILD_FAILURE_LIMIT = 3
REBUILD_COOLDOWN = 60.0
MAX_QUERY_LENGTH = 500
MAX_SNIPPET = 300


class YtIsBackend:
    """Searches YouTube video transcripts cached in transcripts.sqlite.

    Uses FTS5 for full-text search over denormalized content: title + description + transcript.
    The FTS table is built from a LEFT JOIN of transcript_cache with analysis_status on video_id,
    so results include meaningful video titles even when batch_status has no entry.
    """

    BACKEND_NAME = "yt-is"
    TIMEOUT = 5.0  # seconds for FTS queries
    BATCH_SIZE = 100  # rows per batch INSERT

    def __init__(self) -> None:
        self._index_mtime: float | None = None
        self._rebuild_lock = threading.Lock()
        self._rebuild_failures = 0
        self._rebuild_cooldown_until: float | None = None
        self._rebuild_in_progress = False  # Tracks if a rebuild is currently running

    def _get_db_mtime(self) -> float | None:
        """Return mtime of transcript DB as index freshness surrogate."""
        if not _TRANSCRIPT_DB.exists():
            return None
        try:
            return os.path.getmtime(_TRANSCRIPT_DB)
        except OSError:
            return None

    def _ensure_fts(self) -> bool:
        """Ensure FTS5 virtual table exists. Returns True if FTS is ready."""
        if not _TRANSCRIPT_DB.exists():
            return False
        try:
            conn = sqlite3.connect(str(_TRANSCRIPT_DB))
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (_FTS_TABLE,),
            )
            if cur.fetchone() is not None:
                conn.close()
                return True
            conn.close()
            return False
        except Exception:
            return False

    def _sanitize_query(self, query: str) -> str:
        """Limit query length and strip non-printable characters."""
        return "".join(c for c in query if c.isprintable() or c in " ")[:MAX_QUERY_LENGTH]

    def _fts_search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Execute FTS5 search and return results."""
        conn = sqlite3.connect(str(_TRANSCRIPT_DB))
        conn.row_factory = sqlite3.Row
        try:
            # FTS5 bm25() returns score at query time (lower=better, negate for DESC)
            rows = conn.execute(
                f"""
                SELECT title, snippet,
                       -bm25({_FTS_TABLE}) AS score, video_id,
                       'https://youtube.com/watch?v=' || video_id AS url
                FROM {_FTS_TABLE}
                WHERE {_FTS_TABLE} MATCH ?
                ORDER BY score DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        finally:
            conn.close()

        results = []
        for row in rows:
            title = row["title"] or row["video_id"]
            snippet = row["snippet"] or ""
            if len(snippet) > MAX_SNIPPET:
                snippet = snippet[:MAX_SNIPPET] + "..."
            results.append(SearchResult(
                title=title,
                content=snippet,
                source=self.BACKEND_NAME,
                score=row["score"] or 0.0,
                file_path=row["video_id"],
                url=row["url"],
            ))
        return results

    async def search_async(self, query: str, limit: int = 10, **kwargs) -> list[SearchResult]:
        query = self._sanitize_query(query)
        if not query:
            return []

        # Run FTS search in thread pool to avoid blocking the event loop.
        # The sqlite3 calls are thread-safe and this allows concurrent execution
        # with other async backends during the gather.
        try:
            results = await asyncio.to_thread(self._fts_search, query, limit)
            self._rebuild_failures = 0
            self._index_mtime = self._get_db_mtime()
            # If FTS5 is empty but transcript_cache has data, trigger lazy rebuild
            if not results and self._ensure_fts():
                db_mtime = self._get_db_mtime()
                index_mtime = self._index_mtime
                if db_mtime and (index_mtime is None or db_mtime > index_mtime):
                    self._trigger_lazy_rebuild()
            return results
        except Exception as e:
            logger.debug(f"yt-is FTS search failed: {e}")
            return []

    def _trigger_lazy_rebuild(self) -> None:
        """Trigger a lazy background rebuild if one isn't already running.

        Called after an empty-result search when the DB has newer data than the index.
        Runs rebuild in thread pool without blocking the event loop.
        """
        if self._rebuild_in_progress:
            return
        with self._rebuild_lock:
            if self._rebuild_in_progress:
                return
            self._rebuild_in_progress = True
        # Detach rebuild so it doesn't block the caller
        import threading
        t = threading.Thread(target=self._lazy_build_wrapper, daemon=True)
        t.start()

    def _lazy_build_wrapper(self) -> None:
        """Wrapper for lazy rebuild that resets the in-progress flag on completion."""
        try:
            self._sync_build_fts()
        except Exception as e:
            logger.debug(f"yt-is lazy FTS build failed: {e}")
            self._rebuild_failures += 1
            self._update_cooldown()
        finally:
            self._rebuild_in_progress = False

    def build_index(self) -> None:
        """Build or rebuild the FTS5 table from transcript_cache + analysis_status join.

        Called from a thread pool (via asyncio.to_thread) so must be safe to run
        concurrently with search_async on the main thread.
        """
        if not _TRANSCRIPT_DB.exists():
            logger.debug("yt-is transcripts DB not found, skipping index build")
            self._rebuild_in_progress = False
            return

        with self._rebuild_lock:
            # Cooldown check
            import time
            if (
                self._rebuild_cooldown_until is not None
                and time.monotonic() < self._rebuild_cooldown_until
            ):
                self._rebuild_in_progress = False
                return

            try:
                self._sync_build_fts()
                self._rebuild_failures = 0
                self._rebuild_cooldown_until = None
            except Exception as e:
                logger.debug(f"yt-is FTS build failed: {e}")
                self._rebuild_failures += 1
                self._update_cooldown()
            finally:
                self._rebuild_in_progress = False

    def _sync_build_fts(self) -> None:
        """Synchronously rebuild FTS table from joined transcript + metadata."""
        conn = sqlite3.connect(str(_TRANSCRIPT_DB))
        conn.row_factory = sqlite3.Row
        try:
            # Check if batch_status table is accessible and build lookup map
            has_batch = False
            batch_map: dict[str, tuple] = {}
            try:
                batch_conn = sqlite3.connect(str(_BATCH_DB))
                batch_conn.row_factory = sqlite3.Row
                batch_conn.execute("SELECT video_id FROM analysis_status LIMIT 1")
                has_batch = True
                for row in batch_conn.execute(
                    "SELECT video_id, title, description FROM analysis_status"
                ):
                    batch_map[row["video_id"]] = (row["title"], row["description"])
            except Exception:
                pass
            finally:
                if has_batch:
                    batch_conn.close()

            # Build denormalized FTS content from join
            # Note: analysis_status is in batch_status.sqlite (different DB),
            # so join is done in Python, not SQL.
            rows = []
            for row in conn.execute("SELECT video_id, transcript FROM transcript_cache"):
                video_id = row["video_id"]
                if has_batch:
                    meta = batch_map.get(video_id, (None, None))
                    title = meta[0] or video_id
                    description = meta[1] or ""
                else:
                    title = video_id
                    description = ""
                transcript = row["transcript"] or ""
                rows.append({
                    "video_id": video_id,
                    "title": title,
                    "description": description,
                    "transcript": transcript,
                    "snippet": transcript[:MAX_SNIPPET],
                    "content": f"{title} {description} {transcript}",
                })
        finally:
            conn.close()

        # Drop and recreate FTS table
        conn2 = sqlite3.connect(str(_TRANSCRIPT_DB))
        try:
            conn2.execute(f"DROP TABLE IF EXISTS {_FTS_TABLE}")
            conn2.execute(f"""
                CREATE VIRTUAL TABLE {_FTS_TABLE} USING fts5(
                    title,
                    description,
                    transcript,
                    content,
                    snippet,
                    video_id UNINDEXED,
                    tokenize='porter unicode61'
                )
            """)

            # Batch insert: accumulate rows and insert in batches
            batch = []
            for row_data in rows:
                batch.append((
                    row_data["title"],
                    row_data["description"],
                    row_data["transcript"],
                    row_data["content"],
                    row_data["snippet"],
                    row_data["video_id"],
                ))
                if len(batch) >= self.BATCH_SIZE:
                    try:
                        conn2.executemany(
                            f"""INSERT INTO {_FTS_TABLE}
                                (title, description, transcript, content, snippet, video_id)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                            batch,
                        )
                    except Exception as e:
                        logger.debug(f"yt-is FTS batch insert failed: {e}")
                    batch = []

            # Insert remaining rows
            if batch:
                try:
                    conn2.executemany(
                        f"""INSERT INTO {_FTS_TABLE}
                            (title, description, transcript, content, snippet, video_id)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                        batch,
                    )
                except Exception as e:
                    logger.debug(f"yt-is FTS batch insert failed: {e}")

            conn2.commit()
            conn2.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn2.close()

        self._index_mtime = self._get_db_mtime()

    def _update_cooldown(self) -> None:
        """After 3 failures, skip rebuild for 60 seconds."""
        import time
        if self._rebuild_failures >= REBUILD_FAILURE_LIMIT:
            self._rebuild_cooldown_until = time.monotonic() + REBUILD_COOLDOWN
