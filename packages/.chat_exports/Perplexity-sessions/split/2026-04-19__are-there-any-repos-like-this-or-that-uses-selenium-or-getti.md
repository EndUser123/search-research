---
title: "Are there any repos like this, or that uses selenium or getting bulk data from the DOM?"
date: "2026-04-19"
mode: "COPILOT"
uuid: "9cbdee89-54e2-4a3b-aae6-99087c9588e0"
entry_count: 14
---

## Human

Are there any repos like this, or that uses selenium or getting bulk data from the DOM?

## Assistant

No exact open-source replicas of yt-is (your industrial-scale YouTube transcript pipeline using yt-dlp, Selenium Firefox fallback, NotebookLM batching, and SQLite WAL for multi-terminal safety on 140k+ video backlogs) exist on GitHub. Similar repos focus on smaller-scale transcript extraction via Selenium DOM scraping or yt-dlp, but lack your escalation chains, API quota failover, channel gap detection via RSS+playlist enumeration, or production hardening like 24h retry guards and circuit breakers.[1][2][3][4]

## Closest Matches
These repos use Selenium for YouTube transcript/DOM extraction or yt-dlp for bulk data, often processing video lists from CSV/search inputs. They emphasize JS-rendered content access but skip your scale/safety features.

| Repo | Key Techniques | Scale/Limits | Gaps vs yt-is |
|------|----------------|--------------|---------------|
| [aliaagheisX/Getting-Youtube-Video-Transcript-using-Python-and-Selenium](https://github.com/aliaagheisX/Getting-Youtube-Video-Transcript-using-Python-and-Selenium) [3] | Selenium clicks "Show transcript" button; extracts timestamps/chapters as DF/text. Handles single video or search-top results. | Single/batch via search; no DB/persistence. | No yt-dlp fallback, channel tracking, multi-key API, or industrial batching (e.g., no NotebookLM). |
| [bernorieder/youtube-transcript-scraper](https://github.com/bernorieder/youtube-transcript-scraper) [4] | Selenium + Geckodriver (Firefox); bulk from CSV video IDs; scrapes AJAX-loaded transcripts. | CSV bulk (arbitrary size); outputs files. | DOM-focused (no yt-dlp/API); lacks WAL safety, cooldowns, or escalation to audio/LLM. |
| [Dhammer3/youtube_scraper](https://github.com/Dhammer3/youtube_scraper) [5] | Selenium for channel video lists, comments, metadata; bulk channel dumps. | Channel-level bulk; recent uploads query. | DOM-heavy (titles/thumbs/comments); no transcripts or your failover chain. |

## Bulk DOM Patterns
Selenium repos for YouTube bulk data target dynamic elements (e.g., infinite scroll for comments/videos) via XPath/CSS selectors on loaded DOM, often headless Chrome/Firefox with waits. Example from IPRoyal scraper: scrolls to load comments (`driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight")`), extracts via `By.XPATH('//*[@id=\"content-text\"]')`, batches to CSV. Your `csfselenium.py` (Firefox cookies for age-restricted) aligns but adds EJS/curl-cffi pre-steps.[3][6][1]

yt-dlp alternatives appear in pipelines (e.g., your `fetchviaytdlp` WEB client), but no full yt-is clones combine it with Selenium+NotebookLM for 743-channel tracking.[7][1]

## Next Steps
1. Fork a base like `bernorieder/youtube-transcript-scraper`; inject your `transcript.py` chain (yt-dlp → Selenium → NotebookLM).[4]
2. Test quota exhaustion: Your multi-key failover in `sourceenumerator.py` beats single-key limits (~10k units/day).[1]
3. Migrate to Playwright (faster than Selenium 2026 consensus). Uncertainty: No yt-is-scale benchmarks; assume 2-5x speed on DOM bulk.[8][9]

What backlog size or channel count are you targeting next?

## Human

Examples of scraping Nordstrom product data without Selenium

## Assistant

No fully Selenium-free, production-scale Nordstrom scrapers match yt-is complexity (e.g., no WAL-DB multi-terminal or NotebookLM), but several use Requests/BeautifulSoup/httpx to parse HTML/JSON endpoints for product data like price, images, sizes, avoiding JS rendering. Key: Nordstrom embeds product data in `__INITIAL_CONFIG__` script JSON (stylesById), scraped via XPath/Selector—no DOM execution needed. Anti-bot (Akamai) requires proxies/TLS impersonation (curl-cffi/chrome120).[1][2][3]

## Core Techniques
Extract hidden JSON first, then parse listings/products. Requests headers mimic Chrome; proxies evade blocks.

- **JSON Endpoint Scraping**: `Selector(html).xpath("//script[contains(.,'__INITIAL_CONFIG__')]/text()").get()` → `json.loads()` → `nested_lookup("stylesById", data)` for product dict (id, price, variants).[2]
- **Search Results**: GET `/sr?{keyword}+{filters}`; parse `<div data-product-id>` for name/price/stock via BS4/CSS.[4][1]
- **Proxies + Impersonation**: `curl_cffi.Session(impersonate="chrome120")` + residential proxy; delays 2-5s; retry 429s x3.[3]
- **Pagination Hack**: Limit 12/page, derive 63 "pages" via offset params (no Selenium needed).[4]

## Code Examples
Prefer Python (your stack). All output CSV/JSON; scale via `concurrent.futures` or asyncio.

### Scrapfly httpx + Parsel (Product Detail)
```python
import asyncio
import json
from parsel import Selector
from nested_lookup import nested_lookup
import httpx

async def scrape_product(url):
    client = httpx.AsyncClient(http2=True, headers={"User-Agent": "Mozilla/5.0..."})
    resp = await client.get(url)
    data = Selector(resp.text).xpath("//script[contains(.,'__INITIAL_CONFIG__')]/text()").get()
    data = json.loads(data.split("=",1)[-1].strip(";"))
    product = list(nested_lookup("stylesById", data)[0].values())[0]
    return product  # {'id': '...', 'price': ..., 'sizes': [...]}
asyncio.run(scrape_product("https://www.nordstrom.com/s/phoenix-fleece-crewneck-sweatshirt/6665302"))
```
Facts: Bypasses JS; extracts full variants/stock. Add Scrapfly proxy for Akamai.[2]

### ScrapeOps Requests + BS4 (Search Bulk)
```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

def scrape_search(keyword):
    url = f"https://www.nordstrom.com/sr?{urlencode({'keyword': keyword.replace(' ','+')})}"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0...'})
    soup = BeautifulSoup(resp.text, 'html.parser')
    products = []
    for item in soup.select('[data-product-id]'):
        products.append({
            'name': item.select_one('.product-name').text.strip(),
            'price': item.select_one('.price').text.strip(),
            'id': item.get('data-product-id')
        })
    return products
```
Facts: Parallelize with ThreadPoolExecutor; ~100s/page. Residential proxies essential post-2026.[1][3]

### curl-cffi Residential Proxy (2026 Anti-Bot)
From Scraperly: Impersonate Chrome120; parse listings/pricing/inventory. Output `nordstrom_results.json`.[3]

## Repo Examples
| Repo | Stack | Data Extracted | Scale/Notes |
|------|--------|----------------|-------------|
| [SamiAlavi/WebScraper-Nordstrom](https://github.com/SamiAlavi/WebScraper-Nordstrom) [5] | Requests/BS4? (implied) | Images/full paths; categories/pages. | Bulk tabs/subcats; `scrape.py` + download. No Selenium explicit. |
| [GoTrained/Scrapy-Nordstrom](https://github.com/GoTrained/Scrapy-Nordstrom) [4] | Scrapy (Requests-based) | Search products (12/page hack). | Pagination workaround; CSV out. |
| [nultinator/nordstrom-requests-scraper](https://github.com/nultinator/nordstrom-requests-scraper) [6] | Requests | Products (name/price). | Explicit no-Selenium; modern (2024). |
| [saswatnayak1998/Nordstrom_Product_Scrapper](https://github.com/saswatnayak1998/Nordstrom_Product_Scrapper_Saswat) [7] | Python scraper | 20k products (10h CSV). | Bulk scale; no Selenium. |

## Edge Cases & Confidence
- **Blocks**: Akamai detects non-browser TLS/no proxy (90% fail rate raw Requests). Use curl-cffi + ProxyRack residential (~$5/GB). Uncertainty: Nordstrom updates 2026; test chrome120 impersonate.[3]
- **Data Completeness**: JSON > HTML (90% fields); misses dynamic reviews. Consensus: httpx/parsel best for JSON.[2]
- **Legal**: TOS prohibits scraping; use for personal/research. No API official.

Next: Integrate into yt-is via `registerexternaltranscriptprovider` hook? Test with `curl_cffi` like your `fetchviaytdlp`.[8]

What product fields (e.g., price/stock/images) matter most?

## Human

Top 20 Selenium/Playwright scraping repos ranked — stars, features, and code examples compared
​
How to set up Playwright for bulk web scraping instead of Selenium
Best GitHub repos using Puppeteer for DOM data extraction

Top open-source Selenium projects for YouTube scraping

## Assistant

Top Selenium/Playwright scraping repos cluster around testing frameworks with scraping extensions (e.g., infinite scroll, WhatsApp/Amazon bots), ranked by GitHub stars/forks from 2026 lists—no unified "top 20" exists, but docker-selenium leads at 7.3k stars for Grid scaling. Playwright edges Selenium for bulk scraping (auto-waits, async, fewer flakes); Puppeteer excels in Node/JS DOM extraction via stealth plugins. YouTube Selenium repos are niche/low-stars, favoring API/yt-dlp hybrids like your yt-is.[1][2][3][4][5]

## Top Scraping Repos Ranked
Filtered for scraping/relevant features (e.g., DOM/bulk/infinite scroll). Stars/forks from 2026 data; code focuses on Python/TS (your pref).

| Rank | Repo (Stars/Forks) | Language/Key Features | Code Example (DOM/Bulk) |
|------|---------------------|-----------------------|-------------------------|
| 1 | docker-selenium (7.3k/2.5k) [5] | Docker/Grid; bulk parallel browsers. | `docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-firefox` → Scale 100s sessions. |
| 2 | Panther (2.9k/215) [5] | PHP/Symfony; scraping + testing. | `$panther = PantherFactory::createPanther(); $client = $panther->createBrowser(); $client->get('url');` |
| 3 | Awesome Visual Regression (2.1k/169) [5] | Testing/scraping visuals. | Snapshot DOM diffs for bulk page checks. |
| 4 | Playwright Go (1.7k/134) [5] | Go; cross-browser bulk. | `browser := pw.MustLaunch(); page := browser.NewPage(); page.Goto(url)` |
| 5 | Webdrivers (591/114) [5] | Auto-driver mgmt; bulk setup. | `webdrivers.install()` → Handles Chrome/Firefox for fleets. |
| 6 | PyWhatsapp (444/140) [5] | Python Selenium; chat scraping. | `driver.get("web.whatsapp.com"); driver.find_element(By.XPATH("//span[@title='name']")).click()` |
| 7 | Python Scripts (299/146) [5] | Python bots/scrapers. | Generic bulk: `for url in urls: driver.get(url); data.append(extract_dom())` |
| 8 | Amazon Scraping (287/153) [5] | Python Selenium; product bulk. | Scrolls/products: `while True: driver.execute_script("window.scrollTo(0,doc.height)"); items = driver.find_elements(By.CLASS_NAME("s-result-item"))` |
| 9 | Pyleniumio (252/48) [5] | Python; POM for scraping. | `pl.login("user","pass"); pl.expect(".error").to_be_visible()` |
| 10 | Hacking Scripts (214/277) [5] | Multi-lang; scraping utils. | Bulk data pulls with waits/selectors. |

(Top 10 shown; full 52 at. Low YouTube-specific: "Youtube Infinite Scroll" 10/9 stars—HTMX/SQLModel, not pure Selenium.)[5]

## Playwright Bulk Setup
Playwright > Selenium for bulk: Native async/contexts (100s tabs), stealth (evades detection), no WebDriver flakiness. Install: `pip install playwright pytest-playwright; playwright install chromium firefox webkit`. Config for scale (playwright.config.ts/py):[6]

```python
# conftest.py (pytest bulk: shared context, retries)
import pytest
from playwright.async_api import async_playwright

@pytest.fixture(scope="session")
async def browser():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
    yield browser
    await browser.close()

@pytest.mark.asyncio
async def test_bulk(browser):
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    pages = [await context.new_page() for _ in range(50)]  # Bulk tabs
    await asyncio.gather(*(p.goto("https://example.com") for p in pages))
```
Facts: Retries `retries: 2` in CI; trace/screenshot on-failure. Migrate yt-is Selenium: Replace `csfselenium.py` Firefox with `chromium.launch_persistent_context` for cookies. Edge: Proxy per-context (`proxy={"server": "http://proxy:port"}`).[4][7]

## Puppeteer DOM Extraction Repos
Puppeteer (Chrome DevTools) shines for JS-heavy DOM (e.g., React/SPAs). Top from awesome-puppeteer:[8]

| Repo | Stars/Key Features | Code Example |
|------|---------------------|--------------|
| transitive-bullshit/awesome-puppeteer [8] | 3k+; Curated list (scrapers/plugins). | N/A (index). |
| humanwhocodes/puppeteer-data-extractor [9] | Data from DOM templates. | `const extractor = new PuppeteerDataExtractor(page); const data = await extractor.extract({title: 'h1', price: '.price'});` |
| tmptrash/harvester [10] | Fuzzy HTML/DOM extraction. | `await harvester.extract(page, {template: {items: {sel: '.product', props: {name: 'h2'}}}});` |

Consensus: Puppeteer + stealth-plugin for anti-bot; bulk via `puppeteer-cluster` (clusters pages).[8]

## YouTube Selenium Repos
Niche/low-stars; prefer API/yt-dlp (your stack). Top:

- **Youtube Infinite Scroll** (10/9 stars): Selenium? HTMX for channel video scroll.[5]
- From prior: aliaagheisX/Getting-Youtube-Transcript-Selenium (DOM transcript click).[11]
No yt-is scale; use Playwright for fallback (`csftranscript.py`).[5]

Confidence: Lists 2026-current; scraping TOS risks blocks (proxies req'd). Next: yt-is Playwright migration script?[2]

Which tool (Playwright/Puppeteer) for yt-is fallback first?

## Human

Playwright vs Puppeteer performance benchmarks for scraping
Selenium anti-bot evasion techniques in top repos
Code example for Scrapy integrated with Playwright

## Assistant

Here’s a compact, evidence‑grounded comparison and examples.

***

## 1. Playwright vs Puppeteer performance for scraping

**Benchmarks are mixed and scenario‑dependent.** Broad pattern from recent tests:

- Skyvern’s 2025 benchmark (same tasks, same machine):[1]
  - Short scripts: Puppeteer ≈ 3.2s vs Playwright ≈ 4.5s → Puppeteer faster.  
  - Navigation‑heavy flows: Puppeteer 4.784s vs Playwright 4.513s → Playwright faster.  
  - E2E scenarios: both around 8.1–8.2s → essentially a tie.  
  - Scraping tasks: Puppeteer ≈ 6.7s vs Playwright ≈ 7.2s → Puppeteer slightly faster per page.

- PromptCloud’s 2025 “real JS‑heavy e‑commerce” test:[2]
  - Puppeteer: ~75% success across ~500 pages, then increasing failures/incomplete data.  
  - Playwright: ~96% success across 1,000+ pages; slightly slower per page but more robust under parallel load.

- General consensus from practitioners: Puppeteer tends to be **a bit faster per page** because it targets Chromium only, but Playwright tends to be **more stable and scalable** for large, complex flows (auto‑waits, multi‑browser support, better parallelization APIs).[3][2]

**Takeaway for scraping:**

- If you care about **raw per‑page speed** and you’re fine with Chromium‑only, Puppeteer has a small edge.[1][2]
- If you care about **high success rates at scale, complex flows, and robustness**, Playwright tends to win in real‑world scrapes despite being a bit slower per page.[2][3]

I’d model it as:

- **Latency‑critical, simple flows, Node stack → Puppeteer.**  
- **High‑throughput, complex or flaky targets, multi‑browser, Python/TS → Playwright.**

***

## 2. Selenium anti‑bot evasion techniques (from top guides)

Modern anti‑bot (Cloudflare, Akamai, PerimeterX, Datadome) will reliably catch stock Selenium. Better repos/guides converge on:

From ScrapeOps’ “Make Selenium Undetectable” (2024):[4]

1. **Selenium‑Stealth (or equivalent)**
   - Hides obvious automation fingerprints:  
     - Removes/patches `navigator.webdriver`.  
     - Normalizes `navigator.plugins`, `navigator.languages`.  
     - Adjusts WebGL, canvas, audio, and other fingerprint surfaces to look like real Chrome.
   - Typically combined with Chrome in non‑headless or headless‑new mode.

2. **Residential / Mobile Proxies**
   - Rotate **residential IPs** instead of datacenter IPs (which are heavily flagged).[4]
   - Tie IP/session together (sticky sessions) for logged‑in flows; avoid hard resets mid‑flow.

3. **Realistic Headers & TLS Fingerprints**
   - User‑Agent, Accept‑Language, Sec‑CH‑UA, etc., must match the browser build.[4]
   - Some teams replace Selenium’s default driver with patched Chrome (or use tools like curl‑cffi / undetected‑chromedriver) to get realistic TLS fingerprints.

4. **Behavior Simulation**
   - Human‑like delays (`WebDriverWait`, random sleeps), scrolling, small mouse movements.[4]
   - Avoid hammering the same path at machine‑like intervals.

5. **JS Challenge Handling**
   - Offload heavy anti‑bot sites to:  
     - Cloud scraping APIs (ScrapeOps, ScrapingBee, etc.) or  
     - Headless Chrome with patched CDP that auto‑solves JS challenges.[4]

**Takeaway:** Real “undetectable” Selenium in 2026 = stealth layer + residential proxies + tuned headers + human‑like flow; raw `chromedriver` + default options gets flagged quickly on serious targets.[4]

***

## 3. Scrapy + Playwright integration (code example)

The standard approach today is **scrapy‑playwright**, which replaces Scrapy’s downloader with a Playwright‑powered handler for selected requests.[5][6]

### a) settings.py configuration

From Scrapy‑Playwright examples:[5]

```python
# settings.py
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
```

This tells Scrapy to use Playwright for HTTP/HTTPS and to use the asyncio reactor so Playwright’s async loop can run.[5]

You typically also set a realistic user‑agent and headers in `DEFAULT_REQUEST_HEADERS` to look like a real browser.[5]

### b) Minimal spider using Playwright for selected pages

From Trickster/Trickster.dev’s keyword checker example, reduced to essentials:[5]

```python
import scrapy

class KeywordSpider(scrapy.Spider):
    name = "kwchecker"
    start_urls = ["https://example.com"]

    def start_requests(self):
        # enable Playwright rendering for these URLs
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={"playwright": True},  # turn on browser for this request
            )

    async def parse(self, response):
        # When playwright=True, `response` carries a Playwright page in meta
        page = response.meta.get("playwright_page")

        # Example: wait for a dynamic selector before extracting
        await page.wait_for_selector("h1")
        text = await page.inner_text("body")

        yield {
            "url": response.url,
            "has_keyword": "example" in text.lower(),
        }

        # follow links with the same meta to keep using Playwright
        for href in response.css("a::attr(href)").getall():
            yield response.follow(
                href,
                callback=self.parse,
                meta={"playwright": True},
            )
```

Key points from the reference implementation:[6][5]

- `meta["playwright"] = True` ⇒ Scrapy routes that request through Playwright instead of the normal downloader.
- In handlers that need the page object, you access `response.meta["playwright_page"]` and can use `page.wait_for_selector`, `page.inner_text`, etc.[6][5]
- The plugin allows mixing: some requests via Playwright (JS‑heavy, protected), others via plain Scrapy (cheap, fast).[6][5]

For larger projects, DataGuru’s 2024 example uses the same pattern with more elaborate selectors and best practices (timeouts, screenshots, etc.).[6]

***

## How this maps to your use case

Given your stack (Python, Node, large‑scale scraping, and interest in moving away from Selenium):

- For **performance & reliability** at scale, Playwright is usually the safer default over Selenium, and often preferable to Puppeteer for complex multi‑step flows, at the cost of a small per‑page latency penalty.[1][2]
- For browsers embedded in **Scrapy pipelines**, `scrapy-playwright` is now the canonical integration; you can selectively apply Playwright on “hard” URLs and keep the rest as fast HTTP requests.[6][5]
- Selenium still has a place if you already have a heavy investment, but you’ll want a stealth stack + residential proxies to survive modern anti‑bot.[4]

If you tell me your primary targets (e.g., JS‑heavy retail, logged‑in dashboards, YouTube‑like), I can sketch a concrete Playwright architecture (contexts, concurrency limits, proxy rotation) tuned for your volume.  

## Human

Scrapy-Playwright code for handling infinite scroll
Playwright stealth plugins to evade anti-bot detection

## Assistant

Yes: for infinite scroll in Scrapy, the clean pattern is `scrapy-playwright` with `playwright_include_page=True`, repeated scroll/evaluate loops, and final extraction from `await page.content()` rather than trusting the original `response` HTML. For Playwright stealth, the common plugin path is `playwright-extra` plus `puppeteer-extra-plugin-stealth`, which patches automation leaks like `navigator.webdriver`, plugins, and headless markers, but it is not a guarantee against serious anti-bot stacks.[1][2][3][4][5]

## Infinite scroll

A practical Scrapy-Playwright pattern is: open the page with Playwright enabled, scroll in steps, wait briefly for network/rendering, stop when scroll position no longer changes, then parse the updated DOM. This is better than naive “scroll to bottom once” logic because many sites lazy-load in chunks and require repeated movement plus a settle delay.[2][1]

```python
import scrapy
from scrapy.selector import Selector

class InfiniteScrollSpider(scrapy.Spider):
    name = "infinite_scroll"
    start_urls = ["https://example.com/feed"]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse,
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        page.set_default_timeout(15000)

        await page.wait_for_timeout(2000)

        last_height = await page.evaluate("document.body.scrollHeight")
        stable_rounds = 0

        for _ in range(50):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1200)

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
                last_height = new_height

        html = await page.content()
        await page.close()

        sel = Selector(text=html)

        for card in sel.css("[data-testid='product-card']"):
            yield {
                "title": card.css(".title::text").get(),
                "url": response.urljoin(card.css("a::attr(href)").get("")),
                "price": card.css(".price::text").get(),
            }
```

Two useful upgrades are common. First, wait on a content selector after each scroll if the site appends known nodes, which is often more reliable than pure timeout logic. Second, dedupe by extracted URL or ID because infinite-scroll pages often re-render or duplicate cards during client-side hydration.[1][2]

## Stealth plugins

The mainstream Node/TS stack is `playwright-extra` with `puppeteer-extra-plugin-stealth`, used as a drop-in replacement for Playwright’s Chromium launcher. The plugin ecosystem exists because default headless Playwright leaks detectable signals such as `navigator.webdriver`, missing plugins, and headless UA fingerprints.[3][4][5]

```ts
import { chromium } from "playwright-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";

chromium.use(StealthPlugin());

async function run() {
  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    locale: "en-US",
    viewport: { width: 1366, height: 768 },
  });

  const page = await context.newPage();
  await page.goto("https://bot.sannysoft.com", { waitUntil: "networkidle" });
  await page.screenshot({ path: "stealth-check.png", fullPage: true });

  await browser.close();
}

run();
```

The important caveat: stealth plugins help mostly with **basic** browser fingerprint leaks, not with full anti-bot defense by themselves. Serious targets still require aligned headers, realistic browser versions, residential or mobile proxies, sane request pacing, and consistent session behavior; otherwise detection often shifts from browser fingerprinting to IP reputation, TLS, behavioral timing, or account risk models.[5][3]

## Practical notes

For bulk scraping, Playwright stealth is strongest in Node because `playwright-extra` is mature there; Python Playwright has fewer first-class stealth options and often relies on manual context hardening instead. If your target is a modern SPA with long infinite feeds, a mixed strategy is usually best: Scrapy handles scheduling, retrying, and parsing, while Playwright is only enabled on the hard pages that actually need JS execution.[4][6][2][3][1]

**FACT:** `scrapy-playwright` infinite-scroll implementations commonly use repeated `page.evaluate(...)` scroll calls plus `await page.content()` to capture the final DOM.[2][1]
**CONSENSUS:** `playwright-extra` + stealth is the default starting point for Playwright anti-bot work in the Node ecosystem.[3][4][5]
**SPECULATION, medium confidence:** If you are scraping high-value retail or social targets at scale, stealth alone will not materially change block rates without better proxy/session strategy.[3]

Concrete next step: convert one existing Selenium fallback to a Node sidecar that exposes a narrow Playwright-stealth fetch/extract RPC, while keeping Scrapy or Python orchestration in control.

## Human

What do you think would be optimal to download sources from notebooklm?

## Assistant

For what you’re doing (yt‑is scale, batch pipelines, downstream RAG), “optimal” really depends on whether you care more about: (a) fidelity of original binaries, or (b) fast, normalized text for downstream systems.

Given what’s actually available around NotebookLM today, I’d structure it like this:

***

## 1. Constraints & options (as of 2025–26)

- NotebookLM itself has **no native “export sources” or bulk download** for source files.[1][2]
- You can:
  - Download individual Drive sources from Drive (Docs, PDFs, etc.) as usual.[2][1]
  - Use **“Convert all notes to source”** to merge notes into a single source file, then copy it out manually.[3][4]
- For automation you basically have two external paths:
  1. **Browser/extension-based exporters** (Chrome extension running in your session).[5][1]
  2. **3rd‑party NotebookLM export APIs** (e.g. Apify actor).[6][7]

There is no official Google “NotebookLM export sources API” that gives you full PDFs/docs in bulk; all the “API” stories are wrappers that scrape or call internal/undocumented endpoints on your behalf.[7][6]

***

## 2. Recommended strategy by objective

### A. If you want **clean text snapshots** of sources (for RAG / search)

This is closest to what yt‑is wants for transcripts/notes.

**Best balance:** per‑notebook JSON/Markdown export via an extension or API actor, then normalize into your own DB.

- NotebookLM Tools / “NotebookLM Sources Exporter”‑style extensions:
  - Export each notebook’s source list and **parsed text content** to JSON or Markdown/ZIP.[1][5]
  - Typically include: notebook title, each source’s title/URL/type, and the text NotebookLM has indexed.[1]
  - Don’t give you original binaries, but for scraping/RAG the parsed text is often exactly what you want.[1]

- Apify NotebookLM API actor:
  - Bulk export notebooks → JSON/CSV/Markdown/Excel with **source metadata and citations**.[6][7]
  - Designed for “RAG pipelines, backups, n8n workflows”.[7][6]

**Optimal pipeline for you:**

1. Treat NotebookLM as a *frontline ingestion/analysis* tier.
2. On a schedule (or after major changes), run:
   - Extension‑based export per notebook, or
   - Apify actor to bulk export selected notebooks.
3. Store the export in your own SQLite/Postgres (parallel to `transcripts.sqlite` in yt‑is) with:
   - `source_id`, `notebook_id`, `title`, `url`, `type`, `content_text`, `last_exported_at`.
4. Run your own downstream normalization (segmentation, embeddings, quality flags) and never depend on NotebookLM for *primary* storage again.

This gets you **versioned, textual snapshots** suitable for further processing without fighting Google’s lack of bulk download.[6][1]

### B. If you want **original files** (PDFs/Docs)

NotebookLM doesn’t hand those back in bulk. For that:[2][1]

1. Use the export JSON (extension / API actor) **as a directory of references**:
   - Each source row includes the original URL or Drive file reference.[6][1]
2. Resolve those URLs yourself:
   - For Drive doc/slide/sheet IDs in your own Google account, hit Drive API to download binaries.
   - For PDFs/web pages, fetch directly with your own stack (curl‑cffi + TLS impersonation, etc.).
3. Store “source of truth” in your own blob store, and treat NotebookLM as a *derivative index*, not as storage.

This is more work but gives you complete control.

***

## 3. “Optimal” architecture for your context

Given yt‑is and your broader system, I’d do:

1. **One canonical “NotebookLM export” micro‑service**
   - Either:
     - n8n/Apify flow around the NotebookLM API actor, or[7][6]
     - A small browser‑automation worker (Playwright‑stealth) that:
       - Logs into NotebookLM
       - For each notebook, triggers the extension’s “Extract All Sources” / export action[5][1]
       - Downloads the produced JSON/ZIP
   - You avoid reverse‑engineering Google’s internal calls yourself.

2. **Normalized ingest format**
   - Define a simple schema something like:
     ```json
     {
       "notebook_id": "...",
       "notebook_title": "...",
       "sources": [
         {
           "source_id": "...",
           "title": "...",
           "url": "...",
           "type": "pdf|doc|web|youtube|note",
           "content": "parsed text",
           "folder_path": ["Research", "Subtopic A"]
         }
       ]
     }
     ```
   - Map the extension/Apify output into this; both provide notebook title, type, URLs, and text.[1][6]

3. **DB + file layout**
   - Store this into your existing SQLite/WAL world:
     - `notebooks` table (id, title, last_exported_at, etc.)
     - `sources` table (source_id, notebook_id, type, url, title, content, hash)
   - Optionally dedupe by `hash(content)` for repeated exports.

4. **Separation of concerns**
   - NotebookLM is just a “smart ingestion+analysis front end”.
   - `yt-is` + your RAG stack own:
     - Long‑term persistence
     - Heavy lifting (semantic search, QA, metrics, cross‑notebook joins)
   - If NotebookLM disappears or changes format, your exports are still usable.

***

## 4. Why this is “optimal” (under current constraints)

- **You’re not fighting Google’s product limits.** There simply is no first‑party bulk export for sources; the best you can do is text snapshots plus URLs.[8][2][1]
- **You minimize lock‑in.** JSON/Markdown snapshots + your own DB schema = you can re‑index with any LLM or vector store later.[6][1]
- **You can keep your industrial architecture.** Same patterns as yt‑is:
  - WAL‑mode SQLite
  - Idempotent exports (hash + `last_exported_at`)
  - External provider abstraction (NotebookLM exporter looks like any other upstream provider).

***

If you tell me (a) roughly how many notebooks/sources you have, and (b) whether you’re okay using a third‑party actor like Apify vs. only local browser automation, I can sketch a concrete table schema + job design that slots into your existing “csf”/yt‑is pattern.  

## Human

500,000 video transcripts over 2000 channels.  Not use 3rd party, only local browser automation.

## Assistant

For **500,000 transcripts across 2,000 channels**, with **no third party** and **local browser automation only**, the optimal design is: **do not try to “download from NotebookLM” as your primary extraction path**; use NotebookLM only as a secondary batch text source, and build a **local persistent-browser export worker** around Chrome extensions plus Playwright CDP control. At that scale, the bottleneck is not DOM extraction itself but session durability, idempotent state, notebook sharding, and export recovery after partial failures.[1][2][3][4]

## Architecture

NotebookLM has no native bulk source-download feature, while local Chrome extensions now expose per-notebook export of source lists and content as JSON, ZIP, or Markdown with all processing occurring locally in the browser. Because Playwright can control a **persistent Chrome context** with loaded extensions and download handling, the most robust local approach is a **supervised export daemon**: one visible Chrome profile for auth and extension UI, one controller that attaches over CDP, and your own SQLite-backed job queue for notebooks, sources, export manifests, and retries.[1][2][3][5][4]

Use this split:
- **Primary transcript acquisition:** yt-dlp/API/direct methods outside NotebookLM for raw scale and determinism.[4]
- **Secondary NotebookLM export tier:** export normalized source text/content from notebook batches after ingestion into NotebookLM.[2]
- **Canonical storage:** your own DB/filesystem, not NotebookLM, because NotebookLM export is derivative and UI-mediated rather than a first-party durable archive.[2]

## Optimal design

For this workload, I would shard aggressively and keep NotebookLM notebooks **small and disposable** rather than building giant long-lived notebooks, because export/recovery time and UI fragility grow with notebook size while your own system already has persistent state patterns suited to batch processing. A practical shape is:[4]
- 200–400 source URLs per notebook, not thousands; this minimizes re-export blast radius when a notebook or session fails.[2]
- 1 export manifest per notebook containing notebook title, source metadata, hash, exported files, and completion status, written to SQLite in WAL mode just like your yt-is pipeline already does for multi-terminal safety.[4]
- Idempotent export stages: `queued -> opened -> extracted -> downloaded -> verified -> archived -> complete`, with restart at any boundary.[4]

The winning pattern is **extension-assisted extraction**, not pure selector scraping of every source panel, because the extension already packages notebook title, source URLs/types, content where available, and folder structure into JSON/ZIP while staying fully local. In other words: use browser automation to trigger a local exporter, not to manually scrape 500,000 transcript panes one at a time.[1][2]

## Browser worker

Run Chrome manually with a dedicated user-data directory, keep it logged into Google/NotebookLM, load only your chosen exporter extension, then attach Playwright over CDP or launch a persistent context directly with extension args. This reduces re-auth churn and gives you durable cookies, extension state, and stable download handling, which matters much more than headless speed for a half‑million-item archive.[3][5]

Minimal Node/TS launcher pattern:

```ts
import { chromium } from "playwright";
import path from "node:path";

const userDataDir = path.resolve("./chrome-profile");
const extensionPath = path.resolve("./extensions/notebooklm-exporter");

async function main() {
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    acceptDownloads: true,
    downloadsPath: path.resolve("./downloads"),
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`,
      "--disable-blink-features=AutomationControlled",
      "--no-first-run",
      "--no-default-browser-check"
    ]
  });

  const page = context.pages()[0] ?? await context.newPage();
  await page.goto("https://notebooklm.google.com/", { waitUntil: "domcontentloaded" });

  // Navigate to a notebook URL from your job queue.
  // Open extension side panel / injected UI.
  // Click "Extract All Sources" or equivalent export action.
  // Wait for download event, then register file path in SQLite manifest.

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByText("Download JSON").click()
  ]);

  const suggested = download.suggestedFilename();
  await download.saveAs(path.resolve("./downloads", suggested));
}
main();
```

This is the right control plane because persistent contexts support extension loading and download paths, which is exactly what local NotebookLM export workflows need.[5][3]

## Data model

You already have the right mental model from yt-is: keep **append-only state** plus resumable work units. I’d define at least:[4]

- `notebooks(notebook_id, title, shard_key, created_at, export_version, status, last_seen_at)`
- `sources(source_id, notebook_id, source_type, source_url, title, content_hash, exported_at, bytes, local_path, status)`
- `exports(export_id, notebook_id, format, started_at, completed_at, file_path, file_hash, status, error)`
- `download_archive(object_key, first_seen_at, last_verified_at, status)`  
- `session_health(browser_profile, last_ok_at, auth_state, consecutive_failures)`

Then enforce:
- Unique key on `source_url + content_hash` or a normalized source identifier to prevent duplicate archival across notebook reshuffles.[4]
- Export verification step: parse the JSON/ZIP after download and compare source count vs expected source count in the notebook UI before marking complete.[2]
- Retry windows and circuit breakers, the same way your transcript fetch chain already handles transient failure paths.[4]

## What I’d avoid

I would **not** rely on scraping the NotebookLM DOM row by row to expand each source and copy text, except as a fallback when the extension/export button fails, because UI selectors drift and DOM loops are much slower and less restartable than packaged exports. I would also avoid a single giant notebook strategy, because a partial export failure or auth lapse would force expensive rework and make verification harder than sharded notebook batches.[1][2][4]

## Recommendation

**Best local-only plan:**  
1. Keep direct transcript ingestion as tier 1 outside NotebookLM.[4]
2. Use NotebookLM only for batch enrichment/secondary extraction.
3. Build a **Playwright persistent-context export worker** that drives a **local NotebookLM exporter Chrome extension** and saves JSON/ZIP manifests to your filesystem.[3][1][2]
4. Treat every notebook as a resumable shard with SQLite-tracked export states and verification.[4]

**FACT:** local NotebookLM source-export extensions explicitly advertise one-click extraction and local-only processing, with JSON/ZIP/Markdown outputs containing source metadata and content where available.[1][2]
**CONSENSUS:** for long-running browser automation, persistent Chrome profiles plus download/event handling are more durable than ephemeral sessions.[5][3]
**SPECULATION, high confidence:** for 500k transcripts, NotebookLM should remain a secondary provider, not the core archive path, because the operational risk of UI/export coupling will dominate throughput before raw browser speed does.[4]

Concrete next step: design one **export-shard runner** that processes 50 notebooks end-to-end with manifest verification before scaling to the full 2,000-channel estate.

## Human

The issue with yt-dlp is ip banning.

## Assistant

You’re right to treat IP bans / throttling as the core failure mode for yt‑dlp at your scale. The pattern from recent reports is:

- YouTube rarely “permabans” casual users, but **heavy automated use absolutely triggers soft blocks, 403s, 429s, or aggressive throttling** (e.g. 100kbps) on an IP or range.[1][2][3]
- The only sustainable path for 500k+ videos is to treat **IP reputation and request shape as first‑class resources**, not an afterthought.[4][2][5]

Given your target (500k transcripts, 2,000 channels) and existing industrial pipeline, the optimal approach is:

## 1. Separate “transcript” from “bytes”

First, **minimize how often you touch YouTube at all**:

- Use YouTube Data API + RSS for enumeration and metadata; only hit watch pages or transcript endpoints when you actually need text.[6][7]
- Cache aggressively: your `transcripts.sqlite` with `transcriptcache` already gives you idempotency; ensure you never re‑fetch once `videoid+lang+source` is populated.[7]

Every unnecessary yt‑dlp call is just burning IP reputation and quota.

## 2. Slow down and randomize per IP

Evidence from users who hit “soft bans” with 403/429: **adding sleep intervals and backing off sharply reduces bans, at the cost of throughput.**[2][3][5][1]

- Use yt‑dlp’s delay flags per process:
  - `--sleep-interval` and `--max-sleep-interval` to introduce random jitter between requests.[1][2]
  - `--limit-rate` to avoid looking like a bulk downloader (e.g. cap to a few Mbps; throttling is used as a detection response).[3][2]
- Implement **backoff** when you see 429/403:
  - Immediate exponential backoff per IP (e.g. 15 min → 1 hr → multi‑hour) and write this into `channelcooldown`/`downloadarchive`–style tables so multiple terminals don’t keep hammering the same IP/channel combo.[6][7]

Rule of thumb from proxy guides: **constant, high‑rate scraping from one IP = ban; bursty traffic with sleeps and randomization = much less likely to be banned.**[5][4][2]

## 3. Use proper IP diversification, not just “hope”

For 500k transcripts you **cannot** rely on a single residential IP and polite delays; you need **planned IP diversity** or you’ll serialize the entire job behind YouTube’s safety limits.[4][2][5]

Without 3rd‑party scraping APIs, your main options are:

- **Multiple real networks you control** (multi‑WAN, home + office + mobile hotspots, etc.).  
- **Your own proxy pool** (e.g. a handful of VPSes you operate, each doing modest, well‑behaved traffic).  
- **Potentially Tor** (but generally too slow and often blocked for YouTube; usually not worth it at your scale).[8][2]

From proxy guides:  
- **Rotating proxies** (residential or mixed) are standard for avoiding “Too Many Requests” and 403/429 when scraping big playlists.[2][4]
- You can approximate this locally by routing yt‑dlp traffic through your own small proxy farm, with **per‑proxy concurrency and rate caps**.[4][2]

If you want to stay fully “local / self‑owned”:

- Spin up **N small nodes** (cheap VPS or Raspberry Pis on different ISPs) and run your transcript workers there, each:
  - With low concurrent yt‑dlp calls.
  - With built‑in sleeps and backoff.
- Or, build a **local proxy switcher**:
  - simple SOCKS/HTTP proxies on each node.
  - your main orchestrator rotates `--proxy [REDACTED]:port` for yt‑dlp on each job.[2][4]

Proxy vendors say: “use rotating proxies to prevent IP bans; yt‑dlp doesn’t rotate itself, so you must handle it externally.”[4][2]

## 4. Traffic shape: make your yt‑dlp usage look like a human fleet

Guides on avoiding bans in 2025 emphasize that it’s not *just* IP rotation: **request shape matters**.[5][6][2]

Concrete patterns to implement:

- **Mix operations**: don’t do 10k back‑to‑back transcript pulls from one channel; interleave channels and days so it looks like many humans watching/spreading views.[5][2]
- **Stagger jobs** across time zones; avoid obvious 24/7 flat rate scraping from any one IP.  
- **Randomize user‑agents** and client profiles where yt‑dlp supports it, but keep them plausible and consistent per IP (changing UA every request is also suspicious).[2][5]
- Monitor **error and status codes** centrally:
  - Spikes in 429 or recurring 403 at start of requests = treat that IP as “hot” and cool it down.[3][6]

The better anti‑ban articles are clear: **combine IP rotation + rate limiting + behavioral realism.**[5][2]

## 5. Escalation chain design

You already have a multi‑stage transcript chain (`yt‑dlp`, web client, cookies, Selenium, NotebookLM, Whisper). Extend it to include **IP health**:[7]

- If yt‑dlp on IP A gets repeated 429/403, mark IP A as “degraded” in a small `ip_health` table and:
  - Drop concurrency on that IP to 0 for some hours.
  - Route pending jobs to other IPs or back off globally.  
- Consider **alternate transcript providers** (API, caption scraping via browser automation) when yt‑dlp is degraded, so you still make progress without hammering a banned IP.[7]

This is similar to provider scoring in your `providerscore` table—just applied to IPs instead of transcript sources.[7]

## 6. What this means in practice

Putting it together, for yt‑dlp at your scale:

- **Do not** run big, constant, multi‑thread yt‑dlp jobs from one home IP and expect stability; soft bans and throttling are reported at much lower usage levels.[1][3]
- **Do**:
  - Strict per‑IP concurrency + sleep + backoff.
  - Spread load over multiple self‑owned IPs.
  - Treat IP health as a first‑class metric in your scheduler.
  - Prefer cached transcripts and other providers where possible.

**FACT:** Users scraping large channel/playlist sets with yt‑dlp hit 403/429 and “soft bans”; they mitigate with long random sleeps and sometimes IP changes.[3][1]
**FACT:** Proxy guides explicitly recommend rotating IPs and using delays to avoid rate limits and bans when using yt‑dlp at scale.[4][2]
**CONSENSUS:** Avoiding bans in 2025+ requires combining IP rotation, rate control, and realistic behavior, not any single trick alone.[6][2][5]
**SPECULATION (high confidence):** At your target of 500k transcripts, you’ll need **at least a small pool of distinct IPs** plus your existing escalation chain; pure “single‑IP + backoff” will make total run time unacceptably long.

If you tell me roughly how many physical/virtual nodes (IPs) you’re willing to run, I can sketch an explicit concurrency/backoff schedule (jobs/day/IP, expected completion time) for the 500k backlog.  

## Human

Only 1 node.

## Assistant

With a single node/IP, “optimal” for yt‑dlp means **accepting slowness** and designing around IP health as a hard constraint. The goal becomes: never look like a bulk downloader from that IP.

Below is what’s realistically safe and how I’d architect it.

***

## 1. Throughput expectations on 1 IP

From reports of 403/429/soft bans with yt‑dlp and general YouTube anti‑abuse guidelines:[1][2][3][4]

- Bursty, dense scraping from one IP (hundreds of hits/hour, 24/7) **does** trigger throttling or temporary IP blocks.[2][4][1]
- Adding **random delays** and keeping an IP’s usage closer to heavy human browsing substantially reduces issues, but throughput drops a lot.[3][5]

Rough safe ballpark (not a guarantee, just a planning target):

- On one home IP, **tens of videos/hour** with jitter and sleeps is more comfortable than hundreds/hour.
- 500k transcripts at, say, 1 transcript/minute average = ~347 days of wall clock. Faster is possible, but risk rises.

So the architecture should target **low sustained QPS**, strong caching, and robust backoff.

***

## 2. Design principles for the single‑IP scheduler

1. **Minimize calls**  
   - Never refetch a transcript once `transcripts.sqlite` has `videoid+lang+source` populated.[6]
   - Prefer YouTube Data API/RSS for enumeration, only hit watch/transcript when needed.[4][6]

2. **Serial or near‑serial fetching**  
   - Max 1–2 concurrent yt‑dlp jobs. Concurrency >3 from a single IP is where bans/throttling are commonly reported.[1][2]

3. **Randomized pacing**  
   - Use yt‑dlp’s `--sleep-interval` + `--max-sleep-interval` plus your own backoff. Example: 5–15s between videos normally, longer between channels.[7][3]

4. **IP‑health aware backoff**  
   - On transient errors (403, 429, “too many requests” or extreme throttling), back off for 30–60 minutes, then resume slowly.[2][4]

5. **Escalation chain**  
   - If yt‑dlp is blocked or heavily throttled, **pause** rather than hammer. Fallback to other providers only when they do not also hit YouTube from the same IP (e.g. local Whisper from already downloaded audio vs another HTTP client).[6]

***

## 3. Concrete yt‑dlp settings

For a “slow but safe” profile on one IP, something like:

- `--sleep-interval 5 --max-sleep-interval 20`  
  Random 5–20 seconds between downloads.[3][7]
- `--limit-rate 2M`  
  Cap effective download rate to ~2 MB/s to avoid looking like a bulk ripper.[2][3]
- `--retries 5 --fragment-retries 10 --retry-sleep 10`  
  Graceful retry with sleeps, not tight loops.

Wrapped in your scheduler, not just CLI.

***

## 4. Scheduler logic (pseudo)

You already have `downloadarchive`, `channelcooldown`, etc.; extend that for **IP health**.[6]

High‑level flow:

1. Main loop picks next pending video (respecting per‑channel cooldown, already‑downloaded guard).
2. If `ip_state = paused_until > now`, sleep and recheck later.
3. Run yt‑dlp; capture:
   - HTTP status (403/429/other),
   - speed (throttling),
   - success/failure,
   - error text.

4. On success:
   - Mark video complete (as you already do).
   - Log bytes/time; maybe adapt sleeps based on moving average.

5. On error:
   - If 403 or 429, set `ip_state.paused_until = now + backoff`, e.g. 30–60 minutes for first occurrence, exponential thereafter; mark the video as “retry after ip_cooldown”.
   - For other errors (geo, deleted, etc.), mark failed with reason, don’t retry.

Pseudo‑Python:

```python
BACKOFF_MIN = 30 * 60      # 30 minutes
BACKOFF_MAX = 12 * 60 * 60 # 12 hours

def compute_backoff(consecutive_429):
    base = BACKOFF_MIN * (2 ** (consecutive_429 - 1))
    return min(base, BACKOFF_MAX)

def should_pause_ip(ip_state, now):
    return ip_state.get("paused_until", 0) > now

def mark_ip_failure(ip_state, now):
    c = ip_state.get("consecutive_429", 0) + 1
    ip_state["consecutive_429"] = c
    pause = compute_backoff(c)
    ip_state["paused_until"] = now + pause

def mark_ip_success(ip_state):
    ip_state["consecutive_429"] = 0
    ip_state["paused_until"] = 0
```

Store `ip_state` in SQLite so all your terminals respect the same cooldown.

***

## 5. Tactics to reduce exposure further

On a single IP, you also want to reduce how “weird” the traffic looks:

- **Interleave channels & time**  
  Don’t hammer a single channel’s entire history in one go. Process a few from channel A, then B, etc. That’s closer to what a human fleet looks like than a linear walk of 1 channel’s 5,000‑video history.[5][3]

- **Avoid 24/7 flat‑line activity**  
  Run heavier during local “evening” hours, lighter overnight/mid‑day. Flattened, always‑on scraping on one ISP IP stands out.

- **Use a stable but plausible client profile**  
  If you’re using yt‑dlp’s `--user-agent` or client override, keep it consistent over time per IP; constant UA churn is suspicious too.[5][3]

***

## 6. What this implies for your 500k target

Given a single IP and conservative behavior:

- If you average **~1 transcript/minute** (including sleep), you’re in the ~500k / 347‑day range.
- If you push harder (say 3/min), you might shrink that to a few months but with much higher block risk.

So the trade‑off is:

- **Safe and slow**: Accept that this is a long‑running background job. Prioritize reliability over speed.
- **Fast and risky**: Increase concurrency/rate and expect periods where your IP is throttled or temporarily blocked, requiring manual interventions and downtime.

**FACT:** Users hitting YouTube hard with yt‑dlp from a single IP report 403/429 and throttling, and mitigate by introducing sleeps and reducing concurrency.[1][2]
**FACT:** Proxy guides for yt‑dlp explicitly say that without IP rotation you must keep rate low to avoid bans/blocks.[7][3]
**SPECULATION (medium‑high):** At your scale, on one IP, you can complete the 500k backlog, but it will be a **months‑long, background process** unless you accept higher ban risk.

If you want, I can sketch an explicit “daily schedule” (max jobs/day, expected duration) for a conservative vs aggressive profile so you can decide what risk level you’re comfortable with.

## Human

Focus on notebooklm.  I've downloaded 80,000+ transcripts so far and not been banned.  The resrictions around Notebooklm seem very minor.

## Assistant

That matches what’s visible in the ecosystem: NotebookLM’s “limits” are mostly **per‑source / per‑notebook caps and daily chat/report limits**, not hard IP‑style bans like YouTube applies to aggressive scrapers. You’ve effectively been doing 80k+ transcripts on a single node inside a product whose design assumes multi‑hour research sessions, so your usage pattern is much closer to “heavy power user” than “abusive bot.”[1][2][3][4]

A few grounding points:

- Official docs: free tier ≈ **100 notebooks × 50 sources** each, up to **500k words or 200 MB per source**. Paid tiers raise the number of sources/notebooks and daily chats/reports, but the per‑source size limits stay the same.[2][3][5][4][1]
- There’s no mention of IP bans or automated “scraping detection” – the control knobs are **quotas** (sources per notebook, notebooks per user, chat/report counts per day).[3][4][1][2]
- Chrome export extensions explicitly advertise *bulk export of sources, chats, and notes* in one click, with features like “bulk export all sources as Markdown or PDFs”, which implies Google isn’t currently policing that pattern aggressively.[6][7][8]

So from a risk perspective:

- **NotebookLM’s backend is quota‑governed, not IP‑governed.** You hit “too many chats/sources/notebooks” before you trigger anything like a network‑level ban.[4][1][2][3]
- Your 80k+ transcripts have almost certainly been sliced across many sources and notebooks and spread over time, which fits within the documented envelope (especially if you’re on a paid tier with 300–600 sources per notebook and higher daily chat/report ceilings).[5][2][4]
- Compared to directly hitting youtube.com or the transcript APIs with yt‑dlp, **NotebookLM is the safer place to “burn” queries** when you only have one IP, because Google is intentionally fronting it with account‑level limits instead of IP‑level anti‑scraping heuristics.[1][2][3][4]

Given that:

- It’s rational to **lean much harder on NotebookLM as your transcript/text provider** for this backlog, and treat yt‑dlp as the secondary path you use sparingly when NotebookLM can’t ingest or index something.
- Your main constraints to watch are:
  - sources per notebook & per account,
  - daily chat/report/overview limits,
  - and your own system’s ability to manage many shards and exports,  
  not IP bans.

**FACT:** NotebookLM’s documented limits are about number/size of sources, notebooks, and daily chats/reports; there is no mention of IP‑based blocking.[2][3][4][1]
**CONSENSUS:** Power‑user writeups frame the friction as “source caps and notebook caps”, not “risk of being banned for heavy use.”[9][10][2]
**SPECULATION (high confidence):** For a single‑node setup like yours, pushing most of the transcript load through NotebookLM (within plan quotas) is significantly safer, from an IP‑health standpoint, than pulling all 500k directly via yt‑dlp.

If you want, next step I can do is: design a specific NotebookLM sharding + export schedule (e.g., N notebooks × M sources each, daily export volume) that gets you through ~500k transcripts while staying comfortably inside the plan limits.

## Human

Notebooks can be temporary.  I'm on the pro plan.  the issue is mainly using the DOM to get the source contents.

## Assistant

Yes — if notebooks are temporary and you’re on Pro, then the real problem is **not NotebookLM limits**, it’s **reliably extracting source contents from the UI without fragile one-off DOM scraping**. The optimal path is to **stop thinking “scrape the source pane text”** and instead use a **Chrome extension injected into NotebookLM**, with Playwright only acting as the supervisor that opens notebooks, triggers export, and captures downloads.[1][2][3][4][5][6]

## Best approach

The cleanest architecture is:

- **Chrome extension = extraction layer**
  - Runs in the page context.
  - Uses DOM selectors plus `MutationObserver` to detect source lists/panels reliably.[2]
  - Adds its own Export button or command.
  - Collects source metadata and any text/content exposed in the page or returned through the extension’s internal calls.[1][2]

- **Playwright persistent context = orchestration layer**
  - Loads your extension in Chromium.
  - Opens notebook URLs.
  - Waits until notebook/source counts stabilize.
  - Clicks your extension’s export control.
  - Saves JSON/ZIP downloads to disk.[3][5]

That is better than raw Playwright DOM scraping because:
- Selector logic lives with the app in a content script, not in brittle external automation.[2]
- You can use `MutationObserver` and page-context APIs directly.[2]
- You can version the extraction logic independently of the browser runner.

## Why not plain DOM scraping

Plain Playwright/Selenium extraction of source contents is the wrong default for NotebookLM because:
- Panels are often virtualized/lazy-loaded, so “grab all `.source-content` elements” will miss data unless you force open/scroll every source.
- DOM structure can drift at any time.
- Long source lists make pure automation loops slow and hard to resume.

By contrast, extension-based exporters already package:
- notebook title,
- source list,
- source URLs/types,
- and source content where NotebookLM exposes it,
into JSON/ZIP outputs. That is much closer to a stable internal contract than manually traversing the visible DOM.[7][1]

## Recommended design

For your use case, I’d build this as a 3-part local system:

1. **Manifest V3 extension**
   - Content script injected on `https://notebooklm.google.com/*`
   - `MutationObserver` watches for source panel mount/update.[2]
   - Adds an “Export Sources JSON” button to the sources panel.
   - Extracts:
     - notebook id/title,
     - source ids/titles/types/URLs,
     - source content text if present,
     - extraction timestamps,
     - panel counts / verification metadata.

2. **Background/service worker**
   - Handles download packaging.
   - Receives content from the page script.
   - Builds downloadable JSON/ZIP blob locally.

3. **Playwright runner**
   - Launches persistent Chromium with the extension loaded.[5]
   - Visits notebook URLs from your queue.
   - Waits for extension ready state.
   - Clicks export.
   - Watches download directory.[3]
   - Writes manifest status to SQLite.

## Extraction strategy

You want **tiered extraction**, not one method:

### Tier 1: exported content already exposed
If the source content is already available through the page/extension export path, capture that directly into JSON. This is the cheapest and least fragile path.[1]

### Tier 2: source-card expansion
For sources where only metadata is present initially, the extension should:
- iterate source rows,
- click/open each row,
- wait for the content region to stabilize,
- capture normalized text,
- close/move on.

This is still “DOM use,” but it happens **inside the extension** with page-local observers instead of external brittle automation.[2]

### Tier 3: fallback raw panel snapshot
If a source fails full extraction, save:
- source title,
- URL/type,
- visible rendered text,
- extraction error flag.

That gives you partial fidelity without stalling the whole notebook.

## Concrete implementation sketch

### Content script idea
```ts
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

function text(el?: Element | null) {
  return (el?.textContent || "").replace(/\s+/g, " ").trim();
}

async function waitForSelector(selector: string, timeout = 15000): Promise<Element> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const el = document.querySelector(selector);
    if (el) return el;
    await sleep(250);
  }
  throw new Error(`Timeout waiting for ${selector}`);
}

async function extractSources() {
  const notebookTitle = text(document.querySelector("h1")) || document.title;
  const rows = Array.from(document.querySelectorAll("[data-source-id], [role='listitem']"));
  const results: any[] = [];

  for (const row of rows) {
    const title = text(row.querySelector("h2, h3, [data-testid='source-title']")) || text(row);
    const url = (row.querySelector("a[href]") as HTMLAnchorElement | null)?.href || null;

    (row as HTMLElement).click();
    await sleep(800);

    const panel = document.querySelector("[data-testid='source-detail'], [role='dialog'], .source-detail-panel");
    const content = text(panel);

    results.push({
      title,
      url,
      content,
      extractedAt: new Date().toISOString(),
    });
  }

  return {
    notebookTitle,
    sourceCount: results.length,
    sources: results,
  };
}
```

This selector set is intentionally generic; in practice, you’d tighten it once you inspect current NotebookLM markup.[2]

### Download from extension
```ts
function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
```

### Playwright supervisor
```ts
import { chromium } from "playwright";
import path from "node:path";

const extensionPath = path.resolve("./extension");
const userDataDir = path.resolve("./profile");

(async () => {
  const context = await chromium.launchPersistentContext(userDataDir, {
    channel: "chromium",
    headless: false,
    acceptDownloads: true,
    downloadsPath: path.resolve("./downloads"),
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`,
    ],
  });

  const page = context.pages()[0] || await context.newPage();
  await page.goto("https://notebooklm.google.com/notebook/NOTEBOOK_ID");

  await page.waitForLoadState("domcontentloaded");
  await page.getByText("Export Sources JSON").click();

  const download = await page.waitForEvent("download");
  await download.saveAs(path.resolve("./downloads", download.suggestedFilename()));

  await context.close();
})();
```
Persistent Chromium with extension loading is the officially documented pattern for Playwright + Chrome extensions.[5]

## What I would optimize for

Given your scale, optimize for these in order:

1. **Deterministic export artifact per notebook**  
   JSON/ZIP file, not ad hoc copied text.[7][1]

2. **Verifier, not extractor cleverness**  
   Compare expected source count vs exported source count, and retry only missing items.

3. **Disposable notebooks**  
   Since notebooks can be temporary, shard them to simplify recovery.

4. **Extension-first logic**  
   Keep all NotebookLM-specific extraction in one extension repo; keep your Playwright runner generic.

## Recommendation

**Optimal local-only design:** build your own MV3 NotebookLM exporter extension, use `MutationObserver` for resilient source-panel handling, and use Playwright persistent Chromium only to drive notebook navigation and download capture. That gives you a much more stable contract than trying to pull source contents directly from the DOM with plain automation, while still staying entirely local and under your control.[3][5][1][2]

**FACT:** browser-only NotebookLM extensions already use Manifest V3, content scripts, DOM selectors, and `MutationObserver` to manipulate NotebookLM’s UI.[2]
**FACT:** Playwright supports Chrome extensions only in Chromium persistent contexts, with configurable download paths.[5][3]
**FACT:** existing NotebookLM exporters package source list, metadata, and available source content into JSON/ZIP outputs.[7][1]
**SPECULATION, high confidence:** for your workload, a custom extension plus Playwright supervisor will be materially more reliable than pure Playwright/Selenium DOM scraping of the source pane.

Would you like a concrete MV3 extension skeleton plus the exact message flow between content script, service worker, and Playwright runner?

## Human

Playwright script to automate NotebookLM Export Pro extension
How to use Playwright with Chrome extensions for NotebookLM source extraction

## Assistant

Yes. The key is to use **Chromium + persistent context + extension page access**, then automate either the extension’s popup/page directly or trigger its injected UI inside NotebookLM. For NotebookLM source extraction specifically, existing exporter extensions describe a flow of opening a notebook, opening the extension side panel, clicking **“Extract All Sources”**, then downloading markdown/JSON/ZIP outputs, which is exactly the flow Playwright can supervise.[1][2][3][4][5]

## Setup pattern

Playwright only supports Chrome extensions in a **persistent Chromium context**, not a normal ephemeral browser context. The durable setup is:[2][1]

- Use `launchPersistentContext(...)` with a real `userDataDir` so Google auth and NotebookLM session state survive runs.[2]
- Load the unpacked extension with:
  - `--disable-extensions-except=...`
  - `--load-extension=...`[6][1]
- Discover the extension ID through its service worker, then open `chrome-extension://<id>/popup.html` if the extension exposes a popup page.[5][1]

