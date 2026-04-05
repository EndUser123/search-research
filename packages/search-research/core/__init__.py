"""
search-research: Unified search and research package.

Provides fast local search (<1s) and comprehensive web search (5-10s)
with intelligent routing and unified async API.

Example:
    import asyncio
    from search_research import AsyncSearchRouter, UnifiedAsyncRouter

    # Fast local search (FAST mode)
    async def fast_search():
        router = AsyncSearchRouter()
        results = await router.search_async("FastAPI patterns")  # <1s
        return results

    # Comprehensive unified search (auto mode with web fallback)
    async def comprehensive_search():
        router = UnifiedAsyncRouter()
        results = await router.search_async("FastAPI best practices")  # 5-10s
        return results

    # Run async search
    results = asyncio.run(fast_search())
"""

__version__ = "0.1.0"

# Backends
# Analysis & Quality Components
from .analysis import (
    Contradiction,
    ContradictionDetector,
    CoverageGap,
    DensityCalculator,
    GapAnalyzer,
    GapType,
    NoveltyTracker,
    TopicClusterer,
    TopicSignature,
)
from .backends import (
    BACKEND_KG,
    BACKEND_NAME,
    BACKEND_PERSONA,
    KGBackend,
    PersonaMemoryBackend,
    RLMBackend,
    SecurityError,
)

# Security Components (migrated from chat_search_security)
from .chat_search_security import (
    ChatSearchSecurityManager,
    InputValidator,
    RateLimiter,
    ResourceMonitor,
    SecurityEvent,
    SecurityEventType,
    SecurityLevel,
    SecurityMonitor,
)
from .config import ResearchConfig

# Enhancement Components
from .enhancement import (
    ExecutionStatus,
    LearningSystem,
    ModeCombination,
    ModeExecutionResult,
    ModeRelationshipMapper,
    MultiModeOrchestrator,
    OptimizationResult,
    OrchestratedResult,
    PatternInsight,
    QualityPredictor,
    QueryDependencies,
    ResearchDepth,
    ResearchFeedback,
    ResearchMode,
    SimplifiedDependencyAnalyzer,
)
from .hybrid_ensemble import (
    EnsembleResult,
    HybridEnsembleConfig,
    SearchResult,
    run_hybrid_ensemble,
)
from .hyde import apply_hyde, enhance_query, extract_key_phrases
from .hyde_chapters import HydeChapter, HydeChapterConfig, generate_hyde_chapters
from .hyde_chapters_comprehensive import (
    HydeChapter as HydeChapterComprehensive,
)
from .hyde_chapters_comprehensive import (
    HydeChapterConfig as HydeChapterConfigComprehensive,
)
from .hyde_chapters_comprehensive import (
    generate_hyde_chapters as generate_hyde_chapters_comprehensive,
)
from .hyde_multi_perspective import (
    HypotheticalDocument,
    MultiHyDEConfig,
    MultiHypotheticalDocuments,
    generate_multi_hypothetical_documents,
)
from .hyde_multi_perspective_comprehensive import (
    MultiHyDEConfig as MultiHyDEConfigComprehensive,
)
from .hyde_multi_perspective_comprehensive import (
    MultiHypotheticalDocuments as MultiHypotheticalDocumentsComprehensive,
)
from .hyde_multi_perspective_comprehensive import (
    generate_multi_hypothetical_documents as generate_multi_hypothetical_documents_comprehensive,
)
from .hyde_retrieval import (
    HyDERetrievalConfig,
    HyDERetrievalResult,
    extract_retrieval_query,
    search_with_hyde,
)
from .hyde_single import (
    HyDEConfig,
    create_hypothetical_document,
    generate_hypothetical_document,
)
from .hyde_single import (
    HypotheticalDocument as HypotheticalDocumentSingle,
)
from .models import EnhancedQuery, ResearchResult
from .models import SearchResult as SearchResultV2
from .modes import Mode

# Orchestration Components
from .orchestration import CostTracker, PhaseController, PhaseResult
from .orchestrator import ResearchEngine

# Processing Components
from .processing import NormalizedResult as ProcessingResult
from .processing import ResultNormalizer, SourceType
from .quality_checker import QualityConfig, is_satisfactory
from .query import (
    QueryExpander,
    expand_query_if_enabled,
    get_abbreviation_mappings,
    get_query_suggestions,
    get_synonym_mappings,
)
from .result_merger import FusedResult
from .result_merger import reciprocal_rank_fusion as reciprocal_rank_fusion_merger
from .result_normalizer import NormalizedResult, normalize_result
from .results import (
    DeduplicationProcessor,
    RankingProcessor,
    ResultProcessingPipeline,
    SynthesisProcessor,
    apply_temporal_boosting,
    calculate_temporal_boost,
    maximal_marginal_relevance,
    reciprocal_rank_fusion,
    weighted_average_fusion,
)
from .results import (
    EnsembleResult as EnsembleResultV2,
)
from .results import (
    HybridEnsembleConfig as HybridEnsembleConfigV2,
)
from .results import (
    run_hybrid_ensemble as run_hybrid_ensemble_v2,
)
from .router_async import AsyncSearchRouter, create_async_router
from .unified_router import UnifiedAsyncRouter

