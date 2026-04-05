# Interactive Getting Started Guide

Follow along with these working examples to learn the session management system through hands-on practice. Each example builds on the previous ones.

## 🚀 Quick Start: Run These Examples

Open your Python environment and try each example step by step. All code is ready to copy and run.

---

## Example 1: Your First Session (2 minutes)

```python
# Run this in your Python environment
from session_management_hook_events import SessionManagementHookSystem
from datetime import datetime

# Initialize the system
print("🔧 Initializing Session Management System...")
system = SessionManagementHookSystem()

# Create your first session
my_first_session = {
    "session_id": "demo_session_001",
    "user_id": "learning_user",
    "context": {
        "workspace": "getting_started",
        "current_task": "learning_session_management",
        "active_files": ["interactive_guide.py"],
        "chat_history": [
            {"role": "user", "content": "I want to learn session management"},
            {"role": "assistant", "content": "Great! Let's start with the basics"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 1,
        "duration": 0.0
    }
}

print("✅ Session created!")
print(f"📋 Session ID: {my_first_session['session_id']}")
print(f"👤 User: {my_first_session['user_id']}")
print(f"📁 Workspace: {my_first_session['context']['workspace']}")

# Expected output:
# 🔧 Initializing Session Management System...
# ✅ Session created!
# 📋 Session ID: demo_session_001
# 👤 User: learning_user
# 📁 Workspace: getting_started
```

**🎯 Your Task**: Modify the session to include your own username and workspace name.

---

## Example 2: Creating Multiple Sessions (3 minutes)

```python
# Create three related sessions for a project
research_session = {
    "session_id": "research_session_002",
    "user_id": "learning_user",
    "context": {
        "workspace": "web_project",
        "current_task": "api_research",
        "findings": [
            "REST API is best for this project",
            "JWT for authentication",
            "PostgreSQL for database"
        ],
        "chat_history": [
            {"role": "user", "content": "Research API options"},
            {"role": "assistant", "content": "Based on requirements, REST is recommended"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 1
    }
}

development_session = {
    "session_id": "dev_session_003",
    "user_id": "learning_user",
    "context": {
        "workspace": "web_project",
        "current_task": "backend_implementation",
        "active_files": ["api.py", "models.py", "auth.py"],
        "progress": "50% complete"
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 3
    }
}

testing_session = {
    "session_id": "test_session_004",
    "user_id": "learning_user",
    "context": {
        "workspace": "web_project",
        "current_task": "unit_testing",
        "test_files": ["test_api.py", "test_auth.py"],
        "coverage": "75%"
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 2
    }
}

sessions = [research_session, development_session, testing_session]

print("📚 Created multiple sessions:")
for session in sessions:
    print(f"  • {session['session_id']}: {session['context']['current_task']}")

# Your turn: Add a fourth session for documentation
```

**🎯 Your Task**: Create a fourth session called "documentation" and add it to the sessions list.

---

## Example 3: Merging Sessions (5 minutes)

```python
# Now let's merge these sessions into one unified session
from session_management_hook_events import SessionMergeEvent, SessionMergeStrategy

# Use the research session as primary
primary = research_session
merge_sessions = [development_session, testing_session]

print("🔗 Merging sessions...")

# Create merge event
merge_event = system.create_session_merge_event(
    primary_session=primary,
    merge_sessions=merge_sessions,
    merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY,
    conflict_resolution="primary_wins"
)

print(f"📊 Merge event created:")
print(f"  • Primary session: {primary['session_id']}")
print(f"  • Sessions to merge: {len(merge_sessions)}")
print(f"  • Strategy: {merge_event.merge_strategy.value}")

# Execute the merge
import asyncio

async def perform_merge():
    results = await system.execute_session_merge(merge_event)
    print("✅ Merge completed!")
    return results

# Run the merge
merge_results = asyncio.run(perform_merge())

print(f"📈 Results: {len(merge_results)} hook executions")
```

**🎯 Your Task**: Try the merge again with a different strategy (TIME_BASED or TASK_TYPE) and compare results.

---

## Example 4: Splitting a Complex Session (5 minutes)

```python
# Create a complex session with multiple task types
complex_session = {
    "session_id": "complex_session_005",
    "user_id": "learning_user",
    "context": {
        "workspace": "mobile_app_project",
        "chat_history": [
            {"role": "user", "content": "Design the app UI", "task_type": "design"},
            {"role": "assistant", "content": "Creating wireframes and mockups", "task_type": "design"},
            {"role": "user", "content": "Implement user authentication", "task_type": "development"},
            {"role": "assistant", "content": "Building authentication system", "task_type": "development"},
            {"role": "user", "content": "Write authentication tests", "task_type": "testing"},
            {"role": "assistant", "content": "Creating comprehensive test suite", "task_type": "testing"},
            {"role": "user", "content": "Update API documentation", "task_type": "documentation"},
            {"role": "assistant", "content": "Documenting authentication endpoints", "task_type": "documentation"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 4,
        "duration": 240.0  # 4 hours
    }
}

print("📱 Complex session created with mixed task types")
print(f"📊 Total tasks: {len([msg for msg in complex_session['context']['chat_history'] if 'task_type' in msg])}")

# Now split it by task type
from session_management_hook_events import SessionSplitEvent, SessionSplitCriteria

split_event = system.create_session_split_event(
    source_session=complex_session,
    split_criteria=SessionSplitCriteria.BY_TASK_TYPE
)

print("✂️ Splitting session by task type...")

async def perform_split():
    results = await system.execute_session_split(split_event)
    print("✅ Split completed!")
    return results

split_results = asyncio.run(perform_split())
print(f"📈 Split results: {len(split_results)} hooks executed")
```

