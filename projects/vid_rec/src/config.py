# --- INTEGRITY ---
# Previous Character Count: 5313
# Current Character Count: 5389
# Syntax Check: PASS
# Logic Validation: [Replaced undefined logging call with standard setup_logging]
# Reason for Change: [To align the script's logging with the rest of the application and fix a NameError.]
# ------------------
# --- METADATA ---
# Filename: src/config.py
# Version: 1.2
#
# --- CHANGELOG ---
# v1.2: Resolved unused variable warning by changing the resolve_path
#       validator from a classmethod to a more appropriate staticmethod.
# v1.1: Converted to structlog (ADR-007).
#
# --- INTEGRITY ---
# Previous Character Count: 3183
# Current Character Count: 3163
# Reason for Change: Changed classmethod to staticmethod.
# ------------------

import os
import re
from pathlib import Path
from typing import Optional

import structlog
import tomlkit
from pydantic import BaseModel, Field, ValidationError, field_validator
from tomlkit.exceptions import TOMLKitError
from tomlkit.toml_document import TOMLDocument

from .logger import setup_logging

log = structlog.get_logger()

try:
    PROJECT_ROOT = Path(__file__).parent.parent.resolve()
except NameError:
    PROJECT_ROOT = Path.cwd()

CONFIG_FILE_PATH = PROJECT_ROOT / "config.toml"
CONFIG_PATH = CONFIG_FILE_PATH


class PathsConfig(BaseModel):
    source: Path = Field(
        ..., description="The root directory containing your video library."
    )
    temp_dir: Path = Field(
        default=Path("C:/Temp/ReencodedVideos"),
        description="A temporary directory for storing intermediate files.",
    )

    @field_validator("source", "temp_dir")
    @staticmethod
    def resolve_path(v: Path) -> Path:
        return v.resolve()


class SettingsConfig(BaseModel):
    log_level: str = Field(
        default="INFO",
        description="Minimum logging level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    no_replace: bool = Field(
        default=False,
        description="If true, do not replace original files. Leave results in temp_dir.",
    )
    create_subtitles: bool = Field(
        default=True,
        description="If true, generate English subtitles for videos that lack them.",
    )
    normalize_audio: bool = Field(
        default=False,
        description="If true, normalize audio to ITU-R BS.1770-4 loudness standard.",
    )


class EncodingConfig(BaseModel):
    target_height: int = Field(
        default=1080,
        ge=0,
        description="Target vertical resolution. 0 to disable downscaling.",
    )
    crf: int = Field(
        default=0,
        ge=0,
        le=51,
        description="Constant Rate Factor (CRF). 0 for auto-calculation.",
    )


class PerformanceConfig(BaseModel):
    max_workers: int = Field(
        default=0,
        ge=0,
        description="Max parallel workers for CPU tasks. 0 for auto (uses all CPU cores).",
    )
    normalization_timeout: int = Field(
        default=3600,
        ge=300,
        description="Timeout in seconds for audio normalization (minimum 5 minutes).",
    )


class QualityConfig(BaseModel):
    vmaf_decision_enabled: bool = Field(
        default=True, description="Enable VMAF-based decision making to keep files."
    )
    vmaf_decision_threshold: float = Field(
        default=94.0,
        ge=0.0,
        le=100.0,
        description="VMAF score threshold. New file is kept if its score is above this and it's smaller.",
    )


class AppConfig(BaseModel):
    paths: PathsConfig
    settings: SettingsConfig
    encoding: EncodingConfig
    performance: PerformanceConfig
    quality: QualityConfig


def load_configuration(
    config_path: Optional[Path] = None,
) -> tuple[AppConfig, TOMLDocument]:
    path_to_load = config_path or CONFIG_FILE_PATH
    if not path_to_load.exists():
        log.error("Configuration file not found", path=str(path_to_load))
        raise FileNotFoundError(f"Missing config file: {path_to_load}")
    try:
        with open(path_to_load, encoding="utf-8") as f:
            raw_content = f.read()

        def sanitize_path(match):
            key, value = match.groups()
            sanitized_value = re.sub(r"(?<!\\)\\(?!\\)", r"\\\\", value)
            return f'{key}"{sanitized_value}"'

        sanitized_content = re.sub(
            r'(\w+\s*=\s*)"([^"]*\\[^"]*)"', sanitize_path, raw_content
        )
        data = tomlkit.parse(sanitized_content)
        if sanitized_content != raw_content:
            log.info(
                "Found Windows path formatting issues. Auto-correcting config.toml..."
            )
            try:
                with open(path_to_load, "w", encoding="utf-8") as f:
                    f.write(sanitized_content)
                log.info(
                    "Config file automatically corrected with proper backslash escaping."
                )
            except Exception as e:
                log.warning("Could not auto-correct config file", error=e)
        config = AppConfig(
            paths=data.get("paths", {}),
            settings=data.get("settings", {}),
            encoding=data.get("encoding", {}),
            performance=data.get("performance", {}),
            quality=data.get("quality", {}),
        )
        return config, data
    except (TOMLKitError, ValidationError) as e:
        log.error("Error loading or parsing configuration", error=e, exc_info=True)
        raise


def save_configuration(
    config_doc: TOMLDocument,
    final_config: AppConfig,
    config_path: Path = CONFIG_FILE_PATH,
):
    for section_name, section_data in final_config.model_dump().items():
        section_dict = {
            key: str(value) if isinstance(value, Path) else value
            for key, value in section_data.items()
        }
        config_doc[section_name] = section_dict
    temp_path = config_path.with_suffix(".toml.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(config_doc))
        os.replace(temp_path, config_path)
    except Exception as e:
        log.error("Failed to save settings to config.toml", error=e, exc_info=True)
        if temp_path.exists():
            os.remove(temp_path)


if __name__ == "__main__":
    setup_logging(log_level="INFO")
    try:
        app_settings, _ = load_configuration()
        print("\n✅ Configuration loaded successfully!")
        print(app_settings.model_dump_json(indent=2))
    except (FileNotFoundError, ValidationError, Exception):
        log.error(
            "Failed to load configuration when running config.py directly.",
            exc_info=True,
        )
        print("\n❌ Failed to load configuration. Please check the errors above.")
