#!/usr/bin/env python3
"""
Claude Code Plugin Audit & Fix Tool

Audits plugin directories for:
  - Broken symlinks
  - Invalid JSON manifests
  - Malformed hooks.json
  - Hardcoded paths
  - Missing required files
  - Conflicting skill/command names across global and local dirs
Can auto-fix:
  - Invalid JSON
  - Missing hooks.json (creates empty)
  - Broken symlinks (removes or recreates)
  - Stale .claude/.state dirs inside skills/ subdirectories
Can validate:
  - Run 'claude plugin validate' on each plugin
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
except ImportError:
    Console = None
    Table = None
    Panel = None
    def rprint(*args, **kwargs):
        print(*args, **kwargs)
C_RESET = "[0m"
C_RED = "[91m"
C_YELLOW = "[93m"
C_CYAN = "[96m"
C_GREEN = "[92m"
def _detect_marketplace_root(script_path: str, cli_root: Optional[str] = None) -> Optional[str]:
    """Detect marketplace root from CLI root, env var, or script location."""
    if cli_root:
        packages_root = Path(cli_root)
        # Check for .claude-marketplace subdir (packages root scenario)
        mp_dir = packages_root / ".claude-marketplace"
        if mp_dir.exists():
            return str(mp_dir)
        # Fallback: treat as marketplace root itself
        if packages_root.exists() and (packages_root / "plugins").exists():
            return str(packages_root)
    env_root = os.environ.get("CLAUDE_MARKETPLACE_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        root = Path(env_root)
        for parent in [root, root.parent, root.parent.parent]:
            mp_dir = parent / ".claude-marketplace"
            if mp_dir.exists():
                return str(mp_dir)
        if root.exists() and (root / "plugins").exists():
            return str(root)
    script_dir = Path(script_path).resolve().parent
    if script_dir.name == "scripts":
        mp_dir = script_dir.parent / ".claude-marketplace"
        if mp_dir.exists():
            return str(mp_dir)
        mp_dir = script_dir.parent.parent / ".claude-marketplace"
        if mp_dir.exists():
            return str(mp_dir)
    return None
def _load_json(path: Path) -> tuple[bool, Optional[dict]]:
    """Load JSON safely, return (success, data)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return True, json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, None
