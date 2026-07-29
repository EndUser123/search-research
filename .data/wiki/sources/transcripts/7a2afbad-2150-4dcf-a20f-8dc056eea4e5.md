---
source_id: "7a2afbad-2150-4dcf-a20f-8dc056eea4e5"
title: "CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant"
notebook_id: 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
url: https://www.deployhq.com/blog/ai-coding-config-files-guide
type: web_page
exported: 2026-07-28
---

# CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant
CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant

Skip to main content

https://www.deployhq.com/blog/ai-coding-config-files-guide#main-content

 

Skip to navigation

https://www.deployhq.com/blog/ai-coding-config-files-guide#main-navigation

Ready to streamline your deployments? 

Start deploying with confidence today.

Get Started

https://www.deployhq.com/signup?cta=Blog+Sticky+Banner

Header

Primary Navigation

DeployHQDeployHQ

https://www.deployhq.com/

Features

https://www.deployhq.com/features

 DEPLOYMENTS

Zero Downtime Deployments Deploy without interruption

https://www.deployhq.com/features/zero-downtime-deployments

Turbo Deployments Lightning fast deploys

https://www.deployhq.com/features/turbo-deployments

Docker Builds Container-based builds

https://www.deployhq.com/features/docker-builds

Automatic Deployment Deploy on every push

https://www.deployhq.com/features/automatic-deployments

Deploy Behind Firewalls Secure private deployments

https://www.deployhq.com/features/deploy-behind-firewalls

SSH Deployment Deploy to any SSH server

https://www.deployhq.com/features/ssh-deployment

Scheduled Deployments Ship at off-peak times

https://www.deployhq.com/features/scheduled-deployments

Deployment Availability Block deploys during freezes

https://www.deployhq.com/features/deployment-availability

 FEATURES

One-Click Rollback Instant rollback capability

https://www.deployhq.com/features/one-click-rollback

Build Pipelines Custom build workflows

https://www.deployhq.com/features/build-pipelines

Build Cache Cut build times by 90%

https://www.deployhq.com/features/build-cache

Deployment Checks Gate deploys with checks

https://www.deployhq.com/features/deployment-checks

Deployment Targets Multi-environment deploys

https://www.deployhq.com/features/deployment-targets

Deployment Templates Reusable configurations

https://www.deployhq.com/features/deployment-templates

Deployment Zones Geographic distribution

https://www.deployhq.com/features/deployment-zones

Team & Permissions Role-based access

https://www.deployhq.com/features/team-permissions

Single Sign-On SAML for any IdP

https://www.deployhq.com/features/sso

 INTEGRATIONS

Deploy from GitHub GitHub integration

https://www.deployhq.com/deploy-from-github

Deploy from GitLab GitLab integration

https://www.deployhq.com/deploy-from-gitlab

Deploy from Bitbucket Bitbucket integration

https://www.deployhq.com/deploy-from-bitbucket

Deploy to VPS Any virtual private server

https://www.deployhq.com/vps

Deploy WordPress WordPress deployments

https://www.deployhq.com/wordpress

Deploy to Shopify Shopify deployments

https://www.deployhq.com/shopify

Game Servers Deploy to game servers

https://www.deployhq.com/deploy-to-game-servers

 DEVELOPER TOOLS

REST API Full API access

https://www.deployhq.com/features/api

DeployHQ AI AI-powered assistance

https://www.deployhq.com/features/ai

MCP Server Model Context Protocol

https://www.deployhq.com/features/deployhq-mcp

PR Radar Pull request dashboard

https://www.deployhq.com/features/pr-radar

CLI & Agents Deploy from the terminal

https://www.deployhq.com/agents

AI PageSpeed Performance insights

https://pagespeed.deployhq.com/

Powerful Integrations Connect your tools

https://www.deployhq.com/features/integrations

Hosting

https://www.deployhq.com/hosting

Hosting overview All hosting options at a glance

https://www.deployhq.com/hosting

Managed VPS Hosting Fully-managed Linux VPS with CI/CD

https://www.deployhq.com/hosting/managed-vps

Static Hosting Cloudflare edge, atomic deploys

