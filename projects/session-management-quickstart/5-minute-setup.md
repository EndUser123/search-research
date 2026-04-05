# Session Management System - 5-Minute Quick Start

Get started with the modular session management system in under five minutes. This guide covers the essential setup steps for immediate use.

## Prerequisites

- Python 3.8 or higher
- Working Python environment (pip, virtual environment recommended)

## Step 1: Installation (1 minute)

```bash
# Clone or download the session management system
cd path/to/csf-nip

# Install dependencies
pip install -r requirements.txt

# Navigate to session management module
cd src/modules/session_management/hooks
```

## Step 2: Basic Session Operations (2 minutes)

The system provides four core session operations: merge, split, archive, and restore.

### Create Your First Session

```python
from session_management_hook_events import SessionManagementHookSystem

# Initialize the system
session_system = SessionManagementHookSystem()

# Create a basic session
my_session = {
    "session_id": "my_first_session",
    "user_id": "user_123",
    "context": {
        "workspace": "my_project",
        "current_task": "learning_session_management",
        "chat_history": []
    },
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "task_count": 0
    }
}
```

### Merge Sessions

```python
from session_management_hook_events import SessionMergeEvent, SessionMergeStrategy

# Create merge event
merge_event = session_system.create_session_merge_event(
    primary_session=my_session,
    merge_sessions=[other_session1, other_session2],
    merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY
)

# Execute merge (async)
results = await session_system.execute_session_merge(merge_event)
```

### Archive Sessions

```python
from session_management_hook_events import SessionArchiveEvent

# Create archive event
archive_event = session_system.create_session_archive_event(
    session_data=my_session,
    archive_options={
        "compress": True,
        "retention_days": 30
    }
)

# Execute archive (async)
results = await session_system.execute_session_archive(archive_event)
```

## Step 3: Quick Test (1 minute)

Run the demo to verify everything works:

```bash
python demo_session_management.py
```

Expected output:
```
Session Management Demo Started
✓ Merge functionality working
✓ Split functionality working
✓ Archive functionality working
✓ Restore functionality working
✓ Hook system integration working
Demo completed successfully!
```

## Step 4: Key Configuration (30 seconds)

Customize the system with these essential settings:

```python
config = {
    "archive_storage_path": "/path/to/your/archives",
    "max_concurrent_hooks": 10,
    "default_timeout": 30.0,
    "compression_level": 6
}

session_system = SessionManagementHookSystem(config)
```

## Essential Commands Cheat Sheet

| Operation | Command | Example |
|-----------|---------|---------|
| Initialize | `SessionManagementHookSystem()` | `system = SessionManagementHookSystem()` |
| Merge sessions | `create_session_merge_event()` | `event = system.create_session_merge_event(primary, sessions)` |
| Split sessions | `create_session_split_event()` | `event = system.create_session_split_event(session, criteria)` |
| Archive sessions | `create_session_archive_event()` | `event = system.create_session_archive_event(data)` |
| Restore sessions | `create_session_restore_event()` | `event = system.create_session_restore_event(path)` |

## Next Steps

- 📖 Read the [comprehensive documentation](./README.md)
- 🔧 Explore the [command reference](./command-reference.md)
- 🎥 Watch the [2-minute overview video](./video-script.md)
- ❓ Check the [FAQ](./faq.md)
- 🐛 Troubleshoot with the [quick reference](./troubleshooting.md)

## Need Help?

- Check the [troubleshooting guide](./troubleshooting.md) for common issues
- Review the [FAQ](./faq.md) for frequently asked questions
- Run the demo to verify installation: `python demo_session_management.py`

**You're now ready to use the session management system!** 🎉

---

*This quick start covers the essentials. For detailed configuration, advanced features, and best practices, see the full documentation.*
