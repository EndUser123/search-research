---
source_id: "33c4e8ba-bd96-4a83-8eed-f7f0fdbf2a16"
title: "Claude Code MCP Servers: How to Connect, Configure, and Use Them - Builder.io"
notebook_id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
url: https://www.builder.io/blog/claude-code-mcp-servers
type: web_page
exported: 2026-07-27
---

# Claude Code MCP Servers: How to Connect, Configure, and Use Them - Builder.io
Claude Code MCP Servers: How to Connect, Configure, and Use Them

Skip to main content

https://www.builder.io/blog/claude-code-mcp-servers#main

See how Frete cut frontend build time by 70% What are best AI tools? Take the State of AI survey

https://www.builder.io/customer-stories/frete

 

PRODUCTS PRODUCTS

Fusion Generate production-ready web apps and UIs

https://www.builder.io/fusion

Publish Generate, iterate, and optimize pages and headless content

https://www.builder.io/publish

 USERS USERS

Engineering teams Code faster with AI and your design system

https://www.builder.io/engineering-teams

Design teams Design with code, handoff with confidence

https://www.builder.io/design-teams

Product teams Ship prototypes that accelerate the entire software development lifecycle

https://www.builder.io/product-teams

Content teams Generate and publish experiences without developer dependency

https://www.builder.io/content-teams

 USE CASES USE CASES

Web apps

https://www.builder.io/web-apps

Prototypes

https://www.builder.io/prototypes

Design to code

https://www.builder.io/m/design-to-code

Landing pages

https://www.builder.io/landing-pages

Headless CMS

https://www.builder.io/headless-cms

Multi-brand CMS

https://www.builder.io/m/multi-brand-cms

Mobile apps

https://www.builder.io/m/mobile-apps

Marketing sites

https://www.builder.io/m/marketing-sites

Headless commerce

https://www.builder.io/m/headless-commerce

 Platform

LEARN LEARN

Blog Latest insights, tutorials, and announcements

https://www.builder.io/blog

Webinars Upcoming events and recorded sessions

https://www.builder.io/hub/home?resource-type=webinars

Guides Step-by-step instructions and use cases

https://www.builder.io/hub/home?resource-type=guides

Case Studies Real customer success stories

https://www.builder.io/hub/home?resource-type=customer+stories

 CONNECT CONNECT

Builder Forum Join the discussion, ask questions

https://forum.builder.io/

Partners Explore Builder partners and connect with a team

https://www.builder.io/m/partners

CMS Integrations Integrate with your stack and connect your tools

https://www.builder.io/m/integrations

 UPDATES UPDATES

Product Updates Latest features and improvements

https://www.builder.io/updates

 Resources

Fusion docs Learn to vibe code in new or existing apps

https://www.builder.io/c/docs/get-started-fusion

Publish docs Use Builder to publish content for your site

https://www.builder.io/c/docs/get-started-publish

Figma to code docs Convert Figma designs into real code

https://www.builder.io/c/docs/builder-figma-plugin

All docs

https://www.builder.io/c/docs/intro

 Docs

Enterprise

https://www.builder.io/enterprise

Pricing

https://www.builder.io/pricing

Contact sales

https://www.builder.io/m/demo

 

Sign up

https://www.builder.io/signup

 

Sign up

https://www.builder.io/signup

See how Frete cut frontend build time by 70% What are best AI tools? Take the State of AI survey

https://www.builder.io/customer-stories/frete

 

 

‹ Back to blog

https://www.builder.io/blog

AI

Claude Code MCP Servers: How to Connect, Configure, and Use Them

March 3, 2026

Written By 

Vishwas Gopinath

https://www.builder.io/blog/authors/vishwas-gopinath

I asked Claude Code to review a pull request, check Sentry for related production errors, and update the Jira ticket. Three different services in a single session. That's what a Claude Code MCP setup looks like when it clicks.

MCP (Model Context Protocol) gives 

Claude Code

