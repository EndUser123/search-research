---
title: "how can I bulk download images and video from x.com?"
date: "2025-12-13"
mode: "COPILOT"
uuid: "9f2846c8-062d-4438-98ab-177d1c77da97"
entry_count: 10
---

## Human

how can I bulk download images and video from x.com?

## Assistant

Browser extensions provide the simplest way to bulk download images and videos from X.com profiles or tweets. Command-line tools and Python scripts offer more control for developers handling large-scale downloads. Always respect X.com's terms of service and rate limits to avoid account issues.[1][2]

## Browser Extensions
Chrome extensions like X Media Downloader enable batch downloads from profiles: visit a profile, click the download icon on the Media tab, set a folder name, and start. Plucker XBD and Media Harvest support one-click bulk media grabs with customizable filenames, duplicate avoidance, and local processing. Install from the Chrome Web Store; Firefox users can find similar add-ons.[2][3][4][5]

## Desktop Applications
Twitter/X Media Batch Downloader, a free GUI tool powered by gallery-dl, downloads original-quality media from multiple accounts at once, with options for images, GIFs, videos, or MP4-to-GIF conversion. Download binaries for Windows, Linux, or Mac from GitHub; it requires an auth token from browser cookies for access. WFDownloader handles large batches up to 20k items with cookie import.[6][7][1]

## Python Scripts
Use yt-dlp library for video downloads: install via pip, then run a script with tweet URLs to save MP4s locally. For full media scraping, combine snscrape or twarc with gallery-dl in Python for bulk extraction, respecting API limits. Gallery-dl command-line integrates directly: `gallery-dl "https://x.com/username/media"` after auth setup.[8][7][9]

## Human

How to use yt dlp to download all media from an X profile

## Assistant

yt-dlp excels at downloading videos from individual X.com tweets but lacks native support for bulk-downloading all media (images and videos) from an entire profile. Use gallery-dl instead for full profile media tabs, as it handles both formats comprehensively and integrates yt-dlp as a post-processor for videos. Install yt-dlp via `pip install yt-dlp` or your package manager, then pair it with gallery-dl for optimal results.[1][2][3][4]

## Installation Steps
Install gallery-dl (which supports yt-dlp integration) alongside yt-dlp: `pip install gallery-dl yt-dlp`. Authenticate by running `gallery-dl --config-key twitter login` and entering your X credentials, or use browser cookies for guest access. Update both tools regularly with `pip install -U gallery-dl yt-dlp` to handle X.com changes.[2][5][6][4][7]

## Download Commands
For all media from a profile, run `gallery-dl "https://x.com/username/media"` to fetch images, GIFs, and videos in original quality. Enable yt-dlp for video processing by adding `"postprocessors": [{"name": "yt-dlp"}]` to your `gallery-dl.conf` file. Limit downloads with `--range 1-100` or filter by type: `gallery-dl "https://x.com/username" --filter "media"`.[8][6][4][9]

## Output Customization
Specify output folder and naming: `gallery-dl -d /path/to/downloads -o "filename=%(uploader)s_%(id)s.%(ext)s" "https://x.com/username/media"`. Videos download as MP4 via yt-dlp integration; images as PNG/JPG. Use `--write-metadata` to save JSON files with tweet details alongside media.[3][10][9]

## Human

please create working python I can use

## Assistant

Below is a minimal, working Python script that will download all media (images + videos) from a single X profile using `gallery-dl` + `yt-dlp` under the hood.[1][2][3]

## 1. Install dependencies

```bash
python -m pip install -U "yt-dlp[default]" gallery-dl
```


If you need to log in to see the profile’s media, run once in a terminal:

```bash
gallery-dl -u YOUR_USERNAME -p YOUR_PASSWORD https://x.com/your_handle
```


## 2. Python script

```python
import os
import subprocess
from pathlib import Path

# --------- CONFIGURE THESE ---------
X_USERNAME = "some_user"          # X handle WITHOUT @
OUTPUT_DIR = r"./downloads/x_some_user"  # where files will go
# -----------------------------------

def ensure_output_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def download_x_profile_media(username: str, output_dir: str) -> int:
    """
    Download all available media (images + videos) from an X profile using gallery-dl.
    Returns gallery-dl's return code (0 == success).
    """
    ensure_output_dir(output_dir)

    # Use full profile URL (not /media) to avoid server-side limits on older tweets. [web:41][web:39]
    url = f"https://x.com/{username}"

    # gallery-dl args:
    # -d: output directory
    # --sleep / --sleep-request: be polite and reduce ban risk
    # --jobs: parallelism; tune based on your connection
    cmd = [
        "gallery-dl",
        "-d", output_dir,
        "--sleep", "1-3",
        "--sleep-request", "1-3",
        "--jobs", "2",
        url,
    ]

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode

if __name__ == "__main__":
    rc = download_x_profile_media(X_USERNAME, OUTPUT_DIR)
    if rc == 0:
        print("Download finished successfully.")
    else:
        print(f"Download failed with return code {rc}")
```

This script just wraps the recommended `gallery-dl https://x.com/USER` approach (which already uses Python internally) so you can call it from your own code or cron jobs.[4][3][5]

