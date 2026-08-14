---
title: "What other repos are like tavily, exa, brave, etc?"
date: "2025-12-08"
mode: "COPILOT"
uuid: "4221ba56-389f-4915-baf1-8bf7e6d556c3"
entry_count: 8
---

## Human

What other repos are like tavily, exa, brave, etc?

## Assistant

## Key Open-Source Repos

Several GitHub repositories serve as open-source alternatives or wrappers for AI-optimized search APIs like Tavily (search for AI agents), Exa (semantic web search), and Brave (privacy-focused search). These focus on self-hosted search engines, MCP servers for AI tools like Claude Code, and unified search proxies.[1][2][3]

## Search API Wrappers and Aggregators

- **SurfSense (MODSetter/SurfSense)**: Customizable AI research agent integrating Tavily, SearxNG, LinkUp, and external sources like GitHub, Notion, Slack; supports LangChain, LangGraph, and rerankers for RAG workflows.[4][1]
- **mcp-omnisearch (spences10/mcp-omnisearch)**: MCP server combining Tavily, Perplexity, Kagi, Jina AI, Brave, Exa, Firecrawl for unified search and content processing in AI coding environments.[2]
- **Perplexica (ItzCrazyKns/Perplexica)**: Open-source Perplexity AI alternative using SearxNG for real-time search, embeddings, and reranking; supports Tavily/Exa integration and modes like Reddit/video search.[3][5]
- **brave-api (kayvane1/brave-api)**: Python wrapper for Brave Search API emphasizing privacy, with support for custom "goggles" reranking.[6]

## Self-Hosted and Crawling Tools

Firecrawl (firecrawl/firecrawl) offers web search with scraping, markdown extraction, and result crawling, positioning as a production-ready alternative for AI apps. These repos align with your Claude Code and multi-agent workflows, enabling local-first research without vendor lock-in.[7]

## Human

List open source web search API repositories

## Assistant

## Open-Source Web Search API Repositories

Open-source GitHub repositories providing web search APIs or self-hosted alternatives include wrappers for commercial APIs (e.g., Brave, Exa), unified aggregators, and full search engines optimized for AI/RAG use cases.[1][2][3][4]

- **SurfSense (MODSetter/SurfSense or Decentralised-AI/SurfSense)**: Self-hosted AI search agent aggregating Tavily, SearxNG, GitHub, and more; supports LangChain integration and custom rerankers for agentic workflows.[4][1]
- **mcp-omnisearch (spences10/mcp-omnisearch)**: MCP server unifying Tavily, Perplexity, Brave, Exa, Firecrawl; designed for Claude Code/Cursor with semantic search and content extraction.[2]
- **Perplexica (ItzCrazyKns/Perplexica)**: Open-source Perplexity clone using SearxNG backend; features real-time search, embeddings, and specialized modes (e.g., academic/video).[3][5]
- **brave-api (kayvane1/brave-api)**: Lightweight Python client for Brave Search API, supporting queries, images, and custom privacy-focused reranking.[6]
- **exa-search (JoshuaOliphant/exa-search)**: Unofficial Exa.ai search API wrapper for semantic web queries and crawling.[7]
- **firecrawl (firecrawl/firecrawl)**: Web scraping API turning sites into LLM-ready markdown; includes search-like crawling for AI data pipelines.[8]
- **openapi-web-search (postman-open-technologies/openapi-web-search)**: OpenAPI spec and server for generic web search endpoints, extensible for custom backends.[9]

These align with Claude Code MCP servers and local research agents from your prior setups.[10][11]

## Human

How to integrate a search API with LangChain

## Assistant

## Integration Steps

Integrate a search API with LangChain using dedicated tools like `TavilySearchResults`, `ExaSearch`, or `BraveSearchResults` via environment variables and simple imports. Set up requires an API key, then chain the retriever in a RAG pipeline for agentic search.[1][2]

1. Install dependencies: `pip install langchain-community tavily-python exa-py brave-search` (or equivalent for your chosen API).
2. Set API key: `os.environ["TAVILY_API_KEY"] = "your_key"` (repeat for `EXA_API_KEY` or `BRAVE_API_KEY`).
3. Initialize tool: `search = TavilySearchResults(max_results=5)` or `search = ExaSearch(api_key="your_key")`.

## Example Code

```python
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI  # or your LLM

# Initialize search tool
os.environ["TAVILY_API_KEY"] = "tvly-xxxx"
search_tool = TavilySearchResults(max_results=3)

# Create agent
llm = ChatOpenAI(model="gpt-4o-mini")
tools = [search_tool]
agent = create_tool_calling_agent(llm, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Run query
result = agent_executor.invoke({"input": "Latest on LangChain search integrations?"})
print(result["output"])
```
This setup works identically for Exa (`from langchain_community.utilities import ExaAPIWrapper`) and Brave.[3][1]

