import textwrap

from rich.console import Console

from yt_fts.db.search_history import save_search

# from openai import OpenAI  # Lazy import below
from yt_fts.services.export import ExportHandler
from yt_fts.utils import Model, bold_query_matches, time_to_secs

from .database import (
    get_channel_id_from_input,
    get_channel_info_from_video_id,
    get_channel_name_from_video_id,
    get_metadata_from_db,
    search_all,
    search_channel,
    search_video,
)


class SearchHandler:
    def __init__(
        self,
        scope: str = "all",
        channel: str | None = None,
        video_id: str | None = None,
        export: bool = False,
        limit: int | None = None,
        openai_client: object | None = None,  # type: ignore
        proximity: int | None = None,
        near: str | None = None,
        after_date: str | None = None,
        before_date: str | None = None,
        language: str | None = None,
    ) -> None:
        """
        Initialize the search handler with configuration options.

        Args:
            scope: Search scope - "all", "channel", or "video".
            channel: Channel name or ID for channel-scoped search.
            video_id: Video ID for video-scoped search.
            export: If True, export results to file.
            limit: Maximum number of results to return.
            openai_client: OpenAI client for vector search (optional).
            proximity: Proximity window for phrase search in seconds.
            near: Term to search near for phrase queries.
            after_date: Filter results after this date (YYYY-MM-DD).
            before_date: Filter results before this date (YYYY-MM-DD).
            language: Filter by subtitle language code.

        Returns:
            None
        """
        self.console = Console()
        self.scope = scope
        self.channel = channel
        self.video_id = video_id
        self.export = export
        self.limit = limit
        self.proximity = proximity
        self.near = near
        self.after_date = after_date
        self.before_date = before_date
        self.language = language
        self.channel_id: str | None = None
        self.query = ""
        self.response = []
        self.openai_client = openai_client
        self.max_width = 80

    def full_text_search(self, query: str) -> None:
        """
        Perform full-text search using SQLite FTS5.

        Args:
            query: Search query string.

        Returns:
            None
        """
        console = self.console
        self.query = query

        if self.scope == "all":
            self.res = search_all(
                query,
                self.limit,
                proximity=self.proximity,
                near_term=self.near,
                after_date=self.after_date,
                before_date=self.before_date,
                language=self.language,
            )

        if self.scope == "channel":
            self.channel_id = get_channel_id_from_input(self.channel)
            self.res = search_channel(
                self.channel_id,
                self.query,
                self.limit,
                proximity=self.proximity,
                near_term=self.near,
                after_date=self.after_date,
                before_date=self.before_date,
                language=self.language,
            )

        if self.scope == "video":
            self.res = search_video(
                self.video_id,
                self.query,
                self.limit,
                proximity=self.proximity,
                near_term=self.near,
                after_date=self.after_date,
                before_date=self.before_date,
                language=self.language,
            )

        if len(self.res) == 0:
            console.print(
                "[yellow]No matches found[/yellow]\n"
                "- Try shortening the search to specific words\n"
                "- Try using the wildcard operator [bold]*[/bold] to search for partial words\n"
                "- Try using the [bold]OR[/bold] operator to search for multiple words\n"
                '   - EX: "foo OR bar"'
            )

        self.print_fts_res()
        if self.export:
            export_handler = ExportHandler()
            export_handler.export_fts(
                self.query, self.scope, self.channel, self.video_id
            )

        console.print(f"Query '{self.query}' ")
        console.print(f"Scope: {self.scope}")

        # Save search to history
        try:
            save_search(
                query=self.query,
                scope=self.scope,
                result_count=len(self.res),
                channel_id=self.channel_id,
            )
        except Exception:
            # Silently fail if history saving fails
            pass

    def vector_search(self, query: str, model: "Model") -> None:
        """
        Perform semantic vector search using FAISS.

        Args:
            query: Search query string
            model: Model configuration object
        """
        from yt_fts.llm.faiss_store import FaissVectorStore
        from yt_fts.llm.simple_embeddings import SemanticEmbeddingsHandler

        console = self.console

        # Determine channel based on scope
        if self.scope == "channel":
            if not self.channel:
                console.print("[red]Error: Channel required for vector search[/red]")
                return
            # Resolve channel name to ID if needed
            channel_id = get_channel_id_from_input(self.channel)
            channel_ids = [channel_id]
        elif self.scope == "video":
            console.print(
                "[yellow]Video-scoped vector search not yet implemented[/yellow]"
            )
            console.print("[green]Use channel or all scope instead[/green]")
            return
        else:  # scope == "all"
            # Get all channels
            from .database import get_channels

            channels = get_channels()
            channel_ids = [ch[3] for ch in channels]  # channel_id is at index 3

        # Initialize handlers
        embeddings_handler = SemanticEmbeddingsHandler()
        vector_store = FaissVectorStore()

        # Generate query embedding
        query_embedding = embeddings_handler.get_embedding(query)

        all_results = []

        # Search each channel
        for channel_id in channel_ids:
            try:
                # Ensure embeddings exist
                embeddings_handler.generate_and_store_embeddings(
                    channel_id, show_progress=False
                )

                # Build FAISS index if needed
                if not vector_store.index_exists(channel_id):
                    vector_store.build_index(channel_id)

                # Search using FAISS
                channel_results = vector_store.search(
                    query_embedding, channel_id, k=self.limit or 10
                )

                all_results.extend(channel_results)

            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not search channel {channel_id}: {e}[/yellow]"
                )

        if not all_results:
            console.print(
                f"[yellow]No vector search results found for '{query}'[/yellow]"
            )
            return

        # Sort by similarity
        all_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        # Store results for printing
        self.res = [
            {
                "video_id": r.get("video_id"),
                "start_time": r.get("start_time"),
                "text": r.get("text"),
                "distance": 1.0
                - r.get(
                    "similarity", 0.0
                ),  # Convert similarity to distance for print_vector_search_results
            }
            for r in (
                all_results[: self.limit] if self.limit is not None else all_results
            )
        ]

        self.query = query
        self.print_vector_search_results()
        console.print(f"Query: '{query}'")
        console.print(f"Scope: {self.scope} (vector search)")

        # Save search to history
        try:
            from .database import save_search

            save_search(
                query=self.query,
                scope=f"{self.scope}_vector",
                result_count=len(self.res),
                channel_id=getattr(self, "channel_id", None),
            )
        except Exception:
            pass  # Silently fail if history saving fails

    def print_fts_res(self) -> None:
        """
        Print full-text search results formatted by channel and video.

        Returns:
            None
        """
        console = Console()

        query = self.query
        res = self.res
        fts_res = []
        channel_names = []

        for quote in res:
            quote_match = {}
            video_id = quote["video_id"]
            time_stamp = quote["start_time"]
            time = time_to_secs(time_stamp)
            link = f"https://youtu.be/{video_id}?t={time}"

            channel_name, channel_url = get_channel_info_from_video_id(video_id)
            quote_match["channel_name"] = channel_name or "Unknown"
            quote_match["channel_url"] = channel_url
            channel_names.append(quote_match["channel_name"])

            quote_match["metadata"] = get_metadata_from_db(video_id)
            quote_match["subs"] = bold_query_matches(quote["text"].strip(), query)
            quote_match["time_stamp"] = time_stamp
            quote_match["video_id"] = video_id
            quote_match["link"] = link

            fts_res.append(quote_match)

        fts_dict = {}
        for quote in fts_res:
            channel_name = quote["channel_name"]
            channel_url = quote.get("channel_url")
            metadata = quote["metadata"]
            video_name = metadata["video_title"]
            video_date = metadata["video_date"]
            video_id = quote["video_id"]
            quote_data = {
                "quote": quote["subs"],
                "time_stamp": quote["time_stamp"],
                "link": quote["link"],
            }
            # Use (channel_name, channel_url) as key to preserve URL
            if (channel_name, channel_url) not in fts_dict:
                fts_dict[(channel_name, channel_url)] = {}
            if (video_name, video_date) not in fts_dict[(channel_name, channel_url)]:
                fts_dict[(channel_name, channel_url)][
                    (video_name, video_date, video_id)
                ] = []
            fts_dict[(channel_name, channel_url)][
                (video_name, video_date, video_id)
            ].append(quote_data)

        # Sort the list by the total number of quotes in each channel
        channel_list = list(fts_dict.items())
        channel_list.sort(key=lambda x: sum(len(quotes) for quotes in x[1].values()))

        for (channel_name, channel_url), videos in channel_list:
            # Render channel name as clickable link if URL is available
            if channel_url:
                console.print(
                    f"[spring_green2][bold][link={channel_url}]{channel_name}[/link][/bold][/spring_green2]"
                )
            else:
                console.print(
                    f"[spring_green2][bold]{channel_name}[/bold][/spring_green2]"
                )
            console.print("")

            # Sort the list by the number of quotes in each video
            video_list = list(videos.items())
            video_list.sort(key=lambda x: len(x[1]))

            for (video_name, video_date, video_id), quotes in video_list:
                console.print(
                    f'{video_id} ({video_date}) "[bold][blue]{video_name}[/blue][/bold]"'
                )
                console.print("")

                # Sort the quotes by timestamp
                quotes.sort(key=lambda x: x["time_stamp"])

                for quote in quotes:
                    link = quote["link"]
                    time_stamp = quote["time_stamp"]
                    words = quote["quote"]
                    console.print(
                        f"       [grey62][link={link}]{time_stamp}[/link][/grey62] -> "
                        f'[italic][white]"{words}"[/white][/italic]'
                    )
                console.print("")

        num_matches = len(res)
        num_channels = len(set(channel_names))
        num_videos = len({quote["video_id"] for quote in res})

        summary_str = (
            f"Found [bold]{num_matches}[/bold] matches in [bold]{num_videos}[/bold] "
        )
        summary_str += f"videos from [bold]{num_channels}[/bold] channel"

        if num_channels > 1:
            summary_str += "s"

        console.print(summary_str)

    def print_vector_search_results(self) -> None:
        """
        Print vector search results with similarity scores.

        Returns:
            None
        """
        console = Console()

        channel_names = []

        res = self.res
        query = self.query

        for match in reversed(res):
            distance = match["distance"]
            link = match["link"]
            text = bold_query_matches(match["subs"], query)
            time_stamp = match["start_time"]
            channel_id = match["channel_id"]
            video_id = match["video_id"]
            title = match["video_title"]
            channel_name = match["channel_name"]
            channel_names.append(channel_name)

            console.print(
                f'[magenta][italic]"[link={link}]{text}[/link]"[/italic][/magenta]\n'
            )
            console.print(f"    Distance: {distance}", style="none")
            console.print(f"    Channel: {channel_name} - ({channel_id})", style="none")
            console.print(f"    Title: {title}")
            console.print(f"    Time Stamp: {time_stamp}")
            console.print(f"    Video ID: {video_id}")
            console.print(f"    Link: {link}")
            console.print("")

        num_matches = len(res)
        num_channels = len(set(channel_names))
        num_videos = len({quote["video_id"] for quote in res})

        summary_str = f"Found [bold]{num_matches}[/bold] matches in "
        summary_str += (
            f"[bold]{num_videos}[/bold] videos from [bold]{num_channels}[/bold] channel"
        )

        if num_channels > 1:
            summary_str += "s"

        console.print(summary_str)

    def wrap_text(self, text: str) -> str:
        """
        Wrap text to the configured max width, preserving code blocks.

        Args:
            text: Text to wrap.

        Returns:
            Wrapped text with markdown line breaks.
        """
        lines = text.split("\n")
        wrapped_lines = []

        for line in lines:
            # If the line is a code block, don't wrap it
            if line.strip().startswith("```") or line.strip().startswith("`"):
                wrapped_lines.append(line)
            else:
                # Wrap the line
                wrapped = textwrap.wrap(
                    line,
                    width=self.max_width,
                    break_long_words=False,
                    replace_whitespace=False,
                )
                wrapped_lines.extend(wrapped)

        # Join the wrapped lines back together
        return "  \n".join(wrapped_lines)

    def as_json(self) -> dict:
        """
        Convert search results to JSON-serializable dictionary.

        Returns:
            Dictionary with structured search results
        """
        from datetime import datetime, timezone

        if not hasattr(self, "res") or not self.res:
            return {
                "query": self.query,
                "scope": self.scope,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "matches": 0,
                "videos": 0,
                "channels": 0,
                "results": [],
            }

        # Group results by video
        videos_dict = {}
        channel_names = set()

        for quote in self.res:
            video_id = quote["video_id"]
            time_stamp = quote["start_time"]
            time = time_to_secs(time_stamp)
            link = f"https://youtu.be/{video_id}?t={time}"
            text = quote["text"]

            channel_name = get_channel_name_from_video_id(video_id)
            channel_names.add(channel_name)

            metadata = get_metadata_from_db(video_id)
            video_title = metadata["video_title"]
            video_date = metadata["video_date"]

            # Initialize video entry if not exists
            if video_id not in videos_dict:
                videos_dict[video_id] = {
                    "channel_name": channel_name,
                    "video_id": video_id,
                    "video_title": video_title,
                    "video_date": video_date,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}",
                    "quotes": [],
                }

            # Add quote to video
            videos_dict[video_id]["quotes"].append(
                {"timestamp": time_stamp, "text": text, "url": link}
            )

        # Convert to list
        videos_list = list(videos_dict.values())

        # Build output structure
        return {
            "query": self.query,
            "scope": self.scope,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "matches": sum(len(v["quotes"]) for v in videos_list),
            "videos": len(videos_list),
            "channels": len(channel_names),
            "results": videos_list,
        }
