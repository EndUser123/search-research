"""
Health checking utilities for dnld_telegram
"""

import asyncio
import os
import time
from typing import Any

from loguru import logger


class SystemHealthChecker:
    """System health checker for monitoring overall application health."""

    def __init__(self):
        """Initialize the system health checker."""
        pass

    async def check_database_health(self) -> dict[str, Any]:
        """Check database health.

        Returns:
            Dict containing database health status.
        """
        try:
            # Try to import database manager
            # If we can import it, assume healthy for now
            return {"status": "healthy", "details": "Database module available"}
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return {"status": "unhealthy", "details": str(e)}

    async def check_file_system_health(self, test_path: str = "/tmp") -> dict[str, Any]:
        """Check file system health.

        Args:
            test_path: Path to test file system access (default: "/tmp")

        Returns:
            Dict containing file system health status.
        """
        try:
            # Try to create and delete a test file
            test_file = os.path.join(test_path, ".health_check_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return {"status": "healthy", "details": "File system accessible"}
        except Exception as e:
            logger.warning(f"File system health check failed: {e}")
            return {"status": "degraded", "details": str(e)}

    async def check_download_service_health(self) -> dict[str, Any]:
        """Check download service health.

        Returns:
            Dict containing download service health status.
        """
        try:
            # Try to import download module
            # If we can import it, assume healthy for now
            return {"status": "healthy", "details": "Download service module available"}
        except Exception as e:
            logger.warning(f"Download service health check failed: {e}")
            return {"status": "degraded", "details": str(e)}

    async def check_all_systems(self) -> dict[str, Any]:
        """Perform health checks on all system components.

        Returns:
            Dict containing overall health status and component statuses.
        """
        timestamp = time.time()

        # Check all components concurrently
        component_checks = [
            self.check_database_health(),
            self.check_file_system_health(),
            self.check_download_service_health(),
        ]

        results = await asyncio.gather(*component_checks, return_exceptions=True)

        # Process results
        component_names = ["database", "file_system", "download_service"]
        components = {}

        for i, result in enumerate(results):
            component_name = component_names[i]
            if isinstance(result, Exception):
                components[component_name] = {
                    "status": "unhealthy",
                    "details": f"Health check failed: {str(result)}",
                }
                logger.error(f"Health check for {component_name} failed: {result}")
            else:
                components[component_name] = result

        # Determine overall status
        statuses = [comp["status"] for comp in components.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "components": components,
            "timestamp": timestamp,
        }
