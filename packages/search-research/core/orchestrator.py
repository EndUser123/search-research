# Migrated from research_skill/engine.py
"""Research engine orchestration."""

import asyncio
import time
from typing import Any

from .config import ResearchConfig
from .fetchers.batch import BatchURLFetcher
from .fetchers.validator import ContentSecurityValidator
from .hyde_engine import HyDEEngine
from .models import ResearchResult
from .processors.ensemble import HybridEnsembleConfig
from .query.expander import QueryExpander


class ResearchEngine:
    """Main orchestration class for research operations.

    The ResearchEngine coordinates search providers, query enhancement,
    and result synthesis for unified research across multiple backends.

    Attributes:
        config: The ResearchConfig instance for this engine.
        providers: Dictionary of registered search providers by name.
        hyde: The HyDEEngine for query enhancement.
        query_expander: The QueryExpander for query expansion.
        batch_fetcher: BatchURLFetcher for concurrent URL fetching.
        security_validator: ContentSecurityValidator for security checks.
        ensemble_processor: The HybridEnsembleConfig for ensemble methods.
    """

    def __init__(self, config: ResearchConfig | None = None):
        """Initialize ResearchEngine with optional config.

        Args:
            config: Optional ResearchConfig instance. Defaults to ResearchConfig()
                    if not provided.
        """
        self.config: ResearchConfig = config if config is not None else ResearchConfig()
        self.providers: dict[str, Any] = {}
        self.hyde = HyDEEngine(mode=self.config.hyde_mode)
        self.query_expander = QueryExpander()
        self.batch_fetcher = BatchURLFetcher()
        self.security_validator = ContentSecurityValidator()
        self.ensemble_processor = HybridEnsembleConfig()
        self._auto_register_providers()

    def _auto_register_providers(self) -> None:
        """Auto-register default providers from config."""
        from providers.claude import ClaudeProvider
        from providers.serper import SerperProvider
        from providers.tavily import TavilyProvider
        from providers.webreader import WebReaderProvider
        from providers.webreader_mcp import WebReaderMCPProvider

        # Map provider names to their classes
        provider_classes = {
            "tavily": TavilyProvider,
            "serper": SerperProvider,
            "webreader": WebReaderProvider,
            "claude": ClaudeProvider,
            "webreader_mcp": WebReaderMCPProvider,
        }

        for provider_name in self.config.default_providers:
            if provider_name in provider_classes:
                try:
                    provider_cls = provider_classes[provider_name]
                    # Initialize without API key (will read from env)
                    self.providers[provider_name] = provider_cls()
                except Exception:
                    # Skip if provider can't be initialized (e.g., missing API key)
                    pass

        # Register optional backends if enabled
        if self.config.enable_rlm:
            try:
                from .backends.rlm import RLMBackend

                rlm_backend = RLMBackend()
                # Register even if not available for testing purposes
                self.providers["rlm"] = rlm_backend
            except Exception:
                pass

        if self.config.enable_persona:
            try:
                from .backends.persona import PersonaMemoryBackend

                persona_backend = PersonaMemoryBackend()
                # Register even if not available for testing purposes
                self.providers["persona"] = persona_backend
            except Exception:
                pass

        if self.config.enable_kg:
            try:
                from .backends.kg import KGBackend

                kg_backend = KGBackend()
                self.providers["kg"] = kg_backend
            except Exception:
                pass

    def register_backend(self, backend: Any) -> None:
        """Register a custom backend.

        Args:
            backend: A backend object with search capability.
        """
        backend_name = getattr(backend, "BACKEND_NAME", None)
        if not backend_name or not isinstance(backend_name, str):
            backend_name = getattr(backend, "name", None)
        if not backend_name or not isinstance(backend_name, str):
            backend_name = "custom"
        self.providers[backend_name.lower()] = backend

    def register_provider(self, provider: Any) -> None:
        """Register a search provider.

        Args:
            provider: A search provider object with a 'name' attribute.
        """
        self.providers[provider.name] = provider

    async def _execute_provider_searches(self, query: str, **kwargs: Any) -> list:
        """Execute searches across all registered providers concurrently.

        Uses asyncio.gather() for concurrent execution, providing significant
        performance improvements when multiple providers are available.

        Args:
            query: The search query string.
            **kwargs: Additional search parameters.
                - timeout: Maximum time per provider in seconds (optional).

        Returns:
            List of search results from all providers.
        """
        # Extract timeout from kwargs (default: 5 seconds per provider)
        timeout = kwargs.pop("timeout", 5)

        # Create async tasks for each provider
        async def search_provider(provider: Any) -> list:
            """Execute search for a single provider with error handling.

            Args:
                provider: A search provider with a 'search' method.

            Returns:
                List of search results, or empty list on failure.
            """
            try:
                if hasattr(provider, "search"):
                    # Use asyncio.wait_for to enforce timeout per provider
                    return await asyncio.wait_for(provider.search(query, **kwargs), timeout=timeout)
            except (Exception, TimeoutError):
                # Partial failure: return empty list, continue with other providers
                return []
            return []

        # Execute all provider searches concurrently using asyncio.gather()
        provider_tasks = [
            search_provider(provider)
            for provider in self.providers.values()
            if hasattr(provider, "search")
        ]

        # gather() returns results in the same order as input tasks
        # return_exceptions=False would raise first exception, but we handle
        # exceptions inside each task for partial failure resilience
        all_results = await asyncio.gather(*provider_tasks, return_exceptions=False)

        # Flatten list of lists into single list of results
        results = []
        for provider_results in all_results:
            results.extend(provider_results)

        return results

    async def research(self, query: str, **kwargs: Any) -> ResearchResult:
        """Execute research query.

        Args:
            query: The search query string.
            **kwargs: Additional research parameters.
                - hyde_mode: Override HyDE mode for this query.
                - fetch_urls: Whether to fetch full URL content.

        Returns:
            ResearchResult with research findings.
        """
        start_time = time.time()

        # Get hyde_mode from kwargs or config
        hyde_mode = kwargs.get("hyde_mode", self.config.hyde_mode)
        _fetch_urls = kwargs.get("fetch_urls", True)  # Reserved for future use

        # Expand query if enabled
        expanded_queries = []
        if self.config.query_expansion_enabled:
            entity_slug = kwargs.get("entity_slug", None)
            max_variants = self.config.query_expansion_max_variants
            expanded_queries = self.query_expander.expand_query(
                query, entity_slug=entity_slug, max_variations=max_variants
            )

        # Enhance query using HyDE (with error handling)
        enhanced_query = None
        try:
            enhanced_query = await self.hyde.enhance_query(query)
        except Exception:
            # HyDE failed - continue with original query
            enhanced_query = None

        # Execute provider searches
        results = await self._execute_provider_searches(query, **kwargs)

        # Apply MMR reranking if enabled
        if self.config.enable_mmr_reranking and results:
            from .processors.reranking import maximal_marginal_relevance

            results = maximal_marginal_relevance(
                query, results, lambda_param=self.config.mmr_lambda
            )

        # Apply temporal boosting if enabled
        if self.config.temporal_boosting and results:
            from .processors.reranking import apply_temporal_boosting

            results = apply_temporal_boosting(
                results, half_life_days=self.config.temporal_half_life_days
            )

        # Build result
        processing_time = time.time() - start_time

        # Get enhanced query value (handle None case)
        enhanced_query_value = enhanced_query.enhanced if enhanced_query else None

        return ResearchResult(
            query=query,
            enhanced_query=enhanced_query_value,
            expanded_queries=expanded_queries,
            results=results,
            sources_used=list(self.providers.keys()),
            fetched_urls=0,
            vision_analysis=[],
            synthesis="",
            processing_time=processing_time,
            hyde_enabled=True,
            hyde_mode=hyde_mode,
            multi_hyde_enabled=self.config.multi_hyde_enabled,
            chapters_enabled=self.config.chapters_enabled,
            ensemble_enabled=self.config.enable_ensemble,
            ensemble_method=self.config.ensemble_method if self.config.enable_ensemble else None,
            metadata={},
        )
