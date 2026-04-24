# ADR-002: Optimal Architecture for search-research with Persistent Knowledge

**Status:** Accepted
**Date:** 2026-04-10
**Context:** Claude Code and QMD Persistent Knowledge Architecture insights
**Decision:** Hybrid compile-upfront + RAG architecture with advanced fusion

---

## Context

The current search-research package (UnifiedAsyncRouter) implements a progressive enhancement pattern:
- Fast local search (<1s)
- Quality-based web search fallback (5-10s)
- RRF fusion for result merging
- HyDE query enhancement

However, insights from the "Claude Code and QMD: Persistent Knowledge Architecture" notebook reveal advanced patterns not currently implemented:

1. **Compile-upfront knowledge compilation** (Karpathy's LLM Wiki pattern)
2. **Smart chunking with semantic boundaries** (not arbitrary token limits)
3. **AST-aware chunking for code** (tree-sitter based)
4. **Hybrid search with position-aware blending** (protects exact matches)
5. **Query expansion with LLM** (casts wider net)
6. **LLM cross-encoder re-ranking** (contextual relevance)
7. **Confidence scoring with decay** (knowledge lifecycle)
8. **Supersession logic** (version control for knowledge)
9. **Memory lifecycle pipeline** (working → episodic → semantic → procedural)
10. **Progressive disclosure search** (index-first navigation)

## Decision

Implement a **hybrid compile-upfront + RAG architecture** that combines the best of both approaches:

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPILED KNOWLEDGE LAYER                 │
│  (Persistent, pre-compiled wiki for high-signal topics)    │
│  - Smart chunked content (semantic boundaries)              │
│  - AST-aware code chunks (tree-sitter)                     │
│  - Typed relationships (@supports, @contradicts, etc.)     │
│  - Confidence scores with decay                            │
│  - Progressive disclosure (index → topic → article)        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  HYBRID SEARCH ENGINE                       │
│  - Query expansion (LLM-generated variants)                │
│  - Parallel BM25 + Vector + Graph traversal                │
│  - RRF fusion with position-aware blending                 │
│  - LLM cross-encoder re-ranking                            │
│  - Confidence-based ranking                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  MEMORY LIFECYCLE PIPELINE                  │
│  Working → Episodic → Semantic → Procedural                │
│  (Flush cycle: promote insights to compiled wiki)          │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: Smart Chunking Implementation

**Current Gap:** Arbitrary token limits break semantic units.

**Solution:** Implement semantic boundary detection with scored breakpoints.

```python
# core/chunking/smart_chunker.py

from enum import IntEnum
from typing import List, Tuple
import re

class BreakPointScore(IntEnum):
    """Semantic boundary scores for smart chunking."""
    H1 = 100          # Major section
    H2 = 90           # Subsection
    H3 = 80           # Sub-subsection
    CODE_FENCE = 80   # Code block boundary
    HORIZONTAL_RULE = 60
    BLANK_LINE = 20   # Paragraph boundary
    LIST_ITEM = 5
    LINE_BREAK = 1

class SmartChunker:
    """Split documents at semantic boundaries rather than arbitrary token limits.

    Uses distance-weighted scoring to find optimal break points within
    a target window, preserving semantic units (sections, code blocks).

    Target: ~900 tokens per chunk with 15% overlap
    """

    TARGET_TOKENS: int = 900
    OVERLAP_RATIO: float = 0.15
    SEARCH_WINDOW: int = 200  # Tokens before target to search for breaks

    def __init__(self, overlap: bool = True):
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        """Split text into semantically coherent chunks.

        Args:
            text: Input markdown or code

        Returns:
            List of text chunks with semantic boundaries preserved
        """
        # Find all break points with scores
        break_points = self._find_break_points(text)

        # Select optimal break points
        chunks = []
        position = 0
        chunk_id = 0

        while position < len(text):
            # Target end position for this chunk
            target_end = position + self.TARGET_TOKENS

            if target_end >= len(text):
                # Final chunk - take remaining text
                chunks.append(text[position:])
                break

            # Search window for optimal break point
            window_start = max(position, target_end - self.SEARCH_WINDOW)
            window_end = min(len(text), target_end + self.SEARCH_WINDOW)

            # Find highest-scoring break point in window
            best_break = self._find_best_break(
                break_points, window_start, window_end, target_end
            )

            # Extract chunk
            chunk_end = best_break if best_break > position else target_end
            chunks.append(text[position:chunk_end])

            # Calculate overlap for next chunk
            overlap_tokens = int(self.TARGET_TOKENS * self.OVERLAP_RATIO)
            position = chunk_end - overlap_tokens if self.overlap else chunk_end
            chunk_id += 1

        return chunks

    def _find_break_points(self, text: str) -> List[Tuple[int, int]]:
        """Find all semantic break points with scores.

        Returns:
            List of (position, score) tuples sorted by position
        """
        break_points = []

        # Markdown patterns
        patterns = [
            (r'^#\s+', BreakPointScore.H1),
            (r'^##\s+', BreakPointScore.H2),
            (r'^###\s+', BreakPointScore.H3),
            (r'^```\s*$', BreakPointScore.CODE_FENCE),
            (r'^---\s*$', BreakPointScore.HORIZONTAL_RULE),
            (r'^\s*$', BreakPointScore.BLANK_LINE),
            (r'^\s*[-*+]\s+', BreakPointScore.LIST_ITEM),
        ]

        for match, score in patterns:
            for m in re.finditer(match, text, re.MULTILINE):
                break_points.append((m.start(), score))

        # Sort by position
        break_points.sort(key=lambda x: x[0])
        return break_points

    def _find_best_break(
        self,
        break_points: List[Tuple[int, int]],
        window_start: int,
        window_end: int,
        target: int
    ) -> int:
        """Find best break point using distance-weighted scoring.

        Formula: finalScore = baseScore × (1 - (distance/window)² × 0.7)

        This gives preference to closer break points while still allowing
        a strong boundary (e.g., H1) 200 tokens back to beat a weak boundary
        at the target.

        Args:
            break_points: All break points with scores
            window_start: Start of search window
            window_end: End of search window
            target: Ideal target position

        Returns:
            Position of best break point
        """
        candidates = [
            (pos, score) for pos, score in break_points
            if window_start <= pos <= window_end
        ]

        if not candidates:
            return target

        best_pos = target
        best_score = 1  # Default: simple line break at target

        for pos, base_score in candidates:
            distance = abs(pos - target)
            window_size = window_end - window_start

            # Distance decay: squared distance penalty
            distance_penalty = (distance / window_size) ** 2
            decay_factor = 1 - (distance_penalty * 0.7)

            final_score = base_score * decay_factor

            if final_score > best_score:
                best_score = final_score
                best_pos = pos

        return best_pos
