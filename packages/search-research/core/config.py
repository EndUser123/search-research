"""Centralized configuration for search-research plugin.

This module provides portable configuration with environment variable support
and graceful fallbacks for missing paths.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration with environment variable support."""

    # KG Backend
    DEFAULT_KG_PATH: str = os.getenv(
        "SEARCH_RESEARCH_KG_PATH", "P:/projects/kg_builder/knowledge_graph_output"
    )

    # CHS (Chat History) paths
    CHS_DB_PATH: str = os.getenv("SEARCH_RESEARCH_CHS_DB_PATH", "P:/__csf/data/chat_history.db")
    CHS_INDEX_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_INDEX_PATH", "P:/__csf/data/chat_history_faiss_424k/faiss_index.bin"
    )
    CHS_STATE_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_STATE_PATH", "P:/__csf/data/chs_index_state.json"
    )

    # CKS (Constitutional Knowledge System) path
    CKS_DB_PATH: str = os.getenv("SEARCH_RESEARCH_CKS_DB_PATH", "P:/__csf/data/cks.db")

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
        else ["tavily", "serper", "exa", "brave"]
    )

    # Environment files
    ENV_FILES: list[str] = [
        os.getenv("SEARCH_RESEARCH_ENV_FILE", "P:/.env"),
        os.getenv("SEARCH_RESEARCH_PROJECT_ENV", "P:/__csf/.env"),
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
    """Configuration for ResearchEngine.

    Attributes:
        default_providers: List of default search provider names.
        fallback_providers: List of fallback provider names when defaults fail.
        hyde_enabled: Whether Hypothetical Document Embeddings is enabled.
        hyde_mode: The HyDE mode to use (e.g., "confidence", "multi-gen").
        fetch_urls_enabled: Whether to fetch full content from result URLs.
        max_urls_to_fetch: Maximum number of URLs to fetch content from.
        multi_hyde_enabled: Whether multi-HyDE (multiple perspectives) is enabled.
        multi_hyde_perspectives: List of perspectives for multi-HyDE.
        chapters_enabled: Whether chapter-based research is enabled.
        chapters_num: Number of chapters to generate.
        chapters_detail_level: Detail level for chapters (low, medium, high).
        query_expansion_enabled: Whether query expansion is enabled.
        query_expansion_max_variants: Maximum number of query variants to generate.
        auto_learning_enabled: Whether auto-learning from results is enabled.
        enable_ensemble: Whether ensemble methods are enabled.
        ensemble_method: The ensemble method to use.
        enable_mmr_reranking: Whether MMR (Maximal Marginal Relevance) reranking is enabled.
        mmr_lambda: The lambda parameter for MMR (0=relevance, 1=diversity).
        temporal_boosting: Whether temporal boosting is enabled.
        temporal_half_life_days: Half-life in days for temporal decay.
        enable_rlm: Whether RLM (Recursive Language Model) backend is enabled.
        enable_persona: Whether Persona Memory backend is enabled.
        enable_kg: Whether Knowledge Graph backend is enabled.
        using_default_providers: Whether using default websearch/webfetch providers (tavily/serper) instead of claude.
    """

    default_providers: list[str] = field(default_factory=lambda: ["claude", "tavily", "serper"])
    fallback_providers: list[str] = field(default_factory=lambda: ["glm"])
    hyde_enabled: bool = True
    hyde_mode: str = "confidence"
    fetch_urls_enabled: bool = True
    max_urls_to_fetch: int = 5
    multi_hyde_enabled: bool = False
    multi_hyde_perspectives: list[str] | None = None
    chapters_enabled: bool = False
    chapters_num: int = 3
    chapters_detail_level: str = "medium"
    query_expansion_enabled: bool = True
    query_expansion_max_variants: int = 5
    auto_learning_enabled: bool = True
    enable_ensemble: bool = False
    ensemble_method: str = "reciprocal_rank_fusion"
    enable_mmr_reranking: bool = True
    mmr_lambda: float = 0.5
    temporal_boosting: bool = False
    temporal_half_life_days: int = 180
    enable_rlm: bool = False
    enable_persona: bool = False
    enable_kg: bool = False

    # Check if using default websearch/webfetch providers
    using_default_providers: bool = False

    # Two-phase research with novelty-based saturation
    enable_two_phase: bool = False
    budget: float = 1.0
    max_iterations: int = 5
    novelty_threshold: float = 0.05
    results_per_iteration: int = 20

    def __post_init__(self):
        """Handle None and string values for multi_hyde_perspectives."""
        if self.multi_hyde_perspectives is None:
            self.multi_hyde_perspectives = []
        elif isinstance(self.multi_hyde_perspectives, str):
            # Handle both empty string and comma-separated values
            if self.multi_hyde_perspectives == "":
                self.multi_hyde_perspectives = []
            else:
                self.multi_hyde_perspectives = self.multi_hyde_perspectives.split(",")

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues.

        Returns:
            A list of validation issue strings. Empty list indicates valid config.
        """
        issues: list[str] = []

        # Validate provider lists are non-empty
        if not self.default_providers:
            issues.append("default_providers cannot be empty")
        if not self.fallback_providers:
            issues.append("fallback_providers cannot be empty")

        # Validate hyde_mode
        valid_hyde_modes = {"confidence", "multi-gen"}
        if self.hyde_mode not in valid_hyde_modes:
            issues.append(f"hyde_mode must be one of {valid_hyde_modes}, got '{self.hyde_mode}'")

        # Validate numeric bounds
        if self.budget < 0:
            issues.append(f"budget must be >= 0, got {self.budget}")
        if self.max_iterations <= 0:
            issues.append(f"max_iterations must be > 0, got {self.max_iterations}")
        if not 0 < self.novelty_threshold <= 1:
            issues.append(f"novelty_threshold must be in (0, 1], got {self.novelty_threshold}")
        if self.results_per_iteration <= 0:
            issues.append(f"results_per_iteration must be > 0, got {self.results_per_iteration}")
        if not 0 <= self.mmr_lambda <= 1:
            issues.append(f"mmr_lambda must be in [0, 1], got {self.mmr_lambda}")
        if self.max_urls_to_fetch < 0:
            issues.append(f"max_urls_to_fetch must be >= 0, got {self.max_urls_to_fetch}")

        # Validate enum-like fields
        valid_detail_levels = {"low", "medium", "high"}
        if self.chapters_detail_level not in valid_detail_levels:
            issues.append(
                f"chapters_detail_level must be one of {valid_detail_levels}, "
                f"got '{self.chapters_detail_level}'"
            )

        # Validate ensemble_method
        valid_ensemble_methods = {"reciprocal_rank_fusion", "weighted_average"}
        if self.ensemble_method not in valid_ensemble_methods:
            issues.append(
                f"ensemble_method must be one of {valid_ensemble_methods}, "
                f"got '{self.ensemble_method}'"
            )

        return issues
