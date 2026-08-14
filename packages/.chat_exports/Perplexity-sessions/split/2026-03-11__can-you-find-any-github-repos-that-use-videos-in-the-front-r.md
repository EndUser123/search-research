---
title: "can you find any github repos that use videos in the front readme?"
date: "2026-03-11"
mode: "COPILOT"
uuid: "b14b528a-2d9b-4342-bff7-613d3b1f5e4b"
entry_count: 6
---

## Human

can you find any github repos that use videos in the front readme?

## Assistant

Yes. Here are some concrete repos whose front README uses an actual video (either directly playable or as a thumbnail linking to an MP4).

## Direct MP4 or video-linked content

These use an MP4 hosted on GitHub (usually `user-images.githubusercontent.com`) and referenced from the README, often via an `<a>` tag or HTML `<video>`:

| Repo | Where the video is | How it’s used in README |
| --- | --- | --- |
| `divmain/GitSavvy` | MP4 at `https://user-images.githubusercontent.com/8558/...0910.mp4` [1] | README includes an `<a>` tag linking to the MP4, with an inline GIF preview image that users click to watch the full video. [1] |
| `s8sachin/subtitler` | MP4 uploaded as an asset (linked in StackOverflow example) [2] | README demonstrates embedding a video with raw HTML: `<video src="https://user-images.githubusercontent.com/aaa.mp4"></video>`. [2] |

Note: On GitHub’s web UI, full HTML `<video>` tags and raw MP4 links often don’t render as inline players; they may show as links that open or download in a new tab. This is a GitHub limitation, not a repo issue.[2][3][4]

## Pattern you can copy

A practical pattern many repos use:

```html
<a href="https://user-images.githubusercontent.com/8558/290011169-1af9e0e4-aadd-4539-b7ac-d4979b9d0910.mp4">
  <img src="https://user-images.githubusercontent.com/8558/290011195-35d53963-fe57-4c46-b418-e8ed3bf02f54.gif" width="100%">
</a>
```

This gives you:

- GIF inline in the README.
- Click opens the MP4 video hosted by GitHub.[1][2]

If you want more examples, I can look for repos in a specific language or domain (e.g., devtools, CLIs, web apps). What kind of projects do you want these video-in-README examples to come from?  

## Human

it doesn't seem easy to upload the videos to github.  What's the optimal way these days, so I can use them in the readme?

## Assistant

The optimal pattern in 2026 is: don’t fight GitHub’s limited video support in README; host the video somewhere stable, and use a thumbnail link or GitHub’s auto-embed where it actually works.[1][2][3]

## Current reality (constraints)

- README Markdown does not reliably support inline video players; `<video>` tags and iframes are stripped or behave inconsistently.[4][5][6]
- Drag‑dropping an MP4 into a markdown file in some contexts uploads it to `user-images.githubusercontent.com`, but it’s not consistently exposed as a real player in all clients.[3][4]
- GitHub still treats images and links as first‑class, but not rich video embeds in README.[2][5][1]

## Recommended options (ranked)

### 1. Thumbnail → external video (most robust)

Host video on YouTube/Vimeo/your own site and use a clickable image:

```md
/image(https://example.com/your-demo-video "Watch the demo")
```

- Works everywhere GitHub renders Markdown, no HTML quirks.[7][1][2]
- Video hosting handles encoding, streaming, and bandwidth.[8][1]

Minimal flow:

1. Export a short demo (≤60–90s).  
2. Upload to YouTube/Vimeo (unlisted if you like).  
3. Create a 1280×720 or similar PNG thumbnail (`assets/demo-thumb.png`).  
4. Commit thumbnail to repo and use the Markdown above in `README.md`.  

### 2. Thumbnail → MP4 hosted in repo or `user-images` (GitHub-only, still solid)

If you want everything on GitHub:

```md
/image(https://raw.githubusercontent.com/you/your-repo/main/assets/demo.mp4 "Project demo")
```

- GeeksforGeeks and others recommend exactly this pattern.[2][7]
- Click opens the MP4 in a new tab; most browsers will play it.[9][2]

Upload flow:

1. Put `demo.mp4` in `assets/` (or upload via web UI).  
2. Get the raw URL by clicking “Raw” on the file.  
3. Wire that into the Markdown snippet above.  

You can also upload by drag‑dropping the MP4 into an issue or comment and using the generated `https://user-images.githubusercontent.com/...mp4` URL, then link to that.[3]

### 3. GitHub Pages for actual embedded player

If you really want an inline `<video>` player:

- Create a GitHub Pages site (e.g. `/docs` or `gh-pages`).  
- On the Pages site, embed with HTML:

```html
<video controls autoplay muted playsinline width="100%">
  <source src="assets/demo.mp4" type="video/mp4">
</video>
```

