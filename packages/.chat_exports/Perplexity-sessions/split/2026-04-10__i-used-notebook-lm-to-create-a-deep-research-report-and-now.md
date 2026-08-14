---
title: "I used Notebook LM to create a deep research report, and now I would like to export it as Markdown. How do I do that fro"
date: "2026-04-10"
mode: "COPILOT"
uuid: "81b2e653-08da-40cb-99e4-9f34e7fb5b48"
entry_count: 4
---

## Human

I used Notebook LM to create a deep research report, and now I would like to export it as Markdown. How do I do that from Notebook LM?

## Assistant

Based on the current state of Notebook LM (as of April 2026), **Notebook LM does not have a native built-in Markdown export feature for deep research reports**—you'll need to use a third-party Chrome extension or manual workaround.[1]

## Native Export Options

Notebook LM's official export options include exporting to Google Docs, Google Sheets, PDF, and PowerPoint (for slides). For deep research reports specifically, you can add the report as a source to your notebook and then export it via standard methods like sending to Google Docs.[2][1]

## Third-Party Markdown Export

The most practical solutions are Chrome extensions that add Markdown export capability:

- **NotebookLM Ultra Exporter**: Exports notes and reports to Markdown, Word, PDF, and more with one-click buttons integrated into the UI and batch export support.[3]
- **NotebookLM Export Pro**: Adds an Export button directly to Notebook LM for downloading to Markdown, PDF, or Notion format.[4]

Both extensions appear in the Chrome Web Store and integrate seamlessly into the Notebook LM interface.

## Alternative Workflow

If you prefer not to install an extension, you can export to Google Docs (the native option), then use Google Docs' built-in "Download" feature to save as .docx or PDF, followed by converting that output to Markdown using a tool like Pandoc or an online converter. However, this is more manual than using an extension.[2]

**Which approach fits your workflow better—installing a Chrome extension for direct one-click Markdown export, or converting through Google Docs first?**

## Human

When I click on the source in Notebook LM, I don't see any button that says Save to Google Docs.

## Assistant

You're right to clarify—the "Export to Google Docs" button doesn't appear when you click on a source. Here's the correct workflow:

## Correct Export Path

The export functionality is specifically for **saved Notes and Reports**, not sources. The steps are:[1][2]

1. **Save your deep research report as a Note** first—when you generate content (a report, study guide, briefing doc), click the "Save to Note" button below the response to store it in your notebook.
2. **Access the three-dot menu** in the Studio Panel next to your saved note.
3. **Select "Export to Google Docs"**—this creates a new Google Doc with your content in a new browser tab.

## Current Limitations

Notebook LM's native export is limited to individual notes and reports saved within the Studio Panel. You cannot directly export from the source panel itself—only from saved outputs. If your deep research report exists only as a generated response (not saved as a note), you'll need to save it first before the export option appears.[3][1]

Once in Google Docs, you can then download as Markdown using a converter, or use a third-party Chrome extension (like NotebookLM Ultra Exporter) to convert directly from the saved note to Markdown in one step.

**Is your deep research report currently saved as a Note in the Studio Panel, or is it still just a generated response that you haven't saved yet?**

## Human

Once I've already saved the source I don't see a save as note first.

## Assistant

You're correct—I misunderstood your workflow. Based on the official Google support docs and current guides, here's the accurate process:

## Exporting a Deep Research Report to Markdown

**The issue:** Deep Research reports don't have a native Markdown export option. The "Export to Google Docs" button only appears in the Studio panel for **saved Notes**, not for sources or the report itself.[1]

**Your actual workflow should be:**

1. **Generate your Deep Research report** (which creates web research with citations)
2. **Add it as a source to your notebook** (or save key findings as a Note)
3. **Then use the three-dot menu in the Studio panel** to "Export to Google Docs"[1]
4. **From Google Docs, download as markdown** using a tool like Pandoc or a Google Docs to Markdown converter

Alternatively, if your report exists only as a generated response in chat:

- Use a **third-party Chrome extension** like NotebookLM Ultra Exporter to capture it directly to Markdown in one step[2]

## Why There's Confusion

NotebookLM's export model distinguishes between **generated outputs** (which live temporarily in Studio) and **saved Notes** (which persist and have export options). Deep Research results need to be explicitly saved or added as a source before the export button becomes available.[3]

**What's your Deep Research report currently—is it saved as a Note in the Studio panel, or does it exist only as a generated response you haven't saved?**

## Human

What's the most popular extension to highlight something on a webpage like Notebook LM and then right-click it and go save as Markdown?

## Assistant

The most popular extensions for this workflow are:

## Top Choice: Web Highlights

**Web Highlights** (4.8/5 stars) is the highest-rated option. It supports exactly your use case:[1]

- Right-click → save highlighted text directly[2]
- One-click export to Markdown, Notion, Obsidian, and other tools[3][2]
- Free offline highlighting with no account required[1]
- Privacy-focused (data stays local in your browser)[2]

## Strong Alternative: Web Highlighter

**Web Highlighter** provides a simpler, lightweight option:[4]

- Right-click or Ctrl+Shift+S to capture selected text instantly[4]
- Export as Markdown, JSON, or CSV[4]
- Fully local/private (no cloud, no account)[4]
- Tag-based organization[4]

## If Using Obsidian

If you use Obsidian as your knowledge base, **Obsidian Web Clipper** has native highlighting that integrates directly. You can right-click to highlight, then clip with one click to save as Markdown in Obsidian.[5][6]

## Bottom Line

For your workflow (highlight Notebook LM content → right-click → save as Markdown), **Web Highlights is the consensus best choice** due to its polish, active development (updated January 2026), and seamless Markdown export. It's also free and ad-free at its core feature level.[1]
