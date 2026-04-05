#!/usr/bin/env python3
"""
Production Analytics Skill

Constitutionally-compliant on-demand analytics with Phase 2 integration
for CSF NIP Load Testing Optimization System.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add analytics and CSF NIP modules to path
analytics_path = Path(__file__).parent.parent.parent.parent / "__csf" / "src" / "analytics"
csf_path = Path(__file__).parent.parent.parent.parent / "__csf" / "src"

sys.path.insert(0, str(analytics_path))
sys.path.insert(0, str(csf_path))

class ProductionAnalyticsSkill:
    """Production analytics skill with constitutional compliance"""

    def __init__(self):
        try:
            from analytics_dashboard import interactive_dashboard, show_dashboard
            from production_analytics import AnalyticsQuery, get_production_analytics

            self.analytics = get_production_analytics()
            self.AnalyticsQuery = AnalyticsQuery
            self.show_dashboard = show_dashboard
            self.interactive_dashboard = interactive_dashboard

            self.available = True
        except ImportError as e:
            print(f"❌ Analytics system unavailable: {e}")
            self.available = False

    def run_analytics_command(self, args):
        """Main analytics command execution"""

        if not self.available:
            print("❌ Production Analytics System is not available")
            print("   Please ensure the analytics modules are properly installed")
            return False

        print("📊 Production Analytics System")
        print("═" * 50)

        # Route command based on arguments
        if args.dashboard:
            return self._show_dashboard(args)
        elif args.collect:
            return self._collect_metrics(args)
        elif args.query:
            return self._query_analytics(args)
        elif args.export:
            return self._export_analytics(args)
        elif args.health:
            return self._show_health(args)
        elif args.status:
            return self._show_status(args)
        else:
            # Default: show system overview
            return self._show_overview(args)

    def _show_dashboard(self, args) -> bool:
        """Show analytics dashboard"""
        print("\n📈 Analytics Dashboard")
        print("-" * 30)

        try:
            if args.interactive:
                print("Starting interactive dashboard (Ctrl+C to exit)...")
                self.interactive_dashboard()
            else:
                print(self.show_dashboard())
            return True

        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            return False

    def _collect_metrics(self, args) -> bool:
        """Collect and store production metrics"""
        print("\n🔄 Collecting Production Metrics")
        print("-" * 30)

        purpose = getattr(args, 'purpose', 'manual_collection')

        try:
            from production_analytics import collect_production_metrics

            result = collect_production_metrics(purpose)

            print("✅ Metrics Collection Complete:")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            print(f"   Metrics Collected: {result.get('metrics_collected', 0)}")
            print(f"   Metrics Stored: {'✅' if result.get('metrics_stored') else '❌'}")

            if 'session_summary' in result:
                summary = result['session_summary']
                print(f"   Session Duration: {summary.get('duration_seconds', 0):.1f}s")
                print(f"   Operations/sec: {summary.get('operations_per_second', 0):.1f}")

            compliance = result.get('constitutional_compliance', False)
            print(f"   Constitutional Compliance: {'✅' if compliance else '❌'}")

            return True

        except Exception as e:
            print(f"❌ Metrics collection failed: {e}")
            return False

    def _query_analytics(self, args) -> bool:
        """Query analytics data"""
        print("\n🔍 Analytics Query")
        print("-" * 30)

        try:
            query = self._parse_query_string(args.query)
            results = self.analytics.query_analytics(query)

            print(f"Query Results: {len(results)} records found")

            if results:
                # Display results in table format
                print(f"\n{'Timestamp':<19} {'Type':<15} {'Component':<15} {'Value':<10} {'Unit':<8}")
                print("-" * 80)

                for result in results[:20]:  # Limit to 20 for display
                    timestamp = result['timestamp'][:19]
                    metric_type = result['metric_type'][:14]
                    component = result['component'][:14]
                    value = f"{result['value']:.2f}" if isinstance(result['value'], (int, float)) else str(result['value'])[:9]
                    unit = result['unit'][:7]

                    print(f"{timestamp:<19} {metric_type:<15} {component:<15} {value:<10} {unit:<8}")

                if len(results) > 20:
                    print(f"... and {len(results) - 20} more records")

            return True

        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False

    def _parse_query_string(self, query_string: str) -> 'AnalyticsQuery':
        """Parse query string into AnalyticsQuery object"""
        query = self.AnalyticsQuery()

        # Simple parsing - in production would use proper query language
        parts = query_string.split()

        for i, part in enumerate(parts):
            if part == "--hours" and i + 1 < len(parts):
                try:
                    hours = int(parts[i + 1])
                    query.start_time = datetime.now() - timedelta(hours=hours)
                except ValueError:
                    pass
            elif part == "--limit" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                    query.limit = limit
                except ValueError:
                    pass
            elif part == "--type" and i + 1 < len(parts):
                query.metric_types = [parts[i + 1]]
            elif part == "--component" and i + 1 < len(parts):
                query.components = [parts[i + 1]]
            elif part == "--avg":
                query.aggregation = "avg"
            elif part == "--sum":
                query.aggregation = "sum"

        return query

    def _export_analytics(self, args) -> bool:
        """Export analytics data to file"""
        print(f"\n📁 Exporting Analytics to: {args.export}")
        print("-" * 30)

        try:
            # Default query for export (last 24 hours)
            query = self.AnalyticsQuery(
                start_time=datetime.now() - timedelta(hours=24),
                limit=10000
            )

            results = self.analytics.query_analytics(query)

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "query_parameters": {
                    "start_time": query.start_time.isoformat() if query.start_time else None,
                    "end_time": query.end_time.isoformat() if query.end_time else None,
                    "metric_types": query.metric_types,
                    "components": query.components,
                    "limit": query.limit
                },
                "record_count": len(results),
                "data": results
            }

            with open(args.export, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"✅ Export complete: {len(results)} records exported")
            return True

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False

    def _show_health(self, args) -> bool:
        """Show system health summary"""
        print("\n🏥 System Health Summary")
        print("-" * 30)

        try:
            health = self.analytics.get_system_health_summary()

            print(f"Timestamp: {health['timestamp'][:19]}")
            print(f"Constitutional Compliance: {'✅ YES' if health['constitutional_compliance'] else '❌ NO'}")
            print(f"Current CPU Usage: {health['current_cpu_usage']:.1f}%")
            print(f"Current Memory Usage: {health['current_memory_usage']:.1f}%")
            print(f"Metrics Collected (24h): {health['metrics_collected_last_24h']}")
            print(f"Average CPU Usage (24h): {health['avg_cpu_usage_24h']:.1f}%")
            print(f"Average Memory Usage (24h): {health['avg_memory_usage_24h']:.1f}%")
            print(f"Phase 2 Integration: {'✅ Available' if health['phase2_integration_available'] else '❌ Unavailable'}")
            print(f"Active Session: {'✅ Yes' if health['session_active'] else '❌ No'}")

            return True

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    def _show_status(self, args) -> bool:
        """Show analytics system status"""
        print("\n📊 Analytics System Status")
        print("-" * 30)

        try:
            print("System Available: ✅")
            print(f"Database Path: {self.analytics.db_path}")
            print(f"Constitutional Compliance: {'✅' if self.analytics.compliance else '❌'}")
            print(f"Phase 2 Integration: {'✅' if self.analytics.phase2_system else '❌'}")
            print(f"Current Session: {'Active' if self.analytics.start_time else 'Inactive'}")

            if self.analytics.start_time:
                elapsed = time.time() - self.analytics.start_time
                print(f"Session Duration: {elapsed:.1f}s")

            return True

        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return False

    def _show_overview(self, args) -> bool:
        """Show system overview"""
        print("\n🎯 Production Analytics Overview")
        print("-" * 40)

        print("Available Commands:")
        print("  --dashboard              Show analytics dashboard")
        print("  --collect                Collect production metrics")
        print("  --query '<query>'        Query analytics data")
        print("  --export <filename>      Export data to file")
        print("  --health                 Show system health")
        print("  --status                 Show system status")

        print("\nQuery Examples:")
        print("  --query 'cpu_usage --hours 24'")
        print("  --query 'memory_usage --limit 100'")
        print("  --query 'phase2_health --component integration_system'")

        print("\nConstitutional Compliance:")
        print("  ✅ No background services - on-demand only")
        print("  ✅ Resource safety limits enforced")
        print("  ✅ Solo developer optimized")
        print("  ✅ Evidence-based analytics")

        return True


def main():
    """Main entry point for production analytics skill"""
    parser = argparse.ArgumentParser(
        description="Production Analytics with Constitutional Compliance"
    )

    # Main commands
    parser.add_argument('--dashboard', action='store_true', help='Show analytics dashboard')
    parser.add_argument('--interactive', action='store_true', help='Run interactive dashboard')
    parser.add_argument('--collect', action='store_true', help='Collect production metrics')
    parser.add_argument('--purpose', help='Purpose for metrics collection')
    parser.add_argument('--query', help='Query analytics data')
    parser.add_argument('--export', help='Export analytics to file')
    parser.add_argument('--health', action='store_true', help='Show system health')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--show-help', action='store_true', help='Show this help message')

    args = parser.parse_args()

    if args.show_help:
        parser.print_help()
        return

    # Create and run analytics skill
    skill = ProductionAnalyticsSkill()
    result = skill.run_analytics_command(args)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