## Open-Source Repo Integration

For self-hosted options from prior lists, use LangChain's `Tool` abstraction:

- **SurfSense/Perplexica**: Wrap their API endpoints: `from langchain.tools import Tool; surfsense = Tool(name="SurfSense", func=lambda q: requests.post("http://localhost:3000/search", json={"query": q}).json())`.
- **Firecrawl/mcp-omnisearch**: Custom retriever: `class FirecrawlRetriever(BaseRetriever): def _get_relevant_documents(self, query: str): return firecrawl.search(query)`.[4][5]

These integrate seamlessly with your Claude Code MCP workflows via LangGraph for multi-agent routing.[6]

## Human

why would I want to do this?  what's the advantage?

## Assistant

## Core Advantages

Integrating a search API with LangChain equips LLMs with real-time web access, overcoming static knowledge cutoffs for accurate, up-to-date responses in RAG pipelines and agents. This prevents hallucinations on current events, benchmarks, or niche data absent from training corpora.[1][2][3]

## Key Benefits

- **Fresh Data Retrieval**: Agents fetch live info (e.g., "2025 election results" or "latest PyTorch release") instead of outdated internal knowledge; Tavily/Exa optimize for LLM-friendly structured results with summaries/snippets.[2]
- **RAG Accuracy Boost**: Combines search chunks with vector stores for grounded answers; reduces 30-50% hallucination rates in production apps per benchmarks.[3]
- **Agentic Workflows**: Enables multi-step reasoning—search → analyze → verify—like your Claude Code researchers, but with web intelligence for dynamic tasks (e.g., market research, code doc lookup).[4][5]
- **Cost/Control**: Self-hosted options (SurfSense, Perplexica) avoid API quotas; LangChain abstraction swaps providers seamlessly (Tavily → Firecrawl).[6][7]

## Use Case Fit

For your UVIR/video analysis and multi-agent stacks, this adds "live intel" subagents—e.g., route video trends queries to Exa for semantic YouTube/clip search, enhancing prompt engineering without vendor lock-in. Production ROI: 2-5x faster research loops vs. manual browsing.[8][9]

## Human

what are good repos that do this?

## Assistant

## Top Repositories

These GitHub repos demonstrate LangChain search API integrations (Tavily, Exa, Brave, etc.) for RAG agents and workflows, with ready-to-run examples aligning with your multi-agent research stacks.[1][2][3][4]

- **tavily-ai/langchain-tavily**: Official Tavily tools for search, crawl, extract, and map; includes full research agent examples with OpenAI function calling and LangGraph chaining.[5][1]
- **extrawest/langchain_gen_ai_agent**: Streamlit-powered AI agent using LangChain + Groq/Llama3 for web search; supports real-time queries via Tavily-like tools.[2]
- **langchain-ai/open_deep_research**: Configurable deep researcher with MCP tools and search APIs (Tavily/Exa); optimized for agentic RAG and multi-provider swapping.[3]
- **NirDiamant/RAG_Techniques**: Comprehensive RAG tutorials (10k+ stars) covering search-augmented retrieval, query optimization, and LangChain integrations for production accuracy.[6][4]
- **langchain-ai/langchain & langchain-community**: Core libraries with built-in tools (`TavilySearchResults`, `ExaSearch`); community repo has 100+ search wrappers and agent examples.[7][8]

## Claude Code Fit

Fork these for your MCP servers (e.g., omnisearch + Tavily agent) to enhance subagents with live web retrieval, reducing hallucinations in UVIR/video classification prompts.[9][10][11]

## Human

Show top LangChain integrations for web search tools

## Assistant

## Top LangChain Web Search Integrations

LangChain provides native tools and wrappers for leading web search APIs, enabling seamless RAG and agentic workflows with minimal setup via `langchain-community`.[1][2][3]

| Tool | Import Path | Key Features | Best For |
|------|-------------|--------------|----------|
| **TavilySearchResults** | `langchain_community.tools.tavily_search` | LLM-optimized results, summaries, max_results param; API key via env | Agent research, low-hallucination RAG [4][2] |
| **ExaSearch** | `langchain_community.utilities.exa_search` | Semantic search, web crawling, contents extraction | Deep topical retrieval, academic/video queries [5] |
| **BraveSearchResults** | `langchain_community.tools.brave_search` | Privacy-focused, image/news search, custom rerankers | Quick facts, unbiased current events [6] |
| **FirecrawlSearch** | `langchain_community.tools.firecrawl_search` | Site crawling to markdown, structured extraction | Full-page RAG pipelines, self-hosted scraping [7] |
| **PerplexitySearch** | `langchain_community.tools.perplexity_search` | Citation-backed answers, follow-up questions | Conversational research agents [8] |

