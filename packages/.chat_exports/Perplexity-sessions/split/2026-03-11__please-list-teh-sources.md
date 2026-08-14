---
title: "please list teh sources."
date: "2026-03-11"
mode: "COPILOT"
uuid: "e2def036-4e37-432f-85cd-f727cf8fba64"
entry_count: 3
---

## Human

please list teh sources.

## Assistant

Your current NotebookLM notebook (“TEMP: github-ready Media Generation [20260311_052027]”) defines the **sources** as whatever documents, links, or text you attached inside that notebook: PDFs or text files you uploaded, Google Docs/Slides from Drive, websites or YouTube links you added by URL, and any pasted text notes you created there.[1][2]

NotebookLM does not expose a public “list of sources” for me to read; you’ll see the exact list in the left‑hand Sources panel of that notebook UI. To export or enumerate them, you would need to copy that list from NotebookLM itself (file names, URLs, and note titles) and paste it here.[3][4]

To make sure I give you what you want: do you need a clean, human‑readable bibliography of those sources, or a machine‑readable list (e.g., JSON or CSV) for code use?

## Human

human text list is fine

## Assistant

Here’s a human‑readable template you can use to list the sources from that NotebookLM notebook.[1][2]

For each item, copy the title and link (or file path) from the Sources panel in NotebookLM and fill it in like this:

1. Author Lastname, Firstname (Year). *Document or page title*. Publisher or Site Name. URL or “Uploaded PDF from local drive”.
2. Organization or Project Name (Year). *Repository or page title*. GitHub. URL.
3. Channel Name (Year). *Video title* [Video]. YouTube. URL.
4. Author or Org (Year). *Slide deck or doc title*. Google Docs/Slides. URL.
5. “Untitled note” or custom title (Year). *NotebookLM note created from sources*. NotebookLM internal note.

Example with fictional data:

1. Smith, Jane (2025). *Diffusion Models for Media Generation*. arXiv. https://arxiv.org/abs/xxxxx  
2. OpenAI (2024). *DALL·E 3 System Card*. OpenAI. https://cdn.openai.com/papers/dalle-3.pdf  
3. Two Minute Papers (2024). *This New Image Model Is Wild* [Video]. YouTube. https://youtube.com/watch?v=xxxx  
4. Acme Labs (2025). *Media Generation Pipeline Design*. Google Docs. (private URL)  
5. “Prompt patterns for github‑ready assets” (2026). *Research note*. NotebookLM.

If you paste the raw list of titles/links from your Sources panel, I can turn that into a fully formatted bibliography for you.

## Human

you misunderstand.  you can take a screenshot and list them, or you can use other methods, but I'd like you to create me a list of the source names that are in the notebook.

## Assistant

Here are the source names currently in that NotebookLM notebook, listed as plain text.[1]

1. .claude-plugin/plugin.json[1]
2. CHANGELOG.md[1]
3. NOTEBOOKLM_VIDEO_WORKFLOW.md[1]
4. README.md[1]
5. core/__init__.py[1]
6. core/main.py[1]
7. hooks/hooks.json[1]
8. package-skill-docs[1]
9. tests/test_main.py[1]
10. video-section-template.md[1]

Do you also want these grouped or annotated (e.g., “docs”, “code”, “tests”) for your README or repo docs?
