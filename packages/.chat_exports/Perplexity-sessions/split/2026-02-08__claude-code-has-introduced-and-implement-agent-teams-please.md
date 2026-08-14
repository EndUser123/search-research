---
title: "claude code has introduced and implement agent teams.  Please create instructions I can give to an LLM, so that then can"
date: "2026-02-08"
mode: "COPILOT"
uuid: "3c9f867b-3677-4104-893d-0a73a5b2887f"
entry_count: 6
---

## Human

claude code has introduced and implement agent teams.  Please create instructions I can give to an LLM, so that then can update a skill or prompt, to use the feature optimally.

## Assistant

Here’s a copy‑pastable instruction block you can give to another LLM when you want it to update a Claude Skill or project prompt to use Claude Code agent teams optimally.

You can use this as a system prompt, or as the leading part of a user message followed by your current skill/prompt text.

***

### Instruction block for an LLM: “Upgrade this to use Claude Code Agent Teams”

You are updating instructions that will run inside **Claude Code** with **agent teams** enabled. These instructions may live in a Claude Skill, project prompt, or other configuration that Claude Code loads as part of its project context.

Your job: **rewrite or extend the given skill/prompt so that Claude Code uses agent teams optimally when appropriate, while still working correctly when agent teams are not used.**

Follow these rules exactly:

***

#### 1. Understand the environment

1. Assume:
   - You are configuring **Claude Code** with **agent teams** available in research preview.[1][2]
   - Each teammate is a **full, independent Claude Code session** with:
     - Its own context window
     - The same project context as the lead (CLAUDE.md, MCP servers, Skills, etc.)[2]
   - There is a **team lead** (the main Claude Code session) plus zero or more **teammates**.[2]

2. Recall key properties of agent teams:[1][2]
   - Teammates **communicate directly with each other**, not just with the lead.
   - There is a **shared task list** with dependencies, statuses, and self‑claiming of tasks.
   - Lead can be put into **delegate mode** so it only orchestrates and does not directly implement.
   - Only **one team per session**; no nested teams; only the lead can spawn teammates.[2]

You must design instructions that respect these constraints.

***

#### 2. Decide when this workflow should use **agent teams** vs a single agent or subagents

Analyze the given skill/prompt and its intended workflow. Then:

1. Prefer **agent teams** for tasks that are:
   - **Parallelizable** across files/modules/components.
   - **Read-heavy** (e.g., codebase review, cross-cutting analysis, multi-perspective RCA).[1][2]
   - Benefit from **multiple perspectives or competing hypotheses** (e.g., debugging where root cause is unclear).[2]

2. Prefer a **single agent** or simple **subagents** when:
   - Work is mostly **sequential** and tightly coupled.
   - Only the final result matters; discussion/collaboration between agents adds little value.[3][2]
   - The task is small enough that parallelization is overhead.

3. In your rewritten instructions:
   - Add **clear criteria** for when to **propose** an agent team to the user.
   - Add **clear criteria** for when to stay as a single agent or use only subagents.

Example pattern you should encode (adapt to the domain):

> “If the user requests a deep, multi-file code review, large refactor, or ambiguous bug investigation with multiple possible causes, propose creating an agent team with specialized roles. If the task is small or localized to a single file, stay as a single agent.”

***

#### 3. Define an explicit default **team structure** for this workflow

When you decide agent teams are appropriate, design a **default team composition** and encode it in the skill/prompt as instructions for the lead.

1. For each major workflow the skill supports, define:
   - The **team lead’s** role (usually orchestration + synthesis).
   - 2–4 **teammate roles** with clear, non-overlapping responsibilities.

2. Express these roles concretely so Claude can spawn them via natural language, for example:

   - “Architect teammate”: designs refactor plans, high-level architecture, and invariants.
   - “Implementation teammate”: applies code changes, keeps to the approved plan.
   - “Reviewer teammate”: performs code review, tests, and safety/performance checks.
   - “Investigator teammates A/B”: explore competing hypotheses for a bug and challenge each other’s conclusions.[2]

3. In the instructions, include patterns like:

   - “When using an agent team for this workflow, spawn:
     - A lead coordinator (you).
     - An ‘Architect’ teammate focused on planning.
     - An ‘Implementation’ teammate focused on changes.
     - A ‘Reviewer’ teammate focused on testing and verification.”

4. Keep team size **minimal but effective** (usually 2–4 teammates) to control token cost.[4][5]

***

#### 4. Encode ** lead behavior** and use of **delegate mode** and **plan approval**

Modify the instructions so the lead behaves like a disciplined orchestrator.

1. **Delegate mode**:
   - In your rewritten text, explicitly instruct:
     - The lead should **use delegate mode** for complex, parallel work so it focuses on orchestration rather than editing code.
   - Example wording to embed:

     > “For complex, parallelizable tasks (e.g., multi-module refactors, large code reviews), enter delegate mode so you only coordinate teammates (spawning, assigning tasks, messaging, shutting down) and do not directly edit code yourself.”[2]