https://www.builder.io/blog/what-is-claude-code

 access to external tools, databases, and APIs through a standardized protocol. Connecting a server takes one command. Figuring out which servers are worth adding and keeping context usage under control is where I've spent most of the time.

This guide covers your first 

claude mcp add

 command, configuration scopes, server recommendations, and fixes for the issues that come up most often.

What is MCP in Claude Code?

MCP ( 

Model Context Protocol

https://www.builder.io/blog/model-context-protocol

) is an open-source standard that lets Claude Code connect to external tools, databases, and APIs through a unified protocol. Claude Code acts as an MCP client, connecting to MCP servers that expose capabilities like file system access, browser automation, or database queries.

The naming can get confusing. Claude Code is the product. MCP is the protocol it speaks. Claude Code already handles code editing, search, and Bash execution. MCP extends that reach by connecting it to external tools and services.

Think of MCP servers as connectors. Each one gives Claude Code a new set of capabilities. Query a database, create a GitHub issue, run a browser test, or fetch design tokens from Figma.

Three transport types determine how Claude Code talks to MCP servers.

stdio

 runs local processes on your machine. Best for tools that need direct system access.

HTTP

 connects to remote servers. This is the recommended transport for cloud-based services.

SSE (Server-Sent Events)

 is the older remote transport. It's deprecated in favor of HTTP.

Claude Desktop also supports MCP servers through the same protocol, but it uses different configuration paths and offers a GUI for management. If you've already set up servers in Claude Desktop, you can import them directly (covered in the next section).

How do you add MCP servers to Claude Code?

Add MCP servers to Claude Code using the CLI command 

claude mcp add

 , or manually edit the JSON configuration at 

~/.claude.json

 . For existing Claude Desktop setups, run 

claude mcp add-from-claude-desktop

 to import them. Use environment variables in 

.mcp.json

 with 

${VAR}

 syntax to keep API keys out of version control.

The fastest way to set up a Claude Code MCP server is the CLI. This example adds the GitHub MCP server using the recommended HTTP transport.

const incr = num => num + 1


# Add the GitHub MCP server (HTTP transport, recommended)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# Authenticate with your GitHub account
# Run /mcp inside Claude Code and follow the browser login flow


Once connected, you can ask Claude Code to review PRs, create issues, search code, and manage repositories directly from your terminal. Many remote servers use OAuth for authentication. The 

/mcp

 command inside Claude Code handles the browser-based login flow.

For stdio servers that run as local processes, the syntax adds a 

--

 separator between the server name and the command.

# Add a local stdio server (Airtable example)
claude mcp add --transport stdio --env AIRTABLE_API_KEY=YOUR_KEY airtable \
  -- npx -y airtable-mcp-server


All options ( 

--transport

 , 

--env

 , 

--scope

 ) must come before the server name. The 

--

 separates Claude's flags from the server command.

If you prefer editing files directly, 

~/.claude.json

 is where the configuration lives. For scripted or automated setups, 

claude mcp add-json

 accepts raw JSON configuration.

# Add from JSON (useful for scripting and automation)
claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp"}'


To import servers you've already configured in Claude Desktop, run this.

claude mcp add-from-claude-desktop


This reads the Claude Desktop config file and lets you select which servers to import. It works on macOS and WSL.

For team-shared configurations, environment variables keep secrets out of version control. The 

.mcp.json

 file supports 

${VAR}

 and 

${VAR:-default}

 syntax.

{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}


Where does Claude Code store MCP configuration?

Claude Code stores MCP configuration at three scope levels: local (in 

~/.claude.json

 under your project path, private to you), project (in 

.mcp.json

 at the repo root, shared with your team via version control), and user (in 

~/.claude.json

 globally, available across all projects). Local scope takes precedence over project, which takes precedence over user.

Each scope fits a different use case.

Local scope

 (default): Stored in 

~/.claude.json

 under your project's path. Private to you. Use this for experiments or testing new servers like a database MCP server before recommending it to your team. Local scope keeps it out of everyone else's config.

Project scope

