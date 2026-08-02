---
thread_id: hook-timeout-root-cause-20260801
parent_handoff_path: none
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
parent_session: none
current_terminal_id: 311cd4b1-2bf4-47ec-8abd-7530e971493c
produced_at: 2026-08-01T16:30:00Z
last_updated_by: 019fb937-b03e-7f80-a4b0-68afdb7da38d
last_updated_at: 2026-08-02T05:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 448e0b38806f4bbcdc568696a45d638fdd3eb616
---

# Handoff: Hook timeout root cause — deferred work

## Objective

Resolve the remaining deferred work from the hook timeout root cause investigation: (1) yt-is transcript coverage gap, (2) Class C quoting friction enforcement, (3) chronic workspace-health cleanup.

**Scope bounds:** Session 019fb937 resolved the primary problem (hook timeouts from dirty-tree inflation) and captured durable knowledge. This handoff covers the three deferred items that are NOT resolved.

## Status

OPEN — primary fix shipped (dirty tree 1388→399), three deferred items remain.

## Producing context

- Date: 2026-08-01
- Session: 019fb937-b03e-7f80-a4b0-68afdb7da38d
- Terminal: 311cd4b1-2bf4-47ec-8abd-7530e971493c
- Host: grok (Grok Build)

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md` — the RCA + RESOLVED section showing what was fixed and why the original framing was wrong
2. `P:/.data/wiki/concepts/list-before-claim-for-destructive-proposal-actions.md` — the structural fix for inference-as-fact errors (created this session)
3. `P:/.data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md` — the systemic pattern (created this session)
4. `C:/Users/brsth/.grok/hooks/scripts/mutation_receipt.py` — the hook code whose budget math was the proximate cause
5. `C:/Users/brsth/.grok/hooks/quality-gate.json` — the hook registration (timeouts still at 10s, but no longer needed at 30s)

## Verified facts

- [FACT] Dirty tree reduced from 1388 to 399 files by untracking 983 regenerable stubs + 4 ghosts (commit `adef081`, measured `git diff --name-only HEAD` before/after)
- [FACT] `git diff --name-only HEAD` dropped from 1921ms to 929ms after the fix (measured this session)
- [FACT] yt-is `transcript_cache` table has 369 rows; wiki/sources/transcripts/ has 5,070 YouTube-type transcripts (sqlite query + transcript frontmatter scan)
- [FACT] 11 Class C quoting failures (10 Traceback + 1 SyntaxError) occurred this session from inline `python -c` probes (transcript scan)
- [FACT] Hook timeouts were the 4th documented recurrence of the pattern in `hook-evidence-collection-cost-vs-timeout-tradeoff.md`
- [FACT] qmd.exe was stale (`--version` returned "Unknown command"); deleted + references removed from `index_skills.py` (commits `669bbed`, `9e24d7c`)
- [FACT] List-before-claim rule added to `~/.grok/AGENTS.md` line 329 (verified in HEAD)
- [FACT] "Best fix with no negative second-order effects" principle added to `/go` SKILL.md line 35 (commit `d92ecbf`)
- [FACT] `/tp` session-review-protocol.md section order fixed: skills before actionable recommendations (commit `71d2ff1`)
- [FACT] `close-check.md` argument bug fixed: `--lane mechanical` → `mechanical` positional (commit `c9f03c6`)
- [FACT] 448e0b3 committed after this handoff was written — updated tp-parallel-panel handoff and premature-recommendation wiki concept (source: `git log ef36a71..448e0b3`)

## Current state

### Shipped (done, verified):
- 983 stubs + 4 ghosts untracked, `.gitignore` updated
- qmd.exe deleted, 4 code references removed, 2 lint errors fixed
- 3 wiki concepts created/updated (hook-evidence RESOLVED, list-before-claim, analysis-over-action)
- 3 AGENTS.md fixes (count bug, list-before-claim rule, 2 duplications removed)
- close-check.md arg fix
- go/SKILL.md best-fix principle
- tp session-review-protocol.md section order fix

### Deferred (this handoff):
1. yt-is transcript coverage gap (369 of 5,070)
2. Class C quoting friction (11 hits, no enforcement improvement)
3. Chronic workspace-health items (hook syntax errors, dangling paths, state GC)

## Task packets

### TP-01: yt-is transcript coverage expansion

- **id:** TP-01
- **goal:** Expand yt-is to cover all 5,070 YouTube transcripts currently only in wiki/sources/transcripts/
- **in scope:** yt-is package transcript ingestion pipeline
- **out of scope:** web_page transcripts (2,034), generated_text (356), pdf (59) — these have no yt-is equivalent
- **files / anchors:** `P:/packages/yt-is/.data/yt-is/transcripts.sqlite` (369 rows currently), `P:/.data/wiki/sources/transcripts/` (5,070 youtube-type files)
- **acceptance:** yt-is transcript_cache has ≥5,000 rows matching wiki YouTube transcripts; wiki transcripts can be safely deduped
- **falsifier:** success rate <90% (fewer than 4,563 of 5,070 match)
- **verification level required:** LIVE_BEHAVIOR (sqlite query)
- **estimate:** [UNKNOWN] — depends on yt-is ingestion rate and whether video IDs are extractable from wiki transcript frontmatter
- **auth-expiry mitigation:** yt-dlp auth may be needed; chunk by 500-video batches

### TP-02: Class C quoting friction enforcement

- **id:** TP-02
- **goal:** Reduce inline `python -c` failures by enforcing temp-file usage for multi-line Python
- **in scope:** AGENTS.md rule strengthening OR a PreToolUse hook that detects multi-line `python -c` in run_terminal_command
- **out of scope:** Single-line `python -c` (acceptable risk)
- **files / anchors:** `~/.grok/AGENTS.md` § "Class C: shell quoting", `~/.grok/hooks/quality-gate.json`
- **acceptance:** inline `python -c` usage with >1 statement drops to ≤1 per session (from 11)
- **falsifier:** >3 inline `python -c` multi-statement failures in a future session
- **verification level required:** STATIC_INSPECTION (hook exists) or LIVE_BEHAVIOR (friction count drops)

### TP-04: close-check remediation performance optimization

- **id:** TP-04
- **goal:** Reduce close-check Phase 3 from 12+ minutes to <3 minutes
- **in scope:** `~/.grok/workflows/close-check.rhai` Phase 3 Remediate
- **out of scope:** Phase 1 Sweep (parallel agents are fine), Phase 4 Finalize (single agent, fast)
- **files / anchors:** `C:/Users/brsth/.grok/workflows/close-check.rhai` (Phase 3, ~line 370-430)
- **acceptance:** close-check completes in <3 minutes with all 5 lifecycle skills executing
- **falsifier:** close-check still takes >5 minutes after optimization
- **verification level required:** LIVE_BEHAVIOR (time the workflow end-to-end)
- **root cause:** Each remediation skill runs as a full subagent spawn (read SKILL.md → scan transcript → check existing → write → commit). 5 subagent lifecycles = 12+ minutes. The orchestrator can do most of this work directly without spawning subagents.
- **proposed approach:** Move mechanical scanning (grep transcript for correction signals, count friction patterns) inline to the workflow script. Only spawn subagents for the write-capable skills that need LLM judgment to decide what to write. Better yet: have Phase 1 sweep agents ALSO collect the remediation data (they already scan the transcript), then Phase 3 just writes the artifacts based on data already gathered.

### TP-03: chronic workspace-health cleanup

- **id:** TP-03
- **goal:** Resolve chronic workspace-health findings from close-check report
- **in scope:** 10 hook syntax errors, 197 dangling path references, 562 stale state files (>30 days), 201 duplicate skill names
- **out of scope:** Hook dispatch chain changes (working as designed)
- **files / anchors:** `P:/packages/.claude-marketplace/plugins/` (hook syntax), `~/.grok/hooks/state/` (stale files), `P:/.data/wiki/concepts/skill-catalog.md` (duplicates)
- **acceptance:** `python ~/.grok/skills/workspace-health/scripts/workspace_health.py` returns 0 FAIL findings on chronic items
- **falsifier:** same chronic findings reappear in next close-check run
- **verification level required:** LIVE_BEHAVIOR (workspace-health scan)
- **no_live_run_reason:** deferred — this is a `/maintain` session task, not a quick fix

## Open decisions

### OD-01: Class C enforcement mechanism

- **Question:** Should the Class C quoting fix be a behavioral rule (strengthened AGENTS.md) or a mechanical hook?
- **Options:** (1) Stronger AGENTS.md rule with examples [low cost, ~50% compliance ceiling] (2) PreToolUse hook that detects multi-line `python -c` and warns [mechanical, higher compliance] (3) Both [belt and suspenders]
- **Selection criterion:** compliance rate vs implementation cost
- **Currently leads:** Option 3 (both) — the rule is cheap, the hook is reliable
- **What would change it:** if the existing rule's compliance is actually high and this session was an anomaly

## Hard constraints

- Do NOT delete wiki/sources/transcripts/ files until yt-is coverage is verified (TP-01 acceptance met)
- Do NOT change hook timeouts from 10s to 30s — the dirty-tree fix made this unnecessary, and the architectural fixes in the wiki concept remain valid for future-proofing but are no longer urgent
- Do NOT track `.data/wiki/sources/skills/` in git — it's regenerable churn

## Cross-reference couplings

- `P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md` → cites the dirty-tree measurements. If the dirty tree grows again, re-measure.
- `P:/.data/wiki/concepts/list-before-claim-for-destructive-proposal-actions.md` → cites the gitignore incident. The rule is in AGENTS.md line 329.
- `P:/.data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md` → describes the systemic pattern. Structural fix (bridge /why → /go) not yet implemented.
- `~/.grok/AGENTS.md` → contains list-before-claim rule, short-command interpretation rule, Class C quoting rule. All concurrent-session-sensitive.
- This handoff's `accurate_as_of_head` → `448e0b3`. If HEAD moves, re-verify cited paths.

## Other outstanding streams

- **Analysis-over-action bridge** — `/why` Step 14 should end with "invoke `/go` to apply fix #1." Not yet implemented. Open.
- **`/tp` skill improvements** — session-review-protocol.md section order fixed this session. Other improvements (compaction-aware scan, dynamic skill recommendations) documented in the protocol file. Open but not urgent.

## Explicit non-goals

- Do NOT re-investigate the hook timeout root cause — it's resolved and documented
- Do NOT attempt to dedup web_page transcripts (2,034) — they have no yt-is equivalent
- Do NOT refactor the mutation_receipt.py hook architecture — the wiki concept documents the architectural fixes; they're optional future-proofing, not urgent
- Do NOT auto-close the preflight-gate handoff — it was already deleted (commit `a21072f`)

## Resumption protocol

1. Read this handoff + the 3 wiki concepts in the read-first list
2. Pick the highest-priority task packet (TP-03 chronic cleanup has the most findings; TP-01 yt-is coverage has the most value)
3. For TP-03: run `/maintain` which chains workspace-health + skill-prune + cleanup
4. For TP-01: investigate yt-is ingestion pipeline, determine if video IDs are extractable from wiki transcript frontmatter
5. For TP-02: decide OD-01 (rule vs hook vs both), then implement

## Suggested next invocation

```
/maintain — run workspace-health cleanup on the chronic items from the close-check report (10 hook syntax errors, 197 dangling paths, 562 stale state files, 201 duplicate skills)
```

## Last user message (verbatim)

> "Please use the handoff skill"

## Epistemic labels per claim

- [FACT] All measurements (dirty tree, git diff timing, transcript counts, sqlite row counts) — cited with receipt commands above
- [FACT] All commits — cited with SHA hashes
- [FACT] 448e0b3 committed after this handoff was written — updated tp-parallel-panel handoff and premature-recommendation wiki concept (source: `git log ef36a71..448e0b3`)
- [INFERENCE] The analysis-over-action pattern is systemic (not session-specific) — based on 5-session recurrence, but no quantitative measurement of fix-application rate across the workspace
- [UNKNOWN] yt-is ingestion effort estimate — depends on pipeline capabilities not investigated this session

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01T16:30 | 019fb937... | created |
| 2026-08-02T05:00 | 019fb937... | revision 1 — updated accurate_as_of_head to 448e0b3; added TP-03 task packet; added post-handoff commit note |
