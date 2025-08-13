"""
Tool Converter Base Module.

This module provides the base interfaces and implementations for converting
tool definitions between different LLM provider formats. It defines the core
contract that all tool converters must follow and provides common validation
and conversion logic.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class ToolValidationError(Exception):
    """
    Exception raised for tool validation errors.
    
    Attributes:
        message (str): Error message
        tool (Dict): The tool that failed validation
        details (Dict): Additional error details
    """
    
    def __init__(self, message: str, tool: Dict, details: Optional[Dict] = None) -> None:
        self.message = message
        self.tool = tool
        self.details = details or {}
        super().__init__(self.message)


class IToolConverter(ABC):
    """
    Interface defining the contract for tool converters.
    
    Tool converters are responsible for converting tool definitions from
    a standard format to provider-specific formats (e.g., OpenAI, Gemini).
    """
    
    @abstractmethod
    def convert_tools(self, tools: List[Dict]) -> Any:
        """
        Convert tools from standard format to provider-specific format.
        
        Args:
            tools (List[Dict]): List of tool definitions in standard format
            
        Returns:
            Any: Provider-specific tool format
            
        Raises:
            ToolValidationError: If tool validation fails
        """
        pass
    
    @abstractmethod
    def validate_tool(self, tool: Dict) -> bool:
        """
        Validate a single tool definition.
        
        Args:
            tool (Dict): Tool definition to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ToolValidationError: If validation fails
        """
        pass


class BaseToolConverter(IToolConverter):
    """
    Base implementation of tool converter with common functionality.
    
    This class provides common validation and conversion logic that can be
    reused by specific provider implementations.
    
    Attributes:
        REQUIRED_TOOL_FIELDS (List[str]): Required fields in tool definition
        SUPPORTED_PARAMETER_TYPES (List[str]): Supported parameter types
    """
    
    REQUIRED_TOOL_FIELDS = ["name", "description", "parameters"]
    SUPPORTED_PARAMETER_TYPES = ["string", "number", "integer", "boolean", "array", "object"]
    
    def validate_tool(self, tool: Dict) -> bool:
        """
        Validate tool definition against required fields and format.
        
        Args:
            tool (Dict): Tool definition to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ToolValidationError: If validation fails
        """
        try:
            # Check required fields
            for field in self.REQUIRED_TOOL_FIELDS:
                if field not in tool:
                    raise ToolValidationError(
                        f"Missing required field: {field}",
                        tool=tool
                    )
            
            # Validate name format
            if not isinstance(tool["name"], str) or not tool["name"].strip():
                raise ToolValidationError(
                    "Tool name must be a non-empty string",
                    tool=tool
                )
            
            # Validate description
            if not isinstance(tool["description"], str) or not tool["description"].strip():
                raise ToolValidationError(
                    "Tool description must be a non-empty string",
                    tool=tool
                )
            
            # Validate parameters schema
            self._validate_parameters(tool["parameters"])
            
            return True
            
        except ToolValidationError:
            raise
        except Exception as e:
            raise ToolValidationError(
                f"Unexpected error during tool validation: {str(e)}",
                tool=tool,
                details={"error_type": type(e).__name__}
            )
    
    def _validate_parameters(self, params: Dict) -> bool:
        """
        Validate parameter schema definition.
        
        Args:
            params (Dict): Parameter schema to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ToolValidationError: If validation fails
        """
        if not isinstance(params, dict):
            raise ToolValidationError(
                "Parameters must be a dictionary",
                tool={"parameters": params}
            )
        
        # Validate basic schema structure
        required_schema_fields = ["type", "properties"]
        for field in required_schema_fields:
            if field not in params:
                raise ToolValidationError(
                    f"Missing required field in parameters schema: {field}",
                    tool={"parameters": params}
                )
        
        # Validate type
        if params["type"] != "object":
            raise ToolValidationError(
                "Parameters schema type must be 'object'",
                tool={"parameters": params}
            )
        
        # Validate properties
        if not isinstance(params["properties"], dict):
            raise ToolValidationError(
                "Properties must be a dictionary",
                tool={"parameters": params}
            )
        
        # Validate each property
        for prop_name, prop_schema in params["properties"].items():
            if "type" not in prop_schema:
                raise ToolValidationError(
                    f"Missing type in property: {prop_name}",
                    tool={"parameters": params}
                )
            
            if prop_schema["type"] not in self.SUPPORTED_PARAMETER_TYPES:
                raise ToolValidationError(
                    f"Unsupported parameter type: {prop_schema['type']} in property: {prop_name}",
                    tool={"parameters": params}
                )
        
        return True
    
    def _convert_parameters(self, params: Dict) -> Dict:
        """
        Convert parameter schema to a standardized format.
        
        This method can be overridden by provider-specific implementations
        to handle special parameter conversion needs.
        
        Args:
            params (Dict): Parameter schema to convert
            
        Returns:
            Dict: Converted parameter schema
        """
        return params.copy()
    
    def _handle_conversion_error(self, error: Exception, tool: Dict) -> None:
        """
        Handle errors during tool conversion.
        
        Args:
            error (Exception): The error that occurred
            tool (Dict): The tool being converted
            
        Raises:
            ToolValidationError: Wrapped error with context
        """
        logger.error(f"Error converting tool: {error}")
        logger.debug(f"Tool that caused error: {json.dumps(tool, indent=2)}")
        
        if isinstance(error, ToolValidationError):
            raise error
        
        raise ToolValidationError(
            f"Error converting tool: {str(error)}",
            tool=tool,
            details={"error_type": type(error).__name__}
        )