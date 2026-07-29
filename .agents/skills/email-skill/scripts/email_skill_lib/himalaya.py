"""Subprocess wrapper around the himalaya CLI email client.

Himalaya (https://github.com/pimalaya/himalaya) is a stateless Rust CLI
email client. It exposes commands like:

    himalaya -a <account> envelope list -m INBOX --output json
    himalaya -a <account> envelope search <query> --output json
    himalaya -a <account> message read <id> --output json

This module:
  - Detects himalaya on PATH (is_available()).
  - Runs himalaya as a subprocess with a timeout, parses JSON output.
  - Normalizes himalaya's envelope dict into email-skill's item schema
    (account, message_id, thread_id, subject, from, from_domain,
    received_at, is_unread, is_flagged, has_attachments, snippet,
    is_mailing_list). Handles both v1.x and v2.0 envelope shapes.
  - Gracefully degrades: if himalaya is not installed, every function
    returns {"error": "himalaya not found", ...} instead of raising.
    This lets the CLI respond cleanly on hosts where himalaya hasn't been
    installed yet (Phase 0 of the deployment plan).

Field name compatibility notes:
  - "id"            envelope id; same in v1.x and v2.0.
  - "subject"       same name.
  - "from"          may be a string ("Alice <alice@example.com>") in v1.x
                    or an object ({name, email}) in v2.0. We handle both.
  - "date"          v1.x: "from" field may carry it. v2.0: "date" field.
                    We accept "date" or "received_at" from himalaya.
  - "flags"         list of strings: "seen", "flagged", "answered",
                    "draft", "deleted", "has_attachment".
                    v1.x: list. v2.0: list.
  - "thread_id"     v2.0+ has this; v1.x may use message id as fallback.
  - "has_attachment" v2.0 sometimes exposes this as a separate boolean
                    rather than only in flags.
  - "preview"/"snippet" v2.0 envelope list returns "preview"; older
                    versions may return "snippet" or nothing.

Output envelope from himalaya is `{"envelopes": [...]}` per the
archlinux man page and Hermes Agent docs. We also accept `{"messages":
[...]}` as a fallback in case future versions rename the key.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

NOT_FOUND_ERROR = "himalaya not found"


def is_available() -> bool:
    """Return True iff the himalaya binary is on PATH."""
    return shutil.which("himalaya") is not None


# ---------------------------------------------------------------------------
# Subprocess + JSON parsing
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 60) -> dict[str, Any]:
    """Run himalaya and return its parsed JSON output.

    Returns a dict in one of these shapes:
      - The parsed JSON himalaya emitted (usually {"envelopes": [...]} or
        a single message dict on `message read`).
      - {"error": <msg>, ...} on any failure mode (missing binary,
        timeout, non-zero exit, non-JSON output).
    """
    if not is_available():
        return {"error": NOT_FOUND_ERROR}

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        return {"error": f"himalaya timeout after {timeout}s", "command": cmd}
    except FileNotFoundError:
        # Race: PATH changed between is_available() and run.
        return {"error": NOT_FOUND_ERROR}
    except Exception as e:  # pragma: no cover (defensive)
        return {"error": f"himalaya invocation failed: {e}", "command": cmd}

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        return {
            "error": f"himalaya exit {proc.returncode}",
            "stderr": stderr[:500],
            "command": cmd,
        }

    out = (proc.stdout or "").strip()
    if not out:
        # Empty output: himalaya exits 0 with no stdout for empty inboxes.
        return {"envelopes": []}

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {
            "error": "himalaya output not JSON",
            "raw": out[:500],
            "command": cmd,
        }


# ---------------------------------------------------------------------------
# Envelope normalization
# ---------------------------------------------------------------------------


def _parse_from(from_field: Any) -> tuple[str, str]:
    """Parse himalaya's `from` field into (display_name, email).

    Handles:
      - dict {"name": "...", "email": "..."} (himalaya v2.0)
      - string "Display Name <email@domain>" (himalaya v1.x)
      - string "email@domain" (no display name)
      - None / missing ("", "")
    """
    if isinstance(from_field, dict):
        name = from_field.get("name") or ""
        if isinstance(name, list):
            name = " ".join(str(x) for x in name)
        email = from_field.get("email") or from_field.get("addr") or ""
        return (str(name), str(email))

    if isinstance(from_field, str):
        s = from_field.strip()
        if "<" in s and ">" in s:
            name = s.split("<", 1)[0].strip().strip('"').strip("'")
            email = s.split("<", 1)[1].split(">", 1)[0].strip()
            return (name, email)
        return ("", s)

    return ("", "")


def _from_domain(email: str) -> str:
    """Extract the domain part of an email address, lowercased."""
    if not email or "@" not in email:
        return ""
    return email.split("@", 1)[1].lower().strip()


def _normalize_flags(flags: Any) -> set[str]:
    """Normalize himalaya's flags field into a set of lowercase strings."""
    if flags is None:
        return set()
    if isinstance(flags, str):
        return {flags.lower()}
    if isinstance(flags, (list, tuple, set)):
        return {str(f).lower() for f in flags}
    return set()


