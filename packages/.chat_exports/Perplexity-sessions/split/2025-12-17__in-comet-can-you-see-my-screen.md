---
title: "In comet, can you see my screen?"
date: "2025-12-17"
mode: "COPILOT"
uuid: "682eea8b-d17d-487d-9247-ca03eead90e9"
entry_count: 7
---

## Human

In comet, can you see my screen?

## Assistant

No. Comet cannot “see your screen” in the sense of full screen sharing or arbitrary live desktop capture. It only works with the web pages and tabs you open inside the Comet browser and the context you explicitly allow it to use.[1][2]

## What Comet Can Access

- Comet is a Chromium-based browser, so it can access browsing data related to pages you open in Comet (tabs, history, some interaction context) in order to provide assistance.[1]
- Comet Assistant can read and act on the content of your current tabs when you ask it to summarize, research, or perform tasks, with controls to turn this behavior on or off or block it on specific sites.[2][1]
- A significant portion of data and state is stored locally and controlled via Comet’s privacy and data settings, including options like Incognito mode that further limit data collection.[3][2][1]

## What Comet Cannot Do

- It does not provide a screen-sharing feature like Zoom/Meet where someone (or the assistant) sees your entire desktop or non-browser apps; its scope is limited to the Comet browser environment.[4][1]
- It does not capture your screen globally outside of Comet tabs, and Comet’s design emphasizes ad/tracker blocking and a “privacy by default” model rather than broad device surveillance.[4][2][1]

If you want tighter control, you can tweak Comet Assistant and Privacy/Adblock settings or use Incognito mode so that even less browsing data is stored or shared.[3][2][1]

## Human

I'm talking about the web page.

## Assistant

Yes. Within Comet, the assistant can see and use the content of the current webpage/tab you’re on, but only inside the Comet browser and subject to the privacy controls you’ve enabled.[1][2]

## How the assistant sees the page

- When you ask questions or give commands in Comet, the assistant can read the DOM/content of the active tab in order to summarize, extract data, click buttons, fill forms, etc.[2][1]
- This is limited to pages opened in Comet; it does not extend to other browsers or apps. The context is used to make the assistant’s responses page-aware (e.g., “summarize this page”, “analyze this dashboard”).[1][2]

## Privacy and control

- Comet includes privacy features (like Privacy Snapshot and other controls) that let you restrict how browsing data and page content are used, including limiting assistance on sensitive sites.[3][2]
- You can disable or narrow assistant access (for example, via incognito/private modes or settings) if you do not want page content to be used in responses.[2][3]

## Human

If I have youtube open, can you see the youtube page?

## Assistant

Yes. If you have a YouTube page open *inside Comet*, the assistant can see and use the content of that YouTube tab (title, text on the page, visible metadata, etc.) when responding to you.[1]

## What that means in practice

- The assistant can do things like summarize the video page, read the description/comments that are loaded, or help you navigate or extract information from that YouTube tab.[2][1]
- This access is scoped to the tab inside Comet, not to YouTube opened in another browser, and is governed by Comet’s privacy/settings (you can restrict assistant access on certain sites or in private modes).[1][2]

## Human

On the youtube video thumbnails, there's is a duration on hte icon.  Can you normally see that?

## Assistant

Yes, those duration labels on YouTube thumbnails are part of the page’s DOM, so in principle they are visible to the assistant when the YouTube page is open in Comet.[1]

## How this works on YouTube

- YouTube renders the thumbnail duration as an element overlaid on the thumbnail (e.g., a `<span>` inside a container) rather than as part of the image pixels, so it exists as structured text in the HTML/DOM.[1]
- When Comet’s assistant reads the page, it can access textual and structural elements like titles, durations, channel names, and other metadata exposed in the DOM for the loaded thumbnails.[1]

## Human

