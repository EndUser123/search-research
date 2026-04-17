# Session-Aware ChatHistoryClient Usage Guide

## Overview

The enhanced ChatHistoryClient now includes session-aware capabilities that enable cross-session context retrieval, conversation pattern preservation, and intelligent memory management. This guide explains how to use these features effectively.

## Key Features

### 1. Session Context Indexing
- Automatically index session conversations for efficient retrieval
- Generate semantic embeddings for content understanding
- Support multiple session context types (debugging, research, planning, etc.)
- Integration with CKS vector storage for scalability

### 2. Cross-Session Query Capabilities
- Search across all indexed sessions for relevant context
- Keyword-based and semantic similarity matching
- Performance-optimized queries (<200ms target)

### 3. Conversation Pattern Preservation
- Detect and preserve important conversation patterns
- Generate pattern representations for similarity matching
- Support pattern restoration and analysis

### 4. Session Memory Bridge Integration
- Seamless integration with SessionMemoryBridge for context preservation
- Automatic compaction bridge creation for critical sessions
- Memory-efficient session management

## Quick Start

### Basic Setup

```python
from features.cks.integration.clients.chat_history_client import (
    ChatHistoryClient,
    IntegrationConfig,
    SecurityLevel,
)
from features.cks.integration.clients.chat_history_client import ChatMessage, MessageRole

# Configure session-aware client
config = IntegrationConfig(
    enabled=True,
    security_level=SecurityLevel.INTERNAL,
    metadata={
        "enable_session_awareness": True,
        "session_memory_enabled": True,
        "cross_session_queries": True,
        "pattern_preservation_enabled": True,
        "context_query_target_ms": 200,
        "pattern_accuracy_threshold": 0.85,
    }
)

# Initialize client
client = ChatHistoryClient(config)
await client.initialize()
```

### Indexing a Session

```python
from datetime import datetime
from features.cks.integration.clients.chat_history_client import SessionContextType

# Prepare session data
session_id = "debug_session_2024_03_15"
messages = [
    ChatMessage(
        id="msg_001",
        conversation_id=session_id,
        role=MessageRole.USER,
        content="I'm having issues with a Python function that's throwing an exception",
        timestamp=datetime.utcnow() - timedelta(minutes=10),
        metadata={"language": "python", "type": "debugging"}
    ),
    ChatMessage(
        id="msg_002",
        conversation_id=session_id,
        role=MessageRole.ASSISTANT,
        content="I can help you debug that. Could you share the function code?",
        timestamp=datetime.utcnow() - timedelta(minutes=8),
        metadata={"type": "debugging_help"}
    )
]

# Create session context data
context_data = {
    "messages": messages,
    "keywords": ["python", "debugging", "exception", "error"],
    "context_type": "debugging",
    "importance_score": 0.8,
    "metadata": {
        "project": "data_processor",
        "user_role": "developer",
        "session_length_minutes": 25
    }
}

# Index the session
success = await client.session_context_indexing(session_id, context_data)
print(f"Session indexed: {success}")
```

### Cross-Session Query

```python
# Search for relevant context across all sessions
results = await client.get_cross_session_context(
    keywords="python debugging exception",
    max_results=10
)

print(f"Found {len(results)} relevant messages:")
for message in results:
    print(f"- {message.role.value}: {message.content[:100]}...")
```

### Pattern Preservation

```python
# Detect and preserve conversation patterns
patterns = await client.preserve_conversation_patterns(session_id)

print(f"Preserved {len(patterns)} patterns:")
for pattern in patterns:
    print(f"- {pattern.pattern_type.value}: {pattern.confidence_score:.2f}")
```

### Session Relevance Analysis

```python
# Analyze how relevant new content is to current session context
content = "I need help with a Python error in my data processing function"
relevance = await client.analyze_session_relevance(content)

print(f"Content relevance score: {relevance:.2f}")
```

## Advanced Usage

