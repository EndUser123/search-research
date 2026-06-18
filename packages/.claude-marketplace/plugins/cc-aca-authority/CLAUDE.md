# cc-aca-authority

ACA Authority plugin — permission enforcement, approval flow control, delegation gating, risk tiering, and git safety guards.

## Plugin Structure

```
cc-aca-authority/
  .claude-plugin/plugin.json
  __lib/
    _bootstrap.py          # Path setup and hooks_dir resolution
    hooks_resolver.py      # Global hooks dir discovery
    response_intent.py     # Intent classification (orphaned 2026-06-18; only test-consumed)
  hooks/
    hooks.json
    pretool/
      PreToolUse_authorization_gate.py
      PreToolUse_delegation_gate.py
      PreToolUse_user_delegation_gate.py
      PreToolUse_risk_tier_gate.py
      PreToolUse_ask_first_tool_gate.py
      PreToolUse_destructive_git_guard.py
      PreToolUse_git_safety.py
    stop/
      Stop_safety_gate.py
      Stop_behavior_gates.py
      Stop_lazy_workaround_gate.py
      stop_permission_stall.py
    userpromptsubmit/
      UserPromptSubmit_approval.py
      delegation_prospector.py
  tests/
```

## Hook Inventory

### PreToolUse (7 hooks)

| Hook | Purpose |
|------|---------|
| `PreToolUse_authorization_gate.py` | Planning mode detection, CKS decision retrieval |
| `PreToolUse_delegation_gate.py` | Enforces delegation patterns from prospector state |
| `PreToolUse_user_delegation_gate.py` | User-level delegation enforcement |
| `PreToolUse_risk_tier_gate.py` | Risk tier classification for tool operations |
| `PreToolUse_ask_first_tool_gate.py` | Requires user confirmation before certain tools |
| `PreToolUse_destructive_git_guard.py` | Blocks destructive git operations |
| `PreToolUse_git_safety.py` | Worktree cross-checks, git restore suggestions |

### Stop (4 hooks)

| Hook | Purpose |
|------|---------|
| `Stop_safety_gate.py` | Secret/PII leakage, forbidden patterns |
| `Stop_behavior_gates.py` | Behavioral policy enforcement |
| `Stop_lazy_workaround_gate.py` | Detects lazy workaround suggestions |
| `stop_permission_stall.py` | Detects permission-seeking stall patterns |

### UserPromptSubmit (2 hooks)

| Hook | Purpose |
|------|---------|
| `UserPromptSubmit_approval.py` | Approval flow initialization |
| `delegation_prospector.py` | Detects multi-surface work for subagent delegation |

## Module Classification

| Module | Location | Why |
|--------|----------|-----|
| `response_intent.py` | Plugin-local `__lib/` | Consumers (Stop_approval_gate, Stop_commit_gate) deleted 2026-06-18; now only test-consumed — orphan-cleanup candidate |
| `ttl_utils` | Global `__lib/` | Shared with PreToolUse.py router |
| `hook_base` | Global `__lib/` | 41+ consumers across all domains |
| `turn_mode` | Global `__lib/` | Shared across epistemic, session, authority |
| `stop_gate_telemetry` | Global `__lib/` | Shared with Stop.py, cc_health |
| `anti_lazy_policy` | Global `__lib/` | Shared with anti_sycophancy |
| `_cks_cache` | Global `__lib/` | Shared with epistemic/investigation_gate |
| `performance_tracker` | Global `__lib/` | Shared with PostToolUse_tdd_state |

## Compatibility Layer

Original hooks in `P:/.claude/hooks/` are backed up as `.pre-authority` and replaced with compatibility wrappers that delegate to plugin hooks via `importlib.util`.

UPS hooks (delegation_prospector) use `globals().update()` re-export pattern for package-qualified imports from `UserPromptSubmit_modules.base`.

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

## Stop-Block Logging

The `__lib/router.py` module logs every Stop block via the shared `stop_block_log` module. All authority Stop blocks (safety_gate, behavior_gates, lazy_workaround_gate, stop_permission_stall) write structured rows to the canonical log.

**Log location:** `logs/diagnostics/stop_blocks.jsonl`

**Row schema:**
- `timestamp`: ISO 8601 UTC
- `event`: "Stop"
- `gate_name`: Hook filename (e.g., "Stop_safety_gate")
- `reason`: Block reason text
- `matched_span`: Text span that triggered the block
- `response_hash`: Hash of blocked response
- `session_id`: Session UUID
- `terminal_id`: Terminal UUID
- `transcript_path`: Path to session transcript JSONL

**Reader CLI:** `python stop_blocks_report.py` (from project root)
