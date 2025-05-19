"""
Logger utility for AutoNetLab project.

This module provides consistent logging functionality across the project
with customizable log levels and formats.
"""

import logging
import os
import sys
from datetime import datetime

# Default log directory
LOG_DIR = os.path.join(os.path.expanduser("~"), ".autonetlab", "logs")


def setup_logger(name=None, log_level=logging.INFO, log_file=None):
    """
    Set up and configure a logger instance with the specified name and log level.
    
    Args:
        name (str, optional): Name of the logger. Defaults to the module name.
        log_level (int, optional): Logging level. Defaults to logging.INFO.
        log_file (str, optional): Path to the log file. If None, will create a 
                                 timestamped log file in the default directory.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # If no name provided, use the calling module's name
    if name is None:
        name = os.path.basename(sys._getframe(1).f_code.co_filename).replace(".py", "")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with appropriate formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # If log_file is specified or default logging is enabled, add file handler
    if log_file is not None or os.environ.get("AUTONETLAB_LOGGING", "true").lower() == "true":
        # Create log directory if it doesn't exist
        if log_file is None:
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR, exist_ok=True)
            
            # Create a timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(LOG_DIR, f"{name}_{timestamp}.log")
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger
        logger.addHandler(file_handler)
    
    return logger

