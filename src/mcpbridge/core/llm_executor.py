"""
LLM Executor Module

This module provides the LLMExecutor class which manages all interactions with the configured
Large Language Model (LLM). It handles client initialization, completion requests, and session management.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional

from mcpbridge.core.conversation import Conversation
from mcpbridge.llm.base import BaseLLMClient
from mcpbridge.llm.config import LLMConfig, LLMProvider
from mcpbridge.llm.exceptions import LLMConfigurationError, LLMError
from mcpbridge.llm.openai.client import OpenAIClient
from mcpbridge.llm.gemini.client import GeminiClient
from mcpbridge.utils.logging import get_mcpbridge_logger

# Initialize logger for this module
logger = get_mcpbridge_logger(__name__)


class LLMExecutor:
    """
    Manages all interactions with the configured LLM.
    
    This class provides a high-level interface for communicating with Large Language Models.
    It handles client initialization, session management, and provides methods for getting
    completions from the LLM with support for tools/function calling.
    
    Attributes:
        _session_id (str): Unique identifier for the current session
        _client (Optional[BaseLLMClient]): The LLM client instance, initialized lazily
    """

    def __init__(self, session_id: str):
        """
        Initialize the LLM executor with a session identifier.
        
        Args:
            session_id (str): Unique identifier for this session, used for logging and tracking
        """
        self._session_id = session_id
        self._client: Optional[BaseLLMClient] = None

    def _initialize_client(self):
        """
        Initialize the LLM client if not already done.
        
        This method performs lazy initialization of the LLM client. It reads the configuration,
        creates an OpenAIClient instance, and handles any configuration errors gracefully.
        The client is only created when needed to avoid unnecessary resource usage.
        
        Raises:
            LLMConfigurationError: If the LLM configuration is invalid or missing
        """
        if self._client:
            return  # Client already initialized
        
        try:
            # Load configuration and create appropriate client
            config = LLMConfig()
            
            # Create client with tool converter from config
            if config.provider == LLMProvider.OPENAI:
                self._client = OpenAIClient(
                    config=config,
                    session_id=self._session_id,
                    tool_converter=config.tool_converter
                )
            elif config.provider == LLMProvider.GEMINI:
                self._client = GeminiClient(
                    config=config,
                    session_id=self._session_id,
                    tool_converter=config.tool_converter
                )
            else:
                raise LLMConfigurationError(f"Unsupported LLM provider: {config.provider}")
                
            logger.info(
                f"Session {self._session_id}: LLM client initialized for provider {config.provider.value} "
                f"with tools {'enabled' if config.tools_enabled else 'disabled'}"
            )
        except LLMConfigurationError as e:
            logger.warning(f"Session {self._session_id}: LLM configuration error: {e}")
            self._client = None  # Ensure client is None on failure

    async def get_completion(
        self,
        conv: Conversation,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a completion from the LLM.
        
        This method sends a conversation and available tools to the LLM and returns
        the completion response. It handles client initialization, error handling,
        and logging for the entire interaction process.
        
        Args:
            conv (Conversation): The conversation object containing message history
            tools (Optional[List[Dict[str, Any]]]): List of available tools/functions that can be called.
                                                   If None, no tools will be provided even if enabled.
            
        Returns:
            Optional[Dict[str, Any]]: The LLM response as a dictionary, or None if the
                                     request failed or client is not available
                                     
        Note:
            The response format depends on the underlying LLM client implementation.
            Typically includes fields like 'content', 'tool_calls', etc.
            
            If tools are provided and enabled in configuration:
            - OpenAI format will include 'tool_calls' in the response
            - Gemini format will include 'function_call' in the response
        """
        # Ensure client is initialized before making requests
        self._initialize_client()
        if not self._client:
            logger.warning(f"Session {self._session_id}: Cannot get completion, client not available.")
            return None

        try:
            logger.info(f"Session {self._session_id}: Sending request to LLM")
            # Get configuration
            config = LLMConfig()
            
            # Only send tools if enabled and provided
            tools_to_send = tools if config.tools_enabled and tools else None
            
            # Send the conversation and tools to the LLM
            response = await self._client.chat_completion(
                messages=conv.get_messages(),
                tools=tools_to_send
            )
            
            # Log response details
            if tools_to_send:
                tool_call_info = (
                    "tool_calls" if "tool_calls" in response
                    else "function_call" if "function_call" in response
                    else None
                )
                if tool_call_info:
                    logger.info(f"Session {self._session_id}: LLM response received with {tool_call_info}")
                else:
                    logger.info(f"Session {self._session_id}: LLM response received without tool calls")
            else:
                logger.info(f"Session {self._session_id}: LLM response received")
            return response
        except LLMError as e:
            # Handle LLM-specific errors (e.g., API errors, rate limits)
            logger.error(f"Session {self._session_id}: LLM interaction failed: {e}")
            return None
        except Exception as e:
            # Handle unexpected errors (e.g., network issues, parsing errors)
            logger.error(f"Session {self._session_id}: Unexpected error during LLM interaction: {e}")
            return None

    async def close(self):
        """
        Close the LLM client session if it exists.
        
        This method properly cleans up the LLM client resources. It should be called
        when the executor is no longer needed to prevent resource leaks.
        """
        if self._client:
            await self._client.close()
            logger.info(f"Session {self._session_id}: LLM client closed.")

    async def __aenter__(self):
        """
        Async context manager entry point.
        
        Returns:
            LLMExecutor: The executor instance for use in async context managers
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        
        Ensures proper cleanup of the LLM client when exiting an async context.
        
        Args:
            exc_type: The exception type if an exception occurred
            exc_val: The exception value if an exception occurred
            exc_tb: The exception traceback if an exception occurred
        """
        await self.close()