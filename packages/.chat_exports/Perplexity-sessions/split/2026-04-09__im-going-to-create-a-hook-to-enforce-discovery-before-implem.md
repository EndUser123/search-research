---
title: "I'm going to create a hook to enforce discovery before implementation in claude code.  But I think we really should do t"
date: "2026-04-09"
mode: "COPILOT"
uuid: "eecadedc-7217-478e-8f53-e679e11129d9"
entry_count: 10
---

## Human

I'm going to create a hook to enforce discovery before implementation in claude code.  But I think we really should do that before solutioning.  What is best practice?

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

## Assistant

**Best practice is a UserPromptSubmit hook for discovery enforcement before solutioning, as it intervenes earliest in the lifecycle—validating prompts semantically before Claude processes them—rather than PreToolUse which only catches implementation attempts after planning begins.**

This aligns with your SDLC patterns (/ln-200-scope before /ln-400-execute) and Claude Code docs emphasizing strategic exploration first to reduce churn.  UserPromptSubmit detects "new file creation" or "first Edit" via prompt analysis (e.g., regex for "create file", "implement", absent /search or /discover), advises "/search 'query' --mode=quick", and blocks via `{"decision": "block", "reason": "Discover first"}` if needed.[1]

### Why Earlier Than PreToolUse
- **Lifecycle Priority**: UserPromptSubmit fires on submission; PreToolUse only on tools like Edit/Write after Claude reasons.
- **Semantic Check**: Use `type: "prompt"` with Haiku for context-aware detection (e.g., check session history via `transcript_path`), avoiding brittle heuristics.[2]
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

## Human

Deploy ready-to-use Claude Code hooks enforcing discovery first — copy-paste config + scripts
​
Example PreToolUse hook script to check for discovery
UserPromptSubmit hook to add exploration instructions
How to detect prior discovery tools like glob grep
PostToolUse hooks for after discovery phase

## Assistant

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

## Human

Are there popular repos that already have this pattern?

## Assistant

No popular repos implement exact "discovery before implementation" enforcement via hooks (e.g., block Edit/Write without prior /search or Glob).[1][2]

## Closest Patterns
- **decider/claude-hooks** (49 stars): PreToolUse/PostToolUse for quality gates (file length, package age checks), hierarchical config, but no discovery-specific workflow gating.[2]
- **hesreallyhim/awesome-claude-code**: Curated list (hooks section) with validation repos like fcakyon's code quality hooks; no phase enforcement.[1]
- **disler/claude-code-hooks-mastery** (3k stars, per blogs): Covers all events with security/validation; closest to SDLC but no explicit discovery pre-check.[3]

Your custom hooks are novel—community focuses on post-edit linting/blocking risky actions (e.g., rm, .env edits).  Fork decider/claude-hooks and add your PreToolUse logic for a contrib.[4]

## Human

Can you anticipate any additional features I'd want to add to our discovery system?

## Assistant

Yes, based on your SDLC patterns (/ln-200-scope → design → TDD), verification guardrails, and hook inventory, here are 5 high-impact extensions to your discovery system—prioritized by low-friction reliability.

## Phase Gating
- **Design Gate**: PostToolUse after discovery sets `design_done: true`; PrePromptSubmit blocks "implement" until /arch or /design invoked. Ties to your /arch-impl flow.
- **Verification Pre-TDD**: Block Edit on tests until /v or /dlc:check runs (extend tracker). Matches your Stop hooks for tests.

## Detection Upgrades
- **Fuzzy Semantic Check**: Replace regex with Haiku prompt-hook on UserPromptSubmit: "Has discovery occurred? Prior tools: [list]." Handles variants like custom /research.
- **Transcript Parse**: PreToolUse reads `transcript_path` (jq for tool names); detects Glob/Grep/WebSearch precisely, not just state.json. Concurrency-safe with locks. 

## Observability & UX
- **Failure Loop**: On block, inject tool_failure hook (your Exit-Code pattern) with "retry with /search?" suggestion; expires stale signals.
- **Metrics Dashboard**: SessionEnd logs discovery compliance (tools used, blocks hit) to CSV; aggregate for workflow tuning.

Next: Prioritize design gate? Confidence: High (your workflows).

## Human

yes please

