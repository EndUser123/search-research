## User Guide

### Installation
The script requires a working Python 3.10+ environment and `ffprobe` (part of the FFmpeg suite) to be in your system's PATH for the quality upgrade feature.

**1. Install Python Libraries:**
```bash
pip install -r requirements.txt
```

**2. Install Playwright Browsers:**
After installing the libraries, you must download the browser binaries that Playwright uses.
```bash
playwright install
```

### Configuration (`config.yaml`)
All script settings can be managed from a central `config.yaml` file in the project root.

**Example `config.yaml`:**
```yaml
# The root directory for your YouTube library where channel folders are stored.
base_dir: 'D:\YouTubeLibrary'

# The primary file containing the list of channel URLs.
url_file: 'channels.txt'

# The primary file containing per-channel filter rules.
filters_file: 'filters.json'

# Your YouTube Data v3 API keys for fast, reliable video discovery.
youtube_api_keys:
  - "AIzaSy...YOUR_API_KEY_1"
  - "AIzaSy...YOUR_API_KEY_2"

# Authentication data is stored here automatically by the --refresh-auth command.
# You do not need to edit this section manually.
authentication:
  cookies_file: 'C:\_Python\_Projects\YT_Sync\cookies.txt'
  # The following test_video_url is used to verify auth is still working.
  test_video_url: 'https://www.youtube.com/watch?v=o6NW5nGKOA8'

# Performance settings
concurrency:
  max_downloads: 4

# Throttling settings to avoid being blocked.
throttling:
  ratelimit: "10M" # Example: 10 Megabytes per second
  sleep_interval_requests: 1

# Quality Management: Automatically find and upgrade low-quality videos.
quality_management:
  enable_quality_upgrade: true
  minimum_height: 720
  upgrade_batch_size: 10
  backup_old_files: true
```

### Authentication: The `--refresh-auth` Workflow
To reliably download age-restricted or members-only content, the script includes a powerful, semi-automated feature to capture your login credentials.

**How it Works:**
1.  Run the Command: Execute `python yt_channel_sync.py --refresh-auth`.
2.  Automatic Verification & Discovery: The script first checks `config.yaml` for a saved `test_video_url`. It verifies if the current authentication cookies can still access this video.
3.  If verification fails or no cookies exist, the script launches a Playwright browser window for manual login.
4.  After login, the script captures cookies and saves them to the path specified in `config.yaml`.
5.  The script then verifies the captured cookies by attempting to access the `test_video_url` again.
6.  If successful, the cookies are saved, and the script exits.
7.  If verification fails again, the script offers to open the browser for another login attempt.

**Important Notes:**
-   The script now uses a more reliable method for cookie capture, focusing on the `youtube.com` domain.
-   The script includes a fallback mechanism to handle cases where the primary cookie capture fails.
-   The script now uses a more robust method to verify authentication status, checking for specific elements on the page rather than just HTTP status codes.

### Session & Resume Functionality
The script maintains a state file (`yt_sync_state.json`) that tracks:
-   Currently processing channel
-   Videos downloaded in the current session
-   Any errors encountered

If the script is interrupted, it can resume from where it left off by default. To start fresh, use the `--fresh-start` flag.

### Filtering (`filters.json`)
Create a `filters.json` file to exclude specific videos based on title patterns. The file should be an array of objects, each containing a `pattern` (regex) and an `action` ("exclude" or "include").

**Example `filters.json`:**
```json
[
  {
    "pattern": "trailer",
    "action": "exclude"
  },
  {
    "pattern": "full episode",
    "action": "include"
  }
]
```

### Command-Line Usage
```
usage: yt_channel_sync.py [-h] [--refresh-auth] [--fresh-start] [--dry-run] [--debug] [--version]

YouTube Channel Sync - Download and organize videos from YouTube channels

optional arguments:
  -h, --help            show this help message and exit
  --refresh-auth        Refresh authentication cookies
  --fresh-start         Start fresh, ignoring any previous state
  --dry-run             Simulate the run without downloading videos
  --debug               Enable debug logging
  --version             show program's version number and exit
```

### Quality Management & Upgrades
The script can automatically find and upgrade low-quality videos to higher quality versions. This is configured in `config.yaml` under `quality_management`.

**How it Works:**
1.  After downloading videos, the script scans for files that don't meet the `minimum_height` requirement.
2.  It then checks YouTube for available higher quality versions.
3.  If found, it downloads the higher quality version and replaces the original.
4.  The original file is moved to a backup directory if `backup_old_files` is set to `true`.
