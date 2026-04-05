# TaskMaster Session Integration

## TASK-F-007: Implement TaskMaster Session Integration

This module provides comprehensive session linkage and task continuity management for TaskMaster, integrating with the SessionMemoryBridge to preserve task context across session compactions and restorations.

### Overview

The TaskMaster Session Integration component enables seamless task continuity across session lifecycles, ensuring that critical task context is preserved during session compactions, migrations, and restorations. It bridges TaskMaster's database operations with the SessionMemoryBridge to maintain task state integrity and provide intelligent continuity scoring.

### Key Features

#### 1. Session Linkage Management
- **Task-to-Session Linking**: Associate tasks with specific sessions with comprehensive tracking
- **Session Span Tracking**: Monitor how many sessions a task has spanned across
- **Context Criticality Scoring**: Calculate and store task importance for preservation decisions
- **Pre-compaction State Preservation**: Store task state before session compactions

#### 2. Task Continuity Tracking
- **Continuity Score Calculation**: Multi-factor scoring algorithm for session continuity
- **Critical Task Preservation**: Ensure high-priority tasks survive session transitions
- **State Migration**: Seamless transfer of task state between sessions
- **Integrity Validation**: Verify data integrity across session operations

#### 3. SessionMemoryBridge Integration
- **Automatic Bridge Creation**: Create preservation bridges for critical tasks
- **Context Preservation**: Maintain task context through compaction cycles
- **Restoration Support**: Facilitate task restoration from preserved bridges
- **Fallback Mechanisms**: Graceful handling when SessionMemoryBridge is unavailable

#### 4. Performance Optimization
- **Caching Layer**: Intelligent caching for frequently accessed session data
- **Performance Monitoring**: Real-time performance metrics collection
- **Thread Safety**: Concurrent operation support with proper locking
- **Batch Operations**: Optimized bulk operations for better performance

### Performance Targets

| Operation | Target | Achievement |
|-----------|--------|-------------|
| Session Linkage | <10ms per task | ✅ Achieved |
| Continuity Calculation | <5ms per session | ✅ Achieved |
| Session Migration | <50ms per session | ✅ Achieved |
| Task Retrieval | <20ms per session | ✅ Achieved |
| Memory Overhead | <5% | ✅ Achieved |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                TaskMaster Session Integration               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │ Session Linkage │    │ Task Continuity Tracking    │    │
│  │                 │    │                             │    │
│  │ • Link tasks    │    │ • Continuity scoring        │    │
│  │ • Session span  │    │ • Critical task preservation│    │
│  │ • Criticality   │    │ • State migration           │    │
│  └─────────────────┘    └─────────────────────────────┘    │
│                                   │                         │
│                                   ▼                         │
│  ┌─────────────────────────────────────────────────────────┤
│  │           SessionMemoryBridge Integration               │
│  │                                                         │
│  │ • Bridge creation • Context preservation                │
│  │ • Restoration support • Fallback handling               │
│  └─────────────────────────────────────────────────────────┤
│                                   │                         │
│                                   ▼                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │ Database Layer  │    │ Performance & Caching       │    │
│  │                 │    │                             │    │
│  │ • Task records  │    │ • Metrics collection        │    │
│  │ • Session track │    │ • Intelligent caching       │    │
│  │ • State storage │    │ • Thread safety             │    │
│  └─────────────────┘    └─────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### API Reference

#### Core Class: `TaskMasterSessionIntegration`

```python
class TaskMasterSessionIntegration:
    """Integration layer for TaskMaster session management."""

    def __init__(
        self,
        dal: Optional[WorkspaceTaskDAL] = None,
        session_memory_bridge: Optional[SessionMemoryBridge] = None,
        performance_monitoring: bool = True
    ):
        """Initialize the session integration."""
```

#### Key Methods

##### 1. Session Linkage

```python
def link_tasks_to_session(
    self,
    task_ids: List[str],
    session_id: str
) -> SessionLinkageResult:
    """
    Link tasks to a session with comprehensive tracking.

    Args:
        task_ids: List of task IDs to link
        session_id: Session ID to link to

    Returns:
        SessionLinkageResult: Detailed linkage results
    """
```

##### 2. Continuity Scoring

```python
def get_session_continuity_score(self, session_id: str) -> ContinuityScoreResult:
    """
    Calculate continuity score for a session.

    Args:
        session_id: Session to analyze

    Returns:
        ContinuityScoreResult: Detailed continuity analysis
    """
```

##### 3. Session Migration

```python
def migrate_session_state(
    self,
    old_session: str,
    new_session: str
) -> SessionMigrationResult:
    """
    Migrate session state from old to new session.

    Args:
        old_session: Source session ID
        new_session: Target session ID

    Returns:
        SessionMigrationResult: Migration results
    """
```

##### 4. Active Task Retrieval

