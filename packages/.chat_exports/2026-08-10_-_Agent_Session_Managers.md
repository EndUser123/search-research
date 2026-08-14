# 2026-08-10 - Agent Session Managers

- **Created:** 8/13/2026, 7:40:10 AM
- **Exported:** 8/13/2026, 7:40:11 AM
- **Messages:** 4
- **Source:** browser_extension

---

## #1 · user

I run between five and ten concurrent agentic CLIs like Claude Code, Grok Build, etc., Codex. What session management tools would be good for me to use? I know of Orca, I know of Herder, but I don't know of any others, and I don't know which ones are good or which ones have features that matter. Please do the research and let me know what you think. Ask me any questions you think are needed in order to help identify a list of prospective repos or tools.

## #2 · assistant

Yes. I did an initial sweep, and there are **more credible options than Orca and Herder**, including a few I think may fit your 5–10 concurrent-CLI workflow better.

The key insight from the first pass is that these tools actually fall into **different product classes**, so comparing them simply as "session managers" will hide important differences.

### The shortlist I want to investigate

| Tool | What it appears strongest at | Initial fit |
| --- | --- | --- |
| Agent Deck | Multi-CLI TUI + persistent sessions + agent status + programmatic control + orchestration | Very high |
| Orca (Stably) | Full graphical agent development environment; terminals + worktrees + mobile | Very high |
| Claude Squad | Lightweight multi-agent TUI + worktree isolation + review/apply workflow | High |
| Superset | Persistent terminal environment purpose-built around many agents/worktrees | High |
| dmux | tmux/worktree fleet management, multi-project and multi-agent | High |
| cmux | Very lean worktree/session lifecycle | Medium-high |
| tmux-agent-status | Keep existing terminals/tmux, add "who needs me?" visibility | Medium-high |
| Tmux Workbench | Search/navigation/context across lots of existing tmux sessions | Interesting |
| Claude Deck | Claude/Codex coordination, configuration, Agent Mail/Teams | Interesting |
| Vibe Kanban | Task-level orchestration/review/worktrees rather than terminals | Don't adopt now |

