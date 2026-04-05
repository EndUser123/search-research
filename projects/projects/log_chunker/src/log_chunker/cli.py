"""Command line interface for the chunking framework."""

import argparse

from .config import HAS_PYDANTIC, ChunkingConfig


def create_cli_parser() -> argparse.ArgumentParser:
    """Create comprehensive CLI parser with subcommands."""

    parser = argparse.ArgumentParser(
        description="Advanced Log Chunking Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a log file and generate an intelligence report"
    )
    analyze_parser.add_argument("input_file", help="Input log file path")
    add_common_args(analyze_parser)

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate a report from a cached IntelligenceReport"
    )
    report_parser.add_argument(
        "input_file", help="Path to the cached IntelligenceReport JSON file"
    )
    report_parser.add_argument(
        "--type",
        default="summary",
        choices=["summary", "full", "json"],
        help="Type of report to generate",
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Configuration commands"
    )
    config_subparsers.add_parser("sample", help="Generate a sample configuration file")

    return parser


def add_common_args(parser: argparse.ArgumentParser):
    """Add common arguments to a parser."""

    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Output directory for temporary chunk files",
    )
    parser.add_argument(
        "--reports-dir",
        default=None,
        help="Output directory for final reports and analysis files",
    )
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="Keep temporary chunk files after processing",
    )
    parser.add_argument("--config", help="Path to a JSON configuration file")
    parser.add_argument(
        "-t", "--target-tokens", type=int, help="Target number of tokens per chunk"
    )
    parser.add_argument(
        "-m", "--max-tokens", type=int, help="Maximum allowed tokens per chunk"
    )
    parser.add_argument(
        "-r",
        "--overlap-ratio",
        type=float,
        help="Ratio of overlap between consecutive chunks",
    )
    parser.add_argument(
        "--enable-semantic",
        action="store_true",
        help="Enable the Semantic chunking plugin",
    )
    parser.add_argument(
        "--enable-perplexity",
        action="store_true",
        help="Enable the Perplexity chunking plugin",
    )
    parser.add_argument(
        "--enable-temporal",
        action="store_true",
        help="Enable the Temporal chunking plugin",
    )
    parser.add_argument(
        "--enable-conversation",
        action="store_true",
        help="Enable the Conversation chunking plugin",
    )
    parser.add_argument(
        "--disable-pattern",
        action="store_true",
        help="Disable the default pattern chunking plugin.",
    )
    parser.add_argument(
        "--disable-all-plugins",
        action="store_true",
        help="Disable all built-in chunking plugins",
    )
    parser.add_argument(
        "--no-dedup", action="store_true", help="Disable smart log deduplication"
    )
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU usage")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip saving metadata and detailed reports",
    )
    parser.add_argument(
        "--no-rich", action="store_true", help="Disable rich terminal output"
    )
    parser.add_argument("--quiet", action="store_true", help="Minimal logging output")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging output"
    )
    parser.add_argument(
        "--no-adaptive",
        action="store_true",
        help="Disable adaptive configuration suggestions.",
    )
    parser.add_argument(
        "--auto-optimize",
        action="store_true",
        default=True,
        help="Automatically apply optimized configuration",
    )
    parser.add_argument(
        "--no-auto-optimize", action="store_true", help="Disable automatic optimization"
    )
    parser.add_argument("--plugin", action="append", help="Load external plugin file")


def create_config_from_args(args: argparse.Namespace) -> ChunkingConfig:
    """Create configuration from command line arguments, using defaults from ChunkingConfig."""

    # Create a default config instance to get default values
    if HAS_PYDANTIC:
        default_config = ChunkingConfig.model_validate({})
        config_data = default_config.model_dump()

        for field_name, field_info in ChunkingConfig.model_fields.items():
            if hasattr(args, field_name) and getattr(args, field_name) is not None:
                if field_name == "time_window":
                    config_data["time_window_minutes"] = getattr(args, field_name)
                else:
                    config_data[field_name] = getattr(args, field_name)
    else:
        # Dataclass fallback
        default_config = ChunkingConfig()
        config_data = default_config.__dict__.copy()

        # Apply command line arguments
        for arg_name in vars(args):
            arg_value = getattr(args, arg_name)
            if arg_value is not None and hasattr(default_config, arg_name):
                config_data[arg_name] = arg_value

    if hasattr(args, "disable_all_plugins") and args.disable_all_plugins:
        config_data["enabled_plugins"] = []
    elif hasattr(args, "enable_semantic"):  # Check if plugin flags are present
        explicit_plugin_flags_set = any(
            [
                args.enable_semantic,
                args.enable_perplexity,
                args.enable_temporal,
                args.enable_conversation,
            ]
        )
        if explicit_plugin_flags_set:
            enabled_from_cli = []
            if args.enable_semantic:
                enabled_from_cli.append("semantic")
            if args.enable_perplexity:
                enabled_from_cli.append("perplexity")
            if args.enable_temporal:
                enabled_from_cli.append("temporal")
            if args.enable_conversation:
                enabled_from_cli.append("conversation")

            if not args.disable_pattern:
                if "pattern" not in enabled_from_cli:
                    enabled_from_cli.append("pattern")

            config_data["enabled_plugins"] = enabled_from_cli
        else:
            default_plugins = default_config.enabled_plugins
            if args.disable_pattern and "pattern" in default_plugins:
                default_plugins.remove("pattern")
            config_data["enabled_plugins"] = default_plugins

    if hasattr(args, "no_dedup") and args.no_dedup:
        config_data["enable_deduplication"] = False
    if hasattr(args, "no_gpu") and args.no_gpu:
        config_data["use_gpu"] = False
    if hasattr(args, "no_metadata") and args.no_metadata:
        config_data["save_metadata"] = False
    if hasattr(args, "no_rich") and args.no_rich:
        config_data["rich_display"] = False

    if hasattr(args, "no_adaptive"):
        config_data["no_adaptive"] = args.no_adaptive
    if hasattr(args, "auto_optimize") and hasattr(args, "no_auto_optimize"):
        config_data["auto_optimize"] = args.auto_optimize and not args.no_auto_optimize

    if HAS_PYDANTIC:
        return ChunkingConfig(**config_data)
    else:
        return ChunkingConfig(**config_data)


def main():
    """CLI entry point - delegates to the real main function."""
    from log_chunker.log_chunker import main as real_main

    return real_main()


if __name__ == "__main__":
    main()
