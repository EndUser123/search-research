# search-research

Unified search and research package for Claude Code — local code/knowledge search, web research, and repository ingestion.

## Skills (13)

| Skill | Purpose | Home |
|-------|---------|------|
| `/find` | Fast local-only search (CHS, CKS, Code, Docs) | `find/` |
| `/web` | Comprehensive web research with multiple providers | `web/` |
| `/research` | Canonical research (local + web) with Phase 1 evidence routing and artifacts | `research/` |
| `/all` | Compatibility wrapper for `/research` | `all/` |
| /chs | Chat History Search | `chs/` |
| /export-session | Export session chain to markdown (thin wrapper over /chs export) | `export-session/` |
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

Plugins live directly in `P:/packages/.claude-marketplace/plugins/<name>/`.

Command frontends live in `$CLAUDE_PLUGIN_ROOT/commands/`.
