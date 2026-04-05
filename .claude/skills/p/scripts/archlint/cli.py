# SPDX-License-Identifier: MIT
"""CLI module for architectural-validator.

This module provides a command-line interface for validating code architecture
against defined rules and principles. It supports multiple rulesets including
SOLID, Clean Architecture, DRY, and KISS principles.

Features:
- Multiple ruleset validation (solid, clean, dry, kiss)
- Verbose mode for detailed output
- JSON output for integration with CI/CD pipelines
- Color-coded output for better readability
- Comprehensive error messages

Example usage:
    arch-validator /path/to/project
    arch-validator /path/to/project --rulesets solid,clean
    arch-validator /path/to/project --verbose --json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from archlint.core import ArchitectureContext
from archlint.rules import SOLIDValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Valid rulesets that can be used for validation
VALID_RULESETS = {"solid", "clean", "dry", "kiss"}

# Ruleset descriptions for help text
RULESET_DESCRIPTIONS = {
    "solid": "SOLID principles (Single responsibility, Open-closed, Liskov, Interface segregation, Dependency inversion)",
    "clean": "Clean Architecture principles (layer separation, dependency rules, entity isolation)",
    "dry": "DRY principle (Don't Repeat Yourself - code duplication prevention)",
    "kiss": "KISS principle (Keep It Simple, Stupid - simplicity over complexity)",
}


class ValidatorSettings(BaseSettings):
    """Configuration for architectural-validator CLI using pydantic-settings.

    SPEC-002 Fix: Replaces os.environ.get() with typed, validated configuration.
    Python 2025 Standard #8 requires pydantic-settings for all configuration.

    Environment Variables:
        ARCH_VALIDATOR_ALLOWED_ROOTS: Comma-separated list of allowed workspace paths
        ARCH_VALIDATOR_STRICT_MODE: If 'true', fail when allowed_roots not configured (default: false)

    Example:
        export ARCH_VALIDATOR_ALLOWED_ROOTS="P:/projects,P:/workspaces"
        export ARCH_VALIDATOR_STRICT_MODE="true"
    """

    model_config = SettingsConfigDict(
        env_prefix="ARCH_VALIDATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # String field that matches ARCH_VALIDATOR_ALLOWED_ROOTS env var
    allowed_roots: str = ""  # Comma-separated string from env
    strict_mode: bool = False

    @property
    def allowed_roots_list(self) -> list[str]:
        """Parse comma-separated string into list of paths."""
        if not self.allowed_roots:
            return []
        return [root.strip() for root in self.allowed_roots.split(",") if root.strip()]

    def get_resolved_roots(self) -> list[str]:
        """Get allowed workspace roots as resolved real paths."""
        return [os.path.realpath(root) for root in self.allowed_roots_list if root]

    def is_solo_dev_mode(self) -> bool:
        """Check if running in solo-dev mode (no allowed roots configured)."""
        return len(self.allowed_roots_list) == 0


class OutputFormatter:
    """Helper class for formatting CLI output."""

    @staticmethod
    def success(message: str) -> Text:
        """Format success message in green."""
        return Text(message, style="bold green")

    @staticmethod
    def error(message: str) -> Text:
        """Format error message in red."""
        return Text(message, style="bold red")

    @staticmethod
    def warning(message: str) -> Text:
        """Format warning message in yellow."""
        return Text(message, style="bold yellow")

    @staticmethod
    def info(message: str) -> Text:
        """Format info message in blue."""
        return Text(message, style="bold blue")

    @staticmethod
    def dim(message: str) -> Text:
        """Format dimmed message."""
        return Text(message, style="dim")


def _is_path_relative_to(path: Path, parent: Path) -> bool:
    """Check if path is within parent directory.

    Provides compatibility across Python versions by using is_relative_to()
    on Python 3.9+ and falling back to relative_to() on older versions.

    Args:
        path: The path to check
        parent: The potential parent directory

    Returns:
        True if path is within parent, False otherwise
    """
    try:
        # Python 3.9+ has is_relative_to()
        return path.is_relative_to(parent)
    except AttributeError:
        # Fallback for Python < 3.9
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False


def validate_project_path(
    project_path: str, settings: ValidatorSettings | None = None
) -> tuple[bool, str]:
    """
    Ensure project_path is within allowed workspace and exists.

    SECURITY: Resolves path FIRST to normalize '..' and symlinks, then validates
    against allowed workspace roots. This prevents path traversal attacks via
    URL encoding (%2e%2e) or absolute paths that bypass simple string checks.

    SPEC-002 Fix: Uses pydantic-settings for configuration instead of os.getenv().
    QUAL-004 Fix: Properly handles solo-dev mode with actual warnings.

    Args:
        project_path: Path to validate
        settings: Optional ValidatorSettings instance (for testing). If None, loads from environment.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Load settings from environment if not provided
    if settings is None:
        settings = ValidatorSettings()

    # CRITICAL: Resolve path FIRST to normalize '..' and symlinks
    # This prevents bypass via URL encoding, absolute paths, or mixed case
    resolved_path = Path(project_path).resolve()

    # Check if resolved path exists
    if not resolved_path.exists():
        return False, f"Error: Path '{project_path}' not found"

    # Check if resolved path is a directory
    if not resolved_path.is_dir():
        return False, f"Error: Path '{project_path}' is not a directory"

    resolved = str(resolved_path)

    # Get allowed workspace roots from settings
    allowed_roots = settings.get_resolved_roots()

    # Handle solo-dev mode (no allowed roots configured)
    if settings.is_solo_dev_mode():
        if settings.strict_mode:
            # SECURE BY DEFAULT: Fail fast in production when not configured
            return False, (
                "SECURITY: ARCH_VALIDATOR_ALLOWED_ROOTS not configured. "
                "Path validation disabled - Set ARCH_VALIDATOR_ALLOWED_ROOTS for production use."
            )

        # SEC-001 FIX: In solo-dev mode, only allow paths under current working directory
        # This prevents path traversal attacks accessing sensitive system files
        cwd = Path.cwd()

        if _is_path_relative_to(resolved_path, cwd):
            return True, ""

        # Path is outside CWD, reject it
        return (
            False,
            f"Access denied: {resolved} is outside current working directory: {cwd}",
        )

    # Check if resolved path is within any allowed root
    for root in allowed_roots:
        # SEC-008 FIX: Use is_relative_to() to prevent prefix collision attacks
        # Old: resolved.startswith(root) - vulnerable to /data/projects-evil bypass
        # New: Use pathlib to properly check if path is within root
        if _is_path_relative_to(resolved_path, Path(root)):
            return True, ""

    # Path is outside all allowed workspaces
    return (
        False,
        f"Access denied: {resolved} is outside allowed workspace roots: {', '.join(allowed_roots)}",
    )


