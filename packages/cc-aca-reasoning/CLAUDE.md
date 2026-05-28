# cc-aca-reasoning

ACA Reasoning plugin -- sequential thinking, cognitive enhancement, reasoning mode selection, reflection triggers, drift detection, and reasoning quality gates.

## Plugin Structure

```
cc-aca-reasoning/
  .claude-plugin/plugin.json
  __lib/
    _bootstrap.py          # Path setup and hooks_dir resolution
    hooks_resolver.py      # Global hooks dir discovery
    sequential_state.py    # Plugin-local: sequential thinking session state
  hooks/
    hooks.json
    pretool/
      PreToolUse_sequential_thinking.py
    posttool/
      PostToolUse_self_reflection_reminder.py
    start/
      Start_reasoning_mode_selector.py
    stop/
      StopHook_sequential_thinking.py
      StopHook_drift_sentinel.py
      StopHook_rca_reflector.py
      Stop_self_reflection_gate.py
      Stop_reflect_integration.py
      Stop_reasoning_quality_gate.py
    userpromptsubmit/
      UserPromptSubmit_cognitive_tags.py
      sequential_thinking.py
      sequential_thinking_semantic_client.py
      cognitive_enhancers.py
      cognitive_guardrails.py
      reasoning_contract.py
      reasoning_mode_selector.py
      think_trigger.py
  tests/
```

## Hook Inventory

### PreToolUse (2 hooks)

| Hook | Purpose |
|------|---------|
| `PreToolUse_sequential_thinking.py` | Mode enforcement (initial/critique/improve) via iteration state |
| `PreToolUse_investigation_boundary_gate.py` | One-time reflection prompt at investigation-to-implementation transition |

### PostToolUse (1 hook)

| Hook | Purpose |
|------|---------|
| `PostToolUse_self_reflection_reminder.py` | Injects reflection prompts after tool use |

### Start (1 hook)

| Hook | Purpose |
|------|---------|
| `Start_reasoning_mode_selector.py` | Analyzes queries to select optimal reasoning mode |

### Stop (6 hooks)

| Hook | Purpose |
|------|---------|
| `StopHook_sequential_thinking.py` | Sequential thinking session lifecycle |
| `StopHook_drift_sentinel.py` | Detects reasoning drift from original intent |
| `StopHook_rca_reflector.py` | Root-cause analysis reflection triggers |
| `Stop_self_reflection_gate.py` | Quality gate for self-reflection depth |
| `Stop_reflect_integration.py` | Integrates reflection insights into output |
| `Stop_reasoning_quality_gate.py` | Final reasoning quality assessment |

### UserPromptSubmit (1 executable + 7 UPS modules)

| Module | Purpose |
|--------|---------|
| `UserPromptSubmit_cognitive_tags.py` | Injects cognitive framework tag instructions |
| `sequential_thinking.py` | Sequential thinking trigger detection |
| `sequential_thinking_semantic_client.py` | Semantic similarity for trigger detection |
| `cognitive_enhancers.py` | Cognitive enhancement patterns |
| `cognitive_guardrails.py` | Cognitive safety guardrails |
| `reasoning_contract.py` | Reasoning contract enforcement |
| `reasoning_mode_selector.py` | Mode selection logic (shared with Start hook) |
| `think_trigger.py` | Think-trigger pattern detection |

## Module Classification

| Module | Location | Why |
|--------|----------|-----|
| `sequential_state.py` | Plugin-local `__lib/` | Only consumed by reasoning hooks (3 consumers, zero non-reasoning) |
| `cc_diagnostic_logger` | Global `__lib/` | 25+ cross-domain consumers |
| `evidence_store` | Global `__lib/` | 30+ cross-domain consumers |
| `base.py` (UPS) | Global `UserPromptSubmit_modules/` | 84 total consumers (65 non-reasoning) |
| `registry.py` (UPS) | Global `UserPromptSubmit_modules/` | 50 total consumers |
| `unified_detection.py` (UPS) | Global `UserPromptSubmit_modules/` | 31 total consumers |
| `conflict_arbiter.py` (UPS) | Global `UserPromptSubmit_modules/` | 6 total consumers |
| `tag_registry.py` (UPS) | Global `UserPromptSubmit_modules/` | 4 total consumers |

## Compatibility Layer

Original hooks in `P:/.claude/hooks/` are backed up as `.pre-reasoning` and replaced with compatibility wrappers that delegate to plugin hooks via `importlib.util`.

UPS modules use `globals().update()` re-export pattern for package-qualified imports from `UserPromptSubmit_modules.base`.

## Bootstrap Pattern

All hooks use the 4-line bootstrap header:

```python
# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---
```

Must be placed after `from __future__ import annotations` and before regular imports.
