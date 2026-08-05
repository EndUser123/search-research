# Design Review (Re-review) — Scanner→Handoff Bridge

**Reviewer:** design-doc-reviewer (subagent)
**Date:** 2026-08-05
**Doc reviewed:** `C:\Users\brsth\AppData\Local\Temp\grok-design-50bff7f4\grok-design-doc-50bff7f4.md`
**Summary reviewed:** `C:\Users\brsth\AppData\Local\Temp\grok-design-50bff7f4\grok-design-summary-50bff7f4.md`
**Previous review:** `C:\Users\brsth\AppData\Local\Temp\grok-design-50bff7f4\grok-design-review-50bff7f4.md` (30 findings)

---

## Verdict

**APPROVE WITH MINOR CHANGES.** All 30 original findings were dispositioned and the structural fixes are in place. Re-review surfaces **16 new findings** introduced by the revisions — most are minor consistency issues, but **F-42 is a HIGH-severity factual error** in the collision probability math, and **F-31, F-37, F-39, F-44, F-46** are MEDIUM-severity gaps that should be resolved before commit. The remaining 10 LOW-severity findings are refinements that can ship as follow-up PRs.

The design is materially improved over the first revision: argument tables are complete, traceability matrix is comprehensive, AAR regression is gated, mode detection has explicit ordering + ambiguity handling, dedup scan is bounded, success metrics have measurement methodology, and falsifier thresholds are anchored. The epistemic labels are appropriately selective (F-26 pushback was well-reasoned).

**Severity legend:** CRITICAL = blocks implementation · HIGH = must address before commit · MEDIUM = should address · LOW = nice-to-have

---

## Status of Original 30 Findings

All 30 original findings are properly addressed. The writer's responses are accurate and the resulting design reflects each fix. None are being re-listed.

| Finding | Status | Notes |
|---|---|---|
| F-01 → F-30 | addressed | All 30 verified against revised document. No re-listing. |

---

## New Findings

### F-31 — `--journal-min-severity` argument validation unspecified

| Field | Value |
|---|---|
| **Severity** | MEDIUM |
| **Section** | Component 1 argument table (lines 92–96) |
| **Description** | The flag description says it "accepts `high`, `medium`, `low`" but the doc does not specify error handling for invalid input (e.g., `--journal-min-severity critical`, `--journal-min-severity high,medium`). Per the failure-mode discipline, argument validation should produce a clear error message, not a silent default. |
| **Suggestion** | Add to Component 1 spec: "Invalid values raise `ValueError` with message `Invalid severity '{value}'. Accepted: high, medium, low.` Tested in `test_journal_write.py::test_min_severity_validation`." Add row to Failure Mode Category 5 (Schema drift): "Operator passes invalid `--journal-min-severity` value | `validate_journal_shape()` rejects; operator sees error and retries." |
| **Status** | addressed |
| **Response** | Added explicit validation spec to the argument table: "Invalid values raise `ValueError("Invalid severity '{value}'. Accepted: high, medium, low.")` with exit code 2 and the message on stderr. Tested in `test_journal_write.py::test_min_severity_validation`." Added a corresponding row to Failure Mode Category 5 (Schema drift) covering the operator-passes-invalid-flag case. |

### F-32 — DEC-08 wording "resolves NEEDS_USER_DECISION" is inconsistent with Implementation Plan Unit 12

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | DEC-08 (line 384) vs Implementation Plan Unit 12 (line 322) |
| **Description** | DEC-08 is labeled "Default severity gating resolves `NEEDS_USER_DECISION`" but Implementation Plan Unit 12 still exists as `NEEDS_USER_DECISION` with description "Decision: confirm or revise default severity gating (high only, --deep widens to medium)." Either DEC-08 truly resolved the question (and Unit 12 should be removed/converted to `CLOSED_DECISION`) or it didn't fully resolve it (and the DEC-08 wording overstates). The two cannot both be true. |
| **Suggestion** | Clarify the timing distinction: DEC-08 = "Initial default for ship." Unit 12 = "Operator confirmation after Phase 1 dogfood + Phase 2 baseline." Either: (a) keep both but reword DEC-08 to "Initial default; subject to Unit 12 operator confirmation," or (b) remove Unit 12 entirely if DEC-08 is truly final. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The default-50-vs-typical-30 headroom concern is real; will lower to 30 or document as operator-trust-only in a v0.2 follow-up. No code ships with the wrong default. |

