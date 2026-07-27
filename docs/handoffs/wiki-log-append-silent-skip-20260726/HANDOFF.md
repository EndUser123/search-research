---
thread_id: 4f8b2c7d-9e3a-4d61-b8f1-6c0d9a7e5s21
parent_handoff_path: none
current_session_id: 019f9b00-75fc-7290-9a2d-080c3d3c529b
current_terminal_id: noterm
produced_at: 2026-07-26T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 6c9515229daffc015b886587fd2ccaa9c25442d3
assigned_to: grok
assigned_at: 2026-07-26T00:30:00Z
assigned_by: 019f9b00-75fc-7290-9a2d-080c3d3c529b
---

# Handoff — wiki_log_append.py silent-skip bug + downstream check gaps

## Objective

Fix the silent idempotency-skip bug in `wiki_log_append.py` that causes `wiki_ingest.py --post-write` to report `5_log_append: ok` without actually writing a log entry, then update the `/close` and `/aar` Phase 8.5 wiki-log checks to verify by grepping `log.md` instead of trusting the pipeline's exit status.

**Scope bounds:** Work scope is one bug fix (`_entry_already_present` scan-window) + two check upgrades (`/close` + `/aar` Phase 8.5). Not in scope: rewriting the log format, replacing the prepend-with-sentinel design, or any other wiki-lifecycle change.

## Status

**OPEN** — root cause identified this session; workaround applied (manual `append_log.py` calls); fix not implemented.

## Producing context

- Date: 2026-07-26
- Producing session: `019f9b00-75fc-7290-9a2d-080c3d3c529b` (Grok Build, model glm-5-2 inherited)
- Producing terminal: `noterm`
- Head at production: `6c9515229daffc015b886587fd2ccaa9c25442d3` (live `git rev-parse HEAD` at write time)
- Source: discovered in the final `/tp session` of session 019f9b00, after the operator asked "what's remaining?" The check found both `/close` Phase 8.5 and `/aar` Phase 8.5 had reported clear despite the wiki log being missing two entries for concepts created/updated that session.

## Read-first list (ordered, with reasons)

1. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py` — **the bug location**. Read `_entry_already_present` (lines ~46-65) and `atomic_prepend` (lines ~70-96). The idempotency check at line 52 has `head_lines = text.splitlines()[:200]` — only scans first 200 lines.
2. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_ingest.py` — **the caller that masks the bug**. Read the `5_log_append` step (lines ~176-185). It calls `wiki_log_append.py` and reports `ok` on any successful subprocess exit, including the silent-skip case.
3. `P:/.data/wiki/log.md` — **the artifact**. 4997 lines, ~297KB. The 200-line scan window misses any concept whose slug last appeared past line 200 (which is most of them now — the log has ~18 months of entries).
4. `P:/.data/wiki/scripts/append_log.py` — **the canonical workaround**. Different design (append-by-date, not prepend-after-sentinel). AGENTS.md § "Cross-agent coordination" mandates this for log writes. Used successfully in this session to add the two missing entries.
5. `C:\Users\brsth\.grok\skills\close\SKILL.md` Phase 8.5 item 5 — **downstream check gap #1**. Says "Were wiki concepts created or updated but not logged to `P:/.data/wiki/log.md`? Check for concept files newer than the last log entry." The check trusts recency rather than grepping for the specific concept filename.
6. `C:\Users\brsth\.grok\skills\aar\SKILL.md` Phase 8.5 item 5 — **downstream check gap #2**. Same wording, same gap.

**Wiki grounding (related concepts):**
- `[[documented-deferral-substitutes-for-action]]` — the same-session AAR-promoted lesson. The /close and /aar Phase 8.5 checks "trusting the pipeline's exit status" is an instance of documented-deferral at the tooling level: the check appears to verify but doesn't.
- No other wiki concepts cover the wiki-lifecycle tooling specifically.

## Verified facts (with source paths)