def _save_json(path: Path, obj: dict) -> bool:
    """Save JSON safely, return success."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        return True
    except OSError:
        return False
def audit_plugins(plugins_dir: Path, marketplace_root: str) -> list[dict]:
    """Audit plugin directories and manifests."""
    results = []
    if not plugins_dir.exists():
        return results
    for plugin in sorted(plugins_dir.iterdir()):
        if plugin.name.startswith("."):
            continue
        result = {"plugin": plugin.name, "errors": [], "warnings": [], "fixed": False}
        # Check plugin.json
        manifest_path = plugin / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            result["warnings"].append("Missing .claude-plugin/plugin.json")
            marketplace_json = plugin / "marketplace.json"
            if marketplace_json.exists():
                result["warnings"].append("Has marketplace.json but no .claude-plugin/plugin.json")
        else:
            ok, data = _load_json(manifest_path)
            if not ok:
                result["errors"].append("Invalid .claude-plugin/plugin.json")
            elif "name" not in data:
                result["warnings"].append("Missing name in plugin manifest")
        # Check marketplace.json
        mp_json = plugin / "marketplace.json"
        if mp_json.exists():
            ok, data = _load_json(mp_json)
            if not ok:
                result["errors"].append("Invalid marketplace.json")
        # Check hooks.json
        hooks_path = plugin / "hooks.json"
        if hooks_path.exists():
            ok, data = _load_json(hooks_path)
            if not ok:
                result["errors"].append("Invalid hooks.json")
            elif not isinstance(data, dict):
                result["errors"].append("hooks.json must be a dict")
        # Check for .claude/.state inside skill subdirectories (not at plugin root)
        skills_dir = plugin / "skills"
        if skills_dir.is_dir():
            for skill_item in skills_dir.iterdir():
                if skill_item.is_dir():
                    for bad in [".claude", ".state"]:
                        bad_dir = skill_item / bad
                        if bad_dir.exists() and bad_dir.is_dir():
                            result["errors"].append(f"{bad}/ inside skills/{skill_item.name}/ (should be at plugin root)")
        # Check for build artifacts in plugin root
        build_artifacts = ["__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".git"]
        gitignore_path = plugin / ".gitignore"
        gitignored = set()
        if gitignore_path.exists():
            with open(gitignore_path, encoding="utf-8") as f:
                gitignored = {line.strip() for line in f if line.strip() and not line.startswith("#")}
        for artifact in build_artifacts:
            artifact_path = plugin / artifact
            if not artifact_path.exists():
                continue
            # .git is always a directory in a repo; check if it's actually gitignored
            if artifact == ".git":
                if ".git" in gitignored:
                    continue
            else:
                # For other artifacts, only warn if not gitignored
                if artifact in gitignored or artifact + "/" in gitignored:
                    continue
            result["warnings"].append(f"Build artifact '{artifact}' in plugin root (should be gitignored)")
        # Check for state/data files in plugin root (state should be in P:/\.claude/.artifacts/<terminal_id>/)
        for fpath in plugin.iterdir():
            if fpath.is_file() and any(fpath.suffix == ext for ext in [".data.json", ".meta.json", ".state.json"]):
                result["warnings"].append(f"State file '{fpath.name}' in plugin root (should use P:/.claude/.artifacts/<terminal_id>/)")
        results.append(result)
    return results
def audit_marketplace(marketplace_root: str) -> list[dict]:
    """Audit marketplace.json."""
    results = []
    mp_path = Path(marketplace_root) / "marketplace.json"
    if not mp_path.exists():
        results.append({"file": "marketplace.json", "error": "marketplace.json not found in marketplace root"})
        return results
    ok, data = _load_json(mp_path)
    if not ok:
        results.append({"file": "marketplace.json", "error": "Invalid JSON"})
        return results
    if "plugins" not in data:
        results.append({"file": "marketplace.json", "warning": "No plugins array"})
    return results
def _scan_paths(file_path: Path, plugin_name: str) -> list[str]:
    """Scan a file for hardcoded paths."""
    issues = []
    try: content = file_path.read_text(errors="ignore")
    except OSError:
        return issues
    patterns = [
        r"[A-Za-z]:\\[^'\"]+",  # Windows paths
        r"/home/[^'\"]+",         # Linux home paths
        r"/Users/[^'\"]+",       # macOS paths
        r"/Volumes/[^'\"]+",    # macOS volumes
        r"P:\\[^'\"]+",        # Explicit P: drives
    ]
    for pattern in patterns:
        source = re.sub(r"^\./", "", content, flags=re.MULTILINE)
        for match in re.finditer(pattern, source):
            issues.append(f"Hardcoded path: {match.group()}")
    return issues
def scan_source_paths(plugins_dir: Path) -> list[dict]:
    """Recursively scan source files for hardcoded paths."""
    findings = []
    if not plugins_dir.exists():
        return findings
    exts = {".py", ".js", ".ts", ".sh", ".bash", ".md", ".yaml", ".yml", ".json"}
    for plugin in plugins_dir.iterdir():
        if plugin.name.startswith("."):
            continue
        for fpath in plugin.rglob("*"):
            if fpath.is_file() and fpath.suffix in exts:
                issues = _scan_paths(fpath, plugin.name)
                for issue in issues:
                    findings.append({"plugin": plugin.name, "file": str(fpath.relative_to(plugin)), "issue": issue})
    return findings

def audit_name_conflicts() -> list[dict]:
    """Check for conflicting skill and command names across global and local skill/command dirs."""
    findings = []
    # Collect skills/commands from: ~/.claude/ and P:/.claude/
    skill_dirs = [
        Path(os.path.expanduser("~/.claude/skills")),
        Path("P:/.claude/skills"),
    ]
    cmd_dirs = [
        Path(os.path.expanduser("~/.claude/commands")),
        Path("P:/.claude/commands"),
    ]
    # Collect skill names (subdirectory with SKILL.md or .md file under skills/)
    skill_names: dict[str, list[str]] = {}
    for sd in skill_dirs:
        if not sd.exists():
            continue
        for item in sd.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                name = item.name
                skill_names.setdefault(name, []).append(str(sd))
            elif item.is_file() and item.suffix == ".md":
                name = item.stem
                skill_names.setdefault(name, []).append(str(sd))

    # Collect command names (filename without .md under commands/)
    cmd_names: dict[str, list[str]] = {}
    for cd in cmd_dirs:
        if not cd.exists():
            continue
        for item in cd.iterdir():
            if item.is_file() and item.suffix == ".md":
                name = item.stem
                cmd_names.setdefault(name, []).append(str(cd))

    # Report conflicts (same name in multiple locations)
    for name, locations in skill_names.items():
        if len(locations) > 1:
            findings.append({
                "type": "skill",
                "name": name,
                "locations": locations,
                "issue": f"Skill '{name}' found in multiple locations: {'; '.join(locations)}"
            })
    for name, locations in cmd_names.items():
        if len(locations) > 1:
            findings.append({
                "type": "command",
                "name": name,
                "locations": locations,
                "issue": f"Command '{name}' found in multiple locations: {'; '.join(locations)}"
            })
    return findings

def auto_fix_plugins(plugins_dir: Path, delete_hooks: bool) -> list[dict]:
    """Auto-fix common issues."""
    results = []
    if not plugins_dir.exists():
        return results
    for plugin in sorted(plugins_dir.iterdir()):
        if plugin.name.startswith("."):
            continue
        result = {"plugin": plugin.name, "actions": [], "fixed": False}
        # Fix broken symlinks
        if plugin.is_symlink() and not plugin.exists():
            if delete_hooks:
                plugin.unlink()
                result["actions"].append("Removed broken symlink")
                result["fixed"] = True
            else:
                result["actions"].append("Broken symlink (needs --auto-fix --delete-hooks)")
        else:
            # Fix invalid plugin.json
            manifest_path = plugin / ".claude-plugin" / "plugin.json"
            if manifest_path.exists():
                ok, data = _load_json(manifest_path)
                if not ok:
                    fixed_data = {"name": plugin.name, "version": "1.0.0", "description": "Auto-fixed manifest"}
                    if _save_json(manifest_path, fixed_data):
                        result["actions"].append("Auto-fixed invalid plugin.json")
                        result["fixed"] = True
            # Fix invalid hooks.json
            hooks_path = plugin / "hooks.json"
            ok, _ = _load_json(hooks_path)
            if not hooks_path.exists():
                if _save_json(hooks_path, {}):
                    result["actions"].append("Created missing hooks.json")
                    result["fixed"] = True
            elif not ok:
                if _save_json(hooks_path, {}):
                    result["actions"].append("Auto-fixed invalid hooks.json")
                    result["fixed"] = True
            elif delete_hooks and hooks_path.exists():
                hooks_path.unlink()
                result["actions"].append("Deleted hooks.json")
                result["fixed"] = True
        results.append(result)
    return results
def auto_fix_skill_state_dirs(plugins_dir: Path) -> list[dict]:
    """Delete .claude/ and .state/ directories inside skills/ subdirectories."""
    import shutil
    results = []
    if not plugins_dir.exists():
        return results
    for plugin in sorted(plugins_dir.iterdir()):
        if plugin.name.startswith("."):
            continue
        result = {"plugin": plugin.name, "actions": [], "fixed": False}
        skills_dir = plugin / "skills"
        if not skills_dir.is_dir():
            results.append(result)
            continue
        for skill_item in sorted(skills_dir.iterdir()):
            if not skill_item.is_dir():
                continue
            for bad in [".claude", ".state"]:
                bad_dir = skill_item / bad
                if bad_dir.exists() and bad_dir.is_dir():
                    try:
                        shutil.rmtree(bad_dir)
                        result["actions"].append(f"Deleted {bad}/ inside skills/{skill_item.name}/")
                        result["fixed"] = True
                    except OSError as e:
                        result["actions"].append(f"Failed to delete {bad}/ inside skills/{skill_item.name}/: {e}")
        results.append(result)
    return results
def auto_fix_git_artifacts(plugins_dir: Path) -> list[dict]:
    """Add build artifacts to .gitignore files when they exist in plugin root without being gitignored."""
    results = []
    if not plugins_dir.exists():
        return results
    # .git always exists in repos; .pytest_cache is the only other artifact we auto-fix
    auto_fix_artifacts = [".pytest_cache"]
    for plugin in sorted(plugins_dir.iterdir()):
        if plugin.name.startswith("."):
            continue
        result = {"plugin": plugin.name, "actions": [], "fixed": False}
        gitignore_path = plugin / ".gitignore"
        gitignore_entries = set()
        if gitignore_path.exists():
            with open(gitignore_path, encoding="utf-8") as f:
                gitignore_entries = {line.strip() for line in f if line.strip() and not line.startswith("#")}
        for artifact in auto_fix_artifacts:
            artifact_path = plugin / artifact
            if not artifact_path.exists():
                continue
            if artifact in gitignore_entries or artifact + "/" in gitignore_entries:
                continue
            try:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{artifact}\n")
                result["actions"].append(f"Added {artifact} to .gitignore")
                result["fixed"] = True
            except OSError as e:
                result["actions"].append(f"Failed to update .gitignore: {e}")
        results.append(result)
    return results

def main(argv: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Audit and fix Claude Code plugins")
    parser.add_argument("--marketplace-root", default=None, help="Marketplace root directory")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--delete-hooks", action="store_true", help="Delete hooks.json (use with --auto-fix)")
    parser.add_argument("--scan-paths", action="store_true", help="Scan for hardcoded paths")
    parser.add_argument("--scan-name-conflicts", action="store_true", help="Scan for conflicting skill/command names across global and local dirs")
    parser.add_argument("--validate", action="store_true", help="Run 'claude plugin validate' on each plugin")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args(argv[1:])
    resolved_root = args.marketplace_root or os.environ.get("CLAUDE_MARKETPLACE_ROOT")
    script_path = __file__ if "__file__" in dir() else "plugin-audit-and-fix.py"
    mp_root = _detect_marketplace_root(script_path, resolved_root)
    if not mp_root:
        print("Error: Cannot detect marketplace root. Use --marketplace-root or set CLAUDE_MARKETPLACE_ROOT.", file=sys.stderr)
        return 1
    plugins_dir = Path(mp_root) / "plugins"
    C = C_CYAN
    print(f"{C}=== Claude Code Plugin Audit & Fix ==={C}\\nMarketplace: {mp_root}")
    if args.scan_paths:
        print("Scanning for hardcoded paths...")
        findings = scan_source_paths(plugins_dir)
        if findings:
            print(f"{C_RED}Found {len(findings)} hardcoded path(s):{C_RESET}")
            for f in findings:
                print(f"  [{f['plugin']}] {f['file']}: {f['issue']}")
        else:
            print(f"{C_GREEN}No hardcoded paths found.{C_RESET}")
        return 0
    if args.scan_name_conflicts:
        print("Scanning for name conflicts across skill and command directories...")
        conflict_results = audit_name_conflicts()
        if conflict_results:
            print(f"{C_RED}Found {len(conflict_results)} name conflict(s):{C_RESET}")
            for c in conflict_results:
                print(f"  [{c['type']}] {c['name']}: {c['issue']}")
        else:
            print(f"{C_GREEN}No name conflicts found.{C_RESET}")
        return 0
    if args.validate:
        print("Validating plugins...")
        failed = 0
        for plugin in sorted(plugins_dir.iterdir()):
            if plugin.name.startswith("."):
                continue
            plugin_dir = str(plugin)
            result = __import__("subprocess").run(
                ["claude", "plugin", "validate", plugin_dir],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  {C_GREEN}✓ {plugin.name}{C_RESET}")
            else:
                print(f"  {C_RED}✗ {plugin.name}{C_RESET}")
                failed += 1
        if failed > 0:
            print(f"{C_RED}{failed} plugin(s) failed validation{C_RESET}")
        else:
            print(f"{C_GREEN}All plugins validated{C_RESET}")
        return failed
    print("Auditing plugins...")
    plugin_results = audit_plugins(plugins_dir, mp_root)
    error_count = sum(len(r["errors"]) for r in plugin_results)
    warning_count = sum(len(r["warnings"]) for r in plugin_results)
    if error_count > 0 or warning_count > 0:
        print(f"{C_RED}Found {error_count} error(s), {warning_count} warning(s){C_RESET}")
        for r in plugin_results:
            for e in r["errors"]: print(f"  [ERROR] {r['plugin']}: {e}")
            for w in r["warnings"]: print(f"  [WARNING] {r['plugin']}: {w}")
    else:
        print(f"{C_GREEN}All plugins OK.{C_RESET}")
    if args.auto_fix:
        fix_results = auto_fix_plugins(plugins_dir, args.delete_hooks)
        fix_count = sum(len(r["actions"]) for r in fix_results)
        print(f"{C_GREEN}Fixed {fix_count} issue(s).{C_RESET}")
        for r in fix_results:
            for action in r["actions"]:
                print(f"  [{r['plugin']}] {action}")
        skill_state_results = auto_fix_skill_state_dirs(plugins_dir)
        skill_fix_count = sum(len(r["actions"]) for r in skill_state_results)
        if skill_fix_count > 0:
            print(f"{C_GREEN}Deleted {skill_fix_count} stale skill-state dir(s).{C_RESET}")
            for r in skill_state_results:
                for action in r["actions"]:
                    print(f"  [{r['plugin']}] {action}")
        git_results = auto_fix_git_artifacts(plugins_dir)
        git_fix_count = sum(len(r["actions"]) for r in git_results)
        if git_fix_count > 0:
            print(f"{C_GREEN}Added .git to {git_fix_count} .gitignore file(s).{C_RESET}")
            for r in git_results:
                for action in r["actions"]:
                    print(f"  [{r['plugin']}] {action}")
        print(f"\n{C_CYAN}=== Next Steps ==={C_RESET}")
        print(f"  1. Run with --ScanForHardcodedPaths to detect hardcoded paths")
        print(f"  2. Run with --ScanNameConflicts to detect conflicting skill/command names")
        print(f"  3. Run with --Validate to validate all plugins")
        print(f"  4. Update marketplace: {C_CYAN}/plugin marketplace update local{C_RESET}")
    return error_count
if __name__ == "__main__":
    sys.exit(main(sys.argv))