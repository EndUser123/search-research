---
thread_id: a4f2e8c1-7b3d-4e9f-a6c2-1d8e5f3a7b11
parent_handoff_path: P:/docs/handoffs/close-lighter-equivalent-loophole-20260725/HANDOFF.md
current_session_id: 019f9488-2a86-7bf1-ae6f-eeb341ec7095
produced_at: 2026-07-25T21:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: fec1636ae0983b157063cc469c151903d0f2a3b5
source_concept: P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md
---

# Handoff: Apply the "code orchestrates, model judges" pattern across skills

## Objective

Implement the wiki concept `code-orchestrates-model-judges-skill-scale` as a coherent cross-skill workstream. The concept names the pattern (LangGraph StateGraph + conditional edges at the skill-helper-script scale). This handoff bundles the tactical fix (close-lighter-equivalent), the strategic pattern (5 candidate refactors), and three /check improvements surfaced this session.

**Why bundle:** the pattern is the same across all targets. Implementing it once with the right vocabulary makes the next application cheaper. Doing them in separate sessions loses the compound return.

## Status

PARTIAL — the first close-specific vertical slice is implemented in the
working tree and verified; the broader obligation ledger and host-level child
skill dispatch remain open.

## Resolution: apply the existing obligation-ledger design to `/close`

**Decision (2026-07-26):** Do not create a new wiki architecture and do not
adopt LangGraph. Apply the existing
`instruction-to-state-closure-gap-obligation-ledger` concept to `/close` using
the current Python helper/state-machine pattern.

The controller orchestrates **obligations and validated outcomes**, not direct
slash-command execution. Grok Build does not currently expose a verified API
that lets Python invoke and await `/aar`, `/tp session`, `/wiki`, or
`/handoff` inside the active conversation. Therefore the implementation must
not claim that it can force those skills to run. It can require their
session-bound completion evidence before allowing a clean close state.

### Close-specific obligation flow

```text
scan
  -> identify obligations
  -> request child action or bounded judgment
  -> validate session-bound receipt
  -> rescan
  -> render only when obligations are terminal
```

Each obligation needs:

- stable obligation ID and current session ID;
- required action or judgment type;
- expected postcondition;
- verifier and receipt path/schema;
- evidence fingerprint or identity binding;
- lifecycle state: `OPEN`, `SATISFIED`, `BLOCKED`, `WAIVED`, or `SUPERSEDED`.

### Required close receipts

- **AAR:** matching session ID, `_run.json` status `completed`,
  `aar-report.md` present, report validation passed, and evidence identity
  recorded. `_run.json` with `status: started` is not sufficient.
- **TP session review:** structured NOW/NEXT/LATER/FILTER judgment receipt,
  including actionable insights, dispositions, and evidence references.
- **Wiki/handoff capture:** the artifact explicitly references the obligation
  or continuation candidate it satisfies; same-day existence is insufficient.
- **Final report:** unresolved obligations produce `CLOSE INCOMPLETE`, never a
  clean `SESSION CLOSED` claim.

Operator waivers are terminal but distinct from satisfaction: they must be
session-bound, explicit, visible in the report, and never rendered as clean
completion.

### Boundary constraints

- Keep read-only scanning separate from mutation actions such as auto-commit,
  wiki writes, and handoff creation.
- Treat the report validator as a presentation/consistency check, not proof
  that child work completed.
- Do not claim live child-skill orchestration until a Grok dispatch or emission
  control boundary is identified and tested.

This resolution applies the existing wiki design; it does not add a second
obligation-ledger concept.

### Implemented slice (2026-07-26)

`C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py` now treats a
retrospective as satisfied only when the scanner finds a session-matching AAR
run with a report that passes the existing AAR report-plus-packet validator.
An `_run.json` marker, a missing report, a missing preprocess packet, or a
validator failure leaves the retrospective gate at `needs_attention` when
substantive work exists. The compact renderer converts unresolved attention
gates, open handoffs, verification gaps, and manual review into
`CLOSE INCOMPLETE`; only a terminal scan state can emit the clean-close line.

Added synthetic coverage for missing-report rejection, validated-report
acceptance, invalid-receipt gate resolution, and incomplete final rendering.
Verification: `python -m pytest -q` in the close skill — **293 passed**;
`python -m py_compile __lib\\close_accounting.py` — pass; `git diff --check` —
pass.

The AAR limitation is now addressed in
`C:\Users\brsth\.grok\skills\aar\__lib\completion_receipt.py`: after final
report validation, it atomically writes `status: completed`, completion time,
report path, packet path, and report SHA-256 into `_run.json`. `/close` now
requires that terminal state and matching hash.

Relevant AAR tests pass: `python -m pytest -q` — **571 passed**; close remains
**293 passed**. The AAR reference loader now has an executable CLI boundary
that rejects unknown trigger names, and its module contract names the actual
loader function. The finalizer now fails closed when report hashing is
unreadable, without mutating `_run.json`; regression coverage includes that
failure path alongside real packet-validator, path-binding, and idempotence
coverage. Compile and `git diff --check` also pass.

