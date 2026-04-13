---
status: draft
stateful: true
source: /arch nested resolution (STATE-001 + CONTRACT-MATRIX-002 blockers)
unresolved_blockers: 0
---

# Plan: QMD Wiki Skill + search-research Backend

## Goal

Deliver a persistent knowledge system: LLM maintains an Obsidian wiki (ingest/synthesize/lint), searchable via QMD, exposed as `search-research` backend `QMD_WIKI`.

---

## Current State with Evidence

- `P:/.claude/skills/gitingest/karpathy-llm-wiki.md` lines 1-76 — LLM Wiki 3-layer pattern (Raw Sources → Wiki → Schema)
- `P:/.claude/skills/gitingest/claude-code-qmd-repos.yaml` lines 12-14 — qmd + obsidian-claude-code-mcp listed
- `P:/packages/search-research/core/backends/local/base_local_backend.py` line 17 — `BaseLocalBackend` extension pattern
- `P:/packages/search-research/ARCHITECTURE.md` line 161 — 8-local-backend table with integration pattern

---

## State Model

**Identity model:** `vault_page_id` = vault-relative path (e.g. `wiki/entities/session-chain.md`). Globally unique within vault namespace. Multiple vaults possible via `OBSIDIAN_VAULT_PATH` namespacing. The `terminal_id` is used for settings lookup; `task_id` used for task tracking in log entries.

**Ordering contract:** mtime-based (file modification time). All operations (ingest, edit, lint, index) sequenced by wall-clock mtime. No cross-vault total ordering.

**Dedupe contract:** Page identity = vault-relative path. LLM is sole writer. Log entries deduplicated by `[YYYY-MM-DD] ingest | {title}` prefix (append-only).

**Freshness/invalidation contract:** Filesystem mtime is authoritative for wiki page freshness. QMD index freshness authority = QMD index timestamp. If QMD index mtime < vault mtime → index is stale, rebuild triggered. Invalidation trigger: any .md file write/delete/rename.

**Event source of truth:** Wiki writes: filesystem (LLM writes .md directly). Search index: QMD index (rebuilt on `qmd index --rebuild`). `log.md` is append-only record (not a separate event log).

**Isolation boundary:** Vault path = workspace-shared (git-tracked, multi-terminal access). Per-page locking not required — git handles merge conflicts.

**Triggerability:** On every `search_async` call, if vault mtime > index mtime, trigger async index rebuild (non-blocking, background). Fallback trigger: `FileNotFoundError` or `SubprocessError` from qmd CLI call.

---

## Design Decisions and Invariants

| ID | Decision | Rationale |
|----|----------|-----------|
| DEC-001 | Skill owns lifecycle; backend is thin read-only adapter | Separation of concerns — skill handles LLM writes, backend handles search reads only |
| DEC-002 | Graceful degradation to glob+grep when qmd unavailable | `search-research` must not hard-fail on optional tooling |
| DEC-003 | Workspace-shared vault path via settings mechanism | Multi-terminal access requires shared path, not terminal-private state |
| DEC-004 | Filesystem mtime authoritative for wiki; QMD index timestamp for search | Vault is source of truth; QMD index is derived and invalidated by vault changes |
| DEC-005 | Async non-blocking index rebuild when stale detected | Search should not block on index rebuild; stale index is better than no search |

---

## Contract Authority Reference

**Contract-sensitive: YES**

Source: `/arch` nested resolution this session, `contract_authority_packet.packet_version=2`

---

## Contract Boundary Matrix