```

### Phase 2: AST-Aware Chunking for Code

**Current Gap:** Code chunked at arbitrary positions breaks functions/classes.

**Solution:** Use tree-sitter to parse code and break at AST boundaries.

```python
# core/chunking/ast_chunker.py

from typing import List, Optional
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

class ASTNodeScore(IntEnum):
    """AST node scores for code-aware chunking."""
    CLASS_INTERFACE_STRUCT = 100  # Top-level definitions
    FUNCTION_METHOD = 90         # Function/method boundaries
    TYPE_ALIAS_ENUM = 80         # Type definitions
    IMPORT_USE_DECLARATION = 60  # Import blocks

class ASTAwareChunker(SmartChunker):
    """Code-aware chunking using AST parsing.

    For supported languages (.py, .ts, .tsx, .js, .go, .rs), uses tree-sitter
    to break code at function, class, and import boundaries instead of
    arbitrary text positions.

    Falls back to SmartChunker for unsupported languages or if tree-sitter
    is not available.
    """

    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.js': 'javascript',
        '.jsx': 'jsx',
        '.go': 'go',
        '.rs': 'rust',
    }

    def __init__(self, file_path: Optional[str] = None, overlap: bool = True):
        super().__init__(overlap=overlap)
        self.file_path = file_path
        self._parser = None
        self._language = None

        if TREE_SITTER_AVAILABLE and file_path:
            self._init_parser(file_path)

    def _init_parser(self, file_path: str) -> None:
        """Initialize tree-sitter parser for the file type."""
        import os

        _, ext = os.path.splitext(file_path)

        if ext not in self.SUPPORTED_LANGUAGES:
            return

        try:
            lang_name = self.SUPPORTED_LANGUAGES[ext]
            self._language = Language(f'build/{lang_name}.so', lang_name)
            self._parser = Parser(self._language)
        except Exception as e:
            # Fall back to regex chunking
            pass

    def chunk(self, text: str) -> List[str]:
        """Chunk code using AST-aware boundaries if available.

        Args:
            text: Source code

        Returns:
            List of code chunks preserving function/class boundaries
        """
        if self._parser is None:
            # Fall back to regex-based smart chunking
            return super().chunk(text)

        # Parse AST and find break points
        ast_break_points = self._find_ast_break_points(text)

        # Combine AST breaks with regex breaks (AST scores take precedence)
        regex_breaks = self._find_break_points(text)

        # Merge break points (AST overrides regex for same position)
        break_map = {pos: score for pos, score in regex_breaks}
        for pos, score in ast_break_points:
            break_map[pos] = max(break_map.get(pos, 0), score)

        combined_breaks = sorted(break_map.items())

        # Use same chunking algorithm as SmartChunker but with combined breaks
        return self._chunk_with_breaks(text, combined_breaks)

    def _find_ast_break_points(self, code: str) -> List[Tuple[int, int]]:
        """Find break points at AST node boundaries.

        Returns:
            List of (position, score) tuples
        """
        if not self._parser:
            return []

        tree = self._parser.parse(bytes(code, 'utf8'))
        break_points = []

        def find_breaks(node, depth=0):
            """Recursively find breakable nodes."""
            node_type = node.type

            # Score based on node type
            score = 0
            if node_type in ('class_definition', 'interface_declaration',
                            'struct_declaration', 'impl_declaration'):
                score = ASTNodeScore.CLASS_INTERFACE_STRUCT
            elif node_type in ('function_definition', 'method_definition',
                              'async_function_definition'):
                score = ASTNodeScore.FUNCTION_METHOD
            elif node_type in ('type_alias_declaration', 'enum_declaration'):
                score = ASTNodeScore.TYPE_ALIAS_ENUM
            elif node_type in ('import_statement', 'import_from_statement',
                              'use_declaration'):
                score = ASTNodeScore.IMPORT_USE_DECLARATION

            if score > 0:
                break_points.append((node.start_byte, score))

            # Recurse into children
            for child in node.children:
                find_breaks(child, depth + 1)

        find_breaks(tree.root_node)
        return break_points

    def _chunk_with_breaks(
        self, text: str, break_points: List[Tuple[int, int]]
    ) -> List[str]:
        """Chunk using pre-computed break points."""
        chunks = []
        position = 0

        break_idx = 0

        while position < len(text):
            target_end = position + self.TARGET_TOKENS

            if target_end >= len(text):
                chunks.append(text[position:])
                break

            # Find best break in window
            window_start = max(position, target_end - self.SEARCH_WINDOW)

            best_pos = target_end
            best_score = 1

            while break_idx < len(break_points):
                pos, score = break_points[break_idx]

                if pos > target_end + self.SEARCH_WINDOW:
                    break  # Beyond search window

                if pos >= window_start:
                    distance = abs(pos - target_end)
                    window_size = self.SEARCH_WINDOW * 2
                    distance_penalty = (distance / window_size) ** 2
                    decay_factor = 1 - (distance_penalty * 0.7)
                    final_score = score * decay_factor

                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos

                break_idx += 1

            chunk_end = best_pos if best_pos > position else target_end
            chunks.append(text[position:chunk_end])

            overlap_tokens = int(self.TARGET_TOKENS * self.OVERLAP_RATIO)
            position = chunk_end - overlap_tokens if self.overlap else chunk_end

        return chunks
