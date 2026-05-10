"""
Consolidated tree-sitter utilities for code parsing and analysis.

This module provides a unified interface for tree-sitter parsing across multiple
languages, with graceful fallback to stdlib ast when tree-sitter is unavailable.

Migrated from: P:\\\\\\__csf/src/search/backends/tree_sitter_utils.py
"""

from functools import lru_cache
from typing import Any

# Tree-sitter availability flag - set during import
TREE_SITTER_AVAILABLE = True

# Try to import tree-sitter core (required)
try:
    from tree_sitter import Language, Parser, Query
except ImportError:
    TREE_SITTER_AVAILABLE = False
    # Create dummy imports for type hints
    Language = None  # type: ignore
    Parser = None  # type: ignore
    Query = None  # type: ignore
else:
    # Import language packages (optional - make each language independently available)
    _LANGUAGE_PACKAGES = {}

    # Try to import each language package independently
    try:
        import tree_sitter_python as tsp

        _LANGUAGE_PACKAGES["python"] = tsp
    except ImportError:
        pass

    try:
        import tree_sitter_javascript as tjs

        _LANGUAGE_PACKAGES["javascript"] = tjs
    except ImportError:
        pass

    try:
        import tree_sitter_typescript as tts

        _LANGUAGE_PACKAGES["typescript"] = tts
    except ImportError:
        pass

    try:
        import tree_sitter_go as tg

        _LANGUAGE_PACKAGES["go"] = tg
    except ImportError:
        pass

    try:
        import tree_sitter_rust as tr

        _LANGUAGE_PACKAGES["rust"] = tr
    except ImportError:
        pass

    try:
        import tree_sitter_java as tj

        _LANGUAGE_PACKAGES["java"] = tj
    except ImportError:
        pass

    try:
        import tree_sitter_php as tp

        _LANGUAGE_PACKAGES["php"] = tp
    except ImportError:
        pass

    # Export for backward compatibility
    tsp = _LANGUAGE_PACKAGES.get("python")
    tjs = _LANGUAGE_PACKAGES.get("javascript")
    tts = _LANGUAGE_PACKAGES.get("typescript")
    tg = _LANGUAGE_PACKAGES.get("go")
    tr = _LANGUAGE_PACKAGES.get("rust")
    tj = _LANGUAGE_PACKAGES.get("java")
    tp = _LANGUAGE_PACKAGES.get("php")


class TreeSitterError(Exception):
    """Base exception for tree-sitter errors."""

    pass


