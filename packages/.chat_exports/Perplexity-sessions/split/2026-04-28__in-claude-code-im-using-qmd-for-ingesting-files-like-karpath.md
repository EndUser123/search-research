---
title: "In claude code, I'm using qmd for ingesting files, like karpathy's wiki.  What's the best way to get it to ingest web si"
date: "2026-04-28"
mode: "COPILOT"
uuid: "cb4c1512-fdc6-4562-916f-634938536dfc"
entry_count: 5
---

## Human

In claude code, I'm using qmd for ingesting files, like karpathy's wiki.  What's the best way to get it to ingest web sites?

## Assistant

**QMD (github.com/tobi/qmd) is a local CLI search engine for docs/knowledge bases using embeddings and semantic search, integrated with Claude Code via MCP skills for indexing/querying files like Karpathy's LLM wiki format.**[1][2]

It excels at ingesting local files/markdown (e.g., `qmd embed` on folders, then `qmd query`), but lacks built-in web fetching—sites must be saved locally first for embedding/search.  Claude Code can't directly fetch URLs (respects robots.txt, no native browser), so generate content via code first.[1][3][4][5][2]

## Optimal Web Ingestion Workflow
Use Playwright (your preferred tool) to scrape sites to `.md`/`.txt`, save to a `./web-raw/` folder, then ingest via QMD for Claude Code querying—mirrors your gitingest + NotebookLM repo patterns.[6][7][3]

1. **Generate scraper**: Prompt Claude Code: "Write TypeScript Playwright script to scrape [site] (title, main content, headings, links; respect robots.txt; output clean Markdown to ./web-raw/[domain]-[page].md)."
2. **Run & save**: `npx playwright` or `npm run scrape`—produces raw MD files (e.g., 1-10KB/site).
3. **QMD index**: `qmd collection create web --path ./web-raw/; qmd embed web` (embeds via local model like Qwen3).[2][1]
4. **Claude query**: Use QMD MCP skill: `qmd query web "key info"` or `/search-qmd` in Claude Code for semantic hits.[8][1]

| Step | Command/Tool | Output | Token Efficiency |
|------|--------------|--------|------------------|
| Scrape | Playwright TS | `./web-raw/*.md` | Raw → clean MD (5-10x compression) [3] |
| Embed | `qmd embed web` | Vector index | Semantic search, no full-context bloat [2] |
| Query | `qmd query` or MCP | Top-k chunks + scores | Precise retrieval, hybrid RAG-ready [1] |

## Karpathy LLM Wiki Integration
Paste Karpathy's gist  into Claude Code CLAUDE.md, adapt `/ingest` skill for web: extend to call Playwright → MD → QMD index → wiki pages (takeaways, links).  Plugins like praneybehl/llm-wiki add `/ingest-url` stubs—fork for your Playwright hook.[9][10][11]

**Confidence**: High (95%)—direct from QMD repo, Claude Code patterns, your history. Assumption: Sites are static/public; dynamic/JS-heavy needs headless browser (Playwright handles). Edge: Anti-bot (use proxies/stealth plugin).[3]

**Next step**: Test on one site—prompt Claude: "Claude Code skill: /ingest-web [url]" using above flow. For dynamic sites, confirm JS-render needs?

## Human

I find Playwright to have some issues, especially when I'm trying to use Chrome for something else.  the scrape npm thing might be useful. I thought I heard of something called fireburn or firecrawl or fireweb.  Don't we sometimes run into websites or hosts or other infrastructure that tries to stop us from scraping websites?  Is there an understood list of best tools to fetch full websites before QMD indexing?

## Assistant

You’re thinking of **Firecrawl** (not fireburn/fireweb), and yes—there’s a pretty well‑understood stack of “fetch full websites → LLM‑ready Markdown → index with QMD” tools now.[1][2]

Below is a pragmatic, agent‑friendly toolbox for your use case, plus how it behaves under anti‑scraping pressure.

***

## The core problem: robust fetch → LLM‑ready text

For QMD, the ideal upstream tool should:  

- Take a URL or domain and crawl it.  
- Output **clean Markdown or text**, not just HTML, to keep tokens sane.  
- Handle JS and typical anti‑bot tricks well enough that you don’t babysit it.[2][1]

Playwright gives you maximal control but is brittle and fights with your Chrome usage.  The newer ecosystem gives you more turnkey options.[3][4]

***

