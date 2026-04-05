# Visual Tutorial - Step-by-Step Session Management

A comprehensive visual guide to get you started with the session management system. Follow these screenshots and instructions to master the basics.

## Step 1: Installation & Setup

### Screenshot 1: Terminal Installation
```
[User@localhost ~]$ cd csf-nip
[User@localhost csf-nip]$ pip install -r requirements.txt
Collecting required packages...
Successfully installed...
[User@localhost csf-nip]$ cd src/modules/session_management/hooks
```

### Screenshot 2: Directory Structure
```
session_management/
├── hooks/
│   ├── session_management_hook_events.py    ← Main system file
│   ├── demo_session_management.py          ← Demo script
│   └── test_session_management_hook_events.py ← Tests
└── README.md                              ← Documentation
```

## Step 2: Your First Session

### Screenshot 3: Creating a Session in Python
```python
# In your Python editor
from session_management_hook_events import SessionManagementHookSystem
from datetime import datetime

# Initialize the system
system = SessionManagementHookSystem()

# Create your first session
session = {
    "session_id": "demo_001",
    "user_id": "user_123",
    "context": {
        "workspace": "my_project",
        "current_task": "getting_started",
        "chat_history": [
            {"role": "user", "content": "Start new session"},
            {"role": "assistant", "content": "Session created successfully!"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 1
    }
}

print("✓ Session created!")
```

**Expected Output:**
```
✓ Session created!
```

## Step 3: Merging Sessions

### Screenshot 4: Session Merge Workflow
```python
# Primary session (your current work)
primary_session = {
    "session_id": "main_dev_001",
    "context": {
        "workspace": "web_app",
        "current_file": "auth.py",
        "active_branch": "feature/login"
    }
}

# Sessions to merge (previous research, planning sessions)
merge_sessions = [
    {
        "session_id": "research_002",
        "context": {
            "api_docs": "JWT authentication endpoints",
            "security_notes": "Use bcrypt for passwords"
        }
    },
    {
        "session_id": "planning_003",
        "context": {
            "user_stories": "User login and registration",
            "timeline": "2-week sprint"
        }
    }
]

# Create merge event
merge_event = system.create_session_merge_event(
    primary_session=primary_session,
    merge_sessions=merge_sessions,
    merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY
)

# Execute merge
results = await system.execute_session_merge(merge_event)
print("✓ Sessions merged successfully!")
```

**Visual Result:**
```
Before Merge:                After Merge:
┌─────────────────┐         ┌──────────────────────┐
│ Main Session    │    +    │ Research + Planning   │  →  ┌──────────────────────┐
│ auth.py         │         │ JWT docs, security   │     │ Unified Session      │
│ login branch    │         │ User stories, time   │     │ auth.py + docs       │
└─────────────────┘         └──────────────────────┘     │ + planning info      │
                                                       └──────────────────────┘
```

## Step 4: Splitting Sessions

### Screenshot 5: Session Split Interface
```python
# Complex session with multiple task types
complex_session = {
    "session_id": "dev_cycle_004",
    "context": {
        "chat_history": [
            {"role": "user", "content": "Implement user auth", "task_type": "development"},
            {"role": "assistant", "content": "Added JWT auth system", "task_type": "development"},
            {"role": "user", "content": "Write tests for auth", "task_type": "testing"},
            {"role": "assistant", "content": "Created test suite", "task_type": "testing"},
            {"role": "user", "content": "Update API docs", "task_type": "documentation"},
            {"role": "assistant", "content": "API docs updated", "task_type": "documentation"}
        ]
    }
}

# Split by task type
split_event = system.create_session_split_event(
    source_session=complex_session,
    split_criteria=SessionSplitCriteria.BY_TASK_TYPE
)

# Execute split
results = await system.execute_session_split(split_event)
print("✓ Session split into development, testing, and documentation sessions")
```

**Visual Split Result:**
```
Original Session:                           Split Sessions:
┌─────────────────────────────────┐         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Mixed Development Cycle         │    →    │ Development     │ │   Testing       │ │ Documentation   │
│ • Auth implementation           │         │ • JWT auth      │ │ • Unit tests    │ │ • API docs      │
│ • Unit tests                    │         │ • User login    │ │ • Integration   │ │ • Endpoints     │
│ • API documentation             │         │ • Registration  │ │ • Coverage      │ │ • Examples      │
└─────────────────────────────────┘         └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Step 5: Archiving Sessions

### Screenshot 6: Archive Configuration
```python
# Session to archive (completed project)
completed_session = {
    "session_id": "project_alpha_005",
    "context": {
        "project": "E-commerce Platform",
        "status": "completed",
        "deliverables": ["Frontend", "Backend", "Database"],
        "chat_history": [...]  # 100+ messages
    },
    "metadata": {
        "duration": 7200,  # 2 hours
        "tasks_completed": 15
    }
}

# Archive with compression
archive_event = system.create_session_archive_event(
    session_data=completed_session,
    archive_options={
        "compress": True,
        "compression_level": 6,  # Balance between speed and size
        "retention_days": 90,
        "validate_integrity": True
    }
)

