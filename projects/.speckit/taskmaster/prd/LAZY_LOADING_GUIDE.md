# Lazy Loading and Caching Guide

## Overview

The PRDRegistry provides efficient lazy loading and intelligent caching for PRD documents. This guide explains how to use these features to optimize performance and memory usage when working with large collections of PRDs.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Lazy Loading](#lazy-loading)
3. [Caching Strategies](#caching-strategies)
4. [Thread Safety](#thread-safety)
5. [File Watching](#file-watching)
6. [Performance Tuning](#performance-tuning)
7. [Usage Patterns](#usage-patterns)
8. [API Reference](#api-reference)

---

## Quick Start

```python
from prd import create_registry

# Create registry with automatic PRD discovery
registry = create_registry([
    r"P:/projects/*/docs/PRD.md",
    r"P:/projects/*/PRD.md",
])

# PRDs are discovered but NOT loaded yet
print(f"Discovered: {len(registry.list_prds())} PRDs")

# Load specific PRD on-demand (lazy loading)
prd = registry.get("yt_sync")

# Search across all PRDs
results = registry.search_requirements("authentication")

# Check cache performance
stats = registry.get_stats()
print(f"Cache hit rate: {stats.cache_hit_rate():.1%}")
```

---

## Lazy Loading

### What is Lazy Loading?

Lazy loading means PRD files are loaded **only when needed**, not at startup. This provides:

- **Fast startup**: No delay parsing hundreds of PRDs
- **Low memory**: Only loaded PRDs consume memory
- **On-demand access**: Load only what you use

### How It Works

```python
# Step 1: Discover PRD files (fast - just file system scan)
registry.discover(["P:/projects/*/docs/PRD.md"])

# Step 2: Load specific PRD when needed (slower - parses file)
prd = registry.get("my_project")  # First access = cache miss, loads from disk

# Step 3: Subsequent access use cache (fast - memory lookup)
prd = registry.get("my_project")  # Second access = cache hit
```

### Lazy Loading Benefits

| Scenario | Eager Loading | Lazy Loading |
|----------|--------------|--------------|
| 100 PRDs, use 5 | Parse all 100 | Parse only 5 |
| Startup time | 5-10 seconds | < 0.1 seconds |
| Memory usage | ~100MB | ~5MB |
| Cache hit rate | 100% (wastes time) | Varies by usage |

---

## Caching Strategies

### LRU (Least Recently Used) Cache

The registry uses LRU eviction when the cache is full:

```python
registry = PRDRegistry(
    prd_paths=["P:/projects/*/docs/PRD.md"],
    cache_size=50,  # Max 50 PRDs in memory
)

# Load 60 PRDs
for i in range(60):
    registry.get(f"project_{i}")

# Only 50 most recent PRDs remain cached
# Oldest 10 were automatically evicted
```

### TTL (Time-To-Live) Cache

Automatically expire cache entries after a time period:

```python
# Cache PRDs for 1 hour
registry = PRDRegistry(
    prd_paths=["P:/projects/*/docs/PRD.md"],
    ttl_seconds=3600,  # 1 hour
)

prd = registry.get("project_a")  # Loads and caches

# 1 hour later...
prd = registry.get("project_a")  # Reloads from disk (cache expired)
```

### Manual Cache Management

```python
# Check if PRD is loaded
if registry.is_loaded("project_a"):
    print("Already in cache")

# Get cache entry info
info = registry.get_cache_info("project_a")
print(f"Loaded: {info['loaded_at']}")
print(f"Access count: {info['access_count']}")
print(f"Idle time: {info['idle_seconds']:.1f}s")

# Invalidate specific PRD
registry.invalidate("project_a")

# Clear all cached PRDs
registry.clear_cache()

# Evict idle PRDs
evicted = registry.evict_stale(max_idle_seconds=3600)  # 1 hour
print(f"Evicted {evicted} idle PRDs")
```

---

## Thread Safety

All registry operations are **thread-safe** using reentrant locks:

```python
import concurrent.futures

def load_prd(name):
    return registry.get(name)

# Safe concurrent access
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(load_prd, name)
               for name in prd_names]
    results = [f.result() for f in futures]

# Only loads each PRD once (other threads wait)
stats = registry.get_stats()
print(f"Loaded: {stats.loaded_prds}, Cache hits: {stats.cache_hits}")
```

### Thread Safety Guarantees

- ✅ Multiple threads can call `get()` simultaneously
- ✅ Cache is always consistent (no corrupted state)
- ✅ Statistics are atomically updated
- ✅ Discovery is thread-safe

---

## File Watching

The registry can detect when PRD files are modified:

```python
# Enable file watching (default: enabled)
registry = PRDRegistry(
    prd_paths=["P:/projects/*/docs/PRD.md"],
    enable_file_watching=True,
)

prd = registry.get("project_a")

# Someone edits the file...
# Next get() automatically reloads
prd = registry.get("project_a")  # Reloads with new content
```

### File Watching Behavior

| Scenario | File Watch ON | File Watch OFF |
|----------|--------------|----------------|
| File modified | Auto-reload next get() | Uses stale cache |
| Performance | Slight overhead (mtime check) | Maximum speed |
| Use case | Development environments | Production/read-only |

---

## Performance Tuning

### Cache Size Guidelines

```python
# Small projects (< 20 PRDs)
cache_size=20

# Medium projects (20-100 PRDs)
cache_size=50

# Large projects (> 100 PRDs)
cache_size=100  # Cache only frequently accessed PRDs
```

### TTL Guidelines

```python
# Development (PRDs change frequently)
ttl_seconds=300  # 5 minutes

# Staging (occasional changes)
ttl_seconds=3600  # 1 hour

# Production (rare changes)
ttl_seconds=None  # No expiration
```

### Preloading Strategy

```python
# Load all PRDs at startup (defeats lazy loading!)
registry.preload()  # Only if you need all PRDs

# Load only critical PRDs
registry.preload([
    "core_project",
    "api_project",
    "database_project",
])

# Or use pattern: load on first access
prd = registry.get("any_project")  # Loads if needed, uses cache if available
```

### Performance Monitoring

```python
# Get cache statistics
stats = registry.get_stats()

print(f"Total PRDs: {stats.total_prds}")
print(f"Loaded: {stats.loaded_prds}")
print(f"Cache hits: {stats.cache_hits}")
print(f"Cache misses: {stats.cache_misses}")
print(f"Hit rate: {stats.cache_hit_rate():.1%}")
print(f"Avg load time: {stats.avg_load_time*1000:.1f}ms")

# Analyze cache usage
for info in registry.get_loaded_prds_info():
    print(f"{info['prd_name']}: {info['access_count']} accesses, "
          f"{info['idle_seconds']:.0f}s idle")
```

---

## Usage Patterns

### Pattern 1: On-Demand Loading

```python
# Best for: CLI tools, infrequent access
registry = create_registry(["P:/projects/*/docs/PRD.md"])

def show_prd(name):
    prd = registry.get(name)  # Loads only when requested
    if prd:
        print(f"{prd.prd_name}: {prd.total_requirements} requirements")
```

### Pattern 2: Warm Cache with Favorites

```python
# Best for: Apps with frequently used PRDs
registry = create_registry(["P:/projects/*/docs/PRD.md"])

# Preload frequently accessed PRDs
registry.preload(["core", "api", "database"])

# Others load on-demand
prd = registry.get("rare_project")  # Loads when needed
```

### Pattern 3: Search-First Workflow

```python
# Best for: Interactive search interfaces
registry = create_registry(["P:/projects/*/docs/PRD.md"])

def search(query):
    # Loads all PRDs (can be slow for many PRDs)
    results = registry.search_requirements(query, loaded_only=False)

    for prd_name, req_id, text in results:
        print(f"{prd_name}/{req_id}: {text}")
```

### Pattern 4: Memory-Constrained Environment

```python
# Best for: Limited memory, many PRDs
registry = PRDRegistry(
    prd_paths=["P:/projects/*/docs/PRD.md"],
    cache_size=10,  # Small cache
    ttl_seconds=600,  # Expire after 10 minutes
)

def process_prd(name):
    prd = registry.get(name)
    # Process...
    # Let cache evict naturally
```

---

## API Reference

### PRDRegistry

```python
PRDRegistry(
    prd_paths: List[str],
    cache_size: int = 100,
    ttl_seconds: Optional[float] = None,
    enable_file_watching: bool = True,
    base_path: Optional[str] = None,
)
```

**Parameters:**
- `prd_paths`: Glob patterns to find PRD files
- `cache_size`: Maximum number of PRDs to cache
- `ttl_seconds`: Cache TTL in seconds (None = no expiration)
- `enable_file_watching`: Detect file modifications
- `base_path`: Base path for relative patterns

### Key Methods

#### Discovery

```python
registry.discover(prd_paths: Optional[List[str]] = None) -> int
```
Discover PRD files without loading them.

#### Loading

```python
registry.get(prd_name: str, force_reload: bool = False) -> Optional[ParsedPRD]
```
Get a PRD by name (lazy loading).

```python
registry.get_by_path(prd_path: str) -> Optional[ParsedPRD]
```
Get a PRD by file path.

```python
registry.preload(prd_names: Optional[List[str]] = None) -> int
```
Preload specific PRDs or all discovered PRDs.

#### Cache Management

```python
registry.is_loaded(prd_name: str) -> bool
```
Check if PRD is currently cached.

```python
registry.invalidate(prd_name: str) -> bool
```
Invalidate cache entry for a PRD.

```python
registry.clear_cache() -> int
```
Clear all cached PRDs.

```python
registry.evict_stale(max_idle_seconds: float) -> int
```
Evict PRDs idle longer than specified.

#### Information

```python
registry.list_prds(loaded_only: bool = False) -> List[str]
```
List all or only loaded PRD names.

```python
registry.get_stats() -> RegistryStats
```
Get cache performance statistics.

```python
registry.get_cache_info(prd_name: str) -> Optional[Dict[str, Any]]
```
Get detailed cache entry information.

#### Search

```python
registry.search_requirements(
    query: str,
    search_titles: bool = True,
    search_descriptions: bool = True,
    case_sensitive: bool = False,
    loaded_only: bool = True,
) -> List[Tuple[str, str, str]]
```
Search requirements across PRDs.

#### Iteration

```python
registry.iterate_loaded_prds() -> Iterator[Tuple[str, ParsedPRD]]
```
Iterate over all cached PRDs.

---

## Examples

### Example 1: CLI Tool with Lazy Loading

```python
#!/usr/bin/env python3
from prd import create_registry

def main():
    registry = create_registry([r"P:/projects/*/docs/PRD.md"])

    print(f"Found {len(registry.list_prds())} PRDs")

    while True:
        name = input("Enter PRD name (or 'quit'): ")
        if name == 'quit':
            break

        prd = registry.get(name)
        if prd:
            print(f"\n{prd.prd_name}")
            print(f"Requirements: {prd.total_requirements}")
            for req in prd.functional_requirements[:5]:
                print(f"  {req.id}: {req.title}")
        else:
            print("PRD not found")

if __name__ == "__main__":
    main()
```

### Example 2: Web Service with Cache Monitoring

```python
from prd import create_registry
from flask import Flask, jsonify

app = Flask(__name__)
registry = create_registry([r"P:/projects/*/docs/PRD.md"])

@app.route("/prd/<name>")
def get_prd(name):
    prd = registry.get(name)
    if prd:
        return jsonify({
            "name": prd.prd_name,
            "requirements": prd.total_requirements,
        })
    return jsonify({"error": "Not found"}), 404

@app.route("/stats")
def get_stats():
    stats = registry.get_stats()
    return jsonify({
        "total": stats.total_prds,
        "loaded": stats.loaded_prds,
        "hit_rate": stats.cache_hit_rate(),
    })
```

### Example 3: Batch Processing with Memory Management

```python
from prd import create_registry

registry = PRDRegistry(
    prd_paths=[r"P:/projects/*/docs/PRD.md"],
    cache_size=5,  # Small cache to limit memory
)

def process_all_prds():
    names = registry.list_prds()

    for i, name in enumerate(names):
        # Load PRD
        prd = registry.get(name)

        # Process
        print(f"[{i+1}/{len(names)}] {prd.prd_name}: "
              f"{prd.total_requirements} requirements")

        # Cache automatically evicts old entries

        # Periodic cache clear for very large datasets
        if i % 100 == 0:
            registry.clear_cache()
```

---

## Troubleshooting

### Problem: High Memory Usage

**Solution:** Reduce cache size or enable TTL:

```python
registry = PRDRegistry(
    prd_paths=["..."],
    cache_size=20,  # Reduce from default 100
    ttl_seconds=1800,  # Expire after 30 minutes
)
```

### Problem: Slow First Access

**Solution:** Preload frequently used PRDs:

```python
registry.preload(["core", "api", "database"])
```

### Problem: Stale Data

**Solution:** Enable file watching or use force_reload:

```python
# Enable file watching
registry = PRDRegistry(enable_file_watching=True)

# Or force reload
prd = registry.get("project", force_reload=True)
```

### Problem: Low Cache Hit Rate

**Solution:** Increase cache size or check access patterns:

```python
# Increase cache
registry = PRDRegistry(cache_size=200)

# Analyze usage
for info in registry.get_loaded_prds_info():
    print(f"{info['prd_name']}: {info['access_count']} hits")
```

---

## Best Practices

1. **Use lazy loading** for CLI tools and scripts
2. **Preload critical PRDs** for web services
3. **Enable file watching** in development
4. **Disable file watching** in production for speed
5. **Monitor cache statistics** to optimize cache size
6. **Use TTL** for development environments
7. **Use eviction** for long-running processes
8. **Thread-safe** for concurrent access
9. **Search with loaded_only=True** for frequent searches
10. **Clear cache** periodically for batch processing

---

**Version:** 2.0.0
**Author:** Claude Code
**Last Updated:** 2025-12-25
