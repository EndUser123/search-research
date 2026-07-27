---
thread_id: close-pipeline-friction-20260726
parent_handoff_path: none
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
current_terminal_id: console_c0d59c27-a0ec-424a-b5d6-cb19fc5f7c0b
produced_at: 2026-07-26T23:55:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c8a34ce12a38ab0c0f33778ea07358266d9598d4
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8b39-95e3-7121-a8de-4e3f117e511a\chat_history.jsonl
---

# Handoff: Close-pipeline friction — 3 fixes (continuation_coverage, gitleaks, index_skills)

## Objective

Fix three related friction points in the /close pipeline that surfaced during session 019f8b39's close run. All three are mechanical issues with verified root causes — each has a concrete, scoped fix. They cluster because they all produce "close gets blocked or bloated by stuff that isn't this session's work."

**Scope bounds:** Investigation + recommendation. The fixes themselves are surgical (1-10 lines each) but should be implemented as a cluster since they share the symptom "close-pipeline produces noise that obscures the signal."

## Status

OPEN — root causes verified this session; implementation deferred to a fresh session.

## Producing context

- **Date:** 2026-07-26
- **Producing session-id:** 019f8b39-95e3-7121-a8de-4e3f117e511a
- **Producing terminal-id:** console_c0d59c27-a0ec-424a-b5d6-cb19fc5f7c0b
- **Host/version:** Grok Build
- **Trigger:** /tp session (NOW/NEXT/LATER/FILTER pass) identified these as Cluster 1 (close-pipeline friction). All three forced manual intervention during the close run for session 019f8b39.

## Read-first list (ordered)

1. **`P:/.githooks/pre-commit`** — the gitleaks hook (N4 root cause lives here, lines 65-78).
2. **`~/.grok/skills/close/__lib/continuation_coverage.py`** lines 401-429 — the transcript goal-extraction logic (N3 root cause).
3. **`P:/.data/wiki/scripts/index_skills.py`** header + design — the full-regen design (N7 root cause).
4. **`P:/.artifacts/continuation-coverage-019f8b39.json`** — the false-positive candidate that forced manual disposition this session.

## Verified facts (with receipts)

- [FACT] **N3 root cause** (`continuation_coverage.py:401-417`): The `extract_transcript_goals` function strips `<user_info>` blocks from the first user message but does NOT strip `<git_status>`, `<system-reminder>`, or `<skill_information>` blocks. On Grok Build, the session's first user message contains `<user_info>` + `<git_status>` + `<system-reminder>` + `<user_query>` — the code finds the `<git_status>` content (length > 10) and treats it as the opening goal. Receipt: `grep` on `continuation_coverage.py` for `user_info` shows only that one block type is stripped; lines 406-413.
- [FACT] **N4 root cause** (`P:/.githooks/pre-commit:65-78`): The gitleaks scan iterates staged files and invokes `gitleaks detect --source "$f"` per file. With 970+ staged files (wiki source stubs from `index_skills.py`), that is 970 separate gitleaks process spawns. Each writes to a shared `$GL_REPORT` path (`$(git rev-parse --git-path gitleaks-scan.json)`) then `rm -f`s it. The "Device or resource busy" error on `rm` occurs when antivirus or another process holds the file. Total wall-clock for 970 files: 3-8 minutes. Receipt: terminal log `call_8123ccff4fa0482c95dc2438` shows `rm: cannot remove '.git/gitleaks-scan.json': Device or resource busy`.
- [FACT] **N7 root cause** (`index_skills.py:1-14`): The script is designed as full-regen — header says "Regenerate after adding/removing skills." It rewrites all stubs on every run. When only 2 concepts changed, it produces 970+ file diffs (every marketplace/cache stub). This is what triggered N4. Receipt: `head -80 index_skills.py` shows no incremental logic; the script walks all SCOPES unconditionally.
- [FACT] **N6 resolves clean**: A grep for `P:/.grok/skills/` across `~/.grok/skills/` returns only 1 match — the AAR SKILL.md line 74 explanatory note I wrote this session (which describes the bug, not a path reference). No other skills have the path bug. Receipt: `grep -rn "P:/\.grok/skills/" ~/.grok/skills/`.

## Lifecycle block

- **Hypothesis:** Fixing all three issues reduces /close wall-clock time by >50% on sessions that touch wiki or large file sets, and eliminates the false-positive continuation candidate on every Grok Build session.
- **Success signal:** Next /close run on a session with wiki edits (a) produces zero false-positive continuation candidates, (b) commits wiki stub changes in <30s, (c) does not encounter gitleaks lock errors.
- **Failure signal:** Any of the three symptoms recurs after the fixes ship.
- **Retirement condition:** All three fixes implemented and validated on one clean /close run.
- **Trigger for action:** Fresh session with bandwidth for close-pipeline work.
- **Review cadence:** Next /close run after fixes ship.
- **Exit condition:** All three fixes merged + one clean /close validates.

