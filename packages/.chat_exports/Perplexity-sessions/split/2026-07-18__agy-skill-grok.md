---
title: "AGY Skill - Grok"
date: "2026-07-18"
mode: "COPILOT"
uuid: "032b5331-a170-48c7-8f69-6db55cffa202"
entry_count: 8
---

## Human

I gave this to grok and it proposed that prompt.  Would you change anything?  Do you want to see the skill?
"
     ❯ /agy cricially review the agy skill                                                                               9:26 PM


     ◆ Thought for 7.2s

     Running the Pre-Flight Check on your input "cricially review the agy skill":                                        9:27 PM

     • TARGET — "the agy skill" is vague. Resolving to: C:/Users/brsth/.grok/skills/agy/SKILL.md
     • TASK — present: "critically review"
     • CONTEXT — missing. Filling in from session state.

     Since TARGET and CONTEXT needed conductor fill-in, here's the assembled prompt for your approval before I send it
     to agy:

     ───

     Proposed agy prompt:

     │ Read the file at C:/Users/brsth/.grok/skills/agy/SKILL.md — this is a Grok Build skill that wraps the
     │ Antigravity CLI (agy/Gemini) for second-opinion reviews. It was just rewritten to add a Pre-Flight Check
     │ (TARGET/TASK/CONTEXT gate) after an incident where the conductor sent agy an underspecified prompt and agy
     │ reviewed the wrong file.
     │
     │ Task: critically review this skill. Specifically look for:
     │ 1. Does the Pre-Flight Check actually prevent the failure mode it was designed for?
     │ 2. Are there cases where the check passes but the prompt is still garbage?
     │ 3. Is the "show the user and ask permission" step the right friction level, or too much/too little?
     │ 4. Anything missing, contradictory, or over-specified?
     │ 5. Would this skill produce good outcomes if followed literally by a model under momentum?

     ───
"

## Assistant

Yes, I’d tweak that prompt a bit, but it’s already close to what I’d want structurally. The big changes I’d make are about precision, failure‑mode framing, and how much meta-context you bake into the task versus letting agy infer from the SKILL.md itself.[1][2]

I’d definitely like to see the skill at some point, but we can still usefully iterate on the review prompt just from this.

***

## Quick read on your current prompt

What you have:

> Read the file at C:/Users/.../agy/SKILL.md — this is a Grok Build skill that wraps the Antigravity CLI (agy/Gemini) for second-opinion reviews. It was just rewritten to add a Pre-Flight Check (TARGET/TASK/CONTEXT gate) after an incident where the conductor sent agy an underspecified prompt and agy reviewed the wrong file.  
>  
> Task: critically review this skill. Specifically look for:  
> 1. Does the Pre-Flight Check actually prevent the failure mode it was designed for?  
> 2. Are there cases where the check passes but the prompt is still garbage?  
> 3. Is the "show the user and ask permission" step the right friction level, or too much/too little?  
> 4. Anything missing, contradictory, or over-specified?  
> 5. Would this skill produce good outcomes if followed literally by a model under momentum?

High-level assessment:

- **Structure** is good: clear task, concrete sub‑questions, reference to the target artifact.[1]
- It’s missing a bit of “how to respond” guidance: level of detail, examples, and expectation to enumerate failure modes and suggest improvements.
- There’s a subtle bias: you’re framing around one specific incident (“reviewed the wrong file”), which may make the model overweight that failure mode relative to other plausible ones.
- There’s no explicit direction to sample scenarios (few-shot “run the skill mentally” with varied inputs), which is usually key for testing preflight logic.[2]

***

## What I’d change (and why)

### 1. Tighten the objective and output format

Right now “critically review this skill” is broad. I’d make the objective:

- Explicit about producing a *structured report*.
- Explicit about prioritizing *mechanical failure modes* over style.

Proposed modification:

> Task: **critically review** this skill and produce a structured report with:
> - A brief summary of what the skill is trying to do.  
> - A list of concrete failure modes, with input examples that would trigger them.  
> - Recommended changes to the SKILL.md, phrased as specific edits or additions (not just high-level advice).

Why: “structured report + concrete failure modes + recommended edits” pushes the model toward actionable outputs and away from generic critique. This aligns with prompt design guidance that emphasizes clear objectives, structure, and expected output format.[1]

### 2. Make the Pre‑Flight Check evaluation more scenario‑driven

Your Q1 and Q2 are good, but they’re meta. I’d force the model to *simulate* usage with multiple inputs:

Current:

1. Does the Pre-Flight Check actually prevent the failure mode it was designed for?  
2. Are there cases where the check passes but the prompt is still garbage?

Suggested rewrite:

> 1. Identify the specific failure modes this Pre‑Flight Check is intended to prevent. For each, construct at least one example user input and walk through how the skill would process it step by step. Note whether the failure is actually prevented.  
> 2. Construct at least three example inputs where the TARGET/TASK/CONTEXT gate would *pass* but the resulting agy prompt is still low‑quality (ambiguous, mis‑scoped, or misleading). Explain why the gate fails to catch these and what additional checks or constraints might help.

Why: forcing “example inputs + step‑by‑step walkthrough” is essentially a manual test harness for the skill, which is much closer to your real concern (will this gate work under realistic usage?). It mirrors preflight checklist patterns that enumerate assumptions, failure paths, and adversarial inputs.[2]

### 3. Sharpen the friction-level question

Your Q3 (“is the ‘show the user and ask permission’ step the right friction level”) is good but underspecified. I’d:

- Anchor it in different usage modes (expert vs casual, high‑risk vs low‑risk).
- Ask explicitly for trade‑offs and alternative designs.

Proposed rewrite:

> 3. Evaluate the “show the user and ask permission” step:
> - Describe the trade‑off between user safety/clarity and interaction friction for this skill.  
> - Consider at least three scenarios (e.g., quick low‑risk review, high‑stakes production review, batch operations). In which scenarios is this friction appropriate, too high, or too low?  
> - Suggest concrete alternative designs (e.g., opt‑in bypass, batched confirmation, different wording) if you think the current approach is suboptimal.

Why: this pushes the model to think in terms of permission UX patterns, which is consistent with emerging work on user‑level permissions and authorization in agent systems.[3][4][5]

### 4. Clarify “missing, contradictory, over‑specified”

Q4 is good but broad; you can get more signal by splitting it into distinct checks:

Current:

> 4. Anything missing, contradictory, or over-specified?

Suggested rewrite:

> 4. Analyze the SKILL.md specification quality:
> - Missing: Identify any behaviors, edge cases, or constraints that should be documented for safe, predictable use but are absent.  
> - Contradictory: Point out any conflicting instructions or definitions that could confuse the agent.  
> - Over‑specified: Identify areas where the skill is unnecessarily prescriptive in ways that might prevent useful behavior or adaptation by the agent.

Why: asking for each category separately produces a more systematic pass over the skill doc, consistent with prompt health checklists that look at clarity, completeness, and consistency.[1]

### 5. Refine “momentum” and literal execution

Q5 is good but somewhat vague about what “good outcomes” means and what “momentum” implies.

Suggested rewrite:

> 5. Assume a competent but literal model that:
> - Follows the SKILL.md instructions exactly.  
> - Has limited opportunity to clarify ambiguous inputs once execution starts.  
> - Is operating under “momentum” (it’s incentivized to proceed rather than stop and ask).  
>  
> Under these assumptions, assess whether this skill would produce robust, safe outcomes across:
> - Typical use (well‑specified TARGET/TASK/CONTEXT).  
> - Borderline inputs (partially specified, noisy, or conflicting signals).  
> - Adversarial or pathological inputs (underspecified, misleading, or conflicting instructions).  
>  
> For each category, rate outcome quality on a simple scale (e.g., High / Medium / Low) and justify the rating.

Why: this makes your “model under momentum” assumption explicit and forces coverage of normal, borderline, and adversarial regimes, again mirroring robust prompt design practices.[6][2]

***

## A revised end‑to‑end prompt

Here’s how I’d rewrite the whole thing, keeping your original intent but tightening it for an agent/skill review:

> Read the file at `C:/Users/brsth/.grok/skills/agy/SKILL.md`. This is a Grok Build skill that wraps the Antigravity CLI (`agy`) for second‑opinion reviews, and it was recently rewritten to add a Pre‑Flight Check (TARGET/TASK/CONTEXT gate) after an incident where the conductor sent agy an underspecified prompt and agy reviewed the wrong file.  
>  
> **Task:** Critically review this skill and produce a structured report with:  
> - A brief summary of what the skill is trying to do.  
> - A list of concrete failure modes, with example inputs that would trigger them.  
> - Recommended changes to the SKILL.md, phrased as specific edits or additions.  
>  
> Specifically address:
> 1. Identify the failure modes the Pre‑Flight Check is intended to prevent. For each, construct at least one example user input and walk through how the skill would process it step by step. State whether the failure is actually prevented.  
> 2. Construct at least three example inputs where the TARGET/TASK/CONTEXT gate would pass but the resulting agy prompt is still low‑quality (ambiguous, mis‑scoped, or misleading). Explain why the gate fails to catch these and what additional checks or constraints might help.  
> 3. Evaluate the “show the user and ask permission” step: describe the trade‑off between safety/clarity and interaction friction; consider at least three scenarios (low‑risk quick review, high‑stakes production review, batch operations); and suggest concrete alternative designs if the current approach is suboptimal.  
> 4. Analyze the SKILL.md specification quality: call out missing behaviors/constraints that should be documented, any contradictory instructions, and any places where the skill is over‑specified in a way that might block useful behavior.  
> 5. Assume a competent but literal model that follows the SKILL.md exactly, has limited opportunity to clarify once execution starts, and is operating under “momentum” (it tends to proceed rather than stop and ask). Under these assumptions, assess whether this skill would produce robust, safe outcomes for typical, borderline, and adversarial inputs. For each category, rate outcome quality (High / Medium / Low) and justify your rating.  
>  
> Focus your critique on how well the skill guards against mis‑targeting, underspecified prompts, and unsafe or confusing behavior by downstream agents, rather than on minor wording or style issues.

