---
title: "Session: claude-mem-grok provider fix + uncertainty_gate v3 + RCA"
session: 019ffbf4-6734-77a3-bec3-ef4ae502814e
date: 2026-08-13
status: open
host: grok
tags: [claude-mem, uncertainty-gate, bun-runner, groq, nltk, rca, hook-design]
---

# Session handoff

## What shipped (all committed + pushed)

### 1. claude-mem-grok bun-runner stdin fix
- **Problem:** `process.stdin.on('data')` doesn't fire for piped stdin on Windows
  Node.js. Every hook got 0 bytes → CAPTURE_BROKEN → killed child process.
- **Fix:** Replaced async `collectStdin()` with synchronous `fs.readFileSync(0)`.
- **File:** `~/.grok/plugins/claude-mem-grok/scripts/bun-runner.js`
- **Commit:** `ba52c7a` (~/.grok repo)

### 2. claude-mem-grok provider switch: Gemini → Groq
- **Problem:** Gemini quota temporarily rate-limited (503s + empty responses).
  Worker accepted observations but couldn't compress them.
- **Fix:** Set `CLAUDE_MEM_PROVIDER=openrouter` with
  `CLAUDE_MEM_OPENROUTER_BASE_URL=https://api.groq.com/openai/v1` pointing
  directly at Groq. Model: `openai/gpt-oss-20b`.
- **File:** `~/.claude-mem/settings.json` (not in git — user data)
- **Worker port:** Changed from 37778 → 37780 (stale sockets on old ports)
- **Verified:** Two observations stored in DB (obsId 6366, 6367) via Groq.

### 3. uncertainty_gate v3: three-tier hedge detection
- **Problem:** Pure regex missed standalone "likely" + verb, fired false
  positives on quoted examples, couldn't resolve polysemy.
- **Fix:** Three-tier architecture: structural parser (markdown context) +
  regex candidates (4 patterns) + NLTK POS disambiguation (lazy-loaded).
- **File:** `~/.grok/hooks/scripts/uncertainty_gate.py`
- **Test suite:** `P:/tmp/test_uncertainty_v3.py` (17/17 passing)
- **Backups:** `.bak` (original), `.bak2` (v2 regex+structural)
- **Commit:** `ba52c7a` (~/.grok repo)
- **Wiki concept:** `[[three-tier-hedge-detection-regex-structural-nltk]]`

### 4. scheduled_checks.py: date check type
- **Problem:** Only `github_issue` check type existed; needed date-triggered
  reminder for Groq model deprecation on Aug 16.
- **Fix:** Added `check_date()` function + `groq-llama-deprecation-aug16` entry.
- **Commit:** `4edf661` (P:/ repo)

### 5. RCA: agent behavior pattern + hook gaps
- ** RCA target:** Why the agent repeatedly reasons before searching despite
  rules and hooks existing to prevent it.
- **Root cause:** Prose rules have ~50% compliance ceiling under session
  pressure (documented in AGENTS.md). The fix is mechanical enforcement
  (hooks, gates), not behavioral reminders.
- **Hook gaps found:** (1) regex pattern gap ("likely" standalone), (2)
  WindowsPath crash in FAIL_LOG, (3) quoted-example false positives.

## Open items

### claude-mem-grok NOT re-enabled yet
The plugin is disabled in config.toml. Before re-enabling:
1. **Reduce PostToolUse hook timeout** from 120 to 10 seconds (Grok runs hooks
   synchronously; `"async": true` is ignored — verified via docs line 467).
2. **Reduce Stop hook timeout** from 120 to 30 seconds.
3. **Verify worker on port 37780** is still alive after session restart.
4. **Clean up stale ports:** Ports 37778 and 37779 have zombie sockets from
   dead worker processes. May need OS-level socket cleanup or reboot.
5. **Test end-to-end:** After re-enabling, verify observations land in DB.

### Hooks.json timeout changes NOT applied
The PostToolUse and Stop hook timeouts in
`~/.grok/plugins/claude-mem-grok/hooks/hooks.json` still say 120 seconds.
Need to reduce before re-enabling. See open item above.

### /dream not yet run
Was recommended as next step but session was wrapping up. Run in a fresh
session — it reads 90 days of handoffs and synthesizes patterns.

### Session corrections worth capturing
5+ operator corrections this session, all the same pattern class: agent
reasons before searching workspace knowledge. The uncertainty_gate v3 is
the structural fix for the linguistic signal; the deeper fix is a
search-before-answer mechanical gate (UserPromptSubmit or response-level).

## Verification

- bun-runner stdin fix: verified via live probe (133KB received via sync read)
- Groq provider: verified via two observations stored in DB
- uncertainty_gate v3: 17/17 tests passing
- scheduled_checks date type: verified via `--list` output
- Push: both repos pushed (ba52c7a, 4edf661), secret scans passed
