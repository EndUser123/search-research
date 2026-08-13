#!/usr/bin/env python3
"""sync.py — orchestrator for the full wiki-yt v3 pipeline.

Usage:
  # Single notebook (canonical case)
  python sync.py --notebook <uuid> --account-profile a.hominidae

  # All notebooks (sequential)
  python sync.py --all --account-profile a.hominidae --state sync-state.json

  # From nlm-bulk-ingest clusters.json (round-trip)
  python sync.py --from-clusters clusters.json --account-profile a.hominidae --state sync-state.json

  # Dry run (export + cluster + synthesize + reconcile, no page writes)
  python sync.py --notebook <uuid> --dry-run

  # Force semantic regeneration even when source IDs are unchanged
  python sync.py --notebook <uuid> --force-resynthesis --synth-backend mmx

  # v3: with optional vision enrichment (high-scene-change videos only)
  python sync.py --notebook <uuid> --enrich-vision --max-subtopics 12

Per-notebook crash-resumable via --state. Skips notebooks whose source_ids
haven't changed since last sync (manifest-gated).

Pipeline (v3): export transcripts → cluster into sub-topics → synthesize
concept pages per sub-topic (LLM) → reconcile → write+validate → link/log.
"""
from __future__ import annotations

import argparse
import fasteners
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import date
from pathlib import Path

