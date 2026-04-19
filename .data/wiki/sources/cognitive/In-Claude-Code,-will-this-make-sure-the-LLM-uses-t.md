<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# In Claude Code, will this make sure the LLM uses the skill?

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
    No, this setup does not ensure the LLM uses the skill—it's actively preventing it. The PreToolUse:Bash hook in `.claude/hooks/PreToolUse.py` implements a "SKILL-FIRST GATE" that detects the `/claude-automation-recommender` slash command via `[E_SKILL_FIRST_PENDING_INTENT]`, then repeatedly blocks all tool calls (like searches or file reads) until Claude explicitly calls `Skill("claude-automation-recommender")` as its absolute first action.[^1_1][^1_2]

## Hook Mechanism

PreToolUse hooks fire before any tool execution, matching on tool names (e.g., Bash, Read) and allowing blocks via exit code 2 or JSON with `permissionDecision: "deny"`. Your hook script likely inspects recent user input or session transcript for pending skill intents like `/claude-automation-recommender` (from the claude-code-setup plugin), printing the blocking error to stderr on match.[^1_1]

- Blocks analysis, code reading, or scripting until compliance.
- Loop occurs because Claude ignores the instruction, attempts tools (e.g., search codebase), and gets blocked again.
- Matches your log: even `Read` for the hook file itself triggers it.


## Skill Invocation

Skills load via Claude's `Skill()` tool call, not just slash commands. Slash `/name` injects the SKILL.md prompt, but for gated skills (especially with `disable-model-invocation: true`), Claude must proactively `Skill(skill="claude-automation-recommender")` first—common for recommender plugins to enforce structured workflows.[^1_3][^1_4]

## Resolution Steps

To break the loop and ensure skill use:

- Temporarily disable the hook: Run `/hooks`, select [Project] PreToolUse, delete/disable; restart session.
- Or instruct Claude explicitly: "Your FIRST action must be: Skill(skill='claude-automation-recommender') exactly, no analysis."
- Verify post-load: Skill logs "Successfully loaded skill", unblocking tools for hook review.[^1_5]

This gate enforces best practices for your hook-heavy workflows but needs precise obedience.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://code.claude.com/docs/en/hooks

[^1_2]: https://github.com/anthropics/claude-code/issues/22761

[^1_3]: https://www.perplexity.ai/search/6ffc2e3b-987a-42ad-aedf-4c835c277558

[^1_4]: https://code.claude.com/docs/en/skills

[^1_5]: https://mcpmarket.com/tools/skills/claude-automation-recommender

[^1_6]: https://code.claude.com/docs/en/hooks-guide

[^1_7]: https://www.reddit.com/r/ClaudeAI/comments/1qcwckg/the_complete_guide_to_claude_code_v2_claudemd_mcp/

[^1_8]: https://www.datacamp.com/tutorial/claude-code-hooks

[^1_9]: https://github.com/TheDecipherist/claude-code-mastery

[^1_10]: https://platform.claude.com/docs/en/agent-sdk/hooks

[^1_11]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^1_12]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^1_13]: https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/

[^1_14]: https://github.com/anthropics/claude-code/issues/2814

[^1_15]: https://support.claude.com/en/articles/12512180-use-skills-in-claude

[^1_16]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/


---

# Examples of forcing Claude to use specific skills

How do hooks interact with skill invocations
Common pitfalls when calling Skill() in hooks

Hooks enforce skill use by blocking tools until Claude calls `Skill()`, while skills can embed their own hooks for scoped control. Examples include PreToolUse gates that loop errors until compliance, and prompt/agent hooks that evaluate skills before actions. Common pitfalls involve syntax mismatches, missing `$ARGUMENTS`, and hooks lacking direct Skill invocation.[^2_1][^2_2]

## Forcing Skill Use

PreToolUse hooks block tools (e.g., Read, Bash) on slash commands like `/claude-automation-recommender`, forcing `Skill("claude-automation-recommender")` as the first action via exit code 2 and stderr errors like `[E_SKILL_FIRST_PENDING_INTENT]`. Other methods: UserPromptSubmit adds context urging Skill calls; PostToolUse prompts re-evaluation.[^2_3][^2_4][^2_5]

