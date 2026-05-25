# cc-aca-safety

ACA Safety plugin -- filesystem protection, path policy enforcement, bulk delete safety, Windows path correctness, protected file recovery, repo visibility guard, and git auto-staging for deletion safety.

## Plugin Structure

```
cc-aca-safety/
  .claude-plugin/plugin.json
  __lib/
    _bootstrap.py          # Path setup and hooks_dir resolution
    hooks_resolver.py      # Global hooks dir discovery
  hooks/
    hooks.json
    pretool/
      PreToolUse_bulk_delete_gate.py
      PreToolUse_win32_path_gate.py
      PreToolUse_ownership_colocation_gate.py
      PreToolUse_git_auto_stage.py
      PreToolUse_protected_file_recovery_gate.py
      PreToolUse_repo_visibility_guard.py
      PreToolUse_path_validator.py
      PreToolUse_directory_policy.py
    userpromptsubmit/
      ownership_colocation_nudge.py
  tests/
```

## Hook Inventory

### PreToolUse (8 hooks)

| Hook | Purpose |
|------|---------|
| `PreToolUse_bulk_delete_gate.py` | Blocks bulk deletions, creates git recovery tags |
| `PreToolUse_win32_path_gate.py` | Blocks backslash paths in Write/Edit (Windows silent-failure prevention) |
| `PreToolUse_ownership_colocation_gate.py` | Blocks writes to shared-infra paths without consumer-count evidence |
| `PreToolUse_git_auto_stage.py` | Auto-stages files before deletion for git history recovery |
| `PreToolUse_protected_file_recovery_gate.py` | Blocks edits on syntactically broken protected files |
| `PreToolUse_repo_visibility_guard.py` | Prevents accidental repo visibility changes on P: drive |
| `PreToolUse_path_validator.py` | Path validation with symlink, root-level, and sensitive-edit checks |
| `PreToolUse_directory_policy.py` | Directory policy enforcement, external path consent, CSF NIP validation |

### UserPromptSubmit (1 module)

| Module | Purpose |
|---------|---------|
| `ownership_colocation_nudge.py` | Injects ownership-colocation checklist at planning time |

## Module Classification

| Module | Location | Why |
|--------|----------|-----|
| `path_validator.py` | Global `__lib/` | 5 consumers (csf_nip, enhanced_path_validator, directory_policy, path_validator hook, tests) |
| `protected_paths.py` | Global `__lib/` | 3 consumers (protected_file_recovery_gate, python_syntax_checker, tests) |
| `pre_tool_use_logic.py` | Global `__lib/` | 3 consumers (path_validator hook, edit_consent, tests) |
| `hook_base.py` | Global `__lib/` | 41+ consumers across all domains |
| `violation_reporter.py` | Global hooks dir | 1 consumer (directory_policy) -- accessed via hooks_dir |
| `csf_nip_path_validator.py` | Global hooks dir | 1 consumer (directory_policy) -- accessed via hooks_dir |

No plugin-local modules needed -- all dependencies have cross-domain consumers or are accessed via hooks_dir.

## Compatibility Layer

Original hooks in `P:/.claude/hooks/` are backed up as `.pre-safety` and replaced with compatibility wrappers that delegate to plugin hooks via `importlib.util`.

Wrappers use `globals().update()` re-export pattern to expose `run()` and `main()` for in-process and subprocess invocation.

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

## Domain Boundary

**Safety owns:**
- Filesystem protection (delete gates, recovery points)
- Path policy enforcement (directory policy, path validation)
- Windows path correctness (backslash prevention)
- Protected file recovery (syntax lockout)
- Repo visibility guard
- File ownership/colocation enforcement

**NOT in this plugin:**
- Git permission enforcement (cc-aca-authority: `PreToolUse_destructive_git_guard`, `PreToolUse_git_safety`)
- TDD/test workflow (cc-aca-sdlc)
- Observability/telemetry (cc-aca-observability)
