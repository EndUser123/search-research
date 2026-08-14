---
title: "I'm trying to use bulk image downloader on yandex.com.  But it's not working.  files show up in the download list, but t"
date: "2026-07-19"
mode: "COPILOT"
uuid: "e54937c7-fbd0-4147-84ab-4b09b0f8b7e9"
entry_count: 11
---

## Human

I'm trying to use bulk image downloader on yandex.com.  But it's not working.  files show up in the download list, but they say corrupted and stuff.  What does reddit say is the workaround?

## Assistant

Reddit reports that Bulk Image Downloader breaks on Yandex because Yandex serves images through anti‑bot/streaming mechanisms, and the files BID saves are partial or non‑image responses rather than real JPEG/PNG data. The main workarounds people discuss are: use alternative tools that understand Yandex, or pull direct image URLs and feed them to BID (or another downloader) instead of scraping the page directly.[1][2]

## What’s actually going wrong

When BID shows items in the download list but the resulting files are “corrupted”, it usually means one of three things:[2]

- The URL doesn’t point to the raw image but to an HTML or JSON endpoint, so you’re saving non‑image data with an image extension.[2]
- Yandex is rate‑limiting or blocking automated downloads, returning error pages or truncated content that BID still writes to disk.[3][1]
- The page uses dynamic loading/CDN indirection, and BID is grabbing intermediate URLs that expire or redirect to something non‑image by the time of download.[3][2]

On Yandex specifically, their help docs and behavior indicate a mix of third‑party cookie requirements, dynamic content, and download limitations for shared folders, which can produce broken downloads if a tool doesn’t follow the full flow like a browser does.[3]

## What Reddit says to do instead

Reddit doesn’t have a single “official” fix for Yandex+BID, but patterns from DataHoarder and similar threads point to these strategies:[4][5][6][1][2]

- Add human‑like randomness and slow down:  
  Users note that aggressive, parallel downloads trigger anti‑bot protections; adding delays and lowering parallel download count in BID reduces blocks.[1][2]

- Use “deep scan” or alternative scrapers:  
  People often switch from BID to tools like JDownloader 2 (deep scan), DownloadThemAll, WFDownloader, or Scrapy when a site’s dynamic loading defeats BID’s scanner.[7][5][6][4]

- Manually extract direct image URLs:  
  Several workflows rely on getting a text list of URLs (via browser dev tools, link‑collecting extensions like Link Klipper, or custom scripts), then feeding that list to a bulk downloader.[5][7][4][2]

- Check filters and URL type:  
  Guides emphasize verifying that BID (or any downloader) is targeting true image URLs and that filters (file type, size, domain) aren’t silently excluding valid images.[8][2]

None of the threads I can see show a clean “toggle X in BID and Yandex works perfectly”; instead, the consensus is that you either adapt your process around Yandex’s constraints or use different tooling. Confidence: medium, because there isn’t a Yandex‑specific BID Reddit thread in the results, but the behavior matches the symptoms you describe.[1][2][3]

## Concrete workaround you can try now

Given your setup and the “corrupted” files symptom, a pragmatic Reddit‑style workaround would be:

1. Slow down and randomize BID requests  
   - In BID settings, reduce parallel downloads to a very low number (1–3).  
   - Add random delays between downloads and between pages, as suggested in BID user guides and hoarder threads.[2][1]
   - Run a small test batch (10–20 files) and inspect them with an image viewer or hex editor to confirm they’re valid JPEG/PNG rather than HTML error pages.[9][2]

2. Switch to a URL‑list‑based approach  
   - On the Yandex page, use the browser dev tools or a link‑extraction extension (e.g., Link Klipper) to grab the actual image URLs rather than page URLs.[4][5]
   - Save those URLs to a text file and feed them to BID via its “manual links” or batch‑URL mode, or use another downloader like JDownloader 2’s “analyze text with links” plus deep scan.[7][4]
   - This avoids BID trying to interpret Yandex’s dynamic page logic; it just fetches what you explicitly give it.  

3. If BID keeps failing, swap tools for Yandex  
   - Try JDownloader 2 with “analyze text with links”, then allow deep scan if needed; Reddit users report that this often succeeds where BID fails on modern sites.[4]
   - For more control and reliability, a Python script using `requests` + `aiohttp` or `scrapy` is a common DataHoarder‑style suggestion when bulk downloaders struggle with a particular host.[5]

Confidence: medium; these are general Reddit‑endorsed patterns for stubborn sites rather than a documented Yandex‑specific BID fix.

Given you’re on Windows and comfortable with scripting, would you prefer a concrete Python or PowerShell snippet that ingests a list of Yandex image URLs and downloads them in a more “human‑like” pattern?  

## Human

Ok, I installed jdownload 2.  I have a yandex url.  where do I put it?

## Assistant

Paste the Yandex URL into JDownloader’s **LinkGrabber** – either by pasting directly or using the “Add links” dialog – that’s where JDownloader discovers and queues downloads.[1]