https://www.deployhq.com/hosting/static

Bring Your Own Server Deploy to any VPS, SSH, FTP or S3

https://www.deployhq.com/vps

Pricing

https://www.deployhq.com/pricing

Testimonials

https://www.deployhq.com/customers

Blog

https://www.deployhq.com/blog

Help

https://www.deployhq.com/support

Ask AI Instant AI-powered answers

https://www.deployhq.com/support#ask-ai

Support Centre Browse help articles

https://www.deployhq.com/support

Learn Git Git tutorials & guides

https://www.deployhq.com/git

Deployment Guides Step-by-step instructions

https://www.deployhq.com/guides

Cheatsheets Quick-reference docs

https://www.deployhq.com/cheatsheets

Changelog & Updates Latest product updates

https://changelog.deployhq.com/changelog

Service Status System health & uptime

https://status.deployhq.com/

Contact Us Get in touch with us

https://www.deployhq.com/contact

Login

https://identity.deployhq.com/login/deploy

Start deploying free →

https://www.deployhq.com/signup?cta=Start+deploying+free+%E2%86%92

Toggle Menu Close Menu

CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant

By Alex M

· Updated on 12th June 2026

AI

https://www.deployhq.com/blog/category/ai

 and 

Tips & Tricks

https://www.deployhq.com/blog/category/tips

 

Every AI coding tool now reads a configuration file from your project. 

Claude Code

https://www.deployhq.com/blog/getting-started-with-claude-code-the-ai-coding-assistant-for-your-terminal

 looks for 

CLAUDE.md

 . 

Codex CLI

https://www.deployhq.com/blog/getting-started-with-openai-codex-cli-ai-powered-code-generation-from-your-terminal

 reads 

AGENTS.md

 . 

Gemini CLI

https://www.deployhq.com/blog/getting-started-with-google-gemini-cli-open-source-ai-agent-for-your-terminal

 checks for 

GEMINI.md

 . 

Cursor

https://www.deployhq.com/guides/cursor

 has 

.cursorrules

 . GitHub Copilot uses 

copilot-instructions.md

 . 

Windsurf

https://www.deployhq.com/guides/windsurf

 has 

.windsurfrules

 .

These files solve a fundamental problem: AI models have no persistent memory. Every session starts blank. Without a configuration file, you'd repeat the same instructions every time — your tech stack, coding conventions, project structure, deployment rules. These files give your AI assistant the context it needs to produce useful code from the first prompt.

This guide covers every major format — 

CLAUDE.md

 , 

AGENTS.md

 , 

GEMINI.md

 , 

copilot-instructions.md

 , Cursor rules, and Windsurf rules — explains how each discovery process works, and shows you how to write effective instructions that actually improve your AI's output.

The Complete Landscape

Here's every AI configuration file format in use today:

File

Tool

Location

Format

CLAUDE.md

Claude Code

Project root + 

~/.claude/

Markdown

AGENTS.md

Codex CLI, Cursor, Claude Code (fallback)

Project root + subdirectories

Markdown

AGENTS.override.md

Codex CLI (local-only overrides)

Same directory as 

AGENTS.md

Markdown

GEMINI.md

Gemini CLI

Project root + 

~/.gemini/

Markdown

.cursorrules

Cursor (legacy)

Project root

Plain text

