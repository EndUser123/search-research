#!/usr/bin/env python3
"""maintenance.py — nlm-to-wiki state cleanup and audit.

The skill accumulates state across syncs: the manifest (per-notebook sync
records), transcript files (raw source exports), concept pages (written
output), and keyframes (vision enrichment). Notebooks get deleted, sources
get removed, v2→v3 migrations leave stale slugs. This script audits that
state and offers safe repairs.

Default mode is read-only audit. Fixes require explicit flags + --confirm.

Usage:
  # Audit (read-only, safe) — report all mismatches
  python maintenance.py --audit --account-profile a.hominidae

  # Offline audit — inspect local state without querying NotebookLM
  python maintenance.py --audit --offline

  # Fix stale manifest concept_slugs (pages deleted but slugs remain)
  python maintenance.py --fix-stale-slugs --confirm

  # Remove transcripts whose notebook no longer exists in NotebookLM
  python maintenance.py --remove-orphaned-transcripts --confirm

  # Prune ALL state for a deleted notebook (manifest + transcripts + concepts)
  python maintenance.py --prune-notebook <uuid> --confirm

  # Disk usage breakdown per notebook
  python maintenance.py --disk-report

  # Apply all safe fixes in one pass
  python maintenance.py --all-fixes --confirm
"""
from __future__ import annotations

import argparse
import fasteners
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from ytis_nlm import ensure_account_session, list_notebooks as list_canonical_notebooks

SKILL_ROOT = Path(__file__).resolve().parent.parent
WIKI_VAULT = Path("P:/.data/wiki")
TRANSCRIPTS_DIR = WIKI_VAULT / "sources" / "transcripts"
KEYFRAMES_DIR = WIKI_VAULT / "sources" / "keyframes"
CONCEPTS_DIR = WIKI_VAULT / "concepts"
SYNC_MANIFEST = WIKI_VAULT / "_state" / "nlm-sync-manifest.json"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


# --- state accessors -----------------------------------------------------

def load_manifest() -> dict:
    if SYNC_MANIFEST.exists():
        try:
            return json.loads(SYNC_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"notebooks": {}}


@contextmanager
def _manifest_lock():
    """Serialize manifest repairs with sync.py's per-file lock."""
    SYNC_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    lock_path = SYNC_MANIFEST.with_name(SYNC_MANIFEST.name + ".lock")
    with fasteners.InterProcessLock(str(lock_path)):
        yield


def _write_manifest_locked(m: dict) -> None:
    tmp = SYNC_MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, SYNC_MANIFEST)


def _update_manifest(mutator) -> object:
    """Apply one maintenance mutation to the latest manifest under lock."""
    with _manifest_lock():
        manifest = load_manifest()
        result = mutator(manifest)
        if result:
            _write_manifest_locked(manifest)
        return result


def list_notebooks(profile: str) -> set[str] | None:
    """Return live notebook IDs, or None when the live view is unavailable."""
    try:
        probe = ensure_account_session(profile, worker_id="wiki-yt-maintenance")
        if not probe.ok:
            raise RuntimeError(f"canonical auth unavailable: {probe.reason}")
        return {
            n.get("id")
            for n in list_canonical_notebooks(profile, worker_id="wiki-yt-maintenance-list")
            if n.get("id")
        }
    except Exception as exc:
        log(f"canonical notebook list failed: {str(exc)[:240]}")
        return None


def transcript_notebook_id(path: Path) -> str | None:
    """Extract notebook_id from a transcript file's frontmatter."""
    try:
        head = path.read_text(encoding="utf-8")[:800]
        for line in head.splitlines():
            if line.startswith("notebook_id:"):
                return line.split(":", 1)[1].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return None


def dir_size(path: Path) -> int:
    """Total bytes under a directory."""
    if not path.exists():
        return 0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# --- audits --------------------------------------------------------------

