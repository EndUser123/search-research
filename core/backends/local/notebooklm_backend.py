"""NotebookLM Search Backend - CLI-based long-form research synthesis.

This backend provides semantic search over NotebookLM notebooks using
the nlm CLI (not MCP) for authenticated queries.

CLI approach is preferred over MCP because:
- No server process needed
- Full feature parity
- Better error messages
- No module import failures
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import warnings
from typing import Any

warnings.filterwarnings("ignore", category=ResourceWarning)

from ..query_intent import QueryIntent  # noqa: E402
from .base_local_backend import BaseLocalBackend  # noqa: E402

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

BACKEND_NOTEBOOKLM = "notebooklm"

NLM_LIST_TIMEOUT = 10
NLM_QUERY_TIMEOUT = 60


class NotebookLMBackend(BaseLocalBackend):
    """Search backend for NotebookLM notebooks.

    Uses the nlm CLI for long-form research synthesis
    with citation-backed answers from curated notebooks.
    """

    name = BACKEND_NOTEBOOKLM
    description = "Long-form research synthesis from NotebookLM notebooks"
    source_types = ["notebook", "research"]
    # Router uses this for per-backend timeout override (NLM_QUERY_TIMEOUT=60)
    TIMEOUT = 60

    def __init__(
        self,
        root_paths: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
        notebook_id: str | None = None,
    ):
        """Initialize the NotebookLM backend.

        Args:
            root_paths: Not used (kept for BaseLocalBackend compatibility)
            exclude_patterns: Not used (kept for BaseLocalBackend compatibility)
            notebook_id: Optional specific notebook ID to query
        """
        super().__init__(root_paths, exclude_patterns)
        self.notebook_id = notebook_id

    # Auth-error wording (lowercase — _is_auth_error lowercases the text before matching).
    # Covers nlm's "Authentication expired" / "Cookies have expired" / "re-authenticate"
    # plus the common variants "unauthorized" / "session expired" / "* required".
    AUTH_ERROR_PATTERNS = (
        "authentication error",
        "authentication expired",
        "cookies have expired",
        "may have expired",
        "session expired",
        "re-authenticate",
        "unauthenticated",
        "unauthorized",
        "authentication required",
        "login required",
        "401",
    )

    def _is_auth_error(self, text: str) -> bool:
        """Check if text indicates an authentication failure (case-insensitive)."""
        lowered = (text or "").lower()
        return any(pat in lowered for pat in self.AUTH_ERROR_PATTERNS)

    def _is_auth_failure(self, stderr: str, stdout: str = "") -> bool:
        """True if auth-error wording appears in stderr OR stdout.

        nlm emits auth failures as JSON on STDOUT with empty stderr — e.g. rc=1 and
        stdout='{"status":"error","error":"Query failed: Authentication expired...
        re-authenticate..."}'. A stderr-only check misses every real auth failure,
        and a `nlm login --check` preflight is unreliable (it returns valid even when
        the query endpoint sees the creds as expired). Inspecting stdout is the only
        reliable signal, so check both streams.
        """
        return self._is_auth_error(stderr) or self._is_auth_error(stdout)

    def _run_nlm_sync(self, args: list[str], timeout: int) -> str | None:
        """Run nlm CLI synchronously. Used by sync search()."""
        try:
            result = subprocess.run(
                ["nlm"] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                stderr = result.stderr
                if self._is_auth_failure(stderr, result.stdout or ""):
                    logger.warning("NotebookLM auth failed; running `nlm login --force` + retry.")
                    login_result = subprocess.run(
                        ["nlm", "login", "--force"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if login_result.returncode == 0:
                        # Retry original command after login
                        result = subprocess.run(
                            ["nlm"] + args,
                            capture_output=True,
                            text=True,
                            timeout=timeout,
                        )
                        if result.returncode == 0:
                            return result.stdout
                    logger.warning("NotebookLM re-login/retry failed.")
                else:
                    # Auth valid (preflight ok) but query failed — transient (e.g. 60s
                    # synthesis under load). DEBUG, not WARNING, to avoid polluting every
                    # /find log with expected occasional NotebookLM query failures.
                    logger.debug(
                        "nlm command failed (transient, auth ok): rc=%d stderr=%r",
                        result.returncode, stderr,
                    )
                return None
            return result.stdout
        except FileNotFoundError:
            logger.warning("nlm CLI not found in PATH")
            return None
        except subprocess.TimeoutExpired:
            logger.warning(f"nlm command timed out after {timeout}s")
            return None
        except Exception as e:
            logger.warning(f"NotebookLM backend error: {e}")
            return None

    async def _run_nlm_async(self, args: list[str], timeout: int) -> str | None:
        """Run nlm CLI asynchronously. Used by search_async()."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nlm", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                logger.warning(f"nlm command timed out after {timeout}s")
                return None

            if proc.returncode != 0:
                stderr_str = stderr.decode() if stderr else ''
                stdout_str = stdout.decode() if stdout else ''
                if self._is_auth_failure(stderr_str, stdout_str):
                    logger.warning("NotebookLM auth failed; running async `nlm login --force` + retry.")
                    # Attempt re-login (--force clears stale/cross-account creds) and retry once
                    login_proc = await asyncio.create_subprocess_exec(
                        "nlm", "login", "--force",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    try:
                        login_stdout, login_stderr = await asyncio.wait_for(
                            login_proc.communicate(), timeout=30
                        )
                    except asyncio.TimeoutError:
                        login_proc.kill()
                        await login_proc.wait()
                        logger.warning("nlm re-login timed out")
                        return None

                    if login_proc.returncode == 0:
                        # Retry original command after auto-login
                        retry_proc = await asyncio.create_subprocess_exec(
                            "nlm", *args,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        try:
                            stdout, stderr = await asyncio.wait_for(
                                retry_proc.communicate(), timeout=timeout
                            )
                        except asyncio.TimeoutError:
                            retry_proc.kill()
                            await retry_proc.wait()
                            logger.warning(f"nlm command timed out after {timeout}s")
                            return None

                        if retry_proc.returncode == 0:
                            return stdout.decode() if stdout else ""
                    logger.warning("NotebookLM async re-login/retry failed.")
                else:
                    # Auth valid (preflight ok) but query failed — transient. DEBUG to
                    # avoid polluting every /find log with expected occasional failures.
                    logger.debug(
                        "nlm command failed (transient, auth ok): rc=%d stderr=%r",
                        proc.returncode, stderr_str,
                    )
                return None
            return stdout.decode() if stdout else ""
        except FileNotFoundError:
            logger.warning("nlm CLI not found in PATH")
            return None
        except Exception as e:
            logger.warning(f"NotebookLM backend error: {e}")
            return None

    async def search_async(self, query: str, limit: int = 5) -> list["SearchResult"]:
        """Search NotebookLM notebooks asynchronously.

        Args:
            query: Search query
            limit: Maximum number of results (default 5)

        Returns:
            List of search results with title, content, url, source
        """
        # Determine which notebook to query
        notebook_id = self.notebook_id
        if not notebook_id:
            output = await self._run_nlm_async(
                ["notebook", "list", "--json"], timeout=NLM_LIST_TIMEOUT
            )
            if not output:
                return []
            try:
                notebooks = json.loads(output)
                if not isinstance(notebooks, list) or not notebooks:
                    logger.warning("No NotebookLM notebooks found")
                    return []
                notebook_id = notebooks[0].get("id")
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.warning(f"Failed to parse notebook list: {e}")
                return []

        if not notebook_id:
            return []

        # Query the notebook
        output = await self._run_nlm_async(
            ["notebook", "query", notebook_id, query, "--json"],
            timeout=NLM_QUERY_TIMEOUT,
        )
        if not output:
            return []

        try:
            data = json.loads(output)
            # nlm can exit 0 with an error JSON; don't present it as a valid answer.
            if isinstance(data, dict) and data.get("status") == "error":
                logger.debug(f"NotebookLM error JSON on success path: {data.get('error', '')!r}")
                return []
            # nlm notebook query returns {"value": {"answer": "...", "sources": [...]}}
            if isinstance(data, dict) and "value" in data:
                data = data["value"]
            answer = data.get("answer", "") if isinstance(data, dict) else str(data)
            return [
                {
                    "title": "NotebookLM Result",
                    "content": answer,
                    "url": "",
                    "source": "notebooklm",
                }
            ]
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse notebook query response: {e}")
            return []

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Sync wrapper for backward compatibility."""
        return asyncio.get_event_loop().run_until_complete(
            self.search_async(query, limit)
        )

    def supports_intent(self, intent: QueryIntent) -> bool:
        """NotebookLM supports knowledge queries for deep research."""
        return intent == QueryIntent.KNOWLEDGE


def create_notebooklm_backend(
    notebook_id: str | None = None,
) -> NotebookLMBackend:
    """Factory function to create NotebookLM backend.

    Args:
        notebook_id: Optional specific notebook ID to query

    Returns:
        NotebookLMBackend instance
    """
    return NotebookLMBackend(notebook_id=notebook_id)
