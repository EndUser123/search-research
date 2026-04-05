"""
Multi-channel search functionality for yt-fts.

Provides search capabilities across multiple YouTube channels simultaneously.
"""
from __future__ import annotations

import re

from rich.console import Console

from yt_fts.db.search import search_channel

from .database import (
    get_channel_id_from_input,
    get_channels,
)


class MultiChannelSearchController:
    """Controller for managing multi-channel search operations."""

    def __init__(self, console: Console | None = None):
        """
        Initialize the multi-channel search controller.

        Args:
            console: Rich console instance for output
        """
        self.console = console or Console()

    def search_multiple_channels(self,
                                channel_inputs: list[str],
                                query: str,
                                limit: int | None = None) -> list[dict]:
        """
        Search across multiple channels for the given query.

        Args:
            channel_inputs: List of channel handles, URLs, or IDs
            query: Search query string
            limit: Maximum results per channel

        Returns:
            Combined list of search results from all channels
        """
        all_results = []
        valid_channels = []
        invalid_channels = []

        # Resolve channel inputs to IDs
        for channel_input in channel_inputs:
            try:
                channel_id = get_channel_id_from_input(channel_input)
                if channel_id:
                    valid_channels.append(channel_id)
                else:
                    invalid_channels.append(channel_input)
            except (OSError, ValueError, TypeError, RuntimeError):
                invalid_channels.append(channel_input)

        # Report invalid channels
        if invalid_channels:
            self.console.print(f"[yellow]Warning: Could not resolve {len(invalid_channels)} channels[/yellow]")
            for invalid in invalid_channels:
                self.console.print(f"  • {invalid}")

        # Search valid channels
        for channel_id in valid_channels:
            try:
                results = search_channel(channel_id, query, limit)
                all_results.extend(results)
            except Exception as e:
                self.console.print(f"[red]Error searching channel {channel_id}: {e}[/red]")

        return all_results

    def get_channel_statistics(self) -> list[dict]:
        """
        Get statistics for all channels in the database.

        Returns:
            List of channel information with statistics
        """
        channels = get_channels()
        stats = []

        for channel_row in channels:
            channel_stats = {
                "id": channel_row[0],
                "name": channel_row[1],
                "url": channel_row[2],
                "channel_id": channel_row[3],
                "video_count": channel_row[4] if len(channel_row) > 4 else 0
            }
            stats.append(channel_stats)

        return stats



    def search_multiple_channels_vector(
        self,
        query: str,
        channel_ids: list[str],
        limit: int = 10,
        api_key: str = "",
        model: str = "all-MiniLM-L6-v2",
    ) -> list[dict]:
        """
        Perform semantic vector search across multiple channels.

        Args:
            query: Search query string
            channel_ids: List of channel IDs to search
            limit: Maximum results per channel
            api_key: API key (not used for local models, kept for compatibility)
            model: Embedding model name

        Returns:
            Combined list of vector search results from all channels
        """
        from yt_fts.llm.faiss_store import FaissVectorStore
        from yt_fts.llm.simple_embeddings import SemanticEmbeddingsHandler

        all_results = []

        # Initialize embeddings handler
        embeddings_handler = SemanticEmbeddingsHandler(model_name=model)

        # Generate query embedding
        query_embedding = embeddings_handler.get_embedding(query)

        # Search each channel using FAISS
        for channel_id in channel_ids:
            try:
                # Ensure embeddings exist for the channel
                embeddings_handler.generate_and_store_embeddings(
                    channel_id, show_progress=False
                )

                # Build FAISS index if needed
                vector_store = FaissVectorStore(model_name=model)
                if not vector_store.index_exists(channel_id):
                    vector_store.build_index(channel_id)

                # Search using FAISS
                channel_results = vector_store.search(query_embedding, channel_id, k=limit)

                # Format results
                for result in channel_results:
                    all_results.append({
                        "video_id": result.get("video_id"),
                        "start_time": result.get("start_time"),
                        "text": result.get("text"),
                        "video_title": result.get("video_title"),
                        "channel_name": result.get("channel_name"),
                        "channel_id": result.get("channel_id"),
                        "similarity": result.get("similarity", 0.0),
                        "result_type": "vector",
                    })

            except Exception as e:
                self.console.print(f"[red]Error in vector search for channel {channel_id}: {e}[/red]")

        # Sort by similarity (highest first)
        all_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        # Return top results
        return all_results[:limit] if limit else all_results

def parse_channel_inputs(channel_inputs: list[str]) -> tuple[list[str], list[str]]:
    """
    Parse and validate channel inputs from user input.

    Args:
        channel_inputs: Raw channel input strings

    Returns:
        Tuple of (valid_channels, invalid_channels)
    """
    valid_channels = []
    invalid_channels = []

    for channel_input in channel_inputs:
        channel_input = channel_input.strip()
        if not channel_input:
            continue

        # Basic validation for YouTube channel formats
        if (channel_input.startswith("@") or
            "youtube.com/channel/" in channel_input or
            "youtube.com/c/" in channel_input or
            "youtube.com/@" in channel_input or
            re.match(r"^UC[a-zA-Z0-9_-]{22}$", channel_input)):  # Channel ID pattern
            valid_channels.append(channel_input)
        else:
            invalid_channels.append(channel_input)

    return valid_channels, invalid_channels
