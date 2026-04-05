from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ..interfaces.analysis_interfaces import ChatMessage
from ..security_utils import secure_file_path, secure_load_json_file
from .di_container import DIContainer
from .refactored_chat_analyzer import RefactoredChatAnalyzer

#!/usr/bin/env python3
"""Analyzer Integration Layer
Demonstrates how to use the refactored chat analyzer with clean architecture.
"""






class ChatAnalyzerIntegration:
    """Integration layer for the refactored chat analyzer
    Provides simplified interface for common use cases.
    """

    def __init__(self, config_file: Path | None = None) -> None:
        """Initialize analyzer integration.

        Args:
        ----
            config_file: Optional configuration file path

        """
        self.container = DIContainer()
        self.analyzer = RefactoredChatAnalyzer(self.container)
        self.config_file = config_file

    async def analyze_chat_file(
        self, file_path: Path, output_format: str = "json"
    ) -> str:
        """Analyze chat from file with security validation.

        Args:
        ----
            file_path: Path to chat file
            output_format: Output format (json, html, markdown, plain, summary)

        Returns:
        -------
            str: Formatted analysis results

        """
        try:
            # Secure file validation
            base_dir = Path.cwd()
            safe_path = secure_file_path(
                base_dir, str(file_path), {".json", ".jsonl", ".txt"}
            )

            # Load and parse chat data
            messages = await self._load_chat_messages(safe_path)

            # Analyze and format
            return await self.analyzer.analyze_and_format(messages, output_format)

        except Exception as e:
            return f"Error analyzing chat file: {e}"

    async def analyze_chat_messages(
        self, messages: list[dict[str, Any]], output_format: str = "json"
    ) -> str:
        """Analyze chat from message list.

        Args:
        ----
            messages: List of message dictionaries
            output_format: Output format

        Returns:
        -------
            str: Formatted analysis results

        """
        try:
            # Convert to ChatMessage objects
            chat_messages = self._convert_to_chat_messages(messages)

            # Analyze and format
            return await self.analyzer.analyze_and_format(chat_messages, output_format)

        except Exception as e:
            return f"Error analyzing chat messages: {e}"

    async def analyze_and_export(self, file_path: Path, output_path: Path) -> bool:
        """Analyze chat and export to file.

        Args:
        ----
            file_path: Input chat file path
            output_path: Output file path

        Returns:
        -------
            bool: Success status

        """
        try:
            # Secure file validation
            base_dir = Path.cwd()
            safe_input_path = secure_file_path(
                base_dir, str(file_path), {".json", ".jsonl", ".txt"}
            )
            safe_output_path = secure_file_path(
                base_dir, str(output_path), {".json", ".html", ".md", ".txt"}
            )

            # Load and parse chat data
            messages = await self._load_chat_messages(safe_input_path)

            # Analyze and export
            return await self.analyzer.analyze_and_export(
                messages, str(safe_output_path)
            )

        except Exception:
            return False

    async def get_analysis_summary(self, file_path: Path) -> str:
        """Get executive summary of chat analysis.

        Args:
        ----
            file_path: Path to chat file

        Returns:
        -------
            str: Executive summary

        """
        try:
            # Secure file validation
            base_dir = Path.cwd()
            safe_path = secure_file_path(
                base_dir, str(file_path), {".json", ".jsonl", ".txt"}
            )

            # Load and parse chat data
            messages = await self._load_chat_messages(safe_path)

            # Get summary
            return await self.analyzer.get_analysis_summary(messages)

        except Exception as e:
            return f"Error getting analysis summary: {e}"

    async def batch_analyze_files(
        self, file_paths: list[Path], output_dir: Path
    ) -> dict[str, bool]:
        """Batch analyze multiple chat files.

        Args:
        ----
            file_paths: List of input file paths
            output_dir: Output directory

        Returns:
        -------
            Dict[str, bool]: Success status for each file

        """
        results = {}

        for file_path in file_paths:
            try:
                # Generate output filename
                output_file = output_dir / f"{file_path.stem}_analysis.html"

                # Analyze and export
                success = await self.analyze_and_export(file_path, output_file)
                results[str(file_path)] = success

            except Exception:
                results[str(file_path)] = False

        return results

    async def get_analyzer_info(self) -> dict[str, Any]:
        """Get analyzer information and capabilities."""
        return await self.analyzer.get_engine_info()

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        return await self.analyzer.get_performance_metrics()

    async def _load_chat_messages(self, file_path: Path) -> list[ChatMessage]:
        """Load chat messages from file with format detection."""
        try:
            # Determine file format
            if file_path.suffix.lower() == ".jsonl":
                return await self._load_jsonl_messages(file_path)
            if file_path.suffix.lower() == ".json":
                return await self._load_json_messages(file_path)
            if file_path.suffix.lower() == ".txt":
                return await self._load_text_messages(file_path)
            msg = f"Unsupported file format: {file_path.suffix}"
            raise ValueError(msg)

        except Exception as e:
            msg = f"Error loading messages from {file_path}: {e}"
            raise ValueError(msg)

    async def _load_jsonl_messages(self, file_path: Path) -> list[ChatMessage]:
        """Load messages from JSONL format."""
        messages = []

        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    message = self._parse_message_data(data, line_num)
                    if message:
                        messages.append(message)
                except json.JSONDecodeError:
                    continue

        return messages

    async def _load_json_messages(self, file_path: Path) -> list[ChatMessage]:
        """Load messages from JSON format."""
        try:
            data = secure_load_json_file(file_path)

            # Handle different JSON structures
            if isinstance(data, list):
                # Array of message objects
                return [
                    self._parse_message_data(msg, i)
                    for i, msg in enumerate(data)
                    if self._parse_message_data(msg, i)
                ]
            if isinstance(data, dict):
                # Single message or container with messages array
                if "messages" in data:
                    return [
                        self._parse_message_data(msg, i)
                        for i, msg in enumerate(data["messages"])
                        if self._parse_message_data(msg, i)
                    ]
                # Single message object
                message = self._parse_message_data(data, 0)
                return [message] if message else []
            msg = "Invalid JSON structure"
            raise ValueError(msg)

        except Exception as e:
            msg = f"Error loading JSON messages: {e}"
            raise ValueError(msg)

    async def _load_text_messages(self, file_path: Path) -> list[ChatMessage]:
        """Load messages from text format (simple implementation)."""
        messages = []

        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        message_num = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple parsing logic - assumes format like "Author: Message"
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    author = parts[0].strip()
                    content = parts[1].strip()

                    message_num += 1
                    message = ChatMessage(
                        id=str(message_num),
                        content=content,
                        timestamp="2024-01-01T00:00:00Z",  # Default timestamp
                        author=author,
                        metadata={"source": "text_file", "line": message_num},
                    )
                    messages.append(message)

        return messages

    def _parse_message_data(
        self, data: dict[str, Any], index: int
    ) -> ChatMessage | None:
        """Parse message data from dictionary."""
        try:
            # Extract required fields
            message_id = data.get("id", str(index))
            content = data.get("content", data.get("text", data.get("message", "")))
            author = data.get(
                "author", data.get("user", data.get("username", "Unknown"))
            )
            timestamp = data.get(
                "timestamp", data.get("time", data.get("date", "2024-01-01T00:00:00Z"))
            )

            if not content:
                return None

            # Extract metadata
            metadata = data.get("metadata", {})
            metadata.update({"source_index": index})

            return ChatMessage(
                id=str(message_id),
                content=str(content),
                timestamp=str(timestamp),
                author=str(author),
                metadata=metadata,
            )

        except Exception:
            return None

    def _convert_to_chat_messages(
        self, messages: list[dict[str, Any]]
    ) -> list[ChatMessage]:
        """Convert dictionary messages to ChatMessage objects."""
        chat_messages = []

        for i, msg_data in enumerate(messages):
            message = self._parse_message_data(msg_data, i)
            if message:
                chat_messages.append(message)

        return chat_messages

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.analyzer.cleanup()


