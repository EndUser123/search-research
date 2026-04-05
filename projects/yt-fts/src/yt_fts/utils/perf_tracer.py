"""
Performance anti-pattern detection system.

Detects common performance issues at runtime:
- Nested ThreadPoolExecutors
- Duplicate resource instantiation (RSS checkers, DB connections, etc.)
- Per-worker resource creation in parallel contexts

Usage:
    from yt_fts.utils.perf_tracer import trace_performance, get_report

    with trace_performance():
        parallel_processor.process_channels(channels, num_workers=2)

    report = get_report()
    print(report)
"""

from __future__ import annotations
import contextlib
import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metric:
    """A single metric measurement."""
    count: int = 0
    thread_ids: set[int | None] = field(default_factory=set)
    depth_stack: list[int] = field(default_factory=list)
    first_call_stack: str | None = None


class _PerformanceTracer:
    """Global performance tracer singleton."""

    def __init__(self) -> None:
        self._enabled: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._metrics: dict[str, Metric] = defaultdict(Metric)
        self._threadpool_depth: dict[int, int] = defaultdict(int)
        self._original_threadpool_init: Any = None
        self._original_rss_init: Any = None
        self._original_quota_init: Any = None
        self._original_db_connect: Any = None

    def enable(self) -> None:
        """Enable performance tracing."""
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            self._install_hooks()

    def disable(self) -> dict[str, Any] | None:
        """Disable performance tracing and return report."""
        with self._lock:
            if not self._enabled:
                return self._get_report()
            self._enabled = False
            report = self._get_report()
            self._reset()
            return report

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._reset()

    def _reset(self) -> None:
        """Internal reset without lock."""
        self._metrics.clear()
        self._threadpool_depth.clear()

    def _install_hooks(self) -> None:
        """Install tracing hooks on key classes."""
        from concurrent.futures import ThreadPoolExecutor

        # Wrap ThreadPoolExecutor.__init__
        original_init = ThreadPoolExecutor.__init__

        def traced_init(obj: Any, *args: Any, **kwargs: Any) -> None:
            thread_id = threading.current_thread().ident
            if thread_id is not None:
                self._threadpool_depth[thread_id] += 1
                depth = self._threadpool_depth[thread_id]
            else:
                depth = 0

            # Track nested threadpool creation
            key = "ThreadPoolExecutor.__init__"
            self._track_metric(key, depth=depth)

            if depth > 1:
                # Record the stack trace of where nesting occurred
                import traceback
                stack = "".join(traceback.format_stack())
                if not self._metrics[key].first_call_stack:
                    self._metrics[key].first_call_stack = f"Nested ThreadPoolExecutor detected (depth={depth}):\n{stack}"

            return original_init(obj, *args, **kwargs)

            # Note: We can't decrement in __exit__ because we're wrapping __init__
            # Instead, we track max depth seen

        ThreadPoolExecutor.__init__ = traced_init  # type: ignore[method-assign,assignment]
        self._original_threadpool_init = original_init

        # Try to wrap RSS checker creation
        try:
            from yt_fts.services.rss_precheck import create_rss_checker

            original_rss = create_rss_checker

            def traced_rss(*args: Any, **kwargs: Any) -> Any:
                self._track_metric("create_rss_checker")
                return original_rss(*args, **kwargs)

            import yt_fts.services.rss_precheck as rss_module
            rss_module.create_rss_checker = traced_rss
            self._original_rss_init = original_rss
        except ImportError:
            pass

        # Try to wrap DB connection
        try:
            from yt_fts.core.database import get_db_connection

            original_db = get_db_connection

            def traced_db(*args: Any, **kwargs: Any) -> Any:
                self._track_metric("get_db_connection")
                return original_db(*args, **kwargs)

            import yt_fts.core.database as db_module
            db_module.get_db_connection = traced_db
            self._original_db_connect = original_db
        except ImportError:
            pass

    def _track_metric(self, key: str, depth: int = 0) -> None:
        """Track a metric occurrence."""
        if not self._enabled:
            return

        thread_id = threading.current_thread().ident
        metric = self._metrics[key]

        with self._lock:
            metric.count += 1
            metric.thread_ids.add(thread_id)

            if depth > 0:
                metric.depth_stack.append(depth)

    def _get_report(self) -> dict[str, Any]:
        """Generate a performance report."""
        with self._lock:
            return {
                "ThreadPoolExecutor.__init__": {
                    "count": self._metrics["ThreadPoolExecutor.__init__"].count,
                    "max_depth": max(self._metrics["ThreadPoolExecutor.__init__"].depth_stack, default=0),
                    "threads": len(self._metrics["ThreadPoolExecutor.__init__"].thread_ids),
                    "nested_stack": self._metrics["ThreadPoolExecutor.__init__"].first_call_stack,
                },
                "create_rss_checker": {
                    "count": self._metrics["create_rss_checker"].count,
                    "threads": len(self._metrics["create_rss_checker"].thread_ids),
                },
                "get_db_connection": {
                    "count": self._metrics["get_db_connection"].count,
                    "threads": len(self._metrics["get_db_connection"].thread_ids),
                },
            }

    def _restore_hooks(self) -> None:
        """Restore original functions."""
        if self._original_threadpool_init:
            from concurrent.futures import ThreadPoolExecutor
            ThreadPoolExecutor.__init__ = self._original_threadpool_init  # type: ignore[method-assign]

        if self._original_rss_init:
            import yt_fts.services.rss_precheck as rss_module
            rss_module.create_rss_checker = self._original_rss_init

        if self._original_db_connect:
            import yt_fts.core.database as db_module
            db_module.get_db_connection = self._original_db_connect


