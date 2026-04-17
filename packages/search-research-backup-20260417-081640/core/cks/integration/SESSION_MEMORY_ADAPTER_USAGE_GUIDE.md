# Session Memory Adapter Usage Guide

## Overview

The SessionMemoryAdapter provides advanced conversation pattern preservation and reconstruction capabilities for session memory management across compactions. This guide demonstrates how to use the adapter effectively in your applications.

## Key Features

### Pattern Detection Algorithms
- **Accuracy Target**: >85% pattern detection accuracy
- **Performance Target**: <50ms for typical sessions
- **Pattern Types**: Question-answer, problem-solving, code discussion, planning, review, learning, debugging
- **Advanced Analysis**: Temporal patterns, semantic clusters, intent recognition

### Semantic Similarity Scoring
- **Similarity Threshold**: >0.8 threshold support
- **Performance Target**: <20ms per comparison
- **Features**: Multi-dimensional similarity, embedding-based matching, structural analysis
- **Clustering**: Hierarchical clustering with semantic coherence

### Pattern Reconstruction
- **Performance Target**: <100ms for complex scenarios
- **Quality Validation**: Multi-dimensional quality assessment
- **Memory Efficiency**: <10MB overhead for pattern storage
- **Gap Filling**: Intelligent pattern element completion

## Quick Start

### Basic Initialization

```python
from cks.integration.session_memory_adapter import SessionMemoryAdapter
from cks.integration.chat_history_client import ChatHistoryClient
from core.session_memory.session_memory_bridge import SessionMemoryBridge

# Initialize components
chat_client = ChatHistoryClient(config)
session_bridge = SessionMemoryBridge()

# Create adapter
adapter = SessionMemoryAdapter(
    chat_history_client=chat_client,
    session_memory_bridge=session_bridge,
    storage_manager=None,  # Optional: for CKS integration
    device_manager=None,   # Optional: for GPU acceleration
    cache_size_mb=50,
    enable_advanced_features=True
)
```

### Pattern Detection

```python
import asyncio
from datetime import datetime

async def detect_patterns_example():
    # Sample conversation messages
    messages = [
        {
            "content": "I need help debugging this Python function.",
            "role": "user",
            "timestamp": datetime.utcnow()
        },
        {
            "content": "I can help with that. What's the specific error?",
            "role": "assistant",
            "timestamp": datetime.utcnow()
        },
        # ... more messages
    ]

    # Detect patterns
    patterns = await adapter.detect_conversation_patterns(
        messages=messages,
        session_id="debug_session_001"
    )

    print(f"Detected {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"- {pattern['pattern_type']}: {pattern['confidence']:.2f}")

# Run the example
asyncio.run(detect_patterns_example())
```

## Advanced Usage Examples

### 1. Pattern Evolution Tracking

```python
async def track_pattern_evolution_example():
    # Initial pattern
    pattern = {
        'pattern_id': 'debug_pattern_001',
        'pattern_type': 'debugging_session',
        'confidence': 0.7,
        'frequency': 0.5
    }

    # New messages in the conversation
    new_messages = [
        {
            "content": "Now I'm getting a different error about imports.",
            "role": "user",
            "timestamp": datetime.utcnow()
        },
        {
            "content": "You need to add the missing import statements.",
            "role": "assistant",
            "timestamp": datetime.utcnow()
        }
    ]

    # Track evolution
    evolution = await adapter.track_pattern_evolution(pattern, new_messages)

    print(f"Pattern evolution: {evolution.evolution_summary}")
    print(f"Confidence trend: {evolution.confidence_trend}")
```

### 2. Semantic Pattern Clustering

```python
async def cluster_patterns_example():
    # Multiple patterns from different sessions
    all_patterns = [
        {
            'pattern_id': 'pattern_001',
            'pattern_type': 'question_answer',
            'embedding': [0.1, 0.2, 0.3, ...],  # 384-dim vector
            'keywords': ['python', 'debugging']
        },
        {
            'pattern_id': 'pattern_002',
            'pattern_type': 'problem_solving',
            'embedding': [0.15, 0.25, 0.35, ...],
            'keywords': ['python', 'fix']
        },
        # ... more patterns
    ]

    # Cluster similar patterns
    clusters = await adapter.cluster_related_patterns(
        patterns=all_patterns,
        max_clusters=5
    )

    print(f"Created {len(clusters)} clusters:")
    for cluster_id, pattern_ids in clusters.items():
        print(f"Cluster {cluster_id}: {len(pattern_ids)} patterns")
```

### 3. Context Reconstruction

