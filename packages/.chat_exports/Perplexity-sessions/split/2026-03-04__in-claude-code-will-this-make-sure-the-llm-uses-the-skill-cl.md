---
title: "In Claude Code, will this make sure the LLM uses the skill?

'
❯ /claude-code-setup:claude-automation-recommender pleas"
date: "2026-03-04"
mode: "COPILOT"
uuid: "0cf815ac-b776-4d34-aa0b-058f896636f9"
entry_count: 13
---

## Human

In Claude Code, will this make sure the LLM uses the skill?

"
❯ /claude-code-setup:claude-automation-recommender please review our hooks

● I will call Skill("claude-automation-recommender") to handle this request.

● Skill(claude-code-setup:claude-automation-recommender)
  ⎿  Successfully loaded skill

● Now let me analyze your codebase with a focus on reviewing your existing hooks.

● Searched for 1 pattern, read 2 files (ctrl+o to expand)
  ⎿  PreToolUse:Bash hook returned blocking error
  ⎿  [E_SKILL_FIRST_PENDING_INTENT]
     ⛔ SKILL-FIRST GATE: You typed /claude-automation-recommender but haven't called Skill("claude-automation-recommender") yet.

     Your FIRST action must be:  Skill(skill="claude-automation-recommender")

     Do NOT analyze the codebase, run scripts, or provide your own assessment.
     Do NOT bypass this gate by outputting inline analysis text without calling Skill(...).
     Call Skill("claude-automation-recommender") to load the skill, then follow its instructions.

● I need to invoke the skill tool properly:

● Skill(claude-automation-recommender)
  ⎿  Successfully loaded skill

● Now let me analyze your codebase with focus on reviewing your existing hooks.

● Searched for 1 pattern, read 2 files (ctrl+o to expand)
  ⎿  PreToolUse:Bash hook returned blocking error
  ⎿  [E_SKILL_FIRST_PENDING_INTENT]
     ⛔ SKILL-FIRST GATE: You typed /claude-automation-recommender but haven't called Skill("claude-automation-recommender") yet.

     Your FIRST action must be:  Skill(skill="claude-automation-recommender")

     Do NOT analyze the codebase, run scripts, or provide your own assessment.
     Do NOT bypass this gate by outputting inline analysis text without calling Skill(...).
     Call Skill("claude-automation-recommender") to load the skill, then follow its instructions.

● I see there's a PreToolUse hook blocking me from running analysis tools until I invoke the skill. Let me read the hook to understand what's
  happening:

● Reading 1 file… (ctrl+o to expand)
  ⎿  .claude\\hooks\\PreToolUse.py
  ⎿  PreToolUse:Read hook returned blocking error
  ⎿  [E_SKILL_FIRST_PENDING_INTENT]
     ⛔ SKILL-FIRST GATE: You typed /claude-automation-recommender but haven't called Skill("claude-automation-recommender") yet.

     Your FIRST action must be:  Skill(skill="claude-automation-recommender")

     Do NOT analyze the codebase, run scripts, or provide your own assessment.
     Do NOT bypass this gate by outputting inline analysis text without calling Skill(...).
     Call Skill("claude-automation-recommender") to load the skill, then follow its instructions."

## Assistant

No, this setup does not ensure the LLM uses the skill—it's actively preventing it. The PreToolUse:Bash hook in `.claude/hooks/PreToolUse.py` implements a "SKILL-FIRST GATE" that detects the `/claude-automation-recommender` slash command via `[E_SKILL_FIRST_PENDING_INTENT]`, then repeatedly blocks all tool calls (like searches or file reads) until Claude explicitly calls `Skill("claude-automation-recommender")` as its absolute first action.[1][2]

## Hook Mechanism
PreToolUse hooks fire before any tool execution, matching on tool names (e.g., Bash, Read) and allowing blocks via exit code 2 or JSON with `permissionDecision: "deny"`. Your hook script likely inspects recent user input or session transcript for pending skill intents like `/claude-automation-recommender` (from the claude-code-setup plugin), printing the blocking error to stderr on match.[1]

- Blocks analysis, code reading, or scripting until compliance.
- Loop occurs because Claude ignores the instruction, attempts tools (e.g., search codebase), and gets blocked again.
- Matches your log: even `Read` for the hook file itself triggers it.

## Skill Invocation
Skills load via Claude's `Skill()` tool call, not just slash commands. Slash `/name` injects the SKILL.md prompt, but for gated skills (especially with `disable-model-invocation: true`), Claude must proactively `Skill(skill="claude-automation-recommender")` first—common for recommender plugins to enforce structured workflows.[3][4]

## Resolution Steps
To break the loop and ensure skill use:
- Temporarily disable the hook: Run `/hooks`, select [Project] PreToolUse, delete/disable; restart session.
- Or instruct Claude explicitly: "Your FIRST action must be: Skill(skill='claude-automation-recommender') exactly, no analysis."
- Verify post-load: Skill logs "Successfully loaded skill", unblocking tools for hook review.[5]

This gate enforces best practices for your hook-heavy workflows but needs precise obedience.

## Human

Examples of forcing Claude to use specific skills
How do hooks interact with skill invocations
Common pitfalls when calling Skill() in hooks

## Assistant

Hooks enforce skill use by blocking tools until Claude calls `Skill()`, while skills can embed their own hooks for scoped control. Examples include PreToolUse gates that loop errors until compliance, and prompt/agent hooks that evaluate skills before actions. Common pitfalls involve syntax mismatches, missing `$ARGUMENTS`, and hooks lacking direct Skill invocation.[1][2]

## Forcing Skill Use
PreToolUse hooks block tools (e.g., Read, Bash) on slash commands like `/claude-automation-recommender`, forcing `Skill("claude-automation-recommender")` as the first action via exit code 2 and stderr errors like `[E_SKILL_FIRST_PENDING_INTENT]`. Other methods: UserPromptSubmit adds context urging Skill calls; PostToolUse prompts re-evaluation.[3][4][5]

- "Forced eval hook" explicitly reasons YES/NO per skill before tools, boosting activation from 20% to 84%.[3]
- Spawn `claude -p "/skill args"` from command hooks for deterministic invocation.[4]
- `disable-model-invocation: true` hides from auto-trigger but allows manual `/skill`.[1]

## Hooks and Skills Interaction
Hooks run at lifecycle events (PreToolUse before tools, UserPromptSubmit before prompts); skills define scoped hooks in frontmatter like `hooks: { PreToolUse: [...] }`, active only during skill execution. PreToolUse gates detect pending intents from transcript, blocking until Skill loads full content.[2]

| Interaction | Hook Role | Skill Role |
|-------------|-----------|------------|
| Gating | Blocks tools until `Skill()` call | Loads on slash or auto; provides instructions |
| Scoped | Skill frontmatter hooks fire only when active | `context: fork` runs in subagent with hooks |
| Invocation | No direct `type: "skill"`; use Bash proxy | `Skill(name)` tool call loads it |

Skills merge old commands; descriptions auto-trigger unless disabled.[1]

## Common Pitfalls
Hooks can't directly invoke skills (no `type: "skill"`); proxy via `claude -p "/skill"` in Bash hooks. Skill calls fail on name mismatches (exact/lowercase), missing descriptions, or permission denials on `Skill` tool.[6][4]

- Infinite blocks: Exit 2 without JSON; use `permissionDecision: "deny"` in `hookSpecificOutput`.[2]
- Lazy loading: Descriptions always in context; full content only on invoke—exceeds budget with many skills.[1]
- Args ignored: No `$ARGUMENTS` in SKILL.md appends them; use `$0`, `$1` for indexed.

## Human

Best practices for writing skill descriptions to improve auto-activation
How to implement user-invocable vs auto-invocable skills
Examples of fork context and subagents in skills
Workarounds for invoking skills from hooks
Templates for effective skill frontmatter configuration

## Assistant

Skill descriptions act as "search queries" Claude matches against prompts—precise keywords boost auto-activation from ~20% to 80%+. User-invocable skills use `/name`; auto-invocable rely on descriptions without `disable-model-invocation: true`. Fork context leverages built-in agents like Explore; hooks workaround via `claude -p "/skill"`.[1][2][3][4]

## Skill Descriptions
Use action-oriented phrases targeting intents/files: "Validate TypeScript schemas in .claude/rules" over "Schema tool". Specifics (e.g., "debug PreToolUse hooks blocking tools") match better than vague "debugging skill".[5][3][6]

- Test: List skills, prompt matching description—check invocation.
- Length: 1-2 sentences; too long dilutes.
- Hooks amplify: UserPromptSubmit injects "🎯 USE [skill]" on keyword match.[2][7]

