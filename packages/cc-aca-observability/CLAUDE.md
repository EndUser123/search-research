# cc-aca-observability

ACA Observability plugin — session health monitoring, drift detection, artifact scraping, and PostToolUse tracker orchestration.

## Responsibility

All hooks that provide observability: session health checks, CJK drift detection, artifact scraping, and PostToolUse tracker orchestration (15 in-process tracker hooks dispatched by PostToolUse_router.py).

## Directory Structure

```
hooks/
  posttool/
    PostToolUse_router.py         # In-process dispatcher for 15 tracker hooks
    PostToolUse_artifact_scraper.py  # Records search artifacts into ledger
    cjk_drift_detector.py         # Blocks/warns on CJK text (3 events)
  sessionstart/
    SessionStart_cc_health.py     # Session health surface at startup
__lib/
  _bootstrap.py                   # Path setup + sys.path resolution
  hooks_resolver.py               # Resolves global hooks dir for shared __lib__ access
  posttooluse/                    # Tracker package (15 hooks)
    __init__.py                   # HOOK_REGISTRY
    base.py                       # PostToolUseHook base class
    <15 tracker hook files>
    effects/                      # Effect verification modules
```

## Hooks

### PostToolUse

| Hook | Matcher | Purpose |
|------|---------|---------|
| PostToolUse_router.py | `^(?:Edit|Write|MultiEdit)$` | Dispatches 15 in-process tracker hooks |
| PostToolUse_artifact_scraper.py | `^(?:Grep|Glob|Read)$` | Records search artifacts into ledger |
| cjk_drift_detector.py | `^(?:Bash|Task)$` | Warns on CJK text in CLI output |

### Stop

| Hook | Matcher | Purpose |
|------|---------|---------|
| cjk_drift_detector.py | `.*` | Blocks CJK text in agent responses |

### SubagentStop

| Hook | Matcher | Purpose |
|------|---------|---------|
| cjk_drift_detector.py | `.*` | Blocks CJK text in subagent responses |

### SessionStart

| Hook | Matcher | Purpose |
|------|---------|---------|
| SessionStart_cc_health.py | `.*` | Surfaces hook health status at session start |

## Architecture

- **Plugin is canonical source.** No compatibility wrappers. Hooks registered directly via `hooks.json`.
- **hooks_resolver.py** resolves the global hooks dir (`P:/.claude/hooks/`) for shared `__lib__` access.
- **HOOKS_DIR** in hook modules resolves to `P:/.claude/hooks/` (via bootstrap), NOT the plugin directory.

### Import Pattern

Every hook uses `_bootstrap.py` for path setup:

```python
# --- plugin bootstrap ---
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; HOOKS_DIR = bootstrap(__file__)
# --- end bootstrap ---
```

### PostToolUse Router Architecture

`PostToolUse_router.py` is the main entry point for tracker hooks. It:
1. Imports the `posttooluse` package from plugin `__lib/`
2. Creates a registry of enabled tracker hooks via `create_registry()`
3. Runs all enabled hooks in-process (~5-10ms vs ~184ms subprocess)
4. Returns the combined result (block if any hook blocks)

### Shared Module Dependencies

These modules stay in `P:/.claude/hooks/__lib__/` (non-observability consumers):
`terminal_detection`, `evidence_store`, `hook_ledger`, `runtime_env`, `hook_base`, `artifact_ledger`, `tool_sequence_manager`, `buffered_logger`

## What Is NOT in This Plugin

- **Epistemic hooks** — cc-aca-epistemic
- **Investigation hooks** — cc-aca-investigation
- **Session hooks** — cc-aca-session
- **Reasoning hooks** — cc-aca-reasoning
- **log_hook.py** — shared logging, stays in local hooks
