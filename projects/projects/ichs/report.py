from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import get_results

# Rich is optional for CLI pretty table output
try:  # pragma: no cover - optional dependency
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover
    Console = None  # type: ignore
    Table = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class SimpleResult:
    """
    Minimal normalized structure for lightweight results reporting.
    """

    id: int
    created_at: str
    source: str | None
    check: str
    returncode: int | None
    duration_sec: float | None

    @property
    def ok(self) -> bool | None:
        if self.returncode is None:
            return None
        return self.returncode == 0


def _coerce_row(row: dict[str, Any]) -> SimpleResult:
    """
    Convert a raw row from get_results() into a SimpleResult, coercing types safely.
    """
    payload: dict[str, Any] = row.get("payload", {}) or {}
    check = str(
        payload.get("check") or payload.get("name") or payload.get("command") or ""
    ).strip()

    rc = payload.get("returncode")
    try:
        rc = int(rc) if rc is not None else None
    except Exception:
        rc = None

    dur = payload.get("duration_sec")
    try:
        dur = float(dur) if dur is not None else None
    except Exception:
        dur = None

    return SimpleResult(
        id=int(row.get("id", 0)),
        created_at=str(row.get("created_at", "")),
        source=row.get("source"),
        check=check,
        returncode=rc,
        duration_sec=dur,
    )


def load_results(
    limit: int | None = None,
    db_path: str | None = None,
    source: str | None = None,
) -> list[SimpleResult]:
    """
    Load latest lightweight results from the persistence layer, newest first.
    """
    try:
        rows = get_results(limit=limit, db_path=db_path, source=source)
    except Exception as e:
        # Log and return empty set rather than failing the CLI/report
        logger.warning(
            "Failed to load results (db_path=%s, source=%s): %s", db_path, source, e
        )
        rows = []
    return [_coerce_row(r) for r in rows]


def render_cli_table(results: Iterable[SimpleResult]) -> None:
    """
    Render results in a CLI table. Uses rich when available, otherwise a simple fallback.
    """
    if Console is None or Table is None:
        # Fallback: simple print
        print(
            "ID  Created At                Source       Check                         Code  Duration  OK"
        )
        print(
            "--  ------------------------  -----------  ------------------------------  ----  --------  --"
        )
        for r in results:
            created = r.created_at[:22]
            src = (r.source or "")[:11]
            check = r.check[:30]
            code = "" if r.returncode is None else str(r.returncode)
            dur = "" if r.duration_sec is None else f"{r.duration_sec:.2f}s"
            ok = "" if r.ok is None else ("✔" if r.ok else "✘")
            print(f"{r.id:<3}{created:<26}{src:<13}{check:<30}{code:>6}{dur:>10}  {ok}")
        return

    table = Table(title="iCHS Results (latest first)")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Created At", style="magenta")
    table.add_column("Source", style="green")
    table.add_column("Check", style="white")
    table.add_column("Code", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("OK", justify="center")

    for r in results:
        table.add_row(
            str(r.id),
            r.created_at,
            r.source or "",
            r.check,
            "" if r.returncode is None else str(r.returncode),
            "" if r.duration_sec is None else f"{r.duration_sec:.2f}s",
            ""
            if r.ok is None
            else ("[bold green]✔[/bold green]" if r.ok else "[bold red]✘[/bold red]"),
        )

    Console().print(table)


def render_markdown(results: Iterable[SimpleResult]) -> str:
    """
    Build a simple markdown report containing a summary and a results table.
    """
    results_list = list(results)
    total = len(results_list)
    ok_count = sum(1 for r in results_list if r.ok is True)
    sum(1 for r in results_list if r.ok is False)

    lines: list[str] = []
    lines.append("# iCHS Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total Results: {total}")
    lines.append(
        f"Total Progress: {ok_count}/{total} completed in {elapsed_placeholder()}"
    )
    lines.append("")
    lines.append("| ID | Created At | Source | Check | Code | Duration | OK |")
    lines.append("|---:|:-----------|:-------|:------|-----:|---------:|:--:|")
    for r in results_list:
        code = "" if r.returncode is None else str(r.returncode)
        dur = "" if r.duration_sec is None else f"{r.duration_sec:.2f}s"
        ok = "" if r.ok is None else ("✔" if r.ok else "✘")
        lines.append(
            f"| {r.id} | {r.created_at} | {r.source or ''} | {r.check} | {code} | {dur} | {ok} |"
        )

    return "\n".join(lines) + "\n"


def elapsed_placeholder() -> str:
    """
    Respect user rule: prefer {elapsed} and 'Total Progress' phrasing for consistency
    with the CLI progress indicators. Since this path is not live-updated, we keep a
    placeholder token.
    """
    return "{elapsed}"


def generate_report(
    *,
    format: str = "cli",
    output: str | None = None,
    limit: int | None = 50,
    db_path: str | None = None,
    source: str | None = None,
) -> str | None:
    """
    Lightweight report generator. For 'cli', prints to stdout and returns None.
    For 'md'/'markdown', writes a Markdown file and returns its path.
    """
    fmt = (format or "cli").strip().lower()
    if fmt in ("markdown",):
        fmt = "md"
    if fmt not in ("cli", "md"):
        raise ValueError(f"Unsupported format: {format}")

    results = load_results(limit=limit, db_path=db_path, source=source)

    if fmt == "cli":
        render_cli_table(results)
        return None

    # md
    md = render_markdown(results)
    path = Path(output or "report.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return str(path)
