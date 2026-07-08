"""Stdlib-only self-check for gitpack dependency resolution.

Builds a temp plugin-shaped tree where a skill imports from plugin-level
__lib__ and scripts/, and asserts resolve_dependencies closes the set over
those imports + path refs, while leaving stdlib/third-party imports alone.

Run: `python test_gitpack_deps.py`.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gitpack import (  # noqa: E402
    resolve_dependencies,
    _resolve_abs_module,
    _resolve_rel_module,
    _extract_python_imports,
)


def _build_tree(root):
    """root/ = plugin root. Returns skill_dir."""
    skill_dir = root / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# demo\nSee [shared](../../__lib__/shared.py) and "
        "run scripts/run.py.\n", encoding="utf-8")
    # skill-owned module: imports a plugin-level __lib__ module + stdlib + third-party
    (skill_dir / "main.py").write_text(
        "import json\n"                              # stdlib -> skip
        "import os\n"                                # stdlib -> skip
        "from __lib__.shared import helper\n"        # plugin-level -> include
        "from .sibling import x\n"                   # skill sibling -> include
        "import libcst\n"                            # third-party -> skip
        "", encoding="utf-8")
    (skill_dir / "sibling.py").write_text("# sibling\n", encoding="utf-8")
    # plugin-level shared module that itself imports another plugin module (transitive)
    lib_dir = root / "__lib__"
    lib_dir.mkdir()
    (lib_dir / "shared.py").write_text(
        "from __lib__.util import thing\n"           # transitive dep
        "def helper():\n    return 1\n", encoding="utf-8")
    (lib_dir / "util.py").write_text("thing = 1\n", encoding="utf-8")
    # plugin-level scripts/ referenced from SKILL.md path ref
    scripts_dir = root / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.py").write_text("# run\n", encoding="utf-8")
    return skill_dir


def test_abs_import_resolves_sibling():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill_dir = _build_tree(root)
        main = skill_dir / "main.py"
        cands = _resolve_abs_module("__lib__.shared", main, root)
        assert any(p.name == "shared.py" for p in cands), cands


def test_relative_import_resolves():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill_dir = _build_tree(root)
        main = skill_dir / "main.py"
        cands = _resolve_rel_module("sibling", 1, ["x"], main)
        assert any(p.name == "sibling.py" for p in cands), cands


def test_stdlib_not_resolved():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill_dir = _build_tree(root)
        main = skill_dir / "main.py"
        assert _resolve_abs_module("json", main, root) == []
        assert _resolve_abs_module("libcst", main, root) == []


def test_resolve_dependencies_closes_over_imports_and_refs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill_dir = _build_tree(root)
        initial = [str(skill_dir / "main.py"), str(skill_dir / "SKILL.md")]
        out = resolve_dependencies(initial, root, skill_dir=skill_dir,
                                   plugin_root=root)
        out_names = {Path(p).name for p in out}
        assert "main.py" in out_names and "sibling.py" in out_names, out_names
        assert "shared.py" in out_names, out_names      # absolute import in main.py
        assert "util.py" in out_names, out_names        # transitive (shared.py -> util)
        assert "run.py" in out_names, out_names         # path-ref from SKILL.md
        assert "json" not in out_names and "libcst" not in out_names, out_names
        # __pycache__ never appears even if present
        pc = skill_dir / "__pycache__"
        pc.mkdir()
        (pc / "x.py").write_text("x", encoding="utf-8")
        assert not any("__pycache__" in p for p in out), out


def test_out_of_scope_not_pulled():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "plugin"
        root.mkdir()
        outside = Path(tmp) / "outside.py"
        outside.write_text("# outside\n", encoding="utf-8")
        skill_dir = root / "skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# s\n", encoding="utf-8")
        (skill_dir / "a.py").write_text("# a\n", encoding="utf-8")
        out = resolve_dependencies([str(skill_dir / "a.py")], root,
                                   skill_dir=skill_dir, plugin_root=root)
        assert str(outside.resolve()) not in out, out


def test_extract_imports_kind_level():
    with tempfile.TemporaryDirectory() as tmp:
        fp = Path(tmp) / "m.py"
        fp.write_text(
            "import json\n"
            "from os import path\n"
            "from . import x\n"
            "from ..pkg import y\n", encoding="utf-8")
        kinds = {(k, lvl) for (k, _m, lvl, _n) in _extract_python_imports(fp)}
        assert ("abs", 0) in kinds
        assert ("rel", 1) in kinds
        assert ("rel", 2) in kinds


if __name__ == "__main__":
    test_abs_import_resolves_sibling()
    test_relative_import_resolves()
    test_stdlib_not_resolved()
    test_resolve_dependencies_closes_over_imports_and_refs()
    test_out_of_scope_not_pulled()
    test_extract_imports_kind_level()
    print("OK: 6/6 dependency-resolver tests passed")
