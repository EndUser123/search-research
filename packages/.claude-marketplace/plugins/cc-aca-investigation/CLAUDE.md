# cc-aca-investigation

ACA Investigation plugin — discovery-first enforcement, observe-before-act gating, breadcrumb progression tracking, and evidence-grounded reasoning prompts.

## Responsibility

All hooks that enforce investigation discipline: observe-before-act, discovery-first workflow, implementation gating, breadcrumb step verification, and UPS modules for error investigation and evidence grounding.

## Directory Structure

```
hooks/
  pretool/              # PreToolUse gates (7 hooks)
  userpromptsubmit/     # UserPromptSubmit hooks + UPS modules (4 files)
__lib/
  _bootstrap.py         # Path setup + sys.path resolution
  hooks_resolver.py     # Resolves global hooks dir for shared __lib__ access
  compat_loader.py      # Wrapper delegation with phase map
  path_classifier.py    # Path classification (domain-specific, moved from __lib__)
```

## Hooks

### PreToolUse (hooks/pretool/)

| Hook | Purpose |
|------|---------|
| PreToolUse_observe_before_act_gate | Enforces "observe completely, then act once" principle |
| PreToolUse_discovery_tracker | Tracks discovery tool usage before implementation |
| PreToolUse_implementation_default_gate | Blocks implementation without explicit intent |
| PreToolUse_arch_first_enforcer | Enforces architecture-first approach |
| PreToolUse_require_plan_for_features | Requires planning before feature work |
| PreToolUse_breadcrumb_gate | Validates step progression from breadcrumbs |
| PreToolUse_breadcrumb_verifier | Verifies breadcrumb data integrity |

### UserPromptSubmit (hooks/userpromptsubmit/)

| Hook | Purpose |
|------|---------|
| UserPromptSubmit_discovery_block | Blocks implementation prompts until discovery tools used |
| discovery_block | Discovery block UPS module (registered via framework) |
| error_investigation_gate | Injects error investigation reminders |
| evidence_grounding_reminder | Rotated evidence-grounding priming every N turns |

## Architecture

- **Plugin is canonical source.** Compatibility wrappers in `P:/.claude/hooks/` delegate to this plugin via import. Settings.json registration unchanged.
- **hooks_resolver.py** resolves the global hooks dir (`P:/.claude/hooks/`) for shared `__lib__` access.
- **HOOKS_DIR** in core modules resolves to `P:/.claude/hooks/` (via hooks_resolver), NOT the plugin directory.

### Import Pattern

Every hook uses `_bootstrap.py` for path setup:

```python
# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---
```

### Compatibility Wrappers

8 wrapper files in `P:/.claude/hooks/` + 3 UPS delegates in `UserPromptSubmit_modules/` delegate to plugin hooks. Each wrapper is a 6-line stub:

```python
#!/usr/bin/env python3
"""Delegates to cc-aca-investigation plugin."""
import sys
sys.path.insert(0, "P:/packages/cc-aca-investigation/__lib")
from compat_loader import delegate
delegate(__file__)
```

UPS modules use `importlib.util` delegation to preserve `register_hook` exports.

## __lib__ Strategy

### Moved to plugin (domain-specific, zero non-investigation consumers)

| Module | Evidence |
|--------|----------|
| `path_classifier` | Only used by `PreToolUse_require_plan_for_features.py` (investigation hook) |

### Remains shared (has non-investigation consumers)

| Module | Non-investigation consumers |
|--------|---------------------------|
| `commitment_tracker` | `SessionStart_commitment_tracker.py`, `StopHook_commitment_tracker.py` |
| `runtime_env` | `adversarial_aggregator.py`, `PostToolUse_router.py`, `PreToolUse.py` |
| `skill_guard_path` | `PostToolUse_tdd_state.py` |

### UPS Framework (stays shared)

| Module | Location |
|--------|----------|
| `base.py` | `P:/.claude/hooks/UserPromptSubmit_modules/base.py` |
| `registry.py` | `P:/.claude/hooks/UserPromptSubmit_modules/registry.py` |

UPS modules import as `from UserPromptSubmit_modules.base import ...` (package-qualified). The bootstrap adds `hooks_dir` to sys.path so this resolves.

## What Is NOT in This Plugin

- **Epistemic hooks** — belong in cc-aca-epistemic
- **Session hooks** — belong in cc-aca-session
- **Stop/PostToolUse hooks** — investigation has zero Stop or PostToolUse hooks
- **Breadcrumb tracker** — `PostToolUse_breadcrumb_tracker.py` is session infrastructure, not investigation
- **Commitment tracker** — shared between session and investigation domains

## Migration Lessons

### What worked
1. **Consumer audit first** — Phase 1 grep audits prevented moving shared modules
2. **`_bootstrap.py`** — centralized path setup, no per-hook boilerplate
3. **`compat_loader.py`** — reduced 8 unique wrappers to 8 identical stubs
4. **UPS delegation** — `importlib.util` approach preserves `register_hook` exports

### What to avoid
1. **Don't assume UPS import style** — `evidence_grounding_reminder.py` used relative imports while others used package-qualified. Always verify.
2. **Don't move modules without grep proof** — 3 of 4 audited modules had non-investigation consumers
3. **Don't skip UPS module handling** — they must stay in `UserPromptSubmit_modules/` for the framework to discover them