## Task packets

### TK-FIX-N3: continuation_coverage.py — strip all system-context blocks

**Goal:** Extend `extract_transcript_goals` (lines 401-417) to strip `<git_status>`, `<system-reminder>`, and `<skill_information>` blocks in addition to `<user_info>`. If a `<user_query>` block remains after stripping, use that as the goal text.

**In scope:** Edit to `~/.grok/skills/close/__lib/continuation_coverage.py` only.

**Out of scope:** Changing the candidate schema or the continuation_coverage system design.

**Files / anchors:** `~/.grok/skills/close/__lib/continuation_coverage.py:401-417` (the `for idx, text in user_messages:` loop with the block-stripping logic).

**Acceptance:** Running `continuation_coverage.py` on session 019f8b39 produces zero candidates with source_class `user_goal` from the `<git_status>` block. The actual user goal (`/aar has been updated`) is extracted correctly OR (if it appears in a later user message) is captured from there.

**Falsifier:** If the fix breaks extraction for sessions that legitimately embed `<user_query>` in the first message, the regex is too aggressive.

**Verification level required:** UNIT_TEST (mock the first user message with `<git_status>` + `<user_query>` blocks; assert the extracted goal is the `<user_query>` content, not the `<git_status>` content).

**Estimate:** ~20 min (regex extension + 1 test).

### TK-FIX-N4: gitleaks pre-commit — batch scan or skip regenerable stubs

**Goal:** Eliminate the 3-8 minute gitleaks wall-clock on large staging sets.

**Options (in priority order):**
1. **Batch gitleaks scan** — invoke `gitleaks detect --source . --no-git --no-banner --config ...` once on the full staged set (using `git diff --cached` piped via stdin or a single `--source` call) instead of per-file. Loses per-file path fidelity but gitleaks 8+ supports staged-content scanning.
2. **Skip regenerable files** — add `.gitleaksignore` patterns for `/.data/wiki/sources/skills/` (the index_skills.py stubs are regenerable pointers, not source-of-truth content).
3. **Use unique report files per scan** — change `$GL_REPORT` to include a PID or hash so concurrent scans don't lock the same file. Fixes the "Device or resource busy" symptom but not the wall-clock.

**Recommended:** Option 2 (`.gitleaksignore` for regenerable stubs) is the cheapest fix and addresses the immediate symptom. Option 1 is the structural fix but risks losing path-based suppression fidelity (documented in `gitleaks.toml` lines 15-18 as the reason per-file scan exists).

**In scope:** Edit to `P:/.gitleaksignore` (Option 2) OR `P:/.githooks/pre-commit` (Options 1, 3).

**Files / anchors:** `P:/.githooks/pre-commit:65-78`; `P:/.gitleaksignore` (may not exist yet — create if going with Option 2).

**Acceptance:** Committing 970+ staged files in `/.data/wiki/sources/skills/` completes in <30s without gitleaks scan errors.

**Falsifier:** If `.gitleaksignore` is too broad and a real secret in a wiki stub slips through, Option 2 is wrong. (Stubs are auto-generated from SKILL.md frontmatter, so this is unlikely — but the falsifier must be stated.)

**Verification level required:** OBSERVED (stage 970+ wiki stubs, commit, time it).

**Estimate:** ~10 min for Option 2; ~30 min for Option 1.

### TK-FIX-N7: index_skills.py — incremental regeneration

**Goal:** Make `index_skills.py` only rewrite stubs whose source SKILL.md has changed (compare mtime), instead of rewriting all stubs on every run.

**In scope:** Edit to `P:/.data/wiki/scripts/index_skills.py`.

**Out of scope:** Changing the stub format or the catalog concept format.

**Files / anchors:** `P:/.data/wiki/scripts/index_skills.py` (full file — the SCOPES-driven walk at lines 40+).

**Acceptance:** Running `index_skills.py` after adding 1 skill rewrites only that 1 stub + the catalog concept. The other 977 stubs are untouched (no diff).

**Falsifier:** If mtime comparison misses a change (e.g., timezone drift, file copied with old mtime), the catalog goes stale silently. Mitigation: add a `--force` flag that does full regen, and document running `--force` monthly.

**Verification level required:** OBSERVED (add 1 stub, run script, verify only 1 stub changed).

