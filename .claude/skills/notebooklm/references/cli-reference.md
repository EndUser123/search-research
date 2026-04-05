# NLM CLI Complete Reference

Complete command reference for the `nlm` CLI (notebooklm-mcp).

## Noun-First Commands

### Authentication
```bash
nlm login                              # Authenticate (opens Chrome)
nlm login --profile work               # Named profile
nlm login --check                      # Only check if auth valid
nlm auth status                        # Check current auth
nlm auth list                          # List all profiles
nlm auth delete work --confirm         # Delete a profile
```

### Notebook Management
```bash
nlm notebook list                      # List all notebooks
nlm notebook list --json               # JSON output
nlm notebook list --quiet              # IDs only
nlm notebook list --title              # "ID: Title" format
nlm notebook list --full               # All columns
nlm notebook create "Title"            # Create new notebook
nlm notebook get <id>                  # Get notebook details
nlm notebook describe <id>             # AI summary with topics
nlm notebook describe <id> --json      # JSON output
nlm notebook rename <id> "New Title"   # Rename
nlm notebook delete <id> --confirm     # Delete permanently
nlm notebook query <id> "question"     # Chat with sources
nlm notebook query <id> "question" --json  # JSON output
nlm notebook query <id> "follow up" --conversation-id <cid>
nlm notebook query <id> "question" --source-ids <id1,id2>
```

### Source Management
```bash
nlm source list <notebook-id>          # List sources
nlm source list <notebook-id> --full   # Full details
nlm source list <notebook-id> --url    # "ID: URL" format
nlm source list <notebook-id> --drive  # Show Drive sources with freshness
nlm source list <notebook-id> --drive --skip-freshness  # Faster, skip checks

nlm source add <notebook-id> --url "https://..."           # Add URL
nlm source add <notebook-id> --url "https://..." --wait    # Add and wait
nlm source add <notebook-id> --url "https://youtube.com/..." # YouTube
nlm source add <notebook-id> --text "content" --title "Title"  # Add text
nlm source add <notebook-id> --file /path/to/doc.pdf        # Upload file
nlm source add <notebook-id> --file doc.pdf --wait          # Upload and wait
nlm source add <notebook-id> --drive <doc-id>              # Add Drive doc
nlm source add <notebook-id> --drive <doc-id> --type slides  # Drive type
# Types: doc, slides, sheets, pdf
# Supported files: PDF, TXT, MP3, WAV, M4A

nlm source get <source-id>             # Get source metadata
nlm source get <source-id> --json      # JSON output
nlm source describe <source-id>        # AI summary + keywords
nlm source describe <source-id> --json # JSON output
nlm source content <source-id>         # Raw text content
nlm source content <source-id> --json  # JSON output
nlm source content <source-id> --output file.txt  # Export to file
nlm source delete <source-id> --confirm  # Delete source
nlm source stale <notebook-id>         # List stale Drive sources
nlm source sync <notebook-id> --confirm  # Sync all stale
nlm source sync <notebook-id> --source-ids <ids> --confirm  # Sync specific
```

### Chat Configuration
```bash
nlm chat configure <notebook-id> --goal default
nlm chat configure <notebook-id> --goal learning_guide
nlm chat configure <notebook-id> --goal custom --prompt "Act as a tutor..."
nlm chat configure <notebook-id> --response-length longer   # longer, default, shorter
```

### Research
```bash
nlm research start "query" --notebook-id <id>                    # Fast web
nlm research start "query" --notebook-id <id> --mode deep        # Deep web
nlm research start "query" --notebook-id <id> --source drive     # Fast drive
nlm research start "query" --notebook-id <id> --force            # Override pending
nlm research status <notebook-id>                    # Poll until done (5min max)
nlm research status <notebook-id> --max-wait 0       # Single check
nlm research status <notebook-id> --task-id <tid>    # Specific task
nlm research status <notebook-id> --full             # Full details
nlm research import <notebook-id> <task-id>              # Import all
nlm research import <notebook-id> <task-id> --indices 0,2,5  # Import specific
```

