"""Plugins command for yt-fts.

This module provides the plugins command for managing display plugins.
"""
from __future__ import annotations

import builtins
from typing import Any

import click
from rich.console import Console

from yt_fts.utils.rich_console import get_console


@click.command(name="plugins")
@click.option("--list", "list_plugins", is_flag=True, help="List all available display plugins")
@click.option("--category", "-c", help="Filter by category (core, verbose, diagnostic, monitoring)")
def plugins_cmd(list_plugins: bool = False, category: str | None = None) -> None:
    """Manage display plugins.

    Without options, shows help. Use --list to see all plugins.
    """
    from yt_fts.ui.plugins import get_plugin_categories, list_plugins_by_category

    if not list_plugins and not category:
        # Show help by default
        click.echo("Use --list to see all available display plugins.")
        click.echo("Use --category to filter by category.")
        return

    if category:
        # Filter by category
        plugins_by_category = list_plugins_by_category()
        if category not in plugins_by_category:
            click.secho(f"Unknown category: {category}", fg="red")
            click.secho(f"Available categories: {', '.join(get_plugin_categories())}", fg="yellow")
            raise SystemExit(1)
        _display_plugins(category, plugins_by_category[category])
    else:
        # Show all categories
        plugins_by_category = list_plugins_by_category()
        for cat, plugins in plugins_by_category.items():
            _display_plugins(cat, plugins)


def _display_plugins(category: str, plugins: builtins.list[Any]) -> None:
    """Display plugins in a category."""
    display_category = category.upper()
    click.echo("")  # Blank line before category header
    click.secho(f"[{display_category}]", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")

    if not plugins:
        click.echo("  No plugins in this category.")
        return

    for plugin in plugins:
        name = plugin.get("name", "unknown")
        description = plugin.get("description", "No description")
        click.echo(f"  {name:20} - {description}")


def _get_console() -> Console:
    """Get the rich console instance.

    This is a convenience wrapper around the imported get_console function.
    """
    return get_console()