_global_tracer = _PerformanceTracer()


@contextlib.contextmanager
def trace_performance() -> Any:
    """Context manager for performance tracing.

    Example:
        with trace_performance():
            processor.process_channels(channels, num_workers=2)

        report = get_report()
        print(format_report(report))
    """
    _global_tracer.enable()
    try:
        yield
    finally:
        _global_tracer.disable()
        _global_tracer._restore_hooks()


def get_report() -> dict[str, Any]:
    """Get the current performance report without disabling tracing.

    Returns:
        dict with keys: ThreadPoolExecutor, create_rss_checker, get_db_connection
    """
    return _global_tracer._get_report()


def format_report(report: dict[str, Any]) -> str:
    """Format a performance report for human reading.

    Args:
        report: Report dict from get_report()

    Returns:
        Formatted string report
    """
    lines = ["\n🔍 Performance Anti-Pattern Report", "=" * 50]

    # ThreadPoolExecutor analysis
    tp = report["ThreadPoolExecutor.__init__"]
    if tp["count"] > 0:
        lines.append("\n📊 ThreadPoolExecutor:")
        lines.append(f"   Instances created: {tp['count']}")
        lines.append(f"   Max nesting depth: {tp['max_depth']}")

        if tp["max_depth"] > 1:
            lines.append("   ⚠️  WARNING: Nested ThreadPoolExecutor detected!")
            lines.append("       This indicates parallel tasks are creating their own thread pools.")
            lines.append("       Consider flattening the architecture.")

        if tp["threads"] > 1:
            lines.append(f"   ℹ️  Created from {tp['threads']} different threads")

        if tp["nested_stack"]:
            lines.append("\n   Stack trace of nesting:")
            for line in tp["nested_stack"].split("\n")[:20]:  # Limit output
                lines.append(f"   {line}")

    # RSS checker analysis
    rss = report["create_rss_checker"]
    if rss["count"] > 0:
        lines.append("\n📡 RSS Checkers:")
        lines.append(f"   Instances created: {rss['count']}")

        if rss["count"] > 1:
            lines.append("   ⚠️  WARNING: Multiple RSS checkers created!")
            lines.append("       Consider sharing a single RSS checker instance.")

    # DB connection analysis
    db = report["get_db_connection"]
    if db["count"] > 0:
        lines.append("\n💾 DB Connections:")
        lines.append(f"   Connections opened: {db['count']}")

        if db["count"] > 5:
            lines.append("   ⚠️  WARNING: Many DB connections opened!")
            lines.append("       Consider connection pooling or reuse.")

    lines.append("=" * 50)
    return "\n".join(lines)


def analyze_architecture(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
    """Analyze a function's performance characteristics.

    Args:
        func: Function to analyze
        *args, **kwargs: Arguments to pass to func

    Returns:
        tuple of (result, report)
    """
    with trace_performance():
        result = func(*args, **kwargs)
    report = get_report()
    return result, report


# Convenience function for quick analysis
def quick_check(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run a function and print performance report.

    Args:
        func: Function to check
        *args, **kwargs: Arguments to pass to func

    Returns:
        Function result
    """
    result, report = analyze_architecture(func, *args, **kwargs)
    print(format_report(report))

    # Print recommendations
    if report["ThreadPoolExecutor.__init__"]["max_depth"] > 1:
        print("\n💡 RECOMMENDATION: Flatten nested ThreadPoolExecutor structure")
        print("   Create ONE shared thread pool and distribute work via queue.")

    if report["create_rss_checker"]["count"] > 1:
        print("\n💡 RECOMMENDATION: Share RSS checker across workers")
        print("   Create RSS checker once and pass to worker functions.")

    if report["get_db_connection"]["count"] > 5:
        print("\n💡 RECOMMENDATION: Use thread-local DB connection pooling")
        print("   Each worker thread should use its own persistent connection.")

    return result


if __name__ == "__main__":
    # Demo / test
    from concurrent.futures import ThreadPoolExecutor

    def demo_nested() -> list[list[int]]:
        """Demo that creates nested thread pools."""
        def inner() -> list[int]:
            with ThreadPoolExecutor(max_workers=2) as executor:
                return list(executor.map(lambda x: x * 2, [1, 2]))

        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(lambda x: inner(), [1, 2]))

    print("Running demo with nested ThreadPoolExecutor...")
    quick_check(demo_nested)