- "Forced eval hook" explicitly reasons YES/NO per skill before tools, boosting activation from 20% to 84%.[^2_3]
- Spawn `claude -p "/skill args"` from command hooks for deterministic invocation.[^2_4]
- `disable-model-invocation: true` hides from auto-trigger but allows manual `/skill`.[^2_1]


## Hooks and Skills Interaction

Hooks run at lifecycle events (PreToolUse before tools, UserPromptSubmit before prompts); skills define scoped hooks in frontmatter like `hooks: { PreToolUse: [...] }`, active only during skill execution. PreToolUse gates detect pending intents from transcript, blocking until Skill loads full content.[^2_2]


| Interaction | Hook Role | Skill Role |
| :-- | :-- | :-- |
| Gating | Blocks tools until `Skill()` call | Loads on slash or auto; provides instructions |
| Scoped | Skill frontmatter hooks fire only when active | `context: fork` runs in subagent with hooks |
| Invocation | No direct `type: "skill"`; use Bash proxy | `Skill(name)` tool call loads it |

Skills merge old commands; descriptions auto-trigger unless disabled.[^2_1]

## Common Pitfalls

Hooks can't directly invoke skills (no `type: "skill"`); proxy via `claude -p "/skill"` in Bash hooks. Skill calls fail on name mismatches (exact/lowercase), missing descriptions, or permission denials on `Skill` tool.[^2_6][^2_4]

- Infinite blocks: Exit 2 without JSON; use `permissionDecision: "deny"` in `hookSpecificOutput`.[^2_2]
- Lazy loading: Descriptions always in context; full content only on invoke—exceeds budget with many skills.[^2_1]
- Args ignored: No `$ARGUMENTS` in SKILL.md appends them; use `$0`, `$1` for indexed.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://code.claude.com/docs/en/skills

[^2_2]: https://code.claude.com/docs/en/hooks

[^2_3]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^2_4]: https://dev.to/aabyzov/claude-code-hook-limitations-no-skill-invocation-lazy-plugin-loading-and-how-i-solved-it-44f2

[^2_5]: https://www.reddit.com/r/ClaudeAI/comments/1pu0pmb/getting_claude_skills_to_invoke_consistently_with/

[^2_6]: https://institute.sfeir.com/en/claude-code/claude-code-custom-commands-and-skills/errors/

[^2_7]: https://aiblewmymind.substack.com/p/claude-skills-36-examples

[^2_8]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^2_9]: https://huggingface.co/blog/sionic-ai/claude-code-skills-training

[^2_10]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^2_11]: https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/

[^2_12]: https://genaiunplugged.substack.com/p/claude-code-skills-commands-hooks-agents

[^2_13]: https://huggingface.co/blog/hf-skills-training

[^2_14]: https://blog.sshh.io/p/how-i-use-every-claude-code-feature

[^2_15]: https://support.claude.com/en/articles/12512180-using-skills-in-claude


---

# Best practices for writing skill descriptions to improve auto-activation

How to implement user-invocable vs auto-invocable skills
Examples of fork context and subagents in skills
Workarounds for invoking skills from hooks
Templates for effective skill frontmatter configuration

Skill descriptions act as "search queries" Claude matches against prompts—precise keywords boost auto-activation from ~20% to 80%+. User-invocable skills use `/name`; auto-invocable rely on descriptions without `disable-model-invocation: true`. Fork context leverages built-in agents like Explore; hooks workaround via `claude -p "/skill"`.[^3_1][^3_2][^3_3][^3_4]

## Skill Descriptions

Use action-oriented phrases targeting intents/files: "Validate TypeScript schemas in .claude/rules" over "Schema tool". Specifics (e.g., "debug PreToolUse hooks blocking tools") match better than vague "debugging skill".[^3_5][^3_3][^3_6]

- Test: List skills, prompt matching description—check invocation.
- Length: 1-2 sentences; too long dilutes.
- Hooks amplify: UserPromptSubmit injects "🎯 USE [skill]" on keyword match.[^3_2][^3_7]


## Invocable Types