- [FACT] `wiki_log_append.py:_entry_already_present` scans only the first 200 lines of `log.md` for an existing entry with the same slug+type. Source: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py:52` — `head_lines = text.splitlines()[:200]`.
- [FACT] `log.md` is 4997 lines / ~297KB as of this session. Source: `Get-Content log.md | Measure-Object -Line` returned 4997; file size 297120 bytes after manual appends.
- [FACT] When `_entry_already_present` returns True, `atomic_prepend` returns `{"ok": True, "skipped": "entry already present (idempotent no-op)"}` without writing. Source: `wiki_log_append.py:73`.
- [FACT] `wiki_ingest.py` reports `5_log_append: ok` on any subprocess exit 0, including the silent-skip case. Source: `wiki_ingest.py:178-181` — the `run_subprocess` helper treats exit 0 as ok regardless of stdout content.
- [FACT] This session's two new wiki entries (`grok-build-workflows-rhai-orchestration.md` update + `documented-deferral-substitutes-for-action.md`) were silently skipped by `wiki_ingest.py`. Workaround: ran `append_log.py` manually for both. Confirmed via `Select-String -Pattern 'grok-build-workflows-rhai|documented-deferral'` — 5 matches now present after the manual append.
- [FACT] The /close and /aar Phase 8.5 item 5 checks both fired "all clear" this session despite the missing entries. They check "concept files newer than the last log entry" — a recency heuristic that misses the case where the log file is being written to by other concurrent activity (the crawl-ingest entries dated 2026-07-25 made the "last log entry" timestamp recent enough to pass the check).

## Current state

- ✅ Root cause identified: `_entry_already_present` 200-line scan window is too small for a 4997-line log
- ✅ Workaround applied: manual `append_log.py` calls for the two missing entries (committed `503371a`)
- ❌ Root cause fix NOT implemented: `wiki_log_append.py` still has the 200-line window
- ❌ `/close` Phase 8.5 item 5 check NOT upgraded to grep instead of recency-check
- ❌ `/aar` Phase 8.5 item 5 check NOT upgraded
- ❌ `wiki_ingest.py` `5_log_append` step NOT upgraded to surface the `"skipped"` field in its report (currently the ok-status masks it)

## Task packets

### AC-LOG-01 — Fix the `_entry_already_present` 200-line scan window

- **goal:** Eliminate the silent-skip false-positive by scanning the full log (or a much larger window, or by date-bounded search).
- **in scope:** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py:_entry_already_present` — change the scan from first 200 lines to either (a) full file scan, (b) scan within the current calendar month, or (c) scan within the last N entries by count. Option (b) is optimal: matches the SCHEMA.md §6 date-bucketing design and bounds cost.
- **out of scope:** Changing the entry format. Replacing prepend-after-sentinel with append. Any other wiki-lifecycle change.
- **files / anchors:**
  - `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py:46-65` (the `_entry_already_present` function)
  - `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py:52` (the specific line: `head_lines = text.splitlines()[:200]`)
- **acceptance:**
  - Re-running `wiki_ingest.py --post-write` on a concept whose slug appears >200 lines back produces a real log entry (not a silent skip)
  - The idempotency check still works for entries actually added in the same call (re-running twice in a row still skips the second)
  - Test added to `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/tests/` that reproduces the bug (concept slug in lines 201-400 of a fixture log) and verifies the fix
- **falsifier:** The fix fails if (a) it breaks idempotency for entries actually present in the recent window, (b) it regresses performance on the 5K-line log below acceptable (sub-second), or (c) re-running wiki_ingest on a previously-silently-skipped concept still doesn't write the entry.
- **verification level required:** UNIT_TEST — the function is pure-Python string processing; a fixture-log test is sufficient. No live-run needed for the function fix itself.
- **estimate:** ~30 min (read the function, change the window, add a test, run tests).

### AC-INGEST-01 — Surface `"skipped"` in wiki_ingest.py 5_log_append report

- **goal:** Stop masking silent skips. The `5_log_append` step should propagate the `"skipped"` field (and reason) from `wiki_log_append.py`'s output into its own report so the orchestrator and caller can see when an entry was NOT actually written.
- **in scope:** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_ingest.py:176-185`. Parse the subprocess stdout JSON, surface `"skipped"` and `"reason"` fields.
- **out of scope:** Changing the exit-code semantics (still 0 on idempotent-skip — idempotency is a feature, not a bug; the bug is the *false-positive* skip, which AC-LOG-01 fixes).
- **files / anchors:** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_ingest.py:178-181` and the `run_subprocess` helper.
- **acceptance:** When wiki_log_append.py returns `{"ok": True, "skipped": "..."}`, wiki_ingest.py's 5_log_append step reports `{"ok": True, "skipped": "...", "reason": "..."}` in its JSON output — not just `{"ok": True}`.
- **falsifier:** The fix fails if it changes the pipeline's overall exit code on idempotent-skip cases (would break legitimate re-runs).
- **verification level required:** UNIT_TEST.
- **dependency:** Best done after AC-LOG-01 (otherwise the surfaced "skipped" messages will still fire incorrectly).

