"""Code Property Graph Backend - Unified code representation search.

Wraps CPGBuilder from modules.discover.code_property_graph.py for use in
unified search router. Provides query interface for data flow, control flow,
and semantic code structure queries.

Query patterns supported:
- "data flow for <variable>" - Trace data flow from definition to uses
- "control flow to <function>" - Find control flow paths to a function
- "functions in <file>" - List functions in a file
- "classes in <file>" - List classes in a file
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Import the CPGBuilder
try:
    from modules.discover.code_property_graph import (
        CPGBuilder,
        CodePropertyGraph,
        SemanticCPGBuilder,
        SemanticCPG,
    )
    CPG_AVAILABLE = True
except ImportError:
    CPG_AVAILABLE = False
    CPGBuilder = None  # type: ignore[misc, assignment]
    CodePropertyGraph = None  # type: ignore[misc, assignment]
    SemanticCPGBuilder = None  # type: ignore[misc, assignment]
    SemanticCPG = None  # type: ignore[misc, assignment]

from ...backend_health import BackendHealthRegistry


class CPGBackend:
    """
    Backend wrapper for Code Property Graph analysis.

    Provides search interface over CPGBuilder with query
    parsing for data flow, control flow, and code structure queries.
    """

    BACKEND_NAME: str = "CPG"

    def __init__(
        self,
        root_paths: list[str] | None = None,
        enable_health_tracking: bool = True,
        language: str = "python",
    ) -> None:
        """Initialize CPG backend.

        Args:
            root_paths: Root directories to analyze
            enable_health_tracking: Track backend health status
            language: Programming language (default: "python")
        """
        self._root_paths = root_paths or ["P:/__csf/src"]
        self._enable_health = enable_health_tracking
        self._language = language

        # Build CPG
        self._graph: Any = None
        self._semantic_cpg: Any = None
        self._health: BackendHealthRegistry | None = (
            BackendHealthRegistry() if enable_health_tracking else None
        )

        if CPG_AVAILABLE:
            self._build_graph()
        else:
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error="CPGBuilder not available",
                )

    def _build_graph(self) -> None:
        """Build the code property graph by analyzing source files."""
        if not CPG_AVAILABLE or CPGBuilder is None:
            return

        try:
            # Build semantic CPG for code search (supports multiple languages)
            builder = SemanticCPGBuilder()
            root = Path(self._root_paths[0]) if self._root_paths else Path("P:/__csf/src")
            self._semantic_cpg = builder.build(root)

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
        """Check if CPG has been built."""
        return self._semantic_cpg is not None

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search CPG for matching patterns.

        Args:
            query: Search query (e.g., "data flow for config", "functions in auth.py")
            limit: Maximum results to return

        Returns:
            List of search results with standardized format
        """
        if not self.has_index():
            return []

        query_lower = query.lower().strip()

        # Parse query pattern
        if "data flow for" in query_lower or "dataflow for" in query_lower:
            # Find data flow for a variable
            target = self._extract_target(query, "data flow for")
            return self._search_data_flow(target, limit)
        elif "control flow to" in query_lower or "control flow for" in query_lower:
            # Find control flow to a function
            target = self._extract_target(query, "control flow")
            return self._search_control_flow(target, limit)
        elif "functions in" in query_lower:
            # List functions in a file
            target = self._extract_target(query, "functions in")
            return self._search_functions_in_file(target, limit)
        elif "classes in" in query_lower:
            # List classes in a file
            target = self._extract_target(query, "classes in")
            return self._search_classes_in_file(target, limit)
        else:
            # Default: search for code entities by name
            return self._search_by_name(query, limit)

    def _extract_target(self, query: str, prefix: str) -> str:
        """Extract target name from query string."""
        query_lower = query.lower()
        if prefix in query_lower:
            return query_lower.replace(prefix, "").strip()
        return query.strip()

    def _search_data_flow(
        self,
        var_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find data flow paths for a variable.

        Note: Full data flow analysis requires DependencyGraph from
        quality.core.dependency_graph. This returns nodes that reference
        the variable name.
        """
        if not self._semantic_cpg or not hasattr(self._semantic_cpg, "nodes"):
            return []

        results = []
        var_name_lower = var_name.lower()

        # Search for nodes containing the variable name
        for node_id, node in list(self._semantic_cpg.nodes.items())[:limit]:
            # Check if node name, docstring, or signature contains variable
            text_content = (
                getattr(node, "name", "") +
                " " +
                getattr(node, "docstring", "") +
                " " +
                getattr(node, "signature", "")
            ).lower()

            if var_name_lower in text_content:
                results.append(self._semantic_node_to_result(
                    node,
                    f"data flow reference for {var_name}"
                ))

        return results

    def _search_control_flow(
        self,
        func_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find control flow information for a function.

        Returns control flow structures (if/for/while/try) within functions
        matching the given name.
        """
        if not self._semantic_cpg:
            return []

        results = []
        func_name_lower = func_name.lower()

        # Find matching functions
        for node_id, node in list(self._semantic_cpg.nodes.items())[:limit]:
            if func_name_lower in getattr(node, "name", "").lower():
                # Add control flow metadata if available
                control_flow = []
                if hasattr(self._semantic_cpg, "control_flow"):
                    for cf_entity, cf_type, cf_cond, cf_line in self._semantic_cpg.control_flow:
                        if cf_entity == node_id:
                            control_flow.append({
                                "type": cf_type,
                                "condition": cf_cond,
                                "line": cf_line,
                            })

                result = self._semantic_node_to_result(node, f"control flow for {func_name}")
                if control_flow:
                    result["metadata"]["control_flow"] = control_flow
                results.append(result)

        return results

    def _search_functions_in_file(
        self,
        file_path: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """List all functions in a specific file."""
        if not self._semantic_cpg:
            return []

        results = []
        file_path_lower = file_path.lower()

        # Find functions in the specified file
        for node_id, node in list(self._semantic_cpg.nodes.items())[:limit * 2]:  # Search more, filter after
            if getattr(node, "type", "") == "function":
                node_file = getattr(node, "file_path", "")
                if file_path_lower in node_file.lower():
                    results.append(self._semantic_node_to_result(
                        node,
                        f"function in {file_path}"
                    ))

        return results[:limit]

    def _search_classes_in_file(
        self,
        file_path: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """List all classes in a specific file."""
        if not self._semantic_cpg:
            return []

        results = []
        file_path_lower = file_path.lower()

        # Find classes in the specified file
        for node_id, node in list(self._semantic_cpg.nodes.items())[:limit * 2]:
            if getattr(node, "type", "") == "class":
                node_file = getattr(node, "file_path", "")
                if file_path_lower in node_file.lower():
                    results.append(self._semantic_node_to_result(
                        node,
                        f"class in {file_path}"
                    ))

        return results[:limit]

    def _search_by_name(
        self,
        name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for code entities by name pattern."""
        if not self._semantic_cpg or not hasattr(self._semantic_cpg, "nodes"):
            return []

        results = []
        name_lower = name.lower()

        for node_id, node in list(self._semantic_cpg.nodes.items())[:limit]:
            node_name = getattr(node, "name", "").lower()
            if name_lower in node_name:
                results.append(self._semantic_node_to_result(
                    node,
                    f"code entity matching {name}"
                ))

        return results

    def _semantic_node_to_result(
        self,
        node: Any,
        reason: str,
    ) -> dict[str, Any]:
        """Convert SemanticCPGNode to search result format."""
        return {
            "id": getattr(node, "id", f"unknown:{id(node)}"),
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": getattr(node, "name", "unknown"),
            "content": f"{getattr(node, 'name', 'unknown')} at {getattr(node, 'file_path', 'unknown')}:{getattr(node, 'start_line', 0)}",
            "score": 0.75,
            "reason": reason,
            "metadata": {
                "file_path": getattr(node, "file_path", ""),
                "line_number": getattr(node, "start_line", 0),
                "type": getattr(node, "type", "unknown"),
                "signature": getattr(node, "signature", ""),
                "docstring": getattr(node, "docstring", ""),
            },
        }

    def get_stats(self) -> dict[str, Any]:
        """Get CPG statistics."""
        if not self._semantic_cpg:
            return {"error": "CPG not built"}

        total_nodes = len(getattr(self._semantic_cpg, "nodes", {}))
        relationships = len(getattr(self._semantic_cpg, "relationships", []))
        control_flow = len(getattr(self._semantic_cpg, "control_flow", []))

        # Count by type
        type_counts = {}
        for node in getattr(self._semantic_cpg, "nodes", {}).values():
            node_type = getattr(node, "type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        return {
            "total_nodes": total_nodes,
            "relationships": relationships,
            "control_flow_entries": control_flow,
            "by_type": type_counts,
        }