One warning: Vibe Kanban is explicitly **sunsetting**, despite having an unusually broad list of supported CLIs, including Claude Code, Codex, Gemini, OpenCode, Cursor, Droid, CCR and Qwen. I would use it as a **design reference**, not select it as your foundation. [[image]Vibe Kanban+1](https://vibekanban.com/docs/supported-coding-agents?utm_source=chatgpt.com)

## One candidate already stands out: Agent Deck

Agent Deck is substantially more interesting than "a nicer tmux."

It manages Claude, Gemini, OpenCode, Codex and others, but critically it also exposes operations for creating sessions, sending input, obtaining output, starting/stopping/forking sessions, managing worktrees and attaching MCP servers. [[image]GitHub+1](https://github.com/asheshgoplani/agent-deck?utm_source=chatgpt.com)

That means the architecture can become:

**You → primary agent/orchestrator → Agent Deck API/CLI → 5–10 persistent CLI agents**

rather than:

**You → terminal manager → manually babysit 10 terminals.**

There is already a demonstrated Claude integration where Claude invokes Agent Deck to spawn Gemini and Codex sessions, sends them work, retrieves their answers and synthesizes the results. [[image]Reddit](https://www.reddit.com/r/ClaudeCode/comments/1qu4kg7/using_claude_as_an_orchestrator_to_consult_gemini/?utm_source=chatgpt.com)

That capability is particularly relevant because session management for you isn't merely a UI problem. **Machine-controllable session management** could become part of the orchestration layer itself.

## Another important distinction: Orca is ambiguous

There are at least **three unrelated Orca projects** relevant to coding agents.

The Stably Orca is a fairly ambitious graphical environment: Codex, Claude Code, OpenCode and Pi side-by-side, isolated worktrees, terminal splitting, persistent terminals and mobile monitoring/control. [[image]GitHub+1](https://github.com/stablyai/orca?utm_source=chatgpt.com)

There's also [alex2481kobe/orca](https://github.com/alex2481kobe/orca?utm_source=chatgpt.com), which is almost the opposite philosophy: a local harness that lets existing Claude/Codex agents spawn dependent subagents via MCP with governed lanes, worktree isolation, audit gates and phone monitoring. Its author explicitly removed much of the earlier UI/provider machinery to concentrate on the harness. [[image]GitHub](https://github.com/alex2481kobe/orca?utm_source=chatgpt.com)

And [VirtusLab/orca](https://github.com/VirtusLab/orca?utm_source=chatgpt.com) is a deterministic workflow/orchestration framework where coding, planning and reviewing agents can be assigned different backends and flows are resumable. [[image]GitHub](https://github.com/VirtusLab/orca?utm_source=chatgpt.com)

So I need to know **which Orca you meant**.

## The feature that may matter more than UI

At 5–10 simultaneous agents, I think your actual problem decomposes into at least:

**Persistence → Identity → Isolation → Attention → Navigation → Control → Coordination → Integration → Verification**

For example, Superset attacks persistence strongly: its terminal processes run in a background daemon, survive application restarts, retain scrollback, and agents can operate in isolated worktrees. [[image]Reddit+1](https://www.reddit.com/r/ClaudeCode/comments/1qk7bbz/i_built_a_os_terminal_that_wont_kill_your_claude/?utm_source=chatgpt.com)

Claude Squad emphasizes isolated workspaces and lets you inspect changes before applying them. [[image]GitHub](https://github.com/smtg-ai/claude-squad?utm_source=chatgpt.com)

cmux deliberately stays tiny: worktree creation, session continuation, merge and teardown. It was specifically built around the problem of running roughly **5–10 parallel agents**. [[image]GitHub+1](https://github.com/craigsc/cmux?utm_source=chatgpt.com)

And `tmux-agent-status` takes yet another approach: don't replace your terminal environment at all; just surface which Claude/Codex agents are working, done, failed or waiting for you. [[image]Reddit+1](https://www.reddit.com/r/codex/comments/1rozuul/tmux_plugin_to_track_codex_cli_status_across/?utm_source=chatgpt.com)

Those are fundamentally different solutions.

## Questions that will materially change my ranking

Rather than asking you twenty configuration questions, I think these **seven** divide the solution space:

1. 
**Windows:** Are these CLIs primarily running natively under Windows/PowerShell, under WSL2, or a mixture? This is potentially a major eliminator because several candidates assume Unix/tmux.

2. 
**Existing terminals:** Would you happily replace your current terminal windows with a dedicated TUI/GUI such as Agent Deck/Orca/Superset, or should the manager sit **above your existing terminals without owning them**?

3. 
**Session persistence:** When you close/reboot/restart something, how important is returning to the **exact interactive CLI session**, rather than merely being able to `claude --resume`/equivalent?

4. 
**Worktree ownership:** Do you want the manager automatically creating one git worktree per coding task, or do you already have mechanisms that should remain authoritative for worktree creation and cleanup?

5. 
**Human attention:** Is one of your biggest problems currently *"I have ten agents running and don't know which one is waiting for me / finished / failed"*? If yes, I will heavily weight reliable status detection and notifications.

6. 
**Machine control:** Should another agent be able to say essentially **"create a GLM/Grok Build session for this task, send this prompt, wait for completion, retrieve the result"**? If yes, CLI/API/MCP control becomes a first-class requirement and will dramatically change the rankings.

7. 
**Scope:** Do you primarily want **session management**, or would you welcome the tool eventually becoming the control plane for your agent fleet—session management + worktrees + routing + orchestration + review/merge + telemetry?

I deliberately **wouldn't constrain the selection based on migration/refactoring effort**. The question should be which architecture gives you the best steady-state system, even if adopting it means changing how the current setup works.

### Where I'm leaning before your answers

My hypothesis worth testing is:

> 
**Agent Deck may be the strongest foundation if you want the session manager to become machine-controllable infrastructure; Superset/Stably Orca may win if the human UX is paramount; a tmux-based layer such as dmux may win if you want maximum composability and minimal replacement of your existing architecture.**

I don't have enough evidence yet to crown one. In particular, I want to investigate **Herder properly, Agent Deck's actual control interfaces, Superset's programmability, Windows/WSL behavior, status-detection reliability, session identity, and whether any of these can accommodate Grok Build rather than merely the usual Claude/Codex/Gemini/OpenCode set.**

Answer those seven questions—even very briefly—and I'll do the deeper repository-level comparison, including **architecture, activity/maintenance, agent support, persistence, status detection, Windows support, worktrees, hooks, API/MCP/CLI control, notifications, mobile access, orchestration potential, extensibility, failure modes, and what we'd have to build ourselves**.

## #3 · user

1. Native powershell 
2. Don’t care as long as everything works well
3. It hasn’t been important because I didn’t have it but it could be useful
4. Existing solution doesn’t work well
5. Yes
6. Not critical but nice to have maybe
7 don’t know

## #4 · assistant

Based on your answers and a deeper repo-level sweep, I would **change the shortlist substantially**.

Because you run **native PowerShell**, not WSL, a lot of the popular “agent session managers” are poor fits regardless of how good they look on Unix. Your highest-value requirement is also clearer now: **you need an attention-management system for a fleet of 5–10 agents**, not just prettier terminal tabs.

## My ranking for your setup

| Rank | Tool | Native Windows | Agent status / attention | Worktrees | Multi-agent CLI support | Persistence | My assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Herdr | Beta | Excellent | Some/plug-in dependent | Excellent, incl. Grok | Excellent | Best match to the immediate problem |
| 2 | Agent Orchestrator | Yes | Excellent | Excellent | Excellent, incl. Grok | Strong | Best candidate if you want a future control plane |
| 3 | TUICommander | Yes | Excellent | Excellent | Very broad, incl. Grok | Excellent | Possibly best human-facing workspace |
| 4 | CCManager | ⚠️ Unverified native Windows | Very good | Very good | Good | Moderate | Very appealing lightweight design |
| 5 | Parallel Code | needs verification | Good | Excellent | Claude/Codex/Gemini/Copilot | Good | Excellent task/worktree manager, less fleet-oriented |
| 6 | Superset | No native Windows release currently | Excellent | Excellent | Excellent | Excellent | Would rank near top otherwise |
| 7 | Agent Deck | WSL only on Windows | Excellent | Excellent | Excellent | Excellent | Wrong environment for you |
| 8 | dmux / Claude Squad / cmux | tmux/Unix centric | varying | Excellent | varying | strong | Wrong foundation for native PowerShell |

There are two distinct winners because **Herdr and Agent Orchestrator solve different layers of your problem**.

# 1. Herdr — my current first thing to test

This is the project you called “Herder”; its actual name is **Herdr**.

Herdr has converged almost exactly on the pain point you described. It runs a background server that owns actual terminal sessions, and every agent is classified into states such as **working, blocked, done, or idle**. The explicit design goal is that you don't inspect ten terminals to find the one waiting for you. [[image]Herdr+1](https://herdr.dev/)

That matters enormously.

Your current loop is effectively:

> 
start 5–10 agents → periodically inspect windows → discover one asked a question 15 minutes ago → respond → inspect the others → forget which task belonged where

Herdr changes it toward:

> 
start 5–10 agents → **attention queue identifies exceptions** → interact only with agents that need you

That's a much larger productivity improvement than session persistence by itself.

Herdr currently detects **19 agent CLIs**, explicitly including Claude Code, Codex, Cursor, OpenCode, Grok, Pi and others. It doesn't replace the agents; it owns their actual terminals. [[image]Herdr](https://herdr.dev/)

It also has:

- 
background persistence;

- 
terminal reattachment;

- 
restart/session restoration;

- 
CLI control;

- 
local socket API;

- 
remote/SSH access;

- 
phone access ecosystem;

- 
plugin architecture;

- 
agent state detection. [[image]Herdr+2[image]GitHub+2](https://herdr.dev/)

And importantly, it now has a **native Windows PowerShell installer**:

```
irm https://herdr.dev/install.ps1 | iex
```

However, Windows is explicitly labelled **beta**. [[image]Herdr](https://herdr.dev/)

### That beta label is the main blocking risk

I would not simply declare Herdr your winner yet.

The acceptance test needs to be real:

**PowerShell → Herdr → Claude Code + Grok Build + Codex → simultaneous native PTYs → detect waiting/running/done correctly → survive detach/reconnect → no input corruption.**

If that works reliably, Herdr becomes extremely compelling.

# 2. Agent Orchestrator is much more significant than I initially realized

This one deserves serious attention.

Agent Orchestrator has a **native Windows desktop release** and specifically supports a runtime architecture that isn't bound to tmux. [[image]GitHub](https://github.com/AgentWrapper/agent-orchestrator)

Its supported-agent list is unusually broad:

**Claude Code, Codex, Cursor, Kimi, OpenCode, Grok, Droid, Amp, Auggie, Agy, Qwen, Copilot, Goose, Cline, Pi and others.** [[image]GitHub+1](https://github.com/AgentWrapper/agent-orchestrator)

And its architecture looks like:

```
Task
  ↓
Agent Orchestrator
  ↓
isolated worktree + branch
  ↓
selected CLI agent
  ↓
Claude / Grok / Codex / etc.
  ↓
session state
  ↓
PR / CI / reviewer feedback
  ↓
feedback routed back to same worker
  ↓
human only when needed
```

That is much closer to a **fleet management control plane** than a terminal manager.

The daemon watches:

- 
session state;

- 
controller activity;

- 
pull requests;

- 
CI;

- 
review feedback;

- 
merge conflicts. [[image]GitHub](https://github.com/AgentWrapper/agent-orchestrator)

It then feeds those things back to the correct worker.

That last part is particularly important.

A session manager says:

> 
“Codex #4 has stopped.”

Agent Orchestrator wants to say:

> 
“Codex #4's PR failed CI; the failure has been sent back to Codex #4; it is working on the correction.”

That potentially removes an entire class of human coordination.

### This may actually have the highest ceiling for you

Given the broader agentic infrastructure you are building, I would investigate this before investing substantial effort in custom session/worktree orchestration.

It already embodies several mechanisms we have separately been designing:

**task → isolated workspace → agent → state → external evidence → feedback → agent → human escalation.** [[image]GitHub](https://github.com/AgentWrapper/agent-orchestrator)

That's a meaningful architectural overlap.

# 3. TUICommander surprised me

I initially had this too low.

TUICommander explicitly targets people running **5+ agents simultaneously**, which is almost exactly your usage profile. Its own product specification defines success partly as being able to spot a rate-limited or awaiting-input agent immediately while running that many workers. [[image]GitHub](https://github.com/sstraus/tuicommander/blob/main/PRODUCT.md?utm_source=chatgpt.com)

It is **native Windows/macOS/Linux**. [[image]TUICommander](https://tuicommander.com/)

It auto-detects at least:

- 
Claude Code

- 
Codex CLI

- 
Gemini

- 
Aider

- 
Amp

- 
Cursor Agent

- 
OpenCode

- 
Droid

- 
Goose

- 
**Grok**

- 
Pi. [[image]GitHub](https://github.com/sstraus/tuicommander?utm_source=chatgpt.com)

And it combines:

```
agent sessions
+ worktrees
+ terminal
+ status
+ questions/approvals
+ diffs
+ file browser
+ PRs
+ CI
+ usage information
+ persistence
```

It supports up to 50 terminal sessions and restores terminals, layouts and scroll history after restart. [[image]TUICommander](https://tuicommander.com/)

It also has a mobile companion that can show which agents need input and let you answer questions remotely. [[image]TUICommander](https://tuicommander.com/)

That's unusually close to the UX I'd design for you.

### There is an important Windows caveat

TUICommander has had real Windows-specific bugs, including keyboard behavior and configuration persistence issues. [[image]GitHub](https://github.com/sstraus/tuicommander/issues/23?utm_source=chatgpt.com)

Even more importantly, some of its more precise instrumentation is currently macOS/Linux only, while **Windows retains heuristic state detection**. [[image]GitHub](https://github.com/sstraus/tuicommander/releases?utm_source=chatgpt.com)

That matters because **status correctness is one of your highest priority requirements**.

So:

> 
TUICommander has possibly the best feature UX, but Herdr may have the cleaner core runtime architecture.

I would test both.

# 4. CCManager deserves more attention than most lists give it

This is one of the cleaner “do the one job properly” projects.

CCManager supports:

Claude, Gemini, Codex, Cursor Agent, Copilot CLI, Cline, OpenCode and Kimi. [[image]GitHub](https://github.com/kbwo/ccmanager)

Its strongest feature for you is that it explicitly tracks:

**busy / waiting / idle**

and has **configurable state detection strategies per CLI** plus **status-change hooks**. [[image]GitHub](https://github.com/kbwo/ccmanager)

That last bit is valuable.

For example:

```
Claude waiting
        ↓
CCManager state detector
        ↓
status transition hook
        ↓
Windows notification / sound / dashboard / webhook
```

It also manages worktrees itself:

```
new task
 ↓
create worktree
 ↓
launch selected agent
 ↓
monitor state
 ↓
merge/delete worktree
```

[[image]GitHub](https://github.com/kbwo/ccmanager)

And it deliberately **does not depend on tmux**. [[image]GitHub](https://github.com/kbwo/ccmanager)

### Why isn't it ranked higher?

I couldn't establish from its primary documentation that **native Windows is an explicitly supported/tested target**. Its docs contain Unix-style configuration examples, and unlike Herdr, AO and TUICommander, it doesn't prominently state Windows support. [[image]GitHub](https://github.com/kbwo/ccmanager/blob/main/docs/multi-project.md?utm_source=chatgpt.com)

I therefore consider native Windows compatibility a **blocking prerequisite to validate**, rather than assuming Node means Windows.

If it works correctly in native PowerShell, I'd move it up.

# The tools I'd eliminate for now

## Agent Deck

Agent Deck itself answers the question clearly:

> 
Windows support is via WSL; WSL2 is recommended.

[[image]GitHub](https://github.com/asheshgoplani/agent-deck)

That's enough for me to remove it from your primary candidates.

It's otherwise excellent—status detection, worktrees, fleet recovery, MCP, cost tracking, API-style control—but adopting WSL merely to accommodate the session manager makes little architectural sense when native alternatives exist. [[image]GitHub+1](https://github.com/asheshgoplani/agent-deck)

## dmux / Claude Squad / cmux

Same basic problem.

Their design strength comes from:

```
tmux
  +
git worktree
  +
agent CLI
```

dmux in particular has a very elegant model where every task becomes a pane + worktree + branch and can even create A/B agent pairs. [[image]GitHub+1](https://github.com/standardagents/dmux?utm_source=chatgpt.com)

But **tmux is not your substrate**.

I wouldn't redesign your Windows environment around one.

# Superset

Superset is one of the strongest products conceptually.

It has:

- 
10+ agents;

- 
per-task worktrees;

- 
attention indicators;

- 
persistent terminals;

- 
diff review;

- 
custom agents;

- 
model picker;

- 
CLI;

- 
SDK;

- 
MCP;

- 
remote workspaces;

- 
scheduled automation. [[image]GitHub](https://github.com/superset-sh/superset)

That feature set is formidable.

But its current repo presents a **macOS desktop download**, not a native Windows client. [[image]GitHub](https://github.com/superset-sh/superset)

So I'm not recommending it for this machine right now.

# A project I would keep an eye on: Microsoft Intelligent Terminal

This wasn't in my original list.

Microsoft is working on agent-aware infrastructure around **Windows Terminal itself**, including an agent orchestrator (`wta`) that can delegate to agents and a Windows Terminal protocol allowing agents to control terminal surfaces. [[image]GitHub](https://github.com/microsoft/intelligent-terminal/blob/main/AGENTS.md?utm_source=chatgpt.com)

Architecturally, that is extremely interesting for you because it attacks the problem from below:

```
Windows Terminal
      ↑
native protocol
      ↑
agents + orchestrator
```

rather than:

```
third-party terminal emulator
      ↑
pseudo-terminal wrapper
      ↑
agents
```

But there are still integration bugs. For example, Claude and Codex adapter sessions currently have cases where agent hook events don't propagate into Windows Terminal's session registry correctly. [[image]GitHub](https://github.com/microsoft/intelligent-terminal/issues/48?utm_source=chatgpt.com)

So I see it as a **watchlist project**, not today's answer.

# I think requirement #7 can now be answered

You said you don't know whether you want session management or a broader control plane.

I think you **shouldn't decide that upfront**.

Instead, establish three layers.

```
                     YOUR AGENT SYSTEM

┌────────────────────────────────────────────────────┐
│ 3. ORCHESTRATION                                   │
│ task decomposition / routing / reviews / feedback │
└───────────────────────┬────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────┐
│ 2. FLEET CONTROL                                   │
│ status / worktrees / agent identity / attention   │
└───────────────────────┬────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────┐
│ 1. SESSION RUNTIME                                 │
│ PTY / persistence / input-output / reconnect      │
└───────────────────────┬────────────────────────────┘
                        │
            Claude / Grok / Codex / Pi
```

Right now your greatest pain is **Layer 2**.

You don't need a giant orchestration framework merely to solve that.

But you should choose a Layer-2 system that **doesn't prevent Layer 3 later**.

That's why Herdr and AO become so interesting.

# The two architectures I would test

### Option A — thin and composable

```
                Existing orchestration
                        │
                        ▼
                    HERDR
               ┌────────┼────────┐
               ▼        ▼        ▼
            Claude    Grok     Codex
               │        │        │
               └────────┼────────┘
                        ▼
                 attention queue
                        │
                        ▼
                       YOU
```

Herdr owns sessions/status.

Your own machinery continues making routing/reasoning decisions.

This gives you the least coupling.

### Option B — integrated agent control plane

```
                        YOU
                         │
                         ▼
              AGENT ORCHESTRATOR
             ┌───────────┼──────────┐
             │           │          │
          Task A       Task B     Task C
             │           │          │
             ▼           ▼          ▼
         worktree     worktree    worktree
             │           │          │
           Claude       Grok       Codex
             │           │          │
             ▼           ▼          ▼
            PR/CI       PR/CI      PR/CI
             └───────────┼──────────┘
                         ▼
                 feedback automation
                         │
               human exceptions only
```

This potentially replaces much more infrastructure.

# What I'd actually do

I would **not pick a winner from documentation**.

I'd perform a small bake-off with the real CLIs you actually use.

The primary contestants should be:

1. 
**Herdr**

2. 
**Agent Orchestrator**

3. 
**TUICommander**

Then optionally CCManager.

Each should receive the exact same test.

### Acceptance workload

Launch:

```
2 × Grok Build
2 × Claude Code
2 × Codex
1 × arbitrary shell
```

Have them perform real tasks across at least two repositories.

Then deliberately trigger:

- 
agent actively working;

- 
agent waiting for permission;

- 
agent asking a question;

- 
agent idle after completion;

- 
crashed CLI;

- 
CLI rate limit;

- 
long-running shell command;

- 
two worktrees from the same repository;

- 
terminal detach/reconnect;

- 
application restart.

### Success criteria

A tool passes only if you can answer these without opening every terminal:

**Which agents are working?

Which require me?

Which finished?

Which failed?

What task does each correspond to?

What workspace/branch does each own?**

And worktree lifecycle must be correct:

```
create → assign → work → inspect → integrate/discard → cleanup
```

with no stale worktrees or mistaken cross-session ownership.

That test will tell us far more than star counts.

## My current probability ranking

Given what I can verify today:

**Herdr — 35%** chance I'd ultimately choose it.

**Agent Orchestrator — 30%**.

**TUICommander — 22%**.

**CCManager — 8%**.

**Something else / custom combination — 5%.**

The important uncertainty is **native-Windows behavioral reliability**, not feature count.

Herdr is especially intriguing because its product model is so narrow and correct:

> 
**Don't manage agents. Manage your attention to agents.**

And AO is especially intriguing for the opposite reason: it could potentially absorb a surprisingly large portion of the orchestration/worktree/review infrastructure you've been building separately.

So my next research step would be **not another broad repo search**. I'd now go one level deeper into these three repositories—architecture, Windows implementation, PTY/session identity, status detection mechanism, worktree lifecycle, Grok integration, hooks/API, failure behavior, open Windows issues and actual extension points—and produce a **mechanism-by-mechanism decision matrix**.

That is where I expect the winner to become much clearer.
