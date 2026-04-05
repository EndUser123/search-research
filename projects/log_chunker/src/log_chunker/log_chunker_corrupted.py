#!/usr/bin/env python
"""
Advanced Log Chunking Framework - Main Entry Point

A comprehensive, plugin-based system for intelligent log analysis and chunking.
"""

import argparse
import asyncio
import logging
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional  # Import Optional for type hints

# Import logging configuration
from logging_config import init_app_logging, get_logger

# Logger will be initialized after parsing CLI args
logger = None

# rprint alias for rich styling, falls back to standard print if rich not available
_rprint_global = print
try:
    from rich import print as _rich_print_alias  # Alias for rich's print
    from rich.console import Console
    from rich.panel import Panel
    _rprint_global = _rich_print_alias # Use rich print by default if rich is available
except ImportError:
    pass # rich not available, keep _rprint_global as standard print
rprint = _rprint_global # Set global alias for consistent printing

# Import adaptive config components
from adaptive_config import (
    AdaptiveChunker,
    ContentAnalysis,
    _merge_configs,
    display_analysis,
)
from chunking_engine import AdvancedChunkingEngine
from cli import create_cli_parser, create_config_from_args
from config import ChunkingConfig
from data_models import ChunkingResult
from reporter import AdvancedReporter


async def async_chunk_file(engine: AdvancedChunkingEngine, file_path: str) -> ChunkingResult:
    """Async wrapper for chunking, handling file I/O and CPU-bound operations."""

    try:
        # File I/O handling
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed for %s, trying with latin-1.", file_path)
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
        except UnicodeDecodeError as e:
            logger.error("Both UTF-8 and latin-1 decoding failed for file: %s. Error: %s", file_path, e)
            raise
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {file_path}. Error: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading input file {file_path}. Error: {e}")
        raise

    # Run CPU-bound chunking operations in a thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=engine.config.max_workers) as executor:
        result = await loop.run_in_executor(executor, engine.chunk_text, text)

    return result


def cleanup_chunks_directory(chunks_dir: Path, console: Optional[Console] = None) -> bool:
    """Clean up temporary chunk files after successful processing.

    Args:
        chunks_dir: Path to the chunks directory to clean up
        console: Optional Rich console for styled output

    Returns:
        True if cleanup succeeded, False otherwise
    """
    try:
        if chunks_dir.exists() and chunks_dir.is_dir():
            # Count files before cleanup
            chunk_files = list(chunks_dir.glob("*.md")) + list(chunks_dir.glob("*.txt")) + list(chunks_dir.glob("*.json"))
            file_count = len(chunk_files)

            if file_count > 0:
                # Remove all chunk files
                for file_path in chunk_files:
                    file_path.unlink()

                # Try to remove directory if empty (but don't fail if it's not empty)
                try:
                    if not any(chunks_dir.iterdir()):  # Check if directory is empty
                        chunks_dir.rmdir()
                        if console:
                            console.print(f"🧹 Cleaned up {file_count} temporary chunk files and removed empty chunks directory", style="dim green")
                        else:
                            logger.info(f"Cleaned up {file_count} temporary chunk files and removed empty chunks directory")
                    else:
                        if console:
                            console.print(f"🧹 Cleaned up {file_count} temporary chunk files (chunks directory kept - contains other files)", style="dim green")
                        else:
                            logger.info(f"Cleaned up {file_count} temporary chunk files (chunks directory kept - contains other files)")
                except OSError:
                    # Directory not empty or other issue, just clean files
                    if console:
                        console.print(f"🧹 Cleaned up {file_count} temporary chunk files", style="dim green")
                    else:
                        logger.info(f"Cleaned up {file_count} temporary chunk files")
            else:
                if console:
                    console.print("🧹 No temporary chunk files to clean up", style="dim green")
                else:
                    logger.info("No temporary chunk files to clean up")

            return True

    except Exception as e:
        error_msg = f"Failed to cleanup chunks directory: {e}"
        if console:
            console.print(f"⚠️  {error_msg}", style="yellow")
        else:
            logger.warning(error_msg)
        return False

    return True


