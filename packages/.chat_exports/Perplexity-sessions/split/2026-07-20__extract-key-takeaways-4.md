---
title: "Extract key takeaways"
date: "2026-07-20"
mode: "COPILOT"
uuid: "6814c0a3-a350-40db-88c8-5c9364f58fc1"
entry_count: 3
---

## Human

Extract key takeaways

## Assistant

You can treat this video as a concise playbook for “distilling Fable’s process into reusable skills and model routing”, rather than a tutorial about Fable’s raw intelligence.[1]

## Core strategic takeaways

- **Process is the moat, not the model**  
  Fable 5 is very strong, but the advantage comes from how you instruct it, the systems around it, and the loops you build—not just raw model IQ. A great engineer with a weaker model will outperform a beginner with a stronger one because of better system design and prompting discipline.[1]

- **You can keep the process even if you lose the model**  
  Access to Fable may be temporary, but you can permanently codify its habits (scoping, evidence, adversarial reasoning, verification, reporting) into skills that other models run—Opus, Sonnet, GPT, or even open‑source LLMs.[1]

- **Treat frontier models as teachers, not workhorses**  
  Use Fable like a senior engineer or “officer”: have it design workflows, critique setups, and package its methodology into skills that cheaper “junior” models then execute. This lets you retain its thinking style while delegating execution to cheaper models.[1]

## Effort levels and cost–quality tradeoffs

- **Effort level matters as much as model choice**  
  Anthropic’s own release charts show that Fable 5 on low effort can be roughly comparable to Opus 4.8 on high effort in quality, but at different cost points. So you should tune effort levels deliberately rather than always maxing them out.[1]

- **Higher effort is not always better**  
  At very high effort (e.g., “x higher max”), Fable/Opus can overthink, run much longer, and get more expensive, sometimes producing worse results than a more moderate setting. This reinforces that you should actively experiment and calibrate, not accept defaults.[1]

- **Model routing is a core skill for unit economics**  
  The goal is to match task difficulty to just‑enough intelligence and effort, so cheaper models handle work they’re capable of, while frontier models handle planning, judgment, or rare edge cases. This is positioned as a key differentiator for teams optimizing AI budgets.[1]

## “Fable mode” skill concept

- **Extract great Fable sessions into reusable skills**  
  When you get a deliverable from Fable that feels unusually good, you should have Fable or Opus analyze: how it scoped, what evidence it gathered, what reasoning it used, how it verified, and what made the output “tasteful”. Then you turn that into a skill file—“Fable mode”—that encodes this discipline.[1]

- **Five gates: scoping, evidence, attacking, verifying, reporting**  
  The Fable‑mode skill implements these gates so any model can follow Fable’s working discipline. For example: scope before working, gather evidence before reasoning, reason adversarially (devil’s advocate), verify before declaring done, and then calibrate/reflect.[1]

- **Skill as portable methodology across models**  
  Once defined, this skill can be run by Opus 4.8, GPT 5.5, or even local/open source models. The video claims Opus 4.8 with Fable‑mode “feels elevated” compared to vanilla Opus because it inherits Fable’s workflow, not its raw weights.[1]

## Practical model routing patterns

- **Define a routing table of all models in your toolkit**  
  The suggested pattern is to create a table listing each available model, its relative cost score, intelligence, and “taste” (creativity, UX sense, out‑of‑box thinking). You can extend this with custom dimensions aligned to your workflows.[1]

- **Use smart orchestrators with cheap executors**  
  Examples in the video:  
  - Fable orchestrating Opus and Sonnet agents can perform similarly to Fable orchestrating Fable agents, at much lower cost.[1]
  - Opus orchestrating Haiku “scout” agents produced essentially identical results to more expensive configurations, at roughly three times cheaper cost in one test.[1]

