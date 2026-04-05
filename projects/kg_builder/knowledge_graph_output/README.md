# Knowledge Graph Output Directory

This directory contains knowledge graph data for the search-research package.

## File Format

### entities.json
List of entity objects with the following structure:
```json
[
  {
    "text": "entity name",
    "type": "concept|keyword|library|technique",
    "category": "category name",
    "description": "Entity description"
  }
]
```

### conversation_entities.json
Maps conversation IDs to lists of entities mentioned:
```json
{
  "conv_001": ["entity1", "entity2", "entity3"]
}
```

## Usage

The KG backend in search-research automatically loads data from this directory:
- Single entity search: `backend.search("async")`
- AND query: `backend.search("async AND rag")`
- Partial matches supported

## Configuration

Override the default path with environment variable:
```bash
export SEARCH_RESEARCH_KG_PATH="/path/to/kg/data"
```

## Integration

The KG backend is integrated into the search-research router:
```python
from core.router import SearchRouter

router = SearchRouter()
results = router.search("query", backends=["kg"])
```