```python
def get_active_session_tasks(self, session_id: str) -> ActiveSessionTasks:
    """
    Get active tasks for a session.

    Args:
        session_id: Session to query

    Returns:
        ActiveSessionTasks: Session tasks and statistics
    """
```

#### Result Classes

##### `SessionLinkageResult`
```python
@dataclass
class SessionLinkageResult:
    success: bool
    linked_tasks: List[str]
    failed_tasks: List[str]
    session_id: str
    execution_time_ms: float
    warnings: List[str]
    errors: List[str]
```

##### `ContinuityScoreResult`
```python
@dataclass
class ContinuityScoreResult:
    session_id: str
    continuity_score: float
    total_tasks: int
    preserved_tasks: int
    critical_tasks_preserved: int
    session_span: int
    last_compaction: Optional[datetime]
    calculation_time_ms: float
    factors: Dict[str, float]
```

### Usage Examples

#### Basic Session Linkage

```python
from session_integration import TaskMasterSessionIntegration
from db import get_dal

# Initialize integration
dal = get_dal()
integration = TaskMasterSessionIntegration(dal=dal)

# Link tasks to session
task_ids = ["task1", "task2", "task3"]
session_id = "session-123"

result = integration.link_tasks_to_session(task_ids, session_id)

if result.success:
    print(f"Successfully linked {len(result.linked_tasks)} tasks")
    print(f"Execution time: {result.execution_time_ms:.1f}ms")
```

#### Continuity Score Analysis

```python
# Calculate continuity score
result = integration.get_session_continuity_score(session_id)

print(f"Continuity Score: {result.continuity_score:.3f}")
print(f"Total Tasks: {result.total_tasks}")
print(f"Preserved Tasks: {result.preserved_tasks}")
print(f"Critical Factors: {result.factors}")

# Interpret score
if result.continuity_score >= 0.9:
    print("Excellent continuity")
elif result.continuity_score >= 0.7:
    print("Good continuity")
else:
    print("Needs improvement")
```

#### Session Migration

```python
# Migrate session state
old_session = "session-old"
new_session = "session-new"

result = integration.migrate_session_state(old_session, new_session)

if result.success:
    print(f"Successfully migrated {len(result.migrated_tasks)} tasks")
    if result.bridge_created:
        print(f"Context bridge created: {result.bridge_id}")
    print(f"Migration time: {result.migration_time_ms:.1f}ms")
```

#### Active Task Retrieval

```python
# Get active session tasks
result = integration.get_active_session_tasks(session_id)

print(f"Session: {result.session_id}")
print(f"Total tasks: {result.total_count}")
print(f"Active tasks: {result.active_count}")
print(f"Critical tasks: {result.critical_count}")

# Access individual tasks
for task in result.tasks:
    print(f"Task: {task.title}")
    print(f"Status: {task.status}")
    print(f"Progress: {task.progress:.1%}")
```

### Database Schema

The integration extends the existing TaskMaster database schema with session-related columns:

#### Task Table Extensions
```sql
ALTER TABLE task ADD COLUMN session_id TEXT;
ALTER TABLE task ADD COLUMN session_span INTEGER DEFAULT 0;
ALTER TABLE task ADD COLUMN pre_compaction_state TEXT;
ALTER TABLE task ADD COLUMN context_criticality REAL DEFAULT 0.0;
ALTER TABLE task ADD COLUMN compaction_session_id TEXT;
```

#### Session Tracking Table
```sql
CREATE TABLE session_tracking (
    session_id TEXT PRIMARY KEY,
    task_master_session_id TEXT,
    started_at TIMESTAMP,
    last_compaction TIMESTAMP,
    compaction_count INTEGER DEFAULT 0,
    total_context_tokens INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Performance Indexes
```sql
CREATE INDEX idx_task_session_id ON task(session_id);
CREATE INDEX idx_task_compaction_session ON task(compaction_session_id);
CREATE INDEX idx_task_session_span ON task(session_span);
CREATE INDEX idx_task_context_criticality ON task(context_criticality);
CREATE INDEX idx_session_tracking_status ON session_tracking(status);
```

### Continuity Score Algorithm

The continuity score is calculated using a weighted combination of factors:

```
Continuity Score = (
    Preservation Factor × 0.4 +
    Critical Factor × 0.3 +
    Span Factor × 0.15 +
    Recency Factor × 0.15
)
```

#### Factor Definitions

1. **Preservation Factor** (0.0-1.0)
   - Ratio of tasks with preserved pre-compaction state
   - Higher value indicates better state preservation

2. **Critical Factor** (0.0-1.0)
   - Ratio of critical tasks that were preserved
   - Emphasizes preservation of high-importance tasks

3. **Span Factor** (0.0-1.0)
   - Normalized session span (min(1.0, span/5.0))
   - Rewards tasks that have survived multiple sessions

4. **Recency Factor** (0.0-1.0)
   - Time-based decay since last compaction
   - Newer compactions get higher scores

### Configuration

The integration can be configured through constructor parameters:

```python
integration = TaskMasterSessionIntegration(
    dal=custom_dal,                    # Custom data access layer
    session_memory_bridge=custom_bridge,  # Custom bridge instance
    performance_monitoring=True        # Enable/disable metrics
)
```

### Performance Monitoring

The integration provides built-in performance monitoring:

```python
# Get performance metrics
metrics = integration.get_performance_metrics()

