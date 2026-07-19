# Interaction Quality (conditional reference)

**Loaded when:** any of these triggers fire (detector-signal or explicit-prompt):
- `detect_user_corrections` HIGH severity
- `detect_objective_drift` any severity
- `detect_correction_propagation_failure` any severity
- `detect_procedure_saturation` any severity
- Repeated user goal restoration (≥2 corrections of the same objective) observed in the transcript
- User explicitly asks "what went wrong with the interaction" or equivalent

**Authority for:** the 8 deeper-failure lens questions, success-shape-mismatch pattern, calibration-oscillation pattern, mechanism-object confusion pattern.

**Not authority for:** the trigger itself (SKILL.md core owns that); detector implementation (`__lib/detectors.py` owns that).

---

## Premise

Proximate failures (a wrong tool call, a missed evidence cite, an overlong retry loop) are easy to count. The harder, more useful work is to recognise when individually reasonable decisions combine into a deeper failure mode.

The deterministic layer emits three candidate signals:
- `opportunity_candidate_objective_drift`
- `opportunity_candidate_post_failure_continuation`
- `opportunity_candidate_reading_without_synthesis`

The LLM should also consider the eight lens questions below during synthesis. They cover the failure patterns that recur across real sessions.

## The 8 lens questions

1. **Success-shape mismatch.** Did the agent optimize a polished artifact (a markdown table, a calibrated epistemic claim, a report) instead of the user's actual purchase/decision outcome? If the user asked "is X in stock?", did the agent answer the question or did it produce a formatted table about something else?

2. **Continuation past infeasibility.** Did the agent keep producing work after evidence made the requested result unavailable, rather than telling the user "the evidence ceiling has been reached"?

3. **Objective drift.** Did the user have to repeatedly restore the real objective? This is the strongest empirical signal of an agent that has substituted its own goal for the user's.

4. **Mechanism-object confusion.** Is the final artifact serving the goal, or has the agent optimised for the artifact (the plan, the table, the report, the gate) instead of the goal?

5. **Calibration oscillation.** Did the agent swing from unjustified confidence ("I'll handle this") to obstructive caution ("you must choose between A, B, C, or D") within the same task?

6. **Anchoring on invalidated evidence.** After a correction, did the agent re-assert the original claim, or did it update? Re-assertion is a hard failure-mode indicator.

7. **Reasoning offload.** Did the agent require the user to perform reasoning it should have performed itself (e.g. asking the user to rank "viable options" when the next step is structurally obvious)?

8. **Emergent misalignment.** Did each individual instruction look reasonable in isolation but combine into pathological behaviour? This is the hardest to detect mechanically; check whether the end-to-end outcome matches the user's stated intent.

## Usage rule

These lenses are **not mandatory subsections**. Surface a deeper-failure finding only when the evidence supports it; for most AAR runs there will be zero. The objective is to catch the category, not to populate a checklist.

## Cross-reference

- Severity definitions: see `event_model.py` and SKILL.md core
- Source-fidelity rule: see SKILL.md core (a detector may not exceed representation-supported confidence)
- Opportunity schema: see `references/opportunity-discovery.md`
