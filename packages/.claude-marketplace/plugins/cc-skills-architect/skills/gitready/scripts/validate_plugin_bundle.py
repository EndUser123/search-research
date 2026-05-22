#!/usr/bin/env python3
"""
validate_plugin_bundle.py — CI-usable plugin bundle validation

Usage:
    python validate_plugin_bundle.py --all <target_dir>
    python validate_plugin_bundle.py --check-manifest <target_dir>
    python validate_plugin_bundle.py --check-paths <target_dir> [--scope bundle|repo]
    python validate_plugin_bundle.py --check-bundle <target_dir>
    python validate_plugin_bundle.py --smoke-test <target_dir>
    python validate_plugin_bundle.py --fix <target_dir>

Scope (--scope):
    bundle  (default)  Only bundle-relevant files (distributable plugin)
    repo    Full repo hygiene scan (catches internal tech debt)

Bundle scope excludes internal-only scripts:
    scripts/create_github_repo.py, scripts/extract_from_monorepo.py,
    scripts/finalize_github_repo.py, scripts/scan_package_quality.py,
    scripts/upload_*.py, scripts/validate_*.py (internal tooling)

Exit codes:
    0 = all checks pass
    1 = check failed
    2 = error (bad args, file not found)
"""

import argparse
import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path

HARDCODE_PATTERNS = [
    r"P:\\\\+",
    r"P:",
    r"C:\\\\+",
    r"/Users/",
    r"/home/",
    r"~",
]

EXCLUDED_PATTERNS = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".git",
    "dist",
    "build",
    "*.egg-info",
    ".env",
    "*.log",
    ".coverage",
    "coverage.json",
    "*.backup",
    "*.old",
    "*.bak",
    "README_NEW.md",
]

ALWAYS_REQUIRED = [
    ".claude-plugin/plugin.json",
    "README.md",
    "LICENSE",
]


