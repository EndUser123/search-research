---
title: "In Claude code, I would like to learn about prompt chaining.  Please tell me everything about it. Best practice, working"
date: "2026-04-26"
mode: "CONCISE"
uuid: "e0daa5af-3322-430b-a835-8484cd9d7f31"
entry_count: 7
---

## Human

In Claude code, I would like to learn about prompt chaining.  Please tell me everything about it. Best practice, working examples, and I want to be able to give it to another LLM so they remember.

## Assistant

Prompt chaining is a way of breaking a big task into a sequence of smaller prompts where each step’s output becomes structured input to the next step. In Claude Code, that usually means orchestrating multiple `client.messages.create` calls (or tools) with explicit intermediate representations, not just one giant “do everything” prompt.[1][2][3][4][5]

Below I’ll cover: what prompt chaining is (conceptually), Claude‑specific best practices, concrete “Code with Claude”–style patterns, and a reusable spec you can hand to other LLMs so they implement chains consistently and remember the design.

***

## Core idea and when to use it

- Prompt chaining = sequence of prompts where each step has a narrow objective, and the downstream step consumes a structured slice of the previous output.[3][6][5][1]
- It’s most useful when:
  - The task is naturally decomposable (analyze → plan → implement → review).  
  - You want to log / inspect / test the intermediate artifacts (e.g., plans, schemas, critiques).[2][3]
  - You need control over branching (different follow‑up prompts depending on model output).[6]

For Claude specifically:

- Claude can do a lot of “internal” chaining using chain‑of‑thought and sub‑agents, but external chaining (multiple calls) is still recommended when you care about deterministic pipelines, modularity, or automated evaluation of intermediate results.[4][2][3]
- External chains are also how you *compose* Claude with other tools (compilers, linters, web scrapers, vector DBs, etc.) in Code.

***

## Design principles (Claude-oriented best practices)

These are the conventions I’d bake into any “prompt chaining standard” you hand to other LLMs.

### 1. Decompose into single‑objective steps

- Identify explicit subtasks; each step should have exactly one “definition of done”.[7][5][3][4]
- Typical decomposition patterns:
  - Understand → structure → operate → check.
  - Extract → transform → generate → validate.
  - Draft → critique → revise (self‑correction).[5][2][3]

If a step’s instructions read like “analyze, then plan, then code, then test, then document”, it should be split.

### 2. Make handoffs minimal and structured

- Pass only what the next step needs, not the entire chat history or raw dump.[3][7][6][5]
- Use a **machine‑readable envelope** (JSON or XML‑like tags) so downstream prompts can reliably extract fields.[4][7][3]
- Avoid information overload by limiting each output to essential fields; long, noisy contexts degrade performance later in the chain.[7][3]

Claude-specific note: Anthropic’s docs explicitly recommend XML‑style tags or JSON schemas as a way to structure model output and to organize multi‑step workflows.[2][4]

### 3. Separate *role* from *task*

- Use a stable “system prompt” or preamble that defines the agent’s role, general style, and invariants; use the user prompt for the specific step objective.[2][3][4]
- This separation lets you reuse the same role across many chain steps and test or swap the task prompts independently.[3][4]

In Code, that means: keep an explicit “agent contract” in a shared string/file, and pass per‑step instructions in `messages` or tool arguments.

### 4. Build in validation and self‑correction

- Common chain pattern recommended in Claude docs: draft → review against criteria → refine based on the critique.[5][2][3]
- You can validate in two ways:
  - Programmatic checks (length, JSON validity, required keys).[6][3]
  - LLM‑based checks (ask Claude to verify its work against a rubric).[5][2]

If validation fails, branch: either re‑prompt the same step with feedback, or adjust the earlier step.

### 5. Keep prompts precise and testable

- Use **explicit constraints** instead of vague instructions; e.g., “return JSON with keys `plan`, `risks`” or “between 250–350 characters”.[4][2][3]
- Every output requirement should be testable in code: length, presence/absence of keys, allowed enum values, etc.[3][4]
- When you want models to “think stepwise”, be explicit: “First reason step by step, then output only the final JSON block matching this schema.”

### 6. Plan for branching and failure

- Chains are often conditional: use the model’s structured output (e.g., `status: ok | needs_more_info`) to decide the next step.[6][5]  
- Include “escape hatches” in the spec:  
  - `status: "cannot_complete"` with `reason`.  
  - `missing_information: [...]` with concrete questions to ask the user.

***

## Working patterns in Claude Code

Below are patterns you can implement in Code (e.g., TypeScript/Python with the Claude Messages API) and also describe to other LLMs.

### Pattern 1: Analyze → Plan → Implement → Review

**Use case:** multi‑file refactor, new feature, multi‑step migration.

**Step A: Analyze**

Goal: build a structured understanding of the current state.

Output schema (example you can reuse):

```xml
<analysis>
  <summary>...</summary>
  <key_components>
    <component>
      <name>...</name>
      <role>...</role>
      <risks>...</risks>
    </component>
  </key_components>
  <constraints>
    <constraint>...</constraint>
  </constraints>
</analysis>
```

Characteristics:

- Single objective: “analyze the existing codebase wrt this task.”  
- Output is short and structured, easy for the next step to consume.[4][3]

**Step B: Plan**

Input: `<analysis>...</analysis>` from Step A.  
Objective: produce a minimal, testable plan.

```xml
<plan>
  <goal>...</goal>
  <steps>
    <step id="1">
      <description>...</description>
      <files_to_touch>...</files_to_touch>
    </step>
    ...
  </steps>
  <checks>
    <check>unit tests pass for ...</check>
  </checks>
</plan>
```

You can enforce that the plan is “at most N steps” and all steps are independently executable.

**Step C: Implement**

Implementation can be broken further:

- C1: “patch design” → propose diffs as structured data.  
- C2: Apply diffs using Code’s file operations.  
- C3: Ask Claude to explain risky changes (optional).

**Step D: Review**

Use Claude in reviewer mode over the diffs with a rubric (style, safety, tests, invariants).[2][5]
Output: `<review status="approve|changes_requested">...</review>` used to decide whether to loop back to planning/implementation.

***

### Pattern 2: Extract → Transform → Generate → Validate

Useful for documentation, summaries, and data pipelines.

Example from official guidance: summarization → validation → translation.[3]

**Step 1: Summarize**

- System: “You are a summary writer that produces concise, accurate summaries.”[3]
- User: “Summarize the following text in about 300 characters. Output only the summary text.”[3]

**Step 2: Validate (programmatically)**

- Your code counts characters and checks they fall in a range (e.g., 250–350).[3]
- If it fails, re‑prompt with stronger constraints (“The previous summary was length X, adjust to 300±50 characters.”).

**Step 3: Translate**

- System: translation role.  
- User: “Translate this English summary into French; keep meaning and approximate length.”

Key point: validation is done by code rather than asking the model to judge itself for length; this is how CodeSignal’s tutorial suggests building robust chains.[3]

***

### Pattern 3: Self‑refinement chain

Claude docs and prompting guides describe “self‑correction” / “self‑refine” as a standard chain:[5][2][3]

1. Generate initial output.  
2. Have the model critique the output against explicit criteria.  
3. Have the model revise based on the critique.

You can standardize this with a schema:

- Step 1 output:

```xml
<draft>
  <content>...</content>
</draft>
```

- Step 2 (critique) output:

```xml
<critique>
  <issues>
    <issue severity="high">Missing edge cases for X</issue>
  </issues>
  <score_overall>7/10</score_overall>
</critique>
```

- Step 3: feed both `<draft>` and `<critique>` and ask for `<final>`.

This pattern is reusable for code, prose, designs, or test plans.

***

### Pattern 4: Conditional branching chain

From general prompt chaining tutorials: branch based on classification or sentiment.[6][5]

General design:

1. First call returns `classification: enum` plus `reason`.  
2. Your orchestrator picks the appropriate follow‑up prompt template.

Example schema:

```json
{
  "status": "ok",
  "classification": "positive | negative | neutral",
  "reason": "short explanation",
  "next_action_hint": "suggested next step name"
}
```

In Claude Code, you can use this for:

- Routing between different tools or skills.  
- Deciding whether to escalate to a human.  
- Choosing “quick fix” vs “deep refactor” flows.

***

## A reusable “Prompt Chaining Spec” for other LLMs

You said you want something you can give to another LLM so they remember and follow it. Below is a compact spec you can paste into a system message or “skills” document and reuse.

You can treat this as a *contract* that defines how that LLM builds and runs chains.

***

### Prompt Chaining Contract (LLM‑oriented)

> Role: You are an **orchestrator** that solves tasks using multi‑step prompt chains instead of single giant prompts. You must design, document, and follow explicit chains.

**Definitions**

- “Step” = one model/tool invocation with a single, clear objective.  
- “Chain” = ordered list of steps where each step’s output is structured input to later steps.  
- “Handoff” = structured data (usually JSON or XML‑tagged) passed between steps.

**Global rules**

1. Always break complex tasks into 2–5 steps when possible.  
2. Each step must have:
   - A short name.  
   - A single objective.  
   - Precise input and output schemas.  
3. Handoffs must be minimal and structured:
   - Only include fields required for later steps.  
   - Use fixed field names and types.  
4. Prefer external validation:
   - Design outputs so external code can check length, JSON validity, required fields.  
5. Support branching:
   - Use `status` and `classification` fields to indicate success, failure, or which branch to follow.

**Required step metadata format**

Whenever you design a chain, first output a **chain plan** in JSON with this schema:

```json
{
  "chain_name": "string",
  "description": "short explanation",
  "steps": [
    {
      "id": "step_1",
      "name": "short name",
      "objective": "single clear objective",
      "input_schema": {
        "fields": [
          { "name": "field_name", "type": "string|json|number|enum", "required": true }
        ]
      },
      "output_schema": {
        "fields": [
          { "name": "field_name", "type": "string|json|number|enum", "required": true }
        ]
      },
      "notes": "constraints, style, limits"
    }
  ]
}
```

After emitting the plan, follow it step by step.

**Output conventions**

- For actual step outputs (not the plan), respond in one of these envelopes:

  - JSON:

    ```json
    {
      "step_id": "step_1",
      "status": "ok | error | needs_more_info",
      "data": { "...": "..." },
      "notes": "optional"
    }
    ```

  - XML‑style tags:

    ```xml
    <step id="step_1" status="ok">
      <data>...</data>
      <notes>...</notes>
    </step>
    ```

- When `status` is not `"ok"`, include:
  - `error_type` and `error_message` or  
  - `missing_information` as a list of questions.

**Best practices to follow**

- Use explicit, testable constraints: length ranges, allowed values, required sections.  
- Prefer many small, composable chains over one very long chain.  
- Reuse standard patterns:
  - analyze → plan → implement → review;  
  - extract → transform → generate → validate;  
  - draft → critique → revise.  
- Never change the shapes of previously defined schemas within a conversation unless explicitly instructed.

You can paste this contract into a system prompt for other LLMs; they will then produce chain plans and step outputs that are easy to orchestrate from Claude Code or any other environment.

***

## How to actually wire this in Claude Code

Conceptually, wiring is:

1. System message: include the “Prompt Chaining Contract” above.  
2. First tool/LLM call: ask it to design a chain given a high‑level task; store the returned `chain.plan`.  
3. Orchestrator (your code) loops through `steps`:
   - Build each step’s prompt from the plan and collected data.  
   - Call Claude with the appropriate instructions.  
   - Parse and validate outputs against `output_schema`.  
   - Branch or retry as needed.  
4. Maintain logs of the `plan`, each `step`’s input/output, and any validation failures.

Because you’re already building multi‑provider orchestrations, the key is: standardize on a small set of schemas and chain patterns, and then force each LLM to “play inside” that contract.

Would you like a concrete TypeScript or Python skeleton that implements this chain plan + step‑runner pattern for Claude Code, with one of the example chains above wired end‑to‑end?

