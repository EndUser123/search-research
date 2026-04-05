#!/usr/bin/env python3
"""CHS Singleton Pattern to Prevent GPU Exhaustion
Ensures only one ChatHistorySearcher instance exists to prevent GPU memory bloat.
"""

import sys
import threading
import weakref
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))


class CHSSingleton:
    """Singleton manager for ChatHistorySearcher to prevent GPU memory exhaustion."""

    _instance = None
    _lock = threading.Lock()
    _weak_ref = None
    _init_count = 0

    @classmethod
    def get_instance(cls, enable_rag: bool = True, **kwargs):
        """Get the singleton ChatHistorySearcher instance."""
        if cls._instance is not None and cls._weak_ref is not None:
            # Check if the instance is still alive
            instance = cls._weak_ref()
            if instance is not None:
                cls._init_count += 1
                return instance
            else:
                # Reference died, clean up
                cls._instance = None
                cls._weak_ref = None

        with cls._lock:
            if cls._instance is None:
                try:
                    from src.modules.analysis.chat_search.src.chat_history_search import (
                        ChatHistorySearcher,
                    )
                    cls._instance = ChatHistorySearcher(enable_rag=enable_rag, **kwargs)
                    cls._weak_ref = weakref.ref(cls._instance)
                    cls._init_count = 1
                    print(f"🚀 CHS Singleton initialized (instance {cls._init_count})")
                except Exception as e:
                    print(f"❌ CHS Singleton initialization failed: {str(e)}")
                    raise
            else:
                cls._init_count += 1

        return cls._instance

    @classmethod
    def get_stats(cls):
        """Get singleton statistics."""
        return {
            'instance_exists': cls._instance is not None,
            'init_count': cls._init_count,
            'reference_alive': cls._weak_ref() is not None if cls._weak_ref else False
        }

    @classmethod
    def cleanup(cls):
        """Force cleanup of singleton instance."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    # Explicit cleanup
                    if hasattr(cls._instance, 'hybrid_searcher'):
                        cls._instance.hybrid_searcher = None
                    if hasattr(cls._instance, 'vector_store'):
                        cls._instance.vector_store = None
                except:
                    pass
                finally:
                    cls._instance = None
                    cls._weak_ref = None
                    print("🧹 CHS Singleton cleaned up")


# Global accessor function
def get_chs_instance(enable_rag: bool = True, **kwargs):
    """Convenient global function to get CHS singleton."""
    return CHSSingleton.get_instance(enable_rag=enable_rag, **kwargs)


def cleanup_chs_instance():
    """Convenient global function to cleanup CHS singleton."""
    return CHSSingleton.cleanup()
