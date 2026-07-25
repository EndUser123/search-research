# `/check` Conditional Orchestrator — Final Approval (Round 3)

| Field | Value |
|---|---|
| Reviewer | design-doc-reviewer (final approval) |
| Document reviewed | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` (revision after round-2 review) |
| Prior reviews | `2026-07-25-check-orchestrator-review.md`, `2026-07-25-check-orchestrator-review-r2.md` |
| Date | 2026-07-25 |
| Verdict | **APPROVED** (with two minor documentation-drift follow-ups, neither blocking) |

---

## 1. One-line summary

All four targeted round-3 fixes (N-1, N-3, N-4, and consistent 150-test grand total) are correctly and thoroughly applied. The design is ready to implement. Two cosmetic inconsistencies in §7.1 line 1037 and R9 line 1280 (both say `test_exactly_12_detectors` instead of `test_exactly_13_detectors`) and the round-2 N-2 advisory about the validator's `parsed_events` short-circuit behavior are noted but do not block approval.

---

## 2. Targeted fixes — per-finding verdict

| ID | Severity asked | Verdict | Evidence |
|---|---|---|---|
| **N-1** | BLOCK | **FIXED** | `receipt_evaluation` is now the 13th entry in `DETECTOR_NAMES`. Verified at lines 483-496 of the revised design: full tuple spec showing the new entry with comment `# stub detector; bucket populated by load_receipt_summary`. Stub detector `detect_receipt_evaluation` defined at lines 452-471 with rationale referencing `output_validator.py:198-201`. `run_all_detectors` extended at lines 477-480. PR 1 file inventory (line 1036) says *"append three names to `DETECTOR_NAMES` (now 13 entries, not 12)"*. Appendix A (line 1294) says *"Append 3 detector functions ... + 3 entries in `DETECTOR_NAMES`"*. Stub test at lines 501-511 asserts the stub returns `[]` and does not parse transcript content defensively. Module docstring updated "10 detectors → 13 detectors" (line 1036). |
| **N-3** | REVISE | **FIXED** | Appendix A row for `output_validator.py` (line 1296) now reads: *"Add `"1.1"` to `_KNOWN_SCHEMA_VERSIONS`. **No empty-event_indices allowlist** (N-3 fix: F-01 removed the empty-tuple proposal; the validator's empty-event_indices check at `output_validator.py:227-231` stays intact, and the receipt signal uses a real terminal-event anchor instead)"*. LOC delta is `+1 / 0` — just the schema-version line, which matches the actual code change required by the F-01 fix. The contradiction from the prior round (which described an allowlist that the F-01 fix made unnecessary) is removed. |
| **N-4** | REVISE | **FIXED** | `transcript` is now REQUIRED, not optional. Verified at: (a) §5.3 line 522 — `transcript: Transcript,        # N-4: REQUIRED, not optional.`; (b) §7.2 line 1054 — *"exports `load_receipt_summary(session_id, packet, transcript) -> dict | None` (N-4 fix: `transcript` parameter is **required**, not optional...)"*; (c) §7.2 Risks line 1072 — *"The `transcript` parameter is now required (N-4), which means the preprocessor's call site (PR 2 file modification) MUST pass the parsed Transcript — `transcript=None` will raise TypeError, not silently produce an invalid signal"*; (d) §8.1 line 1148 — test list includes "*transcript=None raises TypeError (N-4)*"; (e) Appendix A line 1300 — signature `(N-4: transcript is required, not optional...)`. The fail-closed TypeError semantics (instead of silent invalid signal) are correct and well-documented. |
| **Test counts** | n/a | **CONSISTENT** | Grand total **150** is consistent across every reference: Phase 1=130 (line 1212), Phase 2=137 (line 1213), Phase 3=144 (line 1214), Phase 4=150 (line 1215). PR 4 acceptance (line 1132): *"All 121 + 9 + 7 + 7 + 6 = **150 tests** pass"*. §8.1 grand total (line 1153): *"121 + 29 = 150"*. Breakdown of the 29 new tests (line 1151): *"N-1: +1 receipt stub test; N-4: +1 TypeError test"* — the remaining 27 are the original F-02-derived additions (8 detector + 6 loader + 7 routing + 6 packet-assembly). Arithmetic verifies: 121 + 9 + 7 + 7 + 6 = 150 ✓ and 9 (detector, including N-1 stub) + 7 (loader, including N-4 TypeError) + 7 (routing) + 6 (packet-assembly) = 29 ✓. |

---

## 3. Remaining minor issues (advisory, not blocking)