## Fastest way: copy–paste

For a single Yandex URL you already have:

- Open JDownloader 2 and click the **LinkGrabber** tab.[1]
- Make sure JD is running and just press **Ctrl+V** while the LinkGrabber tab is active; it will automatically pick up the URL from your clipboard and start parsing it.[1]
- After a few seconds, you should see one or more “packages” with files listed under LinkGrabber; then you can right‑click and start downloads.

## Explicit “Add links” dialog

If you want more control (e.g., set folder right away):

- In JDownloader, go to the **LinkGrabber** tab.[1]
- Use the **Add links** button (depending on theme, usually a “+” or “Add links” icon in the toolbar).[1]
- Paste your Yandex URL into the dialog’s URL box.  
- Optionally set package name and download directory there.  
- Confirm; JD will deep‑crawl the URL for downloadable items.[1]

Once it finishes crawling, select the found items in LinkGrabber and click the button to move them to the **Downloads** tab so they actually start.

## Optional: browser integration

If you find yourself doing this a lot:

- Install the **MyJDownloader** browser addon, then right‑click on the Yandex page and choose “Download with JDownloader” to send the current tab URL directly into LinkGrabber.[2][3][1]

If you paste the Yandex URL and LinkGrabber shows nothing or only one “HTML” file, tell me what kind of Yandex URL it is (Disk share, image search, gallery, etc.), and we can adjust JD settings or use a different pattern.

## Human

It said something about playlist, and missing PINs and stuff.

## Assistant

JDownloader is treating that Yandex link as a **playlist/streaming URL**, which uses PIN/auth tokens that JDownloader doesn’t have, so it can’t resolve the actual files. That’s why you’re seeing “playlist” and “missing PINs” messages instead of image packages showing up.

## What that “playlist / PIN” message means

- Some Yandex links (especially media or shared content) are exposed as playlist/manifest URLs (think HLS/DASH style) rather than direct file links.  
- JDownloader sees “playlist” and expects additional parameters (PINs/auth tokens/headers) that a normal browser has, but JD does not, so it can’t turn that one URL into concrete downloadable items.  
- In practice, this is JDownloader’s way of saying “I see a structured stream, but I don’t have the right tokens to fetch the underlying files.”

So instead of feeding JD the “special” Yandex presentation URL, you want to give it URLs that look like normal files or a share page it understands.

## Minimal workaround: send the share page, not the internal URL

If your Yandex link is:

- A weird long URL that mentions `playlist`, `manifest`, or looks like an embedded player URL → this is the problematic one.  
- Try instead:  
  - Open that URL in your browser.  
  - Navigate back to the **share page** or folder view that a human would see (a page listing all photos/files).  
  - Copy that page’s address bar URL and paste it into JDownloader’s **LinkGrabber** (Ctrl+V or “Add links”).  

JD’s Yandex plugin is built around the public Disk/share/file URLs it knows how to parse; if you feed it internal player/playlist links, you get exactly the kind of “playlist / missing PIN” outcome you’re seeing.[1]

## More reliable workflow if that still fails

Because Yandex and JD integrations can be brittle, the more robust Reddit/DataHoarder‑style approach is:

1. Use browser to get “real” URLs  
   - In the browser, open the Yandex gallery or Disk folder that lists the images.  
   - Use the network tab in dev tools or a link‑extracting extension to pull out direct file URLs (they should end in typical file extensions like `.jpg`, `.jpeg`, `.png`, etc.).  

2. Feed those URLs to JDownloader  
   - In JD, open **LinkGrabber**, click **Add links**, and paste the list of URLs (one per line).  
   - JD then treats them as normal file downloads, with no playlist/PIN logic involved.  

This avoids the whole playlist/PIN path and just makes JD do what it’s good at: fetching files given clean URLs.

## Next step

To give you a precise, repeatable path, I need to know what kind of Yandex link you’re using right now:

- Is it a Yandex Disk share/folder link (the page shows thumbnails of lots of images)?  
- Or is it a link that opens some kind of inline player/slider, and JD is grabbing that “player” URL instead?

If you can paste a **redacted** example pattern (just the shape, not your actual private URL), I can tell you exactly which variant to feed into JDownloader and which to avoid.  

## Human

[https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar](https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar)

This is the human facing page.

## Assistant

Thanks, that URL helps. JDownloader is struggling because Yandex Images’ “similar images” view is **not a simple file/gallery page**, it’s a search result UI with dynamic image tiles, so JD sees almost no direct files and sometimes treats internal resources like playlists instead.[1][2][3]

## Why this human page is awkward for JDownloader

- The URL you pasted is an **image search / similar images** page (`rpt=imageview`, `cbir_page=similar`), not a static folder of files.[1]
- The images you see are rendered via JavaScript and internal APIs; the browser combines HTML + JSON + image URLs to build the grid.  
- JDownloader’s generic link parser often doesn’t follow that full JS flow, so it can pick up odd intermediate URLs (manifests, playlists, or HTML endpoints) and then complain about missing PINs/auth when it tries to treat them as downloads.  