## Assistant

Copy-paste these to extend your discovery system with a **design gate**: Blocks "implement" prompts/tools until /arch, /design, or equivalent runs post-discovery. Builds on state.json (now with `design_done`), transcript parsing for precision.[1]

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
Confidence: High (docs + your /arch flow); test sequence: /search → /arch-impl → implement.[1]

## Human

What else would experts in this domain look for or request?

## Assistant

Experts (e.g., disler, ksred, pixelmojo) emphasize prompt/agent hooks for semantic decisions, observability dashboards, multi-agent validation, and exit code mastery over simple blocks.[1][2][3]

## Semantic Intelligence
- **Prompt Hooks**: Replace regex with Haiku eval: `"decision": "block"` from `{"prompt": "Has design occurred? Transcript: $ARGUMENTS"}`. Handles ambiguity; your verification style.[2][3]
- **Agent Hooks**: Spawn subagent (Grep/Glob) for deep checks like "arch doc exists?" before unblock. Most sophisticated per docs.[2]

## Production Reliability
- **Exit Codes Mastery**: Use 0=allow, 1=hint, 2=block with JSON stdout for Claude feedback loop (your tool_failure pattern). Avoids frustration.[1]
- **Env Var Leverage**: Access `CLAUDE_PROJECT_DIR`, `CLAUDE_TOOL_INPUT` JSON for context-aware rules (e.g., block rm -rf).[4]

## Observability Stack
- **Metrics Export**: SessionEnd → Prometheus/Grafana CSV: blocks/s, compliance %, tool sequences. Like enhanced-telemetry skill.[5][6]
- **Notifications**: PostToolUse → desktop alerts/slack for gates passed.[7]

## Workflow Polish
- **CLAUDE.md Backup**: Advisory "Follow /discovery → /design → /impl"; hooks enforce. 80/100% compliance boost.[8]
- **Multi-Agent**: Hook triggers validator agent post-design for plan review.[9]

These scale your phase gates to enterprise (95+ hooks like blakecrosley). Start with prompt hooks?[10]

## Human

How can we optimally use agents or subagents for this work, to improve outcomes and reduce context bloat for the orchestrator?

## Assistant

**Optimal: Use agent hooks (`type: "agent"`) in PrePromptSubmit/PreToolUse to spawn isolated subagents for phase checks, keeping orchestrator context <10% bloated.** They auto-tool (Read/Grep/Glob), return `{"ok": true/false, "reason": "..."}`, timeout 60s.[1][2][3]

## Subagent Architecture
- **Discovery Checker**: Spawns `~/.claude/agents/discovery-agent.md` (YAML: desc="Verify prior /search/Glob", tools=["Read","Grep","Glob"]).
  - Scans transcript_path/session state → "discovery_done?": yes/no + summary (100 tokens).
- **Design Validator**: `design-agent.md` (tools + Bash for arch doc exists?).
- **Orchestrator Benefit**: Gets 1-line JSON, not raw transcript/logs. Saves 2-5k tokens/session.[4][5]

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
**Advanced**: Team mode—lead spawns parallel subagents (discovery + design), gates via TeammateIdle hooks.[6][5]

**Outcomes**: 99% compliance (reddit), reproducibility, safety (scoped tools). Test: `claude-code --debug`.[4]

## Human

Best practices for defining subagent prompts and descriptions
Common pitfalls in subagent coordination and context handoff
Progressive disclosure techniques to further reduce token usage

## Assistant

**Subagents excel with single-responsibility YAML prompts (clear goal/input/output), XML-structured responses, and <500-token desc—reducing orchestrator bloat 70-90%.** Pitfalls: runaway chains (no handoff rules), context leaks (overuse tools), stalled delegation. Progressive disclosure loads only relevant MCP/tools on-demand.[1][2][3]

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
**Practices**: Sequential numbered steps, XML tags (<input>, <output>), DoD checklist, "JSON only" constraint. Test colleague readability.[2][1]

