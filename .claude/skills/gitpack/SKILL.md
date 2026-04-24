---
name: gitpack
version: "2.0.0"
status: "stable"
category: integration
enforcement: advisory
description: >
  Pack any local directory or GitHub clone into a compact LLM-ready context file. Use this skill whenever the user wants to
  distill, pack, compress, or prepare code for LLM consumption — phrases like "make this repo LLM-ready", "compress
  this codebase for context", "prepare code for AI analysis", "pack this directory", "create a context file from this
  repo". Also use when comparing /gitpack vs /repomix, or when the user mentions ai-distiller or aid compression.
  Works with local directories and (via ACQUIRE step) GitHub URLs. Produces 60-90% size reduction while preserving public
  API signatures and docstrings. GitHub repos require git clone --depth=1 before distillation.
triggers:
  - /gitpack
aliases:
  - /gitpack
  - /pack
workflow_steps:
  - PARSE
  - ACQUIRE
  - DISTILL
  - RESOLVE
  - OUTPUT
  - CLEANUP
---

# /gitpack - LLM-Ready Code Packer

Pack a local directory into a compact context file optimized for LLM consumption. GitHub repos must be cloned first (use `/gitingest` for end-to-end GitHub ingestion).

## What This Does

Takes source code (local directory or GitHub URL) and produces a distilled Markdown file with 60-90% size reduction. Public API signatures and docstrings preserved; implementation bodies, private members, and boilerplate stripped.

## Prerequisites

AI-Distiller (`aid`) must be available. Check via:
```bash
aid --version
```

If missing, the MCP tools (`mcp__aid__distill_directory`, `mcp__aid__distill_file`) serve as fallback — they don't require the CLI.

## Your Workflow

1. **PARSE** -- Determine source type and extract parameters:
   - GitHub URL (`https://github.com/owner/repo`): extract owner/repo, note branch if specified
   - Local path (`./my-project` or `P:/path/to/dir`): use directly, skip clone step
   - Flags: `--quick` (signatures only), `--exclude <patterns>` (custom exclusions)

2. **ACQUIRE** -- Get the code locally:
   - GitHub URL: `git clone --depth=1 <url>` into temp directory
   - Local path: use as-is
   - Private repo: user must have git credentials configured; surface auth errors clearly

3. **DISTILL** -- Run AI-Distiller. Prefer MCP tools when available, fallback to CLI:

   **Default mode** (full fidelity — everything included):
   ```
   mcp__aid__distill_directory({
     directory_path: "<target>",
     output_format: "md",
     include_private: true,
     include_protected: true,
     include_implementation: true,
     include_comments: true,
     exclude_patterns: ".mypy_cache/,.pytest_cache/,.ruff_cache/,__pycache__/,node_modules/,*.pyc,*.pyo,*.pyd,*.so,*.dll,*.dylib,*.whl,*.log,*.tmp,tests/,spec/,cache/,benchmarks/,logs/,.git/,.evidence/,.state/,venv/,env/,.venv/,.env/,site-packages/,.claude/worktrees/,_archive*,.archive/,build/,dist/,target/"
   })
   ```
   Or via CLI:
   ```bash
   aid . --format=md --file-path-type absolute --private=1 --protected=1 --implementation=1 --comments=1 --docstrings=1 -o .aid/<dirname>.md --exclude "<exclusions>"
   ```

   **Quick scan mode** (`--quick`) — API signatures only, no bodies, comments, or private members:
   ```
   mcp__aid__distill_directory({
     directory_path: "<target>",
     output_format: "md",
     include_private: false,
     include_protected: false,
     include_implementation: false,
     exclude_patterns: ".mypy_cache/,.pytest_cache/,.ruff_cache/,__pycache__/,node_modules/,*.pyc,*.pyo,*.pyd,*.so,*.dll,*.dylib,*.whl,*.log,*.tmp,tests/,spec/,cache/,benchmarks/,logs/,.git/,.evidence/,.state/,venv/,env/,.venv/,.env/,site-packages/,.claude/worktrees/,_archive*,.archive/,build/,dist/,target/"
   })
   ```
   Or via CLI:
   ```bash
   aid . --format=md --file-path-type absolute -o .aid/<dirname>.md --exclude "<exclusions>"
   ```