User-invocable: Default, slash-trigger + auto via description. Auto-only: Omit description or set `user-invocable: false`—Claude decides.[^3_4]


| Type | Slash `/name` | Auto-Trigger | Other Skills Call | Best For |
| :-- | :-- | :-- | :-- | :-- |
| Default | ✅ | ✅ | ✅ | General |
| No Description | ✅ | ❌ | ✅ | Helpers |
| `disable-model-invocation: true` | ✅ | ❌ | ❌ | User-only |
| `user-invocable: false` | ❌ | ✅ | ✅ | Claude-decided |

## Fork and Subagents

`context: fork` + `agent: Explore` forks parent context into built-in agent (e.g., "Investigate \$ARGUMENTS"), loading SKILL.md as task—lazy, inherits skills/tools.[^3_8]

```
---
context: fork
agent: Plan
---
Plan automations for hooks in .claude/hooks.
```

Subagent `skills: [name1,name2]` preloads full skills + CLAUDE.md; dynamic delegation but higher context cost.[^3_8]

Example: Fork for read-only analysis; subagent for editable workflows.

## Hook Workarounds

No native `Skill()` from hooks—use Bash proxy: `claude -p "/claude-automation-recommender review hooks" > output.json` then parse.[^3_9]

- UserPromptSubmit: Append "MANDATORY: Skill(skill=...) before tools".[^3_2]
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

<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15]</span>

<div align="center">⁂</div>

[^3_1]: https://code.claude.com/docs/en/skills

[^3_2]: https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57

[^3_3]: https://genaiunplugged.substack.com/p/claude-code-skills-commands-hooks-agents

[^3_4]: https://www.reddit.com/r/ClaudeCode/comments/1r3tcno/guide_all_the_ways_to_control_skill_invocability/

[^3_5]: https://claude-plugins.dev/skills/@withzombies/hyperpowers/skills-auto-activation

[^3_6]: https://repovive.com/roadmaps/claude-code/claude-md-skills-hooks-mcp/skill-frontmatter-fields

[^3_7]: https://claudefa.st/blog/tools/hooks/skill-activation-hook

[^3_8]: https://zenn.dev/trust_delta/articles/claude-code-skills-subagents-approaches?locale=en

[^3_9]: https://dev.to/aabyzov/claude-code-hook-limitations-no-skill-invocation-lazy-plugin-loading-and-how-i-solved-it-44f2

[^3_10]: https://scottspence.com/posts/claude-code-skills-dont-auto-activate

[^3_11]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^3_12]: https://mcpmarket.com/ja/tools/skills/claude-code-frontmatter-schemas

[^3_13]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^3_14]: https://github.com/travisvn/awesome-claude-skills

[^3_15]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/


---

# Common pitfalls in skill descriptions that prevent auto-activation

Detailed tutorial for setting up UserPromptSubmit hook
Real-world examples of context:fork skills in action
How to structure skill-rules.json for reliable matching
Differences between hooks and skills for enforcement

Skill descriptions fail auto-activation with vague phrasing, overload (too many skills dilute budget), or mismatches to user intents/files. UserPromptSubmit hooks inject mandatory skill checks pre-prompt via stdout on exit 0. Hooks enforce deterministically via blocks (exit 2); skills suggest probabilistically.[^4_1][^4_2][^4_3]

## Description Pitfalls

Vague/generic terms ("debug tool") ignored; use specifics like "debug PreToolUse hooks blocking Bash". Overlong (>100 chars) or absent descriptions skip loading. Multi-skill prompts drop rates to 0%; test 200+ prompts for baselines.[^4_4][^4_5][^4_1]

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

3. Test: `/hooks` verify; prompt with trigger—sees injection. Restart session for changes.[^4_6][^4_1]

Aggressive lang ("MANDATORY", "NON-NEGOTIABLE") boosts obedience.

## Fork Examples

`context: fork` + `agent: Explore` runs SKILL.md as task in read-only subagent, inheriting parent skills/tools lazily.[^4_2][^4_7]

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

Action: Isolates exploration; returns findings. Real: PR summarizer fetches `gh pr diff` via `!` subst, tasks Explore agent.[^4_2]

