#!/usr/bin/env python3
"""sync.py — orchestrator for the full nlm-to-wiki v3 pipeline.

Usage:
  # Single notebook (canonical case)
  python sync.py --notebook <uuid> --profile a.hominidae

  # All notebooks (sequential)
  python sync.py --all --profile a.hominidae --state sync-state.json

  # From nlm-bulk-ingest clusters.json (round-trip)
  python sync.py --from-clusters clusters.json --profile a.hominidae --state sync-state.json

  # Dry run (export + cluster + synthesize + reconcile, no page writes)
  python sync.py --notebook <uuid> --dry-run

  # v3: with optional vision enrichment (high-scene-change videos only)
  python sync.py --notebook <uuid> --enrich-vision --max-subtopics 12

Per-notebook crash-resumable via --state. Skips notebooks whose source_ids
haven't changed since last sync (manifest-gated).

Pipeline (v3): export transcripts → cluster into sub-topics → synthesize
concept pages per sub-topic (LLM) → reconcile → write+validate → link/log.
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
             clusters_path: Path | None,
             enrich_vision: bool = False,
             max_subtopics: int = 10,
             synth_backend: str | None = None) -> dict:
    """Run the full v3 pipeline on one notebook. Returns result record.

    Pipeline: export transcripts → cluster → synthesize → reconcile →
    write pages → link/log/manifest. Vision enrichment is opt-in.
    """
    import time as _time
    sync_start_time = _time.time()
    title = notebook_title(nb_id, profile)
    log(f"=== Sync: {title} ({nb_id}) ===")

    # Stage A0: re-sync gate
    source_ids, source_hash = source_id_snapshot(nb_id, profile)
    manifest = load_manifest()
    prior = manifest["notebooks"].get(nb_id, {})
    if prior.get("source_hash") == source_hash and source_hash:
        log("SKIP (source_ids unchanged since last sync)")
        return {"notebook_id": nb_id, "title": title, "status": "skipped_unchanged"}

    # Transcripts are durable (wiki/sources/transcripts/); cluster+synthesize use tmp.
    transcripts_dir = WIKI_VAULT / "sources" / "transcripts"

    # Stage A: export transcripts (v3 — raw source content, not Report synthesis)
    log("Stage A: export transcripts...")
    rc, out, err = run(
        ["python", str(SCRIPTS / "export_transcripts.py"),
         "--notebook", nb_id, "--profile", profile,
         "--out", str(transcripts_dir)], timeout=5400)
    # rc=0: all succeeded. rc=5: partial failure (some sources couldn't be fetched —
    # common for status=3 sources that NotebookLM failed to index). Non-fatal: the
    # succeeded transcripts are still valuable; crash-resume handles gaps on re-run.
    # Only rc=2 (fatal: no sources / auth failure) aborts the pipeline.
    if rc == 2:
        log(f"FATAL export_transcripts rc={rc}: {err[:400]}")
        return {"notebook_id": nb_id, "title": title, "status": "export_failed", "error": err[:400]}
    if rc == 5:
        log("WARN export_transcripts rc=5 (partial failure — some sources status=3); continuing with succeeded transcripts")
    elif rc != 0:
        log(f"WARN export_transcripts rc={rc}: {err[:300]}; continuing")
    export_result = json.loads(out)
    n_exported = export_result.get("exported", 0)
    n_skipped = export_result.get("skipped", 0)
    n_failed = export_result.get("failed", 0)
    log(f"  exported {n_exported} new, {n_skipped} already present, {n_failed} failed (status=3/unrecoverable)")

    # Stage A2 (optional): vision enrichment (high-scene-change videos only)
    if enrich_vision:
        log("Stage A2: vision enrichment (high-scene-change only)...")
        rc, out, err = run(
            ["python", str(SCRIPTS / "enrich_vision.py"),
             "--notebook", nb_id, "--profile", profile,
             "--transcripts-dir", str(transcripts_dir)], timeout=7200)
        if rc != 0:
            log(f"WARN enrich_vision rc={rc}: {err[:300]}; continuing without vision")
        else:
            vis = json.loads(out)
            log(f"  enriched {vis.get('enriched', 0)}, skipped {vis.get('skipped_low_density', 0)}")

    with tempfile.TemporaryDirectory(prefix=f"nlm-sync-{nb_id[:8]}-") as td:
        tmp_dir = Path(td)

        # Stage B: cluster transcripts into sub-topics
        log(f"Stage B: cluster transcripts (max {max_subtopics} sub-topics)...")
        subtopics_path = tmp_dir / "subtopics.json"
        rc, out, err = run(
            ["python", str(SCRIPTS / "cluster_transcripts.py"),
             "--transcripts-dir", str(transcripts_dir),
             "--max-subtopics", str(max_subtopics),
             "--notebook", nb_id,
             "-o", str(subtopics_path)], timeout=900)
        if rc != 0:
            log(f"FATAL cluster_transcripts rc={rc}: {err[:400]}")
            return {"notebook_id": nb_id, "title": title, "status": "cluster_failed", "error": err[:400]}
        cluster_result = json.loads(subtopics_path.read_text(encoding="utf-8"))
        n_clusters = cluster_result.get("cluster_count", 0)
        log(f"  {n_clusters} sub-topic clusters")
        if n_clusters == 0:
            return {"notebook_id": nb_id, "title": title, "status": "no_clusters"}

        # Stage C: synthesize concept pages per sub-topic
        log("Stage C: synthesize sub-topic concept pages...")
        concepts_path = tmp_dir / "concepts.json"
        synth_cmd = ["python", str(SCRIPTS / "synthesize_subtopics.py"),
                     "--subtopics", str(subtopics_path),
                     "--transcripts-dir", str(transcripts_dir),
                     "--notebook", nb_id, "--notebook-title", title,
                     "-o", str(concepts_path)]
        if synth_backend:
            synth_cmd.extend(["--backend", synth_backend])
        rc, out, err = run(synth_cmd, timeout=3600)
        if rc != 0:
            log(f"WARN synthesize rc={rc}: {err[:300]} (partial output may exist)")
        concepts = json.loads(concepts_path.read_text(encoding="utf-8"))
        log(f"  synthesized {len(concepts)} concept pages")
        if not concepts:
            return {"notebook_id": nb_id, "title": title, "status": "no_concepts"}

        # Stage D: reconcile
        log("Stage D: reconcile against existing wiki...")
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

        if dry_run:
            log("DRY RUN — not writing pages")
            return {"notebook_id": nb_id, "title": title, "status": "dry_run",
                    "concepts_new": n_new, "concepts_refines": n_refine,
                    "transcripts_exported": n_exported,
                    "clusters": n_clusters,
                    "sample_titles": [c["title"] for c in reconciled[:5]]}

        # Stage E: write pages (with validation)
        log("Stage E: write + validate pages...")
        staging = tmp_dir / "failed-pages"
        write_cmd = ["python", str(SCRIPTS / "write_pages.py"),
                     "--input", str(reconciled_path),
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
            "pipeline": "v3-transcript-cluster",
            "concept_slugs": [w["slug"] for w in write_summary["written"]],
        }
        save_manifest(manifest)
        # Reindex removed (qmd was uninstalled from the workspace; pages are
        # still written and valid — they'll be indexed by the next indexer wired)

        # Stage G: rename notebook with [INGESTED] prefix for visual tracking
        if not title.startswith("[INGESTED]"):
            log("Stage G: rename notebook with [INGESTED] prefix...")
            new_title = f"[INGESTED] - {title}"
            rc, _, err = run(["nlm", "notebook", "rename", nb_id, new_title,
                              "--profile", profile], timeout=60)
            if rc == 0:
                log(f"  renamed: {title} → {new_title}")
                manifest["notebooks"][nb_id]["original_title"] = title
                manifest["notebooks"][nb_id]["title"] = new_title
                save_manifest(manifest)
            else:
                log(f"WARN rename rc={rc}: {err[:200]}; continuing")
        else:
            log("Stage G: already prefixed [INGESTED], skipping rename")

        # Stage H: auto-generate pipeline report (progressive disclosure)
        log("Stage H: generate pipeline report...")
        sync_duration = time.time() - sync_start_time if sync_start_time else None
        report_cmd = ["python", str(SCRIPTS / "report.py"),
                      "--notebook", nb_id, "--profile", profile]
        if sync_duration:
            report_cmd.extend(["--duration", str(sync_duration)])
        rc, out, _ = run(report_cmd, timeout=120)
        if rc == 0 and out.strip():
            # Print the Level 1 + Level 2 summary to stderr (sync logs go to stderr)
            print(out.strip(), file=sys.stderr)

        return {
            "notebook_id": nb_id, "title": title, "status": "synced",
            "written": n_written, "failed_validation": n_failed,
            "transcripts_exported": n_exported,
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
        except Exception:
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
        except Exception:
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


def list_notebooks(profile: str) -> list[dict]:
    """Return the account's notebooks (id, title, source_count)."""
    rc, out, _ = run(["nlm", "notebook", "list", "--profile", profile, "--json"], timeout=120)
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else data.get("notebooks", [])
    except json.JSONDecodeError:
        return []


