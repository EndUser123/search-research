---
title: "'Find official documentation, community tutorials, and optimal workflows for Claude Code bundled prompt-based skills. Sp"
date: "2026-07-10"
mode: "COPILOT"
uuid: "afee6423-c0fb-407a-8cbb-175873696229"
entry_count: 3
---

## Human

"Find official documentation, community tutorials, and optimal workflows for Claude Code bundled prompt-based skills. Specifically, search for usage examples of the /verify skill (part of the run-and-verify trio) and the /simplify command, skill, or custom simplification agent. Detail how to pass arguments to them, test them, and use them optimally in local development."  I thikn there may be code review commands also.

## Assistant

Claude Code ships bundled, prompt-based skills like `/run`, `/verify`, `/code-review`, and `/batch`, plus review-oriented commands like `/simplify`, all exposed as slash commands that you can also override or extend with your own SKILL.md-based skills.[1][2][3]

Below I’ll focus on: (1) how bundled skills work, (2) the run-and-verify trio including `/verify`, (3) `/simplify` and related review commands, (4) argument passing and testing in local dev, and (5) some practical “optimal workflow” patterns you can adopt.

***

## Bundled prompt-based skills: mental model

Bundled skills are just Agent Skills implemented as SKILL.md files that Claude Code ships by default; they behave exactly like your own skills but are marked as **Skill** in the commands reference.[2][3][1]

Key properties for bundled skills in Claude Code:

- They live in Claude’s internal skills directory, but you can override them with your own `.claude/skills/<name>/SKILL.md`.[1]
- They are prompt-based: when you invoke `/code-review`, `/batch`, `/run`, `/verify`, etc., Claude Code reads a SKILL.md-like prompt and lets Claude orchestrate tools (git, bash, tests, etc.).[3][1]
- They appear in `/` autocomplete with **Skill** in the Purpose column; you invoke them exactly like any other command: `/skill-name [args...]`.[3]

For your use-case, the important bundled skills are:

- `/run` – launch and drive your app to see a change working.[1]
- `/verify` – build and run the app and confirm a change via runtime observation (not tests).[3][1]
- `/run-skill-generator` – record app-specific launch recipes that `/run` and `/verify` will reuse.[1]
- `/code-review` – multi-pass diff review, with options to fix and/or comment.[3]
- `/batch` – large-scale multi-agent refactor workflow.[3]
- `/simplify` – cleanup-only review of diffs, focusing on simplification and efficiency.[3]

***

## Run-and-verify trio: `/run`, `/verify`, `/run-skill-generator`

### What `/verify` actually does

The official `/verify` skill’s SKILL.md is public and describes a strict runtime-verification protocol.[4]

Core behavior:

- Goal: “Verify that a code change actually does what it's supposed to by running the app and observing behavior.”[4]
- Evidence must be runtime capture: stdout, HTTP responses, screenshots, pane dumps, etc.—not tests or static inspection.[4]
- Tests and type-checks are deliberately avoided; they’re considered CI’s job, not verification evidence.[4]

The skill instructs Claude to:

1. **Find the change scope** via git/gh commands (`git log`, `git diff`, `gh pr diff`) and treat the diff as ground truth.[4]
2. **Identify the runtime surface** (CLI, API, GUI, library boundary, agent behavior, CI workflow) and disallow “internal function” as a surface.[4]
3. **Get a handle**:
   - Prefer repository-level verifier skills (`verifier-*`) in `.claude/skills/` if present.[4]
   - Fall back to `run-*` skills for build/launch primitives.[4]
   - Otherwise cold-start from README/package.json/Makefile with ~15 min timebox and recommend `/run-skill-generator`.[4]
4. **Drive the app** via the smallest path that exercises the changed code (specific flag/route/error path, etc.), explicitly not just running tests.[4]
5. **Push on it** with probes (invalid inputs, edge cases, wrong methods, concurrent runs, etc.) around the change, at the same surface.[4]
6. **Capture** outputs and environment relevant evidence.[4]
7. **Report** a structured verdict: PASS/FAIL/BLOCKED/SKIP plus steps, probe results, screenshot/sample, and findings.[4]

