# Chat History Search System – Design & Implementation

## SOLUTION DESIGN

### Current State

You are using a FAISS-based `/chs` semantic search over chat history with the following characteristics:
- The FAISS index is a static snapshot stored at a fixed path (for example, `P:/__csf/data/chat_history_faiss_with_text/`).
- The index is stale (e.g., last updated in early 2025) and does not include recent or current session messages.
- `/recent` uses a simple reverse-`grep` over chat log files (JSONL), providing keyword-based search that *does* see current messages but cannot handle semantic or fuzzy queries.
- There is an existing semantic daemon (CHS/CKS) capable of generating embeddings and possibly serving FAISS queries, but it is not tightly integrated with the chat log lifecycle.
- There is no session-aware or topic-aware routing; all semantic search goes through a single vector index without understanding sessions, topics, or project boundaries.

Pain points:
- Recent conversations, including the current day, are invisible to `/chs`.
- Search quality is degraded by the stale index and lack of structure in the retrieval unit (messages vs conversational turns).
- There is no clear operational model for keeping the semantic index current and healthy across many terminals and projects.

### Target State

The target system is a **Chat History Search System** with the following properties:
- All chat history, across all projects and terminals, is indexed from authoritative JSONL logs.
- Semantic search sees **current session messages** and **historical conversations** with minimal lag.
- Search is **chat-aware**: it operates on conversational turns and sessions, not just isolated messages.
- A **session–topic graph** allows topic-scoped and multi-session queries (e.g., "all sessions where we worked on FAISS indexing").
- The system is resilient, versioned, and maintainable:
  - Embedding compatibility is enforced.
  - Checkpoints survive log rotation.
  - Turn building is incremental and idempotent.
- Multi-terminal, multi-project workflows on Windows are fully supported via a single shared database.

### Architecture Overview

High-level components:

```text
+----------------------------+
|      CLI / UI Layer       |
|  (/chs, /recent, tools)   |
+-------------+--------------+
              |
              v
+----------------------------+
|     Query Orchestrator    |
|  - intent detection       |
|  - hybrid retrieval       |
|  - score fusion           |
+------+------+-------------+
       |      |
       |      v
       |  +--------------------------+
       |  |  Session–Topic Graph     |
       |  |  (sessions, topics,     |
       |  |   weights)              |
       |  +--------------------------+
       v
+----------------------------+
|    Semantic Store (DB)    |
|  - projects, sessions     |
|  - messages, turns        |
|  - FTS (turns, messages)  |
|  - embeddings (turns,     |
|    sessions, topics)      |
+-------------^--------------+
              |
              v
+----------------------------+
|  Indexing & Ingestion      |
|  - discovers chat logs     |
|  - parses JSONL           |
|  - builds turns & topics  |
|  - embeds via daemon      |
|  - maintains checkpoints  |
+----------------------------+
```

### Key Changes

1. **Move from static FAISS snapshot to a durable DB-backed semantic store**  
   - Why: A single FAISS snapshot cannot keep up with continuous chat logs and lacks rich metadata. A DB (SQLite) with FTS and embeddings provides persistence, structure, and operational visibility.

2. **Introduce chat-aware structures (sessions, turns, topics)**  
   - Why: Search over conversational turns and sessions yields more natural, contextful results than raw messages. Topics enable cross-session queries and better prefiltering.

3. **Add a robust indexing daemon with checkpoints**  
   - Why: Continuous, incremental ingestion from JSONL logs ensures the semantic index is always near-current. Checkpoints and file identity tracking make it robust to log rotation and restarts.

4. **Implement hybrid retrieval with explicit fusion logic**  
   - Why: Combining full-text (FTS/BM25) with embeddings yields better quality than either alone. Explicit, tunable fusion ensures predictable behavior and future tuning.

5. **Enforce embedding compatibility and versioning**  
   - Why: Changing embedding models or dimensions without tracking breaks similarity. Per-row embedding metadata plus a global configuration prevents silent corruption.

### Benefits & Metrics

- **Freshness**: New messages become searchable within seconds to a few minutes.
- **Recall**: Ability to find semantically related conversations, even when wording differs from the original queries.
- **Precision**: Session- and topic-aware filtering reduces noisy hits.
- **Robustness**: Index survives log rotation, embedding model changes, and partial failures.
- **Operability**: Clear health checks, status commands, and on-demand rebuilds.

