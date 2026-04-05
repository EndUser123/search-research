#!/usr/bin/env python3
"""CHS Production Health Check Monitor"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))

def health_check():
    """Perform comprehensive health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }

    try:
        # Database health
        from src.modules.analysis.chat_search.src.chat_history_db import ChatHistoryDB
        db = ChatHistoryDB()
        stats = db.get_stats()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'sessions': stats.get('sessions', 0),
            'messages': stats.get('messages', 0)
        }

        # Search functionality health
        from src.modules.analysis.chat_search.src.chat_history_search import (
            ChatHistorySearcher,
        )
        searcher = ChatHistorySearcher(enable_rag=True)

        # Test search performance
        start_time = time.perf_counter()
        results = searcher.search("health check", limit=3)
        search_time = (time.perf_counter() - start_time) * 1000

        health_status['checks']['search_performance'] = {
            'status': 'healthy' if search_time < 100 else 'degraded',
            'response_time_ms': search_time,
            'results_count': len(results)
        }

        # Vector store health
        health_status['checks']['vector_store'] = {
            'status': 'healthy' if searcher.enable_rag else 'disabled',
            'rag_enabled': searcher.enable_rag
        }

        # Optimization systems health
        health_status['checks']['optimizations'] = {
            'workflow_optimizations': searcher.workflow_optimization_enabled,
            'session_monitoring': searcher.session_monitor is not None,
            'pattern_recognition': searcher.pattern_recognizer is not None,
            'enhanced_caching': searcher.enable_caching
        }

    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status

if __name__ == "__main__":
    health = health_check()
    print(json.dumps(health, indent=2))
    sys.exit(0 if health['status'] == 'healthy' else 1)