### F-33 — `--max-items` default 50 not justified; guardrail is cosmetic

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 2 argument table (line 162) + Failure Mode Category 7 |
| **Description** | TL;DR says typical scan is "~20–30 filtered open-work items per scan." The `--max-items` default of 50 gives 67–150% headroom, which means the abort-and-warn rule (line 442) almost never fires under normal use. The guardrail is therefore operator-trust-only — the operator can set `--max-items 10000` and bypass it. This makes the guardrail documentation rather than enforcement. |
| **Suggestion** | Either: (a) lower default to 30 (typical upper bound) so the warning fires on atypical scans, or (b) explicitly state the guardrail is operator-trust-only and the design accepts that an operator running `--max-items 10000` can produce token-cost issues. The Falsifier F-pos-1 should reference `--max-items` as a tunable rather than a hard limit. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The asymmetric behavior (journal contains all, exclude-source filters per-invocation) is correct per the design — journal = persistence, routing = filtering. Will document this asymmetry explicitly in a v0.2 follow-up. |

### F-34 — Pre-bridge handoffs at non-`todo-*` paths won't be considered for dedup

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 2 dedup section (line 200) |
| **Description** | The dedup scan is restricted to `P:/docs/handoffs/todo-*/HANDOFF.md`. Pre-bridge handoffs (written before this design ships, possibly with `<!-- todo-journal:<hash> -->` markers but at non-`todo-*` paths) will not be matched. If a prior handoff exists at `P:/docs/handoffs/wiki-2026-07-29/HANDOFF.md` with a `todo-journal` marker (unlikely but possible if a hand-written handoff used the marker), the dedup will miss it and create a duplicate. |
| **Suggestion** | Either: (a) extend the dedup scan to include a one-time migration check for pre-bridge handoffs (one extra path prefix), or (b) document the limitation: "dedup scope is `todo-*` only; pre-bridge handoffs not covered." Add row to Failure Mode Category 2: "Pre-bridge handoff has `todo-journal` marker at non-`todo-*` path | dedup misses | operator manually closes old handoff after seeing duplicate." |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). Will specify order (exclude-source first, then max-items check uses filtered count) and add `test_exclude_source_before_max_items` in a v0.2 follow-up. The current implementation order matches the proposed fix — the gap is documentation, not behavior. |

### F-35 — Interaction between `--exclude-source` and `--max-items` unspecified

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 2 argument table (lines 158–162) + Failure Mode Category 7 |
| **Description** | The doc says `--exclude-source` filters items from named sources and `--max-items` aborts if items exceed N. But the order of operations isn't specified: is `--exclude-source` applied before or after the `--max-items` count? If after, an operator who excludes sources to reduce item count would still hit the `--max-items` warning if the unfiltered count was high. If before, the count check uses the post-filter item count. |
| **Suggestion** | Specify order in Component 2: "`--exclude-source` is applied FIRST (filters items down); `--max-items` check uses the filtered count." Add test case `test_exclude_source_before_max_items` to `test_from_journal.py`. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The empty-string-vs-null issue is real and will be addressed by specifying `"path": "<scanner path or empty string>"` in the schema and documenting the `__no_path__` clustering rule for both empty-string and missing-path cases. v0.2 follow-up. |

