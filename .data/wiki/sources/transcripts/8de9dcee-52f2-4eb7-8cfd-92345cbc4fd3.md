---
source_id: "8de9dcee-52f2-4eb7-8cfd-92345cbc4fd3"
title: "Ultracode: Claude Code Multi-Agent Orchestration Mode Explained - Developers Digest"
notebook_id: e83b6a68-fedc-4757-b492-3360ae8377a2
url: https://www.developersdigest.tech/blog/ultracode-effort-level-explained
type: web_page
exported: 2026-07-27
---

# Ultracode: Claude Code Multi-Agent Orchestration Mode Explained - Developers Digest
Ultracode: Claude Code Multi-Agent Orchestration Mode Explained - Developers Digest

Skip to main content

https://www.developersdigest.tech/blog/ultracode-effort-level-explained#main-content

Latest 

Watch: Grok 4.5 in 10 Minutes

https://www.developersdigest.tech/tutorials/69vVcsihxkg

Developers Digest DEVDIGEST

https://www.developersdigest.tech/

Watch

https://www.developersdigest.tech/tutorials

 

Read

https://www.developersdigest.tech/blog

 

Library

https://www.developersdigest.tech/library

 

Daily

https://www.developersdigest.tech/daily

 

⌘K

 

https://github.com/developersdigest

 

https://youtube.com/@developersdigest

Subscribe

https://www.developersdigest.tech/newsletter

 

Sign in

https://www.developersdigest.tech/sign-in

 

Get started

https://www.developersdigest.tech/sign-up

Watch

https://www.developersdigest.tech/tutorials

 

Sign in

https://www.developersdigest.tech/sign-in

Watch

https://www.developersdigest.tech/tutorials

 

Read

https://www.developersdigest.tech/blog

 

Library

https://www.developersdigest.tech/library

 

Daily

https://www.developersdigest.tech/daily

 Search 

Subscribe

https://www.developersdigest.tech/newsletter

 

YouTube

https://youtube.com/@developersdigest

 

GitHub

https://github.com/developersdigest

Get started

https://www.developersdigest.tech/sign-up

 

Sign in

https://www.developersdigest.tech/sign-in

Developers Digest DEVDIGEST

https://www.developersdigest.tech/

Watch

https://www.developersdigest.tech/tutorials

 

Read

https://www.developersdigest.tech/blog

 

Library

https://www.developersdigest.tech/library

 

Daily

https://www.developersdigest.tech/daily

 

⌘K

 

https://github.com/developersdigest

 

https://youtube.com/@developersdigest

Subscribe

https://www.developersdigest.tech/newsletter

 

Sign in

https://www.developersdigest.tech/sign-in

 

Get started

https://www.developersdigest.tech/sign-up

Watch

https://www.developersdigest.tech/tutorials

 

Sign in

https://www.developersdigest.tech/sign-in

Watch

https://www.developersdigest.tech/tutorials

 

Read

https://www.developersdigest.tech/blog

 

Library

https://www.developersdigest.tech/library

 

Daily

https://www.developersdigest.tech/daily

 Search 

Subscribe

https://www.developersdigest.tech/newsletter

 

YouTube

https://youtube.com/@developersdigest

 

GitHub

https://github.com/developersdigest

Get started

https://www.developersdigest.tech/sign-up

 

Sign in

https://www.developersdigest.tech/sign-in

Home

https://www.developersdigest.tech/

/ 

Blog

https://www.developersdigest.tech/blog

/ Ultracode: Claude Code Multi-Agent Orchestration Mode Explained

Ultracode: Claude Code Multi-Agent Orchestration Mode Explained

Developers Digest Developers Digest

https://www.developersdigest.tech/about

• June 11, 2026

• 8 min read

Claude Code

https://www.developersdigest.tech/tags/claude-code

 

AI Agents

https://www.developersdigest.tech/tags/ai-agents

 

Anthropic

https://www.developersdigest.tech/tags/anthropic

 

Developer Tools

https://www.developersdigest.tech/tags/developer-tools

 

TL;DR

Ultracode is two documented things: a prompt keyword that turns one task into a dynamic workflow, and an /effort setting that pairs xhigh reasoning with automatic orchestration. Here is exactly what the docs say.

