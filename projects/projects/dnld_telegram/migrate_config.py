#!/usr/bin/env python3
"""
Configuration Migration Script

Migrates from legacy config.toml format to the optimal configuration system.
This script will:
1. Analyze existing configuration files
2. Create new structured configuration files
3. Backup legacy configurations
4. Validate the new system

Usage:
    python migrate_config.py [--dry-run] [--backup-dir path]
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import toml


class ConfigMigrator:
    """Handles migration from legacy to optimal configuration system."""

    def __init__(self, project_root: Path, backup_dir: Path | None = None):
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / "config"
        self.backup_dir = backup_dir or (self.project_root / "config_backup")

        # Legacy config files
        self.legacy_config_toml = self.project_root / "config.toml"
        self.legacy_channels_toml = self.project_root / "channels.toml"

        # New config files
        self.new_app_toml = self.config_dir / "app.toml"
        self.new_channels_toml = self.config_dir / "channels.toml"
        self.new_environments_toml = self.config_dir / "environments.toml"

    def analyze_legacy_config(self) -> dict[str, Any]:
        """Analyze existing configuration files."""
        analysis = {
            "legacy_files_found": [],
            "legacy_config": {},
            "migration_needed": False,
            "issues": [],
        }

        # Check for legacy config.toml
        if self.legacy_config_toml.exists():
            analysis["legacy_files_found"].append(str(self.legacy_config_toml))
            try:
                analysis["legacy_config"] = toml.load(self.legacy_config_toml)
                analysis["migration_needed"] = True
            except Exception as e:
                analysis["issues"].append(
                    f"Could not parse {self.legacy_config_toml}: {e}"
                )

        # Check for legacy channels.toml
        if self.legacy_channels_toml.exists():
            analysis["legacy_files_found"].append(str(self.legacy_channels_toml))
            analysis["migration_needed"] = True

        # Check for environment variables
        import os

        env_channels = {k: v for k, v in os.environ.items() if k.startswith("CHANNEL_")}
        if env_channels:
            analysis["env_channels"] = env_channels

        telegram_channels = os.getenv("TELEGRAM_CHANNELS")
        if telegram_channels:
            try:
                analysis["telegram_channels_json"] = json.loads(telegram_channels)
            except json.JSONDecodeError:
                analysis["issues"].append(
                    "TELEGRAM_CHANNELS env var contains invalid JSON"
                )

        return analysis

    def create_backup(self, dry_run: bool = False) -> bool:
        """Create backup of existing configuration files."""
        if not dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_count = 0

        files_to_backup = [
            self.legacy_config_toml,
            self.legacy_channels_toml,
            self.new_app_toml,
            self.new_channels_toml,
            self.new_environments_toml,
        ]

        for file_path in files_to_backup:
            if file_path.exists():
                backup_name = f"{file_path.name}.{timestamp}.bak"
                backup_path = self.backup_dir / backup_name

                print(f"📦 Backing up {file_path} -> {backup_path}")

                if not dry_run:
                    shutil.copy2(file_path, backup_path)
                backup_count += 1

        print(f"✅ Backed up {backup_count} files to {self.backup_dir}")
        return True

    def migrate_app_config(
        self, legacy_config: dict[str, Any], dry_run: bool = False
    ) -> dict[str, Any]:
        """Migrate application configuration to new format."""
        new_config = {
            "app": {
                "name": "Telegram Downloader",
                "version": "2.0",
                "environment": "development",
            },
            "paths": {
                "channels_base": "channels",
                "temp_base": None,
                "media_base": None,
                "database_base": None,
                "logs_base": "logs",
            },
            "database": {
                "connection_timeout": 30,
                "max_connections": 5,
                "pragma_settings": [
                    "journal_mode=WAL",
                    "synchronous=NORMAL",
                    "cache_size=10000",
                    "temp_store=memory",
                ],
                "shard_threshold_gb": 5.0,
                "max_shard_size_gb": 50.0,
                "auto_shard": True,
            },
            "download": {
                "max_concurrent": 2,
                "connection_timeout": 30,
                "read_timeout": 60,
                "retry_attempts": 3,
                "retry_delay": 2,
                "verify_downloads": True,
                "cleanup_temp_on_exit": True,
                "organize_by_channel": True,
            },
            "logging": {
                "console_level": "WARNING",
                "file_level": "DEBUG",
                "max_size_mb": 50,
                "backup_count": 5,
                "retention_days": 30,
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            },
            "ui": {
                "default_mode": "tqdm",
                "fallback_mode": "simple",
                "show_speed": True,
                "show_eta": True,
                "show_file_progress": True,
                "update_frequency": 0.1,
            },
            "performance": {
                "max_memory_mb": 1024,
                "gc_threshold": 100,
                "buffer_size": 65536,
                "use_aiofiles": True,
            },
        }

        # Migrate legacy settings
        if "paths" in legacy_config:
            paths_config = legacy_config["paths"]
            if "channels_base" in paths_config:
                new_config["paths"]["channels_base"] = paths_config["channels_base"]

        # Migrate download settings
        if "download" in legacy_config:
            download_config = legacy_config["download"]
            for key in [
                "max_concurrent",
                "connection_timeout",
                "retry_attempts",
                "verify_downloads",
            ]:
                if key in download_config:
                    new_config["download"][key] = download_config[key]

        # Migrate database settings
        if "database" in legacy_config:
            db_config = legacy_config["database"]
            for key in ["connection_timeout", "shard_threshold_gb", "auto_shard"]:
                if key in db_config:
                    new_config["database"][key] = db_config[key]

        # Migrate logging settings
        if "logging" in legacy_config:
            log_config = legacy_config["logging"]
            for key in ["console_level", "file_level", "max_size_mb", "backup_count"]:
                if key in log_config:
                    new_config["logging"][key] = log_config[key]

        print(
            f"🔧 Migrated app configuration with {len(legacy_config)} legacy sections"
        )

        if not dry_run:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.new_app_toml, "w") as f:
                toml.dump(new_config, f)

        return new_config

    def migrate_channels_config(
        self, analysis: dict[str, Any], dry_run: bool = False
    ) -> dict[str, Any]:
        """Migrate channels configuration to new format."""
        channels = {}

        # Load from legacy channels.toml if it exists
        if self.legacy_channels_toml.exists():
            try:
                legacy_channels = toml.load(self.legacy_channels_toml)
                if "TELEGRAM_CHANNELS" in legacy_channels:
                    channels.update(legacy_channels["TELEGRAM_CHANNELS"])
                elif "channels" in legacy_channels:
                    channels.update(legacy_channels["channels"])
                else:
                    # Assume top-level keys are channels
                    channels.update(legacy_channels)
                print(f"📥 Loaded {len(channels)} channels from legacy channels.toml")
            except Exception as e:
                print(f"⚠️ Could not load legacy channels.toml: {e}")

        # Load from environment variables
        if "env_channels" in analysis:
            env_channels = analysis["env_channels"]
            for key, value in env_channels.items():
                channel_name = key[8:].lower()  # Remove 'CHANNEL_' prefix
                try:
                    channels[channel_name] = int(value)
                    print(f"📥 Loaded channel {channel_name} from environment")
                except ValueError:
                    print(f"⚠️ Invalid channel ID for {channel_name}: {value}")

        # Load from TELEGRAM_CHANNELS JSON
        if "telegram_channels_json" in analysis:
            json_channels = analysis["telegram_channels_json"]
            channels.update(json_channels)
            print(
                f"📥 Loaded {len(json_channels)} channels from TELEGRAM_CHANNELS JSON"
            )

        # Create new format
        if channels:
            print(f"🔧 Migrating {len(channels)} channels to new format")

            if not dry_run:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                with open(self.new_channels_toml, "w") as f:
                    toml.dump(channels, f)
        else:
            print("⚠️ No channels found to migrate")

        return channels

    def create_environment_config(self, dry_run: bool = False):
        """Create environment-specific configuration."""
        env_config = {
            "development": {
                "logging": {"console_level": "DEBUG", "file_level": "DEBUG"},
                "download": {"max_concurrent": 1, "verify_downloads": True},
                "database": {"shard_threshold_gb": 1.0, "max_shard_size_gb": 5.0},
            },
            "production": {
                "logging": {"console_level": "INFO", "file_level": "WARNING"},
                "download": {"max_concurrent": 4, "verify_downloads": False},
                "database": {
                    "connection_timeout": 60,
                    "pragma_settings": [
                        "journal_mode=WAL",
                        "synchronous=NORMAL",
                        "cache_size=50000",
                        "temp_store=memory",
                        "mmap_size=268435456",
                    ],
                },
            },
            "testing": {
                "paths": {"channels_base": "test_channels", "logs_base": "test_logs"},
                "download": {
                    "max_concurrent": 1,
                    "connection_timeout": 5,
                    "retry_attempts": 1,
                },
                "database": {"shard_threshold_gb": 0.1},
            },
        }

        print("🔧 Creating environment-specific configuration")

        if not dry_run:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.new_environments_toml, "w") as f:
                toml.dump(env_config, f)

        return env_config

    def validate_migration(self) -> bool:
        """Validate the migrated configuration."""
        print("\n🔍 Validating migrated configuration...")

        try:
            # Add config directory to path for imports
            import sys

            sys.path.insert(0, str(self.config_dir))

            from manager import get_config_manager

            config_manager = get_config_manager(self.config_dir)
            app_config = config_manager.get_app_config()
            channels_config = config_manager.get_channels_config()

            print(f"✅ App config loaded: {app_config.name} v{app_config.version}")
            print(f"✅ Environment: {app_config.environment.value}")
            print(f"✅ Channels base: {app_config.paths.channels_base}")

            enabled_channels = channels_config.get_enabled_channels()
            print(f"✅ Channels loaded: {len(enabled_channels)} enabled")

            # Test configuration summary
            summary = config_manager.get_effective_config_summary()
            print(f"\n📋 Configuration Summary:\n{summary}")

            return True
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False

    def run_migration(self, dry_run: bool = False, skip_backup: bool = False) -> bool:
        """Run the complete migration process."""
        print("🚀 Starting configuration migration...\n")

        # Analyze legacy configuration
        analysis = self.analyze_legacy_config()

        print("📊 Migration Analysis:")
        print(f"  Legacy files found: {len(analysis['legacy_files_found'])}")
        for file_path in analysis["legacy_files_found"]:
            print(f"    - {file_path}")

        if analysis["issues"]:
            print(f"  Issues found: {len(analysis['issues'])}")
            for issue in analysis["issues"]:
                print(f"    - {issue}")

        if not analysis["migration_needed"]:
            print(
                "✅ No migration needed - optimal configuration system already in use"
            )
            return True

        # Create backup
        if not skip_backup:
            if not self.create_backup(dry_run):
                print("❌ Backup failed")
                return False

        print(f"\n🔄 {'[DRY RUN] ' if dry_run else ''}Starting migration...")

        # Migrate app configuration
        self.migrate_app_config(analysis.get("legacy_config", {}), dry_run)

        # Migrate channels configuration
        self.migrate_channels_config(analysis, dry_run)

        # Create environment configuration
        self.create_environment_config(dry_run)

        if not dry_run:
            # Validate migration
            if self.validate_migration():
                print("\n🎉 Migration completed successfully!")
                print("\nNext steps:")
                print("1. Review the new configuration files in the config/ directory")
                print(
                    "2. Set TELEGRAM_ENV environment variable (development/production/testing)"
                )
                print("3. Test the application with the new configuration system")
                print("4. Remove legacy config files if everything works correctly")
                return True
            else:
                print("\n❌ Migration validation failed")
                return False
        else:
            print("\n✅ Dry run completed - no files were modified")
            print("Run without --dry-run to perform the actual migration")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy configuration to optimal system"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--backup-dir", type=Path, help="Directory for configuration backups"
    )
    parser.add_argument(
        "--skip-backup", action="store_true", help="Skip creating backups"
    )
    parser.add_argument(
        "--project-root", type=Path, default=".", help="Project root directory"
    )

    args = parser.parse_args()

    migrator = ConfigMigrator(args.project_root, args.backup_dir)

    try:
        success = migrator.run_migration(args.dry_run, args.skip_backup)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