class TreeSitterParser:
    """Unified tree-sitter parser with Python 3.14+ PyCapsule support.

    This class handles language-specific parsing with proper PyCapsule wrapping
    for Python 3.14+ compatibility.
    """

    def __init__(self, language: str):
        """Initialize parser for a specific language.

        Args:
            language: Language name (e.g., 'python', 'javascript')

        Raises:
            ValueError: If language is not supported
            TreeSitterError: If tree-sitter is not available
        """
        if not TREE_SITTER_AVAILABLE:
            raise TreeSitterError(
                "tree-sitter is not available. Install with: pip install tree-sitter"
            )

        if language not in _LANGUAGE_PACKAGES:
            raise ValueError(
                f"Unsupported language: {language}. Available: {list(_LANGUAGE_PACKAGES.keys())}"
            )

        self.language = language
        self._parser = None
        self._language_object = None

    @property
    def language_name(self) -> str:
        """Get language name (backward compatibility)."""
        return self.language

    def _get_language_object(self) -> Language:
        """Get Language object with PyCapsule wrapping (Python 3.14+ compatible).

        Returns:
            Language object for the parser

        Raises:
            TreeSitterError: If language module cannot be imported
        """
        if self._language_object is None:
            lang_module = _LANGUAGE_PACKAGES[self.language]
            try:
                lang_capsule = lang_module.language()
                self._language_object = Language(lang_capsule)
            except AttributeError as e:
                raise TreeSitterError(f"Failed to get language from module '{self.language}': {e}")

        return self._language_object

    @property
    def parser(self) -> Parser:
        """Lazy parser initialization.

        Returns:
            Configured Parser instance

        Raises:
            TreeSitterError: If parser initialization fails
        """
        if self._parser is None:
            try:
                lang_obj = self._get_language_object()
                self._parser = Parser()
                self._parser.language = lang_obj  # PyCapsule pattern
            except Exception as e:
                raise TreeSitterError(f"Failed to initialize parser: {e}")

        return self._parser

    def parse(self, source_code: str):
        """Parse source code and return root node.

        Args:
            source_code: Source code string to parse

        Returns:
            Root node of the parse tree

        Raises:
            TreeSitterError: If parsing fails
        """
        try:
            tree = self.parser.parse(source_code.encode("utf-8"))
            return tree.root_node
        except Exception as e:
            raise TreeSitterError(f"Failed to parse source code: {e}")

    def parse_bytes(self, source_bytes: bytes):
        """Parse source code bytes.

        Args:
            source_bytes: Source code as bytes

        Returns:
            Root node of the parse tree

        Raises:
            TreeSitterError: If parsing fails
        """
        try:
            return self.parser.parse(source_bytes).root_node
        except Exception as e:
            raise TreeSitterError(f"Failed to parse source bytes: {e}")

    def query(self, pattern: str, source_code: str):
        """Run a tree-sitter query on source code.

        Args:
            pattern: Query pattern (S-expression syntax)
            source_code: Source code to query

        Returns:
            Query captures (list of (capture_name, node) tuples)

        Raises:
            TreeSitterError: If query fails
        """
        try:
            query = Query(self.parser.language, pattern)
            tree = self.parser.parse(source_code.encode("utf-8"))
            return query.captures(tree.root_node)
        except Exception as e:
            raise TreeSitterError(f"Query failed: {e}")

    def extract_functions(self, source_code: str):
        """Extract all functions from source code.

        Args:
            source_code: Source code to analyze

        Returns:
            List of function metadata dictionaries with keys:
            - name: function name
            - start_line: starting line number
            - end_line: ending line number
            - body_hash: hash of function body (for duplicate detection)
            - body_length: length of function body in characters
        """
        try:
            # Query for function definitions (language-specific)
            if self.language == "python":
                pattern = "(function_definition name: (identifier) @name) @func"
            elif self.language in ["javascript", "typescript"]:
                pattern = "(function_declaration name: (identifier) @name) @func"
            elif self.language == "go":
                pattern = "(function_declaration name: (identifier) @name) @func"
            elif self.language == "rust":
                pattern = "(function_item name: (identifier) @name) @func"
            elif self.language == "java":
                pattern = "(method_declaration name: (identifier) @name) @func"
            else:
                pattern = "(function_definition) @func"

            captures = self.query(pattern, source_code)
            functions = []

            for capture_name, node in captures:
                func_info = {
                    "name": capture_name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                }

                # Extract body hash if possible
                try:
                    if node.child_count > 0:
                        # Get function body (last child is usually body)
                        body_node = node.children[-1]
                        body_text = str(body_node)
                        func_info["body_hash"] = hash(body_text)
                        func_info["body_length"] = len(body_text)
                except Exception:
                    func_info["body_hash"] = None
                    func_info["body_length"] = 0

                functions.append(func_info)

            return functions

        except Exception as e:
            raise TreeSitterError(f"Failed to extract functions: {e}")


@lru_cache(maxsize=128)
def get_parser(language: str) -> TreeSitterParser:
    """Get cached parser instance.

    Args:
        language: Language name (e.g., 'python', 'javascript')

    Returns:
        Cached TreeSitterParser instance

    Raises:
        ValueError: If language is not supported
        TreeSitterError: If tree-sitter is not available
    """
    return TreeSitterParser(language)


