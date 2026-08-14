import logging
import time
from dataclasses import dataclass
from typing import Any

"""Constitutional Validator for CKS Storage Operations.

Constitutional Requirements:
- Solo developer optimization validation
- Evidence-based operation verification
- Force multiplier compliance checking
- Anti-enterprise bloat validation

This validator ensures all storage operations comply with CSF Constitution v4.0
principles for solo developer environments.
"""


@dataclass
class ConstitutionalMetric:
    """Constitutional compliance metric."""

    name: str
    value: float
    threshold: float
    description: str
    constitutional_basis: str


class ConstitutionalValidator:
    """Validates CKS operations against constitutional requirements.

    Algorithm Approach: Multi-factor compliance scoring based on constitutional
    principles and solo developer optimization criteria.

    Time Complexity: O(1) for most validations
    Space Complexity: O(1) - constant memory usage

    Constitutional Principles:
    - §3.6: Evidence-based operations
    - §3.7: Solo developer optimization
    - §3.8: Force multiplier integration
    - §3.9: Long-term architectural thinking
    """

    def __init__(self) -> None:
        """Initialize constitutional validator."""
        self.logger = logging.getLogger(__name__)
        self.metrics: list[ConstitutionalMetric] = []

        # Constitutional thresholds (solo developer optimized)
        self.thresholds = {
            "max_memory_mb": 4096,  # Conservative for solo dev
            "min_evidence_quality": 0.95,
            "min_force_multiplier_score": 0.8,
            "max_complexity_score": 0.6,  # Anti-bloat measure
            "min_simplicity_score": 0.8,
            "min_sustainability_score": 0.7,
        }

        self.logger.info(
            "ConstitutionalValidator initialized with solo developer optimization",
        )

    def validate_storage_config(self, config) -> bool:
        """Validate storage configuration against constitutional requirements.

        Args:
            config: StorageConfig instance

        Returns:
            bool: True if configuration is constitutionally compliant

        Raises:
            ValueError: If configuration violates constitutional principles

        """
        violations = []

        # Solo developer optimization checks
        if config.max_memory_mb > self.thresholds["max_memory_mb"]:
            violations.append(
                f"Memory limit {config.max_memory_mb}MB exceeds constitutional maximum {self.thresholds['max_memory_mb']}MB",
            )

        if config.vector_dimension > 1536:
            violations.append(
                f"Vector dimension {config.vector_dimension} exceeds solo developer optimization limit of 1536",
            )

        # Anti-enterprise bloat checks
        if config.batch_size > 10000:
            violations.append(
                f"Batch size {config.batch_size} exceeds solo developer limit of 10000",
            )

        # Evidence-based configuration checks
        if not hasattr(config, "db_path") or not config.db_path:
            violations.append(
                "Storage configuration lacks evidence-based database path",
            )

        if violations:
            error_msg = "Constitutional violations: " + "; ".join(violations)
            self.logger.error(f"Configuration validation failed: {error_msg}")
            raise ValueError(error_msg)

        self.logger.info("Storage configuration passed constitutional validation")
        return True

    def calculate_storage_compliance_score(self, storage_manager) -> float:
        """Calculate overall storage compliance score.

        Args:
            storage_manager: StorageManager instance

        Returns:
            float: Compliance score (0.0 to 1.0)

        """
        self.metrics.clear()

        # Memory usage compliance (solo developer optimization)
        memory_usage = storage_manager.get_memory_usage()
        memory_score = max(0, 1 - (memory_usage / self.thresholds["max_memory_mb"]))
        self.metrics.append(
            ConstitutionalMetric(
                name="memory_usage",
                value=memory_score,
                threshold=self.thresholds["max_memory_mb"],
                description="Memory usage compliance",
                constitutional_basis="CSF §3.7 - Solo Developer Optimization",
            ),
        )

        # Evidence-based operations
        stats = storage_manager.get_storage_stats()
        evidence_score = self._calculate_evidence_score(stats)
        self.metrics.append(
            ConstitutionalMetric(
                name="evidence_based",
                value=evidence_score,
                threshold=self.thresholds["min_evidence_quality"],
                description="Evidence-based operations",
                constitutional_basis="CSF §3.6 - Evidence-Based Operations",
            ),
        )

        # Force multiplier compliance
        force_multiplier_score = self._calculate_force_multiplier_score(stats)
        self.metrics.append(
            ConstitutionalMetric(
                name="force_multiplier",
                value=force_multiplier_score,
                threshold=self.thresholds["min_force_multiplier_score"],
                description="Force multiplier capability",
                constitutional_basis="CSF §3.8 - Force Multiplier Integration",
            ),
        )

        # Simplicity and anti-bloat
        simplicity_score = self._calculate_simplicity_score(storage_manager)
        self.metrics.append(
            ConstitutionalMetric(
                name="simplicity",
                value=simplicity_score,
                threshold=self.thresholds["min_simplicity_score"],
                description="System simplicity (anti-bloat)",
                constitutional_basis="CSF §3.7 - Solo Developer Optimization",
            ),
        )

        # Overall compliance score
        overall_score = sum(m.value for m in self.metrics) / len(self.metrics)

        self.logger.info(f"Constitutional compliance score: {overall_score:.3f}")
        return overall_score

    def _calculate_evidence_score(self, stats: dict[str, Any]) -> float:
        """Calculate evidence-based operations score.

        Args:
            stats: Storage statistics

        Returns:
            float: Evidence score (0.0 to 1.0)

        """
        evidence_indicators = []

        # Database connectivity evidence
        if stats.get("database_path"):
            evidence_indicators.append(0.3)

        # Vector storage evidence
        if stats.get("faiss_available") and stats.get("vectors_stored", 0) > 0:
            evidence_indicators.append(0.3)

        # Multi-graph evidence
        graph_types = [
            "knowledge_nodes",
            "causal_nodes",
            "social_nodes",
            "system_nodes",
        ]
        active_graphs = sum(1 for graph_type in graph_types if stats.get(graph_type, 0) > 0)
        if active_graphs >= 2:  # Minimum multi-graph evidence
            evidence_indicators.append(0.4)

        return min(1.0, sum(evidence_indicators))

    def _calculate_force_multiplier_score(self, stats: dict[str, Any]) -> float:
        """Calculate force multiplier capability score.

        Args:
            stats: Storage statistics

        Returns:
            float: Force multiplier score (0.0 to 1.0)

        """
        multiplier_indicators = []

        # Multi-graph support
        graph_types = [
            "knowledge_nodes",
            "causal_nodes",
            "social_nodes",
            "system_nodes",
        ]
        active_graphs = sum(1 for graph_type in graph_types if stats.get(graph_type, 0) > 0)
        multiplier_indicators.append(min(1.0, active_graphs / len(graph_types)))

        # Vector operations capability
        if stats.get("vectors_stored", 0) > 0:
            multiplier_indicators.append(0.5)

        # Cross-graph relationships (if implemented)
        # This would be checked when cross-graph operations are available

        return min(1.0, sum(multiplier_indicators) / 2)

    def _calculate_simplicity_score(self, storage_manager) -> float:
        """Calculate system simplicity score (anti-bloat measure).

        Args:
            storage_manager: StorageManager instance

        Returns:
            float: Simplicity score (0.0 to 1.0)

        """
        simplicity_indicators = []

        # Memory efficiency
        memory_usage = storage_manager.get_memory_usage()
        if memory_usage < 1024:  # Under 1GB is simple
            simplicity_indicators.append(1.0)
        elif memory_usage < 2048:  # Under 2GB is moderate
            simplicity_indicators.append(0.7)
        else:
            simplicity_indicators.append(0.3)

        # Configuration simplicity
        config = storage_manager.config
        simple_config = (
            not config.enable_gpu  # GPU is optional complexity
            or config.vector_dimension <= 768  # Standard embedding size
            or config.batch_size <= 1000  # Conservative batch size
        )
        simplicity_indicators.append(1.0 if simple_config else 0.5)

        # Direct interface (no enterprise bloat)
        # This is inherent in the implementation design
        simplicity_indicators.append(1.0)

        return sum(simplicity_indicators) / len(simplicity_indicators)

    def validate_operation(
        self,
        operation_type: str,
        operation_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a specific operation against constitutional requirements.

        Args:
            operation_type: Type of operation (e.g., 'create_node', 'store_vector')
            operation_data: Operation-specific data

        Returns:
            Dict[str, Any]: Validation result

        """
        validation_result = {
            "valid": True,
            "violations": [],
            "constitutional_score": 1.0,
            "recommendations": [],
        }

        # Memory impact validation
        if "memory_impact" in operation_data:
            memory_impact = operation_data["memory_impact"]
            if memory_impact > 100:  # 100MB threshold for individual operations
                validation_result["violations"].append(
                    f"Operation memory impact {memory_impact}MB exceeds solo developer limit",
                )
                validation_result["valid"] = False

        # Evidence validation
        if "evidence" not in operation_data:
            validation_result["violations"].append("Operation lacks evidence")
            validation_result["valid"] = False

        # Complexity validation
        complexity_indicators = len(operation_data.get("parameters", {}))
        if complexity_indicators > 10:  # Arbitrary complexity threshold
            validation_result["recommendations"].append(
                "Consider simplifying operation parameters for solo developer optimization",
            )

        return validation_result

    def get_compliance_report(self) -> dict[str, Any]:
        """Get detailed constitutional compliance report.

        Returns:
            Dict[str, Any]: Comprehensive compliance report

        """
        return {
            "timestamp": time.time(),
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "compliant": metric.value
                    >= (metric.threshold if metric.threshold < 1.0 else metric.threshold),
                    "description": metric.description,
                    "constitutional_basis": metric.constitutional_basis,
                }
                for metric in self.metrics
            ],
            "overall_compliance": (
                sum(m.value for m in self.metrics) / len(self.metrics) if self.metrics else 0.0
            ),
            "constitutional_basis": "CSF Constitution v4.0",
            "solo_developer_optimized": True,
            "anti_enterprise_bloat": True,
        }
