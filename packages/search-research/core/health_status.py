"""Health status dataclass for search backend health checks.

Provides a standard interface for backends to report their health status.

This module was migrated from P:/__csf/src/search/health_status.py
to eliminate circular dependency between search and search_research packages.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass
class HealthStatus:
    """Health check result for a search backend.

    Attributes
    ----------
    status : Literal["pass", "warning", "fail"]
        Overall health status.
    reachable : bool
        Can the module be loaded/initialized?
    working : bool
        Does the backend function correctly?
    has_data : bool
        Is data/index available and not empty?
    message : str
        Human-readable status message.
    details : dict[str, Any]
        Additional backend-specific information (index size, row count, etc.)

    Examples
    --------
    >>> HealthStatus(
    ...     status="pass",
    ...     reachable=True,
    ...     working=True,
    ...     has_data=True,
    ...     message="All systems operational",
    ...     details={"index_size": 1000}
    ... )
    HealthStatus(status='pass', reachable=True, working=True, has_data=True, ...)
    """

    status: Literal["pass", "warning", "fail"]
    reachable: bool
    working: bool
    has_data: bool
    message: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of this health status.
        """
        return asdict(self)
