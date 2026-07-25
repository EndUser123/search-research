#!/usr/bin/env python3
"""sync.py — orchestrator for the full nlm-to-wiki pipeline.

Usage:
  # Single notebook (canonical case)
  python sync.py --notebook <uuid> --profile codex

  # All notebooks (sequential)
  python sync.py --all --profile codex --state sync-state.json

  # From nlm-bulk-ingest clusters.json (round-trip)
  python sync.py --from-clusters clusters.json --profile codex --state sync-state.json

  # Dry run (extract + parse + reconcile, no writes)
  python sync.py --notebook <uuid> --dry-run

Per-notebook crash-resumable via --state. Skips notebooks whose source_ids
haven't changed since last sync (manifest-gated).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
WIKI_VAULT = Path("P:/.data/wiki")
SYNC_MANIFEST = WIKI_VAULT / "_state" / "nlm-sync-manifest.json"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], timeout: int = 1800, capture: bool = True) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def ensure_auth(profile: str) -> bool:
    rc, _, _ = run(["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60)
    if rc == 0:
        return True
    log(f"Auth expired; silent re-auth via profile '{profile}'...")
    rc2, _, err = run(["nlm", "login", "--profile", profile], timeout=300)
    if rc2 != 0:
        log(f"  re-auth failed: {err.strip()[:200]}")
        return False
    rc3, _, _ = run(["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60)
    return rc3 == 0


def notebook_title(nb_id: str, profile: str) -> str:
    rc, out, _ = run(["nlm", "notebook", "get", nb_id, "--profile", profile, "--json"], timeout=60)
    if rc != 0:
        return nb_id
    try:
        return json.loads(out).get("title", nb_id)
    except json.JSONDecodeError:
        return nb_id


def source_id_snapshot(nb_id: str, profile: str) -> tuple[list[str], str]:
    """Return (sorted source_ids, hash) for re-sync gating."""
    rc, out, _ = run(["nlm", "source", "list", nb_id, "--profile", profile, "--json"], timeout=120)
    if rc != 0:
        return [], ""
    try:
        data = json.loads(out)
        sources = data.get("sources", []) if isinstance(data, dict) else data
        ids = sorted([s.get("id") for s in sources if s.get("id")])
        h = hashlib.sha1("|".join(ids).encode("utf-8")).hexdigest()
        return ids, h
    except json.JSONDecodeError:
        return [], ""


def load_manifest() -> dict:
    if SYNC_MANIFEST.exists():
        try:
            return json.loads(SYNC_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"notebooks": {}}


def save_manifest(m: dict) -> None:
    SYNC_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = SYNC_MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, SYNC_MANIFEST)


def sync_one(nb_id: str, profile: str, dry_run: bool,
             clusters_path: Path | None) -> dict:
    """Run the full 6-stage pipeline on one notebook. Returns result record."""
    title = notebook_title(nb_id, profile)
    log(f"=== Sync: {title} ({nb_id}) ===")

    # Stage A0: re-sync gate
    source_ids, source_hash = source_id_snapshot(nb_id, profile)
    manifest = load_manifest()
    prior = manifest["notebooks"].get(nb_id, {})
    if prior.get("source_hash") == source_hash and source_hash:
        log(f"SKIP (source_ids unchanged since last sync)")
        return {"notebook_id": nb_id, "title": title, "status": "skipped_unchanged"}

    # Stage A: extract (Report + Data-Table)
    with tempfile.TemporaryDirectory(prefix=f"nlm-sync-{nb_id[:8]}-") as td:
        tmp_dir = Path(td)
        log("Stage A: extract (Report + Data-Table)...")
        rc, out, err = run(
            ["python", str(SCRIPTS / "extract.py"),
             "--notebook", nb_id, "--profile", profile,
             "--out-dir", str(tmp_dir)], timeout=1800)
        if rc != 0:
            log(f"FATAL extract rc={rc}: {err[:400]}")
            return {"notebook_id": nb_id, "title": title, "status": "extract_failed", "error": err[:400]}
        extract_result = json.loads(out)
        report_path = Path(extract_result["report"]["path"])
        dt_path = Path(extract_result["data_table"]["path"]) if extract_result["data_table"].get("path") else None

        # Stage B: parse
        log("Stage B: parse report + data-table...")
        parse_cmd = ["python", str(SCRIPTS / "parse_report.py"),
                     "--report", str(report_path),
                     "--notebook", nb_id, "--notebook-title", title]
        if dt_path:
            parse_cmd.extend(["--data-table", str(dt_path)])
        rc, out, err = run(parse_cmd, timeout=300)
        if rc != 0:
            log(f"FATAL parse rc={rc}: {err[:400]}")
            return {"notebook_id": nb_id, "title": title, "status": "parse_failed", "error": err[:400]}
        concepts_path = tmp_dir / "concepts.json"
        concepts_path.write_text(out, encoding="utf-8")
        concepts = json.loads(out)
        log(f"  parsed {len(concepts)} concepts")
        if not concepts:
            return {"notebook_id": nb_id, "title": title, "status": "no_concepts"}

        # Stage C: reconcile
        log("Stage C: reconcile against existing wiki...")
        rc, out, err = run(
            ["python", str(SCRIPTS / "reconcile.py"),
             "--input", str(concepts_path)], timeout=300)
        if rc != 0:
            log(f"WARN reconcile rc={rc}: {err[:300]}; continuing without dedup")
            out = concepts_path.read_text(encoding="utf-8")
        reconciled_path = tmp_dir / "reconciled.json"
        reconciled_path.write_text(out, encoding="utf-8")
        reconciled = json.loads(out)
        n_new = sum(1 for c in reconciled if c.get("disposition") == "new")
        n_refine = sum(1 for c in reconciled if c.get("disposition") == "refines")
        log(f"  {n_new} new, {n_refine} refines")

        # Stage D: expand citations (skip on dry-run; saves API calls)
        enriched_path = reconciled_path
        if not dry_run:
            log("Stage D: expand citations...")
            enriched_path = tmp_dir / "enriched.json"
            rc, out, err = run(
                ["python", str(SCRIPTS / "expand_citations.py"),
                 "--input", str(reconciled_path),
                 "--output", str(enriched_path),
                 "--notebook", nb_id, "--profile", profile], timeout=1800)
            if rc != 0:
                log(f"WARN expand_citations rc={rc}: {err[:300]}; using un-enriched")
                enriched_path = reconciled_path

        if dry_run:
            log("DRY RUN — not writing pages")
            return {"notebook_id": nb_id, "title": title, "status": "dry_run",
                    "concepts_new": n_new, "concepts_refines": n_refine,
                    "sample_titles": [c["title"] for c in reconciled[:5]]}

        # Stage E: write pages (with validation)
        log("Stage E: write + validate pages...")
        staging = tmp_dir / "failed-pages"
        write_cmd = ["python", str(SCRIPTS / "write_pages.py"),
                     "--input", str(enriched_path),
                     "--vault", str(WIKI_VAULT),
                     "--staging", str(staging)]
        if clusters_path:
            write_cmd.extend(["--clusters-json", str(clusters_path)])
        rc, out, err = run(write_cmd, timeout=600)
        if rc != 0 and rc != 5:
            log(f"FATAL write rc={rc}: {err[:400]}")
            return {"notebook_id": nb_id, "title": title, "status": "write_failed", "error": err[:400]}
        write_summary = json.loads(out)
        n_written = len(write_summary["written"])
        n_failed = len(write_summary["failed"])
        log(f"  wrote {n_written} pages; {n_failed} failed validation")

        # Stage F: auto-link + log + manifest
        log("Stage F: auto-link + log + manifest...")
        auto_link(write_summary["written"])
        append_log_entries(nb_id, title, write_summary["written"])
        manifest["notebooks"][nb_id] = {
            "notebook_id": nb_id,
            "title": title,
            "last_synced_at": date.today().isoformat(),
            "source_hash": source_hash,
            "source_ids": source_ids,
            "concept_slugs": [w["slug"] for w in write_summary["written"]],
        }
        save_manifest(manifest)
        # Rebuild qmd index for the new pages
        qmd_reindex(write_summary["written"])

        return {
            "notebook_id": nb_id, "title": title, "status": "synced",
            "written": n_written, "failed_validation": n_failed,
            "url": f"https://notebooklm.google.com/notebook/{nb_id}",
        }


def auto_link(pages: list[dict]) -> None:
    awl = Path("P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_after_write.py")
    if not awl.exists():
        log(f"  WARN: auto-link script not found at {awl}")
        return
    for p in pages:
        try:
            subprocess.run(["python", str(awl), p["path"]], capture_output=True, timeout=60, encoding="utf-8")
        except subprocess.TimeoutExpired:
            pass


def append_log_entries(nb_id: str, title: str, pages: list[dict]) -> None:
    append_log = Path("P:/.data/wiki/scripts/append_log.py")
    if not append_log.exists():
        return
    for p in pages:
        try:
            subprocess.run(
                ["python", str(append_log),
                 p["title"], f"nlm-sync-{date.today().isoformat()}",
                 "grok", f"Synced from NotebookLM notebook {title}",
                 f"wiki/concepts/{p['slug']}.md"],
                capture_output=True, timeout=30, encoding="utf-8")
        except subprocess.TimeoutExpired:
            pass


def qmd_reindex(pages: list[dict]) -> None:
    for p in pages:
        slug = p["slug"]
        try:
            subprocess.run(
                ["qmd", "document", "add", "--collection", "wiki",
                 "--document-id", slug, "--markdown-file", p["path"]],
                capture_output=True, timeout=60, encoding="utf-8")
        except subprocess.TimeoutExpired:
            pass


def load_state(path: Path | None) -> dict:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"synced": [], "failed": [], "results": []}


def save_state(state: dict, path: Path | None) -> None:
    if not path:
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--notebook")
    g.add_argument("--all", action="store_true")
    g.add_argument("--from-clusters", type=Path, metavar="CLUSTERS_JSON")
    ap.add_argument("--profile", default="codex")
    ap.add_argument("--state", type=Path, help="resume-state file for --all / --from-clusters")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ensure_auth(args.profile):
        log(f"FATAL: auth failed for profile '{args.profile}'")
        return 2

    state = load_state(args.state)

    # Determine notebook list
    if args.notebook:
        notebooks = [args.notebook]
    elif args.from_clusters:
        clusters = json.loads(args.from_clusters.read_text(encoding="utf-8"))
        # clusters.json from nlm-bulk-ingest doesn't carry notebook_ids directly;
        # operator may have annotated it. Fall back to all synced notebooks.
        notebooks = []
        for c in clusters:
            nids = c.get("notebook_ids") or ([c["notebook_id"]] if c.get("notebook_id") else [])
            notebooks.extend(nids)
        if not notebooks:
            log("--from-clusters: no notebook_ids found in clusters.json")
            log("(expected: clusters annotated after nlm-bulk-ingest completes; check state file)")
            log("Falling back to all notebooks that appear in the bulk-ingest state file.")
            bi_state_path = Path("P:/tmp/wl_notebooks_run.json")
            if bi_state_path.exists():
                bi_state = json.loads(bi_state_path.read_text(encoding="utf-8"))
                notebooks = [n["notebook_id"] for n in bi_state.get("notebooks", {}).values()]
        if not notebooks:
            return 2
    else:  # --all
        rc, out, _ = run(["nlm", "notebook", "list", "--profile", args.profile, "--json"], timeout=120)
        if rc != 0:
            log("FATAL: notebook list failed")
            return 2
        try:
            data = json.loads(out)
            nbs = data if isinstance(data, list) else data.get("notebooks", [])
            notebooks = [n.get("id") for n in nbs if n.get("id")]
        except json.JSONDecodeError:
            log("FATAL: notebook list output not JSON")
            return 2

    log(f"=== {len(notebooks)} notebook(s) to sync ===")
    for nb_id in notebooks:
        if nb_id in state.get("synced", []):
            log(f"SKIP (already in state.synced): {nb_id}")
            continue
        result = sync_one(nb_id, args.profile, args.dry_run, args.from_clusters)
        state.setdefault("results", []).append(result)
        if result.get("status") in ("synced", "skipped_unchanged", "dry_run"):
            state.setdefault("synced", []).append(nb_id)
        else:
            state.setdefault("failed", []).append(nb_id)
        save_state(state, args.state)

    log("=== Pipeline complete ===")
    log(f"Synced: {len(state.get('synced', []))}/{len(notebooks)}")
    if state.get("failed"):
        log(f"Failed: {state['failed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