.cursor/rules/*.mdc

Cursor (current)

.cursor/rules/

 directory

MDC (Markdown+)

.github/copilot-instructions.md

GitHub Copilot

.github/

 directory

Markdown

.github/instructions/*.instructions.md

GitHub Copilot (scoped)

.github/instructions/

Markdown + frontmatter

.windsurfrules

Windsurf (legacy)

Project root

Plain text

.windsurf/rules/*.md

Windsurf (current)

.windsurf/rules/

 directory

Markdown

Every tool has converged on the same core idea: a markdown file in your repository that the AI reads before doing anything. The differences are in naming, discovery order, and how each handles hierarchy.

How Each Format Works

CLAUDE.md — Claude Code

Claude Code reads 

CLAUDE.md

 files from three locations, merged in order:

~/.claude/CLAUDE.md

 — Your personal global instructions file (the claude md global file that applies to every project on your machine)

./CLAUDE.md

 — Project root instructions (shared with your team via git)

Subdirectory CLAUDE.md files

 — Scoped instructions for specific parts of the codebase

Claude Code also reads 

AGENTS.md

 as a fallback if no 

CLAUDE.md

 is found in a directory. This means if your team uses multiple AI tools, you can maintain a single 

AGENTS.md

 and it will work with Claude Code automatically.

You can also place a 

CLAUDE.md

 inside 

.claude/

 at the project root for settings you want separated from the canonical top-level file — Claude Code will load 

.claude/CLAUDE.md

 alongside the root one.

For a single-page reference to Claude Code's slash commands, hooks, and MCP setup that complement these config files, see our 

Claude Code cheatsheet

https://www.deployhq.com/cheatsheets/claude-code

.

A key constraint: research suggests frontier LLMs can reliably follow around 150-200 instructions. Claude Code's system prompt already uses about 50 of those, so keep your 

CLAUDE.md

 concise — ideally under 300 lines.

AGENTS.md — The Cross-Tool Standard

AGENTS.md

 is the closest thing to a universal standard. Originally popularised by OpenAI's Codex CLI, it's now an 

open format stewarded by the Linux Foundation

https://agents.md/

 with adoption across 60,000+ open-source projects. It's supported by:

Codex CLI

 (primary config file)

Cursor

 (reads alongside 

.cursorrules

 )

Claude Code

 (fallback when no 

CLAUDE.md

 exists)

Continue.dev

, 

Aider

, 

OpenHands

Codex CLI discovery: AGENTS.md, AGENTS.override.md, and config.toml

Codex CLI has the most sophisticated discovery process of any coding agent. It walks from your project root down to the current working directory, checking each level for 

AGENTS.md

 . Alongside each 

AGENTS.md

 , it will also load an 

AGENTS.override.md

 file if one exists — that's the mechanism for local-only overrides you don't want committed to git (personal tweaks, machine-specific paths, experiment flags).

You can configure discovery behaviour in 

~/.codex/config.toml

 :

# Fallback filenames Codex will try if AGENTS.md is missing in a directory
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]

# Hard cap on how many bytes of doc content Codex will load per file
project_doc_max_bytes = 65536


project_doc_fallback_filenames

 tells Codex which alternative filenames to look for when there's no 

AGENTS.md

 in a directory. Useful when your team already has an established doc filename and you don't want to rename everything.

project_doc_max_bytes

 controls the per-file size limit (default: 32 KiB on older versions, 64 KiB on current). Anything past the cap is silently truncated, which is why a sprawling 500-line instruction file often stops working on recent Codex releases.

The practical rule: 

AGENTS.md

 is committed and shared, 

AGENTS.override.md

 is gitignored and personal, and the config knobs let you adapt without renaming files.

GEMINI.md — Gemini CLI

Gemini CLI uses 

GEMINI.md

 with a hierarchical discovery system similar to Codex:

~/.gemini/GEMINI.md

 — Global defaults for all projects

Workspace root GEMINI.md

 — Project-level instructions

Subdirectory GEMINI.md files

 — Discovered dynamically when tools access files in those directories

A unique feature: you can inspect the loaded context at any time with the 

/memory show

 command, and force a reload with 

/memory refresh

 . The filename itself is configurable via 

settings.json

 if you prefer a different name.

.cursorrules / .cursor/rules/ — Cursor

Cursor has evolved through two formats:

Legacy

: A single 

.cursorrules

 file in the project root. Still supported but deprecated.

Current (recommended)

: A 

.cursor/rules/

 directory containing multiple 

.mdc

 files, each with its own scope:

Always On

 — Applied to every interaction

Auto Attached

 — Activated when matching files are open

Model Decision

 — The AI decides whether to apply based on a description

Manual

 — Only when explicitly mentioned via 

@

This is the most granular system — you can have 

frontend.mdc

 for React conventions and 

backend.mdc

 for API patterns, each activated only when relevant. Create rules quickly with the 

/rules

 slash command in Cursor's terminal.

copilot-instructions.md — GitHub Copilot

GitHub Copilot reads from 

.github/copilot-instructions.md

 for project-wide instructions. Since July 2025, it also supports scoped instructions via 

.github/instructions/*.instructions.md

 files with glob-pattern frontmatter:

---
applyTo: "**/*.tsx"
---
Use functional components with TypeScript interfaces.
Always use server components unless client interactivity is required.


