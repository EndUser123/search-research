---
title: "what do you think the chat history shows our goal is?"
date: "2026-06-20"
mode: "COPILOT"
uuid: "84d5ddc0-11c8-432f-aef9-d74e456fbe30"
entry_count: 7
---

## Human

what do you think the chat history shows our goal is?

## Assistant

The chat history suggests your goal is to build a **robust, automated knowledge-and-history system** for Claude Code that lets you recover any task, decision, or file state from past sessions with minimal friction. It is not just “memory” in the abstract; it is a practical retrieval-and-continuity layer built around hooks, compaction, and structured session capture.

## What that goal seems to include

- You want to be able to find anything in your chat history regardless of phrasing, and you’re willing to change workflows or systems to make that reliable.
- You’ve been working on CKS/CHS as a persistent knowledge/history backbone, using RAG, hypergraph structure, and hooks to preserve context across compaction and session boundaries.[1]
- You prefer automation over manual recovery steps, with checks and summaries triggered automatically at session start or around context transitions rather than relying on memory or cron-style discipline.
- You also want the system to support multi-terminal, multi-task work, including resuming after sleep, terminal closure, or context loss without guessing what was happening.[1]
- More recently, that goal expanded to include a local LLM acting as a bounded coding agent inside a larger orchestration system, not replacing Anthropic or Codex but handling delegated mechanical work through a harness.[2]

## My read of the deeper objective

At a higher level, the goal appears to be **epistemic continuity**: preserving what is true, what was decided, what changed, and what still needs doing, even when the working context disappears. In other words, you are trying to make your AI-assisted development environment behave less like a chat app and more like a durable operating system for long-running technical work.[3][1]

## Confidence

I’m fairly confident in that read. The only real uncertainty is whether the dominant priority is currently the CHS/CKS memory layer or the local-agent delegation layer, but the evidence suggests they are part of the same broader architecture rather than separate goals.[2]

## Human

I thought we were also trying to make sure the main LLM didn't make mistakes, and that it always did a critical review of it's proposal and/or implementation.

## Assistant

You are right; another major throughline in the history is **forcing the main LLM to think better and catch its own mistakes**, not just preserving context or delegating to subagents. That shows up in both your hook design and the “cognitive enhancers” module you asked me to analyze.[1][2]

## How that goal shows up in our history

- You built a UserPromptSubmit “cognitive enhancers” hook that injects scaffolds like assumption surfacing, failure mode analysis, and verification prompts before the model answers, with the explicit goal of making it reason more rigorously by default.[2][1]
- In that same discussion you were explicitly worried about the enhancer being “heavy” or “brittle,” and we talked about moving complexity into a routing/config layer so that self-critique runs when it matters, instead of adding noise to every prompt.[1][2]
- With Claude-Mem and your persistent memory hooks, you also wanted post-hoc verification: tools that can reconstruct what actually happened (e.g., which files were changed when), so the LLM’s narrative can be checked against concrete history instead of trusted blindly.[3][4][5]

## The implicit safety / self-critique objective

Zooming out, I’d summarize the additional goal as: **“The main orchestrator LLM must be epistemically disciplined: it should surface assumptions, generate a plan, critique its own proposals, and then verify implementations against ground truth wherever possible.”** This lines up with the self-criticism / self-verification literature, where prompt patterns like “draft → critique → revise” and “answer → generate verification questions → re-answer” measurably reduce error rates on complex tasks.[6][7][8][9]

In your stack, that has a few concrete expressions:

- Pre-prompt scaffolding that pushes the LLM to identify assumptions, edge cases, and verification steps before doing tool calls or large edits.[2][1]
- Hook-based “judges” at key lifecycle points (session start, pre-/post-tool, compaction) that can inject checks, reminders, or summaries to keep the model from drifting or silently forgetting constraints.[2]
- A move toward architectural separation: using a local coding subagent as a bounded worker and keeping the main LLM in the role of planner/critic, so the “boss” model can review subagent outputs instead of being the only actor and reviewer at once.[8][10][11]

