#!/usr/bin/env python
"""
speak.py — Read a text file or PDF aloud using Parler-TTS with selectable voices.

Usage:
    python speak.py document.txt                          # default voice
    python speak.py document.txt --voice jon              # named preset
    python speak.py document.txt --voice laura --emotion excited
    python speak.py document.txt --describe "A husky female speaker with a low, breathy voice"
    python speak.py document.pdf --voice jess --output audiobook.wav
    python speak.py document.txt --list-voices            # show all presets

Voice control:
    --voice NAME         Use a named preset (34 built-in speakers)
    --emotion MOOD       Add emotion styling (excited, calm, sad, angry, whispering, husky, breathy)
    --describe TEXT      Custom voice description (overrides --voice and --emotion)
    --speed SLOW|MODERATE|FAST   Speaking rate

Requirements:
    pip install git+https://github.com/huggingface/parler-tts.git
    pip install PyMuPDF   (for PDF support)
"""

import argparse
import sys
import re
import wave
import time
from pathlib import Path

# --- Voice presets ----------------------------------------------------------

# 34 named speakers from the Expresso dataset (baked into Parler-TTS mini)
NAMED_VOICES = [
    "Laura", "Gary", "Jon", "Lea", "Karen", "Rick", "Brenda", "David",
    "Eileen", "Jordan", "Mike", "Yann", "Joy", "James", "Eric", "Lauren",
    "Rose", "Will", "Jason", "Aaron", "Naomie", "Alisa", "Patrick", "Jerry",
    "Tina", "Jenna", "Bill", "Tom", "Carol", "Barbara", "Rebecca", "Anna",
    "Bruce", "Emily",
]

# Emotion → description fragment
EMOTION_MAP = {
    "excited":   "delivers words excitedly with high energy and enthusiasm",
    "calm":      "speaks calmly and soothingly with a steady, relaxed pace",
    "sad":       "speaks in a sad, melancholic tone with slower delivery",
    "angry":     "speaks with an angry, intense delivery and sharp emphasis",
    "whispering":"whispers softly in a hushed, intimate tone",
    "husky":     "has a husky, low and rough voice with a breathy quality",
    "breathy":   "has a breathy, soft voice with gentle airiness",
    "neutral":   "delivers words in a neutral, even tone",
}

SPEED_MAP = {
    "slow":    "slowly",
    "moderate":"at a moderate pace",
    "fast":    "quickly and with brisk energy",
}

def build_description(voice=None, emotion=None, custom_desc=None, speed="moderate"):
    """Build the voice description string that controls Parler-TTS output."""
    if custom_desc:
        return custom_desc

    parts = []

    if voice:
        # Use the named speaker format Parler-TTS was trained on
        voice_cap = voice.capitalize()
        if voice_cap in NAMED_VOICES:
            parts.append(f"{voice_cap}'s voice")
        else:
            parts.append(f"A speaker named {voice_cap}")
    else:
        parts.append("A speaker")

    if emotion and emotion in EMOTION_MAP:
        parts.append(EMOTION_MAP[emotion])

    if speed and speed in SPEED_MAP:
        parts.append(f"speaking {SPEED_MAP[speed]}")

    # Always add quality markers for best output
    parts.append("with very clear audio and almost no background noise")

    return ", ".join(parts) + "."


# --- Text extraction --------------------------------------------------------

def read_text_file(path):
    """Read a plain text, markdown, or similar file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf_file(path):
    """Extract text from a PDF using PyMuPDF (fitz)."""
    try:
        import fitz
    except ImportError:
        print("ERROR: PDF support requires PyMuPDF. Install with: pip install PyMuPDF", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(path)
    text_parts = []
    for page_num, page in enumerate(doc):
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)


def read_file(path):
    """Read text from a file based on extension."""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return read_pdf_file(path)
    else:
        return read_text_file(path)


def split_into_chunks(text, max_chars=300):
    """
    Split text into generation-sized chunks at sentence boundaries.
    Parler-TTS degrades on very long inputs — chunking at sentences
    keeps quality high and allows pause control via punctuation.
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Split on sentence boundaries, keeping the delimiter
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""

    for sentence in sentences:
        # If a single sentence is longer than max_chars, hard-split it
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            # Hard-split long sentences at comma or space boundaries
            words = sentence.split()
            for word in words:
                if len(current) + len(word) + 1 > max_chars:
                    chunks.append(current.strip())
                    current = word
                else:
                    current += " " + word if current else word
            continue

        if len(current) + len(sentence) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


# --- Audio utilities --------------------------------------------------------

def write_wav(path, audio_array, sample_rate):
    """Write a numpy audio array to a WAV file."""
    import numpy as np
    # Normalize to int16
    if audio_array.dtype != np.int16:
        audio_array = (audio_array * 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_array.tobytes())


def concatenate_wav(output_path, wav_paths):
    """Concatenate multiple WAV files into one."""
    if len(wav_paths) == 1:
        # Just rename/copy
        import shutil
        shutil.copy2(wav_paths[0], output_path)
        return

    data = []
    params = None
    for wav_path in wav_paths:
        with wave.open(str(wav_path), "rb") as wf:
            if params is None:
                params = wf.getparams()
            data.append(wf.readframes(wf.getnframes()))

    with wave.open(str(output_path), "w") as wf:
        wf.setparams(params)
        for chunk in data:
            wf.writeframes(chunk)


# --- Main TTS pipeline ------------------------------------------------------