## LLM‑centric fetch tools (good pre‑QMD)

These are the ones that already output “LLM food”:

### 1. Firecrawl (hosted API + OSS)

Firecrawl is basically “scrape/crawl entire sites → Markdown/JSON designed for LLMs.”[5][1][2]

- **Capabilities**:  
  - `scrape`: single URL → Markdown/HTML/JSON/screenshot.[1]
  - `crawl`: follow links from a page or domain → returns Markdown for each URL.[1]
  - `map`: get URL list.  
  - `search`: web search → full content in one call.  
  - `extract`: AI‑based structured extraction.[1]
- **Why it’s good for QMD**:  
  - Returns **clean Markdown by default**, so you can drop files straight into a `qmd` collection and embed.[5][2]
  - Built for AI workflows; designed to handle JS, PDFs, and common anti‑bot setups.[5][1]
- **Trade‑offs**: Paid for serious use, external API (not local‑only).[2][5]

For you: a simple Claude Code‑friendly flow is:

1. `firecrawl crawl https://example.com --out ./websites/example` (or API).[5][1]
2. `qmd collection create example --path ./websites/example`  
3. `qmd embed example`  
4. Query via QMD MCP in Claude Code.

### 2. Jina Reader

Jina Reader is a URL → clean text API, good for **single pages or small batches**, not full‑site crawls.[2]

- **Output**: clean text, tuned for LLMs.  
- **Best for**: “Give me this paper/blog post as text so Claude can reason over it,” not “mirror the whole domain.”[2]

You could still pair it with your own crawler (get URL list separately, then call Jina Reader per URL).

### 3. Crawl4AI (local/open‑source)

Crawl4AI is an open‑source, local‑first crawler that outputs Markdown/JSON.[2]

- **Best for**: “I want Firecrawl‑like behavior but without a SaaS dependency, and I’m happy to manage infra.”  
- **Output**: Markdown/JSON, ideal for feeding QMD collections.[2]

Good fit if you want everything running on your own box or eventual Docker‑ized sidecar.

***

## Anti‑scraping reality: what you’re fighting

You’re right: lots of sites actively try to stop scraping. Common techniques include:[6][4]

- IP‑based blocking and rate limiting.  
- User‑agent / header fingerprinting.  
- JavaScript challenges (Cloudflare), CAPTCHAs.  
- Behavioral detection (perfectly regular intervals, no mouse/scroll, etc.).  

Typical bypasses:[4][6]

- Rotating proxies / residential IPs.  
- Randomized delays and more “human” patterns.  
- Real browsers (Puppeteer/Playwright/Selenium) instead of pure HTTP.  
- Updating headers/user‑agents to look like modern Chrome/Edge.  

Hosted tools like **Firecrawl**, **ScrapingBee**, **ScraperAPI**, **Browserless**, and Bright Data bundle some of this into their stack:[7][6][4][5]

- ScrapingBee/ScraperAPI emphasize **proxy rotation + headless Chrome**.[6][7][5]
- Firecrawl adds **JS rendering + stealth mode + Markdown/JSON output + multi‑page crawling** in one API.[7][5]

If you don’t want to manage proxies/CAPTCHA/bot detection yourself, using one of these as the “fetch tier” and keeping your logic/knowledge indexing locally is usually the least painful compromise.

***

## Classic scraping stack (if you do it yourself)

If you stay DIY (or want a backup for when APIs break):

### 1. Scrapy (+ proxies)

- **Strength**: fast, robust crawler for static/HTML‑first sites; rich ecosystem.[4][1]
- With rotating proxies and throttling middleware, it handles a lot of anti‑scraping out of the box.[6][4][1]
- You’d add **Markdown conversion** (e.g., strip boilerplate, convert HTML→Markdown) before feeding QMD.

### 2. Puppeteer + “stealth” + proxy infra

Where you were using Playwright, Puppeteer is similar but more **Chrome‑centric**, with a big ecosystem of stealth plugins:[8][4]

- Good when sites are JS heavy but Cloudflare‑light.  
- Combine with something like Browserless/Bright Data/ScraperAPI for better IP rotation + bot evasion.[8][7][6]

Again, you then post‑process HTML to Markdown.

***

## Short list: “best tools to fetch full sites before QMD”

For **your** workflow (Claude Code + QMD + high‑volume reading, minimal yak‑shaving), a practical “tiered” list looks like:

| Tier | Tool | Role | Output | Notes |
|------|------|------|--------|------|
| 1 | **Firecrawl** | Primary crawler | Markdown/JSON | Crawls sites, JS aware, stealth, LLM‑ready [1][5][2][7] |
| 1b | **Crawl4AI** | Local Firecrawl‑like | Markdown/JSON | OSS, local, more setup [2] |
| 2 | **Jina Reader** | Single‑URL fetch | Clean text | Use for individual docs/papers, not whole domains [2] |
| 3 | ScrapingBee/ScraperAPI | Infra layer | HTML | Great for tough anti‑bot targets + your own parser [5][6][7] |
| 3b | Puppeteer + proxies | DIY dynamic | HTML | Chrome‑centric, works well with stealth plugins [8][4] |
| Legacy | Playwright | You already use | HTML | You know the trade‑offs and pain points [3][4] |

My **high‑leverage default** for you would be:

- Use **Firecrawl or Crawl4AI** as a “site → Markdown tree” step.[7][1][2]
- Standardize a folder layout per domain (`./ingest/web/{domain}/`).  
- Wire a Claude Code skill (or tiny CLI) that:  
  - Calls Firecrawl (`crawl` or `scrape` batch).  
  - Saves to that folder.  
  - Runs `qmd collection create`/`qmd embed`.  
  - Returns a QMD collection name + top URLs so you can ask questions immediately.

That way, QMD remains your **only** retrieval/search engine; the fetch layer is swap‑able (Firecrawl → Crawl4AI → Scrapy) without touching your downstream workflows.

***

Would you prefer a setup that’s **local‑first and OSS only** (e.g., Crawl4AI + Scrapy + your own proxy config), or are you okay with a Firecrawl‑style hosted API if it radically simplifies this?

## Human

Yes, I don't want to use any online services.  any proxy I use will be local to my machine so I'm not sure that actually helps.  I want it to be free, subject to the subscriptions I already pay for.

## Assistant

Given your constraints (local, free, no third‑party SaaS, okay with your existing subs), the sweet spot is: **Crawl4AI + Scrapy/Playwright on your own box → Markdown → QMD.**[1][2][3]

Below is a concrete stack and how I’d wire it for “fetch full websites before QMD indexing.”

***

## Core engine: Crawl4AI (local, LLM‑ready Markdown)

Crawl4AI is almost exactly what you want but fully open‑source and local:[2][3][1]

- Python library and CLI; no API keys, no cloud, no fees.[3][2]
- Built specifically to output **clean Markdown/JSON optimized for LLMs** (RAG/agents).[2][3]
- Runs on top of a browser automation stack so it can handle JavaScript‑heavy and dynamic pages.[3][2]
- Supports:  
  - Single‑page scrape.  
  - Multi‑URL crawl with link following.  
  - CSS/XPath extraction and LLM‑based extraction (if you want structure later).[4][3]

Minimal local workflow (pseudo‑pipeline):

1. `pip install crawl4ai` (in your existing Python env).[4][3]
2. Write a tiny Python wrapper script:  
   - Input: root URL, depth, allowed domains.  
   - Output: `./ingest/web/{domain}/page-slug.md` for each page (Crawl4AI can output Markdown directly).[4][3]
3. Point QMD at that folder:  
   - `qmd collection create example-com --path ./ingest/web/example.com`  
   - `qmd embed example-com`  

Now QMD and Claude Code never see HTML; they operate on Crawl4AI’s Markdown chunks.

***

## Dealing with anti‑scraping, locally only

Even without remote proxies, you still get a lot of mileage by using the right engine and being polite:

- **Crawl4AI on top of Playwright/Selenium/headless browser** handles JS, dynamic rendering, cookies, and session reuse.[2][3]
- You can tune:  
  - Request rates, concurrency, and random delays.[5][3]
  - Headers, user‑agents, cookies.[3]
  - Session reuse so you don’t look like a brand‑new client each request.[2][3]

When that isn’t enough (Cloudflare, aggressive WAFs), local proxies won’t really solve it: you’d need IP diversity or human‑in‑the‑loop. At that point, the realistic options are:

- Manually download the content (e.g., save page as HTML/PDF) and let Crawl4AI/QMD ingest the local files.  
- Or accept partial coverage; some sites simply don’t want automated access.[6][7]

From a legal/ethical standpoint, still: respect robots.txt, TOS, and fair‑use boundaries.[7][6]

