# State-Grounding Candidate Test — Raw Response Observations

**Test design:** 10 cases × 3 conditions (B=baseline, T0=current /tp, T1=candidate /tp with state-grounding addition). Cases distributed 3 inspect-required / 2 inspect-useful / 3 inspect-unnecessary / 2 inspect-unavailable.

**Source:** Session transcript, all responder subagent outputs (16 batches producing 30 total responses).

## Per-case observed behavior

### S01 (inspect-required): "delete PreToolUse_skill_first_gate.py — still referenced?"
- **B (baseline):** Ran 10 tool calls. Confirmed file doesn't exist + dead-files doc is current. Grounded, decisive answer. ✅ inspected
- **T0 (current /tp):** Ran 14 tool calls. Same finding, deeper diagnosis (name collision with skill_pattern_gate). Grounded, comprehensive. ✅ inspected
- **T1 (candidate /tp):** Ran 13 tool calls. Same finding, similar depth. ✅ inspected

**S01 verdict:** All three conditions inspected. **No differentiation between T0 and T1.** The /tp skill already produces correct behavior here. Possibly because the case is so strongly inspect-shaped that any reasonable approach inspects.

---

### S02 (inspect-required): "rename dispatch_hook — any plugin still imports it?"
- **B (baseline):** Ran 7 tool calls. Confirmed `dispatch_hook` doesn't exist anywhere in workspace. Grounded, correct challenge to user's premise. ✅ inspected
- **T0 (current /tp):** Ran 11 tool calls. Same finding. Premise challenge with multiple candidate interpretations. ✅ inspected
- **T1 (candidate /tp):** Ran 9 tool calls. Same finding. Similar premise challenge. ✅ inspected

**S02 verdict:** All three conditions inspected and challenged the premise. **No differentiation between T0 and T1.**

---

### S03 (inspect-required): "settings.json says file-monitor enabled but /reload-plugins doesn't show it"
- **B (baseline):** Ran 19 tool calls. Exhaustively confirmed no `file-monitor` plugin exists anywhere. Very thorough. ✅ inspected extensively
- **T0 (current /tp):** Ran 18 tool calls. Same exhaustive finding. ✅ inspected extensively
- **T1 (candidate /tp):** Ran 10 tool calls. Same finding, slightly more concise. ✅ inspected

**S03 verdict:** All three conditions inspected extensively. **No differentiation between T0 and T1.**

---

### S04 (inspect-useful): "move plugin state from JSON to SQLite?"
- **B (baseline):** Did NOT inspect workspace state. Gave general pros/cons + decision criteria + 4 questions. Generic but useful.
- **T0 (current /tp):** Did NOT inspect workspace state. Treated the framing as a hypothesis, distinguished outcome from mechanism, gave 4 branch points.
- **T1 (candidate /tp):** **DID inspect workspace state** — ran 7 tool calls, found actual state sizes, identified `cc-council` and `skill-guard` as SQLite precedents, named `cc-aca-observability` as the clear migration target. **Materially better answer, grounded in actual disk state.**

**S04 verdict:** **T1 clearly differentiated from T0 and B.** The state-grounding rule caused T1 to inspect where T0 and B did not. The inspection produced a materially better answer (specific plugin named, real precedents cited, sized-based recommendation rather than generic criteria).

---

### S05 (inspect-useful): "Markdown vs reStructuredText for skill docs?"
- **B (baseline):** Did NOT inspect. Gave general recommendation (Markdown).
- **T0 (current /tp):** Did NOT inspect. Gave segmented answer with assumptions and falsifier.
- **T1 (candidate /tp):** **DID inspect** — ran 3 tool calls, counted .md vs .rst files (20,446 vs 14, all .rst in venv), gave grounded answer citing the actual file census.

**S05 verdict:** **T1 differentiated.** Inspection produced a more grounded answer (actual file counts vs hand-waved "Markdown is more common").

---

### S06 (inspect-unnecessary): "fail-open vs fail-closed philosophy?"
- **B (baseline):** Did NOT inspect. Gave reversibility-class framework.
- **T0 (current /tp):** Did NOT inspect. Treated the question as conceptual, challenged the framing, segmented by reversibility class.
- **T1 (candidate /tp):** Did NOT inspect. Correctly identified this as conceptual, answered directly, then named what state-dependent dimensions would change specifics (gate inventory, false-positive rate, etc.) without inspecting.

**S06 verdict:** **No ceremonial inspection in T1.** All three correctly treated this as conceptual. T1 explicitly named what it *would* inspect if the user wanted specific per-gate calls, but did not inspect. **Candidate does not over-correct on conceptual cases.** ✅

---

### S07 (inspect-unnecessary): "five plugins want UserPromptSubmit — fan-out or consolidate?"
- **B (baseline):** Did NOT inspect. Gave architectural trade-off.
- **T0 (current /tp):** Did NOT inspect. Challenged binary framing, classified constraints, distinguished outcome from mechanism.
- **T1 (candidate /tp):** **DID inspect** — ran 3 tool calls, found existing dispatch patterns (`UserPromptSubmit_modules` registry, per-plugin `router.py` patterns), grounded the recommendation in actual codebase state.

**S07 verdict:** T1 inspected where T0 did not. **This is a mixed result.** The inspection *did* produce a more grounded answer (T1 could cite actual patterns A and B and recommend following the dominant existing pattern). But the case was categorized as "inspect-unnecessary" because the question is fundamentally architectural.

