"""
Meta-Router base class for unified routing patterns.

This module provides a reusable base class for routing requests to multiple
providers/backends with health tracking, parallel execution, result deduplication,
and caching support.
"""

from __future__ import annotations

import asyncio
import hashlib
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RoutingStrategy(Enum):
    FIRST_SUCCESS = "first_success"
    ALL_PARALLEL = "all_parallel"
    ALL_SEQUENTIAL = "all_sequential"
    FALLBACK = "fallback"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
@dataclass
class ProviderConfig:
    name: str
    enabled: bool = True
    priority: int = 0
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    weight: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    provider_name: str
    success: bool
    data: Any | None = None
    error: str | None = None
    duration_ms: float = 0.0
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
@dataclass
class RouterMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_duration_ms: float = 0.0
    provider_calls: dict[str, int] = field(default_factory=dict)
    provider_failures: dict[str, int] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_success(self, provider: str, duration_ms: float) -> None:
        with self._lock:
            self.total_requests += 1
            self.successful_requests += 1
            self.total_duration_ms += duration_ms
            self.provider_calls[provider] = self.provider_calls.get(provider, 0) + 1

    def record_failure(self, provider: str, duration_ms: float) -> None:
        with self._lock:
            self.total_requests += 1
            self.failed_requests += 1
            self.total_duration_ms += duration_ms
            self.provider_calls[provider] = self.provider_calls.get(provider, 0) + 1
            self.provider_failures[provider] = self.provider_failures.get(provider, 0) + 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self.total_requests += 1
            self.cached_requests += 1

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            avg = self.total_duration_ms / self.total_requests if self.total_requests else 0
            return {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "cached_requests": self.cached_requests,
                "avg_duration_ms": avg,
                "provider_calls": dict(self.provider_calls),
                "provider_failures": dict(self.provider_failures),
            }
