---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-01"
mode: "COPILOT"
uuid: "9535d58c-80b3-4873-b70c-bde6d0aecaa0"
entry_count: 1
---

## Human

You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and obvious filler. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works or makes decisions in this domain.[2][1]

Produce a rewritten version of the thread that:

- Keeps every distinct **insight, workflow, configuration, or regimen**, including:
  - Specific sequences of actions, steps, or protocols people follow.
  - Concrete parameter choices (doses, thresholds, settings, schedules, frequencies, tools).[1]
  - Integration details between {artifacts_1}, {artifacts_2}, and {artifacts_3} (e.g., how they are chained or orchestrated).
- Preserves all mentions of **key artifacts** and what people actually do with them:
  - {artifact_type_1}: e.g., tools, agents, drugs, components.
  - {artifact_type_2}: e.g., files, documents, guidelines, protocols.
  - {artifact_type_3}: e.g., automations, policies, hooks, governance mechanisms.
- Removes repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode.

After the rewrite, add a section called **“Operational patterns and setups”** where you explicitly list:

- **Multi‑entity flows**
  - How multiple {entities} are used together (e.g., “I use {artifact_A} and {artifact_B}, then have {artifact_C} consolidate and apply changes”).[1]
- **Automation patterns**
  - Any described triggers, scheduled runs, pipelines, or hooks that react to events or phases.
  - Any rules that determine when something is reviewer‑only vs allowed to auto‑modify.[3][1]
- **Guardrail artifacts**
  - Named documents, configs, or policies (e.g., {guardrail_doc_1}, {guardrail_doc_2}) and the key rules or principles they encode.
  - How those guardrails are enforced in practice (checks, reviews, blocking conditions).

Add a final section **“Practical recommendations”** that distills the most useful advice into concrete steps another practitioner in this domain could implement, for example:

- “Set up {artifact_or_system} with {N} parallel {entities} and one consolidator that merges and applies decisions.”
- “Add a hook or rule that blocks {undesired_pattern} unless {explicit_condition} is met.”
- “Configure {tool_or_policy} to act as a reviewer/critic only, not an automatic changer, for high‑risk operations.”[1]
- “Centralize principles in a single {guardrail_doc} and reference it in every {process_stage} where decisions are made.”

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow, configuration, regimen, or recommendation from the conversation that could alter how someone operates in this domain.[1]

***

To use it, just fill:

- {domain} → “technical”, “clinical evidence”, “policy”, etc.  
- {artifacts_*}, {entities}, {guardrail_doc_*}, {tool_or_policy}, {undesired_pattern}, {process_stage} with your domain‑specific terms.

## Assistant

You are primarily a **technical editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

***

## Cleaned, rewritten thread (spec‑driven / interview‑first Claude Code workflows)

- Spec‑driven development is framed as “interview first, spec second, code last.”[1]
- The core idea is to slow down up front so that Claude asks many clarifying questions, producing a detailed spec that avoids costly rework later.[1]

### Spec‑driven flow with Claude Code

- Start with a minimal spec or prompt, then invoke the **Ask User Question** tool to have Claude interview you before any implementation happens.[1]
- For large features or new projects, Claude may ask on the order of **dozens of questions (e.g., ~40)** to surface implementation details, UI/UX concerns, trade‑offs, and choices that would otherwise remain implicit.[1]
- A recommended prompt pattern is: “Read `spec.md` and interview me using the Ask User Question tool about anything: technical implementation, UI/UX concerns, trade‑offs, etc. Make sure questions are not obvious, be very in‑depth, keep interviewing until complete, then write the spec to the file.”[1]
- This process is explicitly described as **slowing down to speed up**: time is spent in planning and clarification to reduce time spent reworking incorrect assumptions later.[1]

### Why interview mode matters

- When you give a vague prompt like “add authentication” or “build X,” Claude will make many assumptions (JWT vs sessions, OAuth vs managed auth like Clerk/WorkOS, etc.), which can easily diverge from the desired architecture.[1]
- Interview mode flips the default dynamic: instead of you prompting Claude and fixing buried assumptions afterward, Claude prompts you and clarifies before generating code.[1]
- This narrows the solution space early and lets you confront assumptions while they are “cheap to change,” before large code diffs or token‑heavy generations are produced.[1]
- Traditional prompt engineering tries to craft perfect instructions up front; spec‑driven development instead uses AI to help **discover** what you actually want through iterative questioning.[1]