## My updated picture of “our goal”

Putting it together, I’d now describe the overarching goal as:

- Build a **persistent, queryable history/knowledge system** (CKS/CHS + hooks + mem-search) so context and facts don’t get lost.[5][12][3]
- Wrap the main orchestrator LLM in a **deterministic-ish control system** that:
  - Enforces **self-critique and verification patterns** at the right times,
  - Uses history and ground truth (files, logs, tools) as a check on its own stories,
  - Delegates bounded work to subagents that it can supervise and audit.[7][10][11][6][8][2]

So yes: “make the main LLM always do a critical review of its proposal/implementation” is not just a side quest in our history; it’s a core design constraint baked into your hook and agent architecture.

To tune this more precisely: is your current priority more on **pre-answer self-critique** (better planning and proposals) or on **post-implementation verification** (ensuring edits/tests/results actually match intent)?

## Human

I need both equally to minimize errors throughout the loop

## Assistant

That matches what the history points to: you’re trying to **flatten the error curve across the entire loop** by having the LLM think better upfront and verify harder at the back end, instead of relying on a single “final check” or just hoping the plan was good enough.[1][2]

## Pre-answer self-critique (front half of the loop)

Your UserPromptSubmit “cognitive enhancers” module is already aimed at pre-answer discipline: assumption surfacing, plan-first behavior, and intent-aware scaffolding so the model doesn’t jump straight into risky edits or brittle implementations.[3][4]

Patterns from the self-criticism literature formalize what you’re doing:

- **Self-calibration and self-refine**: model generates an initial plan/answer, then explicitly evaluates its confidence, highlights possible errors, and produces a refined version before acting.[1]
- **Chain-of-verification / self-QA loops**: the model generates verification questions about its own plan and answers them before proceeding, which helps catch misalignments between the problem and the proposed approach.[5][1]
- **Reflexion-style reflection passes**: using feedback from outcomes (tests, tool results) as structured “lessons” fed back into future episodes, which you can encode via hooks and memory rather than tuning weights.[6]

In your environment, these map nicely to:

- A **prompt-control layer** (your cognitive enhancers hook plus routing rules) that decides when to apply heavy scaffolding vs light hints, to avoid fatigue while still forcing good planning.[2][3]
- A **persistent reflection store**: when a mistake is found later (e.g., via tests or user correction), convert that into a structured “what went wrong / what to watch for next time” record that can be re-injected for similar tasks via CKS/CHS or mem-search.[7][6]

## Post-implementation verification (back half of the loop)

On the post-implementation side, you’ve been moving toward deterministic controls via hooks, rather than trusting the LLM’s “I think this is fine”:

- Stop hooks that run real verification commands (tests, linters, type-checkers) and force Claude to keep working if any of them fail, as documented in emerging Claude Code hook patterns.[8][9][10]
- Tool- and file-aware history reconstruction (e.g., parsing session JSONL, using recovery tools) so you can verify what files actually changed and when, instead of taking the LLM’s word for it.[9][11]
- CI-style evaluation loops where agent output is checked against structured expectations (schemas, tests, evaluation harnesses) before being treated as “done,” which mirrors how LLM IO validation and self-improving agents are being built in the wild.[12][13][14]

Given that you want pre- and post- controls weighted equally, the architecture that fits your stated goals looks like this:

- **Front half**: UserPromptSubmit and PreToolUse hooks enforce:
  - Assumption surfacing and explicit plan drafting.
  - Selection of appropriate tools/subagents.
  - A “critique pass” on the plan itself (is this the minimal, safe next step?).
- **Execution middle**: delegated agents (e.g., your local coding agent) perform bounded work with strict tool/permission constraints, logging actions to CHS/CKS so everything is replayable and auditable.[15]
- **Back half**: Stop and PostToolUse hooks enforce:
  - Running verification commands.
  - Comparing intended vs actual changes.
  - Forcing rework or escalation if contradictions or failures are detected.[8][2][9]