def analyze_content_only(file_path: str, console_instance: Optional[Console]):
    """Analyzes content and displays recommendations without performing chunking.
    Takes a console instance to use for rich output if available.
    """
    if not Path(file_path).is_file():
        rprint(f"[bold red]Error: File '{file_path}' not found or is not a file.[/bold red]")
        sys.exit(1)

    try:
        # Read a sample of the file for analysis
        with open(file_path, 'r', encoding='utf-8') as f:
            sample_text = f.read(50000)  # Read first 50KB for analysis
    except UnicodeDecodeError:
        rprint(f"[yellow]UTF-8 decode failed for {file_path}, trying with latin-1.[/yellow]")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                sample_text = f.read(50000)
        except UnicodeDecodeError as e:
            rprint(f"[bold red]Error: Both UTF-8 and latin-1 decoding failed for file: {file_path}. Error: {e}[/bold red]")
            sys.exit(1)
    except IOError as e:
        rprint(f"[bold red]Error reading input file {file_path}. Error: {e}[/bold red]")
        sys.exit(1)

    adaptive_chunker = AdaptiveChunker()
    analysis: ContentAnalysis = adaptive_chunker.analyze_and_recommend(sample_text)

    # Display analysis uses the passed console instance
    if console_instance:
        display_analysis(analysis, console_instance)
    else:
        # Fallback for non-rich display
        print(f"\n--- Content Analysis for {file_path} ---")
        print(f"Content Type: {analysis.content_type} (Confidence: {analysis.confidence:.1%})")
        print("Recommended Configuration Changes:")
        default_config = ChunkingConfig()
        for field_name, recommended_value in analysis.recommended_config.model_dump().items():
            if recommended_value != getattr(default_config, field_name):
                print(f"  - {field_name}: {recommended_value}")
        print("Reasoning:")
        for reason in analysis.reasoning:
            print(f"  - {reason}")

    # Show recommended command (reconstructed for clarity)
    rprint("\n[INFO] [bold green]Recommended command for optimized chunking:[/bold green]")

    # Build the command string based on recommended settings that differ from defaults
    cmd_parts = ["python log_chunker.py", f'"{file_path}"']

    default_config = ChunkingConfig()
    rec_config = analysis.recommended_config

    # Iterate over all configurable fields and add to command if different from default
    # This ensures a comprehensive command
    for field_name, default_value in default_config.model_dump().items():
        rec_value = getattr(rec_config, field_name)

        # Skip internal flags that aren't CLI args or are handled separately
        if field_name in ['no_adaptive', 'auto_optimize', 'tokenizer_type', 'tokens_per_char', 'log_parsing_patterns', 'advanced_detection_patterns', 'plugin_weights', 'analysis_results']:
            continue

        # Boolean flags handled with --no-flag or --flag
        if isinstance(default_value, bool):
            if rec_value != default_value:
                if rec_value: # True
                    # Check for specific `--enable-X` flags if they exist in CLI parser.
                    # Otherwise, a generic `--enable-field` is not typical.
                    # Best to handle these based on CLI definition.
                    if field_name.startswith('enable_'):
                        cmd_parts.append(f"--{field_name.replace('_', '-')}")
                    elif field_name == 'use_gpu':
                        cmd_parts.append("--use-gpu") # If user wants to force GPU
                    elif field_name == 'save_metadata': # if save_metadata is False, it's --no-metadata
                        pass # Handled below by `--no-metadata`
                    elif field_name == 'rich_display': # if rich_display is False, it's `--no-rich`
                        pass # Handled below by `--no-rich`
                    # For plugins, a generic --disable-X flag might be needed in CLI parser
                    elif field_name.startswith('enable_') and field_name != 'enable_deduplication':
                        cmd_parts.append(f"--disable-{field_name.replace('enable_', '')}") # e.g., --disable-semantic
        # List of enabled plugins is handled specially
        elif field_name == 'enabled_plugins':
            if set(rec_value) != set(default_config.enabled_plugins): # If the set of plugins differs
                if not rec_value: # If no plugins recommended
                    cmd_parts.append("--disable-all-plugins")
                else:
                    # Add explicit enables for each recommended plugin
                    for plugin_name in rec_value:
                        # Only add --enable-X if X is not pattern, as pattern is special
                        if plugin_name != 'pattern':
                            cmd_parts.append(f"--enable-{plugin_name}")
                    # Add --disable-pattern if pattern is not in recommended but was default
                    if 'pattern' in default_config.enabled_plugins and 'pattern' not in rec_value:
                        cmd_parts.append("--disable-pattern")
        # Other simple type differences
        elif rec_value != default_value:
            # Re-map names if CLI arg name differs from config field name
            cli_arg_name = field_name
            if field_name == 'time_window_minutes': cli_arg_name = 'time_window'

            cmd_parts.append(f"--{cli_arg_name.replace('_', '-')}")
            if isinstance(rec_value, float):
                cmd_parts.append(f"{rec_value:.2f}") # Format floats
            else:
                cmd_parts.append(f"{rec_value}")

    rprint(f"[green]{' '.join(cmd_parts)}[/green]")


