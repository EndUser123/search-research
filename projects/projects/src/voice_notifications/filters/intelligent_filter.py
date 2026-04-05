"""
Intelligent Notification Filter System
Provides context-aware filtering without explicit user feedback
"""

import hashlib
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..config.config_manager import VoiceNotificationSystemConfig

logger = logging.getLogger(__name__)

class FilterDecision(Enum):
    """Filter decision types"""
    ALLOW = "allow"
    FILTER_FREQUENCY = "filter_frequency"
    FILTER_SESSION = "filter_session"
    FILTER_BEHAVIOR = "filter_behavior"
    FILTER_CONTEXT = "filter_context"
    FILTER_PRIORITY = "filter_priority"

@dataclass
class NotificationContext:
    """Context information for a notification"""
    notification_type: str
    task_name: str
    session_id: str
    timestamp: datetime
    priority: str = "normal"
    tool_name: str | None = None
    requires_interaction: bool = False
    content_hash: str | None = None

@dataclass
class FilterResult:
    """Result of filtering a notification"""
    decision: FilterDecision
    confidence: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionMetrics:
    """Metrics for a specific session"""
    session_id: str
    start_time: datetime
    notification_count: int = 0
    last_notification_time: datetime | None = None
    notifications_by_type: dict[str, int] = field(default_factory=dict)
    interaction_requests: int = 0
    filter_violations: int = 0
    session_activity_score: float = 0.0

@dataclass
class BehavioralProfile:
    """Learned behavioral profile for notification filtering"""
    session_patterns: dict[str, float] = field(default_factory=dict)
    temporal_patterns: dict[int, float] = field(default_factory=dict)  # hour of day -> activity
    task_complexity_scores: dict[str, float] = field(default_factory=dict)
    notification_responses: dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

