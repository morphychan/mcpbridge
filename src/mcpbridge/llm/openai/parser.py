import json

from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)

class OpenAIParser:
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
        logger.info("Starting LLM response parsing...")
        # if self.need_tools_call(response):
        #     self.prepare_tools_call(response)
    
    def need_tools_call(self, response: dict) -> bool:
        """
        Check if the LLM response needs a tools call.
        
        Args:
            response (dict): The raw response from the LLM API
            
        Returns:
            bool: True if the LLM response needs a tools call, False otherwise
        """
        if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
            if "tool_calls" in response["choices"][0]["message"]:
                logger.info("LLM response needs a tools call")
                return True
            else:
                logger.info("LLM response does not need a tools call")
                return False

    def prepare_tools_call(self, response: dict) -> list[dict]:
        """
        Prepare the tools call for the LLM response.
        
        Args:
            response (dict): The raw response from the LLM API
            
        Returns:
            list[dict]: List of prepared tools calls in MCP format
        """
        tools_calls = []
        
        if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0]["message"]
            
            if "tool_calls" in message and message["tool_calls"]:
                logger.info(f"Found {len(message['tool_calls'])} tool calls to prepare")
                
                for tool_call in message["tool_calls"]:
                    try:
                        # Convert single tool call from OpenAI to MCP format
                        mcp_tool_call = self._convert_openai_tool_call_to_mcp(tool_call)
                        tools_calls.append(mcp_tool_call)
                        
                        logger.debug(f"Prepared tool call: {mcp_tool_call['name']} with arguments: {mcp_tool_call['arguments']}")
                        
                    except KeyError as e:
                        logger.error(f"Invalid tool call format: missing key {e}")
                        continue
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool arguments: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error preparing tool call: {e}")
                        continue
                
                log_json(logger, tools_calls, "Prepared MCP tool calls")
            else:
                logger.info("No tool calls found in LLM response")
        else:
            logger.warning("Invalid response format for tool call preparation")
        
        return tools_calls

    def _convert_openai_tool_call_to_mcp(self, openai_tool_call: dict) -> dict:
        """
        Convert a single OpenAI tool call to MCP format.
        
        Args:
            openai_tool_call (dict): OpenAI format tool call
            
        Returns:
            dict: MCP format tool call
            
        Raises:
            KeyError: If required fields are missing
            json.JSONDecodeError: If arguments parsing fails
        """
        # Extract tool information from OpenAI format
        tool_name = openai_tool_call["function"]["name"]
        arguments_str = openai_tool_call["function"]["arguments"]
        
        # Parse arguments JSON string
        arguments = json.loads(arguments_str)
        
        # Return MCP tool call format
        return {
            "id": openai_tool_call["id"],
            "name": tool_name,
            "arguments": arguments
        }
