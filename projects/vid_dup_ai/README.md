# Video Dedupe AI: Clean Up and Organize Your Video Library

Ever found yourself with folders full of video files, wondering if you have duplicates, and wishing you could just keep the best-quality version? **Video Dedupe AI** is a smart assistant that automatically cleans up your video collection for you.

It scans your folders, finds duplicate videos (even if they have different names or resolutions!), and helps you keep only the best copy, saving you gigabytes of space.

## What Can It Do For You?

* **Finds All Kinds of Duplicates:** This tool is like a detective for your videos. It doesn't just look at filenames. It analyzes the actual video content to find duplicates that might have been resized, re-encoded, or renamed.
* **Keeps the Best, Deletes the Rest:** You can tell it to automatically keep the video with the highest quality (like the 4K version over the 720p one). No more manually comparing files!
* **Works Safely:**
    * **Practice Mode (`--dry-run`):** You can do a "practice run" where the tool shows you exactly what it *would* do without actually touching any of your files.
    * **Recycle Bin (`--quarantine-dir`):** Instead of permanently deleting files, it can move them to a "quarantine" folder, just like a recycle bin, so you can check them before they're gone for good.
* **(Advanced) Auto-Sorts Your Videos:** If you want, it can use Artificial Intelligence to figure out what your videos are about (like "sports" or "music") and automatically sort them into folders for you.

---

## Getting Started: A 3-Step Guide

### Step 1: Get the necessary tools

Before you can use the script, your computer needs two things:

1.  **Python:** This is the language the script is written in. Many computers already have it.
2.  **FFmpeg:** This is a popular, free tool for working with video. The script uses it to understand your video files. You can download it from the official site: [ffmpeg.org](https://ffmpeg.org/download.html).

### Step 2: Install the Script's "Toolbox"

The script relies on some open-source "tools" to do its job. You can install all of them with a single command.

1.  Save the `requirements.txt` file from this project into a folder.
2.  Open your computer's command line (like Terminal on Mac, or Command Prompt/PowerShell on Windows).
3.  Navigate to that folder and run this command:
    ```bash
    pip install -r requirements.txt
    ```

### Step 3: Run the Script!

Now you're ready to clean up your videos.

1.  Save the script as `video_dedupe_ai.py` in the same folder.
2.  The basic command looks like this:
    ```bash
    python video_dedupe_ai.py "C:\Path\To\Your\Main Videos" "D:\Path\To\Other\Videos" [options]
    ```
    * **Main Videos:** This is the folder where you want to keep your final, best-quality videos.
    * **Other Videos:** This is a second folder you want to scan for duplicates (like a "Downloads" or "Backups" folder).

---

## Example Recipes for Common Tasks

Here are some simple "recipes" you can copy and paste. **Always start with a `--dry-run`!**

#### Recipe 1: The Safe First-Time Checkup

> "I want to see what duplicates you find, keeping the best quality, but **don't change anything yet**."

```bash
python video_dedupe_ai.py "C:\MyVideos" "D:\Downloads" --quality-metric vmaf --dry-run
```

#### Recipe 2: The "Clean-Up and Sort"

> "Find all the duplicates, move the lower-quality ones to a recycle bin, and then automatically sort the good ones into new folders for me."

```bash
python video_dedupe_ai.py "C:\MyVideos" "D:\Downloads" --quality-metric vmaf --quarantine-dir "C:\_VideoRecycleBin" --categorize --organization-dir "C:\Organized Videos"
```

*After running this, you can press `y` to approve the changes.*

---

## Advanced Usage & Concepts

Want to get the most out of Video Dedupe AI? Here’s how some of the advanced features work.

### How does it decide the "best" quality?

It's not just about one thing! When you use `--quality-metric`, the script calculates a **composite quality score** for each video. It looks at:

1.  **Perceptual Score (like VMAF):** How good the video looks to the human eye. (This is the most important factor).
2.  **Resolution:** Is it 4K, 1080p, or 720p? Higher is better.
3.  **Bitrate:** How much data is used for each second of video? Higher is usually better.

It weighs these factors and picks the video with the highest overall score, so you get a truly better-quality file, not just a bigger one.

### How can I make the AI smarter?

The default AI model is a good generalist, but you can make it better for your specific video library.

#### 1. Use a Different AI Model

Think of the AI model as a brain you can swap out. If your library is full of sports videos, you might find a model on the [Hugging Face Hub](https://huggingface.co/models?pipeline_tag=video-classification) that is an expert at identifying different sports.

You can tell the script to use it with the `--categorize-model` flag:
```bash
# Example: Using a hypothetical model specialized in sports
python video_dedupe_ai.py ... --categorize --categorize-model "user-name/sports-video-expert-v2"
```

#### 2. Speed Up AI with Your Graphics Card (GPU)

AI tasks can be slow on a normal computer processor (CPU). If you have a powerful gaming or workstation graphics card (an NVIDIA GPU with CUDA), you can tell the script to use it for a massive speed boost.
```bash
# This tells the script to automatically use your GPU if it finds one
python video_dedupe_ai.py ... --categorize --device auto
```

---

## The `config.ini` File: Your Personal Settings

Tired of typing the same options? You can create a simple text file named `config.ini` to save your favorite settings.

The script includes an option to create one for you automatically:
```bash
python video_dedupe_ai.py --generate-config
```
You can then open this file in a text editor and change the settings (like setting `dry_run = False` or `device = auto`) to your liking. The script will use these settings every time you run it.

---

## Troubleshooting & Frequently Asked Questions (FAQ)

#### Q: Why is the script running slowly?

Video analysis is hard work for a computer! The speed depends on your hardware and the features you enable.

* **Perceptual Hashing (`--perceptual-hash`)** is much slower than basic checks but is far more accurate.
* **AI Categorization (`--categorize`)** is the most intensive feature. For the best speed, use it with a powerful graphics card (`--device auto`).
* **If your computer feels sluggish,** you can try limiting the number of simultaneous tasks by setting `--max-workers 1` (or 2).

#### Q: I got an error like "FFmpeg not found" or "Permission denied." What do I do?

* **"FFmpeg not found":** This means the required FFmpeg tool isn't installed or isn't in your system's PATH. Please double-check the installation steps in the guide above.
* **"Permission denied":** This usually means the script doesn't have the rights to read a folder or write/delete a file. Make sure you have the correct permissions for the directories you're scanning.

#### Q: The script didn't find any duplicates, but I know I have some. Why?

The script has a multi-step process to be safe. For two videos to be considered a match, they must:

1.  Have **similar filenames** (e.g., `My Trip.mp4` and `My Trip (1).mp4` are good matches).
2.  Have a **nearly identical duration** (within a few seconds).
3.  If `--perceptual-hash` is on, they must have **visually similar content**.

If your files have completely different names (e.g., `video_01.mov` and `birthday_party.mp4`), the script may not identify them as potential duplicates in the first step.

#### Q: What happens to my photos and other files in my video folders?

They are completely safe! The script **only** looks at video files that match the extensions you've allowed (like `.mp4`, `.mov`, etc.). All other files and photos are ignored.

#### Q: What happens if I set both the "Main" and "Other" folders to be the same directory?

The script is smart enough to handle this. It will simply compare all the videos within that single folder against each other and plan to remove the lower-quality duplicates it finds there.