- That works because Pages allows full HTML and iframes; README does not.[1]
- In README, link to the demo page: `▶ Live demo video (GitHub Pages)` → `https://you.github.io/your-repo/demo`.[1]

### 4. Animated GIF only (legacy but simple)

- Convert a short segment to GIF and embed directly: `[image]`.  
- Upside: fully inline and immediate.  
- Downside: massive file sizes and lower quality; GitHub itself has asked for `<video>` support because GIFs are inefficient.[5]

This is fine for 3–5s UI loops, not for full tours.

## Pragmatic “optimal” recipe

For something you’ll actually keep using:

1. **Host the video on YouTube (unlisted) or similar.** It solves encoding / mobile / bandwidth.[8][1]
2. **Add a thumbnail image to the repo** and wire it up with the Markdown link pattern in the README.[7][2][1]
3. Optionally add a **secondary raw MP4 link** for people who want to download or for offline decks.[2][3]

If you tell me your repo’s visibility (public portfolio vs internal tooling), I can propose an exact snippet + file layout that fits your use case.  

## Human

public visability, with notebooklm videos for explainations.

## Assistant

Best setup: keep the NotebookLM videos where Google hosts them (shareable links) and surface them in the README as clean, clickable thumbnails; optionally mirror critical ones as MP4s in your repo for durability.[1][2][3]

## Step 1 – Make NotebookLM videos linkable

NotebookLM “Video Overview” has three sharing options.  For public visibility:[4][1]

1. Generate a **Video Overview** in the notebook’s Studio.[1][4]
2. Click **Share** in the video player.[1]
3. Set notebook access to **Anyone with the link, full notebook** so the video link is public.[5][1]
4. Copy the **Video Overview link**.[1]

You can also download the video file if you want a local MP4 backup: Studio → Video Overview → menu → **Download**.[4][1]

## Step 2 – Use thumbnail → NotebookLM link in README

Pattern (most robust with least friction):

```md
/image(https://notebooklm.google.com/video/your-video-id "NotebookLM video overview")
```

- This is the “clickable thumbnail → video URL” pattern recommended for GitHub in 2026.[2][3]
- Works in repo page, profile preview, npm/GitHub mirrors, etc., because it’s just an image plus link.[3][2]

Suggested file layout:

```text
README.md
assets/
  notebooklm-overview-1.png
  notebooklm-overview-2.png
```

You can grab a frame from the video (or use a simple branded slide) as the thumbnail.

## Step 3 – Optional: mirror as repo MP4 for redundancy

For key videos you don’t want to lose if links change:

1. Download the Video Overview from NotebookLM.[4][1]
2. Add `assets/notebooklm-overview-1.mp4` to the repo and commit.  
3. Get the raw URL from GitHub (open file → “Raw”).  

Then add a secondary link:

```md
[▶ Download MP4 version](https://raw.githubusercontent.com/you/your-repo/main/assets/notebooklm-overview-1.mp4)
```

GeeksforGeeks explicitly documents this “thumbnail → raw MP4” pattern as supported, even though README cannot embed a real player.[3]

## Step 4 – Consistent section in README

Example section you can drop into any public project:

```md
## Video walkthroughs (NotebookLM)

High-level feature tours generated with NotebookLM Video Overviews:

- /image(https://notebooklm.google.com/video/FEATURE_ID "NotebookLM feature tour")
- /image(https://notebooklm.google.com/video/ARCH_ID "NotebookLM architecture overview")

Prefer local copies?
- [Download MP4 (feature overview)](https://raw.githubusercontent.com/you/your-repo/main/assets/notebooklm-feature.mp4)
- [Download MP4 (architecture overview)](https://raw.githubusercontent.com/you/your-repo/main/assets/notebooklm-arch.mp4)
```

This keeps NotebookLM as the “source of truth” while giving users direct and fallback paths.

Would you like a tailored snippet for a specific repo (e.g., “ts-web-app-starter” with 2–3 NotebookLM explainer videos), including suggested titles and thumbnail naming?  

## Human

If I share the video from notebooklm, does the world get access to the notebook, or just the video?

## Assistant

By default, if you share a NotebookLM Video Overview “by link,” viewers also get access to the underlying notebook, not just the video.[1]

## What NotebookLM actually shares

Google’s docs for Video Overviews say that when you share a video link you must ensure “the notebook is shared with the recipient or is made public (anyone with the link), and viewers have access to the ‘full notebook’ (and not just ‘chat only’).”[1]
So the standard “Share → copy video link” flow makes both the video and the notebook visible to anyone with that link (for consumer accounts).[2][3][1]

## Ways to limit what people see

You have three distinct sharing patterns.[1]

