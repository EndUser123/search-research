---
title: "When analyzing videos, the problem has to do with knowing where screenshots need to be captured in order to analyze them"
date: "2025-12-29"
mode: "CONCISE"
uuid: "6e5de940-2a2a-47cc-8b31-370a0304c734"
entry_count: 1
---

## Human

When analyzing videos, the problem has to do with knowing where screenshots need to be captured in order to analyze them with LLMs that can only understand static images rather than videos. In the transcript of the video, creators will often use the words "this" or "that" or "here". Those may be indicators of where a screenshot can be taken. So, we need logic and code to take screenshots at those transcript locations and pass them to the analyzing AI.

## Assistant

To address video analysis limitations with image-only LLMs, parse transcripts for deictic terms like "this", "that", or "here" to identify screenshot timestamps, then extract frames using FFmpeg or OpenCV.[1][2]

## Transcript Parsing Logic
Load the transcript as a list of segments with timestamps (e.g., from yt-dlp or Whisper JSON output). Use spaCy or simple keyword matching to detect deictic indicators in lowercase-normalized text, capturing the segment's start time (in seconds) as the screenshot point.[3][4]

- Normalize transcript text: lowercase, strip punctuation.
- Keywords: ["this", "that", "here", "there"] – extend via POS tagging for demonstratives/PRP$.
- Filter segments >2s duration to avoid noise; aggregate nearby hits (±1s) for efficiency.

Example spaCy snippet (install via `pip install spacy; python -m spacy download en_core_web_sm`):
```python
import spacy
nlp = spacy.load("en_core_web_sm")
deictics = {"this", "that", "here", "there"}  # Add POS: doc[i].pos_ == "PRON" and lemma_ in deictics

def find_screenshot_times(transcript_segments):
    times = []
    for seg in transcript_segments:
        doc = nlp(seg["text"].lower())
        if any(token.text in deictics for token in doc):
            times.append(seg["start"])
    return times
```
This yields timestamps like `[10.5, 45.2]` for LLM input.[4]

## Screenshot Extraction
Use FFmpeg subprocess for precise frame grabs at timestamps – faster and more reliable on Windows 11 than OpenCV for large videos, aligning with yt-dlp workflows.[5][6][7]

```python
import subprocess
import json

def extract_screenshots(video_path, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for ts in timestamps:
        out_file = os.path.join(output_dir, f"frame_{ts:.2f}s.png")
        subprocess.run([
            "ffmpeg", "-ss", str(ts), "-i", video_path,
            "-frames:v", "1", "-q:v", "2", out_file, "-y", "-loglevel", "error"
        ], check=True)
    return [os.path.basename(f) for f in glob(os.path.join(output_dir, "*.png"))]
```
Pass screenshot paths + context to vision LLMs (e.g., GPT-4o via LiteLLM).[2][8]

## Integration Workflow
Chain in your UVIR pipeline: yt-dlp for video/transcript → parse → extract → LLM prompt like "Analyze screen at {ts}s: {image} for {transcript_context}". Batch timestamps to respect API limits; store in ChromaDB for RAG.[9]

## Optimization Tips
- Transcript format: Prefer Whisper/yt-dlp `--write-auto-sub` for word-level timestamps; fallback to segment-level.[10]
- Edge cases: Context window (e.g., screenshot at ts ±0.5s); dedupe clusters with 3s threshold.
- Windows 11: Ensure FFmpeg in PATH (via Chocolatey); test with `yt-dlp` aria2c for downloads.[7]