### AC-CLOSE-CHECK-01 — Upgrade /close Phase 8.5 item 5 to grep log.md instead of recency-check

- **goal:** When /close checks "were wiki concepts created/updated but not logged," grep `log.md` for each concept filename, not "is the log file newer than the concept."
- **in scope:** `C:/Users/brsth/.grok/skills/close/SKILL.md` Phase 8.5 item 5. Change the check description from "concept files newer than the last log entry" to "for each concept created/updated this session, grep log.md for the concept filename; flag any without a matching entry."
- **out of scope:** Rewriting the scanner's wiki-log gate logic (which lives in `close_accounting.py` — if the scanner does this check mechanically, that's the place to fix it; if it's a prompt-time check, the SKILL.md update is sufficient).
- **files / anchors:** `C:/Users/brsth/.grok/skills/close/SKILL.md:570-576` (Phase 8.5 item 5). May also need `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py` if the gate is scanner-side.
- **acceptance:** A /close run after creating a wiki concept but before its log entry appears surfaces the gap as a must-fix-before-close item, regardless of whether the log file was touched by other concurrent activity.
- **falsifier:** The fix fails if it produces false positives on concepts that were legitimately logged by an older entry format (e.g., pre-SCHEMA.md §6 entries with different page-path syntax).
- **verification level required:** STATIC_INSPECTION for the SKILL.md change; LIVE_BEHAVIOR if the scanner needs updating.

### AC-AAR-CHECK-01 — Upgrade /aar Phase 8.5 item 5 (same fix as AC-CLOSE-CHECK-01)

- **goal:** Same as AC-CLOSE-CHECK-01 but for the `/aar` SKILL.md.
- **in scope:** `C:/Users/brsth/.grok/skills/aar/SKILL.md` Phase 8.5 item 5.
- **out of scope:** Same as AC-CLOSE-CHECK-01.
- **files / anchors:** `C:/Users/brsth/.grok/skills/aar/SKILL.md` (Phase 8.5 item 5, search for "Wiki concepts without log entries").
- **acceptance / falsifier:** Same as AC-CLOSE-CHECK-01.
- **dependency:** Identical fix to AC-CLOSE-CHECK-01 — do them together.

## Open decisions

**None.** The fix path is clear: scan-window bug → surface skip → grep-based checks. No operator decision needed.

## Hard constraints

1. **Do NOT change the idempotency feature itself.** Silent-skip when an entry is genuinely already present is correct behavior — re-running wiki_ingest on the same concept should not duplicate the log entry. The bug is the *false-positive* skip (entry not actually present but scan window too small to find it), not the skip mechanism.
2. **Do NOT change the log format.** SCHEMA.md §6 governs the format; this fix is purely about the scan window.
3. **Do NOT touch `append_log.py`.** It works correctly (used successfully this session as the workaround). It's a separate code path with a different design (append-by-date). The two scripts coexist; this fix is to `wiki_log_append.py` only.
4. **Run the test suite after the fix.** `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/tests/` — verify idempotency still works for same-call repeats.

## Cross-reference couplings

- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_log_append.py:52` → the 200-line scan window. THIS is the root cause.
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_ingest.py:178` → the call site that masks the silent skip.
- `C:/Users/brsth/.grok/skills/close/SKILL.md` Phase 8.5 item 5 → downstream check that trusts recency over grep.
- `C:/Users/brsth/.grok/skills/aar/SKILL.md` Phase 8.5 item 5 → same.
- `P:/.data/wiki/scripts/append_log.py` → the canonical alternative (works correctly, not in scope).
- `~/.grok/AGENTS.md` § "Cross-agent coordination" → mandates `append_log.py` for log writes. This handoff does NOT propose changing that rule — the rule is correct; the bug is that the pipeline option (`wiki_ingest.py`) doesn't actually fulfill its mandate.
- This handoff's `accurate_as_of_head` → `6c951522…`. If HEAD moves before the fix lands, the line numbers in "files / anchors" should still resolve (they're stable source files not actively being edited).
- `[[documented-deferral-substitutes-for-action]]` → the meta-pattern. The /close and /aar checks trusting pipeline exit-status is a tooling-level instance of documented deferral: the check appears to verify but doesn't.