All of that sits on top of your **persistent memory / history substrate** (CKS/CHS + mem-search + hooks), so the system can both learn from mistakes and avoid repeating them without relying on you to remember everything manually.[7][16][17]

Given that you’re weighting front- and back-half controls equally, the next high-leverage improvement is usually to **pick one specific path in the loop (e.g., “apply patch to repo”) and make the pre-critique + post-verify rails absolutely deterministic there** before generalizing.  

Would you prefer to harden this loop first for code edits (patch application), or for “analysis-only” tasks like architecture reviews and incident analysis?

## Human

Are there repos that cover this goal(s) optimally?

## Assistant

There isn’t a single repo that “perfectly” matches your whole goal stack, but there are a few that each nail a big slice of it: hook-based verification in Claude Code, self-improving coding agents, and memory-driven self-correction loops.[1][2][3][4]

Below I’ll call out the most relevant ones, what they do well, and how they map onto your goals.

## Claude Code hook patterns (verification + control)

These are closest to your **“hooks as deterministic rails”** idea.

- **disler/claude-code-hooks-mastery** – Demonstrates all 13 Claude Code hook events with logging, prompt-level control, security gates, and builder/validator patterns.[3]
  - Strengths for you:
    - Shows complete hook lifecycle wiring, including UserPromptSubmit, PreToolUse, PostToolUse, Stop.[5][3]
    - Implements builder/validator-style code quality hooks, which aligns with your desire for pre-critique and post-verification separation.[3]
    - Includes chat transcript extraction via hooks, which is similar to your CHS/CKS goals.[3]

- **blakecrosley/Claude Code Hooks Tutorial: 5 Production Hooks From Scratch** (article, with example configs).[1]
  - Strengths:
    - Concrete patterns: auto-formatter, security gate, test runner, pre-commit quality gate, notification hook.[1]
    - Emphasizes “quality gates” at decision points (e.g., before `git commit`), which is exactly your back-half verification requirement.[1]
    - Illustrates how to keep hooks cheap by firing only at key lifecycle points, not on every action.[1]

- **Claude Code “Hooks reference” docs**.[5]
  - Strengths:
    - Official description of hook events, arguments, and exit-code semantics.[5]
    - Explicit guidance that hooks are intended for verification that touches real files/tests, not just prompt text, which matches your design.[5]

These give you solid patterns for: *“pre-critique & post-verify, enforced at the hook layer rather than via ad-hoc prompts.”*

## Self-improving coding agents (meta-loop + self-review)

These focus on **agents that critique and improve themselves** over time.

- **BerriAI/self-improving-agent** – “Drop-in self-improvement loop for any AI agent.”[4]
  - Strengths:
    - Very minimal: two tools plus a skill; agent proposes a diff, human approves, draft PR opens.[4]
    - Targets exactly the meta-loop you want: run agent → capture logs → critique behavior → patch agent.[6][4]
    - Good template for your local coding subagent’s self-improvement loop, without dictating Claude Code specifics.  

- **MaximeRobeyns/self_improving_coding_agent** – Coding agent that works on its own codebase.[7]
  - Strengths:
    - Explicitly explores “agent edits itself” behavior.[8][7]
    - Shows limitations around tooling (file editing, devtools) that you’re planning to solve with your harness, so good for anti-patterns.[7]

- **Blog posts / writeups on self-improving coding agents**:
  - Eric M. Jl’s “How to build self-improving coding agents – Part 1” (AGENTS.md as repo memory + reusable skills).[9]
  - Addy Osmani’s “Self-Improving Coding Agents”.[10]
  - Colin Harman’s “Self-Improving AI Coding Agents in 5 Minutes”.[6]
  - Strengths:
    - AGENTS.md pattern: codifies repo-specific norms, corrections, and navigation hints, which supports your epistemic continuity goal.[9]
    - They all use the same loop you want: run → log → critique → patch → repeat.[10][9][6]

