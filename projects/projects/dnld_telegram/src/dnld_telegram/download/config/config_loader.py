from pathlib import Path
from typing import Any

import toml


class ConfigLoader:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        config_file_path = self.base_path / "config" / "config.toml"
        if config_file_path.exists():
            with open(config_file_path) as f:
                self.config = toml.load(f)
        else:
            raise FileNotFoundError(f"Config file not found at {config_file_path}")

    def get_config(self):
        return self.config
