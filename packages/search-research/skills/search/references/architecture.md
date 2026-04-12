# Search Architecture

## Routing Modes

The `UnifiedAsyncRouter` supports 4 operating modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `local-only` | Local sources only (CKS, CHS, CDS, code, docs, skills) | Privacy-preserving, fast |
| `auto` | Local + web quality check + optional web | Balanced coverage |
| `web-fallback` | Local first, then web if insufficient results | Comprehensive |
| `unified` | Full progressive enhancement with RRF fusion | Best quality |

**TF-IDF topic alignment** is computed between query and result content, stored in `metadata["topic_alignment_score"]`.

## Chat History Architecture (Updated 2026-03-19)

Chat history search is handled by the **claude-history** Rust package:

| System | Technology | Purpose |
|--------|------------|---------|
| **claude-history** | Rust + SQLite FTS5 | Fast keyword search over chat history |
| **semantic_daemon** | Python + FAISS | CKS knowledge search (memories/patterns) |

**Why the split?**
- Chat history is keyword-heavy ("what did we say about X") -> FTS5 is optimal
- Knowledge is semantic-heavy ("patterns for async") -> FAISS is optimal
- Rust provides true parallelism, no GIL, better performance

**claude-history backend details:**
- Location: `P:/packages/claude-history/`
- Python wrapper: `core/backends/local/claude_history_backend.py`
- Data sources: JSONL streaming (default) + SQLite FTS5 (indexed)
- Score: 0.9 (competitive with CKS for chat queries)
- Character boundary fix: v1.0.1 - Fixed UTF-8 multi-byte character slicing

## Architecture Alignment

- Unified search interface replacing multiple specialized search commands
- Parallel execution across backends for speed
- Integrates with CKS/CHS storage systems

## NotebookLM Backend

When you need comprehensive, citation-backed answers from your curated knowledge base:

```bash
# Search your NotebookLM notebooks
/search "how does authentication work?" --backend notebooklm

# Get long-form synthesis with sources
/search "debugRCA architecture patterns" --backend notebooklm

# Zero-hallucination answers from your uploaded docs
/search "what did we decide about X?" --backend notebooklm
```

**NotebookLM is ideal for:**
- Deep research on topics you've documented in notebooks
- Multi-document synthesis across your sources
- Zero-hallucination answers (grounded in your sources)
- Long-form explanations with attribution

**Integration:** Requires `notebooklm-mcp` MCP server (installed via `uv tool install notebooklm-mcp-cli`)
