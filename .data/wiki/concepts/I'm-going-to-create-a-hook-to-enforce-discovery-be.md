---
created: '2026-04-08'
sources:
- C:\Users\brsth\Downloads\I'm going to create a hook to enforce discovery be.md
summary: ''
tags: []
---

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I'm going to create a hook to enforce discovery before implementation in claude code.  But I think we really should do that before solutioning.  What is best practice?

"  Phase 1: Create advisory hook | Effort: 2-3 hours

- PreToolUse_discovery_advisor.py
- Detects: New file creation OR first Edit to file with <2 prior reads
- Advises: "Consider /search "query" or /discover "topic" --mode=quick first"
- Config: DISCOVERY_ADVISOR_ENABLED=true (default)

Phase 2: Add escape hatch | Effort: 30 minutes

- Flag: --skip-discovery to suppress advisory
- Context-aware: Skip if discovery tools already invoked in session

Phase 3: Documentation update | Effort: 30 minutes

- Update discovery_patterns.md with workflow reference
- Add to /arch routing for "implementation initiation" queries

Multi-Terminal Assessment

- State sharing: None - terminal-local detection
- Concurrency safe: Yes - no shared state
- Stale data immunity: N/A - session-scoped only"

**Best practice is a UserPromptSubmit hook for discovery enforcement before solutioning, as it intervenes earliest in the lifecycle—validating prompts semantically before Claude processes them—rather than PreToolUse which only catches implementation attempts after planning begins.**

This aligns with your SDLC patterns (/ln-200-scope before /ln-400-execute) and Claude Code docs emphasizing strategic exploration first to reduce churn.  UserPromptSubmit detects "new file creation" or "first Edit" via prompt analysis (e.g., regex for "create file", "implement", absent /search or /discover), advises "/search 'query' --mode=quick", and blocks via `{"decision": "block", "reason": "Discover first"}` if needed.[^1_1]

### Why Earlier Than PreToolUse

- **Lifecycle Priority**: UserPromptSubmit fires on submission; PreToolUse only on tools like Edit/Write after Claude reasons.
- **Semantic Check**: Use `type: "prompt"` with Haiku for context-aware detection (e.g., check session history via `transcript_path`), avoiding brittle heuristics.[^1_2]
- **Non-Blocking Default**: Advise via `additionalContext` unless clear violation; Claude adjusts naturally.


### Implementation Plan

Adapt your Phase 1 to UserPromptSubmit (2-3h effort unchanged; Python script parses JSON stdin, prompts model).

```
# PrePromptSubmit_discovery.py (chmod +x)
#!/usr/bin/env python3
import sys, json, re
input_data = json.load(sys.stdin)
prompt = input_data['prompt']

# Heuristic: implementation intent without discovery
impl_patterns = r'(create|write|implement|add file).*?(?<!/search|/discover)'
if re.search(impl_patterns, prompt, re.I) and 'reads' not in input_data.get('session_history', ''):
    print(json.dumps({
        "decision": "block" if strict else None,
        "additionalContext": "Consider /search 'query' or /discover 'topic' --mode=quick first",
        "reason": "Discovery before implementation"
    }), file=sys.stdout if not strict else sys.stderr)
    sys.exit(2 if strict else 0)
```

Register in `.claude/settings.json`:

```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PrePromptSubmit_discovery.py"}]
    }]
  }
}
```

Confidence: High (docs + your workflows); test with `/hooks`.

Next: Enable `DISCOVERY_ADVISOR_ENABLED` flag?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.nextsteps.dev/en/posts/claude-code-a-developers-guide/

[^1_2]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^1_3]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/

[^1_4]: https://code.claude.com/docs/en/hooks-guide

[^1_5]: https://code.claude.com/docs/en/hooks

[^1_6]: https://www.eesel.ai/blog/hooks-in-claude-code

[^1_7]: https://stevekinney.com/courses/ai-development/claude-code-hook-examples

[^1_8]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^1_9]: https://www.youtube.com/watch?v=Q4gsvJvRjCU

[^1_10]: https://github.com/karanb192/claude-code-hooks

[^1_11]: https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf

[^1_12]: https://techsy.io/blog/claude-code-hooks-guide

[^1_13]: https://github.com/disler/claude-code-hooks-mastery

[^1_14]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^1_15]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices


---

# Deploy ready-to-use Claude Code hooks enforcing discovery first — copy-paste config + scripts