## Other outstanding streams (not handed off)

- **`/www` workflow POC (AC-WWW-POC-01)** — already handed off at `P:\docs\handoffs\grok-workflow-skill-adoption-20260725\HANDOFF.md`. Independent of this handoff.
- **O2 INVESTIGATE from /aar** (detect documented-deferral pattern as a /close gate) — cross-session INVESTIGATE, lifecycle-gated. Independent.

## Explicit non-goals

- **Do NOT rewrite wiki_log_append.py's atomic-prepend design.** It's correct; only the scan window is wrong.
- **Do NOT replace wiki_ingest.py with append_log.py.** They serve different purposes; both should work.
- **Do NOT add a hook that auto-runs append_log.py on every wiki concept write.** That papers over the bug; the bug should be fixed.
- **Do NOT promote the documented-deferral pattern to an AGENTS.md rule based on this session alone.** AAR governance rule 11 requires cross-session evidence. This handoff's existence is one data point; if the pattern recurs in 2+ more sessions, then promote.

## Resumption protocol

1. **Read** `wiki_log_append.py:46-65` to confirm the bug is still present (line 52: `head_lines = text.splitlines()[:200]`).
2. **Read** `wiki_ingest.py:176-185` to confirm the call site still masks the skip.
3. **Start with AC-LOG-01** (the root cause fix). One file, one function, one line change plus a test. Smallest sufficient intervention.
4. **Then AC-INGEST-01** to surface the skipped field (so future silent skips are visible even if the window regresses).
5. **Then AC-CLOSE-CHECK-01 + AC-AAR-CHECK-01 together** (identical fix in two SKILL.md files).
6. **Run the wiki test suite** after each fix.

## Suggested next invocation

Copy-paste for the next session:

```
I'm picking up the wiki_log_append.py silent-skip bug from handoff
P:\docs\handoffs\wiki-log-append-silent-skip-20260726\HANDOFF.md.

Root cause: wiki_log_append.py:52 scans only first 200 lines of log.md
(currently 4997 lines) for idempotency. False-positives on any concept
whose slug last appeared past line 200.

Start with AC-LOG-01: change the scan window in _entry_already_present
to date-bounded (current calendar month) instead of first 200 lines. Add
a test fixture with a 400-line log and a concept slug at line 250.
Verify idempotency still works for same-call repeats.

Then AC-INGEST-01 (surface "skipped" field in wiki_ingest.py 5_log_append
report) and AC-CLOSE-CHECK-01 + AC-AAR-CHECK-01 (grep log.md instead of
recency-check in Phase 8.5 item 5).

Do NOT change the idempotency feature itself — only the false-positive
scan window. Do NOT replace wiki_ingest.py with append_log.py; both
should work correctly.
```

## Last user message (verbatim)

> "/handoff"

## Epistemic labels per claim

- **[FACT]** All "Verified facts" cite specific file:line or command output from this session.
- **[INFERENCE]** The recommendation to use date-bounded scan (current calendar month) as the fix is inferred from SCHEMA.md §6's date-bucketing design — it's the natural match for how the log is structured. Not verified; alternative windows (full file, last N entries) are defensible.
- **[INFERENCE]** "The fix is ~30 min" is inferred from the function's size (20 lines) and simplicity. Could be longer if the test fixture is non-trivial.
- **[UNKNOWN]** Whether `close_accounting.py` (the scanner) implements Phase 8.5 item 5 mechanically or whether it's a prompt-time check. If scanner-side, AC-CLOSE-CHECK-01 needs a code change too; if prompt-side, the SKILL.md update is sufficient. The next session should check this before starting AC-CLOSE-CHECK-01.

## Falsifier (handoff-level)

This handoff is wrong if:

1. The bug is NOT in `_entry_already_present`'s scan window — e.g., if reproduction shows entries ARE being written but to a different location, or the bug is actually in atomic_prepend's tmp-file handling. Verify by adding a print statement to `_entry_already_present` and observing the return value for a known-distant slug.
2. The fix is larger than the handoff implies — e.g., if the function has hidden coupling to the 200-line window that breaks when changed. Verify by running the test suite after the change.
3. The /close and /aar Phase 8.5 checks are already grep-based (in which case AC-CLOSE-CHECK-01 and AC-AAR-CHECK-01 are no-ops). Verify by re-reading the SKILL.md sections.

If any pattern appears, update this handoff or close it before investing in the fix.