**🎯 Your Task**: Create another complex session with different task types and split it using a different criterion (like BY_TIME_RANGE).

---

## Example 5: Archiving Sessions (4 minutes)

```python
# Archive one of our sessions to save space
from session_management_hook_events import SessionArchiveEvent

session_to_archive = complex_session  # Archive our complex session

print(f"💾 Archiving session: {session_to_archive['session_id']}")

# Calculate original size
import json
original_size = len(json.dumps(session_to_archive, default=str).encode('utf-8'))
print(f"📏 Original size: {original_size:,} bytes")

# Create archive event
archive_event = system.create_session_archive_event(
    session_data=session_to_archive,
    archive_options={
        "compress": True,
        "compression_level": 6,
        "retention_days": 30,
        "validate_integrity": True,
        "create_backup": True
    }
)

print("🗜️ Archive configuration:")
print(f"  • Compression: Enabled (level 6)")
print(f"  • Retention: 30 days")
print(f"  • Integrity check: Enabled")

# Execute archive
async def perform_archive():
    results = await system.execute_session_archive(archive_event)
    print("✅ Archive completed!")
    return results

archive_results = asyncio.run(perform_archive())

# Show compression results
estimated_size = archive_event.get_estimated_archive_size()
compression_ratio = (1 - estimated_size / original_size) * 100

print(f"📊 Compression results:")
print(f"  • Original: {original_size:,} bytes")
print(f"  • Estimated compressed: {estimated_size:,} bytes")
print(f"  • Compression ratio: {compression_ratio:.1f}%")
```

**🎯 Your Task**: Try different compression levels (1-9) and see how it affects size vs. speed.

---

## Example 6: System Status & Monitoring (3 minutes)

```python
# Check the system status and performance
print("📊 System Status Overview")

# Get comprehensive status
status = system.get_session_management_status()

print(f"🗄️ Archived sessions: {status['archived_sessions']}")
print(f"📋 Operation history: {status['operation_history_size']} operations")
print(f"📁 Archive storage: {status['archive_storage_path']}")

print("\n⚡ Performance Metrics:")
for op_type, metrics in status['performance_metrics'].items():
    if metrics['count'] > 0:
        print(f"  • {op_type}:")
        print(f"    - Count: {metrics['count']}")
        print(f"    - Average time: {metrics['avg_time']:.3f} seconds")
        print(f"    - Total time: {metrics['total_time']:.3f} seconds")

# Get recent operations
print(f"\n📈 Recent Operations (last 5):")
recent_ops = system.get_operation_history(limit=5)
for i, op in enumerate(recent_ops, 1):
    print(f"  {i}. {op['timestamp'][:19]} - {op['operation_type']}")
    print(f"     ✅ Success: {op['success_count']}/{op['hook_count']} hooks")
    if op.get('error'):
        print(f"     ❌ Error: {op['error']}")
```

**🎯 Your Task**: Perform a few more operations and check how the metrics change.

---

## Example 7: Error Handling & Validation (3 minutes)

```python
# Let's test error handling with invalid data
print("🛡️ Testing Error Handling and Validation")

# Test 1: Invalid session structure
invalid_session = {
    "session_id": "",  # Empty session_id should fail validation
    # Missing required fields
}

try:
    validation_event = system.create_session_merge_event(
        primary_session=invalid_session,
        merge_sessions=[],
        merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY
    )
    print("❌ Should have failed with empty session_id")
except ValueError as e:
    print(f"✅ Caught expected validation error: {str(e)[:50]}...")

# Test 2: Valid session but with conflicts
session_a = {
    "session_id": "conflict_test_a",
    "context": {"workspace": "project_x", "setting": "value_a"},
    "metadata": {"created_at": datetime.now().isoformat()}
}

session_b = {
    "session_id": "conflict_test_b",
    "context": {"workspace": "project_y", "setting": "value_b"},  # Different workspace
    "metadata": {"created_at": datetime.now().isoformat()}
}

print("\n🔄 Testing conflict resolution...")

try:
    conflict_event = system.create_session_merge_event(
        primary_session=session_a,
        merge_sessions=[session_b],
        conflict_resolution="primary_wins"  # Primary session wins
    )

    # Simulate execution
    print("✅ Conflict resolution strategy set successfully")
    print(f"  Strategy: {conflict_event.conflict_resolution}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")

# Test 3: Session structure validation
print("\n✅ Testing session validation...")
from session_merge_utils import validate_session_structure

valid_session = {
    "session_id": "valid_test",
    "user_id": "test_user",
    "context": {},
    "metadata": {}
}

try:
    validate_session_structure(valid_session)
    print("✅ Valid session passed validation")
except Exception as e:
    print(f"❌ Valid session failed: {e}")
```

