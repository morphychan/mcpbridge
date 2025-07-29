"""
MCP Bridge Logging Utilities.

This module provides unified logging configuration and utilities for the MCP Bridge application.
All modules should use this centralized logging system to maintain consistency.
"""

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, List, Union


def get_mcpbridge_logger(name: str) -> logging.Logger:
    """
    Get a configured MCP Bridge logger instance.
    
    This function creates and configures a logger with the standard MCP Bridge
    format and settings. All modules should use this function to get their logger.
    
    Args:
        name (str): The name for the logger, typically __name__ from the calling module
        
    Returns:
        logging.Logger: A configured logger instance with MCP Bridge formatting
        
    Example:
        >>> from mcpbridge.utils.logging import get_mcpbridge_logger
        >>> logger = get_mcpbridge_logger(__name__)
        >>> logger.info("This is a log message")
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Add handlers if not already present
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s - %(message)s', 
            datefmt='%m/%d/%y %H:%M:%S'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler with rotation
        try:
            # Ensure logs directory exists
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create rotating file handler (10MB max, keep 5 backup files)
            file_handler = logging.handlers.RotatingFileHandler(
                "logs/mcpbridge.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except (PermissionError, OSError):
            # If file logging fails, continue with console only
            pass
    
    return logger


def log_json(logger: logging.Logger, data: Union[Dict, List], title: str = "", level: str = "debug") -> None:
    """
    Log JSON data with pretty formatting.
    
    Args:
        logger (logging.Logger): The logger instance to use
        data (Union[Dict, List]): The data to format as JSON
        title (str): Optional title to prepend to the output
        level (str): Log level, defaults to "debug"
        
    Example:
        >>> logger = get_mcpbridge_logger(__name__)
        >>> data = {"name": "add", "args": ["a", "b"]}
        >>> log_json(logger, data, "Tool Info")
        >>> log_json(logger, data, "Important Info", level="info")
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if title:
        message = f"{title}:\n{json_str}"
    else:
        message = json_str
    
    # Use the appropriate log level
    log_func = getattr(logger, level.lower(), logger.debug)
    log_func(message)