### Using Ask User Question as a workflow primitive

- The Ask User Question tool presents multiple‑choice questions mid‑session, with the option to type free‑form answers, and then continues based on your choices.[1]
- A concrete flow: issue a relatively broad instruction such as “Build me a Next.js app and interview me about what I want,” then let a custom skill trigger the interview process.[1]
- In the demo, the interview first disambiguates what is being built (web app vs marketing site, etc.) and the target audience (e.g., “marketing site for developers”), then continues with more targeted questions (pages like “book a demo,” key flows, etc.).[1]

### Plan mode vs interview mode

- **Plan mode** has existed in Claude Code for some time and is described as:
  - Exploring the codebase.
  - Designing implementation files.
  - Writing a plan for the changes.[1]
- **Interview mode** is positioned as a **precursor** to plan mode:
  - Use interview mode to elicit requirements and preferences.
  - Then run plan mode to map those clarified requirements into a concrete implementation plan.[1]
- The combination (interview → plan → code) is recommended to improve outcome quality for complex or large features.[1]

### Implementing an interview “skill”

- The interview behavior can be encapsulated as a **Claude skill** that:
  - Reads a plan/spec file (e.g., `spec.md`).
  - Uses the Ask User Question tool to interrogate you about technical implementations and other concerns.
  - Optionally constrains or configures parameters like the number of questions, or specific focus areas.[1]
- Skills can be configured so that this interview skill **triggers automatically** for relevant prompts, rather than requiring manual invocation each time.[1]
- Skills “latch on” to the Claude Code process and can trigger native tools (like Ask User Question) inside that flow, making the interview step a repeatable, reusable part of the coding workflow.[1]

### Human‑first requirement refinement (comment insight)

- One commenter describes a first phase called **“understand”**, implemented as a human–agent loop focused on:
  - Refining the intent.
  - Mapping requests to business terms.
  - Making all requirements explicit until **formal requirements (REQs)** are a “natural output” of that step.[1]
- They emphasize that agents should not be expected to “guess,” because this invites hallucinations and scope drift; baking an explicit “understand” phase into the workflow acts as a gateway against bad results.[1]

### Skepticism about over‑interviewing and human bottlenecks

- Another commenter argues that **humans are the bottleneck**, so workflows should avoid asking the model to “bug you” with questions it could resolve itself.[1]
- They propose:
  - First, ask the system to **sketch a high‑level plan**.
  - Then correct its wrong assumptions afterward.[1]
- The rationale:
  - It can be faster to correct a lightweight high‑level plan than to answer many detailed questions up front, especially if the system would otherwise ask obvious or trivial questions.
  - This holds as long as the model is not generating large amounts of code before key decisions (e.g., library selection) are made.[1]
- They agree that specificity is important but argue it should be achieved in an efficient way that accounts for human attention and time constraints.[1]

### “This is just Requirements → Spec → Design → Code”

- A different commenter notes that the Requirements → Specification → Design → Code sequence is not new and questions why it is treated as a novel insight.[1]
- They suggest the perceived novelty comes from “vibe coding” workflows that skip or gloss over requirement and specification steps, implicitly assuming the assistant can read the user’s mind.[1]
- Their personal practice since early 2023 (with older models) has been:
  - Load context to get good results.
  - Treat chatbots like a **team member**.
  - Discuss project goals and algorithms with them.
  - Discuss standards and styles.
  - Only then move forward on coding.[1]
- They liken skipping these conversations to “throwing mud against the wall and seeing what kind of pottery you get,” emphasizing that structured engineering practices remain critical even with LLMs.[1]

***

## Operational patterns and setups

### Multi‑entity flows (Claude, skills, human, spec files)

- **Interview skill + Ask User tool + spec file:**
  - User writes or seeds a minimal `spec.md`.
  - A **Claude skill** is configured to:
    - Read `spec.md`.
    - Use the **Ask User Question** tool to interview the user in depth.
    - Write the resulting refined specification back into `spec.md` once “complete.”[1]
- **Interview mode → Plan mode → Code:**
  - Interview mode gathers and clarifies requirements (what to build, audience, pages, technical choices, services like Clerk/WorkOS, etc.).[1]
  - Plan mode then inspects the actual codebase and produces an implementation plan.
  - Only after this combined process does Claude generate code.[1]
