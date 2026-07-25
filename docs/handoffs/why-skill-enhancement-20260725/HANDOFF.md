---
thread_id: why-enhancement-20260725
parent_handoff_path: none
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
current_terminal_id: console_9f93f0d3-0b5b-4985-b779-6a2c
produced_at: 2026-07-25T18:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: unknown
---

# Handoff: `/why` skill enhancement — evidence-gated causal investigation

## Objective

Enhance `~/.grok/skills/why/SKILL.md` from its current 5-dimension Ishikawa RCA into an evidence-gated investigation protocol with conditional control-system analysis, feedback-loop detection, and architecture/code classification. The enhancement was designed through multi-model analysis during session 019f96f5, where the current `/why` was tested against a real failure (the session's own recurring gaps) and found weaker than two external LLM analyses.

## Why this matters

The current `/why` produced an analysis that was correct about individual causes but wrong about the frame. When two external LLMs analyzed the same failure pattern, both produced deeper, more architectural diagnoses. The gap is not analytical vocabulary — it's evidence discipline, coverage completeness, and failure-pattern recognition.

## Evidence for the gap

Session 019f96f5 ran `/why` on "why do I keep making gaps." The analysis found 5 causes across 5 dimensions. Two external analyses found 10 causes each. Key causes the current `/why` missed entirely:

- No authoritative contract map connecting intent → files → identity → mutations → verification → completion
- Mutation ownership and verification ownership are separate systems with no shared identity contract
- Fail-open behavior hides infrastructure failures (ImportError → silent None, not ENFORCEMENT_UNAVAILABLE)
- The recurring cycle: hook blocks → patch nearest artifact → test green → receipt inadequate → hook blocks again
- No negative-path testing (import crash, stale receipt, identity ambiguity)

The MAST paper (Cemri et al. 2025, arxiv 2503.13657, 523 citations) independently confirms: multi-agent LLM systems fail in 14 modes across 3 categories (specification issues, inter-agent misalignment, task verification). The current Ishikawa dimensions don't cover inter-agent misalignment at all.

## What to implement (approved design)

The design went through three rounds of review (my initial proposal, two external LLM analyses, operator-approved corrections). Final approved direction:

### Step ordering (operator-approved)

1. **Verify and define the symptom** (existing Step 0.5, unchanged)
2. **Evidence inventory** (NEW — replaces proposed "evidence gate") — inventory present/missing/still-required/conclusions-allowed across Mechanism, State, Outcome, Authority. NOT a blocking gate — missing evidence may itself be the finding. Proceed with explicitly provisional conclusions.
3. **Identify the first divergence** (NEW) — where did the system first deviate from expected behavior? Prevents jumping from symptom to architectural explanation.
4. **MAST/control-system coverage check** (NEW) — compact checklist using FC1 (specification), FC2 (inter-agent misalignment), FC3 (verification) as "did you check this category?" NOT prevalence claims. Plus a control-system lens (contract/provenance, identity/ownership, enforcement boundary, fail-open patterns, negative-path coverage) that expands only when the failure involves agent-control infrastructure.
5. **Five RCA dimensions** (existing Step 2, unchanged) — Mechanical, Measurement, Behavioral, Process, Environmental
6. **Classify each cause** (Step 4 revision) — five-way: architecture/control-plane, implementation/code, workflow/process, model behavior, environment/runtime. Replaces current binary structural/behavioral.
7. **Detect harmful feedback loops** (NEW Step 7) — general question: "Does the response to the failure change the observed state, evidence, or agent behavior without satisfying the underlying invariant?" Distinguish from legitimate retry/continuation.
8. **Competing-explanation, surprise, absent-evidence, and falsifier checks** (existing Step 5, enhanced) — add: "What evidence should exist if this explanation were true? Is it present?"
9. **Recommend fixes** (existing Step 7, refined) — only for sufficiently supported causes

### Design decisions and objections (the "why we chose what we did")

**Decision 1: Five dimensions + cross-cutting lens, not ten equal dimensions.**
- My initial proposal: expand to 10 dimensions (add Contract/Provenance, Identity/Ownership, Enforcement Boundary, Negative-path Coverage, Fail-Open Patterns).
- Objection (external LLM 2): "expanding to ten mandatory dimensions would probably create checklist fatigue and shallow analysis."
- Resolution: keep 5 dimensions, add a cross-cutting control-system lens that expands only when relevant. The lens is conditional, not mandatory for every investigation.
- Why: the 5 existing dimensions are sound for general debugging. The 5 new agent-control dimensions are only relevant for hooks/gates/receipts/verification failures. Forcing all 10 every time wastes effort on ordinary bugs.

**Decision 2: Evidence inventory, not evidence gate.**
- My initial proposal: "evidence-completeness gate" requiring all four evidence types (Mechanism, State, Outcome, Authority) before investigation begins.
- Objection (external LLM 2): "A missing authority artifact may itself be the finding. Make the gate an evidence inventory... Otherwise `/why` may refuse to investigate precisely when authority or runtime evidence is missing."
- Resolution: inventory approach — present, missing, still-required, conclusions-currently-allowed. Proceed with explicitly provisional conclusions when evidence is incomplete.
- Why: a blocking gate would prevent investigation exactly when the missing artifact IS the root cause. The inventory surfaces the gap without blocking.

**Decision 3: Five-way classification, not binary structural/behavioral.**
- My initial proposal listed four categories (architecture, code, behavior, environment) but called it "five-way" — internally inconsistent.
- Objection (external LLM 2): "It says five-way but lists four... also drops process/workflow." Corrected list: architecture/control-plane, implementation/code, workflow/process, model behavior, environment/runtime.
- Resolution: five-way classification as corrected.
- Why: the current binary conflates "one-file code bug" with "agent-control system design gap." The distinction matters because the fixes have completely different cost/risk profiles.

**Decision 4: Broad feedback-loop detection, not narrow "fix alters evidence" formulation.**
- My initial proposal: "Does the fix alter the evidence used by the gate, without changing the underlying state the gate is intended to measure?"
- Objection (external LLM 2): "Feedback-loop detection should be broader... other harmful loops exist" — identified three additional loop patterns (block→patch→verify→block, retry→partial change→changed hypothesis→retry, failure→no telemetry→assume no failure→repeat).
- Resolution: general question "Does the response to the failure change the observed state, evidence, or agent behavior without satisfying the underlying invariant?" Plus distinguishing harmful loops from legitimate retry/continuation.
- Why: the narrow formulation only catches one loop pattern. The general formulation catches all four observed patterns.

**Decision 5: MAST as coverage taxonomy, not prevalence claim.**
- My initial proposal cited MAST prevalence figures (FC1: 41.77%, FC2: 36.94%, FC3: 21.30%).
- Objection (external LLM 2): "Use FC1/FC2/FC3 as a coverage taxonomy, not as a claim that those categories have the same prevalence in Grok Build."
- Resolution: use as "did you check this category?" not "this category has this probability."
- Why: MAST's dataset (7 MAS frameworks, 200 traces) may not match Grok Build's system model.

**Decision 6: Contract-map check is conditional, not automatic root cause.**
- My initial proposal: Step 0.7 checks for a contract map and if none exists, "that's the root cause."
- Objection (external LLM 2): "'No contract map exists' should not automatically be declared the root cause... The correct output should be: 'No authoritative contract map was found. This is a candidate systemic cause.'"
- Resolution: report as candidate systemic cause, test whether the failure could occur if such a map existed and was enforced.
- Why: absence of an artifact is evidence, not proof of causation.

**Decision 7: Decision-archaeology mode excluded.**
- External LLM 1 proposed adding `decision-archaeology` mode (why does this configuration exist?).
- My objection: scope creep. `/why` is for failure analysis. Decision archaeology should be its own skill or `/wiki query` variant.
- Operator agreed: "keep decision archaeology out of /why."

**Decision 8: No mandatory 3-7 competing hypotheses.**
- External LLM 1 proposed requiring 3-7 competing hypotheses.
- My objection: the existing "≥1 competing explanation" requirement is already hard to satisfy honestly. Forcing 3-7 incentivizes strawman padding.
- Resolution: keep ≥1, use MAST categories as a coverage checklist instead of a count threshold.

**Decision 9: Durable investigation state is conditional.**
- External LLM 1 proposed writing a compact RCA state/report artifact for every investigation.
- My objection: adds ceremony for the 90% of cases that complete in one turn.
- Resolution: make conditional on `--verify` mode or long investigations only.

**Decision 10: Negative-path checks mandatory only for enforcement work.**
- Both external analyses agreed: mandatory for hooks/gates/receipts/verification systems, conditional for ordinary debugging.

### Additional high-ROI optimizations (post-handoff review — 2026-07-25)

These emerged from reviewing the handoff against the Codex prompt
(`C:\Users\brsth\Downloads\why-from-codex.txt`) and the Claude RCA reference
at `cc-skills-sdlc/.../__lib/evidence_tiers.md`. They are NOT covered by the
10 decisions above and have the highest long-term ROI.

**Optimization A: Evidence-tier system (from Claude `evidence_tiers.md`).**
- The handoff's "evidence inventory" (Mechanism/State/Outcome/Authority) is
  necessary but not sufficient. The Claude reference adds a **Tier 1-4
  confidence ceiling** system:
  - Tier 1 (95%): execution artifacts, logs, test output, telemetry
  - Tier 2 (85%): official docs, specs, peer-reviewed reference
  - Tier 3 (75%): static analysis, logical derivation, symbols
  - Tier 4 (50%): comments, unverified claims, speculation
- **Rule:** overall confidence cannot exceed the weakest tier in the causal
  chain (weakest-link). This is mechanically enforceable and prevents the
  "I read the code, therefore FACT" error — reading code is Tier 3, not Tier 1.
- **Why high-ROI:** this single rule structurally prevents the receipt-system
  failure class (treating an inference as a fact). It's the missing enforcement
  layer behind the existing `[FACT]/[INFERENCE]/[UNKNOWN]` labels.

**Optimization B: Pattern-library integration (RADICAL — highest ROI).**
- `/why` currently investigates every failure as novel. This workspace has
  27+ wiki concepts, many documenting recurring failure patterns (closure
  pressure, narrative sufficiency, reactive pattern matching, fail-open,
  etc.).
- **Add Step 0: pattern match.** Before investigating, query the wiki
  (`/wiki query <failure-shape>`) for similar past failures. If a known
  pattern matches, START from the known root cause and verify/disconfirm,
  rather than re-deriving from scratch.
- **Why highest ROI:** turns `/why` from a one-shot analyzer into a
  cumulative-knowledge system. Each investigation builds on prior ones.
  Directly addresses the "external LLMs found deeper causes" gap — the
  external LLMs had broader pattern libraries; our `/why` doesn't query its
  own.
- **Depends on:** Optimization C (the feedback loop that populates the library).

**Optimization C: Feedback-to-wiki loop (RADICAL — enables B).**
- Every `/why` that finds a **systemic or architectural** cause should
  auto-write (with operator confirm) a wiki concept capturing the pattern.
- Without this, `/why` findings evaporate into session transcripts and never
  feed back into future investigations.
- **Threshold:** only systemic/architectural causes (not one-off code bugs).
  The pattern must be reusable to warrant a concept.
- This closes the loop: `/why` → wiki concept → future `/why` Step 0 query.

**Optimization D: Failure-class dispatch (radical refactor of step structure).**
- The handoff keeps a linear 8-step structure with inline "conditional
  expansion." A cleaner radical refactor: **dispatch at Step 0 based on
  failure class**, making the conditionality concrete:
  - `--bug`: ordinary code bug → mechanical dimension primary, skip
    agent-control lens, 60-second fast path
  - `--agent`: agent-control system (hooks/gates/receipts/verification) →
    full protocol: contract-map, feedback loops, negative paths, semantic vs
    lexical feedback
  - `--pattern`: recurring behavioral pattern → wiki-first (Optimization B),
    longitudinal across sessions
  - `--system`: architectural/systemic → contract-map first, then dimensions
- **Why:** makes "conditional expansion" dispatch-driven (clear modes) rather
  than a series of inline conditionals the LLM must track. Saves effort on
  simple bugs; guarantees depth on complex ones.

**Optimization E: Six-layer first-divergence model (from Codex prompt).**
- The handoff has "identify the first divergence" but the Codex prompt
  distinguishes six layers that should not be conflated:
  symptom → first divergence → immediate trigger → proximate cause →
  contributing conditions → systemic/reusable cause.
- **Why:** prevents the common error of conflating trigger with cause
  ("the hook blocked" is a trigger; "the receipt was semantically
  inadequate" is the cause). Explicit layer separation forces the
  distinction.

**Optimization F: Semantic vs lexical feedback (agent-control lens addition).**
- For agent-control systems, distinguish "the gate fired correctly (lexical —
  exit code, file written)" from "the gate measured the right thing
  (semantic — does the receipt actually prove completion?)."
- The receipt-system failure was lexical-correct (hooks fired, files written)
  but semantic-wrong (receipts didn't measure test quality).
- Add as a named sub-check within the agent-control lens (Decision 1).

**Recommended implementation order:** C → B → A → D → E → F.
C and B are the radical refactor (cumulative knowledge system). A is the
enforcement layer. D is structural clarity. E and F are refinements.

## What NOT to change

These existing features are sound and should be preserved:
- Five Whys per dimension (correct drill-down method)
- Competing-explanations requirement (correct anti-premature-closure defense)
- Premise labeling ([FACT]/[INFERENCE]/[UNKNOWN])
- Falsifier step
- "Verify observation before investigating causes" (diagnostic mode)
- `/why` does NOT implement fixes (implementation is `/go`)

## File to edit

- `C:\Users\brsth\.grok\skills\why\SKILL.md` (single file, ~400 lines currently)

## Acceptance criteria

1. The enhanced `/why` run on this session's failure pattern produces findings at least as complete as the external LLM analyses (10 causes, feedback-loop detection, architecture/code classification)
2. Evidence inventory step surfaces missing authority/state evidence without blocking investigation
3. Feedback-loop detection identifies the block→patch→green→inadequate cycle
4. MAST categories used as coverage checklist, not prevalence claims
5. Five-way classification distinguishes architecture from code from process from behavior from environment
6. The skill does not become a 50-step questionnaire — conditional expansion keeps ordinary-bug investigations short
7. All existing features preserved (Five Whys, competing explanations, premise labeling, falsifier, verify-before-conclude)

## Test case

Run the enhanced `/why` on: "Throughout session 019f96f5, I repeatedly produced incomplete work, claimed it was complete, and when caught I patched reactively." The output should find:
- The feedback loop (hook → patch → green → inadequate → hook)
- The contract-map gap (no authoritative source connecting intent → files → mutations → verification → completion)
- The fail-open pattern (ImportError → silent None)
- The enforcement-boundary gap (Stop hook measures exit code, not test quality)
- Classification as architecture/control-plane (not just "behavioral")

## Related wiki concepts

- `P:/.data/wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md` — the existing Ishikawa adaptation that this enhancement extends
- `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` — the behavioral pattern this skill is designed to diagnose

## Reference material

- MAST paper: https://arxiv.org/html/2503.13657v2 (Cemri et al. 2025, 523 citations) — empirically grounded MAS failure taxonomy, 14 modes in 3 categories
- External LLM analysis 1: "Completion-Provenance Drift" diagnosis (10 causes)
- External LLM analysis 2: prioritized implementation direction with corrections
- Session transcript: `~/.grok/sessions/P%3A%5C/019f96f5-dc4a-79d0-9e17-396f2a582186/`

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** other skill improvements

## Status

OPEN — ready for implementation in a fresh session

## Next steps

1. Read this handoff
2. Read the current `~/.grok/skills/why/SKILL.md`
3. Read `P:/.data/wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md`
4. Implement the 9-step protocol with conditional expansion per the design decisions above
5. Test against the session 019f96f5 failure pattern (acceptance criteria above)
6. Run `/check` to verify the skill change

## Last user message (verbatim)

"/handoff for the '/why' enhancement. include the objections and decisions for why we chose what we did."
