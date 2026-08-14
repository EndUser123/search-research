---
title: "10. Decision Matrix (When to Use What)"
date: "2026-03-04"
mode: "ARTICLE"
uuid: "9fddb5f9-fc08-4882-ae04-bd8ee151f382"
entry_count: 21
---

## Assistant

Here’s an end‑to‑end operational guide that folds in Grok’s and Gemini’s ideas, Anthropic’s current docs, and the patterns you’ve been exploring (forced‑eval, PreToolUse gates, progressive disclosure, skill‑rules, session markers). It’s written to be drop‑in for Claude Code v2.4+ as of March 2026.[1][2][3]

***

## Human

Operational Guide: Skills, Hooks, and Gates in Claude Code

## Assistant

**Target:** Claude Code v2.4+ -  **Focus:** SKILL‑FIRST enforcement + high skill activation + safety

## Human

0. Goals & Design Targets

## Assistant

This guide aims for:

- **100% SKILL‑FIRST compliance** when you call a skill slash command (e.g. `/claude-automation-recommender`).[1]
- **84–100% activation rate** on “on‑target” prompts using a forced‑eval UserPromptSubmit hook.[2][3]
- **Low overhead:** <2% of context budget via progressive disclosure (short YAML + compact SKILL.md + external docs).[4][5]

Assumptions:

- You’re on Claude Code v2.4+ with **hooks** and **skills** enabled.[6][1]
- Your repo lives under something like `P:\project`, with `.claude` at the root (your current setup).

***

## Human

1. Architecture Overview

## Assistant

At a high level you’ll wire things like this:

1. **UserPromptSubmit (forced‑eval):** Before Claude even “sees” the prompt, inject instructions forcing it to explicitly evaluate each relevant skill as YES/NO and, if YES, make `Skill(...)` the first action.[1][2][3]
2. **PreToolUse (global SKILL‑FIRST gate):** Before any tool (Bash, Read, Grep, Edit, etc.), block if there’s a pending skill intent like `/claude-automation-recommender` and that skill has not yet been called.[4][2]
3. **Skill design (progressive disclosure):** Tight Level‑1 YAML, constrained Level‑2 SKILL.md, Level‑3 docs/resources via `!glob` or Read.[5][6][7]
4. **skill‑rules.json:** Domain vs guardrail skills with `enforcement` levels (suggest / warn / block) and session markers to avoid repeated gating.[8][9]
5. **Skill‑scoped hooks:** For specific skills (like `claude-automation-recommender`), embed scoped PreToolUse/PostToolUse hooks directly in frontmatter.[2][6]

***

## Human

2. Quick Bootstrap (Minimal but Safe)

## Assistant

If you want a “just get me there” baseline, you can add **three things**:

1. `UserPromptSubmit` forced‑eval hook.  
2. `PreToolUse` global SKILL‑FIRST gate.  
3. A minimal SKILL.md frontmatter for `claude-automation-recommender`.  

Below I give the scripts and config. If you already have `.claude/settings.json`, **merge these snippets** instead of overwriting.

***

## Human

3. Forced‑Eval UserPromptSubmit Hook

## Assistant

### 3.1 Behavior

- Runs **once per user prompt** before Claude processes it.[1]
- Reads JSON on stdin (`{"prompt": "...", ...}`), outputs plain text that gets appended to the model’s context.[1]
- Forces explicit YES/NO reasoning over available skills and mandates that any YES skill must be called first via `Skill(...)` before tools or free‑form analysis.[2][3]

### 3.2 Hook Script

Create `.claude/hooks/forced-eval.sh`:

```bash
#!/bin/bash

## Human

.claude/hooks/forced-eval.sh (UserPromptSubmit)

## Assistant

stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // ""')

## Human

Discover skills (simple: all .md files, adjust paths if needed)

## Assistant

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

Hook semantics (UserPromptSubmit: stdout → extra context, exit code 0 = allow) follow Anthropic’s hook docs.[1][2]

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

This alone tends to push on‑target skill activation into the ~84–100% range in community experiments, compared to ~20–40% with descriptions only.[3][4][5]

***

## Human

4. Global SKILL‑FIRST PreToolUse Gate

## Assistant

### 4.1 Behavior

- Fires **before any tool** (Bash/Read/Grep/Edit/etc.).[1]
- Looks at the tool invocation JSON, and if it detects that the user asked for a skill (e.g. via `/claude-automation-recommender`) but the model hasn’t called `Skill("claude-automation-recommender")` yet, it returns a JSON **deny** response with a clear reason.[2][1]
- This is your “cannot proceed until you obey SKILL‑FIRST” hard gate.  

### 4.2 Gate Script

Create `.claude/hooks/PreToolUse-skill-first-gate.sh`:

```bash
#!/bin/bash

