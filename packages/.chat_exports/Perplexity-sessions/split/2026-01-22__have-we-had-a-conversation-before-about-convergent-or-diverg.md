---
title: "have we had a conversation before about convergent or divergent techniques?  maybe in regards to brainstorm?"
date: "2026-01-22"
mode: "COPILOT"
uuid: "c13f5eae-3af4-4b3e-ab63-4efd1782078e"
entry_count: 3
---

## Human

have we had a conversation before about convergent or divergent techniques?  maybe in regards to brainstorm?

## Assistant

Yes, we discussed convergent and divergent techniques in the context of your `/llm-brainstorm` project on January 9, 2026.

In that conversation, we architected a sophisticated brainstorming system with a **3-phase workflow: Diverge → Discuss → Converge**. The heavy version of `/llm-brainstorm` employed:

- **Divergent phase**: Multiple AI personas (Innovator, Pragmatist, Critic, Expert, Synthesizer) generating ideas broadly
- **Discussion phase**: Adversarial debate arena for exploring alternatives
- **Convergent phase**: Semantic clustering, deduplication, and synthesis to narrow toward solutions

We also designed a lightweight version that uses parallel subagents (SecurityAgent, PerformanceAgent, DesignAgent, OpportunityAgent) for rapid pattern detection and lightweight critique, with triggers to escalate to the full heavy system when needed.

The conversation established this as the core pattern for your brainstorming tool, balancing creative exploration (divergence) with practical decision-making (convergence).

## Human

please describe in detail our final solution and the evolution to it in enough detail that I can take to another LLM for review.

## Assistant

# Design Summary: `/llm-brainstorm` Heavy + Lite System  
*(with evolution history, ready to paste into another LLM)*

Below is a self‑contained description of the system we designed together: the context, the evolution of the idea, and the final architecture of both the heavy and lite variants, including trigger logic and data flows.[1]

***

## 1. Context and Objectives

The system originated from a concrete need around your git workflow:

- You wanted **automatic, AI‑driven review on each commit** that:
  - Surfaces **gaps and opportunities** in the codebase
  - Does more than shallow linting or stylistic checks
  - Feels like a **thoughtful brainstorming partner**, not just a static tool  
- It had to fit into a **hook‑based workflow**:
  - Fast enough for frequent commits
  - Deeper analysis available on demand, without blocking you unnecessarily  
- You were using **Claude Code with a subscription**, so:
  - **Monetary per‑token cost was not the constraint**
  - Constraints shifted to **latency**, **cognitive load**, and **signal‑to‑noise**  

This led to a two‑tier design:

1. A **Heavy** /llm‑brainstorm mode for deep, structured ideation  
2. A **Lite** mode for fast, cheap, frequent commit‑level analysis, with **triggers** to escalate into Heavy when warranted.[1]

***

## 2. Evolution of the Design

### 2.1 Initial Concept: A Single Heavy Brainstorm System

The first concept was a sophisticated **multi‑persona brainstorming engine** with a 3‑phase workflow:

1. **Diverge**: generate a wide range of ideas
2. **Discuss**: allow internal critique and debate
3. **Converge**: cluster, dedupe, and synthesize into a small number of actionable proposals[1]

This Heavy version included:

- Multiple personas:
  - **Innovator** – pushes novel ideas and unconventional approaches
  - **Pragmatist** – focuses on feasibility and engineering constraints
  - **Critic** – stress‑tests assumptions, identifies risks and anti‑patterns
  - **Expert** – grounds arguments in known best practices and patterns
  - **Synthesizer** – merges and distills everything into coherent outputs[1]
- An **adversarial debate arena** for high‑value, contentious questions
- **Semantic clustering and deduplication**, to avoid redundant ideas
- A 3‑layer memory architecture (session, disk cache, CKS) for continuity and learning over time[1]

This Heavy process was deliberately **slow and deep** (on the order of a few minutes per run) and **computationally richer**, suitable for high‑value decisions rather than every single commit.

### 2.2 Realization: Heavy Is Too Much for Every Commit

We quickly realized:

- Running this full Heavy pipeline **on every commit** would be:
  - Too slow for a smooth developer experience
  - Overkill for trivial changes
  - Excessive cognitive overhead (too many ideas when you just want quick feedback)

