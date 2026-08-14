---
title: "'Use the screenshot tool to see the durations'"
date: "2025-12-17"
mode: "COPILOT"
uuid: "d87a18dc-94f7-488a-bdc4-32bc74c61257"
entry_count: 3
---

## Human

"Use the screenshot tool to see the durations"

## Assistant

The playlist page HTML does not expose video durations in the text content, so the screenshot tool cannot read them from this view.[1]

## Why durations are missing

YouTube renders each video’s length inside canvas/SVG overlays and ARIA labels, which do not appear as plain text in the DOM content that is accessible here. As a result, only titles, channels, views, and dates are visible, not the `mm:ss` or `hh:mm:ss` durations.[1]

## How to get durations instead

To capture durations with a screenshot-style workflow, open the playlist in grid view or scroll so the visible thumbnails show their time badges, then use a true visual screenshot/OCR step rather than DOM text extraction. Alternatively, export the playlist via a YouTube API or a browser extension that can read video metadata, which includes duration fields.[1]

## Human

This is what another instance of perplexity tells me:
If an instance tells you it can't take screenshots or see visual elements, that's likely an error in its reasoning, not a toolchain limitation. The computer tool with screenshot action is a standard capability in Perplexity's browser automation agent (Comet).

## Assistant

That other instance is describing Perplexity’s general Comet/browser-automation capabilities, but those are not available in this chat context, so screenshots are not actually possible here.  

## Why the answers differ

Perplexity supports different “modes” and tools depending on where and how it is used (e.g., Comet automation vs. standard web-browsing chat).  
In this conversation, only the tools listed in the system/developer instructions are active, and none of them is a `computer` or screenshot/vision agent that can click around or capture the screen.  

## What this instance can and cannot do

This instance can:  
- Read page HTML/text via browser tools and web requests.  
- Reason over that text and your prompts to help design workflows, including how you could use Comet or other automation tools elsewhere.  

This instance cannot:  
- Trigger a `computer` tool, move the mouse, or take real screenshots in your environment.  
- “See” visual-only elements like overlaid YouTube duration badges unless they also appear as text in the fetched HTML.  

## How to reconcile this with Comet

If you run Comet or another browser-automation agent separately, you can absolutely use its `computer.screenshot` (or equivalent) action to grab the playlist view and OCR the durations.  
The correct mental model is: that instance was talking about what Perplexity+Comet can do in the right environment, while this chat is running in a more restricted tool configuration that does not include the screenshot-capable `computer` tool.

## Human

you are both in the comet browser.  In fact it is in the next tab over.

## Assistant

Both chats may be open in Comet, but they are running with different tool configurations, which is why the capabilities do not match.  

## Why the other tab can talk about screenshots

In Comet, an agent *can* be wired up with a `computer` tool (mouse/keyboard/screenshot actions) in addition to normal web tools.  
The other instance you are using is likely in a workspace or flow where that `computer` tool is enabled, so it can correctly say “I can take screenshots” in that context.  

## Why this tab still cannot take screenshots

This specific conversation’s system instructions enumerate the tools, and they only include web/search, browser-tab, page-content, chart, Python, and Perplexity-support tools—not any `computer.*` tool.  
Even inside Comet, an agent can only call tools that its configuration exposes, so here there is no way to dispatch a screenshot or visual action despite being in a Comet browser tab.  

## How to use both together

To actually grab the playlist durations visually:  
- Use the Comet flow/tab where the `computer` tool is active to run a `computer.screenshot` + OCR step over the playlist page.  
- Use this tab for planning, parsing the extracted text, or designing the automation, but not for the screenshot itself.
