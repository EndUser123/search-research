"""Telemetry writer for /red-team Phase 3 self-improvement.

Mirror of cc-lazy-closure-debt/__lib/debt_store.py: append+fsync JSONL with a
process-local seq counter for sub-second ordering. One telemetry line per
/red-team run.

State path: P:/.claude/state/red-team/telemetry.jsonl
Override: RED_TEAM_STATE_DIR

CLI:
  python telemetry.py commit --run-dir <p> --session-id <id> --verdict <v> \
      [--dispatched a,b] [--deferred c] [--duration-s N] \
      [--operator-outcome accepted|partial|overridden|unknown]
  python telemetry.py recent [--limit N]

`commit` derives counts/critic_conflicts_resolved/top_categories from
{run_dir}/critic.json defensively: a missing or garbled critic produces a
partial line with a `parse_error` field rather than raising.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from telemetry_schema import VALID_OPERATOR_OUTCOMES, VALID_VERDICTS, validate_telemetry

_seq_lock = threading.Lock()
_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    with _seq_lock:
        _seq_counter += 1
        return _seq_counter


DEFAULT_STATE_ROOT = Path(os.environ.get("RED_TEAM_STATE_DIR", "P:/.claude/state"))
PLUGIN_NAME = "red-team"


def _read_plugin_version() -> str:
    # ponytail: read plugin.json at runtime so telemetry never drifts from manifest.
    manifest = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
    try:
        import json
        return json.loads(manifest.read_text()).get("version", "unknown")
    except Exception:
        return "unknown"


PLUGIN_VERSION = _read_plugin_version()


def get_state_dir(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else DEFAULT_STATE_ROOT
    p = base / PLUGIN_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_telemetry_path(root: Optional[Path] = None) -> Path:
    return get_state_dir(root) / "telemetry.jsonl"


def derive_from_critic(run_dir: Path) -> dict:
    """Read {run_dir}/critic.json and derive counts/conflicts/categories.

    Never raises — returns {"parse_error": "...", "counts": {}, ...} on any
    failure so a missing/broken critic does not abort the telemetry commit.
    """
    out: dict = {"counts": {}, "critic_conflicts_resolved": 0, "top_categories": []}
    critic_path = Path(run_dir) / "critic.json"
    if not critic_path.exists():
        return {**out, "parse_error": "critic.json missing"}
    try:
        with open(critic_path, "r", encoding="utf-8") as f:
            critic = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return {**out, "parse_error": f"critic.json unreadable: {exc}"}
    if not isinstance(critic, dict):
        return {**out, "parse_error": "critic.json not a dict"}

    counts = {"BLOCK": 0, "REVISE": 0, "NIT": 0, "suppressed": 0}
    categories: dict[str, int] = {}
    # Tolerate both field names: the schema says "findings" (findings_schema.py),
    # but critic.json has historically been written with "verified_findings"
    # because the critic prompt's "### Verified findings" heading gets serialized
    # as that key. Accept either; the canonical producer-side schema stays "findings".
    findings = critic.get("findings") or critic.get("verified_findings") or []
    if not isinstance(findings, list):
        findings = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        sev = f.get("severity")
        if sev in counts:
            counts[sev] = counts.get(sev, 0) + 1
        if f.get("verification_status") == "NON_REPRODUCIBLE" or f.get("verdict") == "NON_REPRODUCIBLE":
            counts["suppressed"] += 1
        cat = f.get("category")
        if isinstance(cat, str) and cat:
            categories[cat] = categories.get(cat, 0) + 1
    out["counts"] = counts
    out["critic_conflicts_resolved"] = int(critic.get("conflicts_resolved_count") or 0)
    out["top_categories"] = sorted(categories, key=categories.get, reverse=True)[:5]
    return out


def append_telemetry(line: dict, state_root: Optional[Path] = None) -> None:
    """Validate then append+fsync one telemetry line."""
    errors = validate_telemetry(line)
    if errors:
        raise ValueError("invalid telemetry line: " + "; ".join(errors))
    path = get_telemetry_path(state_root)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def commit(
    run_dir: str,
    session_id: str,
    verdict: str,
    dispatched: Optional[list] = None,
    deferred: Optional[list] = None,
    duration_s: Optional[float] = None,
    operator_outcome: str = "unknown",
    state_root: Optional[Path] = None,
) -> dict:
    """Derive critic-derived fields, merge CLI args, append one telemetry line."""
    derived = derive_from_critic(Path(run_dir))
    now = time.time()
    line = {
        "ts": int(now),
        "ts_ms": int(now * 1000),
        "seq": _next_seq(),
        "session_id": session_id,
        "run_id": Path(run_dir).name,
        "verdict": verdict,
        "operator_outcome": operator_outcome,
        "dispatched": dispatched or [],
        "deferred": deferred or [],
        "counts": derived["counts"],
        "critic_conflicts_resolved": derived["critic_conflicts_resolved"],
        "top_categories": derived["top_categories"],
        "duration_s": duration_s,
        "plugin_version": PLUGIN_VERSION,
    }
    if "parse_error" in derived:
        line["parse_error"] = derived["parse_error"]
    append_telemetry(line, state_root)
    return line


def recent(limit: int = 20, state_root: Optional[Path] = None) -> list[dict]:
    """Return the last `limit` telemetry lines (most recent last)."""
    path = get_telemetry_path(state_root)
    if not path.exists():
        return []
    out: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out[-limit:]


def _comma_list(s: Optional[str]) -> list:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="telemetry.py", description="/red-team telemetry writer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit", help="append one telemetry line")
    p_commit.add_argument("--run-dir", required=True)
    p_commit.add_argument("--session-id", required=True)
    p_commit.add_argument("--verdict", required=True, choices=VALID_VERDICTS)
    p_commit.add_argument("--dispatched", default="")
    p_commit.add_argument("--deferred", default="")
    p_commit.add_argument("--duration-s", type=float, default=None)
    p_commit.add_argument("--operator-outcome", default="unknown", choices=VALID_OPERATOR_OUTCOMES)

    p_recent = sub.add_parser("recent", help="tail telemetry.jsonl")
    p_recent.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)
    if args.cmd == "commit":
        line = commit(
            run_dir=args.run_dir,
            session_id=args.session_id,
            verdict=args.verdict,
            dispatched=_comma_list(args.dispatched),
            deferred=_comma_list(args.deferred),
            duration_s=args.duration_s,
            operator_outcome=args.operator_outcome,
        )
        print(json.dumps(line, ensure_ascii=True))
        return 0
    if args.cmd == "recent":
        for line in recent(limit=args.limit):
            print(json.dumps(line, ensure_ascii=True))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
