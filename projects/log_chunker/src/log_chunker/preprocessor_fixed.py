"""Advanced log preprocessing with deduplication."""

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from logging_config import get_logger

try:
    from fuzzywuzzy import fuzz

    HAS_FUZZYWUZZY = True
except ImportError:
    HAS_FUZZYWUZZY = False
    get_logger(__name__).warning(
        "fuzzywuzzy not found. Advanced fuzzy deduplication will be disabled."
    )

try:
    from langdetect import DetectorFactory, LangDetectException, detect

    DetectorFactory.seed = 0  # Ensures consistent results across runs
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    get_logger(__name__).warning(
        "langdetect not found. Language detection will be disabled."
    )

from config import ChunkingConfig
from data_models import LogEntry
from rich.console import Console  # Import Console for passing it down
from rich.progress import Progress

logger = get_logger(__name__)


class Preprocessor:
    """Advanced log preprocessing with ML capabilities"""

    def __init__(self, config: ChunkingConfig, console: Console):
        self.config = config
        self.console = console  # Store console instance
        self.language_cache = {}

        # Load patterns from config
        self.log_parsing_patterns = [re.compile(p) for p in config.log_parsing_patterns]
        self.advanced_detection_patterns = {}
        for category, patterns_list in config.advanced_detection_patterns.items():
            self.advanced_detection_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns_list
            ]

    def detect_language(self, text: str) -> str:
        """Detect programming language or natural language"""
        if text in self.language_cache:
            return self.language_cache[text]

        # Programming language indicators
        if any(
            keyword in text.lower()
            for keyword in ["def ", "class ", "import ", "from "]
        ):
            lang = "python"
        elif any(
            keyword in text.lower()
            for keyword in ["function", "var ", "const ", "let "]
        ):
            lang = "javascript"
        elif any(
            keyword in text.lower()
            for keyword in ["public class", "private ", "package "]
        ):
            lang = "java"
        elif any(
            keyword in text.lower() for keyword in ["#include", "int main", "printf"]
        ):
            lang = "c"
        else:
            try:
                if HAS_LANGDETECT and len(text) > 20:
                    lang = detect(text)
                else:
                    lang = "unknown"
            except Exception:
                lang = "unknown"

        self.language_cache[text] = lang
        return lang

    def advanced_pattern_detection(self, line: str) -> list[str]:
        """Enhanced pattern detection using configurable patterns."""
        detected = []
        for pattern_type, compiled_patterns in self.advanced_detection_patterns.items():
            for pattern_re in compiled_patterns:
                if pattern_re.search(line):
                    detected.append(pattern_type)
                    break  # Only need one match per category

        # Add language detection
        lang = self.detect_language(line)
        if lang != "unknown":
            detected.append(f"lang_{lang}")

        return detected

    def create_pattern(self, message: str, logger: str, level: str) -> str:
        """Create normalized pattern for deduplication"""
        normalized = message

        patterns_to_normalize = [
            (r"\b\d+\.\d+\.\d+\.\d+\b", "[IP]"),
            (
                r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
                "[UUID]",
            ),
            (
                r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.,]\d{3}[Z]?\b",
                "[TIMESTAMP]",
            ),
            (r"\b\d+\.\d+\b", "[FLOAT]"),
            (r"\b\d+\b", "[NUMBER]"),
            (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "[EMAIL]"),
            (r"\bhttps?://[^\s]+\b", "[URL]"),
            (r"\b/[^\s]*\b", "[PATH]"),
            (r"\b[A-Z0-9]{10,}\b", "[TOKEN]"),
        ]

        for pattern, replacement in patterns_to_normalize:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        return f"{level}:{normalized}"

    def parse_log_line(self, line: str) -> LogEntry | None:
        """Enhanced log line parsing"""
        line = line.strip()
        if not line:
            return None

        for pattern_re in self.log_parsing_patterns:
            match = pattern_re.match(line)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    timestamp, _, level, message = groups
                    level = level.upper()
                elif len(groups) == 3:
                    timestamp, level, message = groups
                    level = level.upper()
                else:
                    continue

                pattern = self.create_pattern(message, level)
                detected_patterns = self.advanced_pattern_detection(line)

                return LogEntry(
                    timestamp=timestamp,
                    level=level,
                    message=message,
                    original_line=line,
                    pattern=pattern,
                    detected_patterns=detected_patterns,
                    language=self.detect_language(message),
                )

        # Unstructured log
        pattern = self.create_pattern(line, "UNKNOWN")
        detected_patterns = self.advanced_pattern_detection(line)

        return LogEntry(
            timestamp="unknown",
            level="UNKNOWN",
            message=line,
            original_line=line,
            pattern=pattern,
            detected_patterns=detected_patterns,
            language=self.detect_language(line),
        )

    def fuzzy_deduplication(
        self, entries: list[LogEntry], progress=None, task_id=None
    ) -> list[LogEntry]:
        """Optimized fuzzy deduplication with progress tracking"""
        if not HAS_FUZZYWUZZY:
            logger.warning(
                "Fuzzy deduplication disabled: fuzzywuzzy not found. Falling back to simple."
            )
            return self._simple_deduplication(entries, progress, task_id)

        # Early exit for small datasets
        if len(entries) < 10:
            if progress and task_id:
                progress.advance(task_id, advance=len(entries))
            return entries

        # Performance optimization: batch processing for large datasets
        if len(entries) > 10000:
            logger.info(
                f"Large dataset detected ({len(entries)} entries). Using optimized deduplication."
            )
            return self._optimized_deduplication(entries, progress, task_id)

        groups = []
        used = set()
        processed = 0

        for i, entry in enumerate(entries):
            if i in used:
                processed += 1
                if (
                    progress and task_id and processed % 100 == 0
                ):  # Update every 100 items
                    progress.advance(task_id, advance=100)
                continue

            group = [entry]
            used.add(i)

            # Optimize: only compare with nearby entries first, then expand if needed
            search_window = min(1000, len(entries) - i - 1)  # Limit search window

            for j in range(i + 1, min(i + 1 + search_window, len(entries))):
                if j in used:
                    continue

                other_entry = entries[j]

                # Quick pre-filter: skip if messages are very different in length
                if abs(len(entry.message) - len(other_entry.message)) > 50:
                    continue

                similarity = fuzz.ratio(entry.message, other_entry.message)
                if similarity >= self.config.fuzzy_threshold:
                    group.append(other_entry)
                    used.add(j)

            groups.append(group)
            processed += 1

            # Update progress periodically
            if progress and task_id and processed % 50 == 0:
                progress.advance(task_id, advance=50)

        # Ensure we've advanced the full amount
        if progress and task_id:
            remaining = len(entries) - progress.tasks[task_id].completed
            if remaining > 0:
                progress.advance(task_id, advance=remaining)

        # Create deduplicated entries
        deduplicated = []
        for group in groups:
            if len(group) <= self.config.dedup_threshold:
                deduplicated.extend(group)
            else:
                first_entry = group[0]
                last_entry = group[-1]

                summary_entry = LogEntry(
                    timestamp=first_entry.timestamp,
                    level=first_entry.level,
                    message=first_entry.message,
                    original_line=f"{first_entry.original_line} [FUZZY_REPEATED {len(group)}x, last: {last_entry.timestamp}]",
                    pattern=first_entry.pattern,
                    detected_patterns=first_entry.detected_patterns,
                )
                deduplicated.append(summary_entry)

        return deduplicated

    def _optimized_deduplication(
        self, entries: list[LogEntry], progress=None, task_id=None
    ) -> list[LogEntry]:
        """Optimized deduplication for large datasets using pattern-based grouping first"""
        logger.info("Using pattern-based pre-grouping for large dataset optimization")

        # First pass: group by exact patterns (very fast)
        pattern_groups = defaultdict(list)
        for i, entry in enumerate(entries):
            pattern_groups[entry.pattern].append((i, entry))
            if progress and task_id and i % 1000 == 0:
                progress.advance(task_id, advance=1000)

        # Second pass: fuzzy deduplication within similar pattern groups only
        final_groups = []
        processed_entries = 0

        for pattern, pattern_entries in pattern_groups.items():
            if len(pattern_entries) == 1:
                final_groups.append([pattern_entries[0][1]])
                processed_entries += 1
                continue

            # Apply fuzzy matching only within this pattern group
            entries_only = [entry for _, entry in pattern_entries]
            if len(entries_only) > 100:  # Still large group, use simple dedup
                deduplicated = self._simple_deduplication(entries_only)
                final_groups.extend([[entry] for entry in deduplicated])
            else:
                # Small enough for fuzzy matching
                used_within_group = set()
                for i, entry in enumerate(entries_only):
                    if i in used_within_group:
                        continue

                    group = [entry]
                    used_within_group.add(i)

                    for j, other_entry in enumerate(entries_only[i + 1 :], i + 1):
                        if j in used_within_group:
                            continue

                        similarity = fuzz.ratio(entry.message, other_entry.message)
                        if similarity >= self.config.fuzzy_threshold:
                            group.append(other_entry)
                            used_within_group.add(j)

                    final_groups.append(group)

            processed_entries += len(pattern_entries)
            if progress and task_id:
                progress.advance(task_id, advance=len(pattern_entries))

        # Convert groups back to deduplicated entries
        return self._groups_to_entries(final_groups)

    def _simple_deduplication(
        self, entries: list[LogEntry], progress=None, task_id=None
    ) -> list[LogEntry]:
        """Simple deduplication fallback with progress tracking"""
        pattern_counts = Counter(entry.pattern for entry in entries)
        pattern_entries = defaultdict(list)

        for i, entry in enumerate(entries):
            pattern_entries[entry.pattern].append(entry)
            if progress and task_id and i % 500 == 0:
                progress.advance(task_id, advance=500)

        deduplicated = []
        processed_patterns = 0

        for pattern, count in pattern_counts.items():
            entries_for_pattern = pattern_entries[pattern]

            if count <= self.config.dedup_threshold:
                deduplicated.extend(entries_for_pattern)
            else:
                first_entry = entries_for_pattern[0]
                last_entry = entries_for_pattern[-1]

                summary_entry = LogEntry(
                    timestamp=first_entry.timestamp,
                    level=first_entry.level,
                    message=first_entry.message,
                    original_line=f"{first_entry.original_line} [REPEATED {count}x, last: {last_entry.timestamp}]",
                    pattern=first_entry.pattern,
                    detected_patterns=first_entry.detected_patterns,
                )
                deduplicated.append(summary_entry)

            processed_patterns += 1
            if progress and task_id and processed_patterns % 10 == 0:
                progress.advance(task_id, advance=count)

        # Ensure full progress completion
        if progress and task_id:
            remaining = len(entries) - progress.tasks[task_id].completed
            if remaining > 0:
                progress.advance(task_id, advance=remaining)

        return deduplicated

    def _groups_to_entries(self, groups: list[list[LogEntry]]) -> list[LogEntry]:
        """Convert deduplication groups back to final entries"""
        deduplicated = []
        for group in groups:
            if len(group) <= self.config.dedup_threshold:
                deduplicated.extend(group)
            else:
                first_entry = group[0]
                last_entry = group[-1]

                summary_entry = LogEntry(
                    timestamp=first_entry.timestamp,
                    level=first_entry.level,
                    message=first_entry.message,
                    original_line=f"{first_entry.original_line} [FUZZY_REPEATED {len(group)}x, last: {last_entry.timestamp}]",
                    pattern=first_entry.pattern,
                    detected_patterns=first_entry.detected_patterns,
                )
                deduplicated.append(summary_entry)

        return deduplicated

    def process_file(
        self, file_path: str
    ) -> tuple[str, list[LogEntry], dict[str, Any]]:
        """Main log processing pipeline with persistent progress tracking"""
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        start_time = datetime.now()
        lines = text.split("\n")
        original_char_count = len(text)  # Track original character count
        original_line_count = len(lines)

        # Create persistent progress display
        with Progress(console=self.console, transient=False) as progress:
            # Phase 1: Parsing
            parse_task = progress.add_task("📝 Parsing logs...", total=len(lines))

            entries_before_dedup = []  # Store entries before deduplication
            for line in lines:
                entry = self.parse_log_line(line)
                if entry:
                    entries_before_dedup.append(entry)
                progress.advance(parse_task)

            progress.update(
                parse_task, description=f"✅ Parsed {len(entries_before_dedup)} entries"
            )

            # Phase 2: Deduplication (if enabled)
            processed_entries = entries_before_dedup
            if self.config.enable_deduplication:
                dedup_task = progress.add_task(
                    "🔄 Deduplicating...", total=len(entries_before_dedup)
                )
                processed_entries = self.fuzzy_deduplication(
                    entries_before_dedup, progress, dedup_task
                )
                progress.update(
                    dedup_task,
                    description=f"✅ Deduplicated to {len(processed_entries)} entries",
                )
            else:
                # Add a completed task to show deduplication was skipped
                skip_task = progress.add_task("⏭️ Deduplication skipped", total=1)
                progress.advance(skip_task)

        processed_lines_text = "\n".join(
            [entry.original_line for entry in processed_entries]
        )
        processed_char_count = len(processed_lines_text)

        processing_time = (datetime.now() - start_time).total_seconds()

        # Calculate compression ratios
        compression_ratio_by_chars = (
            1.0 - (processed_char_count / original_char_count)
            if original_char_count > 0
            else 0.0
        )
        compression_ratio_by_lines = (
            1.0 - (len(processed_entries) / len(entries_before_dedup))
            if len(entries_before_dedup) > 0
            else 0.0
        )

        stats = {
            "original_lines": original_line_count,
            "processed_lines": len(processed_entries),
            "entries_parsed": len(
                entries_before_dedup
            ),  # Number of entries successfully parsed
            "compression_ratio": compression_ratio_by_lines,  # Main compression ratio (by lines)
            "compression_ratio_by_chars": compression_ratio_by_chars,
            "compression_ratio_by_lines": compression_ratio_by_lines,
            "processing_time": processing_time,
            "unique_patterns": len(set(entry.pattern for entry in processed_entries)),
            "unique_loggers": len(set(entry.logger for entry in processed_entries)),
            "log_levels": dict(Counter(entry.level for entry in processed_entries)),
        }

        return processed_lines_text, processed_entries, stats