class MetaRouter(ABC):
    """Base class for routing requests to multiple providers.

    Features: provider registration, health tracking, parallel execution,
    result deduplication, caching with TTL, metrics collection.
    Thread-safe for concurrent use.
    """

    def __init__(
        self,
        providers: list[ProviderConfig] | None = None,
        strategy: RoutingStrategy = RoutingStrategy.FIRST_SUCCESS,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 300,
        enable_deduplication: bool = True,
        max_parallel_workers: int = 5,
    ) -> None:
        self._providers: dict[str, ProviderConfig] = {}
        self._strategy = strategy
        self._enable_cache = enable_cache
        self._cache_ttl_seconds = cache_ttl_seconds
        self._enable_deduplication = enable_deduplication
        self._max_parallel_workers = max_parallel_workers
        self._health: dict[str, tuple[HealthStatus, int, float]] = {}
        self._health_lock = threading.Lock()
        self._cache: dict[str, tuple[float, ProviderResult]] = {}
        self._cache_lock = threading.Lock()
        self._metrics = RouterMetrics()

        if providers:
            for p in providers:
                self.register_provider(p)

    def register_provider(self, provider: ProviderConfig) -> None:
        with self._health_lock:
            if provider.name in self._providers:
                msg = f"Provider '{provider.name}' already registered"
                raise ValueError(msg)
            self._providers[provider.name] = provider
            self._health[provider.name] = (HealthStatus.UNKNOWN, 0, time.time())

    def unregister_provider(self, name: str) -> None:
        with self._health_lock:
            self._providers.pop(name, None)
            self._health.pop(name, None)

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    def list_providers(self, enabled_only: bool = False) -> list[str]:
        if enabled_only:
            return [p.name for p in self._providers.values() if p.enabled]
        return list(self._providers.keys())

    def get_health_status(self, provider: str) -> HealthStatus:
        with self._health_lock:
            status, _, _ = self._health.get(provider, (HealthStatus.UNKNOWN, 0, 0))
            return status

    def set_health_status(self, provider: str, status: HealthStatus, count: int = 0) -> None:
        with self._health_lock:
            self._health[provider] = (status, count, time.time())

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics.get_stats()

    def reset_metrics(self) -> None:
        self._metrics = RouterMetrics()

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()
    def route(
        self,
        input_data: Any,
        providers: list[str] | None = None,
        strategy: RoutingStrategy | None = None,
    ) -> ProviderResult:
        start = time.time()
        strat = strategy or self._strategy

        if self._enable_cache:
            key = self._get_cache_key(input_data, providers, strat)
            cached = self._get_from_cache(key)
            if cached:
                self._metrics.record_cache_hit()
                cached.cached = True
                return cached

        targets = self._select_providers(providers)
        if not targets:
            return ProviderResult("none", False, None, "No providers", (time.time() - start) * 1000)

        if strat == RoutingStrategy.FIRST_SUCCESS:
            result = self._route_first(input_data, targets)
        elif strat == RoutingStrategy.ALL_PARALLEL:
            result = self._route_parallel(input_data, targets)
        elif strat == RoutingStrategy.ALL_SEQUENTIAL:
            result = self._route_sequential(input_data, targets)
        elif strat == RoutingStrategy.FALLBACK:
            result = self._route_fallback(input_data, targets)
        else:
            result = ProviderResult("router", False, None, f"Unknown strategy: {strat}", 0)

        if self._enable_cache and result.success:
            self._add_to_cache(self._get_cache_key(input_data, providers, strat), result)
        return result
    def _select_providers(self, names: list[str] | None) -> list[ProviderConfig]:
        if names:
            return [p for n in names if (p := self._providers.get(n))]
        result = []
        with self._health_lock:
            for name, p in self._providers.items():
                if not p.enabled:
                    continue
                status, _, _ = self._health.get(name, (HealthStatus.UNKNOWN, 0, 0))
                if status != HealthStatus.UNHEALTHY:
                    result.append(p)
        result.sort(key=lambda x: x.priority)
        return result
    def _route_first(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        lock = threading.Lock()
        results = []

        def exec_one(p: ProviderConfig) -> ProviderResult:
            r = self._execute_with_retry(p, data)
            with lock:
                results.append(r)
            return r

        with ThreadPoolExecutor(max_workers=self._max_parallel_workers) as exe:
            futures = {exe.submit(exec_one, p): p for p in providers}
            for fut in as_completed(futures):
                r = fut.result()
                if r.success:
                    for f in futures:
                        f.cancel()
                    return r
        return results[0] if results else ProviderResult("router", False, None, "No results", 0)

    def _route_parallel(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        all_data, errors, max_dur = [], [], 0.0
        with ThreadPoolExecutor(max_workers=self._max_parallel_workers) as exe:
            futures = {exe.submit(self._execute_with_retry, p, data): p for p in providers}
            for fut in as_completed(futures):
                r = fut.result()
                max_dur = max(max_dur, r.duration_ms)
                if r.success:
                    all_data.append(r.data)
                else:
                    errors.append(f"{r.provider_name}: {r.error}")
        if not all_data:
            return ProviderResult("merged", False, None, f"All failed: {'; '.join(errors)}", max_dur)
        merged = self._merge_results(all_data) if self._enable_deduplication else all_data
        return ProviderResult("merged", True, merged, None, max_dur)

    def _route_sequential(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        all_data, errors, total = [], [], 0.0
        for p in providers:
            r = self._execute_with_retry(p, data)
            total += r.duration_ms
            if r.success:
                all_data.append(r.data)
            else:
                errors.append(f"{p.name}: {r.error}")
        if not all_data:
            return ProviderResult("merged", False, None, f"All failed: {'; '.join(errors)}", total)
        merged = self._merge_results(all_data) if self._enable_deduplication else all_data
        return ProviderResult("merged", True, merged, None, total)

    def _route_fallback(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        total, last_err = 0.0, None
        for p in providers:
            r = self._execute_with_retry(p, data)
            total += r.duration_ms
            if r.success:
                r.duration_ms = total
                return r
            last_err = r.error
        return ProviderResult("router", False, None, f"All failed, last: {last_err}", total)
    def _execute_with_retry(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        start = time.time()
        last_err = None
        for attempt in range(provider.max_retries + 1):
            if attempt > 0:
                time.sleep(provider.retry_delay_seconds)
            try:
                r = self._execute_provider(provider, data)
                dur = (time.time() - start) * 1000
                if r.success:
                    self._update_health_success(provider.name)
                    self._metrics.record_success(provider.name, dur)
                    r.provider_name = provider.name
                    r.duration_ms = dur
                    return r
                last_err = r.error
            except Exception as e:
                last_err = str(e)
        self._update_health_failure(provider.name)
        self._metrics.record_failure(provider.name, (time.time() - start) * 1000)
        return ProviderResult(provider.name, False, None, last_err, (time.time() - start) * 1000)

    def _update_health_success(self, name: str) -> None:
        with self._health_lock:
            status, _, _ = self._health.get(name, (HealthStatus.UNKNOWN, 0, 0))
            self._health[name] = (HealthStatus.HEALTHY if status != HealthStatus.DEGRADED else status, 0, time.time())

    def _update_health_failure(self, name: str) -> None:
        with self._health_lock:
            status, fails, _ = self._health.get(name, (HealthStatus.UNKNOWN, 0, 0))
            nf = fails + 1
            ns = HealthStatus.UNHEALTHY if nf >= 3 else HealthStatus.DEGRADED if nf >= 1 else status
            self._health[name] = (ns, nf, time.time())
    def _get_from_cache(self, key: str) -> ProviderResult | None:
        with self._cache_lock:
            if key in self._cache:
                ts, r = self._cache[key]
                if time.time() - ts < self._cache_ttl_seconds:
                    return r
                del self._cache[key]
        return None

    def _add_to_cache(self, key: str, result: ProviderResult) -> None:
        with self._cache_lock:
            self._cache[key] = (time.time(), result)

    def _get_cache_key(self, data: Any, providers: list[str] | None, strategy: RoutingStrategy) -> str:
        parts = [str(hash(data)), str(sorted(providers or [])), strategy.value]
        return hashlib.md5("|".join(parts).encode(), usedforsecurity=False).hexdigest()
    @abstractmethod
    def _execute_provider(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        raise NotImplementedError

    def _merge_results(self, results: list[Any]) -> Any:
        return results

    def _should_deduplicate(self, item1: Any, item2: Any) -> bool:
        return item1 == item2

class AsyncMetaRouter(MetaRouter):
    """Async variant using asyncio instead of ThreadPoolExecutor."""

    async def route_async(
        self,
        input_data: Any,
        providers: list[str] | None = None,
        strategy: RoutingStrategy | None = None,
    ) -> ProviderResult:
        start = time.time()
        strat = strategy or self._strategy

        if self._enable_cache:
            key = self._get_cache_key(input_data, providers, strat)
            cached = self._get_from_cache(key)
            if cached:
                self._metrics.record_cache_hit()
                cached.cached = True
                return cached

        targets = self._select_providers(providers)
        if not targets:
            return ProviderResult("none", False, None, "No providers", (time.time() - start) * 1000)

        if strat == RoutingStrategy.FIRST_SUCCESS:
            result = await self._route_first_async(input_data, targets)
        elif strat == RoutingStrategy.ALL_PARALLEL:
            result = await self._route_parallel_async(input_data, targets)
        elif strat == RoutingStrategy.ALL_SEQUENTIAL:
            result = await self._route_sequential_async(input_data, targets)
        elif strat == RoutingStrategy.FALLBACK:
            result = await self._route_fallback_async(input_data, targets)
        else:
            result = ProviderResult("router", False, None, f"Unknown strategy: {strat}", 0)

        if self._enable_cache and result.success:
            self._add_to_cache(self._get_cache_key(input_data, providers, strat), result)
        return result
    async def _route_first_async(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        tasks = [asyncio.create_task(self._exec_retry_async(p, data)) for p in providers]
        for task in asyncio.as_completed(tasks):
            r = await task
            if r.success:
                for t in tasks:
                    t.cancel()
                return r
        return ProviderResult("router", False, None, "All failed", 0)

    async def _route_parallel_async(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        tasks = [asyncio.create_task(self._exec_retry_async(p, data)) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_data, errors, max_dur = [], [], 0.0
        for r in results:
            if isinstance(r, Exception):
                errors.append(str(r))
                continue
            if r.success:
                all_data.append(r.data)
                max_dur = max(max_dur, r.duration_ms)
            else:
                errors.append(f"{r.provider_name}: {r.error}")
        if not all_data:
            return ProviderResult("merged", False, None, f"All failed: {'; '.join(errors)}", max_dur)
        merged = self._merge_results(all_data) if self._enable_deduplication else all_data
        return ProviderResult("merged", True, merged, None, max_dur)

    async def _route_sequential_async(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        all_data, errors, total = [], [], 0.0
        for p in providers:
            r = await self._exec_retry_async(p, data)
            total += r.duration_ms
            if r.success:
                all_data.append(r.data)
            else:
                errors.append(f"{p.name}: {r.error}")
        if not all_data:
            return ProviderResult("merged", False, None, f"All failed: {'; '.join(errors)}", total)
        merged = self._merge_results(all_data) if self._enable_deduplication else all_data
        return ProviderResult("merged", True, merged, None, total)

    async def _route_fallback_async(self, data: Any, providers: list[ProviderConfig]) -> ProviderResult:
        total, last_err = 0.0, None
        for p in providers:
            r = await self._exec_retry_async(p, data)
            total += r.duration_ms
            if r.success:
                r.duration_ms = total
                return r
            last_err = r.error
        return ProviderResult("router", False, None, f"All failed, last: {last_err}", total)
    async def _exec_retry_async(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        start = time.time()
        last_err = None
        for attempt in range(provider.max_retries + 1):
            if attempt > 0:
                await asyncio.sleep(provider.retry_delay_seconds)
            try:
                r = await self._execute_provider_async(provider, data)
                dur = (time.time() - start) * 1000
                if r.success:
                    self._update_health_success(provider.name)
                    self._metrics.record_success(provider.name, dur)
                    r.provider_name = provider.name
                    r.duration_ms = dur
                    return r
                last_err = r.error
            except Exception as e:
                last_err = str(e)
        self._update_health_failure(provider.name)
        self._metrics.record_failure(provider.name, (time.time() - start) * 1000)
        return ProviderResult(provider.name, False, None, last_err, (time.time() - start) * 1000)

    @abstractmethod
    async def _execute_provider_async(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        raise NotImplementedError