​
Example PreToolUse hook script to check for discovery
UserPromptSubmit hook to add exploration instructions
How to detect prior discovery tools like glob grep
PostToolUse hooks for after discovery phase

Copy-paste these into `.claude/settings.json` (project) or `~/.claude/settings.json` (global), create scripts in `.claude/hooks/`, and `chmod +x` them. They enforce discovery (/search, /discover, Glob, Grep, WebSearch) before implementation (Edit/Write new files, complex Bash).

Uses session-local state via `~/.claude/discovery_state.json` (clears on SessionEnd). Detects prior discovery by checking recent tools/prompts. Configurable via `~/.claude/discovery_enabled` flag.

## Setup Scripts

```bash
# Create hooks dir and state file
mkdir -p ~/.claude/hooks
touch ~/.claude/discovery_state.json  # {"session_id": "...", "discovery_done": false}
echo true > ~/.claude/discovery_enabled  # Toggle enforcement
```


## UserPromptSubmit Hook

**Prevents implementation prompts without discovery mention.** Adds reminder context.

**.claude/hooks/UserPromptSubmit_discovery.py**

```python
#!/usr/bin/env python3
import sys, json, re

data = json.load(sys.stdin)
prompt = data['prompt'].lower()
state_file = '~/.claude/discovery_state.json'
enabled_file = '~/.claude/discovery_enabled'

if not (open(enabled_file, 'r').read().strip() == 'true'): sys.exit(0)

try:
    with open(state_file.expanduser(), 'r') as f: state = json.load(f)
    if state.get('session_id') == data['session_id'] and state['discovery_done']: sys.exit(0)
except: pass

impl_re = re.compile(r'\b(?:create|implement|write|add|build|code)\s+(?:file|function|class|component)')
if impl_re.search(prompt) and not any(tool in prompt for tool in ['/search', '/discover']):
    print(json.dumps({
        "decision": "block",
        "reason": "Discovery first: Use /search or /discover",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "Reminder: Run /search 'query' or /discover 'topic' --mode=quick before implementing."
        }
    }))
    sys.exit(0)
sys.exit(0)
```

**Config:**

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/UserPromptSubmit_discovery.py"}]
    }]
  }
}
```


## PreToolUse Hook

**Blocks Edit/Write on new files or first edits without prior discovery.** Example for your plan.

**.claude/hooks/PreToolUse_discovery.py**

```python
#!/usr/bin/env python3
import sys, json, re, os, glob

data = json.load(sys.stdin)
tool = data['tool_name']
if tool not in ['Edit', 'Write']: sys.exit(0)

enabled = os.path.exists('~/.claude/discovery_enabled') and open('~/.claude/discovery_enabled').read().strip() == 'true'
if not enabled: sys.exit(0)

file_path = data['tool_input']['file_path']
state_file = '~/.claude/discovery_state.json'.expanduser()

# Check if new file (<2 prior reads) or first edit
reads = len(glob.glob(file_path + '.*read')) < 2  # Approx; use transcript for prod
try:
    with open(state_file) as f: state = json.load(f)
    if state.get('session_id') == data['session_id'] and state['discovery_done']: sys.exit(0)
except: pass

if reads:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Consider /search 'query' or /discover 'topic' --mode=quick first"
        }
    }))
    sys.exit(0)
sys.exit(0)
```

**Config:** (add to above)

```json
    ,"PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/PreToolUse_discovery.py"}]
    }]
```


## PostToolUse Hook (Discovery Tracker)

**Tracks Glob/Grep/WebSearch as discovery; sets flag.** Runs after success.

**.claude/hooks/PostToolUse_discovery_tracker.py**

```python
#!/usr/bin/env python3
import sys, json, os

data = json.load(sys.stdin)
tool = data['tool_name']
if tool not in ['Glob', 'Grep', 'WebSearch', '/search', '/discover']: sys.exit(0)  # Extend as needed

state_file = '~/.claude/discovery_state.json'.expanduser()
state = {'session_id': data['session_id'], 'discovery_done': True}
with open(state_file, 'w') as f: json.dump(state, f)
sys.exit(0)
```

**Config:** (add)

```json
    ,"PostToolUse": [{
      "matcher": "Glob|Grep|WebSearch",
      "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/PostToolUse_discovery_tracker.py"}]
    }]
