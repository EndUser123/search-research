import builtins
import gc
import logging
import threading
import time
import warnings
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..utils.constitutional_validator import ConstitutionalValidator

"""CKS GPU Memory Manager - RAPIDS integration with 6GB limits and CPU fallback.

Constitutional Requirements:
- Solo developer optimization (strict memory limits, auto-cleanup)
- Evidence-based implementation (TDD approach, comprehensive monitoring)
- Force multiplier integration (GPU acceleration with CPU fallback)
- No enterprise bloat (simple interfaces, direct Python integration)

Architecture:
Phase 1: Single PC deployment with 6GB GPU memory limit
- RAPIDS cuDF/cuML for GPU-accelerated operations
- FAISS-GPU for vector similarity search
- Automatic CPU fallback on GPU memory issues
- Memory leak prevention and cleanup
- Real-time monitoring and alerts

Implementation:
1. GPU memory tracking and management
2. RAPIDS integration with automatic fallback
3. FAISS-GPU optimization with memory pools
4. Memory leak detection and prevention
5. Solo developer optimization features
6. Constitutional compliance validation
"""



# Suppress common warnings for cleaner solo developer experience
warnings.filterwarnings("ignore", category=FutureWarning)

# GPU library imports with graceful fallback
try:
    import pynvml

    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logging.warning("pynvml not available - GPU monitoring will be limited")

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available - vector operations will be CPU-only")

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    logging.warning("CuPy not available - GPU array operations will be limited")

try:
    import cudf
    import cuml

    RAPIDS_AVAILABLE = True
except ImportError:
    RAPIDS_AVAILABLE = False
    logging.warning("RAPIDS not available - DataFrame operations will be CPU-only")