def main() -> int:
    """Main entry point for the Advanced Log Chunking Framework."""

    # --- Step 0: Initial setup and special command handling ---

    # Parse arguments first to determine command and logging/display settings
    parser = create_cli_parser()
    args = parser.parse_args() # args is now available for all top-level logic

    # Initialize modern logging system
    log_dir = Path(__file__).parent / "logs"
    init_app_logging(verbose=args.verbose, quiet=args.quiet, log_dir=str(log_dir))
    logger = get_logger(__name__)

    # Determine the console instance for `rich` output, respecting `--no-rich`
    current_console: Optional[Console] = None
    if not args.no_rich:
        try:
            # Local import for Console class after args are parsed
            from rich.console import Console
            current_console = Console()
        except ImportError:
            # rich not available, but user didn't explicitly disable. Warn.
            print(
                "WARNING: Rich display requested but 'rich' package not found. Falling back to plain text output.",
                file=sys.stderr
            )
            # current_console remains None

    # Display header for initial execution.
    # This header is displayed regardless of whether rich is available, but styled if it is.
    if current_console:
        current_console.print(Panel.fit(
            "[INFO] Advanced Log Chunking Framework\n"
            "Intelligent chunking with ML-powered plugins",
            style="bold blue"
        ))
    else:
        logger.info("Advanced Log Chunking Framework - Starting...")


    # --- Handle Special Commands (mutually exclusive with main chunking) ---
    # These commands are identified by their specific first positional argument.
    if hasattr(args, 'input_file') and args.input_file: # Check if a positional arg was given
        command = args.input_file.lower() # Treat the first positional arg as the command

        if command == 'validate':
            return 0 if validate_installation() else 1
        elif command == 'sample-config':
            create_sample_config()
            return 0
        elif command == 'create-plugin':
            # create-plugin expects a second positional arg (the plugin name)
            # sys.argv is used here because argparse already consumed args.input_file
            if len(sys.argv) > (sys.argv.index(command) + 1):
                plugin_name = sys.argv[sys.argv.index(command) + 1]
                create_plugin_template(plugin_name)
                return 0
            else:
                rprint("[bold red]Usage: python log_chunker.py create-plugin <plugin_name>[/bold red]")
                return 1
        elif command == 'analyze':
            # analyze expects a second positional arg (the file path)
            if len(sys.argv) > (sys.argv.index(command) + 1):
                file_path_for_analyze = sys.argv[sys.argv.index(command) + 1]
                analyze_content_only(file_path_for_analyze, current_console) # Pass current_console
                return 0
            else:
                rprint("[bold red]Usage: python log_chunker.py analyze <log_file_path>[/bold red]")
                return 1

    # If we reach here, it means no special command was detected,
    # so args.input_file should be treated as the log file path for chunking.
    if not args.input_file: # If no positional argument was provided at all (e.g., `python log_chunker.py`)
        rprint("[bold red]Error: No input file specified for chunking. Use 'python log_chunker.py <file_path>' or 'python log_chunker.py analyze <file_path>'.[/bold red]")
        parser.print_help() # Display help if no command/file is given
        return 1

    # Validate input file existence for main chunking operation
    if not Path(args.input_file).is_file():
        logger.error(f"Input file not found or is not a file: {args.input_file}")
        return 1

    # Load base configuration (from file or CLI args)
    config: ChunkingConfig
    try:
        if args.config:
            # If a config file is specified, load it.
            # Then, apply any non-default CLI arguments on top of this loaded config.
            # create_config_from_args reads defaults from ChunkingConfig, then applies args.
            # If `args.config` is used, it's meant to load a *default* state, then args override.
            # A more complex merge would be needed if file config must override CLI defaults.
            # For now, this is simpler: CLI args take precedence.
            config = create_config_from_args(args) # This will create a config primarily from args, with defaults for unset args.

        else:
            # If no config file, create config directly from CLI args and ChunkingConfig defaults
            config = create_config_from_args(args)
    except (FileNotFoundError, ValueError, Exception) as e:
        logger.error(f"Failed to load configuration: {e}")
        if args.verbose:
            logger.exception("Detailed configuration loading error:")
        return 1

    # --- Step 2: Adaptive Configuration (if enabled) ---
    # The 'config' object here is the *base* config (from file or CLI args).
    # Adaptive config will generate a 'recommended' config, and then merge it with this base,
    # respecting overrides from the base (i.e., user-explicit settings).
    analysis_results_for_chunking: Optional[ContentAnalysis] = None
    if not config.no_adaptive:
        try:
            adaptive_chunker = AdaptiveChunker()
            # Read a sample of the file for analysis
            with open(args.input_file, 'r', encoding='utf-8') as f:
                sample_text = f.read(50000)  # Read first 50KB for analysis

            analysis = adaptive_chunker.analyze_and_recommend(sample_text)
            analysis_results_for_chunking = analysis # Store the analysis result

            # Display recommendations and ask user
            if current_console:
                display_analysis(analysis, current_console) # Use current_console

                if not config.auto_optimize:
                    response = current_console.input("\n[INFO] [bold blue]Apply recommended configuration? (y/N):[/bold blue] ").lower().strip()
                    if response in ['y', 'yes']:
                        config = _merge_configs(config, analysis.recommended_config) # Merge base with recommended
                        current_console.print("[OK] [bold green]Applied recommended configuration.[/bold green]")
                    else:
                        current_console.print("[INFO] [bold yellow]Using original configuration.[/bold yellow]")
                else:
                    config = _merge_configs(config, analysis.recommended_config) # Auto-merge
                    current_console.print("[INFO] [bold green]Auto-applied optimized configuration.[/bold green]")
            else: # Non-rich display
                logger.info(f"Adaptive analysis suggests content type: {analysis.content_type}")
                if config.auto_optimize:
                    config = _merge_configs(config, analysis.recommended_config)
                    logger.info("Auto-applied optimized configuration.")
                else:
                    logger.info("Recommendations available. Use --auto-optimize to apply or review logs for details.")

        except Exception as e:
            logger.warning(f"Adaptive configuration failed: {e}. Proceeding with current settings.")
            logger.exception("Detailed adaptive configuration error:")

    # Create output directories with absolute paths relative to script location
    script_dir = Path(__file__).parent.absolute()

    # Use provided paths or default to script directory
    chunks_dir = Path(args.output_dir).absolute() if args.output_dir else script_dir / "chunks"
    reports_dir = Path(args.reports_dir).absolute() if args.reports_dir else script_dir / "reports"

    try:
        chunks_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Error: Failed to create output directories: {e}")
        return 1

    base_name = Path(args.input_file).stem

    # --- Step 3: Main Chunking Process ---
    try:
        # Initialize chunking engine, passing the current_console instance
        engine = AdvancedChunkingEngine(config, current_console)

        # Load external plugins if specified
        if args.plugin:
            for plugin_path in args.plugin:
                try:
                    engine.plugin_manager.load_external_plugin(plugin_path)
                except Exception as e:
                    logger.error(f"Error: Failed to load external plugin '{plugin_path}': {e}")
                    if args.verbose:
                        logger.exception("Detailed external plugin loading error:")

        if current_console:
            current_console.print(f"[INFO] Processing file: [bold cyan]{args.input_file}[/bold cyan]")
            current_console.print(f"[INFO] Target tokens per chunk: [bold magenta]{config.target_tokens:,}[/bold magenta]")
            active_plugins = list(engine.plugin_manager.plugins.keys())
            current_console.print(f"[INFO] Active plugins: [bold green]{', '.join(active_plugins) if active_plugins else 'None'}[/bold green]")
        else:
            logger.info(f"Processing file: {args.input_file}")
            logger.info(f"Target tokens per chunk: {config.target_tokens:,}")
            active_plugins = list(engine.plugin_manager.plugins.keys())
            logger.info(f"Active plugins: {', '.join(active_plugins) if active_plugins else 'None'}")

        # Run chunking pipeline
        result = asyncio.run(async_chunk_file(engine, args.input_file))

        # Attach adaptive analysis results to the final ChunkingResult for reporting
        result.analysis_results = analysis_results_for_chunking

        # Display and save results
        reporter = AdvancedReporter(current_console) # Pass current_console

        if current_console:
            reporter.display_chunking_results(result)
        else:
            # Fallback for non-rich display
            print("\n--- Chunking Summary ---")
            print(f"Created {len(result.chunks)} chunks in {result.total_processing_time:.2f}s")
            print(f"Average chunk size: {result.quality_metrics.get('avg_chunk_size', 0):.0f} tokens")
            print(f"Overall quality score: {result.quality_metrics.get('avg_quality_score', 0):.2f}/1.0")
            print(f"Processed lines: {result.preprocessing_stats['processed_lines']:,} (Original: {result.preprocessing_stats['original_lines']:,})")

        if config.save_metadata:
            reporter.save_detailed_report(result, chunks_dir, reports_dir, base_name, args.llm_tokens)

            # Clean up temporary chunk files after successful report generation
            if not args.keep_chunks:
                cleanup_chunks_directory(chunks_dir, current_console)
        else:
            logger.info("Skipping metadata and detailed report saving (--no-metadata enabled).")
            # Still clean up chunks even if no reports saved (unless explicitly keeping them)
            if not args.keep_chunks:
                cleanup_chunks_directory(chunks_dir, current_console)

        # Cleanup engine resources (e.g., ML models loaded by plugins)
        engine.cleanup()

        if current_console:
            current_console.print("[DONE] Chunking completed successfully!", style="bold green")
        else:
            logger.info("Chunking completed successfully!")

        return 0

    except KeyboardInterrupt:
        if current_console:
            current_console.print("\n[ERROR] Chunking interrupted by user (KeyboardInterrupt).", style="bold red")
        else:
            print("\nChunking interrupted by user.")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred during chunking: {e}")
        if args.verbose:
            logger.exception("Detailed error trace:")
        if current_console:
            current_console.print(f"\n[ERROR] Chunking failed due to an unexpected error: [red]{e}[/red]", style="bold red")
        return 1


