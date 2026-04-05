# Telegram Media Downloader

This tool allows you to download media files from specific Telegram channels using the Telethon library. It includes features to enumerate media files, avoid duplicate downloads, and track downloaded files.

## Prerequisites

1. Python 3.7 or higher
2. Telegram API credentials (API ID and API Hash)
3. Telegram session string

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Process ID (PID) Management

The `dnld_telegram` application includes a robust PID management system to prevent orphaned processes and ensure clean shutdowns, especially when dealing with database locks. This system is implemented in `config/pid_manager.py`.

### Key Features:
- **Orphaned Process Cleanup:** Automatically detects and terminates previous instances of `dnld_telegram` that may not have shut down cleanly.
- **Graceful Shutdown:** Integrates with `atexit` and signal handlers (`SIGINT`, `SIGTERM`) to ensure the current process's PID is removed from the tracking file upon exit.
- **Enhanced Process Identification:** Uses a unique application identifier (`APP_IDENTIFIER`) in conjunction with process name and command-line checks to reliably identify and manage `dnld_telegram` processes.

### Scope and Compatibility:
This PID management system is primarily designed and tested for **Windows operating systems**. While `psutil` offers cross-platform capabilities, the specific implementation and testing has focused on Windows environments to ensure optimal behavior and reliability within this scope. Future enhancements may include broader cross-platform support.

### How it Works:
1.  When `dnld_telegram` starts, it calls `start_process_management()` from `pid_manager.py`.
2.  The system first checks for any existing `dnld_telegram.pid` file in the `config/` directory.
3.  If found, it reads the PIDs and unique identifiers from this file. For each entry, it verifies if the process is still running, is a Python process, and matches the `dnld_telegram` application identifier. If all checks pass, the orphaned process is terminated.
4.  After cleanup, the current process's PID and unique identifier are written to `dnld_telegram.pid`.
5.  Upon graceful exit or signal-based termination, the current process's PID is removed from the file.

## Setup

1. The script reads configuration from a `.env` file. Create a `.env` file in the project directory with the following format:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_SESSION_STRING=your_session_string
   TELEGRAM_CHANNELS={"jcexclusive": -1002436706028, "koreannarchive": -1001518888395}
   TEMP_DIR=.
   ```

2. To obtain your Telegram API credentials:
   - Go to https://my.telegram.org/
   - Log in with your Telegram account
   - Create a new application to get your API ID and API Hash

3. To obtain your session string:
   - You can use the Telethon library to generate a session string by running a simple script that authenticates with your phone number

4. To configure the working directory:
   - Set `TEMP_DIR` in your `.env` file to specify where channel directories should be created
   - Default: `.` (current directory)
   - Example: `TEMP_DIR=C:\_Python\_Projects\temp`

5. To add new channels:
   - Update the `TELEGRAM_CHANNELS` JSON in your `.env` file
   - For example: `TELEGRAM_CHANNELS={"jcexclusive": -1002436706028, "koreannarchive": -1001518888395, "mynewchannel": -1234567890}`

## Channel Configuration

### Finding Channel IDs

To add a new channel, you first need to find its channel ID. Use the provided utility:

```bash
# Find channel ID by username
python find_channel_id.py @channelname
python find_channel_id.py https://t.me/channelname
python find_channel_id.py channelname
```

**Examples:**
```bash
python find_channel_id.py @leaksasian
python find_channel_id.py https://t.me/leaksasian
python find_channel_id.py leaksasian
```

**Requirements for finding channel IDs:**
- Channel must be public OR you must be a member
- Uses the same `.env` credentials as the main downloader
- Channel IDs will be negative numbers (e.g., -1002436706028)

### Adding Channels to Configuration

The script reads channel information from `channels.toml` or the `TELEGRAM_CHANNELS` environment variable.

**Method 1: channels.toml (Recommended)**
```toml
[TELEGRAM_CHANNELS]
jcexclusive = -1002436706028
koreannarchive = -1001518888395
mynewchannel = -1234567890
```

**Method 2: .env file (Legacy)**
```
TELEGRAM_CHANNELS={"jcexclusive": -1002436706028, "koreannarchive": -1001518888395, "mynewchannel": -1234567890}
```

Alternative .env format:
```
CHANNEL_jcexclusive=-1002436706028
CHANNEL_koreannarchive=-1001518888395
```

The script will automatically detect channels from any of these formats.

## Usage

The script supports several modes of operation:

### Enumerate Media Files
To list all media files in a channel and save them to the enumeration list without downloading:
```bash
python download_telegram_media.py --channel koreannarchive --enumerate-only
```

### Download Specific Messages
To download specific messages from a channel:
```bash
python download_telegram_media.py --channel koreannarchive --message-ids 4403 4406 4399
```

### Download All Undownloaded Media from a Channel
To download all media files from a channel that haven't been downloaded yet:
```bash
python download_telegram_media.py --channel koreannarchive --all-media --limit 100
```

### Default Behavior
If no arguments are provided, the script will enumerate media files in the first channel found in the configuration:
```bash
python download_telegram_media.py
```

## Features

1. **Environment Configuration**: Reads Telegram API credentials and channel information from a `.env` file
2. **Per-Channel Tracking**: Maintains separate tracking files for each channel
3. **Duplicate Prevention**: Tracks downloaded files to avoid downloading the same media multiple times
4. **Flexible Arguments**: Supports command-line arguments for different download modes
5. **Media Enumeration**: Can list all media files in a channel and save them to the enumeration list
6. **Selective Download**: Can download specific messages by ID
7. **Bulk Download**: Can download all undownloaded media from a channel
8. **Progress Tracking**: Shows download progress and statistics
9. **Automatic Cleanup**: Removes successfully downloaded files from the enumeration list

## File Tracking

The script creates separate tracking files for each channel in their respective directories:

- `temp/JCexclusive/enumerated_files.json` - Lists all media files in JCexclusive
- `temp/JCexclusive/downloaded_files.json` - Tracks downloaded files from JCexclusive
- `temp/koreannarchive/enumerated_files.json` - Lists all media files in koreannarchive
- `temp/koreannarchive/downloaded_files.json` - Tracks downloaded files from koreannarchive

When a file is successfully downloaded, it's automatically removed from the enumerated files list to prevent redundant processing.

## Troubleshooting

- If you get authentication errors, verify your session string is valid
- If downloads fail, check that you have permission to access the channels and messages
- Make sure the `temp` directory and its subdirectories exist and are writable
- If the script complains about missing environment variables, check that your `.env` file is properly formatted and in the correct location
- If a channel is not recognized, check that it's properly defined in your `.env` file with the `CHANNEL_` prefix

## Security Notes

- Keep your API credentials and session string secure and never share them
- The session file contains sensitive authentication information
- Do not commit your credentials or session file to version control
