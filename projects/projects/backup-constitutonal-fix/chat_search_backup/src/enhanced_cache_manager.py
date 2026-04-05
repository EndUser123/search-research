#!/usr/bin/env python3
"""
Enhanced Cache Manager with Predictive Preloading
Integrates with the existing multi-level cache and adds pattern-based predictive loading.
"""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Import the existing cache system
from multi_level_cache import MultiLevelCache


@dataclass
class PredictivePattern:
    """Pattern for predictive cache preloading"""
    pattern_id: str
    query_sequence: list[str]
    frequency: int
    avg_time_between: float
    confidence_score: float
    next_queries: list[str]
    preload_score: float


@dataclass
class PreloadTask:
    """Task for background cache preloading"""
    task_id: str
    query: str
    filters: dict[str, Any]
    priority: int
    created_time: float
    scheduled_time: float
    pattern_id: str | None = None


class EnhancedCacheManager(MultiLevelCache):
    """Enhanced cache manager with predictive preloading capabilities"""

    def __init__(self, cache_dir: Path, session_id: str | None = None):
        super().__init__(cache_dir, session_id)

        # Enhanced cache components
        self.patterns_file = self.cache_dir / "predictive_patterns.json"
        self.preload_queue_file = self.cache_dir / "preload_queue.json"

        # Pattern recognition and prediction
        self.predictive_patterns: dict[str, PredictivePattern] = {}
        self.query_sequences: defaultdict = defaultdict(list)
        self.preload_queue: deque[PreloadTask] = deque()

        # Background preloading
        self.preload_active = False
        self.preload_thread: threading.Thread | None = None
        self.preload_lock = threading.Lock()

        # Configuration
        self.preload_config = {
            "enabled": True,
            "max_queue_size": 100,
            "preload_delay_seconds": 2.0,
            "min_pattern_frequency": 3,
            "preload_confidence_threshold": 0.6,
            "background_preload_interval": 5.0,
            "max_preload_tasks_per_cycle": 5
        }

        self.logger = logging.getLogger(__name__ + ".Enhanced")
        self._load_predictive_patterns()
        self._start_background_preloading()

    def record_query_sequence(self, session_id: str, queries: list[str],
                            filters_list: list[dict[str, Any]]):
        """Record a sequence of queries for pattern analysis"""
        if len(queries) < 2:
            return

        timestamp = time.time()

        # Add to session query history
        for i, query in enumerate(queries):
            self.query_sequences[session_id].append({
                "query": query,
                "filters": filters_list[i] if i < len(filters_list) else {},
                "timestamp": timestamp + i
            })

        # Analyze for patterns
        self._analyze_query_patterns(session_id)

        # Trigger predictive preloading
        self._trigger_predictive_preload(queries[-1], filters_list[-1] if filters_list else {})

    def _analyze_query_patterns(self, session_id: str):
        """Analyze query sequences for predictive patterns"""
        session_queries = self.query_sequences.get(session_id, [])

        if len(session_queries) < 3:
            return

        # Look for sequential patterns
        for i in range(len(session_queries) - 2):
            seq = [
                session_queries[i]["query"],
                session_queries[i + 1]["query"],
                session_queries[i + 2]["query"]
            ]

            # Calculate time between queries
            time_diffs = [
                session_queries[i + 1]["timestamp"] - session_queries[i]["timestamp"],
                session_queries[i + 2]["timestamp"] - session_queries[i + 1]["timestamp"]
            ]
            avg_time_between = sum(time_diffs) / len(time_diffs)

            # Generate pattern key
            pattern_key = " -> ".join(seq)
            pattern_id = self._generate_pattern_id(pattern_key)

            # Update or create pattern
            if pattern_id in self.predictive_patterns:
                pattern = self.predictive_patterns[pattern_id]
                pattern.frequency += 1
                pattern.avg_time_between = (
                    (pattern.avg_time_between * (pattern.frequency - 1) + avg_time_between) /
                    pattern.frequency
                )
            else:
                pattern = PredictivePattern(
                    pattern_id=pattern_id,
                    query_sequence=seq,
                    frequency=1,
                    avg_time_between=avg_time_between,
                    confidence_score=0.1,
                    next_queries=[],
                    preload_score=0.0
                )
                self.predictive_patterns[pattern_id] = pattern

            # Look for what typically follows this pattern
            self._update_pattern_next_queries(pattern_id, session_queries, i + 3)

        # Update confidence scores and preload scores
        self._update_pattern_scores()
        self._save_predictive_patterns()

    def _update_pattern_next_queries(self, pattern_id: str, session_queries: list[dict],
                                   start_index: int):
        """Update next queries that typically follow a pattern"""
        if start_index >= len(session_queries):
            return

        pattern = self.predictive_patterns[pattern_id]
        next_query = session_queries[start_index]["query"]

        if next_query not in pattern.next_queries:
            pattern.next_queries.append(next_query)

    def _update_pattern_scores(self):
        """Update confidence and preload scores for all patterns"""
        total_patterns = len(self.predictive_patterns)
        if total_patterns == 0:
            return

        max_frequency = max(p.frequency for p in self.predictive_patterns.values())

        for pattern in self.predictive_patterns.values():
            # Confidence score based on frequency and recency
            pattern.confidence_score = min(1.0, (pattern.frequency / max_frequency) * 0.8 + 0.2)

            # Preload score based on confidence, frequency, and time between queries
            time_factor = 1.0 - min(1.0, pattern.avg_time_between / 300)  # 5 minutes max
            pattern.preload_score = pattern.confidence_score * time_factor * (pattern.frequency / 10)

    def _trigger_predictive_preload(self, current_query: str, current_filters: dict[str, Any]):
        """Trigger predictive preloading based on current query"""
        if not self.preload_config["enabled"]:
            return

        # Find matching patterns
        matching_patterns = []
        for pattern in self.predictive_patterns.values():
            if (pattern.confidence_score > self.preload_config["preload_confidence_threshold"] and
                pattern.frequency >= self.preload_config["min_pattern_frequency"]):

                # Check if current query matches pattern start
                if current_query == pattern.query_sequence[0]:
                    matching_patterns.append(pattern)

        # Sort by preload score and add next queries to preload queue
        matching_patterns.sort(key=lambda x: x.preload_score, reverse=True)

        for pattern in matching_patterns[:3]:  # Top 3 patterns
            for next_query in pattern.next_queries[:2]:  # Top 2 next queries
                if self._should_preload(next_query, current_filters):
                    self._schedule_preload(next_query, current_filters, priority=2, pattern_id=pattern.pattern_id)

    def _should_preload(self, query: str, filters: dict[str, Any]) -> bool:
        """Determine if a query should be preloaded"""
        # Don't preload very long queries
        if len(query) > 200:
            return False

        # Don't preload queries with time-specific filters
        if filters.get("session_filter") in ["today", "yesterday"]:
            return False

        # Check cache hit ratio for similar queries
        cache_stats = self.get_comprehensive_stats()
        hit_rate = cache_stats.get("hit_rates", {}).get("overall", 0)

        # Only preload if cache hit rate is reasonable (avoid filling cache with unused queries)
        return hit_rate > 0.2

    def _schedule_preload(self, query: str, filters: dict[str, Any], priority: int = 1,
                         pattern_id: str | None = None, delay: float = 0.0):
        """Schedule a query for preloading"""
        with self.preload_lock:
            if len(self.preload_queue) >= self.preload_config["max_queue_size"]:
                # Remove oldest low-priority task
                for i, task in enumerate(self.preload_queue):
                    if task.priority < priority:
                        del self.preload_queue[i]
                        break

            task_id = f"preload_{hash(query)}_{time.time()}"
            task = PreloadTask(
                task_id=task_id,
                query=query,
                filters=filters,
                priority=priority,
                created_time=time.time(),
                scheduled_time=time.time() + delay,
                pattern_id=pattern_id
            )

            # Insert task sorted by priority and scheduled time
            inserted = False
            for i, existing_task in enumerate(self.preload_queue):
                if priority > existing_task.priority or (
                    priority == existing_task.priority and
                    task.scheduled_time < existing_task.scheduled_time
                ):
                    self.preload_queue.insert(i, task)
                    inserted = True
                    break

            if not inserted:
                self.preload_queue.append(task)

        self.logger.debug(f"Scheduled preload task: {query[:30]}... (priority: {priority})")

    def _start_background_preloading(self):
        """Start background thread for cache preloading"""
        if not self.preload_config["enabled"]:
            return

        self.preload_active = True
        self.preload_thread = threading.Thread(target=self._preload_worker, daemon=True)
        self.preload_thread.start()
        self.logger.info("Background cache preloading started")

    def _preload_worker(self):
        """Background worker for cache preloading"""
        while self.preload_active:
            try:
                with self.preload_lock:
                    if not self.preload_queue:
                        time.sleep(self.preload_config["background_preload_interval"])
                        continue

                    # Get tasks ready for execution
                    ready_tasks = []
                    current_time = time.time()
                    tasks_to_remove = []

                    for i, task in enumerate(self.preload_queue):
                        if task.scheduled_time <= current_time:
                            ready_tasks.append(task)
                            tasks_to_remove.append(i)
                            if len(ready_tasks) >= self.preload_config["max_preload_tasks_per_cycle"]:
                                break

                    # Remove executed tasks from queue
                    for i in reversed(tasks_to_remove):
                        del self.preload_queue[i]

                # Execute preload tasks (outside lock)
                for task in ready_tasks:
                    self._execute_preload_task(task)

                time.sleep(self.preload_config["background_preload_interval"])

            except Exception as e:
                self.logger.error(f"Preload worker error: {e}")
                time.sleep(10)  # Brief pause on error

    def _execute_preload_task(self, task: PreloadTask):
        """Execute a single preload task"""
        try:
            start_time = time.time()

            # Check if already cached
            existing_result = self.get(task.query, task.filters)
            if existing_result:
                self.logger.debug(f"Preload hit for: {task.query[:30]}...")
                return

            # Simulate search execution (in real implementation, would call actual search)
            # For now, we'll just create a placeholder result to test caching
            placeholder_result = {
                "preloaded": True,
                "query": task.query,
                "filters": task.filters,
                "timestamp": time.time(),
                "preload_task_id": task.task_id,
                "pattern_id": task.pattern_id
            }

            # Cache the result
            self.set(task.query, task.filters, placeholder_result)

            execution_time = time.time() - start_time
            self.logger.debug(f"Preloaded: {task.query[:30]}... in {execution_time:.3f}s")

        except Exception as e:
            self.logger.error(f"Failed to execute preload task {task.task_id}: {e}")

    def get_preload_statistics(self) -> dict[str, Any]:
        """Get preload system statistics"""
        with self.preload_lock:
            queue_size = len(self.preload_queue)
            queue_priorities = defaultdict(int)
            current_time = time.time()

            for task in self.preload_queue:
                queue_priorities[task.priority] += 1

            # Ready tasks count
            ready_tasks = sum(1 for task in self.preload_queue
                            if task.scheduled_time <= current_time)

        # Pattern statistics
        total_patterns = len(self.predictive_patterns)
        high_confidence_patterns = sum(1 for p in self.predictive_patterns.values()
                                     if p.confidence_score > 0.7)
        high_score_patterns = sum(1 for p in self.predictive_patterns.values()
                                if p.preload_score > 0.5)

        return {
            "preload_enabled": self.preload_config["enabled"],
            "preload_active": self.preload_active,
            "queue_statistics": {
                "size": queue_size,
                "ready_tasks": ready_tasks,
                "max_size": self.preload_config["max_queue_size"],
                "priority_distribution": dict(queue_priorities)
            },
            "pattern_statistics": {
                "total_patterns": total_patterns,
                "high_confidence_patterns": high_confidence_patterns,
                "high_score_patterns": high_score_patterns,
                "patterns_ready_for_preload": sum(1 for p in self.predictive_patterns.values()
                                                if p.preload_score > self.preload_config["preload_confidence_threshold"])
            },
            "configuration": self.preload_config
        }

    def optimize_preload_strategy(self, session_data: dict | None = None) -> dict[str, Any]:
        """Analyze preload effectiveness and suggest optimizations"""
        stats = self.get_preload_statistics()
        cache_stats = self.get_comprehensive_stats()

        optimizations = {
            "current_performance": {},
            "recommendations": [],
            "effectiveness_metrics": {}
        }

        # Current performance
        overall_hit_rate = cache_stats.get("hit_rates", {}).get("overall", 0)
        optimizations["current_performance"] = {
            "cache_hit_rate": overall_hit_rate,
            "preload_queue_size": stats["queue_statistics"]["size"],
            "active_patterns": stats["pattern_statistics"]["high_score_patterns"]
        }

        # Effectiveness metrics
        if overall_hit_rate > 0.5:
            optimizations["effectiveness_metrics"]["preload_effectiveness"] = "good"
        elif overall_hit_rate > 0.3:
            optimizations["effectiveness_metrics"]["preload_effectiveness"] = "moderate"
        else:
            optimizations["effectiveness_metrics"]["preload_effectiveness"] = "poor"

        # Generate recommendations
        if stats["queue_statistics"]["size"] > stats["queue_statistics"]["max_size"] * 0.8:
            optimizations["recommendations"].append({
                "issue": "Preload queue nearly full",
                "recommendation": "Increase preload confidence threshold or reduce pattern frequency threshold",
                "impact": "Medium"
            })

        if stats["pattern_statistics"]["high_confidence_patterns"] < 5:
            optimizations["recommendations"].append({
                "issue": "Few high-confidence patterns available",
                "recommendation": "Collect more query data before enabling predictive preloading",
                "impact": "High"
            })

        if overall_hit_rate < 0.3:
            optimizations["recommendations"].append({
                "issue": "Low cache hit rate despite preloading",
                "recommendation": "Review pattern matching accuracy and preload timing",
                "impact": "High"
            })

        if not stats["preload_active"]:
            optimizations["recommendations"].append({
                "issue": "Background preloading not active",
                "recommendation": "Enable background preloading for better cache warmup",
                "impact": "High"
            })

        return optimizations

    def _generate_pattern_id(self, pattern_key: str) -> str:
        """Generate pattern ID from pattern key"""
        import hashlib
        return hashlib.md5(pattern_key.encode()).hexdigest()[:12]

    def _load_predictive_patterns(self):
        """Load predictive patterns from file"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file) as f:
                    data = json.load(f)
                    for pattern_data in data.get('patterns', []):
                        pattern = PredictivePattern(**pattern_data)
                        self.predictive_patterns[pattern.pattern_id] = pattern
                self.logger.debug(f"Loaded {len(self.predictive_patterns)} predictive patterns")
            except Exception as e:
                self.logger.error(f"Failed to load predictive patterns: {e}")

    def _save_predictive_patterns(self):
        """Save predictive patterns to file"""
        try:
            data = {
                'last_updated': time.time(),
                'patterns': [asdict(pattern) for pattern in self.predictive_patterns.values()]
            }
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save predictive patterns: {e}")

    def preload_contextual_queries(self, context: dict[str, Any], limit: int = 5):
        """Preload queries based on current context"""
        if not context or not self.preload_config["enabled"]:
            return

        # Extract relevant context information
        project = context.get("project", "")
        recent_topics = context.get("recent_topics", [])
        current_task = context.get("current_task", "")

        # Generate contextual queries
        contextual_queries = []

        if project:
            contextual_queries.extend([
                f"{project} overview",
                f"{project} setup",
                f"{project} configuration"
            ])

        for topic in recent_topics[:3]:
            contextual_queries.extend([
                f"{topic} tutorial",
                f"{topic} examples",
                f"{topic} best practices"
            ])

        if current_task:
            contextual_queries.extend([
                f"{current_task} help",
                f"how to {current_task}",
                f"{current_task} troubleshooting"
            ])

        # Schedule preloading for contextual queries
        for query in contextual_queries[:limit]:
            filters = {"context_filter": "all", "session_filter": "all", "rank_by": "relevance"}
            self._schedule_preload(query, filters, priority=1, delay=1.0)

    def stop_preloading(self):
        """Stop background preloading"""
        self.preload_active = False
        if self.preload_thread:
            self.preload_thread.join(timeout=5)
        self.logger.info("Background cache preloading stopped")

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.stop_preloading()
        except:
            pass