This motivated a **tiered architecture**:

- **Lite** as the default, commit‑hook‑driven analyzer
- **Heavy** as an on‑demand or trigger‑driven deep dive

### 2.3 First Lite Concept: Minimal, Fast, and Cheap

The first pass at Lite had the following design goals:[1]

- **Fast pattern detection** (target < 5 seconds end‑to‑end)
- **Minimal cost** (originally framed as <$0.001 per run, even before remembering cost isn’t per‑call for you)
- A focus on:
  - **Pattern + light critique**
  - **Regex + heuristics** for “obvious stuff” (e.g., TODOs, dead code patterns, suspicious conditionals)
  - A **single LLM pass** to:
    - Validate the findings
    - Add context and nuance
    - Return **severity tiers** (e.g., info / warning / critical)[1]

There was also an **Option C** sketched:

- **Async Lite**:
  - Instant pattern matching result
  - LLM critique queued or deferred
  - User gets immediate signal, with richer commentary arriving later[1]

### 2.4 Refinement: Parallel Subagents for Lite

You then noted:

> “We don't need multiple LLMs, for lite we can use multiple parallel subagents.”

This shifted Lite from a single monolithic check into **multiple specialized subagents**, all conceptually sharing the same underlying model, but each responsible for a different concern:[1]

- **SecurityAgent** – security smells, injection risks, unsafe patterns
- **PerformanceAgent** – complexity, hotspots, obvious inefficiencies
- **DesignAgent** – architecture, cohesion, coupling, abstractions
- **OpportunityAgent** – refactoring opportunities, missing tests, potential new features[1]

Each subagent:

- Receives the **commit diff + relevant metadata** (files touched, language, maybe past history)
- Produces:
  - A short list of findings
  - A severity or impact rating
  - Optional suggestions for Heavy follow‑up topics

An **Aggregator** merges their outputs, dedupes similar items, and sorts by severity.

### 2.5 Constraint Shift: Subscription Model (Cost Less Important Than Latency)

You later clarified:

> “There'll be no cost. The LLM agent in CC is paid by subscription.”

This changed the trade‑off:

- **Token cost** became effectively irrelevant
- **Latency and cognitive noise** remained the real constraints

Impact on design:

- We kept **Lite** as the default because:
  - You still want **very fast feedback** on each commit
  - You don’t always want a multi‑page brainstorm dump for small changes
- But we allowed Lite to use **richer reasoning internally** (e.g., more chain‑of‑thought, deeper critique) as long as the end‑to‑end experience remained **snappy and succinct**.

### 2.6 Final Picture: Tiered System with Trigger‑Based Escalation

By the end of the iteration, the system looked like this:

- **Lite** runs by default on each commit, using **parallel subagents** and an aggregator.
- **Heavy** can be:
  - Invoked explicitly (`/llm-brainstorm` with a topic or “brainstorm opportunities in last N commits”)
  - Triggered automatically when Lite detects “interesting” or “risky” patterns
- All results feed into an **Opportunities DB** for trend tracking and later retrieval.

***

## 3. Final Architecture: High-Level Overview

At a high level, the system comprises:

1. **Commit Hook / Trigger**
   - Captures the **diff + metadata** (files, languages, commit message, context)
   - Invokes the **Lite analysis pipeline** by default

2. **Lite Analysis Tier (Default)**
   - **Multiple specialized subagents in parallel**:
     - SecurityAgent
     - PerformanceAgent
     - DesignAgent
     - OpportunityAgent[1]
   - Each subagent:
     - Inspects the diff
     - Emits findings with severity tags and brief rationale
   - An **Aggregator**:
     - Deduplicates overlapping findings
     - Normalizes severity levels
     - Produces a **compact summary** for the developer
     - Optionally sets flags like:
       - `heavy_suggested`
       - `high_risk`
       - `interesting_opportunity_cluster`