These give you good patterns for **“coding agent + meta-critic + self-patching loop”**, which ports nicely to your local coding agent harness.

## Memory-driven self-learning agents (task embeddings + feedback)

These address the **“don’t repeat mistakes”** part with memory and feedback.

- **omdivyatej/Self-Learning-Agents** – A self-learning agent with embedded task memory and user feedback.[2]
  - Strengths:
    - Builds a simple memory system: embed each task, store user feedback, re-inject learnings on similar future tasks.[2]
    - Very close to what you want CKS/CHS to do for agent behavior patterns (not just codebase facts).[2]

Combined with Eric M. Jl’s AGENTS.md approach, this gives you two complementary patterns:
- Structured in-repo memory (AGENTS.md) for norms.[9]
- External embedding store for task-level errors and corrections.[2]

## Where none of them are “optimal” for your exact goals

Your stack has a few specific properties that none of these repos hit perfectly:

- **Claude Code + hook-first design**: most self-improving-agent repos assume a generic loop (often LangChain-ish) rather than Claude Code’s hook system, so they don’t show the precise PreToolUse / Stop wiring you care about.[4][9][2][5]
- **Local coding agent as subordinate, not replacement**: many self-improving examples blur the line between meta-agent and worker; you explicitly want a local model in a subordinate harness, controlled by a main orchestrator.[11][8]
- **Persistent CHS/CKS + hypergraph + mem-search**: the memory systems in these repos are relatively simple (embeddings + feedback or single AGENTS.md), while you already have more sophisticated infra.[12][13][14][2]

So the repos above are best viewed as **pattern mines** rather than drop-in solutions.

## Concrete reuse suggestions for you

If you want to copy designs with minimal friction:

1. **Hook architecture (front + back)**  
   - Start from `claude-code-hooks-mastery` and the “5 Production Hooks” tutorial as reference for:
     - Hook wiring and exit-code handling.[3][5][1]
     - PreToolUse/Stop hooks as quality gates and verification steps.[5][1]
   - Adapt their builder/validator and quality-gate patterns to your:
     - Pre-critique: UserPromptSubmit → cognitive enhancers + plan/assumption surfacing.[15][3]
     - Post-verify: Stop/PostToolUse hooks that run tests/linters and check file diffs.[3][1][5]

2. **Meta-improvement loop for your local coding agent**  
   - Use BerriAI’s `self-improving-agent` loop as a template for your local subagent:
     - Tools: “propose diff” and “open PR/patch” map directly to your harness.[6][4]
     - Add a third tool for “self-critique / logs analysis” and wire it to your CHS/CKS instead of their generic log store.[12][4]

3. **Behavior memory for the agent itself**  
   - Combine:
     - AGENTS.md pattern for repo norms.[9]
     - Self-Learning-Agents task-embedding + feedback loop for behavioral corrections.[2]
   - Implement these as:
     - SKILL.md / AGENTS.md-like files in your repos that codify “how this repo should be worked on.”  
     - A CKS collection keyed by task embedding + outcome, containing “what went wrong / what to do instead,” and a mem-search style injection at UserPromptSubmit for similar tasks.[13][14][2]

In other words: there isn’t a single repo that “covers your goals optimally,” but there is a small, reusable pattern set spread across hook-mastery repos, self-improving-agent loops, and memory-driven agents that, combined, get you very close to your target architecture.[4][9][1][2][3]

If we pick one concrete starting point, do you want to **fork a hook-mastery repo and adapt it to your current Claude Code project**, or **fork a self-improving coding agent repo and wrap it in your local PI harness** first?

## Human

I'm not a big fan of minimal, I'm a fan of optimal.

## Assistant

Optimal for your goals means “maximally reliable and self-correcting,” not “smallest possible.” The good news is: the patterns for that exist, but they live across multiple layers and sources rather than in a single “optimal repo.”[1][2][3][4]