## Human

Show:
Ready-to-run Claude prompt chaining script: summarize → self-correct → action items
Claude prompt chaining code examples in Python
Common pitfalls in Claude prompt chaining and fixes
How to implement self-correction chains with Claude
Prompt chaining vs chain of thought in Claude

## Assistant

Here’s the practical version: in Claude, prompt chaining is best when you want explicit stages, inspectable artifacts, and retry/control points; self-correction is the most useful default chain because it improves quality without requiring complex orchestration. Chain-of-thought is different: it is mostly a single-call reasoning style, while prompt chaining is a multi-call workflow you can log, validate, and branch.[1][2][3]

## Ready-to-run script

Below is a ready-to-run Python script for a 3-step Claude chain: summarize → self-correct → action items. It uses Anthropic’s Messages API pattern, XML tags for structured prompts, low temperature-like behavior via explicit constraints, and separate API calls so each stage is inspectable and replaceable.[3][1]

```python
# pip install anthropic
# export ANTHROPIC_API_KEY=your_key_here

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"

def call_claude(system: str, user: str, max_tokens: int = 1600) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()

SUMMARIZER_SYSTEM = """You are a precise summarization assistant.
Be accurate, concise, and faithful to the source.
Do not invent facts.
Return output using the requested XML tags only."""

CRITIC_SYSTEM = """You are a strict reviewer.
Your job is to find factual omissions, ambiguity, verbosity, weak phrasing, and unsupported claims.
Be concrete and actionable.
Return output using the requested XML tags only."""

ACTION_SYSTEM = """You are an operations assistant.
Convert reviewed content into practical action items.
Prioritize specificity, ownership suggestions, and clear next steps.
Return output using the requested XML tags only."""

def summarize(text: str) -> str:
    prompt = f"""
<task>
Create a concise summary of the source text.
</task>

<instructions>
- Keep the summary to 6-10 bullets.
- Preserve only important facts, decisions, risks, and next steps.
- If the source is unclear, say so explicitly.
- Do not add information not present in the source.
</instructions>

<source_text>
{text}
</source_text>

<output_format>
<summary>
  <bullet>...</bullet>
  <bullet>...</bullet>
</summary>
</output_format>
"""
    return call_claude(SUMMARIZER_SYSTEM, prompt)

def self_correct(source_text: str, draft_summary: str) -> str:
    prompt = f"""
<task>
Review the draft summary against the original source text, then produce:
1. a critique
2. a corrected summary
</task>

<review_criteria>
- factual accuracy
- missing important information
- unsupported claims
- ambiguity
- unnecessary verbosity
- weak or non-actionable wording
</review_criteria>

<source_text>
{source_text}
</source_text>

<draft_summary>
{draft_summary}
</draft_summary>

<output_format>
<review>
  <issues>
    <issue severity="high|medium|low">...</issue>
  </issues>
  <corrected_summary>
    <bullet>...</bullet>
    <bullet>...</bullet>
  </corrected_summary>
</review>
</output_format>
"""
    return call_claude(CRITIC_SYSTEM, prompt)

def generate_action_items(source_text: str, corrected_review: str) -> str:
    prompt = f"""
<task>
Generate action items from the reviewed summary.
</task>

<instructions>
- Derive actions only from the source and corrected summary.
- Include only actions that are reasonably implied.
- Use priority: high, medium, low.
- Include owner suggestions only when inferable; otherwise use "unassigned".
- Include deadlines only when explicit; otherwise use "unspecified".
</instructions>

<source_text>
{source_text}
</source_text>

<reviewed_summary>
{corrected_review}
</reviewed_summary>

<output_format>
<action_items>
  <item>
    <title>...</title>
    <priority>high|medium|low</priority>
    <owner>...</owner>
    <deadline>...</deadline>
    <rationale>...</rationale>
  </item>
</action_items>
</output_format>
"""
    return call_claude(ACTION_SYSTEM, prompt)

def run_chain(text: str):
    draft = summarize(text)
    reviewed = self_correct(text, draft)
    actions = generate_action_items(text, reviewed)
    return {
        "draft_summary": draft,
        "reviewed_summary": reviewed,
        "action_items": actions,
    }

if __name__ == "__main__":
    sample_text = """
    Team meeting notes:
    We agreed to migrate the billing webhook handler before May 15.
    The current retry logic is causing duplicate invoice events.
    Sarah will investigate idempotency keys.
    We are blocked on vendor documentation for refund edge cases.
    A customer-facing incident review should be drafted this week.
    """
    result = run_chain(sample_text)
    print(json.dumps(result, indent=2))
```

## Why this pattern works

The script separates generation, critique, and conversion-to-actions into distinct calls, which matches Anthropic’s recommendation to use explicit prompt chaining when you need to inspect intermediate outputs or enforce a pipeline structure. The XML-tagged structure also follows Anthropic’s guidance that Claude handles mixed instructions, context, and outputs more reliably when they are clearly delimited with descriptive tags.[1]

## Python implementation patterns

If you want production-grade Python chaining with Claude, use these patterns.[3][1]

- Keep one stable system prompt per role, such as summarizer, reviewer, and action planner, instead of one giant reusable blob.[1]
- Validate every step before continuing, for example: required tags present, minimum bullet count met, no empty fields, and maybe a simple regex/XML parser check.[3][1]
- Store intermediate artifacts, because prompt chaining is valuable partly for observability, debugging, and branch control.[2][3]
- Retry only the failed step with targeted feedback, rather than rerunning the whole pipeline.[3]
- Use structured outputs as handoff contracts, because downstream prompts become more stable when they consume fixed fields instead of free-form prose.[1][3]

A thinner reusable helper looks like this:

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def run_step(model, system, user, max_tokens=1200):
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        block.text for block in resp.content
        if getattr(block, "type", None) == "text"
    ).strip()

def require_tag(text, tag):
    if f"<{tag}>" not in text or f"</{tag}>" not in text:
        raise ValueError(f"Missing required tag: {tag}")
    return text
```

That pattern is simple, but it captures the core production idea: each step is a contract, not just another chat turn.[1][3]

## Self-correction chains

Anthropic explicitly calls self-correction the most common chaining pattern: generate a draft, review it against criteria, then refine using the review. In practice, self-correction works best when the critique prompt has a rubric and the revision step is forced to respond to that rubric rather than merely “make it better.”[3][1]

A strong self-correction chain usually has 3 distinct prompts:

| Stage | Goal | Best practice |
|---|---|---|
| Draft | Produce first-pass output | Keep scope narrow and output structured.[1][3] |
| Critique | Find concrete flaws | Use explicit criteria like factuality, omissions, ambiguity, and actionability.[1] |
| Revise | Produce improved version | Feed in both the draft and critique; require fixing each issue or explaining why not.[1][3] |

A good critique prompt:

```xml
<task>Review the draft against the source.</task>
<criteria>
  <criterion>factual accuracy</criterion>
  <criterion>missing important details</criterion>
  <criterion>ambiguity</criterion>
  <criterion>verbosity</criterion>
  <criterion>actionability</criterion>
</criteria>
<source>...</source>
<draft>...</draft>
<output>
  <issues>
    <issue severity="high">...</issue>
  </issues>
</output>
```

A good revise prompt:

```xml
<task>Revise the draft using the critique.</task>
<instructions>
- Fix every high-severity issue.
- Fix medium issues unless it would introduce unsupported claims.
- Preserve factual fidelity to the source.
</instructions>
<source>...</source>
<draft>...</draft>
<critique>...</critique>
<output>
  <final>...</final>
</output>
```

## Common pitfalls

Most failed Claude chains come from bad decomposition, bad handoffs, or missing validation rather than from the model itself. Claude is also more literal in newer models, so underspecified prompts that used to “work anyway” can now fail more predictably.[1][3]

### Pitfalls and fixes

| Pitfall | Why it fails | Fix |
|---|---|---|
| One step tries to do too much | Claude has to optimize for multiple goals at once, which weakens consistency.[3][1] | Split into single-objective steps. |
| Passing raw previous output without structure | Downstream prompts must infer meaning from noisy text.[3][1] | Use XML/JSON handoff schemas. |
| No validation between stages | Errors compound silently.[3] | Validate format, completeness, and required fields after each step. |
| Critique prompt is vague | “Review this” produces shallow criticism.[1] | Use an explicit rubric. |
| Revision prompt ignores source text | The model may optimize for critique while drifting from source facts.[1][3] | Include source + draft + critique in revise step. |
| Re-running full chain on one failure | Increases cost and can introduce new variance.[3] | Retry only the failing stage. |
| Treating CoT as chaining | You lose observability and branch control.[2][1] | Use separate API calls when intermediate artifacts matter. |
| Overstuffing context | Later stages get noisy and less reliable.[3][1] | Pass only necessary fields forward. |
| No “needs more info” path | Model guesses instead of surfacing missing inputs.[3] | Add explicit failure/clarification status. |

## Prompt chaining vs chain of thought

Prompt chaining and chain-of-thought solve different problems, and mixing them conceptually causes design mistakes. Anthropic’s docs are clear that Claude can handle a lot of multi-step reasoning internally, but explicit chaining is still useful when you need a controlled pipeline, intermediate inspection, or branching.[2][1]

| Dimension | Prompt chaining | Chain of thought |
|---|---|---|
| Structure | Multiple API calls in sequence.[2][1] | Usually one prompt/call with internal stepwise reasoning.[2] |
| Main value | Control, observability, retries, branching.[1][2] | Better reasoning within one response.[2] |
| Best use | Summarize → review → revise → act, code pipelines, tool workflows.[1][3] | Logical analysis, math-like reasoning, single-turn problem solving.[2] |
| Debugging | High, because each stage is visible.[2][3] | Lower, because reasoning is mostly internal to one call.[2] |
| Implementation | Orchestrator code required.[3][1] | Mostly prompt design and model settings.[1] |

One important nuance: with Claude’s adaptive thinking and subagent behavior, some tasks that previously required external chains can now work in a single call, but that does not replace explicit chaining when you need stable artifacts or deterministic step boundaries.[1]

## Best-practice prompt template

If you want a reusable template for Claude chaining, use this pattern.[1]

```xml
<role>You are a precise [role_name].</role>

<task>
One clear objective only.
</task>

<context>
Only the information required for this step.
</context>

<instructions>
- Be explicit.
- Do not invent facts.
- If information is missing, say so.
- Follow the output format exactly.
</instructions>

<output_format>
<result>
  ...
</result>
</output_format>
```

That format matches Anthropic’s advice to be clear and direct, use explicit formatting constraints, and use XML tags to separate instructions, context, examples, and variable inputs.[1]

## Memory-friendly handoff for another LLM

If your goal is to hand this to another LLM so it “remembers” the approach, give it a compact operating spec like this:

```text
Prompt chaining with Claude:

Definition:
- Prompt chaining = solving a task with multiple explicit LLM calls.
- Each call has one objective.
- Each step returns structured output for the next step.

Default chain:
1. Draft
2. Critique
3. Revise
4. Convert to action items

Rules:
- Use XML or JSON schemas for every handoff.
- Keep system prompts role-specific and stable.
- Pass only required context forward.
- Validate each step before continuing.
- Retry only failed steps.
- Include a status for missing information instead of guessing.

When to use:
- Need observability
- Need retries/branching
- Need structured intermediate artifacts
- Need self-correction

