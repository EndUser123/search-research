"""Core RCA modules."""

from __future__ import annotations

__all__ = [
    "ContextAnalyzer",
    "ContextAnalyzerMetrics",
    "PerformanceOptimizer",
    "PerformanceOptimizerMetrics",
    "EnhancedRCACommand",
    "ToolSelector",
    "ToolSelectorMetrics",
]

# Core imports
try:
    from .context_analyzer import ContextAnalyzer, ContextAnalyzerMetrics
except ImportError:
    ContextAnalyzer = None  # type: ignore[assignment]
    ContextAnalyzerMetrics = None  # type: ignore[assignment]

try:
    from .performance_optimizer import (
        PerformanceOptimizer,
        PerformanceOptimizerMetrics,
    )
except ImportError:
    PerformanceOptimizer = None  # type: ignore[assignment]
    PerformanceOptimizerMetrics = None  # type: ignore[assignment]

try:
    from .rca_enhancer import EnhancedRCACommand
except ImportError:
    EnhancedRCACommand = None  # type: ignore[assignment]

try:
    from .tool_selector import ToolSelector, ToolSelectorMetrics
except ImportError:
    ToolSelector = None  # type: ignore[assignment]
    ToolSelectorMetrics = None  # type: ignore[assignment]
