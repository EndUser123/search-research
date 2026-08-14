---
title: "google antigravity"
date: "2025-12-07"
mode: "CONCISE"
uuid: "68feb8cc-9b6c-4281-834f-0169bd856c2b"
entry_count: 1
---

## Human

google antigravity

## Assistant

Google Antigravity is Google’s new “agent‑first” AI development environment, built on Gemini 3 Pro and designed around autonomous coding agents rather than just inline autocomplete.[1][9]

## What Antigravity is

Google describes Antigravity as an agentic development platform: an IDE (forked from Visual Studio Code) where AI agents can plan, execute, and verify complex coding tasks across editor, terminal, and browser.  It was announced in November 2025 alongside Gemini 3 and is in public preview for Windows, macOS, and Linux, free for individual users with “generous” Gemini 3 Pro usage quotas.[9][1]

## Core features

Antigravity has two main views: a familiar editor view with an agent sidebar, and a Manager view that lets you orchestrate multiple agents working in parallel on different tasks or repositories.  Agents produce “artifacts” such as task lists, implementation plans, diffs, test runs, and browser recordings so you can review and approve or block actions instead of scrolling through raw tool calls.[2][1][9]

## Agent and browser integration

A key differentiator is deep browser integration: an agent can control a special Chrome profile via an extension to click, scroll, type, read DOM, capture screenshots, and even record videos, using that to gather context or validate app behavior.  Antigravity also enforces safety via deny‑lists and approval gates, for example blocking certain shell commands (like some uses of curl) unless you explicitly approve them.[2][9]

## Availability, models, and limits

Antigravity supports multiple models: Gemini 3 Pro as the default, plus support for Anthropic Claude Sonnet 4.5 and other compatible models, with model choice configurable per project or task.  Due to high demand, Google has adjusted rate limits using a “work done” metric (task complexity and duration) and now gives Google AI Pro/Ultra subscribers priority while still increasing free‑tier allowances.[5][6][1][9]

## Current issues and risks

Early adopters report strong capabilities but also serious failure modes, including at least one incident where an agentic workflow wiped an entire drive partition (“vibe‑coding” gone wrong) when performing file cleanup.  Commentators emphasize careful configuration of permissions, strict deny‑lists, and limiting filesystem access, especially when letting agents run unattended on important machines.[7][8]
