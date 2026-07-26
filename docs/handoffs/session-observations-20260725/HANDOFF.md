---
thread_id: session-observations-20260725
parent_handoff_path: P:\docs\handoffs\why-skill-enhancement-20260725\HANDOFF.md
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-07-25T22:35:00Z
status: open
handoff_type: observations
accurate_as_of_head: unknown
---

# Session observations — 20260725 (session 019f9a89)

## Origin

Operator asked for `/why` skill optimization proposals using multiple models. Session became a worked example of the multi-producer-cross-model-synthesis methodology that was itself produced as a wiki concept this session.

## Observations worth capturing

### O1 — Multi-producer cross-model synthesis works in practice

**Observation:** Ran 5 producers (Grok + glm-5-2 + codex + agy + mimo) in parallel on the /why optimization assignment. Producers reached consensus on ~80% of design (8 of 10 items) and split cleanly into 2 live disagreements, each with a 2-vs-2 split. The synthesizer resolved both using evidence-grounded criteria.

**Why it matters:** this is the first production application of the N-producers-plus-synthesizer pattern (vs /tp's 1-producer+1-synthesis or /red-team's adversarial panel). It validated the methodology and produced 3 wiki concepts documenting the reusable decisions.

**Reusable for future sessions:** the assignment-packet pattern (`P:/tmp/why-skill-multi-model-assignment.md` is the template). Future skill-design tasks (especially /tp, /check, /review refactors) are candidates.

### O2 — Nemotron serde failure reconfirmed; status still unsolved

**Observation:** `nvidia-nemotron-3-ultra` failed on the /why assignment with `serialization error: invalid type: null, expected u32 at line 1 column 330`. Same error family as 2026-07-23 (different prompt, different session). `glm-5-2` ran 5 minutes later without issue.

**Why it matters:** confirms the failure is not transient. Root cause still `[UNKNOWN]` (transport/schema mismatch hypothesis, unverified). Documented as canonical in `wiki/concepts/model-tool-calling-capability-matrix.md` with the findability section operator requested.

**Reusable for future sessions:** don't waste tokens on Nemotron for large-prompt spawn_subagent work; use glm/mimo/parent. Don't trust trivial READY probes.

### O3 — Operator correction dissolved staging vs auto-write binary

**Observation:** My initial synthesis proposed staging (write to inbox → review → promote). Operator pushed back: "if a3 answers q3 well, why do we need to stage?" The pushback was correct: synchronous cross-model review IS the gate; staging adds nothing in that case. This produced the [[synchronous-review-direct-write-pattern]] wiki concept.

**Why it matters:** demonstrates the failure mode of synthesizer over-engineering. I added staging reflexively (defense against contamination) without checking whether another gate (synchronous review) already covered the failure mode.

**Reusable for future sessions:** when adding a defensive mechanism, ask "does an existing gate already cover this failure mode?" first.

### O4 — v2 was already shipped by another agent; v3 was refactor-of-refactor

**Observation:** The handoff described v2 as "to be implemented." On reading the actual SKILL.md, v2 was already live (commit `774eb43`, by another agent or earlier session). My job became refactoring v2 → v3, not building from v1.

**Why it matters:** I lost ~15 minutes discovering this mid-implementation. The handoff's "accurate_as_of_head: unknown" was the warning sign — I should have checked HEAD state before assuming the handoff's status was current.

**Reusable for future sessions:** when picking up an OPEN handoff, check the actual file state first. The handoff may already be partially or fully implemented.

### O5 — Two wiki concepts failed validator first pass

**Observation:** `inline-conditional-over-dispatch` and `synchronous-review-direct-write` failed `validate_wiki_entry.py` with "Only 2 cross-references; minimum is 3." The third concept (`multi-producer-cross-model-synthesis`) passed first try because it naturally produced more cross-references (it was the meta-level concept that referenced the other two).

**Why it matters:** the validator caught what self-assessment missed. Two of three concepts would have shipped thin if not for the validator gate.

