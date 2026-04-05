# Session Management Command Reference

A comprehensive cheat sheet for session management operations. Print this page for quick reference.

## Core Operations

### System Initialization
```python
from session_management_hook_events import SessionManagementHookSystem

# Basic initialization
system = SessionManagementHookSystem()

# With configuration
config = {
    "archive_storage_path": "/path/to/archives",
    "max_concurrent_hooks": 10,
    "default_timeout": 30.0,
    "compression_level": 6
}
system = SessionManagementHookSystem(config)
```

### Session Merge
```python
from session_management_hook_events import (
    SessionMergeEvent, SessionMergeStrategy
)

# Create merge event
merge_event = system.create_session_merge_event(
    primary_session=primary_session,
    merge_sessions=[session1, session2, session3],
    merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY,  # Options: CONTEXT_PRIORITY, TIME_BASED, TASK_TYPE, CUSTOM
    conflict_resolution="primary_wins"  # Options: primary_wins, merge_all, timestamp_priority
)

# Execute merge
results = await system.execute_session_merge(merge_event)
```

### Session Split
```python
from session_management_hook_events import (
    SessionSplitEvent, SessionSplitCriteria
)

# Create split event
split_event = system.create_session_split_event(
    source_session=complex_session,
    split_criteria=SessionSplitCriteria.BY_TASK_TYPE,  # Options: BY_TASK_TYPE, BY_TIME_RANGE, BY_FILE_TYPE, BY_USER, CUSTOM
    target_sessions=[
        {"session_id": "dev_part", "filter": {"task_type": "development"}},
        {"session_id": "test_part", "filter": {"task_type": "testing"}}
    ]
)

# Execute split
results = await system.execute_session_split(split_event)
```

### Session Archive
```python
from session_management_hook_events import SessionArchiveEvent

# Create archive event
archive_event = system.create_session_archive_event(
    session_data=session_to_archive,
    archive_options={
        "compress": True,                    # Enable compression
        "compression_level": 6,             # 1-9 (higher = smaller, slower)
        "encrypt": False,                    # Enable encryption
        "storage_location": "local_archive", # Storage location
        "retention_days": 90,               # Days to keep archive
        "create_backup": True,              # Create backup before archive
        "validate_integrity": True          # Verify archive integrity
    }
)

# Execute archive
results = await system.execute_session_archive(archive_event)
```

### Session Restore
```python
from session_management_hook_events import SessionRestoreEvent
from datetime import datetime, timedelta
from pathlib import Path

# Create restore event
restore_event = system.create_session_restore_event(
    archive_path=Path("/path/to/archive.json.gz"),
    restore_point=datetime.now() - timedelta(hours=1),  # Restore point in time
    restore_options={
        "partial_restore": False,              # Restore all or selected components
        "restore_components": ["context", "metadata", "chat_history"],  # Components to restore
        "validate_integrity": True,            # Verify archive integrity
        "create_backup": True,                 # Backup current state
        "merge_strategy": "replace",           # How to merge with existing data
        "conflict_resolution": "archive_priority"  # Handle conflicts
    }
)

# Execute restore
results = await system.execute_session_restore(restore_event)
```

## Utility Functions

### Session Context Merging
```python
from session_management_hook_events import merge_session_contexts

# Merge contexts with strategy
merged_context = await merge_session_contexts(
    primary=primary_session,
    merge_sessions=[session1, session2],
    strategy=SessionMergeStrategy.CONTEXT_PRIORITY
)
```

### Compression Operations
```python
from session_management_hook_events import compress_session_data, decompress_session_data

# Compress session data
compressed_data = await compress_session_data(
    session_data=session,
    compression_level=6
)

# Decompress session data
restored_session = await decompress_session_data(compressed_data)
```

### Archive Path Management
```python
from session_management_hook_events import create_session_archive_path

# Create archive file path
archive_path = create_session_archive_path(
    session_id="my_session_001",
    archive_storage=Path("/path/to/archive/directory")
)
# Returns: /path/to/archive/directory/session_my_session_001_20251127_143022.json.gz
```

### Session Validation
```python
from session_merge_utils import validate_session_structure, calculate_session_hash

# Validate session structure
validate_session_structure(session_data)

# Calculate integrity hash
session_hash = calculate_session_hash(session_data)
```

## System Status & Monitoring

### Get System Status
```python
# Comprehensive status
status = system.get_session_management_status()

# Key status fields
print(f"Archived sessions: {status['archived_sessions']}")
print(f"Operation history size: {status['operation_history_size']}")
print(f"Performance metrics: {status['performance_metrics']}")
```

### Get Operation History
```python
# Get all recent operations
history = system.get_operation_history(limit=100)

# Filter by operation type
merge_history = system.get_operation_history(operation_type="session_merge", limit=50)
archive_history = system.get_operation_history(operation_type="session_archive", limit=50)
```

