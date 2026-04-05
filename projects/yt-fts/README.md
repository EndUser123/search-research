# yt-fts - YouTube Full Text Search 
`yt-fts` is a command line program that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to scrape all of a YouTube 
channels subtitles and load them into a sqlite database that is searchable from the command line. It allows you to
query a channel for specific key word or phrase and will generate time stamped YouTube urls to
the video containing the keyword. 

It also supports semantic search via the [OpenAI embeddings API](https://beta.openai.com/docs/api-reference/), [Gemini embedding API](https://ai.google.dev/gemini-api/docs/embeddings) and using [chromadb](https://github.com/chroma-core/chroma).

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)
- [LLM/RAG Chat Bot](#llm-chat-bot)
- [Video Summaries](#summarize)
- [Semantic Search](#vsearch-semantic-search)
- [CHANGELOG](CHANGELOG.md)

https://github.com/NotJoeMartinez/yt-fts/assets/39905973/6ffd8962-d060-490f-9e73-9ab179402f14

## Platform Support

**yt-fts supports YouTube only.**

After extensive research and testing of alternative video platforms (Rumble, Odysee, BitChute), we determined that multiplatform support is not practical due to:

- **Platform fragility**: Alternative platforms frequently change their APIs or block automated access
- **High complexity**: Workarounds require browser automation (Selenium) or full blockchain nodes (LBRY)
- **Low value**: <1% of educational content exists on alternative platforms
- **Maintenance burden**: Keeping extractors working across multiple platforms diverts focus from core functionality

**YouTube works perfectly** with yt-dlp and youtube-transcript-api, providing reliable access to 99% of video content with subtitles.

If you need transcript search for alternative platforms, we recommend:
1. Downloading videos manually with platform-specific tools
2. Using Whisper or similar for transcription
3. Importing transcripts into yt-fts manually

For details on our research, see: [yt-fts-alt-platforms Knowledge Package](https://github.com/NotJoeMartinez/yt-fts/tree/main/yt-fts-alt-platforms/KNOWLEDGE_PACKAGE)

## Performance & Optimization

### Smart Quota Management

yt-fts includes intelligent quota management that automatically chooses between YouTube API and yt-dlp based on efficiency:

**Real API Costs:** 1 quota unit per API call (fetches up to 50 videos)

**Smart Decision Logic:**
- **≤3 missing videos**: Uses yt-dlp (avoids API overhead)
- **4-10 missing videos**: Context-dependent decisions
- **>10 missing videos**: Uses API (batch efficiency wins)

**Three Operation Modes:**
- **🟡 Conservative** (<15% quota remaining): Minimal API usage, preserves quota
- **🟢 Balanced** (15-60% quota remaining): Smart decisions based on channel needs
- **⚪ Aggressive** (>60% quota remaining): Freely uses API for maximum speed

### Database Optimizations

**Strategic Indexing:**
- Optimized queries with targeted WHERE IN clauses
- Strategic indexes on frequently queried columns
- Batch operations for channel statistics

**Performance Benefits:**
- Faster channel resolution and caching
- Optimized batch download queries
- Improved search performance across large datasets

## Installation 

### pip (Traditional)

```bash
pip install yt-fts
```

### uv (Modern - Recommended)

[uv](https://astral.sh/blog/uv) is a fast Python package manager that eliminates manual venv activation:

```bash
# Install uv
pip install uv

# Use uv run - automatically detects and uses .venv
uv run python -m yt_fts download "https://www.youtube.com/@channel"
```

**Benefits:**
- No manual venv activation needed
- 10-100x faster than pip
- Unified tooling (replaces pip, venv, pip-tools, pyenv)

### Configuration Notes

**python-dotenv** is required for loading `.env` files (API keys, configuration):
```bash
# Install with uv
uv add python-dotenv

# Or with pip
pip install python-dotenv
```

**Windows:** If using uv and see hardlink warnings, set `UV_LINK_MODE=copy`:
```powershell
# For current session
$env:UV_LINK_MODE = "copy"

# Permanently (add to PowerShell profile)
[System.Environment]::SetEnvironmentVariable("UV_LINK_MODE", "copy", "User")
```

This occurs when cache and target directories are on different filesystems (common with drives mounted via WSL or network paths).

## Troubleshooting

### "No YouTube API keys provided" error (uv installations)

If you see this error despite having API keys in your `.env` file, it means `python-dotenv` is not installed. This can happen with `uv` installations when the lock file is out of sync with `pyproject.toml`.

**Symptoms:**
- Error: `yt-api discovery failed: No YouTube API keys provided. Set YOUTUBE_API_KEY in .env`
- Warning: `python-dotenv not installed. To load .env files, install with: pip install python-dotenv`

**Fix:**

```bash
# From your project directory
uv lock --refresh
uv sync
```

This synchronizes the `uv.lock` file with `pyproject.toml` and installs all dependencies including `python-dotenv`.

**Verification:**

```bash
# Confirm python-dotenv is installed
uv run python -c "from dotenv import load_dotenv; print('OK')"

# Confirm .env loading works
uv run python -c "from yt_fts.utils.config import find_and_load_env; import os; find_and_load_env(); print('API key:', bool(os.getenv('YOUTUBE_API_KEY')))"
```

**Prevention:** After modifying `pyproject.toml`, always run both `uv lock --refresh` and `uv sync` to keep dependencies synchronized.


## Commands

### `download`
Download subtitles for a channel or playlist. 

Takes a channel or playlist URL as an argument. Specify the number of jobs to parallelize the download with the `--jobs` flag. 
Use the `--cookies-from-browser` to use cookies from your browser in the requests, will help if you're getting errors 
that request you to sign in. You can also run the `update` command several times to gradually get more videos into the database. 

```bash
# Download channel
yt-fts download --jobs 5 "https://www.youtube.com/@3blue1brown"
yt-fts download --cookies-from-browser firefox "https://www.youtube.com/@3blue1brown"

# Download playlist
yt-fts download --playlist "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab"
```

**Options:**
- `-p, --playlist`: Download all videos from a playlist
- `-l, --language`: Language of the subtitles to download (default: en)
- `-j, --jobs`: Number of parallel download jobs (default: 8, recommended: 4-16)
- `--cookies-from-browser`: Browser to extract cookies from (chrome, firefox, etc.)

### `diagnose`
Diagnose 403 errors and other download issues.

This command will test various aspects of the connection to YouTube and provide recommendations for fixing common issues.

```bash
yt-fts diagnose
yt-fts diagnose --test-url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --cookies-from-browser firefox
```

**Options:**
- `-u, --test-url`: URL to test with (default: https://www.youtube.com/watch?v=dQw4w9WgXcQ)
- `--cookies-from-browser`: Browser to extract cookies from
- `-j, --jobs`: Number of parallel download jobs to test with (default: 8)

### Debugging with Telemetry

yt-fts includes a built-in telemetry system for debugging download issues, database problems, and performance bottlenecks. Telemetry is **disabled by default** for performance.

**Enable telemetry for debugging:**

```bash
# Basic level (ERROR, WARNING events only)
yt-fts --enable-telemetry download <channel_url>

# Verbose level (includes INFO events)
yt-fts --enable-telemetry --telemetry-level verbose batch-download channels.txt

# Debug level (all events including detailed execution flow)
yt-fts --enable-telemetry --telemetry-level debug download <channel_url>
```

**Telemetry levels:**

| Level | Events Stored | Use Case |
|-------|---------------|----------|
| `basic` | ERROR, WARNING | Production debugging, minimal overhead |
| `verbose` | + INFO | Detailed operation tracking |
| `debug` | + DEBUG | Full execution trace, development |

**Telemetry data location:**
- Database: `~/.config/yt-fts/telemetry.db` (Linux/Mac) or `%APPDATA%\yt-fts	elemetry.db` (Windows)
- Retention: 7 days automatically
- Max size: 100MB (oldest events deleted when exceeded)

See [TELEMETRY_EVENTS.md](src/yt_fts/debug/TELEMETRY_EVENTS.md) for the complete event type reference.

### `batch-download`
Download multiple YouTube channels in parallel with automatic rate limit handling.

This command processes multiple channels concurrently using ThreadPoolExecutor. It includes **dynamic auto-adjust** for video job tuning based on rate limit feedback (enabled by default).

```bash
# Basic batch download (auto-adjust enabled by default)
yt-fts batch-download channels.txt --parallel-workers 4

# Set starting video jobs and disable auto-adjust
yt-fts batch-download channels.txt --parallel-workers 4 --video-jobs 3 --no-auto-adjust

# With cookies and delay
yt-fts batch-download channels.txt --parallel-workers 2 --cookies-from-browser firefox --delay 5
```

**Options:**
- `INPUT_FILE`: Text file with channel URLs/handles (one per line)
- `-p, --parallel-workers N`: Number of parallel channel workers (default: 2)
- `--video-jobs N`: Video processing jobs per channel (default: auto-adjusted 1-8)
- `--no-auto-adjust`: Disable dynamic video_jobs adjustment (enabled by default)
- `--delay N`: Delay between channels in seconds (default: 3.0)
- `--cookies-from-browser`: Browser to extract cookies from

**Auto-Adjust Behavior:**
- Enabled by default when using `--parallel-workers`
- Starts at 2 video jobs, adjusts between 1-8 based on rate limits
- Uses **asymmetric hysteresis** - requires 2x success threshold to increase jobs
- Prevents oscillation between job counts at rate limit boundaries
- Use `--no-auto-adjust` for fixed `--video-jobs N` value

### `batch`
Advanced batch processing commands for managing multiple operations.

```bash
# Show batch processing status
yt-fts batch status

# Cancel running batch operations
yt-fts batch cancel

# Configure batch processing settings
yt-fts batch config --workers 4 --timeout 3600
```

### `queue`
Queue management commands for scheduling and managing background tasks.

```bash
# Show current queue status
yt-fts queue status

# Add channels to processing queue
yt-fts queue add channels.txt

# Clear the processing queue
yt-fts queue clear
```

### `channel-stats`
Show detailed statistics for a specific channel.

```bash
yt-fts channel-stats --channel "3Blue1Brown"
yt-fts channel-stats --channel "UC1234567890"
```

**Options:**
- `-c, --channel`: Channel name or ID (required)

### `clean-channels`
Clean up and optimize channel data in the database.

```bash
# Clean all channels
yt-fts clean-channels

# Clean specific channel
yt-fts clean-channels --channel "3Blue1Brown"

# Dry run to see what would be cleaned
yt-fts clean-channels --dry-run
```

**Options:**
- `-c, --channel`: Specific channel to clean
- `--dry-run`: Show what would be cleaned without making changes

### `convert-channels`
Convert channel formats and update channel data.

```bash
# Convert all channels to latest format
yt-fts convert-channels

# Convert specific channel
yt-fts convert-channels --channel "3Blue1Brown"
```

### `embeddings-status`
Show the status of embeddings for channels.

```bash
# Show embeddings status for all channels
yt-fts embeddings-status

# Show status for specific channel
yt-fts embeddings-status --channel "3Blue1Brown"
```

### `preset-channels`
Manage preset channel collections for quick setup.

```bash
# List available presets
yt-fts preset-channels list

# Load a preset collection
yt-fts preset-channels load educational

# Show preset details
yt-fts preset-channels show educational
```

### `reset-quota`
Reset API quota tracking for YouTube Data API usage.

```bash
# Reset quota for all keys
yt-fts reset-quota

# Reset quota for specific API key
yt-fts reset-quota --key-index 1
```

**Options:**
- `--key-index`: Specific API key index to reset (default: all keys)

### `transcribe-no-subs`
Transcribe videos that don't have existing subtitles using Whisper.

```bash
# Transcribe videos without subtitles in a channel
yt-fts transcribe-no-subs --channel "3Blue1Brown"

# Transcribe specific video
yt-fts transcribe-no-subs --video "dQw4w9WgXcQ"
```

**Options:**
- `-c, --channel`: Channel to transcribe videos in
- `-v, --video`: Specific video ID to transcribe

### `watch-history`
Show the history of automatic watch operations.

```bash
# Show recent watch history
yt-fts watch-history

# Show history for specific channel
yt-fts watch-history --channel "3Blue1Brown"

# Limit number of entries
yt-fts watch-history --limit 10
```

### `watch-search`
Search through watch history and logs.

```bash
# Search watch history
yt-fts watch-search "error"

# Search specific channel's watch history
yt-fts watch-search "success" --channel "3Blue1Brown"
```

### `playlist`
Extract channels from a YouTube playlist and add them to your channels list.

This command analyzes all videos in a playlist, extracts the unique channels, and adds them to both `channels.txt` and `channels.db`. Automatically removes duplicates.

```bash
# Extract channels from a playlist
yt-fts playlist "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab"

# Preview what would be added (dry run)
yt-fts playlist "https://www.youtube.com/playlist?list=..." --dry-run

# Specify custom output files
yt-fts playlist "URL" -o path/to/channels.txt -d path/to/subtitles.db
```

**Options:**
- `-o, --output`: Path to channels.txt file (default: data/channels.txt)
- `-d, --database`: Path to database file (default: data/subtitles.db)
- `--dry-run`: Show what would be done without making changes

**Output:**
```
📋 Extracting channels from playlist...
URL: https://www.youtube.com/playlist?list=...

✓ Found 12 unique channel(s)

  1. Channel Name (https://www.youtube.com/@handle)
  2. ...

📝 8 new channel(s) to add

  ✓ Updated data/channels.txt
  ✓ Updated data/subtitles.db (+8 new)
```

### `list`
List saved channels, videos, and transcripts.

The (ss) next to the channel name indicates that the channel has semantic search enabled. 

```bash
# List all channels
yt-fts list

# List videos for a specific channel
yt-fts list --channel "3Blue1Brown"

# Show transcript for a specific video
yt-fts list --transcript "dQw4w9WgXcQ"

# Show library (same as default)
yt-fts list --library
```

**Options:**
- `-t, --transcript`: Show transcript for a video
- `-c, --channel`: Show list of videos for a channel
- `-l, --library`: Show list of channels in library

### `languages`
List available subtitle languages for a video or channel.

```bash
# List languages for a specific video
yt-fts languages --video "dQw4w9WgXcQ"

# List all languages used in a channel
yt-fts languages --channel "3Blue1Brown"
```

**Options:**
- `-v, --video`: The video ID to check for subtitle languages
- `-c, --channel`: The channel name or id to check for subtitle languages

### `update`
Update subtitles for all channels in the library or a specific channel. 

Keep in mind some might not have subtitles enabled. This command will still attempt to download subtitles as subtitles are sometimes added later.

```bash
# Update all channels
yt-fts update

# Update specific channel
yt-fts update --channel "3Blue1Brown" --jobs 5
```

**Options:**
- `-c, --channel`: The name or id of the channel to update
- `-l, --language`: Language of the subtitles to download (default: en)
- `-j, --jobs`: Number of parallel download jobs (default: 8)
- `--cookies-from-browser`: Browser to extract cookies from

### `delete`
Delete a channel and all its data.

You must provide the name or the id of the channel you want to delete. The command will ask for confirmation before performing the deletion.

```bash
yt-fts delete --channel "3Blue1Brown"
```

**Options:**
- `-c, --channel`: The name or id of the channel to delete (required)

### `export`
Export transcripts for a channel.

This command will create a directory in the current working directory with the YouTube channel id of the specified channel.

```bash
# Export to txt format (default)
yt-fts export --channel "3Blue1Brown" --format txt

# Export to vtt format
yt-fts export --channel "3Blue1Brown" --format vtt

# Export to markdown format for Obsidian
yt-fts export --channel "3Blue1Brown" --format md --markdown-flavor obsidian

# Export to markdown format for Roam Research
yt-fts export --channel "3Blue1Brown" --format md --markdown-flavor roam

# Export to custom directory
yt-fts export --channel "3Blue1Brown" --format md --output "./MyVault/"
```

**Options:**
- `-c, --channel`: The name or id of the channel to export transcripts for (required)
- `-f, --format`: The format to export transcripts to. Supported formats: txt, vtt, md (default: txt)
- `--markdown-flavor`: Markdown flavor for md format. Options: obsidian, roam (default: obsidian)
- `-o, --output`: Output directory for exported files (default: channel_id_format)

**Markdown Export Features:**
- YAML frontmatter with video metadata (title, channel, date, tags)
- Timestamps as clickable links (wikilinks for Obsidian/Roam)
- Automatic tag extraction from video titles
- Safe filename generation (removes invalid characters)
- Perfect for building personal knowledge bases

### `search` (Full Text Search)
Full text search for a string in saved channels.

- The search string does not have to be a word for word and match 
- Search strings are limited to 40 characters. 

```bash
# search in all channels
yt-fts search "[search query]"

# search in channel
yt-fts search "[search query]" --channel "[channel name or id]"

# search in specific video
yt-fts search "[search query]" --video-id "[video id]"

# limit results
yt-fts search "[search query]" --limit "[number of results]" --channel "[channel name or id]"

# export results to csv
yt-fts search "[search query]" --export --channel "[channel name or id]"

# search in specific language
yt-fts search "[search query]" --sub-lang en
yt-fts search "[search query]" --sub-lang es --channel "[channel name or id]"
```

**Options:**
- `-c, --channel`: The name or id of the channel to search in
- `-v, --video-id`: The id of the video to search in
- `-l, --limit`: Number of results to return (default: 10)
- `-e, --export`: Export search results to a CSV file
- `--sub-lang`: Filter by subtitle language code (e.g., en, es, fr)

**Advanced Search Syntax:**

The search string supports sqlite [Enhanced Query Syntax](https://www.sqlite.org/fts3.html#full_text_index_queries).
which includes things like [prefix queries](https://www.sqlite.org/fts3.html#termprefix) which you can use to match parts of a word.  

```bash
# AND search
yt-fts search "knife AND Malibu" --channel "The Tim Dillon Show" 

# OR SEARCH 
yt-fts search "knife OR Malibu" --channel "The Tim Dillon Show" 

# wild cards
yt-fts search "rea* kni* Mali*" --channel "The Tim Dillon Show" 
```

# Semantic Search and RAG
You can enable semantic search for a channel by using the `embeddings` command.
This requires an OpenAI or Gemini API key set in the environment variable `OPENAI_API_KEY` or `GEMINI_API_KEY`, or 
you can pass the key with the `--api-key` flag. 

### `embeddings`
Fetches embeddings for specified channel

```bash
# make sure API key is set
# export OPENAI_API_KEY="[yourOpenAIKey]"
# or
# export GEMINI_API_KEY="[yourGeminiKey]"

yt-fts embeddings --channel "3Blue1Brown"

# specify time interval in seconds to split text by default is 30 
# the larger the interval the more accurate the llm response  
# but semantic search will have more text for you to read. 
yt-fts embeddings --interval 60 --channel "3Blue1Brown" 
```

**Options:**
- `-c, --channel`: The name or id of the channel to generate embeddings for
- `--api-key`: API key (if not provided, reads from OPENAI_API_KEY or GEMINI_API_KEY environment variable)
- `-i, --interval`: Interval in seconds to split the transcripts into chunks (default: 30)

After the embeddings are saved you will see a `(ss)` next to the channel name when you 
list channels, and you will be able to use the `vsearch` command for that channel. 

### `vsearch` (Semantic Search)
`vsearch` is for "Vector search". This requires that you enable semantic 
search for a channel with `embeddings`. It has the same options as 
`search` but output will be sorted by similarity to the search string and 
the default return limit is 10. 

```bash
# search by channel name
yt-fts vsearch "[search query]" --channel "[channel name or id]"

# search in specific video
yt-fts vsearch "[search query]" --video-id "[video id]"

# limit results
yt-fts vsearch "[search query]" --limit "[number of results]" --channel "[channel name or id]"

# export results to csv
yt-fts vsearch "[search query]" --export --channel "[channel name or id]"

# search in specific language
yt-fts vsearch "[search query]" --sub-lang es
```

**Options:**
- `-c, --channel`: The name or id of the channel to search in
- `-v, --video-id`: The id of the video to search in
- `-l, --limit`: Number of results to return (default: 10)
- `-e, --export`: Export search results to a CSV file
- `--sub-lang`: Filter by subtitle language code (e.g., en, es, fr)
- `--api-key`: API key (if not provided, reads from OPENAI_API_KEY or GEMINI_API_KEY environment variable)

### `llm` (Chat Bot)
Starts interactive chat session with a model using 
the semantic search results of your initial prompt as the context
to answer questions. If it can't answer your question, it has a 
mechanism to update the context by running targeted query based 
off the conversation. The channel must have semantic search enabled.

```bash
yt-fts llm --channel "3Blue1Brown" "How does back propagation work?"
```

**Options:**
- `-c, --channel`: The name or id of the channel to use (required)
- `--api-key`: API key (if not provided, reads from OPENAI_API_KEY or GEMINI_API_KEY environment variable)

### `summarize`
Summarizes a YouTube video transcript, providing time stamped URLS. 
Requires a valid YouTube video URL or video ID as argument. If the 
trancript is not in the database it will try to scrape it.

```bash
yt-fts summarize "https://www.youtube.com/watch?v=9-Jl0dxWQs8"
# or
yt-fts summarize "9-Jl0dxWQs8"

# Use different model
yt-fts summarize --model "gpt-3.5-turbo" "9-Jl0dxWQs8"
```

**Options:**
- `--model, -m`: Model to use in summary
- `--api-key`: API key (if not provided, reads from OPENAI_API_KEY or GEMINI_API_KEY environment variable)

### `watch`
Manage automatic channel updates for new videos.

The watch mode allows you to automatically monitor channels for new uploads and download transcripts as they are published.

```bash
# Add a channel to watch list
yt-fts watch add "@3blue1brown" --interval daily

# List all watch jobs
yt-fts watch list

# Enable/disable a watch job
yt-fts watch enable "@3blue1brown"
yt-fts watch disable "@3blue1brown"

# Remove a channel from watch list
yt-fts watch remove "@3blue1brown"

# Run watch jobs once (check for new videos)
yt-fts watch run

# Start background daemon for automatic updates
yt-fts watch start --interval 60
```

**Options:**
- `add`: Add a channel to watch list
  - `--interval`: Check interval (hourly, daily, weekly) (default: daily)
- `remove`: Remove a channel from watch list
- `list`: List all watch jobs
- `enable`: Enable a watch job
- `disable`: Disable a watch job
- `run`: Run due watch jobs once (manual execution)
- `start`: Start background daemon
  - `--interval`: Check interval in minutes (default: 60)

**Watch Intervals:**
- `hourly`: Check for new videos every hour
- `daily`: Check once per day
- `weekly`: Check once per week

The watch job tracks the number of videos in the channel and downloads new transcripts when the count increases.

output:
```
In this video, 3Blue1Brown explores how large language models (LLMs) like GPT-3 
might store facts within their vast...                                                         

 1 Introduction to Fact Storage in LLMs:                                                                                     
    • The video starts by questioning how LLMs store specific facts and                                                      
      introduces the idea that these facts might be stored in a particular part of the                                       
      network known as multi-layer perceptrons (MLPs).                                                                       
    • 0:00                                                                                                                   
 2 Overview of Transformers and MLPs:                                                                                        
    • Provides a refresher on transformers and explains that the video will focus                                            
```


### `stats`
Show database statistics including channel, video, and subtitle counts.

This command displays a summary of your yt-fts database including the number of indexed channels, videos, subtitle entries, and the database file size.

```bash
yt-fts stats
```

**Output:**
```
                      Database Statistics
┏━━━━━━━━━━┳━━━━━━━━┓
┃ Metric   ┃ Value  ┃
┡━━━━━━━━━━╇━━━━━━━━┩
│ Channels │ 12     │
│ Videos   │ 1,245  │
│ Subtitles│ 847,392│
│ Database │ 125.4  │
│ Size     │ MB     │
└──────────┴────────┘
```

### `health`
Check database integrity and health.

This command verifies the database file exists, checks SQLite integrity using PRAGMA integrity_check, and validates that all expected tables are accessible.

```bash
yt-fts health
```

**Exit Codes:**
- `0` - Healthy: Database exists, integrity check passes, all tables accessible
- `1` - Warning: Database exists but some tables are not readable
- `2` - Error: Database file missing or corrupted

**What it checks:**
- Database file existence at expected path
- Database integrity via SQLite PRAGMA integrity_check
- Each expected table: Channels, Videos, Subtitles, SearchHistory, SavedQueries

**Output:**
```
                Database Health Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Component        Status
────────────────────────────
Database File    OK
Database Integrity OK

Tables
Channels         OK
Videos           OK
Subtitles        OK
SearchHistory    OK
SavedQueries     OK

Overall          HEALTHY
Exit Code        0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### `config`
Show config settings including database and chroma paths.

```bash
yt-fts config
```

## How To

**Export search results:**

For both the `search` and `vsearch` commands you can export the results to a csv file with 
the `--export` flag. and it will save the results to a csv file in the current directory. 
```bash
yt-fts search "life in the big city" --export
yt-fts vsearch "existing in large metropolaten center" --export
```

**Delete a channel:**
You can delete a channel with the `delete` command. 

```bash
yt-fts delete --channel "3Blue1Brown"
```


**Update a channel:**
The update command currently only works for full text search and will not update the 
semantic search embeddings. 

```bash
yt-fts update --channel "3Blue1Brown"
```


**Export all of a channel's transcript:**

This command will create a directory in current working directory with the YouTube 
channel id of the specified channel.
```bash
# Export to vtt
yt-fts export --channel "[id/name]" --format "[vtt/txt]"
```# Checkpoint test
# Another test

**Resume Interrupted Downloads:**

```bash
yt-fts batch-download channels.txt --resume
```

The `--resume` flag uses a checkpoint cache to skip videos that were already downloaded in previous runs. This is useful when:
- A download was interrupted (Ctrl+C, network issue, crash)
- Re-running a batch to get new videos only
- Avoiding re-downloading large videos already processed

The checkpoint file is stored at: `~/.config/yt-fts/checkpoints/download_cache.json`
