"""
Search CLI commands for yt-fts.

This module contains search-related click commands extracted from cli.py:
- search: Unified search across YouTube content (FTS + vector)
- vsearch: Vector search using embeddings
- watch-search: Search in watch history

Helper functions:
- _display_unified_results: Display search results with formatted output
- _format_results_as_json: Format results as JSON
- _remove_duplicate_results: Remove duplicates from combined search results
- _handle_command_result: Handle command execution results
- validate_display_options: Validate display option combinations
"""
from __future__ import annotations

import builtins
import json
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from yt_fts.utils import get_model_config
from yt_fts.utils.config import get_db_path
from yt_fts.utils.rich_console import get_console


def _get_console() -> Console:
    """Get a Rich Console instance for output.

    Returns:
        Configured Rich Console instance.
    """
    return get_console()


from yt_fts.core.metrics import SearchMetrics
from .validation import validate_display_options

console = _get_console()


def _handle_command_result(result: int | None = None) -> None:
    """
    Handle command execution results consistently without sys.exit().

    Args:
        result: Exit code from command execution (0=success, 1=error, 130=interrupt)
                If None, no action is taken (command handles its own flow control)
    """
    if result is not None:
        # Let Click handle the exit code naturally
        # This allows proper cleanup and maintains CLI behavior
        if result != 0:
            # For non-zero exit codes, we'll raise a SystemExit with the code
            # but this is more controlled than direct sys.exit() calls
            raise SystemExit(result)
        # For success (0), we simply return and let Click complete normally


def _remove_duplicate_results(results: builtins.list[Any]) -> builtins.list[Any]:
    """
    Remove duplicate results from combined FTS and vector search results.
    Prioritizes vector search results over FTS for the same content.
    """
    seen = set()
    unique_results = []

    for result in results:
        # Handle both dict and object formats
        if isinstance(result, dict):
            video_id = result.get("video_id", "")
            start_time = result.get("start_time", result.get("timestamp", ""))
        else:
            video_id = getattr(result, "video_id", "")
            start_time = getattr(result, "start_time", getattr(result, "timestamp", ""))

        # Create a unique identifier based on video_id and timestamp
        identifier = f"{video_id}_{start_time}"

        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(result)

    return unique_results


def _display_unified_results(
    results: builtins.list[Any], query: str, has_fts: bool, has_vector: bool
) -> None:
    """
    Display unified search results with clear labeling of search type.
    """
    if not results:
        console.print(f"[yellow]No matches found for query: '{query}'[/yellow]")
        return

    # Group by channel
    channels: dict[str, list[Any]] = {}
    for result in results:
        # Handle both dict and object formats
        if isinstance(result, dict):
            channel_name = result.get("channel_name", result.get("channel", "Unknown"))
        else:
            channel_name = getattr(
                result, "channel_name", getattr(result, "channel", "Unknown")
            )

        if channel_name not in channels:
            channels[channel_name] = []
        channels[channel_name].append(result)

    console.print(f"\n[bold]Unified Search Results:[/bold] '{query}'")
    if has_fts and has_vector:
        console.print(" Combined full-text + semantic search")
    elif has_fts:
        console.print(" Full-text search results")
    else:
        console.print(" Semantic search results")

    console.print(f"Found {len(results)} matches in {len(channels)} channel(s)\n")

    for channel_name, channel_results in channels.items():
        console.print(f"{channel_name} ({len(channel_results)} matches)")

        for i, result in enumerate(channel_results, 1):
            # Handle both dict and object formats
            if isinstance(result, dict):
                result_type = result.get("result_type", "fts")
                video_title = result.get("video_title", result.get("title", "Unknown"))
                relevance_score = result.get(
                    "relevance_score", result.get("similarity", 0)
                )
                timestamp = result.get(
                    "timestamp", result.get("start_time", "00:00:00")
                )
                text = result.get("text", "")
                link = result.get("link", "")
            else:
                result_type = getattr(result, "result_type", "fts")
                video_title = getattr(result, "video_title", "Unknown")
                relevance_score = getattr(
                    result, "relevance_score", getattr(result, "similarity", 0)
                )
                timestamp = getattr(
                    result, "timestamp", getattr(result, "start_time", "00:00:00")
                )
                text = getattr(result, "text", "")
                link = getattr(result, "link", "")

            # Determine search type and format accordingly
            if result_type == "vector":
                search_indicator = ""
                score_text = (
                    f" [dim](similarity: {relevance_score:.3f})[/dim]"
                    if (relevance_score or 0) > 0
                    else ""
                )
            else:
                search_indicator = ""
                score_text = ""

            console.print(
                f"   {search_indicator} [blue]{i}.[/blue] {video_title}{score_text}"
            )
            console.print(
                f"      [grey62][link={link}]{timestamp}[/link][/grey62] {text[:150]}{'...' if len(text) > 150 else ''}"
            )

        console.print()