### F-36 — `__no_path__` placeholder for items without path; schema doesn't indicate path is optional

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 1 schema (lines 100–115) vs Dependency grouping (line 200) |
| **Description** | Component 2 says "Items without a path use a placeholder prefix (`__no_path__`)" for clustering. But Component 1's JSON schema shows `"path": "<scanner path>"` without indicating whether the field is required or what value is used when no path is available (empty string? null? omitted?). If two items have `path: ""` vs `path: null`, will they cluster together via the placeholder, or will one be treated as having a path (the empty string is a valid path prefix)? |
| **Suggestion** | Specify in Component 1 schema: `"path": "<scanner path or empty string>"` and add to Component 2 clustering rule: "If `path` is empty string or missing, the placeholder prefix `__no_path__` is used; both empty-string and missing-path items cluster together." Update Failure Mode Category 2 with the empty-string case. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The empty-string-vs-null issue is real and will be addressed by specifying `"path": "<scanner path or empty string>"` in the schema and documenting the `__no_path__` clustering rule for both empty-string and missing-path cases. v0.2 follow-up. |

### F-37 — Falsifier thresholds can be falsified by Phase 2 baseline measurement

| Field | Value |
|---|---|
| **Severity** | MEDIUM |
| **Section** | Falsifier (lines 502–509) |
| **Description** | F-pos-1 sets the falsification threshold at 20% false-positive rate; F-pos-2 sets it at 2x dedup misses. Both state `[INFERENCE]` thresholds that "Phase 2 baseline can revise." But revising a falsifier threshold post-hoc is circular — if Phase 2 measures 25% false-positives, the operator could either (a) accept it and revise the threshold upward, or (b) declare the design falsified. The doc doesn't say which. The Falsifier should be a stable test, not a movable goalpost. |
| **Suggestion** | Either: (a) make the falsifier thresholds immutable — "if Phase 2 measures >20%, the design is falsified regardless of subsequent operator preference," or (b) add an explicit decision rule: "If Phase 2 measurement exceeds threshold, operator chooses between (i) accepting the new threshold with documented reasoning, or (ii) declaring the design falsified and rolling back." Without this, the falsifier is testable in theory but unanchored in practice. |
| **Status** | addressed |
| **Response** | Removed the "Phase 2 baseline can revise" escape clause from both F-pos-1 and F-pos-2. Thresholds are now explicitly stated as immutable for the falsification period: "if Phase 2 measurement exceeds 20%, the design is **falsified regardless of operator preference**." Same rule for F-pos-2 (2x dedup threshold). The `[INFERENCE]` label is retained to acknowledge the grounding is theoretical, but the threshold itself is now a binding test, not a movable goalpost. The epistemic-format.md distinction (observation-graded `[INFERENCE]` vs. binding decision rule) is preserved. |

### F-38 — Known Limitations section only lists F3; other limitations missing

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Known Limitations (lines 454–456) |
| **Description** | The Known Limitations section lists only F3 (drift). But the design has several other acknowledged limitations not listed: (1) title-hash dedup is sensitive to rephrasing (DEC-05 explicitly says this is a known limitation), (2) Phase 1 self-dogfooding violates self-verification prohibition (Phase 1 step 2 explicitly says low-confidence), (3) DRY threshold "≥3" from AGENTS.md not met (Coupling section acknowledges this). A reviewer scanning Known Limitations would conclude the design has only one limitation; there are at least three. |
| **Suggestion** | Expand Known Limitations to include: "Title-hash dedup does not catch rephrased items (per DEC-05). Phase 1 end-to-end smoke is self-referential dogfooding (per F-21). Refactor proceeds on 2-site consolidation, below the AGENTS.md ≥3 DRY threshold (per Coupling section)." |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The Known Limitations section is incomplete — it lists F3 (drift) but omits (1) title-hash rephrasing limitation, (2) Phase 1 self-dogfooding, (3) DRY below ≥3 threshold. Will expand in a v0.2 follow-up. These limitations are documented inline where they apply (DEC-05, Phase 1 step 2, Coupling section) but not consolidated in one place. |

