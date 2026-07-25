# `/check` Conditional Orchestrator — Re-Review (Round 2)

| Field | Value |
|---|---|
| Reviewer | design-doc-reviewer (re-review) |
| Document reviewed | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` (revised after first review) |
| Prior review | `P:/docs/designs/2026-07-25-check-orchestrator-review.md` |
| Date | 2026-07-25 |
| Verdict | **NEEDS REVISION** |

---

## 1. One-line summary

The author resolved all 14 prior findings thoroughly: the F-01 fix is technically sound against the actual `output_validator.py` and `Signal` dataclass, F-02's test count is correctly propagated through every dependent number, and the F-03 through F-14 clarifications are present, well-structured, and actionable. **However**, re-review surfaced one structural omission (N-1) that re-creates the same class of validator-collision failure that F-01 was supposed to fix, plus two smaller inconsistencies in the file inventory and the empty-transcript fallback claim.

---

## 2. Per-finding verdict

### Original findings

| ID | Original severity | Title | Verdict | Notes |
|---|---|---|---|---|
| F-01 | **BLOCK** | Empty `event_indices=()` violates two contract layers | **FIXED** | Resolution: anchor receipt signal to terminal event `event_indices=(N-1,)`. Technically sound — the validator's range check at `output_validator.py:236-240` passes when `N-1 < parsed_events`, and the dataclass invariant at `detectors.py:252` is satisfied (non-empty tuple). The "fail-open" language in the original §5.3 is correctly characterized as wrong in the new §5.3.1. The chosen approach (anchor to real event) is strictly less invasive than introducing a top-level key. See N-2 below for a minor edge-case claim error in §5.3.1. |
| F-02 | **BLOCK** | Test count wrong (121 not 101) | **FIXED** | All four occurrences updated: header (line 10), G6 (line 53), §6.6 (line 947), §7.4 acceptance (line 1055). Breakdown matches my pytest run: detectors=31, event_model=15, evidence_packet=11, output_validator=22, preprocessor_integration=10, transcript_parser=32. Downstream counts correctly re-derived: Phase 1=129, Phase 2=135, Phase 3=142, Phase 4=148. Grand total in §8.1 = `121 + 27 = 148` ✓. |
| F-03 | **REVISE** | post_verification_mutation: confidence + empty-verification noise | **FIXED** | (a) `confidence="INFERRED"` with rationale referencing `detectors.py:39-42` invariant ✓ (line 348-353). (b) Pseudocode now returns `[]` when no verification event exists (lines 360-361) ✓. The "Why skip the empty-verification case" paragraph (lines 380-386) correctly identifies the Stop-hook duplication and the cross-model-spawn cost. |
| F-04 | **REVISE** | scope_claim_mismatch: "conservative" wording contradicted threshold | **FIXED** | Reframed as "narrow-scope focus detector" (line 405). Threshold promoted to `SCOPE_CLAIM_MISMATCH_FILE_THRESHOLD = 3` named constant (line 397). Pseudocode explicitly states "If scope_files_count >= SCOPE_CLAIM_MISMATCH_FILE_THRESHOLD: return []" (line 432). Honest framing: "fires on small-scope sessions where the mismatch is most diagnosable" ✓. |
| F-05 | **REVISE** | Fast-path "byte-for-byte equivalent" overclaim | **FIXED** | §1.1 (line 24): "functionally equivalent to today's behavior at the verifier-dispatch layer" ✓. §4.4 (line 313-316): "not byte-for-byte equivalent at the PowerShell level ... The relevant invariant is 'zero new verifiers spawned when no signals fire', not 'zero new tool calls in the orchestrator.'" ✓. §5.7 latency table (line 873) carries the explicit "wall-clock UX cost" framing. |
| F-06 | **REVISE** | evidence_packet.py docstring-update step references text that doesn't exist | **FIXED** | PR 1 line 966: now updates "the `to_dict` method's `for kind in DETECTOR_NAMES` loop" with a `# NB: iterates DETECTOR_NAMES; bump when adding a detector` comment. This is the correct, real touch-point. ✓ |
| F-07 | **REVISE** | `claim_audit` threshold rationale lacks distribution data | **FIXED** | §6.4 (line 919): "Threshold is provisional pending §9.2 telemetry" ✓. §9.2 (lines 1140-1147): telemetry commits to reporting `claim_audit_dispatch_count`, `claim_audit_dispatch_rate`, and the distribution of `unverified_claim_candidates` counts. Threshold-tuning protocol documented (raise to ≥5 if dispatch rate >50%). The constant name is documented as provisional. |
| F-08 | **REVISE** | Wrong citation for `minimax-m3` latency | **FIXED** | §6.3 (lines 915-917): now correctly cites `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md`. Acknowledges that `~/.grok/tool-fallbacks.md` documents broken combinations only, so `minimax-m3`'s absence from that file is correct. Appendix D (line 1297) also updated. ✓ |
| F-09 | **REVISE** | `packet_for_specialization.py` underspecified | **FIXED** | New §5.6.1 (lines 798-849) specifies: (1) concatenation order (standard prompt → overlay → footer); (2) template variable set (`{{session_id}}`, `{{run_dir}}`, `{{evidence_packet_path}}`, `{{transcript_path}}`, `{{routing_decision_path}}`); (3) substitution mechanism (`re.sub(r"\{\{(\w+)\}\}", ...)`); (4) fail-open semantics for unrendered variables and missing files; (5) test count increased from 4 to 6 (lines 1024-1032). |
| F-10 | **REVISE** | "Absent" vs "empty list" vs "zero signals" — three inconsistent statements | **FIXED** | All three statements reconciled: G4 (line 56): "always-present, sometimes-empty bucket" ✓. §4.3 (line 274): "always present; 0 when no summary file" ✓. §5.3 (line 517): "the bucket is an empty list (`signals["receipt_evaluation"] = []`) — present-but-empty, never missing" ✓. New test case "summary file absent → returns None, packet unchanged" covers the empty-list path explicitly. |
| F-11 | **ADVISORY** | Shadow-mode `if (Test-Path $routingPath)` guard makes empty case invisible | **FIXED** | §9.2 (line 1135): "Routing decision is computed and ALWAYS written to `$runDir/packets/routing-decision.json` — even when empty (F-11: writing only when non-empty would make the fast-path telemetry invisible)" ✓. Shadow entry appended to `check-shadow-<session_id>.jsonl` per-run with `routing_decision_count`, `routing_decision_specializations`, etc. (lines 1142-1144). |
| F-12 | **ADVISORY** | Feature flag mechanism not specified | **FIXED** | §9.3 (lines 1163-1180) now specifies: (1) two env-var flags with default-when-true semantics; (2) flag storage (PowerShell `$env:` and Python `os.environ`); (3) PR 4 acceptance criterion includes flag mechanism documentation in SKILL.md; (4) rollback scenarios matrix with three configurations. ✓ |
| F-13 | **ADVISORY** | No test for v1.0→v1.1 backwards compatibility | **FIXED** | §8.5 (line 1122): `test_v1_0_packet_still_validates_after_bump(packet_factory)` constructs a synthetic v1.0 packet and asserts `validate_packet` returns `errors=0`. ✓ |
| F-14 | **ADVISORY** | Manual smoke test list missing fast-path profile | **FIXED** | §7.4 (line 1036): now lists 5 smoke profiles; Profile 1 is the explicit fast-path session with verification criteria ("routing-decision.json written with empty decisions; zero specialized verifiers spawned; merged CHECK verdict identical to pre-change behavior"). §9.1 Phase 4 (line 1135) commits to "5 manual smoke sessions (4 signal-fire + 1 fast-path per F-14)". ✓ |

