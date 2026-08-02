---
title: Improvement Opportunities — Session 019fbdfb (2026-08-01)
type: handoff
domain: lifecycle
created: 2026-08-01
source_session: 019fbdfb-a29e-7b50-8b5a-d3a813f9ab2
host: grok
status: open
evidence_window: pre-packed (transcript inaccessible — see Tier 2 item 1)
---

## Improvement Stream — Tier 2 (operator decision needed)

These findings are routed to the improvement stream (actionable items, NOT wiki concepts). Each needs an operator decision before being persisted as a task or follow-up handoff.

---

### 1. Transcript scan infrastructure broken — sessions can be unparsed (NEW)

**Category:** System gap / near-miss failure pattern
**Signal:** This session's transcript could not be scanned because the cwd encoding passed to the session scanner was `P%3A%5C` (URL-encoded `P:\`) but the actual session directory lives at `P%3A%2F` (URL-encoded `P:/`). Verified empirically: `Test-Path 'C:\Users\brsth\.grok\sessions\P%3A%5C'` returns False; the directory `P%3A%2F` exists with 3+ session IDs under it.

**Knowledge captured but not enforced:** Wiki concept `grok-build-session-transcript-tool-call-data-in-updates-jsonl.md` was written today (2026-08-01) documenting that tool call data lives in `updates.jsonl` and that the session path encoding is `P%3A%2F` — but the scanner infrastructure was apparently not updated to use the correct encoding. The concept captures the *what* but not the *where-is-the-bug*, and the scanner keeps sending the wrong path.

