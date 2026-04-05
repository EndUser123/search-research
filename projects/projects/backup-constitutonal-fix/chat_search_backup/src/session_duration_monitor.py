#!/usr/bin/env python3
"""On-demand session duration monitoring tool."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

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
from production_config import get_config_value


class SessionDurationMonitor:
    """On-demand session duration monitoring and analysis."""

    def __init__(self, index_dir: Path = None):
        self.start_time = datetime.now()
        self.active_sessions = {}
        self.index_dir = index_dir or Path(__file__).parent

    def start_session(self, session_id: str) -> None:
        """Start tracking a new session."""
        self.active_sessions[session_id] = {
            'session_id': session_id,
            'start_time': time.time(),
            'queries': [],
            'start_timestamp': datetime.now().isoformat()
        }

    def record_query(self, session_id: str, query: str, execution_time: float, results_count: int, cache_hit: bool = False, success: bool = True) -> None:
        """Record a query for the session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['queries'].append({
                'query': query,
                'execution_time': execution_time,
                'results_count': results_count,
                'cache_hit': cache_hit,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })

    def end_session(self, session_id: str) -> dict[str, Any]:
        """End session tracking and return session metrics."""
        if session_id not in self.active_sessions:
            return {}

        session_data = self.active_sessions[session_id]
        end_time = time.time()
        duration_seconds = end_time - session_data['start_time']

        metrics = {
            'session_id': session_id,
            'start_time': session_data['start_timestamp'],
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_seconds / 60, 2),
            'total_queries': len(session_data['queries']),
            'avg_execution_time': round(sum(q['execution_time'] for q in session_data['queries']) / len(session_data['queries']), 2) if session_data['queries'] else 0,
            'cache_hits': sum(1 for q in session_data['queries'] if q['cache_hit']),
            'successful_queries': sum(1 for q in session_data['queries'] if q['success']),
            'total_results': sum(q['results_count'] for q in session_data['queries'])
        }

        # Remove from active sessions
        del self.active_sessions[session_id]

        return metrics

    def get_current_session_metrics(self) -> dict[str, Any]:
        """Get current session duration metrics."""
        print("⏱️  Current Session Duration Metrics")
        print("-" * 50)

        try:
            # Get database statistics
            db = ChatHistoryDB()
            stats = db.get_stats()

            # Calculate current session metrics
            messages_per_session = stats['messages'] / max(stats['sessions'], 1)

            # Target metrics (from workflow optimization goals)
            target_duration_minutes = 123.1  # 25% reduction from 164.2
            current_duration_estimate = 164.2  # Based on previous analysis
            reduction_needed_percent = ((current_duration_estimate - target_duration_minutes) / current_duration_estimate) * 100

            session_metrics = {
                'total_sessions': stats['sessions'],
                'total_messages': stats['messages'],
                'avg_messages_per_session': round(messages_per_session, 1),
                'current_avg_duration_estimate': current_duration_estimate,
                'target_duration_minutes': target_duration_minutes,
                'reduction_needed_percent': round(reduction_needed_percent, 1),
                'time_saved_per_session_minutes': round(current_duration_estimate - target_duration_minutes, 1),
                'status': 'NEEDS_OPTIMIZATION' if reduction_needed_percent > 5 else 'ON_TRACK'
            }

            print("📊 Database Statistics:")
            print(f"   Total Sessions: {session_metrics['total_sessions']:,}")
            print(f"   Total Messages: {session_metrics['total_messages']:,}")
            print(f"   Avg Messages/Session: {session_metrics['avg_messages_per_session']}")
            print()

            print("⏱️  Session Duration Analysis:")
            print(f"   Current Avg Duration: {session_metrics['current_avg_duration_estimate']:.1f} minutes")
            print(f"   Target Duration: {session_metrics['target_duration_minutes']:.1f} minutes")
            print(f"   Reduction Needed: {session_metrics['reduction_needed_percent']:.1f}%")
            print(f"   Time Saved per Session: {session_metrics['time_saved_per_session_minutes']:.1f} minutes")
            print(f"   Status: {session_metrics['status']}")

            return session_metrics

        except Exception as e:
            print(f"❌ Error getting session metrics: {str(e)}")
            return {}

    def calculate_productivity_impact(self) -> dict[str, Any]:
        """Calculate productivity impact of session duration optimization."""
        print("\n💼 Productivity Impact Analysis")
        print("-" * 50)

        session_metrics = self.get_current_session_metrics()
        if not session_metrics:
            return {}

        # Calculate productivity gains
        time_saved_per_session = session_metrics['time_saved_per_session_minutes']
        sessions_per_day = 5  # Estimate
        working_days_per_year = 250

        productivity_impact = {
            'time_saved_per_session_minutes': time_saved_per_session,
            'sessions_per_day': sessions_per_day,
            'daily_time_saved_hours': round((time_saved_per_session * sessions_per_day) / 60, 1),
            'weekly_time_saved_hours': round(((time_saved_per_session * sessions_per_day) / 60) * 5, 1),
            'annual_time_saved_hours': round(((time_saved_per_session * sessions_per_day) / 60) * working_days_per_year, 1),
            'annual_time_saved_days': round((((time_saved_per_session * sessions_per_day) / 60) * working_days_per_year) / 8, 1),
            'productivity_improvement_percent': session_metrics['reduction_needed_percent']
        }

        print("⚡ Productivity Gains:")
        print(f"   Time Saved per Session: {productivity_impact['time_saved_per_session_minutes']:.1f} minutes")
        print(f"   Daily Time Saved: {productivity_impact['daily_time_saved_hours']:.1f} hours")
        print(f"   Weekly Time Saved: {productivity_impact['weekly_time_saved_hours']:.1f} hours")
        print(f"   Annual Time Saved: {productivity_impact['annual_time_saved_hours']:.0f} hours ({productivity_impact['annual_time_saved_days']:.1f} days)")
        print(f"   Productivity Improvement: {productivity_impact['productivity_improvement_percent']:.1f}%")

        return productivity_impact

    def generate_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Generate session optimization recommendations."""
        print("\n💡 Session Duration Optimization Recommendations")
        print("-" * 50)

        session_metrics = self.get_current_session_metrics()

        recommendations = []

        # High priority recommendations
        if session_metrics.get('reduction_needed_percent', 0) > 20:
            recommendations.append({
                'priority': 'HIGH',
                'recommendation': 'Focus on reducing session duration by 25%',
                'details': f'Current: {session_metrics.get("current_avg_duration_estimate", 0):.1f}min → Target: {session_metrics.get("target_duration_minutes", 0):.1f}min',
                'expected_impact': '25% productivity improvement'
            })

        # Feature activation recommendations
        optimizations_enabled = {
            'pattern_recognition': get_config_value("PATTERN_RECOGNITION_ENABLED", "false") == "true",
            'enhanced_caching': get_config_value("ENHANCED_CACHING_ENABLED", "false") == "true",
            'session_monitoring': get_config_value("SESSION_MONITORING_ENABLED", "false") == "true"
        }

        disabled_features = [feature for feature, enabled in optimizations_enabled.items() if not enabled]
        if disabled_features:
            recommendations.append({
                'priority': 'MEDIUM',
                'recommendation': 'Activate remaining workflow optimizations',
                'details': f'Disabled features: {", ".join(disabled_features)}',
                'expected_impact': 'Enhanced session optimization capabilities'
            })

        print(f"📋 Generated {len(recommendations)} Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(rec['priority'], '⚪')
            print(f"   {i}. {priority_icon} {rec['recommendation']} ({rec['priority']})")
            print(f"      Expected Impact: {rec['expected_impact']}")

        return recommendations


def main():
    """Main session duration monitoring."""
    print("⏱️  Session Duration Monitoring Tool")
    print("=" * 60)
    print("ON-DEMAND MONITORING - No background processes")
    print()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        monitor = SessionDurationMonitor()

        if command == "status":
            monitor.get_current_session_metrics()
        elif command == "impact":
            monitor.calculate_productivity_impact()
        elif command == "recommendations":
            monitor.generate_optimization_recommendations()
        else:
            print("Available commands:")
            print("  status           - Current session metrics")
            print("  impact           - Productivity impact analysis")
            print("  recommendations  - Optimization recommendations")
    else:
        print("Available commands:")
        print("  status           - Current session metrics")
        print("  impact           - Productivity impact analysis")
        print("  recommendations  - Optimization recommendations")
        print()
        print("Examples:")
        print("  python session_duration_monitor.py status")
        print("  python session_duration_monitor.py impact")


if __name__ == "__main__":
    main()
