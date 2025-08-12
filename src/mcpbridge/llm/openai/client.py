"""
LLM Client Module.

This module provides HTTP client functionality for communicating with
OpenAI-compatible LLM services, handling request/response cycles and
error management.
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Any, Optional

import aiohttp

from mcpbridge.llm.base import BaseLLMClient
from mcpbridge.llm.config import LLMConfig
from mcpbridge.llm.exceptions import (
    LLMConnectionError,
    LLMAuthenticationError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseError,
    LLMModelError,
    LLMTokenLimitError,
    LLMConfigurationError,
)
from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    HTTP client for OpenAI-compatible LLM services.
    
    This client provides methods for communicating with OpenAI-compatible
    APIs, handling authentication, request formatting, response parsing,
    and comprehensive error handling.
    
    Attributes:
        config (LLMConfig): Configuration settings for the client
        session_id (str): Session identifier for tracking and logging
        session (Optional[aiohttp.ClientSession]): HTTP session for requests
    """
    
    def __init__(self, config: LLMConfig, session_id: Optional[str] = None) -> None:
        """
        Initialize the OpenAI client.
        
        Args:
            config (LLMConfig): Configuration object containing API settings
            session_id (Optional[str]): Session identifier for tracking and logging.
                                      If not provided, defaults to "unknown"
        """
        super().__init__(config, session_id)
        if not config.base_url:
            raise LLMConfigurationError("OpenAI client requires base_url configuration")
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"Session {self.session_id}: Initialized OpenAI client with base URL: {config.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "mcpbridge/1.0.0",
                    "X-Session-ID": self.session_id
                }
            )
            logger.debug(f"Session {self.session_id}: Created new HTTP session")
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug(f"Session {self.session_id}: Closed HTTP session")
    
    def _convert_mcp_tools_to_openai(self, mcp_tools: List[Dict]) -> List[Dict]:
        """
        Convert MCP tools format to OpenAI tools format.
        
        Args:
            mcp_tools (List[Dict]): Tools in MCP format
            
        Returns:
            List[Dict]: Tools in OpenAI format
        """
        if not mcp_tools:
            return []
            
        openai_tools = []
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            openai_tools.append(openai_tool)
            
        logger.debug(f"Session {self.session_id}: Converted {len(mcp_tools)} MCP tools to OpenAI format")
        return openai_tools
    
    async def chat_completion(
        self, 
        messages: str,
        tools: str = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the LLM service.
        
        Args:
            messages (str): The user message content to send to the LLM
            tools (str): The tools to use for the LLM
            model (Optional[str]): Model to use (overrides config default)
            temperature (Optional[float]): Temperature parameter (overrides config default)
            max_tokens (Optional[int]): Maximum tokens (overrides config default)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Dict[str, Any]: The complete API response as a dictionary
            
        Raises:
            LLMConnectionError: If connection to the service fails
            LLMAuthenticationError: If authentication fails
            LLMAPIError: If the API returns an error response
            LLMTimeoutError: If the request times out
            LLMRateLimitError: If rate limits are exceeded
            LLMResponseError: If response parsing fails
        """
        await self._ensure_session()
        
        # Convert MCP tools to OpenAI format if provided
        openai_tools = None
        if tools:
            openai_tools = self._convert_mcp_tools_to_openai(tools)
        
        # Build request payload
        request_data = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
        }
        
        # Add tools only if provided
        if openai_tools:
            request_data["tools"] = openai_tools
        
        # Add any additional parameters
        request_data.update(kwargs)
        
        logger.info(f"Session {self.session_id}: Sending chat completion request to {self.config.model}")
        logger.debug(f"Session {self.session_id}: Request payload: {json.dumps(request_data, indent=2)}")
        
        try:
            url = f"{self.config.base_url}/chat/completions"
            
            async with self.session.post(url, json=request_data) as response:
                response_text = await response.text()
                
                # Log response details
                logger.debug(f"Session {self.session_id}: Response status: {response.status}")
                logger.debug(f"Session {self.session_id}: Response headers: {dict(response.headers)}")
                
                # Handle different response status codes
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        logger.info(f"Session {self.session_id}: Chat completion request successful")
                        logger.debug(f"Session {self.session_id}: Response data: {json.dumps(response_data, indent=2)}")
                        return response_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Session {self.session_id}: Failed to parse response JSON: {e}")
                        raise LLMResponseError(
                            "Failed to parse API response as JSON",
                            details={"response_text": response_text, "parse_error": str(e), "session_id": self.session_id}
                        )
                
                # Handle error responses
                await self._handle_error_response(response, response_text)
                
        except aiohttp.ClientError as e:
            logger.error(f"Session {self.session_id}: HTTP client error: {e}")
            raise LLMConnectionError(
                f"Failed to connect to LLM service: {e}",
                details={"error_type": type(e).__name__, "url": url, "session_id": self.session_id}
            )
        except asyncio.TimeoutError:
            logger.error(f"Session {self.session_id}: Request timed out")
            raise LLMTimeoutError(
                f"Request timed out after {self.config.timeout} seconds",
                details={"session_id": self.session_id}
            )
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse, response_text: str) -> None:
        """
        Handle API error responses by raising appropriate exceptions.
        
        Args:
            response (aiohttp.ClientResponse): The HTTP response object
            response_text (str): The response body text
            
        Raises:
            LLMAuthenticationError: For 401 status codes
            LLMRateLimitError: For 429 status codes
            LLMModelError: For 404 status codes (model not found)
            LLMTokenLimitError: For specific token limit errors
            LLMAPIError: For other API errors
        """
        status_code = response.status
        
        # Try to parse error response
        error_data = {}
        error_code = None
        error_message = f"API request failed with status {status_code}"
        
        try:
            error_data = json.loads(response_text)
            if "error" in error_data:
                error_info = error_data["error"]
                error_message = error_info.get("message", error_message)
                error_code = error_info.get("code")
        except json.JSONDecodeError:
            # If we can't parse the error response, use the raw text
            error_data = {"raw_response": response_text}
        
        logger.error(f"Session {self.session_id}: API error: {status_code} - {error_message}")
        
        # Add session_id to error_data for all exceptions
        error_data["session_id"] = self.session_id
        
        # Map status codes to specific exceptions
        if status_code == 401:
            raise LLMAuthenticationError(
                "Authentication failed - check your API key",
                details=error_data,
                status_code=status_code,
                error_code=error_code
            )
        elif status_code == 429:
            # Extract retry-after header for rate limiting
            retry_after = None
            if "retry-after" in response.headers:
                try:
                    retry_after = float(response.headers["retry-after"])
                except ValueError:
                    pass
            
            raise LLMRateLimitError(
                "Rate limit exceeded",
                details=error_data,
                status_code=status_code,
                error_code=error_code,
                retry_after=retry_after
            )
        elif status_code == 404:
            raise LLMModelError(
                f"Model not found: {self.config.model}",
                details=error_data,
                status_code=status_code,
                error_code=error_code
            )
        elif error_code == "context_length_exceeded" or "token" in error_message.lower():
            raise LLMTokenLimitError(
                "Token limit exceeded",
                details=error_data,
                status_code=status_code,
                error_code=error_code
            )
        else:
            # Generic API error
            raise LLMAPIError(
                error_message,
                details=error_data,
                status_code=status_code,
                error_code=error_code
            )

 