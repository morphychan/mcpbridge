from __future__ import annotations

from mcpbridge.core.command import Command

class ContextManager:
    def __init__(self, ctx: Context):
        self.ctx = ctx


    def run(self) -> None:
        main_cmd = self.ctx.get_root_command()
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
        self.root_cmd = command
        self.prompt = self._get_prompt()

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