- **Dynamic workflows as the backbone**  
  The pattern is: a high‑end orchestrator (Fable or Opus with Fable‑mode) designs the workflow, explores what could go wrong, then delegates actual execution to cheaper models (Sonnet, Haiku, etc.) which report back for further planning. This loop is what makes cheaper teams competitive with all‑frontier setups.[1]

## Ownership and robustness mindset

- **You don’t own SaaS models; you own systems and hardware**  
  With Fable going behind subscriptions and governance increasing, the video stresses that you can’t rely on permanent access to any one proprietary frontier model. What you can own are: your processes, methodologies, and local hardware + open‑source models.[1]

- **Focus on portable abstractions**  
  By encoding your best practices into skill files and routing tables, your stack becomes resilient: you can swap models while keeping the same epistemic discipline and cost‑aware routing. This reduces the risk of platform changes or model withdrawals disrupting your workflows.[1]

If you want, I can help you sketch a concrete “Fable‑mode” skill file tailored to your current Claude Code + multi‑provider routing setup, based on these five gates and your own preferred verification habits.

## Human

How can we use the material in the transcript and turn it into a reusable skill that can be used across multiple use cases?

## Assistant

We can turn this into a reusable “Fable‑mode” skill by distilling the transcript into a small, model‑agnostic protocol: five gates, effort calibration, and routing hints that any model can follow for any nontrivial task.[1]

Below I’ll outline the structure, then give you a concrete skill template you can adapt for Claude Code, GPT, or local LLMs.

## 1. Extract the durable behaviors

The transcript gives us repeatable behaviors that are independent of Fable’s weights.[1]

From the video, the durable behaviors are:[1]

- **Scoping first**  
  Always clarify the goal, constraints, and unknowns before working. Distinguish between simple linear planning and adversarial “what could go wrong?” exploration.[1]

- Evidence before reasoning  
  Don’t treat vague recall as current knowledge; explicitly gather or check sources and confirm files actually exist before reasoning.[1]

- Adversarial reasoning  
  Play devil’s advocate against the plan and outputs, proactively exploring failure modes and unknowns.[1]

- Verification before declaring done  
  Re‑check accuracy and alignment to the goal before “shipping”, rather than assuming the first coherent answer is good enough.[1]

- Calibrated reporting  
  Answer first, then briefly note what might be wrong and ask at most one clarifying question, staying focused on the user’s problem.[1]

- Effort level awareness  
  Adjust depth of reasoning and number of iterations depending on task difficulty, not blindly maxing out effort.[1]

- Model routing mindset  
  Treat the “smart” model as planner/teacher/orchestrator and cheaper models as executors; match intelligence + effort to task difficulty.[1]

These behaviors are what we encode into a skill file so any model can “act Fable‑like” on arbitrary tasks.

## 2. Define the generic Fable‑mode skill

Here’s a reusable skill specification you can adapt to Claude skills, MCP tools, or your own orchestration layer. I’ll write it in a neutral JSON‑ish format you can translate into your preferred schema.

### Skill: FableMode

**Purpose**  
Make a model operate with Fable‑like judgment, planning, verification, and reasoning habits across arbitrary tasks, using five gates: scoping, evidence, attacking, verifying, reporting.[1]

**Invocation hint**  
Use for any task that is:  
- Ambiguous or open‑ended  
- High stakes (quality matters more than latency)  
- Multi‑step, with nontrivial risk of failure

### Skill structure (pseudo‑spec)

```json
{
  "name": "fable_mode",
  "description": "Apply Fable-style process: scope, gather evidence, reason adversarially, verify, then report with calibrated uncertainty.",
  "inputs": {
    "task": "string",
    "effort_level": "enum(low|medium|high)",
    "context": "optional object"
  },
  "steps": [
    "scope_task",
    "gather_evidence",
    "attack_plan",
    "execute_and_verify",
    "report_and_calibrate"
  ]
}
```

