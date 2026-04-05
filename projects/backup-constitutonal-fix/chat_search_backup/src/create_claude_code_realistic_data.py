#!/usr/bin/env python3
"""Create realistic Claude Code conversation data for testing."""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB


def create_realistic_claude_code_conversations():
    """Create realistic Claude Code conversations based on actual usage patterns."""
    print("🎭 Creating Realistic Claude Code Conversations")
    print("=" * 50)

    db = ChatHistoryDB()

    # Realistic Claude Code conversation scenarios
    conversations = [
        {
            "session_id": "claude_code_file_analysis_001",
            "topic": "File analysis and code review",
            "scenario": "Developer asking Claude to analyze a Python file",
            "messages": [
                {
                    "role": "user",
                    "content": "Can you analyze this Python file and suggest improvements for performance and readability?",
                    "timestamp": "2025-12-19T10:30:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I'd be happy to analyze your Python file. Could you please share the file path or paste the code you'd like me to review? I'll look for performance bottlenecks, code style issues, and suggest specific improvements based on Python best practices.",
                    "timestamp": "2025-12-19T10:30:05Z"
                },
                {
                    "role": "user",
                    "content": "The file is at src/data_processor.py. It's a data processing pipeline that's running slower than expected.",
                    "timestamp": "2025-12-19T10:30:30Z"
                },
                {
                    "role": "assistant",
                    "content": "I'll analyze the data processing pipeline in src/data_processor.py for you. Let me check the file structure and identify potential performance issues such as inefficient loops, memory usage patterns, and I/O operations.",
                    "timestamp": "2025-12-19T10:30:35Z"
                },
                {
                    "role": "assistant",
                    "content": "After analyzing src/data_processor.py, I found several optimization opportunities:\n\n1. **Memory Efficiency**: Using list comprehensions instead of loops for data transformation\n2. **I/O Optimization**: Implementing batch processing for database operations\n3. **Algorithm Improvement**: Replacing nested loops with more efficient data structures\n4. **Caching**: Adding memoization for expensive computations\n\nWould you like me to implement these improvements with specific code changes?",
                    "timestamp": "2025-12-19T10:31:15Z"
                }
            ]
        },
        {
            "session_id": "claude_code_git_workflow_002",
            "topic": "Git workflow and version control",
            "scenario": "Developer asking about Git branching strategies",
            "messages": [
                {
                    "role": "user",
                    "content": "What's the best Git branching strategy for a team of 5 developers working on different features?",
                    "timestamp": "2025-12-19T11:15:00Z"
                },
                {
                    "role": "assistant",
                    "content": "For a team of 5 developers, I recommend the **GitFlow** branching strategy with some modern adaptations:\n\n**Main Branches:**\n- `main` (production)\n- `develop` (integration)\n- `feature/*` (individual features)\n- `release/*` (release preparation)\n- `hotfix/*` (urgent fixes)\n\n**Workflow:**\n1. Create feature branches from `develop`\n2. Use pull requests for code review\n3. Merge to `develop` after approval\n4. Create release branches from `develop`\n5. Merge release to `main` after testing\n\nWould you like me to set up the initial Git configuration and create branch protection rules?",
                    "timestamp": "2025-12-19T11:15:20Z"
                },
                {
                    "role": "user",
                    "content": "Yes, please help me set up the Git configuration and branch protection rules.",
                    "timestamp": "2025-12-19T11:16:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I'll help you set up a comprehensive Git workflow configuration. Let me create the necessary Git configuration files and GitHub/GitLab branch protection rules.",
                    "timestamp": "2025-12-19T11:16:05Z"
                },
                {
                    "role": "assistant",
                    "content": "I've created the following configuration files:\n\n1. `.git/config` - Repository-specific settings\n2. `.github/workflows/branch-protection.yml` - GitHub branch rules\n3. `.gitlab-ci.yml` - GitLab CI/CD pipeline\n4. `CONTRIBUTING.md` - Team guidelines\n\nThe configuration includes:\n- Required pull request reviews (2 reviewers)\n- Status checks (CI/CD must pass)\n- Branch deletion after merge\n- Linear commit history\n- Automated testing\n\nWould you like me to explain any specific part of the configuration?",
                    "timestamp": "2025-12-19T11:17:30Z"
                }
            ]
        },
        {
            "session_id": "claude_code_docker_optimization_003",
            "topic": "Docker and containerization",
            "scenario": "Developer asking about Docker optimization",
            "messages": [
                {
                    "role": "user",
                    "content": "My Docker images are too large and slow to build. How can I optimize them?",
                    "timestamp": "2025-12-19T14:20:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Docker image optimization is crucial for CI/CD performance. Here are the key strategies I recommend:\n\n**1. Multi-stage Builds**\n- Separate build and runtime environments\n- Use .dockerignore to exclude unnecessary files\n- Leverage layer caching\n\n**2. Base Image Optimization**\n- Use alpine or distroless images\n- Remove unnecessary packages\n- Use specific version tags\n\n**3. Layer Optimization**\n- Order instructions by frequency of change\n- Combine related RUN commands\n- Use --mount for cache\n\nLet me examine your Dockerfile and provide specific optimization recommendations.",
                    "timestamp": "2025-12-19T14:20:25Z"
                },
                {
                    "role": "user",
                    "content": "Here's my Dockerfile. It's for a Node.js application with TypeScript.",
                    "timestamp": "2025-12-19T14:21:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I'll optimize your Node.js TypeScript Dockerfile. Based on common issues, I'll implement a multi-stage build with layer caching and use a lightweight base image.",
                    "timestamp": "2025-12-19T14:21:05Z"
                },
                {
                    "role": "assistant",
                    "content": "I've optimized your Dockerfile with these improvements:\n\n**Size Reduction:** 75% smaller (from 1.2GB to 300MB)\n**Build Speed:** 60% faster with layer caching\n**Security:** Non-root user and minimal attack surface\n\nKey changes:\n- Multi-stage build (builder + runtime)\n- npm ci with cache mount\n- .dockerignore optimizations\n- Alpine Linux base image\n- Combined RUN commands\n\nThe optimized image now builds in 45 seconds instead of 2+ minutes. Would you like me to explain any specific optimization technique?",
                    "timestamp": "2025-12-19T14:22:45Z"
                }
            ]
        },
        {
            "session_id": "claude_code_api_design_004",
            "topic": "API design and REST endpoints",
            "scenario": "Developer asking about API design patterns",
            "messages": [
                {
                    "role": "user",
                    "content": "I'm designing a REST API for a task management system. What are the best practices for endpoint design and error handling?",
                    "timestamp": "2025-12-19T16:45:00Z"
                },
                {
                    "role": "assistant",
                    "content": "For a task management API, I recommend following RESTful principles with these key design patterns:\n\n**Resource Naming:**\n- Use plural nouns (/tasks, /users, /projects)\n- Nest related resources (/projects/{id}/tasks)\n- Use consistent HTTP methods\n\n**Response Format:**\n- Standard JSON structure\n- Consistent error responses\n- Include pagination metadata\n\n**Error Handling:**\n- Proper HTTP status codes\n- Detailed error messages\n- Request ID for tracing\n\nWould you like me to create specific endpoint definitions with request/response examples?",
                    "timestamp": "2025-12-19T16:45:20Z"
                },
                {
                    "role": "user",
                    "content": "Yes, please create the API specification with OpenAPI documentation.",
                    "timestamp": "2025-12-19T16:46:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I'll create a comprehensive OpenAPI 3.0 specification for your task management API with all CRUD operations, authentication, and error handling.",
                    "timestamp": "2025-12-19T16:46:05Z"
                },
                {
                    "role": "assistant",
                    "content": "I've created the complete OpenAPI specification including:\n\n**Endpoints:**\n- GET /tasks (list with filtering)\n- POST /tasks (create)\n- GET /tasks/{id} (read)\n- PUT /tasks/{id} (update)\n- DELETE /tasks/{id} (delete)\n- PATCH /tasks/{id}/status (status update)\n\n**Features:**\n- JWT authentication\n- Role-based access control\n- Pagination and sorting\n- Comprehensive error responses\n- Request validation\n- Rate limiting headers\n\nThe spec is ready for Swagger UI integration and automated testing. Would you like me to implement the backend code in Express.js or FastAPI?",
                    "timestamp": "2025-12-19T16:48:30Z"
                }
            ]
        },
        {
            "session_id": "claude_code_database_schema_005",
            "topic": "Database design and SQL optimization",
            "scenario": "Developer asking about database schema optimization",
            "messages": [
                {
                    "role": "user",
                    "content": "My database queries are slow. How can I optimize the database schema and improve query performance?",
                    "timestamp": "2025-12-19T09:30:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Database optimization requires a systematic approach. Let me help you identify and fix performance bottlenecks:\n\n**Analysis Areas:**\n1. Schema design and normalization\n2. Indexing strategy\n3. Query optimization\n4. Connection pooling\n5. Database configuration\n\n**Common Issues:**\n- Missing indexes on foreign keys\n- N+1 query problems\n- Inefficient JOIN operations\n- Large table scans\n\nCan you share your database schema and slow queries? I'll analyze them and provide specific optimization recommendations.",
                    "timestamp": "2025-12-19T09:30:20Z"
                },
                {
                    "role": "user",
                    "content": "The main issue is with user authentication queries that take 2-3 seconds. Here's the schema.",
                    "timestamp": "2025-12-19T09:31:00Z"
                },
                {
                    "role": "assistant",
                    "content": "2-3 seconds for authentication queries is definitely too slow. Let me analyze your schema and identify the bottlenecks.",
                    "timestamp": "2025-12-19T09:31:05Z"
                },
                {
                    "role": "assistant",
                    "content": "I found several performance issues in your authentication schema:\n\n**Critical Problems:**\n1. Missing index on email/username columns\n2. No composite index for (email, password_hash)\n3. Full table scans on user_sessions\n4. Missing foreign key indexes\n\n**Optimizations Applied:**\n- Added strategic indexes (reduced query time by 90%)\n- Implemented query result caching\n- Optimized JOIN operations\n- Added database connection pooling\n\nYour authentication queries now execute in 50-100ms instead of 2-3 seconds. Would you like me to create a migration script for these changes?",
                    "timestamp": "2025-12-19T09:33:45Z"
                }
            ]
        },
        {
            "session_id": "claude_code_testing_strategy_006",
            "topic": "Testing strategy and test automation",
            "scenario": "Developer asking about comprehensive testing approach",
            "messages": [
                {
                    "role": "user",
                    "content": "How should I structure my testing strategy for a microservices application?",
                    "timestamp": "2025-12-19T13:10:00Z"
                },
                {
                    "role": "assistant",
                    "content": "For microservices testing, I recommend the **Testing Pyramid** approach with different test levels:\n\n**Unit Tests (70%)**\n- Individual service logic\n- Business rules validation\n- Mock external dependencies\n\n**Integration Tests (20%)**\n- API endpoint testing\n- Database interactions\n- Message queue integration\n\n**End-to-End Tests (10%)\n- User workflows\n- Cross-service communication\n- UI automation\n\nWould you like me to create a specific testing framework setup for your tech stack?",
                    "timestamp": "2025-12-19T13:10:25Z"
                },
                {
                    "role": "user",
                    "content": "We're using Node.js with Express, PostgreSQL, and Redis. Please create the testing setup.",
                    "timestamp": "2025-12-19T13:11:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I'll create a comprehensive testing setup for your Node.js microservices stack with Jest, Supertest, and test containers.",
                    "timestamp": "2025-12-19T13:11:05Z"
                },
                {
                    "role": "assistant",
                    "content": "I've created a complete testing framework including:\n\n**Test Configuration:**\n- Jest setup with TypeScript support\n- Test database (Docker containers)\n- Mock services and utilities\n\n**Test Categories:**\n- Unit tests for business logic\n- API integration tests\n- Database transaction tests\n- Redis caching tests\n- End-to-end workflow tests\n\n**CI/CD Integration:**\n- Automated test execution\n- Code coverage reporting\n- Performance testing\n\nThe setup provides 85% code coverage and runs all tests in 2 minutes. Would you like me to explain the test organization or add specific test cases?",
                    "timestamp": "2025-12-19T13:13:40Z"
                }
            ]
        }
    ]

    print(f"\n🔄 Creating {len(conversations)} realistic Claude Code conversations...")

    created_sessions = 0
    created_messages = 0

    for conversation in conversations:
        # Convert to session format
        session_data = {
            "session_id": conversation["session_id"],
            "model": "claude-sonnet-4-5-20250929",
            "metadata": {
                "topic": conversation["topic"],
                "scenario": conversation["scenario"],
                "original_format": "realistic_claude_code_conversation"
            },
            "messages": []
        }

        # Add messages with proper timestamps
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))

        for i, msg in enumerate(conversation["messages"]):
            # Create realistic timestamp with time between messages
            message_time = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))

            message = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": message_time.isoformat() + "Z",
                "token_count": len(msg["content"].split()) + random.randint(5, 15),
                "metadata": {
                    "type": "claude_code_conversation",
                    "topic": conversation["topic"],
                    "scenario": conversation["scenario"],
                    "message_position": i
                }
            }

            session_data["messages"].append(message)

        # Store session in database
        stored_id = db.store_session(session_data)
        created_sessions += 1
        created_messages += len(session_data["messages"])

        print(f"   ✅ Created: {conversation['topic']} ({len(session_data['messages'])} messages)")

    print("\n📊 Creation Summary:")
    print(f"   Sessions Created: {created_sessions}")
    print(f"   Messages Created: {created_messages}")
    print(f"   Avg Messages/Session: {created_messages / created_sessions:.1f}")

    # Test search with realistic data
    print("\n🔍 Testing Search with Realistic Claude Code Conversations:")

    test_queries = [
        "Docker optimization",
        "database performance",
        "API design",
        "testing strategy",
        "Git workflow"
    ]

    for query in test_queries:
        results = db.search_messages(query, limit=3)
        print(f"\n📎 Query: '{query}'")
        print(f"   Results: {len(results)} found")

        for i, result in enumerate(results[:2], 1):
            content_preview = result['content'][:100]
            print(f"   {i}. [{result['role']}] {content_preview}...")

    # Show final database stats
    print("\n📈 Final Database Statistics:")
    final_stats = db.get_stats()
    for key, value in final_stats.items():
        if isinstance(value, int):
            print(f"   {key}: {value:,}")
        else:
            print(f"   {key}: {value}")

    print("\n🎉 Realistic Claude Code conversation testing complete!")
    print("   Database now contains authentic conversation patterns")
    print("   Search system tested with real-world scenarios")


if __name__ == "__main__":
    create_realistic_claude_code_conversations()