CONSENSUS: `/verify` is essentially an end-to-end, runtime test harness orchestrated by Claude, deliberately distinct from unit tests or static code review.

### How `/run` and `/verify` infer launch by default

From the skills docs: `/run` and `/verify` work without setup by inferring how to launch the project from its type and from files like README, `package.json`, and `Makefile`.[1]

FACT: This inference is good for “standard” projects (simple CLI/server/TUI/browser apps without complex environment).[1]

When your app requires:

- databases or message queues,  
- env files and secrets,  
- multi-step builds, GUI sessions, or remote dependencies,  

the docs recommend recording an explicit recipe via `/run-skill-generator`.[1]

### `/run-skill-generator` and custom verifier skills

`/run-skill-generator` exists to turn your implicit “I know how to run this app” knowledge into an explicit, reusable skill.[1][4]

Behavior:

- Starts from a “clean” environment, walks through install, env setup, and launch.[1]
- Captures the working recipe (commands, env vars, scripts) and writes a project-specific skill directory under `.claude/skills/run-<name>/`.[1]
- After that, `/run`, `/verify`, and other agents reuse the recorded recipe instead of re-inferring from README, etc.[1]

Optimal pattern (CONSENSUS):

1. For each project, run `/run-skill-generator` once when you first wire Claude Code in.[1]
2. Add a `verifier-<surface>` skill that wraps the runtime verification with your org’s capture protocol (screen recording paths, log paths, etc.). [/verify` looks for these first.] [web:6]  
3. Update the recipe and verifier whenever build/launch steps change.[1][6]

***

## `/simplify` and code-review oriented commands

### `/code-review` and its relation to `/simplify`

The commands reference states that `/code-review` is a bundled Skill that reviews the current diff for correctness and cleanup; it can apply fixes or comment on a PR and supports effort levels (`low`–`ultra`).[3]

Key bits:

- `/code-review [effort] [--fix] [--comment] [target]`:
  - Reviews correctness and maintenance aspects of the diff.[3]
  - `--fix` applies changes directly to the working tree.[3]
  - `--comment` posts findings as inline PR comments via GitHub.[3]
  - `ultra` uses a deep, cloud-based multi-agent review.[3]

From the same table:

- “From v2.1.154, `/simplify` runs a separate cleanup-only review that applies fixes without hunting for bugs.”[3]

FACT: `/simplify` is a specialized, cleanup-oriented skill that focuses on simplification, reuse, and efficiency rather than correctness bug hunting.[5][3]

Community + video behavior:

- `/simplify` runs three review agents in parallel: code reuse review, code quality review, and efficiency review.[5]
- It uses the current git diff to constrain its scope.[5]
- It analyzes and rewrites code, with Sonnet-style analysis feeding into an Opus “orchestrator” agent.[5]

Confidence: High (docs + video + community discussion line up, though the exact agent composition could evolve).

### Practical usage patterns for `/simplify`

Typical local workflow:

- After a change (especially large generated code), you run:
  - `/code-review high --fix` for correctness + cleanup.[3]
  - `/simplify` to perform further structural simplification and efficiency-focused refactors.[5][3]

Arguments:

- `/simplify` takes the current diff implicitly; you can pass hints as trailing text for focus, e.g.:
  - `/simplify limit to src/api/` or `/simplify prefer functional patterns`.  
  These hints just become part of the skill prompt as `$ARGUMENTS`.[1][3]

Optimal pattern:

1. Use `/code-review` with an effort level tuned to risk (e.g. `high` or `max` for complex changes, `low` for trivial patches).[3]
2. Use `/simplify` when:
   - the code is functionally correct but messy,  
   - large LLM-generated code needs DRYing and normalization to CLAUDE.md conventions,  
   - you want automated “cleanup PRs” separate from correctness changes.  

***

## Passing arguments to skills and slash commands

Claude Code’s skills system has a well-defined argument model, which bundled skills use too.[1][3]

### How arguments are passed

A command is recognized only at the start of your message; trailing text becomes its arguments.[3]

For skills (including bundled ones):

- `/skill-name arg1 arg2 "multi word arg3"`  
- All text after `/skill-name` is passed as arguments and can be interpolated into SKILL.md via:
  - `$ARGUMENTS` – full argument string.[1]
  - `$ARGUMENTS[N]` / `$N` – indexed arguments.[1]
  - `$named` – named arguments defined in frontmatter `arguments:`.[1]

If the skill doesn’t explicitly include `$ARGUMENTS`, Claude Code appends an `ARGUMENTS: <value>` line to the rendered skill body.[1]

Multi-skill chaining:

- As of v2.1.199, you can chain up to 6 skills at the start of a message:
  - `/code-review /fix-issue 123`  
  - `123` is passed as $ARGUMENTS to both skills.[3][1]

This applies to bundled skills like `/code-review`, `/simplify`, `/verify`, `/run`, etc., when they’re implemented as skills.[3][1]

### Example: custom “verify-by-pr” skill

You can build a custom orchestration skill around `/verify` that takes a PR number as argument:

```yaml
---
description: Run Claude Code's verify workflow for a given GitHub PR.
arguments: [pr]
disable-model-invocation: true
allowed-tools: Bash(gh pr checkout $pr) Bash(gh pr diff $pr)
---

1. Checkout the PR branch with `gh pr checkout $pr`.
2. Run `/verify` to perform runtime verification of the diff.
3. Summarize findings in a format suitable for reviewers.
```

Invocation:

- `/verify-pr 123` → `$pr` = `123`.[1]

CONSENSUS: this layering is favored by Anthropic’s docs—skills are composable; you keep `/verify` as the primitive but wrap it in project-specific skills that enforce additional rules or pre-steps.

***

## Testing and optimizing these skills in local development

### Where skills live and how to override bundled ones

Locations:[1]

- Personal: `~/.claude/skills/<skill-name>/SKILL.md` (all projects).[1]
- Project: `.claude/skills/<skill-name>/SKILL.md` (this repo only).[1]
- Plugin: `<plugin>/skills/<skill-name>/SKILL.md` (plugin-scoped).[1]

Override rules:

- Enterprise > Personal > Project override built-in/bundled skills by name.[1]
- A project-level `code-review` skill replaces the bundled `/code-review`.[1]

Optimal dev pattern:

1. **Discover** skills via `/` autocomplete and `/skills` UI, plus `ls ~/.claude/skills` and `ls .claude/skills`.[1]
2. **Audit** bundled skill behavior by reading the system prompts in the Piebald repo if needed (e.g. `/verify`).[4]
3. **Override locally**:
   - Create `.claude/skills/verify/SKILL.md` for project-specific verification rules (e.g. domain-specific probes, env bootstrapping).[1]
   - Keep the general structure from the upstream `skill-verify-skill.md` but specialize surfaces and evidence capture.[4]
4. **Test** usage:
   - In a git repo, make small changes and run `/verify`.  
   - Validate that it identifies the diff, picks the right surface, and reports PASS/FAIL/BLOCKED/SKIP with evidence.[4]

You can see whether a skill was actually loaded/used by inspecting session logs under `~/.claude/projects/*.jsonl`; messages include metadata on active and triggered skills.[6]

### Passing arguments and debugging skills

Frontmatter argument features:[1]

- `argument-hint` – what shows in autocomplete as expected arguments (`[issue-number]`).[1]
- `arguments: [issue, branch]` – names for `$issue` and `$branch` in content.[1]

Best practice for skill authoring:

- Use `$ARGUMENTS` or named arguments where you genuinely need structured input.[1]
- Keep SKILL.md under ~500 lines and move detail to supporting files (`reference.md`, `examples.md`).[1]
- Use `allowed-tools` to pre-approve specific commands when the skill is active (e.g. Bash for `git`), but audit for security.[1]

Testing loop in local dev (CONSENSUS):

1. Create a minimal skill with `description` and a simple body logging `$ARGUMENTS` into a file via bash injection (e.g. `!echo "$ARGUMENTS" >> logs/skills.log`).[1]
2. Run `/my-skill foo bar` and inspect the log to ensure argument interpolation works.[1]
3. Iterate on supporting scripts (`scripts/*.sh`, `scripts/*.py`) and call them via `` !`bash ${CLAUDE_SKILL_DIR}/scripts/my-script.sh "$ARGUMENTS"` ``.[1]
4. Use `/debug` to enable session debug logging, then let it troubleshoot issues by reading debug logs. `/debug` itself is a bundled skill.[3]

### Optimal workflows combining `/verify`, `/simplify`, `/code-review`

Putting it together for typical code-change workflows:

**Workflow A: Small feature or bugfix**

1. Write code.  
2. Run `/code-review high --fix` to catch correctness bugs and straightforward cleanups.[3]
3. Run `/simplify` to focus on refactoring, reuse, and efficiency.[5][3]
4. Run `/verify` to perform runtime verification at the appropriate surface, capturing evidence.[4][1]

Assumptions:

- You have a recorded run skill via `/run-skill-generator`, so `/verify` and `/run` build and launch reliably.[1]

**Workflow B: Large generated refactor**

1. Use `/batch` with an instruction like `migrate src/ from Solid to React`. It decomposes work into units, spawns subagents in worktrees, and opens PRs.[3]
2. For each PR:
   - Run `/code-review ultra --comment <pr#>` from your local branch for deep review.[3]
   - Run `/simplify` on the diff to normalize style and remove redundancy.[5][3]
   - Run `/verify` against the PR branch (possibly via a custom `/verify-pr` skill) to produce runtime evidence per PR.[4][1]

**Workflow C: Organization-wide verification protocol**

1. Define `verifier-cli`, `verifier-api`, `verifier-gui` skills in `.claude/skills/` for shared evidence-capture protocols.[4][1]
2. Teach `/verify` (via overridden SKILL.md in `.claude/skills/verify/`) to always look for and use the appropriate verifier based on surface type.[4]
3. Enforce minimal manual inputs:
   - Use arguments to capture the “claim” or PR number.  
   - Use `allowed-tools` to pre-approve `gh`, `git`, `npm`, etc., in verification contexts.[1]

***

I’m confident on the core behavior and usage patterns described above, as they’re grounded in current Claude Code docs plus the upstream `/verify` prompt; still, exact internals (like specific agent names behind `/simplify`) can change across versions without the docs immediately reflecting it, so it’s worth occasionally checking the latest commands and skills documentation from `https://code.claude.com/docs/llms.txt`.[5][1]

What’s the main codebase or stack you want to tune these workflows for first (e.g., TypeScript monorepo, Python services, mixed stack), so I can sketch a concrete SKILL.md for a verifier and simplifier tailored to that environment?  

## Human

how do I properly use /loop and /goal?  what domain do all these skills fall in?  what question would get more information on that domain skill group in claude code?

## Assistant

`/goal` gives Claude a measurable end condition and keeps the current session working toward it until that condition is met or you clear it, while `/loop` is a scheduler that reruns a prompt at intervals until you stop it or it decides the work is done.[1][2]

***

## How to use `/goal` properly

FACT: `/goal` sets a “completion condition” (a goal) and wires a small evaluator model to check after each turn whether that condition holds; if not, Claude automatically starts another turn instead of returning control to you.[1]

Basic usage:

- Set a goal with a condition:
  - `/goal all tests in test/auth pass and the lint step is clean`[1]
- As soon as you run this, Claude:
  - Treats the condition itself as the directive for the next turn (no extra prompt needed).[1]
  - Shows an `◎ /goal active` indicator and tracks how long it has been running.[1]
  - After each turn, a fast model explains why the condition *is or isn’t* met; that reason appears in the status view and transcript.[1]

Managing goals:

- See current state: `/goal` with no arguments (turns, tokens, latest evaluator reason).[1]
- Clear a goal: `/goal clear` (aliases: `stop`, `off`, `reset`, `none`, `cancel`).[1]
- Starting a new conversation via `/clear` also removes any active goal.[1]
- Only one goal can be active per session; setting a new one replaces the old.[1]

Designing good goals:

- The docs recommend goals with:[1]
  - One measurable end state (tests pass, exit code is 0, queue empty, file count reached).  
  - A stated **check**: how Claude should prove it (e.g. “`npm test` exits 0”, “`git status` is clean”).  
  - Relevant constraints: things that must not change (“no other test file is modified”).  
- You can include time/turn bounds in the condition, e.g.:
  - `/goal migrate auth module to new API and all tests pass or stop after 20 turns`[1]

Non-interactive usage:

- The same command works with `claude -p` in headless mode:
  - `claude -p "/goal CHANGELOG.md has an entry for every PR merged this week"`[1]
- You interrupt a non-interactive goal with Ctrl+C.[1]

CONSENSUS: treat `/goal` as a session-scoped “agent loop with a stop condition”: you specify the long-running task and its success condition; Claude uses tools, skills, and hooks to keep iterating until that condition is satisfied or you stop it.[3][4][1]

***

## How to use `/loop` properly

FACT: `/loop` is a scheduled-task command that runs a prompt repeatedly at a specified interval, creating an autonomous routine.[2][1]

Docs distinction:[1]

- `/goal` – next turn starts when the previous turn finishes; stops when a model confirms the condition is met.  
- `/loop` – next turn starts on a time interval; stops when you stop it or Claude decides the work is done.  

Typical syntax (community and docs):[4][2][1]

- `/loop <interval> "<prompt>"`  
  Examples:
  - `/loop 15m "check on the current goal and continue working toward it, adjusting the plan if needed"`[5]
  - `/loop 1h "summarize today’s new PRs and run /code-review ultra --comment on each"`[2]

Behavior:

- Under the hood, `/loop` creates a routine/cron-like job via the routines/scheduled-tasks system that triggers your prompt at that interval.[6][5][1]
- It can be configured to run until a condition is satisfied or a max iteration count is reached.[5]
- You stop it from the routines UI or with the appropriate stop/clear command for that loop.[2][1]

CONSENSUS: `/loop` is in the “schedule / automation” domain—think cron for prompts—while `/goal` is in the “completion condition / agent loop” domain.[6][1]

***

## How `/goal` and `/loop` work together

Community and blog patterns show `/goal` and `/loop` are designed to compose.[7][5][2][1]

Common pattern:

- Use `/goal` to define *what* success means:
  - `/goal decompile module X through all 12 stages with GOAL.md documenting progress`[5]
- Use `/loop` to periodically nudge and manage that goal:
  - `/loop 15m "continue pursuing the active goal, assess progress, and update GOAL.md for the next stage"`[5][2]

Advanced “treadmill effect” pattern:[5]

- Maintain a `GOAL.md` file with the current phase description and instructions for rewriting `GOAL.md` to describe the next phase when this one is done.[5]
- Set `/goal` to “complete the phase described in GOAL.md and then rewrite GOAL.md for the next phase”.[5]
- Claude reaches the end, rewrites GOAL.md, the goal’s condition effectively changes, and the loop continues into the next phase—yielding a multi-stage autonomous routine.[5]

Another documented approach: pair `/goal` with routines so a scheduled job re-runs “continue the goal” prompts without you being present, turning the combination into a full autonomous agent loop.[7][2]

***

## What “domain” these skills fall in

FACT: In Claude Code’s conceptual model, `/goal`, `/loop`, and related constructs sit in the **agentic automation / loop & routines** domain, not in the basic prompts or single-turn tooling domain.[7][6][1]

More concretely:

- `/goal` is part of the **agent loop / completion-condition** domain:
  - It uses the hooks system (a “Stop hook”-style evaluator) to decide after each turn whether to continue.[1]
  - It’s coupled with worktrees, skills, plugins, and state tracking—4 of the 5 pieces called out for effective loops.[6]
- `/loop` is part of the **scheduled routines / cron** domain:
  - It uses routines/scheduled tasks to repeatedly run a prompt.[6][1]
- Together they’re in what some docs and blogs call “loop engineering” or “agentic OS” layers in Claude Code: building autonomous agents with explicit goals plus schedules.[8][7][6]

CONSENSUS: The domain is “Claude Code agent loops and routines”—commands and skills that control multi-turn behavior, schedules, and stop conditions, often combined with skills, hooks, and subagents.

***

## Questions that reveal more about the “loop / goal” skill group

If you want Claude Code (or its docs) to expose and explain this domain more deeply, good questions are:

- “Show me all commands and skills related to loops, goals, routines, and scheduled tasks in this workspace, and map how they interact (hooks, subagents, worktrees).”  
  - This targets the loop-and-routines domain explicitly and forces enumeration plus architecture.[6][1]
- “Explain the architecture of agent loops in Claude Code: how `/goal`, `/loop`, routines, hooks, skills, and subagents fit together, and how to design a robust long-running loop for a codebase.”  
  - This pushes for systems-level explanation of the entire loop domain.[7][6]
- “List and describe all loop-related primitives (goal conditions, loops, routines, stop hooks) and give examples of when to use each for code migration, CI maintenance, or self-improving workflows.”  
  - This asks for a taxonomy of the loop domain and concrete workflows.[7][6][1]

Those questions make the “domain skill group” clear: agentic automation tools that let Claude run multi-turn, scheduled, and self-checking workflows anchored by `/goal` and `/loop`.

For your own work, what kind of long-running tasks are you most interested in wiring up first—codebase maintenance (e.g., lint/test enforcement), documentation refresh, or self-improving agent loops over your orchestration framework?  

## Human

but what about /verify, /simplify, /code-review, etc?

Build a GOAL.md template library for multi-stage Claude Code tasks — automate state tracking and phase shifts.  Or tell me great resources to use for this.

## Assistant

# GOAL.md Template Library for Multi-Stage Claude Code Tasks

This library provides practical `GOAL.md` patterns for long-running Claude Code workflows that use `/goal`, `/loop`, `/verify`, `/simplify`, and `/code-review`. Claude Code's `/goal` command keeps working until a completion condition is satisfied, while `/code-review` reviews diffs locally and `/simplify` runs a cleanup-only review.[1][2]

## How these commands fit together

These commands fall into two overlapping domains:

- **Agent loop / autonomous execution**: `/goal`, `/loop`, routines, stop hooks, and verification loops keep Claude operating across turns until a condition is met or a schedule stops.[3][1]
- **Quality gates / review-and-verify workflows**: `/verify`, `/code-review`, and `/simplify` check that a change works, is correct, and is structurally clean before you treat the task as done. `/code-review` replaced the older bug-finding use of `/simplify`, while `/simplify` now performs cleanup-only review.[2][4]

In practice, `/goal` is the coordinator, while review skills are phase gates. Anthropic's best-practices guide explicitly recommends giving Claude a runnable verification check, using `/goal` across a session, and adding adversarial or independent review before counting work as done.[3]

## Design principles for GOAL.md

A good `GOAL.md` should do four things:

1. **Define the current phase** in one sentence.
2. **State the stop condition** in a measurable form.
3. **Record evidence** Claude must collect before moving on.
4. **Describe the phase shift rule**: how to rewrite `GOAL.md` for the next phase.[1][3]

Use checks Claude can run directly: test exit codes, build success, PR comments, screenshot comparisons, queue emptiness, or runtime observations. Anthropic recommends using explicit checks because autonomous sessions degrade when "looks done" is the only signal.[3]

## Core frontmatter schema

Use this lightweight schema at the top of every `GOAL.md`.

```md
# GOAL.md

## Goal
<one-sentence objective for the current phase>

## Phase
<phase-name>

## Completion condition
<measurable condition that `/goal` can evaluate>

## Verification
- <test, build, runtime, screenshot, or diff review checks>

## Constraints
- <must not change>
- <safety or scope rules>

## Evidence to capture
- <exact commands, artifacts, screenshots, logs, or diffs>

## When complete, rewrite this file
Replace Goal, Phase, Completion condition, Verification, and Evidence sections
for the next phase, preserving the Progress Log.

## Progress Log
- <timestamp>: <what changed, what passed, what remains>
```

This format works well because `/goal` needs a crisp condition, and review commands benefit from explicit verification expectations and scope boundaries.[1][3]

## Template 1: Feature implementation pipeline

Use this for a normal multi-stage delivery path in a local repo.

```md
# GOAL.md

## Goal
Implement the feature described in SPEC.md and land it in a locally reviewable state.

## Phase
phase-2-implementation

## Completion condition
The implementation matches SPEC.md, targeted tests pass, lint/typecheck pass,
`/code-review high --fix` has been run, `/simplify` has been run, and no new
out-of-scope files were changed.

## Verification
- Run targeted tests for touched modules.
- Run lint and typecheck only for affected packages.
- Review the diff against SPEC.md requirements.
- Run `/code-review high --fix` on the current diff.
- Run `/simplify` on the current diff.

## Constraints
- Do not widen scope beyond SPEC.md.
- Reuse existing patterns from the touched package.
- Do not edit unrelated generated files.

## Evidence to capture
- Test command and exit code.
- Lint/typecheck command and exit code.
- Short summary of `/code-review` findings and fixes.
- Short summary of `/simplify` changes.
- Final `git diff --stat`.

## When complete, rewrite this file
Advance to phase-3-runtime-verification. Preserve the Progress Log.

## Progress Log
- 2026-07-10: Initialized implementation phase.
```
```

Why this works: Anthropic recommends a verification loop with runnable checks, and `/code-review` is explicitly designed to review diffs locally, optionally applying fixes. `/simplify` is the cleanup-only pass after correctness review. [cite:30][cite:40]

## Template 2: Runtime verification gate

Use this after implementation, especially for web apps, APIs, CLIs, or worker systems.

```md
# GOAL.md

## Goal
Prove the code change behaves correctly at the runtime surface it modifies.

## Phase
phase-3-runtime-verification

## Completion condition
The changed behavior has been exercised at the real runtime surface, evidence has
been captured, important failures are resolved, and the result is PASS or a
clearly documented BLOCKED state.

## Verification
- Run `/verify` against the current change.
- Prefer the smallest end-to-end path that exercises the changed behavior.
- Probe at least one edge case and one failure mode.

## Constraints
- Do not treat unit tests alone as proof of runtime behavior.
- Capture concrete evidence, not only assertions.

## Evidence to capture
- Commands used to launch or drive the system.
- Runtime output, HTTP responses, screenshots, or logs.
- PASS / FAIL / BLOCKED verdict with brief justification.

## When complete, rewrite this file
Advance to phase-4-polish-or-pr, depending on findings.

## Progress Log
- 2026-07-10: Waiting for runtime verification.
```
```

This template mirrors the documented purpose of `/verify`: it is meant to confirm a change by observing runtime behavior rather than relying only on tests or static inspection.[2][3]

## Template 3: PR hardening loop

Use this for long-lived branches or pre-merge cleanup.

```md
# GOAL.md

## Goal
Prepare the current branch for PR review with correctness, cleanup, and evidence complete.

## Phase
phase-pr-hardening

## Completion condition
The diff has been reviewed with `/code-review`, cleaned with `/simplify`, any
important findings are addressed, and the branch summary is ready for human review.

## Verification
- Run `/code-review high --comment <PR-or-target>` when a PR exists, otherwise run locally.
- Run `/simplify` after fixes land.
- Re-run targeted checks affected by fixes.

## Constraints
- Prefer high-signal fixes over broad refactors.
- Do not chase speculative style-only changes unless they simplify the diff.

## Evidence to capture
- Important findings still open.
- Nits intentionally deferred.
- Final review summary grouped by correctness, cleanup, and residual risk.

## When complete, rewrite this file
Advance to phase-human-review-followup or close the goal.

## Progress Log
- 2026-07-10: PR hardening phase initialized.
```
```

This template aligns with the official distinction: `/code-review` is the correctness-oriented diff review, and `/simplify` is the cleanup pass that no longer hunts for bugs. [cite:30]

## Template 4: Self-improving maintenance loop

Use this for repeated codebase improvement tasks.

```md
# GOAL.md

## Goal
Reduce one class of recurring codebase friction across the repo without breaking behavior.

## Phase
phase-identify-next-friction

## Completion condition
One high-value friction pattern has been identified from the current diff or codebase,
a bounded fix has been applied, review and verification have passed, and GOAL.md has
been rewritten for the next friction pattern.

## Verification
- Define one friction pattern only.
- Implement one bounded improvement.
- Run targeted verification for impacted areas.
- Run `/code-review` and `/simplify` before moving to the next pattern.

## Constraints
- No multi-pattern refactors in one phase.
- Stop if verification is ambiguous; document uncertainty.

## Evidence to capture
- Pattern selected and why.
- Files changed.
- Verification outcome.
- What next phase should optimize.

## When complete, rewrite this file
Set the next friction pattern as the new Goal and append a Progress Log entry.

## Progress Log
- 2026-07-10: Starting recurring improvement loop.
```
```

This pattern is a practical way to combine `/goal` with the iterative, phase-rewriting approach described in community loop-engineering examples. It works best when each phase has a bounded verification step.[1][3]

## Phase-shift rules

Use these rewrite rules consistently:

- **If verification passed cleanly**: rewrite `Goal`, `Phase`, and `Completion condition` for the next stage.
- **If review found important bugs**: rewrite into a remediation phase, not the next planned phase. `/code-review` is specifically intended to catch correctness gaps before merge.[2]
- **If `/verify` is blocked by environment**: rewrite into an environment-enablement phase with a concrete unblock condition.
- **If `/simplify` proposes large churn**: split that cleanup into a separate phase so the main goal does not drift.

A useful convention is to keep `Progress Log` append-only and allow every other section to be overwritten on phase transition.

## Practical command recipes

These are strong starting workflows for local development:

### Recipe A: single-session autonomous feature loop

1. Create `SPEC.md` and `GOAL.md`.
2. Start Claude with `/goal implement the phase described in GOAL.md and satisfy its completion condition`.[1]
3. Let implementation proceed.
4. When the phase demands it, run `/code-review high --fix`.[2]
5. Run `/simplify` for cleanup-only changes.[2]
6. Advance into the runtime verification template and run `/verify`.[2]
7. Rewrite `GOAL.md` for the next phase or close the goal.

### Recipe B: scheduled maintenance loop

1. Use a recurring prompt or `/loop` to revisit the active `GOAL.md`.
2. Limit each phase to one bounded improvement.
3. Require review and verification before phase rewrite.
4. Preserve an append-only `Progress Log` for auditability.

### Recipe C: reviewer-writer split

Anthropic recommends adding an adversarial review step using a fresh context or subagent before counting work as done. Use one session or subagent to implement, and another to review the diff against `GOAL.md` or `PLAN.md`.[3]

## Best resources

For high-authority material, start here:

- Claude Code `/goal` docs: how completion conditions and evaluator-driven looping work.[1]
- Claude Code best practices: verification loops, subagent review, session management, and automation patterns.[3]
- Claude Code Code Review docs: current semantics of `/code-review`, `/simplify`, local-vs-PR review, and `REVIEW.md` tuning.[2]
- Commands index: to discover renamed, bundled, and adjacent review/verification commands.[4]

For community interpretation, use secondary sources only after checking the official docs, especially because command names and behavior have changed over time. A concrete example: the old `/simplify` semantics for bug-finding were replaced by `/code-review`, and community posts often lag that rename.[5][2]

## Next extension ideas

Useful follow-on assets for this library:

- `GOAL-feature.md` — feature delivery template
- `GOAL-verify.md` — runtime verification template
- `GOAL-pr-hardening.md` — pre-merge review template
- `GOAL-maintenance-loop.md` — recurring improvement template
- `PHASES.md` — allowed phase names and transition rules
- `REVIEW.md` — repo-specific review calibration for Claude Code PR review[2]
