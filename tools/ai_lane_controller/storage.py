"""Filesystem-based durable storage for lane messages and events.

Storage layout::

    .ai-lanes/
        registry.json
        lane-a/
            messages/
                msg-<id>.json
                msg-<id>.md
            events.jsonl
        lane-b/
            messages/
                msg-<id>.json
                msg-<id>.md
            events.jsonl

Human-inspectable, no database, survives process restart.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _guess_storage_root() -> Path:
    """Default storage root is ``.ai-lanes/`` in the workspace root."""
    return Path("P:/.ai-lanes")


class MessageStorage:
    """Manages the filesystem-backed message store for all lanes."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root).resolve() if root else _guess_storage_root()

    # -- lane scafold -----------------------------------------------------

    def ensure_lane(self, lane_id: str) -> None:
        """Create the directory structure for a lane."""
        (self.root / lane_id / "messages").mkdir(parents=True, exist_ok=True)

    def _message_dir(self, lane_id: str) -> Path:
        return self.root / lane_id / "messages"

    def _events_path(self, lane_id: str) -> Path:
        return self.root / lane_id / "events.jsonl"

    # -- messages ---------------------------------------------------------

    def message_path(self, lane_id: str, message_id: str) -> Path:
        """Return the JSON metadata path for a message."""
        return self._message_dir(lane_id) / f"{message_id}.json"

    def payload_path(self, lane_id: str, message_id: str) -> Path:
        """Return the payload (markdown/text) path for a message."""
        return self._message_dir(lane_id) / f"{message_id}.md"

    def store_message(
        self,
        message: dict[str, Any],
        payload_text: str,
    ) -> None:
        """Persist a message's JSON metadata and its payload markdown.

        The payload is stored separately at ``payload_path`` so a human
        can read it directly.  The JSON metadata records ``payload_path``.
        """
        lane_id = message["lane_id"]
        msg_id = message["id"]
        self.ensure_lane(lane_id)

        meta_path = self.message_path(lane_id, msg_id)
        pay_path = self.payload_path(lane_id, msg_id)

        # Write payload first so the JSON metadata always has a valid path.
        pay_path.write_text(payload_text, encoding="utf-8")

        msg = dict(message)
        msg["payload_path"] = str(pay_path.relative_to(self.root).as_posix())

        with meta_path.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(msg, f, indent=2, ensure_ascii=False)
            f.write("\n")

    def get_message(self, lane_id: str, message_id: str) -> dict[str, Any] | None:
        """Read a message's JSON metadata, or None if it does not exist."""
        path = self.message_path(lane_id, message_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def read_payload(self, lane_id: str, message_id: str) -> str | None:
        """Read a message's payload text, or None if it does not exist."""
        path = self.payload_path(lane_id, message_id)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_messages(self, lane_id: str) -> list[dict[str, Any]]:
        """Return all stored messages for a lane, newest first."""
        msg_dir = self._message_dir(lane_id)
        if not msg_dir.exists():
            return []
        messages: list[dict[str, Any]] = []
        for child in sorted(msg_dir.iterdir()):
            if child.suffix == ".json" and child.stem.startswith("msg-"):
                messages.append(json.loads(child.read_text(encoding="utf-8")))
        messages.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        return messages

    def list_payload_filenames(self, lane_id: str) -> list[Path]:
        """Return all .md payload filenames for a lane."""
        msg_dir = self._message_dir(lane_id)
        if not msg_dir.exists():
            return []
        return sorted(
            [f for f in msg_dir.iterdir() if f.suffix == ".md"],
            reverse=True,
        )

    # -- events -----------------------------------------------------------

    def append_event(self, lane_id: str, event: dict[str, Any]) -> None:
        """Append one JSON line to the lane's event log."""
        self.ensure_lane(lane_id)
        path = self._events_path(lane_id)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")

    def list_events(self, lane_id: str) -> list[dict[str, Any]]:
        """Read every event from a lane's event log."""
        path = self._events_path(lane_id)
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    events.append(json.loads(stripped))
        return events

    # -- cross-lane queries ------------------------------------------------

    def all_lane_dirs(self) -> list[str]:
        """Return all sub-directory names under the storage root (lane IDs)."""
        if not self.root.exists():
            return []
        return sorted(
            d.name for d in self.root.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