Example metrics you can track:
- Indexing lag: time between last log message timestamp and last indexed timestamp.
- Average `/chs` query latency for small vs large corpora.
- Hit quality: percentage of user-evaluated queries where desired conversation appears in top N results.

### Trade-offs & Constraints

- **SQLite vs dedicated vector DB**: SQLite is simpler and sufficient for up to millions of turns, but very large corpora may eventually benefit from a dedicated ANN engine (FAISS/Qdrant). The design leaves room to swap the vector backend later.
- **Denormalized `project_id`** on messages/turns: This slightly increases write complexity but greatly improves read performance by avoiding joins on the hottest query path.
- **Idle-based session closure**: Time-based closure is a heuristic and may not perfectly match UI semantics, but it avoids dependence on proprietary session events.

---

## IMPLEMENTATION

### Files Required

```text
chat-history-search/
├── schema.sql
├── src/
│   ├── config.py
│   ├── db.py
│   ├── embeddings.py
│   ├── indexer.py
│   ├── topics.py
│   ├── search.py
│   ├── cli_chs.py
│   └── utils.py
├── scripts/
│   ├── init_db.ps1
│   ├── run_indexer.ps1
│   ├── chs.ps1
│   └── health_check.ps1
├── requirements.txt
└── README.md
```

### `requirements.txt`

```text
numpy
```

### `schema.sql`

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    label TEXT
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    session_key TEXT NOT NULL UNIQUE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    is_closed INTEGER NOT NULL DEFAULT 0,
    message_count INTEGER NOT NULL DEFAULT 0,
    summary_short TEXT,
    summary_long TEXT,
    embedding BLOB,
    embedding_model TEXT,
    embedding_dim INTEGER,
    last_turn_built_message_id INTEGER,
    last_message_timestamp INTEGER,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_project_time 
ON sessions(project_id, started_at DESC);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    timestamp INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    has_code INTEGER NOT NULL DEFAULT 0,
    has_error INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_session_time 
ON messages(session_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_messages_project_time 
ON messages(project_id, timestamp);

-- Turn-level chunks
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    start_message_id INTEGER NOT NULL REFERENCES messages(id),
    end_message_id INTEGER NOT NULL REFERENCES messages(id),
    timestamp_start INTEGER NOT NULL,
    timestamp_end INTEGER NOT NULL,
    content TEXT NOT NULL,
    has_code INTEGER NOT NULL DEFAULT 0,
    has_error INTEGER NOT NULL DEFAULT 0,
    length_tokens INTEGER,
    embedding BLOB,
    embedding_model TEXT,
    embedding_dim INTEGER,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    UNIQUE(session_id, start_message_id, end_message_id)
);

CREATE INDEX IF NOT EXISTS idx_turns_session_time 
ON turns(session_id, timestamp_start);

CREATE INDEX IF NOT EXISTS idx_turns_project_time 
ON turns(project_id, timestamp_start DESC);

-- FTS over turns
CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts 
USING fts5(
    content,
    content='turns',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS turns_ai AFTER INSERT ON turns BEGIN
    INSERT INTO turns_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS turns_ad AFTER DELETE ON turns BEGIN
    INSERT INTO turns_fts(turns_fts, rowid, content)
    VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS turns_au AFTER UPDATE ON turns BEGIN
    INSERT INTO turns_fts(turns_fts, rowid, content)
    VALUES('delete', old.id, old.content);
    INSERT INTO turns_fts(rowid, content)
    VALUES(new.id, new.content);
END;

-- FTS over messages
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
USING fts5(
    content,
    content='messages',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
    VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
    VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content)
    VALUES(new.id, new.content);
END;

-- Topics
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT,
    description TEXT,
    embedding BLOB,
    embedding_model TEXT,
    embedding_dim INTEGER
);

