"""
MCP Server Commands
"""

import asyncio
from mcpbridge.client.stdio import run_stdio
import typer
from pathlib import Path

app = typer.Typer(
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
app.add_typer(stdio_app, name="stdio")


@stdio_app.callback(invoke_without_command=True)
def stdio(
    command: str = typer.Option(
        "python", "--command", "-c", help="Command to run"
    ),
    path: Path = typer.Option(
        Path("server.py"), "--path", "-p", help="Path to the MCP server"
    ),
):
    """
    Start the MCP (Model Context Protocol) server over stdio transport.
    
    This function launches an MCP server using the specified command and server file.
    The server communicates via standard input/output streams, which is the most
    common transport method for MCP servers.
    
    Args:
        command (str): The command to execute the MCP server (default: "python").
                      This should be the interpreter or executable that can run
                      the server file.
        path (Path): Path to the MCP server script file (default: "server.py").
                    This file should contain the MCP server implementation.
    
    Raises:
        typer.Exit: Exits with code 1 if the server file doesn't exist or
                   is not a valid file.
    
    Examples:
        # Run with default python command and server.py
        mcpbridge mcpserver stdio
        
        # Run with custom command and path
        mcpbridge mcpserver stdio --command "python3" --path "/path/to/my_server.py"
    """
    # Validate that the server file exists before attempting to run it
    if not path.exists():
        typer.echo(f"Error: Server file '{path}' not found", err=True)
        raise typer.Exit(1)
    
    # Ensure the path points to a file, not a directory
    if not path.is_file():
        typer.echo(f"Error: '{path}' is not a file", err=True)
        raise typer.Exit(1)
    
    # Display the command that will be executed
    typer.echo(f"Running `{command}` on MCP server at {path}")
    asyncio.run(run_stdio(command, [str(path)]))