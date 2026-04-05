# Requirements Analysis: Next-Generation Code Intelligence

**TSK:** TSK-231223-CodeIntel-1406
**Step:** 2 - Requirements Analysis
**Date:** 2025-12-23 14:10 UTC

---

## Functional Requirements Deep Dive

### FR-1: LSP Integration (Priority: P0)

#### Detailed Requirements

**FR-1.1: Python LSP Support**
```python
# Required LSP features:
- goto_definition(symbol, file, line, col) -> Location
- find_references(symbol, file) -> List[Location]
- completion(file, line, col) -> List[CompletionItem]
- diagnostics(file) -> List[Diagnostic]
- hover(file, line, col) -> MarkupContent
- signature_help(file, line, col) -> SignatureInformation
```

**Acceptance Tests:**
```python
def test_python_goto_definition():
    """Test go-to-definition for Python symbols"""
    result = lsp_client.goto_definition("auth.py", 42, 10)
    assert result.file == "models.py"
    assert result.line == 15
    assert result.symbol == "User"

def test_python_find_references():
    """Test find-references across project"""
    refs = lsp_client.find_references("User.authenticate")
    assert len(refs) == 12
    assert all(ref.file.endswith(".py") for ref in refs)
```

**Implementation Options:**
1. **python-lsp-server** (Python-based, easier integration)
2. **Pyright** (Node-based, faster, Microsoft-backed)
3. **Pylsp** (vscode-python default)

**Recommendation:** Start with **python-lsp-server** for simplicity, add Pyright later.

---

**FR-1.2: TypeScript LSP Support**
```typescript
// Required LSP features:
- goto_definition
- find_references
- completion
- diagnostics
- rename_symbol
```

**Implementation Options:**
1. **typescript-language-server** (Official, stable)
2. **vtsls** (Faster, Vue ecosystem)
3. **eslint-language-server** (Linting-focused)

**Recommendation:** **typescript-language-server** for broad compatibility.

---

#### LSP Client Architecture

```python
class LSPClientManager:
    """Manage multiple LSP servers"""

    def __init__(self):
        self.servers = {}  # language -> LSPClient
        self.workspace = Path.cwd()

    async def start_server(self, language: str):
        """Start LSP server for language"""
        if language == "python":
            cmd = ["pylsp", "--stdio"]
        elif language == "typescript":
            cmd = ["typescript-language-server", "--stdio"]
        else:
            raise ValueError(f"Unsupported language: {language}")

        client = LSPClient(cmd, self.workspace)
        await client.start()
        self.servers[language] = client
        return client

    async def goto_definition(self, file: str, line: int, col: int):
        """Go to definition (auto-detect language)"""
        lang = detect_language(file)
        client = self.servers.get(lang)

        if not client:
            client = await self.start_server(lang)

        return await client.request("definition", {
            "textDocument": {"uri": file},
            "position": {"line": line, "character": col}
        })
```

---

### FR-2: ast-grep Integration (Priority: P0)

#### Detailed Requirements

**FR-2.1: Tree-sitter Parsing**
```python
# Required tree-sitter grammars:
- Python (tree-sitter-python)
- TypeScript (tree-sitter-typescript)
- JavaScript (tree-sitter-javascript)
- Go (tree-sitter-go)
- Rust (tree-sitter-rust)
```

**FR-2.2: Pattern Search**
```python
class ASTGrepClient:
    """ast-grep pattern search client"""

    def search_pattern(self, pattern: str, language: str, path: str):
        """Search for AST pattern in codebase"""
        cmd = [
            "ast-grep",
            "--lang", language,
            "--pattern", pattern,
            path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_results(result.stdout)

    def search_rewrite(self, pattern: str, fix: str, language: str):
        """Search and rewrite AST patterns"""
        cmd = [
            "ast-grep",
            "--lang", language,
            "--pattern", pattern,
            "--rewrite", fix
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_results(result.stdout)
```

**Pattern Library Examples:**
```python
# Python patterns
PATTERNS = {
    "bare_except": {
        "pattern": "try: $$BODY except: $$HANDLER",
        "description": "Bare except clause (anti-pattern)",
        "severity": "error",
        "fix": "try: $$BODY except Exception as e: $$HANDLER"
    },
    "async_without_await": {
        "pattern": "async function $$NAME() $$BODY { !await }",
        "description": "Async function without await",
        "severity": "warning",
        "fix": null  # No automatic fix
    },
    "global_variable": {
        "pattern": "global $$VAR",
        "description": "Global variable usage",
        "severity": "warning",
        "fix": null
    }
}
```

---

