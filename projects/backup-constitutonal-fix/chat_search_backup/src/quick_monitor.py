#!/usr/bin/env python3
"""Manual monitoring tool for production workflow optimizations - runs once and exits."""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from chat_history_db import ChatHistoryDB
from chat_history_search import ChatHistorySearcher
from production_config import get_config_value


def quick_status_check():
    """Perform quick status check of production optimizations."""
    print("🔍 Quick Production Status Check")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Initialize components
        searcher = ChatHistorySearcher()
        db = ChatHistoryDB()

        # Check database
        stats = db.get_stats()
        print("📊 Database Status:")
        print(f"   Messages: {stats['messages']:,}")
        print(f"   Sessions: {stats['sessions']:,}")
        print(f"   Size: {stats['db_size_mb']:.2f} MB")
        print()

        # Test search performance
        print("⚡ Search Performance Test:")
        test_queries = ["database performance", "API design", "testing"]

        total_time = 0
        total_results = 0

        for query in test_queries:
            start_time = time.perf_counter()
            results = searcher.search(query, limit=5)
            end_time = time.perf_counter()

            query_time = (end_time - start_time) * 1000
            total_time += query_time
            total_results += len(results)

            status = "✅" if query_time < 50 else "⚠️"
            print(f"   {status} '{query}': {query_time:6.2f}ms | {len(results)} results")

        avg_time = total_time / len(test_queries)
        print(f"   Average: {avg_time:6.2f}ms | Total results: {total_results}")
        print()

        # Check workflow optimizations
        print("🔧 Workflow Optimizations:")
        optimizations = [
            ("Workflow Optimizations", "WORKFLOW_OPTIMIZATIONS_ENABLED"),
            ("Pattern Recognition", "PATTERN_RECOGNITION_ENABLED"),
            ("Enhanced Caching", "ENHANCED_CACHING_ENABLED"),
            ("Session Monitoring", "SESSION_MONITORING_ENABLED")
        ]

        # Check environment variables directly first
        import os
        env_vars = {
            "WORKFLOW_OPTIMIZATIONS_ENABLED": os.environ.get("WORKFLOW_OPTIMIZATIONS_ENABLED", "false"),
            "PATTERN_RECOGNITION_ENABLED": os.environ.get("PATTERN_RECOGNITION_ENABLED", "false"),
            "ENHANCED_CACHING_ENABLED": os.environ.get("ENHANCED_CACHING_ENABLED", "false"),
            "SESSION_MONITORING_ENABLED": os.environ.get("SESSION_MONITORING_ENABLED", "false")
        }

        active_count = 0
        for name, env_var in optimizations:
            enabled = env_vars[env_var] == "true"
            if enabled:
                active_count += 1
            status = "✅ ACTIVE" if enabled else "❌ INACTIVE"
            print(f"   {name}: {status}")

        print(f"   Optimization Coverage: {active_count}/4 ({int((active_count/4)*100)}%)")

        print()

        # Overall assessment
        print("🎯 Overall Assessment:")
        if avg_time < 30:
            print(f"   ✅ Excellent performance ({avg_time:.1f}ms avg)")
        elif avg_time < 50:
            print(f"   ✅ Good performance ({avg_time:.1f}ms avg)")
        else:
            print(f"   ⚠️  Needs attention ({avg_time:.1f}ms avg)")

        return True

    except Exception as e:
        print(f"❌ Error during status check: {str(e)}")
        return False