So even though it’s “human‑facing”, it’s not the kind of simple listing JD was designed around.

Given that, there are three practical paths:

## Option 1: use a Yandex-specific downloader (Reddit-style solution)

Reddit and GitHub folks largely sidestep generic download managers and use tools tailored to Yandex Images:[4][2][5][3]

- Python scripts like `yandex-images-download`, `yandex-images-crawler`, or `yandex-image-scraper` open that exact type of URL and drive a browser (Selenium/Playwright) to scroll, click, and pull real image URLs.[2][5][3][4]
- Workflow:  
  1. Install the tool (`pip install yandex-image-scraper` or clone one of the GitHub repos).  
  2. Provide search keywords or a CBIR/similar‑images URL like the one you pasted.  
  3. Let it crawl and download images directly, bypassing JDownloader entirely.  

This is closer to what DataHoarder‑style Reddit threads recommend when dealing with search‑result pages rather than file storage links.[3][2]

## Option 2: browser extension that understands Yandex Images

There’s a Chrome extension explicitly built to batch‑download images from Yandex search results:[6][7][8]

- Install **“Yandex Image Download”** from the Chrome Web Store.[6]
- Open your Yandex Images similar‑images page in Chrome.  
- Use the extension’s UI to let it extract all visible images and download them in bulk.  

This extension runs inside the browser, so it can see the fully rendered DOM and JS‑generated URLs, which is exactly what JDownloader is missing for this page type.[7][6]

## Option 3: turn the page into a list of direct URLs, then feed JD

If you want to keep JDownloader in the loop:

1. Use dev tools or a helper script/extension to extract visible image URLs:  
   - In the browser on that Yandex page, open DevTools → Network tab.  
   - Filter by “Img” or look for requests to `avatars.mds.yandex.net/get-images-cbir/...` (these are the actual image files).[2][1]
   - Copy those URLs into a text file, one per line.  

2. Paste that list into JDownloader:  
   - In JD, go to **LinkGrabber → Add links**.  
   - Paste your list of direct image URLs.  
   - JD now sees normal files (ending in image formats) instead of playlist/manifest endpoints, so no PIN/playlist errors.  

This is more manual but keeps your existing JD workflow.

## My recommendation given your background

You’re comfortable with Python and automation, so the most future‑proof path is to use a Yandex‑specific Python scraper (Option 1) and treat Yandex Images as a data source rather than a “file host”. JDownloader is great for static file URLs; it’s not optimized for CBIR/similar‑images search grids.

If you want, I can sketch a short Python script using one of the GitHub projects (or Playwright directly) that takes a Yandex Images search URL like the one you posted and dumps all matching images into a local folder on Windows.  

## Human

is there a url for the same content that I can change to?

## Assistant

Short answer: not a single “magic” alternate URL, but yes: the **direct image URLs** embedded in that page are what you want, and you can transform the human page into a list of those URLs, then feed that list to JDownloader instead of the search URL itself.[1][2][3]

## What’s special about your URL

Your link is a **reverse image / similar images** search page (`cbir_page=similar`, `rpt=imageview`). That page:[4][5]

- Is a dynamic search UI, not a static gallery or folder.  
- Loads multiple images via internal APIs and `avatars.mds.yandex.net/get-images-cbir/...` URLs behind the scenes.[2][4]
- Does not expose a single “canonical” URL that JD can turn directly into file downloads.  

So there isn’t a simple query‑parameter change (like `&mode=gallery`) that yields the same content in a JD‑friendly format. Instead, the **same content** is reachable through the individual image URLs that the page uses.

## The “alternate URL” that works: direct file links

For each tile on that page, there is at least one underlying URL like:

- `https://avatars.mds.yandex.net/get-images-cbir/.../orig`  

Those are the URLs JD can handle reliably. The workaround is:

1. Turn the human page into a list of those file URLs.  
2. Give that list to JDownloader via LinkGrabber.  

This is functionally “changing the URL” to something JD understands, just in bulk.

## How to get those URLs from your page

Here’s a practical browser‑side workflow:

- Open your Yandex Images page in Chrome or Firefox.  
- Open **DevTools → Network**.  
- Reload the page and scroll so all the tiles you care about are visible.  
- Filter the network requests by “Img” or look at requests whose URLs start with `https://avatars.mds.yandex.net/get-images-cbir/`.[4][2]
- Right‑click → “Copy all as HAR” or manually copy the relevant URLs to a text file (one per line).  

Those copied URLs *are* the alternate URLs for the same content.

Then:

- In JDownloader, go to **LinkGrabber → Add links**.  
- Paste your list of image URLs.  
- JD should now detect them as individual files, with no playlist/PIN errors, because it’s getting direct image endpoints rather than a complex search UI.[3][1][2]

## If you want this automated instead of manual

Community tools (mostly on GitHub) implement exactly this path: open a Yandex Images search or reverse‑image page, then extract and download underlying image URLs:

- `yandex-images-download`, `ImagesFromYandex`, `yandex-images-crawler`, `yandex-image-scraper` and similar scripts do the crawling and URL extraction for you.[6][1][2][3]
- The typical usage pattern is: give them the search or a base image, they drive a browser, fetch the same content as your human page, and then output direct image URLs and/or download them.  

You can then either let the script download directly or feed its URL list into JD if you prefer JD’s queue management.

## Answering your exact question

So:

- There is no single Yandex‑provided “alternate” URL for that exact reverse‑image page that fixes JDownloader.  
- The **closest equivalent** is a set of direct `avatars.mds.yandex.net/get-images-cbir/...` URLs, which represent the same content in a JD‑friendly way. You obtain them via browser tools or a small script, then give that to JD.  

If you’d like, I can outline a minimal Python script that ingests the HAR from that page and prints out all `avatars.mds.yandex.net/get-images-cbir` URLs, ready to paste into JDownloader.  

## Human

what's the most popular and support yandex repo that I shoudl look at for chrome on windows 11?

## Assistant

For Chrome on Windows 11, the most widely used and actively supported option for working with Yandex **image search** pages is a dedicated Chrome extension like **“Yandex Image Download”**, not a random GitHub repo. Most GitHub repos provide Python scrapers or command‑line tools; for your “click in Chrome, download from Yandex Images” workflow, an extension integrates better.[1][2][3]

## Most relevant, popular browser-side tools

Given your use case (bulk image download from Yandex Images search/similar pages in Chrome), these stand out:

- **Yandex Image Download (Chrome extension)**  
  - Purpose: “Support batch download of pictures from Yandex website.”[2][3][1]
  - It’s explicitly designed to read Yandex search result pages in the browser and trigger bulk downloads with one click.  
  - This aligns directly with your current flow: Chrome + Yandex Images + wanting to avoid broken “playlist/PIN” URLs in JDownloader.

- **Search image with Yandex (Chrome extension)**  
  - Purpose: open‑source helper to send images to Yandex for reverse image search.[4]
  - Useful if you want quick CBIR from Chrome, but it doesn’t focus on bulk downloading; it’s more about opening Yandex search with a given image.

On GitHub, the highest‑signal projects for Yandex image downloading are Python tools like `yandex-images-crawler`, `ImagesFromYandex`, `yandex-image-scraper`, and `yandex-ris`, which are aimed at scraping/training workflows rather than daily Chrome use: You could absolutely use those for automation, but they’re not “Chrome extensions” and don’t show up as a button in your browser.[5][6][7][8]

## Why I’d prioritize the Chrome extension over a repo for you

- It runs **inside Chrome**, so it sees the same fully rendered DOM and JS calls that you see on your Yandex Images page.[1][2]
- It’s already wired for **batch download**, which is exactly what Bulk Image Downloader and JDownloader were failing to do cleanly.  
- Installation/updates go through the Chrome Web Store, which is typically more stable and user‑friendly than manually updating a GitHub repo for this kind of task.[3][1]

You can still use JDownloader downstream if you want: some of these extensions let you export or send URLs, but for a first pass, just let the extension directly download the images from the page.

## What I’d do next on Windows 11

1. In Chrome, open the **Yandex Image Download** extension page in the Web Store.[3][1]
2. Install it and grant permissions.  
3. Open your Yandex Images “similar images” page (like the one you shared).  
4. Use the extension’s UI (typically an icon or context menu) to trigger a batch capture/download of all visible images.  

If you want a repo‑based tool as well (e.g., for scripted runs or non‑Chrome environments), I’d pair that extension with one of the more active Python projects like **`yandex-image-scraper`** or **`yandex-ris`**, but for Chrome on Windows, the extension is the most natural, supported option.[6][7][8][5]

Do you want a quick “Chrome + extension + JD” pipeline sketched out, where the extension grabs URLs and then you push them into JDownloader for queue management?  

## Human

I don't think that extension works properly.

## Assistant

Given that the Chrome “Yandex Image Download” extension isn’t working reliably for you, the best‑supported, high‑signal option for Yandex Images on Windows 11 is actually a **GitHub scraper project**, not a browser extension. The most promising and maintained ones are `yandex-images-crawler` and the various `yandex-image-scraper` repos.[1][2][3][4]

## What “most popular and supported” looks like here

For your use case (bulk downloading from Yandex Images/search):

- **suborofu/yandex-images-crawler**  
  - Purpose: “allows you to download images from Yandex Images automatically,” with support for filters (size, similar images, etc.).[4]
  - Actively maintained (recent updates), clearly focused on Yandex Images rather than generic search scraping.[4]
  - This is the closest match to “well‑supported Yandex image repo” for automated downloads.

- **NijatTagizada/yandex-image-scraper (Python)**  
  - “Simple yandex image scraper with Python.”[2]
  - Good fit for a quick Python‑based workflow, though less feature‑rich than `yandex-images-crawler`.  

