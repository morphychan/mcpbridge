"""
LLM Module for MCP Bridge.

This module provides LLM client functionality for MCP Bridge,
supporting multiple LLM providers including OpenAI and Google's Gemini.
"""

from mcpbridge.llm.base import BaseLLMClient
from mcpbridge.llm.openai.client import OpenAIClient
from mcpbridge.llm.gemini.client import GeminiClient
from mcpbridge.llm.config import LLMConfig, LLMProvider
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
    "BaseLLMClient",
    "OpenAIClient",
    "GeminiClient",
    "LLMConfig",
    "LLMProvider",
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