---
title: "Crawl4AI optimization: built-in features we should use instead of hand-rolling"
created: 2026-08-06
source: session-20260806-www
tags: [crawl4ai, web-scraping, optimization, deep-crawl, dispatcher, research-synthesis]
summary: >
  Crawl4AI v0.7+ has built-in deep crawl strategies (BFSDeepCrawlStrategy,
  BestFirstCrawlingStrategy), MemoryAdaptiveDispatcher, RateLimiter, KeywordRelevanceScorer,
  FilterChain, prefetch mode, LXML parsing, streaming, and crash recovery — all
  features we implemented manually in crawl_to_qmd.py. The right path is to
  migrate to crawl4ai's native APIs rather than maintain our own BFS loop.
agent: grok
host: grok
verification: researched
relations:
  - target: wiki/concepts/web-scraping-tool-alternatives-free-tier.md
    type: extends
---

# Crawl4AI optimization: built-in features we should use

## The gap

Our `crawl_to_qmd.py` implements its own BFS link-following loop, content-density
scoring, and boilerplate filtering — all of which crawl4ai has as native APIs.
We're maintaining custom code that duplicates upstream features.

## What crawl4ai provides that we're not using

### 1. BestFirstCrawlingStrategy (replaces our content-density scoring)

Crawl4AI has a `BestFirstCrawlingStrategy` that uses a `KeywordRelevanceScorer`
to prioritize URLs — exactly what our `_content_score()` function does, but
integrated into the crawler's link discovery pipeline.

```python
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

scorer = KeywordRelevanceScorer(keywords=["rate", "limit", "error", "api"], weight=0.7)
config = CrawlerRunConfig(
    deep_crawl_strategy=BestFirstCrawlingStrategy(
        max_depth=3, max_pages=30, url_scorer=scorer
    ),
)
```

Our hand-rolled `_content_score()` with `_CONTENT_PATH_WEIGHTS` dict maps to
this exactly. The difference: crawl4ai's scorer is integrated into the crawl
loop (no separate queue management), supports streaming, and has crash recovery.

### 2. FilterChain (replaces our boilerplate blocklist)

```python
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter

filter_chain = FilterChain([
    DomainFilter(allowed_domains=["docs.cohere.com"]),
    # PatternFilter can block boilerplate OR allow specific paths
])
```

This replaces our `_is_boilerplate()` regex. More flexible — filters can be
chained, combined, and applied at different stages.

### 3. MemoryAdaptiveDispatcher (replaces our manual loop)

```python
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=70.0,
    max_session_permit=10,
    rate_limiter=RateLimiter(base_delay=(1.0, 2.0), max_retries=2),
)
```

Our manual `for url in link_queue:` loop in `crawl_site()` is a single-threaded
BFS. The dispatcher runs crawls in parallel with memory-adaptive concurrency —
preventing OOM while maximizing throughput.

### 4. Prefetch mode (5-10x faster discovery)

```python
config = CrawlerRunConfig(prefetch=True)  # skips markdown/extraction, returns links only
```

Two-phase crawl: prefetch discovers all links fast (200-500ms/page vs 2-5s),
then selectively crawl high-value pages with full extraction. This is the
optimal pattern for "crawl everything but prioritize docs pages."

### 5. LXMLWebScrapingStrategy (20x faster parsing)

```python
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
config = CrawlerRunConfig(scraping_strategy=LXMLWebScrapingStrategy())
```

Up to 20x faster than default parsing. No reason not to use this.

### 6. Streaming mode (lower memory)

```python
config = CrawlerRunConfig(stream=True)  # process results as they arrive
async for result in await crawler.arun(url, config=config):
    process(result)
```

Reduces memory ~60% for large crawls. Our current code accumulates all results
before writing.

### 7. Crash recovery

```python
strategy = BFSDeepCrawlStrategy(
    on_state_change=lambda state: save_to_file(state),
)
# On restart:
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(resume_state=load_state()),
)
```

Our manual loop has no crash recovery — if it dies mid-crawl, we lose progress.

## General web crawling best practices (from field research)

These apply regardless of whether we use crawl4ai's APIs or our own loop:

| Practice | What we do now | What we should do |
|---|---|---|
| **Parallel dispatch** | Serial (one page at a time) | Use arun_many + dispatcher |
| **Rate limiting** | None | RateLimiter with base_delay + backoff |
| **URL normalization** | None | Strip fragments, tracking params, lowercase host |
| **Content dedup** | SHA256 hash (good) | Same — already implemented |
| **Robots.txt** | Not checked | `check_robots_txt=True` |
| **Caching** | CacheMode.BYPASS (always fresh) | CacheMode.ENABLED for re-crawls |
| **Browser config** | Default (heavy) | text_mode=True, light_mode=True |
| **Monitoring** | Print statements | CrawlerMonitor with DETAILED mode |

## Migration path

The minimal migration: replace our BFS loop with crawl4ai's deep crawl strategy.

```python
# Instead of our manual link queue:
async def crawl_site(root_url, ...):
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=3,
            max_pages=max_pages,
            url_scorer=KeywordRelevanceScorer(
                keywords=["docs", "reference", "api", "rate", "error", "guide"],
                weight=0.7,
            ),
            filter_chain=FilterChain([
                DomainFilter(allowed_domains=[domain]),
            ]),
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(root_url, config=config):
            if result.success:
                await _save_md(_normalize_result(result), ...)
```

This eliminates: our BFS loop, _content_score(), _is_boilerplate(),
_extract_internal_links(), and the link_queue management code — while gaining
parallel dispatch, rate limiting, crash recovery, and streaming.

**Caveat**: requires crawl4ai ≥0.7.0 (we have 0.7.8). Some deep crawl APIs
(BestFirst, FilterChain, scorers) may need 0.8+. The `--check-version` flag
already exists to detect this.

## Sources

- [crawl4ai multi-URL crawling docs](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
- [crawl4ai deep crawling docs](https://docs.crawl4ai.com/core/deep-crawling/)
- [crawl4ai browser/crawler config docs](https://docs.crawl4ai.com/core/browser-crawler-config/)
- [crawl4ai v0.4.3b1 release notes](https://docs.crawl4ai.com/blog/releases/v0.4.3b1/) — streaming, memory improvements
- [crawl4ai GitHub](https://github.com/unclecode/crawl4ai)
- [Scrapfly: Crawl4AI explained](https://scrapfly.io/blog/posts/crawl4AI-explained)
- [Google crawl budget docs](https://developers.google.com/crawling/docs/crawl-budget)
- [ScrapeHero: rate limiting in web scraping](https://www.scrapehero.com/rate-limiting-in-web-scraping/)
- [arXiv:2506.16146](https://arxiv.org/html/2506.16146v2) — neural crawl prioritization

## Falsifier

If crawl4ai's deep crawl APIs are unstable or missing in 0.7.8 (our installed
version), migration should wait until we upgrade. Test by importing
`BestFirstCrawlingStrategy` and `KeywordRelevanceScorer` — if they fail,
the APIs are 0.8+ only.
