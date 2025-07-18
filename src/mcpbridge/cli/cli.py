#!/usr/bin/env python3
"""
MCP Bridge CLI
"""

import typer

from .commands import mcpserver

app = typer.Typer(
    name="mcpbridge",
    help="MCP Bridge - A lightweight MCP host for personal use",
    add_completion=False,
)

app.add_typer(mcpserver.app, name="mcpserver")


@app.command()
def version():
    """Show version information."""
    typer.echo("mcpbridge version 0.1.0")
    typer.echo("MCP Bridge - A lightweight MCP host")


if __name__ == "__main__":
    app() 