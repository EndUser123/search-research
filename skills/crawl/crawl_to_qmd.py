#!/usr/bin/env python3
"""
Crawl4AI to QMD ingestion pipeline.

Crawl a website → Markdown files with frontmatter → QMD collection.

Usage: python crawl_to_qmd.py https://example.com --max-pages 10
       python crawl_to_qmd.py https://example.com --max-pages 10 --collection wiki

Fail-fast: exits with clear error if crawl4ai or qmd not installed.

Wiki integration:
- Computes SHA256 hash for deduplication via log.md
- Adds hash to frontmatter
- Logs entries to wiki log.md
- Finds and injects [[wikilinks]] to related pages
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml

_GITHUB_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/?$")


def _github_readme_markdown(url: str) -> str | None:
    """Return raw README markdown for a bare github.com/<owner>/<repo> URL, else None.

    crawl4ai renders GitHub's nav/menu/footer chrome around the README; fetching
    raw.githubusercontent.com yields clean markdown. Tries main then master,
    README.md then readme.md. Returns None on any miss so the caller falls back
    to the full browser crawl (private repo, non-default branch, sub-path, etc.).
    """
    m = _GITHUB_REPO_RE.match(url.split("#", 1)[0].rstrip("/"))
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    for branch in ("main", "master"):
        for name in ("README.md", "readme.md"):
            raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}"
            try:
                req = Request(raw, headers={"User-Agent": "crawl-to-qmd"})
                with urlopen(req, timeout=15) as resp:
                    if getattr(resp, "status", 200) == 200:
                        return resp.read().decode("utf-8", errors="replace")
            except Exception:
                continue
    return None


QMD_CONFIG_PATH = Path.home() / ".config" / "qmd" / "index.yml"
def _get_wiki_root() -> Path:
    """Get wiki root from QMD config."""
    try:
        with open(QMD_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
        collections = data.get("collections", {})
        if "wiki" in collections:
            path = collections["wiki"].get("path")
            if path:
                return Path(os.path.expanduser(path))
    except (OSError, ValueError, AttributeError):
        pass
    return Path("P:\\\\\\.data/wiki")
def _get_wiki_log_path() -> Path:
    """Get log.md path."""
    return _get_wiki_root() / "log.md"


def _log_ingest(title: str, url: str, filepath: str, content_hash: str, collection: str, action: str = "ingested") -> None:
    """Append entry to wiki log.md. action ∈ {ingested, revised, skipped}."""
    try:
        log_path = _get_wiki_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"- **{title}** ({filepath})\n")
            f.write(f"  - URL: {url}\n")
            f.write(f"  - SHA256: {content_hash}\n")
            f.write(f"  - Source: crawl-ingest ({action})\n")
    except OSError as e:
        print(f"Warning: Could not log to log.md: {e}", file=sys.stderr)


def _qmd_search(title: str, collection: str, limit: int) -> list[dict] | None:
    """Query qmd search. Returns [{title, file}] records, [] for no hits, None on timeout/error.

    qmd's JSON record exposes a `file` path (verified) but no URL, so callers discriminate
    identity by file basename, never title.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "qmd", "search", title, "--collection", collection,
             "--format", "json", "--limit", str(limit)],
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout.decode())
    except (OSError, json.JSONDecodeError):
        return None
    return [{"title": (r.get("title") or "")[:60], "file": r.get("file") or ""} for r in data]


def _exclude_self(records: list[dict], own_file_basename: str) -> list[dict]:
    """Drop the page's own record. Identity = file basename; title is an attribute, not
    identity — two siblings sharing a title must not be dropped (LOGIC-1)."""
    return [r for r in records if Path(r["file"]).name != own_file_basename]


# Matches only a script-injected block: `## Related` followed solely by [[x]]@related lines.
# A source-authored `## Related` with prose body is left intact. Idempotent.
_RELATED_BLOCK_RE = re.compile(r"\n\n## Related\n(?:\[\[[^\]]+\]\]@related\n)+")


def _strip_related(body: str) -> str:
    """Remove a script-injected ## Related wikilink block from the body."""
    return _RELATED_BLOCK_RE.sub("", body)


# --- crawl4ai API shim + content normalization ---------------------------

def _normalize_result(result) -> dict:
    """Stable shape across crawl4ai API versions.

    Returns {url, title, markdown, internal_links, external_links, response_headers}.
    The dict-vs-list drift in result.links and any future reshaping of result.*
    is absorbed here so the crawl loop never touches raw attributes.
    """
    links = getattr(result, "links", {}) or {}
    if isinstance(links, dict):
        internal = links.get("internal", []) or []
        external = links.get("external", []) or []
    elif isinstance(links, list):
        internal, external = links, []
    else:
        internal, external = [], []

    def _href(e):
        if isinstance(e, str):
            return e
        if isinstance(e, dict):
            return e.get("href")
        return None

    metadata = getattr(result, "metadata", None) or {}
    md = getattr(result, "markdown", None) or getattr(result, "extracted_content", "") or ""
    headers = getattr(result, "response_headers", None) or {}
    return {
        "url": getattr(result, "url", "") or "",
        "title": metadata.get("title") if isinstance(metadata, dict) else None,
        "markdown": md,
        "internal_links": [h for h in (_href(e) for e in internal) if h],
        "external_links": [h for h in (_href(e) for e in external) if h],
        "response_headers": headers if isinstance(headers, dict) else {},
    }