Under the hood, each step is a prompt pattern the model follows. You can implement this as a single skill prompt that tells the model to walk the gates sequentially in one response, or as a multi‑step workflow that persists intermediate state.

## 3. Gate prompts you can re‑use everywhere

Here’s a concrete prompt pattern for each gate, designed to be reusable across use cases (code review, system design, marketing plans, etc.).

### Gate 1: Scoping

Goal: Turn a vague task into a precise, testable plan, including exploring unknowns.[1]

Prompt segment:

> **Scoping gate**  
> 1. Restate the task in your own words.  
> 2. Identify: goal, constraints, success criteria, and obvious unknowns.  
> 3. Propose a plan as a list of steps.  
> 4. For each step, list at least one thing that could go wrong or be unknown.  
> Do not execute the plan yet. Focus only on understanding and failure modes.

This captures the “plan plus devil’s advocate” distinction Nate highlights.[1]

### Gate 2: Evidence

Goal: Check reality before you lean on memory.[1]

Prompt segment:

> **Evidence gate**  
> 1. For this task, distinguish:  
>    - Facts you’re confident about.  
>    - Assumptions you’re making.  
>    - Unknowns that require research or inspection.  
> 2. When files, tools, or APIs are referenced, explicitly confirm whether they exist or are accessible.  
> 3. If you cannot access needed evidence, state that clearly and adjust the plan.

This mirrors the leaked system prompt notes: partial recognition ≠ current knowledge; a prompt implying a file is present doesn’t mean it is.[1]

### Gate 3: Attacking (adversarial reasoning)

Goal: Stress‑test the plan and candidate solutions.[1]

Prompt segment:

> **Attacking gate**  
> 1. Take the current plan and play devil’s advocate.  
> 2. List plausible failure scenarios, edge cases, and misinterpretations.  
> 3. Adjust the plan to handle or explicitly defer each scenario.  
> 4. When tradeoffs exist, explain why you’re picking one path over alternatives.

This captures Fable’s “thinking about everything that could go wrong” before executing.[1]

### Gate 4: Execute & verify

Goal: Do the work, then re‑check it before you call it done.[1]

Prompt segment:

> **Execution & verification gate**  
> 1. Execute the plan for the current effort level (see effort rules below).  
> 2. After execution, verify:  
>    - Does the output meet the success criteria you scoped?  
>    - Are there obvious errors, gaps, or unaddressed failure modes?  
> 3. If issues exist, perform at least one iteration of self‑correction before reporting.

This encodes “verify before declaring done” instead of shipping first draft outputs.[1]

### Gate 5: Reporting & calibration

Goal: Answer first, then briefly explain confidence and ask at most one clarifying question.[1]

Prompt segment:

> **Reporting & calibration gate**  
> 1. Present the answer or output clearly.  
> 2. Briefly describe:  
>    - Key assumptions.  
>    - Main residual risks or uncertainties.  
> 3. Give a confidence level (low, medium, high).  
> 4. Ask at most one clarifying question that would most change your answer if answered.

This mirrors “address the query before asking for clarification; one question max” from the system prompt.[1]

## 4. Effort levels as a parameter

Nate emphasizes using effort levels intentionally; we can encode that as a reusable rule set.[1]

Effort mapping:

- **low** effort  
  - 1–2 passes through the gates.  
  - Shallow evidence gathering (rely more on prior knowledge).  
  - Brief adversarial check and verification.  
  Use when the task is simple or low stakes.

- **medium** effort  
  - 3–5 signal facts or evidence items (per Anthropic’s guidance).[1]
  - More detailed failure mode exploration.  
  - At least one full attempt + correction cycle.  
  Use for moderate complexity.

- **high** effort  
  - 5–10 pieces of evidence for deeper research and comparison.[1]
  - Thorough devil’s advocate exploration and multiple verification passes.  
  - But avoid “x higher max” behavior where the model overthinks and becomes worse; cap iterations explicitly.[1]
  Use only for complex, high‑risk tasks.