The close report hardening is now extended in
`C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py` and
`close_accounting.py`: hybrid reports headed only `Session close report` or
ending in `CLOSE INCOMPLETE` cannot bypass canonical-layout validation;
unresolved work is labeled `Open continuation / unresolved`; and an
unresolved retrospective makes the next safe action explicitly `Run /aar and
rerun /close`. The validator's successful CLI output now states the report
disposition separately from field consistency. Close verification: **294
passed**; compile, diff check, and a canonical-report CLI smoke test pass.

## Background

Session 019f9488 (2026-07-25) surfaced a recurring pathology: the model manufactured 4 rationalizations in one session to skip mandatory work. The `/aar` (run properly) traced this to a PROBLEM_CLASS pattern — closure pressure manufactures prose-level bypasses that prose rules cannot prevent. The structural fix is code enforcement at the skill-helper-script scale.

The wiki concept `code-orchestrates-model-judges-skill-scale` (written this session) names the pattern. LangGraph is the conceptual reference: StateGraph + nodes + conditional edges, where conditional edges are routing functions that return the next node from state. The chosen implementation remains a small Python controller because it already fits this bounded local workflow and LangGraph cannot manufacture a missing Grok skill-dispatch boundary.

This handoff bundles everything that applies the pattern, ranked by ROI.

## The workstream (ranked by ROI)

### Tier 1: Tactical (highest ROI, smallest scope)

**1. `/close` Fix 4 — mechanical AAR-to-handoff coverage gate**
- Source: handoff `close-lighter-equivalent-loophole-20260725` (Fix 4)
- Add `aar_handoff_coverage` and `decision_wiki_coverage` gates to `close_accounting.py`
- First concrete instantiation of the pattern
- ~30-60 min Python, includes test

**2. `/check` PR 1 augmentation — three new signals from this session**
- Source: approved design `P:/docs/designs/2026-07-25-check-orchestrator-design.md`
- Add to PR 1's `scope_claim_mismatch` detector:
  - "inline-equivalent" pattern signal: agent claims X is "done inline" or "covered by" Y — equivalence claim requiring receipt
  - "decision-without-wiki" signal: decision language without a wiki concept (symmetric to post-verification-mutation)
- Reframe existing detectors explicitly as LangGraph conditional edges in code comments
- Augments the approved 4-PR plan; doesn't change its structure

### Tier 2: Strategic (medium ROI, medium scope)

**3. Refactor candidate skills to apply the pattern (split: code-enforceable now vs observe-then-refactor)**

**Correction 2026-07-25:** the original version of this section applied "observe-then-refactor" as a blanket rule. That was wrong. The wiki-save gates added this session are structurally identical to the prose gates bypassed 4 times this session — waiting for observation means waiting for the same failure. The optimal split is per-skill, based on whether the skill has a code layer to enforce through.

### Tier 2a: Code-enforceable NOW (skill has `__lib/*.py` helper)

| Skill | Helper exists | What to enforce | Effort |
|---|---|---|---|
| `/close` | `close_accounting.py` | Refuse `status: complete` unless wiki save ran OR explicit "no wiki-worthy findings" with reason | ~20 lines |
| `/aar` | preprocessor pipeline + report validator | Phase 9.5 wiki promotion: validator refuses complete unless PROBLEM_CLASS lessons have concepts | ~15 lines |
| `/model-benchmark` | `analyze.py` | Refuse done-state unless save step ran or no wiki-worthy findings | ~15 lines |

These three land in Tier 1 (tactical), not Tier 2. The bypass pattern is already observed (this session); the code layer exists; the enforceable check is "did the save step fire?" which is mechanical.

### Tier 2b: Observe-then-refactor (prompt-only skills, no code layer)

| Skill | Trigger to refactor |
|---|---|
| `/debrief` | A session runs /debrief but Phase 5 auto-save is skipped — a systemic finding has no wiki concept |
| `/verify` | Already partially code-enforced; extend when a verification bypass is observed |
| `/handoff` | Refactor when a handoff with dangling references is written and not caught |
| `/tp`, `/wargame`, `/review`, `/red-team` | Refactor when the save gate is observed bypassed. **Enforcement alternative:** cross-skill observers (`/check`, `/aar`) can detect the bypass without touching the skill itself — see "structural insight" below. |

### Structural insight: enforcement can live in observers, not just the skill

"Promote to code enforcement after observation" assumes the only enforcement path is through the skill being bypassed. But `/check` and `/aar` are cross-skill observers — they can detect save-step bypasses in ANY skill. So for prompt-only skills, the enforcement doesn't have to live in the skill; it can live in `/check`'s `decision-without-wiki` signal (already added to PR 1) or `/aar`'s continuation coverage.

This is the `/close` Fix 4 pattern (AAR-to-handoff coverage) generalized: any skill's save step can be checked by a downstream scanner.

### DONE 2026-07-25: shared `wiki_save_gate.py` is built and tested

**Status: SHIPPED** — commit `bfb0930` on P:/ repo. The "open decision" below is resolved: we built the shared script, not 4-5 per-skill scripts.

