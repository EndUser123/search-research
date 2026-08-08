---
title: "Fix agy headless permission denial (jetski auto-deny)"
created: 2026-08-07
status: resolved
assigned_to: grok
assigned_at: ""
assigned_by: ""
priority: high
tags: [agy, antigravity, headless, permissions, tp-panel, cross-model]
---

# Fix agy headless permission denial (jetski auto-deny)

## Goal

Fix the agy (Antigravity CLI) headless permission denial that silently kills the agy lens in `/tp` 3-lens parallel panels. The fix is documented in the wiki but was never applied to the config file.

## Context

**What's happening:** when `/tp` fires its 3-lens panel (spawn + codex + agy), the agy lens returns empty output with the error:

```
jetski: no output produced — a tool required the "command" permission
that headless mode cannot prompt for, so it was auto-denied.
Add an allow-rule under permissions.allow in settings.json
(e.g. command(<target>)).
```

This occurs even when the mandatory headless flags are used (`-p --dangerously-skip-permissions --print-timeout 10m --output-format json`). The flags handle the outer permission layer; `jetski` (agy's internal tool layer) has its own permission gate that auto-denies in non-TTY mode.

**The fix is already documented.** Wiki concept `[[gemini-api-vs-agy-cli]]` line 80 (updated 2026-08-01) prescribes:

> add a `permissions.allow` section to `~/.gemini/settings.json` with entries like `"read_file"`, `"list_directory"`, and `"run_shell_command(read_file)"`.

But this was never applied to the actual config file. The settings file exists at `C:\Users\brsth\.gemini\settings.json` — it has `mcp.allowed` and `security.auth` sections but NO `permissions.allow` section.

## What was done this session

1. The `/tp {3}` panel fired with all 3 lenses. Spawn and codex returned critiques. agy returned `INVOCATION_FAILED` — empty output, jetski auto-deny.
2. The operator flagged this for a handoff.

## What needs to happen

1. **Add `permissions.allow` to `~/.gemini/settings.json`.** The entries needed (per wiki `[[gemini-api-vs-agy-cli]]`):
   ```json
   "permissions": {
     "allow": [
       "read_file",
       "list_directory",
       "run_shell_command(read_file)"
     ]
   }
   ```

2. **Verify by re-firing an agy lens.** After applying the config change, run a simple agy headless dispatch to confirm it produces real output instead of the jetski auto-deny:
   ```powershell
   agy -p --dangerously-skip-permissions --print-timeout 30s --output-format json "Reply: AGY_PERMISSION_TEST_OK"
   ```

3. **Update `[[tool-fallbacks]]` § AGY row** to note that the fix has been applied (change the wiki status from "pending live verification" to "verified fixed").

4. **Update `[[gemini-api-vs-agy-cli]]` line 80** to remove "pending live verification" note once the fix is confirmed working.

## Acceptance criteria

- [ ] `permissions.allow` section exists in `~/.gemini/settings.json` with `read_file`, `list_directory`, and `run_shell_command(read_file)`
- [ ] agy headless dispatch produces non-empty output (not the jetski auto-deny error)
- [ ] `[[tool-fallbacks]]` and `[[gemini-api-vs-agy-cli]]` updated to reflect applied fix

## Why this matters

The agy lens is 1/3 of the `/tp` parallel panel. Without it, every `/tp` critique runs at 2/3 capacity — losing the Gemini family perspective. This has been broken since at least 2026-08-01 (wiki documentation date) and has silently degraded every `/tp` 3-lens invocation since.

## Evidence

- Session 019fd9c9 terminal log: `call_955ca37d37704552b9f7c09a.log` — the jetski auto-deny output
- Wiki: `[[gemini-api-vs-agy-cli]]` line 80 — documented fix, unapplied
- Config: `C:\Users\brsth\.gemini\settings.json` — exists, lacks `permissions.allow`

## Execution Status

Updated: 2026-08-07T22:30:00Z
Session: 019fdc45-15b9-71c0-8c0c-58d000ecd1c8 (grok) + 019fde?? (claude fresh-session verification)
Agent: grok
Status: RESOLVED — fully verified end-to-end across two sessions

### Original acceptance criteria

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | `permissions.allow` in `~/.gemini/settings.json` | ✅ DONE (pre-existing) | Config already contained the section (richer than spec): `read_file`, `list_directory`, `run_shell_command(read_file)` + `cat`/`ls`/`dir`/`grep`/`type`/`Get-Content`/`python`. No edit needed. |
| 2 | agy headless produces non-empty output (no jetski auto-deny) | ✅ DONE | Smoke test: `status: SUCCESS`, `response: SMOKE_OK`, 2.4s. File-read test: `status: SUCCESS`, `response: ZX9Q7` (correct), 2.0s, 16K cache-read tokens. |
| 3 | `[[tool-fallbacks]]` + `[[gemini-api-vs-agy-cli]]` updated | ✅ DONE | `gemini-api-vs-agy-cli.md:80` — "pending live verification" → "Verified fixed 2026-08-07". `tool-fallbacks.md:112` — new row for "command permission auto-deny (jetski)". |

### Scope expansion (why this handoff grew)

The original handoff was correct but narrow — it treated the jetski auto-deny as the only blocker on the agy lens. Execution revealed it was **one of four independent failure modes** in the dispatch pipeline, all producing the same symptom (0 output from the agy lens):

1. **Permission gate (jetski auto-deny)** — the handoff's original target; already fixed, live-verified
2. **`tp_dispatch.py:build_agy_command` bare command** — emitted `agy "..."` without mandatory flags (Issue #76); the SKILL.md claimed the dispatch output included the flags but it did not
3. **`agy_lens.py:extract_stream_text` parser schema mismatch** — expected `{"type":"agent_message"}` but agy 1.11.x emits `{"event":"result","result":{"response":"..."}}`
4. **`--output-format json` polling timeout** (GH #266) — agy times out at ~300s on analytical prompts in polling mode; stream-json mode avoids it

A `/tp` panel critiquing the original fix surfaced findings 2-4. A subsequent `/risk` scan surfaced 7 additional hardening findings. A fresh-session `/tp` verification surfaced 6 more (including a gap in one of the in-session fixes).

### Full deliverable inventory

**Permission gate (original handoff scope):**
- Verified `permissions.allow` already applied to `~/.gemini/settings.json` (commit `bdc202c`)
- Updated `[[gemini-api-vs-agy-cli]]` + `[[tool-fallbacks]]` to "Verified fixed 2026-08-07"

**Dispatch pipeline fixes (discovered via in-session `/tp` panels):**
- `tp_dispatch.py:build_agy_command` — routes through `agy_lens.py` instead of bare agy (commit `75b27a0`, `58c73e6`)
- `agy_lens.py:extract_stream_text` — handles agy 1.11.x event schema + legacy schema (commits `75b27a0`, `e2af584`, `b26b54b`)

**Quota optimization (operator-flaged):**
- Pre-packed context + inlined protocol contradiction → agy burned 36 tool calls re-reading files already in context (commit `5d2cfef`)
- Structural fix: replace (not override) the protocol's tool-access section for CLI dispatch (commit `2c81495` preamble, then `58c73e6` anchor-based replacement)

**Hardening from `/risk` scan:**
- #2 SKILL.md drift — dispatch docs updated to match implementation (commit `98c6b5b`)
- #4 Conductor seam — SKILL.md now explicit about reading the `-result.md` file (commit `98c6b5b`)
- #3 Output path collision — terminal-scoped result file (commit `58c73e6`)
- #1 Regex fragility — measured (2/4 realistic edits broke), eliminated with HTML comment anchors (commit `58c73e6`)
- #5 No tests — 13 regression tests added (commit `58c73e6`)

**Fail-closed acceptance contract (in-session commit `010672a`):**
- Clean-empty extraction now returns exit 5 (was 0) with diagnostics in the output file
- Multi-field result extraction (response → text → message → output → content)
- 3 mocked-subprocess regression tests including a captured-real-schema guard

**Remaining findings (fresh-session verification, commit `20f3694`):**
- Gap in `010672a`: `clean_empty` predicate required `events_total > 0` — empty stdout (0 events) still fell through to exit 0. Split into `schema_drift` vs `empty_stream`, both exit 5 with distinct diagnostics.
- F7a: empty (0-byte) input file now fails fast (exit 2) without invoking agy
- F10: `events_error > 0` with text extracted no longer exits 0 silently — WARNING block appended to output file
- F1: removed dead `_SESSION_ID`/`_TERMINAL_ID` text from module docstring
- F11: `noterm` fallback → `noterm{pid}` (process-unique, no collision)
- F12: exit if-chain → elif (precedence explicit)
- F4: tool-fallbacks row 109 doc drift `--output-format json` → `stream-json` (commit `688686f`, P:/) — the wrong value reintroduced the ~300s hang the row documents as fixed

**Cross-cutting:**
- Wiki concept captured: `[[pre-packed-context-protocol-contradiction]]` (commit `369e9a0`) — transferable anti-pattern
- `tp_critique_log.py` missing `import os` fixed (commit `558fdbe`) — telemetry step was silently failing every `/tp` invocation

### Test receipts

- **38/38 pytest pass** across the full `tp/__lib/tests/` suite (20 in `test_agy_dispatch_pipeline.py`, 18 in sibling test files)
- **ruff clean** on `agy_lens.py` + `tp_dispatch.py`
- **End-to-end happy-path re-test** on agy 1.1.11: 874 bytes extracted, exit 0 (fresh session)
- **Stress test**: 64KB production context, 0 tool calls (down from 36), 5638 bytes real critique extracted, 44s (in-session)
- **Fail-closed verified**: schema-drift, empty-stream, empty-input, degraded-with-errors, silent-crash all produce nonzero exit + diagnostic

### Key findings during execution

- **The handoff's core premise was already satisfied** — `permissions.allow` was present, richer than spec. Verifying before acting avoided overwriting the richer config.
- **The handoff's verification command was malformed** — `-p` immediately before `--dangerously-skip-permissions` would have treated the flag as the prompt.
- **In-session `/tp` panels share the session's framing anchor.** Three cross-family panels (zen-deepseek, gpt-5.6-luna, gemini) caught the pipeline bugs but missed the exit-code fail-open gap — they all inherited the author's framing (testing the case observed, not the adjacent case). The fresh-session verification caught it because it started cold from the code. This validates the Costa & Kallick principle at session granularity, not just model granularity. Candidate wiki concept (not yet captured — needs one more instance before promotion).
- **The quota-burn finding is structurally transferable** — any skill that pre-packs context then inlines a tool-encouraging protocol has the same defect. Captured as `[[pre-packed-context-protocol-contradiction]]`.

### Commits (chronological)

P:/ repo: `0dc8e5b`, `bdc202c`, `754f8f8`, `f27bcae`, `0551f78`, `0f07e04`, `369e9a0`, `688686f`
~/.grok repo: `75b27a0`, `e2af584`, `b26b54b`, `2c81495`, `5d2cfef`, `98c6b5b`, `58c73e6`, `558fdbe`, `010672a`, `20f3694`

All commits pushed to both remotes. No unpushed state.
