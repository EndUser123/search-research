---
title: "Browser automation failure modes for LLM chat interfaces"
slug: browser-automation-failure-modes-llm-chat
created: 2026-08-01
updated: 2026-08-06
source: session-20260801, session-20260806
tags: [browser-automation, cdp, rich-text-editor, fill-failure, mcp, model-web, transferable-technique, react, evaluate-script, type-text-race]
summary: >
  Modern web LLM chat interfaces use framework-controlled inputs that silently
  ignore DOM-level `fill()` calls. Two distinct mechanisms cause this:
  contenteditable rich-text editors (ProseMirror, Quill) and React-controlled
  `<textarea>` elements. The universal solution evolved from `type_text()` to
  `evaluate_script()` with native value setter (instant, any prompt length).
  Seven failure modes are now documented: rich-text fill, React textarea fill,
  type_text+submitKey race, evaluate_script IIFE syntax, SSE parse staleness,
  file upload restrictions, and file picker traps. Table-driven input method
  selection (not flat priority list) prevents the #1 cause: trying `fill` first
  on sites the table says need `evaluate_script`. Verify-after-submit is
  mandatory because every failure looks like success.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://dev.to/ottoautomaton/your-ai-agent-filled-the-form-and-clicked-save-but-the-data-never-saved-heres-why-4fob (DEV Community, ottoautomaton, 2026)"
  - "Session 019fba58 (2026-08-01): live ensemble test against ChatGPT, Gemini, Perplexity, Duck.ai, Qwen, HuggingChat, Grok"
  - "Session 019fd6f2 (2026-08-06): ensemble test against ChatGPT, DeepSeek, Qwen, Kimi; /tp critique of model-web SKILL.md"
relations:
  - target: wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md
    type: complements
  - target: wiki/concepts/chromium-cdp-websocket-origin-restriction.md
    type: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/tool-fallbacks-as-index-not-authority.md
    type: related
  - target: wiki/concepts/cdp-network-interception-and-sse-capture-for-llm-chat.md
    type: complements
---

# Browser automation failure modes for LLM chat interfaces

## Decision context

**The problem:** The `/model-web` skill needs to send prompts to web-hosted
LLMs via Chrome DevTools MCP. During the first ensemble test (7 LLMs, same
prompt), we discovered that `fill()` silently fails on several sites — the
text appears in the a11y snapshot, the tool reports success, but when Enter
is pressed, nothing happens. The prompt never reaches the conversation.

This cost significant debugging time across the session: Perplexity's first
prompt was sent and lost, Duck.ai required a different method, Qwen's prompt
sat in the textbox but never submitted, and Grok's `fill` text needed
re-typing via `type_text`.

**Why this matters beyond `/model-web`:** any agent that drives a real browser
to interact with modern web apps hits these failure modes. They're not specific
to LLM chat — they apply to any site using React, Vue, Slate, ProseMirror,
DraftJS, or any framework that maintains its own input state.

## The seven failure modes

Source: autonomous AI agent field report (DEV Community, ottoautomaton, 2026) +
live verification in sessions 019fba58 and 019fd6f2. See also `[[chrome-autoconnect-for-authenticated-cdp-sessions]]`
for the connection layer and `[[concurrent-cdp-auth-contention]]` for the
multi-terminal isolation invariant.

### 1. Rich-text editor ignores `fill()` (contenteditable — ProseMirror, Quill)

**What happens:** Perplexity and Grok use contenteditable rich-text editors.
`fill()` sets the DOM element's `.value` property, but the editor framework
(Slate, ProseMirror, DraftJS) maintains its own internal state model separate
from the DOM. On submit, the framework sends its own empty model.

**Why it's insidious:** the snapshot shows your text in the textbox. The tool
call returns "filled successfully." But the submit sends nothing. No error.

### 2. React-controlled `<textarea>` ignores `fill()` (verified 2026-08-06)

**What happens:** Duck.ai, Qwen, DeepSeek, and Kimi use React-controlled
`<textarea>` elements. `fill()` sets the DOM `.value` but React's synthetic
event system doesn't see it — React maintains its own state separate from the
DOM. The tool returns "Successfully filled out the element" (false success).