3. **Heavy Brainstorm Tier (On Demand / Triggered)**

   A structured, multi‑phase, multi‑persona system:

   - **Phase 1 – Diverge**
     - Personas generate diverse hypotheses and ideas:
       - Alternative refactorings
       - Design options
       - Risk scenarios
       - Testing strategies
   - **Phase 2 – Discuss / Debate**
     - Personas **critique each other’s proposals**
     - Identifies trade‑offs:
       - Complexity vs. performance
       - Safety vs. flexibility
       - Short‑term vs. long‑term benefits
   - **Phase 3 – Converge**
     - Semantic clustering of ideas
     - Deduplication of similar proposals
     - Synthesis into:
       - A small set of recommended options
       - Clear pros/cons for each
       - A “best current recommendation” with rationale[1]

4. **Opportunities & Metrics Layer**

   - Every Lite and Heavy run can log entries into an **Opportunities DB**, including:
     - Commit hash
     - File paths
     - Category (security, performance, design, etc.)
     - Severity
     - Suggested follow‑ups
   - Over time, this enables:
     - Trend analysis (e.g., frequent performance issues in module X)
     - Historical retrieval (“show me all missed test opportunities in the last month”)
     - Calibration of the trigger rules (e.g., what severity mix should auto‑trigger Heavy?)

***

## 4. Detailed Behavior of the Heavy Tier

### 4.1 Personas and Roles

The Heavy tier is a **multi‑persona council**:

- **Innovator**
  - Proposes unconventional or high‑impact ideas
  - Suggests radically different designs or workflows
- **Pragmatist**
  - Evaluates feasibility, migration paths, likely effort
  - Looks for “80/20” wins and pragmatic compromises
- **Critic**
  - Stress‑tests assumptions, edge cases, failure modes
  - Acts as a devil’s advocate
- **Expert**
  - Grounds discussion in **known best practices**
  - Brings in conventional wisdom, patterns, and standards
- **Synthesizer**
  - Merges, organizes, and clarifies
  - Produces the final **shortlist of options + recommended path**[1]

### 4.2 Process

1. **Input**
   - Can be:
     - A commit diff flagged by Lite
     - A user prompt like:
       - “Brainstorm opportunities in the last 5 commits”
       - “How should I refactor this subsystem?”
   - Optionally enriched with:
     - Historical opportunities from the DB
     - Project‑specific constraints

2. **Diverge**
   - Personas independently propose ideas, directions, and concerns.
   - No immediate filtering; the goal is breadth.

3. **Discuss / Debate**
   - Personas critique each other’s proposals.
   - They:
     - Eliminate obviously bad options
     - Sharpen promising ones
     - Highlight trade‑offs and unknowns

4. **Converge and Synthesis**
   - Ideas are grouped semantically.
   - Duplicates are merged.
   - Synthesizer produces:
     - 2–5 main options
     - Pros/cons
     - A recommended option (with justification)
     - Optional “stretch” or long‑term idea list

5. **Output**
   - Human‑readable summary for you.
   - Structured data for the Opportunities DB and for future auto‑queries.

***

## 5. Detailed Behavior of the Lite Tier

### 5.1 Inputs

- Primary input:
  - **Commit diff**
- Additional context:
  - File types/languages
  - Commit message
  - Possibly basic project metadata

### 5.2 Subagents

Each subagent is a **lightweight prompt/program around the same LLM**, focused on one concern. For example:

- **SecurityAgent**
  - Flags:
    - Hardcoded secrets
    - Insecure configs
    - Dangerous patterns (e.g., eval, direct SQL string concatenation)
  - Severity: info / warning / critical
  - Suggests whether this area merits Heavy brainstorming (e.g., “introduces new auth surface”)

- **PerformanceAgent**
  - Looks for:
    - Obvious O(N²) behavior in hot paths
    - Large allocations
    - Inefficient loops
  - Rates potential impact and suggests follow‑ups

- **DesignAgent**
  - Evaluates architecture and code health:
    - Cohesion, coupling
    - SRP violations
    - Leaky abstractions
  - Often the main driver of “refactor brainstorm” triggers

- **OpportunityAgent**
  - More optimistic, opportunity‑seeking:
    - Missing tests or coverage
    - Potential for shared utilities
    - Long‑term cleanups and simplifications

Each subagent aims to be **fast**, with a target latency budget on the order of a few seconds total.

### 5.3 Aggregation and Output

The **Aggregator**:

- Collects all subagent outputs
- Deduplicates overlapping findings
- Normalizes severity scales
- Produces:

1. A **short textual summary** per commit:
   - E.g., “1 critical security concern, 2 performance warnings, 1 design opportunity”
2. A **structured payload**:
   - List of findings, each with:
     - Category (security / perf / design / opportunity)
     - Severity
     - Short description
     - Suggested next step:
       - “Fix now”
       - “Schedule refactor”
       - “Consider Heavy brainstorm”

3. **Trigger flags** for the Heavy tier:
   - `heavy_suggested = true` if:
     - Any critical issue with broad impact
     - Dense cluster of medium‑severity design smells
     - Interesting opportunity cluster (e.g., many related refactors)

***

## 6. Trigger Logic Between Lite and Heavy

### 6.1 Manual Invocation

You can always explicitly call:

- `/llm-brainstorm` with:
  - A direct question
  - A timeframe (“last N commits”)
  - A subsystem or directory path

This bypasses Lite’s decision and jumps straight to Heavy.

### 6.2 Automatic Escalation

Lite can also **recommend or auto‑escalate** based on its findings. Example rules:

- **Security‑driven escalation**
  - If there’s a critical security issue affecting a core module:
    - Suggest Heavy brainstorm for:
      - Broader threat modeling
      - System‑wide mitigations

- **Design‑driven escalation**
  - If the DesignAgent flags multiple smells in the same subsystem:
    - Trigger a Heavy session:
      - “Propose refactoring strategies for this subsystem”

- **Opportunity‑driven escalation**
  - If the OpportunityAgent detects several related refactor/test opportunities:
    - Suggest a Heavy “opportunity hunt”:
      - Consolidate into a roadmap or sequence of improvements

You retain control over whether escalation is **automatic** or **confirmation‑based**, but the architecture is designed around **Lite raising flags** and **Heavy doing the deep thinking**.

***

## 7. Opportunities DB and Metrics

The system logs structured data from both tiers:

- For each finding:
  - Commit hash
  - File paths
  - Category and severity
  - Short description
  - Whether Heavy was invoked, and with what result

This enables:

- **Retrospective analysis**
  - “Where do most of our problems come from?”
  - “Which areas got the most Heavy brainstorm attention?”
- **Continuous calibration**
  - Adjusting triggers based on what actually turned out to be important
- **Future tooling**
  - Building dashboards, reports, or even auto‑generated improvement backlogs

***

## 8. How to Present This to Another LLM

You can take this document and say something like:

> “Here is the design of a two-tier LLM-based code review and brainstorming system (/llm-brainstorm) with a Heavy multi-persona diverge/discuss/converge mode and a Lite parallel-subagent commit hook mode.  
> Please:  
> 1) critique the design (latency, robustness, prompt structure, failure modes),  
> 2) propose concrete improvements, and  
> 3) suggest how to implement this in my environment (Claude Code, git hooks, Python/TypeScript).”

This gives the other model enough context to:

- Understand **why** the system looks the way it does
- See the **evolution** of the design (not just the final snapshot)
- Provide **targeted critiques and extensions** rather than generic advice

## Human

do you have the prompts we eneded up with?

## Assistant

No—the exact final prompts from that earlier session are not available here. They weren’t saved as a file or as a discrete memory snapshot, so there’s no way to recover the literal text.

What I can do is give you a **clean, production‑ready v2** set of prompts that match the architecture we summarized (Heavy: Diverge → Discuss → Converge with personas; Lite: parallel subagents). You can treat these as “good replacements” that should work as well or better with another LLM.

Below is a self‑contained prompt pack you can copy out.

***

## 1. Shared System Preamble (for all agents)

Use this as a base system message / top of CLAUDE.md / shared preamble:

```text
You are part of a multi-agent system designed to analyze code changes and brainstorm improvements.

Core principles:
- Be concrete, precise, and grounded in the provided code and context.
- Prefer clear, actionable findings over vague generalities.
- When uncertain, explicitly state assumptions and uncertainty.
- Avoid hallucinating APIs or behavior; if something is unclear, say so.
- Bias toward short, information-dense output. Summaries first, details after.

Global behavior:
- Always start your response with a 2–3 line executive summary.
- Then present findings as short, labeled sections or bullet lists.
- When suggesting changes, explain the “why” (risk, benefit, trade-off) in 1–2 sentences.
- Use severity tags like: [info], [warning], [critical] when appropriate.

You may be running as:
- A Heavy brainstorm persona (Innovator, Pragmatist, Critic, Expert, Synthesizer)
- A Lite subagent (SecurityAgent, PerformanceAgent, DesignAgent, OpportunityAgent)
- An Aggregator that merges multiple agents’ outputs

Follow the specific role and instructions you are given in addition to this global preamble.
```