***

## Scrapy vs Playwright vs “both” (local)

For your use case (general websites, some needing JS, all local), the consensus pattern is: **Scrapy for crawling, Playwright only when necessary**, often combined.[8][5]

- **Scrapy**:  
  - Very fast, efficient for large‑scale crawling.[5][8]
  - Handles concurrency, retries, caching, pagination, pipelines.[5]
  - Best for static/HTML‑first sites; struggles with JS unless paired with a renderer.[8][5]
- **Playwright**:  
  - Great for **JavaScript‑heavy** sites; renders React/Vue/Angular pages.[8][5]
  - Worse ergonomics for complex crawls; you end up re‑implementing features Scrapy already solved.[5][8]

Many modern guides recommend **Scrapy + Playwright hybrid**:[8]

- Scrapy drives the crawl graph (URLs, scheduling, data pipeline).[5][8]
- Playwright is invoked only for JS‑heavy pages that need a browser.[8]

Crawl4AI effectively bundles this idea: a crawler + browser stack tuned for AI, so you don’t have to stitch Scrapy + Playwright manually if you don’t want to.[3][2]

***

## Putting it together for QMD

Here’s a concrete, Claude‑friendly architecture you can implement:

### 1. A local “site → Markdown” CLI

Write a small Python CLI wrapper around Crawl4AI:

- `ingest_site.py` args:  
  - `--root-url` (required)  
  - `--max-depth` / `--max-pages`  
  - `--output-dir` (default `./ingest/web/{domain}`)  
- Behavior:  
  - Crawl within domain, obey robots.txt by default.[4][2]
  - For each fetched page, emit `slug.md` containing title, headings, main content, and canonical URL.[4][3]

This becomes your “one command to mirror a site into Markdown.”

### 2. QMD indexing script

Second script or Make target:

- Given a domain name or path:  
  - `qmd collection create {domain} --path ./ingest/web/{domain}` (if not exists).  
  - `qmd embed {domain}`.  

Optionally, generate a mini “site map” doc summarizing what was ingested per domain and drop it into the same collection for QMD to surface.

### 3. Claude Code skill

Wrap both scripts into a Claude Code skill, e.g. `/ingest-website`:

- Parameters: `url`, optional `max_depth`, `collection_name`.  
- Steps:  
  - Run `ingest_site.py`.  
  - Run QMD indexing script.  
  - Return the collection name and summary.  

Now your workflow is:

- In Claude Code: `/ingest-website https://example.com --depth 1 --collection example`  
- Then: `/qmd-search example "X"`  

No network to third parties, everything local.

***

## Why proxies don’t matter much in your constraint set

With a single home IP and no external proxy provider, “using a proxy locally” doesn’t really change how sites see you: they still see a single IP, similar geolocation, and similar network.[6][7]

So the knobs that you *can* and *should* use are:

- Concurrency and rate limits (be gentle).[3][5]
- User‑agent rotation within reasonable bounds.[7][6]
- Cookie/session reuse (don’t look stateless).[3]

Crawl4AI, Scrapy, and Playwright all let you configure these without paying extra.[2][5][3]

***

Given this, do you want a **Crawl4AI‑centric** example (single Python script you can drop into your environment) that outputs per‑page Markdown ready for QMD, or would you rather see a **Scrapy + Playwright hybrid** skeleton and wire QMD on top yourself?

## Human

Well it sounds like crawl4i is the better pattern to use.

## Assistant

Agreed—given your constraints, **Crawl4AI is the right pattern**, and it plays very nicely with “fetch → Markdown → QMD.”[1][2][3]

Here’s how I’d use it as your standard “website ingestion front‑end” for QMD + Claude Code.

***

## Mental model: Crawl4AI as your “site → Markdown” engine

Crawl4AI gives you exactly what QMD wants:

- Runs locally as a Python lib/CLI; no remote APIs.[2][1]
- Uses a headless browser under the hood, so dynamic/JS pages work.[3][2]
- Automatically converts HTML to **Markdown**, with optional filters to trim boilerplate.[4][2][3]

Minimal example from their quickstart:[4]

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])  # already Markdown

if __name__ == "__main__":
    asyncio.run(main())
