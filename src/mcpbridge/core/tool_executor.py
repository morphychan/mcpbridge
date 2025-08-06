"""
Tool Executor Module

This module provides the ToolExecutor class which manages interactions with the MCP (Model Context Protocol)
server for tool execution. It handles tool discovery, tool calling, and result parsing.
"""

from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING

from mcpbridge.client.stdio import StdioClient
from mcpbridge.client.result_parser import ToolResultParser
from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

if TYPE_CHECKING:
    from mcpbridge.core.context import Context

logger = get_mcpbridge_logger(__name__)

class ToolExecutor:
    """
    Manages interaction with the MCP server for tool execution.
    
    This class provides a high-level interface for communicating with MCP servers.
    It handles tool discovery, tool execution, and result parsing through the
    standard input/output (stdio) protocol.
    
    Attributes:
        _ctx (Context): The application context containing MCP server configuration
        _clients (Dict[str, StdioClient]): A dictionary of MCP clients, keyed by tool name
    """

    def __init__(self, ctx: Context):
        """
        Initialize the tool executor with application context.
        
        Args:
            ctx (Context): The application context containing MCP server configuration
                          including tool configurations with command and path information
        """
        self._ctx = ctx
        # Initialize stdio clients for each configured tool
        self._clients: Dict[str, StdioClient] = {}
        for tool_config in self._ctx.tools_config:
            self._clients[tool_config['name']] = StdioClient(
                tool_config['command'],
                [str(tool_config['path'])]
            )
        logger.info(f"Finished initializing tool executor with {len(self._clients)} clients: {self._clients}")

    async def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Retrieve available tools definition from all configured MCP servers.
        
        This method queries each MCP server to get its list of available tools.
        It then prefixes the tool names with the server name (e.g., 'search' becomes 'duckduckgo.search')
        and returns a single, flat list of all tool definitions for the LLM.
        
        Returns:
            List[Dict[str, Any]]: A flat list of tool definitions from all servers.
        """
        all_tools_def = []
        for server_name, client in self._clients.items():
            tool_defs: List[Dict[str, Any]] = await client.get_tools()

            for tool in tool_defs:
                original_function_name = tool.get("name", "")
                tool["name"] = f"{server_name}-{original_function_name}"
                all_tools_def.append(tool)

        log_json(logger, all_tools_def, "All tools definition")
        return all_tools_def

    async def call_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a single tool and return the parsed result.
        
        This method parses the tool name to route the call to the correct MCP server,
        executes the tool, and returns the result in a standardized format.
        
        Args:
            tool_call (Dict[str, Any]): The tool call specification from the LLM.
                - name (str): The full tool name, e.g., 'duckduckgo.search'
                - arguments (Dict[str, Any]): The arguments to pass to the tool
                - id (str): Unique identifier for this tool call
                
        Returns:
            Dict[str, Any]: The parsed tool result.
        """
        full_tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]
        tool_id = tool_call["id"]

        # Parse tool name and function name from the full name
        if '-' not in full_tool_name:
            raise ValueError(f"Invalid tool name format: '{full_tool_name}'. Expected 'server_name-tool_name'.")
        tool_name, function_name = full_tool_name.split('-', 1)

        client = self._clients.get(tool_name)
        if not client:
            raise ValueError(f"Tool server '{tool_name}' not found in available clients")
        raw_result = await client.call_tool(function_name, tool_args)

        parser = ToolResultParser()
        return parser.parse(tool_id, raw_result)