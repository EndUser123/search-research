---
source_id: "aacebe2f-3ab6-4648-be8d-dd08efa7a178"
title: "[Plugin] Cortex: An AI obsidian vault agent powered by claude-code - Share & showcase"
notebook_id: 55c988d8-818d-4ed9-b08b-12d6c697ff5f
url: https://forum.obsidian.md/t/plugin-cortex-an-ai-obsidian-vault-agent-powered-by-claude-code/112430
type: web_page
exported: 2026-07-28
---

# [Plugin] Cortex: An AI obsidian vault agent powered by claude-code - Share & showcase
[Plugin] Cortex: An AI obsidian vault agent powered by claude-code - Share & showcase - Obsidian Forum

Obsidian Forum

https://forum.obsidian.md/

[Plugin] Cortex: An AI obsidian vault agent powered by claude-code

https://forum.obsidian.md/t/plugin-cortex-an-ai-obsidian-vault-agent-powered-by-claude-code/112430

Share & showcase

https://forum.obsidian.md/c/share-showcase/9

plugin-release

https://forum.obsidian.md/tag/plugin-release

CptVideo

https://forum.obsidian.md/u/CptVideo

 March 18, 2026, 11:59pm 1

What is Cortex?

Cortex is an Obsidian plugin that puts a Claude Code agent inside your vault. You chat with Claude in a side panel; Claude can read, write, create, move, and organize your notes — the same way Claude Code works in a code project, applied to your Obsidian vault.

No API key required.

 Cortex is powered by Claude Code, Anthropic's desktop CLI tool included with Claude Pro and Max subscriptions — no separate API key needed.

Features

Chat panel

 — a persistent side panel for back-and-forth conversation with Claude

Full vault access

 — Claude can read, write, create, and move notes; the vault root is Claude's working directory. Plus, draft templates, compose dataviews, manage settings, etc.

Session persistence

 — resume previous conversations; sessions stored in 

.obsidian/plugins/cortex/.claude/sessions/

Context system

 — vault folder/file tree and persistent context file injected at session start; configurable depth

Autonomous memory

 — Claude maintains a context file across sessions as it learns your vault

Session history

 — named sessions, rename/delete, resume across restarts

No API key

 — uses your Claude Pro/Max subscription via the 

claude

 CLI

Quick Start (Install via BRAT)

Cortex is currently in beta. You can install it right now using BRAT in 3 simple steps:

Install BRAT:

 Settings → Community Plugins → Browse → search for “BRAT” → Install and Enable

Add TaskLens:

 Open BRAT settings → Add Beta Plugin → paste the repository link: 

https://github.com/ScottKirvan/Cortex

 - Click Add Plugin

Enable:

 Go to Settings → Community Plugins → scroll to “Cortex” → toggle on

I look forward to seeing what y'all think.

 

2 Likes

CptVideo

https://forum.obsidian.md/u/CptVideo

 March 19, 2026, 1:08am 2

" 

Add TaskLens

" - whoops, haha - copy/pasta

 

prog

https://forum.obsidian.md/u/prog

 March 20, 2026, 1:35pm 3

Hi, I am currently using ClaudeCode using Terminal Plugin in Obsidian. What are the benefits of using Cortex instead? Can it do something my current setup cannot? Cortex look cool but I am always weary of adding 3rd-party tools due to increased complexity and security concerns. Cheers!

1 Like

CptVideo

https://forum.obsidian.md/u/CptVideo

 March 20, 2026, 8:18pm 4

Hi 

@prog

https://forum.obsidian.md/u/prog

 !

I've been using claude-code alongside obsidian for a good long time now, so I know what you mean – I was originally like, “why bother?,” but then I was just like, I want this to be a lot tighter - I want the memory to be more persistent, to travel with the vault, to be able to easily add notes and things for context, to get a good UI based session management and things like that. The tight integration you can get is really nice - having it open notes for you automatically, change and update obsidian setting by just telling it to do so rather than digging for the settings myself, having it automatically know what note I'm working on, things like that.

The context depth and layering and per-note control is something I don't think you could reasonably or easily do in a terminal.

On the security side - I totally agree - big concern of mine too, so, it's open source (very permissible MIT license), so anyone can audit the code, it spawns the exact same claude binary as you're using in the terminal and it doesn't add any additional external calls or AI layers. It does have configurable safety modes — from readonly all the way up to full access — so you decide how much reach Cortex has, rather than it being all-or-nothing like most integrations.

If you're already comfortable in the terminal and you've managed to figure out a workflow for context and memory management, the biggest win is just going to be the convenience of the integration: having it one click or ctrl+p command away, and having it automatically build up and maintain it's context, it's knowledge of what notes are open, and ability to open them for you – I hate repetitive tasks and the integration takes care of a lot of that for free.

2 Likes

prog

https://forum.obsidian.md/u/prog

 March 21, 2026, 2:47pm 5

Thanks, this sounds good, I will definitely check it out!

1 Like

rigarcia

https://forum.obsidian.md/u/rigarcia

 April 4, 2026, 11:51pm 6

I too use Claude in the Terminal plugin and so far it works great! Claude literarily maintains the Vault, including coordinating with external sources and updating folders, files, etc. Haven't encountered issues with persistent memory.

Home

https://forum.obsidian.md/

Categories

https://forum.obsidian.md/categories

Guidelines

https://forum.obsidian.md/guidelines

Terms of Service

https://obsidian.md/terms

Privacy Policy

https://obsidian.md/privacy

Powered by 

Discourse

https://www.discourse.org/

, best viewed with JavaScript enabled
