from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

#!/usr/bin/env python3
"""GPU Performance Monitor for Chat History Search.

CSF NIP Comprehensive GPU performance monitoring and metrics tracking system.
Provides real-time GPU performance monitoring, alerting, and historical analysis
for Chat History Search GPU acceleration.

Algorithm Approach: Real-time GPU monitoring with configurable thresholds,
historical data collection, and intelligent alerting system.

Performance Features:
- Real-time GPU monitoring (memory, utilization, temperature)
- Historical performance data collection and analysis
- Configurable alerting and threshold management
- Performance trend analysis and prediction
- Resource usage optimization recommendations
- Integration with CHS GPU accelerator

Monitoring Capabilities:
- GPU memory usage and allocation tracking
- GPU utilization and workload monitoring
- Temperature and thermal management
- Power consumption monitoring
- Performance bottleneck identification
- SLA compliance tracking

Dependencies:
- nvidia-ml-py for detailed GPU monitoring
- psutil for system resource monitoring
- asyncio for real-time monitoring
- Custom GPU accelerator integration

"""




if TYPE_CHECKING:
    from .gpu_chs_accelerator import CHSGPUAccelerator, CHSProcessingResult

# GPU and system monitoring imports
try:
    import pynvml

    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

# Import CHS components
try:
    CHS_ACCELERATOR_AVAILABLE = True
