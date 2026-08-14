---
title: "claude code: Remove the prompt hook — it doesn't work architecturally for Stop events

what type of hook events does it "
date: "2026-02-09"
mode: "CONCISE"
uuid: "b0367dce-4805-4c81-9487-6575a5c5654c"
entry_count: 3
---

## Human

claude code: Remove the prompt hook — it doesn't work architecturally for Stop events

what type of hook events does it work for?

## Assistant

Prompt-based hooks in Claude Code do not work architecturally for Stop events due to limitations in how they receive input (often only metadata, not full context like the model's response). They are explicitly designed to work with Stop and SubagentStop events, but practical issues like incomplete data make them unreliable for Stop.[1][7]

## Supported Hook Events
Claude Code supports multiple hook events, but prompt-based hooks (type: "prompt") are limited primarily to Stop and SubagentStop per documentation—though Stop has known architectural flaws leading to recommendations against their use there.[2][1]

## Working Alternatives
Script-based hooks (shell commands or JSON-output scripts) function reliably across events including PreToolUse, UserPromptSubmit, PostToolUse, PermissionRequest, TeammateIdle, TaskCompleted, and SessionEnd. For Stop specifically, use scripts that output JSON with `decision: "block"` and `reason` to continue processing, while checking `stop_hook_active` to avoid loops.[1][2]

| Event | Prompt Hook Support | Primary Use |
|-------|---------------------|-------------|
| Stop | Limited (architectural issues) | Final checks, prevent stopping [1] |
| SubagentStop | Yes | Subagent completion control [2] |
| PreToolUse | No (script/JSON) | Block tool calls [2] |
| UserPromptSubmit | No (script/JSON) | Add context or block prompts [2] |

## Human

best practices for prompt-based hooks (type: "prompt")

## Assistant

Prompt-based hooks (type: "prompt") in Claude Code are best used for judgment-based decisions on events where full input context is reliably provided to the evaluating model, avoiding architectural gaps like Stop events.

## Key Use Cases
Focus on events such as UserPromptSubmit, where hooks can validate prompts, inject context, or block ambiguous inputs before processing. They excel at clarity checks—e.g., wrapping user prompts to detect vagueness and trigger AskUserQuestion for refinement.[2][3][4]

## Prompt Design Tips
Craft concise prompts instructing the model (Haiku by default) to output structured JSON like `{"ok": true}` or `{"ok": false, "reason": "details"}` for decisions. Specify custom models via `model` if needed, and use `additionalContext` sparingly to avoid bloating the primary agent's window.[3][2]

## Common Pitfalls
Avoid Stop/SubagentStop due to incomplete data (metadata only, no response). Prefer agent hooks (type: "agent") for codebase verification needing tools like Grep; reserve prompt hooks for lightweight, input-only evaluations.[2][3]

| Event | Best for Prompt Hooks | JSON Response Format [2] |
|-------|-----------------------|------------------------------|
| UserPromptSubmit | Prompt validation/injection | `{"decision": "block", "reason": "...", "additionalContext": "..."}` |
| PermissionRequest | Approval logic | `{"hookSpecificOutput": {"decision": {"behavior": "ask"}}}` |
| Stop | Avoid | `{"ok": false, "reason": "..."}` (unreliable) |

## Human

“Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.
Filename requirements:


Include: product (claude-code), main feature (hooks), key hook (userpromptsubmit), platform if relevant (e.g. windows), and any special focus (e.g. async, debug).


Use kebab-case with underscores between major sections, and append today’s date as YYYY-MM-DD.


Return only one filename string.


Topic index requirements:


5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.


Each bullet: SectionTitle – short description.


Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

## Assistant

claude-code_hooks-userpromptsubmit_windows-agnostic-debugging-and-design_2026-02-09

- HooksOverview – Lifecycle, event types, and where prompt-based hooks fit into Claude Code’s architecture.  
- PromptHookRole – When to use type:"prompt" hooks versus command/agent hooks for judgment-based decisions.  
- UserPromptSubmitCore – How UserPromptSubmit hooks intercept prompts, add context, and block or reshape requests before processing.  
- JSONContracts – Recommended JSON schemas for prompt hooks (decisions, reasons, additionalContext) and consistent parsing patterns.  
- StopHookLimitations – Why Stop/SubagentStop are a poor fit for prompt hooks and the architectural constraints involved.  
- ValidationPatterns – Designing UserPromptSubmit prompt hooks for ambiguity checks, safety filters, and “ask-for-clarification” flows.  
- ContextBudgeting – Strategies for keeping injected context lean to avoid window bloat while still enriching Claude’s understanding.  
- DebugWorkflow – Using verbose mode, transcripts, and targeted logging to debug hook behavior and event firing.  
- CrossPlatformNotes – Considerations and quirks when running hooks in Windows-heavy or mixed OS dev environments.  
- FutureExtensions – Ideas for layering async hooks, quality gates, and multi-hook chains around UserPromptSubmit-centric workflows.
