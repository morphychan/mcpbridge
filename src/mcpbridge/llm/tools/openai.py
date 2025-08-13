"""
OpenAI Tool Converter Module.

This module provides the implementation for converting tool definitions
to OpenAI's function calling format.
"""

from typing import Any, Dict, List

from mcpbridge.llm.tools.base import BaseToolConverter, ToolValidationError
from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class OpenAIToolConverter(BaseToolConverter):
    """
    Tool converter implementation for OpenAI's function calling format.
    
    This converter transforms standard tool definitions into the format
    expected by OpenAI's API, which uses a specific function calling schema.
    """
    
    def convert_tools(self, tools: List[Dict]) -> List[Dict[str, Any]]:
        """
        Convert tools to OpenAI's function calling format.
        
        Args:
            tools (List[Dict]): List of tool definitions in standard format
            
        Returns:
            List[Dict[str, Any]]: Tools in OpenAI format
            
        Raises:
            ToolValidationError: If tool validation fails
        """
        openai_tools = []
        
        for tool in tools:
            try:
                # Validate tool before conversion
                self.validate_tool(tool)
                
                # Convert to OpenAI format
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": self._convert_parameters(tool["parameters"])
                    }
                }
                
                openai_tools.append(openai_tool)
                logger.debug(f"Successfully converted tool: {tool['name']}")
                
            except Exception as e:
                self._handle_conversion_error(e, tool)
        
        logger.info(f"Converted {len(openai_tools)} tools to OpenAI format")
        return openai_tools
    
    def _convert_parameters(self, params: Dict) -> Dict:
        """
        Convert parameter schema to OpenAI's format.
        
        This method handles any specific parameter conversions needed for
        OpenAI's function calling format.
        
        Args:
            params (Dict): Parameter schema to convert
            
        Returns:
            Dict: Converted parameter schema
        """
        converted_params = super()._convert_parameters(params)
        
        # Handle any OpenAI-specific parameter adjustments here
        # Currently, OpenAI's format matches our standard format,
        # but this method allows for future customization if needed
        
        return converted_params