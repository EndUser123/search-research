"""
Tests for the centralized display configuration module.

Tests DisplayMode enum, DisplayConfig dataclass, validation logic,
and mode determination functions.
"""

import pytest

from yt_fts.core.display_config import (
    DisplayMode,
    DisplayConfig,
    validate_display_mode,
    get_display_mode,
    create_display_config,
)


class TestDisplayMode:
    """Test DisplayMode enum."""

    def test_display_mode_values(self) -> None:
        """Test DisplayMode has expected values."""
        assert DisplayMode.FZF == "fzf"
        assert DisplayMode.RICH == "rich"
        assert DisplayMode.SIMPLE == "simple"
        assert DisplayMode.VANILLA == "vanilla"
        assert DisplayMode.JSON == "json"

    def test_display_mode_is_string_enum(self) -> None:
        """Test DisplayMode is a string enum (comparable to strings)."""
        assert DisplayMode.FZF == "fzf"
        assert DisplayMode.RICH == "rich"  # Direct comparison works for string enums
        assert DisplayMode.RICH.value == "rich"  # .value gets the string


class TestDisplayConfig:
    """Test DisplayConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default DisplayConfig values."""
        config = DisplayConfig()
        assert config.mode == DisplayMode.VANILLA
        assert config.rich_display_mode == "progress"
        assert config.use_rich_progress is False
        assert config.use_fzf is False
        assert config.use_simple is False
        assert config.console is None

    def test_config_with_rich_mode(self) -> None:
        """Test DisplayConfig with RICH mode."""
        config = DisplayConfig(mode=DisplayMode.RICH, rich_display_mode="table")
        assert config.mode == DisplayMode.RICH
        assert config.rich_display_mode == "table"

    def test_config_post_init_validates_rich_display_mode(self) -> None:
        """Test that invalid rich_display_mode defaults to 'progress'."""
        config = DisplayConfig(mode=DisplayMode.RICH, rich_display_mode="invalid")
        assert config.rich_display_mode == "progress"


class TestValidateDisplayMode:
    """Test validate_display_mode function."""

    def test_vanilla_mode_when_no_flags(self) -> None:
        """Test VANILLA mode when no display flags are set."""
        mode, warnings = validate_display_mode()
        assert mode == DisplayMode.VANILLA
        assert warnings == []

    def test_fzf_mode(self) -> None:
        """Test FZF mode detection."""
        mode, warnings = validate_display_mode(use_fzf=True)
        assert mode == DisplayMode.FZF
        assert warnings == []

    def test_rich_mode(self) -> None:
        """Test RICH mode detection."""
        mode, warnings = validate_display_mode(use_rich_progress=True)
        assert mode == DisplayMode.RICH
        assert warnings == []

    def test_simple_mode(self) -> None:
        """Test SIMPLE mode detection."""
        mode, warnings = validate_display_mode(use_simple=True)
        assert mode == DisplayMode.SIMPLE
        assert warnings == []

    def test_rich_mode_with_table_display(self) -> None:
        """Test RICH mode with table display option."""
        mode, warnings = validate_display_mode(
            use_rich_progress=True, rich_display="table"
        )
        assert mode == DisplayMode.RICH
        assert warnings == []

    def test_invalid_rich_display_produces_warning(self) -> None:
        """Test invalid rich_display mode produces warning."""
        mode, warnings = validate_display_mode(
            use_rich_progress=True, rich_display="invalid"
        )
        assert mode == DisplayMode.RICH
        assert len(warnings) == 1
        assert "Invalid rich-display mode" in warnings[0]
        assert "invalid" in warnings[0]

    def test_conflicting_modes_raises_error(self) -> None:
        """Test conflicting display modes raises ValueError."""
        with pytest.raises(ValueError, match="Conflicting display modes"):
            validate_display_mode(use_fzf=True, use_simple=True)

    def test_conflicting_modes_with_rich_and_simple(self) -> None:
        """Test conflicting RICH and SIMPLE modes raises ValueError."""
        with pytest.raises(ValueError, match="Conflicting display modes"):
            validate_display_mode(use_rich_progress=True, use_simple=True)

    def test_conflicting_modes_all_three(self) -> None:
        """Test all three modes enabled raises ValueError."""
        with pytest.raises(ValueError, match="Conflicting display modes"):
            validate_display_mode(
                use_rich_progress=True, use_fzf=True, use_simple=True
            )

    def test_error_message_lists_conflicting_modes(self) -> None:
        """Test error message lists the conflicting modes."""
        with pytest.raises(ValueError) as exc_info:
            validate_display_mode(use_fzf=True, use_simple=True)

        error_msg = str(exc_info.value)
        assert "fzf" in error_msg
        assert "simple" in error_msg


