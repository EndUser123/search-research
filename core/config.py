"""Centralized configuration for search-research plugin.

This module provides portable configuration with environment variable support
and graceful fallbacks for missing paths.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env files early so MCP subprocess picks up API keys.
# Keys set in the parent process are NOT inherited by child processes
# spawned by Claude Code's MCP client — this ensures web providers work.
for _env_path in [r"P:\.env", r"P:\__csf\.env"]:
    _p = Path(_env_path)
    if _p.exists():
        load_dotenv(_p, override=False)


class Config:
    """Centralized configuration with environment variable support."""

    # KG Backend
    DEFAULT_KG_PATH: str = os.getenv(
        "SEARCH_RESEARCH_KG_PATH", "P:/projects/kg_builder/knowledge_graph_output"
    )

    # CHS (Chat History) paths
    CHS_DB_PATH: str = os.getenv("SEARCH_RESEARCH_CHS_DB_PATH", "P:/.data/chat_history.db")
    CHS_INDEX_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_INDEX_PATH", "P:/__csf/data/chat_history_faiss_424k/faiss_index.bin"
    )
    CHS_STATE_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_STATE_PATH", "P:/__csf/data/chs_index_state.json"
    )

    # CKS (Constitutional Knowledge System) path
    CKS_DB_PATH: str = os.getenv("SEARCH_RESEARCH_CKS_DB_PATH", "P:/.data/cks.db")

    # Source code search paths
    SOURCE_ROOTS: list[str] = (
        os.getenv("SEARCH_RESEARCH_SOURCE_ROOTS", ".").split(os.pathsep)
        if os.getenv("SEARCH_RESEARCH_SOURCE_ROOTS")
        else ["."]
    )

    # Obsidian vault path for QMD wiki search
    OBSIDIAN_VAULT_PATH: str = os.getenv(
        "SEARCH_RESEARCH_OBSIDIAN_VAULT_PATH", "P:/wiki"
    )

    # Skills and commands directories
    SKILLS_DIR: str = os.getenv("SEARCH_RESEARCH_SKILLS_DIR", "P:/.claude/skills")
    COMMANDS_DIR: str = os.getenv("SEARCH_RESEARCH_COMMANDS_DIR", "P:/.claude/commands")

    # Web search providers (comma-separated list or environment variable)
    # Available providers: tavily, serper, exa, bing, brave, google, kagi, mojeek, you
    # Providers requiring API keys: tavily, serper, exa, bing, brave, google, kagi
    WEB_PROVIDERS: list[str] = (
        os.getenv("SEARCH_RESEARCH_WEB_PROVIDERS", "tavily,serper,exa").split(",")
        if os.getenv("SEARCH_RESEARCH_WEB_PROVIDERS")
        else ["tavily", "exa", "brave", "duckduckgo", "minimax"]
    )

    # Environment files
    ENV_FILES: list[str] = [
        os.getenv("SEARCH_RESEARCH_ENV_FILE", r"P:\.env"),
        os.getenv("SEARCH_RESEARCH_PROJECT_ENV", r"P:\__csf\.env"),
    ]

    @property
    def ENV_PATHS(self) -> list[str]:
        """Get environment file paths as list."""
        return self.ENV_FILES

    @classmethod
    def validate_path(cls, path_str: str, context: str = "") -> bool:
        """Validate that a path exists (or is a valid path string).

        Args:
            path_str: Path string to validate
            context: Context description for logging

        Returns:
            True if path exists or is valid, False otherwise
        """
        try:
            path = Path(path_str)
            if path.exists():
                return True

            # Path doesn't exist - log warning but don't fail
            context_msg = f" for {context}" if context else ""
            logger.warning(
                f"Path does not exist{context_msg}: {path_str}. "
                f"Related functionality may be limited."
            )
            return False
        except Exception as e:
            logger.error(f"Invalid path '{path_str}': {e}")
            return False

    @classmethod
    def get_validated_paths(cls, path_strs: list[str], context: str = "") -> list[Path]:
        """Get list of valid paths from a list of path strings.

        Args:
            path_strs: List of path strings to validate
            context: Context description for logging

        Returns:
            List of valid Path objects
        """
        valid_paths = []
        for path_str in path_strs:
            if cls.validate_path(path_str, context):
                valid_paths.append(Path(path_str))
        return valid_paths


# Singleton instance for path configuration
config = Config()

# Export for backward compatibility
__all__ = ["Config", "ResearchConfig", "config"]


# ResearchConfig for ResearchEngine (from old config.py)
# Merged from research_skill/config.py
from dataclasses import dataclass, field


@dataclass
class ResearchConfig:
    """Configuration for research operations.

    Provides environment variable overrides and sensible defaults
    for research engine parameters.
    """

    # Output paths
    OUTPUT_DIR: str = "P:/__csf/research_output"
    RESULT_FILE: str = "result.md"
    JSON_FILE: str = "result.json"

    # Search parameters
    MAX_RESULTS: int = 10
    MAX_FETCH_URLS: int = 5
    TIMEOUT: int = 30

    # Provider configuration
    PRIMARY_PROVIDER: str = "tavily"
    FALLBACK_PROVIDERS: list[str] = field(default_factory=lambda: ["exa", "serpapi"])

    # Saturation detection
    ENABLE_SATURATION: bool = True
    SIMILARITY_THRESHOLD: float = 0.85
    MIN_RESULTS_FOR_SATURATION: int = 5

    # HyDE (Hypothetical Document Embeddings)
    ENABLE_HYDE: bool = True
    HYDE_QUERIES_PER_RESULT: int = 3
    HYDE_MAX_QUERIES: int = 15

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = 60

    # Cache configuration
    ENABLE_CACHE: bool = True
    CACHE_TTL_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"

    @classmethod
    def from_env(cls) -> "ResearchConfig":
        """Create ResearchConfig from environment variables.

        Returns:
            ResearchConfig with environment variable overrides applied
        """
        return cls(
            OUTPUT_DIR=os.getenv("RESEARCH_OUTPUT_DIR", cls.OUTPUT_DIR),
            RESULT_FILE=os.getenv("RESEARCH_RESULT_FILE", cls.RESULT_FILE),
            JSON_FILE=os.getenv("RESEARCH_JSON_FILE", cls.JSON_FILE),
            MAX_RESULTS=int(os.getenv("RESEARCH_MAX_RESULTS", str(cls.MAX_RESULTS))),
            MAX_FETCH_URLS=int(os.getenv("RESEARCH_MAX_FETCH_URLS", str(cls.MAX_FETCH_URLS))),
            TIMEOUT=int(os.getenv("RESEARCH_TIMEOUT", str(cls.TIMEOUT))),
            PRIMARY_PROVIDER=os.getenv("RESEARCH_PRIMARY_PROVIDER", cls.PRIMARY_PROVIDER),
            ENABLE_SATURATION=os.getenv("RESEARCH_ENABLE_SATURATION", str(cls.ENABLE_SATURATION)) == "true",
            SIMILARITY_THRESHOLD=float(os.getenv("RESEARCH_SIMILARITY_THRESHOLD", str(cls.SIMILARITY_THRESHOLD))),
            MIN_RESULTS_FOR_SATURATION=int(os.getenv("RESEARCH_MIN_RESULTS_FOR_SATURATION", str(cls.MIN_RESULTS_FOR_SATURATION))),
            ENABLE_HYDE=os.getenv("RESEARCH_ENABLE_HYDE", str(cls.ENABLE_HYDE)) == "true",
            HYDE_QUERIES_PER_RESULT=int(os.getenv("RESEARCH_HYDE_QUERIES_PER_RESULT", str(cls.HYDE_QUERIES_PER_RESULT))),
            HYDE_MAX_QUERIES=int(os.getenv("RESEARCH_HYDE_MAX_QUERIES", str(cls.HYDE_MAX_QUERIES))),
            MAX_REQUESTS_PER_MINUTE=int(os.getenv("RESEARCH_MAX_REQUESTS_PER_MINUTE", str(cls.MAX_REQUESTS_PER_MINUTE))),
            ENABLE_CACHE=os.getenv("RESEARCH_ENABLE_CACHE", str(cls.ENABLE_CACHE)) == "true",
            CACHE_TTL_HOURS=int(os.getenv("RESEARCH_CACHE_TTL_HOURS", str(cls.CACHE_TTL_HOURS))),
            LOG_LEVEL=os.getenv("RESEARCH_LOG_LEVEL", cls.LOG_LEVEL),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of warnings.

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        if self.MAX_RESULTS < 1:
            warnings.append("MAX_RESULTS must be at least 1")

        if self.MAX_FETCH_URLS < 1:
            warnings.append("MAX_FETCH_URLS must be at least 1")

        if self.SIMILARITY_THRESHOLD < 0 or self.SIMILARITY_THRESHOLD > 1:
            warnings.append("SIMILARITY_THRESHOLD must be between 0 and 1")

        if self.MIN_RESULTS_FOR_SATURATION < 1:
            warnings.append("MIN_RESULTS_FOR_SATURATION must be at least 1")

        if self.HYDE_QUERIES_PER_RESULT < 1:
            warnings.append("HYDE_QUERIES_PER_RESULT must be at least 1")

        if self.HYDE_MAX_QUERIES < self.HYDE_QUERIES_PER_RESULT:
            warnings.append("HYDE_MAX_QUERIES must be >= HYDE_QUERIES_PER_RESULT")

        if self.MAX_REQUESTS_PER_MINUTE < 1:
            warnings.append("MAX_REQUESTS_PER_MINUTE must be at least 1")

        if self.CACHE_TTL_HOURS < 0:
            warnings.append("CACHE_TTL_HOURS must be non-negative")

        if self.PRIMARY_PROVIDER not in self.FALLBACK_PROVIDERS + [self.PRIMARY_PROVIDER]:
            warnings.append(f"PRIMARY_PROVIDER '{self.PRIMARY_PROVIDER}' not in known providers")

        return warnings


# Export research config for backward compatibility
research_config = ResearchConfig.from_env()
__all__.extend(["ResearchConfig", "research_config"])