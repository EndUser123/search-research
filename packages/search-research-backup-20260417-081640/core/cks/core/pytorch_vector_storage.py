import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import psutil

from ..utils.constitutional_validator import ConstitutionalValidator

"""PyTorch-based Vector Storage for CKS System
FAISS GPU replacement with PyTorch tensor operations

Constitutional Requirements:
- Solo developer optimization (zero background services)
- Evidence-based implementation (TDD approach)
- Force multiplier integration (GPU acceleration)
- No enterprise bloat (simple, direct implementation)

Architecture:
Phase 1: Single PC deployment, no clustering
- On-demand processing (no background services)
- GPU acceleration with CPU fallback
- Direct Python integration (no external dependencies)
- Constitutional compliance mandatory
"""


try:
    import torch
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - vector operations will be limited")


@dataclass
class PyTorchStorageConfig:
    """Configuration for PyTorch vector storage system.

    Constitutional Requirements:
    - Solo developer optimized defaults
    - Conservative resource usage
    - GPU with CPU fallback
    """

    db_path: str = field(
        default_factory=lambda: os.path.expanduser("P:/__csf/data/cks.db"),
    )
    tensor_cache_path: str = field(
        default_factory=lambda: os.path.expanduser("~/.cks/storage/tensors.pt"),
    )
    enable_gpu: bool = True
    max_memory_mb: int = 4096  # Conservative for solo developer
    vector_dimension: int = 768  # Standard embedding size
    batch_size: int = 1000
    audit_trail_enabled: bool = True
    auto_cleanup: bool = True
    similarity_threshold: float = 0.7
    enable_mixed_precision: bool = False
    cache_size: int = 10000

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        if self.vector_dimension <= 0:
            raise ValueError("vector_dimension must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.tensor_cache_path), exist_ok=True)


class DeviceManager:
    """Manages GPU/CPU device selection and fallback mechanisms.

    Constitutional Requirements:
    - Solo developer optimization (automatic resource management)
    - Evidence-based device selection (performance benchmarking)
    - Force multiplier integration (GPU acceleration when available)
    """

    def __init__(self, prefer_gpu: bool = True, memory_threshold: float = 0.9) -> None:
        self.prefer_gpu = prefer_gpu
        self.memory_threshold = memory_threshold
        self.device = self._select_device()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _select_device(self) -> torch.device:
        """Select optimal device with constitutional resource management."""
        if not TORCH_AVAILABLE:
            return torch.device("cpu")

        if not self.prefer_gpu:
            return torch.device("cpu")

        if not torch.cuda.is_available():
            if hasattr(self, "logger"):
                self.logger.info("CUDA not available, using CPU")
            return torch.device("cpu")

        # Check GPU memory availability
        try:
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            allocated_memory = torch.cuda.memory_allocated(0)
            gpu_memory - allocated_memory
            memory_usage = allocated_memory / gpu_memory

            if memory_usage > self.memory_threshold:
                if hasattr(self, "logger"):
                    self.logger.warning(
                        f"GPU memory usage ({memory_usage:.2%}) exceeds threshold ({self.memory_threshold:.2%}), using CPU",
                    )
                return torch.device("cpu")

            if hasattr(self, "logger"):
                self.logger.info(
                    f"Using GPU (CUDA available, memory usage: {memory_usage:.2%})",
                )
            return torch.device("cuda:0")

        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.warning(f"GPU selection failed, using CPU: {e}")
            return torch.device("cpu")

    def execute_with_fallback(self, operation, *args, **kwargs):
        """Execute operation with automatic CPU fallback on GPU OOM."""
        try:
            if self.device.type == "cuda":
                return operation(*args, **kwargs)
            # Force CPU execution if already on CPU
            return operation(*args, **kwargs)
        except torch.cuda.OutOfMemoryError:
            if hasattr(self, "logger"):
                self.logger.warning("GPU OOM, falling back to CPU")
            # Move tensors to CPU and retry
            return self._execute_on_cpu(operation, *args, **kwargs)
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.exception(f"Operation failed: {e}")
            raise

    def _execute_on_cpu(self, operation, *args, **kwargs):
        """Execute operation on CPU with tensor conversion."""
        cpu_args = []
        for arg in args:
            if isinstance(arg, torch.Tensor) and arg.is_cuda:
                cpu_args.append(arg.cpu())
            else:
                cpu_args.append(arg)

        cpu_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, torch.Tensor) and v.is_cuda:
                cpu_kwargs[k] = v.cpu()
            else:
                cpu_kwargs[k] = v

        return operation(*cpu_args, **cpu_kwargs)


