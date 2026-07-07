# Close-the-Loop Program — Master Plan (v1.1)

Status date: 2026-07-07. This file is the single source of truth for the
6-phase harness program. If a handoff, memory entry, or recap disagrees with
this file, this file wins; update it here first, then proceed.
Canonical home: move/commit this into P:/.claude/hooks/analysis/ (or plans/)
alongside open_a_write_classification_20260707.md.

## Purpose

Close the feedback loop on the existing hook/skill harness: reliable
telemetry → transcript replay → ground truth → external-fact gating →
completion contracts → measured refactor. Add no surface area that an
existing mechanism can cover.

## Global Rules (binding on every phase)

1. READ BEFORE DESIGN. Read a file and its imports before changing it.
   Never assert behavior from a name.
2. NO INVENTION, NO OFFLOADING. Missing fact? Classify it:
   - DISCOVERABLE (read-only command/grep/read/search can answer): run the
     tool. Never ask the user. Asking for a discoverable fact = inventing it.
   - USER-ONLY (preference, approval, credential, intent): output
     `NEED: <exact question>` and stop.
   Read-only operations never require permission. Only mutations do.
3. PERMISSION SCOPE. Pause only before: destructive actions, shared-helper
   edits, scope changes, budget overruns. "May I run a grep?" is never a
   valid question.
4. ONE PHASE PER RUN. Finish the phase, emit its Evidence Packet, stop.
5. EVIDENCE PACKET = git status --short + git diff --stat (or commit SHAs if
   auto-committed — record them), per-site table (write path AND exception
   path), RAW test output (not summarized counts), unresolved items
   (explicitly empty if empty).
6. BOUNDED-BRANCH DISCIPLINE. Scope overrun or a shape not in the approved
   set → pause and report before editing. (Worked: Phase 0.5 3× overrun
   caught pre-edit.)
7. PROMOTION RULE (amendment protocol for the taxonomy/gates): new failure
   class → first add replay evidence. Only then decide: existing gate
   pattern / existing rubric / existing audit owner / routing note / no
   promotion. Never a new file by default.
8. AUDIT-TRAIL IMMUTABILITY. Once a commit SHA is cited by a task or packet,
   never amend/rebase it, regardless of push state.

## Verified environment facts (provenance + date; re-verify if stale)

- append_jsonl exists: __lib/file_lock.py:60 (verified 2026-07-07).
- append_jsonl_safe added: __lib/file_lock.py:85, returns bool, drops to
  <log>.dropped.jsonl; _LOCK_FAILURES = (OSError, BaseLockException)
  (commit 1a82d79, 2026-07-07).
- log_hook.py lives at hooks root, NOT __lib/ (verified 2026-07-07).
- Canonical block log: stop_blocks.jsonl via __lib/stop_block_log.py.
- Classification doc: P:/.claude/hooks/analysis/
  open_a_write_classification_20260707.md — counts corrected via AST +
  method-call scan (~60 production sites / ~38 files; string-grep
  undercounted). Use AST + method-call scan for all future scope docs.
- cc-aca-session dispatches via __lib/router.py (never hooks.json AND
  router — dispatch invariant).
- Auto-commit hook #906 commits mid-session without authorization —
  task #1256 filed (evidence: 1a82d79, 7f4b9dc; recurring_pattern,
  BLOCK severity). Until fixed: record auto-commit SHAs in packets.

## Phases and status

### Phase 0 — Telemetry reliability [DONE 2026-07-07]
POC: 4 sites migrated to append_jsonl_safe (stop_block_log.py,
hook_ledger.py ×2, Stop.py _log_skill_first_stop_event +
_append_anti_sycophancy_log). Commits: 1a82d79, 7f4b9dc.
Evidence: parallel 8×50 → 400/400; baseline 1600/1600 ×2; fault-injection
drop-branch 6/6 + BaseLockException injection 7/7. ensure_ascii kwarg added
(stop_block_log uses False).