This keeps the spirit of what Grok proposed, but:

- Makes the output shape explicit.
- Anchors the analysis in multiple concrete scenarios.
- Clarifies the “momentum” assumption and friction question.
- Encourages the reviewer to think like a safety engineer, not just a copy editor.[6][2][1]

***

If you’re up for it, sharing the SKILL.md (or a redacted version) would let me sanity‑check whether this prompt is over‑ or under‑scoped relative to what agy is actually doing.  

## Human

How to optimize prompting for local LLM skill review
How to write robust system prompts for code validation

## Assistant

There are two distinct but related things here: (1) prompts you use to get a **local model to review a skill** (like your agy SKILL.md), and (2) **system prompts** that define a persistent “code validator” agent. I’ll treat them separately and tie them together.[1][2]

***

## 1. Optimizing prompts for local LLM skill review

Goal: you want a local model (running via LM Studio / llama.cpp / etc.) to reliably stress‑test a skill file: find failure modes, missing constraints, and bad UX, not just nitpick wording. A good skill‑review prompt has four pillars:

### A. Make the review task concrete and structured

Instead of “critically review this skill”, you want something like:

- Define the **artifact**: “You are reviewing a skill definition file (SKILL.md) for an LLM agent that wraps TOOL_X.”
- Define the **job**: “Your job is to find concrete failure modes, missing constraints, contradictory instructions, and over‑ or under‑specification.”
- Define the **output shape**: sections and bullet lists, not freeform prose.

Template:

> You are a **skill safety and robustness reviewer** for local LLM agents.  
> You are given a skill specification file (SKILL.md) that defines how an agent should use a tool.  
>  
> Task: Produce a structured report with:
> - A short summary of what the skill intends to do.  
> - A list of concrete failure modes, each with a minimal input example and step‑by‑step explanation of how the failure occurs.  
> - Findings about missing, contradictory, or over‑specified instructions.  
> - Specific, actionable edits to the skill text.

This mirrors best practices for system prompts: clear role, scope, and structured instructions.[2][1]

### B. Force scenario-based “mental execution”

Local models are brittle; getting them to “actually run the skill in their head” is key. You want explicit directions to:

- Construct diverse **example inputs** (well‑specified, underspecified, adversarial).
- Walk the skill logic step by step in each scenario.
- Compare expected behavior vs. desired behavior.

Pattern:

> For this review, simulate at least:
> - 2 well‑specified inputs (clear TARGET/TASK/CONTEXT).  
> - 2 underspecified or noisy inputs (missing or conflicting fields).  
> - 2 adversarial/pathological inputs (misleading TARGET, conflicting instructions).  
>  
> For each input:
> 1. Show the input.  
> 2. Describe how the skill would parse and interpret it.  
> 3. Describe what prompt or action it would send to the downstream tool/agent.  
> 4. State whether the outcome is acceptable, ambiguous, or unsafe, and why.

This aligns with evaluation guidance that emphasizes scenario‑based test prompts and diverse test cases rather than single “hero prompts.”[3][4][5]

### C. Encode success criteria and failure modes up front

Your review prompt should encode what “good skill behavior” looks like and what classes of failure you care about:

- Correct targeting (right file / right resource).
- Handling of underspecified requests.
- UX friction vs. safety (confirmations, preflight).
- Safety constraints (authorization, environment limits).

You can give a short checklist:

> Treat the skill as “good” only if:
> - It reliably applies operations to the intended TARGET and never silently acts on the wrong file/resource.  
> - It detects underspecified requests and either asks for clarification or refuses, instead of guessing.  
> - It uses confirmation or friction appropriately for risky operations.  
> - It documents its assumptions and limits clearly (permissions, environment, tools).  
>  
> Whenever the skill fails one of these, add a distinct finding to your report.

That’s very close to the “explicit validation criteria” pattern for system prompts.[6][1]

### D. Adapt to local model limits (context, quality, determinism)

Local models impose constraints you can bake into your prompt and workflow:

- **Context window:** keep the prompt compact; move reusable instructions into a reusable “review harness” and feed SKILL.md separately.
- **Quality:** shallow models need more explicit structure to avoid hand‑wavy critique.
- **Determinism:** if you care about repeatability, fix temperature and sampling parameters and keep the prompt stable across runs.[7][8]

Operationally, for a local skill‑review harness:

- Define a reusable **review system prompt** (as above).
- Feed the SKILL.md as a user message.
- Optionally add a final “compress your findings into a 1‑page summary” step if you want shorter outputs.

***

## 2. Writing robust system prompts for code validation

Now the persistent “code validator” agent: you want a system prompt that can run for days in a multi‑agent setup, validating code diffs, patches, or generated snippets. Think in terms of roles, layers, guardrails, and metrics.[1][6][2]

### A. Role, scope, and “do & don’t”

You must lock the validator into a narrow role:

> You are a **strict code validation agent**, not a general code generator.  
>  
> Your primary responsibilities:
> - Validate code changes and generated code against explicit criteria (correctness, safety, style, performance, security).  
> - Identify issues, explain why they matter, and recommend specific fixes.  
> - Refuse to approve changes when you cannot reasonably validate them (missing context, ambiguous requirements).

Include hard “don’ts”:

> You must **not**:
> - Silently rewrite large portions of the codebase beyond the change under review.  
> - Introduce new dependencies or architectural patterns unless explicitly requested.  
> - Claim validation for behavior you cannot assess with the given information (e.g., external APIs without mocks/specs).

This aligns with “clear role definition and scope” plus safety/authorization constraints.[2][1]

### B. Layered validation criteria

For robust validation, define layers:

1. **Mechanical / static**: syntax, types, imports, basic structure.
2. **Logical / behavioral**: correctness vs. requirements, edge cases.
3. **Safety / security**: obvious vulnerabilities, dangerous patterns.
4. **Style / maintainability**: readability, conventions.

System‑prompt fragment:

> When validating, proceed in the following layers:
> 1. Mechanical correctness: syntax, compilation, type checks, dependency resolution.  
> 2. Logical correctness: does the code implement the intended behavior? consider edge cases.  
> 3. Security and safety: input validation, error handling, resource management, secrets, injection risks.  
> 4. Style and maintainability: readability, naming, modularity, testability.  
>  
> For each layer, explicitly list your findings and clearly separate “must fix” from “nice to have”.

This matches “include explicit validation criteria” and “guardrails and fallbacks” in system prompt best practices.[6][1]

### C. Expected inputs and outputs

For persistence and tooling, make the input contract explicit:

> You will receive:
> - A description of the change or generated code (what/why).  
> - The code snippet(s) or diff.  
> - Optional: tests, config, or domain constraints.  
>  
> You must respond with:
> - `summary`: 2–4 sentences describing what the code does.  
> - `issues`: a list of issues, each with:
>   - `layer` (mechanical/logical/security/style).  
>   - `severity` (blocker/warning/info).  
>   - `location` (file/function/line range if available).  
>   - `description` and `fix` suggestion.  
> - `approval`: `approve` or `reject`, with a short justification.

If you’re wiring this into a local pipeline, you can ask for JSON:

> Respond in JSON with keys `summary`, `issues`, `approval`.

Structured outputs are recommended in agentic system prompt patterns and in code review best practices emphasizing actionable comments.[9][10][11][2]

### D. Guardrails, fallbacks, and “epistemic humility”

Robust validation requires the validator to admit when it **cannot** reliably validate:

> If you lack sufficient context to validate behavior (e.g., missing function definitions, unclear requirements, external dependency behavior), you must:
> - Explicitly state what context is missing.  
> - Mark issues as “speculative” when they depend on assumptions.  
> - Prefer `reject` with a request for more information over guessing.  

> If the code is partially visible (e.g., large diff, truncated file), treat missing parts as unknown and avoid approval based on incomplete views.

This follows guidance that system prompts should include explicit fallback behaviors for edge cases.[1][6]

### E. Robustness strategies for local use

For local models, robustness often comes from **prompt + workflow**, not prompt alone:

- Keep a **base system prompt** that sets role, scope, and validation layers.
- For each validation run:
  - Attach a short, explicit “validation spec” (what we care about: performance, security, correctness).
  - Tailor temperature / sampling for determinism (low temperature, maybe nucleus sampling).[7]
- Optionally run multiple validators (different models/prompts) and aggregate or compare results; this is becoming common in “evaluation frameworks.”[8][5]

***

## 3. Example: unified pattern you can adapt

Here’s a condensed template you could adapt for both skill review and code validation in local setups.

### Skill review harness (local LLM)

