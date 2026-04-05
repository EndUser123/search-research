# Session Management System - Troubleshooting Quick Reference

Fast solutions for common issues. Find your problem and follow the step-by-step fix.

## 🚨 Quick Diagnostics

Run this diagnostic script first:

```python
# quick_diagnostic.py - Run this to check system health
import sys
import os
from pathlib import Path

def run_diagnostics():
    print("🔍 Session Management System Diagnostics\n")

    # Check Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")

    # Check module imports
    try:
        from session_management_hook_events import SessionManagementHookSystem
        print("✅ Core modules imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Test basic functionality
    try:
        system = SessionManagementHookSystem()
        print("✅ System initialization successful")

        # Test session creation
        test_session = {
            "session_id": "test_diagnostic",
            "user_id": "diagnostic_user",
            "context": {},
            "metadata": {}
        }

        # Test archive creation
        from session_management_hook_events import SessionArchiveEvent
        event = system.create_session_archive_event(test_session)
        print("✅ Event creation successful")

    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

    print("\n🎉 All diagnostics passed!")
    return True

if __name__ == "__main__":
    run_diagnostics()
```

---

## Installation Issues

### Problem: ModuleNotFoundError when importing

**Symptoms:**
```
ModuleNotFoundError: No module named 'session_management_hook_events'
ImportError: cannot import name 'SessionManagementHookSystem'
```

**Quick Fix:**
```bash
# 1. Verify you're in the right directory
cd /path/to/csf-nip/src/modules/session_management/hooks

# 2. Add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/csf-nip/src"

# 3. Try importing again
python -c "from session_management_hook_events import SessionManagementHookSystem; print('✅ Import successful')"
```

**Alternative Fix:**
```python
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from session_management_hook_events import SessionManagementHookSystem
```

### Problem: Dependencies not installed

**Symptoms:**
```
ImportError: No module named 'modules.orchestration.hook_system'
ImportError: No module named 'asyncio'
```

**Quick Fix:**
```bash
# Install dependencies
pip install -r requirements.txt

# If no requirements file, install common dependencies
pip install asyncio pathlib dataclasses enum typing

# For development/testing
pip install pytest pytest-asyncio
```

---

## Session Creation Issues

### Problem: Session validation fails

**Symptoms:**
```
ValueError: Primary session is required for merge operation
ValueError: Session data missing required 'session_id' field
```

**Quick Fix:**
```python
# Ensure required fields are present
def create_valid_session():
    return {
        "session_id": "unique_session_id",  # REQUIRED: Must be non-empty string
        "user_id": "user_123",              # REQUIRED: Must be non-empty string
        "context": {                        # REQUIRED: Must be dict
            "workspace": "my_project",
            "active_files": []
        },
        "metadata": {                       # REQUIRED: Must be dict
            "created_at": datetime.now().isoformat(),
            "task_count": 0
        }
    }

# Validate before using
from session_merge_utils import validate_session_structure
session = create_valid_session()
try:
    validate_session_structure(session)
    print("✅ Session is valid")
except ValueError as e:
    print(f"❌ Session validation failed: {e}")
```

### Problem: Session IDs conflict

**Symptoms:**
```
Merge operation fails with duplicate session IDs
Archive overwrites existing files
```

**Quick Fix:**
```python
import uuid
from datetime import datetime

def generate_unique_session_id():
    """Generate unique session ID with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"

# Usage
session_id = generate_unique_session_id()
print(f"Unique session ID: {session_id}")
```

---

## Merge Operation Issues

### Problem: Merge operation hangs or times out

**Symptoms:**
```
Operation takes >30 seconds
TimeoutError or asyncio.TimeoutError
```

**Quick Fix:**
```python
# Increase timeout or reduce session size
config = {
    "default_timeout": 60.0,  # Increase from default 30s
    "max_concurrent_hooks": 5  # Reduce if system is busy
}

system = SessionManagementHookSystem(config)

# Or split large merges into smaller operations
def batch_merge(primary, sessions, batch_size=3):
    """Merge sessions in batches to avoid timeouts"""
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i:i + batch_size]
        print(f"Merging batch {i//batch_size + 1}: {len(batch)} sessions")
        # Perform merge on this batch
        yield batch
```

### Problem: Merge conflicts not resolved

**Symptoms:**
```
Data inconsistencies after merge
Primary session data lost
```

**Quick Fix:**
```python
# Choose appropriate conflict resolution strategy
strategies = {
    "primary_wins": "Primary session data takes precedence",
    "merge_all": "Combine all data, primary wins on conflicts",
    "timestamp_priority": "Most recent data wins conflicts"
}

# Use merge_all to preserve all data
merge_event = system.create_session_merge_event(
    primary_session=primary,
    merge_sessions=to_merge,
    conflict_resolution="merge_all"  # Better than primary_wins for preserving data
)

# Or use CONTEXT_PRIORITY strategy
merge_event = system.create_session_merge_event(
    primary_session=primary,
    merge_sessions=to_merge,
    merge_strategy=SessionMergeStrategy.CONTEXT_PRIORITY
)
```

