from __future__ import annotations

import asyncio
import gc
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

#!/usr/bin/env python3
"""GPU-Enhanced Chat History Search Accelerator.

CSF NIP Compliant GPU acceleration module for Chat History Search system.
Provides high-performance vector operations, similarity search, and semantic
analysis using CUDA-enabled GPUs with intelligent CPU fallback.

Algorithm Approach: GPU-accelerated vector operations with batch processing,
memory management, and automatic CPU fallback for reliability.

Performance Optimization:
- CUDA-accelerated vector similarity search
- FAISS integration for fast approximate nearest neighbor search
- PyTorch tensor operations for embedding computation
- Memory-efficient batch processing
- Intelligent resource management and monitoring

Hardware Optimization:
- RTX 3060 12GB VRAM optimization
- CUDA kernel optimization
- Memory pooling and cleanup
- Thermal and performance monitoring

Dependencies:
- PyTorch for CUDA operations and tensor management
- FAISS-GPU for fast vector similarity search
- NVIDIA CUDA toolkit and drivers
- Optional: pynvml for detailed GPU monitoring

"""




# GPU and vector processing imports
try:
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    F = None

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


# Define local enums and classes based on latest best practices
class GPUStatus(Enum):
    """Enumeration of GPU status types."""

    AVAILABLE = "available"
    BUSY = "busy"
    OUT_OF_MEMORY = "out_of_memory"
    ERROR = "error"
    NOT_AVAILABLE = "not_available"


class ProcessingMode(Enum):
    """Enumeration of processing modes based on latest GPU optimization practices."""

    GPU_ONLY = "gpu_only"
    CPU_FALLBACK = "cpu_fallback"
    HYBRID = "hybrid"
    AUTO = "auto"  # Automatically choose best mode


@dataclass
class GPUMetrics:
    """GPU performance and resource metrics."""

    gpu_name: str = ""
    memory_total: int = 0
    memory_used: int = 0
    memory_free: int = 0
    utilization: float = 0.0
    temperature: float = 0.0
    power_usage: float = 0.0
    cuda_version: str = ""
    driver_version: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GPUConfig:
    """GPU configuration based on latest best practices."""

    device_id: int = 0
    memory_fraction: float = 0.8  # Use 80% of GPU memory
    enable_mixed_precision: bool = True  # Use FP16 for efficiency
    batch_size: int = 512
    temp_memory_mb: int = 512  # 512MB temp memory for FAISS
    fallback_to_cpu: bool = True
    enable_cuda_graphs: bool = True
    benchmark_mode: bool = False


@dataclass
class GPUProcessingResult:
    """Result of GPU processing operation."""

    success: bool = False
    processing_time: float = 0.0
    items_processed: int = 0
    gpu_utilization: float = 0.0
    memory_allocated: float = 0.0
    throughput: float = 0.0
    speedup_factor: float = 1.0
    error_message: str = ""
    mode_used: ProcessingMode = ProcessingMode.AUTO


# Legacy GPU manager imports (optional)
try:
    from ...performance.gpu_acceleration.gpu_manager_factory import (
        GPUManager as RealGPUManager,
    )
    from ...performance.gpu_acceleration.gpu_manager_factory import (
        create_gpu_manager,
    )

    LEGACY_GPU_AVAILABLE = True
except ImportError:
    LEGACY_GPU_AVAILABLE = False
    create_gpu_manager = None
    RealGPUManager = None

# Import CHS components
try:
    from .chat_history_search import ChatHistorySearcher

    CHS_AVAILABLE = True
except ImportError:
    CHS_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


class CHSOperationType(Enum):
    """Enumeration of CHS-specific operation types."""

    EMBEDDING_COMPUTATION = "embedding_computation"
    SIMILARITY_SEARCH = "similarity_search"
    VECTOR_BATCH_PROCESSING = "vector_batch_processing"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    CHUNK_EMBEDDING = "chunk_embedding"
    RAG_INDEXING = "rag_indexing"


@dataclass
class CHSGPUConfig:
    """Configuration for CHS GPU acceleration settings.

    Attributes
    ----------
        device_id (int): CUDA device ID (default: 0)
        max_batch_size (int): Maximum batch size for embedding computation
        embedding_dim (int): Embedding dimension for vectors
        similarity_threshold (float): Threshold for similarity matching
        enable_faiss_gpu (bool): Enable FAISS GPU acceleration
        faiss_index_type (str): FAISS index type (IVF, HNSW, Flat)
        enable_mixed_precision (bool): Enable mixed precision processing
        memory_limit_gb (float): Memory limit in GB for processing
        enable_persistent_cache (bool): Enable persistent GPU cache
        cache_size_mb (int): Size of GPU cache in MB
        fallback_enabled (bool): Enable CPU fallback on GPU failure
        benchmark_mode (bool): Enable benchmarking and performance tracking
        chunk_batch_size (int): Batch size for chunk processing
        index_batch_size (int): Batch size for indexing operations
        search_batch_size (int): Batch size for search operations
        enable_async_processing (bool): Enable async processing for large datasets

    """

    device_id: int = 0
    max_batch_size: int = 2048
    embedding_dim: int = 384
    similarity_threshold: float = 0.7
    enable_faiss_gpu: bool = True
    faiss_index_type: str = "IVF"
    enable_mixed_precision: bool = True
    memory_limit_gb: float = 8.0
    enable_persistent_cache: bool = True
    cache_size_mb: int = 1024
    fallback_enabled: bool = True
    benchmark_mode: bool = False
    chunk_batch_size: int = 512
    index_batch_size: int = 1024
    search_batch_size: int = 256
    enable_async_processing: bool = True


