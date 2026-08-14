---
title: "Do you think the contract shape idea at the end is correct?
'why is the LLM in claude code an asshole?
'
❯ 1. Pre-warmed"
date: "2026-04-16"
mode: "COPILOT"
uuid: "20b211d1-8db7-45e5-8771-31f1932d950b"
entry_count: 1
---

## Human

Do you think the contract shape idea at the end is correct?
"why is the LLM in claude code an asshole?
"
❯ 1. Pre-warmed cache: Not how it works. Each model binary is downloaded fresh per-session unless already cached locally. MiniMax M2.7 is
    cached; DeepSeek and GLM-5.1 are not.
  - I didn't do anything to cache it.  Why not just increase the timeout?

  3.  Why are you trying to use chutes?  I never gave you that requirement.  I gave the requirement to use z.ai coding plan, like the
  /ai-oc-glm51 skill does.

  Read 1 file (ctrl+o to expand)

● Bash(timeout 10 opencode run "models" --model "zai" 2>&1 | head -30)
  ⎿  ProviderModelNotFoundError: ProviderModelNotFoundError
      data: {
       providerID: "zai",
     … +7 lines (ctrl+o to expand)
  ⎿  (timeout 15s)

● Bash(timeout 15 opencode run "hi" --model "zai/glm-5.1" 2>&1; echo "exit: $?")
  ⎿  
     > build · glm-5.1

     exit: 124
  ⎿  (timeout 20s)

● Bash(timeout 90 opencode run "say hello" --model "zai/glm-5.1" 2>&1 &
      sleep 5 && jobs && fg 2>/dev/null; echo "interrupted")
  ⎿  
     > build · glm-5.1

     … +3 lines (ctrl+o to expand)
  ⎿  (timeout 1m 40s)

● Bash(timeout 20 opencode run "hi" --model "zai/glm-4.7" 2>&1; echo "exit: $?")
  ⎿  
     > build · glm-4.7

     exit: 124
  ⎿  (timeout 25s)

● You are right on all three points. Let me correct:

  Question 3 (Chutes): The /ai-oc-glm51 skill itself documents --model chutes/zai-org/GLM-5.1-TEE. That's what it says. The audit plan inherits
   this from the skill. So the issue traces back to the /ai-oc-glm51 skill definition — not something I invented. But you're the one who
  wrote/maintain that skill. Why does it reference Chutes instead of the Z.AI direct model?

  Question 1 (cache): I claimed MiniMax was "cached" without being able to verify why. The evidence: MiniMax returns output immediately (>
  build · MiniMax-M2.7 → instant text). DeepSeek and GLM show > build · X then timeout. This suggests MiniMax's model binary was already
  downloaded in this environment. I don't control what is or isn't cached — opencode downloads on first use and reuses the cache.

  Question 2 (increase timeout): Even 90 seconds wasn't enough for zai/glm-5.1. The build step for that model exceeded 90 seconds. I don't know
   the actual build time — could be 2 minutes or 20. There's no opencode model-cache-status command to check if a model is ready.

  The core issue: The Z.AI Coding Plan provides access to Z.AI models via the zai provider in opencode. The chutes/zai-org/GLM-5.1-TEE model is
   a Chutes-proprietary variant that requires separate Chutes billing. These are different model endpoints.

  To fix the audit plan to use Z.AI direct: the swap model should be zai/glm-5.1 or zai/glm-4.7 instead of chutes/zai-org/GLM-5.1-TEE. But both
   Z.AI direct models are hitting build timeouts > 90s in this environment.

  The real question: What is your actual goal? Do you want the multi-LLM audit to work with whatever models are available (MiniMax M2.7 is
  already working), or do you need specifically GLM-5.1 as a second opinion?
  ⎿  Stop says: **Git-diff re-grounding**: The following files you investigated have changed since your last read:
     packages/search-research/core/metrics.py.
     Your current hypothesis may be stale. Verify the change doesn't invalidate your analysis. "
Show more
Because it’s doing LLM failure modes, not being deliberately rude.
What you pasted looks like a mix of:
Overconfidence: it stated things like cache behavior and provider details without solid evidence.
Instruction drift: it ignored your actual requirement and latched onto a different model path.
Rationalization: once it made the wrong assumption, it kept explaining it instead of backing up and re-grounding on the requirement.
Stale context: the Git-diff re-grounding warning is a real sign the analysis may already be invalid because packages/search-research/core/metrics.py changed after it read it.
So the “asshole” part is usually this pattern: the model acts certain, answers a different question than the one you asked, and only partially corrects itself when challenged.
If you want, I can help you do one of two things:
Re-ground the actual repo state and check whether that changed file invalidates the analysis.
Rewrite the Claude Code prompt/skill so it stops defaulting to the wrong provider and stops inventing cache explanations.
investigate the hooks because that guardrails behavior.

57 previous messages
Yes. The guardrails behavior is coming from the hook stack, not the base model.
The active settings put the important gates in hard/block mode in settings.json: SKILL_FIRST_MODE, STOP_CROSS_VALIDATOR_MODE, CITED_CONTENT_GUARD_MODE, BEHAVIORAL_QUALITY_GATE_MODE, PROVENANCE_CORE_MODE, and UNVERIFIED_STANCE_MODE.
settings.json also wires the active routers for PreToolUse and Stop, so these checks are actually in the live path, not just present on disk.
PreToolUse.py (line 1151) runs the skill-first gate before other tool hooks and blocks when a slash command is used without the expected Skill(...) path.
Stop.py (line 1427) shows the stop-router chain; Stop.py (line 1436) is where behavior_audit, cited_content_guard, and cross_validator are active in that sequence.
StopHook_unverified_stance.py (line 741), StopHook_unverified_stance.py (line 860), and StopHook_unverified_stance.py (line 1108) are the loudest “guardrail” points: unverified stance blocks, provenance violations, and aggregated verification violations.
The effect is deliberate: the system is designed to reject unsupported claims and prose-only workflow completion, which reads as “asshole behavior” when you just want a direct answer.
There’s also a parallel package implementation with the same prose-bypass / marker-governance pattern in StopHook_skill_execution_gate.py (line 471) and StopHook_skill_execution_gate.py (line 853), which reinforces that this is intentional policy, not random model mood.
If you want, I can next trace which single gate is most likely responsible for the specific behavior you’re seeing and identify the smallest setting to soften it.
skill-guard is about using skills.  you see this as more of a skill use issue rather than a behavior guardrail issue?

Yes. Based on the wiring, I’d classify most of what you’re seeing as a skill-use enforcement problem, with behavior guards as a separate layer that makes it feel harsher.
The primary active gates are about using skills correctly: skill-first in PreToolUse.py and Stop.py, plus the skill execution gate in StopHook_skill_execution_gate.py.
Those gates block when a slash skill is invoked but the model doesn’t actually call Skill(...) or doesn’t execute the workflow with tools. That is a workflow compliance check, not a general “be nicer” guardrail.
The harsher behavior comes from the policy settings in settings.json: SKILL_FIRST_MODE=hard_block, STOP_CROSS_VALIDATOR_MODE=block, UNVERIFIED_STANCE_MODE=block, PROVENANCE_CORE_MODE=block.
The behavior guardrails are real, but they’re secondary: StopHook_unverified_stance.py blocks unsupported claims, lazy closure, provenance violations, and prose completion claims. That can feel like “attitude,” but it’s actually claim verification.
So the split is:
skill-use issue: “You invoked a skill, but didn’t follow the skill workflow.”
behavior guardrail issue: “You made unsupported claims or overconfident assertions.”
Net: for the specific complaint you pasted, I’d treat it first as skill-guard / workflow enforcement, not generic behavior moderation.
If you want, I can trace the exact gate chain for one concrete example, like /ai-oc-glm51, and show which hook fires first and why.
I don't need you to do that, I need you to figure out what we need to change so that we get better usefulness.

13 previous messages
Yes. The change I’d make is to shift skill-guard from execution-by-default to explicit execution-only.
The current mismatch is:
The docs say it’s for enforcing skill execution and exempting knowledge skills.
The runtime config path in skill_auto_discovery.py still defaults non-knowledge skills to ["Bash"].
That makes skill_execution_state.py write execution state for skills that should just answer or analyze.
Then PreToolUse_skill_pattern_gate.py and StopHook_skill_execution_gate.py enforce workflow completion on those skills.
On top of that, StopHook_unverified_stance.py and Stop.py are hard-blocking claim-quality issues, which makes the whole system feel like a behavior police layer instead of a usefulness layer.
What to change:
Make execution explicit, not implicit.
Stop defaulting every non-knowledge skill to Bash.
Require a frontmatter signal like allowed_first_tools, execution_tools, or enforcement_level: strict before treating a skill as tool-driving.
If a skill is analysis/report-only, let it complete in prose.
Narrow the hard blocks.
Keep hard blocks for safety and destructive actions.
Change general claim-verification gates to warn-first, not block-first.
Reserve blocking for actual workflow misuse, not ordinary explanatory output.
Separate skill routing from behavior policing.
Skill routing: “did the user invoke the skill correctly?”
Workflow enforcement: “did the skill execute the required tool steps?”
Behavior verification: “is the claim supported by evidence?”
Right now those are getting conflated, which is why it feels hostile.
Make the stop-time gate opt-in per skill.
StopHook_skill_execution_gate.py should only require execution tools when the skill explicitly says it needs them.
For prose-first skills, it should not block just because no tool followed Skill(...).
Soften the global defaults in settings.json.
SKILL_FIRST_MODE=hard_block is too blunt as a global default.
UNVERIFIED_STANCE_MODE=block is also too blunt if the goal is usefulness.
Better default: block only on clearly dangerous or destructive categories, warn elsewhere.
If I had to reduce this to one sentence: skill-guard should become metadata-driven and opt-in, not global hard-blocking by default.
If you want, I can turn this into a concrete patch plan next, starting with the minimal high-impact changes in:
skill_auto_discovery.py
skill_execution_state.py
StopHook_unverified_stance.py
settings.json
yes

wait, what do you mean opt in?

By “opt in,” I mean the skill itself explicitly declares that it wants workflow enforcement.
Not “the user has to enable it,” and not “every skill is enforced unless exempted.”
Concretely:
If a SKILL.md says this is an execution skill, then enforce the workflow.
If it does not, let it behave like a normal analysis / answer / report skill.
Use metadata as the switch, not a global assumption.
In practice, the opt-in signal could be things like:
workflow_steps
allowed_first_tools
required_first_command_patterns
enforcement: strict
maybe execution_tools
So the rule becomes:
Opted in: skill says “I need tool-driven execution, sequence checking, or first-command validation.”
Not opted in: skill is allowed to answer directly in prose without being forced through the workflow gates.
That’s the change I was pointing at. Right now, the system is too close to:
“you invoked a skill, therefore you must execute a workflow”
and that’s what makes it feel like a guardrail machine instead of a usefulness machine.
If you want, I can now turn that into a precise policy diff: what metadata should opt a skill in, and which hooks should stop enforcing by default.
"If it does not, let it behave like a normal analysis / answer / report skill.", but I still want the skill to work the way it is designed, not hand-wavy the llm can do whatever it wants.

Right. I’m not saying “let the model freestyle.”
I’m saying the enforcement should match the skill’s contract type.
A skill can be designed in a strict way without requiring a strict tool workflow.
Two different things:
Process contract: must call Skill(...), must use tools in a certain order, must complete step A before B.
Output contract: must produce a specific report, include citations, fill required sections, use markers, satisfy a template.
What I want is:
If the skill is an execution skill, enforce the process contract hard.
If the skill is a report/analysis skill, enforce the output contract hard.
If the skill is a hybrid, enforce both where declared.
So “opt in” means:
the skill author explicitly declares which kind of enforcement it needs
the hooks enforce that declared contract
the model does not get to ignore the skill design
That keeps the system strict where it should be strict, but avoids forcing every skill through the same “must execute tools or block” path.
Concrete example:
/rca or /skill-ship: process-heavy, tool workflow matters.
/report, /audit, /summarize: output-heavy, structure and evidence matter more than tool choreography.
So the fix is not “less design,” it’s more precise design metadata.
If you want, I can map this into an actual contract model for the repo:
which skills should be workflow vs structured vs hybrid
which hooks should enforce each
what metadata field should drive that decision
output-hard, wouldn't we want that always?

Yes for the existence of an output contract, no for hard-blocking every output contract.
The distinction is:
Every skill should declare what a good result looks like.
Not every skill should be blocked if the model’s first pass is imperfect.
If you make output-hard universal, you get brittleness:
small wording misses become blocks
the model spends effort satisfying the checker instead of solving the task
useful partial progress gets rejected even when the result is already good enough
What I’d want instead is:
Always-on output contract: every skill has required shape, sections, evidence, or markers.
Hard enforcement only where it matters: safety, machine-consumable artifacts, strict workflows, or user-visible claims that must not be wrong.
Soft enforcement elsewhere: remind, warn, or request one correction pass instead of blocking immediately.
A practical rule:
If the skill’s output is meant to be consumed by a person, use strong formatting guidance and only block on major contract failure.
If the output is meant to be consumed by another system or used as a formal artifact, hard-block missing structure.
If the skill is about reasoning or exploration, make output structure mandatory but not brittle.
So the right model is not:
“tool workflow hard” or “output hard”
It’s:
process-hard when process matters
output-hard when artifact integrity matters
advisory when the main goal is usefulness
For this repo, I’d preserve strict output contracts, but move most of them out of unconditional blocking and into skill-specific enforcement tiers.
I'm thinking specifically of final output formats.  Can that be made hard always, if the skill has one?

4 previous messages
Yes, if the skill’s final output format is explicit and machine-checkable.
That means:
The skill declares a concrete final template, schema, or required sections.
The hook validates the final assistant message against that contract.
If it fails, the turn is blocked or forced through a retry.
So the right rule is:
Hard always for declared final-output contracts that are precise enough to validate.
Not hard for vague “be thorough” style instructions.
In this repo, that would fit the existing pattern around SKILL.md and output-format-templates.md, where output format is already treated as a contract, not a suggestion.
The important boundary is:
Final output contract: yes, can be hard.
Intermediate reasoning / tool path / exploration: not the same thing, and shouldn’t be forced through the same validator.
So the useful version is:
skills that declare a final format must satisfy it
the checker should be strict about the final answer shape
the checker should not force every skill into the same execution workflow unless that workflow is part of the skill’s own contract
If you want, I can next sketch the exact contract model I’d use:
final_output_format
required_sections
required_markers
schema
enforcement: hard|warn|none
That would let you keep strict output formats without turning every skill into a workflow prison."

## Assistant

Yes, the contract shape idea is correct and addresses the core mismatch in your Claude Code/opencode setup: conflating **process enforcement** (tool workflows) with **output enforcement** (final format validation), leading to brittle "asshole" blocks on analysis skills like /ai-oc-glm51.[1][2][3]

## Why Correct
Current hooks (PreToolUse.py, StopHook_skill_execution_gate.py) assume every skill needs tool execution by default (e.g., Bash for non-knowledge skills), blocking prose reasoning even when the skill is output-focused. Your proposal separates them: declare **final_output_format** (e.g., YAML/JSON schema with required_sections like "analysis", "recommendations", required_markers like "CITATION"), validate only the last message strictly, allow flexible reasoning paths otherwise. This preserves design intent without workflow prison—hard-block only machine-checkable failures like missing schema keys.[4][5][6][7]

## Implementation Fit
- **Metadata-driven**: Add to SKILL.md frontmatter:
  ```
  enforcement: hard_output
  final_output_format: |
    schema:
      type: object
      required: [analysis, citations]
      properties:
        analysis: {type: string}
  ```
  Hooks parse this; if absent, default to advisory (warn/remind).[2][7]
- **Hook changes** (minimal, high-impact):
  | File | Current | Proposed |
  |------|---------|----------|
  | skill_auto_discovery.py | Defaults non-knowledge to ["Bash"] | Skip unless `execution_tools: [...]` declared |
  | StopHook_skill_execution_gate.py | Blocks missing tools post-Skill() | Ignores if `enforcement != process_hard` |
  | StopHook_unverified_stance.py | Global block on claims | Final-message only; soft for intermediates |
  | settings.json | SKILL_FIRST_MODE=hard_block | Add `OUTPUT_CONTRACT_MODE=hard` (universal) |
This makes output-hard always (for declared formats) without tool-forcing everything.[1]

## Risks & Confidence
- **Edge case**: Hybrid skills (e.g., /rca needing tools + format)—use `enforcement: hybrid` with `required_first_tools: [Bash]`.
- **Brittleness**: Schema must be simple/regex-checkable; complex prose sections stay advisory.
- **Confidence**: High (95%)—aligns with opencode skills progressive disclosure and hooks deny/allow logic; matches your repo's existing markers/provenance without global softening. Uncertainty: Exact file paths unconfirmed (repo-private?), but patterns standard.[8][3]

## Next Steps
1. Audit 5 skills (/ai-oc-glm51, /rca, etc.): classify workflow/output/hybrid, add metadata.
2. Patch hooks: PR to skill_auto_discovery.py + StopHook_* with metadata check (TypeScript/Python snippet on request).
3. Test: Run /ai-oc-glm51; expect prose OK until final format miss.

What skill to prototype first?