: Stored in 

.mcp.json

 at the repo root. Checked into version control. Use this for team-standard tooling like a shared Sentry server or project-specific database access.

User scope

: Stored in 

~/.claude.json

 across all projects. Use this for personal utilities you want everywhere, like a Notion or Linear MCP server.

The scope flag controls where the configuration lands.

# Local scope (default -- private to you, this project only)
claude mcp add --transport http stripe https://mcp.stripe.com

# Project scope (shared via .mcp.json, checked into git)
claude mcp add --transport http sentry --scope project https://mcp.sentry.dev/mcp

# User scope (available across all your projects)
claude mcp add --transport http notion --scope user https://mcp.notion.com/mcp


The precedence order (local > project > user) is the part worth remembering. You can share configurations with your team via a project-scoped 

.mcp.json

 while overriding individual servers locally.

In practice, your team commits a 

.mcp.json

 with a shared Sentry server and a project-specific database connection. Each developer then adds their own authentication tokens through local-scoped entries in 

~/.claude.json

 . The local config overrides the shared one, so server names stay consistent and credentials stay private.

For enterprise deployments, administrators can deploy a 

managed-mcp.json

 file to system-wide directories for centralized control. This supports allowlist and denylist policies to restrict which MCP servers employees can use.

Which MCP servers are worth adding to Claude Code?

The most practical MCP servers for coding tasks include GitHub (repository management and PR workflows), Playwright (browser automation and testing), Sentry (production error monitoring), PostgreSQL or Supabase (direct database access), and Figma (design-to-code workflows). Start with one or two servers that match your daily workflow.

I've organized the best options by category.

Code and repos:

 The GitHub MCP server is the one I'd install first. Connect it with a single command and you get PR reviews, issue creation, and repository management without leaving your terminal.

# Add GitHub MCP (HTTP transport)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/


After authenticating via 

/mcp

 , you can ask Claude Code to "review PR #456 and suggest improvements" or "create an issue for the bug we just found." The GitHub MCP server gives you tools for repository operations, pull requests, issues, and code search. You get the full GitHub workflow from your terminal.

Browser automation:

 Playwright MCP is the go-to for browser testing and automation. It handles more browser contexts than Puppeteer and works well for end-to-end test workflows.

Monitoring:

 Sentry's official MCP server connects Claude Code to your error monitoring data. Query production errors, view stack traces, and identify which deployment introduced regressions.

Database:

 PostgreSQL and 

Supabase MCP servers

https://www.builder.io/blog/supabase-mcp

 give Claude Code direct data access. Ask it to query revenue data, explore schemas, or find customers who haven't made a purchase in 90 days.

Design:

 Figma MCP bridges design and development. For full details on the setup and design-to-code workflows, see our 

Figma MCP server deep-dive

https://www.builder.io/blog/claude-code-figma-mcp-server

 and 

Claude Code to Figma

https://www.builder.io/blog/claude-code-to-figma

 guides.

Custom servers:

 You can also build project-specific MCP servers tailored to internal tools or workflows. Each Claude Code MCP integration extends the tool's reach into a different part of your stack.

For a broader list across categories, see our 

best MCP servers

https://www.builder.io/blog/best-mcp-servers-2026

 roundup.

The catch with adding multiple servers is context cost. Every server loads its tool definitions into your context window, and that adds up fast.

How does tool search reduce MCP context bloat in Claude Code?

Tool Search is a built-in Claude Code feature that dynamically loads only the tool definitions needed for each task, cutting context consumption from roughly 72,000 tokens to about 8,700 tokens. That's an 85% reduction. It activates automatically when tool definitions exceed 10% of the context window and requires Sonnet 4 or Opus 4 models.

Each MCP server exposes multiple tools. A single GitHub server adds tools for PRs, issues, code search, and more. Connect a handful of servers and you can hit 50+ tools, consuming 50,000-100,000 tokens of context before you even start working.

