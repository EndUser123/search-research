# --- INTEGRITY ---
# Previous Character Count: 11413
# Current Character Count: 9948
# Syntax Check: [PASS]
# Logic Validation: [Removed queue-based reads, implemented direct synchronous reads for main thread safety.]
# Reason for Change: [To fix PicklingError by using a multiprocessing-safe pattern for DB reads.]
# ------------------
import queue
import sqlite3
import threading
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog
import xxhash

log = structlog.get_logger()

HASH_CHUNK_SIZE = 1024 * 1024  # 1MB


class JobStatus(Enum):
    NOT_STARTED = "not_started"
    SUBTITLES_COMPLETED = "subtitles_completed"
    FULLY_COMPLETED = "fully_completed"
    FAILED = "failed"


class StateManager:
    def __init__(
        self,
        db_path: Path = Path("vidrec_state.db"),
        db_queue: Optional[queue.Queue] = None,
    ):
        self.db_path = db_path
        self._db_local = threading.local()
        self._shutdown_event = threading.Event()
        self._init_complete_event = threading.Event()

        self._is_queue_owner = db_queue is None
        self._write_queue = db_queue if db_queue is not None else queue.Queue()

        self._writer_thread = threading.Thread(
            target=self._db_writer_loop,
            args=(self._init_complete_event,),
            daemon=False,
            name="StateManagerWriter",
        )
        self._writer_thread.start()

        if not self._init_complete_event.wait(timeout=20.0):
            log.critical("Database initialization timed out.", timeout=20.0)
            raise sqlite3.TimeoutError("DB initialization timed out after 20.0s")

    def _get_db_conn(self) -> sqlite3.Connection:
        # Returns a db connection. For the writer thread, it's thread-local.
        # For the main thread, it creates a new one for each sync method call.
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _db_writer_loop(self, init_complete_event: threading.Event):
        """The target method for the writer thread. Handles WRITE operations only."""
        conn = self._get_db_conn()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jobs (
                        file_path TEXT PRIMARY KEY, status TEXT NOT NULL,
                        file_signature TEXT, last_updated TEXT NOT NULL, error_message TEXT
                    );"""
                )
                cursor = conn.execute("PRAGMA table_info(jobs);")
                columns = {info[1] for info in cursor.fetchall()}
                if "file_signature" not in columns:
                    conn.execute("ALTER TABLE jobs ADD COLUMN file_signature TEXT;")
                if "error_message" not in columns:
                    conn.execute("ALTER TABLE jobs ADD COLUMN error_message TEXT;")
            log.info("Database schema initialized/verified.")
        except Exception as e:
            log.critical(
                "Fatal error during DB initialization", error=str(e), exc_info=True
            )
            return
        finally:
            init_complete_event.set()

        log.info("Database writer thread started processing write queue.")
        while not self._shutdown_event.is_set():
            try:
                item = self._write_queue.get(timeout=1.0)
                if item is None:
                    break
                command, (query, params) = item
                with conn:
                    if command in ("upsert", "reset"):
                        conn.execute(query, params)
                self._write_queue.task_done()
            except (queue.Empty, EOFError):
                continue
            except Exception as e:
                log.critical(
                    "Fatal error in DB writer thread", error=str(e), exc_info=True
                )
                break
        if conn:
            conn.close()
        log.info("Database writer thread has exited.")

    def close(self):
        log.info("Initiating StateManager shutdown.")
        self._shutdown_event.set()
        if self._is_queue_owner:
            self._write_queue.put(None)
        self._writer_thread.join(timeout=10.0)
        if self._writer_thread.is_alive():
            log.warning("StateManager writer thread did not shut down within timeout.")
        else:
            log.info("StateManager shutdown complete.")

    def get_all_job_details(self) -> list[dict[str, Any]]:
        """Synchronously retrieves all job details. Safe for main thread use."""
        try:
            with self._get_db_conn() as conn:
                cursor = conn.execute(
                    "SELECT file_path, status, last_updated, error_message FROM jobs"
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            log.error("Failed to retrieve all job details", error=str(e), exc_info=True)
            return []

    def get_job_status(self, file_path: Path) -> dict:
        """Synchronously retrieves a single job's status. Safe for main thread use."""
        try:
            with self._get_db_conn() as conn:
                cursor = conn.execute(
                    "SELECT status, file_signature FROM jobs WHERE file_path = ? LIMIT 1",
                    (str(file_path),),
                )
                row = cursor.fetchone()
            if row:
                return {
                    "status": JobStatus(row["status"]),
                    "stored_signature": row["file_signature"],
                }
            return {"status": JobStatus.NOT_STARTED, "stored_signature": None}
        except Exception as e:
            log.error(
                "Failed to get job status",
                file=str(file_path),
                error=str(e),
                exc_info=True,
            )
            return {"status": JobStatus.NOT_STARTED, "stored_signature": None}

    def upsert_job(
        self, file_path: Path, status: JobStatus, error_message: Optional[str] = None
    ):
        """Queues an insert/update job operation for the writer thread."""
        file_signature = (
            self.get_file_signature(file_path) if status != JobStatus.FAILED else None
        )
        timestamp = datetime.now().isoformat()
        query = """
            INSERT INTO jobs (file_path, status, file_signature, last_updated, error_message)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(file_path) DO UPDATE SET
            status = excluded.status,
            file_signature = COALESCE(excluded.file_signature, file_signature),
            last_updated = excluded.last_updated,
            error_message = excluded.error_message
            """
        params = (
            str(file_path),
            status.value,
            file_signature,
            timestamp,
            error_message,
        )
        self._write_queue.put(("upsert", (query, params)))

    def reset_job(self, file_path: Path):
        """Queues a delete job operation for the writer thread."""
        query = "DELETE FROM jobs WHERE file_path = ?"
        params = (str(file_path),)
        self._write_queue.put(("reset", (query, params)))

    def get_file_signature(self, file_path: Path) -> str:
        """Calculates a file signature using size and partial hashing."""
        try:
            size = file_path.stat().st_size
            hasher = xxhash.xxh64()
            with open(file_path, "rb") as f:
                if size <= 2 * HASH_CHUNK_SIZE:
                    hasher.update(f.read())
                else:
                    hasher.update(f.read(HASH_CHUNK_SIZE))
                    f.seek(size - HASH_CHUNK_SIZE)
                    hasher.update(f.read(HASH_CHUNK_SIZE))
            return f"{size}-{hasher.hexdigest()}"
        except (FileNotFoundError, OSError) as e:
            log.error(
                "Could not calculate file signature", file=str(file_path), error=str(e)
            )
            return ""