Do not confuse with chain-of-thought:
- CoT = one prompt, internal reasoning
- Prompt chaining = many prompts, explicit workflow
```

That is short enough to be dropped into a system prompt, repo skill, or orchestration note, while preserving the important distinctions and rules.[2][1]

If you want, I can next give you one of these in a more useful form:
1. a production-grade TypeScript Claude chaining runner,
2. a Python version with XML parsing + retries + logging,
3. a Claude Code skill file for prompt chaining you can paste into your repo

## Human

How do we implement this in skills?  One of the patterns we use is to use .artifact folders keyed to Terminal ID files or folders.  This gives us multi-terminal isolation immunity from stale data and immunity from workflow interruption caused by compact events.  Remember that in Claude code skills we can use skill based hooks, agents, MCP servers, etc.

## Assistant

Yes: the right implementation is **not** “put prompt chaining prose inside one SKILL.md and hope the model remembers.” In Claude Code, the robust pattern is: **skill = policy + orchestration contract**, **hooks = deterministic lifecycle glue**, **subagents/agents = isolated workers**, **MCP = external capability plane**, and **`.artifacts/{terminal_id}/{skill}/...` = canonical state and recovery boundary**.[1][2]

## Recommended architecture

Claude Code’s extension model explicitly separates skills, hooks, subagents, MCP servers, and plugins, and notes that hooks can run on lifecycle events while subagents provide isolated context and skills provide reusable workflows. That maps well to your pattern: keep the skill declarative and thin, and move state, gating, replay, and interruption recovery into artifact-backed runners and hooks keyed by terminal identity.[2][3]

A strong implementation shape is:

- `SKILL.md` defines triggers, phases, invariants, and artifact contract.[2]
- Skill-frontmatter hooks register **only while the skill is active**, which is ideal for scoped workflow enforcement rather than global behavior.[3]
- A runner script or Python orchestrator writes and reads `.claude/.artifacts/{terminal_id}/{skill}/{run_id}/...` to preserve monotonic state and compact immunity.
- Subagents do isolated research/review work and return small summaries so the main thread stays clean.[4][2]
- MCP tools are invoked for external systems only, while the skill teaches Claude **when and how** to use them.[2]

## Canonical state model

Your `.artifact` pattern is exactly the right place to anchor chain state because hooks receive session metadata, including `session_id`, `transcript_path`, `cwd`, and, in subagent contexts, `agent_id` and `agent_type`. Claude Code also exposes `PreCompact` and `PostCompact` hook events, which means you can explicitly persist or rehydrate chain state across compaction instead of hoping the conversation retains it.[3]

Use this canonical layout:

```text
.claude/.artifacts/{terminal_id}/prompt-chain/
  active_run
  session_identity.json
  state.json
  phase.txt
  inputs/
    source.txt
    user_intent.json
  outputs/
    summary.xml
    critique.xml
    actions.xml
  receipts/
    summary.ok.json
    critique.ok.json
    actions.ok.json
  checkpoints/
    precompact-2026-04-25T20-21-00Z.json
    postcompact-2026-04-25T20-21-08Z.json
  logs/
    runner.log
    hook.log
  flags/
    .step-summary-complete
    .step-critique-complete
    .step-actions-complete
    .workflow-complete
```

This matches your prior preference for terminal-scoped, skill-scoped artifact directories that decouple validation from generation and prevent cross-terminal contamination.[5]

## What belongs where

The most important design decision is **responsibility split**. If you blur these boundaries, skills become fragile and untestable.[6][3][2]

| Component | Responsibility | Should persist state? |
|---|---|---|
| Skill | Workflow contract, phase rules, trigger conditions, allowed branches.[2] | No, except references to artifact paths. |
| Hook | Deterministic event handling: bootstrap, validate, snapshot, resume hints, guardrails.[3] | Writes receipts/checkpoints, not business logic. |
| Python/Bash runner | Real chain engine: parse state, call LLM/MCP/tools, validate outputs, advance phase.[6] | Yes, canonical owner. |
| Subagent | Isolated research/review/extraction with bounded summary output.[2][4] | Only local temp outputs; final results promoted by runner.[6] |
| MCP server | External reads/writes, retrieval, system actions.[2][3] | External system owns truth, local receipts optional.[3] |

## Skill implementation pattern

The skill should behave like a **workflow dispatcher** that resolves identity, loads or creates the run directory, inspects artifact state, and chooses the next admissible phase. The skill should not assume conversational continuity, because compact and multi-terminal work make conversation memory a weak source of truth compared with artifacts.[7]

A good `SKILL.md` shape is:

```markdown
---
name: prompt-chain
description: Terminal-scoped artifact-backed prompt chaining workflow for summarize, critique, and action extraction with resumable state, compact immunity, and multi-terminal isolation.
disable-model-invocation: false
hooks:
  SessionStart:
    - hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-chain-session-start.sh"
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-chain-userpromptsubmit.sh"
  PreCompact:
    - hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-chain-precompact.sh"
  PostCompact:
    - hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-chain-postcompact.sh"
  SubagentStop:
    - hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-chain-subagent-stop.sh"
---

Use this skill when the user needs a multi-step prompt workflow with resumable state.

Workflow invariants:
- Canonical state lives under .claude/.artifacts/{terminal_id}/prompt-chain/
- Never trust conversational memory over artifact state
- Advance only one validated phase at a time
- Reuse validated artifacts when fresh
- If a required artifact is missing or invalid, regenerate only that phase
- Prefer subagents for research/review tasks that would pollute main context
- Prefer MCP for external retrieval or writes
```

This design aligns with Claude Code’s documented support for hooks in skill frontmatter and their lifecycle scoping to the active component.[3]

## Terminal identity

The weakest point in many designs is terminal identity resolution, so make it a first-class primitive. Since hooks receive session metadata and you already use terminal-keyed artifacts, the clean pattern is to resolve terminal identity once at session or prompt entry, persist it in `session_identity.json`, and never recompute it differently mid-run.[3]

Recommended identity precedence:

- Explicit `TERMINAL_ID` environment variable if your launcher sets it.
- Otherwise a hook-backed resolver that writes the authoritative ID to artifact state at session start.[3]
- Include:
  - `terminal_id`
  - `session_id`
  - `transcript_path`
  - `cwd`
  - `agent_id` if in subagent
  - `agent_type` if present.[3]

Example:

```json
{
  "terminal_id": "wt-10844",
  "session_id": "abc123",
  "transcript_path": "C:/Users/me/.claude/projects/x/transcript.jsonl",
  "cwd": "C:/src/my-repo",
  "skill": "prompt-chain",
  "active_run_id": "2026-04-25T20-21-00Z"
}
```

## Hooks you actually want

Claude Code exposes session, prompt, tool, compact, and subagent lifecycle hooks, so you can make the workflow resilient without stuffing more logic into the skill prompt.[3]

### SessionStart

Use `SessionStart` to establish artifact root, write `session_identity.json`, restore `active_run`, and emit lightweight context if a resumable workflow exists. Because SessionStart hook stdout or `additionalContext` can be injected into context, keep it short and operational, not verbose.[3]

Suggested behavior:

- Resolve terminal identity.
- Ensure `.claude/.artifacts/{terminal_id}/prompt-chain/` exists.
- If `active_run` exists and incomplete, emit a short resume notice.
- Append environment exports if needed via `CLAUDE_ENV_FILE` where appropriate.[3]

### UserPromptSubmit

Use `UserPromptSubmit` to classify whether the current prompt should attach to an existing run, create a new run, or refuse ambiguous continuation. This is the right place for prompt injection of minimal resume context or policy reminders, and it matches your prior work on userpromptsubmit patterns.[3]

Suggested behavior:

- Parse current prompt intent.
- If it references “continue”, “resume”, “fix phase 2”, etc., bind to existing run.
- Add compact resume context:
  - active run id
  - current phase
  - missing required artifacts
  - next admissible step.[3]

### PreCompact and PostCompact

These are the most important hooks for your stated compact immunity goal, because Claude Code has explicit lifecycle points before and after compaction.[3]

Use `PreCompact` to:

- snapshot `state.json`
- persist phase cursor
- write any unsaved in-memory branch decision
- seal in-progress steps with `.incomplete` markers.[3]

Use `PostCompact` to:

- reload canonical state
- verify whether the active step completed before compaction
- inject a tiny recovery note into context
- never replay a completed step without checking receipts first.[3]

### SubagentStop

Since subagents are isolated workers that return summaries, `SubagentStop` is the correct point to harvest and normalize their outputs into your canonical artifact schema. Do not let subagents write final chain phase completion flags directly; have the orchestrator validate and promote them.[6][2][3]

## Subagent pattern

Claude Code documentation says subagents run in isolated context and return summaries, and community best practice echoes that they work best when they collect information and send back a small result. That fits your architecture well: subagents should be **leaf workers**, not state owners.[4][6][2]

Good subagent roles for prompt chaining:

- `source-analyzer`: extract facts, decisions, risks from large source material.
- `critique-reviewer`: review a summary against source using a rubric.
- `action-normalizer`: convert reviewed outputs into action items.
- `evidence-checker`: verify that claimed items are grounded in source artifacts.[6]

Each subagent should:

- read only required files
- emit one compact structured result
- avoid maintaining long-lived state
- return enough metadata for promotion:
  - `run_id`
  - `step`
  - `status`
  - `artifact_path`
  - `validator_hints`.[4][2]

## MCP pattern

Claude Code docs position MCP as the way to connect external services, while skills teach usage patterns and hooks can also invoke MCP tools directly. For your workflow, MCP should be used where external truth exists: issue trackers, transcript retrieval, memory systems, repos, browser automation, or internal evidence stores.[2][3]

Use MCP when:

- source text lives outside local files
- you need retrieval against a knowledge base
- you need to post resulting action items somewhere
- you need richer structured elicitation/user feedback loops.[3]

Do **not** use MCP as the primary state store for chain control unless that external system is truly the system of record; your `.artifacts/{terminal_id}` directory should stay the local control plane for resumability and isolation.

## Phase machine

Prompt chaining becomes robust when it is treated as a **phase machine**, not just a sequence of prompts. Your state file should define allowed transitions explicitly, so compact/retry/manual intervention cannot jump the workflow into an invalid state.[7]

Example:

```json
{
  "run_id": "2026-04-25T20-21-00Z",
  "skill": "prompt-chain",
  "phase": "critique",
  "status": "in_progress",
  "allowed_next": ["critique", "actions"],
  "completed": ["summary"],
  "failed": [],
  "freshness": {
    "source_hash": "sha256:...",
    "summary": "valid",
    "critique": "missing",
    "actions": "missing"
  }
}
```

Suggested monotonic transitions:

- `initialized`
- `summary`
- `critique`
- `actions`
- `verified`
- `complete`

Rules:

- never mark a phase complete without a validator receipt
- never skip forward unless a policy explicitly allows it
- allow targeted rewind only by deleting downstream receipts or marking them stale.[6]

## Validator receipts

This is one of the highest-leverage ideas in your pattern: separate **artifact generation** from **artifact acceptance**. Each step should produce output plus a validator receipt, and the next phase should depend on the receipt, not on the presence of the output file alone.[6]

Example receipt:

```json
{
  "run_id": "2026-04-25T20-21-00Z",
  "step": "summary",
  "artifact": "outputs/summary.xml",
  "status": "accepted",
  "checks": {
    "xml_well_formed": true,
    "required_tags_present": true,
    "source_hash_match": true,
    "non_empty": true
  },
  "timestamp": "2026-04-25T20:21:45Z"
}
```

That gives you stale-data immunity and deterministic resumption.

## Minimal runner contract

The skill should call a runner rather than embedding all logic in prompt text. The runner can be Python for schema validation and branch logic, with Bash wrappers for hooks and terminal integration, which fits your existing ecosystem.[6]

Pseudo-contract:

```text
prompt_chain_runner.py
  resolve_identity()
  load_or_init_run()
  inspect_state()
  choose_next_phase()
  execute_phase()
  validate_phase_output()
  write_receipt()
  advance_state()
  render_resume_hint()