```python
async def reconstruct_context_example():
    # Preserved patterns from compaction
    preserved_patterns = [
        {
            'pattern_id': 'preserved_001',
            'pattern_type': 'planning',
            'importance_score': 0.9,
            'keywords': ['architecture', 'design'],
            'embedding': [0.2, 0.3, 0.4, ...]
        },
        # ... more preserved patterns
    ]

    # Bridge data from compaction
    bridge_data = {
        'session_metadata': {
            'original_session_id': 'session_123',
            'compaction_timestamp': datetime.utcnow(),
            'total_messages': 50
        }
    }

    # Reconstruct context
    reconstruction = await adapter.reconstruct_conversation_context(
        patterns=preserved_patterns,
        bridge_data=bridge_data
    )

    # Check reconstruction quality
    quality = reconstruction['quality']
    print(f"Reconstruction quality: {quality.overall_quality:.3f}")
    print(f"Completeness: {quality.completeness_score:.3f}")
    print(f"Accuracy: {quality.accuracy_score:.3f}")
```

### 4. Cross-Session Pattern Analysis

```python
async def cross_session_analysis_example():
    # Find similar patterns across sessions
    current_pattern = {
        'pattern_id': 'current_session_pattern',
        'pattern_type': 'debugging_session',
        'embedding': [0.1, 0.2, 0.3, ...],
        'keywords': ['python', 'error', 'exception']
    }

    # Search for similar historical patterns
    similar_patterns = await adapter.find_similar_historical_patterns(
        pattern=current_pattern,
        similarity_threshold=0.8,
        max_results=10
    )

    print(f"Found {len(similar_patterns)} similar patterns:")
    for result in similar_patterns:
        print(f"- Similarity: {result['similarity_score']:.3f}")
        print(f"  Session: {result['historical_session_id']}")
        print(f"  Created: {result['created_at']}")
```

## Integration with Chat History Client

### Using Chat History Data

```python
async def integrate_with_chat_history():
    # Get messages from ChatHistoryClient
    chat_request = ChatHistoryRequest(
        query="debugging session",
        time_range_days=7,
        pattern_types={ConversationPattern.DEBUGGING_SESSION}
    )

    result = await chat_client.search_chat_history(chat_request)
    messages = result.messages

    # Detect patterns using SessionMemoryAdapter
    patterns = await adapter.detect_conversation_patterns(
        messages=[msg.__dict__ for msg in messages],  # Convert to dict format
        session_id="chat_history_analysis"
    )

    # Analyze and enhance patterns
    for pattern in patterns:
        # Calculate importance
        importance = await adapter.analyze_pattern_importance(
            pattern, [msg.__dict__ for msg in messages]
        )
        pattern['importance_score'] = importance

        # Identify key decisions
        if pattern['pattern_type'] == 'decision_making':
            decisions = await adapter.identify_key_decisions(
                [msg.__dict__ for msg in messages]
            )
            pattern['key_decisions'] = decisions

    return patterns
```

## Session Compaction Integration

### Preserving Patterns During Compaction

```python
async def preserve_during_compaction(session_id: str):
    # Detect current session patterns
    session_messages = await get_session_messages(session_id)  # Your implementation
    patterns = await adapter.detect_conversation_patterns(
        session_messages, session_id=session_id
    )

    # Preserve important patterns across compaction
    success = await adapter.preserve_patterns_across_compaction(
        session_id=session_id,
        patterns=patterns,
        criticality_threshold=0.7  # Only preserve high-importance patterns
    )

    if success:
        print(f"Successfully preserved critical patterns for session {session_id}")
    else:
        print(f"Failed to preserve patterns for session {session_id}")
```

### Restoring Patterns After Compaction

```python
async def restore_after_compaction(bridge_id: str):
    # Restore patterns from compaction bridge
    restored_patterns = await adapter.restore_patterns_from_compaction(bridge_id)

    if restored_patterns:
        print(f"Restored {len(restored_patterns)} patterns")

        # Validate restoration quality
        bridge_data = await load_bridge_data(bridge_id)  # Your implementation
        reconstruction = await adapter.reconstruct_conversation_context(
            restored_patterns, bridge_data
        )

        quality = reconstruction['quality']
        print(f"Restoration quality: {quality.overall_quality:.3f}")

        return reconstruction
    else:
        print("No patterns to restore")
        return None
```

## Performance Optimization

### Caching Configuration

```python
# Configure for high-performance scenarios
high_performance_adapter = SessionMemoryAdapter(
    cache_size_mb=100,  # Larger cache for better performance
    enable_advanced_features=True,
    storage_manager=cks_storage_manager  # Use CKS for vector operations
)

# Monitor performance
metrics = high_performance_adapter.get_performance_metrics()
print("Performance Metrics:")
for operation, stats in metrics.items():
    print(f"{operation}:")
    print(f"  Average: {stats['avg_time_ms']:.1f}ms")
    print(f"  Count: {stats['count']}")
    print(f"  Min/Max: {stats['min_time_ms']:.1f}ms/{stats['max_time_ms']:.1f}ms")
```

### Batch Processing