# Compatibility aliases for migration from legacy routers
UnifiedRouter = UnifiedAsyncRouter  # Alias for backward compatibility
SearchRouter = UnifiedAsyncRouter  # Alias for backward compatibility

__all__ = [
    "AsyncSearchRouter",
    "UnifiedAsyncRouter",
    "UnifiedRouter",  # Compatibility alias
    "SearchRouter",  # Compatibility alias
    "SearchResult",
    "create_async_router",
    "Mode",
    "__version__",
    # Backends
    "BACKEND_KG",
    "BACKEND_NAME",
    "BACKEND_PERSONA",
    "KGBackend",
    "PersonaMemoryBackend",
    "RLMBackend",
    "SecurityError",
    # Core research engine
    "ResearchEngine",
    "ResearchConfig",
    "ResearchResult",
    "EnhancedQuery",
    "SearchResultV2",
    # HyDE core functions
    "apply_hyde",
    "extract_key_phrases",
    "enhance_query",
    # HyDE multi-chapter (simple)
    "HydeChapter",
    "HydeChapterConfig",
    "generate_hyde_chapters",
    # HyDE multi-chapter (comprehensive)
    "HydeChapterComprehensive",
    "HydeChapterConfigComprehensive",
    "generate_hyde_chapters_comprehensive",
    # HyDE multi-perspective (simple)
    "HypotheticalDocument",
    "MultiHyDEConfig",
    "MultiHypotheticalDocuments",
    "generate_multi_hypothetical_documents",
    # HyDE multi-perspective (comprehensive)
    "MultiHyDEConfigComprehensive",
    "MultiHypotheticalDocumentsComprehensive",
    "generate_multi_hypothetical_documents_comprehensive",
    # HyDE single document
    "HypotheticalDocumentSingle",
    "HyDEConfig",
    "create_hypothetical_document",
    "generate_hypothetical_document",
    # HyDE retrieval
    "HyDERetrievalConfig",
    "HyDERetrievalResult",
    "extract_retrieval_query",
    "search_with_hyde",
    # Hybrid ensemble
    "HybridEnsembleConfig",
    "SearchResult",
    "EnsembleResult",
    "run_hybrid_ensemble",
    # Query processing
    "NormalizedResult",
    "normalize_result",
    "FusedResult",
    "reciprocal_rank_fusion_merger",
    "ProcessingResult",
    "ResultNormalizer",
    "SourceType",
    "QualityConfig",
    "is_satisfactory",
    "QueryExpander",
    "expand_query_if_enabled",
    "get_query_suggestions",
    "get_synonym_mappings",
    "get_abbreviation_mappings",
    # Results processing
    "DeduplicationProcessor",
    "RankingProcessor",
    "SynthesisProcessor",
    "ResultProcessingPipeline",
    "maximal_marginal_relevance",
    "apply_temporal_boosting",
    "calculate_temporal_boost",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "EnsembleResultV2",
    "HybridEnsembleConfigV2",
    "run_hybrid_ensemble_v2",
    # Analysis & Quality Components
    "GapAnalyzer",
    "CoverageGap",
    "GapType",
    "ContradictionDetector",
    "Contradiction",
    "DensityCalculator",
    "TopicClusterer",
    "TopicSignature",
    "NoveltyTracker",
    # Orchestration Components
    "PhaseController",
    "PhaseResult",
    "CostTracker",
    # Enhancement Components
    "SimplifiedDependencyAnalyzer",
    "QueryDependencies",
    "ResearchDepth",
    "LearningSystem",
    "PatternInsight",
    "ResearchFeedback",
    "ModeRelationshipMapper",
    "ResearchMode",
    "ModeCombination",
    "MultiModeOrchestrator",
    "ExecutionStatus",
    "ModeExecutionResult",
    "OrchestratedResult",
    "QualityPredictor",
    "OptimizationResult",
    # Security Components (migrated from chat_search_security)
    "ChatSearchSecurityManager",
    "InputValidator",
    "RateLimiter",
    "ResourceMonitor",
    "SecurityEvent",
    "SecurityEventType",
    "SecurityLevel",
    "SecurityMonitor",
]
