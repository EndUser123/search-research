---
source_id: "bed3b7d5-b540-4d8c-8e03-c3edb6fcf28f"
title: "claude-code-hooks-schemas.md - GitHub Gist"
notebook_id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
url: https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34
type: web_page
exported: 2026-07-27
---

# claude-code-hooks-schemas.md - GitHub Gist
claude-code-hooks-schemas.md · GitHub

Skip to content

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#start-of-content

 

https://gist.github.com/

Search Gists

Search Gists

All gists

https://gist.github.com/discover

 

Back to GitHub

https://github.com/

 

Sign in

https://gist.github.com/auth/github?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34

 

Sign up

https://gist.github.com/join?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34&source=header-gist

 

https://gist.github.com/

Sign in

https://gist.github.com/auth/github?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34

 

Sign up

https://gist.github.com/join?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34&source=header-gist

You signed in with another tab or window. 

Reload

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34

 to refresh your session. You signed out in another tab or window. 

Reload

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34

 to refresh your session. You switched accounts on another tab or window. 

Reload

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34

 to refresh your session. Dismiss alert

Instantly share code, notes, and snippets.

FrancisBourre

https://gist.github.com/FrancisBourre

/ 

claude-code-hooks-schemas.md

Created 7 months ago

Show Gist options

Download ZIP

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34/archive/0b16dccad46225dfb4ce5c7b58d338c2df93f7aa.zip

Star 1 ( 1)

https://gist.github.com/login?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34

 You must be signed in to star a gist

Fork 0 ( 0)

https://gist.github.com/login?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34

 You must be signed in to fork a gist

Embed

Select an option

Embed Embed this gist in your website.

Share Copy sharable link for this gist.

Clone via HTTPS Clone using the web URL.

No results found

Learn more about clone URLs

https://docs.github.com/articles/which-remote-url-should-i-use

 Clone this repository at <script src="https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34.js"></script>

Save FrancisBourre/50dca37124ecc43eaf08328cdcccdb34 to your computer and use it in GitHub Desktop.

Code

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34

 

Revisions 1

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34/revisions

 

Stars 1

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34/stargazers

Embed

Select an option

Embed Embed this gist in your website.

Share Copy sharable link for this gist.

Clone via HTTPS Clone using the web URL.

No results found

Learn more about clone URLs

https://docs.github.com/articles/which-remote-url-should-i-use

Clone this repository at <script src="https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34.js"></script>

Save FrancisBourre/50dca37124ecc43eaf08328cdcccdb34 to your computer and use it in GitHub Desktop.

Download ZIP

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34/archive/0b16dccad46225dfb4ce5c7b58d338c2df93f7aa.zip

Raw

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34/raw/0b16dccad46225dfb4ce5c7b58d338c2df93f7aa/claude-code-hooks-schemas.md

claude-code-hooks-schemas.md

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#file-claude-code-hooks-schemas-md

title

Claude Code Hooks — Input & Output Schemas

description

Authoritative reference for the JSON input/output schemas for all Claude Code hook events, including blocking behaviors and exit codes

category

reference

tags

claude-code hooks json-schema api automation tool-control permissions stdin stdout

last_updated

2025-01-18

difficulty

advanced

estimated_time

30 minutes

author

Claude Code Team

status

published

audience

developers system-administrators devops-engineers

prerequisites

claude-code-basics json shell-scripting unix-signals

related_docs

claude-code-hooks-guide.md claude-code-settings.md claude-code-mcp.md

Claude Code Hooks — Input & Output Schemas (Reference)

A precise, implementation‑ready reference for the JSON 

input

 each hook receives on 

stdin

 and the 

output

 a hook may emit on 

stdout

 to steer Claude Code's behavior.

Scope: 

PreToolUse

 , 

PostToolUse

 , 

Notification

 , 

UserPromptSubmit

 , 

Stop

 , 

SubagentStop

 , 

PreCompact

 , 

SessionStart

 .

Table of Contents

Quick Map of Hook Events

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#quick-map-of-hook-events

Common Input Envelope

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#common-input-envelope

Common Output Contract

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#common-output-contract

Event-Specific Schemas

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#event-specific-schemas

PreToolUse

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#pretooluse

PostToolUse

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#posttooluse

Notification

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#notification

UserPromptSubmit

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#userpromptsubmit

Stop

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#stop

SubagentStop

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#subagentstop

PreCompact

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#precompact

SessionStart

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#sessionstart

Exit-Code-2 Behavior Matrix

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#exit-code-2-behavior-matrix

Matchers and MCP Tool Names

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#matchers-and-mcp-tool-names

Practical Tips

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#practical-tips

Sources

https://gist.github.com/FrancisBourre/50dca37124ecc43eaf08328cdcccdb34#sources