# Example usage functions
async def example_single_file_analysis() -> None:
    """Example: Analyze a single chat file."""
    integration = ChatAnalyzerIntegration()

    try:
        # Analyze file and get HTML report
        result = await integration.analyze_chat_file(
            Path("chat_data.jsonl"),
            output_format="html",
        )

        # Save result
        with open("analysis_report.html", "w", encoding="utf-8") as f:
            f.write(result)

    finally:
        await integration.cleanup()


async def example_batch_analysis() -> None:
    """Example: Batch analyze multiple files."""
    integration = ChatAnalyzerIntegration()

    try:
        # List of files to analyze
        chat_files = [
            Path("chat1.jsonl"),
            Path("chat2.jsonl"),
            Path("chat3.jsonl"),
        ]

        # Output directory
        output_dir = Path("analysis_results")
        output_dir.mkdir(exist_ok=True)

        # Batch analyze
        results = await integration.batch_analyze_files(chat_files, output_dir)

        # Print results
        for _file_path, _success in results.items():
            pass

    finally:
        await integration.cleanup()


async def example_summary_only() -> None:
    """Example: Get only executive summary."""
    integration = ChatAnalyzerIntegration()

    try:
        # Get summary
        await integration.get_analysis_summary(Path("important_chat.jsonl"))

    finally:
        await integration.cleanup()


async def example_custom_messages() -> None:
    """Example: Analyze custom message list."""
    integration = ChatAnalyzerIntegration()

    try:
        # Custom message data
        messages = [
            {
                "id": "1",
                "content": "Hello everyone!",
                "author": "Alice",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "id": "2",
                "content": "Hi Alice! How are you?",
                "author": "Bob",
                "timestamp": "2024-01-01T10:01:00Z",
            },
            {
                "id": "3",
                "content": "I'm doing great, thanks for asking!",
                "author": "Alice",
                "timestamp": "2024-01-01T10:02:00Z",
            },
            {
                "id": "4",
                "content": "What's the topic for today?",
                "author": "Charlie",
                "timestamp": "2024-01-01T10:03:00Z",
            },
        ]

        # Analyze with custom messages
        await integration.analyze_chat_messages(messages, output_format="summary")

    finally:
        await integration.cleanup()


# Command-line interface
async def main() -> None:
    """Main function for command-line usage."""
    import sys

    if len(sys.argv) < 2:
        return

    command = sys.argv[1]
    integration = ChatAnalyzerIntegration()

    try:
        if command == "analyze":
            if len(sys.argv) < 3:
                return

            file_path = Path(sys.argv[2])
            output_format = sys.argv[3] if len(sys.argv) > 3 else "json"

            await integration.analyze_chat_file(file_path, output_format)

        elif command == "summary":
            if len(sys.argv) < 3:
                return

            file_path = Path(sys.argv[2])
            await integration.get_analysis_summary(file_path)

        elif command == "batch":
            if len(sys.argv) < 3:
                return

            file_paths = [Path(arg) for arg in sys.argv[2:]]
            output_dir = Path("batch_results")
            output_dir.mkdir(exist_ok=True)

            results = await integration.batch_analyze_files(file_paths, output_dir)

            for file_path in results:
                pass

        elif command == "info":
            await integration.get_analyzer_info()

        else:
            pass

    finally:
        await integration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