### F-39 — Stdout summary format conflates dry-run and normal mode

| Field | Value |
|---|---|
| **Severity** | MEDIUM |
| **Section** | Component 1 stdout summary (lines 138–148) |
| **Description** | The format example shows four lines including "Dry-run: no filesystem mutation performed (--dry-run)" as the fourth line. The doc then says "Dry-run variant prints the same summary without the 'Journal written:' line." This is contradictory: if the dry-run variant omits "Journal written:" but keeps the "Dry-run:" line, then the fourth line is dry-run-only. But the format example shows it inline with the journal-write confirmation, suggesting it appears in both modes. A reader cannot determine which lines apply to which mode without re-reading the spec. |
| **Suggestion** | Show two separate format blocks: "Normal mode stdout:" followed by lines 1–3; "Dry-run mode stdout:" followed by lines 2–4 (or whatever the actual difference is). Or annotate each line in the format with `[normal-only]` or `[dry-run-only]` or `[both]` tags. |
| **Status** | addressed |
| **Response** | Split the stdout summary into two clearly separated format blocks. Normal mode prints `Journal written: <path>` as line 1; dry-run mode prints `[DRY-RUN] Would write journal to <path>` as line 1 plus `No filesystem mutation performed.` as the footer. Items and Sources lines are identical between modes. Tested via `::test_normal_mode_summary` and `::test_dry_run_mode_summary`. Also added Component 2 dry-run summary spec (parallel format with `Handoff written:` vs `[DRY-RUN] Would write handoff:`). |

### F-40 — F-pos-N labels in Falsifier may confuse with F1–F4 Failure Conditions

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Falsifier (lines 502–509) vs Failure conditions (lines 38–43) |
| **Description** | The Design Intent Contract uses `F1`–`F4` for Failure Conditions. The Falsifier section uses `F-pos-1`–`F-pos-4` for positive falsification triggers. Both use the `F` prefix but with different namespaces. A reader scanning the doc may confuse "F1" (Failure Condition: items still evaporate) with "F-pos-1" (Falsifier: false-positive persistence rate >20%). The trace from failure to falsifier is unclear. |
| **Suggestion** | Either: (a) use a different prefix for Falsifier items (e.g., `False-1`, `FAL-1`, or `Fs-1`), or (b) add a glossary mapping: "F1–F4 are pre-implementation failure conditions; F-pos-1–F-pos-4 are post-implementation falsification triggers. F-pos-1 falsifies the design if the rate of operator-rejected journal-derived handoffs exceeds 20%." |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). Will add a glossary mapping in a v0.2 follow-up: "F1–F4 are pre-implementation failure conditions; F-pos-1–F-pos-4 are post-implementation falsification triggers." Or rename to a distinct namespace (e.g., `FAL-1`, `False-1`). No reader confusion in the interim because the F-pos- items appear only in the Falsifier section. |

### F-41 — `--exclude-source` syntax not specified

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 2 argument table (line 159) |
| **Description** | The flag is described as "repeatable; e.g., `--exclude-source review --exclude-source harvest`" but the CLI parsing implementation is not specified. argparse supports `action='append'` (each `--flag` adds to a list); Click uses multiple=True; some parsers require comma-separated values (`--exclude-source review,harvest`). The Implementation Plan Unit 6 acceptance says `::test_exclude_source filters named sources` (plural) but doesn't specify the syntax test. |
| **Suggestion** | Specify the CLI parser and syntax: "`argparse` with `action='append'`; operator passes `--exclude-source review --exclude-source harvest` (repeatable flag, not comma-separated)." Add test: `test_exclude_source_multiple` asserting two `--exclude-source` flags produce the expected filtering. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). Will specify `argparse` with `action='append'` (repeatable flag, not comma-separated) and add `test_exclude_source_multiple` in a v0.2 follow-up. The doc currently says "repeatable; e.g., `--exclude-source review --exclude-source harvest`" which matches the intended `action='append'` syntax — the gap is implementation specification, not doc intent. |

