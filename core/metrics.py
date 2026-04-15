"""MetricsLogger - async metrics collection for search-research pipeline."""

import json
import queue
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path


class ComponentName(str, Enum):
    QMD_WIKI = "QMD_WIKI"
    YT_IS = "YT_IS"
    CLAUDE_HISTORY = "CLAUDE_HISTORY"
    HYDE = "HYDE"
    SEARCH_PROVIDER = "SEARCH_PROVIDER"
    SYNTHESIS = "SYNTHESIS"
    CONTRADICTION = "CONTRADICTION"
    COVERAGE_GATE = "COVERAGE_GATE"
    CRAG_GRADE = "CRAG_GRADE"


@dataclass
class ComponentMetric:
    timestamp: str
    component: ComponentName
    latency_ms: float
    tokens_used: int
    cache_hit: bool
    output_quality: float
    branch: str = "main"

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self))


class MetricsLogger:
    def __init__(
        self,
        log_path: str = "logs/metrics.jsonl",
        max_size_mb: float = 10,
        queue_size: int = 1000,
    ):
        self._log_path = Path(log_path)
        self._max_size_bytes = max_size_mb * 1_000_000
        self._queue: queue.Queue[ComponentMetric | None] = queue.Queue(maxsize=queue_size)

        # Create log dir if missing
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        # Start daemon writer thread
        self._writer_thread = threading.Thread(
            target=self._background_writer,
            daemon=True,
        )
        self._writer_thread.start()

    def _maybe_rotate(self) -> None:
        if self._log_path.exists():
            size = self._log_path.stat().st_size
            if size >= self._max_size_bytes:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_path = self._log_path.parent / f"{self._log_path.name}.{stamp}"
                try:
                    self._log_path.rename(rotated_path)
                except FileExistsError:
                    rotated_path.unlink()
                    self._log_path.rename(rotated_path)

    def _background_writer(self) -> None:
        while True:
            metric = self._queue.get()
            if metric is None:
                break
            self._maybe_rotate()
            try:
                with open(self._log_path, "a") as f:
                    f.write(metric.to_jsonl() + "\n")
            except OSError:
                pass

    def log(self, metric: ComponentMetric) -> None:
        try:
            self._queue.put_nowait(metric)
        except queue.Full:
            pass

    def log_component(
        self,
        component: ComponentName,
        latency_ms: float,
        tokens_used: int = 0,
        quality: float = 0.0,
        cache_hit: bool = False,
        branch: str = "main",
    ) -> None:
        metric = ComponentMetric(
            timestamp=datetime.now().isoformat(),
            component=component,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            cache_hit=cache_hit,
            output_quality=quality,
            branch=branch,
        )
        self.log(metric)

    def flush(self) -> None:
        self._queue.put(None)
        self._writer_thread.join(timeout=2.0)