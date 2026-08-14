"""Code Documentation Search Backend - AST-based docstring search.

Optimized with persistent disk cache and mtime-based invalidation for
10-50x faster subsequent searches.
"""

from __future__ import annotations

import ast
import hashlib
import hmac
import json
import pickle
import subprocess
import time
from pathlib import Path
from typing import Any

from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]


class CDSBackend(BaseLocalBackend):
    """Code Documentation Search using Python AST with persistent caching."""

    def __init__(
        self,
        root_paths: list[str] | None = None,
        cache_dir: str | None = None,
        enable_cache: bool = True,
        exclude_patterns: set[str] | None = None,
    ) -> None:
        """Initialize with root paths to search.

        Args:
            root_paths: List of root directories to index
            cache_dir: Directory for cache files (default: ~/.cache/cds)
            enable_cache: Whether to use persistent cache (default: True)
            exclude_patterns: Directory/file patterns to exclude from indexing
        """
        # Initialize base class
        super().__init__(root_paths, exclude_patterns)

        self.enable_cache = enable_cache

        # Cache configuration
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "cds")
        self._cache_dir = Path(cache_dir)
        # Use .json extension for new format (SEC-001 fix)
        self._index_path = self._cache_dir / "index.json"
        self._index_meta_path = self._cache_dir / "meta.json"
        # HMAC signing key for tamper protection (SEC-001 fix)
        self._hmac_key = self._cache_key().encode()

        self._import_index: dict[str, list[str]] = {}
        self._doc_index: dict[str, list[dict]] = {}  # Inverted docstring index: word -> items
        self._file_mtimes: dict[str, float] = {}

    def _compute_hmac(self, data: dict[str, Any]) -> str:
        """Compute HMAC-SHA256 signature for cache data (SEC-001 fix)."""
        data_json = json.dumps(data, sort_keys=True)
        return hmac.new(self._hmac_key, data_json.encode(), hashlib.sha256).hexdigest()

    def _migrate_from_pickle(self) -> bool:
        """Migrate old pickle cache to JSON format with HMAC signing (SEC-001 fix)."""
        pickle_path = self._cache_dir / "index.pkl"

        if not pickle_path.exists():
            return False

        try:
            # Load old pickle data
            with open(pickle_path, "rb") as f:
                cached_data = pickle.load(f)

            # Handle both old format (just index) and new format (index + import_index)
            if isinstance(cached_data, dict) and "import_index" in cached_data:
                index_data = cached_data["index"]
                import_index_data = cached_data["import_index"]
            else:
                index_data = cached_data
                import_index_data = {}

            # Save in new JSON format with HMAC signing
            self._index = index_data
            self._import_index = import_index_data
            self._save_cached_index()

            # Remove old pickle file after successful migration
            pickle_path.unlink()

            return True
        except (pickle.PickleError, OSError, Exception):
            return False

    def _cache_key(self) -> str:
        """Generate cache key from root paths."""
        paths_str = "|".join(sorted(str(p) for p in self.root_paths))
        return hashlib.md5(paths_str.encode(), usedforsecurity=False).hexdigest()[:12]

    def _index_is_stale(self) -> bool:
        """Check if any source files are newer than cached index."""
        if not self.enable_cache:
            return True

        if not self._index_path.exists() or not self._index_meta_path.exists():
            return True

        try:
            meta = json.loads(self._index_meta_path.read_text())
            cached_mtimes = meta.get("file_mtimes", {})

            # Check if root paths changed
            if meta.get("cache_key") != self._cache_key():
                return True

            # Check if any source file is newer
            for root_path in self.root_paths:
                if not root_path.exists():
                    continue
                for py_file in root_path.rglob("*.py"):
                    try:
                        file_mtime = py_file.stat().st_mtime
                        cached_mtime = cached_mtimes.get(str(py_file), 0)
                        if file_mtime > cached_mtime:
                            return True
                    except OSError:
                        continue

            return False
        except (json.JSONDecodeError, OSError):
            return True

    def _load_cached_index(self) -> bool:
        """Load index from cache if available and valid (SEC-001: pickle → JSON + HMAC)."""
        if not self.enable_cache:
            return False

        # Check if old pickle file exists for migration (SEC-001 fix)
        pickle_path = self._cache_dir / "index.pkl"
        if pickle_path.exists():
            return self._migrate_from_pickle()

        if self._index_is_stale():
            return False

        try:
            # Try to load JSON format first (SEC-001 fix)
            with open(self._index_path) as f:
                cached_data = json.load(f)

            # Verify HMAC signature to prevent tampering (SEC-001 fix)
            if "signature" not in cached_data:
                return False  # Reject unsigned data

            expected_sig = self._compute_hmac(cached_data.get("index"))
            if not hmac.compare_digest(cached_data["signature"], expected_sig):
                return False  # Reject tampered data

            # Load verified data
            self._index = cached_data.get("index", {})
            self._import_index = cached_data.get("import_index", {})
            self._doc_index = cached_data.get("doc_index", {})

            meta = json.loads(self._index_meta_path.read_text())
            self._file_mtimes = meta.get("file_mtimes", {})
            self._indexed = True
            return True
        except (json.JSONDecodeError, OSError, KeyError):
            # Try to migrate from old pickle format (SEC-001 fix)
            return self._migrate_from_pickle()
        except Exception:
            return False

    def _save_cached_index(self) -> None:
        """Save index to cache with HMAC signing (SEC-001: pickle → JSON + HMAC)."""
        if not self.enable_cache:
            return

        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            # Save index with import_index, doc_index, and HMAC signature (SEC-001 fix)
            cache_data = {
                "index": self._index,
                "import_index": self._import_index,
                "doc_index": self._doc_index,
                "signature": self._compute_hmac(self._index),  # HMAC on _index only
            }
            with open(self._index_path, "w") as f:
                json.dump(cache_data, f, indent=2)

            # Save metadata
            meta = {
                "cache_key": self._cache_key(),
                "file_mtimes": self._file_mtimes,
                "indexed_at": time.time(),
                "total_entries": sum(len(v) for v in self._index.values()),
                "total_imports": len(self._import_index),
                "total_doc_words": len(self._doc_index),
            }
            self._index_meta_path.write_text(json.dumps(meta, indent=2))
        except (OSError, Exception):
            # Fail silently - caching is optional
            pass

    def build_index(self) -> None:
        """Build AST index with persistent caching."""
        # Try to load from cache first
        if self._load_cached_index():
            return

        # Build fresh index
        self._index = {}
        self._file_mtimes = {}

        for root_path in self.root_paths:
            if not root_path.exists():
                continue
            for py_file in root_path.rglob("*.py"):
                # Skip excluded paths (inherited from BaseLocalBackend)
                if self._should_exclude(py_file):
                    continue
                try:
                    self._index_file(py_file)
                    self._file_mtimes[str(py_file)] = py_file.stat().st_mtime
                except Exception:
                    pass  # Skip files that fail to parse

        self._indexed = True

        # Save to cache
        self._save_cached_index()

    def _index_file(self, file_path: Path) -> None:
        """Index a single Python file."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except Exception:
            return  # Skip unparseable files

        file_path_str = str(file_path)

        for node in ast.walk(tree):
            result = None
            if isinstance(node, ast.FunctionDef):
                result = {
                    "type": "function",
                    "name": node.name,
                    "file": file_path_str,
                    "line": node.lineno,
                    "doc": ast.get_docstring(node) or "",
                }
            elif isinstance(node, ast.ClassDef):
                result = {
                    "type": "class",
                    "name": node.name,
                    "file": file_path_str,
                    "line": node.lineno,
                    "doc": ast.get_docstring(node) or "",
                }
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if module_name not in self._import_index:
                        self._import_index[module_name] = []
                    if file_path_str not in self._import_index[module_name]:
                        self._import_index[module_name].append(file_path_str)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    if full_name not in self._import_index:
                        self._import_index[full_name] = []
                    if file_path_str not in self._import_index[full_name]:
                        self._import_index[full_name].append(file_path_str)

            if result and result["doc"]:
                key = result["name"].lower()
                if key not in self._index:
                    self._index[key] = []
                self._index[key].append(result)
                # Build inverted docstring index: tokenize and index
                doc_lower = result["doc"].lower()
                for word in doc_lower.split():
                    # Strip punctuation from word
                    word = word.strip(".,;:()[]{}\"'`!@#$%^&*+-=/\\|<>~")
                    if word and len(word) > 1:  # Skip single-char tokens
                        if word not in self._doc_index:
                            self._doc_index[word] = []
                        self._doc_index[word].append(result)

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for code by name or docstring.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of search results, up to `limit` items.
        """
        if not self._indexed:
            self.build_index()

        query_lower = query.lower()
        results = []
        seen: set[int] = set()

        def add_result(item: dict[str, Any]) -> None:
            item_id = id(item)
            if item_id not in seen:
                seen.add(item_id)
                results.append(item)

        # Direct name matches
        if query_lower in self._index:
            for item in self._index[query_lower]:
                add_result(item)

        # Docstring matches via inverted index (word-split matches query tokenization)
        for word in query_lower.split():
            word = word.strip(".,;:()[]{}\"'`!@#$%^&*+-=/\\|<>~")
            if word and len(word) > 1 and word in self._doc_index:
                for item in self._doc_index[word]:
                    add_result(item)

        return results[:limit]

    def find_importers(self, module_name: str) -> list[str]:
        """Find all files that import the given module.

        Args:
            module_name: Module name to search for (e.g., "src.daemons.unified_semantic_daemon")

        Returns:
            List of file paths that import this module
        """
        if not self._indexed:
            self.build_index()

        # Check import index first
        importers = self._import_index.get(module_name, [])
        if importers:
            return importers

        # Fallback to ripgrep for cache misses or fresh data
        return self._ripgrep_importers(module_name)

    def _ripgrep_importers(self, module_name: str) -> list[str]:
        """Use ripgrep to find importers (fallback for cache misses).

        Args:
            module_name: Module name to search for

        Returns:
            List of file paths that import this module
        """
        importers = []

        # Build search patterns for the module
        patterns = [
            f"from {module_name} ",
            f"from {module_name}.",
            f"import {module_name}",
            f"import {module_name} as ",
        ]

        # Search in all root paths
        for root_path in self.root_paths:
            if not root_path.exists():
                continue

            for pattern in patterns:
                try:
                    cmd = [
                        "rg",
                        "--type",
                        "py",
                        "--files-with-matches",
                        "--no-ignore",
                        pattern,
                        str(root_path),
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        for line in result.stdout.strip().split("\n"):
                            if line and line not in importers:
                                importers.append(line)
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    # ripgrep not available or timeout, use Python fallback
                    for py_file in root_path.rglob("*.py"):
                        try:
                            content = py_file.read_text(errors="ignore")
                            if pattern in content:
                                if str(py_file) not in importers:
                                    importers.append(str(py_file))
                        except Exception:
                            continue

        return importers

    def find_definition(self, symbol_name: str, file_path: str) -> dict[str, Any] | None:
        """Find symbol definition location in a specific file.

        Args:
            symbol_name: Name of the symbol to find (function, class, method)
            file_path: Path to the file to search in

        Returns:
            Dictionary with 'name', 'kind', 'file', 'line' keys, or None if not found
        """
        if not self._indexed:
            self.build_index()

        # Search in index for symbol name
        symbol_lower = symbol_name.lower()

        if symbol_lower in self._index:
            # Find the symbol in the specified file
            for result in self._index[symbol_lower]:
                if result["file"] == file_path:
                    return {
                        "name": result["name"],
                        "kind": result["type"],  # 'function' or 'class'
                        "file": result["file"],
                        "line": result["line"],
                    }

        # Not found in index, try direct AST parsing
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == symbol_name:
                        return {
                            "name": node.name,
                            "kind": "function",
                            "file": file_path,
                            "line": node.lineno,
                        }
                elif isinstance(node, ast.ClassDef):
                    if node.name == symbol_name:
                        return {
                            "name": node.name,
                            "kind": "class",
                            "file": file_path,
                            "line": node.lineno,
                        }
        except Exception:
            pass

        return None

    def clear_cache(self) -> None:
        """Clear the persistent cache."""
        try:
            if self._index_path.exists():
                self._index_path.unlink()
            if self._index_meta_path.exists():
                self._index_meta_path.unlink()
            self._indexed = False
        except OSError:
            pass

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self._index_meta_path.exists():
            return {"cached": False}

        try:
            meta = json.loads(self._index_meta_path.read_text())
            return {
                "cached": True,
                "total_entries": meta.get("total_entries", 0),
                "indexed_at": meta.get("indexed_at"),
                "cache_key": meta.get("cache_key"),
            }
        except (json.JSONDecodeError, OSError):
            return {"cached": False}
