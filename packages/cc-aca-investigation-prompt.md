# Migrate cc-aca-investigation Plugin

You are implementing the cc-aca-investigation plugin migration based on the completed Phase 1 audit.

## Context

Investigation won the coupling analysis with a score of 4 (lowest of all three candidate domains). Key characteristics:

- 11 hooks total
- 7 hooks have zero external dependencies (fully self-contained)
- 4 `__lib__` imports, all 1:1 (each module used by exactly one hook)
- 0 cross-hook dependencies
- 2 UPS hooks use only base/registry (genuinely shared UPS framework)

Already completed migrations for reference:
- cc-aca-session (6 hooks, v0.1.0)
- cc-aca-epistemic (23 hooks, v0.1.7) — **follow this pattern exactly**

## `__lib__` Strategy

Follow the epistemic precedent:

- **Domain-specific modules** that pass the consumer audit (zero non-domain consumers) move to the plugin's `lib/` directory. This matches what cc-aca-epistemic did with `claim_patterns.py`, `claim_layer_map.py`, `epistemic_validator.py`, and `self_verification_gate.py`.
- **Shared modules** with cross-domain consumers stay in the global `P:/.claude/hooks/__lib__/`. This matches what cc-aca-epistemic did with `artifact_ledger`, `claim_type`, `shared_utils`, etc.
- **Never move a module without grep proof.** If `grep -r "from __lib.module_name" P:/.claude/hooks/ --include="*.py"` returns non-investigation hits, the module stays shared.

## UPS Module Handling

Investigation has 3 UPS modules inside `UserPromptSubmit_modules/`:

1. `discovery_block.py` — zero dependencies (self-contained)
2. `error_investigation_gate.py` — imports from UPS framework
3. `evidence_grounding_reminder.py` — imports from UPS framework

**Critical:** Do NOT move `base.py` or `registry.py`. They are shared UPS framework infrastructure used by all UPS modules across all domains.

**Do not assume import style.** The Phase 1 audit found these UPS modules import as `from UserPromptSubmit_modules.base import HookContext, HookResult` — package-qualified, NOT top-level `from base import ...`. Before modifying any UPS module:

1. Read the actual import lines in each file directly.
2. If imports are package-qualified (`UserPromptSubmit_modules.base`), the bootstrap must add the global hooks root (`P:/.claude/hooks/`) to `sys.path` so that `UserPromptSubmit_modules` resolves as a package. Do NOT strip the package qualifier.
3. If imports are top-level (`from base import ...`), the bootstrap must add `UserPromptSubmit_modules/` itself to `sys.path`.
4. Only rewrite import statements after direct file inspection proves the rewrite is safe.
5. When in doubt, preserve the existing import style unchanged.

**Strategy:** Copy the 3 UPS modules to `hooks/userpromptsubmit/` in the plugin. The `_bootstrap.py` must ensure the correct sys.path entry for whichever import style the files actually use.

## Aggressive Subagent Usage

Use subagents for all bounded analysis work. Preserve main context for architectural decisions and migration execution.

### Subagent rules
1. **Each subagent must have a narrow scope and clear deliverable.** Example: "Grep for all imports of `commitment_tracker` across the hooks directory" not "Analyze shared modules."
2. **Ask subagents for evidence, not conclusions.** They should return raw grep output, not "this module is shared."
3. **You must reconcile all subagent outputs.** If two subagents give conflicting data, inspect the underlying files yourself.
4. **Never let a subagent make irreversible changes.** Subagents inspect and report only.
5. **Use Grep-scoped subagents, not Explore-scoped, for large directory scans.** The Phase 1 audit showed Explore agents hit context limits on large hooks directories. Prefer `Explore` for single-file reads, direct `Grep` for directory-wide pattern matching.
6. **If a task is small or tightly coupled, do it yourself.** Don't spawn a subagent to read one file.

## Migration Phases

### Phase 1: Consumer audits for borderline modules (4 subagents)

Use subagents to audit consumers for these 4 `__lib__` modules. Each subagent greps for imports and returns raw file lists.

**Subagent A: commitment_tracker consumers**
- Grep for `from __lib.commitment_tracker` and `from __lib import commitment_tracker` across `P:/.claude/hooks/` (all .py files, including subdirectories)
- Also grep for `import commitment_tracker` as a standalone import
- Return: list of files that import this module, with one-line context showing the import statement
- Do NOT classify — just return raw results

