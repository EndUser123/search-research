"""
Core utilities package for yt-fts.

This package contains reusable base classes and patterns for routing,
coordinating, and managing operations across multiple backends/providers.
"""
from __future__ import annotations

from yt_fts.core_utils.meta_router import (
    AsyncMetaRouter,
    HealthStatus,
    MetaRouter,
    ProviderConfig,
    ProviderResult,
    RoutingStrategy,
)

__all__ = [
    "AsyncMetaRouter",
    "HealthStatus",
    "MetaRouter",
    "ProviderConfig",
    "ProviderResult",
    "RoutingStrategy",
]
