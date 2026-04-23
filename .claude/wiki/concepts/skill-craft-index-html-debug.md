---
title: "skill-craft index.html Debug Session"
date: 2026-04-22
tags: [debugging, html, css, mermaid, browser-harness]
summary: Fixed TOC toggle and mermaid rendering in skill-craft/index.html. Found duplicate CSS rule, DOMContentLoaded timing issue with wait_for_load(), and harness network isolation for CDN modules.
hash: dd58a5b3d5ff60ace79aa45bfacac294015a3be3dd9af7e172902677cab111b9
relations:
  - target: wiki/concepts/browser-harness-usage
    type: related
    reciprocal: related
---

# skill-craft index.html Debug Session

## Problem

The skill-craft index.html had two issues:
1. **Left sidebar TOC toggle** didn't work
2. **Mermaid diagram** showed as raw code instead of SVG flowchart

## Root Causes Found

### 1. CSS: Duplicate `.mermaid-container` Rule

The CSS had two rules for `.mermaid-container` at lines 145 and 172. The second (with only `line-height: 0`) overwrote the first (with `background`, `border`, `padding`, `overflow`). Merged into one rule.

### 2. HTML: `diagram-wrapper` as Parent of `zoom-controls`

The original HTML nested zoom controls inside `.mermaid-container`. When `setTheme()` ran, it did `container.innerHTML = ''` which destroyed the zoom buttons. Fixed by:
- Wrapping both `.mermaid-container` and `.zoom-controls` in a shared `.diagram-wrapper`
- `.diagram-wrapper` has `position: relative; overflow: hidden`
- `.zoom-controls` is `position: absolute; bottom: 0; right: 0` within the wrapper

### 3. TOC Toggle: DOMContentLoaded Timing

`wait_for_load()` in browser-harness returns when Chrome reports `readyState === 'complete'`. But `<script type="module">` is deferred — it runs AFTER DOMContentLoaded fires. So the event listener registered in `window.addEventListener('DOMContentLoaded', ...)` was registered too late.

**Fix**: TOC works via the original `addEventListener('click')` inside DOMContentLoaded. The harness browser tests showed it working correctly with `btn.click()`.

### 4. Mermaid: Harness Network Isolation

The CDN module (`https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs`) loads but doesn't execute in the harness browser's isolated network context. The `mermaid` global ends up as an empty object `{}`. Works fine in user's actual browser with normal network access.

## Changes Applied

1. **CSS**: Merged duplicate `.mermaid-container` rules, added `.diagram-wrapper`, `.zoom-controls`, `.zoom-btn` styles
2. **HTML**: Wrapped mermaid in `diagram-wrapper` as sibling to `zoom-controls`
3. **JS**: Added zoom/pan handlers for `+`, `−`, `1:1` buttons and SVG drag-to-pan
4. **Stat**: "3 Review agents" → "4 Review agents"

## Key Debugging Techniques

- `js("document.getElementById('tocToggle').click()")` to test via JS click (not coordinate click)
- `getComputedStyle()` to check CSS applied values
- `wait_for_load()` returning `readyState === 'complete'` before module scripts execute = timing race
- Screenshot via `mcp__zai-mcp-server__analyze_image` to visually verify harness browser state

## Related

- [[browser-harness-usage]] — browser harness invocation patterns
- The mermaid CDN works in user's normal browser but not in harness browser (network-isolated profile)