**Subagent B: runtime_env consumers**
- Same task for `runtime_env`
- Same deliverable format

**Subagent C: skill_guard_path consumers**
- Same task for `skill_guard_path`
- Same deliverable format

**Subagent D: path_classifier consumers**
- Same task for `path_classifier`
- Same deliverable format

Then in main context, decide for each module:
- **Plugin-specific** — only used by investigation hooks, safe to move to plugin `lib/`
- **Shared** — used by non-investigation hooks, must stay in `__lib__/`
- **Uncertain** — needs deeper inspection (read the file yourself if needed)

Expected outcome based on Phase 1 audit:
- `commitment_tracker` → likely shared (multiple session hooks)
- `runtime_env` → definitely shared (environment detection is cross-domain)
- `path_classifier` → borderline (audit will determine)
- `skill_guard_path` → likely movable (only breadcrumb hooks use it)

### Phase 2: Test discovery (1 subagent)

**Subagent E: Test discovery**
- Grep for test files related to the 11 investigation hooks
- Search patterns: `test_observe_before_act`, `test_discovery_tracker`, `test_implementation_default`, `test_arch_first`, `test_require_plan`, `test_breadcrumb_gate`, `test_breadcrumb_verifier`, `test_discovery_block`, `test_error_investigation`, `test_evidence_grounding`
- Return: list of test files with their paths and a count of test functions in each
- Also check if any of these tests import from the hooks directly (vs. testing functionality independently)

This informs whether tests need migration or can stay in place.

### Phase 3: Hook content verification (1 subagent)

**Subagent F: Verify hook imports**
- For each of the 11 investigation hooks, verify the Phase 1 audit's import claims
- Read the first 30 lines of each hook file and confirm the import list matches the audit
- Flag any discrepancies between the audit and the actual file
- Return: table of `hook_name | verified_imports | audit_said | discrepancy?`

This catches any stale data from the Phase 1 audit before migration begins.

### Phase 4: Create plugin scaffold

Follow the cc-aca-epistemic pattern exactly. Directory structure:

```
P:/packages/cc-aca-investigation/
├── .claude-plugin/
│   └── plugin.json          (v0.1.0, keywords: aca, investigation, discovery, observe-before-act)
├── hooks/
│   ├── hooks.json            ({"hooks": {}} — empty, registration stays in settings.json)
│   ├── pretool/              (7 PreToolUse hooks)
│   │   ├── PreToolUse_observe_before_act_gate.py
│   │   ├── PreToolUse_discovery_tracker.py
│   │   ├── PreToolUse_implementation_default_gate.py
│   │   ├── PreToolUse_arch_first_enforcer.py
│   │   ├── PreToolUse_require_plan_for_features.py
│   │   ├── PreToolUse_breadcrumb_gate.py
│   │   └── PreToolUse_breadcrumb_verifier.py
│   └── userpromptsubmit/     (4 UserPromptSubmit hooks/modules)
│       ├── UserPromptSubmit_discovery_block.py
│       ├── discovery_block.py
│       ├── error_investigation_gate.py
│       └── evidence_grounding_reminder.py
├── __lib/
│   ├── __init__.py
│   ├── _bootstrap.py         (path setup + UPS dir access)
│   ├── hooks_resolver.py     (copy from epistemic — resolves global hooks dir)
│   ├── compat_loader.py      (adapted from epistemic — phase map + delegation)
│   └── (domain-specific modules from Phase 1 audit if movable)
├── tests/
│   └── test_investigation_plugin.py
└── CLAUDE.md
```

Key differences from epistemic:
- No `stop/` or `posttool/` directories — investigation has zero Stop or PostToolUse hooks
- `userpromptsubmit/` holds both the UserPromptSubmit entry hook AND the 3 UPS modules
- Fewer or zero domain-specific `__lib__` modules to move (most imports are genuinely shared)

### Phase 5: Implement bootstrap pattern

Create `__lib/_bootstrap.py` following the epistemic pattern, with one addition:

```python
"""Plugin bootstrap — call bootstrap(__file__) from any hook to set up sys.path.

Replaces per-hook path boilerplate. Single point of change for path resolution logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_LIB = PLUGIN_ROOT / "__lib"


def bootstrap(hook_file: str | Path) -> Path:
    """Set up sys.path for a plugin hook. Returns the resolved hooks dir."""
    # Plugin's own lib/
    if str(PLUGIN_LIB) not in sys.path:
        sys.path.insert(0, str(PLUGIN_LIB))

    # Global hooks dir for shared __lib__ access
    from hooks_resolver import get_hooks_dir
    hooks_dir = get_hooks_dir()
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    hooks_lib = hooks_dir / "__lib"
    if str(hooks_lib) not in sys.path:
        sys.path.insert(0, str(hooks_lib))

    # UPS modules access — needed by error_investigation_gate and evidence_grounding_reminder
    # which import as "from UserPromptSubmit_modules.base import ..."
    # The hooks_dir is already on sys.path above, so UserPromptSubmit_modules resolves as a package.
    # If direct inspection reveals top-level imports ("from base import ...") instead,
    # add hooks_dir / "UserPromptSubmit_modules" to sys.path as well.

    return hooks_dir
```

**Note on UPS sys.path:** The Phase 1 audit found that investigation UPS modules use package-qualified imports (`from UserPromptSubmit_modules.base import ...`). Since `hooks_dir` (`P:/.claude/hooks/`) is already added to `sys.path` by the bootstrap, `UserPromptSubmit_modules` resolves as a package without additional sys.path entries. However, the verification subagent (Phase 3) must confirm this — if any UPS module uses top-level imports instead, add the UPS directory explicitly.

### Phase 6: Copy hooks to plugin (two batches)

**Batch A — Self-contained hooks** (verified by Subagent F as having zero non-stdlib imports):

| Hook | Destination |
|------|-------------|
| PreToolUse_observe_before_act_gate.py | hooks/pretool/ |
| PreToolUse_discovery_tracker.py | hooks/pretool/ |
| UserPromptSubmit_discovery_block.py | hooks/userpromptsubmit/ |
| discovery_block.py | hooks/userpromptsubmit/ |

For each: copy to destination, add bootstrap header, done.

**Batch B — Shared-runtime hooks** (have `__lib__` or UPS framework dependencies):

| Hook | Dependency | Destination |
|------|-----------|-------------|
| PreToolUse_implementation_default_gate.py | `__lib.commitment_tracker` | hooks/pretool/ |
| PreToolUse_arch_first_enforcer.py | `__lib.runtime_env` | hooks/pretool/ |
| PreToolUse_require_plan_for_features.py | `__lib.path_classifier` | hooks/pretool/ |
| PreToolUse_breadcrumb_gate.py | `__lib.skill_guard_path` | hooks/pretool/ |
| PreToolUse_breadcrumb_verifier.py | `__lib.skill_guard_path` | hooks/pretool/ |
| error_investigation_gate.py | `UserPromptSubmit_modules.base, registry` | hooks/userpromptsubmit/ |
| evidence_grounding_reminder.py | `UserPromptSubmit_modules.base, registry` | hooks/userpromptsubmit/ |

For each:
1. Copy to destination
2. Add bootstrap header
3. If the module stayed shared (Phase 1 consumer audit result), the import resolves via sys.path — no change needed
4. If the module moved to plugin `lib/`, update the import path
5. For UPS modules: preserve existing import style (do not rewrite unless Subagent F verified top-level imports)

All hooks get the standard bootstrap header at the top (replacing any existing path setup):

```python
# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---
```

3. For hooks with `__lib__` imports:
   - If the module stayed shared (Phase 1 audit result), the import path stays as-is — `__lib__` is on sys.path via bootstrap
   - If the module moved to plugin `lib/`, update the import to use the plugin-local path

4. For UPS modules: do NOT rewrite their imports. They already use `from UserPromptSubmit_modules.base import ...` which resolves because the hooks root is on sys.path via bootstrap. If verification shows a different import style, preserve it exactly and adjust sys.path accordingly.

### Phase 7: Create compatibility wrappers

Follow the epistemic `compat_loader.py` pattern exactly.

**compat_loader.py** — adapted from epistemic with investigation's phase map:

```python
_PHASE_MAP: dict[str, str] = {
    "PreToolUse": "pretool",
    "UserPromptSubmit": "userpromptsubmit",
}
```

Note: no "Stop", "StopHook", or "PostToolUse" entries — investigation has none.

**11 wrapper stubs** in `P:/.claude/hooks/` — one per hook. Each wrapper is identical:

