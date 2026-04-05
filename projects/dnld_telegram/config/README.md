# Configuration System

This directory contains the optimal configuration system for the Telegram Downloader.

## Architecture

### Schema-Driven Configuration
- **`schema.py`** - Type-safe configuration definitions with validation
- **`manager.py`** - Hot-reloading configuration manager with environment support

### Configuration Files

#### Core Configuration
- **`app.toml`** - Main application settings (paths, database, download, logging, UI, performance)
- **`channels.toml`** - Channel definitions and settings
- **`environments.toml`** - Environment-specific overrides (dev/prod/test)

#### UI Configuration
- **`ui_settings.yaml`** - UI-specific display configurations

#### Legacy
- **`app_legacy.toml`** - Previous config format (kept for migration)

## Usage

### Basic Usage
```python
from config.manager import get_config_manager

# Get configuration manager (singleton)
config_manager = get_config_manager()

# Get app configuration
app_config = config_manager.get_app_config()
print(f"Channels base: {app_config.paths.channels_base}")
print(f"Max concurrent: {app_config.download.max_concurrent}")

# Get channels configuration
channels = config_manager.get_channels_config()
enabled_channels = channels.get_enabled_channels()
```

### Environment-Specific Configuration
```bash
# Development (default)
TELEGRAM_ENV=development python -m src.download

# Production
TELEGRAM_ENV=production python -m src.download

# Testing
TELEGRAM_ENV=testing python -m src.download
```

### Environment Variable Overrides
```bash
# Override any setting via environment variables
TELEGRAM_DOWNLOAD_MAX_CONCURRENT=5 python -m src.download
TELEGRAM_LOGGING_CONSOLE_LEVEL=DEBUG python -m src.download
TELEGRAM_UI_DEFAULT_MODE=rich python -m src.download
```

## Configuration Hierarchy

Settings are applied in order of precedence (highest to lowest):

1. **Environment Variables** - `TELEGRAM_<SECTION>_<KEY>`
2. **Environment Config** - `environments.toml` based on `TELEGRAM_ENV`
3. **Base Config** - `app.toml` and `channels.toml`
4. **Schema Defaults** - Built-in defaults from schema

## Hot Reloading

The configuration system automatically watches for file changes and reloads:
- Changes to any `.toml` or `.yaml` file trigger reload
- Invalid configuration will log errors but not crash the application
- All changes are validated against the schema

## Validation

All configuration is validated:
- **Type Safety** - Automatic type conversion and validation
- **Range Checking** - Numeric bounds and constraints
- **Path Validation** - Directory existence and permissions
- **Cross-Field Validation** - Logical consistency between settings

## Environment Variables

### Paths
- `CHANNELS_BASE_PATH` - Override channels base directory

### Download Settings
- `TELEGRAM_DOWNLOAD_MAX_CONCURRENT` - Max concurrent downloads
- `TELEGRAM_DOWNLOAD_CONNECTION_TIMEOUT` - Connection timeout seconds
- `TELEGRAM_DOWNLOAD_VERIFY_DOWNLOADS` - true/false

### Logging
- `TELEGRAM_LOGGING_CONSOLE_LEVEL` - DEBUG/INFO/WARNING/ERROR/CRITICAL
- `TELEGRAM_LOGGING_FILE_LEVEL` - DEBUG/INFO/WARNING/ERROR/CRITICAL

### UI Settings
- `TELEGRAM_UI_DEFAULT_MODE` - tqdm/simple/rich/textual/alive
- `TELEGRAM_UI_SHOW_SPEED` - true/false
- `TELEGRAM_UI_SHOW_ETA` - true/false

## Adding New Configuration

1. **Update Schema** - Add new configuration to `schema.py`
2. **Add Validation** - Include validation rules
3. **Update Defaults** - Set sensible defaults in schema
4. **Update Documentation** - Add to this README

Example:
```python
@dataclass
class NewFeatureConfig:
    enabled: bool = True
    threshold: int = 100

    def validate(self) -> List[str]:
        errors = []
        if self.threshold <= 0:
            errors.append("threshold must be positive")
        return errors

# Add to AppConfig
@dataclass
class AppConfig:
    # ... existing fields ...
    new_feature: NewFeatureConfig = field(default_factory=NewFeatureConfig)
```

## Migration from Legacy

The legacy `config.toml` format is automatically migrated:
- Path settings moved to `paths` section
- Channel definitions moved to separate `channels.toml`
- Environment-specific settings moved to `environments.toml`