4. **RESOLVE** -- Detect cross-directory dependencies from distilled content:
   - Parse the distilled markdown for references to external paths:
     - `.claude/hooks/` → include hook files
     - `.claude/agents/` → include agent files
     - `.claude-plugin/` → include plugin manifest
     - `mcp_json.md` → include MCP server configs
     - `P:/.claude/docs/` references → include referenced docs
   - Also check SKILL.md frontmatter `hooks:` section for referenced hook IDs
   - For each detected external reference, read the file and append to the pack
   - Skip files that don't exist (warn but continue)
   - **Why this step exists**: An LLM reviewing the pack needs the full picture. If skill-craft references `craft_phase_gate` hook but only packs the SKILL.md, the hook implementation is missing.

5. **OUTPUT** -- Write the result and prepend TOC:
   - Save to `.aid/<dirname>.md` in the target directory (local) or current working directory (remote)
   - Run `gitpack_toc.py .aid/<dirname>.md <dirname> <mode>` to prepend a structured TOC with directory index, file index, and usage guidance
   - Print the full output path to the user
   - Report compression stats: original file count vs output lines
   - If output exceeds 500KB, warn the user and suggest targeting subdirectories or turning off `--full`

   The TOC script (`scripts/gitpack_toc.py`) extracts every `### path/to/file.py` header from aid output, groups files by top-level directory, and prepends:
   - **PACK INFO** — file count, mode, generation timestamp
   - **HOW TO USE THIS PACK** — token efficiency guidance for the receiving LLM
   - **DIRECTORY INDEX** — table of top-level directories with file counts
   - **FILE INDEX** — every file with a brief description derived from its name
   - Separator `---` before the raw aid output

6. **CLEANUP** -- For remote repos only:
   - Remove temp clone directory
   - Verify the temp directory is actually gone (not just attempt removal)
   - Keep the `.aid/` output file

## Compression Modes

| Mode | Bodies | Comments | Private | Protected | Docstrings | Use case |
|------|--------|----------|---------|-----------|------------|----------|
| **Default** | Included | Included | Included | Included | Included | Full analysis, debugging, complete picture |
| **`--quick`** | — | — | — | — | Included | Quick API scan, LLM context overview |

**CLI equivalents:**

| Mode | Command |
|------|---------|
| Default | `aid . --format=md --file-path-type absolute --private=1 --protected=1 --implementation=1 --comments=1 --docstrings=1 -o .aid/<dirname>.md --exclude "..."` |
| `--quick` | `aid . --format=md --file-path-type absolute -o .aid/<dirname>.md --exclude "..."` |

**MCP tool equivalents:**

| Mode | Key flags |
|------|-----------|
| Default | `include_implementation: true, include_comments: true, include_private: true, include_protected: true` |
| `--quick` | `include_implementation: false, include_private: false, include_protected: false` |

## Additional Flags

| Flag | Effect |
|------|--------|
| `--exclude <patterns>` | Override exclusion patterns (comma-separated) |
| `--output <path>` | Custom output path (default: `.aid/<dirname>.md`) |

## Examples

```bash
# Remote GitHub repo (default: full fidelity)
/gitpack https://github.com/owner/repo

# Quick scan (signatures only, no bodies/comments)
/gitpack ./my-project --quick

# Custom exclusions
/gitpack https://github.com/owner/repo --exclude "vendor/,dist/,build/"

# Local, already have the code
/gitpack P:/packages/my-package
```

## Integration

| Target | How |
|--------|-----|
| **NotebookLM** | Save output, then `nlm source add "<id>" --file context.md --title "repo context"` |
| **Claude Code** | Output serves as context for `/explain`, `/review`, `/refactor` |
| **Repomix** | Use `/gitpack` for max compression with semantic preservation; use `/repomix` for XML/JSON output or `--skill` generation |

## Comparison with /repomix

| Feature | /repomix | /gitpack |
|---------|----------|----------|
| Compression | 0% (full) or ~70% (`--compress`) | 60-90% (default) |
| Docstrings | Stripped by default | Included by default |
| Private members | Included | Excluded by default |
| Skill generation | Yes (`--skill`) | No |
| Output formats | XML, MD, JSON, plain | MD only |
| MCP integration | No | Yes (aid MCP tools) |

## Error Handling

| Scenario | Action |
|----------|--------|
| `aid` not installed and MCP unavailable | Surface install instructions: `pip install ai-distiller` or `npm install -g @anthropic/ai-distiller` |
| Private repo, auth failed | Report error; suggest `git config` or SSH key setup |
| Output exceeds 500KB | Warn user; suggest `--full` off or narrower `--exclude` |
| Empty directory | Report "no processable files found" |
| Large repo (>1000 files) | Warn about output size; suggest targeting subdirectories |

## See Also

- `/gitingest` -- Clone + slice + upload to NotebookLM
- `/repomix` -- More output formats, skill generation
- `/aid` -- Single-file or directory distillation with analysis prompts
