#!/usr/bin/env python3
"""
CKS Integration Module for Claude Code Bridge

This module provides simple interfaces to the CKS (Cognitive Knowledge System)
for the Claude Code bridge functionality.

Functions:
- query_cks: Search CKS for relevant past solutions
- store_to_cks: Store new solutions to CKS
- cks_stats: Get CKS system statistics
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# Database path for CKS
CKS_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cks.db"

def _ensure_cks_db():
    """Ensure CKS database exists and is properly initialized."""
    CKS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(CKS_DB_PATH))
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedding BLOB,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_question_text ON memories(question)
    """)

    conn.commit()
    conn.close()

def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using Jaccard similarity."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0

def query_cks(
    query: str,
    top_n: int = 5,
    threshold: float = 0.75,
    metadata_filter: dict | None = None
) -> list[dict[str, Any]]:
    """
    Query CKS for relevant past solutions.

    Args:
        query: Search query text
        top_n: Maximum number of results to return
        threshold: Similarity threshold (0.0-1.0)
        metadata_filter: Optional metadata filters

    Returns:
        List of matching memories with similarity scores
    """
    _ensure_cks_db()

    results = []

    try:
        conn = sqlite3.connect(str(CKS_DB_PATH))
        cursor = conn.cursor()

        # Get all memories
        cursor.execute("""
            SELECT id, question, answer, metadata, created_at
            FROM memories
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()

        for row in rows:
            memory_id, question, answer, metadata_str, created_at = row

            # Calculate similarity
            similarity = _calculate_similarity(query, question)

            if similarity >= threshold:
                # Parse metadata
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {}

                # Apply metadata filter if provided
                if metadata_filter:
                    match = True
                    for key, value in metadata_filter.items():
                        if metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue

                results.append({
                    'id': memory_id,
                    'question': question,
                    'answer': answer,
                    'similarity': similarity,
                    'metadata': metadata,
                    'created_at': created_at
                })

        # Sort by similarity and limit results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_n]

        conn.close()

    except Exception as e:
        print(f"[CKS] Query error: {e}")
        return []

    return results

def store_to_cks(
    question: str,
    answer: str,
    metadata: dict[str, Any] | None = None,
    overwrite: bool = False
) -> bool:
    """
    Store a new solution to CKS.

    Args:
        question: The problem/task description
        answer: The solution/code
        metadata: Additional metadata (source, session_id, etc.)
        overwrite: Whether to overwrite existing similar entries

    Returns:
        True if successfully stored, False otherwise
    """
    _ensure_cks_db()

    if metadata is None:
        metadata = {}

    # Add timestamp to metadata
    metadata['stored_at'] = datetime.utcnow().isoformat()

    try:
        conn = sqlite3.connect(str(CKS_DB_PATH))
        cursor = conn.cursor()

        # Check for similar existing entries if overwrite is False
        if not overwrite:
            cursor.execute("SELECT question FROM memories")
            existing_questions = [row[0] for row in cursor.fetchall()]

            for existing_q in existing_questions:
                similarity = _calculate_similarity(question, existing_q)
                if similarity > 0.9:  # Very similar, don't duplicate
                    conn.close()
                    return False

        # Insert new memory
        cursor.execute("""
            INSERT INTO memories (question, answer, metadata)
            VALUES (?, ?, ?)
        """, (question, answer, json.dumps(metadata, indent=2)))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"[CKS] Store error: {e}")
        return False

def cks_stats() -> dict[str, Any]:
    """
    Get CKS system statistics.

    Returns:
        Dictionary with system statistics
    """
    _ensure_cks_db()

    try:
        conn = sqlite3.connect(str(CKS_DB_PATH))
        cursor = conn.cursor()

        # Get total memories count
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]

        # Get database size
        db_size_bytes = CKS_DB_PATH.stat().st_size if CKS_DB_PATH.exists() else 0
        db_size_mb = db_size_bytes / (1024 * 1024)

        # Get date range
        cursor.execute("""
            SELECT MIN(created_at), MAX(created_at)
            FROM memories
        """)
        date_range = cursor.fetchone()

        # Get source statistics
        cursor.execute("""
            SELECT json_extract(metadata, '$.source') as source, COUNT(*)
            FROM memories
            WHERE json_extract(metadata, '$.source') IS NOT NULL
            GROUP BY source
        """)
        source_stats = dict(cursor.fetchall())

        conn.close()

        return {
            'total_memories': total_memories,
            'db_size_mb': round(db_size_mb, 2),
            'threshold': 0.75,  # Default threshold
            'embedding_model': 'simple_jaccard',  # We're using simple similarity
            'date_range': {
                'earliest': date_range[0],
                'latest': date_range[1]
            },
            'source_breakdown': source_stats,
            'db_path': str(CKS_DB_PATH)
        }

    except Exception as e:
        print(f"[CKS] Stats error: {e}")
        return {
            'total_memories': 0,
            'db_size_mb': 0,
            'threshold': 0.75,
            'embedding_model': 'simple_jaccard',
            'error': str(e)
        }

# Initialize database on import
_ensure_cks_db()

if __name__ == "__main__":
    # Demo usage
    print("=== CKS Integration Demo ===")

    # Store a sample solution
    sample_question = "Build a secure password reset flow with email verification"
    sample_answer = """
    async function initiatePasswordReset(email: string) {
      // Rate limiting check
      const recent = await getRecentAttempts(email, '5m');
      if (recent >= 3) throw new Error('Too many attempts');

      // Generate secure token
      const token = crypto.randomBytes(32).toString('hex');
      const hash = await hashToken(token);

      // Store with 15-min expiry
      await store.resetTokens.create({
        hash,
        email,
        expiresAt: new Date(Date.now() + 15 * 60000)
      });

      // Send email
      await sendResetEmail(email, token);
      return { success: true };
    }
    """

    print("\nStoring sample solution...")
    stored = store_to_cks(
        sample_question,
        sample_answer,
        metadata={
            "source": "claude_code_demo",
            "language": "javascript",
            "success": True
        }
    )
    print(f"Stored: {stored}")

    # Query the solution
    print("\nQuerying for similar solutions...")
    results = query_cks("password reset with email", top_n=3, threshold=0.5)

    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (similarity: {result['similarity']:.2f}):")
        print(f"Question: {result['question'][:80]}...")
        print(f"Answer preview: {result['answer'][:100]}...")

    # Show stats
    print("\nCKS Statistics:")
    stats = cks_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
