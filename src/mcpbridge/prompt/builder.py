from typing import Dict
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
        Build the initial prompt dict with system message from template and user input.

        Args:
            user_prompt (str): User input to include in messages array

        Returns:
            Dict: Prompt dict with format {"messages": [{"role": "system", "content": ...}, {"role": "user", "content": ...}]}
        """
        # Template uses doubled braces ({{ }}) to escape Python format tokens.
        # We parse it as JSON first, then construct the final dict to avoid
        # JSON encoding issues with control characters in user input.

        # Convert doubled braces to single braces for JSON parsing.
        # User content placeholder will be handled separately.
        json_like = (
            self.template_content
            .replace("{{", "{")
            .replace("}}", "}")
        )

        # Temporarily replace the user content placeholder with an empty string
        # to ensure valid JSON for parsing.
        json_like = json_like.replace("{user_prompt}", "")

        try:
            template_obj = json.loads(json_like)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Template '{self.template_name}' is not valid JSON after brace normalization: {error}"
            ) from error

        # Extract system message from template, defaulting to empty if not found
        system_content = ""
        try:
            messages = template_obj.get("messages", [])
            if messages and isinstance(messages, list):
                first = messages[0]
                if isinstance(first, dict) and first.get("role") == "system":
                    system_content = first.get("content", "")
        except Exception:
            # Continue with empty system message if template structure is unexpected
            system_content = ""

        # Build final dict - json.dumps will properly escape any control chars
        prompt_payload: Dict = {
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_prompt},
            ]
        }

        return prompt_payload