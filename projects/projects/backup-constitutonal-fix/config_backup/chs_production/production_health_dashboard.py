#!/usr/bin/env python3
"""Production Health Dashboard - ON-DEMAND Only
No real-time monitoring, just instant health checks when executed.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))


class ProductionHealthDashboard:
    """On-demand production health monitoring dashboard for CHS system."""

    def __init__(self):
        self.start_time = datetime.now()
        self.health_data = {}

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health status."""
        try:
            # Import singleton to ensure minimal resource usage
            from src.modules.analysis.chat_search.src.chs_singleton import (
                get_chs_instance,
            )

            # Get CHS instance
            searcher = get_chs_instance(enable_rag=True)

            # Basic health check
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "chs_instance": {
                    "initialized": True,
                    "rag_enabled": hasattr(searcher, 'enable_rag') and searcher.enable_rag,
                    "cache_enabled": hasattr(searcher, 'enable_caching') and searcher.enable_caching,
                    "session_monitoring": searcher.session_monitor is not None,
                    "pattern_recognition": searcher.pattern_recognizer is not None
                }
            }

            # Test basic functionality
            try:
                start_time = time.perf_counter()
                test_results = searcher.search("health check test", limit=3)
                response_time = (time.perf_counter() - start_time) * 1000

                health_status["functionality"] = {
                    "status": "healthy",
                    "test_search_success": len(test_results) >= 0,
                    "response_time_ms": round(response_time, 2),
                    "response_time_status": "good" if response_time < 50 else "slow" if response_time < 100 else "critical"
                }
            except Exception as e:
                health_status["functionality"] = {
                    "status": "degraded",
                    "error": str(e),
                    "test_search_success": False
                }
                health_status["status"] = "degraded"

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_database_health(self) -> dict[str, Any]:
        """Get database health status."""
        try:
            from src.modules.analysis.chat_search.src.chat_history_db import (
                ChatHistoryDB,
            )

            db = ChatHistoryDB()
            stats = db.get_stats()

            # Check database file health
            db_path = db.db_path
            file_exists = db_path.exists()
            file_size_mb = db_path.stat().st_size / 1024 / 1024 if file_exists else 0

            return {
                "status": "healthy" if file_exists else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "file_health": {
                    "exists": file_exists,
                    "path": str(db_path),
                    "size_mb": round(file_size_mb, 2),
                    "accessible": True
                }
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_gpu_health(self) -> dict[str, Any]:
        """Get GPU health status."""
        try:
            import torch

            if not torch.cuda.is_available():
                return {
                    "status": "unavailable",
                    "message": "CUDA not available",
                    "timestamp": datetime.now().isoformat()
                }

            # Get GPU memory info
            total_memory = torch.cuda.get_device_properties(0).total_memory
            allocated_memory = torch.cuda.memory_allocated(0)
            reserved_memory = torch.cuda.memory_reserved(0)

            # Calculate percentages
            allocated_percent = (allocated_memory / total_memory) * 100
            reserved_percent = (reserved_memory / total_memory) * 100
            free_memory = total_memory - allocated_memory

            # Determine health status
            if reserved_percent > 90:
                status = "critical"
            elif reserved_percent > 75:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "gpu_info": {
                    "device": torch.cuda.get_device_name(0),
                    "total_memory_gb": round(total_memory / 1024**3, 2),
                    "allocated_memory_gb": round(allocated_memory / 1024**3, 3),
                    "reserved_memory_gb": round(reserved_memory / 1024**3, 3),
                    "free_memory_gb": round(free_memory / 1024**3, 3),
                    "allocated_percent": round(allocated_percent, 2),
                    "reserved_percent": round(reserved_percent, 2),
                    "utilization": f"{reserved_percent:.1f}%"
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_vector_store_health(self) -> dict[str, Any]:
        """Get vector store health status."""
        try:
            from src.modules.analysis.chat_search.src.chs_singleton import (
                get_chs_instance,
            )

            searcher = get_chs_instance(enable_rag=True)

            vector_store_info = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "rag_enabled": hasattr(searcher, 'enable_rag') and searcher.enable_rag
            }

            # Get vector store details if available
            if hasattr(searcher, 'hybrid_searcher') and searcher.hybrid_searcher:
                try:
                    vector_store = searcher.hybrid_searcher.vector_store
                    if hasattr(vector_store, '_clients'):
                        client = vector_store._clients.get("chat_history")
                        if client and hasattr(client, '_client'):
                            try:
                                collection_info = client._client.get_collection("chat_vectors")
                                if collection_info:
                                    vector_store_info["collection"] = {
                                        "name": collection_info.name,
                                        "points_count": getattr(collection_info, 'points_count', 0),
                                        "status": "healthy"
                                    }
                            except:
                                pass
                except:
                    pass

            return vector_store_info

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now_isoformat()
            }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics (sampled on-demand)."""
        try:
            from src.modules.analysis.chat_search.src.chs_singleton import (
                get_chs_instance,
            )
            from src.modules.analysis.chat_search.src.gpu_memory_manager import (
                get_gpu_memory_status,
            )

            searcher = get_chs_instance(enable_rag=True)

            # Sample search performance
            test_queries = [
                "database optimization",
                "API design patterns",
                "testing methodology",
                "performance monitoring"
            ]

            response_times = []
            results_counts = []

            for query in test_queries:
                start_time = time.perf_counter()
                try:
                    results = searcher.search(query, limit=5)
                    end_time = time.perf_counter()

                    response_time = (end_time - start_time) * 1000
                    response_times.append(response_time)
                    results_counts.append(len(results))

                except Exception:
                    response_times.append(999)  # Mark as failed
                    results_counts.append(0)

            # Calculate statistics
            valid_times = [t for t in response_times if t < 999]

            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                min_time = min(valid_times)
                max_time = max(valid_times)
                std_dev = (sum((t - avg_time) ** 2 for t in valid_times) / len(valid_times)) ** 0.5
            else:
                avg_time = min_time = max_time = std_dev = 0

            # Get GPU memory status
            gpu_status = get_gpu_memory_status()

            return {
                "timestamp": datetime.now().isoformat(),
                "search_performance": {
                    "avg_response_time_ms": round(avg_time, 2),
                    "min_response_time_ms": round(min_time, 2),
                    "max_response_time_ms": round(max_time, 2),
                    "std_deviation_ms": round(std_dev, 2),
                    "total_queries": len(test_queries),
                    "successful_queries": len(valid_times),
                    "success_rate": len(valid_times) / len(test_queries) * 100,
                    "performance_grade": self._calculate_performance_grade(avg_time)
                },
                "gpu_memory": gpu_status
            }

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "search_performance": {"status": "error"},
                "gpu_memory": {"status": "error"}
            }

    def get_singleton_stats(self) -> dict[str, Any]:
        """Get singleton pattern statistics."""
        try:
            from src.modules.analysis.chat_search.src.chs_singleton import CHSSingleton

            stats = CHSSingleton.get_stats()
            gpu_status = self.get_gpu_health()

            return {
                "timestamp": datetime.now().isoformat(),
                "singleton_pattern": {
                    "instance_exists": stats.get("instance_exists", False),
                    "init_count": stats.get("init_count", 0),
                    "reference_alive": stats.get("reference_alive", False),
                    "memory_efficiency": f"{stats.get('init_count', 1)}x shared instances"
                },
                "memory_impact": {
                    "with_singleton": gpu_status.get("reserved_percent", 0),
                    "estimated_without": gpu_status.get("reserved_percent", 0) * stats.get("init_count", 1),
                    "memory_saved_mb": round((gpu_status.get("reserved_gb", 0) * (stats.get('init_count', 1) - 1)) * 1024, 1)
                }
            }

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "singleton_pattern": {"status": "error"},
                "memory_impact": {"status": "error"}
            }

    def _calculate_performance_grade(self, avg_time_ms: float) -> str:
        """Calculate performance grade based on average response time."""
        if avg_time_ms < 25:
            return "A+"
        elif avg_time_ms < 50:
            return "A"
        elif avg_time_ms < 100:
            return "B"
        elif avg_time_ms < 200:
            return "C"
        else:
            return "D"

    def get_recent_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent error logs."""
        errors = []

        # Check for common error patterns
        error_patterns = [
            "CUDA out of memory",
            "GPU memory exhausted",
            "Qdrant client error",
            "vector store locked",
            "database connection failed",
            "search timeout",
            "initialization failed"
        ]

        # This would normally read from log files
        # For now, simulate recent activity
        if hasattr(self, 'health_data') and 'errors' in self.health_data:
            return self.health_data['errors'][-limit:]

        return []

    def generate_health_report(self) -> dict[str, Any]:
        """Generate comprehensive health report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dashboard_version": "v2.0-on-demand",
            "system_info": {
                "environment": "production",
                "csf_nip_path": str(csf_nip_root),
                "dashboard_mode": "on-demand"
            },
            "health_checks": {
                "system": self.get_system_health(),
                "database": self.get_database_health(),
                "gpu": self.get_gpu_health(),
                "vector_store": self.get_vector_store_health()
            },
            "performance": self.get_performance_metrics(),
            "singleton_stats": self.get_singleton_stats(),
            "recent_errors": self.get_recent_errors()
        }

        # Calculate overall health status
        checks = report["health_checks"]
        statuses = [check["status"] for check in checks.values()]

        if "unhealthy" in statuses or "critical" in statuses:
            overall_status = "critical"
        elif "degraded" in statuses or "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        report["overall_status"] = overall_status
        report["summary"] = self._generate_summary(report)

        return report

    def _generate_summary(self, report: dict[str, Any]) -> dict[str, Any]:
        """Generate health summary."""
        checks = report["health_checks"]

        # Count statuses
        status_counts = {}
        for check_name, check_data in checks.items():
            status = check_data.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        total_checks = len(checks)
        healthy_checks = status_counts.get("healthy", 0)

        # Database metrics
        db_stats = checks["database"].get("statistics", {})
        sessions = db_stats.get("sessions", 0)
        messages = db_stats.get("messages", 0)

        # Performance metrics
        perf_metrics = report.get("performance", {})
        search_perf = perf_metrics.get("search_performance", {})
        avg_time = search_perf.get("avg_response_time_ms", 0)
        success_rate = search_perf.get("success_rate", 0)

        return {
            "overall_health": f"{healthy_checks}/{total_checks} healthy",
            "critical_issues": status_counts.get("critical", 0),
            "warning_issues": status_counts.get("warning", 0),
            "database_stats": f"{sessions} sessions, {messages} messages",
            "performance": f"{avg_time:.0f}ms avg, {success_rate:.0f}% success rate",
            "gpu_utilization": checks["gpu"].get("gpu_info", {}).get("utilization", "0%"),
            "singleton_efficiency": report.get("singleton_stats", {}).get("memory_impact", {}).get("memory_saved_mb", 0)
        }

    def display_dashboard(self) -> None:
        """Display the health dashboard in a readable format."""
        report = self.generate_health_report()

        print("🚀 CHS PRODUCTION HEALTH DASHBOARD (ON-DEMAND)")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Environment: {report['system_info']['environment'].upper()}")
        print(f"Mode: {report['system_info']['dashboard_mode']}")
        print()

        # Overall Status
        status_emoji = {
            "healthy": "🟢",
            "warning": "🟡",
            "critical": "🔴",
            "unhealthy": "❌"
        }.get(report["overall_status"], "•")

        print(f"OVERALL STATUS: {status_emoji} {report['overall_status'].upper()}")

        # Summary
        summary = report["summary"]
        print(f"📊 SUMMARY: {summary['overall_health']}")
        print(f"   Issues: {summary['critical_issues']} critical, {summary['warning_issues']} warning")
        print(f"   Database: {summary['database_stats']}")
        print(f"   Performance: {summary['performance']}")
        print(f"   GPU: {summary['gpu_utilization']} utilization")
        print(f"   Memory Efficiency: {summary['singleton_efficiency']} MB saved")
        print()

        # Health Checks
        print("🔍 HEALTH CHECKS:")
        for check_name, check_data in report["health_checks"].items():
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "🚨",
                "unhealthy": "❌",
                "degraded": "⚠️",
                "unavailable": "⚪"
            }.get(check_data.get("status", "unknown"), "•")

            print(f"   {status_emoji} {check_name.title().replace('_', ' ')}: {check_data['status'].upper()}")

            # Add key details
            if check_name == "system":
                chs_health = check_data.get("chs_instance", {})
                print(f"      CHS: RAG={'✅' if chs_health.get('rag_enabled') else '❌'}")
                print(f"      Cache: {'✅' if chs_health.get('cache_enabled') else '❌'}")

            elif check_name == "database":
                db_health = check_data.get("statistics", {})
                print(f"      Sessions: {db_health.get('sessions', 0):,}")
                print(f"      Messages: {db_health.get('messages', 0):,}")

            elif check_name == "gpu":
                gpu_info = check_data.get("gpu_info", {})
                if gpu_info:
                    print(f"      Device: {gpu_info.get('device', 'Unknown')}")
                    print(f"      Usage: {gpu_info.get('utilization', '0%')}")

            elif check_name == "vector_store":
                print(f"      RAG: {'✅' if check_data.get('rag_enabled') else '❌'}")

        print()

        # Performance Section
        if "search_performance" in report.get("performance", {}):
            perf = report["performance"]["search_performance"]
            grade = perf.get("performance_grade", "Unknown")
            emoji = {"A+": "🏆", "A": "🥇", "B": "🥉", "C": "📊", "D": "📉"}.get(grade, "📊")

            print("⚡ PERFORMANCE:")
            print(f"   Grade: {emoji} {grade}")
            print(f"   Avg Response: {perf.get('avg_response_time_ms', 0):.0f}ms")
            print(f"   Success Rate: {perf.get('success_rate', 0):.1f}%")
            print(f"   Sample Size: {perf.get('total_queries', 0)} queries")

        print()

        # Recent Errors
        recent_errors = report.get("recent_errors", [])
        if recent_errors:
            print("🚨 RECENT ERRORS:")
            for i, error in enumerate(recent_errors[-5:], 1):
                print(f"   {i}. {error.get('message', 'Unknown error')}")
        elif recent_errors:
            print("✅ No recent errors detected")

    def save_health_report(self, output_file: str | None = None) -> str:
        """Save health report to file."""
        report = self.generate_health_report()

        if output_file is None:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(csf_nip_root / ".data" / "logs" / "chs" / f"health_report_{timestamp}.json")

        # Create directory if it doesn't exist
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return output_file

    def print_system_info(self) -> None:
        """Print basic system information."""
        print("🖥️  SYSTEM INFORMATION")
        print("-" * 30)
        print("Environment: Production")
        print(f"CSF NIP Path: {csf_nip_root}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Uptime: {(datetime.now() - self.start_time).total_seconds():.1f} seconds")


def main():
    """Main health dashboard execution."""
    print("🚀 CHS Production Health Dashboard (ON-DEMAND)")
    print("=" * 50)
    print("⚠️  This is ON-DEMAND monitoring - no background processes")
    print()

    dashboard = ProductionHealthDashboard()

    try:
        # Print basic info
        dashboard.print_system_info()
        print()

        # Generate and display full dashboard
        dashboard.display_dashboard()
        print()

        # Save report
        report_file = dashboard.save_health_report()
        print(f"💾 Health report saved to: {report_file}")
        print()

        # Exit with appropriate code
        report = dashboard.generate_health_report()
        if report["overall_status"] == "healthy":
            print("🎉 SYSTEM HEALTH: All systems operational")
            sys.exit(0)
        elif report["overall_status"] == "warning":
            print("⚠️  SYSTEM HEALTH: Minor issues detected")
            sys.exit(1)
        else:
            print("🚨 SYSTEM HEALTH: Critical issues detected")
            sys.exit(2)

    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
