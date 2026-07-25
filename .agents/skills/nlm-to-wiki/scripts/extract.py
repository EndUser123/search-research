#!/usr/bin/env python3
"""extract.py — Stage A: trigger Report + Data-Table artifacts on a notebook.

Generates two Studio artifacts in parallel-ish sequence (sequential to avoid
rate limits):
  - Report: "Create Your Own" format with concept-extraction prompt
  - Data-Table: tabular facts (concept name, definition, key values, source IDs)

Polls studio_status until both complete, then downloads both to local paths.
Returns the artifact IDs and local file paths as JSON on stdout.

Usage:
  python extract.py --notebook <uuid> --profile codex \\
      --out-dir <staging-dir>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Prompt templates kept in references/extraction-prompts.md; inlined here for
# the CLI default so extract.py is self-contained.
REPORT_PROMPT = """For each major concept in this notebook's sources, extract:
1. Concept name (concise, 2-6 words)
2. Definition (1-3 sentences — what it IS, grounded only in the sources)
3. Operational details (thresholds, parameters, mechanisms, named components)
4. Relationships to other concepts in the notebook (named explicitly)
5. Verifiable values (numbers, defaults, ratios, version numbers)
6. Source citations (cite the specific source for each claim)

Format as Markdown with ## for each concept. Aim for 5-20 major concepts.
A major concept is a distinct topic, technique, tool, or architectural pattern.
Ignore minor mentions, tangents, and generic background.

Grounding constraint: use ONLY uploaded sources. Do not invent statistics,
quotes, or examples not in the sources. If a concept has no direct support,
omit it."""

DATA_TABLE_DESC = """Extract a row per concept with columns:
- concept_name (short)
- definition (1 sentence)
- key_values (semicolon-separated thresholds/numbers/defaults)
- related_concepts (semicolon-separated names from this notebook)
- primary_source_id (the source UUID that most directly supports this concept)
- supporting_quote (one short verbatim quote from that source)"""


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True, file=sys.stderr)


def studio_create(notebook_id: str, artifact: str, profile: str,
                   fmt: str | None, prompt: str | None,
                   desc: str | None) -> str | None:
    """Create artifact, return its ID."""
    cmd = ["nlm", "studio", "create", artifact, notebook_id, "--profile", profile, "--confirm", "--json"]
    if fmt:
        cmd.extend(["--format", fmt])
    if prompt:
        cmd.extend(["--prompt", prompt])
    if desc:
        cmd.extend(["--description", desc])
    rc, out, err = run(cmd, timeout=120)
    if rc != 0:
        log(f"  {artifact} create failed rc={rc}: {(err or out).strip()[:300]}")
        return None
    try:
        data = json.loads(out)
        # Status may be different keys depending on nlm version
        return data.get("artifact_id") or data.get("id")
    except json.JSONDecodeError:
        log(f"  {artifact} create output not JSON: {out.strip()[:200]}")
        return None


def poll_status(notebook_id: str, artifact_id: str, profile: str,
                 max_wait: int = 1200, interval: int = 30) -> str:
    """Poll studio status until artifact completes or fails. Returns final status."""
    deadline = time.time() + max_wait
    last = "unknown"
    while time.time() < deadline:
        rc, out, _ = run(["nlm", "studio", "status", notebook_id, "--profile", profile, "--json"], timeout=60)
        if rc != 0:
            time.sleep(interval)
            continue
        try:
            data = json.loads(out)
            artifacts = data.get("artifacts", []) if isinstance(data, dict) else data
            for art in artifacts:
                if art.get("id") == artifact_id or art.get("artifact_id") == artifact_id:
                    last = art.get("status", "unknown")
                    if last in ("completed", "COMPLETED", "done", "ready"):
                        return "completed"
                    if last in ("failed", "error", "FAILED"):
                        log(f"  artifact {artifact_id} FAILED")
                        return "failed"
                    break
        except json.JSONDecodeError:
            pass
        log(f"  status: {last}; sleeping {interval}s")
        time.sleep(interval)
    return last or "timeout"


def download_artifact(notebook_id: str, artifact_id: str, artifact_kind: str,
                       profile: str, out_path: Path) -> bool:
    """Download artifact to out_path. artifact_kind: report | data-table."""
    rc, out, err = run(
        ["nlm", "download", artifact_kind, notebook_id,
         "--profile", profile, "--output", str(out_path)],
        timeout=300)
    if rc != 0:
        log(f"  download {artifact_kind} failed: {(err or out).strip()[:200]}")
        return False
    return out_path.exists()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--profile", default="codex")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--max-wait", type=int, default=1200, help="Max seconds per artifact")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Kick off Report
    log("Creating Report artifact...")
    report_id = studio_create(
        args.notebook, "report", args.profile,
        fmt="Create Your Own", prompt=REPORT_PROMPT, desc=None)
    if not report_id:
        return 2
    log(f"  report artifact: {report_id}")

    # 2. Kick off Data-Table
    log("Creating Data-Table artifact...")
    dt_id = studio_create(
        args.notebook, "data-table", args.profile,
        fmt=None, prompt=None, desc=DATA_TABLE_DESC)
    if not dt_id:
        log("  data-table create failed; continuing with report only")
    else:
        log(f"  data-table artifact: {dt_id}")

    # 3. Poll each in turn (sequential to avoid rate-limit pressure)
    log("Polling report status...")
    report_status = poll_status(args.notebook, report_id, args.profile, max_wait=args.max_wait)
    log(f"  report: {report_status}")

    dt_status = "skipped"
    if dt_id:
        log("Polling data-table status...")
        dt_status = poll_status(args.notebook, dt_id, args.profile, max_wait=args.max_wait)
        log(f"  data-table: {dt_status}")

    if report_status != "completed":
        log(f"FATAL: report did not complete (status={report_status})")
        return 3

    # 4. Download both
    report_path = args.out_dir / "concepts-report.md"
    ok_report = download_artifact(args.notebook, report_id, "report", args.profile, report_path)
    if not ok_report:
        log(f"FATAL: could not download report to {report_path}")
        return 4

    dt_path = None
    if dt_id and dt_status == "completed":
        dt_path = args.out_dir / "facts.csv"
        if not download_artifact(args.notebook, dt_id, "data-table", args.profile, dt_path):
            dt_path = None

    result = {
        "notebook_id": args.notebook,
        "report": {"artifact_id": report_id, "status": report_status, "path": str(report_path)},
        "data_table": {"artifact_id": dt_id, "status": dt_status,
                       "path": str(dt_path) if dt_path else None},
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
