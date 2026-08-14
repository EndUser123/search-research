"""Topic extraction and management for CHS v2."""

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


def extract_topics(text: str, max_topics: int = 10) -> dict[str, float]:
    """
    Extract topics from text using regex patterns.

    Returns dict of {topic_name: weight} where weight is TF-based
    (1.0 base + log-scaled frequency bonus).

    Args:
        text: The text to extract topics from
        max_topics: Maximum number of topics to return (default: 10)

    Returns:
        Dictionary mapping topic names to weights
    """
    text_lower = text.lower()
    weights: dict[str, float] = {}
    for name, topic_info in TOPIC_PATTERNS.items():
        pattern = topic_info["pattern"]
        matches = re.findall(pattern, text_lower, flags=re.IGNORECASE)
        if matches:
            freq = len(matches)
            weight = min(1.0 + (freq - 1) * 0.25, 10.0)
            weights[name] = weight
    sorted_weights = dict(sorted(weights.items(), key=lambda x: x[1], reverse=True)[:max_topics])
    return sorted_weights


def update_session_topics(
    conn: sqlite3.Connection, session_id: int, topics: dict[str, float]
) -> None:
    """
    Update topics for a session.

    Inserts new topics and creates/updates session_topics mappings.

    Args:
        conn: SQLite database connection
        session_id: The session ID to update topics for
        topics: Dictionary of {topic_name: weight} to upsert
    """
    if not topics:
        return
    for topic_name, weight in topics.items():
        conn.execute(
            "INSERT INTO topics(name, pattern) VALUES(?, ?) ON CONFLICT(name) DO NOTHING",
            (topic_name, None),
        )
        cursor = conn.execute("SELECT id FROM topics WHERE name = ?", (topic_name,))
        result = cursor.fetchone()
        if result is None:
            continue
        topic_id = result[0]
        conn.execute(
            "\n            INSERT INTO session_topics(session_id, topic_id, weight)\n            VALUES(?, ?, ?)\n            ON CONFLICT(session_id, topic_id) DO UPDATE\n            SET weight = excluded.weight\n            ",
            (session_id, topic_id, weight),
        )
    conn.commit()
