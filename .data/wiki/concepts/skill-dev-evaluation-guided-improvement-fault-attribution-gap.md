---
title: "Making skill-dev actually improve skills: the eval-guided fault-attribution gap"
created: 2026-08-07
source: session-019fdeea (/www research on how to fix skill-dev's Mode 2 improve)
tags: [skill-dev, skill-improvement, eval-driven, fault-attribution, trigger-accuracy, execution-knowledge, SkillAxe, SkillsBench, self-refinement, anti-pattern]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  The operator's complaint — "the target skills /skill-dev improves are not
  improved that much" — is a formalized, named problem in the 2026 literature.
  SkillsBench shows LLM-authored/revised skills give ~0 measurable gain by
  default; human-authored give +16.2pp. The field (SkillAxe, SkillRevise,
  SkillOpt, agentskills.io, Anthropic skill-creator) converged on the same
  answer our skill-dev is missing: improvement must be EVALUATION-GUIDED with
  FAULT ATTRIBUTION, not reasoning-guided. SkillAxe decomposes skill quality
  into 4 separable dimensions (quality impact, trigger precision, instruction
  compliance with fault attribution, solution-path coverage) and closes 47-67%
  of the gap to human skills. Our Mode 2 reasons about failures (MEC) and
  proposes from a static techniques-index; it never runs the skill with/without,
  never separates agent-fault from skill-fault, and treats improvement as
  additive when the win is often coverage (execution knowledge) or subtractive
  (remove over-constraining rules). This concept maps the 7 missing mechanisms
  and how each plugs into skill-dev. Extends [[claude-side-skill-improvement-tooling-2026]]
  and [[skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency]];
  complements [[self-improving-agent-systems-techniques-and-workspace-gaps]]
  (the Huang 2024 "self-correction fails without external signal" caveat is
  precisely why eval-guided works and pure self-refine doesn't).
sources:
  - external: https://arxiv.org/abs/2606.10546
    title: "SkillAxe: Sharpening LLM-Authored Agent Skills Through Evaluation-Guided Self-Refinement (Gautam, Radhakrishna, Gulwani 2026, Microsoft)"
    quality: 10
    primary_source: true
  - external: https://arxiv.org/html/2606.10546v2
    title: "SkillAxe full text — 4-dimension diagnostic framework, fault attribution mechanism, SkillsBench + SpreadsheetBench results"
    quality: 10
    primary_source: true
  - external: https://agentskills.io/skill-creation/evaluating-skills
    title: "Evaluating skill output quality — agentskills.io (the operational eval loop, evals.json format, blind comparison)"
    quality: 9
    primary_source: true
  - external: https://aclanthology.org/2024.tacl-1.78/
    title: "When Can LLMs Actually Correct Their Own Mistakes? (Huang et al. 2024, TACL) — disconfirmation: pure intrinsic self-correction fails"
    quality: 9
    primary_source: false
  - external: https://www.reddit.com/r/ClaudeAI/comments/1uhed8x/why_are_all_the_claude_code_skill_files_i_see/
    title: "Why are all the Claude Code skill files pointless? (r/ClaudeAI, 928 pts) — 'a skill should be a scar, not a resume'"
    quality: 7
    primary_source: true
  - external: https://www.reddit.com/r/ClaudeAI/comments/1rz2oo3/what_happens_when_you_stop_adding_rules_to/
    title: "Stop adding rules, start building infrastructure (r/ClaudeAI, 545 pts) — line-100 compliance cliff, 40% redundancy"
    quality: 7
    primary_source: true
  - external: https://www.reddit.com/r/ClaudeAI/comments/1tohgpq/i_built_a_tool_that_measures_whether_a_claude/
    title: "SkillBenchmark — measures whether a skill improves output (blind judge, with/without, CIs) — Ties_P"
    quality: 7
    primary_source: true
  - external: https://arxiv.org/abs/2606.01139
    title: "SkillRevise: trace-conditioned skill revision (execution-grounded revision)"
    quality: 8
    primary_source: false
  - external: https://arxiv.org/abs/2605.23904
    title: "SkillOpt: text-space optimization for natural-language skills"
    quality: 7
    primary_source: false
relations:
  - target: wiki/concepts/claude-side-skill-improvement-tooling-2026.md
    type: extends — adds the SkillAxe 4-dimension + fault-attribution mechanism Anthropic's tooling approximates
  - target: wiki/concepts/skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency.md
    type: refines — the trigger-accuracy gap now has a concrete measurement method (geometric trigger diagnostics)
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: related — explains WHY eval-guided works and pure self-refine doesn't (Huang 2024 external signal)
  - target: wiki/concepts/skill-lean-code-context-efficiency.md
    type: complements — the subtractive-improvement recommendation serves leanness
  - target: wiki/concepts/mechanical-enforcement-of-llm-skill-steps-2026.md
    type: related — evals are mechanical enforcement of skill quality
  - target: wiki/concepts/measurement-before-addition-principle.md
    type: related — eval-driven improvement IS the measurement layer
---

# Making skill-dev actually improve skills: the eval-guided fault-attribution gap

## Decision context

**Why this research was needed:** the operator stated that `/skill-dev`'s Mode 2
(improve) does not actually improve the target skills — "the target skills it
'improves' are not improved that much." The skill is large (68KB, 4 modes, 11
scanner checks) and sophisticated, so the failure is not effort or coverage;
it is that the improvement *mechanism* is wrong. The question: what would make
Mode 2 produce revisions that change behavior, not just edit prose?

**What the research changed:** identified that the operator's complaint is a
*named, formalized* problem in the 2026 literature (SkillsBench: LLM-revised
skills give ~0 gain by default). The field converged on an answer our skill-dev
does not implement: **evaluation-guided improvement with fault attribution**.
This concept maps the 7 missing mechanisms, each with an applicability verdict
and the specific plug-in point in skill-dev.

## The core diagnosis: why skill-dev's improvements don't bind

Mode 2 today: identify failure mode (from retrospective MEC) → query a static
techniques-index → propose a prose/code edit → "held-out validation" that is
*reasoning*, not execution. Five structural reasons this produces cosmetic
revisions:

1. **No with/without comparison.** Mode 2 never runs the skill on a task with
   and without the skill injected. It reasons about whether past sessions
   *depended* on the skill. So it can never observe the *behavioral delta* the
   skill produces — the only signal that distinguishes a binding improvement
   from a rewording. (Confirmed: `skill-dev/SKILL.md` Mode 2 has no execution
   step; only Mode 2.5 does, and it is opt-in/high-friction.)

2. **No fault attribution.** When a skill fails, Mode 2 cannot tell whether the
   *rule was wrong* or the *agent ignored a correct rule*. It treats every
   failure as evidence the skill should be rewritten. SkillAxe (§3.3) proves
   this degrades useful skills: "fixing" rules that were already correct.

3. **Flat MEC, not separable diagnostics.** Mode 2's "multi-dimensional
   assessment" (structure/code/prose/enforcement/self-reflection/trigger) is a
   *quality rubric*, not a *failure decomposition*. It scores the skill; it does
   not localize *where in the skill lifecycle the failure occurred*. SkillAxe's
   4 dimensions (below) are separable causes, not quality axes.

4. **Additive-only.** Mode 2 proposes additions (new checks, new steps, new
   techniques). agentskills.io is explicit that the highest-value move is often
   *subtractive*: "if pass rates plateau despite adding more rules, the skill
   may be over-constrained — try removing instructions and see if results hold
   or improve." Mode 2 has no subtractive path.

5. **Wrong target model.** Mode 2 implicitly treats skills as *answer-quality
   guidance*. SkillAxe's headline empirical finding (Table 2): the entire gain
   from good skills comes from *coverage* (execution reliability — preventing
   crashes/timeouts), NOT from *quality* (answer correctness among completed
   tasks was identical, 57.1%, with and without skills). Skills are *execution
   knowledge*; improving them means improving the procedural knowledge that
   prevents brittle execution, not polishing output style.

## SkillAxe: the 4-dimension diagnostic framework (the academic core)

SkillAxe (arXiv 2606.10546, Gautam/Radhakrishna/Gulwani, Microsoft, Jun 2026)
is the most directly relevant system. On SkillsBench it improves pass rates by
28% relative over unimproved LLM skills and closes 47-67% of the gap to
human-authored skills. In the wild (SpreadsheetBench) it raised pass rate from
16.0% → 52.0% with only 22 skills. Its mechanism is the answer to our problem.

**The loop:** run the agent on a task WITH the skill (r_s) and WITHOUT (r_0) →
compute 4 diagnostics from (task, r_0, r_s, skill) → compile into a structured
improvement brief → an LLM refiner rewrites the skill → iterate.

### Dimension 1 — Quality Impact (does the skill help at all?)

Paired comparison: an LLM judge receives r_s and r_0 in randomized order,
determines which better satisfies the task (direction d ∈ {skill wins, baseline
wins, tie}) and the magnitude m ∈ [0,1]. Quality = d·m ∈ [-1,1].

**Why it matters for us:** this is the *outer-loop gate*. Before diagnosing WHY
a skill failed, determine WHETHER it helped. A skill can be fluent and detailed
yet degrade performance by steering the agent toward a wrong strategy. Our MEC
never makes this paired comparison.

### Dimension 2 — Trigger Precision (does it fire on the right tasks?)

Extracts positive trigger phrases (when to activate) and negative trigger
phrases (when NOT to) from the description, embeds them with sentence context,
and computes 3 geometric diagnostics: **coverage breadth** (too narrow?),
**negative specificity** (exclusions too close to activation region?), **boundary
sharpness** (worst-case ambiguity?).

**The field's #1 empirical finding on triggers:** human skills almost never
include exclusion clauses (negative specificity 0.006). SkillAxe adds targeted
negatives and achieves **3× wider discrimination margin** than human skills
(correct-skill similarity +0.13, max-wrong only +0.03). The differentiator is
**negative specification**, not positive enumeration. Our wiki's T16 (exclusion
clause) names this; SkillAxe *measures* it.

