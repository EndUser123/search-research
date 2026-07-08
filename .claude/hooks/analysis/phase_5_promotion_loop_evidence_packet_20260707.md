# Phase 5 Evidence Packet — Promotion Loop

**Program:** Close-the-Loop telemetry reliability (6 phases)
**Phase:** 5 (misses ledger live + promotion gate + two-factor amendment rule + seeded open-questions) DONE 2026-07-07
**Date:** 2026-07-07
**Status:** DELIVERED. Phase 6 yield review reads the seeded rows starting ~2026-07-21.
**Auth context:** misses.jsonl is the live ledger; this phase wired the promotion gate and seeded the open-question counters Phase 6 will read.

---

## Completion Evidence Ledger

| claim | claim_type | authority_required | evidence_provided | status | remaining_gap |
|---|---|---|---|---|---|
| misses.jsonl is the live misses ledger | runtime_behavior_changed | Read of the file + count of rows | `P:/.data/evals/misses.jsonl` 5 rows parse clean: e1960aff, plan_fact_router_forwarding_20260707, phase_3a_shipped_as_phase_3, open_question_discoverable_fact_offloading_recurrence, open_question_task_906_channel | PROVEN | none |
| Promotion gate added to /improve | documentation_updated | Read of the new section | `improve-partner/skills/improve/SKILL.md` "Promotion gate — rubric / gate changes" (3-leg: replay evidence + gold replay green + (≥2 occurrences OR user confirmation)) | PROVEN | gate is prompt_advisory in /improve; runtime enforcement is NOT in scope (the gate is a /improve authoring discipline, not a hook) |
| Two-factor amendment protocol added to bad-behavior-rubric.md | documentation_updated | Read of the new section | `debrief/references/bad-behavior-rubric.md` "Amendment Protocol — promoting / retiring entries" (frequency × blast-radius table; rare+costly promotes at 1 occurrence, frequent+cheap waits at 5+) | PROVEN | none |
| Open-question rows seeded for Phase 6 | runtime_behavior_changed | Re-parse of misses.jsonl | `P:/tmp/seed_misses.py` → rows 4-5 appended; file parses 5/5 clean | PROVEN | both rows are OPEN; Phase 6 yield review (~2026-07-21) is the re-read trigger |
| discoverable_fact_offloading counter at 0 post-refinement | unresolved_gap | The counter row itself | `misses.jsonl` row 4: `counter_state.occurrences_since_rule2: 0`, threshold 5 (frequent-cheap leg) | PROVEN (the counter is honestly at 0) | counter must reach 5 OR user-explicit rare+costly exception before any rubric amendment on this class |
| #906 channel tracked | deferred_work | The channel row + task ref | `misses.jsonl` row 5: `task_ref: "#906"`, status in_progress | PROVEN | #906 not yet closed; if it closes before Phase 6, the closure evidence packet supersedes this row (Rule 8 SHA recording) |

**protection_level:** documentation_only (SKILL.md + rubric edits) + prompt_advisory (the promotion gate is a /improve authoring discipline, not a runtime hook). The misses.jsonl ledger itself is runtime_behavior_changed (it is read by future yield reviews).

---

## 1. Promotion gate (3-leg)

A `/improve` proposal that changes a rubric entry or a runtime gate (new
behavior_type, severity promotion WARN→BLOCK, predicate expansion, threshold
change) MAY NOT ship as a recommendation alone. All three legs required:

1. **Replay evidence** — at least one concrete transcript/fixture line the
   current rubric/gate missed.
2. **Gold replay green** — `P:/.data/evals/` re-run; existing TP/FP counts
   must not regress.
3. **Occurrence threshold OR explicit user confirmation** — ≥2 distinct
   occurrences in `misses.jsonl` OR user confirms in-channel.

Without the three legs, the change is a HYPOTHESIS, not a promotion.

## 2. Two-factor amendment rule (the threshold floor)

The occurrence threshold weighs **expected cost, not raw frequency**.
Judgment axis: `frequency × blast-radius`:

| Class | Frequency | Blast-radius | Promote at |
|---|---|---|---|
| Fabricated architecture facts, ship-blocking false claims, safety/correctness regressions | rare (1–2) | high (days lost, trust loss, irreversible state) | **1 occurrence + user confirmation OR 2 occurrences** |
| Offloaded discoverable facts, unsupported completion claims, lazy routing | frequent (≥5) | low (turn wasted, easy retry) | **5+ occurrences + yield data** |
| Sycophancy, name-based inference, single-occurrence misses | medium | medium | **2 occurrences (standard floor)** |

Rationale: a rare class that burns days wastes real budget per occurrence —
promote after one to stop the bleed. A frequent cheap class is cheap to
retry; promoting without yield data risks adding a noisy gate that fails on
FPs the corpus hasn't measured.

## 3. Seeded open-questions (Phase 6 reads these)

- **`open_question_discoverable_fact_offloading_recurrence`** — counter at 0
  post-Rule-2-refinement. Threshold 5 (frequent-cheap leg). Phase 6 yield
  review re-reads.
- **`open_question_task_906_channel_auto_commit_hardening`** — #906 in
  progress. Phase 6 re-reads; closure supersedes (Rule 8 SHA recording).

## 4. measured_tp_on_corpus (per the gate-discrimination rule)

This phase adds **no new enforcement gate**. The promotion gate is a
/improve authoring discipline (prompt_advisory), not a runtime hook — so
the gate-discrimination rule's "ship with measured_tp_on_corpus" requirement
does not attach. The two-factor rule is the analogue: it gates *future*
amendments, and each future amendment must carry its own measured_tp_on_corpus
under leg (2) (gold replay green) before it ships.

## 5. Unresolved items

- **misses.jsonl write path is ad-hoc.** This phase appended rows via a temp
  script (`P:/tmp/seed_misses.py` using `append_jsonl_safe`). /debrief does
  NOT yet auto-write to misses.jsonl from its finding pipeline — that wiring
  is deferred. The ledger is live (readable) but not yet auto-fed.
- **No runtime hook enforces the promotion gate.** A `/improve` run can
  still propose an amendment without the three legs; the gate is
  prompt_advisory, enforced by the model reading SKILL.md. A future Stop-tier
  check ("amendment proposed without replay evidence") is conceivable but
  NOT in scope — it would duplicate the Tier 4 ledger-presence pattern and
  the gate-discrimination rule already requires measured_tp_on_corpus for
  new gates.
- **The two-factor table's blast-radius tiers are qualitative.** "High /
  medium / low" blast-radius is judgment, not measurement. Acceptable for a
  rubric amendment threshold (which itself is prompt_advisory); would need
  quantification before any runtime hook could enforce it.

## 6. What was skipped (ponytail)

- No auto-write from /debrief to misses.jsonl (the ledger is live and
  readable; auto-feeding is a separate wiring task, deferred).
- No runtime hook on the promotion gate (prompt_advisory is the right
  ceiling for an amendment-threshold rule).
- No quantification of blast-radius (qualitative tiers are correct for a
  rubric header; quantification would be over-engineering for a rule that
  fires on amendment proposals, not on every turn).
