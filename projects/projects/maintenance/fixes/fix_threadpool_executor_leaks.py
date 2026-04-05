#!/usr/bin/env python3
"""
Fix ThreadPoolExecutor resource leaks by improving cleanup
"""


def fix_threadpool_executor_leaks():
    """Fix ThreadPoolExecutor resource leaks with enhanced cleanup"""

    file_path = (
        "C:/_Python/_Projects/ai_studio/src/ai_studio/unified_shutdown_handler.py"
    )

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Replace the cleanup method with enhanced version
    old_cleanup = """    def cleanup(self, timeout: float = 3.0) -> bool:
        \"\"\"Gracefully shutdown the executor.\"\"\"
        self.start_time = time.time()
        try:
            # Cancel pending futures if available
            if hasattr(self.executor, '_futures') and hasattr(self.executor, '_cancel_futures_impl'):
                self.executor._cancel_futures_impl()

            # Shutdown with wait=False to prevent blocking
            self.executor.shutdown(wait=False, cancel_futures=True)

            # Clear thread references
            if hasattr(self.executor, '_threads'):
                self.executor._threads.clear()

            self.end_time = time.time()
            self.cleanup_successful = True
            logger.info(f"Executor {self.name} shut down in {self.end_time - self.start_time:.2f}s")
            return True

        except Exception as e:
            self.end_time = time.time()
            self.cleanup_failed = True
            self.last_error = str(e)
            logger.error(f"Failed to cleanup executor {self.name}: {e}")
            return False"""

    new_cleanup = """    def cleanup(self, timeout: float = 3.0) -> bool:
        \"\"\"Gracefully shutdown the executor with enhanced resource cleanup.\"\"\"
        self.start_time = time.time()
        try:
            # Cancel pending futures if available
            if hasattr(self.executor, '_futures') and hasattr(self.executor, '_cancel_futures_impl'):
                self.executor._cancel_futures_impl()

            # Enhanced: Wait for graceful shutdown with timeout
            shutdown_timeout = min(timeout, 2.0)  # Use at most 2 seconds for graceful shutdown

            # Try graceful shutdown first
            try:
                self.executor.shutdown(wait=shutdown_timeout, cancel_futures=True)
                logger.debug(f"Executor {self.name} graceful shutdown completed")
            except Exception as graceful_error:
                logger.warning(f"Graceful shutdown failed for {self.name}: {graceful_error}")
                # Fallback to immediate shutdown
                self.executor.shutdown(wait=False, cancel_futures=True)

            # Enhanced: Check and clean up thread references more thoroughly
            if hasattr(self.executor, '_threads'):
                threads_to_check = list(self.executor._threads)
                alive_threads = []

                for thread in threads_to_check:
                    try:
                        if thread.is_alive():
                            alive_threads.append(thread)
                            # Give threads a chance to terminate gracefully
                            thread.join(timeout=0.1)
                            if thread.is_alive():
                                logger.warning(f"Thread {thread.name} in executor {self.name} did not terminate gracefully")
                    except Exception as thread_error:
                        logger.debug(f"Error checking thread {thread.name}: {thread_error}")

                # Clear thread references only after checking
                self.executor._threads.clear()

                if alive_threads:
                    logger.info(f"Executor {self.name} had {len(alive_threads)} threads that required cleanup")

            self.end_time = time.time()
            self.cleanup_successful = True
            logger.info(f"Executor {self.name} shut down in {self.end_time - self.start_time:.2f}s")
            return True

        except Exception as e:
            self.end_time = time.time()
            self.cleanup_failed = True
            self.last_error = str(e)
            logger.error(f"Failed to cleanup executor {self.name}: {e}")
            return False"""

    new_content = content.replace(old_cleanup, new_cleanup)

    # Also enhance the force_cleanup method
    old_force_cleanup = """    def force_cleanup(self) -> bool:
        \"\"\"Force shutdown the executor immediately.\"\"\"
        self.start_time = time.time()
        try:
            for attempt in range(3):
                try:
                    self.executor.shutdown(wait=False, cancel_futures=True)
                    if hasattr(self.executor, '_threads'):
                        self.executor._threads.clear()
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(0.1)

            self.end_time = time.time()
            self.cleanup_successful = True
            logger.warning(f"Executor {self.name} force terminated in {self.end_time - self.start_time:.2f}s")
            return True

        except Exception as e:
            self.end_time = time.time()
            self.cleanup_failed = True
            self.last_error = str(e)
            logger.error(f"Failed to force cleanup executor {self.name}: {e}")
            return False"""

    new_force_cleanup = """    def force_cleanup(self) -> bool:
        \"\"\"Force shutdown the executor immediately with enhanced cleanup.\"\"\"
        self.start_time = time.time()
        try:
            # Cancel all futures first
            if hasattr(self.executor, '_futures') and hasattr(self.executor, '_cancel_futures_impl'):
                try:
                    self.executor._cancel_futures_impl()
                except Exception as cancel_error:
                    logger.debug(f"Future cancellation failed: {cancel_error}")

            # Force shutdown with multiple attempts
            for attempt in range(3):
                try:
                    self.executor.shutdown(wait=False, cancel_futures=True)

                    # Enhanced: Check if threads are still alive and terminate them
                    if hasattr(self.executor, '_threads'):
                        for thread in list(self.executor._threads):
                            try:
                                if thread.is_alive():
                                    # Try to interrupt the thread
                                    if hasattr(thread, '_thread_id'):
                                        import ctypes
                                        import threading
                                        tid = ctypes.c_long(thread.ident)
                                        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
                                        if res == 0:
                                            logger.debug(f"Successfully sent async exception to thread {thread.name}")
                                        elif res > 1:
                                            logger.warning(f"Failed to send async exception to thread {thread.name}")
                                            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                            except Exception as thread_term_error:
                                logger.debug(f"Thread termination failed: {thread_term_error}")

                        self.executor._threads.clear()
                    break
                except Exception as shutdown_error:
                    if attempt == 2:
                        logger.error(f"Force shutdown failed after 3 attempts for {self.name}: {shutdown_error}")
                        raise
                    logger.debug(f"Force shutdown attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.05)  # Short retry delay

            self.end_time = time.time()
            self.cleanup_successful = True
            logger.warning(f"Executor {self.name} force terminated in {self.end_time - self.start_time:.2f}s")
            return True

        except Exception as e:
            self.end_time = time.time()
            self.cleanup_failed = True
            self.last_error = str(e)
            logger.error(f"Failed to force cleanup executor {self.name}: {e}")
            return False"""

    final_content = new_content.replace(old_force_cleanup, new_force_cleanup)

    if final_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        print("✅ Enhanced ThreadPoolExecutor cleanup to prevent resource leaks")
        return True
    else:
        print("❌ No changes made - cleanup may already be enhanced")
        return False


if __name__ == "__main__":
    fix_threadpool_executor_leaks()
