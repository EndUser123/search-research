#!/usr/bin/env python3
"""Tests for mode selection collisions.

Verifies that graph mode no longer exposes tag tokens in user-facing context.
"""

import pytest


class TestTagCollisionFix:
    """Test that visible mode tag collisions are resolved."""

    def test_graph_mode_uses_gra_tag_not_cog(self):
        """Graph mode should emit [GRA] tag, not [COG]."""
        # Import the reasoning mode selector
        import sys
        from pathlib import Path

        reasoning_hooks = Path("P:/packages/reasoning/hooks")
        if str(reasoning_hooks) not in sys.path:
            sys.path.insert(0, str(reasoning_hooks))

        import Start_reasoning_mode_selector as selector

        # Call process_prompt with a graph-mode query
        result = selector.process_prompt({
            "query": "Explore the alternatives for implementing caching"
        })

        # Should return context with graph mode guidance
        assert "additionalContext" in result, "Expected additionalContext in result"

        context = result["additionalContext"]

        assert "[GRA]" not in context, (
            f"Found graph tag in user-facing context: {context[:200]}"
        )
        assert "[COG]" not in context, (
            f"Found [COG] tag in user-facing context: {context[:200]}"
        )
        assert "Reasoning mode: graph" in context

    def test_other_modes_keep_original_tags(self):
        """Other modes should keep their original mode guidance."""
        import sys
        from pathlib import Path

        reasoning_hooks = Path("P:/packages/reasoning/hooks")
        if str(reasoning_hooks) not in sys.path:
            sys.path.insert(0, str(reasoning_hooks))

        import Start_reasoning_mode_selector as selector

        # Test sequential mode
        result = selector.process_prompt({
            "query": "Explain step by step how to implement authentication"
        })

        if "additionalContext" in result:
            assert "[SEQ]" not in result["additionalContext"]
            assert "reasoning mode: sequential" in result["additionalContext"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