class PyTorchVectorStorage:
    """PyTorch-based vector storage with GPU acceleration.

    Replaces FAISS GPU functionality with PyTorch tensor operations.
    Maintains constitutional compliance and solo developer optimization.
    """

    def __init__(self, config: PyTorchStorageConfig) -> None:
        """Initialize PyTorch vector storage with constitutional validation."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.constitutional_validator = ConstitutionalValidator()

        # Constitutional validation
        if not self.constitutional_validator.validate_storage_config(config):
            raise ValueError("Storage configuration failed constitutional validation")

        # Initialize device manager
        self.device_manager = DeviceManager(
            prefer_gpu=config.enable_gpu,
            memory_threshold=0.8,
        )

        # Initialize storage components
        self.vectors_tensor: torch.Tensor | None = None
        self.vector_ids: list[str] = []
        self.vector_metadata: dict[str, dict] = {}
        self.similarity_cache: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
        self.access_count: dict[str, int] = {}
        self.last_access: dict[str, float] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Performance tracking
        self.operation_stats = {
            "searches": 0,
            "additions": 0,
            "gpu_operations": 0,
            "cpu_fallbacks": 0,
            "cache_hits": 0,
        }

        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize PyTorch tensor storage."""
        try:
            device = self.device_manager.device

            # Initialize empty tensor on appropriate device
            self.vectors_tensor = torch.empty(
                (0, self.config.vector_dimension),
                dtype=torch.float32,
                device=device,
            )

            self.logger.info(f"PyTorch vector storage initialized on {device}")

            # Try to load cached tensors if available
            self._load_cached_tensors()

        except Exception as e:
            self.logger.exception(f"Storage initialization failed: {e}")
            raise

    def _load_cached_tensors(self) -> None:
        """Load cached tensors from disk if available."""
        if os.path.exists(self.config.tensor_cache_path):
            try:
                checkpoint = torch.load(
                    self.config.tensor_cache_path,
                    map_location=self.device_manager.device,
                )
                self.vectors_tensor = checkpoint["vectors"].to(
                    self.device_manager.device,
                )
                self.vector_ids = checkpoint["ids"]
                self.vector_metadata = checkpoint.get("metadata", {})

                self.logger.info(f"Loaded {len(self.vector_ids)} cached vectors")

            except Exception as e:
                self.logger.warning(f"Failed to load cached tensors: {e}")

    def _save_cached_tensors(self) -> None:
        """Save current tensors to disk for persistence."""
        try:
            checkpoint = {
                "vectors": self.vectors_tensor.cpu(),
                "ids": self.vector_ids,
                "metadata": self.vector_metadata,
                "timestamp": time.time(),
            }

            torch.save(checkpoint, self.config.tensor_cache_path)
            self.logger.debug("Saved tensors to cache")

        except Exception as e:
            self.logger.warning(f"Failed to save cached tensors: {e}")

    def store_vector(
        self,
        vector_id: str,
        vector: np.ndarray,
        metadata: dict | None = None,
    ) -> bool:
        """Store a vector with constitutional compliance validation.

        Args:
            vector_id: Unique identifier for the vector
            vector: Vector data as numpy array
            metadata: Optional metadata dictionary

        Returns:
            Boolean indicating success

        """
        with self._lock:
            try:
                # Constitutional validation
                if not self._validate_vector_storage(vector_id, vector):
                    return False

                # Convert to tensor
                if isinstance(vector, np.ndarray):
                    tensor = torch.from_numpy(vector.astype(np.float32))
                else:
                    tensor = torch.tensor(vector, dtype=torch.float32)

                # Ensure correct dimension
                if tensor.dim() == 1:
                    tensor = tensor.unsqueeze(0)

                # Move to device
                tensor = tensor.to(self.device_manager.device)

                # Store vector
                self._add_vector_internal(vector_id, tensor, metadata or {})

                # Update statistics
                self.operation_stats["additions"] += 1

                self.logger.debug(
                    f"Stored vector {vector_id} on {self.device_manager.device}",
                )
                return True

            except Exception as e:
                self.logger.exception(f"Failed to store vector {vector_id}: {e}")
                return False

    def _validate_vector_storage(self, vector_id: str, vector: np.ndarray) -> bool:
        """Validate vector storage against constitutional requirements."""
        # Constitutional compliance check
        if not self.constitutional_validator.validate_vector_storage(vector_id, vector):
            return False

        # Dimension validation
        if len(vector) != self.config.vector_dimension:
            self.logger.error(
                f"Vector dimension mismatch: expected {self.config.vector_dimension}, got {len(vector)}",
            )
            return False

        return True

    def _add_vector_internal(
        self,
        vector_id: str,
        tensor: torch.Tensor,
        metadata: dict,
    ) -> None:
        """Internal method to add vector with thread safety."""
        # Check if vector already exists
        if vector_id in self.vector_ids:
            idx = self.vector_ids.index(vector_id)
            self.vectors_tensor[idx] = tensor.squeeze(0)
        else:
            # Add new vector
            if self.vectors_tensor.size(0) == 0:
                self.vectors_tensor = tensor
            else:
                self.vectors_tensor = torch.cat([self.vectors_tensor, tensor], dim=0)

            self.vector_ids.append(vector_id)

        # Store metadata
        self.vector_metadata[vector_id] = metadata

        # Update access tracking
        self.access_count[vector_id] = 0
        self.last_access[vector_id] = time.time()

        # Clear cache for consistency
        self.similarity_cache.clear()

    def search_similar_vectors(
        self,
        query_vector: np.ndarray,
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for similar vectors using PyTorch operations.

        Args:
            query_vector: Query vector as numpy array
            k: Number of similar vectors to return

        Returns:
            List of (vector_id, similarity_score) tuples

        """
        with self._lock:
            try:
                if self.vectors_tensor is None or len(self.vector_ids) == 0:
                    return []

                # Convert query to tensor
                if isinstance(query_vector, np.ndarray):
                    query_tensor = torch.from_numpy(query_vector.astype(np.float32))
                else:
                    query_tensor = torch.tensor(query_vector, dtype=torch.float32)

                if query_tensor.dim() == 1:
                    query_tensor = query_tensor.unsqueeze(0)

                query_tensor = query_tensor.to(self.device_manager.device)

                # Perform search with fallback
                results = self.device_manager.execute_with_fallback(
                    self._perform_similarity_search,
                    query_tensor,
                    k,
                )

                # Update statistics
                self.operation_stats["searches"] += 1

                return results

            except Exception as e:
                self.logger.exception(f"Vector search failed: {e}")
                return []

    def _perform_similarity_search(
        self,
        query_tensor: torch.Tensor,
        k: int,
    ) -> list[tuple[str, float]]:
        """Perform similarity search using optimized PyTorch operations."""
        if self.vectors_tensor.size(0) == 0:
            return []

        # Adjust k if necessary
        k = min(k, self.vectors_tensor.size(0))

        # Normalize vectors for cosine similarity
        query_norm = F.normalize(query_tensor, p=2, dim=1)
        vectors_norm = F.normalize(self.vectors_tensor, p=2, dim=1)

        # Compute cosine similarity
        similarities = torch.mm(query_norm, vectors_norm.t()).squeeze(0)

        # Get top-k similarities
        top_k_similarities, top_k_indices = torch.topk(similarities, k)

        # Convert to list of (vector_id, similarity) tuples
        results = []
        for score, idx in zip(
            top_k_similarities.cpu().numpy(),
            top_k_indices.cpu().numpy(),
            strict=False,
        ):
            vector_id = self.vector_ids[idx]
            similarity_score = float(score)

            # Update access tracking
            self.access_count[vector_id] = self.access_count.get(vector_id, 0) + 1
            self.last_access[vector_id] = time.time()

            results.append((vector_id, similarity_score))

        return results

    def get_vector(self, vector_id: str) -> np.ndarray | None:
        """Retrieve a stored vector by ID."""
        with self._lock:
            try:
                if vector_id not in self.vector_ids:
                    return None

                idx = self.vector_ids.index(vector_id)
                vector_tensor = self.vectors_tensor[idx]

                # Convert to numpy and return
                return vector_tensor.cpu().numpy()

            except Exception as e:
                self.logger.exception(f"Failed to retrieve vector {vector_id}: {e}")
                return None

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a stored vector by ID."""
        with self._lock:
            try:
                if vector_id not in self.vector_ids:
                    return False

                idx = self.vector_ids.index(vector_id)

                # Remove from tensor
                mask = torch.ones(self.vectors_tensor.size(0), dtype=torch.bool)
                mask[idx] = False
                self.vectors_tensor = self.vectors_tensor[mask]

                # Remove from metadata
                del self.vector_ids[idx]
                self.vector_metadata.pop(vector_id, None)
                self.access_count.pop(vector_id, None)
                self.last_access.pop(vector_id, None)

                # Clear cache
                self.similarity_cache.clear()

                self.logger.debug(f"Deleted vector {vector_id}")
                return True

            except Exception as e:
                self.logger.exception(f"Failed to delete vector {vector_id}: {e}")
                return False

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            return {
                "total_vectors": len(self.vector_ids),
                "vector_dimension": self.config.vector_dimension,
                "device": str(self.device_manager.device),
                "storage_size_mb": (
                    self.vectors_tensor.numel() * 4 / (1024 * 1024)
                    if self.vectors_tensor is not None
                    else 0
                ),
                "cache_size": len(self.similarity_cache),
                "operation_stats": self.operation_stats.copy(),
                "constitutional_compliance": self._check_constitutional_compliance(),
            }

    def _check_constitutional_compliance(self) -> dict[str, Any]:
        """Check constitutional compliance status."""
        try:
            # Memory usage check
            memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_compliant = memory_usage < self.config.max_memory_mb

            # Solo developer optimization check
            resource_efficient = (
                len(self.vector_ids) > 0 or memory_usage < 100
            )  # Less than 100MB if empty

            return {
                "memory_usage_mb": memory_usage,
                "memory_compliant": memory_compliant,
                "resource_efficient": resource_efficient,
                "compliance_score": (1.0 if memory_compliant and resource_efficient else 0.5),
            }
        except Exception as e:
            self.logger.warning(f"Constitutional compliance check failed: {e}")
            return {"compliance_score": 0.0, "error": str(e)}

    def cleanup(self) -> None:
        """Cleanup resources and save state."""
        with self._lock:
            try:
                # Save cached tensors
                self._save_cached_tensors()

                # Clear GPU memory if using CUDA
                if self.device_manager.device.type == "cuda":
                    if self.vectors_tensor is not None:
                        self.vectors_tensor = self.vectors_tensor.cpu()
                    torch.cuda.empty_cache()

                # Clear references
                self.similarity_cache.clear()
                self.access_count.clear()
                self.last_access.clear()

                self.logger.info("PyTorch vector storage cleanup completed")

            except Exception as e:
                self.logger.exception(f"Cleanup failed: {e}")

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction


# Factory function for easy instantiation
def create_pytorch_vector_storage(
    config: PyTorchStorageConfig | None = None,
) -> PyTorchVectorStorage:
    """Factory function to create PyTorch vector storage with default configuration.

    Constitutional Requirements:
    - Solo developer optimized defaults
    - Evidence-based parameter selection
    - Force multiplier integration enabled
    """
    if config is None:
        config = PyTorchStorageConfig()

    return PyTorchVectorStorage(config)
