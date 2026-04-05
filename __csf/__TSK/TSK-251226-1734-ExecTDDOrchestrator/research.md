# Research Intelligence

## Existing CKS Semantic Search

Current CKS already has semantic search capability:
- Located in `P:/__csf.nip/src/cks/unified.py`
- Uses `all-MiniLM-L6-v2` model (384 dimensions)
- FAISS index for fast similarity search
- Disabled in hooks due to 8.3s model load time

## IPC Mechanism Options

| Option | Pros | Cons | Selected |
|--------|------|------|----------|
| HTTP (FastAPI) | Standard, testable, cross-platform | Extra dependency | ✅ Yes |
| Unix socket | Fast, no HTTP overhead | Windows only (WSL2 issues) | ❌ No |
| Named pipe | Windows native | Complex protocol | ❌ No |
| gRPC | Type-safe, fast | Overkill for local IPC | ❌ No |

## Daemon Management Approaches

### Option 1: Subprocess with Status Polling
- Simple, reliable
- No external dependencies
- ✅ Selected

## Timeout Refresh Implementation

### Strategy: Query-Based Heartbeat

```python
class TimeoutRefresh:
    def __init__(self, timeout_seconds=3600):
        self.timeout = timeout_seconds
        self.last_activity = time.time()

    def refresh(self):
        """Called on each query"""
        self.last_activity = time.time()

    def should_shutdown(self):
        """Background thread check"""
        return time.time() - self.last_activity > self.timeout
```

## Key Findings

1. **CKS semantic search already exists** - just needs daemon wrapper
2. **HTTP is best IPC choice** - standard, testable, works cross-platform
3. **Subprocess management is straightforward** - Python has robust support
4. **Timeout refresh is simple** - track last activity, check in background thread