## skill-rules.json Structure

`.claude/skills/skill-rules.json` defines triggers/enforcement for plugins like skill-creator (not core).[^4_8][^4_9]

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

Fields: `type` (domain/global), `enforcement` (block/suggest/warn), triggers (keywords/regex/glob).[^4_8]

## Hooks vs Skills Enforcement

Hooks: Deterministic scripts at events (PreToolUse blocks via exit 2); run always on match.[^4_10]


| Aspect | Hooks | Skills |
| :-- | :-- | :-- |
| Trigger | Event+matcher (e.g., Bash) | Description match or /invoke |
| Enforcement | Hard (exit 2 blocks) | Soft (Claude decides, ~20-84%) |
| Scope | Global/project | Inline/fork/subagent |
| Output | JSON/exit codes | Instructions/\$ARGUMENTS |

Use hooks for gates (your SKILL-FIRST); skills for knowledge/workflows.[^4_3][^4_10]
<span style="display:none">[^4_11][^4_12][^4_13][^4_14][^4_15]</span>

<div align="center">⁂</div>

[^4_1]: https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57

[^4_2]: https://code.claude.com/docs/en/skills

[^4_3]: https://claude-plugins.dev/skills/@withzombies/hyperpowers/skills-auto-activation

[^4_4]: https://scottspence.com/posts/claude-code-skills-dont-auto-activate

[^4_5]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^4_6]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^4_7]: https://zenn.dev/trust_delta/articles/claude-code-skills-subagents-approaches?locale=en

[^4_8]: https://skills.pub/en/skills/diet103-claude-code-infrastructure-showcase::claude-code-infrastructure-showcase::-claude-skills-skill-developer::diet103

[^4_9]: https://claude-plugins.dev/skills/@PaulRBerg/dot-claude/skill-creator

[^4_10]: https://genaiunplugged.substack.com/p/claude-code-skills-commands-hooks-agents

[^4_11]: https://www.reddit.com/r/ClaudeCode/comments/1r89084/selfimprovement_loop_my_favorite_claude_code_skill/

[^4_12]: https://x.com/EricBuess/status/2009073718450889209

[^4_13]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^4_14]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^4_15]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf


---

# How to implement LLM hook for 80% skill activation

What is forced eval hook and its script example
Best practices for skill-rules.json trigger patterns
How to use agent-scoped hooks like PreToolUse
Examples of multi-skill prompts and their pitfalls

Forced eval hooks boost skill activation to 84-100% by requiring Claude to explicitly reason YES/NO per skill before tools. LLM hooks (e.g., UserPromptSubmit prompt handlers) pre-classify via fast model for ~80% rates. Agent-scoped hooks limit PreToolUse to skill/subagent lifecycles via frontmatter.[^5_1][^5_2][^5_3][^5_4]

## LLM Hook for 80% Activation

Use UserPromptSubmit "LLM eval hook": prompt Claude (or fast model) to classify skills from prompt/transcript, inject "USE [skill]" context. Boosts from 50% baseline to 80%; cheaper than forced eval.[^5_2][^5_5]

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

Config: `"hooks": {"UserPromptSubmit": [{"hooks": [{"type":"command","command":"$CLAUDE_PROJECT_DIR/.claude/hooks/skill-eval.sh"}]}]}`[^5_3][^5_1]

## Forced Eval Hook

"forced-eval hook" (UserPromptSubmit command) forces Claude to YES/NO evaluate each skill pre-prompt, committing via structured reasoning. Hits 84-100% across 250+ evals; outperforms simple instructions (40%).[^5_1][^5_3]

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

Reddit tests: 100% on 44 tests; handles ambiguity ("no skill needed").[^5_1]

## skill-rules.json Patterns

Use precise regex/glob for triggers; `enforcement: "block"` for gates. Prioritize `medium/high`; test with 200+ prompts.[^5_6][^5_7]

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
- Avoid broad: Kills precision.[^5_6]


## Agent-Scoped PreToolUse

Frontmatter in agent/skill YAML: `hooks: { PreToolUse: [...] }`—runs only in that agent's loop (e.g., block Bash in Explore).[^5_4]

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