```

### Phase 3: Query Expansion with LLM

**Current Gap:** Single query searches may miss relevant results due to query phrasing.

**Solution:** Generate LLM query variants and search with all variants, merging results.

```python
# core/query/expansion.py

from dataclasses import dataclass
from typing import List
import asyncio

@dataclass
class QueryVariant:
    """A query variant with generation metadata."""
    variant: str
    weight: float = 1.0  # Weight for fusion (original = 2.0)
    source: str = "original"  # original, llm_expansion

class QueryExpander:
    """Generate query variants using LLM expansion.

    Casts a wider net by generating semantically similar queries.
    Original query gets 2x weight in RRF fusion to preserve exact matches.

    Uses local GGUF model (qmd-query-expansion-1.7B-q4_k_m) for privacy.
    """

    def __init__(self, enabled: bool = True, num_variants: int = 1):
        """Initialize query expander.

        Args:
            enabled: Whether to enable query expansion
            num_variants: Number of LLM-generated variants (default: 1)
        """
        self.enabled = enabled
        self.num_variants = num_variants
        self._llm = None  # Lazy-loaded local LLM

    async def expand(self, query: str) -> List[QueryVariant]:
        """Generate query variants.

        Args:
            query: Original query string

        Returns:
            List of query variants including original
        """
        variants = [
            QueryVariant(variant=query, weight=2.0, source="original")
        ]

        if not self.enabled:
            return variants

        # Generate LLM variants
        llm_variants = await self._generate_llm_variants(query)
        variants.extend(llm_variants)

        return variants

    async def _generate_llm_variants(self, query: str) -> List[QueryVariant]:
        """Generate LLM query variants.

        Prompt template:
        "Generate 1 alternative search query that would help find relevant
        information for: '{query}'. Return only the query text."

        Args:
            query: Original query

        Returns:
            List of generated query variants
        """
        # Implementation would use local GGUF model
        # For now, return rule-based variants as fallback
        return [
            QueryVariant(
                variant=f"{query} tutorial examples",
                weight=1.0,
                source="llm_expansion"
            )
        ]
