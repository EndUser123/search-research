# NotebookLM Workflows

Complete end-to-end workflows for common NotebookLM tasks.

## Workflow 1: Research → Podcast → Download

Create a research notebook, discover sources, generate a podcast, and download.

```bash
# 1. Authenticate
nlm login

# 2. Create notebook
nlm notebook create "AI Research 2026"
# Output: ID: abc123...

# 3. Set alias for convenience
nlm alias set ai abc123...

# 4. Start deep research
nlm research start "agentic AI trends 2026" --notebook-id ai --mode deep
# Output: Task ID: task456...

# 5. Wait for completion (polls up to 5 minutes)
nlm research status ai --max-wait 300

# 6. Import all discovered sources
nlm research import ai task456...

# 7. Generate podcast
nlm audio create ai --format deep_dive --confirm

# 8. Check status until completed
nlm studio status ai
# Note the artifact ID: audio789...

# 9. Download when ready
nlm download audio ai --id audio789... --output podcast.mp3
```

## Workflow 2: Quick Source Ingestion

Add multiple sources to an existing notebook.

```bash
# Set alias for notebook (one-time)
nlm alias set myproject abc123...

# Add URL sources
nlm source add myproject --url "https://example.com/article1"
nlm source add myproject --url "https://example.com/article2"

# Add text notes
nlm source add myproject --text "My notes on topic X" --title "Topic Notes"

# Add local file
nlm source add myproject --file /path/to/document.pdf

# List all sources to verify
nlm source list myproject
```

## Workflow 3: Generate Study Materials

Create a complete study package from course materials.

```bash
# Use notebook ID directly or alias
nlm quiz create course101 --count 10 --difficulty 3 --confirm
nlm flashcards create course101 --difficulty hard --confirm
nlm report create course101 --format "Study Guide" --confirm

# Check all artifact statuses
nlm studio status course101 --full

# Download when complete
nlm download quiz course101 <quiz-artifact-id> --format html
nlm download flashcards course101 <flashcards-artifact-id> --format html
nlm download report course101 <report-artifact-id> --output study-guide.md
```

## Workflow 4: Content Analysis Pipeline

Generate all content types from research materials.

```bash
# Create all content at once
nlm create audio research --confirm
nlm create video research --confirm
nlm create report research --confirm
nlm create quiz research --confirm
nlm create flashcards research --confirm
nlm create mindmap research --confirm
nlm create slides research --confirm
nlm create infographic research --confirm

# Poll for completion
nlm status artifacts research --full

# Download all when ready (replace with actual artifact IDs)
nlm download audio research <audio-id> --output podcast.mp3
nlm download video research <video-id> --output overview.mp4
nlm download report research <report-id> --output report.md
nlm download mind-map research <mindmap-id> --output mindmap.txt
nlm download slide-deck research <slides-id> --output slides.txt
nlm download infographic research <infographic-id> --output overview.png
```

## Workflow 5: Collaborative Notebook Setup

Set up a notebook for team collaboration.

```bash
# Create notebook
nlm notebook create "Team Documentation"

# Set alias
nlm alias set teamdocs <notebook-id>

# Add sources from multiple URLs
nlm source add teamdocs --url "https://docs.example.com/api"
nlm source add teamdocs --url "https://docs.example.com/guide"

# Enable public access
nlm share public teamdocs

# Invite collaborators
nlm share invite teamdocs --email colleague@example.com --role viewer
nlm share invite teamdocs --email lead@example.com --role editor

# Verify sharing settings
nlm share status teamdocs
```

## Workflow 6: Drive Source Management

Sync and manage Google Drive sources.

```bash
# Check which Drive sources need syncing
nlm source stale notebook-alias

# Sync all stale sources
nlm source sync notebook-alias --confirm

# Or sync specific sources
nlm source sync notebook-alias --source-ids id1,id2,id3 --confirm
```

## Common Patterns

### Poll for Completion

For long-running operations (audio, video, deep research):

```bash
# Single check (returns immediately)
nlm studio status <notebook-id> --max-wait 0

# Continuous polling (blocks until done or timeout)
nlm studio status <notebook-id> --max-wait 300
```

### Use Aliases for Convenience

```bash
# Set once
nlm alias set main <long-uuid-here>

# Use everywhere
nlm notebook query main "what are the key points?"
nlm source list main
nlm audio create main --confirm
```

### Filter by Specific Sources

```bash
# Generate artifact from specific sources only
nlm report create <notebook-id> --source-ids id1,id2,id3 --confirm

# Query specific sources
nlm notebook query <notebook-id> "question" --source-ids id1,id2
```

### Export to Google Workspace

```bash
# Export report to Google Docs
nlm export to-docs <notebook-id> <artifact-id>

# Export data table to Google Sheets
nlm export to-sheets <notebook-id> <artifact-id>
```