**🎯 Your Task**: Create a session with missing required fields and see what validation errors you get.

---

## Example 8: Real-World Scenario (5 minutes)

```python
# Complete real-world workflow: Research → Development → Testing → Archive
print("🌍 Real-World Scenario: Building a Feature")

# Step 1: Research session
research_session = {
    "session_id": "feature_research_006",
    "user_id": "developer_123",
    "context": {
        "feature": "user_notification_system",
        "requirements": [
            "Email notifications",
            "Push notifications",
            "User preferences",
            "Delivery tracking"
        ],
        "research_links": ["https://docs.example.com/notifications"],
        "chat_history": [
            {"role": "user", "content": "Research notification systems"},
            {"role": "assistant", "content": "Found several approaches for notifications"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 1,
        "phase": "research"
    }
}

# Step 2: Development session
dev_session = {
    "session_id": "feature_dev_007",
    "user_id": "developer_123",
    "context": {
        "feature": "user_notification_system",
        "files": ["notification_service.py", "email_sender.py", "push_handler.py"],
        "progress": "80% complete",
        "tests_written": 12,
        "chat_history": [
            {"role": "user", "content": "Implement notification service"},
            {"role": "assistant", "content": "Created modular notification system"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 5,
        "phase": "development"
    }
}

# Step 3: Testing session
test_session = {
    "session_id": "feature_test_008",
    "user_id": "developer_123",
    "context": {
        "feature": "user_notification_system",
        "test_coverage": "95%",
        "automated_tests": True,
        "bugs_found": 2,
        "bugs_fixed": 2,
        "chat_history": [
            {"role": "user", "content": "Test the notification system thoroughly"},
            {"role": "assistant", "content": "Running comprehensive test suite"}
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 3,
        "phase": "testing"
    }
}

print("📋 Feature development lifecycle:")
for session in [research_session, dev_session, test_session]:
    phase = session['metadata']['phase']
    progress = session['context'].get('progress', session['context'].get('test_coverage', 'Research'))
    print(f"  • {phase.title()}: {progress}")

# Step 4: Archive the completed feature
feature_session = {
    "session_id": "feature_complete_009",
    "user_id": "developer_123",
    "context": {
        "feature": "user_notification_system",
        "status": "completed",
        "merged_sessions": [s['session_id'] for s in [research_session, dev_session, test_session]],
        "deliverables": [
            "Notification service implemented",
            "95% test coverage achieved",
            "All bugs resolved",
            "Documentation updated"
        ]
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "total_tasks": 9,
        "completion_time": "3 days",
        "phase": "completed"
    }
}

# Archive the completed feature
archive_event = system.create_session_archive_event(
    session_data=feature_session,
    archive_options={
        "compress": True,
        "retention_days": 365,  # Keep for a year
        "validate_integrity": True
    }
)

print(f"\n💾 Archiving completed feature: {feature_session['context']['feature']}")
print(f"📦 Total tasks completed: {feature_session['metadata']['total_tasks']}")
print(f"⏱️ Completion time: {feature_session['metadata']['completion_time']}")
print(f"📅 Retention: 365 days")

# Simulate archive execution
estimated_size = archive_event.get_estimated_archive_size()
print(f"📊 Estimated archive size: {estimated_size:,} bytes")

print("\n🎉 Feature lifecycle complete!")
```

**🎯 Your Task**: Create your own real-world scenario for a feature or project you're working on.

---

## 🏆 Challenge Exercise

Now put everything together! Complete this challenge to test your skills:

```python
# CHALLENGE: Create a complete session workflow
# Your task:
# 1. Create 3 different sessions for different aspects of a project
# 2. Merge two sessions together
# 3. Split the merged session by some criteria
# 4. Archive one session
# 5. Check the system status and report your results

print("🏆 CHALLENGE: Complete Session Workflow")
print("Create your own project workflow using all operations learned")

# Your code here...
```

---

## ✅ What You've Learned

- **Session Creation**: Structured data with context and metadata
- **Session Merging**: Combining multiple sessions intelligently
- **Session Splitting**: Breaking complex sessions into focused parts
- **Session Archiving**: Compressing and storing completed work
- **Error Handling**: Validating data and handling conflicts
- **System Monitoring**: Tracking performance and operations
- **Real-world Application**: Complete project lifecycle management

## 🎯 Next Steps

1. **Practice** with your own project data
2. **Explore** advanced features in the [command reference](./command-reference.md)
3. **Watch** the [2-minute overview video](./video-script.md)
4. **Troubleshoot** any issues with the [quick reference](./troubleshooting.md)

---

**🎉 Congratulations!** You've completed the interactive guide. You now have hands-on experience with the session management system and are ready to use it in your projects.

Need help? Check our [FAQ](./faq.md) or [troubleshooting guide](./troubleshooting.md).
