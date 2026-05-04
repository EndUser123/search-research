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
def audit_plugins(plugins_dir: Path, marketplace_root: str, plugin_filter: Optional[str] = None) -> list[dict]:
    """Audit plugin directories and manifests."""
    results = []
    if not plugins_dir.exists():
        return results
    for plugin in sorted(plugins_dir.iterdir()):
        if plugin.name.startswith(".") or not plugin.is_dir():
            continue
        if plugin_filter and plugin.name != plugin_filter:
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
        # Check hooks.json (at hooks/hooks.json)
        hooks_path = plugin / "hooks" / "hooks.json"
        if hooks_path.exists():
            ok, data = _load_json(hooks_path)
            if not ok:
                result["errors"].append("Invalid hooks/hooks.json")
            elif not isinstance(data, dict):
                result["errors"].append("hooks/hooks.json must be a dict")
            elif "hooks" not in data:
                result["errors"].append("hooks/hooks.json missing required 'hooks' key")
            else:
                # Validate hook entry structure: each event entry needs matcher + hooks array
                for event, entries in data.get("hooks", {}).items():
                    if not isinstance(entries, list):
                        result["errors"].append(f"hooks.{event} must be a list")
                        continue
                    for i, entry in enumerate(entries):
                        if not isinstance(entry, dict):
                            result["errors"].append(f"hooks.{event}[{i}] must be a dict")
                            continue
                        if "matcher" not in entry:
                            result["errors"].append(f"hooks.{event}[{i}] missing 'matcher' field")
                        if "hooks" not in entry:
                            result["errors"].append(f"hooks.{event}[{i}] missing 'hooks' array")
                        elif not isinstance(entry["hooks"], list):
                            result["errors"].append(f"hooks.{event}[{i}].hooks must be an array")
                        else:
                            for j, hook in enumerate(entry["hooks"]):
                                if not isinstance(hook, dict):
                                    result["errors"].append(f"hooks.{event}[{i}].hooks[{j}] must be a dict")
                                elif "type" not in hook or "command" not in hook:
                                    result["errors"].append(f"hooks.{event}[{i}].hooks[{j}] missing 'type' or 'command'")
                                elif hook.get("type") == "command":
                                    cmd = hook.get("command", "")
                                    # $CLAUDE_PLUGIN_ROOT/%CLAUDE_PLUGIN_ROOT% is the correct runtime convention.
                                    # Skip path-existence check — it will expand correctly at hook execution time.
                                    has_runtime_env = (
                                        "$CLAUDE_PLUGIN_ROOT" in cmd
                                        or "%CLAUDE_PLUGIN_ROOT%" in cmd.lower()
                                    )
                                    if "$$" in cmd:
                                        result["errors"].append(
                                            f"Hook command contains double-dollar (corrupted variable): {cmd[:80]}"
                                        )
                                    # Extract script path from command (handles "python script.py --args", "node script.js", etc.)
                                    parts = cmd.split()
                                    if parts:
                                        script_path = Path(parts[-1].strip('"').strip("'"))
                                        # Pre-expand runtime env vars BEFORE relative-path prefix
                                        # to prevent double-prefix when path is not absolute
                                        path_str = str(script_path)
                                        env_vars = {"CLAUDE_PLUGIN_ROOT": str(plugin)}
                                        for var, replacement in env_vars.items():
                                            if var in path_str:
                                                path_str = path_str.replace(f"${var}", replacement)
                                        script_path = Path(path_str)
                                        # Resolve relative paths from plugin root (only if still relative after expansion)
                                        if not script_path.is_absolute():
                                            script_path = plugin / script_path
                                        # Only check existence for non-runtime commands (no $CLAUDE_PLUGIN_ROOT/%VAR%)
                                        if not has_runtime_env and not script_path.exists():
                                            result["errors"].append(f"Hook command file not found: {script_path}")
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
            # .git is always a directory in a repo; check if it's actually gitignored or has a real remote
            if artifact == ".git":
                if ".git" in gitignored:
                    continue
                # Skip warning if plugin is a real git repo with a remote — .git is appropriate there
                try:
                    check = __import__("subprocess").run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=str(plugin),
                        capture_output=True, text=True, timeout=5,
                    )
                    if check.returncode == 0 and check.stdout.strip():
                        continue  # has real remote, .git is legitimate
                except Exception:
                    pass
                # No remote detected — likely a stray clone, warn about it
                result["warnings"].append(f"Build artifact '.git' in plugin root (should be gitignored)")
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