def _format_results_as_json(results: builtins.list[Any], reverse: bool = False) -> str:
    """Format search results as JSON array for output.

    Args:
        results: List of search result dictionaries
        reverse: If True, reverse the result order

    Returns:
        JSON string representation of results
    """
    # Reverse results if requested (default is newest first, reverse makes oldest first)
    if reverse:
        results = results[::-1]

    formatted = []
    for r in results:
        # Handle both dict and object formats
        if isinstance(r, dict):
            video_id = r.get("video_id", "")
            video_title = r.get("title", r.get("video_title", ""))
            channel_name = r.get("channel_name", "")
            timestamp = r.get("start_time", r.get("timestamp", ""))
            text = r.get("text", "")
            url = r.get("link", r.get("url", ""))
        else:
            video_id = getattr(r, "video_id", "")
            video_title = getattr(r, "video_title", getattr(r, "title", ""))
            channel_name = getattr(r, "channel_name", "")
            timestamp = getattr(r, "start_time", getattr(r, "timestamp", ""))
            text = getattr(r, "text", "")
            url = getattr(r, "link", getattr(r, "url", ""))

        formatted.append({
            "video_id": video_id,
            "video_title": video_title,
            "channel_name": channel_name,
            "timestamp": timestamp,
            "text": text,
            "url": url
        })

    return json.dumps(formatted, ensure_ascii=False, indent=2)


def _time_to_seconds(time_str: str) -> int:
    """Convert time string to seconds"""
    try:
        from yt_fts.utils import time_to_secs

        return time_to_secs(time_str)
    except (ValueError, TypeError, AttributeError):
        return 0


def export_multi_channel_results(results: Any, query: str, export_type: str) -> None:
    """Export multi-channel search results to CSV."""
    import csv

    if not results:
        console.print("[yellow]No results to export[/yellow]")
        return

    # Generate filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c.isspace()).rstrip()[:20]
    filename = f"{export_type}_{safe_query.replace(' ', '_')}_{timestamp}.csv"

    # Write CSV
    with Path(filename).open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "rank",
            "query",
            "text",
            "video_id",
            "video_title",
            "channel_id",
            "channel_name",
            "start_time",
            "timestamp",
            "link",
            "relevance_score",
            "result_type",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, result in enumerate(results, 1):
            writer.writerow(
                {
                    "rank": i,
                    "query": query,
                    "text": result.text,
                    "video_id": result.video_id,
                    "video_title": result.video_title,
                    "channel_id": result.channel_id,
                    "channel_name": result.channel_name,
                    "start_time": result.start_time,
                    "timestamp": result.timestamp,
                    "link": result.link,
                    "relevance_score": f"{result.relevance_score:.3f}",
                    "result_type": result.result_type,
                }
            )

    console.print(f"[green]Results exported to:[/green] {filename}")


