"""Dependency Graph Backend - Cross-file reference and call graph search.

Wraps DependencyGraph from quality.core.dependency_graph.py for use in
unified search router. Provides query interface for unused symbols, impact
analysis, and dependency relationships.

Query patterns supported:
- "unused in <file>" - Find unused symbols in a file
- "callers of <function>" - Find what calls a given function
- "callees of <function>" - Find what a function calls
- "impact of <symbol>" - Analyze impact of removing a symbol
- "cycles" - Detect circular dependencies
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Import the DependencyGraph
try:
    from quality.core.dependency_graph import (
        DependencyGraph,
        DependencyGraphBuilder,
        build_dependency_graph,
        Symbol,
        EdgeKind,
    )
    DEP_GRAPH_AVAILABLE = True
except ImportError:
    DEP_GRAPH_AVAILABLE = False
    DependencyGraph = None  # type: ignore[misc, assignment]
    DependencyGraphBuilder = None  # type: ignore[misc, assignment]
    build_dependency_graph = None  # type: ignore[misc, assignment]
    Symbol = None  # type: ignore[misc, assignment]
    EdgeKind = None  # type: ignore[misc, assignment]

from ...backend_health import BackendHealthRegistry


class DependencyBackend:
    """
    Backend wrapper for dependency graph analysis.

    Provides search interface over DependencyGraph with query
    parsing for unused symbols, call graph queries, and impact analysis.
    """

    BACKEND_NAME: str = "DEPENDENCY"

    def __init__(
        self,
        root_paths: list[str] | None = None,
        enable_health_tracking: bool = True,
    ) -> None:
        """Initialize dependency graph backend.

        Args:
            root_paths: Root directories to analyze
            enable_health_tracking: Track backend health status
        """
        self._root_paths = root_paths or ["P:/__csf/src"]
        self._enable_health = enable_health_tracking

        # Build dependency graph
        self._graph: Any = None
        self._health: BackendHealthRegistry | None = (
            BackendHealthRegistry() if enable_health_tracking else None
        )

        if DEP_GRAPH_AVAILABLE:
            self._build_graph()
        else:
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error="DependencyGraph not available",
                )

    def _build_graph(self) -> None:
        """Build the dependency graph by analyzing source files."""
        if not DEP_GRAPH_AVAILABLE or build_dependency_graph is None:
            return

        try:
            # Collect Python files from root paths
            files = []
            for root_path in self._root_paths:
                root = Path(root_path)
                if root.is_file():
                    files.append(root)
                else:
                    files.extend(root.rglob("*.py"))

            if files:
                # Build graph with subset of files for performance
                # Limit to first 500 files for quick initialization
                sample_files = list(files)[:500]
                self._graph = build_dependency_graph(sample_files)

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
        """Check if dependency graph has been built."""
        return self._graph is not None

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search dependency graph for matching patterns.

        Args:
            query: Search query (e.g., "unused in file.py", "callers of foo")
            limit: Maximum results to return

        Returns:
            List of search results with standardized format
        """
        if not self.has_index():
            return []

        query_lower = query.lower().strip()

        # Parse query pattern
        if "unused in" in query_lower:
            # Find unused symbols in a file
            target = self._extract_target(query, "unused in")
            return self._search_unused(target, limit)
        elif "callers of" in query_lower or "who calls" in query_lower:
            # Find callers of a function
            target = self._extract_target(query, "callers of")
            return self._search_callers(target, limit)
        elif "callees of" in query_lower or "what does.*call" in query_lower:
            # Find callees of a function
            target = self._extract_target(query, "callees of")
            return self._search_callees(target, limit)
        elif "impact of" in query_lower:
            # Analyze impact of removing a symbol
            target = self._extract_target(query, "impact of")
            return self._search_impact(target, limit)
        elif "cycle" in query_lower:
            # Detect circular dependencies
            return self._search_cycles(limit)
        elif "data flow for" in query_lower or "dataflow for" in query_lower:
            # Trace data flow
            target = self._extract_target(query, "data flow")
            return self._search_data_flow(target, limit)
        else:
            # Default: search for symbols by name
            return self._search_by_name(query, limit)

    def _extract_target(self, query: str, prefix: str) -> str:
        """Extract target name from query string."""
        query_lower = query.lower()
        if prefix in query_lower:
            return query_lower.replace(prefix, "").strip()
        return query.strip()

    def _search_unused(
        self,
        file_path: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find unused symbols in a file."""
        if not self._graph or not hasattr(self._graph, "find_unused_symbols"):
            return []

        try:
            unused = self._graph.find_unused_symbols(file_path)
            results = []

            for symbol in list(unused)[:limit]:
                results.append(self._symbol_to_result(
                    symbol,
                    f"unused {symbol.kind.value} in {file_path}"
                ))

            return results
        except Exception:
            return []

    def _search_callers(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find symbols that call the given function."""
        if not self._graph or not hasattr(self._graph, "get_callers"):
            return []

        results = []
        func_name_lower = func_name.lower()

        # Find the target symbol
        target_symbol = None
        for symbol in self._graph.symbols.values():
            if func_name_lower in symbol.name.lower():
                target_symbol = symbol
                break

        if not target_symbol:
            return []

        try:
            callers = self._graph.get_callers(target_symbol)
            for caller in list(callers)[:limit]:
                results.append(self._symbol_to_result(
                    caller,
                    f"caller of {func_name}"
                ))
        except Exception:
            pass

        return results

    def _search_callees(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find symbols called by the given function."""
        if not self._graph or not hasattr(self._graph, "get_callees"):
            return []

        results = []
        func_name_lower = func_name.lower()

        # Find the source symbol
        source_symbol = None
        for symbol in self._graph.symbols.values():
            if func_name_lower in symbol.name.lower():
                source_symbol = symbol
                break

        if not source_symbol:
            return []

        try:
            callees = self._graph.get_callees(source_symbol)
            for callee in list(callees)[:limit]:
                results.append(self._symbol_to_result(
                    callee,
                    f"{func_name} calls"
                ))
        except Exception:
            pass

        return results

    def _search_impact(
        self,
        symbol_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Analyze impact of removing a symbol."""
        if not self._graph or not hasattr(self._graph, "compute_impact"):
            return []

        results = []
        symbol_name_lower = symbol_name.lower()

        # Find the target symbol
        target_symbol = None
        for symbol in list(self._graph.symbols.values())[:limit]:
            if symbol_name_lower in symbol.name.lower():
                target_symbol = symbol
                break

        if not target_symbol:
            return []

        try:
            impact = self._graph.compute_impact(target_symbol)
            results.append({
                "id": f"dep_impact_{symbol_name}",
                "source": self.BACKEND_NAME,
                "backend": self.BACKEND_NAME,
                "title": f"Impact of removing {symbol_name}",
                "content": (
                    f"Direct callers: {impact.get('direct_callers', 0)}, "
                    f"Total callers: {impact.get('total_callers', 0)}, "
                    f"Risk: {impact.get('risk', 'unknown')}"
                ),
                "score": 0.7,
                "reason": f"impact analysis for {symbol_name}",
                "metadata": {
                    "symbol_name": symbol_name,
                    "impact_details": impact,
                },
            })
        except Exception:
            pass

        return results

    def _search_cycles(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Detect circular dependencies."""
        if not self._graph or not hasattr(self._graph, "detect_cycles"):
            return []

        results = []

        try:
            cycles = self._graph.detect_cycles()
            for i, cycle in enumerate(list(cycles)[:limit]):
                results.append({
                    "id": f"dep_cycle_{i}",
                    "source": self.BACKEND_NAME,
                    "backend": self.BACKEND_NAME,
                    "title": f"Circular dependency {i + 1}",
                    "content": " -> ".join(cycle) + f" -> {cycle[0]}" if cycle else "",
                    "score": 0.6,
                    "reason": "circular dependency",
                    "metadata": {
                        "cycle": cycle,
                        "length": len(cycle),
                    },
                })
        except Exception:
            pass

        return results

    def _search_data_flow(
        self,
        var_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Trace data flow from variable definition to uses."""
        if not self._graph or not hasattr(self._graph, "find_data_flow"):
            return []

        results = []

        try:
            paths = self._graph.find_data_flow(var_name, max_depth=10)
            for i, path in enumerate(list(paths)[:limit]):
                steps_str = " -> ".join([
                    f"{f}:{l}" for f, l in list(path.steps)[:5]
                ]) if path.steps else "direct"

                results.append({
                    "id": f"dep_dataflow_{i}",
                    "source": self.BACKEND_NAME,
                    "backend": self.BACKEND_NAME,
                    "title": f"Data flow for {var_name}",
                    "content": (
                        f"{var_name} at {path.start_location} -> "
                        f"{path.end_location} via {steps_str}"
                    ),
                    "score": 0.75,
                    "reason": f"data flow for {var_name}",
                    "metadata": {
                        "var_name": var_name,
                        "confidence": path.confidence,
                        "path": path.to_dict() if hasattr(path, "to_dict") else {},
                    },
                })
        except Exception:
            pass

        return results

    def _search_by_name(
        self,
        name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for symbols by name pattern."""
        if not self._graph or not hasattr(self._graph, "symbols"):
            return []

        results = []
        name_lower = name.lower()

        for symbol in list(self._graph.symbols.values())[:limit]:
            if name_lower in symbol.name.lower():
                results.append(self._symbol_to_result(
                    symbol,
                    f"symbol matching {name}"
                ))

        return results

    def _symbol_to_result(
        self,
        symbol: Any,
        reason: str,
    ) -> dict[str, Any]:
        """Convert Symbol to search result format."""
        return {
            "id": f"{symbol.file_path}:{symbol.line}:{symbol.name}",
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": symbol.name,
            "content": f"{symbol.kind.value} {symbol.name} at {symbol.file_path}:{symbol.line}",
            "score": 0.75,
            "reason": reason,
            "metadata": {
                "file_path": symbol.file_path,
                "line_number": symbol.line,
                "symbol_kind": symbol.kind.value,
                "scope": symbol.scope,
                "is_exported": symbol.is_exported,
                "is_private": symbol.is_private,
            },
        }

    def get_stats(self) -> dict[str, Any]:
        """Get dependency graph statistics."""
        if not self._graph:
            return {"error": "Graph not built"}

        stats = {
            "total_symbols": len(self._graph.symbols),
            "total_edges": len(self._graph.edges),
            "files_analyzed": getattr(self._graph, "files_analyzed", 0),
        }

        # Add breakdown by symbol kind
        kind_counts = {}
        for symbol in self._graph.symbols.values():
            kind = symbol.kind.value
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
        stats["by_kind"] = kind_counts

        return stats