| ID | Severity | Section | Title | Detail | Recommendation |
|---|---|---|---|---|---|
| **N-2 (carry-over)** | ADVISORY | §5.3.1 lines 617-621 | Validator-behavior claim about `parsed_events=0` is still incorrect | The `_resolve_event_anchor` docstring still says *"the validator's range check at output_validator.py:235-240 will reject any packet with parsed_events=0 anyway (the packet would be UNVERIFIED source status), so this fallback is unreachable in practice."* Verified: `output_validator.py:236` uses `elif parsed_events and any(...)` which short-circuits when `parsed_events == 0`. The range check is **skipped**, not enforced. The fallback's safety relies on path-unreachability (the loader is only invoked when a transcript exists), not on validator enforcement. The claim was carried over from the original design and never corrected. Not blocking because the path is unreachable in practice. | Either rephrase to *"this fallback is unreachable in practice because the loader is only invoked when a transcript exists"* (drops the incorrect validator-behavior claim), or tighten `_resolve_event_anchor` to raise when the transcript is empty (caller treats as no-receipt-data path). Option 1 is sufficient. |
| **D-1** | ADVISORY | §7.1 line 1037 | PR 1 description says "test_exactly_12_detectors" instead of 13 | §7.1 line 1037: *"update `test_exactly_10_detectors` → `test_exactly_12_detectors`; update bucket-presence assertions to 12"*. The acceptance section three lines below (line 1044) correctly says *"10 to 13 in `test_exactly_10_detectors` → `test_exactly_13_detectors` per N-1"*. The file-inventory line and the acceptance line contradict each other within §7.1 itself. Cosmetic — the acceptance section is the authoritative requirement. | Change line 1037 from "test_exactly_12_detectors" to "test_exactly_13_detectors" and "12" to "13". |
| **D-2** | ADVISORY | R9 risk (line 1280) | Risk row says "test_exactly_10 → test_exactly_12" instead of 13 | Risk R9 (line 1280): *"PR 1 updates `test_exactly_10_detectors` → `test_exactly_12_detectors`"*. Stale from before the N-1 fix. Appendix A line 1298 correctly says "from 10 to 13". Cosmetic. | Change "test_exactly_12_detectors" → "test_exactly_13_detectors" in R9. |

---

## 4. Open issues count

| Severity | Round 2 carried over | New in round 3 | Total open (post-approval) |
|---|---|---|---|
| **BLOCK** | 0 (N-1 was round-2 BLOCK, now FIXED) | 0 | **0** |
| **REVISE** | 0 (N-3 and N-4 both FIXED) | 0 | **0** |
| **ADVISORY** | 1 (N-2 carry-over) | 2 (D-1, D-2 — both cosmetic) | **3** |
| **Total** | **1** | **2** | **3** |

All three remaining items are documentation drift or unblocking nitpicks that the implementer can resolve during PR 1 in 5 minutes. None change the design.

---

## 5. Overall verdict

**APPROVED.**

The design is structurally sound, internally consistent in all load-bearing sections (acceptance criteria, file inventory, test counts, signature contracts), and ready for implementation to begin. The four targeted fixes from round 2 are correctly applied:

- N-1 (the round-2 BLOCK) is properly resolved: `receipt_evaluation` is the 13th `DETECTOR_NAMES` entry, the stub detector is well-specified with a defensive test, and `run_all_detectors` correctly delegates to it.
- N-3 (Appendix A contradiction) is resolved: the file inventory correctly states "No empty-event_indices allowlist" with the F-01 rationale, and the LOC delta `+1 / 0` matches reality.
- N-4 (transcript required) is resolved at every reference: signature, docstring, PR 2 description, risk row, test list, Appendix A — all consistently state REQUIRED with fail-closed TypeError semantics.
- Test counts are mathematically consistent across all sections: 121 base + 29 new = 150 grand total; Phase 1/2/3/4 = 130/137/144/150.

The three remaining advisory items (N-2 validator-behavior claim, D-1 §7.1 count drift, D-2 R9 count drift) are all 5-minute fixes the implementer can make during PR 1 without further design review. None change what gets built or how.

**Implementation may proceed.** The PR 1 acceptance criteria are: all 130 tests pass (121 base + 9 new including the N-1 receipt-stub test); `test_exactly_13_detectors` passes; `detect_receipt_evaluation` returns `[]` for any input including transcripts with content resembling receipt JSON; old v1.0 packets still validate.

---

## 6. Verification receipts

| Claim | Source | Line |
|---|---|---|
| `DETECTOR_NAMES` has 13 entries after PR 1 (N-1 fix) | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 483-496 (tuple spec) |
| Stub detector `detect_receipt_evaluation` defined | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 452-471 |
| `run_all_detectors` extended with the stub | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 477-480 |
| PR 1 inventory says "13 entries, not 12" | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1036 |
| Stub test asserts return value `[]` for any input | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 501-511 |
| Appendix A: 3 detector functions + 3 entries | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1294 |
| Appendix A: "No empty-event_indices allowlist" (N-3 fix) | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1296 |
| `transcript: Transcript, # N-4: REQUIRED, not optional` | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 522 |
| PR 2 signature includes required `transcript` | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1054 |
| TypeError on `transcript=None` documented | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1063, 1067, 1072, 1148, 1300 |
| Phase 1/2/3/4 = 130/137/144/150 | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1212-1215 |
| §8.1 grand total = 150 | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1151-1153 |
| PR 4 acceptance: 121 + 9 + 7 + 7 + 6 = 150 | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1132 |
| N-2 validator-behavior claim still incorrect | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 617-621 (compared to `output_validator.py:236` `parsed_events and ...`) |
| D-1: §7.1 line 1037 says "12" instead of "13" | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1037 (vs correct count at 1044) |
| D-2: R9 risk says "12" instead of "13" | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | 1280 (vs correct count at 1044, 1298) |