## Node example

This is the most practical starting point because extension automation examples are best documented in Playwright’s Node docs.[1][5]

```ts
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs/promises';

const EXT_PATH = path.resolve('./extensions/notebooklm-export-pro'); // unpacked extension dir
const USER_DATA_DIR = path.resolve('./chrome-profile-notebooklm');
const DOWNLOADS_DIR = path.resolve('./downloads');

async function ensureDir(dir: string) {
  await fs.mkdir(dir, { recursive: true });
}

async function getExtensionId(context: Awaited<ReturnType<typeof chromium.launchPersistentContext>>) {
  let [serviceWorker] = context.serviceWorkers();
  if (!serviceWorker) {
    serviceWorker = await context.waitForEvent('serviceworker');
  }
  const swUrl = serviceWorker.url();
  return swUrl.split('/')[2];
}

async function clickIfVisible(page, selectors: string[]) {
  for (const selector of selectors) {
    const loc = page.locator(selector).first();
    if (await loc.count()) {
      if (await loc.isVisible().catch(() => false)) {
        await loc.click();
        return true;
      }
    }
  }
  return false;
}

async function waitForNotebookReady(page) {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(2000);
}

async function exportNotebook(context, notebookUrl: string) {
  const page = context.pages()[0] ?? await context.newPage();
  await page.goto(notebookUrl, { waitUntil: 'domcontentloaded' });
  await waitForNotebookReady(page);

  const extensionId = await getExtensionId(context);

  // Option A: open extension popup directly if it exposes popup.html
  const popup = await context.newPage();
  await popup.goto(`chrome-extension://${extensionId}/popup.html`);

  // If the extension needs the active NotebookLM tab, keep notebook page focused first.
  await page.bringToFront();
  await page.waitForTimeout(500);

  // Then interact with popup page.
  await popup.bringToFront();
  await popup.waitForLoadState('domcontentloaded');

  const extracted =
    await clickIfVisible(popup, [
      'button:has-text("Extract All Sources")',
      'button:has-text("Extract sources")',
      'button:has-text("Export Sources")'
    ]);

  if (!extracted) {
    throw new Error('Could not find extract button in popup');
  }

  await popup.waitForTimeout(1500);

  const [download] = await Promise.all([
    page.waitForEvent('download').catch(() => popup.waitForEvent('download')),
    clickIfVisible(popup, [
      'button:has-text("Download JSON")',
      'button:has-text("Download ZIP")',
      'button:has-text("Download Markdown")',
      'a:has-text("Download JSON")',
      'a:has-text("Download ZIP")'
    ])
  ]);

  if (!download) {
    throw new Error('No download event captured');
  }

  const filename = download.suggestedFilename();
  const outPath = path.join(DOWNLOADS_DIR, filename);
  await download.saveAs(outPath);

  await popup.close();
  return outPath;
}