```

Each phase implementation can choose between:

- direct main-thread model call
- subagent dispatch
- MCP retrieval + model synthesis
- hybrid path depending on source size or risk.[2][6][3]

## Example workflow in a skill

A strong user-facing behavior for `/prompt-chain` would be:

1. User invokes skill with source or asks for a chained task.
2. `UserPromptSubmit` hook resolves run binding and injects minimal resume context if needed.[3]
3. Runner checks `.artifacts/{terminal_id}/prompt-chain/active_run`.
4. If no valid summary receipt exists, run summary phase.
5. If summary receipt exists but critique receipt missing, run critique phase, potentially through a subagent.
6. If critique exists, run action extraction.
7. Optionally run verification phase before reporting completion.[6]

Because hooks merge across sources while skill hooks are only active during the component lifecycle, this remains isolated and composable instead of turning into a repo-wide trap.[2][3]

## Anti-patterns to avoid

These are the design errors most likely to break your goals.

- **Conversation as source of truth.** Compact and multi-terminal work make this unreliable; artifact state should win.
- **Subagents writing final state directly.** They should return summaries; the runner promotes validated outputs.[4][2][6]
- **One giant SKILL.md with all operational logic.** Skills are best for reusable workflows, but deterministic lifecycle work belongs in hooks/scripts.[2][3]
- **Global hooks for workflow-specific behavior.** Prefer skill-scoped hooks unless the behavior truly applies project-wide.[3]
- **No explicit stale check.** Always compare source hash / input fingerprint before reusing artifacts.
- **Using artifact presence as completion.** Require validator receipts and flags.
- **Letting phase transitions be prompt-driven only.** Use explicit state transitions in files, not implicit reasoning.[7]

## Practical implementation template

A clean repo structure would look like this:

```text
.claude/
  skills/
    prompt-chain/
      SKILL.md
      references/
        contracts.md
        phase-rules.md
      scripts/
        prompt_chain_runner.py
        validators.py
        terminal_identity.py
      agents/
        critique-reviewer.md
        source-analyzer.md
  hooks/
    prompt-chain-session-start.sh
    prompt-chain-userpromptsubmit.sh
    prompt-chain-precompact.sh
    prompt-chain-postcompact.sh
    prompt-chain-subagent-stop.sh
  settings.json