CREATE TABLE IF NOT EXISTS session_topics (
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    weight REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY(session_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_session_topics_topic 
ON session_topics(topic_id, weight DESC);

-- Checkpoints
CREATE TABLE IF NOT EXISTS indexer_checkpoints (
    source_path TEXT PRIMARY KEY,
    last_offset INTEGER NOT NULL,
    file_size INTEGER NOT NULL,
    mtime INTEGER NOT NULL,
    content_hash_prefix TEXT,
    last_message_timestamp INTEGER,
    last_indexed_at INTEGER NOT NULL
);

-- Embeddings config
CREATE TABLE IF NOT EXISTS embeddings_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    model_name TEXT NOT NULL,
    dim INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

### `src/config.py`

```python
import os
from pathlib import Path


class Config:
    DB_PATH: Path = Path(os.environ.get("CHS_DB_PATH", r"P:/__csf/data/chat_history.db"))
    CHAT_LOG_ROOT: Path = Path(os.environ.get("CHS_CHAT_LOG_ROOT", r"P:/__csf/chat_logs"))

    EMBEDDING_MODEL_NAME: str = os.environ.get("CHS_EMBED_MODEL", "local-embed-model")
    EMBEDDING_DIM: int = int(os.environ.get("CHS_EMBED_DIM", "768"))

    SESSION_IDLE_SECONDS: int = int(os.environ.get("CHS_SESSION_IDLE", str(30 * 60)))
    INDEXER_IDLE_SECONDS: int = int(os.environ.get("CHS_INDEXER_IDLE", str(15 * 60)))
    SEMANTIC_CANDIDATE_LIMIT: int = int(os.environ.get("CHS_SEM_LIMIT", "5000"))

    LOG_LEVEL: str = os.environ.get("CHS_LOG_LEVEL", "INFO")
```

### `src/db.py`

```python
import sqlite3
from pathlib import Path
from typing import Tuple
from .config import Config


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(Config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(schema_path: Path) -> None:
    conn = get_connection()
    try:
        with schema_path.open("r", encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def load_embeddings_config(conn: sqlite3.Connection) -> Tuple[str, int]:
    row = conn.execute("SELECT model_name, dim FROM embeddings_config WHERE id = 1").fetchone()
    if not row:
        raise RuntimeError("embeddings_config not initialized")
    return row["model_name"], row["dim"]


def set_embeddings_config(conn: sqlite3.Connection, model_name: str, dim: int) -> None:
    conn.execute(
        """
        INSERT INTO embeddings_config(id, model_name, dim, updated_at)
        VALUES(1, ?, ?, strftime('%s','now'))
        ON CONFLICT(id) DO UPDATE SET
            model_name = excluded.model_name,
            dim = excluded.dim,
            updated_at = excluded.updated_at
        """,
        (model_name, dim),
    )
    conn.commit()
```

### `src/embeddings.py`

```python
import numpy as np
from typing import List
from .config import Config


class EmbedClient:
    """Placeholder embedding client.

    Replace embed_texts implementation with calls to your semantic daemon.
    """

    def __init__(self, model_name: str, dim: int) -> None:
        self.model_name = model_name
        self.dim = dim

    def embed_texts(self, texts: List[str]) -> List[bytes]:
        out: List[bytes] = []
        for t in texts:
            seed = abs(hash(t)) % (2**32)
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(self.dim, dtype=np.float32)
            out.append(vec.tobytes())
        return out


def validate_embedding_blob(emb: bytes, dim: int) -> None:
    expected = dim * 4
    actual = len(emb)
    if actual != expected:
        raise ValueError(f"Embedding bytes mismatch: expected {expected}, got {actual}")


def bytes_to_vector(emb: bytes, dim: int) -> np.ndarray:
    validate_embedding_blob(emb, dim)
    return np.frombuffer(emb, dtype=np.float32, count=dim)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    if denom == 0.0:
        return 0.0
    return float(a @ b / denom)


def get_embed_client() -> EmbedClient:
    return EmbedClient(Config.EMBEDDING_MODEL_NAME, Config.EMBEDDING_DIM)
```

### `src/utils.py`

```python
import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Tuple


def file_identity(path: Path) -> Tuple[int, int, str]:
    st = path.stat()
    size = st.st_size
    mtime = int(st.st_mtime)
    with path.open("rb") as f:
        if size <= 64 * 1024:
            data = f.read()
            h = hashlib.sha256(data).hexdigest()
        else:
            head = f.read(1024)
            f.seek(max(0, size - 1024))
            tail = f.read(1024)
            h = hashlib.sha256(head + tail).hexdigest()
    return size, mtime, h


def parse_jsonl_line(line: bytes) -> Dict[str, Any]:
    return json.loads(line.decode("utf-8"))


def detect_chat_logs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    logs: list[Path] = []
    for p in root.rglob("*.jsonl"):
        if p.is_file():
            logs.append(p)
    return logs


def detect_current_project_root() -> Path:
    return Path(os.getcwd()).resolve()


def adaptive_lambda(query: str) -> float:
    if '"' in query:
        return 0.7
    if len(query.split()) <= 2:
        return 0.3
    return 0.4
```

### `src/indexer.py`

```python
import time
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from .config import Config
from .db import get_connection, load_embeddings_config, set_embeddings_config
from .embeddings import get_embed_client, validate_embedding_blob
from .utils import file_identity, parse_jsonl_line, detect_chat_logs


class ChatIndexer:
    def __init__(self) -> None:
        self.idle_timeout = Config.INDEXER_IDLE_SECONDS

    def daemon_loop(self) -> None:
        last_activity = time.time()
        while True:
            did_work = self.index_once()
            if did_work:
                last_activity = time.time()
            else:
                if time.time() - last_activity > self.idle_timeout:
                    break
                time.sleep(5)

    def index_once(self) -> bool:
        conn = get_connection()
        try:
            logs = detect_chat_logs(Config.CHAT_LOG_ROOT)
            did_work = False
            for path in logs:
                conn.execute("BEGIN")
                try:
                    updated = self._index_file(conn, path)
                    conn.execute("COMMIT")
                    did_work = did_work or updated
                except Exception:
                    conn.execute("ROLLBACK")
            return did_work
        finally:
            conn.close()

    def _load_checkpoint(self, conn: sqlite3.Connection, path: Path) -> Dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT last_offset, file_size, mtime, content_hash_prefix
            FROM indexer_checkpoints
            WHERE source_path = ?
            """,
            (str(path),),
        ).fetchone()
        return dict(row) if row else None

    def _update_checkpoint(self, conn: sqlite3.Connection, path: Path, offset: int, size: int, mtime: int, hash_prefix: str, last_ts: int) -> None:
        conn.execute(
            """
            INSERT INTO indexer_checkpoints(
                source_path, last_offset, file_size, mtime,
                content_hash_prefix, last_message_timestamp, last_indexed_at
            ) VALUES (?, ?, ?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(source_path) DO UPDATE SET
                last_offset = excluded.last_offset,
                file_size = excluded.file_size,
                mtime = excluded.mtime,
                content_hash_prefix = excluded.content_hash_prefix,
                last_message_timestamp = excluded.last_message_timestamp,
                last_indexed_at = excluded.last_indexed_at
            """,
            (str(path), offset, size, mtime, hash_prefix, last_ts),
        )

    def _index_file(self, conn: sqlite3.Connection, path: Path) -> bool:
        size, mtime, h = file_identity(path)
        cp = self._load_checkpoint(conn, path)
        if cp:
            if size < cp["file_size"] or mtime != cp["mtime"] or h != cp["content_hash_prefix"]:
                last_offset = 0
            else:
                last_offset = cp["last_offset"]
        else:
            last_offset = 0

        with path.open("rb") as f:
            f.seek(last_offset)
            new_bytes = f.read()
        if not new_bytes:
            return False

        lines = new_bytes.splitlines()
        if not lines:
            return False

        last_ts = 0
        for line in lines:
            obj = parse_jsonl_line(line)
            ts = self._ingest_message(conn, path, obj)
            if ts and ts > last_ts:
                last_ts = ts

        new_offset = last_offset + len(new_bytes)
        self._update_checkpoint(conn, path, new_offset, size, mtime, h, last_ts)

        self._build_turns_and_embeddings(conn)
        self._close_idle_sessions(conn)

        return True

    def _get_or_create_project(self, conn: sqlite3.Connection, path: Path) -> int:
        proj_path = str(Config.CHAT_LOG_ROOT)
        row = conn.execute("SELECT id FROM projects WHERE path = ?", (proj_path,)).fetchone()
        if row:
            return row[0]
        cur = conn.execute("INSERT INTO projects(path, label) VALUES(?, ?)", (proj_path, "default"))
        return cur.lastrowid

    def _get_or_create_session(self, conn: sqlite3.Connection, project_id: int, obj: Dict[str, Any]) -> int:
        session_key = str(obj.get("session_id", "default-session"))
        row = conn.execute("SELECT id FROM sessions WHERE session_key = ?", (session_key,)).fetchone()
        ts = int(obj.get("timestamp", int(time.time())))
        if row:
            conn.execute(
                """
                UPDATE sessions
                SET message_count = message_count + 1,
                    last_message_timestamp = ?,
                    updated_at = strftime('%s','now')
                WHERE id = ?
                """,
                (ts, row[0]),
            )
            return row[0]
        cur = conn.execute(
            """
            INSERT INTO sessions(
                session_key, project_id, started_at, ended_at,
                is_closed, message_count, last_message_timestamp
            ) VALUES(?, ?, ?, NULL, 0, 1, ?)
            """,
            (session_key, project_id, ts, ts),
        )
        return cur.lastrowid

    def _ingest_message(self, conn: sqlite3.Connection, path: Path, obj: Dict[str, Any]) -> int:
        project_id = self._get_or_create_project(conn, path)
        session_id = self._get_or_create_session(conn, project_id, obj)

        message_id = str(obj.get("id") or obj.get("message_id") or obj.get("uuid"))
        ts = int(obj.get("timestamp", int(time.time())))
        role = str(obj.get("role", "user"))
        content = str(obj.get("content", ""))
        has_code = 1 if "```" in content else 0
        has_error = 1 if "Exception" in content or "Traceback" in content or "Error" in content else 0

        conn.execute(
            """
            INSERT OR IGNORE INTO messages(
                message_id, session_id, project_id,
                timestamp, role, content, has_code, has_error, raw_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, session_id, project_id, ts, role, content, has_code, has_error, str(obj)),
        )

        conn.execute(
            """
            UPDATE sessions
            SET last_message_timestamp = ?,
                ended_at = CASE WHEN ended_at IS NULL OR ended_at < ? THEN ? ELSE ended_at END,
                updated_at = strftime('%s','now')
            WHERE id = ?
            """,
            (ts, ts, ts, session_id),
        )

        return ts

    def _build_turns_and_embeddings(self, conn: sqlite3.Connection) -> None:
        set_embeddings_config(conn, Config.EMBEDDING_MODEL_NAME, Config.EMBEDDING_DIM)
        model_name, dim = load_embeddings_config(conn)
        embed_client = get_embed_client()

        sessions = conn.execute("SELECT id FROM sessions").fetchall()
        for s in sessions:
            self._build_new_turns_for_session(conn, s[0])

        rows = conn.execute("SELECT id, content FROM turns WHERE embedding IS NULL LIMIT 128").fetchall()
        if not rows:
            return
        ids = [r["id"] for r in rows]
        texts = [r["content"] for r in rows]
        blobs = embed_client.embed_texts(texts)
        for turn_id, emb in zip(ids, blobs):
            validate_embedding_blob(emb, dim)
            conn.execute(
                """
                UPDATE turns
                SET embedding = ?, embedding_model = ?, embedding_dim = ?
                WHERE id = ?
                """,
                (emb, model_name, dim, turn_id),
            )

    def _build_new_turns_for_session(self, conn: sqlite3.Connection, session_id: int) -> None:
        row = conn.execute(
            "SELECT last_turn_built_message_id, is_closed FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return
        last_msg_id = row["last_turn_built_message_id"] or 0
        is_closed = bool(row["is_closed"])

        cur = conn.execute(
            """
            SELECT * FROM messages
            WHERE session_id = ? AND id > ?
            ORDER BY timestamp, id
            """,
            (session_id, last_msg_id),
        )
        rows = list(cur)
        if not rows:
            return

        turns: List[List[sqlite3.Row]] = []
        current: List[sqlite3.Row] = []

        for msg in rows:
            if msg["role"] == "user" and current:
                turns.append(current)
                current = [msg]
            else:
                current.append(msg)

        if current and is_closed:
            turns.append(current)

        for t in turns:
            start_msg = t[0]
            end_msg = t[-1]
            parts = [f"[{m['role']}] {m['content']}" for m in t]
            content = "
".join(parts)
            has_code = any(m["has_code"] for m in t)
            has_error = any(m["has_error"] for m in t)

            conn.execute(
                """
                INSERT OR IGNORE INTO turns(
                    session_id, project_id,
                    start_message_id, end_message_id,
                    timestamp_start, timestamp_end,
                    content, has_code, has_error
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    start_msg["project_id"],
                    start_msg["id"],
                    end_msg["id"],
                    start_msg["timestamp"],
                    end_msg["timestamp"],
                    content,
                    int(has_code),
                    int(has_error),
                ),
            )

        max_msg_id = max(m["id"] for m in rows)
        conn.execute(
            "UPDATE sessions SET last_turn_built_message_id = ?, updated_at = strftime('%s','now') WHERE id = ?",
            (max_msg_id, session_id),
        )

    def _close_idle_sessions(self, conn: sqlite3.Connection) -> None:
        now = int(time.time())
        idle_cutoff = now - Config.SESSION_IDLE_SECONDS
        conn.execute(
            """
            UPDATE sessions
            SET is_closed = 1,
                updated_at = strftime('%s','now')
            WHERE is_closed = 0
              AND last_message_timestamp IS NOT NULL
              AND last_message_timestamp < ?
            """,
            (idle_cutoff,),
        )
        conn.commit()
```

### `src/topics.py`

```python
import re
import sqlite3
from typing import Dict

TOPIC_PATTERNS = {
    "faiss": r"faiss",
    "ask-olymp": r"/ask-olymp",
    "windows-paths": r"[A-Z]:\",
    "git": r"git",
}


def extract_topics_for_text(text: str) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for name, pat in TOPIC_PATTERNS.items():
        matches = re.findall(pat, text, flags=re.IGNORECASE)
        if matches:
            freq = len(matches)
            weight = 1.0 + (freq - 1) * 0.25
            weights[name] = weight
    return weights


def update_session_topics(conn: sqlite3.Connection, session_id: int) -> None:
    cur = conn.execute("SELECT content FROM turns WHERE session_id = ?", (session_id,))
    chunks = [r["content"] for r in cur]
    if not chunks:
        return
    text = "
".join(chunks)
    topics = extract_topics_for_text(text)
    if not topics:
        return

    for name, w in topics.items():
        conn.execute("INSERT INTO topics(name) VALUES(?) ON CONFLICT(name) DO NOTHING", (name,))
        topic_id = conn.execute("SELECT id FROM topics WHERE name = ?", (name,)).fetchone()[0]
        conn.execute(
            """
            INSERT INTO session_topics(session_id, topic_id, weight, source)
            VALUES(?, ?, ?, 'heuristic')
            ON CONFLICT(session_id, topic_id) DO UPDATE SET weight = excluded.weight
            """,
            (session_id, topic_id, w),
        )
    conn.commit()
```

### `src/search.py`

```python
import sqlite3
from typing import Dict, List, Tuple
import numpy as np

from .config import Config
from .db import get_connection, load_embeddings_config
from .embeddings import bytes_to_vector, cosine_similarity, get_embed_client
from .utils import adaptive_lambda


def min_max_norm(scores: Dict[int, float]) -> Dict[int, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {k: 1.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def search_fts_turns(conn: sqlite3.Connection, query: str, project_id: int | None, limit: int = 200) -> Dict[int, float]:
    if project_id is None:
        cur = conn.execute(
            """
            SELECT t.id, bm25(turns_fts) AS score
            FROM turns_fts
            JOIN turns t ON t.id = turns_fts.rowid
            WHERE turns_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        )
    else:
        cur = conn.execute(
            """
            SELECT t.id, bm25(turns_fts) AS score
            FROM turns_fts
            JOIN turns t ON t.id = turns_fts.rowid
            WHERE turns_fts MATCH ? AND t.project_id = ?
            ORDER BY score
            LIMIT ?
            """,
            (query, project_id, limit),
        )
    res: Dict[int, float] = {}
    for row in cur:
        res[row["id"]] = -float(row["score"])
    return res


def search_fts_messages(conn: sqlite3.Connection, query: str, project_id: int | None, limit: int = 200) -> List[int]:
    if project_id is None:
        cur = conn.execute(
            """
            SELECT m.id
            FROM messages_fts
            JOIN messages m ON m.id = messages_fts.rowid
            WHERE messages_fts MATCH ?
            LIMIT ?
            """,
            (query, limit),
        )
    else:
        cur = conn.execute(
            """
            SELECT m.id
            FROM messages_fts
            JOIN messages m ON m.id = messages_fts.rowid
            WHERE messages_fts MATCH ? AND m.project_id = ?
            LIMIT ?
            """,
            (query, project_id, limit),
        )
    return [r["id"] for r in cur]


def semantic_search_turns(conn: sqlite3.Connection, query_vec: np.ndarray, model_name: str, dim: int, project_id: int | None, limit: int) -> Dict[int, float]:
    if project_id is None:
        cur = conn.execute(
            "SELECT id, embedding, embedding_model, embedding_dim FROM turns WHERE embedding IS NOT NULL LIMIT ?",
            (limit,),
        )
    else:
        cur = conn.execute(
            """
            SELECT id, embedding, embedding_model, embedding_dim
            FROM turns
            WHERE embedding IS NOT NULL AND project_id = ?
            LIMIT ?
            """,
            (project_id, limit),
        )

    scores: Dict[int, float] = {}
    for row in cur:
        if row["embedding_model"] != model_name or row["embedding_dim"] != dim:
            continue
        vec = bytes_to_vector(row["embedding"], dim)
        score = cosine_similarity(query_vec, vec)
        scores[row["id"]] = score
    return scores


def fuse_scores(query: str, bm25_raw: Dict[int, float], cos_raw: Dict[int, float]) -> List[Tuple[int, float]]:
    lam = adaptive_lambda(query)
    bm25 = min_max_norm(bm25_raw)
    cos = min_max_norm(cos_raw)
    scores: Dict[int, float] = {}
    ids = set(bm25.keys()) | set(cos.keys())
    for i in ids:
        s_k = bm25.get(i, 0.0)
        s_v = cos.get(i, 0.0)
        scores[i] = lam * s_k + (1.0 - lam) * s_v
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def search_turns(query: str, project_id: int | None = None, limit: int = 20) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        model_name, dim = load_embeddings_config(conn)
        embed_client = get_embed_client()
        q_vec_bytes = embed_client.embed_texts([query])[0]
        q_vec = bytes_to_vector(q_vec_bytes, dim)

        bm25_raw = search_fts_turns(conn, query, project_id, limit=200)
        cos_raw = semantic_search_turns(
            conn,
            q_vec,
            model_name,
            dim,
            project_id,
            limit=Config.SEMANTIC_CANDIDATE_LIMIT,
        )
        fused = fuse_scores(query, bm25_raw, cos_raw)
        if not fused and not bm25_raw:
            msg_ids = search_fts_messages(conn, query, project_id, limit=200)
            if not msg_ids:
                return []
            placeholders = ",".join("?" for _ in msg_ids)
            cur = conn.execute(
                f"""
                SELECT DISTINCT t.*
                FROM turns t
                JOIN messages m ON m.session_id = t.session_id
                WHERE m.id IN ({placeholders})
                ORDER BY t.timestamp_start DESC
                LIMIT ?
                """,
                (*msg_ids, limit),
            )
            return cur.fetchall()

        turn_ids = [tid for tid, _ in fused[:limit]]
        if not turn_ids:
            return []
        placeholders = ",".join("?" for _ in turn_ids)
        cur = conn.execute(
            f"SELECT * FROM turns WHERE id IN ({placeholders})",
            tuple(turn_ids),
        )
        rows = cur.fetchall()
        order_map = {tid: i for i, tid in enumerate(turn_ids)}
        rows.sort(key=lambda r: order_map.get(r["id"], 1e9))
        return rows
    finally:
        conn.close()
```

### `src/cli_chs.py`

```python
import argparse
from .config import Config
from .search import search_turns
from .utils import detect_current_project_root
from .db import get_connection


def get_project_id_for_path(path) -> int | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM projects WHERE path = ?", (str(Config.CHAT_LOG_ROOT),)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat history semantic search (/chs)")
    parser.add_argument("query", nargs="+", help="search query")
    parser.add_argument("--global", dest="global_scope", action="store_true", help="search all projects")
    parser.add_argument("--limit", type=int, default=20, help="max results")
    args = parser.parse_args()

    query = " ".join(args.query)

    if args.global_scope:
        project_id = None
    else:
        project_id = get_project_id_for_path(detect_current_project_root())

    rows = search_turns(query, project_id=project_id, limit=args.limit)
    if not rows:
        print("No results.")
        return

    for i, row in enumerate(rows, start=1):
        print(f"=== Result {i} ===")
        print(f"Session ID: {row['session_id']}  Turn ID: {row['id']}")
        print(f"Time: {row['timestamp_start']} - {row['timestamp_end']}")
        print("Content:")
        print(row["content"])
        print()


if __name__ == "__main__":
    main()
```

### `scripts/init_db.ps1`

```powershell
param(
    [string]$DbPath = "P:/__csf/data/chat_history.db",
    [string]$SchemaPath = "schema.sql"
)

$ErrorActionPreference = "Stop"

$schemaFull = Resolve-Path $SchemaPath

Write-Host "Initializing DB at $DbPath using schema $schemaFull" -ForegroundColor Cyan

$dir = Split-Path $DbPath
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
}

python - <<PY
from pathlib import Path
from src.db import init_db

init_db(Path(r"$schemaFull"))
PY

Write-Host "DB initialized." -ForegroundColor Green
```

### `scripts/run_indexer.ps1`

```powershell
$ErrorActionPreference = "Stop"

Write-Host "Starting Chat Indexer daemon..." -ForegroundColor Cyan

python - <<PY
from src.indexer import ChatIndexer

ChatIndexer().daemon_loop()
PY

Write-Host "Indexer exited (idle timeout or completion)." -ForegroundColor Yellow
```

### `scripts/chs.ps1`

```powershell
param(
    [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Query,
    [switch]$Global,
    [int]$Limit = 20
)

$ErrorActionPreference = "Stop"

$joined = $Query -join ' '

if ($Global) {
    python -m src.cli_chs --global --limit $Limit --% $joined
} else {
    python -m src.cli_chs --limit $Limit --% $joined
}
```

### `scripts/health_check.ps1`

```powershell
$ErrorActionPreference = "Stop"

Write-Host "Chat History Search Health Check" -ForegroundColor Cyan

python - <<PY
from src.db import get_connection

conn = get_connection()
try:
    cur = conn.execute("SELECT COUNT(*) AS c FROM sessions")
    sessions = cur.fetchone()["c"]
    cur = conn.execute("SELECT COUNT(*) AS c FROM messages")
    messages = cur.fetchone()["c"]
    cur = conn.execute("SELECT COUNT(*) AS c FROM turns")
    turns = cur.fetchone()["c"]
    print(f"Sessions: {sessions}")
    print(f"Messages: {messages}")
    print(f"Turns: {turns}")
finally:
    conn.close()
PY
```

### `README.md`

```markdown
# Chat History Search System

This project provides a chat-aware search system over your chat logs using SQLite, FTS5, and semantic embeddings.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:CHS_DB_PATH = "P:/__csf/data/chat_history.db"
$env:CHS_CHAT_LOG_ROOT = "P:/__csf/chat_logs"
$env:CHS_EMBED_MODEL = "local-embed-model"
$env:CHS_EMBED_DIM = "768"

pwsh scripts/init_db.ps1 -DbPath $env:CHS_DB_PATH -SchemaPath "schema.sql"
pwsh scripts/run_indexer.ps1
pwsh scripts/chs.ps1 "faiss incremental" -Limit 10
```

## Health Check

```powershell
pwsh scripts/health_check.ps1
```
```

## Steady-State Operation

- Run `scripts/run_indexer.ps1` periodically or as a background task.
- Use `scripts/chs.ps1` for day-to-day search.
- Use `scripts/health_check.ps1` for on-demand status.

