"""
MCP Bridge Session Management Module.

This module provides session management functionality for MCP Bridge,
handling the complete lifecycle of bridging MCP servers with LLM services.
This includes MCP server connections, tool discovery, prompt building,
LLM interactions, and response handling.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from mcpbridge.client.stdio import StdioClient
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
                tools_spec = await stdio_client.get_tools()
            finally:
                # Ensure stdio_client is properly closed
                if hasattr(stdio_client, 'close'):
                    await stdio_client.close()
            
            # Build initial prompt with tools specification
            prompt_builder = PromptBuilder(template_name="default")
            initial_prompt = prompt_builder.build_initial_prompt(
                user_prompt=self.ctx.prompt,
                tools_info=tools_spec
            )
            
            # Log the initial prompt with JSON formatting
            logger.info("Initial prompt generated successfully")
            log_json(logger, initial_prompt, "Full initial prompt")
            
            # Initialize and use LLM client
            await self._handle_llm_interaction(initial_prompt)
            
        except Exception as e:
            logger.error(f"Session {self.id}: Critical error during session: {e}")
            raise
        finally:
            logger.info(f"Session {self.id}: Session completed")

    async def _handle_llm_interaction(self, initial_prompt: dict) -> None:
        """
        Handle LLM interaction with proper error handling.
        
        Args:
            initial_prompt: The initial prompt to send to the LLM
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
                    messages=initial_prompt["messages"],
                    tools=initial_prompt["tools"]
                )
                
               # Log successful LLM response
                logger.info(f"Session {self.id}: LLM response received successfully")
                # log_json(logger, llm_response, "LLM Response")

                # Parse LLM response
                llm_response_parser = OpenAIParser()
                llm_response_parser.parse(llm_response)
 

            finally:
                # Close LLM client session
                await llm_client.close()
            
        except LLMConfigurationError as e:
            logger.warning(f"Session {self.id}: LLM configuration error: {e}")
            logger.warning(f"Session {self.id}: Continuing without LLM interaction")
            
        except LLMError as e:
            logger.error(f"Session {self.id}: LLM interaction failed: {e}")
            logger.warning(f"Session {self.id}: Continuing despite LLM error")
            
        except Exception as e:
            logger.error(f"Session {self.id}: Unexpected error during LLM interaction: {e}")
            logger.warning(f"Session {self.id}: Continuing despite unexpected error")