# NotebookLM Markdown Exporter — Usage Guide

This is a **production-ready Python script** that replaces NotebookLM Export Pro's Markdown export functionality with your own codebase. No browser extension needed.

## What it does

- ✓ Exports **sources** (transcripts, documents) from NotebookLM notebooks
- ✓ Exports **chat history** with Q&A pairs
- ✓ Exports **notes** if present
- ✓ Bulk exports **multiple notebooks** from a config file
- ✓ Saves all output as **clean Markdown files**
- ✓ Runs **headless** (no UI) or headful (for debugging)

## Installation

```bash
pip install playwright
playwright install chromium
```

## Usage

### Single notebook export
```bash
python notebooklm_exporter.py --url "https://notebooklm.google.com/notebook/abc123"
```

### Export multiple notebooks from config
```bash
# Create notebooks.json with list of URLs
python notebooklm_exporter.py --config notebooks.json
```

### Export only sources (skip chat/notes)
```bash
python notebooklm_exporter.py --url "..." --export sources
```

### See browser while exporting (headful mode)
```bash
python notebooklm_exporter.py --url "..." --headful
```

### Verbose logging
```bash
python notebooklm_exporter.py --url "..." --verbose
```

### Custom output directory
```bash
python notebooklm_exporter.py --url "..." --output ./my_exports
```

## Config File Format

**notebooks.json:**
```json
{
  "notebooks": [
    "https://notebooklm.google.com/notebook/abc123",
    "https://notebooklm.google.com/notebook/def456"
  ]
}
```

Or just a simple list:
```json
[
  "https://notebooklm.google.com/notebook/abc123",
  "https://notebooklm.google.com/notebook/def456"
]
```

## Output

Exports are saved to `./exports/` (customizable via `--output`) with filenames like:

- `abc123_sources_2026-04-12_102345.md` — All sources and their transcript content
- `abc123_chat_2026-04-12_102345.md` — Q&A chat history
- `abc123_notes_2026-04-12_102345.md` — Timestamped notes

Each file is self-contained Markdown, ready for Git, Obsidian, or your own corpus.

## Markdown output format

### Sources
```markdown
# Sources

## 1. Video Title Here
**URL:** https://youtube.com/watch?v=...
**Type:** YouTube

[Full transcript text here...]

---

## 2. Another Source
...
```

### Chat History
```markdown
# Chat History

## Q1
What are the main themes?

**A1:**
Based on your sources, the main themes are...

---

## Q2
...
```

## Automation Example: Weekly Export Script

Save as `weekly_export.sh`:

```bash
#!/bin/bash
# Export all notebooks every Sunday at 10pm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y-%m-%d)

cd "$SCRIPT_DIR"

echo "📓 Weekly NotebookLM export - $TIMESTAMP"

python notebooklm_exporter.py \
  --config notebooks.json \
  --export all \
  --output "./exports/$TIMESTAMP"

# Commit to Git
git add exports/
git commit -m "Weekly NotebookLM export: $TIMESTAMP"
git push

echo "✓ Export and backup complete"
```

Add to crontab:
```bash
crontab -e
# Add this line:
0 22 * * 0 /path/to/weekly_export.sh >> /path/to/export_log.txt 2>&1
```

## Troubleshooting

### "Playwright not installed"
```bash
pip install playwright
playwright install chromium
```

### "Invalid NotebookLM URL"
Make sure URL is:
- Full URL with `https://notebooklm.google.com/notebook/...`
- No shortened or redirected URLs

### "No sources found"
- Wait for NotebookLM to fully load
- Try `--headful` mode to see what's happening
- Check if you're logged in to the correct Google account

### "Browser timeout"
Add more wait time or use `--headful` to debug:
```bash
python notebooklm_exporter.py --url "..." --headful --verbose
```

## Integration with your yt→NotebookLM pipeline

### Step 1: After bulk importing videos into sharded notebooks
```bash
python notebooklm_exporter.py --config notebooks.json --export all
```

### Step 2: Store in your corpus
```bash
cp exports/*_sources_*.md ~/corpus/transcripts/markdown/
```

### Step 3: Backup to Git
```bash
git add ~/corpus/transcripts/markdown/
git commit -m "Updated transcripts from NotebookLM"
```

### Step 4: Index for semantic search
Use the Markdown files with any vector DB or search tool.

## API / Programmatic Usage

```python
import asyncio
from notebooklm_exporter import NotebookLMExporter

async def export_my_notebooks():
    exporter = NotebookLMExporter(output_dir="./exports")

    notebooks = [
        "https://notebooklm.google.com/notebook/abc123",
        "https://notebooklm.google.com/notebook/def456",
    ]

    for url in notebooks:
        print(f"Exporting {url}...")
        results = await exporter.export_notebook(url, export_type="all")
        for export_type, file_path in results.items():
            print(f"  {export_type}: {file_path}")

    await exporter.close()

asyncio.run(export_my_notebooks())
```

## Key Differences from NotebookLM Export Pro Extension

| Feature | This Script | Export Pro Extension |
|---------|-------------|---------------------|
| Bulk export multiple notebooks | ✓ Yes (via config) | ✓ Yes |
| Markdown output | ✓ Yes | ✓ Yes |
| GUI needed | ✗ No | ✓ Yes |
| Headless automation | ✓ Yes | ✗ No |
| Schedulable (cron/task) | ✓ Yes | ✗ No |
| Cost | ✓ Free | Varies |
| Maintainability | ✓ Your code | Third-party |

## Caveats

- **NotebookLM DOM may change**: Selectors are based on April 2026 UI. If Google redesigns, some selectors may need updating. Fallback selectors minimize breakage.
- **Large notebooks are slow**: Extracting 500+ sources takes time. Run overnight for big batches.
- **Chat history is optional**: Not all notebooks have extensive chat history; exports gracefully handle missing sections.

## Next Steps

1. **Save the script** to your codebase.
2. **Create notebooks.json** with your shard notebook URLs.
3. **Test with one notebook first**:
   ```bash
   python notebooklm_exporter.py --url "https://..." --verbose
   ```
4. **Set up weekly cron job** for automated backups.
5. **Store exports in Git** for version history + auditing.

You now have **full control over your transcript export workflow** without relying on third-party extensions.