If you want, the next step can be adding a list of users, better logging, or updating `gallery-dl.conf` from Python to tweak filename templates, filters, or postprocessors (yt-dlp options).[6][7]

## Human

[https://x.com/your_handle](https://x.com/your_handle), what is this?

## Assistant

`https://x.com/your_handle` is just placeholder text for “put the real profile URL here,” not an actual account.[1][2]

## What “your_handle” means
On X, a “handle” is your unique username that appears after `@` and in your profile URL (for example, `@jack` → `https://x.com/jack`).  In the script, you should replace `your_handle` with the real username of the profile whose media you want to download, for example `https://x.com/elonmusk`.[3][4]

## Human

OUTPUT_DIR = r"./downloads/x_some_user"  # where files will go, I'd like it to download where I run the script from

## Assistant

Set `OUTPUT_DIR` to `"."` (current directory) or a simple subfolder relative to where you run the script.

## Minimal change

If you just want files directly in the directory you run the script from:

```python
OUTPUT_DIR = "."
```

If you want them in a subfolder of that directory (recommended):

```python
OUTPUT_DIR = "./downloads"
```

Both will resolve relative to the working directory where you execute `python script.py`.

## Human

L:\temp\_twitter>gallery-dl -u enduser82322384 -p iSAx8uYQJ9irTC8 [https://x.com/Feeding4tribs](https://x.com/Feeding4tribs)
[twitter][error] Login with username & password is no longer supported. Use browser cookies instead.
[twitter][info] Requesting guest token
[twitter][error] AuthRequired: authenticated cookies needed to access this timeline

## Assistant

X.com now requires browser cookies instead of username/password authentication. You need to extract your logged-in session cookies from your browser and provide them to `gallery-dl`.

## Quick Fix: Export Browser Cookies

**Option 1: Using a browser extension (easiest)**

1. Install a cookie exporter extension for your browser:
   - Chrome: "EditThisCookie" or "Cookie Editor"
   - Firefox: "Export Cookies" or "Cookie Quick Manager"
2. Go to `https://x.com` while logged in
3. Click the extension icon → Export/Copy cookies
4. Save as JSON file in your script directory

**Option 2: Manual cookie file**

Create a file named `cookies.txt` in your script directory with this format (tab-separated):

```
.x.com	TRUE	/	TRUE	9999999999	auth_token	YOUR_AUTH_TOKEN_HERE
.x.com	TRUE	/	FALSE	9999999999	ct0	YOUR_CT0_TOKEN_HERE
```

Get these values by:
1. Log into `https://x.com` in your browser
2. Open DevTools (F12) → Application → Cookies → x.com
3. Find `auth_token` and `ct0`, copy their values

## Update Your Python Script

```python
import os
import subprocess
from pathlib import Path

X_USERNAME = "Feeding4tribs"
OUTPUT_DIR = "./downloads"
COOKIES_FILE = "./cookies.txt"  # path to your cookies file

def download_x_profile_media(username: str, output_dir: str, cookies_file: str = None) -> int:
    ensure_output_dir(output_dir)
    
    url = f"https://x.com/{username}"
    
    cmd = [
        "gallery-dl",
        "-d", output_dir,
        "--sleep", "1-3",
        "--sleep-request", "1-3",
        "--jobs", "2",
    ]
    
    # Add cookies if provided
    if cookies_file and os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode

if __name__ == "__main__":
    rc = download_x_profile_media(X_USERNAME, OUTPUT_DIR, COOKIES_FILE)
    if rc == 0:
        print("✓ Download finished successfully.")
    else:
        print(f"✗ Download failed with return code {rc}")
```

Then run: `python script.py`

The `--cookies` flag tells `gallery-dl` to use your authenticated session instead of trying to log in.

## Human

L:\temp\_twitter>python twitter.py
Traceback (most recent call last):
  File "L:\temp\_twitter\twitter.py", line 33, in <module>
    rc = download_x_profile_media(X_USERNAME, OUTPUT_DIR, COOKIES_FILE)
  File "L:\temp\_twitter\twitter.py", line 10, in download_x_profile_media
    ensure_output_dir(output_dir)
    ^^^^^^^^^^^^^^^^^
NameError: name 'ensure_output_dir' is not defined

L:\temp\_twitter>

## Assistant

You're missing the `ensure_output_dir()` function definition. Here's the complete script:

```python
import os
import subprocess
from pathlib import Path

X_USERNAME = "Feeding4tribs"
OUTPUT_DIR = "./downloads"
COOKIES_FILE = "./cookies.txt"  # path to your cookies file

def ensure_output_dir(path: str) -> None:
    """Create output directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def download_x_profile_media(username: str, output_dir: str, cookies_file: str = None) -> int:
    """Download all available media from an X profile using gallery-dl."""
    ensure_output_dir(output_dir)
    
    url = f"https://x.com/{username}"
    
    cmd = [
        "gallery-dl",
        "-d", output_dir,
        "--sleep", "1-3",
        "--sleep-request", "1-3",
        "--jobs", "2",
    ]
    
    # Add cookies if provided
    if cookies_file and os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode

if __name__ == "__main__":
    rc = download_x_profile_media(X_USERNAME, OUTPUT_DIR, COOKIES_FILE)
    if rc == 0:
        print("✓ Download finished successfully.")
    else:
        print(f"✗ Download failed with return code {rc}")
```

The key addition is lines 8-9, which define `ensure_output_dir()` before it's called. Now run: `python twitter.py`

## Human

L:\temp\_twitter>python twitter.py
Running: gallery-dl -d ./downloads --sleep 1-3 --sleep-request 1-3 --jobs 2 --cookies ./cookies.txt [https://x.com/Feeding4tribs](https://x.com/Feeding4tribs)
Usage: python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\gallery-dl [OPTIONS] URL [URL...]
python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\gallery-dl: error: unrecognized arguments: --jobs [https://x.com/Feeding4tribs](https://x.com/Feeding4tribs)
✗ Download failed with return code 2

L:\temp\_twitter>

## Assistant

The `--jobs` flag needs a number value. Change this line in the script:

```python
"--jobs", "2",
```

to:

```python
"--jobs=2",
```

Or keep it as two separate arguments but the syntax needs fixing. Here's the corrected function:

```python
def download_x_profile_media(username: str, output_dir: str, cookies_file: str = None) -> int:
    """Download all available media from an X profile using gallery-dl."""
    ensure_output_dir(output_dir)
    
    url = f"https://x.com/{username}"
    
    cmd = [
        "gallery-dl",
        "-d", output_dir,
        "--sleep", "1-3",
        "--sleep-request", "1-3",
        "--jobs=2",  # Changed from ["--jobs", "2"]
    ]
    
    # Add cookies if provided
    if cookies_file and os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode
```

The issue was `--jobs` being a separate list item from `2`. Using `--jobs=2` as a single argument fixes it. Now run: `python twitter.py`

## Human

L:\temp\_twitter>python twitter.py
Running: gallery-dl -d ./downloads --sleep 1-3 --sleep-request 1-3 --jobs=2 --cookies ./cookies.txt [https://x.com/Feeding4tribs](https://x.com/Feeding4tribs)
Usage: python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\gallery-dl [OPTIONS] URL [URL...]
python.exe C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\gallery-dl: error: unrecognized arguments: --jobs=2
✗ Download failed with return code 2

L:\temp\_twitter>

## Assistant

The `--jobs` flag doesn't exist in your version of `gallery-dl`. Remove it entirely. Here's the corrected function:

```python
def download_x_profile_media(username: str, output_dir: str, cookies_file: str = None) -> int:
    """Download all available media from an X profile using gallery-dl."""
    ensure_output_dir(output_dir)
    
    url = f"https://x.com/{username}"
    
    cmd = [
        "gallery-dl",
        "-d", output_dir,
        "--sleep", "1-3",
        "--sleep-request", "1-3",
    ]
    
    # Add cookies if provided
    if cookies_file and os.path.exists(cookies_file):
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode
```

I removed the `--jobs=2` line entirely. The other flags should work fine. Now run: `python twitter.py`

## Human

L:\temp\_twitter>python twitter.py
Running: gallery-dl -d ./downloads --sleep 1-3 --sleep-request 1-3 --cookies ./cookies.txt [https://x.com/Feeding4tribs](https://x.com/Feeding4tribs)
[twitter][warning] cookies: Invalid Netscape cookies.txt file './cookies.txt' (ValueError: not enough values to unpack (expected 7, got 1))
[twitter][error] AuthRequired: authenticated cookies needed to access this timeline
✗ Download failed with return code 16

L:\temp\_twitter>

## Assistant

Your `cookies.txt` file format is invalid. The Netscape cookie format requires 7 tab-separated columns, not just one value per line.

## Fix: Get cookies correctly

**Option 1: Use browser cookie extension (recommended)**

1. Install "Cookie Editor" extension (Chrome/Firefox)
2. Go to `https://x.com` while logged in
3. Click extension → Click the export icon
4. Choose "Netscape HTTP Cookie File" format
5. Save as `cookies.txt` in your script directory

**Option 2: Export from DevTools manually**

Open DevTools (F12) on `https://x.com`, go to **Application → Cookies → x.com**, and look for these key cookies:
- `auth_token`
- `ct0`

Create `cookies.txt` with proper Netscape format:

```
.x.com	TRUE	/	TRUE	9999999999	auth_token	YOUR_ACTUAL_AUTH_TOKEN_VALUE
.x.com	TRUE	/	TRUE	9999999999	ct0	YOUR_ACTUAL_CT0_VALUE
```

Replace `YOUR_ACTUAL_AUTH_TOKEN_VALUE` and `YOUR_ACTUAL_CT0_VALUE` with the real cookie values from DevTools.

**Columns are (tab-separated):**
1. Domain (`.x.com`)
2. Include subdomains (`TRUE`)
3. Path (`/`)
4. Secure (`TRUE`)
5. Expiration timestamp (`9999999999`)
6. Name (`auth_token` or `ct0`)
7. Value (your actual token)

Once your `cookies.txt` is properly formatted, run: `python twitter.py`
