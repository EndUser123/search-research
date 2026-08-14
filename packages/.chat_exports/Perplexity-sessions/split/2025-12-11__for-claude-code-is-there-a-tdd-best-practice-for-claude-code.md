---
title: "for claude code, is there a TDD best practice for claude code hooks?"
date: "2025-12-11"
mode: "COPILOT"
uuid: "0aea0b40-a772-4ce5-b108-9e799dd11bcc"
entry_count: 3
---

## Human

for claude code, is there a TDD best practice for claude code hooks?

## Assistant

## TDD Best Practices for Claude Code Hooks

Yes, there are established TDD best practices specifically for Claude Code hooks. The community has developed several patterns and tools that address Claude's default tendency to write implementation first, which conflicts with test-driven development principles.

### The Core Challenge

Claude Code's natural behavior is to implement features first, skipping or minimizing test coverage. This is a structural problem in single-context LLM workflows—when everything runs in one context window, the test writer's analysis bleeds into the implementer's thinking, causing the model to design tests around anticipated implementations rather than true test-first development.[1][2]

### Enforcing TDD with Hooks: TDD Guard

One proven approach is **TDD Guard**, which uses hooks to validate TDD adherence before modifications execute. The system intercepts file modifications and checks for three common violations:[1]

- Implementing functionality without a relevant failing test
- Implementing more than necessary to pass a test  
- Adding more than one test at a time

TDD Guard works by persisting context data to files between hook phases, allowing different hooks (validation before changes, lint checks after) to access shared state without complex inter-process communication. When violations are detected, the hook blocks the action and provides corrective feedback.[1]

The key insight from TDD Guard's development is that **mechanical rule enforcement alone isn't sufficient**. While enforcing test-first development works, it doesn't guarantee meaningful refactoring or good design. The system evolved to combine blocking validation with lightweight linting tools (like Sonar) to identify complexity and encourage genuine refactoring, not just superficial changes.[1]

### Multi-Agent Architecture: Skills + Subagents + Hooks

A more comprehensive approach uses **skills, subagents, and hooks working together**. The critical innovation is context isolation—each TDD phase runs in separate subagent contexts:[2]

**The RED phase (test writer)** sees only the feature requirement, with no implementation context to bias test design

**The GREEN phase (implementer)** sees only the failing test, unable to be influenced by how tests were structured

**The REFACTOR phase (refactorer)** evaluates clean implementation with a dedicated refactoring checklist

This architectural separation prevents the LLM from "cheating" at TDD by subconsciously designing tests around anticipated code.[2]

To reliably activate this multi-agent TDD workflow, use a **`UserPromptSubmit` hook** that injects a mandatory skill evaluation sequence before every prompt. Research shows this increases skill activation from ~20% to ~84%:[3][2]

```
"hooks": {
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "npx tsx \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-skill-eval.ts\"",
          "timeout": 5
        }
      ]
    }
  ]
}
```

The hook script forces Claude to explicitly evaluate which skills apply before proceeding with implementation.[3]

### General Hook Best Practices

Beyond TDD-specific patterns, effective hook usage for quality assurance follows these principles:[4]

**Use specific file patterns** rather than running heavy operations on every edit

**Make hooks fast**—avoid operations that interrupt workflow or require user input

**Prioritize code quality enforcement** (linting, type checking) and running relevant tests after changes

**Keep hooks simple**—complex logic belongs in scripts, not hooks

**Test hook commands manually first** before adding them to your configuration

Common hook events include `PostToolUse` (after Claude edits files), `PreToolUse` (before Claude acts), and `UserPromptSubmit` (when you submit a prompt).[4]

### Getting Started

Start simple with one hook for type checking or linting, then gradually add more as you discover what helps your workflow. The setup cost is relatively low (~2 hours for a complete TDD system with skills and subagents), after which feature requests automatically follow the Red-Green-Refactor cycle without manual enforcement.[2]

## Human

What github.com repos should I look at?

## Assistant

## Recommended GitHub Repositories

Here are the key repositories for Claude Code hooks and TDD best practices you should explore:

### TDD-Focused Repositories

**nizos/tdd-guard** is the foundational repository for automated TDD enforcement. It provides a complete hook system that validates Test-Driven Development principles, preventing Claude from skipping tests or over-implementing. It supports multiple languages (TypeScript, JavaScript, Python, PHP, Go, Rust) and includes reporters for Vitest, Jest, Pytest, PHPUnit, and more. This is essential if you want structured TDD enforcement in Claude Code.[1][2]

### General Hook Collections

**decider/claude-hooks** is a comprehensive Python-based hook system for code quality validation and automation. It includes validators for function length, file length, line length, nesting depth, and package age checking. The implementation uses a dispatcher pattern and is well-documented for extending with custom hooks.[3]

