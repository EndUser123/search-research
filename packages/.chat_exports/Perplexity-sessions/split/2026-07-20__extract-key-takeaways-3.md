---
title: "Extract key takeaways"
date: "2026-07-20"
mode: "COPILOT"
uuid: "7e65291c-922f-46b0-a68a-bae2f96c5186"
entry_count: 2
---

## Human

Extract key takeaways

## Assistant

Anthropic’s Fable 5 best‑practice doc + Nate’s experience condense down to six prompting habits and one routing caveat that materially change how you should use Fable (and, mostly, any frontier model) for real work.[1]

## Cost, availability, and role of Fable 5

- Fable 5 is currently Anthropic’s strongest model and feels noticeably better at understanding and executing complex instructions than prior models.[1]
- It is expensive: about \( \$10 \) per million input tokens and \( \$50 \) per million output tokens, roughly double Opus, and only partly free during a short promotional window.[1]
- You realistically should only reach for Fable on the hardest 5–15% of tasks; using it for everything is overkill and will burn usage credits quickly.[1]

## Habit 1 – Always give the “why”

- Fable 5 performs better when it understands your intent and the bigger task around a request; Anthropic explicitly calls out that it “does better when it understands your intent.”[1]
- Instead of bare directives (“Write me an email about the delay”), wrap the task in context: who it’s for, what they need, and how it fits into a larger project so the model can pull and connect the right information.[1]

**Actionable takeaway:** In your system and task prompts, add 1–3 sentences explaining purpose, audience, and success criteria before you ask for the output.

## Habit 2 – Use explicit negative prompting

- Nate highlights that Anthropic’s own Fable 5 docs repeatedly instruct the model what *not* to do (“don’t add features”, “don’t overcomplicate”, “don’t do X”), which is essentially structured negative prompting.[1]
- Because the model is trained to predict likely next words, it will often add flourishes or actions you didn’t ask for unless you explicitly fence it in with “do not” instructions.[1]

**Actionable takeaway:** For each important task, include a short line like: “Do not send emails, delete data, or make API calls; only produce a written assessment.” This is especially useful for skills, tools, and agents that act on real systems.[1]

## Habit 3 – Let it act once it has “enough”

- Anthropic warns that long, high‑effort queries on hard tasks can run for minutes gathering context and planning, so “when you have enough information to act, then act” is a core guideline.[1]
- Nate has largely stopped relying on Claude Code’s built‑in “plan mode” and instead uses his own pattern: a short planning phase followed by explicit permission to act once the model has sufficient information.[1]

**Actionable takeaway:** Replace “research everything and fully plan before doing anything” with instructions like: “Do a brief plan, then start implementing once you have enough detail to make progress; don’t over‑plan.”

## Habit 4 – Match effort levels to the task

- Anthropic provides multiple “effort” settings (low, medium, high, extra high) and recommends high as the default for most tasks, extra high for capability‑sensitive work, and medium/low for routine work.[1]
- Nate notes that Fable 5 on low effort can be similar to Opus 4.8 on extra‑high/max, but cheaper, so picking the right effort level per task is a major cost and performance lever.[1]

**Actionable takeaway:**  
- Use medium/low for straightforward coding, CRUD, and routine text work.  
- Use high for non‑trivial reasoning, multi‑step plans, or complex refactors.  
- Reserve extra high for deeply complex reasoning, multi‑agent orchestration, or safety‑critical changes.

## Habit 5 – Make it prove its work

- A key pattern from the video: never accept “I’m done” at face value; require the model to point to evidence that the work is complete and correct.[1]
- Good prompts: “Before you say this is done, show the test results, logs, or concrete outputs that prove it. Only report work you can back with evidence; if something isn’t verified, say so plainly instead of guessing.”[1]

**Actionable takeaway:** Bake verification loops into system prompts, skills, and agents (rather than manually appending them each time) so every workflow includes self‑checks before handing results back to you.

## Habit 6 – Say less, not more (but keep intent)

