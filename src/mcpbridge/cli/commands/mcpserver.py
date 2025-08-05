"""
MCP Server Command Module

This module provides command-line interfaces for managing Model Context Protocol
(MCP) servers. It includes functionality for starting MCP servers using different
transport mechanisms, with stdio transport being the primary supported method.

The module implements a hierarchical command structure:
- mcpserver: Top-level server management commands
  - stdio: Start MCP server using stdio transport
"""

from mcpbridge.core.context import Command, Context as MCPContext, ContextManager
from mcpbridge.utils.logging import get_mcpbridge_logger
import typer
from pathlib import Path
from typing import List, Optional

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)

mcpserv_app = typer.Typer(
    name="mcpserver",
    help="MCP server related commands",
    add_completion=False,
)

stdio_app = typer.Typer(
    name="stdio",
    help="stdio MCP server",
    add_completion=False,
    invoke_without_command=True,
)
mcpserv_app.add_typer(stdio_app, name="stdio")


@mcpserv_app.callback(invoke_without_command=True)
def mcpserv(ctx: typer.Context):
    """
    Handle MCP server command group initialization.
    
    This callback function is invoked when the 'mcpserver' command is called.
    It extends the command chain context by adding the mcpserver command to
    the execution path, allowing subcommands to access the full command hierarchy.
    
    Args:
        ctx (typer.Context): The Typer context object containing the shared
            MCP context from the parent command.
            
    Note:
        This function modifies the command chain in place by adding the
        mcpserver command as a nested command to the current tail command.
        If ctx.obj is None (e.g., during help requests), the function returns
        gracefully without modifying the context.
        
    Example:
        mcpbridge mcpserver stdio  # This function is called for 'mcpserver'
    """
    # If ctx.obj is None, this is likely a help request
    # Return gracefully without modifying the context
    if ctx.obj is None:
        return
    
    if not isinstance(ctx.obj, MCPContext):
        raise AttributeError(f"Invalid context type. Expected MCPContext, got {type(ctx.obj)}")
    
    mcp_ctx: MCPContext = ctx.obj
    mcpserv_cmd = Command(cmd="mcpserver")
    mcp_ctx.get_root_command().set_nested_command(mcpserv_cmd)


@stdio_app.callback(invoke_without_command=True)
def stdio(
    ctx: typer.Context,
    tool: Optional[List[str]] = typer.Option(
        None,
        "--tool",
        "-t",
        help='Define a tool. The value should be a single string with name, command, and path separated by spaces. e.g., -t "mytool /path/to/command /path/to/script.py". Can be used multiple times.',
    ),
):
    """
    Start an MCP server using stdio transport.
    
    This function configures and starts a Model Context Protocol (MCP) server
    that communicates via standard input/output streams. It extends the command
    chain context and prepares the execution environment for the MCP server.
    
    Args:
        ctx (typer.Context): The Typer context object containing the shared
            MCP context from parent commands.
        tool (Optional[List[str]]): A list of tool definitions. Each tool is defined by
            a single string containing three space-separated values: name, command, and path.
            
    Raises:
        AttributeError: If ctx.obj is None or doesn't contain a valid MCP context.
        typer.Exit: If the tool definitions are invalid.
        
    Example:
        # Start server with two tools
        mcpbridge mcpserver stdio -t "tool1 python /path/to/server1.py" -t "tool2 node /path/to/server2.js"
    """
    if not tool:
        typer.echo("Error: At least one tool must be provided via --tool or -t.", err=True)
        raise typer.Exit(1)

    tools = []
    for t in tool:
        name, command, path = t.split()
        tools.append({"name": name, "command": command, "path": path})

    logger.info(f"Tools: {tools}")

    if not isinstance(ctx.obj, MCPContext):
        raise AttributeError(f"Invalid context type. Expected MCPContext, got {type(ctx.obj)}")

    mcp_ctx: MCPContext = ctx.obj
    tail_cmd = mcp_ctx.get_root_command().get_tail_command()
    stdio_cmd = Command(cmd="stdio", options={"tools": tools})
    tail_cmd.set_nested_command(stdio_cmd)

    manager = ContextManager(mcp_ctx)
    manager.run()
