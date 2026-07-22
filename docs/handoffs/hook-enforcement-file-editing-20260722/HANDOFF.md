---
thread_id: 09e4308c-4c6e-41e4-95c3-f3d12bb800ed
parent_handoff_path: none
current_session_id: 019f8523-d9f7-73c3-9e25-9e6c417cfccd
current_terminal_id: console_ec84a662-c26f-40e0-b5f0-3b1d
produced_at: 2026-07-22T15:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c629aa1f61ecfbdbaa2a4390d955c7a47605c880
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8523-d9f7-73c3-9e25-9e6c417cfccd\chat_history.jsonl
---

# Handoff: 3-hook enforcement for file-editing protocol

## 1. Objective (one sentence)

Implement the 3 PreToolUse hooks recommended in the file-editing protocol review: Write ban on existing files, destructive-git block, read-before-write warning.

## 2. Status

**OPEN — design documented, not implemented.**

## 3. Producing context

- **Date:** 2026-07-21→22
- **Session:** `019f8523-d9f7-73c3-9e25-9e6c417cfccd`
- **Terminal:** `console_ec84a662-c26f-40e0-b5f0-3b1d`
- **Origin:** Session reviewed `P:\tmp\file-editing-protocol-for-review.md` and recommended 3 enforcement hooks in Q6 of the review questions.

## 4. Read-first list

1. `P:\tmp\file-editing-protocol-019f8523-d9f7-73c3-9e25-9e6c417cfccd.md` — the reviewed version of the protocol (§7 Q6 has the 3-hook recommendation)
2. `C:\Users\brsth\.grok\AGENTS.md` § "File editing protocol" — the shipped rules (advisory; these hooks would enforce them)
3. `C:\Users\brsth\.grok\hooks\scripts\drift_surface_session_start.py` — example of a working Grok-native hook (pattern to follow)
4. `P:\.data\wiki\concepts\grok-pretooluse-deny-contract-verified.md` — verified deny contract for PreToolUse hooks (exit codes, env vars)

## 5. Verified facts

- [FACT] The file-editing protocol (shipped to AGENTS.md by another agent, commit `2b04f38`) is advisory — no hooks enforce it
- [FACT] Session 2026-07-21 experienced 2 silent edit overwrites because no enforcement existed
- [FACT] The reviewed protocol (§7 Q6) recommends 3 hooks: (1) Write ban on existing files, (2) destructive-git block, (3) read-before-write warning
- [FACT] The Grok PreToolUse deny contract is verified: exit 0 = allow, exit 2 = block with stderr, exit 1 = error

## 6. Current state

**Design documented; not implemented.** The 3 hooks are specified in the reviewed protocol document but no hook scripts exist.

## 7. Task packets

### TP-1: Write-ban hook (PreToolUse)
- goal: Block `Write` tool on existing files; allow on new files
- in scope: Create `~/.grok/hooks/scripts/write_ban_existing.py`; register in hook config
- out of scope: Other enforcement hooks (TP-2, TP-3)
- files / anchors: `~/.grok/hooks/scripts/write_ban_existing.py`, `~/.grok/hooks/active-surface.json` or equivalent hook config
- acceptance: `Write` on a new file succeeds; `Write` on an existing file is blocked with stderr explaining the rule
- falsifier: `Write` on an existing file succeeds silently (hook not firing)
- verification level required: LIVE_BEHAVIOR

### TP-2: Destructive-git block hook (PreToolUse)
- goal: Block `git reset --hard`, `git push --force`, `git filter-branch`, `git filter-repo`, `git clean -fd`, `git checkout -- <path>` in `run_terminal_command`
- in scope: Create `~/.grok/hooks/scripts/destructive_git_block.py`; register in hook config
- out of scope: The Write-ban hook (TP-1)
- files / anchors: `~/.grok/hooks/scripts/destructive_git_block.py`
- acceptance: Allowed git commands pass; forbidden commands blocked with stderr citing the AGENTS.md rule
- falsifier: A forbidden command executes successfully (hook not matching)
- verification level required: LIVE_BEHAVIOR

### TP-3: Read-before-write warning hook (PreToolUse)
- goal: Warn (not block) if `search_replace` or `Write` is called on a path that hasn't been `read_file`'d in the last 5 tool calls
- in scope: Create `~/.grok/hooks/scripts/read_before_write_warn.py`; register in hook config
- out of scope: TP-1 and TP-2
- files / anchors: `~/.grok/hooks/scripts/read_before_write_warn.py`
- acceptance: Edit without prior read produces stderr warning; edit with prior read produces no warning
- falsifier: Warning fires even after a recent read (false positive)
- verification level required: LIVE_BEHAVIOR