### Studio Artifacts
```bash
nlm studio status <notebook-id>                    # List artifacts + status
nlm studio status <notebook-id> --json             # JSON output
nlm studio status <notebook-id> --full             # All details
nlm studio delete <notebook-id> <artifact-id> --confirm  # Delete artifact
```

### Audio Generation
```bash
nlm audio create <notebook-id> --confirm
nlm audio create <notebook-id> --format deep_dive --length default --confirm
# Formats: deep_dive, brief, critique, debate
# Lengths: short, default, long
nlm audio create <notebook-id> --format brief --focus "key topic" --confirm
```

### Video Generation
```bash
nlm video create <notebook-id> --confirm
nlm video create <notebook-id> --format brief --style whiteboard --confirm
# Formats: explainer, brief
# Styles: auto_select, classic, whiteboard, kawaii, anime, watercolor, retro_print, heritage, paper_craft
```

### Report Generation
```bash
nlm report create <notebook-id> --confirm
nlm report create <notebook-id> --format "Study Guide" --confirm
nlm report create <notebook-id> --format "Create Your Own" --prompt "Summary..." --confirm
# Formats: "Briefing Doc", "Study Guide", "Blog Post", "Create Your Own"
```

### Quiz Generation
```bash
nlm quiz create <notebook-id> --confirm
nlm quiz create <notebook-id> --count 5 --difficulty 3 --confirm
# Count: number of questions (default: 2)
# Difficulty: 1-5 (1=easy, 5=hard, default: 2)
```

### Flashcards Generation
```bash
nlm flashcards create <notebook-id> --confirm
nlm flashcards create <notebook-id> --difficulty hard --confirm
# Difficulty: easy, medium, hard (default: medium)
```

### Mind Map Generation
```bash
nlm mindmap create <notebook-id> --confirm
nlm mindmap create <notebook-id> --title "Topic Overview" --confirm
```

### Slides Generation
```bash
nlm slides create <notebook-id> --confirm
nlm slides create <notebook-id> --format presenter --length short --confirm
# Formats: detailed_deck, presenter_slides (default: detailed_deck)
# Lengths: short, default
```

### Infographic Generation
```bash
nlm infographic create <notebook-id> --confirm
nlm infographic create <notebook-id> --orientation portrait --detail detailed --confirm
# Orientations: landscape, portrait, square (default: landscape)
# Detail: concise, standard, detailed (default: standard)
```

### Data Table Generation
```bash
nlm data-table create <notebook-id> "Extract all dates and events" --confirm
# DESCRIPTION is REQUIRED as second argument
```

### Downloads
```bash
nlm download audio <notebook-id> --id <artifact-id>              # Specific audio
nlm download audio <notebook-id> --output podcast.mp3          # Latest audio
nlm download video <notebook-id>                               # Latest video
nlm download video <notebook-id> --output video.mp4
nlm download report <notebook-id> --output report.md
nlm download mind-map <notebook-id>
nlm download slide-deck <notebook-id>
nlm download infographic <notebook-id>
nlm download data-table <notebook-id>
```

### Interactive Downloads (Quiz, Flashcards)
```bash
nlm download quiz <notebook-id> <artifact-id>                    # JSON (default)
nlm download quiz <notebook-id> <artifact-id> --format json      # Structured
nlm download quiz <notebook-id> <artifact-id> --format markdown  # Markdown
nlm download quiz <notebook-id> <artifact-id> --format html      # Interactive

nlm download flashcards <notebook-id> <artifact-id>                    # JSON
nlm download flashcards <notebook-id> <artifact-id> --format markdown  # Markdown
nlm download flashcards <notebook-id> <artifact-id> --format html      # Interactive
```