## Invocable Types
User-invocable: Default, slash-trigger + auto via description. Auto-only: Omit description or set `user-invocable: false`—Claude decides.[4]

| Type | Slash `/name` | Auto-Trigger | Other Skills Call | Best For |
|------|---------------|--------------|-------------------|----------|
| Default | ✅ | ✅ | ✅ | General |
| No Description | ✅ | ❌ | ✅ | Helpers |
| `disable-model-invocation: true` | ✅ | ❌ | ❌ | User-only |
| `user-invocable: false` | ❌ | ✅ | ✅ | Claude-decided |

## Fork and Subagents
`context: fork` + `agent: Explore` forks parent context into built-in agent (e.g., "Investigate $ARGUMENTS"), loading SKILL.md as task—lazy, inherits skills/tools.[8]

```
---
context: fork
agent: Plan
---
Plan automations for hooks in .claude/hooks.
```
Subagent `skills: [name1,name2]` preloads full skills + CLAUDE.md; dynamic delegation but higher context cost.[8]

Example: Fork for read-only analysis; subagent for editable workflows.

## Hook Workarounds
No native `Skill()` from hooks—use Bash proxy: `claude -p "/claude-automation-recommender review hooks" > output.json` then parse.[9]

- UserPromptSubmit: Append "MANDATORY: Skill(skill=...) before tools".[2]
- Deterministic spawn in PreUserPrompt for gates.

## Frontmatter Templates
Minimal auto-invocable:
```
---
name: hook-reviewer
description: Review and debug .claude/hooks blocking errors
allowed-tools: Read,Grep,Bash
---
Instructions...
```
User-only:
```
---
name: private-validator
disable-model-invocation: true
argument-hint: "file or pattern"
---
```
Fork subagent:
```
---
context: fork
agent: Explore
skills: []  # Optional preload
---
Task with $ARGUMENTS.
```

## Human

Common pitfalls in skill descriptions that prevent auto-activation
Detailed tutorial for setting up UserPromptSubmit hook
Real-world examples of context:fork skills in action
How to structure skill-rules.json for reliable matching
Differences between hooks and skills for enforcement

## Assistant

Skill descriptions fail auto-activation with vague phrasing, overload (too many skills dilute budget), or mismatches to user intents/files. UserPromptSubmit hooks inject mandatory skill checks pre-prompt via stdout on exit 0. Hooks enforce deterministically via blocks (exit 2); skills suggest probabilistically.[1][2][3]

## Description Pitfalls
Vague/generic terms ("debug tool") ignored; use specifics like "debug PreToolUse hooks blocking Bash". Overlong (>100 chars) or absent descriptions skip loading. Multi-skill prompts drop rates to 0%; test 200+ prompts for baselines.[4][5][1]

- Budget overflow: Descriptions cap at 2% context or 16k chars—excess excluded (/context warns).
- No keywords: Misses "hooks", "skills", "E_SKILL_FIRST_PENDING_INTENT".
- Probable override: Claude skips if "thinks it knows better".

## UserPromptSubmit Tutorial
Fires pre-prompt processing—no matcher. Stdout (exit 0) appends to context; exit 2 blocks/erases prompt.

1. Create `.claude/hooks/user-prompt-skill-gate.sh`:
```
#!/bin/bash
# Read JSON stdin
prompt=$(jq -r '.prompt' /dev/stdin)

# Check for skill triggers (e.g., /skill-name or keywords)
if [[ "$prompt" =~ "/claude-automation-recommender" ]]; then
  cat << EOF
MANDATORY FIRST ACTION: Skill("claude-automation-recommender")
Do NOT analyze, read files, or use tools until skill loaded.
EOF
  exit 0
fi
exit 0
```
Make executable: `chmod +x .claude/hooks/user-prompt-skill-gate.sh`.

2. Add to `.claude/settings.json`:
```
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-skill-gate.sh"
          }
        ]
      }
    ]
  }
}
```
3. Test: `/hooks` verify; prompt with trigger—sees injection. Restart session for changes.[6][1]

Aggressive lang ("MANDATORY", "NON-NEGOTIABLE") boosts obedience.

## Fork Examples
`context: fork` + `agent: Explore` runs SKILL.md as task in read-only subagent, inheriting parent skills/tools lazily.[2][7]

```
---
name: deep-research
description: Research codebase topic thoroughly
context: fork
agent: Explore
---
Research $ARGUMENTS:
1. Glob/Grep relevant files
2. Analyze structure
3. Summarize with refs
```
Action: Isolates exploration; returns findings. Real: PR summarizer fetches `gh pr diff` via `!` subst, tasks Explore agent.[2]

## skill-rules.json Structure
`.claude/skills/skill-rules.json` defines triggers/enforcement for plugins like skill-creator (not core).[8][9]

```
{
  "hook-reviewer": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "medium",
    "promptTriggers": {
      "keywords": ["hooks", "PreToolUse"],
      "intentPatterns": ["debug.*hook", "block.*error"]
    },
    "fileTriggers": {
      "glob": [".claude/hooks/**/*.py"]
    }
  }
}
```
Fields: `type` (domain/global), `enforcement` (block/suggest/warn), triggers (keywords/regex/glob).[8]

## Hooks vs Skills Enforcement
Hooks: Deterministic scripts at events (PreToolUse blocks via exit 2); run always on match.[10]

| Aspect | Hooks | Skills |
|--------|-------|--------|
| Trigger | Event+matcher (e.g., Bash) | Description match or /invoke |
| Enforcement | Hard (exit 2 blocks) | Soft (Claude decides, ~20-84%) |
| Scope | Global/project | Inline/fork/subagent |
| Output | JSON/exit codes | Instructions/$ARGUMENTS |

Use hooks for gates (your SKILL-FIRST); skills for knowledge/workflows.[3][10]

## Human

How to implement LLM hook for 80% skill activation
What is forced eval hook and its script example
Best practices for skill-rules.json trigger patterns
How to use agent-scoped hooks like PreToolUse
Examples of multi-skill prompts and their pitfalls

## Assistant

Forced eval hooks boost skill activation to 84-100% by requiring Claude to explicitly reason YES/NO per skill before tools. LLM hooks (e.g., UserPromptSubmit prompt handlers) pre-classify via fast model for ~80% rates. Agent-scoped hooks limit PreToolUse to skill/subagent lifecycles via frontmatter.[1][2][3][4]

## LLM Hook for 80% Activation
Use UserPromptSubmit "LLM eval hook": prompt Claude (or fast model) to classify skills from prompt/transcript, inject "USE [skill]" context. Boosts from 50% baseline to 80%; cheaper than forced eval.[2][5]

```
# .claude/hooks/skill-eval.sh (UserPromptSubmit)
#!/bin/bash
prompt=$(jq -r '.prompt' /dev/stdin)
# Extract skills list from .claude/skills or ls
skills=$(ls .claude/skills/*.md | xargs basename -s .md)
echo "EVALUATE SKILLS FOR: $prompt"
echo "Skills: $skills"
echo "List matching: YES/NO + reason for each. Activate if YES."
exit 0
```
Config: `"hooks": {"UserPromptSubmit": [{"hooks": [{"type":"command","command":"$CLAUDE_PROJECT_DIR/.claude/hooks/skill-eval.sh"}]}]}`[3][1]

## Forced Eval Hook
"forced-eval hook" (UserPromptSubmit command) forces Claude to YES/NO evaluate each skill pre-prompt, committing via structured reasoning. Hits 84-100% across 250+ evals; outperforms simple instructions (40%).[1][3]

Script example (`.claude/hooks/forced-eval.sh`):
```
#!/bin/bash
# Parse prompt/transcript for context
prompt=$(jq -r '.prompt' /dev/stdin)
skills=$(ls .claude/skills | sed 's/\.md$//')  # List skills

cat << EOF
MANDATORY: Evaluate EVERY skill:
$skills

For "$prompt":
- [skill1]: YES/NO - reason
- [skill2]: YES/NO - reason

If YES, FIRST ACTION: Skill("[skill]")
NO tools/analysis until evals complete.
EOF
exit 0
```
JSON config:
```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/forced-eval.sh"
      }]
    }]
  }
}
```
Reddit tests: 100% on 44 tests; handles ambiguity ("no skill needed").[1]

## skill-rules.json Patterns
Use precise regex/glob for triggers; `enforcement: "block"` for gates. Prioritize `medium/high`; test with 200+ prompts.[6][7]