You can implement this in your orchestrator by passing an `effort_level` parameter into the skill and having the prompt branch on it (“If effort_level = high, do X; if low, do Y”).

## 5. Model‑agnostic routing hints inside the skill

The video’s routing table concept is portable across providers; we can bake minimal routing hints into the skill.[1]

Inside the skill description, add a section like:

> **Routing hints (optional, for orchestrators)**  
> - If the task is mostly planning, scoping, or adversarial reasoning, prefer a frontier/orchestrator model.  
> - If the task is mostly execution (data transformation, code search, CRUD), prefer cheaper “worker” models.  
> - For dynamic workflows, use this skill in the orchestrator, then delegate specific steps to workers and re‑aggregate results.

In code, this might look like a separate routing table that the orchestrator consults, but the Fable‑mode skill itself simply encourages this pattern.

## 6. Concrete reusable template you can drop into tools

Here’s a consolidated prompt template you can reuse in Claude skills, system prompts, or workflow nodes. You can adapt variable names to your environment.

> **Fable‑mode skill (generic prompt)**  
>  
> You are operating in **Fable mode**. Your job is to apply disciplined Fable‑style process to the following task.  
>  
> Task: `{task}`  
> Effort level: `{effort_level: low|medium|high}`  
> Context (optional): `{context}`  
>  
> Follow these gates in order, adjusting depth for effort level:  
>  
> 1. **Scoping**  
>    - Restate the task.  
>    - Identify goal, constraints, success criteria, and unknowns.  
>    - Propose a stepwise plan.  
>    - For each step, list at least one thing that could go wrong or be unknown.  
>  
> 2. **Evidence**  
>    - Separate facts, assumptions, and unknowns.  
>    - Explicitly check which files/tools/APIs actually exist or are accessible.  
>    - If needed evidence is missing, say so and adjust the plan.  
>    - For effort:  
>      - low: rely on 1–2 key references or prior knowledge.  
>      - medium: use ~3–5 signal facts/evidence items.  
>      - high: use ~5–10 evidence items and comparisons.  
>  
> 3. **Attacking**  
>    - Play devil’s advocate on the plan and candidate solutions.  
>    - List plausible failure modes and edge cases.  
>    - Adjust the plan to address or explicitly defer each.  
>  
> 4. **Execute & verify**  
>    - Execute the plan at the chosen effort level.  
>    - After execution, verify against the success criteria.  
>    - If issues are found, perform at least one self‑correction iteration.  
>    - Avoid unbounded over‑thinking; cap yourself to a reasonable number of iterations based on effort level.  
>  
> 5. **Report & calibrate**  
>    - Present the final answer or artifact.  
>    - Summarize key assumptions and remaining uncertainties.  
>    - Provide a confidence level (low/medium/high).  
>    - Ask at most one clarifying question that would most change your answer.  
>  
> Throughout, prioritize accurate, evidence‑grounded reasoning over speed. When in doubt, state uncertainty and your assumptions explicitly.

That single template is reusable across:  
- Code review tasks  
- System architecture design  
- Agentic workflow design  
- Marketing or ops strategy  
- Research synthesis

You simply change `{task}` and `{context}`, keep the gates and effort logic.

## 7. How to integrate this across your stack

Given your setup (Claude Code + multi‑provider routing), a minimal integration path could be:

- Add Fable‑mode as a Claude Code skill file that:  
  - Accepts `task`, `effort_level`, and `context`.  
  - Applies the above gating pattern in one or multiple steps.  

- In your orchestrator:  
  - Use Fable‑mode on the orchestrator model (Fable/Opus/GPT frontier) for planning and verification steps.  
  - Route individual execution steps (data crunching, simple coding, batch tasks) to Sonnet/Haiku or local models.  
  - Return to Fable‑mode for final verification and reporting.  

