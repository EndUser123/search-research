"""Call Graph Backend - Static call relationship search.

Wraps StaticCallGraphBuilder from modules.discover.static_call_graph.py for use in
unified search router. Provides query interface for callers/callees/entry_points.

Query patterns supported:
- "callers of <function>" - Find what calls a given function
- "callees of <function>" - Find what a function calls
- "entry points" - Find functions not called by others
"""

from __future__ import annotations

from typing import Any

# Import the StaticCallGraphBuilder
try:
    from modules.discover.static_call_graph import CallGraph, StaticCallGraphBuilder

    STATIC_GRAPH_AVAILABLE = True
except ImportError:
    STATIC_GRAPH_AVAILABLE = False
    StaticCallGraphBuilder = None  # type: ignore[misc, assignment]
    CallGraph = None  # type: ignore[misc, assignment]

from ...backend_health import BackendHealthRegistry


# Backend identifier
BACKEND_NAME_CALL_GRAPH = "CALL_GRAPH"


class CallGraphBackend:
    """
    Backend wrapper for static call graph analysis.

    Provides search interface over StaticCallGraphBuilder with query
    parsing for callers, callees, and entry points.
    """

    BACKEND_NAME: str = "CALL_GRAPH"

    def __init__(
        self,
        root_paths: list[str] | None = None,
        enable_health_tracking: bool = True,
    ):
        """Initialize call graph backend.

        Args:
            root_paths: Root directories to analyze
            enable_health_tracking: Track backend health status
        """
        self._root_paths = root_paths or ["P:/packages/search-research"]
        self._enable_health = enable_health_tracking

        # Build call graph
        self._graph: Any = None
        self._health: BackendHealthRegistry | None = (
            BackendHealthRegistry() if enable_health_tracking else None
        )

        if STATIC_GRAPH_AVAILABLE:
            self._build_graph()
        else:
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error="StaticCallGraphBuilder not available",
                )

    def _build_graph(self) -> None:
        """Build the call graph by analyzing source files."""
        if not STATIC_GRAPH_AVAILABLE or StaticCallGraphBuilder is None:
            return

        try:
            builder = StaticCallGraphBuilder(root_paths=self._root_paths)
            builder.analyze()
            self._graph = builder.get_graph()

            if self._health:
                self._health.record_result(self.BACKEND_NAME, success=True)
        except Exception as e:
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error=str(e),
                )

    def has_index(self) -> bool:
        """Check if call graph has been built."""
        return self._graph is not None

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search call graph for matching patterns.

        Args:
            query: Search query (e.g., "callers of foo", "callees of bar", "entry points")
            limit: Maximum results to return

        Returns:
            List of search results with standardized format
        """
        if not self.has_index():
            return []

        query_lower = query.lower().strip()

        # Parse query pattern
        if "callers of" in query_lower or "who calls" in query_lower:
            # Find callers of a function
            target = self._extract_function_name(query)
            return self._search_callers(target, limit)
        elif "callees of" in query_lower or "what does.*call" in query_lower:
            # Find callees of a function
            target = self._extract_function_name(query)
            return self._search_callees(target, limit)
        elif "entry point" in query_lower or "entry points" in query_lower:
            # Find entry points
            return self._search_entry_points(limit)
        else:
            # Default: search for function by name
            return self._search_by_name(query, limit)

    def _extract_function_name(self, query: str) -> str:
        """Extract function name from query string."""
        # Remove common query prefixes
        for prefix in ["callers of ", "callees of ", "who calls ", "what does ", "who calls "]:
            if prefix in query.lower():
                return query.lower().replace(prefix, "").strip()

        # Handle "X calls Y" pattern
        query_lower = query.lower()
        if " calls " in query_lower:
            parts = query_lower.split(" calls ")
            if len(parts) == 2:
                return parts[0].strip()

        return query.strip()

    def _search_callers(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find functions that call the given function."""
        if not hasattr(self._graph, "get_callers"):
            return []

        try:
            callers = self._graph.get_callers(func_name)
            results = []
            for caller in callers[:limit]:
                node = self._graph.functions.get(caller)
                if node:
                    results.append(self._node_to_result(node, "caller of " + func_name))
            return results
        except Exception:
            return []

    def _search_callees(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find functions called by the given function."""
        if not hasattr(self._graph, "get_callees"):
            return []

        try:
            callees = self._graph.get_callees(func_name)
            results = []
            for callee in callees[:limit]:
                node = self._graph.functions.get(callee)
                if node:
                    results.append(self._node_to_result(node, func_name + " calls "))
            return results
        except Exception:
            return []

    def _search_entry_points(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find entry point functions (not called by others)."""
        if not hasattr(self._graph, "get_entry_points"):
            return []

        try:
            entry_points = self._graph.get_entry_points()
            results = []
            for ep in entry_points[:limit]:
                node = self._graph.functions.get(ep)
                if node:
                    results.append(self._node_to_result(node, "entry point"))
            return results
        except Exception:
            return []

    def _search_by_name(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for functions by name pattern."""
        if not self._graph or not hasattr(self._graph, "functions"):
            return []

        results = []
        func_name_lower = func_name.lower()

        for name, node in self._graph.functions.items():
            if func_name_lower in node.name.lower():
                results.append(self._node_to_result(node, "function match"))
                if len(results) >= limit:
                    break

        return results

    def _node_to_result(
        self,
        node: Any,
        reason: str,
    ) -> dict[str, Any]:
        """Convert CallNode to search result format."""
        return {
            "id": f"{node.file}:{node.line}:{node.name}",
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": node.name,
            "content": f"{node.name}() at {node.file}:{node.line}",
            "score": 0.8,
            "reason": reason,
            "metadata": {
                "file_path": node.file,
                "line_number": node.line,
                "is_method": node.is_method,
                "class_name": node.class_name or "",
                "is_external": node.is_external,
            },
        }

    def get_stats(self) -> dict[str, Any]:
        """Get call graph statistics."""
        if not self._graph:
            return {"error": "Graph not built"}

        return {
            "total_functions": len(self._graph.functions),
            "total_calls": sum(len(callees) for callees in self._graph._calls.values()),
            "entry_points": len(self._graph.get_entry_points())
            if hasattr(self._graph, "get_entry_points")
            else 0,
        }