**Distinction from #1:** this is a different mechanism. Failure mode #1 is
about contenteditable editors (ProseMirror). This is about standard
`<textarea>` elements wrapped by React. Both produce the same symptom (silent
empty submit) but the fix is different.

**Verified sites and working methods (updated 2026-08-06):**

| Site | Editor type | `fill()` works? | Preferred method | Verified |
|---|---|---|---|---|
| ChatGPT | ProseMirror (contenteditable) | ✅ | `fill` + Enter | 2026-08-06 |
| Gemini | Quill (shadow DOM) | ✅ | `fill` + Enter | 2026-08-02 |
| Perplexity | contenteditable | ❌ | `evaluate_script` execCommand | 2026-08-02 |
| Claude | ProseMirror (contenteditable) | ❌ | `evaluate_script` execCommand | 2026-08-02 |
| Duck.ai | React `<textarea>` | ❌ | `evaluate_script` native setter | 2026-08-01 |
| Qwen | React `<textarea>` | ❌ | `evaluate_script` native setter | 2026-08-06 |
| DeepSeek | React `<textarea>` | ❌ | `evaluate_script` native setter | 2026-08-06 |
| Kimi | React `<textarea>` | ❌ | `evaluate_script` native setter + 5-event sequence | 2026-08-06 |
| Grok | ProseMirror (contenteditable) | ❌ | `evaluate_script` execCommand | 2026-08-01 |

### 3. `type_text(submitKey)` race condition on React sites (verified 2026-08-06)

**What happens:** `type_text` with `submitKey="Enter"` types character-by-character
AND presses Enter in the same call. On React-controlled textareas, Enter can
fire before React's synthetic event queue finishes processing all character
events. The model receives only the first sentence.

**Verified incident:** Kimi (session 019fd6f2) — full prompt typed via
`type_text(submitKey="Enter")`. Kimi responded "What would you like me to do?"
— it saw only the first sentence. The remaining text was in the DOM but not in
React's state when Enter fired.

**Fix:** never combine `type_text` with `submitKey` on React sites. Instead:
1. `evaluate_script` with native setter (one call, all chars at once)
2. Verify text landed (read it back)
3. `press_key("Enter")` as a separate step

This is the most subtle failure mode: the prompt APPEARS to submit (the page
navigates, a response comes back) but the model only saw a partial prompt. No
error, no timeout — just degraded response quality.

### 4. `evaluate_script` IIFE syntax rejection (verified 2026-08-06)

**What happens:** the `evaluate_script` MCP tool wraps your function in its own
invocation context. IIFE syntax `(() => { ... })()` fails with
"Unexpected token ';'". The tool expects a function declaration/expression,
not a self-invoking function.

**Fix:** use a plain arrow function: `() => { ... }` or `(el) => { ... }`.
The tool handles calling the function; you just declare it.

### 5. SSE shim stale-parse-format (verified 2026-08-06)

**What happens:** the SSE capture shim (see [[cdp-network-interception-and-sse-capture-for-llm-chat]])
patches `window.fetch` to capture SSE response data. The shim's `extractText()`
parses `data:` lines as JSON to extract text content. When a site changes its
SSE delta format, `chunkCount > 0` and `isDone() == true` but `extractText()`
returns an empty string — silent extraction failure.

**Verified incident:** ChatGPT (session 019fd6f2) — shim captured 2 chunks,
reported done, but extractText() returned "". The JSON parse format in the shim
no longer matched ChatGPT's current SSE delta shape.

**Fix:** when `chunkCount > 0` and `sseData == ""`, inspect raw chunks via
`getChunks().slice(-3)` before falling through to DOM extraction. Report the
format mismatch. See `/model-web` SKILL.md Step 5 stale-parse recovery.

### 6. File upload blocked by workspace restrictions

**What happened:** `upload_file(uid, path)` failed with "not within any
configured workspace roots" regardless of path (`P:/tmp/`, `P:/packages/yt-is/`,
`P:/`, `C:/Users/brsth/`). The Grok Build MCP sandbox restricts upload paths.

**Workaround:** stage files to the MCP server's `os.tmpdir()` (always within
workspace roots). Not yet tested. For long prompts: use `evaluate_script`
(instant, any length up to ~50K chars) instead of shortening.