2. **Planning and plan approval**:
   - Instruct that certain teammates must **plan first**, then request approval:
     - Architect/Investigator teammates should produce a written plan before implementation.
     - The lead should require **plan approval** for risky tasks: refactors, schema changes, critical infra changes.[2]
   - Encode criteria for approval, e.g.:

     > “Only approve plans that:
     >  - Include clear scope and non-goals
     >  - Specify affected files/modules
     >  - Include test coverage and rollback strategy
     >  - Minimize unnecessary changes”

3. **Synthesis and shutdown**:
   - Instruct the lead to:
     - Periodically **summarize intermediate progress** across teammates.
     - **Shut down** teammates and clean up the team once work is complete.

***

#### 5. Use the **shared task list** explicitly

Update the instructions to make good use of the shared task list mechanism.[2]

1. In your rewritten text, tell the lead to:
   - Break work into **atomic, dependency-aware tasks**:
     - Each task should be small, concrete, and testable.
     - Use dependencies when one task relies on the output of another.
   - Assign tasks in two ways:
     - **Lead assigns**: directly assign tasks to specific teammates for critical or ordered work.
     - **Self-claim**: allow teammates to pick up the next unblocked task when possible to maximize parallelism.[2]

2. Provide patterns like:

   > “Decompose the requested work into a set of small tasks with clear dependencies. Mark tasks as pending, in progress, or completed. Allow teammates to self-claim unblocked tasks, except for high-risk changes, which you should explicitly assign.”

3. Instruct teammates (via the prompt text) to:
   - Update task status promptly.
   - Add follow-up tasks when they discover additional necessary work.

***

#### 6. Optimize **information sharing** between teammates

Given each teammate has its own context, and communication is via messaging and shared tasks:[2]

1. In your rewritten prompt, instruct teammates to:
   - Share **concise, structured updates** with each other (not just with the lead) when they:
     - Discover important constraints or invariants.
     - Make design decisions that affect others.
     - Identify risks, blockers, or inconsistencies.

2. Encourage patterns like:
   - Short, labeled messages (“[Finding]”, “[Assumption]”, “[Risk]”) exchanged between teammates.
   - Explicitly challenging each other’s reasoning for root cause analysis:

     > “When investigating bugs with unclear root causes, each investigator should:
     >  - Form its own hypothesis.
     >  - Actively challenge other hypotheses and present counter-evidence.
     >  - Update or discard its own theory if evidence contradicts it.”[2]

3. Add guidance to avoid flooding:
   - Summaries over raw logs.
   - Only share information likely to impact other teammates’ work.

***

#### 7. Control **token cost** and failure modes

Explicitly encode safety and cost controls in the instructions.

1. Token/cost control:
   - Instruct the agent to:
     - Only propose agent teams for tasks that are **large enough** to justify the overhead.
     - **Limit team size** and complexity by default.
     - Prefer **short, structured messages** and concise plans.

2. UX & robustness:
   - Ensure the rewritten instructions:
     - Still make coherent sense even if agent teams are disabled; they should gracefully degenerate to a single-agent workflow (e.g., “if teams are not available, approximate these roles sequentially yourself”).
     - Never assume nested teams or more than one team per session.

3. Add a fallback clause such as:

   > “If you cannot create or use an agent team for any reason, approximate this team structure within a single session, working sequentially but preserving the same roles, checks, and planning discipline.”

***

#### 8. Preserve and enhance the original skill logic

When rewriting:

1. **Do not change the core intent** of the skill/prompt:
   - Preserve business rules, domain constraints, and safety requirements.
   - Keep existing MCP/tool usage logic and constraints intact.

2. **Enhance** the skill by:
   - Adding a short section near the top describing **when and how** to use agent teams for this workflow.
   - Integrating team-specific behavior into existing sections (planning, execution, review, safety).

3. Output:
   - Return a **single, updated version** of the skill or prompt, fully rewritten as if it will be used directly by Claude Code.
   - Do **not** include explanations, commentary, or diff markup—only the final updated instructions.

***

#### 9. Output format

- Your final answer must be **only** the updated skill/prompt text, ready to paste into a Claude Skill or project configuration.
- Do not add meta-explanations or surrounding commentary.
- Keep the style consistent with the original skill (tone, structure, headings) while adding the agent-team-specific guidance described above.

***

You must follow all the rules above when updating the provided skill or prompt.

***

If you paste this as the “system” or top-level instruction, you can then append:

> “Here is the current skill/prompt you should upgrade:  
> ```  
> …  
> ```”

and the other LLM should output a team-aware version that uses Claude Code’s agent teams in a disciplined way.

