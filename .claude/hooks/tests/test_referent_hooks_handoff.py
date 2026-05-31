from __future__ import annotations

import json
import sys
from pathlib import Path

# Same path setup as test_referent_hooks.py
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

from referent_anchor import _strip_pasted_content, referent_anchor_hook
from base import HookContext


class TestHandoffPaste:
    """Regression: pasted handoffs with quoted blocks should not create false anchors."""

    def test_large_quoted_block_stripped_before_extraction(self):
        """Quoted blocks >=200 chars are stripped so anchors only come from user's own words."""
        from referent_anchor import _strip_pasted_content

        # Simulate the actual handoff paste from the incident
        prompt_with_handoff = (
            "why are our LLMs being lazy, and how can we stop that? Here's a handoff:\n\n"
            '" Lazy Reasoning RCA Handoff\n'
            "Assumptions Made (Zero Verification)\n"
            "1. Cause: Assumed it was a PreToolUse hook exit(2), but didn't verify which hook\n"
            "2. Impact: Assumed it was harmless because session continued\n"
            "3. Immutability: Called it 'transient' with no evidence it won't recur\n"
            "4. Relevance: Assumed unrelated to my changes without checking\n"
            "5. Urgency: Declared 'no further investigation needed' without enumerating...\n"
            '"\n'
            "we did some plugin moves. please make the changes."
        )
        stripped = _strip_pasted_content(prompt_with_handoff)
        # After stripping, the large quoted block is gone
        assert "Assumptions Made" not in stripped
        assert "Cause" not in stripped
        assert "PreToolUse hook" not in stripped
        # User's own question is still there
        assert "lazy" in stripped or "LLMs" in stripped

    def test_no_false_scope_from_handoff_in_referent_context(self):
        """Hook should not extract anchors from pasted handoff in referential context."""
        tid = "test_handoff"
        state_file = Path.home() / ".claude" / ".artifacts" / tid / "referent_anchors.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.unlink(missing_ok=True)  # clean up stale state first

        # User's question references "those findings" but the bullet list
        # is inside a large quoted block from a prior model handoff
        prompt = (
            "Check those findings and confirm which ones actually exist.\n\n"
            '" Lazy Reasoning RCA Handoff\n'
            "- silently changed behavior\n"
            "- dropped work product\n"
            "- indicates a hook that should be fixed\n"
            "- will recur in a more impactful context\n"
            '"\n'
        )
        ctx = HookContext(
            prompt=prompt,
            data={},
            session_id="test_handoff_session",
            terminal_id=tid,
        )
        referent_anchor_hook(ctx)

        state = json.loads(state_file.read_text(encoding="utf-8"))
        # The large quoted block should be stripped, so no anchors from it
        # The user's own words have no table/list, so no anchors created
        assert state.get("status") == "no_anchors" or len(state.get("anchor_terms", [])) == 0
        state_file.unlink(missing_ok=True)

    def test_fenced_code_block_stripped(self):
        """Fenced code blocks are stripped before anchor extraction."""
        from referent_anchor import _strip_pasted_content

        prompt = (
            "Investigate those items.\n\n"
            "```\n"
            "- silently changed behavior\n"
            "- dropped work product\n"
            "- indicates a hook that should be fixed\n"
            "```\n"
        )
        stripped = _strip_pasted_content(prompt)
        assert "silently changed behavior" not in stripped
        assert "Investigate" in stripped  # user word preserved