"""Heuristic 3+3 scoring for email items.

Two axes, each summed across sub-axes and shifted into a 0-10 range:

  Importance (raw 0-2 each, summed, then +5, clamped to 0-10):
    - sender_domain:    2 if from_domain in operator whitelist,
                        1 if from_domain in KNOWN_DOMAINS,
                        0 otherwise.
    - deadline_language: 2 if subject OR body contains an urgent word
                         (urgent, asap, deadline, today, tomorrow),
                         1 if a softer time word (this week, soon,
                         tonight, this morning),
                         0 otherwise.
    - is_flagged:       2 if item["is_flagged"] is truthy, else 0.

  Urgency (raw 0-3 each, summed, then +5, clamped to 0-10):
    - hours_since:      3 if received < 1h ago,
                        2 if < 6h,
                        1 if < 24h,
                        0 otherwise.
    - reply_owed:       3 if subject contains "?" AND not a mailing list
                        (i.e. sent directly to the operator), else 0.
    - is_unread:        1 if item["is_unread"] is truthy, else 0.

Action type is derived from the combined scores:
    importance >= 7 AND urgency >= 7          -> "respond"
    importance >= 5  OR  urgency >= 5         -> "review"
    otherwise                                -> "fyi"

Note on the "fyi" branch: with the +5 shift the minimum achievable
score on either axis is 5 (one raw point = +5), so the "fyi" branch is
effectively unreachable in v1.0. It is preserved for clarity and as a
landing zone if a future version introduces a sub-5 signal path (e.g.
LLM-based scoring that returns <5 for clearly-fyi mail).

Sort order (sort_items):
    1. action_type ascending: respond < review < fyi
    2. received_at descending: most recent first
    3. is_unread descending: unread first

Whitelist source: ~/.config/email-skill/whitelist.txt
    One domain per line. Lines starting with '#' are comments. Empty
    lines are ignored. Domain comparison is case-insensitive.

Body text for deadline_language scoring: scoring accepts an optional
"body" key on the item. himalaya's envelope list output does NOT include
body (only envelope-level fields), so in v1.0 deadline_language is
effectively scored on subject only. When read_message() is called and
its output includes body, callers may pre-populate item["body"] before
passing to score_item.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

WHITELIST_PATH = Path.home() / ".config" / "email-skill" / "whitelist.txt"

# Words that signal "act now" deadlines. Match is case-insensitive
# substring on subject (and body, if present).
DEADLINE_URGENT = ("urgent", "asap", "deadline", "today", "tomorrow")

# Softer time hints — these bump deadline_language to 1 but not 2.
DEADLINE_TIME = ("this week", "this morning", "tonight", "soon")

# Domains we treat as "known" (not whitelisted, but not unknown either).
# Whitelisted domains always outrank these.
KNOWN_DOMAINS = frozenset({
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "yahoo.com", "icloud.com", "aol.com",
    "github.com",
})

# Action-type rank for sorting. Lower = higher priority.
_ACTION_RANK = {"respond": 0, "review": 1, "fyi": 2}


def _load_whitelist() -> frozenset[str]:
    """Load the operator's whitelist of high-importance sender domains.

    Returns an empty frozenset if the file is missing. The whitelist is
    loaded once at import time — operators who edit the file should
    restart the CLI to pick up changes (v1.0 limitation; acceptable
    since the file is rarely edited).
    """
    try:
        if not WHITELIST_PATH.exists():
            return frozenset()
        text = WHITELIST_PATH.read_text(encoding="utf-8")
    except OSError:
        return frozenset()
    domains: set[str] = set()
    for line in text.splitlines():
        s = line.strip().lower()
        if not s or s.startswith("#"):
            continue
        domains.add(s)
    return frozenset(domains)


_WHITELIST = _load_whitelist()


def _parse_received_at(item: dict) -> datetime | None:
    """Parse the received_at field as a UTC datetime, or None on failure."""
    raw = item.get("received_at")
    if not raw or not isinstance(raw, str):
        return None
    try:
        if raw.endswith("Z"):
            return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _hours_since(item: dict) -> float:
    """Hours between now (UTC) and item['received_at']. Returns large
    positive value when received_at is missing/unparseable."""
    dt = _parse_received_at(item)
    if dt is None:
        return 9999.0
    return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0


def score_item(item: dict) -> dict:
    """Score a single item in place. Returns the same item with added
    importance_score, urgency_score, action_type, and score_explanation
    fields. Safe to call repeatedly — the fields are overwritten.
    """
    subject_raw = item.get("subject") or ""
    body_raw = item.get("body") or ""
    subject = subject_raw.lower() if isinstance(subject_raw, str) else ""
    body = body_raw.lower() if isinstance(body_raw, str) else ""
    from_domain = (item.get("from_domain") or "").lower()

    # ---- Importance ----
    if from_domain and from_domain in _WHITELIST:
        sender_raw = 2
    elif from_domain and from_domain in KNOWN_DOMAINS:
        sender_raw = 1
    else:
        sender_raw = 0

    combined_text = f"{subject} {body}"
    has_urgent = any(w in combined_text for w in DEADLINE_URGENT)
    has_time = any(w in combined_text for w in DEADLINE_TIME)
    if has_urgent:
        deadline_raw = 2
    elif has_time:
        deadline_raw = 1
    else:
        deadline_raw = 0

    flagged_raw = 2 if item.get("is_flagged") else 0

    importance_raw = sender_raw + deadline_raw + flagged_raw
    importance_score = max(0, min(10, importance_raw + 5))

    # ---- Urgency ----
    hours = _hours_since(item)
    if hours < 1:
        hours_raw = 3
    elif hours < 6:
        hours_raw = 2
    elif hours < 24:
        hours_raw = 1
    else:
        hours_raw = 0

    is_direct = not bool(item.get("is_mailing_list"))
    has_question = "?" in subject_raw
    reply_owed_raw = 3 if (has_question and is_direct) else 0

    unread_raw = 1 if item.get("is_unread") else 0

    urgency_raw = hours_raw + reply_owed_raw + unread_raw
    urgency_score = max(0, min(10, urgency_raw + 5))

    # ---- Action type ----
    if importance_score >= 7 and urgency_score >= 7:
        action_type = "respond"
    elif importance_score >= 5 or urgency_score >= 5:
        action_type = "review"
    else:
        action_type = "fyi"

    item["importance_score"] = importance_score
    item["urgency_score"] = urgency_score
    item["action_type"] = action_type
    item["score_explanation"] = {
        "sender_domain": sender_raw,
        "deadline_language": deadline_raw,
        "is_flagged": flagged_raw,
        "hours_since": hours_raw,
        "reply_owed": reply_owed_raw,
        "is_unread": unread_raw,
    }
    return item


def sort_items(items: list[dict]) -> list[dict]:
    """Sort by (action_type asc [respond first], received_at desc [newest
    first], is_unread desc [unread first]).

    Uses a sort key that inverts the desc fields via negation. Python's
    sort is stable, so equal-key items keep their input order.
    """
    def sort_key(it: dict) -> tuple:
        action = _ACTION_RANK.get(it.get("action_type", "fyi"), 99)

        dt = _parse_received_at(it)
        if dt is None:
            # Place items without a timestamp at the bottom of any
            # action group. -inf ensures they sort last under negation.
            neg_ts = float("inf")
        else:
            neg_ts = -dt.timestamp()

        unread_neg = -1 if it.get("is_unread") else 0

        return (action, neg_ts, unread_neg)

    return sorted(items, key=sort_key)