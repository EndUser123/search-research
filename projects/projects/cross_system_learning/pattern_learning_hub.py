"""
Pattern Learning Hub - Central system for collecting, analyzing, and distributing
enhancement patterns across all registered systems.

This hub serves as the intelligence center that:
1. Collects patterns from all registered enhancement systems
2. Analyzes pattern performance and relationships
3. Distributes successful patterns to relevant systems
4. Maintains pattern lifecycle management
5. Provides pattern recommendation and optimization
"""

import logging
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .core.base_patterns import (
    DomainType,
    EnhancementPattern,
    PatternCluster,
    PatternRelationship,
)
from .core.memory_structures import MemoryManager


class RegistrationStatus(Enum):
    """Status of system registration in the learning hub."""

    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class SystemRegistration:
    """Registration information for enhancement systems."""

    system_id: str
    system_name: str
    system_type: str  # e.g., "prompt_enhancer", "quality_assessor", "domain_specific"
    version: str
    capabilities: set[str] = field(default_factory=set)
    supported_domains: set[DomainType] = field(default_factory=set)
    api_endpoint: str | None = None
    callback_url: str | None = None
    status: RegistrationStatus = RegistrationStatus.PENDING
    registered_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime | None = None
    contribution_score: float = 0.0  # Based on pattern contributions and quality

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "system_name": self.system_name,
            "system_type": self.system_type,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "supported_domains": [d.value for d in self.supported_domains],
            "status": self.status.value,
            "contribution_score": self.contribution_score,
            "registered_at": self.registered_at.isoformat(),
        }


@dataclass
class PatternDistributionRecord:
    """Record of pattern distribution to systems."""

    distribution_id: str
    pattern_id: str
    target_system_id: str
    distributed_at: datetime
    adoption_status: str  # "pending", "adopted", "rejected", "modified"
    feedback_score: float | None = None
    modification_notes: str | None = None


