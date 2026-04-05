"""
yt_grok_srt_to_text.py

Purpose:
Converts YouTube SRT (subtitle) files to readable TXT format while preserving:
- Natural speech patterns and content flow
- Logical paragraph breaks based on timing and topics
- Technical terms, proper nouns, and numbers
- Speaker transitions and emphasis
- Content validation via word count metrics

Usage: python yt_grok_srt_to_text.py <channel_name>
Author: [Your Name]
Date: February 20, 2025
"""

import os
import re


def parse_srt(srt_file):
    """Parse SRT file into blocks with timestamps and content."""
    with open(srt_file, encoding="utf-8") as file:
        content = file.read()

    # Split into blocks and preserve timing
    blocks = []
    current_time = 0
    for block in re.split(r"\n\n", content):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and lines[0].isdigit():
            # Extract timestamp and check for pauses
            time_parts = lines[1].split(" --> ")
            start_time = parse_timestamp(time_parts[0])

            # Add paragraph break on significant pauses
            if start_time - current_time > 2.0:  # 2 second pause threshold
                blocks.append("")  # Add break

            text = " ".join(lines[2:]).strip()
            if text and not text == "[Music]":
                blocks.append(text)
                current_time = parse_timestamp(time_parts[1])

    return blocks


def parse_timestamp(ts):
    """Convert timestamp to seconds."""
    h, m, s = ts.split(":")
    s, ms = s.split(",")
    return int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000


def format_text(blocks):
    """Format text blocks into readable paragraphs while preserving meaning."""
    # Remove filler words
    filler_words = {
        r"\b(um|uh)\b": "",
        r"\byou know\b": "",
        r"\bkind of\b": "",
        r"\bsort of\b": "",
        r"\blike\b(?!\s+to\b)": "",  # Preserve "like to"
    }

    # Enhanced section markers
    section_breaks = {
        # Market Analysis
        "looking at the market",
        "turning to",
        "in terms of",
        # Technical Analysis
        "technical perspective",
        "support level",
        "resistance",
        # Stock Discussion
        "moving to",
        "speaking of",
        "when we look at",
        # Summary/Conclusion
        "bottom line",
        "key takeaway",
        "what this means",
    }

    # Technical terms to preserve
    tech_terms = {
        # Market Indices
        "S&P 500",
        "NASDAQ",
        "DOW",
        "Russell 2000",
        # Technical Indicators
        "RSI",
        "MACD",
        "moving average",
        "support",
        "resistance",
        # Stock Groups
        "MAG-7",
        "Magnificent Seven",
    }

    paragraphs = []
    current = []

    for block in blocks:
        # Clean up filler words
        for pattern, replacement in filler_words.items():
            block = re.sub(pattern, replacement, block, flags=re.IGNORECASE)
        block = re.sub(r"\s+", " ", block).strip()

        # Start new paragraph on major transitions
        if len(current) >= 3 or any(
            marker in block.lower() for marker in section_breaks
        ):
            if current:
                paragraphs.append(" ".join(current))
                paragraphs.append("")  # Extra line break
            current = []

        # Preserve technical terms
        for term in tech_terms:
            pattern = re.compile(rf"\b{term.lower()}\b", re.IGNORECASE)
            block = pattern.sub(term, block)

        if block:
            current.append(block)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(filter(None, paragraphs))


def process_directory(channel_name, root_path="C:\\TEMP\\_yt"):
    """Process all SRT files in the channel's _SRT directory into TXT files."""
    srt_dir = os.path.join(root_path, channel_name, "_SRT")
    txt_dir = os.path.join(root_path, channel_name, "_TXT")
    os.makedirs(txt_dir, exist_ok=True)

    for srt_file in os.listdir(srt_dir):
        if srt_file.endswith(".srt"):
            srt_path = os.path.join(srt_dir, srt_file)
            txt_filename = srt_file.replace(".srt", ".txt")
            txt_path = os.path.join(txt_dir, txt_filename)

            # Get original SRT content word count
            with open(srt_path, encoding="utf-8") as f:
                srt_content = f.read()
                srt_words = len(srt_content.split())

            # Convert SRT to formatted text
            blocks = parse_srt(srt_path)
            if not blocks:
                print(
                    f"SRT words: {srt_words:>5}, TXT words:     0 - No text found in {srt_file}"
                )
                continue

            final_text = format_text(blocks)
            final_words = len(final_text.split())

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            print(
                f"SRT words: {srt_words:>5}, TXT words: {final_words:>5} - {srt_file}"
            )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python yt_grok_srt_to_text.py <channel_name>")
        sys.exit(1)
    process_directory(sys.argv[1])