(async () => {
  await ensureDir(DOWNLOADS_DIR);

  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: 'chromium',
    headless: false,
    acceptDownloads: true,
    downloadsPath: DOWNLOADS_DIR,
    args: [
      `--disable-extensions-except=${EXT_PATH}`,
      `--load-extension=${EXT_PATH}`,
      '--no-first-run',
      '--no-default-browser-check'
    ]
  });

  try {
    const notebookUrl = 'https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID';
    const saved = await exportNotebook(context, notebookUrl);
    console.log('Saved export:', saved);
  } finally {
    // keep open for debugging if needed
    // await context.close();
  }
})();
```

This follows the documented extension pattern: persistent context, wait for service worker, derive extension ID, then open the popup URL directly.[5][1]

## Python example

Python works too, and the Playwright Python extension pattern mirrors the same persistent-context approach.[6]

```python
from pathlib import Path
from playwright.sync_api import sync_playwright

EXT_PATH = str(Path("./extensions/notebooklm-export-pro").resolve())
USER_DATA_DIR = str(Path("./chrome-profile-notebooklm").resolve())
DOWNLOADS_DIR = str(Path("./downloads").resolve())

def get_extension_id(context):
    service_workers = context.service_workers
    sw = service_workers[0] if service_workers else context.wait_for_event("serviceworker")
    return sw.url.split("/")[2]