### Dimension 3 — Instruction Compliance with FAULT ATTRIBUTION (the breakthrough)

Decomposes the skill into explicit evaluable rules {R_1..R_n} with severity
weights (critical/major/minor). For each rule, judges: **relevance** (does it
apply to this task?), **adherence** a_i (did the agent follow it?), **rule
quality** g_i (is the rule precise and operationalizable?), **skill fault** f_i
(did the failure originate from weak guidance or the agent ignoring valid
instructions?).

The fault-adjusted credit: `c_i = a_i + (1−a_i)(1−f_i)` — when failures are the
agent's fault, credit is restored. This prevents the system from "fixing"
correct rules that the agent simply failed to execute.

**Worked example (SkillAxe Table 1):** the agent produced the wrong shade of
yellow. If the rule was SPECIFIC ("use FFFF00"), the fault is the agent's →
preserve the rule. If the rule was VAGUE ("use yellow"), the fault is the
skill's → sharpen the rule (add the hex code). Same observed behavior, opposite
improvement action. Our Mode 2 cannot make this distinction.

### Dimension 4 — Solution-Path Coverage (does it support multiple valid strategies?)

Enumerates plausible solution paths for the task, measures how well skill chunks
align with each. A skill may trigger correctly and contain precise instructions
yet fail systematically because it only supports one execution strategy and the
agent pursued another valid one. **This dimension is entirely absent from our
skill-dev** — we have no concept of "does this skill cover the solution space?"