def notebook_status(profile: str, min_sources: int = 10) -> list[dict]:
    """Build a status table: notebook × {synced?, transcripts, concept_pages}.

    Filters to notebooks with >= min_sources (skips test/worker junk).
    """
    nbs = list_notebooks(profile)
    manifest = load_manifest()
    transcripts_dir = WIKI_VAULT / "sources" / "transcripts"
    rows = []
    for nb in nbs:
        nid = nb.get("id")
        sc = nb.get("source_count") or 0
        if sc < min_sources:
            continue
        m = manifest["notebooks"].get(nid, {})
        # Count transcripts whose frontmatter notebook_id matches
        n_tx = 0
        if transcripts_dir.exists():
            for f in transcripts_dir.glob("*.md"):
                try:
                    head = f.read_text(encoding="utf-8")[:600]
                    if f"notebook_id: {nid}" in head:
                        n_tx += 1
                except (OSError, UnicodeDecodeError):
                    continue
        rows.append({
            "notebook_id": nid,
            "title": nb.get("title", "")[:60],
            "source_count": sc,
            "last_synced": m.get("last_synced_at", "—"),
            "pipeline": m.get("pipeline", "—"),
            "concept_pages": len(m.get("concept_slugs", [])),
            "transcripts": n_tx,
            "synced": bool(m),
        })
    rows.sort(key=lambda r: -r["source_count"])
    return rows