- **GirkovArpa/yandex-image-scraper (Puppeteer/JS)**  
  - Puppeteer script that drives a browser to scrape Yandex image search.[1]
  - Better if you want a Node/JS stack and directly automate Chrome‑like behavior rather than raw HTTP.  

These GitHub projects are heavily used by people doing dataset collection and bulk scraping, which is closer to your DataHoarder‑style goal than the typical “search in Yandex from right‑click” browser extensions like **Search image with Yandex**, **Yandex Image Search**, etc.[5][6][7][8][9]

## Why the Chrome batch extension feels brittle

- Many Yandex‑related Chrome extensions focus on **sending an image TO Yandex** (reverse search, context menu), not reliably **pulling bulk images FROM Yandex**.[6][7][8][9][5]
- The few “batch download” extensions are often one‑maintainer projects; they can break silently when Yandex changes its front‑end or internal APIs.  
- You already hit symptoms of that: page recognized, but downloads are incomplete/corrupted or the extension does nothing visible.  

Given your preference for correctness and repeatability, a scriptable scraper is more controllable and debuggable than hoping a closed extension keeps up with Yandex changes.

## Recommendation for you on Windows 11 + Chrome

Given your background (Python, multi‑agent systems, data hoarding habits):

- Use **`yandex-images-crawler`** or a Python **`yandex-image-scraper`** repo as your main tool:[2][4]
  - Clone the repo.  
  - Feed it either keywords or your reverse‑image/similar‑images URL.  
  - Let it download images into a local folder.  
  - Optionally, point JDownloader at that folder later if you want JD’s queue and bandwidth management.  

That gives you:

- A clear, auditable pipeline (you can read the code, tweak filters, control concurrency).  
- Independence from Chrome extension behavior and UI quirks.  
- Better alignment with how Reddit/DataHoarder users handle Yandex: dedicated scripts rather than generic downloaders.[3][10][4]

## Concrete next step

I’d start by looking at:

- [`suborofu/yandex-images-crawler` on GitHub] for a featureful, filter‑aware crawler.[4]
- [`NijatTagizada/yandex-image-scraper`] if you want a simpler Python entry point.[2]

If you tell me whether you’d rather use **Python** or **Node/TypeScript** for this, I can outline a minimal script based on one of those repos that:

- Accepts your Yandex Images URL (like the CBIR/similar page you showed).  
- Downloads all visible/similar images to a folder on Windows 11.  

## Human

how confident are you in your suggestions?

## Assistant

Overall: **medium–high confidence** in the *direction* (use a Yandex‑specific scraper repo rather than JDownloader/Bulk Image Downloader/Chrome batch extensions), and **medium confidence** in specific repo picks, because GitHub popularity and maintenance can shift quickly.

I’ll break it down explicitly.

## Confidence by suggestion

- **“JDownloader/Bulk Image Downloader will be brittle on Yandex Images search pages”**  
  - **Confidence: high.**  
  - Basis: BID and JD are optimized for static file URLs and known host plugins; Yandex Images “similar” pages are dynamic search UIs with CBIR parameters and JS‑loaded tiles, which generic download managers historically struggle with.[1][2]

- **“Chrome ‘Yandex Image Download’ style extensions are fragile and often break”**  
  - **Confidence: medium–high.**  
  - Basis: The extensions seen in Chrome Web Store focus on context‑menu reverse search, not robust bulk downloading, and are usually maintained by single authors. You already observed that one “doesn’t work properly”, which matches that pattern.[3][4][5][6][7]

- **“A dedicated GitHub Yandex image scraper/crawler is a better long‑term solution for bulk download”**  
  - **Confidence: high.**  
  - Basis: Multiple repos exist specifically for Yandex Images scraping (e.g., `yandex-images-crawler`, `yandex-image-scraper`, `ImagesFromYandex`), used for dataset creation, which is very close to your data‑hoarding style use case. The tooling matches the problem domain more closely than generic download managers.[8][9][10]

- **“suborofu/yandex-images-crawler and Python yandex-image-scraper are good starting points right now”**  
  - **Confidence: medium.**  
  - Basis: They are clearly branded as Yandex Images scrapers/crawlers and have non‑trivial code and some recent activity, but I can’t see full clone/download stats or detailed issue health here. They look promising; I can’t guarantee they’re the single “most popular” or bug‑free option at this moment.[10][11][8]

## Where uncertainty is highest

- **Exact “most popular” repo:**  
  - GitHub doesn’t expose popularity in a single canonical way via the snippets I see (stars, forks, last commit, issues). Multiple repos claim to be “Yandex image scraper”, and without deeper inspection I can’t definitively crown one project.[9][11][12][8][10]
  - So when I say “best‑supported”, I mean “high‑signal and aligned with your use case”, not “objectively largest star count”.

- **Future behavior of Yandex UIs and extension compatibility:**  
  - Yandex can change their front‑end, CBIR URL formats, or internal APIs, which may break both extensions and scrapers. I can’t guarantee any specific tool will continue working unchanged.