### 7. File picker trap

**What happened:** clicking "Add files and more" on ChatGPT opened a native OS
file dialog that blocked the entire page. No further CDP commands worked until
the dialog was dismissed. The dialog is invisible to `take_snapshot()` (it's
OS-level, not DOM-level).

**Fix:** never click the "Add files" button. If stuck: `press_key("Escape")`
or operator clicks Cancel.

### 8. Site interstitials and overlays (verified 2026-08-06)

**What happens:** some sites show onboarding overlays, ad interstitials, or
model confirmation dialogs that block the chat composer after navigation.

| Site | What appears | How to dismiss |
|---|---|---|
| Z.ai | Model confirmation dialog or welcome screen | Take snapshot → find confirm/skip button → click |
| MiniMax | Advertisement overlay with "✕" close button | Take snapshot → find close button → click |
| Grok.com | "Prompt Genie" optimization overlay | Click "Dismiss evaluation" |

**Detection:** after `navigate_page`, take a snapshot. If the textbox is not
visible or a modal/dialog covers it, there is an overlay to dismiss before
filling.

## Why `evaluate_script()` is now the preferred method (evolution from type_text)

`fill()` sets the DOM element's `.value` property directly. Framework-controlled
inputs don't listen to `.value` changes — they listen to synthetic events.

