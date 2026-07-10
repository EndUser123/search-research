#!/usr/bin/env python3
"""hooks_audit.py — self-verification for the hook ecosystem.

The hooks enforce behavior on the model; nothing verified the hooks.
This script closes that loop. Motivating failures (2026-07-09 session):
  - HOOKS_CATALOG.md claimed a module was missing that existed and was live
  - an injected prompt pointed at a doc that never existed anywhere
  - a semantic layer never fired once, its keyword fallback became the
    primary trigger path (1671 vs 614), unnoticed for weeks
  - a registered-looking hook was in no dispatch chain at all

Checks (all stdlib, no model calls, no imports of hook code by default):
  1. REGISTRATION  every script path in settings.json commands exists;
                   plugin hooks route via __lib/router.py (router pattern) —
                   direct registration of a plugin-hosted script is flagged
                   as a convention violation.
  2. SYNTAX        every .py under hooks/ ast-parses (no side effects).
  3. DANGLING PATHS path-like string literals inside hook sources
                   (P:/..., *.md) that don't exist on disk.
  4. CATALOG DRIFT hook filenames named in HOOKS_CATALOG.md that don't
                   exist on disk, and stale "[DISABLED...missing X]" notes
                   where X actually exists.
  5. STATS ANOMALY any *stats*.json under logs/ where a 'fallback' counter
                   exceeds the sum of non-fallback counters.
  6. HYGIENE       .bak/.DISABLED/.disabled files living in live hook dirs
                   (belongs in hooks/_archive/ or git).
  7. IMPORTS       (opt-in: --imports) try to import each top-level hook.
                   Off by default: import side effects, and the production
                   interpreter (3.13+) differs from wherever this runs.

Exit code: number of failing categories (0 = clean). Run manually or on
a schedule; deliberately not a hook itself.

Usage:
    python hooks_audit.py [--root P:/.claude] [--packages P:/packages] [--imports]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import time
from pathlib import Path

PATHLIKE_RE = re.compile(r"""["']([A-Za-z]:/[^"'\s]+?\.(?:md|py|json|yaml|yml|txt))["']""")
BAK_PATTERNS = ("*.bak", "*.bak-*", "*.DISABLED", "*.disabled", "*.old")


def norm(p: str) -> str:
    return p.replace("\\", "/")


def iter_settings_commands(settings: dict):
    for event, entries in (settings.get("hooks") or {}).items():
        for entry in entries:
            for h in entry.get("hooks", []):
                yield event, entry.get("matcher", ""), h.get("command", "")


def script_paths_from_command(cmd: str) -> list[str]:
    """Extract path-like tokens from a hook command line."""
    return [t.strip('"') for t in cmd.split() if norm(t.strip('"')).endswith(".py")]


def to_local(path_str: str, drive_map: dict[str, Path]) -> Path | None:
    """Map a P:/... style path to a locally readable Path, if possible.

    Picks the longest drive_map prefix whose joined path actually exists on disk
    (falling back to raw Path() if it exists). Previous version always took the
    first prefix match, which produced false-positive "script missing" findings
    whenever a drive_map value was a SUBDIR of the matched prefix (e.g.
    drive_map["P:/packages"] = P:/packages/.claude-marketplace/plugins -> joining
    P:/packages/.claude-marketplace/plugins/snapshot_PreCompact.py doubled the
    marketplace segment to plugins/.claude-marketplace/plugins/snapshot_PreCompact.py).
    """
    n = norm(path_str)
    best: Path | None = None
    best_len = -1
    for prefix, local in drive_map.items():
        if not n.lower().startswith(prefix.lower()):
            continue
        tail = n[len(prefix):].lstrip("/")
        cand = (local / tail) if tail else local
        if cand.exists() and len(prefix) > best_len:
            best, best_len = cand, len(prefix)
    raw = Path(n)
    if raw.exists() and best_len < len(n):
        best = raw
    return best



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="P:/.claude")
    ap.add_argument("--packages", default="P:/packages")
    ap.add_argument("--imports", action="store_true", help="also try importing hooks (side effects!)")
    ap.add_argument("--emit-catalog", action="store_true",
                    help="WRITE hooks/HOOKS_CATALOG.md from filesystem + registration data (overwrites)")
    ap.add_argument("--state-gc-days", type=int, default=30,
                    help="flag state files older than N days (default 30; report-only, never deletes)")
    args = ap.parse_args()

    root = Path(args.root)
    packages = Path(args.packages)
    # When run from the Cowork sandbox the drive letters don't exist; allow env-free
    # dual-mode by falling back to mounted paths.
    if not root.exists():
        for cand in ("/sessions",):
            hits = list(Path(cand).glob("*/mnt/.claude")) if Path(cand).exists() else []
            if hits:
                root = hits[0]
                packages = hits[0].parent / "packages"
                break
    if not root.exists():
        print(f"FATAL: hooks root not found: {args.root}")
        return 1

    hooks_dir = root / "hooks"
    drive_map = {"P:/.claude": root, "P:/packages": packages}
    failures: dict[str, list[str]] = {}

    def fail(cat: str, msg: str) -> None:
        failures.setdefault(cat, []).append(msg)

    # --- 1. REGISTRATION -------------------------------------------------
    settings_file = root / "settings.json"
    registered_scripts: set[str] = set()
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        for event, matcher, cmd in iter_settings_commands(settings):
            for sp in script_paths_from_command(cmd):
                n = norm(sp)
                registered_scripts.add(Path(n).name)
                local = to_local(n, drive_map)
                if local is None or not local.exists():
                    fail("REGISTRATION", f"{event} [{matcher}]: script missing: {sp}")
            # Router convention: plugin-hosted hooks must dispatch via __lib/router.py
            n_all = norm(cmd)
            if "/plugins/" in n_all and "router.py" not in n_all:
                fail("REGISTRATION", f"{event} [{matcher}]: plugin hook registered directly "
                                     f"(convention: route via __lib/router.py): {cmd}")
    except Exception as e:
        fail("REGISTRATION", f"cannot parse {settings_file}: {e}")

    # Plugin hooks.json manifests: commands must exist and use router or namespaced scripts
    # Convention: plugins live in .claude-marketplace/plugins/<name>/ — do NOT
    # recursively walk the whole monorepo (.github_repos alone makes that minutes-slow).
    plugin_root = packages / ".claude-marketplace" / "plugins"
    if plugin_root.exists():
        for hj in plugin_root.glob("*/hooks/hooks.json"):
            try:
                manifest = json.loads(hj.read_text(encoding="utf-8"))
                for event, matcher, cmd in iter_settings_commands(manifest):
                    for sp in script_paths_from_command(cmd):
                        local = to_local(norm(sp), drive_map)
                        # plugin cache paths (C:/Users/...) can't be checked from here; skip
                        if local is not None and not local.exists():
                            fail("REGISTRATION", f"{hj}: {event} script missing: {sp}")
            except Exception as e:
                fail("REGISTRATION", f"cannot parse {hj}: {e}")

    # --- 2. SYNTAX + 3. DANGLING PATHS -----------------------------------
    py_files = [p for p in hooks_dir.rglob("*.py") if "__pycache__" not in p.parts and "_archive" not in p.parts]
    for py in py_files:
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            fail("SYNTAX", f"{py.name}: unreadable: {e}")
            continue
        try:
            ast.parse(src, filename=str(py))
        except SyntaxError as e:
            fail("SYNTAX", f"{py.relative_to(root)}: line {e.lineno}: {e.msg}")
            continue
        # dangling path literals (only inside string constants, via AST, to skip comments)
        try:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for ref in PATHLIKE_RE.findall(f'"{node.value}"'):
                        local = to_local(ref, drive_map)
                        if local is not None and not local.exists() and not Path(norm(ref)).exists():
                            fail("DANGLING_PATHS", f"{py.relative_to(root)}: references missing {ref}")
                        elif local is None:
                            # unmapped drive path — can't verify here, only flag P:/ ones
                            if norm(ref).lower().startswith(("p:/.claude", "p:/packages")):
                                fail("DANGLING_PATHS", f"{py.relative_to(root)}: references missing {ref}")
        except Exception:
            pass

    # --- 4. CATALOG DRIFT --------------------------------------------------
    catalog = hooks_dir / "HOOKS_CATALOG.md"
    if catalog.exists():
        text = catalog.read_text(encoding="utf-8", errors="replace")
        on_disk = {p.name for p in py_files}
        # one pruned pass over plugin dirs only, not the whole monorepo
        if plugin_root.exists():
            on_disk |= {p.name for p in plugin_root.glob("*/hooks/*.py")}
            on_disk |= {p.name for p in plugin_root.glob("*/skills/*/hooks/*.py")}
        for name in set(re.findall(r"`([A-Za-z0-9_\-.]+\.py)`", text)):
            if name not in on_disk:
                fail("CATALOG_DRIFT", f"HOOKS_CATALOG.md names `{name}` — not found in hooks/ or plugin dirs")
        for m in re.finditer(r"missing\s+([A-Za-z0-9_]+)\s+module", text, re.IGNORECASE):
            mod = m.group(1)
            if (hooks_dir / f"{mod}.py").exists():
                fail("CATALOG_DRIFT", f"HOOKS_CATALOG.md claims '{mod}' missing, but {mod}.py exists")

    # --- 5. STATS ANOMALY ---------------------------------------------------
    logs = root / "hooks" / "logs"
    if logs.exists():
        for sf in logs.glob("*stats*.json"):
            try:
                stats = json.loads(sf.read_text(encoding="utf-8"))
                if not isinstance(stats, dict):
                    continue
            except json.JSONDecodeError as e:
                # Fail fast, don't skip: a corrupt stats file usually means a
                # non-atomic writer was interrupted mid-write.
                fail("STATS_ANOMALY", f"{sf.name}: corrupt JSON ({e}) — check for non-atomic writers")
                continue
            try:
                numeric = {k: v for k, v in stats.items() if isinstance(v, (int, float))}
                fb = sum(v for k, v in numeric.items() if "fallback" in k.lower())
                primary = sum(v for k, v in numeric.items() if "fallback" not in k.lower())
                if fb > primary > 0:
                    fail("STATS_ANOMALY", f"{sf.name}: fallback count {fb} exceeds primary {primary} "
                                          f"— a degraded path has become the main path")
            except Exception:
                continue

    # --- 6. HYGIENE ----------------------------------------------------------
    for pat in BAK_PATTERNS:
        for f in hooks_dir.rglob(pat):
            if "_archive" not in f.parts:
                fail("HYGIENE", f"stale copy in live dir: {f.relative_to(root)} (move to hooks/_archive/ or rely on git)")

    # --- 7. STATE_GC (report-only, never deletes) ----------------------------
    # Flag files in hooks/state/, hooks/session_data/, and *.json.1 rotation debris
    # older than --state-gc-days. No mutation; deletion is a separate task.
    gc_cutoff = time.time() - args.state_gc_days * 86400
    for sd in (hooks_dir / "state", hooks_dir / "session_data"):
        if not sd.exists():
            continue
        for f in sd.rglob("*"):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime < gc_cutoff:
                age_days = (time.time() - mtime) / 86400
                fail("STATE_GC", f"{f.relative_to(root)}: age {age_days:.1f}d > {args.state_gc_days}d threshold")
    for f in hooks_dir.rglob("*.json.1"):
        if "__pycache__" in f.parts or "_archive" in f.parts:
            continue
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if mtime < gc_cutoff:
            age_days = (time.time() - mtime) / 86400
            fail("STATE_GC", f"{f.relative_to(root)}: rotation debris {age_days:.1f}d old")

    # --- 8. IMPORTS (opt-in) ---------------------------------------------------
    if args.imports:
        import importlib.util
        sys.path.insert(0, str(hooks_dir))
        for py in py_files:
            if py.parent != hooks_dir:
                continue  # top-level only; submodules need their dispatcher context
            try:
                spec = importlib.util.spec_from_file_location(py.stem, py)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except SystemExit:
                pass
            except Exception as e:
                fail("IMPORTS", f"{py.name}: {type(e).__name__}: {e}")

    # --- report -----------------------------------------------------------------
    checks = ["REGISTRATION", "SYNTAX", "DANGLING_PATHS", "CATALOG_DRIFT", "STATS_ANOMALY", "HYGIENE", "STATE_GC"]
    if args.imports:
        checks.append("IMPORTS")

    # --- --emit-catalog: regenerate HOOKS_CATALOG.md from ground truth ----------
    if args.emit_catalog:
        catalog = hooks_dir / "HOOKS_CATALOG.md"
        settings_cmds: list = []
        try:
            settings = json.loads((root / "settings.json").read_text(encoding="utf-8"))
            settings_cmds = list(iter_settings_commands(settings))
        except Exception:
            pass
        plugin_py: list = []
        if plugin_root.exists():
            plugin_py += [(p, "plugin/hooks") for p in plugin_root.glob("*/hooks/*.py")]
            plugin_py += [(p, "plugin/skill/hooks") for p in plugin_root.glob("*/skills/*/hooks/*.py")]
            plugin_py += [(p, "plugin/__lib/router") for p in plugin_root.glob("*/__lib/router.py")]
        registered = {Path(norm(sp)).name for _, _, cmd in settings_cmds
                      for sp in script_paths_from_command(cmd)}
        out = ["# CSF Hooks Catalog", "",
               "> Regenerated from filesystem + settings.json by `hooks_audit.py --emit-catalog`.",
               "> Every row is observed, not hand-curated. Hand-curated perspectives",
               "> (by domain / enforcement / ownership) belong in a separate doc on top of this.",
               "", f"Last regenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}", "",
               f"- Hooks on disk: {len(py_files)} in hooks/, {len(plugin_py)} in plugin dirs.",
               f"- settings.json commands: {len(settings_cmds)}.", "",
               "## settings.json dispatch", "",
               "| Event | Matcher | Script |", "|-------|---------|--------|"]
        for ev, ma, cmd in settings_cmds:
            for sp in script_paths_from_command(cmd):
                out.append(f"| {ev} | `{ma}` | `{sp}` |")
        out += ["", "## Hooks on disk", "", "| Path | In settings? | Where |",
                "|------|--------------|-------|"]
        for p, where in sorted([(x, "hooks/") for x in py_files] + plugin_py, key=lambda t: str(t[0])):
            try:
                rel = p.relative_to(root)
            except ValueError:
                rel = p
            tag = "yes" if p.name in registered else "-"
            out.append(f"| `{rel}` | {tag} | {where} |")
        catalog.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"emitted: {catalog} ({len(py_files) + len(plugin_py)} hooks)")
    print(f"hooks_audit: scanned {len(py_files)} hook files under {hooks_dir}")
    for cat in checks:
        msgs = failures.get(cat, [])
        status = "FAIL" if msgs else "ok"
        print(f"[{status:4}] {cat} ({len(msgs)})")
        for m in msgs[:25]:
            print(f"       - {m}")
        if len(msgs) > 25:
            print(f"       ... and {len(msgs) - 25} more")
    return len([c for c in checks if failures.get(c)])


if __name__ == "__main__":
    sys.exit(main())