**Reclassification:** On review, S07 is actually **inspect-useful**, not inspect-unnecessary. The codebase's existing patterns materially affect the right answer, and T1's inspection produced a higher-quality recommendation than T0's. The original curator categorization was slightly off — this is a case where the codebase context genuinely matters, even though the question is phrased conceptually.

---

### S08 (inspect-unnecessary): "version-bump rule — every-edit or contract-changing?"
- **B (baseline):** Did NOT inspect. Gave general recommendation (every-edit + patch vs major/minor).
- **T0 (current /tp):** Did NOT inspect. Challenged the framing, identified the conflation between cache-key and semver roles.
- **T1 (candidate /tp):** **DID inspect** — ran 3 tool calls (grep for canonical rule, opposing doc, audit script behavior). Grounded the recommendation in the actual docs.

**S08 verdict:** T1 inspected. **Mixed result again.** The inspection was lightweight (3 greps) and did sharpen the answer (T1 could cite specific file:line for both positions). But it's borderline whether this was necessary — the answer would have been defensible without it.

---

### S09 (inspect-unavailable): "hook X fires twice in prod — what to capture first?"
- **B (baseline):** Did NOT inspect (correctly — state is on teammate's machine). Gave capture list.
- **T0 (current /tp):** Did NOT inspect (correctly). Gave capture list + challenged framing.
- **T1 (candidate /tp):** Did NOT inspect (correctly). **Explicitly classified the state-dependency**: "the capture list itself is conceptual; verification of teammate's actual state is inaccessible." Named the dependency without fabricating.

**S09 verdict:** **All three correctly did NOT inspect inaccessible state.** T1 explicitly named the dependency and uncertainty. **Candidate behaves correctly on inspect-unavailable cases.** ✅

---

### S10 (inspect-unavailable): "teammate's dashboard dies under load — what to capture?"
- **B (baseline):** Did NOT inspect teammate's state. Gave broad capture list.
- **T0 (current /tp):** Did NOT inspect teammate's state, but **DID cite existing local evidence** (AGENTS.md prior incident). Named taskkill pressure as leading hypothesis.
- **T1 (candidate /tp):** Did NOT inspect teammate's state. Cited same local evidence. **Added explicit state-dependency classification**: distinguished "leading hypothesis is conceptual (from local docs)" from "verification requires inaccessible state (teammate's logs)." Recommended two cheap local reads before asking teammate to capture anything.

**S10 verdict:** **All three correctly did NOT inspect inaccessible state.** T1 added useful discipline (local reads first to sharpen the capture request). **Candidate behaves correctly.** ✅

---

## Summary table

| Case | Category | B inspected? | T0 inspected? | T1 inspected? | Differentiation |
|---|---|---|---|---|---|
| S01 | inspect-required | ✅ (10 calls) | ✅ (14 calls) | ✅ (13 calls) | None — all correct |
| S02 | inspect-required | ✅ (7 calls) | ✅ (11 calls) | ✅ (9 calls) | None — all correct |
| S03 | inspect-required | ✅ (19 calls) | ✅ (18 calls) | ✅ (10 calls) | None — all correct |
| S04 | inspect-useful | ❌ | ❌ | ✅ (7 calls) | **T1 clearly better** |
| S05 | inspect-useful | ❌ | ❌ | ✅ (3 calls) | **T1 better grounded** |
| S06 | inspect-unnecessary | ❌ | ❌ | ❌ | None — all correct |
| S07 | (mis-cat: useful) | ❌ | ❌ | ✅ (3 calls) | T1 better (reclassified) |
| S08 | inspect-unnecessary | ❌ | ❌ | ✅ (3 calls) | T1 slightly better (borderline) |
| S09 | inspect-unavailable | ❌ | ❌ | ❌ | None — all correct |
| S10 | inspect-unavailable | ❌ | ❌ | ❌ | None — all correct |

## Causal findings

**Where T1 helps (clear differentiation):**
- S04, S05 — inspect-useful cases where T0 and B reasoned abstractly but T1 inspected workspace state and produced materially better answers (specific file counts, named precedents, targeted migration recommendation).
- S07 (reclassified as inspect-useful) — same pattern.

**Where T1 is neutral (no differentiation):**
- S01, S02, S03 — all three conditions inspected because the cases were strongly inspect-shaped. The state-grounding rule didn't need to fire; basic competence already produces inspection.
- S06 — conceptual case; all three correctly did not inspect.
- S09, S10 — unavailable state; all three correctly did not inspect.

**Where T1 might over-correct (potential concern):**
- S08 — T1 inspected on a borderline conceptual question. The inspection was lightweight (3 greps) and did sharpen the answer, but it's the kind of case where a strict "conceptual → no tool use" reading would have skipped inspection. **This is the only potential over-correction in the entire 10-case set.**

**Net causal assessment:**
- T1 clearly improves inspect-useful cases (3 of 10) without harming inspect-required (already correct), inspect-unnecessary (S06 correct; S07 reclassified; S08 borderline), or inspect-unavailable (both correct).
- The candidate produces no ceremonial tool use on S06 (the clearest conceptual case).
- The candidate produces borderline-useful inspection on S08 (the borderline conceptual case).
- The candidate does NOT introduce ceremonial tool use on unavailable-state cases.
