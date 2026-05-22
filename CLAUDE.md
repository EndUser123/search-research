# search-research

Unified search and research package for Claude Code — local code/knowledge search, web research, and repository ingestion.

## Skills (11)

| Skill | Purpose | Home |
|-------|---------|------|
| /explore | Universal search (local + web) with three-layer filtering | `all/` |
| /search | Fast local-only search (CHS, CKS, Code, Docs) | `search/` |
| /research | Comprehensive web research with multiple providers | `research/` |
| /chs | Chat History Search | `chs/` |
| /discover | Intelligent codebase pattern discovery (ML-enhanced) | `discover/` |
| /aid | AI-Distiller wrapper for deep code analysis | `aid/` |
| /crawl | Ingest websites into QMD for semantic search | `crawl/` |
| /gitingest | Ingest GitHub repos into NotebookLM | `gitingest/` |
| /repomix | Pack repo contents into AI-friendly formats (XML/MD) | `repomix/` |
| /gitpack | LLM-ready context packer (pure Python AST) | `gitpack/` |
| /context7 | Fetch fresh, version-specific library docs | `context7/` |

## Artifacts Convention

All runtime artifacts write to:

```
.claude/.artifacts/{terminal_id}/{skill_name}/
```

Skills MUST NOT write state to their own directory or to the package root.

## Installation

Skills surfaced via junctions in `P:/\.claude/skills/`.

Command frontends live in `$CLAUDE_PLUGIN_ROOT/commands/`.