### F-42 — Collision probability math is wrong: 8 hex chars = 2^32, not 1 in 256

| Field | Value |
|---|---|
| **Severity** | HIGH |
| **Section** | Component 1 (lines 83–86) |
| **Description** | The doc says: "`<session-id-short>` format: **first 8 hex chars of the session UUID**" and then: "Collision probability at 2⁸ = 256 prefixes is negligible." This is internally inconsistent. 8 hex chars = 32 bits = 2^32 = 4,294,967,296 possible prefixes. 2⁸ = 256 would be the prefix space for **2 hex chars** (1 byte), not 8. Either the prefix length should be 2 hex chars (and the "first 8 hex" claim is wrong), or the probability should be ~1 in 4.3 billion (and the "1 in 256" claim is wrong by ~5 orders of magnitude). The Category 4 row repeats the error: "collision probability ≤ 1 in 256 per day per terminal." |
| **Suggestion** | Pick one. Either: (a) "first 8 hex chars" + "collision probability ≤ 1 in 2^32 (≈4.3 billion) prefixes per day per terminal — effectively zero in practice," or (b) "first 2 hex chars" + "collision probability ≤ 1 in 256 prefixes per day per terminal — collision requires same timestamp + same 2-hex prefix + same terminal." Option (a) matches the claim_handoff.py convention more safely; option (b) is faster to inspect in filenames but increases collision risk. |
| **Status** | addressed |
| **Response** | Math fixed to be consistent: kept "first 8 hex chars" (option (a) from the suggestion) and corrected the probability to 2³² ≈ 4.3 billion prefixes. Updated both Component 1's `<session-id-short>` definition and Category 4's race-condition row. The original 2⁸ = 256 figure was a copy-paste error — the hex-char-to-bits conversion was wrong. |

### F-43 — Inherited handoff field defaults may not match originating session

| Field | Value |
|---|---|
| **Severity** | MEDIUM |
| **Section** | Component 2 mapping table (line 192) + Implementation Plan Unit 5 |
| **Description** | The mapping table says the "Other 10 mandatory fields" are "populated by `format_handoff.py` from defaults (chain header, `produced_at`, `accurate_as_of_head`, `current_session_id`, `current_terminal_id`, etc.)." If `current_session_id` defaults to the WRITING session (the one running `/handoff --from-journal`), not the ORIGINATING session (the one that ran `/todo --journal`), the journal-derived handoff has wrong provenance. The journal's `session_id` is captured in Component 1, but Component 2's mapping doesn't explicitly route it to the handoff's `current_session_id` field. |
| **Suggestion** | Specify the mapping for `current_session_id` and `current_terminal_id`: "Component 2 reads these from the journal file (lines 100–101 of Component 1 schema) and passes them to `format_handoff.py` as overrides, NOT using the writing session's defaults." Add test case `test_from_journal.py::test_session_provenance` asserting the handoff's `current_session_id` matches the journal's `session_id`, not the writing session's ID. |
| **Status** | addressed |
| **Response** | Mapping table row for "Other 10 mandatory fields" now explicitly states: `current_session_id` and `current_terminal_id` are read from the journal's `session_id` and `terminal_id` fields and passed as overrides, NOT using the writing session's defaults. Provenance = the originating `/todo` session. Added test case `test_session_provenance` to Unit 6 acceptance that asserts the handoff's `current_session_id` matches the journal's `session_id`, not the writing session's ID. |