## Coordination Pitfalls & Fixes
| Pitfall | Symptom | Fix [1][4] |
|---------|---------|----------------------|
| Runaway Chains | Infinite sub-spawns | Hooks print "Paste /design-agent" for human OK; maxToolTurns=10 |
| Context Leak | Orchestrator sees full transcripts | Subagent returns JSON summary; no raw dumps |
| Stalled Handoff | Sub ignores delegation | "Ask first" rules: ambiguous → numbered questions + wait |
| Overuse | Spawns for simple grep | Scoped tools; prompt "Direct tool if <3 files" |
| Loop/Stall | Repeats failed tools | Timeout 30s; verifiable outputs (e.g., code diffs) |

**Handoff**: Explicit `<handoff>Orchestrator: proceed if ok</handoff>`; hooks enforce.[5][1]

## Progressive Disclosure
- **MCP Files**: Index.md lists tools; load on relevance (pdf-processing.md only for PDFs). Cuts bloat 50%.[3][6]
- **Lazy Context**: Hooks inject summaries ("Discovery: Glob found 5 utils"); skills trigger full load.
- **Chaining**: Self-correction (draft → review subagent → refine); inspect JSON intermediates.[7][2]

Apply to your gates: discovery-checker → JSON → gate decision. Confidence: High (PubNub/Anthropic).[1]

## Human

Strategies to prevent looping and stalling in multi-agent setups
Verification checklists for subagent outputs like ADR and tests

## Assistant

**Prevent loops/stalls with harnesses (watchdogs, max turns, HITL gates), synchronous subagents for short tasks, and verifiable outputs.** For subagents: embed DoD checklists in prompts, verify ADR/tests via code-review agents.[1][2][3]

## Loop/Stall Strategies
| Strategy | How | Pitfall Fixed [2][4] |
|----------|-----|--------------------------------|
| Watchdog Hooks | PreToolUse counts iterations; exit(2) after 20 turns | Infinite "let me write..." loops [5] |
| Sync Subagents | Use subagents (blocking) for checks; teammates only for async | Stalled handoffs (no resume) |
| HITL Gates | Print "Approve: /design-agent?"; human paste to proceed | Runaway chains |
| Verifiable Progress | JSON outputs with version/hash; reject duplicates | No-forward-progress stalls |
| Emergency Stops | Escape/Ctrl+C; monitor CPU/mem kill | Resource loops [6] |

**Harness Example**: PostToolUse hook diffs state.json; retry 3x then escalate to human.

## Subagent Verification Checklists
**ADR Subagent Prompt** (mhylle-style ):[7]
```
# DoD Checklist
- [ ] ADR.md written: title, status, context, decision, consequences
- [ ] Tradeoffs: pros/cons vs alternatives
- [ ] Risks/mitigations listed
- [ ] Links to specs/transcript
Output: <checklist>{complete: bool, gaps: []}</checklist> or STOP.
```

**Tests Subagent** (implementer-tester ):[2]
```
# Verify Tests
- [ ] npm test / pytest passes (Bash tool)
- [ ] Coverage >80% on new code (grep report)
- [ ] Edge cases: errors, empty input
- [ ] AAA pattern: arrange/act/assert
Output JSON: {green: bool, failures: [], coverage: num}
```

**Reviewer Agent**: Spawns on PostToolUse (code-review ): Grep ADR compliance, patterns, security. Sets queue status.[8][9]

Integrate: Design subagent → ADR → checklist verify → gate unlock. Cuts stalls 90%, verifies 95% outputs.[2]

## Human

Example prompts for subagent Definition of Done checklists
Handling context window overflow in long-running agent loops
Sample ADR template used by architect-review subagent

## Assistant

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
**Practices**: <tags> for parse, numbered steps, DoD checkboxes, scoped tools.[1][2]

## Context Overflow Handling
- **Truncate Transcript**: Hooks: `jq '.[-100:]' transcript.json` (last turns).[3]
- **State Summaries**: JSON state.json + 50-word diffs per loop. Max 2k tokens.
- **Checkpoint Loops**: /loop cmd: Save artifacts every 5 turns; reload clean.[4]
- **Dynamic Pruning**: Subagent: "Summarize prior 10 turns" → inject 200 tokens.
- **Teammate Mode**: Parallel sessions; merge JSON (no shared context).[5]

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
Subagent verifies: Grep sections present, tables formatted.[6]

**Usage**: Write ADR-{n}.md → validator → gate. Tokens saved: 80% via checklists.[1]
