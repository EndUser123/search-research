"""Diagnostics CLI command."""

import click
from rich.console import Console

from .checker import Status
from .cookies import CookieChecker
from .database import DatabaseChecker
from .network import NetworkChecker
from .ytdlp import YtdlpChecker

console = Console()


@click.command()
@click.option("--network", is_flag=True, help="Run network diagnostics only")
@click.option("--ytdlp", is_flag=True, help="Run yt-dlp diagnostics only")
@click.option("--cookies", is_flag=True, help="Run cookie diagnostics only")
@click.option("--database", is_flag=True, help="Run database diagnostics only")
@click.option("--fix", is_flag=True, help="Attempt automatic fixes where possible")
def diagnose(network: bool, ytdlp: bool, cookies: bool, database: bool, fix: bool) -> None:
    """Run diagnostics to troubleshoot common issues."""

from __future__ import annotations
    console.print("\n🔍 [bold]yt-fts Diagnostics[/bold]")
    console.print("━" * 60)

    all_checkers = [
        ("Network Connectivity", NetworkChecker),
        ("yt-dlp Health", YtdlpChecker),
        ("Cookie File", CookieChecker),
        ("Database Health", DatabaseChecker),
    ]

    # Determine which checkers to run
    selected = []
    if network:
        selected.append(("Network Connectivity", NetworkChecker))
    if ytdlp:
        selected.append(("yt-dlp Health", YtdlpChecker))
    if cookies:
        selected.append(("Cookie File", CookieChecker))
    if database:
        selected.append(("Database Health", DatabaseChecker))

    if not selected:
        selected = all_checkers

    # Run diagnostics
    all_results = []
    for name, checker_cls in selected:
        checker = checker_cls()
        results = checker.run()
        all_results.extend(results)

        # Display results for this category
        _display_category_results(name, results)

    # Summary
    _display_summary(all_results, fix)


def _display_category_results(category_name: str, results: list) -> None:
    """Display results for a single diagnostic category."""
    if not results:
        return

    # Determine overall status for the category
    has_fail = any(r.status == Status.FAIL for r in results)
    has_warn = any(r.status == Status.WARN for r in results)

    if has_fail:
        status_icon = "❌"
        status_color = "red"
    elif has_warn:
        status_icon = "⚠️ "
        status_color = "yellow"
    else:
        status_icon = "✅"
        status_color = "green"

    # Collect details from all results
    all_details = []
    remediation = None

    for result in results:
        if result.details:
            all_details.extend([f"   • {d}" for d in result.details])
        if result.remediation:
            remediation = result.remediation

    # Build output
    console.print(f"\n{status_icon} [{status_color}]{category_name}[/{status_color}]")
    if all_details:
        for detail in all_details[:5]:  # Limit details
            console.print(detail)
        if len(all_details) > 5:
            console.print(f"   ... and {len(all_details) - 5} more")

    if remediation:
        console.print(f"\n   [dim]💡 Fix:[/dim] {remediation}")


def _display_summary(results: list, fix: bool) -> None:
    """Display summary and recommendations."""
    console.print("\n" + "━" * 60)

    # Count statuses
    passes = sum(1 for r in results if r.status == Status.PASS)
    warns = sum(1 for r in results if r.status == Status.WARN)
    fails = sum(1 for r in results if r.status == Status.FAIL)
    infos = sum(1 for r in results if r.status == Status.INFO)

    # Overall status
    if fails > 0:
        console.print(f"\n❌ [red]{fails} issue(s) found[/red]")
        if not fix:
            console.print("💡 Run [cyan]yt-fts diagnose --fix[/cyan] to attempt automatic repairs")
    elif warns > 0:
        console.print(f"\n⚠️  [yellow]{warns} warning(s)[/yellow]")
    else:
        console.print(f"\n✅ [green]All checks passed![/green] ({passes + infos} passed)")

    if fix and (warns > 0 or fails > 0):
        console.print("\n🔧 Attempting automatic fixes...")
        # Auto-fix logic would go here
        # For now, just indicate what would be fixed
        console.print("   (Auto-fix not yet implemented - manual action required)")
