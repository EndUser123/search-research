#!/usr/bin/env python3
"""
Telegram Channel ID Finder & TOML Auto-Fixer

This utility helps you find the chat_id/channel_id for Telegram channels
and can automatically fix problems in your channels.toml configuration file.

Usage:
    # Find individual channel info:
    python find_channel_id.py @channelname
    python find_channel_id.py https://t.me/channelname
    python find_channel_id.py channelname

    # Auto-fix TOML file:
    python find_channel_id.py --fix-toml
    python find_channel_id.py --validate-toml

Requirements:
    - Same .env file as dnld_telegram with your API credentials
    - Channel must be public or you must be a member
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import os
import re
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from telethon import TelegramClient  # type: ignore
from telethon.errors import (
    ChannelPrivateError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
)

# type: ignore
from telethon.sessions import StringSession  # type: ignore

if TYPE_CHECKING:
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib


def load_credentials() -> tuple[int, str, str]:
    """Load Telegram API credentials from .env file"""
    # Find .env in project root
    project_root = Path(__file__).parent
    env_path = project_root / ".env"

    if not env_path.exists():
        print("❌ Error: .env file not found!")
        print(f"Expected location: {env_path}")
        print("\nPlease create a .env file with your Telegram API credentials:")
        print("TELEGRAM_API_ID=your_api_id")
        print("TELEGRAM_API_HASH=your_api_hash")
        print("TELEGRAM_SESSION_STRING=your_session_string")
        sys.exit(1)

    load_dotenv(env_path)

    api_id = os.getenv("TELEGRAM_API_ID", "")
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

    if not all([api_id, api_hash, session_string]):
        print("❌ Error: Missing Telegram credentials in .env file!")
        print("Required: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING")
        sys.exit(1)

    return int(api_id) if api_id else 0, api_hash, session_string


def clean_channel_input(channel_input):
    """Clean and normalize channel input"""
    channel = channel_input.strip()

    # Check if input is a channel ID (positive or negative number)
    if channel.isdigit():  # Checks for positive digits only
        return -int(channel)  # Convert positive ID to negative
    elif (
        channel.startswith("-") and channel[1:].isdigit()
    ):  # Checks for negative digits
        return int(channel)  # Keep negative ID as is

    # Remove https://t.me/ prefix
    if channel.startswith("https://t.me/"):
        channel = channel[13:]
    elif channel.startswith("http://t.me/"):
        channel = channel[12:]
    elif channel.startswith("t.me/"):
        channel = channel[5:]

    # Remove @ prefix if present
    if channel.startswith("@"):
        channel = channel[1:]

    return channel


async def find_channel_info(channel_input):
    """Find channel info - works with both username and channel ID"""
    api_id, api_hash, session_string = load_credentials()

    # Create client from session string (same method as dnld_telegram)
    client = TelegramClient(StringSession(session_string), api_id, api_hash)

    try:
        # Connect and check authorization
        await client.connect()
        if not await client.is_user_authorized():
            print(
                "❌ Error: Client is not authorized. Please check your session string."
            )
            return None
        print("✅ Connected to Telegram")

        # Clean the channel input (returns int if ID, string if username)
        clean_input = clean_channel_input(channel_input)

        # Determine lookup type
        if isinstance(clean_input, int):
            print(f"🔍 Looking up channel ID: {clean_input}")
            lookup_type = "ID"
        else:
            print(f"🔍 Looking for channel: {clean_input}")
            lookup_type = "username"

        try:
            # Get the entity (channel/chat)
            entity = await client.get_entity(clean_input)

            # Extract information
            channel_id = entity.id
            title = getattr(entity, "title", "Unknown")
            username = getattr(entity, "username", None)
            members_count = getattr(entity, "participants_count", None)

            print("\n" + "=" * 60)
            print("🎉 CHANNEL FOUND!")
            print("=" * 60)
            print(f"Title: {title}")
            print(f"Username: @{username}" if username else "Username: None (Private)")
            print(f"Channel ID: {channel_id}")
            if members_count:
                print(f"Members: {members_count:,}")
            print(
                f"Link: https://t.me/{username}"
                if username
                else "Link: Private channel"
            )

            if lookup_type == "ID":
                print("\n📝 Add this to your channels.toml:")
                config_name = username if username else f"channel_{abs(channel_id)}"
                print(f"{config_name} = {channel_id}")
            else:
                print("\n📝 Add this to your channels.toml:")
                print(f"{clean_input} = {channel_id}")

            print("\nOr add to your .env TELEGRAM_CHANNELS:")
            config_name = (
                username
                if username
                else (
                    clean_input
                    if isinstance(clean_input, str)
                    else f"channel_{abs(channel_id)}"
                )
            )
            print(f'"{config_name}": {channel_id}')
            print("=" * 60)

            return channel_id

        except ChannelPrivateError:
            if isinstance(clean_input, int):
                print(
                    f"❌ Error: Channel ID '{clean_input}' is private and you're not a member"
                )
            else:
                print(
                    f"❌ Error: Channel '@{clean_input}' is private and you're not a member"
                )
            print("💡 Tip: Join the channel first, then try again")

        except UsernameNotOccupiedError:
            if isinstance(clean_input, int):
                print(f"❌ Error: Channel ID '{clean_input}' does not exist")
            else:
                print(f"❌ Error: Channel '@{clean_input}' does not exist")
            print("💡 Tip: Check the spelling/ID and try again")

        except UsernameInvalidError:
            if isinstance(clean_input, int):
                print(f"❌ Error: '{clean_input}' is not a valid channel ID")
            else:
                print(f"❌ Error: '{clean_input}' is not a valid username")
            print(
                "💡 Tip: Use format like 'channelname', '@channelname', or '-1001234567890'"
            )

        except Exception as e:
            print(f"❌ Error finding channel: {e}")
            print("💡 Tip: Make sure the channel exists and you have access")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Tip: Check your API credentials in .env file")

    finally:
        await client.disconnect()

    return None


async def get_channel_info_silent(client, channel_id_or_username):
    """Get channel info without printing, for batch operations"""
    try:
        entity = await client.get_entity(channel_id_or_username)
        return {
            "id": entity.id,
            "title": getattr(entity, "title", "Unknown"),
            "username": getattr(entity, "username", None),
            "members_count": getattr(entity, "participants_count", None),
        }
    except Exception:
        return None


def validate_toml_file(toml_path=None):
    """Validate channels.toml file and return issues found"""
    if toml_path is None:
        toml_path = Path(__file__).parent / "channels.toml"

    if not toml_path.exists():
        return [f"❌ channels.toml not found at {toml_path}"]

    issues = []

    try:
        # Read raw content to check for syntax issues
        with open(toml_path, encoding="utf-8") as f:
            content = f.read()

        # Check for incomplete lines (lines that look like IDs but have no key=value format)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("[") or line.startswith("#"):
                continue

            # Check for lines that are just numbers (incomplete entries)
            if re.match(r"^\d+$", line):
                issues.append(
                    f"Line {i}: Incomplete entry '{line}' - missing key name and equals sign"
                )
            elif "=" not in line and line:
                issues.append(
                    f"Line {i}: Invalid TOML syntax '{line}' - missing equals sign"
                )

        # Try to parse TOML
        if tomllib:
            try:
                parsed = tomllib.loads(content)
                if "TELEGRAM_CHANNELS" not in parsed:
                    issues.append("❌ Missing [TELEGRAM_CHANNELS] section")
                else:
                    channels = parsed["TELEGRAM_CHANNELS"]
                    if not channels:
                        issues.append("❌ [TELEGRAM_CHANNELS] section is empty")
            except Exception as e:
                issues.append(f"❌ TOML parsing error: {e}")
        else:
            issues.append(
                "⚠️  Cannot validate TOML format - tomllib/tomli not available"
            )

    except Exception as e:
        issues.append(f"❌ Error reading file: {e}")

    return issues


async def fix_toml_file(toml_path=None, dry_run=False):
    """Automatically fix issues in channels.toml file"""
    if toml_path is None:
        toml_path = Path(__file__).parent / "channels.toml"

    print(f"🔧 {'Validating' if dry_run else 'Fixing'} channels.toml file...")
    print(f"📁 File: {toml_path}")
    print("=" * 60)

    # First validate
    issues = validate_toml_file(toml_path)
    if not issues:
        print("✅ No issues found in channels.toml!")
        return True

    print("🔍 Issues found:")
    for issue in issues:
        print(f"  {issue}")

    if dry_run:
        print("\n💡 Run with --fix-toml to automatically fix these issues")
        return False

    # Load API credentials
    try:
        api_id, api_hash, session_string = load_credentials()
    except SystemExit:
        print("❌ Cannot fix TOML without API credentials")
        return False

    # Read current content
    with open(toml_path, encoding="utf-8") as f:
        content = f.read()

    # Create backup
    backup_path = toml_path.with_suffix(".toml.backup")
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Backup created: {backup_path}")

    # Connect to Telegram
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    fixed_lines = []
    fixes_made = 0

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Client not authorized - cannot lookup channel info")
            return False

        print("✅ Connected to Telegram API")
        print("🔍 Looking up missing channel information...")

        lines = content.split("\n")
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()

            # Keep empty lines, comments, and section headers as-is
            if not line or line.startswith("[") or line.startswith("#"):
                fixed_lines.append(original_line)
                continue

            # Check for incomplete entries (just a number)
            if re.match(r"^\d+$", line):
                print(f"🔍 Looking up incomplete entry: {line}")
                # Convert to negative ID format
                channel_id = -int(line)

                # Look up channel info
                info = await get_channel_info_silent(client, channel_id)
                if info:
                    # Use username if available, otherwise generate a name
                    if info["username"]:
                        key_name = info["username"]
                    else:
                        key_name = f"channel_{abs(info['id'])}"

                    fixed_line = f"{key_name} = {info['id']}"
                    fixed_lines.append(fixed_line)
                    print(f"✅ Fixed: {line} → {fixed_line} (Title: {info['title']})")
                    fixes_made += 1
                else:
                    print(
                        f"❌ Could not lookup channel ID {channel_id} - keeping as comment"
                    )
                    fixed_lines.append(f"# FIXME: Could not lookup channel {line}")
                    fixes_made += 1

            # Check for lines missing equals sign but not just numbers
            elif "=" not in line and line and not re.match(r"^\d+$", line):
                print(f"⚠️  Invalid syntax, commenting out: {line}")
                fixed_lines.append(f"# FIXME: Invalid syntax - {line}")
                fixes_made += 1

            else:
                # Line looks fine, keep as-is
                fixed_lines.append(original_line)

    finally:
        await client.disconnect()

    if fixes_made > 0:
        # Write fixed content
        fixed_content = "\n".join(fixed_lines)
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        print(f"\n✅ Fixed {fixes_made} issues in channels.toml")
        print(f"📁 Original backed up to: {backup_path}")

        # Validate the fixed file
        new_issues = validate_toml_file(toml_path)
        if new_issues:
            print("\n⚠️  Some issues remain:")
            for issue in new_issues:
                print(f"  {issue}")
        else:
            print("\n🎉 All issues have been resolved!")

        return True
    else:
        print("\n💡 No automatic fixes could be applied")
        return False


def print_usage():
    """Print usage instructions"""
    print("🔧 Telegram Channel Info Finder & TOML Auto-Fixer")
    print("=" * 50)
    print("Usage:")
    print("  # Find individual channel info:")
    print("  python find_channel_id.py @channelname")
    print("  python find_channel_id.py https://t.me/channelname")
    print("  python find_channel_id.py channelname")
    print("  python find_channel_id.py -1001234567890")
    print("\n  # Find name from ID:")
    print("  python find_channel_id.py -1002436706028")
    print("  python find_channel_id.py -1001518888395")
    print("\n  # Fix TOML issues:")
    print("  python find_channel_id.py --validate-toml  # Shows what needs fixing")
    print(
        "  python find_channel_id.py --fix-toml       # Auto-fixes incomplete entries"
    )
    print("\nNotes:")
    print("• Works both ways: username → ID or ID → username")
    print("• Channel must be public or you must be a member")
    print("• Requires same .env file as dnld_telegram")
    print("• Channel IDs are negative numbers (e.g., -1002436706028)")
    print("• TOML auto-fix looks up missing channel info and creates backups")


async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    channel_input = sys.argv[1]

    if channel_input in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)

    print("🔧 Telegram Channel Info Finder")
    print("=" * 40)

    if channel_input == "--fix-toml":
        await fix_toml_file(dry_run=False)
    elif channel_input == "--validate-toml":
        await fix_toml_file(dry_run=True)
    else:
        await find_channel_info(channel_input)


if __name__ == "__main__":
    asyncio.run(main())
