"""
Channel Cleaner Utility
Normalizes YouTube channel inputs to proper URLs for yt-dlp compatibility
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from rich.console import Console


class ChannelCleaner:
    """
    Cleans and normalizes YouTube channel inputs to proper URLs.
    Converts @handles, channel IDs, and partial URLs to full YouTube URLs.
    """

    def __init__(self, console: Console | None = None):
        """Initialize the ChannelCleaner.

        Args:
            console: Optional Rich console instance for output. Defaults to a new Console().
        """
        self.console = console or Console()

    def normalize_channel(self, channel_input: str) -> str:
        """
        Normalize a single channel input to a proper YouTube URL.

        Args:
            channel_input: Channel input (@handle, URL, channel ID, etc.)

        Returns:
            Normalized YouTube URL
        """
        channel_input = channel_input.strip()

        # Skip empty lines and comments
        if not channel_input or channel_input.startswith("#"):
            return channel_input

        # Already a full YouTube URL
        if channel_input.startswith("https://www.youtube.com/"):
            return channel_input

        # @handle format -> full URL
        if channel_input.startswith("@"):
            return f"https://www.youtube.com/{channel_input}"

        # Channel ID format -> full URL
        if self._is_channel_id(channel_input):
            return f"https://www.youtube.com/channel/{channel_input}"

        # Partial URL format
        if channel_input.startswith(("youtube.com/", "/")):
            return f'https://www.{channel_input.lstrip("/")}'

        # Legacy channel format (without @)
        if self._is_handle_format(channel_input):
            return f"https://www.youtube.com/@{quote(channel_input, safe="")}"

        # Assume it's already a proper format or return as-is
        return channel_input

    def _is_channel_id(self, text: str) -> bool:
        """Check if text looks like a YouTube channel ID.

        Channel IDs are typically 24 characters with UC prefix.

        Args:
            text: Text to check

        Returns:
            True if text matches channel ID pattern, False otherwise
        """
        # Pattern for channel IDs (UC prefix followed by 18-26 chars)
        # Allow flexibility as channel ID lengths can vary
        channel_id_pattern = r"^UC[a-zA-Z0-9_-]{18,26}$"
        return bool(re.match(channel_id_pattern, text))

    def _is_handle_format(self, text: str) -> bool:
        """Check if text looks like a channel handle (without @).

        Args:
            text: Text to check

        Returns:
            True if text matches handle pattern, False otherwise
        """
        # Handles are typically 3-30 chars, alphanumeric with hyphens
        handle_pattern = r"^[a-zA-Z0-9_-]{3,30}$"
        return bool(re.match(handle_pattern, text))

    def clean_channels_file(self, file_path: str, backup: bool = True) -> dict[str, Any]:
        """
        Clean and normalize a channels file.

        Args:
            file_path: Path to channels file
            backup: Whether to create a backup of the original

        Returns:
            Dictionary with cleaning statistics
        """
        if not Path(file_path).exists():
            self.console.print(f"[red]Channels file not found: {file_path}[/red]")
            return {"success": False, "error": "File not found"}

        # Read original file
        try:
            with Path(file_path).open("r", encoding="utf-8") as f:
                original_lines = f.readlines()
        except Exception as e:
            self.console.print(f"[red]Error reading channels file: {e}[/red]")
            return {"success": False, "error": str(e)}

        # Create backup if requested
        if backup:
            backup_path = f"{file_path}.backup"
            try:
                with Path(backup_path).open("w", encoding="utf-8") as f:
                    f.writelines(original_lines)
                self.console.print(f"[green][/green] Created backup: {backup_path}")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")

        # Process and normalize channels
        normalized_lines = []
        normalized_count = 0
        duplicates_removed = 0

        seen_channels: set[str] = set()

        for line in original_lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                normalized_lines.append(line)
                continue

            # Keep comments as-is
            if stripped.startswith("#"):
                normalized_lines.append(line)
                continue

            # Normalize channel
            normalized = self.normalize_channel(stripped)

            # Remove duplicates
            if normalized not in seen_channels:
                seen_channels.add(normalized)
                if normalized != stripped:
                    normalized_count += 1
                    self.console.print(f"[blue]->[/blue] {stripped} -> {normalized}")

                # Preserve original line endings
                if line.endswith("\n"):
                    normalized_lines.append(normalized + "\n")
                else:
                    normalized_lines.append(normalized)
            else:
                duplicates_removed += 1
                self.console.print(f"[yellow]X[/yellow] Removed duplicate: {normalized}")

        # Write cleaned file
        try:
            with Path(file_path).open("w", encoding="utf-8") as f:
                f.writelines(normalized_lines)
        except Exception as e:
            self.console.print(f"[red]Error writing cleaned file: {e}[/red]")
            return {"success": False, "error": str(e)}

        # Count channels
        channel_count = len([line for line in normalized_lines
                           if line.strip() and not line.strip().startswith("#")])

        return {
            "success": True,
            "normalized_count": normalized_count,
            "duplicates_removed": duplicates_removed,
            "total_channels": channel_count,
            "total_lines": len(normalized_lines)
        }

    def validate_channels(self, file_path: str) -> list[str]:
        """
        Validate channels in a file and return list of invalid ones.

        Args:
            file_path: Path to channels file

        Returns:
            List of invalid channel entries
        """
        if not Path(file_path).exists():
            return [f"File not found: {file_path}"]

        invalid_channels = []

        try:
            with Path(file_path).open("r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                if not stripped or stripped.startswith("#"):
                    continue

                # Basic validation
                if not (stripped.startswith(("https://www.youtube.com/", "@", "#"))) and not self._is_channel_id(stripped):
                    invalid_channels.append(f"Line {line_num}: {stripped}")

        except Exception as e:
            invalid_channels.append(f"Error reading file: {e}")

        return invalid_channels

    def analyze_channels(self, channels: list[str]) -> dict[str, Any]:
        """
        Analyze a channel list and provide statistics.

        Args:
            channels: List of channel entries

        Returns:
            Dictionary with analysis statistics
        """
        total_entries = len(channels)
        valid_channels = []
        invalid_channels = []
        duplicates = []
        handles = []
        urls = []
        channel_ids = []
        plain_names = []

        seen = set()
        for channel in channels:
            channel = channel.strip()
            if not channel or channel.startswith("#"):
                continue

            # Check for duplicates
            if channel in seen:
                duplicates.append(channel)
                continue
            seen.add(channel)

            # Categorize channel types
            if channel.startswith("@"):
                handles.append(channel)
            elif channel.startswith("https://www.youtube.com/"):
                urls.append(channel)
            elif self._is_channel_id(channel):
                channel_ids.append(channel)
            else:
                plain_names.append(channel)

            # Basic validation
            if (channel.startswith(("https://www.youtube.com/", "@")) or self._is_channel_id(channel)):
                valid_channels.append(channel)
            else:
                invalid_channels.append(channel)

        return {
            "total_entries": total_entries,
            "valid_channels": len(valid_channels),
            "invalid_channels": len(invalid_channels),
            "duplicates": len(duplicates),
            "handles": len(handles),
            "urls": len(urls),
            "channel_ids": len(channel_ids),
            "plain_names": len(plain_names),
            "invalid_channel_list": invalid_channels,
            "duplicate_list": duplicates
        }

    def display_analysis(self, analysis: dict[str, Any]) -> None:
        """
        Display channel analysis results.

        Args:
            analysis: Analysis dictionary from analyze_channels
        """
        self.console.print("\n[bold] Channel Analysis:[/bold]")
        self.console.print(f"  -Total entries: {analysis['total_entries']}")
        self.console.print(f"  -Valid channels: {analysis['valid_channels']}")
        self.console.print(f"  -Invalid channels: {analysis['invalid_channels']}")
        self.console.print(f"  -Duplicates: {analysis['duplicates']}")

        self.console.print("\n[bold]📋 Channel Types:[/bold]")
        self.console.print(f"  -@handles: {analysis['handles']}")
        self.console.print(f"  -Full URLs: {analysis['urls']}")
        self.console.print(f"  -Channel IDs: {analysis['channel_ids']}")
        self.console.print(f"  -Plain names: {analysis['plain_names']}")

        if analysis["invalid_channels"] > 0:
            self.console.print("\n[yellow]WARNING:  Invalid channels found:[/yellow]")
            for invalid in analysis["invalid_channel_list"][:5]:
                self.console.print(f"    -{invalid}")
            if len(analysis["invalid_channel_list"]) > 5:
                self.console.print(f"    ... and {len(analysis['invalid_channel_list']) - 5} more")

        if analysis["duplicates"] > 0:
            self.console.print("\n[yellow]WARNING:  Duplicates found:[/yellow]")
            for duplicate in analysis["duplicate_list"][:5]:
                self.console.print(f"    -{duplicate}")
            if len(analysis["duplicate_list"]) > 5:
                self.console.print(f"    ... and {len(analysis['duplicate_list']) - 5} more")

    def clean_channels(self, channels: list[str], prefer_handles: bool = True, convert_names: bool = True, quiet_mode: bool = False) -> tuple[list[str], dict[str, Any]]:
        """
        Clean and standardize a channel list.
        quiet_mode: Suppress individual removal/change messages
        Args:
            channels: List of channel entries
            prefer_handles: Convert URLs to @handles when possible
            convert_names: Convert plain names to @handles

        Returns:
            Tuple of (cleaned_channels, stats)
        """
        cleaned_channels = []
        seen = set()
        stats = {
            "original_count": len(channels),
            "cleaned_count": 0,
            "duplicates_removed": 0,
            "invalid_removed": 0,
            "handles_converted": 0,
            "names_converted": 0
        }

        import sys
        total = len(channels)
        show_progress = total > 100  # Only show progress for large lists

        for i, channel in enumerate(channels):
            channel = channel.strip()

            # Skip empty lines and comments
            if not channel or channel.startswith("#"):
                cleaned_channels.append(channel)
                continue

            # Show progress for large lists
            if show_progress and i % 100 == 0 and i > 0:
                sys.stderr.write(f" Cleaning channels: {i}/{total}...\r")
                sys.stderr.flush()

            # Normalize channel
            normalized = self.normalize_channel(channel)

            # Check for duplicates
            if normalized in seen:
                stats["duplicates_removed"] += 1
                continue
            seen.add(normalized)

            # Apply format preferences
            final_channel = normalized
            if prefer_handles and normalized.startswith("https://www.youtube.com/@"):
                # Convert URL to @handle
                handle = normalized.split("/")[-1]
                # handle already includes @, so don't add another one
                final_channel = handle
                stats["handles_converted"] += 1
            elif convert_names and not (normalized.startswith(("@", "https://"))):
                # Convert plain name to @handle
                final_channel = f"@{normalized}"
                stats["names_converted"] += 1

            # Basic validation
            if (final_channel.startswith(("@", "https://www.youtube.com/")) or self._is_channel_id(final_channel)):
                cleaned_channels.append(final_channel)
                if channel != final_channel:
                    stats["cleaned_count"] += 1
                    # Only print details for small lists or first 10 changes
                    if not quiet_mode and (total <= 50 or stats["cleaned_count"] <= 10):
                        self.console.print(f"[blue]->[/blue] {channel} -> {final_channel}")
            else:
                stats["invalid_removed"] += 1
                # Only print details for small lists or first 10 removals
                if not quiet_mode and (total <= 50 or stats["invalid_removed"] <= 10):
                    self.console.print(f"[yellow]X[/yellow] Removed invalid: {channel}")

        # Clear progress line
        if show_progress:
            sys.stderr.write(" " * 50 + "\r")
            sys.stderr.flush()

        stats["final_count"] = len([c for c in cleaned_channels if c.strip() and not c.strip().startswith("#")])

        return cleaned_channels, stats

    def display_cleanup_results(self, cleaned_channels: list[str], stats: dict[str, Any]) -> None:
        """
        Display cleaning results and statistics.

        Args:
            cleaned_channels: List of cleaned channels
            stats: Statistics dictionary from clean_channels
        """
        self.console.print("\n[green] Cleaning Complete![/green]")
        self.console.print(f"  -Original entries: {stats['original_count']}")
        self.console.print(f"  -Channels cleaned: {stats['cleaned_count']}")
        self.console.print(f"  -Duplicates removed: {stats['duplicates_removed']}")
        self.console.print(f"  -Invalid removed: {stats['invalid_removed']}")
        self.console.print(f"  -Handles converted: {stats['handles_converted']}")
        self.console.print(f"  -Names converted: {stats['names_converted']}")
        self.console.print(f"  -Final channels: {stats['final_count']}")

        # Show note if details were suppressed for large lists
        if stats["original_count"] > 50:
            if stats["cleaned_count"] > 10:
                self.console.print(f"  [dim](First 10 changes shown - {stats['cleaned_count'] - 10} more omitted)[/dim]")
            if stats["invalid_removed"] > 10:
                self.console.print(f"  [dim](First 10 removals shown - {stats['invalid_removed'] - 10} more omitted)[/dim]")


    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file for cache invalidation.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(Path(file_path).read_bytes()).hexdigest()

    def clean_channels_file_cached(
        self,
        file_path: str,
        prefer_handles: bool = True,
        convert_names: bool = True,
        cache_dir: str = "data/cache",
        force: bool = False,
        quiet_mode: bool = False,
    ) -> tuple[list[str], dict[str, Any]]:
        """Clean channels from file with automatic caching.

        Only re-cleans if:
        1. Cache doesn't exist, OR
        2. File hash changed, OR
        3. force=True

        Args:
            file_path: Path to channels file
            prefer_handles: Convert URLs to @handles when possible
            convert_names: Convert plain names to @handles
            cache_dir: Directory for cache storage
            force: Force re-cleaning even if cache exists
            quiet_mode: Suppress individual messages (auto-enabled on cache hit)

        Returns:
            Tuple of (cleaned_channels, stats)
        """
        file_path_obj = Path(file_path)
        cache_dir_obj = Path(cache_dir)

        # Create cache directory if needed
        cache_dir_obj.mkdir(parents=True, exist_ok=True)

        # Generate cache and hash file paths
        cache_name = f"{file_path_obj.stem}_cleaned.txt"
        hash_name = f"{file_path_obj.stem}_hash.txt"
        cache_path = cache_dir_obj / cache_name
        hash_path = cache_dir_obj / hash_name

        # Get current file hash
        try:
            current_hash = self._get_file_hash(file_path)
        except Exception:
            # If we can't read the file, just clean normally
            channels = file_path_obj.read_text(encoding="utf-8").splitlines()
            return self.clean_channels(channels, prefer_handles, convert_names)

        # Check if we can use cached result
        if not force and cache_path.exists() and hash_path.exists():
            try:
                cached_hash = hash_path.read_text().strip()
                if cached_hash == current_hash:
                    # Cache hit - load cleaned channels
                    cleaned_channels = cache_path.read_text(encoding="utf-8").splitlines()
                    # Try to load cached stats
                    stats_path = cache_dir_obj / f"{file_path_obj.stem}_stats.json"
                    if stats_path.exists():
                        import json
                        stats = json.loads(stats_path.read_text(encoding="utf-8"))
                        stats["cache_hit"] = True
                        stats["cache_source"] = str(cache_path)
                    else:
                        # Fallback for old cache format
                        stats = {
                            "original_count": len(cleaned_channels),
                            "cleaned_count": 0,
                            "duplicates_removed": 0,
                            "invalid_removed": 0,
                            "handles_converted": 0,
                            "names_converted": 0,
                            "final_count": len([c for c in cleaned_channels if c.strip() and not c.strip().startswith("#")]),
                            "cache_hit": True,
                            "cache_source": str(cache_path)
                        }
                    return cleaned_channels, stats
            except Exception:
                # Cache read failed, continue to normal cleaning
                pass

        # Cache miss - do actual cleaning
        channels = file_path_obj.read_text(encoding="utf-8").splitlines()
        cleaned_channels, stats = self.clean_channels(channels, prefer_handles, convert_names, quiet_mode=quiet_mode)
        stats["cache_hit"] = False

        # Write to cache (using join to avoid string issues)
        try:
            cache_content = "\n".join(cleaned_channels)
            cache_path.write_text(cache_content, encoding="utf-8")
            # Also cache stats for consistent reporting
            stats_path = cache_dir_obj / f"{file_path_obj.stem}_stats.json"
            import json
            stats_path.write_text(json.dumps(stats), encoding="utf-8")
            hash_path.write_text(current_hash, encoding="utf-8")
        except Exception:
            # Cache write failed - non-fatal
            pass

        return cleaned_channels, stats

    def generate_clean_file(self, channels: list[str], output_path: str, include_stats: bool = True) -> None:
        """
        Write cleaned channels to a file.

        Args:
            channels: List of cleaned channels
            output_path: Path to output file
            include_stats: Whether to include statistics header
        """
        try:
            with Path(output_path).open("w", encoding="utf-8") as f:
                if include_stats:
                    f.write("# yt-fts Cleaned Channel List\n")
                    f.write(f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total channels: {len([c for c in channels if c.strip() and not c.strip().startswith('#')])}\n")
                    f.write("#\n")

                for channel in channels:
                    f.write(channel + "\n")

        except Exception as e:
            self.console.print(f"[red]Error writing cleaned file: {e}[/red]")


def auto_clean_channels(file_path: str = "channels.txt", console: Console | None = None) -> bool:
    """
    Convenience function to auto-clean channels file.

    Args:
        file_path: Path to channels file (default: channels.txt)
        console: Console instance for output

    Returns:
        True if successful, False otherwise
    """
    cleaner = ChannelCleaner(console)

    # Check if file exists
    if not Path(file_path).exists():
        if console:
            console.print(f"[yellow]Channels file not found: {file_path}[/yellow]")
        return False

    # Clean the file
    result = cleaner.clean_channels_file(file_path)

    if result["success"]:
        if console:
            console.print("\n[green] Channels file cleaned successfully![/green]")
            console.print(f"   Total channels: {result['total_channels']}")
            console.print(f"   Normalized: {result['normalized_count']}")
            console.print(f"   Duplicates removed: {result['duplicates_removed']}")

            # Validate cleaned channels
            invalid = cleaner.validate_channels(file_path)
            if invalid:
                console.print(f"\n[yellow]WARNING:  Found {len(invalid)} potentially invalid channels:[/yellow]")
                for invalid_channel in invalid[:5]:  # Show first 5
                    console.print(f"   -{invalid_channel}")
                if len(invalid) > 5:
                    console.print(f"   ... and {len(invalid) - 5} more")
            else:
                console.print("\n[green] All channels appear to be valid YouTube URLs[/green]")
        return True
    if console:
        console.print(f"[red] Failed to clean channels file: {result['error']}[/red]")
    return False


def create_channel_list_from_input() -> list[str]:
    """
    Create the built-in AI/automation focused channel list.

    Returns:
        List[str]: List of AI and automation YouTube channel URLs
    """
    # AI/ML Research & Education
    return [
        "https://www.youtube.com/@TwoMinutePapers",
        "https://www.youtube.com/@OpenAI",
        "https://www.youtube.com/@AnthropicAI",
        "https://www.youtube.com/@HuggingFace",
        "https://www.youtube.com/@GoogleAI",
        "https://www.youtube.com/@DeepMind",
        "https://www.youtube.com/@LexFridman",
        "https://www.youtube.com/@YannicKilcher",
        "https://www.youtube.com/@AIExplained",
        "https://www.youtube.com/@RobertMilesAI",
        "https://www.youtube.com/@Computerphile",
        "https://www.youtube.com/@3Blue1Brown",
        "https://www.youtube.com/@StatQuest",
        "https://www.youtube.com/@SirajRaval",
        "https://www.youtube.com/@KrishNaik",
        "https://www.youtube.com/@MachineLearningTV",
        "https://www.youtube.com/@DataProfessor",
        "https://www.youtube.com/@TechWithTim",
        "https://www.youtube.com/@freeCodeCamp",
        "https://www.youtube.com/@ProgrammingKnowledge",
        "https://www.youtube.com/@CoreySchafer",
        "https://www.youtube.com/@sentdex",
        "https://www.youtube.com/@JeffHawkinsNumenta",
        "https://www.youtube.com/@GaryMarcus",
        "https://www.youtube.com/@AndrewNg",
        "https://www.youtube.com/@Fei-FeiLi",
        "https://www.youtube.com/@YannLeCun",
        "https://www.youtube.com/@GeoffreyHinton",
        "https://www.youtube.com/@DemisHassabis",
        "https://www.youtube.com/@DaphneKoller",
        "https://www.youtube.com/@MichaelIJordan",
        "https://www.youtube.com/@YoshuaBengio",
        "https://www.youtube.com/@JurgenSchmidhuber",
        "https://www.youtube.com/@PieterAbbeel",
        "https://www.youtube.com/@AndrejKarpathy",
        "https://www.youtube.com/@IanGoodfellow",
        "https://www.youtube.com/@NandoDF",
        "https://www.youtube.com/@DavidSilverRL",
        "https://www.youtube.com/@CarlVondrick",
        "https://www.youtube.com/@DevonBarrett",
        "https://www.youtube.com/@TimnitGebru",
        "https://www.youtube.com/@JoyBuolamwini",
        "https://www.youtube.com/@KateCrawford",
        "https://www.youtube.com/@MilesBrundage",
        "https://www.youtube.com/@AISafetyResearch",
        "https://www.youtube.com/@FutureOfLifeInstitute",
        "https://www.youtube.com/@MachineLearningStreet",
        "https://www.youtube.com/@MLStreetTalk",
        "https://www.youtube.com/@AIforGood",
        "https://www.youtube.com/@DeepLearningAI",
        "https://www.youtube.com/@AIAlignmentForum",
        "https://www.youtube.com/@MachineLearningMastery",
        "https://www.youtube.com/@Kaggle",
        "https://www.youtube.com/@DataCamp",
        "https://www.youtube.com/@Coursera",
        "https://www.youtube.com/@edX",
        "https://www.youtube.com/@MITOpenCourseWare",
        "https://www.youtube.com/@StanfordOnline",
        "https://www.youtube.com/@UCBerkeley",
        "https://www.youtube.com/@CarnegieMellonU",
        "https://www.youtube.com/@Caltech",
        "https://www.youtube.com/@Harvard",
        "https://www.youtube.com/@OxfordUniversity",
        "https://www.youtube.com/@CambridgeUniversity",
        "https://www.youtube.com/@ETHZurich",
        "https://www.youtube.com/@EPFL",
        "https://www.youtube.com/@INRIA",
        "https://www.youtube.com/@MicrosoftResearch",
        "https://www.youtube.com/@FAIR",
        "https://www.youtube.com/@IntelLabs",
        "https://www.youtube.com/@IBMResearch",
        "https://www.youtube.com/@GoogleResearch",
        "https://www.youtube.com/@AmazonScience",
        "https://www.youtube.com/@AppleMachineLearning",
        "https://www.youtube.com/@NVIDIA",
        "https://www.youtube.com/@AMD",
        "https://www.youtube.com/@Intel",
        "https://www.youtube.com/@TeslaAI",
        "https://www.youtube.com/@BostonDynamics",
        "https://www.youtube.com/@OpenRobotics",
        "https://www.youtube.com/@Waymo",
        "https://www.youtube.com/@Cruise",
        "https://www.youtube.com/@UberAI",
        "https://www.youtube.com/@LyftLevel5",
        "https://www.youtube.com/@AuroraInnovation",
        "https://www.youtube.com/@ArgoAI",
        "https://www.youtube.com/@Nuro",
        "https://www.youtube.com/@Zoox",
        "https://www.youtube.com/@Motional",
        "https://www.youtube.com/@PonyAI",
        "https://www.youtube.com/@WeRide",
        "https://www.youtube.com/@BaiduApollo",
        "https://www.youtube.com/@HuaweiTechnologies",
        "https://www.youtube.com/@TencentAI",
        "https://www.youtube.com/@Alibaba DAMO Academy",
        "https://www.youtube.com/@ByteDanceAI",
        "https://www.youtube.com/@MeituanAI",
        "https://www.youtube.com/@DidiChuxingAI",
        "https://www.youtube.com/@XiaomengAI",
        "https://www.youtube.com/@SenseTime",
        "https://www.youtube.com/@Megvii",
        "https://www.youtube.com/@YituTech",
        "https://www.youtube.com/@CloudWalk",
        "https://www.youtube.com/@HikvisionAI",
        "https://www.youtube.com/@DahuaAI",
        "https://www.youtube.com/@iFlytek",
        "https://www.youtube.com/@BaiduAI",
        "https://www.youtube.com/@TencentAILab",
        "https://www.youtube.com/@HuaweiNoahEulerLab",
        "https://www.youtube.com/@HuaweiMindSpore",
        "https://www.youtube.com/@AlibabaCloudAI",
        "https://www.youtube.com/@AlibabaPAI",
        "https://www.youtube.com/@TencentYoutuLab",
        "https://www.youtube.com/@ByteDanceAILab"
    ]

