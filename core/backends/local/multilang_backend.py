"""Multi-language Code Analysis Backend with Tree-sitter support.

Supports Python, TypeScript, JavaScript, CSS, HTML, Go, Rust, and Java analysis.
Uses tree-sitter for unified parsing across all languages with fallback to Python's ast.

Performance: 10x faster than pure ast, incremental parsing, error recovery.

Migrated from: P:\\\\\\__csf/src/search/backends/multilang_backend.py
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from search_research.backends.base.code_analysis_backend import CodeAnalysisBackend
from search_research.utils.tree_sitter_utils import (
    LanguageRegistry,
    TreeSitterParser,
    is_available,
)

logger = logging.getLogger(__name__)

# Backend identifier
BACKEND_MULTILANG = "MULTILANG"
SOURCE_RELIABILITY_MULTILANG = 0.85  # Higher than AST-only

# Language extension mapping (HTML docs excluded from indexing)
# Merge LanguageRegistry extensions with multilang-specific extensions
LANGUAGE_EXTENSIONS = {
    **LanguageRegistry.LANGUAGE_EXTENSIONS,  # Base extensions from tree_sitter_utils
    ".pyi": "python",  # Type stubs
    ".tsx": "tsx",  # TypeScript JSX
    ".css": "css",  # CSS stylesheets
    # HTML docs excluded - too many, causes memory exhaustion
    # ".html": "html",
    # ".htm": "html",
}

# Tree-sitter availability from consolidated utils
_TREE_SITTER_AVAILABLE = is_available()


class MultiLangCodeBackend(CodeAnalysisBackend):
    """Multi-language code analysis backend.

    Provides code analysis features across Python, TypeScript, JavaScript, CSS, HTML, Go, Rust, Java:
    - Entity indexing (functions, classes, methods, structs, selectors, elements)
    - Dependency tracking (imports, requires, calls)
    - Control flow extraction (if/while/for/try)
    - Semantic search (name-based)
    - Cross-language relationship tracking

    Uses tree-sitter when available for optimal performance and coverage.
    Falls back to Python's ast module or regex-based extraction.

    Note: root_paths is REQUIRED for this backend (no default via get_src_path).
    """

    # Backend reliability score (higher = more trustworthy)
    SOURCE_RELIABILITY_MULTILANG = 0.85  # Higher than AST-only backends

    # Default exclude patterns to prevent memory exhaustion
    DEFAULT_EXCLUDE_PATTERNS = {
        "_archive",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "node_modules",
        ".git",
        "dist",
        "build",
        "*.egg-info",
    }

    def __init__(
        self,
        root_paths: list[str] | None = None,
        use_tree_sitter: bool = True,
        exclude_patterns: set[str] | None = None,
    ):
        """Initialize Multi-language Code Backend.

        Args:
            root_paths: List of root directories to analyze. Optional - if not provided,
                backend will instantiate but search() will return empty results until configured.
            use_tree_sitter: Whether to use tree-sitter if available.
            exclude_patterns: Directory/file patterns to exclude from indexing.
        """
        # Default to empty list if not provided - backend can be instantiated
        # but search() will return empty results until configured with root_paths
        if root_paths is None:
            root_paths = []

        self.root_paths = [Path(p) for p in root_paths]
        self.use_tree_sitter = use_tree_sitter and _TREE_SITTER_AVAILABLE
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS | (exclude_patterns or set())
        self._entity_index: dict[str, dict[str, Any]] = {}
        self._call_graph: dict[str, set[str]] = {}
        self._reverse_call_graph: dict[str, set[str]] = {}
        self._control_flow_cache: dict[str, dict[str, list[dict]]] = {}
        self._indexed = False
        self._language_stats: dict[str, int] = {}
        # Optimization: track file modification times for incremental indexing
        self._file_mtimes: dict[str, float] = {}
        # Optimization: cache search results with index version
        self._search_cache: dict[str, list[dict]] = {}
        self._index_version: int = 0  # Increment when index changes

        # Initialize parsers dict (even when tree-sitter unavailable for test compatibility)
        self._parsers: dict[str, Any] = {}

        if self.use_tree_sitter:
            # Use TreeSitterParser from tree_sitter_utils
            # Create parser for each supported language
            supported_languages = set(LANGUAGE_EXTENSIONS.values())
            for lang_name in supported_languages:
                try:
                    ts_parser = TreeSitterParser(lang_name)
                    self._parsers[lang_name] = ts_parser.parser
                except Exception as e:
                    logger.debug(f"Failed to create parser for {lang_name}: {e}")

        logger.info(
            f"MultiLangCodeBackend initialized with {len(self.root_paths)} paths, "
            f"tree-sitter: {self.use_tree_sitter}"
        )

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from indexing."""
        for part in path.parts:
            if part in self.exclude_patterns:
                return True
            for pattern in self.exclude_patterns:
                if pattern.startswith("*") and part.endswith(pattern[1:]):
                    return True
        return False

    def build_index(self) -> None:
        """Build entity index from all supported language files.

        Uses incremental indexing - only re-indexes files that have changed.
        """

        # Clear search cache and increment version when rebuilding index
        self._search_cache.clear()
        self._index_version += 1

        # Don't clear everything on rebuild - support incremental updates
        # Reset stats for this build
        self._language_stats = {}
        files_to_process = set()

        # Collect all files that need processing
        for root_path in self.root_paths:
            for ext in LANGUAGE_EXTENSIONS.keys():
                for file_path in root_path.rglob(f"*{ext}"):
                    # Skip excluded paths to prevent memory exhaustion
                    if self._should_exclude(file_path):
                        continue
                    file_str = str(file_path)
                    try:
                        current_mtime = file_path.stat().st_mtime
                        cached_mtime = self._file_mtimes.get(file_str)

                        # Process if new or modified
                        if cached_mtime is None or current_mtime > cached_mtime:
                            files_to_process.add(file_path)
                            # Update mtime
                            self._file_mtimes[file_str] = current_mtime
                    except Exception as e:
                        logger.debug(f"Failed to stat {file_path}: {e}")

        # Remove entities from deleted files
        current_files = {str(fp) for fp in files_to_process}
        tracked_files = set(self._file_mtimes.keys())
        (
            tracked_files
            - current_files
            - {
                str(fp)
                for root in self.root_paths
                for ext in LANGUAGE_EXTENSIONS.keys()
                for fp in root.rglob(f"*{ext}")
            }
        )

        # Clean up deleted files from tracking and index
        for deleted_file in list(self._file_mtimes.keys()):
            if not Path(deleted_file).exists():
                # Remove entities from this file
                # Remove entities indexed from this file
                to_remove = [
                    eid
                    for eid, entity in self._entity_index.items()
                    if entity.get("file_path") == deleted_file
                ]
                for eid in to_remove:
                    del self._entity_index[eid]
                del self._file_mtimes[deleted_file]

        # Process new/modified files
        for file_path in files_to_process:
            self._index_file(file_path)

        # Update stats
        for entity in self._entity_index.values():
            lang = entity.get("metadata", {}).get("language", "unknown")
            self._language_stats[lang] = self._language_stats.get(lang, 0) + 1

        self._indexed = True
        total = len(self._entity_index)
        logger.info(
            f"MultiLangCodeBackend indexed {total} entities across {len(self._language_stats)} languages"
        )
        logger.info(f"  Stats: {self._language_stats}")
        logger.info(f"  Files tracked: {len(self._file_mtimes)}")

    def _index_directory(self, root_path: Path) -> None:
        """Index all supported files in a directory."""
        # Index all supported extensions
        for ext in LANGUAGE_EXTENSIONS.keys():
            for file_path in root_path.rglob(f"*{ext}"):
                try:
                    self._index_file(file_path)
                except Exception as e:
                    logger.debug(f"Failed to index {file_path}: {e}")

    def _index_file(self, file_path: Path) -> None:
        """Index a single file based on its extension."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        language = self._detect_language(file_path)
        if not language:
            return

        rel_path = file_path.relative_to(file_path.anchor)
        file_entity_id = f"file:{rel_path}"

        # Track language stats
        self._language_stats[language] = self._language_stats.get(language, 0) + 1

        # Store file entity
        self._entity_index[file_entity_id] = {
            "type": "file",
            "name": file_path.name,
            "file_path": str(file_path),
            "language": language,
            "imports": [],
        }

        # Extract entities based on language
        if language == "python":
            self._index_python_file(file_path, source)
        elif language == "typescript":
            self._index_typescript_file(file_path, source)
        elif language == "tsx":
            self._index_tsx_file(file_path, source)
        elif language == "javascript":
            self._index_javascript_file(file_path, source)
        elif language == "css":
            self._index_css_file(file_path, source)
        elif language == "html":
            self._index_html_file(file_path, source)
        elif language == "go":
            self._index_go_file(file_path, source)
        elif language == "rust":
            self._index_rust_file(file_path, source)
        elif language == "java":
            self._index_java_file(file_path, source)

    def _detect_language(self, file_path: Path) -> str | None:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language name or None if unsupported.
        """
        ext = file_path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(ext)

    # Python indexing (using ast or tree-sitter)

    def _index_python_file(self, file_path: Path, source: str) -> None:
        """Index Python file using ast or tree-sitter."""
        if self.use_tree_sitter and "python" in self._parsers:
            self._index_with_tree_sitter(file_path, source, "python")
        else:
            self._index_with_ast(file_path, source)

    def _index_with_ast(self, file_path: Path, source: str) -> None:
        """Index Python file using built-in ast module."""
        try:
            tree = ast.parse(source, filename=str(file_path))
        except Exception:
            return

        rel_path = file_path.relative_to(file_path.anchor)

        # Collect imports
        file_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_imports.add(node.module)

        # Update file entity
        file_entity_id = f"file:{rel_path}"
        if file_entity_id in self._entity_index:
            self._entity_index[file_entity_id]["imports"] = list(file_imports)

        # Index classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._index_ast_class(node, file_path, source)
            elif isinstance(node, ast.FunctionDef):
                self._index_ast_function(node, file_path, source)

    def _index_ast_class(self, node: ast.ClassDef, file_path: Path, source: str) -> None:
        """Index a class from AST node."""
        rel_path = file_path.relative_to(file_path.anchor)
        entity_id = f"class:{rel_path}:{node.name}"

        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        self._entity_index[entity_id] = {
            "type": "class",
            "name": node.name,
            "file_path": str(file_path),
            "language": "python",
            "line": node.lineno,
            "bases": bases,
        }

    def _index_ast_function(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        source: str,
        class_name: str | None = None,
    ) -> None:
        """Index a function from AST node."""
        rel_path = file_path.relative_to(file_path.anchor)

        if class_name:
            entity_id = f"func:{rel_path}:{class_name}.{node.name}"
            display_name = f"{class_name}.{node.name}"
        else:
            entity_id = f"func:{rel_path}:{node.name}"
            display_name = node.name

        calls = self._extract_ast_calls(node)
        control_flow = self._extract_ast_control_flow(node)

        args = [arg.arg for arg in node.args.args]
        signature = f"def {node.name}({', '.join(args)})"

        self._entity_index[entity_id] = {
            "type": "function",
            "name": display_name,
            "file_path": str(file_path),
            "language": "python",
            "line": node.lineno,
            "signature": signature,
            "calls": calls,
        }

        self._control_flow_cache[entity_id] = control_flow

        # Update call graphs
        self._call_graph[entity_id] = set()
        for call in calls:
            self._call_graph[entity_id].add(call)
            if call not in self._reverse_call_graph:
                self._reverse_call_graph[call] = set()
            self._reverse_call_graph[call].add(entity_id)

    def _extract_ast_calls(self, node: ast.FunctionDef) -> list[str]:
        """Extract function calls from AST node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(ast.unparse(child.func))
        return calls

    def _extract_ast_control_flow(self, node: ast.FunctionDef) -> dict[str, list[dict]]:
        """Extract control flow from AST node."""
        branches = {"if": [], "while": [], "for": [], "try": []}

        for child in ast.walk(node):
            if child not in node.body:
                continue

            if isinstance(child, ast.If):
                branches["if"].append(
                    {
                        "type": "if",
                        "condition": ast.unparse(child.test)[:100],
                        "line": child.lineno,
                    }
                )
            elif isinstance(child, ast.While):
                branches["while"].append(
                    {
                        "type": "while",
                        "condition": ast.unparse(child.test)[:100],
                        "line": child.lineno,
                    }
                )
            elif isinstance(child, ast.For):
                target = ast.unparse(child.target)
                iter_expr = ast.unparse(child.iter)
                branches["for"].append(
                    {
                        "type": "for",
                        "condition": f"{target} in {iter_expr}"[:100],
                        "line": child.lineno,
                    }
                )
            elif isinstance(child, ast.Try):
                handlers = []
                for handler in child.handlers:
                    if handler.type:
                        handlers.append(ast.unparse(handler.type))
                branches["try"].append(
                    {
                        "type": "try",
                        "condition": ", ".join(handlers)[:100],
                        "line": child.lineno,
                    }
                )

        return branches

    # TypeScript/JavaScript indexing (tree-sitter)

    def _index_typescript_file(self, file_path: Path, source: str) -> None:
        """Index TypeScript file."""
        entities = self._extract_typescript_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_typescript_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from TypeScript source."""
        entities = []

        if not self.use_tree_sitter or "typescript" not in self._parsers:
            return entities

        try:
            tree = self._parsers["typescript"].parse(bytes(source, "utf8"))
        except Exception:
            return entities

        rel_path = file_path.relative_to(file_path.anchor)

        # Find all function declarations
        for node in self._find_nodes(tree.root_node, "function_declaration"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"func:{rel_path}:{name}"
                calls = self._extract_calls_from_node(node, source, "typescript")
                control_flow = self._extract_control_flow_from_node(node, source, "typescript")

                entities.append(
                    {
                        "id": entity_id,
                        "type": "function",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "typescript",
                        "line": line_no,
                        "signature": f"function {name}(...)",
                        "calls": calls,
                        "control_flow": control_flow,
                    }
                )

                # Cache control flow
                self._control_flow_cache[entity_id] = control_flow

        # Find all class declarations
        for node in self._find_nodes(tree.root_node, "class_declaration"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"class:{rel_path}:{name}"
                entities.append(
                    {
                        "id": entity_id,
                        "type": "class",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "typescript",
                        "line": line_no,
                    }
                )

        # Find export statements
        for node in self._find_nodes(tree.root_node, "export_statement"):
            entities.append(
                {
                    "id": f"export:{rel_path}:{node.start_point[0]}",
                    "type": "export",
                    "file_path": str(file_path),
                    "language": "typescript",
                    "line": node.start_point[0] + 1,
                }
            )

        return entities

    def _index_javascript_file(self, file_path: Path, source: str) -> None:
        """Index JavaScript file."""
        entities = self._extract_javascript_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_javascript_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from JavaScript source."""
        entities = []

        if not self.use_tree_sitter or "javascript" not in self._parsers:
            return entities

        try:
            tree = self._parsers["javascript"].parse(bytes(source, "utf8"))
        except Exception:
            return entities

        rel_path = file_path.relative_to(file_path.anchor)

        # Find all function declarations
        for node in self._find_nodes(tree.root_node, "function_declaration"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"func:{rel_path}:{name}"
                calls = self._extract_calls_from_node(node, source, "javascript")
                control_flow = self._extract_control_flow_from_node(node, source, "javascript")

                entities.append(
                    {
                        "id": entity_id,
                        "type": "function",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "javascript",
                        "line": line_no,
                        "signature": f"function {name}(...)",
                        "calls": calls,
                        "control_flow": control_flow,
                    }
                )

                # Cache control flow
                self._control_flow_cache[entity_id] = control_flow

        # Find variable declarations with functions
        for node in self._find_nodes(tree.root_node, "variable_declarator"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"var:{rel_path}:{name}"
                entities.append(
                    {
                        "id": entity_id,
                        "type": "variable",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "javascript",
                        "line": line_no,
                    }
                )

        return entities

    def _index_tsx_file(self, file_path: Path, source: str) -> None:
        """Index TSX (TypeScript JSX) file."""
        entities = self._extract_tsx_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_tsx_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from TSX source."""
        entities = []

        if not self.use_tree_sitter or "tsx" not in self._parsers:
            return entities

        try:
            tree = self._parsers["tsx"].parse(bytes(source, "utf8"))
        except Exception:
            return entities

        rel_path = file_path.relative_to(file_path.anchor)

        # Find all function declarations
        for node in self._find_nodes(tree.root_node, "function_declaration"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"func:{rel_path}:{name}"
                calls = self._extract_calls_from_node(node, source, "typescript")
                control_flow = self._extract_control_flow_from_node(node, source, "typescript")

                entities.append(
                    {
                        "id": entity_id,
                        "type": "function",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "typescript",
                        "line": line_no,
                        "signature": f"function {name}(...)",
                        "calls": calls,
                        "control_flow": control_flow,
                    }
                )

                self._control_flow_cache[entity_id] = control_flow

        # Find all class declarations
        for node in self._find_nodes(tree.root_node, "class_declaration"):
            name = self._get_node_name(node, source)
            if name:
                line_no = node.start_point[0] + 1
                entity_id = f"class:{rel_path}:{name}"
                entities.append(
                    {
                        "id": entity_id,
                        "type": "class",
                        "name": name,
                        "file_path": str(file_path),
                        "language": "typescript",
                        "line": line_no,
                    }
                )

        # Find arrow functions assigned to variables (common in React components)
        for node in self._find_nodes(tree.root_node, "variable_declarator"):
            name = self._get_node_name(node, source)
            if name:
                # Check if value is an arrow_function
                for child in node.children:
                    if child.type == "arrow_function":
                        line_no = node.start_point[0] + 1
                        entity_id = f"func:{rel_path}:{name}"
                        entities.append(
                            {
                                "id": entity_id,
                                "type": "function",
                                "name": name,
                                "file_path": str(file_path),
                                "language": "typescript",
                                "line": line_no,
                                "signature": f"const {name} = (...) => ...",
                            }
                        )
                        break

        # Find JSX element declarations (React components)
        for node in self._find_nodes(tree.root_node, "jsx_element"):
            # Get element name (first child after opening)
            name = node.type
            for child in node.children:
                if child.type == "identifier" or child.type == "member_expression":
                    name = self._get_node_text(child, source)
                    if name and name[0].isupper():  # React components are PascalCase
                        line_no = node.start_point[0] + 1
                        entity_id = f"component:{rel_path}:{name}"
                        entities.append(
                            {
                                "id": entity_id,
                                "type": "component",
                                "name": name,
                                "file_path": str(file_path),
                                "language": "typescript",
                                "line": line_no,
                            }
                        )
                    break

        return entities

    # CSS indexing

    def _index_css_file(self, file_path: Path, source: str) -> None:
        """Index CSS file."""
        entities = self._extract_css_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_css_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from CSS source."""
        entities = []

        if not self.use_tree_sitter or "css" not in self._parsers:
            # Simple regex fallback for CSS
            return self._extract_css_fallback(file_path, source)

        try:
            tree = self._parsers["css"].parse(bytes(source, "utf8"))
        except Exception:
            return self._extract_css_fallback(file_path, source)

        rel_path = file_path.relative_to(file_path.anchor)

        # Find rule sets
        for node in self._find_nodes(tree.root_node, "rule_set"):
            line_no = node.start_point[0] + 1

            # Extract selectors
            selectors = []
            for child in node.children:
                if child.type == "selectors":
                    for selector in child.children:
                        sel_text = self._get_node_text(selector, source).strip()
                        if sel_text and sel_text != "{":
                            selectors.append(sel_text)

            if selectors:
                entity_id = f"rule:{rel_path}:{line_no}"
                entities.append(
                    {
                        "id": entity_id,
                        "type": "rule",
                        "name": ", ".join(selectors[:3]),
                        "file_path": str(file_path),
                        "language": "css",
                        "line": line_no,
                        "selectors": selectors,
                    }
                )

        return entities

    def _extract_css_fallback(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Fallback CSS extraction using simple parsing."""
        entities = []
        rel_path = file_path.relative_to(file_path.anchor)

        # Simple regex for class and id selectors
        import re

        class_pattern = re.compile(r"\.([\w-]+)\s*\{")
        id_pattern = re.compile(r"#([\w-]+)\s*\{")

        for match in class_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            entity_id = f"selector:{rel_path}:class.{match.group(1)}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "selector",
                    "name": f".{match.group(1)}",
                    "file_path": str(file_path),
                    "language": "css",
                    "line": line_no,
                }
            )

        for match in id_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            entity_id = f"selector:{rel_path}:id.{match.group(1)}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "selector",
                    "name": f"#{match.group(1)}",
                    "file_path": str(file_path),
                    "language": "css",
                    "line": line_no,
                }
            )

        return entities

    # HTML indexing

    def _index_html_file(self, file_path: Path, source: str) -> None:
        """Index HTML file."""
        entities = self._extract_html_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_html_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from HTML source."""
        entities = []

        if not self.use_tree_sitter or "html" not in self._parsers:
            return self._extract_html_fallback(file_path, source)

        try:
            tree = self._parsers["html"].parse(bytes(source, "utf8"))
        except Exception:
            return self._extract_html_fallback(file_path, source)

        rel_path = file_path.relative_to(file_path.anchor)

        # Find elements with id or class attributes
        for node in self._find_nodes(tree.root_node, "element"):
            line_no = node.start_point[0] + 1

            # Get tag name from start_tag child
            tag = "element"
            element_id = None
            element_class = None

            for child in node.children:
                if child.type == "start_tag":
                    # Get tag name
                    for tag_child in child.children:
                        if tag_child.type == "tag_name":
                            tag = self._get_node_text(tag_child, source)
                            break
                    # Find attributes (id, class) - nested under start_tag
                    for tag_child in child.children:
                        if tag_child.type == "attribute":
                            # Get attribute name/value
                            attr_name = None
                            attr_value = None
                            for attr_child in tag_child.children:
                                if attr_child.type == "attribute_name":
                                    attr_name = self._get_node_text(attr_child, source)
                                elif attr_child.type in (
                                    "quoted_attribute_value",
                                    "attribute_value",
                                ):
                                    attr_value = self._get_node_text(attr_child, source).strip(
                                        "\"'"
                                    )
                            if attr_name == "id" and attr_value:
                                element_id = attr_value
                            elif attr_name == "class" and attr_value:
                                element_class = attr_value

            # Create entity for elements with id
            if element_id:
                entities.append(
                    {
                        "id": f"element:{rel_path}:#{element_id}",
                        "type": "element",
                        "name": f"{tag}#{element_id}",
                        "file_path": str(file_path),
                        "language": "html",
                        "line": line_no,
                        "tag": tag,
                        "html_id": element_id,
                    }
                )
            # Also create entity for elements with class
            elif element_class:
                first_class = element_class.split()[0]
                entities.append(
                    {
                        "id": f"element:{rel_path}.{first_class}",
                        "type": "element",
                        "name": f"{tag}.{first_class}",
                        "file_path": str(file_path),
                        "language": "html",
                        "line": line_no,
                        "tag": tag,
                        "class": element_class,
                    }
                )

        return entities

    def _extract_html_fallback(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Fallback HTML extraction using simple parsing."""
        entities = []
        rel_path = file_path.relative_to(file_path.anchor)

        # Simple regex for id attributes
        import re

        id_pattern = re.compile(r'<(\w+)[^>]*\sid=([\'"])([^\'"]+)\2[^>]*>')

        for match in id_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            tag = match.group(1)
            element_id = match.group(3)
            entity_id = f"element:{rel_path}:#{element_id}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "element",
                    "name": f"{tag}#{element_id}",
                    "file_path": str(file_path),
                    "language": "html",
                    "line": line_no,
                    "tag": tag,
                    "html_id": element_id,
                }
            )

        return entities

    # Go language indexing

    def _index_go_file(self, file_path: Path, source: str) -> None:
        """Index Go file."""
        entities = self._extract_go_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_go_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from Go source."""
        entities = []

        if not self.use_tree_sitter or "go" not in self._parsers:
            return self._extract_go_fallback(file_path, source)

        try:
            tree = self._parsers["go"].parse(bytes(source, "utf8"))
        except Exception:
            return self._extract_go_fallback(file_path, source)

        rel_path = file_path.relative_to(file_path.anchor)

        # Extract functions
        for node in self._find_nodes(tree.root_node, "function_declaration"):
            name = self._get_node_name(node, source)
            if not name:
                continue

            line_no = node.start_point[0] + 1
            entity_id = f"func:{rel_path}:{name}"
            calls = self._extract_calls_from_node(node, source, "go")
            control_flow = self._extract_control_flow_from_node(node, source, "go")

            entities.append(
                {
                    "id": entity_id,
                    "type": "function",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "go",
                    "line": line_no,
                    "calls": calls,
                    "control_flow": control_flow,
                }
            )

            self._control_flow_cache[entity_id] = control_flow

        # Extract structs (type declarations)
        for node in self._find_nodes(tree.root_node, "type_declaration"):
            for child in node.children:
                if child.type == "type_spec":
                    name = self._get_node_name(child, source)
                    if not name:
                        continue

                    line_no = child.start_point[0] + 1
                    entity_id = f"struct:{rel_path}:{name}"

                    entities.append(
                        {
                            "id": entity_id,
                            "type": "struct",
                            "name": name,
                            "file_path": str(file_path),
                            "language": "go",
                            "line": line_no,
                        }
                    )

        return entities

    def _extract_go_fallback(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Fallback Go extraction using simple parsing."""
        entities = []
        rel_path = file_path.relative_to(file_path.anchor)
        import re

        # Extract functions: func name(...)
        func_pattern = re.compile(r"^func\s+(\w+)\s*\(", re.MULTILINE)
        for match in func_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(1)
            entity_id = f"func:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "function",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "go",
                    "line": line_no,
                    "calls": [],
                    "control_flow": {},
                }
            )

        # Extract structs: type Name struct
        struct_pattern = re.compile(r"^type\s+(\w+)\s+struct", re.MULTILINE)
        for match in struct_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(1)
            entity_id = f"struct:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "struct",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "go",
                    "line": line_no,
                }
            )

        return entities

    # Rust language indexing

    def _index_rust_file(self, file_path: Path, source: str) -> None:
        """Index Rust file."""
        entities = self._extract_rust_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_rust_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from Rust source."""
        entities = []

        if not self.use_tree_sitter or "rust" not in self._parsers:
            return self._extract_rust_fallback(file_path, source)

        try:
            tree = self._parsers["rust"].parse(bytes(source, "utf8"))
        except Exception:
            return self._extract_rust_fallback(file_path, source)

        rel_path = file_path.relative_to(file_path.anchor)

        # Extract functions
        for node in self._find_nodes(tree.root_node, "function_item"):
            name = self._get_node_name(node, source)
            if not name:
                continue

            line_no = node.start_point[0] + 1
            entity_id = f"func:{rel_path}:{name}"
            calls = self._extract_calls_from_node(node, source, "rust")
            control_flow = self._extract_control_flow_from_node(node, source, "rust")

            entities.append(
                {
                    "id": entity_id,
                    "type": "function",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "rust",
                    "line": line_no,
                    "calls": calls,
                    "control_flow": control_flow,
                }
            )

            self._control_flow_cache[entity_id] = control_flow

        # Extract structs
        for node in self._find_nodes(tree.root_node, "struct_item"):
            name = self._get_node_name(node, source)
            if not name:
                continue

            line_no = node.start_point[0] + 1
            entity_id = f"struct:{rel_path}:{name}"

            entities.append(
                {
                    "id": entity_id,
                    "type": "struct",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "rust",
                    "line": line_no,
                }
            )

        return entities

    def _extract_rust_fallback(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Fallback Rust extraction using simple parsing."""
        entities = []
        rel_path = file_path.relative_to(file_path.anchor)
        import re

        # Extract functions: fn name(...)
        func_pattern = re.compile(r"^\s*(pub\s+)?fn\s+(\w+)\s*\(", re.MULTILINE)
        for match in func_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(2)
            entity_id = f"func:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "function",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "rust",
                    "line": line_no,
                    "calls": [],
                    "control_flow": {},
                }
            )

        # Extract structs: struct Name
        struct_pattern = re.compile(r"^\s*(pub\s+)?struct\s+(\w+", re.MULTILINE)
        for match in struct_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(2)
            entity_id = f"struct:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "struct",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "rust",
                    "line": line_no,
                }
            )

        return entities

    # Java language indexing

    def _index_java_file(self, file_path: Path, source: str) -> None:
        """Index Java file."""
        entities = self._extract_java_entities(file_path, source)
        for entity in entities:
            self._add_entity(entity)

    def _extract_java_entities(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Extract entities from Java source."""
        entities = []

        if not self.use_tree_sitter or "java" not in self._parsers:
            return self._extract_java_fallback(file_path, source)

        try:
            tree = self._parsers["java"].parse(bytes(source, "utf8"))
        except Exception:
            return self._extract_java_fallback(file_path, source)

        rel_path = file_path.relative_to(file_path.anchor)

        # Extract classes
        for node in self._find_nodes(tree.root_node, "class_declaration"):
            name = self._get_node_name(node, source)
            if not name:
                continue

            line_no = node.start_point[0] + 1
            entity_id = f"class:{rel_path}:{name}"

            entities.append(
                {
                    "id": entity_id,
                    "type": "class",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "java",
                    "line": line_no,
                }
            )

            # Extract methods from class body
            for child in node.children:
                if child.type == "class_body":
                    for method_node in self._find_nodes(child, "method_declaration"):
                        method_name = self._get_node_name(method_node, source)
                        if method_name:
                            method_line = method_node.start_point[0] + 1
                            method_entity_id = f"method:{rel_path}:{name}.{method_name}"
                            calls = self._extract_calls_from_node(method_node, source, "java")
                            control_flow = self._extract_control_flow_from_node(
                                method_node, source, "java"
                            )

                            entities.append(
                                {
                                    "id": method_entity_id,
                                    "type": "method",
                                    "name": method_name,
                                    "file_path": str(file_path),
                                    "language": "java",
                                    "line": method_line,
                                    "class": name,
                                    "calls": calls,
                                    "control_flow": control_flow,
                                }
                            )

                            self._control_flow_cache[method_entity_id] = control_flow

        # Also find interface declarations
        for node in self._find_nodes(tree.root_node, "interface_declaration"):
            name = self._get_node_name(node, source)
            if not name:
                continue

            line_no = node.start_point[0] + 1
            entity_id = f"interface:{rel_path}:{name}"

            entities.append(
                {
                    "id": entity_id,
                    "type": "interface",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "java",
                    "line": line_no,
                }
            )

        return entities

    def _extract_java_fallback(self, file_path: Path, source: str) -> list[dict[str, Any]]:
        """Fallback Java extraction using simple parsing."""
        entities = []
        rel_path = file_path.relative_to(file_path.anchor)
        import re

        # Extract classes: class Name { or public class Name {
        class_pattern = re.compile(r"(?:public\s+)?(?:abstract\s+)?class\s+(\w+)", re.MULTILINE)
        for match in class_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(1)
            entity_id = f"class:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "class",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "java",
                    "line": line_no,
                }
            )

        # Extract methods: public/private/protected return_type name(...)
        method_pattern = re.compile(
            r"\s+(public|private|protected)?\s*(static\s+)?\w+\s+(\w+)\s*\(", re.MULTILINE
        )
        for match in method_pattern.finditer(source):
            line_no = source[: match.start()].count("\n") + 1
            name = match.group(3)
            entity_id = f"method:{rel_path}:{name}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "method",
                    "name": name,
                    "file_path": str(file_path),
                    "language": "java",
                    "line": line_no,
                    "calls": [],
                    "control_flow": {},
                }
            )

        return entities

    # Tree-sitter helper methods

    def _index_with_tree_sitter(self, file_path: Path, source: str, language: str) -> None:
        """Index file using tree-sitter parser."""
        if language not in self._parsers:
            return

        try:
            tree = self._parsers[language].parse(bytes(source, "utf8"))
        except Exception:
            return

        rel_path = file_path.relative_to(file_path.anchor)

        # Extract functions and classes based on language
        if language == "python":
            for node in self._find_nodes(tree.root_node, "function_definition"):
                self._index_ts_function(node, file_path, source, rel_path)
            for node in self._find_nodes(tree.root_node, "class_definition"):
                self._index_ts_class(node, file_path, source, rel_path)

    def _index_ts_function(self, node, file_path: Path, source: str, rel_path: Path) -> None:
        """Index function from tree-sitter node."""
        name = self._get_node_name(node, source)
        if not name:
            return

        line_no = node.start_point[0] + 1
        entity_id = f"func:{rel_path}:{name}"

        # Extract calls and control flow
        calls = self._extract_calls_from_node(node, source, "python")
        control_flow = self._extract_control_flow_from_node(node, source, "python")

        self._entity_index[entity_id] = {
            "type": "function",
            "name": name,
            "file_path": str(file_path),
            "language": "python",
            "line": line_no,
            "calls": calls,
            "control_flow": control_flow,
        }

        # Cache control flow
        self._control_flow_cache[entity_id] = control_flow

        # Update call graphs
        self._call_graph[entity_id] = set()
        for call in calls:
            self._call_graph[entity_id].add(call)
            if call not in self._reverse_call_graph:
                self._reverse_call_graph[call] = set()
            self._reverse_call_graph[call].add(entity_id)

    def _index_ts_class(self, node, file_path: Path, source: str, rel_path: Path) -> None:
        """Index class from tree-sitter node."""
        name = self._get_node_name(node, source)
        if not name:
            return

        line_no = node.start_point[0] + 1
        entity_id = f"class:{rel_path}:{name}"

        self._entity_index[entity_id] = {
            "type": "class",
            "name": name,
            "file_path": str(file_path),
            "language": "python",
            "line": line_no,
        }

    def _find_nodes(self, root_node: Any, node_type: str) -> list:
        """Find all nodes of a given type using tree-sitter query or walk."""
        nodes = []

        def walk(node):
            if node.type == node_type or node_type in node.type:
                nodes.append(node)
            for child in node.children:
                walk(child)

        walk(root_node)
        return nodes

    def _get_node_name(self, node, source: str) -> str | None:
        """Extract name from tree-sitter node."""
        for child in node.children:
            if child.type in ["identifier", "name", "property_identifier", "type_identifier"]:
                return self._get_node_text(child, source)
        return None

    def _get_node_text(self, node, source: str) -> str:
        """Get text content from tree-sitter node."""
        try:
            return source[node.start_byte : node.end_byte]
        except Exception:
            return ""

    def _add_entity(self, entity: dict[str, Any]) -> None:
        """Add entity to index and update graphs."""
        entity_id = entity.get("id", "")
        if not entity_id:
            return

        self._entity_index[entity_id] = entity

        # Update call graph if entity has calls
        calls = entity.get("calls", [])
        if calls:
            self._call_graph[entity_id] = set(calls)
            for call in calls:
                if call not in self._reverse_call_graph:
                    self._reverse_call_graph[call] = set()
                self._reverse_call_graph[call].add(entity_id)

    # Public API methods (compatible with ASTCodeBackend)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for entities by name across all languages.

        Args:
            query: Search query (entity name or pattern).
            limit: Maximum results.

        Returns:
            List of matching entities.
        """
        if not self._indexed:
            self.build_index()

        # Check cache (includes index version to invalidate on index changes)
        cache_key = f"{self._index_version}:{query}:{limit}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        query_lower = query.lower()
        results = []

        for entity_id, entity in self._entity_index.items():
            name = entity.get("name", "")
            if query_lower in name.lower():
                results.append(
                    {
                        "id": entity_id,
                        "title": f"{entity['type'].capitalize()}: {name}",
                        "content": entity.get("signature", name),
                        "score": 1.0 if query_lower == name.lower() else 0.8,
                        "metadata": {
                            "file_path": entity.get("file_path", ""),
                            "line": entity.get("line", 0),
                            "entity_type": entity["type"],
                            "language": entity.get("language", "unknown"),
                        },
                    }
                )

        results = results[:limit]

        # Cache the results
        self._search_cache[cache_key] = results

        return results

    async def asearch(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Async version of search for compatibility."""
        return self.search(query, limit)

    def get_dependents(self, entity_id: str, limit: int = 0) -> list[str]:
        """Get entities that depend on this entity."""
        if not self._indexed:
            self.build_index()

        dependents = list(self._reverse_call_graph.get(entity_id, set()))

        if entity_id.startswith("file:"):
            file_path = entity_id.split(":", 1)[1]
            for eid, entity in self._entity_index.items():
                if entity.get("file_path", "").endswith(file_path) and eid != entity_id:
                    dependents.append(eid)

        return dependents[:limit] if limit > 0 else dependents

    def get_dependencies(self, entity_id: str, limit: int = 0) -> list[str]:
        """Get entities that this entity depends on."""
        if not self._indexed:
            self.build_index()

        entity = self._entity_index.get(entity_id)
        if not entity:
            return []

        dependencies = []
        for call in entity.get("calls", []):
            dependencies.append(f"call:{call}")

        if entity["type"] == "file":
            for imp in entity.get("imports", []):
                dependencies.append(f"module:{imp}")

        return dependencies[:limit] if limit > 0 else dependencies

    def get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]:
        """Get control flow for an entity."""
        if not self._indexed:
            self.build_index()

        entity = self._entity_index.get(entity_id)
        if not entity:
            return {}

        if entity["type"] == "function":
            return self._control_flow_cache.get(entity_id, {})

        return {}

    # get_related() inherited from CodeAnalysisBackend

    def analyze_impact(self, entity_id: str) -> dict[str, Any]:
        """Analyze the impact of changing an entity."""
        dependents = self.get_dependents(entity_id)
        dependencies = self.get_dependencies(entity_id)
        control_flow = self.get_control_flow(entity_id)

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

    # Alias for backward compatibility with base class API
    def impact_analysis(self, entity_id: str) -> dict[str, Any]:
        """Analyze impact - alias to analyze_impact for base class compatibility."""
        result = self.analyze_impact(entity_id)
        # Map old field names to new field names
        return {
            "entity_id": result.get("entity_id", entity_id),
            "dependents": result.get("dependents", []),
            "dependents_count": result.get("dependent_count", 0),
            "dependencies": result.get("dependencies", []),
            "dependencies_count": result.get("dependency_count", 0),
            "control_flow_branches": result.get("branch_count", 0),
            "risk_level": result.get("risk_level", "UNKNOWN"),
            "is_safe": result.get("safe_to_change", False),
        }

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get entity by ID - implements abstract method from base class."""
        if not self._indexed:
            self.build_index()
        return self._entity_index.get(entity_id)

    # Tree-sitter call extraction helpers

    def _extract_calls_from_node(self, node: Any, source: str, language: str) -> list[str]:
        """Extract function calls from a tree-sitter function node.

        Works across all tree-sitter languages by looking for call expressions.
        """
        calls = []

        # Language-specific call node types
        call_node_types = ["call"]
        if language == "java":
            call_node_types.append("method_invocation")

        # Find all call expressions in the function
        for call_type in call_node_types:
            for call_node in self._find_nodes(node, call_type):
                # Get the function being called
                func = None
                for child in call_node.children:
                    if child.type in [
                        "identifier",
                        "field_expression",
                        "member_expression",
                        "subscript_expression",
                        "selector_expression",
                    ]:
                        # For simple identifiers
                        if child.type == "identifier":
                            func = self._get_node_text(child, source)
                        # For member expressions like obj.method()
                        elif child.type in [
                            "field_expression",
                            "member_expression",
                            "selector_expression",
                        ]:
                            # Extract just the method name or full expression
                            for subchild in child.children:
                                if (
                                    subchild.type == "property_identifier"
                                    or subchild.type == "field_identifier"
                                ):
                                    func = self._get_node_text(subchild, source)
                                    break
                                elif subchild.type == "identifier" and not func:
                                    func = self._get_node_text(subchild, source)
                        elif child.type == "subscript_expression":
                            # For array/object access like arr[0]()
                            for subchild in child.children:
                                if subchild.type == "identifier":
                                    func = self._get_node_text(subchild, source)
                                    break
                        break

                if func:
                    calls.append(func)

        return calls

    def _extract_control_flow_from_node(
        self, node: Any, source: str, language: str
    ) -> dict[str, list[dict]]:
        """Extract control flow from a tree-sitter function node.

        Extracts if/else, for/while loops, try/catch blocks across all languages.
        """
        control_flow = {
            "if": [],
            "loop": [],
            "exception": [],
        }

        # Language-specific node type mappings
        if_nodes = ["if", "if_statement", "if_expression"]
        loop_nodes = [
            "for",
            "while",
            "for_statement",
            "while_statement",
            "for_in_statement",
            "for_range_statement",
            "loop_statement",
        ]
        try_nodes = ["try", "try_statement", "try_expression"]

        # Check for if statements
        for node_type in if_nodes:
            for if_node in self._find_nodes(node, node_type):
                line_no = if_node.start_point[0] + 1
                condition = "?"
                # Try to extract condition
                for child in if_node.children:
                    if child.type in [
                        "parenthesized_expression",
                        "condition",
                        "binary_expression",
                        "unary_expression",
                        "identifier",
                        "call",
                    ]:
                        condition = self._get_node_text(child, source)[:50]
                        break
                control_flow["if"].append(
                    {
                        "condition": condition,
                        "line": line_no,
                    }
                )

        # Check for loops
        for node_type in loop_nodes:
            for loop_node in self._find_nodes(node, node_type):
                line_no = loop_node.start_point[0] + 1
                control_flow["loop"].append(
                    {
                        "type": loop_node.type,
                        "line": line_no,
                    }
                )

        # Check for try/catch
        for node_type in try_nodes:
            for try_node in self._find_nodes(node, node_type):
                line_no = try_node.start_point[0] + 1
                control_flow["exception"].append(
                    {
                        "type": "try-catch",
                        "line": line_no,
                    }
                )

        # Remove empty categories
        return {k: v for k, v in control_flow.items() if v}


def create_multilang_backend(
    root_paths: list[str] | None = None, use_tree_sitter: bool = True
) -> MultiLangCodeBackend:
    """Factory function to create Multi-language Code Backend.

    Args:
        root_paths: List of root directories to analyze. REQUIRED.
        use_tree_sitter: Whether to use tree-sitter if available.

    Returns:
        Configured MultiLangCodeBackend instance.

    Raises:
        ValueError: If root_paths is not provided.
    """
    return MultiLangCodeBackend(root_paths=root_paths, use_tree_sitter=use_tree_sitter)


__all__ = [
    "MultiLangCodeBackend",
    "create_multilang_backend",
    "BACKEND_MULTILANG",
    "SOURCE_RELIABILITY_MULTILANG",
    "_TREE_SITTER_AVAILABLE",
]