### Custom Session Context Types

```python
# Use different session context types
context_types = {
    "research": SessionContextType.RESEARCH,
    "planning": SessionContextType.PLANNING,
    "debugging": SessionContextType.DEBUGGING,
    "review": SessionContextType.REVIEW,
    "collaboration": SessionContextType.COLLABORATION,
    "learning": SessionContextType.LEARNING,
}

context_data = {
    "messages": messages,
    "keywords": ["machine learning", "model training", "tensorflow"],
    "context_type": "research",
    "importance_score": 0.9,
    "metadata": {
        "project": "ml_experiment",
        "research_area": "computer_vision",
    }
}
```

### Memory Index Management

```python
# Create comprehensive memory index for a session
success = await client.create_session_memory_index(session_id)

# Access session indices
if session_id in client._session_indices:
    index = client._session_indices[session_id]
    print(f"Session indexed with {len(index.vector_ids)} vectors")
    print(f"Keywords: {', '.join(index.context_keywords)}")
```

### Performance Optimization

```python
# Configure for optimal performance
config = IntegrationConfig(
    metadata={
        # Enable all session-aware features
        "enable_session_awareness": True,
        "session_memory_enabled": True,
        "cross_session_queries": True,
        "pattern_preservation_enabled": True,

        # Performance targets
        "context_query_target_ms": 150,  # Lower target for better performance
        "pattern_accuracy_threshold": 0.75,  # Lower threshold for more patterns

        # Storage configuration
        "enable_semantic_search": True,
        "embedding_model": "fast_embedding",  # Use fast embedding model
    }
)

# Monitor performance
import time

start = time.time()
results = await client.get_cross_session_context("query", max_results=20)
duration = (time.time() - start) * 1000

print(f"Query completed in {duration:.1f}ms")
```

## Integration with SessionMemoryBridge

```python
# The client automatically integrates with SessionMemoryBridge if available
# Sessions with high importance scores will be preserved automatically

high_importance_session = {
    "messages": critical_messages,
    "keywords": ["critical", "important", "must_preserve"],
    "context_type": "active_work",
    "importance_score": 0.95,  # High importance for preservation
    "metadata": {"critical_session": True}
}

await client.session_context_indexing("critical_session", high_importance_session)
# This session will automatically be preserved via SessionMemoryBridge
```

## Configuration Options

### Core Session-Aware Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_session_awareness` | `True` | Enable session-aware features |
| `session_memory_enabled` | `True` | Enable SessionMemoryBridge integration |
| `cross_session_queries` | `True` | Enable cross-session context search |
| `pattern_preservation_enabled` | `True` | Enable conversation pattern preservation |

### Performance Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `context_query_target_ms` | `200` | Target time for context queries |
| `pattern_accuracy_threshold` | `0.85` | Minimum confidence for pattern preservation |

### Session Context Types

- `ACTIVE_WORK`: Active development work sessions
- `RESEARCH`: Research and exploration sessions
- `DEBUGGING`: Problem-solving and debugging sessions
- `PLANNING`: Architecture and planning sessions
- `LEARNING`: Educational and learning sessions
- `COLLABORATION`: Team collaboration sessions
- `REVIEW`: Code review and feedback sessions

## Error Handling

```python
# Handle validation errors
try:
    await client.session_context_indexing("", {})  # Empty session_id
except ValidationException as e:
    print(f"Validation error: {e}")

# Handle missing context gracefully
results = await client.get_cross_session_context("nonexistent topic")
# Returns empty list if no relevant context found

# Check session availability before operations
if session_id in client._session_contexts:
    patterns = await client.preserve_conversation_patterns(session_id)
else:
    print("Session not found - need to index first")
```

## Performance Best Practices

### 1. Optimize Session Size
```python
# Break large sessions into smaller, focused sessions
# Each session should represent a coherent work session
# Ideal session size: 50-200 messages
```

