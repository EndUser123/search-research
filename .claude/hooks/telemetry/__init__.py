"""
telemetry package - Verification gate telemetry collection system

TASK-010: Monitoring & Iteration

This package provides telemetry collection for verification gate hooks
with security fixes (SEC-003) for safe metrics logging.
"""

from .verification_metrics import (
    SECURE_PERMISSIONS,
    VerificationMetrics,
    collect_verification_metric,
    get_metrics_summary,
    sanitize_metric_entry,
)

__all__ = [
    "SECURE_PERMISSIONS",
    "VerificationMetrics",
    "collect_verification_metric",
    "get_metrics_summary",
    "sanitize_metric_entry",
]