except ImportError:
    CHS_ACCELERATOR_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Enumeration of alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Enumeration of metric types."""

    MEMORY_USAGE = "memory_usage"
    GPU_UTILIZATION = "gpu_utilization"
    TEMPERATURE = "temperature"
    POWER_USAGE = "power_usage"
    PROCESSING_THROUGHPUT = "processing_throughput"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    CACHE_HIT_RATE = "cache_hit_rate"


@dataclass
class GPUMetricSnapshot:
    """Single GPU metric snapshot at a point in time.

    Attributes
    ----------
        timestamp (datetime): When the snapshot was taken
        gpu_id (int): GPU device ID
        memory_used_mb (float): Memory used in MB
        memory_total_mb (float): Total memory in MB
        memory_utilization (float): Memory utilization percentage (0-100)
        gpu_utilization (float): GPU utilization percentage (0-100)
        temperature_celsius (float): GPU temperature in Celsius
        power_usage_watts (float): Power usage in watts
        clock_frequency_mhz (float): GPU clock frequency in MHz
        memory_clock_frequency_mhz (float): Memory clock frequency in MHz
        active_processes (int): Number of active processes using GPU
        performance_state (str): GPU performance state
        processing_throughput (Optional[float]): Current processing throughput
        error_rate (Optional[float]): Current error rate
        latency_ms (Optional[float]): Current processing latency
        cache_hit_rate (Optional[float]): Current cache hit rate

    """

    timestamp: datetime
    gpu_id: int
    memory_used_mb: float
    memory_total_mb: float
    memory_utilization: float
    gpu_utilization: float
    temperature_celsius: float
    power_usage_watts: float
    clock_frequency_mhz: float
    memory_clock_frequency_mhz: float
    active_processes: int
    performance_state: str
    processing_throughput: float | None = None
    error_rate: float | None = None
    latency_ms: float | None = None
    cache_hit_rate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "gpu_id": self.gpu_id,
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self.memory_total_mb,
            "memory_utilization": self.memory_utilization,
            "gpu_utilization": self.gpu_utilization,
            "temperature_celsius": self.temperature_celsius,
            "power_usage_watts": self.power_usage_watts,
            "clock_frequency_mhz": self.clock_frequency_mhz,
            "memory_clock_frequency_mhz": self.memory_clock_frequency_mhz,
            "active_processes": self.active_processes,
            "performance_state": self.performance_state,
            "processing_throughput": self.processing_throughput,
            "error_rate": self.error_rate,
            "latency_ms": self.latency_ms,
            "cache_hit_rate": self.cache_hit_rate,
        }


@dataclass
class PerformanceAlert:
    """Performance alert definition.

    Attributes
    ----------
        id (str): Unique alert identifier
        severity (AlertSeverity): Alert severity level
        metric_type (MetricType): Type of metric that triggered alert
        gpu_id (int): GPU device ID
        message (str): Alert message
        current_value (float): Current metric value
        threshold (float): Threshold that was exceeded
        timestamp (datetime): When alert was triggered
        resolved (bool): Whether alert has been resolved
        resolved_timestamp (Optional[datetime]): When alert was resolved
        acknowledged (bool): Whether alert has been acknowledged
        acknowledged_by (Optional[str]): Who acknowledged the alert

    """

    id: str
    severity: AlertSeverity
    metric_type: MetricType
    gpu_id: int
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: datetime | None = None
    acknowledged: bool = False
    acknowledged_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary for serialization."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "metric_type": self.metric_type.value,
            "gpu_id": self.gpu_id,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_timestamp": (
                self.resolved_timestamp.isoformat() if self.resolved_timestamp else None
            ),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
        }


@dataclass
class MonitoringConfig:
    """Configuration for GPU performance monitoring.

    Attributes
    ----------
        gpu_ids (List[int]): List of GPU device IDs to monitor
        monitoring_interval_seconds (int): Interval between metric collections
        history_retention_hours (int): Hours to retain historical data
        alert_cooldown_minutes (int): Minimum time between same alert type
        enable_alerts (bool): Enable alert generation
        enable_prediction (bool): Enable performance prediction
        log_file_path (Optional[str]): Path to log file
        metrics_file_path (Optional[str]): Path to metrics storage file
        alerts_file_path (Optional[str]): Path to alerts storage file
        thresholds (Dict[str, float]): Alert thresholds for various metrics
        enable_system_monitoring (bool): Enable system-wide monitoring
        enable_chs_integration (bool): Enable CHS accelerator integration

    """

    gpu_ids: list[int] = field(default_factory=lambda: [0])
    monitoring_interval_seconds: int = 5
    history_retention_hours: int = 24
    alert_cooldown_minutes: int = 5
    enable_alerts: bool = True
    enable_prediction: bool = True
    log_file_path: str | None = None
    metrics_file_path: str | None = None
    alerts_file_path: str | None = None
    thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "memory_usage_warning": 80.0,
            "memory_usage_critical": 90.0,
            "gpu_utilization_warning": 85.0,
            "temperature_warning": 75.0,
            "temperature_critical": 85.0,
            "power_usage_warning": 250.0,
            "error_rate_warning": 5.0,
            "error_rate_critical": 10.0,
            "latency_warning": 1000.0,  # ms
            "latency_critical": 2000.0,  # ms
            "cache_hit_rate_warning": 50.0,  # %
        },
    )
    enable_system_monitoring: bool = True
    enable_chs_integration: bool = True


class GPUPerformanceMonitor:
    """Comprehensive GPU performance monitoring system.

    Algorithm Approach: Real-time monitoring with configurable thresholds,
    historical data collection, and intelligent alerting for proactive
    performance management.

    Key Features:
    - Real-time GPU metric collection
    - Historical performance analysis
    - Configurable alerting system
    - Performance trend prediction
    - Resource optimization recommendations
    - CHS accelerator integration

    Example:
    -------
        >>> monitor = GPUPerformanceMonitor()
        >>> await monitor.start_monitoring()
        >>> metrics = monitor.get_current_metrics()
        >>> await monitor.stop_monitoring()

    """

    def __init__(
        self,
        config: MonitoringConfig | None = None,
        chs_accelerator: CHSGPUAccelerator | None = None,
    ) -> None:
        """Initialize GPU performance monitor with configuration.

        Parameters
        ----------
        config: Monitoring configuration parameters
        chs_accelerator: Optional CHS GPU accelerator for integration

        Raises
        ------
        ImportError: If required monitoring libraries are not available
        RuntimeError: If GPU monitoring initialization fails

        """
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # GPU monitoring setup
        self.gpu_available = False
        self.gpu_handles = {}
        self.gpu_count = 0

        # CHS accelerator integration
        self.chs_accelerator = chs_accelerator

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        self.alert_handlers: list[Callable] = []

        # Data storage
        self.metrics_history: dict[int, deque] = {}
        self.active_alerts: dict[str, PerformanceAlert] = {}
        self.alert_history: list[PerformanceAlert] = []
        self.last_alert_times: dict[str, datetime] = {}

        # Performance statistics
        self.processing_results: list[CHSProcessingResult] = []
        self.performance_stats = {
            "total_processing_time": 0.0,
            "total_items_processed": 0,
            "total_errors": 0,
            "average_throughput": 0.0,
            "average_latency": 0.0,
            "cache_hit_rate": 0.0,
        }

        # Initialize GPU monitoring
        self._initialize_gpu_monitoring()

        # Initialize CHS integration
        if self.config.enable_chs_integration and CHS_ACCELERATOR_AVAILABLE:
            self._initialize_chs_integration()

        self.logger.info(
            f"GPUPerformanceMonitor initialized - GPU available: {self.gpu_available}"
        )

    def _initialize_gpu_monitoring(self) -> None:
        """Initialize GPU monitoring capabilities."""
        try:
            if not PYNVML_AVAILABLE:
                self.logger.warning("pynvml not available - limited GPU monitoring")
                return

            # Initialize NVML
            pynvml.nvmlInit()

            # Get GPU count
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            self.gpu_available = self.gpu_count > 0

            if not self.gpu_available:
                self.logger.warning("No GPUs found for monitoring")
                return

            # Initialize handles for specified GPUs
            for gpu_id in self.config.gpu_ids:
                if gpu_id < self.gpu_count:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
                    self.gpu_handles[gpu_id] = handle
                    self.metrics_history[gpu_id] = deque(
                        maxlen=self._get_history_size()
                    )

            self.logger.info(
                f"GPU monitoring initialized for {len(self.gpu_handles)} GPUs"
            )

        except Exception as e:
            self.logger.exception(f"GPU monitoring initialization failed: {e}")
            self.gpu_available = False

    def _initialize_chs_integration(self) -> None:
        """Initialize CHS accelerator integration."""
        try:
            if self.chs_accelerator:
                # Add processing result handler
                self.chs_accelerator.processing_history = self.processing_results
                self.logger.info("CHS accelerator integration initialized")
            else:
                self.logger.info(
                    "No CHS accelerator provided - monitoring limited to hardware metrics"
                )

        except Exception as e:
            self.logger.exception(f"CHS integration initialization failed: {e}")

    def _get_history_size(self) -> int:
        """Calculate history size based on retention period."""
        interval_seconds = self.config.monitoring_interval_seconds
        retention_hours = self.config.history_retention_hours
        return int((retention_hours * 3600) / interval_seconds)

    async def start_monitoring(self) -> None:
        """Start continuous GPU performance monitoring."""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        if not self.gpu_available:
            self.logger.warning("No GPUs available - cannot start monitoring")
            return

        try:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("GPU performance monitoring started")

        except Exception as e:
            self.logger.exception(f"Failed to start monitoring: {e}")
            self.monitoring_active = False
            raise

    async def stop_monitoring(self) -> None:
        """Stop continuous GPU performance monitoring."""
        if not self.monitoring_active:
            self.logger.warning("Monitoring not active")
            return

        try:
            self.monitoring_active = False

            if self.monitoring_task:
                self.monitoring_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.monitoring_task
                self.monitoring_task = None

            # Save final data
            await self._save_metrics()
            await self._save_alerts()

            self.logger.info("GPU performance monitoring stopped")

        except Exception as e:
            self.logger.exception(f"Error stopping monitoring: {e}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for collecting GPU metrics."""
        while self.monitoring_active:
            try:
                # Collect metrics for all monitored GPUs
                for gpu_id in self.config.gpu_ids:
                    if gpu_id in self.gpu_handles:
                        snapshot = await self._collect_gpu_metrics(gpu_id)
                        if snapshot:
                            self.metrics_history[gpu_id].append(snapshot)
                            await self._process_snapshot(snapshot)

                # Process CHS accelerator data
                if self.config.enable_chs_integration and self.chs_accelerator:
                    await self._process_chs_data()

                # Clean up old data
                await self._cleanup_old_data()

                # Sleep until next collection
                await asyncio.sleep(self.config.monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config.monitoring_interval_seconds)

    async def _collect_gpu_metrics(self, gpu_id: int) -> GPUMetricSnapshot | None:
        """Collect current GPU metrics for specified device."""
        try:
            if gpu_id not in self.gpu_handles:
                return None

            handle = self.gpu_handles[gpu_id]

            # Collect basic GPU metrics
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )
            power_usage = (
                pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            )  # Convert to watts

            # Collect clock frequencies
            try:
                clock_freq = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_GRAPHICS
                )
                memory_clock_freq = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_MEM
                )
            except Exception:
                clock_freq = 0.0
                memory_clock_freq = 0.0

            # Collect performance state
            try:
                performance_state = pynvml.nvmlDeviceGetPerformanceState(handle)
                performance_state_str = f"P{performance_state}"
            except Exception:
                performance_state_str = "Unknown"

            # Collect active processes
            try:
                processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                active_processes = len(processes)
            except Exception:
                active_processes = 0

            # Calculate memory utilization
            memory_used_mb = memory_info.used / (1024 * 1024)
            memory_total_mb = memory_info.total / (1024 * 1024)
            memory_utilization = (memory_info.used / memory_info.total) * 100

            # Create snapshot
            snapshot = GPUMetricSnapshot(
                timestamp=datetime.utcnow(),
                gpu_id=gpu_id,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                memory_utilization=memory_utilization,
                gpu_utilization=utilization.gpu,
                temperature_celsius=temperature,
                power_usage_watts=power_usage,
                clock_frequency_mhz=clock_freq,
                memory_clock_frequency_mhz=memory_clock_freq,
                active_processes=active_processes,
                performance_state=performance_state_str,
            )

            # Add CHS-specific metrics if available
            if self.chs_accelerator:
                snapshot.processing_throughput = self._get_current_throughput()
                snapshot.error_rate = self._get_current_error_rate()
                snapshot.latency_ms = self._get_current_latency()
                snapshot.cache_hit_rate = self._get_current_cache_hit_rate()

            return snapshot

        except Exception as e:
            self.logger.exception(
                f"Failed to collect GPU metrics for device {gpu_id}: {e}"
            )
            return None

    async def _process_snapshot(self, snapshot: GPUMetricSnapshot) -> None:
        """Process collected snapshot and generate alerts if needed."""
        try:
            # Check thresholds and generate alerts
            if self.config.enable_alerts:
                await self._check_thresholds(snapshot)

            # Log metrics if configured
            if self.config.log_file_path:
                await self._log_metrics(snapshot)

        except Exception as e:
            self.logger.exception(f"Error processing snapshot: {e}")

    async def _check_thresholds(self, snapshot: GPUMetricSnapshot) -> None:
        """Check metric thresholds and generate alerts."""
        try:
            # Check memory usage
            if (
                snapshot.memory_utilization
                > self.config.thresholds["memory_usage_critical"]
            ):
                await self._generate_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.MEMORY_USAGE,
                    snapshot.gpu_id,
                    f"Critical memory usage: {snapshot.memory_utilization:.1f}%",
                    snapshot.memory_utilization,
                    self.config.thresholds["memory_usage_critical"],
                )
            elif (
                snapshot.memory_utilization
                > self.config.thresholds["memory_usage_warning"]
            ):
                await self._generate_alert(
                    AlertSeverity.WARNING,
                    MetricType.MEMORY_USAGE,
                    snapshot.gpu_id,
                    f"High memory usage: {snapshot.memory_utilization:.1f}%",
                    snapshot.memory_utilization,
                    self.config.thresholds["memory_usage_warning"],
                )

            # Check GPU utilization
            if (
                snapshot.gpu_utilization
                > self.config.thresholds["gpu_utilization_warning"]
            ):
                await self._generate_alert(
                    AlertSeverity.WARNING,
                    MetricType.GPU_UTILIZATION,
                    snapshot.gpu_id,
                    f"High GPU utilization: {snapshot.gpu_utilization:.1f}%",
                    snapshot.gpu_utilization,
                    self.config.thresholds["gpu_utilization_warning"],
                )

            # Check temperature
            if (
                snapshot.temperature_celsius
                > self.config.thresholds["temperature_critical"]
            ):
                await self._generate_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.TEMPERATURE,
                    snapshot.gpu_id,
                    f"Critical temperature: {snapshot.temperature_celsius:.1f}°C",
                    snapshot.temperature_celsius,
                    self.config.thresholds["temperature_critical"],
                )
            elif (
                snapshot.temperature_celsius
                > self.config.thresholds["temperature_warning"]
            ):
                await self._generate_alert(
                    AlertSeverity.WARNING,
                    MetricType.TEMPERATURE,
                    snapshot.gpu_id,
                    f"High temperature: {snapshot.temperature_celsius:.1f}°C",
                    snapshot.temperature_celsius,
                    self.config.thresholds["temperature_warning"],
                )

            # Check CHS-specific metrics
            if (
                snapshot.error_rate is not None
                and snapshot.error_rate > self.config.thresholds["error_rate_critical"]
            ):
                await self._generate_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.ERROR_RATE,
                    snapshot.gpu_id,
                    f"Critical error rate: {snapshot.error_rate:.1f}%",
                    snapshot.error_rate,
                    self.config.thresholds["error_rate_critical"],
                )

            if (
                snapshot.latency_ms is not None
                and snapshot.latency_ms > self.config.thresholds["latency_critical"]
            ):
                await self._generate_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.LATENCY,
                    snapshot.gpu_id,
                    f"Critical latency: {snapshot.latency_ms:.1f}ms",
                    snapshot.latency_ms,
                    self.config.thresholds["latency_critical"],
                )

            if (
                snapshot.cache_hit_rate is not None
                and snapshot.cache_hit_rate
                < self.config.thresholds["cache_hit_rate_warning"]
            ):
                await self._generate_alert(
                    AlertSeverity.WARNING,
                    MetricType.CACHE_HIT_RATE,
                    snapshot.gpu_id,
                    f"Low cache hit rate: {snapshot.cache_hit_rate:.1f}%",
                    snapshot.cache_hit_rate,
                    self.config.thresholds["cache_hit_rate_warning"],
                )

        except Exception as e:
            self.logger.exception(f"Error checking thresholds: {e}")

    async def _generate_alert(
        self,
        severity: AlertSeverity,
        metric_type: MetricType,
        gpu_id: int,
        message: str,
        current_value: float,
        threshold: float,
    ) -> None:
        """Generate and process performance alert."""
        try:
            # Check cooldown period
            alert_key = f"{metric_type.value}_{gpu_id}"
            current_time = datetime.utcnow()

            if alert_key in self.last_alert_times:
                time_since_last = current_time - self.last_alert_times[alert_key]
                cooldown_period = timedelta(minutes=self.config.alert_cooldown_minutes)

                if time_since_last < cooldown_period:
                    return  # Still in cooldown period

            # Create alert
            alert_id = f"{metric_type.value}_{gpu_id}_{int(current_time.timestamp())}"
            alert = PerformanceAlert(
                id=alert_id,
                severity=severity,
                metric_type=metric_type,
                gpu_id=gpu_id,
                message=message,
                current_value=current_value,
                threshold=threshold,
                timestamp=current_time,
            )

            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.last_alert_times[alert_key] = current_time

            # Log alert
            self.logger.warning(f"GPU Alert [{severity.value.upper()}]: {message}")

            # Call alert handlers
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.exception(f"Error in alert handler: {e}")

        except Exception as e:
            self.logger.exception(f"Error generating alert: {e}")

    async def _log_metrics(self, snapshot: GPUMetricSnapshot) -> None:
        """Log metrics to file."""
        try:
            if not self.config.log_file_path:
                return

            log_path = Path(self.config.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{json.dumps(snapshot.to_dict())}\n")

        except Exception as e:
            self.logger.exception(f"Error logging metrics: {e}")

    async def _process_chs_data(self) -> None:
        """Process CHS accelerator data for monitoring."""
        try:
            if not self.chs_accelerator:
                return

            # Get recent processing results
            recent_results = self.chs_accelerator.processing_history[
                -10:
            ]  # Last 10 results

            if not recent_results:
                return

            # Update performance statistics
            total_processing_time = sum(r.processing_time for r in recent_results)
            total_items = sum(r.items_processed for r in recent_results)
            error_count = sum(1 for r in recent_results if r.error_message)

            self.performance_stats.update(
                {
                    "total_processing_time": total_processing_time,
                    "total_items_processed": total_items,
                    "total_errors": error_count,
                    "average_throughput": (
                        total_items / total_processing_time
                        if total_processing_time > 0
                        else 0
                    ),
                    "average_latency": (
                        total_processing_time / len(recent_results)
                        if recent_results
                        else 0
                    ),
                    "cache_hit_rate": (
                        self.chs_accelerator.cache_hits
                        / (
                            self.chs_accelerator.cache_hits
                            + self.chs_accelerator.cache_misses
                        )
                        if (
                            self.chs_accelerator.cache_hits
                            + self.chs_accelerator.cache_misses
                        )
                        > 0
                        else 0
                    ),
                },
            )

        except Exception as e:
            self.logger.exception(f"Error processing CHS data: {e}")

    def _get_current_throughput(self) -> float | None:
        """Get current processing throughput."""
        try:
            if not self.processing_results:
                return None

            # Calculate throughput from recent results
            recent_results = self.processing_results[-5:]  # Last 5 results
            total_items = sum(r.items_processed for r in recent_results)
            total_time = sum(r.processing_time for r in recent_results)

            return total_items / total_time if total_time > 0 else None

        except Exception:
            return None

    def _get_current_error_rate(self) -> float | None:
        """Get current error rate."""
        try:
            if not self.processing_results:
                return None

            # Calculate error rate from recent results
            recent_results = self.processing_results[-10:]  # Last 10 results
            error_count = sum(1 for r in recent_results if r.error_message)

            return (error_count / len(recent_results)) * 100 if recent_results else None

        except Exception:
            return None

    def _get_current_latency(self) -> float | None:
        """Get current average processing latency."""
        try:
            if not self.processing_results:
                return None

            # Calculate average latency from recent results
            recent_results = self.processing_results[-5:]  # Last 5 results
            avg_latency = sum(r.processing_time for r in recent_results) / len(
                recent_results
            )

            return avg_latency * 1000  # Convert to milliseconds

        except Exception:
            return None

    def _get_current_cache_hit_rate(self) -> float | None:
        """Get current cache hit rate."""
        try:
            if not self.chs_accelerator:
                return None

            total_access = (
                self.chs_accelerator.cache_hits + self.chs_accelerator.cache_misses
            )

            if total_access == 0:
                return None

            return (self.chs_accelerator.cache_hits / total_access) * 100

        except Exception:
            return None

    async def _cleanup_old_data(self) -> None:
        """Clean up old metrics and alert data."""
        try:
            current_time = datetime.utcnow()
            retention_cutoff = current_time - timedelta(
                hours=self.config.history_retention_hours
            )

            # Clean up old alerts
            self.alert_history = [
                alert
                for alert in self.alert_history
                if alert.timestamp > retention_cutoff
            ]

            # Clean up old last alert times
            self.last_alert_times = {
                key: time
                for key, time in self.last_alert_times.items()
                if time > retention_cutoff
            }

        except Exception as e:
            self.logger.exception(f"Error cleaning up old data: {e}")

    async def _save_metrics(self) -> None:
        """Save metrics history to file."""
        try:
            if not self.config.metrics_file_path:
                return

            metrics_data = {}
            for gpu_id, history in self.metrics_history.items():
                metrics_data[str(gpu_id)] = [snapshot.to_dict() for snapshot in history]

            metrics_path = Path(self.config.metrics_file_path)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)

            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.exception(f"Error saving metrics: {e}")

    async def _save_alerts(self) -> None:
        """Save alerts to file."""
        try:
            if not self.config.alerts_file_path:
                return

            alerts_data = {
                "active_alerts": {
                    aid: alert.to_dict() for aid, alert in self.active_alerts.items()
                },
                "alert_history": [alert.to_dict() for alert in self.alert_history],
            }

            alerts_path = Path(self.config.alerts_file_path)
            alerts_path.parent.mkdir(parents=True, exist_ok=True)

            with open(alerts_path, "w", encoding="utf-8") as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.exception(f"Error saving alerts: {e}")

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current GPU metrics for all monitored GPUs."""
        current_metrics = {}

        for gpu_id, history in self.metrics_history.items():
            if history:
                latest_snapshot = history[-1]
                current_metrics[str(gpu_id)] = latest_snapshot.to_dict()

        return current_metrics

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "monitoring_active": self.monitoring_active,
            "gpus_monitored": len(self.gpu_handles),
            "total_alerts": len(self.alert_history),
            "active_alerts": len(self.active_alerts),
            "performance_stats": self.performance_stats.copy(),
            "monitoring_config": {
                "interval_seconds": self.config.monitoring_interval_seconds,
                "retention_hours": self.config.history_retention_hours,
                "alerts_enabled": self.config.enable_alerts,
            },
        }

        # Add GPU-specific summaries
        for gpu_id in self.config.gpu_ids:
            if self.metrics_history.get(gpu_id):
                history = self.metrics_history[gpu_id]
                if history:
                    latest = history[-1]
                    summary[f"gpu_{gpu_id}"] = {
                        "current_memory_usage": latest.memory_utilization,
                        "current_gpu_utilization": latest.gpu_utilization,
                        "current_temperature": latest.temperature_celsius,
                        "current_power_usage": latest.power_usage_watts,
                        "data_points": len(history),
                    }

        return summary

    def get_alerts(self, include_resolved: bool = False) -> list[PerformanceAlert]:
        """Get alerts, optionally including resolved ones."""
        if include_resolved:
            return self.alert_history.copy()
        return [alert for alert in self.alert_history if not alert.resolved]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        try:
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].acknowledged = True
                self.active_alerts[alert_id].acknowledged_by = acknowledged_by
                return True
            return False

        except Exception as e:
            self.logger.exception(f"Error acknowledging alert: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_timestamp = datetime.utcnow()
                del self.active_alerts[alert_id]
                return True
            return False

        except Exception as e:
            self.logger.exception(f"Error resolving alert: {e}")
            return False

    def add_alert_handler(self, handler: Callable[[PerformanceAlert], Any]) -> None:
        """Add custom alert handler."""
        self.alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[PerformanceAlert], Any]) -> None:
        """Remove custom alert handler."""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)

    def update_config(self, config: MonitoringConfig) -> None:
        """Update monitoring configuration."""
        self.config = config
        self.logger.info("Monitoring configuration updated")

    async def cleanup(self) -> None:
        """Cleanup monitoring resources."""
        try:
            # Stop monitoring
            await self.stop_monitoring()

            # Cleanup NVML
            if PYNVML_AVAILABLE and self.gpu_handles:
                with contextlib.suppress(Exception):
                    pynvml.nvmlShutdown()

            # Clear data
            self.metrics_history.clear()
            self.active_alerts.clear()
            self.alert_history.clear()
            self.processing_results.clear()

            self.logger.info("GPUPerformanceMonitor cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")


# Factory function for easy initialization
def create_gpu_performance_monitor(
    gpu_ids: list[int] | None = None,
    monitoring_interval: int = 5,
    enable_alerts: bool = True,
    chs_accelerator: CHSGPUAccelerator | None = None,
) -> GPUPerformanceMonitor:
    """Factory function to create a configured GPU performance monitor.

    Parameters
    ----------
    gpu_ids: List of GPU device IDs to monitor
    monitoring_interval: Monitoring interval in seconds
    enable_alerts: Enable alert generation
    chs_accelerator: Optional CHS GPU accelerator for integration

    Returns
    -------
    GPUPerformanceMonitor: Configured performance monitor instance

    """
    config = MonitoringConfig(
        gpu_ids=gpu_ids or [0],
        monitoring_interval_seconds=monitoring_interval,
        enable_alerts=enable_alerts,
        enable_chs_integration=chs_accelerator is not None,
    )

    return GPUPerformanceMonitor(config, chs_accelerator)


# Example alert handler
async def console_alert_handler(alert: PerformanceAlert) -> None:
    """Example alert handler that logs alerts to console."""
    alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")


# Example usage and testing
if __name__ == "__main__":

    async def main() -> None:
        """Example usage of GPUPerformanceMonitor."""
        # Create monitor with default configuration
        monitor = create_gpu_performance_monitor(
            gpu_ids=[0],
            monitoring_interval=5,
            enable_alerts=True,
        )

        # Add console alert handler
        monitor.add_alert_handler(console_alert_handler)

        try:
            # Start monitoring
            await monitor.start_monitoring()

            # Monitor for 30 seconds
            await asyncio.sleep(30)

            # Get performance summary
            monitor.get_performance_summary()

            # Get current metrics
            monitor.get_current_metrics()

            # Get alerts
            alerts = monitor.get_alerts()
            if alerts:
                for _alert in alerts:
                    pass

        finally:
            # Stop monitoring and cleanup
            await monitor.cleanup()

    # Run example
    asyncio.run(main())
