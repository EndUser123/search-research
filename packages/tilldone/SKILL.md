---
name: tilldone
version: 1.0.0
status: "stable"
description: Run a command on each package in a target directory until phases stop changing (till-done) or for a fixed count. Works with any slash command or CLI tool. Use when you want to batch-process multiple packages with iterative convergence checking.
category: batch
enforcement: advisory
triggers:
  - /tilldone
aliases:
  - /tilldone
workflow_steps:
  - parse_args
  - discover_targets
  - run_convergence_loop
  - report_results
suggest:
  - /gitready
  - /refactor
---

# /tilldone — Batch Convergence Runner

## Purpose

Run a command on each package in a target directory with two modes:
- **Till-done**: Run until phase states stop changing (convergence check, gitready-specific)
- **Count**: Run exactly N passes per package

Stops on first stable package, reports, then continues to the next.

## Usage

```bash
/tilldone P:/packages --command "/gitready"                    # till-done, gitready
/tilldone P:/packages --command "/gitready" --count 3          # 3 passes per package
/tilldone P:/packages --command "/gitready" --dry-run          # preview targets
/tilldone P:/packages --command "/gitready" --publish --finalize  # pass flags to command
```

| Argument | Description |
|----------|-------------|
| `target` | Directory containing packages to process |
| `--command` / `-c` | Command to run per package (quote the full slash command) |
| `--count N` | Override: run exactly N passes instead of till-done |
| `--dry-run` | Preview targets and iteration plan, no execution |
| `-- <flags>` | Additional flags passed through to the command |

## Modes

### Till-Done (default)
For each package:
1. Read `references/changelog.md` phase states
2. Run command
3. Re-read phase states — if unchanged, package is **stable**, move to next
4. If changed, repeat until stable or max iterations (20) reached

### Count Mode (`--count N`)
For each package: run command N times, no convergence check.

## Target Discovery

Finds all directories in `target` that have a `.git/` subdirectory.
Skips hidden directories (starting with `.`).

## Command Invocation

The `--command` value is passed to Claude Code CLI:
```bash
claude "<command> <target>"
```

Example: `/tilldone P:/packages --command "/gitready"` runs:
```bash
claude "/gitready P:/packages/pkg1 --publish --finalize"
```

Flags after `--` are passed verbatim:
```bash
/tilldone P:/packages --command "/gitready" -- --publish --finalize
# becomes: claude "/gitready P:/packages/pkg1 --publish --finalize"
```

## Exit Codes

- `0` — all packages stable
- `1` — one or more packages did not converge within max iterations

## Examples

```bash
# Polish all packages with gitready until phases settle
/tilldone P:/packages --command "/gitready" --publish --finalize

# Preview what would run
/tilldone P:/packages --command "/gitready" --dry-run

# Run a fixed 3-pass sweep
/tilldone P:/packages --command "/gitready" --count 3

# Run refactor on all packages in a directory
/tilldone P:/worktrees --command "/refactor" --count 1
```