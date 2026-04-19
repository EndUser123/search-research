"""Per-backend test to verify each backend produces ≥1 result.

Run: pytest tests/test_all_backends.py -v
"""

import pytest

from dotenv import load_dotenv

# Load .env so API keys are available when running pytest directly
load_dotenv()

from search_research import AsyncSearchRouter

BACKEND_QUERIES = {
    "cds": "async def",
    "cks": "router",
    "claude-history": "import asyncio",
    "grep": "class AsyncSearchRouter",
    "kg": "rag",
    "ast_code": "class",
    "lsp": "class",
    "notebooklm": "class",
    "rlm": "class AsyncSearchRouter",
    "skills": "class",
    "yt_is": "class",
    "qmd_wiki": "import asyncio",
}


@pytest.fixture
def router():
    """Create a router in local-only mode for testing."""
    return AsyncSearchRouter(enable_jmri=True, enable_cache=False, mode="local-only")


@pytest.mark.parametrize("backend_name,query", list(BACKEND_QUERIES.items()))
@pytest.mark.asyncio
async def test_backend_returns_results(router, backend_name, query):
    """Each backend should return ≥1 result for its specific query."""
    results = await router.search_async(query, limit=3, backends=[backend_name])
    assert len(results) >= 1, f"Backend '{backend_name}' returned 0 results for query '{query}'"
