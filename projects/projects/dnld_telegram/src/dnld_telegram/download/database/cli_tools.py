#!/usr/bin/env python3
"""
CLI tools for database sharding management.

This module provides command-line tools for:
- Analyzing database sharding status
- Migrating large databases to sharded format
- Managing database maintenance
"""

import argparse
import json

from loguru import logger

from .migration import get_migration_candidates, migrate_channel
from .sharding import check_all_channels_sharding_status, get_shard_manager


def cmd_status(args):
    """Show sharding status for all channels."""
    print("=== Database Sharding Status ===\n")

    all_status = check_all_channels_sharding_status()

    if not all_status:
        print("No channels found.")
        return

    # Sort by size (largest first)
    all_status.sort(key=lambda x: x["total_size_gb"], reverse=True)

    total_size = 0
    large_channels = 0
    needs_migration = 0

    for channel in all_status:
        name = channel["channel_name"]
        size_gb = channel["total_size_gb"]
        messages = channel["total_messages"]
        is_sharded = channel["is_sharded"]
        needs_sharding = channel["needs_sharding"]

        total_size += size_gb
        if size_gb > 1.0:
            large_channels += 1
        if needs_sharding and not is_sharded:
            needs_migration += 1

        # Color coding
        if needs_sharding and not is_sharded:
            status_color = "🔴"  # Red - needs migration
            status_text = "NEEDS MIGRATION"
        elif is_sharded:
            status_color = "🟢"  # Green - already sharded
            status_text = f"SHARDED ({len(channel['shards'])} shards)"
        elif size_gb > 1.0:
            status_color = "🟡"  # Yellow - large but manageable
            status_text = "LARGE"
        else:
            status_color = "⚪"  # White - small
            status_text = "OK"

        print(
            f"{status_color} {name:<20} {size_gb:>6.1f}GB {messages:>8,} msgs  {status_text}"
        )

        # Show shard details if sharded
        if is_sharded and args.verbose:
            for shard in channel["shards"]:
                shard_status = "CURRENT" if shard["is_current"] else "ARCHIVED"
                date_range = (
                    f" ({shard['date_range'][0][:10]} to {shard['date_range'][1][:10]})"
                    if shard["date_range"]
                    else ""
                )
                print(
                    f"    └─ {shard['name']:<15} {shard['size_gb']:>6.1f}GB {shard['message_count']:>8,} msgs  {shard_status}{date_range}"
                )

    print("\n=== Summary ===")
    print(f"Total channels: {len(all_status)}")
    print(f"Large channels (>1GB): {large_channels}")
    print(f"Channels needing migration: {needs_migration}")
    print(f"Total size: {total_size:.1f}GB")


def cmd_migrate(args):
    """Migrate a channel to sharded format."""
    channel_name = args.channel

    if not channel_name:
        print("Please specify a channel to migrate with --channel")
        return

    print(f"=== Migrating Channel: {channel_name} ===\n")

    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made\n")

    # Perform migration
    result = migrate_channel(
        channel_name=channel_name,
        create_backup=not args.no_backup,
        dry_run=args.dry_run,
    )

    if result.success:
        print("✅ Migration completed successfully!")
        print(f"Original size: {result.original_size_gb:.1f}GB")

        if not args.dry_run:
            print(f"New total size: {result.new_total_size_gb:.1f}GB")
            print(f"Shards created: {result.shards_created}")
            print(f"Messages migrated: {result.messages_migrated:,}")

            if result.backup_path:
                print(f"Backup created: {result.backup_path}")
    else:
        print("❌ Migration failed!")
        for error in result.errors:
            print(f"   Error: {error}")


def cmd_candidates(args):
    """Show channels that are candidates for migration."""
    print("=== Migration Candidates ===\n")

    candidates = get_migration_candidates()

    if not candidates:
        print("No channels found that need migration.")
        return

    # Sort by size (largest first)
    candidates.sort(key=lambda x: x["size_gb"], reverse=True)

    print(f"{'Channel':<20} {'Size':<10} {'Messages':<12} {'Status'}")
    print("-" * 55)

    for candidate in candidates:
        name = candidate["channel_name"]
        size_gb = candidate["size_gb"]
        messages = candidate["message_count"]

        if candidate["needs_migration"]:
            status = "🔴 NEEDS MIGRATION"
        elif candidate["is_sharded"]:
            status = "🟢 ALREADY SHARDED"
        else:
            status = "🟡 LARGE"

        print(f"{name:<20} {size_gb:>6.1f}GB {messages:>10,}   {status}")

    print(
        f"\nFound {len([c for c in candidates if c['needs_migration']])} channels needing migration."
    )


def cmd_analyze(args):
    """Analyze a specific channel in detail."""
    channel_name = args.channel

    if not channel_name:
        print("Please specify a channel to analyze with --channel")
        return

    print(f"=== Analyzing Channel: {channel_name} ===\n")

    manager = get_shard_manager(channel_name)
    summary = manager.get_shard_summary()

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    print(f"Channel: {summary['channel_name']}")
    print(f"Total size: {summary['total_size_gb']}GB")
    print(f"Total messages: {summary['total_messages']:,}")
    print(f"Total shards: {summary['total_shards']}")
    print(f"Is sharded: {'Yes' if summary['is_sharded'] else 'No'}")
    print(f"Needs sharding: {'Yes' if summary['needs_sharding'] else 'No'}")

    print("\n=== Shard Details ===")
    for shard in summary["shards"]:
        status = "CURRENT" if shard["is_current"] else "ARCHIVED"
        date_range = (
            f" ({shard['date_range'][0][:10]} to {shard['date_range'][1][:10]})"
            if shard["date_range"]
            else ""
        )
        print(
            f"  {shard['name']:<15} {shard['size_gb']:>6.1f}GB {shard['message_count']:>8,} msgs  {status}{date_range}"
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database sharding management tools for dnld_telegram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show all channels sharding status
  %(prog)s status -v                 # Show detailed shard information
  %(prog)s candidates                # Show channels needing migration
  %(prog)s migrate leaksasian        # Migrate leaksasian channel
  %(prog)s migrate leaksasian --dry-run  # Test migration without changes
  %(prog)s analyze leaksasian        # Analyze specific channel
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    status_parser = subparsers.add_parser(
        "status", help="Show sharding status for all channels"
    )
    status_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed shard information"
    )
    status_parser.set_defaults(func=cmd_status)

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate", help="Migrate a channel to sharded format"
    )
    migrate_parser.add_argument("channel", help="Channel name to migrate")
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze migration without making changes",
    )
    migrate_parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup before migration"
    )
    migrate_parser.set_defaults(func=cmd_migrate)

    # Candidates command
    candidates_parser = subparsers.add_parser(
        "candidates", help="Show channels that need migration"
    )
    candidates_parser.set_defaults(func=cmd_candidates)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a specific channel")
    analyze_parser.add_argument("channel", help="Channel name to analyze")
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")
    analyze_parser.set_defaults(func=cmd_analyze)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
