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
   2a. CROSS-SESSION/CONCURRENT STATE IS NOT AUTOMATICALLY USER-ONLY. Before
   escalating "another session touched X" or "is the move done?": attempt
   read-only disambiguation against a known manifest or expected inventory
   (ls both locations, diff against the deliverable list). Escalate ONLY when
   the observation is genuinely ambiguous — partial state, both locations
   populated, inventory mismatch — and then report what the check SHOWED,
   not just that you're blocked. "Another session touched X" triggers a
   verification step, not a question. (Added 2026-07-07 after the evals-
   relocation pause was over-applied: the move was fully discoverable by
   ls + manifest match.)
3. PERMISSION SCOPE. Pause only before: destructive actions, shared-helper
   edits, scope changes, budget overruns. "May I run a grep?" is never a
   valid question.
4. BATCHED PHASES PER RUN. Multiple phases may run in one session, subject to:
   a. Each phase still emits its own Evidence Packet section; a phase is
      DONE only when its packet section exists. No merged "all done" claims.
   b. HARD PAUSE (report + wait) remains before: live-injection changes,
      shared-helper edits, anything that alters behavior for concurrent
      sessions. Shadow-mode, warn-mode, docs, fixtures, and eval code
      proceed without pause.
   c. Rule 6 (bounded-branch) unchanged — any scope surprise or new shape
      still pauses the run regardless of batch authorization.
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
- **Gold corpus canonical path: `P:/.data/evals/`** (verified 2026-07-07).
  Phase 1 corpus relocated from `P:/.claude/hooks/evals/` → `P:/.data/evals/`
  to escape Claude Code's hardcoded `.claude` write-protection. Verification:
  ls target = 4 gold fixtures (0f183615, 4897f5bd, a07ff025, b2014a6e) +
  extract_fixtures.py + replay_eval.py + test_replay_eval_corrupt.py +
  misses.jsonl (8/8 manifest items); ls source = absent. .claude subtree is
  write-protected; relocation is the only fix. Future reference convention:
  evals → `P:/.data/evals/`, never under `.claude/`. Expiry-on-relocation
  applies to any subsequent move — re-run the manifest check + update this
  fact on every move.

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