In this article (14)

Last updated:

 June 11, 2026

If you typed the word "workflow" into 

Claude Code

https://www.developersdigest.tech/glossary#claude-code

 in late May and watched it spin up a background 

orchestration

https://www.developersdigest.tech/glossary#orchestration

 run, then tried the same thing this week and got nothing, you hit a deliberate rename. As of v2.1.160, the trigger keyword for dynamic workflows is 

ultracode

 , and the same name also appears in the 

/effort

 menu. Two different behaviors share one name, which is exactly why search results about it are confusing.

This post explains both, using only what the 

Claude Code changelog

https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

 and the official docs actually say, verified on June 11, 2026. For the full mechanics of workflow scripts themselves, see the 

dynamic workflows guide

https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide

. This post is about the ultracode entry points specifically.

What Ultracode Actually Is: Two Documented Behaviors

Dynamic workflows shipped in 

Claude Code

https://www.developersdigest.tech/tools/claude-code

 v2.1.154. A workflow is a JavaScript orchestration script that 

Claude

https://www.developersdigest.tech/tools/claude

 writes for your task and a runtime executes in the background, across what the 

announcement post

https://claude.com/blog/introducing-dynamic-workflows-in-claude-code

 describes as tens to hundreds of parallel subagents. Intermediate results live in script variables rather than in Claude's 

context window

https://www.developersdigest.tech/glossary#context-window

, which is what lets a run scale past what one conversation can coordinate.

Ultracode is how you reach that machinery. The 

workflows documentation

https://code.claude.com/docs/en/workflows

 describes two distinct entry points.

The prompt keyword: one task, one workflow

Include the literal keyword 

ultracode

 anywhere in a prompt and Claude writes a workflow script for that task instead of working through it turn by turn:

ultracode: audit every API endpoint under src/routes/ for missing auth checks


Copy

The keyword is highlighted in the prompt input - violet, per the v2.1.160 changelog - so you can see the trigger armed before you hit Enter. Three documented escape hatches exist if you typed it by accident:

Press 

Option+W

 on macOS or 

Alt+W

 on Windows and Linux to dismiss the highlight for that prompt

Press backspace while the 

cursor

https://www.developersdigest.tech/tools/cursor

 sits right after the highlighted keyword

Turn off "Ultracode keyword trigger" in 

/config

 to disable keyword detection entirely

Asking in your own words, for example "use a workflow for this", still works in every version; the docs treat a direct natural-language request as the same opt-in. The rename only retired the literal 

workflow

 keyword as a trigger: per the changelog, the word "workflow" no longer starts a run on its own.

The /effort setting: Claude decides per task

The second behavior is a session setting:

/effort ultracode


Copy

The 

model configuration docs

https://code.claude.com/docs/en/model-config

 define it precisely: "Ultracode is a Claude Code setting rather than a model effort level: it sends 

xhigh

 to the model and additionally has Claude orchestrate dynamic workflows for substantive tasks."

That sentence settles the most common misconception: the API never receives an effort value called ultracode. The model runs at 

xhigh

 , and Claude Code layers automatic orchestration on top. With the setting on, Claude plans a workflow for each substantive task without waiting for the keyword. The docs note that a single request can turn into several workflows in a row: one to understand the code, one to make the change, one to verify it.

Ultracode applies to the current session only and resets when you start a new one. It is deliberately excluded from every persistence mechanism: the docs state it is not part of the 

effortLevel

 setting, the 

--effort

 flag, or the 

CLAUDE_CODE_EFFORT_LEVEL

 environment variable. The two documented programmatic routes are 

--settings

 and an Agent SDK control request:

claude --settings '{"ultracode": true}'


Copy

That session-only design is a cost guardrail: multi-agent runs on every substantive task are expensive by construction, and the docs recommend dropping back with 

/effort high

 for routine work.

Newsletter

Get the weekly deep dive

Tutorials on Claude Code, AI agents, and dev tools, delivered free every week.

Subscribe

From the archive

