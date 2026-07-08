"""AST-based Code Analysis Backend.

Lightweight code analysis using Python's AST module.
Provides dependents, dependencies, and control flow analysis
without requiring CPG, embeddings, or vector storage.

This is a pragmatic implementation for the LSP query interface
when full CPG infrastructure is unavailable.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache schema version. Bump to invalidate all old caches (e.g. on index shape
# change, new field added, hash algorithm change).
_CACHE_VERSION = 1
_CACHE_DIR = Path(os.getenv("SEARCH_RESEARCH_CACHE_DIR", "P:/.data/cache"))
_CACHE_FILE = _CACHE_DIR / f"ast_code_index_v{_CACHE_VERSION}.json"
_CACHE_LOCK = _CACHE_FILE.with_suffix(".lock")
_CACHE_STALE_LOCK_SECS = 60  # dotlock-style: lock older than this is treated as abandoned

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
        self.root_paths = [Path(p) for p in (root_paths or ["."])]
        self._entity_index: dict[str, dict[str, Any]] = {}
        self._call_graph: dict[str, set[str]] = {}  # entity_id -> callers
        self._reverse_call_graph: dict[str, set[str]] = {}  # entity_id -> callees
        self._control_flow_cache: dict[str, dict[str, list[dict]]] = {}
        self._indexed = False

        logger.info(f"ASTCodeBackend initialized with {len(self.root_paths)} paths")

    def build_index(self) -> None:
        """Build entity index from Python files.

        Tries persistent cache first; falls back to full rebuild on miss.
        Cache file uses md5 fingerprints per .py file and an atomic temp+rename
        write so multi-terminal readers never see a torn state.
        """
        # Try cache hit (multi-terminal safe — readers don't lock)
        loaded = self._try_load_cache()
        if loaded is not None:
            self._entity_index, self._call_graph, self._reverse_call_graph, self._control_flow_cache = loaded
            self._indexed = True
            logger.info(f"ASTCodeBackend loaded {len(self._entity_index)} entities from cache")
            return

        # Cache miss / stale — full rebuild
        self._entity_index = {}
        self._call_graph = {}
        self._reverse_call_graph = {}
        self._control_flow_cache = {}

        for root_path in self.root_paths:
            self._index_directory(root_path)

        self._indexed = True
        logger.info(f"ASTCodeBackend indexed {len(self._entity_index)} entities (cache rebuilt)")

        # NOTE: persistence is intentionally NOT called here. build_index() is
        # the pure build path used by tests; persisting on every call would
        # double the I/O (full rehash for the manifest) and write an 87MB file
        # in unit tests. The production warm-up path (_do_warm_up in
        # router_async.py) calls build_index() then _persist_cache() so the
        # cache is written once per process on the router lifecycle, not per
        # build_index call.

    def _try_load_cache(self) -> tuple[dict, dict, dict, dict] | None:
        """Try to load index from disk. Returns None on miss, stale, or corrupt.

        Safety invariants:
        - Version mismatch → None (cache schema changed)
        - Per-file md5 mismatch OR mtime_ns/size mismatch → None
        - Corrupt JSON → None (logged, not raised)
        """
        if not _CACHE_FILE.exists():
            return None
        try:
            with open(_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"ASTCodeBackend cache read failed: {e}")
            return None

        if data.get("version") != _CACHE_VERSION:
            logger.debug(f"ASTCodeBackend cache version mismatch (got {data.get('version')}, want {_CACHE_VERSION})")
            return None

        manifest = data.get("files", {})
        for file_path, fingerprint in manifest.items():
            try:
                st = os.stat(file_path)
            except OSError:
                # File deleted since cache was written → cache stale
                return None
            if (
                st.st_mtime_ns != fingerprint.get("mtime_ns")
                or st.st_size != fingerprint.get("size")
            ):
                # mtime/size changed → recheck content hash (handles git
                # operations that touch files without bumping mtime cleanly)
                try:
                    with open(file_path, "rb") as f:
                        actual_md5 = hashlib.md5(f.read()).hexdigest()
                except OSError:
                    return None
                if actual_md5 != fingerprint.get("md5"):
                    return None

        # All checks passed — load the dicts
        return (
            data.get("entities", {}),
            {k: set(v) for k, v in data.get("call_graph", {}).items()},
            {k: set(v) for k, v in data.get("reverse_call_graph", {}).items()},
            data.get("control_flow_cache", {}),
        )

    def _persist_cache(self) -> None:
        """Atomically write the index to disk. Multi-terminal safe via flock.

        Invariants:
        - Acquire .lock with LOCK_EX + LOCK_NB. If held, skip persist (another
          terminal will publish). The current build is still in memory and used.
        - Detect stale lock (mtime > 60s old) → break it.
        - Write via tempfile.mkstemp + os.replace() for atomic publish.
        """
        # Build the manifest: per-file md5 + mtime_ns + size
        manifest: dict[str, dict[str, int | str]] = {}
        for root_path in self.root_paths:
            for py_file in root_path.rglob("*.py"):
                try:
                    st = py_file.stat()
                    with open(py_file, "rb") as f:
                        md5 = hashlib.md5(f.read()).hexdigest()
                    manifest[str(py_file)] = {
                        "mtime_ns": st.st_mtime_ns,
                        "size": st.st_size,
                        "md5": md5,
                    }
                except OSError:
                    continue  # file vanished mid-build; ignore

        payload = {
            "version": _CACHE_VERSION,
            "root_paths": [str(p) for p in self.root_paths],
            "files": manifest,
            "entities": self._entity_index,
            "call_graph": {k: list(v) for k, v in self._call_graph.items()},
            "reverse_call_graph": {k: list(v) for k, v in self._reverse_call_graph.items()},
            "control_flow_cache": self._control_flow_cache,
        }

        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Best-effort cross-process lock. The atomic temp+rename below already
        # protects readers from torn writes — this lock is only build
        # coordination so two terminals don't both rebuild + race to publish.
        # POSIX: fcntl.flock. Windows: msvcrt.locking (byte-range, but works on
        # a 1-byte file for cross-process mutual exclusion). If neither works
        # (e.g., exotic platform), proceed without coordination.
        lock_fd = None
        lock_acquired = False
        try:
            lock_fd = os.open(str(_CACHE_LOCK), os.O_CREAT | os.O_RDWR, 0o644)
            # Detect stale lock: if mtime > threshold, another terminal crashed
            try:
                lock_mtime = os.fstat(lock_fd).st_mtime
                import time as _time
                if _time.time() - lock_mtime > _CACHE_STALE_LOCK_SECS:
                    os.ftruncate(lock_fd, 0)
            except OSError:
                pass
            if os.name == "posix":
                try:
                    import fcntl as _fcntl
                    _fcntl.flock(lock_fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
                    lock_acquired = True
                except (BlockingIOError, OSError):
                    logger.debug("ASTCodeBackend cache lock held by another process; skipping persist")
                    return
            elif os.name == "nt":
                try:
                    import msvcrt as _msvcrt
                    _msvcrt.locking(lock_fd, _msvcrt.LK_NBLCK, 1)
                    lock_acquired = True
                except OSError:
                    logger.debug("ASTCodeBackend cache lock held by another process; skipping persist")
                    return
        except OSError:
            lock_fd = None

        try:
            # Atomic write: temp file in same dir → os.replace() (atomic on POSIX & Win)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(_CACHE_DIR), prefix=".ast_code_", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        pass
                os.replace(tmp_path, _CACHE_FILE)
                logger.debug(f"ASTCodeBackend cache persisted to {_CACHE_FILE}")
            except Exception:
                # Clean up the temp file on failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        finally:
            if lock_fd is not None and lock_acquired:
                try:
                    if os.name == "posix":
                        import fcntl as _fcntl
                        _fcntl.flock(lock_fd, _fcntl.LOCK_UN)
                    elif os.name == "nt":
                        import msvcrt as _msvcrt
                        _msvcrt.locking(lock_fd, _msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            if lock_fd is not None:
                os.close(lock_fd)

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
