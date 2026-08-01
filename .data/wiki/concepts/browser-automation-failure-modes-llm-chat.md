---
title: "Browser automation failure modes for LLM chat interfaces"
slug: browser-automation-failure-modes-llm-chat
created: 2026-08-01
source: session-20260801
tags: [browser-automation, cdp, rich-text-editor, fill-failure, mcp, model-web, transferable-technique]
summary: >
  Modern web LLM chat interfaces (ChatGPT, Perplexity, Gemini, Duck.ai, Qwen)
  use framework-controlled rich-text editors that silently ignore DOM-level
  `fill()` calls. The text appears in the snapshot but never reaches the
  editor's internal state — submit sends nothing. Four failure modes apply:
  rich-text fill, controlled inputs, file upload restrictions, and file picker
  traps. The universal solution is `click()` + `type_text()` which fires real
  keyboard events the framework listens to. Verify-after-submit is mandatory
  because every failure looks like success.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "https://dev.to/ottoautomaton/your-ai-agent-filled-the-form-and-clicked-save-but-the-data-never-saved-heres-why-4fob (DEV Community, ottoautomaton, 2026)"
  - "Session 019fba58 (2026-08-01): live ensemble test against ChatGPT, Gemini, Perplexity, Duck.ai, Qwen, HuggingChat, Grok"
relations:
  - target: wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md
    type: complements
  - target: wiki/concepts/chromium-cdp-websocket-origin-restriction.md
    type: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/tool-fallbacks-as-index-not-authority.md
    type: related
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

## The four failure modes

Source: autonomous AI agent field report (DEV Community, ottoautomaton, 2026) +
live verification in session 019fba58. See also `[[chrome-autoconnect-for-authenticated-cdp-sessions]]`
for the connection layer and `[[concurrent-cdp-auth-contention]]` for the
multi-terminal isolation invariant.

### 1. Rich-text editor ignores `fill()`

**What happens:** Perplexity, Duck.ai, Qwen, and Grok all use contenteditable
rich-text editors (not standard `<textarea>` elements). `fill()` sets the DOM
element's `.value` property, but the editor framework (Slate, ProseMirror,
DraftJS) maintains its own internal state model separate from the DOM. On
submit, the framework sends its own empty model.

**Why it's insidious:** the snapshot shows your text in the textbox. The tool
call returns "filled successfully." But the submit sends nothing. No error.

**Verified sites and working methods:**

| Site | `fill()` works? | Working method |
|---|---|---|
| ChatGPT | ✅ | `fill` + `press_key("Enter")` |
| Gemini | ✅ | `fill` + `press_key("Enter")` |
| HuggingChat | ✅ | `fill` + click send button |
| Perplexity | ❌ | `click(uid)` + `type_text(text, submitKey="Enter")` |
| Duck.ai | ❌ | `click(uid)` + `type_text(text, submitKey="Enter")` |
| Qwen | ❌ | `click(uid)` + `Ctrl+A` + `type_text(text, submitKey="Enter")` |
| Grok | ❌ | `click(uid)` + `type_text(text, submitKey="Enter")` |

### 2. Controlled inputs (React/Vue) — not yet encountered

Same root cause as #1 but for standard `<input>`/`<textarea>` elements wrapped
by React/Vue. Setting `.value` doesn't fire the framework's synthetic
`onChange`. The fix: native value setter + `dispatchEvent(new Event('input',
{bubbles:true}))` via `evaluate_script`. [INFERENCE] — not directly tested,
from the DEV Community article.

### 3. File upload blocked by workspace restrictions

**What happened:** `upload_file(uid, path)` failed with "not within any
configured workspace roots" regardless of path (`P:/tmp/`, `P:/packages/yt-is/`,
`P:/`, `C:/Users/brsth/`). The Grok Build MCP sandbox restricts upload paths.

**Workaround:** stage files to the MCP server's `os.tmpdir()` (always within
workspace roots). Not yet tested. For long prompts: shorten to fit
`fill`/`type_text`, or have the operator paste manually.

### 4. File picker trap

**What happened:** clicking "Add files and more" on ChatGPT opened a native OS
file dialog that blocked the entire page. No further CDP commands worked until
the dialog was dismissed. The dialog is invisible to `take_snapshot()` (it's
OS-level, not DOM-level). This caused lasting problems — the prompt was typed
but couldn't submit because the dialog was modal.

**Fix:** never click the "Add files" button. If stuck: `press_key("Escape")`
or operator clicks Cancel.

## Why `type_text()` works when `fill()` doesn't

`fill()` sets the DOM element's `.value` property directly. Framework-controlled
inputs don't listen to `.value` changes — they listen to synthetic events
(`onChange`, `onInput`).

`type_text()` simulates real keyboard input: `keydown` → `input` → `keyup`
events fire in sequence. The framework's event listeners catch these and update
the internal state correctly. This is why click + type_text is the universal
fallback — it works regardless of which framework the site uses.

**Cost tradeoff:** `type_text` is slower (~1s per prompt vs instant `fill`)
because it simulates real keystrokes. For the ensemble use case this is
acceptable.

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

1. **`/model-web` has per-site input methods documented** — the site config
   table records which method works for each of 16+ LLM interfaces.
2. **Step 3.5 verify-after-submit is mandatory** — catches silent failures
   before they waste an entire ensemble round.
3. **The discovery procedure for new sites** is: try `fill` → snapshot to
   verify → if empty, use `click` + `type_text` → record in the site table.
4. **This pattern applies to any browser automation skill**, not just
   `/model-web`. Any agent driving modern web apps should verify-after-write.

## Falsifier

This entry is wrong if:
- Chrome DevTools MCP adds automatic rich-text detection (fill works
  everywhere without fallback).
- Sites migrate back to standard `<textarea>` elements (unlikely; the
  industry trend is toward rich-text editors).
- A new MCP tool (e.g., `set_editor_content`) is added that handles
  framework-controlled inputs natively.

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

## Sources

- [Your AI agent "filled the form" and clicked save — but the data never saved](https://dev.to/ottoautomaton/your-ai-agent-filled-the-form-and-clicked-save-but-the-data-never-saved-heres-why-4fob) (ottoautomaton, DEV Community, 2026) — autonomous AI agent field report identifying the four failure modes
- Session 019fba58 (2026-08-01) — live verification across 7 LLM chat interfaces

## Auto-related

- [[chrome-acp-grok-build-browser-driven-agentic-clis]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[skill-catalog]]
- [[parallel-cdp-mcp-servers-openchrome]]
- [[multi-model-ai-workflow-patterns]]

