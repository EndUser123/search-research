#!/usr/bin/env python3
"""Example demonstrating session-aware ChatHistoryClient usage.

This example shows how to:
1. Initialize the session-aware client
2. Index multiple sessions with different contexts
3. Perform cross-session queries
4. Preserve and analyze conversation patterns
5. Monitor performance and handle errors

Usage:
    python example_session_aware_usage.py
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any

# Import the enhanced ChatHistoryClient and related classes
from chat_history_client import (
    ChatHistoryClient,
    ChatMessage,
    IntegrationConfig,
    MessageRole,
    SecurityLevel,
)


class SessionAwareDemo:
    """Demonstrates session-aware ChatHistoryClient functionality."""

    def __init__(self) -> None:
        self.client = None
        self.session_data = {}

    async def setup_client(self) -> None:
        """Initialize the session-aware ChatHistoryClient."""
        print("🚀 Initializing Session-Aware ChatHistoryClient...")

        # Configure with session-aware features enabled
        config = IntegrationConfig(
            enabled=True,
            timeout_seconds=30,
            security_level=SecurityLevel.INTERNAL,
            enable_caching=True,
            metadata={
                "enable_session_awareness": True,
                "session_memory_enabled": True,
                "cross_session_queries": True,
                "pattern_preservation_enabled": True,
                "context_query_target_ms": 200,
                "pattern_accuracy_threshold": 0.75,  # Slightly lower for demo
                "database_path": ":memory:",  # In-memory for demo
            },
        )

        # Initialize client
        self.client = ChatHistoryClient(config)
        success = await self.client.initialize()

        if success:
            print("✅ ChatHistoryClient initialized successfully")
            print(f"   Session-aware features: {self.client.enable_session_awareness}")
            print(f"   Cross-session queries: {self.client.cross_session_queries}")
            print(f"   Pattern preservation: {self.client.pattern_preservation_enabled}")
        else:
            raise RuntimeError("Failed to initialize ChatHistoryClient")

    def create_debugging_session(self) -> dict[str, Any]:
        """Create a debugging session example."""
        session_id = "debug_python_api_2024_03_15"

        messages = [
            ChatMessage(
                id="msg_001",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="I'm working on a FastAPI endpoint that's returning a 500 error. The logs show 'Internal Server Error' but no specific details.",
                timestamp=datetime.utcnow() - timedelta(minutes=25),
                metadata={"framework": "fastapi", "error_type": "500_error"},
            ),
            ChatMessage(
                id="msg_002",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Let's help you debug that FastAPI endpoint. Could you share the endpoint code and any relevant stack trace?",
                timestamp=datetime.utcnow() - timedelta(minutes=23),
                metadata={"type": "debugging_help"},
            ),
            ChatMessage(
                id="msg_003",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="The endpoint handles user authentication. It's throwing an error when validating JWT tokens. The error occurs in the token decoding step.",
                timestamp=datetime.utcnow() - timedelta(minutes=20),
                metadata={"domain": "authentication", "token_type": "jwt"},
            ),
            ChatMessage(
                id="msg_004",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="JWT decoding errors often happen due to expired tokens, incorrect secrets, or malformed tokens. Check your token validation logic and ensure the secret key is correctly configured.",
                timestamp=datetime.utcnow() - timedelta(minutes=18),
                metadata={"type": "jwt_debugging"},
            ),
            ChatMessage(
                id="msg_005",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="Found the issue! The secret key was hardcoded and didn't match the environment configuration. Fixed it by loading from environment variables.",
                timestamp=datetime.utcnow() - timedelta(minutes=15),
                metadata={"resolution": "config_fix", "status": "resolved"},
            ),
        ]

        context_data = {
            "messages": messages,
            "keywords": ["fastapi", "debugging", "jwt", "authentication", "500_error", "token"],
            "context_type": "debugging",
            "importance_score": 0.8,
            "metadata": {
                "project": "user_auth_service",
                "framework": "fastapi",
                "resolution_time_minutes": 10,
                "complexity": "medium",
            },
        }

        return session_id, context_data

    def create_architecture_session(self) -> dict[str, Any]:
        """Create an architecture planning session example."""
        session_id = "arch_microservices_2024_03_15"

        messages = [
            ChatMessage(
                id="msg_101",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="We need to design a microservices architecture for our e-commerce platform. Current monolith is becoming hard to maintain.",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                metadata={"domain": "e-commerce", "architecture": "microservices"},
            ),
            ChatMessage(
                id="msg_102",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Great decision! Let's break down the monolith into logical services: User Service, Product Catalog, Order Management, Payment Service, and Inventory Service.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=55),
                metadata={"services": ["user", "product", "order", "payment", "inventory"]},
            ),
            ChatMessage(
                id="msg_103",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="How should we handle data consistency between services? We need to ensure inventory is updated when orders are placed.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=50),
                metadata={"concern": "data_consistency", "pattern": "event_driven"},
            ),
            ChatMessage(
                id="msg_104",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Consider using event-driven architecture with Kafka for async communication. The Order service publishes events that Inventory and Payment services consume. Use sagas for distributed transactions.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=45),
                metadata={"pattern": "event_sourcing", "message_broker": "kafka"},
            ),
            ChatMessage(
                id="msg_105",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="What about API Gateway and service discovery? We're using Kubernetes for deployment.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=40),
                metadata={"infrastructure": "kubernetes", "concern": "routing"},
            ),
            ChatMessage(
                id="msg_106",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Use Kong or Ambassador as API Gateway for routing, rate limiting, and authentication. For service discovery, Kubernetes native services work well. Consider Istio for advanced traffic management.",
                timestamp=datetime.utcnow() - timedelta(hours=1, minutes=35),
                metadata={"api_gateway": "kong", "service_mesh": "istio"},
            ),
        ]

        context_data = {
            "messages": messages,
            "keywords": [
                "microservices",
                "architecture",
                "kubernetes",
                "kafka",
                "api_gateway",
                "event_driven",
            ],
            "context_type": "planning",
            "importance_score": 0.9,  # High importance for architectural decisions
            "metadata": {
                "project": "ecommerce_platform",
                "team_size": 8,
                "timeline": "6_months",
                "complexity": "high",
            },
        }

        return session_id, context_data

    def create_learning_session(self) -> dict[str, Any]:
        """Create a learning/research session example."""
        session_id = "learn_rag_2024_03_15"

        messages = [
            ChatMessage(
                id="msg_201",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="I want to learn about Retrieval-Augmented Generation (RAG) for improving LLM responses with domain-specific knowledge.",
                timestamp=datetime.utcnow() - timedelta(hours=6),
                metadata={"topic": "rag", "llm": "general"},
            ),
            ChatMessage(
                id="msg_202",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="RAG combines retrieval systems with LLMs. The process: 1) Query vector database for relevant documents, 2) Augment prompt with retrieved context, 3) Generate response with enhanced knowledge.",
                timestamp=datetime.utcnow() - timedelta(hours=5, minutes=50),
                metadata={"process": ["retrieve", "augment", "generate"]},
            ),
            ChatMessage(
                id="msg_203",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="What vector databases work well for RAG? I'm considering ChromaDB, Pinecone, and Weaviate.",
                timestamp=datetime.utcnow() - timedelta(hours=5, minutes=40),
                metadata={"vector_dbs": ["chromadb", "pinecone", "weaviate"]},
            ),
            ChatMessage(
                id="msg_204",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="ChromaDB is great for local development and open-source projects. Pinecone offers managed scalability. Weaviate provides hybrid search capabilities. For production, consider factors like scale, latency, and cost.",
                timestamp=datetime.utcnow() - timedelta(hours=5, minutes=30),
                metadata={"comparison": ["local", "managed", "hybrid_search"]},
            ),
            ChatMessage(
                id="msg_205",
                conversation_id=session_id,
                role=MessageRole.USER,
                content="How do you handle embedding updates when documents change? Do you need to re-index everything?",
                timestamp=datetime.utcnow() - timedelta(hours=5, minutes=20),
                metadata={"concern": "embedding_updates", "maintenance": "true"},
            ),
            ChatMessage(
                id="msg_206",
                conversation_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Implement incremental updates: detect document changes, recompute embeddings only for modified content, use version control. Consider strategies like document chunking and metadata filtering for efficient updates.",
                timestamp=datetime.utcnow() - timedelta(hours=5, minutes=10),
                metadata={"strategy": "incremental", "techniques": ["chunking", "versioning"]},
            ),
        ]

        context_data = {
            "messages": messages,
            "keywords": ["rag", "llm", "vector_database", "embeddings", "chromadb", "pinecone"],
            "context_type": "learning",
            "importance_score": 0.7,
            "metadata": {
                "learning_path": "ai_ml",
                "difficulty": "intermediate",
                "practical_application": True,
            },
        }

        return session_id, context_data

    async def demonstrate_session_indexing(self) -> None:
        """Demonstrate session context indexing."""
        print("\n📚 DEMONSTRATION: Session Context Indexing")
        print("=" * 60)

        # Create and index different types of sessions
        sessions = [
            ("Debugging Session", self.create_debugging_session),
            ("Architecture Session", self.create_architecture_session),
            ("Learning Session", self.create_learning_session),
        ]

        for session_name, create_session_func in sessions:
            print(f"\n🏷️  Indexing {session_name}...")

            session_id, context_data = create_session_func()

            # Time the indexing operation
            start_time = time.time()
            success = await self.client.session_context_indexing(session_id, context_data)
            indexing_time = (time.time() - start_time) * 1000

            if success:
                print(f"✅ Session indexed successfully in {indexing_time:.1f}ms")
                print(f"   Session ID: {session_id}")
                print(f"   Context Type: {context_data['context_type']}")
                print(f"   Messages: {len(context_data['messages'])}")
                print(f"   Keywords: {', '.join(context_data['keywords'][:5])}")
                print(f"   Importance Score: {context_data['importance_score']}")

                # Store for later use
                self.session_data[session_id] = context_data
            else:
                print("❌ Failed to index session")

    async def demonstrate_cross_session_queries(self) -> None:
        """Demonstrate cross-session context retrieval."""
        print("\n🔍 DEMONSTRATION: Cross-Session Context Queries")
        print("=" * 60)

        # Define test queries
        test_queries = [
            ("API authentication error debugging", ["fastapi", "jwt", "debugging"]),
            (
                "Microservices architecture design patterns",
                ["microservices", "architecture", "kubernetes"],
            ),
            ("Vector database for RAG implementation", ["rag", "vector_database", "embeddings"]),
            ("Error handling in distributed systems", ["debugging", "microservices", "kafka"]),
        ]

        for query_text, expected_keywords in test_queries:
            print(f"\n🔎 Query: '{query_text}'")
            print(f"   Expected keywords: {', '.join(expected_keywords)}")

            # Time the query
            start_time = time.time()
            results = await self.client.get_cross_session_context(query_text, max_results=5)
            query_time = (time.time() - start_time) * 1000

            print(f"   ⏱️  Query completed in {query_time:.1f}ms")
            print(f"   📊 Found {len(results)} relevant messages")

            # Display results
            for i, message in enumerate(results[:3], 1):  # Show top 3
                print(f"   {i}. [{message.role.value}] {message.content[:80]}...")

            # Check if query met performance target
            if query_time <= self.client.context_query_target_ms:
                print(f"   ✅ Performance target met (<{self.client.context_query_target_ms}ms)")
            else:
                print(
                    f"   ⚠️  Performance target exceeded ({query_time:.1f}ms > {self.client.context_query_target_ms}ms)"
                )

    async def demonstrate_pattern_preservation(self) -> None:
        """Demonstrate conversation pattern preservation."""
        print("\n🎯 DEMONSTRATION: Conversation Pattern Preservation")
        print("=" * 60)

        total_patterns = 0

        for session_id in self.session_data:
            print(f"\n🔍 Analyzing patterns in session: {session_id}")

            # Preserve conversation patterns
            start_time = time.time()
            patterns = await self.client.preserve_conversation_patterns(session_id)
            pattern_time = (time.time() - start_time) * 1000

            print(f"   ⏱️  Pattern analysis completed in {pattern_time:.1f}ms")
            print(f"   📊 Found {len(patterns)} patterns")

            total_patterns += len(patterns)

            # Display pattern details
            for pattern in patterns:
                print(f"   🎯 Pattern: {pattern.pattern_type.value}")
                print(f"      Confidence: {pattern.confidence_score:.2f}")
                print(f"      Key phrases: {', '.join(pattern.key_phrases[:3])}")
                print(f"      Embedding dimensions: {len(pattern.embedding)}")

        print(f"\n📈 Total patterns preserved: {total_patterns}")

    async def demonstrate_relevance_analysis(self) -> None:
        """Demonstrate session relevance analysis."""
        print("\n📏 DEMONSTRATION: Session Relevance Analysis")
        print("=" * 60)

        # Test content with different relevance levels
        test_content = [
            (
                "My FastAPI service is throwing JWT validation errors",
                "High relevance - debugging session",
            ),
            (
                "We need to design microservices for our new platform",
                "High relevance - architecture session",
            ),
            ("How do I implement RAG with ChromaDB?", "High relevance - learning session"),
            ("What's the weather like today?", "Low relevance - unrelated content"),
            ("Python error handling best practices", "Medium relevance - some overlap"),
        ]

        for content, expected_relevance in test_content:
            print(f"\n📝 Analyzing: '{content}'")
            print(f"   Expected: {expected_relevance}")

            # Analyze relevance
            start_time = time.time()
            relevance_score = await self.client.analyze_session_relevance(content)
            analysis_time = (time.time() - start_time) * 1000

            print(f"   📊 Relevance Score: {relevance_score:.3f}")
            print(f"   ⏱️  Analysis time: {analysis_time:.1f}ms")

            # Interpret score
            if relevance_score >= 0.7:
                interpretation = "🟢 Highly relevant"
            elif relevance_score >= 0.4:
                interpretation = "🟡 Moderately relevant"
            else:
                interpretation = "🔴 Low relevance"

            print(f"   💭 Interpretation: {interpretation}")

    async def demonstrate_performance_monitoring(self) -> None:
        """Demonstrate performance monitoring and statistics."""
        print("\n📈 DEMONSTRATION: Performance Monitoring")
        print("=" * 60)

        # Run performance tests
        query_times = []
        test_queries = ["debugging", "architecture", "learning", "api", "database"]

        print("🏃 Running performance tests...")

        for query in test_queries:
            # Measure multiple times for average
            times = []
            for _ in range(3):
                start = time.time()
                await self.client.get_cross_session_context(query, max_results=10)
                duration = (time.time() - start) * 1000
                times.append(duration)

            avg_time = sum(times) / len(times)
            query_times.extend(times)
            print(f"   '{query}': {avg_time:.1f}ms avg")

        # Calculate statistics
        if query_times:
            import statistics

            avg_time = statistics.mean(query_times)
            median_time = statistics.median(query_times)
            min_time = min(query_times)
            max_time = max(query_times)
            p95_time = (
                statistics.quantiles(query_times, n=20)[18] if len(query_times) >= 20 else max_time
            )

            print("\n📊 Performance Statistics:")
            print(f"   Average query time: {avg_time:.1f}ms")
            print(f"   Median query time: {median_time:.1f}ms")
            print(f"   Min query time: {min_time:.1f}ms")
            print(f"   Max query time: {max_time:.1f}ms")
            print(f"   95th percentile: {p95_time:.1f}ms")
            print(f"   Target: <{self.client.context_query_target_ms}ms")

            # Check if target is met
            if p95_time <= self.client.context_query_target_ms:
                print("   ✅ Performance target achieved!")
            else:
                print("   ⚠️  Performance target not met (95th percentile exceeds target)")

    async def demonstrate_session_management(self) -> None:
        """Demonstrate session management capabilities."""
        print("\n🗂️  DEMONSTRATION: Session Management")
        print("=" * 60)

        # Show session statistics
        print("📊 Current Session Statistics:")
        print(f"   Indexed sessions: {len(self.client._session_indices)}")
        print(f"   Stored contexts: {len(self.client._session_contexts)}")
        print(
            f"   Preserved patterns: {sum(len(patterns) for patterns in self.client._session_patterns.values())}"
        )

        # Show session details
        print("\n📋 Session Details:")
        for session_id, index in self.client._session_indices.items():
            context = self.client._session_contexts.get(session_id)
            patterns = self.client._session_patterns.get(session_id, [])

            print(f"\n   Session: {session_id}")
            print(f"   📅 Last updated: {index.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🔤 Keywords: {len(index.context_keywords)} indexed")
            print(f"   🔢 Vectors: {len(index.vector_ids)} stored")
            print(f"   🎯 Patterns: {len(patterns)} preserved")

            if context:
                print(f"   📝 Context Type: {context.context_type.value}")
                print(f"   ⭐ Importance: {context.importance_score:.2f}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("\n🧹 Cleaning up...")

        if self.client:
            await self.client.cleanup()
            print("✅ Client cleaned up successfully")

    async def run_demo(self) -> None:
        """Run the complete demonstration."""
        print("🚀 SESSION-AWARE CHATHISTORYCLIENT DEMONSTRATION")
        print("=" * 70)

        try:
            # Setup
            await self.setup_client()

            # Core functionality demonstrations
            await self.demonstrate_session_indexing()
            await self.demonstrate_cross_session_queries()
            await self.demonstrate_pattern_preservation()
            await self.demonstrate_relevance_analysis()

            # Advanced features
            await self.demonstrate_session_management()
            await self.demonstrate_performance_monitoring()

            print("\n🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
            print("=" * 70)

            # Summary
            print("\n📋 SUMMARY:")
            print("   ✅ Session context indexing - Working")
            print("   ✅ Cross-session queries - Working")
            print("   ✅ Pattern preservation - Working")
            print("   ✅ Relevance analysis - Working")
            print("   ✅ Performance monitoring - Working")
            print("   ✅ Session management - Working")

        except Exception as e:
            print(f"\n❌ DEMONSTRATION FAILED: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # Cleanup
            await self.cleanup()


async def main() -> None:
    """Main function to run the demonstration."""
    demo = SessionAwareDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
