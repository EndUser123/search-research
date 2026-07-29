"""Per-thread defer (snooze) and ignore (suppress) state.

Files:
    P:/.data/email-scan/state.json  — the state document.
    P:/.data/email-scan/state.lock  — file lock for atomic writers.

State shape:
    {
      "threads": {
        "<account>:<thread_id>": {
          "deferred_until":          "2026-07-28T22:00:00Z" | null,
          "ignore_reason":           "handled offline"        | null,
          "thread_id_when_ignored":  "thread123"               | null
        },
        ...
      }
    }

The key is the concatenation "<account>:<thread_id>" so the same thread_id
under different accounts (rare but possible) stays disambiguated.

Semantics:
    - defer:  set deferred_until = now + hours. Item is hidden from the
              scan output until that timestamp passes. When it expires,
              the item re-surfaces automatically — no permanent dismissal.
    - ignore: set ignore_reason + thread_id_when_ignored. Item is hidden
              until EITHER ignore_reason is cleared OR the item's
              thread_id changes (a new message in the same thread). The
              thread-change check is the forgiveness principle — evolving
              conversations are not permanently dismissed.

This module is intentionally separate from cache.py:
    - cache.json holds scan results (TTL-expires, rewritten on refresh).
    - state.json holds user actions (defer/ignore) — must persist across
      cache refreshes indefinitely.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# P:/.agents/__lib/ is parents[4] from this file (which lives at
# P:/.agents/skills/email-skill/scripts/email_skill_lib/defer.py).
_PKG_PARENT = Path(__file__).resolve().parents[4]
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from __lib.atomic_io import atomic_write_with_lock  # noqa: E402

STATE_DIR = Path("P:/.data/email-scan")
STATE_FILE = STATE_DIR / "state.json"
LOCK_FILE = STATE_DIR / "state.lock"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _key(account: str, thread_id: str) -> str:
    return f"{account}:{thread_id}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    """Parse a stored ISO8601 UTC timestamp. Returns None on missing/invalid."""
    if not s or not isinstance(s, str):
        return None
    try:
        if s.endswith("Z"):
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _save_state(state: dict) -> None:
    """Atomic write of state.json with the file lock."""
    _ensure_dir()
    payload = json.dumps(state, indent=2, ensure_ascii=False)
    atomic_write_with_lock(LOCK_FILE, STATE_FILE, payload, timeout=10.0)


# ---------------------------------------------------------------------------
# Public API: state read/write
# ---------------------------------------------------------------------------


def get_state() -> dict:
    """Return the current state dict.

    Shape: {"threads": {<key>: {"deferred_until": ..., "ignore_reason":
    ..., "thread_id_when_ignored": ...}, ...}}

    Returns {"threads": {}} if the file is missing or unparseable. The
    caller can treat empty and missing identically.
    """
    _ensure_dir()
    if not STATE_FILE.exists():
        return {"threads": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"threads": {}}


def set_defer(thread_id: str, account: str, hours: float = 4.0) -> dict:
    """Snooze a thread. Sets deferred_until = now + hours.

    Side effect: also clears any ignore_reason on this thread, because
    defer and ignore are mutually exclusive — applying a defer to a
    thread that was ignored means "I'm engaged with it now, push it
    later" which supersedes "I don't want to see this."

    Returns the updated entry.
    """
    state = get_state()
    threads = state.setdefault("threads", {})
    key = _key(account, thread_id)

    entry = threads.get(key) or {}
    entry["deferred_until"] = _iso(_now_utc() + timedelta(hours=hours))
    entry["ignore_reason"] = None
    entry["thread_id_when_ignored"] = None
    threads[key] = entry

    _save_state(state)
    return entry


def set_ignore(
    thread_id: str,
    account: str,
    reason: str,
    current_thread_id: str,
) -> dict:
    """Suppress a thread until its thread_id changes.

    Side effect: also clears any deferred_until on this thread, because
    ignore supersedes defer (an ignored thread shouldn't pop back up
    when the defer timer expires).

    Args:
        thread_id:           the thread identifier to track.
        account:             account short name.
        reason:              operator-provided explanation (e.g. "handled
                             offline", "spam", "waiting on external").
        current_thread_id:   the current thread_id we last saw, so we can
                             detect when new messages arrive in the thread.
                             Defaults to `thread_id` if not overridden.
    """
    state = get_state()
    threads = state.setdefault("threads", {})
    key = _key(account, thread_id)

    entry = threads.get(key) or {}
    entry["ignore_reason"] = reason
    entry["thread_id_when_ignored"] = current_thread_id
    entry["deferred_until"] = None
    threads[key] = entry

    _save_state(state)
    return entry


# ---------------------------------------------------------------------------
# Public API: filter checks (called per item)
# ---------------------------------------------------------------------------


def check_deferred(item: dict) -> bool:
    """Return True if the item should be SHOWN (not currently deferred).

    An item is considered deferred when state["threads"][key]
    ["deferred_until"] exists and is in the future. If the timestamp is
    in the past, the item re-surfaces (returns True).
    """
    state = get_state()
    threads = state.get("threads", {})
    key = _key(item.get("account", ""), item.get("thread_id", ""))
    entry = threads.get(key)
    if not entry:
        return True
    deferred_until_iso = entry.get("deferred_until")
    if not deferred_until_iso:
        return True
    dt = _parse_iso(deferred_until_iso)
    if dt is None:
        # Unparseable timestamp — show the item rather than hide it.
        return True
    return _now_utc() >= dt


def check_ignored(item: dict) -> bool:
    """Return True if the item should be SHOWN (not currently ignored).

    An item is currently ignored when:
      - state["threads"][key]["ignore_reason"] is set, AND
      - item["thread_id"] matches thread_id_when_ignored (no new message).

    If the thread_id has changed (new message arrived in the thread),
    the item re-surfaces automatically.
    """
    state = get_state()
    threads = state.get("threads", {})
    key = _key(item.get("account", ""), item.get("thread_id", ""))
    entry = threads.get(key)
    if not entry:
        return True
    ignore_reason = entry.get("ignore_reason")
    if not ignore_reason:
        return True
    when_ignored = entry.get("thread_id_when_ignored")
    current = item.get("thread_id", "")
    if when_ignored is not None and current and current != when_ignored:
        # Thread evolved — resurface.
        return True
    return False


def apply_filters(items: list[dict]) -> list[dict]:
    """Return the subset of items that should be shown.

    Applies both check_deferred and check_ignored. Items passing both
    checks are kept; items failing either are dropped.
    """
    return [it for it in items if check_deferred(it) and check_ignored(it)]