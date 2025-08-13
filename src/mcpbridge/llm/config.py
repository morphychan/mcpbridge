"""
LLM Configuration Management Module.

This module provides configuration management for LLM interactions,
reading configuration from environment variables with validation
and default values.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional, Dict, Any

from mcpbridge.llm.tools.base import IToolConverter
from mcpbridge.llm.tools.openai import OpenAIToolConverter
from mcpbridge.llm.tools.gemini import GeminiToolConverter


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    
    @classmethod
    def from_string(cls, value: str) -> "LLMProvider":
        """Convert string to LLMProvider enum."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Unsupported LLM provider: {value}. Must be one of: {', '.join([p.value for p in cls])}")

from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class LLMConfig:
    """
    Configuration manager for LLM client settings.
    
    This class reads and validates LLM configuration from environment variables,
    providing default values for optional settings and ensuring required
    configuration is present.
    
    Environment Variables:
        MCPBRIDGE_LLM_API_KEY (required): API key for LLM service
        MCPBRIDGE_LLM_BASE_URL (optional): Base URL for API endpoints
        MCPBRIDGE_LLM_MODEL (optional): Default model to use
        MCPBRIDGE_LLM_TEMPERATURE (optional): Temperature parameter (0.0-2.0)
        MCPBRIDGE_LLM_MAX_TOKENS (optional): Maximum tokens in response
        MCPBRIDGE_LLM_TIMEOUT (optional): Request timeout in seconds
        MCPBRIDGE_LLM_TOOLS_ENABLED (optional): Enable/disable tool support (true/false)
    """
    
    def __init__(self) -> None:
        """
        Initialize LLM configuration by reading environment variables.
        
        Loads configuration from environment variables, validates required
        settings, and applies default values for optional settings.
        
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        logger.debug("Initializing LLM configuration from environment variables")
        
        # Load and validate provider configuration
        provider_str = self._get_optional_env("MCPBRIDGE_LLM_PROVIDER", "openai")
        self.provider = LLMProvider.from_string(provider_str)
        
        # Load provider-specific API key
        key_env_var = (
            "MCPBRIDGE_OPENAI_API_KEY" if self.provider == LLMProvider.OPENAI
            else "MCPBRIDGE_GEMINI_API_KEY"
        )
        self.api_key = self._get_required_env(key_env_var)
        
        # Load base URL (only needed for OpenAI)
        if self.provider == LLMProvider.OPENAI:
            self.base_url = self._get_optional_env(
                "MCPBRIDGE_LLM_BASE_URL", 
                "https://api.openai.com/v1"
            )
        else:
            # Gemini uses a fixed API endpoint
            self.base_url = None
        
        # Load model with provider-specific defaults
        self.model = self._get_optional_env(
            "MCPBRIDGE_LLM_MODEL", 
            "gpt-4" if self.provider == LLMProvider.OPENAI
            else "gemini-pro"
        )
        
        self.temperature = self._get_float_env(
            "MCPBRIDGE_LLM_TEMPERATURE", 
            1.0, 
            min_val=0.0, 
            max_val=2.0
        )
        
        self.max_tokens = self._get_int_env(
            "MCPBRIDGE_LLM_MAX_TOKENS", 
            4096, 
            min_val=1
        )
        
        self.timeout = self._get_float_env(
            "MCPBRIDGE_LLM_TIMEOUT", 
            120.0, 
            min_val=1.0
        )
        
        # Load tool-related configuration
        self.tools_enabled = self._get_bool_env("MCPBRIDGE_LLM_TOOLS_ENABLED", True)
        
        # Create appropriate tool converter based on provider if tools are enabled
        self.tool_converter = self._create_tool_converter() if self.tools_enabled else None
        
        logger.info("LLM configuration loaded successfully")
        logger.debug(
            f"Configuration: model={self.model}, base_url={self.base_url}, "
            f"tools_enabled={self.tools_enabled}"
        )
    
    def _get_required_env(self, var_name: str) -> str:
        """
        Get a required environment variable.
        
        Args:
            var_name (str): Name of the environment variable
            
        Returns:
            str: Value of the environment variable
            
        Raises:
            ValueError: If the environment variable is not set or empty
        """
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Required environment variable '{var_name}' is not set")
        return value.strip()
    
    def _get_optional_env(self, var_name: str, default: str) -> str:
        """
        Get an optional environment variable with a default value.
        
        Args:
            var_name (str): Name of the environment variable
            default (str): Default value if environment variable is not set
            
        Returns:
            str: Value from environment variable or default value
        """
        value = os.getenv(var_name)
        return value.strip() if value else default
    
    def _get_int_env(self, var_name: str, default: int, min_val: Optional[int] = None) -> int:
        """
        Get an integer environment variable with validation.
        
        Args:
            var_name (str): Name of the environment variable
            default (int): Default value if environment variable is not set
            min_val (Optional[int]): Minimum allowed value
            
        Returns:
            int: Parsed integer value
            
        Raises:
            ValueError: If the value cannot be parsed as integer or is out of range
        """
        value = os.getenv(var_name)
        if not value:
            return default
        
        try:
            int_value = int(value.strip())
        except ValueError:
            raise ValueError(f"Environment variable '{var_name}' must be an integer, got '{value}'")
        
        if min_val is not None and int_value < min_val:
            raise ValueError(f"Environment variable '{var_name}' must be >= {min_val}, got {int_value}")
        
        return int_value
    
    def _get_float_env(
        self, 
        var_name: str, 
        default: float, 
        min_val: Optional[float] = None, 
        max_val: Optional[float] = None
    ) -> float:
        """
        Get a float environment variable with validation.
        
        Args:
            var_name (str): Name of the environment variable
            default (float): Default value if environment variable is not set
            min_val (Optional[float]): Minimum allowed value
            max_val (Optional[float]): Maximum allowed value
            
        Returns:
            float: Parsed float value
            
        Raises:
            ValueError: If the value cannot be parsed as float or is out of range
        """
        value = os.getenv(var_name)
        if not value:
            return default
        
        try:
            float_value = float(value.strip())
        except ValueError:
            raise ValueError(f"Environment variable '{var_name}' must be a number, got '{value}'")
        
        if min_val is not None and float_value < min_val:
            raise ValueError(f"Environment variable '{var_name}' must be >= {min_val}, got {float_value}")
        
        if max_val is not None and float_value > max_val:
            raise ValueError(f"Environment variable '{var_name}' must be <= {max_val}, got {float_value}")
        
        return float_value
    
    def _get_bool_env(self, var_name: str, default: bool) -> bool:
        """
        Get a boolean environment variable.
        
        Args:
            var_name (str): Name of the environment variable
            default (bool): Default value if environment variable is not set
            
        Returns:
            bool: Parsed boolean value
            
        Raises:
            ValueError: If the value cannot be parsed as boolean
        """
        value = os.getenv(var_name)
        if not value:
            return default
        
        value = value.strip().lower()
        if value in ("true", "1", "yes", "on"):
            return True
        if value in ("false", "0", "no", "off"):
            return False
        
        raise ValueError(
            f"Environment variable '{var_name}' must be a boolean value "
            f"(true/false/1/0/yes/no/on/off), got '{value}'"
        )
    
    def _create_tool_converter(self) -> Optional[IToolConverter]:
        """
        Create appropriate tool converter based on provider.
        
        Returns:
            Optional[IToolConverter]: Tool converter instance or None if tools are disabled
        """
        if not self.tools_enabled:
            return None
            
        if self.provider == LLMProvider.OPENAI:
            return OpenAIToolConverter()
        elif self.provider == LLMProvider.GEMINI:
            return GeminiToolConverter()
        else:
            logger.warning(f"No tool converter available for provider: {self.provider}")
            return None
    
    def __str__(self) -> str:
        """
        Return a string representation of the configuration.
        
        Returns:
            str: A formatted string showing the configuration (API key masked)
        """
        masked_key = f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***"
        base_url_str = f"base_url={self.base_url}, " if self.base_url else ""
        tools_str = (
            f"tools_enabled={self.tools_enabled}, "
            f"tool_converter={self.tool_converter.__class__.__name__ if self.tool_converter else 'None'}"
        )
        return (
            f"LLMConfig(provider={self.provider.value}, model={self.model}, "
            f"{base_url_str}"
            f"api_key={masked_key}, temperature={self.temperature}, "
            f"max_tokens={self.max_tokens}, timeout={self.timeout}, "
            f"{tools_str})"
        ) 