def audit(profile: str, *, offline: bool = False) -> dict:
    """Run all audit checks; return a structured report."""
    manifest = load_manifest()
    live_notebooks = None if offline else list_notebooks(profile)
    report = {
        "live_inventory_status": "skipped" if offline else (
            "available" if live_notebooks is not None else "unavailable"
        ),
        "live_notebooks_available": live_notebooks is not None,
        "live_notebook_count": len(live_notebooks) if live_notebooks is not None else None,
        "tracked_notebook_count": len(manifest.get("notebooks", {})),
        "stale_slugs": [],          # manifest concept_slugs whose pages don't exist
        "orphaned_transcripts": [],  # transcripts whose notebook is gone from NotebookLM
        "untracked_transcripts": 0,  # transcripts whose notebook_id is not in manifest
        "orphaned_manifest_entries": [],  # manifest entries whose notebook is gone from NotebookLM
        "missing_pipeline_tag": [], # manifest entries without v3 pipeline tag
    }

    # 1. Stale concept_slugs
    for nb_id, entry in manifest.get("notebooks", {}).items():
        for slug in entry.get("concept_slugs", []):
            page = CONCEPTS_DIR / f"{slug}.md"
            if not page.exists():
                report["stale_slugs"].append({"notebook_id": nb_id, "slug": slug})
        if "pipeline" not in entry:
            report["missing_pipeline_tag"].append(nb_id)

    # 2. Orphaned transcripts (notebook deleted from NotebookLM)
    if TRANSCRIPTS_DIR.exists():
        for f in TRANSCRIPTS_DIR.glob("*.md"):
            nid = transcript_notebook_id(f)
            if nid and live_notebooks is not None and nid not in live_notebooks:
                report["orphaned_transcripts"].append({
                    "file": f.name, "notebook_id": nid,
                })
            elif nid and nid not in manifest.get("notebooks", {}):
                report["untracked_transcripts"] += 1

    # 3. Orphaned manifest entries
    if live_notebooks is not None:
        for nb_id in manifest.get("notebooks", {}):
            if nb_id not in live_notebooks:
                report["orphaned_manifest_entries"].append(nb_id)

    return report


def print_audit(report: dict) -> None:
    print("\n=== wiki-yt audit ===\n")
    if report.get("live_inventory_status") == "skipped":
        print("Live notebooks in NotebookLM: SKIPPED (--offline; no orphan decisions made)")
    elif report.get("live_notebooks_available"):
        print(f"Live notebooks in NotebookLM: {report['live_notebook_count']}")
    else:
        print("Live notebooks in NotebookLM: UNAVAILABLE (no orphan decisions made)")
    print(f"Tracked in manifest:          {report['tracked_notebook_count']}")
    print()
    if report["stale_slugs"]:
        print(f"⚠ STALE CONCEPT_SLUGS ({len(report['stale_slugs'])}):")
        for s in report["stale_slugs"][:10]:
            print(f"    {s['notebook_id'][:12]}  {s['slug']}")
        if len(report["stale_slugs"]) > 10:
            print(f"    ... and {len(report['stale_slugs']) - 10} more")
        print("  → fix with: --fix-stale-slugs --confirm")
        print()
    else:
        print("✓ no stale concept_slugs")
    if report["orphaned_transcripts"]:
        n = len(report["orphaned_transcripts"])
        print(f"⚠ ORPHANED TRANSCRIPTS ({n}): notebook deleted, transcripts remain")
        nb_ids = sorted({t["notebook_id"] for t in report["orphaned_transcripts"]})
        for nid in nb_ids[:5]:
            print(f"    {nid[:12]}")
        if len(nb_ids) > 5:
            print(f"    ... and {len(nb_ids) - 5} more notebooks")
        print("  → fix with: --remove-orphaned-transcripts --confirm")
        print()
    else:
        print("✓ no orphaned transcripts")
    if report["orphaned_manifest_entries"]:
        print(f"⚠ ORPHANED MANIFEST ENTRIES ({len(report['orphaned_manifest_entries'])}):")
        for nid in report["orphaned_manifest_entries"][:5]:
            print(f"    {nid[:12]}  {manifest_title(nid)}")
        print("  → fix with: --prune-notebook <uuid> --confirm")
        print()
    if report["missing_pipeline_tag"]:
        print(f"ℹ PRE-V3 MANIFEST ENTRIES ({len(report['missing_pipeline_tag'])}): no pipeline tag")
        print("  (harmless; next re-sync will add it. No action needed.)")
        print()


