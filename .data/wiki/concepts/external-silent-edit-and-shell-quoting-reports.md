---
title: \"External reports: silent edit non-persistence and shell quoting failures\"
created: 2026-07-21
source: session-2026-07-21-www
sources:
  - https://github.com/anthropics/claude-code/issues/40227
  - https://github.com/anthropics/claude-code/issues/49805
  - https://github.com/anthropics/claude-code/issues/12805
  - https://github.com/anthropics/claude-code/issues/65162
  - https://forum.cursor.com/t/agent-edits-sometimes-not-saving-file-to-disk/134528
  - https://gist.github.com/kmgallahan/cf44f50293901c7d4034b21b52c5804f
  - https://www.morphllm.com/common-errors/error-editing-file
tags: [file-editing, persistence, shell-quoting, windows, multi-agent, external-evidence, claude-code, cursor]
summary: >
  Yes — other people report both problems at scale. Silent \"success but not on
  disk\" Write/Edit failures appear across Claude Code (macOS Desktop + Windows
  CLI) and Cursor (buffer-not-flushed). Shell quoting failures are a separate
  dual-shell class (PowerShell @'...'@ inside Bash, heredoc hangs, path escapes).
  Community workarounds match ours: verify after write, write via Python/temp
  file, match idiom to shell. Does not replace our Class A/B distinction.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/file-edit-failures-two-classes
    type: related
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: related
---

# External reports: silent edit non-persistence and shell quoting failures

## One-line answer

**Yes.** Both failure classes show up widely outside this host — across Claude Code, Cursor, and Windows dual-shell setups. Our session is not special-case paranoia.

## What external users report (by symptom)

### 1. Tool reports success; file not on disk (silent non-persistence)

