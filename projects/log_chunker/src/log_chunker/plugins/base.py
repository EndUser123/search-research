"""Base plugin class and protocol."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from rich.console import Console

from ..config import ChunkingConfig
from ..data_models import ChunkInfo, LogEntry


class ChunkingPlugin(Protocol):
    """Protocol for chunking plugins"""

    name: str
    version: str
    dependencies: list[str]

    def initialize(self, config: ChunkingConfig, console: Console) -> bool:
        """Initialize plugin with config"""
        ...

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Find chunk boundaries"""
        ...

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score chunk quality (0-1)"""
        ...

    def cleanup(self) -> None:
        """Cleanup resources"""
        ...


class BaseChunkingPlugin(ABC):
    """Base class for chunking plugins"""

    def __init__(self):
        self.config: ChunkingConfig = None  # Will be set during initialize
        self.console: Console = None  # Will be set during initialize

    @abstractmethod
    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Abstract method to find chunk boundaries based on plugin's strategy."""
        pass

    @abstractmethod
    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """Perform a detailed analysis on the generated chunks.

        Returns:
            A dictionary containing structured analysis data.
            The keys of this dictionary should be unique to the plugin.
        """
        return {}

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """
        Default method to score chunk quality.
        Plugins should override this for specific scoring.
        """
        return 0.5  # Default neutral score

    def initialize(self, config: ChunkingConfig, console: Console) -> bool:
        """
        Initializes the plugin with the provided configuration and console.
        Returns True on successful initialization, False otherwise.
        """
        self.config = config
        self.console = console
        return True

    def cleanup(self) -> None:
        """Default cleanup method. Plugins can override for resource release."""
        pass
