---
name: gitpack
description: Pack a code or markdown directory (or a scattered set of files) into compact LLM-context files using only stdlib — AST for Python, regex signatures for JS/TS/HTML/CSS/SQL/YAML/JSON/PowerShell, and heading+frontmatter extraction for Markdown. Deterministic, no external deps. Emits <name>_sig.md (signatures + indexes) and <name>_full.md (+ full source appendix) to .claude/.artifacts/. Use when preparing a focused code or skill context for an LLM.
---
# /gitpack - LLM-Ready Code & Markdown Packer

Pack a codebase **or markdown tree** — or a scattered set of files (e.g. a skill whose command lives in `commands/` and agents in `agents/`) — into a compact context file using only Python's stdlib (AST parsing for Python, regex signatures for other languages, heading+frontmatter extraction for Markdown, direct file reads for the appendix). No external AI tools, no corruption, deterministic output.

## What This Does

Takes one or more input paths (files and/or directories) and produces two output files:
- **`<name>_sig.md`** — SIGNATURE TOC + DIRECTORY/FILE INDEX (compact, scannable)
- **`<name>_full.md`** — same + APPENDIX with full source code read directly from disk

Python signatures are extracted via `ast`; other languages via language-specific regex schemas; **markdown** via headings (`#`-`######`) + YAML frontmatter keys + list items. All exact, deterministic, no LLM involvement.

## Workflow

```
python "<skill-dir>/scripts/gitpack.py" <path>... [--skill <name>] [--name <pack-name>] [--exclude <patterns>] [--overview]
```

- `<path>...` — one or more files or directories. A directory is **recursed fully** (all nested subdirectories, depth-unlimited). A directly-listed file is included regardless of extension. Use multiple paths to pack a skill scattered across `commands/` + `agents/`, or pass one plugin/skill root and let recursion collect the whole tree.
- `--skill <name>` — **deterministic skill-name resolution.** Resolves `/improve`, `improve`, or `plugin:improve` to its installed directory (plugin cache first, marketplace source second) and packs it. Removes the model's cache-vs-source hand-resolution step — prefer this over guessing paths.
- `--name <pack-name>` — output basename (`<pack-name>_sig.md` / `<pack-name>_full.md`). Defaults to the common-parent directory name.
- `--overview` — emit an `## OVERVIEW (LLM-generated)` placeholder section at the top of both outputs. See "Code vs LLM split" below.

1. **DISCOVER** — Collect files from every input path (files included as-is; directories recursed with component-wise exclusion)
2. **EXTRACT** — Per file: `ast` (Python), language regex (JS/TS/HTML/CSS/SQL/YAML/JSON/PowerShell), or heading+frontmatter (Markdown)
3. **BUILD** — Write two markdown files to `P://.claude/.artifacts/`:
   - `_sig.md` — signatures + indexes only
   - `_full.md` — signatures + indexes + full source appendix

**Default exclusions** — always applied unless user overrides with `--exclude`:
```
__pycache__/,*.pyc,*.pyo,*.so,*.dll,*.exe
.venv/,venv/,env/,site-packages/
.pytest_cache/,.mypy_cache/,.ruff_cache/,.tox/
.git/,.hg/,.svn/
dist/,build/,out/,target/,egg-info/,*.egg-info/
.idea/,.vscode/,.DS_Store,Thumbs.db
.env,.env.*,*.log
```

## Output Files

| File | Contents |
|------|----------|
| `<name>_sig.md` | PACK INFO, HOW TO USE, SIGNATURE TOC, DIRECTORY INDEX, FILE INDEX |
| `<name>_full.md` | All of the above + APPENDIX: FULL IMPLEMENTATIONS (full source from disk) |

**Output location:** `P://.claude/.artifacts/` — always, never inside the target directory.
This prevents polluting source trees (especially skills/plugin cache) with temp files. |

## Reporting (model must do — do not skip)

After the run completes, **always report the full Windows paths** of the produced `_sig.md` and `_full.md` to the user — verbatim from the script's final `ARTIFACT PATHS` banner. Do not paraphrase, abbreviate, or omit. The user cannot open what they cannot point to. If you report anything about the run, the paths are the first thing to surface.

## Features

