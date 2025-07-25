"""
MCP Bridge Session Management Module.

This module provides session management functionality for MCP Bridge,
handling the lifecycle of MCP server connections and tool interactions.
"""

from __future__ import annotations

import uuid
import json
from typing import TYPE_CHECKING

from mcpbridge.client.stdio import StdioClient

if TYPE_CHECKING:
    from mcpbridge.core.context import Context


class Session:
    """
    Manages a session for communicating with MCP servers.
    
    A session represents a single interaction lifecycle with an MCP server,
    including connection establishment, tool discovery, and communication.
    Each session has a unique identifier for tracking and debugging purposes.
    """
    
    def __init__(self, ctx: Context) -> None:
        """
        Initialize a new MCP session.
        
        Args:
            ctx (Context): The context containing MCP server configuration
                          and other session parameters
        """
        # Generate unique session identifier for tracking
        self.id = str(uuid.uuid4())
        self.ctx = ctx

    async def start(self) -> None:
        """
        Start the MCP session and establish connection with the server.
        
        This method:
        1. Initializes the session
        2. Creates a StdIO client connection to the MCP server
        3. Retrieves available tools from the server
        4. Optionally displays tool information (currently commented out)
        
        The method sets up the communication channel and performs initial
        handshake with the MCP server to discover available capabilities.
        
        Raises:
            Exception: If connection to the MCP server fails or session 
                      initialization encounters an error
        """
        # Log session startup with unique identifier
        print(f"starting session {self.id}")
        
        # Create StdIO client with server configuration from context
        stdio_client = StdioClient(
            self.ctx.mcp_server['stdio']['command'], 
            [str(self.ctx.mcp_server['stdio']['path'])]
        )
        
        # Retrieve available tools from the MCP server
        tools_info = await stdio_client.get_tools()
        
        # Optional tool information display (currently disabled)
        # These lines can be uncommented for debugging or verbose output
        # tool_names = [tool['name'] for tool in tools_info['tools']]
        # print(f"Available tools: {tool_names}")
        # print(json.dumps(tools_info['tools'], indent=2, ensure_ascii=False))