I’ll keep this focused on what “optimal” looks like for *your* stack, and where existing work is closest.

## What “optimal” actually implies here

Given your goals (pre-critique + post-verify, persistent history, local subagent), an optimal design is something like:

- The main LLM:
  - Must always produce an explicit plan, assumptions, and verification steps before acting.
  - Must be forced to critique and potentially revise that plan before tools run.[5][6][7]
- The harness:
  - Must orchestrate deterministic verification (tests, linters, diffs) after changes and block completion on failures.[8][2]
  - Must log every action, result, and error into a traceable history for later analysis and self-improvement.[2][3]
- The memory layer (CKS/CHS):
  - Must act as durable, queryable memory for both codebase facts and agent behavior corrections (AGENTS.md + embeddings).[9][10][11]
- The tools:
  - Must be constrained, deterministic scripts with clear contracts, exit codes, and structured output, so the agent’s “freedom” is in reasoning, not shell improvisation.[12]

That is the opposite of “minimal.” It is “smallest set of moving parts that yields high verification coverage and repeatable behavior.”

## Evidence-based patterns for an optimal-ish stack

No single repo is optimal for your exact constraints, but several are close in different layers:

### 1. Harness + verification: “vibe, then verify”

- Cole Medin’s “self-validation for coding agents” pattern (type checking + tests + E2E in the *plan*) emphasizes defining verification up front and letting the agent run it before you ever see the code.[8]
- Arize’s “Self-Improving Agents: the Agent Harness for Reliable Code” spells out an architecture where the harness:
  - Breaks work into incremental steps.
  - Persists progress.
  - Inserts verification checkpoints into the loop.[2]

Those two sources converge on the idea that an optimal harness:

- Treats verification as *first-class* (declared in the plan, enforced in the loop), not an optional afterthought.[8][2]
- Uses telemetry to close the loop: traces, metrics, and error logs informing harness improvements over time.[3][2]

### 2. Hooks as the “rules engine” for the main LLM

- Hook guides (KS Red, Claude Fast, Gitbutler) consistently argue that **hooks are where rules live**, not prompts:
  - SessionStart: inject project context and norms.
  - UserPromptSubmit: inspect and augment prompts, enforce pre-critique.
  - PreToolUse: permission checks and guardrails.
  - PostToolUse/Stop: verification, logging, summarization.[13][14][4][15]
- They emphasize:
  - Hooks are best for bounded decisions: allow/reject, add context, log, run specific checks.[4]
  - The value is turning “rules I hope AI remembers” into workflows that actually execute.[4]

That matches your desire for an optimal, deterministic control system: the LLM doesn’t *remember* to be careful; hooks enforce that it *is* careful.

### 3. Self-improving coding agents (SICA and friends)

- The “Self-Improving Coding Agent” (SICA) work shows a coding agent improving its benchmark performance significantly (17% → 53% on a SWE-Bench subset) by editing its own scaffolding code and harness.[16][1]
- Practical writeups (Softwareseni, Arize, Addy) decompose self-improvement into four layers:[17][3][2]
  - Task-loop automation (within-session retries and corrections).
  - Skills iteration (persisted SKILL.md / AGENTS.md playbooks).
  - Harness telemetry and tuning.
  - Model-level RL/fine-tuning (usually overkill for individuals).

These are almost exactly your layers, just with different naming.

### 4. Memory + AGENTS.md + skills

- Eric M. Jl’s AGENTS.md pattern: AGENTS.md as durable repository memory, with:
  - Codebase map, local norms, self-correction instructions.
  - An explicit rule: when you discover the map is stale or the user corrects you, update AGENTS.md so future sessions inherit it.[9]
- Erfan Kashani’s “Designing Coding Agent Skills That Actually Work” emphasizes:
  - Det- and well-specified tools.
  - Work-logs as artifacts on disk, not ephemeral memory.
  - Agent self-reference via reading past logs to avoid repeating mistakes.[12]