class IntelligentNotificationFilter:
    """
    Intelligent notification filtering system that learns user behavior
    without explicit feedback loops
    """

    def __init__(self, config: VoiceNotificationSystemConfig):
        self.config = config
        self.filter_config = config.intelligent_filter
        self.enabled = self.filter_config.enabled

        # Thread safety
        self._lock = threading.RLock()

        # Session tracking
        self.active_sessions: dict[str, SessionMetrics] = {}
        self.session_cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

        # Behavioral learning
        self.behavioral_profile = BehavioralProfile()
        self.profile_file = Path("P:/hooks/voice_notification_profile.json")
        self._load_behavioral_profile()

        # Frequency tracking
        self.notification_history: deque = deque(maxlen=1000)
        self.hourly_notification_counts: dict[int, int] = defaultdict(int)
        self._last_hourly_reset = datetime.now().replace(minute=0, second=0, microsecond=0)

        # Context analysis
        self.context_cache: dict[str, float] = {}
        self.context_cache_ttl = 3600  # 1 hour
        self.deduplication_cache: dict[str, datetime] = {}
        self.dedup_window = timedelta(minutes=5)

        # Performance metrics
        self.filter_metrics = {
            'total_filtered': 0,
            'total_allowed': 0,
            'filter_reasons': defaultdict(int),
            'avg_filter_time_ms': 0.0,
            'filter_times': deque(maxlen=100)
        }

    def _load_behavioral_profile(self) -> None:
        """Load behavioral profile from disk"""
        try:
            if self.profile_file.exists():
                with open(self.profile_file, encoding='utf-8') as f:
                    data = json.load(f)
                    self.behavioral_profile = BehavioralProfile(**data)
                    logger.info("Behavioral profile loaded successfully")
            else:
                logger.info("No existing behavioral profile found, starting fresh")
        except Exception as e:
            logger.warning(f"Error loading behavioral profile: {e}, using defaults")

    def _save_behavioral_profile(self) -> None:
        """Save behavioral profile to disk"""
        try:
            # Ensure directory exists
            self.profile_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.behavioral_profile), f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error saving behavioral profile: {e}")

    def should_filter_notification(self, context: NotificationContext) -> FilterResult:
        """
        Main filtering decision method
        Returns FilterResult with decision and reasoning
        """
        start_time = time.time()

        try:
            if not self.enabled:
                return FilterResult(FilterDecision.ALLOW, 1.0, "Filtering disabled")

            # Clean up old sessions periodically
            self._cleanup_old_sessions()

            # Update session metrics
            self._update_session_metrics(context)

            # Apply filtering rules in order of priority
            result = self._check_priority_exemption(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            result = self._check_frequency_limits(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            result = self._check_session_limits(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            result = self._check_behavioral_patterns(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            result = self._check_context_relevance(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            # Check for duplicate content
            result = self._check_content_deduplication(context)
            if result.decision != FilterDecision.ALLOW:
                return result

            # Notification passed all filters
            self._record_notification_allowed(context)
            return FilterResult(FilterDecision.ALLOW, 0.9, "Notification allowed")

        except Exception as e:
            logger.error(f"Error in filtering logic: {e}")
            return FilterResult(FilterDecision.ALLOW, 0.5, f"Filtering error: {e}")

        finally:
            # Record performance metrics
            filter_time = (time.time() - start_time) * 1000
            self._record_filter_performance(filter_time)

    def _check_priority_exemption(self, context: NotificationContext) -> FilterResult:
        """Check if notification is exempt from filtering due to priority"""
        if self.filter_config.exempt_high_priority and context.priority in ["high", "critical"]:
            return FilterResult(FilterDecision.ALLOW, 1.0, f"Exempt due to {context.priority} priority")

        if context.requires_interaction:
            return FilterResult(FilterDecision.ALLOW, 1.0, "Requires user interaction")

        return FilterResult(FilterDecision.ALLOW, 0.0, "Priority check passed")

    def _check_frequency_limits(self, context: NotificationContext) -> FilterResult:
        """Check if notification exceeds frequency limits"""
        if not self.filter_config.frequency_limits:
            return FilterResult(FilterDecision.ALLOW, 0.0, "Frequency limits disabled")

        # Check per-hour limit
        current_hour = datetime.now().hour
        self._reset_hourly_counts_if_needed()

        hourly_count = self.hourly_notification_counts.get(current_hour, 0)
        if hourly_count >= self.filter_config.max_notifications_per_hour:
            return FilterResult(
                FilterDecision.FILTER_FREQUENCY,
                0.8,
                f"Hourly limit exceeded: {hourly_count}/{self.filter_config.max_notifications_per_hour}"
            )

        # Check per-type frequency
        notif_config = self.config.get_notification_config(context.notification_type)
        if notif_config:
            recent_same_type = self._count_recent_notifications(
                context.notification_type,
                timedelta(hours=1)
            )
            if recent_same_type >= notif_config.max_frequency_per_hour:
                return FilterResult(
                    FilterDecision.FILTER_FREQUENCY,
                    0.7,
                    f"Type frequency limit exceeded: {recent_same_type}/{notif_config.max_frequency_per_hour}"
                )

        return FilterResult(FilterDecision.ALLOW, 0.0, "Frequency limits passed")

    def _check_session_limits(self, context: NotificationContext) -> FilterResult:
        """Check if session has exceeded notification limits"""
        if not self.filter_config.session_isolation:
            return FilterResult(FilterDecision.ALLOW, 0.0, "Session isolation disabled")

        session_metrics = self.active_sessions.get(context.session_id)
        if not session_metrics:
            return FilterResult(FilterDecision.ALLOW, 0.0, "New session")

        # Check per-session limit
        if session_metrics.notification_count >= self.filter_config.max_notifications_per_session:
            return FilterResult(
                FilterDecision.FILTER_SESSION,
                0.9,
                f"Session limit exceeded: {session_metrics.notification_count}/{self.filter_config.max_notifications_per_session}"
            )

        # Check session timeout
        session_duration = datetime.now() - session_metrics.start_time
        if session_duration > timedelta(minutes=self.filter_config.session_timeout_minutes):
            return FilterResult(
                FilterDecision.FILTER_SESSION,
                0.6,
                f"Session timeout: {session_duration}"
            )

        return FilterResult(FilterDecision.ALLOW, 0.0, "Session limits passed")

    def _check_behavioral_patterns(self, context: NotificationContext) -> FilterResult:
        """Check against learned behavioral patterns"""
        if not self.filter_config.behavioral_filtering:
            return FilterResult(FilterDecision.ALLOW, 0.0, "Behavioral filtering disabled")

        # Calculate session activity score
        session_score = self._calculate_session_activity_score(context.session_id)
        if session_score < 0.2:  # Low activity session
            return FilterResult(
                FilterDecision.FILTER_BEHAVIOR,
                0.5,
                f"Low session activity: {session_score:.2f}"
            )

        # Check temporal patterns
        temporal_score = self._get_temporal_activity_score(context.timestamp.hour)
        if temporal_score < 0.1:  # Unusual time for notifications
            return FilterResult(
                FilterDecision.FILTER_BEHAVIOR,
                0.3,
                f"Unusual time: {context.timestamp.hour} (score: {temporal_score:.2f})"
            )

        # Check task complexity appropriateness
        if context.task_name:
            complexity_score = self._get_task_complexity_score(context.task_name)
            if complexity_score < 0.3 and context.priority != "high":
                return FilterResult(
                    FilterDecision.FILTER_BEHAVIOR,
                    0.4,
                    f"Low complexity task: {complexity_score:.2f}"
                )

        return FilterResult(FilterDecision.ALLOW, 0.0, "Behavioral patterns passed")

    def _check_context_relevance(self, context: NotificationContext) -> FilterResult:
        """Check notification context relevance"""
        if not self.filter_config.context_analysis:
            return FilterResult(FilterDecision.ALLOW, 0.0, "Context analysis disabled")

        # Generate context signature
        context_hash = self._generate_context_hash(context)

        # Check cache first
        if context_hash in self.context_cache:
            relevance_score = self.context_cache[context_hash]
            if relevance_score < self.filter_config.filter_strength:
                return FilterResult(
                    FilterDecision.FILTER_CONTEXT,
                    0.5,
                    f"Low relevance score: {relevance_score:.2f}"
                )
        else:
            # Calculate relevance score
            relevance_score = self._calculate_context_relevance(context)
            self.context_cache[context_hash] = relevance_score

            # Clean old cache entries
            self._cleanup_context_cache()

        if relevance_score < self.filter_config.filter_strength:
            return FilterResult(
                FilterDecision.FILTER_CONTEXT,
                0.6,
                f"Context filtered: {relevance_score:.2f} < {self.filter_config.filter_strength}"
            )

        return FilterResult(FilterDecision.ALLOW, 0.0, "Context analysis passed")

    def _check_content_deduplication(self, context: NotificationContext) -> FilterResult:
        """Check for duplicate content within deduplication window"""
        content_hash = context.content_hash or self._generate_content_hash(context)
        now = datetime.now()

        if content_hash in self.deduplication_cache:
            last_seen = self.deduplication_cache[content_hash]
            if now - last_seen < self.dedup_window:
                return FilterResult(
                    FilterDecision.FILTER_CONTEXT,
                    0.8,
                    f"Duplicate content: last seen {last_seen}"
                )

        # Update deduplication cache
        self.deduplication_cache[content_hash] = now
        self._cleanup_deduplication_cache()

        return FilterResult(FilterDecision.ALLOW, 0.0, "Content deduplication passed")

    def _update_session_metrics(self, context: NotificationContext) -> None:
        """Update session metrics with new notification"""
        with self._lock:
            if context.session_id not in self.active_sessions:
                self.active_sessions[context.session_id] = SessionMetrics(
                    session_id=context.session_id,
                    start_time=context.timestamp
                )

            session = self.active_sessions[context.session_id]
            session.notification_count += 1
            session.last_notification_time = context.timestamp
            session.notifications_by_type[context.notification_type] = (
                session.notifications_by_type.get(context.notification_type, 0) + 1
            )

            if context.requires_interaction:
                session.interaction_requests += 1

            # Update activity score
            session.session_activity_score = self._calculate_session_activity_score(context.session_id)

            # Update behavioral profile
            if self.filter_config.learning_enabled:
                self._update_behavioral_profile(context)

    def _calculate_session_activity_score(self, session_id: str) -> float:
        """Calculate activity score for a session (0.0 to 1.0)"""
        session = self.active_sessions.get(session_id)
        if not session:
            return 0.0

        # Factors for activity score
        notification_frequency = min(session.notification_count / 10.0, 1.0)  # Normalized to 10 notifications
        type_diversity = len(session.notifications_by_type) / 5.0  # Normalized to 5 types
        interaction_ratio = session.interaction_requests / max(session.notification_count, 1)

        # Calculate weighted score
        score = (notification_frequency * 0.4 +
                type_diversity * 0.3 +
                interaction_ratio * 0.3)

        return min(score, 1.0)

    def _get_temporal_activity_score(self, hour: int) -> float:
        """Get temporal activity score for a given hour"""
        return self.behavioral_profile.temporal_patterns.get(hour, 0.5)

    def _get_task_complexity_score(self, task_name: str) -> float:
        """Get complexity score for a task"""
        # Simple heuristic based on task name characteristics
        complexity_indicators = [
            'implement', 'create', 'build', 'develop', 'design',
            'optimize', 'refactor', 'migrate', 'integrate', 'deploy'
        ]

        task_lower = task_name.lower()
        score = 0.0

        for indicator in complexity_indicators:
            if indicator in task_lower:
                score += 0.2

        # Add score for task name length (longer names often more complex)
        score += min(len(task_name) / 50.0, 0.3)

        return min(score, 1.0)

    def _calculate_context_relevance(self, context: NotificationContext) -> float:
        """Calculate relevance score for notification context"""
        score = 0.0

        # Priority factor
        priority_scores = {"low": 0.2, "normal": 0.5, "high": 0.8, "critical": 1.0}
        score += priority_scores.get(context.priority, 0.5) * 0.3

        # Task name complexity factor
        if context.task_name:
            complexity_score = self._get_task_complexity_score(context.task_name)
            score += complexity_score * 0.2

        # Session activity factor
        if context.session_id:
            activity_score = self._calculate_session_activity_score(context.session_id)
            score += activity_score * 0.3

        # Temporal factor
        temporal_score = self._get_temporal_activity_score(context.timestamp.hour)
        score += temporal_score * 0.2

        return min(score, 1.0)

    def _update_behavioral_profile(self, context: NotificationContext) -> None:
        """Update behavioral profile with new notification data"""
        profile = self.behavioral_profile

        # Update temporal patterns
        hour = context.timestamp.hour
        current_temporal = profile.temporal_patterns.get(hour, 0.5)
        new_temporal = (current_temporal * (1 - self.filter_config.learning_rate) +
                       self.filter_config.learning_rate)
        profile.temporal_patterns[hour] = new_temporal

        # Update task complexity scores
        if context.task_name:
            complexity_score = self._get_task_complexity_score(context.task_name)
            current_complexity = profile.task_complexity_scores.get(context.task_name, complexity_score)
            new_complexity = (current_complexity * (1 - self.filter_config.learning_rate) +
                            complexity_score * self.filter_config.learning_rate)
            profile.task_complexity_scores[context.task_name] = new_complexity

        # Update notification responses (based on whether it was allowed)
        if hasattr(context, '_was_allowed') and context._was_allowed:
            response = profile.notification_responses.get(context.notification_type, 0.5)
            new_response = min(response + self.filter_config.learning_rate * 0.1, 1.0)
            profile.notification_responses[context.notification_type] = new_response

        profile.last_updated = datetime.now()

        # Decay old patterns
        self._apply_decay_to_profile()

    def _apply_decay_to_profile(self) -> None:
        """Apply decay rate to behavioral profile patterns"""
        profile = self.behavioral_profile
        decay = self.filter_config.decay_rate

        # Decay temporal patterns
        for hour in profile.temporal_patterns:
            profile.temporal_patterns[hour] *= (1 - decay)

        # Decay task complexity scores
        for task in profile.task_complexity_scores:
            profile.task_complexity_scores[task] *= (1 - decay)

    def _count_recent_notifications(self, notification_type: str, time_window: timedelta) -> int:
        """Count notifications of a type within a time window"""
        cutoff_time = datetime.now() - time_window
        count = 0

        for notif_context in self.notification_history:
            if (notif_context.notification_type == notification_type and
                notif_context.timestamp >= cutoff_time):
                count += 1

        return count

    def _generate_content_hash(self, context: NotificationContext) -> str:
        """Generate hash for content deduplication"""
        content = f"{context.notification_type}:{context.task_name}:{context.session_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _generate_context_hash(self, context: NotificationContext) -> str:
        """Generate hash for context analysis"""
        content = f"{context.notification_type}:{context.task_name}:{context.priority}:{context.session_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _cleanup_old_sessions(self) -> None:
        """Clean up inactive sessions"""
        now = time.time()
        if now - self._last_cleanup < self.session_cleanup_interval:
            return

        cutoff_time = datetime.now() - timedelta(minutes=self.filter_config.session_timeout_minutes)

        with self._lock:
            expired_sessions = [
                session_id for session_id, metrics in self.active_sessions.items()
                if metrics.last_notification_time and metrics.last_notification_time < cutoff_time
            ]

            for session_id in expired_sessions:
                del self.active_sessions[session_id]

        self._last_cleanup = now

    def _cleanup_context_cache(self) -> None:
        """Clean up old context cache entries"""
        cutoff_time = datetime.now() - timedelta(seconds=self.context_cache_ttl)

        expired_keys = [
            key for key, timestamp in self.deduplication_cache.items()
            if timestamp < cutoff_time
        ]

        for key in expired_keys:
            self.deduplication_cache.pop(key, None)
            self.context_cache.pop(key, None)

    def _cleanup_deduplication_cache(self) -> None:
        """Clean up old deduplication cache entries"""
        cutoff_time = datetime.now() - self.dedup_window

        expired_keys = [
            key for key, timestamp in self.deduplication_cache.items()
            if timestamp < cutoff_time
        ]

        for key in expired_keys:
            del self.deduplication_cache[key]

    def _reset_hourly_counts_if_needed(self) -> None:
        """Reset hourly notification counts if we've entered a new hour"""
        now = datetime.now()
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)

        if current_hour_start > self._last_hourly_reset:
            self.hourly_notification_counts.clear()
            self._last_hourly_reset = current_hour_start

    def _record_notification_allowed(self, context: NotificationContext) -> None:
        """Record that a notification was allowed"""
        self.notification_history.append(context)
        context._was_allowed = True  # Mark for learning

        # Update hourly counts
        current_hour = datetime.now().hour
        self.hourly_notification_counts[current_hour] += 1

    def _record_filter_performance(self, filter_time_ms: float) -> None:
        """Record filtering performance metrics"""
        self.filter_metrics['filter_times'].append(filter_time_ms)
        self.filter_metrics['avg_filter_time_ms'] = (
            sum(self.filter_metrics['filter_times']) / len(self.filter_metrics['filter_times'])
        )

        # Update decision counts
        # This would be set by the calling method with the actual result

    def record_filter_result(self, result: FilterResult) -> None:
        """Record the result of a filtering decision"""
        if result.decision == FilterDecision.ALLOW:
            self.filter_metrics['total_allowed'] += 1
        else:
            self.filter_metrics['total_filtered'] += 1
            self.filter_metrics['filter_reasons'][result.decision.value] += 1

    def get_filter_metrics(self) -> dict[str, Any]:
        """Get current filtering metrics"""
        total = self.filter_metrics['total_filtered'] + self.filter_metrics['total_allowed']
        filter_rate = (self.filter_metrics['total_filtered'] / max(total, 1)) * 100

        return {
            'total_processed': total,
            'total_filtered': self.filter_metrics['total_filtered'],
            'total_allowed': self.filter_metrics['total_allowed'],
            'filter_rate_percent': filter_rate,
            'avg_filter_time_ms': self.filter_metrics['avg_filter_time_ms'],
            'active_sessions': len(self.active_sessions),
            'behavioral_profile_size': len(self.behavioral_profile.temporal_patterns),
            'filter_reasons': dict(self.filter_metrics['filter_reasons'])
        }

    def save_profile(self) -> None:
        """Save behavioral profile to disk"""
        self._save_behavioral_profile()

    def reset_learning(self) -> None:
        """Reset learned behavioral patterns"""
        self.behavioral_profile = BehavioralProfile()
        self.context_cache.clear()
        self.notification_history.clear()
        self.hourly_notification_counts.clear()
        logger.info("Behavioral learning reset")
