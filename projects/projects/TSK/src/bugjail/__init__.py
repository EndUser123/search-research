"""
BugJail - Automated Bug Detection System

Phase 2 Implementation for CSF NIP Security Framework

Comprehensive bug detection and vulnerability scanning system with:
- Pattern-based bug detection
- Static analysis integration
- Vulnerability scanning with OWASP compliance
- Constitutional security validation
- Actionable fix recommendations
- Integration with exploration workflow
"""

from .core.analyzer import BugJailAnalyzer
from .core.detector import BugJailDetector
from .core.types import (
    AnalysisReport,
    BugCategory,
    BugJailConfig,
    BugSeverity,
    DetectionResult,
    VulnerabilityType,
)

__version__ = "2.0.0"
__author__ = "CSF NIP Security Agent"

# Convenience exports
__all__ = [
    "BugJailDetector",
    "BugJailAnalyzer",
    "BugSeverity",
    "BugCategory",
    "VulnerabilityType",
    "DetectionResult",
    "AnalysisReport",
    "BugJailConfig"
]