```

### Phase 4: Hybrid Search with RRF + Position-Aware Blending

**Current Gap:** Current RRF treats all results equally, can dilute exact matches.

**Solution:** Implement position-aware blending that protects exact keyword matches.

```python
# core/search/hybrid_fusion.py

from typing import List, Dict
from dataclasses import dataclass
from ..models import SearchResult

@dataclass
class FusionConfig:
    """Configuration for hybrid search fusion."""
    rrf_k: int = 60
    top_rank_bonus: List[float] = (0.05, 0.02, 0.02)  # #1, #2-3, #4+
    position_blends: List[tuple] = (
        (0.75, 0.25),  # Ranks 1-3: 75% retrieval, 25% reranker
        (0.60, 0.40),  # Ranks 4-10: 60% retrieval, 40% reranker
        (0.40, 0.60),  # Ranks 11+: 40% retrieval, 60% reranker
    )

class HybridSearchEngine:
    """Hybrid search with BM25, vector, and LLM re-ranking.

    Implements QMD-style fusion:
    1. Query expansion (original + LLM variants)
    2. Parallel retrieval (BM25 + vector for each query variant)
    3. RRF fusion with top-rank bonus
    4. LLM re-ranking of top 30 candidates
    5. Position-aware blending (final scores)

    Position-aware blending protects exact keyword matches from being
    diluted by semantic search, while trusting reranker for long-tail.
    """

    def __init__(
        self,
        bm25_backend,  # FTS5 backend
        vector_backend,  # Vector similarity backend
        reranker_llm,  # Local LLM for re-ranking
        config: FusionConfig = FusionConfig()
    ):
        """Initialize hybrid search engine.

        Args:
            bm25_backend: Full-text search backend (BM25)
            vector_backend: Vector similarity backend
            reranker_llm: Local LLM for cross-encoder re-ranking
            config: Fusion configuration
        """
        self.bm25 = bm25_backend
        self.vector = vector_backend
        self.reranker = reranker_llm
        self.config = config

    async def search(
        self,
        query: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """Execute hybrid search with full fusion pipeline.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            Ranked list of search results
        """
        # Phase 1: Query expansion
        expander = QueryExpander(enabled=True)
        query_variants = await expander.expand(query)

        # Phase 2: Parallel retrieval for all query variants
        all_results = []

        for variant in query_variants:
            # BM25 search
            bm25_results = await self.bm25.search(variant.variant, limit=limit * 2)
            # Vector search
            vector_results = await self.vector.search(variant.variant, limit=limit * 2)

            # Tag results with query variant for fusion
            for r in bm25_results:
                r.metadata['query_variant'] = variant.variant
                r.metadata['variant_weight'] = variant.weight
                r.metadata['retrieval_method'] = 'bm25'
            for r in vector_results:
                r.metadata['query_variant'] = variant.variant
                r.metadata['variant_weight'] = variant.weight
                r.metadata['retrieval_method'] = 'vector'

            all_results.extend(bm25_results + vector_results)

        # Phase 3: RRF fusion with top-rank bonus
        fused = self._rrf_fusion(all_results)

        # Phase 4: LLM re-ranking of top 30
        top_candidates = fused[:30]
        reranked = await self._llm_rerank(query, top_candidates)

        # Phase 5: Position-aware blending
        final_results = self._position_aware_blend(
            fused[:limit],
            reranked[:limit]
        )

        return final_results[:limit]

    def _rrf_fusion(self, results: List[SearchResult]) -> List[SearchResult]:
        """Reciprocal Rank Fusion with top-rank bonus.

        Formula: score = Σ(weight / (k + rank + 1))

        Top-rank bonus: Documents ranking #1 for any variant get +0.05,
        #2-3 get +0.02. This prevents query expansion from diluting exact matches.

        Args:
            results: All retrieved results from all backends/variants

        Returns:
            Fused and ranked results
        """
        k = self.config.rrf_k
        scores: Dict[str, float] = {}
        ranks: Dict[str, int] = {}

        # Group by result ID and track best rank
        for i, result in enumerate(results):
            result_id = result.id

            # Track best rank (for top-rank bonus)
            if result_id not in ranks or i < ranks[result_id]:
                ranks[result_id] = i

            # Calculate RRF score
            variant_weight = result.metadata.get('variant_weight', 1.0)
            rrf_score = variant_weight / (k + i + 1)

            if result_id not in scores:
                scores[result_id] = 0
            scores[result_id] += rrf_score

        # Apply top-rank bonus
        for result_id, rank in ranks.items():
            bonus_idx = 0 if rank == 0 else (1 if rank < 3 else 2)
            if bonus_idx < len(self.config.top_rank_bonus):
                scores[result_id] += self.config.top_rank_bonus[bonus_idx]

        # Re-rank by fused score
        ranked = sorted(
            results,
            key=lambda r: scores.get(r.id, 0),
            reverse=True
        )

        # Update scores
        for result in ranked:
            result.score = scores.get(result.id, 0)

        return ranked

    async def _llm_rerank(
        self,
        query: str,
        candidates: List[SearchResult]
    ) -> List[SearchResult]:
        """LLM cross-encoder re-ranking.

        Uses local LLM to score each candidate on contextual relevance.
        Returns scores normalized to 0-1 range.

        Args:
            query: Original search query
            candidates: Top N candidates from RRF fusion

        Returns:
            Re-ranked candidates with updated scores
        """
        # Implementation would use local GGUF reranker model
        # (qwen3-reranker-0.6b-q8_0)

        # For now, return candidates unchanged
        return candidates

    def _position_aware_blend(
        self,
        retrieval_results: List[SearchResult],
        rerank_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Position-aware blending of retrieval and rerank scores.

        Blending ratio depends on RRF rank:
        - Ranks 1-3: 75% retrieval, 25% reranker (protects exact matches)
        - Ranks 4-10: 60% retrieval, 40% reranker
        - Ranks 11+: 40% retrieval, 60% reranker (trust reranker more)

        Args:
            retrieval_results: Results from RRF fusion (with scores)
            rerank_results: Results from LLM re-ranking (with scores)

        Returns:
            Blended results with final scores
        """
        # Build rerank score map
        rerank_scores = {
            r.id: r.score
            for r in rerank_results
        }

        blended = []

        for i, result in enumerate(retrieval_results):
            retrieval_score = result.score
            rerank_score = rerank_scores.get(result.id, 0.5)

            # Determine blend ratio based on rank
            if i < 3:
                blend = self.config.position_blends[0]
            elif i < 10:
                blend = self.config.position_blends[1]
            else:
                blend = self.config.position_blends[2]

            final_score = (
                blend[0] * retrieval_score +
                blend[1] * rerank_score
            )

            # Create new result with blended score
            result.score = final_score
            blended.append(result)

        return sorted(blended, key=lambda r: r.score, reverse=True)
```

### Phase 5: Confidence Scoring with Decay

**Current Gap:** All knowledge treated as equally valid forever. Stale information not deprioritized.

**Solution:** Implement confidence scoring with exponential decay and reinforcement.

```python
# core/knowledge/confidence.py

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import math

@dataclass
class ConfidenceMetadata:
    """Confidence metadata for knowledge items."""
    confidence: float              # Current confidence score [0, 1]
    source_count: int              # Number of supporting sources
    last_confirmed: datetime       # Last confirmation timestamp
    decay_constant: float = 0.0001 # Lambda (transient=high, structural=low)
    reinforcement_constant: float = 0.5 # K (how quickly confidence builds)

class ConfidenceScorer:
    """Confidence scoring with exponential decay and reinforcement.

    Formula: C = (1 - e^(-k*n)) * e^(-λ*t)

    Where:
    - n = number of confirming sources
    - k = reinforcement constant (how fast confidence builds)
    - t = time since last confirmation (seconds)
    - λ = decay constant (transient facts decay fast, structural slow)

    Each re-confirmation resets t to zero, reinforcing the memory.
    """

    def __init__(self):
        self._default_decay = {
            'transient': 0.001,    # Bugs, temporary issues (fast decay)
            'structural': 0.00001, # Architecture decisions (slow decay)
            'procedural': 0.0001,  # Workflows (medium decay)
        }

    def calculate(
        self,
        source_count: int,
        last_confirmed: datetime,
        fact_type: str = 'structural',
        custom_decay: Optional[float] = None,
        custom_reinforcement: Optional[float] = None
    ) -> float:
        """Calculate current confidence score.

        Args:
            source_count: Number of supporting sources
            last_confirmed: Last time this fact was confirmed
            fact_type: Type of fact (transient, structural, procedural)
            custom_decay: Custom decay constant (overrides fact_type)
            custom_reinforcement: Custom reinforcement constant

        Returns:
            Confidence score [0, 1]
        """
        k = custom_reinforcement or 0.5
        lam = custom_decay or self._default_decay.get(fact_type, 0.0001)

        # Time since last confirmation (seconds)
        t = (datetime.now(timezone.utc) - last_confirmed).total_seconds()

        # Confidence formula
        base_confidence = 1 - math.exp(-k * source_count)
        decay_factor = math.exp(-lam * t)

        return max(0.0, min(1.0, base_confidence * decay_factor))

    def reinforce(self, metadata: ConfidenceMetadata) -> ConfidenceMetadata:
        """Reinforce a memory by confirming it.

        Resets last_confirmed to now, which strengthens the memory.

        Args:
            metadata: Existing confidence metadata

        Returns:
            Updated metadata with reset timestamp
        """
        return ConfidenceMetadata(
            confidence=metadata.confidence,
            source_count=metadata.source_count + 1,
            last_confirmed=datetime.now(timezone.utc),
            decay_constant=metadata.decay_constant,
            reinforcement_constant=metadata.reinforcement_constant
        )
```

### Phase 6: Progressive Disclosure Search

**Current Gap:** All searches load all embeddings/indices - expensive for large corpora.

**Solution:** Index-first navigation that drills down progressively.

```python
# core/search/progressive_disclosure.py

from typing import List, Optional, Tuple
from pathlib import Path
from ..models import SearchResult

class ProgressiveDisclosureSearch:
    """Index-first search that drills down progressively.

    Instead of searching all embeddings, navigates a hierarchy:
    1. Read master index → identify relevant topic folders
    2. Read topic indexes → identify relevant articles
    3. Read specific articles → extract answer

    This is faster than vector search for large corpora and provides
    better context for the LLM.

    File structure:
    /wiki/
      index.md           # Master catalog of all topics
      topics/
        index.md         # Topic overview
        async-patterns.md
        fastapi-guide.md
      entities/
        index.md         # Entity catalog
        fastapi.md
        jwt.md
    """

    def __init__(self, wiki_root: Path):
        """Initialize progressive disclosure search.

        Args:
            wiki_root: Root of compiled knowledge wiki
        """
        self.wiki_root = Path(wiki_root)
        self.master_index = self.wiki_root / "index.md"

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """Progressive disclosure search.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Relevant search results with citations
        """
        # Phase 1: Read master index
        relevant_topics = await self._scan_master_index(query)

        # Phase 2: Read relevant topic indexes
        candidate_articles = []
        for topic_path in relevant_topics[:5]:  # Top 5 topics
            articles = await self._scan_topic_index(topic_path, query)
            candidate_articles.extend(articles)

        # Phase 3: Read and score candidate articles
        results = []
        for article_path in candidate_articles[:limit * 2]:
            article = await self._read_article(article_path)
            if article:
                score = self._score_relevance(query, article)
                if score > 0.3:  # Relevance threshold
                    results.append(SearchResult(
                        title=article['title'],
                        content=article['content'],
                        source='wiki',
                        score=score,
                        file_path=str(article_path)
                    ))

        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]

    async def _scan_master_index(self, query: str) -> List[Path]:
        """Scan master index for relevant topics.

        Args:
            query: Search query

        Returns:
            List of relevant topic index paths
        """
        # Read master index
        index_content = await self._read_file(self.master_index)
        if not index_content:
            return []

        # Simple keyword matching (could be enhanced with TF-IDF)
        topics = []
        for line in index_content.split('\n'):
            if query.lower() in line.lower():
                # Extract topic path from link syntax
                if '](' in line:
                    link_start = line.index('](') + 2
                    link_end = line.find(')', link_start)
                    if link_end > link_start:
                        topic_link = line[link_start:link_end]
                        topic_path = self.wiki_root / topic_link
                        if topic_path.exists():
                            topics.append(topic_path)

        return topics

    async def _scan_topic_index(
        self,
        topic_path: Path,
        query: str
    ) -> List[Path]:
        """Scan topic index for relevant articles.

        Args:
            topic_path: Path to topic index
            query: Search query

        Returns:
            List of relevant article paths
        """
        content = await self._read_file(topic_path)
        if not content:
            return []

        articles = []
        for line in content.split('\n'):
            if query.lower() in line.lower():
                if '](' in line:
                    link_start = line.index('](') + 2
                    link_end = line.find(')', link_start)
                    if link_end > link_start:
                        article_link = line[link_start:link_end]
                        # Resolve relative path
                        article_path = (topic_path.parent / article_link).resolve()
                        if article_path.exists():
                            articles.append(article_path)

        return articles

    async def _read_article(self, path: Path) -> Optional[dict]:
        """Read article and extract metadata.

        Args:
            path: Article file path

        Returns:
            Article dict with title, content, metadata
        """
        content = await self._read_file(path)
        if not content:
            return None

        # Extract title from first heading or filename
        title = path.stem
        for line in content.split('\n')[:5]:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        return {
            'title': title,
            'content': content,
            'path': path
        }

    async def _read_file(self, path: Path) -> Optional[str]:
        """Async file read.

        Args:
            path: File path

        Returns:
            File content or None if error
        """
        try:
            # Use asyncio.to_thread for blocking I/O
            import asyncio
            return await asyncio.to_thread(path.read_text, encoding='utf-8')
        except Exception:
            return None

    def _score_relevance(self, query: str, article: dict) -> float:
        """Score article relevance to query.

        Args:
            query: Search query
            article: Article dict

        Returns:
            Relevance score [0, 1]
        """
        content = article['content'].lower()
        query_lower = query.lower()

        # Simple keyword matching score
        query_words = set(query_lower.split())
        content_words = set(content.split())

        matches = query_words & content_words
        if not query_words:
            return 0.0

        return len(matches) / len(query_words)
```

---

## Implementation Phases

### Phase 1: Smart Chunking (Week 1-2)
- [ ] Implement SmartChunker with semantic boundary detection
- [ ] Implement ASTAwareChunker with tree-sitter integration
- [ ] Add tests for chunking quality (semantic unit preservation)
- [ ] Integrate into existing backends (CDS, Grep)

### Phase 2: Query Expansion & Fusion (Week 2-3)
- [ ] Implement QueryExpander with LLM variants
- [ ] Implement HybridSearchEngine with RRF + position-aware blending
- [ ] Add local LLM integration (GGUF models)
- [ ] Benchmark fusion quality vs baseline

### Phase 3: Confidence & Memory (Week 3-4)
- [ ] Implement ConfidenceScorer with decay
- [ ] Add confidence metadata to SearchResult
- [ ] Implement progressive disclosure search
- [ ] Add memory lifecycle pipeline (flush cycle)

### Phase 4: Integration & Testing (Week 4-5)
- [ ] Integrate all phases into UnifiedAsyncRouter
- [ ] Add end-to-end tests
- [ ] Performance benchmarking
- [ ] Documentation updates

---

## Alternatives Considered

### Alternative 1: Pure RAG (No Compilation)
**Pros:** Simpler, always fresh data
**Cons:** Stateless amnesia, no knowledge accumulation, slower queries

### Alternative 2: Pure Compilation (No RAG)
**Pros:** Fast queries, knowledge accumulates
**Cons:** Stale data, expensive recompilation, poor for fresh content

### Alternative 3: External Vector DB (Pinecone, Weaviate)
**Pros:** Managed service, scalable
**Cons:** External dependency, privacy concerns, cost

**Decision:** Hybrid compile-upfront + RAG provides best of both worlds while maintaining local-only operation for privacy.

---

## Consequences

### Positive
- **Faster queries:** Progressive disclosure avoids loading all embeddings
- **Better relevance:** Position-aware blending protects exact matches
- **Knowledge accumulation:** Compiled wiki grows with use
- **Stale resilience:** Confidence scoring deprioritizes old information

### Negative
- **Complexity:** More moving parts (chunking, expansion, fusion, confidence)
- **Storage overhead:** Compiled wiki + raw sources + embeddings
- **Recompilation cost:** Need to re-chunk when sources change

### Mitigation
- Phased implementation allows incremental value delivery
- Lazy compilation (compile on first access) reduces upfront cost
- Configurable quality/speed trade-offs

---

## References

- Karpathy, A. (2025). "LLM Wiki" pattern - compile-upfront vs stateless RAG
- QMD (Query Markup Documents) - Hybrid search engine design
- NotebookLM documentation - Progressive disclosure search
- search-research ARCHITECTURE.md - Current architecture baseline

---

**Document Control**

- **Author:** /arch (AI Architecture Advisor)
- **Status:** Accepted
- **Next Review:** After Phase 1 completion
- **Related:** ADR-001 (Async-first approach)