def main():
    Path(DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            channel="chromium",
            headless=False,
            accept_downloads=True,
            downloads_path=DOWNLOADS_DIR,
            args=[
                f"--disable-extensions-except={EXT_PATH}",
                f"--load-extension={EXT_PATH}",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        extension_id = get_extension_id(context)
        popup = context.new_page()
        popup.goto(f"chrome-extension://{extension_id}/popup.html")

        popup.get_by_role("button", name="Extract All Sources").click()
        popup.wait_for_timeout(1500)

        with popup.expect_download() as dl_info:
            popup.get_by_role("button", name="Download JSON").click()

        download = dl_info.value
        download.save_as(str(Path(DOWNLOADS_DIR) / download.suggested_filename))

        # context.close()

if __name__ == "__main__":
    main()
```

The exact button names may differ by extension version, so the selectors should be treated as **likely**, not guaranteed.[3][4]

## NotebookLM-specific tips

For NotebookLM extraction, the most important implementation detail is whether the extension acts through:
1. a popup page,
2. a side panel,
3. or a content script injecting controls into NotebookLM itself.[4][3]

That gives you two automation strategies:

- **Popup-driven:** open `chrome-extension://<id>/popup.html` and click buttons there.[1][5]
- **In-page driven:** once the extension is loaded, interact with buttons injected into the NotebookLM page, such as “Extract All Sources,” if they are rendered into the DOM.[3]

A reliable fallback is to inspect the extension manifest and find:
- `action.default_popup`
- `side_panel.default_path`
- `content_scripts`
so you know whether to automate popup, side panel, or NotebookLM DOM.

## Practical caveats

- The Chrome Web Store build itself cannot be loaded by path; for Playwright you generally want an **unpacked extension directory** so you can pass it to `--load-extension=...`.[1]
- Extension UI text and selectors can drift, so your automation should prefer resilient matching by visible button text and support multiple labels.[4][3]
- If the extension downloads from the active NotebookLM tab, keep the notebook tab open and authenticated in the same persistent profile before invoking the popup.[2][3]

## Recommended flow

For your use case, I’d implement this exact sequence:

1. Launch persistent Chromium with your NotebookLM profile and unpacked extension loaded.[2][1]
2. Open notebook URL and wait for it to stabilize.
3. Open extension popup via `chrome-extension://.../popup.html`.[5][1]
4. Click **Extract All Sources**.[3]
5. Wait for extraction complete state or source count.
6. Click **Download JSON** first; ZIP/Markdown second if needed.[4][3]
7. Save the file and record notebook ID, filename, and source count in your own manifest.

**FACT:** Playwright extension automation requires Chromium with a persistent context and extension-loading args.[6][1][2]
**FACT:** exporter-style NotebookLM extensions advertise a workflow of opening a notebook, triggering extraction, and downloading source outputs.[3][4]
**SPECULATION, high confidence:** the fastest path to a stable pipeline is to inspect the extension manifest once, then automate whichever of popup, side panel, or injected page controls it actually exposes.

If you want, I can turn this into a more production-ready runner with retry logic, manifest logging, and selector fallbacks for NotebookLM Export Pro specifically.

## Human

Handle multiple NotebookLM notebooks in Playwright loop
Download and save exported markdown files automatically
turn this into a more production-ready runner with retry logic, manifest logging, and selector fallbacks for NotebookLM Export Pro specifically.

Why focus on NotebookLM Export Pro?

## Assistant

Focus on **Export Pro** only if it is the extension you already installed or if its injected UI is the most stable in your environment; it is not the only option. I focused on it because it explicitly claims NotebookLM-integrated export buttons, Markdown export, bulk source export, and one-click workflows that map cleanly to Playwright automation, but if your actual installed extension is `NotebookLM Sources Exporter` or another exporter, the runner should target that instead.[1][2][3][4]

## Why Export Pro

`NotebookLM Export Pro` advertises direct export from NotebookLM to Markdown, plain text, PDF, LaTeX, and Notion, including downloading sources, chat history, and notes, plus selective export using NotebookLM checkboxes. That makes it attractive for automation because the extension appears to inject an **Export** button directly into NotebookLM panels, which is easier to drive than opening a browser-action popup and trying to synchronize active-tab state.[1]

But there is a more important caveat: `NotebookLM Sources Exporter` and `NoteBookLM Exporter` look more source-centric, and one of them explicitly documents JSON/ZIP packaging with per-source Markdown files, which may actually fit your source-extraction goal better than Export Pro’s broader “export everything” positioning. So the production runner should be **extension-agnostic with selector fallbacks**, then you pin the extension after one inspection pass.[3][4]

## Production runner

Below is a more production-ready **Node/TypeScript Playwright runner** for multiple notebooks, retries, manifest logging, auto-saved Markdown downloads, and selector fallbacks. It assumes:
- persistent Chromium profile,
- unpacked extension loaded,
- a notebook URL list,
- and an extension that either injects export controls into the NotebookLM page or exposes a popup page.[5][6][7]

```ts
import { chromium, Page, BrowserContext, Download } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

type NotebookJob = {
  notebookId: string;
  url: string;
};

type ManifestRow = {
  notebookId: string;
  url: string;
  status: "ok" | "retry" | "failed";
  attempts: number;
  startedAt: string;
  finishedAt: string;
  outputFile?: string;
  sourceCountHint?: number | null;
  error?: string;
};

const EXT_PATH = path.resolve("./extensions/notebooklm-exporter");
const USER_DATA_DIR = path.resolve("./chrome-profile-notebooklm");
const DOWNLOADS_DIR = path.resolve("./downloads");
const MANIFEST_PATH = path.resolve("./output/notebooklm-export-manifest.ndjson");
const MAX_RETRIES = 3;

const NOTEBOOKS: NotebookJob[] = [
  { notebookId: "nb-001", url: "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID_1" },
  { notebookId: "nb-002", url: "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID_2" }
];

const SELECTORS = {
  inPageExportButtons: [
    'button:has-text("Export")',
    'button:has-text("Export Pro")',
    'button:has-text("Export Sources")',
    'button:has-text("Extract All Sources")'
  ],
  markdownButtons: [
    'button:has-text("Markdown")',
    'button:has-text("Download Markdown")',
    'button:has-text(".md")',
    'text=Markdown'
  ],
  sourcePanelHints: [
    'text=Sources',
    '[role="tab"]:has-text("Sources")',
    '[aria-label*="Sources"]'
  ],
  popupExtractButtons: [
    'button:has-text("Extract All Sources")',
    'button:has-text("Export Sources")',
    'button:has-text("Export")'
  ],
  popupMarkdownButtons: [
    'button:has-text("Download Markdown")',
    'button:has-text("Markdown")',
    'a:has-text("Download Markdown")'
  ]
};

async function ensureDir(dir: string) {
  await fs.mkdir(dir, { recursive: true });
}

async function appendManifest(row: ManifestRow) {
  await fs.appendFile(MANIFEST_PATH, JSON.stringify(row) + "\n", "utf8");
}

async function getExtensionId(context: BrowserContext): Promise<string | null> {
  let [sw] = context.serviceWorkers();
  if (!sw) {
    try {
      sw = await context.waitForEvent("serviceworker", { timeout: 5000 });
    } catch {
      return null;
    }
  }
  return sw.url().split("/")[2] ?? null;
}

async function clickFirstVisible(page: Page, selectors: string[], timeout = 1500): Promise<string | null> {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      await locator.waitFor({ state: "visible", timeout });
      await locator.click();
      return selector;
    } catch {}
  }
  return null;
}

async function countSourcesHint(page: Page): Promise<number | null> {
  const candidates = [
    '[role="tab"]:has-text("Sources")',
    'text=/Sources\\s*\\(\\d+\\)/',
    'text=/\\d+\\s+sources/i'
  ];
  for (const selector of candidates) {
    try {
      const text = await page.locator(selector).first().textContent({ timeout: 1000 });
      if (!text) continue;
      const m = text.match(/(\d+)/);
      if (m) return Number(m[1]);
    } catch {}
  }
  return null;
}

async function waitNotebookReady(page: Page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(2500);
  await clickFirstVisible(page, SELECTORS.sourcePanelHints, 1200).catch(() => null);
  await page.waitForTimeout(1000);
}

async function saveDownload(download: Download, notebookId: string): Promise<string> {
  const suggested = download.suggestedFilename();
  const safeName = suggested.endsWith(".md") ? suggested : `${notebookId}-${suggested}`;
  const outPath = path.join(DOWNLOADS_DIR, safeName);
  await download.saveAs(outPath);
  return outPath;
}

async function tryInPageExport(page: Page, notebookId: string): Promise<string | null> {
  const clicked = await clickFirstVisible(page, SELECTORS.inPageExportButtons, 2500);
  if (!clicked) return null;

  await page.waitForTimeout(1200);

  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 15000 }).catch(() => null),
    clickFirstVisible(page, SELECTORS.markdownButtons, 4000)
  ]);

  if (!download) return null;
  return await saveDownload(download, notebookId);
}

async function tryPopupExport(context: BrowserContext, page: Page, notebookId: string): Promise<string | null> {
  const extensionId = await getExtensionId(context);
  if (!extensionId) return null;

  const popup = await context.newPage();
  try {
    await page.bringToFront();
    await popup.goto(`chrome-extension://${extensionId}/popup.html`, { waitUntil: "domcontentloaded" });
    await popup.waitForTimeout(1200);

    const extracted = await clickFirstVisible(popup, SELECTORS.popupExtractButtons, 2500);
    if (!extracted) return null;

    await popup.waitForTimeout(1500);

    const [download] = await Promise.all([
      popup.waitForEvent("download", { timeout: 15000 }).catch(() => null),
      clickFirstVisible(popup, SELECTORS.popupMarkdownButtons, 4000)
    ]);

    if (!download) return null;
    return await saveDownload(download, notebookId);
  } finally {
    await popup.close().catch(() => {});
  }
}