for operation, metric in metrics.items():
    print(f"{operation}:")
    print(f"  Count: {metric['count']}")
    print(f"  Avg Time: {metric['avg_time_ms']:.2f}ms")
    print(f"  Last 10 Avg: {metric['last_10_avg_ms']:.2f}ms")
```

### Error Handling

The integration includes comprehensive error handling:

- **Graceful Degradation**: Continues operating when SessionMemoryBridge is unavailable
- **Partial Success Handling**: Reports partial failures with detailed information
- **Validation**: Input validation with clear error messages
- **Thread Safety**: Safe concurrent access with proper locking

### Testing

Run the comprehensive test suite:

```bash
python -m pytest test_session_integration.py -v
```

Test coverage includes:
- ✅ Session linkage operations
- ✅ Continuity score calculations
- ✅ Session state migrations
- ✅ Active session task retrieval
- ✅ Performance validation
- ✅ Error handling and edge cases
- ✅ Thread safety
- ✅ Integration with SessionMemoryBridge

### Demo Script

Run the interactive demo to see all features in action:

```bash
python demo_session_integration.py
```

The demo covers:
- Basic session linkage
- Continuity score analysis
- Session migration with bridge creation
- Active task retrieval
- Performance monitoring
- Cross-compaction continuity

### Dependencies

**Required Dependencies:**
- Python 3.8+
- sqlite3
- pathlib
- typing
- dataclasses
- threading
- json
- time
- uuid
- datetime
- logging

**Optional Dependencies:**
- SessionMemoryBridge (from `__csf.nip.src.core.session_memory`)
- CriticalityCalculator (from `__csf.nip.src.core.session_memory`)
- TaskContext model (from `__csf.nip.src.core.session_memory.models`)

### Migration Guide

If upgrading from a previous version without session support:

1. **Run Database Migration:**
   ```bash
   python add_session_columns_final.py
   ```

2. **Update Application Code:**
   ```python
   # Old code
   dal = get_dal()

   # New code
   from session_integration import get_session_integration
   integration = get_session_integration()
   ```

3. **Update Task Creation:**
   ```python
   # Consider session linkage when creating tasks
   integration.link_tasks_to_session([task_id], session_id)
   ```

### Troubleshooting

#### Common Issues

1. **SessionMemoryBridge Not Available**
   - **Symptom**: Warning messages about missing SessionMemoryBridge
   - **Solution**: Install SessionMemoryBridge components or continue with limited functionality

2. **Performance Issues**
   - **Symptom**: Operations exceeding performance targets
   - **Solution**: Check performance metrics and consider caching optimization

3. **Database Schema Issues**
   - **Symptom**: Errors about missing columns
   - **Solution**: Run the session columns migration script

4. **Memory Usage**
   - **Symptom**: High memory usage with many sessions
   - **Solution**: Use cache clearing and monitoring features

### Future Enhancements

Planned improvements for future versions:

1. **Advanced Continuity Algorithms**
   - Machine learning-based criticality assessment
   - Dynamic weight adjustment based on usage patterns

2. **Enhanced Bridge Integration**
   - Automatic bridge cleanup and maintenance
   - Bridge sharing between related sessions

3. **Performance Optimizations**
   - Asynchronous operations for large-scale deployments
   - Distributed caching support

4. **Analytics and Reporting**
   - Session continuity trend analysis
   - Performance dashboards and alerts

### Contributing

To contribute to the TaskMaster Session Integration:

1. **Code Style**: Follow PEP 8 and existing code patterns
2. **Testing**: Add comprehensive tests for new features
3. **Documentation**: Update documentation for API changes
4. **Performance**: Ensure new features meet performance targets
5. **Review**: Submit pull requests for code review

### License

This module is part of the CSF NIP (Critical Session Framework - Next Integration Platform) project and follows the same licensing terms.

### Support

For support and questions:
- Create issues in the project repository
- Check the troubleshooting section above
- Review the demo script for usage examples
- Consult the API documentation

---

**Implementation Status**: ✅ Complete
**Performance Targets**: ✅ All Met
**Test Coverage**: ✅ Comprehensive
**Documentation**: ✅ Complete

*Last Updated: 2025-12-13*
