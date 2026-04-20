"""QMD Wiki Backend - searches Obsidian vault via QMD CLI."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ...config import config
from .base_local_backend import BaseLocalBackend

from ...models import SearchResult

logger = logging.getLogger(__name__)

MAX_FILE_READ = 1024 * 1024  # 1MB
VAULT_MTIME_CACHE_TTL = 5.0  # seconds
REBUILD_FAILURE_LIMIT = 3
REBUILD_COOLDOWN = 60.0  # seconds
MAX_QUERY_LENGTH = 500

# QMD config path for reading actual vault locations
QMD_CONFIG_PATH = Path.home() / ".config" / "qmd" / "index.yml"


def _get_vault_from_qmd_config(scope: str) -> Path | None:
    """Read vault path for a scope from qmd's config file.

    qmd CLI uses its own config (~/.config/qmd/index.yml) rather than
    OBSIDIAN_VAULT_PATH. This ensures we track the correct vault.
    """
    import yaml

    try:
        with open(QMD_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
        collections = data.get("collections", {})
        if scope in collections:
            path = collections[scope].get("path")
            if path:
                return Path(os.path.expanduser(path))
    except Exception:
        pass
    return None


class QMDWikiBackend(BaseLocalBackend):
    BACKEND_NAME = "QMD_WIKI"
    TIMEOUT = 0.5  # seconds

    def __init__(
        self,
        vault_path: str | None = None,
        qmd_scope: str | None = None,
    ):
        # Initialize BaseLocalBackend first to ensure exclude_patterns is set
        super().__init__(root_paths=[str(vault_path)] if vault_path else None)

        self.qmd_scope = qmd_scope if qmd_scope is not None else ""

        # Resolve vault_path: prefer qmd's config, fall back to OBSIDIAN_VAULT_PATH
        if vault_path:
            raw_vault = os.path.expanduser(vault_path)
        else:
            # qmd's config IS the source of truth — the path already includes the
            # collection subdirectory (e.g. ".../personal-wiki/wiki"), so
            # qmd_scope must be "" to avoid doubling the subdirectory
            qmd_vault = _get_vault_from_qmd_config("wiki")
            raw_vault = str(qmd_vault) if qmd_vault else config.OBSIDIAN_VAULT_PATH

        self.vault_path = Path(raw_vault).resolve()
        self._index_mtime: float | None = None
        self._rebuild_lock = asyncio.Lock()
        self._rebuild_failures = 0
        self._rebuild_cooldown_until: float | None = None
        self._vault_mtime_cache: tuple[float, float] | None = None

        wiki_path = self.vault_path / self.qmd_scope
        # Constraint 3: Path traversal prevention
        if not wiki_path.resolve().is_relative_to(self.vault_path.resolve()):
            raise ValueError(f"qmd_scope '{qmd_scope}' escapes vault directory.")

        # Constraint 8: Vault existence validation
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")

    def _sanitize_query(self, query: str) -> str:
        """Constraint 4: Query sanitization - limit to MAX_QUERY_LENGTH chars, strip non-printable."""
        return "".join(c for c in query if c.isprintable() or c in " ")[:MAX_QUERY_LENGTH]

    def _get_vault_mtime_cached(self) -> float | None:
        """Constraint 11: os.scandir() for vault mtime scan with 5-second cache TTL."""
        now = time.monotonic()
        if (
            self._vault_mtime_cache is not None
            and now - self._vault_mtime_cache[1] < VAULT_MTIME_CACHE_TTL
        ):
            return self._vault_mtime_cache[0]

        wiki_path = self.vault_path / self.qmd_scope if self.qmd_scope else self.vault_path
        if not wiki_path.exists():
            return None

        max_mtime: float | None = None
        try:
            with os.scandir(wiki_path) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith(".md"):
                        try:
                            mtime = entry.stat().st_mtime
                            if max_mtime is None or mtime > max_mtime:
                                max_mtime = mtime
                        except PermissionError:
                            continue
        except PermissionError:
            return None

        if max_mtime is not None:
            self._vault_mtime_cache = (max_mtime, now)
        return max_mtime

    def _get_index_mtime(self) -> float | None:
        """Constraint 5: Index freshness tracks QMD index FILE mtime, not vault mtime."""
        index_path = self.vault_path / ".qmd" / "index"
        if not index_path.exists():
            return None
        try:
            return index_path.stat().st_mtime
        except OSError:
            return None

    def _get_vault_mtime(self) -> float | None:
        """Constraint 10: Empty vault guard in _get_vault_mtime()."""
        return self._get_vault_mtime_cached()

    async def search_batch_async(
        self, queries: list[str], limit: int = 10
    ) -> list["SearchResult"]:
        """Run multiple queries in parallel and aggregate results.

        Fails fast — any subprocess failure propagates immediately.
        Deduplicates by file_path, keeping the highest score per file.
        """
        results = await asyncio.gather(
            *[self.search_async(q, limit=limit) for q in queries],
            return_exceptions=False,
        )
        # Flatten and deduplicate by file_path (first-seen = highest score wins,
        # since search_async returns descending score order)
        seen: dict[str, SearchResult] = {}
        for result_list in results:
            for result in result_list:
                key = result.file_path or ""
                if key not in seen:
                    seen[key] = result
        return list(seen.values())

    async def search_async(self, query: str, limit: int = 10, **kwargs) -> list["SearchResult"]:
        query = self._sanitize_query(query)

        # CAUSE-001 fix: Await in-flight rebuild before searching to avoid stale index
        if self._rebuild_lock.locked():
            async with self._rebuild_lock:
                pass  # Wait for any in-progress rebuild to complete

        # Constraint 7: Circuit breaker - skip rebuild if in cooldown
        if (
            self._rebuild_cooldown_until is not None
            and time.monotonic() < self._rebuild_cooldown_until
        ):
            pass
        else:
            # CAUSE-003 fix: Use fresh vault mtime for rebuild decision, not cached
            # (cache is fine for display/logging but not for freshness-critical decisions)
            vault_mtime = self._get_vault_mtime()
            index_mtime = self._index_mtime
            # Constraint 5: Trigger rebuild if vault mtime > index mtime
            if vault_mtime and (index_mtime is None or vault_mtime > index_mtime):
                if not self._rebuild_lock.locked():
                    asyncio.create_task(self._async_rebuild_index())

        try:
            # Enforce English locale for qmd output
            env = {**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
            result = await asyncio.create_subprocess_exec(
                "qmd", "search", "--collection", self.qmd_scope.rstrip("/"), "--format", "json", query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), timeout=self.TIMEOUT
            )
            # Constraint 12: stderr logging on qmd errors
            if stderr:
                logger.debug(f"qmd stderr: {stderr.decode()}")
            # Constraint 6: _index_mtime updated after primary search completes
            self._index_mtime = self._get_index_mtime()
            self._rebuild_failures = 0
            return self._parse_qmd_json(stdout)
        except asyncio.TimeoutError:
            logger.debug("qmd search timed out")
            return []
        except FileNotFoundError:
            # Constraint 9: PermissionError handling in fallback path
            # CAUSE-002 fix: Check cooldown before expensive fallback
            if self._rebuild_cooldown_until is not None and time.monotonic() < self._rebuild_cooldown_until:
                logger.debug("qmd not found, circuit breaker active — skipping fallback")
                return []
            logger.debug("qmd not found, falling back to grep")
            return self._fallback_grep(query)
        except OSError as e:
            # CAUSE-002 fix: Check cooldown before expensive fallback
            if self._rebuild_cooldown_until is not None and time.monotonic() < self._rebuild_cooldown_until:
                logger.debug("qmd subprocess error, circuit breaker active — skipping fallback")
                return []
            logger.debug(f"qmd subprocess error: {e}")
            return self._fallback_grep(query)

    def _parse_qmd_json(self, stdout: bytes) -> list["SearchResult"]:
        import json, re
        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return []
        results = []
        items = data if isinstance(data, list) else data.get("results", [])
        diff_line_re = re.compile(r"@@ -(\d+),\d+ @@")
        for r in items:
            path = r.get("file", "")
            snippet = r.get("snippet", "")
            score = r.get("score", 0.0)
            title = r.get("title", path.split("/")[-1].rsplit(".md", 1)[0] or path)
            # Extract line number from diff notation e.g. "@@ -308,5 @@ (307 before..."
            line_number: int | None = None
            m = diff_line_re.search(snippet)
            if m:
                line_number = int(m.group(1))
            results.append(SearchResult(
                title=title, content=snippet, source=self.BACKEND_NAME,
                score=score, file_path=path, line_number=line_number,
            ))
        return results

    def _fallback_grep(self, query: str) -> list["SearchResult"]:
        """Fallback to glob+grep when qmd is unavailable.

        Captures line_number for citation granularity.
        """
        results = []
        wiki_path = self.vault_path / self.qmd_scope
        if not wiki_path.exists():
            return results

        query_lower = query.lower()
        for md_file in wiki_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue
            try:
                with open(md_file, "rb") as f:
                    content_bytes = f.read(MAX_FILE_READ)
            except PermissionError:
                continue
            except Exception:
                continue

            content = content_bytes.decode("utf-8", errors="replace")
            lines = content.split("\n")
            for line_num, line in enumerate(lines, start=1):
                if query_lower in line.lower():
                    byte_off = sum(len(l) + 1 for l in lines[:line_num - 1])
                    snippet = content[byte_off:byte_off + 200]
                    title = md_file.name.rsplit(".md", 1)[0]
                    results.append(SearchResult(
                        title=title, content=snippet,
                        source=self.BACKEND_NAME, score=0.5,
                        file_path=str(md_file), line_number=line_num,
                    ))
        return results

    async def _async_rebuild_index(self) -> None:
        """Async index rebuild - non-blocking background task."""
        async with self._rebuild_lock:
            if (
                self._rebuild_cooldown_until is not None
                and time.monotonic() < self._rebuild_cooldown_until
            ):
                return
            try:
                env = {**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
                result = await asyncio.create_subprocess_exec(
                    "qmd", "update", self.qmd_scope.rstrip("/"),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=self.TIMEOUT * 4
                )
                if stderr:
                    logger.debug(f"qmd index stderr: {stderr.decode()}")
                # Constraint 5: _index_mtime tracks QMD index FILE mtime
                self._index_mtime = self._get_index_mtime()
                self._rebuild_failures = 0
                self._rebuild_cooldown_until = None
            except asyncio.TimeoutError:
                self._rebuild_failures += 1
                self._update_cooldown()
            except Exception as e:
                logger.debug(f"qmd index rebuild failed: {e}")
                self._rebuild_failures += 1
                self._update_cooldown()

    def _update_cooldown(self) -> None:
        """Constraint 7: Circuit breaker - after 3 failures, skip rebuild for 60s."""
        if self._rebuild_failures >= REBUILD_FAILURE_LIMIT:
            self._rebuild_cooldown_until = time.monotonic() + REBUILD_COOLDOWN

    async def build_index(self) -> None:
        """Sync rebuild wrapper for external callers."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_rebuild)

    def _sync_rebuild(self) -> None:
        """Constraint 1: _sync_rebuild uses sync subprocess.run(), NOT async."""
        try:
            env = {**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
            result = subprocess.run(
                ["qmd", "update", self.qmd_scope.rstrip("/")],
                capture_output=True, timeout=self.TIMEOUT * 4,
                env=env,
            )
            if result.stderr:
                logger.debug(f"qmd index stderr: {result.stderr.decode()}")
            self._index_mtime = self._get_index_mtime()
            self._rebuild_failures = 0
            self._rebuild_cooldown_until = None
        except subprocess.TimeoutExpired:
            self._rebuild_failures += 1
            self._update_cooldown()
        except Exception as e:
            logger.debug(f"qmd index rebuild failed (sync): {e}")
            self._rebuild_failures += 1
            self._update_cooldown()