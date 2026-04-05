# Skills Dependency Matrix

**Generated:** 2026-03-09
**Total Skills Analyzed:** 204
**Task:** #1555 - Tools and API dependencies

## Summary

| Category | Count | Files |
|----------|-------|-------|
| **Built-in Tools** | 1548 occurrences | 292 files |
| **GitHub API** | 81 occurrences | 26 files |
| **Subprocess** | 403 occurrences | 90 files |
| **SQLite/Database** | 261 occurrences | 93 files |
| **Context7 MCP** | 20 occurrences | 5 files |
| **Tavily MCP** | 8 occurrences | 4 files |
| **NotebookLM MCP** | 0 occurrences | 0 files* |
| **Perplexity MCP** | 0 occurrences | 0 files* |
| **AI-Distiller** | 1 occurrence | 1 skill |
| **HTTP Clients** | 5 occurrences | 3 files |

*Note: MCP servers are invoked via Skill tool calls, not direct imports

---

## 1. Built-in Tool Dependencies

### Core Tools (High Usage)
| Tool | Usage Count | Skills |
|------|-------------|--------|
| `Agent()` | 22 | orchestrator, skill-complete, code, main, analytics, llm-api |
| `Bash` | 400+ | git, llm-cli, package, p, r, cleanup, media-pipeline |
| `Read` | 800+ | All skills (universal file reading) |
| `Edit` | 300+ | code, refactor, package, tdd, p |
| `Write` | 200+ | docs, package, artifact, session |
| `Glob` | 150+ | discovery, cleanup, refactor, analyze |
| `Grep` | 100+ | search, audit, validate, analyze |
| `Skill` | 22 | orchestrator, agent-orchestrator, skill-complete |

### Discovery Tools
| Tool | Usage Count | Skills |
|------|-------------|--------|
| `Glob` | 150+ | discover, cleanup, refactor |
| `Grep` | 100+ | bug-hunt, comply, analyze |

---

## 2. MCP Server Dependencies

### Context7 (Documentation)
| Skill | Integration |
|-------|-------------|
| `/code` | `code/utils/context7_client.py` - 20 references |
| `/context7` | Direct MCP integration via `mcp__plugin_context7` |

**Usage Pattern:**
- Resolve library ID → Query docs → Extract code examples
- Rate limiting via `context7_rate_limiter.py`

### Tavily (Research/Web)
| Skill | Integration |
|-------|-------------|
| `/crawl` | `mcp__tavily-mcp__tavily_crawl` - 4 references |
| `/research` | `mcp__tavily-mcp__tavily_search` (via MCP) |

### NotebookLM (Research)
| Skill | Integration |
|-------|-------------|
| `/notebooklm` | CLI wrapper `nlm` (via MCP server) |

**Note:** 0 direct MCP imports in codebase. Uses MCP server protocol with `nlm` CLI.

### Perplexity (Research)
| Skill | Integration |
|-------|-------------|
| `/research` | Via MCP server (no direct imports) |

---

## 3. External API Dependencies

### GitHub API
| Skill | Usage |
|-------|-------|
| `/git` | Sync operations, semantic commits |
| `/package` | Badge generation, repo metadata |
| `/github-public-posting` | Issue/PR creation |
| Total: 26 files | 81 occurrences |

**Pattern:** `github.com/`, `api.github.com`, `gh api`

### LLM APIs
| Skill | Provider |
|-------|----------|
| `/llm-api` | Multi-provider via litellm |
| `/s` | Provider selection (Chutes models) |
| `/ask` | Direct API calls |
| Total: 1548 occurrences | 292 files (anthropic/openai references) |

---

## 4. File System Dependencies

### State Files (Universal)
| Path | Usage |
|------|-------|
| `.claude/state/` | 50+ skills |
| `.claude/hooks/` | 30+ skills |
| `.claude/cognitive/` | 15+ skills |
| `.claude/memory/` | 10+ skills |

### Project-Specific Paths
| Path | Skills |
|------|--------|
| `__csf/` | csf-nip-dev, csf-nip-integration, package |
| `.aid/` | aid (AI-Distiller output) |
| `P:/` | Hardcoded path references (30 files) |

---

## 5. Database Dependencies

### SQLite
| Skill | Tables |
|-------|--------|
| `/cks` | findings table (migrations) |
| `/av2` | evidence tracking |
| `/cleanup` | State management |

**Total:** 93 files with database references

---

## 6. Subprocess Dependencies (90 files)

### Heavy Users
| Skill | Commands |
|-------|----------|
| `/git` | git operations, sync |
| `/llm-cli` | Model execution, workspace checks |
| `/media-pipeline` | GPU detection, asset verification |
| `/p` | linting, security scans, formatting |
| `/cleanup` | File operations, regex validation |

---

## 7. HTTP Client Dependencies

| Library | Usage |
|---------|-------|
| `requests` | GitHub API, web scraping |
| `httpx` | Async HTTP operations (3 files) |
| `urllib` | Legacy URL handling |

---

## 8. Environment Variable Dependencies

| Variable | Skills |
|----------|--------|
| `CLAUDE_SESSION_ID` | artifact, session |
| `CLAUDE_TERMINAL_ID` | artifact-core, session |
| `OPENAI_API_KEY` | llm-api, ask |
| `ANTHROPIC_API_KEY` | llm-api, s |

---

## 9. Key Findings

### High-Dependency Skills (Most External Touchpoints)
1. **`/code`** - Context7, state files, hooks, subprocess
2. **`/p`** - Subprocess (lint/security/scan), state, hooks
3. **`/package`** - GitHub API, Context7, state files
4. **`/llm-api`** - LLM providers, model catalog API
5. **`/notebooklm`** - NotebookLM MCP server

### Zero-External Skills
- Pure workflow/documentation skills
- No API calls, subprocess, or external tools
- Example: `/cognitive-frameworks`, `/constraints`

### MCP Integration Pattern
- **Direct import:** Context7 (via mcp__plugin_context7)
- **CLI wrapper:** NotebookLM (nlm CLI → MCP protocol)
- **Skill tool:** Perplexity, Tavily (via Skill tool invocations)

---

## 10. Dependency Clusters

### Code Analysis Cluster
```
/code, /aid, /llm-api, /bug-hunt
├── Context7 MCP
├── Subprocess (linting tools)
└── State files
```

### Research Cluster
```
/research, /notebooklm, /crawl
├── Tavily MCP
├── NotebookLM MCP
└── HTTP clients
```

### Package Cluster
```
/package, /git, /github-public-posting
├── GitHub API
├── Context7 MCP
└── State files
```

### Testing Cluster
```
/t, /p, /tdd, /q
├── Subprocess (pytest, nox)
├── State files
└── SQLite databases
```

---

## 11. Risk Assessment

### High External Dependency Risk
| Skill | Risk | Reason |
|-------|------|--------|
| `/llm-api` | API Keys | Multiple provider credentials |
| `/notebooklm` | Auth Session | 20-min session timeout |
| `/package` | GitHub API | Rate limits, token expiry |

### Medium Risk
| Skill | Risk | Reason |
|-------|------|--------|
| `/code` | Context7 | API availability |
| `/p` | Subprocess | External tool availability |

### Low Risk
- Pure workflow skills
- Documentation skills
- Validation skills (use built-in tools only)

---

**END OF DEPENDENCY MATRIX**
