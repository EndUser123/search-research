# Consolidated Search Features

Includes functionality from `search-more`, `progressive-search`, `chs`, and `recent`.

## Source Control (`--source`)

| Value | Description | Equivalent To |
|-------|-------------|----------------|
| `local` | Local sources: CKS, CHS, CDS, Code, DOCS, SKILLS | Default `/find` behavior |
| `chat` | Chat history only | `/chs`, `/recent` |
| `all` | Search all local sources | Combines local + chat |

```bash
# Search chat history with FAISS
/find "authentication" --source chat --chat-method vector

# Search only local sources
/find "database" --source local

# Search all local
/find "async patterns" --source all
```

**Note:** For web search, use `/web` instead.

## Chat Search Method (`--chat-method`)

When `--source chat` is specified, choose the search algorithm:

| Value | Description | Performance | When To Use |
|-------|-------------|-------------|-------------|
| `vector` | FAISS semantic search | <1s (indexed), 87s (first) | Deep history, semantic meaning |
| `grep` | Reverse grep scan | Instant | Recent messages (minutes/hours) |
| `auto` | Auto-detect best method | Varies | Let system decide |

```bash
# Deep semantic search
/find "we discussed authentication" --source chat --chat-method vector

# Fast recent message search
/find "what happened 5 min ago" --source chat --chat-method grep

# Auto-detect (system chooses based on query)
/find "git commit message" --source chat --chat-method auto
```

**Auto-detection logic:**
- Time-based queries ("5 minutes ago", "recent", "today") -> `grep`
- Semantic queries ("we discussed", "meaning of", "concept") -> `vector`
- Default -> `vector`

## Detail Level (`--depth`)

| Value | Description | Token Cost | When To Use |
|-------|-------------|------------|-------------|
| `summary` | Lightweight index with IDs | ~10x savings | Initial exploration, finding relevant results |
| `full` | Complete content for all results | High | Final research, need all details |
| `auto` | Auto-detect based on query | Varies | Let system decide |

```bash
# Get lightweight index (token-efficient)
/find "authentication" --depth summary

# Get full details immediately
/find "authentication" --depth full

# Auto-detect based on result count
/find "authentication" --depth auto
```

**Auto-detection logic:**
- Query contains "ID", "specific", "details" -> `full`
- Query returns <10 results -> `summary`
- Default -> `summary`

## Progressive Disclosure Workflow

For token-efficient research:

1. **Start with summary:**
   ```bash
   /find "authentication" --depth summary
   # Returns: [1] CHS: User auth flow (ID: chs_abc123)
   #          [2] CKS: Auth module (ID: cks_def456)
   ```

2. **Review interesting results:**
   ```bash
   /find "authentication" --source local --depth summary
   # Identify which IDs are relevant
   ```

3. **Drill down to specific IDs:**
   ```bash
   /find "chs_abc123,cks_def456" --source local --depth full
   # Fetches full content only for specified IDs
   ```

**Token savings:** ~90% for typical workflows

## Recent Message Search (Fast Reverse Grep)

For very recent messages (minutes/hours old), the system automatically uses reverse grep instead of FAISS:

```bash
# Messages newer than FAISS index
/find "litellm error" --source chat --chat-method grep

# Time-windowed recent search
/find "faiss" --source chat --chat-method grep --minutes 60
```

This bypasses the 11-minute FAISS rebuild and provides instant results for recent conversations.

## Combined Examples

```bash
# Deep chat history search (weeks/months)
/find "database design" --source chat --chat-method vector --depth summary

# Recent messages only (today)
/find "faiss" --source chat --chat-method grep

# Local sources with summary
/find "async patterns" --source local --depth summary

# Everything with full details
/find "architecture" --source all --depth full

# Auto-detect everything
/find "git hooks" --depth auto --chat-method auto
```

---

## Migration Reference

| Old Command | New Behavior | Notes |
|-------------|--------------|-------|
| `/chs "query"` | `/find "query"` | Auto-detects chat intent |
| `/recent "query"` | `/find "query"` | Auto-detects recent + grep |
| `/find-more "id"` | `/find "id" --depth full` | Drill-down by ID |
| `/progressive-search` | `/find "query"` | Auto depth selection |

**Auto-detection means you rarely need flags.** Just search naturally:

```bash
# These all work - no flags needed
/find "what did we discuss about authentication"  # -> chat search
/web "how does FAISS work"                    # -> web search
/find "authentication [recent]"              # -> recent chat
```

**The /chs skill directory has been deleted.** All functionality is now in /find with smarter defaults.
