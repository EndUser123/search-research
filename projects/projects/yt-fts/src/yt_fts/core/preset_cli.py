"""Preset channels command for yt-fts.

This module provides the preset-channels command for generating
AI/automation focused channel lists.
"""

import click

from yt_fts.utils.rich_console import get_console


@click.command(
    name="preset-channels",
    help="Generate the preset channel list with AI/automation focused channels.",
)
@click.option(
    "--output",
    "-o",
    default="channels_preset.txt",
    help="Output file for preset channels (default: channels_preset.txt)",
)
@click.option("--clean", is_flag=True, help="Clean the preset list before saving")
def preset_channels(output: str, clean: bool) -> None:
    """Generate the preset AI/automation focused channel list."""

    from yt_fts.services.channel_cleaner import (
        ChannelCleaner,
        create_channel_list_from_input,
    )

    console = get_console()

    console.print("[bold blue]📋 Generating Preset Channel List[/bold blue]")

    try:
        channels = create_channel_list_from_input()

        if clean:
            console.print("[blue]🧹 Cleaning preset channels...[/blue]")
            cleaner = ChannelCleaner(console)
            channels, stats = cleaner.clean_channels(channels)
            cleaner.display_cleanup_results(channels, stats)

        # Write channels to file
        cleaner = ChannelCleaner(console)
        cleaner.generate_clean_file(channels, output, include_stats=False)

        console.print(
            f"[green]Preset channel list written to:[/green] [cyan]{output}[/cyan]"
        )
        console.print("\n Statistics:")
        console.print(f"   Total channels: {len(channels)}")
        console.print(
            f"   @Handles: {len([c for c in channels if c.startswith('@')])}"
        )
        console.print(
            f"   URLs: {len([c for c in channels if c.startswith('https://')])}"
        )

        console.print("\n💡 [bold]Usage:[/bold]")
        console.print(f"   yt_fts_cli.py batch-download {output} --jobs 1")

    except Exception as e:
        console.print(f"❌ [red]Error generating preset:[/red] {e!s}")


def _get_console():
    """Get the rich console instance.

    This is a convenience wrapper around the imported get_console function.
    """
    return get_console()
