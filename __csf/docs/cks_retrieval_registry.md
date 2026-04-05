# CKS Retrieval Registry

**Purpose**: Enable skills to declare their CKS query needs for automatic context injection.

## Pattern

Skills can declare `cks_queries` in their `SKILL.md` or routing.py to enable automatic lesson retrieval:

```markdown
## CKS Integration

cks_queries:
  - trigger: "user asks about {domain}"
    query: "{domain} patterns precedents"
    entry_types: ["pattern", "decision"]
    limit: 3
  - trigger: "before suggesting {pattern}"
    query: "{pattern} best practices"
    entry_types: ["pattern"]
    limit: 2
```

## Usage in Skills

### Example: `/arch` skill

The `/arch` skill already has CKS integration in `routing.py`:
```python
def cks_semantic_search(query: str, limit: int = 5) -> list[dict]:
    """Search CKS for relevant precedents."""
    daemon = DaemonClient(auto_start=True, enable_fallback=True)
    result = daemon.search("cks", query, limit=limit)
    return result.get("results", [])
```

### Adding to New Skills

To add CKS retrieval to a skill:

1. Import the DaemonClient
2. Query CKS with relevant terms
3. Inject results into skill context

**Example minimal integration**:
```python
from daemons.daemon_client import DaemonClient

def get_relevant_lessons(query: str) -> list[dict]:
    daemon = DaemonClient(auto_start=True, enable_fallback=True)
    result = daemon.search("cks", query, limit=3)
    return result.get("results", []) if result.get("status") == "success" else []
```

## Current CKS Usage Locations

| Location | Type | Trigger |
|----------|------|---------|
| `SessionStart_ckseeder.py` | Auto-inject | Session start |
| `vague_directive_gate.py` | Hook advisory | Vague directives |
| `authorization_gate.py` | Hook advisory | Destructive actions |
| `investigation_gate.py` | Hook advisory | Debug/investigate |
| `src/core/lesson_extractor.py` | Novelty check | Before storing |
| `skills/arch/routing.py` | Precedent search | Architecture queries |
| `skills/learn/learn.py` | Direct search | User invoked |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CKS_SEEDER_ENABLED` | true | Enable session-start injection |
| `CKS_SEEDER_LESSON_COUNT` | 3 | Max lessons to inject |
| `CKS_SEEDER_THRESHOLD` | 0.7 | Similarity threshold 0-1 |

## Implementation Status

- [x] Session-start seeder (SessionStart_ckseeder.py)
- [x] Usage tracking metadata (last_accessed in store_to_cks)
- [x] Bi-directional CHS↔CKS linkage (chs_references in metadata)
- [ ] Skill-level CKS query registry (pattern for future skills)
- [ ] `/garden cks` stale entry detection (uses last_accessed)
- [ ] Proactive lesson suggestions (deferred - high cost/uncertain benefit)