def audit_orphan_skill_junctions(plugins_dir: Path) -> list[dict]:
    """Detect marketplace entries that are junctions to skills already inside a cluster package.

    A cluster package is any plugin that has .claude-plugin/plugin.json AND a skills/ directory
    with multiple skills. If a marketplace entry is a junction pointing to a subdirectory inside
    another cluster package's skills/ dir, it's redundant — the cluster already provides it.
    """
    findings: list[dict] = []
    if not plugins_dir.exists():
        return findings

    # Build map: cluster_name -> set of skill names it provides
    cluster_skills: dict[str, set[str]] = {}
    for plugin in plugins_dir.iterdir():
        if plugin.name.startswith(".") or not plugin.is_dir():
            continue
        manifest = plugin / ".claude-plugin" / "plugin.json"
        skills_dir = plugin / "skills"
        if manifest.exists() and skills_dir.is_dir():
            skill_names = set()
            for skill in skills_dir.iterdir():
                if skill.is_dir() and (skill / "SKILL.md").exists():
                    skill_names.add(skill.name)
            if len(skill_names) >= 2:  # Clusters have multiple skills
                cluster_skills[plugin.name] = skill_names

    # Check each plugin: is it a junction pointing into a cluster's skills/?
    for plugin in plugins_dir.iterdir():
        if plugin.name.startswith(".") or not plugin.is_dir():
            continue
        # Skip cluster packages themselves
        if plugin.name in cluster_skills:
            continue

        # Resolve junction target
        target = None
        try:
            target = os.readlink(str(plugin))
        except OSError:
            continue

        if not target:
            continue

        # Normalize path separators
        target_norm = target.replace("\\", "/").replace("/p/", "P:/")

        # Check if target points into a cluster's skills/ subdirectory
        for cluster_name, skill_names in cluster_skills.items():
            # Pattern: P:/packages/{cluster}/skills/{skill_name}
            prefix = f"P:/packages/{cluster_name}/skills/"
            if target_norm.startswith(prefix):
                skill_name = target_norm[len(prefix):]
                if skill_name in skill_names:
                    findings.append({
                        "type": "orphan_skill_junction",
                        "marketplace_entry": plugin.name,
                        "target": target_norm,
                        "cluster": cluster_name,
                        "skill": skill_name,
                        "issue": f"'{plugin.name}' is a junction to a skill already provided by cluster '{cluster_name}'",
                    })
                    break

    return findings


def audit_source_cache_drift(plugins_dir: Path) -> list[dict]:
    """Detect drift between source packages and their cache copies.

    Source is truth. Cache lives at ~/.claude/plugins/cache/local/{name}/{version}/.
    If cache files differ from source, the cache is stale.
    """
    findings: list[dict] = []
    if not plugins_dir.exists():
        return findings

    cache_root = Path(os.path.expanduser("~/.claude/plugins/cache/local"))

    for plugin in plugins_dir.iterdir():
        if plugin.name.startswith(".") or not plugin.is_dir():
            continue

        source_dir = Path(f"P:/packages/{plugin.name}")
        if not source_dir.exists():
            continue

        cache_dir = cache_root / plugin.name
        if not cache_dir.exists():
            continue

        # Find versioned directory in cache
        version_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]
        if not version_dirs:
            continue

        version_dir = version_dirs[0]  # Use first version found

        # Sample key files for drift check (don't diff everything — too slow)
        drift_files: list[str] = []
        key_patterns = ["**/*.py", "**/*.json", "**/SKILL.md"]
        for pattern in key_patterns:
            for src_file in source_dir.glob(pattern):
                if ".git" in src_file.parts or "__pycache__" in src_file.parts:
                    continue
                rel = src_file.relative_to(source_dir)
                cache_file = version_dir / rel
                if cache_file.exists():
                    try:
                        if src_file.read_text(encoding="utf-8", errors="ignore") != cache_file.read_text(encoding="utf-8", errors="ignore"):
                            drift_files.append(str(rel))
                    except OSError:
                        pass

        if drift_files:
            findings.append({
                "type": "source_cache_drift",
                "plugin": plugin.name,
                "cache_version": version_dir.name,
                "drift_count": len(drift_files),
                "sample_files": drift_files[:5],
                "issue": f"'{plugin.name}' cache ({version_dir.name}) has {len(drift_files)} file(s) diverged from source",
            })

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
        if plugin.name.startswith(".") or not plugin.is_dir():
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
            # Fix invalid hooks/hooks.json (only when hooks dir exists)
            hooks_dir = plugin / "hooks"
            if hooks_dir.is_dir():
                hooks_path = hooks_dir / "hooks.json"
                ok, data = _load_json(hooks_path)
                if not hooks_path.exists():
                    if _save_json(hooks_path, {}):
                        result["actions"].append("Created missing hooks/hooks.json")
                        result["fixed"] = True
                elif not ok:
                    if _save_json(hooks_path, {}):
                        result["actions"].append("Auto-fixed invalid hooks/hooks.json")
                        result["fixed"] = True
                elif delete_hooks:
                    hooks_path.unlink()
                    result["actions"].append("Deleted hooks/hooks.json")
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

