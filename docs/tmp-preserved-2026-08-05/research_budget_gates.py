"""Research: mechanisms to prevent AI agents from exceeding resource budgets."""
from ddgs import DDGS

queries = [
    "AI agent cost budget enforcement mechanism tool-use constraint",
    "LLM agent spending limit quota gate prevent excessive API calls",
    "cost-aware agentic architecture resource governance budget ceiling",
    "AI agent free-tier-first routing strategy quota optimization",
    "LLM tool use permission gate pre-flight cost check",
]

for q in queries:
    print(f"\n=== QUERY: {q} ===")
    try:
        results = DDGS().text(q, max_results=5)
        for r in results:
            print(f"TITLE: {r['title']}")
            print(f"URL: {r['href']}")
            print(f"SNIPPET: {r['body'][:200]}")
            print()
    except Exception as e:
        print(f"ERROR: {e}")