---

## Archive Issues

### Problem: Archive creation fails

**Symptoms:**
```
FileNotFoundError: Archive directory not found
PermissionError: Cannot write to archive location
```

**Quick Fix:**
```python
# Check and create archive directory
import os
from pathlib import Path

def ensure_archive_directory(path="/tmp/csf_nip_session_archives"):
    archive_path = Path(path)
    try:
        archive_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Archive directory ready: {archive_path}")
        return archive_path
    except PermissionError:
        print(f"❌ Permission denied for: {archive_path}")
        print("Try creating archive in user directory:")
        user_archive = Path.home() / "csf_nip_archives"
        return ensure_archive_directory(str(user_archive))

# Use the ensured directory
archive_path = ensure_archive_directory()
```

### Problem: Compression fails or is too slow

**Symptoms:**
```
Compression takes >10 seconds
MemoryError during compression
```

**Quick Fix:**
```python
# Adjust compression settings
archive_options = {
    "compress": True,
    "compression_level": 3,  # Lower level for faster compression (1-9)
    "min_size_threshold": 10240  # Only compress files >10KB
}

# Or disable compression for small sessions
if session_size_bytes < 1000:
    archive_options["compress"] = False
    print("Skipping compression for small session")

# Check available memory
import psutil
available_memory_gb = psutil.virtual_memory().available / (1024**3)
if available_memory_gb < 1:
    print("⚠️ Low memory detected, reducing compression")
    archive_options["compression_level"] = 1
```

---

## Restore Issues

### Problem: Archive restore fails

**Symptoms:**
```
FileNotFoundError: Archive file not found
IntegrityError: Archive corrupted
gzip.BadGzipFile: Not a gzipped file
```

**Quick Fix:**
```python
def safe_restore_archive(archive_path):
    """Safely restore with integrity checks"""
    archive_path = Path(archive_path)

    # Check if file exists
    if not archive_path.exists():
        print(f"❌ Archive not found: {archive_path}")
        return None

    # Check file size
    if archive_path.stat().st_size == 0:
        print(f"❌ Archive file is empty: {archive_path}")
        return None

    try:
        # Test decompression
        from session_management_hook_events import decompress_session_data
        with open(archive_path, 'rb') as f:
            compressed_data = f.read()

        restored_data = decompress_session_data(compressed_data)
        print(f"✅ Archive integrity verified: {archive_path}")
        return restored_data

    except Exception as e:
        print(f"❌ Archive restore failed: {e}")
        print(f"Archive: {archive_path}")
        return None

# Usage
restored_session = safe_restore_archive("/path/to/archive.json.gz")
```

### Problem: Partial restore needed

**Symptoms:**
```
Need only certain parts of large archive
Restore takes too long for full session
```

**Quick Fix:**
```python
# Configure partial restore
restore_options = {
    "partial_restore": True,
    "restore_components": ["context"],  # Only restore context
    # Options: ["context", "metadata", "chat_history", "environment", "files"]
}

restore_event = system.create_session_restore_event(
    archive_path=archive_path,
    restore_options=restore_options
)

# Or extract specific data manually
def extract_session_component(archive_path, component="context"):
    """Extract only specific component from archive"""
    try:
        with open(archive_path, 'rb') as f:
            compressed_data = f.read()

        full_session = decompress_session_data(compressed_data)
        return full_session.get(component, {})

    except Exception as e:
        print(f"Failed to extract {component}: {e}")
        return {}

# Usage
context_only = extract_session_component(archive_path, "context")
```

---

## Performance Issues

### Problem: System is slow

**Symptoms:**
```
Operations take >1 second
High CPU/memory usage
```

**Quick Fix:**
```python
# Optimize configuration
config = {
    "max_concurrent_hooks": min(20, (os.cpu_count() or 1) * 2),
    "default_timeout": 15.0,  # Shorter timeout
    "enable_performance_tracking": True  # Monitor bottlenecks
}

# Monitor performance
def analyze_performance():
    status = system.get_session_management_status()
    metrics = status['performance_metrics']

    print("Performance Analysis:")
    for op_type, data in metrics.items():
        if data['count'] > 0:
            avg_time = data['avg_time']
            if avg_time > 0.5:  # Slow operations
                print(f"⚠️ {op_type}: {avg_time:.3f}s average (slow)")
            else:
                print(f"✅ {op_type}: {avg_time:.3f}s average")

# Call this periodically
analyze_performance()
```

### Problem: Memory usage too high

**Symptoms:**
```
MemoryError: Unable to allocate memory
System becomes unresponsive
```

**Quick Fix:**
```python
# Monitor memory usage
import psutil

def check_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024

    print(f"Memory usage: {memory_mb:.1f} MB")

    if memory_mb > 1000:  # More than 1GB
        print("⚠️ High memory usage detected")
        print("Solutions:")
        print("  1. Archive completed sessions")
        print("  2. Reduce session history size")
        print("  3. Use partial restores")
        return False
    return True

# Archive old sessions to free memory
def cleanup_old_sessions(days_old=7):
    """Archive sessions older than specified days"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days_old)
    old_sessions = []  # Get your old sessions here

    for session in old_sessions:
        if datetime.fromisoformat(session['metadata']['created_at']) < cutoff_date:
            print(f"Archiving old session: {session['session_id']}")
            # Archive the session
```

