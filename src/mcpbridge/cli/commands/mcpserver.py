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
import typer
from pathlib import Path

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
            
    Raises:
        AttributeError: If ctx.obj is None or doesn't contain a valid MCP context.
        
    Note:
        This function modifies the command chain in place by adding the
        mcpserver command as a nested command to the current tail command.
        
    Example:
        mcpbridge mcpserver stdio  # This function is called for 'mcpserver'
    """
    if ctx.obj is None:
        raise AttributeError("MCP context not found. Ensure the main command was executed properly.")
    
    if not isinstance(ctx.obj, MCPContext):
        raise AttributeError(f"Invalid context type. Expected MCPContext, got {type(ctx.obj)}")
    
    mcp_ctx: MCPContext = ctx.obj
    mcpserv_cmd = Command(cmd="mcpserver")
    mcp_ctx.get_root_command().set_nested_command(mcpserv_cmd)


@stdio_app.callback(invoke_without_command=True)
def stdio(
    ctx: typer.Context,
    command: str = typer.Option(
        "python", "--command", "-c", help="Command to run"
    ),
    path: Path = typer.Option(
        Path("server.py"), "--path", "-p", help="Path to the MCP server"
    ),
):
    """
    Start an MCP server using stdio transport.
    
    This function configures and starts a Model Context Protocol (MCP) server
    that communicates via standard input/output streams. It extends the command
    chain context and prepares the execution environment for the MCP server.
    
    The stdio transport is the most common method for MCP server communication,
    where the server receives JSON-RPC messages through stdin and sends responses
    through stdout.
    
    Args:
        ctx (typer.Context): The Typer context object containing the shared
            MCP context from parent commands.
        command (str, optional): The command/interpreter to execute the MCP server.
            Common values include "python", "python3", "node", etc. 
            Defaults to "python".
        path (Path, optional): Path to the MCP server script file that implements
            the MCP protocol. Defaults to "server.py" in the current directory.
            
    Raises:
        AttributeError: If ctx.obj is None or doesn't contain a valid MCP context.
        typer.Exit: If the server file validation fails (when implemented).
        
    Example:
        # Start server with custom interpreter and path
        mcpbridge mcpserver stdio --command python3 --path /path/to/server.py
    """
    if ctx.obj is None:
        raise AttributeError("MCP context not found. Ensure the main command was executed properly.")
    
    if not isinstance(ctx.obj, MCPContext):
        raise AttributeError(f"Invalid context type. Expected MCPContext, got {type(ctx.obj)}")
    
    mcp_ctx: MCPContext = ctx.obj
    tail_cmd = mcp_ctx.get_root_command().get_tail_command()
    stdio_cmd = Command(cmd="stdio", options={"command": command, "path": path})
    tail_cmd.set_nested_command(stdio_cmd)

    manager = ContextManager(mcp_ctx)
    manager.run()

    # Validate that the server file exists before attempting to run it
    # if not path.exists():
    #     typer.echo(f"Error: Server file '{path}' not found", err=True)
    #     raise typer.Exit(1)
    
    # Ensure the path points to a file, not a directory
    # if not path.is_file():
    #     typer.echo(f"Error: '{path}' is not a file", err=True)
    #     raise typer.Exit(1)
    
    # Display the command that will be executed
    # typer.echo(f"Running `{command}` on MCP server at {path}")
    # asyncio.run(run_stdio(command, [str(path)]))