---
title: "is there an extention or repo for chrome that allows saving a page as markdown?"
date: "2025-12-09"
mode: "COPILOT"
uuid: "32fae13c-aa17-4baf-945e-415ed990df9d"
entry_count: 1
---

## Human

is there an extention or repo for chrome that allows saving a page as markdown?

## Assistant

Yes, there are excellent open-source Chrome extensions and GitHub repositories available for this.

The best options fall into two categories: **browser extensions** (for one-click saving) and **CLI/Library repos** (for developers who want to automate the process).

### **Top Recommendation: MarkDownload**
This is widely considered the gold standard. It is both a polished Chrome extension and an open-source repository.

*   **Type:** Chrome Extension & Open Source Repo
*   **Repo:** [deathau/markdownload](https://github.com/deathau/markdownload)
*   **Why it's the best:**
    *   **Preview & Edit:** It shows you a preview of the Markdown before you save, allowing you to delete junk text (ads, navigation) immediately.
    *   **Image Handling:** It can download images alongside the Markdown file and rewrite the links to point to your local copies (crucial for true archiving).
    *   **Customization:** You can customize the "Frontmatter" (metadata at the top of the file) to include the URL, date, and author, which is perfect for apps like Obsidian or Notion.
    *   **Selection Only:** You can highlight just one paragraph, right-click, and save only that selection as Markdown.

### **Other Notable Extensions**

| Name | Best For | Key Feature |
| :--- | :--- | :--- |
| **Copy as Markdown** | **LLM Context** | Extremely lightweight. It adds a context menu item to copy selection or page as Markdown directly to your clipboard (great for pasting into ChatGPT/Claude). |
| **Webpage to Markdown** | **Simplicity** | A simple "one-click" extension. It uses the `Turndown` library to convert the page immediately without a complex popup UI. |
| **SingleFile** | **Archival** | While primarily for saving exact HTML replicas, it has options/companion tools for text extraction. It is the most robust tool for saving a page *exactly* as it looks, but MarkDownload is better for editable text. |

### **Best GitHub Repos (CLI & Libraries)**
If you are looking for a "repo" because you want to run a script or build a tool, these are the industry-standard libraries used to build the extensions above.

#### 1. **url-to-markdown-cli-tool**
*   **Repo:** `mmdclx/url-to-markdown-cli-tool`
*   **Description:** A command-line tool that uses a headless browser (Puppeteer) to visit a URL, strip out the navigation/ads (using Mozilla's Readability), and save the clean article as Markdown.
*   **Use case:** `url-to-md https://example.com -o article.md`

#### 2. **Turndown**
*   **Repo:** `mixmark-io/turndown`
*   **Description:** This is the Javascript engine that powers most of the extensions listed above. It converts HTML input into Markdown.
*   **Use case:** If you are building your own scraper or extension, this is the library you would import to handle the text conversion.

#### 3. **r/Archivist (Community Scripts)**
*   **Context:** There is no single "Archivist" repo, but many users in the **Obsidian** and **Data Hoarder** communities share Python scripts that use `BeautifulSoup` and `Markdownify` to bulk-download pages.
*   **Repo Search Term:** `github.com search: "python script save url to markdown"` will yield simple Python scripts if you prefer a 50-line code snippet over a full application.
