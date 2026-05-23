# cc-aca-epistemic

ACA Epistemic plugin — evidence verification, claim validation, provenance tracking, anti-fabrication, and anti-sycophancy enforcement.

## Responsibility

All hooks that enforce epistemic discipline: claim verification, evidence hierarchy gating, provenance tracking, contamination prevention, anti-fabrication, and anti-sycophancy detection. Also absorbs the fact-guard plugin (PreToolUse/PostToolUse structured-edit guards).

## Directory Structure

```
hooks/
  pretool/           # PreToolUse gates
  stop/              # Stop hooks (response validation)
  posttool/          # PostToolUse validators
  userpromptsubmit/  # UserPromptSubmit classifiers
lib/
  provenance.py      # Claim provenance tracking (from fact-guard)
  contamination.py   # Contamination detection (from fact-guard)
  evidence_store.py  # Evidence accumulation and scope
  evidence_scope.py  # Scope-aware evidence tracking
  hooks_resolver.py  # Resolves global hooks dir for shared __lib__ access
  epistemic_validator.py
  verify_claims.py
  unified_claim_verifier.py
  verification/      # Claim decomposition, coverage, engine, rubric
  anti_sycophancy/   # Sycophancy detection modules
```

## Hooks

### PreToolUse (hooks/pretool/)

| Hook | Purpose |
|------|---------|
| PreToolUse_evidence_hierarchy_gate | Enforce evidence-tier requirements before edits |
| PreToolUse_verification_router | Unified router for verification gates |
| PreToolUse_investigation_gate | Gate investigation-type tool calls |
| PreToolUse_dependency_verification_gate | Verify dependencies before changes |
| PreToolUse_file_existence_guard | Block edits to nonexistent files |
| PreToolUse_command_intent_gate | Validate command intent before execution |
| PreToolUse_type_validator | Type-check tool inputs |
| fact-guard_PreToolUse | Block unsupported literals and contamination in structured edits |

### Stop (hooks/stop/)

| Hook | Purpose |
|------|---------|
| StopHook_unverified_stance | Detect unverified claims in responses |
| StopHook_cross_validator | Cross-reference claims against evidence |
| StopHook_cited_content_guard | Validate cited content exists and matches |
| StopHook_perf_attribution_gate | Gate performance-related claims |
| Stop_comparative_claim_guard | Guard against unsupported comparisons |
| Stop_deletion_verification_guard | Verify deletion claims match git diff |
| Stop_fake_done_detector | Detect false completion signals |
| Stop_diagnostic_analysis_quality_gate | Quality gate for diagnostic analysis |
| Stop_git_diff_reground | Reground claims against actual git diff |
| Stop_skill_dir_correlation_gate | Verify skill directory claims |
| Stop_artifact_enforcement | Enforce artifact presence for claims |
| Stop_cks_correction_anchor | Anchor corrections to CKS entries |

### PostToolUse (hooks/posttool/)

| Hook | Purpose |
|------|---------|
| PostToolUse_artifact_validator | Validate artifacts after tool use |
| fact-guard_PostToolUse | Post-edit contamination and provenance check |

### UserPromptSubmit (hooks/userpromptsubmit/)

| Hook | Purpose |
|------|---------|
| UserPromptSubmit_claim_classifier | Classify incoming user claims for verification scope |

## Architecture

- **Plugin is canonical source.** Compatibility wrappers in `P:/.claude/hooks/` delegate to this plugin via import. Settings.json registration unchanged.
- **hooks_resolver.py** resolves the global hooks dir (`P:/.claude/hooks/`) for shared `__lib__` access and state file location.
- **HOOKS_DIR** in core modules resolves to `P:/.claude/hooks/` (via hooks_resolver), NOT the plugin directory. State files stay in the hooks dir.

### Import Pattern

Every hook uses `_bootstrap.py` for path setup (single point of change):

```python
# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---
```

`_bootstrap.py` adds plugin `lib/` and the global hooks dir to `sys.path`. This ensures hooks can import both plugin-local modules (`provenance`, `contamination`) and shared modules from `P:/.claude/hooks/__lib__/`. Hooks that need `HOOKS_DIR` use `_hooks_dir` from the bootstrap return value.

### Compatibility Wrappers

23 wrapper files in `P:/.claude/hooks/` delegate to plugin hooks via `compat_loader.py`. Each wrapper is a 6-line stub:

```python
#!/usr/bin/env python3
"""Delegates to cc-aca-epistemic plugin."""
import sys
sys.path.insert(0, "P:/packages/cc-aca-epistemic/lib")
from compat_loader import delegate
delegate(__file__)
```

`compat_loader.py` resolves the wrapper filename to the correct plugin `hooks/<phase>/` subdirectory and loads the plugin hook. It also uses `_bootstrap.py` for path setup (no duplicated resolver logic).

## Fact-Guard Integration

Absorbed from the standalone fact-guard plugin:

- **provenance.py** — claim provenance tracking (moved here)
- **contamination.py** — contamination detection (moved here)
- **fact-guard_PreToolUse.py** — PreToolUse structured-edit guard (kept as-is in pretool/)
- **fact-guard_PostToolUse.py** — PostToolUse contamination check (kept as-is in posttool/)

Modules that remain separate: `state.py`, `fact_extraction.py`, `file_patterns.py` (in `P:/.claude/hooks/__lib__/`).

## What Is NOT in This Plugin

- **Reasoning hooks** — belong in cc-aca-reasoning (or local hooks)
- **Behavioral hooks** — belong in cc-aca-behavioral (or local hooks)
- **Observability/telemetry** — belongs in cc-aca-session or local hooks
- **scanners/** — shared framework in `P:/.claude/hooks/__lib__/`
- **validators/** — shared framework in `P:/.claude/hooks/__lib__/`