### The headline empirical insight (reframes what skills ARE)

Hierarchical decomposition of SkillAxe's SkillsBench results: the ENTIRE gain
over no-skill came from **coverage** (+26pp — tasks producing evaluable output
rose 46.7% → 72.7%), NOT from **quality** (native correctness among completed
tasks was identical, 57.1%, with and without skills). **Skills are execution
knowledge** — library usage, format handling, recalculation semantics, workflow
structure — that prevents brittle execution failures. They do not improve the
quality of answers the agent already knows how to produce.

This means: an improvement that polishes output guidance but does not add
execution knowledge will measure ~0 gain. Most of our Mode 2 proposals are
output-guidance polish. That is why they don't bind.

## The operational eval loop (agentskills.io)

agentskills.io's "Evaluating skill output quality" is the practitioner-grade
operationalization. Three signals feed iteration: **failed assertions** (specific
gaps), **human feedback** (broader quality), **execution transcripts** (WHY
things went wrong — did the agent ignore an instruction, or spend time on
unproductive steps?). "The most effective way to turn these signals into skill
improvements is to give all three — along with the current SKILL.md — to an LLM
and ask it to propose changes."

Key principles that contradict Mode 2's defaults:
- **Keep the skill lean. Fewer, better instructions often outperform exhaustive
  rules.** If pass rates plateau, the skill may be over-constrained → try
  *removing* instructions.