1) Quick Map of Hook Events

PreToolUse

 — before a tool call executes (approval/gating).

PostToolUse

 — after a tool completes successfully (validate/feedback).

Notification

 — on system notifications (permission wait, idle input).

UserPromptSubmit

 — when a user submits a prompt (pre‑processing).

Stop

 — when the main agent finishes its reply (not user interrupt).

SubagentStop

 — when a subagent (via 

Task

 ) finishes its reply.

PreCompact

 — right before conversation compaction.

SessionStart

 — when a session starts or resumes.

Matchers:

 Only 

PreToolUse

 and 

PostToolUse

 use 

matcher

 patterns for tools. Other events ignore 

matcher

 . MCP tools are named 

mcp__<server>__<tool>

 (e.g. 

mcp__filesystem__read_file

 ).

2) Common Input Envelope (all hooks)

Each hook receives a base envelope plus event‑specific fields:

{
  "type": "object",
  "properties": {
    "session_id":      { "type": "string" },
    "transcript_path": { "type": "string" },   // path to session .jsonl
    "cwd":             { "type": "string" },   // current working directory
    "hook_event_name": { "type": "string" }    // one of the 8 events
  },
  "required": ["session_id","transcript_path","cwd","hook_event_name"],
  "additionalProperties": true
}


3) Common Output Contract (all hooks)

Hooks can signal decisions via 

exit codes

 and/or 

structured JSON

 on 

stdout

 .

Exit codes

0

 → success. 

stdout

 is visible in transcript mode (Ctrl‑R). 

Special cases:

 for 

UserPromptSubmit

 

and

 

SessionStart

 , 

stdout

 is 

added to context

.

2

 → 

blocking

. 

stderr

 is routed according to the event (matrix below).

Other

 → non‑blocking error; 

stderr

 is shown to the user; execution continues.

Optional JSON fields (recognized by every hook)

{
  "type": "object",
  "properties": {
    "continue":       { "type": "boolean", "description": "If false, halt after hooks run (overrides decisions)" },
    "stopReason":     { "type": "string"  },
    "suppressOutput": { "type": "boolean", "description": "Hide this hook's stdout in transcript mode" }
  },
  "additionalProperties": true
}


Precedence:

 If 

"continue": false

 , Claude stops after hooks run — this 

overrides

 any 

"decision": "block"

 you might also set.

4) Event-Specific Schemas

4.1 

PreToolUse

When:

 After Claude prepares tool params 

before

 executing a tool. Good for policy checks and approvals.

Additional Input fields:

{
  "tool_name":  { "type": "string" },
  "tool_input": { "type": "object" }   // tool‑specific shape
}


Output (two styles):

A) Preferred (hookSpecificOutput):

{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow" | "deny" | "ask",
    "permissionDecisionReason": "string"
  }
}


B) Legacy (still supported):

{
  "decision": "approve" | "block",
  "reason": "string"
}


Semantics:

"allow"

 — bypasses permission UI (reason shown to 

user

, not Claude).

"deny"

 — blocks call (reason shown to 

Claude

).

"ask"

 — shows permission UI (reason shown to 

user

).

Exit code 2:

 blocks the tool call; 

stderr

 is sent to Claude.

4.2 

PostToolUse

When:

 Immediately 

after

 a tool completes successfully. Good for validating results and giving automated feedback.

Additional Input fields:

{
  "tool_name":     { "type": "string" },
  "tool_input":    { "type": "object" },
  "tool_response": { "type": "object" }
}


Output:

{
  "decision": "block" | null,
  "reason":   "string"
}


"block"

 — automatically prompts Claude with 

reason

 about the tool's result.

Omitted/ 

null

 — accept result; 

reason

 ignored.

Exit code 2:

 tool already ran; 

stderr

 shown to Claude.

4.3 

Notification

When:

 On system notifications (e.g., permission request; input idle ≥ 60s).

Additional Input fields:

{ "message": { "type": "string" } }


Output:

 Only 

common

 JSON fields apply (no event‑specific decisions).

Exit code 2:

 N/A; 

stderr

 shown to the 

user only

.

4.4 

UserPromptSubmit

When:

 As soon as the user submits a prompt, 

before

 Claude processes it.

Additional Input fields:

{ "prompt": { "type": "string" } }


Output options:

{
  "decision": "block" | null,
  "reason":   "string",                      // shown to user; not added to context
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "string"           // appended to context if not blocked
  }
}


"block"

 — prevents processing; prompt is erased from context.

Alternative:

 print plain text to 

stdout

 with exit code 

0

 — it will be 

injected into context

.

Exit code 2:

 blocks prompt; 

stderr

 shown to the 

user only

.

4.5 

Stop

When:

 Main agent finishes naturally (not user interrupt).

