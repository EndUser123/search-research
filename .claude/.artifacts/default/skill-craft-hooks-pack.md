# SKILL PACK: skill-craft + Hooks

**Generated:** 2026-04-23
**Source:** P:/.claude/skills/skill-craft/ + P:/.claude/hooks/
**Mode:** full (implementation included)

---

## FILE INDEX

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill orchestrator (5-phase pipeline: diagnosing → planning → executing → evaluating → gating) |
| `index.html` | HTML artifact page with mermaid diagrams |
| `pipeline.html` | Pipeline visualization |
| `eval_sets/default.json` | Evaluation set for fidelity testing |

### Hooks (Relevant to skill-craft)

| File | Description |
|------|-------------|
| `StopHook_skill_execution_gate.py` | Global skill execution gate — enforces skill workflow, blocks prose-only responses |
| `PreToolUse_skill_pattern_gate.py` | Primary defense for skill workflow enforcement (Layer 0) |

---

## skill-craft/SKILL.md

### Frontmatter

```yaml
---
name: skill-craft
description: Unified Skill-Craft Orchestrator — coordinates skill improvement through a 5-phase pipeline (diagnose → plan → execute → evaluate → gate) with fidelity closing gates.
version: 0.4.0
category: orchestration
enforcement: strict
layer1_enforcement: true
workflow_steps:
  - diagnosing
  - planning
  - executing
  - evaluating
  - gating
usage_markers:
  - "Phase 1: DIAGNOSING"
  - "Phase 2: PLANNING"
  - "Phase 3: EXECUTING"
  - "Phase 4: EVALUATING"
  - "Phase 5: GATING"
  - "fidelity gate"
  - "craft-done"
triggers:
  - '/skill-craft'
  - 'improve this skill'
  - 'audit this skill'
  - 'craft this'
  - 'create skill documentation'
  - 'add mermaid diagram'
hooks:
  - id: craft_phase_tracker
    type: PostToolUse
    matcher: "skill-craft"
  - id: craft_phase_gate
    type: PreToolUse
    matcher: "skill-craft.*(planning|executing|evaluating|gating)"
    blocking: true
  - id: craft_telemetry_collector
    type: PostToolUse
    matcher: "skill-craft.*gating"
---
```

### Overview

Coordinates skill improvement through a 5-phase pipeline: diagnosing → planning → executing → evaluating → gating.

### Mermaid Diagram Authoring

When creating documentation diagrams, produce mermaid that is readable, minimal, and almost never has crossing lines.

**Layout Rules:**
- **Direction matters** — TD (top-down) keeps phases vertical; LR (left-right) is good for state machines
- **Avoid crossing edges** — Reorder nodes or insert invisible style nodes
- **Color-code edge types** — Different colors for pass/fail/loop-back paths

**Color Palette (dark + light):**
```javascript
dark:  { success: '#4ade80', fallback: '#f87171', discovery: '#c084fc', entry: '#60a5fa', analysis: '#22d3ee', other: '#71717a' }
light: { success: '#16a34a', fallback: '#dc2626', discovery: '#7c3aed', entry: '#2563eb', analysis: '#0891b2', other: '#6b7280' }
```

### 5-Phase Pipeline

#### Phase 1: DIAGNOSING
Run validation via `av`. When `av` is unavailable, perform direct analysis:
- Imperative form check (all directives in present tense)
- Third-person trigger check
- SKILL.md body line count verification
- Progressive disclosure verification

#### Phase 2: PLANNING
Capability discovery via `/usm` runs first, before routing

#### Phase 3: EXECUTING
Invoke sub-skills by priority order. GitHub Issues Review runs FIRST (pre-flight).

#### Phase 4: EVALUATING
Iterate until fidelity threshold is met (80% threshold).

#### Phase 5: GATING
Two independent gates: Artifact Completeness (hard) + Diff-Based Semantic Delta (soft).

### Review Agents

1. **Hook Review Agent** — Reviews skill for optimal hook integration
2. **Agent Review Agent** — Reviews skill for optimal sub-agent and MCP use
3. **MCP Review Agent** — Reviews skill for optimal MCP tool use
4. **Skill Implementation Review Agent** — Reviews skill for runtime quality

### Telemetry

After Phase 5, `craft_telemetry_collector` captures run history and computes delta vs baseline.

**Artifact Structure:**
```
.claude/.artifacts/{terminal_id}/skill-craft/telemetry/{target_skill}/
  run-{timestamp}.json   # Full run record
  latest.json            # Most recent baseline
  delta.json             # Diff vs baseline
  index.jsonl            # Run history index
```

### Plugin Architecture

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
├── agents/
│   └── *.md
└── mcp_json.md
```

### $ARGUMENTS Note

$ARGUMENTS is a `type:prompt` / `type:agent` feature only — NOT available in `type:command` command strings. Use stdin JSON parsing instead.

---

## StopHook_skill_execution_gate.py (Key Excerpts)

### Purpose
Safety net for skill execution validation. Secondary defense — PreToolUse hook handles real-time blocking. This Stop hook only fires when PreToolUse failed to block.

**Problem Solved:** Claude loads skill documentation, then provides its own analysis instead of executing the skill's designated workflow.

### Key Functions

```python
# Extract user prompt to detect slash commands
def extract_user_prompt(input_data: dict) -> str: ...

# Extract tools used in current response
def extract_tools_used(input_data: dict) -> list[str]: ...

# Layer 1 marker-based governance check
def _check_governance_markers(input_data: dict) -> dict: ...
```

### Configuration

```python
ENABLED = os.environ.get("SKILL_EXECUTION_GATE_ENABLED", "true").lower() == "true"
BUILTIN_SLASH_COMMANDS = {"help", "clear", "compact", "cost", "doctor", ...}
LIGHTWEIGHT_SLASH_COMMANDS = {"context-status", "clear-notifications", "obs", ...}
STALE_TIMEOUT = 300  # 5 minutes
```

### Two-Strike Pattern
1. First bypass: Advisory message with retry instruction
2. Second bypass: Hard block with descriptive error

### Version History
- v3.2: Simplified to safety net only
- v3.3: Added Layer 1 marker-based governance
- v3.4: Slash command bypass detection

---

## HOW TO USE THIS PACK

- skill-craft is a PROCEDURE type skill (5-phase orchestrator)
- Phase enforcement via `craft_phase_gate` PreToolUse hook
- Telemetry via `craft_telemetry_collector` PostToolUse hook
- Evaluation: 80% threshold on eval_sets/default.json
- GitHub Issues Review runs FIRST before other review agents
- StopHook_skill_execution_gate.py provides secondary enforcement for all skills