**Recommendation:** Find the caller that constructs the session directory path and fix the encoding from `\` to `/` before URL-encoding. If the bug is in multiple callers, write a single utility (`session_path(cwd) -> Path`) and route all session-lookup code through it.

**Effort:** ~1 hour (investigate caller, patch, add test)
**Priority:** HIGH — every session that triggers this bug has degraded capture coverage. A single missed fix means uncaptured knowledge across N future sessions.

**Evidence:**
- Pre-packed raw: `compaction-recovery raw evidence: Error: C:\Users\brsth\.grok\sessions\P%3A%5C\{...} is not a valid directory.`
- Pre-packed raw: `friction raw evidence: No transcript available. Path resolution failed at the first tool call.`
- Pre-packed raw: `obligation-coverage raw evidence: All input artifacts for this check are inaccessible.`
- Verification: `Get-ChildItem 'C:\Users\brsth\.grok\sessions\P%3A%2F' | Select Name` returns session IDs; same command against `P%3A%5C` returns nothing.

---

### 2. Close scanner unavailable — AAR + capture blocked (CHRONIC)

**Category:** System gap (already tracked, still unresolved)
**Signal:** Sweep reports `close-gates: Close scanner unavailable — no changes assessed. The close scanner could not produce a valid result for this session. No persistence, AAR, or closure claims should be derived from session memory.`

**Status:** Existing handoff `close-runner-scanner-unavailable-regression-20260731/` tracks this. Three follow-up handoffs modified today (close-check-lifecycle, close-check-remediation-performance, close-check-lifecycle-auto-chain) show work was attempted. But the scanner is STILL unavailable for this session, meaning:
- AAR did NOT run mechanically (ran only via this manual capture)
- Decisions auto-promotion gate failed
- Verification (static + runtime) NOT PERFORMED
- Persistence boundary NOT ASSESSED — all AAR/closure claims blocked

**Recommendation:** Treat this session's "no AAR" as a known gap, not a deliverable. Move on. Do not claim AAR coverage for session 019fbdfb. Operator decision needed on whether the scanner regression is now a chronic state to be accepted (and /close documented to skip AAR) or whether it requires an active fix this week.

**Effort:** Decision + documentation (~30 min) OR ~3-6 hours of scanner debug
**Priority:** MEDIUM — workaround exists (manual capture) but compounds every session.

---

### 3. Git state — 38 unpushed commits + 36 uncommitted files (CHRONIC)

**Category:** Repeated manual step / friction
**Signal:**
- `P:\` : 15 unpushed commits (all 2026-08-01/02 — handoffs, wiki concepts, AGENTS.md updates, post-session work) + 29 uncommitted files (log.md, notebooklm/SKILL.md, design docs, .pi changes)
- `~/.grok`: 23 unpushed commits (close fixes, dream skill, nim-openai-gpt-oss-20b note, qmd removal reverts) + 7 uncommitted files (test_file_inference_smoke.py, file_extractor.py, todo/SKILL.md, hook_failures.jsonl, version.json)

**Pattern:** Each session that runs `/close` accumulates more unpushed commits. None have been pushed since the regression. This is a workspace divergence problem — local commits diverge from origin across both repos.

**Recommendation:** Decide a push policy. Options:
1. Push weekly with `--no-verify` if pre-push hooks are failing — accepts some local divergence
2. Stop accumulating and treat close as commit-only — push becomes an explicit operator task
3. Investigate why no push has happened since 2026-07-30

The 36 uncommitted files are a separate problem — many are mid-session work that needs either commit or stash. Operator decision on which is which.

**Effort:** ~2 hours investigation + decision + push
**Priority:** MEDIUM — divergence grows monotonically; recovery gets harder

**Receipts:**
- Pre-packed raw: `git-state: P: 29 uncommitted + 15 unpushed; ~/.grok: 7 uncommitted + 23 unpushed. dirty_age.py: 4 files >7d, 0 >30d.`
- Recent unpushed commits include: `8a585f4` (replacement-before-investigation rule), `babbc12` (tool-fallbacks), `4e5cdae` (tool-fallbacks updates), `5afbd72` (coding-model-pool), `9208495` (coding-model-pool updates).

---

### 4. Workspace-health chronic issues — aggregate batch (CHRONIC)

**Category:** System gap (long-running, low-priority-but-accumulates)
**Signal:** hooks_audit + index_skills chronic findings:

| Item | Count | Severity |
|------|-------|----------|
| DANGLING_PATHS (file references to deleted .claude/state, deleted tests, missing hooks) | 197 | LOW |
| STATE_GC items (state files >30d old; skill_context_*.json ages 64-94d, log files 82-92d, guidance cache 82d) | 572 | LOW |
| Orphan script references (e.g., aar missing scripts/dirty_age.py, close missing scripts/git_state_check.py, dream missing scripts/append_log.py, go missing scripts/capabilities.py) | 134 | MEDIUM |
| Duplicate skill names across multiple scopes | 201 | MEDIUM |
| Hook SYNTAX failures (BOM on task_tracker_hook.py and __lib/hook_base.py; bad escape in test_verification_engine.py:550 and write_fix.py:166; etc.) | 10 | MEDIUM |
| Hook REGISTRATION failure (snapshot plugin hook registered directly, not via __lib/router.py) | 1 | HIGH (one specific bug) |
| Disabled-count delta (30 Grok-disabled plugins vs 51 Claude-enabled plugins) | 21 plugins | LOW |
| Submodule staleness (cc-skills-ai-api, cc-skills-sdlc; 12 days old) | 2 | LOW |
| ornith-server.log.err (10 days), mpc-favorites-to-playlist.ps1 (8 days) | 2 files | LOW |

**Pattern:** Most are chronic (recurring across many sessions). Some are signal of real breakage (orphan script refs mean scripts/* paths in SKILL.md no longer exist, so skills calling them break silently). The snapshot hook registration is a single concrete bug.

**Recommendation:** Three batches:
1. **Fix-now (1-2 hours):** the snapshot hook registration + the 10 SYNTAX failures (BOM removal, escape fixes). These are concrete bugs that the scanner has flagged consistently.
2. **Decide-this-week:** orphan script references (134) — either rewrite the SKILL.md scripts/* references to point at existing files, OR delete the SKILL.md references and accept the skill works with broken subcommands.
3. **Accept-as-chronic:** DANGLING_PATHS, STATE_GC, duplicates, submodule staleness, server log err, mpc script. Document in AGENTS.md as known-untriaged and stop running the scan as a blocker.

**Effort:** Batch 1 ~2 hours; Batch 2 ~4 hours; Batch 3 ~30 min documentation
**Priority:** Batch 1 = HIGH (concrete bugs); Batch 2 = MEDIUM (silent breakage); Batch 3 = LOW (chronic noise)

---

### 5. Harvest pending obligation: tp-session-019fb926 (RECENT, <2 days)

**Category:** Improvement stream — actionable tasks waiting
**Signal:** `P:/.data/harvest/pending/tp-session-019fb926.json` contains 3 open obligations from session 019fb926:

1. **NEXT_ACTION_PACKET prototype in /www** — Replace prose Skill suggestion with structured packet so operator-gated skill routing costs one keystroke not re-derivation. Operation: GENERALIZE.
2. **tool_choice=required injection in /codex skill for Luna/mini-class** — Lighter GPT-5 tiers intermittently emit text-only instead of tool calls; conductor should inject tool_choice=required when available. Operation: GENERALIZE.
3. **Luna no-auto-pool update not applied** — Wiki concept recommends adding Luna to no-auto-pool list in model-tool-calling-capability-matrix.md but the matrix was not updated. Operation: COMPLETE.

**Recommendation:** Run `harvest triage` to route each. Items 1 and 2 are GENERALIZE — they need a follow-up skill/wiring change. Item 3 is COMPLETE — it's a small one-line fix to the matrix file that someone just needs to do. Recommend completing #3 immediately (~10 min) and routing #1 + #2 to follow-up handoffs.

**Effort:** #3 = 10 min; #1 + #2 = new handoffs (~30 min each to spec)
**Priority:** #3 = HIGH (trivial); #1 + #2 = MEDIUM

---

## Tier 1 Auto-Capture (already persisted this session or adjacent)

| Finding | Output | Status |
|---------|--------|--------|
| Replacement-before-investigation pattern | AGENTS.md rule (commit 8a585f4) + wiki concept `replacement-before-investigation-pattern.md` | Persisted |
| AAR always-deep-mode operator directive | Wiki concept `aar-always-deep-mode-operator-directive.md` | Persisted |
| Serde-broken false-positive sweep | Wiki concept `serde-broken-false-positive-sweep-20260801.md` | Persisted |
| Pre-packed evidence pattern | Wiki concept `pre-packed-evidence-pattern.md` | Persisted |
| PostToolUse auto-verify | Wiki concept `posttooluse-auto-verify.md` | Persisted |
| Python -m ruff swallows stdout in PowerShell | Wiki concept `python-m-ruff-swallows-stdout-in-powershell.md` | Persisted |
| Behavioral compliance gap | Wiki concept `behavioral-compliance-gap.md` | Persisted |
| Grok Build transcript tool-call data location | Wiki concept `grok-build-session-transcript-tool-call-data-in-updates-jsonl.md` | Persisted (covers the bug in Tier 2 item 1 — but scanner infrastructure not fixed) |
| Gemini API vs agy CLI comparison | Wiki concept `gemini-api-vs-agy-cli.md` | Persisted |
| Operator collaboration style and leverage | Wiki concept `operator-collaboration-style-and-leverage.md` | Persisted |
| Ship-phase log enforcement design | Wiki concept `ship-phase-log-enforcement-design.md` | Persisted |
| Chrome job object escape via task scheduler | Wiki concept `chrome-job-object-escape-via-task-scheduler.md` | Persisted |
| Accumulation problem resolution rate binding constraint | Wiki concept `accumulation-problem-resolution-rate-binding-constraint.md` | Persisted |
| LLM context windows map-reduce synthesis thresholds | Wiki concept `llm-context-windows-map-reduce-synthesis-thresholds.md` | Persisted |
| Agent failure modes 2026 | Wiki concept `agent-failure-modes-2026.md` | Persisted |
| Functional decomposition when test mocks constrain structure | Wiki concept `functional-decomposition-when-test-mocks-constrain-structure.md` | Persisted |
| Close-check invokes capture | Wiki concept `close-check-invokes-capture.md` | Persisted |
| Class-C quoting friction (019fb937) | Handoff `class-c-quoting-friction-019fb937-20260802/` | Persisted |
| Hook timeout root cause + deferred work | Handoff `hook-timeout-root-cause-and-deferred-work-20260801/` | Persisted |
| Premature recommendation pattern | Handoff `premature-recommendation-pattern-20260801/` | Persisted |
| TP parallel panel dispatch | Handoff `tp-parallel-panel-dispatch-20260801/` | Persisted |
| Verification before completion | Handoff `verification-before-completion-20260801/` | Persisted |
| Harvest burn-down | Handoff `harvest-burn-down-20260801/` | Persisted |
| Session observations (019fba58, 019fbf02, 019fb937) | Handoffs (3 dirs) | Persisted |

---

## Success Patterns (Category 7) — already formalized

| Pattern | Output | Status |
|---------|--------|--------|
| Pre-packed evidence pattern (sweep → agent, skip re-scan) | Wiki concept `pre-packed-evidence-pattern.md` | Persisted |
| Dual-stream routing (knowledge vs improvement separation) | /capture SKILL.md design (line 41-55) | Persisted (design) |
| Multi-terminal atomic write discipline | AGENTS.md file-editing-protocol | Persisted |
| Operational sub-handoff per session (session-observations-NNNN-DATE) | Handoff convention | Persisted (convention) |

---

## Coverage Check

| Check | Result |
|-------|--------|
| /aar ran | NO — close scanner unavailable. Manual capture only. 0 AAR findings recovered. |
| /wiki ran | YES — 54 wiki concepts modified today (2026-08-01); this capture relies on those. |
| Decisions auto-promoted | NO — close scanner unavailable. Manual review of unpushed commits recovered 0 architectural decisions worth promoting beyond what was already persisted. |
| Corrections captured | YES (already, in adjacent session(s)) — replacement-before-investigation rule (commit 8a585f4) + multiple wiki concepts. |
| Friction addressed | PARTIAL — chronic workspace-health friction remains (Tier 2 item 4). |
| Transcript accessible | NO — path encoding bug (Tier 2 item 1) made chat_history.jsonl + updates.jsonl unreachable. Capture ran on pre-packed sweep evidence only. |

---

## Next Actions (operator decision needed)

1. **Tier 2 item 1 (transcript scan bug):** approve ~1 hour fix, OR document the workaround (callers must use `P%3A%2F` not `P%3A%5C`).
2. **Tier 2 item 3 (git push backlog):** approve push strategy OR commit-only mode for /close going forward.
3. **Tier 2 item 5 (#3 in harvest):** trivially apply the Luna no-auto-pool matrix update (~10 min, no operator decision needed; just a flag for the operator that the operator-flagged item is now done).
4. **Tier 2 item 4 batch 1:** approve snapshot hook registration fix + 10 syntax-failure batch.
5. **Tier 2 items 2, 4 (rest), 5 (#1, #2):** defer to next session — chronic, not urgent, requires broader strategy decisions.