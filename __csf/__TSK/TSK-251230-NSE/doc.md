# Documentation: FAISS Incremental Update Optimization

**Date**: 2025-12-31
**Step**: CWO12 Step 11 - Documentation

## Overview

This document describes the optimized FAISS incremental update system for Chat History Search (CHS).

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Incremental CHS Update                       │
├─────────────────────────────────────────────────────────────────┤
│  1. State Manager (chs_incremental_state.json)                  │
│     - file_byte_position: Resume position in history.jsonl      │
│     - last_indexed_count: Total messages indexed                │
│     - last_update: ISO timestamp of last update                │
│                                                                  │
│  2. Message Loader (load_new_messages)                          │
│     - Seeks to file_byte_position                               │
│     - Skips first partial line                                  │
│     - Processes remaining lines (no duplicate check!)           │
│                                                                  │
│  3. Embedding Generator (generate_embeddings)                   │
│     - Uses ComponentManager singleton (cached model)            │
│     - L2-normalizes for cosine similarity                       │
│                                                                  │
│  4. FAISS Updater (FAISSVectorStore.incremental_update)         │
│     - Deduplicates new messages                                 │
│     - Creates automatic backups                                 │
│     - Atomically updates index                                  │
└─────────────────────────────────────────────────────────────────┘
```

## API Reference

### incremental_chs_update.py

#### Main Entry Point

```bash
python incremental_chs_update.py [--force] [--batch-size N] [--no-backup]
```

**Arguments**:
- `--force`: Rescan from beginning (ignore position tracking)
- `--batch-size N`: Embedding batch size (default: 512)
- `--no-backup`: Skip backup before update

#### State File Format

```json
{
  "last_indexed_timestamp": 1735651106785,
  "last_indexed_count": 98037,
  "last_update": "2025-12-31T13:38:26.813814",
  "file_byte_position": 2787278016
}
```

#### Functions

**load_new_messages()**
```python
def load_new_messages(
    history_path: Path,
    indexed_ids: set[str],
    min_timestamp: int = 0,
    force: bool = False,
    start_byte: int = 0,
    skip_duplicate_check: bool = False
) -> tuple[list[dict], int]:
    """Load new messages from history.jsonl.

    Args:
        history_path: Path to history.jsonl
        indexed_ids: Set of already indexed message IDs (for backwards compat)
        min_timestamp: Minimum timestamp (not used with position tracking)
        force: Force rescan from beginning
        start_byte: Byte position to start reading from
        skip_duplicate_check: Skip msg_id check when using position tracking

    Returns:
        Tuple of (new_messages, last_byte_position)
    """
```

**generate_embeddings()**
```python
def generate_embeddings(
    messages: list[dict],
    batch_size: int = 512
) -> np.ndarray:
    """Generate embeddings using singleton ComponentManager.

    Args:
        messages: List of message dicts with 'content' field
        batch_size: Embedding batch size (GPU-optimized)

    Returns:
        L2-normalized embeddings (float32)
    """
```

## Usage Examples

### Manual Incremental Update

```bash
# Standard incremental update
cd P:\__csf.nip
python src/modules/analysis/chat_search/incremental_chs_update.py

# Force full rescan
python src/modules/analysis/chat_search/incremental_chs_update.py --force

# With custom batch size
python src/modules/analysis/chat_search/incremental_chs_update.py --batch-size 256
```

### Programmatic Usage

```python
from pathlib import Path
from lib.core_utils.embedding_manager import ComponentManager
from lib.core_utils.faiss_vector_store import FAISSVectorStore

# Get singleton embedding manager (cached)
manager = ComponentManager.get_embedding_manager("all-mpnet-base-v2")

# Generate embeddings
embeddings = manager.encode(["message 1", "message 2"])

# Update FAISS index
store = FAISSVectorStore(index_path="path/to/index")
result = store.incremental_update(
    messages=[{"id": "msg1", "content": "message 1"}],
    embeddings=embeddings,
    backup=True,
    validate=True
)
```

## Performance Characteristics

### Scanning Performance

| Scenario | Lines | Time |
|----------|-------|------|
| Initial scan (no position) | 424,795 | ~60s |
| Incremental (with position) | ~7 | <1s |

### Update Performance

| Operation | Time |
|-----------|------|
| Model load (first run) | 2-3s |
| Model load (cached) | ~0s |
| Embeddings (6 messages) | <1s |
| FAISS index save | ~100s |
| Backup creation | ~50s |

### Bottlenecks

1. **FAISS index save**: ~100s (dominates incremental update time)
2. **Backup creation**: ~50s (can be skipped with --no-backup)

## Troubleshooting

### Issue: "File position corrupted"

**Solution**:
```bash
# Reset to full scan
rm P:/__csf.nip/data/chs_incremental_state.json
python incremental_chs_update.py --force
```

### Issue: "Duplicate messages in index"

**Solution**: FAISSVectorStore.incremental_update() already deduplicates. If duplicates persist, check metadata.pkl for corruption.

### Issue: "Update too slow"

**Solution**: The 100s overhead is FAISS index save. Use --no-backup to skip backup (not recommended).

## Configuration

### Environment Variables

None required. All configuration is via command-line arguments.

### Paths

| Path | Purpose |
|------|---------|
| `P:\__csf.nip\data\chat_history_faiss_424k` | FAISS index location |
| `P:\__csf.nip\data\chs_incremental_state.json` | State file |
| `C:\Users\{user}\.claude\history.jsonl` | Chat history |

## Future Enhancements

1. **Async index saves**: Reduce 100s FAISS save overhead
2. **Periodic rebuilds**: Instead of per-update saves
3. **Compression**: Reduce index size
4. **Incremental backups**: Only backup changed vectors

## References

- FAISS documentation: https://faiss.ai/
- Sentence Transformers: https://www.sbert.net/
- ComponentManager: `P:\__csf.nip\src\lib\core_utils\embedding_manager.py`
- FAISSVectorStore: `P:\__csf.nip\src\lib\core_utils\faiss_vector_store.py`