def bump_version(plugins_dir: Path, marketplace_root: str, plugin_name: str) -> dict:
    """Bump patch version for a plugin in all three version locations."""
    result = {"plugin": plugin_name, "actions": [], "old_version": None, "new_version": None, "errors": []}
    plugin_dir = plugins_dir / plugin_name
    if not plugin_dir.exists():
        result["errors"].append(f"Plugin directory not found: {plugin_dir}")
        return result

    # 1. Read current version from plugin.json
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        result["errors"].append("Missing .claude-plugin/plugin.json")
        return result
    ok, manifest = _load_json(manifest_path)
    if not ok or "version" not in manifest:
        result["errors"].append("Invalid or version-less plugin.json")
        return result
    old_ver = manifest["version"]
    result["old_version"] = old_ver

    # Bump patch version
    parts = old_ver.split(".")
    if len(parts) != 3:
        result["errors"].append(f"Unexpected version format: {old_ver}")
        return result
    parts[2] = str(int(parts[2]) + 1)
    new_ver = ".".join(parts)
    result["new_version"] = new_ver

    # 2. Update plugin.json
    manifest["version"] = new_ver
    if _save_json(manifest_path, manifest):
        result["actions"].append(f"Updated .claude-plugin/plugin.json: {old_ver} → {new_ver}")
    else:
        result["errors"].append("Failed to save plugin.json")

    # 3. Update both marketplace.json files
    for mp_path in [
        Path(marketplace_root) / "marketplace.json",
        Path(marketplace_root) / ".claude-plugin" / "marketplace.json",
    ]:
        if not mp_path.exists():
            continue
        ok, mp_data = _load_json(mp_path)
        if not ok or "plugins" not in mp_data:
            result["errors"].append(f"Invalid marketplace.json at {mp_path}")
            continue
        found = False
        for entry in mp_data["plugins"]:
            if entry.get("name") == plugin_name:
                entry["version"] = new_ver
                found = True
                break
        if not found:
            result["errors"].append(f"Plugin '{plugin_name}' not found in {mp_path}")
            continue
        if _save_json(mp_path, mp_data):
            result["actions"].append(f"Updated {mp_path.name}: {old_ver} → {new_ver}")
        else:
            result["errors"].append(f"Failed to save {mp_path}")

    return result


