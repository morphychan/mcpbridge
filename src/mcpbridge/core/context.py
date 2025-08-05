from __future__ import annotations
import asyncio

from mcpbridge.core.command import Command
from mcpbridge.core.session import Session
from mcpbridge.utils.logging import get_mcpbridge_logger

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)

class ContextManager:
    """
    Manages and orchestrates the execution of a Context.
    
    The ContextManager class is responsible for handling the lifecycle
    of a Context object, including parsing and validating commands,
    and initiating session execution.
    """
    
    def __init__(self, ctx: Context):
        """
        Initialize a ContextManager instance.
        
        Args:
            ctx (Context): The context object to be managed
        """
        self.ctx = ctx

    def run(self) -> None:
        """
        Execute the managed context.
        
        This method performs the following operations:
        1. Parse commands from the context 
        2. Validate commands from the context (TODO)
        3. Create and start a session with the context
        
        Returns:
            None
        """
        # TODO: 
        # validate commands of ctx
        ctx_parser = ContextParser(self.ctx)
        ctx_parser.parse()
        session = Session(self.ctx)
        asyncio.run(session.start())


class ContextParser:
    """
    Parses and validates command structures within a Context.
    
    The ContextParser is responsible for analyzing the hierarchical command structure
    stored in a Context object and extracting relevant configuration information.
    It validates command sequences, ensures proper nesting, and populates the
    context's tools_config list with parsed server configurations.
    
    The parser expects a specific command structure:
    - Level 0: Root command (contains global options like prompt)
    - Level 1: Service type command (e.g., 'mcpservers')
    - Level 2: Protocol command (e.g., 'stdio')
    
    Attributes:
        ctx (Context): The context object containing the command structure to parse
    
    Example:
        >>> parser = ContextParser(context)
        >>> parser.parse()  # Parses the entire command structure
    """
    
    def __init__(self, ctx: Context):
        """
        Initialize a ContextParser instance.
        
        Args:
            ctx (Context): The context object containing command structures to parse.
                          Must contain a valid root command with nested commands.
        """
        self.ctx = ctx
    
    def parse(self) -> None:
        """
        Parse the entire command structure within the context.
        
        This is the main entry point for parsing operations. It initiates the
        parsing process by examining the first-level command and delegating
        to appropriate specialized parsing methods.
        
        The parsing process validates the command hierarchy and populates
        the context's tools_config list with extracted configurations.
        
        Raises:
            ValueError: If the command structure is invalid or incomplete
        """
        self._parse_first_level_command()
        logger.info(f"Context parsing completed successfully: {self.ctx}")
        logger.debug(f"Parsed tool configurations: {self.ctx.tools_config}")

    def _parse_first_level_command(self) -> None:
        """
        Parse and validate the first-level command in the command hierarchy.
        
        Extracts the first-level command from the root command and validates
        that it matches expected service types. Currently supports 'mcpservers'
        as the primary service type.
        
        Raises:
            ValueError: If the first-level command is missing or is not a 
                       recognized service type ('mcpserver')
        """
        first_level_cmd = self.ctx.get_root_command().get_n_level_command(1)
        if first_level_cmd.get_cmd() == "mcpserver":
            self._parse_mcp_servers()
        else:
            raise ValueError(f"Expected 'mcpserver' command at first level, got {first_level_cmd.get_cmd()}")
        
    def _parse_mcp_servers(self) -> None:
        """
        Parse and validate MCP server configuration commands.
        
        Processes the second-level command which specifies the communication
        protocol for the MCP server. Currently supports 'stdio' protocol
        for standard input/output communication.
        
        This method acts as a dispatcher, routing to protocol-specific
        parsing methods based on the detected protocol type.
        
        Raises:
            ValueError: If the second-level command is missing or specifies 
                       an unsupported protocol type
        """
        second_level_cmd = self.ctx.get_root_command().get_n_level_command(2)
        if second_level_cmd.get_cmd() == "stdio":
            self._parse_stdio(second_level_cmd)
        else:
            raise ValueError(f"Expected 'stdio' command at second level, got {second_level_cmd.get_cmd()}")
    
    def _parse_stdio(self, stdio: Command) -> None:
        """
        Parse stdio-specific MCP server configurations from a list of tools.
        
        Extracts and validates configuration options for stdio-based MCP servers
        from the 'tools' option. The parsed configurations are stored in the 
        context's tools_config list.
        
        Args:
            stdio (Command): The stdio command object containing server configuration
                           options. Must have a 'tools' option which is a list of
                           dictionaries, each with 'name', 'command', and 'path'.
        
        Raises:
            ValueError: If the 'tools' option is missing, not a list, or if any
                       tool definition is invalid.
        
        Side Effects:
            Updates self.ctx.tools_config with the parsed configurations.
        """
        tools = stdio.options.get('tools')
        if not isinstance(tools, list):
            raise ValueError("'tools' option is required and must be a list for stdio")

        for tool_config in tools:
            if not all(k in tool_config for k in ['name', 'command', 'path']):
                raise ValueError(f"Invalid tool definition. Each tool must have 'name', 'command', and 'path'. Got: {tool_config}")
            self.ctx.tools_config.append(tool_config)


class Context:
    """
    Represents an execution context.
    
    The Context class serves as a container for command objects, providing
    a way to manage a specific execution context.
    """
    
    def __init__(self, command: Command) -> None:
        """
        Initialize a Context instance.
        
        Args:
            command (Command): The command object to be held in this context
        """
        self.root_cmd = command
        self.prompt = self._get_prompt()
        self.tools_config = []

    def get_root_command(self) -> Command:
        """
        Get the command object from this context.
        
        Returns:
            Command: The command object stored in this context
        """
        return self.root_cmd
    
    def set_root_command(self, command: Command) -> None:
        """
        Set a new command object for this context.
        
        Args:
            command (Command): The new command object to store in this context
        """
        self.root_cmd = command
    
    def print_prompt(self) -> None:
        """
        Print the prompt to the console.
        """
        logger.info(f"User prompt: {self.prompt}")
        logger.debug(f"Prompt length: {len(self.prompt)} characters")

    def __str__(self) -> str:
        """
        Return a string representation of the Context.
        
        Provides a concise summary of the context's key attributes including
        the root command name, prompt length, and tool configurations.
        
        Returns:
            str: A formatted string showing the context's current state
        """
        return f"Context(root_cmd='{self.root_cmd.cmd}', prompt_len={len(self.prompt)}, tools_config={self.tools_config})"

    def _get_prompt(self) -> str:
        """
        Get the prompt from the root command options.
        
        Returns:
            str: The prompt string from the command options
            
        Raises:
            ValueError: If the prompt is not set
        """
        if not self.root_cmd.options['prompt']:
            raise ValueError("Prompt is not set in command options")
        return self.root_cmd.options['prompt']
