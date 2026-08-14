---
title: "with 'bulk image downloader' why are images blurred out, when on the web page they are not?"
date: "2026-04-25"
mode: "CONCISE"
uuid: "62aeea43-16d9-4ef3-81c4-25fcaa4bb048"
entry_count: 4
---

## Human

with 'bulk image downloader' why are images blurred out, when on the web page they are not?

## Assistant

The blurred images issue with bulk image downloaders typically stems from **lazy loading** and **thumbnail vs. full-resolution extraction**. Here are the main causes:[1]

## Lazy Loading

Many modern websites only load thumbnail or low-resolution placeholder images initially, with full-resolution versions loading only when users scroll or interact with the page. Bulk image downloaders that don't simulate scrolling or JavaScript execution capture these low-res placeholders instead of the actual full-resolution images. The images appear sharp in your browser because you're viewing them as the page renders progressively—the higher-resolution versions load dynamically after initial page load.[2][1]

## Image Delivery Methods

Websites use increasingly sophisticated image delivery to prevent bulk downloads. This includes:[3]
- **Blob URLs and dynamic image generation** where images are created on-demand via JavaScript
- **CDN transformations** that serve different resolutions based on request parameters
- **Carousel/gallery systems** that load only visible images
- **API-driven image delivery** from sources the downloader can't detect

When a bulk downloader can't access the full delivery pipeline, it grabs whatever static image URLs it finds—often compressed previews.[2]

## Incomplete JavaScript Rendering

Basic bulk downloaders extract images from static HTML without executing JavaScript. Since many galleries load images dynamically through scripts, the tool misses high-resolution sources entirely and captures only placeholder images currently in the DOM.[2]

**To get full-resolution images, you'd need a tool that:**
- Executes JavaScript and waits for dynamic content to render
- Simulates scrolling through infinite-scroll pages
- Detects and follows API calls for image data
- Extracts full-resolution URLs from srcset attributes or CDN parameters

Are you working with a specific website where this is happening, or is this a general issue across multiple sites you're trying to download from?

## Human

How to force Bulk Image Downloader to grab full resolution images

## Assistant

Bulk Image Downloader has several built-in mechanisms to force full-resolution captures. Here's how to maximize resolution extraction:

## Filter Settings

Verify your filter is set to **"Thumbnailed images only"** (press Alt+1). This tells BID to follow thumbnail links to their full-resolution versions rather than downloading the thumbnails directly. If you're using the Queue Manager, apply the same filter there—Queue Manager settings override BID's default settings.[1]

## Resolution Selection

In the BID settings, explicitly choose **Desktop resolution over Mobile**. Mobile pages often serve lower-resolution images. BID also handles **srcset images**, which specify multiple resolution options; selecting Desktop ensures BID prioritizes the highest available resolution from the srcset attribute.[2]

## Enable JavaScript Rendering

Toggle **JavaScript loading on** in your settings instead of HTML-only mode. This is slower but critical for lazy-loaded galleries—without JavaScript execution, BID captures only thumbnail placeholders already in the DOM. JavaScript rendering allows the tool to trigger dynamic image loading and access full-resolution URLs loaded by scripts.[2]

## Advanced Configuration: Include List

For sites BID doesn't recognize, use the **Include List** in Advanced Configuration:[3]

- Add regex patterns matching full-resolution image URLs. For example: `<example.com/pics/fullsized/>`
- Prefix with `*` to follow links to even larger/original images: `*<example.com/pics/original/>`
- Prefix with `**` for non-standard thumbnail detection: `**<thumbnailgenerator.php?id=>`
- For infinite-scroll galleries, use `**` prefix to enable auto-scrolling: `**<gallery-container>`[3]

## JavaScript Site Configuration

If a gallery uses endless scrolling (no "next" page links), prefix the regex in your Include List with `**` to make BID auto-scroll the page and capture dynamically-loaded images.[3]

**Critical limitation**: If a website uses blob URLs, API-driven image delivery, or anti-scraping protection, even these settings won't bypass the constraints—BID extracts only what's publicly available in the HTML/JavaScript response.[3]

Are you working with a specific gallery platform (WordPress, Shopify, Pinterest, etc.) or a custom site? The Include List regex patterns depend on the site's URL structure.

## Human

BID advanced config options for ignoring thumbnails

## Assistant

Based on the official BID documentation, here are the advanced config options specifically for ignoring thumbnails:[1]

## Ignore List Configuration

The **Ignore List** in Advanced Configuration filters out links misidentified as images. Add regex patterns to exclude thumbnail URLs you don't want:[1]

```
<thumbnail-pattern-here>
```

For example, if thumbnails follow the pattern `site.com/thumbs/img_small.jpg`, add:
```
<site.com/thumbs/img_small>
```

BID will discard any matching links.[1]

## Override Ignore Rules with Force Prefix

If BID keeps downloading the wrong thumbnails despite your Ignore List, prefix the ignore rule with `**` to force BID to apply it strictly. This overrides any conflicting Include List entries:[1]

