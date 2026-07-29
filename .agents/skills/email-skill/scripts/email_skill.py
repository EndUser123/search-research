#!/usr/bin/env python3
"""email-skill: stateless CLI for cross-agent email access.

A thin wrapper around the himalaya CLI email client that adds:
  - 15-minute TTL cache (P:/.data/email-scan/cache.json)
  - Heuristic 3+3 scoring (importance 0-10 + urgency 0-10 + action_type)
  - Per-thread defer (snooze) and ignore (suppress) state
  - JSON envelope output (schema_version: "1.0") when --json is passed

Designed for invocation from any agent runtime with shell access (Grok
Build, Claude Code, Codex, OpenCode, Pi). No MCP client, no per-runtime
config. See SKILL.md for full usage docs.

Subcommands:
    scan-inbox     Scan all accounts; return scored items from cache or fresh.
    read-message   Read a single message by id.
    search         Search across accounts.
    defer          Snooze a thread for N hours.
    ignore         Suppress a thread until it changes.
    status         Show cache age, lock state, account health.
    accounts       List configured accounts and their provider type.

Exit codes:
    0   Success
    1   Generic error
    2   Config error (unknown account, malformed id)
    3   Auth error (OAuth / IMAP login failed)
    4   Cache was stale and we performed a fresh scan
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make sibling imports work when invoked as `python email_skill.py` or
# `python -m email_skill`. The scripts/ dir contains both the CLI and
# the email_skill_lib package.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from email_skill_lib import accounts, cache, defer, himalaya, scoring  # noqa: E402
from email_skill_lib.schema import make_envelope  # noqa: E402

# Exit codes — see module docstring.
EXIT_OK = 0
EXIT_ERR = 1
EXIT_CONFIG = 2
EXIT_AUTH = 3
EXIT_STALE_RESCAN = 4


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_output(command: str, payload: dict, as_json: bool) -> None:
    """Emit command output. JSON path wraps in the v1.0 envelope; text
    path prints a short human-readable summary."""
    if as_json:
        envelope = make_envelope(command, **payload)
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return

    # Human-readable summary
    if payload.get("error"):
        print(f"error: {payload['error']}", file=sys.stderr)
        return

    if command == "scan-inbox":
        hit = "cache hit" if payload.get("cache_hit") else "fresh scan"
        scanned = payload.get("scanned_at", "")
        items = payload.get("items", [])
        print(f"scan-inbox: {hit} at {scanned}; {len(items)} items")
        for it in items:
            if isinstance(it, dict):
                action = it.get("action_type", "?")
                subj = it.get("subject", "")[:60]
                acct = it.get("account", "?")
                imp = it.get("importance_score", "?")
                urg = it.get("urgency_score", "?")
                print(f"  [{action}] {acct} imp={imp} urg={urg}: {subj}")
        return

    if command == "search":
        items = payload.get("items", [])
        print(f"search '{payload.get('query', '')}': {len(items)} items")
        for it in items:
            if isinstance(it, dict):
                print(f"  {it.get('account', '?')}: {it.get('subject', '')[:60]}")
        return

    if command == "status":
        for k, v in payload.items():
            if k in ("command",):
                continue
            print(f"{k}: {v}")
        return

    if command == "accounts":
        for a in payload.get("accounts", []):
            print(f"{a['name']:20s} {a['provider']:10s} {a['email']}")
        return

    if command == "defer":
        entry = payload.get("entry") or {}
        print(f"deferred {payload.get('thread_id')} until {entry.get('deferred_until')}")
        return

    if command == "ignore":
        entry = payload.get("entry") or {}
        print(f"ignored {payload.get('thread_id')} (reason: {entry.get('ignore_reason')})")
        return

    if command == "read-message":
        msg = payload.get("message") or {}
        if isinstance(msg, dict):
            print(json.dumps(msg, indent=2, ensure_ascii=False))
        return

    # Fallback: dump the payload as JSON even on the text path.
    print(json.dumps(payload, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Subcommand: scan-inbox
# ---------------------------------------------------------------------------


def cmd_scan_inbox(args: argparse.Namespace) -> int:
    """Return cached or freshly-scored inbox items.

    Cache hit path:
        1. Read cache.json if fresh (< TTL).
        2. Re-score items (defensive — scoring may have been updated).
        3. Apply defer/ignore filters.
        4. Sort by (action_type, received_at, is_unread).

    Cache miss / --refresh path:
        1. If himalaya not on PATH: graceful return with empty items.
        2. Otherwise: scan each account, score, write cache, filter, sort.

    Exit code 4 (EXIT_STALE_RESCAN) is reserved for "we performed a
    fresh scan because cache was stale"; we return 0 instead because
    operators don't want stale-vs-fresh to look like an error. Reserved
    in case a future caller wants to detect it.
    """
    as_json = args.json

    # Determine which accounts to scan
    if args.account:
        acct = accounts.get_account(args.account)
        if not acct:
            _print_output("scan-inbox", {
                "error": f"unknown account: {args.account}",
                "items": [],
            }, as_json)
            return EXIT_CONFIG
        account_list = [acct]
    else:
        account_list = list(accounts.ACCOUNTS)

    # ---- Cache hit path ----
    cached = None if args.refresh else cache.read_cache()
    if cached is not None:
        all_items: list[dict] = []
        for acc_data in cached.get("accounts", []):
            for it in acc_data.get("items", []):
                if isinstance(it, dict):
                    # Re-score defensively (catches scoring formula changes
                    # between runs without invalidating the cache file).
                    scoring.score_item(it)
                    all_items.append(it)

        all_items = defer.apply_filters(all_items)
        all_items = scoring.sort_items(all_items)
        if args.max is not None:
            all_items = all_items[: args.max]

        _print_output("scan-inbox", {
            "cache_hit": True,
            "scanned_at": cached.get("scanned_at"),
            "items": all_items,
        }, as_json)
        return EXIT_OK

    # ---- Fresh scan path ----
    if not himalaya.is_available():
        _print_output("scan-inbox", {
            "cache_hit": False,
            "error": "himalaya not found",
            "items": [],
        }, as_json)
        return EXIT_OK

    fresh_accounts: list[dict] = []
    all_items = []
    for acc in account_list:
        acc_data = himalaya.scan_account(acc, max_items=args.max or 50)
        for it in acc_data.get("items", []):
            if isinstance(it, dict):
                scoring.score_item(it)
                all_items.append(it)
        fresh_accounts.append(acc_data)

    # Write the cache (atomic, file-locked). We persist the per-account
    # raw shape so a future cache hit doesn't need to re-read himalaya.
    cache.write_cache({"accounts": fresh_accounts})

    all_items = defer.apply_filters(all_items)
    all_items = scoring.sort_items(all_items)
    if args.max is not None:
        all_items = all_items[: args.max]

    _print_output("scan-inbox", {
        "cache_hit": False,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": all_items,
    }, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Subcommand: read-message
# ---------------------------------------------------------------------------


def cmd_read_message(args: argparse.Namespace) -> int:
    """Read a single message. ID format: '<account>:<message_id>'.

    v1.0 requires the account prefix because himalaya's `message read`
    is per-account. Callers that only have a message_id need to look up
    the account from the cache first.
    """
    as_json = args.json
    msg_id = args.message_id

    if ":" not in msg_id:
        _print_output("read-message", {
            "error": "message_id must include account prefix (e.g. 'a.hominidae:abc123')",
            "message_id": msg_id,
        }, as_json)
        return EXIT_CONFIG

    acct_name, _, local_id = msg_id.partition(":")
    if not local_id:
        _print_output("read-message", {
            "error": "empty message_id after account prefix",
            "message_id": msg_id,
        }, as_json)
        return EXIT_CONFIG

    acct = accounts.get_account(acct_name)
    if not acct:
        _print_output("read-message", {
            "error": f"unknown account: {acct_name}",
        }, as_json)
        return EXIT_CONFIG

    if not himalaya.is_available():
        _print_output("read-message", {
            "error": "himalaya not found",
        }, as_json)
        return EXIT_ERR

    result = himalaya.read_message(acct_name, local_id)
    if result.get("error"):
        err_msg = str(result["error"]).lower()
        exit_code = EXIT_AUTH if "auth" in err_msg or "oauth" in err_msg or "token" in err_msg else EXIT_ERR
        _print_output("read-message", {
            "error": result["error"],
            "stderr": result.get("stderr", ""),
        }, as_json)
        return exit_code

    _print_output("read-message", {"message": result}, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Subcommand: search
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> int:
    """Search across all configured accounts."""
    as_json = args.json
    query = args.query
    max_per_account = args.max or 20

    if not himalaya.is_available():
        _print_output("search", {
            "query": query,
            "error": "himalaya not found",
            "items": [],
        }, as_json)
        return EXIT_OK

    all_items: list[dict] = []
    for acc in accounts.ACCOUNTS:
        items = himalaya.search(acc["name"], query, max_results=max_per_account)
        for it in items:
            scoring.score_item(it)
            all_items.append(it)

    all_items = defer.apply_filters(all_items)
    all_items = scoring.sort_items(all_items)
    if args.max is not None:
        all_items = all_items[: args.max]

    _print_output("search", {"query": query, "items": all_items}, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Subcommand: defer
# ---------------------------------------------------------------------------


def cmd_defer(args: argparse.Namespace) -> int:
    """Snooze a thread for N hours (default 4)."""
    as_json = args.json
    raw = args.thread_id
    if ":" not in raw:
        _print_output("defer", {
            "error": "thread_id must be 'account:thread_id'",
            "thread_id": raw,
        }, as_json)
        return EXIT_CONFIG

    acct_name, _, tid = raw.partition(":")
    if not tid:
        _print_output("defer", {
            "error": "empty thread_id after account prefix",
            "thread_id": raw,
        }, as_json)
        return EXIT_CONFIG

    acct = accounts.get_account(acct_name)
    if not acct:
        _print_output("defer", {
            "error": f"unknown account: {acct_name}",
        }, as_json)
        return EXIT_CONFIG

    entry = defer.set_defer(tid, acct_name, hours=args.hours)
    _print_output("defer", {
        "thread_id": raw,
        "hours": args.hours,
        "entry": entry,
    }, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Subcommand: ignore
# ---------------------------------------------------------------------------


def cmd_ignore(args: argparse.Namespace) -> int:
    """Suppress a thread until its thread_id changes."""
    as_json = args.json
    raw = args.thread_id
    if ":" not in raw:
        _print_output("ignore", {
            "error": "thread_id must be 'account:thread_id'",
            "thread_id": raw,
        }, as_json)
        return EXIT_CONFIG

    acct_name, _, tid = raw.partition(":")
    if not tid:
        _print_output("ignore", {
            "error": "empty thread_id after account prefix",
            "thread_id": raw,
        }, as_json)
        return EXIT_CONFIG

    acct = accounts.get_account(acct_name)
    if not acct:
        _print_output("ignore", {
            "error": f"unknown account: {acct_name}",
        }, as_json)
        return EXIT_CONFIG

    # current-thread defaults to the thread_id we were given
    current = args.current_thread if args.current_thread else tid
    entry = defer.set_ignore(tid, acct_name, args.reason, current_thread_id=current)
    _print_output("ignore", {
        "thread_id": raw,
        "reason": args.reason,
        "entry": entry,
    }, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    """Show cache age, lock state, account health."""
    as_json = args.json
    status: dict = {
        "himalaya_available": himalaya.is_available(),
        "cache_file": str(cache.CACHE_FILE),
        "cache_lock": str(cache.LOCK_FILE),
        "state_file": str(defer.STATE_FILE),
        "state_lock": str(defer.LOCK_FILE),
    }

    # Cache freshness
    cached = cache.read_cache()
    if cached is not None:
        ts = _parse_iso(cached.get("scanned_at"))
        if ts is not None:
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            status["cache_age_seconds"] = round(age, 1)
            status["cache_fresh"] = age <= cache.DEFAULT_TTL
        else:
            status["cache_age_seconds"] = None
            status["cache_fresh"] = False
        status["cache_scanned_at"] = cached.get("scanned_at")
        status["cache_account_count"] = len(cached.get("accounts", []))
        # Sum items across accounts for a quick "how much is in the cache"
        status["cache_item_count"] = sum(
            len(acc.get("items", []) or [])
            for acc in cached.get("accounts", [])
            if isinstance(acc, dict)
        )
    else:
        status["cache_age_seconds"] = None
        status["cache_fresh"] = False
        status["cache_scanned_at"] = None
        status["cache_account_count"] = 0
        status["cache_item_count"] = 0

    # Lock state — non-blocking attempt to acquire.
    got_lock = cache.acquire_lock(timeout=0.05)
    status["lock_free"] = got_lock
    if got_lock:
        cache.release_lock()

    # State file size
    if defer.STATE_FILE.exists():
        try:
            state = defer.get_state()
            status["state_thread_count"] = len(state.get("threads", {}))
        except Exception:
            status["state_thread_count"] = None
    else:
        status["state_thread_count"] = 0

    # Per-account health
    status["accounts"] = [
        {"name": a["name"], "provider": a["provider"], "email": a["email"]}
        for a in accounts.ACCOUNTS
    ]

    _print_output("status", status, as_json)
    return EXIT_OK


def _parse_iso(s):
    """Parse an ISO timestamp from cache metadata."""
    if not s:
        return None
    try:
        if s.endswith("Z"):
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Subcommand: accounts
# ---------------------------------------------------------------------------


def cmd_accounts(args: argparse.Namespace) -> int:
    """List configured accounts and their provider type."""
    as_json = args.json
    _print_output("accounts", {"accounts": accounts.ACCOUNTS}, as_json)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse with all 7 subcommands."""
    parser = argparse.ArgumentParser(
        prog="email-skill",
        description=(
            "Stateless CLI for cross-agent email access. "
            "Wraps himalaya with TTL cache, heuristic scoring, and defer/ignore state."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    # scan-inbox
    p_scan = sub.add_parser(
        "scan-inbox",
        help="Scan all accounts; return scored items from cache or fresh scan.",
    )
    p_scan.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_scan.add_argument("--account", metavar="NAME",
                        help="Restrict scan to one account short name.")
    p_scan.add_argument("--max", type=int, metavar="N",
                        help="Maximum items to return (default: no limit).")
    p_scan.add_argument("--refresh", action="store_true",
                        help="Bypass cache; force a fresh himalaya scan.")
    p_scan.set_defaults(func=cmd_scan_inbox)

    # read-message
    p_read = sub.add_parser(
        "read-message",
        help="Read a single message. ID format: 'account:message_id'.",
    )
    p_read.add_argument("message_id", help="Message ID, format 'account:msgid'.")
    p_read.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_read.set_defaults(func=cmd_read_message)

    # search
    p_search = sub.add_parser(
        "search",
        help="Search across accounts for envelopes matching a query.",
    )
    p_search.add_argument("query", help="Search query string.")
    p_search.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_search.add_argument("--max", type=int, metavar="N",
                          help="Maximum results per account (default: 20).")
    p_search.set_defaults(func=cmd_search)

    # defer
    p_defer = sub.add_parser(
        "defer",
        help="Snooze a thread for N hours (default 4).",
    )
    p_defer.add_argument("thread_id",
                         help="Thread ID, format 'account:thread_id'.")
    p_defer.add_argument("--hours", type=float, default=4.0,
                         help="Hours to defer (default: 4).")
    p_defer.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_defer.set_defaults(func=cmd_defer)

    # ignore
    p_ignore = sub.add_parser(
        "ignore",
        help="Suppress a thread until its thread_id changes.",
    )
    p_ignore.add_argument("thread_id",
                          help="Thread ID, format 'account:thread_id'.")
    p_ignore.add_argument("--reason", required=True,
                          help="Reason for ignoring (e.g. 'handled offline').")
    p_ignore.add_argument("--current-thread", metavar="ID",
                          help="Override the current thread id (defaults to thread_id).")
    p_ignore.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_ignore.set_defaults(func=cmd_ignore)

    # status
    p_status = sub.add_parser(
        "status",
        help="Show cache age, lock state, account health.",
    )
    p_status.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_status.set_defaults(func=cmd_status)

    # accounts
    p_accounts = sub.add_parser(
        "accounts",
        help="List configured accounts and their provider type.",
    )
    p_accounts.add_argument("--json", action="store_true", help="Emit JSON envelope.")
    p_accounts.set_defaults(func=cmd_accounts)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # pragma: no cover (defensive)
        # Last-resort handler: emit the error to stderr and exit non-zero.
        # The subcommand handlers are expected to handle their own errors
        # and return appropriate exit codes; this catches anything they
        # missed.
        print(f"fatal: {e}", file=sys.stderr)
        return EXIT_ERR


if __name__ == "__main__":
    sys.exit(main())