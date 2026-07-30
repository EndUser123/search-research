---
name: email-skill
description: Stateless CLI for cross-agent email access. Wraps himalaya with TTL cache, scoring, and deferral.
host: both
---

# email-skill

Single-binary CLI that gives any agent runtime on this host access to email.
Wraps the [himalaya](https://github.com/pimalaya/himalaya) CLI email client
with a 15-minute TTL cache, heuristic scoring, and per-thread defer/ignore state.

## Why a CLI, not MCP

Cross-runtime support. Any agent with shell access (Grok Build, Claude
Code, Codex, OpenCode, Pi) can invoke `email-skill scan-inbox --json`.
No per-runtime MCP client, no per-runtime config. The TTL cache + file
lock handle concurrent access safely.

Prior decision: `P:/.data/wiki/concepts/stateless-cli-vs-mcp-for-cross-agent-email-access.md`.

## Usage

```bash
# Scan inbox (uses cache if fresh — default 15-minute TTL)
email-skill scan-inbox --json

# Force fresh scan, single account, top 10 only
email-skill scan-inbox --refresh --account a.hominidae --max 10 --json

# Read a single message
email-skill read-message "a.hominidae:abc123" --json

# Search across accounts
email-skill search "Q3 budget" --json --max 10

# Snooze a thread for 4 hours (default; override with --hours)
email-skill defer "a.hominidae:thread-xyz" --hours 4

# Suppress a thread until it changes (a new message arrives)
email-skill ignore "a.hominidae:thread-xyz" --reason "handled offline"

# Check cache age, lock state, account health
email-skill status --json

# List configured accounts and their provider type
email-skill accounts --json
```

## Output format (JSON envelope)

Every `--json` output uses the v1.0 envelope:

```json
{
  "schema_version": "1.0",
  "command": "scan-inbox",
  "cache_hit": true,
  "scanned_at": "2026-07-28T19:06:00Z",
  "items": [
    {
      "account": "a.hominidae",
      "message_id": "...",
      "thread_id": "...",
      "subject": "...",
      "from": "alice@example.com",
      "from_name": "Alice Smith",
      "from_domain": "example.com",
      "received_at": "2026-07-28T18:00:00Z",
      "is_unread": true,
      "is_flagged": false,
      "has_attachments": false,
      "snippet": "first 200 chars of body...",
      "is_mailing_list": false,
      "importance_score": 9,
      "urgency_score": 10,
      "action_type": "respond",
      "score_explanation": {
        "sender_domain": 2,
        "deadline_language": 2,
        "is_flagged": 2,
        "hours_since": 3,
        "reply_owed": 3,
        "is_unread": 1
      }
    }
  ]
}
```

Consumers parse `schema_version` first, then `command` to know which
payload fields to expect.

## Exit codes

| Code | Meaning                                                      |
|------|--------------------------------------------------------------|
| 0    | Success                                                      |
| 1    | Generic error (himalaya not installed, subprocess failed)    |
| 2    | Config error (unknown account, malformed thread_id)          |
| 3    | Auth error (OAuth / IMAP login failed)                       |
| 4    | Cache was stale and we re-scanned (reserved; not currently emitted) |

## Scoring model (v1.0 — heuristic, no LLM)

Two axes, each summed across sub-axes and shifted into a 0-10 range:

| Axis         | Sub-axis           | Max | Source                                          |
|--------------|--------------------|-----|-------------------------------------------------|
| importance   | sender_domain      | 2   | whitelist > known-domain > otherwise            |
| importance   | deadline_language  | 2   | subject (and body, if present) match            |
| importance   | is_flagged         | 2   | item.is_flagged                                 |
| urgency      | hours_since        | 3   | (now - received_at) bucket                      |
| urgency      | reply_owed         | 3   | subject contains "?" AND not a mailing list     |
| urgency      | is_unread          | 1   | item.is_unread                                  |

Raw axis scores are summed, then +5, then clamped to 0-10. Action type:

- `importance >= 7 AND urgency >= 7` → **respond**
- `importance >= 5 OR urgency >= 5` → **review**
- otherwise → **fyi** (unreachable in v1.0 due to the +5 floor)

Sort order: action_type ascending (respond first), received_at
descending (newest first), is_unread descending (unread first).

## Setup

### 1. Install himalaya + ortie

```bash
# himalaya: Rust CLI email client (multi-account, JSON output, OAuth2)
cargo install himalaya

# ortie: OAuth2 token helper for himalaya
cargo install ortie

# OR on Windows, pre-built binaries via Scoop
scoop install himalaya ortie
```

### 2. Configure himalaya

`~/.config/himalaya/config.toml`:

```toml
[accounts.a-hominidae]
email = "a.hominidae@gmail.com"
default = true
backend = "gmail"

[accounts.a-hominidae.backend.auth]
type = "oauth2"
token.cmd = ["ortie", "token", "show", "-a", "gmail"]

# Repeat for troup.hominidae (Gmail) and brsthomson (Outlook/Hotmail).
```

### 3. OAuth browser auth (one-time per account)

```bash
ortie auth add gmail       # opens browser, captures refresh token
ortie auth add outlook     # same for Microsoft
```

### 4. Verify

```bash
himalaya -a a.hominidae envelope list -m INBOX --output json
email-skill status --json
```

If himalaya is not installed, `email-skill status` reports
`himalaya_available: false` and `scan-inbox` returns gracefully with
`{"error": "himalaya not found", "items": []}`. The CLI is fully usable
in degraded mode (status, accounts, defer, ignore) so it can be deployed
before himalaya is installed.

## Files

```
P:/.agents/skills/email-skill/
  SKILL.md
  scripts/
    email_skill.py             # CLI entry point
    email_skill_lib/           # Library
      __init__.py
      accounts.py              # Hardcoded account list (3 accounts)
      schema.py                # SCHEMA_VERSION + make_envelope
      cache.py                 # TTL cache + cross-platform file lock
      scoring.py               # Heuristic 3+3 scoring + sort
      himalaya.py              # Himalaya subprocess wrapper
      defer.py                 # Defer/ignore state

P:/.agents/__lib/
  __init__.py                  # Host primitives marker
  atomic_io.py                 # Atomic writes + file lock (shared by email-skill)

P:/.data/email-scan/
  cache.json                   # TTL-cached scan results
  cache.lock                   # File lock during scan
  state.json                   # Defer/ignore state (persists across cache TTLs)
  state.lock                   # File lock for state writes

~/.config/email-skill/
  whitelist.txt                # Sender domains scored as high-importance
                               # (one per line; # for comments)
```

## Whitelist

Create `~/.config/email-skill/whitelist.txt` with one domain per line:

```
example.com
important-client.com
```

Domains in this file score `sender_domain=2` in importance (outranking
the built-in known-domain set which scores 1). The whitelist is loaded
once at import time — restart the CLI after editing.

## Integration with /todo

The `/todo` skill (operator's unified action-list orchestrator) calls
`email-skill scan-inbox --json` in its Step 2 to merge email items with
workspace scan results. Email scan results are shared across terminals
via the TTL cache at `P:/.data/email-scan/cache.json`.

## Constraints (v1.0)

- **Read-only.** No send subcommand. Defer/ignore modify local state only.
- **Heuristic scoring only.** No LLM-based scoring in v1.0.
- **No tests shipped.** Tests are a separate phase (per spec).
- **No automatic himalaya install.** Operator installs himalaya + ortie.
- **No automatic OAuth setup.** Operator does browser auth.

## Architecture references

- `P:/.data/wiki/concepts/stateless-cli-vs-mcp-for-cross-agent-email-access.md`
  — the architecture decision this skill implements.
- `P:/.data/wiki/concepts/adhd-friendly-unified-todo-workspace-email-scanning.md`
  — the /todo integration and TTL-deferral design.
- `P:/.data/wiki/concepts/concurrent-cdp-auth-contention.md` — the
  multi-terminal auth isolation pattern that motivates the file-lock
  + TTL-cache concurrency model.

## Reusable internals

Other skills can import these functions directly:

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `atomic_write_only(path, content)` | `P:/.agents/__lib/atomic_io.py` | tmp+fsync+os.replace atomic write (no lock). UTF-8. | **stable** |
| `atomic_write_with_lock(lock, path, content, timeout=30)` | `P:/.agents/__lib/atomic_io.py` | atomic write + cross-platform file lock (msvcrt/fcntl). | **stable** |
| `acquire_lock(timeout=30)` / `release_lock()` | `email_skill_lib/cache.py` | Cross-platform advisory file lock with stale-lock detection (checks PID alive). | **stable** |
| `read_cache(ttl_seconds=900)` / `write_cache(data)` | `email_skill_lib/cache.py` | TTL-based JSON cache with auto-expiry. Cross-platform locking. | **stable** |
| `score_item(item)` / `sort_items(items)` | `email_skill_lib/scoring.py` | 3+3 heuristic scoring (importance × urgency). Returns scored dict. | **internal** — email-specific; generalize before reuse |
| `apply_filters(items)` | `email_skill_lib/defer.py` | Apply defer/ignore state to a list of items with TTL resurface. | **stable** |

**Import pattern:**
```python
import sys; sys.path.insert(0, "P:/.agents/__lib")
from atomic_io import atomic_write_only, atomic_write_with_lock

sys.path.insert(0, "P:/.agents/skills/email-skill/scripts")
from email_skill_lib.cache import acquire_lock, release_lock, read_cache, write_cache
```