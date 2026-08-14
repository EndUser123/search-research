"""TDD Tests for CHS Reindex Content Extraction.

RED phase: Write failing tests first.
These tests define the expected behavior - implementation follows.

Implementation file: core/chs/scripts/reindex_from_jsonl.py
"""

from __future__ import annotations


class TestExtractTextContentToolResult:
    """Tests for extract_text_content() handling of tool_result blocks."""

    def test_tool_result_content_is_extracted_not_json_string(self) -> None:
        """tool_result content should be extracted as plain text, not stored as JSON string.

        CRIT-002: tool_result blocks have 'type' and 'content' fields.
        The content field contains the actual text that should be searchable.
        Currently, such blocks fall through to the else clause and get json.dumps'd.
        """
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        # Simulate the actual structure found in history.jsonl tool messages
        message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call_b8e2z1e2n3",
                    "content": "name: '/main'\ncategory: 'System'",
                }
            ],
        }

        result = extract_text_content(message)

        # The content should be extracted as plain text, NOT as a JSON string
        assert '"type"' not in result, (
            f"tool_result content was JSON-encoded instead of extracted. Got: {result[:100]}..."
        )
        assert '"tool_use_id"' not in result, (
            f"tool_result content was JSON-encoded instead of extracted. Got: {result[:100]}..."
        )
        # The actual content should be present
        assert "name: '/main'" in result or "/main" in result, (
            f"tool_result content was not properly extracted. Got: {result[:100]}..."
        )

    def test_tool_result_with_multiline_content(self) -> None:
        """tool_result content often contains multiline output that must be searchable."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call_abc123",
                    "content": "---\nname: '/process'\ncategory: 'Handler'\nstatus: 'completed'\n---",
                }
            ],
        }

        result = extract_text_content(message)

        # All content lines should be present
        assert "name: '/process'" in result
        assert "category: 'Handler'" in result
        assert "status: 'completed'" in result
        # Newlines should be preserved or normalized to spaces
        assert "---" in result

    def test_tool_result_in_array_with_other_blocks(self) -> None:
        """tool_result can appear alongside text blocks in content array."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Here is the result:"},
                {"type": "tool_result", "tool_use_id": "call_xyz789", "content": "Output: success"},
            ],
        }

        result = extract_text_content(message)

        # Both text and tool_result content should appear
        assert "Here is the result:" in result
        assert "Output: success" in result
        # Should NOT have JSON encoding artifacts
        assert '"type"' not in result

    def test_tool_result_empty_content(self) -> None:
        """tool_result with empty content should not cause errors."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "call_empty", "content": ""}],
        }

        result = extract_text_content(message)
        # Should not raise, should return empty string or handle gracefully
        assert isinstance(result, str)

    def test_tool_result_missing_content_field(self) -> None:
        """tool_result without content field should be handled gracefully."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call_no_content",
                    # Note: no 'content' field
                }
            ],
        }

        result = extract_text_content(message)
        # Should not raise, should return empty string
        assert isinstance(result, str)


class TestExtractTextContentToolRole:
    """Tests for extract_text_content() handling of tool role messages."""

    def test_tool_message_with_input_is_extracted(self) -> None:
        """Tool messages with 'input' field should have input extracted."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {"type": "tool_use", "name": "Read", "input": {"path": "/some/file.txt"}}

        result = extract_text_content(message)

        # Should contain the tool name and input
        assert "Read" in result
        assert "/some/file.txt" in result

    def test_thinking_block_is_handled(self) -> None:
        """Thinking blocks should be extracted with [Thinking] marker."""
        from core.chs.scripts.reindex_from_jsonl import extract_text_content

        message = {
            "role": "assistant",
            "content": [{"type": "thinking", "thinking": "Let me think about this..."}],
        }

        result = extract_text_content(message)

        assert "[Thinking]" in result
        assert "Let me think about this..." in result