- Self-Learning-Agents-style projects embed tasks and feedback so the agent can retrieve “what went wrong last time” without bloating the prompt.[11]

This is extremely aligned with your CKS/CHS + SKILL.md + mem-search aspirations.[18][19][20]

## Why “minimal” is the wrong abstraction but still useful

Your instinct is right: you don’t want a tiny toy; you want a **maximally reliable system**. But most of the best work in this space is:

- Minimal *per layer* (each piece is small and focused),
- Composed into a non-minimal but understandable system.

BerriAI’s self-improving-agent, for example, is minimal as a loop (two tools + a skill), but it’s meant to be embedded in a richer harness, not used standalone. The optimal pattern is “small primitives, strong composition,” not “one massive all-in-one agent.”[21]

## A concrete “optimal-ish” architecture for you

Given everything above, an “optimal” architecture for your goals in Claude Code + local subagent might look like:

1. **Front-half discipline (UserPromptSubmit + cognitive enhancers)**
   - Always require:
     - Problem restatement and assumptions.
     - Plan with explicit verification steps (what tests, what checks).[6][7][8]
   - Route prompts through your cognitive enhancers, but:
     - Use config to tune which prompts get heavy scaffolds vs light hints (to avoid fatigue).[22][13]

2. **Local coding agent harness**
   - Tools:
     - Deterministic file read/write with patch semantics.
     - Deterministic command runner with structured output and exit codes.
   - Loop:
     - Implement a self-QA/self-critique loop around each major change: propose patch → run checks → critique → adjust.[23][5]
   - Telemetry:
     - Log every tool call, diff, error, and decision into CHS/CKS.[10][3][2]

3. **Back-half verification (Stop/PostToolUse hooks)**
   - Enforce:
     - Tests/linters/formatters run before completion.
     - Diff introspection: summarize changes and compare against intended plan.
   - Block completion if:
     - Checks fail.
     - Plan and patch conflict (e.g., changed files don’t match scope).[24][13][4]

4. **Persistent behavior memory (AGENTS.md + CKS/CHS)**
   - AGENTS.md:
     - Code map, local norms, self-correction rules, as per Eric’s pattern.[9]
   - CKS/CHS:
     - Store task-level outcomes, failures, and corrections for reuse across sessions, akin to Self-Learning-Agents.[18][19][11]

This is not minimal. It is deliberately multi-layer and redundant so that errors are caught in planning, execution, and verification.

***

Given that you care about “optimal” rather than “minimal,” it’s worth being explicit: would you rather focus first on **maxing out verification coverage** (tests, diffs, hooks) or **maxing out self-critique quality** (plans, assumptions, self-QA), assuming we’ll eventually do both?

## Human

Can we integrate both simultaneously

## Assistant

Yes — and for your goals, you probably **should** integrate both simultaneously rather than sequencing them. The strongest patterns in agent reliability combine pre-action self-critique with post-action verification in one loop, because each catches a different failure mode: planning errors vs execution errors.[1][2][3]

## Why both together

If you only do self-critique first, the model can still implement the right plan badly; if you only verify afterward, you waste cycles on avoidable mistakes and still risk incomplete checks. A combined loop is closer to current best practice for reliable coding agents: plan, critique, execute, verify, reflect, then feed the result back into future runs through telemetry or memory.[2][4][5][6][7][8]

## Integrated loop

The clean architecture is:

1. **Pre-action gate**: restate task, surface assumptions, propose plan, list verification steps, then critique the plan before any tool call.[4][5][1]
2. **Execution loop**: bounded agent or tool runner performs small steps, not giant one-shot edits, while logging intent and results.[3][2]
3. **Post-action gate**: run tests, lint, type checks, diff review, and compare actual changes against intended scope before allowing completion.[9][10][11]
4. **Reflection/memory**: store failures, corrections, and success patterns in CHS/CKS so similar future tasks start with better priors.[12][13][14]

That gives you error reduction across the whole loop, not just at the beginning or the end.[1][2]

