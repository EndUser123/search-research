"""Static call graph analysis using AST.

Provides CallGraph data structure and StaticCallGraphBuilder for building
call graphs from Python source code via AST analysis.

Usage:
    builder = StaticCallGraphBuilder(root_paths=["P:\\\\src"])
    builder.analyze()
    graph = builder.get_graph()
    callers = graph.get_callers("my_function")
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CallNode:
    """Represents a function/method node in the call graph."""

    name: str
    file: str
    line: int
    is_method: bool = False
    class_name: str | None = None
    is_external: bool = False

    def __hash__(self) -> int:
        return hash((self.name, self.file, self.line))


@dataclass
class CallGraph:
    """Stores the call graph with function nodes and call relationships."""

    functions: dict[str, CallNode] = field(default_factory=dict)
    _calls: dict[str, set[str]] = field(default_factory=dict)
    _called_by: dict[str, set[str]] = field(default_factory=dict)

    def add_function(self, node: CallNode) -> None:
        """Add a function node to the graph."""
        key = f"{node.file}:{node.line}:{node.name}"
        self.functions[key] = node

    def add_call(self, caller_key: str, callee_key: str) -> None:
        """Record a call relationship from caller to callee."""
        if caller_key not in self._calls:
            self._calls[caller_key] = set()
        self._calls[caller_key].add(callee_key)

        if callee_key not in self._called_by:
            self._called_by[callee_key] = set()
        self._called_by[callee_key].add(caller_key)

    def get_callers(self, func_name: str) -> list[str]:
        """Find function keys that call the given function name."""
        callers = []
        for key, node in self.functions.items():
            if node.name == func_name:
                callers.append(key)
        return callers

    def get_callees(self, func_name: str) -> list[str]:
        """Find function keys that the given function calls."""
        for key, node in self.functions.items():
            if node.name == func_name:
                if key in self._calls:
                    return list(self._calls[key])
        return []

    def get_entry_points(self) -> list[str]:
        """Find functions that are not called by any other function."""
        entry_points = []
        for key in self.functions:
            if key not in self._called_by:
                entry_points.append(key)
        return entry_points


def _analyze_file(filepath: Path, graph: CallGraph) -> set[str]:
    """Analyze a single Python file and extract function definitions and calls.

    Args:
        filepath: Path to the Python file to analyze
        graph: CallGraph to populate with functions and calls

    Returns:
        Set of function keys found in this file
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return set()

    try:
        tree = ast.parse(content, filename=str(filepath))
    except Exception:
        return set()

    file_key = str(filepath)
    functions_in_file: set[str] = set()
    current_class: str | None = None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            current_class = node.name
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _add_function(filepath, item, graph, functions_in_file, is_method=True, class_name=node.name)
            current_class = None
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _add_function(filepath, node, graph, functions_in_file, is_method=False, class_name=None)

    return functions_in_file


def _add_function(
    filepath: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    graph: CallGraph,
    functions_in_file: set[str],
    is_method: bool,
    class_name: str | None,
) -> None:
    """Add a function node to the graph."""
    key = f"{filepath}:{node.lineno}:{node.name}"
    functions_in_file.add(key)

    graph.add_function(CallNode(
        name=node.name,
        file=str(filepath),
        line=node.lineno,
        is_method=is_method,
        class_name=class_name,
        is_external=False,
    ))


class StaticCallGraphBuilder:
    """Builds a call graph by analyzing Python source files via AST."""

    def __init__(self, root_paths: list[str] | None = None):
        """Initialize builder with root paths to analyze.

        Args:
            root_paths: List of root directory paths to search for Python files.
                       Defaults to ["P:\\\\__csf/src"].
        """
        self._root_paths = root_paths or ["P:\\\\__csf/src"]
        self._graph: CallGraph = CallGraph()
        self._file_functions: dict[str, set[str]] = {}

    def analyze(self) -> None:
        """Analyze all Python files in root paths and build call graph."""
        for root_path in self._root_paths:
            root = Path(root_path)
            if not root.exists():
                continue

            for py_file in root.rglob("*.py"):
                self._file_functions[str(py_file)] = _analyze_file(py_file, self._graph)

    def get_graph(self) -> CallGraph:
        """Return the built call graph."""
        return self._graph


def get_callers(func_name: str) -> list[str]:
    """Find all functions that call the given function name."""
    builder = StaticCallGraphBuilder()
    builder.analyze()
    return builder.get_graph().get_callers(func_name)


def get_callees(func_name: str) -> list[str]:
    """Find all functions called by the given function name."""
    builder = StaticCallGraphBuilder()
    builder.analyze()
    return builder.get_graph().get_callees(func_name)


def get_entry_points() -> list[str]:
    """Find all entry point functions (not called by others)."""
    builder = StaticCallGraphBuilder()
    builder.analyze()
    return builder.get_graph().get_entry_points()