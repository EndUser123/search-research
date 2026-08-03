---
thread_id: a7b8c9d0-1e2f-3a4b-5c6d-7e8f9a0b1c2d
parent_handoff_path: none
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T23:00:00Z
status: CLOSED
handoff_type: bug
accurate_as_of_head: 5ef88d7
---

# Close scanner gate robustness: 2 false-positive gates from design-doc + system-prompt parsing

## Objective

Fix two close-scanner gates that produce false positives during `/close` because they don't classify the source type of what they're parsing. Both gates treat structurally different inputs as the same type, forcing manual explanation on every `/close` that touches design work.

## Status

OPEN — bugs identified and verified during session 019fa39d `/close` run; fixes not started.

## Root cause (shared)

Both gates lack **source-type classification**. They treat all "missing file" or "goal-like text" signals as the same category, regardless of whether the source is:
- A design-doc forward reference (file marked "(new)" — supposed to be created during future implementation)
- A system-prompt context block (`<git_status>`, `<system-reminder>`)
- Actual stated intent that was silently lost (the real failure mode the gate exists to catch)

The gates correctly detect the surface signal but can't distinguish the categories that matter.

## Read-first list

1. `~/.grok/skills/close/__lib/close_accounting.py` — both gates live here (`scan_referenced_files`, `continuation_coverage`)
2. `~/.grok/skills/close/__lib/continuation_coverage.py` — the extractor that parses goals from the transcript
3. `~/.grok/skills/close/SKILL.md` — gate-specific guidance sections for `referenced_files` and `continuation_coverage`
4. `P:/docs/handoffs/session-observations-019fa39d-20260727/HANDOFF.md` observation #4 — the continuation_coverage false positive

## Verified facts

- [FACT] `referenced_files` gate flags 6 files as "not found on disk" — receipt: close_accounting.py scan output during this session's /close, gate detail `"6 file(s) referenced in handoffs but not found"`
- [FACT] All 6 files are design-doc forward references marked "(new)" in their handoffs — receipt: grep across `wiki-query-stop-hook-20260727/HANDOFF.md` shows every path annotated with "(new)"; same for `workspace-improvement-opportunities-20260727` and `routine-skill-improvement-cadence-20260727`
- [FACT] `continuation_coverage` gate extracted the `<git_status>` block from the session's system prompt as the opening goal — receipt: `P:/.artifacts/continuation-coverage-019fa39d.json`, candidate `goal_opening_4b5e14fa648e`, title starts with `"<git_status> This is the git status..."`
- [FACT] The candidate was manually rejected with `REJECTED` disposition to unblock the close — receipt: the same ledger file, updated during this session
- [FACT] Both gates block `/close` with CLOSE INCOMPLETE until manually resolved — receipt: close_runner.py exit code 1 on both gate states

## Task packets

### BUG-01: Add design-doc forward-reference classification to `referenced_files` gate

- **problem:** The gate scans handoff files for file paths, then checks if each path exists on disk. If a path doesn't exist, it flags it as "referenced but not found." But design handoffs legitimately reference files that WILL be created during future implementation — these are forward references marked "(new)", not dangling intent. The gate treats both as the same failure.
- **root cause:** `scan_referenced_files` checks file existence but doesn't classify the reference type. It has no way to distinguish "file was supposed to exist by now" from "file is an implementation target for a future session."
- **fix approach:** When a referenced file doesn't exist, check the surrounding context in the handoff for forward-reference markers: `(new)`, `COMMIT_THIS_SESSION`, `HANDOFF`, or a unit/task-packet structure that marks the file as an implementation target. If the context indicates a forward reference, classify as `FORWARD_REFERENCE` (informational, not blocking) instead of `MISSING` (blocking).
- **in scope:** `scan_referenced_files` function in `close_accounting.py`; possibly a context-window read around each missing path
- **out of scope:** changing the handoff format or adding a formal "forward reference" syntax
- **acceptance:** the 6 files from this session's design handoffs classify as `FORWARD_REFERENCE`, not `MISSING`; the gate state becomes `pre_satisfied` or `needs_llm_check` (informational) instead of `needs_attention`
- **falsifier:** if the context-based classification produces false negatives (flags a real dangling intent as a forward reference), the classification logic is too broad
- **verification:** re-run `/close` on this session after the fix — the `referenced_files` gate should not block
- **disposition:** HANDOFF

### BUG-02: Filter system-prompt blocks in `continuation_coverage` goal extraction

- **problem:** The extractor reads `chat_history.jsonl` line 1 to find the session's opening goal. But line 1 of a Grok Build transcript contains the system prompt, which includes structured blocks like `<git_status>`, `<system-reminder>`, and `<user_info>`. The extractor parsed the `<git_status>` block as the opening goal, producing a false-positive continuation candidate.
- **root cause:** `continuation_coverage.py` (or the extraction function in `close_accounting.py`) doesn't filter XML-tagged context blocks from the goal extraction. It treats the first text block as a goal regardless of whether it's system-injected context.
- **fix approach:** Before extracting a goal from the transcript, strip or skip content inside these tags: `<git_status>`, `<system-reminder>`, `<user_info>`, `<system-reminder>`, `<skill_information>`. Alternatively, only extract goals from messages with `"type":"user"` and `"role":"user"`, not from the system-prompt preamble.
- **in scope:** the goal extraction logic in `continuation_coverage.py` or `close_accounting.py`
- **out of scope:** the full continuation coverage system (only the extraction filter)
- **acceptance:** re-running the extractor on this session's transcript produces 0 candidates (or only real user goals), not the `<git_status>` block
- **falsifier:** if the filter strips a real user goal that happens to contain angle brackets or XML-like syntax, the filter is too aggressive
- **verification:** re-run `/close` on this session after the fix — the `continuation_coverage` gate should produce 0 false-positive candidates
- **disposition:** HANDOFF

## Open decisions

None — both fixes are scoped and the fix approaches are clear.

## Resumption protocol

1. Read `close_accounting.py` — find `scan_referenced_files` and the continuation coverage extraction logic
2. Start with BUG-02 (simpler — add a tag filter to the extraction function)
3. Then BUG-01 (requires context-window logic around each missing path)
4. Test by re-running `/close` on session `019fa39d` — both gates should resolve without manual intervention

## Suggested next invocation

```
/go "Fix two close-scanner false-positive gates. BUG-02: continuation_coverage extractor parses <git_status> from the system prompt as a goal — filter XML-tagged context blocks from goal extraction in continuation_coverage.py. BUG-01: referenced_files gate flags design-doc forward references (files marked '(new)') as missing — add context-based classification to distinguish forward references from dangling intent in scan_referenced_files in close_accounting.py. Test by re-running /close on session 019fa39d-ff7a-7372-96c8-d8b980ec2e88."
```

## Cross-reference couplings

- `P:/docs/handoffs/session-observations-019fa39d-20260727/HANDOFF.md` observation #4 — the continuation_coverage false positive
- `~/.grok/skills/close/SKILL.md` — gate-specific guidance for `referenced_files` and `continuation_coverage`
- `P:/.artifacts/continuation-coverage-019fa39d.json` — the ledger where the false positive was manually rejected

## Explicit non-goals

- Do NOT change the handoff format to require formal forward-reference syntax
- Do NOT remove the gates — they catch real failures; they just need source-type classification
- Do NOT merge the two fixes into one — they're in different code paths with different fix approaches