- **Human “understand” phase + AI interview/spec:**
  - A human–agent loop is used first to understand and map business concepts and refine intent.
  - This can then feed into the AI interview and spec‑writing flow, so the AI works from already clarified business language and constraints.
- **High‑level plan first, corrective pass:**
  - User asks Claude to produce a high‑level plan without extensive questioning.
  - User reviews that plan and corrects wrong assumptions.
  - Follow‑up prompts or tools then adjust the plan and eventual implementation.[1]

### Automation patterns (triggers, hooks, constraints)

- **Skill‑triggered interviews:**
  - A Claude skill is set up to automatically trigger the interview process for certain kinds of prompts (e.g., “build a Next.js app,” “add authentication,” “implement large feature”), using Ask User Question internally.[1]
  - The skill can encode parameters such as the number of questions or areas to focus on (technical, UI/UX, trade‑offs), effectively acting as a reusable **interview template**.[1]
- **Precursors vs main pipeline:**
  - Interview mode is explicitly a **precursor** to plan mode, not a replacement, forming an ordered pipeline:
    - Phase 1: Interview (requirements elicitation).
    - Phase 2: Plan (codebase analysis and implementation design).
    - Phase 3: Code generation and application.[1]
- **Human‑gated requirement refinement:**
  - The “understand” phase is explicitly human‑in‑the‑loop and treated as the first phase of the flow, focusing on intent refinement and mapping to business terms before an AI is allowed to implement.[1]
- **Plan‑then‑correct strategy:**
  - As a counter‑pattern to heavy interviewing, one workflow is:
    - Trigger a quick plan generation.
    - Use human review to correct mistakes rather than answering many questions upfront.
  - The implicit rule is: avoid heavy up‑front questioning when humans are the primary bottleneck and the model can self‑propose options that are easy to correct.[1]

### Guardrail artifacts (specs, requirements, phases)

- **`spec.md` as a central guardrail:**
  - `spec.md` is used as a source of truth for what is to be built; the interview skill reads from and writes to this file.[1]
  - It encodes:
    - Technical decisions (auth style, services, UI flows).
    - UX and business requirements discovered through questioning.
- **Plan documents as implementation guardrails:**
  - Plan mode produces a plan that acts as a design‑phase guardrail for subsequent code generation, constraining how Claude will modify the codebase.[1]
- **Requirement (REQ) outputs from “understand” phase:**
  - The human “understand” phase is designed so that explicit **REQs** naturally fall out of the process, becoming a de facto requirements document before any design or coding.
- **Implicit guardrail rules:**
  - Do not allow Claude to “guess” about critical architectural decisions (e.g., auth mechanism, managed vs self‑rolled services).
  - Force these decisions to be expressed explicitly either in `spec.md`, REQs, or the plan before code is generated.[1]
  - For some practitioners, also avoid workflows that ask the model to generate large amounts of code before core choices (library selection, services) are locked in.[1]

***

## Practical recommendations

- Configure an **interview skill** in Claude Code that:
  - Reads `spec.md`.
  - Uses the Ask User Question tool to ask non‑obvious, in‑depth questions until requirements feel complete.
  - Writes the refined spec back to `spec.md` before any code is generated.[1]
- Use a **three‑phase pipeline** for substantial features:
  - Phase 1: Interview mode to clarify requirements.
  - Phase 2: Plan mode to map those requirements to your existing codebase.
  - Phase 3: Code generation following the agreed plan.[1]
- For every major feature (e.g., auth, complex flows), require that decisions like protocol choice, managed vs custom services, and UX flows are captured explicitly in `spec.md` or REQs before Claude is allowed to modify code.[1]
- Add an explicit **“understand” phase** at the very start of your workflow where you and the model:
  - Refine intent.
  - Map needs to business terms.
  - Produce REQs as a natural outcome.
  - Only after this phase should interview/plan/code flows run.[1]
- If human attention is the main constraint, use a **plan‑first, correct‑later** pattern:
  - Ask Claude for a concise high‑level plan.
  - Correct wrong assumptions.
  - Then let it expand into more detailed specs and code, rather than answering long sequences of questions upfront.[1]
- Treat your spec and plan files (`spec.md`, plan outputs, REQs) as **guardrail documents**:
  - Centralize principles and decisions there.
  - Reference them explicitly during each process stage (interview, planning, coding).
  - Block or roll back any code generation that conflicts with these documents until they are updated.[1]