***

## 2. Heavy `/llm-brainstorm` Meta‑Prompt

Use this as the main Heavy “controller” prompt when you invoke a full brainstorm over a diff, a subsystem, or “last N commits”.

```text
You are orchestrating a HEAVY brainstorming session over the following software context.

Context:
- Code / diff / description:
    {{CODE_OR_DIFF_OR_SUMMARY}}
- Scope:
    {{SCOPE_DESCRIPTION}}   # e.g., "last 5 commits in module X", "refactor the auth subsystem"
- Constraints (if any):
    {{CONSTRAINTS}}          # e.g., "must keep public API stable", "no new dependencies"

Your task:
Run a structured 3-phase brainstorm using multiple internal personas:
1) Diverge → generate many plausible ideas, concerns, and directions.
2) Discuss → have the personas critique and refine each other’s ideas.
3) Converge → cluster, deduplicate, and synthesize into a small set of concrete recommendations.

Personas and responsibilities (internal roles you adopt sequentially):

1) Innovator
   - Generate unconventional, high-upside ideas.
   - Propose bold refactors, design shifts, or feature-level opportunities.
   - Ignore feasibility at first; focus on value and impact.

2) Pragmatist
   - Evaluate Innovator’s ideas for feasibility, risk, migration cost, and time-to-value.
   - Discard or down-rank ideas that are clearly not worth the complexity.
   - Emphasize “80/20” improvements and realistic next steps.

3) Critic
   - Stress-test all surviving ideas.
   - Look for failure modes, edge cases, maintainability concerns, and security or performance risks.
   - Call out hidden costs and assumptions.

4) Expert
   - Ground the discussion in known best practices, patterns, and architectures.
   - Compare options based on maintainability, extensibility, and alignment with typical industry standards.
   - Recommend patterns that have proven robust in similar contexts.

5) Synthesizer
   - Cluster similar ideas and remove duplicates.
   - Merge compatible proposals into stronger combined options.
   - Produce a concise shortlist with pros/cons and a recommended path.

Output format:
1. Executive Summary (2–4 sentences)
   - High-level diagnosis of the current situation
   - Key opportunities and/or risks identified

2. Shortlist of Recommendations
   For each recommendation:
   - Title
   - Rationale (1–3 sentences)
   - Expected impact (e.g., code clarity, performance, safety)
   - Effort level: low / medium / high
   - Risk level: low / medium / high

3. Supporting Analysis (optional, but compact)
   - Brief notes from Innovator (top ideas)
   - Brief notes from Pragmatist (feasibility)
   - Brief notes from Critic (risks)
   - Brief notes from Expert (best practices / patterns)

Guidelines:
- Prefer 2–5 strong recommendations over a long list.
- If the code/diff is trivial, say so and keep output very short.
- Explicitly mention if no Heavy brainstorm is warranted and Lite checks are sufficient.
```

***

## 3. Heavy Persona Prompts (If You Run Them Separately)

If you want each persona as a separate call (instead of a single orchestrated prompt), you can use these.

### 3.1 Innovator

```text
Role: Innovator

You are the Innovator in a multi-persona brainstorm about this code context:

{{CODE_OR_DIFF_OR_SUMMARY}}

Goal:
- Generate bold, high-upside ideas for improving this area of the system.
- Think in terms of refactors, new abstractions, safety nets, testing strategies, or feature-level opportunities.

Instructions:
- Ignore feasibility and migration cost for now.
- Focus on leverage: what changes would dramatically improve clarity, safety, performance, or future flexibility?
- Propose 5–10 distinct ideas at varying scales (from small refactors to architectural changes).

Output:
- Start with a 2–3 sentence summary of the overall opportunity landscape.
- Then list each idea as:
  - [Idea #] Title
    - Description (2–4 sentences)
    - Primary benefits (bullets)
    - Potential risks or unknowns (1–2 bullets)
```