### FR-3: Graph Database Integration (Priority: P1)

#### Schema Design

```cypher
// Node types
(:Class {name, file, line, docstring})
(:Function {name, file, line, parameters, returns})
(:Variable {name, type, file, line})
(:Module {name, file, imports})

// Relationship types
-[:INHERITS]->       // Class inheritance
-[:CALLS]->          // Function calls
-[:IMPORTS]->        // Module imports
-[:DEFINES]->        // Defines variable/function
-[:REFERENCES]->      // Variable usage
-[:OVERRIDES]->      // Method override
```

**Example Graph:**
```cypher
// Create nodes
CREATE (u:Class {name: "User", file: "models.py", line: 10})
CREATE (a:Function {name: "authenticate", file: "models.py", line: 25})
CREATE (bc:Class {name: "BaseController", file: "controllers.py", line: 5})

// Create relationships
CREATE (u)-[:DEFINES]->(a)
CREATE (u)-[:INHERITS]->(bc)

// Query: Find all functions calling User.authenticate
MATCH (f:Function)-[:CALLS]->(a:Function {name: "authenticate"})
RETURN f.name, f.file
```

**Implementation Options:**
1. **Neo4j** (Full-featured, requires separate service)
2. **RocksDB** (Embedded, lightweight, less features)
3. **NetworkX** (In-memory, good for <10K nodes)

**Recommendation:** Start with **RocksDB** for simplicity, migrate to Neo4j if needed.

---

### FR-4: Cross-Repository Search (Priority: P1)

#### Repository Discovery

```python
class RepoIndexer:
    """Index multiple git repositories"""

    def __init__(self, root: Path):
        self.root = root
        self.repos = []

    def discover_repos(self):
        """Auto-discover git repositories"""
        for path in self.root.rglob(".git"):
            repo_path = path.parent
            if self._is_valid_repo(repo_path):
                self.repos.append(repo_path)

    def index_all(self):
        """Index all discovered repositories"""
        for repo in self.repos:
            self.index_repo(repo)

    def index_repo(self, repo_path: Path):
        """Index single repository"""
        # Skip excluded paths (venv, node_modules, etc.)
        filtered_files = filter_venv_and_cache(repo_path.rglob("*.py"))

        # Build LSP indexes
        for file in filtered_files:
            self.lsp_client.index_file(file)

        # Build ast-grep index
        self.ast_grep.index_repo(repo_path)

        # Build graph database
        self.graph_builder.build_from_repo(repo_path)
```

**Deduplication Strategy:**
```python
def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results across repos"""
    seen = set()
    unique = []

    for result in results:
        # Hash based on content, not location
        content_hash = hash(result.code_snippet)

        if content_hash not in seen:
            seen.add(content_hash)
            unique.append(result)

    return unique
```

---

### FR-5: Real-Time Updates (Priority: P2)

#### File System Watcher

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeWatcher(FileSystemEventHandler):
    """Watch filesystem for code changes"""

    def __init__(self, indexer):
        self.indexer = indexer

    def on_modified(self, event):
        if event.src_path.endswith((".py", ".ts", ".js")):
            print(f"File changed: {event.src_path}")
            self.indexer.incremental_update(event.src_path)

class IncrementalIndexer:
    """Incremental index updates"""

    def incremental_update(self, file_path: str):
        """Update indexes for single file"""
        # Update LSP cache
        self.lsp_client.invalidate_file(file_path)

        # Update ast-grep index
        self.ast_grep.reindex_file(file_path)

        # Update graph database
        self.graph_builder.update_file(file_path)

        # Clear affected cache entries
        self.cache.invalidate_patterns_for_file(file_path)
```

---

### FR-6: CKS Integration (Priority: P2)

#### Pattern Extraction

```python
class CKSPatternExtractor:
    """Extract code patterns for CKS storage"""

    def extract_from_analysis(self, analysis_results: dict):
        """Extract patterns from code analysis results"""

        patterns = []

        # Extract LSP diagnostics
        for diagnostic in analysis_results.get("diagnostics", []):
            pattern = {
                "title": f"LSP Diagnostic: {diagnostic['message']}",
                "content": diagnostic["message"],
                "metadata": {
                    "source": "lsp",
                    "severity": diagnostic["severity"],
                    "rule": diagnostic.get("code", "unknown")
                },
                "tags": ["lsp", "diagnostic", diagnostic["severity"]]
            }
            patterns.append(pattern)

        # Extract ast-grep matches
        for match in analysis_results.get("ast_grep_matches", []):
            pattern = {
                "title": f"AST Pattern: {match['pattern_id']}",
                "content": match["code_snippet"],
                "metadata": {
                    "source": "ast-grep",
                    "pattern": match["pattern"],
                    "file": match["file"]
                },
                "tags": ["ast-grep", "pattern", match["pattern_id"]]
            }
            patterns.append(pattern)

        # Store in CKS
        for pattern in patterns:
            self.cks.ingest_pattern(**pattern)

        return patterns
