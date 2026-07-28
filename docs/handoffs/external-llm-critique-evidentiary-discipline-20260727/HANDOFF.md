---
thread_id: external-llm-critique-evidentiary-discipline-20260727
parent_handoff_path: none
current_session_id: 019fa5a1-0446-7e02-9766-bd2457ee58c3
current_terminal_id: grok-build-primary
produced_at: 2026-07-27T16:46:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ac63013e8a17b30995e22f887142c2046f873659
---

# Handoff — Evidentiary-discipline gaps surfaced by external LLM critique of close-authority work

## Objective

Address four meta-discipline gaps that an external LLM correctly identified when
critiquing the close-authority implementation report (session 019fa5a1, commit
7148eb6). These are workspace-wide improvements to evidentiary discipline, NOT
the close-authority fix itself (which is tracked separately as live-integration
work on branch `close-authority-019fa5a1`).

## Why this exists

The close-authority report (prior turn) shipped a `CLOSE_AUTHORITY_ENFORCEMENT_PROVEN_WITH_LIMITATIONS`
verdict that the external critique correctly showed was overstated: the module
was standalone, not wired into the live `/close` path, yet the report labeled a
synthetic direct-function-call test a "real replay." The existing AGENTS.md rules
(Completion-language discipline, Claims-require-receipts, Evidence-scope
discipline) caught the *surface* of this but lacked the *specific axes* that
would have prevented the overstatement. Four gaps are genuinely new and actionable.

## The four gaps (clustered by shared root: enforcement/verification evidentiary discipline)

### GAP-1: Verdict taxonomy lacks COMPONENT-vs-LIVE axis

The workspace has verdict tokens (`PROVEN`, `PROVEN_WITH_LIMITATIONS`, `NOT_PROVEN`,
`PASS`, `FAIL`) but none distinguish "component proven in isolation" from "live
enforcement proven via the production path." The close-authority report used
`PROVEN_WITH_LIMITATIONS` when the accurate token was `COMPONENT_PROVEN — LIVE_NOT_PROVEN`.

**Root cause:** the verdict vocabulary conflates two independent axes — (a) does
the component work, (b) is it wired into production. A standalone-tested module
is component-proven; live enforcement requires the production path to invoke it.

**Fix direction:** extend the verdict vocabulary with a `COMPONENT_PROVEN — LIVE_NOT_PROVEN`
token (or a two-field verdict: `{component: PROVEN, live: NOT_PROVEN}`). Apply to
any enforcement/authority claim where the module exists but isn't wired in.

### GAP-2: No replay-realism rubric

The report labeled test_20 a "real replay" when it used synthetic digests
(`"replay-digest"`), direct function calls (`authorize_completion()`), and an
in-test fake. The AGENTS.md "Claims require receipts" rule exists but doesn't
define what makes a replay "real" vs "integration-style unit test."

**Root cause:** the workspace has test-discipline rules (TDD, anti-mock stance)
but no rubric for the specific claim "this is a real replay of the production path."

**Fix direction:** add a wiki concept defining replay realism tiers:
- **Unit test** — calls functions directly with synthetic inputs
- **Integration test** — calls real components but in a test harness (not the production entry point)
- **Real replay** — executes the actual production entry point (real CLI command, real scanner, real persistence, real validator reload), captures real artifacts at real paths

A report may only label a test "real replay" if it meets tier 3. Lower tiers must be labeled honestly.

### GAP-3: Baseline-aware regression contract missing

The report said "zero regressions" while 23 baseline tests were already failing.
That claim was technically accurate (no NEW failures) but evidentially weak —
with a dirty baseline, "zero regressions" needs a precise before/after failure-set
diff, not an assertion. The existing regression rules assume a clean baseline.

**Root cause:** the regression-discipline rules (`testing.md`, `/check` contracts)
assume the baseline passes. When the baseline has pre-existing failures (common
on this multi-writer host with dirty trees), "zero regressions" is ambiguous.

**Fix direction:** add a regression-reporting contract: when the baseline has N
failures, the regression report must state (a) baseline failure count, (b) post-change
failure count, (c) exact failure-set diff (newly-failing tests + newly-passing tests),
not an umbrella "zero regressions."

### GAP-4: No production-wiring gate for enforcement claims