### 2. Use Appropriate Keywords
```python
# Use specific, relevant keywords for better indexing
context_data = {
    "keywords": [
        "python", "asyncio", "concurrency",  # Specific technologies
        "bug_fix", "performance_optimization",  # Task types
        "user_authentication", "database_queries",  # Domain-specific terms
    ]
}
```

### 3. Set Correct Importance Scores
```python
# Use importance scores to prioritize critical sessions
importance_scores = {
    "critical_bug_fix": 0.9,
    "feature_development": 0.7,
    "routine_discussion": 0.5,
    "experimentation": 0.6,
}
```

### 4. Monitor Performance
```python
import time
import statistics

# Track query performance
query_times = []
for query in test_queries:
    start = time.time()
    await client.get_cross_session_context(query)
    duration = (time.time() - start) * 1000
    query_times.append(duration)

print(f"Average query time: {statistics.mean(query_times):.1f}ms")
print(f"95th percentile: {statistics.quantiles(query_times, n=20)[18]:.1f}ms")
```

## Testing

The enhanced ChatHistoryClient includes comprehensive tests. Run them with:

```bash
cd __csf.nip/src/features/cks/integration/clients
python -m pytest test_session_aware_chat_history_client.py -v
```

Key test coverage:
- Session context indexing
- Cross-session queries
- Pattern preservation
- Performance targets
- Error handling
- Integration testing

## Troubleshooting

### Common Issues

1. **Slow query performance**
   - Check if `context_query_target_ms` is set appropriately
   - Verify CKS vector storage is available and initialized
   - Consider reducing pattern accuracy threshold

2. **No relevant context found**
   - Ensure sessions are properly indexed before querying
   - Check if keywords match indexed session keywords
   - Verify cross-session queries are enabled

3. **Pattern preservation not working**
   - Check if `pattern_preservation_enabled` is True
   - Verify messages contain pattern-eligible content
   - Adjust `pattern_accuracy_threshold` if too strict

4. **Memory usage too high**
   - Disable unused features in configuration
   - Implement regular cleanup of old sessions
   - Use appropriate importance scores to limit preservation

### Debug Information

```python
# Check client status
print(f"Session-aware enabled: {client.enable_session_awareness}")
print(f"Indexed sessions: {len(client._session_indices)}")
print(f"Stored patterns: {sum(len(patterns) for patterns in client._session_patterns.values())}")
print(f"CKS storage available: {client._cks_storage is not None}")
print(f"SessionMemoryBridge available: {client._session_memory_bridge is not None}")
```

## Future Enhancements

Planned improvements to session-aware functionality:

1. **Enhanced Pattern Recognition**
   - More sophisticated pattern detection algorithms
   - Support for custom pattern types
   - Pattern evolution tracking

2. **Improved Vector Storage**
   - Better integration with production vector databases
   - Embedding model fine-tuning
   - Incremental embedding updates

3. **Advanced Memory Management**
   - Automatic session cleanup based on relevance
   - Memory usage optimization
   - Intelligent session merging

4. **Analytics and Insights**
   - Session pattern analytics
   - Collaboration insights
   - Development workflow optimization

## Migration Guide

To migrate existing ChatHistoryClient usage to session-aware:

1. **Update configuration**
   ```python
   config.metadata.update({
       "enable_session_awareness": True,
       "session_memory_enabled": True,
   })
   ```

2. **Add session indexing**
   ```python
   # Replace direct message storage with session indexing
   await client.session_context_indexing(session_id, context_data)
   ```

3. **Update search operations**
   ```python
   # Replace direct searches with cross-session queries
   results = await client.get_cross_session_context(query)
   ```

4. **Handle new imports**
   ```python
   from features.cks.integration.clients.chat_history_client import (
       SessionContextType,
       SessionContext,
   )
   ```

The enhanced client maintains backward compatibility with existing functionality while adding powerful session-aware capabilities.
