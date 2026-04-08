"""Temporary script to execute /all skill search."""
import asyncio
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))
skills_path = Path(__file__).parent
sys.path.insert(0, str(skills_path))
try:
    from search_research import UnifiedAsyncRouter
    from search_research.quality_checker import QualityConfig
    print('✓ Successfully imported search_research modules')
except ImportError as e:
    print(f'✗ Failed to import search_research: {e}')
    sys.exit(1)
try:
    import adaptive_limits
    import query_complexity
    import search_executor
    import semantic_cluster
    print('✓ Successfully imported Layer 1 enhancements')
except ImportError as e:
    print(f'✗ Failed to import Layer 1 enhancements: {e}')
    sys.exit(1)
try:
    import agent_filter
    import layer2_filter
    print('✓ Successfully imported Layer 2 filtering')
except ImportError as e:
    print(f'✗ Failed to import Layer 2 filtering: {e}')
    sys.exit(1)

async def execute_search():
    """Execute the search query."""
    query = 'please find all the claude.md files we have.'
    print('\n=== Executing Universal Search ===')
    print(f'Query: {query}\n')
    mode = 'local-only'
    limit = 50
    rrf_k = 60
    min_score = 0.3
    min_results = 1
    context_threshold = 20
    force_context_filter = False
    no_context_filter = True
    quality_config = QualityConfig(min_score=min_score, min_results=min_results, require_content_match=False)
    print(f"[Layer 1A] Searching for '{query}' (mode: {mode}, limit: {limit})")
    complexity_score = query_complexity.calculate_complexity_score(query)
    adaptive_limit = adaptive_limits.get_adaptive_limit(complexity_score)
    print(f'[Layer 1C] Query complexity: {complexity_score}/100 ({query_complexity.get_complexity_label(complexity_score)})')
    print(f'[Layer 1D] Adaptive limit: {adaptive_limit} (base: {limit})')
    results = await search_executor.execute_search(query=query, mode=mode, limit=adaptive_limit, rrf_k=rrf_k, quality_config=quality_config)
    print(f'[Layer 1A] → {len(results)} results')
    if not results:
        print('\n=== No Results Found ===')
        return
    print('\n=== Search Results ===\n')
    for i, result in enumerate(results[:20], 0):
        score = getattr(result, 'score', 0.0)
        title = getattr(result, 'title', 'Untitled')
        source = getattr(result, 'source', 'UNKNOWN')
        url = getattr(result, 'url', '')
        content = getattr(result, 'content', '')[:200]
        print(f'[{score:.2f}] {source}: {title}')
        if url:
            print(f'    URL: {url}')
        print(f'    Preview: {content}...')
        print()
if __name__ == '__main__':
    asyncio.run(execute_search())
