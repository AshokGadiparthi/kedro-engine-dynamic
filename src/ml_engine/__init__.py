"""ML Engine - World-Class Machine Learning Pipeline (v0.2.0)."""

__version__ = "0.2.0"
__author__ = "ML Team"

import sys
import logging

if sys.version_info < (3, 9):
    raise RuntimeError("ML Engine requires Python 3.9 or higher")

from ml_engine.utils.logger import setup_logging
from ml_engine.utils.exceptions import MLEngineException

setup_logging()
logger = logging.getLogger(__name__)
logger.info(f"🚀 ML Engine v{__version__} initialized")

__all__ = ["__version__", "setup_logging", "MLEngineException"]