def generate_speech(model, tokenizer, text, description, device, output_path,
                    chunk_dir=None):
    """Generate speech from text using the Parler-TTS model."""
    import torch

    chunks = split_into_chunks(text)

    if not chunks:
        print("ERROR: No text to generate.", file=sys.stderr)
        return False

    print(f"Text split into {len(chunks)} chunks ({sum(len(c) for c in chunks)} chars total)")
    print(f"Voice description: \"{description}\"")
    print()

    chunk_paths = []
    total_start = time.monotonic()

    for i, chunk in enumerate(chunks):
        chunk_start = time.monotonic()
        print(f"  [{i+1}/{len(chunks)}] Generating... ({len(chunk)} chars) ", end="", flush=True)

        input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
        prompt_input_ids = tokenizer(chunk, return_tensors="pt").input_ids.to(device)

        with torch.no_grad():
            generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)

        audio_arr = generation.cpu().numpy().squeeze()
        sample_rate = model.config.sampling_rate

        # Save chunk
        if chunk_dir:
            chunk_path = chunk_dir / f"chunk_{i:04d}.wav"
        else:
            chunk_path = Path(f"chunk_{i:04d}.wav")
        write_wav(chunk_path, audio_arr, sample_rate)
        chunk_paths.append(chunk_path)

        chunk_time = time.monotonic() - chunk_start
        audio_duration = len(audio_arr) / sample_rate
        print(f"done ({audio_duration:.1f}s audio in {chunk_time:.1f}s)")

    # Concatenate all chunks
    print()
    print("Concatenating chunks...")
    concatenate_wav(output_path, chunk_paths)
    total_time = time.monotonic() - total_start

    # Get total audio duration
    with wave.open(str(output_path), "rb") as wf:
        total_audio_duration = wf.getnframes() / wf.getframerate()

    print(f"Output: {output_path}")
    print(f"Total audio: {total_audio_duration:.1f}s | Generation time: {total_time:.1f}s | RTF: {total_time/total_audio_duration:.2f}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Read a text file or PDF aloud using Parler-TTS with selectable voices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python speak.py story.txt
  python speak.py story.txt --voice jon --emotion excited
  python speak.py story.txt --voice laura --emotion husky --speed slow
  python speak.py document.pdf --voice jess --output book.wav
  python speak.py story.txt --describe "A deep male voice with a Scottish accent, speaking warmly"
  python speak.py --list-voices
        """)
    parser.add_argument("input_file", nargs="?", help="Text or PDF file to read")
    parser.add_argument("--voice", default=None, help=f"Named preset voice ({', '.join(NAMED_VOICES[:8])}, ...)")
    parser.add_argument("--emotion", default=None, choices=list(EMOTION_MAP.keys()),
                        help="Emotion styling for the voice")
    parser.add_argument("--describe", default=None, help="Custom voice description (overrides --voice and --emotion)")
    parser.add_argument("--speed", default="moderate", choices=list(SPEED_MAP.keys()),
                        help="Speaking rate")
    parser.add_argument("--output", "-o", default="output.wav", help="Output WAV file path")
    parser.add_argument("--model", default="parler-tts/parler-tts-mini-v1",
                        help="Model name (default: parler-tts-mini-v1)")
    parser.add_argument("--list-voices", action="store_true", help="List available named voices and exit")
    parser.add_argument("--device", default=None, help="Device (cuda:0, cpu). Auto-detected if omitted.")
    parser.add_argument("--keep-chunks", action="store_true", help="Keep individual chunk WAV files")

    args = parser.parse_args()

    if args.list_voices:
        print("Named voices (from Expresso dataset):")
        for i, name in enumerate(NAMED_VOICES):
            print(f"  {name}", end="")
            if (i + 1) % 6 == 0:
                print()
        print()
        print()
        print("Emotions:", ", ".join(EMOTION_MAP.keys()))
        print("Speeds:", ", ".join(SPEED_MAP.keys()))
        print()
        print("Or use --describe for a fully custom voice.")
        return

    if not args.input_file:
        parser.error("input_file is required (or use --list-voices)")

    if not Path(args.input_file).exists():
        parser.error(f"File not found: {args.input_file}")

    # Determine device
    import torch
    device = args.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if "cuda" in device:
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Build voice description
    description = build_description(
        voice=args.voice,
        emotion=args.emotion,
        custom_desc=args.describe,
        speed=args.speed,
    )

    # Read input file
    print(f"Reading: {args.input_file}")
    text = read_file(args.input_file)
    print(f"Text length: {len(text)} characters")
    print()

    if len(text.strip()) < 5:
        print("ERROR: File appears to be empty or contains no readable text.", file=sys.stderr)
        sys.exit(1)

    # Load model
    print(f"Loading model: {args.model}")
    print("(First run downloads model weights (~1.8 GB for mini, ~4.5 GB for large) — this takes a minute)")
    load_start = time.monotonic()

    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer

    model = ParlerTTSForConditionalGeneration.from_pretrained(args.model).to(device)
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    load_time = time.monotonic() - load_start
    print(f"Model loaded in {load_time:.1f}s")
    print()

    # Create chunk directory
    output_path = Path(args.output)
    chunk_dir = output_path.parent / f".{output_path.stem}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    # Generate
    success = generate_speech(
        model=model,
        tokenizer=tokenizer,
        text=text,
        description=description,
        device=device,
        output_path=output_path,
        chunk_dir=chunk_dir,
    )

    if success and not args.keep_chunks:
        # Clean up chunk files
        if chunk_dir and chunk_dir.exists():
            import shutil
            shutil.rmtree(chunk_dir)
            print("Cleaned up temporary chunks.")
        else:
            for p in Path(".").glob("chunk_*.wav"):
                p.unlink()

    if success:
        print()
        print(f"Done! Audio saved to: {output_path}")


if __name__ == "__main__":
    main()