---

## Async Issues

### Problem: Async/await errors

**Symptoms:**
```
RuntimeError: You cannot await this coroutine
TypeError: object NoneType can't be used in 'await' expression
```

**Quick Fix:**
```python
# Common async patterns

# 1. Correct way to call async functions
async def main():
    # Create system
    system = SessionManagementHookSystem()

    # Create event
    merge_event = system.create_session_merge_event(primary, sessions)

    # Execute async operation
    results = await system.execute_session_merge(merge_event)
    return results

# Run the async function
import asyncio
results = asyncio.run(main())

# 2. In existing async code, just await
async def existing_async_function():
    system = SessionManagementHookSystem()
    archive_event = system.create_session_archive_event(session)
    results = await system.execute_session_archive(archive_event)
    return results

# 3. For multiple operations
async def batch_operations():
    system = SessionManagementHookSystem()

    tasks = []
    for session in sessions_to_archive:
        event = system.create_session_archive_event(session)
        task = system.execute_session_archive(event)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

---

## Environment Issues

### Problem: Path issues

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory
Permission denied when accessing files
```

**Quick Fix:**
```python
# Use absolute paths
from pathlib import Path

def get_safe_paths():
    # Get current script directory
    script_dir = Path(__file__).parent

    # Create safe paths
    archive_dir = script_dir / "archives"
    temp_dir = script_dir / "temp"
    log_dir = script_dir / "logs"

    # Ensure directories exist
    for dir_path in [archive_dir, temp_dir, log_dir]:
        dir_path.mkdir(exist_ok=True)

    return {
        "archive_dir": archive_dir.absolute(),
        "temp_dir": temp_dir.absolute(),
        "log_dir": log_dir.absolute()
    }

# Use safe paths in configuration
paths = get_safe_paths()
config = {
    "archive_storage_path": str(paths["archive_dir"])
}
```

### Problem: Windows vs Unix path issues

**Symptoms:**
```
Path works on one OS but not another
File not found on different operating systems
```

**Quick Fix:**
```python
from pathlib import Path
import platform

def get_cross_platform_path(relative_path):
    """Get platform-agnostic path"""
    base_path = Path(__file__).parent
    return (base_path / relative_path).resolve()

# Usage regardless of OS
config_path = get_cross_platform_path("config.json")
archive_path = get_cross_platform_path("../archives")

# Check OS for specific handling
if platform.system() == "Windows":
    # Windows-specific handling
    pass
elif platform.system() in ["Linux", "Darwin"]:
    # Unix-specific handling
    pass
```

---

## 🆘 Emergency Procedures

### System completely unresponsive

```python
# 1. Force reset system
def emergency_reset():
    """Emergency system reset"""
    import gc
    gc.collect()  # Force garbage collection

    # Create fresh system instance
    system = SessionManagementHookSystem({
        "max_concurrent_hooks": 1,  # Reduce load
        "default_timeout": 5.0      # Short timeout
    })
    return system

# 2. Check system health
def emergency_health_check():
    status = system.get_session_management_status()
    print(f"Archived sessions: {status['archived_sessions']}")
    print(f"Operation history: {status['operation_history_size']}")

    # Check if responding
    try:
        test_session = {"session_id": "emergency_test", "user_id": "test", "context": {}, "metadata": {}}
        event = system.create_session_archive_event(test_session)
        print("✅ System responding")
        return True
    except Exception as e:
        print(f"❌ System not responding: {e}")
        return False
```

### Data corruption suspected

```python
# Verify all archived sessions
def verify_all_archives(archive_dir):
    """Verify integrity of all archives"""
    archive_path = Path(archive_dir)
    corrupted = []

    for archive_file in archive_path.glob("*.json.gz"):
        try:
            with open(archive_file, 'rb') as f:
                compressed_data = f.read()

            # Test decompression
            decompress_session_data(compressed_data)

        except Exception as e:
            print(f"❌ Corrupted archive: {archive_file} - {e}")
            corrupted.append(archive_file)

    if corrupted:
        print(f"Found {len(corrupted)} corrupted archives")
        return False
    else:
        print("✅ All archives verified")
        return True
```

---

## 📞 Getting More Help

If these solutions don't work:

1. **Run the diagnostic script** at the top of this guide
2. **Check the logs** for detailed error messages
3. **Review the FAQ** for common questions
4. **Create a minimal reproducible example** of your issue
5. **Consult the command reference** for correct syntax

**Before asking for help, please provide:**
- Exact error message
- Code that causes the issue
- System information (Python version, OS)
- What you've already tried

---

**💡 Pro Tip**: Most issues are resolved by:
1. Checking file paths and permissions
2. Verifying session structure
3. Using proper async/await syntax
4. Ensuring required fields are present

This guide covers 95% of common issues. For edge cases or specific problems, check the full documentation or community forums.