def _extract_internal_links(norm: dict, domain: str, visited: set) -> list:
    """Filter normalized internal_links to same-domain, not-yet-visited hrefs."""
    domain = domain.replace("www.", "")
    out, seen = [], set()
    for href in norm["internal_links"]:
        if urlparse(href).netloc.replace("www.", "") != domain:
            continue
        if href in visited or href in seen:
            continue
        seen.add(href)
        out.append(href)
    return out


def _normalize_content(md: str) -> str:
    """Drift-invariant fingerprint of page body.

    ponytail: Markdown generator already stripped most HTML chrome, so this is a
    light pass — drop analytics query strings (utm/cache-busters) and collapse
    whitespace. Upgrade to DOM-aware stripping if drift still fires on real revisions.
    """
    # Strip query strings on URLs embedded in markdown
    md = re.sub(r"\?[^\s)\]]*", "", md)
    # Collapse whitespace runs to one space
    md = re.sub(r"\s+", " ", md).strip()
    return md


# --- per-domain URL registry ---------------------------------------------

REGISTRY_NAME = "index.json"


def _registry_path(domain_dir: Path) -> Path:
    return domain_dir / REGISTRY_NAME


def _load_registry(domain_dir: Path) -> dict:
    try:
        with open(_registry_path(domain_dir), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_registry(domain_dir: Path, registry: dict) -> None:
    """Atomic write so a mid-crawl crash can't corrupt the registry."""
    domain_dir.mkdir(parents=True, exist_ok=True)
    p = _registry_path(domain_dir)
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)
    tmp.replace(p)


class CrawlIngestError(Exception):
    """Raised when crawl-ingest fails."""
    pass


class DependencyError(CrawlIngestError):
    """Raised when a required dependency is missing."""
    pass


