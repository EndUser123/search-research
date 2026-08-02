#!/usr/bin/env python
"""
sample_voices.py — Generate short audio clips for each named voice and emotion
so you can listen and pick your favorites.

Usage:
    python sample_voices.py                          # all 34 voices, default emotion
    python sample_voices.py --emotion excited        # all voices, excited
    python sample_voices.py --voices jon,laura,jess   # specific voices only
    python sample_voices.py --emotion husky --voices laura,karen,brenda
    python sample_voices.py --all-emotions --voices jon,laura  # every emotion for 2 voices

Output: samples/ directory with one WAV per voice/emotion combo.
"""

import argparse
import sys
import time
from pathlib import Path

# Reuse the voice + emotion maps from speak.py
sys.path.insert(0, str(Path(__file__).parent))
from speak import NAMED_VOICES, EMOTION_MAP, SPEED_MAP, build_description, write_wav

SAMPLE_TEXT = "The quick brown fox jumps over the lazy dog. But wait — that's not the whole story, is it?"


def main():
    parser = argparse.ArgumentParser(description="Generate sample clips for each Parler-TTS voice.")
    parser.add_argument("--voices", default=None,
                        help="Comma-separated voice names (default: all 34). E.g.: jon,laura,jess")
    parser.add_argument("--emotion", default="neutral",
                        choices=list(EMOTION_MAP.keys()),
                        help="Emotion to apply to all samples (default: neutral)")
    parser.add_argument("--all-emotions", action="store_true",
                        help="Generate a clip for every emotion × voice combination")
    parser.add_argument("--speed", default="moderate", choices=list(SPEED_MAP.keys()))
    parser.add_argument("--model", default="parler-tts/parler-tts-mini-v1")
    parser.add_argument("--device", default=None)
    parser.add_argument("--output-dir", default="samples")
    args = parser.parse_args()

    import torch
    device = args.device or ("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if "cuda" in device:
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Determine which voices to sample
    if args.voices:
        voices = [v.strip().capitalize() for v in args.voices.split(",")]
        invalid = [v for v in voices if v not in NAMED_VOICES]
        if invalid:
            print(f"WARNING: {invalid} are not in the named voice list. They'll be used as custom descriptions.")
    else:
        voices = NAMED_VOICES

    # Determine which emotions to sample
    if args.all_emotions:
        emotions = list(EMOTION_MAP.keys())
    else:
        emotions = [args.emotion]

    total_clips = len(voices) * len(emotions)
    print(f"Generating {total_clips} sample clips ({len(voices)} voices × {len(emotions)} emotions)...")
    print(f"Sample text: \"{SAMPLE_TEXT}\"")
    print()

    # Load model
    print(f"Loading model: {args.model}")
    load_start = time.monotonic()
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer

    model = ParlerTTSForConditionalGeneration.from_pretrained(args.model).to(device)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    print(f"Model loaded in {time.monotonic() - load_start:.1f}s")
    print()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate clips
    completed = 0
    gen_start = time.monotonic()

    for voice in voices:
        for emotion in emotions:
            safe_name = voice.lower().replace(" ", "_")
            filename = f"{safe_name}_{emotion}.wav" if args.all_emotions else f"{safe_name}.wav"
            output_path = output_dir / filename

            description = build_description(
                voice=voice,
                emotion=emotion,
                speed=args.speed,
            )

            print(f"  [{completed+1}/{total_clips}] {voice} ({emotion})... ", end="", flush=True)

            input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
            prompt_input_ids = tokenizer(SAMPLE_TEXT, return_tensors="pt").input_ids.to(device)

            clip_start = time.monotonic()
            with torch.no_grad():
                generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)

            audio_arr = generation.cpu().numpy().squeeze()
            sample_rate = model.config.sampling_rate
            write_wav(output_path, audio_arr, sample_rate)

            clip_time = time.monotonic() - clip_start
            audio_dur = len(audio_arr) / sample_rate
            print(f"{audio_dur:.1f}s audio in {clip_time:.1f}s → {filename}")

            completed += 1

    total_time = time.monotonic() - gen_start
    print()
    print(f"Done! {completed} clips in {total_time:.1f}s")
    print(f"Samples saved to: {output_dir.resolve()}")
    print()
    print("Listen to them and pick your favorite, then use:")
    print("  python speak.py yourfile.txt --voice <name> --emotion <emotion>")


if __name__ == "__main__":
    main()