```python
#!/usr/bin/env python3
"""Delegates to cc-aca-investigation plugin."""
import sys
sys.path.insert(0, "P:/packages/cc-aca-investigation/__lib")
from compat_loader import delegate
delegate(__file__)
```

**Backup originals** as `.pre-investigation` before replacing with wrappers.

### Phase 8: Operational validation

1. Install plugin via marketplace junction
2. Run `plugin-audit-and-fix.py --bump cc-aca-investigation` to refresh cache
3. Trigger at least 3 hooks to verify E2E execution:
   - `PreToolUse_observe_before_act_gate` — trigger a write without prior read
   - `PreToolUse_discovery_tracker` — trigger discovery tracking
   - `UserPromptSubmit_discovery_block` — submit a prompt that triggers discovery block
4. Report whether hooks fired, whether they executed via plugin path, and any errors
5. Check stderr for import errors or path resolution failures

### Phase 9: Documentation and cleanup

1. Write `CLAUDE.md` following the epistemic template — include:
   - Responsibility section
   - Directory structure
   - Hook table with purpose for each hook
   - Architecture section explaining bootstrap and compat_loader
   - `__lib__` strategy section (what moved vs. what stayed shared)
   - "What Is NOT in This Plugin" section
   - Migration lessons for the next ACA plugin

2. Run consumer audit grep to verify old module copies are dead (if any were moved):
   ```bash
   grep -r "from __lib.skill_guard_path" P:/.claude/hooks/ --include="*.py" | grep -v ".pre-investigation"
   ```
   If zero results, the old copy in `__lib__/` can be deleted.

3. Delete dead code from `__lib__/` only if consumer audit confirms zero consumers
4. Keep `.pre-investigation` backups until validation passes
5. Remove backups after validation passes
6. Bump version, commit

## Output Format

Return a structured report with these sections:

### 1. CONSUMER AUDIT RESULTS
Raw grep output for each of the 4 borderline modules.

### 2. MODULE CLASSIFICATION DECISIONS
Which modules moved to plugin, which stayed shared, and why. Include grep evidence for each decision.

### 3. PLUGIN STRUCTURE
Directory tree of the created plugin.

### 4. HOOKS MIGRATED
Table: hook name, source path, destination path, external dependencies, bootstrap changes needed.

### 5. COMPATIBILITY LAYER
How many wrappers created, where they delegate, the compat_loader phase map.

### 6. OPERATIONAL VALIDATION
Install result, reload result, E2E execution results for 3 hooks.

### 7. ARCHITECTURE DOCUMENTATION
Confirm CLAUDE.md updated with full content.

### 8. DEAD CODE REMOVED
Which old copies were deleted (with grep proof of zero consumers), or why they were kept.

### 9. RISKS AND BLOCKERS
Any unresolved issues or decisions deferred.

### 10. SUBAGENT SUMMARY
How many subagents used, what each did, conflicts resolved, subagent failures recovered.

## Behavioral Constraints

- **Do not move modules without consumer audit proof.** If a module has non-investigation consumers, it must stay shared. Grep output is the evidence.
- **Do not skip operational validation.** Pytest is not enough. Hooks must fire in actual Claude Code runtime.
- **Do not assume bootstrap works.** Verify imports resolve by running a hook and checking stderr.
- **Use subagents for consumer audits and data gathering, not architectural decisions.** You decide what moves and what stays.
- **Follow the epistemic migration pattern exactly** unless there's a documented reason to diverge. The bootstrap, compat_loader, and wrapper stub patterns are proven — don't reinvent them.
- **If `skill_guard_path` is movable, move it to plugin `lib/`.** If not, document why and keep the import as-is.

## Success Criteria

A successful migration will:

1. Install cleanly and pass `plugin-audit-and-fix.py --validate`
2. Execute all 11 hooks via plugin path in actual Claude Code runtime
3. Move all domain-specific modules that pass the consumer audit (with grep proof)
4. Keep all genuinely shared modules in `__lib__/` (with grep proof)
5. Document architecture clearly in CLAUDE.md
6. Remove dead code (with grep proof of zero consumers)
7. Provide evidence-based justification for all shared-vs-movable decisions
8. Use subagents for at least 6 bounded tasks (4 consumer audits + test discovery + hook verification)

**Start by spawning Subagent A to audit commitment_tracker consumers.**
