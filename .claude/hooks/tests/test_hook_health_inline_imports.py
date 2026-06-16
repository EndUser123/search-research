"""Tests for the inline-import-detection branch in _collect_router_hooks().

Regression: The 6th collection pattern in SessionStart_hook_health_check.py
scans router files (PostToolUse_router.py, PreToolUse.py, Stop_router.py,
SessionStart.py, UserPromptSubmit_router.py) for `from X import Y` and
`import X` statements where X resolves to a sibling .py file in HOOKS_DIR.
This is what kept `PostToolUse_artifact_access_tracker.py` from being
flagged as ORPHAN when the only thing wiring it up is an import in
PostToolUse_router.py:617.

Without this branch, the health check would emit false-positive ORPHAN
findings for any library module imported by a router.
"""
from __future__ import annotations

import unittest

# tests/ -> P:/.claude/hooks/ is on sys.path via conftest.py
from SessionStart_hook_health_check import (  # noqa: E402
    _collect_router_hooks,
    _collect_orphan_hooks,
)


class TestInlineImportDetection(unittest.TestCase):
    """The new 6th pattern: sibling .py files imported by any router."""

    def test_artifact_access_tracker_recognized_via_posttooluse_router_import(self):
        """PostToolUse_artifact_access_tracker.py is imported by
        PostToolUse_router.py:617 (`from PostToolUse_artifact_access_tracker
        import track_tool_use`). It must show up in the router-hooks set
        so it is not flagged ORPHAN.
        """
        router_hooks = _collect_router_hooks()
        assert "PostToolUse_artifact_access_tracker.py" in router_hooks, (
            "Inline-imported library module missing from router-hooks set. "
            "The 6th pattern in _collect_router_hooks() failed to recognize "
            "the `from X import Y` statement in PostToolUse_router.py."
        )

    def test_genuine_orphan_still_flagged(self):
        """A hook file that is NOT imported by any router and NOT in any
        settings.json registry must still appear as ORPHAN.
        """
        # Build a minimal wired list (empty is fine — we're checking
        # `_is_wired` behavior via the orphan detection pass).
        orphans = _collect_orphan_hooks(wired=[])
        orphan_names = {p.name for p in orphans}

        # PostToolUse_adversarial_aggregate.py is genuinely dead (verified
        # in the RCA — top-level runnable, not imported by any router).
        # It must STILL be reported as orphan.
        assert "PostToolUse_adversarial_aggregate.py" in orphan_names, (
            "Genuine orphan was incorrectly classified as wired. "
            "The 6th pattern is over-matching."
        )

    def test_stdlib_imports_are_ignored(self):
        """`import json`, `import os`, `import re` etc. must NOT add
        `json.py`/`os.py`/`re.py` to the router-hooks set (they don't
        exist as siblings in HOOKS_DIR, so the filter naturally excludes
        them — but verify the filter works).
        """
        # Create a synthetic router file that imports stdlib + a sibling.
        # We exercise this by inspecting what the real routers import.
        router_hooks = _collect_router_hooks()

        # No stdlib module name should ever be a sibling .py in HOOKS_DIR.
        for name in ("json", "os", "sys", "re", "ast", "pathlib"):
            assert f"{name}.py" not in router_hooks, (
                f"Stdlib module `{name}` leaked into router-hooks set. "
                "The 6th pattern is not filtering non-sibling imports."
            )

    def test_router_scan_is_does_not_match_dotted_subpackage_imports(self):
        """`from posttooluse.breadcrumb import X` should NOT add the
        dotted path as a flat file. The regex only matches top-level
        bare names. This guards against future refactors that break
        the dotted-import path.
        """
        router_hooks = _collect_router_hooks()
        # posttooluse/ subpackage entries are added by pattern 4
        # (create_registry class names), not by pattern 6.
        # The router-hooks set may legitimately contain path-style
        # entries from pattern 4; we just verify pattern 6 didn't
        # add a malformed entry. Spot-check: no entry should be a
        # raw dotted name.
        for entry in router_hooks:
            assert "." not in entry.replace(".py", ""), (
                f"Router-hooks entry has unexpected dotted form: {entry!r}"
            )


class TestOrphanFalsePositiveRepro:
    """End-to-end: the original 3 reported orphans split into 1 FP + 2 real."""

    def test_only_artifact_access_tracker_resolved(self):
        """Of the 3 ORPHAN entries originally reported, only
        `PostToolUse_artifact_access_tracker.py` should be cleared
        by the inline-import fix. The other 2 (adversarial_aggregate,
        artifact_scraper) are genuinely dead code and must remain.
        """
        router_hooks = _collect_router_hooks()
        orphans = _collect_orphan_hooks(wired=[])
        orphan_names = {p.name for p in orphans}

        # The inline-imported one MUST be wired.
        assert "PostToolUse_artifact_access_tracker.py" in router_hooks
        # And therefore must NOT appear as orphan.
        assert "PostToolUse_artifact_access_tracker.py" not in orphan_names

        # The two genuinely dead files MUST still appear as orphan.
        assert "PostToolUse_adversarial_aggregate.py" in orphan_names
        assert "PostToolUse_artifact_scraper.py" in orphan_names


if __name__ == "__main__":
    unittest.main()