```

---

## Non-Functional Requirements Analysis

### NFR-1: Performance

**Target Metrics:**

| Operation | Target | 95th Percentile |
|-----------|--------|-----------------|
| LSP goto_definition | 200ms | 500ms |
| LSP find_references | 500ms | 2s |
| ast-grep pattern search | 500ms | 1s |
| Graph query (simple) | 50ms | 100ms |
| Graph query (complex) | 500ms | 1s |
| Cross-repo search | 1s | 2s |

**Performance Optimization Strategies:**

1. **Caching**
```python
from functools import lru_cache

class CachedLSPClient:
    @lru_cache(maxsize=1000)
    async def goto_definition(self, file: str, line: int, col: int):
        """Cached go-to-definition"""
        return await self._uncached_goto_definition(file, line, col)
```

2. **Parallel Execution**
```python
async def parallel_search(query: str, repos: List[Path]):
    """Search multiple repos in parallel"""
    tasks = [search_repo(query, repo) for repo in repos]
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

3. **Incremental Updates**
```python
# Only rebuild affected indexes on file change
def on_file_change(file_path: str):
    affected_functions = get_functions_in_file(file_path)

    for func in affected_functions:
        graph_db.update_node(func.id)
        cache.invalidate(f"function:{func.name}")
```

---

### NFR-2: Scalability

**Target Scale:**

| Metric | Target | Max |
|--------|--------|-----|
| LOC indexed | 100K | 1M |
| Repositories | 10 | 50 |
| Graph nodes | 10K | 100K |
| Graph edges | 100K | 1M |
| Cached patterns | 10K | 100K |

**Scalability Strategies:**

1. **Sharding**
```python
# Split index across multiple shards
class ShardedIndex:
    def __init__(self, num_shards: int = 4):
        self.shards = [Index() for _ in range(num_shards)]

    def get_shard(self, key: str) -> Index:
        shard_id = hash(key) % len(self.shards)
        return self.shards[shard_id]
```

2. **Lazy Loading**
```python
# Load LSP servers on-demand
class LazyLSPManager:
    def __init__(self):
        self.servers = {}

    async def get_server(self, lang: str):
        if lang not in self.servers:
            self.servers[lang] = await self.start_server(lang)
        return self.servers[lang]
```

3. **Connection Pooling**
```python
# Reuse database connections
class ConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.pool = Queue(maxsize=max_connections)

    def acquire(self):
        return self.pool.get()

    def release(self, conn):
        self.pool.put(conn)
```

---

### NFR-3: Usability

**CLI Design:**

```bash
# Unified interface
/codeintel "query" [options]

# Examples:
/codeintel "find all functions calling User.authenticate"
/codeintel --pattern "async function without await"
/codeintel --graph "show inheritance hierarchy for BaseController"
/codeintel --repos "all" "find JWT implementations"

# Output formats:
/codeintel --output json "query"
/codeintel --output graph "query"
/codeintel --output table "query"
```

**Query Language:**

```python
# Natural language queries
"find all functions calling database operations"
→ Parsed to: graph.query("MATCH (f:Function)-[:CALLS]->(db:DatabaseOperation)")

# Pattern queries
--pattern "bare_except"
→ Searches AST pattern library

# LSP queries
--lsp "definition of User.authenticate"
→ Uses LSP goto_definition
```

---

### NFR-4: Maintainability

**Modular Architecture:**

```
code_intelligence/
├── cli.py                 # CLI entry point
├── lsp/
│   ├── client.py          # LSP client manager
│   ├── python.py          # Python-specific
│   └── typescript.py      # TypeScript-specific
├── ast_grep/
│   ├── client.py          # ast-grep wrapper
│   └── patterns.py        # Pattern library
├── graph/
│   ├── builder.py         # Graph construction
│   ├── query.py           # Graph queries
│   └── storage.py         # Database backend
├── repo/
│   ├── indexer.py         # Repository indexer
│   └── watcher.py         # File system watcher
├── cks/
│   └── integration.py     # CKS integration
└── utils/
    ├── cache.py           # Caching utilities
    └── parallel.py        # Parallel execution
```

**Testing Strategy:**