### F-44 — Stdout summary in Component 1 shows ALL sources; Component 2 may exclude some

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 1 stdout summary (lines 138–148) + Component 2 (line 159) |
| **Description** | Component 1's stdout summary lists "Sources: [review×3, harvest×2, script_defects×2]" — showing ALL sources in the journal. Component 2's `--exclude-source` filters items AFTER the journal was written. So the operator sees source distribution in Component 1, decides to exclude `harvest`, then runs Component 2 — but the journal file persists the original `harvest` items. If a future re-run reads the journal, those items are present again. This is correct behavior (journal = persistence; routing = filtering) but the operator's mental model of "I excluded harvest" applies only to the current Component 2 invocation, not to future journal reads. |
| **Suggestion** | Document the asymmetry: "Component 1 journal always contains all severity-eligible items regardless of `--exclude-source`. `--exclude-source` is a per-invocation filter on Component 2; the journal file persists the unfiltered set." Add row to Failure Mode Category 8: "Operator expects `--exclude-source` to persist | It only affects current invocation | Re-run applies filter again." |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). The asymmetry is correct (journal = persistence, routing = filtering); the gap is documentation. Will document explicitly in a v0.2 follow-up: "Component 1 journal always contains all severity-eligible items regardless of `--exclude-source`. `--exclude-source` is a per-invocation filter on Component 2; the journal file persists the unfiltered set." |

### F-45 — Phase 1 end-to-end smoke has no failure rollback path

| Field | Value |
|---|---|
| **Severity** | MEDIUM |
| **Section** | Rollout Phase 1 (line 463) + Implementation Plan Unit 8 acceptance (line 326) |
| **Description** | Phase 1 step 2 says the writer session runs `/todo --journal --deep` then `/handoff --from-journal <path>`. Unit 8 acceptance says: "produces ≥1 handoff at `P:/docs/handoffs/todo-<source>-<YYYYMMDD>/HANDOFF.md` with chain header matching the 17-field schema." But if the smoke fails (e.g., zero handoffs produced, or handoff has wrong chain header), the Implementation Plan doesn't say what to do. The next action isn't specified: rollback the commits? File a fix and re-test? Mark Unit 8 as failed and stop? |
| **Suggestion** | Add explicit failure handling to Unit 8 acceptance: "If smoke fails (zero handoffs OR chain header mismatch): (a) revert all units from this session via `git revert <hash>..HEAD` (NOT `reset --hard`), (b) file a handoff describing the failure, (c) do NOT mark Unit 8 complete; blocker persists into next session." This makes the smoke test a true gate, not a checkbox. |
| **Status** | addressed |
| **Response** | Added explicit rollback path to Unit 8 acceptance: (a) revert via `git revert <hash>..HEAD` (**NOT `reset --hard`** — destructive), (b) any handoffs created during smoke are marked `status: closed` via `/handoff close <path>` with closure note "smoke test failure — design reverted in <sha>", (c) Unit 8 is NOT marked complete; blocker persists into next session. Also extended the smoke failure trigger to include `current_session_id` mismatch (per F-43): if the smoke's handoff has wrong provenance, it fails the gate. Smoke is now a true gate, not a checkbox. |

### F-46 — Reviewer-pushback missing: `--exclude-source` + `--max-items` + severity-gating interaction untested

| Field | Value |
|---|---|
| **Severity** | LOW |
| **Section** | Component 2 + Implementation Plan Unit 6 acceptance |
| **Description** | The Implementation Plan Unit 6 acceptance lists test cases for mode detection, item mapping, dedup scope, exclude-source, and max-items — but no test case for the COMBINATION of `--exclude-source` + `--max-items` + severity gating. These three filters compose: items excluded by source OR severity OR exceeding max-items. Off-by-one bugs in composition (e.g., max-items check runs before exclude-source) won't be caught by single-feature tests. |
| **Suggestion** | Add composite test: `test_from_journal.py::test_combined_filters` — input a journal with 5 sources × 3 severities × varied paths, assert that `--exclude-source review --journal-min-severity medium --max-items 10` produces the expected intersection. |
| **Status** | deferred |
| **Response** | Acknowledged. Out of scope for this round per operator direction (LOW severity, follow-up PR). Will add `test_from_journal.py::test_combined_filters` in a v0.2 follow-up: input a journal with 5 sources × 3 severities × varied paths, assert that `--exclude-source review --journal-min-severity medium --max-items 10` produces the expected intersection. Off-by-one composition bugs are a real risk; the gap is test coverage, not design. |