## Assumptions I’m making

- You prioritize control and reliability over convenience, so a scriptable repo fits better than a fragile extension.  
- You’re comfortable in Python/Node, so “clone a scraper and run it” is feasible for you.  
- Your target is **bulk download from Yandex Images/search/similar pages**, not Yandex Disk file storage, which is a different plugin ecosystem (JD does have a Disk plugin).[13][14]

## One concrete next step under these uncertainties

Given this:

- I’m highly confident you’ll get **better, debuggable behavior** by trying a Yandex‑focused scraper repo than by continuing to push JDownloader/BID/Chrome extensions against the “similar images” search UI.  
- I’m moderately confident `yandex-images-crawler` or a Python `yandex-image-scraper` will work out of the box for your reverse‑image URL, but you should expect minor tweaks (filters, pagination, concurrency) as you test.[8][10]

If you’d like, I can propose a very small validation plan: clone one repo, run a test against your CBIR URL, and inspect outputs to decide quickly whether that project meets your standards or you should pivot to another.  

## Human

PS D:\.code\yandex-images-crawler> D:\.code\yandex-images-crawler>.\yandex-images-crawler [https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar](https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar) -loaders-per-link 1

Id     Name            PSJobTypeName   State         HasMoreData     Location             Command
--     ----            -------------   -----         -----------     --------             -------
1      Job1            BackgroundJob   Running       True            localhost            D:\.code\yandex-i…
3      Job3            BackgroundJob   Running       True            localhost            p=1
5      Job5            BackgroundJob   Running       True            localhost            text=cum
7      Job7            BackgroundJob   Running       True            localhost            pos=23
9      Job9            BackgroundJob   Running       True            localhost            rpt=imageview
11     Job11           BackgroundJob   Running       True            localhost            lr=21457
13     Job13           BackgroundJob   Running       True            localhost            url=https%3A%2F%2…
cbir_page=similar: The term 'cbir_page=similar' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

## Assistant

PowerShell is splitting your Yandex URL on `&` and treating each query parameter (`p=1`, `text=cum`, `cbir_page=similar`, etc.) as **separate commands**, which is why you’re seeing background jobs for each piece and the error `cbir_page=similar: The term 'cbir_page=similar' is not recognized…`. PowerShell thinks `cbir_page=similar` is an executable, not part of the URL.[1]

## What’s going wrong in your command

Your command:

```powershell
.\yandex-images-crawler https://yandex.com/images/search?cbir_id=...&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=...&cbir_page=similar -loaders-per-link 1
```

PowerShell parsing rules:

- `&` is a **command separator** in PowerShell, similar to `;`.  
- So PowerShell interprets this as:
  - Run `.\yandex-images-crawler` with `https://yandex.com/images/search?cbir_id=...`  
  - Then run a new background job with command `p=1`  
  - Then another with `text=cum`  
  - …and finally tries to run `cbir_page=similar` as a command, which fails.

That explains the job list (Job3: `p=1`, Job5: `text=cum`, etc.) and the final error.[1]

## How to fix it: quote the URL

You need to wrap the whole URL in quotes so PowerShell treats it as a single string argument:

```powershell
# In your repo directory
PS D:\.code\yandex-images-crawler> .\yandex-images-crawler `
    "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" `
    -loaders-per-link 1
```

Key points:

- Use `"..."` around the entire URL.  
- Keep `-loaders-per-link 1` as a separate argument after the quoted URL.  
- No square brackets or Markdown formatting in the actual PowerShell command.

That should stop PowerShell from spawning jobs for each query parameter and let `yandex-images-crawler` receive the URL as intended.[1]

## Double-checking the tool’s expected usage

From the project’s usage snippet:[1]

```text
usage: yandex-images-crawler [-h] [--links LINK1,...] [--links-file FILE] ...
                             [--loaders-per-link N] [--headless]
```

Typical CLI call looks like:

```bash
yandex-images-crawler --links "https://yandex.com/images/search?..." --loaders-per-link 1
```

On Windows PowerShell, that translates to:

```powershell
.\yandex-images-crawler --links "https://yandex.com/images/search?..." --loaders-per-link 1
```

So you may also need the `--links` flag depending on how the binary/script is implemented. If running without `--links` doesn’t produce output, try:

```powershell
PS D:\.code\yandex-images-crawler> .\yandex-images-crawler `
    --links "https://yandex.com/images/search?cbir_id=...&cbir_page=similar" `
    --loaders-per-link 1
```

## Next step

Try re‑running with the URL quoted (and, if necessary, `--links`). If it still misbehaves, paste the *exact* help output from:

```powershell
.\yandex-images-crawler --help
```

and we can align on the correct argument pattern for this binary in your environment.

## Human

PS D:\.code\yandex-images-crawler> D:\.code\yandex-images-crawler>.\yandex-images-crawler "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" -loaders-per-link 1
D:\.code\yandex-images-crawler>.\yandex-images-crawler: The term 'D:\.code\yandex-images-crawler>.\yandex-images-crawler' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS D:\.code\yandex-images-crawler>

