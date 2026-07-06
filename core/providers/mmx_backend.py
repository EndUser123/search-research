"""MiniMax search provider via mmx CLI.

Uses the installed mmx CLI (minimax-cli) for web search.
Requires mmx to be installed and authenticated (mmx auth login).
"""

import asyncio
import json
import logging
import os
import platform
import sys

from .base_web import BaseWebBackend

logger = logging.getLogger(__name__)


def _resolve_mmx_command() -> list[str]:
    """Resolve the mmx CLI entry point.

    On Windows, bare `mmx` resolves to a .cmd shim that CreateProcess
    cannot execute directly. Use the node script instead.
    """
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", "")
        node_script = os.path.join(appdata, "npm", "node_modules", "mmx-cli", "dist", "mmx.mjs")
        if os.path.exists(node_script):
            return ["node", node_script]
    return ["mmx"]


class MMXBackend(BaseWebBackend):
    """MiniMax search provider using the mmx CLI.

    Features:
    - Uses MiniMax's own search index
    - Returns structured JSON (title, link, snippet)
    - No additional API key needed (uses mmx auth)
    - 1-3s response time

    Usage:
        backend = MMXBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        return "minimax"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def api_key_env_var(self) -> str:
        return ""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self._available: bool | None = None
        self._cmd: list[str] | None = None

    def _get_cmd(self) -> list[str]:
        if self._cmd is None:
            self._cmd = _resolve_mmx_command()
        return self._cmd

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            cmd = self._get_cmd()
            result = subprocess.run(
                cmd + ["search", "--help"],
                capture_output=True, text=True, timeout=5,
            )
            self._available = result.returncode == 0
        except Exception:
            self._available = False
        if not self._available:
            logger.debug("mmx CLI not available or search subcommand missing")
        return self._available

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 8.0,
        **kwargs,
    ) -> list[dict]:
        if not self.is_available():
            return []

        cmd = self._get_cmd() + [
            "search", "query", query,
            "--output", "json",
            "--quiet",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )

            if proc.returncode != 0:
                logger.debug(f"mmx search failed (exit {proc.returncode}): {stderr.decode()[:200]}")
                return []

            data = json.loads(stdout.decode())
            raw_results = data.get("organic", [])

            results = []
            for item in raw_results[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "score": 0.5,
                    "metadata": {"source": self.name},
                })

            return results

        except asyncio.TimeoutError:
            logger.debug(f"mmx search timed out after {timeout}s")
            return []
        except json.JSONDecodeError as e:
            logger.debug(f"mmx search returned invalid JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"mmx search failed: {e}")
            return []

    async def close(self):
        pass


# Needed for is_available() check
import subprocess  # noqa: E402
