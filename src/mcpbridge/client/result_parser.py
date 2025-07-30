"""
MCP Tool Result Parser Module.

This module provides functionality for parsing and extracting information
from MCP (Model Context Protocol) tool execution results.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Union
import json

from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class ToolResultParser:
    """
    Parser for MCP tool execution results.
    
    This class handles the parsing and extraction of information from MCP tool
    results, including text content, structured data, error information, and
    metadata. It provides a standardized interface for processing tool results
    regardless of their specific format or content type.
    """
    
    def __init__(self) -> None:
        """Initialize the ResultParser."""
        self.logger = logger
    
    def parse(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a tool result and extract all relevant information.
        
        This is the main entry point for parsing tool results. It extracts
        text content, structured data, error information, and metadata into
        a standardized format.
        
        Args:
            tool_result (Dict[str, Any]): The raw tool result from MCP server
            
        Returns:
            Dict[str, Any]: Standardized parsed result containing:
                - success (bool): Whether the tool execution was successful
                - text_content (str): Human-readable text content
                - structured_data (Dict[str, Any]): Structured data content
                - summary (str): Brief summary of the result
                - metadata (Dict[str, Any]): Extracted metadata
                - error_info (Optional[Dict[str, str]]): Error information if any
                
        Raises:
            ValueError: If the tool result structure is invalid
        """
        self.logger.debug("Parsing tool result")
        
        # Validate the result structure first
        if not self.validate_result_structure(tool_result):
            raise ValueError("Invalid tool result structure")
        
        # Check for errors
        success = not self.is_error(tool_result)
        error_info = None
        
        if not success:
            error_info = self.extract_error_info(tool_result)
            self.logger.warning(f"Tool execution failed: {error_info}")
        
        # Extract content
        text_content = self.extract_text_content(tool_result)
        structured_data = self.extract_structured_content(tool_result)
        metadata = self.extract_metadata(tool_result)
        
        # Generate summary
        summary = self.get_result_summary(tool_result)
        
        parsed_result = {
            "success": success,
            "text_content": text_content,
            "structured_data": structured_data,
            "summary": summary,
            "metadata": metadata,
            "error_info": error_info
        }
        
        self.logger.debug(f"Tool result parsed successfully: {summary}")
        return parsed_result
    
    def is_error(self, tool_result: Dict[str, Any]) -> bool:
        """
        Check if the tool result indicates an error.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to check
            
        Returns:
            bool: True if the result indicates an error, False otherwise
        """
        return tool_result.get("isError", False)
    
    def extract_error_info(self, tool_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract error information from a tool result.
        
        Args:
            tool_result (Dict[str, Any]): The tool result containing error info
            
        Returns:
            Dict[str, str]: Dictionary containing error details:
                - error_type (str): Type of error
                - message (str): Error message
                - details (str): Additional error details if available
        """
        error_info = {
            "error_type": "unknown",
            "message": "Tool execution failed",
            "details": ""
        }
        
        # Try to extract error message from content
        text_content = self.extract_text_content(tool_result)
        if text_content:
            error_info["message"] = text_content
        
        # Extract structured error information if available
        structured_data = self.extract_structured_content(tool_result)
        if structured_data:
            error_info["error_type"] = structured_data.get("error_type", "unknown")
            error_info["details"] = structured_data.get("details", "")
        
        return error_info
    
    def extract_text_content(self, tool_result: Dict[str, Any]) -> str:
        """
        Extract human-readable text content from tool result.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to extract text from
            
        Returns:
            str: Concatenated text content from all text-type content items
        """
        content_items = tool_result.get("content", [])
        text_parts = []
        
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                if text:
                    text_parts.append(str(text))
        
        return " ".join(text_parts)
    
    def extract_structured_content(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data content from tool result.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to extract structured data from
            
        Returns:
            Dict[str, Any]: The structured content, or empty dict if none available
        """
        structured_content = tool_result.get("structuredContent", {})
        
        # Ensure we return a dictionary
        if not isinstance(structured_content, dict):
            self.logger.warning(f"Structured content is not a dict: {type(structured_content)}")
            return {}
        
        return structured_content
    
    def extract_metadata(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata information from tool result.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to extract metadata from
            
        Returns:
            Dict[str, Any]: Extracted metadata information
        """
        metadata = {}
        
        # Extract top-level metadata
        if "_meta" in tool_result and tool_result["_meta"] is not None:
            metadata["tool_meta"] = tool_result["_meta"]
        
        # Extract content-level metadata
        content_items = tool_result.get("content", [])
        content_metadata = []
        
        for item in content_items:
            if isinstance(item, dict):
                item_meta = {}
                if item.get("_meta") is not None:
                    item_meta["_meta"] = item["_meta"]
                if item.get("annotations") is not None:
                    item_meta["annotations"] = item["annotations"]
                if item_meta:
                    content_metadata.append(item_meta)
        
        if content_metadata:
            metadata["content_metadata"] = content_metadata
        
        return metadata
    
    def get_result_summary(self, tool_result: Dict[str, Any]) -> str:
        """
        Generate a brief summary of the tool result.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to summarize
            
        Returns:
            str: Brief summary describing the result
        """
        if self.is_error(tool_result):
            return "Tool execution failed"
        
        # Try to get summary from text content
        text_content = self.extract_text_content(tool_result)
        if text_content:
            # Limit summary length
            if len(text_content) > 100:
                return f"Tool executed successfully: {text_content[:97]}..."
            return f"Tool executed successfully: {text_content}"
        
        # Fallback to structured content summary
        structured_data = self.extract_structured_content(tool_result)
        if structured_data:
            if "result" in structured_data:
                return f"Tool executed successfully with result: {structured_data['result']}"
            return f"Tool executed successfully with {len(structured_data)} data fields"
        
        return "Tool executed successfully"
    
    def validate_result_structure(self, tool_result: Dict[str, Any]) -> bool:
        """
        Validate that the tool result has the expected structure.
        
        Args:
            tool_result (Dict[str, Any]): The tool result to validate
            
        Returns:
            bool: True if the structure is valid, False otherwise
        """
        if not isinstance(tool_result, dict):
            self.logger.error("Tool result is not a dictionary")
            return False
        
        # Check for required fields
        required_fields = ["isError"]
        for field in required_fields:
            if field not in tool_result:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate content structure if present
        if "content" in tool_result:
            content = tool_result["content"]
            if not isinstance(content, list):
                self.logger.error("Content field must be a list")
                return False
            
            # Validate content items
            for i, item in enumerate(content):
                if not isinstance(item, dict):
                    self.logger.error(f"Content item {i} is not a dictionary")
                    return False
                if "type" not in item:
                    self.logger.error(f"Content item {i} missing type field")
                    return False
        
        # Validate structured content if present
        if "structuredContent" in tool_result:
            if not isinstance(tool_result["structuredContent"], (dict, type(None))):
                self.logger.error("Structured content must be a dictionary or null")
                return False
        
        return True
