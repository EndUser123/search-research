#!/usr/bin/env python3
"""
Fix YouTube processor shutdown handler registration
"""

import re


def fix_youtube_processor_shutdown_handler():
    """Fix the shutdown handler registration in YouTube processor"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_processor.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find and replace the problematic shutdown handler registration
    old_pattern = r"""            # Create a proper resource handler object instead of passing the method directly
            from \.unified_shutdown_handler import ResourceCleanupHandler
            cleanup_handler = ResourceCleanupHandler\(
                cleanup_func=self\.cleanup,
                name="youtube_processor",
                priority=50
            \)
            self\.shutdown_handler\.register_resource\(cleanup_handler\)"""

    new_code = """            # Create a custom cleanup handler for YouTube processor
            from .unified_shutdown_handler import ResourceCleanupHandler

            class YouTubeProcessorCleanupHandler(ResourceCleanupHandler):
                def __init__(self, youtube_processor):
                    super().__init__("youtube_processor", priority=50)
                    self.youtube_processor = youtube_processor

                def cleanup(self, timeout: float = 5.0) -> bool:
                    \"\"\"Perform cleanup operation.\"\"\"
                    self.start_time = time.time()
                    try:
                        self.youtube_processor.cleanup()
                        self.end_time = time.time()
                        self.cleanup_successful = True
                        logger.info(f"YouTube processor cleaned up in {self.end_time - self.start_time:.2f}s")
                        return True
                    except Exception as e:
                        self.end_time = time.time()
                        self.cleanup_failed = True
                        self.last_error = str(e)
                        logger.error(f"Failed to cleanup YouTube processor: {e}")
                        return False

                def force_cleanup(self) -> bool:
                    \"\"\"Force cleanup operation.\"\"\"
                    self.start_time = time.time()
                    try:
                        self.youtube_processor.cleanup()
                        self.end_time = time.time()
                        self.cleanup_successful = True
                        logger.warning(f"YouTube processor force cleaned up in {self.end_time - self.start_time:.2f}s")
                        return True
                    except Exception as e:
                        self.end_time = time.time()
                        self.cleanup_failed = True
                        self.last_error = str(e)
                        logger.error(f"Failed to force cleanup YouTube processor: {e}")
                        return False

            cleanup_handler = YouTubeProcessorCleanupHandler(self)
            self.shutdown_handler.register_resource(cleanup_handler)"""

    # Replace the pattern
    new_content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE | re.DOTALL)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Fixed YouTube processor shutdown handler registration")
        return True
    else:
        print("❌ No changes made - pattern not found")
        return False


if __name__ == "__main__":
    fix_youtube_processor_shutdown_handler()