@click.command(
    name="search",
    help="""
    Unified search command combining full-text and vector search.

    Performs full-text search (FTS) and semantic vector search across
    YouTube video subtitles. Results are combined, deduplicated, and
    displayed with clear labeling of the search type.

    Supports searching across:
    - All channels
    - Specific channel (by --channel or -c)
    - Specific video (by --video-id or -v)
    - Multiple channels (by --channels)

    Advanced features:
    - Multi-channel search with comma-separated channel lists
    - Export results to CSV for further analysis
    - Configurable result limits and relevance scoring
    - Duplicate removal across search types
    - Rich formatting with video links and timestamps

    Examples:
    yt-fts search "machine learning"                    # Combined search across all channels
    yt-fts search "AI agents" --channels "Channel1,Channel2"
    yt-fts search "neural networks" --fts-only         # Text search only
    yt-fts search "deep learning" --vector-only        # Semantic search only
    yt-fts search "transformers" --export              # Export results to CSV
    """,
)
@click.argument("text", required=True)
@click.option(
    "-c", "--channel", default=None, help="The name or id of the channel to search in."
)
@click.option(
    "-v", "--video-id", default=None, help="The id of the video to search in."
)
@click.option(
    "--channels",
    "channels",
    multiple=True,
    help="Multiple channels to search in (can be used multiple times or with comma-separated values).",
)
@click.option(
    "-l",
    "--limit",
    default=10,
    type=int,
    help="Number of results to return per search type",
)
@click.option(
    "-e", "--export", is_flag=True, help="Export search results to a CSV file."
)
@click.option(
    "--fts-only", is_flag=True, help="Use full-text search only (faster, exact matches)"
)
@click.option(
    "--vector-only",
    is_flag=True,
    help="Use vector search only (semantic meaning, requires embeddings)",
)
@click.option(
    "--api-key",
    default=None,
    help="API key for vector search (uses GEMINI_API_KEY if not provided)",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format: table (default) or json",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse result order (oldest first instead of newest first)",
)
@click.option(
    "--metrics",
    is_flag=True,
    help="Track and display search metrics/telemetry",
)
@click.option(
    "--proactive",
    is_flag=True,
    help="Enable proactive search injection based on query intent (auto-triggers search for information-seeking queries)",
)
def search(
    text: str,
    channel: str | None,
    video_id: str | None,
    channels: tuple[str, ...],
    export: bool,
    limit: int,
    fts_only: bool,
    vector_only: bool,
    api_key: str | None,
    output_format: str,
    reverse: bool,
    metrics: bool,
    proactive: bool,
) -> None:
    # Validate search mode options
    if fts_only and vector_only:
        console.print(
            "[bold red]Error:[/bold red] Cannot use both --fts-only and --vector-only at the same time"
        )
        msg = "Invalid search mode combination"
        raise click.ClickException(msg)

    # Determine search modes
    use_fts = not vector_only  # Use FTS unless vector-only is specified
    use_vector = not fts_only  # Use vector unless fts-only is specified

    # Handle proactive search injection
    if proactive:
        from yt_fts.lib.search import ProactiveSearchInjection

        injector = ProactiveSearchInjection()

        # Determine scope for proactive search
        if channel:
            proactive_scope = "channel"
            proactive_channel = channel
        elif video_id:
            proactive_scope = "video"
            proactive_channel = None
        elif channels:
            # Multi-channel doesn't support proactive yet
            console.print(
                "[yellow]Warning:[/yellow] Proactive search not supported with --channels flag"
            )
            proactive = False
        else:
            proactive_scope = "all"
            proactive_channel = None

        if proactive:
            # Get injection context
            context = injector.get_injection_context(
                query=text,
                scope=proactive_scope,
                channel=proactive_channel,
                video_id=video_id if proactive_scope == "video" else None,
                limit=limit,
            )

            # Display proactive search information
            if context["should_inject"]:
                console.print(
                    f"\n[bold cyan]Proactive Search:[/bold cyan] Detected '{context['intent']}' intent"
                )
                if context["results"] and len(context["results"]) > 0:
                    console.print(
                        f"[green]Found {len(context['results'])} result(s)[/green] that can be used to enhance LLM context"
                    )
                    if output_format == "json":
                        console.print(
                            "\n[bold]Formatted Search Results for LLM:[/bold]"
                        )
                        console.print(context["formatted_for_llm"])
                    else:
                        # In table mode, just show a summary
                        console.print(
                            "[dim](Use --format json to see full results formatted for LLM)[/dim]"
                        )
                else:
                    console.print(
                        "[yellow]No search results found for this query[/yellow]"
                    )
                console.print()
            else:
                console.print(
                    f"[dim]Proactive Search:[/dim] Query intent is '{context['intent']}', skipping search injection\n"
                )

    # Initialize metrics tracking if enabled
    metrics_tracker = None
    import time
    search_start_time = time.time()

    # Handle multi-channel search
    if channels:
        from .multi_channel_search import (
            MultiChannelSearchController,
            parse_channel_inputs,
        )

        # Parse channels from tuple (handle comma-separated values)
        all_channels = []
        for ch in channels:
            if "," in ch:
                all_channels.extend([c.strip() for c in ch.split(",")])
            else:
                all_channels.append(ch.strip())

        controller = MultiChannelSearchController()
        channel_inputs = parse_channel_inputs(all_channels)

        # Resolve channels
        channel_specs, error_messages = controller.resolve_channels(channel_inputs)

        # Validate channels
        valid_channel_ids, validation_errors = controller.validate_channels(
            channel_specs
        )

        # Display validation errors if any
        if error_messages or validation_errors:
            controller.display_channel_validation_errors(channel_specs)

        if not valid_channel_ids:
            console.print("[bold red]Error:[/bold red] No valid channels specified")
            controller.suggest_available_channels()
            msg = "No valid channels specified"
            raise click.ClickException(msg)

        # Perform unified multi-channel search
        all_results = []

        # FTS Search
        if use_fts:
            if output_format != "json":
                console.print("Performing full-text search...")
            fts_results = controller.search_multiple_channels_fts(
                text, valid_channel_ids, limit
            )
            all_results.extend(fts_results)

        # Vector Search
        if use_vector:
            # Get API key for vector search
            vector_api_key = api_key
            if not vector_api_key:
                try:
                    model_config = get_model_config()
                    vector_api_key = model_config["api_key"]
                except ValueError:
                    console.print(
                        "[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not set for vector search"
                    )
                    console.print(
                        "[yellow]Tip:[/yellow] Use --fts-only for text search only, or set your Gemini API key"
                    )
                    msg = "API key required for vector search"
                    raise click.ClickException(msg)

            if output_format != "json":
                console.print("Performing semantic search...")
            vector_results = controller.search_multiple_channels_vector(
                text, valid_channel_ids, limit, vector_api_key
            )
            all_results.extend(vector_results)

        # Remove duplicates and sort by relevance
        unique_results = _remove_duplicate_results(all_results)

        # Handle JSON output format
        if output_format == "json" and unique_results:
            json_output = _format_results_as_json(unique_results, reverse=reverse)
            click.echo(json_output)
        else:
            _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")

        return  # Success - let Click handle naturally

    # Single channel/video/all search logic (unified)
    if channel:
        scope = "channel"
        from .database import get_channel_id_from_input
        # Suppress output during channel ID resolution for JSON format
        if output_format == "json":
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                channel_id = get_channel_id_from_input(channel)
        else:
            channel_id = get_channel_id_from_input(channel)
    elif video_id:
        scope = "video"
        channel_id = None
    else:
        scope = "all"
        channel_id = None

    # Collect all results
    all_results = []

    # FTS Search for single channel/video/all
    if use_fts:
        if scope == "all":
            if output_format != "json":
                console.print(
                    "Performing full-text search across all channels..."
                )
            from .database import search_all

            fts_results = search_all(text, limit)
        # For JSON output, use database functions directly to avoid console printing
        elif output_format == "json":
            from yt_fts.db.infra import get_db_connection

            if scope == "channel":
                # Direct query to get all results in one go, avoiding helper functions
                conn = get_db_connection()
                curr = conn.cursor()
                # Query that joins subtitles, videos, and channels to get all needed fields
                curr.execute("""
                        SELECT s.video_id, s.start_time, s.text,
                               v.video_title, c.channel_name
                        FROM Subtitles s
                        JOIN Videos v ON s.video_id = v.video_id
                        JOIN Channels c ON v.channel_id = c.channel_id
                        JOIN Subtitles_fts fts ON s.rowid = fts.rowid
                        WHERE v.channel_id = ? AND fts.text MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (channel_id, text, limit or 10))
                fts_results = []
                for row in curr.fetchall():
                    fts_results.append({
                        "video_id": row[0],
                        "start_time": row[1],
                        "text": row[2],
                        "title": row[3],
                        "channel_name": row[4],
                        "link": f"https://youtu.be/{row[0]}"
                    })
                conn.close()
            else:  # scope == "video"
                # For video scope, use the existing search_video function
                from .database import search_video
                fts_results = search_video(video_id, text, limit)
            fts_results = fts_results if fts_results else []
        else:
            console.print(f"Performing full-text search in {scope}...")
            from .search import SearchHandler

            search_handler = SearchHandler(
                scope=scope,
                video_id=video_id,
                channel=channel,
                export=False,  # We'll handle export separately
                limit=limit,
            )
            search_handler.full_text_search(text)
            fts_results = search_handler.res
            fts_results = fts_results if fts_results else []

        # Convert to MultiChannelResult format for unified display
        for result in fts_results:
            multi_result = type(
                "MultiChannelResult",
                (),
                {
                    "video_id": result.get("video_id", ""),
                    "video_title": result.get("title", ""),
                    "channel_id": result.get("channel_id", ""),
                    "channel_name": result.get("channel_name", ""),
                    "start_time": result.get("start_time", ""),
                    "text": result.get("text", ""),
                    "link": result.get("link", ""),
                    "result_type": "fts",
                    "timestamp": result.get("start_time", ""),
                    "relevance_score": 1.0,
                },
            )()
            all_results.append(multi_result)

    # Vector Search for single channel with enhanced recovery
    if use_vector and channel_id:
        # For JSON output, skip vector search entirely
        if output_format != "json":
            # Get API key for vector search
            vector_api_key = api_key
            if not vector_api_key:
                try:
                    model_config = get_model_config()
                    vector_api_key = model_config["api_key"]
                except ValueError:
                    console.print(
                        "[red]Error:[/red] GEMINI_API_KEY environment variable not set for vector search"
                    )
                    console.print(
                        "[yellow]Tip:[/yellow] Use --fts-only for text search only, or set your Gemini API key"
                    )
                    msg = "API key required for vector search"
                    raise click.ClickException(msg)

            console.print("Performing semantic search in channel...")
            from yt_fts.llm.embedding_recovery_manager import (
                EmbeddingRecoveryManager,
            )

            # Use enhanced recovery manager
            EmbeddingRecoveryManager()

            # First try with existing auto-embeddings system
            from yt_fts.llm.auto_embeddings import (
                auto_ensure_embeddings_for_vsearch,
            )

            if not auto_ensure_embeddings_for_vsearch(channel_id, vector_api_key):
                console.print(
                    "[red]Error:[/red] Cannot proceed with vector search. Embeddings generation failed."
                )
                msg = "Embeddings generation failed"
                raise click.ClickException(msg)

            # Now perform the vector search
            from yt_fts.llm.simple_embeddings import SimpleEmbeddingsHandler

            embeddings_handler = SimpleEmbeddingsHandler()
            from yt_fts.llm.faiss_store import FaissVectorStore

            # Get query embedding
            query_embedding = embeddings_handler.get_embedding(text)

            # Search using FAISS store
            vector_store = FaissVectorStore()
            vector_results = vector_store.search(
                query_embedding=query_embedding,
                channel_id=channel_id,
                k=limit
            )

            # Convert to MultiChannelResult format
            for result in vector_results:
                # FAISS returns flat result structure with metadata directly in result
                multi_result = type(
                    "MultiChannelResult",
                    (),
                    {
                        "video_id": result["video_id"],
                        "video_title": result["video_title"],
                        "channel_id": channel_id,
                        "channel_name": result.get("channel_name", ""),
                        "start_time": result["start_time"],
                        "text": result.get("text", ""),
                        "link": f"https://youtu.be/{result['video_id']}?t={_time_to_seconds(result['start_time'])}",
                        "relevance_score": result["similarity"],
                        "result_type": "vector",
                        "timestamp": result.get("start_time", ""),
                    },
                )()
                all_results.append(multi_result)

            # If no vector results, provide helpful message
            if not vector_results:
                console.print(
                    "[yellow]Tip:[/yellow] Try using --fts-only for text search or ensure the channel has downloadable subtitles"
                )

    # Display unified results
    if all_results:
        unique_results = _remove_duplicate_results(all_results)

        # Handle JSON output format
        if output_format == "json":
            json_output = _format_results_as_json(unique_results, reverse=reverse)
            # Print only the JSON, ignore any other output
            click.echo(json_output)
        else:
            _display_unified_results(unique_results, text, use_fts, use_vector)

        # Export if requested
        if export and unique_results:
            export_multi_channel_results(unique_results, text, "unified_search")
    # Handle empty results for JSON
    elif output_format == "json":
        click.echo("[]")
    else:
        console.print(f"[yellow]No matches found for query: '{text}'[/yellow]")

    # Track and display metrics if enabled
    if metrics:
        if metrics_tracker is None:
            metrics_tracker = SearchMetrics()

        duration_ms = int((time.time() - search_start_time) * 1000)

        # Determine scope
        scope = "all"
        if channel:
            scope = "channel"
        elif video_id:
            scope = "video"
        elif channels:
            scope = "channel"

        # Track the search (using FTS backend if FTS was used)
        backend = "fts" if use_fts else "vector"
        if use_fts and use_vector:
            # If both were used, track as fts (primary)
            backend = "fts"

        metrics_tracker.track_search(
            query=text,
            scope=scope,
            result_count=len(unique_results) if all_results else 0,
            backend=backend,
            duration_ms=duration_ms,
            channel_id=channel if channel else None,
            video_id=video_id if video_id else None,
        )

        # Save metrics
        metrics_tracker.save()

        # Display metrics
        console.print("")
        console.print("[bold cyan]Search Metrics:[/bold cyan]")
        console.print(metrics_tracker.display())

    # Success - let Click handle naturally


@click.command(
    name="vsearch",
    help="""
            Vector search. Requires embeddings to be generated for the channel
            and environment variable GEMINI_API_KEY to be set (recommended).
            Gemini embeddings are free to use.

            Multi-channel examples:
            yt-fts vsearch "query" --channels "Channel1,Channel2,Channel3"
            yt-fts vsearch "query" -c "Channel1" -c "Channel2"
        """,
)
@click.argument("text", required=True)
@click.option(
    "-c", "--channel", default=None, help="The name or id of the channel to search in"
)
@click.option(
    "-v", "--video-id", default=None, help="The id of the video to search in."
)
@click.option(
    "--channels",
    "channels",
    multiple=True,
    help="Multiple channels to search in (can be used multiple times or with comma-separated values).",
)
@click.option("-l", "--limit", default=10, help="Number of results to return")
@click.option(
    "-e", "--export", is_flag=True, help="Export search results to a CSV file."
)
@click.option(
    "--api-key",
    default=None,
    help="OpenAI or Gemini API key. If not provided, the script will attempt to read it from the OPENAI_API_KEY or GEMINI_API_KEY"
    "environment variables.",
)
def vsearch(
    text: str,
    channel: str | None,
    video_id: str | None,
    channels: tuple[str, ...],
    limit: int,
    export: bool,
    api_key: str | None,
) -> None:

    try:
        model = get_model_config(api_key)
        api_key = model["api_key"]
    except ValueError:
        console.print(
            "[red]Error:[/red] GEMINI_API_KEY environment variable not set\n"
            'To set the key run: export "GEMINI_API_KEY=<your_key>" or pass '
            "one in with --api-key\n"
            "Get your free Gemini API key from: https://makersuite.google.com/app/apikey"
        )
        msg = "API key required for vector search"
        raise click.ClickException(msg)

    # Handle multi-channel vector search
    if channels:
        from .multi_channel_search import (
            MultiChannelSearchController,
            parse_channel_inputs,
        )

        # Parse channels from tuple (handle comma-separated values)
        all_channels = []
        for ch in channels:
            if "," in ch:
                all_channels.extend([c.strip() for c in ch.split(",")])
            else:
                all_channels.append(ch.strip())

        controller = MultiChannelSearchController()
        channel_inputs = parse_channel_inputs(all_channels)

        # Resolve channels
        channel_specs, error_messages = controller.resolve_channels(channel_inputs)

        # Validate channels
        valid_channel_ids, validation_errors = controller.validate_channels(
            channel_specs
        )

        # Display validation errors if any
        if error_messages or validation_errors:
            controller.display_channel_validation_errors(channel_specs)

        if not valid_channel_ids:
            console.print("[bold red]Error:[/bold red] No valid channels specified")
            controller.suggest_available_channels()
            msg = "No valid channels specified"
            raise click.ClickException(msg)

        # Ensure embeddings exist for all channels
        from yt_fts.llm.auto_embeddings import auto_ensure_embeddings_for_vsearch

        for channel_id in valid_channel_ids:
            if not auto_ensure_embeddings_for_vsearch(channel_id, api_key):
                console.print(
                    f"[red]Error:[/red] Cannot generate embeddings for channel {channel_id}"
                )
                msg = f"Embeddings generation failed for channel {channel_id}"
                raise click.ClickException(
                    msg
                )

        # Perform multi-channel vector search
        results = controller.search_multiple_channels_vector(
            text, valid_channel_ids, limit, api_key, model
        )

        # Display results
        if not results:
            console.print(f"[yellow]No results found for query: '{text}'[/yellow]")
            return  # Success - let Click handle naturally

        controller.format_multi_channel_results(results, text, group_by_channel=False)

        # Export if requested
        if export and results:
            export_multi_channel_results(results, text, "multi_channel_vector_search")

        return  # Success - let Click handle naturally

    # Original single-channel vector search logic
    if not channel:
        console.print(
            "[red]Error:[/red] Vector search requires --channel option or --channels for multi-channel search"
        )
        msg = "Channel option required for vector search"
        raise click.ClickException(msg)

    # Convert channel name to channel ID if needed
    from .db_utils import get_channel_id_from_input

    channel_id = get_channel_id_from_input(channel)

    # Auto-ensure embeddings exist (NEW!)
    from yt_fts.llm.auto_embeddings import auto_ensure_embeddings_for_vsearch

    if not auto_ensure_embeddings_for_vsearch(channel_id, api_key):
        console.print(
            "[red]Error:[/red] Cannot proceed with vector search. Embeddings generation failed."
        )
        msg = "Embeddings generation failed"
        raise click.ClickException(msg)

    # Use simple embeddings handler
    from yt_fts.llm.simple_embeddings import SimpleEmbeddingsHandler

    embeddings_handler = SimpleEmbeddingsHandler()

    # Get query embedding and search using FAISS
    query_embedding = embeddings_handler.get_embedding(text)

    from yt_fts.llm.faiss_store import FaissVectorStore
    vector_store = FaissVectorStore()
    results = vector_store.search(
        query_embedding=query_embedding,
        channel_id=channel_id,
        k=limit
    )

    # Display results
    if not results:
        console.print(f"[yellow]No results found for query: '{text}'[/yellow]")
        return  # Success - let Click handle naturally

    console.print(f"\n[bold]Vector Search Results for '{text}'[/bold]")
    console.print(f"Found {len(results)} similar segments:\n")

    for i, result in enumerate(results, 1):
        similarity = result["similarity"]
        # FAISS returns flat result structure with metadata directly in result
        text = result.get("text", "")

        console.print(f"[blue]{i}.[/blue] [green]Similarity: {similarity:.3f}[/green]")
        console.print(f"[bold]Video:[/bold] {result['video_title']}")
        console.print(f"[bold]Channel:[/bold] {result['channel_name']}")
        console.print(f"[bold]Time:[/bold] {result['start_time']}")
        console.print(
            f"[bold]Text:[/bold] {text[:200]}{'...' if len(text) > 200 else ''}"
        )
        console.print("-" * 50)

    if export:
        import csv

        filename = f"vector_search_{text.replace(' ', '_')[:20]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        with Path(filename).open("w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "rank",
                "similarity",
                "video_title",
                "channel_name",
                "start_time",
                "text",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, result in enumerate(results, 1):
                writer.writerow(
                    {
                        "rank": i,
                        "similarity": result["similarity"],
                        "video_title": result["video_title"],
                        "channel_name": result["channel_name"],
                        "start_time": result["start_time"],
                        "text": result.get("text", ""),
                    }
                )
        console.print(f"\n[green]Results exported to:[/green] {filename}")



@click.command(
    name="watch-search",
    help="""
    Search within your watch history.

    Searches video titles and channel names in your watch history.
    Case-insensitive substring search.

    Examples:
        yt-fts watch-search "python"
        yt-fts watch-search "Academy" --days 30
        yt-fts watch-search "tutorial" --limit 10 --format json
    """,
)
@click.argument("query", required=True)
@click.option(
    "--days",
    "-d",
    type=int,
    default=None,
    help="Only search videos watched in the last N days",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    help="Maximum number of results to show (default: 20)",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format: table (default) or json",
)
def watch_search(query: str, days: int | None, limit: int, output_format: str) -> None:
    """Search within watch history."""
    from rich.table import Table

    from .watch import search_watched

    results = search_watched(query=query, days=days, limit=limit)

    if output_format == "json":
        click.echo(json.dumps(results, indent=2))
        return

    if not results:
        console.print(f"[yellow]No matches found for '{query}'[/yellow]")
        return

    table = Table(title=f"Watch History Search: '{query}'")
    table.add_column("Time", style="dim")
    table.add_column("Video")
    table.add_column("Channel")

    for item in results:
        watched_at = item["watched_at"]
        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(watched_at)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = watched_at

        table.add_row(
            time_str,
            item["video_title"] or item["video_id"],
            item["channel_name"] or "",
        )

    console.print(table)