> System: You are a **skill safety and robustness reviewer** for local LLM agents.  
>  
> You review skill specification files (SKILL.md) that define how agents use tools (CLIs, APIs, etc.).  
>  
> Your goals:
> - Identify concrete failure modes in targeting, input handling, and tool usage.  
> - Detect missing, contradictory, or over‑specified instructions.  
> - Recommend specific, minimal edits to make the skill safer and more robust.  
>  
> Process:
> 1. Summarize the skill’s intent in 3–5 sentences.  
> 2. Simulate at least 6 inputs (typical, underspecified, adversarial) and walk through how the skill would process each, step by step.  
> 3. For each simulation, classify the outcome (acceptable / ambiguous / unsafe) and explain why.  
> 4. List findings under:
>    - `failure_modes`  
>    - `missing_constraints`  
>    - `contradictions`  
>    - `over_specification`  
> 5. Propose edits to the SKILL.md text, referencing sections or headings, striving for minimal changes that fix the issues.  
>  
> If you lack context, call it out explicitly instead of guessing.

User message: SKILL.md content.

### Code validator system prompt (for a persistent agent)

> System: You are a **code validation agent**.  
>  
> Role and scope:
> - Validate code changes and generated code against mechanical correctness, logical behavior, security/safety, and style/maintainability.  
> - Produce structured, actionable feedback.  
> - Refuse to approve code when context is insufficient.  
>  
> Validation layers:
> 1. Mechanical correctness (syntax, types, imports).  
> 2. Logical correctness (behavior vs. intent, edge cases).  
> 3. Security and safety (input validation, error handling, secrets, injection, resource use).  
> 4. Style and maintainability (readability, conventions, modularity, tests).  
>  
> Response format (JSON):
> ```json
> {
>   "summary": "…",
>   "issues": [
>     {
>       "layer": "mechanical|logical|security|style",
>       "severity": "blocker|warning|info",
>       "location": "file:line or description",
>       "description": "…",
>       "fix": "…"
>     }
>   ],
>   "approval": "approve|reject",
>   "notes": "…"
> }
> ```
>  
> Epistemic rules:
> - Mark issues as `speculative` in `notes` when they depend on assumptions.  
> - Prefer `reject` + request for more context over guessing.  
> - Do not rewrite large portions of the codebase beyond the change under review.

This follows common guidance on system prompt design for agentic systems (role definition, structured instructions, explicit tool/output contracts, safety/guardrails).[6][2][1]

***

If you share an example of your current local model setup (which runner, typical context window, and whether you’re routing multiple models), I can tailor these patterns into concrete prompt snippets and parameter sets you can drop into your orchestrator or skills.  

## Human

How to implement Few-Shot prompting for code generation tasks

Please tailor the patterns.  Also I'm willing to consider radical refactoring if there's long term ROI.

Are there repos with useful ideas we should be copying?

## Assistant

Yes — for **code generation** and **skill review** on local models, I’d move away from “one long universal prompt” and toward a small prompt architecture: a stable system prompt, a compact task contract, and a dynamically selected few-shot pack. That is the biggest long-term ROI change here, especially if you route multiple local models with different context limits and strengths.[1][2][3]

Your current agy skill is already thinking in the right direction because it separates prerequisites, pre-flight checks, execution rules, and failure triage, but it is still mostly a **policy document** for one skill rather than a reusable prompting framework for many code-generation tasks.[1]

## Tailored patterns

For your workflow, I’d split prompting into three layers:

| Layer | Purpose | What belongs there |
|---|---|---|
| System prompt | Stable behavior contract | Role, refusal rules, output schema, validation posture, epistemic rules. [4][3] |
| Task contract | Per-run instruction | Target files, requested change, constraints, success criteria, repo context. [5][6] |
| Few-shot pack | Pattern transfer | 1–3 highly similar examples showing the exact reasoning/output style you want. [7][8][9] |

That matters because few-shot examples are strongest when they teach a **task pattern**, not when they try to carry all the policy and safety burden themselves. If you put too much governance in the examples, local models often overfit the wording and under-generalize.[7][8]

For your use case, I’d define **three separate few-shot families** instead of one generic set:

- **Patch generation**: minimal diff, preserve surrounding structure, no opportunistic refactors.
- **Validation / critique**: identify defects, missing tests, edge cases, uncertainty.
- **Scaffold / greenfield generation**: produce a new module or file with explicit boundaries and tests.

That is a better fit than one blended “code generation” prompt because the failure modes differ a lot; your own agy skill already hints at this by distinguishing review/research from write-heavy flows and by requiring stricter handling for ambiguous targets.[1]

## Few-shot design

For code generation, the best few-shot examples are short, local, and strongly typed by task. I would use this structure for each example:

1. **Input context**: target file(s), brief repo purpose, request, constraints.
2. **Expected approach**: one compact “plan” section.
3. **Output**: patch, code block, or structured review.
4. **Validation note**: what was checked, and what remains uncertain.

A good example pair looks like this:

- Example A: “Add retry with exponential backoff to an existing fetch helper; preserve API; no new dependency.”
- Example B: “Refactor duplicate parsing logic into one helper; do not change public behavior.”
- Counterexample C: “Request is underspecified; ask for missing target or reject.”

That last one is important: few-shot prompting for coding should include at least one **refusal / clarification** example, otherwise the model learns that every prompt should end in code, even when the task is garbage. That directly addresses the same class of failure your agy skill is trying to prevent with TARGET/TASK/CONTEXT.[3][1]

A practical template for a local model:

```text
System:
You are a disciplined code generation agent.
Prefer the smallest correct change.
Do not guess missing requirements.
When target, behavior, or constraints are ambiguous, ask clarifying questions or refuse.
Output sections in order:
1. Understanding
2. Plan
3. Patch
4. Validation
5. Assumptions

User:
Task:
- Target: src/http/client.ts
- Change: add retry on 429 and 503
- Constraints: no new deps, preserve exported API, TypeScript only
- Success: existing callers unchanged; max 3 retries; jittered backoff

Example 1:
Input:
- Target: src/db/cache.ts
- Change: add TTL support
- Constraints: no API break, no deps
Output:
Understanding: ...
Plan: ...
Patch: ...
Validation: ...
Assumptions: ...

Example 2:
Input:
- Target: unclear
- Change: "fix the timeout bug"
Output:
Understanding: request is underspecified...
Plan: ask for target file and failing path...
Patch: none
Validation: cannot validate without target...
Assumptions: ...
```

The key optimization is not “more examples”; it is **better example selection**. Dynamic few-shot selection based on task similarity tends to outperform static packs when context is tight.[10][9]

## Refactor direction

If you’re open to radical refactoring, I think the long-term ROI play is this:

### 1. Convert skill prose into an executable prompt spec

Right now the agy skill is a readable instruction document with embedded policies, examples, and command rules. That is good for humans, but it is not ideal as a machine-optimized source of truth.[1]

I’d split it into:

- `policy.md`: invariant rules, e.g. target ambiguity, permission rules, verification.
- `templates/`: prompt skeletons for review, codegen, compare, red-team.
- `fewshot/`: small task-specific example packs.
- `checks.ts` or `checks.py`: deterministic preflight validators for TARGET/TASK/CONTEXT, path resolution, duplicate filename detection.
- `evals/`: regression cases for common failures.

That gives you a hybrid design: deterministic code enforces what can be checked mechanically, while prompts handle judgment. This is higher ROI than trying to encode everything in prompt text alone. The agy skill already has several rules that are deterministic enough to be code, such as “filename alone is insufficient when duplicates exist” and “absolute path required for file review.”[1]

### 2. Make preflight a structured object, not prose

Instead of “verify the prompt has all three elements,” generate a typed preflight record:

```json
{
  "target": {
    "status": "resolved|missing|ambiguous",
    "value": "C:/repo/src/foo.ts",
    "description": "HTTP retry helper"
  },
  "task": {
    "status": "present|missing|weak",
    "verb": "review"
  },
  "context": {
    "status": "sufficient|insufficient",
    "decision": "whether to adopt the skill changes",
    "success_criteria": ["catch false passes", "assess friction"]
  },
  "requires_confirmation": true
}
```

Then build prompts from that object. This is much more robust under “model momentum” than letting a model rewrite preflight logic in natural language each time. It also makes evals far easier.[3][1]

### 3. Separate “generator” and “critic” prompts

For local LLMs, combining generation and validation in one pass often causes self-approval. I’d use:

- **Generator prompt**: produce smallest working patch.
- **Critic/validator prompt**: inspect the patch against constraints and edge cases.
- Optional **arbiter prompt**: compare baseline vs patched output or choose between candidate patches.

This pattern has more overhead, but if you care about correctness over speed, it usually pays off. It also aligns with your preference for evidence-grounded, verification-oriented workflows.

### 4. Introduce task-class routing for few-shot packs

I would create a simple router that classifies tasks into buckets:

- bugfix-small
- refactor-local
- generate-new-module
- test-generation
- review-skill
- review-code
- compare-options

Each bucket gets:
- a task template,
- a validation rubric,
- a few-shot set,
- and max context budget.

That is much better than trying to make one skill handle every code task by prose alone.

## Repos worth copying

Yes — there are several places with ideas worth stealing, though not blindly.

### Aider

Aider’s docs emphasize adding only the relevant files, limiting context, and using a repository map so the model sees structure without loading the whole repo. That is directly useful for local code-generation and review workflows, especially under 4K–8K context limits.[5][11][6]

The main ideas worth copying from Aider are:

- **Repo map / compressed codebase summary** instead of full-repo stuffing.[6]
- **Explicit file targeting**: only add the files that need to be changed.[5]
- **Ignore mechanisms / subtree mode** for context control.[11]

Those fit your environment extremely well. In fact, your agy skill’s insistence on clear targets and absolute paths is philosophically aligned with Aider’s “name the files explicitly” model.[5][1]

### Promptfoo

Promptfoo is worth copying for the **evaluation loop**, not for the prompts themselves. Their guides emphasize repeatable eval suites, multiple runs to measure variance, structured assertions, and checking the path taken when that matters. That is extremely relevant if you want to harden skills and code-validation prompts over time.[12][2][3]

Ideas worth stealing:

- Regression suites for prompt/skill behavior.[2][3]
- `--repeat 3` style repeated runs to detect instability.[3]
- Structured output assertions and semantic rubrics, not just string matching.[3]

For your setup, I’d absolutely build evals around:
- ambiguous target,
- weak task verb,
- missing success criteria,
- codegen with and without enough context,
- correct refusal behavior.

### Dynamic few-shot selection repos

The dynamic prompting repo is useful conceptually because it shows a pattern for selecting contextually close examples from a pool rather than hardcoding a single few-shot block. That is the right direction if you plan to route many task types across local models.[10]

I would not copy it verbatim without inspecting quality, but the **strategy** is solid:
- store curated examples with metadata,
- rank by task similarity,
- inject top 1–3 examples.

### OpenAI / Codex eval guidance

The eval guidance is useful because it frames coding-agent evals like integration tests: baseline first, assertions, repeated runs, cost/latency thresholds, and checking not only final answers but the process when path matters. That maps well to your “accuracy > agreement” and “inspect before editing” approach.[13][3]

## What I would actually build

Given your willingness to refactor, I’d build this:

1. **Skill compiler**
- Input: human-readable SKILL.md plus YAML/JSON metadata.
- Output: task-specific prompt templates, machine-readable checks, and eval fixtures.

2. **Few-shot library**
- Store examples as structured records:
  - task class,
  - language,
  - size,
  - difficulty,
  - requires refusal?,
  - expected output form.
- Retrieve by similarity and context budget.

3. **Two-pass local code agent**
- Pass 1: generate or revise code.
- Pass 2: validate mechanically and semantically against explicit rubric.
- Reject or escalate when uncertainty is high.

4. **Eval harness**
- Run regression tasks across your candidate local models.
- Track pass rate, refusal quality, verbosity, and variance over repeated runs.[2][3]

That is a bigger upfront build, but the long-term ROI is real if you are repeatedly reviewing skills, validating code, and routing across multiple providers/models.

## Specific changes for your agy-adjacent prompting

Based on the attached skill, I’d change these things:

- Move TARGET/TASK/CONTEXT from descriptive prose into a **structured preflight result** generated before the prompt is assembled.[1]
- Add an explicit **weak-but-present** state, especially for TASK and CONTEXT; many bad prompts technically contain all three elements but are still poor.[1]
- Add a **clarification example** to every few-shot pack so the model learns that “do not proceed” is a valid outcome.
- Split “review” from “write” into different prompt templates and different few-shot examples; the skill already treats write-heavy use as more dangerous, so the prompts should reflect that too.[1]
- Add evaluation fixtures for “gate passes but prompt still bad,” because that is the exact blind spot in the current design.

## Confidence and caveats

**FACT:** Your current SKILL.md already contains a solid skeleton for preflight, explicit targeting, verification, and post-run skepticism.[1]
**CONSENSUS:** Structured output contracts, eval harnesses, dynamic example selection, and constrained file targeting improve robustness for coding agents and local-model workflows.[6][2][5][3]
**SPECULATION, medium confidence:** For your environment, the best ROI is not more clever wording in SKILL.md but a refactor toward structured preflight + task-class templates + eval-backed few-shot retrieval.

Next concrete step: extract 10–20 real tasks from your history, label them by task class, and build a first few-shot library plus eval suite around them. After that, you’ll know whether the right improvement is better prompts, better routing, or more deterministic preflight code.

## Human

Let's abstract the useful ideas, and focus on the agy skill.  It's for review, analysis, design, coding (if we want), anything really we could want to use an external cli or model like agy.  So it needs to be adaptable and smart about how it invokes agy.

## Assistant

Yes — I would **reframe the agy skill from “a review skill with a pre-flight check” into “a conductor for external intelligence”**. That is the real abstraction your current SKILL.md is pointing toward, but it still encodes too much around one failure mode and one invocation style.[1]

The right design is: agy is a general external-model/tool delegation layer, while the conductor decides **whether to invoke, how to invoke, what prompt shape to use, how much friction to add, and how to verify the result afterward**. Your current skill already has the seeds of that model: conductor-owned prompt assembly, explicit target/task/context checks, and separate safety treatment for read-only vs write-heavy use.[1]

## Core abstraction

I’d define the skill’s job like this:

> `/agy` is a **delegation adapter** for external CLI/model execution.  
> Its purpose is not just “send prompt to agy,” but “select the right invocation pattern for the user’s intent while minimizing ambiguity, unnecessary friction, and unverified adoption of external output.”

That framing matters because it lets you support:

- review,
- analysis,
- design critique,
- coding,
- option comparison,
- red-teaming,
- research synthesis,

without pretending they are all the same prompt type. Right now the skill says agy can be used for “review, research, or analysis” and can also handle scaffolding if explicitly asked, but the logic is still mostly one-size-fits-all.[1]

## What to abstract

I’d keep these ideas from the current skill because they are genuinely valuable:

- **Grok stays the conductor.** External output is advisory unless explicitly elevated.[1]
- **Pre-flight before every invocation.** Good rule, but needs richer states than just “present/missing.”[1]
- **Absolute-path targeting for file work.** This is a hard-won operational invariant and should stay.[1]
- **Different safety posture for write-heavy execution.** Dedicated branch/worktree and diff review is the right direction.[1]
- **Never trust self-reported success.** Re-run tests/checks yourself.[1]

What I would change is the abstraction boundary. Right now the skill mixes together:

1. tool capability facts,
2. preflight policy,
3. prompt construction policy,
4. execution command rules,
5. result verification,
6. safety mode selection.

Those are all useful, but they should be modeled separately inside the skill.

## Better mental model

I’d split the agy skill into five decision stages.

### 1. Intent classification

Before prompting, the conductor should classify the request into an **invocation mode** such as:

| Mode | Purpose | Typical output |
|---|---|---|
| Review | Critique existing artifact | Findings, risks, suggestions |
| Analysis | Explain/compare/tradeoff | Structured reasoning |
| Design | Propose architecture or prompt/system design | Options and recommendation |
| Generate | Write code/content/spec | Patch, file, scaffold |
| Verify | Check correctness/claims/tests | Pass/fail + evidence |
| Red-team | Find failure modes or adversarial cases | Attack surfaces, failure scenarios |

This is the key upgrade. Your current skill treats TASK as “must contain a verb,” which is necessary but not enough. “Review,” “design,” and “write code” should not share the same prompt template or post-run verification standard.[1]

### 2. Target resolution

The current TARGET check is good, but too binary. I’d make target resolution produce one of:

- `none`
- `question-only`
- `single-artifact-resolved`
- `multi-artifact-resolved`
- `ambiguous`
- `dangerous-scope`

Examples:
- “What are the tradeoffs of X vs Y?” → `question-only`
- “Review SKILL.md” with one known file → `single-artifact-resolved`
- “Review the auth flow” with 8 candidate files → `ambiguous`
- “Rewrite the repo to use Zod everywhere” → `dangerous-scope`

That gives the conductor a real routing surface. Agy should not be invoked the same way for `question-only` vs `single-artifact-resolved` vs `dangerous-scope`. Your current skill already recognizes filename ambiguity and same-name collisions; this just generalizes it.[1]

### 3. Context sufficiency

This is where I’d most change the current design. CONTEXT should not just mean “some explanation exists.” It should capture whether agy can meaningfully succeed.

I’d define context fields like:

- artifact description,
- user goal / decision at stake,
- success criteria,
- constraints,
- trust posture,
- allowed scope.

For example:

```yaml
context:
  artifact: "Grok Build skill that wraps agy"
  goal: "decide whether the new pre-flight design prevents mis-target reviews"
  success_criteria:
    - identifies false-pass cases
    - critiques confirmation friction
    - suggests specific edits
  constraints:
    - review only
    - no file writes
  trust_posture: "advisory"
```

That is more robust than the current prose check “what is the artifact / why invoking / what does a good answer look like,” though those are still the right conceptual ingredients.[1]

### 4. Invocation policy

This is the heart of the skill and should be explicit. Once intent, target state, and context sufficiency are known, the conductor chooses an invocation policy.

Example policy table:

| Condition | Action |
|---|---|
| Question-only + clear task + sufficient context | Fire directly |
| Single artifact + all fields explicit from user | Fire directly |
| Missing or weak target/context filled by conductor | Show assembled prompt for approval |
| Ambiguous target | Refuse or ask clarification before invocation |
| Generate/write with broad scope | Require explicit confirmation + isolated worktree |
| High-risk verify/red-team request | Prefer more explicit prompt with success criteria and evidence request |

This is better than your current rule “if any element was filled in by the conductor, show prompt and ask permission.” That rule is useful, but crude. Some conductor-filled details are low-risk; some user-supplied prompts are still terrible and should not fire.[1]

