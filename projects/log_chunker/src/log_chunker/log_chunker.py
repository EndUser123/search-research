"""
Advanced Log Chunking Framework - Main Entry Point

A comprehensive, plugin-based system for intelligent log analysis and chunking.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# Import core components
from .adaptive_config import AdaptiveChunker, _merge_configs
from .chunking_engine import ChunkingEngine
from .cli import create_cli_parser, create_config_from_args
from .data_models import ChunkingResult, IntelligenceEngine
from .enhanced_progress import EnhancedDisplaySystem

# Import logging configuration
from .logging_config import get_logger, init_app_logging
from .reporter import Reporter

logger = get_logger(__name__)


def setup_console() -> Console:
    """Setup Rich console."""
    return Console(record=True, width=120)


def display_header(console: Console):
    """Display application header."""
    console.print(
        Panel.fit(
            "🚀 Advanced Log Chunking Framework\n"
            "Intelligent chunking with ML-powered plugins",
            style="bold blue",
        )
    )


def main() -> int:
    """Main entry point for the Advanced Log Chunking Framework."""
    parser = create_cli_parser()
    args = parser.parse_args()

    log_dir = Path(__file__).parent / "logs"
    init_app_logging(verbose=args.verbose, quiet=args.quiet, log_dir=str(log_dir))

    console = setup_console()
    display_header(console)

    display_system = EnhancedDisplaySystem(console)

    if args.command == "analyze" or args.command is None:
        try:
            config = create_config_from_args(args)

            if not config.no_adaptive:
                adaptive_chunker = AdaptiveChunker()
                try:
                    with open(args.input_file, encoding="utf-8", errors="ignore") as f:
                        sample_content = f.read(50000)

                    (
                        recommended_config,
                        analysis_data,
                    ) = adaptive_chunker.analyze_and_recommend(config, sample_content)
                    display_system.display_content_analysis(analysis_data)

                    if recommended_config and config.auto_optimize:
                        config = _merge_configs(config, recommended_config)
                        display_system.display_simple_status(
                            "🤖 Auto-applied optimized configuration", "green"
                        )
                except Exception as e:
                    logger.warning(f"Content analysis failed: {e}")

            intelligence_engine = IntelligenceEngine(config, console)
            chunking_engine = ChunkingEngine(config, console, display_system)

            display_system.display_simple_status(
                f"Starting processing: {args.input_file}", "cyan"
            )
            chunks, preprocessing_stats = chunking_engine.chunk_file(
                args.input_file, intelligence_engine
            )

            with display_system.track_intelligence_generation(len(chunks)):
                report = intelligence_engine.analyze(
                    chunks, preprocessing_stats, args.input_file
                )

            result = ChunkingResult(
                chunks=chunks,
                intelligence_report=report,
                total_processing_time=0.0,
                config_used=config,
                preprocessing_stats=preprocessing_stats,
                quality_metrics={},
            )

            with display_system.track_report_saving():
                reporter = Reporter(console)
                reporter.save_intelligence_report(
                    report, Path(args.reports_dir), config
                )

            display_system.display_final_summary(result)

            console.print("🎉 Analysis completed successfully!", style="bold green")
            with open("rich_output.log", "w", encoding="utf-8") as f:
                f.write(console.export_text())
            return 0

        except Exception as e:
            logger.error(
                f"An unexpected error occurred during analysis: {e}", exc_info=True
            )
            console.print(f"[red]Error: {e}[/red]")
            return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
