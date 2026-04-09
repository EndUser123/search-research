"""Code Search Backend - AST-based function/class name search."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)


class GrepBackend(BaseLocalBackend):
    """Code Pattern Search using Python AST."""

    def __init__(
        self, root_paths: list[str] | None = None, exclude_patterns: set[str] | None = None
    ) -> None:
        """Initialize with root paths to search.

        Args:
            root_paths: List of root directories to index
            exclude_patterns: Additional patterns to exclude
        """
        # Initialize base class
        super().__init__(root_paths, exclude_patterns)

    def build_index(self) -> None:
        """Build AST index of functions, classes, and methods."""
        self._index = {}

        for root_path in self.root_paths:
            for py_file in root_path.rglob("*.py"):
                # Skip excluded paths (inherited from BaseLocalBackend)
                if self._should_exclude(py_file):
                    continue
                try:
                    self._index_file(py_file)
                except Exception:
                    pass

        self._indexed = True

    def _index_file(self, file_path: Path) -> None:
        """Index a single Python file."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}:{e.lineno} - skipping: {e.msg}")
            return
        except Exception as e:
            logger.debug(f"Could not parse {file_path} - skipping: {e}")
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result = {
                    "source": "grep",
                    "type": "function",
                    "name": node.name,
                    "file": str(file_path),
                    "line": node.lineno,
                    "signature": self._get_signature(node),
                }
                key = node.name.lower()
                if key not in self._index:
                    self._index[key] = []
                self._index[key].append(result)

            elif isinstance(node, ast.ClassDef):
                result = {
                    "source": "grep",
                    "type": "class",
                    "name": node.name,
                    "file": str(file_path),
                    "line": node.lineno,
                    "signature": f"class {node.name}",
                }
                key = node.name.lower()
                if key not in self._index:
                    self._index[key] = []
                self._index[key].append(result)

    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature."""
        args = [arg.arg for arg in node.args.args]
        return f"def {node.name}({', '.join(args)})"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search by name matching.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns results in format expected by search routers:
        - id: Unique identifier
        - source: Backend name ("grep")
        - title: Result title
        - content: Result content (signature)
        - score: Relevance score (0.5 for all matches)
        - metadata: Additional info
        """
        if not self._indexed:
            self.build_index()

        query_lower = query.lower()
        results = []

        # Exact matches first
        if query_lower in self._index:
            for idx, item in enumerate(self._index[query_lower]):
                results.append(self._format_result(item, f"grep_{query_lower}_{idx}", 0.6))

        # Multi-word AND matching: split query into words, require all words to match
        if not results and " " in query_lower:
            words = query_lower.split()
            word_matches = {}
            for word in words:
                if word in self._index:
                    word_matches[word] = self._index[word]

            # Only return items that match ALL words
            if word_matches and len(word_matches) == len(words):
                # Build intersection by (file, line) key
                matched_items = {}
                for word, items in word_matches.items():
                    for item in items:
                        key = (item["file"], item["line"])
                        if key not in matched_items:
                            matched_items[key] = {"item": item, "match_count": 0}
                        matched_items[key]["match_count"] += 1

                # Filter to items matching all words, rank by match quality
                for key, data in matched_items.items():
                    if data["match_count"] == len(words):
                        item = data["item"]
                        score = 0.5 + (0.1 * data["match_count"])
                        results.append(
                            self._format_result(item, f"grep_multi_{key[0]}_{key[1]}", score)
                        )

        # Partial matches
        for key, items in self._index.items():
            if query_lower in key and query_lower != key:
                for idx, item in enumerate(items):
                    results.append(self._format_result(item, f"grep_{key}_{idx}", 0.4))

        return results[:limit]

    def _format_result(self, item: SearchResult, result_id: str, score: float) -> SearchResult:
        """Format a result for search routers."""
        return {
            "id": result_id,
            "source": "grep",
            "title": f"{item['type']}: {item['name']}",
            "content": item.get("signature", f"{item['type']} {item['name']}"),
            "score": score,
            "metadata": {
                "type": item["type"],
                "file_path": item["file"],
                "line": item["line"],
            },
        }