This lets you define different rules for different file types — TypeScript vs Python, frontend vs backend — without cluttering a single file.

.windsurfrules / .windsurf/rules/ — Windsurf

Windsurf follows the same legacy-to-directory evolution as Cursor:

Legacy

: 

.windsurfrules

 in the project root

Current

: 

.windsurf/rules/

 directory with individual rule files

Rules can be 

Always On

, 

Manual

 (via @mention), or 

Model Decision

. Note the character limits: individual rule files are capped at 6,000 characters, and total combined rules must not exceed 12,000 characters.

CLAUDE.md vs AGENTS.md vs copilot-instructions.md

The three files that most teams end up choosing between are 

CLAUDE.md

 , 

AGENTS.md

 , and 

copilot-instructions.md

 . They overlap in purpose but differ in reach and mechanics:

Question

CLAUDE.md

AGENTS.md

copilot-instructions.md

Which tools read it?

Claude Code (primary), plus any tool that falls back to it

Codex CLI, Cursor, Claude Code (fallback), Continue.dev, Aider, OpenHands

GitHub Copilot (Chat, CLI, code completion)

Location

Project root, 

~/.claude/

 , any subdirectory

Project root and walked downward; 

AGENTS.override.md

 for local-only

.github/copilot-instructions.md

 ; scoped files under 

.github/instructions/

Hierarchy

Global → project → subdirectory

Root → subdirectory (nearer wins)

Single project file + glob-scoped files

Size limit

~300 lines recommended (soft)

project_doc_max_bytes

 (default 64 KiB)

No hard cap, but brevity still wins

Gitignored override?

Not built in

Yes, via 

AGENTS.override.md

Not built in

CLAUDE.md or AGENTS.md?

 If your team uses Claude Code alongside any other agent, start with 

AGENTS.md

 and let Claude Code fall back to it. Only add a 

CLAUDE.md

 when you have Claude-specific instructions that shouldn't leak to Codex or Cursor sessions — things like use the Serena MCP server for symbol navigation or prefer 

Task

 tool over bash for searches.

CLAUDE.md vs copilot-instructions.md?

 They don't compete. If you use both tools, write 

AGENTS.md

 for Claude Code and 

copilot-instructions.md

 for Copilot, and keep the two narrowly focused on what each tool actually needs. Copilot's glob-scoped 