Lists 10+ skills drop activation to 0%—budget overflow, decision paralysis. Simple hooks fail; forced eval survives via per-skill eval.[^5_5][^5_3]

Examples:

- 44 skills: Baseline 50%, multi-prompt 0%.
- Pitfall: Vague descriptions compete; overloads context (descriptions ~16k chars cap).
- Fix: skill-rules.json progressive disclosure; gates limit to 3-5 active.[^5_1]
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://www.reddit.com/r/ClaudeCode/comments/1qzjy2h/claude_code_skills_went_from_84_to_100_activation/

[^5_2]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^5_3]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^5_4]: https://claudelog.com/faqs/what-are-agent-scoped-hooks-in-claude-code/

[^5_5]: https://www.linkedin.com/posts/spences10_how-to-make-claude-code-skills-activate-reliably-activity-7395925529599627264-9iZP

[^5_6]: https://claude-plugins.dev/skills/@blencorp/claude-code-kit/skill-developer

[^5_7]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^5_8]: https://www.linkedin.com/posts/spences10_measuring-claude-code-skill-activation-with-activity-7426362619307032576-N5uG

[^5_9]: https://code.claude.com/docs/en/skills

[^5_10]: https://code.claude.com/docs/en/hooks

[^5_11]: https://www.youtube.com/watch?v=cG2saB8hpxg

[^5_12]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^5_13]: https://skills.pub/en/skills/diet103-claude-code-infrastructure-showcase::claude-code-infrastructure-showcase::-claude-skills-skill-developer::diet103

[^5_14]: https://x.com/EricBuess/status/2009073718450889209

[^5_15]: https://institute.sfeir.com/en/claude-code/claude-code-custom-commands-and-skills/errors/


---

# LLM-eval hook script differences from forced-eval

skill-rules.json enforcement levels explained
PreToolUse hook practical example
Progressive disclosure in Claude Code skills
Debugging low skill activation rates

LLM-eval hooks pre-classify skills cheaply via fast model (e.g., Haiku), hitting 80% activation with speed but false positives; forced-eval requires Claude's YES/NO reasoning for 84-100% consistency. skill-rules.json `enforcement` levels escalate from suggest (passive) to block (hard gates). Debug activation via /hooks logs, eval harnesses, and keyword tests.[^6_1][^6_2][^6_3][^6_4]

## Hook Differences

LLM-eval: External/small model scans prompt/skills, injects "USE [skill]"—fast (10% cheaper), 80%, but hallucinates non-matches (67% accuracy). Forced-eval: Claude self-evals each skill pre-proceeding—no deps, 84-100%, zero false positives via commitment.[^6_2][^6_1]


| Hook | Activation | Speed/Cost | Reliability | Script Style |
| :-- | :-- | :-- | :-- | :-- |
| LLM-eval | 80% | High (Haiku) | Hallucinations on edges | Proxy to claude -m haiku |
| Forced-eval | 84-100% | Medium | Consistent, no FPs | UserPromptSubmit injection |

## Enforcement Levels

From skill-rules.json/plugins: Controls via hooks (UserPromptSubmit/PreToolUse).[^6_4]

- **suggest**: Append "🎯 USE [skill]" to prompt (passive, ~40%).
- **warn**: Stderr note + suggest (~60%).
- **block**: Exit 2 on PreToolUse/Edit, forces Skill() first (100% if triggered).[^6_4]

Example: `guardrail` skills block writes until verification.

## PreToolUse Example

Blocks `rm -rf` or git --force; JSON denies with reason fed to Claude.[^6_5]

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

Config: `"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": ".../block-destruct.sh"}] }]`.[^6_5]

## Progressive Disclosure

Load minimal SKILL.md (desc+core logic); defer deep docs/tools via `context: fork` or on-demand Read. Saves 70-90% tokens, scales 100+ skills.[^6_6][^6_7]

- Core: 500-line rule (essentials only).
- Defer: `!glob .claude/docs/${TOPIC}` in instructions.
- skill-rules.json skips irrelevant based on session/files.


## Debugging Activation

