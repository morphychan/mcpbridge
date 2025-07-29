"""
MCP Bridge StdIO Client Module.

This module provides a client interface for communicating with MCP (Model Context Protocol)
servers over standard input/output streams.
"""

import json
from typing import Dict, Any, List
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class StdioClient:
    """
    A client for communicating with MCP servers via standard I/O.
    
    This class handles the connection and communication with MCP servers
    that operate through standard input/output streams.
    """
    
    def __init__(self, command: str, args: list[str]) -> None:
        """
        Initialize the StdIO client.
        
        Args:
            command (str): The command to execute the MCP server
            args (list[str]): Command line arguments for the MCP server
        """
        self.command = command
        self.args = args
        self.logger = logger

    async def get_tools(self) -> Dict[str, Any]:
        """
        Retrieve available tools from the MCP server.
        
        Establishes a connection to the MCP server, initializes the session,
        and fetches the list of available tools with their specifications.
        
        Returns:
            Dict[str, Any]: A dictionary containing the tools information in the format:
                {
                    "tools": [
                        {
                            "name": "tool_name",
                            "description": "tool_description",
                            "inputSchema": {...},
                            "outputSchema": {...}
                        },
                        ...
                    ]
                }
        
        Raises:
            Exception: If connection to the MCP server fails or tool retrieval fails
        """
        # Log connection attempt with server details
        self.logger.debug(f"Connecting to MCP server: {self.command} {self.args}")
        
        # Create server parameters for stdio connection
        params = StdioServerParameters(
            command=self.command,
            args=self.args,
        )

        # Establish connection and create session
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                # Initialize the MCP session
                await session.initialize()
                self.logger.debug("MCP session initialized successfully")

                # Request available tools from the server
                tools_response = await session.list_tools()
                
                # Extract tools and convert to dictionary format
                tools = tools_response.tools                  
                tools_spec = [t.model_dump(by_alias=True) for t in tools]
                
                # Log tools information
                tool_names = [tool['name'] for tool in tools_spec]
                self.logger.info(f"Retrieved {len(tools_spec)} tools: {tool_names}")
                log_json(self.logger, tools_spec, "Tools specification")
                
                # Return tools array directly
                return tools_spec
                