.github/instructions/*.instructions.md

 files are unique and worth using for frontend-vs-backend rule splits.

The copilot equivalent of CLAUDE.md

 is 

.github/copilot-instructions.md

 — same idea (persistent project-wide instructions), different filename and location.

Which One Should You Use?

If your team uses a single AI tool, use that tool's native format. But most teams now use multiple tools — Cursor in the IDE, Claude Code in the terminal, Copilot for quick completions. Here's a practical approach:

your-project/
├── AGENTS.md              ← Universal instructions (works with Codex, Cursor, Claude Code)
├── AGENTS.override.md     ← Local-only overrides (gitignored)
├── CLAUDE.md              ← Claude-specific additions (if needed)
├── .github/
│   └── copilot-instructions.md  ← Copilot-specific (if your team uses it)
├── .cursor/
│   └── rules/             ← Cursor-specific scoped rules (if needed)
└── ...


Start with AGENTS.md

 as your single source of truth. It has the widest cross-tool support. Then add tool-specific files only when you need features that 

AGENTS.md

 can't provide (like Cursor's scoped activation or Copilot's glob patterns).

For Claude Code users: you can make your 

CLAUDE.md

 simply reference the shared instructions:

Strictly follow the rules in ./AGENTS.md


If you're still evaluating which CLI to standardise on, our 

Claude Code vs Codex CLI vs Gemini CLI comparison

https://www.deployhq.com/blog/comparing-claude-code-openai-codex-and-google-gemini-cli-which-ai-coding-assistant-is-right-for-your-deployment-workflow

 walks through the tradeoffs in more depth.

Writing Effective Instructions

The most common mistake is treating these files like comprehensive documentation. They're not — they're concise instructions that fit within a model's attention window. Here's what works.

What to Include

Build and test commands

 — The single most valuable thing you can provide:

## Commands
- Build: `npm run build`
- Test single file: `npm test -- path/to/test.ts`
- Lint: `npm run lint`
- Type check: `npx tsc --noEmit`


Tech stack and versions

 — Prevents the AI from guessing wrong:

## Stack
- Framework: Next.js 15 (App Router)
- Language: TypeScript 5.7 (strict mode)
- Styling: Tailwind CSS 4.0
- Database: PostgreSQL 16 with Drizzle ORM
- Deployment: DeployHQ → Ubuntu 22.04 VPS


Project structure

 — Especially important for monorepos:

## Structure
- `apps/web/` — Next.js frontend
- `apps/api/` — Express API server
- `packages/shared/` — Shared types and utilities
- `infra/` — Terraform configuration


Critical conventions

 — Things the AI would otherwise get wrong:

## Conventions
- Use named exports, not default exports
- API routes return { data, error } shape
- Database migrations go in `drizzle/migrations/`
- Environment variables are validated in `src/env.ts`


For a deeper treatment of what belongs in each section, see our guide on 

developer CLIs that AI coding agents use well

https://www.deployhq.com/blog/6-developer-clis-ai-coding-agents-use-well

 — the CLI inventory it covers is exactly what goes in the Commands block.

What to Leave Out

Code style rules

 — Use ESLint, Prettier, and formatters instead. They're faster, deterministic, and don't consume your instruction budget.

Obvious things

 — Write clean code and follow best practices waste tokens. Be specific or don't include it.

Full API documentation

 — Link to it instead. Use a 

docs/

 or 

agent_docs/

 directory for supplementary context that the AI can pull in when needed. If you publish docs on the web, our guide on 

serving markdown to AI coding assistants with llms.txt and content negotiation

https://www.deployhq.com/blog/making-your-documentation-ai-friendly-serving-markdown-to-ai-coding-assistants

 covers how to make those external docs first-class context for Claude, Cursor, and Copilot.

Task-specific instructions

 — These belong in your prompt, not in a persistent config file.

Once your AGENTS.md is dialed in, the next loop to close is what happens after the AI commits. If you spend your day in the terminal anyway, you can 

deploy from your terminal

https://www.deployhq.com/agents

 too — the 

DeployHQ

https://www.deployhq.com/

 CLI ships code straight from your shell or from inside Claude Code, Codex CLI, and Cursor. Same agent that wrote the code can deploy it.

A Deployment-Focused Example

Here's a complete 

AGENTS.md

 for a PHP team using 

automatic deployments from Git

https://www.deployhq.com/features/automatic-deployments

:

## Project: Acme Web App

Laravel 11 application deployed via DeployHQ to Ubuntu 22.04 VPS.
Production: Nginx + PHP-FPM 8.3. Database: MySQL 8.

## Commands
- Run tests: `php artisan test --filter=TestName`
- Run all tests: `php artisan test`
- Lint: `./vendor/bin/pint`
- Static analysis: `./vendor/bin/phpstan analyse`
- DB migrate: `php artisan migrate`

## Deployment Rules
- Never modify production configs directly
- All database migrations must be reversible
- Run migrations before deploying code that depends on schema changes
- Include rollback steps in PR descriptions for risky changes
- Feature flags for anything touching payments or auth
- Run `composer install --no-dev` in production builds

## Structure
- `app/Services/` — Business logic (not in controllers)
- `app/Jobs/` — Background jobs (Laravel Queue)
- `app/Actions/` — Single-purpose action classes
- `deploy/` — DeployHQ build commands
- `tests/` — PHPUnit tests (mirror app/ structure)

## Conventions
- Action classes: single `handle()` method
- API responses: always use `JsonResource` classes
- Logging: use `Log::info()`, never `dd()` or `dump()`
- Secrets: use `config()` helper, never `env()` outside config files
- Validation: FormRequest classes, never inline in controllers


If you're already thinking about wiring these agents into CI, our walkthrough on 

running AI coding agents in CI/CD headless mode

https://www.deployhq.com/blog/running-ai-coding-agents-cicd-headless-mode-claude-code-codex-gemini

 shows how 

AGENTS.md

 carries through to automated pipelines.

Common Mistakes

Writing a novel.

 If your config file is over 500 lines, most of it is being ignored. LLMs have limited instruction-following capacity — a focused 50-line file outperforms a sprawling 1,000-line one. Codex CLI will also silently truncate anything past 

project_doc_max_bytes

 , so oversized files actively lose context.

Duplicating across tools.

 Maintain one source of truth ( 

AGENTS.md

 ) and have tool-specific files reference it. Don't copy-paste the same rules into 

CLAUDE.md

 , 

.cursorrules

 , and 

copilot-instructions.md

 .

Using /init or auto-generators.

 Auto-generated config files tend to be generic and bloated. Write yours by hand — every line should earn its place by solving a real problem you've encountered.

Including things a linter handles.

 Use 2-space indentation and always add trailing commas are Prettier's job, not your AI config file's job.

Forgetting to update.

 These files rot just like any other documentation. When your stack changes, update the instructions. A wrong instruction is worse than no instruction.

Committing AGENTS.override.md .

 The override file is meant for local, machine-specific tweaks. Add it to 

.gitignore

 the same day you create one — once it's committed, it stops being an override and becomes another source of drift.

Looking to automate your deployment pipeline? DeployHQ deploys code from Git to your servers automatically — one less thing to configure, with automated deployments straight from your repository. Get started free.

Have questions? Reach out at support@deployhq.com or find us on X/Twitter.

Tell us how you feel about this post?

[-] thumbsup

 

1

 

[-] laughing

 

0

 

[-] heart

 

0

 

[-] sad

 

0

 

[-] penguin

 

0

Enjoy this? Share it!

Share on LinkedIn

https://www.linkedin.com/shareArticle?title=CLAUDE.md%2C+AGENTS.md+%26+Copilot+Instructions%3A+Configure+Every+AI+Coding+Assistant&url=https%3A%2F%2Fwww.deployhq.com%2Fblog%2Fai-coding-config-files-guide&summary=Configure+Claude+Code%2C+Codex%2C+Cursor%2C+Copilot%2C+Gemini%2C+and+Windsurf+with+AGENTS.md+and+CLAUDE.md+that+actually+work+%E2%80%94+no+auto-generated+bloat.+&mini=true&source=The+DeployHQ+Blog

Share on X

https://twitter.com/share?text=CLAUDE.md%2C+AGENTS.md+%26+Copilot+Instructions%3A+Configure+Every+AI+Coding+Assistant&url=https%3A%2F%2Fwww.deployhq.com%2Fblog%2Fai-coding-config-files-guide

Share on Bluesky

https://bsky.app/intent/compose?text=CLAUDE.md%2C%20AGENTS.md%20%26%20Copilot%20Instructions%3A%20Configure%20Every%20AI%20Coding%20Assistant%20https%3A%2F%2Fwww.deployhq.com%2Fblog%2Fai-coding-config-files-guide

Share on Mastodon

https://mastodonshare.com/?text=CLAUDE.md%2C%20AGENTS.md%20%26%20Copilot%20Instructions%3A%20Configure%20Every%20AI%20Coding%20Assistant%20https%3A%2F%2Fwww.deployhq.com%2Fblog%2Fai-coding-config-files-guide

Written by

Alex M

Alex is a content specialist on the DeployHQ team, focused on helping developers streamline their deployment workflows. With a background in DevOps and technical writing, Alex enjoys breaking down complex topics into actionable guides for the DeployHQ and DeployBot communities.

More posts →

https://www.deployhq.com/blog

About DeployHQ

 

 

DeployHQ automates your deployment workflow — push code to your repository and let DeployHQ build, test, and deploy to any server. Supports Git, SSH/SFTP, cloud providers, and integrations with the tools you already use.

Start deploying for free

https://www.deployhq.com/signup

Back to top

https://www.deployhq.com/blog/ai-coding-config-files-guide

DeployHQDeployHQ

https://www.deployhq.com/

All systems operational

https://status.deployhq.com/

GitHubGitHub

https://github.com/deployhq

 

XX

https://x.com/deployhq

 

LinkedInLinkedInLinkedIn

https://linkedin.com/company/deployhq/

 

BlueskyBlueskyBluesky

https://bsky.app/profile/deployhq.com

Deploy faster with confidence.

From idea to production in minutes.

Product

Features

https://www.deployhq.com/features

 

Pricing

https://www.deployhq.com/pricing

 

Testimonials

https://www.deployhq.com/customers

 

Documentation

https://www.deployhq.com/support

 

API Reference

https://api.deployhq.com/docs

 

Integrations

https://www.deployhq.com/features/integrations

 

For Developers

https://www.deployhq.com/for-developers

 

For Agencies

https://www.deployhq.com/for-agencies

 

For Engineering Teams

https://www.deployhq.com/for-engineering-teams

Resources

Blog

https://www.deployhq.com/blog

 

Support Center

https://www.deployhq.com/support

 

Guides and tutorials

https://www.deployhq.com/guides

 

Status Page

https://status.deployhq.com/

 

Changelog

https://changelog.deployhq.com/

 

Learn Git

https://www.deployhq.com/git

 

AI PageSpeed

https://pagespeed.deployhq.com/

 

DeployHQ AI

https://www.deployhq.com/features/ai

 

DeployHQ MCP Server

https://www.deployhq.com/features/deployhq-mcp

 

CLI & Agents

https://www.deployhq.com/agents

 

PR Radar

https://www.deployhq.com/features/pr-radar

 

Single Sign-On

https://www.deployhq.com/features/sso

 

Ask AI

https://www.deployhq.com/support#ask-ai

Solutions

Deploy from GitHub

https://www.deployhq.com/deploy-from-github

 

Deploy from GitLab

https://www.deployhq.com/deploy-from-gitlab

 

Deploy from Bitbucket

https://www.deployhq.com/deploy-from-bitbucket

 

Deploy from Slack

https://www.deployhq.com/features/integrations/slack

 

Hosting

https://www.deployhq.com/hosting

 

Managed VPS Hosting

https://www.deployhq.com/hosting/managed-vps

 

Static Hosting

https://www.deployhq.com/hosting/static

 

Shared Hosting Deployments

https://www.deployhq.com/shared-hosting

 

VPS Deployments

https://www.deployhq.com/vps

 

WordPress Deployments

https://www.deployhq.com/wordpress

 

Zero Downtime

https://www.deployhq.com/features/zero-downtime-deployments

 

Turbo Deployments

https://www.deployhq.com/features/turbo-deployments

 

Game Server Deployments

https://www.deployhq.com/deploy-to-game-servers

Company

About

https://www.deployhq.com/about

 

Careers

https://saas.group/careers/

 

Contact

https://www.deployhq.com/contact

 

Terms of Service

https://www.deployhq.com/terms

 

Privacy Policy

https://www.deployhq.com/privacy

 

Security

https://www.deployhq.com/security

 

Cookie Policy

https://www.deployhq.com/blog/ai-coding-config-files-guide

Compare

DeployHQ vs Buddy

https://www.deployhq.com/compare/deployhq-vs-buddy

 

DeployHQ vs Jenkins

https://www.deployhq.com/compare/deployhq-vs-jenkins

 

DeployHQ vs GitHub Actions

https://www.deployhq.com/compare/deployhq-vs-github-actions

 

DeployHQ vs CircleCI

https://www.deployhq.com/compare/deployhq-vs-circleci

 

DeployHQ vs Laravel Forge

https://www.deployhq.com/compare/deployhq-vs-laravel-forge

 

All comparisons

https://www.deployhq.com/compare

2026 DeployHQ (saas.group LLC). All rights reserved. 

Running on 100% renewable energy

https://www.deployhq.com/green