Run eval harness: 200+ synthetic prompts (/p harness); log /hooks output, Claude responses.[^6_8][^6_1]

Steps:

- Baseline: No hooks → 0-50%.
- Keyword test: Rephrase prompts (semantic fails; keywords win).
- Logs: `tail -f ~/.claude/logs/*` for hook firings.
- Metrics: Track YES/NO commits, false skips.
- Fixes: Forced-eval, precise descriptions, <16k char totals.[^6_9][^6_2]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15]</span>

<div align="center">⁂</div>

[^6_1]: https://www.reddit.com/r/ClaudeCode/comments/1qzjy2h/claude_code_skills_went_from_84_to_100_activation/

[^6_2]: https://www.linkedin.com/posts/spences10_measuring-claude-code-skill-activation-with-activity-7426362619307032576-N5uG

[^6_3]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^6_4]: https://claude-plugins.dev/skills/@deomiarn/claude-setup-template/skill-developer

[^6_5]: https://codango.com/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too/

[^6_6]: https://mcpmarket.com/zh/tools/skills/progressive-disclosure-pattern

[^6_7]: https://www.youtube.com/watch?v=DQHFow2NoQc

[^6_8]: https://www.linkedin.com/posts/spences10_how-to-make-claude-code-skills-activate-reliably-activity-7395925529599627264-9iZP

[^6_9]: https://github.com/orgs/community/discussions/182117

[^6_10]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^6_11]: https://code.claude.com/docs/en/hooks-guide

[^6_12]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^6_13]: https://claude-plugins.dev/skills/@blencorp/claude-code-kit/skill-developer

[^6_14]: https://www.eesel.ai/blog/hooks-reference-claude-code

[^6_15]: https://paddo.dev/blog/claude-skills-hooks-solution/


---

# How to implement progressive disclosure in a custom skill

Sample skill-rules.json for block enforcement
Full PreToolUse hook script for git blocking
Fixing keyword matching failures in skills
Compare UserPromptSubmit vs PreToolUse hooks

Progressive disclosure in custom skills keeps YAML frontmatter + core SKILL.md minimal (~100-500 tokens), deferring details to on-demand files via glob/Read. Block enforcement in skill-rules.json uses `enforcement: "block"` to gate tools until Skill() via PreToolUse. Keyword failures fix with exact phrases, regex in rules, and eval hooks.[^7_1][^7_2][^7_3][^7_4]

## Progressive Disclosure Implementation

YAML: Teaser description. Core SKILL.md: 500-line essentials + refs. Details: `.claude/skills/[skill]/docs/*.md` loaded via `!glob` or instructions.[^7_2][^7_3]

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

Claude reads docs only on match; scales 100+ skills.[^7_5]

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

Triggers PreToolUse block; Claude must Skill() to proceed.[^7_4][^7_6]

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

Blocks force-push; prompts Skill use.[^7_7]

## Fixing Keyword Matching

Failures from semantics > literals; use rules regex, eval hooks. Test: 200 prompts, track misses.[^7_8]

- Exact: "PreToolUse hook" not "pre-tool use".
- Rules: `intentPatterns: ["\\b(block|debug)\\b.*hook"]`.
- Hooks: Forced-eval lists skills explicitly.
- Descriptions: Action+files ("Review hooks blocking E_SKILL_FIRST").


## Hook Comparison

UserPromptSubmit pre-prompt (suggest/block via context); PreToolUse per-tool (deny with reason).[^7_9]


| Hook | Timing | Block Method | Use Case | Scope |
| :-- | :-- | :-- | :-- | :-- |
| UserPromptSubmit | Pre-prompt submit | Stdout inject/exit 2 erase | Skill gates, eval | Global/prompt-wide |
| PreToolUse | Pre-tool exec | JSON deny/stderr | Tool guards (git/Edit) | Per-tool (Bash/Edit) |

UserPromptSubmit for activation (80%); PreToolUse for safety (100%).[^7_10]
<span style="display:none">[^7_11][^7_12][^7_13][^7_14][^7_15]</span>

<div align="center">⁂</div>

[^7_1]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^7_2]: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

[^7_3]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^7_4]: https://claude-plugins.dev/skills/@blencorp/claude-code-kit/skill-developer