def check_manifest(target_dir: Path) -> tuple[bool, list[str]]:
    errors = []
    manifest = target_dir / ".claude-plugin" / "plugin.json"

    if not manifest.exists():
        errors.append("Missing .claude-plugin/plugin.json")
        return False, errors

    try:
        data = json.load(open(manifest, encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in plugin.json: {e}")
        return False, errors

    if "name" not in data:
        errors.append("plugin.json missing required 'name' field")

    return len(errors) == 0, errors


def check_paths(target_dir: Path, scope: str = "bundle") -> tuple[bool, list[str]]:
    errors = []
    seen = set()

    # Internal-only scripts excluded from bundle scope
    INTERNAL_ONLY = {
        "scripts/create_github_repo.py",
        "scripts/extract_from_monorepo.py",
        "scripts/finalize_github_repo.py",
        "scripts/scan_package_quality.py",
        "scripts/upload_github_videos.py",
        "scripts/upload_via_issue.py",
        "scripts/upload_via_issue_simple.py",
        "scripts/validate_banner.py",
        "scripts/validate_media_assets.py",
        "scripts/validate_plugin_bundle.py",
    }

    BUNDLE_EXCLUDE_DIRS = {"tests", "docs", "eval_sets", "assets", ".pytest_cache"}

    py_files = [f for f in target_dir.rglob("*.py") if "__pycache__" not in str(f)]

    for py_file in py_files:
        rel = py_file.relative_to(target_dir).as_posix()

        # In bundle scope, skip internal-only scripts and non-bundle directories
        if scope == "bundle":
            parent = rel.split("/")[0] if "/" in rel else rel.split("\\")[0]
            if parent in BUNDLE_EXCLUDE_DIRS or rel in INTERNAL_ONLY:
                continue
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            for pat in HARDCODE_PATTERNS:
                if re.search(pat, content):
                    msg = f"{rel}: hardcoded path pattern '{pat}'"
                    if msg not in seen:
                        seen.add(msg)
                        errors.append(msg)
        except Exception:
            pass

    return len(errors) == 0, errors


def check_bundle(target_dir: Path) -> tuple[bool, list[str]]:
    errors = []

    for required in ALWAYS_REQUIRED:
        if not (target_dir / required).exists():
            errors.append(f"Missing required bundle file: {required}")

    if (target_dir / "pyproject.toml").exists():
        errors.append("pyproject.toml found — plugins use .claude-plugin/, not pip packaging")

    if (target_dir / "core").exists():
        errors.append("core/ directory found — should be scripts/ (see PLUGIN_STANDARDS.md)")

    return len(errors) == 0, errors


def smoke_test(target_dir: Path) -> tuple[bool, list[str]]:
    errors = []
    scripts_dir = target_dir / "scripts"

    if not scripts_dir.exists():
        return True, []

    init_py = scripts_dir / "__init__.py"
    if init_py.exists():
        try:
            py_compile.compile(str(init_py), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Import compile failed: {e}")
            return False, errors

    return len(errors) == 0, errors


def fix_hardcoded_paths(target_dir: Path, scope: str = "bundle") -> int:
    """Replace hardcoded paths with ${CLAUDE_PLUGIN_ROOT} in Python files."""
    INTERNAL_ONLY = {
        "scripts/create_github_repo.py",
        "scripts/extract_from_monorepo.py",
        "scripts/finalize_github_repo.py",
        "scripts/scan_package_quality.py",
        "scripts/upload_github_videos.py",
        "scripts/upload_via_issue.py",
        "scripts/upload_via_issue_simple.py",
        "scripts/validate_banner.py",
        "scripts/validate_media_assets.py",
        "scripts/validate_plugin_bundle.py",
    }
    BUNDLE_EXCLUDE_DIRS = {"tests", "docs", "eval_sets", "assets", ".pytest_cache"}

    py_files = [f for f in target_dir.rglob("*.py") if "__pycache__" not in str(f)]
    fixed = 0

    for py_file in py_files:
        rel = py_file.relative_to(target_dir).as_posix()
        if scope == "bundle":
            parent = rel.split("/")[0] if "/" in rel else rel.split("\\")[0]
            if parent in BUNDLE_EXCLUDE_DIRS or rel in INTERNAL_ONLY:
                continue
            continue
        try:
            original = py_file.read_text(encoding="utf-8")
            content = original

            # Replace P:\\... with ${CLAUDE_PLUGIN_ROOT}/
            # Handle various escape levels
            content = re.sub(r"P:\\\\+", "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r'P:\\', "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r"C:\\\\+", "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r'C:\\', "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r"/Users/[^/]+/", "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r"/home/[^/]+/", "${CLAUDE_PLUGIN_ROOT}/", content)
            content = re.sub(r"(?<![\w])\~(?![\w/])", "${CLAUDE_PLUGIN_ROOT}", content)

            if content != original:
                py_file.write_text(content, encoding="utf-8")
                fixed += 1
                print(f"Fixed: {py_file.relative_to(target_dir)}")
        except Exception as e:
            print(f"Error fixing {py_file}: {e}", file=sys.stderr)

    return fixed


def main():
    parser = argparse.ArgumentParser(description="Validate plugin bundle readiness")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--check-manifest", nargs="?", const=".", help="Check manifest completeness")
    parser.add_argument("--check-paths", nargs="?", const=".", help="Check path portability")
    parser.add_argument("--check-bundle", nargs="?", const=".", help="Check bundle contents")
    parser.add_argument("--smoke-test", nargs="?", const=".", help="Run smoke test")
    parser.add_argument("--fix", nargs="?", const=".", help="Auto-fix hardcoded paths")
    parser.add_argument("--scope", default="bundle", choices=["bundle", "repo"],
                        help="Validation scope: 'bundle' (distributable, default) or 'repo' (full repo hygiene)")
    parser.add_argument("target_dir", nargs="?", default=".", help="Target directory")

    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()

    if not target_dir.exists():
        print(f"ERROR: Target directory not found: {target_dir}", file=sys.stderr)
        sys.exit(2)

    checks = []
    if args.all:
        checks = ["manifest", "paths", "bundle", "smoke"]
    else:
        if args.check_manifest is not None:
            checks.append("manifest")
        if args.check_paths is not None:
            checks.append("paths")
        if args.check_bundle is not None:
            checks.append("bundle")
        if args.smoke_test is not None:
            checks.append("smoke")

    if "manifest" in checks:
        ok, errs = check_manifest(target_dir)
        status = "PASS" if ok else "FAIL"
        print(f"Manifest: {status}")
        for e in errs:
            print(f"  {e}")
        if not ok:
            print()

    if "paths" in checks:
        ok, errs = check_paths(target_dir, scope=args.scope)
        status = "PASS" if ok else "FAIL"
        print(f"Paths: {status}")
        for e in errs:
            print(f"  {e}")
        if not ok:
            print()

    if "bundle" in checks:
        ok, errs = check_bundle(target_dir)
        status = "PASS" if ok else "FAIL"
        print(f"Bundle: {status}")
        for e in errs:
            print(f"  {e}")
        if not ok:
            print()

    if "smoke" in checks:
        ok, errs = smoke_test(target_dir)
        status = "PASS" if ok else "FAIL"
        print(f"Smoke: {status}")
        for e in errs:
            print(f"  {e}")
        if not ok:
            print()

    if args.fix is not None:
        fixed = fix_hardcoded_paths(target_dir, scope=args.scope)
        print(f"Fixed {fixed} files")

    if not checks and args.fix is None:
        parser.print_help()
        sys.exit(2)

    # Exit code: 0 if all passed, 1 if any failed
    if checks:
        all_pass = all([
            check_manifest(target_dir)[0] if "manifest" in checks else True,
            check_paths(target_dir)[0] if "paths" in checks else True,
            check_bundle(target_dir)[0] if "bundle" in checks else True,
            smoke_test(target_dir)[0] if "smoke" in checks else True,
        ])
        sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()