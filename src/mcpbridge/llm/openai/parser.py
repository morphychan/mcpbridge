import json

class LLMResponseParser:
    def __init__(self):
        pass

    def parse(self, response: dict) -> dict:
        """
        Parse LLM response and print it in JSON format for debugging.
        
        Args:
            response (dict): The raw response from the LLM API
            
        Returns:
            dict: The parsed response (currently just returns the input)
        """
        print("Parsing LLM response...")
        if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
            print(json.dumps(response["choices"][0]["message"], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(response, indent=2, ensure_ascii=False))
        return response