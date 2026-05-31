#!/usr/bin/env python3
"""
SessionStart Hook - Hook Health Smoke Check

Validates that hook files wired in settings.json:
1) Exist
2) Parse (AST)
3) Import top-level code without executing __main__
"""

from __future__ import annotations

import ast
import json
import os
import runpy
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

try:
    from __lib.hook_base import hook_main
except ImportError:

    def hook_main(func):
        return func


HOOKS_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = HOOKS_DIR.parent / "settings.json"
REPORT_PATH = HOOKS_DIR / "logs" / "diagnostics" / "hook_health.json"
FALLBACK_REPORT_PATH = Path(tempfile.gettempdir()) / "claude_hooks" / "hook_health.json"


def _check_file(path: Path) -> str | None:
    if not path.exists():
        return f"MISSING: {path}"
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"READ_FAIL: {path} ({type(e).__name__}: {e})"

    try:
        ast.parse(src)
    except SyntaxError as e:
        return f"SYNTAX_FAIL: {path}:{e.lineno} ({e.msg})"

    try:
        # Runs import-time code only; __main__ blocks are not executed.
        runpy.run_path(str(path), run_name="__hook_healthcheck__")
    except Exception as e:
        return f"IMPORT_FAIL: {path} ({type(e).__name__}: {e})"
    return None


# Subdirectories that contain non-hook utilities (not actual orphan hooks)
_ORPHAN_EXCLUDE_SUBDIRS = frozenset(
    [
        "damage-control",
        "docs",
        "analysis",
        "baselines",
        "evidence",
        "competence",
        "scripts",
        "_archive",
        "tests",
    ]
)

# File-name prefixes for known non-hook utilities (standalone analyzers, not registered hooks)
# Covers infrastructure support modules that are imported by hooks but are NOT hooks themselves.
# These are top-level utility modules (e.g., artifact_claims.py, assumption_audit_v2.py,
# cc_diagnostic_logger.py, shared_utils.py) that live in hooks/ but are never registered
# as hooks in any router or settings.json.
#
# Two matching modes:
# - startswith: for prefixes WITHOUT trailing underscore (e.g., "dreaming_", "debug_")
#   applied via name.startswith(prefix)
# - underscore: for prefixes WITH trailing underscore (e.g., "artifact_", "clean_")
#   applied via name.startswith(prefix) — the underscore is part of the prefix string
_ORPHAN_EXCLUDE_PREFIXES = (
    # Infrastructure / support modules (underscore-delimited)
    "artifact_",
    "assumption_",
    "auto_",
    "autonomy_",
    "backup_",
    "block_",
    "cc_",
    "change_",
    "check_",
    "clean_",
    "cleanup_",
    "command_",
    "commit_",
    "claim_",
    "compatibility_",
    "config_",
    "constraint_",
    "context_",
    "conversational_",
    "credential_",
    "cross_",
    "db_",
    "decision_",
    "delegate_",
    "demand_",
    "diagnostic_",
    "discovery_",
    "domain_",
    "edit_",
    "empirical_",
    "enforcement_",
    "evidence_",
    "execution_",
    "exploration_",
    "failure_",
    "feedback_",
    "find_",
    "focus_",
    "forward_",
    "framework_",
    "generic_",
    "governance_",
    "graph_",
    "grounded_",
    "guard_",
    "handoff_",
    "health_",
    "heuristic_",
    "hypothesis_",
    "idea_",
    "identity_",
    "impact_",
    "ingest_",
    "inspect_",
    "intent_",
    "internal_",
    "invalidate_",
    "journal_",
    "knowledge_",
    "ledger_",
    "library_",
    "lint_",
    "logic_",
    "loss_",
    "manifest_",
    "memory_",
    "merge_",
    "model_",
    "monitor_",
    "motivation_",
    "naming_",
    "narrative_",
    "norm_",
    "novelty_",
    "observation_",
    "opinion_",
    "ordering_",
    "origin_",
    "outcome_",
    "overlap_",
    "ownership_",
    "pairing_",
    "parsing_",
    "patch_",
    "path_",
    "pattern_",
    "phase_",
    "placement_",
    "policy_",
    "predict_",
    "preference_",
    "priority_",
    "problem_",
    "process_",
    "prompt_",
    "provenance_",
    "quality_",
    "query_",
    "rank_",
    "rating_",
    "reasoning_",
    "recommendation_",
    "recovery_",
    "refinement_",
    "reflection_",
    "region_",
    "relevance_",
    "render_",
    "report_",
    "requirement_",
    "resolve_",
    "resource_",
    "restore_",
    "result_",
    "retrieval_",
    "rollback_",
    "root_",
    "routing_",
    "safety_",
    "saliency_",
    "schema_",
    "scope_",
    "scratch_",
    "search_",
    "segment_",
    "self_",
    "semantic_",
    "sensation_",
    "sequence_",
    "session_",
    "severity_",
    "signal_",
    "similarity_",
    "skill_",
    "sleuth_",
    "smart_",
    "snapshot_",
    "source_",
    "span_",
    "spec_",
    "stage_",
    "state_",
    "status_",
    "storage_",
    "story_",
    "strategy_",
    "structural_",
    "subagent_",
    "suggestion_",
    "summary_",
    "suppression_",
    "synchronization_",
    "syntax_",
    "tag_",
    "tactic_",
    "taxonomy_",
    "template_",
    "terminal_",
    "test_",
    "theory_",
    "thinking_",
    "thread_",
    "throughput_",
    "timestamp_",
    "tool_",
    "topic_",
    "tracking_",
    "trade_",
    "transformation_",
    "trigger_",
    "truth_",
    "type_",
    "upstream_",
    "utterance_",
    "validation_",
    "value_",
    "version_",
    "violation_",
    "visibility_",
    "warning_",
    "weight_",
    "workflow_",
    "worktree_",
    # Explicit standalone analyzers and scripts
    "analyze_",
    "adversarial_",
)

