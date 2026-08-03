---
thread_id: 019fa8f8-todo-rns-20260803
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-03T07:38:00-06:00
status: open
handoff_type: implementation
accurate_as_of_head: f7f8706
---

# Handoff: /todo RNS renderer + scanner overhaul

## 1. Objective

Port the Claude-side RNS action renderer to Grok Build, integrate it into
/todo, fix the scanner's session isolation, add a transcript scanner for
unpersisted action items, and replace Claude-oriented domains with
operator-oriented categories.

## 2. Status

OPEN — renderer ported and working, scanner session-isolated, transcript
scanner built with tuning. Several deferred improvements remain.

## 3. Producing context

This session's /todo work produced 15+ commits across two work phases:

**Phase 1: RNS renderer port + integration**
- Ported `render_rns.py` from `cc-skills-analysis/skills/recap/__lib/`
- Adapted for Grok Build: emoji priority dots → text tags ([CRIT], [HIGH], etc.)
- Replaced Claude domains (QUALITY, TESTS, DOCS, etc.) with operator domains
  (DO NOW, FIX, CAPTURE, MAINTAIN, BACKLOG)
- Added `classify_scan_item()` and `infer_action_type()` helpers
- Added `scan_transcript.py` — extracts numbered recommendations from
  chat_history.jsonl and checks if they were persisted
- Updated SKILL.md Step 6 with renderer instructions + presentation rule
  ("output IS the response, no code block")
- Removed code block from /tp actionable recommendations format

**Phase 2: Scanner fixes + tuning**
- Fixed handoffs scanner: `len(parts) >= 4` was wrong (actual output has
  3 columns); changed to `>= 3`. Bug found by sibling session 019fbf77.
- Added session isolation to scan_review_findings() and scan_check_failures()
  via `_session_artifacts_dir()` — scans only console_<short_sid> directory
- Tuned transcript scanner: position-aware persist check, tighter recommendation
  filter, semantic dedup, /tp improve format support
- 5 review findings fixed (missing source keys, stale domain names, silent
  fallback warning, carryover numbering collision, empty input handling)

## 4. Remaining work

### NEXT-1: Tighten persist-detection in transcript scanner

The `_check_persisted_after()` function uses keyword proximity matching (300-char
window, 2+ distinctive keywords near commit/file patterns). This produces some
false negatives (items marked as persisted when they weren't) and false positives
(items marked as unpersisted when they were). Needs empirical tuning with a
labeled test set.

**Acceptance criteria:** 80%+ precision on a 20-item labeled test set from
this session's transcript.

### NEXT-2: Add scan for superseded files

The sibling session identified that dead code (e.g., fusion.html should be
deleted) has no scan source. The scanner doesn't detect files that were
replaced by newer versions. Would need a git-based approach: find files
that haven't been imported/referenced in N days.

### NEXT-3: Wire renderer directly into scan_functions.py output

Currently the LLM must manually build CrossSessionAction objects from the
scanner JSON and call format_rns_output(). The proper integration would
have scan_functions.py optionally call the renderer when --format rns is
passed, producing the final output in one call.

### LATER-1: Behavioral findings gap

/tp session and /tp improve produce evaluative findings (correction patterns,
behavioral analysis) that don't have numbered format. The transcript scanner
catches numbered items but not evaluative prose. The structural fix is either
extending the scanner to detect behavioral finding patterns, or making /tp
session's harvest write fire via code instead of behavioral rule.

## 5. Key decisions

- **Operator-oriented domains over Claude RNS domains:** the Claude domains
  (QUALITY, TESTS, DOCS, SECURITY, PERFORMANCE, GIT, DEPS) are oriented toward
  PR review. The operator asks "what should I do next?" — the domains should
  match that mental model (DO NOW, FIX, CAPTURE, MAINTAIN, BACKLOG).
- **Code-rendered output over LLM-formatted:** the renderer produces deterministic
  output with domain grouping, priority tags, and hierarchical numbering. The LLM
  fills in the analysis (building CrossSessionAction objects), not the formatting.
- **Session isolation as default:** scanner searches only the current session's
  artifact directory. Falls back to all artifacts only with stderr warning.
- **Transcript scanner as 11th source:** reads chat_history.jsonl directly, no
  dependency on /tp or any other skill writing harvest files.

## 6. Source files

- `~/.grok/skills/todo/__lib/render_rns.py` (NEW — ported + adapted)
- `~/.grok/skills/todo/__lib/scan_transcript.py` (NEW)
- `~/.grok/skills/todo/__lib/scan_functions.py` (MODIFIED — session isolation, handoffs fix, transcript source)
- `~/.grok/skills/todo/SKILL.md` (MODIFIED — Step 6 renderer instructions, domain table, presentation rule)
- `~/.grok/skills/tp/SKILL.md` (MODIFIED — code block removal from recommendations)
- Commits: 0348867, 4da236a, 46f642d, 621e224, ecde532, 0464774, 0eebf8c, 4f0b0ed, f7f8706

## Suggested next invocation

```
/go Fix the transcript scanner persist-detection false positives in scan_transcript.py. Start with _check_persisted_after() — tighten the keyword matching threshold and proximity window. Then wire the renderer directly into scan_functions.py so the LLM doesn't need to manually build CrossSessionAction objects. Verify: python scan_functions.py --json produces correctly classified items with no false positives on this session's transcript.
```
