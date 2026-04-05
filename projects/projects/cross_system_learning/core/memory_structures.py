"""
Memory structures for storing and managing patterns and learning data.
"""

import pickle
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .base_patterns import DomainType, EnhancementPattern


@dataclass
class MemoryEntry:
    """Base entry for memory systems."""

    id: str
    timestamp: datetime
    data: dict[str, Any]
    access_count: int = 0
    last_accessed: datetime | None = None
    expiry: datetime | None = None

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expiry is None:
            return False
        return datetime.now() > self.expiry

    def access(self) -> None:
        """Record access to this entry."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryBank(ABC):
    """Abstract base class for all memory banks."""

    def __init__(self, name: str, max_entries: int = 10000):
        self.name = name
        self.max_entries = max_entries
        self.entries: dict[str, MemoryEntry] = {}
        self.lock = threading.RLock()

    @abstractmethod
    def store(
        self, entry_id: str, data: dict[str, Any], ttl_hours: int | None = None
    ) -> None:
        """Store data in memory bank."""
        pass

    @abstractmethod
    def retrieve(self, entry_id: str) -> dict[str, Any] | None:
        """Retrieve data from memory bank."""
        pass

    @abstractmethod
    def cleanup(self) -> int:
        """Clean up expired entries and enforce size limits."""
        pass

    def _create_entry(
        self, entry_id: str, data: dict[str, Any], ttl_hours: int | None = None
    ) -> MemoryEntry:
        """Create a memory entry."""
        expiry = None
        if ttl_hours:
            expiry = datetime.now() + timedelta(hours=ttl_hours)

        return MemoryEntry(
            id=entry_id, timestamp=datetime.now(), data=data, expiry=expiry
        )

    def _enforce_size_limit(self) -> int:
        """Remove least recently used entries if over size limit."""
        if len(self.entries) <= self.max_entries:
            return 0

        # Sort by last_accessed (None treated as oldest)
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: (x[1].last_accessed or datetime.min, x[1].access_count),
        )

        entries_to_remove = len(self.entries) - self.max_entries
        for entry_id, _ in sorted_entries[:entries_to_remove]:
            del self.entries[entry_id]

        return entries_to_remove


@dataclass
class PatternMemoryEntry(MemoryEntry):
    """Specialized memory entry for enhancement patterns."""

    pattern: EnhancementPattern
    application_context: dict[str, Any]
    result_metrics: dict[str, float]


class PatternMemory(MemoryBank):
    """Specialized memory bank for enhancement patterns."""

    def __init__(self, max_patterns: int = 5000):
        super().__init__("PatternMemory", max_patterns)
        self.patterns: dict[str, EnhancementPattern] = {}
        self.pattern_applications: dict[str, list[PatternMemoryEntry]] = defaultdict(
            list
        )
        self.success_tracking: dict[str, float] = defaultdict(float)

    def store(
        self, entry_id: str, data: dict[str, Any], ttl_hours: int | None = None
    ) -> None:
        """Store enhancement pattern or application result."""
        with self.lock:
            if "pattern" in data:
                # Store the pattern itself
                pattern = data["pattern"]
                self.patterns[pattern.id] = pattern

                # Create memory entry for the pattern
                entry = self._create_entry(entry_id, data, ttl_hours)
                self.entries[entry_id] = entry

            elif "application_result" in data:
                # Store pattern application result
                result_data = data["application_result"]
                pattern_id = result_data.get("pattern_id")

                if pattern_id and pattern_id in self.patterns:
                    entry = PatternMemoryEntry(
                        id=entry_id,
                        timestamp=datetime.now(),
                        data=data,
                        pattern=self.patterns[pattern_id],
                        application_context=result_data.get("context", {}),
                        result_metrics=result_data.get("metrics", {}),
                    )
                    self.entries[entry_id] = entry
                    self.pattern_applications[pattern_id].append(entry)

                    # Update success tracking
                    success_metric = result_data.get("metrics", {}).get("success", 0.0)
                    self.success_tracking[pattern_id] = (
                        self.success_tracking[pattern_id] + success_metric
                    ) / 2.0

    def retrieve(self, entry_id: str) -> dict[str, Any] | None:
        """Retrieve pattern or application result."""
        with self.lock:
            if entry_id in self.entries:
                entry = self.entries[entry_id]
                entry.access()

                if entry.is_expired():
                    del self.entries[entry_id]
                    return None

                return entry.data
            return None

    def get_pattern(self, pattern_id: str) -> EnhancementPattern | None:
        """Get a specific pattern by ID."""
        return self.patterns.get(pattern_id)

    def get_successful_patterns(
        self, min_success_rate: float = 0.7, min_applications: int = 5
    ) -> list[EnhancementPattern]:
        """Get patterns that meet success criteria."""
        successful_patterns = []

        for pattern_id, pattern in self.patterns.items():
            applications = self.pattern_applications[pattern_id]
            if len(applications) >= min_applications:
                success_rate = self.success_tracking.get(pattern_id, 0.0)
                if success_rate >= min_success_rate:
                    successful_patterns.append(pattern)

        return successful_patterns

    def get_similar_patterns(
        self, pattern_id: str, similarity_threshold: float = 0.8
    ) -> list[EnhancementPattern]:
        """Get patterns similar to the given pattern."""
        target_pattern = self.patterns.get(pattern_id)
        if not target_pattern:
            return []

        similar_patterns = []
        for pid, pattern in self.patterns.items():
            if pid != pattern_id:
                similarity = self._calculate_pattern_similarity(target_pattern, pattern)
                if similarity >= similarity_threshold:
                    similar_patterns.append((pattern, similarity))

        # Sort by similarity (descending)
        similar_patterns.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in similar_patterns]

    def _calculate_pattern_similarity(
        self, pattern_a: EnhancementPattern, pattern_b: EnhancementPattern
    ) -> float:
        """Calculate similarity between two patterns."""
        similarity_score = 0.0
        factors = 0

        # Domain similarity
        if pattern_a.domain_context.domain == pattern_b.domain_context.domain:
            similarity_score += 0.3
        factors += 1

        # Pattern type similarity
        if pattern_a.pattern_type == pattern_b.pattern_type:
            similarity_score += 0.2
        factors += 1

        # Tag similarity
        common_tags = pattern_a.tags.intersection(pattern_b.tags)
        if pattern_a.tags or pattern_b.tags:
            tag_similarity = len(common_tags) / len(
                pattern_a.tags.union(pattern_b.tags)
            )
            similarity_score += 0.3 * tag_similarity
        factors += 1

        # Template similarity (simplified)
        if pattern_a.template and pattern_b.template:
            template_similarity = self._calculate_text_similarity(
                pattern_a.template, pattern_b.template
            )
            similarity_score += 0.2 * template_similarity
        factors += 1

        return similarity_score if factors == 0 else similarity_score / factors

    def _calculate_text_similarity(self, text_a: str, text_b: str) -> float:
        """Simple text similarity calculation."""
        if not text_a or not text_b:
            return 0.0

        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)

        return len(intersection) / len(union) if union else 0.0

    def cleanup(self) -> int:
        """Clean up expired entries and old application results."""
        removed_count = 0
        current_time = datetime.now()

        with self.lock:
            # Remove expired entries
            expired_entries = [
                entry_id
                for entry_id, entry in self.entries.items()
                if entry.is_expired()
            ]

            for entry_id in expired_entries:
                del self.entries[entry_id]
                removed_count += 1

            # Clean up old application results (older than 30 days)
            cutoff_date = current_time - timedelta(days=30)

            for pattern_id, applications in self.pattern_applications.items():
                valid_applications = [
                    app for app in applications if app.timestamp > cutoff_date
                ]
                self.pattern_applications[pattern_id] = valid_applications
                removed_count += len(applications) - len(valid_applications)

            # Enforce size limit
            removed_count += self._enforce_size_limit()

        return removed_count


@dataclass
class QualityMetricsEntry(MemoryEntry):
    """Specialized entry for quality metrics tracking."""

    domain: DomainType
    initial_quality: float
    enhanced_quality: float
    improvement_percentage: float
    processing_time: float
    user_feedback: float | None = None
    error_occurred: bool = False


class QualityMemory(MemoryBank):
    """Memory bank for tracking quality metrics and improvement patterns."""

    def __init__(self, max_entries: int = 10000):
        super().__init__("QualityMemory", max_entries)
        self.quality_history: dict[str, list[QualityMetricsEntry]] = defaultdict(list)
        self.domain_performance: dict[DomainType, list[float]] = defaultdict(list)
        self.quality_trends: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def store_quality_metrics(
        self, session_id: str, metrics_data: dict[str, Any]
    ) -> None:
        """Store quality metrics for an enhancement session."""
        entry = QualityMetricsEntry(
            id=session_id,
            timestamp=datetime.now(),
            data=metrics_data,
            domain=DomainType(metrics_data.get("domain", "software_development")),
            initial_quality=metrics_data.get("initial_quality", 0.0),
            enhanced_quality=metrics_data.get("enhanced_quality", 0.0),
            improvement_percentage=metrics_data.get("improvement_percentage", 0.0),
            processing_time=metrics_data.get("processing_time", 0.0),
            user_feedback=metrics_data.get("user_feedback"),
            error_occurred=metrics_data.get("error_occurred", False),
        )

        with self.lock:
            self.entries[session_id] = entry
            self.quality_history[session_id].append(entry)
            self.domain_performance[entry.domain].append(entry.improvement_percentage)
            self.quality_trends[str(entry.domain)].append(entry.improvement_percentage)

    def get_domain_performance(self, domain: DomainType) -> dict[str, float]:
        """Get performance statistics for a specific domain."""
        with self.lock:
            improvements = self.domain_performance.get(domain, [])
            if not improvements:
                return {
                    "average_improvement": 0.0,
                    "median_improvement": 0.0,
                    "min_improvement": 0.0,
                    "max_improvement": 0.0,
                    "total_sessions": 0,
                }

            sorted_improvements = sorted(improvements)
            total_sessions = len(improvements)

            return {
                "average_improvement": sum(improvements) / total_sessions,
                "median_improvement": sorted_improvements[total_sessions // 2],
                "min_improvement": min(improvements),
                "max_improvement": max(improvements),
                "total_sessions": total_sessions,
            }

    def get_quality_trend(
        self, domain: DomainType, window_size: int = 50
    ) -> list[float]:
        """Get recent quality trend for a domain."""
        with self.lock:
            trend_data = list(self.quality_trends.get(str(domain), []))
            return trend_data[-window_size:] if trend_data else []

    def store(
        self, entry_id: str, data: dict[str, Any], ttl_hours: int | None = None
    ) -> None:
        """Implementation of abstract store method."""
        if "quality_metrics" in data:
            self.store_quality_metrics(entry_id, data["quality_metrics"])

    def retrieve(self, entry_id: str) -> dict[str, Any] | None:
        """Implementation of abstract retrieve method."""
        with self.lock:
            if entry_id in self.entries:
                entry = self.entries[entry_id]
                entry.access()

                if entry.is_expired():
                    del self.entries[entry_id]
                    return None

                return entry.data
            return None

    def cleanup(self) -> int:
        """Clean up old quality data."""
        removed_count = 0
        cutoff_date = datetime.now() - timedelta(days=90)

        with self.lock:
            # Remove old entries
            old_entries = [
                entry_id
                for entry_id, entry in self.entries.items()
                if entry.timestamp < cutoff_date
            ]

            for entry_id in old_entries:
                del self.entries[entry_id]
                removed_count += 1

            # Limit domain performance history
            for domain in self.domain_performance:
                if len(self.domain_performance[domain]) > 10000:
                    self.domain_performance[domain] = self.domain_performance[domain][
                        -5000:
                    ]

            removed_count += self._enforce_size_limit()

        return removed_count


@dataclass
class ConversationMemoryEntry(MemoryEntry):
    """Entry for conversation context and patterns."""

    user_intent: str
    conversation_context: dict[str, Any]
    enhancement_history: list[str]
    successful_enhancements: list[str]


class ConversationMemory(MemoryBank):
    """Memory bank for conversation context and enhancement history."""

    def __init__(self, max_conversations: int = 1000):
        super().__init__("ConversationMemory", max_conversations)
        self.conversation_patterns: dict[str, list[str]] = defaultdict(list)
        self.intent_patterns: dict[str, list[ConversationMemoryEntry]] = defaultdict(
            list
        )

    def store_conversation_context(
        self, conversation_id: str, context_data: dict[str, Any]
    ) -> None:
        """Store conversation context and enhancement patterns."""
        entry = ConversationMemoryEntry(
            id=conversation_id,
            timestamp=datetime.now(),
            data=context_data,
            user_intent=context_data.get("user_intent", ""),
            conversation_context=context_data.get("context", {}),
            enhancement_history=context_data.get("enhancement_history", []),
            successful_enhancements=context_data.get("successful_enhancements", []),
        )

        with self.lock:
            self.entries[conversation_id] = entry
            self.intent_patterns[entry.user_intent].append(entry)

            # Track conversation patterns
            if "pattern_sequence" in context_data:
                self.conversation_patterns[conversation_id].extend(
                    context_data["pattern_sequence"]
                )

    def get_similar_conversations(
        self, user_intent: str, limit: int = 5
    ) -> list[ConversationMemoryEntry]:
        """Get conversations with similar intents."""
        with self.lock:
            similar_conversations = self.intent_patterns.get(user_intent, [])

            # Sort by recency and success
            similar_conversations.sort(
                key=lambda x: (x.timestamp, len(x.successful_enhancements)),
                reverse=True,
            )

            return similar_conversations[:limit]

    def get_common_pattern_sequences(self, min_occurrences: int = 3) -> dict[str, int]:
        """Get commonly occurring pattern sequences."""
        sequence_counts = defaultdict(int)

        with self.lock:
            for patterns in self.conversation_patterns.values():
                if len(patterns) >= 2:
                    # Create sequence of consecutive patterns
                    for i in range(len(patterns) - 1):
                        sequence = f"{patterns[i]} -> {patterns[i + 1]}"
                        sequence_counts[sequence] += 1

        # Filter by minimum occurrences
        return {
            seq: count
            for seq, count in sequence_counts.items()
            if count >= min_occurrences
        }

    def store(
        self, entry_id: str, data: dict[str, Any], ttl_hours: int | None = None
    ) -> None:
        """Implementation of abstract store method."""
        if "conversation_context" in data:
            self.store_conversation_context(entry_id, data["conversation_context"])

    def retrieve(self, entry_id: str) -> dict[str, Any] | None:
        """Implementation of abstract retrieve method."""
        with self.lock:
            if entry_id in self.entries:
                entry = self.entries[entry_id]
                entry.access()

                if entry.is_expired():
                    del self.entries[entry_id]
                    return None

                return entry.data
            return None

    def cleanup(self) -> int:
        """Clean up old conversation data."""
        removed_count = 0
        cutoff_date = datetime.now() - timedelta(days=60)

        with self.lock:
            # Remove old conversations
            old_entries = [
                entry_id
                for entry_id, entry in self.entries.items()
                if entry.timestamp < cutoff_date
            ]

            for entry_id in old_entries:
                del self.entries[entry_id]
                removed_count += 1

            # Clean up intent patterns
            for intent in self.intent_patterns:
                self.intent_patterns[intent] = [
                    entry
                    for entry in self.intent_patterns[intent]
                    if entry.timestamp >= cutoff_date
                ]

            removed_count += self._enforce_size_limit()

        return removed_count


class MemoryManager:
    """Central manager for all memory banks."""

    def __init__(self, base_path: str = "/tmp/memory_storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize memory banks
        self.pattern_memory = PatternMemory()
        self.quality_memory = QualityMemory()
        self.conversation_memory = ConversationMemory()

        # Memory bank registry
        self.memory_banks = {
            "patterns": self.pattern_memory,
            "quality": self.quality_memory,
            "conversations": self.conversation_memory,
        }

    def save_to_disk(self) -> None:
        """Save all memory banks to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.base_path / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        for bank_name, memory_bank in self.memory_banks.items():
            file_path = backup_path / f"{bank_name}.pkl"
            with open(file_path, "wb") as f:
                pickle.dump(memory_bank, f)

    def load_from_disk(self, backup_path: str | None = None) -> bool:
        """Load memory banks from disk backup."""
        if not backup_path:
            # Find most recent backup
            backup_dirs = [
                d
                for d in self.base_path.iterdir()
                if d.is_dir() and d.name.startswith("backup_")
            ]
            if not backup_dirs:
                return False
            backup_dirs.sort(reverse=True)
            backup_path = str(backup_dirs[0])

        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            return False

        success = True
        for bank_name, memory_bank in self.memory_banks.items():
            file_path = backup_dir / f"{bank_name}.pkl"
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f:
                        loaded_bank = pickle.load(f)
                        self.memory_banks[bank_name] = loaded_bank
                except Exception:
                    success = False

        return success

    def cleanup_all(self) -> dict[str, int]:
        """Clean up all memory banks."""
        cleanup_results = {}
        for bank_name, memory_bank in self.memory_banks.items():
            removed_count = memory_bank.cleanup()
            cleanup_results[bank_name] = removed_count

        return cleanup_results
