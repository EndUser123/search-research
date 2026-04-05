"""Plugin template generation utilities."""

from pathlib import Path

try:
    from rich import print as rprint
except ImportError:
    rprint = print


def create_plugin_template(plugin_name: str, output_dir: str | None = None) -> Path:
    """Create a template for a new plugin.

    Args:
        plugin_name: Name of the plugin to create
        output_dir: Optional directory to save the plugin (defaults to current dir)

    Returns:
        Path to the created plugin file
    """
    # Sanitize plugin name for class and file naming
    safe_plugin_name = "".join(c for c in plugin_name.title() if c.isalnum())

    template = f'''#!/usr/bin/env python
"""
Custom Chunking Plugin: {plugin_name}
"""

from typing import List
from .plugins.base import BaseChunkingPlugin
from .data_models import LogEntry, ChunkInfo
from .config import ChunkingConfig
from rich.console import Console


class {safe_plugin_name}Plugin(BaseChunkingPlugin):
    """Custom chunking plugin: {plugin_name}"""

    name = "{plugin_name.lower()}"
    version = "1.0.0"
    dependencies = []  # List any required pip packages (e.g., ["tensorflow", "spacy"])

    def initialize(self, config: ChunkingConfig, console: Console) -> bool:
        """
        Initialize plugin with configuration and console.
        This method is called once when the plugin is loaded.
        Perform expensive setup (e.g., model loading) here.
        Return False if initialization fails (e.g., missing dependencies).
        """
        # Call the base class initializer
        super().initialize(config, console)

        self.console.log(f"[bold green]Initializing {{self.name}} plugin...[/bold green]")

        try:
            # --- Add your plugin-specific initialization logic here ---
            # Access configuration: self.config.my_setting
            # Log messages: self.console.log('...') or logger.info('...')

            # Example: Load a custom model (if external dependency is installed)
            # if "my_model_lib" in self.dependencies:
            #     try:
            #         import my_model_lib
            #         self.custom_model = my_model_lib.load(self.config.my_custom_model_path)
            #     except ImportError:
            #         self.console.log("[yellow]Warning: MyModelLib not installed.[/yellow]")
            #         return False

            self.console.log(f"[bold green]{{self.name}} plugin initialized successfully.[/bold green]")
            return True
        except Exception as e:
            self.console.log(f"[bold red]Error initializing {{self.name}} plugin: {{e}}[/bold red]")
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Exception during {{self.name}} plugin initialization:")
            return False

    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """
        Find chunk boundaries in the log entries.

        This method is called for each log file.

        Args:
            text (str): The full preprocessed log text.
            log_entries (List[LogEntry]): A list of parsed LogEntry objects.

        Returns:
            List[int]: A list of line indices (0-based) where new chunks should start.
                       These indices refer to `log_entries` and `text.split('\\\\n')`.
                       For example, [0, 10, 25] means chunks start at line 0, 10, and 25.
        """
        boundaries = []

        self.console.log(f"[dim]Running {{self.name}} boundary detection...[/dim]")

        # --- Add your boundary detection logic here ---
        # Example: Simple boundary every 100 lines (for demonstration)
        # for i in range(0, len(log_entries), 100):
        #    if i != 0:  # Don't add 0 if it's not explicitly a boundary from this plugin
        #        boundaries.append(i)

        # Example: Boundary when a specific keyword appears
        # for i, entry in enumerate(log_entries):
        #     if "CRITICAL ERROR" in entry.message:
        #         boundaries.append(i)

        self.console.log(f"[dim]{{self.name}} found {{len(boundaries)}} boundaries.[/dim]")
        return sorted(list(set(boundaries)))  # Ensure boundaries are unique and sorted

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """
        Score the quality of a given chunk (0.0 to 1.0).
        Higher scores indicate better quality (e.g., more coherent, less noise).

        Args:
            chunk (str): The raw text content of the chunk.
            info (ChunkInfo): Metadata about the chunk.

        Returns:
            float: A score between 0.0 and 1.0.
        """
        # --- Add your chunk scoring logic here ---
        # Example: Score based on number of lines
        # score = min(1.0, info.original_lines / self.config.target_lines_per_chunk)

        # Example: Score based on presence of certain patterns
        # if "error_start" in info.detected_patterns:
        #     score = 0.2  # Lower score for error-only chunks perhaps
        # else:
        #     score = 0.8

        return 0.5  # Default neutral score if no specific logic

    def cleanup(self) -> None:
        """
        Cleanup any resources used by the plugin (e.g., close model connections, free memory).
        This method is called when the framework shuts down.
        """
        self.console.log(f"[dim]Cleaning up {{self.name}} plugin resources...[/dim]")
        # --- Add cleanup logic here if needed ---
        # if hasattr(self, 'custom_model') and self.custom_model:
        #    del self.custom_model
        #    import torch; torch.cuda.empty_cache()  # If using PyTorch
        pass
'''

    # Determine output path
    filename = f"{plugin_name.lower()}_plugin.py"
    if output_dir:
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(filename)

    # Write the template
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)
        rprint(f"Plugin template created: [bold green]{output_path}[/bold green]")
        rprint(
            f"Edit the file and use with: [cyan]python log_chunker.py logs.txt --plugin {output_path}[/cyan]"
        )
        return output_path
    except OSError as e:
        rprint(
            f"[bold red]Error: Failed to write plugin template to {output_path}: {e}[/bold red]"
        )
        raise