**timoconnellaus/define-claude-code-hooks** provides a TypeScript-based approach to defining hooks. It offers predefined hooks for logging `PreToolUse` and `Stop` events, with automatic log rotation and session tracking. This is useful if you prefer a more programmatic, type-safe hook definition approach.[4]

**EvanL1/claude-code-hooks** is a collection of practical hooks including Git security checks, NPM package safety validation, Java build checks, and AWS security enforcement. Good for learning different hook patterns and seeing real-world use cases.[5]

### Curated Resources

**hesreallyhim/awesome-claude-code** is a curated list of awesome commands, files, and workflows specifically for Claude Code. This provides broader context beyond just hooks.[6]

**disler/claude-code-hooks-mastery** focuses on mastery-level hook implementation patterns.[7]

### Official Documentation

**code.claude.com/docs/en/hooks** provides the official Anthropic documentation for Claude Code hooks, including the reference for project-specific hook scripts and environment variables like `CLAUDE_PROJECT_DIR`.

### Learning Path Recommendation

Start with **nizos/tdd-guard** if TDD is your primary focus. If you want a more modular approach to hooks, explore **decider/claude-hooks** for Python-based validation. For TypeScript projects with logging needs, **timoconnellaus/define-claude-code-hooks** provides good patterns. Use **awesome-claude-code** as a reference library for discovering other community implementations.

## Human

Multi-Agent Architecture: Skills + Subagents + Hooks, what about for this?

## Assistant

## GitHub Repositories for Multi-Agent TDD Architecture

Here are the key repositories to explore for implementing the multi-agent skills + subagents + hooks pattern for TDD:

### The Foundational Reference: alexop.dev Implementation

**alexop.dev's post on Custom TDD Workflow** documents a complete, production-tested multi-agent TDD system. This is the most comprehensive resource—it walks through the exact structure of skills and subagents needed for Red-Green-Refactor isolation, including:[1]

- A **tdd-integration skill** that orchestrates the three phases
- Three specialized subagents: **tdd-test-writer**, **tdd-implementer**, and **tdd-refactorer**
- A **UserPromptSubmit hook** that injects mandatory skill evaluation (boosting activation from ~20% to ~84%)[1]
- Complete agent system prompts with phase gates and decision frameworks

This is the gold standard for the architecture you're asking about. The code is Vue-focused but framework-agnostic—the principles apply equally to Python, Go, Rust, or any language.

### Production-Ready Subagent Collections

**serco-chen/agents** contains 61+ specialized production-ready subagents with model assignments (Haiku for cost-effective tasks, Sonnet for standard work, Opus for complex analysis). While broader than TDD, it demonstrates professional subagent organization, tool configuration, and sequential/parallel orchestration patterns useful for building your own TDD subagents.[2]

**0xfurai/claude-code-subagents** has 100+ subagents covering programming languages, frameworks, infrastructure, and databases. Useful for understanding how to structure specialized subagents, though not TDD-focused.[3]

**kyle-cassidy/claude-code-agents** provides production-ready subagents—good reference for agent quality and specificity.[4]

### Hook Implementation & Context Isolation

**GitHub Issue: Allow Hooks to Bridge Context Between Sub-Agents** documents three official patterns for solving context isolation between parent and child agents using `SubagentStop` and `UserPromptSubmit` hooks. Essential for understanding how to maintain isolation while passing results between TDD phases.[5]

### Subagent Orchestration Patterns

**VoltAgent/awesome-claude-code-subagents** shows how to structure complex multi-agent workflows with sequential, parallel, and conditional branching patterns. The `/full-stack-feature` and `/incident-response` command patterns demonstrate orchestration you could adapt for TDD multi-phase workflows.[6]

### Skill Activation & Hook Optimization

The Reddit post on **AppendSubagents Hook** documents the ~99% subagent activation pattern using `UserPromptSubmit` hooks with `-s` flags, directly supporting the technique mentioned in the alexop.dev article for forcing skill evaluation.[7]

## Quick Start Path

**Start here**: Read through alexop.dev's article end-to-end to understand the complete architecture—skills, subagents, hooks, and the context isolation problem they solve.

**Then clone**: The patterns from serco-chen/agents and 0xfurai/claude-code-subagents to see professional subagent organization.

**Implement**: Create your own `.claude/skills/tdd-integration.md` and three `.claude/agents/tdd-*.md` subagents following the alexop.dev template, adapted to your tech stack.

**Deploy hooks**: Add the `UserPromptSubmit` hook from alexop.dev's settings.json to force skill evaluation consistently.

The setup cost is ~2 hours, after which every feature request follows Red-Green-Refactor automatically without manual intervention.[1]