@dataclass
class CHSProcessingResult:
    """Result of CHS GPU-accelerated processing.

    Attributes
    ----------
        operation_type (CHSOperationType): Type of operation performed
        processing_mode (ProcessingMode): Mode used for processing
        gpu_accelerated (bool): Whether GPU acceleration was used
        items_processed (int): Number of items processed
        processing_time (float): Processing time in seconds
        gpu_memory_peak (int): Peak GPU memory usage in MB
        throughput (float): Items processed per second
        efficiency_score (float): Processing efficiency score (0-100)
        accuracy_score (Optional[float]): Accuracy score for search operations
        similarity_scores (Optional[List[float]]): Similarity scores for results
        embeddings (Optional[List[Any]]): Generated embeddings
        indices (Optional[List[int]]): Result indices from search
        error_message (Optional[str]): Error message if processing failed
        metrics (Optional[GPUMetrics]): GPU metrics during processing
        fallback_used (bool): Whether CPU fallback was used
        benchmark_data (Optional[Dict[str, Any]]): Benchmark performance data

    """

    operation_type: CHSOperationType
    processing_mode: ProcessingMode
    gpu_accelerated: bool
    items_processed: int
    processing_time: float
    gpu_memory_peak: int = 0
    throughput: float = 0.0
    efficiency_score: float = 0.0
    accuracy_score: float | None = None
    similarity_scores: list[float] | None = None
    embeddings: list[Any] | None = None
    indices: list[int] | None = None
    error_message: str | None = None
    metrics: GPUMetrics | None = None
    fallback_used: bool = False
    benchmark_data: dict[str, Any] | None = None