```python
async def batch_pattern_analysis(sessions: List[str]):
    """Process multiple sessions efficiently."""
    results = []

    # Process sessions in batches to optimize memory usage
    batch_size = 10
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i:i + batch_size]

        # Process batch concurrently
        batch_tasks = []
        for session_id in batch:
            messages = await get_session_messages(session_id)
            task = adapter.detect_conversation_patterns(
                messages, session_id=session_id
            )
            batch_tasks.append(task)

        # Wait for batch completion
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

        print(f"Processed batch {i//batch_size + 1}: {len(batch)} sessions")

    return results
```

## Error Handling and Edge Cases

### Robust Error Handling

```python
async def robust_pattern_detection(messages: List[Dict]):
    """Detect patterns with comprehensive error handling."""
    try:
        # Validate input
        if not messages or not isinstance(messages, list):
            logger.warning("Invalid message input")
            return []

        # Filter valid messages
        valid_messages = [
            msg for msg in messages
            if isinstance(msg, dict) and msg.get('content') and msg.get('role')
        ]

        if not valid_messages:
            logger.warning("No valid messages found")
            return []

        # Detect patterns with timeout
        try:
            patterns = await asyncio.wait_for(
                adapter.detect_conversation_patterns(valid_messages),
                timeout=10.0  # 10 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Pattern detection timed out")
            return []

        # Validate results
        if not isinstance(patterns, list):
            logger.error("Invalid pattern detection result")
            return []

        return patterns

    except Exception as e:
        logger.exception(f"Pattern detection failed: {e}")
        return []
```

## Testing and Validation

### Unit Testing Example

```python
import pytest
from cks.integration.session_memory_adapter import SessionMemoryAdapter

@pytest.mark.asyncio
async def test_pattern_detection_performance():
    adapter = SessionMemoryAdapter()

    # Test with sample data
    messages = [
        {"content": "Help me debug this code", "role": "user"},
        {"content": "What error are you seeing?", "role": "assistant"}
    ]

    start_time = time.time()
    patterns = await adapter.detect_conversation_patterns(messages)
    execution_time = (time.time() - start_time) * 1000

    # Validate performance target
    assert execution_time < 50, f"Too slow: {execution_time}ms"
    assert len(patterns) > 0, "Should detect patterns"

    # Cleanup
    await adapter.cleanup()
```

### Integration Testing

```python
async def test_end_to_end_workflow():
    """Test complete workflow from detection to reconstruction."""

    # Step 1: Detect patterns
    messages = load_test_conversation()
    patterns = await adapter.detect_conversation_patterns(messages)

    # Step 2: Select important patterns
    important_patterns = [
        p for p in patterns if p.get('importance_score', 0) > 0.7
    ]

    # Step 3: Simulate compaction
    bridge_data = simulate_compaction(important_patterns)

    # Step 4: Reconstruct context
    reconstruction = await adapter.reconstruct_conversation_context(
        important_patterns, bridge_data
    )

    # Step 5: Validate quality
    quality = reconstruction['quality']
    assert quality.overall_quality > 0.5, "Poor reconstruction quality"

    print(f"✓ End-to-end workflow successful (quality: {quality.overall_quality:.3f})")
```

## Best Practices

### 1. Memory Management
- Set appropriate cache sizes based on available memory
- Cleanup adapters when no longer needed
- Monitor memory usage in production

### 2. Performance Optimization
- Use batch processing for multiple sessions
- Enable GPU acceleration when available
- Configure appropriate similarity thresholds

### 3. Error Handling
- Always validate input data
- Implement timeout handling for long operations
- Provide fallback behavior for critical failures

### 4. Integration Guidelines
- Integrate with existing chat history systems
- Use SessionMemoryBridge for cross-compaction preservation
- Leverage CKS vector storage for large-scale deployments

### 5. Monitoring and Maintenance
- Track performance metrics regularly
- Monitor pattern accuracy and quality
- Update embedding models as needed

## Troubleshooting

### Common Issues

1. **Pattern Detection Too Slow**
   - Increase cache size
   - Enable GPU acceleration
   - Reduce input message count

2. **Low Pattern Accuracy**
   - Check message formatting
   - Verify embedding generation
   - Adjust confidence thresholds

3. **Memory Usage High**
   - Reduce cache size
   - Implement regular cleanup
   - Use persistent storage for embeddings

4. **Reconstruction Quality Poor**
   - Increase preserved pattern count
   - Verify bridge data integrity
   - Check pattern importance scores

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Create adapter with debug features
debug_adapter = SessionMemoryAdapter(
    enable_advanced_features=True,
    cache_size_mb=10  # Smaller cache for debugging
)

# Get detailed metrics
metrics = debug_adapter.get_performance_metrics()
print("Detailed metrics:", json.dumps(metrics, indent=2))
```

## Conclusion

The SessionMemoryAdapter provides powerful conversation pattern preservation and reconstruction capabilities. By following this guide and best practices, you can effectively integrate these capabilities into your applications while maintaining high performance and reliability.

For additional support or questions, refer to the test files and implementation examples provided in the codebase.
