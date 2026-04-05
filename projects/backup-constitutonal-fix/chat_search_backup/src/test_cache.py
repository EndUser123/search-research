#!/usr/bin/env python3
"""Simple test script for caching system"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from chat_history_search import ChatHistorySearcher


def main():
    print("Testing CHS caching system...")

    # Initialize searcher
    searcher = ChatHistorySearcher(enable_rag=False)

    print(f"Caching available: {searcher.enable_caching}")
    print(f"Cache object: {searcher.cache is not None}")

    if searcher.enable_caching and searcher.cache:
        print("Cache system is properly initialized")

        # Test cache stats
        stats = searcher.get_cache_stats()
        print(f"Cache stats: {stats}")

        # Perform a search to populate cache
        print("Performing search...")
        results = searcher.search("test", limit=3)
        print(f"Search results: {len(results)} items")

        # Check stats again
        stats = searcher.get_cache_stats()
        print(f"Cache stats after search: {stats}")
    else:
        print("Cache system not available")

if __name__ == "__main__":
    main()