Tool Search fixes this by deferring tool definitions. Instead of loading everything upfront, Claude searches for the right tool on demand. Anthropic's engineering team published the numbers, and beyond the context savings, Opus 4 accuracy on tool selection improved from 49% to 74% with Tool Search enabled.

Tool Search requires Sonnet 4 or later, or Opus 4 or later. Haiku models don't support it. Configure it through the 

ENABLE_TOOL_SEARCH

 environment variable.

# Auto mode (default): activates when MCP tools exceed 10% of context
ENABLE_TOOL_SEARCH=auto claude

# Custom threshold: activate at 5% of context
ENABLE_TOOL_SEARCH=auto:5 claude

# Always on
ENABLE_TOOL_SEARCH=true claude

# Disabled: all MCP tools loaded upfront
ENABLE_TOOL_SEARCH=false claude


You can also set 

ENABLE_TOOL_SEARCH

 in your 

settings.json

 

env

 field to avoid passing it on every launch.

If you're running multiple MCP servers, leave Tool Search on 

auto

 . It's the feature that made multi-server setups practical.

How do you troubleshoot MCP connection issues in Claude Code?

The most common MCP issues and their fixes:

"Connection closed" errors:

 fix PATH/environment issues or add 

cmd /c

 wrapper on Windows

Server timeouts:

 switch from SSE to HTTP transport

"Command not found":

 add npm bin to PATH

JSON syntax errors:

 validate with a linter

macOS permission prompts

 on first run: grant permissions and retry

These five issues come up most often in GitHub Issues, the go-to troubleshooting resource for Claude Code MCP. The official MCP docs are the definitive reference for configuration details and edge cases. Run 

claude mcp list

 to verify server status after any configuration change.

"Connection closed" errors

Usually a PATH or environment issue. Claude Code launches MCP server subprocesses with a different shell environment than your terminal, so tools like 

node

 and 

npx

 may not be found. If you use nvm, either use absolute paths to the Node binary and server script, or ensure nvm loads in non-interactive shells by adding the nvm initialization block to your shell profile.

# Option 1: Use absolute paths
which node  # Find your Node path, e.g. /Users/you/.nvm/versions/node/v20.11.0/bin/node

# Option 2: Ensure nvm loads in non-interactive shells
# Add nvm initialization to ~/.zshrc or ~/.bashrc (not just ~/.zprofile)


On Windows, wrap npx commands with 

cmd /c

 to avoid this error entirely.

claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package


Without the 

cmd /c

 wrapper, Windows can't execute npx directly and throws "Connection closed."

Server timeout or hangs

If a server hangs during connection, the MCP_TIMEOUT environment variable doesn't apply to SSE connections. Switch to HTTP transport, which is more reliable and recommended by the official docs.

"Command not found" after npm install

The npm global bin directory isn't in your PATH. Add it to your shell profile ( 

export PATH="$(npm config get prefix)/bin:$PATH"

 ), or use 

npx

 prefix in your MCP server command to bypass the PATH issue entirely.

JSON config syntax errors

Trailing commas, missing quotes, and unescaped backslashes cause silent failures. JSON doesn't allow trailing commas (unlike JavaScript), and this is one of the most common mistakes in MCP config files. Validate your 

~/.claude.json

 and 

.mcp.json

 files with a JSON linter before restarting Claude Code.

macOS permission prompts

System permission dialogs block MCP server startup on first launch. Grant the permissions when prompted. The first run sometimes fails. Subsequent runs succeed.

After making any configuration changes, restart Claude Code and verify your server status.

claude mcp list


Configuration changes don't take effect until you restart. This catches everyone at least once.

How do you give your whole team access to MCP integrations?

This guide covers MCP from a developer's perspective. Terminal commands, JSON configs, scope flags. That works for your engineering team.

But designers, PMs, content teams, and marketing also need Sentry for error context, Linear for ticket status, and Supabase for content data. MCP only reaches developers who work in the terminal.

Builder.io

