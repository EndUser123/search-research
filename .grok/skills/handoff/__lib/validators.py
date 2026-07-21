"""Handoff structural validators.

These functions check that a handoff file conforms to the v0.1 contract
before it is reported as "written." The model invokes them after writing
to verify its own output. They are deliberately pure functions so they
can be tested without filesystem state.

Validators return a list of issues (empty list = passed). Each issue is a
dict with:
    {"field": <name>, "severity": "error"|"warn", "message": <text>}

Errors block "handoff written" claims. Warnings are surfaced but do not block.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Constants — the v0.1 contract
# ---------------------------------------------------------------------------

# Mandatory chain-header fields. All must be present and non-empty.
HEADER_REQUIRED = (
    "thread_id",
    "parent_handoff_path",  # may be "none"
    "current_session_id",
    "current_terminal_id",
    "produced_at",
    "status",
    "handoff_type",
    "accurate_as_of_head",  # git HEAD sha at production time (from summary.json.head_commit)
)

# Optional assignment/lock fields (v0.1.1). Not required, but if assigned_to
# is present, the others should be too (checked by validate_assignment_fields).
HEADER_ASSIGNMENT_FIELDS = ("assigned_to", "assigned_at", "assigned_by")

HEADER_STATUS_ALLOWED = {"open", "closed", "superseded"}
HEADER_TYPE_ALLOWED_V01 = {"investigation"}

# Mandatory body sections (markdown headings). Each must appear as a heading.
# Matched case-insensitively against the heading text after the last "## ".
BODY_REQUIRED_SECTIONS = (
    "objective",
    "status",
    "producing context",
    "read-first list",
    "verified facts",
    "current state",
    "task packets",
    "open decisions",
    "hard constraints",
    "cross-reference couplings",
    "explicit non-goals",
    "resumption protocol",
    "suggested next invocation",
    "last user message (verbatim)",
    "epistemic labels",
)

# "Other outstanding streams" is optional but, when present, must follow the
# documented format (at least one bullet naming a stream and its status).
OPTIONAL_STREAMS_SECTION = "other outstanding streams"

# Mandatory task-packet sub-fields (each task packet must carry all of these).
TASK_PACKET_REQUIRED = (
    "id",
    "goal",
    "in scope",
    "out of scope",
    "files / anchors",
    "acceptance",
    "falsifier",
    "verification level required",
)

VERIFICATION_LEVEL_ALLOWED = {
    "STATIC_INSPECTION",
    "UNIT_TEST",
    "LIVE_BEHAVIOR",
}

# Keywords that signal a task is a bulk/batch/scale operation. When present
# in a task packet's goal or in-scope, the falsifier-strength validator
# applies a stricter check (must mention a rate/threshold, not just "0 output").
_BULK_KEYWORDS = frozenset(
    w.lower() for w in (
        "fetch", "batch", "bulk", "backlog", "scale", "migrate", "import",
        "export", "process", "production", "thousand", "million",
        "videos", "records", "rows", "items", "files", "all pending",
    )
)

# Indicators that a falsifier mentions a rate/success-threshold (not just
# catastrophic-zero detection).
_RATE_INDICATORS = frozenset(
    w.lower() for w in (
        "%", "percent", "rate", "ratio", "threshold", "success rate",
        ">=", "<=", "> ", "< ", "at least", "no more than", "fewer than",
    )
)

# Keywords that indicate the handoff author has explicitly labeled scope
# bounds (subset vs total). Suppresses the scope-discrepancy warning.
_SCOPE_LABEL_KEYWORDS = frozenset(
    w.lower() for w in (
        "scope bound", "scope:", "work scope", "subset", "of these",
        "of which", "out of", "deferred", "remaining", "total backlog",
        "in scope",
    )
)

# UUID shape (Grok session ids and our thread_ids are UUID-ish).
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# ISO 8601 timestamp (loose: accepts with/without timezone, with Z or offset).
_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a markdown file into (frontmatter dict, body).

    Frontmatter is YAML between `---` fences at the top of the file. We only
    parse the simple `key: value` form the handoff contract uses; we do not
    embed a YAML library. Quoted values have their quotes stripped.
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_block = parts[1]
    body = parts[2].lstrip("\n")
    fm: dict[str, str] = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        fm[key] = value
    return fm, body


def extract_headings(body: str) -> list[str]:
    """Return all markdown heading texts (## Foo -> 'foo'), lowercased.

    Only level-2 headings are returned (the contract uses ## for sections).

    Strips a leading numbered prefix (e.g. '## 1. Objective' -> 'objective')
    so authors who number their sections still validate cleanly. The prefix
    must be `\\d+\\.\\s+` immediately after '## ' to be stripped.
    """
    numbered_prefix_re = re.compile(r"^\d+\.\s+")
    headings: list[str] = []
    for line in body.splitlines():
        s = line.lstrip()
        if s.startswith("## ") and not s.startswith("### "):
            heading = s[3:].strip()
            heading = numbered_prefix_re.sub("", heading, count=1)
            headings.append(heading.lower())
    return headings


def extract_section_body(body: str, section_name: str) -> str:
    """Return the text under a `## <section_name>` heading (case-insensitive,
    leading numbered prefix tolerated), up to the next `## ` heading.

    Returns '' if the section is absent. Used by tools that need to surface a
    specific body field (e.g. `/handoff list` reads the Status section's first
    line). Heading matching mirrors `extract_headings`: lowercased and
    number-prefix-stripped.
    """
    numbered_prefix_re = re.compile(r"^\d+\.\s+")
    target = section_name.lower()
    in_section = False
    lines: list[str] = []
    for line in body.splitlines():
        s = line.lstrip()
        if s.startswith("## ") and not s.startswith("### "):
            heading = s[3:].strip()
            heading = numbered_prefix_re.sub("", heading, count=1).lower()
            if heading == target:
                in_section = True
                continue
            if in_section:
                break  # next ## section ends this one
            continue
        if in_section:
            lines.append(line)
    return "\n".join(lines)


def extract_task_packets(body: str) -> list[dict[str, str]]:
    """Extract task packets as a list of field-dicts.

    Task packets are markdown blocks following a '## Task packets' heading.
    Each packet is introduced by a sub-heading (### <id>: <goal>) and
    contains `- key: value` lines until the next sub-heading or section.

    This is a forgiving parser — it captures fields it recognizes and
    ignores the rest. The validators then check for missing required fields.
    """
    packets: list[dict[str, str]] = []
    in_section = False
    current: dict[str, str] | None = None

    for line in body.splitlines():
        s = line.lstrip()
        if s.startswith("## "):
            heading = s[3:].strip().lower()
            in_section = heading == "task packets"
            if not in_section and current is not None:
                packets.append(current)
                current = None
            continue
        if not in_section:
            continue
        if s.startswith("### "):
            if current is not None:
                packets.append(current)
            current = {}
            # Try to pull an id from the heading: "### AC-CONTAIN-01: goal text"
            heading_text = s[4:].strip()
            if ":" in heading_text:
                packet_id, _, goal = heading_text.partition(":")
                current["id"] = packet_id.strip()
                current["goal"] = goal.strip()
            else:
                current["id"] = heading_text
            continue
        if current is None:
            continue
        # Capture "- key: value" lines
        m = re.match(r"^[-*]\s+([^:]+):\s*(.*)$", s)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            current[key] = value
    if current is not None:
        packets.append(current)
    return packets


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def validate_header(fm: dict[str, str]) -> list[dict[str, str]]:
    """Validate the chain header. Returns a list of issues."""
    issues: list[dict[str, str]] = []

    # Required fields present and non-empty.
    for field in HEADER_REQUIRED:
        if field not in fm:
            issues.append({
                "field": field,
                "severity": "error",
                "message": f"missing required header field: {field}",
            })
        elif not fm[field].strip():
            issues.append({
                "field": field,
                "severity": "error",
                "message": f"empty header field: {field}",
            })

    # thread_id must be UUID-shaped.
    tid = fm.get("thread_id", "").strip()
    if tid and not _UUID_RE.match(tid):
        issues.append({
            "field": "thread_id",
            "severity": "error",
            "message": f"thread_id is not UUID-shaped: {tid!r}",
        })

    # current_session_id must be UUID-shaped.
    sid = fm.get("current_session_id", "").strip()
    if sid and not _UUID_RE.match(sid):
        issues.append({
            "field": "current_session_id",
            "severity": "error",
            "message": f"current_session_id is not UUID-shaped: {sid!r}",
        })

    # parent_handoff_path: "none" or an absolute Windows/POSIX path that exists.
    # We do not check existence here (the validator is pure); path existence
    # is checked by validate_paths_exist() which needs filesystem access.
    ppath = fm.get("parent_handoff_path", "").strip()
    if ppath and ppath.lower() != "none":
        # Must look like an absolute path (drive letter or leading slash).
        if not (re.match(r"^[A-Za-z]:[\\/]", ppath) or ppath.startswith("/")):
            issues.append({
                "field": "parent_handoff_path",
                "severity": "error",
                "message": f"parent_handoff_path is neither 'none' nor an absolute path: {ppath!r}",
            })

    # produced_at: ISO 8601.
    ts = fm.get("produced_at", "").strip()
    if ts and not _ISO8601_RE.match(ts):
        issues.append({
            "field": "produced_at",
            "severity": "error",
            "message": f"produced_at is not ISO 8601: {ts!r}",
        })

    # status: must be in allowed set.
    status = fm.get("status", "").strip().lower()
    if status and status not in HEADER_STATUS_ALLOWED:
        issues.append({
            "field": "status",
            "severity": "error",
            "message": f"status must be one of {sorted(HEADER_STATUS_ALLOWED)}, got: {status!r}",
        })

    # handoff_type: v0.1 allows only "investigation".
    htype = fm.get("handoff_type", "").strip().lower()
    if htype and htype not in HEADER_TYPE_ALLOWED_V01:
        issues.append({
            "field": "handoff_type",
            "severity": "error",
            "message": (
                f"handoff_type must be one of {sorted(HEADER_TYPE_ALLOWED_V01)} "
                f"in v0.1; got: {htype!r}"
            ),
        })

    return issues


def validate_body_sections(headings: list[str]) -> list[dict[str, str]]:
    """Validate that all mandatory body sections are present.

    Matching is prefix-based: a heading matches a required section if the
    heading starts with the section name followed by a word boundary
    (space, paren, colon, or end-of-string). This allows descriptive
    headings like ``## 1. Objective (one sentence)`` or
    ``## 5. Verified facts (with source paths)`` to match the required
    sections ``objective`` and ``verified facts`` respectively.
    """
    issues: list[dict[str, str]] = []
    for section in BODY_REQUIRED_SECTIONS:
        found = any(
            h == section
            or h.startswith(section + " ")
            or h.startswith(section + "(")
            or h.startswith(section + ":")
            for h in headings
        )
        if not found:
            issues.append({
                "field": section,
                "severity": "error",
                "message": f"missing mandatory body section: '## {section.title()}'",
            })
    return issues


def validate_task_packets(packets: list[dict[str, str]]) -> list[dict[str, str]]:
    """Validate each task packet has all required sub-fields."""
    issues: list[dict[str, str]] = []
    for i, pkt in enumerate(packets):
        pkt_id = pkt.get("id", f"<packet {i+1}>")
        for field in TASK_PACKET_REQUIRED:
            if field not in pkt:
                issues.append({
                    "field": f"task_packets.{pkt_id}.{field}",
                    "severity": "error",
                    "message": f"task packet {pkt_id!r} missing required field: {field}",
                })
        # verification level must be in allowed set if present
        vl = pkt.get("verification level required", "").strip().upper()
        if vl and vl not in VERIFICATION_LEVEL_ALLOWED:
            issues.append({
                "field": f"task_packets.{pkt_id}.verification_level_required",
                "severity": "error",
                "message": (
                    f"verification level must be one of "
                    f"{sorted(VERIFICATION_LEVEL_ALLOWED)}, got: {vl!r}"
                ),
            })
        # falsifier must be non-trivial (not just "n/a" or empty)
        falsifier = pkt.get("falsifier", "").strip().lower()
        if falsifier in ("n/a", "none", "—", "-"):
            issues.append({
                "field": f"task_packets.{pkt_id}.falsifier",
                "severity": "warn",
                "message": (
                    f"task packet {pkt_id!r} has trivial falsifier; "
                    "falsifier should describe what would prove the task failed"
                ),
            })
    return issues


def validate_verbatim_message(body: str) -> list[dict[str, str]]:
    """Validate the 'Last user message (verbatim)' section has actual quoted text.

    Mutation guard: a summarizer that paraphrases the user message will
    fail this check. The section must contain a blockquote (`>`) with
    non-trivial content.

    If the section is absent, this validator returns no issues — the
    mandatory-section check elsewhere catches the missing section, and
    double-reporting would be noise.
    """
    issues: list[dict[str, str]] = []
    lines = body.splitlines()
    in_section = False
    section_seen = False
    found_quote = False
    quote_text = ""
    for line in lines:
        s = line.lstrip()
        if s.startswith("## "):
            heading = s[3:].strip().lower()
            in_section = heading == "last user message (verbatim)"
            if in_section:
                section_seen = True
            continue
        if not in_section:
            continue
        if s.startswith(">"):
            quote = s[1:].strip()
            # Strip surrounding quotes if present.
            if len(quote) >= 2 and quote[0] == quote[-1] and quote[0] in ("'", '"'):
                quote = quote[1:-1]
            if quote:
                found_quote = True
                quote_text = quote
    if not section_seen:
        # Section absent — let the mandatory-section check handle it.
        return []
    if not found_quote:
        issues.append({
            "field": "last_user_message_verbatim",
            "severity": "error",
            "message": (
                "'Last user message (verbatim)' section must contain a "
                "blockquote (>) with the actual user text"
            ),
        })
    elif len(quote_text) < 5:
        issues.append({
            "field": "last_user_message_verbatim",
            "severity": "warn",
            "message": (
                f"verbatim user message is suspiciously short ({len(quote_text)} chars): "
                f"{quote_text!r}"
            ),
        })
    return issues


def validate_streams_section_format(body: str) -> list[dict[str, str]]:
    """If 'Other outstanding streams' section is present, validate its format.

    Each entry must be a bullet with a stream name and an Open/Closed marker.
    Prevents the section from becoming a dumping ground of vague notes.
    """
    issues: list[dict[str, str]] = []
    lines = body.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        s = line.lstrip()
        if s.startswith("## "):
            heading = s[3:].strip().lower()
            if in_section:
                break  # next section starts
            in_section = heading == OPTIONAL_STREAMS_SECTION
            continue
        if in_section:
            section_lines.append(line)
    if not in_section:
        return []  # section absent is valid

    # Must have at least one bullet that names a stream and includes a status.
    bullets = [ln.strip() for ln in section_lines if ln.strip().startswith(("- ", "* "))]
    if not bullets:
        issues.append({
            "field": "other_outstanding_streams",
            "severity": "warn",
            "message": (
                "'Other outstanding streams' section is present but has no bullets; "
                "either document the streams or remove the section"
            ),
        })
    for b in bullets:
        if "open" not in b.lower() and "closed" not in b.lower():
            issues.append({
                "field": "other_outstanding_streams",
                "severity": "warn",
                "message": (
                    f"stream bullet lacks Open/Closed marker: {b!r}; "
                    "each stream should say whether it is open or closed"
                ),
            })
    return issues


def _extract_section(body: str, section_name: str) -> str:
    """Extract the text content of a ## section by name (case-insensitive).

    Returns the lines between the heading and the next ## heading (or EOF).
    Strips the numbered prefix from the heading before matching, consistent
    with extract_headings().
    """
    numbered_prefix_re = re.compile(r"^\d+\.\s+")
    lines = body.splitlines()
    in_section = False
    section_lines: list[str] = []
    target = section_name.lower()
    for line in lines:
        s = line.lstrip()
        if s.startswith("## ") and not s.startswith("### "):
            heading = s[3:].strip()
            heading = numbered_prefix_re.sub("", heading, count=1).lower()
            if in_section:
                break  # next section starts
            in_section = heading == target
            continue
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines)


def _extract_integers(text: str) -> set[int]:
    """Extract integer values from text, handling comma-separated thousands.

    E.g., '7,000' -> 7000, '51337' -> 51337. Filters out years (1800-2099)
    and very small numbers (<10) that are likely not scope quantities.
    """
    numbers: set[int] = set()
    # Match plain integers or comma-grouped integers (e.g., 51,337).
    for m in re.finditer(r"\b(\d{1,3}(?:,\d{3})+|\d{3,})\b", text):
        raw = m.group(1).replace(",", "")
        try:
            n = int(raw)
        except ValueError:
            continue
        # Filter out likely-years and trivially small numbers.
        if n < 100:
            continue
        if 1800 <= n <= 2099:
            continue
        numbers.add(n)
    return numbers


def validate_assignment_fields(fm: dict[str, str]) -> list[dict[str, str]]:
    """Validate optional assignment/lock fields for internal consistency.

    If ``assigned_to`` is present, ``assigned_at`` and ``assigned_by`` should
    also be present so fleet coordination has a timestamp and provenance.
    All three are optional — this validator only fires when one or more are
    set.

    Introduced in v0.1.1 after the fleet-coordination incident (2026-07-20):
    a handoff was claimed verbally but the claim was not recorded in the file,
    so another host started the same work. The assignment fields make claims
    machine-readable for ``/handoff list``.
    """
    issues: list[dict[str, str]] = []
    assigned_to = fm.get("assigned_to", "").strip()
    assigned_at = fm.get("assigned_at", "").strip()
    assigned_by = fm.get("assigned_by", "").strip()

    if not assigned_to:
        # All absent is the normal v0.1 state — no issues.
        if not assigned_at and not assigned_by:
            return []
        # assigned_at or assigned_by present without assigned_to is inconsistent.
        issues.append({
            "field": "assigned_to",
            "severity": "warn",
            "message": (
                "assigned_at/assigned_by are set but assigned_to is missing; "
                "a claim needs an assignee"
            ),
        })
        return issues

    # assigned_to is set — check the companions.
    if not assigned_at:
        issues.append({
            "field": "assigned_at",
            "severity": "warn",
            "message": "assigned_to is set but assigned_at is missing; fleet coordination needs a timestamp",
        })
    elif not _ISO8601_RE.match(assigned_at):
        issues.append({
            "field": "assigned_at",
            "severity": "warn",
            "message": f"assigned_at is not ISO 8601: {assigned_at!r}",
        })

    if not assigned_by:
        issues.append({
            "field": "assigned_by",
            "severity": "warn",
            "message": "assigned_to is set but assigned_by is missing; record which session claimed this",
        })

    return issues


def validate_scope_bounds(fm: dict[str, str], body: str) -> list[dict[str, str]]:
    """Warn when a Verified Facts number is much larger than the Objective number.

    Catches the scope-ambiguity failure mode (2026-07-20 incident): the
    Objective said "7000+ videos" but a Verified Fact mentioned "51,337
    pending videos" without labeling which was the work scope and which was
    the ambient total. A fresh reader who sees only one number will
    misestimate the work.

    This is a **heuristic with false positives** — severity is 'warn'. The
    check is suppressed when the handoff author has used explicit scope-label
    keywords ("scope bound", "work scope", "of these", "deferred", etc.).
    """
    issues: list[dict[str, str]] = []

    obj_text = _extract_section(body, "objective")
    if not obj_text:
        return []

    obj_numbers = _extract_integers(obj_text)
    if not obj_numbers:
        return []

    facts_text = _extract_section(body, "verified facts")
    if not facts_text:
        return []

    fact_numbers = _extract_integers(facts_text)

    # Check for large discrepancies without subset labeling.
    max_obj = max(obj_numbers)
    combined_text = (obj_text + " " + facts_text).lower()
    has_subset_label = any(kw in combined_text for kw in _SCOPE_LABEL_KEYWORDS)

    if has_subset_label:
        return []  # author explicitly labeled the scope bounds

    for fn in sorted(fact_numbers, reverse=True):
        if fn > max_obj * 3:
            issues.append({
                "field": "objective.scope_bounds",
                "severity": "warn",
                "message": (
                    f"Objective's largest number is {max_obj:,} but a Verified Fact mentions "
                    f"{fn:,}. If the work scope is a subset of a larger total, state both "
                    f"explicitly (e.g., 'Scope: ~{max_obj:,} of {fn:,} total'). Ambiguous scope "
                    f"caused the 7,000-vs-51,337 incident (2026-07-20)."
                ),
            })
            break  # one warning is enough

    return issues


def validate_falsifier_strength(packets: list[dict[str, str]]) -> list[dict[str, str]]:
    """Warn when a bulk-operation task has a falsifier that only catches catastrophe.

    A falsifier like 'produces 0 transcripts' only catches **total** failure,
    not a 30% success rate (which is still a disaster for a production run).
    Bulk/batch/scale tasks should specify a success-rate threshold.

    Heuristic: fires when the task goal or in-scope contains a bulk keyword
    AND the falsifier does not mention any rate/threshold indicator AND the
    falsifier mentions a catastrophic-zero keyword. Severity is 'warn'.
    """
    issues: list[dict[str, str]] = []
    for pkt in packets:
        pkt_id = pkt.get("id", "<unknown>")
        goal = pkt.get("goal", "").lower()
        scope = pkt.get("in scope", "").lower()
        falsifier = pkt.get("falsifier", "").lower()

        # Is this a bulk operation?
        combined = goal + " " + scope
        is_bulk = any(kw in combined for kw in _BULK_KEYWORDS)
        if not is_bulk or not falsifier:
            continue

        # Does the falsifier mention a rate/threshold?
        has_rate = any(ind in falsifier for ind in _RATE_INDICATORS)
        if has_rate:
            continue  # good — rate threshold present

        # Does it only mention catastrophic-zero?
        catastrophe_words = ("0 ", "zero", "no output", "produces 0", "none", "empty", "crash")
        only_catastrophe = any(w in falsifier for w in catastrophe_words)

        if only_catastrophe:
            issues.append({
                "field": f"task_packets.{pkt_id}.falsifier",
                "severity": "warn",
                "message": (
                    f"task packet {pkt_id!r} appears to be a bulk operation but its falsifier "
                    f"only catches catastrophic failure (0 output / crash). For bulk operations, "
                    f"specify a success-rate threshold (e.g., 'success rate < 90%'). A run that "
                    f"produces 30% of target passes the 'not zero' bar but is a disaster."
                ),
            })

    return issues


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def validate_handoff_text(text: str) -> list[dict[str, str]]:
    """Run all pure (non-filesystem) validators on a handoff file's text.

    Returns a list of issues. Empty list = passed.
    """
    fm, body = parse_frontmatter(text)
    headings = extract_headings(body)
    packets = extract_task_packets(body)

    issues: list[dict[str, str]] = []
    issues.extend(validate_header(fm))
    issues.extend(validate_body_sections(headings))
    issues.extend(validate_task_packets(packets))
    issues.extend(validate_verbatim_message(body))
    issues.extend(validate_streams_section_format(body))
    issues.extend(validate_assignment_fields(fm))
    issues.extend(validate_scope_bounds(fm, body))
    issues.extend(validate_falsifier_strength(packets))
    return issues


def validate_handoff_file(path: str | Path) -> list[dict[str, str]]:
    """Read a handoff file from disk and validate it."""
    text = Path(path).read_text(encoding="utf-8")
    return validate_handoff_text(text)


def is_valid(text: str) -> bool:
    """Convenience: returns True if no error-severity issues are found."""
    return not any(i["severity"] == "error" for i in validate_handoff_text(text))


__all__ = [
    "HEADER_REQUIRED",
    "HEADER_ASSIGNMENT_FIELDS",
    "HEADER_STATUS_ALLOWED",
    "HEADER_TYPE_ALLOWED_V01",
    "BODY_REQUIRED_SECTIONS",
    "TASK_PACKET_REQUIRED",
    "VERIFICATION_LEVEL_ALLOWED",
    "parse_frontmatter",
    "extract_headings",
    "extract_section_body",
    "extract_task_packets",
    "validate_header",
    "validate_body_sections",
    "validate_task_packets",
    "validate_verbatim_message",
    "validate_streams_section_format",
    "validate_assignment_fields",
    "validate_scope_bounds",
    "validate_falsifier_strength",
    "validate_handoff_text",
    "validate_handoff_file",
    "is_valid",
]
