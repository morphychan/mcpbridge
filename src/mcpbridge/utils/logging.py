"""
MCP Bridge Logging Utilities.

This module provides unified logging configuration and utilities for the MCP Bridge application.
All modules should use this centralized logging system to maintain consistency.
"""

import json
import logging
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
    
    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        # Use standard MCP Bridge format: [MM/DD/YY HH:MM:SS] LEVEL - message
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s - %(message)s', 
            datefmt='%m/%d/%y %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
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