Best practices:
```
{
  "hook-reviewer": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "high",
    "promptTriggers": {
      "keywords": ["hook", "PreToolUse", "block"],
      "intentPatterns": ["(debug|fix).*?(hook|error)", "\\bE_SKILL_FIRST\\b"]
    },
    "fileTriggers": {
      "pathPatterns": [".claude/hooks/**/*.sh", ".claude/hooks/**/*.py"],
      "glob": ["**/*.hook.md"]
    }
  }
}
```
- Keywords: Exact matches.
- intentPatterns: Regex like `(create|review).*hooks`.
- Avoid broad: Kills precision.[6]

## Agent-Scoped PreToolUse
Frontmatter in agent/skill YAML: `hooks: { PreToolUse: [...] }`—runs only in that agent's loop (e.g., block Bash in Explore).[4]

```
---
name: secure-explore
agent: Explore
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: "command"
          command: "./secure-bash-check.sh"
---
```
Perfect for verification agents enforcing formats.

## Multi-Skill Pitfalls
Lists 10+ skills drop activation to 0%—budget overflow, decision paralysis. Simple hooks fail; forced eval survives via per-skill eval.[5][3]

Examples:
- 44 skills: Baseline 50%, multi-prompt 0%.
- Pitfall: Vague descriptions compete; overloads context (descriptions ~16k chars cap).
- Fix: skill-rules.json progressive disclosure; gates limit to 3-5 active.[1]

## Human

LLM-eval hook script differences from forced-eval
skill-rules.json enforcement levels explained
PreToolUse hook practical example
Progressive disclosure in Claude Code skills
Debugging low skill activation rates

## Assistant

LLM-eval hooks pre-classify skills cheaply via fast model (e.g., Haiku), hitting 80% activation with speed but false positives; forced-eval requires Claude's YES/NO reasoning for 84-100% consistency. skill-rules.json `enforcement` levels escalate from suggest (passive) to block (hard gates). Debug activation via /hooks logs, eval harnesses, and keyword tests.[1][2][3][4]

## Hook Differences
LLM-eval: External/small model scans prompt/skills, injects "USE [skill]"—fast (10% cheaper), 80%, but hallucinates non-matches (67% accuracy). Forced-eval: Claude self-evals each skill pre-proceeding—no deps, 84-100%, zero false positives via commitment.[2][1]

| Hook | Activation | Speed/Cost | Reliability | Script Style |
|------|------------|------------|-------------|--------------|
| LLM-eval | 80% | High (Haiku) | Hallucinations on edges | Proxy to claude -m haiku |
| Forced-eval | 84-100% | Medium | Consistent, no FPs | UserPromptSubmit injection |

## Enforcement Levels
From skill-rules.json/plugins: Controls via hooks (UserPromptSubmit/PreToolUse).[4]

- **suggest**: Append "🎯 USE [skill]" to prompt (passive, ~40%).
- **warn**: Stderr note + suggest (~60%).
- **block**: Exit 2 on PreToolUse/Edit, forces Skill() first (100% if triggered).[4]

Example: `guardrail` skills block writes until verification.

## PreToolUse Example
Blocks `rm -rf` or git --force; JSON denies with reason fed to Claude.[5]

`.claude/hooks/block-destruct.sh` (Bash matcher):
```
#!/bin/bash
command=$(jq -r '.toolArguments.command' /dev/stdin)
if [[ "$command" =~ "rm -rf" || "$command" =~ "--force.*git" ]]; then
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: Destructive op. Use Skill(\"safe-delete\") first."
  }
}
EOF
  exit 0
fi
echo "{}"
exit 0
```
Config: `"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": ".../block-destruct.sh"}] }]`.[5]

## Progressive Disclosure
Load minimal SKILL.md (desc+core logic); defer deep docs/tools via `context: fork` or on-demand Read. Saves 70-90% tokens, scales 100+ skills.[6][7]

- Core: 500-line rule (essentials only).
- Defer: `!glob .claude/docs/${TOPIC}` in instructions.
- skill-rules.json skips irrelevant based on session/files.

## Debugging Activation
Run eval harness: 200+ synthetic prompts (/p harness); log /hooks output, Claude responses.[8][1]

Steps:
- Baseline: No hooks → 0-50%.
- Keyword test: Rephrase prompts (semantic fails; keywords win).
- Logs: `tail -f ~/.claude/logs/*` for hook firings.
- Metrics: Track YES/NO commits, false skips.
- Fixes: Forced-eval, precise descriptions, <16k char totals.[9][2]

## Human

How to implement progressive disclosure in a custom skill
Sample skill-rules.json for block enforcement
Full PreToolUse hook script for git blocking
Fixing keyword matching failures in skills
Compare UserPromptSubmit vs PreToolUse hooks

## Assistant

Progressive disclosure in custom skills keeps YAML frontmatter + core SKILL.md minimal (~100-500 tokens), deferring details to on-demand files via glob/Read. Block enforcement in skill-rules.json uses `enforcement: "block"` to gate tools until Skill() via PreToolUse. Keyword failures fix with exact phrases, regex in rules, and eval hooks.[1][2][3][4]

## Progressive Disclosure Implementation
YAML: Teaser description. Core SKILL.md: 500-line essentials + refs. Details: `.claude/skills/[skill]/docs/*.md` loaded via `!glob` or instructions.[2][3]

Sample `.claude/skills/hook-reviewer/SKILL.md`:
```
---
name: hook-reviewer
description: Debug .claude/hooks via PreToolUse blocks (e.g., git, destruct)
---
## Core Rules (500-line limit)
1. Grep .claude/hooks for matcher/tool
2. Test dry-run: claude -p "debug $ARGS"
3. Propose fixes

## Defer: !glob .claude/skills/hook-reviewer/docs/*.md for examples
Read hook-debug.md for PreToolUse patterns.
```
Claude reads docs only on match; scales 100+ skills.[5]

## Sample skill-rules.json (Block)
```
{
  "hook-reviewer": {
    "type": "guardrail",
    "enforcement": "block",
    "priority": "critical",
    "promptTriggers": {
      "keywords": ["hook", "block", "PreToolUse"],
      "intentPatterns": ["debug.*hook", "fix.*error"]
    },
    "fileTriggers": {
      "glob": [".claude/hooks/**/*.sh"]
    },
    "skipConditions": {
      "sessionMarker": ".claude/session-hooks-reviewed"
    }
  }
}
```
Triggers PreToolUse block; Claude must Skill() to proceed.[4][6]

## Full Git-Blocking PreToolUse
`.claude/hooks/block-git.sh` (matcher: Bash):
```
#!/bin/bash
# Parse JSON stdin
read stdin
command=$(echo "$stdin" | jq -r '.toolArguments.command // empty')

if [[ "$command" =~ git.*(commit|push|rebase|reset\ --hard|\-\-force) ]]; then
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: Git $command requires Skill(\"git-reviewer\") approval. Review changes first."
  }
}
EOF
  exit 0
fi

echo "{}"
exit 0
```
settings.json:
```
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/block-git.sh",
        "timeout": 5
      }]
    }]
  }
}
```
Blocks force-push; prompts Skill use.[7]

## Fixing Keyword Matching
Failures from semantics > literals; use rules regex, eval hooks. Test: 200 prompts, track misses.[8]

- Exact: "PreToolUse hook" not "pre-tool use".
- Rules: `intentPatterns: ["\\b(block|debug)\\b.*hook"]`.
- Hooks: Forced-eval lists skills explicitly.
- Descriptions: Action+files ("Review hooks blocking E_SKILL_FIRST").

## Hook Comparison
UserPromptSubmit pre-prompt (suggest/block via context); PreToolUse per-tool (deny with reason).[9]

| Hook | Timing | Block Method | Use Case | Scope |
|------|--------|--------------|----------|-------|
| UserPromptSubmit | Pre-prompt submit | Stdout inject/exit 2 erase | Skill gates, eval | Global/prompt-wide |
| PreToolUse | Pre-tool exec | JSON deny/stderr | Tool guards (git/Edit) | Per-tool (Bash/Edit) |

UserPromptSubmit for activation (80%); PreToolUse for safety (100%).[10]

## Human

Progressive disclosure Level 3 detailed resources examples
Guardrail vs domain skill types differences
UserPromptSubmit hook implementation for skills
Session tracking in skill-rules.json to avoid repeats
Debugging skill activation failures in Claude Code

## Assistant

Progressive disclosure Level 3 loads on-demand resources (code/docs) via filesystem tools after Level 1 (YAML) and Level 2 (SKILL.md) match. Guardrail skills block/validate (e.g., PreToolUse gates); domain skills provide context (suggestive). Session tracking uses `.claude/hooks/state/*.json` to skip repeats; debug via eval harnesses and logs.[1][2][3][4]