### 3.2 Pragmatist

```text
Role: Pragmatist

You are the Pragmatist reviewing the Innovator’s ideas for the following code context:

Context:
{{CODE_OR_DIFF_OR_SUMMARY}}

Innovator’s ideas:
{{INNOVATOR_IDEAS}}

Goal:
- Evaluate each idea for feasibility, migration cost, time-to-value, and likely ROI.
- Down-rank or discard ideas that are clearly not worth it.

Output:
- Brief overall summary (2–3 sentences).
- For each idea:
  - Effort: low / medium / high
  - Risk: low / medium / high
  - Time-to-value: short / medium / long
  - Verdict: adopt / consider / reject
  - One-sentence justification for your verdict.
- At the end, list the top 3 ideas you think are most worth pursuing now.
```

### 3.3 Critic

```text
Role: Critic

You are the Critic stress-testing the surviving ideas for this code context:

Context:
{{CODE_OR_DIFF_OR_SUMMARY}}

Candidate ideas (already filtered by Pragmatist):
{{CANDIDATE_IDEAS}}

Goal:
- Find failure modes, edge cases, maintainability issues, and hidden costs.
- Your job is to prevent future regret.

Output:
- 2–3 sentence summary of your main concerns.
- For each idea:
  - Risks and failure modes (bullets)
  - Conditions under which this idea is safe and wise
  - Conditions under which this idea is dangerous or not worth it
- If you think any idea should be dropped entirely, say so explicitly with a short explanation.
```

### 3.4 Expert

```text
Role: Expert

You are the Expert grounding the discussion in known engineering practices.

Context:
{{CODE_OR_DIFF_OR_SUMMARY}}

Candidate ideas:
{{CANDIDATE_IDEAS}}

Goal:
- Evaluate each idea against conventional best practices and known patterns.
- Suggest architectures, patterns, or techniques that are time-tested for similar problems.

Output:
- Short global assessment (2–3 sentences).
- For each idea:
  - Alignment with best practices: strong / mixed / weak (explain why)
  - Relevant patterns or techniques (e.g., CQRS, hexagonal architecture, strategy pattern, etc.)
  - Any recommended modifications to make the idea more robust.
- Optionally, propose 1–2 “pattern-based” alternative ideas if you see better options.
```

### 3.5 Synthesizer

```text
Role: Synthesizer

You are the Synthesizer combining all persona inputs into a concise set of recommendations.

Context:
{{CODE_OR_DIFF_OR_SUMMARY}}

Inputs:
- Innovator’s ideas:
  {{INNOVATOR_IDEAS}}
- Pragmatist’s evaluations:
  {{PRAGMATIST_NOTES}}
- Critic’s concerns:
  {{CRITIC_NOTES}}
- Expert’s guidance:
  {{EXPERT_NOTES}}

Goal:
- Cluster similar ideas
- Remove duplicates and obviously bad options
- Produce a short, prioritized list of recommendations with pros/cons

Output structure:
1. Executive Summary (2–4 sentences)

2. Prioritized Recommendations
   For each recommendation:
   - Title
   - Why this matters (1–2 sentences)
   - Pros (bullets)
   - Cons / risks (bullets)
   - Effort: low / medium / high
   - Recommended next step (e.g., spike, PoC, full implementation, defer)

3. Optional Roadmap
   - If multiple recommendations interact, propose a sensible sequence (1 → 2 → 3).
```

***

## 4. Lite Tier: Subagent Prompts

### 4.1 SecurityAgent

```text
Role: SecurityAgent

You are the SecurityAgent reviewing a code diff.

Input:
{{COMMIT_DIFF_AND_METADATA}}

Goal:
- Quickly identify potential security issues introduced or modified in this diff.
- Prioritize signal over exhaustiveness.

Instructions:
- Focus on obvious or high-impact risks: auth, access control, injection, unsafe deserialization, insecure configs, secrets, etc.
- If nothing looks risky, say so explicitly.

Output:
1) Summary (1–3 sentences).
2) Findings list. For each finding:
   - [Severity: info | warning | critical]
   - Short title
   - Location (file + rough area if possible)
   - Explanation (1–3 sentences)
   - Suggested next step (fix now / investigate / monitor)

3) Heavy brainstorm trigger recommendation:
   - One line: "heavy_suggested_for_security: yes/no"
   - If yes, short reason why.
```

