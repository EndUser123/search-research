---
title: "Claude Code Session Identity and Hook Context"
created: 2026-08-11
source: nlm-sync-2026-08-11
tags: [nlm-synced, reference, github]
summary: >
  A pattern of issues and design notes around how Claude Code identifies a session (via sessionId UUID) and what context — environment variables, JSON stdin fields, plugin root — is actually available inside tool execution and hook execution contexts. The sources collectively describe a gap between wh
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook 4017aa6e-35fb-426d-bc53-34620bec405e" ([INGESTED] - Claude Code Guide: Production Hooks and Agent Skills, synced 2026-08-11)
  - "Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/47018, transcript synced 2026-08-11)
  - "Stop hooks in Skills never fire · Issue #19225 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/19225, transcript synced 2026-08-11)
  - "[BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code" (https://github.com/anthropics/claude-code/issues/24371, transcript synced 2026-08-11)
  - "claude-code-best-practice/reports/claude-global-vs-project-settings.md at main - GitHub" (https://github.com/shanraisshan/claude-code-best-practice/blob/main/reports/claude-global-vs-project-settings.md, transcript synced 2026-08-11)
  - "claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub" (https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md?plain=1, transcript synced 2026-08-11)
provenance:
  chain:
    - level: concept
      id: claude-code-session-identity-and-hook-context
    - level: notebook
      id: 4017aa6e-35fb-426d-bc53-34620bec405e
      title: [INGESTED] - Claude Code Guide: Production Hooks and Agent Skills
      url: https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e
    - level: cluster
      id: 2
      name: github-claude-code
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/47018
      title: Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/19225
      title: Stop hooks in Skills never fire · Issue #19225 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/24371
      title: [BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code
    - level: source_url
      url: https://github.com/shanraisshan/claude-code-best-practice/blob/main/reports/claude-global-vs-project-settings.md
      title: claude-code-best-practice/reports/claude-global-vs-project-settings.md at main - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md?plain=1
      title: claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub
relations:
  - target: wiki/concepts/claude-code-hooks-(pretooluse-/-posttooluse-/-stop-/-subagentstop-/-sessionstart-/-sessionend-/-userpromptsubmit-/-precompact-/-notification).md
    type: related
  - target: wiki/concepts/claude-code-skills-(skill.md-frontmatter-hooks).md
    type: related
  - target: wiki/concepts/claude-code-sessionstart-hook-pattern-for-env-injection-via-$claude_env_file.md
    type: related
---

# Claude Code Session Identity and Hook Context

## Decision context

**Definition:** A pattern of issues and design notes around how Claude Code identifies a session (via sessionId UUID) and what context — environment variables, JSON stdin fields, plugin root — is actually available inside tool execution and hook execution contexts. The sources collectively describe a gap between what the documentation promises and what the shell or hook environment exposes, alongside workarounds that persist identity through SessionStart hooks.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills*, clustered into the "github-claude-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The env vars that DO exist in Claude Code's Bash tool context as of v2.1.104 are CLAUDECODE=1, CLAUDE_CODE_ENTRYPOINT=cli, and CLAUDE_CODE_EXECPATH; CLAUDE_SESSION_ID is NOT exported, so `echo $CLAUDE_SESSION_ID` returns empty.
- String substitution of ${CLAUDE_SESSION_ID} inside skill prompt text was added in v2.1.9, but that is a prompt-time substitution only — it does not surface the value to shell commands or to hook execution.
- Shell PID mapping is unreliable: $$ returns a child bash PID and $PPID resolves to 1 (orphaned) on Windows/MinGW, so tools cannot reliably walk back up to the parent claude.exe process.
- Session JSON files at ~/.claude/sessions/<pid>.json contain sessionId + pid, so the data exists on disk — but tools cannot discover which file is theirs without a known PID or session ID.
- The ~/.claude/sessions/snapshot-unknown.txt file writes session=unknown instead of the actual session ID, so it provides no usable identity today.
- Issue #19225 documents that Stop hooks defined inside SKILL.md frontmatter never fire, even though PreToolUse hooks in the same skill DO fire; a commenter attributes this to the system firing SubagentStop instead of Stop for skill scopes.
- Issue #24371 reports CLAUDE_SESSION_ID regression: it worked in a previous version and is no longer present as a built-in env var; the workaround injects it via a SessionStart hook that writes to $CLAUDE_ENV_FILE and emits hookSpecificOutput.additionalContext.
- The SessionStart hook workaround captures session_id from stdin JSON, then echoes `export CLAUDE_CODE_SESSION_ID="$SESSION_ID"` into $CLAUDE_ENV_FILE (guarded so resume/continue sessions don't overwrite) and returns `{ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: 'CLAUDE_CODE_SESSION_ID=...' } }` so the model can also see it.
- Per the hook-development SKILL.md, all hooks receive a JSON stdin containing session_id, transcript_path, cwd, permission_mode, and hook_event_name; SessionStart additionally exposes $CLAUDE_ENV_FILE for exporting env vars into the shell.
- Hook scripts run in parallel and do not see each other's output; hook configuration is loaded at session start and requires restarting Claude Code to pick up changes — there is no hot-swap.
- Defaults from the hook documentation: command hooks timeout 60s, prompt hooks timeout 30s; matcher syntax supports exact names, alternation ('Write|Edit'), wildcard ('*'), and regex ('mcp__.*__delete.*'), and is case-sensitive.
- Exit-code contract: 0 success (stdout in transcript), 2 blocking (stderr fed back to Claude), other non-blocking error.
- Per the global-vs-project settings report, ~/.claude/settings.json (user) and .claude/settings.json (project) are dual-scope, with project > global precedence and .claude/settings.local.json sitting above project for personal uncommitted overrides.
- Skills, hooks, commands, agents, and rules all exist at both ~/.claude/ and .claude/ scopes; tasks (~/.claude/tasks/), teams (~/.claude/teams/), keybindings (~/.claude/keybindings.json), and per-project auto-memory (~/.claude/projects/<hash>/memory/) are global-only.
- The Tasks system introduced in v2.1.16 (Jan 22, 2026) replaces TodoWrite and stores persistent state at ~/.claude/tasks/{task-list-id}/, with multi-session sharing driven by the env var CLAUDE_CODE_TASK_LIST_ID.

## Verifiable values

| Name | Value |
|---|---|
| Claude Code version for #47018 (CLAUDE_SESSION_ID env request) | `v2.1.104` |
| Version where ${CLAUDE_SESSION_ID} prompt substitution was added | `v2.1.9` |
| Claude Code version for #24371 (CLAUDE_SESSION_ID regression report) | `2.1.37 (confirmed still broken at 2.1.52)` |
| Tasks system introduction version | `v2.1.16 (January 22, 2026)` |
| Agent Teams announcement date | `February 5, 2026` |
| Default command hook timeout | `60 seconds` |
| Default prompt hook timeout | `30 seconds` |
| Example session ID UUID format observed | `736848ea-e359-4f8c-9e44-7f2dea2ad9b1 (and a4b692e2-9095-43e4-849d-385e9e454782 in workaround example)` |
| Observed bash PID / PPID on Windows MinGW | `$$=1338, PPID=1` |
| Example claude.exe PID from tasklist | `57116` |

## Related concepts

- /claude-code-hooks-(pretooluse-/-posttooluse-/-stop-/-subagentstop-/-sessionstart-/-sessionend-/-userpromptsubmit-/-precompact-/-notification) — Claude Code Hooks (PreToolUse / PostToolUse / Stop / SubagentStop / SessionStart / SessionEnd / UserPromptSubmit / PreCompact / Notification)
- /claude-code-skills-(skill.md-frontmatter-hooks) — Claude Code Skills (SKILL.md frontmatter hooks)
- /claude-code-sessionstart-hook-pattern-for-env-injection-via-$claude_env_file — Claude Code SessionStart hook pattern for env injection via $CLAUDE_ENV_FILE
- /claude-code-global-vs-project-settings-precedence — Claude Code global vs project settings precedence
- /claude-code-tasks-system-(~/.claude/tasks/) — Claude Code Tasks system (~/.claude/tasks/)
- /claude-code-agent-teams-(~/.claude/teams/) — Claude Code Agent Teams (~/.claude/teams/)
- /claude-code-plugins-(hooks/hooks.json-wrapper-format,-${claude_plugin_root}) — Claude Code Plugins (hooks/hooks.json wrapper format, ${CLAUDE_PLUGIN_ROOT})

## Citations (from contributing transcripts)

- **Claim:** CLAUDE_SESSION_ID is not exported in the Bash tool context as of v2.1.104; only CLAUDECODE, CLAUDE_CODE_ENTRYPOINT, and CLAUDE_CODE_EXECPATH exist.
  - Source: Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub (`5adc948e-9ccf-4e1e-ad56-1bcc85aba676`)
  - Context: $ env | grep CLAUDE
CLAUDECODE=1
CLAUDE_CODE_ENTRYPOINT=cli
CLAUDE_CODE_EXECPATH=C:\Users\Chad\.local\bin\claude.exe

# No session ID:
$ echo "$CLAUDE_SESSION_ID"
(empty)
- **Claim:** ${CLAUDE_SESSION_ID} string substitution was added in v2.1.9 for skill prompt text but does not surface as a shell env var.
  - Source: Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub (`5adc948e-9ccf-4e1e-ad56-1bcc85aba676`)
  - Context: While ${CLAUDE_SESSION_ID} string substitution was added for skill prompt text in v2.1.9, the session ID is not available as an environment variable in the Bash tool execution context or in hook shell commands.
- **Claim:** PID-based session lookup is broken on Windows MinGW — $$ is the child bash PID and $PPID resolves to 1.
  - Source: Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub (`5adc948e-9ccf-4e1e-ad56-1bcc85aba676`)
  - Context: # PID chain is broken (MinGW on Windows):
$ echo "$$=$$ PPID=$PPID"
$$=1338 PPID=1
- **Claim:** Session JSON files at ~/.claude/sessions/<pid>.json contain sessionId + pid, but tools cannot discover which file belongs to them.
  - Source: Expose CLAUDE_SESSION_ID as environment variable in tool execution context · Issue #47018 · anthropics/claude-code - GitHub (`5adc948e-9ccf-4e1e-ad56-1bcc85aba676`)
  - Context: Session JSON files in ~/.claude/sessions/ — Yes — Contains sessionId + pid, but tools can't discover which file is theirs
- **Claim:** Stop hooks declared inside SKILL.md frontmatter never fire, while PreToolUse hooks in the same skill do.
  - Source: Stop hooks in Skills never fire · Issue #19225 · anthropics/claude-code - GitHub (`87247bcb-3788-4941-a668-3b3543a92575`)
  - Context: The Stop hook never fires. The marker file is never created… PreToolUse hooks in the same skill DO work - I have a PreToolUse hook with matcher: "Bash" that fires correctly
- **Claim:** A community commenter explains the missing Stop behavior by linking to #19220, stating that SubagentStop fires instead of Stop for skill scopes.
  - Source: Stop hooks in Skills never fire · Issue #19225 · anthropics/claude-code - GitHub (`87247bcb-3788-4941-a668-3b3543a92575`)
  - Context: Reason is #19220
it fires SubagentStop instead
- **Claim:** CLAUDE_SESSION_ID regressed in 2.1.37 and was still missing at 2.1.52; it is not exported in the main agent context.
  - Source: [BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code (`e5a311fc-ed5e-4c5e-b520-48c04ba1e924`)
  - Context: CLAUDE_SESSION_ID seems to be no longer available in the main agent context… Claude Code Version 2.1.37… Confirmed this is still an bug on CC version 2.1.52
- **Claim:** The workaround injects CLAUDE_CODE_SESSION_ID via a SessionStart hook that writes to $CLAUDE_ENV_FILE and emits hookSpecificOutput.additionalContext for the model.
  - Source: [BUG] `CLAUDE_SESSION_ID` not found in env · Issue #24371 · anthropics/claude-code (`e5a311fc-ed5e-4c5e-b520-48c04ba1e924`)
  - Context: jq -n --arg ctx "CLAUDE_CODE_SESSION_ID=$SESSION_ID" \
    '{ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: $ctx } }'… if [ -n "$CLAUDE_ENV_FILE" ] && ! grep -q "CLAUDE_CODE_SESSION_ID" "$CLAUDE_ENV_FILE" 2>/dev/null; then
    echo "export CLAUDE_CODE_SESSION_ID=\"$SESSION_ID\"" > "$CLAUDE_ENV_FILE"
fi
- **Claim:** All hooks receive a JSON stdin containing session_id, transcript_path, cwd, permission_mode, and hook_event_name; $CLAUDE_ENV_FILE is exposed during SessionStart for persisting env vars.
  - Source: claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub (`ff2fcb50-fa28-4b37-a4d8-3e7acf36140f`)
  - Context: { "session_id": "abc123", "transcript_path": "/path/to/transcript.txt", "cwd": "/current/working/dir", "permission_mode": "ask|allow", "hook_event_name": "PreToolUse" }… $CLAUDE_ENV_FILE - SessionStart only: persist env vars here
- **Claim:** Hooks run in parallel, cannot see each other's output, and are loaded at session start — changes require restarting Claude Code.
  - Source: claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub (`ff2fcb50-fa28-4b37-a4d8-3e7acf36140f`)
  - Context: All matching hooks run in parallel… Hooks don't see each other's output… Hooks are loaded when Claude Code session starts. Changes to hook configuration require restarting Claude Code.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `4017aa6e-35fb-426d-bc53-34620bec405e`
(cluster `github-claude-code`). No claims are made
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