### Performance Metrics
```python
# Access performance metrics directly
metrics = system.performance_metrics

print(f"Merge operations: {metrics['merge_operations']['count']}")
print(f"Average merge time: {metrics['merge_operations']['avg_time']:.3f}s")
print(f"Archive operations: {metrics['archive_operations']['count']}")
print(f"Average archive time: {metrics['archive_operations']['avg_time']:.3f}s")
```

## Configuration Options

### System Configuration
```python
config = {
    # Core settings
    "max_concurrent_hooks": 10,        # Maximum concurrent hook executions
    "default_timeout": 30.0,           # Default timeout for operations (seconds)
    "isolation_enabled": True,         # Enable hook isolation

    # Archive settings
    "archive_storage_path": "/tmp/csf_nip_session_archives",  # Archive directory
    "compression_level": 6,            # Default compression level (1-9)
    "retention_days": 90,              # Default retention period

    # Performance settings
    "enable_performance_tracking": True,    # Track operation metrics
    "operation_history_limit": 1000,        # Max operations in history

    # Validation settings
    "validate_sessions": True,         # Validate session structure
    "integrity_checks": True,          # Perform integrity checks
}
```

### Hook Configuration
```python
from modules.orchestration.hook_system import HookMetadata, HookType

# Create custom hook
async def my_session_hook(event):
    # Custom hook logic
    return {"status": "success", "processed": True}

hook_metadata = HookMetadata(
    name="my_session_hook",
    hook_type=HookType.TASK_COMPLETE,  # or appropriate hook type
    function=my_session_hook,
    priority=100,                      # Higher priority = executes first
    timeout=10.0,                      # Maximum execution time
    enabled=True
)

# Register hook
system.register_hook(hook_metadata)
```

## Merge Strategies

### CONTEXT_PRIORITY
```python
# Primary session context takes precedence
strategy = SessionMergeStrategy.CONTEXT_PRIORITY
# Result: Primary session context preserved, merge sessions add new keys only
```

### TIME_BASED
```python
# Most recent activity wins
strategy = SessionMergeStrategy.TIME_BASED
# Result: Sessions sorted by last_activity, newest wins conflicts
```

### TASK_TYPE
```python
# Merge by task type priorities
strategy = SessionMergeStrategy.TASK_TYPE
# Result: Task type-based merging with defined priorities
```

### CUSTOM
```python
# Custom merge logic
strategy = SessionMergeStrategy.CUSTOM
# Result: Requires custom merge implementation
```

## Split Criteria

### BY_TASK_TYPE
```python
criteria = SessionSplitCriteria.BY_TASK_TYPE
# Splits session into separate sessions by task_type in chat_history
```

### BY_TIME_RANGE
```python
criteria = SessionSplitCriteria.BY_TIME_RANGE
# Splits session by time periods (hourly, daily, etc.)
```

### BY_FILE_TYPE
```python
criteria = SessionSplitCriteria.BY_FILE_TYPE
# Splits session by file types referenced in context
```

### BY_USER
```python
criteria = SessionSplitCriteria.BY_USER
# Splits session by user_id or user interactions
```

## Error Handling

### Common Exceptions
```python
try:
    results = await system.execute_session_merge(merge_event)
except ValueError as e:
    print(f"Validation error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Result Validation
```python
results = await system.execute_session_merge(merge_event)

# Check results
for result in results:
    if result.status == HookStatus.COMPLETED:
        print(f"✅ Hook {result.hook_name} completed successfully")
    elif result.status == HookStatus.FAILED:
        print(f"❌ Hook {result.hook_name} failed: {result.error}")
    elif result.status == HookStatus.TIMEOUT:
        print(f"⏰ Hook {result.hook_name} timed out")
```

## Quick Commands

### One-Liners for Common Tasks
```python
# Quick session merge
merge_event = system.create_session_merge_event(primary, [s1, s2])
results = await system.execute_session_merge(merge_event)

# Quick session archive
archive_event = system.create_session_archive_event(session)
results = await system.execute_session_archive(archive_event)

# Quick system status
status = system.get_session_management_status()
print(f"System running: {len(status['session_management_hooks'])} hooks active")

# Quick operation check
history = system.get_operation_history(limit=5)
for op in history:
    print(f"{op['timestamp']}: {op['operation_type']} - {op['success_count']}/{op['hook_count']} successful")
```

## Environment Variables

### Optional Environment Configuration
```bash
# Archive storage location
export CSF_NIP_ARCHIVE_PATH="/path/to/archives"

# System configuration
export CSF_NIP_MAX_HOOKS="20"
export CSF_NIP_DEFAULT_TIMEOUT="60"

# Compression settings
export CSF_NIP_COMPRESSION_LEVEL="6"
export CSF_NIP_RETENTION_DAYS="90"

# Performance settings
export CSF_NIP_PERFORMANCE_TRACKING="true"
export CSF_NIP_HISTORY_LIMIT="1000"
```

---

**💡 Pro Tip:** Keep this reference handy while developing. Most operations follow a consistent pattern: create event → execute operation → handle results.

**🚀 Need more examples?** See the [interactive guide](./interactive-guide.md) for working examples.
