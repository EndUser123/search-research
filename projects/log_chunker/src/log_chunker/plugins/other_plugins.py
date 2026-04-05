"""Additional chunking plugins."""

import logging
import re
from datetime import datetime
from typing import Any

try:
    import numpy as np
    from scipy.signal import find_peaks
    from sklearn.preprocessing import StandardScaler

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logging.warning(
        "SciPy and Scikit-learn not found. TemporalChunkingPlugin will be disabled."
    )

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning(
        "Transformers and Torch not found. PerplexityChunkingPlugin will be disabled."
    )

from ..data_models import ChunkInfo, LogEntry
from .base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class TemporalChunkingPlugin(BaseChunkingPlugin):
    """Temporal anomaly-based chunking"""

    name = "temporal"
    version = "1.0.0"
    dependencies = [
        "scipy",
        "sklearn",
    ]  # For documentation, actual check is done via HAS_SCIPY

    def parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse various timestamp formats"""
        # Optimized parsing for common formats first
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with Z (UTC)
            "%Y-%m-%dT%H:%M:%S",  # ISO without Z
            "%Y-%m-%d %H:%M:%S,%f",  # Log4j style with milliseconds
            "%Y-%m-%d %H:%M:%S.%f",  # ISO with microseconds
            "%Y-%m-%d %H:%M:%S",  # Simple date-time
            "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY HH:MM:SS
            "%m/%d/%Y %H:%M:%S",  # MM/DD/YYYY HH:MM:SS
        ]

        # Strip potential time zone info or extra log data after timestamp for cleaner parsing
        clean_timestamp_str = timestamp_str.split(" ")[
            0
        ]  # Heuristic for common log formats
        if "," in clean_timestamp_str:
            clean_timestamp_str = clean_timestamp_str.split(",")[0]
        if (
            "." in clean_timestamp_str and len(clean_timestamp_str.split(".")[-1]) > 6
        ):  # Handle nano/pico seconds
            clean_timestamp_str = clean_timestamp_str.rsplit(".", 1)[0]

        for fmt in formats:
            try:
                # Attempt to parse, handling potential fractional seconds more robustly
                if "%f" in fmt:
                    return datetime.strptime(clean_timestamp_str, fmt)
                else:
                    return datetime.strptime(
                        clean_timestamp_str.split(".")[0], fmt
                    )  # Remove sub-seconds if format doesn't expect it
            except ValueError:
                continue
        logger.debug(f"Could not parse timestamp: {timestamp_str}")
        return None

    def initialize(self, config, console) -> bool:
        """Initialize temporal plugin and check dependencies."""
        if not HAS_SCIPY:
            self.console.log(
                "[yellow]TemporalChunkingPlugin disabled: Missing scipy or scikit-learn.[/yellow]"
            )
            return False
        return super().initialize(config, console)

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        if not HAS_SCIPY or len(log_entries) < 3:
            return []

        timestamps = []
        valid_indices = []

        for i, entry in enumerate(log_entries):
            # Use entry.timestamp which is already parsed by preprocessor if possible
            if entry.timestamp != "unknown":
                try:
                    # Attempt to parse it as a datetime object directly if not already
                    dt = (
                        datetime.fromtimestamp(float(entry.timestamp))
                        if isinstance(entry.timestamp, (int, float))
                        else self.parse_timestamp(entry.timestamp)
                    )
                    if dt:
                        timestamps.append(
                            dt.timestamp()
                        )  # Convert to Unix timestamp for calculation
                        valid_indices.append(i)
                except (ValueError, TypeError):
                    logger.debug(
                        f"Invalid timestamp format in LogEntry for temporal analysis: {entry.timestamp}"
                    )
                    continue
            else:  # Fallback for entries where timestamp was 'unknown'
                dt = self.parse_timestamp(
                    entry.original_line
                )  # Try to parse from original line
                if dt:
                    timestamps.append(dt.timestamp())
                    valid_indices.append(i)

        if len(timestamps) < 3:
            return []

        # Calculate time differences
        time_diffs = np.diff(timestamps)

        if len(time_diffs) < 2:
            return []

        # Normalize differences
        scaler = StandardScaler()
        try:
            normalized_diffs = scaler.fit_transform(time_diffs.reshape(-1, 1)).flatten()

            # Find peaks (anomalous gaps)
            # peaks, _ = find_peaks(normalized_diffs, height=self.config.temporal_std_threshold)
            # Min_height: Only consider peaks above a certain normalized standard deviation threshold
            # Distance: Minimum horizontal distance (in samples) between neighboring peaks
            # Prominence: Measures how much a peak stands out from the surrounding baseline of the signal

            # Use a relative prominence for finding peaks which makes it robust to general noise levels
            # A common heuristic is to look for peaks that are a certain factor above the standard deviation.
            # `prominence` parameter is more robust than `height` for anomalies.
            # We use `height` as a simple filter based on config for now, as defined in the config.

            # Using height for simplicity as it directly maps to temporal_std_threshold
            peaks, _ = find_peaks(
                normalized_diffs, height=self.config.temporal_std_threshold
            )

            # Map back to log entry indices
            boundaries = []
            for peak in peaks:
                # The peak index refers to an index in `time_diffs`.
                # If time_diffs[peak] is a boundary, it applies to valid_indices[peak+1]
                if peak + 1 < len(
                    valid_indices
                ):  # Ensure the index is within bounds of valid_indices
                    boundaries.append(valid_indices[peak + 1])

            return boundaries

        except ValueError as ve:
            logger.debug(f"ValueError in temporal analysis (e.g., NaN in data): {ve}")
            return []
        except (
            Exception
        ) as e:  # Catch other potential issues like empty arrays after filtering
            logger.debug(f"Unexpected error in temporal analysis: {e}", exc_info=True)
            return []

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """
        Performs analysis on the generated chunks.
        This plugin does not perform chunk analysis, returning an empty dict.
        """
        return {}


class ConversationChunkingPlugin(BaseChunkingPlugin):
    """Conversation-aware chunking for chat logs"""

    name = "conversation"
    version = "1.0.0"
    dependencies = []

    def extract_speaker(self, line: str) -> str | None:
        """Extract speaker from various chat formats"""
        # Make patterns more robust, e.g., optional whitespace around separator
        patterns = [
            r"^\s*([A-Za-z0-9_.-]+)\s*:\s*",  # Username: or Username-something:
            r"^\s*\[([A-Za-z0-9_.-]+)\]\s*",  # [Username]
            r"^\s*<([A-Za-z0-9_.-]+)>\s*",  # <Username>
            r"^\s*\*([A-Za-z0-9_.-]+)\*\s*",  # *Username*
            r"^\s*([A-Za-z0-9_.-]+)\s*>",  # Username > (e.g. IRC logs)
        ]

        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                return match.group(1)
        return None

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        boundaries = []
        current_speaker = None

        for i, entry in enumerate(log_entries):
            speaker = self.extract_speaker(entry.original_line)

            # Speaker change indicates potential boundary
            # Apply speaker_change_weight from config to influence boundary fusion
            if speaker and speaker != current_speaker and current_speaker is not None:
                # Add index i as a boundary
                boundaries.append(i)

            if speaker:
                current_speaker = speaker

        return boundaries

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """
        Performs analysis on the generated chunks.
        This plugin does not perform chunk analysis, returning an empty dict.
        """
        return {}


class PatternChunkingPlugin(BaseChunkingPlugin):
    """Advanced pattern-based chunking"""

    name = "pattern"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self._compiled_patterns = {}  # To store compiled regex patterns for performance

    def initialize(self, config, console) -> bool:
        """Initialize plugin and load patterns from configuration."""
        super().initialize(config, console)

        # Load patterns from config
        self.advanced_patterns = self.config.advanced_detection_patterns

        # Compile patterns for efficiency
        for category, patterns_list in self.advanced_patterns.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns_list
            ]

        return True

    def detect_patterns(self, line: str) -> list[str]:
        """Detect patterns in a log line"""
        detected = []

        for category, compiled_patterns in self._compiled_patterns.items():
            for pattern_re in compiled_patterns:
                if pattern_re.search(line):
                    detected.append(category)
                    break  # Only need one match per category

        return detected

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        boundaries = []

        # We assume preprocessor has already detected patterns and stored them in LogEntry.detected_patterns
        # This plugin can then use those or run its own (if its patterns are different/more granular)
        # For simplicity, we'll iterate and mark boundaries based on specific pattern types.

        previous_patterns = set()

        for i, entry in enumerate(log_entries):
            current_patterns = set(
                entry.detected_patterns
            )  # Patterns from preprocessor

            # Alternatively, if this plugin has its own specific patterns not in preprocessor:
            # current_patterns = set(self.detect_patterns(entry.original_line))

            # A "boundary" is often indicated by a change in the primary type of log.
            # For example, starting an error block, a new section, or specific network activity.

            # Heuristic for boundary: new error/section starts or significant shift
            is_new_error_section = (
                "error_start" in current_patterns
                and "error_start" not in previous_patterns
            ) or (
                "section_start" in current_patterns
                and "section_start" not in previous_patterns
            )

            # Or if major pattern categories significantly change.
            # This logic can be refined based on desired chunking behavior.
            if i > 0 and is_new_error_section:
                boundaries.append(i)

            previous_patterns = current_patterns

        return boundaries

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """
        Performs analysis on the generated chunks.
        This plugin does not perform chunk analysis, returning an empty dict.
        """
        return {}


class PerplexityChunkingPlugin(BaseChunkingPlugin):
    """Perplexity-based chunking using language model uncertainty"""

    name = "perplexity"
    version = "1.0.0"
    dependencies = ["transformers", "torch"]

    def __init__(self):
        super().__init__()
        self.tokenizer = None
        self.model = None
        self.device = "cpu"  # Default device

    def initialize(self, config, console) -> bool:
        """Initialize perplexity plugin, load model, and check dependencies."""
        if not HAS_TRANSFORMERS:
            self.console.log(
                "[yellow]PerplexityChunkingPlugin disabled: Missing transformers or torch.[/yellow]"
            )
            return False

        try:
            self.device = (
                "cuda" if config.use_gpu and torch.cuda.is_available() else "cpu"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(config.perplexity_model)
            self.model = AutoModelForCausalLM.from_pretrained(
                config.perplexity_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            ).to(self.device)

            if self.tokenizer.pad_token is None:
                # Some models don't have a pad token, use EOS token as fallback
                self.tokenizer.pad_token = self.tokenizer.eos_token

            logger.info(
                f"Loaded perplexity model {config.perplexity_model} on {self.device}"
            )
            return super().initialize(config, console)
        except (ImportError, OSError) as ie:  # OSError for e.g. model not found
            self.console.log(
                f"[red]Failed to load perplexity model {config.perplexity_model}: {ie}[/red]"
            )
            logger.error(f"Failed to initialize perplexity chunker: {ie}")
            self.model = None  # Ensure model is None if loading fails
            self.tokenizer = None
            return False
        except Exception as e:
            self.console.log(
                f"[red]An unexpected error occurred initializing perplexity chunker: {e}[/red]"
            )
            logger.error(f"Failed to initialize perplexity chunker: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None
            return False

    def calculate_perplexity(self, text: str) -> list[float]:
        """Calculate perplexity for each sentence"""
        if not self.model or not self.tokenizer:
            return []

        import torch  # Import locally to ensure it's available

        sentences = [
            s.strip() for s in text.split("\n") if s.strip()
        ]  # Clean empty lines
        if not sentences:
            return []

        perplexities = []

        for i, sentence in enumerate(sentences):
            # Build context using configurable window
            start_idx = max(0, i - self.config.perplexity_context_window)
            context_sentences = sentences[start_idx : i + 1]
            context = " ".join(context_sentences)

            try:
                # Tokenize context
                # max_length should respect model's max input length (e.g., 512 for GPT-2 medium)
                # This could be configurable if different models are used.
                inputs = self.tokenizer(
                    context,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.tokenizer.model_max_length,  # Use model's max length
                    padding=True,  # Pad to max_length for batch processing if needed
                ).to(self.device)

                # Calculate loss and perplexity
                with torch.no_grad():
                    outputs = self.model(**inputs, labels=inputs["input_ids"])
                    loss = outputs.loss
                    perplexity = torch.exp(loss).item()
                    perplexities.append(perplexity)

            except torch.cuda.OutOfMemoryError:
                logger.error(
                    "CUDA Out of Memory for perplexity calculation. Try reducing batch_size or context_window."
                )
                # Append 0.0 or raise, depending on desired robustness vs. failure
                perplexities.append(0.0)
            except Exception as e:
                logger.debug(
                    f"Error calculating perplexity for sentence {i}: {e}", exc_info=True
                )
                perplexities.append(0.0)

        return perplexities

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        if not self.model or not log_entries:
            return []

        # Calculate perplexities per log line/sentence
        # Note: self.calculate_perplexity splits by '\n', assuming each log_entry.message is a sentence.
        # This might not always be true, but it's a common simplification.
        perplexities = self.calculate_perplexity(text)

        if len(perplexities) < 3:  # Need at least 3 points to find a local minimum
            return []

        boundaries = []
        # Find local minima (uncertainty valleys)
        # A boundary is considered where perplexity drops significantly after a rise or stays low.
        for i in range(1, len(perplexities) - 1):
            if (
                perplexities[i] > 0  # Ensure valid perplexity value
                and perplexities[i]
                < perplexities[i - 1]  # Current is lower than previous
                and perplexities[i] < perplexities[i + 1]
            ):  # Current is lower than next
                # Check if the drop is significant relative to surrounding values
                # A common heuristic is (current - min(neighbors)) / current.
                # Or, (max(neighbors) - current) / max(neighbors) for a peak.

                # For local minima, we want a significant drop from the *preceding* values.
                # This check ensures it's not just a small wiggle.
                # The perplexity_threshold applies here.
                # It determines how 'sharp' the valley needs to be.

                # Calculate relative drop from the average of immediate neighbors
                avg_neighbor = (perplexities[i - 1] + perplexities[i + 1]) / 2

                if (
                    avg_neighbor > 0
                    and (avg_neighbor - perplexities[i]) / avg_neighbor
                    > self.config.perplexity_threshold
                ):
                    boundaries.append(i)  # Boundary is before line i

        return boundaries

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """
        Performs analysis on the generated chunks.
        This plugin does not perform chunk analysis, returning an empty dict.
        """
        return {}