# --- Special Command Handlers (called from main) ---
# These functions should use the global `rprint` alias which is initialized based on rich availability.

def validate_installation() -> bool:
    """Validate that all required and optional packages are installed."""

    rprint("[bold blue]--- Validating Advanced Log Chunking Framework Installation ---")

    required_packages = {
        'rich': 'Rich terminal output',
        'pydantic': 'Data validation and settings management',
        'numpy': 'Numerical operations'
    }

    optional_packages = {
        'torch': 'PyTorch (for Perplexity/Semantic plugins)',
        'transformers': 'Hugging Face transformers (for Perplexity plugin)',
        'sentence_transformers': 'Sentence embeddings (for Semantic plugin)',
        'sklearn': 'Scikit-learn (for Temporal/Semantic plugins)',
        'scipy': 'Scientific computing (for Temporal plugin)',
        'langdetect': 'Language detection (for Preprocessor)',
        'fuzzywuzzy': 'Fuzzy string matching (for Preprocessor deduplication)',
        'python-levenshtein': 'C-optimized Levenshtein distance for fuzzywuzzy'
    }

    missing_required = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            rprint(f"[OK] [bold green]{package}[/bold green]: {description}")
        except ImportError:
            rprint(f"[ERROR] [bold red]{package}[/bold red]: {description} - [bold red]REQUIRED[/bold red]")
            missing_required.append(package)

    missing_optional = []
    for package, description in optional_packages.items():
        try:
            __import__(package)
            rprint(f"[OK] [green]{package}[/green]: {description}")
        except ImportError:
            rprint(f"[WARNING]  [yellow]{package}[/yellow]: {description} - [yellow]OPTIONAL[/yellow]")
            missing_optional.append(package)

    if missing_required:
        rprint(f"\n[bold red]Error: Missing required packages: {', '.join(missing_required)}[/bold red]")
        rprint("Please install them with: [cyan]pip install " + " ".join(missing_required) + "[/cyan]")
        return False
    elif missing_optional:
        rprint("\n[bold yellow]Note: Optional packages not found. Some advanced features might be disabled.[/bold yellow]")
        rprint("To enable full features, install with: [cyan]pip install " + " ".join(missing_optional) + "[/cyan]")

    rprint("\n[DONE] [bold green]Core framework dependencies are satisfied![/bold green]")
    return True


