#!/usr/bin/env python3
"""Create sample chat data for testing the SQLite database.
"""

import sys
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB


def create_sample_sessions():
    """Create sample chat sessions for testing."""
    db = ChatHistoryDB()

    # Sample session 1: GPU optimization discussion
    session1 = {
        "session_id": "gpu_opt_session_001",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "GPU memory optimization",
            "project": "CSF NIP",
            "original_format": "sample_data"
        },
        "messages": [
            {
                "role": "user",
                "content": "optimize GPU memory usage further",
                "timestamp": "2025-12-19T19:00:00Z",
                "token_count": 8,
                "metadata": {"type": "user_request"}
            },
            {
                "role": "assistant",
                "content": "I'll create an advanced GPU memory optimization system with dynamic batch sizing and real-time monitoring.",
                "timestamp": "2025-12-19T19:00:05Z",
                "token_count": 15,
                "metadata": {"type": "response", "confidence": "high"}
            },
            {
                "role": "assistant",
                "content": "I've created optimized_gpu_analyzer.py with GPUMemoryManager class that achieves 99.2% memory efficiency.",
                "timestamp": "2025-12-19T19:00:30Z",
                "token_count": 18,
                "metadata": {"type": "result", "file_created": "optimized_gpu_analyzer.py"}
            },
            {
                "role": "user",
                "content": "did you build something with real-time monitoring dashboards?",
                "timestamp": "2025-12-19T19:01:00Z",
                "token_count": 9,
                "metadata": {"type": "question"}
            },
            {
                "role": "assistant",
                "content": "Yes, I implemented monitoring infrastructure with real-time memory tracking and performance metrics.",
                "timestamp": "2025-12-19T19:01:05Z",
                "token_count": 12,
                "metadata": {"type": "confirmation"}
            }
        ]
    }

    # Sample session 2: TaskMaster integration
    session2 = {
        "session_id": "taskmaster_session_002",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "TaskMaster integration",
            "project": "CSF NIP",
            "original_format": "sample_data"
        },
        "messages": [
            {
                "role": "user",
                "content": "shouldn't rag and vector graph everything be used by default?",
                "timestamp": "2025-12-19T19:30:00Z",
                "token_count": 10,
                "metadata": {"type": "question"}
            },
            {
                "role": "assistant",
                "content": "You're absolutely right. RAG and vector search should be enabled by default for optimal search performance.",
                "timestamp": "2025-12-19T19:30:05Z",
                "token_count": 14,
                "metadata": {"type": "agreement", "action": "enable_rag_by_default"}
            },
            {
                "role": "assistant",
                "content": "I've updated the chat search system to use RAG and vector search by default instead of keyword search fallback.",
                "timestamp": "2025-12-19T19:30:20Z",
                "token_count": 16,
                "metadata": {"type": "implementation", "success": True}
            }
        ]
    }

    # Sample session 3: Database storage discussion
    session3 = {
        "session_id": "database_session_003",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "SQLite database storage",
            "project": "CSF NIP",
            "original_format": "sample_data"
        },
        "messages": [
            {
                "role": "user",
                "content": "why isn't it being stored in sqlite?",
                "timestamp": "2025-12-19T20:00:00Z",
                "token_count": 7,
                "metadata": {"type": "question"}
            },
            {
                "role": "assistant",
                "content": "Chat history is currently stored in compressed session files rather than SQLite. I found TaskMaster has SQLite infrastructure but chat sessions aren't using it.",
                "timestamp": "2025-12-19T20:00:05Z",
                "token_count": 20,
                "metadata": {"type": "analysis", "finding": "session_files_not_sqlite"}
            },
            {
                "role": "user",
                "content": "Is using the taskmaster sqlite database the optimal choice?",
                "timestamp": "2025-12-19T20:00:30Z",
                "token_count": 9,
                "metadata": {"type": "decision_question"}
            },
            {
                "role": "assistant",
                "content": "No, TaskMaster SQLite is not optimal for chat storage. I recommend creating a dedicated chat_history.db with proper schema for sessions and messages.",
                "timestamp": "2025-12-19T20:00:35Z",
                "token_count": 19,
                "metadata": {"type": "recommendation", "action": "create_dedicated_db"}
            }
        ]
    }

    # Store sample sessions
    sessions = [session1, session2, session3]

    for session in sessions:
        session_id = db.store_session(session)
        print(f"✅ Stored session: {session_id} with {len(session['messages'])} messages")

    # Test search functionality
    print("\n🔍 Testing search functionality:")

    # Test GPU-related search
    gpu_results = db.search_messages("GPU memory optimization", limit=3)
    print(f"GPU search results: {len(gpu_results)} found")
    for result in gpu_results:
        print(f"  - {result['timestamp']}: {result['content'][:60]}...")

    # Test RAG search
    rag_results = db.search_messages("vector search", limit=3)
    print(f"RAG search results: {len(rag_results)} found")
    for result in rag_results:
        print(f"  - {result['timestamp']}: {result['content'][:60]}...")

    # Show database statistics
    print("\n📊 Database Statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    create_sample_sessions()