def manifest_title(nb_id: str) -> str:
    m = load_manifest()
    return m.get("notebooks", {}).get(nb_id, {}).get("title", "")


# --- fixes ---------------------------------------------------------------

def fix_stale_slugs(confirm: bool) -> int:
    """Clear manifest concept_slugs whose pages don't exist on disk."""
    def clear_stale(manifest, *, report=False):
        cleared = 0
        for nb_id, entry in manifest.get("notebooks", {}).items():
            kept = []
            for slug in entry.get("concept_slugs", []):
                page = CONCEPTS_DIR / f"{slug}.md"
                if page.exists():
                    kept.append(slug)
                else:
                    cleared += 1
                    if report:
                        log(f"  clear stale slug: {nb_id[:12]}  {slug}")
            entry["concept_slugs"] = kept
        return cleared

    preview_count = clear_stale(load_manifest(), report=True)
    if preview_count and confirm:
        applied = _update_manifest(lambda current: clear_stale(current))
        log(f"Cleared {applied} stale slug(s) from manifest.")
    elif preview_count:
        log(f"DRY RUN: would clear {preview_count} stale slug(s). Re-run with --confirm to apply.")
    else:
        log("No stale slugs found.")
    return preview_count


def remove_orphaned_transcripts(confirm: bool) -> int:
    """Remove transcripts whose notebook is no longer in NotebookLM."""
    # Requires live notebook list; caller passes profile via global
    live = list_notebooks(GLOBAL_PROFILE)
    if live is None:
        log("Cannot verify orphan status: live notebook list unavailable.")
        return 2
    removed = 0
    if not TRANSCRIPTS_DIR.exists():
        log("No transcripts directory.")
        return 0
    for f in TRANSCRIPTS_DIR.glob("*.md"):
        nid = transcript_notebook_id(f)
        if nid and nid not in live:
            log(f"  orphaned: {f.name} (notebook {nid[:12]} deleted)")
            if confirm:
                f.unlink()
                removed += 1
    if removed:
        log(f"Removed {removed} orphaned transcript(s).")
    elif not confirm:
        # count only
        count = sum(1 for f in TRANSCRIPTS_DIR.glob("*.md")
                    if (transcript_notebook_id(f) or "") not in live)
        log(f"DRY RUN: would remove {count} orphaned transcript(s). Re-run with --confirm.")
    else:
        log("No orphaned transcripts found.")
    return removed


def prune_notebook(nb_id: str, confirm: bool) -> int:
    """Remove ALL state for a notebook: manifest entry + transcripts + concept pages.

    Destructive — requires explicit --confirm. Concept pages are moved to a
    trash dir (recoverable), not deleted outright.
    """
    manifest = load_manifest()
    entry = manifest.get("notebooks", {}).get(nb_id)
    if not entry:
        log(f"No manifest entry for {nb_id}; nothing to prune.")
        return 0

    removed = 0
    log(f"Pruning notebook {nb_id} ({entry.get('title', '')}):")

    # 1. Manifest entry
    slugs = entry.get("concept_slugs", [])
    log(f"  manifest entry: {len(slugs)} concept_slugs, last_synced {entry.get('last_synced_at')}")

    # 2. Transcripts
    n_tx = 0
    if TRANSCRIPTS_DIR.exists():
        for f in TRANSCRIPTS_DIR.glob("*.md"):
            if transcript_notebook_id(f) == nb_id:
                n_tx += 1
    log(f"  transcripts: {n_tx} files")

    # 3. Concept pages (move to trash, don't delete)
    trash = WIKI_VAULT / "_state" / "nlm-trash" / nb_id
    n_pages = 0
    for slug in slugs:
        page = CONCEPTS_DIR / f"{slug}.md"
        if page.exists():
            n_pages += 1
    log(f"  concept pages: {n_pages} files")

    if not confirm:
        log("DRY RUN: re-run with --confirm to prune.")
        return 0

    # Apply
    if TRANSCRIPTS_DIR.exists():
        for f in TRANSCRIPTS_DIR.glob("*.md"):
            if transcript_notebook_id(f) == nb_id:
                f.unlink()
                removed += 1
    trash.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        page = CONCEPTS_DIR / f"{slug}.md"
        if page.exists():
            shutil.move(str(page), str(trash / page.name))
            removed += 1
    # Keyframes
    kf = KEYFRAMES_DIR / nb_id
    if kf.exists():
        shutil.rmtree(kf, ignore_errors=True)
    # Manifest: reload under the shared lock so a concurrent sync cannot erase
    # unrelated notebook entries. Destructive maintenance should still run
    # only while queue workers are idle because it moves files as well.
    def remove_entry(current):
        notebooks = current.setdefault("notebooks", {})
        if nb_id not in notebooks:
            return False
        del notebooks[nb_id]
        return True

    _update_manifest(remove_entry)
    log(f"Pruned {removed} files. Concept pages moved to {trash}. Manifest entry removed.")
    return removed