def print_status(profile: str, min_sources: int) -> int:
    """Print notebook sync status as a table; return 0."""
    rows = notebook_status(profile, min_sources)
    if not rows:
        log("No notebooks found (or none meet --min-sources threshold).")
        return 0
    print(f"\n{'notebook_id':<14} {'srcs':>5} {'synced':<10} {'tx':>5} {'pages':>5} {'pipeline':<22} {'title'}")
    print("-" * 110)
    for r in rows:
        flag = "yes" if r["synced"] else "—"
        print(f"{r['notebook_id'][:12]:<14} {r['source_count']:>5} {flag:<10} "
              f"{r['transcripts']:>5} {r['concept_pages']:>5} {r['pipeline']:<22} {r['title']}")
    print(f"\n{len(rows)} notebooks (>= {min_sources} sources). "
          f"Synced: {sum(1 for r in rows if r['synced'])}. "
          f"Run `python sync.py --notebook <id>` to sync one, or `--all` for everything.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=False)  # no-arg → status picker
    g.add_argument("--notebook")
    g.add_argument("--all", action="store_true")
    g.add_argument("--from-clusters", type=Path, metavar="CLUSTERS_JSON")
    g.add_argument("--status", action="store_true",
                   help="print notebook sync status table and exit (also the default when no target given)")
    ap.add_argument("--profile", default="a.hominidae")
    ap.add_argument("--state", type=Path, help="resume-state file for --all / --from-clusters")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-sources", type=int, default=10,
                    help="status filter: skip notebooks with fewer sources (default 10)")
    ap.add_argument("--enrich-vision", action="store_true",
                    help="v3: run crv vision enrichment on high-scene-change videos (opt-in)")
    ap.add_argument("--max-subtopics", type=int, default=10,
                    help="v3: max sub-topic clusters per notebook (default 10)")
    ap.add_argument("--synth-backend", choices=["mmx", "dgemma"], default=None,
                    help="v3: LLM backend for sub-topic synthesis (default mmx)")
    args = ap.parse_args()

    # No target → status picker (the friendly default)
    if not (args.notebook or args.all or args.from_clusters or args.status):
        if not ensure_auth(args.profile):
            log(f"FATAL: auth failed for profile '{args.profile}'")
            return 2
        return print_status(args.profile, args.min_sources)

    if args.status:
        if not ensure_auth(args.profile):
            log(f"FATAL: auth failed for profile '{args.profile}'")
            return 2
        return print_status(args.profile, args.min_sources)

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
        result = sync_one(nb_id, args.profile, args.dry_run, args.from_clusters,
                          enrich_vision=args.enrich_vision,
                          max_subtopics=args.max_subtopics,
                          synth_backend=args.synth_backend)
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
