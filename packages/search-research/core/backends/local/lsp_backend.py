"""LSP Symbol Search Backend.

Provides symbol-aware code search using existing LSP infrastructure
(code_intelligence/lsp/client.py).

Features:
- Symbol name search via LSP workspace/symbol
- Language-aware symbol detection
- Graceful degradation when LSP unavailable
- Compatible with UnifiedSearchRouter interface
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final, NotRequired, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from code_intelligence.lsp.client import LSPClientManager


# =============================================================================
# Type Definitions
# =============================================================================


class LSPSymbolMetadata(TypedDict):
    """Metadata for LSP symbol search results.

    Attributes:
        file_path: Path to the file containing the symbol
        line: Line number where symbol is defined
        symbol_name: Name of the symbol
        symbol_kind: LSP SymbolKind integer value
        symbol_kind_name: Human-readable symbol kind name
        type: Identifier for result type ("lsp_symbol")
        search_method: Method used to find the symbol
    """

    file_path: str
    line: int
    symbol_name: str
    symbol_kind: int
    symbol_kind_name: str
    type: str
    search_method: str


class LSPSearchResult(TypedDict):
    """LSP-specific search result format.

    NOTE: This is a TypedDict for LSP backend internal use.
    For canonical SearchResult, import from core.models.

    Attributes:
        id: Unique identifier for the result
        source: Backend source identifier (e.g., "LSP")
        title: Human-readable title
        content: Main content/description
        score: Relevance score (0.0 to 1.0+)
        metadata: Additional metadata about the result
    """

    id: str
    source: str
    title: str
    content: str
    score: float
    metadata: LSPSymbolMetadata


class LSPSymbolInfo(TypedDict):
    """Internal representation of a symbol from LSP or AST.

    Attributes:
        name: Symbol name
        kind: LSP SymbolKind integer value
        file: File path as string
        line: Line number (1-indexed)
        detail: Additional details (optional)
        _score: Internal relevance score (optional)
    """

    name: str
    kind: int
    file: str
    line: int
    detail: NotRequired[str]
    _score: NotRequired[float]


# LSP SymbolKind integer values (from LSP specification)
# See: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#symbolKind
class LSPSymbolKind:
    """LSP SymbolKind numeric values.

    These match the LSP specification for SymbolKind.
    """

    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


# Backend identifier
BACKEND_LSP_SYMBOL: Final[str] = "LSP"
SOURCE_RELIABILITY_LSP: Final[float] = 0.88  # Between CKS (0.95) and CHS (0.90)

# Configure logging
logger = logging.getLogger(__name__)

# LSP SymbolKind mapping to readable names
LSP_SYMBOL_KINDS: Mapping[int, str] = {
    LSPSymbolKind.FILE: "File",
    LSPSymbolKind.MODULE: "Module",
    LSPSymbolKind.NAMESPACE: "Namespace",
    LSPSymbolKind.PACKAGE: "Package",
    LSPSymbolKind.CLASS: "Class",
    LSPSymbolKind.METHOD: "Method",
    LSPSymbolKind.PROPERTY: "Property",
    LSPSymbolKind.FIELD: "Field",
    LSPSymbolKind.CONSTRUCTOR: "Constructor",
    LSPSymbolKind.ENUM: "Enum",
    LSPSymbolKind.INTERFACE: "Interface",
    LSPSymbolKind.FUNCTION: "Function",
    LSPSymbolKind.VARIABLE: "Variable",
    LSPSymbolKind.CONSTANT: "Constant",
    LSPSymbolKind.STRING: "String",
    LSPSymbolKind.NUMBER: "Number",
    LSPSymbolKind.BOOLEAN: "Boolean",
    LSPSymbolKind.ARRAY: "Array",
    LSPSymbolKind.OBJECT: "Object",
    LSPSymbolKind.KEY: "Key",
    LSPSymbolKind.NULL: "Null",
    LSPSymbolKind.ENUM_MEMBER: "EnumMember",
    LSPSymbolKind.STRUCT: "Struct",
    LSPSymbolKind.EVENT: "Event",
    LSPSymbolKind.OPERATOR: "Operator",
    LSPSymbolKind.TYPE_PARAMETER: "TypeParameter",
}


class LSPSymbolBackend:
    """Symbol-aware code search using LSP workspace/symbol.

    Uses existing LSP infrastructure from code_intelligence/lsp/client.py.

    Features:
    - Symbol name search with fuzzy matching
    - Language-aware symbol detection
    - Graceful degradation when LSP unavailable
    - Compatible with other search backends

    Attributes:
        root_paths: List of root paths to search
        _index: Internal symbol index mapping lowercase names to symbols
        _indexed: Whether the index has been built
        _lsp_available: Whether LSP client is available
    """

    def __init__(self, root_paths: list[str] | None = None) -> None:
        """Initialize LSP symbol backend.

        Args:
            root_paths: List of root paths to search. Defaults to src directory.
        """
        self.root_paths: list[Path] = [Path(p) for p in (root_paths or ["."])]
        self._index: dict[str, list[LSPSymbolInfo]] = {}
        self._indexed: bool = False
        self._lsp_available: bool = self._check_lsp_available()

        logger.info(
            f"LSPSymbolBackend initialized with {len(self.root_paths)} paths, "
            f"LSP available: {self._lsp_available}"
        )

    def _check_lsp_available(self) -> bool:
        """Check if LSP client is available.

        Returns:
            True if LSPClientManager can be imported, False otherwise.
        """
        try:
            from code_intelligence.lsp.client import LSPClientManager  # noqa: F401

            return True
        except ImportError:
            logger.info("LSP client not available, using AST fallback for symbol indexing")
            return False

    def build_index(self) -> None:
        """Build symbol index from workspace.

        This uses LSP workspace/symbol to discover all symbols
        in the codebase and caches them for faster searching.
        Falls back to AST-based indexing when LSP is unavailable.
        """
        self._index = {}
        total_symbols: int = 0

        for root_path in self.root_paths:
            try:
                if self._lsp_available:
                    # Run async LSP query
                    symbols: list[LSPSymbolInfo] = asyncio.run(
                        self._query_workspace_symbols(root_path)
                    )
                else:
                    # Use AST fallback when LSP unavailable
                    symbols = self._index_python_symbols(root_path)

                for symbol in symbols:
                    # Index by symbol name for quick lookup
                    name_lower: str = symbol["name"].lower()
                    if name_lower not in self._index:
                        self._index[name_lower] = []

                    self._index[name_lower].append(symbol)
                    total_symbols += 1

            except Exception as e:
                logger.debug(f"Failed to index {root_path}: {e}")

        self._indexed = True
        logger.info(f"LSPSymbolBackend indexed {total_symbols} symbols")

    async def _query_workspace_symbols(self, root_path: Path) -> list[LSPSymbolInfo]:
        """Query LSP for all workspace symbols.

        Uses real LSP server communication via the LSPClientManager.
        Falls back to AST indexing only when LSP is unavailable.

        Args:
            root_path: Root path to search

        Returns:
            List of symbol information dictionaries
        """
        try:
            from code_intelligence.lsp.client import Language, LSPClientManager

            manager: LSPClientManager = LSPClientManager(workspace=root_path)

            # Check if LSP is available
            if not manager.is_available():
                logger.debug("LSP server not available, using AST fallback")
                return await self._index_python_symbols(root_path)

            # Query workspace symbols using real LSP
            try:
                symbols_data = await manager.workspace_symbols("", language=Language.PYTHON)

                # Convert LSP response to LSPSymbolInfo format
                symbols: list[LSPSymbolInfo] = []
                for symbol in symbols_data:
                    symbols.append(
                        LSPSymbolInfo(
                            {
                                "name": symbol.get("name", ""),
                                "kind": symbol.get("kind", 0),
                                "file": symbol.get("file", ""),
                                "line": symbol.get("line", 0),
                                "detail": symbol.get("kind_name", ""),
                            }
                        )
                    )

                logger.info(f"LSP returned {len(symbols)} symbols for {root_path}")
                return symbols

            except Exception as e:
                logger.debug(f"LSP query failed: {e}, using AST fallback")
                return await self._index_python_symbols(root_path)

        except ImportError:
            # LSP module not available, use AST fallback
            logger.debug("LSP client module not available, using AST fallback")
            return await self._index_python_symbols(root_path)

    def _index_python_symbols(self, root_path: Path) -> list[LSPSymbolInfo]:
        """Index Python symbols using AST (fallback when LSP unavailable).

        Args:
            root_path: Root path to search

        Returns:
            List of symbol information dictionaries
        """
        import ast

        symbols: list[LSPSymbolInfo] = []

        for py_file in root_path.rglob("*.py"):
            try:
                source: str = py_file.read_text(encoding="utf-8", errors="ignore")
                tree: ast.Module = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_symbol: LSPSymbolInfo = {
                            "name": node.name,
                            "kind": LSPSymbolKind.FUNCTION,
                            "file": str(py_file),
                            "line": node.lineno or 1,
                            "detail": f"def {node.name}(...)",
                        }
                        symbols.append(func_symbol)

                    elif isinstance(node, ast.ClassDef):
                        class_symbol: LSPSymbolInfo = {
                            "name": node.name,
                            "kind": LSPSymbolKind.CLASS,
                            "file": str(py_file),
                            "line": node.lineno or 1,
                            "detail": f"class {node.name}",
                        }
                        symbols.append(class_symbol)

            except Exception:
                pass  # Skip files that can't be parsed

        return symbols

    def search(self, query: str, limit: int = 50) -> list[LSPSearchResult]:
        """Search for symbols matching the query.

        Args:
            query: Search query (symbol name or pattern)
            limit: Maximum results to return

        Returns:
            List of search results with LSPSearchResult format
        """
        if not self._indexed:
            self.build_index()

        query_lower: str = query.lower().replace("-", "_").replace(".", "_")
        results: list[LSPSearchResult] = []
        seen: set[str] = set()  # Deduplicate by file:line

        # First try exact matches
        if query_lower in self._index:
            for symbol in self._index[query_lower][:limit]:
                exact_result = self._format_result(symbol, query, 1.0)
                key: str = (
                    f"{exact_result['metadata']['file_path']}:{exact_result['metadata']['line']}"
                )
                if key not in seen:
                    results.append(exact_result)
                    seen.add(key)

        # Then partial matches
        for key, symbols in self._index.items():
            if query_lower in key and query_lower != key:
                for symbol in symbols:
                    if len(results) >= limit:
                        break
                    partial_result = self._format_result(symbol, query, 0.8)
                    result_key: str = f"{partial_result['metadata']['file_path']}:{partial_result['metadata']['line']}"
                    if result_key not in seen:
                        results.append(partial_result)
                        seen.add(result_key)

        return results[:limit]

    def workspace_symbols(self, query: str = "", limit: int = 50) -> list[dict[str, str | int]]:
        """Get workspace symbols matching query.

        Args:
            query: Query string to filter symbols (case-insensitive substring match)
            limit: Maximum number of results to return

        Returns:
            List of symbol dictionaries with 'name', 'kind', 'file', 'line' keys
        """
        if not self._indexed:
            self.build_index()

        # Get all symbols from the index
        all_symbols: list[LSPSymbolInfo] = []
        for symbols_list in self._index.values():
            all_symbols.extend(symbols_list)

        # Filter by query if provided
        if query:
            query_lower: str = query.lower()
            filtered: list[LSPSymbolInfo] = []
            for symbol in all_symbols:
                name: str = symbol.get("name", "")
                if query_lower in name.lower():
                    # Calculate relevance score
                    if name.lower() == query_lower:
                        # Exact match - highest priority
                        symbol["_score"] = 2.0
                    elif name.lower().startswith(query_lower):
                        # Starts with query - second priority
                        symbol["_score"] = 1.0
                    else:
                        # Contains query - lower priority
                        symbol["_score"] = 0.5
                    filtered.append(symbol)
            # Sort by score descending
            filtered.sort(key=lambda s: s.get("_score", 0), reverse=True)
            all_symbols = filtered

        # Format results with required keys
        results: list[dict[str, str | int]] = []
        for symbol in all_symbols[:limit]:
            results.append(
                {
                    "name": symbol["name"],
                    "kind": symbol["kind"],
                    "file": symbol["file"],
                    "line": symbol["line"],
                }
            )

        return results

    def _format_result(self, symbol: LSPSymbolInfo, query: str, score: float) -> LSPSearchResult:
        """Format a symbol as a standard LSPSearchResult.

        Args:
            symbol: Symbol information from LSP
            query: Original search query
            score: Relevance score

        Returns:
            Formatted LSPSearchResult dictionary
        """
        file_path: str = symbol.get("file", "")
        line: int = symbol.get("line", 0)
        name: str = symbol.get("name", "Unknown")
        kind: int = symbol.get("kind", 0)
        detail: str = symbol.get("detail", "")

        # Create readable title
        kind_name: str = LSP_SYMBOL_KINDS.get(kind, "Symbol")
        title: str = f"{kind_name}: {name}"

        metadata: LSPSymbolMetadata = {
            "file_path": file_path,
            "line": line,
            "symbol_name": name,
            "symbol_kind": kind,
            "symbol_kind_name": kind_name,
            "type": "lsp_symbol",
            "search_method": "workspace_symbol",
        }

        return LSPSearchResult(
            id=f"lsp:{file_path}:{line}:{name}",
            source=BACKEND_LSP_SYMBOL,
            title=title,
            content=detail or name,
            score=score,
            metadata=metadata,
        )


def create_lsp_backend(root_paths: list[str] | None = None) -> LSPSymbolBackend:
    """Factory function to create LSP symbol backend.

    Args:
        root_paths: List of root paths to search

    Returns:
        Configured LSPSymbolBackend instance
    """
    return LSPSymbolBackend(root_paths=root_paths)
