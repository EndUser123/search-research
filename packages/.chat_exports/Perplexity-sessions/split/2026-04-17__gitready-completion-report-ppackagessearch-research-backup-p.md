---
title: "'
  /gitready Completion Report — P:/packages/search-research

  Backup: P:/packages/search-research-backup-20260417-"
date: "2026-04-17"
mode: "COPILOT"
uuid: "6753cbdf-3844-4797-a522-c25de7479014"
entry_count: 1
---

## Human

"
  /gitready Completion Report — P:/packages/search-research

  Backup: P:/packages/search-research-backup-20260417-081640

  Phase Tracking (all phases executed)

  ┌─────────────────────────────────┬──────────────┬───────────────────────────────────────────────────────┐
  │              Phase              │    Status    │                         Notes                         │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 1: Diagnose               │ ✅ COMPLETED │ Tree + state cleared                                  │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 1.5: Detect Type          │ ✅ COMPLETED │ claude-plugin (.claude-plugin/ exists)                │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 1.6.5: Exception Registry │ ✅ COMPLETED │ Created .gitready/exceptions.json                     │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 1.7: Plugin Standards     │ ✅ COMPLETED │ Manual validation (no scripts in v5.26.0)             │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 1.8: Stale Cleanup        │ ✅ COMPLETED │ Structure aligned                                     │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 2: Build Structure        │ ✅ COMPLETED │ Created commands/, agents/, skills/, hooks/, scripts/ │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 3: Templates              │ ✅ COMPLETED │ Hooks JSON scaffolded                                 │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 4: Validate               │ ✅ COMPLETED │ pytest 12/12 pass, imports OK                         │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 4.5: Code Review          │ ✅ COMPLETED │                                                       │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 4.7: Media                │ ⏭ SKIPPED    │ NotebookLM auth not available                         │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 4.8: Course               │ ⏭ SKIPPED    │ NotebookLM auth not available                         │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 5: Polish                 │ ✅ COMPLETED │ Badges/docs via existing CHANGELOG                    │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 6: GitHub Publication     │ ⏭ SKIPPED    │ --publish flag not provided                           │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 7: Finalization           │ ⏭ SKIPPED    │ --finalize flag not provided                          │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 8: Cleanup                │ ✅ COMPLETED │                                                       │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 9: Git                    │ ✅ COMPLETED │ Repo already initialized with origin                  │
  ├─────────────────────────────────┼──────────────┼───────────────────────────────────────────────────────┤
  │ PHASE 10: Recruiter Readiness   │ ✅ COMPLETED │                                                       │
  └─────────────────────────────────┴──────────────┴───────────────────────────────────────────────────────┘

  What Changed

  - New: .gitready/exceptions.json — waives src/, pyproject.toml, .claude/ from plugin violations
  - New: hooks/hooks.json — PreToolUse scaffold for Edit/Write validation
  - New: scripts/__init__.py
  - New: commands/, agents/, skills/ (empty directories, ready for content)
  - Expanded: .claude-plugin/plugin.json — now includes keywords, repository, homepage
  - GitHub: Origin already configured → [https://github.com/EndUser123/search-research.git](https://github.com/EndUser123/search-research.git)

  Plugin Compliance — Current State

  The package is a hybrid brownfield: a pip-installable Python library (core/ + contrib/ via package-dir, search-research CLI entry
  point) with a Claude Code plugin layer on top. Three intentional deviations are documented and waived:

  1. .claude/ — project workspace hooks/state (git-tracked), not plugin content
  2. src/ — legacy daemon code predating plugin migration
  3. pyproject.toml — required for pip-install + CLI entry point

  Git Status (staged)

  M  .claude-plugin/plugin.json   (expanded manifest)
  A  .gitready/exceptions.json    (violation waivers)
  M  hooks/hooks.json             (PreToolUse scaffold)
  A  scripts/__init__.py
  M  CHANGELOG.md                 (phase tracking)

  Ready to commit. Want me to create the commit?

✻ Cogitated for 29m 30s

❯ why do we want it as a pip-installable Python library?

● Inferred: you want to know if the pip-installable library design is actually serving us well, or if it's creating more problems
  than it solves.

  What the pip-installable design gives us:
  1. search-research CLI works from any terminal — pip install . or pip install -e .
  2. core/ and contrib/ are mapped via package-dir so imports resolve cleanly
  3. The search_research package can be imported by external tools

  What it costs us:
  - pyproject.toml is flagged as a plugin violation (documented in exceptions)
  - The package-dir mapping (search_research.core = core) masks structural issues — if core/ files get deleted/staged, imports
  silently break (exactly the tombstone bug we hit)
  - Dual identity: is it a library you pip install or a Claude Code plugin? These pull in opposite directions
  - The src/ directory is legacy dead weight on top of this

  The honest question: Is there a reason search-research the CLI needs to be pip-installable, or was that just the default scaffold
  choice? If the CLI is the valuable thing, we could keep it as a standalone script or thin wrapper. If it's genuinely a library
  consumed by other tools, the pyproject.toml makes sense.

  The tombstone bug — from .tracing import while tracing.py was staged deleted — is a direct consequence of the package-dir
  indirection hiding the actual file structure from Python's import resolution.

  What would change your mind on this: is the pip-installable constraint real, or is it historical accident?

✻ Crunched for 1m 27s

※ recap: Gitready completed on search-research — plugin structure scaffolded, backup at `search-research-backup-20260417-081640`,
  all phases tracked in CHANGELOG. Staged and ready to commit if you approve.

❯ why you asking me?  what are the pro / con for keeping it hybrid vs claude plugin only?

● Tradeoff: Hybrid (pip-installable + plugin) vs Plugin-only

  Decision criterion: What serves your actual workflow better — the ability to pip install and run search-research as a CLI from any
   terminal, or keeping the Claude Code integration clean?

  ┌─────┬────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────┐
  │     │                       Hybrid                       │                        Plugin-only                        │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Pro │ CLI works anywhere (pip install .)                 │ Simpler structure, no plugin violations                   │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Pro │ External tools can import search_research          │ package-dir indirection gone — tombstone risk lower       │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Pro │ GitHub repo looks like a real OSS project          │ Fewer exceptions to maintain in .gitready/exceptions.json │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Con │ pyproject.toml violates plugin spec (needs waiver) │ No search-research CLI from terminals                     │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Con │ package-dir hides file structure from Python       │ —                                                         │
  ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Con │ Dual identity is confusing                         │ —                                                         │
  └─────┴────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────┘

  The real cost of hybrid: The package-dir = {search_research = "core"} mapping means Python resolves search_research.X to core/X.py
   without you seeing that core/tracing.py was deleted. That's how the tombstone bug silently broke the CLI. A plugin-only structure
   would use core/ directly as core, so git deleted core/tracing.py would immediately cause import failures before staging.

  Failure mode if wrong: If you abandon the pip-installable path, any scripts/automation depending on search-research CLI will
  break.

  Discriminating check: Do you have anything that calls pip install search-research or depends on the CLI existing as a system
  command? If not, the plugin-only path costs nothing and removes the indirection that caused the tombstone bug.

  Want me to check if anything in this repo or your automation depends on the pip-installable aspect?

✻ Baked for 1m 23s

❯ Please check if we depend on the pip installable aspect. I have a feeling we do not.

  Searched for 2 patterns (ctrl+o to expand)

● Bash(cd "P:/packages/search-research" && grep -r "search-research" --include="*.sh" --include="*.bat" --include="*.ps1"
      --include="*.yml" --include="*.yaml" 2>/dev/n…)
  ⎿  .venv/Scripts/activate.bat:@for %%i in ("P:\\packages\\search-research\\.venv") do @set "VIRTUAL_ENV=%%~fi"
     .venv/Scripts/activate.bat:@set "VIRTUAL_ENV_PROMPT=search-research"
     .venv/Scripts/activate.ps1:if ("search-research" -ne "") {
     .venv/Scripts/activate.ps1:    $env:VIRTUAL_ENV_PROMPT = "search-research"

  Searched for 2 patterns (ctrl+o to expand)

● Now let me check the external references (outside search-research itself):

● Searching for 10 patterns, reading 2 files… (ctrl+o to expand)
  ⎿  P:/packages/test_backends_quick.py

✶ Adding EmbeddingCache L2 to core/cache.py… (1m 48s · ↓ 891 tokens · thought for 5s)
  ⎿  Next: Plan 3 TASK-002b: Confirm plan.md path propagation to worktree B

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── cleanup ──
❯ 
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ accept edits on (shift+tab to cycle)
 ▐▛███▜▌   Claude Code v2.1.110
▝▜█████▛▘  MiniMax-M2.7 with medium effort · API Usage Billing
  ▘▘ ▝▝    P:\\

  Searched for 9 patterns, read 2 files (ctrl+o to expand)

● Verdict: We don't need it as pip-installable for ourselves. But claude-chain-miner depends on it.

  Evidence:

  ┌──────────────────────────────────────────┬────────────────────────────────────────────────────────┬───────────────────┐
  │                Reference                 │                        Approach                        │ Uses pip-install? │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ yt-is/csf/cks_store.py                   │ sys.path.insert(0, "P:/packages/search-research/core") │ No                │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ yt-is/extract_channels.py                │ Same sys.path approach                                 │ No                │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ claude-chain-miner/scripts/exporter.py   │ sys.executable '-m', 'search_research.cli', query      │ Yes               │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ test_backends_quick.py                   │ sys.path.insert(0, ".../search-research")              │ No                │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ test_end_to_end.py, test_all_backends.py │ No references                                          │ N/A               │
  ├──────────────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────┤
  │ CLI_USAGE.md                             │ Documents pip install -e                               │ Yes, but docs     │
  └──────────────────────────────────────────┴────────────────────────────────────────────────────────┴───────────────────┘

  The only real external dependency is claude-chain-miner/scripts/exporter.py — it calls python -m search_research.cli. If we remove
   pyproject.toml, that breaks.

  Everything else uses sys.path pointing at the repo directly — doesn't care about pip install.

  This means: You could drop the pip-installable aspect, migrate claude-chain-miner/scripts/exporter.py to use sys.path-based
  invocation, and have a cleaner plugin-only structure. That's a ~30 second change in exporter.py.

  Want me to do that migration and convert to plugin-only? The claude-chain-miner would need to be in the same session or you'll
  break the cross-package link.

✻ Sautéed for 3m 57s

❯ And plugin only means no tombstones?

● No — plugin-only doesn't fix tombstones. Here's why:

  The tombstone failure chain:
  1. router_async.py had from .tracing import QueryTracer — syntactically valid
  2. core/tracing.py was staged-deletion (on disk: deleted; in git index: staged delete)
  3. Python tried to import tracing.py → OS couldn't find it → ModuleNotFoundError
  4. The PreToolUse hooks only see file edits, not import resolution
  5. import_deletion_guard catches it post-git add, not pre-edit

  The package-dir indirection wasn't the cause — it was just the mapping. Even with direct filesystem imports (core/ as core/), if
  core/tracing.py is deleted and you try from core.tracing import, Python still can't find it.

  What actually prevents tombstones:
  - Don't stage-delete a module while files still import from it
  - A pre-check that validates "every from X import in modified files resolves to a file on disk or in git staging" — but this is
  complex because it requires tracing all imports in a file, not just checking if the file itself is tracked
  - import_deletion_guard (which already exists) catches the post-git add case

  The root fix is discipline/workflow, not structure. The package-dir is incidental to the tombstone cause."

What should we do? Use a plugin only? A package only? Or a hybrid? It's going on GitHub for other people to see and use.

## Assistant

## Recommendation
Keep the **hybrid** structure: Claude Code plugin + pip-installable Python library. It aligns with your external dependency (claude-chain-miner), eliminates tombstone risks via workflow discipline, and positions the GitHub repo as usable OSS—others can `pip install git+https://github.com/EndUser123/search-research.git` or install as a plugin.[1][2][3]
## Tradeoffs
| Aspect | Hybrid Pros/Cons | Plugin-Only | Package-Only |
|--------|------------------|-------------|--------------|
| **Your Workflow** | CLI via pip works; chain-miner unbroken (migrate if drop). Minor plugin violations waived. | No CLI/pip; fix chain-miner (~30s sys.path change). Cleanest plugin compliance.[4][1] | No plugin (lose commands/agents/hooks). CLI only. |
| **Tombstones** | package-dir hides deletions (root cause: staging deletes pre-import check). Guard hook mitigates post-add.[5] | Same risk (direct imports fail on missing files). | Same risk. |
| **GitHub Appeal** | Looks professional/dual-use (pip + plugin). Common in examples.[3][6] | Pure plugin; niche audience. | Standard PyPI; broad but no Claude integration. |
| **Maintenance** | .gitready exceptions for pyproject.toml/src/.claude/. Dual manifests. | Zero exceptions; drop pyproject.toml, legacy src/. | Drop plugin dirs; simplify. |

**Key Fact**: Tombstones stem from git staging deletes before import resolution—not package-dir (Python fails regardless). Fix: Enhance PreToolUse hook for import validation (scan modified files' imports vs disk/git index).[5]
## Next Steps
1. Commit staged changes (safe: backup exists).
2. Test chain-miner post-commit.
3. Add hook: Parse imports in edited files, verify targets exist (disk or staged).
4. Publish to GitHub (--publish flag next run).
5. Document dual-use in README: "pip install -e . for CLI; claude plugins install . for integration."[7]

Confidence: High—hybrid matches real repos (e.g., promptlayer-claude-plugins has pyproject.toml). No data conflicts; plugin docs silent on packages (allows hybrids).[1][4][3]