## Human

Are there conditions or triggers where it makes sense to use subagents vs agent teams?

## Assistant

Yes, Claude Code distinguishes subagents and agent teams by their architecture, communication needs, and cost profiles, with clear triggers for each. Subagents operate within a single session, while agent teams use independent sessions for deeper collaboration.[1][2]

## Key Differences

| Aspect | Subagents | Agent Teams [1][3] |
|--------|-----------|-----------------------------|
| Context | Own window; results summarized back to main agent | Fully independent sessions |
| Communication | Only reports to main agent | Direct messaging between teammates |
| Coordination | Main agent directs all work | Shared task list; self-claiming and dependencies |
| Token Cost | Lower (within one session) | Higher (separate instances) |
| Limitations | No inter-agent discussion | No nesting; one team per session; no resume with active teammates [1] |

## Use Subagents When

Subagents suit quick, focused delegation without peer interaction.
- Tasks need only final results, like single-file analysis, research, or retrieval (e.g., log scanning).[2][4]
- Sequential or iterative work with tight main-agent oversight.
- Cost or latency matters, as they avoid full-session overhead.[1]
- Context preservation for specialized prompts without cluttering the main chat.[5]

## Use Agent Teams When

Agent teams excel at collaborative, parallel work requiring discussion.
- Teammates must share findings, challenge hypotheses, or coordinate (e.g., multi-module debugging, refactors).[6][1]
- Complex builds with competing perspectives or cross-dependencies.
- Visibility into individual progress via split panes or tmux, for real-time intervention.[4]
- Tasks large enough to justify coordination overhead, like full-feature development.[1]

## Decision Triggers

Choose based on workflow needs:
- **No inter-agent talk needed** → Subagents (e.g., "analyze this log").
- **Teammates debate or sync** → Agent teams (e.g., "frontend/backend teams align API").
- **Small/quick** → Single agent or subagents; **large/collaborative** → Teams.[3][7]

## Human

please update the agent teams guidance to include the optimal conditions for subagents, allowing the possibility of both subagents and agents teams to be used, even at the same time.

## Assistant

Claude Code supports both subagents (lightweight delegation within a session) and agent teams (independent sessions with direct communication), and they can be combined in the same workflow for optimal parallelism. Here's the updated instruction block incorporating subagents as complementary tools, with triggers for each and hybrid usage patterns.[1][2]

***

### Updated Instruction Block: “Upgrade to Use Claude Code Agent Teams + Subagents Optimally”

You are updating instructions that will run inside **Claude Code** with **agent teams** and **subagents** available. These instructions may live in a Claude Skill, project prompt, or other configuration.

Your job: **rewrite or extend the given skill/prompt to use agent teams, subagents, or both optimally based on task needs, while preserving single-agent compatibility.**

Follow these rules exactly:

***

#### 1. Understand the Environment

- **Agent Teams**: Independent Claude Code sessions with shared task lists, direct teammate messaging, and full project context (CLAUDE.md, MCP, skills). Best for collaboration.[1]
- **Subagents**: Lightweight delegation within one session. Own context, tool restrictions, but only report to main agent—no inter-subagent talk. Lower cost, faster startup.[2]
- **Key Difference**: Subagents for focused results; teams for discussion/coordination.[1]

***

#### 2. Decision Triggers: Subagents vs. Agent Teams vs. Both

Analyze the workflow and encode **explicit criteria**:

| Scenario | Use Subagents [2] | Use Agent Teams [1] | Use Hybrid (Both) |
|----------|------------------------|--------------------------|-------------------|
| Quick research/retrieval (e.g., logs, docs) | ✅ Focused, low-cost | ❌ Overhead | N/A |
| Sequential tasks with main oversight | ✅ Chainable | ❌ Rigid | ✅ Subagents for prep |
| Parallel collaboration/debate (e.g., debugging hypotheses) | ❌ No peer talk | ✅ Direct messaging | ✅ Teams + subagents per teammate |
| Multi-module refactor/review | ❌ Context limits | ✅ Independent contexts | ✅ Teams own modules; subagents for tests/lint |
| Cost/latency sensitive | ✅ Inherit permissions | ❌ Separate sessions | ✅ Teams only if justified |

- **Default Rule**: Propose subagents first for simple delegation; escalate to teams for coordination; hybrid for complex flows (e.g., team lead uses subagents internally).[2][1]
- **Fallback**: If teams/subagents unavailable, sequential single-agent.

Example to embed:
> "For quick analysis: delegate to subagents. For cross-module coordination: spawn agent team. For large refactors: agent team where each teammate uses subagents for verification."

***

#### 3. Hybrid Usage Patterns