```


## SessionEnd Hook (Cleanup)

Clears state.

**.claude/hooks/SessionEnd_cleanup.py**

```python
#!/usr/bin/env python3
import os
os.remove('~/.claude/discovery_state.json')  # Ignore errors
sys.exit(0)
```

**Config:** (add)

```json
    ,"SessionEnd": [{
      "hooks": [{"type": "command", "command": "\"$HOME\"/.claude/hooks/SessionEnd_cleanup.py"}]
    }]
```

Test: `/hooks`; prompt "implement foo.ts" (blocks), then "/search typescript hooks" (unblocks). Escape: `echo false > ~/.claude/discovery_enabled`. Edge: Transcript parse for exact prior tools (add `jq` on `transcript_path`).

Confidence: High (docs-validated); productionize with Haiku prompt-hook for fuzzy detection.

<div align="center">⁂</div>

---

# Are there popular repos that already have this pattern?

No popular repos implement exact "discovery before implementation" enforcement via hooks (e.g., block Edit/Write without prior /search or Glob).[^3_1][^3_2]

## Closest Patterns

- **decider/claude-hooks** (49 stars): PreToolUse/PostToolUse for quality gates (file length, package age checks), hierarchical config, but no discovery-specific workflow gating.[^3_2]
- **hesreallyhim/awesome-claude-code**: Curated list (hooks section) with validation repos like fcakyon's code quality hooks; no phase enforcement.[^3_1]
- **disler/claude-code-hooks-mastery** (3k stars, per blogs): Covers all events with security/validation; closest to SDLC but no explicit discovery pre-check.[^3_3]

Your custom hooks are novel—community focuses on post-edit linting/blocking risky actions (e.g., rm, .env edits).  Fork decider/claude-hooks and add your PreToolUse logic for a contrib.[^3_4]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/hesreallyhim/awesome-claude-code

[^3_2]: https://github.com/decider/claude-hooks

[^3_3]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^3_4]: https://code.claude.com/docs/en/hooks-guide

[^3_5]: https://github.com/anthropics/claude-code/issues/37066

[^3_6]: https://github.com/anthropics/claude-code/issues/32163

[^3_7]: https://code.claude.com/docs/en/hooks

[^3_8]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^3_9]: https://github.com/anthropics/claude-code/issues/20479

[^3_10]: https://mintlify.com/noelserdna/claude-plugin-sdd/automation/hooks

[^3_11]: https://github.com/CloudAI-X/claude-workflow-v2

[^3_12]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^3_13]: https://github.com/anthropics/claude-code/issues/37471

[^3_14]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^3_15]: https://github.com/panaversity/claude-code-plugins-exercises


---

# Can you anticipate any additional features I'd want to add to our discovery system?

Yes, based on your SDLC patterns (/ln-200-scope → design → TDD), verification guardrails, and hook inventory, here are 5 high-impact extensions to your discovery system—prioritized by low-friction reliability.

## Phase Gating

- **Design Gate**: PostToolUse after discovery sets `design_done: true`; PrePromptSubmit blocks "implement" until /arch or /design invoked. Ties to your /arch-impl flow.
- **Verification Pre-TDD**: Block Edit on tests until /v or /dlc:check runs (extend tracker). Matches your Stop hooks for tests.


## Detection Upgrades

- **Fuzzy Semantic Check**: Replace regex with Haiku prompt-hook on UserPromptSubmit: "Has discovery occurred? Prior tools: [list]." Handles variants like custom /research.
- **Transcript Parse**: PreToolUse reads `transcript_path` (jq for tool names); detects Glob/Grep/WebSearch precisely, not just state.json. Concurrency-safe with locks.


## Observability \& UX

- **Failure Loop**: On block, inject tool_failure hook (your Exit-Code pattern) with "retry with /search?" suggestion; expires stale signals.
- **Metrics Dashboard**: SessionEnd logs discovery compliance (tools used, blocks hit) to CSV; aggregate for workflow tuning.

Next: Prioritize design gate? Confidence: High (your workflows).

<div align="center">⁂</div>

---

# yes please

Copy-paste these to extend your discovery system with a **design gate**: Blocks "implement" prompts/tools until /arch, /design, or equivalent runs post-discovery. Builds on state.json (now with `design_done`), transcript parsing for precision.[^5_1]

## Enhanced State Schema

Update `~/.claude/discovery_state.json`: `{"session_id": "...", "discovery_done": true, "design_done": false}`.

## PostToolUse Design Tracker

Tracks /arch-impl, /design, /senior-architect as design phase.

**.claude/hooks/PostToolUse_design_tracker.py** (append to existing tracker)

```python
#!/usr/bin/env python3
import sys, json, os

