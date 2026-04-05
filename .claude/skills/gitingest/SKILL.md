---
name: gitingest
version: "1.0.1"
status: "stable"
category: integration
enforcement: advisory
description: Ingest GitHub repos into NotebookLM — clone, slice, and upload in one pipeline.
---

# gitingest

**Goal:** Ingest GitHub repos into NotebookLM — clone, slice, and upload in one pipeline.

**Prerequisites:** `nlm` CLI (v0.3.3+) from https://github.com/jacob-bd/notebooklm-mcp-cli

---

## Usage

```bash
# 1. Copy the config template to .staging
cp references/repos-template.yaml P:/.staging/my-repos.yaml

# 2. Edit the config — add your repos and notebook ID
vim P:/.staging/my-repos.yaml

# 3. Dry run (verify what would happen)
python scripts/gitingest_runner.py --config P:/.staging/my-repos.yaml --dry-run

# 4. Run for real
python scripts/gitingest_runner.py --config P:/.staging/my-repos.yaml
```

---

## Config file (`references/repos-template.yaml`)

**Config files are templates in `references/` — actual configs live in `P:/.staging/` (not `/tmp/`), never in the skill itself.**

> **Note:** On this system, `/tmp` is blocked by `PreToolUse_directory_policy.py`. Use `P:/.staging/` instead.

```yaml
notebooklm_id: "your-notebook-id-from-url"
repos:
  - url: "https://github.com/owner/repo"
    branch: "main"   # optional, default: main
    path: ""         # optional: sparse checkout path
    skip: false      # optional: skip this repo
```

---

## Pipeline (6 steps, executed by `scripts/gitingest_runner.py`)

1. **Clone** — `git clone --depth=1 --filter=blob:none`, optionally sparse
2. **File lists** — `git ls-files` (repo), `.claude/` configs, `docs/` + top-level README
3. **Slice** — repo-index, agent-configs, docs; ≤150 lines/slice; entry points inlined
4. **Upload** — `nlm source add <notebook_id> --file <slice> --wait`
5. **Cleanup** — removes clone dir (always, even on error)
6. **Status** — saves `status.json` to staging dir after each repo

---

## Output

```
=== [1/17] owner/repo ===
--- clone ---
  $ git clone ...
--- file lists ---
  → 42 repo files, 3 agent configs, 2 docs
--- slices ---
  → slice: repo-index-part-1.md (8.2 KB)
  → slice: agent-configs-part-1.md (1.1 KB)
--- upload ---
  ✓ repo-index-part-1.md uploaded
  ✓ agent-configs-part-1.md uploaded
✓ owner/repo done

=== Summary ===
  ✓ 15 succeeded
  ✗ 2 failed:
    - owner/bad-repo: clone failed
```

---

## References

- `references/repos-template.yaml` — config template (copy to `/tmp/` before use)
- `references/github-urls.md` — URL parsing + clone commands
- `references/notebooklm-upload.md` — nlm CLI commands
- `scripts/gitingest_runner.py` — the pipeline engine