https://www.builder.io/

 is an agentic development platform where those same connections (Neon, Supabase, Linear, Sentry, Stripe, Notion) are built in and available to everyone on the team from day one. It runs 20+ agents in parallel, each in its own cloud container with a full dev environment and browser preview. Every integration feeds directly into every agent session.

Designers

 open a visual canvas connected to your real components, propose spacing and layout changes, and commit directly to the branch

PMs

 verify acceptance criteria against live previews pulling from the same database and monitoring data your code uses

Content and marketing teams

 update copy, review pages, and validate changes in the browser, then send validated PRs to your queue

You

 review architecture and merge clean code

See how Builder.io brings these integrations to your whole team

https://www.builder.io/

.

FAQ

What is the difference between Claude Desktop MCP and Claude Code MCP?

Both support the same MCP protocol, but they use different configuration paths and management approaches. Claude Desktop stores configs in its own settings file and offers a GUI. Claude Code uses 

~/.claude.json

 and 

.mcp.json

 with CLI-based management via 

claude mcp add

 . You can import Claude Desktop servers into Claude Code with 

claude mcp add-from-claude-desktop

 . Claude Code also supports Tool Search and project-scoped team configurations, which Claude Desktop doesn't.

Can you use Claude Code as an MCP server?

Yes. Run 

claude mcp serve

 to expose Claude Code's built-in tools (file editing, Bash execution, search, and more) to other MCP clients like Claude Desktop or Cursor. On first run, you need to accept permissions. Your MCP client is responsible for confirming individual tool calls. Connected clients access only Claude Code's own tools, though. They can't reach MCP servers that Claude Code itself is connected to.

What is the performance impact of running multiple MCP servers?

Each server adds tool definitions to your context window. Without Tool Search, 50+ tools consume 50,000-100,000 tokens. With Tool Search enabled (automatic on Sonnet 4+ and Opus 4+), context usage drops to roughly 8,700 tokens regardless of server count. Start with 1-2 servers and scale up as needed.

Does Claude Code MCP work with other AI coding tools like Cursor or Windsurf?

MCP is an open standard, so the same MCP servers work across all compatible clients. Cursor, Windsurf, and other MCP-compatible tools can connect to the same servers. Configuration syntax varies by client, but the servers themselves are interchangeable.

Conclusion

Claude Code MCP servers give you a connected development hub. Your repositories, databases, monitoring tools, and design systems all become accessible through a standardized, open protocol.

Start with the GitHub MCP server. It's one command to add, OAuth handles authentication, and you'll feel the difference the first time you ask Claude Code to review a PR without leaving your terminal. From there, add a second server that matches your workflow, set up project-scoped configuration so your team shares the same setup, and let Tool Search handle the context cost as you scale up.

If you're new to Claude Code, our 

Claude Code overview

https://www.builder.io/blog/what-is-claude-code

 covers the full picture.

 

Convert Figma designs into code with AI

Generate clean code using your components & design tokens

Try Fusion

https://builder.io/signup

 

Get a demo

https://www.builder.io/m/demo

 

 

 

 

 

 

 

 

 

 

 

Generate high quality code that uses your components & design tokens.

Try it now

https://builder.io/signup

 

Get a demo

https://www.builder.io/m/demo

 

Continue Reading

AI 5 MIN The Visual Agentic Development Series: How AI-Native Teams Ship Faster WRITTEN BY Amy Cross March 25, 2026

https://www.builder.io/blog/visual-agentic-development-series

Software engineering 6 MIN Fix the Workflow, Not the Headcount WRITTEN BY Amy Cross March 23, 2026

https://www.builder.io/blog/fix-the-workflow-not-the-headcount

Design 6 MIN Turn a Figma Landing Page into a Live Website WRITTEN BY Alice Moore March 23, 2026

https://www.builder.io/blog/turn-a-figma-landing-page-into-a-live-website

 

Product

Visual CMS

https://www.builder.io/m/visual-cms

Theme Studio for Shopify

https://www.builder.io/m/theme-studio

Sign up

https://www.builder.io/m/get-started