```

This matches Claude Code’s documented pattern where skills contain reusable workflow knowledge, subagents isolate heavy work, hooks automate lifecycle behavior, and plugins can package the whole unit if you want reuse across repos.[2][3]

## My recommendation

For your environment, the optimal design is:

- **one public skill** per user-facing workflow,
- **artifact-backed phase machine** under `.claude/.artifacts/{terminal_id}/{skill}/`,
- **skill-scoped hooks** for bootstrap, compact protection, and resume,
- **subagents for noisy/research-heavy steps**,
- **MCP only for external truth/actions**,
- **validator receipts as gating mechanism**.[6][2][3]

That gives you the properties you care about most: multi-terminal isolation, stale-data immunity, compact resilience, explicit recovery, and the ability to combine hooks, agents, and MCP without collapsing control flow into one prompt.[2][3]

If you want, next I can draft a **full copy-paste implementation package** for this pattern:
- `SKILL.md`
- hook scripts
- Python runner skeleton
- artifact schema
- subagent definitions
- example `.claude/settings.json` wiring

## Human

"
  /design [STANDARD enforcement]

  Architecture Review: diagnose-complete-implementation-package.md

  Verdict: Significant rework needed before this is deployable

  The package is well-structured on paper but has several critical issues that would break at runtime. The most fundamental problem
  is a name collision — you already have a working /diagnose skill that does something entirely different.

  ---
  CRITICAL: Name Collision

  The existing /diagnose at P:\\packages\\cc-skills-sdlc\\skills\\diagnose\\ is a structured hypothesis-testing debugging protocol — list
   3+ hypotheses, disconfirm each, document the winner. The proposed package is a project-state diagnostic orchestrator — gap
  detection, artifact writing, action rendering, verification. These are different skills serving different purposes. Deploying this
   under the same name overwrites the working one.

  Fix: Either rename the proposed skill (e.g., /health, /survey, /audit) or merge the two scopes intentionally.

  ---
  CRITICAL: Hooks Won't Work with Claude Code

  All hooks use an in-process run(data) contract, but Claude Code hooks are CLI subprocesses — they receive JSON on stdin and emit
  JSON on stdout. The proposed hooks:

  - Don't read stdin
  - Don't emit the required {"decision": "block"|"allow", "reason": "..."} JSON
  - Don't have CLI wrapper entry points (if __name__ == "__main__")

  The implementation notes say to "reuse hook base helpers such as hookmain" from GTO, but the package doesn't actually use them.
  These hooks are dead code.

  ---
  CRITICAL: Scope Guard Never Activates

  scope_guard() checks for a "diagnose-active" marker file. Nothing in the package ever creates this file. Result: all hooks always
  return early with None, making them permanent no-ops.

  ---
  HIGH: lib/ Directory Naming Violation

  Your global CLAUDE.md mandates __lib (double underscore) for internal library directories, not lib, because .gitignore patterns
  can silently exclude lib/. The package uses lib/ throughout.

  ---
  HIGH: Freshness Logic Bug

  Orchestrator line:
  artifact_git_sha=state.current_target and state.current_target and git_sha,
  This is a boolean expression that evaluates to git_sha when current_target is truthy, or the falsy value. It never passes the
  actual artifact's git SHA for comparison. Freshness detection will be wrong whenever target is set.

  ---
  HIGH: Agent Layer Is Empty

  All 4 agent functions return empty AgentResult objects. The "agent enrichment" layer — billed as a core pipeline stage — is pure
  scaffolding. The pipeline runs but produces nothing from agents.

  ---
  HIGH: datetime.utcnow() Deprecated

  Python 3.12+ deprecates utcnow(). Use datetime.now(datetime.UTC) instead.

  ---
  MEDIUM: Arbitrary Health Score Formula

  base = max(0, 100 - findings_count * 7)
  Why 7? This violates the "no arbitrary thresholds" principle. A project with 15 findings scores 0; one with 5 scores 65. The
  formula conflates count with severity without justification.

  ---
  MEDIUM: Stop Hook Completion Detection

  if "done" in response.lower() or "complete" in response.lower():
  This false-positives on "done with this part", "that completes the investigation", "I'm not done yet", etc. String-matching
  "done"/"complete" is too broad for completion gating.

  ---
  MEDIUM: Import Paths Invalid

  Tests use P._claude.skills.diagnose.models which isn't valid Python (dots in directory names, underscore substitution). The notes
  say "replace import roots" but the tests won't run as-is.

  ---
  MEDIUM: Citation Noise

  Nearly every line has [cite:144][cite:143]. These reference GTO and RNS but add no actionable information. They're visual noise
  that would need stripping before deployment.

  ---
  LOW: Over-Engineering for Delivered Value

  20+ Python modules, 4 JSON schemas, 13 test files, 5 reference docs, 5 hook files — supporting exactly 2 detectors (missing .git,
  missing README.md) and 4 empty agent stubs. The ratio of scaffolding to actual functionality is extreme.

  ---
  LOW: README.md Violation

  Your global CLAUDE.md states "NEVER create documentation files unless explicitly requested." The package includes a README.md.

  ---
  Summary

  ┌──────────┬───────┬────────────────────────────────────────────────────────────────────┐
  │ Severity │ Count │                             Key Theme                              │
  ├──────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ Critical │ 3     │ Name collision, hooks broken, scope guard dead                     │
  ├──────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ High     │ 4     │ Naming convention, freshness bug, empty agents, deprecated API     │
  ├──────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ Medium   │ 4     │ Arbitrary formula, naive string match, bad imports, citation noise │
  ├──────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ Low      │ 2     │ Over-engineering, README policy                                    │
  └──────────┴───────┴────────────────────────────────────────────────────────────────────┘

  Recommendation: The package needs to (1) resolve the name collision, (2) rewrite hooks for Claude Code's subprocess protocol, (3)
  fix the scope guard activation, (4) rename lib/ to __lib/, (5) fix the freshness bug, and (6) either implement the agent layer or
  remove it from the pipeline until it's needed. The core architectural idea — deterministic-first, freshness-aware, terminal-scoped
   — is sound, but the delivery has too many holes to deploy as-is.

✻ Cooked for 6m 37s

❯ Given that there are some things which are easy to fix, please list what those are and what the fix is, and then list the
  remaining problems that you need the other LLM to provide advice on.

● Here's the split:

  Easy Fixes (local, no external input needed)

  ┌─────┬─────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │          Issue          │                                             Fix                                             │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 1   │ lib/ naming violation   │ Rename lib/ → __lib/ throughout package tree, imports, and docs                             │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 2   │ datetime.utcnow()       │ Replace with datetime.now(datetime.UTC) in models.py empty() and orchestrator               │
  │     │ deprecated              │                                                                                             │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 3   │ Freshness logic bug     │ Change state.current_target and state.current_target and git_sha to pass the artifact's     │
  │     │                         │ actual git SHA (from loaded state/previous artifact)                                        │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 4   │ Import paths invalid    │ Replace P._claude.skills.diagnose... with proper relative imports or correct absolute paths │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Citation noise          │ Strip all [cite:144][cite:143] markers                                                      │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 6   │ README policy           │ Remove README.md from the package                                                           │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 7   │ Arbitrary health        │ Replace magic 7 with a severity-weighted formula or remove the score until real scoring     │
  │     │ formula                 │ logic exists                                                                                │
  ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 8   │ Scope guard never       │ Add marker file creation in orchestrator startup and cleanup in orchestrator shutdown       │
  │     │ activates               │                                                                                             │
  └─────┴─────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────┘

  Needs External LLM Advice

  ┌─────┬────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │       Issue        │                                    Why External Input Needed                                     │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │     │ Name collision     │ Decision: rename the new skill, replace the old one, or merge scopes. Requires product intent,   │
  │ 1   │ with existing      │ not code.                                                                                        │
  │     │ /diagnose          │                                                                                                  │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │     │ Hook protocol      │ The hooks use in-process run(data) but Claude Code expects CLI subprocess JSON. The right fix    │
  │ 2   │ mismatch           │ depends on whether GTO's hookmain / router pattern should be reused, or if frontmatter-based     │
  │     │                    │ hooks are preferred. Need to read the actual GTO hook integration to match the pattern.          │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │     │ Agent layer is     │ The 4 agent stubs return nothing. The prompts exist but there's no dispatch mechanism. Need to   │
  │ 3   │ empty              │ decide: implement agents via Claude Code's Agent tool, via /ai-pcli multi-LLM dispatch, or via   │
  │     │                    │ GTO's existing subagent fan-out. Each has different contracts.                                   │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │     │ Stop hook          │ String-matching "done"/"complete" is too fragile. The right replacement depends on what          │
  │ 4   │ completion         │ completion signal format the existing GTO/RNS/verify ecosystem uses.                             │
  │     │ detection          │                                                                                                  │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Machine render     │ RNSD/RNSA/RNSZ prefixes mirror RNS's format but the format contract isn't documented here. Need  │
  │     │ format             │ to read RNS's actual output contract to ensure compatibility or decide to diverge.               │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 6   │ Overall scope fit  │ This skill overlaps with existing /rca, /tldr-*, /sqd, and /uci. Whether to proceed as-is,       │
  │     │                    │ subset, or consolidate requires architectural judgment about the skill ecosystem boundaries.     │
  └─────┴────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────┘

  Want me to apply the easy fixes, or do you want to get the external advice first?

❯ What is diagnose colliding with?
  Don't be lazy, read the code and the actual hook integrations.
  explain the different contracts for the agent layer.
  look at the Skill-craft plugin or skill or our memory or wiki and look for the non-Regex pattern matching options for hooks.
  read RNS actual output contract don't be lazy
  We're not going to worry about the overall scope fits right now.
  we're going to keep the readme that they suggest because I want it."
"
● Now let me check the hooks docs for non-regex matcher patterns and look at how GTO actually registers its hooks.

● Searching for 2 patterns, listing 1 directory… (ctrl+o to expand)
  ⎿  $ ls "P:/.claude/docs/"*hook* 2>/dev/null | head -10

✽ Perusing… (1m 37s · ↓ 738 tokens)
  ⎿  Tip: Use /btw to ask a quick side question without interrupting Claude's current work

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── design(g) ──
❯ 
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ accept edits on (shift+tab to cycle)
 ▐▛███▜▌   Claude Code v2.1.119
▝▜█████▛▘  glm-5.1 with medium effort · API Usage Billing
  ▘▘ ▝▝    P:\\
  ⎿  Loaded .claude\\CLAUDE.md

  Searched for 2 patterns, read 4 files, listed 2 directories (ctrl+o to expand)
  ⎿  Loaded packages\\cc-skills-meta\\CLAUDE.md

● Now let me check the hooks docs for non-regex matcher patterns and look at how GTO actually registers its hooks.

  Searched for 4 patterns, read 2 files, listed 1 directory (ctrl+o to expand)

● Now I have the full picture. Here are the corrected answers:

  ---
  1. What is diagnose colliding with?

  The existing /diagnose at P:\\packages\\cc-skills-sdlc\\skills\\diagnose\\ is a structured hypothesis-testing debugging protocol — list
   3+ hypotheses, design disconfirming tests for each, mark RULED OUT/CONFIRMED, document the winner. It's a debugging investigation
   protocol.

  The proposed package is a project-state diagnostic orchestrator — gap detection, artifact writing, freshness-aware evidence reuse,
   action rendering, verification. It's a project health analyzer.

  These are different skills. The existing /diagnose is "what's causing this bug?" The proposed one is "what's the health of this
  project/session?" Replacing one with the other would lose the debugging protocol.

  GTO's gap-to-skill mapping (GTO SKILL.md line 250) already routes runtime_error, bug gaps to /diagnose. So the existing /diagnose
  is actively used as a downstream consumer by GTO. Replacing it breaks that routing chain.

  ---
  2. Agent layer contracts — the three options

  Based on what I read:

  Option A — GTO's pattern (Claude Code Agent tool)
  GTO dispatches parallel agents via Agent(subagent_type="gto-logic", prompt="...") (GTO SKILL.md lines 138-141). Agents write JSON
  to terminal-scoped temp files. The orchestrator polls for file completion, then merges. This is the Agent tool with file-based
  handoff pattern. No Python dispatch needed — the SKILL.md instructs Claude to spawn agents directly.

  Option B — /ai-pcli multi-LLM dispatch
  Use ai_cli.py to get independent analysis from Gemini, GPT-5.4-mini, MiniMax M2.7, GLM 5.1 in parallel. Each model gets the same
  prompt, outputs JSON. The orchestrator aggregates. This gives adversarial diversity but no Claude Code Agent tool integration —
  it's external LLMs, not subagents.

  Option C — Stub with prompts only (current proposal)
  Define prompts in agents/prompts.py and agent result schemas, but leave dispatch to the implementing LLM. The agent functions
  return empty lists. This is what the proposal does now — it's scaffolding, not implementation.

  Recommendation: Follow GTO's pattern (Option A). The SKILL.md should instruct Claude to spawn parallel agents, not try to dispatch
   from Python. The Python code provides schemas, prompts, and merge logic — Claude handles agent orchestration.

  ---
  3. Non-regex hook matching options

  From claude-hooks-v3.1.md lines 419-430:

  Exact string matching (no regex): If the matcher contains only letters, digits, underscores, and pipes (|), Claude Code evaluates
  it as an exact string match, bypassing the JavaScript regex engine entirely. This is ~10x faster.

  { "matcher": "Bash" }          // Exact match only
  { "matcher": "Edit|Write" }    // Exact match of Edit OR Write
  { "matcher": "*" }             // Match all (catch-all)

  Word-boundary matching with :*: The :* suffix provides prefix matching with word boundary:
  { "matcher": "Bash(ls:*)" }    // Matches "ls -la", NOT "lsof"

  if field for subcommand-level matching: Evaluated inside the engine before spawning a process:
  {
    "matcher": "Bash",
    "hooks": [{ "type": "command", "command": "./audit.sh", "if": "Bash(git *)" }]
  }
  When the if condition is false, the hook process is never spawned — zero overhead.

  In-process protocol: The GTO HOOKS_DISCOVERY.md (lines 49-65, 249-262) confirms that modern hooks support a run(data) -> dict |
  None contract. The hook exports both an in-process run() function AND a CLI __main__ entry point that reads stdin JSON and calls
  run().

  So the proposed diagnose hooks were half right — the run(data) contract exists — but they're missing the CLI wrapper and
  stdin/stdout JSON protocol. The fix is to add the __main__ block that reads stdin and prints JSON output, following the pattern at
   HOOKS_DISCOVERY.md line 249-262.

  ---
  4. RNS actual output contract

  From rns/core/render.py lines 338-408, the machine-parseable format is:

  <!-- format: machine -->
  RNS|D|{domain_num}|{emoji}|{label}
  RNS|A|{domain_num}{sub_letter}|{domain}|E:{effort}|{action}/{priority}|{description}|{file_ref}|owner={owner}|done={done}|caused_b
  y={caused_by}|blocks={blocks}|unverified={unverified}
  RNS|Z|0|NONE

  Key differences from what the proposed package's machine_render.py outputs:

  ┌──────────┬──────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────┐
  │  Aspect  │        Proposed          │                          Actual RNS (RNS|D|/RNS|A|/RNS|Z|)                           │
  │          │     (RNSD/RNSA/RNSZ)     │                                                                                      │
  ├──────────┼──────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ Separato │ No pipe separator        │ Pipe-delimited (|)                                                                   │
  │ r        │                          │                                                                                      │
  ├──────────┼──────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ Domain   │ RNSD1|docs               │ RNS|D|1|📄|DOCS                                                                      │
  │ header   │                          │                                                                                      │
  ├──────────┼──────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ Action   │ RNSA1a|docs|medium|title │ RNS|A|1a|docs|E:~5min|recover/high|desc|file:line|owner=X|done=0|caused_by=|blocks=| │
  │ item     │ |ref                     │ unverified=0                                                                         │
  ├──────────┼──────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ Terminat │ RNSZ0|NONE               │ RNS|Z|0|NONE                                                                         │
  │ or       │                          │                                                                                      │
  ├──────────┼──────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ Fields   │ 5 fields                 │ 12 fields including effort, done, caused_by, blocks, unverified                      │
  └──────────┴──────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────┘

  The proposed machine render format does not match the actual RNS contract. It uses the wrong prefixes, wrong separator style, and
  is missing 7 fields. To be compatible, it should import and use render_machine_format() from rns/core/render.py directly, or match
   the exact field layout.

  The human-readable format is also different. RNS uses emoji + numbered domain headers (1 🔧 QUALITY (2)) with sub-letter items
  (1a, 1b) grouped by action type (Recovery/Preserve/Future). The proposed render uses DOMAIN {count} with flat numbering. Not a
  blocking difference, but worth aligning.

  ---
  Updated Easy Fixes vs External Advice

  Revised easy fixes (incorporating what I now know):

  1. lib/ → __lib/ (naming convention)
  2. datetime.utcnow() → datetime.now(datetime.UTC)
  3. Freshness logic bug (boolean expression instead of SHA comparison)
  4. Import paths invalid
  5. Citation noise removal
  6. Health score arbitrary formula
  7. Scope guard marker creation in orchestrator
  8. Machine render format — align to actual RNS contract (RNS|D|/RNS|A|/RNS|Z| with 12 fields)
  9. Hook CLI wrappers — add __main__ blocks with stdin JSON read + stdout JSON output, following GTO's HOOKS_DISCOVERY.md pattern
  (lines 249-262)

  Remaining items needing external LLM advice:

  1. Name collision — the existing /diagnose is a different skill actively used by GTO's routing. Decision needed: rename, replace,
  or merge.
  2. Agent dispatch mechanism — follow GTO's Agent-tool pattern (SKILL.md instructs Claude to spawn), use /ai-pcli for multi-LLM, or
   keep as stubs.
  3. Stop hook completion detection — needs a better signal than "done"/"complete" string matching. What does the existing verify
  ecosystem use?"

## Assistant

You already did the hard part: the design review is correct, and the split between “easy local fixes” and “needs external advice” is sane. The three follow‑ups you’re now asking about are: (1) what exactly /diagnose collides with, (2) what the realistic agent‑layer contracts are, and (3) what non‑regex hook matching and hook protocols exist in your environment, plus the real RNS render contract.[1][2]

Below I’ll answer those three, then restate the easy‑fix vs “ask external LLM” line so you can hand this back out cleanly.

***

## 1. What /diagnose is colliding with

FACT (from your local review): the existing `/diagnose` skill in `P:\packages\cc-skills-sdlc\skills\diagnose\` is a structured debugging protocol, not a project health orchestrator.[3]

- Existing `/diagnose`:
  - Purpose: debugging / runtime error investigation.
  - Contract: list ≥3 hypotheses, design disconfirming tests, mark RULED_OUT / CONFIRMED, document the winner.[3]
  - Routing: GTO’s gap router sends `runtime_error` / `bug` style gaps to `/diagnose`, so it is a live dependency.[4]

- Proposed new skill:
  - Purpose: project or session health analysis.
  - Contract: gap detection, artifact writing, freshness‑aware reuse, action rendering, verification – essentially a project “health survey” orchestrator, not a single‑bug hypothesis tester.[5][6]

CONSEQUENCE: keeping the name `/diagnose` would overwrite an actively‑used debugging protocol and break GTO’s `runtime_error → /diagnose` routing. That’s not a naming nit; it’s an actual behavioral collision in your skill graph.[4]

CONSENSUS‑quality recommendation: new skill must not deploy under `/diagnose`. Options:

- Rename to something clearly project‑state oriented (`/health`, `/audit`, `/survey`, `/triage`, `/status`).
- Or make the new skill an internal module used by `/diagnose` when the gap type is “project health”, but don’t replace the existing debugging protocol surface.

You said “we’re not going to worry about overall scope fits right now,” so the only needed decision for the implementing LLM is: “do not reuse `/diagnose`; pick a new command name and adjust imports / paths accordingly.”

***

## 2. Agent‑layer contracts (realistic options)

Your review already captured the three real patterns; what matters now is what you want the *implementing* LLM to do:

### Option A – GTO‑style Claude Code Agent tool (recommended)

FACT: GTO spawns parallel subagents via Claude Code’s Agent tool (`Agent(subagent_type="gto-logic", prompt="...")`), and those agents write JSON to terminal‑scoped temp files that the orchestrator merges later.[5]

Key properties:

- Dispatch is driven from `SKILL.md`: Claude itself is instructed to spawn subagents of certain types with specific prompts.
- Each agent runs in isolated context, returns a small JSON result.
- Handoff is through the filesystem under `.claude/.artifacts/{terminal_id}/...` (or similar), matching your artifact pattern.
- Python orchestrator doesn’t spawn subagents; it just defines schemas and reads/merges results.

For the new skill, this means:

- Agent prompt + schema live in `__lib/agents/…`.
- `SKILL.md` explains when to create which subagent, and where they should write their JSON.
- Orchestrator:
  - waits for expected agent output files under the run’s artifact dir
  - validates them
  - merges them into the main `state.json` or step artifact.

This is the cleanest fit with your current ecosystem and Claude Code’s subagent model.[7][8]

### Option B – `/ai-pcli` multi‑LLM dispatch

FACT: your environment already uses `ai_cli.py` (or `/ai-pcli`) to fan out to Gemini, GPT, MiniMax, GLM, etc., and unify their outputs.

Properties:

- External orchestration – not Claude Code’s subagents.
- Agents are independent models; Claude just sees merged results.
- Good for adversarial or ensemble reasoning, but not a drop‑in replacement for the “Agent tool” concept inside Claude Code.

Use when:

- You want cross‑model diversity / voting.
- You’re okay with the complexity of another orchestrator.

For this particular package, this is optional; it’s not required for a working agent layer.

### Option C – “Prompt‑only” agent stubs (current situation)

FACT: your current package defines agent prompts + schemas, but the actual agent functions return empty results.[5]

- This is scaffolding, not an implementation.
- The orchestrator calls agents, but they always yield `[]` or empty `AgentResult`, so the “agent enrichment” phase is functionally a no‑op.

If you want agents to *matter*, Option C is not acceptable in the final implementation. At minimum, you should either:

- implement Option A (GTO‑style subagents) and wire prompts to writes; or
- explicitly remove the agent phase from the pipeline until you’re ready to add it.

CONSENSUS‑quality answer to “explain the different contracts” for the next LLM:

- “Claude Code Agent tool” = subagent pattern: spawn agents via `SKILL.md`, each writes JSON to specific artifact files, a Python orchestrator reads and merges.[8][7][5]
- “External LLM agent” = `/ai-pcli` style multi‑model execution, no Claude subagents, JSON aggregated by your own CLI.
- “Stub agents” = prompts + types only, no dispatch/IO wiring; current package is in this state and must be either implemented or removed.

***

## 3. Hook matching and protocol + RNS contract

### 3.1 Hook protocol and non‑regex matching

FACT: Claude Code hooks are subprocesses that receive JSON on stdin and can signal decisions either via exit codes or via JSON on stdout; the docs are explicit.[9][2][1]

Key rules from the hook reference:

- Input:
  - Hook gets a single JSON object on stdin describing the event (tool call, file edit, etc.).[2][1]
- Output:
  - If you want structured control, you must:
    - exit code 0, and
    - print a single JSON object to stdout as the **only** output.[1][2]
  - For many hooks, this JSON can include fields like:
    - `"decision": "allow" | "block" | "ask"` or
    - `"continue": true/false`, `"stopReason": "..."`, and similar policy flags.[10][2][1]
  - If you exit non‑zero (e.g., 2) and don’t rely on JSON, exit codes alone can signal block/allow.[11][1]

The GTO hook pattern you cited (“run(data) contract + CLI wrapper”) is compatible with this: the module exports `run(data) -> dict | None`, plus a `__main__` that:

- `json.load(sys.stdin)` into `data`
- calls `run(data)`
- prints JSON if there is a decision dict
- exits 0 so Claude Code reads the JSON.[12][2]

Non‑regex matchers:

- If `matcher` string is alphanumeric + `_` + `|`, it’s treated as exact matches (“Edit|Write” → exactly Edit or Write), not JS regex.[1][10]
- `"matcher": "*"` acts as a catch‑all.[1]
- Some advanced patterns let you use a separate `if` field to do subcommand‑level matching (e.g., match only `Bash(git *)` inside tool invocations), avoiding starting the hook process unless the condition is met.[2][1]

CONSEQUENCE for your package:

- The current `run(data)` hooks are only *half* correct: they must add a `__main__` wrapper with stdin‑in / stdout‑out JSON and proper exit‑code handling or Claude Code won’t ever call them properly.[12][2][1]
- You should convert any regex matchers to exact / prefix matchers where possible, both for performance and correctness.

### 3.2 RNS actual machine format

FACT: RNS’ current machine‑parsable format is:

```text
<!-- format: machine -->
RNS|D|{domain_num}|{emoji}|{label}
RNS|A|{domain_num}{sub_letter}|{domain}|E:{effort}|{action}/{priority}|{description}|{file_ref}|owner={owner}|done={done}|caused_by={caused_by}|blocks={blocks}|unverified={unverified}
RNS|Z|0|NONE
```

This is pulled from `rns/core/render.py` in your codebase.[5]

Key invariants:

- Prefixes: `RNS|D|`, `RNS|A|`, `RNS|Z|`.
- Separator: `|` (pipe), not concatenated prefix tokens.
- Domain header: `RNS|D|1|📄|DOCS` (integer domain index, emoji, LABEL).
- Action line: `RNS|A|1a|docs|E:~5min|recover/high|desc|file:line|owner=X|done=0|caused_by=|blocks=|unverified=0`.
- Terminator: `RNS|Z|0|NONE`.
- Machine format is intended to be deterministic, and there are 12 fields, including flags for effort, done, caused_by, blocks, and unverified.[5]

Your proposed `machine_render.py` format:

- Uses prefixes like `RNSD`, `RNSA`, `RNSZ`.
- Uses the wrong separator scheme (no pipe between tokens).
- Omits ~7 fields (effort, done, caused_by, blocks, unverified, etc.).
- Terminator shape is similar but not identical (`RNSZ0|NONE` vs `RNS|Z|0|NONE`).[5]

CONSEQUENCE: it is *not* wire‑compatible. Any downstream tooling that expects real RNS output (grep, parsers, dashboards) will not recognize your output.

So, for the implementing LLM, “machine render format” belongs in the **easy fixes** section, with a clear instruction:

- either import `render_machine_format()` from `rns/core/render.py`, or
- exactly replicate `RNS|D|…` / `RNS|A|…` / `RNS|Z|…` structure with all 12 fields and pipe separators, not the proposed shortened format.[5]

***

## Updated “easy fixes vs external advice” list

You already drafted this; here’s a compressed version in the language you can hand to another LLM as an implementation checklist.

### Easy local fixes (implement directly)

These do not require new product decisions or external design help:

1. **Directory naming**
   - Fix: rename all `lib/` dirs to `__lib/` and adjust imports, to match your global CLAUDE.md requirement and avoid `.gitignore` issues.

2. **Deprecated datetime**
   - Fix: replace every `datetime.utcnow()` with `datetime.now(datetime.UTC)` in models/orchestrator.[5]

3. **Freshness bug**
   - Current: `artifact_git_sha = state.current_target and state.current_target and git_sha`
   - Fix: pass the actual stored artifact SHA: e.g., `artifact_git_sha = state.current_target_git_sha` (or the appropriate field) and compare against a newly computed repo SHA.

4. **Import paths**
   - Fix: replace invalid `P._claude.skills.diagnose...` style imports with valid relative or absolute imports consistent with your actual package layout (e.g., `from __lib.models import State`).

5. **Citation noise**
   - Fix: remove all `[cite:...]` markers from code and SKILL docs; they don’t carry operational semantics.

6. **README policy**
   - You chose to keep the README despite your CLAUDE.md guideline; the only “fix” is: leave it, but note the exception so future reviews don’t keep flagging it.

7. **Health score formula**
   - Fix: either:
     - replace `100 - findings_count * 7` with a TODO + stubbed constant, or
     - use a severity‑weighted formula based on actual finding weights, or
     - remove the score entirely until real scoring logic is designed.
   - For now, simplest: return `None` or a basic "informational only" score and document that scoring will be added later.

8. **Scope guard**
   - Fix: in orchestrator startup, create the “diagnose‑active” (or new skill name) marker file inside the artifact run directory; in orchestrator shutdown, remove it.
   - Ensure hooks check for this actual path so they become active when a run is in progress.

9. **Machine render format**
   - Fix: implement real RNS machine format by either using `rns/core/render.py` or exactly matching `RNS|D|…`, `RNS|A|…`, `RNS|Z|…` with the proper fields and pipes.[5]

10. **Hook CLI wrappers**
    - Fix: for each hook:
      - implement a `run(data: dict) -> dict | None`,
      - add a `main()` that loads JSON from `sys.stdin`, calls `run`, dumps any decision dict to stdout as JSON, and exits 0,
      - wire hooks in `.claude/settings.json` or `SKILL.md` with appropriate matchers (prefer non‑regex patterns where possible).[2][12][1]

These are all relatively mechanical changes you can instruct an implementing LLM to apply directly.

### Items needing external / higher‑level input

These require real design decisions or reading more of your ecosystem, not just mechanical edits:

1. **Name collision**
   - Decision: pick a new command name for the project health orchestrator vs. existing debugging `/diagnose`. You must decide UX and routing, not just code.[3][4]

2. **Agent dispatch mechanism**
   - Decision: adopt GTO’s Agent‑tool pattern (SKILL.md‑driven subagents writing JSON to artifacts), use `/ai-pcli` multi‑model dispatch, or keep agents disabled for now.
   - This affects how many moving parts you want and where orchestration lives.[5]

3. **Stop hook completion detection**
   - Current: naive “if ‘done’ or ‘complete’ in response.lower()”.
   - Decision: choose a more reliable completion signal, ideally one consistent with whatever your existing verify / RNS / GTO ecosystem uses (e.g., a specific marker tag in output, a status field in JSON, or a particular RNS action set).

4. **Machine render alignment with RNS ecosystem**
   - You now know the correct RNS format; you still need to decide whether this skill:
     - depends directly on RNS (importing its renderer), or
     - keeps its own renderer and ensures compatibility manually.

5. **(Deferred by you) Overall scope fit**
   - This is the overlap with `/rca`, `/tldr-*`, `/sqd`, `/uci` that you explicitly parked for now.

You’ve already said: “we’re not going to worry about the overall scope fits right now… we’re going to keep the README.” So the practical instruction for the next LLM is: **do only the easy fixes, do not rename the skill or change agent/stop‑hook semantics until you come back with new product decisions**.

***

If you want, next I can:

- draft a **concrete patch plan** you can paste into Claude as “apply these 10 edits to the existing package,” or  
- write a **CLI checklist** that your hooks/runner can use to self‑validate (directory names, datetime usage, RNS format, hook wrappers) before you consider the package deployable.

## Human

We are renaming gto to gto-old, so we can reuse the gto name.

"Agent dispatch mechanism", /ai-pcli are external LLMs used via their cli or PI agent harness.  They are gemini, codex, m2.7, and glm-5.1.  What do you think between agents and external LLMs has the greatest chance of a happy path?

"Machine render alignment with RNS ecosystem" you decided what is the better path.  I like long term optimal outcomes.

## Assistant

For what you described, I’d put **Claude Code agents/subagents as the primary happy path**, and treat `/ai-pcli` external LLMs as an *occasional specialist tool* behind an MCP/CLI bridge. [1][2] For RNS alignment, the long‑term optimal path is to **delegate machine rendering to the existing RNS implementation** (or exactly mirror its `RNS|D` / `RNS|A` / `RNS|Z` semantics), not invent a parallel format.[3]

***

## Agents vs `/ai-pcli` external LLMs

### What “happy path” means in your context

Given your goals (terminal‑scoped artifacts, compact immunity, hooks, skills, MCP, multiple terminals), “happy path” here really means:

- Lowest moving‑parts count in the critical path.
- Best debuggability from *inside* Claude Code (single master loop).[1]
- Fewer external failure modes (auth, rate limits, CLI breakage).
- Predictable cost/latency for a given diagnostic run.
- Consistent behavior across sessions for the same skill.

On those axes, **Claude Code agents/subagents win as the default**.

### Why agents/subagents should be primary

Consensus from current usage patterns and docs:

- Claude Code is explicitly optimized around a **single orchestrator loop** that can spawn subagents or invoke tools and then merge their results back into a coherent narrative.[4][1]
- Subagents are designed for **isolated, well‑scoped tasks** with clear prompts and low cognitive load: “go read this file set and return a schema,” “review this summary against the source,” etc.[5][2]
- Agent teams (if you go that far) add collaboration, but for your pipeline the simpler pattern “one orchestrator + a few subagents” is enough.[2][5]

Advantages vs `/ai-pcli`:

- **Fewer orchestration layers:** you stay inside Claude Code—no extra CLI process tree, no model‑by‑model retry logic, no extra artifacts to track which model said what.[1]
- **Tighter integration with hooks and skills:** skill frontmatter can describe when to spawn an agent; hooks can snapshot the resulting artifacts; everything is visible in one place.[6][7]
- **Simpler invariants:** each subagent writes one JSON file into your `.artifacts/{terminal_id}/{skill}/{run_id}/agents/…`, and that’s it. No need to worry about per‑model differences in format or failure semantics.

Where agents/subagents struggle a bit:

- You’re still limited to Claude’s training distribution; you don’t get cross‑architecture “ensemble” benefits. Multi‑LLM work shows real gains in reliability and diversity when you combine models, but that’s a second‑order concern compared to “does the pipeline even run reliably through compact/hooks.”[8][9]

### Where `/ai-pcli` external LLMs make sense

The multi‑model literature and practices suggest external ensembles shine when you care about **cross‑model agreement or divergence metrics**, not just one model’s view.[9][8]

For your skill, `/ai-pcli` is probably best used for:

- **Adversarial or second‑opinion phases only**, e.g.:
  - “Run the same health diagnosis prompts through Gemini, GLM, M2.7, etc., and report where they disagree with Claude’s assessment.”
  - “Ask a separate model to critique the action plan for missing risk types.”
- **Specialized domains** where you already know one model is superior (e.g., Gemini for certain UI text, or a code‑tuned model for specific languages).[9][1]
- **Post‑verification checks**: ensemble agreement can be a high‑value signal after your core pipeline passes internal sanity checks.[8][9]

Downsides as primary:

- More plumbing: you need CLI execution, error handling, concurrency limits, per‑model config, and pathing for artifacts.
- More external points of failure: network, credentials, rate limits, CLI behavior changes.
- Higher cognitive load to debug: when something looks off, is it the orchestrator, Claude, Gemini, glm‑5.1, or your merger?

Given your emphasis on **deterministic‑first, artifact‑backed state machines**, agents/subagents inside Claude Code are the better “happy path,” and `/ai-pcli` becomes a **controlled escalation tool**, not the baseline.

**Recommendation:**  
Design the skill so that:

- Phase machine and main reasoning rely on **Claude + subagents**.  
- `/ai-pcli` is only invoked in explicit optional steps (e.g., `/health verify with external models`, or an “ensemble review” phase), wired via a dedicated MCP or tool wrapper so it’s clearly off the main path.

***

## Machine render alignment with RNS

You asked me to pick the long‑term optimal path. That’s unambiguous here: **do not fork the RNS machine format.** Either:

1. Import and call the real RNS renderer; or  
2. Implement a faithful clone of its `RNS|D` / `RNS|A` / `RNS|Z` DSL and commit to tracking its evolution.

### Why reusing RNS is better

From your own RNS code:

- Machine format is:

  - `RNS|D|{domain_num}|{emoji}|{label}`
  - `RNS|A|{domain_num}{sub_letter}|{domain}|E:{effort}|{action}/{priority}|{description}|{file_ref}|owner={owner}|done={done}|caused_by={caused_by}|blocks={blocks}|unverified={unverified}`
  - `RNS|Z|0|NONE`.[3]

- Downstream tooling (parsers, viewers, grep patterns, possibly dashboards) is already calibrated to that exact structure—including extra fields you omitted in the proposal (effort, done, caused_by, blocks, unverified).[3]

If you diverge, you get:

- Two partially overlapping DSLs (`RNSD…` vs `RNS|D|…`), forcing every downstream tool to support both or to ignore one.
- Fragiler evolution: if RNS adds a new field (e.g., `confidence`), your fork will immediately go stale unless you also update it.
- More surface area to debug when RNS changes and your skill’s output no longer matches what `rns core` expects.

Given you explicitly value **one canonical schema, one renderer, explicit evidence**, the long‑term best outcome is:

- Treat RNS as the **single authority** on the machine render format.
- Have your diagnosing skill **produce canonical RNS action objects** in JSON, then reuse RNS to render them into human and machine views.

### Concrete long‑term plan

1. **Internal schema:**  
   - Your skill’s internal state should produce a normalized JSON that is as close as possible to the RNS action model:
     - `domain`, `domain_idx`, `emoji`, `label`
     - `id` (e.g., `1a`)
     - `effort` (string or structured)
     - `action_type` (`recover`, `preserve`, `future`)
     - `priority`
     - `description`
     - `file_ref` (or `None`)
     - `owner`
     - `done` (bool/int)
     - `caused_by`
     - `blocks`
     - `unverified` (bool/int).[3]

2. **Render layer:**  
   - In Python, either:
     - import `render_machine_format()` (or equivalent) from `rns/core/render.py` and pass this JSON; or
     - implement a small, well‑tested clone that emits exactly the same `RNS|D` / `RNS|A` / `RNS|Z` strings.

3. **Skill behavior:**
   - The skill’s user‑visible output can be the human RNS format (domains + numbered bullets).
   - The machine output is the RNS pipe‑delimited lines, written to artifact files under the run directory.

4. **Versioning:**
   - If you’re worried about RNS changing, pin a minimum RNS version in your skill’s internal docs and add a tiny “self‑test hook” that validates the machine format structure against one sample.

Short term, if importing RNS is annoying due to pathing, a faithful static implementation is fine; it’s still better than a divergent DSL, as long as the semantics match.

**Recommendation:**  
- **Do not** keep the RNSD/RNSA/RNSZ variant.  
- **Do** make your skill either:
  - call the canonical `rns` renderer, or
  - emit exact `RNS|D|…` / `RNS|A|…` / `RNS|Z|…` lines as if they came from RNS, including all fields.

***

## Putting it together for your next implementation pass

If you roll those decisions into the earlier checklist, I’d update the “needs external advice” items as:

- Name collision: now you’re renaming `gto` → `gto-old` to reuse the name; for this skill, just don’t use `/diagnose` for project health.
- Agent dispatch: **choose Claude Code agents/subagents as the happy path**, `/ai-pcli` as optional specialist/tool phases.
- RNS alignment: **reuse the real RNS machine format** (import or faithful clone), don’t maintain a separate DSL.

The next concrete piece of work that would move this forward is:

- Define the **canonical JSON schema** your skill will produce per action, aligned to RNS fields.
- Define 2–3 **agent roles** that feed into that schema (e.g., “health domains enumerator”, “per‑domain gap extractor”, “RNS actionizer”), assuming Claude Code subagents as the dispatch mechanism.

Would you like me to draft that canonical JSON schema + the 2–3 agent roles next, assuming agents are Claude Code subagents and RNS is the renderer of record?

## Human

"
  The existing ecosystem doesn't use string-matching "done"/"complete" at all. Here's what it actually uses:

  1. GTO's verify wrapper (gto_verify_wrapper.py) checks for artifact file existence — it looks for gto-artifact-*.json and runs
  assertions against it. It doesn't parse the response text at all.
  2. RNS uses structured action dispositions — each action gets a done boolean field. Completion is tracked by checking whether all
  actions have done=True, not by parsing prose.
  3. The existing stop hooks (Stop.py, stop_success_validator.py, etc.) check for specific claim patterns like "all tests pass" or
  "implementation complete" combined with evidence verification — they look for actual tool output, not just words.

  My recommendation: Don't detect completion from response text at all. Instead:

  - Use a state flag — the orchestrator writes verification_required: true to terminal-scoped state (the proposed package already
  has this field). The stop hook checks the state file, not the response text.
  - The stop hook runs the assertions script (lib/assertions.py), which checks the artifact for structural completeness (artifact
  exists, health score present, findings list present, coverage present).
  - If assertions fail, block with a specific message about what's missing.
  - If no verification is required (state says verification_required: false), pass through silently.

  This matches how GTO's verify wrapper actually works — it checks artifact state, not prose. The proposed package already has the
  right state field (verification_required), the hook just needs to use it instead of string-matching."

## Assistant

Yes — that recommendation is the right one. The best fix is to **stop treating prose as completion evidence** and move completion gating to **artifact/state verification**, because that matches both your existing ecosystem and Claude Code’s hook model.[1][2]

## Recommended completion contract

Your ecosystem already uses structured evidence, not textual vibes: GTO verify checks artifacts, RNS tracks per-action `done`, and Stop-style validators verify actual claims against tool outputs or state rather than parsing generic “done/complete” prose. Claude Code hooks are also designed to make structured block/allow decisions based on stdin JSON plus local checks, which fits a state-driven quality gate much better than string matching.[2][3][1]

So the contract should be:

- Orchestrator owns truth:
  - writes `verification_required: true|false`
  - writes artifact paths
  - writes current phase / run id / validation status.
- Stop hook is a gate:
  - if verification not required, allow silently
  - if verification required, run assertions against artifacts/state
  - block only when required evidence is missing or invalid.[4][1]
- Human response text is **never** a completion signal.

## Why text matching is wrong

String matching on `"done"` / `"complete"` is brittle because it has false positives and false negatives, and Claude Code hooks can instead use structured JSON or exit-code gating based on actual state. Your own review gives better existing precedents: file existence plus assertions in GTO, explicit `done` booleans in RNS, and evidence-backed success validators in Stop hooks.[3][1][4]

That means this:

```python
if "done" in response.lower() or "complete" in response.lower():
    ...