## Human

.claude/hooks/PreToolUse-skill-first-gate.sh (PreToolUse)

## Assistant

stdin=$(cat)

tool_name=$(echo "$stdin" | jq -r '.toolName // ""')
arguments=$(echo "$stdin" | jq -r '.toolArguments // ""')

## Human

Prompt text if present (depends on Claude Code version)

## Assistant

recent_prompt=$(echo "$stdin" | jq -r '.recentUserPrompt // empty')

## Human

Detect intent to use claude-automation-recommender by slash command

## Assistant

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

## Human

Default: allow

## Assistant

echo "{}"
exit 0
```

This follows the documented pattern: PreToolUse can return JSON containing `hookSpecificOutput.permissionDecision: "deny"` to veto a tool call.[1][2]

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

You can narrow the matcher if needed (e.g., only `Bash|Read`) to reduce latency.[2][3]

***

## Human

5. Skill Design: YAML Frontmatter & Progressive Disclosure

## Assistant

### 5.1 Level‑1 YAML (Always Loaded)

Keep YAML short and **keyword‑dense**: name, description, maybe a couple of config fields. This is what Claude uses for **auto‑activation** heuristics.[1][2]

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

Best practices from Anthropic’s skill authoring docs and community write‑ups:[2][1][3]

- **Name:** lowercase‑hyphen; avoid ambiguity.  
- **Description:** ≤ 1024 characters, include **literal** keywords (“PreToolUse”, “E_SKILL_FIRST”, “hooks”) rather than only semantic language.[4][5]
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

Keep this tight; push long examples and docs to Level‑3 resources.[3][6]

### 5.3 Level‑3 Resources (Progressive Disclosure)

Create `./.claude/skills/claude-automation-recommender/docs/` for heavier docs.[7][6]

Examples:

- `blocking-hooks-examples.md` – patterns for PreToolUse/UserPromptSubmit.  
- `progressive-disclosure.md` – policy for Level 1–3.  

Reference them in SKILL.md as **optional** reads:

```markdown
If you need more examples of blocking hooks, read:
- .claude/skills/claude-automation-recommender/docs/blocking-hooks-examples.md
```

Claude only pulls these into context when necessary, keeping budget low.[6][3]

***

## Human

6. skill‑rules.json: Domain vs Guardrail Skills

## Assistant

While Claude Code doesn’t ship a canonical `skill-rules.json` format, several “skill developer” helpers and community guides converge on the same pattern: triggers + enforcement + priority.[1][2][3]

### 6.1 Domain Skill Example

“Domain” skills add expertise but don’t *have* to be used.[2][1]

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
- `intentPatterns` as regex catch variations like “fix my hook blocking error”.[3]

### 6.2 Guardrail Skill Example (Block)

Guardrail skills **must** be used before dangerous actions, so they integrate with your PreToolUse gates.[4][1]

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

Your PreToolUse scripts can check for `sessionMarker` files to avoid repeatedly blocking after the first compliant run in a session.[5][3]

***

## Human

7. Skill‑Scoped Hooks (Per‑Skill Safety & Quality)

## Assistant

Claude Code now supports **scoped hooks in SKILL frontmatter**: they only fire while the skill’s agent is active.[1][2]

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

- The **scoped PreToolUse** here can, for example, block editing of `.claude/hooks/**` unless it has already produced a plan.[3][2]
- The **scoped PostToolUse** can act as a quality gate: check that recommended hooks/skills follow your patterns before returning to the user.[2]

This localizes aggressive constraints to when the skill is running, instead of globally.

***

## Human

8. Additional Safety: Git‑Focused PreToolUse

## Assistant

You’ve already looked at git safety; here’s a more complete PreToolUse script to block destructive git operations unless a “safe‑git” skill has been used in this session.[1][2]

Create `.claude/hooks/PreToolUse-git-guard.sh`:

```bash
#!/bin/bash
stdin=$(cat)

tool_name=$(echo "$stdin" | jq -r '.toolName // ""')
command=$(echo "$stdin" | jq -r '.toolArguments.command // ""')

## Human

Only care about Bash

## Assistant

if [[ "$tool_name" != "Bash" ]]; then
  echo "{}"
  exit 0
fi

## Human

Simple destructive checks

## Assistant

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

Register alongside your SKILL‑FIRST gate, either as a second PreToolUse entry or as a router script that runs multiple checks.[1][2]

***

## Human

9. Testing & Debugging Skill Activation

## Assistant

### 9.1 Activation Harness

Use CLI to stress‑test activation the way community posts did (200–250 prompts):[1][2]

```bash
for i in {1..50}; do
  claude -p "test $i: debug .claude/hooks PreToolUse E_SKILL_FIRST"
done
```

Manually/with a script, count how often the **first** assistant turn calls the correct `Skill(...)`. Aim for ≥84% after forced‑eval; 100% when combined with SKILL‑FIRST gate for slash‑invoked workflows.[3][2][1]

### 9.2 Diagnostic Checklist

When things misbehave:

1. **/hooks** – confirm hooks are loaded and project‑scoped, and that matchers are correct.[4]
2. **Logs** – check `~/.claude/logs` to see hook JSON, stderr, and decisions.[5][6]
3. **/context** – ensure combined skill descriptions + CLAUDE.md + extras don’t blow past the model’s description budget (~2% of window, ~16k chars by common guidance).[7][8][9]
4. **Skill names** – use exact names in `Skill(skill="name")` (lowercase‑hyphen).[10][9]
5. **Description hygiene** – ensure the YAML description contains literal keywords matching your prompts and files.[11][12][2]
6. **Forced‑eval working?** – inspect first assistant turn; it should enumerate skills with YES/NO and then immediately call Skill() where appropriate.[2][1]