## What “smart invocation” should mean

If the skill needs to be adaptable and smart, I think that means five things.

### Prompt template selection

Agy should not always get a generic prompt. Use different prompt skeletons by mode:

- **Review**: summarize artifact, ask for issues, edge cases, contradictions, recommended edits.
- **Analysis**: ask for tradeoff framing, assumptions, alternatives, and recommendation.
- **Design**: ask for proposed architectures/options, failure modes, migration path.
- **Generate**: ask for smallest correct change, constraints, output shape, tests/validation notes.
- **Verify**: ask for claims-to-check, evidence required, and explicit uncertainty.
- **Red-team**: ask for failure modes, adversarial examples, and exploitation path.

That is the biggest prompting improvement you can make.

### Friction proportional to risk

Instead of a universal permission rule, use friction tiers:

| Tier | Example | Friction |
|---|---|---|
| Low | Simple question or analysis | Fire directly |
| Medium | Review with conductor-filled details | Show assembled prompt |
| High | Writes, repo-wide changes, destructive commands | Explicit confirmation + isolated environment |

Your current safety section already distinguishes read-only from write-heavy use, so this is a natural extension.[1]

### Verification proportional to claim type

Not all outputs need the same verification:

- Opinion/design review: verify only if adopting concrete claims.
- Code review: re-check referenced files and tests.
- Code generation: inspect diff, run tests, validate constraints.
- Research/analysis: spot-check important factual claims.

Your current conductor rule “verify material claims against repo/tools before adopting as fact” is correct, but it should become mode-specific guidance.[1]

### Scope control

Smart invocation means narrowing scope before delegation:

- pass only the necessary files,
- use absolute paths,
- describe target in one line,
- say what not to do,
- keep the ask tight when the risk is high.

That is already present in the skill’s “what works” section and should remain a first-class principle.[1]

### Outcome handling

The skill should tell the conductor what to do with agy’s output:

- summarize key findings,
- separate evidence from interpretation,
- mark unverified claims,
- decide whether to escalate, retry, or discard.

Right now “return relevant stdout” is underspecified; it should say how to normalize agy output into conductor-usable results.[1]

## Concrete redesign

If I were rewriting the agy skill, I’d structure it like this:

### 1. Purpose

State that `/agy` is a **general external-model delegation skill** for external review, analysis, design, verification, and optional generation. The conductor owns targeting, prompting, safety, and verification.[1]

### 2. Mode selection

Add a section:

- Determine mode: `review | analysis | design | generate | verify | red-team`
- Determine risk tier: `low | medium | high`
- Determine target state: `question-only | resolved | ambiguous | dangerous-scope`

This replaces the current implicit reliance on a generic TASK verb list.[1]

### 3. Structured preflight

Replace “ALL THREE elements” with something like:

```text
Preflight:
- TARGET: resolved / ambiguous / missing / dangerous
- TASK MODE: review / analysis / design / generate / verify / red-team
- CONTEXT: sufficient / weak / missing
- RISK: low / medium / high
- PERMISSION: direct / show-assembled-prompt / explicit-confirmation-required
```

That is much stronger than the current binary gate.[1]

### 4. Prompt assembly by mode

Add prompt skeletons for each mode.

Example for review:

```text
Read [ABSOLUTE_PATHS].
Artifact: [ONE-LINE DESCRIPTION]
Task: Critically review for [FOCUS AREAS].
Decision context: [WHY THIS REVIEW MATTERS].
Good answer: [EXPECTED SHAPE].
Constraints: advisory only, no writes.
```

Example for generate:

```text
Read [ABSOLUTE_PATHS].
Task: Make the smallest correct change to achieve [GOAL].
Constraints: [NO NEW DEPS / PRESERVE API / FILE LIMITS / STYLE LIMITS].
Output: proposed patch or code, assumptions, and validation steps.
Do not broaden scope beyond the listed files.
```

Example for verify:

```text
Check whether [CLAIM / PATCH / DESIGN] is correct.
Artifacts: [ABSOLUTE_PATHS / TEST OUTPUT / DIFF]
Return:
1. claim-by-claim assessment
2. evidence from artifacts
3. uncertainties
4. overall confidence
```

### 5. Invocation rules

Keep the operational rules already proven in the skill:

- `--dangerously-skip-permissions` required in headless mode,
- `--print-timeout 10m` for substantial file reads,
- absolute paths for file reviews,
- `@file` when prompt is large.[1]

Those are exactly the kind of low-level truths the skill should preserve.

### 6. Post-run verification

Replace the generic “verify material claims” with mode-specific rules:

- Review/design: verify claims before adoption.
- Generate: inspect diff, run tests, check constraints.
- Verify/red-team: independently check at least the highest-severity findings.

### 7. Retry / fallback logic

Add explicit retry policy:

- If output is vague: retry once with narrower scope and stricter success criteria.
- If output targeted wrong artifact: retry only after re-resolving target.
- If output is long but shallow: switch to `@prompt.txt` and request prioritized findings.
- If output is still unreliable: do not recurse endlessly; report limitations.

## My recommendation

I would not optimize the current skill by adding more prose around TARGET/TASK/CONTEXT alone. I would **upgrade it into a routing-and-invocation skill** with:

- explicit mode selection,
- structured preflight states,
- risk-tiered confirmation,
- mode-specific prompt templates,
- mode-specific verification rules.

That is the durable abstraction for “anything really we could want to use an external CLI or model like agy” while preserving the very practical lessons your current skill already captured about ambiguity, path resolution, and verification.[1]

**Confidence:** high on the architectural direction; medium on exact section names and thresholds, because those depend on how Grok Build skills are parsed and how much structure you can safely add without hurting usability.[1]

The next best move is to draft a revised SKILL.md around that model, not just critique the current one.

## Human

Yes I agree.  Note you should consider it's use for research on the internet.  Also, is it possible to have it return how much quota is left when it responds for agy?

## Assistant

Yes on both counts: the agy skill should explicitly support **internet research** as a first-class mode, and quota visibility looks at least **partially possible**, but probably not as a clean, stable value returned by `agy -p` itself based on what I could verify.[1][2][3][4]

The clean design is to treat quota as **adjacent telemetry**, not part of the semantic answer. In other words: run agy, capture its answer, and optionally append a small “quota status” block if you have a reliable way to query it separately. That keeps the skill robust even if quota reporting is flaky or only available in interactive surfaces.[3][1]

## Research mode

Your current skill mentions “review, research, or analysis,” but the mechanics are still mostly optimized for file-based review and code/design tasks. It should explicitly add a **research mode** with different prompt assembly and verification rules.[4]

I’d model research as distinct from analysis:

| Mode | Primary input | Typical use |
|---|---|---|
| Analysis | User question plus existing local context | Compare options, explain tradeoffs, reason about architecture. |
| Research | User question requiring external/web information | Find current facts, docs, pricing, releases, policies, competing approaches. |

That matters because research prompts should tell agy things like:
- whether freshness matters,
- which sources are preferred,
- whether to prioritize primary docs over community discussion,
- what output shape you want: brief synthesis, source list, comparison table, recommendation.

That is consistent with your preference for evidence-grounded, newer primary sources and explicit uncertainty, and it fits naturally into the “conductor stays the conductor” rule in the current skill.[4]

A research prompt skeleton could be:

```text
Research the following question using current internet sources:
[QUESTION]

Goal:
[WHAT DECISION THIS SUPPORTS]

Source preferences:
- Prefer official docs, vendor pages, specs, policy pages, or authoritative primary sources
- Use community sources only to identify issues or edge cases, not as sole authority
- Call out uncertainty or conflicting information

Return:
1. Direct answer
2. Key findings
3. Source-quality notes
4. Uncertainties / open questions
```

That gives the skill a real internet-research pathway instead of treating all non-file tasks as generic Q&A.

## Quota reporting

### What seems supported

The strongest evidence I found is that Antigravity docs describe **quota / credits visibility inside the CLI environment**, including an AI Credits panel and a model quotas command, and they say the CLI can monitor active quota and credit consumption.[5][1]

That suggests quota data is **available somewhere in the product**, but not necessarily in a machine-friendly, non-interactive stdout form that your skill can reliably append after every `agy -p` invocation.[1][5]

### What seems unreliable

There is also evidence from public reports that:
- quota visibility has been a pain point,[6]
- `/stats` or quota-related commands have not worked reliably in some Antigravity CLI contexts,[2]
- `/usage` has reportedly shown incorrect 100% values for some users.[3]

So the safe answer is:

- **Possible in principle:** probably yes, if there is a working command or inspectable state source.
- **Reliable enough to bake into every response unconditionally:** uncertain, and likely no unless you verify a stable command in your environment.[2][1][3]

## How I’d design it

I would add a **best-effort telemetry layer** to the skill.

### Recommended behavior

After agy returns, the conductor may optionally append:

```text
Quota status (best effort):
- Model quota: [value if reliably available]
- Credits remaining: [value if reliably available]
- Refresh window: [value if reliably available]
- Status source: [interactive command / settings / external helper / unknown]
- Confidence: high / medium / low
```

This should only appear if the data was retrieved from a verified source. If not, the skill should say something like:

```text
Quota status: unavailable or unreliable in current environment
```

That is much better than pretending the quota number is always available.

### Skill-level rule

I’d add a rule like:

