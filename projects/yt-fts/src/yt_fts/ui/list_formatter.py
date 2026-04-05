from __future__ import annotations

import sqlite3

from rich.console import Console
from rich.table import Table

from yt_fts.db.videos import get_title_from_db
from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path
from yt_fts.utils.helpers import get_time_delta, time_to_secs


def show_video_transcript(video_id: str) -> None:
    """
    Display the transcript for a specific video.

    Args:
        video_id: Video identifier.

    Returns:
        None
    """
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM subtitles WHERE video_id=?", (video_id,))
        rows = cur.fetchall()

        console = Console()
        word_count = 0
        for row in rows:
            timestamp = row[2]
            time = time_to_secs(timestamp)
            url = f"https://www.youtube.com/watch?v={video_id}&t={time}s"
            text = row[4]
            word_count += len(text.split())
            console.print(f"[link={url}]{timestamp[:-4]}[/link] - {text}")

        video_length = get_time_delta(rows[0][2], rows[-1][2])
        video_title = get_title_from_db(video_id)
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        console.print("")
        console.print(f"Title: [bold][link={video_url}]{video_title}[/link][/bold]")
        console.print(f"Video Length: {video_length}")
        console.print(f"Word Count: {word_count}")


def show_video_list(channel_id: str) -> None:
    """
    List all videos for a channel.

    Args:
        channel_id: Channel identifier.

    Returns:
        None
    """
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM videos WHERE channel_id=?", (channel_id,))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Link", style="cyan")
        table.add_column("Video ID")
        table.add_column("Title")

        rows = cur.fetchall()
        for i, row in enumerate(rows):
            video_id = row[0]
            link = f"https://www.youtube.com/watch?v={video_id}"
            link_str = f"[link={link}]Link[/link]"
            title = get_title_from_db(video_id)

            table.add_row(link_str, video_id, title)

            if i != len(rows) - 1:
                table.add_row(
                    "----", "-" * len(video_id), "-" * len(title), style="dim"
                )

        console = Console()
        console.print(table)
        console.print("")
        console.print(f"[bold]Total videos: {len(rows)}[/bold]")


def list_channels(channel_id: str | None = None) -> None:
    """
    List all channels in the database.

    Args:
        channel_id: Optional channel ID to filter by.

    Returns:
        None
    """
    from yt_fts.core.database import get_channel_list_by_id, get_channels, get_num_vids
    from yt_fts.display.rich_table_builder import RichTableBuilder

    builder = RichTableBuilder(header_style="bold")
    builder.add_column("ID", style="cyan")
    builder.add_column("Name", justify="left")
    builder.add_column("Count")
    builder.add_column("Channel ID", justify="left")

    if channel_id is not None:
        channel = next(iter(get_channel_list_by_id(channel_id)))
        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        channel.insert(1, count)

        id_link = f"[link={channel_url}]{channel_id}[/link]"
        builder.add_row(str(channel[0]), channel[2], str(channel[1]), id_link)

        console = Console()
        console.print("")
        console.print(builder.build(), justify="left")
        console.print("")
        return

    raw_channels = get_channels()
    for i in raw_channels:
        # get_channels() returns: channel_id, channel_name, channel_url
        channel_id = i[0]
        channel_name = i[1]
        # i[2] is channel_url, not used directly

        if check_ss_enabled(channel_id):
            channel_name += " (ss)"

        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        id_link = f"[link={channel_url}]{channel_id}[/link]"

        # Use channel_id as the ID column (no separate row_id in schema)
        builder.add_row(str(channel_id), channel_name, str(count), id_link)

    console = Console()
    console.print("")
    console.print(builder.build(), justify="left")
    console.print("")


#  not dry but for some reason importing from get_embeddings.py causes slow down
def check_ss_enabled(channel_id: str | None = None) -> bool:
    """
    Check if semantic search is enabled for a channel.

    Args:
        channel_id: Optional channel identifier.

    Returns:
        True if semantic search is enabled.
    """
    from yt_fts.db.infra import get_db_connection

    db_path = get_db_path()
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()

        if channel_id is None:
            cur.execute(
                """
            SELECT channel_id FROM SemanticSearchEnabled
            """
            )
        else:
            cur.execute(
                """
            SELECT channel_id FROM SemanticSearchEnabled
            WHERE channel_id = ?
            """,
                [channel_id],
            )

        res = cur.fetchone()
        return res is not None