## 8. Open decisions

### Decision 1: Hook registration mechanism
The existing `drift_surface_session_start.py` is registered in `~/.grok/hooks/active-surface.json` as a SessionStart hook. PreToolUse hooks need a different registration path. Options:
- **A: Same `active-surface.json`** with a `"PreToolUse"` key (if Grok Build supports it)
- **B: `settings.json`** router pattern (if that's how PreToolUse hooks are wired)
- **Currently leading:** Need to verify which mechanism Grok Build uses for PreToolUse hooks before implementing.

### Decision 2: Block vs warn on Write
TP-1 blocks Write on existing files (exit 2). Some agents may need Write for legitimate full-file rewrites. Options:
- **A: Block (exit 2)** — strict; forces search_replace
- **B: Warn (stderr only, exit 0)** — advisory; allows override
- **Currently leading:** A (block) — the AGENTS.md rule says "Never on existing files"; a warning would be routinely ignored

## 9. Hard constraints

1. Hooks must follow the verified PreToolUse deny contract (exit 0/2/1; stderr on block)
2. Hooks must be registered at user scope (`~/.grok/hooks/`), not workspace
3. Hooks must fail-open if the hook script itself errors (exit 0, not exit 2)
4. Hooks must not slow down normal operations (>100ms overhead is unacceptable)

## 10. Cross-reference couplings

- `C:\Users\brsth\.grok\AGENTS.md` § "File editing protocol" — the rules being enforced
- `P:\tmp\file-editing-protocol-019f8523-d9f7-73c3-9e25-9e6c417cfccd.md` — the reviewed protocol with the 3-hook recommendation (§7 Q6)
- `C:\Users\brsth\.grok\hooks\scripts\drift_surface_session_start.py` — working hook example
- `P:\.data\wiki\concepts\grok-pretooluse-deny-contract-verified.md` — hook exit code contract
- `P:\.data\wiki\concepts\file-edit-failures-two-classes.md` — the failure modes these hooks prevent
- `P:\.data\wiki\concepts\external-state-cross-check-as-structural-fix.md` — hooks are the structural fix; rules are the advisory layer

## 11. Resumption protocol

1. Read this handoff
2. Read the reviewed protocol at `P:\tmp\file-editing-protocol-019f8523-d9f7-73c3-9e25-9e6c417cfccd.md` §7 Q6
3. Verify the Grok Build PreToolUse hook registration mechanism (check `~/.grok/docs/user-guide/` or the active-surface snapshot)
4. Start with TP-1 (Write ban) — highest leverage
5. Test each hook with both a trigger case (should block/warn) and a pass case (should allow)
6. Register hooks and verify they fire

## 12. Suggested next invocation

```
Implement the 3 PreToolUse hooks from the file-editing protocol review
(§7 Q6): Write-ban on existing files, destructive-git block, read-before-write
warning. Start with the Write-ban hook. Follow the pattern from
drift_surface_session_start.py. Verify the PreToolUse registration mechanism
for Grok Build before writing code.
```

## 13. Last user message (verbatim)

> "/handoff both our aar files."

## 14. Explicit non-goals

- Do NOT modify the AGENTS.md rules (they're already shipped; this handoff is about enforcing them)
- Do NOT implement SessionStart or Stop hooks (different event types; separate scope)
- Do NOT enforce the deliberation-waste rules via hooks (those are advisory by design — see companion handoff)

## 15. Epistemic labels

- [FACT] 3-hook recommendation is documented in the reviewed protocol (§7 Q6)
- [FACT] The AGENTS.md rules these hooks would enforce are already shipped (commit `2b04f38`)
- [INFERENCE] The PreToolUse registration mechanism is the same as SessionStart (untested for PreToolUse specifically)
- [UNKNOWN] Whether Grok Build supports PreToolUse hooks at all (need to verify before implementing)

## Dependencies

- **Requires:** Verify Grok Build PreToolUse hook support (Decision 1)
- **Blocks:** nothing
- **Non-blocking to:** deliberation-waste-rules-20260722 (independent — that handoff ships advisory rules, this one enforces structural rules)