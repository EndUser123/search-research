"""
Validation utilities for yt-fts CLI options.

This module provides reusable validation functions for CLI arguments
and display options.
"""
from __future__ import annotations


import click


def validate_display_options(
    simple: bool = False,
    fzf: bool = False,
    rich: bool = False,
    richo: bool = False,
    rich_1: bool = False,
    json: bool = False,
) -> None:
    """
    Validate display options for conflicting combinations.

    Ensures that only one display mode is active at a time, since
    different display formats are mutually exclusive.

    Args:
        simple: Simple line-by-line output
        fzf: fzf-style output
        rich: New Rich UI with fixed footer layout
        richo: Old Rich UI with progress bars
        rich_1: Alias for rich mode
        json: JSON output format

    Raises:
        click.BadOptionException: When conflicting display options are provided.
    """
    # Count how many display modes are active
    display_modes = []

    if simple:
        display_modes.append("--simple")
    if fzf:
        display_modes.append("--fzf")
    if rich or rich_1:
        display_modes.append("--rich/--rich-1")
    if richo:
        display_modes.append("--richo")

    # Check for multiple display modes (json is mutually exclusive with all)
    if json and display_modes:
        modes = " and ".join(display_modes)
        msg = (
            f"Cannot use --json with {modes}. JSON output is mutually exclusive "
            f"with other display formats."
        )
        raise click.BadOptionException(  # type: ignore[operator]
            msg
        )

    # Check for multiple non-JSON display modes
    if len(display_modes) > 1:
        modes = " and ".join(display_modes)
        msg = (
            f"Cannot use {modes} together. These display formats are mutually exclusive. "
            f"Choose one: --simple, --fzf, --rich/--rich-1, or --richo"
        )
        raise click.BadOptionException(  # type: ignore[operator]
            msg
        )


def validate_display_options_strict(
    simple: bool,
    fzf: bool,
    rich: bool,
    richo: bool,
    rich_1: bool,
    json: bool = False,
) -> None:
    """
    Strict version of validate_display_options without default parameters.

    This version is used when all parameters must be explicitly provided,
    such as in batch processing contexts.

    Unlike validate_display_options, this raises ValueError instead of
    click.BadOptionException, making it suitable for non-CLI contexts.

    Args:
        simple: Simple line-by-line output
        fzf: fzf-style output
        rich: New Rich UI with fixed footer layout
        richo: Old Rich UI with progress bars
        rich_1: Alias for rich mode
        json: JSON output format

    Raises:
        ValueError: When conflicting display options are provided.
    """
    # Count how many display modes are active
    display_modes = []

    if simple:
        display_modes.append("simple")
    if fzf:
        display_modes.append("fzf")
    if rich or rich_1:
        display_modes.append("rich")
    if richo:
        display_modes.append("richo")

    # Check for multiple display modes (json is mutually exclusive with all)
    if json and display_modes:
        modes = ", ".join(display_modes)
        msg = (
            f"Conflicting display options: json, {modes}. "
            f"Only one display mode can be enabled at a time."
        )
        raise ValueError(
            msg
        )

    # Check for multiple non-JSON display modes
    if len(display_modes) > 1:
        modes = ", ".join(display_modes)
        msg = (
            f"Conflicting display options: {modes}. "
            f"Only one display mode can be enabled at a time."
        )
        raise ValueError(
            msg
        )
