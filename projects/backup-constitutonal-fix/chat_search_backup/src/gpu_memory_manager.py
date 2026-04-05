#!/usr/bin/env python3
"""GPU Memory Manager for CHS
Prevents GPU exhaustion through intelligent memory management.
"""

import gc
import os
import time
from datetime import datetime
from typing import Any

import torch


class GPUMemoryManager:
    """Manages GPU memory to prevent exhaustion in CHS system."""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.total_gpu_memory = 0
        self.warning_threshold = 0.75  # 75%
        self.critical_threshold = 0.90  # 90%
        self.monitoring_enabled = True

        if torch.cuda.is_available():
            self.total_gpu_memory = torch.cuda.get_device_properties(0).total_memory
            print("🚀 GPU Memory Manager initialized")
            print(f"   Total VRAM: {self.total_gpu_memory / 1024**3:.2f} GB")
            print(f"   Warning Threshold: {self.warning_threshold * 100:.0f}%")
            print(f"   Critical Threshold: {self.critical_threshold * 100:.0f}%")

    def get_memory_usage(self) -> dict[str, Any]:
        """Get current GPU memory usage statistics."""
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}

        allocated = torch.cuda.memory_allocated(0)
        reserved = torch.cuda.memory_reserved(0)
        free = self.total_gpu_memory - allocated

        return {
            "total_gb": self.total_gpu_memory / 1024**3,
            "allocated_gb": allocated / 1024**3,
            "reserved_gb": reserved / 1024**3,
            "free_gb": free / 1024**3,
            "allocated_percent": (allocated / self.total_gpu_memory) * 100,
            "reserved_percent": (reserved / self.total_gpu_memory) * 100,
            "free_percent": (free / self.total_gpu_memory) * 100,
            "timestamp": datetime.now().isoformat()
        }

    def check_memory_status(self) -> str:
        """Check current memory status and return alert level."""
        if not torch.cuda.is_available():
            return "no_gpu"

        usage = self.get_memory_usage()
        usage_percent = usage["reserved_percent"]

        if usage_percent >= self.critical_threshold:
            return "critical"
        elif usage_percent >= self.warning_threshold:
            return "warning"
        else:
            return "good"

    def cleanup_memory(self, aggressive: bool = False) -> dict[str, Any]:
        """Clean up GPU memory."""
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}

        # Get memory before cleanup
        before = self.get_memory_usage()

        # Python garbage collection
        gc.collect()

        # PyTorch CUDA cleanup
        torch.cuda.empty_cache()

        if aggressive:
            # More aggressive cleanup
            torch.cuda.synchronize()
            # Clear all caches
            torch.cuda.ipc_collect()

        # Get memory after cleanup
        after = self.get_memory_usage()

        freed_mb = (before["reserved_gb"] - after["reserved_gb"]) * 1024

        return {
            "before": before,
            "after": after,
            "freed_mb": freed_mb,
            "aggressive": aggressive,
            "timestamp": datetime.now().isoformat()
        }

    def monitor_memory(self, duration_seconds: int = 10, interval_seconds: float = 1.0) -> dict[str, Any]:
        """Monitor memory usage over time."""
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}

        print(f"🔍 Monitoring GPU memory for {duration_seconds} seconds...")

        samples = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            usage = self.get_memory_usage()
            usage["elapsed_seconds"] = time.time() - start_time
            samples.append(usage)

            status = self.check_memory_status()
            status_icon = {"good": "✅", "warning": "⚠️", "critical": "🚨"}.get(status, "•")

            print(f"   {status_icon} {usage['elapsed_seconds']:4.1f}s: "
                  f"{usage['reserved_percent']:5.1f}% "
                  f"({usage['reserved_gb']:.3f} GB)")

            time.sleep(interval_seconds)

        # Calculate statistics
        if samples:
            avg_usage = sum(s["reserved_percent"] for s in samples) / len(samples)
            max_usage = max(s["reserved_percent"] for s in samples)
            min_usage = min(s["reserved_percent"] for s in samples)

            return {
                "samples_count": len(samples),
                "duration_seconds": duration_seconds,
                "average_percent": avg_usage,
                "max_percent": max_usage,
                "min_percent": min_usage,
                "samples": samples,
                "status": "completed"
            }

        return {"error": "No samples collected"}

    def prevent_exhaustion(self) -> bool:
        """Take preventive measures if memory usage is high."""
        status = self.check_memory_status()

        if status == "critical":
            print("🚨 CRITICAL: GPU memory usage at dangerous level")
            cleanup_result = self.cleanup_memory(aggressive=True)

            freed_mb = cleanup_result.get("freed_mb", 0)
            print(f"   Aggressive cleanup freed {freed_mb:.1f} MB")

            # Check if cleanup helped
            new_status = self.check_memory_status()
            return new_status != "critical"

        elif status == "warning":
            print("⚠️  WARNING: GPU memory usage is high")
            cleanup_result = self.cleanup_memory(aggressive=False)

            freed_mb = cleanup_result.get("freed_mb", 0)
            if freed_mb > 10:  # Only log if significant
                print(f"   Cleanup freed {freed_mb:.1f} MB")

        return True

    def get_optimal_batch_size(self, model_size_gb: float = 0.4) -> int:
        """Calculate optimal batch size based on available GPU memory."""
        if not torch.cuda.is_available():
            return 1

        usage = self.get_memory_usage()
        available_memory = usage["free_gb"] * 0.8  # Use 80% of free memory

        # Account for model size and overhead
        memory_per_batch = model_size_gb * 1.5  # 50% overhead

        if available_memory < memory_per_batch:
            return 1

        optimal_batch = int(available_memory / memory_per_batch)
        return max(1, min(optimal_batch, 8))  # Cap at 8 to prevent issues

    def setup_environment_variables(self):
        """Set environment variables to optimize GPU usage."""
        if torch.cuda.is_available():
            # Optimize PyTorch CUDA settings
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
            os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

            # Enable memory pooling
            os.environ["PYTORCH_CUDA_MEMORY_POOL"] = "1"

            print("✅ GPU optimization environment variables set")


# Global GPU memory manager instance
gpu_manager = GPUMemoryManager()


def get_gpu_memory_status():
    """Quick function to get current GPU memory status."""
    return gpu_manager.get_memory_usage()


def cleanup_gpu_memory(aggressive: bool = False):
    """Quick function to cleanup GPU memory."""
    return gpu_manager.cleanup_memory(aggressive=aggressive)


def check_gpu_exhaustion():
    """Quick function to check for GPU exhaustion risk."""
    return gpu_manager.check_memory_status()