class LanguageRegistry:
    """Maps file extensions to tree-sitter languages.

    This class provides utilities for determining the appropriate language
    parser based on file extensions.
    """

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".php": "php",
    }

    @classmethod
    def get_language_from_path(cls, file_path: str) -> str | None:
        """Extract language from file extension.

        Args:
            file_path: Path to the source file

        Returns:
            Language name or None if extension not supported
        """
        import os

        _, ext = os.path.splitext(file_path)
        return cls.LANGUAGE_EXTENSIONS.get(ext.lower())

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if file extension is supported.

        Args:
            file_path: Path to the source file

        Returns:
            True if file extension is supported, False otherwise
        """
        return cls.get_language_from_path(file_path) is not None


class QueryEngine:
    """Pre-built queries for common code patterns.

    This class provides a collection of reusable tree-sitter queries for
    common code analysis tasks.
    """

    QUERIES = {
        "all_functions": "(function_definition) @func",
        "all_classes": "(class_definition) @class",
        "methods_with_db_param": "(function_definition parameters: (parameter (identifier) @param)) @func",
        "test_functions": "(function_definition name: (identifier) @name) @func",
        "async_functions": "(function_definition async: (async) @async) @func",
        "decorators": "(decorator) @decorator",
    }

    def __init__(self, language: str | TreeSitterParser):
        """Initialize query engine with a language or parser.

        Args:
            language: Language name (e.g., 'python', 'javascript') OR TreeSitterParser instance

        Raises:
            TreeSitterError: If tree-sitter is not available
            ValueError: If language is not supported
        """
        if not TREE_SITTER_AVAILABLE:
            raise TreeSitterError(
                "tree-sitter is not available. Install with: pip install tree-sitter"
            )

        # Support both language string and parser object
        if isinstance(language, str):
            self.parser = TreeSitterParser(language)
        elif isinstance(language, TreeSitterParser):
            self.parser = language
        else:
            raise ValueError(f"Expected language string or TreeSitterParser, got {type(language)}")

        self._compiled_queries = {}

    def query(self, pattern: str, source_code: str):
        """Run custom query pattern on source code.

        Args:
            pattern: Tree-sitter query pattern (S-expression syntax)
            source_code: Source code to query

        Returns:
            Query captures (matches found by the query)

        Raises:
            TreeSitterError: If query execution fails
        """
        if not TREE_SITTER_AVAILABLE:
            raise TreeSitterError("tree-sitter is not available")

        try:
            query = Query(self.parser.parser.language, pattern)
            tree = self.parser.parser.parse(source_code.encode("utf-8"))
            return query.captures(tree.root_node)
        except Exception as e:
            raise TreeSitterError(f"Query execution failed: {e}")

    def get_prebuilt_query(self, name: str) -> str:
        """Get pre-built query by name.

        Args:
            name: Name of the pre-built query

        Returns:
            Query pattern string

        Raises:
            ValueError: If query name is not found
        """
        if name not in self.QUERIES:
            raise ValueError(f"Unknown query: {name}. Available: {list(self.QUERIES.keys())}")
        return self.QUERIES[name]

    def run_prebuilt_query(self, name: str, source_code: str):
        """Run a pre-built query on source code.

        Args:
            name: Name of the pre-built query
            source_code: Source code to query

        Returns:
            Query captures

        Raises:
            ValueError: If query name is not found
            TreeSitterError: If query execution fails
        """
        pattern = self.get_prebuilt_query(name)
        return self.query(pattern, source_code)


class FallbackBackend:
    """Fallback to stdlib ast when tree-sitter unavailable.

    This class provides Python stdlib ast parsing as a fallback mechanism
    when tree-sitter is not installed or fails to initialize.
    """

    @staticmethod
    def detect_fallback_needed() -> bool:
        """Check if tree-sitter is available.

        Returns:
            True if tree-sitter is available, False if fallback needed
        """
        try:
            import tree_sitter

            return True
        except ImportError:
            return False

    @staticmethod
    def parse_with_ast(source_code: str):
        """Parse Python code using stdlib ast.

        Args:
            source_code: Python source code string

        Returns:
            AST module node

        Raises:
            SyntaxError: If source code has syntax errors
        """
        import ast

        return ast.parse(source_code)

    @staticmethod
    def is_available() -> bool:
        """Check if fallback backend is available.

        Returns:
            True (stdlib ast is always available for Python code)
        """
        return True


# Convenience functions for common operations


def parse_code(source_code: str, language: str):
    """Parse source code with auto-detected or specified language.

    Args:
        source_code: Source code to parse
        language: Language name (e.g., 'python', 'javascript')

    Returns:
        Root node of the parse tree

    Raises:
        TreeSitterError: If tree-sitter unavailable or parsing fails
        ValueError: If language is not supported
    """
    parser = get_parser(language)
    return parser.parse(source_code)


def parse_file(file_path: str) -> Any:
    """Parse a file and return the root node.

    Args:
        file_path: Path to the source file

    Returns:
        Root node of the parse tree, or AST node if using fallback

    Raises:
        TreeSitterError: If parsing fails
        ValueError: If file extension is not supported
        FileNotFoundError: If file does not exist
    """
    import os

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    language = LanguageRegistry.get_language_from_path(file_path)
    if language is None:
        raise ValueError(f"Unsupported file type: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        source_code = f.read()

    return parse_code(source_code, language)


def create_query_engine(language: str) -> QueryEngine:
    """Create a QueryEngine for the specified language.

    Args:
        language: Language name (e.g., 'python', 'javascript')

    Returns:
        QueryEngine instance

    Raises:
        TreeSitterError: If tree-sitter unavailable
        ValueError: If language is not supported
    """
    parser = get_parser(language)
    return QueryEngine(parser)


# Module-level helper functions for backward compatibility


def is_available() -> bool:
    """Check if tree-sitter is available.

    Returns:
        True if tree-sitter can be imported, False otherwise
    """
    return TREE_SITTER_AVAILABLE


# Aliases for backward compatibility with old tests
TreeSitterQueryEngine = QueryEngine


# Benchmark utilities (for testing performance)


def benchmark_parse(file_paths: list, iterations: int = 5):
    """Benchmark parsing performance across multiple files.

    Args:
        file_paths: List of file paths to parse
        iterations: Number of times to parse each file (for averaging)

    Returns:
        Dictionary with benchmark results:
        - total_files: Number of files parsed
        - iterations: Number of iterations per file
        - total_time_ms: Total parsing time in milliseconds
        - avg_time_per_file_ms: Average time per file per iteration
        - files_per_second: Parsing throughput (files/second)
    """
    import time

    if not TREE_SITTER_AVAILABLE:
        return {
            "total_files": 0,
            "iterations": iterations,
            "total_time_ms": 0,
            "avg_time_per_file_ms": 0,
            "files_per_second": 0,
            "error": "tree-sitter not available",
        }

    total_time = 0
    successful_parses = 0

    for file_path in file_paths:
        try:
            language = LanguageRegistry.get_language_from_path(file_path)
            if language is None:
                continue

            for _ in range(iterations):
                start = time.perf_counter()
                tree = parse_file(file_path)
                end = time.perf_counter()
                total_time += end - start
                successful_parses += 1

        except Exception:
            continue

    if successful_parses == 0:
        return {
            "total_files": 0,
            "iterations": iterations,
            "total_time_ms": 0,
            "avg_time_per_file_ms": 0,
            "files_per_second": 0,
            "error": "no files parsed successfully",
        }

    total_time_ms = total_time * 1000
    avg_time_per_file_ms = total_time_ms / successful_parses

    return {
        "total_files": len(file_paths),
        "iterations": iterations,
        "total_time_ms": total_time_ms,
        "avg_time_per_file_ms": avg_time_per_file_ms,
        "files_per_second": 1000 / avg_time_per_file_ms if avg_time_per_file_ms > 0 else 0,
    }
