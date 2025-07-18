#!/usr/bin/env python3
"""
MCP Bridge CLI
"""

import typer
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="mcpbridge",
    help="MCP Bridge - A lightweight MCP host for personal use",
    add_completion=False,
)

@app.command()
def mcpserver(
    path: str = typer.Option("localhost", "--path", "-p", help="Path to the MCP server"),
):
    """Start the MCP server"""
    typer.echo(f"MCP server path is {path}")


@app.command()
def version():
    """Show version information"""
    typer.echo("mcpbridge version 0.1.0")
    typer.echo("MCP Bridge - A lightweight MCP host")


if __name__ == "__main__":
    app() 