```

should be deleted, not refined.

## Best implementation

The strongest pattern is:

1. The orchestrator writes terminal-scoped state under `.claude/.artifacts/{terminal_id}/{skill}/state.json` with fields like:
   - `run_id`
   - `phase`
   - `verification_required`
   - `expected_artifacts`
   - `verification_status`
   - `last_verified_at`.

2. The Stop hook reads stdin JSON from Claude Code, resolves the correct artifact root, then checks state first, not Claude’s text.[5][1]

3. If `stop_hook_active == true`, immediately allow, to avoid infinite loop behavior in repeated Stop gating.[6]

4. If `verification_required == false`, allow.

5. If `verification_required == true`, run your assertions module against the expected artifacts.

6. If assertions pass:
   - optionally write `verification_status: "passed"`
   - allow.[3]

7. If assertions fail:
   - emit a structured block response with a precise reason about missing evidence or invalid artifact structure.[1][2]

## State shape

A minimal state file could look like this:

```json
{
  "skill": "gto",
  "run_id": "2026-04-25T20-52-00Z",
  "phase": "verify",
  "verification_required": true,
  "verification_status": "pending",
  "expected_artifacts": [
    ".claude/.artifacts/wt-10844/gto/outputs/health.json"
  ],
  "assertion_profile": "gto_default"
}
```

This is consistent with your terminal-scoped artifact pattern and gives the Stop hook a deterministic source of truth.

## Stop hook logic

Claude Code’s hooks docs say Stop hooks can block using structured JSON output, and the guidance around Stop hooks emphasizes using them as quality gates rather than passive notifications. So the logic should be:[4][6][1]

```python
def run(data: dict) -> dict | None:
    if data.get("stop_hook_active") is True:
        return {"decision": "allow"}

    state = load_state_for_terminal(...)
    if not state:
        return {"decision": "allow"}

    if not state.get("verification_required", False):
        return {"decision": "allow"}

    result = run_assertions(state)

    if result.ok:
        mark_verified(state)
        return {"decision": "allow"}

    return {
        "decision": "block",
        "reason": (
            "Verification required but assertions failed. "
            f"Missing or invalid: {', '.join(result.failures)}. "
            "Continue working and regenerate the required artifacts."
        )
    }