[^7_5]: https://www.youtube.com/watch?v=DQHFow2NoQc

[^7_6]: https://skills.pub/en/skills/diet103-claude-code-infrastructure-showcase::claude-code-infrastructure-showcase::-claude-skills-skill-developer::diet103

[^7_7]: https://dev.to/anand_rathnas_d5b608cc3de/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too-53cm

[^7_8]: https://www.reddit.com/r/ClaudeAI/comments/1rdx60b/when_claude_is_failing_keywords_phrases_to_look/

[^7_9]: https://code.claude.com/docs/en/hooks-guide

[^7_10]: https://github.com/anthropics/claude-code/issues/27365

[^7_11]: https://blog.scuti.jp/claude-skills-complete-guide-progressive-disclosure-implementation/

[^7_12]: https://mcpmarket.com/tools/skills/skill-error-correction

[^7_13]: https://www.linkedin.com/posts/michaelridland_the-progressive-disclosure-pattern-in-claude-activity-7421121437094064128-5IPz

[^7_14]: https://dev.to/mikelane/building-guardrails-for-ai-coding-assistants-a-pretooluse-hook-system-for-claude-code-ilj

[^7_15]: https://code.claude.com/docs/en/skills


---

# Progressive disclosure Level 3 detailed resources examples

Guardrail vs domain skill types differences
UserPromptSubmit hook implementation for skills
Session tracking in skill-rules.json to avoid repeats
Debugging skill activation failures in Claude Code

Progressive disclosure Level 3 loads on-demand resources (code/docs) via filesystem tools after Level 1 (YAML) and Level 2 (SKILL.md) match. Guardrail skills block/validate (e.g., PreToolUse gates); domain skills provide context (suggestive). Session tracking uses `.claude/hooks/state/*.json` to skip repeats; debug via eval harnesses and logs.[^8_1][^8_2][^8_3][^8_4]

## Level 3 Disclosure

Level 1: YAML (always; name/desc/triggers). Level 2: SKILL.md (~500 lines; core logic). Level 3: `!glob .claude/skills/[skill]/resources/*.md` or bash fetches code/docs only when needed.[^8_5][^8_1]

Examples:

- PR reviewer: SKILL.md plans; Level 3 reads `pr-template.md` for structure.[^8_6]

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

- Hook debugger: Level 3 loads `examples/blocking-hooks.md` post-match.[^8_5]


## Skill Types Comparison

Guardrail: Enforcement-focused (block/warn via hooks). Domain: Knowledge (suggest context).[^8_3]