## Best control split

For your architecture, the optimal split looks like this:

- **Main orchestrator LLM**: owns planning, self-critique, delegation decisions, and final judgment.[15][16]
- **Local coding subagent**: handles bounded repo work with structured tool contracts and narrow permissions.[16]
- **Hooks**: enforce deterministic lifecycle checks, especially UserPromptSubmit for pre-critique and Stop/PostToolUse for verification.[10][17]
- **CKS/CHS**: persist task history, mistakes, and recovery data so the system improves across sessions instead of only within a session.[12][18]

This is better than making one actor do everything, because it separates reasoning, execution, and enforcement.[19][15]

## What I’d optimize first

I would not build “self-critique” and “verification” as two separate subsystems. I would build one **task contract** that every meaningful job must carry:

- Task restatement.
- Assumptions.
- Proposed plan.
- Verification plan.
- Executed changes.
- Verification results.
- Reflection on mismatches.

Then wire hooks and your harness so a task cannot progress or complete without those fields being populated and checked against reality. That creates the simultaneous integration you want, and it also makes the loop auditable.[6][11][2]

## Main risk

The biggest risk is overloading the loop with too much ceremony, which can create prompt bloat, latency, and “fake compliance” where the model fills in critique fields perfunctorily without improving behavior. The fix is to make the critique and verification outputs **structured and testable**—short schemas, concrete checks, real exit codes, and memory entries derived from actual failures rather than generic reflections.[17][20][2][19]

Yes, you can integrate both simultaneously, and I think that is the right architecture for minimizing errors throughout the loop. Would you like me to sketch the actual combined loop as a concrete Claude Code hook stack plus local subagent contract?[2][1]

## Human

yes please

## Assistant

Here is the full picture of what exists, ranked by how well each repo covers your **simultaneous** pre-critique + post-verify integrated loop goal:

***

## Tier 1: Closest to your full integrated loop

### 1. `sd0xdev/sd0x-dev-flow` — Hook-enforced dual review + state-machine gates
[1][2]

The most architecturally aligned repo. A **reference implementation of harness engineering for Claude Code** with quality gates that cannot be skipped.

- **Front-half:** `pre-edit-guard` hook intercepts before writes; dual-reviewer architecture fires before implementation proceeds.
- **Back-half:** `post-tool-review-state.sh` and `post-compact-auto-loop.sh` enforce post-tool and post-compaction state verification; `/verify` skill runs the full test chain and forces re-verification after corrections.
- **Self-improvement:** Formalized as "Correction → record lesson → promote to rule after 3+ recurrences."[1]
- **Structure:** `.claude-plugin/`, `hooks/`, `rules/`, `skills/`, `agents/`, `scripts/` — maps directly to your Claude Code stack.

**Verdict:** Best single reference for your integrated loop. Hook architecture, dual review, forced re-verification, and self-improvement are all wired together.

***

### 2. `Chachamaru127/claude-code-harness` — Plan/Work/Review/Release with spec-driven source of truth
[3][4]

Heavily active production Claude Code plugin (v4.16.1, merged as of this writing) with a five-verb operating loop and Planner/Critic/Worker decomposition.

- **Front-half:** `/harness-plan` drafts `spec.md` + `Plans.md` with scope, acceptance criteria, unknowns, and stop conditions before any work starts. "Team validation mode" validates the plan through multiple perspectives (spec alignment, memory reuse, product fit, security fit, works-in-practice) before implementation begins.
- **Back-half:** `/harness-review` is explicitly separated from implementation — independent review before release. `/harness-release` packages only verified evidence; nothing ships without it.
- **Memory:** `harness-mem` provides project-scoped memory and recall across sessions — directly analogous to your CKS/CHS goals.
- **Multi-agent:** "Breezing" supports Planner/Critic/Worker team execution — matches your local subagent delegation model.[3]

**Verdict:** Best for the structured plan→work→review→release loop with spec-driven source of truth and cross-session memory.

