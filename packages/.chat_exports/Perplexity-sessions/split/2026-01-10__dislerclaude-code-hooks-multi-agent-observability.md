---
title: "disler/claude-code-hooks-multi-agent-observability"
date: "2026-01-10"
mode: "CONCISE"
uuid: "e25640b3-3f38-40e7-a5b7-e61555e3e43d"
entry_count: 1
---

## Human

disler/claude-code-hooks-multi-agent-observability

## Assistant

The GitHub repo you’re looking for is here: https://github.com/disler/claude-code-hooks-multi-agent-observability.[1]

## What the project is

- Multi-agent **observability** system for Claude Code that captures all hook events (tool calls, user prompts, notifications, session lifecycle) and streams them into a central dashboard.[2][1]
- Lets you monitor many concurrent Claude Code instances with real-time timelines, session tracking, and summarized event payloads.[3][1][2]

## High-level architecture

- Data flow is: `Claude Agents → Hook Scripts → HTTP POST → Bun Server → SQLite → WebSocket → Vue Client`.[1]
- Server: Bun + TypeScript with SQLite for event storage and WebSocket endpoints; client: Vue 3 + TypeScript SPA for live visualization.[1]

## Key features

- Real-time WebSocket updates, live pulse chart of agent activity, multi-criteria filters (source app, session, event type, time range).[2][1]
- Chat transcript viewer, event summarization using fast models (e.g., Haiku), and support for multiple codebases/devices via a single observability backend.[2][1]

## Repo structure

- `apps/server`: Bun TS server (`index.ts`, `db.ts`, `types.ts`) plus SQLite DB.[1]
- `apps/client`: Vue 3 TS client with components like `EventTimeline.vue`, `LivePulseChart.vue`, and WebSocket/chart composables.[1]
- `.claude`: hook scripts (`send_event.py`, `pre_tool_use.py`, `post_tool_use.py`, `user_prompt_submit.py`, etc.) plus `settings.json` to wire into Claude Code hooks.[1]

## Using it with your own projects

- Clone the repo and start the system from its root: `./scripts/start-system.sh`, then open `http://localhost:5173`.[1]
- Copy the `.claude` directory into any project you want to observe, and update `.claude/settings.json` `source-app` to a unique name for each codebase, then keep the observability server running while you work.[3][1]