- Fable 5 is strong enough that short, focused instructions in a well‑instrumented environment (tools, context, skills) can steer it just as well as long, rule‑heavy prompts.[1]
- This is not a contradiction with Habit 1: you should still give the “why” and core context, but avoid bloating prompts with long lists of micro‑rules that could be summarized into a few behavioural principles.[1]

**Actionable takeaway:** Replace long numbered rule lists with small guiding phrases like “Lead with the outcome, keep it simple, verify your work before reporting.” This reduces token use and makes your system files easier to maintain.[1]

## Fable‑specific caveat – Don’t force “show your reasoning”

- Anthropic has safety guardrails in Fable 5 that silently route certain requests to Opus 4.8 if they look like jailbreaking, hacking, dangerous biology, or attempts to reveal private reasoning.[1]
- A standing “explain your reasoning” line, especially in the system prompt, can trigger refusals or cause Fable 5 to hand your task off to Opus, sometimes without UI indication (though the API shows you the actual model used).[1]

**Actionable takeaway:**  
- Avoid blanket “show your chain‑of‑thought reasoning” instructions in Fable’s system prompts.  
- Prefer outcome‑oriented verification (“show tests, examples, and evidence”) rather than exposing hidden internal reasoning steps.[1]

## How this changes your own Fable 5 setup

If you’re wiring Fable 5 into Claude Code, routing, or multi‑agent systems, the practical adjustments suggested by the video are:

- Use Fable only on the hardest 5–15% of tasks; keep Opus or cheaper models as defaults for routine work.[1]
- Update system and skill prompts to: include task intent, add 1–3 concrete “do not” constraints, require evidence before claiming completion, and avoid generic “show your reasoning” boilerplate for Fable.[1]
- Make effort level selection part of your router: match high/extra‑high only to tasks that truly need Fable‑grade reasoning, and lean on low/medium where similar capability is available more cheaply.[1]

If you share your current Claude/Fable prompt or router setup, I can propose minimally invasive edits that implement these six habits without disrupting what already works for you.

## Human

How can we turn the content of the video into a resuable skill that can be used accross different use cases?

## Assistant

You can turn the video’s six habits and Fable‑specific caveats into a reusable “Fable 5 prompting skill” by encoding them as a small, composable contract that you inject into system prompts, tools, and agents, with a few parameters for context, effort level, and verification.[1]

Below is a concrete, implementation‑oriented design you can drop into Claude Code skills or a router.

## Core idea: a model‑agnostic “Prompting Contract”

The video’s habits are mostly model‑agnostic (any frontier model) with one Fable‑specific caveat.[1]
That’s ideal for a reusable skill: you define a single “prompting contract” that wraps any task, and flip Fable‑specific flags when the active model is Fable 5.[1]

At a high level, the skill should:

- Accept: task description, user intent, audience, effort level, risk/safety level, and “allowed actions”.[1]
- Emit: a structured instruction block that enforces the six habits plus Fable routing caveat, ready to prepend to a task prompt or to use as a system role.[1]

Think of it as a function that turns arbitrary tasks into “well‑formed Fable‑ready prompts”.

## Skill inputs and outputs

### Inputs

Design the skill to take something like:

- `task`: natural language description of what the user wants.[1]
- `intent`: why the user is doing this (business goal, bigger workflow).[1]
- `audience`: who the output is for (client, internal engineer, end user).[1]
- `effort`: one of `low | medium | high | extra_high` (maps to Fable effort settings). [1]  
- `risk_level`: `routine | complex | safety_critical` (controls verification strength). [1]  
- `allowed_actions`: explicit list like `["analyze", "summarize"]` or `["edit code", "run tests"]`.[1]
- `disallowed_actions`: explicit list like `["send emails", "delete data", "call external APIs"]`.[1]
- `model`: `fable_5 | opus_4_8 | other` (for Fable‑specific caveat logic). [1]  

### Outputs

The skill should output a structured object:

- `system_prompt`: the reusable “contract” text you’ll inject in system / tool prompts.[1]
- `task_prompt`: a concise user‑side task description that assumes the contract is in force.[1]
- `metadata`: effort mapping, chosen verification pattern, and a flag if “explain reasoning” is suppressed due to Fable.[1]

You can easily implement this as a Claude Code helper that runs before most calls, or as a router‑side function that wraps requests.

## Encoding the six habits in the skill

### 1. Always give the “why”

From the video: Fable 5 does better when it understands your intent and uses context to connect your task to the right information.[1]

In the skill:

- Require `intent` and `audience` as inputs; if missing, have the skill derive minimal defaults.[1]
- Always embed a short “why” paragraph in the `system_prompt`, independent of the specific task.[1]

Example system fragment the skill can generate:

> You are assisting with a larger workflow: \(intent\). The primary audience is \(audience\). Use this context to choose which information, tools, and memory to consult, and avoid guessing when context is missing.

This makes the contract reusable across writing, coding, analysis, and planning tasks.

### 2. Explicit negative prompting (what NOT to do)

The docs and video emphasize Anthropic’s own pattern: “Do not do X”, “Don’t add features”, “Don’t do this.”[1]

In the skill:

- Take `disallowed_actions` and convert them into explicit “do not” clauses.[1]
- Also emit a generic safety fence for operational work: “Do not fix, send, edit, or delete anything unless explicitly instructed.”[1]

Example generated block:

> When describing a problem or answering a question, your deliverable is your assessment and written output. Report what you find and then stop. Do not fix, send, edit, or delete anything unless explicitly told to do so. Do not perform the following actions: \(disallowed_actions\).

This can be the same across models and skills; only the list changes.

### 3. Let it act once it has “enough”

Anthropic’s docs and Nate’s pattern: “When you have enough information to act, then act”; stop over‑planning, especially at high effort levels.[1]

In the skill:

- Map `effort` to a planning policy:  
  - `low/medium`: very short planning, act quickly.  
  - `high/extra_high`: brief plan then act; no unbounded research loops.[1]
- Generate a directive that discourages infinite planning:

> Do a brief, explicit plan only when needed. When you have enough information to act, then act. Do not over‑plan or gather endless context; prefer incremental execution with verification.

This is reusable for coding, agents, and research skills.

### 4. Match effort to task

Anthropic recommends high as default, extra‑high for capability‑sensitive tasks, medium/low for routine work; Fable 5 on low is similar to Opus 4.8 on extra‑high/max and cheaper.[1]

In the skill:

- Accept `effort` and attach guidance to it:

> Effort setting: \(effort\).  
> - Routine tasks: keep plans minimal, act quickly.  
> - Complex or capability‑sensitive tasks: use more thorough planning and self‑checking, but still act once you have enough detail.

- If you have a router, this skill can also emit “recommended model” metadata based on `effort` and `risk_level`.[1]

So the skill is not just prompt text, but a small policy engine for model/effort selection.

### 5. Make it prove its work (verification loops)

Nate’s strongest rule: “Make it prove it”; bake verification loops into agents and skills instead of asking “Is this done?” at the end.[1]

In the skill:

- Use `risk_level` to choose verification intensity:  
  - `routine`: require at least one explicit check or example.  
  - `complex`: require tests/logs/consistency checks.  
  - `safety_critical`: require multiple independent checks and clear disclosure of any unverified assumptions.[1]

Generated directive example:

> Before you say any task is complete, point to concrete results that prove it (tests, logs, examples, diffs, or other evidence). Only report work you can back with evidence. If anything is not verified, say so plainly instead of guessing, and list the missing checks.

You can standardize this string across all your skills and agents; the skill just toggles phrasing based on risk.

### 6. Say less, not more (but keep intent)

Tip 6: short instructions can steer just as well as spelling out long rule lists, especially when Fable is wrapped in a good environment (tools, context, skills).[1]

In the skill:

