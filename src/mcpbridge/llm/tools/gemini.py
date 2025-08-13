"""
Gemini Tool Converter Module.

This module provides the implementation for converting tool definitions
to Google's Gemini function calling format.
"""

from typing import Any, Dict, List

from google.generativeai.types import Tool
from mcpbridge.llm.tools.base import BaseToolConverter, ToolValidationError
from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class GeminiToolConverter(BaseToolConverter):
    """
    Tool converter implementation for Gemini's function calling format.
    
    This converter transforms standard tool definitions into the format
    expected by Gemini's API, which uses function declarations.
    """
    
    def convert_tools(self, tools: List[Dict]) -> Tool:
        """
        Convert tools to Gemini's function calling format.
        
        Args:
            tools (List[Dict]): List of tool definitions in standard format
            
        Returns:
            Tool: Tools in Gemini format
            
        Raises:
            ToolValidationError: If tool validation fails
        """
        function_declarations = []
        
        for tool in tools:
            try:
                # Validate tool before conversion
                self.validate_tool(tool)
                
                # Convert to Gemini format
                function_declaration = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": self._convert_parameters(tool["parameters"])
                }
                
                function_declarations.append(function_declaration)
                logger.debug(f"Successfully converted tool: {tool['name']}")
                
            except Exception as e:
                self._handle_conversion_error(e, tool)
        
        logger.info(f"Converted {len(function_declarations)} tools to Gemini format")
        return Tool(function_declarations=function_declarations)
    
    def _convert_parameters(self, params: Dict) -> Dict:
        """
        Convert parameter schema to Gemini's format.
        
        This method handles any specific parameter conversions needed for
        Gemini's function calling format.
        
        Args:
            params (Dict): Parameter schema to convert
            
        Returns:
            Dict: Converted parameter schema
        """
        converted_params = super()._convert_parameters(params)
        
        # Ensure the schema follows Gemini's requirements
        if "type" in converted_params and converted_params["type"] == "object":
            # Gemini expects properties and required fields at the top level
            if "properties" in converted_params:
                for prop_name, prop_schema in converted_params["properties"].items():
                    # Add any Gemini-specific property adjustments here if needed
                    pass
        
        return converted_params