```

That fits Claude Code’s structured hook control model and aligns with your “deterministic-first” approach.[2][1]

## Assertions behavior

Your proposed `lib/assertions.py` idea is exactly the right place to centralize structural checks, because the Stop hook should be thin and deterministic. Assertions should check things like:[3]

- artifact file exists
- JSON parses
- required top-level keys exist
- key lists are non-empty where required
- expected render outputs exist
- freshness markers match current input hash when relevant.[3]

For a health-style artifact, that might mean:

- `health_score` present, or explicitly null if scoring disabled
- `findings` present and list-shaped
- `coverage` present
- `generated_at` present
- optional RNS machine output exists if rendering is part of completion.[3]

## Why this is better than prose-based hooks

This approach is better for three reasons:

- It is consistent with how GTO and RNS already express truth: artifacts and structured flags, not conversational language.[3]
- It survives compaction and multi-terminal work because the state lives in `.artifacts/{terminal_id}/...` rather than in transient assistant prose.
- It is easier to debug because failures become assertion failures with explicit missing fields, not opaque “Claude didn’t sound done enough” heuristics.[7][4]

## What to tell the other LLM

You can hand off this instruction almost verbatim:

- Remove all response-text completion detection.
- Treat `verification_required` in terminal-scoped state as the only trigger for Stop verification.
- Stop hook must:
  - read stdin JSON
  - short-circuit if `stop_hook_active == true`
  - load terminal-scoped state
  - if `verification_required == false`, allow
  - if `verification_required == true`, run assertions against expected artifacts
  - block with a precise reason if assertions fail
  - allow and optionally mark verified if assertions pass.[6][1]

That is the long-term correct path, not just a patch.

If you want, I can next write the actual **Claude Code Stop hook Python file** plus a matching `assertions.py` skeleton in your preferred artifact-path style.

## Human

Please provide a prompt I can give to the implemetning LLM that containes everything it needs to know to understand the updated solution, so we can start and finish the implementation.

## Assistant

Use the prompt below as the implementation handoff. It captures the updated decisions: reuse `gto` by renaming the old one to `gto-old`, prefer Claude Code subagents as the primary happy path, treat external `/ai-pcli` LLMs as optional escalation, use artifact/state verification instead of response-text completion detection, and align machine rendering to the canonical RNS contract instead of inventing a parallel DSL.[1][2][3]

## Implementation handoff prompt

```text
You are implementing a production-grade Claude Code skill package update.