> Quota reporting is optional and best-effort.  
> Do not fabricate quota or usage numbers.  
> If a verified quota command or status source exists and works in the current session, append a short quota status block.  
> If quota telemetry is missing, broken, or known unreliable, omit it or explicitly mark it unavailable.

That matches the current skill’s “do not invent output” and “verify material claims” posture.[4]

## Possible implementation patterns

I’d think about three implementation paths, ordered by confidence.

### 1. Separate quota command in the skill

If you can identify a working CLI command in your environment for credits or model quotas, run it **separately** from the main `agy -p` request and parse the result. The docs suggest there is an AI Credits command and a Model Quotas command, but the exact non-interactive syntax was not confirmed in what I found.[1]

So the pattern would be:

- run agy task,
- run quota query,
- parse if successful,
- append telemetry block.

This is the cleanest if it works.

### 2. External helper tool

There is at least one community-built helper specifically intended to inspect Antigravity quota because native transparency was lacking. That is not authoritative, so I would not base the skill on it by default, but it does prove the pattern is feasible if you’re willing to depend on an external helper.[7]

This is acceptable as an optional extension, not as the core skill behavior.

### 3. Interactive-state scraping / settings inspection

The docs and tutorials imply that quota can be seen in the UI/statusline/settings area. That may mean there is some internal state or config surface you could inspect, but this is more brittle and version-sensitive.[8][1]

I would avoid this unless you verify the on-disk or command-line interface directly.

## Recommended agy skill upgrade

I’d now define the agy skill as supporting these modes:

| Mode | Uses internet? | Writes? | Verification style |
|---|---|---|---|
| Review | Usually no | Optional | Re-check files, claims, diffs. |
| Analysis | Sometimes | No | Verify key local claims before adopting. |
| Research | Yes | No | Check source quality, freshness, conflicts. |
| Design | Sometimes | Optional | Validate assumptions against repo/docs. |
| Generate | Sometimes | Yes | Diff review, tests, constraint checks. |
| Verify | Sometimes | Optional | Independent checks required. |
| Red-team | Sometimes | Optional | Reproduce or inspect highest-risk findings. |

And add this operational rule:

> If the mode is `research`, the conductor must specify whether current internet information is required, what source types are preferred, and how to handle conflicting or stale sources.

That is the missing abstraction for internet use.

## Bottom-line answer

For **internet research**, yes: I would make it a first-class agy mode with its own prompt template, source-quality expectations, and output shape. Your current skill is conceptually close, but still too review-centric.[4]

For **quota left when it responds**, maybe — but only as a **best-effort secondary status block**, not as a guaranteed field in every agy response. The available documentation suggests quota/credits can be viewed somewhere in Antigravity, but public reports also suggest CLI quota reporting has been unreliable in some cases, so you should treat it as optional telemetry that must be verified in your actual environment before baking it into the skill contract.[2][3][1]

The next practical step is to add two new sections to the skill:
- `Mode selection` with `research` as a first-class mode.
- `Quota telemetry` with “best effort, never fabricate, append only if verified.”

## Human

show me the final copy paste prompt back to the LLM.  Include all the updates you think are useful.  use modular structure in the prompt if you want.  Use code (preferably not inline) with the skill if you want.  Act as a thought partner and add everything you think is a good idea.

## Assistant

Here’s a **single, copy‑pasteable prompt** you can send to an LLM (Grok, agy, or another conductor agent) to critically review and help redesign the agy skill, including all the abstractions and research/quota ideas we discussed. It’s structured and modular so you can trim sections if needed.[1]

***

```text
You are my thought partner and architecture reviewer for a Grok Build skill.

TARGET:
- The skill file at:
  C:/Users/brsth/.grok/skills/agy/SKILL.md

BACKGROUND:
- This skill defines the `/agy` command, which wraps the Google Antigravity CLI (agy / Gemini).
- Current intent: “Run agy non-interactively for a second opinion, code review, research, or analysis.”
- The skill was recently updated to add a Pre-Flight Check (TARGET/TASK/CONTEXT) after a failure where the conductor sent an underspecified prompt and agy reviewed the wrong file. [file:31]
- Agy is advisory by default; the conductor (Grok) prepares prompts, runs agy, and verifies the result before trusting it. [file:31]

HIGH-LEVEL GOAL:
- Evolve this from “a review skill with a pre-flight gate” into a **general delegation adapter** for external CLI/model usage.
- It should:
  - Support multiple modes (review, analysis, design, coding, verification, red-teaming, and internet research).
  - Be smart about how it invokes agy: choosing prompt templates, scope, friction, and verification behavior based on intent and risk.
  - Maintain strong protections against mis-targeting, underspecified prompts, and unverified adoption.
  - Optionally append a best-effort “quota status” summary when reliable information is available from Antigravity/agy quota/credits interfaces (without fabricating values). [web:52][web:53][web:58]

CONSTRAINTS AND ASSUMPTIONS:
- Environment: Windows 11, Grok Build skills, Antigravity CLI (agy) on PATH, Gemini models managed by Antigravity.
- Verified CLI behavior today:
  - `agy` reads the current working directory (CWD) as project/repo root. [file:31]
  - Headless runs hang or fail without `--dangerously-skip-permissions`. [file:31]
  - Multi-file reviews often need `--print-timeout 10m`. [file:31]
  - JSON/structured machine output from `-p` should not be assumed; treat stdout as text blob. [file:31]
- Antigravity has quota/credits concepts and some usage interfaces; public reports indicate quota transparency and CLI usage commands have been unreliable in some cases, so quota telemetry MUST be treated as best-effort and never fabricated. [web:52][web:53][web:58]
- The user (me) cares more about correctness, safety, and epistemic clarity than raw speed.

TASK:
Critically review SKILL.md and propose a redesigned skill spec that turns `/agy` into a robust external delegation adapter.

You must produce:
1. A clear summary of what the current skill does well and where it fails or under-specifies behavior.
2. A proposed modular structure for the new skill (sections, responsibilities, and any supporting code).
3. Concrete text for a revised SKILL.md (you can assume Markdown) that:
   - Defines modes, pre-flight structures, invocation policies, safety rules, and post-run verification.
   - Is practical to use in Grok Build for real workflows (code review, design, research, etc.).
4. Optional but encouraged: pseudo-code or TypeScript/Python snippets that illustrate deterministic pre-flight checks or routing logic.

FOCUS AREAS (MANDATORY):

A. MODE SELECTION (INTENT CLASSIFICATION)
- Read the current SKILL.md and:
  - Enumerate the implicit usage modes it supports today (e.g., review, research, analysis, limited scaffolding). [file:31]
  - Define an explicit mode taxonomy that includes at least:
    - review
    - analysis
    - design
    - generate (code/content)
    - verify (claims/tests)
    - red-team (failure-mode discovery)
    - research (internet data, docs, pricing, specs, policies)
  - For each mode, specify:
    - Typical inputs (files, questions, URLs, repo state).
    - Typical outputs (findings, patches, options, etc.).
    - Risk level (low/medium/high).
    - Required safety posture (read-only vs write-heavy, confirmation requirements, verification strategies).

B. STRUCTURED PRE-FLIGHT CHECK (BEYOND TARGET/TASK/CONTEXT)
- The current skill defines a Pre-Flight Check that ensures TARGET, TASK, and CONTEXT are present and has rules like:
  - File review requires absolute paths in the prompt.
  - Vague references (“the skill”, “this code”) must be resolved by the conductor to a specific file + one-line description.
  - A bare noun is not a TASK; a verb like “review, critique, compare, design, analyze, verify, red-team” is required. [file:31]
- Critique this design and upgrade it to a **structured preflight object** with fields such as:
  - `target_status`: none / question-only / single-artifact-resolved / multi-artifact-resolved / ambiguous / dangerous-scope.
  - `task_mode`: review / analysis / design / generate / verify / red-team / research.
  - `context_status`: sufficient / weak / missing.
  - `risk_level`: low / medium / high.
  - `requires_confirmation`: direct / show-assembled-prompt / explicit-confirmation.
- For each state and combination, define what the conductor must do:
  - When to fire directly.
  - When to show the assembled prompt and ask permission.
  - When to refuse or ask for clarification instead of firing.
- Provide concrete examples of prompts that:
  - Pass preflight and are safe.
  - Pass preflight but are still garbage (e.g., weak context, over-broad tasks).
  - Fail preflight and must be rejected or clarified.

C. PROMPT TEMPLATES BY MODE
- Design prompt skeletons for each mode that the conductor can fill in.
- They should:
  - Use absolute paths for file work and one-line artifact descriptions. [file:31]
  - Specify why we’re invoking agy (what decision depends on the answer).
  - Define what a good answer looks like (shape, level of detail, examples).
  - Constrain scope when risk is high (e.g., generate mode should prefer “smallest correct change”).
- Required templates:
  - REVIEW (e.g., “Read [paths], summarize intent, list issues, risks, missing constraints, recommended edits.”)
  - ANALYSIS (e.g., “Explain tradeoffs between options X and Y, assumptions, and recommendation.”)
  - DESIGN (e.g., “Propose architectures, failure modes, migration path.”)
  - GENERATE (e.g., “Make the smallest correct change to achieve [goal], with constraints and validation steps.”)
  - VERIFY (e.g., “Check whether [claim/patch] is correct; provide evidence and uncertainty.”)
  - RED-TEAM (e.g., “Find failure modes, adversarial inputs, exploitation paths for [system/skill].”)
  - RESEARCH (e.g., “Use current internet sources; prefer official docs/specs; handle conflicting information, call out uncertainty.”)

D. INTERNET RESEARCH MODE (FIRST-CLASS)
- Treat research as a first-class mode:
  - Identify how research prompts differ from pure analysis.
  - Specify expectations for source selection:
    - Prefer newest authoritative primary sources when possible (docs, spec pages, help centers, laws, official announcements).
    - Use blogs/community posts for edge cases and practical pitfalls, but not as sole authority.
    - Clearly mark uncertainty and conflicting reports.
  - Design a research prompt template that:
    - States the question and decision context.
    - Defines what sources are preferred.
    - Requests a structured output: answer, key findings, source-quality notes, and remaining uncertainties.

E. EXECUTION DIRECTIVES AND SAFETY (CLI INVOCATION)
- Preserve and refine execution rules already in SKILL.md:
  - Use `--dangerously-skip-permissions` for headless runs to avoid hangs. [file:31]
  - Use `--print-timeout 10m` for multi-file or deep reviews. [file:31]
  - Use `-p` / `--print` for non-interactive single-shot runs. [file:31]
  - Always pass file paths as absolute paths and name them explicitly in the prompt. [file:31]
- Upgrade the “What works / What does not work” tables by:
  - Strengthening rules against filename-only targeting, `--add-dir` misuse, and assuming structured JSON output.
  - Adding mode-aware scope control (e.g., guard against repo-wide rewrites in GENERATE mode without explicit scope).
- For write-heavy operations:
  - Keep the dedicated branch/worktree rule.
  - Define a minimal pipeline: run agy → inspect diff → run tests → require human review → never auto-merge.

F. POST-RUN VERIFICATION AND UNCERTAINTY
- Refine the conductor rules around verifying agy output:
  - Map verification behavior to mode:
    - REVIEW/DESIGN: verify claims you want to adopt.
    - GENERATE: inspect diff, run tests, validate constraints.
    - RESEARCH/ANALYSIS: spot-check key sources; note outdated/stale information.
    - VERIFY/RED-TEAM: independently reproduce or inspect highest-risk findings.
  - Encode epistemic behavior:
    - When context is insufficient or output seems inconsistent, prefer “reject or ask for more info” over guessing.
    - Explicitly mark speculative or assumption-based concerns.
- Suggest output normalization strategies for the conductor:
  - Structured sections: summary, findings, evidence, assumptions, recommendations.
  - Optional JSON wrapping when feasible.

G. QUOTA / USAGE TELEMETRY (BEST-EFFORT)
- Based on Antigravity docs and known behavior:
  - Acknowledge that AI Credits / quota can be inspected somewhere (settings panel, CLI commands), but CLI-level usage commands (e.g., `/stats`, `/usage`) have been reported as unreliable. [web:52][web:53][web:58]
- Design a **best-effort quota telemetry policy**:
  - If a reliable CLI or API status source exists and is verified in this environment, the conductor MAY:
    - Query quota/credits after running agy.
    - Parse usage/remaining quota.
    - Append a short “Quota status” block to the user-facing result.
  - If quota telemetry is missing, broken, or known unreliable:
    - Do NOT fabricate numbers.
    - Either omit quota or explicitly say “Quota status unavailable or unreliable in current environment.”
- Propose how to represent quota status in output:
  - Example:
    - Quota status (best effort):
      - Credits remaining: …
      - Model quota: …
      - Refresh window: …
      - Source: [CLI command / settings page / helper tool]
      - Confidence: high / medium / low

H. FAILURE MODES AND RETRY POLICY
- Using the Failure triage table in SKILL.md as a starting point (agy not found, hangs, timeouts, wrong file, empty output), define:
  - Additional failure modes tied to PRE-FLIGHT and mode selection:
    - Preflight passes but target is still ambiguous.
    - Mode misclassified (e.g., generate used instead of verify).
    - Research mode returns stale or conflicting info.
  - A retry strategy:
    - When to retry with narrower scope or better context.
    - When to re-resolve TARGET/TASK/CONTEXT instead of retrying.
    - When to stop and escalate to the user as “we hit limits; here’s what failed.”

I. PROPOSED NEW SKILL STRUCTURE (FINAL DELIVERABLE)
- After criticism and design thinking, output:
  1. A revised SKILL.md (Markdown) that:
     - Keeps the good parts of the current skill (clear prerequisites, absolute-path rules, execution flags, safety distinctions).
     - Adds explicit modes, structured preflight, prompt templates, mode-aware safety rules, research handling, and quota telemetry policy.
  2. Optional supporting code (pseudo-code, TypeScript, or Python) that implements:
     - Preflight classification (`target_status`, `task_mode`, `context_status`, `risk_level`, `requires_confirmation`).
     - Mode routing to prompt templates.
     - Basic failure triage and retry decisions.
  3. A short “migration note” for me explaining how to port from the old skill to the new one and where to plug in real quota commands, if we find a reliable approach.

STYLE AND PRIORITIES:
- Be explicit and pragmatic. Keep the skill readable to humans, but favor precise behavior over vague prose.
- Treat premises as questionable; if any of my assumptions look wrong, call them out and suggest alternatives.
- Always surface your own uncertainty explicitly when you’re speculating.
- Prefer TypeScript/Node or Python examples for code snippets.
- Aim for long-term maintainability: modular skill sections, clear responsibilities, and separation between human-readable policy and machine-enforced checks.

Now:
1. Summarize the current agy skill and its main strengths/weaknesses.
2. Design and present the upgraded, modular skill spec and concrete SKILL.md text that satisfies the requirements above.
3. Where useful, include small code snippets to illustrate preflight classification and routing logic.
```

