"""
Playlist CLI command - extract channels from playlist and update channels list.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote

import click
import requests
import yt_dlp
from rich.console import Console

from yt_fts.auth import (
    get_oauth_credentials,
    is_oauth_required,
    setup_oauth_instructions,
)
from yt_fts.db.infra import get_db_connection
from yt_fts.core.database import get_db_path


def _detect_available_browsers() -> list[str]:
    """Detect available browsers for cookie extraction.

    Returns browsers in preference order (Firefox first - best cookie support).
    """
    browsers = []

    # Check Firefox FIRST - best cookie support on Windows (no DPAPI issues)
    firefox_paths = [
        os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
        os.path.expanduser("~/Library/Application Support/Firefox/Profiles"),
        os.path.expanduser("~/.mozilla/firefox"),
    ]
    if any(os.path.exists(p) for p in firefox_paths):
        browsers.append("firefox")

    # Check Chrome SECOND - may have DPAPI issues on Windows
    chrome_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        os.path.expanduser("~/.config/google-chrome"),
    ]
    if any(os.path.exists(p) for p in chrome_paths):
        browsers.append("chrome")

    # Check Edge LAST - also has DPAPI issues on Windows
    edge_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.MicrosoftEdge_*\LocalCache\Roaming\Microsoft\Edge\User Data"),
        os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
        os.path.expanduser("~/.config/microsoft-edge"),
    ]
    if any(os.path.exists(p) for p in edge_paths):
        browsers.append("edge")

    return browsers


def _load_api_keys() -> list[str]:
    """Load YouTube API keys from environment variables."""
    keys = []
    if key1 := os.getenv("YOUTUBE_API_KEY"):
        keys.append(key1)
    if key2 := os.getenv("YOUTUBE_API_KEY_2"):
        keys.append(key2)
    return keys


def _extract_playlist_id(url: str) -> str | None:
    """Extract playlist ID from URL."""
    patterns = [
        r"[?&]list=([a-zA-Z0-9_-]+)",
        r"playlist\?list=([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def _extract_channels_via_youtube_api(
    playlist_id: str,
    console: Console,
    api_keys: list[str] | None = None,
    use_oauth: bool = False,
) -> list[dict] | None:
    """
    Extract channels from playlist using YouTube Data API v3.

    This is more reliable for special playlists (WL, Liked) than yt-dlp.
    For private playlists like WL/LL, OAuth authentication is used.

    Args:
        playlist_id: YouTube playlist ID (e.g., "WL", "LL", or actual ID)
        console: Rich console for output
        api_keys: List of YouTube API keys (optional, for public playlists)
        use_oauth: If True, use OAuth credentials instead of API key

    Returns:
        List of dicts with channel_id, name, url, or None if API unavailable
    """
    channels_dict = {}

    # YouTube API v3 playlistItems endpoint
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    page_token = None

    # Prepare auth headers
    headers = {}
    auth_params = {}

    if use_oauth:
        # Try OAuth for private playlists
        creds = get_oauth_credentials()
        if not creds:
            console.print("[dim]  OAuth credentials not available[/dim]")
            console.print(setup_oauth_instructions())
            return None

        if not creds.valid:
            console.print("[dim]  OAuth credentials expired[/dim]")
            return None

        headers["Authorization"] = f"Bearer {creds.token}"
    elif not api_keys:
        console.print("[dim]  No YOUTUBE_API_KEY found in .env[/dim]")
        return None
    else:
        auth_params["key"] = api_keys[0]

    try:
        while True:
            params = {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": 50,  # Max per page
            }
            params.update(auth_params)

            if page_token:
                params["pageToken"] = page_token

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 401:
                console.print("[dim]  OAuth authorization failed - token may be expired[/dim]")
                return None
            if response.status_code == 403:
                if use_oauth:
                    console.print("[dim]  OAuth access denied - check permissions[/dim]")
                else:
                    console.print("[dim]  API quota exceeded or key invalid[/dim]")
                return None
            if response.status_code == 404:
                console.print("[dim]  Playlist not found (may be empty or private)[/dim]")
                return None

            response.raise_for_status()
            data = response.json()

            # Check if playlist is empty
            total_results = data.get("pageInfo", {}).get("totalResults", 0)
            if total_results == 0 and not channels_dict:
                console.print(f"[dim]  Playlist '{playlist_id}' is empty or inaccessible[/dim]")
                if use_oauth:
                    console.print("[dim]  Make sure you're authorized with the correct Google account[/dim]")
                    console.print("[dim]  (Delete youtube_oauth_token.json to re-authorize)[/dim]")
                return None

            # Extract channel info from each item
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                resource_id = snippet.get("resourceId", {})

                # Skip if not a video (could be playlist, etc.)
                if resource_id.get("kind") != "youtube#video":
                    continue

                channel_id = snippet.get("videoOwnerChannelId")
                channel_name = snippet.get("videoOwnerChannelTitle", "Unknown Channel")

                if channel_id:
                    # Build channel URL (prefer @handle format)
                    channel_handle = snippet.get("videoOwnerChannelName")
                    if channel_handle and channel_handle.startswith("@"):
                        channel_url = f"https://www.youtube.com/{quote(channel_handle, safe="")}"
                    else:
                        # Fallback to channel URL with ID
                        channel_url = f"https://www.youtube.com/channel/{channel_id}"

                    channels_dict[channel_id] = {
                        "channel_id": channel_id,
                        "name": channel_name,
                        "url": channel_url,
                    }

            # Check for next page
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        if channels_dict:
            return list(channels_dict.values())

        return None

    except requests.RequestException as e:
        console.print(f"[dim]  API request error: {str(e)[:60]}...[/dim]")
        return None
    except Exception as e:
        console.print(f"[dim]  API error: {type(e).__name__}: {str(e)[:60]}...[/dim]")
        return None


@click.command(
    name="playlist",
    help="""
    Extract channels from a YouTube playlist and update channels list.

    Takes a YouTube playlist URL, extracts all unique channels from videos
    in the playlist, and adds them to both channels.txt and channels.db.

    Automatically removes duplicates and shows a summary of channels added.

    Example:
        yt-fts playlist "https://www.youtube.com/playlist?list=..."
    """,
)
@click.argument("playlist_url")
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=None,
    help="Path to channels.txt file (default: data/channels.txt)",
)
@click.option(
    "-d",
    "--database",
    type=click.Path(),
    default=None,
    help="Path to database file (default: data/subtitles.db)",
)
@click.option(
    "--cookies-from-browser",
    default=None,
    help="Browser for cookies (auto-detected if not specified)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without making changes",
)
def playlist(playlist_url: str, output: str, database: str, cookies_from_browser: str, dry_run: bool) -> int:
    """
    Extract channels from playlist and update channels list.

    Args:
        playlist_url: YouTube playlist URL
        output: Path to channels.txt file
        database: Path to database file
        cookies_from_browser: Browser for cookies (auto-detected if needed)
        dry_run: Show changes without applying them

    Returns:
        0 on success, 1 on error
    """
    console = Console()

    # Default paths
    if output is None:
        output = "data/channels.txt"
    if database is None:
        database = str(get_db_path())

    output_path = Path(output)
    db_path = Path(database)

    try:
        # Validate playlist URL
        if not _is_valid_playlist_url(playlist_url):
            console.print("[red]❌ Invalid playlist URL[/red]")
            console.print("[yellow]Expected format:[/yellow]")
            console.print("  https://www.youtube.com/playlist?list=...")
            console.print("  https://www.youtube.com/watch?v=...&list=...")
            return 1

        console.print("[cyan]📋 Extracting channels from playlist...[/cyan]")
        console.print(f"[dim]URL: {playlist_url}[/dim]\n")

        # Auto-detect browsers if cookies not specified
        if not cookies_from_browser:
            available_browsers = _detect_available_browsers()
        else:
            available_browsers = [cookies_from_browser]

        # Try without cookies first, then retry with cookies if needed
        channels = None
        last_error = None

        # First attempt: no cookies (for public playlists)
        with console.status("[bold yellow]Fetching playlist info...[/bold yellow]"):
            channels = _extract_channels_from_playlist(playlist_url, console, None)

        if not channels:
            # Failed - try with auto-detected cookies
            if available_browsers:
                console.print("[dim]ⓘ Playlist may require authentication, trying browser cookies...[/dim]\n")
                for browser in available_browsers:
                    try:
                        with console.status(f"[bold yellow]Trying {browser}...[/bold yellow]"):
                            channels = _extract_channels_from_playlist(playlist_url, console, browser)
                        if channels:
                            console.print(f"[dim]✓ Using {browser} for authentication[/dim]\n")
                            break
                        console.print(f"[dim]  {browser}: No channels found[/dim]")
                    except Exception as e:
                        # Check for DPAPI/cookie errors
                        error_msg = str(e)
                        if "DPAPI" in error_msg or "decrypt" in error_msg.lower():
                            console.print(f"[dim]  {browser}: Cookie encryption not supported (Windows DPAPI)[/dim]")
                        elif "cookies" in error_msg.lower():
                            console.print(f"[dim]  {browser}: Could not load cookies[/dim]")
                        else:
                            console.print(f"[dim]  {browser}: {error_msg[:60]}...[/dim]")
                        last_error = f"{browser}: {type(e).__name__}"

        if not channels:
            # Final fallback: Try YouTube API with OAuth for private playlists
            playlist_id = _extract_playlist_id(playlist_url)

            if playlist_id:
                # Use OAuth for Watch Later and Liked playlists (requires user auth)
                use_oauth = is_oauth_required(playlist_id)

                if use_oauth:
                    console.print("[dim]ⓘ Watch Later playlist detected, using OAuth...[/dim]\n")
                    with console.status("[bold yellow]Fetching via YouTube API (OAuth)...[/bold yellow]"):
                        channels = _extract_channels_via_youtube_api(
                            playlist_id, console, api_keys=None, use_oauth=True
                        )

                    if channels:
                        console.print(f"[dim]✓ Using YouTube API with OAuth ({len(channels)} channels)[/dim]\n")
                    else:
                        console.print("[dim]  YouTube API (OAuth): No channels returned[/dim]")
                        console.print("[dim]  Make sure you're logged into the correct Google account[/dim]")
                else:
                    # Try with API key for public playlists
                    api_keys = _load_api_keys()
                    if api_keys:
                        console.print("[dim]ⓘ yt-dlp methods failed, trying YouTube API...[/dim]\n")
                        with console.status("[bold yellow]Fetching via YouTube API...[/bold yellow]"):
                            channels = _extract_channels_via_youtube_api(
                                playlist_id, console, api_keys=api_keys, use_oauth=False
                            )

                        if channels:
                            console.print(f"[dim]✓ Using YouTube API (quota used: ~{len(channels)//50 + 1})[/dim]\n")
                        else:
                            console.print("[dim]  YouTube API: No channels returned[/dim]")

        if not channels:
            console.print("[red]❌ Failed to extract playlist[/red]")
            if last_error:
                console.print(f"[yellow]⚠ {last_error}[/yellow]")
            console.print("[yellow]💡 Try:[/yellow]")
            console.print("   • Verify the playlist URL is correct")
            playlist_id = _extract_playlist_id(playlist_url)
            if is_oauth_required(playlist_id):
                console.print("   • For Watch Later/Liked: Set up OAuth credentials")
                console.print(setup_oauth_instructions())
            else:
                console.print("   • Set YOUTUBE_API_KEY in .env for API access")
            console.print("   • Sign in to YouTube in your browser")
            return 1

        console.print(f"[green]✓ Found {len(channels)} unique channel(s)[/green]\n")

        # Show channels found
        for i, channel in enumerate(channels, 1):
            console.print(f"  {i}. {channel['name']} ({channel['url']})")

        console.print()

        # Get existing channels
        existing_txt_channels = _load_channels_from_txt(output_path)
        _load_channels_from_db(db_path)

        # Determine new channels
        new_channels = []
        for channel in channels:
            url = channel["url"]
            if url not in existing_txt_channels:
                new_channels.append(channel)

        if not new_channels:
            console.print("[yellow]⚠ All channels already in channels.txt[/yellow]")
            return 0

        console.print(f"[cyan]📝 {len(new_channels)} new channel(s) to add[/cyan]\n")

        if dry_run:
            console.print("[yellow]🔍 Dry run mode - no changes will be made[/yellow]")
            console.print(f"[dim]Would add to {output_path}:[/dim]")
            for channel in new_channels:
                console.print(f"  + {channel['url']}")
            return 0

        # Update channels.txt
        _update_channels_txt(output_path, new_channels, console)

        # Update channels.db
        _update_channels_db(db_path, new_channels, console)

        console.print(f"\n[green]✅ Done! Added {len(new_channels)} channel(s)[/green]")
        console.print(f"[dim]   {output_path}[/dim]")
        console.print(f"[dim]   {db_path}[/dim]")

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        return 1


def _is_valid_playlist_url(url: str) -> bool:
    """Validate that the URL is a YouTube playlist URL."""
    if not url:
        return False

    # Extract playlist ID from various URL formats
    patterns = [
        r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)",  # Standard playlist URL
        r"youtube\.com/watch.*[?&]list=([a-zA-Z0-9_-]+)",  # Watch page with playlist
        r"youtu\.be/.*[?&]list=([a-zA-Z0-9_-]+)",  # Short URL with playlist
    ]

    return any(re.search(pattern, url) for pattern in patterns)


def _extract_channels_from_playlist(
    playlist_url: str, console: Console, cookies_from_browser: str | None = None
) -> list[dict]:
    """
    Extract all unique channels from a YouTube playlist.

    Returns:
        List of dicts with keys: channel_id, name, url
    """
    channels_dict = {}  # Use dict to deduplicate by channel_id

    # yt-dlp options
    # Note: Watch Later playlist requires full extraction (extract_flat=False)
    # because it returns empty entries with extract_flat=True
    is_watch_later = "list=WL" in playlist_url

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": not is_watch_later,  # Full extract for WL playlist
        "ignoreerrors": True,
    }

    # Add cookies if specified (required for private playlists like WL)
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

            if not info:
                # Silent failure - let caller handle
                return []

            info.get("id", "unknown")
            playlist_title = info.get("title", "Unknown Playlist")

            # Only show playlist info if we're not in a retry loop
            # (caller handles status display)
            console.print(
                f"[dim]Playlist: {playlist_title}[/dim]"
            )
            console.print(
                f"[dim]Videos: {info.get('entry_count', 'unknown')}[/dim]\n"
            )

            # Extract channel info from each video
            entries = info.get("entries", [])
            if not entries:
                # Silent failure - playlist exists but has no accessible entries
                # (common with private playlists when cookies don't work)
                return []

            # Simple progress - avoid Rich Progress which conflicts with console.status
            total = len(entries)
            for i, entry in enumerate(entries, 1):
                channel_id = entry.get("channel_id")
                channel_name = entry.get("channel", "Unknown Channel")
                channel_url = entry.get("channel_url")

                if channel_id:
                    # Use the actual channel_url from yt-dlp (most reliable)
                    # If not available, construct from channel_id (never fabricate from name)
                    if channel_url:
                        channel_url_clean = channel_url
                    else:
                        # Fallback: use channel_id format (reliable)
                        channel_url_clean = f"https://www.youtube.com/channel/{channel_id}"

                    channels_dict[channel_id] = {
                        "channel_id": channel_id,
                        "name": channel_name,
                        "url": channel_url_clean,
                    }

                # Show progress every 10 entries or at the end
                if i % 10 == 0 or i == total:
                    console.print(
                        f"[dim]  Extracted {i}/{total} channels...[/dim]"
                    )

    except Exception as e:
        console.print(f"[red]Error extracting playlist: {e}[/red]")
        raise

    return list(channels_dict.values())


def _load_channels_from_txt(path: Path) -> set[str]:
    """Load existing channel URLs from channels.txt."""
    channels = set()

    if not path.exists():
        return channels

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    channels.add(line)
    except (OSError, UnicodeDecodeError):
        pass  # If file doesn't exist or can't be read, return empty set

    return channels


def _load_channels_from_db(path: Path) -> set[str]:
    """Load existing channel URLs from database."""
    channels = set()

    if not path.exists():
        return channels

    try:
        import sqlite3

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT channel_url FROM Channels")
        for row in cursor.fetchall():
            channels.add(row[0])

        conn.close()
    except (sqlite3.Error, OSError):
        pass  # If table doesn't exist or other error, return empty set

    return channels


def _update_channels_txt(
    path: Path, new_channels: list[dict], console: Console
) -> None:
    """Append new channels to channels.txt."""
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content
    existing_lines = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing_lines = f.readlines()

    # Find where to insert (before first non-comment, or at end)
    insert_position = len(existing_lines)
    for i, line in enumerate(existing_lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            insert_position = i
            break

    # Prepare new entries
    new_entries = []
    for channel in new_channels:
        new_entries.append(f"{channel['url']}\n")

    # Write updated file
    with open(path, "w", encoding="utf-8") as f:
        # Write existing content before insert position
        f.writelines(existing_lines[:insert_position])

        # Add a blank line if inserting in middle
        if insert_position > 0 and insert_position < len(existing_lines):
            f.write("\n")

        # Write new channels
        f.writelines(new_entries)

        # Write remaining content
        f.writelines(existing_lines[insert_position:])

    console.print(f"[dim]  ✓ Updated {path}[/dim]")


def _update_channels_db(
    path: Path, new_channels: list[dict], console: Console
) -> None:
    """Insert new channels into database."""
    import sqlite3

    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure Channels table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS [Channels] (
            [channel_id] TEXT PRIMARY KEY,
            [channel_name] TEXT NOT NULL,
            [channel_url] TEXT NOT NULL
        )
    """)

    # Insert new channels (ignore duplicates)
    added_count = 0
    for channel in new_channels:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO Channels (channel_id, channel_name, channel_url)
                VALUES (?, ?, ?)
                """,
                (channel["channel_id"], channel["name"], channel["url"])
            )
            if cursor.rowcount > 0:
                added_count += 1
        except sqlite3.IntegrityError:
            pass  # Duplicate, skip

    conn.commit()
    conn.close()

    console.print(f"[dim]  ✓ Updated {path} (+{added_count} new)[/dim]")