- For multi‑use‑case reuse:  
  - Make `task_category` optional (e.g., `"code_review" | "architecture" | "marketing_plan"`) and add small category‑specific hints.  
  - Keep the five gates, effort logic, and reporting discipline identical across categories so behaviors stay consistent.

My confidence that this skill structure faithfully captures the video’s core ideas is **high**: it’s derived directly from the transcript’s description of the five gates, effort guidance, and routing patterns. The main assumption is that your orchestration environment can pass a simple `effort_level` parameter and either run this as a single prompt or a multi‑step workflow.[1]

Would you prefer to implement this first as a single Claude Code skill that you manually call, or as part of an automated router that wraps all complex tasks in Fable‑mode by default?  

## Human

Are there repos already doing this, that can enhance our solution without enterprise bloat?  I'm a solo director with a fleet of ai coders.

## Assistant

Yes—there are already lightweight, open‑source projects that implement “cheap‑first model routing + effort calibration + agent orchestration” without the enterprise bloat, and you can piggyback on them instead of reinventing the plumbing.[1][2][3][4][5]

I’ll focus on options that fit a solo director with a fleet of AI coders, not a big platform team.

## 1. What you already have from Nate’s video

From the Fable video + transcript, your missing pieces are mostly *process* and *routing tables*, not heavy infra:[6]

- A Fable‑mode skill that encodes: scoping, evidence, adversarial reasoning, verification, calibrated reporting.[6]
- An effort‑level schema (1 signal fact for simple, 3–5 for medium, 5–10 for deep research).[6]
- A model routing table: cost score, intelligence, taste, plus maybe categories tied to your workflows.[6]

What you *don’t* get is an implementation of actual routing infrastructure or multi‑provider gateways. That’s where existing repos help.

## 2. Lightweight routing libraries (no enterprise bloat)

These are the most relevant “drop‑in” routers/frameworks you can wrap with Fable‑mode prompts:

| Tool           | What it gives you                                                                 | Why it fits your use case |
|----------------|------------------------------------------------------------------------------------|---------------------------|
| RouteLLM       | Research‑grade framework for serving and evaluating LLM routers; routes simple queries to cheaper models.[4] | Good backbone if you want learned or rule‑based routing with measurable gains. |
| Semantic Router| Semantic embeddings based router; routes prompts to different models or tools based on intent.[1][2] | Great for routing by *task type* (code vs prose vs analysis) without huge overhead. |
| LiteLLM        | OpenAI‑compatible proxy across 100+ providers; can embed simple routing/fallback logic.[2][5] | Ideal if your “fleet of coders” already talks to OpenAI‑style APIs. |
| Microchain     | Very lightweight orchestration; not actively maintained but still useful for simple pipelines.[7] | Good for minimal chains if you don’t want LangChain/LangGraph weight. |
| Model‑routing topic repos | Several simple gateways that route simple prompts to local/cheap models and complex prompts to premium models.[3][5] | These are close to the “cheap‑first, escalate on failure” pattern you want. |

All of these are self‑hostable and avoid the “platform tax” of something like enterprise LangSmith; you can run them behind a single gateway that your coders use.

## 3. Orchestration frameworks that won’t drown you

You likely don’t want full LangGraph governance layers yet, but you do want agentic workflow primitives.

From current surveys of LLM orchestration tools:[2][8][9]

- **LangChain / LangGraph**  
  - Pros: mature ecosystem, supports multi‑agent, multi‑model workflows.  
  - Cons: heavy; can accumulate boilerplate quickly.  
  Use *selectively* for graph‑style workflows where your Fable‑mode orchestrator fans out to workers.

- **FlowiseAI (Node)**  
  - Visual editor over LangChainJS for building flows.[9]
  - Could be useful if you want to quickly sketch agent teams and then export them to code, but it’s optional given your expertise.

