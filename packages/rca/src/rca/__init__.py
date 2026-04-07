"""rca Tier 1 Implementation.

Evidence saturation detection, phase state persistence, hypothesis scoring,
evidence tiering, and flow-of-action tracing for root cause analysis debugging workflows.
"""

__version__ = "2.5.0"

# Main Tier 1 classes
# Flow-of-Action Paradigm (Task #986)
from .action_tracer import (
    EXPECTED_PATHS,
    Action,
    ActionGraph,
    ActionTracer,
    ActionType,
    classify_action,
    create_tracer_for_session,
    get_expected_path,
)
from .config import LocalFallbackMode as ConfigLocalFallbackMode
from .converge_validator import ConvergeValidator, ValidationResult
from .debugpy_client import DebugCapture, DebugPyClient, DebugStateExtractor, StackFrame
from .evidence_saturation import EvidenceSaturationDetector

# Evidence Tiering (Task #988)
from .evidence_tier import (
    SOURCE_TYPE_TIERS,
    EvidenceLedger,
    EvidenceSource,
    EvidenceTier,
    apply_ceiling,
    classify_evidence,
    format_evidence_summary,
    get_confidence_ceiling,
    get_lowest_tier,
    store_rca_finding,  # CKS integration convenience function
)
from .error_signature import (
    ErrorSignature,
    ErrorSignatureExtractor,
    extract_signature,
    match_to_pattern,
)
from .flow_visualizer import (
    FlowVisualizer,
    VisualizationConfig,
    create_visualizer,
    render_flow_from_session,
)
from .hypothesis_generator import (
    DEFAULT_WEIGHTS,
    Hypothesis,
    HypothesisCategory,
    HypothesisSet,
    calculate_hypothesis_confidence,
    generate_hypotheses,
    generate_hypotheses_from_evidence,
)
from .hypothesis_scorer import HypothesisScorer
from .stack_trace_fingerprint import (
    FixRecord,
    StackTraceFingerprint,
    fingerprint_from_error,
)

# Metrics tracking
from .metrics_tracker import (
    FixType,
    MatchType,
    MetricAlert,
    MetricThresholds,
    RCAMetrics,
    RCAMetricsTracker,
    RCASession,
    check_metric_alerts,
    enforce_verification_gate,
    format_alerts,
    get_debug_stats,
    get_metrics_tracker,
    get_metrics_with_alerts,
    problem_hash,
    record_chs_search,
    record_debug_start,
    record_delegation_event,
    record_fix,
    record_verification,
)
from .phase_state_manager import PhaseStateManager
from .quality_estimator import (
    ISSUE_TYPE_WEIGHTS,
    TOOL_WEIGHTS,
    QualityEstimator,
    get_quality_summary,
)

# Session management and problem classification
from .session import (
    ProblemType,
    classify_problem_type,
    detect_error_type,
    load_active_session,
    manage_active_session,
    run_regression_check,
    search_cks_history,
)

# Meta-RAG: Unified search integration (Task #987)
from .simple_rca_engine import (
    RCAAnalysis,
    RCAMethodologyResult,
    SimpleRCAEngine,
)

# Log File Discovery (Task #1536)
from .log_discovery import (
    LogDiscoveryEngine,
    LogDiscoveryResult,
    LogFile,
    LogFinding,
    LogPattern,
    discover_logs_for_problem,
)

__all__ = [
    "__version__",
    # Core RCA modules
    "EvidenceSaturationDetector",
    "PhaseStateManager",
    "HypothesisScorer",
    # Evidence Tiering (Task #988)
    "EvidenceTier",
    "EvidenceSource",
    "EvidenceLedger",
    "classify_evidence",
    "get_lowest_tier",
    "get_confidence_ceiling",
    "apply_ceiling",
    "format_evidence_summary",
    "SOURCE_TYPE_TIERS",
    "store_rca_finding",  # CKS integration
    # Flow-of-Action Paradigm (Task #986)
    "Action",
    "ActionGraph",
    "ActionTracer",
    "ActionType",
    "classify_action",
    "create_tracer_for_session",
    "get_expected_path",
    "EXPECTED_PATHS",
    "FlowVisualizer",
    "VisualizationConfig",
    "create_visualizer",
    "render_flow_from_session",
    # Convergence validation
    "ConvergeValidator",
    "ValidationResult",
    # Debugpy integration
    "DebugPyClient",
    "DebugCapture",
    "DebugStateExtractor",
    "StackFrame",
    # Local fallback mode
    "ConfigLocalFallbackMode",
    # Quality estimation
    "QualityEstimator",
    "ISSUE_TYPE_WEIGHTS",
    "TOOL_WEIGHTS",
    "get_quality_summary",
    # Session management
    "ProblemType",
    "classify_problem_type",
    "detect_error_type",
    "manage_active_session",
    "load_active_session",
    "search_cks_history",
    "run_regression_check",
    # Metrics tracking
    "RCASession",
    "RCAMetrics",
    "RCAMetricsTracker",
    "problem_hash",
    "get_metrics_tracker",
    "record_debug_start",
    "record_chs_search",
    "record_fix",
    "record_verification",
    "record_delegation_event",
    "get_debug_stats",
    "MetricAlert",
    "MetricThresholds",
    "check_metric_alerts",
    "format_alerts",
    "get_metrics_with_alerts",
    "enforce_verification_gate",
    "FixType",
    "MatchType",
    # Meta-RAG: Unified search integration (Task #987)
    "SimpleRCAEngine",
    "RCAAnalysis",
    "RCAMethodologyResult",
    # Log File Discovery (Task #1536)
    "LogDiscoveryEngine",
    "LogDiscoveryResult",
    "LogFile",
    "LogFinding",
    "LogPattern",
    "discover_logs_for_problem",
    # Hypothesis Generation
    "Hypothesis",
    "HypothesisCategory",
    "HypothesisSet",
    "DEFAULT_WEIGHTS",
    "generate_hypotheses",
    "generate_hypotheses_from_evidence",
    "calculate_hypothesis_confidence",
    # Error Signature
    "ErrorSignature",
    "ErrorSignatureExtractor",
    "extract_signature",
    "match_to_pattern",
    # Stack Trace Fingerprinting
    "StackTraceFingerprint",
    "FixRecord",
    "fingerprint_from_error",
]