def _check_dependencies() -> None:
    """Fail-fast: verify crawl4ai and qmd are available."""
    # Check crawl4ai
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        raise DependencyError(
            "crawl4ai not installed.\n"
            "Install: pip install crawl4ai"
        )

    # Check qmd CLI via python -m
    try:
        result = subprocess.run(
            [sys.executable, "-m", "qmd", "--help"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise DependencyError(
                "qmd CLI failed.\n"
                "Install: pip install qmd\n"
                "Docs: https://github.com/tobi/qmd"
            )
    except FileNotFoundError:
        raise DependencyError(
            "qmd CLI not found (python -m qmd failed).\n"
            "Install: pip install qmd\n"
            "Docs: https://github.com/tobi/qmd"
        )


def _get_vault_path(collection: str) -> Path:
    """Get vault path for a QMD collection."""
    try:
        with open(QMD_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
        collections = data.get("collections", {})
        if collection in collections:
            path = collections[collection].get("path")
            if path:
                return Path(os.path.expanduser(path))
    except (OSError, ValueError, AttributeError):
        pass

    return Path("P:/.data/wiki") / collection


async def crawl_site(
    root_url: str,
    collection: str = "wiki",
    max_pages: int = 10,
) -> dict:
    """Crawl site and ingest into QMD collection.

    Args:
        root_url: Root URL to crawl
        collection: QMD collection name
        max_pages: Max pages to fetch
        headless: Use headless browser

    Returns:
        Dict with ingestion stats
    """
    _check_dependencies()

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai import DefaultMarkdownGenerator
    from crawl4ai import CacheMode

    vault_path = _get_vault_path(collection)
    output_dir = vault_path / "sources"

    if not vault_path.exists():
        raise CrawlIngestError(
            f"Vault path does not exist: {vault_path}\n"
            "Configure your QMD collection in ~/.config/qmd/index.yml"
        )

    stats = {
        "url": root_url,
        "collection": collection,
        "pages_fetched": 0,
        "pages_saved": 0,
        "pages_skipped": 0,
        "files_written": [],
        "crawl_errors": [],
        "write_errors": [],
    }

    # Parse domain for folder
    domain = urlparse(root_url).netloc.replace("www.", "")

    markdown_gen = DefaultMarkdownGenerator()
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=markdown_gen,
        wait_until="networkidle",
        delay_before_return_html=1.0,
    )

    # ponytail: bare github.com/<owner>/<repo> → raw README beats browser crawl
    # (crawl4ai renders GitHub nav chrome around the README). Falls back below.
    readme_md = _github_readme_markdown(root_url)
    if readme_md is not None:
        owner_repo = root_url.split("github.com/", 1)[-1].rstrip("/")
        norm = {
            "url": root_url,
            "title": owner_repo,
            "markdown": readme_md,
            "internal_links": [],
            "external_links": [],
            "response_headers": {},
        }
        stats["pages_fetched"] += 1
        saved = await _save_md(norm, output_dir, domain, 0, collection, stats)
        if saved:
            stats["pages_saved"] += 1
        elif saved is None:
            stats["pages_skipped"] += 1
    else:
        visited = {root_url}
        async with AsyncWebCrawler() as crawler:
            # Initial crawl
            result = await crawler.arun(url=root_url, config=config)
            if result.success:
                stats["pages_fetched"] += 1
                norm = _normalize_result(result)
                saved = await _save_md(norm, output_dir, domain, 0, collection, stats)
                if saved:
                    stats["pages_saved"] += 1
                elif saved is None:
                    stats["pages_skipped"] += 1

                # Follow internal links (limit to domain + dedup visited)
                urls_to_crawl = _extract_internal_links(norm, domain, visited)[: max_pages - 1]

                for i, url in enumerate(urls_to_crawl):
                    if stats["pages_fetched"] >= max_pages:
                        break
                    visited.add(url)
                    try:
                        result = await crawler.arun(url=url, config=config)
                        if result.success:
                            stats["pages_fetched"] += 1
                            norm = _normalize_result(result)
                            saved = await _save_md(norm, output_dir, domain, i + 1, collection, stats)
                            if saved:
                                stats["pages_saved"] += 1
                            elif saved is None and not any(e.startswith(url) for e in stats["crawl_errors"]):
                                stats["pages_skipped"] += 1
                    except Exception as e:
                        stats["crawl_errors"].append(f"{url}: {str(e)}")

    # Update QMD index
    try:
        subprocess.run(
            [sys.executable, "-m", "qmd", "update", collection],
            capture_output=True,
            timeout=30,
            check=True,
        )
        stats["index_updated"] = True
        # Verify index is fresh
        index_path = vault_path / ".qmd" / "index.db"
        if index_path.exists():
            index_mtime = index_path.stat().st_mtime
            # Check if any saved file is newer than index
            for f in stats["files_written"]:
                f_path = Path(f)
                if f_path.exists() and f_path.stat().st_mtime > index_mtime:
                    stats["index_stale"] = True
                    break
    except subprocess.TimeoutExpired:
        stats["crawl_errors"].append("QMD index update timed out")
    except subprocess.CalledProcessError as e:
        stats["crawl_errors"].append(f"QMD index update failed: {e.stderr.decode()}")

    # Post-index related-link injection (Change A). Gated on a fresh index (STATE-1): if
    # qmd update failed or any saved file postdates the index, skip rather than inject
    # links computed against stale state.
    if stats.get("index_updated") and not stats.get("index_stale"):
        _inject_related_links(stats, collection)
    else:
        stats["related_skipped_stale_index"] = True

    return stats


async def _save_md(
    norm: dict,
    output_dir: Path,
    domain: str,
    index: int,
    collection: str,
    stats: dict,
) -> str | None:
    """Save normalized Markdown with frontmatter, registry-driven dedup.

    Decision (URL is the primary key, in sources/{domain}/index.json):
      - URL unseen              → ingest (revisions=1)
      - URL seen, etag matches  → skip (server says unchanged)
      - URL seen, hash matches  → skip (drift-invariant body unchanged)
      - URL seen, neither match → revise (overwrite same file, revisions += 1)

    Returns filepath on ingest/revise, None on skip or no-content.
    """
    url = norm["url"] or ""
    title = norm["title"] or (url.split("/")[-1] or "Untitled")
    md_content = norm["markdown"]
    headers = norm["response_headers"]

    if not md_content:
        return None

    domain_dir = output_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    registry = _load_registry(domain_dir)
    entry = registry.get(url)

    # Drift-invariant hash + cheap header fingerprint
    content_hash = hashlib.sha256(_normalize_content(md_content).encode()).hexdigest()
    etag = headers.get("etag") or headers.get("ETag")
    last_modified = headers.get("last-modified") or headers.get("Last-Modified")

    # Path-only slug keeps filenames stable across runs and matches pre-registry files
    slug = re.sub(r"[^\w\-]", "-", urlparse(url).path.strip("/"))[:50]

    if entry:
        if etag and entry.get("etag") == etag:
            print(f"Skipping (etag unchanged): {url}")
            _log_ingest(title, url, entry.get("file", ""), content_hash, collection, action="skipped")
            return None
        if entry.get("hash") == content_hash:
            print(f"Skipping (content unchanged): {url}")
            _log_ingest(title, url, entry.get("file", ""), content_hash, collection, action="skipped")
            return None
        action = "revised"
        # Reuse the existing filename so revisions overwrite, not orphan
        filename = entry.get("file") or f"{index:03d}-{slug}.md"
    else:
        action = "ingested"
        filename = f"{index:03d}-{slug}.md"

    filepath = domain_dir / filename

    today = datetime.now().strftime("%Y-%m-%d")
    frontmatter = f"""---
source:
  url: {url}
  crawled_at: {today}
  hash: {content_hash}
title: {title}
tags:
  - web-ingested
---

"""

    try:
        filepath.write_text(frontmatter + md_content, encoding="utf-8")
        print(f"{action.capitalize()}: {filename} ({len(md_content)} chars)")
        stats["files_written"].append(str(filepath))
    except OSError as e:
        stats["write_errors"].append(f"{filepath.name}: {str(e)}")
        print(f"Write failed: {filepath.name} — {e}", file=sys.stderr)
        return None

    # Update registry (URL → stable identity + change tracking)
    registry[url] = {
        "hash": content_hash,
        "etag": etag,
        "last_modified": last_modified,
        "title": title,
        "file": filename,
        "crawled_at": today,
        "revised_at": today if action == "revised" else None,
        "revisions": (entry.get("revisions", 1) if entry else 1) + (1 if action == "revised" else 0),
    }
    _save_registry(domain_dir, registry)

    _log_ingest(title, url, str(filepath), content_hash, collection, action=action)
    return str(filepath)


_FM_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_FM_TITLE_RE = re.compile(r"\ntitle:\s*(.+?)\s*$", re.MULTILINE)


def _split_frontmatter(content: str) -> tuple[str, str]:
    """Return (frontmatter_block_incl_fences, body). frontmatter_block is '' if absent."""
    m = _FM_RE.match(content)
    if not m:
        return "", content
    return m.group(0), content[m.end():]


def _inject_related_links(stats: dict, collection: str, limit: int = 5) -> None:
    """Post-index pass: for each saved file, query the freshly-rebuilt qmd index, drop the
    page's own record, inject a ## Related wikilink section.

    STATE-3 invariant: the frontmatter block (including the dedup hash) is preserved
    byte-for-byte and the registry is never touched — only the body's trailing ## Related
    section changes. Dedup safety follows because the next crawl recomputes the hash from
    fresh crawl content, never from this file's body.
    """
    for fpath_str in stats["files_written"]:
        fpath = Path(fpath_str)
        try:
            content = fpath.read_text(encoding="utf-8")
        except OSError as e:
            stats["write_errors"].append(f"related-read {fpath.name}: {e}")
            continue

        fm, body = _split_frontmatter(content)
        title_match = _FM_TITLE_RE.search(fm)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        records = _qmd_search(title, collection, limit + 2)
        if records is None:
            stats["related_lookup_timeouts"] = stats.get("related_lookup_timeouts", 0) + 1
            continue
        related = _exclude_self(records, fpath.name)[:limit]
        if not related:
            continue

        body = _strip_related(body)
        related_links = "\n".join(f"[[{r['title']}]]@related" for r in related)
        new_body = f"{body.rstrip()}\n\n## Related\n{related_links}\n"
        fpath.write_text(fm + new_body, encoding="utf-8")


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Crawl site → QMD-ready Markdown")
    parser.add_argument("url", help="Root URL to crawl")
    parser.add_argument("--collection", default="wiki", help="QMD collection name")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to fetch")
    args = parser.parse_args()

    try:
        stats = await crawl_site(
            args.url,
            collection=args.collection,
            max_pages=args.max_pages,
        )

        print(f"\n=== SUMMARY ===")
        print(f"Pages fetched: {stats['pages_fetched']}")
        print(f"Pages saved: {stats['pages_saved']}")
        print(f"Pages skipped: {stats['pages_skipped']}")
        print(f"Collection: {stats['collection']}")
        print(f"Index updated: {stats.get('index_updated', False)}")
        if stats.get("index_stale"):
            print("WARNING: Index may be stale — some files are newer than index")
        if stats.get("related_skipped_stale_index"):
            print("NOTE: Related-link injection skipped (index stale or update failed)")
        if stats.get("related_lookup_timeouts"):
            print(f"Related lookups timed out: {stats['related_lookup_timeouts']}")
        if stats["crawl_errors"]:
            print(f"Crawl errors ({len(stats['crawl_errors'])}):")
            for err in stats["crawl_errors"][:5]:
                print(f"  - {err}")
        if stats["write_errors"]:
            print(f"Write errors ({len(stats['write_errors'])}):")
            for err in stats["write_errors"][:5]:
                print(f"  - {err}")

    except DependencyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except CrawlIngestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
