from log_chunker.data_models import ChunkInfo, LogEntry

from .boundary_config import BoundaryConfig


class BoundaryDetector:
    def __init__(self, config: BoundaryConfig):
        self.config = config
        self.tag_weights = config.tag_weights
        self.threshold = config.threshold
        self.min_chunk_size = config.min_chunk_size
        self.max_chunk_size = config.max_chunk_size
        self.compiled_patterns = config.compiled_patterns

    def calculate_line_score(self, entry: LogEntry) -> float:
        """Calculate boundary score for a single log entry based on tags and patterns"""
        score = 0.0

        # Score based on tags
        for tag in entry.tags:
            if tag in self.tag_weights:
                score += self.tag_weights[tag]

        # Score based on boundary patterns
        for pattern in self.compiled_patterns:
            if pattern.match(entry.message):
                score += 10.0
                break

        return score

    def detect_boundaries(self, entries: list[LogEntry]) -> list[ChunkInfo]:
        """Detect chunk boundaries in a sequence of log entries"""
        if not entries:
            return []

        chunks = []
        current_chunk = []
        current_score = 0.0
        start_index = 0

        for i, entry in enumerate(entries):
            line_score = self.calculate_line_score(entry)
            current_score += line_score

            # Check if we've reached a boundary
            if current_score >= self.threshold or self.is_explicit_boundary(entry):
                # Ensure minimum chunk size
                if len(current_chunk) >= self.min_chunk_size:
                    chunk_info = self.create_chunk_info(start_index, i, current_chunk)
                    chunks.append(chunk_info)
                    current_chunk = []
                    current_score = 0.0
                    start_index = i + 1
                # If chunk is too small but we're at max size, force boundary
                elif len(current_chunk) >= self.max_chunk_size:
                    chunk_info = self.create_chunk_info(start_index, i, current_chunk)
                    chunks.append(chunk_info)
                    current_chunk = [entry]
                    current_score = line_score
                    start_index = i
                else:
                    current_chunk.append(entry)
            else:
                current_chunk.append(entry)

                # Force boundary if we've reached max chunk size
                if len(current_chunk) >= self.max_chunk_size:
                    chunk_info = self.create_chunk_info(start_index, i, current_chunk)
                    chunks.append(chunk_info)
                    current_chunk = []
                    current_score = 0.0
                    start_index = i + 1

        # Add remaining entries as final chunk
        if current_chunk:
            chunk_info = self.create_chunk_info(
                start_index, len(entries) - 1, current_chunk
            )
            chunks.append(chunk_info)

        return chunks

    def is_explicit_boundary(self, entry: LogEntry) -> bool:
        """Check if log entry matches explicit boundary patterns"""
        for pattern in self.compiled_patterns:
            if pattern.match(entry.message):
                return True
        return False

    def create_chunk_info(
        self, start_index: int, end_index: int, entries: list[LogEntry]
    ) -> ChunkInfo:
        """Create ChunkInfo object for a detected chunk"""
        estimated_tokens = sum(len(entry.message.split()) for entry in entries)
        return ChunkInfo(
            chunk_id=len(entries),  # Temporary ID, will be reassigned later
            start_line=entries[0].line_number,
            end_line=entries[-1].line_number,
            estimated_tokens=estimated_tokens,
            method_used="tag_based_boundary",
            quality_score=0.0,  # Will be calculated later
            boundary_type="auto"
            if not self.is_explicit_boundary(entries[-1])
            else "explicit",
        )
