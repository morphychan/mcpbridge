"""
MCP Bridge CLI

A command-line interface for the MCP Bridge application, providing
a lightweight Model Context Protocol (MCP) host for personal use.
"""

from mcpbridge.core.context import Command, Context as MCPContext
import typer
from pathlib import Path
import yaml

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
    ),
    config: Path = typer.Option(
        None,
        "--config",
        help="Path to the configuration file (YAML format)",
        exists=True,
        dir_okay=False,
        resolve_path=True
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
        config (Path, optional): Path to a YAML configuration file. If provided,
            settings from this file will be used, but can be overridden by
            command line arguments.
            
    Note:
        The created MCP context is stored in ctx.obj and can be accessed
        by all subcommands in the application hierarchy.
        
    Example:
        mcpbridge mcpserver stdio --path server.py
    """
    # Load config file if provided
    config_data = {}
    if config:
        try:
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            typer.echo(f"Error reading config file: {e}", err=True)
            raise typer.Exit(1)
    
    # Command line prompt overrides config file prompt
    final_prompt = prompt or config_data.get('prompt')
    
    if final_prompt is None:
        ctx.obj = None
        return
    
    # Create MCPContext with the final prompt
    main_cmd = Command(cmd="main", options={"prompt": final_prompt})
    mcp_ctx = MCPContext(main_cmd)
    
    # Store config data in context for subcommands
    if config_data:
        mcp_ctx.config = config_data
    
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