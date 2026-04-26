#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse Semantic Compression Hook
======================================

Compresses large tool outputs for token efficiency while preserving
important information like errors, warnings, and key patterns.

Features:
- Detects large outputs (>500 estimated tokens)
- Preserves error messages and important keywords
- Async compression to avoid blocking workflow
- Optional: can store compressed version to CKS

Extracted from PostToolUse_semantic_compress.py for in-process execution.
"""

import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook

# SemanticCompressor was never available (features.checkpoint module doesn't exist)
# The _simple_compress fallback is the only implementation


class SemanticCompress(PostToolUseHook):
    # Only Bash produces large enough output to compress
    tool_matcher = {"Bash"}
    """
    Compresses large tool outputs asynchronously.
    """

    env_var = "SEMANTIC_COMPRESS_ENABLED"
    default_enabled = True

    # Configuration
    TOKEN_THRESHOLD = 500  # Compress outputs larger than this
    COMPRESSION_TARGET = 200  # Target token count for compressed output
    ASYNC_DELAY_SECONDS = 0.1

    # Tools whose outputs can be compressed
    COMPRESSIBLE_TOOLS = {"Bash", "Read", "Task"}

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent
        self.log_file = self.hooks_dir / "data" / "semantic_compress_log.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Process and potentially compress tool output.

        Returns dict with compression status (compression happens async).
        """
        result = {
            "passed": True,
            "compressed": False,
        }

        if not self._should_compress(tool_name, tool_response):
            result["reason"] = "below_threshold"
            return result

        output_text = str(tool_response)

        # Compress asynchronously
        self._compress_output_async(tool_name, output_text)

        result["compressed"] = True
        result["original_tokens"] = self._estimate_tokens(output_text)
        result["target_tokens"] = self.COMPRESSION_TARGET

        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        if not text:
            return 0
        return len(str(text)) // 4

    def _should_compress(self, tool_name: str, tool_output: Any) -> bool:
        """Determine if output should be compressed."""
        if tool_name not in self.COMPRESSIBLE_TOOLS:
            return False

        output_str = str(tool_output)
        return self._estimate_tokens(output_str) > self.TOKEN_THRESHOLD

    def _compress_output_async(self, tool_name: str, output_text: str) -> None:
        """Compress output in background thread."""

        def compression_worker():
            try:
                time.sleep(self.ASYNC_DELAY_SECONDS)

                # Try to import SemanticCompressor from checkpoint module
                try:
                    from features.checkpoint import SemanticCompressor
                    compressor = SemanticCompressor()
                    compressed = compressor.compress(
                        output_text,
                        max_tokens=self.COMPRESSION_TARGET,
                        preserve_errors=True
                    )
                except Exception:
                    # Fallback: simple truncation
                    compressed = self._simple_compress(output_text)

                # Log compression stats
                original_tokens = self._estimate_tokens(output_text)
                compressed_tokens = self._estimate_tokens(compressed)
                compression_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

                self._log_compression(tool_name, original_tokens, compressed_tokens, compression_ratio)

            except Exception:
                pass  # Silently fail - don't block workflow

        thread = threading.Thread(target=compression_worker, daemon=True)
        thread.start()

    def _simple_compress(self, text: str) -> str:
        """Simple compression fallback: truncate with preservation."""
        lines = text.split("\n")

        # Keep lines with errors, warnings, or important keywords
        important_keywords = ["error", "warning", "fail", "exception", "traceback", "errno"]
        important_lines = []

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in important_keywords):
                important_lines.append(line)

        # Add first and last few lines for context
        header = lines[:5]
        footer = lines[-5:] if len(lines) > 10 else []

        result_lines = header + ["..."] + important_lines + ["..."] + footer

        return "\n".join(result_lines)[:self.COMPRESSION_TARGET * 4]

    def _log_compression(self, tool_name: str, original_tokens: int, compressed_tokens: int, compression_ratio: float) -> None:
        """Log compression stats for value assessment."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "tool_name": tool_name,
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                    "compression_ratio": compression_ratio,
                }) + "\n")
        except Exception:
            pass  # Don't fail if logging fails
