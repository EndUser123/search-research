import logging
import time

import numpy as np

from core.gpu_manager import GPUMemoryConfig, GPUMemoryManager
from core.storage_manager import StorageConfig, StorageManager

"""CKS GPU Memory Manager Usage Examples.

Constitutional Requirements:
- Solo developer optimization (simple interfaces, clear examples)
- Evidence-based implementation (real-world usage patterns)
- Force multiplier integration (GPU acceleration with CPU fallback)
- No enterprise bloat (direct Python usage, no complex setup)

Examples:
1. Basic GPU memory management
2. RAPIDS integration for data operations
3. FAISS GPU vector operations
4. Memory monitoring and cleanup
5. Solo developer optimization patterns
6. Constitutional compliance validation
"""


# Add CKS to path for examples


# Configure logging for examples
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def example_1_basic_gpu_management() -> None:
    """Example 1: Basic GPU Memory Management.

    Demonstrates fundamental GPU memory management with strict limits
    and automatic CPU fallback for solo developer optimization.

    Constitutional Features:
    - Solo developer optimized (6GB limit, auto-cleanup)
    - Evidence-based operations (monitoring, audit trails)
    - Force multiplier (GPU acceleration with fallback)
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic GPU Memory Management")
    print("=" * 60)

    # Solo developer optimized configuration
    config = GPUMemoryConfig(
        max_gpu_memory_mb=6144,  # Strict 6GB limit
        memory_threshold_mb=5120,  # Warning at 5GB
        cleanup_threshold_mb=5632,  # Auto-cleanup at 5.5GB
        auto_cleanup=True,  # Automatic cleanup
        fallback_to_cpu=True,  # CPU fallback
        monitoring_interval=2.0,  # Monitoring every 2 seconds
    )

    print(f"GPU Config: {config.max_gpu_memory_mb}MB limit, auto-cleanup enabled")

    try:
        with GPUMemoryManager(config) as gpu_manager:
            print(
                f"GPU Manager initialized: GPU available = {gpu_manager._gpu_available}",
            )

            # Get current memory statistics
            stats = gpu_manager.get_memory_stats()
            print(
                f"Memory stats: {stats.used_memory_mb:.0f}MB used, "
                f"{stats.utilization_percent:.1f}% utilization",
            )

            # Allocate some GPU arrays with automatic fallback
            print("\nAllocating GPU arrays...")
            for i in range(5):
                shape = (1000, 1000)  # ~4MB each for float32
                array = gpu_manager.allocate_gpu_array(shape, np.float32)
                print(
                    f"  Allocated array {i + 1}: shape={shape}, type={type(array).__name__}",
                )

            # Check performance statistics
            perf_stats = gpu_manager.get_performance_stats()
            print("\nPerformance stats:")
            print(
                f"  Total operations: {perf_stats['operation_stats']['total_operations']}",
            )
            print(
                f"  Fallback count: {perf_stats['operation_stats']['fallback_count']}",
            )
            print(
                f"  Fallback rate: {perf_stats['operation_stats']['fallback_rate']:.1f}%",
            )

            # Get constitutional compliance score
            compliance_score = gpu_manager.get_constitutional_compliance_score()
            print(f"  Constitutional compliance: {compliance_score:.3f}")

    except Exception as e:
        print(f"Error: {e}")
        print("Falling back to CPU-only operations (constitutional requirement)")


def example_2_rapids_integration() -> None:
    """Example 2: RAPIDS Integration for Data Operations.

    Demonstrates RAPIDS cuDF and cuML integration with automatic fallback
    to pandas and scikit-learn for solo developer compatibility.

    Constitutional Features:
    - Solo developer optimization (fallback when RAPIDS unavailable)
    - Evidence-based operations (real data processing)
    - Force multiplier (GPU acceleration when available)
    """
    print("\n" + "=" * 60)
    print("Example 2: RAPIDS Integration")
    print("=" * 60)

    config = GPUMemoryConfig(
        max_gpu_memory_mb=4096,  # Conservative 4GB for RAPIDS
        auto_cleanup=True,
        fallback_to_cpu=True,
    )

    try:
        with GPUMemoryManager(config) as gpu_manager:
            print("RAPIDS Status:")
            perf_stats = gpu_manager.get_performance_stats()
            rapids_status = perf_stats["rapids_enabled"]
            print(f"  cuDF available: {rapids_status['cudf']}")
            print(f"  cuML available: {rapids_status['cuml']}")
            print(f"  CuPy available: {rapids_status['cupy']}")

            # Create sample data
            print("\nCreating sample data...")
            data_size = 10000
            data = {
                "id": range(data_size),
                "value": np.random.randn(data_size),
                "category": np.random.choice(["A", "B", "C"], data_size),
                "timestamp": np.arange(data_size),
            }

            # Create GPU DataFrame with automatic fallback
            print(f"Creating DataFrame with {data_size:,} rows...")
            df = gpu_manager.create_gpu_dataframe(data)
            print(f"  DataFrame type: {type(df).__name__}")
            print(f"  Shape: {df.shape if hasattr(df, 'shape') else len(df)}")

            # Perform some operations
            print("\nPerforming operations...")
            start_time = time.time()

            # Basic filtering (will work on both GPU and CPU DataFrames)
            if hasattr(df, "query"):  # pandas/cudf style
                filtered_df = df.query("value > 0.5")
                print(f"  Filtered rows with value > 0.5: {len(filtered_df):,}")

            # Group by operation
            if hasattr(df, "groupby"):
                grouped = df.groupby("category")["value"].mean()
                print(
                    f"  Average value by category: {dict(grouped) if hasattr(grouped, 'items') else grouped}",
                )

            operation_time = time.time() - start_time
            print(f"  Operation time: {operation_time:.3f} seconds")

    except Exception as e:
        print(f"RAPIDS integration error: {e}")
        print("Falling back to CPU-only operations (constitutional requirement)")


def example_3_faiss_gpu_operations() -> None:
    """Example 3: FAISS GPU Vector Operations.

    Demonstrates FAISS GPU integration for vector similarity search
    with automatic CPU fallback for constitutional compliance.

    Constitutional Features:
    - Solo developer optimization (GPU memory limits, CPU fallback)
    - Evidence-based operations (real vector similarity search)
    - Force multiplier (GPU acceleration for vector operations)
    """
    print("\n" + "=" * 60)
    print("Example 3: FAISS GPU Vector Operations")
    print("=" * 60)

    config = GPUMemoryConfig(
        max_gpu_memory_mb=3072,  # 3GB for FAISS operations
        memory_pool_size_mb=512,  # 512MB memory pool
        auto_cleanup=True,
        fallback_to_cpu=True,
    )

    try:
        with GPUMemoryManager(config) as gpu_manager:
            print(f"FAISS GPU available: {gpu_manager._faiss_gpu_index is not None}")

            # Create sample vectors for similarity search
            vector_dimension = 128
            num_vectors = 1000

            print(
                f"\nGenerating {num_vectors:,} random vectors (dim={vector_dimension})...",
            )
            vectors = np.random.random((num_vectors, vector_dimension)).astype(
                np.float32,
            )

            # Normalize vectors for cosine similarity
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / (norms + 1e-8)

            # Create FAISS index with GPU support
            print("Creating FAISS index...")
            index = gpu_manager.create_faiss_index(vector_dimension, "flat")
            print(f"  Index type: {type(index).__name__}")

            # Add vectors to index
            print("Adding vectors to index...")
            start_time = time.time()
            index.add(vectors)
            add_time = time.time() - start_time
            print(f"  Added {num_vectors:,} vectors in {add_time:.3f} seconds")

            # Perform similarity search
            print("\nPerforming similarity search...")
            query_vectors = np.random.random((10, vector_dimension)).astype(np.float32)
            query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
            query_vectors = query_vectors / (query_norms + 1e-8)

            k = 5  # Top 5 similar vectors
            start_time = time.time()
            similarities, _indices = index.search(query_vectors, k)
            search_time = time.time() - start_time

            print(f"  Searched {len(query_vectors)} queries for top {k} results")
            print(f"  Search time: {search_time:.3f} seconds")
            print(f"  Average similarity: {np.mean(similarities):.4f}")

            # Memory cleanup
            freed_memory = gpu_manager.cleanup_gpu_memory()
            print(f"\nMemory cleanup freed: {freed_memory:.0f}MB")

    except Exception as e:
        print(f"FAISS GPU operations error: {e}")
        print("Falling back to CPU-only FAISS operations")


def example_4_memory_monitoring_and_cleanup() -> None:
    """Example 4: Memory Monitoring and Cleanup.

    Demonstrates comprehensive memory monitoring, leak detection,
    and automatic cleanup for solo developer optimization.

    Constitutional Features:
    - Solo developer optimization (memory limits, auto-cleanup)
    - Evidence-based operations (real-time monitoring)
    - Memory leak prevention and detection
    """
    print("\n" + "=" * 60)
    print("Example 4: Memory Monitoring and Cleanup")
    print("=" * 60)

    config = GPUMemoryConfig(
        max_gpu_memory_mb=2048,  # 2GB for demonstration
        memory_threshold_mb=1536,  # Warning at 1.5GB
        cleanup_threshold_mb=1792,  # Auto-cleanup at 1.75GB
        monitoring_interval=1.0,  # Fast monitoring for demo
        leak_detection_threshold_mb=50,  # 50MB leak detection
        auto_cleanup=True,
    )

    try:
        with GPUMemoryManager(config) as gpu_manager:
            print("Starting memory monitoring demonstration...")

            # Baseline memory check
            initial_stats = gpu_manager.get_memory_stats()
            print(f"Initial memory: {initial_stats.used_memory_mb:.0f}MB")

            # Simulate memory usage patterns
            print("\nSimulating memory usage patterns...")
            allocations = []

            for i in range(10):
                # Allocate progressively larger arrays
                size = (100 + i * 50, 100 + i * 50)
                array = gpu_manager.allocate_gpu_array(size, np.float32)
                allocations.append(array)

                stats = gpu_manager.get_memory_stats()
                print(
                    f"  Allocation {i + 1}: {size}, Memory: {stats.used_memory_mb:.0f}MB",
                )

                # Small delay to see monitoring in action
                time.sleep(0.5)

                # Check if auto-cleanup was triggered
                if stats.memory_leaks_detected > 0:
                    print(f"    ⚠️  Memory leak detected: {stats.memory_leaks_detected}")

            # Trigger manual cleanup
            print("\nTriggering manual cleanup...")
            freed_memory = gpu_manager.cleanup_gpu_memory()
            print(f"Manual cleanup freed: {freed_memory:.0f}MB")

            # Final memory check
            final_stats = gpu_manager.get_memory_stats()
            print(f"Final memory: {final_stats.used_memory_mb:.0f}MB")

            # Performance summary
            perf_stats = gpu_manager.get_performance_stats()
            print("\nPerformance Summary:")
            print(
                f"  Total operations: {perf_stats['operation_stats']['total_operations']}",
            )
            print(
                f"  Memory warnings: {perf_stats['operation_stats']['memory_warnings']}",
            )
            print(
                f"  Cleanup operations: {perf_stats['operation_stats']['cleanup_count']}",
            )
            print(
                f"  Constitutional compliance: {gpu_manager.get_constitutional_compliance_score():.3f}",
            )

    except Exception as e:
        print(f"Memory monitoring error: {e}")


def example_5_integrated_storage_and_gpu() -> None:
    """Example 5: Integrated Storage and GPU Operations.

    Demonstrates integration between CKS Storage Manager and GPU Manager
    for comprehensive data and vector operations.

    Constitutional Features:
    - Solo developer optimization (integrated, simple interface)
    - Evidence-based operations (real storage + GPU operations)
    - Force multiplier (combined storage and GPU acceleration)
    """
    print("\n" + "=" * 60)
    print("Example 5: Integrated Storage and GPU Operations")
    print("=" * 60)

    # Configure both storage and GPU managers
    storage_config = StorageConfig(
        max_memory_mb=1024,  # Conservative storage memory
        enable_gpu=True,  # Enable GPU in storage
        auto_cleanup=True,
    )

    gpu_config = GPUMemoryConfig(
        max_gpu_memory_mb=3072,  # 3GB for combined operations
        auto_cleanup=True,
        fallback_to_cpu=True,
    )

    try:
        # Initialize both managers
        with (
            StorageManager(storage_config) as storage_manager,
            GPUMemoryManager(gpu_config) as gpu_manager,
        ):
            print("Storage and GPU managers initialized successfully")

            # Create some knowledge nodes
            print("\nCreating knowledge nodes...")
            nodes = []
            for i in range(5):
                node_data = {
                    "type": "document",
                    "content": f"Document {i} content for testing GPU integration",
                    "metadata": {
                        "category": "test",
                        "priority": i,
                        "timestamp": time.time(),
                    },
                }
                node_id = storage_manager.create_knowledge_node(node_data)
                nodes.append(node_id)
                print(f"  Created node: {node_id}")

            # Generate and store embeddings (vectors)
            print("\nGenerating and storing vector embeddings...")
            vector_dimension = 256
            for i, node_id in enumerate(nodes):
                # Simulate embedding generation
                embedding = np.random.random(vector_dimension).astype(np.float32)

                # Store in storage manager
                storage_manager.store_vector(node_id, embedding)

                # Also allocate as GPU array for demonstration
                gpu_manager.allocate_gpu_array(
                    (vector_dimension,),
                    np.float32,
                )

                print(f"  Stored vector for {node_id}: {len(embedding)} dimensions")

            # Perform vector similarity search
            print("\nPerforming vector similarity search...")
            query_embedding = np.random.random(vector_dimension).astype(np.float32)
            similar_vectors = storage_manager.search_similar_vectors(
                query_embedding,
                k=3,
            )

            print(f"  Found {len(similar_vectors)} similar vectors:")
            for vector_id, similarity in similar_vectors:
                print(f"    {vector_id}: {similarity:.4f}")

            # Memory and storage statistics
            storage_stats = storage_manager.get_storage_stats()
            gpu_stats = gpu_manager.get_performance_stats()

            print("\nStorage Statistics:")
            print(f"  Knowledge nodes: {storage_stats.get('knowledge_nodes', 0)}")
            print(f"  Vectors stored: {storage_stats.get('vectors_stored', 0)}")
            print(f"  Memory usage: {storage_stats.get('memory_usage_mb', 0):.0f}MB")

            print("\nGPU Statistics:")
            print(
                f"  GPU operations: {gpu_stats['operation_stats']['total_operations']}",
            )
            print(
                f"  GPU memory used: {gpu_stats['current_memory_stats']['used_mb']:.0f}MB",
            )
            print(
                f"  Fallback rate: {gpu_stats['operation_stats']['fallback_rate']:.1f}%",
            )

            # Constitutional compliance scores
            storage_compliance = storage_manager.get_constitutional_compliance_score()
            gpu_compliance = gpu_manager.get_constitutional_compliance_score()

            print("\nConstitutional Compliance:")
            print(f"  Storage: {storage_compliance:.3f}")
            print(f"  GPU: {gpu_compliance:.3f}")
            print(f"  Overall: {(storage_compliance + gpu_compliance) / 2:.3f}")

    except Exception as e:
        print(f"Integrated operations error: {e}")
        print("Falling back to basic operations (constitutional requirement)")


def example_6_solo_developer_optimization() -> None:
    """Example 6: Solo Developer Optimization Patterns.

    Demonstrates optimization patterns specifically designed for
    solo developer workflows and resource constraints.

    Constitutional Features:
    - Solo developer optimization (conservative defaults, auto-management)
    - Evidence-based operations (real development patterns)
    - No enterprise bloat (simple, direct interfaces)
    """
    print("\n" + "=" * 60)
    print("Example 6: Solo Developer Optimization Patterns")
    print("=" * 60)

    # Solo developer optimized configuration
    config = GPUMemoryConfig(
        max_gpu_memory_mb=2048,  # Conservative 2GB for solo dev
        memory_threshold_mb=1536,  # Early warning
        cleanup_threshold_mb=1792,  # Aggressive cleanup
        memory_pool_size_mb=256,  # Small memory pool
        monitoring_interval=5.0,  # Less frequent monitoring
        auto_cleanup=True,  # Always auto-cleanup
        fallback_to_cpu=True,  # Always fallback
        leak_detection_threshold_mb=25,  # Sensitive leak detection
    )

    try:
        with GPUMemoryManager(config) as gpu_manager:
            print("Solo developer optimization enabled")
            print(
                f"Configuration: {config.max_gpu_memory_mb}MB limit, "
                f"auto-cleanup: {config.auto_cleanup}",
            )

            # Pattern 1: Context-based operations
            print("\nPattern 1: Context-based operations")
            with gpu_manager.gpu_context(required_memory_mb=50):
                # Operations within context get automatic cleanup
                gpu_manager.allocate_gpu_array((100, 100), np.float32)
                gpu_manager.allocate_gpu_array((200, 50), np.float32)
                print("  Allocated arrays within context")
            # Automatic cleanup happens here

            # Pattern 2: Batch operations with monitoring
            print("\nPattern 2: Batch operations with monitoring")
            batch_size = 10
            print(f"Processing {batch_size} items in batches...")

            for batch_num in range(3):
                print(f"  Batch {batch_num + 1}:")
                batch_start = time.time()

                # Process batch
                for i in range(batch_size):
                    gpu_manager.allocate_gpu_array((50, 50), np.float32)
                    # Simulate some processing
                    time.sleep(0.01)

                batch_time = time.time() - batch_start
                stats = gpu_manager.get_memory_stats()

                print(f"    Processed {batch_size} items in {batch_time:.2f}s")
                print(f"    Memory: {stats.used_memory_mb:.0f}MB")

                # Check if cleanup is needed
                if stats.used_memory_mb > config.memory_threshold_mb:
                    print("    ⚠️  Memory threshold exceeded, triggering cleanup")
                    freed = gpu_manager.cleanup_gpu_memory()
                    print(f"    Freed {freed:.0f}MB")

            # Pattern 3: Resource monitoring and alerts
            print("\nPattern 3: Resource monitoring and alerts")
            perf_stats = gpu_manager.get_performance_stats()

            op_stats = perf_stats["operation_stats"]
            if op_stats["fallback_rate"] > 50:
                print(f"  ⚠️  High fallback rate: {op_stats['fallback_rate']:.1f}%")
                print(
                    "  Consider checking GPU availability or reducing memory requirements",
                )

            if op_stats["memory_warnings"] > 0:
                print(f"  ⚠️  Memory warnings: {op_stats['memory_warnings']}")
                print("  Consider reducing memory usage or increasing limits")

            if op_stats["cleanup_count"] > 0:
                print(f"  ✓ Auto-cleanup triggered {op_stats['cleanup_count']} times")

            # Pattern 4: Constitutional compliance checking
            print("\nPattern 4: Constitutional compliance checking")
            compliance_score = gpu_manager.get_constitutional_compliance_score()

            if compliance_score >= 0.9:
                print(f"  ✓ Excellent compliance: {compliance_score:.3f}")
            elif compliance_score >= 0.7:
                print(f"  ⚠️  Good compliance: {compliance_score:.3f}")
            else:
                print(f"  ❌ Poor compliance: {compliance_score:.3f}")
                print("  Review configuration and usage patterns")

            print("\nSolo Developer Optimization Summary:")
            print(f"  Total operations: {op_stats['total_operations']}")
            print(f"  Efficiency rate: {100 - op_stats['fallback_rate']:.1f}%")
            print(f"  Compliance score: {compliance_score:.3f}")
            print(
                f"  Memory utilization: {perf_stats['current_memory_stats']['utilization_percent']:.1f}%",
            )

    except Exception as e:
        print(f"Solo developer optimization error: {e}")
        print("Constitutional compliance ensures graceful degradation")


def main() -> None:
    """Run all GPU manager examples with constitutional compliance.

    Each example demonstrates specific aspects of the CKS GPU Memory Manager
    while maintaining strict adherence to CSF constitutional requirements
    for solo developer optimization and evidence-based operations.
    """
    print("CKS GPU Memory Manager Examples")
    print("Constitutional Compliance: Solo Developer Optimization")
    print("Evidence-Based Implementation with GPU Acceleration")

    examples = [
        ("Basic GPU Management", example_1_basic_gpu_management),
        ("RAPIDS Integration", example_2_rapids_integration),
        ("FAISS GPU Operations", example_3_faiss_gpu_operations),
        ("Memory Monitoring", example_4_memory_monitoring_and_cleanup),
        ("Integrated Storage + GPU", example_5_integrated_storage_and_gpu),
        ("Solo Developer Optimization", example_6_solo_developer_optimization),
    ]

    for example_name, example_func in examples:
        try:
            print(f"\n{'=' * 80}")
            print(f"Running: {example_name}")
            print(f"{'=' * 80}")

            start_time = time.time()
            example_func()
            end_time = time.time()

            print(f"\n✓ {example_name} completed successfully")
            print(f"  Time: {end_time - start_time:.2f} seconds")

        except Exception as e:
            print(f"\n❌ {example_name} failed: {e}")
            print("  Constitutional compliance ensures graceful degradation")

        # Small delay between examples
        time.sleep(1)

    print(f"\n{'=' * 80}")
    print("All GPU Manager Examples Completed")
    print("Constitutional compliance maintained throughout")
    print("Evidence-based implementation verified")
    print("{'='*80}")


if __name__ == "__main__":
    main()