class PatternLearningHub:
    """Central hub for pattern learning and distribution across systems."""

    def __init__(self, memory_manager: MemoryManager | None = None):
        self.memory_manager = memory_manager or MemoryManager()
        self.logger = logging.getLogger(__name__)

        # Core data structures
        self.registered_systems: dict[str, SystemRegistration] = {}
        self.pattern_clusters: dict[str, PatternCluster] = {}
        self.pattern_relationships: list[PatternRelationship] = []
        self.distribution_records: dict[str, PatternDistributionRecord] = {}

        # Pattern analysis components
        self.pattern_analyzers: dict[str, Callable] = {}
        self.distribution_strategies: dict[str, Callable] = {}
        self.quality_thresholds: dict[DomainType, float] = {
            domain: 0.7 for domain in DomainType
        }

        # Learning parameters
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.distribution_frequency = timedelta(hours=6)

        # Threading and synchronization
        self.lock = threading.RLock()
        self._shutdown = False
        self._background_threads: list[threading.Thread] = []

        # Performance tracking
        self.performance_metrics = {
            "total_patterns_processed": 0,
            "successful_distributions": 0,
            "failed_distributions": 0,
            "average_pattern_quality": 0.0,
            "active_systems": 0,
        }

        # Initialize background processing
        self._start_background_tasks()

    def register_system(self, registration: SystemRegistration) -> bool:
        """Register a new enhancement system with the hub."""
        with self.lock:
            try:
                if registration.system_id in self.registered_systems:
                    self.logger.warning(
                        f"System {registration.system_id} already registered"
                    )
                    return False

                # Validate registration
                if not self._validate_registration(registration):
                    self.logger.error(
                        f"Invalid registration for system {registration.system_id}"
                    )
                    return False

                registration.status = RegistrationStatus.ACTIVE
                registration.last_activity = datetime.now()
                self.registered_systems[registration.system_id] = registration

                self.logger.info(
                    f"Successfully registered system: {registration.system_name}"
                )
                self._update_performance_metrics()

                return True

            except Exception as e:
                self.logger.error(
                    f"Error registering system {registration.system_id}: {str(e)}"
                )
                return False

    def _validate_registration(self, registration: SystemRegistration) -> bool:
        """Validate system registration data."""
        if not registration.system_id or not registration.system_name:
            return False

        if not registration.capabilities:
            return False

        # Check for required capabilities
        required_capabilities = {"pattern_contribution", "feedback_provision"}
        if not required_capabilities.issubset(registration.capabilities):
            return False

        return True

    def submit_pattern(
        self, pattern: EnhancementPattern, source_system_id: str
    ) -> bool:
        """Submit a new enhancement pattern to the learning hub."""
        with self.lock:
            try:
                # Validate source system
                if source_system_id not in self.registered_systems:
                    self.logger.error(f"Unknown source system: {source_system_id}")
                    return False

                source_system = self.registered_systems[source_system_id]
                if source_system.status != RegistrationStatus.ACTIVE:
                    self.logger.error(f"Source system {source_system_id} not active")
                    return False

                # Validate pattern
                if not pattern.validate():
                    self.logger.error(f"Invalid pattern submitted: {pattern.id}")
                    return False

                # Store pattern in memory
                pattern.creator_system = source_system_id
                self.memory_manager.pattern_memory.store(
                    pattern.id, {"pattern": pattern}
                )

                # Analyze pattern
                self._analyze_pattern(pattern)

                # Update source system contribution score
                source_system.contribution_score += (
                    pattern.quality_metrics.calculate_overall_score()
                )

                self.performance_metrics["total_patterns_processed"] += 1
                self.logger.info(
                    f"Successfully submitted pattern {pattern.id} from {source_system_id}"
                )

                return True

            except Exception as e:
                self.logger.error(f"Error submitting pattern: {str(e)}")
                return False

    def _analyze_pattern(self, pattern: EnhancementPattern) -> None:
        """Analyze submitted pattern for clustering and relationships."""
        # Find similar patterns
        similar_patterns = self.memory_manager.pattern_memory.get_similar_patterns(
            pattern.id, 0.6
        )

        if similar_patterns:
            # Create or update pattern cluster
            cluster = self._find_or_create_cluster(pattern, similar_patterns)
            cluster.add_pattern(pattern.id)

            # Create relationships
            for similar_pattern in similar_patterns:
                relationship = self._create_relationship(pattern.id, similar_pattern.id)
                self.pattern_relationships.append(relationship)

        # Update quality thresholds based on pattern performance
        self._update_quality_thresholds(pattern)

    def _find_or_create_cluster(
        self, pattern: EnhancementPattern, similar_patterns: list[EnhancementPattern]
    ) -> PatternCluster:
        """Find existing cluster or create new one for pattern."""
        # Look for existing clusters with similar patterns
        for cluster in self.pattern_clusters.values():
            if any(p.id in cluster.pattern_ids for p in similar_patterns):
                return cluster

        # Create new cluster
        cluster_id = str(uuid.uuid4())
        cluster = PatternCluster(
            id=cluster_id,
            name=f"Cluster_{pattern.domain_context.domain.value}_{len(self.pattern_clusters)}",
            description=f"Cluster for {pattern.pattern_type} patterns in {pattern.domain_context.domain.value}",
            domain_focus=pattern.domain_context.domain,
        )

        self.pattern_clusters[cluster_id] = cluster
        return cluster

    def _create_relationship(
        self, pattern_a_id: str, pattern_b_id: str, relationship_type: str = "similar"
    ) -> PatternRelationship:
        """Create relationship between two patterns."""
        # Check if relationship already exists
        for rel in self.pattern_relationships:
            if (
                rel.pattern_a_id == pattern_a_id and rel.pattern_b_id == pattern_b_id
            ) or (
                rel.pattern_a_id == pattern_b_id and rel.pattern_b_id == pattern_a_id
            ):
                return rel

        # Calculate relationship strength
        strength = self._calculate_relationship_strength(pattern_a_id, pattern_b_id)

        return PatternRelationship(
            pattern_a_id=pattern_a_id,
            pattern_b_id=pattern_b_id,
            relationship_type=relationship_type,
            strength=strength,
        )

    def _calculate_relationship_strength(
        self, pattern_a_id: str, pattern_b_id: str
    ) -> float:
        """Calculate strength of relationship between two patterns."""
        # Get patterns
        pattern_a = self.memory_manager.pattern_memory.get_pattern(pattern_a_id)
        pattern_b = self.memory_manager.pattern_memory.get_pattern(pattern_b_id)

        if not pattern_a or not pattern_b:
            return 0.0

        # Calculate strength based on multiple factors
        strength = 0.0
        factors = 0

        # Domain similarity
        if pattern_a.domain_context.domain == pattern_b.domain_context.domain:
            strength += 0.4
        factors += 1

        # Quality similarity
        quality_diff = abs(
            pattern_a.quality_metrics.calculate_overall_score()
            - pattern_b.quality_metrics.calculate_overall_score()
        )
        similarity = max(0, 1.0 - quality_diff)
        strength += 0.3 * similarity
        factors += 1

        # Tag overlap
        common_tags = pattern_a.tags.intersection(pattern_b.tags)
        if pattern_a.tags or pattern_b.tags:
            tag_similarity = len(common_tags) / len(
                pattern_a.tags.union(pattern_b.tags)
            )
            strength += 0.3 * tag_similarity
        factors += 1

        return strength if factors == 0 else strength / factors

    def _update_quality_thresholds(self, pattern: EnhancementPattern) -> None:
        """Dynamically update quality thresholds based on pattern performance."""
        domain = pattern.domain_context.domain
        pattern_quality = pattern.quality_metrics.calculate_overall_score()

        # Adaptive threshold update
        current_threshold = self.quality_thresholds[domain]
        if pattern_quality > current_threshold:
            # Gradually increase threshold if high-quality patterns emerge
            self.quality_thresholds[domain] = min(
                0.95, current_threshold + self.learning_rate * 0.05
            )
        elif pattern_quality < current_threshold * 0.5:
            # Gradually decrease threshold if patterns are struggling
            self.quality_thresholds[domain] = max(
                0.3, current_threshold - self.learning_rate * 0.05
            )

    def get_recommended_patterns(
        self, system_id: str, context: dict[str, Any], limit: int = 10
    ) -> list[EnhancementPattern]:
        """Get recommended patterns for a specific system based on context."""
        with self.lock:
            if system_id not in self.registered_systems:
                return []

            system = self.registered_systems[system_id]
            domain = DomainType(context.get("domain", "software_development"))

            # Get high-quality patterns
            min_quality = self.quality_thresholds.get(domain, 0.7)
            quality_patterns = (
                self.memory_manager.pattern_memory.get_successful_patterns(
                    min_quality, 3
                )
            )

            # Filter by system capabilities and supported domains
            recommended_patterns = []
            for pattern in quality_patterns:
                if pattern.domain_context.domain in system.supported_domains:
                    # Calculate recommendation score
                    rec_score = self._calculate_recommendation_score(
                        pattern, system, context
                    )
                    recommended_patterns.append((pattern, rec_score))

            # Sort by recommendation score
            recommended_patterns.sort(key=lambda x: x[1], reverse=True)

            return [pattern for pattern, _ in recommended_patterns[:limit]]

    def _calculate_recommendation_score(
        self,
        pattern: EnhancementPattern,
        system: SystemRegistration,
        context: dict[str, Any],
    ) -> float:
        """Calculate recommendation score for pattern-system pairing."""
        score = 0.0
        factors = 0

        # Quality score
        score += pattern.quality_metrics.calculate_overall_score() * 0.4
        factors += 1

        # Domain compatibility
        if pattern.domain_context.domain in system.supported_domains:
            score += 0.3
        factors += 1

        # System capability alignment
        required_capabilities = set(pattern.template.split(":")[0].split("_"))
        capability_overlap = len(
            required_capabilities.intersection(system.capabilities)
        )
        if required_capabilities:
            score += 0.2 * (capability_overlap / len(required_capabilities))
        factors += 1

        # Context relevance
        context_keywords = set(context.get("keywords", []))
        pattern_keywords = set(pattern.description.lower().split())
        keyword_overlap = len(context_keywords.intersection(pattern_keywords))
        if context_keywords:
            score += 0.1 * (keyword_overlap / len(context_keywords))
        factors += 1

        return score if factors == 0 else score / factors

    def distribute_patterns(self, force_distribution: bool = False) -> dict[str, int]:
        """Distribute high-quality patterns to appropriate systems."""
        if not force_distribution and not self._should_distribute():
            return {"distributed": 0, "failed": 0}

        distribution_results = {"distributed": 0, "failed": 0}

        with self.lock:
            for system_id, system in self.registered_systems.items():
                if system.status != RegistrationStatus.ACTIVE:
                    continue

                try:
                    # Get patterns for this system
                    context = {
                        "domain": system.supported_domains.pop()
                        if system.supported_domains
                        else "software_development",
                        "keywords": list(system.capabilities),
                    }

                    recommended_patterns = self.get_recommended_patterns(
                        system_id, context, limit=5
                    )

                    # Distribute patterns
                    for pattern in recommended_patterns:
                        if self._distribute_pattern_to_system(pattern, system_id):
                            distribution_results["distributed"] += 1
                        else:
                            distribution_results["failed"] += 1

                except Exception as e:
                    self.logger.error(
                        f"Error distributing patterns to {system_id}: {str(e)}"
                    )
                    distribution_results["failed"] += 1

        self.performance_metrics["successful_distributions"] += distribution_results[
            "distributed"
        ]
        self.performance_metrics["failed_distributions"] += distribution_results[
            "failed"
        ]

        return distribution_results

    def _should_distribute(self) -> bool:
        """Check if pattern distribution should occur."""
        # Check time since last distribution
        last_distributed = datetime.now() - self.distribution_frequency
        for record in self.distribution_records.values():
            if record.distributed_at > last_distributed:
                return False

        return True

    def _distribute_pattern_to_system(
        self, pattern: EnhancementPattern, system_id: str
    ) -> bool:
        """Distribute a specific pattern to a system."""
        distribution_id = str(uuid.uuid4())
        record = PatternDistributionRecord(
            distribution_id=distribution_id,
            pattern_id=pattern.id,
            target_system_id=system_id,
            distributed_at=datetime.now(),
            adoption_status="pending",
        )

        try:
            # In a real implementation, this would make an API call to the system
            # For now, we'll just record the distribution
            self.distribution_records[distribution_id] = record

            # Mark pattern as applied to update metrics
            pattern.quality_metrics.update_success()
            pattern.last_applied = datetime.now()

            self.logger.info(f"Distributed pattern {pattern.id} to system {system_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to distribute pattern {pattern.id} to {system_id}: {str(e)}"
            )
            record.adoption_status = "rejected"
            self.distribution_records[distribution_id] = record
            return False

    def record_feedback(
        self, distribution_id: str, feedback_score: float, notes: str | None = None
    ) -> bool:
        """Record feedback for a distributed pattern."""
        with self.lock:
            if distribution_id not in self.distribution_records:
                return False

            record = self.distribution_records[distribution_id]
            record.feedback_score = feedback_score
            record.adoption_status = "adopted" if feedback_score >= 0.7 else "modified"
            record.modification_notes = notes

            # Update pattern quality metrics
            pattern = self.memory_manager.pattern_memory.get_pattern(record.pattern_id)
            if pattern:
                if feedback_score >= 0.7:
                    pattern.quality_metrics.update_success(feedback_score * 100)
                else:
                    pattern.quality_metrics.update_failure()

            self.logger.info(
                f"Recorded feedback for distribution {distribution_id}: {feedback_score}"
            )
            return True

    def _start_background_tasks(self) -> None:
        """Start background processing threads."""
        # Pattern analysis thread
        analysis_thread = threading.Thread(
            target=self._background_pattern_analysis, daemon=True
        )
        analysis_thread.start()
        self._background_threads.append(analysis_thread)

        # Distribution thread
        distribution_thread = threading.Thread(
            target=self._background_distribution, daemon=True
        )
        distribution_thread.start()
        self._background_threads.append(distribution_thread)

        # Metrics update thread
        metrics_thread = threading.Thread(
            target=self._background_metrics_update, daemon=True
        )
        metrics_thread.start()
        self._background_threads.append(metrics_thread)

    def _background_pattern_analysis(self) -> None:
        """Background thread for continuous pattern analysis."""
        while not self._shutdown:
            try:
                # Analyze pattern clusters
                for cluster in self.pattern_clusters.values():
                    cluster_patterns = {
                        pid: self.memory_manager.pattern_memory.get_pattern(pid)
                        for pid in cluster.pattern_ids
                    }
                    valid_patterns = {
                        pid: p for pid, p in cluster_patterns.items() if p
                    }
                    cluster.calculate_cluster_metrics(valid_patterns)

                # Sleep for a while
                threading.Event().wait(timeout=3600)  # 1 hour

            except Exception as e:
                self.logger.error(f"Error in background pattern analysis: {str(e)}")
                threading.Event().wait(timeout=300)  # 5 minutes on error

    def _background_distribution(self) -> None:
        """Background thread for automatic pattern distribution."""
        while not self._shutdown:
            try:
                self.distribute_patterns()
                threading.Event().wait(
                    timeout=self.distribution_frequency.total_seconds()
                )

            except Exception as e:
                self.logger.error(f"Error in background distribution: {str(e)}")
                threading.Event().wait(timeout=300)

    def _background_metrics_update(self) -> None:
        """Background thread for updating performance metrics."""
        while not self._shutdown:
            try:
                self._update_performance_metrics()
                threading.Event().wait(timeout=300)  # 5 minutes

            except Exception as e:
                self.logger.error(f"Error in background metrics update: {str(e)}")
                threading.Event().wait(timeout=60)

    def _update_performance_metrics(self) -> None:
        """Update internal performance metrics."""
        with self.lock:
            # Count active systems
            self.performance_metrics["active_systems"] = sum(
                1
                for system in self.registered_systems.values()
                if system.status == RegistrationStatus.ACTIVE
            )

            # Calculate average pattern quality
            all_patterns = []
            for pattern_id in self.memory_manager.pattern_memory.patterns:
                pattern = self.memory_manager.pattern_memory.get_pattern(pattern_id)
                if pattern:
                    all_patterns.append(
                        pattern.quality_metrics.calculate_overall_score()
                    )

            if all_patterns:
                self.performance_metrics["average_pattern_quality"] = sum(
                    all_patterns
                ) / len(all_patterns)

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        with self.lock:
            return {
                "registered_systems": len(self.registered_systems),
                "active_systems": self.performance_metrics["active_systems"],
                "total_patterns": len(self.memory_manager.pattern_memory.patterns),
                "pattern_clusters": len(self.pattern_clusters),
                "pattern_relationships": len(self.pattern_relationships),
                "total_distributions": len(self.distribution_records),
                "performance_metrics": self.performance_metrics.copy(),
                "quality_thresholds": {
                    domain.value: threshold
                    for domain, threshold in self.quality_thresholds.items()
                },
            }

    def shutdown(self) -> None:
        """Shutdown the learning hub gracefully."""
        self._shutdown = True

        # Wait for background threads to finish
        for thread in self._background_threads:
            if thread.is_alive():
                thread.join(timeout=10)

        # Save memory to disk
        self.memory_manager.save_to_disk()

        self.logger.info("Pattern Learning Hub shutdown complete")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except:
            pass
