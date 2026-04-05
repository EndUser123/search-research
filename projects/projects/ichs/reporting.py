from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .database import Database

logger = logging.getLogger(__name__)


@dataclass
class _RunRow:
    id: int
    command: str
    exit_code: int
    success: int
    duration_sec: float
    created_at: str


@dataclass
class _IssueRow:
    id: int
    run_id: int
    parser: str
    file_path: str
    line_number: int | None
    rule_id: str | None
    severity: str | None
    message: str
    created_at: str


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _default_report_path(kind: str) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / ".ichs" / f"{kind}-report-{ts}.md"


def _cutoff_iso(days: int) -> str:
    dt = datetime.now(UTC) - timedelta(days=max(0, days))
    return dt.replace(microsecond=0).isoformat()


class Reporting:
    """
    Reporting service that queries the Database and produces Markdown reports.

    API (used by CLI):
      - generate_summary_report(days: int, output_file: Optional[str]) -> str
      - generate_comprehensive_report(days: int, output_file: Optional[str]) -> str
      - generate_issue_report(run_id: int, output_file: Optional[str]) -> str
    """

    def __init__(
        self, config: Any, db: Database, synthesis: Any, trends: Any, diagnostics: Any
    ) -> None:
        self._config = config
        self._db = db
        # Dependencies are accepted to remain API-compatible; not required for core queries
        self._synthesis = synthesis
        self._trends = trends
        self._diagnostics = diagnostics

    # --------- Public methods ---------

    def generate_summary_report(
        self, *, days: int = 7, output_file: str | None = None
    ) -> str:
        cutoff = _cutoff_iso(days)
        rows = self._get_runs_since(cutoff)
        totals = self._aggregate_runs(rows)
        top_rules = self._top_rules_since(cutoff, limit=10)

        lines: list[str] = []
        lines.append(f"# iCHS Summary Report (last {days} day(s))")
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- Total runs: {totals['total']}")
        lines.append(f"- Successes: {totals['success']}")
        lines.append(f"- Failures: {totals['fail']}")
        lines.append(f"- Average duration (s): {totals['avg_duration_sec']:.2f}")
        lines.append("")
        lines.append("## Recent runs")
        lines.append("")
        lines.append("| ID | Time (UTC) | Success | Exit | Duration (s) | Command |")
        lines.append("|---:|------------|:------:|-----:|-------------:|---------|")
        for r in rows[:20]:
            ok = "✅" if r.success else "❌"
            lines.append(
                f"| {r.id} | {r.created_at} | {ok} | {r.exit_code} | {r.duration_sec:.2f} | {self._short_cmd(r.command)} |"
            )
        if not rows:
            lines.append("| (none) |  |  |  |  |  |")

        lines.append("")
        lines.append("## Top issue rules")
        lines.append("")
        lines.append("| Rule | Count |")
        lines.append("|------|------:|")
        if top_rules:
            for rule, cnt in top_rules:
                label = rule or "(unknown)"
                lines.append(f"| {label} | {cnt} |")
        else:
            lines.append("| (none) | 0 |")

        out_path = Path(output_file) if output_file else _default_report_path("summary")
        _ensure_parent(out_path)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return str(out_path)

    def generate_comprehensive_report(
        self, *, days: int = 7, output_file: str | None = None
    ) -> str:
        cutoff = _cutoff_iso(days)
        runs = self._get_runs_since(cutoff)
        totals = self._aggregate_runs(runs)

        lines: list[str] = []
        lines.append(f"# iCHS Comprehensive Report (last {days} day(s))")
        lines.append("")
        lines.append("## Overview")
        lines.append(f"- Total runs: {totals['total']}")
        lines.append(f"- Successes: {totals['success']}")
        lines.append(f"- Failures: {totals['fail']}")
        lines.append(f"- Average duration (s): {totals['avg_duration_sec']:.2f}")
        lines.append("")

        lines.append("## Runs")
        lines.append("")
        for r in runs:
            ok = "✅" if r.success else "❌"
            lines.append(f"### Run {r.id} — {ok}")
            lines.append("")
            lines.append(f"- Time (UTC): {r.created_at}")
            lines.append(f"- Command: `{r.command}`")
            lines.append(f"- Exit code: {r.exit_code}")
            lines.append(f"- Duration: {r.duration_sec:.2f} s")
            issue_rows = self._issues_for_run(r.id)
            lines.append(f"- Issues: {len(issue_rows)}")
            if issue_rows:
                lines.append("")
                lines.append("| Parser | File | Line | Rule | Severity | Message |")
                lines.append("|--------|------|-----:|------|----------|---------|")
                for i in issue_rows[:50]:
                    line = "" if i.line_number is None else str(i.line_number)
                    rule = i.rule_id or ""
                    sev = i.severity or ""
                    msg = self._short_msg(i.message)
                    lines.append(
                        f"| {i.parser} | {self._short_path(i.file_path)} | {line} | {rule} | {sev} | {msg} |"
                    )
            lines.append("")

        out_path = (
            Path(output_file) if output_file else _default_report_path("comprehensive")
        )
        _ensure_parent(out_path)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return str(out_path)

    def generate_issue_report(
        self, *, run_id: int, output_file: str | None = None
    ) -> str:
        run = self._get_run(run_id)
        issues = self._issues_for_run(run_id)

        lines: list[str] = []
        lines.append(f"# iCHS Issue Report — Run {run_id}")
        lines.append("")
        if run:
            ok = "✅" if run.success else "❌"
            lines.append("## Run")
            lines.append(f"- Time (UTC): {run.created_at}")
            lines.append(f"- Command: `{run.command}`")
            lines.append(f"- Exit code: {run.exit_code}")
            lines.append(f"- Duration: {run.duration_sec:.2f} s")
            lines.append(f"- Status: {ok}")
            lines.append("")
        else:
            lines.append("_Warning: run not found_")
            lines.append("")

        lines.append(f"## Issues ({len(issues)})")
        lines.append("")
        if issues:
            lines.append("| Parser | File | Line | Rule | Severity | Message |")
            lines.append("|--------|------|-----:|------|----------|---------|")
            for i in issues:
                line = "" if i.line_number is None else str(i.line_number)
                rule = i.rule_id or ""
                sev = i.severity or ""
                msg = self._short_msg(i.message)
                lines.append(
                    f"| {i.parser} | {self._short_path(i.file_path)} | {line} | {rule} | {sev} | {msg} |"
                )
        else:
            lines.append("_No issues logged for this run._")

        out_path = (
            Path(output_file)
            if output_file
            else _default_report_path(f"issues-run-{run_id}")
        )
        _ensure_parent(out_path)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return str(out_path)

    # --------- Query helpers ---------

    def _get_runs_since(self, cutoff_iso: str) -> list[_RunRow]:
        conn = self._db._get_conn()  # Using internal accessor for read-only queries
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, command, exit_code, success, duration_sec, created_at
                FROM runs
                WHERE created_at >= ?
                ORDER BY created_at DESC, id DESC
                """,
                (cutoff_iso,),
            )
            rows = cur.fetchall()
            return [
                _RunRow(
                    id=int(r["id"]),
                    command=str(r["command"]),
                    exit_code=int(r["exit_code"]),
                    success=int(r["success"]),
                    duration_sec=float(r["duration_sec"]),
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            cur.close()

    def _get_run(self, run_id: int) -> _RunRow | None:
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, command, exit_code, success, duration_sec, created_at
                FROM runs
                WHERE id = ?
                """,
                (int(run_id),),
            )
            r = cur.fetchone()
            if not r:
                return None
            return _RunRow(
                id=int(r["id"]),
                command=str(r["command"]),
                exit_code=int(r["exit_code"]),
                success=int(r["success"]),
                duration_sec=float(r["duration_sec"]),
                created_at=str(r["created_at"]),
            )
        finally:
            cur.close()

    def _issues_for_run(self, run_id: int) -> list[_IssueRow]:
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, run_id, parser, file_path, line_number, rule_id, severity, message, created_at
                FROM issues
                WHERE run_id = ?
                ORDER BY file_path ASC, line_number ASC NULLS LAST, id ASC
                """,
                (int(run_id),),
            )
            rows = cur.fetchall()
            return [
                _IssueRow(
                    id=int(r["id"]),
                    run_id=int(r["run_id"]),
                    parser=str(r["parser"]),
                    file_path=str(r["file_path"]),
                    line_number=(
                        None if r["line_number"] is None else int(r["line_number"])
                    ),
                    rule_id=(None if r["rule_id"] is None else str(r["rule_id"])),
                    severity=(None if r["severity"] is None else str(r["severity"])),
                    message=str(r["message"]),
                    created_at=str(r["created_at"]),
                )
                for r in rows
            ]
        finally:
            cur.close()

    def _top_rules_since(
        self, cutoff_iso: str, *, limit: int = 10
    ) -> list[tuple[str, int]]:
        conn = self._db._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COALESCE(rule_id, '') AS rule_id, COUNT(*) AS cnt
                FROM issues
                WHERE run_id IN (SELECT id FROM runs WHERE created_at >= ?)
                GROUP BY COALESCE(rule_id, '')
                ORDER BY cnt DESC, rule_id ASC
                LIMIT ?
                """,
                (cutoff_iso, int(limit)),
            )
            rows = cur.fetchall()
            return [(str(r["rule_id"]), int(r["cnt"])) for r in rows]
        finally:
            cur.close()

    def _aggregate_runs(self, rows: list[_RunRow]) -> dict[str, Any]:
        total = len(rows)
        success = sum(1 for r in rows if r.success)
        fail = total - success
        avg_dur = (sum(r.duration_sec for r in rows) / total) if total else 0.0
        return {
            "total": total,
            "success": success,
            "fail": fail,
            "avg_duration_sec": avg_dur,
        }

    # --------- Formatting helpers ---------

    def _short_cmd(self, cmd: str, max_len: int = 60) -> str:
        if len(cmd) <= max_len:
            return cmd
        return cmd[: max_len - 3] + "..."

    def _short_path(self, path: str, max_len: int = 60) -> str:
        if len(path) <= max_len:
            return path
        return "…" + path[-(max_len - 1) :]

    def _short_msg(self, msg: str, max_len: int = 80) -> str:
        if len(msg) <= max_len:
            return msg
        return msg[: max_len - 3] + "..."
