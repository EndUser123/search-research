from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

#!/usr/bin/env python3
"""Chat History Search (CHS) - Advanced Cross-Session Chat Intelligence
CSF NIP Command Interface for intelligent chat history search and analysis.
"""


# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))

# Import the chat history search module with context-aware import handling
try:
    from chat_history_search import ChatHistorySearcher
    CHS_AVAILABLE = True
except ImportError:
    try:
        # Fallback: Try importing from the current directory
        current_file = Path(__file__).resolve()
        chs_dir = current_file.parent
        if str(chs_dir) not in sys.path:
            sys.path.insert(0, str(chs_dir))

        from chat_history_search import ChatHistorySearcher
        CHS_AVAILABLE = True

        # Clean up the path
        if str(chs_dir) in sys.path:
            sys.path.remove(str(chs_dir))
    except ImportError as e:
        CHS_AVAILABLE = False
        ChatHistorySearcher = None
        print(f"[INFO] Chat History Search not available: {e}")

        # Create a fallback class for basic functionality
        class ChatHistorySearcher:
            def __init__(self, *args, **kwargs):
                self.available = False

            def search(self, *args, **kwargs):
                return {"results": [], "error": "Chat History Search not available"}

            def analyze(self, *args, **kwargs):
                return {"results": [], "error": "Chat History Search not available"}

# Import CSF integrations
try:
    from core_utils.structured_error_handler import StructuredErrorHandler
    from core_utils.validation_components.validation_gate import ValidationGate
except ImportError:
    # Fallback for development without full CSF stack
    ValidationGate = None
    StructuredErrorHandler = None


class CHSError(Exception):
    """Custom error for CHS operations."""


