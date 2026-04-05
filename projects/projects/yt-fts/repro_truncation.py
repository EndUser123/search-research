import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yt_fts.services.channel_cleaner import ChannelCleaner
from yt_fts.utils.text_formatter import TextFormatter


def test_truncation():
    cleaner = ChannelCleaner()
    formatter = TextFormatter()

    channels = ["@GoogleDeepMind", "https://www.youtube.com/@GoogleDeepMind"]

    print("Testing ChannelCleaner...")
    cleaned, stats = cleaner.clean_channels(channels)
    for original, final in zip(channels, cleaned):
        print(f"'{original}' -> '{final}' (Length: {len(final)})")
        if len(final) < len(original) and "@" not in final:  # simplistic check
            print("  [POTENTIAL TRUNCATION DETECTED]")

    print("\nTesting TextFormatter.shorten_channel...")
    long_channel = "A" * 60
    shortened = formatter.shorten_channel(long_channel)
    print(f"Original: {long_channel} (60 chars)")
    print(f"Shortened: {shortened} (Length: {len(shortened)})")

    # Test valid channel
    valid_channel = "https://www.youtube.com/@GoogleDeepMind"
    shortened_valid = formatter.shorten_channel(valid_channel)
    print(f"Valid URL shortened: {shortened_valid}")

    # Test logic from ParallelBatchProcessor
    # simulating the loop
    print("\nSimulating ParallelBatchProcessor loop...")
    channel = "@GoogleDeepMind"
    # Logic in parallel_processor uses 'channel' directly
    print(f"Channel passed to downloader: {channel}")


if __name__ == "__main__":
    test_truncation()
