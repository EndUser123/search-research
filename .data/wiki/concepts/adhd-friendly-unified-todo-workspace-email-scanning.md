---
title: "ADHD-Friendly Unified Todo: Workspace + Email Scanning with TTL-Based Deferral"
slug: adhd-friendly-unified-todo-workspace-email-scanning
created: 2026-07-28
category: decision
tags: [adhd, todo, email-scanning, task-prioritization, external-memory, workflow, multi-account, gmail, outlook, shared-cache, ttl-deferral]
summary: >
  Design for a unified "what should I do next?" system that scans both
  workspace state (handoffs, git, wiki) AND external accounts (email,
  calendar) to produce one prioritized action list. Email scanning uses a
  shared TTL cache (15-min default) so multiple terminals don't re-scan.
  Individual email items support per-item deferral (snooze for N hours)
  and ignore (suppress permanently or until thread changes). Email scan
  results are shared across terminals; workspace scan is per-session.
  Score-based prioritization (0-10 importance + 0-10 urgency) ranks items
  from all sources into one list. Built on prior art from abhuva/email-agent
  (MIT) and Super-Productivity's ADHD design principles.
cognitive_load: 3
verification: multi-source-verified
agent: grok
host: both
sources:
  - "abhuva/email-agent (GitHub, MIT) — multi-account IMAP+OAuth, score-based classification"
  - "Google Gmail API v1 — messages.list with q='is:unread is:important'"
  - "Microsoft Graph API / IMAP XOAUTH2 — Outlook/Hotmail access"
  - "Super-Productivity ADHD developer guide — external-memory principles"
  - "Augment Code study — 10-15 min context recovery cost per interruption"
  - "Reddit r/ADHD_Programmers — community consensus on what works"
relations:
  - target: wiki/concepts/dynamic-wiki-driven-skill-configuration.md
    type: related
  - target: wiki/concepts/optimal-wiki-usage-for-ai-agent-fleets.md
    type: related
---

# ADHD-Friendly Unified Todo: Workspace + Email Scanning with TTL-Based Deferral

## Decision context

**The problem:** the operator has ADHD and manages a fleet of AI coding agents
across multiple terminals. When context is lost (which happens frequently),
there's no single command that answers "what should I do right now?" — the
answer requires checking handoffs, git, wiki, AND email. Each check is a
separate skill or manual action. The cognitive cost of assembling the
picture exceeds the cognitive cost of doing the work.

**What the research found:** the field has solved the individual pieces
(email scanning, task extraction, ADHD-friendly prioritization) but not
the unified view. The closest prior art is `abhuva/email-agent` (multi-
account IMAP+OAuth, score-based classification) and Super-Productivity
(ADHD-designed task manager with external-memory patterns). Neither
integrates workspace state with email state.

**What this decision changes:** `/todo` becomes the single command that
scans everything — workspace + email — and produces one prioritized list.
Email scanning is a shared plugin (TTL-cached across terminals); workspace
scanning is per-session. Individual items support deferral (snooze) and
ignore (suppress), with automatic re-surfacing.

## Architecture

### Two isolation models (operator requirement)

| Data source | Isolation | Cache | Why |
|-------------|-----------|-------|-----|
| **Email scan** | Shared across terminals | TTL: 15 min at `P:/.data/email-scan/cache.json` | Email is external state — changes on its own timeline, not per-session. Scanning 3 accounts via API/IMAP is expensive (~5-10s). |
| **Workspace scan** | Per-session | None (always fresh) | Each terminal may have different commits, handoffs, modified files. Session 1's open threads ≠ session 2's. |

### Email scan module (shared plugin)

**Accounts:**
- `a.hominidae@gmail.com` (Gmail) — via Gmail API (OAuth 2.0)
- `troup.hominidae@gmail.com` (Gmail) — via Gmail API (OAuth 2.0)
- `brsthomson@hotmail.com` (Outlook/Hotmail) — via IMAP XOAUTH2 or MS Graph

**Scan process:**
1. Check shared cache at `P:/.data/email-scan/cache.json`
2. If `scanned_at + ttl_minutes > now`: return cached results
3. If stale: acquire file lock, scan all 3 accounts, write cache, release lock
4. Return: list of `{account, subject, from, date, importance_score, urgency_score, action_type, thread_id}`

**Per-item scoring (0-10 each axis):**
- **Importance:** sender domain, presence of deadline language, thread depth, operator whitelist/blacklist
- **Urgency:** time-since-received, deadline proximity, reply-owed heuristic (question mark + sent to operator directly)

**Pre-filter (cheap, before LLM):** rules-based — skip newsletters, receipts, automated notifications. Naive Bayes optional for cold start.

### TTL-based deferral (per-item snooze)

Each email item in the cache can have a `deferred_until` field:

```json
{
  "thread_id": "abc123",
  "subject": "Re: Q3 budget review",
  "importance_score": 8,
  "urgency_score": 7,
  "deferred_until": "2026-07-28T18:00:00Z",
  "ignore_reason": null
}
```

**Deferral rules:**
- `defer` action: set `deferred_until` to `now + N hours` (default: 4h)
- Item disappears from the action list until `deferred_until < now`
- When TTL expires, item re-surfaces automatically — no permanent dismissal
- The `$AIProcessed` IMAP keyword (or Gmail label) marks the email as scanned; deferral is a separate concern from scanning

