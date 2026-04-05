# FILE: ichs/cli.py
# CLI entry point exposing run, list-checks, and report using argparse.
from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm  # type: ignore[import-untyped]

from . import runner
from .check_registry import available as available_checks
from .check_registry import get as get_check
from .cli_config import load_config_file
from .config import EnhancedConfig as Config
from .database import Database
from .diagnostics import Diagnostics
from .parsers import ruff as ruff_parser
from .report import generate_report as generate_simple_report
from .reporting import Reporting
from .synthesis import Synthesis
from .trends import Trends

logger = logging.getLogger(__name__)


# ---------------------------
# Utilities
# ---------------------------


def _ensure_dirs(path: str | None) -> None:
    """Create parent directories for the given output path if provided."""
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)


def _resolve_sys_config(cli_cfg_path: str | None) -> tuple[dict[str, Any], Config]:
    """Load CLI configuration and bridge to EnhancedConfig.

    Args:
        cli_cfg_path: Optional explicit path to YAML/JSON CLI config.

    Returns:
        A tuple of (cli_config_dict, system_config_instance)
    """
    cfg_data = load_config_file(cli_cfg_path)
    sys_cfg = Config("ichs.toml")
    db_path = cfg_data.get("database", {}).get("path")
    if db_path:
        # Allow CLI YAML/JSON to override DB path used by EnhancedConfig consumers.
        sys_cfg.database_path = db_path
    return cfg_data, sys_cfg


def _build_services(sys_cfg: Config) -> tuple[Database, Reporting]:
    """Construct core services (Database, Reporting with its deps).

    Args:
        sys_cfg: The system config.

    Returns:
        Tuple of (Database, Reporting)
    """
    db = Database(sys_cfg)
    syn = Synthesis(sys_cfg, db)
    tr = Trends(sys_cfg, db)
    diag = Diagnostics(sys_cfg, db)
    reporter = Reporting(sys_cfg, db, syn, tr, diag)
    return db, reporter


def _log_and_parse_issues(
    db: Database, run_id: int, check_name: str, result: dict[str, Any]
) -> None:
    """Parse tool output (e.g., Ruff) and persist parsed issues for this run.

    Currently supports:
      - ruff: expects parse_output(stdout) to yield dicts with keys:
        file, line, column, severity, message, rule_code
    """
    try:
        if "ruff" in check_name.lower() and result.get("stdout"):
            issues = ruff_parser.parse_output(result["stdout"])
            for issue in issues:
                db.log_issue(
                    run_id=run_id,
                    parser="ruff",
                    file_path=issue.get("file"),
                    line_number=issue.get("line"),
                    rule_id=issue.get("rule_code"),
                    severity=issue.get("severity"),
                    message=issue.get("message"),
                )
    except Exception as e:
        # Never fail the run due to a parser error.
        logger.warning(f"Issue parsing failed for '{check_name}': {e}")


def _submit_check(pool: ThreadPoolExecutor, name: str, check_cfg: dict[str, Any]):
    """Submit a check to the thread pool, resolving registry or shell command."""
    func = get_check(name)
    if func is not None:
        return pool.submit(
            func, command=check_cfg.get("command"), **(check_cfg.get("params") or {})
        ), (name, check_cfg)
    # Fallback to shell command if no registry entry found
    cmd = check_cfg.get("command")
    if not cmd:
        raise ValueError(f"Skipping check '{name}': no command and not registered")
    return pool.submit(runner.run_command, cmd), (name, check_cfg)


def _execute_checks(checks: list[dict[str, Any]], db: Database) -> list[dict[str, Any]]:
    """Execute checks concurrently, persist run/issue data, and return raw results.

    Args:
        checks: Enabled checks from CLI config.
        db: Database instance.

    Returns:
        List of result dicts with run_id attached.
    """
    if not checks:
        return []

    results: list[dict[str, Any]] = []
    # Preserve existing behavior: cap at 8 workers and never exceed number of checks
    max_workers = max(1, min(8, len(checks)))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures: dict[Any, tuple[str, dict[str, Any]]] = {}
        for c in checks:
            name = c.get("name", "")
            try:
                fut, meta = _submit_check(pool, name, c)
                futures[fut] = meta
            except ValueError as ve:
                logger.warning(str(ve))
                continue

        # Progress display showing elapsed time only
        with tqdm(total=len(futures), bar_format="Elapsed: {elapsed}") as pbar:
            for idx, f in enumerate(as_completed(futures), start=1):
                name, c = futures[f]
                try:
                    result = f.result()
                except Exception as e:
                    # Safeguard any unexpected exception during execution
                    result = {
                        "name": c.get("command", name),
                        "stdout": "",
                        "stderr": str(e),
                        "returncode": -1,
                        "duration_sec": 0,
                    }

                # Persist run
                run_id = db.log_run(
                    command=str(result.get("name", name)),
                    exit_code=int(result.get("returncode", 1)),
                    duration=float(result.get("duration_sec", 0.0)),
                    cwd=str(Path.cwd()),
                    success=bool(result.get("returncode", 1) == 0),
                )

                # Persist parsed issues (best-effort)
                _log_and_parse_issues(db, run_id, name, result)

                results.append({"check": name, **result, "run_id": run_id})
                logger.info(
                    f"Completed {idx}/{len(futures)}: {name} -> code {result.get('returncode')}"
                )
                pbar.update(1)

    return results


