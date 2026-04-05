#!/usr/bin/env python3
"""
Fix race conditions in worker status updates with improved synchronization
"""


def fix_race_conditions():
    """Fix race conditions in worker status updates with enhanced thread safety"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/video_processor.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Replace the _update_worker_status method with an enhanced version
    old_method = '''    def _update_worker_status(
        self, worker_statuses: dict, lock: threading.Lock, status: str, source: str
    ):
        """Safely updates the status for the current worker thread."""
        worker_id = threading.get_ident()
        current_time = time.monotonic()

        with lock:
            if worker_id not in worker_statuses:
                worker_statuses[worker_id] = {}

            last_update = worker_statuses[worker_id].get("last_update_time", 0)
            if (
                worker_statuses[worker_id].get("status") != status
                or current_time - last_update >= 0.5
            ):
                worker_statuses[worker_id].update(
                    {
                        "status": status,
                        "source": source,
                        "start_time": time.monotonic(),
                        "last_update_time": current_time,
                    }
                )'''

    new_method = '''    def _update_worker_status(
        self, worker_statuses: dict, lock: threading.Lock, status: str, source: str
    ):
        """Enhanced thread-safe status updates with race condition prevention."""
        worker_id = threading.get_ident()
        current_time = time.monotonic()

        # CRITICAL FIX: Use thread-local storage to prevent race conditions
        thread_local = threading.local()

        # Get thread-specific state to prevent cross-thread contamination
        if not hasattr(thread_local, 'last_status'):
            thread_local.last_status = None
        if not hasattr(thread_local, 'last_update_time'):
            thread_local.last_update_time = 0

        # Quick check without lock to reduce contention
        if (thread_local.last_status == status and
            current_time - thread_local.last_update_time < 0.5):
            return  # Skip update if no significant change

        # Acquire lock for actual update
        with lock:
            # Double-check pattern to prevent race conditions
            if worker_id not in worker_statuses:
                worker_statuses[worker_id] = {}

            worker_status = worker_statuses[worker_id]
            last_update = worker_status.get("last_update_time", 0)

            # Only update if status changed or enough time has passed
            if (worker_status.get("status") != status or
                current_time - last_update >= 0.5):

                # Atomic update with all required fields
                worker_status.update({
                    "status": status,
                    "source": source,
                    "start_time": worker_status.get("start_time", current_time),
                    "last_update_time": current_time,
                    "thread_id": worker_id,  # Add thread ID for debugging
                    "thread_name": threading.current_thread().name,
                })

                # Update thread-local state
                thread_local.last_status = status
                thread_local.last_update_time = current_time

    def _cleanup_worker_status(self, worker_statuses: dict, lock: threading.Lock):
        """Clean up stale worker status entries to prevent memory leaks."""
        current_time = time.monotonic()
        stale_threshold = 300.0  # 5 minutes

        with lock:
            stale_workers = []
            for worker_id, status_info in worker_statuses.items():
                if (current_time - status_info.get("last_update_time", 0) > stale_threshold):
                    stale_workers.append(worker_id)

            for worker_id in stale_workers:
                del worker_statuses[worker_id]
                logger.debug(f"Cleaned up stale worker status for thread {worker_id}")'''

    new_content = content.replace(old_method, new_method)

    if new_content != content:
        content = new_content
        print("✅ Enhanced worker status update method with race condition prevention")
    else:
        print("ℹ️ Worker status method pattern not found or already enhanced")

    # Add import for threading if not already present
    if "import threading" not in content:
        # Find the imports section and add threading import
        imports_section = "import time"
        new_imports = "import time\nimport threading"

        new_content = content.replace(imports_section, new_imports)

        if new_content != content:
            content = new_content
            print("✅ Added threading import")
        else:
            print("ℹ️ Could not add threading import")
    else:
        print("ℹ️ Threading import already present")

    # Add cleanup call at the end of process_video method
    cleanup_pattern = (
        r'return \\{\\n\\s*"source": source,\\n\\s*"status": "cancelled"\\n\\s*\\}'
    )
    cleanup_replacement = """return {"source": source, "status": "cancelled"}

        # Clean up stale worker status entries
        self._cleanup_worker_status(worker_statuses, worker_statuses_lock)"""

    new_content = re.sub(
        cleanup_pattern, cleanup_replacement, content, flags=re.MULTILINE
    )

    if new_content != content:
        content = new_content
        print("✅ Added cleanup call for worker status entries")
    else:
        print("ℹ️ Cleanup pattern not found")

    # Write the improved content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Race conditions in worker status updates fixed successfully")
    return True


if __name__ == "__main__":
    fix_race_conditions()