`type_text()` simulates real keyboard input: `keydown` → `input` → `keyup`
events fire in sequence. This works but has two problems: (1) slow for long
prompts (~30 chars/sec, so an 8K prompt takes ~4 minutes), and (2) the
`submitKey` race condition (failure mode #3 above).

`evaluate_script()` with the **native value setter** is the current best method:
- Uses `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set`
  which bypasses React's synthetic event wrapper
- Dispatches native `input` + `change` events that React listens to
- **Instant** — no character-by-character typing, handles ~50K char prompts
- For ProseMirror/contenteditable: `execCommand('insertText')` fires the correct
  internal events

**Input method decision tree (table-driven — not a flat priority list):**

The original version of this concept recommended "try fill → fall back to
type_text." Session 019fd6f2 revealed this causes silent failures: operators
try `fill` first (per the flat priority list), it returns false success, and
they don't check the site table which says the site needs `evaluate_script`.
The fix: make the decision **table-driven**. If the site is in the verified
table, use its documented method directly — don't experiment.

```
1. Site in table? → use table's method. Do NOT try fill.
2. Unknown site, <textarea>/<input>? → evaluate_script native setter
3. Unknown site, contenteditable? → evaluate_script execCommand
4. evaluate_script unavailable? → type_text (LAST RESORT)
```

**Prompt-size tradeoff:** `type_text`'s slowness tempted operators to condense
prompts from 8K to 1.5K chars. This loses context the model needs for specific
code-level critique. Models with condensed prompts produce generic advice.
**Do not condense — use evaluate_script instead** (instant, any length).

## The verify-after-submit principle

Every failure mode above **looks like success**. The only reliable defense:

> After any prompt submission, take a snapshot and confirm the prompt text
> appears in the conversation history. If it doesn't, the submission silently
> failed.

This is now Step 3.5 in the `/model-web` adapter protocol. It catches:
- Rich-text fill failures (text in DOM but not in editor state)
- Rate limit walls (prompt accepted but model refused to respond)
- Login walls (session expired mid-loop)
- Submit button still disabled (framework didn't register the change event)

The pattern `[[tool-fallbacks-as-index-not-authority]]` documents the related
principle: fast-decision layers should cross-reference authority, not duplicate
it. Here, `type_text` is the fast-decision fallback when `fill` fails, and
this concept is the authority explaining why.

Source: *"An agent that trusts tool-call success reports will confidently ship
empty forms. An agent that verifies against a fresh load won't."* — ottoautomaton,
DEV Community.

## What this means for our workspace

1. **`/model-web` uses a table-driven input method decision tree** (v1.3, 2026-08-06) —
   the verified table is the single source of truth. If a site is listed, use
   its method directly. Do NOT try `fill` first on known React sites.
2. **`evaluate_script` is the default for all React-controlled textareas** — instant,
   handles full-length prompts, no race conditions.
3. **Step 3.5 verify-after-submit is mandatory** — catches silent failures
   before they waste an entire ensemble round.
4. **Step 3a.5 overlay dismissal** — Z.ai, MiniMax, and other sites with
   interstitials require a snapshot + click-dismiss step between navigation
   and fill.
5. **This pattern applies to any browser automation skill**, not just
   `/model-web`. Any agent driving modern web apps should verify-after-write
   and use `evaluate_script` for framework-controlled inputs.

## Falsifier

This entry is wrong if:
- Chrome DevTools MCP adds automatic rich-text detection (fill works
  everywhere without fallback).
- Chrome DevTools MCP adds a native `set_editor_content` tool that handles
  framework-controlled inputs.
- React changes its synthetic event system so that `.value` assignment
  triggers `onChange` natively (unlikely; would break React's contract).
- Sites migrate back to standard `<textarea>` elements (unlikely; the
  industry trend is toward rich-text editors).

## Receipts

- **Perplexity fill failure:** `fill(uid, text)` reported success, snapshot
  showed text in textbox, `press_key("Enter")` did nothing. Page stayed at
  `perplexity.ai/`. Fixed with `click(uid)` + `type_text(text, submitKey="Enter")`.
  Session 019fba58.
- **Duck.ai fill failure:** Same pattern — fill appeared to work, submit
  button stayed disabled. Fixed with click + type_text. Session 019fba58.
- **Qwen fill failure:** `fill` wrote text but Enter didn't submit. Needed
  `click` + `Ctrl+A` (to clear stale text) + `type_text`. Session 019fba58.
- **ChatGPT file picker:** Clicking "Add files and more" (uid 25_20) opened
  a native OS file dialog. Page was blocked for several tool calls until
  dismissed. Session 019fba58.
- **File upload restriction:** `upload_file(uid, "P:/tmp/file.txt")` →
  "Access denied: path is not within any of the configured workspace roots."
  Tested with 4 different paths, all rejected. Session 019fba58.
- **Kimi/DeepSeek/Qwen fill silent failure:** `fill` returned "Successfully
  filled" on all three React-controlled `<textarea>` sites. On submit, the
  frameworks sent empty strings — no text reached the models. Root cause:
  `fill` sets DOM `.value` but React's state stays empty. Session 019fd6f2.
- **Kimi type_text+submitKey race:** `type_text(prompt, submitKey="Enter")`
  on Kimi resulted in the model seeing only the first sentence ("What would
  you like me to do?"). Enter fired before React processed all character
  events. Session 019fd6f2.
- **ChatGPT SSE stale parse:** SSE shim captured 2 chunks, `isDone()` returned
  true, but `extractText()` returned "". Shim's JSON parse format didn't match
  ChatGPT's current SSE delta shape. Session 019fd6f2.
- **evaluate_script IIFE rejection:** `(() => { ... })()` failed with
  "Unexpected token ';'". Fixed by restructuring as `() => { ... }`.
  Session 019fd6f2.
- **Z.ai/MiniMax interstitials:** Z.ai showed a model confirmation dialog;
  MiniMax showed an ad overlay with "✕" close button. Both blocked the chat
  composer until dismissed. Session 019fd6f2.

## Sources

- [Your AI agent "filled the form" and clicked save — but the data never saved](https://dev.to/ottoautomaton/your-ai-agent-filled-the-form-and-clicked-save-but-the-data-never-saved-heres-why-4fob) (ottoautomaton, DEV Community, 2026) — autonomous AI agent field report identifying the original four failure modes
- Session 019fba58 (2026-08-01) — live verification across 7 LLM chat interfaces
- Session 019fd6f2 (2026-08-06) — ensemble test against ChatGPT/DeepSeek/Qwen/Kimi revealing React textarea fill failure, type_text race, SSE stale parse, IIFE syntax constraint, and site interstitials; /tp critique driving model-web v1.3 update

## Auto-related

- [[chrome-acp-grok-build-browser-driven-agentic-clis]]
- [[cdp-network-interception-and-sse-capture-for-llm-chat]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[multi-llm-aggregator-landscape]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]

