<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# claude code: Remove the prompt hook — it doesn't work architecturally for Stop events

what type of hook events does it work for?

Prompt-based hooks in Claude Code do not work architecturally for Stop events due to limitations in how they receive input (often only metadata, not full context like the model's response). They are explicitly designed to work with Stop and SubagentStop events, but practical issues like incomplete data make them unreliable for Stop.[^1_1][^1_7]

## Supported Hook Events

Claude Code supports multiple hook events, but prompt-based hooks (type: "prompt") are limited primarily to Stop and SubagentStop per documentation—though Stop has known architectural flaws leading to recommendations against their use there.[^1_2][^1_1]

## Working Alternatives

Script-based hooks (shell commands or JSON-output scripts) function reliably across events including PreToolUse, UserPromptSubmit, PostToolUse, PermissionRequest, TeammateIdle, TaskCompleted, and SessionEnd. For Stop specifically, use scripts that output JSON with `decision: "block"` and `reason` to continue processing, while checking `stop_hook_active` to avoid loops.[^1_1][^1_2]


| Event | Prompt Hook Support | Primary Use |
| :-- | :-- | :-- |
| Stop | Limited (architectural issues) | Final checks, prevent stopping [^1_1] |
| SubagentStop | Yes | Subagent completion control [^1_2] |
| PreToolUse | No (script/JSON) | Block tool calls [^1_2] |
| UserPromptSubmit | No (script/JSON) | Add context or block prompts [^1_2] |

<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_3][^1_4][^1_5][^1_6][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://code.claude.com/docs/en/hooks-guide

[^1_2]: https://code.claude.com/docs/en/hooks

[^1_3]: https://docs.claude-mem.ai/hooks-architecture

[^1_4]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^1_5]: https://www.datacamp.com/tutorial/claude-code-hooks

[^1_6]: https://hexdocs.pm/claude/hooks.html

[^1_7]: https://github.com/anthropics/claude-code/issues/11786

[^1_8]: https://www.reddit.com/r/ClaudeAI/comments/1odev4r/two_most_useful_hooks_stop_notification/

[^1_9]: https://mlearning.substack.com/p/hooks-in-cursor-and-claude-code-a-step-by-step-guide

[^1_10]: https://github.com/anthropics/claude-code/issues/10610

[^1_11]: https://bennycheung.github.io/hear-your-ai-agents-work

[^1_12]: https://www.youtube.com/watch?v=Q4gsvJvRjCU

[^1_13]: https://www.linkedin.com/posts/antonabyzov_claudecode-aiengineering-developertools-activity-7420637858362982400-mb9C

[^1_14]: https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d


---

# best practices for prompt-based hooks (type: "prompt")

Prompt-based hooks (type: "prompt") in Claude Code are best used for judgment-based decisions on events where full input context is reliably provided to the evaluating model, avoiding architectural gaps like Stop events.

## Key Use Cases

Focus on events such as UserPromptSubmit, where hooks can validate prompts, inject context, or block ambiguous inputs before processing. They excel at clarity checks—e.g., wrapping user prompts to detect vagueness and trigger AskUserQuestion for refinement.[^2_2][^2_3][^2_4]

## Prompt Design Tips

Craft concise prompts instructing the model (Haiku by default) to output structured JSON like `{"ok": true}` or `{"ok": false, "reason": "details"}` for decisions. Specify custom models via `model` if needed, and use `additionalContext` sparingly to avoid bloating the primary agent's window.[^2_3][^2_2]

## Common Pitfalls

Avoid Stop/SubagentStop due to incomplete data (metadata only, no response). Prefer agent hooks (type: "agent") for codebase verification needing tools like Grep; reserve prompt hooks for lightweight, input-only evaluations.[^2_2][^2_3]


| Event | Best for Prompt Hooks | JSON Response Format [^2_2] |
| :-- | :-- | :-- |
| UserPromptSubmit | Prompt validation/injection | `{"decision": "block", "reason": "...", "additionalContext": "..."}` |
| PermissionRequest | Approval logic | `{"hookSpecificOutput": {"decision": {"behavior": "ask"}}}` |
| Stop | Avoid | `{"ok": false, "reason": "..."}` (unreliable) |

<span style="display:none">[^2_1][^2_10][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.anthropic.com/engineering/claude-code-best-practices

[^2_2]: https://code.claude.com/docs/en/hooks

[^2_3]: https://code.claude.com/docs/en/hooks-guide

[^2_4]: https://www.reddit.com/r/ClaudeAI/comments/1o9t35o/built_a_hook_that_makes_claude_code_unvibe_your/

[^2_5]: https://claudecode.io/guides/prompt-engineering

[^2_6]: https://www.claudecode.io/guides/prompt-engineering

[^2_7]: https://www.claudecode.page/guides/best-practices

[^2_8]: https://github.com/disler/claude-code-hooks-mastery

[^2_9]: https://www.reddit.com/r/ClaudeCode/comments/1m7wml8/my_claude_code_setup_prompts_commands_hooks_and/

[^2_10]: https://www.youtube.com/watch?v=amEUIuBKwvg


---

# “Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.

Filename requirements:

Include: product (claude-code), main feature (hooks), key hook (userpromptsubmit), platform if relevant (e.g. windows), and any special focus (e.g. async, debug).

Use kebab-case with underscores between major sections, and append today’s date as YYYY-MM-DD.

Return only one filename string.

Topic index requirements:

5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.

Each bullet: SectionTitle – short description.

Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

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
<span style="display:none">[^3_1][^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_2][^3_3][^3_4][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://code.claude.com/docs/en/hooks-guide

[^3_2]: https://code.claude.com/docs/en/hooks

[^3_3]: https://www.anthropic.com/engineering/claude-code-best-practices

[^3_4]: https://github.com/disler/claude-code-hooks-mastery

[^3_5]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^3_6]: https://www.marc0.dev/en/blog/claude-code-hooks-production-patterns-async-setup-guide-1770480024093

[^3_7]: https://github.com/dagger/container-use/issues/253

[^3_8]: https://docs.anthropic.com/en/docs/claude-code/hooks?asuniq=d8f8d9d0

[^3_9]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/

[^3_10]: https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

[^3_11]: https://www.reddit.com/r/ClaudeAI/comments/1o9t35o/built_a_hook_that_makes_claude_code_unvibe_your/

[^3_12]: https://github.com/shanraisshan/claude-code-voice-hooks

[^3_13]: https://anthropic.mintlify.app/en/docs/claude-code/hooks-guide

[^3_14]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^3_15]: https://www.letanure.dev/blog/2025-08-06--claude-code-part-8-hooks-automated-quality-checks

