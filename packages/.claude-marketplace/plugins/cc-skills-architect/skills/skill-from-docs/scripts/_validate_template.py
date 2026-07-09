"""skill-from-docs output validator — TEMPLATE.

Copy this file into a generated skill's scripts/ directory as `_validate.py`
and run it from the skill root to verify the output contract holds.

This template is the converter-side defense for the 6 pitfalls documented in
P:/.data/wiki/lessons/skill-from-docs-output-pitfalls.md. Every skill-from-docs
output should include this file (or one derived from it) so the pitfalls
are caught at validation time, not at runtime.

Usage:
    python scripts/_validate.py            # validate current skill
    python scripts/_validate.py --root .   # validate from explicit root
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(2)

# ROOT and SKILL are resolved lazily inside main() so tests can patch sys.argv.
ROOT: Path | None = None
SKILL: Path | None = None

results: list[tuple[str, str, str]] = []  # (gate, status, detail)


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, "PASS" if ok else "FAIL", detail))


def _resolve_paths() -> tuple[Path, Path]:
    """Resolve the skill root lazily from sys.argv. Computed at call time so
    tests can patch sys.argv before invoking main()."""
    if len(sys.argv) >= 3 and sys.argv[1] == "--root":
        root = Path(sys.argv[2]).resolve()
    else:
        root = Path(".").resolve()
    return root, root / "SKILL.md"


def main() -> int:
    global ROOT, SKILL
    ROOT, SKILL = _resolve_paths()
    # --- Existence + structure ---
    check("SKILL.md exists", SKILL.is_file(), f"path={SKILL}")
    if not SKILL.is_file():
        return 1
    check("references/ exists", (ROOT / "references").is_dir())
    check("resources/ exists", (ROOT / "resources").is_dir())
    check("scripts/ exists", (ROOT / "scripts").is_dir())

    raw = SKILL.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", raw, flags=re.DOTALL)
    check("YAML frontmatter present", bool(m))
    if not m:
        return 1
    fm = yaml.safe_load(m.group(1))

    # --- Required fields ---
    check("name field present", "name" in fm and isinstance(fm["name"], str))
    name = fm.get("name", "")
    check("name matches dir", name == ROOT.name, f"name={name!r} dir={ROOT.name!r}")
    check("description field present", "description" in fm)
    desc = str(fm.get("description", ""))
    check("description >= 100 chars", len(desc) >= 100, f"len={len(desc)}")
    check("version field present", "version" in fm)
    check("enforcement field present", "enforcement" in fm)
    check("enforcement is valid value", fm.get("enforcement") in {"strict", "advisory", "none"})

    # --- workflow_steps: structure + contract cross-check (PITFALL 1, 3) ---
    steps = fm.get("workflow_steps") if isinstance(fm.get("workflow_steps"), list) else []
    check("workflow_steps field present", bool(steps))
    if steps:
        check("workflow_steps entries have id+name", all(
            isinstance(s, dict) and {"id", "name"}.issubset(s.keys()) for s in steps
        ))
        # Cross-check: every step with a `script:` key must resolve to a file.
        for s in steps:
            if "script" in s:
                sp = ROOT / s["script"]
                check(f"step[{s.get('id')}].script resolves", sp.is_file(), f"path={sp}")

    # --- Body sections ---
    body = raw[m.end():]
    for header in ("When to use", "When NOT to use", "Output contract", "Related skills"):
        check(f"has '{header}' section", f"## {header}" in body)

    # --- Inline body code-block header drift (PITFALL 2) ---
    # If a code block in the body has a header like "# scripts/foo.py",
    # it must agree with the frontmatter `script:` key for that phase.
    body_headers = re.findall(r"^#\s*scripts/(\w+\.py)\s*$", body, flags=re.MULTILINE)
    frontmatter_scripts = {Path(s["script"]).name for s in steps if "script" in s}
    drift = [h for h in body_headers if h not in frontmatter_scripts]
    check("body code-block headers match frontmatter scripts", not drift, f"drift={drift}")

    # --- Anti-patterns: structural check, not exact-substring (PITFALL 6) ---
    has_antipatterns_header = "## Anti-patterns" in body or "## Anti-pattern" in body
    check("has Anti-patterns section", has_antipatterns_header)
    if has_antipatterns_header:
        # Structural: a markdown table row with 3+ columns. Look for "Trap | Symptom | Mitigation"
        # or any 3-column markdown table.
        table_rows = [
            line for line in body.splitlines()
            if line.startswith("|") and line.count("|") >= 4
        ]
        check("anti-patterns table has >= 2 rows (header + 1)", len(table_rows) >= 2)

    # --- Portability: detect hardcoded absolute paths in body (PITFALL 5) ---
    # Any C:/, C:\, /Users/, or /home/ path in body prose is a portability red flag.
    abs_path_patterns = [
        r"\bC:[/\\][^\s'\")\]]+",          # Windows drive paths
        r"\b/Users/\w+/[^\s'\")\]]+",        # macOS home
        r"\b/home/\w+/[^\s'\")\]]+",         # Linux home
    ]
    body_lines = body.splitlines()
    portability_violations = []
    for i, line in enumerate(body_lines, 1):
        for pat in abs_path_patterns:
            for m in re.finditer(pat, line):
                portability_violations.append(f"line {i}: {m.group(0)}")
    check(
        "no hardcoded absolute paths in body prose",
        not portability_violations,
        f"violations={portability_violations[:3]}{'...' if len(portability_violations) > 3 else ''}",
    )

    # --- Session-UUID leakage check (PITFALL 5) ---
    # Detects hardcoded session UUIDs in body (not in frontmatter metadata.source_session).
    uuid_re = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    )
    body_uuids = []
    for i, line in enumerate(body_lines, 1):
        for m in uuid_re.finditer(line):
            body_uuids.append(f"line {i}: {m.group(0)}")
    check(
        "no session UUIDs leaked into body",
        not body_uuids,
        f"uuids={body_uuids[:3]}{'...' if len(body_uuids) > 3 else ''}",
    )

    # --- Helper scripts: count + byte-compile ---
    scripts_dir = ROOT / "scripts"
    py_scripts = sorted(
        p for p in scripts_dir.glob("*.py")
        if not p.name.startswith("_") and "__pycache__" not in p.parts
    )
    check(">= 1 helper script present", len(py_scripts) >= 1, f"found={len(py_scripts)}")
    for s in py_scripts:
        try:
            compile(s.read_text(encoding="utf-8"), str(s), "exec")
            check(f"byte-compile {s.name}", True)
        except SyntaxError as e:
            check(f"byte-compile {s.name}", False, str(e))

    # --- Report ---
    print(f"PHASE 3 VALIDATION REPORT — {name}")
    print("=" * 60)
    pass_count = sum(1 for _, s, _ in results if s == "PASS")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")
    for gate, status, detail in results:
        line = f"  [{status}] {gate}"
        if detail:
            line += f"  — {detail}"
        print(line)
    print("=" * 60)
    print(f"PASS: {pass_count}   FAIL: {fail_count}   TOTAL: {len(results)}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
