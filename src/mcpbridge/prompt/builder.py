from typing import Dict, List
from pathlib import Path
import json

class PromptBuilder:
    def __init__(self, template_name: str = "default"):
        self.template_name = template_name
        self.template_content = self._load_template()
    
    def _load_template(self) -> str:
        """
        Load template content from the templates directory.
        
        Returns:
            str: The template content as a string
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
            IOError: If there's an error reading the file
        """
        # Get the template file path
        template_dir = Path(__file__).parent / "templates"
        template_file = template_dir / f"{self.template_name}.txt"
        
        # Check if template exists
        if not template_file.exists():
            raise FileNotFoundError(
                f"Template '{self.template_name}' not found at {template_file}"
            )
        
        # Load and return template content
        try:
            return template_file.read_text(encoding='utf-8')
        except IOError as e:
            raise IOError(f"Failed to read template '{self.template_name}': {e}")
    
    def build_initial_prompt(self, user_prompt: str) -> Dict:
        """
        Build the initial prompt by combining user prompt.
        
        Args:
            user_prompt (str): The user's input prompt
            
        Returns:
            Dict: Complete prompt dictionary ready for LLM API
        """
        # Simple string replacement
        filled_template = self.template_content.format(
            user_prompt=user_prompt,
        )
        
        # Parse and return as dictionary
        return json.loads(filled_template)