# Router files that should be excluded from orphan detection
_ROUTER_FILES = frozenset(
    [
        "PreToolUse.py",
        "Stop.py",
        "Stop_router.py",
        "PostToolUse_router.py",
        "UserPromptSubmit.py",
        "PostToolUse.py",
        "SessionStart.py",
    ]
)

# Subdirectory packages containing router-loaded hooks
_HOOK_SUBDIRS = frozenset(["PreToolUse", "stop", "posttooluse", "UserPromptSubmit_modules"])


def _snake_to_filename(snake_case: str) -> str:
    """Convert snake_case to PascalCase filename convention.

    E.g. 'breadcrumb_tracker_hook' -> 'BreadcrumbTrackerHook'
    Used to map registry.register() class names to their filenames.
    """
    return "".join(word.capitalize() for word in snake_case.split("_")) + ".py"


def _extract_hook_targets(command: str) -> list[Path]:
    """Extract python hook targets from a settings command."""
    targets: list[Path] = []
    cmd = command.strip()
    if not cmd:
        return targets

    tokens = [t.strip().strip('"').strip("'") for t in cmd.split()]
    lowered = [t.lower() for t in tokens]

    for i, token in enumerate(lowered):
        if token.endswith("hook_runner.py") and i + 1 < len(tokens):
            candidate = Path(tokens[i + 1])
            if candidate.suffix.lower() == ".py":
                targets.append(candidate)

    if not targets:
        for token in tokens:
            if token.lower().endswith(".py") and "hook_runner.py" not in token.lower():
                targets.append(Path(token))
                break
    return targets


def _collect_wired_hook_files() -> list[Path]:
    """Collect hooks registered directly in settings.json."""
    if not SETTINGS_PATH.exists():
        return []
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    hooks = settings.get("hooks", {})
    files: list[Path] = []
    seen: set[str] = set()
    for event_entries in hooks.values():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            hook_list = entry.get("hooks", []) if isinstance(entry, dict) else []
            for hook_def in hook_list:
                if not isinstance(hook_def, dict):
                    continue
                command = str(hook_def.get("command", ""))
                for path in _extract_hook_targets(command):
                    resolved = path if path.is_absolute() else (HOOKS_DIR.parent / path)
                    key = str(resolved).lower()
                    if key not in seen:
                        seen.add(key)
                        files.append(resolved)
    return files