The report claimed "enforcement proven" for a module that was not invoked by the
production path. The "Evidence-scope discipline" rule exists ("passing unit tests
does not prove live activation") but doesn't structurally gate enforcement claims
on production wiring.

**Root cause:** there is no mechanical check that an enforcement/authority module
is actually invoked by the production entry point. A standalone module with 20
passing tests can be reported as enforcement without the production path calling it.

**Fix direction:** either (a) a `/check` or `/review` rule that flags
"enforcement proven" claims when the module has zero callers in the production path
(detectable via grep for imports), or (b) a definition-of-done checklist item for
enforcement claims: "the production entry point invokes this module" verified by
showing the import + call site.

## What is NOT in this handoff (belongs in the close-authority /go task)

The critique also raised two design points about the close-authority module itself:
- 14-day freshness TTL should be lifecycle-ordering-based, not time-based
- `renderer_identity == "close_authority.py"` string is weak authority

These are close-authority design refinements, not workspace-wide discipline gaps.
They belong in the live-integration `/go` task (branch `close-authority-019fa5a1`),
not in this handoff.

## Read-first list

1. This handoff
2. `P:/.data/wiki/concepts/` — search for existing evidentiary-discipline concepts (receipt-before-write, claims-require-receipts, completion-language-discipline) to confirm these gaps aren't already covered
3. The external LLM critique (in session 019fa5a1 chat_history, the turn containing "## Verdict / The implementation report overstates what has been proven")
4. Commit `7148eb6` on branch `close-authority-019fa5a1` — the report that triggered the critique
5. `~/.grok/AGENTS.md` § "Completion-language discipline" and § "Claims require receipts" — the existing rules these gaps extend

## Verified facts

- [FACT] The close-authority report (commit 7148eb6, session 019fa5a1) used verdict `CLOSE_AUTHORITY_ENFORCEMENT_PROVEN_WITH_LIMITATIONS` while the module was standalone (verified: `git diff --stat HEAD` on the worktree showed zero modified files, only 2 untracked new files).
- [FACT] The report labeled test_20 a "real replay" while it used `"replay-digest"` and direct `authorize_completion()` calls (verified: read test_close_authority.py test_20 this session).
- [FACT] The report said "zero regressions" while 23 baseline tests failed (verified: pytest output showed 23 failed, 89 passed; failures were pre-existing at HEAD `af6450f` due to Workstream B `cfg` parameter mismatch).
- [FACT] No existing wiki concept defines replay-realism tiers or a COMPONENT-vs-LIVE verdict axis (verified: qmd search for "replay realism", "component proven", "live enforcement" returned no concept-level matches — needs confirmation when this handoff is acted on).

## Suggested next

These four gaps are low-urgency workspace-hygiene improvements. They prevent a
class of overstatement but do not block the close-authority live integration.
Suggested disposition:

- **GAP-1 (verdict taxonomy):** one wiki concept + an AGENTS.md rule update. Small.
- **GAP-2 (replay rubric):** one wiki concept. Small.
- **GAP-3 (baseline-aware regression):** one wiki concept + `/check` SKILL.md note. Small.
- **GAP-4 (production-wiring gate):** potentially a `/check` scanner rule (grep for callers). Medium.

Can be batched into a single session: "evidentiary-discipline gap-closing." Each
is independently shippable.

## Cross-references

- `P:/docs/handoffs/close-authority-*` (branch `close-authority-019fa5a1`) — the work that triggered this critique
- `P:/.data/wiki/concepts/claims-require-receipts-...` (if exists) — the parent rule these gaps extend
- Session 019fa5a1 — the session where the overstatement occurred and was critiqued

---

## Revision 1 — 2026-07-27T16:55:00Z (session 019fa5a1)

**Trigger:** a second external LLM critique of the live-integration report (commit b8db4d0) reinforced three of the original gaps and surfaced one genuinely new one.

### Reinforcements (deepen existing gaps, no new handoff needed)

- **GAP-1 reinforced:** proving the *negative* (bypass rejected) is insufficient for a PROVEN verdict; the *positive* terminal path (valid input → CLOSE COMPLETE → persisted receipt → reloaded → validated) must also be demonstrated in production. The first critique established component-vs-live; this adds the positive-vs-negative axis within "live."
- **GAP-2 reinforced:** the replay rubric must cover BOTH directions — rejection of invalid AND acceptance of valid. A replay that only proves rejection is half-evidence.
- **GAP-3 reinforced (concrete operationalization):** "the changed code path is `main()`, which is precisely what scanner/renderer tests exercise; therefore 'same code, no need to rerun' is unreliable." The rule: **execute the regression suites on the changed branch, do not infer regression safety from code-similarity reasoning.** Record exact baseline failures, then run on the integration commit, then report the diff.

### GAP-5 (NEW): authority-output channel unification

**The pattern:** when adding an enforcement/authority boundary, ensuring ONE field (e.g., `output.authority.verdict`) reflects it is insufficient. ALL consumer-visible output paths (JSON fields, compact human text, persisted receipts, validator inputs) must derive from the single authoritative result. Otherwise the system has split authority — one channel authoritative, one channel stale/independent — which is exactly the failure the boundary was meant to eliminate.

**Generalizable beyond close-authority:** applies to any system where a new authority layer is added atop an existing output path. The close-authority case (JSON `authority` field vs. compact renderer's independent verdict) is the instance; the principle is universal.

**Fix direction:** a wiki concept + an AGENTS.md rule: "when adding an authority/security boundary, audit every consumer-visible output path; all must delegate to the authority result, or the boundary is decorative." Detectable in review: grep for verdict-emission sites and confirm they all route through the authority module.

### Why no second handoff was created

This revision block captures the genuinely new content (GAP-5) and the reinforcements in-place. A second handoff would duplicate this one's scope (evidentiary discipline for enforcement claims) — itself an instance of the handoff-fragmentation-under-recurrence pattern documented in `P:/.data/wiki/concepts/handoff-fragmentation-under-recurrence.md`. Appending is correct; duplicating is the anti-pattern.

## Last user message (verbatim)

> "from the copy paste chat with another LLM, identify those things that we should want to address to improve usefulness and efficiency. /handoff create handoff files for them. Then /go [live integration prompt]"

## Epistemic labels

- [FACT] The four gaps are genuinely not covered by existing AGENTS.md rules (the rules exist but lack the specific axes identified). This is supported by the critique's correct identification of the overstatement that the existing rules did not prevent.
- [INFERENCE] These gaps are worth fixing workspace-wide (not just for close-authority) because the same overstatement pattern could recur on any enforcement/authority work. Confidence: medium — needs operator confirmation that the pattern is frequent enough to warrant formalization.
- [UNKNOWN] Whether a `/check` scanner can mechanically detect GAP-4 (enforcement module with zero production callers). Technically feasible via import-graph analysis; implementation cost unmeasured.

---

## Revision 2 — 2026-07-27T22:30:00Z (session 019fa5a1)

**Trigger:** auto-update — three of the five gaps now have partial wiki coverage from session work after Revision 1 was written.

### Wiki coverage shipped this session

- **GAP-1, GAP-2, GAP-3 now partially covered** by `P:/.data/wiki/concepts/verification-claim-admissibility.md` (written this session). The concept defines: (1) verdict vocabulary distinguishing `COMPONENT_PROVEN` from `LIVE_ENFORCEMENT_PROVEN` (covers GAP-1), (2) replay realism tiers — unit / integration / real replay (covers GAP-2), and (3) baseline-aware regression contract requiring explicit failure-set diff (covers GAP-3).
- **GAP-5 (authority-output channel unification)** referenced in the new `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` under "Implication for skill design" — the split-output anti-pattern is named as an instance of the enforcement-code maker-checker problem.
- **GAP-4 (production-wiring gate)** remains uncovered — no wiki concept or scanner rule yet. This is the only gap with no partial coverage.

### What remains for each gap

- **GAP-1/2/3:** the wiki concept defines the vocabulary and rubric, but the AGENTS.md rule update and `/check` SKILL.md note are NOT yet done. The concept is the specification; the enforcement mechanism (rule + scanner) is still pending.
- **GAP-4:** fully open. Needs a `/check` scanner rule design or a definition-of-done checklist item.
- **GAP-5:** named in the maker-checker concept but no standalone AGENTS.md rule yet. Could pair with GAP-4 as a review-time checklist.

### Status update

No change to disposition — all five gaps remain low-urgency workspace-hygiene improvements. The wiki concepts reduce the risk of the overstatement pattern recurring by making the vocabulary explicit, but structural enforcement (scanner rules, mandatory checklists) is still pending.

### New open items

None beyond what was already listed. The wiki coverage is additive; it doesn't change the fix directions.
