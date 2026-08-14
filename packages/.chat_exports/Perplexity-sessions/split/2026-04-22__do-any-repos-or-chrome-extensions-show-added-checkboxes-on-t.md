---
title: "do any repos or chrome extensions, show added checkboxes on the notebooklm page?"
date: "2026-04-22"
mode: "COPILOT"
uuid: "e9c38108-2354-4679-91c9-0d09dbc01ce3"
entry_count: 1
---

## Human

do any repos or chrome extensions, show added checkboxes on the notebooklm page?

## Assistant

Yes, multiple Chrome extensions and repositories add checkboxes to the NotebookLM page, primarily for batch selection of notes or sources in the sidebar. These enhancements address NotebookLM's native limitations in multi-select and organization, injecting UI elements like checkboxes via content scripts.[1][2][3]

## NotebookLM Enhancer

This open-source Chrome extension overlays a folder system on NotebookLM's sidebar, including a "Batch Delete" feature that adds checkboxes next to notes for multi-select. Users toggle "Selection Mode" via a header icon, click rows or checkboxes to select, then delete in bulk—automatically handling NotebookLM's confirmation modals without manual clicks.[2][3][1]

Repo: https://github.com/CGCM070/NotebookLM_Enhancer (MV3 extension with Angular/Tailwind UI, drag-drop, themes).[3]

Chrome Web Store: https://chromewebstore.google.com/detail/notebooklm-enhancer/geedlihiipifeifhnmjhmnmkffanlhpg.[4]

Install by loading unpacked from the repo (enable Developer mode in chrome://extensions).[1]

## NotebookLM Source Plus

This repo provides a Chrome extension focused on source management, explicitly adding toggle checkboxes to the NotebookLM sources list. Toggles sync with native checkboxes, preserving app state, and save selections locally per notebook for bulk actions.[5]

Repo: https://github.com/ramitdour/notebooklm-source-plus (load unpacked via chrome://extensions).[5]

## Other Extensions

Kortex-NotebookLM adds filter buttons for sources (e.g., show PDFs only), which may involve checkbox-like toggles, but primarily focuses on imports/exports rather than explicit multi-select checkboxes.[6][7]

No native NotebookLM feature adds extra checkboxes beyond basic source selection; these are all third-party injections.[8]

## Next Steps

- Clone https://github.com/CGCM070/NotebookLM_Enhancer, load in Chrome extensions developer mode, refresh NotebookLM—checkboxes appear in the new sidebar for batch ops.[3][1]
- Test on a notebook with 10+ notes; edge case: reorganize folders post-update as storage schema evolved.[1]
- Uncertainty: Repos may update; verify latest releases for compatibility (assumes current NotebookLM UI as of Apr 2026). No conflicts found in primary sources.[3]