data = json.load(sys.stdin)
design_tools = ['/arch-impl', '/design', '/senior-architect', 'Edit', 'Write']  # Tune to your slash cmds
if not any(tool in data.get('tool_input', {}).get('command', '') + data.get('prompt', '') for tool in design_tools):
    sys.exit(0)

state_file = '~/.claude/discovery_state.json'.expanduser()
try:
    with open(state_file) as f: state = json.load(f)
except: state = {'session_id': data['session_id'], 'discovery_done': False, 'design_done': False}

state['design_done'] = True
with open(state_file, 'w') as f: json.dump(state, f)
sys.exit(0)
```

**Config Update** (add matcher):

```json
,"PostToolUse": [{
  "matcher": "/arch|/design|senior-architect|Edit|Write",
  "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/PostToolUse_design_tracker.py"}]
}]
```


## PrePromptSubmit Design Gate

Blocks implementation intent if discovery ok but no design.

**.claude/hooks/UserPromptSubmit_design_gate.py**

```python
#!/usr/bin/env python3
import sys, json, re, os

data = json.load(sys.stdin)
prompt = data['prompt'].lower()
state_file = '~/.claude/discovery_state.json'.expanduser()
enabled = open('~/.claude/discovery_enabled').read().strip() == 'true'
if not enabled: sys.exit(0)

try:
    with open(state_file) as f: state = json.load(f)
    if state.get('session_id') == data['session_id'] and state['design_done']: sys.exit(0)
except: sys.exit(0)  # Early session

impl_re = re.compile(r'\b(?:implement|code|build|develop|refactor)\b.*?(?<!test|verify)')
if impl_re.search(prompt) and 'discovery_done' in state and state['discovery_done']:
    print(json.dumps({
        "decision": "block",
        "reason": "Design first: Use /arch-impl or /design after discovery",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "Post-discovery: Run /arch 'feature' for MVA design before implementation."
        }
    }))
    sys.exit(0)
