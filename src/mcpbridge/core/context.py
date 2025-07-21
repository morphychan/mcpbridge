from __future__ import annotations
from typing import Optional, Dict, Any

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
        self.command = command

    def get_command(self) -> Command:
        """
        Get the command object from this context.
        
        Returns:
            Command: The command object stored in this context
        """
        return self.command
    
    def set_command(self, command: Command) -> None:
        """
        Set a new command object for this context.
        
        Args:
            command (Command): The new command object to store in this context
        """
        self.command = command

class Command:
    """
    Represents a command with options and support for nested command chaining.
    
    This class allows creating hierarchical command structures where each command
    can have a nested command, forming a chain or tree-like structure.
    """
    
    def __init__(self, cmd: str, 
                 options: Dict[str, Any] = None, 
                 nested_command: Optional[Command] = None) -> None:
        """
        Initialize a Command instance.
        
        Args:
            cmd (str): The command string to execute
            options (Dict[str, Any]): Dictionary containing command options and parameters
            nested_command (Optional[Command]): Another Command object to nest within this command.
                                              Defaults to None.
        """
        self.cmd = cmd
        self.options = options
        self.nested_command = nested_command  

    def get_cmd(self) -> str:
        """
        Get the command string.
        
        Returns:
            str: The command string
        """
        return self.cmd
    
    def has_options(self) -> bool:
        """
        Check if this command has options.
        
        Returns:
            bool: True if options exist, False otherwise
        """
        return self.options is not None

    def get_options(self) -> Dict[str, Any]:
        """
        Get the command options.
        
        Returns:
            Dict[str, Any]: Dictionary containing command options and parameters
        """
        return self.options
    
    def get_nested_command(self) -> Optional[Command]:
        """
        Get the nested command object.
        
        Returns:
            Optional[Command]: The nested command object, or None if no nested command exists
        """
        return self.nested_command
    
    def set_nested_command(self, next_command: Command) -> None:
        """
        Set the nested command object.
        
        Args:
            next_command (Command): The command object to set as nested command
        """
        self.nested_command = next_command
    
    def has_nested_command(self) -> bool:
        """
        Check if this command has a nested command.
        
        Returns:
            bool: True if a nested command exists, False otherwise
        """
        return self.nested_command is not None
    
    def print_command_chain(self) -> None:
        """
        Print the entire command chain starting from this command.
        
        Recursively prints all commands in the chain, displaying the command
        and its options for each level.
        """
        print(f"command: {self.cmd}, options: {self.options}")
        if self.nested_command:
            self.nested_command.print_command_chain()
    
    def calculate_chain_length(self) -> int:
        """
        Calculate the total length of the command chain.
        
        Returns:
            int: The number of commands in the chain including this command
        """
        if self.nested_command:
            return 1 + self.nested_command.calculate_chain_length()
        return 1
    
    def __str__(self) -> str:
        """
        Return string representation of the command chain.
        
        Returns:
            str: A string showing the command and its nested commands in chain format
        """
        if self.nested_command:
            return f"Command({self.cmd}) -> {str(self.nested_command)}"
        return f"Command({self.cmd})"
    