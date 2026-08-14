---
title: "in lmstudio on windows, I see an integration for rag.  how do I enable it optimally?"
date: "2026-04-04"
mode: "COPILOT"
uuid: "9ebaa19d-afd5-4122-92bd-7ee9f09f8d86"
entry_count: 3
---

## Human

in lmstudio on windows, I see an integration for rag.  how do I enable it optimally?

## Assistant

LM Studio on Windows includes a built-in RAG feature for chatting with attached documents, automatically enabling retrieval for long files. Optimal use involves attaching concise, relevant docs and crafting specific queries.

## Enabling RAG
Attach .docx, .pdf, or .txt files directly to a chat session via the attachment icon. LM Studio loads short docs fully into context; for longer ones, it switches to RAG to retrieve relevant chunks.[1]

Update to the latest version first: Download from lmstudio.ai, run the installer—it preserves models and settings.[2]

## Optimal Settings
- Use models with large contexts (e.g., Llama 3.1, Mistral Nemo) to minimize RAG reliance on short docs.
- Query with precise terms/phrases from docs to boost retrieval accuracy (e.g., "summarize section on X using Y term").
- Limit to 5 docs per chat for native support; unload/reload as needed.[3]

## Advanced: Big RAG Plugin
For large-scale RAG (GBs of docs), install the "Big RAG" plugin via LM Studio's Plugins settings (search "big-rag"). Set Documents Directory (e.g., C:\MyDocs) and Vector Store path; use nomic-embed-text-v1.5-GGUF for embeddings. Tune chunk size (512-1024), affinity threshold (0.5 default, lower to 0.3 for recall), retrieval limit (5-10).[4][5]

Next: Test with a sample PDF—what doc types/hardware specs are you using?[4][1]

## Human

how do I configure big rag?

## Assistant

LM Studio's Big RAG plugin handles large document libraries via configurable indexing and retrieval. Configure it in the Plugins section after installation for optimal performance on Windows.

## Installation Steps
Download from LM Studio Hub (search "big-rag"), install via Plugins > Install. Requires Node.js (install from nodejs.org if missing).[page:0 from previous]

Run `npm install` then `npm run dev` in the plugin directory (e.g., C:\Users\[user]\.lmstudio\plugins\big-rag).[page:1]

## Required Settings
Set **Documents Directory** to your doc folder (e.g., C:\MyDocs)—supports PDFs, TXT, etc. Set **Vector Store** to a dedicated path (e.g., C:\.lmstudio\big-rag-db); use nomic-embed-text-v1.5-GGUF model (download via LM Studio).[page:1]

First run auto-indexes; flip **Manual Reindex Trigger** ON for rebuilds, toggle OFF after.[page:1]

## Optimal Configurations
| Dataset Size | Chunk Size | Affinity Threshold | Retrieval Limit | Notes |
|--------------|------------|---------------------|-----------------|-------|
| Small (<100 files, <100MB) | 512 (default) | 0.5 (default) | 5 (default) | Defaults suffice [page:1] |
| Medium (100-1000 files, 100MB-1GB) | 768 | 0.4 | 8 | Balance recall/speed [page:1] |
| Large (1GB+) | 1024 | 0.3-0.4 | 10+ | Lower threshold if low recall; monitor RAM [page:1] |

Test with sample docs first. Uncertainty: Docs dated 2025; verify in-app for 2026 updates.[][page:1]

Next step: Create test folder, index, query—what dataset size/docs? 

## Human

where's the setting for that?

## Assistant

Big RAG settings are in LM Studio's Plugins panel on Windows. Access via the main menu or sidebar after installing the plugin.

## Access Path
Open LM Studio > Plugins (sidebar icon or hamburger menu > Plugins). Select "big-rag" > Configure/Edit.[1]

If not visible, restart LM Studio post-install; path typically `C:\Users\[YourUser]\.lmstudio\plugins\big-rag\config.json` for manual edits (backup first).[]

## Key Settings Locations
- **Documents Directory/Vector Store**: Plugin config UI fields; click "Index" to apply.
- **Advanced (Chunk/Affinity)**: Edit `config.json` or UI sliders if exposed.[page:1]

Verify in latest version (check lmstudio.ai changelog). Next: Screenshot your Plugins view? [page:1][]
