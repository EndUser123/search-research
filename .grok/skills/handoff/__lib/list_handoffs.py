"""`/handoff list` CLI: survey all handoffs under a directory.

For each `<topic>-<YYYYMMDD>/HANDOFF.md` found, print one row showing:
- topic-date (from directory name)
- yaml status (chain header `status`)
- work status (first line of the body `## Status` section)
- mismatch flag (when work is terminal but file is still open)
- relative produced_at ("just now", "12m", "3h", "2d")
- terminal short form
- objective first line (truncated)

Rows are sorted newest-first by produced_at. Files missing produced_at sink
to the bottom and are flagged `no-ts`.

This exists because opening every handoff to triage status does not scale.
A single run surfaces: which are recent, which are done-but-not-closed,
which are stale, and which were written by another terminal recently
(likely in-flight — do not open).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow execution as `python list_handoffs.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validators import parse_frontmatter, extract_section_body  # noqa: E402

DEFAULT_ROOT = Path("P:/docs/handoffs")

# Work-status values that mean the work is finished. If the file (chain header)
# is still `status: open` but the body work-status is one of these, the
# handoff should have been closed — flag it.
TERMINAL_WORK_STATUSES = {"closed", "wontfix", "won't fix", "wont-fix"}


def _short_terminal(tid: str) -> str:
    """Short form for a terminal_id. Prefer the prefix before first underscore
    (e.g. `console_fb11bbd2...` -> `console`); fall back to first 8 chars."""
    if not tid:
        return "?"
    if "_" in tid:
        return tid.split("_", 1)[0]
    return tid[:8]


def _relative_time(produced_at: str, now: datetime | None = None) -> str:
    """Human relative time. Returns '?' on parse failure.

    Tolerates small negative deltas (handoffs written with timezone drift that
    places `produced_at` slightly in the future relative to the host clock) by
    clamping to 0 — the practical reading is "very fresh", not "invalid".
    Deltas more than 48h in the future are treated as parse failures.
    """
    if not produced_at:
        return "?"
    ts = _parse_iso(produced_at)
    if ts is None:
        return "?"
    now = now or datetime.now(timezone.utc)
    delta = now - ts
    secs = int(delta.total_seconds())
    if secs < -48 * 3600:
        # More than 48h in the future — likely a corrupt timestamp.
        return "?"
    if secs < 0:
        secs = 0
    if secs < 60:
        return "just now"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    if hours < 48:
        return f"{hours}h"
    days = hours // 24
    if days < 14:
        return f"{days}d"
    weeks = days // 7
    if weeks < 8:
        return f"{weeks}w"
    months = days // 30
    if months < 18:
        return f"{months}mo"
    years = days // 365
    return f"{years}y"


def _parse_iso(ts: str) -> datetime | None:
    """Parse an ISO 8601 timestamp tolerantly. Returns None on failure."""
    s = ts.strip().rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _first_nonempty_line(text: str) -> str:
    """First non-empty, non-markup line of a section body. Strips leading
    markdown bullets, bold markers, and `**Label:** value` prefixes so a body
    line like `**Status:** OPEN` returns `OPEN`. Requires the colon — a line
    like `**READY_FOR_REVIEW** — explanation` is NOT a label:value form and
    must be preserved for the status-keyword extractor to find the keyword.
    """
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Strip leading list markers.
        line = re.sub(r"^[-*]\s+", "", line)
        # Strip a `**Label:**` prefix only when the colon is present
        # (e.g. "**Status:** OPEN" -> "OPEN"). Without the colon, `**X**` is
        # the value, not a label.
        m = re.match(r"^\*\*[^*]+:\*\*\s*(.*)$", line)
        if m:
            line = m.group(1).strip()
        # Strip bold wrapping that spans the whole line (`**X**` -> `X`).
        line = re.sub(r"^\*\*(.+?)\*\*$", r"\1", line)
        if line:
            return line
    return ""


# Recognized work-status keywords. The body `## Status` section conventionally
# opens with one of these (optionally bolded, optionally followed by " — "
# and an explanation). We surface just the keyword in the list view.
WORK_STATUS_KEYWORDS = (
    "READY_FOR_REVIEW",
    "BLOCKED",
    "CLOSED",
    "WONTFIX",
    "OPEN",
)


def _extract_status_keyword(section_body: str) -> str:
    """Pull just the leading status keyword from a `## Status` body.

    Handles forms observed in the corpus:
    - `**READY_FOR_REVIEW** — design complete...`
    - `READY_FOR_REVIEW — design complete...`
    - `OPEN`
    - `**OPEN** — pattern identified...`

    Returns the uppercased keyword, or '' if no recognized keyword leads.
    """
    first = _first_nonempty_line(section_body)
    if not first:
        return ""
    # Split on em-dash, en-dash, or " - " to drop any trailing explanation.
    for sep in ("\u2014", "\u2013", " - ", " — "):
        if sep in first:
            first = first.split(sep, 1)[0]
            break
    first = first.strip().strip("*").strip()
    upper = first.upper().replace(" ", "_").replace("-", "_").replace("'", "_")
    # Accept exact keyword matches only; arbitrary text falls through.
    if upper in WORK_STATUS_KEYWORDS:
        return upper
    # Also accept WONTFIX variants.
    if upper in {"WONT_FIX", "WON_T_FIX"}:
        return "WONTFIX"
    return ""


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def survey(root: Path, now: datetime | None = None,
           current_head: str | None = None) -> list[dict]:
    """Return one dict per HANDOFF.md found under `root/<topic>/HANDOFF.md`.

    Dict keys: dir_name, yaml_status, work_status, mismatch, relative_time,
    terminal_short, objective, produced_at_raw, head_status, assigned_to,
    claim_consistent, error (optional).

    `current_head` — if provided, compare each handoff's `accurate_as_of_head`
    against it. Resulting `head_status`: 'ok' (match), 'drift' (differ),
    '?' (handoff has no `accurate_as_of_head`, e.g. pre-v0.1.1 schema).
    If `current_head` is None, head_status is None (check skipped).