def _persist_raw_results_if_requested(
    sys_cfg: Config, cfg_data: dict[str, Any], results: list[dict[str, Any]]
) -> None:
    """Persist raw results either to the lightweight DB or fallback to JSON file.

    Args:
        sys_cfg: System config for DB path override.
        cfg_data: CLI config dict.
        results: Collected run results.
    """
    json_out = cfg_data.get("output", {}).get("json_export")
    if not json_out:
        return

    try:
        from .db import init_db, save_result  # Lightweight results DB
    except Exception:
        save_result = None  # type: ignore
        init_db = None  # type: ignore

    # Ensure DB exists (best-effort)
    if init_db:
        init_db(getattr(sys_cfg, "database_path", None))

    if save_result:
        for r in results:
            save_result(
                r, source="cli.run", db_path=getattr(sys_cfg, "database_path", None)
            )
        logger.info("Raw results persisted to database via persistence layer")
    else:
        # Fallback to file if persistence module is unavailable
        _ensure_dirs(json_out)
        Path(json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info(f"Raw results saved to {json_out}")


# ---------------------------
# Subcommand implementations
# ---------------------------


def cmd_list_checks(args: argparse.Namespace) -> int:
    """List registered checks and those configured in the provided config file.

    Returns:
        Exit status code (0 on success).
    """
    cfg_data = load_config_file(getattr(args, "config", None))
    configured = cfg_data.get("checks", [])

    logger.info("Registered checks:")
    for name in sorted(available_checks().keys()):
        logger.info(f"  - {name}")

    logger.info("\nConfigured checks:")
    if not configured:
        logger.info("  (none)")
    else:
        for c in configured:
            status = "enabled" if c.get("enabled", True) else "disabled"
            cmd = c.get("command") or "<registry>"
            logger.info(f"  - {c.get('name', '')} [{status}] -> {cmd}")

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Execute configured checks, persist runs and issues, and optional reporting.

    Returns:
        Exit status code (0 on success).
    """
    cfg_data, sys_cfg = _resolve_sys_config(getattr(args, "config", None))
    db, reporter = _build_services(sys_cfg)

    checks = [c for c in cfg_data.get("checks", []) if c.get("enabled", True)]
    if not checks:
        logger.info("No checks enabled in config. Nothing to run.")
        return 0

    # Execute checks concurrently and persist
    results = _execute_checks(checks, db)

    # Optionally write a quick summary report if requested via CLI flags
    if getattr(args, "report", False):
        out = cfg_data.get("output", {}).get("report_file")
        _ensure_dirs(out)
        path = reporter.generate_summary_report(days=7, output_file=out)
        logger.info(f"Report saved to {path}")

    # Optional raw results persistence (DB via .db or fallback to JSON)
    _persist_raw_results_if_requested(sys_cfg, cfg_data, results)

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate reports from the database.

    Uses the lightweight results reporter when --format is provided, otherwise
    the comprehensive Reporting system.

    Returns:
        Exit status code (0 on success).
    """
    # Load both configs
    cfg_data, sys_cfg = _resolve_sys_config(getattr(args, "config", None))

    # If --format is provided, use the lightweight DB results reporter
    if getattr(args, "format", None):
        out = args.output or "report.md"
        result_path = generate_simple_report(
            format=args.format,
            output=out,
            limit=getattr(args, "limit", None),
            db_path=getattr(sys_cfg, "database_path", None),
            source=getattr(args, "source", None),
        )
        if result_path:
            logger.info(f"Report saved to {result_path}")
        return 0

    # Otherwise fall back to the comprehensive Reporting system
    db, reporter = _build_services(sys_cfg)

    out = args.output or cfg_data.get("output", {}).get("report_file")
    _ensure_dirs(out)

    if args.type == "summary":
        path = reporter.generate_summary_report(days=args.days, output_file=out)
    elif args.type == "comprehensive":
        path = reporter.generate_comprehensive_report(days=args.days, output_file=out)
    else:
        # issue report for a specific run id
        if args.run_id is None:
            logger.error("--run-id is required for type=issue")
            return 2
        path = reporter.generate_issue_report(run_id=args.run_id, output_file=out)

    logger.info(f"Report saved to {path}")
    return 0


# ---------------------------
# Argument parsing and main
# ---------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser and subcommands."""
    p = argparse.ArgumentParser(
        prog="ichs", description="Intelligent Code Health System (iCHS)"
    )
    p.add_argument("--config", help="Path to ichs.yml or ichs.json", default=None)
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # list-checks
    sp_list = sub.add_parser(
        "list-checks", help="List registered and configured checks"
    )
    sp_list.set_defaults(func=cmd_list_checks)

    # run
    sp_run = sub.add_parser("run", help="Run configured checks")
    sp_run.add_argument(
        "--report", action="store_true", help="Generate a summary report after running"
    )
    sp_run.set_defaults(func=cmd_run)

    # report
    sp_rep = sub.add_parser("report", help="Generate reports from the database")
    sp_rep.add_argument(
        "--type", choices=["summary", "comprehensive", "issue"], default="summary"
    )
    sp_rep.add_argument(
        "--days",
        type=int,
        default=7,
        help="Period of analysis for summary/comprehensive",
    )
    sp_rep.add_argument("--run-id", type=int, help="Run ID (for type=issue)")
    sp_rep.add_argument("--output", help="Output path for the report file")
    # New simple report formats based on lightweight results DB
    sp_rep.add_argument(
        "--format",
        choices=["cli", "md", "markdown"],
        help="Render results table to CLI or Markdown (uses lightweight DB)",
    )
    sp_rep.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Limit number of results from lightweight DB",
    )
    sp_rep.add_argument("--source", help="Filter by source label in lightweight DB")
    sp_rep.set_defaults(func=cmd_report)

    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: parse arguments, configure logging, and dispatch commands."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging based on verbosity
    level = logging.WARNING
    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose == 1:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