def create_sample_config():
    """Create a sample configuration file."""

    config = ChunkingConfig(
        target_tokens=75000,
        max_tokens=100000,
        overlap_ratio=0.2,
        enable_semantic=True,
        enable_perplexity=False,  # Perplexity requires more resources, default to off in sample
        enable_temporal=True,
        enable_conversation=True,
        semantic_threshold=0.25,
        dedup_threshold=3,
        fuzzy_threshold=90,
        batch_size=16,
        use_gpu=False  # Set to True if you have GPU
    )

    # Use argparse for output path consistent with other CLI commands
    parser = argparse.ArgumentParser(description="Generate a sample config file.")
    parser.add_argument(
        "--output",
        type=str,
        default="sample_config.json",
        help="Path to save the sample config file (default: sample_config.json)"
    )
    # Parse only known args to allow other potential args to be present without error
    args, _ = parser.parse_known_args()

    output_path = Path(args.output)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Use model_dump_json for pretty printing and Pydantic V2 compatibility
            f.write(config.model_dump_json(indent=2))
        rprint(f"Sample configuration saved to [bold green]{output_path}[/bold green]")
    except OSError as e:
        rprint(f"[bold red]Error: Failed to write sample config to {output_path}: {e}[/bold red]", file=sys.stderr)


def create_plugin_template(plugin_name: str):
    """Create a template for a new plugin."""

    # Sanitize plugin name for class and file naming
    safe_plugin_name = ''.join(c for c in plugin_name.title() if c.isalnum())

    template = (
        "#!/usr/bin/env python\n"
        """\n"""  # Triple double quotes for docstring
        "Custom Chunking Plugin: " + plugin_name + "\n"
        """\n"""  # Closing triple double quotes
        "\n"  # Blank line
        "from typing import List\n"
        "from plugins.base import BaseChunkingPlugin\n"
        "from data_models import LogEntry, ChunkInfo\n"
        "from config import ChunkingConfig # For type hinting configuration\n"
        "from rich.console import Console # For logging within the plugin\n"
        "\n"
        "\n"
        "class " + safe_plugin_name + "Plugin(BaseChunkingPlugin):\n"
        "    """Custom chunking plugin: " + plugin_name + """"\n"  # Docstring for the class
        "    \n"
        "    name = "" + plugin_name.lower() + "" # Lowercase name for config/identification\n"
        "    version = "1.0.0"\n"
        "    dependencies = []  # List any required pip packages (e.g., ["tensorflow", "spacy"])\n"
        "    \n"
        "    def initialize(self, config: ChunkingConfig, console: Console) -> bool:\n"
        "        """\n"
        "        Initialize plugin with configuration and console.\n"
        "        This method is called once when the plugin is loaded.\n"
        "        Perform expensive setup (e.g., model loading) here.\n"
        "        Return False if initialization fails (e.g., missing dependencies).\n"
        "        """\n"
        "        # Call the base class initializer\n"
        "        super().initialize(config, console) # Pass console to base class\n"
        "        \n"
        "        self.console.log(f"[bold green]Initializing {{self.name}} plugin...[/bold green]")\n"
        "        \n"
        "        try:\n"
        "            # --- Add your plugin-specific initialization logic here ---\n"
        "            # Access configuration: self.config.my_setting\n"
        "            # Log messages: self.console.log('...') or logger.info('...')\n"
        "            \n"
        "            # Example: Load a custom model (if external dependency is installed)\n"
        "            # # if "my_model_lib" in self.dependencies:\n"
        "            # #     try:\n"
        "            # #         import my_model_lib\n"
        "            # #         self.custom_model = my_model_lib.load(self.config.my_custom_model_path) # Assumes custom_model_path in config\n"
        "            # #     except ImportError:\n"
        "            # #         self.console.log("[yellow]Warning: MyModelLib not installed. This plugin might not function fully.[/yellow]")\n"
        "            # #         return False # Or handle gracefully\n"
        "            # \n"
        "            self.console.log(f"[bold green]{{self.name}} plugin initialized successfully.[/bold green]")\n"
        "            return True\n"
        "        except Exception as e:\n"
        "            self.console.log(f"[bold red]Error initializing {{self.name}} plugin: {{e}}[/bold red]")\n"
        "            # Log full traceback for debugging during development\n"
        "            import logging\n"
        "            logger = logging.getLogger(__name__)\n"
        "            logger.exception(f"Exception during {{self.name}} plugin initialization:")\n"
        "            return False # Indicate initialization failure\n"
        "    \n"
        "    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:\n"
        "        """\n"
        "        Find chunk boundaries in the log entries.\n"
        "        \n"
        "        This method is called for each log file.\n"
        "        \n"
        "        Args:\n"
        "            text (str): The full preprocessed log text.\n"
        "            log_entries (List[LogEntry]): A list of parsed LogEntry objects.\n"
        "            \n"
        "        Returns:\n"
        "            List[int]: A list of line indices (0-based) where new chunks should start.\n"
        "                       These indices refer to `log_entries` and `text.split('\n')`.\n"
        "                       For example, [0, 10, 25] means chunks start at line 0, 10, and 25.\n"
        "        """\n"
        "        boundaries = []\n"
        "        \n"
        "        self.console.log(f"[dim]Running {{self.name}} boundary detection...[/dim]")\n"
        "        \n"
        "        # --- Add your boundary detection logic here ---\n"
        "        # # Example: Simple boundary every 100 lines (for demonstration)\n"
        "        # # for i in range(0, len(log_entries), 100):\n"
        "        # #    if i != 0: # Don't add 0 if it's not explicitly a boundary from this plugin\n"
        "        # #        boundaries.append(i)\n"
        "        # \n"
        "        # # Example: Boundary when a specific keyword appears\n"
        "        "        # # for i, entry in enumerate(log_entries):\n"
        "        # #     if "CRITICAL ERROR" in entry.message:\n"
        "        # #         boundaries.append(i)\n"
        "        # \n"
        "        self.console.log(f"[dim]{{self.name}} found {{len(boundaries)}} boundaries.[/dim]")\n"
        "        return sorted(list(set(boundaries))) # Ensure boundaries are unique and sorted\n"
        "    \n"
        "    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:\n"
        "        """\n"
        "        Score the quality of a given chunk (0.0 to 1.0).\n"
        "        Higher scores indicate better quality (e.g., more coherent, less noise).\n"
        "        \n"
        "        Args:\n"
        "            chunk (str): The raw text content of the chunk.\n"
        "            info (ChunkInfo): Metadata about the chunk.\n"
        "            \n"
        "        Returns:\n"
        "            float: A score between 0.0 and 1.0.\n"
        "        """\n"
        "        # --- Add your chunk scoring logic here ---\n"
        "        # # Example: Score based on number of lines\n"
        "        # # score = min(1.0, info.original_lines / self.config.target_lines_per_chunk)\n"
        "        # \n"
        "        # # Example: Score based on presence of certain patterns\n"
        "        "        # # if "error_start" in info.detected_patterns:\n"
        "        # #     score = 0.2 # Lower score for error-only chunks perhaps\n"
        "        # # else:\n"
        "        # #     score = 0.8\n"
        "        # \n"
        "        return 0.5  # Default neutral score if no specific logic\n"
        "    \n"
        "    def cleanup(self) -> None:\n"
        "        """\n"
        "        Cleanup any resources used by the plugin (e.g., close model connections, free memory).\n"
        "        This method is called when the framework shuts down.\n"
        "        """\n"
        "        self.console.log("[dim]Cleaning up {self.name} plugin resources...[/dim]")\n"
        "        # --- Add your cleanup logic here ---\n"
        "        # # if hasattr(self, 'custom_model') and self.custom_model:\n"
        "        # #    del self.custom_model\n"
        "        # #    import torch; torch.cuda.empty_cache() # If using PyTorch\n"
        "        pass\n"
    )

    filename = f"{plugin_name.lower()}_plugin.py"
    output_path = Path(filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template)
        rprint(f"Plugin template created: [bold green]{output_path}[/bold green]")
        rprint(f"Edit the file and use with: [cyan]python log_chunker.py logs.txt --plugin {output_path}[/cyan]")
    except OSError as e:
        rprint(f"[bold red]Error: Failed to write plugin template to {output_path}: {e}[/bold red]", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())
