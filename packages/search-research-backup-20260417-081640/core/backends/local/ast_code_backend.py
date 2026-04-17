"""AST-based Code Analysis Backend.

Lightweight code analysis using Python's AST module.
Provides dependents, dependencies, and control flow analysis
without requiring CPG, embeddings, or vector storage.

This is a pragmatic implementation for the LSP query interface
when full CPG infrastructure is unavailable.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Backend identifier
BACKEND_AST_CODE = "AST_CODE"
SOURCE_RELIABILITY_AST = 0.80


class ASTCodeBackend:
    """AST-based code analysis backend.

    Provides lightweight code analysis features:
    - Entity indexing (functions, classes, methods)
    - Dependency tracking (imports, function calls)
    - Control flow extraction (if/while/for/try)
    - Semantic search (name-based)

    This backend works standalone without external dependencies.
    """

    def __init__(self, root_paths: list[str] | None = None):
        """Initialize AST Code Backend.

        Args:
            root_paths: List of root directories to analyze.
        """
        self.root_paths = [Path(p) for p in (root_paths or ["P:/__csf/src"])]
        self._entity_index: dict[str, dict[str, Any]] = {}
        self._call_graph: dict[str, set[str]] = {}  # entity_id -> callers
        self._reverse_call_graph: dict[str, set[str]] = {}  # entity_id -> callees
        self._control_flow_cache: dict[str, dict[str, list[dict]]] = {}
        self._indexed = False

        logger.info(f"ASTCodeBackend initialized with {len(self.root_paths)} paths")

    def build_index(self) -> None:
        """Build entity index from Python files."""
        self._entity_index = {}
        self._call_graph = {}
        self._reverse_call_graph = {}
        self._control_flow_cache = {}

        for root_path in self.root_paths:
            self._index_directory(root_path)

        self._indexed = True
        logger.info(f"ASTCodeBackend indexed {len(self._entity_index)} entities")

    def _index_directory(self, root_path: Path) -> None:
        """Index all Python files in a directory."""
        for py_file in root_path.rglob("*.py"):
            try:
                self._index_file(py_file)
            except Exception as e:
                logger.debug(f"Failed to index {py_file}: {e}")

    def _index_file(self, file_path: Path) -> None:
        """Index a single Python file."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(file_path))
        except Exception:
            return

        # Track imports for this file
        file_imports = set()
        file_entity_id = f"file:{file_path.relative_to(file_path.anchor)}"

        # First pass: collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_imports.add(node.module)

        # Store file entity
        self._entity_index[file_entity_id] = {
            "type": "file",
            "file_path": str(file_path),
            "imports": list(file_imports),
        }

        # Second pass: index classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._index_class(node, file_path, source)
            elif isinstance(node, ast.FunctionDef):
                self._index_function(node, file_path, source)

    def _index_class(self, node: ast.ClassDef, file_path: Path, source: str) -> None:
        """Index a class definition."""
        rel_path = file_path.relative_to(file_path.anchor)
        entity_id = f"class:{rel_path}:{node.name}"

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        # Index methods
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                self._index_function(item, file_path, source, class_name=node.name)

        self._entity_index[entity_id] = {
            "type": "class",
            "name": node.name,
            "file_path": str(file_path),
            "line": node.lineno,
            "bases": bases,
            "methods": methods,
        }

    def _index_function(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        source: str,
        class_name: str | None = None,
    ) -> None:
        """Index a function definition."""
        rel_path = file_path.relative_to(file_path.anchor)

        if class_name:
            entity_id = f"func:{rel_path}:{class_name}.{node.name}"
            display_name = f"{class_name}.{node.name}"
        else:
            entity_id = f"func:{rel_path}:{node.name}"
            display_name = node.name

        # Extract calls made by this function
        calls = self._extract_calls(node)

        # Extract control flow
        control_flow = self._extract_control_flow(node)

        # Get signature
        args = [arg.arg for arg in node.args.args]
        signature = f"def {node.name}({', '.join(args)})"

        self._entity_index[entity_id] = {
            "type": "function",
            "name": display_name,
            "file_path": str(file_path),
            "line": node.lineno,
            "signature": signature,
            "calls": calls,
        }

        # Store control flow
        self._control_flow_cache[entity_id] = control_flow

        # Update call graphs
        self._call_graph[entity_id] = set()
        for call in calls:
            self._call_graph[entity_id].add(call)
            if call not in self._reverse_call_graph:
                self._reverse_call_graph[call] = set()
            self._reverse_call_graph[call].add(entity_id)

    def _extract_calls(self, node: ast.FunctionDef) -> list[str]:
        """Extract function calls from a function."""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Get the function name
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(ast.unparse(child.func))

        return calls

    def _extract_control_flow(self, node: ast.FunctionDef) -> dict[str, list[dict]]:
        """Extract control flow branches from a function."""
        branches = {
            "if": [],
            "while": [],
            "for": [],
            "try": [],
        }

        for child in ast.walk(node):
            # For top-level statements only (avoid nested duplicates)
            if child not in node.body:
                continue

            if isinstance(child, ast.If):
                condition = ast.unparse(child.test)
                branches["if"].append({
                    "type": "if",
                    "condition": condition[:100],  # Truncate long conditions
                    "line": child.lineno,
                })
            elif isinstance(child, ast.While):
                condition = ast.unparse(child.test)
                branches["while"].append({
                    "type": "while",
                    "condition": condition[:100],
                    "line": child.lineno,
                })
            elif isinstance(child, ast.For):
                target = ast.unparse(child.target)
                iter_expr = ast.unparse(child.iter)
                branches["for"].append({
                    "type": "for",
                    "condition": f"{target} in {iter_expr}"[:100],
                    "line": child.lineno,
                })
            elif isinstance(child, ast.Try):
                handlers = []
                for handler in child.handlers:
                    if handler.type:
                        exc_type = ast.unparse(handler.type)
                        handlers.append(exc_type)
                branches["try"].append({
                    "type": "try",
                    "condition": ", ".join(handlers)[:100],
                    "line": child.lineno,
                })

        return branches

    # Public API methods

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for entities by name.

        Args:
            query: Search query (entity name or pattern).
            limit: Maximum results.

        Returns:
            List of matching entities.
        """
        if not self._indexed:
            self.build_index()

        query_lower = query.lower()
        results = []

        for entity_id, entity in self._entity_index.items():
            name = entity.get("name", "")
            if query_lower in name.lower():
                results.append({
                    "id": entity_id,
                    "title": f"{entity['type'].capitalize()}: {name}",
                    "content": entity.get("signature", name),
                    "score": 1.0 if query_lower == name.lower() else 0.8,
                    "metadata": {
                        "file_path": entity.get("file_path", ""),
                        "line": entity.get("line", 0),
                        "entity_type": entity["type"],
                    },
                })

        return results[:limit]

    async def asearch(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Async version of search for compatibility."""
        return self.search(query, limit)

    def get_dependents(self, entity_id: str, limit: int = 50) -> list[str]:
        """Get entities that depend on this entity.

        Args:
            entity_id: Entity ID to find dependents for.
            limit: Maximum results.

        Returns:
            List of entity IDs that depend on this entity.
        """
        if not self._indexed:
            self.build_index()

        # Check reverse call graph
        dependents = list(self._reverse_call_graph.get(entity_id, set()))

        # Also check for file-level dependencies
        if entity_id.startswith("file:"):
            # Find functions/classes in this file
            file_path = entity_id.split(":", 1)[1]
            for eid, entity in self._entity_index.items():
                if entity.get("file_path", "").endswith(file_path) and eid != entity_id:
                    dependents.append(eid)

        return dependents[:limit]

    def get_dependencies(self, entity_id: str, limit: int = 50) -> list[str]:
        """Get entities that this entity depends on.

        Args:
            entity_id: Entity ID to find dependencies for.
            limit: Maximum results.

        Returns:
            List of entity IDs that this entity depends on.
        """
        if not self._indexed:
            self.build_index()

        entity = self._entity_index.get(entity_id)
        if not entity:
            return []

        dependencies = []

        # Add calls
        for call in entity.get("calls", []):
            dependencies.append(f"call:{call}")

        # Add imports for files
        if entity["type"] == "file":
            for imp in entity.get("imports", []):
                dependencies.append(f"module:{imp}")

        # Add base classes for classes
        if entity["type"] == "class":
            for base in entity.get("bases", []):
                dependencies.append(f"class:{base}")

        return dependencies[:limit]

    def get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]:
        """Get control flow for an entity.

        Args:
            entity_id: Entity ID to get control flow for.

        Returns:
            Dictionary mapping branch types to lists of branches.
        """
        if not self._indexed:
            self.build_index()

        entity = self._entity_index.get(entity_id)
        if not entity:
            return {}

        # For functions, return cached control flow
        if entity["type"] == "function":
            return self._control_flow_cache.get(entity_id, {})

        # For other entities, return empty
        return {}

    def get_related(self, entity_id: str, limit: int = 50) -> list[str]:
        """Get related entities (dependents + dependencies).

        Args:
            entity_id: Entity ID to find related entities for.
            limit: Maximum results.

        Returns:
            List of related entity IDs.
        """
        dependents = set(self.get_dependents(entity_id))
        dependencies = set(self.get_dependencies(entity_id))
        related = dependents | dependencies
        return list(related)[:limit]

    def analyze_impact(self, entity_id: str) -> dict[str, Any]:
        """Analyze the impact of changing an entity.

        Args:
            entity_id: Entity ID to analyze.

        Returns:
            Dict with risk_level, safe_to_change, and affected counts.
        """
        dependents = self.get_dependents(entity_id)
        dependencies = self.get_dependencies(entity_id)
        control_flow = self.get_control_flow(entity_id)

        # Determine risk level
        if len(dependents) > 10:
            risk = "CRITICAL"
        elif len(dependents) > 5:
            risk = "HIGH"
        elif len(dependents) > 1:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        is_safe = len(dependents) == 0
        branch_count = sum(len(b) for b in control_flow.values())

        return {
            "entity_id": entity_id,
            "risk_level": risk,
            "safe_to_change": is_safe,
            "dependent_count": len(dependents),
            "dependency_count": len(dependencies),
            "branch_count": branch_count,
            "dependents": dependents,
            "dependencies": dependencies,
        }

    def get_context(self, file_path: str) -> str:
        """Get context for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Formatted context string.
        """
        entity_id = f"file:{file_path}"
        dependents = self.get_dependents(entity_id, limit=3)
        dependencies = self.get_dependencies(entity_id, limit=3)

        parts = []

        if dependents:
            parts.append(f"Depended on by: {', '.join(dependents[:3])}")

        if dependencies:
            parts.append(f"Depends on: {', '.join(dependencies[:3])}")

        return "\n".join(parts) if parts else "No analysis data"

    def _parse_entity_id(self, entity_id: str) -> dict[str, Any] | None:
        """Parse an entity ID into components.

        Args:
            entity_id: Entity ID string.

        Returns:
            Dict with type, file, name components, or None if invalid.
        """
        parts = entity_id.split(":", 2)
        if len(parts) < 2:
            return None

        return {
            "type": parts[0],
            "file": parts[1] if len(parts) > 1 else "",
            "name": parts[2] if len(parts) > 2 else "",
        }


def create_ast_backend(root_paths: list[str] | None = None) -> ASTCodeBackend:
    """Factory function to create AST Code Backend.

    Args:
        root_paths: List of root directories to analyze.

    Returns:
        Configured ASTCodeBackend instance.
    """
    return ASTCodeBackend(root_paths=root_paths)


__all__ = [
    "ASTCodeBackend",
    "create_ast_backend",
    "BACKEND_AST_CODE",
    "SOURCE_RELIABILITY_AST",
]