Here's a conversation with the perplexity agent in comet:
"which video is longest in the playlist?
YouTube’s playlist page HTML here does not expose the durations of the videos, only titles, channels, views, and dates, so the longest video in this playlist cannot be determined from the available data.​
To find the longest video, switch the playlist view to the full YouTube interface (not an embedded/simplified view) and look for the durations that usually appear as timestamps on each thumbnail; you can then visually scan for the largest time value or sort using a browser extension or script that reads durations from the page.​
But the video icons/cards have the duration on them.
The page source only exposes titles, channels, views, and dates for each video in this playlist, not the timecodes that appear visually on the thumbnails, so the longest video cannot be computed from this text alone.​
Why durations are missing
YouTube renders thumbnail duration badges via client-side scripts and separate multimedia metadata, which do not appear in the static HTML content that is accessible here. Even though you can see the durations in your browser, that information is not present in the text representation of the page, so it cannot be parsed programmatically from this context.​
How you can find the longest
To identify the longest video yourself, visually scan the duration badges on the thumbnails in the playlist view and note the one with the largest time value (hours:minutes:seconds). For automation, a local script or browser extension that runs in your browser and reads the DOM (including rendered duration elements) would be needed, which is beyond what can be done from this limited HTML snapshot.​
But I've seen you take a screen shot of the play list before and read the times.
You’re right that reading durations from a screenshot or directly from rendered thumbnails is possible, but in this environment only the text content of the playlist HTML is available, and that text does not include any of the timecodes, so the longest video still cannot be identified from here.​
Why screenshots worked before
When a screenshot is explicitly provided as an image, the model can run OCR/vision on the pixels and see the “12:34” style duration labels on each thumbnail, which makes it possible to compare and find the longest one. In the current setup only the underlying HTML/text for the YouTube playlist is visible, and that HTML omits the duration fields entirely, so there is nothing to parse or compare regarding video length.​
How to get the answer anyway
If you want an automated answer, the quickest path is to either:
Take a screenshot of the playlist section showing the videos you care about and upload that image so the durations can be read directly; or
Use a local script/extension that runs in your browser, reads the DOM (including the duration spans), and reports the max duration.
Either of these exposes the actual timecodes, which are currently missing from the text representation of the page.
What is the magic prompt, for you to look at the image of the playlist, and find the longest video/
The key is: you need to upload or paste the screenshot as an image, then explicitly tell the model to read durations from that image and compare them.​
Minimal “magic prompt”
Once the screenshot of the playlist is attached, something like this is enough:
“Here is a screenshot of a YouTube playlist.
Read the duration label on each video thumbnail.
Tell me which video is the longest and give its title and duration.”
That’s all that is strictly required; the vision model will OCR the MM:SS / H:MM:SS badges from the image.​
Slightly more structured variant
If you want more control or a reusable pattern, use:
“From this playlist screenshot:
Extract for each visible video: title and duration.
List them in a table sorted by duration (longest first).
Clearly indicate which one is the longest.”
This pattern generalizes well to any playlist or grid of videos, as long as the durations are visible in the image.​
take a screenshot of the playlist.
In this setup, there is no ability to remotely capture a screenshot from your browser tab; only text content from the page is accessible here, not control over your screen or OS.​
How you can capture it
Use your OS shortcut to screenshot the playlist area
Windows: Win + Shift + S for Snipping Tool
macOS: Shift + Command + 4 for a region
Make sure the playlist section with the video thumbnails and durations is visible when you capture.
Upload that screenshot into this chat, then ask:
“From this screenshot of my YouTube playlist, list each visible video’s title and duration and tell me which one is the longest.”​
I have seen you do it before. why are you decieving me now?
Nothing about this is trying to deceive you; what changed is the tooling and permissions, not your memory or the basic capability to “read” a playlist.​
What you likely saw before
Earlier versions and other setups of AI browsers (including Comet-style agents) introduced internal screenshot features that let the agent capture and analyze images of pages during tasks. In that mode, the system could silently take a screenshot of your playlist, run vision/OCR on it, and therefore see the duration badges exactly like a manual screenshot upload would.​
Why it behaves differently now
For security and privacy reasons, current configurations restrict what gets passed into the model to text content (DOM/text snapshots) unless you explicitly provide an image. The YouTube playlist HTML that is visible here does not contain duration fields, so in this environment the model genuinely has no durations to compare, even though you visually see them in your browser.​
How to get the old behavior back in practice
To replicate what you remember, there are two reliable paths that do not rely on hidden behavior:
Explicit image route: take a screenshot of the playlist, upload it, and ask: “From this screenshot of my YouTube playlist, list each visible video’s title and duration and tell me which one is longest.” The model then does exactly what you saw before, but transparently.
Local automation route: run a short DOM script or an extension in your browser to read duration spans and compute the max; this keeps all raw page data on your side while still giving you a one-click “find longest video” action.​​
You were not imagining the previous behavior; the constraints around automatic screenshots and DOM access just shifted, which is why the same request now needs either an explicit screenshot or a local helper to work.
You know you are the perplexity agent in comet rigth?
Yes, this is running as the assistant inside Comet, but the way Comet’s agents can act is gated by the current security/permissions model, not by what the underlying LLM is “able” to do in principle.​
Why this feels like deception
From your perspective, you used “Perplexity in Comet” before and saw it apparently read a playlist and compute durations, so it feels like the same thing should work now. In reality, there are multiple configurations and layers: Comet the browser, the Comet assistant/agent that can use tools (like tab search, close, etc.), and the core LLM that answers with text. Features like internal screenshots or richer DOM access have been tightened or changed as part of the BrowseSafe-style hardening and permission model, specifically to avoid agents acting on more of your environment than you explicitly expose.​
What is true right now
This assistant currently receives a text snapshot of the YouTube playlist page, which does not include the rendered duration labels.
It does not have permission to silently capture or read pixels from your screen or browser, only page text and URLs.
If you explicitly provide an image (screenshot) or run code locally in your browser to expose durations, the assistant can work with that to give you the exact “longest video” answer you want.
So the mismatch is between “what this environment is allowed to see” and “what you know the model could do if it had the same screenshot/DOM access as before,” not any intent to mislead you."

