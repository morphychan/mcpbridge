"""
MCP Bridge Session Management Module.

This module provides session management functionality for MCP Bridge,
handling the complete lifecycle of bridging MCP servers with LLM services.
This includes MCP server connections, tool discovery, prompt building,
LLM interactions, and response handling.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional, Dict, Any

from mcpbridge.client.result_parser import ToolResultParser
from mcpbridge.client.stdio import StdioClient
from mcpbridge.core.conversation import Conversation
from mcpbridge.llm.openai.client import OpenAIClient
from mcpbridge.llm.config import LLMConfig
from mcpbridge.llm.exceptions import LLMConfigurationError, LLMError
from mcpbridge.llm.openai.parser import OpenAIParser
from mcpbridge.prompt.builder import PromptBuilder
from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

if TYPE_CHECKING:
    from mcpbridge.core.context import Context

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class Session:
    """
    Manages a session for MCP Bridge operations.
    
    A session represents a complete interaction lifecycle that bridges MCP servers
    with LLM services. This includes:
    - MCP server connection and tool discovery
    - Prompt building with available tools
    - LLM interaction with the constructed prompt
    - Response handling and session cleanup
    
    Each session has a unique identifier for tracking and debugging purposes
    across both MCP and LLM interactions.
    """
    
    def __init__(self, ctx: Context) -> None:
        """
        Initialize a new MCP session.
        
        Args:
            ctx (Context): The context containing MCP server configuration
                          and other session parameters
        """
        # Generate unique session identifier for tracking
        self.id = str(uuid.uuid4())
        self.ctx = ctx

    async def start(self) -> None:
        """
        Start the MCP session and establish connection with the server.
        
        This method performs the complete MCP Bridge workflow:
        1. Initializes the session
        2. Creates a StdIO client connection to the MCP server
        3. Retrieves available tools from the server
        4. Builds the initial prompt with tools information
        5. Sends the prompt to the LLM service for processing
        6. Handles LLM response and cleanup
        
        The method integrates MCP server capabilities with LLM interactions,
        providing a complete bridge between the two systems. LLM configuration
        is loaded from environment variables and errors are handled gracefully.
        
        Raises:
            Exception: If connection to the MCP server fails or session 
                      initialization encounters an error. LLM errors are 
                      caught and logged but do not interrupt the session.
        """
        # Log session startup with unique identifier
        logger.info(f"Starting session {self.id}")
        logger.debug(f"Session context: {self.ctx}")
        
        try:
            # Create StdIO client with server configuration from context
            stdio_client = StdioClient(
                self.ctx.mcp_server['stdio']['command'], 
                [str(self.ctx.mcp_server['stdio']['path'])]
            )
            
            # Use async context manager if available, otherwise handle cleanup manually
            try:
                # Retrieve available tools from the MCP server
                tools_info = await stdio_client.get_tools()
            finally:
                # Ensure stdio_client is properly closed
                if hasattr(stdio_client, 'close'):
                    await stdio_client.close()
            
            # Build initial prompt with tools specification
            prompt_builder = PromptBuilder(template_name="default")
            initial_prompt = prompt_builder.build_initial_prompt(user_prompt=self.ctx.prompt)

            # Log the initial prompt with JSON formatting
            logger.info("Initial prompt generated successfully")
            log_json(logger, initial_prompt, "Full initial prompt")

            conv = Conversation(session=self.id, system_prompt=initial_prompt["messages"][0]["content"])
            conv.add_user_message(initial_prompt["messages"][1]["content"])
            messages = conv.get_messages()
            log_json(logger, messages, "Full initial messages")

            # Initialize with LLM and handle LLM response
            llm_response = await self._handle_llm_interaction(conv, tools_info)
            conv.add_assistant_message(llm_response)
            messages = conv.get_messages()
            log_json(logger, messages, "First LLM response messages")

            # Parse LLM response
            response_parser = OpenAIParser()
            while response_parser.need_tools_call(llm_response):
                tool_call =response_parser.prepare_tools_call(llm_response)
                # Assume only one tool call is needed
                tool_result = await stdio_client.call_tool(tool_call[0]["name"], tool_call[0]["arguments"])
                tool_result_parser = ToolResultParser()
                parse_result = tool_result_parser.parse(tool_call[0]["id"], tool_result)
                conv.add_tool_result(tool_call[0]["id"], tool_call[0]["name"], parse_result["text_content"])
                messages = conv.get_messages()
                log_json(logger, messages, "Tool result messages")
                llm_response = await self._handle_llm_interaction(conv, tools_info)
                break
  
        except Exception as e:
            logger.error(f"Session {self.id}: Critical error during session: {e}")
            raise
        finally:
            logger.info(f"Session {self.id}: Session completed")

    async def _handle_llm_interaction(self, conv: Conversation, tools_info: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Handle LLM interaction with proper error handling.
        
        Args:
            conv: The conversation to send to the LLM
            tools_info: The tools information to send to the LLM
            
        Returns:
            Optional[Dict[str, Any]]: The LLM response if successful, None if error occurred
        """
        try:
            # Create LLM configuration from environment variables
            llm_config = LLMConfig()
            logger.info(f"Session {self.id}: LLM configuration loaded successfully")
            
            # Create LLM client with session ID for tracking
            llm_client = OpenAIClient(llm_config, session_id=self.id)
            
            try:
                # Send chat completion request with initial prompt and tools
                logger.info(f"Session {self.id}: Sending request to LLM")
                llm_response = await llm_client.chat_completion(
                    messages=conv.get_messages(),
                    tools=tools_info
                )
                
               # Log successful LLM response
                logger.info(f"Session {self.id}: LLM response received successfully")

                return llm_response

            finally:
                # Close LLM client session
                await llm_client.close()
            
        except LLMConfigurationError as e:
            logger.warning(f"Session {self.id}: LLM configuration error: {e}")
            logger.warning(f"Session {self.id}: Continuing without LLM interaction")
            return None
            
        except LLMError as e:
            logger.error(f"Session {self.id}: LLM interaction failed: {e}")
            logger.warning(f"Session {self.id}: Continuing despite LLM error")
            return None
            
        except Exception as e:
            logger.error(f"Session {self.id}: Unexpected error during LLM interaction: {e}")
            logger.warning(f"Session {self.id}: Continuing despite unexpected error")
            return None