[

12 Ways Developers Are Actually Leveraging Claude Fable 5

Jun 11, 2026 • 10 min read](https://www.developersdigest.tech/blog/ways-developers-are-leveraging-fable-5)

[

What a Fleet of Claude Agents Actually Costs (June 2026 Math)

Jun 11, 2026 • 10 min read](https://www.developersdigest.tech/blog/what-parallel-claude-agents-actually-cost)

[

The One-Cent Attack: Prompt Injection Through Bank Transfer Memos

Jun 10, 2026 • 8 min read](https://www.developersdigest.tech/blog/ai-agent-prompt-injection-banking)

[

The Pushback on Amodei's Exponential Essay: Too Slow, Too Convenient, or About Right?

Jun 10, 2026 • 9 min read](https://www.developersdigest.tech/blog/amodei-exponential-essay-pushback-roundup)

Ultracode vs Ultrathink vs xhigh

Three similar-sounding controls do three different jobs, all documented on the model configuration page:

 

Abstract systems illustration for Ultracode vs Ultrathink vs xhigh

Control

What it does

Scope

xhigh

Effort level sent to the model; deeper adaptive reasoning at higher 

token

https://www.developersdigest.tech/glossary#token

 spend

Persists across sessions

ultrathink

Prompt keyword that adds an in-context instruction for deeper reasoning on one turn; the effort level sent to the API is unchanged

Single turn

ultracode

Claude Code

https://www.developersdigest.tech/glossary#claude-code

 setting: sends 

xhigh

 to the model plus automatic workflow 

orchestration

https://www.developersdigest.tech/glossary#orchestration

 for substantive tasks

Current session only

A useful mental model: 

ultrathink

 makes one response think harder, 

xhigh

 makes every response think harder, and 

ultracode

 makes the harness work differently - it moves execution out of the conversation and into orchestrated background agents.

Model support follows the effort ladder. Per the model configuration docs, 

xhigh

 is available on 

Fable 5

https://www.developersdigest.tech/glossary#fable-5

, Opus 4.8, and Opus 4.7, but not on Opus 4.6 or Sonnet 4.6, where the ladder tops out at 

high

 and 

max

 . Ultracode is only offered on models that support 

xhigh

 ; on other models the 

/effort

 menu simply does not show it. That behavior was tightened in v2.1.160, whose changelog notes a fix for 

/effort ultracode

 "incorrectly blaming the dynamic workflows setting when the model cannot run xhigh." If you want the full ladder including where 

max

 fits and why the same level name maps to different underlying values per model, see 

Fable 5 effort levels explained

https://www.developersdigest.tech/blog/fable-5-effort-levels-explained

.

What Happens When a Workflow Triggers

Whichever entry point you use, the run behaves the same way, and the limits are documented:

Up to 16 concurrent agents, fewer on machines with limited CPU cores

1,000 agents total per run, which bounds the cost of a runaway script

No mid-run user input; only agent permission prompts can pause a run

The script itself has no filesystem or shell access; agents do the reading, writing, and command running

You watch and manage runs with 

/workflows

 : drill into phases and individual agents, see token totals per agent, pause and resume with 

p

 , stop with 

x

 , restart an agent with 

r

 , and save the run's script as a reusable command with 

s

 . Saved scripts land in 

.claude/workflows/

 for the project or 

~/.claude/workflows/

 for your user, and run as 

/<name>

 afterward. A saved workflow accepts structured input through an 

args

 global:

> Run /triage-issues on issues 1024, 1025, and 1030


Copy

Claude

https://www.developersdigest.tech/tools/claude

 passes the list as structured data, so the script can call array methods on 

args

 directly. This save-and-rerun loop is the practical payoff for repeated jobs: trigger a run once with the keyword, confirm it does what you want, press 

s

 , and the orchestration becomes a versionable artifact your whole team can run. For how workflows compare against subagents and agent teams as coordination primitives, see the 

subagents vs agent teams vs workflows breakdown

https://www.developersdigest.tech/blog/claude-code-subagents-vs-agent-teams-vs-workflows

.

Separately from workflows, v2.1.172 allows 

sub-agents

https://www.developersdigest.tech/glossary#sub-agents

 to spawn their own sub-agents up to 5 levels deep - worth knowing when you reason about how much parallel machinery a single prompt can now mobilize.

Permissions and Cost: Check Before a Long Run

Two operational details from the workflows docs matter before you leave an ultracode session running.

 

Abstract systems illustration for Permissions and Cost: Check Before a Long Run

First, permissions. Workflow subagents always run in 

acceptEdits

 mode and inherit your tool allowlist regardless of your session's permission mode. File edits are auto-approved. Shell commands, web fetches, and MCP tools outside your allowlist can still prompt you mid-run, so the docs recommend adding the commands agents will need to your allowlist before starting a long run. Note also that in auto mode the launch approval prompt is skipped entirely when ultracode is on - convenient, but it removes the last launch checkpoint, leaving only non-allowlisted tool calls to pause a run.

Second, cost. Runs count toward your plan's usage and rate limits like any other session, and every agent uses your session's model unless the script routes a stage to a different one. The docs' advice is to gauge spend on a small slice first: one directory instead of the whole repo. With 

/effort ultracode

 active this compounds, because every substantive task in the session pays the orchestration premium. If you are running multiple sessions of this kind, the operational patterns in 

managing a fleet of Claude agents

https://www.developersdigest.tech/blog/managing-a-fleet-of-claude-agents

 apply directly, and the 

orchestrator model playbook

https://www.developersdigest.tech/blog/fable-5-orchestrator-model-playbook

 covers routing cheap stages to cheap models.

Turning It Off, and Version Requirements

Requirements, all from the workflows docs: 

Claude Code

https://www.developersdigest.tech/tools/claude-code

 v2.1.154 or later, on any paid plan, the Anthropic API, Bedrock, Vertex AI, or Microsoft Foundry. Pro users enable workflows from the Dynamic workflows row in 

/config

 . The keyword has been spelled 

ultracode

 since v2.1.160.

Three documented ways to disable workflows for yourself:

// ~/.claude/settings.json
{ "disableWorkflows": true }


Copy

Or toggle Dynamic workflows off in 

/config

 , or set 

CLAUDE_CODE_DISABLE_WORKFLOWS=1

 in your environment. When workflows are disabled, the 

ultracode

 keyword stops triggering and ultracode disappears from the 

/effort

 menu. Organizations can set 

disableWorkflows

 in managed settings. If you only dislike the keyword but want workflows available on request, the narrower "Ultracode keyword trigger" toggle in 

/config

 is the right knob.

One honest caveat to close on: most tasks do not need a workflow. The docs position them for jobs that need more agents than one conversation can coordinate - codebase-wide audits, large migrations, cross-checked research. For everything else, 

/effort high

 and a normal conversation remain the cheaper, faster, easier-to-review path.

FAQ

What does ultracode do in Claude Code?

Two things, depending on where you use it. As a keyword in a prompt, it runs that single task as a dynamic workflow - a background orchestration script coordinating up to 16 concurrent subagents - without changing your session settings. As 

/effort ultracode

 , it sets reasoning effort to 

xhigh

 and has Claude automatically plan workflows for every substantive task in the session.

Is ultracode an effort level like xhigh or max?

No. The model configuration docs state it is "a Claude Code setting rather than a model effort level." The model itself runs at 

xhigh

 ; the ultracode part is harness behavior, which is why it cannot be set through 

effortLevel

 , 

--effort

 , or 

CLAUDE_CODE_EFFORT_LEVEL

 , and why it resets when the session ends.

What is the difference between ultracode and ultrathink?

ultrathink

 is a prompt keyword that requests deeper reasoning on one turn by adding an in-context instruction; the effort level sent to the API does not change and no extra agents run. 

ultracode

 triggers multi-agent workflow orchestration. They solve different problems: ultrathink for one hard question, ultracode for one large task.

Which models support ultracode?

Models that support the 

xhigh

 effort level: Fable 5, Opus 4.8, and Opus 4.7 per the current model configuration docs. On Opus 4.6 and Sonnet 4.6 the 

/effort

 menu does not offer ultracode. Since v2.1.160, Claude Code hides the option rather than erroring when the model cannot run 

xhigh

 .

How do I stop the ultracode keyword from triggering workflows?

Per prompt: press 

Option+W

 (macOS) or 

Alt+W

 (Windows/Linux), or backspace immediately after the highlighted keyword. Permanently: turn off "Ultracode keyword trigger" in 

/config

 . To disable workflows entirely, set 

"disableWorkflows": true

 in settings or 

CLAUDE_CODE_DISABLE_WORKFLOWS=1

 in your environment.

Sources

Claude Code CHANGELOG.md

https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

 - v2.1.154 (dynamic workflows introduction), v2.1.160 (keyword rename, ultracode fix), v2.1.172 (nested sub-agents). Accessed June 11, 2026.

Orchestrate subagents at scale with dynamic workflows - Claude Code docs

https://code.claude.com/docs/en/workflows

 - keyword and 

/effort ultracode

 behavior, limits, permissions, 

/workflows

 controls, disable settings. Accessed June 11, 2026.

Model configuration - Claude Code docs

https://code.claude.com/docs/en/model-config

 - effort level ladder per model, ultracode definition, ultrathink keyword, session-only behavior. Accessed June 11, 2026.

Introducing dynamic workflows in Claude Code - Claude blog

https://claude.com/blog/introducing-dynamic-workflows-in-claude-code

 - announcement framing, use cases, availability. Accessed June 11, 2026.

Read next

[

Claude Code Dynamic Workflows: The Complete Guide

Claude Code dynamic workflows turn orchestration into a JavaScript script that runs up to 1,000 agents per run - here is how scripts, schemas, budgets, and resume actually work. 10 min read](https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide)

[

Claude Code Auto Mode Explained: Permissions Without the Prompts

Auto mode replaces permission prompts with a background safety classifier - here is how the Shift+Tab cycle, hard_deny rules, and glob deny patterns actually fit together. 8 min read](https://www.developersdigest.tech/blog/claude-code-auto-mode-explained)

[

Claude Agents vs Skills: Which One Do You Actually Need?

Claude agents vs skills, untangled: agents are workers with their own context window, skills are instructions loaded on demand. Here is the decision table. 8 min read](https://www.developersdigest.tech/blog/claude-agents-vs-skills)

Share Twitter/X LinkedIn Reddit Hacker News Email Copy Cite

Suggest an edit

https://github.com/developersdigest/developers-digest-site/edit/main/content/blog/ultracode-effort-level-explained.md

 Save

Discuss this article on Twitter/X

https://twitter.com/intent/tweet?text=Thoughts%20on%20%22Ultracode%3A%20Claude%20Code%20Multi-Agent%20Orchestration%20Mode%20Explained%22%20by%20%40devdigest&url=https%3A%2F%2Fwww.developersdigest.tech%2Fblog%2Fultracode-effort-level-explained

Developers Digest

https://www.developersdigest.tech/about

Technical content at the intersection of AI and development. Building with AI agents, Claude Code, and modern dev tools - then showing you exactly how it works.

300+ videos 30K+ GitHub stars 50+ articles

Subscribe

https://www.developersdigest.tech/newsletter

 

YouTube

https://youtube.com/@developersdigest

 

GitHub

https://github.com/developersdigest

 

Twitter/X

https://x.com/devdigest

Comments

Sign in to join the conversation

Sign In to Comment

On this page

What Ultracode Actually Is: Two Documented Behaviors The prompt keyword: one task, one workflow The /effort setting: Claude decides per task Ultracode vs Ultrathink vs xhigh What Happens When a Workflow Triggers Permissions and Cost: Check Before a Long Run Turning It Off, and Version Requirements FAQ What does ultracode do in Claude Code? Is ultracode an effort level like xhigh or max? What is the difference between ultracode and ultrathink? Which models support ultracode? How do I stop the ultracode keyword from triggering workflows? Sources

Weekly deep dives

One email, tutorials + open-source. Free.

Subscribe

Read next

[

Claude Code Dynamic Workflows: The Complete Guide

10 min read](https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide)

[

Claude Code Auto Mode Explained: Permissions Without the Prompts

8 min read](https://www.developersdigest.tech/blog/claude-code-auto-mode-explained)

[

Claude Agents vs Skills: Which One Do You Actually Need?

8 min read](https://www.developersdigest.tech/blog/claude-agents-vs-skills)

[

Claude Code Agent Teams, Subagents, and MCP: The 2026 Playbook

9 min read](https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026)

Previous 12 Ways Developers Are Actually Leveraging Claude Fable 5

https://www.developersdigest.tech/blog/ways-developers-are-leveraging-fable-5

 

Next Rewriting Your Prompts and Skills for Fable 5

https://www.developersdigest.tech/blog/rewriting-prompts-and-skills-for-fable-5

Related Tools

[AI Models C

Claude Opus 4.7

Anthropic's flagship reasoning model. Best-in-class for coding, long-context analysis, and agentic workflows. 1M token c... View Tool](https://www.developersdigest.tech/tools/claude-opus-4-7)

[AI Coding Daily Driver

Claude Code

Anthropic's agentic coding CLI. Runs in your terminal, edits files autonomously, spawns sub-agents, and maintains memory... View Tool](https://www.developersdigest.tech/tools/claude-code)

[AI Coding C

Conductor

Mac app for running parallel Claude Code, Codex, and Cursor agents in isolated workspaces. Watch every agent work at onc... View Tool](https://www.developersdigest.tech/tools/conductor)

[Productivity New A

AgentCanvas

A hosted infinite canvas your headless AI agents drive over MCP. Any MCP-speaking agent - Claude Code, Codex, Cursor, or... View Tool](https://www.developersdigest.tech/tools/agentcanvas)

Apps from Developers Digest

[Developer Tools

Agent Hub

Every coding agent in one window. Stop alt-tabbing between Claude, Codex, and Cursor. View App](https://www.developersdigest.tech/apps/agent-hub)

[Developer Tools In Progress

Skill Builder

Turn a one-liner into a working Claude Code skill. From idea to installed in a minute. View App](https://www.developersdigest.tech/apps/skill-builder)

[Developer Tools Plus $20/mo

Skills Pro

Unlock pro skills and share private collections with your team. View App](https://www.developersdigest.tech/apps/dd-skills-marketplace)

Related Guides

[Guide

Interactive Mode - Claude Code

Real-time prompt loop with history, completions, and multiline input. Claude Code](https://www.developersdigest.tech/guides/interactive-mode)

[Guide

Vim Editor Mode - Claude Code

Full vim keybindings (normal and insert modes) for prompt editing. Claude Code](https://www.developersdigest.tech/guides/vim-editor-mode)

[Guide

Bash Mode - Claude Code

Prefix prompts with ! to run shell commands directly, bypassing Claude. Claude Code](https://www.developersdigest.tech/guides/bash-mode)

Related Videos

[

Anthropic's Cowork: Claude Code for the Rest of Your Work

In this video, we dive into Anthropic's newly launched Cowork, a user-friendly extension of Claude Code designed to streamline work for both developers and non-developers. This discussion includes an Video · January 13, 2026](https://www.developersdigest.tech/tutorials/SpqqWaDZ3ys)

[

Claude Code 'Interview' Mode in 6 Minutes

Effortless Project Planning: Mastering Spec-Driven Development with Claude Code Kick off the new year with a fresh approach to project planning using Claude Code! In this video, learn how to achieve Video · January 1, 2026](https://www.developersdigest.tech/tutorials/vgHBEju4kGE)

[

Anthropic Sonnet 4.5 in Claude Code in 10 Minutes

To learn for free on Brilliant, go to https://brilliant.org/DevelopersDigest/ . You'll also get 20% off an annual premium subscription TOOLS I USE → Wispr Flow (voice-to-text): https://dub.sh/... Video · October 3, 2025](https://www.developersdigest.tech/tutorials/U9bjOBOU7Nc)

Related Posts

[

 8 min read Claude Code

Claude Agents vs Skills: Which One Do You Actually Need?

Claude agents vs skills, untangled: agents are workers with their own context window, skills are instructions loaded on... June 11, 2026](https://www.developersdigest.tech/blog/claude-agents-vs-skills)

[

 10 min read Claude Code

Claude Code Dynamic Workflows: The Complete Guide

Claude Code dynamic workflows turn orchestration into a JavaScript script that runs up to 1,000 agents per run - here is... June 11, 2026](https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide)

[

 10 min read MCP

MCP Servers vs Agent Skills: Which to Build in 2026

A decision framework for 2026: MCP servers give an agent access to a live system, Agent Skills teach it how to do a task... July 2, 2026](https://www.developersdigest.tech/blog/mcp-servers-vs-agent-skills-2026)

[

 8 min read AI Agents

Agent Workspaces Need Filesystem Contracts

GitHub's latest agent workspace trend points at a boring but important primitive: agents need explicit filesystem contra... June 13, 2026](https://www.developersdigest.tech/blog/agent-workspaces-need-filesystem-contracts)

[

 8 min read Claude Code

Claude Code Auto Mode Explained: Permissions Without the Prompts

Auto mode replaces permission prompts with a background safety classifier - here is how the Shift+Tab cycle, hard_deny r... June 11, 2026](https://www.developersdigest.tech/blog/claude-code-auto-mode-explained)

[

 8 min read Anthropic

Setting Up the Memory Tool with Fable 5: Persistent Agents That Learn

Anthropic says persistent file-based memory improved Fable 5 three times more than it improved Opus 4.8. Here is the ful... June 11, 2026](https://www.developersdigest.tech/blog/fable-5-memory-tool-setup)

Build with the member tools

Chat, image and voice generation, memory, and more run on one universal credit balance across every Developers Digest app. Sign up free and get 25 credits, no card required.

Start free

https://www.developersdigest.tech/sign-up

 

See pricing

https://www.developersdigest.tech/pricing

Subscribe

 

Get Smarter About AI Dev

New tutorials, open-source projects, and deep dives on coding agents - delivered weekly.

One email per week Real code, not theory Free forever

Subscribe Free

Platform

App Builder

https://www.developersdigest.tech/dashboard/app-builder-v2

 New

Chat

https://www.developersdigest.tech/dashboard/chat

AgentCanvas

https://www.developersdigest.tech/canvas

 New

Multi-Media Studio

https://www.developersdigest.tech/dashboard/tools

Skill Studio

https://www.developersdigest.tech/dashboard/skills-studio

Library

https://www.developersdigest.tech/dashboard/library

Agents

MCP

https://www.developersdigest.tech/dashboard/mcp

CLI

https://www.developersdigest.tech/dashboard/cli

AI Gateway

https://www.developersdigest.tech/dashboard/ai-gateway

API Keys

https://www.developersdigest.tech/dashboard/keys

Content

Blog

https://www.developersdigest.tech/blog

Tutorials

https://www.developersdigest.tech/tutorials

Guides

https://www.developersdigest.tech/guides

Courses

https://www.developersdigest.tech/courses

News

https://www.developersdigest.tech/news

Research Papers

https://www.developersdigest.tech/papers

 New

Tools

Tools Directory

https://www.developersdigest.tech/tools

Toolkit

https://www.developersdigest.tech/toolkit

Skills

https://www.developersdigest.tech/skills

Resources

https://www.developersdigest.tech/resources

Projects

https://www.developersdigest.tech/projects

Company

About

https://www.developersdigest.tech/about

Connect

https://www.developersdigest.tech/connect

Newsletter

https://www.developersdigest.tech/newsletter

Pricing

https://www.developersdigest.tech/pricing

Changelog

https://www.developersdigest.tech/dashboard/whats-new

Legal

Privacy Policy

https://www.developersdigest.tech/privacy

Terms of Service

https://www.developersdigest.tech/terms

Contact

https://www.developersdigest.tech/contact

Social

YouTube

https://youtube.com/@developersdigest

X

https://x.com/devdigest

GitHub

https://github.com/developersdigest

Newsletter

Weekly AI dev insights. Free.

Subscribe

 

© 2026 DEVELOPERS DIGEST

Videos and open-source projects at the intersection of AI and development

DEVDIGEST

x

Before you go

One email per week. Tutorials, open-source projects, and deep dives. Free.

Subscribe
