"""Kedro project settings for ml_engine.

Kedro 1.1.1 Compatible Settings File
"""

from pathlib import Path
from typing import Any, Dict

# Project name
PROJECT_NAME = "ml_engine"

# Project version
__version__ = "0.2.1"

# Default run environment
RUN_ENVIRONMENT = "local"

# Configuration paths
CONF_SOURCE = str(Path(__file__).parent.parent.parent / "conf")

# Kedro settings
KEDRO_INIT_VERSION = "1.1.1"

# Session name format
SESSION_NAME = "ml_engine_session"

# Package name
PACKAGE_NAME = "ml_engine"

# Logging configuration
# Uncomment to enable file logging
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

# Data catalog
DATA_CATALOG_PATH = str(Path(CONF_SOURCE) / "base" / "catalog.yml")

# Parameters file path
PARAMETERS_FILE_PATH = str(Path(CONF_SOURCE) / "base" / "parameters.yml")

# Runtime parameters that can be overridden
RUNTIME_PARAMS = {}

def get_config() -> Dict[str, Any]:
    """Get the project configuration."""
    return {
        "project_name": PROJECT_NAME,
        "version": __version__,
        "kedro_version": KEDRO_INIT_VERSION,
        "package_name": PACKAGE_NAME,
    }


__all__ = [
    "PROJECT_NAME",
    "__version__",
    "RUN_ENVIRONMENT",
    "CONF_SOURCE",
    "KEDRO_INIT_VERSION",
    "SESSION_NAME",
    "PACKAGE_NAME",
    "LOGGING_CONFIG",
    "DATA_CATALOG_PATH",
    "PARAMETERS_FILE_PATH",
    "RUNTIME_PARAMS",
    "get_config",
]