@dataclass
class GPUMemoryConfig:
    """GPU memory configuration with strict 6GB limit.

    Constitutional Requirements:
    - Solo developer optimized (conservative memory limits)
    - Evidence-based configuration (real-world testing)
    - Force multiplier (GPU + CPU hybrid)
    """

    max_gpu_memory_mb: int = 6144  # Strict 6GB limit for solo developer
    memory_threshold_mb: int = 4608  # 4.5GB threshold for warnings (75% of max)
    cleanup_threshold_mb: int = 5324  # 5.25GB threshold for auto-cleanup (86.7% of max)
    enable_gpu: bool = True
    auto_cleanup: bool = True
    memory_pool_size_mb: int = 1024  # 1GB memory pool
    fallback_to_cpu: bool = True
    monitoring_interval: float = 5.0  # Monitoring interval in seconds
    leak_detection_threshold_mb: int = 100  # Memory leak detection threshold

    def __post_init__(self):
        """Validate configuration parameters with constitutional compliance."""
        if self.max_gpu_memory_mb <= 0:
            raise ValueError("max_gpu_memory_mb must be positive")

        # Solo developer optimization: enforce 6GB maximum
        if self.max_gpu_memory_mb > 6144:
            raise ValueError(
                f"max_gpu_memory_mb {self.max_gpu_memory_mb}MB exceeds solo developer maximum of 6144MB",
            )

        # Auto-adjust thresholds if they conflict with max_memory_mb
        if self.memory_threshold_mb >= self.max_gpu_memory_mb:
            self.memory_threshold_mb = int(self.max_gpu_memory_mb * 0.75)  # 75% of max
            logging.info(
                f"Auto-adjusted memory_threshold_mb to {self.memory_threshold_mb}MB",
            )

        if self.cleanup_threshold_mb >= self.max_gpu_memory_mb:
            self.cleanup_threshold_mb = int(
                self.max_gpu_memory_mb * 0.867,
            )  # 86.7% of max
            logging.info(
                f"Auto-adjusted cleanup_threshold_mb to {self.cleanup_threshold_mb}MB",
            )

        if self.memory_pool_size_mb > self.max_gpu_memory_mb:
            self.memory_pool_size_mb = min(1024, self.max_gpu_memory_mb // 2)
            logging.info(
                f"Auto-adjusted memory_pool_size_mb to {self.memory_pool_size_mb}MB",
            )

        # Validate final configuration
        if self.memory_threshold_mb >= self.max_gpu_memory_mb:
            raise ValueError("memory_threshold_mb must be less than max_gpu_memory_mb")
        if self.cleanup_threshold_mb >= self.max_gpu_memory_mb:
            raise ValueError("cleanup_threshold_mb must be less than max_gpu_memory_mb")
        if self.memory_pool_size_mb > self.max_gpu_memory_mb:
            raise ValueError("memory_pool_size_mb cannot exceed max_gpu_memory_mb")


@dataclass
class GPUMemoryStats:
    """GPU memory statistics snapshot."""

    timestamp: float = field(default_factory=time.time)
    total_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    free_memory_mb: float = 0.0
    utilization_percent: float = 0.0
    temperature_celsius: float = 0.0
    power_usage_watts: float = 0.0
    is_available: bool = False
    memory_leaks_detected: int = 0


class GPUMemoryManager:
    """Advanced GPU memory manager with RAPIDS integration and strict limits.

    Algorithm Approach: Multi-layered memory management with proactive monitoring,
    automatic cleanup, and seamless CPU fallback for solo developer optimization.

    Time Complexity:
    - Memory checks: O(1) for direct GPU queries
    - Cleanup operations: O(n) where n is number of allocated objects
    - Fallback operations: O(1) for CPU transition

    Space Complexity:
    - GPU Memory: Configurable with strict 6GB limit
    - CPU Memory: O(1) for management overhead
    - Monitoring: O(1) constant memory usage

    Constitutional Features:
    - Solo developer optimization (strict limits, auto-cleanup)
    - Evidence-based operations (comprehensive monitoring, audit trails)
    - Force multiplier (GPU acceleration with CPU fallback)
    - No enterprise bloat (simple Python interfaces, no external services)
    """

    def __init__(self, config: GPUMemoryConfig) -> None:
        """Initialize GPU memory manager with configuration."""
        self.config = config
        self._lock = threading.RLock()
        self._validator = ConstitutionalValidator()
        self._initialized = False
        self._monitoring_active = False
        self._monitoring_thread: threading.Thread | None = None

        # GPU state tracking
        self._gpu_available = False
        self._gpu_device_count = 0
        self._current_gpu_id = 0
        self._memory_pool: Any | None = None
        self._allocated_objects: dict[str, Any] = {}
        self._memory_history: list[GPUMemoryStats] = []
        self._leak_detection_baseline = 0.0

        # RAPIDS components
        self._cudf_enabled = False
        self._cuml_enabled = False
        self._faiss_gpu_index: Any | None = None

        # Performance tracking
        self._operation_count = 0
        self._fallback_count = 0
        self._cleanup_count = 0
        self._memory_warnings_count = 0

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.logger.info("GPUMemoryManager initialized with constitutional compliance")

    def initialize(self) -> None:
        """Initialize GPU memory manager and components.

        Raises:
            RuntimeError: If initialization fails
        """
        if self._initialized:
            return

        try:
            self._validate_configuration()
            self._initialize_gpu_monitoring()
            self._initialize_rapids_components()
            self._initialize_faiss_gpu()
            self._initialize_memory_pool()
            self._start_monitoring()
            self._initialized = True

            self.logger.info("GPUMemoryManager initialization completed successfully")
            self._audit_log(
                "system",
                "initialize",
                {
                    "success": True,
                    "gpu_available": self._gpu_available,
                    "max_memory_mb": self.config.max_gpu_memory_mb,
                },
            )

        except Exception as e:
            self.logger.exception(f"GPUMemoryManager initialization failed: {e}")
            self._audit_log(
                "system",
                "initialize",
                {
                    "success": False,
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Failed to initialize GPUMemoryManager: {e}")

    def _validate_configuration(self) -> None:
        """Validate configuration against constitutional requirements."""
        violations = []

        # Solo developer optimization checks
        if self.config.max_gpu_memory_mb > 6144:
            violations.append(
                f"GPU memory limit {self.config.max_gpu_memory_mb}MB exceeds solo developer maximum of 6GB",
            )

        # Evidence-based configuration checks
        if self.config.monitoring_interval > 30.0:
            violations.append(
                "Monitoring interval exceeds 30 seconds - may miss critical memory issues",
            )

        # Anti-enterprise bloat checks
        if self.config.memory_pool_size_mb > 2048:
            violations.append(
                "Memory pool size exceeds solo developer optimization limit",
            )

        if violations:
            error_msg = "Constitutional violations: " + "; ".join(violations)
            self.logger.error(f"Configuration validation failed: {error_msg}")
            raise ValueError(error_msg)

        self.logger.info("Configuration passed constitutional validation")

    def _initialize_gpu_monitoring(self) -> None:
        """Initialize GPU monitoring with NVML."""
        if not self.config.enable_gpu:
            self.logger.info("GPU disabled in configuration")
            return

        try:
            if NVML_AVAILABLE:
                pynvml.nvmlInit()
                self._gpu_device_count = pynvml.nvmlDeviceGetCount()
                self._gpu_available = self._gpu_device_count > 0

                if self._gpu_available:
                    # Test GPU access
                    handle = pynvml.nvmlDeviceGetHandleByIndex(self._current_gpu_id)
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                    # Check if GPU has sufficient memory
                    total_memory_mb = memory_info.total / 1024 / 1024
                    if total_memory_mb < self.config.max_gpu_memory_mb:
                        self.logger.warning(
                            f"GPU has only {total_memory_mb:.0f}MB memory, less than configured limit {self.config.max_gpu_memory_mb}MB",
                        )

                    self.logger.info(
                        f"GPU monitoring initialized: {self._gpu_device_count} devices, {total_memory_mb:.0f}MB total memory",
                    )
                else:
                    self.logger.warning("No GPU devices found")
            else:
                self.logger.warning("NVML not available - GPU monitoring limited")

        except Exception as e:
            self.logger.warning(f"GPU monitoring initialization failed: {e}")
            self._gpu_available = False

    def _initialize_rapids_components(self) -> None:
        """Initialize RAPIDS components with fallback."""
        if not self._gpu_available or not RAPIDS_AVAILABLE:
            self.logger.info(
                "RAPIDS components disabled - GPU not available or RAPIDS not installed",
            )
            return

        try:
            # Test CuPy
            if CUPY_AVAILABLE:
                test_array = cp.array([1, 2, 3, 4, 5])
                del test_array
                self.logger.info("CuPy initialized successfully")

            # Test cuDF
            try:
                test_df = cudf.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
                del test_df
                self._cudf_enabled = True
                self.logger.info("cuDF initialized successfully")
            except Exception as e:
                self.logger.warning(f"cuDF initialization failed: {e}")

            # Test cuML
            try:
                from cuml.neighbors import NearestNeighbors

                NearestNeighbors(n_neighbors=2)
                self._cuml_enabled = True
                self.logger.info("cuML initialized successfully")
            except Exception as e:
                self.logger.warning(f"cuML initialization failed: {e}")

        except Exception as e:
            self.logger.exception(f"RAPIDS initialization failed: {e}")
            if self.config.fallback_to_cpu:
                self.logger.info("Falling back to CPU-only operations")
            else:
                raise

    def _initialize_faiss_gpu(self) -> None:
        """Initialize FAISS GPU resources."""
        if not self._gpu_available or not FAISS_AVAILABLE:
            self.logger.info(
                "FAISS GPU disabled - GPU not available or FAISS not installed",
            )
            return

        try:
            # Create GPU resources
            gpu_resources = faiss.StandardGpuResources()

            # Set memory limits for FAISS
            gpu_resources.setTempMemory(self.config.memory_pool_size_mb * 1024 * 1024)

            self.logger.info("FAISS GPU resources initialized successfully")

        except Exception as e:
            self.logger.warning(f"FAISS GPU initialization failed: {e}")
            if self.config.fallback_to_cpu:
                self.logger.info("FAISS will use CPU-only operations")
            else:
                raise

    def _initialize_memory_pool(self) -> None:
        """Initialize GPU memory pool for efficient allocation."""
        if not self._gpu_available or not CUPY_AVAILABLE:
            self.logger.info("GPU memory pool disabled - CuPy not available")
            return

        try:
            # Create memory pool
            self._memory_pool = cp.get_default_memory_pool()
            self._memory_pool.set_limit(
                size=self.config.memory_pool_size_mb * 1024 * 1024,
            )

            self.logger.info(
                f"GPU memory pool initialized: {self.config.memory_pool_size_mb}MB limit",
            )

        except Exception as e:
            self.logger.warning(f"Memory pool initialization failed: {e}")

    def _start_monitoring(self) -> None:
        """Start background GPU memory monitoring."""
        if not self._gpu_available or self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True,
        )
        self._monitoring_thread.start()
        self.logger.info("GPU memory monitoring started")

    def _monitoring_loop(self) -> None:
        """Background monitoring loop for GPU memory."""
        while self._monitoring_active:
            try:
                stats = self.get_memory_stats()
                self._memory_history.append(stats)

                # Keep only last 1000 entries to prevent memory bloat
                if len(self._memory_history) > 1000:
                    self._memory_history = self._memory_history[-1000:]

                # Check memory thresholds
                if stats.used_memory_mb > self.config.memory_threshold_mb:
                    self._memory_warnings_count += 1
                    self.logger.warning(
                        f"GPU memory usage high: {stats.used_memory_mb:.0f}MB ({stats.utilization_percent:.1f}%)",
                    )

                # Trigger auto-cleanup if needed
                if (
                    self.config.auto_cleanup
                    and stats.used_memory_mb > self.config.cleanup_threshold_mb
                ):
                    self._trigger_auto_cleanup()

                # Check for memory leaks
                self._detect_memory_leaks(stats)

                time.sleep(self.config.monitoring_interval)

            except Exception as e:
                self.logger.exception(f"Monitoring loop error: {e}")
                time.sleep(self.config.monitoring_interval)

    def _trigger_auto_cleanup(self) -> None:
        """Trigger automatic GPU memory cleanup."""
        try:
            freed_memory = self.cleanup_gpu_memory()
            self._cleanup_count += 1
            self.logger.info(f"Auto-cleanup completed: freed {freed_memory:.0f}MB")
        except Exception as e:
            self.logger.exception(f"Auto-cleanup failed: {e}")

    def _detect_memory_leaks(self, current_stats: GPUMemoryStats) -> None:
        """Detect potential memory leaks."""
        if len(self._memory_history) < 10:  # Need baseline
            return

        # Calculate average memory usage over recent history
        recent_memory = [stats.used_memory_mb for stats in self._memory_history[-10:]]
        avg_recent = sum(recent_memory) / len(recent_memory)

        # Check if memory is consistently growing
        if (
            avg_recent
            > self._leak_detection_baseline + self.config.leak_detection_threshold_mb
        ):
            current_stats.memory_leaks_detected = int(
                (avg_recent - self._leak_detection_baseline)
                / self.config.leak_detection_threshold_mb,
            )
            self.logger.warning(
                f"Potential memory leak detected: {avg_recent - self._leak_detection_baseline:.0f}MB increase",
            )

        # Update baseline periodically
        if self._operation_count % 100 == 0:
            self._leak_detection_baseline = avg_recent

    def get_memory_stats(self) -> GPUMemoryStats:
        """Get current GPU memory statistics.

        Returns:
            GPUMemoryStats: Current GPU memory statistics
        """
        stats = GPUMemoryStats()

        if not self._gpu_available:
            return stats

        try:
            if NVML_AVAILABLE:
                handle = pynvml.nvmlDeviceGetHandleByIndex(self._current_gpu_id)

                # Memory information
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                stats.total_memory_mb = memory_info.total / 1024 / 1024
                stats.used_memory_mb = memory_info.used / 1024 / 1024
                stats.free_memory_mb = memory_info.free / 1024 / 1024
                stats.utilization_percent = (memory_info.used / memory_info.total) * 100

                # Temperature and power (if available)
                with suppress(builtins.BaseException):
                    stats.temperature_celsius = pynvml.nvmlDeviceGetTemperature(
                        handle,
                        pynvml.NVML_TEMPERATURE_GPU,
                    )

                with suppress(builtins.BaseException):
                    stats.power_usage_watts = (
                        pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                    )

                stats.is_available = True

            elif CUPY_AVAILABLE:
                # Fallback to CuPy memory info
                mempool = cp.get_default_memory_pool()
                stats.used_memory_mb = mempool.used_bytes() / 1024 / 1024
                stats.total_memory_mb = mempool.total_bytes() / 1024 / 1024
                stats.free_memory_mb = stats.total_memory_mb - stats.used_memory_mb
                stats.utilization_percent = (
                    (stats.used_memory_mb / stats.total_memory_mb) * 100
                    if stats.total_memory_mb > 0
                    else 0
                )
                stats.is_available = True

        except Exception as e:
            self.logger.warning(f"Failed to get GPU memory stats: {e}")
            stats.is_available = False

        return stats

    def check_memory_availability(self, required_memory_mb: float) -> bool:
        """Check if GPU has sufficient memory available.

        Args:
            required_memory_mb: Required memory in MB

        Returns:
            bool: True if memory is available
        """
        if not self._gpu_available:
            return self.config.fallback_to_cpu

        stats = self.get_memory_stats()
        available_memory = stats.free_memory_mb

        # Add safety margin (10% of required memory)
        safety_margin = required_memory_mb * 0.1
        total_required = required_memory_mb + safety_margin

        return available_memory >= total_required

    def allocate_gpu_array(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float32,
    ) -> np.ndarray | Any:
        """Allocate GPU array with memory checking and fallback.

        Args:
            shape: Shape of the array
            dtype: Data type of the array

        Returns:
            Union[np.ndarray, Any]: GPU array or CPU numpy array as fallback
        """
        self._operation_count += 1

        if not self._gpu_available or not CUPY_AVAILABLE:
            self._fallback_count += 1
            return np.zeros(shape, dtype=dtype)

        # Calculate required memory
        element_size = np.dtype(dtype).itemsize
        total_elements = np.prod(shape)
        required_memory_mb = (total_elements * element_size) / 1024 / 1024

        # Check memory availability
        if not self.check_memory_availability(required_memory_mb):
            self._fallback_count += 1
            self.logger.info(
                f"GPU memory insufficient for {required_memory_mb:.1f}MB, falling back to CPU",
            )
            return np.zeros(shape, dtype=dtype)

        try:
            # Allocate GPU array
            gpu_array = cp.zeros(shape, dtype=dtype)

            # Track allocation
            array_id = f"array_{int(time.time() * 1000000)}"
            self._allocated_objects[array_id] = {
                "type": "gpu_array",
                "shape": shape,
                "dtype": str(dtype),
                "memory_mb": required_memory_mb,
                "created_at": time.time(),
            }

            return gpu_array

        except Exception as e:
            self._fallback_count += 1
            self.logger.warning(f"GPU allocation failed: {e}, falling back to CPU")
            return np.zeros(shape, dtype=dtype)

    def create_gpu_dataframe(self, data: dict[str, Any]) -> Any | pd.DataFrame:
        """Create GPU DataFrame with fallback.

        Args:
            data: Dictionary of column data

        Returns:
            Union[Any, pd.DataFrame]: GPU DataFrame or pandas DataFrame as fallback
        """
        self._operation_count += 1

        if not self._cudf_enabled:
            self._fallback_count += 1
            import pandas as pd

            return pd.DataFrame(data)

        try:
            # Create cuDF DataFrame
            gpu_df = cudf.DataFrame(data)

            # Track allocation
            df_id = f"df_{int(time.time() * 1000000)}"
            self._allocated_objects[df_id] = {
                "type": "gpu_dataframe",
                "columns": list(data.keys()),
                "rows": len(next(iter(data.values()))),
                "created_at": time.time(),
            }

            return gpu_df

        except Exception as e:
            self._fallback_count += 1
            self.logger.warning(
                f"GPU DataFrame creation failed: {e}, falling back to CPU",
            )

            return pd.DataFrame(data)

    def create_faiss_index(self, dimension: int, index_type: str = "flat") -> Any:
        """Create FAISS index with GPU support.

        Args:
            dimension: Vector dimension
            index_type: Type of index (flat, ivf, etc.)

        Returns:
            Any: FAISS index (GPU or CPU)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is not available")

        self._operation_count += 1

        try:
            # Create CPU index first
            if index_type == "flat":
                cpu_index = faiss.IndexFlatIP(dimension)
            elif index_type == "ivf":
                nlist = min(100, max(1, dimension // 4))
                quantizer = faiss.IndexFlatIP(dimension)
                cpu_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            else:
                raise ValueError(f"Unsupported index type: {index_type}")

            # Move to GPU if available
            if self._gpu_available:
                try:
                    gpu_resources = faiss.StandardGpuResources()
                    gpu_index = faiss.index_cpu_to_gpu(
                        gpu_resources,
                        self._current_gpu_id,
                        cpu_index,
                    )
                    self._faiss_gpu_index = gpu_index
                    self.logger.info(
                        f"Created FAISS GPU index: {index_type}, dimension={dimension}",
                    )
                    return gpu_index
                except Exception as e:
                    self.logger.warning(
                        f"FAISS GPU index creation failed: {e}, using CPU",
                    )
                    self._fallback_count += 1

            return cpu_index

        except Exception as e:
            self.logger.exception(f"FAISS index creation failed: {e}")
            raise

    def cleanup_gpu_memory(self, force: bool = False) -> float:
        """Clean up GPU memory and return freed memory amount.

        Args:
            force: Force cleanup even if memory usage is low

        Returns:
            float: Amount of memory freed in MB
        """
        if not self._gpu_available:
            return 0.0

        freed_memory_mb = 0.0

        try:
            # Get memory before cleanup
            stats_before = self.get_memory_stats()

            # Clear allocated objects tracking
            objects_to_remove = []
            for obj_id, obj_info in self._allocated_objects.items():
                if force or time.time() - obj_info["created_at"] > 300:  # 5 minutes old
                    objects_to_remove.append(obj_id)

            for obj_id in objects_to_remove:
                del self._allocated_objects[obj_id]

            # Force garbage collection
            gc.collect()

            # Clear GPU memory pool
            if CUPY_AVAILABLE and self._memory_pool:
                self._memory_pool.free_all_blocks()

            # Additional GPU cleanup
            if CUPY_AVAILABLE:
                cp.get_default_memory_pool().free_all_blocks()
                cp.clear_memo()

            # Get memory after cleanup
            stats_after = self.get_memory_stats()
            freed_memory_mb = stats_before.used_memory_mb - stats_after.used_memory_mb

            if freed_memory_mb > 0:
                self.logger.info(f"GPU cleanup freed {freed_memory_mb:.0f}MB")
            else:
                self.logger.info("GPU cleanup completed (no measurable memory freed)")

        except Exception as e:
            self.logger.exception(f"GPU cleanup failed: {e}")

        return freed_memory_mb

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics.

        Returns:
            Dict[str, Any]: Performance statistics
        """
        current_stats = self.get_memory_stats()

        return {
            "gpu_available": self._gpu_available,
            "current_memory_stats": {
                "used_mb": current_stats.used_memory_mb,
                "free_mb": current_stats.free_memory_mb,
                "utilization_percent": current_stats.utilization_percent,
                "temperature_celsius": current_stats.temperature_celsius,
                "is_available": current_stats.is_available,
            },
            "operation_stats": {
                "total_operations": self._operation_count,
                "fallback_count": self._fallback_count,
                "cleanup_count": self._cleanup_count,
                "memory_warnings": self._memory_warnings_count,
                "fallback_rate": (self._fallback_count / max(1, self._operation_count))
                * 100,
            },
            "configuration": {
                "max_memory_mb": self.config.max_gpu_memory_mb,
                "memory_threshold_mb": self.config.memory_threshold_mb,
                "cleanup_threshold_mb": self.config.cleanup_threshold_mb,
                "memory_pool_size_mb": self.config.memory_pool_size_mb,
                "auto_cleanup": self.config.auto_cleanup,
                "fallback_to_cpu": self.config.fallback_to_cpu,
            },
            "allocated_objects": len(self._allocated_objects),
            "memory_history_length": len(self._memory_history),
            "rapids_enabled": {
                "cudf": self._cudf_enabled,
                "cuml": self._cuml_enabled,
                "cupy": CUPY_AVAILABLE,
                "faiss_gpu": self._faiss_gpu_index is not None,
            },
        }

    @contextmanager
    def gpu_context(self, required_memory_mb: float = 0):
        """Context manager for GPU operations with automatic cleanup.

        Args:
            required_memory_mb: Estimated memory requirement
        """
        if not self.check_memory_availability(required_memory_mb):
            if not self.config.fallback_to_cpu:
                raise MemoryError(
                    f"Insufficient GPU memory: required {required_memory_mb}MB",
                )
            self.logger.info("GPU context falling back to CPU")
            yield None
            return

        try:
            yield self
        finally:
            # Minimal cleanup after operation
            if CUPY_AVAILABLE:
                cp.get_default_memory_pool().free_all_blocks()

    def get_constitutional_compliance_score(self) -> float:
        """Get constitutional compliance score for GPU memory management.

        Returns:
            float: Compliance score (0.0 to 1.0)
        """
        metrics = []

        # Memory usage compliance
        stats = self.get_memory_stats()
        if self.config.max_gpu_memory_mb > 0:
            memory_score = max(
                0, 1 - (stats.used_memory_mb / self.config.max_gpu_memory_mb),
            )
        else:
            memory_score = 1.0
        metrics.append(memory_score)

        # Solo developer optimization (low fallback rate is good)
        if self._operation_count > 0:
            fallback_rate = self._fallback_count / self._operation_count
            optimization_score = max(0, 1 - fallback_rate)
        else:
            optimization_score = 1.0
        metrics.append(optimization_score)

        # Evidence-based operations (monitoring active)
        monitoring_score = 1.0 if self._monitoring_active else 0.0
        metrics.append(monitoring_score)

        # Force multiplier (GPU availability and usage)
        force_multiplier_score = 0.0
        if self._gpu_available:
            force_multiplier_score += 0.5
        if self._operation_count > 0:
            gpu_usage_rate = 1 - (self._fallback_count / self._operation_count)
            force_multiplier_score += 0.5 * gpu_usage_rate
        metrics.append(force_multiplier_score)

        return sum(metrics) / len(metrics)

    def _audit_log(
        self, operation_type: str, operation: str, details: dict[str, Any],
    ) -> None:
        """Log operation for audit trail."""
        try:
            {
                "timestamp": time.time(),
                "operation_type": operation_type,
                "operation": operation,
                "details": details,
                "memory_stats": self.get_memory_stats().__dict__,
            }

            # In a real implementation, this would be stored to database or file
            self.logger.debug(f"Audit: {operation_type}.{operation} - {details}")

        except Exception as e:
            self.logger.exception(f"Audit logging failed: {e}")

    def shutdown(self) -> None:
        """Shutdown GPU memory manager and cleanup resources."""
        if not self._initialized:
            return

        try:
            # Stop monitoring
            self._monitoring_active = False
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)

            # Final cleanup
            freed_memory = self.cleanup_gpu_memory(force=True)
            self.logger.info(f"Final GPU cleanup freed {freed_memory:.0f}MB")

            # Clear FAISS index
            self._faiss_gpu_index = None

            # Shutdown NVML
            if NVML_AVAILABLE and self._gpu_available:
                with suppress(builtins.BaseException):
                    pynvml.nvmlShutdown()

            self._initialized = False
            self.logger.info("GPUMemoryManager shutdown completed")

        except Exception as e:
            self.logger.exception(f"GPU manager shutdown failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