***

This prompt gives the LLM everything it needs: target file, context, goals, explicit focus areas (including research and quota), and a strong expectation of structured, actionable output. It also preserves your “accuracy > agreement, epistemic clarity, and minimal but powerful abstractions” preferences while still being usable as a drop‑in “please help me redesign this skill” command.[2][3][4][1]

## Human

I forget, did you already talk about popular and maintained repos that can provide useful ideas?

## Assistant

Yes, we already touched some, but it’s worth making the list explicit and a bit more opinionated for your use case.

## Repos and projects worth copying ideas from

### 1. Aider (AI pair programming in your terminal)

- Repo: [aider-ai/aider](https://github.com/aider-ai/aider)[1]
- Why it’s relevant:
  - Strong emphasis on **explicit file targeting**: only add the files you intend to edit, and use repo maps and ignore files to control scope.[2][3]
  - Repo map: builds a concise map of classes/functions/signatures so the model sees structure without loading the whole repo. This is a great pattern for “external delegation with constrained context” and fits directly with your agy skill’s absolute-path and pre-flight targeting approach.[2]
  - Git integration and diff workflows: commit each change, inspect diffs, rollback easily. That lines up with your dedicated branch/worktree pattern for write-heavy agy usage.[4][5]

Useful ideas to copy for agy:

- A “repo map” concept for code-focused `/agy` calls: instead of sending lots of raw code, generate a concise structural summary and let agy ask for specific files if needed.
- Strict file selection and subtree-only modes; your skill already says “filename alone is insufficient, use absolute paths,” but you could add similar ignore/subtree behaviors as explicit guidance.[3][5]
- Automatic diff-based verification pipelines for write-heavy operations.

### 2. Promptfoo (LLM evals & red-teaming)

- Repo: [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)[6]
- Why it’s relevant:
  - Designed for **systematic evaluation of prompts, agents, and RAGs**, with CI/GitHub Action integrations for “before vs after” prompt changes.[7][8]
  - Has specific guidance for **evaluating coding agents**, including multi-run variance checks and structured assertions.[9]

Useful ideas to copy for agy:

- Treat your agy skill as a **prompted agent** and build eval suites around:
  - mis-targeting,
  - underspecified tasks,
  - research freshness/authority,
  - write-heavy safety.
- Use before/after prompt tests whenever you change SKILL.md: run a small set of canonical tasks and see if behavior improved or regressed.[8][9]

### 3. Dynamic few‑shot prompting packages

- Repo: [ElmiraGhorbani/dynamic_prompting](https://github.com/ElmiraGhorbani/dynamic_prompting)[10]
- Why it’s relevant:
  - Implements **dynamic few-shot selection** from a small example knowledge base based on semantic similarity, akin to RAG but for prompts.[11][10]
- Related patterns: LangChain example selectors and SemFew-style approaches in newer work.[12][13]

Useful ideas to copy for agy:

- Maintain a small library of **task-specific examples** (review, analysis, generate, verify, red-team, research) and dynamically inject the most similar ones when building agy prompts.
- Let pre-flight classification pick which example pack to pull from (e.g., research vs code review) instead of having one static few-shot section.

### 4. Few-shot learning with language models (meta-patterns)

- Repo: [tonyzhaozh/few-shot-learning](https://github.com/tonyzhaozh/few-shot-learning)[14]
- Why it’s relevant:
  - Implements classic GPT‑style **in-context learning experiments**, which can inform how many examples and what structure tend to work well.

Useful ideas to copy for agy:

- Use **short, strongly typed examples** rather than long, mixed-mode ones.
- Include at least one refusal/clarification example so agy learns that “do not proceed” is a valid move when pre-flight fails.

### 5. System prompt pattern collections

- Repo: [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts)[15]
- Why it’s relevant:
  - Curated system prompts for many agentic tools (ChatGPT, Claude, Grok, etc.), plus pattern-level commentary on role definition, tool usage, structured outputs, safety constraints.[15]

Useful ideas to copy for agy:

- Clear role/scope separation: “delegation adapter” vs “code generator.”
- Structured response formats (sections or JSON) for agy outputs that the conductor can reliably post-process.
- Explicit safety and fallback rules embedded in the skill (e.g., when to refuse, when to ask for more context) instead of only relying on “be careful” prose.[5][15]

## Short answer to your question

Yes, we already discussed repos and projects like **Aider**, **Promptfoo**, dynamic few‑shot prompting libraries, and system‑prompt pattern collections, and they are still the main maintained sources I’d mine for ideas for your agy skill.[1][6][10][14][9][2][15]

If you want, I can next sketch exactly how to plug “repo map + dynamic few-shot selection + prompt evals” into the redesigned SKILL.md so it’s not just conceptual but something you could implement over a weekend in your Grok Build setup.

## Human

yes please

## Assistant

Here’s how I’d wire **repo map + dynamic few‑shot + evals** directly into a redesigned `/agy` skill, in a way you could realistically build over a weekend in your Grok Build environment. I’ll keep it concrete and code‑lean, not just conceptual.[1][2][3][4]

***

## 1. Repo map integration for `/agy` (code-focused modes)

Goal: give agy a **compact structural view of the repo** instead of raw bulk code, so it can reason better about where to look and what to change, without blowing up context. This is the Aider pattern.[2][5][6]

### Concept

- When mode ∈ {review, generate, verify, red-team} and **TARGET is “code in repo”**, run a repo‑mapping tool before constructing the agy prompt:
  - Could be Aider’s `--show-repo-map` if you have it,[7]
  - or a dedicated tool like RepoMap,[8]
  - or a small custom mapper using ctags or Tree-sitter.[5][6]
- Include **only the map** plus the specific files in the agy prompt, not the whole repo body.

### agy skill additions

Add a new section to SKILL.md:

> ### Repository map (code-aware context)
>
> When the TARGET is “code in a git repo” and the mode is `review`, `generate`, `verify`, or `red-team`:
> - Before building the agy prompt, generate a **repo map**:
>   - For each relevant file: list key symbols (classes, functions, types) and their call signatures.
>   - Include only critical lines (definitions and docstrings), not full bodies.[6][2][5]
> - Pass the repo map + absolute paths for specific files into the agy prompt instead of sending large bodies by default.
> - If the repo is huge, restrict the map to:
>   - The subtree containing the TARGET files.
>   - Files with direct dependencies on those files (imports/calls).
> - If repo mapping fails, fall back to explicit absolute paths and a short textual description of relationships.

Example fragment in the agy prompt:

```text
Repository map (partial):
- src/http/client.ts
  - fetchWithRetry(url: string, opts: RequestOptions): Promise<Response>
- src/auth/session.ts
  - createSession(userId: string): Session
  - getSession(token: string): Session | null
- src/config/index.ts
  - getConfig(): Config

Target files:
- C:/repo/src/http/client.ts
- C:/repo/src/auth/session.ts
```

This preserves your absolute‑path invariants while scaling better to real-world repos.[4][2][6]

***

## 2. Dynamic few‑shot selection for `/agy` modes

Goal: avoid one static set of examples and instead pick **mode‑specific, task‑similar examples** per request. This is the dynamic few‑shot prompting pattern.[3][9][10]

### Concept

- Maintain an **examples library** in a small JSON/YAML file per skill:

```json
[
  {
    "id": "review-skill-preflight",
    "mode": "review",
    "target_type": "skill-file",
    "input": "Critically review SKILL.md for mis-targeting failures",
    "output": "Structured findings about TARGET/TASK/CONTEXT, examples of bad prompts, suggested edits"
  },
  {
    "id": "generate-small-patch",
    "mode": "generate",
    "target_type": "code-file",
    "input": "Add retry to HTTP client without changing its public API",
    "output": "Small patch, plan, validation steps, assumptions"
  },
  {
    "id": "research-docs",
    "mode": "research",
    "target_type": "question-only",
    "input": "Find current Antigravity quota docs and summarize key limits",
    "output": "Answer, primary sources, conflicts, uncertainties"
  },
  {
    "id": "refusal-underspecified",
    "mode": "any",
    "target_type": "ambiguous",
    "input": "Fix the timeout bug",
    "output": "Explanation that TARGET is ambiguous; request for file path and scenario; no changes"
  }
]
```

- When pre-flight classifies a request, pick 1–3 examples with the same `mode` and similar `target_type` and optionally embed the input texts for semantic similarity (if you have a local embedder).[3]

### agy skill additions

Add a section:

> ### Few-shot examples (mode-aware)
>
> The conductor maintains an external examples file (JSON or YAML) with:
> - `mode`: review, analysis, design, generate, verify, red-team, research
> - `target_type`: skill-file, code-file, repo, question-only, ambiguous, dangerous-scope
> - `input`: a concise task example
> - `output`: a high-quality response example
>
> When building an agy prompt:
> - Use pre-flight classification to filter examples by `mode` and `target_type`.
> - Optionally use semantic similarity over `input` strings to pick the closest 1–3 examples.[10][3]
> - Inject the chosen examples as “assistant/user” turns before the actual user request.
> - Always include at least one example where the agent refuses or asks for clarification when TARGET/CONTEXT are insufficient.

Because you’re routing multiple local models, you can vary the examples per model or per risk tier.[9][3]

***

## 3. Prompt evals for `/agy` via Promptfoo

Goal: **lock in behavior** of the agy skill and detect regressions whenever you change SKILL.md or your routing logic. This is exactly what Promptfoo is built for.[11][12][13][14]

### Concept

- Define a small set of **canonical scenarios** for `/agy`:
  - Mis-targeting scenarios (two SKILL.md files, ambiguous “the skill”).
  - Underspecified tasks (“fix the timeout bug”).
  - Write-heavy operations (repo-wide refactor request).
  - Internet research tasks (quota docs, pricing, API limits).
  - Safety-critical verify/red-team tasks.
- For each scenario, encode:
  - the raw user command (`/agy …`),
  - expected pre-flight classification,
  - expected invocation mode,
  - expected friction level,
  - expected agy prompt summary,
  - expected response shape (not exact text).

- Use Promptfoo to:
  - run the conductor+agy pipeline (or an echo provider of the prompt text),[14]
  - apply rubrics: “did the skill refuse when TARGET ambiguous?”, “did it show assembled prompt when filling in context?”, “did it pick research mode for internet-heavy questions?”, etc.[12][1]

### agy skill additions

Add a short “Evals” section:

> ### Evals (Promptfoo or similar)
>
> We maintain a small eval suite for the `/agy` skill, with scenarios that cover:
> - Mis-targeting (multiple candidates, vague references).
> - TASK under-specification (no verb, or overly broad verbs).
> - Ambiguous or dangerous scopes (“rewrite the repo”).
> - Research tasks that require internet sources and fresh docs.
> - Write-heavy operations vs read-only review.[4]
>
> For each scenario:
> - Check that pre-flight classifies `target_status`, `task_mode`, `context_status`, `risk_level`, and `requires_confirmation` correctly.
> - Check that the assembled agy prompt uses the right mode template and scope.
> - Check that the friction level matches risk (direct vs show-assembled vs explicit confirmation).
>
> Evals are run via a CLI framework (e.g. Promptfoo) whenever SKILL.md or routing code changes.[13][11][12][14]

In practice, you’d likely stub the actual agy call and just evaluate prompt assembly and pre-flight behavior most of the time, only occasionally running full end-to-end tests for real outputs.[12][14]

***

## 4. How to plug this into the redesigned SKILL.md

Putting it together, the redesigned SKILL.md would have:

1. **Overview**: high-level purpose and modes (`review, analysis, design, generate, verify, red-team, research`).[4]
2. **Prereqs**: current verified flags and environment notes (`agy` on PATH, `--dangerously-skip-permissions`, `--print-timeout`).[4]
3. **Pre-flight**: structured classification for `target_status`, `task_mode`, `context_status`, `risk_level`, `requires_confirmation`.
4. **Repo map integration**: how and when to generate and inject a map.[2][5][6]
5. **Few-shot integration**: how to select examples by mode/target, with refusal examples included.[10][3]
6. **Prompt templates by mode**: concrete skeletons for each mode.
7. **Execution directives**: how to actually call agy for each mode (including internet research notes).
8. **Verification & safety**: mode-aware verification and write-heavy safety rules.[4]
9. **Quota telemetry (best-effort)**: optional “quota status” block, only when reliable telemetry is available.[15][16][17]
10. **Evals**: pointers to the external eval suite and expectations.[1][13][12]

None of this requires full-blown refactoring of your runtime; you can start with:

- A small script to generate a repo map (using ctags or a simple AST walker),[5][6]
- A JSON file of examples plus a simple similarity heuristic (or manual mode-based selection),
- A prompt assembly function that takes pre-flight output + map + examples and builds the final agy prompt,
- A minimal Promptfoo eval config that shells out to your conductor script or uses an echo provider to inspect prompts.[14][1]

***

If you want, next step could be: I draft a concrete **pre-flight function signature** and a **TypeScript/Node pseudo‑implementation** that runs in your Grok Build environment, including where repo map generation and example selection plug in.
