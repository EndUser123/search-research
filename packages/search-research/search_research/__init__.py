"""Top-level package exports for search-research.

This module provides the public API for the search-research package,
re-exporting key components from their implementation modules.
"""

# Canonical models
# HyDE query enhancement
from core.hyde import (
    apply_hyde,
    enhance_query,
    extract_key_phrases,
)
from core.models import (
    EnhancedQuery,
    ResearchResult,
    SearchResult,
)

# Enums
from core.modes import Mode

# Session chain traversal (for GTO skill integration)
from core.session_chain import (
    SessionChainEntry,
    SessionChainResult,
    get_all_chain_files,
    load_sessions_index,
    walk_handoff_chain,
    walk_session_chain,
    walk_sessions_index_chain,
)

# Core components
from core.unified_router import (
    AsyncSearchRouter,
    UnifiedAsyncRouter,
)

__all__ = [
    # Models
    "SearchResult",
    "EnhancedQuery",
    "ResearchResult",
    # Routers
    "AsyncSearchRouter",
    "UnifiedAsyncRouter",
    # Enums
    "Mode",
    # HyDE
    "apply_hyde",
    "enhance_query",
    "extract_key_phrases",
]
