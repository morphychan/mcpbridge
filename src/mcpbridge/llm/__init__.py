"""
LLM Module for MCP Bridge.

This module provides LLM client functionality for MCP Bridge,
supporting OpenAI-compatible API interactions.
"""

from mcpbridge.llm.client import OpenAIClient
from mcpbridge.llm.config import LLMConfig
from mcpbridge.llm.exceptions import (
    LLMError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMAuthenticationError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseError,
    LLMModelError,
    LLMTokenLimitError,
)

__all__ = [
    "OpenAIClient",
    "LLMConfig",
    "LLMError",
    "LLMConfigurationError", 
    "LLMConnectionError",
    "LLMAuthenticationError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMModelError",
    "LLMTokenLimitError",
]