Login

https://www.builder.io/login

Featured Integrations

React

https://www.builder.io/m/react

Angular

https://www.builder.io/m/angular

Next.js

https://www.builder.io/m/nextjs

Gatsby

https://www.builder.io/m/gatsby

Resources

User Guides

https://www.builder.io/c/docs/guides/page-building

Developer Docs

https://www.builder.io/c/docs/getting-started

Forum

https://forum.builder.io/

Blog

https://www.builder.io/blog

Github

https://github.com/builderio/builder

Get In Touch

Chat With Us

Twitter

https://twitter.com/builderio

Linkedin

https://www.linkedin.com/company/builder-io/

Careers

https://www.builder.io/m/careers

© 2020 Builder.io, Inc.

Security

https://www.builder.io/c/security

Privacy Policy

https://www.builder.io/docs/privacy

Terms of Service

https://www.builder.io/docs/terms

Get the latest from Builder.io

[x] Developer Newsletter

Dev Drop Newsletter

News, tips, and tricks from Builder, for frontend developers.

 

[x] Marketing Newsletter

Product Newsletter

Latest features and updates on the Builder.io platform

By submitting, you agree to our Privacy Policy

https://builder.io/docs/privacy

 

Platform

Fusion

https://www.builder.io/fusion

Publish

https://www.builder.io/publish

Product Updates

https://www.builder.io/updates

Use Cases

Design to Code

https://www.builder.io/m/design-to-code

Headless CMS

https://www.builder.io/headless-cms

 

Multi-Brand CMS

https://www.builder.io/m/multi-brand-cms

Landing Pages

https://www.builder.io/landing-pages

Web Apps

https://www.builder.io/web-apps

Prototypes

https://www.builder.io/prototypes

Marketing Sites

https://www.builder.io/m/marketing-sites

Headless Commerce

https://www.builder.io/m/headless-commerce

Developer Resources

Documentation

https://www.builder.io/c/docs/developers

Fusion Docs

https://www.builder.io/c/docs/get-started-fusion

Publish Docs

https://www.builder.io/c/docs/get-started-publish

Frameworks

Design to Code >

CMS >

Page Builder >

Workflows

Figma AI to Production Code

https://www.builder.io/workflows/figma-ai

AI Prototyping for Product Managers

https://www.builder.io/workflows/ai-prototyping-product-managers

Figma to Storybook

https://www.builder.io/workflows/figma-to-storybook

Figma to App Converter

https://www.builder.io/workflows/figma-to-app

Resources

Blog

https://www.builder.io/blog

Webinars

https://www.builder.io/hub/home?resource-type=webinars

Guides

https://www.builder.io/hub/home?resource-type=guides

Case Studies

https://www.builder.io/hub/home?resource-type=customer+stories

Community Forum

https://forum.builder.io/

Partners

https://www.builder.io/m/partners

Affiliate Program

https://www.builder.io/affiliate

CMS Integrations

https://www.builder.io/m/integrations

CMS Blueprints

https://www.builder.io/c/blueprints

Explainers

https://www.builder.io/explainers

Glossary

https://www.builder.io/glossary

Agent-Native

https://agent-native.com/

Popular Guides

Figma to Code Guide

https://www.builder.io/hub/guides/figma-design-to-code

Headless CMS Guide

https://www.builder.io/m/knowledge-center/headless-cms-visual-guide

Headless Commerce Guide

https://www.builder.io/m/knowledge-center/headless-commerce

Composable DXP Guide

https://www.builder.io/m/explainers/composable-dxp

Company

About

https://www.builder.io/m/about-us

News

https://www.builder.io/news

Careers

https://www.builder.io/careers

Contact Sales

https://www.builder.io/m/demo

 

© 2026 Builder.io, Inc.

Security

https://www.builder.io/c/security

Privacy Policy

https://www.builder.io/legal/privacy

SaaS Terms

https://www.builder.io/legal/terms

Trust Center

https://trust.builder.io/

Cookie Preferences