| Type | Purpose | Enforcement | Triggers | Example |
| :-- | :-- | :-- | :-- | :-- |
| Guardrail | Block/validate actions | block/warn (PreToolUse) | Destructive (git --force) | Skill("safe-git") first |
| Domain | Provide expertise | suggest (UserPromptSubmit) | Files/keywords (hooks/*.py) | Hook review patterns |

## UserPromptSubmit for Skills

Injects "EVALUATE: Use hook-reviewer?" pre-prompt; blocks on no Skill() for gates.[^8_7][^8_8]

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

settings.json: `"UserPromptSubmit": [{"hooks": [{"type":"command","command":"./skill-gate.sh"}]}]`[^8_8]

## Session Tracking

`skipConditions.sessionMarker`: Hooks check/write `.claude/hooks/state/skills-used-{session_id}.json`.[^8_4][^8_3]

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

Hook: `jq -e '.hooks_reviewed' state.json || echo '{"hooks_reviewed":true}' > state.json` skips if marked.[^8_4]

## Debugging Failures

Use skill-debugging-assistant or harness: `/p "test 50 prompts: hooks debug"`; check logs `/hooks`, token budget (`/context`), triggers.[^8_9][^8_10]

- Logs: `~/.claude/logs/` for hook firings.
- Test: Rephrase (exact keywords win).
- Metrics: Track % activation; forced-eval baselines.
- Common: Budget overflow (>16k descs), vague descs, no eval hooks.[^8_9]
<span style="display:none">[^8_11][^8_12][^8_13][^8_14][^8_15]</span>

<div align="center">⁂</div>

[^8_1]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^8_2]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

[^8_3]: https://claude-plugins.dev/skills/@dwalleck/catalyst/skill-developer

[^8_4]: https://claude-plugins.dev/skills/@PaulRBerg/dot-claude/skill-creator

[^8_5]: https://docs.claude-mem.ai/progressive-disclosure

[^8_6]: https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/

[^8_7]: https://code.claude.com/docs/en/hooks

[^8_8]: https://github.com/disler/claude-code-hooks-mastery

[^8_9]: https://claude-plugins.dev/skills/@Exploration-labs/Nates-Substack-Skills/skill-debugging-assistant

[^8_10]: https://agent-skills.md/skills/0xDarkMatter/claude-mods/claude-code-debug

[^8_11]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^8_12]: https://jonimms.com/claude-code-rules-skills-agents-explained/

[^8_13]: https://www.youtube.com/watch?v=DQHFow2NoQc

[^8_14]: https://mcpmarket.com/tools/skills/claude-skill-architect-1770966284688

[^8_15]: https://claude-plugins.dev/skills/@authenticwalk/mybibletoolbox-code/progressive-disclosure


---

# Examples of domain skill trigger patterns in skill-rules.json

How to set up PreToolUse hook for skill safety
YAML frontmatter best practices for Level 1 disclosure
Subagents vs skills configuration differences
Debugging low skill activation rates in Claude Code

Domain skills use suggestive triggers like keywords ("hooks", "debug") or intent regex for guidance; examples include patterns for React patterns or API design. PreToolUse for skill safety blocks tools until Skill() via JSON deny on unsafe calls. YAML Level 1 prioritizes name/desc (1024 chars max) with trigger keywords; subagents fork context while skills inline or fork.[^9_1][^9_2]

## Domain Trigger Patterns

From skill-rules.json examples: Suggestive for non-blocking knowledge.[^9_2]

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

Level 1 (always-loaded): name (lowercase-hyphen), description (trigger keywords, <1024 chars).[^9_1]

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

Subagents: Independent context, skills field preloads others; skills: Inline/fork into main.[^9_3]


| Config | Subagents | Skills |
| :-- | :-- | :-- |
| Context | Separate window | Inline or fork |
| YAML | .claude/agents/name.yaml (skills: [...]) | SKILL.md frontmatter |
| Invoke | Delegate or /agent | /skill or auto |
| Use | Multi-step expert | Task/reference |

## Debugging Activation

Eval 200+ prompts; check /context budget, logs.[^9_4][^9_5]

- Harness: "test hooks debug" x50.
- Logs: /hooks, ~/.claude/logs.
- Fixes: Forced-eval hook, exact keywords, <16k desc total.[^9_4]
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_6][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://code.claude.com/docs/en/skills

[^9_2]: https://claude-plugins.dev/skills/@blencorp/claude-code-kit/skill-developer

[^9_3]: https://www.eesel.ai/blog/skills-vs-subagent

[^9_4]: https://forums.sobergroup.com/forum/services/website-development/16304-claude-code-skills-not-triggering-2-fixes-for-100-activation

[^9_5]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^9_6]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^9_7]: https://github.com/glebis/claude-skills

[^9_8]: https://aiblewmymind.substack.com/p/claude-skills-36-examples

[^9_9]: https://cdn.egghead.io/lessons/secure-your-claude-skills-with-custom-pre-tool-use-hooks~dhqko

[^9_10]: https://skywork.ai/blog/ai-agent/how-to-create-claude-skill-step-by-step-guide/

[^9_11]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^9_12]: https://dev.to/mikelane/building-guardrails-for-ai-coding-assistants-a-pretooluse-hook-system-for-claude-code-ilj

[^9_13]: https://repovive.com/roadmaps/claude-code/claude-md-skills-hooks-mcp/skill-frontmatter-fields

[^9_14]: https://www.youngleaders.tech/p/claude-skills-commands-subagents-plugins

[^9_15]: https://www.linkedin.com/posts/carlvellotti_skills-are-claude-codes-most-powerful-feature-activity-7429946350034747392-rxRN