- **Maestro (from AY Automate)**  
  - Purpose‑built “cheap‑first routing with cost breakdown per response,” open source and focused on unit economics.[2]
  - It already embodies the “cheap‑first, escalate, verify, then ship” pattern you care about.

Given your profile (TypeScript/Python, solo but advanced), I’d lean:

- Python: RouteLLM + Semantic Router + maybe a thin LangGraph for agent orchestration.  
- TypeScript: LiteLLM gateway + semantic routing layer + your own Fable‑mode prompt skill.

## 4. How to plug Fable‑mode into these repos

You can layer Nate’s Fable‑mode skill on top of any of these without adopting their entire philosophy.

A minimal pattern:

1. **Gateway**  
   - Stand up LiteLLM or similar OpenAI‑compatible proxy that fronts all providers you use.[5][2]
   - This gives your “fleet of coders” a single base URL and a `model` parameter.

2. **Router**  
   - Use RouteLLM or a simple rule‑based router (from GitHub model‑routing topics) that:  
     - Classifies the request: `task_type`, `difficulty`, `stakes`.  
     - Picks a model + effort level: e.g., cheap local/Haiku for low difficulty, Sonnet/Opus/Fable for high difficulty.[10][4][1]

3. **Fable‑mode skill wrapper**  
   - Wrap “difficult or high‑stakes” requests in the Fable‑mode skill prompt you defined: scoping, evidence, attacking, verifying, reporting.[6]
   - The router decides whether to apply Fable‑mode and which model runs it (Opus, Fable, GPT‑premium, etc).

4. **Worker agents**  
   - When Fable‑mode is in “planner/orchestrator” role, use the router to delegate execution steps to cheaper models (Sonnet, Haiku, local LLMs), exactly like Nate’s dynamic workflows.[1][2][6]

This lets you keep your own logic for effort levels and process, while using existing repos for:

- Multi‑provider plumbing  
- Model selection logic  
- Observability (cost, latency, success metrics)

## 5. Keeping it solo‑friendly, not enterprise‑bloated

To avoid bloat and still get leverage:

- Start with **one gateway + one router**  
  - Example: LiteLLM gateway + simple rule‑based router (no learned router yet).[5][2]
  - Only add RouteLLM if you later want data‑driven routing.

- Treat **Fable‑mode as a pure prompt skill**, not a giant framework  
  - Implement it as a function in your orchestrator that wraps tasks, not as a separate microservice.  
  - Pass `effort_level` explicitly, use the five gates inside one or two calls per task.[6]

- Add observability via **lightweight tools**  
  - Langfuse, Helicone, Phoenix give you trace/eval dashboards without enterprise overhead and are self‑hostable.[11]
  - This is useful for verifying that Fable‑mode + routing actually beats your current “just use frontier model” baseline.

## 6. Concrete next step for you

Given you’re a solo director with multiple AI coders, a pragmatic sequence would be:

1. Pick a gateway (LiteLLM or similar OpenAI‑compatible proxy) and make your coders talk to it instead of providers directly.[2][5]
2. Implement a *very* small TypeScript/Python router that:  
   - Classifies tasks (`code`, `architecture`, `analysis`, `writing`) and difficulty (`low|med|high`).  
   - Selects `{model, effort_level}` accordingly, using a YAML/JSON model table like Nate’s.[10][6]
3. Add your Fable‑mode skill as a wrapper for any `difficulty=high` or `stakes=high` task.  
4. Measure cost and quality using a self‑hosted observability tool (Langfuse/Helicone) to prove the routing is giving you “a ton more for a ton less.”[11][2]

My confidence that these repos match what you want is **medium‑high**: they demonstrably implement cheap‑first routing, multi‑provider orchestration, and lightweight gateways, but none will give you Nate’s exact Fable‑mode skill—you’ll need to slot your skill into them.[4][1][5][2][6]

Do you want me to suggest a concrete minimal stack (gateway + router + observability) tailored to your current providers so you can stand this up in a day or two?  