```
**<unwanted-thumbnail-pattern>
```

This forces BID to ignore that pattern even if other rules would include it.[1]

## Non-Thumbnailed Image Types

In the **Images** section of Advanced Configuration, uncheck specific image types you want BID to ignore when processing embedded images. This prevents BID from treating certain image file types (SVG, GIF, etc.) as valid candidates.[1]

## Delete Small Images Automatically

Enable **"Delete images smaller than [X] KB"** to automatically remove thumbnail files after downloading. Set the threshold based on your typical full-resolution file size—BID will discard anything smaller.[1]

## Include List Priority

The Include List overrides Ignore List entries unless you prefix the Ignore rule with `**`. So if you want to force exclusion of certain patterns, always use `**` prefix on those Ignore List rules.[1]

The key strategy: use the `**`-prefixed Ignore List patterns to block thumbnail URLs completely, preventing BID from even attempting to follow them to full-resolution versions.[1]

## Human

what about for yandex site?

## Assistant

On Yandex Images specifically, BID tends to grab the preview/thumbnail layer because Yandex wraps full‑res URLs behind JS, parameters, and an intermediate viewer. FACT, medium confidence. To bias BID toward full‑res and away from thumbnails, you typically need a site‑specific config rather than only generic “ignore thumbnails” rules. CONSENSUS, medium confidence.[1][2][3]

## What Yandex is doing

Yandex Images usually serves images via:

- A grid of search thumbnails, each linking to a JS viewer rather than the raw file. FACT, high confidence.[1]
- Full‑size images loaded dynamically when you open the viewer, sometimes via additional request params or a redirect chain. FACT, medium confidence.[1]

So if you point BID at the search‑results page and let it scrape `<img>` tags, it mostly sees those low‑res thumbnails, not the final original URLs. FACT, high confidence.[3][1]

## Practical options with BID

BID doesn’t ship a first‑class “Yandex module”, so you’re working with generic rules. CONSENSUS, medium confidence. The realistic options:[4][3]

1. **Target the viewer URL, not the search grid**  
   - Open a Yandex image, so you’re on the individual image viewer, not the search results grid. FACT, high confidence.[1]
   - Give that URL to BID (or a list of those URLs) so it’s parsing the viewer where the full‑res image is actually present in the DOM/JS. SPECULATION, medium confidence, assuming BID can see it once JS loads.[3][1]

2. **Use size‑based filters in BID**  
   - In BID’s Advanced Config, set “delete images smaller than X KB” or a minimum pixel size so that any small preview files get auto‑discarded. FACT, high confidence.[3]
   - This doesn’t stop downloads of thumbnails but cleans them out automatically so you keep only larger, likely full‑res files. CONSENSUS, high confidence.[3]

3. **Ignore typical thumbnail patterns (if detectable)**  
   - Yandex often encodes different sizes in the URL (e.g., with parameters or segments that indicate lower sizes). You can add regex patterns for these into BID’s Ignore List to skip them. SPECULATION, low–medium confidence, as exact current patterns aren’t documented publicly.[1][3]
   - If you see a consistent “preview” subdomain or path in thumbnail URLs when you inspect them in DevTools, add that to Ignore List, and leave only the “img”/full‑res host patterns for Include List. SPECULATION, medium confidence.[3]

4. **Rely on a specialized Yandex downloader for the hard cases**  
   - There are tools like `yandex-images-crawler` that drive a headless browser, scroll, and explicitly fetch images at a minimum size; they’re built to deal with Yandex’s JS and size filters. FACT, high confidence.[2]
   - For large Yandex scrapes, these tools are much more reliable than trying to force BID through generic rules. CONSENSUS, high confidence.[2]

## Limits you should expect

- If Yandex is serving the *only* available public image as a low‑res proxy (e.g., for copyright or bandwidth reasons), BID can’t “upgrade” it—there simply is no bigger file accessible without Yandex’s own APIs or different endpoints. FACT, high confidence.[5]
- If the full‑res is loaded via JS into a `<canvas>` or via blob URLs, BID may not see a direct file URL even with JS enabled; in that case, only a tool that actually controls the browser and intercepts network requests will see the true file. SPECULATION, medium confidence.[2][3]

## Concrete next steps I’d take

1. Pick one Yandex image that you know has a higher resolution when opened in the viewer. FACT, high confidence.[1]
2. Open DevTools → Network in your browser, open that image in the viewer, and watch for the largest `.jpg`/`.png` request; note its domain/path pattern. FACT, high confidence.[1]
3. In BID Advanced Config:  
   - Add that full‑res host/path to the **Include List**. FACT, high confidence.[3]
   - Add obvious preview/thumbnail host/path patterns to the **Ignore List**, using `**<pattern>` if you need to hard‑exclude them. FACT, high confidence.[3]
   - Set a minimum size (KB) to auto‑delete small files. FACT, high confidence.[3]

If you paste a sample Yandex image URL (search result link or viewer link), I can propose very specific Include/Ignore regex patterns tailored to that exact structure.
