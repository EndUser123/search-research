"""
Status Display Utility for yt-fts
Shows comprehensive status information including cookies, user info, and system status
"""

import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class StatusDisplay:
    """
    Comprehensive status display system for yt-fts.
    Shows cookies status, user info, database statistics, and system configuration.
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.config_path = Path(os.getenv("APPDATA", "")) / "yt-fts"

    def get_user_info(self) -> dict[str, Any]:
        """Get current user information."""
        import getpass

        user_info = {
            "username": getpass.getuser(),
            "os": sys.platform,
            "python_version": sys.version.split()[0],
            "working_dir": str(Path.cwd()),
            "appdata_dir": self.config_path
        }

        # Add system-specific info
        if sys.platform == "win32":
            import platform
            user_info.update({
                "windows_version": platform.version(),
                "machine": platform.machine()
            })

        return user_info

    def get_database_status(self) -> dict[str, Any]:
        """Get database statistics and status."""
        from yt_fts.utils.config import get_db_path

        db_path = get_db_path()
        status = {
            "database_path": db_path,
            "database_exists": Path(db_path).exists(),
            "channels": 0,
            "videos": 0,
            "subtitles": 0,
            "last_modified": None,
            "file_size": 0
        }

        if Path(db_path).exists():
            try:
                # Get file info
                stat = os.stat(db_path)
                status["last_modified"] = datetime.fromtimestamp(stat.st_mtime)
                status["file_size"] = stat.st_size

                # Get database content stats
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    # Get count of channels with recent activity
                    cursor.execute(
                        "SELECT COUNT(DISTINCT channel_id) FROM Videos"
                    )
                    recent_channels = cursor.fetchone()[0]

                status["recent_channels"] = recent_channels

            except Exception as e:
                status["error"] = str(e)

        return status

    def get_cookie_status(self) -> dict[str, Any]:
        """Get cookie extraction status and information."""
        cookie_status = {
            "cookies_available": False,
            "cookie_file": None,
            "cookie_count": 0,
            "browser_used": None,
            "last_extraction": None,
            "cookies_working": False,
            "needs_refresh": False
        }

        # Check for cookie files in temp directory
        temp_dir = tempfile.gettempdir()
        cookie_files = [f for f in os.listdir(temp_dir) if f.startswith("yt_cookies_")]

        if cookie_files:
            # Get most recent cookie file
            cookie_files.sort(reverse=True)
            latest_cookie = Path(temp_dir) / cookie_files[0]

            cookie_status["cookie_file"] = latest_cookie
            cookie_status["cookies_available"] = True
            cookie_status["last_extraction"] = datetime.fromtimestamp(
                Path(latest_cookie).stat().st_mtime
            )

            # Check if cookies need refresh (older than 24 hours)
            time_diff = datetime.now(timezone.utc) - cookie_status["last_extraction"]
            if time_diff.total_seconds() > 24 * 3600:  # 24 hours
                cookie_status["needs_refresh"] = True

            # Extract browser from filename and count cookies
            try:
                with Path(latest_cookie).open("r") as f:
                    content = f.read()
                    # Count non-comment lines
                    cookie_count = len([line for line in content.split("\n")
                                       if line.strip() and not line.startswith("#")])
                    cookie_status["cookie_count"] = cookie_count - 1  # Subtract header line

                    # Extract browser name from filename (more reliable than content heuristics)
                    filename = Path(latest_cookie).name
                    if "yt_cookies_" in filename:
                        # Extract browser from yt_cookies_browser_name_timestamp.txt format
                        browser_part = filename.replace("yt_cookies_", "").split("_")[0]
                        if browser_part and browser_part in ["chrome", "firefox", "edge", "safari"]:
                            cookie_status["browser_used"] = browser_part.capitalize()
                        # Fallback to content heuristics if filename parsing fails
                        elif "__Secure-3PAPISID" in content or "SAPISID" in content:
                            cookie_status["browser_used"] = "Chrome"
                        elif "__Secure-ROLLOUT_TOKEN" in content:
                            cookie_status["browser_used"] = "Firefox"
                        else:
                            cookie_status["browser_used"] = "Unknown"

            except Exception:
                cookie_status["browser_used"] = "Unknown"

            # Test if cookies work
            try:
                import yt_dlp
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "cookiefile": latest_cookie,
                    "extract_flat": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(
                        "https://www.youtube.com/@TwoMinutePapers",
                        download=False,
                        process=False
                    )

                    if result and "title" in result:
                        cookie_status["cookies_working"] = True

            except Exception:
                pass

        return cookie_status

    def get_channels_status(self, active_file: str | None = None) -> dict[str, Any]:
        """
        Get channels file status and information.

        Args:
            active_file: Currently active channel file (optional, for batch operations)
        """
        channels_status = {
            "database_file": "channels.txt",
            "active_file": active_file,
            "database_exists": False,
            "active_exists": False,
            "database_channels": 0,
            "active_channels": 0,
            "clean_channels": 0,
            "handle_channels": 0,
            "url_channels": 0,
            "last_cleaned": None
        }

        # Check main database file (channels.txt)
        if Path("channels.txt").exists():
            channels_status["database_exists"] = True
            channels_status["database_size"] = Path("channels.txt").stat().st_size

            try:
                with Path("channels.txt").open("r", encoding="utf-8") as f:
                    lines = f.readlines()

                channels_status["database_channels"] = len([
                    line for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ])

                channels_status["clean_channels"] = len([
                    line for line in lines
                    if line.strip().startswith("https://") and not line.strip().startswith("#")
                ])

                channels_status["handle_channels"] = len([
                    line for line in lines
                    if line.strip().startswith("@") and not line.strip().startswith("#")
                ])

            except Exception as e:
                channels_status["error"] = str(e)

        # Check active file if specified
        if active_file and Path(active_file).exists():
            channels_status["active_exists"] = True
            channels_status["active_size"] = Path(active_file).stat().st_size

            try:
                with Path(active_file).open("r", encoding="utf-8") as f:
                    lines = f.readlines()

                channels_status["active_channels"] = len([
                    line for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ])

            except Exception as e:
                channels_status["active_error"] = str(e)

        return channels_status

    def get_system_status(self) -> dict[str, Any]:
        """Get system configuration and status."""
        system_status = {
            "yt_dlp_available": False,
            "chromadb_removed": True,
            "playwright_available": False,
            "memory_usage": 0,
            "disk_space": 0
        }

        # Check yt-dlp
        try:
            import yt_dlp
            system_status["yt_dlp_available"] = True
            system_status["yt_dlp_version"] = getattr(yt_dlp, "__version__", "unknown")
        except ImportError:
            pass

        # Check playwright
        try:
            from playwright.sync_api import sync_playwright
            system_status["playwright_available"] = True
        except ImportError:
            pass

        # Check chromadb removal
        try:
            import chromadb
            system_status["chromadb_removed"] = False
        except ImportError:
            system_status["chromadb_removed"] = True

        # Memory usage (basic)
        try:
            import psutil
            process = psutil.Process()
            system_status["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass

        # Disk space for project
        try:
            import shutil
            _total, _used, free = shutil.disk_usage(".")
            system_status["disk_space"] = free / 1024 / 1024 / 1024  # GB
        except (OSError, AttributeError):
            pass

        return system_status

    def display_status_line(self) -> str:
        """Generate a compact status line for CLI output."""
        status_parts = []

        # User info
        user_info = self.get_user_info()
        status_parts.append(f"👤 {user_info['username']}")

        # Database status
        db_status = self.get_database_status()
        if db_status["database_exists"]:
            status_parts.append(f"📊 {db_status['channels']}ch/{db_status['videos']}v/{db_status['subtitles']}s")
        else:
            status_parts.append("📊 No DB")

        # Cookie status
        cookie_status = self.get_cookie_status()
        if cookie_status["cookies_available"] and cookie_status["cookies_working"]:
            status_parts.append(f"🍪 {cookie_status['browser_used']} Cookies")
        else:
            status_parts.append("🍪 No Cookies")

        # Channels status
        channels_status = self.get_channels_status()
        if channels_status["database_exists"]:
            status_parts.append(f"📺 {channels_status['database_channels']} Channels")
        else:
            status_parts.append("📺 No Channels")

        return " | ".join(status_parts)

    def display_comprehensive_status(self, show_config: bool = False, active_file: str | None = None) -> None:
        """Display a focused status panel with essential information only."""
        # Gather essential status information
        db_status = self.get_database_status()
        cookie_status = self.get_cookie_status()
        channels_status = self.get_channels_status(active_file)
        system_status = self.get_system_status()

        # Create status table with better column widths
        status_table = Table(show_header=True, header_style="bold blue", box=None)
        status_table.add_column("Category", style="cyan", width=12)
        status_table.add_column("Status", style="green", width=12)
        status_table.add_column("Details", style="yellow")

        # Database Status - Most important info
        if db_status["database_exists"]:
            db_text = f"{db_status['channels']} channels • {db_status['videos']} videos • {db_status['subtitles']:,} subtitles"
            if db_status.get("last_modified"):
                db_text += f"\nUpdated: {db_status['last_modified'].strftime('%Y-%m-%d %H:%M')}"
            status_table.add_row("📊 Database", "✅ Ready", db_text)
        else:
            status_table.add_row("📊 Database", "❌ Empty", "Run 'download' or 'batch-download' to create database")

        # Cookie Status - Critical for performance
        if cookie_status["cookies_available"] and cookie_status["cookies_working"]:
            cookie_text = f"{cookie_status['browser_used']} cookies working"
            if cookie_status["needs_refresh"]:
                cookie_text += "\n⚠️ Old (refresh recommended)"
            status_table.add_row("🍪 Cookies", "✅ Active", cookie_text)
        elif cookie_status["cookies_available"]:
            cookie_text = f"{cookie_status['browser_used']} cookies untested"
            status_table.add_row("🍪 Cookies", "⚠️ Test", cookie_text)
        else:
            cookie_text = "Extract cookies for better performance"
            status_table.add_row("🍪 Cookies", "❌ Missing", cookie_text)

        # Channels Status - Shows both database and active file
        if channels_status["database_exists"]:
            if active_file and channels_status["active_exists"]:
                # Show both database and active file
                channels_text = f"Database: {channels_status['database_channels']} channels"
                channels_text += f"\nProcessing: {channels_status['active_file']} ({channels_status['active_channels']} channels)"
                status_table.add_row("📺 Channels", "✅ Active", channels_text)
            else:
                # Show only database
                channels_text = f"{channels_status['database_channels']} channels ready"
                if channels_status["handle_channels"] > 0:
                    channels_text += f"\n⚠️ {channels_status['handle_channels']} @handles need conversion"
                status_table.add_row("📺 Channels", "✅ Ready", channels_text)
        else:
            channels_text = "Use 'preset-channels' or create channels.txt"
            status_table.add_row("📺 Channels", "❌ Missing", channels_text)

        # Only show system config if requested
        if show_config:
            # Essential system info only
            system_text = []
            if system_status["yt_dlp_available"]:
                system_text.append(f"✅ yt-dlp {system_status.get('yt_dlp_version', 'unknown')}")
            else:
                system_text.append("❌ yt-dlp missing")

            if system_status.get("disk_space"):
                system_text.append(f"💾 {system_status['disk_space']:.1f}GB free")

            status_table.add_row("⚙️ System", "✅ Ready", "\n".join(system_text))

        # Display the table with focused subtitle
        subtitle = "Essential system status" if not show_config else "Complete system status including configuration"
        self.console.print(Panel(
            status_table,
            title="[bold green]🚀 yt-fts Status[/bold green]",
            subtitle=subtitle,
            border_style="blue"
        ))

    def display_minimal_status(self) -> None:
        """Display a minimal status line."""
        status_line = self.display_status_line()
        self.console.print(f"[dim]{status_line}[/dim]")

    def display_download_status(self, operation: str = "Download") -> None:
        """Display status specifically for download operations."""
        self.display_minimal_status()

        # Additional download-specific info
        cookie_status = self.get_cookie_status()
        if not cookie_status["cookies_available"] or not cookie_status["cookies_working"]:
            self.console.print(
                "[yellow]💡 Tip: Extract browser cookies for better performance:[/yellow]")
            self.console.print(
                "[yellow]   python -c \"from yt_fts.cookie_extractor import auto_extract_cookies; auto_extract_cookies('firefox')\"[/yellow]"
            )
        else:
            self.console.print(
                f"[green]✅ Using {cookie_status['browser_used']} cookies for optimal performance[/green]"
            )


def show_status(detailed: bool = False, config: bool = False, active_file: str | None = None, console: Console | None = None) -> None:
    """
    Convenience function to display status.

    Args:
        detailed: Show comprehensive status if True, minimal if False
        config: Include system configuration details (yt-dlp version, disk space, etc.)
        active_file: Currently active channel file for batch operations
        console: Console instance for output
    """
    status = StatusDisplay(console)

    if detailed:
        status.display_comprehensive_status(show_config=config, active_file=active_file)
    else:
        status.display_minimal_status()