## Assistant

PowerShell is complaining about the literal text `D:\.code\yandex-images-crawler>.\yandex-images-crawler` because that whole string is being treated as a command, not just `.\yandex-images-crawler`. In other words, your prompt (`D:\.code\yandex-images-crawler>`) got copied into the command line, so PowerShell is trying to run `D:\.code\yandex-images-crawler>.\yandex-images-crawler` as if it were an executable, which it isn’t.[1]

You also don’t need to call the repo as a bare `.\yandex-images-crawler` binary; the README shows you should either:

- install it via `pip` and run the `yandex-images-crawler` **command**, or  
- invoke the `download.py` script directly.[1]

Let’s fix both issues.

## 1. Clean up the PowerShell command

Make sure the command line contains **only** the command, not a pasted prompt:

- BAD (what you have):

  ```powershell
  PS D:\.code\yandex-images-crawler> D:\.code\yandex-images-crawler>.\yandex-images-crawler "https://yandex.com/..." -loaders-per-link 1
  ```

  Here, `D:\.code\yandex-images-crawler>` is part of the command, causing the error.

- GOOD:

  ```powershell
  PS D:\.code\yandex-images-crawler> .\yandex-images-crawler "https://yandex.com/..." -loaders-per-link 1
  ```

Or even better (per the README), you run the installed CLI or the script.

## 2. Use the repo as documented

From the project’s README:[1]

- Install from PyPI:

  ```powershell
  pip install yandex-images-crawler
  ```

- Then you can run the CLI:

  ```powershell
  yandex-images-crawler --links "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" `
                        --loaders-per-link 1
  ```

Alternative: from the cloned repo without installing:

```powershell
PS D:\.code\yandex-images-crawler> python .\yandex_images_crawler\download.py `
    --links "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" `
    --loaders-per-link 1