### 9.3 Common Failure Modes & Fixes

- **Vague descriptions → no activation.**  
  - Fix: add error codes (`E_SKILL_FIRST`), hook names (`PreToolUse`), framework names, and file patterns directly into the description.[12][2]

- **Too many skills loaded → zero activation.**  
  - Fix: prune to a small set of high‑value skills per repo, and use skill‑rules + forced‑eval to progressively disclose others.[13][14][2]

- **Infinite SKILL‑FIRST loops.**  
  - Fix: temporarily disable the gate (`mv PreToolUse-skill-first-gate.sh{,.disabled}`), manually type `Skill(skill="claude-automation-recommender")`, then re‑enable.[6][4]

- **Hooks silently bricking tools.**  
  - Fix: ensure PreToolUse hooks emit valid JSON with `permissionDecision` and a clear reason, and avoid mixing old “exit 2 only” patterns with the newer JSON API.[15][4]

***

## Human

10. Decision Matrix (When to Use What)

## Assistant

| Technique                         | Role                                  | Enforcement | Typical Activation | Best Use Case                                      |
|----------------------------------|----------------------------------------|------------|--------------------|----------------------------------------------------|
| Clean YAML + SKILL.md only       | Baseline behavior                      | Soft       | ~20–50%            | Simple repos / few skills                          |
| Forced‑Eval UserPromptSubmit     | “LLM traffic controller”               | Soft+      | 84–100% (targeted) | Ensuring right skill is considered for each prompt |
| Global SKILL‑FIRST PreToolUse    | Hard SKILL‑FIRST gate                  | Hard       | 100% if triggered  | Enforcing slash workflows like `/claude-automation-recommender` |
| Guardrail PreToolUse (git, edit) | Safety guard for destructive tools     | Hard       | 100% if triggered  | Git, shell, and mass‑edit safety                   |
| Skill‑scoped hooks               | Per‑skill safety/quality checks        | Hard (scoped) | 100% while active | Constraining specific skills’ behavior             |
| skill‑rules.json (block/suggest) | Policy layer for domain/guardrail split| Mixed      | Depends            | Scaling many skills with clear priorities          |

This layering matches what Anthropic’s docs and community patterns suggest for robust, production‑style Claude Code setups.[1][2][3][4][5]

***

If you’d like, I can next:

- Generate a **repo‑ready `SKILL.md`** for `claude-automation-recommender` using your actual stack and pain points, or  
- Produce a **compact hooks inventory** for your existing `.claude/hooks` with suggested routers and refactors.
