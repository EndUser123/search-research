---
title: "claude compound engineering"
date: "2026-02-01"
mode: "CONCISE"
uuid: "16c5a92c-5e80-4231-a619-c6e51251d05f"
entry_count: 1
---

## Human

claude compound engineering

## Assistant

Claude compound engineering refers to an AI-driven development workflow popularized by the Every team, using Claude Code to orchestrate multiple AI agents in a loop that makes each engineering task progressively easier.[1][3]

## Core Workflow
The process cycles through **Plan**, **Work**, **Review**, and **Compound** stages. Agents first generate detailed plans from feature ideas, then execute code in parallel across worktrees with tests, followed by multi-agent reviews to catch issues. Learnings from each cycle are documented as reusable prompts, skills, or patterns to reduce future effort—80% of time goes to planning/review for compounding gains.[3][1]

## Installation
Use the official open-source plugin from EveryInc: run `/plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin` then `/plugin install compound-engineering` in Claude Code. This adds commands like `/workflows:plan`, `/workflows:work`, and `/workflows:compound` for the full loop.[1]

## Philosophy
Traditional coding accumulates debt, but compound engineering inverts this—each feature adds reusable knowledge via agent orchestration, turning solo devs into team-scale producers. It's tool-agnostic but optimized for Claude Code's terminal-based autonomy (full repo access, git ops, parallel terminals).[5][3]