**Ignore action (stronger than defer):**
- `ignore` action: set `ignore_reason` to operator-provided text
- Item is suppressed from the list
- **Re-surfaces if the thread changes** (new reply in the thread) — checked via thread ID comparison on next scan
- If thread doesn't change, item stays suppressed indefinitely
- This prevents permanent dismissal of evolving conversations

**Operator commands (from `/todo` output):**
```
1. [email] Re: Q3 budget review (importance: 8, urgency: 7)
   → defer 4h | defer 1d | ignore "handled offline" | open
```

### Workspace scan module (per-session, already built)

The existing `coverage_scan.py` handles this:
- Scans `P:/docs/handoffs/` for `status: open`
- Groups by session-chain membership and age
- Returns prioritized list of open work items

No changes needed — workspace scan is already per-session and isolated.

### Unified prioritization

`/todo` merges both lists and sorts by:

1. **Critical emails** (importance ≥8 AND urgency ≥7) — always first
2. **Session-chain handoffs** (🔗 marked) — second
3. **Other emails** (importance ≥5) — third
4. **Other open handoffs** — fourth
5. **Deferred items resurfacing** — fifth (flagged as "deferred, now due")

## Email auth setup (one-time per account)

### Gmail (2 accounts)

```python
# Requires: pip install google-api-python-client google-auth-oauthlib
# One-time: create OAuth credentials at console.cloud.google.com
# Scope: gmail.readonly
# Flow: browser-based consent (same as nlm login, silent after first time)
```

The nlm profiles already have Google OAuth tokens. The Gmail API scope
is different from NotebookLM's scope, so a separate consent is needed.
But the same `google-auth-oauthlib` flow applies — silent via CDP after
first interactive setup.

### Outlook/Hotmail (1 account)

Option A: **MS Graph API** (recommended)
```python
# pip install msgraph-sdk msal
# Register app at portal.azure.com
# Scope: Mail.Read
# Flow: device code or browser consent
```

Option B: **IMAP with XOAUTH2**
```python
# pip install imap-tools
# Connect to outlook.office365.com:993
# Auth: XOAUTH2 with MSAL token
# Basic auth deprecated since Oct 2022
```

## File layout

```
P:/.data/email-scan/
  cache.json          — shared TTL cache (scan results + deferral state)
  .lock               — file lock during scan
  credentials/
    a.hominidae.json  — OAuth tokens (refresh + access)
    troup.hominidae.json
    brsthomson.json
```

## The forgiveness principle (ADHD-specific design)

From the research (Reddit r/ADHD_Programmers, Super-Productivity guide):

> "A system that survives being ignored for a week beats one that punishes
> you for skipping a review."

Design implications:
- **No penalty for stale cache.** If `/todo` hasn't run in 3 days, the
  email scan just runs fresh. No "you have 847 unread" shame counter.
- **Deferred items resurface gently.** Not "OVERDUE" in red — just
  "deferred 4h ago, now due" in the normal list position.
- **Quick actions are one keystroke.** `defer`, `ignore`, `done` — no
  menus, no multi-step workflows.
- **The list is short by design.** Top 10 items max. If there are 200
  unread emails, `/todo` shows the top 10 by score, not all 200.

## Prior art referenced

| Source | What we borrow |
|--------|---------------|
| `abhuva/email-agent` (MIT) | Multi-account IMAP+OAuth loop, score-based classification, `$AIProcessed` keyword |
| Super-Productivity | ADHD external-memory patterns, energy-aware scheduling, forgiveness principle |
| Gmail API v1 | `messages.list` with `q='is:unread is:important'`, pagination via `nextPageToken` |
| MS Graph / IMAP XOAUTH2 | Outlook/Hotmail access via MSAL tokens |
| Augment Code study | Context-recovery cost (10-15 min), justifies unified list |
| Naive Bayes email classifier | Cheap pre-filter before LLM scoring |

## Falsifier

This design is wrong if:
- Email scanning via 3 different APIs (Gmail × 2 + Outlook × 1) proves too
  fragile to maintain (OAuth tokens expire, APIs change)
- The scoring model produces noise instead of signal (items ranked wrong)
- The deferral mechanism is gamed (operator defers everything, nothing
  ever surfaces)
- The shared cache causes stale-data bugs across terminals
- The operator stops using `/todo` because it's too slow (>10s scan)

## Receipts

- `~/.grok/skills/todo/SKILL.md` — the `/todo` orchestrator skill (built this session)
- `~/.grok/skills/close/__lib/coverage_scan.py` — workspace scanner (shared plugin, built this session)
- `~/.grok/skills/close/__lib/close_runner.py --coverage` — entry point for workspace scan
- `P:/.data/email-scan/cache.json` — planned shared email cache location
- `P:/.agents/skills/nlm-to-wiki/scripts/bin/export_yt_cookies.py` — existing profile cookie pattern (reusable for email OAuth)

## Related

- [[dynamic-wiki-driven-skill-configuration]] — same "shared plugin, per-session consumer" pattern
- [[optimal-wiki-usage-for-ai-agent-fleets]] — moment-of-action surfacing principle
- [[concurrent-cdp-auth-contention]] — multi-terminal auth isolation (email scan must avoid same pattern)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
