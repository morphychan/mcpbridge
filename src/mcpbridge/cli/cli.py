"""
MCP Bridge CLI

A command-line interface for the MCP Bridge application, providing
a lightweight Model Context Protocol (MCP) host for personal use.
"""

from mcpbridge.core.context import Command, Context as MCPContext
import typer

from .commands import mcpserver

app = typer.Typer(
    name="mcpbridge",
    help="MCP Bridge - A lightweight MCP host for personal use",
    add_completion=False,
)

app.add_typer(mcpserver.mcpserv_app, name="mcpserver")


@app.callback()
def main(
    ctx: typer.Context,
    prompt: str = typer.Option(
        None,
        "--prompt",
        help="Prompt string for the language model"
    )
):
    """
    Initialize the MCP Bridge CLI application context.
    
    This function serves as the main entry point for the MCP Bridge CLI.
    It creates the initial command context and stores it in the Typer context
    object for use by subcommands. The context tracks the command chain
    execution path throughout the application lifecycle.
    
    Args:
        ctx (typer.Context): The Typer context object for storing shared state
            across commands.
        prompt (str, optional): An optional prompt string that can be passed
            to the language model. Defaults to None.
            
    Note:
        The created MCP context is stored in ctx.obj and can be accessed
        by all subcommands in the application hierarchy.
        
    Example:
        mcpbridge mcpserver stdio --path server.py
    """
    main_cmd = Command(cmd="main", options={"prompt": prompt})
    mcp_ctx = MCPContext(main_cmd)
    ctx.obj = mcp_ctx


@app.command()
def version():
    """
    Display version information for MCP Bridge.
    
    Prints the current version number and description of the MCP Bridge
    application to standard output.
    
    Example:
        mcpbridge version
    """
    typer.echo("mcpbridge version 0.1.0")
    typer.echo("MCP Bridge - A lightweight MCP host")


if __name__ == "__main__":
    app() 