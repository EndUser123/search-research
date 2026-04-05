"""
Example: Message Content and Thread Organization

This example demonstrates how to collect and organize Telegram messages
with their text content, organized by threads, alongside media downloads.
"""

import os
import sys
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dnld_telegram.src.download.storage import (
    DATABASE_AVAILABLE,
    ensure_database_initialized,
    get_channel_statistics,
    get_messages_by_thread,
    get_thread_roots,
    save_message_with_content,
    search_messages,
)


async def collect_messages_with_threads(
    client, chat_id: int, channel_name: str, limit: int = 100
) -> dict[str, Any]:
    """
    Collect messages from a Telegram channel with thread organization.

    This function would be integrated into the existing enumeration process
    to collect message text content alongside media information.
    """

    if not DATABASE_AVAILABLE:
        print("Database not available - message threading requires SQLite backend")
        return {"error": "Database not available"}

    # Ensure database is initialized
    ensure_database_initialized(channel_name, chat_id)

    print(
        f"Collecting messages from channel '{channel_name}' with thread organization..."
    )

    collected_messages = 0
    thread_relationships = 0

    # This would be integrated with existing message iteration logic
    async for message in client.iter_messages(chat_id, limit=limit):
        # Extract message information
        message_text = message.text or message.caption
        reply_to_id = None

        # Check if this is a reply (thread relationship)
        if message.reply_to and message.reply_to.reply_to_msg_id:
            reply_to_id = message.reply_to.reply_to_msg_id
            thread_relationships += 1

        # Extract media information if present
        media_type = None
        file_id = None
        file_size = None

        if message.media:
            media_type = type(message.media).__name__
            if hasattr(message.media, "document") and message.media.document:
                file_id = str(message.media.document.id)
                file_size = message.media.document.size
            elif hasattr(message.media, "photo") and message.media.photo:
                file_id = str(message.media.photo.id)

        # Save message with content and thread relationship
        save_message_with_content(
            channel_name=channel_name,
            telegram_id=message.id,
            message_text=message_text,
            reply_to_message_id=reply_to_id,
            date=message.date,
            media_type=media_type,
            file_id=file_id,
            file_size=file_size,
        )

        collected_messages += 1

        if collected_messages % 50 == 0:
            print(f"Collected {collected_messages} messages...")

    return {
        "collected_messages": collected_messages,
        "thread_relationships": thread_relationships,
        "channel_name": channel_name,
    }


def analyze_channel_threads(channel_name: str) -> dict[str, Any]:
    """Analyze thread structure and content in a channel."""

    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}

    print(f"\n=== Thread Analysis for Channel: {channel_name} ===")

    # Get overall statistics
    stats = get_channel_statistics(channel_name)
    print(f"Total messages: {stats['total_messages']}")
    print(f"Media messages: {stats['media_messages']}")
    print(f"Thread count: {stats['thread_count']}")

    # Get thread roots (messages that started conversations)
    thread_roots = get_thread_roots(channel_name)
    print(f"\nThread roots found: {len(thread_roots)}")

    thread_analysis = []

    for root in thread_roots:
        root_id = root["telegram_id"]
        reply_count = root["reply_count"]

        print(f"\n--- Thread {root_id} ({reply_count} replies) ---")
        print(
            f'Root message: "{root["text"][:100] if root["text"] else "(no text)"}..."'
        )
        print(f"Date: {root['date']}")
        print(f"Media: {root['media_type'] or 'None'}")

        # Get all messages in this thread
        thread_messages = get_messages_by_thread(
            channel_name, root_id, include_root=True
        )

        print("Thread conversation:")
        for i, msg in enumerate(thread_messages):
            prefix = "  ROOT" if msg["reply_to_message_id"] is None else f"  └─ {i}"
            text_preview = (msg["text"][:80] if msg["text"] else "(no text)") + "..."
            media_info = f" [Media: {msg['media_type']}]" if msg["media_type"] else ""
            print(f'{prefix}: "{text_preview}"{media_info}')

        thread_analysis.append(
            {
                "root_id": root_id,
                "reply_count": reply_count,
                "total_messages": len(thread_messages),
                "has_media": any(msg["media_type"] for msg in thread_messages),
                "root_text_preview": root["text"][:100] if root["text"] else None,
            }
        )

    return {
        "channel_stats": stats,
        "thread_count": len(thread_roots),
        "thread_analysis": thread_analysis,
    }


def search_channel_content(
    channel_name: str, search_terms: list[str]
) -> dict[str, Any]:
    """Search for specific content across messages."""

    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}

    print(f"\n=== Content Search in Channel: {channel_name} ===")

    search_results = {}

    for term in search_terms:
        results = search_messages(channel_name, term, limit=10)
        search_results[term] = results

        print(f"\nSearch term: '{term}' - {len(results)} results")
        for result in results[:3]:  # Show top 3 results
            text_preview = (
                result["text"][:100] if result["text"] else "(no text)"
            ) + "..."
            thread_info = (
                f" [Thread reply to {result['reply_to_message_id']}]"
                if result["reply_to_message_id"]
                else " [Thread root]"
            )
            print(f'  Message {result["telegram_id"]}: "{text_preview}"{thread_info}')

    return search_results


def main():
    """Example usage of message threading functionality."""

    print("=== Telegram Message Threading Example ===")

    if not DATABASE_AVAILABLE:
        print(
            "ERROR: Database backend not available. Message threading requires SQLite."
        )
        return

    # Use the test channel we've been working with
    channel_name = "koreannarchive"

    # Analyze existing thread structure
    analysis = analyze_channel_threads(channel_name)

    # Search for specific content
    search_terms = ["Korean", "culture", "thanks", "resources"]
    search_results = search_channel_content(channel_name, search_terms)

    # Summary
    print("\n=== Summary ===")
    if "error" not in analysis:
        print(f"Channel: {channel_name}")
        print(f"Total messages: {analysis['channel_stats']['total_messages']}")
        print(f"Active threads: {analysis['thread_count']}")
        print(
            f"Search terms found: {len([term for term, results in search_results.items() if results])}"
        )

        # Show thread structure summary
        if analysis["thread_analysis"]:
            print("\nThread Summary:")
            for thread in analysis["thread_analysis"]:
                print(
                    f"  Thread {thread['root_id']}: {thread['reply_count']} replies, "
                    f"{'with media' if thread['has_media'] else 'text only'}"
                )


if __name__ == "__main__":
    main()
