"""
Enhanced Search Integration for yt-fts
Integrates embedding recovery with existing search functionality
"""

import logging
import time
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..src.yt_fts.config import get_chroma_client
from ..src.yt_fts.db_utils import (
    get_channel_name_from_video_id,
    get_title_from_db,
    search_all,
    search_channel,
    search_video,
    time_to_secs,
)
from ..src.yt_fts.llm.get_embeddings import EmbeddingsHandler
from ..src.yt_fts.search import SearchHandler
from ..src.yt_fts.utils import Model
from .embedding_recovery_manager import EmbeddingRecoveryManager


class EnhancedSearchHandler(SearchHandler):
    """
    Enhanced Search Handler with embedding recovery capabilities.

    Extends the existing yt-fts SearchHandler to include automatic
    embedding recovery and fallback strategies for missing embeddings.
    """

    def __init__(self,
                 scope: str = 'all',
                 channel: str | None = None,
                 video_id: str | None = None,
                 export: bool = False,
                 limit: int | None = None,
                 openai_client: Any = None,
                 enable_recovery: bool = True,
                 recovery_config: dict[str, Any] = None):
        """
        Initialize Enhanced Search Handler.

        Args:
            scope: Search scope ('all', 'channel', 'video')
            channel: Channel name for channel-scoped search
            video_id: Video ID for video-scoped search
            export: Enable export functionality
            limit: Maximum number of results
            openai_client: OpenAI client instance
            enable_recovery: Enable embedding recovery
            recovery_config: Configuration for recovery manager
        """
        super().__init__(scope, channel, video_id, export, limit, openai_client)

        self.enable_recovery = enable_recovery
        self.console = Console()
        self.logger = logging.getLogger(__name__)

        # Initialize recovery manager if enabled
        if self.enable_recovery:
            recovery_config = recovery_config or {}
            self.recovery_manager = EmbeddingRecoveryManager(**recovery_config)
        else:
            self.recovery_manager = None

        self.search_stats = {
            'total_searches': 0,
            'vector_searches': 0,
            'recovery_attempts': 0,
            'recovery_successes': 0,
            'total_search_time': 0.0
        }

        self.logger.info(f"EnhancedSearchHandler initialized (recovery: {self.enable_recovery})")

    def vector_search_with_recovery(self, query: str, model: Model) -> None:
        """
        Perform vector search with automatic embedding recovery.

        Args:
            query: Search query
            model: Model configuration
        """
        start_time = time.time()
        self.search_stats['total_searches'] += 1
        self.search_stats['vector_searches'] += 1

        console = self.console
        self.query = query

        console.print("[blue]Performing enhanced vector search...[/blue]")

        # Prepare scope options
        scope_options = self._prepare_scope_options()

        try:
            # Attempt standard vector search first
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Performing vector search...", total=None)

                chroma_results = self._attempt_vector_search(query, model, scope_options)

                progress.update(task, description="Analyzing search results...")

                # Check if we need recovery
                if self.recovery_manager and self._needs_recovery(chroma_results):
                    progress.update(task, description="Detecting missing embeddings...")
                    missing_info = self._identify_missing_embeddings(chroma_results, scope_options)

                    if missing_info:
                        progress.update(task, description="Recovering missing embeddings...")
                        recovery_results = self.recovery_manager.recover_missing_embeddings(
                            missing_info, model
                        )

                        # Re-run search with newly generated embeddings
                        if any(r.embedding_generated for r in recovery_results):
                            progress.update(task, description="Re-running search with recovered embeddings...")
                            chroma_results = self._attempt_vector_search(query, model, scope_options)

                progress.update(task, description="Processing results...")

        except Exception as e:
            console.print(f"[red]Vector search failed: {e}[/red]")
            self.logger.error(f"Vector search error: {e}")

            # Fallback to full-text search
            console.print("[yellow]Falling back to full-text search...[/yellow]")
            self.fallback_to_full_text_search(query)
            return

        # Process and display results
        self._process_vector_search_results(chroma_results, query, model)

        # Update statistics
        search_time = time.time() - start_time
        self.search_stats['total_search_time'] += search_time

        console.print(f"[green]Search completed in {search_time:.2f} seconds[/green]")

    def _prepare_scope_options(self) -> dict[str, str] | None:
        """Prepare scope options for ChromaDB query."""
        if self.scope == "all":
            return None
        elif self.scope == "channel":
            from ..src.yt_fts.db_utils import get_channel_id_from_input
            return {"channel_id": get_channel_id_from_input(self.channel)}
        elif self.scope == "video":
            return {"video_id": self.video_id}
        return None

    def _attempt_vector_search(self,
                             query: str,
                             model: Model,
                             scope_options: dict[str, str] | None) -> dict[str, Any]:
        """
        Attempt standard vector search.

        Args:
            query: Search query
            model: Model configuration
            scope_options: Scope options for filtering

        Returns:
            ChromaDB results
        """
        chroma_client = get_chroma_client()
        collection = chroma_client.get_collection(name="subEmbeddings")

        embeddings_handler = EmbeddingsHandler()

        # Generate query embedding
        from openai import OpenAI
        openai_client = OpenAI(api_key=model['api_key'], base_url=model['base_url'])

        search_embedding = next(embeddings_handler.get_embedding(
            [query], model['embedding_model'], openai_client)
        )

        # Perform search
        chroma_results = collection.query(
            query_embeddings=[search_embedding],
            n_results=self.limit,
            where=scope_options,
        )

        return chroma_results

    def _needs_recovery(self, chroma_results: dict[str, Any]) -> bool:
        """
        Determine if embedding recovery is needed.

        Args:
            chroma_results: Results from ChromaDB query

        Returns:
            True if recovery is needed
        """
        if not chroma_results or 'documents' not in chroma_results:
            return True

        documents = chroma_results['documents']
        if not documents or not documents[0]:
            return True

        # Check if we got fewer results than expected
        actual_count = len(documents[0])
        expected_count = self.limit or 10  # Default limit if not specified

        return actual_count < expected_count

    def _identify_missing_embeddings(self,
                                   chroma_results: dict[str, Any],
                                   scope_options: dict[str, str] | None) -> list:
        """
        Identify missing embeddings based on search results and scope.

        Args:
            chroma_results: Results from ChromaDB query
            scope_options: Search scope options

        Returns:
            List of missing embedding information
        """
        missing_info = []

        # For now, this is a simplified implementation
        # In a full implementation, we would:
        # 1. Query the database for expected content based on scope
        # 2. Cross-reference with actual ChromaDB results
        # 3. Identify content that should have embeddings but doesn't

        return missing_info

    def fallback_to_full_text_search(self, query: str) -> None:
        """
        Fallback to full-text search when vector search fails.

        Args:
            query: Search query
        """
        self.console.print("[yellow]Executing full-text search fallback...[/yellow]")

        try:
            # Use existing full-text search functionality
            if self.scope == 'all':
                self.res = search_all(query, self.limit)
            elif self.scope == 'channel':
                from ..src.yt_fts.db_utils import get_channel_id_from_input
                channel_id = get_channel_id_from_input(self.channel)
                self.res = search_channel(channel_id, query, self.limit)
            elif self.scope == 'video':
                self.res = search_video(self.video_id, query, self.limit)

            if len(self.res) == 0:
                self.console.print("[yellow]No matches found in fallback search[/yellow]")
            else:
                self.console.print(f"[green]Found {len(self.res)} results in fallback search[/green]")
                self.print_fts_res()

        except Exception as e:
            self.console.print(f"[red]Fallback search also failed: {e}[/red]")
            self.logger.error(f"Fallback search error: {e}")

    def _process_vector_search_results(self,
                                     chroma_results: dict[str, Any],
                                     query: str,
                                     model: Model) -> None:
        """
        Process and display vector search results.

        Args:
            chroma_results: Results from ChromaDB query
            query: Original search query
            model: Model configuration
        """
        if not chroma_results or 'documents' not in chroma_results:
            self.console.print("[yellow]No results found[/yellow]")
            return

        documents = chroma_results["documents"][0] if chroma_results["documents"] else []
        metadata = chroma_results["metadatas"][0] if chroma_results["metadatas"] else []
        distances = chroma_results["distances"][0] if chroma_results["distances"] else []

        if not documents:
            self.console.print("[yellow]No documents found in search results[/yellow]")
            return

        res = []

        for i in range(len(documents)):
            text = documents[i]
            video_id = metadata[i]["video_id"]
            start_time = metadata[i]["start_time"]
            link = f"https://youtu.be/{video_id}?t={time_to_secs(start_time)}"
            channel_name = get_channel_name_from_video_id(video_id)
            channel_id = metadata[i]["channel_id"]
            title = get_title_from_db(video_id)

            match = {
                "distance": distances[i],
                "channel_name": channel_name,
                "channel_id": channel_id,
                "video_title": title,
                "subs": text,
                "start_time": start_time,
                "video_id": video_id,
                "link": link,
            }
            res.append(match)

        self.res = res
        self.print_vector_search_results()

        # Export if requested
        if self.export:
            from ..src.yt_fts.export import ExportHandler
            export_handler = ExportHandler()
            export_handler.export_vector_search(self.res, self.query, self.scope)

    def enhanced_search(self, query: str, model: Model, search_type: str = "vector") -> None:
        """
        Enhanced search with automatic fallback and recovery.

        Args:
            query: Search query
            model: Model configuration
            search_type: Type of search ('vector', 'full_text', 'hybrid')
        """
        if search_type == "vector":
            self.vector_search_with_recovery(query, model)
        elif search_type == "full_text":
            self.full_text_search(query)
        elif search_type == "hybrid":
            # Try vector search first, fallback to full text
            try:
                self.vector_search_with_recovery(query, model)
            except Exception:
                self.console.print("[yellow]Vector search failed, trying full-text search...[/yellow]")
                self.full_text_search(query)

    def get_search_statistics(self) -> dict[str, Any]:
        """
        Get search handler statistics.

        Returns:
            Dictionary of search statistics
        """
        stats = self.search_stats.copy()

        if stats['total_searches'] > 0:
            stats['average_search_time'] = stats['total_search_time'] / stats['total_searches']
            stats['vector_search_ratio'] = stats['vector_searches'] / stats['total_searches']
        else:
            stats['average_search_time'] = 0.0
            stats['vector_search_ratio'] = 0.0

        # Include recovery manager statistics if available
        if self.recovery_manager:
            stats['recovery_stats'] = self.recovery_manager.get_statistics()

        return stats

    def log_search_statistics(self) -> None:
        """Log search handler statistics."""
        stats = self.get_search_statistics()

        self.console.print("[bold blue]Enhanced Search Statistics:[/bold blue]")
        self.console.print(f"Total Searches: {stats['total_searches']}")
        self.console.print(f"Vector Searches: {stats['vector_searches']}")
        self.console.print(f"Recovery Attempts: {stats['recovery_attempts']}")
        self.console.print(f"Recovery Successes: {stats['recovery_successes']}")
        self.console.print(f"Average Search Time: {stats['average_search_time']:.3f}s")
        self.console.print(f"Vector Search Ratio: {stats['vector_search_ratio']:.2%}")

        if 'recovery_stats' in stats:
            self.console.print("\n[bold green]Recovery Manager Statistics:[/bold green]")
            recovery_stats = stats['recovery_stats']
            self.console.print(f"Recovery Success Rate: {recovery_stats['success_rate']:.2%}")
            self.console.print(f"Embedding Generation Rate: {recovery_stats['embedding_generation_rate']:.2%}")

        self.logger.info(f"Enhanced search statistics: {stats}")