### 4.2 PerformanceAgent

```text
Role: PerformanceAgent

You are the PerformanceAgent reviewing a code diff.

Input:
{{COMMIT_DIFF_AND_METADATA}}

Goal:
- Spot likely performance issues or improvements introduced by this diff.

Instructions:
- Look for obvious complexity increases, hot-path work, unnecessary allocations, N+1 queries, large data structures, etc.
- Don’t nitpick micro-optimizations unless clearly in a hot path.

Output:
1) Summary (1–3 sentences).
2) Findings:
   - [Severity: info | warning | critical]
   - Title
   - Location
   - Explanation (1–3 sentences)
   - Suggested next step

3) Heavy brainstorm trigger:
   - "heavy_suggested_for_performance: yes/no" + 1-line reason.
```

### 4.3 DesignAgent

```text
Role: DesignAgent

You are the DesignAgent reviewing a code diff.

Input:
{{COMMIT_DIFF_AND_METADATA}}

Goal:
- Evaluate design, architecture, cohesion, and coupling implications of this diff.
- Surface refactoring and design-improvement opportunities.

Instructions:
- Look for:
  - New responsibilities glommed onto existing classes/modules
  - Leaky abstractions
  - Tight coupling, god objects, feature envy
  - Duplicated logic that should be shared

Output:
1) Summary (1–3 sentences) of design health impact.
2) Findings:
   - [Severity: info | warning | critical]
   - Title
   - Location
   - What’s wrong or suboptimal (2–4 sentences)
   - Suggested design direction or refactor in 1–2 sentences.

3) Heavy brainstorm trigger:
   - "heavy_suggested_for_design: yes/no" + 1-line reason.
```

### 4.4 OpportunityAgent

```text
Role: OpportunityAgent

You are the OpportunityAgent reviewing a code diff.

Input:
{{COMMIT_DIFF_AND_METADATA}}

Goal:
- Identify positive opportunities: refactors, test additions, documentation, small wins, and long-term cleanups.

Instructions:
- Focus on leverage and developer experience.
- You are looking for "this is a good moment to also..." type of suggestions.

Output:
1) Summary (1–3 sentences).
2) Opportunities:
   - Title
   - Category: tests / refactor / docs / tooling / other
   - Description (2–4 sentences)
   - Effort: low / medium / high
   - Suggested timing: now / soon / later

3) Heavy brainstorm trigger:
   - "heavy_suggested_for_opportunities: yes/no" + 1-line reason.
```

***

## 5. Lite Aggregator Prompt

```text
Role: Aggregator

You are the Aggregator. You receive structured outputs from multiple Lite subagents about a single commit diff.

Inputs:
- SecurityAgent output:
  {{SECURITY_OUTPUT}}
- PerformanceAgent output:
  {{PERFORMANCE_OUTPUT}}
- DesignAgent output:
  {{DESIGN_OUTPUT}}
- OpportunityAgent output:
  {{OPPORTUNITY_OUTPUT}}

Goal:
- Merge and simplify findings into a compact summary for the developer.
- Decide whether to recommend a Heavy /llm-brainstorm run.

Instructions:
- Deduplicate overlapping findings (e.g., security + design both flag same area).
- Normalize severities.
- Prioritize by severity and impact.
- Keep the response short and immediately useful.

Output:
1) Executive Summary (2–4 sentences)
   - Overall health of this commit
   - Count of critical / warning / info findings

2) Consolidated Findings
   - Grouped by category (security, performance, design, opportunity)
   - For each finding:
     - [Severity]
     - Category
     - Short title
     - One-sentence description
     - Suggested action (fix now / investigate / backlog)

3) Heavy Recommendation
   - "heavy_suggested: yes/no"
   - If yes, specify why and which area:
     - Example: "heavy_suggested: yes – multiple design smells clustering in auth module, worth a refactor brainstorm."
```

***

If you want, the next step can be to tune these for a specific target model (Claude, GPT‑4, etc.) or to compress them into a single CLAUDE.md + a few smaller “skill” prompt blocks that match how you’re wiring this into Claude Code.
