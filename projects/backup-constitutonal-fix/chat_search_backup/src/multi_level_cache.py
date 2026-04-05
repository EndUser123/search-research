#!/usr/bin/env python3
"""
Multi-Level Caching System for CHS
Provides L1 (memory), L2 (session), and L3 (persistent) caching layers
"""

import gzip
import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: datetime
    ttl: timedelta
    hit_count: int = 0
    access_frequency: float = 1.0

    @property
    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > self.ttl

    def update_access(self):
        self.hit_count += 1
        # Update frequency using exponential moving average
        self.access_frequency = 0.9 * self.access_frequency + 0.1 * self.hit_count


class L1MemoryCache:
    """L1 Cache: In-memory cache with fast access"""

    def __init__(self, max_size: int = 1000, default_ttl: timedelta = timedelta(minutes=30)):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__ + ".L1")

    def _evict_expired(self) -> int:
        """Remove expired entries"""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

    def _evict_lru(self) -> str:
        """Evict least recently used entry"""
        if not self.cache:
            return None

        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].access_frequency)
        del self.cache[lru_key]
        self.logger.debug(f"L1 evicted LRU entry: {lru_key}")
        return lru_key

    def get(self, key: str) -> Any | None:
        """Get value from L1 cache"""
        with self.lock:
            entry = self.cache.get(key)
            if entry:
                if entry.is_expired:
                    del self.cache[key]
                    self.logger.debug(f"L1 expired entry: {key}")
                    return None
                entry.update_access()
                self.logger.debug(f"L1 hit: {key}")
                return entry.value
            return None

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in L1 cache"""
        with self.lock:
            # Clean expired entries first
            self._evict_expired()

            # Enforce size limit
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl=ttl or self.default_ttl
            )

            self.cache[key] = entry
            self.logger.debug(f"L1 set: {key}")
            return True

    def invalidate(self, key: str) -> bool:
        """Remove specific key from L1 cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.logger.debug(f"L1 invalidated: {key}")
                return True
            return False

    def clear(self) -> int:
        """Clear all entries from L1 cache"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.logger.info(f"L1 cleared {count} entries")
            return count

    def get_stats(self) -> dict[str, Any]:
        """Get L1 cache statistics"""
        with self.lock:
            return {
                "level": "L1",
                "type": "memory",
                "size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size,
                "total_hits": sum(e.hit_count for e in self.cache.values()),
                "expired_entries": sum(1 for e in self.cache.values() if e.is_expired)
            }


class L2SessionCache:
    """L2 Cache: Session-based persistent cache"""

    def __init__(self, session_id: str, cache_dir: Path,
                 max_size: int = 10000, default_ttl: timedelta = timedelta(hours=6)):
        self.session_id = session_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.default_ttl = default_ttl

        # SQLite for persistent storage
        self.db_path = self.cache_dir / f"session_cache_{session_id}.db"
        self._init_db()

        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__ + ".L2")

    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    timestamp REAL NOT NULL,
                    ttl_seconds REAL NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    access_frequency REAL DEFAULT 1.0
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)
            ''')
            conn.commit()

    def _serialize_entry(self, entry: CacheEntry) -> bytes:
        """Serialize cache entry"""
        data = {
            'key': entry.key,
            'value': entry.value,
            'timestamp': entry.timestamp.isoformat(),
            'ttl_seconds': entry.ttl.total_seconds(),
            'hit_count': entry.hit_count,
            'access_frequency': entry.access_frequency
        }
        return gzip.compress(pickle.dumps(data))

    def _deserialize_entry(self, data: bytes) -> CacheEntry:
        """Deserialize cache entry"""
        entry_data = pickle.loads(gzip.decompress(data))
        return CacheEntry(
            key=entry_data['key'],
            value=entry_data['value'],
            timestamp=datetime.fromisoformat(entry_data['timestamp']),
            ttl=timedelta(seconds=entry_data['ttl_seconds']),
            hit_count=entry_data['hit_count'],
            access_frequency=entry_data['access_frequency']
        )

    def _cleanup_expired(self) -> int:
        """Remove expired entries from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute('''
                DELETE FROM cache_entries
                WHERE timestamp + ttl_seconds < ?
            ''', (now,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def _cleanup_overflow(self) -> int:
        """Remove oldest entries if cache is full"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check current size
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            current_size = cursor.fetchone()[0]

            if current_size <= self.max_size:
                return 0

            # Remove oldest entries
            entries_to_remove = current_size - self.max_size
            cursor.execute('''
                DELETE FROM cache_entries
                WHERE key IN (
                    SELECT key FROM cache_entries
                    ORDER BY access_frequency ASC, timestamp ASC
                    LIMIT ?
                )
            ''', (entries_to_remove,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def get(self, key: str) -> Any | None:
        """Get value from L2 cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT data, hit_count, access_frequency FROM cache_entries
                        WHERE key = ?
                    ''', (key,))

                    row = cursor.fetchone()
                    if not row:
                        return None

                    # Deserialize and check expiration
                    entry = self._deserialize_entry(row[0])
                    if entry.is_expired:
                        # Remove expired entry
                        cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                        conn.commit()
                        return None

                    # Update access statistics
                    entry.update_access()
                    serialized = self._serialize_entry(entry)
                    cursor.execute('''
                        UPDATE cache_entries
                        SET data = ?, hit_count = ?, access_frequency = ?
                        WHERE key = ?
                    ''', (serialized, entry.hit_count, entry.access_frequency, key))
                    conn.commit()

                    self.logger.debug(f"L2 hit: {key}")
                    return entry.value

            except Exception as e:
                self.logger.error(f"L2 get error for {key}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in L2 cache"""
        with self.lock:
            try:
                # Create entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    timestamp=datetime.now(),
                    ttl=ttl or self.default_ttl
                )

                serialized = self._serialize_entry(entry)
                ttl_seconds = ttl.total_seconds() if ttl else self.default_ttl.total_seconds()
                timestamp = entry.timestamp.timestamp()

                with sqlite3.connect(self.db_path) as conn:
                    # Check if we need cleanup
                    self._cleanup_expired()
                    self._cleanup_overflow()

                    # Insert or replace
                    conn.execute('''
                        INSERT OR REPLACE INTO cache_entries
                        (key, data, timestamp, ttl_seconds, hit_count, access_frequency)
                        VALUES (?, ?, ?, ?, 0, 1.0)
                    ''', (key, serialized, timestamp, ttl_seconds))
                    conn.commit()

                self.logger.debug(f"L2 set: {key}")
                return True

            except Exception as e:
                self.logger.error(f"L2 set error for {key}: {e}")
                return False

    def invalidate(self, key: str) -> bool:
        """Remove specific key from L2 cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    deleted = cursor.rowcount
                    conn.commit()
                    if deleted:
                        self.logger.debug(f"L2 invalidated: {key}")
                    return deleted > 0
            except Exception as e:
                self.logger.error(f"L2 invalidate error for {key}: {e}")
                return False

    def clear(self) -> int:
        """Clear all entries from L2 cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM cache_entries')
                    count = cursor.fetchone()[0]
                    cursor.execute('DELETE FROM cache_entries')
                    conn.commit()
                    self.logger.info(f"L2 cleared {count} entries")
                    return count
            except Exception as e:
                self.logger.error(f"L2 clear error: {e}")
                return 0

    def get_stats(self) -> dict[str, Any]:
        """Get L2 cache statistics"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Basic counts
                    cursor.execute('SELECT COUNT(*) FROM cache_entries')
                    total_entries = cursor.fetchone()[0]

                    # Expired entries
                    cursor.execute('''
                        SELECT COUNT(*) FROM cache_entries
                        WHERE timestamp + ttl_seconds < ?
                    ''', (time.time(),))
                    expired_entries = cursor.fetchone()[0]

                    # Hit statistics
                    cursor.execute('SELECT SUM(hit_count) FROM cache_entries')
                    total_hits = cursor.fetchone()[0] or 0

                    return {
                        "level": "L2",
                        "type": "session_sqlite",
                        "size": total_entries,
                        "max_size": self.max_size,
                        "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
                        "total_hits": total_hits,
                        "expired_entries": expired_entries,
                        "session_id": self.session_id,
                        "db_path": str(self.db_path)
                    }
            except Exception as e:
                self.logger.error(f"L2 stats error: {e}")
                return {"error": str(e)}


class L3PersistentCache:
    """L3 Cache: Long-term persistent cache for frequently used patterns"""

    def __init__(self, cache_dir: Path,
                 max_size: int = 50000, default_ttl: timedelta = timedelta(days=7)):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.default_ttl = default_ttl

        # Use JSON files for pattern storage
        self.patterns_file = self.cache_dir / "persistent_patterns.jsonl"
        self.metadata_file = self.cache_dir / "persistent_metadata.json"

        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__ + ".L3")
        self._init_metadata()

    def _init_metadata(self):
        """Initialize metadata file"""
        if not self.metadata_file.exists():
            metadata = {
                "created": datetime.now().isoformat(),
                "last_cleaned": datetime.now().isoformat(),
                "total_patterns": 0,
                "version": "1.0"
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

    def _generate_pattern_key(self, query: str, filters: dict[str, Any]) -> str:
        """Generate pattern key for caching"""
        pattern_data = {
            "query": query.lower().strip(),
            "session_filter": filters.get("session_filter", "all"),
            "context_filter": filters.get("context_filter", "all"),
            "rank_by": filters.get("rank_by", "relevance")
        }
        pattern_str = json.dumps(pattern_data, sort_keys=True)
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]

    def _cleanup_old_patterns(self) -> int:
        """Clean up old or low-frequency patterns"""
        if not self.patterns_file.exists():
            return 0

        cleaned_count = 0
        current_time = time.time()
        cutoff_time = current_time - self.default_ttl.total_seconds()

        # Read all patterns
        patterns = []
        with open(self.patterns_file) as f:
            for line in f:
                try:
                    pattern = json.loads(line.strip())
                    patterns.append(pattern)
                except:
                    continue

        # Filter patterns
        filtered_patterns = []
        for pattern in patterns:
            timestamp = pattern.get("timestamp", 0)
            frequency = pattern.get("access_frequency", 1.0)

            # Keep if recent or high frequency
            if timestamp > cutoff_time or frequency > 2.0:
                filtered_patterns.append(pattern)
            else:
                cleaned_count += 1

        # Keep only top patterns by size
        if len(filtered_patterns) > self.max_size:
            # Sort by frequency and keep top entries
            filtered_patterns.sort(key=lambda x: x.get("access_frequency", 1.0), reverse=True)
            excess = len(filtered_patterns) - self.max_size
            cleaned_count += excess
            filtered_patterns = filtered_patterns[:self.max_size]

        # Write back filtered patterns
        if cleaned_count > 0:
            with open(self.patterns_file, 'w') as f:
                for pattern in filtered_patterns:
                    f.write(json.dumps(pattern) + '\n')

            # Update metadata
            metadata = {
                "created": datetime.now().isoformat(),
                "last_cleaned": datetime.now().isoformat(),
                "total_patterns": len(filtered_patterns),
                "version": "1.0"
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        return cleaned_count

    def get(self, query: str, filters: dict[str, Any]) -> Any | None:
        """Get cached search results for pattern"""
        with self.lock:
            pattern_key = self._generate_pattern_key(query, filters)

            if not self.patterns_file.exists():
                return None

            try:
                with open(self.patterns_file) as f:
                    for line in f:
                        try:
                            pattern = json.loads(line.strip())
                            if pattern.get("key") == pattern_key:
                                # Check expiration
                                timestamp = pattern.get("timestamp", 0)
                                if time.time() - timestamp > self.default_ttl.total_seconds():
                                    continue

                                # Update access stats
                                pattern["hit_count"] = pattern.get("hit_count", 0) + 1
                                pattern["last_accessed"] = time.time()
                                pattern["access_frequency"] = min(10.0, pattern.get("access_frequency", 1.0) * 1.1)

                                self.logger.debug(f"L3 pattern hit: {pattern_key}")
                                return pattern.get("results")
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.logger.error(f"L3 get error: {e}")

            return None

    def set(self, query: str, filters: dict[str, Any], results: Any,
            ttl: timedelta | None = None) -> bool:
        """Store search results as persistent pattern"""
        with self.lock:
            try:
                pattern_key = self._generate_pattern_key(query, filters)

                # Check if we need cleanup
                if self.patterns_file.exists():
                    size = sum(1 for _ in open(self.patterns_file))
                    if size >= self.max_size:
                        self._cleanup_old_patterns()

                # Create pattern entry
                pattern = {
                    "key": pattern_key,
                    "query": query.lower().strip(),
                    "filters": filters,
                    "results": results,
                    "timestamp": time.time(),
                    "ttl_seconds": ttl.total_seconds() if ttl else self.default_ttl.total_seconds(),
                    "hit_count": 0,
                    "last_accessed": time.time(),
                    "access_frequency": 1.0,
                    "created": datetime.now().isoformat()
                }

                # Append to patterns file
                with open(self.patterns_file, 'a') as f:
                    f.write(json.dumps(pattern) + '\n')

                self.logger.debug(f"L3 pattern stored: {pattern_key}")
                return True

            except Exception as e:
                self.logger.error(f"L3 set error: {e}")
                return False

    def invalidate_pattern(self, query: str, filters: dict[str, Any]) -> bool:
        """Invalidate specific pattern"""
        with self.lock:
            pattern_key = self._generate_pattern_key(query, filters)

            if not self.patterns_file.exists():
                return False

            try:
                patterns = []
                found = False
                with open(self.patterns_file) as f:
                    for line in f:
                        try:
                            pattern = json.loads(line.strip())
                            if pattern.get("key") != pattern_key:
                                patterns.append(pattern)
                            else:
                                found = True
                        except:
                            patterns.append(line)  # Preserve malformed lines

                if found:
                    with open(self.patterns_file, 'w') as f:
                        for pattern in patterns:
                            if isinstance(pattern, str):
                                f.write(pattern)
                            else:
                                f.write(json.dumps(pattern) + '\n')
                    self.logger.debug(f"L3 pattern invalidated: {pattern_key}")
                    return True

            except Exception as e:
                self.logger.error(f"L3 invalidate error: {e}")

            return False

    def get_stats(self) -> dict[str, Any]:
        """Get L3 cache statistics"""
        with self.lock:
            try:
                if not self.patterns_file.exists():
                    return {
                        "level": "L3",
                        "type": "persistent_jsonl",
                        "size": 0,
                        "max_size": self.max_size,
                        "utilization": 0.0
                    }

                # Count patterns
                total_patterns = 0
                total_hits = 0
                expired_patterns = 0
                current_time = time.time()

                with open(self.patterns_file) as f:
                    for line in f:
                        try:
                            pattern = json.loads(line.strip())
                            total_patterns += 1
                            total_hits += pattern.get("hit_count", 0)

                            timestamp = pattern.get("timestamp", 0)
                            ttl_seconds = pattern.get("ttl_seconds", self.default_ttl.total_seconds())
                            if current_time - timestamp > ttl_seconds:
                                expired_patterns += 1
                        except:
                            continue

                return {
                    "level": "L3",
                    "type": "persistent_jsonl",
                    "size": total_patterns,
                    "max_size": self.max_size,
                    "utilization": total_patterns / self.max_size,
                    "total_hits": total_hits,
                    "expired_entries": expired_patterns,
                    "patterns_file": str(self.patterns_file)
                }

            except Exception as e:
                self.logger.error(f"L3 stats error: {e}")
                return {"error": str(e)}


class MultiLevelCache:
    """Multi-level caching system combining L1, L2, and L3 caches"""

    def __init__(self, cache_dir: Path, session_id: str | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Generate session ID if not provided
        if not session_id:
            session_id = hashlib.md5(f"{datetime.now().isoformat()}{id(self)}".encode()).hexdigest()[:12]

        self.session_id = session_id
        self.logger = logging.getLogger(__name__ + ".MultiLevel")

        # Initialize cache layers
        self.l1_cache = L1MemoryCache(max_size=1000, default_ttl=timedelta(minutes=30))
        self.l2_cache = L2SessionCache(
            session_id=session_id,
            cache_dir=self.cache_dir,
            max_size=10000,
            default_ttl=timedelta(hours=6)
        )
        self.l3_cache = L3PersistentCache(
            cache_dir=self.cache_dir,
            max_size=50000,
            default_ttl=timedelta(days=7)
        )

        # Statistics
        self.stats = {
            "total_requests": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "total_misses": 0
        }

    def _generate_query_key(self, query: str, filters: dict[str, Any]) -> str:
        """Generate cache key for search query"""
        key_data = {
            "query": query.lower().strip(),
            "session_filter": filters.get("session_filter", "all"),
            "context_filter": filters.get("context_filter", "all"),
            "rank_by": filters.get("rank_by", "relevance"),
            "limit": filters.get("limit", 20)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, query: str, filters: dict[str, Any]) -> Any | None:
        """Get cached results with multi-level fallback"""
        self.stats["total_requests"] += 1
        query_key = self._generate_query_key(query, filters)

        # L1: Memory cache (fastest)
        result = self.l1_cache.get(query_key)
        if result:
            self.stats["l1_hits"] += 1
            self.logger.debug(f"Cache hit: L1 for query {query[:20]}...")
            return result

        # L2: Session cache
        result = self.l2_cache.get(query_key)
        if result:
            self.stats["l2_hits"] += 1
            # Promote to L1
            self.l1_cache.set(query_key, result)
            self.logger.debug(f"Cache hit: L2 for query {query[:20]}...")
            return result

        # L3: Persistent pattern cache
        result = self.l3_cache.get(query, filters)
        if result:
            self.stats["l3_hits"] += 1
            # Promote to higher levels
            self.l2_cache.set(query_key, result)
            self.l1_cache.set(query_key, result)
            self.logger.debug(f"Cache hit: L3 for query {query[:20]}...")
            return result

        # Cache miss
        self.stats["total_misses"] += 1
        self.logger.debug(f"Cache miss for query {query[:20]}...")
        return None

    def set(self, query: str, filters: dict[str, Any], results: Any) -> bool:
        """Cache results in all appropriate levels"""
        query_key = self._generate_query_key(query, filters)

        success = True

        # Always store in L1
        success &= self.l1_cache.set(query_key, results)

        # Store in L2 (session cache)
        success &= self.l2_cache.set(query_key, results, ttl=timedelta(hours=6))

        # Store in L3 if pattern is likely to be reused
        # Heuristic: simple queries with common filters
        if self._should_cache_persistently(query, filters):
            success &= self.l3_cache.set(query, filters, results, ttl=timedelta(days=7))

        return success

    def _should_cache_persistently(self, query: str, filters: dict[str, Any]) -> bool:
        """Determine if query should be cached persistently"""
        # Don't cache very long queries
        if len(query) > 200:
            return False

        # Don't cache queries with specific time filters
        if filters.get("session_filter") in ["today", "yesterday"]:
            return False

        # Cache queries that are likely to be repeated
        common_patterns = [
            "error", "bug", "fix", "implement", "add", "create",
            "search", "find", "help", "how to", "what is"
        ]

        query_lower = query.lower()
        return any(pattern in query_lower for pattern in common_patterns)

    def invalidate_query(self, query: str, filters: dict[str, Any]) -> bool:
        """Invalidate cached results for specific query"""
        query_key = self._generate_query_key(query, filters)

        l1_invalidated = self.l1_cache.invalidate(query_key)
        l2_invalidated = self.l2_cache.invalidate(query_key)
        l3_invalidated = self.l3_cache.invalidate_pattern(query, filters)

        return l1_invalidated or l2_invalidated or l3_invalidated

    def clear_all(self) -> dict[str, int]:
        """Clear all cache levels"""
        return {
            "L1_cleared": self.l1_cache.clear(),
            "L2_cleared": self.l2_cache.clear(),
            "L3_cleared": self.l3_cache.get_stats().get("size", 0)  # Approximate
        }

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics across all levels"""
        stats = {
            "cache_system": "MultiLevel",
            "session_id": self.session_id,
            "cache_directory": str(self.cache_dir),
            "performance_stats": self.stats.copy(),
            "hit_rates": {
                "overall": 0.0,
                "l1": 0.0,
                "l2": 0.0,
                "l3": 0.0
            },
            "levels": {
                "L1": self.l1_cache.get_stats(),
                "L2": self.l2_cache.get_stats(),
                "L3": self.l3_cache.get_stats()
            }
        }

        # Calculate hit rates
        total = self.stats["total_requests"]
        if total > 0:
            stats["hit_rates"]["overall"] = (total - self.stats["total_misses"]) / total
            stats["hit_rates"]["l1"] = self.stats["l1_hits"] / total
            stats["hit_rates"]["l2"] = self.stats["l2_hits"] / total
            stats["hit_rates"]["l3"] = self.stats["l3_hits"] / total

        return stats

    def health_check(self) -> dict[str, Any]:
        """Perform health check on all cache levels"""
        health = {
            "overall_status": "healthy",
            "issues": [],
            "recommendations": []
        }

        # Check L1
        l1_stats = self.l1_cache.get_stats()
        if l1_stats["utilization"] > 0.9:
            health["issues"].append("L1 cache near capacity")
            health["recommendations"].append("Consider increasing L1 cache size")

        # Check L2
        l2_stats = self.l2_cache.get_stats()
        if isinstance(l2_stats, dict) and l2_stats.get("expired_entries", 0) > 100:
            health["issues"].append("L2 cache has many expired entries")
            health["recommendations"].append("Run L2 cache cleanup")

        # Check L3
        l3_stats = self.l3_cache.get_stats()
        if isinstance(l3_stats, dict) and l3_stats.get("utilization", 0) > 0.8:
            health["issues"].append("L3 cache nearing capacity")
            health["recommendations"].append("Consider L3 cache pruning or size increase")

        # Overall hit rate
        overall_hit_rate = health.get("hit_rates", {}).get("overall", 0)
        if overall_hit_rate < 0.3:
            health["issues"].append("Low overall cache hit rate")
            health["recommendations"].append("Review caching strategy and TTL settings")

        if health["issues"]:
            health["overall_status"] = "degraded"

        return health
