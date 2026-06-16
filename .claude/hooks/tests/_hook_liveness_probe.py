#!/usr/bin/env python3
"""Subprocess worker for test_hook_registration_liveness.

Loads ONE hook file in an isolated interpreter (mirroring the runtime, where
each subprocess-registered hook runs as its own `python X.py` process) and
reports two things as JSON on stdout:

  1. ok / error          — did the module's TOP-LEVEL import path resolve?
                           (catches dead `from X import Y` at module scope)
  2. unresolved[]        — first-party DEFERRED imports (inside function bodies)
                           that do not resolve via find_spec. This is the
                           veridical-gate class: a lazy `from _veridical_gate
                           import ...` shim that never existed, swallowed by a
                           fail-open try/except, so the gate silently died while
                           its unit tests still passed.

Run isolation is deliberate: importing ~100 hook modules in one process risks
sys.modules / sys.path cross-contamination (local wrapper vs plugin twin share
stems). One subprocess per file removes that whole class of false signal.

Always exits 0; the parent reads the JSON verdict. This is a test helper, not a
pytest module (no test_ prefix → not collected).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import traceback
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

# Top-level package names that are first-party to this hook tree. A DEFERRED
# import of one of these that fails to resolve is a real liveness defect, not an
# optional third-party dependency with an intended fallback. Underscore-prefixed
# modules (e.g. the dead `_veridical_gate` shim) are always treated first-party.
FIRST_PARTY_HINTS = {
    "anti_sycophancy",
    "verification",
    "validators",
    "scanners",
    "posttooluse",
    "UserPromptSubmit_modules",
}
# Excluded on purpose: 'daemons'/'shared' name optional contrib namespaces that
# hooks load behind `if path.exists()` + fail-open try/except (e.g. the
# semantic_daemon write-signal client). Their absence is graceful degradation,
# not a dead gate — flagging them would be a false positive.


def setup_base_syspath(target: Path) -> None:
    """Replicate the runtime sys.path a `python <hook>.py` subprocess sees:
    the script's OWN directory is on sys.path[0] (CPython does this for the main
    script — importlib.exec_module does not), plus the global hooks dir + __lib
    that local hooks and bootstraps expect. Plugin hooks add their own plugin
    roots via their top-of-file bootstrap block when exec'd."""
    for p in (HOOKS_DIR, HOOKS_DIR / "__lib", target.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build import spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    # Register under stem so intra-module relative refs resolve like the runtime.
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod


def deferred_imports(source: str):
    """Yield (top_pkg, full_module, lineno) for imports nested inside function
    bodies — i.e. imports that a plain module load does NOT execute."""
    out = []

    class V(ast.NodeVisitor):
        def __init__(self) -> None:
            self.depth = 0

        def visit_FunctionDef(self, node):
            self.depth += 1
            self.generic_visit(node)
            self.depth -= 1

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Import(self, node):
            if self.depth > 0:
                for alias in node.names:
                    out.append((alias.name.split(".")[0], alias.name, node.lineno))
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            # level==0 → absolute import; module is None for `from . import x`
            if self.depth > 0 and node.module and node.level == 0:
                out.append((node.module.split(".")[0], node.module, node.lineno))
            self.generic_visit(node)

    V().visit(ast.parse(source))
    return out


def is_first_party(top: str) -> bool:
    if top.startswith("_"):
        return True
    if top in FIRST_PARTY_HINTS:
        return True
    if (HOOKS_DIR / f"{top}.py").exists() or (HOOKS_DIR / top).is_dir():
        return True
    return False


def main() -> None:
    path = Path(sys.argv[1])
    # Optional context module: imported FIRST to replicate an in-process
    # environment. Stop.py's IN_PROCESS_GATES gate modules run inside Stop.py's
    # process, so they rely on the sys.path Stop.py sets up at module load
    # (e.g. the cc-aca-epistemic __lib that holds compat_loader). The test
    # passes Stop.py as context for those modules so the probe matches runtime.
    context = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    res = {"path": str(path), "ok": False, "error": None, "unresolved": []}

    if not path.exists():
        res["error"] = "FILE_NOT_FOUND: registration points at a missing file"
        print(json.dumps(res))
        return

    setup_base_syspath(path)
    if context is not None and context.exists():
        try:
            load_module(context)
        except Exception:  # noqa: BLE001 — context load must not mask target
            pass
    try:
        load_module(path)
    except Exception as exc:  # noqa: BLE001 — any load failure is the signal
        res["error"] = f"{type(exc).__name__}: {exc}"
        res["traceback"] = traceback.format_exc()[-1800:]
        print(json.dumps(res))
        return

    res["ok"] = True

    # Deferred-import resolution scan (veridical-gate class).
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        seen = set()
        for top, full, lineno in deferred_imports(src):
            if full in seen:
                continue
            seen.add(full)
            try:
                spec = importlib.util.find_spec(full)
            except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
                spec = None
            if spec is None and is_first_party(top):
                res["unresolved"].append({"module": full, "line": lineno})
    except Exception as exc:  # noqa: BLE001
        res["scan_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(res))


if __name__ == "__main__":
    main()