The gate is a single deterministic node at `P:/.agents/scripts/wiki_save_gate.py` that any skill calls after its save step:

```
python P:/.agents/scripts/wiki_save_gate.py --artifact <run-artifact-path> --skill <name> [--session <sid>]
```

Exit codes: 0=pass (concept written OR explicit no-findings marker), 1=fail (bypass caught), 2=n/a (no systemic findings), 3=error.

**What it catches:** the model cannot silently skip a save step. Either a wiki concept gets written, OR a sidecar `._wiki_save_status.json` explicitly records `status: no_findings` with a reason. Silent skip → gate fails → exit 1.

**7 tests passing** (`test_wiki_save_gate.py`): bypass caught, pass with concept, pass with marker, discrepancy caught (sidecar claims "saved" but no concept), no-findings n/a, no-artifact n/a, regex detection.

**Remaining work for the implementing session:** wire the gate into each skill's `__lib/*.py` (or for prompt-only skills, document the gate invocation in the SKILL.md so the model calls it). The gate itself is built; the wiring is per-skill. Per the optimal-vs-blanket split (Tier 2a vs 2b), the 3 skills with helper scripts (close, aar, model-benchmark) get the gate wired into their scanner; the 4 prompt-only skills (debrief, tp, wargame, review, red-team) get the invocation documented in SKILL.md as a mandatory post-save step that `/check` and `/aar` can verify was called.

### Tier 3: LangGraph decision — deferred

**Resolved 2026-07-26: do not adopt LangGraph for `/close` now.** The
workflow is bounded, sequential, local, and already represented by tested
Python gates. LangGraph would not solve the missing host-level skill-dispatch
or emission-control boundary. Reconsider only if multiple workflows need
shared resumable nodes, cross-process execution, complex branching, or the
hand-rolled controllers become harder to audit than the framework.

## Acceptance criteria

1. `/close` Fix 4 implemented + tested (from existing handoff)
2. The close-specific obligation/receipt contract above is implemented and
   tested; no clean close is possible with unresolved required obligations.
3. AAR completion requires `status: completed` plus a validated report, not
   merely an existing `_run.json`.
4. TP session judgment has a structured, session-bound receipt or is reported
   as unresolved.
5. Read-only scan and mutations are separately testable and idempotent.
6. `/check` PR 1 augmented with the 3 new signals (inline-equivalent, decision-without-wiki, LangGraph reframing)
7. At least 2 of the 5 Tier 2 candidate skills refactored to code-enforced coverage gates
8. Each new gate has a synthetic test case (create scenario where gate SHOULD fail; verify scanner catches it)
9. A live Grok test demonstrates the actual emission-control boundary before
   any claim of direct child-skill orchestration.

## Out of scope (do not implement)

- LangGraph framework adoption itself (Tier 3 — decision deferred)
- Changes to `/tp`, `/red-team`, `/review` (not in the candidate list — those are model-judgment-heavy skills where the pattern doesn't apply cleanly)
- The 3 prose-rule fixes from `close-lighter-equivalent-loophole-20260725` (Fixes 1-3) — those are guardrails, separately scheduled

## Integration with /why v3 (shipped by parallel session)

The parallel session shipped `/why` v3 (`ddf793d`, `774eb43`) — evidence-tiered, pattern-aware, with Step 15 feedback-to-wiki that uses synchronous cross-model review → direct write. **No conflict with this workstream.** The two complement:

- `/why` v3 already implements a version of the pattern at Step 15 (mechanical gate 15a + cross-model review 15b → direct write). It's an existence check on the wiki concept, not a coverage check. Could be enhanced under Tier 2 candidate #1.
- The `/check` "inline-equivalent" signal (Tier 1 #2) would catch exactly the failure mode that motivated `/why` v3's existence (the receipt-system zero-metrics misdiagnosis that `/why` Step 1 observation-verification now catches).

**Action:** the implementing session should read `/why` v3 SKILL.md Step 15 and verify the Tier 2 `/aar` refactor and `/why` Step 15 don't diverge in their wiki-writeback patterns.

## Verification plan

After implementation:
- Next `/close` invocation must mechanically fail when ACT_NOW items lack handoffs (Fix 4)
- Next `/check` run must catch "inline-equivalent" claims (Tier 1 #2)
- The refactored Tier 2 skills must show the pattern in their `__lib/*.py` files (coverage gate, not existence check)
- A retrospective wiki concept capture: "we applied the pattern to N skills; here's the compound-return measurement"

## Source evidence

- Wiki concept: `P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md` (177 lines, multi-source-verified, LangGraph as canonical reference)
- Parent handoff: `P:/docs/handoffs/close-lighter-equivalent-loophole-20260725/HANDOFF.md` (Fix 4 detail)
- /check design: `P:/docs/designs/2026-07-25-check-orchestrator-design.md` (4-PR plan, approved)
- AAR report: `P:/.artifacts/grok-aar/console_console_83b3323a-a71b-4f55-8a5d-6a41/20260725-close/aar-report.md` (pattern evidence)
- /why v3 SKILL.md: `C:/Users/brsth/.grok/skills/why/SKILL.md` (parallel-session integration check)
