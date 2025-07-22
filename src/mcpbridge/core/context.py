from __future__ import annotations

from mcpbridge.core.command import Command

class ContextManager:
    def __init__(self, ctx: Context):
        self.ctx = ctx

    def run(self) -> None:
        main_cmd = self.ctx.get_command()
        leaf_cmd = main_cmd.get_tail_command()

        if leaf_cmd.cmd == "stdio":
            self._execute_stdio(leaf_cmd)

    def _execute_stdio(self, cmd: Command) -> None:
        pass

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