class TestGetDisplayMode:
    """Test get_display_mode convenience function."""

    def test_get_display_mode_vanilla(self) -> None:
        """Test get_display_mode returns VANILLA by default."""
        mode = get_display_mode()
        assert mode == DisplayMode.VANILLA

    def test_get_display_mode_fzf(self) -> None:
        """Test get_display_mode returns FZF."""
        mode = get_display_mode(use_fzf=True)
        assert mode == DisplayMode.FZF

    def test_get_display_mode_rich(self) -> None:
        """Test get_display_mode returns RICH."""
        mode = get_display_mode(use_rich_progress=True)
        assert mode == DisplayMode.RICH

    def test_get_display_mode_simple(self) -> None:
        """Test get_display_mode returns SIMPLE."""
        mode = get_display_mode(use_simple=True)
        assert mode == DisplayMode.SIMPLE

    def test_get_display_mode_raises_on_conflict(self) -> None:
        """Test get_display_mode raises ValueError on conflict."""
        with pytest.raises(ValueError, match="Conflicting display modes"):
            get_display_mode(use_fzf=True, use_simple=True)


class TestCreateDisplayConfig:
    """Test create_display_config factory function."""

    def test_create_default_config(self) -> None:
        """Test creating default DisplayConfig."""
        config = create_display_config()
        assert config.mode == DisplayMode.VANILLA
        assert config.use_rich_progress is False
        assert config.use_fzf is False
        assert config.use_simple is False

    def test_create_fzf_config(self) -> None:
        """Test creating FZF DisplayConfig."""
        config = create_display_config(use_fzf=True)
        assert config.mode == DisplayMode.FZF
        assert config.use_fzf is True
        assert config.use_rich_progress is False
        assert config.use_simple is False

    def test_create_rich_config(self) -> None:
        """Test creating RICH DisplayConfig."""
        config = create_display_config(use_rich_progress=True)
        assert config.mode == DisplayMode.RICH
        assert config.use_rich_progress is True
        assert config.use_fzf is False
        assert config.use_simple is False

    def test_create_rich_config_with_table_mode(self) -> None:
        """Test creating RICH DisplayConfig with table mode."""
        config = create_display_config(
            use_rich_progress=True, rich_display="table"
        )
        assert config.mode == DisplayMode.RICH
        assert config.rich_display_mode == "table"

    def test_create_simple_config(self) -> None:
        """Test creating SIMPLE DisplayConfig."""
        config = create_display_config(use_simple=True)
        assert config.mode == DisplayMode.SIMPLE
        assert config.use_simple is True
        assert config.use_fzf is False
        assert config.use_rich_progress is False

    def test_create_config_with_console(self) -> None:
        """Test creating DisplayConfig with console."""
        mock_console = object()  # Use any object for testing
        config = create_display_config(console=mock_console)
        assert config.console is mock_console

    def test_create_config_raises_on_conflict(self) -> None:
        """Test create_display_config raises ValueError on conflict."""
        with pytest.raises(ValueError, match="Conflicting display modes"):
            create_display_config(use_fzf=True, use_simple=True)

    def test_create_config_fixes_invalid_rich_display(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test create_display_config prints warning for invalid rich_display."""
        config = create_display_config(
            use_rich_progress=True, rich_display="invalid"
        )
        assert config.rich_display_mode == "progress"

        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "invalid" in captured.out


class TestDisplayModePriority:
    """Test display mode priority when multiple flags are set (error case)."""

    def test_fzf_takes_precedence_in_error_message(self) -> None:
        """Test that FZF is mentioned in conflict error."""
        with pytest.raises(ValueError) as exc_info:
            validate_display_mode(use_fzf=True, use_simple=True)
        assert "fzf" in str(exc_info.value)

    def test_rich_takes_precedence_in_error_message(self) -> None:
        """Test that rich-progress is mentioned in conflict error."""
        with pytest.raises(ValueError) as exc_info:
            validate_display_mode(use_rich_progress=True, use_simple=True)
        assert "rich-progress" in str(exc_info.value)
