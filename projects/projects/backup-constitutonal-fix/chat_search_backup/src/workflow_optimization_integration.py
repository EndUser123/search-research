#!/usr/bin/env python3
"""
Workflow Optimization Integration
Integrates all workflow optimization components into the main chat search system.
"""

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from context_aware_session import ContextAwareSessionManager
from enhanced_cache_manager import EnhancedCacheManager

# Import optimization components
from query_pattern_recognition import QueryPatternRecognizer
from session_duration_monitor import SessionDurationMonitor, SessionMetrics
from workflow_optimization_analytics import WorkflowOptimizationAnalytics


class WorkflowOptimizedChatSearch:
    """Chat search system integrated with workflow optimization components"""

    def __init__(self, cache_dir: Path | None = None):
        # Initialize cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent / ".cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Initialize optimization components
        self.pattern_recognizer = QueryPatternRecognizer(self.cache_dir)
        self.session_monitor = SessionDurationMonitor(self.cache_dir)
        self.cache_manager = EnhancedCacheManager(self.cache_dir)
        self.context_manager = ContextAwareSessionManager(self.cache_dir)
        self.analytics = WorkflowOptimizationAnalytics(self.cache_dir)

        # Session tracking
        self.current_sessions: dict[str, dict] = {}

        self.logger.info("Workflow-optimized chat search system initialized")

    def start_session(self, project_path: str | None = None,
                     initial_context: dict[str, Any] | None = None) -> str:
        """Start a new optimized session"""
        session_id = str(uuid.uuid4())[:8]

        # Initialize context-aware session
        session_context = self.context_manager.initialize_session(
            session_id, project_path, initial_context
        )

        # Start session duration monitoring
        self.session_monitor.start_session(session_id, initial_context)

        # Track active session
        self.current_sessions[session_id] = {
            "context": session_context,
            "project_path": project_path,
            "start_time": time.time()
        }

        # Get contextual suggestions for the session
        suggestions = self.context_manager.get_session_suggestions(session_id)

        # Preload contextual queries
        if session_context.project_context:
            self.cache_manager.preload_contextual_queries(
                session_context.project_context, limit=3
            )

        self.logger.info(f"Started optimized session {session_id}")

        return {
            "session_id": session_id,
            "suggestions": suggestions,
            "context_restored": session_context.previous_session_id is not None,
            "optimization_features": {
                "pattern_recognition": True,
                "predictive_caching": True,
                "context_awareness": True,
                "duration_monitoring": True
            }
        }

    def search(self, session_id: str, query: str, session_filter: str = "all",
              context_filter: str = "all", rank_by: str = "relevance",
              limit: int = 20) -> dict[str, Any]:
        """Perform optimized search with full workflow integration"""
        if session_id not in self.current_sessions:
            self.logger.warning(f"Session {session_id} not found, starting new session")
            self.start_session()
            session_id = list(self.current_sessions.keys())[-1]

        start_time = time.time()
        session_context = self.current_sessions[session_id]["context"]

        # Prepare filters
        filters = {
            "session_filter": session_filter,
            "context_filter": context_filter,
            "rank_by": rank_by,
            "limit": limit
        }

        # Check enhanced cache first
        cached_results = self.cache_manager.get(query, filters)
        cache_hit = cached_results is not None

        if cache_hit:
            execution_time = time.time() - start_time
            results_count = len(cached_results) if cached_results else 0

            # Record query with cache hit
            self._record_query_optimization(
                session_id, query, execution_time, results_count,
                cache_hit=True, success=results_count > 0
            )

            return {
                "results": cached_results or [],
                "session_id": session_id,
                "optimization_info": {
                    "cache_hit": True,
                    "execution_time": execution_time,
                    "optimization_applied": "cache_hit"
                },
                "suggestions": []
            }

        # Perform actual search (this would integrate with the main search system)
        # For now, we'll simulate a search result
        search_results = self._perform_search(query, filters)

        execution_time = time.time() - start_time
        results_count = len(search_results)
        success = results_count > 0

        # Record query for optimization
        self._record_query_optimization(
            session_id, query, execution_time, results_count,
            cache_hit=False, success=success
        )

        # Cache the results
        if success:
            self.cache_manager.set(query, filters, search_results)

        # Get intelligent suggestions
        suggestions = self.pattern_recognizer.get_intelligent_suggestions(
            query, session_id, limit=3
        )

        # Trigger predictive preloading for next queries
        recent_queries = self.session_monitor.active_sessions.get(
            session_id, {}
        ).get("queries", [])

        if recent_queries:
            query_sequence = [q["query"] for q in recent_queries[-5:]] + [query]
            filters_sequence = [filters] * (len(query_sequence))
            self.cache_manager.record_query_sequence(session_id, query_sequence, filters_sequence)

        return {
            "results": search_results,
            "session_id": session_id,
            "optimization_info": {
                "cache_hit": False,
                "execution_time": execution_time,
                "optimization_applied": "full_search_with_caching"
            },
            "suggestions": suggestions,
            "session_metrics": self._get_session_metrics(session_id)
        }

    def _record_query_optimization(self, session_id: str, query: str, execution_time: float,
                                 results_count: int, cache_hit: bool = False,
                                 success: bool = True):
        """Record query for all optimization systems"""
        # Update pattern recognizer
        self.pattern_recognizer.record_query(
            session_id, query, results_count, execution_time, success
        )

        # Update session monitor
        self.session_monitor.record_query(
            session_id, query, execution_time, results_count, cache_hit, success
        )

        # Update context manager
        self.context_manager.update_session_context(
            session_id, query, execution_time, results_count, cache_hit, success
        )

    def _perform_search(self, query: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Perform the actual search (placeholder implementation)"""
        # This would integrate with the actual chat search system
        # For now, return mock results

        return [
            {
                "id": "result_1",
                "content": f"Mock search result for '{query}'",
                "relevance_score": 0.9,
                "timestamp": time.time(),
                "metadata": {"mock": True}
            }
        ]

    def _get_session_metrics(self, session_id: str) -> dict[str, Any]:
        """Get current session metrics"""
        if session_id not in self.current_sessions:
            return {}

        session_data = self.session_monitor.active_sessions.get(session_id, {})
        recent_queries = session_data.get("queries", [])

        if not recent_queries:
            return {"query_count": 0, "avg_execution_time": 0.0}

        query_count = len(recent_queries)
        avg_time = sum(q["execution_time"] for q in recent_queries) / query_count
        cache_hits = sum(1 for q in recent_queries if q.get("cache_hit", False))
        cache_hit_rate = cache_hits / query_count

        return {
            "query_count": query_count,
            "avg_execution_time": avg_time,
            "cache_hit_rate": cache_hit_rate,
            "success_rate": sum(1 for q in recent_queries if q.get("success", False)) / query_count,
            "session_duration": time.time() - self.current_sessions[session_id]["start_time"]
        }

    def end_session(self, session_id: str) -> dict[str, Any]:
        """End a session and return comprehensive metrics"""
        if session_id not in self.current_sessions:
            return {"error": "Session not found"}

        # End monitoring and get metrics
        session_metrics = self.session_monitor.end_session(session_id)
        session_context = self.context_manager.end_session(session_id)

        # Remove from active sessions
        del self.current_sessions[session_id]

        # Generate session summary
        summary = {
            "session_id": session_id,
            "session_metrics": session_metrics.__dict__ if session_metrics else {},
            "optimization_applied": {
                "patterns_recognized": len(session_context.successful_patterns) if session_context else 0,
                "cache_efficiency": session_metrics.cache_hit_rate if session_metrics else 0,
                "context_restored": session_context.previous_session_id is not None if session_context else False
            },
            "improvements_for_next_session": self._get_session_improvements(session_metrics)
        }

        self.logger.info(f"Ended session {session_id} with comprehensive metrics")
        return summary

    def _get_session_improvements(self, session_metrics: SessionMetrics | None) -> list[str]:
        """Get improvement suggestions for next session"""
        if not session_metrics:
            return []

        improvements = []

        if session_metrics.duration_seconds and session_metrics.duration_seconds > 300:
            improvements.append("Consider breaking complex searches into multiple focused sessions")

        if session_metrics.cache_hit_rate < 0.3:
            improvements.append("Try using more consistent search terms for better cache performance")

        if session_metrics.average_query_time > 2.0:
            improvements.append("Consider using more specific search filters to reduce query time")

        if session_metrics.query_count > 20:
            improvements.append("Review search strategy - high query count may indicate inefficient approach")

        if session_metrics.optimization_score < 50:
            improvements.append("Focus on query construction and utilize provided suggestions for better results")

        return improvements

    def get_optimization_dashboard(self) -> dict[str, Any]:
        """Get real-time optimization dashboard data"""
        return self.analytics.get_dashboard_data()

    def get_comprehensive_analytics(self) -> dict[str, Any]:
        """Generate comprehensive analytics report"""
        return self.analytics.generate_comprehensive_report()

    def get_session_recommendations(self, session_id: str) -> dict[str, Any]:
        """Get real-time recommendations for active session"""
        if session_id not in self.current_sessions:
            return {"error": "Session not found"}

        # Get suggestions from all systems
        context_suggestions = self.context_manager.get_session_suggestions(session_id)
        pattern_suggestions = self.pattern_recognizer.get_intelligent_suggestions(
            "", session_id, limit=3  # Empty query to get general suggestions
        )
        session_status = self.session_monitor.get_active_session_status()

        # Combine and prioritize recommendations
        all_recommendations = []

        # Add context suggestions
        for suggestion in context_suggestions.get("query_suggestions", []):
            all_recommendations.append({
                "type": "query",
                "suggestion": suggestion["pattern"],
                "reasoning": suggestion["suggestion"],
                "priority": "medium"
            })

        # Add performance tips
        for tip in context_suggestions.get("performance_tips", []):
            all_recommendations.append({
                "type": "performance",
                "suggestion": tip["message"],
                "reasoning": "Based on current session performance",
                "priority": tip.get("priority", "low")
            })

        # Add pattern suggestions
        for suggestion in pattern_suggestions:
            all_recommendations.append({
                "type": "pattern",
                "suggestion": suggestion["suggested_query"],
                "reasoning": suggestion["reasoning"],
                "priority": "high" if suggestion["confidence"] > 0.8 else "medium"
            })

        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        all_recommendations.sort(key=lambda x: priority_order.get(x["priority"], 1), reverse=True)

        return {
            "session_id": session_id,
            "current_metrics": self._get_session_metrics(session_id),
            "recommendations": all_recommendations[:5],  # Top 5 recommendations
            "session_health": "good" if self._get_session_metrics(session_id).get("success_rate", 0) > 0.8 else "needs_attention"
        }

    def optimize_system_settings(self) -> dict[str, Any]:
        """Optimize system settings based on current performance"""
        analytics_report = self.get_comprehensive_analytics()

        optimization_settings = {
            "cache_adjustments": {},
            "pattern_recognition_adjustments": {},
            "session_monitoring_adjustments": {},
            "recommendations": []
        }

        # Analyze cache performance
        cache_stats = analytics_report["component_statistics"]["cache_performance"]
        overall_hit_rate = cache_stats.get("hit_rates", {}).get("overall", 0)

        if overall_hit_rate < 0.3:
            optimization_settings["cache_adjustments"] = {
                "increase_ttl": True,
                "enable_aggressive_preload": True,
                "expand_cache_size": True
            }
            optimization_settings["recommendations"].append(
                "Cache performance is low - enabling aggressive optimization settings"
            )

        # Analyze session patterns
        session_stats = analytics_report["component_statistics"]["session_monitoring"]
        avg_duration = session_stats.get("duration_stats", {}).get("average", 0)

        if avg_duration > 300:  # 5 minutes
            optimization_settings["session_monitoring_adjustments"] = {
                "reduce_warning_threshold": True,
                "enable_proactive_suggestions": True,
                "increase_pattern_analysis": True
            }
            optimization_settings["recommendations"].append(
                "Sessions are running long - enabling proactive optimization features"
            )

        # Apply settings to components (this would update the actual configuration)
        # For now, just return the recommendations
        return optimization_settings

    def cleanup(self):
        """Cleanup resources and save data"""
        try:
            # End all active sessions
            for session_id in list(self.current_sessions.keys()):
                self.end_session(session_id)

            # Stop background processes
            self.cache_manager.stop_preloading()

            # Save all data
            self.analytics._save_analytics_data(self.analytics.generate_comprehensive_report())

            self.logger.info("Workflow optimization system cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup on destruction"""
        try:
            self.cleanup()
        except:
            pass


# Factory function for easy instantiation
def create_optimized_search_system(cache_dir: Path | None = None) -> WorkflowOptimizedChatSearch:
    """Create an instance of the workflow-optimized chat search system"""
    return WorkflowOptimizedChatSearch(cache_dir)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')

    # Create optimized search system
    search_system = create_optimized_search_system()

    try:
        # Start a new session
        session_result = search_system.start_session(
            project_path="/example/project",
            initial_context={"task": "code_review"}
        )

        print(f"Started session: {session_result['session_id']}")
        print(f"Context restored: {session_result['context_restored']}")

        session_id = session_result["session_id"]

        # Perform some searches
        queries = [
            "How to optimize Python performance",
            "Best practices for code review",
            "Common security vulnerabilities"
        ]

        for query in queries:
            print(f"\nSearching for: {query}")
            result = search_system.search(session_id, query)
            print(f"Found {len(result['results'])} results")
            print(f"Execution time: {result['optimization_info']['execution_time']:.3f}s")
            print(f"Cache hit: {result['optimization_info']['cache_hit']}")

            if result["suggestions"]:
                print("Suggestions:")
                for suggestion in result["suggestions"]:
                    print(f"  - {suggestion['suggested_query']} (confidence: {suggestion['confidence']:.2f})")

        # Get session recommendations
        recommendations = search_system.get_session_recommendations(session_id)
        print(f"\nSession recommendations: {len(recommendations['recommendations'])}")
        for rec in recommendations["recommendations"]:
            print(f"  - {rec['suggestion']} ({rec['type']}, {rec['priority']})")

        # Get dashboard data
        dashboard = search_system.get_optimization_dashboard()
        print(f"\nOverall optimization score: {dashboard['overall_score']:.1f}")
        print(f"System status: {dashboard['status']}")

        # End session
        session_summary = search_system.end_session(session_id)
        print(f"\nSession ended with optimization score: {session_summary['session_metrics'].get('optimization_score', 0):.1f}")

        # Get comprehensive analytics
        analytics = search_system.get_comprehensive_analytics()
        print(f"\nGenerated analytics report with {len(analytics['optimization_metrics'])} metrics")

    finally:
        # Cleanup
        search_system.cleanup()