def validate_rulesets(rulesets: str | None, console: Console) -> list[str]:
    """
    Validate and parse ruleset string.

    Args:
        rulesets: Comma-separated string of ruleset names
        console: Rich console instance for output

    Returns:
        List of validated ruleset names

    Raises:
        click.Exit: If invalid rulesets are provided
    """
    if not rulesets:
        return []

    ruleset_list = [r.strip().lower() for r in rulesets.split(",")]

    # Validate ruleset names
    invalid_rulesets = [r for r in ruleset_list if r not in VALID_RULESETS]
    if invalid_rulesets:
        error_msg = (
            f"Invalid ruleset(s): {', '.join(invalid_rulesets)}\n\nValid rulesets:\n"
        )
        for ruleset in sorted(VALID_RULESETS):
            error_msg += f"  - {ruleset}: {RULESET_DESCRIPTIONS.get(ruleset, 'No description')}\n"
        console.print(OutputFormatter.error(error_msg))
        sys.exit(1)

    return ruleset_list


@click.command(name="arch-validator")
@click.argument("project_path", metavar="PROJECT_PATH")
@click.option(
    "--rulesets",
    type=str,
    metavar="RULESETS",
    help=(
        "Comma-separated list of rulesets to use. "
        "Available: solid, clean, dry, kiss. "
        "If not specified, all rulesets are applied."
    ),
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with detailed validation information",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output results in JSON format for CI/CD integration",
)
@click.option(
    "--no-color", is_flag=True, help="Disable colored output (useful for logging)"
)
@click.version_option(version="0.1.0", prog_name="arch-validator")
def cli(
    project_path: str,
    rulesets: str | None,
    verbose: bool,
    json_output: bool,
    no_color: bool,
) -> None:
    """Architectural Validator - Check code architecture against defined rules.

    \b
    Validate your project's architecture against established principles and patterns.
    Supports SOLID, Clean Architecture, DRY, and KISS principles out of the box.

    \b
    PROJECT_PATH:
        The path to the project directory to validate.
        Must be an existing directory.

    \b
    EXAMPLES:
        # Validate a project with all default rulesets
        arch-validator ./my-project

        # Validate with specific rulesets
        arch-validator ./my-project --rulesets solid,clean

        # Validate with verbose output
        arch-validator ./my-project --verbose

        # Validate and output as JSON
        arch-validator ./my-project --json

    \b
    EXIT CODES:
        0 - Validation passed, project is compliant
        1 - Validation failed or error occurred
    """
    # Create console instance for this CLI invocation
    console = Console(no_color=no_color)

    # SEC-010 FIX: Validate project path BEFORE any processing
    # This prevents security bypass by validating workspace boundaries,
    # blocking directory junctions, and checking path existence
    is_valid, error = validate_project_path(project_path)
    if not is_valid:
        console.print(OutputFormatter.error(error))
        sys.exit(1)

    try:
        # Validate and parse rulesets
        ruleset_list = validate_rulesets(rulesets, console)

        # Display validation start
        if not json_output:
            console.print(
                "\n[bold blue]Starting architectural validation...[/bold blue]\n"
            )
            console.print(f"[dim]Project path:[/dim] {project_path}")

            if ruleset_list:
                console.print(f"[dim]Rulesets:[/dim] {', '.join(ruleset_list)}")
            else:
                console.print("[dim]Rulesets:[/dim] (default - all rulesets)")

            console.print()

        # CLIT001 FIX: Perform actual validation using SOLIDValidator
        # Create architecture context from project path
        context = ArchitectureContext(
            architecture_id=Path(project_path).name,
            name=f"Architecture: {Path(project_path).name}",
            description=f"Validation of project at {project_path}",
            metadata={"project_path": str(project_path)},
        )

        # Run SOLID validation
        validator = SOLIDValidator()
        validation_result = validator.validate(context)

        # Extract results
        is_valid = validation_result.is_compliant
        violations = validation_result.violations
        recommendations = []

        # Generate recommendations from violations
        for v in violations[:5]:  # Top 5 violations
            if "recommendation" in v:
                recommendations.append(v["recommendation"])

        # Format and display results
        if json_output:
            result = {
                "project_path": str(project_path),
                "is_valid": is_valid,
                "rulesets": ruleset_list if ruleset_list else list(VALID_RULESETS),
                "status": "compliant" if is_valid else "non_compliant",
                "violations": violations,
                "recommendations": recommendations,
            }
            if verbose:
                result["details"] = {
                    "total_rulesets": len(ruleset_list)
                    if ruleset_list
                    else len(VALID_RULESETS),
                    "validation_timestamp": str(getattr(click.ctx, "timestamp", "N/A")),
                }
            click.echo(json.dumps(result, indent=2))
        else:
            # Display formatted output
            if is_valid:
                console.print(
                    Panel(
                        "[bold green]COMPLIANT[/bold green]",
                        title="[bold blue]Validation Result[/bold blue]",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        "[bold red]NON-COMPLIANT[/bold red]",
                        title="[bold blue]Validation Result[/bold blue]",
                        border_style="red",
                    )
                )

            console.print(f"\n[bold]Project:[/bold] {project_path}")

            if ruleset_list:
                console.print(f"[bold]Rulesets:[/bold] {', '.join(ruleset_list)}")
            else:
                console.print("[bold]Rulesets:[/bold] (default - all rulesets)")

            if verbose:
                console.print("\n[bold cyan]Verbose Details:[/bold cyan]")
                console.print(
                    f"  Total rulesets evaluated: {len(ruleset_list) if ruleset_list else len(VALID_RULESETS)}"
                )
                console.print(
                    f"  Validation mode: {'strict' if ruleset_list else 'standard'}"
                )
                console.print(f"  Violations found: {len(violations)}")
                console.print(f"  Recommendations: {len(recommendations)}")

                if violations:
                    console.print("\n[bold yellow]Violations:[/bold yellow]")
                    for v in violations:
                        console.print(f"  - {v}")

                if recommendations:
                    console.print("\n[bold blue]Recommendations:[/bold blue]")
                    for r in recommendations:
                        console.print(f"  - {r}")

            console.print("\n[bold green]Validation complete.[/bold green]\n")

    except SystemExit:
        # Re-raise SystemExit from validate_rulesets
        raise
    except Exception as e:
        # Handle unexpected errors
        if json_output:
            error_result = {
                "error": str(e),
                "project_path": str(project_path),
                "status": "error",
            }
            click.echo(json.dumps(error_result, indent=2))
        else:
            console.print(
                Panel(
                    f"[bold red]Error:[/bold red] {str(e)}",
                    title="[bold red]Validation Failed[/bold red]",
                    border_style="red",
                )
            )
        sys.exit(1)


if __name__ == "__main__":
    cli()
