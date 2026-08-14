---
title: "in claude code, is it possible, maybe with the claude agent sdk, to automatically switch to plan mode?  for instance if "
date: "2026-01-09"
mode: "COPILOT"
uuid: "d253cd9c-ef0c-432e-a513-f743d5b86790"
entry_count: 1
---

## Human

in claude code, is it possible, maybe with the claude agent sdk, to automatically switch to plan mode?  for instance if I ask a qusetion, that could trigger plan mode, thus no accidental implemetnation.

## Assistant

Great question. Yes, this is absolutely possible with Claude Code, and I've found some interesting approaches you can use depending on your exact workflow. Let me break this down:

## **The Answer: Auto Plan Mode**

**Yes**, you can automatically trigger plan mode without manual activation. There are two main approaches:

### **1. Auto Plan Mode via System Prompt (Recommended)**

This is the modern approach using the `--append-system-prompt` flag (available since v1.0.51). You essentially inject a system prompt that forces Claude into planning mode before any destructive operations:

```bash
claude --append-system-prompt "CRITICAL WORKFLOW REQUIREMENT

MANDATORY PLANNING STEP: Before executing ANY tool (Read, Write, Edit, Bash, Grep, etc.), you MUST:

1. FIRST: Use exit_plan_mode tool to present your plan
2. WAIT: For explicit user approval before proceeding
3. ONLY THEN: Execute the planned actions

ZERO EXCEPTIONS: This applies to EVERY tool usage regardless of perceived task scope.

ENFORCEMENT: If you execute ANY tool without first using exit_plan_mode, you have violated this requirement."
```

Or save it to a file for reusability:
```bash
claude --append-system-prompt "$(cat auto-plan-mode.txt)"
```

This leverages the hidden `exit_plan_mode` tool to force a planning workflow automatically.

### **2. Claude Agent SDK / Custom Hooks**

If you're building more sophisticated workflows, you can use Claude Code's **hook system** or the **Claude Agent SDK** to:
- Programmatically detect when certain types of queries are made
- Automatically trigger plan mode based on conditional logic
- Create custom workflows that enforce planning for specific operations

Users have built `UserPromptSubmit` hooks that detect when you switch to Plan Mode and automatically use the `@agent-plan` subagent for deterministic planning.

### **3. Plan Mode Detection (Automatic)**

Claude Code also has some **built-in automatic detection** that triggers plan mode when:
- The task scope is large (e.g., "refactor the entire authentication system")
- You're working with unfamiliar codebases
- Multi-file changes are detected

However, this isn't always reliable—hence the system prompt approach is preferred.

## **Best Practice for Your Workflow**

Given your heavy Claude Code usage, I'd recommend:

1. **Create a reusable auto-plan-mode.txt** file with your customized system prompt
2. **Alias it** in PowerShell for quick access:
   ```powershell
   alias claude-plan="claude --append-system-prompt \$(cat ~/auto-plan-mode.txt)"
   ```
3. **Use it for analysis/complex tasks**, switch to normal mode for simple edits when you trust the context

This prevents accidental implementations while maintaining flexibility for quick iterations when appropriate.

The `exit_plan_mode` tool approach is particularly elegant because it works within Claude Code's existing permission architecture rather than fighting against it.

Would you want me to help you create a customized auto-plan-mode system prompt tailored to your specific safety requirements? I could build one that targets specific operations (e.g., planning for writes/edits but allowing reads immediately) if that fits your workflow better.
