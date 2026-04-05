#!/usr/bin/env python3
"""Tests for [COG] tag collision fix - TASK-001.

Verifies that graph mode uses [GRA] tag instead of [COG] to avoid
collision with cognitive frameworks.
"""

import pytest


class TestTagCollisionFix:
    """Test that [COG] tag collision is resolved."""

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

        # Should return context with [GRA] tag for graph mode
        assert "additionalContext" in result, "Expected additionalContext in result"

        context = result["additionalContext"]

        # Graph mode should use [GRA] tag
        assert "[GRA]" in context, (
            f"Expected [GRA] tag for graph mode, but got: {context[:200]}"
        )

        # Should NOT contain [COG] for graph mode
        # Note: [COG] is reserved for cognitive frameworks
        assert "[COG]" not in context, (
            f"Found [COG] tag in graph mode context (collision): {context[:200]}"
        )

    def test_other_modes_keep_original_tags(self):
        """Other modes should keep their original tags."""
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
            # Sequential should use [SEQ]
            assert "[SEQ]" in result["additionalContext"] or "sequential" in result["additionalContext"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