- Compress rules into a few guiding principles instead of enumerating dozens of lines.[1]
- Use style text like:

> Lead with the outcome, keep your explanations and code changes simple, and pause only when the work truly needs human review.

The skill’s job is then to produce concise but high‑leverage guidance for any downstream task, not huge boilerplate blocks.

## Fable‑specific caveat: avoid “show your reasoning”

The video highlights that a standing “explain your reasoning” line, especially in the system prompt, can cause Fable 5 to refuse or silently route to Opus 4.8, due to safety checks around private reasoning and jailbreak‑like requests.[1]

In the skill:

- When `model === "fable_5"`, suppress chain‑of‑thought language in system prompts.[1]
- Instead, emphasize *evidence‑based outputs*:

> Do not expose your private internal reasoning. Focus on clear outcomes supported by tests, examples, and other evidence, rather than describing hidden internal thought processes.

- When `model !== "fable_5"`, you can optionally let the caller add their own “show reasoning” instructions.[1]

This keeps the skill safely reusable across models while respecting Fable’s guardrails.

## Example reusable skill spec (for Claude Code / router)

Here’s a compact spec you can implement as a function in your router or as a Claude Code “pre‑prompt skill”:

**Signature (TypeScript‑ish)**

```ts
type Effort = "low" | "medium" | "high" | "extra_high";
type RiskLevel = "routine" | "complex" | "safety_critical";
type ModelName = "fable_5" | "opus_4_8" | "other";

interface PromptContractInput {
  task: string;
  intent: string;
  audience: string;
  effort: Effort;
  riskLevel: RiskLevel;
  allowedActions: string[];
  disallowedActions: string[];
  model: ModelName;
}

interface PromptContractOutput {
  systemPrompt: string;
  taskPrompt: string;
  metadata: {
    effort: Effort;
    riskLevel: RiskLevel;
    model: ModelName;
    showReasoningSuppressed: boolean;
  };
}
```

**Behavior (high level)**

- Build `systemPrompt` by stitching together:  
  - Context / “why” block.[1]
  - Negative prompting / allowed vs disallowed actions.[1]
  - Effort and planning guidance (“act once you have enough”).[1]
  - Verification / evidence requirements.[1]
  - Concise “lead with outcome, keep it simple” style guidance.[1]
  - Fable‑specific “no internal reasoning exposure” if `model === "fable_5"`.[1]
- Build `taskPrompt` as a short, focused description of the immediate task, relying on the contract for behaviour.[1]

You then:

- Inject `systemPrompt` into the system role for Claude or the tool/skill.  
- Use `taskPrompt` as the actual user query content.  
- Use `metadata` for routing (effort setting, model choice).

## Concrete next steps for your stack

Given your setup (Claude Code, multi‑provider routing, custom plugins), pragmatic steps:

1. **Define the skill as code, not just text.**  
   Implement the `PromptContractInput → PromptContractOutput` function in your router/service layer so it’s callable from any entry point (CLI, Claude Code, HTTP API).[1]

2. **Wrap all “hard” tasks with the skill.**  
   For tasks likely to use Fable or other frontier models, route them through this skill to generate a consistent system prompt that encodes the six habits and Fable caveat.[1]

3. **Parameterize effort and risk.**  
   Add simple heuristics or a classifier that picks `effort` and `riskLevel` per task, so you’re not manually deciding each time. This is where you embed the “Fable only for the hardest 5–15% of tasks” rule.[1]

4. **Bake verification into all agents.**  
   Update your Claude Code skills / agents to always include the verification block from the skill, instead of ad‑hoc “is this done?” queries.[1]

5. **Add a Fable‑aware flag in the router.**  
   Whenever `model === "fable_5"`, have the router automatically remove generic “explain your reasoning” boilerplate and rely instead on evidence‑focused instructions from this skill.[1]

If you share one of your existing Claude Code system prompts or router configs, I can help translate these six habits and the Fable caveat into a concrete prompt+code snippet that drops in with minimal changes to your current architecture.