def main(argv: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Audit and fix Claude Code plugins")
    parser.add_argument("--marketplace-root", default=None, help="Marketplace root directory")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--delete-hooks", action="store_true", help="Delete hooks.json (use with --auto-fix)")
    parser.add_argument("--scan-paths", action="store_true", help="Scan for hardcoded paths")
    parser.add_argument("--scan-name-conflicts", action="store_true", help="Scan for conflicting skill/command names across global and local dirs")
    parser.add_argument("--plugins", metavar="NAME", help="Filter to a specific plugin name")
    parser.add_argument("--validate", action="store_true", help="Run 'claude plugin validate' on each plugin")
    parser.add_argument("--bump", metavar="PLUGIN_NAME", help="Bump patch version for a plugin in all version files")
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
    if args.bump:
        bump_result = bump_version(plugins_dir, mp_root, args.bump)
        if bump_result["errors"]:
            for e in bump_result["errors"]:
                print(f"  {C_RED}ERROR: {e}{C_RESET}")
            return 1
        for a in bump_result["actions"]:
            print(f"  {C_GREEN}{a}{C_RESET}")
        print(f"\n{C_CYAN}=== Next Steps ==={C_RESET}")
        print(f"  1. /plugin marketplace update local")
        print(f"  2. /reload-plugins")
        return 0
    if args.validate:
        print("Validating plugins...")
        failed = 0
        for plugin in sorted(plugins_dir.iterdir()):
            if plugin.name.startswith("."):
                continue
            if args.plugins and plugin.name != args.plugins:
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
    plugin_results = audit_plugins(plugins_dir, mp_root, plugin_filter=args.plugins)
    error_count = sum(len(r["errors"]) for r in plugin_results)
    warning_count = sum(len(r["warnings"]) for r in plugin_results)
    if error_count > 0 or warning_count > 0:
        print(f"{C_RED}Found {error_count} error(s), {warning_count} warning(s){C_RESET}")
        for r in plugin_results:
            for e in r["errors"]: print(f"  [ERROR] {r['plugin']}: {e}")
            for w in r["warnings"]: print(f"  [WARNING] {r['plugin']}: {w}")
    else:
        print(f"{C_GREEN}All plugins OK.{C_RESET}")

    # Check for orphan skill junctions (skills duplicated outside their cluster)
    print("\nChecking for orphan skill junctions...")
    orphan_findings = audit_orphan_skill_junctions(plugins_dir)
    if orphan_findings:
        print(f"{C_YELLOW}Found {len(orphan_findings)} orphan skill junction(s):{C_RESET}")
        for f in orphan_findings:
            print(f"  {f['marketplace_entry']} -> {f['cluster']}/skills/{f['skill']}")
    else:
        print(f"{C_GREEN}No orphan skill junctions.{C_RESET}")

    # Check for source/cache drift
    print("\nChecking source vs cache drift...")
    drift_findings = audit_source_cache_drift(plugins_dir)
    if drift_findings:
        print(f"{C_YELLOW}Found {len(drift_findings)} plugin(s) with cache drift:{C_RESET}")
        for f in drift_findings:
            sample = ", ".join(f["sample_files"][:3])
            extra = f" (+{f['drift_count'] - 3} more)" if f["drift_count"] > 3 else ""
            print(f"  {f['plugin']} ({f['cache_version']}): {f['drift_count']} file(s) drifted — {sample}{extra}")
    else:
        print(f"{C_GREEN}Cache is in sync with source.{C_RESET}")

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

        # Auto-fix: remove orphan skill junctions
        if orphan_findings:
            import shutil
            print(f"\n{C_YELLOW}Removing {len(orphan_findings)} orphan skill junction(s)...{C_RESET}")
            for f in orphan_findings:
                junction_path = plugins_dir / f["marketplace_entry"]
                try:
                    if junction_path.is_dir():
                        shutil.rmtree(str(junction_path))
                    print(f"  {C_GREEN}Removed: {f['marketplace_entry']} (now via {f['cluster']}){C_RESET}")
                except OSError as e:
                    print(f"  {C_RED}Failed to remove {f['marketplace_entry']}: {e}{C_RESET}")

        # Auto-fix: sync source to cache
        if drift_findings:
            import subprocess
            print(f"\n{C_YELLOW}Syncing source -> cache for {len(drift_findings)} plugin(s)...{C_RESET}")
            cache_root = Path(os.path.expanduser("~/.claude/plugins/cache/local"))
            for f in drift_findings:
                pkg = f["plugin"]
                src = Path(f"P:/packages/{pkg}")
                version_dir = cache_root / pkg / f["cache_version"]
                if src.exists() and version_dir.exists():
                    result = subprocess.run(
                        ["robocopy", str(src), str(version_dir), "/MIR", "/XD", ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
                         "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS", "/NP"],
                        capture_output=True, text=True,
                    )
                    # robocopy returns 0-7 for success, 8+ for errors
                    if result.returncode < 8:
                        print(f"  {C_GREEN}Synced: {pkg}{C_RESET}")
                    else:
                        print(f"  {C_RED}Failed: {pkg} (robocopy exit {result.returncode}){C_RESET}")

        print(f"\n{C_CYAN}=== Next Steps ==={C_RESET}")
        print(f"  1. Run with --scan-paths to detect hardcoded paths")
        print(f"  2. Run with --scan-name-conflicts to detect conflicting skill/command names")
        print(f"  3. Run with --validate to validate all plugins")
        print(f"  4. Update marketplace: {C_CYAN}/plugin marketplace update local{C_RESET}")
    return error_count
if __name__ == "__main__":
    sys.exit(main(sys.argv))