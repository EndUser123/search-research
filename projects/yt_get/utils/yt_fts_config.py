import configparser
import os
import warnings


class YtFtsConfig:
    LEGACY_ENV_VARS = {
        "OUTPUT_DIR",
        "CACHE_DIR",
        "CHANNEL_URL",
        "CHANNEL_FILE",
        "YOUTUBE_DAILY_QUOTA",
        "YOUTUBE_QUOTA_RESERVE",
        "QUOTA_DB_PATH",
        "WORKERS",
        "NEW_VIDEOS",
        "NO_AUDIO",
        "ALIGN",
        "SKIP_STUCK",
        "YTDLP_DEFAULT_TIMEOUT_S",
        "YTDLP_METADATA_TIMEOUT_S",
        "YTDLP_LIST_FETCH_TIMEOUT_S",
        "YTDLP_INCR_LIST_TIMEOUT_S",
        "YTDLP_TRANSCRIPT_TIMEOUT_S",
        "YTDLP_AUDIO_TIMEOUT_S",
        "CACHE_LOCK_TIMEOUT_S",
        "DB_CONNECT_TIMEOUT_S",
        "API_RETRY_DELAY_S",
        "API_RETRIES",
        "LOG_CONSOLE",
        "DEBUG",
        "LOG_PATH",
        "METADATA_ONLY",
        "SCAN_ONLY",
        "REFRESH_ALL",
        "SKIP_SCAN",
        "API_DIAGNOSTICS",
        "DRY_RUN",
        "SHOW_CONFIG_ON_STARTUP",
        "TRANSCRIPT_SEGMENT_GAP_S",
        "YOUTUBE_API_KEY",
    }

    def __init__(self):
        self.config_path = self.get_config_path()
        self.config_file_path = os.path.join(self.config_path, "config.ini")
        self.config = self.load_config()
        self.check_legacy_env_vars()

    def check_legacy_env_vars(self):
        for var in self.LEGACY_ENV_VARS:
            if var in os.environ:
                warnings.warn(
                    f"The environment variable {var} is deprecated and will be removed in a future version. "
                    f"Please use the config file at {self.config_file_path} instead.",
                    DeprecationWarning,
                )

    def get_config_path(self) -> str:
        """
        Returns the path to the config directory.
        """
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return os.path.join(config_home, "yt_fts")
        return os.path.join(os.path.expanduser("~"), ".config", "yt_fts")

    def load_config(self):
        config = configparser.ConfigParser()

        default_config = {
            "General": {
                "db_path": os.path.join(self.get_config_path(), "yt_fts.db"),
                "chroma_db_path": os.path.join(self.get_config_path(), "chroma_db"),
                "temp_dir": os.path.join(self.get_config_path(), "tmp"),
            },
            "YouTube": {"api_key": "YOUR_API_KEY"},
        }

        # create config directory and file if they don't exist
        os.makedirs(self.config_path, exist_ok=True)
        if not os.path.exists(self.config_file_path):
            with open(self.config_file_path, "w") as f:
                f.write("")

        config.read_dict(default_config)
        config.read(self.config_file_path)

        # Environment variables override config file
        if "YT_FTS_API_KEY" in os.environ:
            config["YouTube"]["api_key"] = os.environ["YT_FTS_API_KEY"]

        # Write changes back to config file
        with open(self.config_file_path, "w") as configfile:
            config.write(configfile)

        return config

    def get_db_path(self) -> str:
        """
        Returns the path to the database file.
        """
        return self.config["General"]["db_path"]

    def get_or_make_chroma_path(self) -> str:
        """
        Returns the path to the chroma db directory.
        """
        chroma_path = self.config["General"]["chroma_db_path"]
        os.makedirs(chroma_path, exist_ok=True)
        return chroma_path

    def get_temp_dir(self) -> str:
        """
        Returns the path to the temp directory.
        """
        temp_dir = self.config["General"]["temp_dir"]
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir


def get_config_path() -> str:
    """
    Returns the path to the config directory.
    This function is deprecated and will be removed in a future version.
    """
    warnings.warn(
        "get_config_path is deprecated, use YtFtsConfig().get_config_path() instead.",
        DeprecationWarning,
    )
    return YtFtsConfig().get_config_path()


def get_db_path() -> str:
    """
    Returns the path to the database file.
    This function is deprecated and will be removed in a future version.
    """
    warnings.warn(
        "get_db_path is deprecated, use YtFtsConfig().get_db_path() instead.",
        DeprecationWarning,
    )
    return YtFtsConfig().get_db_path()


def get_or_make_chroma_path() -> str:
    """
    Returns the path to the chroma db directory.
    This function is deprecated and will be removed in a future version.
    """
    warnings.warn(
        "get_or_make_chroma_path is deprecated, use YtFtsConfig().get_or_make_chroma_path() instead.",
        DeprecationWarning,
    )
    return YtFtsConfig().get_or_make_chroma_path()


def get_temp_dir() -> str:
    """
    Returns the path to the temp directory.
    This function is deprecated and will be removed in a future version.
    """
    warnings.warn(
        "get_temp_dir is deprecated, use YtFtsConfig().get_temp_dir() instead.",
        DeprecationWarning,
    )
    return YtFtsConfig().get_temp_dir()
