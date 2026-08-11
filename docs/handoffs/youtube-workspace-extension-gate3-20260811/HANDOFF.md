---
thread_id: gate3-ask-backend-20260811
parent_handoff_path: P:/docs/handoffs/yt-workspace-vertical-slice-20260810/HANDOFF.md
current_session_id: 019fee39-abb7-7490-a66a-e2cd7df5600a
current_terminal_id: 019fee39-abb7-7490-a66a-e2cd7df5600a
produced_at: 2026-08-11T14:00:00Z
last_updated_by: 019fee39-abb7-7490-a66a-e2cd7df5600a
last_updated_at: 2026-08-11T14:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c660d0f
---

# Handoff — YouTube Workspace Extension: Gate 3 (AI-Powered Ask)

## Objective

Upgrade the Ask tab from keyword search to AI-powered Q&A. The current Ask tab does transcript keyword search with highlighted matches. Gate 3 makes it answer natural-language questions about the video using the transcript as context.

**Scope bounds:** This is a backend integration spike, not a UI redesign. The Ask tab's search box already exists; it becomes a chat input. The hard part is choosing and wiring the model backend.

## Producing context

- Date: 2026-08-11
- Session: 019fee39... (YT Workspace build session)
- The vertical slice (VS-01..05) is functionally complete. The Ask tab does keyword search. This handoff covers the AI upgrade.

## Read-first list (ordered)

1. **Vertical slice handoff:** `P:/docs/handoffs/yt-workspace-vertical-slice-20260810/HANDOFF.md` — full context on the extension architecture.
2. **Current Ask implementation:** `P:/packages/yt-workspace/src/content/ask.ts` — keyword search over transcript segments. This is the starting point.
3. **Transcript module:** `P:/packages/yt-workspace/src/content/transcript.ts` — fetches caption track via timedtext baseUrl, parses into timestamped segments.
4. **Research concept:** `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — describes Gate 3 as "opportunistic backend with detection + timeout + validation + fallback."

## Backend options to evaluate

| Option | Pros | Cons | Verdict needed |
|--------|------|------|----------------|
| **YouTube native Ask** | Zero cost, YouTube's own model, already trained on the video | May not exist on all videos; DOM access uncertain; may require YouTube Premium | Detect if it exists on watch pages via DOM inspection |
| **Fleet model (local)** | Free (llama.cpp), private, no API key | Context window limit; quality varies; latency on long videos | Check if transcript fits in context window (typically 4-32K tokens) |
| **API call (OpenAI/Anthropic)** | High quality, large context | Cost per query; requires API key in the extension (security concern); adds network latency | Evaluate whether the extension should hold an API key or proxy through a local server |
| **Perplexity API** | Good at synthesis with citations | Cost; may not have the specific video content indexed | Test with a specific video query |

## Hard constraints

1. **No API keys in the extension source.** If using an API, the key must be stored in `chrome.storage.local` (set by the user) or proxied through a local server.
2. **Timeout + fallback.** Per the research concept: if the model is slow (>5s), fall back to the existing keyword search results.
3. **Detection.** If YouTube's native Ask exists on the page, prefer it (zero cost, zero latency, already contextually aware).
4. **Transcript as context.** The transcript is already fetched by the Transcript tab. The Ask backend should use the same transcript data — no duplicate fetching.

## Deliverables

1. **Backend selection document** — which option was chosen and why, with test evidence.
2. **Updated `ask.ts`** — natural-language Q&A with the chosen backend, keyword search as fallback.
3. **Settings panel update** — model/backend selector (if multiple backends are supported).
4. **Evidence** — at least 3 Q&A exchanges tested against a real video with a transcript.

## Explicit non-goals

- Do NOT redesign the workspace UI. The Ask tab's layout stays the same.
- Do NOT add streaming responses in v1. Full response only.
- Do NOT implement conversation history in v1. Each question is independent.
- Do NOT start Overview/Transcript/Links AI work. This is Ask-only.