from ytis_nlm import (
    ensure_account_session,
    get_notebook,
    list_notebooks as list_nlm_notebooks,
    list_sources,
    rename_notebook,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
WIKI_VAULT = Path("P:/.data/wiki")
SYNC_MANIFEST = WIKI_VAULT / "_state" / "nlm-sync-manifest.json"
CHILD_FAILURE_ROOT = Path("P:/.logs/wiki-yt-queue/child-failures")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], timeout: int = 1800, capture: bool = True) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def persist_child_failure(
    notebook_id: str,
    stage: str,
    returncode: int,
    stdout: str,
    stderr: str,
) -> str:
    """Persist complete child output before the temporary sync run disappears."""
    safe_stage = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stage)
    path = CHILD_FAILURE_ROOT / (
        f"{notebook_id[:16]}-{safe_stage}-{uuid.uuid4().hex}.json"
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_and_fsync(
            path,
            json.dumps(
                {
                    "notebook_id": notebook_id,
                    "stage": stage,
                    "returncode": returncode,
                    "stdout": stdout or "",
                    "stderr": stderr or "",
                    "created_at_epoch": time.time(),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    except OSError as exc:
        log(f"WARN unable to persist {stage} child failure: {type(exc).__name__}: {exc}")
        return ""

    # Keep stable classifier markers visible in the outer queue receipt even
    # when the detailed child stderr is longer than the summary log window.
    for line in (stderr or "").splitlines():
        if line.startswith(("FAILURE_CLASS=", "SYNTHESIS_QUALITY=")):
            log(line)
    log(f"CHILD_FAILURE_RECEIPT={path}")
    return str(path)


def ensure_auth(profile: str) -> bool:
    """Validate and durably repair canonical auth without user interaction."""
    try:
        probe = ensure_account_session(profile, worker_id="wiki-yt-coordinator")
    except Exception as exc:  # fail closed with an actionable operator message
        log(f"FATAL canonical auth probe failed for account '{profile}': {exc}")
        return False
    if probe.ok:
        return True
    log(
        f"FATAL canonical auth unavailable for account '{profile}': {probe.reason}; "
        "non-interactive durable repair was attempted; no user login was requested"
    )
    return False


def notebook_title(nb_id: str, profile: str) -> str:
    try:
        data = get_notebook(profile, nb_id, worker_id="wiki-yt-title")
    except Exception:
        return nb_id
    return data.get("title", nb_id) or nb_id


def source_id_snapshot(nb_id: str, profile: str) -> tuple[list[str], str]:
    """Return (sorted source_ids, hash) for re-sync gating."""
    try:
        sources = list_sources(profile, nb_id, worker_id="wiki-yt-snapshot")
    except Exception as exc:
        raise RuntimeError(
            f"canonical source snapshot failed for notebook {nb_id}: "
            f"{type(exc).__name__}: {str(exc)[:300]}"
        ) from exc
    ids = sorted([s.get("id") for s in sources if s.get("id")])
    h = hashlib.sha1("|".join(ids).encode("utf-8")).hexdigest()
    return ids, h


def load_manifest() -> dict:
    if SYNC_MANIFEST.exists():
        try:
            return json.loads(SYNC_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"notebooks": {}}


def save_manifest(m: dict) -> None:
    SYNC_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    lock_path = SYNC_MANIFEST.with_name(SYNC_MANIFEST.name + ".lock")
    with fasteners.InterProcessLock(str(lock_path)):
        # Multiple queue workers can finish concurrently. Merge the caller's
        # notebook updates into the latest on-disk state while holding the
        # lock, rather than replacing newer siblings from a stale snapshot.
        current = load_manifest()
        current_notebooks = current.setdefault("notebooks", {})
        current_notebooks.update(m.get("notebooks", {}))
        tmp = SYNC_MANIFEST.with_suffix(".tmp")
        _write_and_fsync(tmp, json.dumps(current, ensure_ascii=False, indent=2))
        os.replace(tmp, SYNC_MANIFEST)


def _export_receipt(export_result: dict) -> dict[str, int]:
    """Select deterministic export outcome counters for durable sync receipts."""
    return {
        key: int(export_result.get(key, 0) or 0)
        for key in (
            "from_cache_count",
            "cache_hit_count",
            "cache_miss_count",
            "cache_unresolved_count",
            "feed_forward_success_count",
            "feed_forward_failure_count",
        )
    }


def sync_one(nb_id: str, profile: str, dry_run: bool,
             clusters_path: Path | None,
             enrich_vision: bool = False,
             max_subtopics: int = 10,
             synth_backend: str | None = None,
             allow_degraded_fallback: bool = False,
             force_resynthesis: bool = False,
             synth_context_budget: int | None = None,
             synth_checkpoint: Path | None = None,
             synth_resume: Path | None = None) -> dict:
    """Run the full v3 pipeline on one notebook. Returns result record.

    Pipeline: export transcripts → cluster → synthesize → reconcile →
    write pages → link/log/manifest. Vision enrichment is opt-in.
    """
    if synth_context_budget is not None and synth_context_budget <= 0:
        raise ValueError("synth_context_budget must be > 0")
    if synth_checkpoint is not None and synth_resume is not None:
        raise ValueError("synth_checkpoint and synth_resume are mutually exclusive")
    import time as _time
    sync_start_time = _time.time()
    title = notebook_title(nb_id, profile)
    log(f"=== Sync: {title} ({nb_id}) ===")

    # Stage A0: re-sync gate
    try:
        source_ids, source_hash = source_id_snapshot(nb_id, profile)
    except RuntimeError as exc:
        log(f"FATAL {exc}")
        return {"notebook_id": nb_id, "title": title,
                "status": "source_snapshot_failed", "error": str(exc)}
    manifest = load_manifest()
    prior = manifest["notebooks"].get(nb_id, {})
    if prior.get("source_hash") == source_hash and source_hash and not force_resynthesis:
        log("SKIP (source_ids unchanged since last sync)")
        return {"notebook_id": nb_id, "title": title, "status": "skipped_unchanged"}
    if force_resynthesis and prior.get("source_hash") == source_hash and source_hash:
        log("FORCE RESYNTHESIS (source_ids unchanged; rebuilding semantic pages)")

    # Transcripts are durable (wiki/sources/transcripts/); cluster+synthesize use tmp.
    transcripts_dir = WIKI_VAULT / "sources" / "transcripts"

    # Stage A: export transcripts (v3 — raw source content, not Report synthesis)
    log("Stage A: export transcripts...")
    rc, out, err = run(
            ["python", str(SCRIPTS / "export_transcripts.py"),
         "--notebook", nb_id, "--account-profile", profile,
         "--out", str(transcripts_dir)], timeout=5400)
    try:
        export_result = json.loads(out)
    except json.JSONDecodeError:
        log(f"FATAL export_transcripts returned invalid JSON (rc={rc}): {err[:400]}")
        return {"notebook_id": nb_id, "title": title, "status": "export_failed",
                "error": f"invalid export result (rc={rc})"}
    n_exported = export_result.get("exported", 0)
    n_skipped = export_result.get("skipped", 0)
    n_failed = export_result.get("failed", 0)
    export_receipt = _export_receipt(export_result)
    log(f"  exported {n_exported} new, {n_skipped} already present, {n_failed} failed (status=3/unrecoverable)")
    if rc != 0 or export_result.get("auth_failed") or export_result.get("fatal_error"):
        status = "export_partial" if rc == 5 and n_exported + n_skipped else "export_failed"
        log(f"FATAL export_transcripts rc={rc}; preserving transcripts but not advancing the notebook")
        return {"notebook_id": nb_id, "title": title, "status": status,
                "exported": n_exported, "skipped": n_skipped, "failed": n_failed,
                "error": (err or "; ".join(export_result.get("errors", [])))[:400]}

    # Stage A2 (optional): vision enrichment (high-scene-change videos only)
    if enrich_vision:
        log("Stage A2: vision enrichment (high-scene-change only)...")
        rc, out, err = run(
            ["python", str(SCRIPTS / "enrich_vision.py"),
             "--notebook", nb_id, "--account-profile", profile,
             "--transcripts-dir", str(transcripts_dir)], timeout=7200)
        if rc != 0:
            log(f"FATAL enrich_vision rc={rc}: {err[:300]}")
            return {"notebook_id": nb_id, "title": title, "status": "vision_failed",
                    "error": err[:400], "transcripts_exported": n_exported}
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
        if synth_context_budget is not None:
            synth_cmd.extend(["--context-budget", str(synth_context_budget)])
        if synth_resume is not None:
            synth_cmd.extend(["--resume", str(synth_resume)])
        elif synth_checkpoint is not None:
            synth_cmd.extend(["--checkpoint", str(synth_checkpoint)])
        if allow_degraded_fallback:
            synth_cmd.append("--allow-degraded-fallback")
        rc, out, err = run(synth_cmd, timeout=3600)
        if rc != 0:
            receipt = persist_child_failure(nb_id, "synthesis", rc, out, err)
            detail = f"{err[:300]}"
            if receipt:
                detail += f"; child_receipt={receipt}"
            log(f"FATAL synthesize rc={rc}: {detail}")
            return {"notebook_id": nb_id, "title": title, "status": "synthesis_failed",
                    "error": err[:400], "child_receipt": receipt,
                    "transcripts_exported": n_exported}
        concepts = json.loads(concepts_path.read_text(encoding="utf-8"))
        log(f"  synthesized {len(concepts)} concept pages")
        degraded_fallback_count = sum(
            1 for concept in concepts
            if concept.get("synthesis_quality") == "degraded_fallback"
        )
        if degraded_fallback_count:
            if not allow_degraded_fallback:
                log("FATAL degraded synthesis appeared without explicit promotion opt-in")
                return {"notebook_id": nb_id, "title": title,
                        "status": "synthesis_degraded",
                        "error": "degraded fallback requires explicit promotion opt-in",
                        "transcripts_exported": n_exported}
            log(
                f"SYNTHESIS_QUALITY=degraded_fallback "
                f"count={degraded_fallback_count}"
            )
        if not concepts:
            return {"notebook_id": nb_id, "title": title, "status": "no_concepts"}

        # Stage D: reconcile
        log("Stage D: reconcile against existing wiki...")
        rc, out, err = run(
            ["python", str(SCRIPTS / "reconcile.py"),
             "--input", str(concepts_path)], timeout=300)
        if rc != 0:
            log(f"FATAL reconcile rc={rc}: {err[:300]}")
            return {"notebook_id": nb_id, "title": title, "status": "reconcile_failed",
                    "error": err[:400], "transcripts_exported": n_exported}
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
        staging = (
            WIKI_VAULT / "_state" / "nlm-sync-staging"
            / f"{nb_id[:8]}-{uuid.uuid4().hex}"
        )
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
        if rc == 5 or n_failed:
            log("FATAL page validation was incomplete; no manifest or [INGESTED] rename will be written")
            return {"notebook_id": nb_id, "title": title, "status": "partial_write",
                    "written": n_written, "failed_validation": n_failed,
                    "staging": str(staging), "transcripts_exported": n_exported}

        # Stage F: auto-link + log + manifest
        log("Stage F: auto-link + log + manifest...")
        synthesis_quality_counts: dict[str, int] = {}
        for written_page in write_summary["written"]:
            quality = str(written_page.get("synthesis_quality", "llm_validated"))
            synthesis_quality_counts[quality] = synthesis_quality_counts.get(quality, 0) + 1
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
            "synthesis_quality_counts": synthesis_quality_counts,
            "export_receipt": export_receipt,
        }
        save_manifest(manifest)
        # Reindex removed (qmd was uninstalled from the workspace; pages are
        # still written and valid — they'll be indexed by the next indexer wired)

        # Stage G: rename notebook with [INGESTED] prefix for visual tracking
        if not title.startswith("[INGESTED]"):
            log("Stage G: rename notebook with [INGESTED] prefix...")
            new_title = f"[INGESTED] - {title}"
            try:
                rename_notebook(profile, nb_id, new_title, worker_id="wiki-yt-rename")
                log(f"  renamed: {title} → {new_title}")
                manifest["notebooks"][nb_id]["original_title"] = title
                manifest["notebooks"][nb_id]["title"] = new_title
                save_manifest(manifest)
            except Exception as exc:
                log(f"WARN canonical rename failed: {str(exc)[:200]}; continuing")
        else:
            log("Stage G: already prefixed [INGESTED], skipping rename")

        # Stage H: auto-generate pipeline report (progressive disclosure)
        log("Stage H: generate pipeline report...")
        sync_duration = time.time() - sync_start_time if sync_start_time else None
        report_cmd = ["python", str(SCRIPTS / "report.py"),
                      "--notebook", nb_id, "--account-profile", profile]
        if sync_duration:
            report_cmd.extend(["--duration", str(sync_duration)])
        rc, out, _ = run(report_cmd, timeout=120)
        if rc == 0 and out.strip():
            # Print the Level 1 + Level 2 summary to stderr (sync logs go to stderr)
            print(out.strip(), file=sys.stderr)

        sync_status = "synced_degraded_fallback" if degraded_fallback_count else "synced"
        if degraded_fallback_count:
            log("DEGRADED_FALLBACK_PROMOTED=1 pages passed citation and wiki validation")
        return {
            "notebook_id": nb_id, "title": title, "status": sync_status,
            "written": n_written, "failed_validation": n_failed,
            "transcripts_exported": n_exported,
            "export_receipt": export_receipt,
            "synthesis_quality_counts": synthesis_quality_counts,
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
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_and_fsync(tmp, json.dumps(state, ensure_ascii=False, indent=2))
    os.replace(tmp, path)


def _write_and_fsync(path: Path, content: str) -> None:
    """Flush a durable state file before atomically publishing its replacement."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def list_notebooks(profile: str) -> list[dict]:
    """Return the account's notebooks (id, title, source_count)."""
    try:
        return list_nlm_notebooks(profile, worker_id="wiki-yt-list")
    except Exception as exc:
        raise RuntimeError(
            f"canonical notebook list failed for {profile}: "
            f"{type(exc).__name__}: {str(exc)[:300]}"
        ) from exc


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
    try:
        rows = notebook_status(profile, min_sources)
    except RuntimeError as exc:
        log(f"FATAL {exc}")
        return 2
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
    return 5 if run_failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=False)  # no-arg → status picker
    g.add_argument("--notebook")
    g.add_argument("--all", action="store_true")
    g.add_argument("--from-clusters", type=Path, metavar="CLUSTERS_JSON")
    g.add_argument("--status", action="store_true",
                   help="print notebook sync status table and exit (also the default when no target given)")
    ap.add_argument("--profile", "--account-profile", dest="profile", default="a.hominidae",
                    help="exact account identity (a.hominidae, troup.hominidae, or brsthomson)")
    ap.add_argument("--state", type=Path, help="resume-state file for --all / --from-clusters")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-sources", type=int, default=10,
                    help="status filter: skip notebooks with fewer sources (default 10)")
    ap.add_argument("--enrich-vision", action="store_true",
                    help="v3: run crv vision enrichment on high-scene-change videos (opt-in)")
    ap.add_argument("--max-subtopics", type=int, default=10,
                    help="v3: max sub-topic clusters per notebook (default 10)")
    ap.add_argument("--synth-backend", choices=["mmx", "dgemma", "deterministic"], default=None,
                    help="v3: synthesis backend; deterministic preserves cited excerpts without an LLM")
    ap.add_argument("--allow-degraded-fallback", action="store_true",
                    help="explicitly allow citation-backed excerpt pages after backend exhaustion")
    ap.add_argument("--force-resynthesis", action="store_true",
                    help="rerun export/cluster/synthesis even when source IDs are unchanged")
    ap.add_argument("--synth-context-budget", type=int, default=None,
                    help="override synthesis map-reduce threshold in characters")
    ap.add_argument("--synth-checkpoint", type=Path,
                    help="durable per-notebook Stage-C checkpoint to create")
    ap.add_argument("--synth-resume", type=Path,
                    help="durable per-notebook Stage-C checkpoint to resume")
    args = ap.parse_args()

    if (args.synth_checkpoint or args.synth_resume) and not args.notebook:
        ap.error("--synth-checkpoint/--synth-resume require --notebook")

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
        try:
            nbs = list_nlm_notebooks(args.profile, worker_id="wiki-yt-all")
        except Exception as exc:
            log(f"FATAL: canonical notebook list failed: {exc}")
            return 2
        notebooks = [n.get("id") for n in nbs if n.get("id")]

    log(f"=== {len(notebooks)} notebook(s) to sync ===")
    run_failed = 0
    for nb_id in notebooks:
        if nb_id in state.get("synced", []):
            log(f"SKIP (already in state.synced): {nb_id}")
            continue
        result = sync_one(nb_id, args.profile, args.dry_run, args.from_clusters,
                          enrich_vision=args.enrich_vision,
                          max_subtopics=args.max_subtopics,
                          synth_backend=args.synth_backend,
                          allow_degraded_fallback=args.allow_degraded_fallback,
                          force_resynthesis=args.force_resynthesis,
                          synth_context_budget=args.synth_context_budget,
                          synth_checkpoint=args.synth_checkpoint,
                          synth_resume=args.synth_resume)
        state.setdefault("results", []).append(result)
        if result.get("status") in (
            "synced", "synced_degraded_fallback", "skipped_unchanged", "dry_run"
        ):
            state.setdefault("synced", []).append(nb_id)
        else:
            state.setdefault("failed", []).append(nb_id)
            run_failed += 1
        save_state(state, args.state)

    log("=== Pipeline complete ===")
    log(f"Synced: {len(state.get('synced', []))}/{len(notebooks)}")
    if state.get("failed"):
        log(f"Failed: {state['failed']}")
    return 1 if run_failed else 0


if __name__ == "__main__":
    sys.exit(main())
