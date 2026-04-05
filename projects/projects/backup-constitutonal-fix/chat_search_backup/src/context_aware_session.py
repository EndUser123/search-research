#!/usr/bin/env python3
"""
Context-Aware Session Initialization
Provides intelligent session initialization with persistent context restoration.
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SessionContext:
    """Complete session context for restoration"""
    session_id: str
    previous_session_id: str | None
    session_start_time: float
    last_activity_time: float
    project_context: dict[str, Any]
    recent_queries: list[dict[str, Any]]
    successful_patterns: list[str]
    user_preferences: dict[str, Any]
    task_progress: dict[str, Any]
    knowledge_state: dict[str, Any]
    performance_metrics: dict[str, float]


@dataclass
class ContextSnapshot:
    """Snapshot of context for restoration"""
    snapshot_id: str
    session_id: str
    timestamp: float
    context_data: dict[str, Any]
    restoration_score: float
    expiration_time: float


class ContextAwareSessionManager:
    """Manages context-aware session initialization and restoration"""

    def __init__(self, cache_dir: Path, max_sessions: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_sessions = max_sessions

        # Data files
        self.contexts_file = self.cache_dir / "session_contexts.json"
        self.snapshots_file = self.cache_dir / "context_snapshots.json"
        self.preferences_file = self.cache_dir / "user_preferences.json"

        # Session management
        self.active_contexts: dict[str, SessionContext] = {}
        self.context_history: list[SessionContext] = []
        self.context_snapshots: list[ContextSnapshot] = []

        # User preferences and learning
        self.user_preferences: dict[str, Any] = {}
        self.learned_patterns: dict[str, float] = {}

        # Configuration
        self.config = {
            "context_retention_days": 30,
            "snapshot_interval_minutes": 10,
            "auto_restore_threshold": 0.7,
            "max_snapshots_per_session": 50,
            "context_similarity_threshold": 0.6
        }

        self.logger = logging.getLogger(__name__)
        self._load_contexts()
        self._load_preferences()
        self._cleanup_expired_data()

    def initialize_session(self, session_id: str, project_path: str | None = None,
                          initial_context: dict[str, Any] | None = None) -> SessionContext:
        """Initialize a new session with context awareness"""
        current_time = time.time()

        # Find best context to restore
        restored_context = self._find_best_context_to_restore(
            session_id, project_path, initial_context
        )

        if restored_context:
            # Create new session based on restored context
            new_context = SessionContext(
                session_id=session_id,
                previous_session_id=restored_context.session_id,
                session_start_time=current_time,
                last_activity_time=current_time,
                project_context=restored_context.project_context.copy(),
                recent_queries=restored_context.recent_queries[-10:],  # Last 10 queries
                successful_patterns=restored_context.successful_patterns.copy(),
                user_preferences=restored_context.user_preferences.copy(),
                task_progress=restored_context.task_progress.copy(),
                knowledge_state=restored_context.knowledge_state.copy(),
                performance_metrics=restored_context.performance_metrics.copy()
            )

            self.logger.info(f"Session {session_id} initialized with context from {restored_context.session_id}")
        else:
            # Create fresh session context
            new_context = SessionContext(
                session_id=session_id,
                previous_session_id=None,
                session_start_time=current_time,
                last_activity_time=current_time,
                project_context=self._extract_project_context(project_path),
                recent_queries=[],
                successful_patterns=[],
                user_preferences=self.user_preferences.copy(),
                task_progress={},
                knowledge_state={},
                performance_metrics={
                    "avg_query_time": 0.0,
                    "cache_hit_rate": 0.0,
                    "success_rate": 1.0,
                    "optimization_score": 100.0
                }
            )

            self.logger.info(f"Session {session_id} initialized with fresh context")

        # Add to active contexts
        self.active_contexts[session_id] = new_context

        # Save context
        self._save_context(new_context)

        return new_context

    def _find_best_context_to_restore(self, session_id: str, project_path: str | None,
                                    initial_context: dict[str, Any] | None) -> SessionContext | None:
        """Find the best context to restore for the new session"""
        if not self.context_history:
            return None

        candidates = []
        current_project = self._extract_project_context(project_path)

        for context in self.context_history:
            # Skip very old contexts
            age_days = (time.time() - context.last_activity_time) / (24 * 3600)
            if age_days > self.config["context_retention_days"]:
                continue

            # Calculate restoration score
            similarity_score = self._calculate_context_similarity(
                current_project, context.project_context
            )

            time_decay = max(0.1, 1.0 - (age_days / self.config["context_retention_days"]))
            performance_boost = context.performance_metrics.get("optimization_score", 50) / 100

            restoration_score = (
                similarity_score * 0.4 +
                time_decay * 0.3 +
                performance_boost * 0.3
            )

            if restoration_score >= self.config["auto_restore_threshold"]:
                candidates.append((context, restoration_score))

        # Return best candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    def _calculate_context_similarity(self, current_context: dict[str, Any],
                                    historical_context: dict[str, Any]) -> float:
        """Calculate similarity between current and historical contexts"""
        similarity_score = 0.0
        factors = 0

        # Project path similarity
        current_project = current_context.get("project_path", "")
        historical_project = historical_context.get("project_path", "")
        if current_project and historical_project:
            if current_project == historical_project:
                similarity_score += 1.0
            elif current_project in historical_project or historical_project in current_project:
                similarity_score += 0.6
            factors += 1

        # Recent queries similarity
        current_recent = current_context.get("recent_queries", [])
        historical_recent = historical_context.get("recent_queries", [])
        if current_recent and historical_recent:
            query_similarity = self._calculate_query_similarity(current_recent, historical_recent)
            similarity_score += query_similarity
            factors += 1

        # Successful patterns similarity
        current_patterns = set(current_context.get("successful_patterns", []))
        historical_patterns = set(historical_context.get("successful_patterns", []))
        if current_patterns and historical_patterns:
            pattern_overlap = len(current_patterns & historical_patterns)
            pattern_union = len(current_patterns | historical_patterns)
            pattern_similarity = pattern_overlap / max(pattern_union, 1)
            similarity_score += pattern_similarity
            factors += 1

        return similarity_score / max(factors, 1)

    def _calculate_query_similarity(self, queries1: list[dict], queries2: list[dict]) -> float:
        """Calculate similarity between query lists"""
        if not queries1 or not queries2:
            return 0.0

        # Extract normalized queries
        norm_queries1 = [self._normalize_query(q.get("query", "")) for q in queries1]
        norm_queries2 = [self._normalize_query(q.get("query", "")) for q in queries2]

        # Calculate Jaccard similarity
        set1 = set(norm_queries1)
        set2 = set(norm_queries2)

        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union)

    def _normalize_query(self, query: str) -> str:
        """Normalize query for comparison"""
        import re
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = ' '.join(word for word in normalized.split() if len(word) > 2)
        return normalized

    def _extract_project_context(self, project_path: str | None) -> dict[str, Any]:
        """Extract context information from project path"""
        context = {
            "project_path": project_path or "",
            "project_name": "",
            "project_type": "",
            "last_modified": 0.0,
            "relevant_files": [],
            "dependencies": []
        }

        if project_path and Path(project_path).exists():
            path = Path(project_path)

            # Extract project name
            context["project_name"] = path.name

            # Determine project type
            if (path / "package.json").exists():
                context["project_type"] = "nodejs"
            elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
                context["project_type"] = "python"
            elif (path / "Cargo.toml").exists():
                context["project_type"] = "rust"
            elif (path / "go.mod").exists():
                context["project_type"] = "golang"
            else:
                context["project_type"] = "unknown"

            # Get last modified time
            try:
                context["last_modified"] = max(
                    f.stat().st_mtime for f in path.rglob("*") if f.is_file()
                )
            except:
                context["last_modified"] = 0.0

        return context

    def update_session_context(self, session_id: str, query: str, execution_time: float,
                            results_count: int, cache_hit: bool = False,
                            success: bool = True, context_data: dict | None = None):
        """Update session context with new query information"""
        if session_id not in self.active_contexts:
            self.logger.warning(f"Session {session_id} not found in active contexts")
            return

        context = self.active_contexts[session_id]
        current_time = time.time()

        # Update basic metrics
        context.last_activity_time = current_time

        # Add query to recent queries
        query_record = {
            "timestamp": current_time,
            "query": query,
            "execution_time": execution_time,
            "results_count": results_count,
            "cache_hit": cache_hit,
            "success": success
        }
        context.recent_queries.append(query_record)

        # Keep only recent queries (last 50)
        if len(context.recent_queries) > 50:
            context.recent_queries = context.recent_queries[-50:]

        # Update performance metrics
        self._update_performance_metrics(context)

        # Learn from successful queries
        if success and results_count > 0:
            self._learn_from_query(context, query, context_data)

        # Create context snapshot periodically
        if len(context.recent_queries) % 10 == 0:  # Every 10 queries
            self._create_context_snapshot(session_id, context)

        # Save updated context
        self._save_context(context)

    def _update_performance_metrics(self, context: SessionContext):
        """Update performance metrics for the session"""
        if not context.recent_queries:
            return

        recent_queries = context.recent_queries[-20:]  # Last 20 queries

        # Average query time
        avg_time = sum(q["execution_time"] for q in recent_queries) / len(recent_queries)
        context.performance_metrics["avg_query_time"] = avg_time

        # Cache hit rate
        cache_hits = sum(1 for q in recent_queries if q["cache_hit"])
        context.performance_metrics["cache_hit_rate"] = cache_hits / len(recent_queries)

        # Success rate
        successful_queries = sum(1 for q in recent_queries if q["success"])
        context.performance_metrics["success_rate"] = successful_queries / len(recent_queries)

        # Optimization score (simplified calculation)
        time_score = max(0, 100 - (avg_time * 10))  # Lower time is better
        cache_score = context.performance_metrics["cache_hit_rate"] * 50
        success_score = context.performance_metrics["success_rate"] * 30

        context.performance_metrics["optimization_score"] = (time_score + cache_score + success_score) / 1.3

    def _learn_from_query(self, context: SessionContext, query: str,
                         context_data: dict | None = None):
        """Learn from successful queries"""
        # Add to successful patterns
        normalized_query = self._normalize_query(query)
        if normalized_query not in context.successful_patterns:
            context.successful_patterns.append(normalized_query)

        # Keep only recent successful patterns
        if len(context.successful_patterns) > 100:
            context.successful_patterns = context.successful_patterns[-100:]

        # Update global learned patterns
        self.learned_patterns[normalized_query] = (
            self.learned_patterns.get(normalized_query, 0) + 1
        )

        # Update task progress if context data provided
        if context_data:
            task_type = context_data.get("task_type", "general")
            if task_type not in context.task_progress:
                context.task_progress[task_type] = {"count": 0, "success_rate": 1.0}

            context.task_progress[task_type]["count"] += 1

    def _create_context_snapshot(self, session_id: str, context: SessionContext):
        """Create a snapshot of current context for future restoration"""
        snapshot_id = hashlib.md5(f"{session_id}{time.time()}".encode()).hexdigest()[:12]

        snapshot_data = {
            "project_context": context.project_context.copy(),
            "recent_queries": context.recent_queries.copy(),
            "successful_patterns": context.successful_patterns.copy(),
            "task_progress": context.task_progress.copy(),
            "knowledge_state": context.knowledge_state.copy(),
            "performance_metrics": context.performance_metrics.copy()
        }

        snapshot = ContextSnapshot(
            snapshot_id=snapshot_id,
            session_id=session_id,
            timestamp=time.time(),
            context_data=snapshot_data,
            restoration_score=context.performance_metrics.get("optimization_score", 50),
            expiration_time=time.time() + (self.config["context_retention_days"] * 24 * 3600)
        )

        self.context_snapshots.append(snapshot)

        # Limit snapshots per session
        session_snapshots = [s for s in self.context_snapshots if s.session_id == session_id]
        if len(session_snapshots) > self.config["max_snapshots_per_session"]:
            # Remove oldest snapshot for this session
            oldest_snapshot = min(session_snapshots, key=lambda x: x.timestamp)
            self.context_snapshots = [s for s in self.context_snapshots if s.snapshot_id != oldest_snapshot.snapshot_id]

        self.logger.debug(f"Created context snapshot {snapshot_id} for session {session_id}")

    def get_session_suggestions(self, session_id: str) -> dict[str, Any]:
        """Get contextual suggestions for the current session"""
        if session_id not in self.active_contexts:
            return {"error": "Session not found"}

        context = self.active_contexts[session_id]
        suggestions = {
            "query_suggestions": [],
            "context_insights": [],
            "performance_tips": [],
            "related_patterns": []
        }

        # Query suggestions based on successful patterns
        if context.successful_patterns:
            # Suggest variations of successful queries
            top_patterns = context.successful_patterns[-10:]  # Recent successful patterns
            suggestions["query_suggestions"] = [
                {
                    "pattern": pattern,
                    "suggestion": f"Try similar queries to '{pattern}' which was successful before",
                    "confidence": 0.7
                }
                for pattern in top_patterns[:5]
            ]

        # Context insights
        if context.project_context.get("project_name"):
            project_name = context.project_context["project_name"]
            suggestions["context_insights"].append({
                "type": "project_context",
                "message": f"Working on {project_name} ({context.project_context.get('project_type', 'unknown')} project)",
                "actionable": True
            })

        # Performance tips
        opt_score = context.performance_metrics.get("optimization_score", 0)
        if opt_score < 70:
            suggestions["performance_tips"].append({
                "type": "optimization",
                "message": "Session optimization score is low. Consider using more specific search terms.",
                "priority": "medium"
            })

        cache_rate = context.performance_metrics.get("cache_hit_rate", 0)
        if cache_rate < 0.3:
            suggestions["performance_tips"].append({
                "type": "cache",
                "message": "Low cache hit rate. Try using consistent search terms for better performance.",
                "priority": "low"
            })

        # Related patterns from learned data
        if context.recent_queries:
            last_query = context.recent_queries[-1]["query"]
            related_patterns = self._find_related_patterns(last_query)
            suggestions["related_patterns"] = related_patterns[:3]

        return suggestions

    def _find_related_patterns(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find patterns related to the given query"""
        normalized_query = self._normalize_query(query)
        related = []

        for pattern, frequency in self.learned_patterns.items():
            if pattern == normalized_query:
                continue

            # Simple similarity check (could be enhanced with more sophisticated NLP)
            query_words = set(normalized_query.split())
            pattern_words = set(pattern.split())

            if query_words and pattern_words:
                overlap = len(query_words & pattern_words)
                if overlap > 0:
                    similarity = overlap / len(query_words | pattern_words)
                    if similarity > 0.2:  # Minimum similarity threshold
                        related.append({
                            "pattern": pattern,
                            "frequency": frequency,
                            "similarity": similarity,
                            "suggestion": f"Related pattern used {frequency} times before"
                        })

        # Sort by frequency and similarity
        related.sort(key=lambda x: (x["frequency"] * x["similarity"]), reverse=True)
        return related[:limit]

    def end_session(self, session_id: str) -> SessionContext | None:
        """End a session and preserve context"""
        if session_id not in self.active_contexts:
            self.logger.warning(f"Session {session_id} not found in active contexts")
            return None

        context = self.active_contexts[session_id]
        context.last_activity_time = time.time()

        # Move to history
        self.context_history.append(context)

        # Limit history size
        if len(self.context_history) > self.max_sessions:
            self.context_history = self.context_history[-self.max_sessions:]

        # Remove from active contexts
        del self.active_contexts[session_id]

        # Create final snapshot
        self._create_context_snapshot(session_id, context)

        # Save to file
        self._save_all_contexts()

        self.logger.info(f"Session {session_id} ended and context preserved")
        return context

    def get_context_statistics(self) -> dict[str, Any]:
        """Get statistics about context management"""
        total_sessions = len(self.context_history) + len(self.active_contexts)

        # Calculate average metrics
        if self.context_history:
            avg_optimization = sum(
                ctx.performance_metrics.get("optimization_score", 0)
                for ctx in self.context_history
            ) / len(self.context_history)

            avg_session_duration = sum(
                ctx.last_activity_time - ctx.session_start_time
                for ctx in self.context_history
            ) / len(self.context_history)
        else:
            avg_optimization = 0
            avg_session_duration = 0

        return {
            "total_sessions": total_sessions,
            "active_sessions": len(self.active_contexts),
            "context_snapshots": len(self.context_snapshots),
            "learned_patterns": len(self.learned_patterns),
            "average_optimization_score": avg_optimization,
            "average_session_duration": avg_session_duration,
            "configuration": self.config
        }

    def _load_contexts(self):
        """Load session contexts from file"""
        if self.contexts_file.exists():
            try:
                with open(self.contexts_file) as f:
                    data = json.load(f)
                    for context_data in data.get('contexts', []):
                        context = SessionContext(**context_data)
                        self.context_history.append(context)
                self.logger.debug(f"Loaded {len(self.context_history)} session contexts")
            except Exception as e:
                self.logger.error(f"Failed to load session contexts: {e}")

    def _load_preferences(self):
        """Load user preferences from file"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file) as f:
                    data = json.load(f)
                    self.user_preferences = data.get('preferences', {})
                    self.learned_patterns = data.get('learned_patterns', {})
                self.logger.debug(f"Loaded user preferences and {len(self.learned_patterns)} learned patterns")
            except Exception as e:
                self.logger.error(f"Failed to load user preferences: {e}")

    def _save_context(self, context: SessionContext):
        """Save a single context to memory"""
        # Update in history if it exists
        for i, existing_context in enumerate(self.context_history):
            if existing_context.session_id == context.session_id:
                self.context_history[i] = context
                break

        # Save periodically
        if len(self.context_history) % 10 == 0:
            self._save_all_contexts()

    def _save_all_contexts(self):
        """Save all contexts to file"""
        try:
            data = {
                'last_updated': time.time(),
                'contexts': [asdict(context) for context in self.context_history],
                'snapshots': [asdict(snapshot) for snapshot in self.context_snapshots]
            }
            with open(self.contexts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save session contexts: {e}")

        # Save preferences and learned patterns
        try:
            pref_data = {
                'last_updated': time.time(),
                'preferences': self.user_preferences,
                'learned_patterns': self.learned_patterns
            }
            with open(self.preferences_file, 'w') as f:
                json.dump(pref_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save user preferences: {e}")

    def _cleanup_expired_data(self):
        """Clean up expired context snapshots"""
        current_time = time.time()
        original_count = len(self.context_snapshots)

        self.context_snapshots = [
            snapshot for snapshot in self.context_snapshots
            if snapshot.expiration_time > current_time
        ]

        removed_count = original_count - len(self.context_snapshots)
        if removed_count > 0:
            self.logger.debug(f"Cleaned up {removed_count} expired context snapshots")