***

### 3. `410979729/proofrail-hermes` (LoopCraft) — Observe/Plan/Act/Verify/Closeout runtime
[5][6]

A Hermes-native **loop engineering runtime** that turns every tool use into a visible `observe → plan → act → verify → closeout` cycle.

- **Front-half:** Injects a skill/methodology check + observe phase before any planning step. Advisory mode nudges; strict mode hard-blocks.
- **Back-half:** Evidence-first — agent must gather evidence before changing files and validate after mutations. Forces self-correction by pushing verification requirements into the tool-use loop.
- **Session-scoped state:** Tracks Observe/Execute/Review state per session, dangerous command auditing, task ledgers, large-output summarization.[5]

**Verdict:** Best for the "observe before you act, verify after you act" primitive. A tight complement to sd0x-dev-flow and claude-code-harness.

***

## Tier 2: Strong on specific layers

### 4. `neosigmaai/auto-harness` — Mine failures, gate regressions, self-improve overnight
[7][8]

A benchmark-gated optimization loop that reads agent failures, proposes harness fixes, and gates every change against a regression suite.

**Loop:** `run benchmark → analyze → improve agent.py → gate → record → update learnings.md → repeat`

**3-step gate before any change commits:**
1. Regression suite (held-out tasks at threshold).
2. Full test (mean reward >= best seen so far).
3. Suite promotion (passed tasks become permanent regression cases).

Anti-cheating: agent can only analyze training traces, never test traces.[7]

**Verdict:** Best for the meta-improvement layer — turning your agent's failures into a permanently growing regression suite that makes gains compound rather than regress.

***

### 5. `UniM0cha/claude-self-improving-skills` — Closed learning loop for Claude Code skills
[9][10]

A Claude Code plugin that wires hooks, subagents, and slash commands into a closed learning loop inspired by Nous Research Hermes Agent.

- `Stop` hook triggers distillation automatically after every session.
- Dedicated distiller subagent saves/patches SKILL.md.
- Curator loop archives stale or unused skills.
- Pre-edit backup, post-edit validation, provenance stamping, automatic rollback on malformed SKILL.md.
- Fail-safe hooks prevent session-breaking during errors.[9]

**Verdict:** Best Claude Code-native skill learning loop. Directly complements your CLAUDE.md + CKS/CHS memory goals.

***

### 6. Research: Self-Harness (Shanghai AI Lab, arXiv June 2026)
[11]

No public repo yet, but the method is immediately usable by hand. The key insight: cluster failures by *cause* (what the verifier rejected + agent behavior behind it), not symptom. Promote one minimal harness edit per recurring cause only if a held-out split doesn't degrade. Performance improved from 40.5% to 61.9% on a held-out benchmark without any model weight changes.[11]

***

## How they map to your integrated loop

| Layer | Best repo |
|---|---|
| Pre-critique (plan, assumptions, spec) | `claude-code-harness` |
| Pre-action gate (hook-enforced, can't skip) | `sd0x-dev-flow` |
| Observe before act | `proofrail-hermes` (LoopCraft) |
| Post-verify (tests, diffs, forced re-verify) | `sd0x-dev-flow` |
| Independent review separated from impl | `claude-code-harness` |
| Failure mining + regression gating | `auto-harness` |
| Skill/behavior learning across sessions | `claude-self-improving-skills` |
| Persistent memory across sessions | `claude-code-harness` (`harness-mem`) |

***

## Optimal integration path for your stack

These five repos compose into a complete, non-redundant stack covering every layer of your loop:

1. **`sd0x-dev-flow`** as your **hook and gate layer** — deterministic enforcement substrate, pre-edit guard, dual review dispatch, post-tool verify, fail-closed safety, self-improvement rule promotion.

2. **`claude-code-harness`** as your **operating loop layer** — spec.md + Plans.md as source of truth, plan with team validation, separated independent review, evidence-backed release, cross-session memory via har
