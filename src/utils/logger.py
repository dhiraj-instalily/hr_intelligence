"""
Logger module for configuring logging.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Define log levels
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

# Get log level from environment variable or use default
DEFAULT_LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info').lower()
LOG_LEVEL = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.INFO)

# Configure root logger
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name and log level.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Optional log level override
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set log level if specified
    if log_level is not None:
        level = LOG_LEVELS.get(log_level.lower(), LOG_LEVEL)
        logger.setLevel(level)
    
    return logger

def setup_file_logging(log_dir: str = 'logs'):
    """
    Set up file logging in addition to console logging.
    
    Args:
        log_dir: Directory to store log files
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    
    log_file = log_path / 'hr_intelligence.log'
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add file handler to root logger
    logging.getLogger().addHandler(file_handler)
    
    # Log that file logging has been set up
    logger = get_logger(__name__)
    logger.info(f"File logging set up at {log_file}")