def disk_report() -> None:
    """Print disk usage breakdown: transcripts + keyframes per notebook."""
    manifest = load_manifest()
    print("\n=== wiki-yt disk usage ===\n")
    tx_total = dir_size(TRANSCRIPTS_DIR)
    kf_total = dir_size(KEYFRAMES_DIR)
    print(f"Total transcripts: {fmt_bytes(tx_total)} ({TRANSCRIPTS_DIR})")
    print(f"Total keyframes:   {fmt_bytes(kf_total)} ({KEYFRAMES_DIR})")
    print()

    # Per-notebook transcript size
    by_nb: dict[str, int] = {}
    if TRANSCRIPTS_DIR.exists():
        for f in TRANSCRIPTS_DIR.glob("*.md"):
            nid = transcript_notebook_id(f) or "unknown"
            try:
                by_nb[nid] = by_nb.get(nid, 0) + f.stat().st_size
            except OSError:
                pass
    if by_nb:
        print(f"{'notebook_id':<14} {'transcripts':>12}  {'title'}")
        print("-" * 80)
        for nid, size in sorted(by_nb.items(), key=lambda kv: -kv[1]):
            title = manifest.get("notebooks", {}).get(nid, {}).get("title", "(untracked)")[:50]
            print(f"{nid[:12]:<14} {fmt_bytes(size):>12}  {title}")


# --- main ----------------------------------------------------------------

GLOBAL_PROFILE = "a.hominidae"  # set from args; used by remove_orphaned_transcripts


def main() -> int:
    global GLOBAL_PROFILE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", action="store_true", help="read-only audit (default if no other action)")
    ap.add_argument("--fix-stale-slugs", action="store_true")
    ap.add_argument("--remove-orphaned-transcripts", action="store_true")
    ap.add_argument("--prune-notebook", metavar="UUID", help="remove ALL state for a notebook")
    ap.add_argument("--all-fixes", action="store_true", help="run fix-stale-slugs + remove-orphaned-transcripts")
    ap.add_argument("--disk-report", action="store_true")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="skip the live NotebookLM inventory query (audit/local repairs only)",
    )
    ap.add_argument("--profile", "--account-profile", dest="profile", default="a.hominidae",
                    help="exact account identity (a.hominidae, troup.hominidae, or brsthomson)")
    ap.add_argument("--confirm", action="store_true",
                    help="required to apply any destructive change (default is dry-run)")
    args = ap.parse_args()

    if args.offline and (args.remove_orphaned_transcripts or args.all_fixes):
        ap.error("--offline cannot be combined with --remove-orphaned-transcripts or --all-fixes")

    GLOBAL_PROFILE = args.profile

    # Default action: audit
    if not any([args.audit, args.fix_stale_slugs, args.remove_orphaned_transcripts,
                args.prune_notebook, args.all_fixes, args.disk_report]):
        args.audit = True

    exit_code = 0
    if args.audit or args.all_fixes:
        report = audit(args.profile, offline=args.offline)
        print_audit(report)
        if not args.offline and not report.get("live_notebooks_available"):
            exit_code = 2

    if args.disk_report:
        disk_report()

    if args.fix_stale_slugs or args.all_fixes:
        fix_stale_slugs(args.confirm)

    if args.remove_orphaned_transcripts or args.all_fixes:
        exit_code = max(exit_code, remove_orphaned_transcripts(args.confirm))

    if args.prune_notebook:
        prune_notebook(args.prune_notebook, args.confirm)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