| Report | Product / OS | Symptom | Confidence |
|--------|--------------|---------|------------|
| [anthropics/claude-code#40227](https://github.com/anthropics/claude-code/issues/40227) | Claude Desktop Write/Edit, **macOS** | \"File created successfully\" / \"updated successfully\" but ls finds nothing; intermittent same dir/session; Bash always works | [HIGH] primary issue + cross-links to #36084, #40341, #43588, #45557, #49805, #51214 |
| [anthropics/claude-code#49805](https://github.com/anthropics/claude-code/issues/49805) | Claude Code Write, **Windows** | New files only: success message, file absent; ~150KB of specs lost until transcript re-extract | [HIGH] platform:windows; closed as duplicate of #40227 |
| [anthropics/claude-code#12805](https://github.com/anthropics/claude-code/issues/12805) | Claude Code Edit/Write, **Windows MINGW** | \"File has been unexpectedly modified\" despite unchanged mtime/md5; forces Bash/Python workarounds; community patches cli.js timestamp checks | [HIGH] multi-comment, repro, patches |
| [Cursor forum #134528](https://forum.cursor.com/t/agent-edits-sometimes-not-saving-file-to-disk/134528) | Cursor agent, Win→Linux remote | Patch lands in **editor buffer only** (unsaved tab dot), not disk; agent death-spirals on build | [HIGH] clear repro narrative |
| Related Cursor topics | Cursor | \"not saving after edits\", \"no changes made\", AI changes immediately revert | [MEDIUM] titles only |

**Community workarounds that recur (match our protocol):**
1. Read-back / ls after every Write/Edit
2. Prefer Bash/Python file IO over native Write when flaky
3. Retry after failure sometimes succeeds (non-deterministic)

**Issue hygiene note:** Several Claude Code reports were closed as invalid / duplicate / stale without a root-cause fix. Prevalence ≠ vendor acknowledgment.

Maps to our **Class A (persistence)** in [[file-edit-failures-two-classes]] — tool self-reports success; disk disagrees. External reports also show **non-Windows** cases (macOS Desktop), so \"Windows-only\" is false.

### 2. Shell quoting / dual-shell idiom failures

| Report | Symptom | Confidence |
|--------|---------|------------|
| [anthropics/claude-code#65162](https://github.com/anthropics/claude-code/issues/65162) | Model emits PowerShell @'...'@ here-string **inside Bash tool** → silent corruption of git commit / gh pr edit body; exit 0 | [HIGH] open, multi-user recurrence (\"10-20 min/day\"), fish-shell sibling #71339 |
| [anthropics/claude-code#62813](https://github.com/anthropics/claude-code/issues/62813) | Bash tool hangs on heredoc inside command substitution (~512B+) | [MEDIUM] linked from #65162 |
| [gist: Bash Syntax Auto-Corrector](https://gist.github.com/kmgallahan/cf44f50293901c7d4034b21b52c5804f) | Pre-tool hook rewrites common Windows bash mistakes: backslash paths, $USERPROFILE vs $HOME, PowerShell vars in double quotes, git commit heredocs → $'...', bare cmdlets → pwsh -NoProfile | [HIGH] practitioner implementation of the failure class |
| Copilot community | Model emits bash when user is on PowerShell (wrong-shell) | [MEDIUM] discussion |

**Root pattern:** Windows sessions often expose **two shells** (Git Bash + PowerShell) with **incompatible multi-line quoting**. Models mix idioms; exit code 0 hides corruption.

**Community mitigations:**
- Write multi-line payloads to a **temp file**, then python script.py / git commit -F msg.txt / gh pr edit --body-file
- CLAUDE.md rule: never @'...'@ in Bash
- Match idiom to tool (PowerShell tool only for PowerShell here-strings)
- Auto-corrector PreToolUse hooks for known Windows bash mistakes

This is **orthogonal to Class A/B file edits** but co-occurs in the same sessions (shell used as edit workaround).

### 3. Fragile string-patch editing (adjacent, not silent success)

Vendor-adjacent write-up: MorphLLM \"Error editing file\" (Claude Code str_replace, Cursor apply, Aider diffs). Claims text-based find-replace is fragile (whitespace, formatOnSave, duplicates). Stats (35% fail / 98% Morph) are **vendor-claimed** — treat as [LOW] for numbers, [MEDIUM] for the failure taxonomy.

Does **not** equal \"reports success but disk empty\" — that is usually a loud error. Still relevant: same read-then-patch fragility chain.

## Do's and don'ts (from external + our host)

### Do

| Do | Why | Source |
|----|-----|--------|
| Verify on disk after every Write/Edit (Read / ls / surrounding lines) | Tool success is not a receipt | #40227, #49805, our protocol |
| Prefer temp-file + Python/shell for multi-line or batch edits | Avoids shell quoting *and* flaky native Write | #12805 workarounds, #65162, our install script pattern |
| Match quoting idiom to the **actual** shell of the tool | Dual-shell is the root of silent corruption | #65162 |
| Use append mode for log-shaped shared files | Prevents Class B sequential collision | [[file-edit-failures-two-classes]] |
| Re-read after long think / concurrent accept-reject | Stale buffer/apply races (Cursor) | Cursor #134528, Morph taxonomy |

### Don't

| Don't | Why | Source |
|-------|-----|--------|
| Trust \"File created successfully\" without read-back | Documented silent failure path | #40227, #49805 |
| Put PowerShell @'...'@ in Bash | Exit 0 + corrupted content | #65162 |
| Put large heredocs inline in shell argv on Windows | Hang / parse failures | #62813, auto-corrector gist |
| Blame only Windows / only search_replace | macOS Desktop + Cursor buffer-not-flush also fail | #40227, Cursor forum |
| Assume atomic Python write alone fixes multi-agent loss | Class B still clobbers | [[file-edit-failures-two-classes]] |

## Mapping to our local model

| External cluster | Our class | Notes |
|------------------|-----------|-------|
| Success message, file missing | Class A | Also seen on macOS → not NTFS-only |
| \"Unexpectedly modified\" false positive | Tool-state / mtime tracking (Windows) | Adjacent to A; forces shell path |
| Buffer saved in UI, not disk (Cursor) | Class A variant (layer: editor, not agent tool) | Same verification fix |
| Concurrent agent / accept-reject clobber | Class B | Multi-writer |
| Shell wrong-idiom / quoting | **Class C (shell quoting)** — new label | Not in two-class page; orthogonal |

**Class C definition (proposed):** model or harness emits shell syntax that does not match the executing shell; command may exit 0 while corrupting data or never applying intended content. Fix: temp files, shell-specific rules, optional auto-correct hooks — not atomic write.

## Conflicts / caveats

- **⚠️ Anthropic issue bots** frequently close these as invalid/duplicate/stale. That is process noise, not disproof.
- **Morph 35%/98% numbers** are marketing-adjacent; independent replication not found in this pass.
- **Reddit \"6 critical bugs\"** post title seen in search; scrape blocked — do not cite body details.
- Local **verified-then-vanished after read-back** (our log.md/AGENTS cases where Python write + immediate Read succeeded then later absent) remains **under-reported externally** in this pass. External reports focus on *tool claimed success / disk never had it*, not *disk had it then lost it*. That residual may still be multi-agent Class B or host-specific.

## Implications for this host

1. File-editing protocol install (verify + no full overwrite + temp Python) is **aligned with industry workarounds**, not overfit.
2. Shell quoting: keep **write-script-to-temp-file** as default for multi-line PowerShell/Python; never inline large strings in python -c with nested quotes.
3. Worth treating **Class C** as a named third failure mode next to A/B in protocol docs.
4. Optional future: PreToolUse shell auto-corrector (gist pattern) for Grok/Claude on Windows.

## Falsifier

If after 6 months of monitoring Claude Code / Cursor / Grok issue trackers:
- no new silent-success-write reports appear, **and**
- dual-shell quoting issues disappear from Windows threads,
then reclassify this as historical. As of 2026-07-21 research, both are active classes.

## Related

- [[file-edit-failures-two-classes]] — local A/B model; this page is external prevalence + Class C
- [[plausible-narratives-substitute-for-verification]] — \"tool said success\" is Disguise 5
- [[external-state-cross-check-as-structural-fix]] — disk read-back is the external state
- ~/.grok/docs/file-editing-protocol.md — always-loaded operational rules

## Sources (scored CREDIBLE-lite)

| Source | Auth | Rec | Evid | Bias | Total | Role |
|--------|------|-----|------|------|-------|------|
| GH #40227 | 3 | 3 | 3 | 3 | 12 | Primary silent-write (macOS) |
| GH #49805 | 3 | 3 | 3 | 3 | 12 | Primary silent-write (Windows) |
| GH #12805 | 3 | 2 | 3 | 3 | 11 | Windows Edit false-mtime + workarounds |
| GH #65162 | 3 | 3 | 3 | 3 | 12 | PowerShell-in-Bash quoting |
| Cursor #134528 | 2 | 2 | 3 | 3 | 10 | Buffer-not-disk |
| Bash auto-corrector gist | 2 | 3 | 3 | 2 | 10 | Practitioner Class C mitigations |
| MorphLLM edit errors | 2 | 3 | 1 | 1 | 7 | [LOW-QUALITY] numbers; taxonomy only |

Phase 2 synthesis: parent-inherited model.