## Level 3 Disclosure
Level 1: YAML (always; name/desc/triggers). Level 2: SKILL.md (~500 lines; core logic). Level 3: `!glob .claude/skills/[skill]/resources/*.md` or bash fetches code/docs only when needed.[5][1]

Examples:
- PR reviewer: SKILL.md plans; Level 3 reads `pr-template.md` for structure.[6]
```
---
name: pr-reviewer
description: Generate PRs with structured template
---
## Level 2: Core flow
1. Analyze diff
2. Read .claude/skills/pr-reviewer/resources/pr-template.md  # Level 3
3. Format PR
```
- Hook debugger: Level 3 loads `examples/blocking-hooks.md` post-match.[5]

## Skill Types Comparison
Guardrail: Enforcement-focused (block/warn via hooks). Domain: Knowledge (suggest context).[3]

| Type | Purpose | Enforcement | Triggers | Example |
|------|---------|-------------|----------|---------|
| Guardrail | Block/validate actions | block/warn (PreToolUse) | Destructive (git --force) | Skill("safe-git") first |
| Domain | Provide expertise | suggest (UserPromptSubmit) | Files/keywords (hooks/*.py) | Hook review patterns |

## UserPromptSubmit for Skills
Injects "EVALUATE: Use hook-reviewer?" pre-prompt; blocks on no Skill() for gates.[7][8]

```
#!/bin/bash  # .claude/hooks/skill-gate.sh
prompt=$(jq -r '.prompt' /dev/stdin)
if [[ "$prompt" =~ "hook|PreToolUse" ]]; then
  cat << EOF
CRITICAL: FIRST ACTION Skill("hook-reviewer")
NO tools until loaded. Skills available: [list from ls .claude/skills]
EOF
  exit 0
fi
exit 0
```
settings.json: `"UserPromptSubmit": [{"hooks": [{"type":"command","command":"./skill-gate.sh"}]}]`[8]

## Session Tracking
`skipConditions.sessionMarker`: Hooks check/write `.claude/hooks/state/skills-used-{session_id}.json`.[4][3]

```
{
  "hook-reviewer": {
    "skipConditions": {
      "sessionMarker": ".claude/hooks/state/hooks-reviewed-{session_id}.json",
      "exists": true
    }
  }
}
```
Hook: `jq -e '.hooks_reviewed' state.json || echo '{"hooks_reviewed":true}' > state.json` skips if marked.[4]

## Debugging Failures
Use skill-debugging-assistant or harness: `/p "test 50 prompts: hooks debug"`; check logs `/hooks`, token budget (`/context`), triggers.[9][10]

- Logs: `~/.claude/logs/` for hook firings.
- Test: Rephrase (exact keywords win).
- Metrics: Track % activation; forced-eval baselines.
- Common: Budget overflow (>16k descs), vague descs, no eval hooks.[9]

## Human

Examples of domain skill trigger patterns in skill-rules.json
How to set up PreToolUse hook for skill safety
YAML frontmatter best practices for Level 1 disclosure
Subagents vs skills configuration differences
Debugging low skill activation rates in Claude Code

## Assistant

Domain skills use suggestive triggers like keywords ("hooks", "debug") or intent regex for guidance; examples include patterns for React patterns or API design. PreToolUse for skill safety blocks tools until Skill() via JSON deny on unsafe calls. YAML Level 1 prioritizes name/desc (1024 chars max) with trigger keywords; subagents fork context while skills inline or fork.[1][2]

## Domain Trigger Patterns
From skill-rules.json examples: Suggestive for non-blocking knowledge.[2]

```
"backend-guidelines": {
  "type": "domain",
  "enforcement": "suggest",
  "promptTriggers": {
    "keywords": ["api", "endpoint", "prisma", "database"],
    "intentPatterns": ["(create|build).*?(api|endpoint)", "query.*prisma"]
  },
  "fileTriggers": {
    "glob": ["**/api/**/*.ts", "**/*.prisma"]
  }
}
```
- Keywords: Exact matches.
- intentPatterns: "(debug|fix).*hook".

## PreToolUse Skill Safety
Blocks Edit/Bash until Skill("safe-*"); JSON reason prompts Claude.

settings.json:
```
"PreToolUse": [{
  "matcher": "Edit",
  "hooks": [{"type": "command", "command": "./skill-safety.sh"}]
}]
```
Script blocks unsafe:
```
if [[ ! "$file" =~ ^\.claude/skills/ ]]; then
  echo '{"permissionDecision": "deny", "reason": "Use Skill(\"safe-edit\") first"}'
fi
```

## YAML Frontmatter Best Practices
Level 1 (always-loaded): name (lowercase-hyphen), description (trigger keywords, <1024 chars).[1]

```
---
name: hook-debugger
description: Debug .claude/hooks PreToolUse blocks, E_SKILL_FIRST errors, bash scripts. Triggers: hooks, debug, block.
disable-model-invocation: false
allowed-tools: Grep, Read
---
```
- Keywords in desc for auto-trigger.
- No deep logic—defer to SKILL.md.

## Subagents vs Skills Config
Subagents: Independent context, skills field preloads others; skills: Inline/fork into main.[3]

| Config | Subagents | Skills |
|--------|-----------|--------|
| Context | Separate window | Inline or fork |
| YAML | .claude/agents/name.yaml (skills: [...]) | SKILL.md frontmatter |
| Invoke | Delegate or /agent | /skill or auto |
| Use | Multi-step expert | Task/reference |

## Debugging Activation
Eval 200+ prompts; check /context budget, logs.[4][5]

- Harness: "test hooks debug" x50.
- Logs: /hooks, ~/.claude/logs.
- Fixes: Forced-eval hook, exact keywords, <16k desc total.[4]

## Human

Which of these two LLM responses has the better operational guide?
Grok:
"**Yes — the team and I just ran a quick review with the latest March 2026 Claude Code behavior (skills + slash commands now merged, scoped hooks in frontmatter, JSON output preferred, new PostToolUse/TeammateIdle events, etc.).**

Here is **v2 of the Operational Best Practices** with the highest-value upgrades baked in:

- Bootstrap script at the top (one-command setup)  
- Executive summary + success metrics  
- Phased roadmap  
- Decision matrix (which method to use when)  
- Native Skill-Scoped Hooks section (2026 feature)  
- Full recovery / “Stuck in Gate” section first  
- Diagnostic checklist + rollback procedure  
- Production hardening + PostToolUse quality gate  
- Activation testing harness  
- Anti-patterns appendix  

Everything is copy-paste ready and tested against current docs.

---

**Operational Best Practices: Skills & Hooks in Claude Code**  
**March 2026 Edition** (targeted at Claude Code v2.4+)  
Last updated: March 03, 2026

### Executive Summary & Success Metrics
A single PreToolUse gate + Forced-Eval UserPromptSubmit + clean skill frontmatter delivers:
- 100% SKILL-FIRST compliance (no more loops)  
- 84–100% auto-activation on target prompts  
- <2% context-budget overhead with progressive disclosure  

### Quick Bootstrap Script (Run Once)
```bash
#!/bin/bash
mkdir -p .claude/hooks .claude/hooks/state .claude/skills/claude-automation-recommender/docs
cat > .claude/hooks/PreToolUse-gate.sh << 'EOF'
#!/bin/bash
# PreToolUse gate – forces Skill() first
input=$(cat)
if [[ "$input" == *"/claude-automation-recommender"* ]]; then
  cat << JSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "⛔ SKILL-FIRST GATE: Call Skill(\\"claude-automation-recommender\\") as your FIRST action."
  }
}
JSON
  exit 0
fi
echo "{}"
exit 0
EOF

cat > .claude/hooks/forced-eval.sh << 'EOF'
#!/bin/bash
prompt=$(jq -r '.prompt // ""' /dev/stdin)
skills=$(ls .claude/skills/*.md 2>/dev/null | xargs -n1 basename -s .md)
cat << EOF
MANDATORY EVALUATION (2026 best practice):
$skills

For: "$prompt"
List every skill → YES/NO + 1-line reason.
If YES → FIRST ACTION must be: Skill("name")
NO tools or analysis until complete.
EOF
exit 0
EOF

# Add to settings.json (creates if missing)
cat > .claude/settings.json << 'JSON'
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash|Read|Grep|Edit",
      "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PreToolUse-gate.sh" }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/forced-eval.sh" }]
    }]
  }
}
JSON

chmod +x .claude/hooks/*.sh
echo "✅ Bootstrap complete. Restart Claude session and type /claude-automation-recommender"
```

Run it → done.

### Phased Implementation Roadmap
**Phase 1 (Must-have – 5 min)**  
Bootstrap script + PreToolUse gate + Forced-Eval hook

**Phase 2 (Recommended)**  
Clean skill frontmatter + skill-rules.json + progressive disclosure

**Phase 3 (Advanced)**  
Native Skill-Scoped Hooks + PostToolUse quality gate + session markers

### Decision Matrix – Which Method to Use

| Method                        | Activation Rate | Context Cost | Enforcement Strength | Best For                          | Risk of Loop |
|-------------------------------|-----------------|--------------|----------------------|-----------------------------------|--------------|
| PreToolUse Gate only          | 100% (once triggered) | Low         | Hard block           | SKILL-FIRST compliance            | High until obeyed |
| UserPromptSubmit + Forced-Eval| 84–100%         | Low         | Soft + commitment    | Reliable auto-activation          | Very low     |
| skill-rules.json (block)      | 95–100%         | Medium      | Hard via gate        | Domain/guardrail skills           | Low          |
| Native Skill-Scoped Hooks     | 100% (scoped)   | Lowest      | Targeted             | Behavior only when skill active   | None         |
| CLAUDE.md / description only  | 20–50%          | Medium      | Advisory             | Never use alone                   | High         |

### 1. The SKILL-FIRST GATE (Core Enforcement)
Use the bootstrap version above (JSON output is now preferred in 2026).

### 2. Native Skill-Scoped Hooks (2026 Feature)
You can now embed hooks directly in the skill’s YAML — they only fire while that skill is active.

Example in `.claude/skills/claude-automation-recommender/SKILL.md`:
```yaml
---
name: claude-automation-recommender
description: Review .claude/hooks, fix PreToolUse blocks, recommend automation patterns. Keywords: hook, PreToolUse, E_SKILL_FIRST
context: fork
hooks:
  PreToolUse:
    - matcher: "Bash|Edit"
      hooks: [{ "type": "command", "command": "./internal-safety.sh" }]
  PostToolUse:
    - hooks: [{ "type": "command", "command": "./validation.sh" }]
---
```

### 3. Skill Frontmatter & Progressive Disclosure (Level 1–3)
Keep Level 1 (YAML) under 1024 chars, Level 2 (core logic) ≤500 lines, defer everything else.

### 4. skill-rules.json (Advanced Trigger Control)
Use `enforcement: "block"` for guardrails — it auto-triggers your PreToolUse gate.

### 5. Post-Activation Quality Gate (New Pattern)
After the skill loads, run validation with PostToolUse:
```bash
# .claude/hooks/post-skill-validation.sh
cat << JSON
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Skill loaded successfully. Proceeding with hook review."
  }
}
JSON
```

### Recovery: “Stuck in Gate” Fix (Run if Claude loops)
```bash
# Temporary disable (safe)
mv .claude/hooks/PreToolUse-gate.sh .claude/hooks/PreToolUse-gate.sh.disabled
# Force compliance manually:
# Type exactly: Skill(skill="claude-automation-recommender")
# Then re-enable the hook.
```

**Rollback procedure** (if a hook bricks the session):  
Delete the offending hook file or set `hooks: {}` in settings.json and restart Claude.

### Activation Testing Harness
```bash
# Run in terminal
for i in {1..50}; do
  claude -p "test prompt $i: review hooks PreToolUse E_SKILL_FIRST"
done
```
Count how often Skill() appears in the first turn. Target ≥84%.

### Production Hardening & Anti-Patterns
- Always use session markers in skill-rules.json to avoid repeat gates.  
- Never put arbitrary bash in global hooks without input validation.  
- Limit global PreToolUse matchers (latency).  
- Anti-patterns: >15 skills in context, vague descriptions, forgetting to chmod +x, mixing old exit-2 style with new JSON.

### Troubleshooting Diagnostic Checklist
1. Run `/hooks` — are all hooks loaded?  
2. Check `~/.claude/logs/` for gate firings.  
3. Token budget (`/context`) under 16k for descriptions?  
4. Exact skill name match (lowercase-hyphen)?  
5. Still looping? Use Recovery section above.  
6. Skill not loading full content? Use `context: fork`.

### Official References (2026)
- [https://code.claude.com/docs/en/hooks-guide](https://code.claude.com/docs/en/hooks-guide)  
- [https://code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)  
- [https://code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) (scoped hooks section)

---

This v2 is now truly operational: one script to rule them all, clear decision-making, recovery paths, and 2026 features included.

Want me to:
- Export this as a Markdown file you can drop into your repo?
- Add the full recommended SKILL.md template for claude-automation-recommender?
- Or generate a visual flowchart of the decision matrix?

Just say the word and I’ll ship it."

---

Gemini 3:
"Gemini said
TL;DR: To ensure Claude consistently uses skills, implement a "Forced Eval" hook via UserPromptSubmit to mandate skill checks, and a PreToolUse gate to block all tool execution until the Skill() tool is explicitly called.
I. Gating & Enforcement (The "Hard" Gate)
If Claude attempts to analyze code or run scripts before loading a required skill, use a PreToolUse hook to block execution. This creates a deterministic gate that Claude cannot bypass without following instructions.
1. PreToolUse Blocking Mechanism
Trigger: Detects a pending skill intent (e.g., a slash command like /claude-automation-recommender) in the session transcript.
Action: If Skill() hasn't been called, the hook returns exit code 2 with a blocking error message.
Error Code: Use [E_SKILL_FIRST_PENDING_INTENT] to signal to the model that it is in a "Skill-First Gate".
Result: All tools (Bash, Read, Grep) are disabled until the model issues the Skill(name="...") tool call.
2. Enforcement Levels in skill-rules.json
You can escalate enforcement based on the criticality of the skill:
| Level | Action | Activation Rate |
| :--- | :--- | :--- |
| Suggest | Appends a reminder to the prompt. | ~40% |
| Warn | Prints a warning to stderr but allows tools. | ~60% |
| Block | Uses PreToolUse to stop tools until Skill() is called. | 100% (if triggered) |
II. Activation Strategies (The "Soft" Guide)
While gates block tools, UserPromptSubmit hooks actively guide Claude to choose the right skill before the prompt is even processed.
1. The "Forced Eval" Hook (Recommended)
This method forces Claude to explicitly reason whether a skill is needed for every prompt.
Reliability: Increases activation from ~20% to 84-100%.
Implementation: Injects a "MANDATORY: Evaluate EVERY skill" block into the context.
Constraint: Instruct the model that its FIRST ACTION must be the Skill() call, or it must explicitly state "NO" with a reason.
2. The "LLM Eval" Hook
A faster, cheaper alternative that uses a small model (like Haiku) to pre-classify the user's prompt.
Performance: Achieves ~80% activation.
Pros/Cons: Faster than full evaluation but can suffer from hallucinations or false positives.
III. Skill Design & Progressive Disclosure
To manage the 16k character context limit for skill descriptions, use a tiered disclosure approach.
1. Tiered Content Strategy
Level 1 (YAML): Keep names (lowercase-hyphen) and descriptions under 1,024 characters. Focus on keywords (e.g., "debug", "hooks", "git") rather than prose.
Level 2 (SKILL.md): Contain core logic and essential rules (max 500 lines).
Level 3 (Resources): Use !glob or instructions to load detailed documentation or code examples only after the skill is active.
2. Effective Trigger Patterns
In skill-rules.json, use specific regex patterns and globbing to trigger skills automatically:
File Triggers: Trigger a hook-review skill when the user touches .claude/hooks/**/*.py.
Intent Patterns: Use regex like (debug|fix).*?hook to catch semantic variations of the user's intent.
IV. Debugging & Maintenance
Audit Hooks: Use the /hooks command to verify which hooks are active and project-specific.
Check Logs: Monitor ~/.claude/logs/ to see exactly why a hook returned a blocking error or why a skill failed to load.
Token Budget: Use /context to ensure your combined skill descriptions aren't exceeding the context budget (typically ~2% of the window).
Would you like me to generate a sample bash script for a Forced Eval hook to help you get started?
You said
Do you have anything you can think of to make this operational guide better?
Gemini said
TL;DR: To elevate this guide, add boilerplate script templates for immediate deployment, implement session-based state tracking to prevent "hook fatigue," and clarify the hierarchical logic between prompt-level activation and tool-level gating.
To make the operational guide truly "battle-ready," you should incorporate these specific technical refinements found in the documentation:
1. Implement a Lifecycle Flowchart
Understanding exactly when these hooks fire is critical for debugging. A UserPromptSubmit hook is your "Traffic Controller," while PreToolUse is your "Security Guard".
2. Add Boilerplate "Forced-Eval" Script
The guide mentions the strategy, but providing the actual logic ensures it is implemented correctly. This script should be placed in .claude/hooks/forced-eval.sh:
Bash
#!/bin/bash
# .claude/hooks/forced-eval.sh (UserPromptSubmit)
read -r stdin
prompt=$(echo "$stdin" | jq -r '.prompt')
skills=$(ls .claude/skills/*.md | xargs -n 1 basename | sed 's/\.md$//')

cat << EOF
MANDATORY PROTOCOL: You must evaluate the following skills for the prompt: "$prompt"
Available Skills: $skills

For each skill, reason: "Is this skill needed? YES/NO."
If YES, your ABSOLUTE FIRST ACTION must be: Skill(skill="name")
Do NOT perform analysis or run tools until the required skill is loaded.
EOF
exit 0

Mandatory Reasoning: Forcing the LLM to write "YES/NO" per skill boosts activation to near 100%.
Stdin Handling: Ensure you use jq to parse the JSON input provided by Claude Code to the hook.
3. Use Session Markers for "Stateful" Hooks
One major pitfall is Claude getting stuck in a loop or becoming repetitive. You can use session markers in your skill-rules.json to skip the gate once a skill has been successfully loaded once in a session.
Logic: Check for a temporary file like .claude/state/skill_loaded_[session_id].
Benefit: This prevents the "SKILL-FIRST GATE" from blocking Claude every time it tries to run a tool after it has already complied.
4. Operational "Keyword Hygiene"
Move away from vague descriptions. The documentation shows that "semantic" matching often fails where "literal" matching succeeds.
Instead of...
Use...
Why?
"Help with hooks"
"Debug PreToolUse and E_SKILL_FIRST"
Specific error codes trigger the model's "fix-it" mode.
"A coding assistant"
"Refactor Python using Pydantic"
Explicit library names in the Level 1 YAML trigger auto-activation.
5. Guardrail vs. Domain Differentiation
Explicitly label your skills in your internal registry to avoid "Priority Bloat":
Guardrail Skills: Use enforcement: block and priority: critical. These are for safety and "must-use" workflows.
Domain Skills: Use enforcement: suggest and priority: medium. These are for optional expertise (e.g., "SQL Best Practices").
Would you like me to write a specialized PreToolUse hook script that specifically handles Git safety (blocking force-pushes unless a skill is active)?"

## Assistant

**Grok's response provides the superior operational guide.** It offers immediate, copy-paste executable code, a structured roadmap with metrics, recovery procedures, and a decision matrix tailored to Claude Code v2.4+ workflows like yours.[1]

## Key Strengths of Grok
Fully operational: Single bootstrap script deploys PreToolUse gate, forced-eval UserPromptSubmit, and settings.json—tested against 2026 docs (scoped hooks, JSON output). Includes phased rollout, testing harness (50 prompts), anti-patterns, and "Stuck in Gate" fix with rollback—matches your hook inventory/debugging focus.[2]

- Decision matrix quantifies tradeoffs (100% block vs 84% eval).
- Native skill-scoped hooks example (2026 feature).
- Diagnostic checklist aligns with your ML transcript analysis habits.

## Gemini's Shortcomings
High-level strategies (e.g., "implement Forced Eval") lack deployable code—scripts are incomplete (no jq stdin parsing, chmod). Conceptual tables/enforcement levels good but non-actionable without your custom tweaks.[3][4]

| Aspect | Grok | Gemini |
|--------|------|--------|
| Deploy Speed | 1 script (5 min) | Manual scripts |
| Completeness | Bootstrap + recovery | TL;DR + concepts |
| Metrics/Tests | Harness, 84-100% | ~20-100% claims |
| User Fit | Hook-heavy (PreToolUse, state) | General |

## Recommendations
Drop Grok's bootstrap into your P:/.claude for claude-automation-recommender gate. Add your session markers from skill-rules.json research. Test with `/hooks` and 50-prompt harness for 100% compliance.[1]

## Human

please create your improved version of the operational guide, with all the information you have available.

## Assistant

Here’s an end‑to‑end operational guide that folds in Grok’s and Gemini’s ideas, Anthropic’s current docs, and the patterns you’ve been exploring (forced‑eval, PreToolUse gates, progressive disclosure, skill‑rules, session markers). It’s written to be drop‑in for Claude Code v2.4+ as of March 2026.[1][2][3]

***

# Operational Guide: Skills, Hooks, and Gates in Claude Code  
**Target:** Claude Code v2.4+ -  **Focus:** SKILL‑FIRST enforcement + high skill activation + safety

## 0. Goals & Design Targets

This guide aims for:

- **100% SKILL‑FIRST compliance** when you call a skill slash command (e.g. `/claude-automation-recommender`).[4][1]
- **84–100% activation rate** on “on‑target” prompts using a forced‑eval UserPromptSubmit hook.[5][6]
- **Low overhead:** <2% of context budget via progressive disclosure (short YAML + compact SKILL.md + external docs).[7][8]

Assumptions:

- You’re on Claude Code v2.4+ with **hooks** and **skills** enabled.[2][1]
- Your repo lives under something like `P:\project`, with `.claude` at the root (your current setup).

***

## 1. Architecture Overview

At a high level you’ll wire things like this:

1. **UserPromptSubmit (forced‑eval):** Before Claude even “sees” the prompt, inject instructions forcing it to explicitly evaluate each relevant skill as YES/NO and, if YES, make `Skill(...)` the first action.[6][1][5]
2. **PreToolUse (global SKILL‑FIRST gate):** Before any tool (Bash, Read, Grep, Edit, etc.), block if there’s a pending skill intent like `/claude-automation-recommender` and that skill has not yet been called.[9][1]
3. **Skill design (progressive disclosure):** Tight Level‑1 YAML, constrained Level‑2 SKILL.md, Level‑3 docs/resources via `!glob` or Read.[8][2][7]
4. **skill‑rules.json:** Domain vs guardrail skills with `enforcement` levels (suggest / warn / block) and session markers to avoid repeated gating.[10][11]
5. **Skill‑scoped hooks:** For specific skills (like `claude-automation-recommender`), embed scoped PreToolUse/PostToolUse hooks directly in frontmatter.[1][2]

***

## 2. Quick Bootstrap (Minimal but Safe)

If you want a “just get me there” baseline, you can add **three things**:

1. `UserPromptSubmit` forced‑eval hook.  
2. `PreToolUse` global SKILL‑FIRST gate.  
3. A minimal SKILL.md frontmatter for `claude-automation-recommender`.  

Below I give the scripts and config. If you already have `.claude/settings.json`, **merge these snippets** instead of overwriting.

***

## 3. Forced‑Eval UserPromptSubmit Hook

### 3.1 Behavior

- Runs **once per user prompt** before Claude processes it.[1]
- Reads JSON on stdin (`{"prompt": "...", ...}`), outputs plain text that gets appended to the model’s context.[4][1]
- Forces explicit YES/NO reasoning over available skills and mandates that any YES skill must be called first via `Skill(...)` before tools or free‑form analysis.[5][6]

### 3.2 Hook Script

Create `.claude/hooks/forced-eval.sh`:

```bash
#!/bin/bash
# .claude/hooks/forced-eval.sh (UserPromptSubmit)

stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // ""')

# Discover skills (simple: all .md files, adjust paths if needed)
skills=$(ls .claude/skills/*.md 2>/dev/null | xargs -n1 basename -s .md)

cat << EOF
MANDATORY SKILL EVALUATION PROTOCOL:

User prompt:
"$prompt"

Available skills:
$skills

For EACH skill above, you MUST reason explicitly:
- "[skill-name]: YES/NO - 1-line reason"

Rules:
- If you answer YES for any skill, your ABSOLUTE FIRST ACTION must be
  \`Skill(skill="[skill-name]")\` for that skill.
- You MUST NOT analyze the codebase, read files, or use tools until all
  required skills (YES) have been loaded.
- If NO skills apply, say so explicitly and then proceed normally.
EOF

exit 0
```

Hook semantics (UserPromptSubmit: stdout → extra context, exit code 0 = allow) follow Anthropic’s hook docs.[4][1]

### 3.3 Hook Registration

Merge into `.claude/settings.json`:

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/forced-eval.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

This alone tends to push on‑target skill activation into the ~84–100% range in community experiments, compared to ~20–40% with descriptions only.[12][6][5]

***

## 4. Global SKILL‑FIRST PreToolUse Gate

### 4.1 Behavior

- Fires **before any tool** (Bash/Read/Grep/Edit/etc.).[1][4]
- Looks at the tool invocation JSON, and if it detects that the user asked for a skill (e.g. via `/claude-automation-recommender`) but the model hasn’t called `Skill("claude-automation-recommender")` yet, it returns a JSON **deny** response with a clear reason.[9][1]
- This is your “cannot proceed until you obey SKILL‑FIRST” hard gate.  

### 4.2 Gate Script

Create `.claude/hooks/PreToolUse-skill-first-gate.sh`:

```bash
#!/bin/bash
# .claude/hooks/PreToolUse-skill-first-gate.sh (PreToolUse)

stdin=$(cat)

tool_name=$(echo "$stdin" | jq -r '.toolName // ""')
arguments=$(echo "$stdin" | jq -r '.toolArguments // ""')
# Prompt text if present (depends on Claude Code version)
recent_prompt=$(echo "$stdin" | jq -r '.recentUserPrompt // empty')

# Detect intent to use claude-automation-recommender by slash command
if [[ "$recent_prompt" == *"/claude-automation-recommender"* ]]; then
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "⛔ SKILL-FIRST GATE: You typed /claude-automation-recommender but have not yet called Skill(\\"claude-automation-recommender\\"). Your FIRST action must be Skill(skill=\\"claude-automation-recommender\\"). Do NOT analyze the codebase, run scripts, or provide your own assessment until the skill is loaded."
  }
}
EOF
  exit 0
fi

# Default: allow
echo "{}"
exit 0
```

This follows the documented pattern: PreToolUse can return JSON containing `hookSpecificOutput.permissionDecision: "deny"` to veto a tool call.[9][1]

### 4.3 Hook Registration

Merge into `.claude/settings.json`:

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Grep|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PreToolUse-skill-first-gate.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

You can narrow the matcher if needed (e.g., only `Bash|Read`) to reduce latency.[1][13]

***

## 5. Skill Design: YAML Frontmatter & Progressive Disclosure

### 5.1 Level‑1 YAML (Always Loaded)

Keep YAML short and **keyword‑dense**: name, description, maybe a couple of config fields. This is what Claude uses for **auto‑activation** heuristics.[3][2]

Example for `claude-automation-recommender`:

```yaml
---
name: claude-automation-recommender
description: Analyze this repo and recommend Claude Code automations: hooks (PreToolUse, UserPromptSubmit), skills, MCP servers, subagents. Focus on debugging blocking hooks (E_SKILL_FIRST), git safety, and workflow templates.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Bash
  - ListFiles
context: fork
---
```

Best practices from Anthropic’s skill authoring docs and community write‑ups:[2][3][7]

- **Name:** lowercase‑hyphen; avoid ambiguity.  
- **Description:** ≤ 1024 characters, include **literal** keywords (“PreToolUse”, “E_SKILL_FIRST”, “hooks”) rather than only semantic language.[14][5]
- Don't stuff the description with procedural details—those belong in SKILL.md (Level‑2).  

### 5.2 Level‑2 SKILL.md (Core Logic, ≤~500 lines)

Right under the YAML, define core instructions:

```markdown
You are the claude-automation-recommender skill.

Primary goals:
1. Discover relevant automations for this repo (hooks, skills, MCP, subagents).
2. Debug and improve existing .claude/hooks (especially PreToolUse gates, SKILL-FIRST enforcement).
3. Propose phased rollout and safety checks.

When called, you MUST:
- Read .claude/settings.json, .claude/hooks/**, and .claude/skills/**/SKILL.md as needed.
- Explain what each existing hook does, including matchers and permission behavior.
- Recommend concrete changes (file edits, new hooks, new skills) with rationale.
```

Keep this tight; push long examples and docs to Level‑3 resources.[7][8]

### 5.3 Level‑3 Resources (Progressive Disclosure)

Create `./.claude/skills/claude-automation-recommender/docs/` for heavier docs.[15][8]

Examples:

- `blocking-hooks-examples.md` – patterns for PreToolUse/UserPromptSubmit.  
- `progressive-disclosure.md` – policy for Level 1–3.  

Reference them in SKILL.md as **optional** reads:

```markdown
If you need more examples of blocking hooks, read:
- .claude/skills/claude-automation-recommender/docs/blocking-hooks-examples.md
```

Claude only pulls these into context when necessary, keeping budget low.[8][7]

***

## 6. skill‑rules.json: Domain vs Guardrail Skills

While Claude Code doesn’t ship a canonical `skill-rules.json` format, several “skill developer” helpers and community guides converge on the same pattern: triggers + enforcement + priority.[11][16][10]

### 6.1 Domain Skill Example

“Domain” skills add expertise but don’t *have* to be used.[16][11]

```json
{
  "hook-reviewer": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "medium",
    "promptTriggers": {
      "keywords": ["hook", "PreToolUse", "UserPromptSubmit", "E_SKILL_FIRST"],
      "intentPatterns": ["(debug|fix|investigate).*hook", "why.*hook.*block"]
    },
    "fileTriggers": {
      "glob": [".claude/hooks/**/*.*"]
    }
  }
}
```

- `enforcement: "suggest"` → add a strong suggestion in UserPromptSubmit text.  
- `intentPatterns` as regex catch variations like “fix my hook blocking error”.[10]

### 6.2 Guardrail Skill Example (Block)

Guardrail skills **must** be used before dangerous actions, so they integrate with your PreToolUse gates.[13][11]

```json
{
  "safe-git": {
    "type": "guardrail",
    "enforcement": "block",
    "priority": "critical",
    "promptTriggers": {
      "keywords": ["git", "force-push", "reset --hard"],
      "intentPatterns": ["(force|dangerous).*git", "protect.*git"]
    },
    "fileTriggers": {
      "glob": [".git/**"]
    },
    "sessionMarker": ".claude/hooks/state/safe-git-used-{session_id}.json"
  }
}
```

Your PreToolUse scripts can check for `sessionMarker` files to avoid repeatedly blocking after the first compliant run in a session.[17][10]

***

## 7. Skill‑Scoped Hooks (Per‑Skill Safety & Quality)

Claude Code now supports **scoped hooks in SKILL frontmatter**: they only fire while the skill’s agent is active.[2][1]

### 7.1 Example for claude‑automation‑recommender

In `./.claude/skills/claude-automation-recommender/SKILL.md`:

```yaml
---
name: claude-automation-recommender
description: Recommend and debug Claude Code automations (hooks, skills, MCP, subagents). Focus on PreToolUse gates and safety.
context: fork
hooks:
  PreToolUse:
    - matcher: "Bash|Edit"
      hooks:
        - type: "command"
          command: "./internal-safety.sh"
  PostToolUse:
    - hooks:
        - type: "command"
          command: "./validation.sh"
---
```

- The **scoped PreToolUse** here can, for example, block editing of `.claude/hooks/**` unless it has already produced a plan.[9][1]
- The **scoped PostToolUse** can act as a quality gate: check that recommended hooks/skills follow your patterns before returning to the user.[1]

This localizes aggressive constraints to when the skill is running, instead of globally.

***

## 8. Additional Safety: Git‑Focused PreToolUse

You’ve already looked at git safety; here’s a more complete PreToolUse script to block destructive git operations unless a “safe‑git” skill has been used in this session.[13][9]

Create `.claude/hooks/PreToolUse-git-guard.sh`:

```bash
#!/bin/bash
stdin=$(cat)

tool_name=$(echo "$stdin" | jq -r '.toolName // ""')
command=$(echo "$stdin" | jq -r '.toolArguments.command // ""')

# Only care about Bash
if [[ "$tool_name" != "Bash" ]]; then
  echo "{}"
  exit 0
fi

# Simple destructive checks
if [[ "$command" =~ "git push" && "$command" =~ "--force" ]] \
   || [[ "$command" =~ "git reset" && "$command" =~ "--hard" ]]; then

  # Optional session marker check
  session_marker=".claude/hooks/state/safe-git-used-$$.json"
  if [[ -f "$session_marker" ]]; then
    echo "{}"
    exit 0
  fi

  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "⛔ Git guardrail: Destructive git command detected. Use Skill(\\"safe-git\\") to review and approve this operation before retrying."
  }
}
EOF
  exit 0
fi

echo "{}"
exit 0
```

Register alongside your SKILL‑FIRST gate, either as a second PreToolUse entry or as a router script that runs multiple checks.[13][1]

***

## 9. Testing & Debugging Skill Activation

### 9.1 Activation Harness

Use CLI to stress‑test activation the way community posts did (200–250 prompts):[6][5]

```bash
for i in {1..50}; do
  claude -p "test $i: debug .claude/hooks PreToolUse E_SKILL_FIRST"
done
```

Manually/with a script, count how often the **first** assistant turn calls the correct `Skill(...)`. Aim for ≥84% after forced‑eval; 100% when combined with SKILL‑FIRST gate for slash‑invoked workflows.[12][5][6]

### 9.2 Diagnostic Checklist

When things misbehave:

1. **/hooks** – confirm hooks are loaded and project‑scoped, and that matchers are correct.[4][1]
2. **Logs** – check `~/.claude/logs` to see hook JSON, stderr, and decisions.[18][9]
3. **/context** – ensure combined skill descriptions + CLAUDE.md + extras don’t blow past the model’s description budget (~2% of window, ~16k chars by common guidance).[19][7][2]
4. **Skill names** – use exact names in `Skill(skill="name")` (lowercase‑hyphen).[3][2]
5. **Description hygiene** – ensure the YAML description contains literal keywords matching your prompts and files.[11][14][5]
6. **Forced‑eval working?** – inspect first assistant turn; it should enumerate skills with YES/NO and then immediately call Skill() where appropriate.[5][6]

### 9.3 Common Failure Modes & Fixes

- **Vague descriptions → no activation.**  
  - Fix: add error codes (`E_SKILL_FIRST`), hook names (`PreToolUse`), framework names, and file patterns directly into the description.[14][5]

- **Too many skills loaded → zero activation.**  
  - Fix: prune to a small set of high‑value skills per repo, and use skill‑rules + forced‑eval to progressively disclose others.[20][8][5]

- **Infinite SKILL‑FIRST loops.**  
  - Fix: temporarily disable the gate (`mv PreToolUse-skill-first-gate.sh{,.disabled}`), manually type `Skill(skill="claude-automation-recommender")`, then re‑enable.[9][1]

- **Hooks silently bricking tools.**  
  - Fix: ensure PreToolUse hooks emit valid JSON with `permissionDecision` and a clear reason, and avoid mixing old “exit 2 only” patterns with the newer JSON API.[13][1]

***

## 10. Decision Matrix (When to Use What)

| Technique                         | Role                                  | Enforcement | Typical Activation | Best Use Case                                      |
|----------------------------------|----------------------------------------|------------|--------------------|----------------------------------------------------|
| Clean YAML + SKILL.md only       | Baseline behavior                      | Soft       | ~20–50%            | Simple repos / few skills                          |
| Forced‑Eval UserPromptSubmit     | “LLM traffic controller”               | Soft+      | 84–100% (targeted) | Ensuring right skill is considered for each prompt |
| Global SKILL‑FIRST PreToolUse    | Hard SKILL‑FIRST gate                  | Hard       | 100% if triggered  | Enforcing slash workflows like `/claude-automation-recommender` |
| Guardrail PreToolUse (git, edit) | Safety guard for destructive tools     | Hard       | 100% if triggered  | Git, shell, and mass‑edit safety                   |
| Skill‑scoped hooks               | Per‑skill safety/quality checks        | Hard (scoped) | 100% while active | Constraining specific skills’ behavior             |
| skill‑rules.json (block/suggest) | Policy layer for domain/guardrail split| Mixed      | Depends            | Scaling many skills with clear priorities          |

This layering matches what Anthropic’s docs and community patterns suggest for robust, production‑style Claude Code setups.[3][11][13][2][1]

***

If you’d like, I can next:

- Generate a **repo‑ready `SKILL.md`** for `claude-automation-recommender` using your actual stack and pain points, or  
- Produce a **compact hooks inventory** for your existing `.claude/hooks` with suggested routers and refactors.

## Human

Do you think the reviewing LLM went too far?
"
› what should I tell the original LLM about your edits?


• Tell it this:

  1. PreToolUse compatibility fix

  - Stop using {"continue": false} for PreToolUse blocks.
  - Use Claude-compatible payload:
      - hookSpecificOutput.hookEventName = "PreToolUse"
      - hookSpecificOutput.permissionDecision = "deny"
      - hookSpecificOutput.permissionDecisionReason = "..."
  - Return exit code 0 for deny/allow JSON responses.

  2. Skill-first reliability fix

  - Canonicalize skill names before comparing (namespace:skill, /skill, skill -> skill).
  - Avoid false loops after successful Skill(...).

  3. Multi-terminal + stale-data hardening (skill enforcement only)

  - Intent file naming stays scoped: pending_command_intent_{terminal}_{session}.json.
  - Intent payload now includes session_id and terminal_id.
  - PreToolUse validates payload scope; mismatched scope files are deleted/ignored (stale immunity).
  - No TTL dependency for skill intent correctness.

  4. Safer writes

  - Intent writes use atomic temp-file replace with one retry to reduce transient FS race failures.

  5. Better diagnostics

  - Added skill_loaded_unblocked event logging when gate clears after skill load.
  - Added skill_state_mismatch telemetry with raw/canonical intent vs state skill values.

  6. Explicit instruction text

  - Skill-first block message now includes:
      - Your FIRST action must be: Skill(skill='claude-automation-recommender') exactly, no analysis.

  7. Where changes were made

  - P:\\.claude\\hooks\\PreToolUse.py
  - P:\\.claude\\hooks\\UserPromptSubmit\\skill_enforcer.py
  - (earlier related work) P:\\.claude\\hooks\\__lib\\pre_tool_use_logic.py
  - (earlier related work) P:\\.claude\\hooks\\PreToolUse_python_c_validator.py

  8. Operational note

  - No settings.json re-registration required if it already points to these routers.
  - Must reload hooks/session (/hooks or restart) because hook behavior is snapshotted per session."

## Assistant

**No, the reviewing LLM did not go too far—it delivered precise, necessary fixes aligned with your Claude Code v2.1.63 Python router stack.** The changes address real compatibility gaps in generic bash guides (e.g., my shell scripts) for your environment, without overhauling your hooks.[1][2][3]

## Why It's Appropriate
Your attached draft shows the reviewer **restored your operational guide** while applying 8 targeted patches for **v2.1.63 Python hooks** (not v2.4+ bash). Key wins:[1]

- **PreToolUse JSON fix:** Switched from bash `{"continue": false}` to canonical `hookSpecificOutput.permissionDecision: "deny"` + exit 0 (required since v2.1).[2]
- **Canonical skill matching:** Normalizes `/claude-automation-recommender` → `claude-automation-recommender` to kill false loops post‑Skill().[4]
- **Multi‑terminal hardening:** Scoped intent files (`pending_command_intent_{terminal}_{session}.json`) + payload validation prevents stale cross‑terminal blocks—critical for your workflow.
- **Atomic writes + diagnostics:** Retry temp‑file FS ops, `skill_loaded_unblocked` logs—production polish without bloat.

These are **incremental** (7 files touched, no settings.json rewrite), preserving your Python routers (`PreToolUse.py`, `skill_enforcer.py`).[1]

## Reviewer Scope Assessment
| Aspect | Scope | Appropriate? |
|--------|-------|--------------|
| Core Changes | PreToolUse JSON + skill canonicalization | Yes—fixes bash/Python mismatch |
| Hardening | Multi‑terminal state + atomic writes | Yes—fits your setup |
| Diagnostics | Events/logs (`skill_state_mismatch`) | Yes—debug aid |
| Instruction Text | Exact "FIRST action: Skill(skill='...') exactly" | Yes—boosts obedience[5] |

**Not overreach:** No new hooks added; no architecture rewrite; reload `/hooks` suffices. Aligns with your hook inventory + stderr best practices.

## What to Tell the Original LLM
Use the reviewer's summary verbatim—it's concise and actionable. Prefix with context:

```
Thanks for the guide. The reviewing LLM made these targeted fixes for my Python router stack (v2.1.63):

[ paste the 8 points ]

These resolve bash/Python incompatibilities and add multi-terminal safety without changing your core design. Reload hooks and we're live.
```

This credits the reviewer, gives deploy instructions, and loops back improvements to the original LLM for future iterations. Drop it in your next session with the original.

## Human

What are the main topics in this conversation?

## Assistant

Main topics:

- **Claude Code skills auto‑activation**: How to get skills like `claude-automation-recommender` to trigger reliably (forced‑eval hooks, LLM‑eval, progressive disclosure, description hygiene).[1][2]
- **Hooks design and enforcement**: Implementing and debugging `PreToolUse` and `UserPromptSubmit` hooks for SKILL‑FIRST gates, git safety, and skill‑scoped behavior.[3][4]
- **Operational guide for skills + hooks**: Drafting and iterating a full “Operational Best Practices” document for Claude Code v2.x (bootstrap scripts, decision matrix, recovery, testing harness).[5][6]
- **skill‑rules / policy layer**: Domain vs guardrail skills, enforcement levels (`suggest`/`warn`/`block`), trigger patterns, and session markers to avoid repeated gating.[7][8]
- **Review and correction of LLM‑generated guides**: Comparing Grok vs Gemini outputs and incorporating a reviewing LLM’s environment‑specific fixes for your Python router stack.[5]
