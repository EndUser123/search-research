---
title: "Hook Lifecycle And Safety Overrides"
created: 2026-08-11
source: nlm-sync-2026-08-11
tags: [nlm-synced, reference, claude]
summary: >
  Claude Code's hook pipeline defines 27 event types spanning tool authorization, session lifecycle, subagent coordination, context management, workspace events, and notifications. Stop and SubagentStop hooks must honor a stop_hook_active contract, since the runtime enforces a hard cap (CLAUDE_CODE_ST
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook 4017aa6e-35fb-426d-bc53-34620bec405e" ([INGESTED] - Claude Code Guide: Production Hooks and Agent Skills, synced 2026-08-11)
  - "Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems - arXiv" (https://arxiv.org/html/2604.14228v1, transcript synced 2026-08-11)
  - "Claude Code's 9-block safety override fires on every persistence mode (ultrawork/ralph/autopilot/ultragoal/...) · Issue #3138 · Yeachan-Heo/oh-my-claudecode - GitHub" (https://github.com/Yeachan-Heo/oh-my-claudecode/issues/3138, transcript synced 2026-08-11)
  - "Hook Lifecycle - Claude-Mem" (https://docs.claude-mem.ai/architecture/hooks, transcript synced 2026-08-11)
  - "[BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/49585, transcript synced 2026-08-11)
provenance:
  chain:
    - level: concept
      id: hook-lifecycle-and-safety-overrides
    - level: notebook
      id: 4017aa6e-35fb-426d-bc53-34620bec405e
      title: [INGESTED] - Claude Code Guide: Production Hooks and Agent Skills
      url: https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e
    - level: cluster
      id: 4
      name: claude-github-https
    - level: source_url
      url: https://arxiv.org/html/2604.14228v1
      title: Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems - arXiv
    - level: source_url
      url: https://github.com/Yeachan-Heo/oh-my-claudecode/issues/3138
      title: Claude Code's 9-block safety override fires on every persistence mode (ultrawork/ralph/autopilot/ultragoal/...) · Issue #3138 · Yeachan-Heo/oh-my-claudecode - GitHub
    - level: source_url
      url: https://docs.claude-mem.ai/architecture/hooks
      title: Hook Lifecycle - Claude-Mem
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/49585
      title: [BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub
relations:
  - target: wiki/concepts/compaction-pipeline.md
    type: related
  - target: wiki/concepts/tool-authorization-pipeline.md
    type: related
  - target: wiki/concepts/permission-modes.md
    type: related
---

# Hook Lifecycle And Safety Overrides

## Decision context

**Definition:** Claude Code's hook pipeline defines 27 event types spanning tool authorization, session lifecycle, subagent coordination, context management, workspace events, and notifications. Stop and SubagentStop hooks must honor a stop_hook_active contract, since the runtime enforces a hard cap (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP, default 9) that force-overrides hooks returning decision:block beyond that limit.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills*, clustered into the "claude-github-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The source describes a five-stage observation pattern (SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd) used by claude-mem to capture session state via fire-and-forget HTTP calls (timeout 2s) to a worker process on port 37777.
- Stop and SubagentStop hooks must return success (e.g., {continue: true, suppressOutput: true}) when the payload carries stop_hook_active: true, otherwise the runtime's consecutive-block counter hits its cap and force-overrides the hook.
- The 9-block safety override fires on every persistence mode (ultrawork, ralph, autopilot, ultragoal, ultraqa, pipeline, team, omcTeams, swarm, ultrapilot) when persistent-mode.mjs fails to read stop_hook_active and keeps emitting decision:block.
- A separate normalizeMessagesForAPI pipeline (smooshSystemReminderSiblings, smooshIntoToolResult, mergeAdjacentUserMessages) folds dynamic <system-reminder> text into tool_result.content every turn; gated by feature flag tengu_chair_sermon (Statsig-cached via _CACHED_MAY_BE_STALE), the fold is byte-non-idempotent across turns whenever reminder values change (token_usage, output_token_usage, budget_usd, deferred_tools_delta, todo_reminder, mcp_instructions_delta).
- The non-idempotency of the smoosh pass invalidates the prompt cache prefix, producing cache_creation bursts (observed ~99M tokens on 204 fusion-attributable turns, ~56% of one session's total cache_creation spend on Opus 4.7 1M-context).
- PostToolUse hooks can return updatedMCPToolOutput to mutate MCP tool results before they enter the context; for non-MCP tools the tool_result is emitted before PostToolUse fires, so the same mutability does not apply.
- Hook persistence commands support four types: shell (type: command), LLM prompt (type: prompt), HTTP (type: http), and agentic verifier (type: agent); non-persistable callbacks (type: callback) are used by SDK and internal instrumentation.
- Hook sources include settings.json, plugins, and managed policy at startup; skill-scoped hooks register dynamically on each skill invocation (utils/hooks.ts).
- Of the 27 documented event types, 5 participate directly in the authorization flow (PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied); the remaining 22 cover lifecycle and orchestration.
- A hook allow decision does not bypass subsequent deny-first rule evaluation; subsequent layers (rule evaluation, classifier, sandbox) still apply.

## Verifiable values

| Name | Value |
|---|---|
| Stop-hook consecutive-block cap | `9 (default) via CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` |
| OHC persistent-mode max_reinforcements default | `50 (effectively capped at ~9 by the Stop-hook override)` |
| Observed fusion-attributable cache_creation spend | `~99M tokens across 204 turns on one Opus 4.7 1M-context session` |
| Cache_creation spike magnitude per smoosh-drift turn | `tens to hundreds of thousands of tokens` |
| claude-mem HTTP timeout | `2000 ms (fire-and-forget)` |
| claude-mem worker port | `37777` |
| Total hook event types | `27` |
| Hook event types in authorization flow | `5 (PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied)` |
| Max output-token recovery attempts per turn | `3 (MAX_OUTPUT_TOKENS_RECOVERY_LIMIT)` |

## Related concepts

- /compaction-pipeline — Compaction Pipeline
- /tool-authorization-pipeline — Tool Authorization Pipeline
- /permission-modes — Permission Modes
- /stop-conditions — Stop Conditions
- /reactive-compaction — Reactive Compaction

## Citations (from contributing transcripts)

- **Claim:** A hook blocked the turn from ending 9 consecutive times — overriding and ending turn. For Stop/SubagentStop hooks, check stop_hook_active in the input and return success while it's true. Set CLAUDE_CODE_STOP_HOOK_BLOCK_CAP to raise this limit.
  - Source: Claude Code's 9-block safety override fires on every persistence mode (ultrawork/ralph/autopilot/ultragoal/...) · Issue #3138 · Yeachan-Heo/oh-my-claudecode - GitHub (`5ea9a3cd-e539-4104-a2da-85ad75743520`)
  - Context: Claude Code emits this warning before forcibly ending the turn: A hook blocked the turn from ending 9 consecutive times — overriding and ending turn.
- **Claim:** Claude Code's Stop/SubagentStop hook contract sends a stop_hook_active: true field when the hook is being re-invoked after a previous {decision: "block"}; hooks must return success when this flag is true, otherwise the hard cap (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP, default 9) kicks in and force-overrides.
  - Source: Claude Code's 9-block safety override fires on every persistence mode (ultrawork/ralph/autopilot/ultragoal/...) · Issue #3138 · Yeachan-Heo/oh-my-claudecode - GitHub (`5ea9a3cd-e539-4104-a2da-85ad75743520`)
  - Context: Claude Code's Stop/SubagentStop hook contract sends a stop_hook_active: true field in the hook payload when the hook is being re-invoked after a previous {decision: "block"}
- **Claim:** persistent-mode.mjs never reads data.stop_hook_active, so every persistence mode (ralph, ultragoal, autopilot, ultrapilot, ultrawork, ultraqa, pipeline, team, omcTeams, swarm) keeps emitting decision:block until Claude Code's hard cap of 9 always wins first.
  - Source: Claude Code's 9-block safety override fires on every persistence mode (ultrawork/ralph/autopilot/ultragoal/...) · Issue #3138 · Yeachan-Heo/oh-my-claudecode - GitHub (`5ea9a3cd-e539-4104-a2da-85ad75743520`)
  - Context: this means every persistence mode — ralph, ultragoal, autopilot, ultrapilot, ultrawork, ultraqa, pipeline, team, omcTeams, swarm — keeps emitting {decision: "block", reason: …}
- **Claim:** normalizeMessagesForAPI runs a smoosh pass every turn that folds <system-reminder>-prefixed text blocks into the preceding tool_result.content string; because reminders carry dynamic values (token_usage, output_token_usage, budget_usd, deferred_tools_delta, todo_reminder, mcp_instructions_delta), the smoosh produces different byte output turn-over-turn.
  - Source: [BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub (`a3beaf53-0eea-4ad5-b2f1-b0bca52b1723`)
  - Context: normalizeMessagesForAPI runs a smoosh pass every turn that folds <system-reminder>-prefixed text blocks into the preceding tool_result.content string.
- **Claim:** Feature gate tengu_chair_sermon (~lines 2274, ~2335) is Statsig-cached via _CACHED_MAY_BE_STALE; when ON, mergeUserContentBlocks takes the universal-smoosh branch (messages.ts:2628-2643) and folds each incoming reminder into the currently-last tool_result of the accumulating message.
  - Source: [BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub (`a3beaf53-0eea-4ad5-b2f1-b0bca52b1723`)
  - Context: Feature gate tengu_chair_sermon ~2274, ~2335: Statsig-cached (_CACHED_MAY_BE_STALE) gate; when ON, runs the merge+smoosh pipeline.
- **Claim:** Of 204 fusion-attributable turns across one user session, cache_creation summed to ~99M tokens, ~56% of total cache_creation spend; cache_read clustered tightly at ~19,282 tokens (tools-only) or ~16,700 (smaller tools set).
  - Source: [BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub (`a3beaf53-0eea-4ad5-b2f1-b0bca52b1723`)
  - Context: ~99M cache_creation tokens on fusion-attributable turns — ~56% of this session's total cache_creation spend went to re-caching content that was already present in prior turns.
- **Claim:** The source defines 27 hook events spanning tool authorization (PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied), session lifecycle (SessionStart, SessionEnd, Setup, Stop, StopFailure), user interaction (UserPromptSubmit, Elicitation, ElicitationResult), subagent coordination (SubagentStart, SubagentStop, TeammateIdle, TaskCreated, TaskCompleted), context management (PreCompact, PostCompact, InstructionsLoaded, ConfigChange), workspace events (CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove), and notifications.
  - Source: Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems - arXiv (`46952a5a-560e-43c1-a518-344293f38167`)
  - Context: The source code defines 27 hook events spanning tool authorization (PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied), session lifecycle (SessionStart, SessionEnd, Setup, Stop, StopFailure)...
- **Claim:** PreToolUse hooks can return permissionDecision (deny or ask, but allow does not bypass subsequent checks), permissionDecisionReason, and updatedInput to modify parameters; hook allow does not bypass subsequent rule-based denies or safety checks.
  - Source: Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems - arXiv (`46952a5a-560e-43c1-a518-344293f38167`)
  - Context: PreToolUse: Can return permissionDecision (deny or ask, but allow does not bypass subsequent checks), permissionDecisionReason, and updatedInput (modify parameters).
- **Claim:** claude-mem implements a 5-stage hook system: SessionStart (context-hook.js), UserPromptSubmit (new-hook.js), PostToolUse (save-hook.js), Stop (summary-hook.js), SessionEnd (cleanup-hook.js); the extension HTTP call has a 2-second timeout and does not wait for AI processing.
  - Source: Hook Lifecycle - Claude-Mem (`5ee95d53-5ace-43dc-b200-4058e413ae9c`)
  - Context: Claude-Mem implements a 5-stage hook system that captures development work across Claude Code sessions.
- **Claim:** claude-mem hooks send fire-and-forget HTTP POST requests with 2000ms timeouts to a worker service on port 37777; the worker performs AI compression asynchronously using an event-driven queue.
  - Source: Hook Lifecycle - Claude-Mem (`5ee95d53-5ace-43dc-b200-4058e413ae9c`)
  - Context: The extension's HTTP call has a 2-second timeout and doesn't wait for AI processing. The worker handles compression asynchronously using an event-driven queue.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `4017aa6e-35fb-426d-bc53-34620bec405e`
(cluster `claude-github-https`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills](https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
