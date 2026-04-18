"""Tests for OpenCode model alias resolution."""

from ai_cli import DEFAULT_OPENCODE_MODEL, _resolve_opencode_model


class TestOpenCodeModelAliases:
    """Test model alias resolution function."""

    def test_kimi_alias_resolves(self):
        """Kimi alias resolves to full Kimi K2.5 TEE model ID."""
        result = _resolve_opencode_model("kimi")
        assert result == "chutes/moonshotai/Kimi-K2.5-TEE"

    def test_minimax_alias_resolves(self):
        """MiniMax alias resolves to full MiniMax M2.1 TEE model ID."""
        result = _resolve_opencode_model("minimax")
        assert result == "chutes/MiniMaxAI/MiniMax-M2.1-TEE"

    def test_full_model_id_passthrough(self):
        """Full model ID is passed through unchanged."""
        custom_id = "chutes/custom/model"
        result = _resolve_opencode_model(custom_id)
        assert result == custom_id

    def test_none_returns_default(self):
        """None input returns DEFAULT_OPENCODE_MODEL."""
        result = _resolve_opencode_model(None)
        assert result == DEFAULT_OPENCODE_MODEL

    def test_empty_string_returns_default(self):
        """Empty string input returns DEFAULT_OPENCODE_MODEL."""
        result = _resolve_opencode_model("")
        assert result == DEFAULT_OPENCODE_MODEL

    def test_unknown_alias_returns_as_is(self):
        """Unknown alias values are returned as-is (fallback behavior)."""
        unknown = "some_unknown_alias"
        result = _resolve_opencode_model(unknown)
        # Should return the input as-is when not in aliases dict and not empty/None
        assert result == unknown
