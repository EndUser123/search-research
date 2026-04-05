"""
Semantic Daemon - Windows named pipe server for CHS/CKS search.

This is a Windows-specific daemon that provides fast semantic search
via named pipes. It is part of the search-research contrib modules.

Usage:
    from search_research.contrib.semantic_daemon import UnifiedSemanticDaemon, DaemonClient

    daemon = UnifiedSemanticDaemon()
    daemon.start()

    client = DaemonClient(auto_start=True)
    results = client.search("chs", "query", limit=10)
"""

from .daemon_client import DaemonClient
from .unified_semantic_daemon import SemanticClient, UnifiedSemanticDaemon

__all__ = [
    "UnifiedSemanticDaemon",
    "SemanticClient",
    "DaemonClient",
]