def _collect_router_hooks() -> set[str]:
    """Collect all hooks registered via router patterns.

    Scans five registration mechanisms:
    1. SETUP_SEQUENCE in SessionStart.py
    2. UNIVERSAL + TOOL_HOOKS in PreToolUse.py
    3. HOOK_SEQUENCE in Stop_router.py
    4. create_registry() in posttooluse/__init__.py
    5. core_hook_modules in UserPromptSubmit_modules/registry.py
    """
    import re

    router_hooks: set[str] = set()

    # ── 1. SessionStart SETUP_SEQUENCE ─────────────────────────────────────
    session_start = HOOKS_DIR / "SessionStart.py"
    if session_start.exists():
        try:
            src = session_start.read_text(encoding="utf-8")
            # Extract: "SessionStart_foo.py"
            for match in re.finditer(r'"(SessionStart_[^"]+\.py)"', src):
                router_hooks.add(match.group(1))
        except Exception:
            pass

    # ── 2. PreToolUse UNIVERSAL + TOOL_HOOKS ───────────────────────────────
    pre_tool_use = HOOKS_DIR / "PreToolUse.py"
    if pre_tool_use.exists():
        try:
            src = pre_tool_use.read_text(encoding="utf-8")
            # UNIVERSAL = [ "PreToolUse_foo.py", "PreToolUse/bar.py", ... ]
            universal_match = re.search(r"UNIVERSAL\s*=\s*\[(.*?)\]", src, re.DOTALL)
            if universal_match:
                for m in re.finditer(r'"([^"]+\.py)"', universal_match.group(1)):
                    router_hooks.add(m.group(1))

            # COMPAT_POST_ROUTER_HOOKS = [ ... ]
            compat_match = re.search(r"COMPAT_POST_ROUTER_HOOKS\s*=\s*\[(.*?)\]", src, re.DOTALL)
            if compat_match:
                for m in re.finditer(r'"([^"]+\.py)"', compat_match.group(1)):
                    router_hooks.add(m.group(1))

            # TOOL_HOOKS = { "Write": [...], "Edit": [...], ... }
            tool_hooks_match = re.search(r"TOOL_HOOKS\s*=\s*\{(.*?)\n\}", src, re.DOTALL)
            if tool_hooks_match:
                for m in re.finditer(r'"([^"]+\.py)"', tool_hooks_match.group(1)):
                    router_hooks.add(m.group(1))
        except Exception:
            pass

    # ── 3. Stop_router HOOK_SEQUENCE ───────────────────────────────────────
    stop_router = HOOKS_DIR / "Stop_router.py"
    if stop_router.exists():
        try:
            src = stop_router.read_text(encoding="utf-8")
            # HOOK_SEQUENCE = [ ("foo.py", env, default, "inprocess"), ... ]
            seq_match = re.search(r"HOOK_SEQUENCE\s*=\s*\[(.*?)\]", src, re.DOTALL)
            if seq_match:
                for m in re.finditer(r'\("([^"]+\.py)"', seq_match.group(1)):
                    router_hooks.add(m.group(1))
        except Exception:
            pass

    # ── 4. posttooluse/__init__.py create_registry() class names ───────────
    post_init = HOOKS_DIR / "posttooluse" / "__init__.py"
    if post_init.exists():
        try:
            src = post_init.read_text(encoding="utf-8")
            # registry.register("name", ClassName())
            for m in re.finditer(r'registry\.register\("[^"]+",\s*(\w+)\(', src):
                class_name = m.group(1)
                # ClassName like BreadcrumbTrackerHook -> breadcrumb_tracker_hook.py
                # FIX: Use snake directly (already lowercase) instead of _snake_to_filename
                # which converts to PascalCase, mismatching the actual snake_case filenames on disk
                snake = re.sub(
                    r"(?<=[a-z])([A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", r"_\1", class_name
                ).lower()
                filename = f"{snake}.py"
                # All posttooluse hooks live in posttooluse/ subdirectory
                router_hooks.add(f"posttooluse/{filename}")
        except Exception:
            pass

    # ── 5. UserPromptSubmit_modules/registry.py core_hook_modules ───────────
    ups_registry = HOOKS_DIR / "UserPromptSubmit_modules" / "registry.py"
    if ups_registry.exists():
        try:
            src = ups_registry.read_text(encoding="utf-8")
            # core_hook_modules = [ "foo", "bar", ... ]
            # each maps to UserPromptSubmit_modules/foo.py
            modules_match = re.search(r"^core_hook_modules\s*=\s*\[(.*?)\]", src, re.DOTALL)
            if modules_match:
                for m in re.finditer(r'"(\w+)"', modules_match.group(1)):
                    router_hooks.add(f"UserPromptSubmit_modules/{m.group(1)}.py")
        except Exception:
            pass

    return router_hooks


