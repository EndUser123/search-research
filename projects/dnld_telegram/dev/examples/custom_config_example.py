#!/usr/bin/env python3
"""
Example: Custom Media Type Configuration

This example shows how to customize media type classification
by modifying the config.toml file.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dnld_telegram.src.download.config import classify_media_type, get_media_config


def demonstrate_custom_config():
    """Demonstrate custom media type configuration."""

    print("=== Custom Media Type Configuration Example ===")
    print()

    # Load current configuration
    config = get_media_config()
    print(f"Configuration loaded from: {config.config_path}")
    print()

    # Show current classification rules
    print("Current Classification Rules:")
    rules = config.get_classification_rules()
    for category, category_rules in rules.items():
        if category == "defaults":
            continue
        extensions = category_rules.get("extensions", [])
        keywords = category_rules.get("keywords", [])
        print(f"  {category}:")
        if extensions:
            print(
                f"    Extensions: {extensions[:5]}{'...' if len(extensions) > 5 else ''}"
            )
        if keywords:
            print(f"    Keywords: {keywords}")
    print()

    # Test with various files
    test_files = [
        # Standard cases
        ("MessageMediaDocument", "movie.mp4"),
        ("MessageMediaDocument", "song.flac"),
        ("MessageMediaPhoto", "photo.jpg"),
        ("MessageMediaDocument", "document.pdf"),
        ("MessageMediaDocument", "archive.7z"),
        # Edge cases that can be customized
        ("MessageMediaDocument", "presentation.pptx"),
        ("MessageMediaDocument", "database.sqlite"),
        ("MessageMediaDocument", "source.py"),
        ("MessageMediaDocument", "config.yaml"),
        ("MessageMediaDocument", "backup.iso"),
    ]

    print("Classification Examples:")
    categories = {}
    for media_type, filename in test_files:
        result = classify_media_type(media_type, filename)
        print(f"  {filename:<20} → {result}")

        if result not in categories:
            categories[result] = []
        categories[result].append(filename)

    print()
    print("Files Grouped by Category:")
    for category, files in sorted(categories.items()):
        print(f"  {category}: {len(files)} files")
        for file in files:
            print(f"    - {file}")

    print()
    print("=== Customization Instructions ===")
    print()
    print("To customize media type classification, edit config.toml:")
    print()
    print("1. Add new file extensions to existing categories:")
    print("   [media_classification.text]")
    print('   extensions = ["txt", "pdf", "py", "js", "sql", "your_extension"]')
    print()
    print("2. Add keywords for better detection:")
    print("   [media_classification.video]")
    print('   keywords = ["video", "movie", "clip", "your_keyword"]')
    print()
    print("3. Create custom categories (update CLI choices too):")
    print("   [media_classification.code]")
    print('   extensions = ["py", "js", "css", "html", "sql"]')
    print('   keywords = ["source", "script", "code"]')
    print()
    print("4. Adjust priority order:")
    print("   [media_classification.defaults]")
    print('   priority_order = ["video", "image", "code", "text", "archive", "other"]')
    print()
    print("After editing config.toml, restart the application or call reload_config()")


def show_config_format():
    """Show the expected config.toml format."""

    print("=== config.toml Format Reference ===")
    print()

    sample_config = """
# Media Type Classification Configuration
[media_classification]

[media_classification.video]
extensions = ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"]
telegram_types = ["MessageMediaDocument"]
keywords = ["video", "movie", "clip"]

[media_classification.image]
extensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"]
telegram_types = ["MessageMediaPhoto", "MessageMediaWebPage"]
keywords = ["image", "photo", "picture", "screenshot"]

[media_classification.text]
extensions = ["txt", "pdf", "doc", "docx", "md", "html", "xml"]
telegram_types = []
keywords = ["document", "text", "manual", "guide"]

[media_classification.audio]
extensions = ["mp3", "wav", "flac", "aac", "ogg", "m4a"]
telegram_types = ["MessageMediaDocument"]
keywords = ["audio", "music", "song", "sound"]

[media_classification.archive]
extensions = ["zip", "rar", "7z", "tar", "gz", "exe", "msi"]
telegram_types = ["MessageMediaDocument"]
keywords = ["archive", "backup", "installer"]

[media_classification.defaults]
priority_order = ["video", "image", "audio", "text", "archive", "other"]
strict_mode = false
use_telegram_types = true
use_keywords = true
case_sensitive = false
"""

    print(sample_config.strip())


if __name__ == "__main__":
    demonstrate_custom_config()
    print("\n" + "=" * 60 + "\n")
    show_config_format()
