"""Core chunking engine for processing log files."""


from rich.console import Console

from .config import ChunkingConfig
from .data_models import ChunkInfo, IntelligenceEngine, LogEntry
from .enhanced_progress import EnhancedDisplaySystem
from .plugin_manager import PluginManager
from .preprocessor import Preprocessor
from .reporter import Reporter


class ChunkingEngine:
    """Orchestrates the log chunking process."""

    def __init__(
        self,
        config: ChunkingConfig,
        console: Console,
        display_system: EnhancedDisplaySystem,
    ):
        self.config = config
        self.console = console
        self.display_system = display_system
        self.preprocessor = Preprocessor(
            config, console, self.display_system.progress_tracker.progress
        )
        self.plugin_manager = PluginManager(config, console)
        self.reporter = Reporter(console)

    def chunk_file(self, file_path: str, intelligence_engine: IntelligenceEngine):
        """Process a single log file and return chunks."""

        with self.display_system.track_preprocessing() as task_id:
            self.display_system.progress_tracker.update_task_description(
                task_id, "Reading and preprocessing file..."
            )
            _, log_entries, preprocessing_stats = self.preprocessor.process_file(
                file_path
            )
            self.display_system.progress_tracker.update_progress(task_id, 50)
            text = "\n".join([entry.message for entry in log_entries])
            self.display_system.progress_tracker.update_progress(task_id, 50)

        boundary_dict = self.plugin_manager.find_boundaries(text, log_entries)

        with self.display_system.track_chunk_creation(len(log_entries)) as task_id:
            self.display_system.progress_tracker.update_task_description(
                task_id, "Merging boundaries..."
            )
            merged_boundaries = self.plugin_manager.merge_boundaries(
                boundary_dict, log_entries
            )
            self.display_system.progress_tracker.update_progress(task_id, 50)
            final_chunks = self._create_chunks_from_boundaries(
                log_entries, merged_boundaries
            )
            self.display_system.progress_tracker.update_progress(task_id, 50)

        if final_chunks:
            with self.display_system.progress_tracker.track_operation(
                "Scoring Chunks", len(final_chunks)
            ) as task_id:
                self.plugin_manager.score_chunks(final_chunks)

        plugin_analysis_results = self.plugin_manager.run_analysis_plugins(final_chunks)
        intelligence_engine.set_plugin_analysis(plugin_analysis_results)

        return final_chunks, preprocessing_stats

    def _create_chunks_from_boundaries(
        self, log_entries: list[LogEntry], boundaries: list[int]
    ):
        """Create final chunks based on a list of boundary indices."""
        if not log_entries:
            return []

        chunk_boundaries = sorted(list(set(boundaries)))
        chunks = []
        start_index = 0
        chunk_id_counter = 0

        for boundary_index in chunk_boundaries:
            if boundary_index > start_index:
                chunk_entries = log_entries[start_index:boundary_index]
                chunk_text = "\n".join([entry.message for entry in chunk_entries])
                estimated_tokens = sum(
                    len(entry.message.split()) for entry in chunk_entries
                )
                chunk_info = ChunkInfo(
                    chunk_id=chunk_id_counter,
                    start_line=start_index,
                    end_line=boundary_index - 1,
                    estimated_tokens=estimated_tokens,
                )
                chunks.append((chunk_text, chunk_info))
                chunk_id_counter += 1
            start_index = boundary_index

        if start_index < len(log_entries):
            chunk_entries = log_entries[start_index:]
            chunk_text = "\n".join([entry.message for entry in chunk_entries])
            estimated_tokens = sum(
                len(entry.message.split()) for entry in chunk_entries
            )
            chunk_info = ChunkInfo(
                chunk_id=chunk_id_counter,
                start_line=start_index,
                end_line=len(log_entries) - 1,
                estimated_tokens=estimated_tokens,
            )
            chunks.append((chunk_text, chunk_info))

        return chunks