def _collect_orphan_hooks(wired: list[Path]) -> list[Path]:
    """Find hook .py files not in any wired registry.

    Cross-checks settings.json direct entries AND all five router patterns.
    """
    wired_names = {p.name.lower() for p in wired}
    router_hooks = _collect_router_hooks()

    # Normalize: some entries are "dir/file.py", some are "file.py"
    # Build two lookup sets for flexible matching (all lowercase for case-insensitive comparison)
    flat_names: set[str] = set()  # just "foo.py" (lowercase)
    path_names: set[str] = set()  # "dir/foo.py" (lowercase)
    for hook in router_hooks:
        path_names.add(hook.lower())
        flat_names.add(hook.split("/")[-1].lower())

    def _is_wired(name: str) -> bool:
        """Return True if name matches any wired or router-registered hook."""
        lower = name.lower()
        if lower in wired_names:
            return True
        if lower in flat_names:
            return True
        # Also check path-style entries
        if lower in path_names:
            return True
        # Normalize "dir/file.py" -> "file.py" and check
        if "/" in name:
            if name.split("/")[-1].lower() in wired_names:
                return True
        return False

    orphans: list[Path] = []

    for item in sorted(HOOKS_DIR.iterdir()):
        name = item.name
        # Exclude hidden, private, non-.py files
        if name.startswith(".") or name.startswith("_"):
            continue
        if not name.endswith(".py"):
            continue
        # Exclude self
        if name == "SessionStart_hook_health_check.py":
            continue
        # Exclude router files themselves
        if name in _ROUTER_FILES:
            continue
        # Exclude subdirectory packages (hooks inside them are tracked via path_names)
        if item.is_dir() and name.lower() in {s.lower() for s in _HOOK_SUBDIRS}:
            continue
        # Exclude known non-hook subdirectory contents
        if item.is_dir() and name.lower() in {s.lower() for s in _ORPHAN_EXCLUDE_SUBDIRS}:
            continue

        # Exclude known non-hook utility files by prefix (analyzers, standalone scripts)
        # FIX: Use case-insensitive comparison since _ORPHAN_EXCLUDE_PREFIXES is all-lowercase
        if item.is_file() and any(name.lower().startswith(p) for p in _ORPHAN_EXCLUDE_PREFIXES):
            continue

        # For files in HOOK_SUBDIRS, construct the path-style name and check
        hook_name = name
        if item.is_file():
            # Check both flat and path-style
            if _is_wired(hook_name):
                continue

        # Also exclude if it's in a subdir but the subdir is excluded
        # (handled above by skipping _HOOK_SUBDIRS dirs entirely)

        orphans.append(item)

    return orphans


def _report_paths() -> list[Path]:
    override = os.environ.get("HOOK_HEALTH_REPORT_PATH", "").strip()
    if override:
        return [Path(override)]
    return [REPORT_PATH, FALLBACK_REPORT_PATH]


def _load_previous_report(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _write_report(files_checked: list[Path], failures: list[str]) -> Path:
    base_report = {
        "status": "ok" if not failures else "fail",
        "checked_at": datetime.now(UTC).isoformat(),
        "files_checked_count": len(files_checked),
        "files_checked": [str(p) for p in files_checked],
        "failure_count": len(failures),
        "failures": failures,
    }
    last_error = None
    for path in _report_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            previous = _load_previous_report(path)
            prev_failures = []
            prev_checked_at = None
            if isinstance(previous, dict):
                prev_checked_at = previous.get("checked_at")
                raw_prev_failures = previous.get("failures", [])
                if isinstance(raw_prev_failures, list):
                    prev_failures = [str(x) for x in raw_prev_failures]

            prev_set = set(prev_failures)
            curr_set = {str(x) for x in failures}
            new_failures = sorted(list(curr_set - prev_set))
            resolved_failures = sorted(list(prev_set - curr_set))

            report = dict(base_report)
            report["report_path"] = str(path)
            report["previous_checked_at"] = str(prev_checked_at or "")
            report["new_failure_count"] = len(new_failures)
            report["resolved_failure_count"] = len(resolved_failures)
            report["unchanged_failure_count"] = len(curr_set & prev_set)
            report["new_failures"] = new_failures
            report["resolved_failures"] = resolved_failures

            path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            return path
        except Exception as e:
            last_error = e
            continue
    raise OSError(f"Unable to write hook health report: {last_error}")


@hook_main
def main() -> int:
    enabled = os.environ.get("HOOK_HEALTHCHECK_ENABLED", "1").lower() in ("1", "true", "yes")
    if not enabled:
        print("{}")
        return 0

    files = _collect_wired_hook_files()
    if not files:
        print("{}")
        return 0

    failures: list[str] = []
    for path in files:
        issue = _check_file(path)
        if issue:
            failures.append(issue)

    # Orphan detection: warn about hook files not in any registry
    orphans = _collect_orphan_hooks(files)
    for orphan in orphans:
        failures.append(f"ORPHAN: {orphan.name} (wired but not registered)")

    report_path = None
    report_write_error = None
    try:
        report_path = _write_report(files, failures)
    except Exception as e:
        # Health check itself should never block startup.
        report_write_error = f"{type(e).__name__}: {e}"

    if not failures:
        if report_write_error:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": (
                                "Hook health check passed, but report persistence failed.\n"
                                f"Error: {report_write_error}"
                            ),
                        }
                    }
                )
            )
            return 0
        print("{}")
        return 0

    preview = failures[:12]
    suffix = (
        "" if len(failures) <= len(preview) else f"\n...and {len(failures) - len(preview)} more"
    )
    message = (
        "Hook health check found startup risks:\n"
        + "\n".join(f"- {line}" for line in preview)
        + suffix
    )
    if report_path:
        message += f"\n\nReport: {report_path}"
    elif report_write_error:
        message += f"\n\nReport write failed: {report_write_error}"
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": message,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
