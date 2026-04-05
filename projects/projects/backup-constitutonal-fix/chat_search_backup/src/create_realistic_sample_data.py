#!/usr/bin/env python3
"""Create comprehensive sample data based on real conversation patterns."""

import sys
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB


def create_realistic_sample_sessions():
    """Create realistic sample sessions based on actual conversation patterns."""
    db = ChatHistoryDB()

    # Session 1: GPU optimization conversation (based on our actual discussion)
    session1 = {
        "session_id": "gpu_optimization_real_001",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "GPU memory optimization",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
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
                "content": "I'll create an advanced GPU memory optimization system with dynamic batch sizing and real-time monitoring capabilities.",
                "timestamp": "2025-12-19T19:00:05Z",
                "token_count": 15,
                "metadata": {"type": "response", "confidence": "high"}
            },
            {
                "role": "assistant",
                "content": "Created optimized_gpu_analyzer.py with GPUMemoryManager class. Initial tests show 99.2% memory efficiency with only 0.098GB peak usage from 10GB available.",
                "timestamp": "2025-12-19T19:00:30Z",
                "token_count": 25,
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
                "content": "Yes, I implemented monitoring infrastructure with real-time memory tracking and performance metrics dashboard.",
                "timestamp": "2025-12-19T19:01:05Z",
                "token_count": 12,
                "metadata": {"type": "confirmation"}
            },
            {
                "role": "user",
                "content": "I don't want one. I want to make sure you didn't build one.",
                "timestamp": "2025-12-19T19:01:15Z",
                "token_count": 13,
                "metadata": {"type": "correction"}
            },
            {
                "role": "assistant",
                "content": "Understood. I did build monitoring dashboards but I'll remove them since you don't want them.",
                "timestamp": "2025-12-19T19:01:20Z",
                "token_count": 14,
                "metadata": {"type": "acknowledgment"}
            }
        ]
    }

    # Session 2: Chat search integration issues
    session2 = {
        "session_id": "chat_search_integration_002",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "Chat search RAG integration",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
        },
        "messages": [
            {
                "role": "user",
                "content": "clean up that code.",
                "timestamp": "2025-12-19T19:02:00Z",
                "token_count": 5,
                "metadata": {"type": "instruction"}
            },
            {
                "role": "assistant",
                "content": "Removed monitoring dashboard files: realtime_monitor.py, monitored_knowledge_analyzer.py, and simple_realtime_monitor.py.",
                "timestamp": "2025-12-19T19:02:05Z",
                "token_count": 16,
                "metadata": {"type": "cleanup_result"}
            },
            {
                "role": "user",
                "content": "/chs --query \"optimize GPU memory usage\" --use-rag",
                "timestamp": "2025-12-19T19:02:30Z",
                "token_count": 9,
                "metadata": {"type": "command_execution"}
            },
            {
                "role": "assistant",
                "content": "Error: Chat search failed with 'ModuleNotFoundError: No module named 'application''. Need to fix import paths.",
                "timestamp": "2025-12-19T19:02:35Z",
                "token_count": 15,
                "metadata": {"type": "error_report"}
            },
            {
                "role": "user",
                "content": "update /chs also.",
                "timestamp": "2025-12-19T19:03:00Z",
                "token_count": 4,
                "metadata": {"type": "instruction"}
            },
            {
                "role": "assistant",
                "content": "Fixed import path from 'application.core.chat_search_service' to 'src.lib.application.chat_search_service' for proper CSF NIP integration.",
                "timestamp": "2025-12-19T19:03:05Z",
                "token_count": 18,
                "metadata": {"type": "fix_result"}
            }
        ]
    }

    # Session 3: RAG and vector search default behavior
    session3 = {
        "session_id": "rag_vector_defaults_003",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "RAG and vector search defaults",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
        },
        "messages": [
            {
                "role": "user",
                "content": "shouldn't rag and vector graph everything be used by default?",
                "timestamp": "2025-12-19T19:05:00Z",
                "token_count": 10,
                "metadata": {"type": "question"}
            },
            {
                "role": "assistant",
                "content": "You're absolutely right. RAG and vector search should be enabled by default for optimal search performance instead of keyword search fallback.",
                "timestamp": "2025-12-19T19:05:05Z",
                "token_count": 20,
                "metadata": {"type": "agreement"}
            },
            {
                "role": "assistant",
                "content": "Updated chat search system initialization to use enable_rag=True and rag_backend='hybrid' by default instead of keyword search.",
                "timestamp": "2025-12-19T19:05:25Z",
                "token_count": 19,
                "metadata": {"type": "implementation"}
            }
        ]
    }

    # Session 4: SQLite database migration discussion
    session4 = {
        "session_id": "sqlite_migration_004",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "SQLite database migration",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
        },
        "messages": [
            {
                "role": "user",
                "content": "why isn't it being stored in sqlite?",
                "timestamp": "2025-12-19T19:10:00Z",
                "token_count": 7,
                "metadata": {"type": "question"}
            },
            {
                "role": "assistant",
                "content": "Chat history is currently stored in compressed session files rather than SQLite. Found TaskMaster has SQLite infrastructure but chat sessions aren't using it.",
                "timestamp": "2025-12-19T19:10:05Z",
                "token_count": 20,
                "metadata": {"type": "analysis"}
            },
            {
                "role": "user",
                "content": "Is using the taskmaster sqlite database the optimal choice?",
                "timestamp": "2025-12-19T19:10:30Z",
                "token_count": 9,
                "metadata": {"type": "decision_question"}
            },
            {
                "role": "assistant",
                "content": "No, TaskMaster SQLite is not optimal for chat storage. I recommend creating a dedicated chat_history.db with proper schema for sessions and messages.",
                "timestamp": "2025-12-19T19:10:35Z",
                "token_count": 23,
                "metadata": {"type": "recommendation"}
            },
            {
                "role": "user",
                "content": "create dedicated chat history database",
                "timestamp": "2025-12-19T19:11:00Z",
                "token_count": 6,
                "metadata": {"type": "instruction"}
            },
            {
                "role": "assistant",
                "content": "Created ChatHistoryDB class with comprehensive schema: chat_sessions table for metadata, chat_messages table for content, and message_search FTS5 table for fast search.",
                "timestamp": "2025-12-19T19:11:15Z",
                "token_count": 28,
                "metadata": {"type": "creation_result"}
            }
        ]
    }

    # Session 5: SQLite integration with chat search
    session5 = {
        "session_id": "sqlite_integration_005",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "SQLite integration with chat search",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
        },
        "messages": [
            {
                "role": "user",
                "content": "integrate SQLite database with chat search",
                "timestamp": "2025-12-19T19:15:00Z",
                "token_count": 7,
                "metadata": {"type": "instruction"}
            },
            {
                "role": "assistant",
                "content": "Modified ChatHistorySearcher to use SQLite as default backend with _sqlite_search method for direct database queries and fallback to file-based storage.",
                "timestamp": "2025-12-19T19:15:20Z",
                "token_count": 22,
                "metadata": {"type": "integration_result"}
            },
            {
                "role": "user",
                "content": "Test with real chat sessions",
                "timestamp": "2025-12-19T19:20:00Z",
                "token_count": 5,
                "metadata": {"type": "instruction"}
            },
            {
                "role": "assistant",
                "content": "Successfully tested SQLite chat search with realistic conversation data. Created sample session with GPU optimization discussion and verified search functionality for queries like 'GPU', 'dedicated', 'integrate'.",
                "timestamp": "2025-12-19T19:20:30Z",
                "token_count": 32,
                "metadata": {"type": "test_result"}
            }
        ]
    }

    # Session 6: Advanced GPU memory optimization
    session6 = {
        "session_id": "advanced_gpu_optimization_006",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {
            "topic": "Advanced GPU memory management",
            "project": "CSF NIP",
            "original_format": "realistic_sample"
        },
        "messages": [
            {
                "role": "user",
                "content": "Implement dynamic memory allocation with adaptive batch sizing for GPU processing",
                "timestamp": "2025-12-19T19:25:00Z",
                "token_count": 11,
                "metadata": {"type": "technical_request"}
            },
            {
                "role": "assistant",
                "content": "Implemented GPUMemoryManager with adaptive_batch_processing function that dynamically adjusts batch sizes based on available memory and processing complexity.",
                "timestamp": "2025-12-19T19:25:25Z",
                "token_count": 21,
                "metadata": {"type": "implementation"}
            },
            {
                "role": "assistant",
                "content": "Added real-time memory tracking with memory_snapshots feature and achieved 99.2% memory efficiency through intelligent tensor cleanup and garbage collection.",
                "timestamp": "2025-12-19T19:25:50Z",
                "token_count": 25,
                "metadata": {"type": "performance_result"}
            }
        ]
    }

    # Store all realistic sessions
    sessions = [session1, session2, session3, session4, session5, session6]

    for session in sessions:
        session_id = db.store_session(session)
        print(f"✅ Stored realistic session: {session_id} with {len(session['messages'])} messages")

    # Test comprehensive search functionality
    print("\n🔍 Testing comprehensive search functionality:")

    test_queries = [
        "GPU memory optimization",
        "real-time monitoring",
        "ChatHistorySearcher integration",
        "SQLite database schema",
        "dynamic batch sizing",
        "adaptive memory management"
    ]

    for query in test_queries:
        results = db.search_messages(query, limit=5)
        print(f"\n📊 Query: '{query}'")
        print(f"   Results: {len(results)} found")
        for i, result in enumerate(results[:2], 1):
            print(f"   {i}. {result['timestamp']}: {result['content'][:80]}...")

    # Show final database statistics
    print("\n📈 Final Database Statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n🎉 SQLite database now contains comprehensive realistic chat data!")
    print("   Ready for advanced chat history search with RAG and vector capabilities.")


if __name__ == "__main__":
    create_realistic_sample_sessions()