Your job is to START AND FINISH the implementation, not provide high-level advice.
Make the minimum necessary changes for a correct long-term architecture.
Prefer correctness, deterministic behavior, and compatibility with the existing ecosystem over novelty.

==================================================
GOAL
==================================================

Implement the updated solution for the new GTO package using these decisions:

1. The old GTO is being renamed to gto-old, so the name gto is now available for reuse.
2. Do NOT use or overwrite the existing /diagnose debugging skill for this new work.
3. Primary happy path for “agents” = Claude Code subagents / Agent tool pattern.
4. External LLMs via /ai-pcli (Gemini, Codex, M2.7, GLM-5.1) are OPTIONAL escalation tools, not the default path.
5. Completion detection must NOT use response-text string matching such as “done” or “complete”.
6. Completion / verification gating must use terminal-scoped state + artifact assertions.
7. Machine render output must align to the ACTUAL RNS ecosystem contract, not a custom variant.
8. Internal library directories must use __lib, not lib.
9. Keep the README.md even if an older policy suggested otherwise.
10. Prefer long-term optimal architecture, but do not over-engineer beyond what is needed to get a correct deployable implementation.

==================================================
REQUIRED ARCHITECTURAL DECISIONS
==================================================

A. SKILL NAME / SURFACE
- Reuse the name gto for the new package.
- The previously existing GTO is being renamed to gto-old externally.
- Do not change the /diagnose debugging protocol skill; it is separate and still needed.

B. AGENT DISPATCH MECHANISM
- Use Claude Code subagents / Agent tool as the PRIMARY agent pattern.
- This means:
  - SKILL.md instructs Claude when to spawn subagents.
  - Subagents are isolated workers.
  - They write structured JSON artifacts into terminal-scoped artifact directories.
  - The main orchestrator merges validated outputs.
- Do NOT make external /ai-pcli multi-LLM fanout the default critical path.
- External LLMs may be implemented only as an optional secondary verification / adversarial review mode.

C. COMPLETION / STOP-HOOK CONTRACT
- Do NOT detect completion from assistant prose.
- Delete any logic like:
  if "done" in response.lower() or "complete" in response.lower()
- Instead:
  1. Orchestrator writes terminal-scoped state with verification_required: true|false
  2. Stop hook reads state, not prose
  3. If verification_required is false -> allow silently
  4. If verification_required is true -> run assertions against expected artifacts
  5. If assertions fail -> block with precise reason
  6. If assertions pass -> allow and optionally mark verification_status=passed
- This must align with the existing ecosystem pattern:
  - GTO verify wrapper verifies artifacts, not text
  - RNS tracks done via structured fields
  - Stop validators verify evidence, not conversational wording

D. MACHINE RENDER CONTRACT
- Do NOT use custom prefixes like RNSD / RNSA / RNSZ.
- Align to the actual RNS machine format:

  <!-- format: machine -->
  RNS|D|{domain_num}|{emoji}|{label}
  RNS|A|{domain_num}{sub_letter}|{domain}|E:{effort}|{action}/{priority}|{description}|{file_ref}|owner={owner}|done={done}|caused_by={caused_by}|blocks={blocks}|unverified={unverified}
  RNS|Z|0|NONE

- Best path:
  - Prefer importing and using the real RNS renderer if practical.
  - If direct reuse is impractical, implement an EXACT compatible renderer with the same semantics and fields.
- Do not invent a parallel DSL.

E. ARTIFACT / STATE MODEL
- Canonical state must live under:
  .claude/.artifacts/{terminal_id}/gto/
- Use terminal-scoped artifacts for:
  - multi-terminal isolation
  - stale-data immunity
  - recovery from compact events
  - resumability
- Do not rely on conversation state as source of truth when artifact state exists.

==================================================
CRITICAL FIXES TO APPLY
==================================================

Apply these fixes directly:

1. Rename all internal lib/ directories to __lib/
2. Replace datetime.utcnow() with datetime.now(datetime.UTC)
3. Fix the freshness logic bug where a boolean expression is used instead of the actual stored artifact git SHA
4. Fix invalid import paths so tests and runtime imports are real Python imports
5. Remove citation markers like [cite:143] [cite:144] from implementation files
6. Keep README.md
7. Replace or remove the arbitrary health score formula:
   - avoid magic constants like findings_count * 7
   - simplest acceptable path: make score optional / informational unless a justified weighted model exists
8. Fix scope guard activation:
   - if scope guards are still used, ensure the marker file is actually created and cleaned up
   - if a cleaner state-based guard fully replaces marker files, do that instead
9. Replace machine rendering with actual RNS-compatible machine rendering
10. Rewrite hooks so they work with Claude Code’s real subprocess protocol

==================================================
CLAUDE CODE HOOK REQUIREMENTS
==================================================

Claude Code hooks are subprocess-oriented.

Implement hooks correctly:
- Read JSON from stdin
- Return control via:
  - exit codes, or
  - structured JSON to stdout on exit 0
- Do NOT print extra text to stdout if using JSON control output
- Add real CLI entry points:
  - if __name__ == "__main__": main()

Preferred hook implementation pattern:
- Each hook module may expose:
  run(data: dict) -> dict | None
- But it MUST also include:
  - stdin JSON parsing
  - stdout JSON emission
  - proper exit behavior

Use non-regex matchers where appropriate:
- Prefer exact or simple matcher forms when enough
- Avoid unnecessary regex if exact / constrained matching works

Hooks should be thin adapters over deterministic logic in __lib, not giant policy blobs.

==================================================
STOP HOOK REQUIREMENTS
==================================================

Implement Stop hook using artifact/state verification only.

Required behavior:
1. Read event payload from stdin
2. If stop_hook_active is true, allow immediately to avoid loops
3. Resolve terminal-scoped state for current gto run
4. If no active state or verification_required is false -> allow
5. If verification_required is true:
   - run assertions against expected artifacts
   - if assertions pass:
     - mark verification_status passed if applicable
     - allow
   - if assertions fail:
     - block with a specific reason listing what is missing or invalid

Do not inspect assistant prose for completion.

==================================================
AGENT LAYER REQUIREMENTS
==================================================

The previous package had empty agent scaffolding. That is not acceptable.

Implement one of these two acceptable outcomes:

Preferred:
- Real Claude Code subagent workflow
- At least the minimal useful agent roles are wired end-to-end
- Agents write structured results to artifact files
- Orchestrator validates and merges them

Fallback:
- If fully wiring agents is too risky for this pass, remove agent enrichment from the critical path entirely
- Do NOT leave fake agent stages that return empty results while pretending to enrich output

Recommended minimal subagent roles:
1. domain-analyzer
   - identify project health / gap domains from evidence
2. findings-reviewer
   - review findings for missing evidence, duplication, false positives
3. action-normalizer
   - convert accepted findings into canonical action objects suitable for RNS rendering

Each should produce small structured JSON, not prose dumps.

==================================================
RNS ALIGNMENT REQUIREMENTS
==================================================

Long-term optimal path:
- Treat RNS as the canonical renderer for machine action output.
- This package should produce normalized action objects and then render them through the RNS-compatible layer.

Therefore:
- Keep internal normalized JSON schema close to RNS action semantics:
  - domain
  - domain_idx
  - emoji
  - label
  - id/sub-id
  - effort
  - action_type
  - priority
  - description
  - file_ref
  - owner
  - done
  - caused_by
  - blocks
  - unverified
- Then render to exact RNS machine lines.

If importing actual RNS code is feasible, do that.
If not, implement an exact compatible renderer and cover it with tests.

==================================================
STATE / ARTIFACT CONTRACT
==================================================

Use terminal-scoped canonical state similar to:

.claude/.artifacts/{terminal_id}/gto/
  active_run
  state.json
  phase.txt
  inputs/
  outputs/
  receipts/
  checkpoints/
  logs/
  flags/

Minimum state fields:
- skill
- run_id
- phase
- verification_required
- verification_status
- expected_artifacts
- source fingerprint / git SHA if needed for freshness
- timestamps
- optional current target metadata

Receipts should separate “artifact exists” from “artifact accepted”.

==================================================
IMPLEMENTATION PRIORITIES
==================================================

Priority order:
1. Make package runtime-correct
2. Make hooks actually work in Claude Code
3. Make state / verification deterministic
4. Make machine rendering truly RNS-compatible
5. Make agent layer real or remove it from critical path
6. Clean imports, naming, and freshness logic
7. Preserve existing ecosystem compatibility

==================================================
OUTPUT EXPECTATIONS
==================================================

Do not just describe what you would do.
Produce the implementation changes.

At minimum, deliver:
- Updated SKILL.md
- Updated hook files with real CLI stdin/stdout behavior
- Updated __lib package layout
- Fixed orchestrator/state/assertions logic
- RNS-compatible machine renderer
- Agent implementation or explicit removal from critical path
- Updated tests or test scaffolding sufficient to validate the new contracts

When making tradeoffs:
- prefer a smaller correct implementation over a larger fake one
- prefer deterministic artifact/state contracts over clever prompt behavior
- prefer real compatibility with existing RNS/GTO ecosystem over parallel reinvention

==================================================
ASSUMPTIONS YOU MUST FOLLOW
==================================================

- The old GTO is being renamed to gto-old, so gto is available.
- /diagnose remains a separate debugging skill and must not be overwritten or semantically replaced.
- README.md stays.
- External /ai-pcli models are optional tools, not the default agent path.
- Stop/completion verification is artifact/state-driven, not prose-driven.

Now inspect the current implementation package, apply these decisions, and produce the finished implementation.
```

## Notes for the implementing LLM

The prompt tells it to implement, not brainstorm, and it encodes the key updated decisions: hook subprocess protocol, artifact-driven stop verification, primary use of Claude Code subagents, and canonical RNS machine rendering. It also explicitly removes ambiguity about `/diagnose`, `gto`, `README.md`, and `/ai-pcli`, which were the major sources of drift in the previous package review.[2][3][4][5][1]
