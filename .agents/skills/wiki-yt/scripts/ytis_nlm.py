#!/usr/bin/env python3
"""Canonical NotebookLM bridge for the wiki-yt skill.

The YTIS package owns the account-to-storage mapping, durable non-interactive
auth repair, and the direct ``notebooklm-py`` client.  This bridge keeps
wiki-yt from maintaining a second CLI profile store.  Read-only probes remain
available for diagnostics; pipeline entry points use the explicit durable
repair helper before doing work.

The public helpers return small dictionaries matching the shapes the legacy
``nlm --json`` callers consumed.  The underlying client is opened only after
the caller requests an operation, so importing this module has no network or
auth side effects.
"""
from __future__ import annotations

import os
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

T = TypeVar("T")

YTIS_ROOT = Path(os.environ.get("YTIS_ROOT", "P:/packages/yt-is"))


def _load_nlm_module() -> Any:
    """Load the package-owned YTIS client without requiring installation."""
    root = YTIS_ROOT.resolve()
    if not (root / "csf" / "nlm_client.py").is_file():
        raise RuntimeError(f"YTIS client source not found at {root / 'csf' / 'nlm_client.py'}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from csf import nlm_client

    return nlm_client


def probe_account_session(account_profile: str, *, worker_id: str = "wiki-yt") -> Any:
    """Run YTIS's read-only canonical storage/session probe."""
    return _load_nlm_module().probe_account_session(account_profile, worker_id=worker_id)


def ensure_account_session(
    account_profile: str,
    *,
    worker_id: str = "wiki-yt",
    timeout_s: float = 180.0,
) -> Any:
    """Probe and repair one account using YTIS's non-interactive auth path."""
    return _load_nlm_module().ensure_account_session(
        account_profile,
        worker_id=worker_id,
        timeout_s=timeout_s,
    )


def open_account_client(account_profile: str, *, worker_id: str = "wiki-yt") -> Any:
    """Open one exact-account client using YTIS canonical storage."""
    return _load_nlm_module().NLMSyncClient.from_account_profile(
        account_profile,
        worker_id=worker_id,
    )


def canonical_storage_path(account_profile: str) -> Path:
    """Return the YTIS-owned storage path for an exact account identity."""
    _load_nlm_module()
    from csf.nlm_auth_check import storage_path_for_account_profile

    return Path(storage_path_for_account_profile(account_profile))


def load_canonical_cookies(account_profile: str) -> list[dict[str, Any]]:
    """Read cookies from canonical Playwright storage for yt-dlp export."""
    _load_nlm_module()
    from csf.nlm_auth_check import inspect_account_storage

    status = inspect_account_storage(account_profile)
    if not status.ok:
        raise RuntimeError(
            f"canonical storage validation failed for {account_profile!r}: {status.reason}"
        )
    path = Path(status.storage_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"canonical storage unreadable for {account_profile!r}: {exc}") from exc
    cookies = payload.get("cookies") if isinstance(payload, dict) else None
    if not isinstance(cookies, list):
        raise RuntimeError(f"canonical storage has no cookies list: {path}")
    return [cookie for cookie in cookies if isinstance(cookie, dict)]


@contextmanager
def account_client(account_profile: str, *, worker_id: str = "wiki-yt") -> Iterator[Any]:
    """Yield a canonical client and always close its event loop/session."""
    client = open_account_client(account_profile, worker_id=worker_id)
    try:
        yield client
    finally:
        client.close()


def _run_with_client(
    account_profile: str,
    worker_id: str,
    operation: Callable[[Any], T],
) -> T:
    with account_client(account_profile, worker_id=worker_id) as client:
        return operation(client)


def _enum_value(value: Any) -> Any:
    value = getattr(value, "value", value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def notebook_to_dict(notebook: Any) -> dict[str, Any]:
    """Convert a notebooklm-py Notebook to the legacy JSON shape."""
    return {
        "id": str(getattr(notebook, "id", "") or ""),
        "title": str(getattr(notebook, "title", "") or ""),
        "source_count": int(
            getattr(notebook, "sources_count", getattr(notebook, "source_count", 0)) or 0
        ),
    }


def source_to_dict(source: Any) -> dict[str, Any]:
    """Convert a notebooklm-py Source to the legacy JSON shape."""
    return {
        "id": str(getattr(source, "id", "") or ""),
        "title": str(getattr(source, "title", "") or ""),
        "url": getattr(source, "url", None),
        "type": _enum_value(getattr(source, "_type_code", None)),
        "status": _enum_value(getattr(source, "status", None)),
    }


def list_notebooks_from_client(client: Any) -> list[dict[str, Any]]:
    return [notebook_to_dict(item) for item in client.run(client.notebooks.list())]


def get_notebook_from_client(client: Any, notebook_id: str) -> dict[str, Any]:
    return notebook_to_dict(client.run(client.notebooks.get(notebook_id)))


def list_sources_from_client(client: Any, notebook_id: str) -> list[dict[str, Any]]:
    return [source_to_dict(item) for item in client.run(client.sources.list(notebook_id))]


def get_source_content_from_client(
    client: Any,
    notebook_id: str,
    source_id: str,
) -> str:
    fulltext = client.run(client.sources.get_fulltext(notebook_id, source_id, output_format="text"))
    return str(getattr(fulltext, "content", "") or "")


def rename_notebook_from_client(client: Any, notebook_id: str, title: str) -> dict[str, Any]:
    return notebook_to_dict(client.run(client.notebooks.rename(notebook_id, title)))


def list_notebooks(account_profile: str, *, worker_id: str = "wiki-yt") -> list[dict[str, Any]]:
    return _run_with_client(
        account_profile,
        worker_id,
        list_notebooks_from_client,
    )


def get_notebook(
    account_profile: str,
    notebook_id: str,
    *,
    worker_id: str = "wiki-yt",
) -> dict[str, Any]:
    return _run_with_client(
        account_profile,
        worker_id,
        lambda client: get_notebook_from_client(client, notebook_id),
    )


def list_sources(
    account_profile: str,
    notebook_id: str,
    *,
    worker_id: str = "wiki-yt",
) -> list[dict[str, Any]]:
    return _run_with_client(
        account_profile,
        worker_id,
        lambda client: list_sources_from_client(client, notebook_id),
    )


def get_source_content(
    account_profile: str,
    notebook_id: str,
    source_id: str,
    *,
    worker_id: str = "wiki-yt",
) -> str:
    return _run_with_client(
        account_profile,
        worker_id,
        lambda client: get_source_content_from_client(client, notebook_id, source_id),
    )


def rename_notebook(
    account_profile: str,
    notebook_id: str,
    title: str,
    *,
    worker_id: str = "wiki-yt",
) -> dict[str, Any]:
    return _run_with_client(
        account_profile,
        worker_id,
        lambda client: rename_notebook_from_client(client, notebook_id, title),
    )
