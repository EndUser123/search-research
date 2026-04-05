"""Integration modules for RCA."""

from __future__ import annotations

__all__ = [
    "CKSPatternRegistry",
    "ExploreIntegration",
    "RCASpecialistSignatureBridge",
    "SignatureAnalysisResult",
    "get_cks_pattern_registry",
    "lookup_cks_pattern_fix",
    "register_cks_pattern_fix",
    "analyze_error_with_signatures",
    "get_fix_suggestions_for_rca",
    "register_fix_from_rca",
]

# CKS Pattern Integration
try:
    from .cks_pattern_integration import (
        CKSPatternRegistry,
        get_cks_pattern_registry,
        lookup_cks_pattern_fix,
        register_cks_pattern_fix,
    )
except ImportError:
    CKSPatternRegistry = None  # type: ignore[assignment]
    get_cks_pattern_registry = None  # type: ignore[assignment]
    lookup_cks_pattern_fix = None  # type: ignore[assignment]
    register_cks_pattern_fix = None  # type: ignore[assignment]

# Explore Integration
try:
    from .explore_integration import ExploreIntegration
except ImportError:
    ExploreIntegration = None  # type: ignore[assignment]

# TaskMaster Integration (DEPRECATED - removed TaskMaster dependency)
# Pattern storage now handled by CKS (see cks_pattern_integration.py)
TaskMasterIntegration = None  # type: ignore[assignment]

# RCA Specialist Integration
try:
    from .rca_specialist_integration import (
        RCASpecialistSignatureBridge,
        SignatureAnalysisResult,
        analyze_error_with_signatures,
        get_fix_suggestions_for_rca,
        register_fix_from_rca,
    )
except ImportError:
    RCASpecialistSignatureBridge = None  # type: ignore[assignment]
    SignatureAnalysisResult = None  # type: ignore[assignment]
    analyze_error_with_signatures = None  # type: ignore[assignment]
    get_fix_suggestions_for_rca = None  # type: ignore[assignment]
    register_fix_from_rca = None  # type: ignore[assignment]