Enable **combining both**:
- **Team lead uses subagents**: Lead orchestrates team but delegates internal tasks (e.g., linting) to subagents.[2]
- **Teammates spawn subagents**: Each teammate uses subagents for focused work (e.g., "Architect teammate: use code-reviewer subagent to validate plan"). Subagents can't spawn others, but chaining works.[2]
- **Prep with subagents, then team**: Subagents explore upfront; results feed into team spawn prompt.

Example patterns:
> "Spawn agent team for multi-module work. Have each teammate use the 'test-runner' subagent to verify changes before marking tasks complete."

***

#### 4. Team Structure (When Using Agent Teams)

Default 2–4 teammates + subagent delegation:
- Lead: Orchestrate + synthesize (use delegate mode).
- Roles: Architect (plans, uses subagents for validation), Implementer, Reviewer (subagent-heavy for checks).[1]

***

#### 5. Lead & Delegate Mode

- **Delegate Mode**: Lead only coordinates (spawn, message, tasks). Use subagents for lead's internal helpers.[1]
- Planning: Require teammate plans; approve based on criteria (e.g., subagent-verified tests).

***

#### 6. Shared Task List & Communication

- Tasks: Atomic, dependencies; self-claim or assign.
- Messages: Structured (e.g., "[Finding]"); subagent results can trigger team broadcasts.[1]

***

#### 7. Subagent Optimization

When delegating to subagents:
- Define/reuse project/user-level subagents (e.g., via `/agents`).[2]
- Restrict tools (e.g., read-only for reviewers).
- Background for non-blocking; foreground for iteration.
- Resume via agent ID for continuity.

***

#### 8. Cost & Safety Controls

- Subagents: Lower tokens; ideal for routine.
- Teams: Reserve for parallel gains; limit size.
- Fallback: "Approximate with single agent + subagents if teams disabled."

***

#### 9. Output

Single updated skill/prompt text only—no commentary.

***

Paste this before your skill/prompt for an LLM to upgrade it with both features.[2][1]

## Human

do the agent teams use the same environment as the initial claude code cli?

## Assistant

Yes, agent teams in Claude Code use the same project environment as the initial CLI session. Each teammate loads identical project context from CLAUDE.md, MCP servers, and skills.[1]

## Shared Elements

Teammates inherit the full environment:
- **Project files**: Same working directory and codebase access.[2][1]
- **Configuration**: CLAUDE.md, custom skills, MCP tools propagate automatically.[3][1]
- **CLI setup**: Same Claude model, environment variables (e.g., `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), and permissions.[2]

## Non-Shared Elements

Differences ensure independence:
- **Context windows**: Each has its own; no lead history carryover, only spawn prompt.[1]
- **Sessions**: Separate processes; own terminals/panes for viewing.[1]
- **State**: Shared task list (`~/.claude/tasks/`) and mailboxes for coordination, stored locally.[4][1]

This setup enables parallel work on the same codebase without conflicts, via task locks and messaging.[2][1]

## Human

meaning if I use glm as the ai for claude code, all the agent teams started will use glm also?

## Assistant

Yes, if you configure Claude Code CLI to use GLM (e.g., GLM-4.7 via API proxy or settings.local.json), all spawned agent team teammates will use the same GLM model. Teammates inherit the CLI's model configuration and environment settings.[1][2]

## How Inheritance Works

Agent teams launch as separate CLI instances from the same project:
- **Model flag**: CLI args like `--model glm-4.7` or env vars propagate to teammates.[2][3]
- **API endpoints**: Custom GLM proxies (e.g., Claudish API) are shared via config files.[2]
- **Project context**: CLAUDE.md, skills, and MCP remain identical across all.[1]

## Limitations & Tips

- **Plan limits**: GLM plans cap parallel connections (e.g., 3–5 on $3–$12 tiers), so limit team size.[2]
- **Verification**: Check CLI output shows GLM model for lead and teammates; no override unless explicitly set in spawn prompt.[2]
- **Mixed models**: Not natively supported—teams use uniform inheritance. For variety, use subagents with model restrictions or manual CLI spawns.[4][1]

This ensures consistent behavior across the team while respecting your GLM setup.[3][2]

## Human

don't I need to set an option or env for the agent teams to work?

## Assistant

Yes, agent teams are experimental and disabled by default in Claude Code. You must enable them explicitly via the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable.[1]

## Enable Methods

Two equivalent options persist across sessions:

**Shell Environment** (temporary or via `.bashrc`/`.zshrc`):
```
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**settings.json** (recommended; `~/.claude/settings.json`):
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```
Restart CLI after changes.[2][1]

## Verification

- Check CLI startup logs: "Agent teams: enabled".
- Prompt Claude: "Are agent teams available?" → Confirms if flag active.[3]
- Once enabled, instruct naturally (e.g., "Create an agent team for..."). No further flags needed.[4][1]

Update to latest Claude Code first for compatibility.[4]
