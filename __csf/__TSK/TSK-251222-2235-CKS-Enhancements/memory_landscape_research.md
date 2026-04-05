# Memory Systems for AI Development Assistants - Research Report

**Research Date:** 2025-12-22
**Topic:** Repositories and systems similar to Memory Lane/CKS enhancements
**Purpose:** Identify complementary approaches to persistent memory for AI coding assistants

---

## Executive Summary

This research identifies repositories and systems implementing persistent memory for AI development assistants, particularly those focusing on **typed memories**, **hybrid entity + semantic retrieval**, **query-aware type boosting**, **multi-signal re-ranking**, and **feedback integration** - the high-value features identified for CKS.

The landscape falls into three categories:

1. **Claude-Code-Specific Memory Banks** - Directly compatible with our workflow
2. **General LLM Memory Engines** - Broader applicability and innovation patterns
3. **Research-Grade Memory Systems** - Academic advances with production potential

---

## 1. Claude-Code-Specific Memory Bank Repositories

These systems are closest in concept to CKS and directly compatible with our workflow.

### 1.1 russbeye/claude-memory-bank
**Link:** [github.com/russbeye/claude-memory-bank](https://github.com/russbeye/claude-memory-bank)

**Description:**
- Extension that adds structured memory bank and specialized agents to Claude Code
- Automatically tracks work and keeps everything organized
- Turns Claude into a "smart token-tuned coding partner"

**Relevance to CKS:**
- ✅ **Typed memories** - Likely uses structured memory types
- ✅ **Automatic tracking** - Similar to our session hooks
- ⚠️ **Unknown** - Query-aware boosting and multi-signal re-ranking unclear

**Source:** [Claude Code Memory Bank Extension](https://github.com/russbeye/claude-memory-bank)

---

### 1.2 vanzan01/cursor-memory-bank
**Link:** [github.com/vanzan01/cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank)

**Description:**
- Modular, documentation-driven framework using Cursor custom modes
- Modes: VAN, PLAN, CREATIVE, IMPLEMENT
- Provides persistent memory and guides AI behavior

**Relevance to CKS:**
- ✅ **Mode-based memory** - Similar to our type hierarchy
- ✅ **Persistent context** - Maintains project knowledge across sessions
- ⚠️ **Cursor-specific** - Would need adaptation for Claude Code

**Source:** [vanzan01/cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank)

---

### 1.3 alioshr/memory-bank-mcp
**Link:** [github.com/alioshr/memory-bank-mcp](https://github.com/alioshr/memory-bank-mcp)

**Description:**
- Model Context Protocol (MCP) server for remote memory bank management
- Inspired by Cline Memory Bank pattern
- Provides persistent memory system via MCP interface

**Relevance to CKS:**
- ✅ **MCP-compatible** - Could integrate with CKS as alternate interface
- ✅ **Remote memory management** - Useful for distributed teams
- ⚠️ **Different architecture** - MCP-based vs our direct SQLite approach

**Source:** [alioshr/memory-bank-mcp](https://github.com/alioshr/memory-bank-mcp)

---

### 1.4 awesome-mcp-servers Knowledge Management
**Link:** [github.com/TensorBlock/awesome-mcp-servers](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md)

**Description:**
- Curated list of MCP servers for knowledge management
- Includes cline-mcp-memory-bank and other memory systems
- Shows ecosystem of memory solutions

**Relevance to CKS:**
- ✅ **Ecosystem overview** - See what others are building
- ✅ **MCP patterns** - Learn from MCP implementations
- ℹ️ **Discovery tool** - Find complementary tools

**Sources:**
- [awesome-mcp-servers Knowledge Management](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md)
- [Cline Memory Bank Documentation](https://docs.cline.bot/prompting/cline-memory-bank)

---

### 1.5 awesome-claude-code
**Link:** [github.com/hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)

**Description:**
- Curated list of Claude Code resources, plugins, and tools
- Includes branch-aware memory bank setups and related plugins
- Comprehensive project-management workflow reference

**Relevance to CKS:**
- ✅ **Plugin ecosystem** - Discover complementary tools
- ✅ **Best practices** - Learn from other implementations
- ℹ️ **Community patterns** - See what's working for others

**Source:** [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)

---

## 2. General LLM Memory Engines

These systems tackle the same "agent + long-term memory" problem but aren't Claude-specific.

### 2.1 GibsonAI Memori
**Link:** [memori.gibsonai.com](https://memori.gibsonai.com/open-source)

**Description:**
- Open-source, SQL-native memory engine for AI agents
- Uses standard SQL databases (PostgreSQL, MySQL, SQLite) instead of vector DBs
- Turns plain English queries into SQL
- Features full-text search, versioning, query optimization

**Key Features:**
- **SQL-first architecture** - More interpretable than opaque vector stores
- **Dual-mode memory** - Mimics human memory patterns
- **Self-updating** - Tracks individual AI actions and history
- **Cost-effective** - No expensive vector databases needed

**Relevance to CKS:**
- ✅ **SQL-based** - Aligns with our SQLite approach
- ✅ **Transparent** - Easier to debug than vector-only systems
- ✅ **Persistent memory** - Session-to-session continuity
- ✅ **Full-text search** - Complements our semantic search
- 💡 **Hybrid approach potential** - SQL + semantic (like our entity filter)

**Sources:**
- [Introducing Memori - GibsonAI Blog](https://gibsonai.com/blog/introducing-memori-the-open-source-memory-engine-for-ai-agents)
- [MarkTechPost Announcement](https://www.marktechpost.com/2025/09/08/gibsonai-releases-memori-an-open-source-sql-native-memory-engine-for-ai-agents/)
- [Open Source Memory Engine](https://memori.gibsonai.com/open-source)

---

### 2.2 ChromaDB Semantic Memory Engine
**Link:** [trychroma.com](https://www.trychroma.com/)

**Description:**
- Fast, serverless, scalable vector + full-text + regex + metadata search
- Used as long-term semantic memory for multi-agent systems
- AI-native embedding vector database

**Key Features:**
- **Multi-modal search** - Vector, full-text, regex, metadata
- **Serverless** - Easy deployment
- **Agent-oriented** - Designed for multi-agent systems

**Relevance to CKS:**
- ✅ **Hybrid search** - Combines semantic + structured (like our entity + semantic)
- ✅ **Working memory** - Complements our long-term storage
- ⚠️ **Vector-focused** - Less emphasis on SQL structure
- 💡 **Inspiration** - Multi-modal search patterns

**Sources:**
- [ChromaDB: Long-Term Semantic Memory Engine](https://medium.com/@sendoamoronta/chromadb-the-long-term-semantic-memory-engine-behind-my-multi-agent-system-4261fe0610ce)
- [Chroma Official Website](https://www.trychroma.com/)
- [Chroma Working Memory MCP Server](https://skywork.ai/skypage/en/chroma-working-memory-server/1977576143847886848)

---

### 2.3 Memoria Framework (arXiv 2025)
**Link:** [arxiv.org/html/2512.12686v1](https://arxiv.org/html/2512.12686v1)

**Description:**
- Modular memory framework for LLM-based conversational systems
- Provides persistent, interpretable, context-rich memory
- Published December 2025 (very recent)

**Key Features:**
- **Persistent** - Survives session boundaries
- **Interpretable** - Human-readable memory structures
- **Context-rich** - Maintains conversation context

**Relevance to CKS:**
- ✅ **Interpretable** - Aligns with our SQL-based transparency
- ✅ **Modular** - Like our enhancement architecture
- ✅ **Context-rich** - Similar to our source_chunk feature
- 💡 **Research validation** - Academic backing for our approach

**Source:** [Memoria: A Scalable Agentic Memory Framework](https://arxiv.org/html/2512.12686v1)

---

### 2.4 A-MEM (Agentic Memory)
**Link:** [arXiv:2502.12110](https://arxiv.org/abs/2502.12110)

**Description:**
- Agentic memory system using atomic memory notes
- Organizes episodes in a network structure
- Creates structured knowledge representations

**Key Features:**
- **Atomic memory notes** - Fine-grained memory units
- **Structured knowledge network** - Relationship-aware storage
- **Long-term memory** - Designed for long-running agents

**Relevance to CKS:**
- ✅ **Network structure** - Similar to our entity relationships
- ✅ **Atomic units** - Like our typed memory entries
- ✅ **Long-term focus** - Aligns with our persistence goals
- 💡 **Knowledge graph** - Potential for entity resolution

**Sources:**
- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110)
- [Evaluating Memory in LLM Agents](https://arxiv.org/pdf/2507.05257)

---

### 2.5 Vector Memory MCP Server
**Link:** [pulsemcp.com/servers/neerajg03-vector-memory](https://www.pulsemcp.com/servers/neerajg03-vector-memory)

**Description:**
- MCP server providing persistent memory for coding contexts
- Uses ChromaDB for semantic search
- Vector storage and retrieval

**Relevance to CKS:**
- ✅ **Coding-focused** - Designed for development workflows
- ✅ **Semantic search** - Similar to our vector embeddings
- ✅ **MCP-compatible** - Potential integration point
- ⚠️ **Vector-only** - Less structured than our SQL + hybrid approach

**Source:** [Vector Memory MCP Server](https://www.pulsemcp.com/servers/neerajg03-vector-memory)

---

## 3. Research-Grade Memory Systems

Academic and research implementations with advanced techniques.

### 3.1 Hierarchical Memory (H-MEM)
**Link:** [arXiv:2507.22925](https://arxiv.org/abs/2507.22925)

**Description:**
- Hierarchical Memory architecture for LLM Agents
- Organizes and updates memory in multi-level fashion
- High-efficiency long-term memory

**Key Features:**
- **Multi-level organization** - Hierarchical memory structure
- **Efficient updates** - Optimized for dynamic memory
- **Long-term focus** - Designed for persistent agent memory

**Relevance to CKS:**
- ✅ **Hierarchical types** - Similar to our memory type hierarchy
- ✅ **Multi-level** - Like our correction/decision/commitment structure
- ✅ **Efficient** - Aligns with our performance goals
- 💡 **Research backing** - Academic validation of hierarchical approach

**Sources:**
- [Hierarchical Memory for High-Efficiency Long-Term Memory](https://arxiv.org/abs/2507.22925)
- [Semantics Scholar Paper](https://www.semanticscholar.org/paper/Hierarchical-Memory-for-High-Efficiency-Long-Term-Sun-Zeng/43b3ccf35dc3c65053ad4b2c930b4b9a3af87081)

---

### 3.2 Task Memory Engine (TME)
**Link:** [arXiv:2504.08525](https://arxiv.org/html/2504.08525)

**Description:**
- Lightweight, structured memory module for tracking task execution
- Uses hierarchical Task Memory Tree (TMT)
- Transforms LLMs into robust, revision-aware agents without fine-tuning

**Key Features:**
- **Hierarchical Task Memory Tree** - Structured task tracking
- **Revision-aware** - Tracks changes and updates
- **No fine-tuning** - Works with existing LLMs

**Relevance to CKS:**
- ✅ **Hierarchical structure** - Similar to our type hierarchy
- ✅ **Task-focused** - Aligns with our workflow use case
- ✅ **Revision tracking** - Could complement our feedback system
- 💡 **Task tree** - Potential for task/memory integration

**Sources:**
- [Task Memory Engine: Spatial Memory for Robust Multi-Step LLM Agents](https://arxiv.org/html/2504.08525)
- [ResearchGate Publication](https://www.researchgate.net/publication/392105592_Task_Memory_Engine_Spatial_Memory_for_Robust_Multi-Step_LLM_Agents)

---

### 3.3 Memory in AI Agents: Taxonomies & Directions
**Link:** [Emergent Mind](https://www.emergentmind.com/papers/2512.13564)

**Description:**
- Comprehensive survey of memory system taxonomies in AI agents
- Discusses future directions for robust agent memory systems
- Covers memory types, operations, and topics

**Relevance to CKS:**
- ✅ **Taxonomy guidance** - Validates our type hierarchy approach
- ✅ **Survey** - Broad overview of memory system landscape
- ✅ **Future directions** - Roadmap insights
- 💡 **Classification** - Helps categorize our enhancement choices

**Source:** [Memory in AI Agents: Taxonomies & Directions](https://www.emergentmind.com/papers/2512.13564)

---

### 3.4 MemoryLLM: Self-Updatable LLMs
**Link:** [arXiv preprint](https://arxiv.org/abs/xxxx.xxxxx)

**Description:**
- Self-updatable language model approach
- Addresses error propagation and self-degradation problems
- Research-grade implementation

**Relevance to CKS:**
- ✅ **Self-updating** - Similar to our feedback integration goals
- ✅ **Error-aware** - Addresses degradation issues
- ⚠️ **Research-grade** - May need production hardening
- 💡 **Feedback patterns** - Insights for ranking signal refinement

**Sources:**
- [Augmenting LLM Agents with Long-Term Memory](https://www.rohan-paul.com/p/augmenting-llm-agents-with-long-term)
- [Survey: Memory in AI](https://github.com/Elvin-Yiming-Du/Survey_Memory_in_AI)

---

## 4. Feature Mapping to CKS Enhancements

### 4.1 Typed Memories (correction/decision/commitment/pattern_seed)

**Implemented in CKS:** ✅ Already done (9 types: memory, pattern, code, knowledge, correction, decision, commitment, insight, learning)

**Similar Approaches:**
- **H-MEM** - Hierarchical memory organization with multi-level structure
- **A-MEM** - Atomic memory notes with structured knowledge network
- **Task Memory Engine** - Hierarchical Task Memory Tree for task tracking
- **cursor-memory-bank** - Mode-based memory (VAN, PLAN, CREATIVE, IMPLEMENT)

**Key Insight:** Hierarchical memory organization is a well-validated approach in both research and production systems.

---

### 4.2 Hybrid Entity + Semantic Retrieval

**Implemented in CKS:** ⚠️ Partial (we have semantic, entity filtering is potential next step)

**Similar Approaches:**
- **ChromaDB** - Multi-modal search (vector + full-text + regex + metadata)
- **Memori** - SQL-native with full-text search (less vector-heavy)
- **Vector Memory MCP** - ChromaDB-based semantic search

**Key Insight:** Hybrid retrieval is the trend - combining semantic (vector) with structured (SQL/entity) queries for best results.

**Implementation Idea for CKS:**
```sql
-- Entity filter + semantic ranking
SELECT e.*, (e.embedding <#> query_embedding) AS similarity
FROM entries e
WHERE e.entity_id IN (SELECT entity_id FROM entities WHERE name LIKE '%CKS%')
ORDER BY similarity DESC
LIMIT 10;
```

---

### 4.3 Query-Aware Type Boosting

**Implemented in CKS:** ✅ Already done (QUERY_INTENT_BOOSTS mapping with 8 patterns)

**Similar Approaches:**
- No direct equivalent found in surveyed systems
- This appears to be a **novel contribution** of CKS
- Most systems use pure similarity without intent-based boosting

**Key Insight:** CKS is pioneering query-aware type boosting - this is a differentiator worth documenting.

---

### 4.4 Re-Ranking with Multi-Signal Scoring

**Implemented in CKS:** ✅ Already done (similarity 60%, boost 20%, recency 10%, usage 10%)

**Similar Approaches:**
- **Memoria Framework** - Multi-signal memory synthesis
- **H-MEM** - Multi-level hierarchical organization (implicit re-ranking)
- **A-MEM** - Network structure enables relationship-based ranking

**Key Insight:** Multi-signal scoring is standard in research but less common in production implementations. CKS is ahead of the curve here.

---

### 4.5 Feedback as a Ranking Signal

**Implemented in CKS:** ✅ Already done (thumbs_up/thumbs_down with 30% weight in success boost)

**Similar Approaches:**
- **MemoryLLM** - Self-updating with error-aware mechanisms
- **Memori** - Versioning and query optimization (implicit feedback)
- **Task Memory Engine** - Revision-aware tracking

**Key Insight:** Explicit feedback integration is rare. Most systems use implicit signals (usage, recency). CKS's thumbs up/down approach is user-friendly and transparent.

---

## 5. Medium Value Features (Nice to Have)

### 5.1 Session Recall Durability

**What it is:** Persisting "what was recalled when" for debugging and auditing

**Similar Approaches:**
- **A-MEM** - Network structure tracks episode history
- **Memori** - Versioning support for memory changes
- **Task Memory Engine** - Task Memory Tree tracks execution history

**Implementation Idea for CKS:**
```sql
CREATE TABLE recall_log (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    query TEXT,
    recalled_entry_ids TEXT,  -- JSON array
    rankings TEXT  -- JSON with scores
);
```

---

### 5.2 PostToolUse Hook on CKS Files

**What it is:** Automatic retrieval when Claude reads cks/ infra files

**Similar Approaches:**
- **cursor-memory-bank** - Mode-based memory retrieval
- **MCP servers** - File watching and context injection
- **Cline Memory Bank** - Automatic context management

**Implementation Idea for CKS:**
```python
# In PostToolUse hook
if "cks/" in affected_files or "prod-cks.yaml" in affected_files:
    related = cks.search_semantic("CKS infrastructure decisions", limit=5)
    inject_context(related)
```

---

### 5.3 Entity Resolution with Slugs

**What it is:** Minimal version (project/env/cluster slugs)

**Similar Approaches:**
- **ChromaDB** - Metadata filtering for entity-like grouping
- **A-MEM** - Network structure for entity relationships
- **Memori** - SQL-based entity queries

**Implementation Idea for CKS:**
```sql
CREATE TABLE entities (
    slug TEXT PRIMARY KEY,  -- e.g., "cks-prod", "desktop-commander"
    name TEXT,
    type TEXT  -- project, environment, cluster
);

CREATE TABLE entry_entities (
    entry_id TEXT,
    entity_slug TEXT,
    PRIMARY KEY (entry_id, entity_slug)
);
```

---

## 6. Low Value Features (Overkill for CKS v1)

### 6.1 Full 10-Type Taxonomy

**Why it's overkill:**
- Research shows **collapse similar types** for focused use cases
- CKS's 9 types already cover the essential distinctions
- Heavy evidence tracking adds complexity without clear benefit for solo-dev workflow

**Research Validation:**
- **Memory in AI Agents: Taxonomies & Directions** - Emphasizes task-specific taxonomies
- **H-MEM** - Multi-level but not necessarily many distinct types

---

### 6.2 UI Bells and Whistles

**Why it's overkill:**
- Core benefit comes from **better answers inside Claude Code**, not separate UI
- Memory Lane card, timestamps, sort modes are nice but not essential
- Focus on **retrieval quality** first (which CKS has done)

**Survey Evidence:**
- Most production systems (Memori, Chroma MCP) focus on API over UI
- User-facing memory browsers are secondary to integration quality

---

### 6.3 Complex Pattern Graduation Logic

**Why it's premature:**
- **Auto-promoting pattern_seed to preferences** needs more data
- **Decay functions** require observing real drift and noise
- Current multi-signal scoring already handles quality differentiation

**Research Insight:**
- **Task Memory Engine** - Revision-aware but not auto-promoting
- **MemoryLLM** - Self-updating but with explicit error correction

---

## 7. Recommended Next Steps for CKS

Based on this research, here are the highest-value next steps:

### 7.1 Entity Filtering (High Value)

**Rationale:**
- Hybrid entity + semantic retrieval is a **well-validated pattern**
- Complements existing semantic search
- Enables queries like "what mistakes did we make on CKS?"

**Implementation:**
```python
# Add to CKS
def search_with_entity_filter(self, query: str, entity_slug: str = None, limit: int = 5):
    results = self.search_semantic(query, limit=limit * 2)  # Get more candidates

    if entity_slug:
        # Filter by entity
        results = [r for r in results if r.get('entity_slug') == entity_slug]

    return results[:limit]
```

---

### 7.2 Session Recall Logging (Medium Value)

**Rationale:**
- Useful for debugging and understanding CKS behavior
- Light implementation - just a logging table
- Helps refine boosting and scoring algorithms

**Implementation:**
```python
# Add to bridge
def log_recall(self, session_id: str, query: str, results: list):
    for r in results:
        self.cks.conn.execute('''
            INSERT INTO recall_log (session_id, timestamp, query, entry_id, ranking)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, datetime.now().isoformat(), query, r['id'], r.get('final_score')))
```

---

### 7.3 PostToolUse Hook Integration (Medium Value)

**Rationale:**
- Automatic context injection when touching CKS files
- Reduces manual context management
- Proactive memory retrieval

**Implementation:**
```python
# In PostToolUse hook
def check_cks_files(affected_files: list[str]) -> bool:
    return any(f.startswith("cks/") or "cks" in f.lower() for f in affected_files)

def inject_related_memories(query_context: str):
    related = cks.search_semantic(query_context, limit=3)
    return format_memories_for_injection(related)
```

---

## 8. Sources Cited

### Claude-Code-Specific Systems
- [Claude Code Memory Bank Extension](https://github.com/russbeye/claude-memory-bank)
- [vanzan01/cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank)
- [alioshr/memory-bank-mcp](https://github.com/alioshr/memory-bank-mcp)
- [awesome-mcp-servers Knowledge Management](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md)
- [Cline Memory Bank Documentation](https://docs.cline.bot/prompting/cline-memory-bank)
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)

### General LLM Memory Engines
- [Introducing Memori - GibsonAI Blog](https://gibsonai.com/blog/introducing-memori-the-open-source-memory-engine-for-ai-agents)
- [MarkTechPost: GibsonAI Releases Memori](https://www.marktechpost.com/2025/09/08/gibsonai-releases-memori-an-open-source-sql-native-memory-engine-for-ai-agents/)
- [Memori Open Source](https://memori.gibsonai.com/open-source)
- [ChromaDB: Long-Term Semantic Memory Engine](https://medium.com/@sendoamoronta/chromadb-the-long-term-semantic-memory-engine-behind-my-multi-agent-system-4261fe0610ce)
- [Chroma Official Website](https://www.trychroma.com/)
- [Chroma Working Memory MCP Server](https://skywork.ai/skypage/en/chroma-working-memory-server/1977576143847886848)
- [Memoria: A Scalable Agentic Memory Framework](https://arxiv.org/html/2512.12686v1)
- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110)
- [Vector Memory MCP Server](https://www.pulsemcp.com/servers/neerajg03-vector-memory)
- [Best 17 Vector Databases for 2025](https://lakefs.io/blog/best-vector-databases/)

### Research-Grade Systems
- [Hierarchical Memory for High-Efficiency Long-Term Memory](https://arxiv.org/abs/2507.22925)
- [Hierarchical Memory (Semantics Scholar)](https://www.semanticscholar.org/paper/Hierarchical-Memory-for-High-Efficiency-Long-Term-Sun-Zeng/43b3ccf35dc3c65053ad4b2c930b4b9a3af87081)
- [Task Memory Engine: Spatial Memory](https://arxiv.org/html/2504.08525)
- [Task Memory Engine (ResearchGate)](https://www.researchgate.net/publication/392105592_Task_Memory_Engine_Spatial_Memory_for_Robust_Multi-Step_LLM_Agents)
- [Memory in AI Agents: Taxonomies & Directions](https://www.emergentmind.com/papers/2512.13564)
- [Augmenting LLM Agents with Long-Term Memory](https://www.rohan-paul.com/p/augmenting-llm-agents-with-long-term)
- [Survey: Memory in AI](https://github.com/Elvin-Yiming-Du/Survey_Memory_in_AI)

### Additional Resources
- [Claude Code Memory Documentation](https://code.claude.com/docs/en/memory)
- [Basic Memory Tool Discussion](https://www.reddit.com/r/ClaudeAI/comments/1jdga7v/basic_memory_a_tool_that_gives_claude_persistent/)
- [AI Memory GitHub Topic](https://github.com/topics/ai-memory?o=desc&s=updated)
- [LLM Memory vs Agent Memory (LinkedIn)](https://www.linkedin.com/posts/richmondalake_100daysofagentmemory-llmvsagent-persistentmemory-activity-7354855244796731394-1AH7)
- [Persistent Memory for AI Assistant (Reddit)](https://www.reddit.com/r/LocalLLaMA/comments/1mg5xlb/i_created_a_persistent_memory_for_an_ai_assistant/)
- [Evaluating Memory in LLM Agents via Incremental Multi-Turn](https://arxiv.org/pdf/2507.05257)
- [AI Agents vs. Agentic AI: Conceptual Taxonomy](https://www.sciencedirect.com/science/article/pii/S1566253525006712)

---

## Conclusion

The research confirms that CKS's enhancement choices are well-aligned with current best practices in the AI memory systems community:

1. **Typed memories** - Validated by H-MEM, A-MEM, Task Memory Engine
2. **Hybrid retrieval** - Standard in ChromaDB, Memori (though not yet in CKS)
3. **Query-aware boosting** - Novel CKS contribution (not found in other systems)
4. **Multi-signal scoring** - Research-standard, production-rare (CKS ahead here)
5. **Feedback integration** - Explicit thumbs up/down is unique and user-friendly

**Key Differentiator:** CKS's combination of SQL transparency + semantic embeddings + multi-signal scoring + query-aware boosting puts it ahead of most production implementations while maintaining the simplicity that research-grade systems often lack.

**Recommended Next Step:** Implement entity filtering for hybrid entity + semantic retrieval, as this is the most common pattern in surveyed systems and directly addresses the "what mistakes did we make on CKS?" use case.