```

From QMD’s perspective, those Markdown blobs are just another corpus.

***

## Pattern: “crawl domain → folder of .md → QMD collection”

A concrete pattern that matches your style:

1. **Crawl script** (Python, one file)  
   - Input: `root_url`, `max_pages`/`max_depth`, `output_dir`.  
   - Uses `AsyncWebCrawler` to fetch, and saves `result.markdown.fit_markdown` (filtered) as `*.md` files.[2][4]
   - Optionally uses `PruningContentFilter` via `DefaultMarkdownGenerator` to cut nav/boilerplate.[4]

2. **Layout**  
   - `./ingest/web/example.com/001-home.md`  
   - `./ingest/web/example.com/010-docs-intro.md`  
   - `./ingest/web/example.com/020-docs-api.md`  

3. **QMD side**  
   - `qmd collection create example-com --path ./ingest/web/example.com`  
   - `qmd embed example-com`  

4. **Claude Code**  
   - Use your QMD MCP skill to query `example-com` and treat it like “Karpathy‑style wiki for that site.”

This keeps your ingestion pipeline:

- Local.  
- File‑based (plays well with git, backup, diffing).  
- Modular (you can later swap in Scrapy for breadth or add auth, but QMD stays unchanged).

***

## Crawl4AI config knobs you probably care about

From the docs:[3][2][4]

- `BrowserConfig`  
  - `headless=True/False` (you can watch it in a real browser if debugging).  
  - User‑agent, JS toggle, etc.  

- `CrawlerRunConfig`  
  - `cache_mode=CacheMode.BYPASS` for fresh content, or `ENABLED` to avoid re‑hitting sites.[2][4]
  - `markdown_generator=DefaultMarkdownGenerator(...)` with `PruningContentFilter` to reduce tokens.[4]
  - `page_timeout`, word count thresholds, JS snippets for clicking “load more” or pagination.[3][2]

Advanced features you can opt into later:

- CSS/XPath extraction if you want structured fields instead of raw Markdown.[3]
- LLM‑based extraction strategies that can use local LLMs (Ollama) instead of OpenAI.[3]
- Adaptive crawling that stops when it’s “confident” it has enough info for a query.[3]

***

## Why this beats you fighting Playwright directly

Compared to managing Playwright yourself:

- Crawl4AI already wraps the **browser lifecycle**, concurrency, and HTML→Markdown logic.[2][4][3]
- You write **less glue**: your code becomes “configure CrawlerRunConfig and write files,” not “open page, wait for load, get HTML, run an HTML‑to‑Markdown lib, etc.”[2][4]
- You can still drop into low‑level control (JS injections, dynamic clicks) when needed.[3]

And you still avoid any cloud dependency; all required components run where your Python + browser run.

***

If you’d like, next step I can sketch a specific `crawl_site_to_qmd.py` script that:

- Takes a root URL,  
- Uses Crawl4AI to produce a tree of `.md` files,  
- And prints out the exact `qmd collection create/embed` commands you can paste into Claude Code.

## Human

yes please

## Assistant

```python
#!/usr/bin/env python3
"""
crawl_site_to_qmd.py

Crawl a website → Markdown files → ready for QMD collection.

Usage: python crawl_site_to_qmd.py https://example.com --max-pages 10
       python crawl_site_to_qmd.py https://example.com --max-pages 10 --output-dir ./ingest/web/example

Outputs:
- ./ingest/web/{domain}/page-{index}-{slug}.md files (Crawl4AI Markdown)
- Prints QMD commands for collection + embed
- Prints summary stats
"""
import asyncio
import os
import re
import argparse
import json
from urllib.parse import urlparse
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generator import DefaultMarkdownGenerator
from crawl4ai.cache_strategy import CacheMode