```python
# Unit tests
tests/test_lsp_client.py
tests/test_ast_grep.py
tests/test_graph_builder.py

# Integration tests
tests/test_integration.py
tests/test_e2e.py

# Performance tests
tests/test_performance.py
```

---

### NFR-5: Compatibility

**Platform Support:**

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | ✅ Full support | Primary target |
| macOS | ✅ Full support | Tested on macOS 14+ |
| Windows | ⚠️ WSL2 only | Native Windows not supported |

**Python Version:** 3.11+

**Dependencies:**
```
python-lsp-server
typescript-language-server
ast-grep
rocksdb (or neo4j)
watchdog
pydantic
click
```

---

## Requirements Traceability Matrix

| ID | Requirement | Priority | Component | Test Case |
|----|-------------|----------|-----------|-----------|
| FR-1.1 | Python LSP | P0 | lsp/python.py | test_python_lsp.py |
| FR-1.2 | TypeScript LSP | P0 | lsp/typescript.py | test_ts_lsp.py |
| FR-1.3 | goto_definition | P0 | lsp/client.py | test_goto_def.py |
| FR-1.4 | find_references | P0 | lsp/client.py | test_find_refs.py |
| FR-1.5 | diagnostics | P0 | lsp/client.py | test_diagnostics.py |
| FR-1.6 | caching | P0 | utils/cache.py | test_lsp_cache.py |
| FR-2.1 | tree-sitter | P0 | ast_grep/client.py | test_tree_sitter.py |
| FR-2.2 | pattern search | P0 | ast_grep/client.py | test_patterns.py |
| FR-2.3 | multi-lang | P0 | ast_grep/patterns.py | test_multilang.py |
| FR-2.4 | rewriting | P0 | ast_grep/client.py | test_rewrite.py |
| FR-2.5 | integration | P0 | cli.py | test_integration.py |
| FR-3.1 | entities | P1 | graph/builder.py | test_entities.py |
| FR-3.2 | relationships | P1 | graph/builder.py | test_relationships.py |
| FR-3.3 | storage | P1 | graph/storage.py | test_storage.py |
| FR-3.4 | queries | P1 | graph/query.py | test_queries.py |
| FR-3.5 | visualization | P2 | graph/viz.py | test_viz.py |
| FR-4.1 | indexing | P1 | repo/indexer.py | test_indexing.py |
| FR-4.2 | deduplication | P1 | repo/indexer.py | test_dedup.py |
| FR-4.3 | context | P1 | cli.py | test_context.py |
| FR-4.4 | incremental | P1 | repo/watcher.py | test_incremental.py |
| FR-5.1 | watcher | P2 | repo/watcher.py | test_watcher.py |
| FR-5.2 | rebuild | P2 | repo/indexer.py | test_rebuild.py |
| FR-5.3 | invalidate | P2 | utils/cache.py | test_invalidate.py |
| FR-5.4 | reindex | P2 | cli.py | test_reindex.py |
| FR-6.1 | patterns | P2 | cks/integration.py | test_patterns.py |
| FR-6.2 | retrieval | P2 | cks/integration.py | test_retrieval.py |
| FR-6.3 | enforcement | P2 | cli.py | test_enforcement.py |
| FR-6.4 | learning | P2 | cks/integration.py | test_learning.py |

---

## Dependencies

**External Tools:**
- python-lsp-server >= 1.9.0
- typescript-language-server >= 4.0.0
- ast-grep >= 0.23.0
- rocksdb >= 9.0.0 (or neo4j >= 5.0.0)
- watchdog >= 4.0.0

**Python Libraries:**
- pydantic >= 2.0
- click >= 8.1
- aiohttp >= 3.9
- pytest >= 7.4

**Internal Modules:**
- cks.unified (CKS knowledge base)
- modules.discover.base_explorer (existing discovery)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LSP server crashes | High | Medium | Restart mechanism, health checks |
| Graph DB corruption | High | Low | Backups, write-ahead logging |
| Performance degradation | High | Medium | Caching, monitoring, optimization |
| Integration complexity | Medium | High | Modular design, phased rollout |
| Windows compatibility | Low | High | Document WSL2 requirement |

---

## Success Criteria Summary

**Must Have (P0):**
- ✅ LSP integration for Python + TypeScript
- ✅ ast-grep integration with 50+ patterns
- ✅ CLI interface matching `/discover`
- ✅ Performance targets met

**Should Have (P1):**
- ✅ Graph database integration
- ✅ Cross-repository search
- ✅ 80%+ test coverage

**Nice to Have (P2):**
- ✅ Real-time file watching
- ✅ Graph visualization
- ✅ CKS automatic learning
