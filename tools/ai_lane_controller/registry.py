"""Human-readable lane registry.

Lane IDs are explicit strings.  No inference from process IDs, window titles,
terminal names, or timestamps.  Unknown lanes fail closed.

Multi-lane (Milestone 5): supports lane-01 through lane-08 as standard slots.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LANE_IDS = [f"lane-{i:02d}" for i in range(1, 9)]
"""The eight standard lane slots."""


class RegistryError(ValueError):
    """Lane does not exist in the registry."""


class Lane:
    """One known lane with an explicit identity."""

    def __init__(self, id: str, *, enabled: bool = True) -> None:
        if not isinstance(id, str) or not id.strip():
            raise ValueError("lane id must be a non-empty string")
        self.id = id.strip()
        self.enabled = enabled

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lane:
        if not isinstance(data, dict):
            raise ValueError("lane entry must be an object")
        lid = data.get("id")
        if not isinstance(lid, str) or not lid.strip():
            raise ValueError("lane entry must have a non-empty 'id' string")
        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("lane 'enabled' must be a boolean")
        return cls(id=lid.strip(), enabled=enabled)


def create_standard_lanes() -> list[Lane]:
    """Return exactly eight lane slots: lane-01 through lane-08, all enabled."""
    return [Lane(f"lane-{i:02d}") for i in range(1, 9)]


def load_registry(path: str | Path) -> list[Lane]:
    """Read and validate a lane registry JSON file."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict) or "lanes" not in data:
        raise ValueError("registry must contain a 'lanes' array")
    lanes_data = data["lanes"]
    if not isinstance(lanes_data, list):
        raise ValueError("registry 'lanes' must be an array")
    lanes = [Lane.from_dict(entry) for entry in lanes_data]
    ids = [l.id for l in lanes]
    if len(ids) != len(set(ids)):
        raise ValueError("lane ids must be unique")
    return lanes


def save_registry(lanes: list[Lane], path: str | Path) -> None:
    """Write lanes to a human-readable JSON registry file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {"lanes": [l.to_dict() for l in lanes]}
    target.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def lane_exists(lanes: list[Lane], lane_id: str) -> bool:
    """Return True if a lane with the given ID exists and is enabled."""
    return any(l.id == lane_id and l.enabled for l in lanes)


def require_lane(lanes: list[Lane], lane_id: str) -> None:
    """Raise RegistryError if the lane does not exist or is disabled."""
    if not lane_exists(lanes, lane_id):
        raise RegistryError(f"unknown or disabled lane: {lane_id}")