- **Generalize from feedback** — fixes should address underlying issues broadly,
  not patch specific test cases.
- **Explain the why** — reasoning-based instructions ("Do X because Y tends to
  cause Z") outperform rigid directives ("ALWAYS do X, NEVER do Y").
- **Blind comparison** — present both outputs to a judge without revealing which
  version produced which; reduces bias about which "should" be better.
- **Remove assertions that always pass in BOTH configs** — they don't measure
  skill value, they inflate the with-skill rate.

## Practitioner signal

- **"Why are all skill files pointless?" (r/ClaudeAI, 928 pts):** "a good skill
  should be a **scar, not a resume**" — fix what the model consistently gets
  wrong, don't state what it already knows. Top comment (mindwalkr, 31 pts):
  "Skills need a structural test that an Agent can use to determine if they
  should take an action or not. Then they need the actions specified if the test
  passes or fails." → **test-then-action structure**, not prose aspirations.
- **"Stop adding rules, build infrastructure" (r/ClaudeAI, 545 pts):**
  "instructions past ~line 100 get treated as suggestions, not rules"; forensic
  audit found 40% redundancy; the fix was infrastructure (skills/scripts/hooks),
  not more rules. Mod-bot TL;DR: "everyone hits a wall around 100-150 lines."
- **SkillBenchmark (Ties_P):** a tool that runs the LLM N times with/without the
  skill, blind judge scores against a rubric, returns CIs + delta. "Nobody
  actually knows if they work. You install one, use it for a week, and form a
  vague impression. That's not a measurement."
- **SWE-Skills-Bench (cited in-thread):** 49 public skills tested, only 7 gave a
  meaningful boost — the vast majority of community skills measure ~0 value.

## Recommendations (applicability-gated)

Each recommendation is tagged with evidence basis and tested-status per the
/www Round 3.25 gate. **None were tested on this workspace this session** — all
are `[UNTESTED]`. SkillAxe used Claude Opus 4.5 / GPT-5.4 as judges; our fleet
judge models are weaker, so fault attribution will be noisier here. That is the
single biggest applicability risk.

### R1. Make eval-driven improvement the DEFAULT Mode 2 path, not optional Mode 2.5. `[SUPPORTED] [UNTESTED]`
- **Mechanism:** for a target skill, run 2-3 realistic tasks with the skill and
  without (snapshot the old version). Grade with assertions + blind comparison.
  The *delta* is the only honest signal an improvement changed behavior.
- **Applicability:** HIGH. We have 2000+ session transcripts that can seed eval
  cases (see R6). `spawn_subagent` provides the clean-context isolation
  skill-creator gets from `claude -p`. Meta-skills (/tp, /close) are harder to
  isolate-test than narrow skills (/bf), but not impossible — test the
  *observable artifact* (does /handoff mention X? does /close emit the gate?).
- **Evidence basis:** multi-source (SkillAxe, agentskills.io, Anthropic
  skill-creator, OpenAI eval-skills, SkillBenchmark).
- **What would make it wrong:** if our judge models are too weak to grade
  reliably, the delta is noise. Mitigation: use the strongest available model
  for grading, prefer mechanical (script-checkable) assertions over LLM judgment.

### R2. Add fault attribution before any rewrite. `[PRELIMINARY] [UNTESTED]`
- **Mechanism:** decompose the target skill into evaluable rules; for each rule
  the agent violated, judge whether the *rule was vague/contradictory* (skill
  fault → sharpen) or *the agent ignored a clear rule* (agent fault → preserve,
  maybe add mechanical enforcement). Stop rewriting correct rules.
- **Applicability:** HIGH — this is the single highest-leverage missing
  mechanism. It directly prevents the "fixing rules that were already correct"
  failure that SkillAxe §3.3 identifies.
- **Evidence basis:** single primary source (SkillAxe §3.3), but mechanistically
  sound and consistent with our own [[mechanical-enforcement-of-llm-skill-steps-2026]]
  (behavioral steps fail; move to mechanical).
- **What would make it wrong:** if the judge cannot reliably distinguish
  skill-fault from agent-fault (it requires reading the rule AND the output
  evidence), the attribution adds noise. SkillAxe grounds judgments in
  file-level evidence (formulas, diffs), which is harder for prose-heavy
  meta-skills.

### R3. Replace flat MEC with the 4 separable diagnostics. `[PRELIMINARY] [UNTESTED]`
- **Mechanism:** score each skill firing on Quality Impact, Trigger Precision,
  Instruction Compliance, Solution-Path Coverage — separately. A skill that
  triggers correctly but is ignored needs a different fix than one that
  triggers wrongly.
- **Applicability:** MEDIUM-HIGH. The first three map onto things we half-do;
  the fourth (solution-path coverage) is genuinely new and high-value for
  multi-strategy skills (/review, /refactor).
- **Evidence basis:** SkillAxe (single source, but the decomposition is the
  paper's central contribution).

### R4. Measure trigger precision and MANDATE exclusion clauses. `[SUPPORTED] [UNTESTED]`
- **Mechanism:** for each skill description, extract positive/negative trigger
  phrases, check that negatives exist and are separated from positives. Flag
  skills with zero exclusion clauses (SkillAxe: human skills rarely have them
  → 3× worse discrimination). This operationalizes our T16.
- **Applicability:** HIGH and cheap. Our fleet has 100+ skills with overlapping
  descriptions; routing confusion is the likely #1 hidden cost. A script can
  check "does this description contain a 'Do NOT trigger for...' clause?"
- **Evidence basis:** multi-source (SkillAxe Appendix E, our wiki T16,
  SkillRouter).
- **Goodhart warning:** do NOT set a numeric trigger-accuracy *target* — the
  /deferred-and-rejected-skill-improvements-registry rejected plan-writer's
  length budget on exactly this basis ("arbitrary thresholds become targets").
  Measure and surface; let the operator decide.

### R5. Reframe skills as EXECUTION KNOWLEDGE (coverage), not answer quality. `[SUPPORTED] [UNTESTED]`
- **Mechanism:** when proposing improvements, ask "does this add procedural
  knowledge that prevents a brittle execution failure?" If not, it likely
  measures ~0 gain. Prioritize improvements that add library/sequence/format/
  workflow knowledge over ones that polish output style.
- **Applicability:** HIGH as a *reframing* (changes what Mode 2 looks for), low
  implementation cost. Hardest for meta-skills where "execution" is itself the
  skill's output — but even there, the analog is "does this prevent a
  process failure (skipped gate, silent empty output)?"
- **Evidence basis:** SkillAxe Table 2 (the coverage-vs-quality decomposition is
  the paper's most citable empirical result).

### R6. Auto-generate eval cases from session transcripts. `[INFERENCE] [UNTESTED]`
- **Mechanism:** the friction killer. Instead of hand-writing evals.json, mine
  our 2000+ session transcripts for (a) real user prompts that should trigger
  the skill and (b) real outputs to derive assertions. Start with 2-3; expand.
- **Applicability:** MEDIUM. This is the path to making R1 actually runnable
  regularly. [[cross-session-transcript-mining-continuous-improvement]] documents
  the 3-layer architecture (episodic→working→procedural); this is the
  episodic→eval-case edge that has no automated pipeline yet.
- **Evidence basis:** single-source principle (agentskills.io "start with 2-3,
  expand later") + our transcript corpus. The auto-generation mechanism itself
  is `[INFERENCE]` — no system does this end-to-end yet.

### R7. Make Mode 2 SUBTRACTIVE-capable. `[SUPPORTED] [UNTESTED]`
- **Mechanism:** add a "remove over-constraining rules" proposal type. When an
  improvement plateaus or when transcripts show wasted work (unnecessary
  validation, unneeded intermediate outputs), propose *removing* instructions
  and re-testing. This serves [[skill-lean-code-context-efficiency]].
- **Applicability:** HIGH and cheap. Mode 2 currently only adds. The
  agentskills.io principle is explicit and multi-source-confirmed.
- **Evidence basis:** agentskills.io + the 545-pt practitioner post (40%
  redundancy, line-100 cliff).

### R8. Adopt "scar, not resume" as an authoring + improvement principle. `[SUPPORTED] [UNTESTED]`
- **Mechanism:** every improvement proposal must answer "what does the model
  CONSISTENTLY GET WRONG that this addresses?" If the answer is "nothing — it
  just reminds the model," the improvement measures ~0 gain. Reject resume-style
  improvements ("You are an expert...").
- **Applicability:** HIGH as a gate; near-zero cost.
- **Evidence basis:** practitioner consensus (928-pt post) + SkillsBench (LLM
  skills that state what the model knows give 0 gain).

## Workspace-counterexample check (Step 3.15)

- **R1-R3 (eval-driven, fault attribution):** no counterexample. The wiki
  *supports* moving to mechanical/external-signal enforcement
  ([[mechanical-enforcement-of-llm-skill-steps-2026]]). The Huang 2024 caveat
  ([[self-improving-agent-systems-techniques-and-workspace-gaps]]) is satisfied
  because eval-driven uses an *external* signal (with/without comparison), not
  pure intrinsic self-correction.
- **R4 (exclusion clauses):** no counterexample — extends our own T16.
- **R6 (auto-generate evals from transcripts):** check against
  [[measurement-before-addition-principle]] — "adding detection to a
  low-conversion system makes it worse." Eval-generation is itself measurement,
  not detection-addition, so the principle does not block it. But the *output*
  of evals (more findings) into a low-action-rate system WOULD — so R6 must
  pair with R1's "only act on the delta," not generate evals that flood.
- **Goodhart risk (R4):** ⚠️ flagged above — no numeric targets; measure and
  surface only. Consistent with /deferred-and-rejected-skill-improvements-registry.
- **Subagent infrastructure caveat:** this very /www run could not use parallel
  research subagents — `pick_model.py`'s top 3 lanes (cerebras reasoning =
  8192 ctx limit; nim deepseek = EOL today 2026-08-07; cohere coding = trial
  rate-limited) were ALL unusable for spawn_subagent. R1's eval loop will hit
  the same wall unless a reliable high-context subagent model is available.
  See [[tool-fallbacks]].

## Host invariant check (Round 3.5)

- R1's with/without runs must respect multi-terminal isolation — no shared live
  browser state, session-scoped artifacts. Use `spawn_subagent` with fresh
  context (the context firewall pattern), not a second concurrent driver.
- R6's transcript mining must not read live session state — read closed
  transcripts at `~/.grok/sessions/`.
- No violations detected in the recommendations themselves.

## How to read the evidence basis tags

- `[SUPPORTED]` = multi-source or field-consensus. Higher confidence.
- `[PRELIMINARY]` = single primary source, mechanistically sound.
- `[INFERENCE]` = reasoned from principles, not yet demonstrated.
- All `[UNTESTED]` = not run on this workspace this session. The next step for
  every recommendation is a small eval-driven pilot on ONE skill (a narrow one
  like `/bf` or `/tdd`, not a meta-skill) to measure the delta before fleet rollout.

## Falsifier

These recommendations are wrong if:
- **Our judge models cannot grade reliably** → eval deltas are noise, and R1/R2
  produce worse signal than current MEC. Test: grade 5 known-good vs known-bad
  skill outputs blind; if the judge can't separate them, the approach fails.
- **Meta-skills resist isolation testing** → R1 only works for narrow skills,
  not for /tp, /close, /review. Test: try to construct a with/without eval for
  /handoff; if the observable artifact can't be assertion-checked, the gap is
  real.
- **The coverage-vs-quality finding doesn't transfer** → SkillAxe's "skills are
  execution knowledge" was measured on SpreadsheetBench (procedural tasks). Our
  meta-skills may behave differently. Test: decompose one meta-skill's gain
  into coverage vs quality.
- **Subagent infrastructure stays broken** → R1 can't run parallel with/without
  at all. This is a blocking dependency, not a methodology question.

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| LLM-authored skills give ~0 gain; human +16.2pp | SkillAxe abstract + SkillsBench (arXiv 2606.10546) — read in full this session | [OBSERVED] primary source |
| SkillAxe closes 47-67% of gap; +28% relative | SkillAxe abstract + Table 2 | [OBSERVED] primary source |
| Entire gain is coverage, not quality (both 57.1%) | SkillAxe §4.2 Table 2 | [OBSERVED] primary source |
| Fault attribution separates agent-fault from skill-fault | SkillAxe §3.3 + Table 1 | [OBSERVED] primary source |
| Exclusion clauses → 3× discrimination margin | SkillAxe Appendix E Tables 6-7 | [OBSERVED] primary source |
| "skills past line 100 get treated as suggestions" | r/ClaudeAI DevMoses post (545 pts) — read in full | [OBSERVED] practitioner |
| "a skill should be a scar, not a resume" | r/ClaudeAI 928-pt post + mod TL;DR | [OBSERVED] practitioner |
| SkillBenchmark: blind judge with/without + CIs | r/ClaudeAI Ties_P post — read in full | [OBSERVED] practitioner |
| Pure self-correction fails without external signal | Huang et al. 2024 TACL (cited via search, not full-text) | [INFERENCE] — secondary cite |
| Our Mode 2 has no execution step | `skill-dev/SKILL.md` Mode 2 read in full this session | [OBSERVED] |
| skill-dev has no fault attribution / no solution-path coverage | grep of skill-dev body | [OBSERVED] |
| pick_model lanes broken for subagents today | this session: cerebras 8192 ctx, deepseek EOL 2026-08-07, cohere trial-limit | [OBSERVED] |

## Related concepts

- [[claude-side-skill-improvement-tooling-2026]] — the 5 capability gaps vs Anthropic skill-creator; this adds the SkillAxe mechanism
- [[skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency]] — trigger accuracy + token efficiency gaps; this provides the concrete measurement method
- [[self-improving-agent-systems-techniques-and-workspace-gaps]] — Huang 2024 caveat is precisely why eval-guided works
- [[skill-lean-code-context-efficiency]] — R7 (subtractive improvement) serves leanness
- [[mechanical-enforcement-of-llm-skill-steps-2026]] — evals are mechanical enforcement of skill quality
- [[measurement-before-addition-principle]] — R6 must pair with R1
- [[routine-skill-improvement-cadence]] — when to run the eval-driven loop
- /deferred-and-rejected-skill-improvements-registry — Goodhart warning on numeric targets

## What this means for our workspace

1. **The single highest-leverage change to skill-dev:** add a fault-attribution
   step (R2) before any Mode 2 rewrite. It is cheap (one extra judge call per
   violated rule) and prevents the dominant failure mode (rewriting correct
   rules). This is the SkillAxe §3.3 mechanism.
2. **Make eval-driven the default, not opt-in (R1).** Mode 2.5 exists but is
   high-friction. The fix is R6 (auto-generate evals from transcripts) so the
   operator doesn't hand-write them. Pilot on one narrow skill first.
3. **Add solution-path coverage (R3 dim 4) — it is entirely absent and
   high-value for multi-strategy skills.**
4. **Block dependency:** fix subagent model availability (cerebras ctx limit,
   deepseek EOL, cohere trial). R1's parallel with/without runs need a reliable
   high-context subagent model. Record in [[tool-fallbacks]].
5. **skill-dev itself has a defect:** its own frontmatter lists `host: grok`
   twice (lines 14-15) — ironic for the skill that checks frontmatter. Fix on
   next edit.
