"""
Tool Executor Module

This module provides the ToolExecutor class which manages interactions with the MCP (Model Context Protocol)
server for tool execution. It handles tool discovery, tool calling, and result parsing.
"""

from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING

from mcpbridge.client.stdio import StdioClient
from mcpbridge.client.result_parser import ToolResultParser

if TYPE_CHECKING:
    from mcpbridge.core.context import Context


class ToolExecutor:
    """
    Manages interaction with the MCP server for tool execution.
    
    This class provides a high-level interface for communicating with MCP servers.
    It handles tool discovery, tool execution, and result parsing through the
    standard input/output (stdio) protocol.
    
    Attributes:
        _ctx (Context): The application context containing MCP server configuration
        _client (StdioClient): The MCP client for stdio communication
    """

    def __init__(self, ctx: Context):
        """
        Initialize the tool executor with application context.
        
        Args:
            ctx (Context): The application context containing MCP server configuration
                          including stdio command and path information
        """
        self._ctx = ctx
        # Initialize the stdio client with command and path from context
        self._client = StdioClient(
            self._ctx.mcp_server['stdio']['command'],
            [str(self._ctx.mcp_server['stdio']['path'])]
        )

    async def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Retrieve available tools definition from the MCP server.
        
        This method queries the MCP server to get the list of available tools
        and their definitions. The returned list contains tool schemas that
        describe the available functions, their parameters, and return types.
        
        Returns:
            List[Dict[str, Any]]: List of tool definitions, where each tool definition
                                 contains schema information like name, description,
                                 parameters, etc.
                                 
        Note:
            The tool definitions follow the MCP protocol specification and can be
            used by LLMs to understand available capabilities.
        """
        return await self._client.get_tools()

    async def call_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a single tool and return the parsed result.
        
        This method executes a tool call by sending the tool name and arguments
        to the MCP server, then parses and returns the result in a standardized format.
        
        Args:
            tool_call (Dict[str, Any]): The tool call specification containing:
                - name (str): The name of the tool to call
                - arguments (Dict[str, Any]): The arguments to pass to the tool
                - id (str): Unique identifier for this tool call
                
        Returns:
            Dict[str, Any]: The parsed tool result containing:
                - id (str): The tool call ID that was executed
                - result (Any): The actual result from the tool execution
                - error (Optional[str]): Error message if the tool call failed
                
        Note:
            The result is parsed using ToolResultParser to ensure consistent
            formatting and error handling across different tool types.
        """
        # Extract tool call components
        tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]
        tool_id = tool_call["id"]

        # Execute the tool call through the MCP client
        raw_result = await self._client.call_tool(tool_name, tool_args)

        # Parse and format the result
        parser = ToolResultParser()
        return parser.parse(tool_id, raw_result)