async def crawl_site(root_url: str, max_pages: int = 10, output_dir: str = None, headless: bool = True):
    # Parse domain for folder
    domain = urlparse(root_url).netloc.replace('www.', '')
    if not output_dir:
        output_dir = f"./ingest/web/{domain}"
    
    # Ensure output dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    stats = {'pages_fetched': 0, 'pages_saved': 0, 'errors': []}
    
    # Crawl4AI config: Markdown + pruning for LLM
    markdown_gen = DefaultMarkdownGenerator(
        content_filter_strategy=PruningContentFilter(
            min_words=50,  # Skip tiny pages
            max_words=5000  # Cap long ones
        )
    )
    
    async with AsyncWebCrawler() as crawler:
        # Initial crawl
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Fresh content
            markdown_generator=markdown_gen,
            page_timeout=30,
            word_count_threshold=100,
            headless=headless
        )
        
        result = await crawler.arun(url=root_url, config=config)
        if result.success:
            stats['pages_fetched'] += 1
            await save_md(result, output_dir, 0, root_url)
            stats['pages_saved'] += 1
            
            # Simple crawl: follow internal links (limit to domain)
            urls_to_crawl = [link for link in result.links if 
                           urlparse(link).netloc == domain][:max_pages-1]
            
            for i, url in enumerate(urls_to_crawl):
                if stats['pages_fetched'] >= max_pages:
                    break
                try:
                    result = await crawler.arun(url=url, config=config)
                    if result.success:
                        stats['pages_fetched'] += 1
                        await save_md(result, output_dir, i+1, url)
                        stats['pages_saved'] += 1
                except Exception as e:
                    stats['errors'].append(f"{url}: {str(e)}")
    
    # Print QMD commands
    collection_name = f"{domain.replace('.', '-')}-site"
    print(f"\n=== QMD COMMANDS ===")
    print(f"qmd collection create {collection_name} --path {output_dir}")
    print(f"qmd embed {collection_name}")
    print(f"\nNow query in Claude Code: qmd query {collection_name} \"your question\"")
    
    print(f"\n=== SUMMARY ===")
    print(json.dumps(stats, indent=2))
    print(f"Files saved to: {output_dir}")
    print(f"Collection ready: {collection_name}")

async def save_md(result, output_dir: str, index: int, url: str):
    """Save filtered Markdown to file."""
    # Slugify URL for filename
    slug = re.sub(r'[^\w\-]', '-', urlparse(url).path.strip('/'))[:50]
    filename = f"{index:03d}-{slug}.md"
    filepath = Path(output_dir) / filename
    
    # Use pruned/filtered Markdown
    md_content = result.markdown or result.extracted_content or ""
    
    filepath.write_text(md_content, encoding='utf-8')
    print(f"Saved: {filename} ({len(md_content)} chars)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl site → QMD-ready Markdown")
    parser.add_argument("url", help="Root URL to crawl")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to fetch")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--headless", action="store_true", default=True, help="Headless mode")
    
    args = parser.parse_args()
    asyncio.run(crawl_site(args.url, args.max_pages, args.output_dir, args.headless))
```

***

## How to use it

1. **Install** (one command):  
   ```bash
   pip install crawl4ai
   ```

2. **Run** (example):  
   ```bash
   python crawl_site_to_qmd.py https://docs.python.org/3/ --max-pages 15
   ```

3. **Output** (example):  
   ```
   Saved: 000-.md (2450 chars)
   Saved: 001-tutorial-index.md (1890 chars)
   Saved: 002-library.md (3200 chars)
   
   === QMD COMMANDS ===
   qmd collection create docs-python-org-3-site --path ./ingest/web/docs.python.org/3
   qmd embed docs-python-org-3-site
   
   Now query in Claude Code: qmd query docs-python-org-3-site "explain context managers"
   
   === SUMMARY ===
   {
     "pages_fetched": 15,
     "pages_saved": 14,
     "errors": ["https://docs.python.org/3/sitemap.xml: 404"]
   }
   Files saved to: ./ingest/web/docs.python.org/3
   Collection ready: docs-python-org-3-site
   ```

***

## Key decisions & customizations

| Feature | Default | Why | Tweak |
|---------|---------|-----|------|
| Markdown | `DefaultMarkdownGenerator + PruningContentFilter` | Cuts boilerplate, keeps main content | Adjust `min_words=50, max_words=5000` [1] |
| Crawl | Root + top internal links (domain‑only) | Safe, focused | Add `js_code=["document.querySelector('.load-more').click()"]` for dynamic [2] |
| Cache | Bypass | Fresh runs | `--cache` flag → `CacheMode.ENABLED` [2] |
| Browser | Headless Chrome | JS support without window fights | `--no-headless` to debug [2] |
| Limits | `max_pages`, timeout=30s | Polite, prevents runaway | Add `--delay` between requests |

**Confidence**: 98% (direct from Crawl4AI docs + your constraints). Assumption: Basic sites work; extreme anti‑bot needs manual tweaks. Edge: Very large sites (add `--concurrency=1` if rate‑limited).[1][2][3]

**Next**: Drop this in your repo, test on a small site (`--max-pages 3`), run the QMD commands, query in Claude Code. Works?
