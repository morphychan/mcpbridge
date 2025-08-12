"""
LLM Base Classes Module.

This module defines the abstract base classes for LLM clients and parsers,
providing a common interface that all LLM implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from mcpbridge.llm.config import LLMConfig


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.
    
    This class defines the interface that all LLM client implementations
    must follow. It provides the basic structure for interacting with
    different LLM services in a consistent way.
    
    Attributes:
        config (LLMConfig): Configuration settings for the client
        session_id (str): Session identifier for tracking and logging
    """
    
    def __init__(self, config: LLMConfig, session_id: Optional[str] = None) -> None:
        """
        Initialize the base LLM client.
        
        Args:
            config (LLMConfig): Configuration object containing API settings
            session_id (Optional[str]): Session identifier for tracking and logging
        """
        self.config = config
        self.session_id = session_id or "unknown"
    
    @abstractmethod
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Implementations should handle session initialization here.
        """
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        
        Implementations should handle cleanup here.
        """
        pass
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: str,
        tools: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the LLM service.
        
        Args:
            messages (str): The user message content to send to the LLM
            tools (Optional[str]): The tools to use for the LLM
            model (Optional[str]): Model to use (overrides config default)
            temperature (Optional[float]): Temperature parameter (overrides config default)
            max_tokens (Optional[int]): Maximum tokens (overrides config default)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Dict[str, Any]: The complete API response as a dictionary
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the client connection.
        
        Implementations should handle proper resource cleanup here.
        """
        pass


class BaseLLMParser(ABC):
    """
    Abstract base class for LLM response parsers.
    
    This class defines the interface that all LLM parser implementations
    must follow. It provides the basic structure for parsing and processing
    responses from different LLM services.
    """
    
    @abstractmethod
    def parse(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the LLM response.
        
        Args:
            response (Dict[str, Any]): The raw response from the LLM API
            
        Returns:
            Dict[str, Any]: The parsed response
        """
        pass
    
    @abstractmethod
    def need_tools_call(self, response: Dict[str, Any]) -> bool:
        """
        Check if the LLM response needs a tools call.
        
        Args:
            response (Dict[str, Any]): The raw response from the LLM API
            
        Returns:
            bool: True if the LLM response needs a tools call, False otherwise
        """
        pass
    
    @abstractmethod
    def prepare_tools_call(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare the tools call for the LLM response.
        
        Args:
            response (Dict[str, Any]): The raw response from the LLM API
            
        Returns:
            List[Dict[str, Any]]: List of prepared tools calls
        """
        pass
    
    @abstractmethod
    def _convert_tools_format(self, tools_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert tools data between provider-specific and MCP format.
        
        Args:
            tools_data (Dict[str, Any]): Tools data in provider-specific format
            
        Returns:
            Dict[str, Any]: Tools data in MCP format
        """
        pass