class ChatHistoryCommand:
    """Command interface for Chat History Search functionality."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.error_handler = (
            StructuredErrorHandler() if StructuredErrorHandler else None
        )
        self.searcher = ChatHistorySearcher()
        self.validation_gate = ValidationGate() if ValidationGate else None

    def handle_search(self, args) -> int:
        """Handle search command with proper error handling."""
        try:
            self.logger.info(f"Executing search for: {args.query}")

            # Validate inputs
            if not args.query or len(args.query.strip()) < 2:
                msg = "Query must be at least 2 characters long"
                raise CHSError(msg)

            # Perform search
            results = self.searcher.search(
                query=args.query,
                session_filter=args.session_filter,
                context_filter=args.context_filter,
                rank_by=args.rank_by,
                limit=args.limit,
            )

            # Validate results
            if self.validation_gate:
                validation_result = self.validation_gate.validate_search_results(
                    results
                )
                if not validation_result.is_valid:
                    self.logger.warning(
                        f"Search validation warnings: {validation_result.warnings}"
                    )

            # Format and output results
            self._output_results(results, args.format, args.output, args.query)

            # ToolRegistry integration removed - users can manually create tasks if needed

            self.logger.info(f"Search completed: {len(results)} results found")
            return 0

        except CHSError as e:
            self.logger.exception(f"Search failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_SEARCH")
            return 1
        except Exception as e:
            self.logger.exception(f"Unexpected search error: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_SEARCH_UNEXPECTED")
            return 1

    def handle_analyze(self, args) -> int:
        """Handle analyze command with comprehensive analysis."""
        try:
            self.logger.info("Executing chat pattern analysis")

            # Perform analysis
            analysis = self.searcher.analyze_patterns(
                pattern_analysis=args.pattern_analysis,
                trend_analysis=args.trend_analysis,
                topic_modeling=args.topic_modeling,
            )

            # Validate analysis
            if self.validation_gate:
                validation_result = self.validation_gate.validate_analysis(analysis)
                if not validation_result.is_valid:
                    self.logger.warning(
                        f"Analysis validation warnings: {validation_result.warnings}"
                    )

            # Output results
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
            else:
                pass

            # ToolRegistry integration removed - users can manually create tasks from insights

            self.logger.info("Analysis completed successfully")
            return 0

        except Exception as e:
            self.logger.exception(f"Analysis failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_ANALYZE")
            return 1

    def handle_index(self, args) -> int:
        """Handle index command with validation."""
        try:
            self.logger.info("Executing chat history indexing")

            if args.rebuild:
                self.logger.info("Rebuilding entire index...")

            success = self.searcher.index_chat_history(rebuild=args.rebuild)

            if success:
                status = self.searcher.get_status()

                # Validate index health
                if self.validation_gate:
                    validation_result = self.validation_gate.validate_index_health(
                        status
                    )
                    if not validation_result.is_valid:
                        pass

                return 0
            return 1

        except Exception as e:
            self.logger.exception(f"Indexing failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_INDEX")
            return 1

    def handle_status(self, args) -> int:
        """Handle status command with comprehensive reporting."""
        try:
            status = self.searcher.get_status()

            # Basic status

            # Detailed status if index is built
            if status["index_status"] == "built":
                pass

            # Health check
            if self.validation_gate:
                health_result = self.validation_gate.validate_system_health(status)
                if health_result.issues:
                    for _issue in health_result.issues:
                        pass

            return 0

        except Exception as e:
            self.logger.exception(f"Status check failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_STATUS")
            return 1

    def handle_export(self, args) -> int:
        """Handle export command with validation."""
        try:
            self.logger.info(f"Executing export: {args.format} format")

            # Validate export parameters
            if args.format not in ["json", "csv", "markdown"]:
                msg = f"Unsupported export format: {args.format}"
                raise CHSError(msg)

            success = self.searcher.export_results(
                search_query=args.search_query,
                format=args.format,
                output_file=args.output,
            )

            if success:
                return 0
            return 1

        except Exception as e:
            self.logger.exception(f"Export failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e, context="CHS_EXPORT")
            return 1

    def _output_results(self, results, format_type, output_file, query) -> None:
        """Output search results in specified format."""
        if format_type == "json":
            output = json.dumps(results, indent=2, ensure_ascii=False)
        elif format_type == "markdown":
            output = f"# Search Results for: {query}\n\n"
            output += f"Found {len(results)} results\n\n"
            for i, result in enumerate(results, 1):
                timestamp = datetime.fromtimestamp(
                    result.get("timestamp", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
                output += f"## {i}. Score: {result.get('relevance_score', 0):.2f}\n\n"
                output += f"**Time:** {timestamp}\n\n"
                output += f"**Project:** {result.get('project', 'N/A')}\n\n"
                output += f"**Content:** {result.get('display', 'N/A')}\n\n"
                output += "---\n\n"
        else:
            output = f"Search Results for: {query}\n"
            output += f"Found {len(results)} results\n\n"
            for i, result in enumerate(results, 1):
                timestamp = datetime.fromtimestamp(
                    result.get("timestamp", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
                output += f"{i}. [{timestamp}] Score: {result.get('relevance_score', 0):.2f}\n"
                content = result.get("display", "")[:200]
                output += f"   {content}...\n\n"

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            pass

    def _integrate_with_taskmaster(self, query, results) -> None:
        """ToolRegistry integration removed to focus on core search functionality.

        Users can manually create tasks from search results using:
        tsk create --title "Task from search" --description "Query: {query}"
        """

    def _integrate_analysis_with_taskmaster(self, analysis) -> None:
        """ToolRegistry integration removed to focus on core search functionality.

        Users can manually create tasks from analysis insights using:
        tsk create --title "Chat pattern insights" --description "Analysis results available"
        """


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="chs",
        description="Chat History Search (CHS) - Advanced Cross-Session Chat Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chs search "archon search engines" --session-filter today
  chs analyze --pattern-analysis --trend-analysis
  chs index --rebuild
  chs status
  chs export --format markdown --output results.md
        """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="Available Commands",
        description="Commands for chat history search and analysis",
        help="Use 'chs <command> --help' for detailed help",
    )

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search chat history with intelligent filtering",
    )
    search_parser.add_argument(
        "query",
        help="Search query (natural language)",
    )
    search_parser.add_argument(
        "--session-filter",
        choices=["today", "yesterday", "week", "month", "all"],
        default="all",
        help="Filter by time period",
    )
    search_parser.add_argument(
        "--context-filter",
        choices=["project", "general", "technical", "all"],
        default="all",
        help="Filter by context type",
    )
    search_parser.add_argument(
        "--rank-by",
        choices=["relevance", "recency", "frequency"],
        default="relevance",
        help="Result ranking method",
    )
    search_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        help="Maximum number of results (default: 20)",
    )
    search_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format",
    )
    search_parser.add_argument(
        "--output",
        "-o",
        help="Output file (optional)",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze chat patterns and trends",
    )
    analyze_parser.add_argument(
        "--pattern-analysis",
        action="store_true",
        help="Include pattern analysis",
    )
    analyze_parser.add_argument(
        "--trend-analysis",
        action="store_true",
        help="Include trend analysis",
    )
    analyze_parser.add_argument(
        "--topic-modeling",
        action="store_true",
        help="Include topic modeling",
    )
    analyze_parser.add_argument(
        "--output",
        "-o",
        help="Output file for analysis results",
    )

    # Index command
    index_parser = subparsers.add_parser(
        "index",
        help="Index chat history for searching",
    )
    index_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild entire index from scratch",
    )

    # Status command
    subparsers.add_parser(
        "status",
        help="Show system status and health",
    )

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export search results or data",
    )
    export_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "markdown"],
        default="json",
        help="Export format",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        help="Output filename",
    )
    export_parser.add_argument(
        "--search-query",
        help="Export specific search results",
    )

    return parser


def main() -> int:
    """Main entry point for CHS command."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = create_parser()
    args = parser.parse_args()

    # Handle help
    if not args.command:
        parser.print_help()
        return 0

    # Initialize command interface
    try:
        chs_command = ChatHistoryCommand()
    except Exception as e:
        logging.exception(f"Failed to initialize CHS command: {e}")
        return 1

    # Route to appropriate handler
    if args.command == "search":
        return chs_command.handle_search(args)
    if args.command == "analyze":
        return chs_command.handle_analyze(args)
    if args.command == "index":
        return chs_command.handle_index(args)
    if args.command == "status":
        return chs_command.handle_status(args)
    if args.command == "export":
        return chs_command.handle_export(args)
    logging.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