---

## 3. New findings surfaced in re-review

| ID | Severity | Section | Title | Detail | Recommendation |
|---|---|---|---|---|---|
| N-1 | **BLOCK** | §5.3 / §7.1 / Appendix A | `receipt_evaluation` is not in `DETECTOR_NAMES` per the file inventory, which would cause silent routing failure | The design states (§5.3 line 518) that `receipt_evaluation` "matches the existing pattern of `unverified_claim_candidates` (always present, sometimes empty) and the `output_validator.py:198-201` requirement that every `DETECTOR_NAMES` entry has a bucket in `signals`." But PR 1's file changes (lines 957-963) only append TWO detectors (`post_verification_mutation`, `scope_claim_mismatch`) to `DETECTOR_NAMES`. `receipt_evaluation` is not listed. Consequence: (a) `evidence_packet.py:signal_counts` (line 89) iterates `DETECTOR_NAMES` only — `signal_counts["receipt_evaluation"]` would not exist; (b) `routing.py:compute_routing_decision` (line 594) uses `counts.get(signal_kind, 0)` — returns 0 silently; (c) `receipt_eval_v1` specialization never fires. The pattern the design claims to mirror (`unverified_claim_candidates`) requires the detector name to be in `DETECTOR_NAMES` for this to work. **Receipt:** `evidence_packet.py:88-89` (signal_counts property), `output_validator.py:198-201` (DETECTOR_NAMES iteration), §7.1 lines 957-963 (PR 1 file changes). | Add a stub detector to PR 1: `detect_receipt_evaluation(transcript) -> list[Signal]` returning `[]`, plus append `"receipt_evaluation"` to `DETECTOR_NAMES`. The loader (`load_receipt_summary.py`, PR 2) then patches the empty bucket with the real signal. This preserves the structural invariant the design itself names. Concretely: PR 1 file list should include `detectors.py — append stub detect_receipt_evaluation returning [] and add "receipt_evaluation" to DETECTOR_NAMES` (now 13 entries, not 12). The `test_exactly_10_detectors` → `test_exactly_13_detectors` rename and `run_all_detectors` test updates follow. |
| N-2 | **ADVISORY** | §5.3.1 (line 543-553) | Empty-transcript fallback claim about validator behavior is incorrect | §5.3.1 line 552 says: *"the validator's range check at output_validator.py:235-240 will reject any packet with parsed_events=0 anyway (the packet would be UNVERIFIED source status), so this fallback is unreachable in practice."* Verified: the validator's range check at lines 236-240 uses `elif parsed_events and any(x >= parsed_events for x in ei):` — the `parsed_events and` short-circuits when `parsed_events == 0`, so the range check is **skipped**, not enforced. An empty packet with `event_indices=(0,)` would NOT be rejected by this check. The fallback's safety relies on the path being unreachable, not on validator enforcement. **Receipt:** `output_validator.py:236` read. | Either (a) rephrase the claim to "the empty-transcript case is unreachable in practice because the loader is only invoked when a transcript exists" (which is true per `load_receipt_summary(session_id, packet, transcript)`'s contract), dropping the incorrect validator-behavior claim; or (b) tighten `_resolve_event_anchor` to raise when transcript is empty (caller treats as "no receipt data, skip receipt_eval verifier" — the empty-bucket path already handles this case). Option (a) is sufficient. |
| N-3 | **REVISE** | Appendix A (line 1219) | File inventory contradicts the F-01 fix on `output_validator.py` change | Appendix A row for `output_validator.py` (line 1219) reads: *"Add `"1.1"` to known versions; **allow `receipt_evaluation` to have empty `event_indices`**"* with LOC delta `+2 / 0`. But the F-01 fix in §5.3.1 explicitly chose the approach that does NOT require validator changes: `event_indices=(N-1,)` is non-empty, so the existing check at `output_validator.py:227-231` passes unchanged. The "allow empty event_indices" framing is from the rejected alternative (Option b in the F-01 review). This contradiction will mislead the PR author into either (a) implementing the rejected approach, or (b) trying to add validator logic that isn't needed. **Receipt:** `output_validator.py:42` (`_KNOWN_SCHEMA_VERSIONS = frozenset({PACKET_SCHEMA_VERSION})` — currently has no per-detector kind whitelist), Appendix A line 1219 read. | Update the row to: *"Add `"1.1"` to known versions; **no validator change needed (F-01 fix anchors receipt signal to terminal event, so `event_indices` is non-empty and satisfies the existing check)"*. LOC delta `+2 / 0` is still correct (just the two-line `KNOWN_SCHEMA_VERSIONS` update). |
| N-4 | **ADVISORY** | §7.2 (line 982) vs §5.3 (line 451-456) | PR 2 file description's function signature omits the `transcript` parameter | §5.3 specifies `load_receipt_summary(session_id: str, packet: EvidencePacket, transcript: Transcript | None = None)`. §7.2's PR 2 file description (line 982) says `exports `load_receipt_summary(session_id, packet) -> dict | None`` — the `transcript` parameter is missing. The PR author implementing against §7.2 alone would build a loader without the transcript parameter needed for the F-01 event anchor. **Receipt:** §5.3 lines 451-456 vs §7.2 line 982 read. | Update §7.2 to match §5.3: `exports `load_receipt_summary(session_id, packet, transcript=None) -> dict | None``. The four PR 2 test descriptions also implicitly assume the transcript is available (e.g., the bucket-shape test must construct a transcript to verify the event anchor) — consider adding `transcript: Transcript | None` to the loader's test fixtures too. |

---

## 4. Open issues count

| Severity | From prior review | New in re-review | Total open |
|---|---|---|---|
| **BLOCK** | 0 (both prior BLOCKs FIXED) | 1 (N-1) | **1** |
| **REVISE** | 0 (all 8 prior REVISE FIXED) | 1 (N-3) | **1** |
| **ADVISORY** | 0 (all 4 prior ADVISORY FIXED) | 2 (N-2, N-4) | **2** |
| **Total** | **0** | **4** | **4** |

Net change: 14 prior findings → 0 open. 4 new findings introduced. The new BLOCK (N-1) is the same architectural class as the original F-01 — it concerns how `receipt_evaluation` integrates with the existing `DETECTOR_NAMES` invariant.

---

## 5. Overall verdict

**NEEDS REVISION.**

The author did a thorough job resolving all 14 prior findings. The F-01 fix is the right call (anchor to a real event index, don't relax the contract), F-02's count propagation is mathematically correct through all four PRs, and F-03 through F-14 each have a concrete, well-placed resolution. The new §5.3.1 ("F-01 fix") and §5.6.1 ("packet_for_specialization.py contract") sections are well-structured and would significantly de-risk PR 1-4 implementation.

**The one remaining BLOCK is N-1: `receipt_evaluation` not in `DETECTOR_NAMES`.** This is the same architectural class as the original F-01 — the design's structural claim ("every DETECTOR_NAMES entry has a bucket in signals") is violated by the PR plan as written. Without the fix, the routing decision will silently never fire for the receipt bucket, and the G4 acceptance criterion ("Receipt-system evaluation summary attached to evidence packet as always-present, sometimes-empty bucket") will fail functionally even though it passes syntactically.

**Recommendation:** add the stub `detect_receipt_evaluation` detector and the `DETECTOR_NAMES` entry in PR 1 (now 13 detectors, not 12). This is a one-line code change but it must be present in the file inventory before implementation begins — otherwise the PR author will replicate the F-01 omission at PR-merge time.

After N-1 is resolved (and ideally N-2 through N-4 clarified), the design should be **APPROVED**. No further architecture changes are needed.

---

## 6. Verification receipts

| Claim | Source | Line |
|---|---|---|
| All 14 prior findings present in the revised design | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | (full file read, 1307 lines) |
| F-01 fix uses `event_indices=(N-1,)` (non-empty) | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | §5.3 lines 494-497, §5.3.1 lines 538-553 |
| F-02 test count is 121 throughout | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | lines 10, 53, 947, 1055; breakdown matches `pytest --collect-only` from prior review |
| Validator's range check short-circuits when parsed_events=0 | `P:/.grok/skills/check/__lib/output_validator.py` | 236-240 (the `parsed_events and` clause) |
| `signal_counts` iterates only `DETECTOR_NAMES` | `P:/.grok/skills/check/__lib/evidence_packet.py` | 88-89 |
| Validator requires every `DETECTOR_NAMES` entry in `signals` | `P:/.grok/skills/check/__lib/output_validator.py` | 198-201 |
| Routing uses `counts.get(signal_kind, 0)` (silent default) | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | §5.4 line 594 |
| PR 1 file inventory lists 2 detector appends, not 3 | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | §7.1 lines 957-963 |
| Appendix A says "allow `receipt_evaluation` to have empty `event_indices`" | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | Appendix A line 1219 |
| §5.3 loader signature includes `transcript` parameter | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | §5.3 lines 451-456 |
| §7.2 PR 2 file description omits `transcript` parameter | `P:/docs/designs/2026-07-25-check-orchestrator-design.md` | §7.2 line 982 |