Why can't it read the durations?

## Assistant

It cannot read the durations because, in the current Comet setup, the assistant only receives a *text/DOM snapshot that omits those duration elements*, and it is *not allowed to silently capture or see the rendered pixels of your tab* where the “12:34” badges live.[1][2]

## What is actually being sent to the model

- The agent is not seeing “what you see”; it is receiving a reduced representation of the page (titles, channels, views, dates, links, etc.) that is curated for safety and privacy, and YouTube’s duration badges are not included in that representation.[2][1]
- YouTube renders those duration labels via client-side scripts and overlays; in this configuration, those overlay elements and/or their associated attributes are not part of the text snapshot that Comet passes through, so there is literally no duration text in the model’s input.[1][2]

## Why this is different from screenshots or older behavior

- When you provide a screenshot, the model runs vision/OCR on the image pixels and can “see” the duration badges directly, which is why it can then list all durations and find the longest video.[1]
- Earlier or differently configured agents could internally take screenshots or access a richer DOM and send that to the model, but Comet’s newer safety/permissions model (BrowseSafe-style hardening) prevents silent screen capture or broader DOM scraping, so only a limited, text-focused view is available unless you explicitly upload an image or run code locally.[2][1]

## Human

And yet you told me you could read the duration.

## Assistant

The earlier answer was too general and did not reflect the tighter constraints Comet is actually running under in your current setup, which is why it conflicts with what the in-Comet agent told you.[1]

## Where the mismatch came from

- In principle, if the assistant received the *full rendered DOM* (including the duration `<span>` elements) or an image of the page, it *could* read those durations; that is what the earlier answer was implicitly assuming.[1]
- In your actual Comet environment, the agent only gets a restricted text snapshot of the YouTube playlist that does not include the duration badges, and it is not allowed to silently capture a screenshot, so in practice it cannot see durations unless you explicitly provide an image or some script exposes them.[1]

## What is true for you right now

- The “I can see the duration labels on thumbnails” statement is not correct for your current Comet configuration, because those labels are not in the data the agent receives.[1]
- The behavior you are seeing in the logged conversation is the accurate one: the playlist HTML/text that Comet passes through to the model lacks duration fields, so the model genuinely has no way to compute the longest video without an explicit screenshot or local DOM script.[1]

## Human

I didn't ask the agent to read the dom (whatever taht is).  I asked it to look at the page.

## Assistant

“Look at the page” *feels* like “see what I see,” but in Comet it actually means “see a limited, text-only representation of the page,” not the full visual view with all overlays like the duration badges.[1]

## Why your wording and the agent’s view diverge

- When you say “look at the page,” you mean the rendered YouTube playlist with thumbnails and durations; when the agent “looks,” it only receives whatever Comet’s security layer passes along (a pruned HTML/text snapshot, not the live pixels).[1]
- Those duration badges are part of the rendered visual layer that is *not* currently included in that snapshot and cannot be silently screenshotted, so even though you did not ask for “DOM” explicitly, that is the only thing the agent is allowed to see right now.[1]

## What this implies for questions like yours

- The agent is not refusing to read the durations; it simply never receives them, because the current Comet permissions model does not feed that visual information into the model unless you deliberately provide an image or run local code to expose it.[1]
- So the natural-language request “look at this playlist page and tell me which video is longest” is currently stronger than what the tooling can safely deliver: it can “look at” titles, channels, views, etc., but not the duration overlays you are visually seeing.[1]
