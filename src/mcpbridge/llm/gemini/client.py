"""
Gemini Client Module.

This module provides HTTP client functionality for communicating with
Google's Gemini LLM service, handling request/response cycles and
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
from mcpbridge.llm.tools.gemini import GeminiToolConverter
from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class GeminiClient(BaseLLMClient):
    """
    HTTP client for Google's Gemini LLM service.
    
    This client provides methods for communicating with Gemini API,
    handling authentication, request formatting, response parsing,
    and comprehensive error handling.
    
    Attributes:
        config (LLMConfig): Configuration settings for the client
        session_id (str): Session identifier for tracking and logging
        session (Optional[aiohttp.ClientSession]): HTTP session for requests
        credentials: Google Cloud credentials
    """
    
    def __init__(
        self,
        config: LLMConfig,
        session_id: Optional[str] = None,
        tool_converter: Optional[GeminiToolConverter] = None
    ) -> None:
        """
        Initialize the Gemini client.
        
        Args:
            config (LLMConfig): Configuration object containing API settings
            session_id (Optional[str]): Session identifier for tracking and logging
            tool_converter (Optional[GeminiToolConverter]): Tool converter instance.
                                                          If not provided, a new instance will be created.
        """
        # Create default tool converter if not provided
        if tool_converter is None:
            tool_converter = GeminiToolConverter()
            
        super().__init__(config, tool_converter, session_id)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_endpoint = "https://generativelanguage.googleapis.com/v1"
        logger.info(f"Session {self.session_id}: Initialized Gemini client")
    
    async def _ensure_session(self) -> None:
        """
        Ensure HTTP session is created.
        
        This method handles session creation with API key authentication.
        """
        if self.session is None or self.session.closed:
            try:
                # Create session with API key authentication
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers={
                        "x-goog-api-key": self.config.api_key,
                        "Content-Type": "application/json",
                        "User-Agent": "mcpbridge/1.0.0",
                        "X-Session-ID": self.session_id
                    }
                )
                logger.debug(f"Session {self.session_id}: Created new HTTP session with API key auth")
                
            except Exception as e:
                logger.error(f"Session {self.session_id}: Failed to create session: {e}")
                raise LLMAuthenticationError(
                    "Failed to create session",
                    details={"error": str(e), "session_id": self.session_id}
                )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug(f"Session {self.session_id}: Closed HTTP session")
    
    def _convert_messages_to_gemini_format(self, messages: str) -> List[Dict[str, Any]]:
        """
        Convert MCP message format to Gemini format.
        
        Args:
            messages (str): Messages in MCP format
            
        Returns:
            List[Dict[str, Any]]: Messages in Gemini format
        """
        if isinstance(messages, str):
            return [{
                "role": "user",
                "parts": [{"text": messages}]
            }]
        
        # If messages is already a list, convert each message
        if isinstance(messages, list):
            return [{
                "role": msg.get("role", "user"),
                "parts": [{"text": msg.get("content", "")}]
            } for msg in messages]
            
        logger.warning(f"Unexpected message format: {type(messages)}")
        return []
    
    def _prepare_tools(self, tools: Optional[List[Dict]]) -> Optional[Any]:
        """
        Prepare tools for API request using the tool converter.
        
        Args:
            tools (Optional[List[Dict]]): Tools in MCP format
            
        Returns:
            Optional[Any]: Tools in Gemini format, or None if no tools provided
        """
        if not tools or not self.tool_converter:
            return None
            
        try:
            converted_tools = self.tool_converter.convert_tools(tools)
            logger.debug(f"Session {self.session_id}: Converted {len(tools)} tools to Gemini format")
            return converted_tools
        except Exception as e:
            logger.error(f"Session {self.session_id}: Failed to convert tools: {e}")
            return None
    
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
        Send a chat completion request to the Gemini service.
        
        Args:
            messages (str): The user message content to send
            tools (Optional[str]): The tools to use
            model (Optional[str]): Model to use (overrides config default)
            temperature (Optional[float]): Temperature parameter
            max_tokens (Optional[int]): Maximum tokens
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Dict[str, Any]: The complete API response
            
        Raises:
            LLMConnectionError: If connection fails
            LLMAuthenticationError: If authentication fails
            LLMAPIError: If the API returns an error
            LLMTimeoutError: If the request times out
            LLMRateLimitError: If rate limits are exceeded
            LLMResponseError: If response parsing fails
        """
        await self._ensure_session()
        
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini_format(messages)
        
        # Build request payload
        request_data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.config.temperature,
                "maxOutputTokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                "topK": 40,
                "topP": 0.95,
            }
        }
        
        # Convert tools using the tool converter if provided
        gemini_tools = self._prepare_tools(tools)
        if gemini_tools:
            request_data["tools"] = gemini_tools
        
        # Add any additional parameters
        if kwargs:
            request_data["generationConfig"].update(kwargs)
        
        logger.info(f"Session {self.session_id}: Sending chat completion request")
        logger.debug(f"Session {self.session_id}: Request payload: {json.dumps(request_data, indent=2)}")
        
        try:
            url = f"{self.api_endpoint}/models/{self.config.model}:generateContent"
            async with self.session.post(url, json=request_data) as response:
                response_text = await response.text()
                
                # Log response details
                logger.debug(f"Session {self.session_id}: Response status: {response.status}")
                logger.debug(f"Session {self.session_id}: Response headers: {dict(response.headers)}")
                
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
                            details={"response_text": response_text, "parse_error": str(e)}
                        )
                
                # Handle error responses
                await self._handle_error_response(response, response_text)
                
        except aiohttp.ClientError as e:
            logger.error(f"Session {self.session_id}: HTTP client error: {e}")
            raise LLMConnectionError(
                f"Failed to connect to Gemini service: {e}",
                details={"error_type": type(e).__name__, "url": self.api_endpoint}
            )
        except asyncio.TimeoutError:
            logger.error(f"Session {self.session_id}: Request timed out")
            raise LLMTimeoutError(
                f"Request timed out after {self.config.timeout} seconds"
            )
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse, response_text: str) -> None:
        """
        Handle API error responses by raising appropriate exceptions.
        
        Args:
            response (aiohttp.ClientResponse): The HTTP response
            response_text (str): The response body text
            
        Raises:
            LLMAuthenticationError: For authentication errors
            LLMRateLimitError: For rate limiting
            LLMModelError: For model not found
            LLMTokenLimitError: For token limits
            LLMAPIError: For other API errors
        """
        status_code = response.status
        
        try:
            error_data = json.loads(response_text)
            error_message = error_data.get("error", {}).get("message", f"API request failed with status {status_code}")
        except json.JSONDecodeError:
            error_data = {"raw_response": response_text}
            error_message = f"API request failed with status {status_code}"
        
        logger.error(f"Session {self.session_id}: API error: {status_code} - {error_message}")
        
        if status_code == 401:
            raise LLMAuthenticationError("Authentication failed", details=error_data)
        elif status_code == 429:
            raise LLMRateLimitError("Rate limit exceeded", details=error_data)
        elif status_code == 404:
            raise LLMModelError(f"Model not found: {self.config.model}", details=error_data)
        elif "quota" in error_message.lower() or "limit" in error_message.lower():
            raise LLMTokenLimitError("Resource limits exceeded", details=error_data)
        else:
            raise LLMAPIError(error_message, details=error_data)