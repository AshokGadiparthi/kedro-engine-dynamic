"""Structured logging setup."""

import logging
import logging.config
from pathlib import Path
from typing import Optional

def setup_logging(log_dir: str = "logs", config_file: Optional[str] = None) -> None:
    """Set up structured logging for the application."""
    Path(log_dir).mkdir(exist_ok=True)
    
    if config_file and Path(config_file).exists():
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{log_dir}/ml_engine.log"),
                logging.StreamHandler()
            ]
        )
    
    logger = logging.getLogger(__name__)
    logger.info("✅ Logging configured")

def get_logger(name: str) -> logging.Logger:
    """Get logger for a module."""
    return logging.getLogger(name)