180→    """
    rows: list[dict] = []
    if not root.exists():
        return rows
    for handoff_path in sorted(root.glob("*/HANDOFF.md")):
        dir_name = handoff_path.parent.name
        try:
            text = handoff_path.read_text(encoding="utf-8")
        except OSError as exc:
            rows.append({
                "dir_name": dir_name,
                "yaml_status": "?",
                "work_status": "?",
                "mismatch": False,
                "relative_time": "?",
                "terminal_short": "?",
                "objective": "",
                "produced_at_raw": "",
                "head_status": None,
                "assigned_to": "",
                "claim_consistent": True,
                "error": f"read_failed:{exc.__class__.__name__}",
            })
            continue

        fm, body = parse_frontmatter(text)
        yaml_status = (fm.get("status") or "?").strip().lower()
        produced_at_raw = (fm.get("produced_at") or "").strip()
        terminal_id = (fm.get("current_terminal_id") or "").strip()
        assigned_to = (fm.get("assigned_to") or "").strip()
        assigned_at = (fm.get("assigned_at") or "").strip()
        assigned_by = (fm.get("assigned_by") or "").strip()
        accurate_head = (fm.get("accurate_as_of_head") or "").strip()

        status_section = extract_section_body(body, "Status")
        work_status_raw = _extract_status_keyword(status_section)
        work_status_norm = work_status_raw.strip().lower().rstrip(".!")

        # Narrow mismatch: work is terminal but file still open.
        is_terminal_work = work_status_norm in TERMINAL_WORK_STATUSES
        mismatch = yaml_status == "open" and is_terminal_work

        # Objective: try "Objective" first; some handoffs use "Goal" instead.
        objective_section = extract_section_body(body, "Objective")
        if not objective_section.strip():
            objective_section = extract_section_body(body, "Goal")
        objective = _first_nonempty_line(objective_section)

        # HEAD drift: only meaningful when the caller passes current_head.
        # Compare on the short-sha prefix (first 12 chars) to tolerate
        # full-vs-short forms.
        head_status: str | None = None
        if current_head is not None:
            if not accurate_head:
                head_status = "?"  # pre-v0.1.1 schema or missing field
            elif accurate_head[:12] == current_head[:12]:
                head_status = "ok"
            else:
                head_status = "drift"

        # Claim consistency: matches the validator's rule. If `assigned_to`
        # is set, `assigned_at` and `assigned_by` should also be present.
        # When inconsistent, hide the claim marker (don't surface a claim
        # the validator would warn about).
        claim_consistent = True
        if assigned_to:
            if not assigned_at or not assigned_by:
                claim_consistent = False

        rows.append({
            "dir_name": dir_name,
            "yaml_status": yaml_status or "?",
            "work_status": work_status_raw or "?",
            "mismatch": mismatch,
            "relative_time": _relative_time(produced_at_raw, now),
            "terminal_short": _short_terminal(terminal_id),
            "objective": objective,
            "produced_at_raw": produced_at_raw,
            "head_status": head_status,
            "assigned_to": assigned_to,
            "claim_consistent": claim_consistent,
        })

    # Sort: rows with a parseable timestamp newest-first; unparseable sink.
    now = now or datetime.now(timezone.utc)

    def sort_key(row: dict) -> tuple[int, float]:
        ts = _parse_iso(row.get("produced_at_raw", ""))
        if ts is None:
            return (1, 0.0)
        return (0, -(ts - now).total_seconds())

    rows.sort(key=sort_key)
    return rows


def _format_row(row: dict, width_topic: int, width_terminal: int,
                head_active: bool) -> str:
    """Format one row for terminal output.

    `head_active` — whether HEAD-drift checking is enabled (caller passed
    current_head). When False, the head column is omitted from the row.
    """
    topic = row["dir_name"].ljust(width_topic)
    yaml_s = row["yaml_status"]
    work_s = row["work_status"]
    flag = " MISMATCH" if row["mismatch"] else ""
    claim_field = row.get("assigned_to", "")
    claim_consistent = row.get("claim_consistent", True)
    # Hide the claim marker when fields are inconsistent (matches validator).
    claim = f" claimed:{claim_field}" if (claim_field and claim_consistent) else ""
    head_part = ""
    if head_active:
        hs = row.get("head_status")
        if hs == "drift":
            head_part = " head:DRIFT"
        elif hs == "ok":
            head_part = ""  # don't clutter; ok is the default expectation
        elif hs == "?":
            head_part = " head:?"
        # hs is None only when head_active was False — handled above.
    rel = row["relative_time"].rjust(8)
    term = row["terminal_short"].ljust(width_terminal)
    obj = _truncate(row["objective"] or "(no objective)", 70)
    return f"{topic}  yaml:{yaml_s:<8} work:{work_s:<20}{flag}{claim}{head_part}  {rel}  {term}  {obj}"


def main(argv: list[str]) -> int:
    """CLI entry.

    Usage:
        python list_handoffs.py [handoffs_root] [--head <git-sha>]

    `--head <sha>` — enable HEAD-drift detection. Compares each handoff's
    `accurate_as_of_head` against `<sha>` and surfaces 'drift' / 'ok' / '?'
    per row. Omit to skip the check.
    """
    args = argv[1:]
    # Strict arg-count check: at most 1 positional (root) + 2 for --head + sha.
    if len(args) > 3:
        print("usage: python list_handoffs.py [handoffs_root] [--head <sha>]",
              file=sys.stderr)
        return 2

    root = DEFAULT_ROOT
    current_head: str | None = None
    positionals: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--head":
            if i + 1 >= len(args):
                print("error: --head requires a sha argument", file=sys.stderr)
                return 2
            current_head = args[i + 1]
            i += 2
        else:
            positionals.append(args[i])
            i += 1

    if len(positionals) > 1:
        print("usage: python list_handoffs.py [handoffs_root] [--head <sha>]",
              file=sys.stderr)
        return 2
    if positionals:
        root = Path(positionals[0])

    if not root.exists():
        print(f"error: handoffs root not found: {root}", file=sys.stderr)
        return 2

    rows = survey(root, current_head=current_head)
    if not rows:
        print(f"(no handoffs under {root})")
        return 0

    width_topic = max(len(r["dir_name"]) for r in rows)
    width_topic = max(width_topic, len("<topic>-<date>"))
    width_terminal = max(len(r["terminal_short"]) for r in rows)
    width_terminal = max(width_terminal, len("terminal"))

    head_active = current_head is not None

    # Header
    print(
        f"{'<topic>-<date>'.ljust(width_topic)}  "
        f"{'yaml':<13}{'work':<22}{'':<9}{'produced':>8}  "
        f"{'terminal'.ljust(width_terminal)}  objective"
    )
    print("-" * 120)
    for row in rows:
        print(_format_row(row, width_topic, width_terminal, head_active))
        if "error" in row:
            print(f"    error: {row['error']}")

    # Summary
    total = len(rows)
    open_count = sum(1 for r in rows if r["yaml_status"] == "open")
    closed_count = sum(1 for r in rows if r["yaml_status"] in {"closed", "superseded"})
    mismatch_count = sum(1 for r in rows if r["mismatch"])
    recent_count = sum(1 for r in rows if r["relative_time"] in {"just now"} or r["relative_time"].endswith("m"))
    drift_count = sum(1 for r in rows if r.get("head_status") == "drift")
    no_head_count = sum(1 for r in rows if r.get("head_status") == "?")
    print()
    parts = [f"{total} handoffs: {open_count} open, {closed_count} closed/superseded, "
             f"{mismatch_count} mismatch, {recent_count} fresh (<1h)"]
    if head_active:
        parts.append(f"{drift_count} HEAD-drift, {no_head_count} no-head-field")
    print("  ".join(parts))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