async function exportNotebook(context: BrowserContext, job: NotebookJob, attempt: number): Promise<ManifestRow> {
  const page = context.pages()[0] ?? await context.newPage();
  const startedAt = new Date().toISOString();

  try {
    await page.goto(job.url, { waitUntil: "domcontentloaded", timeout: 30000 });
    await waitNotebookReady(page);

    const sourceCountHint = await countSourcesHint(page);

    let outputFile = await tryInPageExport(page, job.notebookId);
    if (!outputFile) {
      outputFile = await tryPopupExport(context, page, job.notebookId);
    }
    if (!outputFile) {
      throw new Error("No export path succeeded: in-page and popup flows both failed");
    }

    return {
      notebookId: job.notebookId,
      url: job.url,
      status: "ok",
      attempts: attempt,
      startedAt,
      finishedAt: new Date().toISOString(),
      outputFile,
      sourceCountHint
    };
  } catch (err: any) {
    return {
      notebookId: job.notebookId,
      url: job.url,
      status: attempt < MAX_RETRIES ? "retry" : "failed",
      attempts: attempt,
      startedAt,
      finishedAt: new Date().toISOString(),
      error: String(err?.message || err)
    };
  }
}

async function run() {
  await ensureDir(DOWNLOADS_DIR);
  await ensureDir(path.dirname(MANIFEST_PATH));

  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    channel: "chromium",
    headless: false,
    acceptDownloads: true,
    downloadsPath: DOWNLOADS_DIR,
    args: [
      `--disable-extensions-except=${EXT_PATH}`,
      `--load-extension=${EXT_PATH}`,
      "--no-first-run",
      "--no-default-browser-check"
    ]
  });

  try {
    for (const job of NOTEBOOKS) {
      let attempt = 1;
      while (attempt <= MAX_RETRIES) {
        const row = await exportNotebook(context, job, attempt);
        await appendManifest(row);

        if (row.status === "ok" || row.status === "failed") break;

        const backoffMs = attempt * 5000;
        await new Promise(r => setTimeout(r, backoffMs));
        attempt += 1;
      }
    }
  } finally {
    // leave open for debugging if desired
    // await context.close();
  }
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
```

## What this runner does

It loops through many notebook URLs, retries failures up to a cap, and writes one NDJSON manifest row per attempt so you can resume or audit later. That matches your existing “industrial architecture” instincts: append-only logs, resumability, and selector fallbacks rather than a single brittle happy path.[8]

The runner also prefers **Markdown downloads** first because Export Pro explicitly advertises Markdown export for notes, sources, and chat history, which fits your downstream Obsidian/RAG-style text workflows better than PDF. If your actual source-focused extension produces ZIP with per-source Markdown files, adapt `saveDownload()` to preserve the ZIP and unpack later instead of forcing plain `.md` flows.[4][3][1]

## Recommended selector strategy

Do not hardcode one selector set and hope. Use three layers:

- **Primary:** visible button text, because these export extensions market themselves around user-facing labels like Export, Markdown, Download Markdown, and Extract All Sources.[3][1]
- **Secondary:** aria labels, role selectors, or nearby panel text such as Sources/Chat/Studio if UI labels drift.
- **Tertiary:** extension manifest inspection, so you know whether the real UI entry point is popup, side panel, or injected page control.[5]

If you want “NotebookLM Export Pro specifically,” inspect the unpacked extension once:
- `manifest.json`
- popup HTML path
- content script selectors
- button text strings  
Then replace the fallback arrays with exact selectors from the extension codebase. That is the fastest route to reliability.

## Why not only Export Pro

I would not lock the architecture to Export Pro unless you have already validated that:
- it exports **source contents** the way you need,
- it exposes stable controls,
- and it performs better than the more source-oriented alternatives.[4][1][3]

There are at least three extension classes here:
- **general export** tools like Export Pro, broader but possibly noisier for source extraction,[1]
- **source exporters** that package notebook/source metadata and source content into JSON/ZIP or per-source Markdown,[4]
- **content-specific exporters** for notes/chat only.[9][10]

For your use case, **source-first exporters** may be a better fit than “export everything” tools.[3][4]

**FACT:** Export Pro explicitly advertises Markdown export, direct NotebookLM integration, and one-click export of sources, chats, and notes.[1]
**FACT:** other NotebookLM exporters explicitly advertise source export as JSON/ZIP or ZIP of Markdown/HTML files, which may align more directly with source extraction.[3][4]
**SPECULATION, high confidence:** the best production approach is an extension-agnostic Playwright runner plus one-time extension inspection, not hard-coding your system to Export Pro before verifying its actual source-export behavior.

Would you like the next step to be a concrete SQLite-backed manifest schema and resume algorithm, or a version of this runner in Python instead of TypeScript?

## Human

provide a list of clickable links for the extensions that may help with exports or downloads form notebooklm

## Assistant

## NotebookLM Export Extensions

Here’s a curated list of Chrome extensions for exporting sources, notes, and content from NotebookLM, with clickable links. I prioritized ones with **source export**, **Markdown/ZIP/JSON formats**, and **bulk capabilities**, based on 2026 reviews and descriptions.[1][2][3][4][5][6]

| Extension | Key Features | Chrome Web Store Link |
|-----------|--------------|-----------------------|
| **NotebookLM Export Pro** | Sources + chats + notes to Markdown, PDF, Notion; bulk export, selective sources, one-click from NotebookLM panels.[1] | [Install](https://chromewebstore.google.com/detail/notebooklm-export-pro/fhplgheiijiledgfpabdiiheblmjoaog) |
| **NotebookLM Sources Exporter** | Bulk extract all sources as Markdown files; view/browse/download; perfect for backing up source content.[3][2] | [Install](https://chromewebstore.google.com/detail/notebooklm-sources-export/ildjnemeokopkjjkkhooonanjckcclfj) |
| **NotebookLM Ultra Exporter** | Notes/reports/sources to Markdown, PDF, ZIP batch; slides, mindmaps, flashcards, tables; bulk source download.[4] | [Install](https://chromewebstore.google.com/detail/notebooklm-ultra-exporter/afchokljnhhggkhedfbmkcmdagjmjchj) |
| **NotebookLM Tools** | Per-notebook source list + content + folder structure as JSON/ZIP; archive/share/re-import sources.[2] | [Blog/Install](https://www.nlmtools.com/blog/notebooklm-export-sources) |
| **NoteBookLM Exporter** | Notes, reports, chats to Markdown, Word, PDF; selective messages/notes.[5] | [Install](https://chromewebstore.google.com/detail/notebooklm-exporter/gejoojiehhghphimkfaccjmnmadahblc) |
| **Notebooklm Tex, MD Exporter** | Sources/notes to Markdown, LaTeX, Tex; focused on text formats.[6] | [Install](https://chromewebstore.google.com/detail/notebooklm-tex-md-exporte/fjbhcpgodilncafncjpggobiaknjmcbn) |
| **NotebookLM ExportKit** | Notes/reports to Markdown, Word, PPT, CSV; Anki export; Google Drive sync.[7] | [Search Chrome Store](https://chrome.google.com/webstore/search/notebooklm%20exportkit) |

## Quick Notes

- **Source-focused:** “NotebookLM Sources Exporter” and “NotebookLM Tools” explicitly target source lists/content/folder structure as Markdown/JSON/ZIP, ideal for your use case.[2][3]
- **Full‑export:** “Export Pro” and “Ultra Exporter” do sources + notes/chats/slides, good if you want everything in one pass.[4][1]
- **Test before automating:** Install 2–3, open a test notebook, trigger exports manually, and inspect the output format (JSON vs ZIP vs plain Markdown) to pick the one with the most stable UI and desired file shape.[1][2]
- **Local unpacked:** For Playwright automation, download the `.crx` file, unpack it (`unzip -d ./extension crx`), and load the directory via `--load-extension=...`.[8]

**FACT:** These extensions explicitly advertise NotebookLM source export to Markdown, JSON, ZIP, and PDF formats, with bulk and selective options.[3][5][2][4][1]
**CONSENSUS:** NotebookLM exporters are the standard workaround for bulk source/notes download, as NotebookLM lacks native export buttons.[2][4][1]
