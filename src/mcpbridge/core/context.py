from __future__ import annotations

from mcpbridge.core.command import Command
from mcpbridge.core.session import Session

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
        session.start()


class ContextParser:
    """
    Parses and validates command structures within a Context.
    
    The ContextParser is responsible for analyzing the hierarchical command structure
    stored in a Context object and extracting relevant configuration information.
    It validates command sequences, ensures proper nesting, and populates the
    context's mcp_servers dictionary with parsed server configurations.
    
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
        the context's mcp_servers dictionary with extracted configurations.
        
        Raises:
            ValueError: If the command structure is invalid or incomplete
        """
        self._parse_first_level_command()
        print(f"finished parsing context: {self.ctx}")

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
        parsing methods based on the detected protocol type. It initializes
        the server configuration dictionary before delegating to specific parsers.
        
        Raises:
            ValueError: If the second-level command is missing or specifies 
                       an unsupported protocol type
        """
        second_level_cmd = self.ctx.get_root_command().get_n_level_command(2)
        if second_level_cmd.get_cmd() == "stdio":
            self.ctx.mcp_servers["stdio"] = {}
            self._parse_stdio(second_level_cmd)
        else:
            raise ValueError(f"Expected 'stdio' command at second level, got {second_level_cmd.get_cmd()}")
    
    def _parse_stdio(self, stdio: Command) -> None:
        """
        Parse stdio-specific MCP server configuration.
        
        Extracts and validates configuration options for stdio-based MCP servers.
        This includes the command to execute and the path to the server script.
        The parsed configuration is stored in the context's mcp_servers dictionary
        under the 'stdio' key, replacing the initial empty dictionary.
        
        Args:
            stdio (Command): The stdio command object containing server configuration
                           options. Must have 'command' and 'path' options defined
                           and non-empty.
        
        Raises:
            ValueError: If required options ('command' or 'path') are missing
                       or empty
        
        Side Effects:
            Updates self.ctx.mcp_servers["stdio"] with the parsed configuration
            containing 'command' and 'path' keys
        """
        if not stdio.options['command'] or not stdio.options['path']:
            raise ValueError("'command' or 'path' options are required for stdio")
        self.ctx.mcp_servers["stdio"] = {
            "command": stdio.options['command'],
            "path": stdio.options['path']
        }

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
        self.mcp_servers = {}

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
        print(f"user prompt: {self.prompt}")

    def __str__(self) -> str:
        """
        Return a string representation of the Context.
        
        Provides a concise summary of the context's key attributes including
        the root command name, prompt length, and MCP server configurations.
        
        Returns:
            str: A formatted string showing the context's current state
        """
        return f"Context(root_cmd='{self.root_cmd.cmd}', prompt_len={len(self.prompt)}, mcp_servers={self.mcp_servers})"

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