| Boundary | Contract authority packet | Producer | Consumer | Input Schema | Output Schema | Required Fields | Freshness Authority | Invalidation Trigger | Failure Behavior | Packet Alignment | Test Binding |
|----------|--------------------------|----------|----------|--------------|--------------|----------------|--------------------|--------------------|-----------------|-----------------|-------------|
| skill-to-vault | source: /arch CAP v2 this session | /wiki skill (LLM) | Obsidian vault (filesystem) | raw source (file path, URL, or text blob) | .md file with YAML frontmatter + body | path, content, frontmatter.tags, frontmatter.created | filesystem (vault mtime) | new ingest, user edit, or explicit rebuild | skill surfaces error; does not corrupt existing pages | ingest-only log; no delete without user consent | file existence + frontmatter parse validation |
| vault-to-qmd | source: /arch CAP v2 this session | Obsidian vault (filesystem) | QMD search engine | directory of .md files under vault/wiki/ | QMD binary vector + BM25 index file | wiki/*.md files | QMD index timestamp | any .md file create/edit/delete within vault | qmd rebuilds index automatically on next search | vault is immutable source; qmd index is derived | `qmd index --rebuild` produces valid index; timestamp updated |
| qmd-to-backend | source: /arch CAP v2 this session | QMD CLI | QMDWikiBackend | query string | `list[SearchResult]` | query, results | QMD index | qmd index rebuild or vault file change | fallback to glob+grep (FileNotFoundError or asyncio.subprocess.SubprocessError) | qmd JSON is input; backend output is list[SearchResult] | mock qmd stdout with valid JSON; mock FileNotFoundError triggers fallback |
| backend-to-router | source: /arch CAP v2 this session | QMDWikiBackend.search_async() | UnifiedRouter | query string | `list[SearchResult]` (path, snippet, score fields) | query, results, file_path | QMDWikiBackend result | search timeout (0.5s) or uncaught exception | returns empty list, logs error to stderr | backend result is input to router | `pytest test_qmd_wiki_backend.py::test_search_returns_results` |

**Graceful Degradation Notes:**
- Fallback glob+grep path truncates `content` to 200 characters per result (`content[:200]`). Consumers must not assume full content length in fallback mode.
- Cross-terminal rebuild coordination: `_rebuild_lock` is per-process only. Concurrent rebuilds across terminals are serialized by separate locks; vault mtime is re-checked after lock acquisition to minimize stale-index blindness.

---

## Implementation Changes

### TASK-001: Create /qmd-wiki skill structure

**Scope:**
- `P:/.claude/skills/qmd-wiki/SKILL.md`
- `P:/.claude/skills/qmd-wiki/CLAUDE.md`

**Operations:**

| Operation | Description |
|-----------|-------------|
| Ingest | Accept source (file/URL/text) → LLM reads → writes/updates wiki pages → updates `index.md` → appends to `log.md` |
| Query | Accept question → `qmd search` → LLM synthesizes → optionally file answer as wiki page |
| Lint | Health-check: contradictions, orphan pages, missing cross-refs, stale claims |
| Index | Rebuild `index.md` catalog from current wiki state |

**Configuration (settings.json):**
```json
{
  "OBSIDIAN_VAULT_PATH": "~/.obsidian/vaults/personal-wiki",
  "QMD_WIKI_SOURCES": "sources/",
  "QMD_WIKI_SCOPE": "wiki/"
}
```

**Schema conventions (vault/CLAUDE.md):**
- Every wiki page: YAML frontmatter with `tags`, `created`, `sources`, `summary`
- `wiki/entities/` — entity pages
- `wiki/concepts/` — concept pages
- `sources/` — immutable raw sources (never modified by LLM)
- `wiki/comparisons/` — comparison pages
- Log entries: `## [YYYY-MM-DD] ingest | Title`
- Graceful degradation: glob+grep fallback when `qmd` unavailable

**Acceptance:**
- Skill has ingest, query, lint, index operations documented in SKILL.md
- Schema conventions in CLAUDE.md
- Graceful degradation documented in SKILL.md

---

### TASK-002: Implement QMDWikiBackend

**Scope:**
- `P:/packages/search-research/core/backends/local/qmd_wiki_backend.py` (new file)
- Add `__init__` as part of the new QMDWikiBackend class following the BaseLocalBackend pattern (reuse existing pattern from `base_local_backend.py` line 17)
- `_should_exclude()` is inherited from `BaseLocalBackend` — no new implementation needed

**Implementation:**

```python
from typing import TYPE_CHECKING
import os
if TYPE_CHECKING:
    from .models import SearchResult

class QMDWikiBackend(BaseLocalBackend):
    BACKEND_NAME = "QMD_WIKI"
    TIMEOUT = 0.5  # seconds

    def __init__(
        self,
        vault_path: str | None = None,
        qmd_scope: str = "wiki/",
    ):
        self.vault_path = Path(os.path.expanduser(vault_path or config.OBSIDIAN_VAULT_PATH))
        self.qmd_scope = qmd_scope
        self._index_mtime: float | None = None
        self._rebuild_lock = asyncio.Lock()

    async def search_async(self, query: str, **kwargs) -> list["SearchResult"]:
        # Primary: qmd search --scope wiki/ "query" → parse JSON
        # Fallback: glob *.md in wiki/ + naive grep if qmd unavailable
        # Staleness check: if vault mtime > index mtime, rebuild index async
        vault_mtime = self._get_vault_mtime()
        if vault_mtime and (self._index_mtime is None or vault_mtime > self._index_mtime):
            asyncio.create_task(self._async_rebuild_index())
        try:
            result = await asyncio.create_subprocess_exec(
                "qmd", "search", "--scope", self.qmd_scope, query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=self.TIMEOUT)
            return self._parse_qmd_json(stdout)
        except (FileNotFoundError, asyncio.subprocess.SubprocessError, asyncio.TimeoutError):
            return self._fallback_grep(query)

    def _parse_qmd_json(self, stdout: bytes) -> list["SearchResult"]:
        """Parse qmd JSON output into SearchResult list.

        qmd output schema: {query: str, results: [{path: str, snippet: str, score: float}]}
        SearchResult required fields: title, content, source, score
        """
        import json
        data = json.loads(stdout.decode())
        results = []
        for r in data.get("results", []):
            path = r.get("path", "")
            snippet = r.get("snippet", "")
            score = r.get("score", 0.0)
            # Derive title from path basename (strip wiki/ prefix and .md extension)
            title = path.split("/")[-1].rsplit(".md", 1)[0] or path
            results.append(SearchResult(
                title=title,
                content=snippet,
                source=self.BACKEND_NAME,
                score=score,
                file_path=path,
            ))
        return results

    def _fallback_grep(self, query: str) -> list["SearchResult"]:
        """Fallback glob+grep when qmd unavailable. Constructs proper SearchResult objects."""
        results = []
        wiki_path = self.vault_path / self.qmd_scope
        if not wiki_path.exists():
            return results
        for md_file in wiki_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    title = md_file.name.rsplit(".md", 1)[0]
                    results.append(SearchResult(
                        title=title,
                        content=content[:200],
                        source=self.BACKEND_NAME,
                        score=0.5,
                        file_path=str(md_file),
                    ))
            except Exception:
                continue
        return results

    def _get_vault_mtime(self) -> float | None:
        """Get max mtime of vault files, or None if vault empty/absent."""
        wiki_path = self.vault_path / self.qmd_scope
        if not wiki_path.exists():
            return None
        mtimes = [f.stat().st_mtime for f in wiki_path.rglob("*.md") if f.is_file()]
        return max(mtimes) if mtimes else None

    async def _async_rebuild_index(self) -> None:
        """Non-blocking index rebuild with lock to prevent concurrent rebuilds."""
        async with self._rebuild_lock:
            try:
                result = await asyncio.create_subprocess_exec(
                    "qmd", "index", "--scope", self.qmd_scope, "--rebuild",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(result.communicate(), timeout=self.TIMEOUT * 2)
                self._index_mtime = self._get_vault_mtime()
            except (asyncio.TimeoutError, Exception):
                pass  # Best-effort rebuild; search continues with stale index

    async def build_index(self) -> None:
        """Synchronous index rebuild wrapper (async-safe)."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_rebuild)

    def _sync_rebuild(self) -> None:
        """Synchronous index rebuild for use in executor."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.create_subprocess_exec(
                    "qmd", "index", "--scope", self.qmd_scope, "--rebuild",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
            )
        finally:
            loop.close()
```

**Acceptance:**
- Backend registers as `QMD_WIKI` in `BACKEND_NAME`
- `search_async` falls back to glob+grep when `qmd` raises `FileNotFoundError` or `asyncio.subprocess.SubprocessError`
- Add `_parse_qmd_json()`, `_fallback_grep()`, `_get_vault_mtime()`, `_sync_rebuild()`, and `_async_rebuild_index()` as new helper functions defined inline in this file (not imported)
- Add `_rebuild_lock` asyncio.Lock initialized in `__init__` (no new implementation)
- `_should_exclude()` is inherited from `BaseLocalBackend` (no new implementation)

---

### TASK-003: Wire QMDWikiBackend into UnifiedRouter

**Scope:**
- `P:/packages/search-research/core/backends/local/__init__.py` — import and export `QMDWikiBackend`
- `P:/packages/search-research/core/unified_router.py` — add `QMD_WIKI` to backend registry

**Acceptance:**
- `/search --backend QMD_WIKI` returns wiki search results
- `OBSIDIAN_VAULT_PATH` read from settings.json via `config`

---

### TASK-004: Add Obsidian vault configuration to search-research settings

**Scope:**
- `P:/packages/search-research/.claude/settings.json` — add settings keys

**Settings keys:**
```json
{
  "OBSIDIAN_VAULT_PATH": "~/.obsidian/vaults/personal-wiki",
  "QMD_WIKI_SOURCES": "sources/",
  "QMD_WIKI_SCOPE": "wiki/"
}
```

**Acceptance:**
- `OBSIDIAN_VAULT_PATH` configurable via settings.json
- Backend reads path from config, falls back to `~/.obsidian/vaults/personal-wiki`

---

## Test Matrix

| TASK | Test File | Cases |
|------|-----------|-------|
| TASK-002 | `pytest tests/test_backends/test_qmd_wiki_backend.py` | qmd available: returns search results from qmd JSON output; qmd unavailable: falls back to glob+grep; empty vault: returns empty results without error; malformed page (no frontmatter): skips page, logs warning; stale index: triggers async rebuild when vault mtime > index mtime |
| TASK-003 | `pytest tests/test_unified_router.py` | `QMD_WIKI` backend listed and callable via `--backend QMD_WIKI` |
| TASK-004 | `pytest tests/test_backends/test_qmd_wiki_backend.py` | Settings override: `OBSIDIAN_VAULT_PATH` from settings.json is used |

---

## Assumptions and Defaults

- Windows 11 environment (file paths use `Path` from `pathlib`)
- `qmd` CLI installable via `pip install qmd`
- Obsidian vault is git-tracked workspace-shared state
- Graceful degradation: glob+grep fallback preserves search without qmd

---

## Open Questions

None. All boundaries closed in `/arch` session this session.

---

## Constraint Classification

| Constraint | Type | Reason | Could This Be False? |
|------------|------|--------|---------------------|
| qmd CLI always available | assumed | User requested qmd integration | YES — graceful degradation handles absence |
| Vault is git-tracked | assumed | Convention from LLM Wiki pattern | NO — git is the multi-terminal coordination mechanism |
| LLM is sole wiki writer | soft | Design decision — prevents merge conflicts | Unlikely false |
| glob+grep fallback acceptable | soft | Degraded but functional | YES — for small vaults only |