def monitor_response_time(duration_minutes=5):
    """Manual response time monitoring for specified duration - NOT automatic."""
    print(f"⏱️  MANUAL Response Time Monitoring ({duration_minutes} minutes)")
    print("=" * 60)
    print("🛑 MANUAL ONLY: This will stop after specified duration")
    print()

    try:
        searcher = ChatHistorySearcher()
        test_queries = ["database performance", "API design", "testing", "optimization", "workflow"]

        print("MANUAL MONITORING RESULTS:")
        print("Query | Response Time | Results | Status")
        print("-" * 50)

        # Test each query once manually
        response_times = []

        for query in test_queries:
            query_start = time.perf_counter()
            try:
                results = searcher.search(query, limit=5)
                query_end = time.perf_counter()

                response_time = (query_end - query_start) * 1000
                response_times.append(response_time)

                status = "✅" if response_time < 50 else "⚠️"
                print(f"{query[:20]:20s} | {response_time:8.2f}ms | {len(results):7d} | {status}")

            except Exception as e:
                print(f"{query[:20]:20s} |     ERROR |     0 | ❌ {str(e)[:30]}")
                response_times.append(999)  # High value for errors

        # Summary statistics
        print("\n" + "=" * 60)
        print("📊 MANUAL Monitoring Summary:")
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            print(f"   Total Queries: {len(response_times)}")
            print(f"   Average Time: {avg_time:.2f}ms")
            print(f"   Fastest Time: {min_time:.2f}ms")
            print(f"   Slowest Time: {max_time:.2f}ms")
            print(f"   Performance Grade: {get_performance_grade(avg_time)}")
            print("   ✅ MANUAL CHECK COMPLETED - System idle now")
        else:
            print("   No successful queries recorded")
            print("   ✅ MANUAL CHECK COMPLETED - System idle now")

        print("\n🛑 This was a manual check only - no background monitoring")

    except Exception as e:
        print(f"\n❌ Manual monitoring error: {str(e)}")
        print("🛑 System remains idle - no background monitoring")


def get_performance_grade(avg_time):
    """Get performance grade based on average response time."""
    if avg_time < 20:
        return "A+ (Excellent)"
    elif avg_time < 30:
        return "A (Very Good)"
    elif avg_time < 50:
        return "B (Good)"
    elif avg_time < 100:
        return "C (Fair)"
    else:
        return "D (Needs Improvement)"


def check_alerts():
    """Check for active alerts."""
    print("🚨 Alert Status Check")
    print("=" * 30)

    try:
        # Check response time alert
        searcher = ChatHistorySearcher()

        # Quick performance test
        start_time = time.perf_counter()
        results = searcher.search("alert check", limit=3)
        end_time = time.perf_counter()

        response_time = (end_time - start_time) * 1000

        alerts = []

        if response_time > 50:
            alerts.append(f"🔴 HIGH RESPONSE TIME: {response_time:.2f}ms (threshold: 50ms)")

        if len(results) == 0:
            alerts.append("🟡 ZERO RESULTS: Search returned no results")

        # Check configuration
        workflow_enabled = get_config_value("WORKFLOW_OPTIMIZATIONS_ENABLED", "false") == "true"
        if not workflow_enabled:
            alerts.append("🟡 WORKFLOW OPTIMIZATIONS: Not enabled")

        if alerts:
            print("Active Alerts:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print("✅ No active alerts - System operating normally")

        return len(alerts) == 0

    except Exception as e:
        print(f"❌ Alert check failed: {str(e)}")
        return False


def main():
    """Main monitoring interface."""
    print("🎯 Quick Production Monitoring Tool")
    print("=" * 50)
    print()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "status":
            quick_status_check()
        elif command == "monitor":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor_response_time(duration)
        elif command == "alerts":
            check_alerts()
        else:
            print("Usage:")
            print("  python quick_monitor.py status      - Quick system status")
            print("  python quick_monitor.py monitor [N] - Monitor for N minutes")
            print("  python quick_monitor.py alerts      - Check active alerts")
    else:
        print("Available commands:")
        print("  status   - Quick system status check")
        print("  monitor  - Real-time response time monitoring")
        print("  alerts   - Check for active alerts")
        print()
        print("Examples:")
        print("  python quick_monitor.py status")
        print("  python quick_monitor.py monitor 10")
        print("  python quick_monitor.py alerts")


if __name__ == "__main__":
    main()