**Estimate:** ~30 min (read the script's current structure, add mtime comparison, test).

**Alternative (cheaper):** gitignore the stubs entirely. They're regenerable pointers; committing them adds noise (every index run = 970 diffs) without value. If gitignored, `index_skills.py` runs as a local pre-step before `/wiki` queries but doesn't touch git. **Trade-off:** the catalog concept (`skill-catalog.md`) should stay tracked (it's the human-readable index), but the 977 stub files could be gitignored.

## Open decisions

### D1: Which N4 fix?

**Options:** (a) `.gitleaksignore` for stubs (cheap, narrow), (b) batch gitleaks scan (structural, risks path fidelity), (c) per-PID report files (fixes lock, not wall-clock).

**Currently leading:** (a) — cheapest, addresses the symptom, low risk. The structural fix (b) is documented in the gitleaks.toml comments as the reason per-file scan exists, so reverting to batch is non-trivial.

### D2: Gitignore stubs vs incremental index_skills?

**Options:** (a) gitignore `/.data/wiki/sources/skills/*.md` stubs (eliminates N7 and N4 together), (b) make `index_skills.py` incremental (keeps stubs tracked, eliminates N7's diff-blast).

**Currently leading:** (a) — stubs are regenerable pointers, not source-of-truth. Gitignoring them eliminates both the diff-blast AND the gitleaks-scan issue in one move. The catalog concept (`skill-catalog.md`) stays tracked.

## Hard constraints

- **No breaking the close pipeline.** All fixes must be validated on one clean /close run before declaring done.
- **Edit-verify pattern.** Every edit requires read-back.
- **gitleaks security posture.** Don't disable secret scanning; scope it correctly.

## Cross-reference couplings

- `P:/.githooks/pre-commit` → N4 fix target.
- `~/.grok/skills/close/__lib/continuation_coverage.py` → N3 fix target.
- `P:/.data/wiki/scripts/index_skills.py` → N7 fix target.
- AAR report `P:/.artifacts/aar/019f8b39-95e3-7121-a8de-4e3f117e511a/aar-report.md` → documents the close-run friction at a high level.

## Explicit non-goals

- **Do NOT redesign the continuation_coverage system.** Just fix the block-stripping regex.
- **Do NOT redesign the gitleaks hook architecture.** Just scope it correctly for regenerable files.
- **Do NOT change the wiki stub format.** Just make regeneration incremental (or gitignored).

## Resumption protocol

1. Read this handoff's three task packets.
2. Decide D1 and D2 (recommendation: N4=Option 2 `.gitleaksignore`, N7=Option (a) gitignore stubs).
3. Implement TK-FIX-N3 (continuation_coverage block-stripping) — ~20 min.
4. Implement TK-FIX-N4 (`.gitleaksignore` for stubs) — ~10 min. (Becomes moot if N7 is fixed via gitignore.)
5. Implement TK-FIX-N7 (gitignore stubs) — ~5 min (one `.gitignore` line + `git rm --cached` the existing stubs).
6. Run one /close on a session with wiki edits and verify all three symptoms are gone.

## Suggested next invocation

```
Fix close-pipeline friction. Read
P:/docs/handoffs/close-pipeline-friction-20260726/HANDOFF.md.

Three fixes, all verified root causes:
- N3: continuation_coverage.py extracts <git_status> as user_goal (strip more blocks)
- N4: gitleaks pre-commit scans 970 files individually (scope to non-regenerable)
- N7: index_skills.py rewrites all stubs every run (gitignore the stubs)

Recommended: D1=Option 2 (.gitleaksignore), D2=Option (a) gitignore stubs.
N7 gitignore subsumes N4 — if stubs are gitignored, gitleaks never sees them.

Implement in order N3 → N7 → N4 (or N3 → N7 if N7 makes N4 moot).
Validate on one /close run.
```

## Last user message (verbatim)

> "great ideas, please do all recommendation."

(context: user approved all /tp session recommendations. This handoff covers Cluster 1: N3+N4+N7 close-pipeline friction fixes.)

## Epistemic labels per claim

- [FACT] N3 root cause verified by reading `continuation_coverage.py:401-417` — only `<user_info>` is stripped.
- [FACT] N4 root cause verified by reading `P:/.githooks/pre-commit:65-78` — per-file gitleaks scan + shared `$GL_REPORT` path.
- [FACT] N7 root cause verified by reading `index_skills.py:1-14` header — full-regen by design.
- [FACT] N6 resolves clean — grep across `~/.grok/skills/` returned only the AAR explanatory note.
- [INFERENCE] Option (a) gitignore stubs is the cheapest combined fix for N4+N7 — plausible but depends on whether qmd search works without tracked stubs.
- [UNKNOWN] Whether gitleaks batch scan loses path fidelity in practice — documented risk in `gitleaks.toml` but not tested.
