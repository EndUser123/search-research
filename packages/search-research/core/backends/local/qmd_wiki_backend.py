"""QMD Wiki Backend - searches Obsidian vault via QMD CLI."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path

from ...config import config
from ...models import SearchResult
from .base_local_backend import BaseLocalBackend

logger = logging.getLogger(__name__)

MAX_FILE_READ = 1024 * 1024  # 1MB
VAULT_MTIME_CACHE_TTL = 5.0  # seconds
REBUILD_FAILURE_LIMIT = 3
REBUILD_COOLDOWN = 60.0  # seconds


class QMDWikiBackend(BaseLocalBackend):
    BACKEND_NAME = "QMD_WIKI"
    TIMEOUT = 5.0  # seconds

    def __init__(
        self,
        vault_path: str | None = None,
        qmd_scope: str = "wiki/",
    ):
        super().__init__()
        raw_vault = os.path.expanduser(vault_path or config.OBSIDIAN_VAULT_PATH)
        self.vault_path = Path(raw_vault).resolve()
        self.qmd_scope = qmd_scope
        self._index_mtime: float | None = None
        self._rebuild_lock = asyncio.Lock()
        self._rebuild_failures = 0
        self._rebuild_cooldown_until: float | None = None
        self._vault_mtime_cache: tuple[float, float] | None = None

        wiki_path = self.vault_path / self.qmd_scope
        try:
            if not wiki_path.resolve().is_relative_to(self.vault_path.resolve()):
                raise ValueError(f"qmd_scope '{qmd_scope}' escapes vault directory.")
        except ValueError:
            raise

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")

    def _sanitize_query(self, query: str) -> str:
        return "".join(c for c in query if c.isprintable())[:500]

    def _get_vault_mtime_cached(self) -> float | None:
        import time
        now = time.monotonic()
        if (
            self._vault_mtime_cache is not None
            and now - self._vault_mtime_cache[1] < VAULT_MTIME_CACHE_TTL
        ):
            return self._vault_mtime_cache[0]
        wiki_path = self.vault_path / self.qmd_scope
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
        index_path = self.vault_path / ".qmd" / "index"
        if not index_path.exists():
            return None
        try:
            return index_path.stat().st_mtime
        except OSError:
            return None

    def _get_vault_mtime(self) -> float | None:
        return self._get_vault_mtime_cached()

    def _collection_name(self) -> str:
        """Return collection name from qmd_scope (strips trailing slash)."""
        return self.qmd_scope.rstrip("/")

    async def search_async(self, query: str, limit: int = 10, **kwargs) -> list[SearchResult]:
        query = self._sanitize_query(query)
        import time
        if (
            self._rebuild_cooldown_until is not None
            and time.monotonic() < self._rebuild_cooldown_until
        ):
            pass
        else:
            vault_mtime = self._get_vault_mtime_cached()
            index_mtime = self._index_mtime
            if vault_mtime and (index_mtime is None or vault_mtime > index_mtime):
                if not self._rebuild_lock.locked():
                    asyncio.create_task(self._async_rebuild_index())
        try:
            result = await asyncio.create_subprocess_exec(
                "qmd", "search", "--collection", self._collection_name(),
                "--format", "json", query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), timeout=self.TIMEOUT
            )
            if stderr:
                logger.debug(f"qmd stderr: {stderr.decode()}")
            self._index_mtime = self._get_index_mtime()
            self._rebuild_failures = 0
            return self._parse_qmd_json(stdout)
        except asyncio.TimeoutError:
            logger.debug("qmd search timed out")
            return []
        except FileNotFoundError:
            logger.debug("qmd not found, falling back to grep")
            return self._fallback_grep(query)
        except subprocess.SubprocessError as e:
            logger.debug(f"qmd subprocess error: {e}")
            return self._fallback_grep(query)

    def _parse_qmd_json(self, stdout: bytes) -> list[SearchResult]:
        import json
        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return []
        # QMD may return {"results": [...]} or a raw [...]
        items = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        results = []
        for r in items:
            path = r.get("file", r.get("path", ""))
            snippet = r.get("snippet", "")
            score = r.get("score", 0.0)
            title = r.get("title", path.split("/")[-1].rsplit(".md", 1)[0] or path)
            results.append(SearchResult(
                title=title, content=snippet, source=self.BACKEND_NAME,
                score=score, file_path=path,
            ))
        return results

    def _fallback_grep(self, query: str) -> list[SearchResult]:
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
                    content = f.read(MAX_FILE_READ).decode("utf-8", errors="replace")
                if query_lower in content.lower():
                    title = md_file.name.rsplit(".md", 1)[0]
                    results.append(SearchResult(
                        title=title, content=content[:200],
                        source=self.BACKEND_NAME, score=0.5,
                        file_path=str(md_file),
                    ))
            except PermissionError:
                continue
            except Exception:
                continue
        return results

    async def _async_rebuild_index(self) -> None:
        import time
        async with self._rebuild_lock:
            if (
                self._rebuild_cooldown_until is not None
                and time.monotonic() < self._rebuild_cooldown_until
            ):
                return
            try:
                result = await asyncio.create_subprocess_exec(
                    "qmd", "update", self._collection_name(),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=self.TIMEOUT * 4
                )
                if stderr:
                    logger.debug(f"qmd index stderr: {stderr.decode()}")
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
        import time
        if self._rebuild_failures >= REBUILD_FAILURE_LIMIT:
            self._rebuild_cooldown_until = time.monotonic() + REBUILD_COOLDOWN

    async def build_index(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_rebuild)

    def _sync_rebuild(self) -> None:
        try:
            result = subprocess.run(
                ["qmd", "update", self._collection_name()],
                capture_output=True, timeout=self.TIMEOUT * 4,
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