### Phase 1 — Gold replay corpus + runner [DONE 2026-07-07]
4-transcript gold corpus built from stop_blocks.jsonl: 4897f5bd (epistemic
triple-fire + partial recovery, 3 turns, live gate), a07ff025
(deletion_verification), 0f183615 (perf_attribution re-fire), b2014a6e
(unverified_stance empty-hedge). e1960aff (lazy_workaround FP) shipped as a
misses.jsonl seed instead — 0 stop_blocks rows; #1214 removed the producing
path; only self_referen rows are a different gate (see decisions ledger).
Build: evals/gold/ fixtures (excerpt, expected behavior_type classes,
earliest-cause turn, disallowed conclusions, expected destination) +
replay_eval.py mirroring cc-aca-epistemic/.eval/judge_eval.py holdout
discipline (single-source live validate() import, no hand-copied prompt) +
extract_fixtures.py provenance tool + test_replay_eval_corrupt.py.
Verify bar MET: green on expected (STRUCTURAL 6/6, LIVE 3/3) + corrupt-one-
fixture mismatch detection (4/4, three modes). 3 DRIFT findings surfaced on
4897f5bd (post-#1215 block→allow/warn downgrades) — reported not asserted.
Evidence Packet: analysis/phase_1_gold_replay_evidence_packet_20260707.md.

### Phase 2 — Freshness-ruled runtime ground truth [PENDING]
runtime-ground-truth.md: fact | source | verification command |
last-verified | expiry trigger. Sessionstart injection via cc-aca-session
(router.py registration, NOT hooks.json). Expired entries render
`[STALE — reverify: <cmd>]`, never dropped or silently trusted. Add
cumulative injection budget across injectors (ground truth +
mechanism_manifest protected; recall segments truncate first).

**Seed entry (first row of the ground-truth table):**
| fact | source | verification command | last-verified | expiry trigger |
|------|--------|----------------------|---------------|----------------|
| Gold corpus canonical path = `P:/.data/evals/` | `ls P:/.data/evals/` + manifest match (4 fixtures + 3 .py + misses.jsonl) | `ls P:/.data/evals/ P:/.data/evals/gold/` | 2026-07-07 | any `evals/` relocation — re-run manifest check + update this row + the verified-facts block |

### Phase 3a — External-fact claim shape (predicate + offline calibration) [DONE 2026-07-07]
Pure-text predicate for external-world claims: `ExternalFactKind =
{version_assertion, api_behavior_claim, entity_existence, ecosystem_fact}`.
Two name classes (`_CAP_NAME` bare-major only in api_behavior with a verb;
`_LOW_NAME` requires dotted/v) + `_GENERIC_WORDS` denylist — FP 171→0 on
stop_blocks.jsonl. Offline calibration: precision 1.0 / recall 0.8 on a
synthetic 12-row seed; gold corpus = 1 hit (GSM8K 51.7). Shipped as
`P:/.data/evals/external_fact_detector.py` + `shadow_eval.py` + 13/13 tests.
SHADOW-only: 0 real TPs in the corpus (external-fact claims are a
false-negative surface — never caught, absent from stop_blocks), so per the
gate-discrimination rule it cannot block until Phase 6 reseeds real TPs.

### Phase 3b — Integration + evidence join + live SHADOW + re-calibration [DONE 2026-07-07]
1. **Single source:** predicate moved into `verification/claims.py`
   (`_detect_external_fact_claims`, `EXTERNAL_FACT` in `_CLASSIFICATION_MAP`,
   `extract_claims` extended). `evals/external_fact_detector.py` is now a thin
   re-export — no drift. (Anti_sycophancy `hypothesis_as_fact_detector` import
   made optional — source file missing, only `.pyc` exists; pre-existing
   breakage, fixed in-scope so the emitter doesn't fail-open forever.)
2. **Evidence join** (`verification/engine.py:_verify_external_fact_claim`):
   `EXTERNAL_FACT` claim SUPPORTED only if a same-session WebSearch/WebFetch/
   mcp__*api* event covers a target, or an unexpired runtime-ground-truth row
   matches; else SILENT. Stale rows (past YYYY-MM in expiry_trigger) never
   SUPPORT. Wired in `match_claim_to_events` BEFORE the path-oriented pre-filter.
3. **Live SHADOW emitter** (`Stop.py:_run_external_fact_shadow`): emits one
   row per SILENT EXTERNAL_FACT verdict to
   `logs/diagnostics/external_fact_shadow.jsonl` via `append_jsonl_safe`
   (Path, not str — bug caught in smoke). Non-blocking, no stderr, no
   additionalContext; gated by `EXTERNAL_FACT_SHADOW_ENABLED` (default true);
   fail-open. Called from `main()` after the gate sweep.
4. **Re-calibration through the integrated path:** gold still 1,
   stop_blocks still 0, seed precision 1.0 / recall 0.8 — numbers hold.
   13/13 detector tests + 3/3 new evidence-join tests + 29/1skip engine
   suite (no regression).

**Plan deviation logged:** Phase 3 was initially marked "DELIVERED" when
only 3a had landed. Staging 3a-then-3b was reasonable, but shipping staged
work under DELIVERED without reporting the fork violates bounded-branch
discipline (same class as the renderer-cap omission, `misses.jsonl` row 2).
Corrective action: plan + packet split into 3a/3b; deviation row appended to
`misses.jsonl` (`phase_3a_shipped_as_phase_3_under_delivered_20260707`).

### Phase 4 — Completion contract at report time [DONE 2026-07-07]
Upgraded debrief/references/completion-evidence-contract.md from after-action
mining rubric to report-time requirement: ledger table (claim | claim_type |
authority_required | evidence_provided | status | remaining_gap) on
implementation reports. Extended Stop_fake_done_detector for ledger presence
(Tier 4, WARN mode). Did NOT duplicate cross_validator / artifact_enforcement
— Tier 4 is structural (ledger PRESENCE), not per-claim verification. See
phase_4_completion_contract_evidence_packet_20260707.md.

### Phase 5 — Misses ledger + promotion loop [DONE 2026-07-07]
/debrief writes misses.jsonl (fixture ref, behavior_type, evidence) — live.
/improve promotes rubric/gate changes only when: replay evidence exists,
≥2 independent occurrences or explicit user confirmation, gold replay green.
Recorded Amendment Protocol (two-factor: frequency × blast-radius) in
bad-behavior-rubric.md as the amendment threshold header. Seeded open-question
rows: (1) discoverable_fact_offloading recurrence counter; (2) #906 channel.
See phase_5_promotion_loop_evidence_packet_20260707.md.

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
- 2026-07-07: Phase 1 — 4 fixtures shipped, not 5. e1960aff (lazy_workaround
  self-referential FP) has 0 stop_blocks rows; #1214 removed the producing
  code path and historical blocks rotated out of the log. Substituting a
  different behavior class would violate Rule 7 (replay evidence before
  promotion) — shipped as misses.jsonl seed for Phase 5 instead. Real
  gate-block transcripts beat imported chat transcripts (decision stands).
- 2026-07-07: Phase 1 — two-layer drift-aware corpus design. Each fixture
  encodes historical intent (block record) AND live expected (current
  validate()) separately; replay_eval asserts structural hash + live
  expected only, REPORTS recorded-vs-live delta as a finding. Rationale:
  a drifted gate must not silently rewrite corpus history; the delta IS the
  signal the program exists to surface. 3 post-#1215 downgrades caught on
  4897f5bd.
- 2026-07-07: Rule 4 amended ONE-PHASE-PER-RUN → BATCHED-PHASES-PER-RUN.
  Batch scope earned after Phases 0 / 0.5 / 1 each shipped a clean Evidence
  Packet with no scope creep or premature "all done" claims. Guardrails
  retained: per-phase packet sections (4a), hard-pause before live-injection /
  shared-helper / concurrent-session-impacting changes (4b), Rule 6 scope-surprise
  pause unchanged (4c). First authorized batch = Phase 1.5 leftovers + Phase 2
  (pause at router.py registration) + Phase 3 (shadow-only).
