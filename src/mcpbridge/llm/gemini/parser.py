"""
Gemini Parser Module.

This module provides response parsing functionality for Gemini LLM service,
converting between Gemini and MCP formats.
"""

import json
from typing import Dict, List, Any

from mcpbridge.llm.base import BaseLLMParser
from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class GeminiParser(BaseLLMParser):
    """
    Parser for Gemini LLM responses.
    
    This class handles parsing and converting responses from the Gemini
    service into the standard MCP format, including tool calls and
    other special response types.
    """
    
    def parse(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the Gemini response.
        
        Args:
            response (Dict[str, Any]): The raw response from Gemini API
            
        Returns:
            Dict[str, Any]: The parsed response in MCP format
        """
        logger.info("Starting Gemini response parsing...")
        
        if not isinstance(response, dict) or "predictions" not in response:
            logger.warning("Invalid response format")
            return {}
        
        try:
            # Extract the main prediction (we only request one candidate)
            prediction = response["predictions"][0]
            
            # Convert to MCP format
            mcp_response = {
                "choices": [{
                    "message": {
                        "content": prediction.get("content", ""),
                        "role": "assistant"
                    },
                    "finish_reason": prediction.get("finishReason", "stop")
                }]
            }
            
            # Handle tool calls if present
            if "toolCalls" in prediction:
                mcp_response["choices"][0]["message"]["tool_calls"] = (
                    self._convert_tool_calls_to_mcp(prediction["toolCalls"])
                )
            
            logger.debug("Successfully parsed Gemini response")
            log_json(logger, mcp_response, "Parsed MCP response")
            return mcp_response
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {}
    
    def need_tools_call(self, response: Dict[str, Any]) -> bool:
        """
        Check if the response needs a tools call.
        
        Args:
            response (Dict[str, Any]): The raw response from Gemini API
            
        Returns:
            bool: True if tools call is needed, False otherwise
        """
        if not isinstance(response, dict) or "predictions" not in response:
            return False
            
        prediction = response["predictions"][0]
        has_tool_calls = "toolCalls" in prediction and prediction["toolCalls"]
        
        if has_tool_calls:
            logger.info("Gemini response needs tools call")
        else:
            logger.info("Gemini response does not need tools call")
            
        return has_tool_calls
    
    def prepare_tools_call(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare tools call from Gemini response.
        
        Args:
            response (Dict[str, Any]): The raw response from Gemini API
            
        Returns:
            List[Dict[str, Any]]: List of prepared tool calls in MCP format
        """
        tool_calls = []
        
        if not self.need_tools_call(response):
            return tool_calls
            
        try:
            prediction = response["predictions"][0]
            gemini_tool_calls = prediction["toolCalls"]
            
            for tool_call in gemini_tool_calls:
                try:
                    mcp_tool_call = self._convert_tools_format(tool_call)
                    tool_calls.append(mcp_tool_call)
                except Exception as e:
                    logger.error(f"Failed to convert tool call: {e}")
                    continue
            
            log_json(logger, tool_calls, "Prepared MCP tool calls")
            
        except Exception as e:
            logger.error(f"Failed to prepare tool calls: {e}")
            
        return tool_calls
    
    def _convert_tools_format(self, tools_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert tools data between Gemini and MCP format.
        
        Args:
            tools_data (Dict[str, Any]): Tools data in Gemini format
            
        Returns:
            Dict[str, Any]: Tools data in MCP format
        """
        if not tools_data:
            return {}
            
        try:
            # Extract tool information from Gemini format
            tool_name = tools_data["name"]
            arguments_str = tools_data.get("arguments", "{}")
            
            # Parse arguments
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {"raw_arguments": arguments_str}
            
            # Convert to MCP format
            return {
                "id": tools_data.get("id", "unknown"),
                "name": tool_name,
                "arguments": arguments
            }
            
        except Exception as e:
            logger.error(f"Failed to convert Gemini tool format: {e}")
            return {}