# Execute archive
results = await system.execute_session_archive(archive_event)
print(f"✓ Session archived (compressed from 2.4MB to 0.7MB)")
```

**Archive Visual:**
```
Before Archive:                   After Archive:
┌─────────────────────┐          ┌─────────────────────┐
│ Active Session      │  →       │   Archived File     │
│ • 2.4MB data        │          │ • 0.7MB compressed  │
│ • 100+ messages     │          │ • Integrity hash    │
│ • 15 tasks          │          │ • 90-day retention  │
│ • Memory intensive  │          │ • Auto-cleanup      │
└─────────────────────┘          └─────────────────────┘
```

## Step 6: Restoring Sessions

### Screenshot 7: Restore Process
```python
from pathlib import Path
from datetime import datetime, timedelta

# Restore from archive
archive_path = Path("/path/to/archives/session_project_alpha_005_20251127_143022.json.gz")

restore_event = system.create_session_restore_event(
    archive_path=archive_path,
    restore_point=datetime.now() - timedelta(days=1),  # Restore from yesterday
    restore_options={
        "partial_restore": False,  # Restore everything
        "restore_components": ["context", "metadata", "chat_history"],
        "validate_integrity": True,
        "conflict_resolution": "archive_priority"
    }
)

# Execute restore
results = await system.execute_session_restore(restore_event)
print("✓ Session restored with full integrity validation")
```

**Restore Visual:**
```
Archive File:                     Restored Session:
┌─────────────────────┐          ┌─────────────────────┐
│ Compressed Archive  │  →       │ Active Session      │
│ • 0.7MB size        │          │ • 2.4MB restored    │
│ • Integrity hash    │          │ • All messages      │
│ • 90-day old        │          │ • Ready to use      │
└─────────────────────┘          └─────────────────────┘
```

## Step 7: System Status & Monitoring

### Screenshot 8: Status Dashboard
```python
# Get comprehensive system status
status = system.get_session_management_status()

print("Session Management System Status:")
print(f"  📁 Archived sessions: {status['archived_sessions']}")
print(f"  📊 Operations history: {status['operation_history_size']}")
print(f"  ⚡ Performance metrics:")
for op_type, metrics in status['performance_metrics'].items():
    print(f"    {op_type}: {metrics['count']} ops, {metrics['avg_time']:.3f}s avg")

# Get recent operations
recent_ops = system.get_operation_history(limit=10)
print("  📈 Recent operations:")
for op in recent_ops:
    print(f"    {op['timestamp']}: {op['operation_type']} ({op['execution_time']:.3f}s)")
```

**Status Output Example:**
```
Session Management System Status:
  📁 Archived sessions: 23
  📊 Operations history: 157
  ⚡ Performance metrics:
    merge_operations: 45 ops, 0.234s avg
    split_operations: 12 ops, 0.156s avg
    archive_operations: 67 ops, 0.089s avg
    restore_operations: 33 ops, 0.312s avg
  📈 Recent operations:
    2025-11-27T14:30:22: session_archive (0.087s)
    2025-11-27T14:28:15: session_merge (0.245s)
    2025-11-27T14:25:03: session_split (0.134s)
```

## Step 8: Quick Verification

### Screenshot 9: Demo Script Execution
```bash
# Run the complete demo
$ python demo_session_management.py

Session Management Hook System Demo
====================================

✓ Session Merge Demo
  - Merged 3 sessions successfully
  - Context priority strategy applied
  - 0.23s execution time

✓ Session Split Demo
  - Split complex session by task type
  - Created 3 focused sessions
  - 0.15s execution time

✓ Session Archive Demo
  - Compressed session (71% reduction)
  - Integrity hash generated
  - Archive created at: /tmp/csf_nip_session_archives/

✓ Session Restore Demo
  - Archive integrity verified ✓
  - Session restored successfully
  - All components recovered

✓ Hook System Integration Demo
  - 2 hooks registered
  - Events processed successfully
  - 5.2ms total execution time

🎉 All demos completed successfully!
```

## Step 9: Integration Checklist

### Screenshot 10: Integration Verification
```
✅ Installation verified
✅ Dependencies installed
✅ Session creation working
✅ Merge operations functional
✅ Split operations functional
✅ Archive system working
✅ Restore operations successful
✅ Hook system integrated
✅ Performance monitoring active
✅ Demo script completed

🎯 Ready for production use!
```

## Common Visual Patterns

### Success Indicators
- ✅ Green checkmarks for completed operations
- 📊 Blue charts for performance metrics
- 📁 Yellow folders for file operations
- 🎯 Purple targets for achieved goals

### Warning Indicators
- ⚠️ Yellow warnings for non-critical issues
- 🔴 Red alerts for errors
- 🔄 Blue spinners for operations in progress
- ❓ Blue question marks for missing information

### Action Icons
- ▶️ Play buttons to start operations
- ⏸️ Pause buttons for interrupted tasks
- 🔄 Refresh buttons for retries
- 💾 Save icons for persistence

---

**🎉 Congratulations! You've completed the visual tutorial.** You now have the skills to effectively use the session management system for your development workflow.

Need more help? Check out our [troubleshooting guide](./troubleshooting.md) or [FAQ](./faq.md).