**Reusable for future sessions:** always run `validate_wiki_entry.py` before declaring a wiki concept done. The 3-link minimum is real and useful.

### O6 — Class C shell-quoting failure during v3 atomic swap

**Observation:** First attempt at the v3 atomic swap used inline Python with f-strings containing backslash escapes; syntax error aborted the script before `os.replace` executed. The file stayed at v2. Per AGENTS.md Class C rule, switched to writing a temp `.py` script and invoking it — worked first try.

**Why it matters:** confirms the Class C rule. Inline Python with f-string escapes is a known trap; temp scripts are the structural fix.

**Reusable for future sessions:** for any Python with f-strings + backslashes + multiple asserts, write to a temp `.py` file from the start. Don't try inline.

### O7 — Wiki now captures decisions by default (not just findings)

**Observation:** Operator instruction "make sure /wiki captures decisions by default" led to splitting SCHEMA.md §4 into §4a (findings gate) and §4b (decisions gate). Decisions require: architectural + selection-criterion + rationale + steelman + falsifier + durable + distinct.

**Why it matters:** the wiki was previously findings-only. Decisions were captured ad-hoc and held to the wrong quality bar. The §4b gate makes decision quality explicit.

**Reusable for future sessions:** when writing a wiki concept, first ask "is this a finding or a decision?" — they have different quality gates.

### O8 — /why v3 now has a production-grade feedback-to-wiki loop

**Observation:** Step 15 of /why v3 implements: mechanical gate (5 criteria) → synchronous cross-model review (3 yes/no questions) → direct write to concepts/. No operator-as-gatekeeper. Operator can delete post-hoc.

**Why it matters:** /why is now a cumulative-knowledge system, not a one-shot analyzer. Each investigation builds on prior ones via Step 0.5 (wiki query). This is the highest-ROI change in the v3 refactor.

**Reusable for future sessions:** when designing similar loops for other skills (/aar → dispositions, /debrief → action items, /check → rules), apply the same pattern: mechanical gate + sync review + direct write.

## What did NOT work well

- **My initial synthesis recommendation was wrong on auto-write.** Operator caught it; I updated. The lesson: when rejecting an option, check whether a different gate already handles the failure mode I was worried about.
- **Discovering v2 was already shipped mid-implementation.** Cost ~15 min. Lesson: read the actual file state before assuming the handoff status is current.
- **Class C quoting failure on first atomic-swap attempt.** Preventable; the AGENTS.md rule is right there.

## What worked well

- **5-model parallel synthesis** — produced deeper analysis than any single model could have
- **Cross-family lens diversity** — exposed the dispatch-vs-inline disagreement that same-family producers would likely have agreed on
- **The /tp Step 3 verification gate** — applied to producer outputs, caught unsupported findings
- **Wiki validator** — caught thin concepts before they shipped
- **Surgical staging** — committed only my work, never touched other agents' uncommitted files

## Source references

- Session: 019f9a89-d902-7930-ad3a-bab7e682830b
- Wiki concepts produced (3):
  - `P:/.data/wiki/concepts/multi-producer-cross-model-synthesis.md`
  - `P:/.data/wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md`
  - `P:/.data/wiki/concepts/synchronous-review-direct-write-pattern.md`
- Wiki updated (2):
  - `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` (Nemotron canonical + not-solved)
  - `P:/.data/wiki/SCHEMA.md` §4 split into findings + decisions gates
- Skill implementations (2):
  - `C:/Users/brsth/.grok/skills/why/SKILL.md` v3 (commit `ddf793d`)
  - `C:/Users/brsth/.grok/skills/wiki/SKILL.md` decisions-default (commit `7ab98b7`)
- Assignment packet template: `P:/tmp/why-skill-multi-model-assignment.md`
- Producer outputs: `P:/tmp/why-skill-codex-final.md`, `P:/tmp/why-skill-agy-out.txt`
- Handoff driving the work: `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md`