- Option 1 – **Video link (default)**:  
  - Requires notebook access be at least “Anyone with link → full notebook” for true public sharing.[1]
  - Viewers can see the notebook contents, not just the video.

- Option 2 – **Share notebook explicitly**:  
  - You send the notebook link; recipients can open the notebook and then play the Video Overview in the Studio panel.[1]

- Option 3 – **Download & host the video yourself**:  
  - You download the Video Overview and share the file (e.g., on YouTube or as an MP4 in your repo) without exposing the NotebookLM notebook at all.[4][1]

For a public GitHub README, if you want the world to see the explanation but not the notebook contents, you should use Option 3: download from NotebookLM, then host or upload that video elsewhere and link/thumbnail it from the README.

Do you specifically want to keep the underlying sources and notes private while still using the NotebookLM-generated narration, or is it acceptable if people can browse your notebooks too?

## Human

I want videos public but notebooks fully private

## Assistant

You can do that, but you must avoid sharing NotebookLM’s own links and instead use downloaded videos hosted elsewhere.[1][2]

## What NotebookLM exposes by default

- “Share video link” expects the notebook to be shared (at least “anyone with the link, full notebook”), so the viewer typically gets both notebook and video.[3][4][1]
- Google’s docs explicitly list a separate option: **Option 3: Download & share the Video Overview** as an MP4 file.[2][1]

So to keep notebooks private while videos are public, you must use Option 3 and never share the NotebookLM URL.

## Workflow: private notebook, public video

1. In NotebookLM Studio, open your **Video Overview**.[5][1]
2. Use the **Download** / “Download MP4” option (three-dot menu).[6][2]
3. Host that MP4 somewhere public but notebook-agnostic:  
   - YouTube (unlisted or public) or Google Drive, or  
   - Commit the MP4 into your repo or a separate static hosting bucket.[7][5]
4. In your README, link via a clickable thumbnail:

```md
/image(https://youtu.be/YOUR_VIDEO_ID "Video overview")
```

or, if hosting in the repo:

```md
/image(https://raw.githubusercontent.com/you/your-repo/main/assets/notebooklm-demo.mp4 "Video overview")
```

This way:

- Notebook remains fully private in NotebookLM.  
- Only the exported MP4 is visible to the world, and GitHub/YouTube know nothing about the underlying notes or sources.[1][7][2]

Do you want to standardize on YouTube for hosting, or would you rather keep the MP4s inside your GitHub repo for tighter control?

## Human

Prefer hosting all MP4s inside the GitHub repo

## Assistant

Got it. Then the pattern is: keep NotebookLM notebooks private, export MP4s, store them under `assets/` in your repo, and expose them via thumbnail links in the README.

## NotebookLM → MP4 → GitHub

1. **Generate & export from NotebookLM**  
   - Create your Video Overview in the Studio panel.[1][2]
   - Use the **Download / Download video** option to get an MP4 file.[2][3]
   - Do **not** use NotebookLM’s “share video link” (that expects the notebook to be shared).[4][1]

2. **Store MP4s in your repo**

Recommended layout:

```text
README.md
assets/
  video/
    overview-intro.mp4
    feature-tour.mp4
  img/
    overview-intro-thumb.png
    feature-tour-thumb.png
```

- This keeps videos versioned and local to the project.  
- Use short, compressed MP4s (e.g., 720p, 30–60s) to avoid bloating clone size; you can recompress with ffmpeg before committing if needed. (Best practice; not GitHub-specific.)  

3. **Link videos from README using thumbnails**

GitHub doesn’t reliably render inline `<video>` players in README, so use clickable thumbnails → raw MP4 URLs.[5][6]

Example:

```md
## Video walkthroughs (NotebookLM)

- /image(https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/assets/video/overview-intro.mp4 "Intro overview (MP4)")
- /image(https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/assets/video/feature-tour.mp4 "Feature tour (MP4)")
```

Details:

- Get the exact `raw.githubusercontent.com/...` URL by opening the MP4 in GitHub and clicking **Raw**.[5]
- This “image → link to raw MP4” pattern is widely documented as the reliable way to use videos in README.[6][5]

4. **Optional: direct download links**

Below the thumbnails you can add:

```md
Or download directly:

- [Download intro MP4](https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/assets/video/overview-intro.mp4)
- [Download feature tour MP4](https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/assets/video/feature-tour.mp4)
```

Same URL, just without the thumbnail.

5. **Keep notebooks private**

Since you never share NotebookLM links, your notebooks and sources remain fully private; only the exported MP4s live in Git/GitHub.[1][2]

If you’d like, I can draft a ready-to-paste `## Video walkthroughs` block with generic copy that you can reuse across repos.  
