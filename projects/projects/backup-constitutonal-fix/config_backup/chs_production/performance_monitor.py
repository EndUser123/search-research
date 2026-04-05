#!/usr/bin/env python3
"""CHS Production Performance Monitor"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))

def performance_monitor():
    """Monitor CHS system performance."""
    perf_data = {
        'timestamp': datetime.now().isoformat(),
        'system_metrics': {},
        'chs_metrics': {}
    }

    try:
        # System metrics
        process = psutil.Process()
        perf_data['system_metrics'] = {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'threads': process.num_threads()
        }

        # CHS performance metrics
        from src.modules.analysis.chat_search.src.chat_history_search import (
            ChatHistorySearcher,
        )
        searcher = ChatHistorySearcher(enable_rag=True)

        # Test search performance
        test_queries = ["database", "API", "testing"]
        search_times = []

        for query in test_queries:
            start_time = time.perf_counter()
            results = searcher.search(query, limit=5)
            search_time = (time.perf_counter() - start_time) * 1000
            search_times.append(search_time)

        perf_data['chs_metrics'] = {
            'avg_search_time_ms': sum(search_times) / len(search_times),
            'max_search_time_ms': max(search_times),
            'min_search_time_ms': min(search_times),
            'rag_enabled': searcher.enable_rag,
            'cache_enabled': searcher.enable_caching,
            'optimizations_enabled': searcher.workflow_optimization_enabled
        }

        # Database stats
        from src.modules.analysis.chat_search.src.chat_history_db import ChatHistoryDB
        db = ChatHistoryDB()
        db_stats = db.get_stats()
        perf_data['chs_metrics']['database_stats'] = db_stats

    except Exception as e:
        perf_data['error'] = str(e)

    return perf_data

if __name__ == "__main__":
    perf = performance_monitor()
    print(json.dumps(perf, indent=2))