def _normalize_envelope(env: dict, account_name: str) -> dict:
    """Convert a himalaya envelope dict into email-skill's item schema.

    Tolerates missing fields by defaulting to empty/False. Does NOT
    call score_item — the CLI composes scoring after collection.
    """
    name, email = _parse_from(env.get("from"))
    domain = _from_domain(email)

    flags = _normalize_flags(env.get("flags"))
    is_unread = "seen" not in flags
    is_flagged = "flagged" in flags
    # Some himalaya versions expose has_attachment as a top-level boolean
    # OR only via flags.
    has_attachments = bool(env.get("has_attachment")) or "has_attachment" in flags
    is_mailing_list = "list" in flags or bool(env.get("list"))

    msg_id = str(env.get("id") or "")
    # v2.0 has thread_id; v1.x often doesn't. Fall back to message id
    # so defer/ignore state can still key on something stable.
    thread_id = str(env.get("thread_id") or msg_id)

    received_at = (
        env.get("date")
        or env.get("received_at")
        or env.get("internal_date")
        or ""
    )

    # Snippet: prefer "preview" (v2.0), then "snippet" (v1.x), else empty.
    raw_snippet = (
        env.get("preview")
        or env.get("snippet")
        or env.get("body")
        or ""
    )
    if isinstance(raw_snippet, str) and len(raw_snippet) > 200:
        snippet = raw_snippet[:200]
    elif isinstance(raw_snippet, str):
        snippet = raw_snippet
    else:
        snippet = ""

    return {
        "account": account_name,
        "message_id": msg_id,
        "thread_id": thread_id,
        "subject": env.get("subject") or "",
        "from": email or name or "",
        "from_name": name,
        "from_domain": domain,
        "received_at": received_at,
        "is_unread": is_unread,
        "is_flagged": is_flagged,
        "has_attachments": has_attachments,
        "snippet": snippet,
        "is_mailing_list": is_mailing_list,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_account(account: dict, max_items: int = 20) -> dict:
    """Scan a single account's INBOX. Returns:

        {
            "name":     <account short name>,
            "provider": <provider string>,
            "error":    None | <error message>,
            "items":    [normalized envelope dict, ...]
        }

    On himalaya-not-found, error="himalaya not found" and items=[] so
    callers can iterate without None-checks.
    """
    name = account.get("name", "")
    provider = account.get("provider", "")

    if not is_available():
        return {
            "name": name,
            "provider": provider,
            "error": NOT_FOUND_ERROR,
            "items": [],
        }

    cmd = [
        "himalaya",
        "-a", name,
        "envelope", "list",
        "-m", "INBOX",
        "--output", "json",
    ]
    raw = _run(cmd)
    if raw.get("error"):
        return {
            "name": name,
            "provider": provider,
            "error": raw["error"],
            "items": [],
        }

    envelopes = raw.get("envelopes") or raw.get("messages") or []
    items: list[dict] = []
    for env in envelopes[:max_items]:
        if not isinstance(env, dict):
            continue
        try:
            items.append(_normalize_envelope(env, name))
        except Exception as e:  # pragma: no cover (defensive)
            items.append({
                "account": name,
                "error": f"normalize failed: {e}",
                "raw": str(env)[:200],
            })

    return {
        "name": name,
        "provider": provider,
        "error": None,
        "items": items,
    }


def read_message(account: str, message_id: str) -> dict:
    """Read a single message's full content. Returns the parsed JSON
    himalaya emits, or {"error": ...} on failure.

    himalaya's `message read` returns a richer object than envelope list
    — typically including body, headers, attachments. We pass it through
    unchanged rather than re-normalizing, so consumers see all fields.
    """
    if not is_available():
        return {"error": NOT_FOUND_ERROR}

    cmd = [
        "himalaya",
        "-a", account,
        "message", "read", message_id,
        "--output", "json",
    ]
    return _run(cmd)


def search(account: str, query: str, max_results: int = 20) -> list[dict]:
    """Search one account for envelopes matching `query`. Returns a
    list of normalized items (empty list on error / no results)."""
    if not is_available():
        return []

    cmd = [
        "himalaya",
        "-a", account,
        "envelope", "search", query,
        "--output", "json",
    ]
    raw = _run(cmd)
    if raw.get("error"):
        return []

    envelopes = raw.get("envelopes") or raw.get("messages") or []
    items: list[dict] = []
    for env in envelopes[:max_results]:
        if isinstance(env, dict):
            try:
                items.append(_normalize_envelope(env, account))
            except Exception:  # pragma: no cover (defensive)
                continue
    return items