## Usage Example

```python
from langchain_community.tools import TavilySearchResults, ExaSearch
tools = [TavilySearchResults(), ExaSearch()]
# Bind to agent: agent_executor = AgentExecutor(tools=tools)
```
These integrate directly with LangGraph for your multi-subagent routing and Claude Code MCP servers.[9][10][11]

## Human

what the archon repo with crawl4ai?

## Assistant

## Archon Repo Overview

Archon (primarily coleam00/Archon) is an open-source AI agent builder and knowledge management system for coding assistants, featuring Streamlit UI, Docker deployment, MCP servers, and agentic RAG workflows. It evolves iteratively (V3-V5+), integrating LangChain, Pydantic AI, and web crawling to auto-generate agents from natural language specs.[1][2][3]

## Crawl4AI Integration

Archon uses Crawl4AI (unclecode/crawl4ai) for LLM-friendly web crawling, turning sites into clean Markdown/JSON for RAG pipelines. Key integrations:[4]
- **Documentation Crawlers**: Dedicated scripts (`crawl_langchain_python_docs.py`, `crawl_crawl4ai_docs.py`) fetch sitemaps, extract/chunk content, embed, and store in Supabase for agentic retrieval.[1]
- **MCP-RAG Server**: coleam00/mcp-crawl4ai-rag provides MCP tools for AI agents (e.g., Cursor/Claude Code) to crawl, vectorize (OpenAI/Ollama), and query crawled data.[5]
- **Forked Variant**: CCwithAi/ArchonV5-CRAWL4AI-LANGCHAIN adds LangChain/Crawl4AI doc crawling to core Archon, enabling hybrid agents combining orchestration (LangChain), crawling (Crawl4AI), and agent creation (Pydantic).[1]

## Fit for Your Stack

Dockerized setup aligns with your Claude Code MCP workflows; use for UVIR by crawling video docs/trends into RAG for classification prompts. Recent updates (Crawl4AI v0.7.4) ensure compatibility. Start with `docker compose up` for full knowledge engine.[2][6][7]

## Human

any repos with search expansion, progressive discovery, and other advanced deep research functionality?

## Assistant

## Advanced Deep Research Repositories

Several GitHub repos implement sophisticated **search expansion**, **progressive discovery**, and **iterative research** patterns for multi-faceted queries:

### Core Deep Research Frameworks

**langchain-ai/deep_research_from_scratch** is the gold standard for learning advanced research workflows. It features five tutorial notebooks building a complete system with:[1]
- **Scoping phase**: Clarifies ambiguous queries before research
- **Iterative research agent**: Uses ReAct loops with Tavily search, tool calling, and content summarization for multi-step discovery
- **Parallel research supervisor**: Delegates sub-topics to concurrent agents, combining results with async orchestration
- **MCP integration**: Seamlessly swaps search providers (Tavily, Perplexity, Kagi, Exa, Firecrawl) via Model Context Protocol[1]

**langchain-ai/open_deep_research** is a production-ready variant with configurable models, search tools, and MCP servers for agentic workflows.[2]

**langchain-ai/local-deep-researcher** runs entirely locally via Ollama/LMStudio, enabling offline research without vendor APIs.[3]

### Query Expansion & Semantic Enhancement

**jina-ai/llm-query-expansion** implements LLM-based query expansion (100-250 words) to improve retrieval; uses Gemini to generate synonyms, related concepts, and context-rich restatements before embedding search. This directly combats "no results" failures.[4]

**HyDE (Hypothetical Document Embeddings)** technique generates synthetic documents from queries rather than searching directly. LangChain/Haystack implementations exist; works by having LLM imagine a full document answering your query, embedding that instead—captures semantic intent even without exact matches in the index.[5][6]

### Perplexity AI Clones (Reference Implementations)

**ItzCrazyKns/Perplexica** features "Balanced/Fast/Quality" modes with multi-turn research; integrates SearxNG for self-hosted search and supports query expansion via multiple search backends.[7]

**rashadphz/farfalle** is a lightweight Perplexity clone optimized for Ollama (local LLM) with Docker setup.[8]

**Fireplexity** (Firecrawl team) uses V2 crawling (10x faster) for on-demand deep research with Groq/Claude integration; includes Vercel deployment.[9]

**Simplicity** open-sourced: FastAPI backend breaking deep research into sub-questions, then researching each independently—exemplifies progressive discovery.[10]

### Integration for Your Stack

For UVIR/video analysis, combine **deep_research_from_scratch** (scoping + iterative research) with **jina-ai/llm-query-expansion** (multi-term discovery) + **mcp-crawl4ai-rag** (doc crawling) to build intelligent research subagents that expand vague video taxonomy queries into comprehensive topic maps.[11][12]