### Export to Google Docs/Sheets
```bash
nlm export to-docs <notebook-id> <artifact-id>              # Report → Docs
nlm export to-docs <notebook-id> <artifact-id> --title "My Doc"
nlm export to-sheets <notebook-id> <artifact-id>            # Data Table → Sheets
```

### Aliases
```bash
nlm alias set <name> <uuid>     # Create/update alias
nlm alias get <name>            # Resolve to UUID
nlm alias list                  # List all
nlm alias delete <name>         # Remove
```

### Sharing
```bash
nlm share status <notebook-id>              # View sharing settings
nlm share status <notebook-id> --json       # JSON output
nlm share public <notebook-id>              # Enable public link
nlm share private <notebook-id>             # Disable public link
nlm share invite <notebook-id> <email>      # Invite as viewer
nlm share invite <notebook-id> <email> --role editor  # Invite as editor
```

### Notes
```bash
nlm note list <notebook-id>          # List all notes
nlm note create <id> --content       # Create note
nlm note update <id> --note-id       # Update note
nlm note delete <id> --note-id       # Delete note
```

### Config
```bash
nlm config show                 # Display config (TOML)
nlm config show --json          # Display as JSON
nlm config get <key>            # Get specific setting
nlm config set <key> <value>    # Update setting
```

### Diagnostics
```bash
nlm doctor                      # Run all diagnostic checks
nlm doctor --verbose            # Show additional details
nlm setup list                  # Show all clients and MCP status
nlm setup add claude-code       # Add to Claude Code
nlm setup add cursor            # Add to Cursor
nlm setup remove <client>       # Remove MCP from client
```

## Verb-First Commands

```bash
nlm list notebooks                     # List notebooks
nlm create notebook "Title"            # Create notebook
nlm get notebook <id>                  # Get details
nlm describe notebook <id>             # AI summary
nlm rename notebook <id> "Title"       # Rename
nlm delete notebook <id> --confirm     # Delete
nlm query notebook <id> "question"     # Chat

nlm list sources <notebook-id>         # List sources
nlm add url <notebook-id> <url>        # Add URL
nlm add url <notebook-id> <url> --wait # Add and wait
nlm add text <notebook-id> "content" --title "Title"
nlm add drive <notebook-id> <doc-id>
nlm get source <source-id>
nlm describe source <source-id>
nlm content source <source-id>
nlm delete source <source-id> --confirm
nlm list stale-sources <notebook-id>
nlm stale sources <notebook-id>        # Alternative
nlm sync sources <notebook-id> --confirm

nlm configure chat <notebook-id> --goal default
nlm configure chat <notebook-id> --style conversational
nlm configure chat <notebook-id> --length longer

nlm status research <notebook-id>

nlm create audio <notebook-id> --confirm
nlm create video <notebook-id> --confirm
nlm create report <notebook-id> --confirm
nlm create quiz <notebook-id> --confirm
nlm create flashcards <notebook-id> --confirm
nlm create mindmap <notebook-id> --confirm
nlm create slides <notebook-id> --confirm
nlm create infographic <notebook-id> --confirm
nlm create data-table <notebook-id> "description" --confirm

nlm status artifacts <notebook-id>                 # List artifacts

nlm set alias <name> <uuid>
nlm get alias <name>
nlm list aliases
nlm show aliases
nlm delete alias <name>

nlm show config
nlm get config <key>
nlm set config <key> <value>
```

## Output Formats

| Flag | Description | Available On |
|------|-------------|------|
| (none) | Rich table (human-readable) | All |
| `--json` | JSON output (for parsing) | list, get, describe, query, content, status |
| `--quiet` | IDs only | list |
| `--title` | "ID: Title" format | notebook list |
| `--url` | "ID: URL" format | source list |
| `--full` | All columns/details | list, status |

**Auto-detection:** When stdout is not a TTY (e.g., piping to `jq`), JSON output is used automatically.