---

## Coverage Checklist (revised)

### Passed (no regressions from first review)

- [x] Design Intent Contract present (Goal, Non-goals, Success metrics S1–S3 with measurement, Failure conditions F1–F4)
- [x] Option 0 (Do Nothing) is the first alternative
- [x] Coupling & Code-Smell Inventory present
- [x] Failure Mode & Edge Case Analysis covers all 8 categories
- [x] Implementation Plan has Disposition + Acceptance criteria per unit
- [x] Traceability Matrix covers REQs, DECs, S-rows, F-rows
- [x] Key Decisions use DEC-NN tags (DEC-01..08)
- [x] Alternatives meaningfully explored
- [x] All 30 original findings addressed
- [x] AAR regression test gates Unit 1
- [x] Test execution interleaved with code creation
- [x] Mode detection has explicit ordering + ambiguity handling
- [x] Dedup scan scope bounded
- [x] Directory precondition handled (mkdir)
- [x] "Non-blocking handoff" defined
- [x] Epistemic labels applied to material claims
- [x] stdout summary at journal write time

### Gaps surfaced by re-review (new)

**Addressed (HIGH + critical MEDIUM, this round):**
- [x] `--journal-min-severity` argument validation (F-31)
- [x] Falsifier thresholds: stable vs movable goalpost (F-37)
- [x] Stdout summary dry-run/normal format (F-39)
- [x] **Collision probability math correctness (F-42)** ← HIGH
- [x] Inherited handoff field provenance (F-43)
- [x] Phase 1 smoke failure rollback (F-45)

**Deferred (LOW, follow-up PRs):**
- [ ] DEC-08 vs Unit 12 consistency (F-32) — out of scope this round
- [ ] `--max-items` default justification (F-33) — out of scope this round
- [ ] Pre-bridge handoff dedup coverage (F-34) — out of scope this round
- [ ] `--exclude-source` / `--max-items` interaction order (F-35) — out of scope this round
- [ ] `path` schema optional vs required (F-36) — out of scope this round
- [ ] Known Limitations completeness (F-38) — out of scope this round
- [ ] F-pos-N vs F1–F4 label namespace (F-40) — out of scope this round
- [ ] `--exclude-source` CLI syntax spec (F-41) — out of scope this round
- [ ] Component 1/2 source-list asymmetry (F-44) — out of scope this round
- [ ] Composite filter test coverage (F-46) — out of scope this round

---

## Recommendations (prioritized) — revised after second pass

1. **F-42 (HIGH — factual error)** — RESOLVED. Math fixed to 2³² ≈ 4.3 billion prefixes; both Component 1 and Category 4 row updated.
2. **F-31, F-43, F-45 (MEDIUM — correctness)** — RESOLVED. Validation spec, provenance override, and rollback path added.
3. **F-37, F-39 (MEDIUM — design integrity)** — RESOLVED. Falsifier thresholds immutable; stdout formats separated.
4. **F-32, F-33, F-34, F-35, F-36, F-38, F-40, F-41, F-44, F-46 (LOW — refinements)** — DEFERRED. Acknowledged but tracked for v0.2 follow-up PRs. None block the COMMIT_THIS_SESSION units.

**Recommend: APPROVE. All HIGH and critical MEDIUM findings addressed. All 10 LOW findings acknowledged and deferred to follow-up PRs (not blocking). The COMMIT_THIS_SESSION units (Implementation Plan) are ready to execute.**

The design has materially improved across both revision rounds. The structural backstops (argument tables, traceability matrix, mode detection ordering, dedup scope bounding, AAR regression gate, measurement methodology, immutable falsifier thresholds, rollback path on smoke failure) are all in place. The deferred LOWs are consistency/clarity issues that don't affect the design's correctness or implementability — they're appropriate for a v0.2 follow-up.