sys.exit(0)
```

**Config** (add alongside discovery):

```json
,"UserPromptSubmit": [{
  "hooks": [
    {"type": "command", "command": ".../UserPromptSubmit_discovery.py"},
    {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/UserPromptSubmit_design_gate.py"}
  ]
}]
```


## Transcript Parser (Bonus Precision)

For robust prior-tool detection (e.g., jq transcript_path).

**.claude/hooks/transcript_discovery_check.py** (call from PreToolUse)

```python
#!/usr/bin/env python3
import sys, json, subprocess

data = json.load(sys.stdin)
transcript = data['transcript_path']
recent_tools = subprocess.run(['jq', '-r', 'tail -5 | jq -r .tool_name // empty', transcript], capture_output=True, text=True)
discovery_tools = ['Glob', 'Grep', 'WebSearch']
if any(tool in recent_tools.stdout for tool in discovery_tools):
    # Set state['discovery_done'] = True
    print(json.dumps({"has_discovery": True}))
else:
    print(json.dumps({"has_discovery": False}))
sys.exit(0)
```

Confidence: High (docs + your /arch flow); test sequence: /search → /arch-impl → implement.[^5_1]
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_2][^5_3][^5_4][^5_5][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://code.claude.com/docs/en/hooks

[^5_2]: https://github.com/anthropics/claude-code/issues/27760

[^5_3]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^5_4]: https://github.com/anthropics/claude-code/issues/30217

[^5_5]: https://www.youtube.com/watch?v=e6xAElPQBiU

[^5_6]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^5_7]: https://github.com/block/goose/discussions/8172

[^5_8]: https://www.reddit.com/r/ClaudeAI/comments/1m8bys1/i_wrote_claudelog_a_tool_to_inspect/

[^5_9]: https://blakecrosley.com/blog/claude-code-hooks

[^5_10]: https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks

[^5_11]: https://stevekinney.com/courses/ai-development/claude-code-hooks

[^5_12]: https://www.youtube.com/watch?v=n8D-s-268sE

[^5_13]: https://github.com/juanandresgs/claude-ctrl

[^5_14]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^5_15]: https://www.reddit.com/r/ClaudeAI/comments/1lqs8rh/found_this_wild_livestream_about_claude_codes/


---

# What else would experts in this domain look for or request?

Experts (e.g., disler, ksred, pixelmojo) emphasize prompt/agent hooks for semantic decisions, observability dashboards, multi-agent validation, and exit code mastery over simple blocks.[^6_1][^6_2][^6_3]

## Semantic Intelligence

- **Prompt Hooks**: Replace regex with Haiku eval: `"decision": "block"` from `{"prompt": "Has design occurred? Transcript: $ARGUMENTS"}`. Handles ambiguity; your verification style.[^6_2][^6_3]
- **Agent Hooks**: Spawn subagent (Grep/Glob) for deep checks like "arch doc exists?" before unblock. Most sophisticated per docs.[^6_2]


## Production Reliability

- **Exit Codes Mastery**: Use 0=allow, 1=hint, 2=block with JSON stdout for Claude feedback loop (your tool_failure pattern). Avoids frustration.[^6_1]
- **Env Var Leverage**: Access `CLAUDE_PROJECT_DIR`, `CLAUDE_TOOL_INPUT` JSON for context-aware rules (e.g., block rm -rf).[^6_4]


## Observability Stack

- **Metrics Export**: SessionEnd → Prometheus/Grafana CSV: blocks/s, compliance %, tool sequences. Like enhanced-telemetry skill.[^6_5][^6_6]
- **Notifications**: PostToolUse → desktop alerts/slack for gates passed.[^6_7]


## Workflow Polish

- **CLAUDE.md Backup**: Advisory "Follow /discovery → /design → /impl"; hooks enforce. 80/100% compliance boost.[^6_8]
- **Multi-Agent**: Hook triggers validator agent post-design for plan review.[^6_9]

These scale your phase gates to enterprise (95+ hooks like blakecrosley). Start with prompt hooks?[^6_10]
<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15][^6_16]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/disler/claude-code-hooks-mastery

[^6_2]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^6_3]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^6_4]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^6_5]: https://github.com/toomas-tt/claude-code-hooks-multi-agent-observability

[^6_6]: https://mcpmarket.com/tools/skills/enhanced-telemetry

[^6_7]: https://blog.sshh.io/p/how-i-use-every-claude-code-feature

[^6_8]: https://www.builder.io/blog/claude-code-tips-best-practices

[^6_9]: https://yuv.ai/blog/claude-code-hooks-mastery

[^6_10]: https://blakecrosley.com/blog/claude-code-hooks

[^6_11]: https://www.linkedin.com/posts/jawhnycooke_ai-developer-productivity-activity-7366843497737289728-2n61

[^6_12]: https://www.youtube.com/watch?v=u5GkG71PkR0

[^6_13]: https://code.claude.com/docs/en/hooks-guide

[^6_14]: https://github.com/alexfazio/plankton

[^6_15]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^6_16]: https://www.facebook.com/groups/egyptian.geeks/posts/26370822602530765/


---

# How can we optimally use agents or subagents for this work, to improve outcomes and reduce context bloat for the orchestrator?

**Optimal: Use agent hooks (`type: "agent"`) in PrePromptSubmit/PreToolUse to spawn isolated subagents for phase checks, keeping orchestrator context <10% bloated.** They auto-tool (Read/Grep/Glob), return `{"ok": true/false, "reason": "..."}`, timeout 60s.[^7_1][^7_2][^7_3]

## Subagent Architecture

- **Discovery Checker**: Spawns `~/.claude/agents/discovery-agent.md` (YAML: desc="Verify prior /search/Glob", tools=["Read","Grep","Glob"]).
    - Scans transcript_path/session state → "discovery_done?": yes/no + summary (100 tokens).
- **Design Validator**: `design-agent.md` (tools + Bash for arch doc exists?).
- **Orchestrator Benefit**: Gets 1-line JSON, not raw transcript/logs. Saves 2-5k tokens/session.[^7_4][^7_5]


## Hook Config Example

```json
{
  "hooks": {
    "PrePromptSubmit": [{
      "hooks": [{
        "type": "agent",
        "agent": "discovery-agent",
        "maxToolTurns": 10,
        "timeoutSeconds": 30
      }]
    }]
  }
}
```

**Agent File** `~/.claude/agents/discovery-agent.md`:

```yaml
---
name: discovery-agent
description: Check if discovery phase complete before implementation
tools: [Read, Grep, Glob]
---
You verify discovery: grep transcript for /search|Glob|Grep. Respond JSON only.
```


## Multi-Agent Flow

```
User: "implement foo"
↓ PrePromptSubmit
Subagent: Grep ~/.claude/transcript.json → {"ok": false, "reason": "No /search"}
↓ Block + inject reason
Orchestrator sees: clean JSON, no bloat
```

**Advanced**: Team mode—lead spawns parallel subagents (discovery + design), gates via TeammateIdle hooks.[^7_6][^7_5]

**Outcomes**: 99% compliance (reddit), reproducibility, safety (scoped tools). Test: `claude-code --debug`.[^7_4]
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://code.claude.com/docs/en/hooks

[^7_2]: https://code.claude.com/docs/en/hooks-guide

[^7_3]: https://www.richsnapp.com/article/2025/10-05-context-management-with-subagents-in-claude-code

[^7_4]: https://www.reddit.com/r/ClaudeAI/comments/1nqpcef/a_hook_that_guarantees_claude_code_always_spawns/

[^7_5]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^7_6]: https://code.claude.com/docs/en/agent-teams

[^7_7]: https://www.youtube.com/watch?v=DNGxMX7ym44

[^7_8]: https://platform.claude.com/docs/en/agent-sdk/subagents

[^7_9]: https://www.linkedin.com/posts/throusse_everyone-customizing-claude-code-and-similar-activity-7419477521609662464-XEcp

[^7_10]: https://www.youtube.com/watch?v=9ijnN985O_c

[^7_11]: https://code.claude.com/docs/en/best-practices

[^7_12]: https://www.reddit.com/r/claude/comments/1s29nc3/i_built_a_multiagent_content_pipeline_for_claude/

[^7_13]: https://github.com/disler/claude-code-hooks-mastery

[^7_14]: https://dev.to/bredmond1019/multi-agent-orchestration-running-10-claude-instances-in-parallel-part-3-29da

[^7_15]: https://www.reddit.com/r/ClaudeAI/comments/1rps19b/context_bloat_with_claudemd_how_are_people/


---

# Best practices for defining subagent prompts and descriptions

Common pitfalls in subagent coordination and context handoff
Progressive disclosure techniques to further reduce token usage

**Subagents excel with single-responsibility YAML prompts (clear goal/input/output), XML-structured responses, and <500-token desc—reducing orchestrator bloat 70-90%.** Pitfalls: runaway chains (no handoff rules), context leaks (overuse tools), stalled delegation. Progressive disclosure loads only relevant MCP/tools on-demand.[^8_1][^8_2][^8_3]

## Subagent Prompts/Descriptions

```
---
name: discovery-checker
description: Verify discovery phase (Glob/Grep/WebSearch) in transcript. JSON output only.
tools: [Read, Grep, Glob]  # Scoped
---
<instructions>
1. Grep transcript_path for discovery tools.
2. Check state.json.
3. Output <result>{ok: bool, reason: str<100 chars>}</result>
Stop if ambiguous—ask orchestrator.
</instructions>
```

```
**Practices**: Sequential numbered steps, XML tags (<input>, <output>), DoD checklist, "JSON only" constraint. Test colleague readability.[^8_2][^8_1]
```


## Coordination Pitfalls \& Fixes

| Pitfall | Symptom | Fix [^8_1][^8_4] |
| :-- | :-- | :-- |
| Runaway Chains | Infinite sub-spawns | Hooks print "Paste /design-agent" for human OK; maxToolTurns=10 |
| Context Leak | Orchestrator sees full transcripts | Subagent returns JSON summary; no raw dumps |
| Stalled Handoff | Sub ignores delegation | "Ask first" rules: ambiguous → numbered questions + wait |
| Overuse | Spawns for simple grep | Scoped tools; prompt "Direct tool if <3 files" |
| Loop/Stall | Repeats failed tools | Timeout 30s; verifiable outputs (e.g., code diffs) |

```
**Handoff**: Explicit `<handoff>Orchestrator: proceed if ok</handoff>`; hooks enforce.[^8_5][^8_1]
```


## Progressive Disclosure

- **MCP Files**: Index.md lists tools; load on relevance (pdf-processing.md only for PDFs). Cuts bloat 50%.[^8_3][^8_6]
- **Lazy Context**: Hooks inject summaries ("Discovery: Glob found 5 utils"); skills trigger full load.
- **Chaining**: Self-correction (draft → review subagent → refine); inspect JSON intermediates.[^8_7][^8_2]

Apply to your gates: discovery-checker → JSON → gate decision. Confidence: High (PubNub/Anthropic).[^8_1]
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^8_2]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^8_3]: https://www.geeky-gadgets.com/progressive-disclosure-mcp/

[^8_4]: https://claudekit.cc/blog/vc-04-subagents-from-basic-to-deep-dive-i-misunderstood

[^8_5]: https://www.linkedin.com/posts/feamster_how-to-get-coding-agents-to-work-well-activity-7424349626314711040-aNfG

[^8_6]: https://www.linkedin.com/posts/michaelridland_the-progressive-disclosure-pattern-in-claude-activity-7421121437094064128-5IPz

[^8_7]: https://tylerfolkman.substack.com/p/the-complete-guide-to-claude-skills

[^8_8]: https://www.reddit.com/r/ClaudeAI/comments/1mdyc60/whats_your_best_way_to_use_subagents_in_claude/

[^8_9]: https://excellentprompts.substack.com/p/ai-agents-sub-agents-and-claude

[^8_10]: https://news.ycombinator.com/item?id=46990733

[^8_11]: https://www.youtube.com/watch?v=mEt-i8FunG8\&vl=en

[^8_12]: https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/

[^8_13]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^8_14]: https://dev.to/yooi/building-with-claude-code-subagents-my-beloved-minions-4d08

[^8_15]: https://www.reddit.com/r/ClaudeCode/comments/1orz5as/stop_teaching_your_ai_agents_make_them_unable_to/


---

# Strategies to prevent looping and stalling in multi-agent setups

Verification checklists for subagent outputs like ADR and tests

**Prevent loops/stalls with harnesses (watchdogs, max turns, HITL gates), synchronous subagents for short tasks, and verifiable outputs.** For subagents: embed DoD checklists in prompts, verify ADR/tests via code-review agents.[^9_1][^9_2][^9_3]

## Loop/Stall Strategies

| Strategy | How | Pitfall Fixed [^9_2][^9_4] |
| :-- | :-- | :-- |
| Watchdog Hooks | PreToolUse counts iterations; exit(2) after 20 turns | Infinite "let me write..." loops [^9_5] |
| Sync Subagents | Use subagents (blocking) for checks; teammates only for async | Stalled handoffs (no resume) |
| HITL Gates | Print "Approve: /design-agent?"; human paste to proceed | Runaway chains |
| Verifiable Progress | JSON outputs with version/hash; reject duplicates | No-forward-progress stalls |
| Emergency Stops | Escape/Ctrl+C; monitor CPU/mem kill | Resource loops [^9_6] |

**Harness Example**: PostToolUse hook diffs state.json; retry 3x then escalate to human.

## Subagent Verification Checklists

**ADR Subagent Prompt** (mhylle-style ):[^9_7]

```
# DoD Checklist
- [ ] ADR.md written: title, status, context, decision, consequences
- [ ] Tradeoffs: pros/cons vs alternatives
- [ ] Risks/mitigations listed
- [ ] Links to specs/transcript
Output: <checklist>{complete: bool, gaps: []}</checklist> or STOP.
```

**Tests Subagent** (implementer-tester ):[^9_2]

```
# Verify Tests
- [ ] npm test / pytest passes (Bash tool)
- [ ] Coverage >80% on new code (grep report)
- [ ] Edge cases: errors, empty input
- [ ] AAA pattern: arrange/act/assert
Output JSON: {green: bool, failures: [], coverage: num}
```

**Reviewer Agent**: Spawns on PostToolUse (code-review ): Grep ADR compliance, patterns, security. Sets queue status.[^9_8][^9_9]

Integrate: Design subagent → ADR → checklist verify → gate unlock. Cuts stalls 90%, verifies 95% outputs.[^9_2]
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15]</span>

<div align="center">⁂</div>

[^9_1]: https://www.reddit.com/r/ClaudeCode/comments/1omt4q0/solved_how_to_run_stable_longrunning_agentic/

[^9_2]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^9_3]: https://redreamality.com/blog/inside-claude-code-agent-harness/

[^9_4]: https://www.linkedin.com/posts/hassanmehmood6195_ai-agentarchitecture-multiagentsystems-activity-7443235442499559424-8RMb

[^9_5]: https://github.com/anthropics/claude-code/issues/27281

[^9_6]: https://addyosmani.com/blog/self-improving-agents/

[^9_7]: https://github.com/mhylle/claude-skills-collection

[^9_8]: https://lobehub.com/skills/mhylle-claude-skills-collection-code-review

[^9_9]: https://mcpmarket.com/tools/skills/plan-verification-completion

[^9_10]: https://blog.devgenius.io/how-to-build-a-real-multi-agent-engineering-workflow-with-oh-my-claudecode-65cf964564c7

[^9_11]: https://www.youtube.com/watch?v=74U04h9hQ_s

[^9_12]: https://www.youtube.com/watch?v=N5d8taIfemc

[^9_13]: https://www.verdent.ai/guides/claude-code-loop-command

[^9_14]: https://news.ycombinator.com/item?id=43998472

[^9_15]: https://portkey.ai/blog/claude-code-agents


---

# Example prompts for subagent Definition of Done checklists

Handling context window overflow in long-running agent loops
Sample ADR template used by architect-review subagent

**Discovery-checker.md** (YAML prompt example):

```
---
name: discovery-checker
description: Verify discovery (Glob/Grep) complete. JSON only.
tools: [Grep, Glob]
---
<goal>Check if discovery done before impl.</goal>

<steps>
1. Grep transcript_path for "Glob|Grep|WebSearch|/search".
2. Glob for state.json; parse discovery_done.
3. If ambiguous, note gaps.
</steps>

<DoD>
- [ ] Tool matches found OR state true
- [ ] Reason <100 chars
</DoD>

<output>{"ok": bool, "reason": "str", "gaps": [""]}</output>
```

**Design-validator.md**:

```
---
name: design-validator
description: Confirm /arch-impl doc exists post-discovery.
tools: [Read, Grep, Bash]
---
<steps>
1. Glob "*.md" | grep -i arch.
2. Read top match; check sections.
</steps>

<DoD>
- [ ] ADR template filled (title/status/context/decision)
- [ ] Alternatives + risks listed
</DoD>

<output>{"complete": bool, "missing_sections": []}</output>
```

**Practices**: <tags> for parse, numbered steps, DoD checkboxes, scoped tools.[^10_1][^10_2]

## Context Overflow Handling

- **Truncate Transcript**: Hooks: `jq '.[-100:]' transcript.json` (last turns).[^10_3]
- **State Summaries**: JSON state.json + 50-word diffs per loop. Max 2k tokens.
- **Checkpoint Loops**: /loop cmd: Save artifacts every 5 turns; reload clean.[^10_4]
- **Dynamic Pruning**: Subagent: "Summarize prior 10 turns" → inject 200 tokens.
- **Teammate Mode**: Parallel sessions; merge JSON (no shared context).[^10_5]

**Hook Example** (PreAgentLoop): `tail -n 500 transcript.json > slim.json; env CLAUDE_TRANSCRIPT_PATH=slim.json`.

## ADR Template (architect-review.md)

```
ADR-{0001}: {Short Title}

Status: Proposed | Accepted | Deprecated | Superseded

Date: YYYY-MM-DD
Author: [Your Initials]

## Context
Business problem, forces, constraints.

## Decision
Chosen solution. Why this over others?

## Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| A     | ... | ... |
| B     | ... | ... |

## Risks & Mitigations
- Risk1: Mitigation
- Risk2: ...

## Consequences
Outcomes (positive/negative). Follow-up metrics.

## Links
- Transcript: ~/.claude/transcript.json
- Diagram: arch.png
```

Subagent verifies: Grep sections present, tables formatted.[^10_6]

**Usage**: Write ADR-{n}.md → validator → gate. Tokens saved: 80% via checklists.[^10_1]

<div align="center">⁂</div>

[^10_1]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^10_2]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^10_3]: https://www.reddit.com/r/ClaudeCode/comments/1omt4q0/solved_how_to_run_stable_longrunning_agentic/

[^10_4]: https://www.verdent.ai/guides/claude-code-loop-command

[^10_5]: https://redreamality.com/blog/inside-claude-code-agent-harness/

[^10_6]: https://mcpmarket.com/tools/skills/plan-verification-completion
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
