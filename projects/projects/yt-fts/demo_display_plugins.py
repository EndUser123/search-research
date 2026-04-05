#!/usr/bin/env python3
"""
Demo script showing different display plugin styles for yt-fts batch downloads.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yt_fts.ui.plugins import create_plugin


def demo_plugin(plugin_name: str) -> None:
    """Demonstrate a display plugin with sample data."""
    print(f"\n{'='*60}")
    print(f"🎨 DISPLAY PLUGIN: {plugin_name.upper()}")
    print(f"{'='*60}")

    # Create plugin
    plugin = create_plugin(plugin_name)

    # Sample channel header
    plugin.display_channel_header(
        {
            "index": 1,
            "total": 3,
            "name": "@NVIDIAdeveloper",
            "db_count": 926,
            "db_stats": "926 videos, 124 with transcripts",
        }
    )

    # Sample RSS status
    plugin.display_rss_status(
        {
            "status": "new_videos",
            "message": "5 discovered -> saving 3",
            "missing_count": 5,
            "scan_count": 3,
        }
    )

    # Sample download result
    plugin.display_download_result(
        {
            "success": True,
            "videos_count": 3,
            "videos_without_subtitles": 1,
            "total_videos": 4,
            "message": "Successfully downloaded",
        }
    )

    # Sample failed result
    plugin.display_channel_header(
        {
            "index": 2,
            "total": 3,
            "name": "@SomeChannel",
            "db_count": 0,
            "db_stats": "0 videos",
        }
    )

    plugin.display_rss_status(
        {"status": "error", "message": "error", "error_msg": "Network timeout"}
    )

    plugin.display_download_result({"success": False, "error": "Rate limit exceeded"})

    # Final summary
    plugin.display_batch_summary(
        {
            "successful": [
                {"channel": "@NVIDIAdeveloper", "videos_count": 3},
                {"channel": "@AnotherChannel", "videos_count": 5},
            ],
            "failed": [{"channel": "@SomeChannel", "error": "Rate limit exceeded"}],
            "total_channels": 3,
            "total_videos": 8,
        }
    )

    plugin.cleanup()


def main() -> None:
    """Run demo for all display plugins."""
    print("🚀 yt-fts Display Plugin Demo")
    print("Shows how different display styles present the same information")

    plugins = ["default", "compact", "detailed", "minimal", "table", "progress"]

    for plugin_name in plugins:
        try:
            demo_plugin(plugin_name)
        except Exception as e:
            print(f"❌ Error with {plugin_name} plugin: {e}")

    print(f"\n{'='*60}")
    print("✅ Demo complete! All 5 display plugins working.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