- **Multi-language** — `ast` for Python; regex signatures for JS/TS/HTML/CSS/SQL/YAML/JSON/PowerShell; **Markdown is first-class** (headings + frontmatter keys extracted as the signature TOC)
- **Multi-path** — pass any mix of files and directories; a scattered skill (command + agents in different dirs) packs into one pair via `--name`
- **Pure stdlib** — no external dependencies
- **No corruption** — source read directly from disk for appendix, no LLM processing
- **Deterministic** — same input always produces same output
- **Type annotations preserved** — return types and arg types shown when present

## Scope and Related Files

**Primary target:** the requested directory. But a complete LLM context often needs related files outside that path.

**Always include when present near the target:**
- Any companion `.py` files referenced by the target (e.g., a service that backs a skill)
- Any `CLAUDE.md`, `AGENTS.md`, or `.mcp.json` in the same tree
- If packing a skill, also pack its backing service, companion scripts, or related config files if they live in `P://tools/`, `P://.claude/`, or other well-known locations

**Rule:** If a file is named in code as a dependency or companion, it belongs in the pack. Err on the side of inclusion.

## Skill Name Resolution

When the target is a known skill name (e.g., `/git`, `handoff:id`), resolve it to a filesystem path before packing:

**Resolution order:**
1. `P://.claude/skills/<name>/` — local skill directory
2. `P://packages/.claude-marketplace/plugins/<plugin>/skills/<name>/` — marketplace source
3. `C:/Users/brsth/.claude/plugins/cache/local/<plugin>/<version>/skills/<name>/` — installed plugin cache

**Rule:** Skills installed via marketplace are loaded from the **cache on C:**, not from P: source. Always resolve through the cache path when the plugin is installed.

```python
# Skill name resolution helper
SKILL_CACHE_ROOT = Path("C:/Users/brsth/.claude/plugins/cache/local")
MARKETPLACE_ROOT = Path("P://packages/.claude-marketplace/plugins")

def resolve_skill_path(skill_ref: str) -> Path | None:
    """Resolve a skill reference like '/git' or 'handoff:id' to a filesystem path."""
    # Strip leading slash and split on ':' for namespaced skills
    name = skill_ref.lstrip("/").split(":")[0]
    # Check marketplace plugins for matching skill
    for plugin_dir in MARKETPLACE_ROOT.iterdir():
        if not plugin_dir.is_dir():
            continue
        skill_path = plugin_dir / "skills" / name
        if skill_path.exists() and skill_path.is_dir():
            # Check if installed in cache
            cache_root = SKILL_CACHE_ROOT
            for cache_plugin in cache_root.iterdir() if cache_root.exists() else []:
                for version_dir in cache_plugin.iterdir() if cache_plugin.is_dir() else []:
                    installed = version_dir / "skills" / name
                    if installed.exists():
                        return installed
            return skill_path  # fall back to marketplace source
    return None
```

## Examples

```bash
# Pack a directory — outputs go to P://.claude/.artifacts/
/gitpack P://packages/.claude-marketplace/plugins/cc-skills-analysis

# Pack with exclusions
/gitpack ./my-project --exclude __pycache__,*.pyc

# Pack a scattered skill (command in commands/, agents in agents/) into one named pair
/gitpack P://.claude/commands/red-team.md P://.claude/agents/red-team-planner.md P://.claude/agents/red-team-critic.md --name red-team

# Pack a markdown-only directory (headings + frontmatter become the signature TOC)
/gitpack P://.data/wiki/concepts --name wiki-concepts
```

**Output:** `P://.claude/.artifacts/<name>_sig.md` and `_full.md`

## Architecture

The packer is `scripts/gitpack.py` — a standalone stdlib script. Run it directly:

```bash
python "<skill-dir>/scripts/gitpack.py" <path>... [--name <pack-name>] [--exclude <patterns>]
```

Produces `P:/.claude/.artifacts/<name>_sig.md` and `<name>_full.md`.

**Fallback:** If the script is unreachable, the inline AST packer pattern in the examples section can be used, but it lacks fallback regex extraction and multi-language support that `gitpack.py` provides.

## See Also

- `/gitingest` — Clone + slice + upload to NotebookLM
- `/repomix` — XML/JSON output, skill generation
- `/aid` — Single-file or directory distillation with analysis prompts