Additional Input fields:

{ "stop_hook_active": { "type": "boolean" } }  // true if a previous Stop hook already kept Claude running


Output:

{
  "decision": "block" | null,                 // prevent stopping
  "reason":   "string"                        // REQUIRED if decision = "block"
}


"block"

 — prevents stopping; 

reason

 instructs Claude on what to do next.

"continue": false

 in common fields halts everything and 

overrides

 

decision

 .

Exit code 2:

 blocks stoppage; 

stderr

 shown to Claude.

4.6 

SubagentStop

When:

 A subagent (via 

Task

 tool) finishes.

Input / Output:

 Same structure and semantics as 

Stop

 .

Exit code 2:

 blocks subagent stoppage; 

stderr

 shown to the subagent.

4.7 

PreCompact

When:

 Right before conversation compaction (manual 

/compact

 or automatic).

Additional Input fields:

{
  "trigger":             { "enum": ["manual","auto"] },
  "custom_instructions": { "type": "string" }  // empty when auto
}


Output:

 Only 

common

 JSON fields apply.

Exit code 2:

 N/A; 

stderr

 shown to the 

user only

.

4.8 

SessionStart

When:

 On new session start or resume.

Additional Input fields:

{ "source": { "enum": ["startup","resume","clear"] } }


Output (context injection):

{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "string"
  }
}


Also supported:

 printing plain text to 

stdout

 with exit code 

0

 — 

added to context

.

Exit code 2:

 N/A; 

stderr

 shown to the 

user only

.

Documentation note:

 Anthropic's page includes a reminder that mentions only 

UserPromptSubmit

 for stdout‑to‑context on code 0, while the bullet list states it applies to 

both

 

UserPromptSubmit

 

and

 

SessionStart

 . The bullet list is the authoritative statement; many teams rely on 

SessionStart

 stdout to inject bootstrapping context.

5) Exit-Code-2 Behavior Matrix

Event

Effect of exit code 2

PreToolUse

Blocks

 the tool call; 

stderr

 → Claude

PostToolUse

Tool already ran; 

stderr

 → Claude

Notification

N/A; 

stderr

 → 

user only

UserPromptSubmit

Blocks

 prompt; prompt erased; 

stderr

 → 

user only

Stop

Blocks

 stoppage; 

stderr

 → Claude

SubagentStop

Blocks

 stoppage; 

stderr

 → Claude (subagent)

PreCompact

N/A; 

stderr

 → 

user only

SessionStart

N/A; 

stderr

 → 

user only

6) Matchers and MCP tool names (where applicable)

PreToolUse

 / 

PostToolUse

 support 

matcher

 patterns targeting tools: exact string, regex ( 

Edit|Write

 ), or wildcard 

*

 (also 

""

 or omitted).

MCP tools appear as 

mcp__<server>__<tool>

 and can be matched similarly (e.g., 

mcp__filesystem__read_file

 ).

7) Practical Tips

Prefer 

hookSpecificOutput

 for new setups ( 

permissionDecision

 on 

PreToolUse

 , 

additionalContext

 on 

UserPromptSubmit

 / 

SessionStart

 ).

Use 

"continue": false

 sparingly; it halts processing and 

takes precedence

 over any 

"decision"

 fields.

For 

UserPromptSubmit

 / 

SessionStart

 , decide between 

stdout injection

 (quick text) and 

JSON additionalContext

 (explicit).

Keep hook scripts idempotent and time‑bounded; default timeout is 60s (configurable).

8) Sources

Anthropic — 

Hooks reference

 (event list, input/output, decisions, exit‑code semantics). 

https://docs.anthropic.com/en/docs/claude-code/hooks

https://docs.anthropic.com/en/docs/claude-code/hooks

Anthropic — 

Get started with Claude Code hooks

 (setup & examples). 

https://docs.anthropic.com/en/docs/claude-code/hooks-guide

https://docs.anthropic.com/en/docs/claude-code/hooks-guide

Sign up for free

https://gist.github.com/join?source=comment-gist

 

to join this conversation on GitHub

. Already have an account? 

Sign in to comment

https://gist.github.com/login?return_to=https%3A%2F%2Fgist.github.com%2FFrancisBourre%2F50dca37124ecc43eaf08328cdcccdb34

Footer

© 2026 GitHub, Inc.

Footer navigation

Terms

https://docs.github.com/site-policy/github-terms/github-terms-of-service

Privacy

https://docs.github.com/site-policy/privacy-policies/github-privacy-statement

Security

https://github.com/security

Status

https://www.githubstatus.com/

Community

https://github.community/

Docs

https://docs.github.com/

Contact

https://support.github.com?tags=dotcom-footer

Manage cookies

Do not share my personal information

You can't perform that action at this time.
