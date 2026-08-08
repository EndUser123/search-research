#!/usr/bin/env python3
"""Deterministic pre-check runner — all 9 layers in one Python call.

Replaces the inline PowerShell block in /check SKILL.md Step 0.9.
Runs ruff, pyright, pylint, trace_check, bandit, radon, vulture,
pip-audit, and diff-cover on the given .py files, soft-skipping any
tool that is not installed. Produces a merged JSON packet for verifiers.

Usage:
    python run_deterministic_checks.py --py-files file1.py file2.py \\
        --run-dir P:/.artifacts/.../grok-check/20260729-... \\
        --scope-files requirements.txt pyproject.toml \\
        --output P:/.artifacts/.../deterministic-check.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Skills lib dir for trace_check.py and vulture_precheck.py
_SKILL_LIB = Path(__file__).resolve().parent


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a command, return (exit_code, stdout, stderr). Soft-fail on error."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, r.stdout, r.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return -1, "", ""


def _parse_json_safe(raw: str) -> Any:
    """Parse JSON, returning None on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def run_ruff(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    if not shutil.which("ruff"):
        return {"status": "skipped", "reason": "ruff not installed"}
    code, out, _ = _run(
        ["ruff", "check", "--select", "E,F", "--output-format=json", "--"] + py_files
    )
    return {"raw": out, "exit_code": code, "findings": _parse_json_safe(out) or []}


def run_pyright(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    if not shutil.which("pyright"):
        return {"status": "skipped", "reason": "pyright not installed"}
    code, out, _ = _run(["pyright", "--outputjson", "--"] + py_files, timeout=120)
    parsed = _parse_json_safe(out)
    errors = []
    if parsed and "generalDiagnostics" in parsed:
        errors = [
            d for d in parsed["generalDiagnostics"] if d.get("severity") == "error"
        ]
    return {"raw": out if out else "", "exit_code": code, "errors": errors}


def run_pylint(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    if not shutil.which("pylint"):
        return {"status": "skipped", "reason": "pylint not installed"}
    code, out, _ = _run(
        [
            "pylint",
            "--errors-only",
            "--enable=cyclic-import",
            "--output-format=json",
            "--",
        ]
        + py_files,
        timeout=120,
    )
    return {"raw": out, "exit_code": code, "findings": _parse_json_safe(out) or []}


def run_trace_check(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    script = _SKILL_LIB / "trace_check.py"
    if not script.exists():
        return {"status": "skipped", "reason": f"trace_check.py not found at {script}"}
    code, out, _ = _run([sys.executable, str(script), "--paths"] + py_files)
    parsed = _parse_json_safe(out)
    if parsed:
        return parsed
    if code != 0:
        return {
            "status": "error",
            "exit_code": code,
            "reason": "trace_check subprocess failed",
        }
    return {"status": "ok", "findings": [], "finding_count": 0}


def run_bandit(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    if not shutil.which("bandit"):
        return {"status": "skipped", "reason": "bandit not installed"}
    code, out, _ = _run(
        ["bandit", "-f", "json", "-ll", "-x", "tests", "--"] + py_files, timeout=60
    )
    return _parse_json_safe(out) or {
        "status": "skipped",
        "reason": "bandit output parse failed",
    }


def run_radon(py_files: list[str]) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    if not shutil.which("radon"):
        return {"status": "skipped", "reason": "radon not installed"}
    code, out, _ = _run(
        ["radon", "cc", "-j", "-s", "-n", "C", "--"] + py_files, timeout=120
    )
    parsed = _parse_json_safe(out)
    if not parsed:
        return {
            "status": "skipped",
            "reason": "radon output parse failed",
            "raw": out[:2000] if out else "",
        }
    # Count functions at complexity grade C or worse
    hotspot_count = 0
    hotspots = []
    for filepath, items in parsed.items():
        if not isinstance(items, list):
            continue
        for item in items:
            rank = item.get("rank", item.get("letter", ""))
            if rank in ("C", "D", "E", "F"):
                hotspot_count += 1
                hotspots.append(
                    {
                        "file": filepath,
                        "name": item.get("name", "?"),
                        "complexity": item.get("complexity", 0),
                        "rank": rank,
                    }
                )
    return {
        "hotspot_count": hotspot_count,
        "hotspots": hotspots,
        "policy": "advisory_only",
    }


def run_vulture(py_files: list[str], run_dir: Path) -> dict[str, Any]:
    if not py_files:
        return {"status": "skipped", "reason": "no py_files"}
    script = _SKILL_LIB / "vulture_precheck.py"
    if not script.exists():
        return {
            "status": "skipped",
            "reason": f"vulture_precheck.py not found at {script}",
        }
    out_file = run_dir / "packets" / "vulture-advisory.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    code, out, _ = _run(
        [sys.executable, str(script), "--paths"]
        + py_files
        + ["--min-confidence", "80", "--output", str(out_file)]
    )
    if out_file.exists():
        return _parse_json_safe(out_file.read_text(encoding="utf-8")) or {
            "status": "ok",
            "finding_count": 0,
        }
    return {"status": "skipped", "reason": "vulture output not produced"}


def run_pip_audit(scope_files: list[str]) -> dict[str, Any]:
    if not shutil.which("pip-audit"):
        return {"status": "skipped", "reason": "pip-audit not installed"}
    # Find requirements file in scope — deterministic precedence:
    # pyproject.toml first, then requirements.txt
    req_file = None
    for f in scope_files:
        if f.endswith("pyproject.toml") and Path(f).exists():
            req_file = f
            break
    if not req_file:
        for f in scope_files:
            if f.endswith("requirements.txt") or (
                f.endswith(".txt") and "requirements" in f
            ):
                if Path(f).exists():
                    req_file = f
                    break
    if not req_file:
        return {"status": "skipped", "reason": "no requirements file in scope"}
    code, out, _ = _run(["pip-audit", "-r", req_file, "-f", "json"], timeout=60)
    return _parse_json_safe(out) or {
        "status": "skipped",
        "reason": "pip-audit output parse failed",
    }


def run_diff_cover(run_dir: Path) -> dict[str, Any]:
    if not shutil.which("diff-cover"):
        return {"status": "skipped", "reason": "diff-cover not installed"}
    cov_xml = run_dir / "packets" / "coverage.xml"
    if not cov_xml.exists():
        return {"status": "skipped", "reason": "no coverage.xml found"}
    code, out, _ = _run(["diff-cover", str(cov_xml), "--fail-under=80"])
    return {"raw": out, "policy": "advisory_only"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run all deterministic pre-check layers "
        "and produce a merged JSON packet."
    )
    parser.add_argument(
        "--py-files", nargs="+", required=True, help="Python files to check"
    )
    parser.add_argument(
        "--run-dir", required=True, help="Run directory for output packets"
    )
    parser.add_argument(
        "--scope-files",
        nargs="*",
        default=[],
        help="All scope files (for pip-audit requirements detection)",
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Write merged JSON result to this path"
    )
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Run all layers
    ruff = run_ruff(args.py_files)
    pyright = run_pyright(args.py_files)
    pylint = run_pylint(args.py_files)
    trace = run_trace_check(args.py_files)
    bandit = run_bandit(args.py_files)
    radon = run_radon(args.py_files)
    vulture = run_vulture(args.py_files, run_dir)
    pip_audit = run_pip_audit(args.scope_files)
    diff_cover = run_diff_cover(run_dir)

    # Build merged packet
    packet: dict[str, Any] = {
        "ruff": ruff,
        "pyright": pyright,
        "pylint": pylint,
        "trace_check": trace,
        "bandit": bandit,
        "radon_advisory": radon,
        "vulture_advisory": vulture,
        "pip_audit_advisory": pip_audit,
        "diff_cover_advisory": diff_cover,
    }

    # Summary counts
    has_errors = (
        ruff.get("exit_code", 0) != 0
        or len(pyright.get("errors", [])) > 0
        or pylint.get("exit_code", 0) not in (0, -1)
    )
    bandit_medium_high = 0
    if isinstance(bandit.get("results"), list):
        bandit_medium_high = sum(
            1
            for r in bandit["results"]
            if r.get("issue_severity", "") in ("MEDIUM", "HIGH")
        )

    vulture_count = vulture.get("finding_count", 0) if isinstance(vulture, dict) else 0
    radon_count = radon.get("hotspot_count", 0)

    # Add summary to the packet for verifiers
    packet["summary"] = {
        "has_errors": has_errors,
        "bandit_medium_high": bandit_medium_high,
        "radon_count": radon_count,
        "vulture_count": vulture_count,
    }

    # Print status
    if has_errors:
        print("DETERMINISTIC_CHECK: ERRORS FOUND (ruff/pyright/pylint)")
    else:
        print("DETERMINISTIC_CHECK: ruff/pyright/pylint clean")
    if bandit_medium_high > 0:
        print(
            f"DETERMINISTIC_CHECK: bandit findings={bandit_medium_high}"
            " (security — verifiers treat as bugs)"
        )
    if radon_count > 0:
        print(
            f"DETERMINISTIC_CHECK: radon advisory={radon_count}"
            " functions at complexity C+ (spot-check candidates)"
        )
    if vulture_count > 0:
        print(
            f"DETERMINISTIC_CHECK: vulture advisory findings="
            f"{vulture_count} (does not block CHECK alone)"
        )

    # Test coverage gap check: for each __lib/*.py, verify tests/test_*.py exists
    coverage_gaps = []
    for py_file in args.py_files:
        p = Path(py_file)
        if "__lib" in p.parts:
            # Walk up to find the package root (parent of __lib)
            lib_idx = list(p.parts).index("__lib")
            pkg_root = Path(*p.parts[:lib_idx])
            test_name = f"test_{p.stem}.py"
            test_path = pkg_root / "tests" / test_name
            if not test_path.exists():
                coverage_gaps.append(
                    {
                        "source": str(p),
                        "missing_test": str(test_path),
                        "message": (
                            f"{p.name} has no test file. Expected: {test_path}"
                        ),
                    }
                )
    packet["test_coverage_gaps"] = coverage_gaps
    if coverage_gaps:
        print(
            f"DETERMINISTIC_CHECK: {len(coverage_gaps)} "
            "test coverage gap(s) — __lib script(s) without tests"
        )

    # Write output
    output_path = args.output or str(run_dir / "packets" / "deterministic-check.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(packet, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(f"DETERMINISTIC_CHECK: packet written to {output_path}")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