### Phase 0.5 — Critical-tier expansion [DONE 2026-07-07]
Scope: Option B — CRITICAL tier only. Migrated: stop_gate_telemetry,
hook_runner, hook_error_sink, hook_importer, unified_evidence_enforcer,
agentic_reliability_telemetry, gate_health, quality_log,
verification_audit_logger, Stop.py (6 sites), PreToolUse.py (3 JSONL
sites + 1 plain-text canary, debug, excluded).
Accepted variants: .open("a") method form (collapses to existing shapes).
Scoped OUT (see decisions ledger): evidence_store (TASK-010 zero-loss
strategy strictly stronger); Stop.py:4232 ascii (sole reader
regen_cap_stats.py:39 uses read_text utf-8/replace — ascii-safe,
ensure_ascii=True confirmed correct).
DEBUG tier: deferred task, gated on evidence (Phase 6 yield data or a
dropped-trace investigation implicating a debug log). Not scheduled.
Evidence Packet: analysis/phase_0_5_critical_tier_evidence_packet_20260707.md
(per-site table, raw parallel-test output through stop_gate_telemetry +
hook_runner paths, #906 auto-commit SHAs f4addf6/16966a4).

### Phase 1 — Gold replay corpus + runner [READY — fixtures located]
5-transcript set from stop_blocks.jsonl metadata: 4897f5bd (epistemic
triple-fire + recovery), a07ff025 (deletion_verification), e1960aff
(lazy_workaround FP, self-referential), 0f183615 (perf_attribution re-fire),
b2014a6e (unverified_stance empty-hedge). Known gap: no fake_done fixture
(0 blocks in corpus) — first misses.jsonl entry.
Build: evals/gold/ fixtures (excerpt, expected behavior_type classes,
earliest-cause turn, disallowed conclusions, expected destination) +
replay_eval.py mirroring cc-aca-epistemic/.eval/judge_eval.py holdout
discipline. Verify: green on expected; corrupt-one-fixture test shows
mismatch detection.

### Phase 2 — Freshness-ruled runtime ground truth [PENDING]
runtime-ground-truth.md: fact | source | verification command |
last-verified | expiry trigger. Sessionstart injection via cc-aca-session
(router.py registration, NOT hooks.json). Expired entries render
`[STALE — reverify: <cmd>]`, never dropped or silently trusted. Add
cumulative injection budget across injectors (ground truth +
mechanism_manifest protected; recall segments truncate first).

### Phase 3 — External-fact claim shape [PENDING]
In verification/engine.py + claims.py (TASK-012 pattern). NO new gate file.
Patterns: quotas, prices, context windows, model IDs, versions,
repo/plugin/issue existence, API capability claims. Evidence required:
same-session WebSearch/WebFetch/API tool event OR unexpired ground-truth
entry. Model self-report text is NOT evidence. Ship SHADOW mode. Calibrate
on Phase 1 fixtures: flags fabricated-quota / invented-model-ID turns,
silent on ≥95% of normal turns.

### Phase 4 — Completion contract at report time [PENDING]
Upgrade debrief/references/completion-evidence-contract.md from after-action
mining rubric to report-time requirement: ledger table (claim | claim_type |
authority_required | evidence_provided | status | remaining_gap) on
implementation reports. Extend Stop_fake_done_detector for ledger presence
(warn mode). Do not duplicate cross_validator / artifact_enforcement.

### Phase 5 — Misses ledger + promotion loop [PENDING]
/debrief writes misses.jsonl (fixture ref, behavior_type, evidence).
/improve promotes rubric/gate changes only when: replay evidence exists,
≥2 independent occurrences or explicit user confirmation, gold replay green.
Record Global Rule 7 at top of bad-behavior-rubric.md as amendment protocol.
Seed entries: (1) missing fake_done fixture; (2) classification-methodology
miss (string-grep vs AST scan); (3) #906 unsupervised mutation channel.

### Phase 6 — Yield-based refactor [GATED — do not start]
Requires: Phases 0–5 live PLUS ≥2 weeks of trustworthy telemetry (clock
started at Phase 0 completion, 2026-07-07 → earliest ~2026-07-21).
Then: per-gate fire/FP report; propose merges (deletion_verification +
removal_completeness first candidates) and eval-only demotions.
PROPOSE ONLY — no gate deleted/merged without gold replay green + explicit
user approval. Note: any other "Phase 1+2 measurement (55d after
2026-06-01)" numbering in memory is a DIFFERENT program — do not conflate.

## Decisions ledger

- 2026-07-07: Option A ensure_ascii kwarg on append_jsonl (fidelity).
- 2026-07-07: auto-commits 1a82d79/7f4b9dc kept as-is; no history rewrite;
  SHA-cited commits immutable (Rule 8). Fix channel = #1256.
- 2026-07-07: Phase 0.5 scope = Option B critical tier; debug tier deferred
  on evidence, not calendar.
- 2026-07-07: Phase 1 fixture substitution accepted — real gate-block
  transcripts beat imported chat transcripts.
- 2026-07-07: PreToolUse.py count corrected — 3 JSONL sites migrated +
  1 plain-text canary (L1215, `pretooluse_canary.log`, env-gated debug)
  excluded. JSON-encoding the timestamped plain-text line would break the
  canary's purpose. Scope read-down, not a missed site.
- 2026-07-07: evidence_store scoped OUT — its temp-file zero-loss strategy
  (TASK-010: FileLock(0.5s) + unique-per-ms-per-pid temp-file fallback at
  evidence_store.py:484-513) is strictly stronger than append_jsonl_safe's
  dropped-sidecar (lossy by design). Migration would regress a documented
  fix. Scope-out, not a missed site.
- 2026-07-07: Stop.py:4232 `ensure_ascii=True` confirmed safe — sole reader
  `scripts/regen_cap_stats.py:39` uses `read_text(encoding="utf-8",
  errors="replace")`; UTF-8 is a strict superset of ASCII so 7-bit-clean
  output reads back losslessly. Grep-verified single reader.
- 2026-07-07: Phase 6 note — evaluate whether evidence_store's temp-file
  pattern should become the recommended shape for any log where loss is
  later shown to matter. It is the stronger primitive (zero-loss vs
  dropped-trace). Revisit at Phase 6 yield review (earliest ~2026-07-21).