```

Key points:[1]

- Use `python download.py` or the `yandex-images-crawler` console script, not `.\yandex-images-crawler` unless you’ve created a local wrapper.  
- Always quote the URL.  
- Include `--links` to tell the tool where to crawl from.

## 3. Quick sanity check

Before running against your Yandex URL:

1. In `D:\.code\yandex-images-crawler`, run:

   ```powershell
   python .\yandex_images_crawler\download.py --help
   ```

   Confirm it prints usage showing `--links` and `--loaders-per-link`.[1]

2. Try a simpler test, e.g.:

   ```powershell
   python .\yandex_images_crawler\download.py `
       --links "https://yandex.com/images/search?text=cats" `
       --loaders-per-link 1
   ```

   Verify it creates a folder and downloads some images.

Once that works, switch the `--links` value to your reverse‑image URL.

If that still doesn’t produce any downloads, paste the exact `--help` output so we can confirm the argument names and defaults for this version.  

## Human

PS D:\.code\yandex-images-crawler> yandex-images-crawler --help
usage: python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\yandex-images-crawler
       [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N] [--dir DIR] [--prev-dir DIR]
       [--loaders-per-link N] [--headless]

Yandex Images Crawler

options:
  -h, --help            show this help message and exit
  --links LINK1,...     Full links to image sets for download. Links should be separated by commas. Each
                        link should lead to an image search result or to an open preview of an image. The
                        program will open all links each in its own window.
  --links-file FILE     Text file with full links to image sets for download. Links should be separated by
                        newlines. Each link should lead to an image search result or to an open preview of
                        an image. The program will open all links each in its own window.
  --size WxH            Minimum size of images to download. Width an height should be separated by 'x'.
  --count N             Required count of images to download. Do not set it at all for infinite count. A
                        message appears if the desired number of images are downloaded.
  --dir DIR             Directory for new images.
  --prev-dir DIR        Directory of previously loaded images. Program skips the loading of already loaded
                        images in another directory. Useful for re-downloading.
  --loaders-per-link N  Number of loaders per link. Use larger values to speed up loading, but take into
                        account your computer's performance.
  --headless            Run the program in headless mode. The program will not open any browser windows.
                        You can't fix some problems in browser windows manually, so use this option with
                        caution.
PS D:\.code\yandex-images-crawler> yandex-images-crawler --links [https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar](https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar) -loaders-per-link 1

Id     Name            PSJobTypeName   State         HasMoreData     Location             Command
--     ----            -------------   -----         -----------     --------             -------
15     Job15           BackgroundJob   Running       True            localhost            yandex-images-cra…
17     Job17           BackgroundJob   Running       True            localhost            p=1
19     Job19           BackgroundJob   Running       True            localhost            text=cum
21     Job21           BackgroundJob   Running       True            localhost            pos=23
23     Job23           BackgroundJob   Running       True            localhost            rpt=imageview
25     Job25           BackgroundJob   Running       True            localhost            lr=21457
27     Job27           BackgroundJob   Running       True            localhost            url=https%3A%2F%2…
cbir_page=similar: The term 'cbir_page=similar' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.

PS D:\.code\yandex-images-crawler> yandex-images-crawler --links "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" -loaders-per-link 1
usage: python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\yandex-images-crawler
       [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N] [--dir DIR] [--prev-dir DIR]
       [--loaders-per-link N] [--headless]
python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\yandex-images-crawler: error: unrecognized arguments: -loaders-per-link 1
PS D:\.code\yandex-images-crawler>

## Assistant

You’re hitting two separate issues:

1. PowerShell parsing when you used the Markdown‑style `[https://…](https://…)` in the command.  
2. A mismatch between the CLI help you’re seeing and the arguments it actually accepts (`--loaders-per-link` vs `-loaders-per-link`).

Let’s tackle them cleanly.

## What just happened in that last command

- First call (with square brackets and parentheses):

  ```powershell
  yandex-images-crawler --links [https://yandex.com/images/search?...](https://yandex.com/images/search?...) -loaders-per-link 1
  ```

  PowerShell again sees `&` inside the unquoted URL and starts background jobs for `p=1`, `text=cum`, etc., exactly like earlier. It also sees the Markdown syntax, which has no meaning in PowerShell, so the URL gets split and mangled. That’s why you get the list of jobs and the `cbir_page=similar` error: PowerShell thinks those are separate commands.[1]

- Second call (properly quoted URL):

  ```powershell
  yandex-images-crawler --links "https://yandex.com/images/search?cbir_id=...&cbir_page=similar" -loaders-per-link 1
  ```

  The **URL part** is now fine, but the error is:

  ```text
  error: unrecognized arguments: -loaders-per-link 1
  ```

  Meaning: the installed `yandex-images-crawler` entry point doesn’t accept an argument named `-loaders-per-link`. The help text you pasted shows `--loaders-per-link N`, so either:

  - The script expects `--loaders-per-link` (two hyphens) and you passed one, or  
  - There’s an inconsistency: help text mentions `--loaders-per-link` but the args parser version you have doesn’t recognize it (bug or older version).[2]

In your snippet, the failing command shows `-loaders-per-link` (single `-`), while the help uses `--loaders-per-link` (double `-`). The error says “unrecognized arguments: -loaders-per-link 1”, which strongly suggests the single‑dash form is wrong for that CLI.

## Correct pattern to call this CLI

Based on the help output you showed:[2]

```text
usage: python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\yandex-images-crawler
       [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N] [--dir DIR] [--prev-dir DIR]
       [--loaders-per-link N] [--headless]
```

The correct call should be:

```powershell
# No Markdown, URL fully quoted, double dashes on options
yandex-images-crawler `
  --links "https://yandex.com/images/search?cbir_id=2955102%2FT0ao5vOxQ1BUArcaTOor0w9090&p=1&text=cum&pos=23&rpt=imageview&lr=21457&url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F2955102%2FT0ao5vOxQ1BUArcaTOor0w9090%2Forig&cbir_page=similar" `
  --loaders-per-link 1
```

Key details:

- **No** `[https://...](https://...)` — that’s Markdown only, not shell syntax.  
- The URL is in double quotes so `&` doesn’t spawn jobs.  
- Use `--links` and `--loaders-per-link` (two hyphens) exactly as in the help.[2]

If this still gives “unrecognized arguments: --loaders-per-link 1”, that means the installed version is out of sync with the README/help string and doesn’t actually support that option. In that case, just drop `--loaders-per-link` and use the defaults:

```powershell
yandex-images-crawler `
  --links "https://yandex.com/images/search?cbir_id=...&cbir_page=similar"
```

## Sanity test with a simple query

Before fighting the reverse‑image URL, verify the CLI works at all:

```powershell
yandex-images-crawler --links "https://yandex.com/images/search?text=cats"
```

Expected behavior (from README): it should open a browser (unless `--headless` is used), navigate to the `cats` search, and start downloading images into its default directory.[2]

If **that** fails:

- The CLI install may be broken or mis‑versioned.  
- At that point, you’re fighting tool bugs rather than Yandex itself.

## Confidence and next step

- I’m **highly confident** the immediate error you saw is due to:
  - Markdown URL syntax in the command, and  
  - Single dash on `-loaders-per-link` instead of the documented double dash.[2]
- I’m **medium** on whether your installed `yandex-images-crawler` version truly supports `--loaders-per-link`—the error hints it might not, despite the help text.

Concrete next step:

1. Run:

   ```powershell
   yandex-images-crawler --links "https://yandex.com/images/search?text=cats"
   ```

2. If that works, rerun with your CBIR URL (quoted) **without** `--loaders-per-link`.  

3. If it still rejects `--loaders-per-link`, ignore that flag; if it downloads too aggressively, we can adjust later via other parameters or by throttling in a different tool.

Would you be willing to run that simple `cats` test and tell me exactly what happens (does a browser open, any files appear, any traceback)? That will tell us whether the Yandex crawler itself is functioning, or whether we should switch to a different scraper altogether.  