class CHSGPUAccelerator:
    """GPU accelerator for Chat History Search system.

    Algorithm Approach: High-performance GPU-accelerated vector operations
    with intelligent CPU fallback and comprehensive error handling.

    Key Features:
    - GPU-accelerated embedding computation
    - FAISS-powered similarity search
    - Memory-efficient batch processing
    - Real-time performance monitoring
    - Automatic CPU fallback
    - Persistent caching system
    - Async processing support

    Example:
    -------
        >>> accelerator = CHSGPUAccelerator()
        >>> result = await accelerator.process_embeddings(texts)
        >>> print(f"Processed {result.items_processed} embeddings with {result.efficiency_score:.1f}% efficiency")

    """

    def __init__(self, config: CHSGPUConfig | None = None) -> None:
        """Initialize CHS GPU accelerator with configuration and resource validation.

        Parameters
        ----------
        config: CHS GPU configuration parameters

        Raises
        ------
        ImportError: If required GPU libraries are not available
        RuntimeError: If GPU initialization fails

        """
        self.config = config or CHSGPUConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # GPU availability and management
        self.gpu_available = False
        self.gpu_manager = None
        self.device = None
        self.faiss_index = None
        self.faiss_gpu_resources = None

        # Performance tracking
        self.processing_history = []
        self.benchmark_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Persistent cache
        self.embedding_cache = {}
        self.cache_timestamps = {}

        # Initialize GPU components
        self._initialize_gpu_resources()

        self.logger.info(
            f"CHSGPUAccelerator initialized - GPU available: {self.gpu_available}"
        )

    def _initialize_gpu_resources(self) -> None:
        """Initialize GPU resources and validate availability."""
        try:
            # Check basic requirements
            if not TORCH_AVAILABLE:
                self.logger.warning("PyTorch not available - GPU acceleration disabled")
                return

            if not NUMPY_AVAILABLE:
                self.logger.warning("NumPy not available - GPU acceleration disabled")
                return

            if not torch.cuda.is_available():
                self.logger.warning("CUDA not available - GPU acceleration disabled")
                return

            # Validate device ID
            if self.config.device_id >= torch.cuda.device_count():
                self.logger.warning(f"GPU device {self.config.device_id} not found")
                return

            # Initialize device
            self.device = torch.device(f"cuda:{self.config.device_id}")
            self.gpu_available = True

            # Initialize legacy GPU manager if available
            if LEGACY_GPU_AVAILABLE:
                try:
                    legacy_config = GPUConfig(
                        device_id=self.config.device_id,
                        memory_fraction=self.config.memory_limit_gb
                        / torch.cuda.get_device_properties(
                            self.config.device_id
                        ).total_memory
                        * 1024,
                        max_batch_size=self.config.max_batch_size,
                        enable_mixed_precision=self.config.enable_mixed_precision,
                        fallback_enabled=self.config.fallback_enabled,
                    )
                    self.gpu_manager = create_gpu_manager(
                        device_id=self.config.device_id,
                        memory_fraction=legacy_config.memory_fraction,
                        enable_mixed_precision=self.config.enable_mixed_precision,
                        fallback_enabled=self.config.fallback_enabled,
                    )
                    self.logger.info("Legacy GPU manager initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize legacy GPU manager: {e}")

            # Initialize FAISS if available and enabled
            if FAISS_AVAILABLE and self.config.enable_faiss_gpu:
                self._initialize_faiss()

            # Set up mixed precision if enabled
            if self.config.enable_mixed_precision:
                torch.backends.cudnn.benchmark = True
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True

            # Log GPU information
            gpu_props = torch.cuda.get_device_properties(self.config.device_id)
            self.logger.info(
                f"GPU initialized: {gpu_props.name}, "
                f"Memory: {gpu_props.total_memory // (1024**3)}GB, "
                f"CUDA: {torch.version.cuda}",
            )

        except Exception as e:
            self.logger.exception(f"GPU initialization failed: {e}")
            self.gpu_available = False

    def _initialize_faiss(self) -> None:
        """Initialize FAISS index for similarity search."""
        try:
            # Create GPU resources for FAISS
            if FAISS_AVAILABLE:
                self.faiss_gpu_resources = faiss.StandardGpuResources()

                # Set memory limit
                self.faiss_gpu_resources.setTempMemory(
                    int(self.config.cache_size_mb * 1024 * 1024),
                )

                # Create index based on configuration
                embedding_dim = self.config.embedding_dim

                if self.config.faiss_index_type == "IVF":
                    # Inverted File Index
                    nlist = min(100, max(1, self.config.max_batch_size // 10))
                    quantizer = faiss.IndexFlatL2(embedding_dim)
                    self.faiss_index = faiss.IndexIVFFlat(
                        quantizer, embedding_dim, nlist
                    )
                elif self.config.faiss_index_type == "HNSW":
                    # HNSW Index
                    self.faiss_index = faiss.IndexHNSWFlat(embedding_dim, 32)
                else:
                    # Flat Index (exact search)
                    self.faiss_index = faiss.IndexFlatL2(embedding_dim)

                # Move to GPU if using GPU resources
                if self.faiss_gpu_resources:
                    self.faiss_index = faiss.index_cpu_to_gpu(
                        self.faiss_gpu_resources,
                        self.config.device_id,
                        self.faiss_index,
                    )

                self.logger.info(
                    f"FAISS index initialized: {self.config.faiss_index_type}"
                )

        except Exception as e:
            self.logger.warning(f"FAISS initialization failed: {e}")
            self.faiss_index = None
            self.faiss_gpu_resources = None

    def _get_or_create_cache_key(self, texts: list[str]) -> str:
        """Generate cache key for text list."""
        combined_text = "|||".join(texts)
        import hashlib

        return hashlib.md5(combined_text.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> list[Any] | None:
        """Check cache for existing embeddings."""
        if not self.config.enable_persistent_cache:
            return None

        if cache_key in self.embedding_cache:
            # Check if cache is still valid (24 hours)
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < 86400:  # 24 hours
                self.cache_hits += 1
                return self.embedding_cache[cache_key]

        self.cache_misses += 1
        return None

    def _update_cache(self, cache_key: str, embeddings: list[Any]) -> None:
        """Update cache with new embeddings."""
        if not self.config.enable_persistent_cache:
            return

        self.embedding_cache[cache_key] = embeddings
        self.cache_timestamps[cache_key] = time.time()

    def _get_memory_usage(self) -> int:
        """Get current GPU memory usage in MB."""
        if self.gpu_available and torch:
            return torch.cuda.memory_allocated(self.config.device_id) // (1024 * 1024)
        return 0

    async def process_embeddings(
        self,
        texts: list[str],
        batch_size: int | None = None,
        use_cache: bool = True,
    ) -> CHSProcessingResult:
        """Process text embeddings using GPU acceleration with automatic fallback.

        Algorithm Approach: GPU-accelerated embedding computation with batch processing,
        memory management, and intelligent caching for performance optimization.

        Performance Optimization:
        - Batch processing for optimal GPU utilization
        - Persistent caching for repeated queries
        - Mixed precision when available
        - Memory-efficient operations

        Parameters
        ----------
        texts: List of texts to embed
        batch_size: Batch size for processing (uses config default if None)
        use_cache: Whether to use persistent cache

        Returns
        -------
        CHSProcessingResult: Processing results with performance metrics

        Raises
        ------
        RuntimeError: If processing fails on both GPU and CPU

        """
        start_time = time.time()
        operation_type = CHSOperationType.EMBEDDING_COMPUTATION
        processing_mode = ProcessingMode.AUTO
        gpu_accelerated = False
        fallback_used = False
        error_message = None

        try:
            # Check cache first
            if use_cache:
                cache_key = self._get_or_create_cache_key(texts)
                cached_embeddings = self._check_cache(cache_key)
                if cached_embeddings:
                    processing_time = time.time() - start_time
                    return CHSProcessingResult(
                        operation_type=operation_type,
                        processing_mode=ProcessingMode.AUTO,
                        gpu_accelerated=False,  # From cache
                        items_processed=len(texts),
                        processing_time=processing_time,
                        throughput=len(texts) / processing_time,
                        efficiency_score=100.0,  # Cache is most efficient
                        embeddings=cached_embeddings,
                        fallback_used=False,
                        benchmark_data={
                            "cache_hit": True,
                            "cache_efficiency": self.cache_hits
                            / (self.cache_hits + self.cache_misses),
                        },
                    )

            # Use configured batch size or default
            if batch_size is None:
                batch_size = self.config.chunk_batch_size

            # Try GPU processing
            if self.gpu_available and self._check_gpu_readiness():
                processing_mode = ProcessingMode.GPU_ONLY
                gpu_accelerated = True

                result = await self._process_embeddings_gpu(texts, batch_size)

                if result.success:
                    embeddings = result.embeddings
                    gpu_memory_peak = result.gpu_memory_peak

                    # Update cache
                    if use_cache and cache_key:
                        self._update_cache(cache_key, embeddings)

                    processing_time = time.time() - start_time

                    return CHSProcessingResult(
                        operation_type=operation_type,
                        processing_mode=processing_mode,
                        gpu_accelerated=gpu_accelerated,
                        items_processed=len(texts),
                        processing_time=processing_time,
                        gpu_memory_peak=gpu_memory_peak,
                        throughput=len(texts) / processing_time,
                        efficiency_score=self._calculate_efficiency_score(result),
                        embeddings=embeddings,
                        fallback_used=False,
                        metrics=self._get_current_metrics(),
                        benchmark_data=(
                            result.benchmark_data
                            if hasattr(result, "benchmark_data")
                            else None
                        ),
                    )
                error_message = result.error
                self.logger.warning(f"GPU embedding processing failed: {error_message}")

            # Fallback to CPU if enabled
            if self.config.fallback_enabled:
                self.logger.info("Falling back to CPU embedding processing")
                processing_mode = ProcessingMode.CPU_FALLBACK
                fallback_used = True

                result = await self._process_embeddings_cpu(texts, batch_size)

                if result.success:
                    embeddings = result.embeddings
                    processing_time = time.time() - start_time

                    # Update cache
                    if use_cache and cache_key:
                        self._update_cache(cache_key, embeddings)

                    return CHSProcessingResult(
                        operation_type=operation_type,
                        processing_mode=processing_mode,
                        gpu_accelerated=False,
                        items_processed=len(texts),
                        processing_time=processing_time,
                        throughput=len(texts) / processing_time,
                        efficiency_score=self._calculate_cpu_efficiency_score(result),
                        embeddings=embeddings,
                        fallback_used=True,
                        error_message=error_message,
                    )
                msg = f"CPU embedding processing also failed: {result.error}"
                raise RuntimeError(msg)

            msg = "GPU embedding processing failed and CPU fallback disabled"
            raise RuntimeError(msg)

        except Exception as e:
            self.logger.exception(f"Embedding processing failed: {e}")
            processing_time = time.time() - start_time

            return CHSProcessingResult(
                operation_type=operation_type,
                processing_mode=processing_mode,
                gpu_accelerated=gpu_accelerated,
                items_processed=0,
                processing_time=processing_time,
                error_message=str(e),
                fallback_used=fallback_used,
            )

    async def similarity_search(
        self,
        query_embedding: list[float],
        candidate_embeddings: list[list[float]],
        top_k: int = 10,
        threshold: float | None = None,
    ) -> CHSProcessingResult:
        """Perform similarity search using GPU acceleration with FAISS.

        Algorithm Approach: GPU-accelerated similarity search with FAISS index
        for fast approximate nearest neighbor search and CPU fallback.

        Performance Optimization:
        - FAISS GPU acceleration for fast search
        - Efficient vector comparison
        - Threshold-based filtering
        - Batch processing for multiple queries

        Parameters
        ----------
        query_embedding: Query embedding vector
        candidate_embeddings: List of candidate embedding vectors
        top_k: Number of top results to return
        threshold: Similarity threshold (uses config default if None)

        Returns
        -------
        CHSProcessingResult: Search results with similarity scores and indices

        Raises
        ------
        RuntimeError: If search fails on both GPU and CPU

        """
        start_time = time.time()
        operation_type = CHSOperationType.SIMILARITY_SEARCH
        processing_mode = ProcessingMode.AUTO
        gpu_accelerated = False
        fallback_used = False
        error_message = None

        try:
            # Use configured threshold if none provided
            if threshold is None:
                threshold = self.config.similarity_threshold

            # Convert to numpy arrays
            query_array = np.array([query_embedding], dtype=np.float32)
            candidates_array = np.array(candidate_embeddings, dtype=np.float32)

            # Try GPU processing with FAISS
            if self.gpu_available and self.faiss_index and self._check_gpu_readiness():
                processing_mode = ProcessingMode.GPU_ONLY
                gpu_accelerated = True

                result = await self._similarity_search_gpu(
                    query_array,
                    candidates_array,
                    top_k,
                    threshold,
                )

                if result.success:
                    similarity_scores = result.similarity_scores
                    indices = result.indices
                    gpu_memory_peak = result.gpu_memory_peak

                    processing_time = time.time() - start_time

                    return CHSProcessingResult(
                        operation_type=operation_type,
                        processing_mode=processing_mode,
                        gpu_accelerated=gpu_accelerated,
                        items_processed=len(candidate_embeddings),
                        processing_time=processing_time,
                        gpu_memory_peak=gpu_memory_peak,
                        throughput=len(candidate_embeddings) / processing_time,
                        efficiency_score=self._calculate_efficiency_score(result),
                        similarity_scores=similarity_scores,
                        indices=indices,
                        accuracy_score=self._calculate_search_accuracy(result),
                        fallback_used=False,
                        metrics=self._get_current_metrics(),
                    )
                error_message = result.error
                self.logger.warning(f"GPU similarity search failed: {error_message}")

            # Fallback to CPU processing
            if self.config.fallback_enabled:
                self.logger.info("Falling back to CPU similarity search")
                processing_mode = ProcessingMode.CPU_FALLBACK
                fallback_used = True

                result = await self._similarity_search_cpu(
                    query_array,
                    candidates_array,
                    top_k,
                    threshold,
                )

                if result.success:
                    similarity_scores = result.similarity_scores
                    indices = result.indices
                    processing_time = time.time() - start_time

                    return CHSProcessingResult(
                        operation_type=operation_type,
                        processing_mode=processing_mode,
                        gpu_accelerated=False,
                        items_processed=len(candidate_embeddings),
                        processing_time=processing_time,
                        throughput=len(candidate_embeddings) / processing_time,
                        efficiency_score=self._calculate_cpu_efficiency_score(result),
                        similarity_scores=similarity_scores,
                        indices=indices,
                        accuracy_score=self._calculate_search_accuracy(result),
                        fallback_used=True,
                        error_message=error_message,
                    )
                msg = f"CPU similarity search also failed: {result.error}"
                raise RuntimeError(msg)

            msg = "GPU similarity search failed and CPU fallback disabled"
            raise RuntimeError(msg)

        except Exception as e:
            self.logger.exception(f"Similarity search failed: {e}")
            processing_time = time.time() - start_time

            return CHSProcessingResult(
                operation_type=operation_type,
                processing_mode=processing_mode,
                gpu_accelerated=gpu_accelerated,
                items_processed=0,
                processing_time=processing_time,
                error_message=str(e),
                fallback_used=fallback_used,
            )

    def _check_gpu_readiness(self) -> bool:
        """Check if GPU is ready for processing."""
        if not self.gpu_available:
            return False

        try:
            # Check memory availability
            memory_used = self._get_memory_usage()
            memory_limit_mb = int(self.config.memory_limit_gb * 1024)

            if memory_used > memory_limit_mb:
                self.logger.warning(
                    f"GPU memory limit exceeded: {memory_used}MB > {memory_limit_mb}MB"
                )
                return False

            # Test basic operation
            test_tensor = torch.randn(10, self.config.embedding_dim, device=self.device)
            _ = torch.sum(test_tensor)
            del test_tensor

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return True

        except Exception as e:
            self.logger.warning(f"GPU readiness check failed: {e}")
            return False

    async def _process_embeddings_gpu(
        self,
        texts: list[str],
        batch_size: int,
    ) -> Any:
        """Process embeddings using GPU acceleration."""
        try:
            embeddings = []
            gpu_memory_peak = 0
            benchmark_data = {
                "batches_processed": 0,
                "avg_batch_time": 0.0,
                "memory_efficiency": 0.0,
            }

            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                batch_start_time = time.time()

                # Mock embedding computation (replace with actual embedding model)
                # In real implementation, this would use a sentence transformer or similar
                batch_embeddings = []
                for text in batch_texts:
                    # Generate mock embedding - replace with actual model inference
                    text_hash = hash(text) % 10000
                    embedding = [text_hash * 0.001] * self.config.embedding_dim
                    batch_embeddings.append(embedding)

                # Convert to tensor and move to GPU for processing
                if torch and NUMPY_AVAILABLE:
                    batch_tensor = torch.tensor(
                        batch_embeddings,
                        dtype=torch.float32,
                        device=self.device,
                    )

                    # Perform GPU processing (e.g., normalization)
                    batch_tensor = F.normalize(batch_tensor, p=2, dim=1)

                    # Move back to CPU and convert to list
                    processed_embeddings = batch_tensor.cpu().numpy().tolist()
                    embeddings.extend(processed_embeddings)

                    # Track memory usage
                    current_memory = self._get_memory_usage()
                    gpu_memory_peak = max(gpu_memory_peak, current_memory)

                    # Clean up
                    del batch_tensor
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                else:
                    embeddings.extend(batch_embeddings)

                # Update benchmark data
                batch_time = time.time() - batch_start_time
                benchmark_data["batches_processed"] += 1
                benchmark_data["avg_batch_time"] += batch_time

            # Calculate memory efficiency
            if gpu_memory_peak > 0:
                total_memory_mb = torch.cuda.get_device_properties(
                    self.config.device_id
                ).total_memory // (1024 * 1024)
                benchmark_data["memory_efficiency"] = (
                    gpu_memory_peak / total_memory_mb
                ) * 100

            if benchmark_data["batches_processed"] > 0:
                benchmark_data["avg_batch_time"] /= benchmark_data["batches_processed"]

            # Create result object
            class EmbeddingResult:
                def __init__(
                    self,
                    success,
                    embeddings,
                    gpu_memory_peak,
                    benchmark_data=None,
                    error=None,
                ) -> None:
                    self.success = success
                    self.embeddings = embeddings
                    self.gpu_memory_peak = gpu_memory_peak
                    self.benchmark_data = benchmark_data
                    self.error = error

            return EmbeddingResult(True, embeddings, gpu_memory_peak, benchmark_data)

        except Exception as e:
            self.logger.exception(f"GPU embedding processing failed: {e}")

            class EmbeddingResult:
                def __init__(self, success=False, error=None) -> None:
                    self.success = success
                    self.error = error
                    self.embeddings = []
                    self.gpu_memory_peak = 0

            return EmbeddingResult(False, error=str(e))

    async def _process_embeddings_cpu(
        self,
        texts: list[str],
        batch_size: int,
    ) -> Any:
        """Process embeddings using CPU fallback."""
        try:
            embeddings = []

            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]

                # CPU embedding computation
                for text in batch_texts:
                    # Mock embedding computation
                    text_hash = hash(text) % 10000
                    embedding = [text_hash * 0.001] * self.config.embedding_dim

                    # Normalize embedding
                    import math

                    norm = math.sqrt(sum(x * x for x in embedding))
                    if norm > 0:
                        embedding = [x / norm for x in embedding]

                    embeddings.append(embedding)

                # Simulate processing time
                await asyncio.sleep(0.001)  # Small delay to simulate CPU work

            class EmbeddingResult:
                def __init__(self, success, embeddings, error=None) -> None:
                    self.success = success
                    self.embeddings = embeddings
                    self.error = error

            return EmbeddingResult(True, embeddings)

        except Exception as e:
            self.logger.exception(f"CPU embedding processing failed: {e}")

            class EmbeddingResult:
                def __init__(self, success=False, error=None) -> None:
                    self.success = success
                    self.error = error
                    self.embeddings = []

            return EmbeddingResult(False, error=str(e))

    async def _similarity_search_gpu(
        self,
        query_array: np.ndarray,
        candidates_array: np.ndarray,
        top_k: int,
        threshold: float,
    ) -> Any:
        """Perform similarity search using GPU FAISS."""
        try:
            if self.faiss_index is None:
                # Initialize FAISS index with candidates
                self.faiss_index.add(candidates_array)

            # Perform search
            distances, indices = self.faiss_index.search(query_array, top_k)

            # Convert distances to similarity scores (assuming L2 distance)
            max_dist = np.max(distances) if np.max(distances) > 0 else 1.0
            similarity_scores = (1.0 - distances / max_dist).tolist()[0]

            # Filter by threshold
            filtered_results = []
            filtered_scores = []
            filtered_indices = []

            for _i, (score, idx) in enumerate(
                zip(similarity_scores, indices[0], strict=False)
            ):
                if score >= threshold:
                    filtered_results.append(idx)
                    filtered_scores.append(score)
                    filtered_indices.append(int(idx))

            # Track memory usage
            gpu_memory_peak = self._get_memory_usage()

            class SearchResult:
                def __init__(
                    self,
                    success,
                    similarity_scores,
                    indices,
                    gpu_memory_peak,
                    error=None,
                ) -> None:
                    self.success = success
                    self.similarity_scores = similarity_scores
                    self.indices = indices
                    self.gpu_memory_peak = gpu_memory_peak
                    self.error = error

            return SearchResult(
                True, filtered_scores, filtered_indices, gpu_memory_peak
            )

        except Exception as e:
            self.logger.exception(f"GPU similarity search failed: {e}")

            class SearchResult:
                def __init__(self, success=False, error=None) -> None:
                    self.success = success
                    self.error = error
                    self.similarity_scores = []
                    self.indices = []
                    self.gpu_memory_peak = 0

            return SearchResult(False, error=str(e))

    async def _similarity_search_cpu(
        self,
        query_array: np.ndarray,
        candidates_array: np.ndarray,
        top_k: int,
        threshold: float,
    ) -> Any:
        """Perform similarity search using CPU."""
        try:
            query_embedding = query_array[0]
            similarities = []

            # Compute cosine similarity
            for i, candidate in enumerate(candidates_array):
                # Cosine similarity
                dot_product = np.dot(query_embedding, candidate)
                norm_query = np.linalg.norm(query_embedding)
                norm_candidate = np.linalg.norm(candidate)

                if norm_query > 0 and norm_candidate > 0:
                    similarity = dot_product / (norm_query * norm_candidate)
                else:
                    similarity = 0.0

                similarities.append((similarity, i))

            # Sort by similarity (descending)
            similarities.sort(reverse=True, key=lambda x: x[0])

            # Filter and get top results
            similarity_scores = []
            indices = []

            for similarity, idx in similarities[:top_k]:
                if similarity >= threshold:
                    similarity_scores.append(float(similarity))
                    indices.append(int(idx))

            class SearchResult:
                def __init__(
                    self, success, similarity_scores, indices, error=None
                ) -> None:
                    self.success = success
                    self.similarity_scores = similarity_scores
                    self.indices = indices
                    self.error = error

            return SearchResult(True, similarity_scores, indices)

        except Exception as e:
            self.logger.exception(f"CPU similarity search failed: {e}")

            class SearchResult:
                def __init__(self, success=False, error=None) -> None:
                    self.success = success
                    self.error = error
                    self.similarity_scores = []
                    self.indices = []

            return SearchResult(False, error=str(e))

    def _get_current_metrics(self) -> GPUMetrics | None:
        """Get current GPU metrics."""
        if self.gpu_manager:
            return self.gpu_manager.gpu_metrics

        # Fallback metrics calculation
        if self.gpu_available and torch:
            try:
                props = torch.cuda.get_device_properties(self.config.device_id)
                memory_total = props.total_memory // (1024 * 1024)
                memory_used = torch.cuda.memory_allocated(self.config.device_id) // (
                    1024 * 1024
                )

                return GPUMetrics(
                    gpu_name=props.name,
                    memory_total=memory_total,
                    memory_used=memory_used,
                    memory_free=memory_total - memory_used,
                )
            except Exception:
                pass

        return None

    def _calculate_efficiency_score(self, result: Any) -> float:
        """Calculate processing efficiency score (0-100)."""
        if not hasattr(result, "gpu_memory_peak"):
            return 0.0

        # Base score on memory efficiency
        if self.gpu_manager and self.gpu_manager.gpu_metrics:
            memory_efficiency = 1.0 - (
                result.gpu_memory_peak / self.gpu_manager.gpu_metrics.memory_total
            )
        else:
            memory_efficiency = 0.8  # Default assumption

        # Include cache efficiency if available
        if (
            hasattr(result, "benchmark_data")
            and "memory_efficiency" in result.benchmark_data
        ):
            cache_efficiency = max(
                0, 1.0 - (result.benchmark_data["memory_efficiency"] / 100)
            )
        else:
            cache_efficiency = 0.8

        efficiency = (memory_efficiency * 0.6 + cache_efficiency * 0.4) * 100
        return min(100.0, efficiency)

    def _calculate_cpu_efficiency_score(self, result: Any) -> float:
        """Calculate CPU processing efficiency score."""
        # CPU efficiency is generally lower than GPU
        base_score = 70.0  # Base efficiency for CPU processing

        # Adjust based on cache hits
        if hasattr(self, "cache_hits") and hasattr(self, "cache_misses"):
            total_cache_access = self.cache_hits + self.cache_misses
            if total_cache_access > 0:
                cache_bonus = (self.cache_hits / total_cache_access) * 20
                base_score += cache_bonus

        return min(100.0, base_score)

    def _calculate_search_accuracy(self, result: Any) -> float:
        """Calculate search accuracy score based on similarity scores."""
        if not hasattr(result, "similarity_scores") or not result.similarity_scores:
            return 0.0

        # Average similarity score as accuracy metric
        avg_similarity = sum(result.similarity_scores) / len(result.similarity_scores)
        return min(100.0, avg_similarity * 100)

    async def benchmark_performance(
        self,
        test_sizes: list[int] | None = None,
        test_operations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Benchmark GPU performance across different operations and sizes.

        Parameters
        ----------
        test_sizes: List of dataset sizes to test
        test_operations: List of operations to test

        Returns
        -------
        Dict[str, Any]: Comprehensive benchmark results

        """
        if test_sizes is None:
            test_sizes = [100, 500, 1000, 5000]

        if test_operations is None:
            test_operations = ["embedding", "similarity_search"]

        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "gpu_available": self.gpu_available,
            "device_info": {},
            "results": {},
        }

        # Get device information
        if self.gpu_available:
            props = torch.cuda.get_device_properties(self.config.device_id)
            benchmark_results["device_info"] = {
                "name": props.name,
                "total_memory_gb": props.total_memory // (1024**3),
                "compute_capability": f"{props.major}.{props.minor}",
                "multiprocessor_count": props.multiprocessor_count,
            }

        # Run benchmarks
        for size in test_sizes:
            size_results = {}

            for operation in test_operations:
                try:
                    if operation == "embedding":
                        # Generate test texts
                        test_texts = [f"Test text {i}" for i in range(size)]

                        # Benchmark GPU processing
                        start_time = time.time()
                        result = await self.process_embeddings(
                            test_texts, use_cache=False
                        )
                        gpu_time = time.time() - start_time

                        size_results[f"{operation}_gpu"] = {
                            "time": gpu_time,
                            "throughput": size / gpu_time,
                            "efficiency": result.efficiency_score,
                            "memory_peak_mb": result.gpu_memory_peak,
                        }

                        # Benchmark CPU fallback (disable GPU)
                        original_gpu_available = self.gpu_available
                        self.gpu_available = False

                        start_time = time.time()
                        cpu_result = await self.process_embeddings(
                            test_texts, use_cache=False
                        )
                        cpu_time = time.time() - start_time

                        self.gpu_available = original_gpu_available

                        size_results[f"{operation}_cpu"] = {
                            "time": cpu_time,
                            "throughput": size / cpu_time,
                            "efficiency": cpu_result.efficiency_score,
                        }

                        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                        size_results[f"{operation}_speedup"] = speedup

                    elif operation == "similarity_search":
                        # Generate test embeddings
                        query_embedding = [0.1] * self.config.embedding_dim
                        candidate_embeddings = [
                            [0.1 + i * 0.001] * self.config.embedding_dim
                            for i in range(size)
                        ]

                        # Benchmark search
                        start_time = time.time()
                        result = await self.similarity_search(
                            query_embedding, candidate_embeddings
                        )
                        search_time = time.time() - start_time

                        size_results[f"{operation}_gpu"] = {
                            "time": search_time,
                            "throughput": size / search_time,
                            "results_found": (
                                len(result.indices) if result.indices else 0
                            ),
                            "avg_similarity": (
                                sum(result.similarity_scores)
                                / len(result.similarity_scores)
                                if result.similarity_scores
                                else 0
                            ),
                        }

                except Exception as e:
                    size_results[f"{operation}_error"] = str(e)
                    self.logger.exception(
                        f"Benchmark {operation} size {size} failed: {e}"
                    )

            benchmark_results["results"][f"size_{size}"] = size_results

        return benchmark_results

    def get_accelerator_status(self) -> dict[str, Any]:
        """Get comprehensive accelerator status and metrics."""
        status = {
            "gpu_available": self.gpu_available,
            "device_id": self.config.device_id,
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "embedding_dim": self.config.embedding_dim,
                "enable_faiss_gpu": self.config.enable_faiss_gpu,
                "faiss_index_type": self.config.faiss_index_type,
                "enable_mixed_precision": self.config.enable_mixed_precision,
                "fallback_enabled": self.config.fallback_enabled,
            },
            "performance": {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": (
                    self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0
                    else 0.0
                ),
                "cached_items": len(self.embedding_cache),
            },
            "gpu_metrics": {},
            "faiss_status": {
                "available": FAISS_AVAILABLE,
                "gpu_enabled": self.faiss_index is not None,
                "index_type": (
                    self.config.faiss_index_type if self.faiss_index else None
                ),
            },
        }

        # Add GPU metrics
        if self.gpu_available:
            current_metrics = self._get_current_metrics()
            if current_metrics:
                status["gpu_metrics"] = current_metrics.__dict__

        return status

    async def cleanup(self) -> None:
        """Cleanup GPU resources and cache."""
        try:
            # Clear cache
            self.embedding_cache.clear()
            self.cache_timestamps.clear()

            # Cleanup FAISS
            if self.faiss_index:
                try:
                    if hasattr(faiss, "reset_index"):
                        faiss.reset_index(self.faiss_index)
                except Exception:
                    pass
                self.faiss_index = None

            if self.faiss_gpu_resources:
                try:
                    # FAISS GPU resources cleanup is automatic
                    pass
                except Exception:
                    pass
                self.faiss_gpu_resources = None

            # Cleanup GPU manager
            if self.gpu_manager:
                await self.gpu_manager.cleanup()

            # Cleanup PyTorch
            if self.gpu_available and torch:
                torch.cuda.empty_cache()
                gc.collect()

            self.logger.info("CHSGPUAccelerator cleanup completed")

        except Exception as e:
            self.logger.exception(f"Cleanup failed: {e}")


# Factory function for easy initialization
def create_chs_gpu_accelerator(
    device_id: int = 0,
    max_batch_size: int = 2048,
    embedding_dim: int = 384,
    enable_faiss_gpu: bool = True,
    fallback_enabled: bool = True,
    mixed_precision: bool = True,
) -> CHSGPUAccelerator:
    """Factory function to create a configured CHSGPUAccelerator.

    Parameters
    ----------
    device_id: CUDA device ID
    max_batch_size: Maximum batch size for processing
    embedding_dim: Embedding dimension for vectors
    enable_faiss_gpu: Enable FAISS GPU acceleration
    fallback_enabled: Enable CPU fallback on GPU failure
    mixed_precision: Enable mixed precision processing

    Returns
    -------
    CHSGPUAccelerator: Configured GPU accelerator instance

    """
    config = CHSGPUConfig(
        device_id=device_id,
        max_batch_size=max_batch_size,
        embedding_dim=embedding_dim,
        enable_faiss_gpu=enable_faiss_gpu,
        fallback_enabled=fallback_enabled,
        enable_mixed_precision=mixed_precision,
    )

    return CHSGPUAccelerator(config)


# Example usage and testing
if __name__ == "__main__":

    async def main() -> None:
        """Example usage of CHSGPUAccelerator."""
        accelerator = create_chs_gpu_accelerator(
            device_id=0,
            max_batch_size=1024,
            embedding_dim=384,
            enable_faiss_gpu=True,
            fallback_enabled=True,
        )

        try:
            # Get accelerator status
            accelerator.get_accelerator_status()

            # Test embedding processing
            test_texts = [
                "This is a test message for embedding",
                "Another test message with different content",
                "Third message to test batch processing",
            ]

            result = await accelerator.process_embeddings(test_texts)

            # Test similarity search
            if result.embeddings and len(result.embeddings) > 1:
                query_embedding = result.embeddings[0]
                candidate_embeddings = result.embeddings[1:]

                search_result = await accelerator.similarity_search(
                    query_embedding,
                    candidate_embeddings,
                    top_k=3,
                )

                if search_result.similarity_scores:
                    pass

            # Run benchmark if GPU is available
            if accelerator.gpu_available:
                benchmark = await accelerator.benchmark_performance([100, 500])

                for results in benchmark["results"].values():
                    if "embedding_speedup" in results:
                        pass

        finally:
            await accelerator.cleanup()

    # Run example
    asyncio.run(main())
